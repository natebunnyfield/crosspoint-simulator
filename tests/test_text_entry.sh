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
# Which text-entry activity the factory builds: 0 daisywheel, 1 13-grid,
# 2 QWERTY (CrossPointSettings::KEYBOARD_LAYOUT). Set rather than inherited,
# because the two activities are separate implementations of the same channel
# and the card's own choice is not the suite's business — a card left on the
# daisywheel used to fail this test for the wrong reason.
set_keyboard_layout() {
  python3 -c "
import json
p = '$SETTINGS'
d = json.load(open(p)); d['keyboard'] = $1
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
# does not wrap). Settings opens on row 0, and its list DOES wrap, so counting
# UP from the top reaches the tail whatever the row count is. Device Owner is
# the SECOND-to-last row: Colophon was added after it and sits last, being
# informational (SettingsActivity.cpp, the deviceSettings tail). One UP used to
# be right and started silently opening Colophon instead -- the run_case guard
# below is what caught it, so keep asserting the activity rather than trusting
# the count.
# RIGHT, NOT DOWN, and 900 ms apart. Both were wrong and the test had been
# failing against firmware main for it (S-015): a menu list navigates on the
# FRONT pair -- DOWN is a SIDE button that pages by a screenful, and a
# one-screen menu has no next screenful, so every DOWN here moved nothing and
# the run never reached the field it tests. 180 ms spacing was the second
# fault: docs/headless-qa.md measures that presses need ~900 ms or half are
# swallowed.
# OVER-PRESS, deliberately. The row count depends on how many RECENT BOOKS the
# card has, so any fixed count is stale the moment someone opens a different
# book -- which is how this went red. The Home list does NOT wrap, so pressing
# past the end simply rests on the last row (Settings); 20 covers any plausible
# recents list and costs only time.
NAV_TO_OWNER_FIELD="2000:HOME"
T=2900
for _ in $(seq 1 20); do
  NAV_TO_OWNER_FIELD="$NAV_TO_OWNER_FIELD;$T:RIGHT"
  T=$((T + 900))
done
NAV_TO_OWNER_FIELD="$NAV_TO_OWNER_FIELD;$T:ENTER"
T=$((T + 1200))
# LEFT, not UP -- and this is the SAME fault as the Home leg above, in the
# other list: UP/DOWN are the SIDE pair and page by a screenful, so in a
# one-screen menu they move nothing. Every UP count from 1 to 5 landed on
# FontSelect, i.e. on row 0, which is what "the key does nothing" looks like
# from outside.
#
# The Settings list DOES wrap, so counting backwards from row 0 is stable
# whatever the row count: LEFT x1 is Colophon (last, informational), LEFT x2 is
# Device Owner. Verified by sweeping the count against the activity log.
NAV_TO_OWNER_FIELD="$NAV_TO_OWNER_FIELD;$T:LEFT;$((T + 900)):LEFT;$((T + 1800)):ENTER"
# When the field is open, in ms. Every case fragment below starts after this.
FIELD_OPEN_MS=$((T + 3000))

# One run: navigate to the field, play $1 (script fragment, times off FIELD_OPEN_MS), quit.
# $3 is the activity the current layout should produce.
run_case() {
  local label="$1"
  local typing="$2"
  local want_activity="${3:-KeyboardEntry}"
  local log="$WORK/$label.log"
  force_home_boot
  ( cd "$FIRMWARE_DIR" && \
    CROSSPOINT_SIM_INPUT_SCRIPT="$NAV_TO_OWNER_FIELD;$typing;$((FIELD_OPEN_MS + 6000)):QUIT" \
    SDL_VIDEODRIVER=dummy "$BIN" >"$log" 2>&1 )
  if ! grep -q "Entering activity: $want_activity" "$log"; then
    echo "FAIL[$label]: never reached $want_activity -- either the Home/Settings row"
    echo "  counts in this script are stale, or the layout setting no longer selects it"
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

# The 13-grid layer of KeyboardEntryActivity.
set_keyboard_layout 1

# 1. Type, erase, commit. The two backspaces must apply where they arrived, so
#    the ZZ never reaches the stored name.
set_owner_name ""
run_case commit "$((FIELD_OPEN_MS + 400)):TYPE:CrossPoint QAZZ;$((FIELD_OPEN_MS + 1000)):TYPE:\\b\\b;$((FIELD_OPEN_MS + 1600)):TYPE:\\n"
expect_owner commit "CrossPoint QA"

# 2. Cancel. The field is seeded with what run 1 stored; typing then cancelling
#    must leave the stored name exactly as it was.
run_case cancel "$((FIELD_OPEN_MS + 400)):TYPE:ZZZ;$((FIELD_OPEN_MS + 1000)):TYPE:\\e"
expect_owner cancel "CrossPoint QA"

# 3. A commit with nothing typed stores the seed unchanged (the entry is not
#    emptied by the host having been attached).
run_case untouched "$((FIELD_OPEN_MS + 400)):TYPE:\\n"
expect_owner untouched "CrossPoint QA"

# 4. The daisywheel is a separate activity implementing the same channel, and
#    the owner can be on either. It has no cursor, so typed text appends at the
#    end -- which is where its own picks land too.
set_keyboard_layout 0
set_owner_name ""
run_case daisy "$((FIELD_OPEN_MS + 400)):TYPE:CrossPoint QAZZ;$((FIELD_OPEN_MS + 1000)):TYPE:\\b\\b;$((FIELD_OPEN_MS + 1600)):TYPE:\\n" DaisyEntry
expect_owner daisy "CrossPoint QA"

# --- The REAL key path -------------------------------------------------------
#
# Everything above injects at the typed queue (TYPE), which enters BELOW SDL and
# never meets the scancode gate in HalGPIO::update(). Both shipped bugs in this
# area lived in exactly that gate, so every scripted run passed while a human
# pressing the same key got the wrong thing. RAWKEY pushes a real
# SDL_EVENT_KEY_DOWN/UP, which is the only way from a script to see it.
#
# The contract for a SINGLE-LINE field (src/TextEntryKeyRouting.h): plain Return
# is BTN_CONFIRM -- Select on the on-screen keyboard, the key that types the
# highlighted character -- and Cmd/Ctrl+Return is the host typist's commit.
set_keyboard_layout 1

expect_owner_not() {
  local label="$1"
  local unwanted="$2"
  local got
  got="$(owner_name)"
  if [ "$got" = "$unwanted" ]; then
    echo "FAIL[$label]: ownerName is still \"$got\""
    exit 1
  fi
}

# 5. A plain Return must NOT commit: it is Select, so it types the highlighted
#    key and the field stays open. If it committed, the field would close on the
#    Return holding the seed unchanged and the later typed commit would be
#    dropped for want of an open field -- which is the "Select exits instead of
#    typing" bug, and is exactly what this distinguishes.
set_owner_name "SEED"
run_case raw_select "$((FIELD_OPEN_MS + 400)):RAWKEY:RETURN;$((FIELD_OPEN_MS + 1600)):TYPE:\\n"
expect_owner_not raw_select "SEED"

# 6. Cmd+Return is the commit, through the same real key path.
set_owner_name ""
run_case raw_commit "$((FIELD_OPEN_MS + 400)):TYPE:Ada;$((FIELD_OPEN_MS + 1000)):RAWKEY:CMD+RETURN"
expect_owner raw_commit "Ada"

echo "PASS: host keyboard typed, erased, committed and cancelled in both text-entry activities,"
echo "      and a real Return picks rather than commits in a single-line field"
exit 0
