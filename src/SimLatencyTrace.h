#pragma once

// CROSSPOINT_SIM_LOG_LATENCY=1: one `[lat]` line per input edge and per panel
// call, stamped in microseconds on the firmware's own clock (micros()), with
// the storage traffic since the previous line. Off by default and LATCHED, so
// an unarmed run pays one branch per hook.
//
// What it is for: the time from a press to the first panel call is the part of
// a page turn or a menu move the FIRMWARE owns; the panel's waveform after that
// (~500 ms FAST, ~1650 ms HALF/FULL, measured on the X4) is the part it does
// not. The host cannot price SD I/O, so the counts travel with each line --
// call counts are what transfer to the device, wall time on the host does not.

#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstdlib>

#include "Arduino.h"

namespace simlat {

inline bool enabled() {
  static const bool on = [] {
    const char *e = std::getenv("CROSSPOINT_SIM_LOG_LATENCY");
    return e && *e && *e != '0';
  }();
  return on;
}

struct Counters {
  std::atomic<uint32_t> opens{0}, reads{0}, seeks{0}, writes{0};
  std::atomic<uint64_t> readBytes{0};
};
inline Counters &counters() {
  static Counters c;
  return c;
}

inline void countOpen() { if (enabled()) counters().opens++; }
inline void countRead(long n) {
  if (!enabled()) return;
  counters().reads++;
  if (n > 0) counters().readBytes += static_cast<uint64_t>(n);
}
inline void countSeek() { if (enabled()) counters().seeks++; }
inline void countWrite() { if (enabled()) counters().writes++; }

// Prints and resets the storage counters, so each line carries the traffic
// that happened between it and the line before.
inline void note(const char *what, int arg = -1) {
  if (!enabled()) return;
  Counters &c = counters();
  std::fprintf(stdout,
               "[lat] %llu %s %d opens=%u reads=%u rbytes=%llu seeks=%u "
               "writes=%u\n",
               static_cast<unsigned long long>(micros()), what, arg,
               c.opens.exchange(0), c.reads.exchange(0),
               static_cast<unsigned long long>(c.readBytes.exchange(0)),
               c.seeks.exchange(0), c.writes.exchange(0));
  std::fflush(stdout);
}

// FNV-1a over the frame about to be shown, so two refreshes of an identical
// frame -- a whole waveform that changes nothing on the glass -- are visible.
inline uint32_t frameHash(const uint8_t *fb, size_t n) {
  uint32_t h = 2166136261u;
  for (size_t i = 0; i < n; ++i) h = (h ^ fb[i]) * 16777619u;
  return h;
}

}  // namespace simlat
