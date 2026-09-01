#pragma once

#include <atomic>

// The action-menu channel: a host gesture (a bindable action in
// ios/GestureBindings.h -- Action::OpenActionMenu, offered with no default
// binding -- or OPENMENU in CROSSPOINT_SIM_INPUT_SCRIPT) on its way to
// FileManagerActivity::openActionMenu(). Owned by HalGPIO; kept as a free
// header with no SDL or HAL state so a plain host test can assert the
// contract, same reasoning as FontFamilyStepChannel.h beside it.
//
// This exists because the per-item action menu in Manage Files was reachable
// only by held Confirm (~1000 ms) -- a device HAS a keyboard-style button for
// it. A touchscreen host does not, and holding is being phased out as a
// trigger where it can be (docs/hold-gestures.md); this channel is the touch
// route in, alongside the button route that stays.
//
// SAME CONSUME DISCIPLINE AS FontFamilyStepChannel: exactly one consume per
// inject, and a burst of injects between polls collapses to ONE open -- the
// menu is idempotent to open twice in a row (the second call is a no-op
// while the popup is already active), but a queue here would still be the
// wrong model for what is fundamentally a single request, not a counted one.
//
// NO DIRECTION, unlike FontFamilyStepChannel: opening the menu is a single
// action with nothing to steer, so this is the plain boolean pulse
// FontFamilyStepChannel was before 2026-08-29 added direction() to it.
//
// NOT DRAINED HERE ON ITS OWN: the channel has no notion of which activity is
// current, so it cannot decide for itself whether a pending open is stale.
// FileManagerActivity::onEnter() drains it (consumes and discards) before
// polling for real, so a gesture fired minutes earlier on a different screen
// (Home, Settings, a book) cannot surface the menu the instant the owner
// happens to open Manage Files -- see the comment at that call site for why
// that direction was chosen over, say, a global per-activity-switch drain.
class OpenActionMenuChannel {
 public:
  // Host side (simulator-only, like injectButton*). A burst between polls
  // still resolves to one open.
  void inject() { pending_.store(true); }

  // Firmware side: true once per inject.
  bool consume() { return pending_.exchange(false); }

  // The in-process (iOS) reboot boundary: a request injected in the run
  // being abandoned must not land on the next boot's Manage Files.
  void resetForReboot() { pending_.store(false); }

 private:
  std::atomic<bool> pending_{false};
};
