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
  # the ACCENTED pairs (round 449's sweep): every pair with an accented letter on either
  # side, the accent at fault -- the default sweep above never sees them, so a redrawn mark
  # or a moved accent could touch its neighbor under GATES UNCHANGED (round 452's review, F3)
  echo "touch.composites.$st $(PYTHON_GIL=0 python3 cmp_touch.py "$F" --composites 2>/dev/null | grep -oE '[0-9]+ pair\(s\) TOUCHING, [0-9]+ below' | head -1)" >>"$REP"
  # the READER'S KERN CLASSES (round 453): fontconvert_sdcard.py folds the GPOS pairs into
  # classes stored as uint8 and, over 255 either way, drops the style's kerning ENTIRELY with
  # only a warning. Every explicit composite-clearance pair can split a class; round 453's 2-D
  # mark clearance moved the Italic from 86/106 to 105/152. ok / NEAR-LIMIT (230+) / DROPPED.
  echo "kernclasses.$st $(PYTHON_GIL=0 python3 instruments/kern_classes.py "$F" 2>/dev/null | awk '{print $NF}')" >>"$REP"
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

# The contour census: cut.py's decimation phase runs off a counter advanced
# per contour, so a glyph whose CONTOUR COUNT moves re-cuts every glyph built
# after it -- 169 of them when the italic ampersand shipped. Owner ruling
# 2026-09-21: gate it, do not change the drawing. cmp_contours.py's header
# has the whole account.
CONTOUR_OUT="$(PYTHON_GIL=0 python3 cmp_contours.py --check \
    --regular "$OUT/Albo-Regular.ttf" --italic "$OUT/Albo-Italic.ttf" 2>&1)"
CONTOUR_RC=$?
echo "$CONTOUR_OUT"

# The e's mouth AS THE READER RENDERS IT (round 400 added the gate on the
# autohinted render, docs/albo-e-legibility-2026-09-26.md; round 401 moved it
# to NO HINTING, because the firmware's converter now loads Albo with
# FT_LOAD_NO_HINTING -- owner ruling 2026-09-26, "no hinting wins",
# docs/albo-hinting-options-2026-09-26.md). Hard: the mouth must be open at
# every reader slot, 1x and 2x, in 8-bit and in the converter's 2 bits
# (limit 0.15), and at 9-12 ppem unhinted (limit 0.20; round 400 reads 0.149
# at 9.0, and a bar dropped to 0.52 x-height reads 0.345 and fails). 8-8.75
# ppem is printed but not gated -- every unhinted serif, Georgia included,
# greys its e's mouth there. REGULAR ONLY: the limits are calibrated on its
# e. `etrace/e_hint_gate.py --autohint` still runs the round-400 check, which
# is what the Kept Legibility Index's renderer sees.
EHINT_OUT="$(PYTHON_GIL=0 python3 etrace/e_hint_gate.py "$OUT/Albo-Regular.ttf" 2>&1)"
EHINT_RC=$?
echo "e mouth (unhinted, as the reader renders): $EHINT_OUT"

# Every OGONEK touches its letter (round 452): the traced mark is hung by a search over
# shifts, and a redrawn foot can leave it floating. Hard: any gap fails the run.
JOIN_OUT="$(PYTHON_GIL=0 python3 instruments/ogonek_join.py "$OUT" 2>/dev/null)"
JOIN_RC=$?
echo "ogonek joins:"; echo "$JOIN_OUT"

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
  if [ "$EHINT_RC" != "0" ]; then
    echo "GATES unchanged, but the roman e falls in an AUTOHINTER WINDOW (above):"
    echo "its mouth inks at small sizes and machine readers take it for o."
    echo "Move the e's outline off the window (round 400: ALBO_ROM_E_BAR_TOP)."; exit 1
  fi
  if [ "$JOIN_RC" != "0" ]; then
    echo "GATES unchanged, but an OGONEK no longer touches its letter (above)."
    echo "Check the foot it hangs from: python3 instruments/ogonek_join.py <dir> --zoom out.png"; exit 1
  fi
  if [ "$CONTOUR_RC" != "0" ]; then
    echo "GATES unchanged, but a glyph's CONTOUR COUNT moved (above), which"
    echo "re-cuts every glyph after it. Accept it deliberately:"
    echo "  python3 cmp_contours.py --accept --regular <R.ttf> --italic <I.ttf>"; exit 1
  fi
  echo "GATES UNCHANGED against $BASE"; exit 0
fi
echo "GATE DELTA — something moved that the baseline does not record:"; cat "$OUT/diff"
echo
echo "If the change is intended, rerun with --accept and COMMIT the new baseline"
echo "with the reason. Do not accept a delta you cannot explain."
exit 1
