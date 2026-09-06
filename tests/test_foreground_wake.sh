#!/usr/bin/env bash
# Headless regression test: the app returning to the FOREGROUND must wake a
# deep-sleeping simulator, and must count as activity once it is awake.
#
# The bug this pins down (owner, 2026-09-06: "ios app needs to wake on
# reactivation. is staying power off"): on a phone the app becoming active is
# the owner picking the device up, but HalGPIO::startDeepSleep woke only on a
# key or an injected press, so an app put away asleep came back asleep. And an
# app put away AWAKE came back asleep too: millis() is steady_clock, which does
# not stop while iOS holds the process suspended, so the firmware's inactivity
# timer had expired by the first loop() after resume and it slept on the spot.
# The fix handles SDL_EVENT_DID_ENTER_FOREGROUND in both places: the sleep loop
# reboots as a power wake, and update() latches it as activity so the firmware
# resets its timer before the auto-sleep check.
#
# Desktop SDL never sends that event, so the script's FOREGROUND verb pushes
# the real one (HalGPIO.cpp, pushForeground) and the test runs anywhere.
#
# Scenario (all times from process start):
#   2500ms POWER held 700ms  -> firmware's own sleep path (threshold 400ms;
#                               main.cpp only allows sleep after boot+2000ms)
#   6000ms FOREGROUND        -> must wake; wake = process relaunch, which
#                               promotes *_AFTER_WAKE schedules
#   after-wake: 800ms FOREGROUND with the device awake -> the [power] log
#               station proves update() saw it as activity; a screenshot
#               proves the relaunched process rendered; then QUIT.
#
# Pass: exits 0 with the after-wake screenshot and the activity station both
# present. Fail: the foreground return is ignored, no relaunch happens, the
# timeout kills a still-sleeping process.
#
# Usage: tests/test_foreground_wake.sh <firmware-checkout-dir>

set -u
FIRMWARE_DIR="${1:?usage: test_foreground_wake.sh <firmware-checkout-dir>}"
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
CROSSPOINT_SIM_INPUT_SCRIPT='2500:POWER:700;6000:FOREGROUND' \
CROSSPOINT_SIM_INPUT_SCRIPT_AFTER_WAKE='800:FOREGROUND;1500:QUIT' \
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
  echo "FAIL: simulator still running after 60s -- the foreground return did not wake it"
  tail -5 "$WORK/log.txt"
  exit 1
fi
wait "$PID"; RC=$?

if [ ! -s "$SHOT" ]; then
  echo "FAIL: process exited (rc=$RC) but no after-wake screenshot -- it never relaunched as a wake"
  tail -5 "$WORK/log.txt"
  exit 1
fi
if ! grep -q 'waking: app returned to the foreground' "$WORK/log.txt"; then
  echo "FAIL: relaunched, but not through the foreground wake station"
  grep '\[power\]' "$WORK/log.txt" | tail -5
  exit 1
fi
if ! grep -q 'foreground return counts as activity' "$WORK/log.txt"; then
  echo "FAIL: the awake device did not see the foreground return as activity"
  grep '\[power\]' "$WORK/log.txt" | tail -5
  exit 1
fi
echo "PASS: foreground return woke the device and counted as activity afterwards (rc=$RC)"
exit 0
