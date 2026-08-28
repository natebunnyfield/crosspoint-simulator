// What a one-finger hold does, decided by WHERE IT LANDS.
//
// Owner, 2026-08-27: "change long tap to only swap zen/singlefinger modes if
// tap held for .75 sec above paper, if held below top of paper in zen mode,
// make it a select after .75 before lift."
//
// One threshold, two zones:
//
//   above the paper -> Toggle, in EITHER mode
//   on the paper    -> Select, in ZEN ONLY
//
// Three inversions, all silent on a device, which is why this is a truth table
// and not a comment:
//
//  * a toggle that stops firing in ONE mode. This already shipped once, on
//    2026-08-27 (the tracker's lifecycle was owned by a zen-only recognizer, so
//    it went stale out of zen). It is the reason the mode is an ARGUMENT to the
//    rule rather than a property of which recognizer is enabled.
//  * a select fired OUTSIDE zen, where there is no selection to make and the
//    press reaches the reader as a stray CONFIRM.
//  * one hold firing BOTH, which is what the previous two-threshold shape had
//    to work to avoid and this shape cannot express.
#include <cassert>
#include <cstdio>

#include "../ios/ZenHoldRouting.h"

using zenhold::Action;
using zenhold::Zone;

static int failures = 0;

static void check(bool ok, const char* what) {
  if (!ok) {
    std::printf("  FAIL: %s\n", what);
    failures++;
  }
}

static void checkAction(Action got, Action want, const char* what) {
  if (got != want) {
    std::printf("  FAIL: %s (got '%s', want '%s')\n", what,
                zenhold::actionName(got), zenhold::actionName(want));
    failures++;
  }
}

int main() {
  // ---- The rule, all four combinations of zone and mode. ----
  checkAction(zenhold::onHold(Zone::AbovePaper, false, false), Action::Toggle,
              "above the paper, zen OFF -> toggle (the way IN)");
  checkAction(zenhold::onHold(Zone::AbovePaper, true, false), Action::Toggle,
              "above the paper, zen ON -> toggle (the way OUT)");
  checkAction(zenhold::onHold(Zone::OnPaper, true, false), Action::Select,
              "on the paper, zen ON -> select");
  checkAction(zenhold::onHold(Zone::OnPaper, false, false), Action::None,
              "on the paper, zen OFF -> NOTHING (no stray CONFIRM)");

  // ---- The toggle works in BOTH modes. This is the shipped-once bug. ----
  check(zenhold::onHold(Zone::AbovePaper, false, false) ==
            zenhold::onHold(Zone::AbovePaper, true, false),
        "the toggle does not depend on the mode it is toggling");

  // ---- Poison kills everything, in every zone and mode. ----
  const Zone kZones[] = {Zone::AbovePaper, Zone::OnPaper};
  const bool kModes[] = {false, true};
  for (Zone z : kZones)
    for (bool zen : kModes)
      checkAction(zenhold::onHold(z, zen, true), Action::None,
                  "a poisoned hold fires nothing, whatever the zone");

  // ---- The latch: one action per hold, however often .began is delivered. ----
  {
    zenhold::Hold h;
    h.begin();
    h.noteTouches(1);
    checkAction(h.resolve(Zone::AbovePaper, false), Action::Toggle,
                "first .began toggles");
    checkAction(h.resolve(Zone::AbovePaper, true), Action::None,
                "a re-delivered .began does NOT toggle back");
    checkAction(h.resolve(Zone::OnPaper, true), Action::None,
                "nor select afterwards -- one action per hold");
  }

  // ---- A NEW hold is clean, with no release in between. ----
  //
  // The 2026-08-27 defect in one line: out of zen nothing called the tracker's
  // lifecycle, so a stale flag killed every later hold. begin() must scrub.
  {
    zenhold::Hold h;
    h.begin();
    h.noteTouches(2);  // poisoned
    checkAction(h.resolve(Zone::AbovePaper, false), Action::None,
                "stale: a poisoned hold does nothing");
    h.begin();  // a NEW hold, nothing else called
    h.noteTouches(1);
    checkAction(h.resolve(Zone::AbovePaper, false), Action::Toggle,
                "regression: begin() scrubs an inherited poison");
  }
  {
    zenhold::Hold h;
    h.begin();
    h.noteTouches(1);
    checkAction(h.resolve(Zone::AbovePaper, false), Action::Toggle, "fires once");
    h.begin();  // a NEW hold, nothing else called
    h.noteTouches(1);
    checkAction(h.resolve(Zone::AbovePaper, false), Action::Toggle,
                "regression: begin() scrubs an inherited fired-latch");
  }

  // ---- A second finger mid-hold poisons, but cannot un-fire. ----
  {
    zenhold::Hold h;
    h.begin();
    h.noteTouches(1);
    checkAction(h.resolve(Zone::OnPaper, true), Action::Select, "select fires");
    h.noteTouches(2);  // a second finger arrives after the action
    check(h.poisoned(), "the late second finger still poisons");
    checkAction(h.resolve(Zone::OnPaper, true), Action::None,
                "and cannot produce a second action");
  }

  // ---- A cancelled hold fires nothing. ----
  {
    zenhold::Hold h;
    h.begin();
    h.noteTouches(1);
    h.cancel();
    checkAction(h.resolve(Zone::AbovePaper, false), Action::None,
                "iOS took the touch -> nothing");
  }

  // ---- The threshold is the owner's, and there is only ONE now. ----
  check(zenhold::kHoldMs == 750,
        "the hold threshold is the owner's 0.75 s, shared by both actions");

  if (failures == 0) {
    std::printf("zen_hold_test: all checks passed\n");
    return 0;
  }
  std::printf("zen_hold_test: %d FAILURES\n", failures);
  return 1;
}
