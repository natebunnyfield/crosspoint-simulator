#pragma once
#include <cassert>
#include <chrono>
#include <cmath>
#include <cstdarg>
#include <cstdint>
#include <string>
#include <thread>

#define PROGMEM
#define ICACHE_RODATA_ATTR
#define IRAM_ATTR
#define DRAM_ATTR
#define RTC_NOINIT_ATTR
#define PGM_P const char *
#define PSTR(s) (s)

inline unsigned long millis() {
  using namespace std::chrono;
  static const auto start = steady_clock::now();
  return duration_cast<milliseconds>(steady_clock::now() - start).count();
}

inline unsigned long micros() {
  using namespace std::chrono;
  static const auto start = steady_clock::now();
  return duration_cast<microseconds>(steady_clock::now() - start).count();
}

inline void delay(unsigned long ms) {
  std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}
inline void yield() { std::this_thread::yield(); }

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
  // a restart rather than a wake, and which platforms honour it.
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
