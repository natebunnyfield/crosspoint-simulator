// THE ONE-FINGER HOLD'S BOOKKEEPING -- ios/ZenHoldRouting.h.
//
// WHAT THE HOLD DOES is no longer decided here. Owner ruling 2026-08-28
// (T-025): every gesture is configurable, so the hold's action comes from
// ios/GestureBindings.h with all the others and its truth table is
// tests/gesture_bindings_test.cpp -- including the three-zone split, the
// defaults that reproduce the two-zone rule this file used to pin, and the zen
// gate. What is left here is the part that is not a mapping: the tracker for
// one hold in flight.
//
// It is still worth its own test, because all three of its failure modes are
// silent on a device and none can be driven off-device -- UIKit's recognizers
// live above SDL, where no input script and no simctl can synthesize a touch:
//
//  * a STALE poison. This shipped, on 2026-08-27: out of zen nothing called the
//    tracker's lifecycle, a flag went stale, and the hold died in one mode with
//    nothing in the log to say why. begin() must scrub.
//  * a STALE latch, the same bug wearing the other flag: the hold fires once
//    and then never again for the life of the app.
//  * a MISSING latch, which lets UIKit's re-delivered .began fire twice -- and
//    two zen toggles in one gesture cancel out, which reads on device as the
//    gesture doing nothing at all.
#include <cassert>
#include <cstdio>

#include "../ios/ZenHoldRouting.h"

static int failures = 0;

static void check(bool ok, const char* what) {
  if (!ok) {
    std::printf("  FAIL: %s\n", what);
    failures++;
  }
}

int main() {
  // ---- The latch: one action per hold, however often .began is delivered. ----
  {
    zenhold::Hold h;
    h.begin();
    h.noteTouches(1);
    check(h.claim(), "the first .began may act");
    check(!h.claim(), "a re-delivered .began may NOT act again");
    check(h.fired(), "and the hold reports itself fired");
  }

  // ---- A poisoned hold may never act, however it was poisoned. ----
  {
    zenhold::Hold h;
    h.begin();
    h.noteTouches(2);  // a second finger: a hand on the glass, not a press
    check(h.poisoned(), "two touches poison the hold");
    check(!h.claim(), "a poisoned hold may not act");
  }
  {
    zenhold::Hold h;
    h.begin();
    h.noteTouches(0);
    check(h.poisoned(), "zero touches poison the hold too");
    check(!h.claim(), "...and it still may not act");
  }
  {
    zenhold::Hold h;
    h.begin();
    h.noteTouches(1);
    h.cancel();  // iOS took the touch for its own gesture (.cancelled/.failed)
    check(!h.claim(), "a cancelled hold may not act");
  }

  // ---- A NEW hold is clean, with no release in between. ----
  //
  // The 2026-08-27 defect in one line: out of zen nothing called the tracker's
  // lifecycle, so a stale flag killed every later hold. begin() must scrub.
  {
    zenhold::Hold h;
    h.begin();
    h.noteTouches(2);  // poisoned
    check(!h.claim(), "stale: a poisoned hold does nothing");
    h.begin();         // a NEW hold, nothing else called
    h.noteTouches(1);
    check(h.claim(), "regression: begin() scrubs an inherited poison");
  }
  {
    zenhold::Hold h;
    h.begin();
    h.noteTouches(1);
    check(h.claim(), "fires once");
    h.begin();  // a NEW hold, nothing else called
    h.noteTouches(1);
    check(h.claim(), "regression: begin() scrubs an inherited fired-latch");
  }

  // ---- A second finger mid-hold poisons, but cannot un-fire. ----
  {
    zenhold::Hold h;
    h.begin();
    h.noteTouches(1);
    check(h.claim(), "the action fires");
    h.noteTouches(2);  // a second finger arrives after the action
    check(h.poisoned(), "the late second finger still poisons");
    check(h.fired(), "...and cannot un-fire what already happened");
    check(!h.claim(), "...nor produce a second action");
  }

  // ---- A HOLD THAT DOES NOTHING LEAVES THE TRACKER UNLATCHED. ----
  //
  // The caller asks claim() only when it has an action to perform, so a hold
  // bound to Nothing never latches -- there is nothing for the latch to
  // protect. Stated as a test because the plausible alternative (latch at
  // .began, unconditionally) would make an unbound hold poison the re-delivery
  // path for a hold that IS bound, which is exactly the kind of coupling
  // between two settings this feature is not allowed to have.
  {
    zenhold::Hold h;
    h.begin();
    h.noteTouches(1);
    check(!h.fired(), "a hold that never claims has not fired");
    check(h.claim(), "...so it is still free to act");
  }

  // ---- The threshold is the owner's, and there is only ONE. ----
  check(zenhold::kHoldMs == 750,
        "the hold threshold is the owner's 0.75 s, shared by every zone");

  if (failures == 0) {
    std::printf("zen_hold_test: all checks passed\n");
    return 0;
  }
  std::printf("zen_hold_test: %d FAILURES\n", failures);
  return 1;
}
