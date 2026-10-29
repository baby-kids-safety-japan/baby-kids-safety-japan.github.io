# -*- coding: utf-8 -*-
"""出典のリンク切れを調べる。

    python3 src/link_check.py              # 全部調べる
    python3 src/link_check.py --key ia_crib  # 1件だけ調べる
    python3 src/link_check.py --quiet      # 問題のあるものだけ出す

出典は人が1件ずつ開いて確かめるものだが、公的機関の資料は URL が黙って変わる。
消えたものと、移動したものを機械で見つけて、人が確かめる手間をそこに集める。

依存は標準ライブラリだけ。このリポジトリに pip の依存を増やさないため。
"""
import argparse
import concurrent.futures
import os
import random
import re
import ssl
import sys
import time
import urllib.error
import urllib.request

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import SRC  # noqa: E402
from products import PRODUCTS  # noqa: E402

WORKERS = 8
MAX_RETRY = 2

# 失敗の種別を分ける。
# 404 は「もう無い」とはっきり分かるが、接続できないのは
# 相手側の一時的な不調や、こちらの回線からの遮断であることが多い。
# どちらも「リンク切れ」として報告すると、直しようのない指摘が積み上がる。
GONE = "gone"              # 404。URL を直す必要がある
UNREACHABLE = "unreach"    # 到達できなかった。ブラウザでは開けることが多い

# ここに挙げたホストは、プログラムからのアクセスを拒むが、
# ブラウザでは問題なく開ける。到達できなくても報告しない。
# 載せるときは、実際にブラウザで開けることを確かめてから。
BROWSER_ONLY = [
    "https://www.gov-online.go.jp/",   # 403 を返すが、ブラウザでは開ける
    "https://www.meti.go.jp/",         # 同上
    "https://h-crisis.niph.go.jp/",    # 403
]

# Amazon は、このスクリプトからは確かめられない。
# 実在する ASIN も、でたらめな ASIN も、同じ 200 と同じ長さの案内ページを返す。
# 「ok」と出しても何も確かめていないので、商品は別の方法で確かめる。
# ブラウザ（Claude in Chrome）で /dp/<ASIN> を開き、#productTitle を読む。
# 手順は SKILL.md の「Amazon で商品を探す手法」にある。
AMAZON = "https://www.amazon.co.jp/"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def browser_only(url):
    return any(url.startswith(h) for h in BROWSER_ONLY)


def normalize(url):
    """比較用。末尾のスラッシュと、index.html の有無を無視する。"""
    u = re.sub(r"index\.html?$", "", url)
    return u.rstrip("/")


def check_url(url, retry=MAX_RETRY):
    """(状態, 表示用の文字列, 最終URL) を返す。

    HEAD と GET を交互に試す。HEAD に答えないサーバと、
    GET が重いだけのサーバの、どちらも拾うため。
    """
    attempt = MAX_RETRY - retry
    method = "HEAD" if attempt % 2 == 0 else "GET"
    timeout = 20 + 15 * attempt

    ctx = ssl.create_default_context()
    # 公的機関のサイトに、中間証明書を返さないものがある。
    # 証明書の検証はこの用途の目的ではないので、緩める。
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return ("ok", str(r.status), r.geturl())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return (GONE, "404", url)
        if e.code in (403, 405, 406):
            # 405/406 は HEAD を受け付けないだけのことがある。GET で試し直す。
            if retry > 0:
                return check_url(url, retry - 1)
            return (UNREACHABLE, str(e.code), url)
        if retry > 0:
            time.sleep(2 ** attempt + random.uniform(0, 2))
            return check_url(url, retry - 1)
        return (UNREACHABLE, str(e.code), url)
    except Exception as e:
        if retry > 0:
            time.sleep(2 ** attempt + random.uniform(0, 2))
            return check_url(url, retry - 1)
        return (UNREACHABLE, type(e).__name__, url)


def targets(key, with_products):
    """調べる (種別, キー, 表示名, URL) の一覧。"""
    out = []
    for k, (title, url) in SRC.items():
        if key and k != key:
            continue
        out.append(("出典", k, title, url))
    if with_products:
        for k, v in PRODUCTS.items():
            if key and k != key:
                continue
            asin, name = v[0], v[1]
            out.append(("商品", k, name, AMAZON + "dp/" + asin))
    return out


def main():
    ap = argparse.ArgumentParser(description="出典と商品のリンクを調べる")
    ap.add_argument("--key", default="", help="このキーだけ調べる")
    ap.add_argument("--products", action="store_true",
                    help="商品のASINの一覧を出す（Amazonは自動アクセスでは"
                         "実在を確かめられないので、確認はブラウザで行う）")
    ap.add_argument("--quiet", action="store_true", help="問題のあるものだけ出す")
    args = ap.parse_args()

    items = targets(args.key, args.products)
    if not items:
        print("対象がない", file=sys.stderr)
        return 1

    gone, moved, unreach = [], [], []

    def run(item):
        kind, k, title, url = item
        state, note, final = check_url(url)
        return (kind, k, title, url, state, note, final)

    # Amazon はここでは判定せず、一覧として出すだけにする。
    amazon = [i for i in items if i[3].startswith(AMAZON)]
    items = [i for i in items if not i[3].startswith(AMAZON)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for kind, k, title, url, state, note, final in ex.map(run, items):
            if state == "ok":
                if normalize(final) != normalize(url):
                    moved.append((kind, k, url, final))
                elif not args.quiet:
                    print("ok   %-6s %-24s" % (kind, k))
            elif state == GONE:
                gone.append((kind, k, title, url))
            else:
                if browser_only(url):
                    if not args.quiet:
                        print("skip %-6s %-24s （%s・ブラウザでは開ける）" % (kind, k, note))
                else:
                    unreach.append((kind, k, url, note))

    if amazon:
        print()
        print("■ 商品（%d件）── このスクリプトでは確かめられません" % len(amazon))
        print("   Amazon は、実在する ASIN にも、でたらめな ASIN にも、")
        print("   同じ案内ページを返します。ブラウザで次のURLを開き、")
        print("   #productTitle が登録名と合っているかを目で確かめてください。")
        for kind, k, title, url in [(a[0], a[1], a[2], a[3]) for a in amazon]:
            print("   %-22s %s" % (k, url))
            print("     登録名: %s" % title[:70])

    print()
    if gone:
        print("■ 消えている（URL を直す）")
        for kind, k, title, url in gone:
            print("  %s %s" % (k, url))
            print("     %s" % title[:70])
    if moved:
        print("■ 移動している（登録先を書き換える）")
        for kind, k, url, final in moved:
            print("  %s" % k)
            print("     旧 %s" % url)
            print("     新 %s" % final)
    if unreach:
        print("■ 到達できなかった（リンク切れとは限らない。ブラウザで確かめる）")
        for kind, k, url, note in unreach:
            print("  %s %s （%s）" % (k, url, note))

    print()
    print("調べた %d 件／消えている %d／移動 %d／到達できず %d"
          % (len(items), len(gone), len(moved), len(unreach)))
    if amazon:
        print("商品 %d 件は未確認（Amazon は自動アクセスでは確かめられない）" % len(amazon))
    # 消えているものがあるときだけ、異常終了にする。
    # 到達できなかっただけで止めると、動かすたびに落ちて見なくなる。
    return 1 if gone else 0


if __name__ == "__main__":
    sys.exit(main())
