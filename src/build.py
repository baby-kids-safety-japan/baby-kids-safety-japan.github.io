# -*- coding: utf-8 -*-
"""index.html を生成する。  python3 src/build.py"""
import html
import json
import os
import re
import sys

# __pycache__ を作らない。content.py を書き戻したときに、
# mtime が同じ秒に収まると古いバイトコードが読まれ、
# 直したはずの内容でビルドが落ち続けることが実際にあった。
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content import TABS, UPDATED
from glossary import GLOSSARY
from products import award as product_award
from products import note as product_note
from products import cred as product_cred
from products import staple as product_staple
from products import link as product_link
from sources import SRC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "src")

# 公開先。OGP と canonical、sitemap.xml が参照する。
# 末尾のスラッシュを含める。
SITE_URL = "https://baby-kids-safety-japan.github.io/"

SITE_TITLE = "赤ちゃんとこどもの安全ノート"
SITE_TAGLINE = "日本の公的情報でつくる、月齢別の事故予防ガイド"
SITE_DESC = ("日本の赤ちゃんとこどもの安全対策を月齢・年齢別にまとめたガイド。"
             "おくるみの巻き方、首がすわる前の抱っこ、揺さぶられっ子症候群の境目など、"
             "公的機関の情報をもとに図解で解説します。")

# お問い合わせフォーム（Google フォーム）の回答用URL。
# このファイルは公開リポジトリに入るので、フォームの編集用URLはここに書かない。
# 編集用URLは baby スキル（~/.claude/skills/baby/SKILL.md）に置いてある。
FORM_URL = ("https://docs.google.com/forms/d/e/"
            "1FAIpQLScwSVqJlYD9BVqomsr1YFCMWcyBmhq2yj8V0buz2B0z6a5NcA/viewform")

DISCLOSURE = ("当サイトはアフィリエイトプログラムに参加しています。"
              "Amazonのアソシエイトとして、当サイトは適格販売により収入を得ています。")


def asset(path, prefix=""):
    """assets/ のファイルに内容ハッシュを付ける。更新してもキャッシュが残らないように。

    prefix は、項目ページのように深い階層から参照するときの「../」を入れる。
    """
    import hashlib
    full = os.path.join(ROOT, path)
    try:
        with open(full, "rb") as f:
            h = hashlib.sha1(f.read()).hexdigest()[:8]
    except OSError:
        return prefix + path
    return "%s%s?v=%s" % (prefix, path, h)


def img_size(path):
    """JPEG/PNG の幅と高さを返す。外部ライブラリを使わない。
    width/height を HTML に書いておくと、遅延読み込みでも高さが先に確保され、
    ページ内リンクで飛んだあとに位置がずれない。"""
    full = os.path.join(ROOT, path)
    try:
        with open(full, "rb") as f:
            head = f.read(2)
            if head == b"\xff\xd8":                      # JPEG
                while True:
                    b = f.read(1)
                    if not b:
                        return None
                    if b != b"\xff":
                        continue
                    marker = f.read(1)
                    while marker == b"\xff":
                        marker = f.read(1)
                    if marker in (b"\xc0", b"\xc1", b"\xc2", b"\xc3"):
                        f.read(3)
                        h = int.from_bytes(f.read(2), "big")
                        w = int.from_bytes(f.read(2), "big")
                        return w, h
                    seglen = int.from_bytes(f.read(2), "big")
                    f.seek(seglen - 2, 1)
            f.seek(0)
            if f.read(8) == b"\x89PNG\r\n\x1a\n":        # PNG
                f.seek(16)
                w = int.from_bytes(f.read(4), "big")
                h = int.from_bytes(f.read(4), "big")
                return w, h
    except OSError:
        return None
    return None


def img_tag(src, alt, indent, eager=False):
    """図版を <picture> で出す。WebP を先に置き、元の JPEG を残す。

    図版は1枚平均 210KB の JPEG で、全部で 25MB あった。モバイルの通信量の
    ほとんどがこれだった。WebP の 1000px 版なら、同じ図が平均 47KB になる。

    2種類置くのは、スマートフォンの表示幅が約 311px（画素密度3倍でも
    933px で足りる）なのに対し、PC の Retina では 1400px が要るため。
    srcset でブラウザに選ばせると、モバイルは 1000px 版だけを落とす。

    JPEG を <img> に残すのは、WebP を読めない古い端末のため。
    ダウンロードされるのはどちらか一方だけなので、通信量は増えない。
    WebP が無いあいだ（変換前）は、これまでどおり <img> だけを出す。
    """
    size = img_size(src)
    dim = ' width="%d" height="%d"' % size if size else ""
    # 検索から着地する項目ページでは、唯一の図が最初の画面に入る。
    # lazy にすると、レイアウトが決まったあとに低い優先度で取りに行くため、
    # いちばん見たい図が1往復ぶん遅れて出る。
    load = (' loading="eager" fetchpriority="high"' if eager
            else ' loading="lazy"')
    img = '<img src="%s" alt="%s"%s%s decoding="async">' % (
        src, esc(alt), dim, load)

    base = src[:-4] if src.endswith(".jpg") else None
    webps = []
    if base:
        for w in (1000, 1400):
            cand = "%s-%d.webp" % (base, w)
            if os.path.exists(os.path.join(ROOT, cand)):
                webps.append((cand, w))
    if not webps:
        return indent + img

    srcset = ", ".join("%s %dw" % (c, w) for c, w in webps)
    return ('%s<picture>\n'
            '%s  <source type="image/webp" srcset="%s" sizes="%s">\n'
            '%s  %s\n'
            '%s</picture>' % (indent, indent, srcset, IMG_SIZES, indent, img, indent))


# 図版が実際に表示される幅。ブラウザが srcset からどれを選ぶかの判断に使う。
# 本文の列は max-width 840px で、カードの内側の余白を引くと約 790px。
# 狭い画面ではほぼ画面幅いっぱいになる。
IMG_SIZES = "(max-width: 840px) 100vw, 790px"


def esc(s):
    return html.escape(s, quote=False)


def render_figure(fig, eager=False):
    """fig = (src, alt, caption, kind)
    kind: "grid"    2x2の4コマ。読み順の番号バッジを重ねる
          "compare" 左右の比較図。左に×、右に◯のバッジを重ねる
          None      そのまま出す
    """
    src, alt, caption, kind = fig
    if kind in ("grid", "grid6"):
        cells = 6 if kind == "grid6" else 4
        cls = "figure-grid6" if kind == "grid6" else "figure-grid"
        badges = "\n".join(
            '        <span class="order order-%d" aria-hidden="true">'
            '<span class="mark">%d</span></span>' % (i, i)
            for i in range(1, cells + 1))
        img = ('      <div class="%s">\n%s\n%s\n      </div>'
               % (cls, img_tag(src, alt, "        ", eager), badges))
    elif kind in ("compare", "compare-ok-left"):
        # compare          左が危険な例、右が安全な例
        # compare-ok-left  左が安全な例、右が危険な例
        left, right = ("ng", "ok") if kind == "compare" else ("ok", "ng")
        mark = {"ng": "×", "ok": "◯"}
        side = {"ng": "危険な例", "ok": "安全な例"}
        badges = ('        <span class="sr-only">左は%s、右は%sです。</span>\n'
                  '        <span class="judge judge-left judge-%s" aria-hidden="true">'
                  '<span class="mark">%s</span></span>\n'
                  '        <span class="judge judge-right judge-%s" aria-hidden="true">'
                  '<span class="mark">%s</span></span>'
                  % (side[left], side[right],
                     left, mark[left], right, mark[right]))
        img = ('      <div class="figure-compare">\n%s\n%s\n      </div>'
               % (img_tag(src, alt, "        ", eager), badges))
    else:
        img = img_tag(src, alt, "      ", eager)
    return ('    <figure class="figure">\n%s\n'
            '      <figcaption>%s</figcaption>\n    </figure>\n' % (img, esc(caption)))


