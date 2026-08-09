// PLACEHOLDER, AHEAD OF THE FIRMWARE -- do not delete as unused.
//
// Nothing in the firmware calls this: lib/hal/ has exactly six HAL classes
// (Clock, Display, GPIO, PowerManager, Storage, System) and this is not one of
// them. It is here because the hardware is real -- the tilt sensor is device hardware,
// and the SDK carries its own support -- so the day
// the firmware grows a brightness control this is the file it links against.
//
// Ruled KEEP (ST-002 in TODO.md). Zero references is not grounds for deletion
// in this project; deleting it means rebuilding it later, blind, by someone who
// does not know it existed.

#pragma once

#include <Arduino.h>

#include "HalGPIO.h"

namespace CrossPointOrientation {
enum Value : uint8_t {
  PORTRAIT = 0,
  LANDSCAPE_CW = 1,
  INVERTED = 2,
  LANDSCAPE_CCW = 3
};
}

namespace CrossPointTiltPageTurn {
enum Value : uint8_t { TILT_OFF = 0, TILT_NORMAL = 1, TILT_INVERTED = 2 };
}

class HalTiltSensor;
extern HalTiltSensor halTiltSensor;

class HalTiltSensor {
private:
  bool _available = false;
  bool _isAwake = false;

public:
  void begin() {
#if defined(SIMULATOR_DEVICE_X3)
    _available = true;
#else
    _available = false;
#endif
    _isAwake = false;
  }

  bool wake() {
    if (!_available)
      return false;
    _isAwake = true;
    return true;
  }

  bool deepSleep() {
    if (!_available)
      return false;
    _isAwake = false;
    return true;
  }

  bool isAvailable() const { return _available; }
  // Support both firmware HAL shapes while the repos are out of sync.
  // Current firmware is portrait-only and passes no orientation.
  void update(const uint8_t /*mode*/, const bool /*inReader*/) {}
  void update(const uint8_t /*mode*/, const uint8_t /*orientation*/, const bool /*inReader*/) {}
  void update(const uint8_t mode, const uint8_t /*direction*/, const uint8_t orientation, const bool inReader) {
    update(mode, orientation, inReader);
  }
  bool wasTiltedForward() { return false; }
  bool wasTiltedBack() { return false; }
  bool hadActivity() { return false; }
  void clearPendingEvents() {}
};
