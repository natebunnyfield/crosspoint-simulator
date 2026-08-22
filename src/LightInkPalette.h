#pragma once

// LIGHT INK PALETTE -- historical inks at variable density on proven paper
// stocks, for the LIGHT page. Doctrine (owner order 2026-08-22): light mode is
// paper-and-ink emulation; dark mode is the CRT and keeps the gun mixer. This
// header is the light picker's whole model: the ink table, the six papers, the
// dilution curve, the contrast math and the 7:1 clamps. Research and the
// derivation of every number: docs/light-ink-picker.md.
//
// PURE AND HOST-TESTABLE, on the same terms as PanelPalette.h: no SDL, no
// UIKit, no clock, no I/O. tests/light_ink_test.cpp exercises all of it on a
// Mac or Linux box, because every failure mode here is a wrong COLOR or a
// broken floor, and neither is visible to a compiler.
//
// --- The three rules that shape this file ----------------------------------
//
// APPEND-ONLY INDICES. An ink or paper choice persists as an integer
// (lightInkIndex / lightPaperIndex in NSUserDefaults), so rows APPEND and are
// never inserted or re-pointed -- the PanelPalette preset rule. Row 0 of each
// table is the SHIPPED tone ("Standard" ink #2D2D2D, "Bright White" paper
// #FBFBF9), so an untouched install changes nothing and the default stays a
// row.
//
// DENSITY IS THE ONLY VARIABLE. Each ink is one hue with one dial: dilution
// along the ink's own wash curve, 0 = the paper itself, 100 = the full-strength
// film. Physically honest -- a writer never had a hue slider, but every wash
// drawing is the same pigment at different concentrations -- and it keeps every
// offered color ON an ink's real dilution locus.
//
// THE 7:1 FLOOR IS A CLAMP, NOT ADVICE. Every ink x paper pair clears 7:1 at
// full density (the tables were derived under that constraint; the test
// re-measures every pair), and the density slider's floor per ink is exactly
// where 7:1 would break on the CURRENT paper -- the PhosphorGrain budget
// pattern.
//
// --- The dilution curve is Beer-Lambert, not a lerp ------------------------
//
// A pigment wash obeys the Beer-Lambert law: absorbance is proportional to
// concentration, so transmittance EXPONENTIATES with density. Per channel in
// linear light:
//
//   wash(d) = paper_lin * (ink_lin / paper_lin)^d
//
// d=0 is the paper exactly and d=1 the ink exactly (byte-exact, pinned by
// test). The spec's suggested linear-light lerp was implemented, compared at
// 30-70% density, and rejected: the lerp is the straight chord through the
// gamut and desaturates immediately (sepia at 30% on Cream lerps to #D5CDBC, a
// pale gray-beige), while the exponential path keeps the hue's channel
// ordering all the way down (#A79376, a recognizable sepia wash). The ink's
// linear channels are clamped to a small epsilon before the ratio, or an ink
// with a zero channel would dilute to zero in that channel at ANY density --
// a 1% Prussian wash with literally no red.

#include <cmath>
#include <cstdint>

