// Unit tests for GrayscalePreview::previewLevel -- the decode that turns the
// firmware's two AA planes into the simulator's gray levels.
//
// WHY THIS EXISTS. The decode shipped with a rule that was true in one polarity
// and false in the other: "a base-WHITE pixel stays white regardless of plane
// bits". In light mode the firmware's base pass paints every coverage level as
// ink, so a flagged pixel is always black and the rule never fires. In DARK mode
// the base paints only full ink, so every partial-coverage pixel -- every glyph
// edge -- arrives white AND flagged, and the rule discarded all of them.
//
// The result was that dark-mode text had NO antialiasing whatsoever: 28,550
// computed AA pixels for one book page, all thrown away, glyph stems rendered
// skeletal with hard edges. Reported from the phone as "the antialiasing on the
// sans serif fonts looks bad in crt", and it was worst on a sans serif because
// its long straight stems are almost entirely edge pixels at reading sizes.
//
// Nothing else could have caught it. It is not a crash, not a leak, and not a
// wrong API: it is a page that renders, in one appearance only, with a detail
// missing. No compiler sees that, and every other test in this repo passed
// throughout.
//
// The masks below are the FIRMWARE'S OWN, transcribed from
// lib/GfxRenderer/GlyphAaPlanes.h. They are what makes this a test of the
// contract rather than a restatement of the implementation.
//
// Build + run (no framework, no CMake):
//   c++ -std=c++17 -Isrc tests/grayscale_preview_test.cpp -o /tmp/gp && /tmp/gp

#include "GrayscalePreview.h"

#include <utility>

#include <cstdio>

static int failures = 0;

#define CHECKM(cond, ...)                                                      \
  do {                                                                         \
    if (!(cond)) {                                                             \
      std::printf("FAIL %s:%d: ", __FILE__, __LINE__);                         \
      std::printf(__VA_ARGS__);                                                \
      std::printf("\n");                                                       \
      failures++;                                                              \
    }                                                                          \
  } while (0)

namespace {

using namespace GrayscalePreview;

// The firmware's plane assignment, from GlyphAa::planes(). Bit N is glyph
// coverage level N: L0 full ink, L1 high coverage, L2 low coverage.
constexpr uint8_t L0 = 1u << 0;
constexpr uint8_t L1 = 1u << 1;
constexpr uint8_t L2 = 1u << 2;

struct Planes {
  uint8_t baseInk;  // levels the BW base pass paints as ink
  uint8_t msb;
  uint8_t lsb;
};

// Light mode, AA_STANDARD: the base paints EVERY level as ink.
constexpr Planes kLightStandard{L0 | L1 | L2, L1 | L2, L1};
// Dark mode, AA_STANDARD: the base paints ONLY full ink. This is the case that
// was broken -- L1 and L2 arrive base-white and flagged.
constexpr Planes kDarkStandard{L0, L1 | L2, L2};
// Dark mode, AA_CRISP: base paints L0 and L1, so only L2 arrives base-white.
constexpr Planes kDarkCrisp{L0 | L1, L2, L2};

// What the decode returns for one glyph coverage level under one plane
// assignment -- i.e. exactly what the panel would show for that pixel.
uint8_t levelFor(const Planes &p, uint8_t coverageBit) {
  const bool baseWhite = (p.baseInk & coverageBit) == 0;
  const bool msb = (p.msb & coverageBit) != 0;
  const bool lsb = (p.lsb & coverageBit) != 0;
  return previewLevel(baseWhite, msb, lsb);
}

// THE BUG ITSELF: in dark mode every partial-coverage level must produce a gray
// that is neither the page nor solid ink. Before the fix all three of these
// returned kWhite -- the page -- which is an edge that vanishes.
void testDarkModeEdgesAreGray() {
  for (const auto &tc : {std::pair<const char *, Planes>{"dark Standard",
                                                         kDarkStandard},
                         {"dark Crisp", kDarkCrisp}}) {
    const uint8_t high = levelFor(tc.second, L1);
    const uint8_t low = levelFor(tc.second, L2);
    CHECKM(high != kWhite, "%s: high-coverage edge is the page (%d)", tc.first,
           high);
    CHECKM(low != kWhite, "%s: low-coverage edge is the page (%d)", tc.first,
           low);
    CHECKM(high == kLight || high == kDark || high == kBlack,
           "%s: high-coverage edge is not a panel level (%d)", tc.first, high);
    CHECKM(low == kLight || low == kDark,
           "%s: low-coverage edge is not a gray (%d)", tc.first, low);
  }
}

// Full ink stays full ink in both polarities -- an edge fix that also lightened
// the glyph body would be a different bug wearing the first one's clothes.
void testFullInkIsUntouched() {
  CHECKM(levelFor(kLightStandard, L0) == kBlack, "light: full ink is not ink");
  CHECKM(levelFor(kDarkStandard, L0) == kBlack, "dark: full ink is not ink");
  CHECKM(levelFor(kDarkCrisp, L0) == kBlack, "dark crisp: full ink is not ink");
}

// LIGHT MODE IS UNCHANGED BY THE FIX. There a flagged pixel is always already
// black, so the reordering cannot alter any input the firmware emits. This is
// the regression guard on the half that was working.
void testLightModeIsUnchanged() {
  // The pre-fix decode, verbatim.
  auto oldDecode = [](bool baseWhite, bool msb, bool lsb) -> uint8_t {
    if (baseWhite) return kWhite;
    if (msb) return lsb ? kDark : kLight;
    if (lsb) return kDark;
    return kBlack;
  };
  for (uint8_t bit : {L0, L1, L2}) {
    const bool baseWhite = (kLightStandard.baseInk & bit) == 0;
    const bool msb = (kLightStandard.msb & bit) != 0;
    const bool lsb = (kLightStandard.lsb & bit) != 0;
    CHECKM(previewLevel(baseWhite, msb, lsb) == oldDecode(baseWhite, msb, lsb),
           "light mode changed for coverage bit %d", bit);
  }
  // And an unflagged white pixel is still the page, in every polarity: that is
  // the margin, and the fix must not tint it.
  CHECKM(previewLevel(true, false, false) == kWhite,
         "an unflagged white pixel is no longer the page");
  CHECKM(previewLevel(false, false, false) == kBlack,
         "an unflagged black pixel is no longer ink");
}

// The two grays must stay distinct and ordered, or the ramp collapses and the
// edge is back to a hard step with extra work done to produce it.
void testGraysAreDistinct() {
  CHECKM(kLight != kDark, "the two grays are the same level");
  CHECKM(kBlack < kDark && kDark < kLight && kLight < kWhite,
         "the four levels are not ordered ink -> page");
  CHECKM(previewLevel(false, true, false) == kLight, "MSB only is light gray");
  CHECKM(previewLevel(false, true, true) == kDark, "MSB+LSB is dark gray");
  CHECKM(previewLevel(false, false, true) == kDark, "LSB only is dark gray");
  // Same answers with the base white, which is the whole point of the fix.
  CHECKM(previewLevel(true, true, false) == kLight,
         "MSB only is light gray on a white base too");
  CHECKM(previewLevel(true, true, true) == kDark,
         "MSB+LSB is dark gray on a white base too");
}

}  // namespace

int main() {
  testDarkModeEdgesAreGray();
  testFullInkIsUntouched();
  testLightModeIsUnchanged();
  testGraysAreDistinct();

  if (failures) {
    std::printf("\n%d failure(s)\n", failures);
    return 1;
  }
  std::printf("grayscale_preview: all checks passed\n");
  return 0;
}
