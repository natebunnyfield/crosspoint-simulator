#pragma once

// The Picco frontlight's state as the simulated page sees it (TODO.md ST-012).
// Its own header so src/HalFrontlight.cpp, which publishes it, does not have to
// pull in the color models that src/FrontlitPage.h turns it into a page with.

namespace frontlitpage {

// The firmware's defaults (crosspoint-reader src/CrossPointSettings.h:249-250).
// The frozen page is what renders at exactly these.
inline constexpr int kDefaultBrightness = 60;
inline constexpr int kDefaultWarmth = 50;
inline constexpr int kMax = 100;

// BRIGHTNESS RUNS -100..300 IN THE APP (owner 2026-11-27: "let brightness go
// from -100 to 300, keeping current 0 to 100 as is"). 0..100 is unchanged;
// below 0 the trace and ink fade under the 7:1 floor to 1.5:1 at -100, and
// above 100 they keep the 60..100 slope. A settings byte cannot hold the range,
// so the firmware's Picco app build stores the STEP (crosspoint-reader
// src/CrossPointSettings.h, SettingsList.h withShown): shown = -100 + 5 x
// stored, 0..80. tests/frontlit_page_test.cpp pins the decode against the
// firmware's row.
inline constexpr int kMinBrightness = -100;
inline constexpr int kMaxBrightness = 300;
inline constexpr int kBrightnessStoredStep = 5;
inline constexpr int kMaxStoredBrightness =
    (kMaxBrightness - kMinBrightness) / kBrightnessStoredStep;  // 80
inline constexpr int brightnessFromStored(int stored) {
  return kMinBrightness +
         (stored < 0 ? 0 : (stored > kMaxStoredBrightness ? kMaxStoredBrightness : stored)) *
             kBrightnessStoredStep;
}

// THE TUBE (owner 2026-11-27, docs/crt-gamut-plan-2026-11-27.md "Owner
// rulings"): which phosphor the dark page is. The firmware's Tube row, a Picco
// row compiled into the app and simulator builds only, in its order: the index
// IS the stored value. 0 is Mixed, today's four-gun tube.
inline constexpr int kTubeMixed = 0;
inline constexpr int kTubeCount = 8;

struct Light {
  int brightness = kDefaultBrightness;
  int warmth = kDefaultWarmth;
  bool on = false;
  int tube = kTubeMixed;
};

}  // namespace frontlitpage

// The live state, published by the simulator's HalFrontlight on a Picco build
// and read by the hosts. Simulator-only: the firmware HAL has no counterpart,
// and nothing here is a HalFrontlight method (the HAL's surface must mirror
// the firmware's).
namespace simfrontlight {

// Off (and at the defaults) on every board but the Picco, so nothing else moves.
frontlitpage::Light current();
// Bumped on every change, so a per-frame poll can be edge-triggered.
unsigned generation();
// Called, on the thread that changed the light, after each change. The desktop
// installs one to re-seed the page; iOS polls generation() instead.
using ChangedHook = void (*)();
void setChangedHook(ChangedHook hook);

}  // namespace simfrontlight
