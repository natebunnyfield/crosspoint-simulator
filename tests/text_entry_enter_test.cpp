// Who owns Return while a firmware text field is open (src/TextEntryKeyRouting.h).
//
// WHY THIS IS A TEST AND NOT A COMMENT. Both shipped bugs in this area were
// one-line routing mistakes that no test could see, because every headless
// script in this repo injects below SDL (syntheticButtonDown[] / the typed
// queue) and never meets the scancode gate at all:
//
//   * Return committed a single-line field instead of picking, so Select on
//     the daisywheel left the screen rather than typing a character.
//   * Return pressed Select in the MULTI-LINE note editor instead of breaking
//     the line (ST-006).
//
// The two fixes pull in opposite directions on the same key, which is exactly
// the shape of thing that gets reverted by the next person to read only one of
// the bug reports. The table below is the contract; the end-to-end proof that
// HalGPIO is wired to it is tests/test_text_entry.sh plus the RAWKEY script
// action, which pushes real SDL key events.
#include "TextEntryKeyRouting.h"

#include <cstdio>
#include <cstdlib>

using textentry::EnterOwner;
using textentry::enterOwner;
using textentry::Lines;

static int failures = 0;

static const char *ownerName(EnterOwner owner) {
  return owner == EnterOwner::Button ? "Button" : "Text";
}

static void expectOwner(Lines lines, bool modifierHeld, EnterOwner want,
                        const char *why) {
  const EnterOwner got = enterOwner(lines, modifierHeld);
  if (got == want)
    return;
  std::printf("FAIL: %s%s Return -> %s, expected %s\n    %s\n",
              modifierHeld ? "Cmd+" : "plain ",
              lines == Lines::Multi ? " (multi-line)" : " (single-line)",
              ownerName(got), ownerName(want), why);
  failures++;
}

int main() {
  // Single-line: the field is one line, so Return has no line to break. It is
  // Select on the on-screen keyboard -- the key that types the highlighted
  // character -- and taking it away broke character entry outright.
  expectOwner(Lines::Single, false, EnterOwner::Button,
              "Select on the daisywheel/grid must still type; committing here "
              "is the 'Select exits instead of typing' bug");
  // ...and the host typist who wants to finish the field without hunting for
  // the on-screen OK key keeps the modified chord.
  expectOwner(Lines::Single, true, EnterOwner::Text,
              "Cmd/Ctrl+Return is the host typist's commit for single-line "
              "fields (Wi-Fi password, Device owner, rename)");

  // Multi-line: Return is a line break, the same thing a Bluetooth keyboard's
  // Enter does on real hardware (firmware src/notes/HidKeymap.h maps HID usage
  // 0x28 to '\n'). This is ST-006.
  expectOwner(Lines::Multi, false, EnterOwner::Text,
              "ST-006: Return in the note editor must insert a line break, not "
              "press Select");
  // ...and the on-screen panel does not lose its pick on a desktop keyboard,
  // where Return is the only key bound to BTN_CONFIRM.
  expectOwner(Lines::Multi, true, EnterOwner::Button,
              "Cmd/Ctrl+Return keeps the on-screen panel's pick reachable in a "
              "multi-line editor");

  if (failures != 0) {
    std::printf("%d failure(s)\n", failures);
    return 1;
  }
  std::printf("PASS: Return routing matches the contract in all four states\n");
  return 0;
}