def render_goods(goods, kind=None, seen=None):
    points = "\n".join("        <li>%s</li>" % annotate(p, seen if seen is not None else set())
                        for p in goods["points"])
    picks = []
    for key in goods["picks"]:
        url, name = product_link(key)
        aw = product_award(key)
        cr = product_cred(key)
        st = product_staple(key)
        if aw:
            badge = '<span class="award">🏅 %s</span>' % esc(aw[0])
        elif cr:
            # 賞ではなく、現場で使われている実績や国の許可で選んだもの。賞と混ぜない。
            badge = '<span class="cred">🏥 %s</span>' % esc(cr[0])
        elif st:
            # 賞も実績も無いが、長く売られている定番であることを示す。
            badge = '<span class="staple">📌 %s</span>' % esc(st[0])
        else:
            # 受賞バッジが無いと、その行だけ空きができる。
            # 代わりに「なぜ挙げたのか」の一言を同じ位置に出す。
            nt = product_note(key)
            badge = ('<span class="pick-note">%s</span>' % esc(nt)) if nt else ""
        picks.append('        <li><a href="%s" target="_blank" rel="nofollow sponsored noopener">'
                     '<span class="pick-name">%s%s</span>'
                     '<span class="go">Amazonで見る →'
                     '<span class="sr-only">（新しいタブで開きます）</span></span></a></li>'
                     % (url, esc(name), badge))

    body = '      <ul class="goods-picks">\n%s\n      </ul>\n' % "\n".join(picks)
    note = "リンクはAmazonアソシエイトリンクです。%s" % esc(DISCLOSURE)

    heading = "📚 読んでおくと役に立つ本" if kind == "books" else "🛍 グッズの選び方"
    return ('    <div class="goods">\n'
            '      <div class="goods-head"><h4>%s</h4>'
            '<span class="pr">PR</span></div>\n'
            '      <ul class="goods-points">\n%s\n      </ul>\n'
            '%s'
            '      <p class="goods-note">%s '
            '<a href="#policy">選び方の方針</a></p>\n'
            '    </div>\n' % (heading, points, body, note))


def render_sources(sources):
    lis = []
    for key, note in sources:
        title, url = SRC[key]
        lis.append('        <li><a href="%s" target="_blank" rel="noopener">%s<span class="sr-only">（新しいタブで開きます）</span></a>'
                   '<br><small>%s</small></li>' % (url, esc(title), esc(note)))
    return ('    <details class="sources">\n'
            '      <summary>この項目の根拠</summary>\n'
            '      <ul>\n%s\n      </ul>\n    </details>\n' % "\n".join(lis))


def item_url(tab_id, item_id):
    """項目ページのURL（サイトのルートからの相対）。"""
    return "%s/%s/" % (tab_id, item_id)


def item_page_prefix():
    """項目ページ（/タブ/項目/）から見たルートへの相対パス。"""
    return "../../"


def render_item(item, color, tab_id=None, page_prefix="", eager_figure=False):
    """tab_id を渡すと、カードの末尾に、その項目だけのページへのリンクが付く。
    項目ページ自身では渡さない（自分へのリンクになるため）。
    見出しの「#」は、どちらの場合もそのカードへのページ内リンクである。"""
    seen = set()
    out = ['  <article class="card card-%s" id="%s">' % (color, item["id"])]
    out.append('    <div class="card-head">')
    out.append('      <span class="chip">%s</span>' % esc(item["chip"]))
    out.append('      <h3><a class="anchor" href="#%s">%s'
               '<span class="anchor-mark" aria-hidden="true">#</span></a></h3>'
               % (item["id"], esc(item["title"])))
    if item.get("sub"):
        out.append('      <p class="card-tagline">%s</p>' % esc(item["sub"]))
    out.append('      <p class="card-sub">%s</p>' % annotate(item["lead"], seen))
    out.append('    </div>')

    if item.get("figure"):
        out.append(render_figure(item["figure"], eager_figure).rstrip("\n"))

    if item.get("steps"):
        out.append('    <ol class="steps">')
        for h, p in item["steps"]:
            out.append('      <li><h4>%s</h4><p>%s</p></li>' % (esc(h), annotate(p, seen)))
        out.append('    </ol>')

    if item.get("figure2"):
        src, alt, caption = item["figure2"]
        out.append(render_figure((src, alt, caption, False)).rstrip("\n"))

    if item.get("table"):
        head, rows = item["table"]
        out.append('    <div class="hazard">')
        out.append('      <h4>%s</h4>' % esc(head))
        out.append('      <table>')
        for left, right in rows:
            out.append('        <tr><th>%s</th><td>%s</td></tr>' % (esc(left), annotate(right, seen)))
        out.append('      </table>')
        out.append('    </div>')

    if item.get("checks"):
        out.append('    <div class="checklist">')
        out.append('      <ul>')
        for kind, title, body in item["checks"]:
            mark = "◯" if kind == "ok" else "×"
            # 見出し語として読ませる。「してはいけないこと：手を離さない」だと
            # 二重否定になるので、「しないこと」にとどめる。
            label = "すること" if kind == "ok" else "しないこと"
            # 記号を内側の span で包む。
            # グリフの墨は丸の中心より下に出るので、少しだけ上げて戻す。
            # 外側の span を動かすと丸ごと動いてしまうため、内側が要る。
            out.append('        <li><span class="%s" aria-hidden="true">'
                       '<span class="mark">%s</span></span>'
                       '<span class="sr-only">%s：</span>'
                       '<div><strong>%s</strong><br>%s</div></li>'
                       % (kind, mark, label, esc(title), annotate(body, seen)))
        out.append('      </ul>')
        out.append('    </div>')

    callouts = item.get("callouts") or ([item["callout"]] if item.get("callout") else [])
    for title, body in callouts:
        out.append('    <div class="callout callout-warn">')
        out.append('      <h4>%s</h4>' % esc(title))
        out.append(annotate(body, seen).rstrip())
        out.append('    </div>')

    if item.get("goods"):
        out.append(render_goods(item["goods"], item.get("goods_kind"), seen).rstrip("\n"))

    out.append(render_sources(item["sources"]).rstrip("\n"))
    if tab_id:
        # 個別ページへの入口は、記号ではなく言葉で出す。
        # 「#」は見出しのページ内リンクとして使っているうえ、
        # 技術文書の慣習なので、このサイトの読者には通じない。
        out.append('    <p class="card-permalink">'
                   '<a href="%s%s">この項目だけを開く</a></p>'
                   % (page_prefix, item_url(tab_id, item["id"])))
    out.append('  </article>')
    return "\n".join(out)


_TERMS = sorted(GLOSSARY, key=len, reverse=True)
_TAG = re.compile(r'(<[^>]+>)')



# 用語の説明に振る通し番号（aria-describedby の id に使う）
_TERM_N = [0]

def _mark_text(text):
    """地の文に出てくる用語すべてに印を付ける。
    左から順に走査し、付けた印の内側は見直さない。
    こうしないと、挿入した説明文の中の語にさらに印が付く。
    同じ位置で複数の語が当たるときは長いほうを採る
    （「突き上げ法」より「胸部突き上げ法」）。"""
    out = []
    pos = 0
    while pos < len(text):
        best = None
        for term in _TERMS:
            idx = text.find(term, pos)
            if idx == -1:
                continue
            if best is None or idx < best[0] or (idx == best[0] and len(term) > len(best[1])):
                best = (idx, term)
        if best is None:
            out.append(text[pos:])
            break
        idx, term = best
        out.append(text[pos:idx])
        # 説明は data-desc ではなく、実体のある要素に入れる。
        # data-desc は CSS の content で描けるだけで、
        # アクセシビリティAPIには何も渡らない。
        # tabindex で止まるのに何も読まれない状態だった。
        _TERM_N[0] += 1
        did = "gl%d" % _TERM_N[0]
        out.append('<span class="term" tabindex="0" role="button"'
                   ' aria-describedby="%s">%s'
                   '<span class="term-desc" id="%s" role="tooltip">%s</span>'
                   '</span>'
                   % (did, term, did, esc(GLOSSARY[term])))
        pos = idx + len(term)
    return "".join(out)


def annotate(html, seen=None):
    """用語に、マウスオーバーで1行説明が出る印を付ける。
    見出し（項目名、サブタイトル、チェックの見出し、表の左列）には付けない。
    タグの内側（属性値）にも触れない。"""
    if not html:
        return html
    parts = _TAG.split(html)
    for i, part in enumerate(parts):
        if part.startswith("<"):
            continue
        parts[i] = _mark_text(part)
    return "".join(parts)


