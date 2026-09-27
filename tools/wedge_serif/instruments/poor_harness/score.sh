#!/bin/bash
# score.sh TAG "cuts" chars...   -> geom/legib cached per tag, F for chars vs r405
P=${POOR_WORK:?set POOR_WORK to a scratch dir}
PY=${POOR_PY:?python with scipy freetype uharfbuzz}; FA=/Users/natebunnyfield/src/crosspoint-simulator/tools/wedge_serif/fit_audit
tag=$1; cuts=$2; shift 2
cd $FA
$PY run_geom.py --albo $tag=$P/fonts/$tag --out $P/geom.json --no-refs >/dev/null
largs=(); for c in $cuts; do largs+=(--font $tag/$c $P/fonts/$tag/Albo-$c.ttf); done
VISIONOCR=${VISIONOCR:?kept-legibility-index ocr/visionocr} $PY legib.py "${largs[@]}" --out $P/legib.json --work $P/legwork >/dev/null
$PY score.py --geom $P/geom.json --legib $P/legib.json --spacing ${SPACING:-$P/spacing.json} --tag $tag --out $P/fit-$tag.json >/dev/null
BASE=${BASE:-r405} CUTS="$cuts" $PY - "$tag" "$@" <<'PYEOF'
import json,sys,os
P=os.environ["POOR_WORK"]
tag=sys.argv[1]; chars=sys.argv[2:]
A=json.load(open(f"{P}/fit-{os.environ.get('BASE','r405')}.json")); B=json.load(open(f"{P}/fit-{tag}.json"))
for cut in [c for c in B if c in os.environ["CUTS"].split()]:
    rk={ch:i+1 for i,(ch,_) in enumerate(sorted(B[cut].items(),key=lambda kv:-kv[1]["F"]))}
    ra={ch:i+1 for i,(ch,_) in enumerate(sorted(A[cut].items(),key=lambda kv:-kv[1]["F"]))}
    for ch in chars:
        a,b=A[cut][ch],B[cut][ch]
        ax=" ".join(f"{k}{b['axes'][k]['z']:+.1f}" for k in "abcdefgh" if k in b["axes"])
        print(f"{tag:14s} {cut:10s} {ch}  F {a['F']:.2f}(#{ra[ch]}) -> {b['F']:.2f}(#{rk[ch]})  [{a['reason']}:{a['axes'][a['reason']]['z']:+.1f} -> {b['axes'][a['reason']]['z']:+.1f}]  {ax}")
    # collateral: any other glyph whose F moved by >0.3
    mv=[(ch,A[cut][ch]['F'],B[cut][ch]['F']) for ch in B[cut] if ch not in chars and abs(B[cut][ch]['F']-A[cut][ch]['F'])>0.3]
    if mv: print(f"   collateral {cut}: "+" ".join(f"{c}:{x:.2f}->{y:.2f}" for c,x,y in mv))
PYEOF
