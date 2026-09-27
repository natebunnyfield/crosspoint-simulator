#!/bin/bash
# redo.sh "CUTS" "CHARS" TAG=ENV [TAG=ENV ...]   rebuild + rescore arms, clearing caches
P=${POOR_WORK:?set POOR_WORK to a scratch dir}
cuts=$1; chars=$2; shift 2
tags=()
for spec in "$@"; do tag=${spec%%=*}; env=${spec#*=}; tags+=($tag); rm -rf $P/fonts/$tag; "$(dirname "$0")"/arm.sh $tag "$cuts" "$env" & done; wait
${POOR_PY:?python with scipy freetype uharfbuzz} - "${tags[@]}" <<'PY'
import json,sys,os;f=os.environ["POOR_WORK"]+"/"
for fn in ["geom.json","legib.json"]:
    g=json.load(open(f+fn)); [g.pop(k) for k in list(g) if k.split("/")[0] in sys.argv[1:]]; json.dump(g,open(f+fn,"w"))
PY
for t in "${tags[@]}"; do "$(dirname "$0")"/score.sh $t "$cuts" $chars; done
