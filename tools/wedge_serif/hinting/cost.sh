#!/usr/bin/env bash
# What each hinting arm costs in the REAL converter: .cpfont bytes and wall time.
#
#   cost.sh CONV_DIR FONTS_DIR OUT_DIR [PYTHON]
#
# CONV_DIR is a copy of the firmware's lib/EpdFont/scripts carrying the one
# scratch patch validate.py describes (CPFONT_PRIMARY_LOAD_FLAGS_OR). Albo
# Regular + Italic, `reading` intervals, NO fallback chain (the chain's glyphs
# are the same bytes in every arm), sizes 8..18 at 1x and 16..36 at the 2x
# tier -- the sd-fonts.yaml ramp. Metrics override is skipped: it rewrites
# hhea/OS2 only and moves no glyph pixel.
set -euo pipefail
conv=$1; fonts=$2; out=$3; py=${4:-python3}
mkdir -p "$out"
run() {  # arm fontprefix flags
  local arm=$1 pre=$2 flags=$3
  for tier in 1 2; do
    local sizes; sizes=$(for s in 8 10 12 14 16 18; do printf '%s,' $((s * tier)); done); sizes=${sizes%,}
    local d="$out/$arm/${tier}x"; rm -rf "$d"; mkdir -p "$d"
    local t0; t0=$($py -c 'import time;print(time.time())')
    CPFONT_PRIMARY_LOAD_FLAGS_OR=$flags $py "$conv/fontconvert_sdcard.py" \
      --regular "$fonts/$pre-Regular.ttf" --italic "$fonts/$pre-Italic.ttf" \
      --sizes "$sizes" --intervals reading --name Albo --output-dir "$d" >/dev/null 2>"$d/log.txt"
    local t1; t1=$($py -c 'import time;print(time.time())')
    local bytes; bytes=$(cat "$d"/*.cpfont | wc -c | tr -d ' ')
    printf '%-8s %sx  %9s bytes  %6.1f s\n' "$arm" "$tier" "$bytes" "$($py -c "print($t1-$t0)")"
  done
}
run today   today    0
run ttfa-q  ttfa-qsq 0
run light   today    0x10000
run nohint  today    0x2
