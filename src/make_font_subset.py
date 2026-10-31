# -*- coding: utf-8 -*-
"""このサイトで実際に使っている文字だけの Webフォントを作る。

なぜ要るか:
  Google Fonts から Zen Maru Gothic を読むと、CSS 87KB に加えて
  woff2 が 168ファイル・2.33MB 落ちてくる（2026年10月の実測）。
  日本語のサブセットは使用頻度順の塊に分かれているので、使う文字が
  少なくても塊が散り、結果として大量のファイルを引く。
  これはこのサイトで最も重い部分で、図版 25MB より効く。

  実際に使っているのは約1,900字なので、その分だけを1ファイルに詰めれば
  ウェイトあたり数百KBに収まる。同一オリジンに置けば、描画を止める
  サードパーティのCSSも、DNS と TLS の往復2本も要らなくなる。

  Google Fonts の text= で同じことができるが、URLが14KBになる字数では
  無視されることを確認済みなので、自前で作る。

拾う文字:
  生成済みの index.html と全項目ページに出てくる文字すべて。
  これに加えて、ASCII・ひらがな・カタカナ・約物の全域を入れる。
  検索欄に打った文字が代替フォントに落ちて見た目が変わるのを防ぐため。

ライセンス:
  Zen Maru Gothic は SIL Open Font License 1.1。自前配信してよい。
  assets/fonts/OFL.txt に原文を置く。

使い方（fontTools と brotli が要る）:
  python3 -m venv /tmp/fontenv
  /tmp/fontenv/bin/pip install fonttools brotli
  /tmp/fontenv/bin/python src/make_font_subset.py <元のttfを置いたディレクトリ>
"""
import glob
import html as html_mod
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets", "fonts")

# ウェイトと、元ファイルの名前。500 は使っていないので作らない。
WEIGHTS = [(400, "ZenMaruGothic-Regular.ttf"),
           (700, "ZenMaruGothic-Bold.ttf"),
           (900, "ZenMaruGothic-Black.ttf")]

# 本文に出てこなくても入れておく範囲。
# 検索欄に打った文字が代替フォントに落ちると、入力中だけ字形が変わる。
ALWAYS = []
ALWAYS += [chr(c) for c in range(0x20, 0x7F)]        # ASCII
ALWAYS += [chr(c) for c in range(0x3000, 0x3040)]    # 句読点・括弧
ALWAYS += [chr(c) for c in range(0x3041, 0x30A0)]    # ひらがな
ALWAYS += [chr(c) for c in range(0x30A0, 0x3100)]    # カタカナ
ALWAYS += [chr(c) for c in range(0xFF01, 0xFF60)]    # 全角英数・記号
ALWAYS += list("　…※→←↑↓◯×♯℃±〜–—‐")


def used_chars():
    """生成済みのHTMLに出てくる文字を集める。"""
    files = [os.path.join(ROOT, "index.html")]
    files += sorted(glob.glob(os.path.join(ROOT, "*", "*", "index.html")))
    chars = set(ALWAYS)
    for path in files:
        raw = io.open(path, encoding="utf-8").read()
        raw = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", raw)
        text = html_mod.unescape(re.sub(r"<[^>]+>", " ", raw))
        chars.update(text)
    chars.discard("\n")
    chars.discard("\r")
    chars.discard("\t")
    return "".join(sorted(chars))


def main():
    src_dir = sys.argv[1] if len(sys.argv) > 1 else None
    if not src_dir or not os.path.isdir(src_dir):
        print("元のttfを置いたディレクトリを渡してください", file=sys.stderr)
        return 1
    from fontTools import subset

    text = used_chars()
    print("拾った異なり字数: %d" % len(text))
    os.makedirs(OUT_DIR, exist_ok=True)

    total = 0
    for weight, name in WEIGHTS:
        src = os.path.join(src_dir, name)
        if not os.path.exists(src):
            print("  %s が無い" % name, file=sys.stderr)
            return 1
        out = os.path.join(OUT_DIR, "zen-maru-gothic-%d.woff2" % weight)
        args = [
            src,
            "--text=%s" % text,
            "--output-file=%s" % out,
            "--flavor=woff2",
            "--layout-features=kern,liga,vert,vrt2,palt",
            "--no-hinting",
            "--desubroutinize",
            "--drop-tables+=DSIG",
            "--name-IDs=*",
        ]
        subset.main(args)
        size = os.path.getsize(out)
        total += size
        print("  %d: %s %s バイト" % (weight, os.path.basename(out), format(size, ",")))
    # ビルド時の照合に使う。どの文字を入れたかを残しておく。
    io.open(os.path.join(OUT_DIR, "chars.txt"), "w", encoding="utf-8").write(text)
    print("合計 %s バイト" % format(total, ","))
    return 0


if __name__ == "__main__":
    sys.exit(main())
