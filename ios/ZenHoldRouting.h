#pragma once

#include <cstdint>

// ONE-FINGER HOLD ROUTING — two thresholds, three outcomes, on one gesture.
//
// Owner ask, 2026-08-27: *"holding down one finger longer than five seconds
// toggles zen and single finger modes."* "Single finger mode" is his own term
// for NOT-zen (he disambiguated it on 2026-08-22: "remove the color button
// from single finger (not zen) mode ui"), so this is a toggle BETWEEN the two
// modes, reachable from both sides — not a new mode.
//
// That lands on top of the zen LONG-PRESS SELECT (owner 2026-08-22, "in zen
// mode, long tap is select button (please use apple for this so everything
// works as expected)", threshold widened the same day to 0.75 s: "long tap
// select is too fast. make at least 1.5x longer"). A five-second hold crosses
// 0.75 s on its way, so in zen ONE hold wanted to fire TWO things.
//
// OWNER RULING, 2026-08-27, resolving it: **select fires on LIFT, not while
// held.** A hold of 0.75 s .. 5 s selects when the finger comes up; a hold that
// reaches 5 s toggles zen at the 5 s mark, while still held, and then the lift
// does nothing. Exactly one action per hold, never both, never neither-by-
// accident.
//
// This deliberately reverses the .began feel of the 2026-08-22 ruling — an iOS
// long press normally fires under the finger. The owner accepted that cost
// knowingly when the alternative was presented; see
// ios/CrossPointZenRecognizers.mm, where the superseded note is kept beside its
// replacement rather than deleted.
//
// WHY THIS IS A HEADER AND NOT AN `if` IN THE RECOGNIZER ACTION. Both
// inversions of a two-way routing rule are SILENT — a select that stops firing
// looks like a gesture the phone did not deliver, and a select that fires
// alongside the toggle looks like the toggle misfiring — and the repo has
// already paid for exactly that shape once: src/TextEntryKeyRouting.h exists
// because both inversions of the Return-key rule shipped as bugs. Nothing here
// can be proven on device by a screenshot, so the truth table is proven off it
// (tests/zen_hold_test.cpp) and the recognizer only reports events into it.
//
// Same discipline as ZenVerbs.h and PadCore.h beside it: pure, no clock of its
// own, no SDL and no UIKit types. The caller supplies the timestamps.
//
// THE RULES, each one a way a real hand fails:
//
//   * < 0.75 s          -> nothing. That is a tap, and the tap belongs to the
//                          SDL deliberate-tap classifier (ZenVerbs.h, 400 ms
//                          ceiling). The two windows do not overlap.
//   * >= 0.75 s, < 5 s  -> SELECT, on the lift.
//   * >= 5 s            -> TOGGLE, at the 5 s mark while held; the lift is
//                          then silent. Both the elapsed time AND a latched
//                          flag say so, because the lift and the 5 s deadline
//                          can arrive in either order at the boundary.
//   * poisoned          -> nothing at all. A touch iOS takes for its own
//                          gesture (cancel), or a second finger landing
//                          mid-hold, kills the whole hold — same discipline as
//                          ZenVerbs.h, where a rolling hand is not a tap.
//
// The poison and the toggle latch both clear on the NEXT begin(), which is the
// other silent failure this pins: a sticky poison would mean select never
// fires again and nothing would say why.
namespace zenhold {

// Milliseconds. `kSelect` is the owner's device-tuned long-press threshold and
// is NOT re-tuned here — only WHEN it fires changed. `kToggle` is his five
// seconds.
constexpr uint32_t kSelectMs = 750;
constexpr uint32_t kToggleMs = 5000;

// The ordering IS the rule. Inverted, a hold would toggle before it could
// select and the select window would be empty — invisible at runtime, so it is
// a compile error instead. (Prefer a gate over a paragraph.)
static_assert(kSelectMs < kToggleMs,
              "the select window must open before the toggle deadline");

enum class Action {
  None,
  Select,  // BTN_CONFIRM, on the lift
  Toggle,  // zen <-> not-zen, at the 5 s mark under the finger
};

inline const char *actionName(Action a) {
  switch (a) {
    case Action::Select: return "select";
    case Action::Toggle: return "toggle";
    default: return "none";
  }
}

// The two pure decisions, separated from the bookkeeping so a truth table can
// address them directly.

// What a finished hold did, given how long it lasted, whether the touch was
// poisoned, and whether the 5 s deadline had already fired.
constexpr Action onRelease(uint32_t holdMs, bool poisoned, bool alreadyToggled) {
  if (poisoned) return Action::None;
  if (alreadyToggled || holdMs >= kToggleMs) return Action::None;
  if (holdMs >= kSelectMs) return Action::Select;
  return Action::None;
}

// What the 5 s deadline does when it is reached with the finger still down.
// Fires once per hold: a recognizer can be asked twice (UIKit re-delivers
// .began after a .changed on some paths) and two toggles would cancel out,
// which reads on device as the gesture doing nothing at all.
constexpr Action onToggleDeadline(bool poisoned, bool alreadyToggled) {
  if (poisoned || alreadyToggled) return Action::None;
  return Action::Toggle;
}

// The bookkeeping: one hold at a time, fed by the recognizer actions.
//
// begin() takes the time the FINGER WENT DOWN, not the time the recognizer
// recognized. UIKit recognizes a long press exactly `minimumPressDuration`
// after touch-down, so the caller subtracts its own threshold; expressing the
// rule against total hold time is what makes the truth table readable.
//
// That subtraction can underflow, and it FAILS CLOSED on purpose. If the tick
// clock is younger than the caller's threshold -- a hold begun in the first
// 750 ms of the process -- `downMs` wraps to a huge number, and both readers
// below guard with `>=` and answer 0 ms, so the hold fires nothing rather than
// reporting a bogus 49-day press and toggling zen. Flagged twice in review,
// once by the author and once adversarially; recorded here so it is not
// re-derived a third time.
class Hold {
 public:
  void begin(uint32_t downMs) {
    active_ = true;
    poisoned_ = false;
    toggled_ = false;
    downMs_ = downMs;
  }

