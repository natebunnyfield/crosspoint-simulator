#pragma once

#include <cstdint>
#include <string>

namespace HalSystem {
struct StackFrame {
  uint32_t sp;
  uint32_t spp[8];
};

void begin();
void restart();

// Dump panic info to SD card if necessary
void checkPanic();
void clearPanic();
// Firmware stores a heap sample in RTC memory for the next panic report; the
// simulator has no RTC and its panic path reads nothing back, so a no-op.
void recordHeapSample();

std::string getPanicInfo(bool full = false);
bool isRebootFromPanic();
} // namespace HalSystem
