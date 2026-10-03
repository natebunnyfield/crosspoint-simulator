#!/bin/bash
# refit_arm.sh TAG -- docs/local-ai-spacing-options-2026-09-26.md §14b end to end (round 463). Env: SCRATCH (holds
# spacing_b2.before.json = the tables to start from, bigrams.json = the census), BASE (the shipped build the holds
# keep their whites against), VENV (python with fontTools/uharfbuzz/scipy), plus any b2_fit env (ALBO_B2_REBASE_SKIP=c).
set -e
TAG="$1"
S="${SCRATCH:?set SCRATCH to a work dir holding spacing_b2.before.json, bigrams.json and the base build}"
WS=/Users/natebunnyfield/src/crosspoint-simulator/tools/wedge_serif
V="${VENV:-$S/venv/bin/python}"
cd $WS; source build_env.sh; export PATH="/Users/natebunnyfield/.asdf/shims:$PATH"
cp $S/spacing_b2.before.json outlines/spacing_b2.json
(cd local_ai && ALBO_SPACING_TABLES=_fit_$TAG.json $V b2_fit.py --census $S/bigrams.json --extra | tail -2)
python3 - "$TAG" <<'PY'
import json, sys
tag=sys.argv[1]
p='outlines/spacing_b2.json'; a=json.load(open(p)); b=json.load(open(f'outlines/_fit_{tag}.json'))
for st in ['roman','italic']:
    for blk in ['letters','marks','kerns','scope','in_sample']:
        if blk in b[st]: a[st][blk]=b[st][blk]
json.dump(a, open(p,'w'), indent=1, ensure_ascii=False, sort_keys=True)
a['roman']['holds']={}; a['italic']['holds']={}
json.dump(a, open('outlines/_noholds.json','w'), indent=1, ensure_ascii=False, sort_keys=True)
PY
H=$S/r${TAG}h; rm -rf $H; mkdir -p $H
( (env "${ALBO_ROM_ENV[@]}" ALBO_SPACING_TABLES=_noholds.json PYTHON_GIL=0 python3 -m outlines.build $H --style Regular > $H/r.log 2>&1) & (env "${ALBO_ITA_ENV[@]}" ALBO_SPACING_TABLES=_noholds.json PYTHON_GIL=0 python3 -m outlines.build $H --style Italic > $H/i.log 2>&1) & wait )
(cd local_ai && $V b2_fit.py --census $S/bigrams.json --extra --holds ${BASE:?set BASE to the shipped build dir} $H | grep -c "held pairs")
F=$S/r${TAG}f; rm -rf $F; mkdir -p $F
( (env "${ALBO_ROM_ENV[@]}" ALBO_FENCES=0 PYTHON_GIL=0 python3 -m outlines.build $F --style Regular > $F/r.log 2>&1) & (env "${ALBO_ITA_ENV[@]}" ALBO_FENCES=0 PYTHON_GIL=0 python3 -m outlines.build $F --style Italic > $F/i.log 2>&1) & (env "${ALBO_BLD_ENV[@]}" ALBO_FENCES=0 PYTHON_GIL=0 python3 -m outlines.build $F --style Bold > $F/b.log 2>&1) & (env "${ALBO_BIT_ENV[@]}" ALBO_FENCES=0 PYTHON_GIL=0 python3 -m outlines.build $F --style BoldItalic > $F/z.log 2>&1) & wait )
(cd local_ai && $V fences.py $F | tail -1)
R=$S/r$TAG; rm -rf $R; mkdir -p $R
for pass in 1 2 3 4 5 6 7 8; do
  ( (env "${ALBO_ROM_ENV[@]}" PYTHON_GIL=0 python3 -m outlines.build $R --style Regular > $R/r.log 2>&1) & (env "${ALBO_ITA_ENV[@]}" PYTHON_GIL=0 python3 -m outlines.build $R --style Italic > $R/i.log 2>&1) & (env "${ALBO_BLD_ENV[@]}" PYTHON_GIL=0 python3 -m outlines.build $R --style Bold > $R/b.log 2>&1) & (env "${ALBO_BIT_ENV[@]}" PYTHON_GIL=0 python3 -m outlines.build $R --style BoldItalic > $R/z.log 2>&1) & wait )
  a=$(cd local_ai && $V clearance.py $R 2>&1 | grep -oE "^[0-9]+ clearance" | grep -oE "^[0-9]+")
  b=$(cd local_ai && $V clearance.py $R --composites 2>&1 | grep -oE "^[0-9]+ composite" | grep -oE "^[0-9]+")
  c=$($V instruments/mark_crowd.py --clear $R 2>&1 | grep -oE "^[0-9]+ 2-D" | grep -oE "^[0-9]+")
  echo "pass $pass: base $a composites $b marks $c"
  if [ "$a" = "0" ] && [ "$b" = "0" ] && [ "$c" = "0" ]; then echo converged; break; fi
done
cp outlines/spacing_b2.json $S/tables_$TAG.json
echo "done $TAG"
