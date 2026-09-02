#pragma once

// Whether the shake catcher may take FIRST RESPONDER right now.
//
// Motion events reach the first responder only, so CPXShakeCatcher
// (CrossPointZenRecognizers.mm) re-asserts the status on every
// CrossPointZenRecognizers_setEnabled call -- and one of those calls is the
// zen toggle itself. One first responder per window: while the software
// keyboard is up, SDL's hidden UITextField holds the status and the keyboard
// is up BECAUSE it does (CrossPointKeyboardBar.mm). So every zen toggle
// dropped the keyboard -- the 0.75 s hold above the paper fires outside zen,
// mid-password, and once in zen nothing can raise the keyboard again
// (docs/ux-navigation-audit-2026-09-02.md, finding 2 -- P1).
//
// The rule: a field open AND the keyboard up is the one state in which the
// text field's claim outranks the shake's. Every other state (no field, or a
// field whose keyboard the reader put away with the chip) the shake claims as
// before, so a shake during typing is still dropped -- the stated ceiling in
// the recognizer file -- but a zen toggle no longer costs the keyboard. The
// shake claims again when the keyboard goes down
// (SDL_EVENT_SCREEN_KEYBOARD_HIDDEN in CrossPointIOSShim.cpp), which is the
// recovery the previous re-assert-on-every-call gave and this keeps.
//
// Pure for the reason every header beside it is: the wrong answer is silent
// on a device (a keyboard that vanished, or a shake that never lands) and
// UIKit's responder chain cannot be driven from a host.
namespace shakeresp {

constexpr bool shouldClaim(const bool textEntryActive, const bool hostKeyboardVisible) {
  return !(textEntryActive && hostKeyboardVisible);
}

}  // namespace shakeresp
