#!/usr/bin/env bash
# Headless regression test: a FAST synthetic POWER tap must wake the
# deep-sleeping simulator.
#
# The bug this pins down: HalGPIO::startDeepSleep polled syntheticButtonDown[]
# as a LEVEL once per 10 ms iteration. A tap whose down and up edges are both
# applied inside one processSyntheticEvents() call (e.g. a 1 ms scripted tap,
# or iOS delivering a queued FINGER_DOWN+FINGER_UP burst after unlock) leaves
# no level behind to observe -- the wake is silently missed and the device
# sleeps forever. The fix latches an edge in injectButtonDown that the sleep
# loop consumes.
#
# Scenario (all times from process start):
#   2500ms POWER held 700ms  -> firmware's own sleep path (threshold 400ms;
#                               main.cpp only allows sleep after boot+2000ms,
#                               so the hold must start beyond that)
#   6000ms POWER tapped 1ms  -> must wake; wake = process relaunch, which
#                               promotes *_AFTER_WAKE schedules
#   after-wake: screenshot proves the relaunched process rendered, then QUIT.
#
# Pass: exits 0 with the after-wake screenshot present. Fail: the 1ms tap is
# missed, no relaunch happens, the timeout kills a still-sleeping process.
#
# Usage: tests/test_sleep_wake.sh <firmware-checkout-dir>

set -u
FIRMWARE_DIR="${1:?usage: test_sleep_wake.sh <firmware-checkout-dir>}"
BIN="$FIRMWARE_DIR/.pio/build/simulator/program"
[ -x "$BIN" ] || { echo "SKIP: simulator binary not built at $BIN"; exit 2; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
SHOT="$WORK/after-wake.bmp"

cd "$FIRMWARE_DIR"

# FORCE THE HOME BOOT PATH, and put the card back afterwards.
#
# The press at 2500 ms has to land after allowSleepAt, which main.cpp sets to
# (end of setup) + 2000 ms. Booting into Home, setup finishes in ~400 ms and the
# press lands comfortably. Booting into the READER -- which a card with a
# recently-read book does -- setup also paginates, and on the seed book's
# mono-file chapter that takes tens of seconds, so allowSleepAt moves past the
# press and the device never sleeps.
#
# That is what S-011 was: not firmware drift in the power semantics, but a test
# whose result depended on whatever state the working card happened to be in.
# readerActivityLoadCount > 0 is the documented lever for a Home boot.
STATE="$FIRMWARE_DIR/fs_/.crosspoint/state.json"
STATE_BACKUP="$WORK/state.json.orig"
if [ -f "$STATE" ]; then
  cp "$STATE" "$STATE_BACKUP"
  python3 - "$STATE" <<'SEED'
import json, sys
p = sys.argv[1]
try:
    d = json.load(open(p))
except Exception:
    d = {}
d["readerActivityLoadCount"] = 1
json.dump(d, open(p, "w"))
SEED
  # RESTORE BEFORE THE CLEANUP. The backup lives inside $WORK, so wiping $WORK
  # first deletes the very file the restore reads -- which silently left the
  # seeded state on the working card.
  # shellcheck disable=SC2064
  trap "[ -f '$STATE_BACKUP' ] && cp '$STATE_BACKUP' '$STATE'; rm -rf '$WORK'" EXIT
fi

# HEADLESS, and this is what made the test flaky rather than any drift.
#
# It was the only test here that did NOT set SDL_VIDEODRIVER=dummy, so it opened
# a REAL SDL window and its timing followed the window server, the GPU and the
# machine's load. It failed as "the 1ms wake tap was missed" whenever the box was
# busy -- indistinguishable from a firmware regression, and it was filed as one
# (S-011). Run headless it passes every time; run windowed it fails under load
# and passes idle. The two tests that were never flaky both set this.
#
# Dummy still renders, so the after-wake screenshot below is captured exactly as
# before -- that is what the other headless tests here rely on too.
SDL_VIDEODRIVER=dummy \
CROSSPOINT_SIM_INPUT_SCRIPT='2500:POWER:700;6000:POWER:1' \
CROSSPOINT_SIM_INPUT_SCRIPT_AFTER_WAKE='1500:QUIT' \
CROSSPOINT_SIM_SCREENSHOTS_AFTER_WAKE="1000:$SHOT" \
"$BIN" >"$WORK/log.txt" 2>&1 &
PID=$!

# 60s ceiling: normal pass completes in ~9s (sleep at ~2.9s, tap at 6s,
# relaunch + 1.5s after-wake script), but the FIRST exec of a freshly built
# binary can eat 20s+ in macOS Gatekeeper verification before main() runs.
for _ in $(seq 1 120); do
  kill -0 "$PID" 2>/dev/null || break
  sleep 0.5
done
if kill -0 "$PID" 2>/dev/null; then
  kill -9 "$PID" 2>/dev/null
  echo "FAIL: simulator still running after 30s -- the 1ms wake tap was missed"
  exit 1
fi
wait "$PID"; RC=$?

if [ ! -s "$SHOT" ]; then
  echo "FAIL: process exited (rc=$RC) but no after-wake screenshot -- it never relaunched as a wake"
  tail -5 "$WORK/log.txt"
  exit 1
fi
echo "PASS: fast tap woke the device (after-wake screenshot captured, rc=$RC)"
exit 0
