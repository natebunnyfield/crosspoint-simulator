#!/bin/bash
# arm.sh TAG CUTS "ENV=.. ENV=.."   build an arm from HEAD + my overlaid files
P=${POOR_WORK:?set POOR_WORK to a scratch dir}
REPO=/Users/natebunnyfield/src/crosspoint-simulator
MINE="${MINE_FILES-outlines/glyphs/stems.py outlines/glyphs/diagonals.py outlines/glyphs/caps_straight.py outlines/glyphs/aldine.py}"
tag=$1; cuts=${2:-"Regular Bold"}; extra=$3
W=$P/work
if [ ! -f $W/.synced ] || [ -n "$RESYNC" ]; then
  rm -rf $W; mkdir -p $W; git -C $REPO archive HEAD tools/wedge_serif | tar -x -C $W; touch $W/.synced
fi
for f in $MINE; do cp $REPO/tools/wedge_serif/$f $W/tools/wedge_serif/$f; done
cd $W/tools/wedge_serif; source build_env.sh
out=$P/fonts/$tag; mkdir -p $out
for cut in $cuts; do
  case $cut in Regular) E=("${ALBO_ROM_ENV[@]}");; Italic) E=("${ALBO_ITA_ENV[@]}");; Bold) E=("${ALBO_BLD_ENV[@]}");; BoldItalic) E=("${ALBO_BIT_ENV[@]}");; esac
  env "${E[@]}" $extra PYTHON_GIL=0 python3 -m outlines.build $out --style $cut > $out/build-$cut.log 2>&1 || { echo "BUILD FAIL $tag $cut"; tail -5 $out/build-$cut.log; }
done
