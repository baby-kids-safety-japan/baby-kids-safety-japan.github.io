#!/bin/sh
# 図版の WebP を作る。元の JPEG は消さずに残す。
#
# なぜ要るか:
#   図版は1枚あたり平均 210KB の JPEG で、全部で 25MB ある。これがモバイルの
#   通信量のほとんどを占めていた。WebP にすると 8割前後まで落ちる。
#
# なぜ2種類作るか:
#   スマートフォンでの表示幅は約 311px なので、画素密度3倍でも 933px で足りる。
#   一方 PC の Retina では 1400px が要る。srcset でブラウザに選ばせるため、
#   1000px と 1400px の2つを置く。モバイルは 1000px のほうだけを落とす。
#
# なぜ元を残すか:
#   <picture> のフォールバックとして使う。WebP を読めない古い端末でも
#   図版が出る。ダウンロードされるのはどちらか一方だけなので、
#   両方置いても通信量は増えない。
#
# 使い方:
#   src/make_webp.sh            変換が必要なものだけ作る
#   src/make_webp.sh --force    全部作り直す
set -eu

cd "$(dirname "$0")/.."

command -v cwebp >/dev/null 2>&1 || {
  echo "cwebp が見つかりません。brew install webp で入ります。" >&2
  exit 1
}

force=""
[ "${1:-}" = "--force" ] && force=1

made=0
skipped=0

for jpg in $(find assets/img -name '*.jpg' ! -path '*/tab/*' | sort); do
  base="${jpg%.jpg}"
  for width in 1000 1400; do
    out="${base}-${width}.webp"
    if [ -z "$force" ] && [ -f "$out" ] && [ "$out" -nt "$jpg" ]; then
      skipped=$((skipped + 1))
      continue
    fi
    # 1400 は元と同じ幅なので、拡大しないよう -resize は width 側だけ渡す。
    # cwebp は元より大きい値を渡しても拡大するので、元幅を超えないようにする。
    src_w=$(sips -g pixelWidth "$jpg" 2>/dev/null | awk '/pixelWidth/{print $2}')
    if [ "$width" -ge "$src_w" ]; then
      cwebp -quiet -q 82 "$jpg" -o "$out"
    else
      cwebp -quiet -q 84 -resize "$width" 0 "$jpg" -o "$out"
    fi
    made=$((made + 1))
  done
done

# タブの絵は 144x144 と小さいので、1種類だけ作る。
for jpg in $(find assets/img/tab -name '*.jpg' | sort); do
  out="${jpg%.jpg}.webp"
  if [ -z "$force" ] && [ -f "$out" ] && [ "$out" -nt "$jpg" ]; then
    skipped=$((skipped + 1))
    continue
  fi
  cwebp -quiet -q 86 "$jpg" -o "$out"
  made=$((made + 1))
done

echo "作成 ${made} 件 / 既存のまま ${skipped} 件"
echo "JPEG 合計: $(find assets/img -name '*.jpg' -exec cat {} + | wc -c | tr -d ' ') バイト"
echo "WebP 合計: $(find assets/img -name '*.webp' -exec cat {} + | wc -c | tr -d ' ') バイト"
