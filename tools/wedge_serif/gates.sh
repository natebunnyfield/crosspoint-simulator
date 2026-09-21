#!/usr/bin/env bash
# Run every Albo gate against a baseline and fail only on a DELTA.
#
# WHY A BASELINE AND NOT A PASS/FAIL. Every gate here exits non-zero on the
# shipping font and has for months: the roman's `h` HAIR, the italic's `b p y`,
# the `VI` touching pair, `ff` and `fT` under the floor. Those are accepted --
# but they were accepted IN PROSE, in three different docs, so "clean" drifted
# to mean "my glyph raises no row" in some commits and "the same rows as
# before" in others, and nobody could tell which. Round 297 shipped a NEW hair
# in the italic `y` to TestFlight as build 205 under a commit that said "every
# other font unchanged". A baseline makes that impossible to say by accident:
# accepting a finding becomes a reviewable commit to gates-baseline.txt.
#
#   ./gates.sh            compare against the baseline, exit 1 on any delta
#   ./gates.sh --accept   rewrite the baseline (review the diff before you commit)
#
# A full run is a few seconds; there has never been a performance reason to
# skip it.
set -uo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"; trap 'rm -rf "$OUT"' EXIT
BASE="gates-baseline.txt"
ACCEPT=0; [ "${1:-}" = "--accept" ] && ACCEPT=1

ROM="FJORD_STEM=66.9 FJORD_CONTRAST=0.892"
ITA="ALBO_ITALIC=aldine FJORD_STEM=66.9 FJORD_CONTRAST=0.80 FJORD_WIDTH=95 FJORD_SLANT=13"

echo "building..." >&2
env $ROM PYTHON_GIL=0 python3 -m outlines.build "$OUT" --style Regular >"$OUT/br.log" 2>&1 \
  || { echo "ROMAN BUILD FAILED"; tail -5 "$OUT/br.log"; exit 2; }
env $ITA PYTHON_GIL=0 python3 -m outlines.build "$OUT" --style Italic  >"$OUT/bi.log" 2>&1 \
  || { echo "ITALIC BUILD FAILED"; tail -5 "$OUT/bi.log"; exit 2; }

REP="$OUT/report.txt"; : >"$REP"
# Each gate is reduced to a SET OF NAMES, not its full text: the text carries
# coordinates that move for innocent reasons, and a baseline that churns is a
# baseline nobody reads.
rows() { grep -E '^\s+[A-Za-z][A-Za-z0-9_.]*\s+segs' | awk '{print $1}' | sort | tr '\n' ' '; }

for st in Regular Italic; do
  F="$OUT/Albo-$st.ttf"
  echo "hairs.letters.$st  $(PYTHON_GIL=0 python3 cmp_contour_hairs.py "$F" --letters 2>/dev/null | rows)" >>"$REP"
  echo "hairs.all.$st      $(PYTHON_GIL=0 python3 cmp_contour_hairs.py "$F" 2>/dev/null | rows)" >>"$REP"
  echo "touch.$st          $(PYTHON_GIL=0 python3 cmp_touch.py "$F" 2>/dev/null | grep -oE '[0-9]+ pair\(s\) TOUCHING, [0-9]+ below' | head -1)" >>"$REP"
done
sed -i '' -E 's/[[:space:]]+$//' "$REP" 2>/dev/null || sed -i -E 's/[[:space:]]+$//' "$REP"

# The approved-glyph ledger: does the DEFAULT build still draw what the owner
# ruled on? Round 336 shipped a letter no ruling was made on, and both builds
# were gate-clean, so nothing else here would notice.
APPROVED_OUT="$(PYTHON_GIL=0 python3 approved.py --check \
    --regular "$OUT/Albo-Regular.ttf" --italic "$OUT/Albo-Italic.ttf" 2>&1)"
APPROVED_RC=$?
echo "$APPROVED_OUT"

# The bench ledger: do build.py's four bearing tables still equal what the
# owner's spacing bench asks for? Round 308 shipped tables whose input was
# never committed, so they could not be re-derived at all; this makes a
# hand-edit to those tables, or a stale bench_values.json, a failing run.
BENCH_OUT="$(PYTHON_GIL=0 python3 bench_fit.py --check 2>&1 | grep -E '^(DIFFERS|build\.py)')"
BENCH_RC=0; echo "$BENCH_OUT" | grep -q 'does NOT match' && BENCH_RC=1
echo "$BENCH_OUT"

if [ "$ACCEPT" = "1" ]; then
  cp "$REP" "$BASE"; echo "baseline written to $BASE:"; cat "$BASE"; exit 0
fi
if [ ! -f "$BASE" ]; then
  echo "no $BASE yet — run ./gates.sh --accept once, review it, and commit it"; cat "$REP"; exit 2
fi
if diff -u "$BASE" "$REP" >"$OUT/diff"; then
  if [ "$APPROVED_RC" != "0" ]; then
    echo "GATES unchanged, but an APPROVED GLYPH moved (above)."; exit 1
  fi
  if [ "$BENCH_RC" != "0" ]; then
    echo "GATES unchanged, but build.py no longer matches the BENCH (above)."
    echo "Run ./bench_fit.py and paste its tables, or refresh bench_values.json."; exit 1
  fi
  echo "GATES UNCHANGED against $BASE"; exit 0
fi
echo "GATE DELTA — something moved that the baseline does not record:"; cat "$OUT/diff"
echo
echo "If the change is intended, rerun with --accept and COMMIT the new baseline"
echo "with the reason. Do not accept a delta you cannot explain."
exit 1
