#!/bin/zsh
# 使い方: src/install_image.sh <タブID|common> <出力名（拡張子なし）> [長辺px] [元ファイル]
#   例: src/install_image.sh m7 stairs-gate
#       src/install_image.sh m7 stairs-gate 1400 ~/Downloads/階段の比較図.png
#
# 元ファイルを省くと ~/Downloads の最新 PNG を使う。変換後、その元ファイルは消す。
#
# 画像を作るエージェントを複数同時に動かすときは、必ず元ファイルを明示すること。
# 省略すると「最新の PNG」を奪い合い、他のエージェントがダウンロードした
# まだ処理していないファイルを変換して消してしまう。
#
# タブIDは src/content.py のタブの "id"（m0 / m4 / m7 / y1 / y3 / y6 / y10）。
# 複数のタブで使う画像は common に置く。
set -e
dir_id="$1"; name="$2"; max="${3:-1400}"; src="$4"
[ -n "$dir_id" ] && [ -n "$name" ] || { echo "usage: install_image.sh <タブID|common> <名前> [長辺px] [元ファイル]"; exit 1; }
root="$(cd "$(dirname "$0")/.." && pwd)"
out="$root/assets/img/$dir_id"
mkdir -p "$out"
if [ -n "$src" ]; then
  f="$src"
  [ -f "$f" ] || { echo "no such file: $f"; exit 1; }
else
  f=$(ls -t ~/Downloads/*.png 2>/dev/null | head -1)
  [ -n "$f" ] || { echo "no png in ~/Downloads"; exit 1; }
fi
sips -s format jpeg -s formatOptions 80 -Z "$max" "$f" --out "$out/$name.jpg" >/dev/null
rm -f "$f"
ls -l "$out/$name.jpg"