COLORS = ["mint", "peach", "sky", "lemon", "grape", "pink"]


def tab_icon(tab):
    """タブの絵。assets/img/tab/<id>.jpg があればそれを使い、
    無ければ絵文字のまま出す。画像を1枚ずつ作っていくあいだも、ビルドが通るように。

    alt は空にする。すぐ隣に月齢のラベルがあるので、
    読み上げで同じことを二度言わせない。"""
    path = "assets/img/tab/%s.jpg" % tab["id"]
    if os.path.exists(os.path.join(ROOT, path)):
        return '<img class="tab-icon" src="%s" alt="" width="36" height="36">' % asset(path)
    return '<span class="tab-emoji">%s</span>' % tab["emoji"]


def render_tab_nav():
    rows = []
    for i, t in enumerate(TABS):
        active = " is-active" if i == 0 else ""
        sel = "true" if i == 0 else "false"
        rows.append(
            '    <button class="tab%s" role="tab" aria-selected="%s" tabindex="%s"'
            ' aria-controls="%s" id="tab-%s" data-tab="%d">\n'
            '      %s'
            '<span class="tab-label">%s</span>'
            '<span class="tab-sub">%s</span>\n    </button>'
            % (active, sel, "0" if i == 0 else "-1", t["id"], t["id"], i,
               tab_icon(t), esc(t["label"]), esc(t["sub"])))
    return "\n".join(rows)


def render_toc(tab):
    """目次は、本文と同じグループの区切りで出す。
    26項目を平らに並べると、流し見で全体をつかめなくなる。"""
    total = sum(len(g["items"]) for g in tab["groups"])
    blocks = []
    for g in tab["groups"]:
        links = []
        for item in g["items"]:
            links.append('        <li><a href="#%s"><span class="toc-title">%s</span>'
                         '<span class="toc-sub">%s</span></a></li>'
                         % (item["id"], esc(item["title"]), esc(item.get("sub", ""))))
        blocks.append('      <div class="toc-group">\n'
                      '        <h4>%s<span class="toc-count">%d</span></h4>\n'
                      '        <ul>\n%s\n        </ul>\n      </div>'
                      % (esc(g["name"]), len(g["items"]), "\n".join(links)))
    return ('  <nav class="toc" aria-label="このタブの目次">\n'
            '    <h3>このページの項目（%d）</h3>\n%s\n  </nav>'
            % (total, "\n".join(blocks)))


def render_panel(i, tab):
    hidden = "" if i == 0 else " hidden"
    active = " is-active" if i == 0 else ""
    # tabindex="0" を付けて、タブを切り替えたあとに
    # 読み上げの位置をここへ移せるようにする（app.js の activate）。
    out = ['<section class="panel%s" id="%s" role="tabpanel" aria-labelledby="tab-%s"'
           ' tabindex="0"%s>' % (active, tab["id"], tab["id"], hidden)]
    out.append('  <div class="panel-intro">')
    out.append('    <h2 class="panel-title">%s <small>%s</small></h2>'
               % (esc(tab["title"]), esc(tab["subtitle"])))
    out.append('    <p class="panel-lead">%s</p>' % tab["lead"])
    out.append('  </div>')
    out.append(render_toc(tab))
    n = 0
    for g in tab["groups"]:
        out.append('  <h3 class="group-title"><span>%s</span></h3>' % esc(g["name"]))
        for item in g["items"]:
            out.append(render_item(item, COLORS[n % len(COLORS)], tab["id"]))
            n += 1
    out.append('</section>')
    return "\n".join(out)


def render_jsonld():
    """検索エンジン向けの構造化データ。

    書いてよいのは、ページに実際に書いてあることだけ。
    発行者や著者を名乗れる法人がないので、publisher と author は入れない。
    入れないほうがリッチリザルトに出にくくなるが、
    出すために実体のないものを名乗るほうが悪い。
    """
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": SITE_URL + "#website",
                "url": SITE_URL,
                "name": SITE_TITLE,
                "description": SITE_DESC,
                "inLanguage": "ja",
            },
            {
                "@type": "WebPage",
                "@id": SITE_URL + "#webpage",
                "url": SITE_URL,
                "name": "%s｜%s" % (SITE_TITLE, SITE_TAGLINE),
                "description": SITE_DESC,
                "inLanguage": "ja",
                "isPartOf": {"@id": SITE_URL + "#website"},
                "dateModified": UPDATED,
                "isAccessibleForFree": True,
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)



# color-scheme を only light にして、ブラウザ側の自動ダーク変換を断る。
# イラストは119枚とも明るい背景のJPEGで、暗くできない。
# 文字と背景だけが暗くなると、光る長方形が並ぶ紙面になる。
ITEM_PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="only light">
<title>%(title)s｜%(site)s</title>
<meta name="description" content="%(desc)s">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<!-- フォントのCSSは、そのまま置くと描画を止める。Googleから返るまで1文字も
     出ないので、夜間のモバイル回線では待たされる。media を print にして
     読み込み、届いてから all に戻すと、本文が先に出る。
     JavaScript を切っている場合は noscript のほうが効く。
     ウェイトは 400/700/900 の3つ。500 は装飾的な小さい文字2か所だけだったので、
     400 で代替して1ウェイト分の転送をやめた。 -->
<link rel="preload" as="style"
      href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;700;900&display=swap">
<link rel="stylesheet" media="print" onload="this.media='all'"
      href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;700;900&display=swap">
<noscript><link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;700;900&display=swap"></noscript>
<link rel="stylesheet" href="%(css)s">
<link rel="icon" href="%(favicon_svg)s" type="image/svg+xml">
<link rel="icon" href="%(favicon_32)s" sizes="32x32" type="image/png">
<!-- ブラウザの上下の帯の色。端末を夜間モードにしている人には、
     ページは明るいままでも、枠だけ落とせる。
     ページ自体のダークモードは持たない（color-scheme: only light）が、
     これは矛盾しない。 -->
<meta name="theme-color" content="#FFD3BC" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#4A3B34" media="(prefers-color-scheme: dark)">
<link rel="canonical" href="%(url)s">
<meta property="og:type" content="article">
<meta property="og:site_name" content="%(site)s">
<meta property="og:title" content="%(title)s｜%(site)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(url)s">
<meta property="og:image" content="%(og_image)s">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
%(jsonld)s
</script>
</head>
<body class="itempage">

<header class="itemhead">
  <p class="tabs-emergency"><a href="#emergency"><span aria-hidden="true">☎</span> 困ったときの番号</a></p>
  <p class="crumbs">
    <a href="%(root)s">%(site)s</a> ›
    <a href="%(root)s#%(tab_id)s">%(tab_label)s</a>
  </p>
  <p class="itemhead-updated">
    <time datetime="%(updated)s">%(updated_ja)s</time>の時点での最新情報を掲載しています。
  </p>
</header>

<main class="itemmain">
%(card)s

  <nav class="itemnav">
    <h2>%(tab_label)s のほかの項目</h2>
    <ul>
%(siblings)s
    </ul>
    <p class="itemnav-all"><a href="%(root)s#%(tab_id)s">%(tab_label)s をまとめて見る</a></p>
  </nav>
</main>

<section class="itememergency" id="emergency">
  <h2>困ったときの番号</h2>
  <p><strong>意識がない、呼吸がおかしい、顔色が青白い、けいれんしている。
  このときは相談ではなく、<a class="tel" href="tel:119">119番<span class="sr-only">に発信する</span></a>です。</strong></p>
  <ul>
    <li><a class="tel" href="tel:%%238000">#8000<span class="sr-only">に発信する</span></a>　子ども医療電話相談。夜間・休日に、小児科の医師・看護師へ相談できます</li>
    <li><a class="tel" href="tel:%%237119">#7119<span class="sr-only">に発信する</span></a>　救急安心センター。救急車を呼ぶか迷ったとき（全国42地域）</li>
    <li><a class="tel" href="tel:0727272499">072-727-2499<span class="sr-only">に発信する</span></a>　中毒110番・大阪（24時間）。飲み込んだかもしれないとき</li>
  </ul>
  <p class="itememergency-more"><a href="%(root)s#emergency">ほかの番号も見る</a></p>
</section>

<a class="to-emergency" href="#emergency">
  <span aria-hidden="true">☎</span> 緊急の番号
