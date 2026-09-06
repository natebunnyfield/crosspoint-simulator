#!/usr/bin/env bash
# Headless regression test: a QUEUED POWER tap must wake the deep-sleeping
# simulator -- the HAL half of the zen wake (S-039).
#
# What this pins. On a phone in zen there is no button pad, so nothing can
# press POWER the way the pad's capsule does (injectButtonDown, the edge
# test_sleep_wake.sh covers). A finger landing on a sleeping zen glass is the
# power button instead (ios/SleepTouch.h): padWatch queues a POWER tap through
# HalGPIO::queueButtonTap, and HalGPIO::startDeepSleep turns any queued tap
# into a wake edge -- consumed, never fired, since the wake press has no
# release. That queued-tap rule had no test of its own: the two wake tests
# use the injected edge and the foreground event. QTAP:<BUTTON> in the input
# script drives queueButtonTap exactly as the harness does, so this runs on
# the desktop with no phone.
#
# Scenario (all times from process start):
#   2500ms POWER held 700ms  -> firmware's own sleep path (threshold 400ms;
#                               main.cpp only allows sleep after boot+2000ms)
#   6000ms QTAP:POWER        -> must wake through the queued-tap station;
#                               wake = process relaunch, which promotes the
#                               *_AFTER_WAKE schedules
#   after-wake: a screenshot proves the relaunched process rendered, then
#               QUIT.
#
# Pass: exits 0 with the after-wake screenshot present and both [power]
# stations (the queued-tap wake edge, then the synthetic-edge reboot) in the
# log. Fail: the queued tap is ignored, no relaunch happens, the timeout kills
# a still-sleeping process.
#
# Usage: tests/test_queued_tap_wake.sh <firmware-checkout-dir>

set -u
FIRMWARE_DIR="${1:?usage: test_queued_tap_wake.sh <firmware-checkout-dir>}"
BIN="$FIRMWARE_DIR/.pio/build/simulator/program"
[ -x "$BIN" ] || { echo "SKIP: simulator binary not built at $BIN"; exit 2; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
SHOT="$WORK/after-wake.bmp"

cd "$FIRMWARE_DIR"

# Force the Home boot path, exactly as test_sleep_wake.sh does and for the same
# reason: the press at 2500 ms has to land after allowSleepAt, and a reader boot
# paginating the seed book pushes that past the press.
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
  # Restore before the cleanup: the backup lives inside $WORK.
  # shellcheck disable=SC2064
  trap "[ -f '$STATE_BACKUP' ] && cp '$STATE_BACKUP' '$STATE'; rm -rf '$WORK'" EXIT
fi

# Headless (SDL_VIDEODRIVER=dummy) for the reason test_sleep_wake.sh gives: a
# real window's timing follows the window server and the machine's load.
SDL_VIDEODRIVER=dummy \
CROSSPOINT_SIM_LOG_POWER=1 \
CROSSPOINT_SIM_INPUT_SCRIPT='2500:POWER:700;6000:QTAP:POWER' \
CROSSPOINT_SIM_INPUT_SCRIPT_AFTER_WAKE='1500:QUIT' \
CROSSPOINT_SIM_SCREENSHOTS_AFTER_WAKE="1000:$SHOT" \
"$BIN" >"$WORK/log.txt" 2>&1 &
PID=$!

# 60s ceiling: a normal pass completes in ~9s, but the first exec of a freshly
# built binary can eat 20s+ in macOS Gatekeeper verification before main().
for _ in $(seq 1 120); do
  kill -0 "$PID" 2>/dev/null || break
  sleep 0.5
done
if kill -0 "$PID" 2>/dev/null; then
  kill -9 "$PID" 2>/dev/null
  echo "FAIL: simulator still running after 60s -- the queued POWER tap did not wake it"
  tail -5 "$WORK/log.txt"
  exit 1
fi
wait "$PID"; RC=$?

if [ ! -s "$SHOT" ]; then
  echo "FAIL: process exited (rc=$RC) but no after-wake screenshot -- it never relaunched as a wake"
  tail -5 "$WORK/log.txt"
  exit 1
fi
if ! grep -q 'deep sleep loop entered' "$WORK/log.txt"; then
  echo "FAIL: the POWER hold never reached the sleep loop (the test's premise, not its subject)"
  grep '\[power\]' "$WORK/log.txt" | tail -5
  exit 1
fi
if ! grep -q 'wake edge: queued tap' "$WORK/log.txt"; then
  echo "FAIL: relaunched, but not through the queued-tap wake station"
  grep '\[power\]' "$WORK/log.txt" | tail -5
  exit 1
fi
if ! grep -q 'waking: injected/synthetic edge' "$WORK/log.txt"; then
  echo "FAIL: the queued-tap edge was raised but did not reboot the device"
  grep '\[power\]' "$WORK/log.txt" | tail -5
  exit 1
fi
echo "PASS: a queued POWER tap woke the sleeping device (after-wake screenshot captured, rc=$RC)"
exit 0
