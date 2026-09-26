#!/usr/bin/env bash
# Build the roman Regular at EVERY commit touching tools/wedge_serif between
# two commits, and record per commit: the e's outline hash (so a jump can be
# tied to the commit that moved the e), its advance, and the e_hint_gate
# verdict. The OCR runs (kli_e.py) are then spent only on commits where the
# e's hash changes -- a commit that leaves the e byte-identical cannot move
# e>o except through spacing, which the index's per-condition split shows.
#
#   bisect_all.sh FROM TO OUT.tsv
set -uo pipefail
from="${1:?from}"; to="${2:?to}"; out="${3:?out.tsv}"
here="$(cd "$(dirname "$0")" && pwd)"; repo="$(cd "$here/../../.." && pwd)"
scratch="${ETRACE_SCRATCH:?set ETRACE_SCRATCH}"
py="${ETRACE_PY:-python3}"
printf "commit\tdate\tsubject\te_hash\te_adv\tgate\tworst\n" > "$out"
for c in $(git -C "$repo" log --reverse --format=%h "$from^..$to" -- tools/wedge_serif); do
  d="$scratch/fonts/bis/$c"
  if [ ! -f "$d/Albo-Regular.ttf" ]; then
    "$here/snap_build.sh" "$c" "$d" >/dev/null 2>&1 || { printf "%s\t\t\tBUILD-FAIL\t\t\t\n" "$c" >> "$out"; continue; }
  fi
  info=$("$py" - "$d/Albo-Regular.ttf" <<'EOF'
import sys, hashlib
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
f = TTFont(sys.argv[1]); p = RecordingPen(); f.getGlyphSet()["e"].draw(p)
print(hashlib.md5(repr(p.value).encode()).hexdigest()[:10] + "\t" + str(f["hmtx"]["e"][0]))
EOF
)
  g=$("$py" "$here/e_hint_gate.py" "$d/Albo-Regular.ttf" 2>/dev/null)
  verdict=$(echo "$g" | awk '{print $1}'); worst=$(echo "$g" | awk '{print $4}')
  meta=$(git -C "$repo" log -1 --format='%ad%x09%s' --date=short "$c" | cut -c1-90)
  printf "%s\t%s\t%s\t%s\t%s\n" "$c" "$meta" "$info" "$verdict" "$worst" >> "$out"
done
