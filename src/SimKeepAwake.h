#pragma once

// KEEP AWAKE for the length of an Update Fonts / Update Library run, and only
// then (owner ruling 2026-09-26, S-042, "Fix both").
//
// The run is minutes with nobody touching the phone. With "Allow Device to
// Sleep on Battery" on (it ships on) iOS auto-locks the screen, the app is
// suspended and the run stops -- which, from across the room, is a frozen
// screen. So while a run is WORKING (checking or syncing) the host holds
// UIApplication.idleTimerDisabled, and gives the owner's own value back the
// moment it is not.
//
// The firmware says only what it WANTS (request(), any thread, an atomic); the
// host's main loop applies it (apply(), main thread, which UIKit requires) and
// is the only writer of the idle timer here. That split is what makes every
// exit path the same path: done, failed, stopped, Back, sleep, the activity
// destroyed, a reboot -- each of them just stops wanting, and the next main
// loop pass restores. Backgrounding counts as not wanting (the flag means
// nothing to a suspended app) and a return to the foreground mid-run takes the
// lease again.
//
// Lease is PURE so tests/keep_awake_test.cpp can drive every edge without
// UIKit. Header-only for the same reason as SimUpdateTrace.h.

#include <atomic>

#include "SimHostScreen.h"
#include "SimUpdateTrace.h"

namespace sim_keep_awake {

enum class Action { None, Set, Reassert, Restore };

// Raised on every Restore: the host's own screen-awake preference re-applies
// itself on the next pass (simulator_main applyKeepScreenAwake), so a
// preference that CHANGED during the run -- a phone plugged in or unplugged --
// wins over the value snapshotted minutes ago. That function only writes on a
// change, so without this the restore would stand until the next cable event.
inline std::atomic<bool> g_reapplyPreference{false};
struct Lease {
  bool held = false;
  bool previous = false;  // the idle timer's value before the lease

  // One main-loop pass. `current` is the idle timer's value right now.
  // Returns what the host must do; on Restore, `previous` is the value.
  Action step(bool wanted, bool foreground, bool current) {
    const bool effective = wanted && foreground;
    if (effective && !held) {
      held = true;
      previous = current;
      return Action::Set;
    }
    if (!effective && held) {
      held = false;
      g_reapplyPreference.store(true);
      return Action::Restore;
    }
    // Held, and someone else turned the timer back on -- the owner's
    // charging-dependent preference (applyKeepScreenAwake) flips it when the
    // cable comes out. Mid-run that would let the phone lock, which is the
    // whole thing the lease exists to prevent. (Adversarial review 2026-09-26.)
    if (held && !current) return Action::Reassert;
    return Action::None;
  }
};

// What the firmware wants. Written by the update activities (loop thread),
// cleared by a reboot reset in the host.
inline std::atomic<bool> g_wanted{false};
// The host's foreground state, kept by HalDisplay::setBackgrounded.
inline std::atomic<bool> g_foreground{true};

inline void request(bool wanted) { g_wanted.store(wanted, std::memory_order_relaxed); }
inline void setForeground(bool foreground) {
  g_foreground.store(foreground, std::memory_order_relaxed);
}

// One pass of the host side. MAIN THREAD ONLY (UIKit's idle timer). Called
// from the main loop every iteration AND from the deep-sleep loop
// (HalGPIO::startDeepSleep): a power-off mid-run leaves the main loop for
// that one, and before it was called there the lease was never released --
// found on the iOS Simulator, 2026-09-26, a sleeping app holding the phone
// awake.
inline void applyOnMainThread() {
#if !CROSSPOINT_SIM_HOST_SCREEN
  // No host idle timer to hold (the desktop): its stub always reads "enabled",
  // which would read as a reassert on every pass.
  return;
#endif
  static Lease lease;
  const bool current = sim_host_screen::idleTimerDisabled();
  switch (lease.step(g_wanted.load(), g_foreground.load(), current)) {
    case Action::Set:
      sim_host_screen::setIdleTimerDisabledNow(true);
      sim_update_trace::logf("keep-awake SET for the update run (idle timer was %s)",
                             current ? "already disabled" : "enabled");
      break;
    case Action::Reassert:
      sim_host_screen::setIdleTimerDisabledNow(true);
      sim_update_trace::logf("keep-awake REASSERTED: the idle timer was re-enabled mid-run");
      break;
    case Action::Restore:
      sim_host_screen::setIdleTimerDisabledNow(lease.previous);
      sim_update_trace::logf("keep-awake RESTORED: idle timer %s (was %s during the run)",
                             lease.previous ? "disabled" : "enabled", current ? "disabled" : "enabled");
      break;
    case Action::None:
      break;
  }
}

}  // namespace sim_keep_awake
