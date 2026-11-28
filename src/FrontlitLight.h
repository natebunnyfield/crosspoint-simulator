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
