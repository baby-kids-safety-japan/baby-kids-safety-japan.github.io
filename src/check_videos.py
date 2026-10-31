# -*- coding: utf-8 -*-
"""貼ってある動画が、まだ見られるかを確かめる。

動画は消される。埋め込みを止められることもある。どちらも、こちらからは
見えないまま、読者の画面にだけ「この動画は利用できません」が出る。

YouTube の oembed に問い合わせると、生きていれば題名とチャンネル名が
返り、消えていれば404、埋め込みを止めてあれば401が返る。
題名とチャンネル名は videos.py に書いたものと突き合わせる。

使い方:
  python3 -I src/check_videos.py
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
from videos import VIDEOS

OEMBED = "https://www.youtube.com/oembed?format=json&url="


def check(vid):
    url = OEMBED + urllib.parse.quote(
        "https://www.youtube.com/watch?v=" + vid, safe="")
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            d = json.load(r)
        return None, d.get("title", ""), d.get("author_name", "")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return "消えている（404）", "", ""
        if e.code in (401, 403):
            return "埋め込みを止められている（%d）" % e.code, "", ""
        return "HTTP %d" % e.code, "", ""
    except Exception as e:                      # ネットワークが無いときなど
        return "届かない（%s）" % e, "", ""


def main():
    seen = {}
    bad = 0
    for item_id, rows in sorted(VIDEOS.items()):
        for vid, title, _shown, channel in rows:
            if vid in seen:
                continue
            seen[vid] = True
            err, got_title, got_channel = check(vid)
            if err:
                bad += 1
                print("× %s（%s）: %s" % (vid, item_id, err))
                continue
            note = []
            if got_channel != channel:
                note.append("チャンネル名が違う: 手元「%s」／実際「%s」"
                            % (channel, got_channel))
            if note:
                bad += 1
                print("△ %s: %s" % (vid, " / ".join(note)))
            else:
                print("◯ %s %s" % (vid, got_title))
    print("%d本中 %d本に問題" % (len(seen), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
