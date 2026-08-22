#pragma once
#include <algorithm>
#include <cassert>
#include <cerrno>
#include <chrono>
#include <cmath>
#include <cstdarg>
#include <cstdint>
#include <cstdlib>
#include <string>
#include <thread>

#define PROGMEM
#define ICACHE_RODATA_ATTR
#define IRAM_ATTR
#define DRAM_ATTR
#define RTC_NOINIT_ATTR
#define PGM_P const char *
#define PSTR(s) (s)

// The epoch lives in SimulatorClock.h, NOT in a function-local static here: a
// function-local start survives the iOS in-process (longjmp) reboot, so
// millis() kept counting across a wake while hardware zeroes it at reset.
// SimulatorLifecycle re-bases the epoch at that boundary; on desktop the
// reboot is execvp and the registrar never runs, so nothing changes there.
#include "SimulatorClock.h"

inline unsigned long millis() { return simclock::millisSinceEpoch(); }

inline unsigned long micros() { return simclock::microsSinceEpoch(); }

inline void delay(unsigned long ms) {
  std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}
inline void yield() { std::this_thread::yield(); }

// Native builds have no GPIO pins. Treat every input as released, matching the
// idle pull-up state used by the button diagnostics in firmware startup.
inline int digitalRead(int /*pin*/) { return 1; }

#include "HardwareSerial.h"
#include "Print.h"
#include "SimulatorHeap.h"
#include "SimulatorLifecycle.h"
#include "WString.h"

struct ESPMock {
  // Flat 1 MB unless CROSSPOINT_SIM_HEAP / CROSSPOINT_SIM_HEAP_FREE is set --
  // see SimulatorHeap.h for why a flat figure made every low-memory branch in
  // the firmware unreachable, and why this is opt-in.
  uint32_t getFreeHeap() { return simheap::freeBytes(); }
  // Was a no-op, which meant the firmware's silentRestart() -- how every file
  // transfer and font download ends, to defragment the heap -- painted its
  // "Loading..." popup and then simply fell through. On hardware this call
  // never returns, so the reboot-to-Home that follows a transfer was never
  // exercised in the simulator at all. See SimulatorLifecycle.h for why this is
  // a restart rather than a wake, and which platforms honor it.
  void restart() { SimulatorLifecycle::rebootAsFirmwareRestart(); }
  uint32_t getHeapSize() { return simheap::totalBytes(); }
  uint32_t getMinFreeHeap() { return simheap::minFreeBytes(); }
  uint32_t getMaxAllocHeap() { return simheap::maxAllocBytes(); }
};
extern ESPMock ESP;

inline long random(long max) { return std::rand() % max; }

template <typename A, typename B>
constexpr auto max(A a, B b) -> decltype(a > b ? a : b) {
  return a > b ? a : b;
}
template <typename A, typename B>
constexpr auto min(A a, B b) -> decltype(a < b ? a : b) {
  return a < b ? a : b;
}
