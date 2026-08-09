// PLACEHOLDER, AHEAD OF THE FIRMWARE -- do not delete as unused.
//
// Nothing in the firmware calls this: lib/hal/ has exactly six HAL classes
// (Clock, Display, GPIO, PowerManager, Storage, System) and this is not one of
// them. It is here because the hardware is real -- the X4 Pro has a frontlight,
// and the SDK ships freeink-sdk/libs/hardware/FrontlightManager -- so the day
// the firmware grows a brightness control this is the file it links against.
//
// Ruled KEEP (ST-002 in TODO.md). Zero references is not grounds for deletion
// in this project; deleting it means rebuilding it later, blind, by someone who
// does not know it existed.

#pragma once

#include <Arduino.h>

// Host model of the X4 Pro dual-channel frontlight. The framebuffer is
// unchanged; this class preserves the firmware-visible brightness, warmth, and
// on/off state so the quick panel and persisted settings can be exercised.
class HalFrontlight {
public:
  static HalFrontlight &getInstance();

  void begin(uint8_t brightness, uint8_t warmth, bool on);

  bool present() const;
  bool hasColorTemperature() const;

  void setBrightness(uint8_t percent);
  void setWarmth(uint8_t warmPercent);
  void setOn(bool on);

  uint8_t brightness() const;
  uint8_t warmth() const;
  bool isOn() const;

private:
  uint8_t lastBrightness = 60;
  uint8_t lastWarmth = 50;
  bool lit = false;
};

#define Frontlight HalFrontlight::getInstance()
