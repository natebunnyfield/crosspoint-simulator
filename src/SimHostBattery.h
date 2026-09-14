#pragma once

// The HOST's battery, published to the firmware's battery display.
//
// On device the gauge is an I2C part read by BatteryMonitor and the charging
// bolt is a GPIO (`HalGPIO::isUsbConnected`). In this library both were
// env-var stubs latched into a `static` on first call -- 100 % and
// always-charging unless CROSSPOINT_SIM_BATTERY / CROSSPOINT_SIM_USB said
// otherwise (S-001). That is right for a headless capture, where a fixed
// battery is what makes a screenshot reproducible, and wrong on a phone, where
// the header sits beside iOS's own status bar showing a different number.
//
// So: the host may PUBLISH a reading, and the two HAL stubs prefer it when one
// exists. Nothing else changes -- a build that never publishes behaves exactly
// as before, which is every desktop run and every test.
//
// WHY A PUBLISH RATHER THAN A READ. `getBatteryPercentage()` is called from
// the firmware's render task, and UIKit's `UIDevice` is main-thread-only. The
// iOS backend therefore observes the two battery notifications on the main
// thread and pushes the result in here; the render task only ever reads an
// atomic. Same shape, and the same reason, as SimulatorOverlay's panel state.
//
// WHY NOT A FIELD ON THE FIRMWARE'S HAL. The device HAL has no notion of a
// host battery and never will. This is a free-function hook for the same
// reason SimHostSettings.h and SimWiFiHost.h are: it is a property of THIS
// HOST running the app, not of the simulated device, and on real hardware
// there is nothing to read.
//
// THE THREE-STATE ANSWER MATTERS. `percent()` returns -1 for "no host reading",
// not 0 -- 0 % is a real and alarming battery level, and an iOS Simulator
// (as opposed to a phone) reports exactly that for `batteryLevel` when
// monitoring is off. Conflating the two would have every simulator run render
// a flat empty battery and trip the firmware's low-battery paths. Same for
// `charging()`.

#include <atomic>
#include <cstdlib>

namespace sim_host_battery {

// The desktop escape hatches, named once so a doc or a test can cite them.
// Deliberately NOT consulted when a host reading exists: a phone has no
// environment to set, and a build that read both would have two answers to one
// question.
inline constexpr char kPercentEnvVar[] = "CROSSPOINT_SIM_BATTERY";
inline constexpr char kUsbEnvVar[] = "CROSSPOINT_SIM_USB";

namespace detail {
// -1 = nothing published. Written by the host's main thread, read by the
// firmware's render task; relaxed is enough because the two are independent
// scalars and no invariant spans them -- a frame that pairs a new percentage
// with the old charging flag renders a battery that was true a moment ago,
// which is what any polled gauge shows anyway.
inline std::atomic<int> gPercent{-1};
inline std::atomic<int> gCharging{-1};
// Set once per plug/unplug edge, cleared by the reader. `wasUsbStateChanged()`
// is what makes main.cpp request a repaint, so without this the bolt would
// appear only at the next page turn.
inline std::atomic<bool> gUsbEdge{false};
}  // namespace detail

// Publish a reading from the host. `percent` outside 0-100 and `charging` < 0
// both mean "unknown" and clear that half of the reading.
//
// Safe to call from any thread, but in practice the main one: the iOS backend
// is driven by UIKit notifications.
inline void publish(int percent, int charging) {
  detail::gPercent.store(percent < 0 || percent > 100 ? -1 : percent,
                         std::memory_order_relaxed);
  const int before = detail::gCharging.exchange(charging < 0 ? -1 : (charging ? 1 : 0),
                                                std::memory_order_relaxed);
  const int after = detail::gCharging.load(std::memory_order_relaxed);
  // An edge only when both readings are real: -1 -> 1 at launch is the first
  // reading arriving, not a cable being plugged in, and raising it there would
  // queue a repaint on every cold start.
  if (before >= 0 && after >= 0 && before != after)
    detail::gUsbEdge.store(true, std::memory_order_relaxed);
}

// The host's battery level, 0-100, or -1 when the host has not published one.
inline int percent() { return detail::gPercent.load(std::memory_order_relaxed); }

// 1 charging, 0 on battery, -1 unknown.
inline int charging() { return detail::gCharging.load(std::memory_order_relaxed); }

// True once per plug/unplug edge since the last call. Consuming rather than
// peeking, because main.cpp's contract is "true once per edge" and a peek
// would repaint on every loop iteration for as long as the cable stayed in.
inline bool consumeUsbEdge() {
  return detail::gUsbEdge.exchange(false, std::memory_order_relaxed);
}

// ---------------------------------------------------------------- resolution
//
// The two functions the HAL stubs actually call. Both keep the historical
// behavior exactly when no host reading exists, which is what lets every
// existing headless capture stay byte-identical.

// Battery percentage for the firmware's display: the host's reading when there
// is one, else CROSSPOINT_SIM_BATTERY, else 100.
//
// The env var is read EVERY call rather than latched into a static. The latch
// was invisible on the desktop (the variable cannot change mid-run) and wrong
// on a phone, where it would freeze whatever level happened to be current when
// the header first drew.
inline int resolvedPercent() {
  const int host = percent();
  if (host >= 0) return host;
  const char *v = std::getenv(kPercentEnvVar);
  if (!v) return 100;
  const long n = std::strtol(v, nullptr, 10);
  return static_cast<int>(n < 0 ? 0 : (n > 100 ? 100 : n));
}

// Is the charger connected: the host's reading when there is one, else
// CROSSPOINT_SIM_USB=0 for unplugged, else true.
inline bool resolvedUsbConnected() {
  const int host = charging();
  if (host >= 0) return host != 0;
  const char *v = std::getenv(kUsbEnvVar);
  return !(v && v[0] == '0' && v[1] == '\0');
}

}  // namespace sim_host_battery
