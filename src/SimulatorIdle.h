#pragma once
// THE MAIN THREAD'S SLEEPS PUMP PRESENTS (2026-10-03).
//
// The firmware's loop() sleeps between input polls -- delayWallClock(10) at
// 100 Hz, and HalPowerManager::lightSleep's delay(50) once idle -- and in
// the simulator those sleeps are on the MAIN THREAD, the only thread SDL may
// present from. So nothing could reach the glass while the firmware slept:
// the present loop in simulator_main runs once per loop() pass, and a pass
// is 50 ms of sleep plus the compose. Measured on the desktop X3 (the
// [timing] line's `pass`): 77 ms between passes with a 20 ms compose, which
// capped every self-driving animation -- the phosphor trail, the beam, the
// zen goal's breath -- at ~13 fps whatever its own cadence asked for. The
// owner (2026-10-03): "all effects need to be at 60fps".
//
// delay() therefore pumps while it waits, when it is called on the main
// thread: the installed pump (simulator_main installs presentIfNeeded) runs
// about once a millisecond until the deadline, so a present owed during a
// sleep lands within a millisecond of being owed. On any other thread -- the
// firmware's render task delays too -- it is the plain sleep it always was,
// because that thread may not touch SDL. Nested calls (a pump that itself
// delays) fall through to the plain sleep rather than recurse.
//
// The firmware's own semantics are untouched: delay(ms) still returns no
// sooner than ms later, and millis() runs on the same steady clock. What
// changed is only what the main thread does with the time.
//
// HEADER-ONLY for the usual reason: cmake/CrossPointSources.cmake is
// generated and a new .cpp here goes stale in it. Pure enough to host-test:
// tests/simulator_idle_test.cpp drives it with a counting pump.
#include <atomic>
#include <chrono>
#include <thread>

namespace simidle {

using Pump = void (*)();

inline std::atomic<Pump> &pumpSlot() {
  static std::atomic<Pump> p{nullptr};
  return p;
}
inline std::thread::id &mainThread() {
  static std::thread::id id;
  return id;
}
inline bool &nested() {
  thread_local bool n = false;
  return n;
}

// Call from the thread that owns SDL, once the display exists. Idempotent;
// the iOS longjmp reboot reaches it again and simply re-records the thread.
inline void install(Pump pump) {
  mainThread() = std::this_thread::get_id();
  pumpSlot().store(pump, std::memory_order_release);
}
inline void uninstall() { pumpSlot().store(nullptr, std::memory_order_release); }

inline void plainSleep(unsigned long ms) {
  std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}

// How many times the pump ran during the last pumped sleep on this thread --
// for the test, and for anyone instrumenting the loop.
inline unsigned long &lastPumpCount() {
  thread_local unsigned long n = 0;
  return n;
}

inline void sleepMs(unsigned long ms) {
  const Pump pump = pumpSlot().load(std::memory_order_acquire);
  if (!pump || nested() || std::this_thread::get_id() != mainThread()) {
    plainSleep(ms);
    return;
  }
  using clock = std::chrono::steady_clock;
  const auto deadline = clock::now() + std::chrono::milliseconds(ms);
  unsigned long pumped = 0;
  nested() = true;
  for (;;) {
    pump();
    ++pumped;
    const auto now = clock::now();
    if (now >= deadline) break;
    const auto left = deadline - now;
    std::this_thread::sleep_for(left < std::chrono::milliseconds(1)
                                    ? left
                                    : std::chrono::duration_cast<clock::duration>(
                                          std::chrono::milliseconds(1)));
  }
  nested() = false;
  lastPumpCount() = pumped;
}

}  // namespace simidle
