#pragma once

// Cross-target build identity, and the check that two halves of one binary
// agree about it.
//
// WHY THIS EXISTS. The iOS app is two CMake targets: `crosspoint_core` (the
// firmware plus this HAL, ~155 TUs) and `CrossPointX3` (the harness, 7 TUs).
// A compile definition set on only one of them produces a binary whose halves
// disagree, and every symptom of that is remote from its cause:
//
//   * CROSSPOINT_RENDER_SCALE=2 sat PRIVATE on the app target through 15
//     TestFlight builds. Those shipped 1x glyphs while the pbxproj said 2x.
//   * SIMULATOR_DEVICE_X3 sat PRIVATE on the app target until 2026-08-06, so
//     the firmware and the whole HAL built an X4. HalClock then refused to
//     arm (X3 / X4 Pro only), getDateTime() failed, and every calendar sleep
//     screen fell back to the stock logo screen. The reported bug was "the
//     sleep screen setting does nothing".
//
// Both were invisible at build time: the code compiles, links and runs. So
// this is a runtime equality check, called once at startup from a HARNESS TU,
// comparing the constants that TU compiled against with the ones the core
// library compiled against. A mismatch aborts, loudly, with both values —
// there is no useful work a split-brain binary can do, and shipping one is
// how the two bugs above reached testers.
//
// It is deliberately NOT a static_assert: the whole failure mode is two
// translation units in DIFFERENT targets seeing different macro values, and
// no compile-time construct in one TU can see the other's.
//
// On desktop, where there is one target, the check compares the core against
// itself and always passes. Keep calling it anyway — the cost is one function
// call at startup, and it prints the identity, which is worth having in a log.

#include <EInkDisplay.h>

#include <cstdint>

struct SimulatorBuildIdentity {
  // Which BoardConfig.h branch this TU compiled: "X3", "X4Pro" or "X4". The
  // X4 case is the silent #else default, which is exactly why it is reported
  // by name rather than inferred from the absence of the other two.
  const char *device;
  // Logical panel geometry the firmware lays out against.
  uint16_t logicalWidth;
  uint16_t logicalHeight;
  // Supersampling CEILING. Comes from CROSSPOINT_RENDER_SCALE via HalDisplay.h,
  // which silently defaults to 1 — the other half of the 15-build 1x bug.
  //
  // The ceiling and not the active factor, deliberately: this struct exists to
  // prove the harness and the core were COMPILED the same way, and the active
  // factor is a launch-time choice both halves read from one variable. A field
  // that can differ between two runs of the same binary would make the compare
  // meaningless.
  int renderScale;
};

namespace simulator_build_identity_detail {

#if defined(SIMULATOR_DEVICE_X4_PRO)
inline constexpr const char *kDevice = "X4Pro";
#elif defined(SIMULATOR_DEVICE_X3)
inline constexpr const char *kDevice = "X3";
#else
inline constexpr const char *kDevice = "X4";
#endif

#if defined(CROSSPOINT_RENDER_SCALE)
inline constexpr int kRenderScale = CROSSPOINT_RENDER_SCALE;
#else
inline constexpr int kRenderScale = 1;
#endif

} // namespace simulator_build_identity_detail

// The identity of the TU that includes this header, evaluated from its own
// macros. Two targets that disagree produce two different values here.
inline constexpr SimulatorBuildIdentity localBuildIdentity() {
  return SimulatorBuildIdentity{simulator_build_identity_detail::kDevice,
                                EInkDisplay::DISPLAY_WIDTH,
                                EInkDisplay::DISPLAY_HEIGHT,
                                simulator_build_identity_detail::kRenderScale};
}

// Defined in SimulatorBuildIdentity.cpp, which lives in crosspoint_core — so
// this returns the CORE's view, whatever the caller compiled against.
SimulatorBuildIdentity coreBuildIdentity();

// Compare the caller's identity with the core's; log both and abort on any
// difference. `who` names the calling layer for the log line ("iOS harness").
// Call once, early, from a translation unit OUTSIDE crosspoint_core.
void verifyBuildIdentityMatchesCore(const SimulatorBuildIdentity &local,
                                    const char *who);
