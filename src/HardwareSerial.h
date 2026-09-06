#pragma once
#include <cstdio>
#include <cstring>
#include <iostream>

#include "Arduino.h"
#include "FirmwareLogFile.h"
#include "Print.h"
#include "Stream.h"
#include "WString.h"

// Every write goes to stderr AND to firmwarelog, which is a no-op until the
// host arms it. stderr is the desktop's log and is discarded by a TestFlight
// build; firmwarelog is the phone's, and is the only way a LOG_DBG line ever
// reaches the owner. See FirmwareLogFile.h.
class HWCDC : public Stream {
public:
  void begin(unsigned long baud) {}
  void setTxTimeoutMs(uint32_t timeoutMs) {}
  size_t write(uint8_t c) override {
    std::cerr << (char)c;
    firmwarelog::write((const char *)&c, 1);
    return 1;
  }
  size_t write(const uint8_t *buffer, size_t size) override {
    std::cerr.write((const char *)buffer, size);
    firmwarelog::write((const char *)buffer, size);
    return size;
  }
  int available() override { return 0; }
  int read() override { return -1; }
  int peek() override { return -1; }
  template <typename... Args> void printf(const char *format, Args... args) {
    // Not routed through write(): logPrintf builds a whole line and calls
    // print(), so this overload only carries the codebase's few direct
    // logSerial.printf() calls. They belong in the file too.
    if constexpr (sizeof...(Args) == 0) {
      std::cerr << format;
      firmwarelog::write(format, strlen(format));
    } else {
      char buf[256];
      const int n = snprintf(buf, sizeof(buf), format, args...);
      std::cerr << buf;
      if (n > 0) {
        firmwarelog::write(buf, (size_t)n < sizeof(buf) - 1 ? (size_t)n : sizeof(buf) - 1);
      }
    }
  }
  operator bool() const { return true; }
};

// CrossPoint uses HardwareSerial when ARDUINO_USB_CDC_ON_BOOT is not defined.
// The simulator has a single stderr-backed serial endpoint, so both Arduino
// serial types intentionally resolve to the same host implementation.
using HardwareSerial = HWCDC;

extern HWCDC Serial;
