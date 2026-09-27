#!/bin/bash
# The whole fit audit, end to end (docs/albo-fit-audit-2026-09-26.md).
#   run_all.sh WORKDIR KLI_DIR [PY]
# WORKDIR gets fonts/<tag>/ (rebuilt from git archive, READ-ONLY on the repo),
# the caches and the proof page. KLI_DIR is a kept-legibility-index checkout
# (for ocr/visionocr). PY must have numpy scipy freetype-py uharfbuzz pillow
# fonttools (the asdf 3.14t python has no scipy).
set -e
W=${1:?WORKDIR}; KLI=${2:?KLI_DIR}; PY=${3:-python3}
HERE=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$HERE/../../.." && pwd)
# tag commit: r402 is the audited build; the rest are the validation pairs
LIST="r402 bdfd477
r223 5a06f87
r224 a43bcef
r372 6addf63
r373 05527e2
r377 8c2fddc
r378 091ad7f
r390 0c02ee9
r391 80d8e74
r392 6ec8517
r393 b40737c
r395 95bf547
r397 2a3a27a
r398 03e3bd5
r399 1648143
r400 9e28bb5"
build() {
  local tag=$1 c=$2 src=$W/snap/$1 out=$W/fonts/$1
  [ -f $out/Albo-Italic.ttf ] && return
  mkdir -p $src $out
  git -C $REPO archive $c tools/wedge_serif | tar -x -C $src
  cd $src/tools/wedge_serif
  if [ -f build_env.sh ]; then source build_env.sh; albo_build_all $out >/dev/null 2>&1
  else  # before round 259: the two 400s, by the README's recipe of the day
    FJORD_STEM=66.9 FJORD_CONTRAST=0.892 PYTHON_GIL=0 python3 -m outlines.build $out --style Regular >/dev/null 2>&1
    ALBO_ITALIC=aldine FJORD_STEM=66.9 FJORD_CONTRAST=0.80 FJORD_WIDTH=95 FJORD_SLANT=13 \
      PYTHON_GIL=0 python3 -m outlines.build $out --style Italic >/dev/null 2>&1
  fi
}
while read tag c; do build $tag $c & done <<< "$LIST"; wait
cd "$HERE"
args=(); largs=()
while read tag c; do
  args+=(--albo $tag=$W/fonts/$tag)
  for cut in Regular Italic Bold BoldItalic; do
    [ -f $W/fonts/$tag/Albo-$cut.ttf ] && largs+=(--font $tag/$cut $W/fonts/$tag/Albo-$cut.ttf)
  done
done <<< "$LIST"
$PY run_geom.py "${args[@]}" --out $W/geom.json
S=/System/Library/Fonts/Supplemental; P=/System/Library/Fonts/Palatino.ttc
for r in "Georgia:$S/Georgia.ttf:$S/Georgia Italic.ttf:$S/Georgia Bold.ttf:$S/Georgia Bold Italic.ttf" \
         "Times:$S/Times New Roman.ttf:$S/Times New Roman Italic.ttf:$S/Times New Roman Bold.ttf:$S/Times New Roman Bold Italic.ttf"; do
  IFS=: read n a b c d <<< "$r"
  largs+=(--font $n/Regular "$a" --font $n/Italic "$b" --font $n/Bold "$c" --font $n/BoldItalic "$d")
done
largs+=(--font Charter/Regular "$S/Charter.ttc:0" --font Charter/Italic "$S/Charter.ttc:1" --font Charter/Bold "$S/Charter.ttc:3" --font Charter/BoldItalic "$S/Charter.ttc:2")
largs+=(--font Baskerville/Regular "$S/Baskerville.ttc:0" --font Baskerville/Italic "$S/Baskerville.ttc:2" --font Baskerville/Bold "$S/Baskerville.ttc:1" --font Baskerville/BoldItalic "$S/Baskerville.ttc:3")
largs+=(--font Hoefler/Regular "$S/Hoefler Text.ttc:0" --font Hoefler/Italic "$S/Hoefler Text.ttc:2" --font Hoefler/Bold "$S/Hoefler Text.ttc:1" --font Hoefler/BoldItalic "$S/Hoefler Text.ttc:3")
largs+=(--font Palatino/Regular "$P:0" --font Palatino/Italic "$P:1" --font Palatino/Bold "$P:2" --font Palatino/BoldItalic "$P:3")
VISIONOCR=$KLI/ocr/visionocr $PY legib.py "${largs[@]}" --out $W/legib.json --work $W/legwork
$PY spacing.py --rev bdfd477 --out $W/spacing.json
$PY score.py --geom $W/geom.json --legib $W/legib.json --spacing $W/spacing.json --tag r402 --out $W/fit-r402.json
$PY validate.py --geom $W/geom.json --legib $W/legib.json --out $W/validation.json
$PY validate.py --geom $W/geom.json --legib $W/legib.json --out $W/variants.json --variants
$PY report.py $W/fit-r402.json $W/legib.json r402 > $W/tables.md
$PY proof.py --fit $W/fit-r402.json --fonts $W/fonts/r402 --out $W/proof
