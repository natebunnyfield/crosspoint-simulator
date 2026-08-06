#!/usr/bin/env bash
# Headless end-to-end test: a host keyboard types into the firmware's own text
# field, and the committed text is what the firmware stores.
#
# WHAT IS UNDER TEST. The X3 has no keyboard, so text entry pecks characters
# out of an on-screen grid. HalGPIO carries a host keyboard into that same
# field: the activity announces itself (setTextEntryActive), the host queues
# UTF-8 plus three control bytes (\b backspace, \n commit, \x1b cancel), and
# the activity drains it in loop(). This drives the REAL KeyboardEntryActivity
# through Settings > Device Owner, which saves immediately -- so the assertion
# is the persisted settings.json, not a screenshot.
#
# WHAT IT CANNOT COVER. The script's TYPE action injects at the queue
# (injectTypedText), which is the same entry point the iOS harness uses but is
# NOT the real SDL key path. Two things therefore need a windowed run with a
# real keyboard (a Mac window, or the iOS Simulator with a hardware keyboard
# attached): SDL_EVENT_TEXT_INPUT arriving at all, and the suppression that
# stops those keystrokes from ALSO being read as buttons -- P is POWER, S is
# the sleep shortcut, H is Home, Return is CONFIRM. See ios/README.md.
#
# Usage: tests/test_text_entry.sh <firmware-checkout-dir>

set -u
FIRMWARE_DIR="${1:?usage: test_text_entry.sh <firmware-checkout-dir>}"
BIN=""
for env_name in simulator_x3 simulator; do
  CANDIDATE="$FIRMWARE_DIR/.pio/build/$env_name/program"
  [ -x "$CANDIDATE" ] && { BIN="$CANDIDATE"; break; }
done
[ -n "$BIN" ] || { echo "SKIP: no simulator binary built under $FIRMWARE_DIR/.pio/build"; exit 2; }

CARD="$FIRMWARE_DIR/fs_/.crosspoint"
SETTINGS="$CARD/settings.json"
STATE="$CARD/state.json"
[ -f "$SETTINGS" ] || { echo "SKIP: $SETTINGS not found -- run the simulator once first"; exit 2; }

WORK="$(mktemp -d)"
cp "$SETTINGS" "$WORK/settings.json.orig"
[ -f "$STATE" ] && cp "$STATE" "$WORK/state.json.orig"
restore() {
  cp "$WORK/settings.json.orig" "$SETTINGS" 2>/dev/null
  [ -f "$WORK/state.json.orig" ] && cp "$WORK/state.json.orig" "$STATE"
  rm -rf "$WORK"
}
trap restore EXIT

owner_name() {
  python3 -c "import json,sys; print(json.load(open('$SETTINGS')).get('ownerName',''))"
}
set_owner_name() {
  python3 -c "
import json
p = '$SETTINGS'
d = json.load(open(p)); d['ownerName'] = '''$1'''
json.dump(d, open(p, 'w'))"
}
# Booting into the last book is deliberate (main.cpp: 'the device IS the current
# book'); a non-zero crash-recovery counter is the only lever a headless script
# has to land on Home instead. See the simulator's CLAUDE.md.
force_home_boot() {
  [ -f "$STATE" ] || return 0
  python3 -c "
import json
p = '$STATE'
d = json.load(open(p)); d['readerActivityLoadCount'] = 1
json.dump(d, open(p, 'w'))"
}

# Home: DOWN past every recent book to the last menu row (Settings; the list
# does not wrap). Settings opens on row 0, and its list DOES wrap, so one UP
# lands on the last row -- Device Owner -- whatever the row count is.
NAV_TO_OWNER_FIELD="2000:HOME"
T=2400
for _ in $(seq 1 15); do
  NAV_TO_OWNER_FIELD="$NAV_TO_OWNER_FIELD;$T:DOWN"
  T=$((T + 180))
done
NAV_TO_OWNER_FIELD="$NAV_TO_OWNER_FIELD;5500:ENTER;6700:UP;7400:ENTER"

# One run: navigate to the field, play $1 (script fragment, times >= 8000), quit.
run_case() {
  local label="$1"
  local typing="$2"
  local log="$WORK/$label.log"
  force_home_boot
  ( cd "$FIRMWARE_DIR" && \
    CROSSPOINT_SIM_INPUT_SCRIPT="$NAV_TO_OWNER_FIELD;$typing;12000:QUIT" \
    SDL_VIDEODRIVER=dummy "$BIN" >"$log" 2>&1 )
  if ! grep -q "Entering activity: KeyboardEntry" "$log"; then
    echo "FAIL[$label]: never reached the text field -- the Home/Settings row counts in this script are stale"
    grep "Entering activity" "$log" | tail -5
    exit 1
  fi
  if ! grep -q "\[TEXT\] text entry active" "$log"; then
    echo "FAIL[$label]: the activity never announced the open field to the host"
    exit 1
  fi
}

expect_owner() {
  local label="$1"
  local want="$2"
  local got
  got="$(owner_name)"
  if [ "$got" != "$want" ]; then
    echo "FAIL[$label]: ownerName is \"$got\", expected \"$want\""
    exit 1
  fi
}

# 1. Type, erase, commit. The two backspaces must apply where they arrived, so
#    the ZZ never reaches the stored name.
set_owner_name ""
run_case commit "8400:TYPE:CrossPoint QAZZ;9000:TYPE:\\b\\b;9600:TYPE:\\n"
expect_owner commit "CrossPoint QA"

# 2. Cancel. The field is seeded with what run 1 stored; typing then cancelling
#    must leave the stored name exactly as it was.
run_case cancel "8400:TYPE:ZZZ;9000:TYPE:\\e"
expect_owner cancel "CrossPoint QA"

# 3. A commit with nothing typed stores the seed unchanged (the entry is not
#    emptied by the host having been attached).
run_case untouched "8400:TYPE:\\n"
expect_owner untouched "CrossPoint QA"

echo "PASS: host keyboard typed, erased, committed and cancelled in the firmware's text field"
exit 0
