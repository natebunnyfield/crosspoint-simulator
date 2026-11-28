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
  // SIMULATOR ONLY, no firmware HAL counterpart: the firmware calls it only
  // under SIMULATOR. The Tube row (the dark page's phosphor, src/FrontlitPage.h
  // kTubePhosphor), published with the light so every host follows it.
  void setTube(uint8_t tube);

  uint8_t brightness() const;
  uint8_t warmth() const;
  bool isOn() const;

private:
  // The Picco app's byte is the Brightness STEP (FrontlitLight.h), so its
  // power-on 60 is step 32; the X4 Pro's is a percent.
#if defined(SIMULATOR_DEVICE_PICCO)
  uint8_t lastBrightness = 32;
#else
  uint8_t lastBrightness = 60;
#endif
  uint8_t lastWarmth = 50;
  bool lit = false;
  uint8_t lastTube = 0;
};

#define Frontlight HalFrontlight::getInstance()
