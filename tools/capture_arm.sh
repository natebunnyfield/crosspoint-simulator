#!/bin/bash
#
# One gate capture, for surface work that must not move a pixel.
#
#   tools/capture_arm.sh <program> <dark 0|1> <out.bmp> [input-script] [shot-ms]
#
# WHY THIS EXISTS RATHER THAN A RECIPE IN A DOC. Three separate traps cost a
# wrong reading or a dead session on 2026-08-25, and all three are handled here:
#
# 1. DO NOT COPY THE CARD. An earlier harness copied the whole 522 MB simulated
#    SD card per arm; it filled the disk and blocked a session outright, to the
#    point that Bash could not run because it could not create its own output
#    file. Only fs_/.crosspoint is mutable, so only that is restored -- 104 KB.
#
# 2. THE DESKTOP settings.json OVERRIDES CROSSPOINT_SIM_AS_SHIPPED. It sits
#    beside the binary and the settings watcher re-asserts its palette about once
#    a second, so two arms that should differ come back byte-identical. This
#    script parks it for the run and restores it on exit, including on failure.
#
# 3. TWO ARMS COMING BACK IDENTICAL IS THE SIGNATURE of both traps above, not a
#    result. If dark and light give the same md5, something is overriding you.
#
# To reach a SYSTEM screen instead of the book, set readerActivityLoadCount to 1
# (this script forces the book with 0). Holding Back does NOT work against that
# -- main.cpp's `counter != 0 || backHeld` resolves to the reader either way.
# Confirm which screen you got from the `[ACT] Entering activity:` log line and
# never from the picture: under Lyra Six, Home renders the current book's page.
#
# Animated surfaces (the collapse, the warm-up) CANNOT be photographed on a
# fixed schedule -- they sample the wall clock and the tick they start on moves
# between runs. Those need clock pinning; see docs/power-off-collapse.md.
set -euo pipefail

PROG="${1:?usage: capture_arm.sh <program> <dark 0|1> <out.bmp> [script] [ms]}"
DARK="${2:?}"; OUT="${3:?}"; EXTRA="${4:-}"; AT="${5:-6000}"
FW="${CROSSPOINT_FIRMWARE_DIR:-$HOME/src/crosspoint-reader}"
CARD="$FW/fs_/.crosspoint"
BACKUP="${CROSSPOINT_CARD_BACKUP:?set CROSSPOINT_CARD_BACKUP to a pristine .crosspoint copy}"

PARKED=""
restore() {
  [ -n "$PARKED" ] && [ -f "$PARKED" ] && mv "$PARKED" "$FW/settings.json" || true
}
trap restore EXIT

if [ -f "$FW/settings.json" ]; then
  PARKED="$(mktemp -t cpsettings)"
  mv "$FW/settings.json" "$PARKED"
fi

rm -rf "$CARD"
cp -R "$BACKUP" "$CARD"
python3 - "$CARD" "$DARK" <<'PY'
import json, sys, os
card, dark = sys.argv[1], int(sys.argv[2])
json.dump({'darkMode': dark}, open(os.path.join(card, 'settings.json'), 'w'))
p = os.path.join(card, 'state.json')
d = json.load(open(p)); d['readerActivityLoadCount'] = 0; json.dump(d, open(p, 'w'))
PY

SCRIPT="9000:QUIT"
[ -n "$EXTRA" ] && SCRIPT="$EXTRA;9000:QUIT"
( cd "$FW" && timeout 120 env \
    CROSSPOINT_SIM_AS_SHIPPED=1 \
    CROSSPOINT_SIM_GRAIN_SEED="${CROSSPOINT_SIM_GRAIN_SEED:-7}" \
    CROSSPOINT_SIM_INPUT_SCRIPT="$SCRIPT" \
    CROSSPOINT_SIM_SCREENSHOTS="$AT:$OUT" \
    SDL_VIDEODRIVER=dummy "$PROG" >/dev/null 2>&1 ) || true

[ -f "$OUT" ] || { echo "capture_arm: no capture at $OUT" >&2; exit 1; }
md5 -q "$OUT" 2>/dev/null || md5sum "$OUT" | cut -d' ' -f1
