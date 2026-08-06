#pragma once

// Host screen-sleep control, for the one case where the firmware's idea of
// "idle" and the phone's disagree.
//
// A file transfer is minutes of the firmware doing nothing visible while a peer
// pushes books over the network. To iOS that is an idle app, so the screen locks
// and the app is suspended -- which stops the listening socket accepting and
// kills the transfer partway through. During QA that reads as a firmware bug in
// the web server, which is exactly the wrong conclusion to hand someone.
//
// A free hook rather than a HalDisplay method, for the same reason as
// SimulatorOverlay.h: real hardware has no analog, so it must not appear on a
// surface that mirrors the firmware's HAL. Everywhere but iOS it compiles to
// nothing.

#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif

#ifndef CROSSPOINT_SIM_HOST_SCREEN
#if defined(__APPLE__) && TARGET_OS_IPHONE
#define CROSSPOINT_SIM_HOST_SCREEN 1
#else
#define CROSSPOINT_SIM_HOST_SCREEN 0
#endif
#endif

namespace sim_host_screen {

#if CROSSPOINT_SIM_HOST_SCREEN
// Safe to call from any thread; the platform hop to the main thread, which
// UIKit requires, happens inside. Reference-free: the last call wins, so a
// server that fails to start must still pass false on its way out.
void setKeepAwake(bool keepAwake);
#else
inline void setKeepAwake(bool) {}
#endif

}  // namespace sim_host_screen