namespace lightink {

struct Ink {
  const char *name;
  const char *era;      // one-line era note, shown in the picker row
  uint8_t full[3];      // the full-strength film (density 100)
};

struct Paper {
  const char *name;
  const char *note;
  uint8_t tone[3];
};

// APPEND ONLY. See the header comment; the stored integer IS the row.
enum InkIndex : int {
  kInkStandard = 0,   // the shipped e-ink tone; the default stays a row
  kInkCarbonBlack,    // lampblack/soot, Egypt & China ~2500 BCE
  kInkIronGall,       // the 5th-19th c. blue-black; browns with age
  kInkSepia,          // cuttlefish wash medium, late 18th-19th c.
  kInkWalnutBistre,   // old-master golden-brown washes
  kInkOxblood,        // deep madder/carmine red, dark enough for body text
  kInkIndigo,         // the vat dye's violet-leaning blue
  kInkPrussianBlue,   // 1704, the first synthetic pigment
  kInkCount
};

enum PaperIndex : int {
  kPaperBrightWhite = 0,  // the shipped paper; real bright stock is not #FFFFFF
  kPaperCream,            // classic cream trade-book stock
  kPaperBone,             // natural/bone offset -- warm, far less yellow
  kPaperChamois,          // aged tan; darkest field, sets most floors
  kPaperPressGray,        // cool gray press stock; the one cool option
  kPaperSepiaToned,       // browner and pinker than chamois' yellow tan
  kPaperCount
};

// Full-strength anchors are THIS REPO'S derivation: the recognized hue carried
// to body-text density under the 7:1-on-every-paper constraint. The named
// swatch an ink is known by is often a WASH -- Maerz & Paul's sepia #704214
// (A Dictionary of Color, 1930) sits ~42% along this table's sepia curve on
// Cream -- so the anchors are darker than the famous hex on purpose.
inline constexpr Ink kInks[kInkCount] = {
    {"Standard", "the shipped e-ink tone", {0x2D, 0x2D, 0x2D}},
    {"Carbon Black", "soot & binder, ~2500 BCE", {0x1E, 0x1C, 0x1A}},
    {"Iron Gall", "5th-19th c. blue-black, browns with age", {0x1B, 0x2A, 0x3C}},
    {"Sepia", "cuttlefish wash, 18th-19th c.", {0x3E, 0x2A, 0x18}},
    {"Walnut & Bistre", "old-master brown washes", {0x4B, 0x3A, 0x15}},
    {"Oxblood", "deep madder red", {0x4F, 0x15, 0x11}},
    {"Indigo", "the vat dye's blue", {0x2A, 0x3B, 0x5C}},
    {"Prussian Blue", "1704, first synthetic pigment", {0x0B, 0x30, 0x50}},
};

inline constexpr Paper kPapers[kPaperCount] = {
    {"Bright White", "bright text stock (shipped)", {0xFB, 0xFB, 0xF9}},
    {"Cream", "cream trade-book stock", {0xF8, 0xF0, 0xD9}},
    {"Bone", "natural offset", {0xEF, 0xEA, 0xE0}},
    {"Chamois", "aged tan", {0xEC, 0xDA, 0xB7}},
    {"Press Gray", "cool press stock", {0xE9, 0xEA, 0xEC}},
    {"Sepia Toned", "toned sheet", {0xEE, 0xDF, 0xCC}},
};

inline constexpr double kContrastFloor = 7.0;
inline constexpr int kDensityMax = 100;

// Unknown indices FALL BACK rather than index out of bounds: a restored backup
// written by a future build must land on the shipped look, the same answer
// panelpalette::resolve gives an unknown preset.
constexpr int clampInkIndex(int i) {
  return (i >= 0 && i < kInkCount) ? i : kInkStandard;
}
constexpr int clampPaperIndex(int i) {
  return (i >= 0 && i < kPaperCount) ? i : kPaperBrightWhite;
}

// --- Contrast (WCAG relative luminance, the repo's standing arithmetic) ----

inline double srgbToLinear(uint8_t v) {
  const double c = v / 255.0;
  return c <= 0.04045 ? c / 12.92 : std::pow((c + 0.055) / 1.055, 2.4);
}

inline uint8_t linearToSrgb(double l) {
  double v = l <= 0.0031308 ? l * 12.92 : 1.055 * std::pow(l, 1.0 / 2.4) - 0.055;
  v = v * 255.0;
  if (v < 0.0) v = 0.0;
  if (v > 255.0) v = 255.0;
  return static_cast<uint8_t>(std::lround(v));
}

inline double relativeLuminance(const uint8_t rgb[3]) {
  return 0.2126 * srgbToLinear(rgb[0]) + 0.7152 * srgbToLinear(rgb[1]) +
         0.0722 * srgbToLinear(rgb[2]);
}

inline double contrastRatio(const uint8_t a[3], const uint8_t b[3]) {
  const double ya = relativeLuminance(a), yb = relativeLuminance(b);
  const double hi = ya > yb ? ya : yb, lo = ya > yb ? yb : ya;
  return (hi + 0.05) / (lo + 0.05);
}

// --- The dilution curve ----------------------------------------------------

// Floor for a linear channel entering the Beer-Lambert ratio. Not a tuning
// value: it only exists so a zero channel dilutes like a very dark one instead
// of like a perfect filter.
inline constexpr double kLinearEpsilon = 1e-4;

// The wash: ink `inkIdx` at `densityPct` (0..100) on paper `paperIdx`.
// densityPct is clamped to [0, 100]; indices fall back per the clamps above.
// The two ends return the table bytes EXACTLY -- stated as code, not left to
// floating-point luck, because "0% is the paper and 100% is the ink" is the
// contract every consumer leans on.
inline void inkAtDensity(int inkIdx, int paperIdx, int densityPct,
                         uint8_t out[3]) {
  const Ink &ink = kInks[clampInkIndex(inkIdx)];
  const Paper &paper = kPapers[clampPaperIndex(paperIdx)];
  if (densityPct >= kDensityMax) {
    for (int c = 0; c < 3; c++) out[c] = ink.full[c];
    return;
  }
  if (densityPct <= 0) {
    for (int c = 0; c < 3; c++) out[c] = paper.tone[c];
    return;
  }
  const double d = densityPct / static_cast<double>(kDensityMax);
  for (int c = 0; c < 3; c++) {
    double il = srgbToLinear(ink.full[c]);
    double pl = srgbToLinear(paper.tone[c]);
    if (il < kLinearEpsilon) il = kLinearEpsilon;
    if (pl < kLinearEpsilon) pl = kLinearEpsilon;
    out[c] = linearToSrgb(pl * std::pow(il / pl, d));
  }
}

// The contrast of a wash against its own paper.
inline double contrastAtDensity(int inkIdx, int paperIdx, int densityPct) {
  uint8_t wash[3];
  inkAtDensity(inkIdx, paperIdx, densityPct, wash);
  return contrastRatio(wash, kPapers[clampPaperIndex(paperIdx)].tone);
}

// THE FLOOR: the smallest density (percent) whose wash still clears 7:1 on
// this paper. Luminance is strictly monotone in density (every ink channel
// sits below its paper channel -- the test proves it), so this is a single
// point and a linear scan finds it exactly on the integer lattice the slider
// offers. Every pair clears the floor at 100 by table construction, and the
// 100 return on the (unreachable) alternative is the safe end of the dial.
inline int floorDensityPct(int inkIdx, int paperIdx) {
  for (int pct = 0; pct <= kDensityMax; pct++) {
    if (contrastAtDensity(inkIdx, paperIdx, pct) >= kContrastFloor) return pct;
  }
  return kDensityMax;
}

// The clamp the slider and every stored value go through: never below the
// paper's floor for this ink, never above full strength.
inline int clampDensityPct(int inkIdx, int paperIdx, int densityPct) {
  const int floor = floorDensityPct(inkIdx, paperIdx);
  if (densityPct < floor) return floor;
  if (densityPct > kDensityMax) return kDensityMax;
  return densityPct;
}

// --- Guards ----------------------------------------------------------------
//
// Row 0 of each table must be the shipped tones, or "an untouched install
// changes nothing" is broken silently and in pixels.
static_assert(kInks[kInkStandard].full[0] == 0x2D &&
                  kInks[kInkStandard].full[1] == 0x2D &&
                  kInks[kInkStandard].full[2] == 0x2D,
              "Standard ink must be the shipped 2D2D2D");
static_assert(kPapers[kPaperBrightWhite].tone[0] == 0xFB &&
                  kPapers[kPaperBrightWhite].tone[1] == 0xFB &&
                  kPapers[kPaperBrightWhite].tone[2] == 0xF9,
              "Bright White must be the shipped FBFBF9");
static_assert(clampInkIndex(-1) == kInkStandard &&
                  clampInkIndex(kInkCount) == kInkStandard &&
                  clampPaperIndex(999) == kPaperBrightWhite,
              "unknown indices must fall back to the shipped rows");

}  // namespace lightink
