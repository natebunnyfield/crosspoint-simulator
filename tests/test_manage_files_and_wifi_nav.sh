#!/usr/bin/env bash
# Headless end-to-end pins for three firmware navigation bugs from
# docs/ux-navigation-audit-2026-09-02.md, fixed on the fork 2026-09-02 at the
# owner's "All three" ruling. Each is a whole-activity behavior with no pure
# unit to extract (a ButtonNavigator callback, a latch cleared in a result
# lambda, a row re-found on onEnter), so the pin is the real firmware driven
# by CROSSPOINT_SIM_INPUT_SCRIPT and judged from its own `[ACT]` log lines.
#
#   F3  Wi-Fi list: the SIDE pair steps the networks. It paged a screenful
#       since f278be2fc, and ButtonNavigator::pageDown returns false on a
#       list that fits one screen, while front Right is Retry -- so nothing
#       moved the highlight down. Proof: four networks, ONE Down, Confirm
#       connects to the SECOND. Pre-fix Down is a no-op (Alpha); a page that
#       clamped would land on the last row (Delta); only a step gives Bravo.
#       Reasoned from ButtonNavigator.cpp:156, not measured on the old tree.
#   F6  Manage Files: View pushed a child while lockNextConfirmRelease was
#       latched, the release landed in the child, and the first Confirm back
#       on the list was eaten. Proof: View, Back, Confirm enters TextViewer
#       TWICE. The pre-fix tree enters it once (measured 2026-09-02).
#   F7  Manage Files -> Edit: the editor rebuilds the manager on exit
#       (replaceActivity) and it came back on row 0. Proof: the
#       `Re-focused '<name>' at row N` line names the edited note at its row,
#       AND the manager then ACTS on that row -- open the action menu, step to
#       Move (View, Edit, Rename, Duplicate, Move for a .md) and Confirm, which
#       logs `armMove entry='note1.md'`. The log line alone would pass a tree
#       that computed the row and then lost it (adversarial review 2026-09-02).
#
# Runs from a SCRATCH card (settings.json copied from the checkout's card,
# three notes at the root) so the real card is never written. Note the row
# arithmetic: the root lists `.crosspoint/` first, so the second note is row 2.
#
# Usage: tests/test_manage_files_and_wifi_nav.sh <firmware-checkout-dir>

set -u
FIRMWARE_DIR="${1:?usage: test_manage_files_and_wifi_nav.sh <firmware-checkout-dir>}"
BIN=""
for env_name in simulator_x3 simulator; do
  CANDIDATE="$FIRMWARE_DIR/.pio/build/$env_name/program"
  [ -x "$CANDIDATE" ] && { BIN="$CANDIDATE"; break; }
done
[ -n "$BIN" ] || { echo "SKIP: no simulator binary built under $FIRMWARE_DIR/.pio/build"; exit 2; }
SETTINGS="$FIRMWARE_DIR/fs_/.crosspoint/settings.json"
[ -f "$SETTINGS" ] || { echo "SKIP: $SETTINGS not found -- run the simulator once first"; exit 2; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# A fresh card per run: the FileManager runs rename nothing, but a shared card
# would carry one run's final state (and .crosspoint/state.json) into the next.
fresh_card() {
  rm -rf "$WORK/fs_"
  mkdir -p "$WORK/fs_/.crosspoint"
  cp "$SETTINGS" "$WORK/fs_/.crosspoint/settings.json"
  for n in aaa note1 zzz; do echo "hello $n" > "$WORK/fs_/$n.md"; done
}

# Home is forced by holding Back across the boot routing check
# (docs/headless-qa.md); with no recent books the menu starts on row 0, so
# RIGHT x2 is Manage Files and RIGHT x3 is File Transfer.
HOME_THEN="200:QTAP:BACK:2500;4000:RIGHT;4900:RIGHT"
run_script() {  # <log> <script> [extra env assignments...]
  local log="$1" script="$2"; shift 2
  fresh_card
  (cd "$WORK" && env "$@" SDL_VIDEODRIVER=dummy CROSSPOINT_SIM_INPUT_SCRIPT="$script" \
     timeout 45 "$BIN" > "$log" 2>&1)
}

fail=0

# F3 -- File Transfer -> Join Network popup -> Wi-Fi list -> DOWN -> Confirm.
run_script "$WORK/f3.log" \
  "$HOME_THEN;5800:RIGHT;6800:CONFIRM;8000:CONFIRM;12500:DOWN;13400:CONFIRM;17000:QUIT" \
  CROSSPOINT_SIM_WIFI_NETWORKS='Alpha:-40:open;Bravo:-50:open;Charlie:-60:open;Delta:-70:open'
if grep -q 'Entering activity: WifiSelection' "$WORK/f3.log" && grep -q 'Connecting to Bravo' "$WORK/f3.log"; then
  echo "PASS: F3 side pair stepped the Wi-Fi list (one DOWN -> Bravo)"
else
  echo "FAIL: F3 -- expected 'Connecting to Bravo' after one DOWN"; grep 'Entering activity\|Connecting to' "$WORK/f3.log"; fail=1
fi

# F6 -- Manage Files -> row 2 -> action menu -> View -> Back -> Confirm.
run_script "$WORK/f6.log" \
  "$HOME_THEN;5800:CONFIRM;7500:RIGHT;8400:RIGHT;9300:OPENMENU;10500:CONFIRM;12500:BACK;14000:CONFIRM;16000:QUIT"
viewer_entries=$(grep -c 'Entering activity: TextViewer' "$WORK/f6.log")
if [ "$viewer_entries" -eq 2 ]; then
  echo "PASS: F6 the first Confirm after View opened the viewer again"
else
  echo "FAIL: F6 -- TextViewer entered $viewer_entries time(s), expected 2"; grep 'Entering activity' "$WORK/f6.log"; fail=1
fi

# F7 -- Manage Files -> row 2 -> action menu -> RIGHT (Edit) -> Confirm -> Back,
# then action menu -> RIGHT x4 (Move) -> Confirm on whatever row came back.
run_script "$WORK/f7.log" \
  "$HOME_THEN;5800:CONFIRM;7500:RIGHT;8400:RIGHT;9300:OPENMENU;10300:RIGHT;11200:CONFIRM;13500:BACK;15000:OPENMENU;15900:RIGHT;16800:RIGHT;17700:RIGHT;18600:RIGHT;19500:CONFIRM;21000:QUIT"
if grep -q 'Entering activity: NoteEditor' "$WORK/f7.log" && grep -q "Re-focused 'note1.md' at row 2" "$WORK/f7.log" \
   && grep -q "armMove entry='note1.md'" "$WORK/f7.log"; then
  echo "PASS: F7 the manager came back on note1.md at row 2 and acted on it"
else
  echo "FAIL: F7 -- expected \"Re-focused 'note1.md' at row 2\" and \"armMove entry='note1.md'\""; grep 'Entering activity\|Re-focused\|armMove' "$WORK/f7.log"; fail=1
fi

exit $fail