  // More than one finger took part -> poison. Called with the recognizer's
  // live touch count; anything but exactly one kills the hold.
  void noteTouches(int touches) {
    if (touches != 1) poisoned_ = true;
  }

  // iOS took the touch (.cancelled / .failed).
  void cancel() { poisoned_ = true; }

  bool active() const { return active_; }
  bool poisoned() const { return poisoned_; }
  bool toggled() const { return toggled_; }

  // The 5 s deadline arrived under the finger. Latches, so the lift is silent.
  Action deadline() {
    const Action a = onToggleDeadline(poisoned_, toggled_);
    if (a == Action::Toggle) toggled_ = true;
    return a;
  }

  // The finger came up. Ends the hold either way, and leaves the tracker
  // CLEAN: an idle Hold must never carry a previous hold's poison, because the
  // toggle deadline is asked on holds this tracker never saw begin (out of
  // zen the select recognizer is disabled, so nothing calls begin() at all)
  // and a stale poison there would silently kill the toggle in one mode only.
  Action release(uint32_t upMs) {
    const uint32_t held = upMs >= downMs_ ? upMs - downMs_ : 0u;
    const Action a = active_ ? onRelease(held, poisoned_, toggled_) : Action::None;
    active_ = false;
    poisoned_ = false;
    toggled_ = false;
    return a;
  }

  // How long the finger has been down, for the log line.
  uint32_t heldMs(uint32_t nowMs) const {
    return nowMs >= downMs_ ? nowMs - downMs_ : 0u;
  }

 private:
  bool active_ = false;
  bool poisoned_ = false;
  bool toggled_ = false;
  uint32_t downMs_ = 0;
};

}  // namespace zenhold
