#pragma once

#include <cstdint>

// WHAT A ONE-FINGER HOLD DOES, decided by WHERE IT LANDS.
//
// Owner, 2026-08-27: "change long tap to only swap zen/singlefinger modes if
// tap held for .75 sec above paper, if held below top of paper in zen mode,
// make it a select after .75 before lift."
//
// So there is now ONE duration and TWO ZONES, where there used to be two
// durations and one zone:
//
//   above the paper   -> toggle zen <-> single-finger, in EITHER mode
//   on or below it    -> Select (BTN_CONFIRM), in ZEN ONLY
//
// Both fire at 0.75 s with the finger still down. Nothing happens on the lift.
//
// THIS IS THE THIRD SHAPE THIS RULE HAS HAD IN ONE DAY, and the succession is
// worth keeping because each step removed a real cost:
//
//  1. A 5 s hold toggled, anywhere, while a 0.75 s hold selected in zen. A hold
//     on its way to 5 s crossed 0.75 s, so one gesture wanted to fire two
//     things.
//  2. The select was moved to the LIFT so a long hold could suppress it. That
//     worked, but it cost the stock iOS long-press feel the owner had asked for
//     on 2026-08-22 -- the action no longer happened under the finger.
//  3. Splitting by POSITION removes the collision at its root. The two actions
//     can now share a threshold because they can never both apply: a touch is
//     either above the paper or it is not. So the select goes back to firing
//     while held, and the 5 s wait is gone from the toggle as well.
//
// The simplification is the point. One threshold, one recognizer, no
// simultaneity delegate, no lift bookkeeping, and no latch to suppress a second
// action -- there is no second action to suppress.
namespace zenhold {

// Milliseconds. The owner's device-tuned long-press threshold, unchanged since
// 2026-08-22 ("long tap select is too fast. make at least 1.5x longer") and now
// serving both actions.
constexpr uint32_t kHoldMs = 750;

enum class Action {
  None,
  Select,  // BTN_CONFIRM -- zen only, and only at or below the paper's top
  Toggle,  // zen <-> single-finger -- either mode, above the paper
};

// Where the finger landed, relative to the top edge of the visible paper.
//
// "Above the paper" is the strip of ground above the sheet -- the bezel and the
// safe-area cut-out -- not merely the top of the page. The card's top edge is
// where black ends and paper begins (`g_cardTopPx`), which is published on
// every layout pass in BOTH modes, so this question has an answer even on the
// launch before zen has ever been entered.
enum class Zone {
  AbovePaper,
  OnPaper,
};

// THE WHOLE RULE.
//
// Pure so the three ways it can be wrong are provable off-device, and each of
// them is silent: a toggle that also selects, a select that fires outside zen
// (where there is no selection to make and the press would reach the reader as
// a stray CONFIRM), and a toggle that stops working in one mode -- which is
// exactly the defect reported and fixed earlier today.
constexpr Action onHold(Zone zone, bool zenOn, bool poisoned) {
  if (poisoned) return Action::None;
  if (zone == Zone::AbovePaper) return Action::Toggle;
  return zenOn ? Action::Select : Action::None;
}

// The bookkeeping for the hold in flight. Smaller than what it replaces because
// there is no lift action and no cross-action latch left to keep.
class Hold {
 public:
  // A hold cannot both toggle and select, so a single fired-flag is enough to
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

  // The 0.75 s mark arrived with the finger still down. Latches.
  Action resolve(Zone zone, bool zenOn) {
    if (fired_) return Action::None;
    const Action a = onHold(zone, zenOn, poisoned_);
    if (a != Action::None) fired_ = true;
    return a;
  }

 private:
  bool poisoned_ = false;
  bool fired_ = false;
};

constexpr const char* actionName(Action a) {
  return a == Action::Select ? "select" : a == Action::Toggle ? "toggle" : "none";
}

}  // namespace zenhold
