#pragma once

#include <cstdint>

// THE ONE-FINGER HOLD'S THRESHOLD AND ITS BOOKKEEPING.
//
// WHAT IT DOES IS NO LONGER DECIDED HERE. Owner ruling 2026-08-28 (T-025): every
// gesture is configurable from Settings.app, so the hold's action comes from
// ios/GestureBindings.h with all the others -- above the paper and below it are
// rows, the paper itself is fixed. This header kept the two things that are not
// a mapping: the duration, and the state of a hold in flight.
//
// THE RULE THAT USED TO LIVE HERE, kept because the succession explains the
// shape the new one inherited. Owner, 2026-08-27: "change long tap to only swap
// zen/singlefinger modes if tap held for .75 sec above paper, if held below top
// of paper in zen mode, make it a select after .75 before lift." That was ONE
// duration and TWO ZONES, where there had been two durations and one zone:
//
//   1. A 5 s hold toggled, anywhere, while a 0.75 s hold selected in zen. A hold
//      on its way to 5 s crossed 0.75 s, so one gesture wanted to fire two
//      things.
//   2. The select was moved to the LIFT so a long hold could suppress it. That
//      worked, but it cost the stock iOS long-press feel the owner had asked for
//      on 2026-08-22 -- the action no longer happened under the finger.
//   3. Splitting by POSITION removed the collision at its root. The two actions
//      can never both apply: a touch is either above the paper or it is not. So
//      the select went back to firing while held, and the 5 s wait went with the
//      second threshold.
//
// One threshold, one recognizer, no simultaneity delegate, no lift bookkeeping,
// and no latch to suppress a second action -- there is no second action to
// suppress. T-025 added a third ZONE below the paper and made two of the three
// assignable; it did not add a second threshold, and must not.
namespace zenhold {

// Milliseconds. The owner's device-tuned long-press threshold, unchanged since
// 2026-08-22 ("long tap select is too fast. make at least 1.5x longer").
constexpr uint32_t kHoldMs = 750;

// The bookkeeping for the hold in flight.
class Hold {
 public:
  // A hold fires at most one action, so a single fired-flag is enough to
  // survive UIKit re-delivering .began (it does on some paths, and two toggles
  // in one gesture cancel out -- which reads on device as the gesture doing
  // nothing at all).
  void begin() {
    poisoned_ = false;
    fired_ = false;
  }

  // Called with the recognizer's live touch count; anything but exactly one
  // kills the hold. A hand resting on the glass is not a deliberate press.
  void noteTouches(int touches) {
    if (touches != 1) poisoned_ = true;
  }

  // iOS took the touch for its own gesture (.cancelled / .failed).
  void cancel() { poisoned_ = true; }

  bool poisoned() const { return poisoned_; }
  bool fired() const { return fired_; }

  // MAY THIS HOLD ACT NOW? True at most once per hold, and never for a poisoned
  // one. The caller asks only when it has an action to perform, so a hold bound
  // to Nothing leaves the tracker unlatched exactly as a poisoned one does --
  // which matters because latching is what a re-delivered .began is tested
  // against, and there is nothing to protect when nothing happens.
  bool claim() {
    if (fired_ || poisoned_) return false;
    fired_ = true;
    return true;
  }

 private:
  bool poisoned_ = false;
  bool fired_ = false;
};

}  // namespace zenhold
