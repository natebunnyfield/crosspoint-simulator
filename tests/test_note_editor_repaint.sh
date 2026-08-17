#!/usr/bin/env bash
# Headless end-to-end test: typing into a NOTE on a host keyboard repaints the
# note, including while the host's own software keyboard is up.
#
# WHAT IS UNDER TEST, and why it is a screenshot rather than a file.
# tests/test_text_entry.sh already covers the host-keyboard CHANNEL end to end
# (Settings > Device owner, a SINGLE-line field, asserted against the persisted
# settings.json). It cannot see this bug at all: the bug was never in the
# channel. NoteEditorActivity drained the typed text into its buffer correctly
# and SAVED it correctly -- and never called relayout()/requestUpdate() again,
# because its debounced repaint sat at the bottom of loop(), below an early
# `if (panelHidden) return;`. panelHidden is true exactly when a host software
# keyboard is up, which is every iPhone note. Reported as "create note with iOS
# keyboard: not updating while typing at all", and the file-contents assertion
# that catches everything else PASSES throughout, which is why this test
# compares frames instead.
#
# So the load-bearing assertion is: the frame captured before typing and the
# frame captured after it must DIFFER. Under CROSSPOINT_SIM_HOST_KEYBOARD=1
# they were byte-identical (md5 a04d4495e702ddf650f91cb46381f7f4 twice) before
# the fix.
#
# Both polarities of the host keyboard are run. The =0 arm is the control: it
# was already working, and a change that fixes =1 by breaking =0 is not a fix.
#
# WHAT IT CANNOT COVER. TYPE injects at the queue (injectTypedText), the same
# entry point the iOS harness uses, but not the real SDL key path -- see
# test_text_entry.sh's note on that, and ios/README.md. It also cannot prove
# anything about what the PHONE draws; it proves the firmware repaints when a
# host keyboard is up, which is the half that was dead.
#
# Usage: tests/test_note_editor_repaint.sh <firmware-checkout-dir>

set -u
FIRMWARE_DIR="${1:?usage: test_note_editor_repaint.sh <firmware-checkout-dir>}"
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
# Create Note writes a NEW YYYYMMDDHHmmss.md into the card root every run, so
# the test cleans up after itself rather than growing the fixture card.
ls "$FIRMWARE_DIR/fs_" >"$WORK/root.before"
restore() {
  cp "$WORK/settings.json.orig" "$SETTINGS" 2>/dev/null
  [ -f "$WORK/state.json.orig" ] && cp "$WORK/state.json.orig" "$STATE"
  if [ -f "$WORK/root.before" ]; then
    ls "$FIRMWARE_DIR/fs_" >"$WORK/root.after" 2>/dev/null
    comm -13 "$WORK/root.before" "$WORK/root.after" 2>/dev/null | while read -r f; do
      case "$f" in *.md) rm -f "$FIRMWARE_DIR/fs_/$f" ;; esac
    done
  fi
  rm -rf "$WORK"
}
trap restore EXIT

# Pin the redraw debounce rather than inheriting the card's: the flush this test
# is about is gated on it (SETTINGS.getDisplayDebounceMs()), so a card left on
# the 1000 ms step would decide the answer by timing. 3 == 250 ms.
python3 -c "
import json
p = '$SETTINGS'
d = json.load(open(p)); d['displayDebounce'] = 3
json.dump(d, open(p, 'w'))"

# Booting into the last book is deliberate; a non-zero crash-recovery counter is
# the only lever a headless script has to land on Home. See the simulator's
# CLAUDE.md.
force_home_boot() {
  [ -f "$STATE" ] || return 0
  python3 -c "
import json
p = '$STATE'
d = json.load(open(p)); d['readerActivityLoadCount'] = 1
json.dump(d, open(p, 'w'))"
}

# Home: RIGHT, not DOWN. Lists navigate on the FRONT pair -- the side buttons
# page by a screenful, and a one-screen menu has no next screenful, so DOWN here
# does nothing at all (correctly). See docs/headless-qa.md.
#
# RIGHT x15 walks past every recent book to the last row (Settings; the list
# does not wrap), then LEFT counts back up to Create Note. The count depends on
# whether the Update Firmware row is compiled in (CROSSPOINT_NO_DEVICE_FLASH),
# so it is ASSERTED from the log rather than trusted -- same rule as
# test_text_entry.sh's Settings row count.
NAV="2000:HOME"
T=2400
for _ in $(seq 1 15); do
  NAV="$NAV;$T:RIGHT"
  T=$((T + 250))
done
NAV="$NAV;6600:LEFT;6900:LEFT;7200:LEFT;8000:ENTER"

# One arm. $1 is the CROSSPOINT_SIM_HOST_KEYBOARD value, $2 a label.
run_arm() {
  local hk="$1"
  local label="$2"
  local log="$WORK/$label.log"
  local before="$WORK/$label.before.bmp"
  local after="$WORK/$label.after.bmp"
  force_home_boot
  ( cd "$FIRMWARE_DIR" && \
    CROSSPOINT_SIM_HOST_KEYBOARD="$hk" \
    CROSSPOINT_SIM_INPUT_SCRIPT="$NAV;10000:TYPE:hello world;13000:BACK;15000:QUIT" \
    CROSSPOINT_SIM_SCREENSHOTS="9500:$before;12500:$after" \
    SDL_VIDEODRIVER=dummy "$BIN" >"$log" 2>&1 )

  if ! grep -q "Entering activity: NoteEditor" "$log"; then
    echo "FAIL[$label]: never reached NoteEditor -- the Home row counts in this"
    echo "  script are stale (did the Home menu gain or lose a row?)"
    grep "Entering activity" "$log" | tail -5
    exit 1
  fi
  # Multi-line, not Single: a note editor's Return is a line break. If this
  # regresses, Return starts pressing Select on the on-screen panel (ST-006).
  if ! grep -q "\[TEXT\] text entry active (multi-line)" "$log"; then
    echo "FAIL[$label]: the editor did not announce a MULTI-line field to the host"
    grep "\[TEXT\]" "$log" | tail -5
    exit 1
  fi
  [ -s "$before" ] && [ -s "$after" ] || {
    echo "FAIL[$label]: a frame was not captured ($before / $after)"
    exit 1
  }

  # The buffer half: the typed text reached the note and was written out. This
  # passed throughout the bug and is here to keep the frame assertion honest --
  # two identical frames because nothing was ever typed would be a different
  # failure with the same symptom.
  if ! grep -q "saved 11/11 bytes" "$log"; then
    echo "FAIL[$label]: the typed text did not reach the note buffer"
    grep "NOTEEDIT" "$log" | tail -5
    exit 1
  fi

  if cmp -s "$before" "$after"; then
    echo "FAIL[$label]: the note did not repaint while typing -- the frame before"
    echo "  the keystrokes and the frame after them are byte-identical, though the"
    echo "  characters did reach the buffer (see 'saved 11/11 bytes' above)."
    echo "  This is the reported bug: with a host software keyboard up, the"
    echo "  editor's debounced relayout()/requestUpdate() is not reached."
    exit 1
  fi
}

# 1. Control: no host software keyboard, so the firmware's own on-screen panel
#    is up and the editor takes its ordinary path.
run_arm 0 panel_visible

# 2. The reported case: a host software keyboard is up, the panel is hidden and
#    the phone's keyboard is the only way to type.
run_arm 1 host_keyboard

echo "PASS: a note repaints while a host keyboard types into it, with the firmware's"
echo "      panel visible AND with a host software keyboard covering it"
exit 0
