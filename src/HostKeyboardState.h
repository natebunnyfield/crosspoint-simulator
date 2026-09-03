#pragma once

#include <atomic>

// Whether the host's software keyboard should be up right now -- and, when it
// should be up but already is, whether the platform has to be kicked.
//
// A field opening does NOT raise the keyboard by itself (owner ruling
// 2026-08-12): it only makes the "Tap to type" chip appear. The keyboard
// comes up on an explicit requestVisible(true), i.e. the chip getting tapped.
// This used to be inverted -- every field opened with the keyboard already up
// -- which on iPhone (see HalGPIO.h's comment on setHostKeyboardVisible) meant
// the keyboard covering ~40% of the screen the instant any field appeared,
// with no chance to see the page or the firmware's own grid keyboard first.
//
// WHY THIS IS ITS OWN HEADER
//
// The keyboard is raised by pumpHostTextInput() comparing the firmware's
// text-entry flag against what it last did. Adding a second input (the owner
// asking it up or down) means three booleans interacting on a path that has
// no visible output on desktop and cannot be single-stepped on a phone. Every
// bug this file exists to prevent is a state bug, not a UIKit bug:
//
//   - lowering the keyboard behind pumpHostTextInput()'s back leaves its
//     `applied` flag saying "up", so nothing ever raises it again;
//   - a manual show or hide that outlives the field it was requested in is an
//     invisible preference with no UI -- a keyboard that mysteriously stays up
//     (or stays down) across an unrelated later field, with nothing on screen
//     saying why;
//   - a raise issued while the platform believes text input is already active
//     is a no-op, so the tap does nothing.
//
// No SDL and no UIKit, so tests/host_keyboard_test.cpp drives the real object
// on a host in microseconds -- not a mirror of it that can drift.

namespace hostkbd {

enum class Action {
  None,     // the platform already matches what we want
  Start,    // raise it: SDL_StartTextInput
  Stop,     // lower it: SDL_StopTextInput
  Restart,  // lower then raise, to force becomeFirstResponder to run again
};

// The keyboard belongs up only while the firmware has a field open. Suppression
// is the owner's override on top of that -- it can hide a keyboard the firmware
// wants, never summon one it does not.
constexpr bool wantsKeyboard(const bool fieldOpen, const bool suppressed) {
  return fieldOpen && !suppressed;
}

// `applied` is what the caller last told the platform. `forceRestart` is armed
// by an explicit raise request and answers the case the other two cannot see:
// the platform lowered the keyboard on its own (iPad's dismiss key, a hardware
// keyboard connecting) without our noticing, so `applied` and `want` agree at
// "up" while the screen shows no keyboard at all. Only a stop-then-start makes
// the field first responder again.
//
// Note the order: a raise from nothing is Start, not Restart. Stopping text
// input that was never started is harmless, but it would log a spurious pair of
// transitions on every field open.
constexpr Action decide(const bool applied, const bool want,
                        const bool forceRestart) {
  if (want && !applied)
    return Action::Start;
  if (want && forceRestart)
    return Action::Restart;
  if (!want && applied)
    return Action::Stop;
  return Action::None;
}

// Whether the keyboard chip -- the one control that raises the keyboard -- is
// on the glass and hit-testable. ONE INPUT, on purpose: the chip lives while
// a firmware text field is open, and nothing else gates it. Zen is
// deliberately NOT a parameter, because zen hides the whole pad and for a
// while hid this chip with it (audit finding 5, 2026-09-02): every field opens
// suppressed, the chip is the only way up, so a field opened in zen could
// only be pecked out of the daisywheel. Owner ruling 2026-09-02: paint and
// hit-test the chip in zen. A future caller that wants to gate it on zen has
// to add the parameter here, where the test will see it.
constexpr bool chipLive(const bool fieldOpen) { return fieldOpen; }

// The live state. Atomic because the three inputs arrive on three threads: the
// firmware task opens and closes fields, a UIKit callback asks to show or hide,
// and only poll() runs on the main thread.
class State {
public:
  // Both edges of the firmware's text-entry flag reset to the default: hidden.
  // A field always opens with the keyboard down and the chip showing -- a
  // manual show from one field must not leak into the next one, the same way
  // a manual hide must not (that direction is the one this file used to get
  // wrong: a dismiss used to stick for the rest of the session; now nothing
  // sticks in either direction, because every edge re-arms the same default).
  void onFieldEdge() { suppressed_.store(true); }

  void requestVisible(const bool visible) {
    // A raise ALWAYS arms the restart, even when suppression does not change.
    // If the platform lowered the keyboard without telling us, suppressed_ is
    // already false, decide() sees nothing to do, and the tap asking for the
    // keyboard back does nothing at all.
    if (visible)
      forceRestart_.store(true);
    suppressed_.store(!visible);
  }

  bool suppressed() const { return suppressed_.load(); }

  bool wants(const bool fieldOpen) const {
    return wantsKeyboard(fieldOpen, suppressed_.load());
  }

  // MAIN THREAD ONLY. Consumes the armed restart, so call it only when able to
  // act on the answer -- a poll() dropped because there is no window yet would
  // swallow a raise request made during startup.
  Action poll(const bool fieldOpen) {
    const bool want = wants(fieldOpen);
    const Action action = decide(applied_, want, forceRestart_.exchange(false));
    if (action != Action::None)
      applied_ = want;
    return action;
  }

private:
  std::atomic<bool> suppressed_{true};
  std::atomic<bool> forceRestart_{false};
  bool applied_ = false; // main thread only, guarded by poll()'s contract
};

} // namespace hostkbd