</a>

<footer class="itemfoot">
  <p>
    <strong>このページは「%(site)s」の1項目です。</strong>
    0〜3か月から10歳〜までの%(total)d項目を、公的機関の資料をもとにまとめています。
    <a href="%(root)s">全体を見る</a>
  </p>
  <p class="itemfoot-note">%(disclosure)s</p>
</footer>

<script src="%(js)s"></script>
</body>
</html>
"""


def render_item_jsonld(item, tab, url):
    """項目ページの構造化データ。記事として出す。"""
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": item["title"],
        "description": item.get("sub") or re.sub(r"<[^>]+>", "", item["lead"])[:110],
        "inLanguage": "ja",
        "dateModified": UPDATED,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "isPartOf": {"@type": "WebSite", "name": SITE_TITLE, "url": SITE_URL},
        "publisher": {"@type": "Organization", "name": SITE_TITLE, "url": SITE_URL},
        "breadcrumb": {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": SITE_TITLE, "item": SITE_URL},
                {"@type": "ListItem", "position": 2, "name": tab["title"],
                 "item": SITE_URL + "#" + tab["id"]},
                {"@type": "ListItem", "position": 3, "name": item["title"], "item": url},
            ],
        },
    }
    if item.get("figure"):
        data["image"] = SITE_URL + item["figure"][0]
    return json.dumps(data, ensure_ascii=False, indent=2)


def _relink_card(html, own_id, root):
    """カードの中の同一ページ前提のリンクを、項目ページから届く形に直す。

    カードはトップページ用に組み立ててあるので、「#policy」のような
    フッターへのリンクや、ほかの項目への相互参照が入っている。
    項目ページにはその行き先が無いため、押しても何も起きない。
    自分自身を指すリンク（見出しのアンカー）だけは、そのまま残す。"""
    def fix(m):
        target = m.group(1)
        if target == own_id:
            return m.group(0)
        return 'href="%s#%s"' % (root, target)
    return re.sub(r'href="#([^"]+)"', fix, html)


def write_item_pages():
    """項目ごとのページを書き出す。

    トップページは月齢別に見渡すためのもので、これはその逆。
    「ベビーゲート 階段上」のように、1つのことを調べて来た人が着地する。
    本文はトップと同じ render_item を使うので、二重に持たない。
    """
    root = item_page_prefix()
    n = 0
    for tab in TABS:
        items = [it for g in tab["groups"] for it in g["items"]]
        for idx, item in enumerate(items):
            url = SITE_URL + item_url(tab["id"], item["id"])
            sib = []
            for other in items:
                if other["id"] == item["id"]:
                    continue
                sib.append('      <li><a href="%s%s">%s</a></li>'
                           % (root, item_url(tab["id"], other["id"]), esc(other["title"])))
            desc = item.get("sub") or re.sub(r"<[^>]+>", "", item["lead"])
            doc = ITEM_PAGE % {
                "title": esc(item["title"]),
                "site": SITE_TITLE,
                "desc": esc(desc[:115]),
                "url": url,
                "root": root,
                "tab_id": tab["id"],
                "tab_label": esc(tab["title"]),
                "updated": UPDATED,
                "updated_ja": _updated_ja(),
                "og_image": (SITE_URL + item["figure"][0]) if item.get("figure")
                            else SITE_URL + "assets/og.png",
                "jsonld": render_item_jsonld(item, tab, url),
                # 図のパスは assets/ からの相対なので、2階層分の「../」を足す
                # 項目ページでは、その1枚が最初の画面に入る。遅延読み込みに
                # すると、いちばん見たい図が1往復ぶん遅れて出る。
                # 図のパスは assets/ からの相対なので、2階層分の「../」を足す。
                # src= だけでなく srcset= も直す。<picture> の WebP は
                # srcset で指すので、src だけ直すと WebP が404になり、
                # 静かに JPEG に落ちる（表示は出るので気づきにくい）。
                "card": _relink_card(
                    render_item(item, COLORS[idx % len(COLORS)],
                                eager_figure=True)
                    .replace('src="assets/', 'src="%sassets/' % root)
                    .replace('srcset="assets/', 'srcset="%sassets/' % root)
                    .replace(' assets/img/', ' %sassets/img/' % root),
                    item["id"], root),
                "siblings": "\n".join(sib),
                "total": sum(len(g["items"]) for t in TABS for g in t["groups"]),
                "disclosure": esc(DISCLOSURE),
                "css": asset("assets/style.css", root),
                "js": asset("assets/app.js", root),
                "favicon_svg": asset("assets/favicon.svg", root),
                "favicon_32": asset("assets/favicon-32.png", root),
            }
            d = os.path.join(ROOT, tab["id"], item["id"])
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
                f.write(doc)
            n += 1
    return n


def write_sitemap_and_robots():
    """sitemap.xml と robots.txt を書き出す。

    トップページと、項目ごとのページを全部載せる。
    タブは URL を持たない（ハッシュで切り替える）ので、タブごとには出さない。
    """
    urls = [SITE_URL]
    for tab in TABS:
        for g in tab["groups"]:
            for it in g["items"]:
                urls.append(SITE_URL + item_url(tab["id"], it["id"]))
    body = "".join(
        '  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n  </url>\n' % (u, UPDATED)
        for u in urls)
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + body + '</urlset>\n')
    robots = ("User-agent: *\n"
              "Allow: /\n"
              "\n"
              "Sitemap: %ssitemap.xml\n" % SITE_URL)
    for name, body in (("sitemap.xml", sitemap), ("robots.txt", robots)):
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
            f.write(body)


def render_footer():
    seen, lis = set(), []
    for t in TABS:
        for g in t["groups"]:
            for item in g["items"]:
                for key, _ in item["sources"]:
                    if key in seen:
                        continue
                    seen.add(key)
                    title, url = SRC[key]
                    lis.append('      <li><a href="%s" target="_blank" rel="noopener">%s<span class="sr-only">（新しいタブで開きます）</span></a></li>'
                               % (url, esc(title)))
    return "\n".join(lis)


def _updated_ja():
    """UPDATED（YYYY-MM-DD）を「2026年10月29日」の形にする。"""
    y, m, d = UPDATED.split("-")
    return "%d年%d月%d日" % (int(y), int(m), int(d))


def _hero_updated():
    """ヒーローの掲載内容の時点。UPDATED が None のあいだは何も出さない。"""
    if not UPDATED:
        return ""
    return ('    <p class="hero-updated">\n'
            '      <time datetime="%s">%s</time>の時点での最新情報を掲載しています。\n'
            '    </p>' % (UPDATED, _updated_ja()))


def _footer_updated(total):
    """フッターの掲載内容の時点。UPDATED が None のあいだは何も出さない。"""
    if not UPDATED:
        return ""
    return ('    <p>\n'
            '      <strong>古くならないことが、このサイトの価値です。</strong><br>\n'
            '      制度や指針が改訂されると、正しい対策が変わります。\n'
            '      公的機関の資料%d件を見直し、変わった時点で書き直しています。\n'
            '      最新の更新は<strong><time datetime="%s">%s</time></strong>。\n'
            '    </p>\n'
            '    <p>\n'
            '      全体の総点検はときどき、項目を直すときはその項目の出典に当たり直しています。\n'
            '      公的機関のページは、URLが変わらないまま中身が差し替わることもあります。\n'
            '      気になる点は、各項目の「この項目の根拠」から出典に当たってください。\n'
            '    </p>' % (len(SRC), UPDATED, _updated_ja()))


def _duplicate_keys():
    """レジストリの重複キーを見つける。

    Python の dict リテラルは同じキーを黙って上書きするので、
    登録したつもりの出典や商品が、気づかないうちに消える。
    ソースを文字列として読んで、dict ごとに重複を数える。
    """
    import re
    errors = []
    for name in ("sources", "products", "glossary"):
        path = os.path.join(SRC_DIR, name + ".py")
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        blocks = re.split(r"^(\w+)\s*=\s*\{", text, flags=re.M)
        for i in range(1, len(blocks), 2):
            dict_name, body = blocks[i], blocks[i + 1].split("\n}")[0]
            seen = {}
            for key in re.findall(r'^    "([^"]+)":', body, re.M):
                seen[key] = seen.get(key, 0) + 1
            for key, count in sorted(seen.items()):
                if count > 1:
                    errors.append("%s.py の %s にキー \"%s\" が %d 回ある（後ろが前を消します）"
                                  % (name, dict_name, key, count))
    return errors


def _duplicate_item_keys():
    """content.py の項目 dict に、同じキーを2回書いていないか見つける。

    項目の dict でも Python は後ろのキーで前を黙って上書きする。
    "figure": None と書いたあとに実体を書き足すと、たまたま後ろが勝って
    表示は正しくなるが、順序が入れ替わった瞬間に図が消える。
    項目は「{"id": ...」で始まり「]},」か「)]},」で終わる書き方に揃えているので、
    "id" の行から次の "id" の行までを1項目として、行頭のキーを数える。
    """
    import re
    path = os.path.join(SRC_DIR, "content.py")
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    errors, start, item_id = [], None, None

    def flush(end):
        if start is None:
            return
        seen = {}
        for line in lines[start:end]:
            m = re.match(r'\s*"(\w+)":', line)
            if m:
                seen[m.group(1)] = seen.get(m.group(1), 0) + 1
        for key, count in sorted(seen.items()):
            if count > 1:
                errors.append('content.py の項目 "%s" にキー "%s" が %d 回ある'
                              '（後ろが前を消します）' % (item_id, key, count))

    for i, line in enumerate(lines):
        # タブの区切りでいったん閉じる。閉じないと、タブ末尾の項目が
        # 次のタブの lead を自分のキーとして数えてしまう。
        if line.startswith("TABS.append("):
            flush(i)
            start, item_id = None, None
            continue
        m = re.match(r'\s*\{"id": "([\w-]+)"', line)
        if m:
            flush(i)
            start, item_id = i, m.group(1)
    flush(len(lines))
    return errors


# 項目 dict に書いてよいキー。ここに無いキーは、たいてい綴りの間違いか、
# 描画されない名前（"callout2" など）。黙って無視されると気づけないので止める。
ITEM_KEYS = {
    "id", "chip", "title", "sub", "lead", "figure", "figure2",
    "table", "callout", "callouts", "steps", "checks", "goods", "goods_kind", "sources",
}


def _unknown_item_keys():
    errors = []
    for t in TABS:
        for g in t["groups"]:
            for item in g["items"]:
                for k in sorted(set(item) - ITEM_KEYS):
                    errors.append('%s / %s: 項目に知らないキー "%s" がある'
                                  % (t["label"], item.get("id", "?"), k))
    return errors


def _duplicate_source_urls():
    """同じURLを2つのキーで登録していないか。

    同じ資料に別名のキーが生えると、片方だけ直したときに
    同じ出典の説明が2通りになる。実際に、消費者庁の窒息の注意喚起が
    caa_food_choking と caa_choking_food の2つで登録されていた。
    """
    seen, errors = {}, []
    for k, (title, url) in SRC.items():
        u = re.sub(r"index\.html?$", "", url).rstrip("/")
        if u in seen:
            errors.append('sources.py: 同じURLが2つのキーで登録されている "%s" と "%s"\n       %s'
                          % (seen[u], k, url))
        else:
            seen[u] = k
    return errors


def _missing_webp():
    """WebP が作られていない図版を知らせる。

    無くてもビルドは通り、JPEG で表示されるので壊れない。ただし
    1枚あたり4〜5倍の通信量になるので、気づかずに放置したくない。
    src/make_webp.sh を走らせると作られる。"""
    missing = []
    for tab in TABS:
        for group in tab["groups"]:
            for item in group["items"]:
                for key in ("figure", "figure2"):
                    fig = item.get(key)
                    if not fig:
                        continue
                    src = fig[0]
                    if not src.endswith(".jpg"):
                        continue
                    for w in (1000, 1400):
                        cand = "%s-%d.webp" % (src[:-4], w)
                        if not os.path.exists(os.path.join(ROOT, cand)):
                            missing.append(cand)
    if missing:
        return ["WebP が無い図版が %d 件ある（src/make_webp.sh で作れる）: %s"
                % (len(missing), ", ".join(missing[:3]) + ("…" if len(missing) > 3 else ""))]
    return []


def _tags_in_escaped_fields():
    """そのまま画面に出る欄に、HTMLタグが書かれていないかを見る。

    チェックの見出しと出典の要約は esc() を通すので、<strong> と書くと
    「&lt;strong&gt;」という文字として読者に見える。本文（annotate）は
    タグを通すため、同じ項目の中で片方だけ効く形になり、気づきにくい。"""
    errors = []
    for tab in TABS:
        for group in tab["groups"]:
            for item in group["items"]:
                where = "%s / %s" % (tab["title"], item["id"])
                for _, title, _body in item.get("checks") or []:
                    if "<" in title:
                        errors.append("%s: チェックの見出しにタグが入っている（"
                                      "この欄は文字として出る）: %s" % (where, title[:40]))
                for _key, note in item.get("sources") or []:
                    if "<" in note:
                        errors.append("%s: 出典の要約にタグが入っている（"
                                      "この欄は文字として出る）: %s" % (where, note[:40]))
    return errors


def validate():
    """本文を書くときに踏みやすい間違いを、ビルド時に止める。"""
    from products import PRODUCTS
    errors, warnings = [], []
    errors.extend(_duplicate_keys())
    errors.extend(_duplicate_item_keys())
    errors.extend(_tags_in_escaped_fields())
    warnings.extend(_missing_webp())
    from products import AWARDS, CREDS, NOTES, STAPLES
    for k in sorted(set(AWARDS) - set(PRODUCTS)):
        errors.append('products.py: 受賞 "%s" が、登録のない商品を指している' % k)
    errors.extend(_duplicate_source_urls())
    # 同じ ASIN を別のキーで二重登録すると、同じ商品が2行並ぶ。
    # 競合を足しているときに実際にやった（repel_kincho / repel_kincho200）。
    seen_asin = {}
    for k, (asin, _name) in PRODUCTS.items():
        if asin in seen_asin:
            errors.append('products.py: 同じ ASIN %s を "%s" と "%s" が指している'
                          % (asin, seen_asin[asin], k))
        seen_asin[asin] = k
    errors.extend(_unknown_item_keys())
    for t in TABS:
        for g in t["groups"]:
            for item in g["items"]:
                where = "%s / %s" % (t["label"], item["id"])
                goods = item.get("goods")
                if goods:
                    # 下限3、上限6。3は下限であって目標ではない。
                    # 種類ごとに1つずつ置いて3つ、という埋め方をしないこと。
                    if len(goods["picks"]) < 3:
                        errors.append("%s: グッズは3件以上にする（現在 %d 件）"
                                      % (where, len(goods["picks"])))
                    elif len(goods["picks"]) > 6:
                        errors.append("%s: グッズは6件までにする（現在 %d 件）"
                                      % (where, len(goods["picks"])))
                    # 選び方のポイントは「何を基準に選ぶか」で、商品1件ごとの説明ではない。
                    # 商品ごとの違いは products.py の NOTES（カードに出る一言）が担う。
                    # 以前は商品の件数以上を求めていたが、商品を最大6件に増やしたときに
                    # 基準を水増しさせる形になったのでやめた。下限は3。
                    if len(goods["points"]) < 3:
                        warnings.append("%s: 選び方のポイントが3件未満（%d 件）"
                                        % (where, len(goods["points"])))
                    for k in goods["picks"]:
                        if k not in PRODUCTS:
                            errors.append("%s: 未登録の商品キー %s" % (where, k))
                        # 受賞バッジも導入実績バッジも一言も無いと、その行だけ空きができる。
                        elif not (AWARDS.get(k) or CREDS.get(k)
                                  or STAPLES.get(k) or NOTES.get(k)):
                            warnings.append("%s: 商品 %s にバッジも一言も無い"
                                            % (where, k))

                # 受賞の登録が、存在しない商品を指していないか。
                # 商品を差し替えたときに、受賞だけ残ると古い情報が出る。
                figs = [item.get("figure"), item.get("figure2")]
                for fig in figs:
                    if not fig:
                        continue
                    src = fig[0]
                    if not os.path.exists(os.path.join(ROOT, src)):
                        errors.append("%s: 画像がない %s" % (where, src))
                    kind = fig[3] if len(fig) > 3 else None
                    if kind not in (None, "grid", "grid6", "compare", "compare-ok-left"):
                        errors.append("%s: 図の種類が不正 %r" % (where, kind))
                if not item.get("sub"):
                    errors.append("%s: サブタイトルがない" % where)
                if not item.get("sources"):
                    errors.append("%s: 根拠がない" % where)
                seen_src = set()
                for key, _ in item["sources"]:
                    if key not in SRC:
                        errors.append("%s: 未登録の出典キー %s" % (where, key))
                    # 同じ出典を1項目に2回書くと、「この項目の根拠」に二重に出る。
                    if key in seen_src:
                        errors.append("%s: 出典キー %s が重複している" % (where, key))
                    seen_src.add(key)
    # どこからも参照していない出典は、消し忘れか、埋めていない内容の穴である。
    # 受賞制度と第三者評価の参照先は、項目ではなくフッターから使うので除く。
    used_src = set(k for t in TABS for g in t["groups"] for i in g["items"]
                   for k, _ in i.get("sources", []))
    FOOTER_SRC = {"mothers_selection", "tamahiyo_award", "kids_design",
                  "good_design", "caa_special_use",
                  "kids_design_18"}
    for k in sorted(set(SRC) - used_src - FOOTER_SRC):
        warnings.append("出典 %s がどこからも参照されていない" % k)
    if errors:
        raise SystemExit("ビルド中止:\n  " + "\n  ".join(errors))
    if warnings:
        print("あとで直す:\n  " + "\n  ".join(warnings))


def build():
    validate()
    total = sum(len(g["items"]) for t in TABS for g in t["groups"])
    panels = "\n\n".join(render_panel(i, t) for i, t in enumerate(TABS))
    # color-scheme を only light にして、ブラウザ側の自動ダーク変換を断る。
    # イラストは119枚とも明るい背景のJPEGで、暗くできない。
    # 文字と背景だけが暗くなると、光る長方形が並ぶ紙面になる。
    doc = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="only light">
<title>%(title)s｜%(tagline)s</title>
<meta name="description" content="%(desc)s">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<!-- フォントのCSSは、そのまま置くと描画を止める。Googleから返るまで1文字も
     出ないので、夜間のモバイル回線では待たされる。media を print にして
     読み込み、届いてから all に戻すと、本文が先に出る。
     JavaScript を切っている場合は noscript のほうが効く。
     ウェイトは 400/700/900 の3つ。500 は装飾的な小さい文字2か所だけだったので、
     400 で代替して1ウェイト分の転送をやめた。 -->
<link rel="preload" as="style"
      href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;700;900&display=swap">
<link rel="stylesheet" media="print" onload="this.media='all'"
      href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;700;900&display=swap">
<noscript><link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;700;900&display=swap"></noscript>
<link rel="stylesheet" href="%(css)s">
<link rel="icon" href="%(favicon_svg)s" type="image/svg+xml">
<link rel="icon" href="%(favicon_32)s" sizes="32x32" type="image/png">
<link rel="icon" href="%(favicon_16)s" sizes="16x16" type="image/png">
<link rel="apple-touch-icon" href="%(apple_icon)s">
<!-- ブラウザの上下の帯の色。端末を夜間モードにしている人には、
     ページは明るいままでも、枠だけ落とせる。
     ページ自体のダークモードは持たない（color-scheme: only light）が、
     これは矛盾しない。 -->
<meta name="theme-color" content="#FFD3BC" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#4A3B34" media="(prefers-color-scheme: dark)">
<link rel="canonical" href="%(site_url)s">
<meta property="og:type" content="website">
<meta property="og:site_name" content="%(title)s">
<meta property="og:title" content="%(title)s｜%(tagline)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(site_url)s">
<meta property="og:image" content="%(og_image)s">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="赤ちゃんとこどもの安全ノート。0〜3か月から10歳〜までの月齢・年齢タブ">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title)s｜%(tagline)s">
<meta name="twitter:description" content="%(desc)s">
<meta name="twitter:image" content="%(og_image)s">
<script type="application/ld+json">
%(jsonld)s
</script>
</head>
<body>

<header class="hero">
  <div class="blob blob-a"></div>
  <div class="blob blob-b"></div>
  <div class="blob blob-c"></div>
  <div class="hero-inner">
    <p class="hero-eyebrow">%(tagline)s</p>
    <h1 class="hero-title">赤ちゃんとこどもの<br>安全ノート</h1>
    <p class="hero-lead">
      赤ちゃんとこどもの安全対策は、どの資料にも全部は載っていません。
      あちこちの情報源を行き来するうちに説明が食い違い、どれを信じればいいのか迷いがちです。
      このサイトは、公的機関が出している情報を月齢・年齢ごとに網羅して、
      <strong>%(total)d項目</strong>を同じ組み立てで並べました。
      多くの項目には、危ない例とよい例を並べた図解が付いています。
    </p>
    <div class="search">
      <label class="sr-only" for="q">項目を探す</label>
      <input type="search" id="q" class="search-input" autocomplete="off"
             placeholder="探す（例：ボタン電池、浴槽、ヘルメット）">
      <ul class="search-results" id="search-results" role="listbox" aria-label="検索結果" hidden></ul>
    </div>
    <div class="hero-badges">
      <span class="badge badge-mint">出典は公的機関</span>
      <span class="badge badge-peach">図解つき</span>
      <span class="badge badge-sky">月齢べつに網羅</span>
    </div>
%(hero_updated)s
  </div>
  <div class="hero-wave" aria-hidden="true">
    <svg viewBox="0 0 1440 120" preserveAspectRatio="none"><path d="M0,64 C180,110 360,10 540,42 C720,74 900,118 1080,96 C1260,74 1380,30 1440,20 L1440,120 L0,120 Z"></path></svg>
  </div>
</header>

<nav class="tabs" aria-label="月齢で選ぶ">
  <p class="tabs-emergency"><a href="#emergency"><span aria-hidden="true">☎</span> 困ったときの番号</a></p>
  <div class="tabs-inner" role="tablist">
%(tabnav)s
  </div>
</nav>

<main>

%(panels)s

</main>

<footer class="site-footer">
  <div class="footer-inner">

    <section class="emergency" id="emergency">
      <h2>困ったときの番号</h2>
      <p class="emergency-lead"><strong>意識がない、呼吸がおかしい、顔色が青白い、けいれんしている。
      このときは相談ではなく、<a class="tel" href="tel:119">119番<span class="sr-only">に発信する</span></a>です。</strong></p>
      <ul>
        <li><a class="tel" href="tel:%%238000">#8000<span class="sr-only">に発信する</span></a>　子ども医療電話相談（厚生労働省）<br>
            夜間・休日に、小児科の医師・看護師へ電話で相談できます。実施時間帯は都道府県によって違います。</li>
        <li><a class="tel" href="tel:%%237119">#7119<span class="sr-only">に発信する</span></a>　救急安心センター事業（消防庁）<br>
            救急車を呼ぶか迷ったとき。医師・看護師・救急救命士から助言を受けられます。全国42地域での実施なので、
            お住まいの地域で使えるかを先に確かめてください。</li>
        <li><strong>中毒110番</strong>（日本中毒情報センター）<br>
            大阪 <a class="tel" href="tel:0727272499">072-727-2499<span class="sr-only">に発信する</span></a>（24時間）／
            つくば <a class="tel" href="tel:0298529999">029-852-9999<span class="sr-only">に発信する</span></a>（9〜21時）／
            たばこ専用 <a class="tel" href="tel:0727269922">072-726-9922<span class="sr-only">に発信する</span></a>（自動音声・24時間）</li>
        <li><a class="tel" href="tel:118">118番<span class="sr-only">に発信する</span></a>　海上保安庁<br>海でのもしものとき。川や湖は119番です。</li>
        <li><a class="tel" href="tel:%%239110">#9110<span class="sr-only">に発信する</span></a>　警察相談専用電話（警察庁）<br>
            110番するほどではないが不安なとき。発信地を管轄する都道府県警察本部につながります。</li>
        <li><a class="tel" href="tel:188">188<span class="sr-only">に発信する</span></a>　消費者ホットライン<br>無断課金や通信販売のトラブル。</li>
        <li><a class="tel" href="tel:0120078310">0120-0-78310<span class="sr-only">に発信する</span></a>　24時間子供SOSダイヤル（文部科学省）<br>いじめや学校のこと。24時間。</li>
        <li><a class="tel" href="tel:171">171<span class="sr-only">に発信する</span></a>　災害用伝言ダイヤル（総務省）<br>
            毎月1日・15日、正月三が日、防災週間などの体験利用日に、平時でも試せます。</li>
      </ul>
      <p class="emergency-note">紙に書いて、電話のそばに貼っておくと、探す時間が要りません。</p>
    </section>

    <h2>このサイトについて</h2>
    <p>
      日本の公的機関（こども家庭庁・消費者庁・東京都）および専門学会（日本小児科学会・日本小児整形外科学会・米国小児科学会）が
      公開している情報をもとにまとめた、保護者向けの安全ガイドです。
      各項目の「この項目の根拠」から、出典のページを直接たどれるようにしています。
    </p>
%(footer_updated)s
    <p class="disclaimer">
      掲載内容は一般的な情報であり、個別の診断や指導に代わるものではありません。
      お子さんの様子に気になる点があるときは、かかりつけの小児科医や、
      お住まいの市区町村の母子保健担当窓口・保健センターにご相談ください。
      緊急時は迷わず119番に通報してください。
    </p>
    <h3 id="policy-items">何を載せるかの決め方</h3>
    <p>
      このサイトは、<strong>その時期に気をつけることを一度に見渡せるようにする</strong>ために作っています。
      安全対策は多くの機関がそれぞれの担当範囲について公開していて、ひとつにまとまっていません。
      あちこちを行き来して、どれを信じればよいか決められなくなる
      ── その状態をなくすことが目的です。
      だから<strong>選り抜くのではなく、載せられるものはできる限り載せる</strong>方針を採っています。
    </p>
    <p>載せるかどうかは、次の2つだけで決めています。</p>
    <ol class="policy">
      <li><strong>日本の公的機関か専門学会の一次資料に、根拠があること。</strong>
        こども家庭庁、消費者庁、国民生活センター、厚生労働省、環境省、警察庁、東京都などの資料と、
        日本小児科学会の傷害速報（Injury Alert）をはじめとする学会の資料です。
        商業記事やSNSで見かけただけのものは載せません。
        海外の資料で補うときは、日本の学会の記述と突き合わせ、
        指示の分かれるところでは<strong>弱いほうを採りません</strong>。</li>
      <li><strong>その月齢・年齢に実際に起こること。</strong>
        事故の報告がその時期に集中しているか、その時期の発達でできるようになることかで判断します。
        別の時期の話は、その時期のタブに置きます。</li>
    </ol>
    <p>
      この2つを満たすものは、<strong>書きにくい内容でも落としません。</strong>
      受診をすすめるもの、よく売られている製品を使わないようすすめるもの、
      「よかれと思ってしていること」を否定するものも、同じように載せています。
      特定の育児観に合う情報だけを採るということをしていません。
    </p>
    <p class="disclaimer">
      <strong>それでも、漏れはあります。</strong>
      新しい注意喚起は次々に出ますし、公的機関の資料そのものが改訂されます。
      掲載していない対策が「安全だから省いた」という意味ではありません。
      まだ拾えていないだけ、ということがあります。
      各項目に出典のリンクを付けてあるのは、書いてあることを確かめるためだけでなく、
      <strong>書いていないことに気づくため</strong>でもあります。
      気になる点は、出典のページから先をたどってください。
    </p>
    <p>
      <strong>誤りや、抜けている対策にお気づきの点があれば、
      <a href="%(form)s" target="_blank" rel="noopener">お問い合わせフォーム<span class="sr-only">（新しいタブで開きます）</span></a>からお知らせください。</strong>
      出典に当たり直したうえで、必要があれば修正します。修正したときは、掲載内容の時点を更新します。
      なお、個別の健康相談にはお答えできません。
      お子さんの様子に気になる点があるときは、かかりつけの小児科医か、
      お住まいの市区町村の母子保健担当窓口・保健センターにご相談ください。
    </p>
    <h3 id="policy">グッズの選び方の方針</h3>
    <p>商品は、次の順で選んでいます。</p>
    <ol class="policy">
      <li><strong>その項目の安全上の根拠を満たすこと。</strong>
        たとえば「脚がM字に曲げられる」ことが根拠なら、それを満たす構造の製品を選びます。
        各項目の「グッズの選び方」に、その基準を書いています。</li>
      <li><strong>安全規格のマークがあること。</strong>
        SGマーク、CEマーク、IHDI認証（股関節）、桜マーク（国土交通省型式承認・ライフジャケット）、
        STマーク（おもちゃ）、一般医療機器の届出（ベビーセンサー）など。<br>
        <strong>ベビーベッドとライターは、法律でPSCマークが義務づけられた「特定製品」です。</strong>
        マークのないものは販売できません
        （<a href="%(caa_psc_start)s" target="_blank" rel="noopener">消費者庁<span class="sr-only">（新しいタブで開きます）</span></a>）。
        ベビーカーと乳幼児用ベッドガードも、順次この対象になります。</li>
      <li><strong>定番として長く売られていること。</strong>
        廃番になりにくく、使い方の情報も見つけやすいためです。</li>
      <li><strong>第三者の評価があること。</strong>
        <a href="%(mothers_selection)s" target="_blank" rel="noopener">マザーズセレクション大賞<span class="sr-only">（新しいタブで開きます）</span></a>、
        <a href="%(tamahiyo_award)s" target="_blank" rel="noopener">たまひよ赤ちゃんグッズ大賞<span class="sr-only">（新しいタブで開きます）</span></a>、
        <a href="%(kids_design)s" target="_blank" rel="noopener">キッズデザイン賞<span class="sr-only">（新しいタブで開きます）</span></a>、
        <a href="%(good_design)s" target="_blank" rel="noopener">グッドデザイン賞<span class="sr-only">（新しいタブで開きます）</span></a>を参照しています。
        商品そのもの、または同じシリーズの別の型番が受賞したと確認できたものだけ、
        商品名の下に受賞を書いています。別の型番が受賞した場合は、その型番をかっこの中に書いています。
        メーカー別の集計で上位だったものは、紹介している商品と受賞対象が一致しないため書いていません。<br>
        賞ではなく、<strong>医療機関や保育施設で使われている実績</strong>や
        <strong>国の許可</strong>で選んだものには 🏥 のバッジを、
        <strong>広く使われている定番</strong>であるものには 📌 のバッジを付けています。
        定番のバッジには、メーカーが公表している累計販売数だけを書いています。</li>
    </ol>
    <h3 id="ads">広告について</h3>
    <p>
      <strong>このサイトには、広告枠を一切置いていません。</strong>
      バナーも、記事のあいだに差し込まれる広告も、追いかけてくる広告もありません。
      子どもの安全について調べているときに、関係のないものが目に入って読む手が止まるのは、
      このサイトの目的と正面からぶつかります。
    </p>
    <p>
      そのうえで、<strong>各項目の「グッズの選び方」のリンクだけは、アフィリエイトリンクです。</strong>
      ここから商品が購入されると、当サイトに収入が入ります。
      出典を1件ずつ開いて確かめ直す作業にも、公的機関の資料が改訂されたときに書き直す作業にも、
      手間と費用がかかります。それを続けるための費用に充てています。
    </p>
    <p>
      <strong>紹介する商品は、報酬額では選んでいません。</strong>
      高い商品のほうが収入は大きくなりますが、そちらを選ぶということをしていません。
      選んでいるのは、<a href="#policy-items">その項目の根拠として挙げた資料</a>が求める条件を
      満たす製品です。たとえば「脚をM字に曲げられること」が根拠なら、それを満たす構造のものを選びます。
      対象月齢の下限、安全規格のマーク、取扱説明書の記載を、商品ページで一つずつ確かめています。
      判断の基準は、各項目の「グッズの選び方」と、下の
      <a href="#policy">グッズの選び方の方針</a>に書いたとおりです。
    </p>
    <p>
      <strong>買わなくても、項目は完結します。</strong>
      道具で解決しない項目には商品を置いていませんし、
      置いてある項目でも、やることの本体はチェックリストのほうに書いてあります。
    </p>
    <p class="disclaimer">%(disclosure)s</p>
    <p class="disclaimer">
      <strong>紹介している商品を、当サイトが購入して試したわけではありません。</strong>
      上の方針にもとづき、公開されている仕様・取扱説明書・安全規格・第三者の評価から選んでいます。
      特定の商品の安全性を保証するものではありません。
      購入前に、対象月齢・体重と取扱説明書を必ずご確認ください。</p>
    <p class="disclaimer">
      受賞を示すバッジは、<strong>その商品そのものが受賞したと公式の受賞一覧で確認できたものだけ</strong>に付けています。
      同じブランドの別モデルが受賞した場合や、メーカー別の集計で上位だった場合は付けていません。
      そのため、バッジのない商品が劣るという意味ではありません。</p>
    <p class="disclaimer">
      Amazonアソシエイト運営規約により、価格・在庫・★評価・商品画像は掲載していません。
      これらは購入前にリンク先でご確認ください。</p>
    <h3 id="ai">このサイトは、AIで作っています</h3>
    <p>
      本文、出典の収集、イラストは、人の指示のもとで生成AI（Claude）が作成しています。
      作り方を隠さずに書いておくほうが、書かれている内容を確かめるときの助けになると考えています。
    </p>
    <p>
      <strong>AIを使っているのは、網羅するためです。</strong>
      赤ちゃんとこどもの安全対策は、こども家庭庁、消費者庁、国民生活センター、日本小児科学会、
      各自治体といった多くの機関が、それぞれの担当範囲について別々に公開しています。
      ひとつの資料にまとまっておらず、説明の粒度も用語もそろっていません。
      これを月齢ごとに集め直し、同じ形で並べ、1項目ごとに出典をたどれるようにする作業は、
      量としてはAIの得意な仕事です。
    </p>
    <p>
      <strong>集めたうえで、説明の形をそろえています。</strong>
      資料を行ったり来たりしていると、同じ対策が別の言葉で書かれていたり、
      ある資料では強く禁じられていることが別の資料では条件つきで認められていたりして、
      どれを採ればよいか決められなくなります。
      このサイトでは、どの項目も「何が起きるか」「何をするか」「その根拠」を同じ順に並べ、
      やることとやらないことを◯と×で示し、図解は左を危険な例、右を安全な例に統一しています。
      月齢のタブを選べば、その時期に関係するものだけが出ます。
      同じ対策について資料のあいだで記述が違うときは、強いほうの指示に合わせ、
      どちらの資料に何と書かれていたかを各項目の根拠に残しています。
    </p>
    <p>観点を分けて、複数のAIに相互レビューさせています。ひとつの項目に対して、</p>
    <ol class="policy">
      <li><strong>項目が足りているか</strong>
        ── 公的機関の資料を当たり直し、その月齢に必要なのに書かれていない項目を探します。</li>
      <li><strong>出典と本文が合っているか</strong>
        ── 出典のURLを1件ずつ開き、本文の記述を一文ずつ突き合わせます。
        出典より断定的になっていないか、数値や条件がずれていないかを見ます。</li>
      <li><strong>日本語として読めるか</strong>
        ── 回りくどい言い方、意味のない一文、その月齢の赤ちゃんには起こりえない前提を探します。</li>
      <li><strong>図解と商品が本文と合っているか</strong>
        ── イラストを1枚ずつ見て、対象年齢や発達段階と矛盾していないかを確かめます。</li>
    </ol>
    <p>
      別々の観点から独立に見ると、同じ箇所が複数の観点から指摘されることがあります。
      そこは構造的に間違っていることが多く、直す優先順位の手がかりになります。
      観点どうしで判断が食い違ったときは、原典に戻って確かめます。
    </p>
    <p class="disclaimer">
      <strong>この工程でも、誤りはなくなりません。</strong>
      生成AIは、もっともらしい誤りを作ります。実際にこのサイトでも、
      公的機関の資料にない数値を書いていた箇所、
      ある項目で薦めた製品を次の項目で否定していた箇所、
      その月齢の赤ちゃんにはできない動作を前提にしていた箇所が、レビューで見つかっています。
      だからこそ、<strong>全項目に出典のリンクを付けています。</strong>
      書かれていることを信じるかどうかは、出典を開いて読者が判断できる形にしてあります。
    </p>
    <p>
      <strong>項目に過不足がないかの最終的な判断は、人が行っています。</strong>
      AIに任せているのは、資料を集めること、同じ形に整えること、
      そして書いたものを別の観点から点検することです。
      何を載せるかの基準そのものは
      <a href="#policy-items">「何を載せるかの決め方」</a>に書いたとおりで、
      その基準に照らして足りないもの・余計なものがないかを、人が確かめています。
    </p>
    <h3 id="disclaimer">免責事項</h3>
    <p>
      このサイトは、公的機関が公開している情報を、月齢・年齢ごとに並べ替えてまとめたものです。
      <strong>掲載内容は一般的な情報であり、個別の状況に対する診断・指導・助言ではありません。</strong>
      お子さんの体質、発達の度合い、住まいの作り、使っている製品によって、
      何が安全かは変わります。
    </p>
    <p>
      内容は、出典にあたって正確を期していますが、
      <strong>完全であること、誤りがないこと、最新であることを保証するものではありません。</strong>
      公的機関の資料は改訂され、URLも変わります。
      製品の仕様も、こちらが確かめた時点から変わることがあります。
    </p>
    <p>
      <strong>このサイトの情報を用いて行った判断や行動の結果について、
      運営者は責任を負いません。</strong>
      最終的な判断は、出典にあたったうえで、ご自身で行ってください。
      お子さんの様子に気になる点があるときは、かかりつけの小児科医や、
      お住まいの市区町村の母子保健担当窓口・保健センターにご相談ください。
      緊急時は、迷わず<strong>119番</strong>に通報してください。
    </p>
    <p>
      誤りを見つけられた場合は、
      <a href="%(form)s" target="_blank" rel="noopener">お問い合わせフォーム<span class="sr-only">（新しいタブで開きます）</span></a>
      からお知らせください。確認のうえ、直します。
    </p>
    <p class="disclaimer" id="about-author">
      このサイトは、子どもが生まれて退院した日に安全対策のまとまった資料が見つからなかったことから、
      公的機関の資料を月齢別に網羅し、1項目ずつ出典をたどれるようにしたもので、
      <strong>高橋 晶（Akira Takahashi）</strong>が運営しています。
    </p>
    <h3>主な出典</h3>
    <ul class="footer-sources">
%(sources)s
    </ul>
  </div>
</footer>

<a class="to-emergency" href="#emergency">
  <span aria-hidden="true">☎</span> 緊急の番号
</a>

<button type="button" class="to-toc" id="to-toc">
  <span aria-hidden="true">↑</span> 目次へ
</button>

<script src="%(js)s"></script>
</body>
</html>
""" % {"title": SITE_TITLE, "tagline": SITE_TAGLINE, "desc": SITE_DESC,
       "site_url": SITE_URL, "og_image": SITE_URL + "assets/og.png",
       "jsonld": render_jsonld(),
       "hero_updated": _hero_updated(), "footer_updated": _footer_updated(total),
       "total": total, "tabnav": render_tab_nav(), "panels": panels,
       "sources": render_footer(), "disclosure": DISCLOSURE, "form": FORM_URL,
       # 第三者評価と制度の参照先。直書きせず出典レジストリから引く。
       # 直書きだと link_check.py の対象から外れ、リンク切れに気づけない。
       "mothers_selection": SRC["mothers_selection"][1],
       "tamahiyo_award": SRC["tamahiyo_award"][1],
       "kids_design": SRC["kids_design"][1],
       "good_design": SRC["good_design"][1],
       "caa_psc_start": SRC["caa_psc_start"][1],
       "css": asset("assets/style.css"), "js": asset("assets/app.js"),
       "favicon_svg": asset("assets/favicon.svg"),
       "favicon_32": asset("assets/favicon-32.png"),
       "favicon_16": asset("assets/favicon-16.png"),
       "apple_icon": asset("assets/apple-touch-icon.png")}

    path = os.path.join(ROOT, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    pages = write_item_pages()
    write_sitemap_and_robots()
    print("built %s (%d 項目)" % (path, total))
    print("built %d 項目ページ" % pages)


if __name__ == "__main__":
    build()
