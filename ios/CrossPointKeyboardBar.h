#pragma once

// A dismiss bar riding on top of the software keyboard.
//
// WHY IT EXISTS
//
// The firmware raises the keyboard by opening a text field, and until now
// nothing could lower it. On iPad that is survivable -- the system keyboard
// carries its own dismiss key in the bottom-right. On iPhone it does not, so a
// field open meant roughly 40% of the screen gone, the panel squeezed into what
// was left, and no way to see the page or reach the firmware's own on-screen
// grid without leaving the screen entirely.
//
// WHAT IT ATTACHES TO
//
// UIKit presents an `inputAccessoryView` alongside whatever is first responder,
// and on iOS that responder is SDL's: a hidden SDLUITextField the UIKit backend
// adds as a subview of the root view controller's view
// (SDL_uikitviewcontroller.m:274, :350). SDL exposes no accessor for it and no
// accessory API of its own -- `grep -rn inputAccessoryView` across all of SDL
// 3.4.12 returns nothing -- so we find it by ordinary public traversal from the
// UIWindow SDL does publish. No private headers, no ivar reads, no swizzling;
// the search is over public UIKit properties and would keep compiling against
// any SDL.
//
// It is unambiguous which field: SDL adds exactly one, and this harness's own
// views (CPPageTextInputView) are UIView, not UITextField.
//
// Only HIDING lives here. The bar rides on the keyboard, so it leaves with it
// and cannot be the way back up -- that is the panel tap and the "Tap to type"
// chip in CrossPointIOSShim.cpp.

#ifdef __cplusplus
extern "C" {
#endif

// Attach the bar, if it is not attached already. Idempotent, and safe to call
// from any thread -- it hops to the main queue itself, because everything it
// touches is UIKit.
//
// Call it when the keyboard appears (SDL_EVENT_SCREEN_KEYBOARD_SHOWN): SDL
// raises that from inside -startTextInput BEFORE becomeFirstResponder
// (SDL_uikitviewcontroller.m:503), which is the cheapest moment to attach.
void CrossPointKeyboardBar_install(void);

#ifdef __cplusplus
}
#endif
