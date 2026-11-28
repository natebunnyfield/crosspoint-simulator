// THE PICCO PAD'S UP/DOWN PAIR -- the truth table for ios/PiccoPad.h.
//
// Owner 2026-11-27, verbatim: "just match x3 app and make it an ios app
// setting (default off)". The Picco app may show the X3's Up/Down pair in the
// place the X3 pad gives it (the row the Picco's rocker vacated), pressing the
// X3's side pair. Three things here can only go wrong silently on a phone:
//
//  1. OFF IS TODAY'S PAD. With the setting off nothing is placed, so the two
//     reused slots stay zero rects and the pad draws exactly what it did.
//  2. IT NEVER SITS ON ANOTHER CONTROL. The owner's rule: it must not overlap
//     or displace POWER, the slide switch, the keyboard chip, Select or the
//     rocker. If the X3's place collides with any of them in some layout, the
//     pair is NOT placed (and the shim logs which), rather than moving them.
//  3. UP IS THE X3's UP. The X3 pad's pair puts Up on the LEFT half, so the
//     left rect presses the side Up key and the right the side Down -- not the
//     Picco rocker's swapped halves.
#include <cstdio>

#include "../ios/PiccoPad.h"

using piccopad::Rect;

static int failures = 0;
static void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("  FAIL: %s\n", what);
    ++failures;
  }
}
static bool same(Rect a, Rect b) {
  return a.x == b.x && a.y == b.y && a.w == b.w && a.h == b.h;
}

int main() {
  // A phone-portrait-like bottom row: POWER and the switch on the left, the
  // chip in the middle, the X3's Up|Down pair on the right.
  const Rect up{600, 2400, 150, 75}, down{750, 2400, 150, 75};
  const Rect power{150, 2400, 150, 75}, sw{308, 2400, 142, 75};
  const Rect chip{480, 2400, 75, 75};
  const Rect select{150, 2200, 150, 150}, rockerL{600, 2200, 150, 150},
      rockerR{750, 2200, 150, 150};
  const Rect others[] = {power, sw, chip, select, rockerL, rockerR};
  const int n = static_cast<int>(sizeof(others) / sizeof(others[0]));

  // 1. Off: nothing placed.
  {
    const auto p = piccopad::sidePair(false, up, down, others, n);
    check(!p.placed, "off places nothing");
    check(p.up.w == 0 && p.down.w == 0, "off leaves zero rects (today's pad)");
  }
  // On, clear of everything: the X3's own rects, Up on the left.
  {
    const auto p = piccopad::sidePair(true, up, down, others, n);
    check(p.placed, "on and clear: placed");
    check(same(p.up, up) && same(p.down, down), "the X3's place, unchanged");
    check(p.up.x < p.down.x, "Up is the LEFT half, as on the X3 pad");
    check(p.collidesWith < 0, "no collision reported");
  }
  // 2. A collision with any one control refuses the pair and names it.
  for (int i = 0; i < n; ++i) {
    Rect moved[6];
    for (int j = 0; j < n; ++j) moved[j] = others[j];
    moved[i] = Rect{down.x + 10, down.y + 10, 20, 20};  // inside Down
    const auto p = piccopad::sidePair(true, up, down, moved, n);
    check(!p.placed, "a collision refuses the pair");
    check(p.collidesWith == i, "and names the control it hit");
  }
  // Touching edges is not an overlap (the X3 pad's pairs abut).
  {
    const Rect abut[] = {Rect{up.x - 50, up.y, 50, 75}};
    check(piccopad::sidePair(true, up, down, abut, 1).placed, "abutting is fine");
  }
  // A zero (retired or not-laid-out) control collides with nothing.
  {
    const Rect zero[] = {Rect{0, 0, 0, 0}};
    check(piccopad::sidePair(true, up, down, zero, 1).placed, "zero rects ignored");
  }
  // No X3 place yet (a layout with no Up/Down pair, or before the first pass):
  // nothing placed, nothing invented.
  {
    const auto p = piccopad::sidePair(true, Rect{0, 0, 0, 0}, down, others, n);
    check(!p.placed && p.up.w == 0, "no X3 place, no pair");
  }

  if (failures) {
    std::printf("picco_pad: %d FAILURES\n", failures);
    return 1;
  }
  std::printf("picco_pad: all checks passed\n");
  return 0;
}
