#!/usr/bin/env bash
# Every Albo gate, on an ARM build against its baseline build -- the
# poor-characters pass (2026-09-26; docs/albo-poor-characters-2026-09-26.md).
#
# gates.sh builds the DEFAULT font, so it cannot see an arm that lives behind
# an env dial. This runs the same gate scripts on two already-built font
# directories and prints only what DIFFERS between them, per cut:
#   moved      cmp_outlines: which glyph outlines changed (must be the letter
#              and nothing else -- a contour-count change re-cuts later glyphs)
#   hairs      cmp_contour_hairs --letters and the full sweep: rows added
#   touch      cmp_touch: the touching / below-floor counts
#   dents      cmp_counter_dents (700s only): findings in the arm
#   glitch     cmp_aldine_glitch on the moved letters
#   contours   cmp_contours --check on the arm's Regular + Italic
#   approved   approved.py --check (the owner's ruled letters)
#   e mouth    etrace/e_hint_gate.py on the arm's Regular
#
#   instruments/poor_gates.sh BASE_DIR ARM_DIR ["Regular Bold"]
set -uo pipefail
cd "$(dirname "$0")/.."
B=${1:?base dir}; A=${2:?arm dir}; CUTS=${3:-"Regular Italic Bold BoldItalic"}
PY="env PYTHON_GIL=0 python3"
rows() { grep -E '^\s+[A-Za-z][A-Za-z0-9_.]*\s+segs' | awk '{print $1}' | sort | tr '\n' ' '; }
bad=0; seen=0
for c in $CUTS; do
  fb="$B/Albo-$c.ttf"; fa="$A/Albo-$c.ttf"; [ -f "$fa" ] || continue; seen=1
  mv=$($PY cmp_outlines.py --verbose "$fb" "$fa" 2>/dev/null | grep "moved:" | sed 's/.*moved: //')
  echo "[$c] moved: ${mv:-none}"
  for mode in --letters ""; do
    hb=$($PY cmp_contour_hairs.py "$fb" $mode 2>/dev/null | rows); ha=$($PY cmp_contour_hairs.py "$fa" $mode 2>/dev/null | rows)
    new=$(comm -13 <(tr ' ' '\n' <<<"$hb" | sort -u) <(tr ' ' '\n' <<<"$ha" | sort -u) | tr '\n' ' ')
    gone=$(comm -23 <(tr ' ' '\n' <<<"$hb" | sort -u) <(tr ' ' '\n' <<<"$ha" | sort -u) | tr '\n' ' ')
    echo "[$c] hairs${mode:- (full)}: new [${new}] cleared [${gone}]"; [ -n "${new// /}" ] && bad=1
  done
  tb=$($PY cmp_touch.py "$fb" 2>/dev/null | grep -oE '[0-9]+ pair\(s\) TOUCHING, [0-9]+ below' | head -1)
  ta=$($PY cmp_touch.py "$fa" 2>/dev/null | grep -oE '[0-9]+ pair\(s\) TOUCHING, [0-9]+ below' | head -1)
  echo "[$c] touch: $tb -> $ta"; [ "$tb" != "$ta" ] && bad=1
  if [[ $c == Bold* ]]; then
    db=$($PY cmp_counter_dents.py "$fb" 2>/dev/null | grep -ciE 'dent'); da=$($PY cmp_counter_dents.py "$fa" 2>/dev/null | grep -ciE 'dent')
    echo "[$c] counter-dent lines: $db -> $da"; [ "$da" -gt "$db" ] && bad=1
  fi
  # the moved GLYPH NAMES mapped back to characters through the font's cmap:
  # cmp_aldine_glitch --chars takes characters, and the names concatenated
  # ("cacuteccaron...") swept the letters of the names instead (2026-09-28)
  chars=$($PY -c '
import sys, ast
from fontTools.ttLib import TTFont
names = set(ast.literal_eval(sys.argv[2])) if sys.argv[2].strip().startswith("[") else set()
rev = {}
for cp, n in TTFont(sys.argv[1]).getBestCmap().items(): rev.setdefault(n, chr(cp))
print("".join(rev[n] for n in sorted(names) if n in rev))' "$fa" "${mv:-[]}" 2>/dev/null)
  if [ -n "$chars" ]; then
    gb=$($PY cmp_aldine_glitch.py --ttf "$fb" --chars "$chars" 2>&1 | tail -1)
    ga=$($PY cmp_aldine_glitch.py --ttf "$fa" --chars "$chars" 2>&1 | tail -1)
    nb=$(echo "$gb" | grep -oE '[0-9]+ with findings' | grep -oE '^[0-9]+'); na=$(echo "$ga" | grep -oE '[0-9]+ with findings' | grep -oE '^[0-9]+')
    echo "[$c] glitch ($chars): $gb  ->  $ga"; [ "${na:-0}" -gt "${nb:-0}" ] && bad=1   # more glyphs with findings = a delta; fewer is a fix
  fi
done
[ $seen = 1 ] || { echo "POOR GATES: NO ARM FONT in $A for [$CUTS]"; exit 2; }
R="$A/Albo-Regular.ttf"; [ -f "$R" ] || R="$B/Albo-Regular.ttf"
I="$A/Albo-Italic.ttf"; [ -f "$I" ] || I="$B/Albo-Italic.ttf"
CT=$($PY cmp_contours.py --check --regular "$R" --italic "$I" 2>&1)
# a contour-count change re-cuts every later glyph in the style (cut.py's phase
# counter): it is a DELTA, not a note -- 2026-09-28 it printed "no delta" over one
echo "$CT" | grep -q "CHANGED" && { echo "[contours] $(echo "$CT" | grep -A3 CHANGED | tr '\n' ' ')"; bad=1; } || echo "[contours] $(echo "$CT" | tail -1)"
echo "[approved] $($PY approved.py --check --regular "$R" --italic "$I" 2>&1 | tail -1)"
echo "[e mouth]  $($PY etrace/e_hint_gate.py "$R" 2>&1 | tail -1)"
[ $bad = 0 ] && echo "POOR GATES: no delta" || echo "POOR GATES: DELTA (above)"
