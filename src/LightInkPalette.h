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
// CONCENTRATION IS THE ONLY VARIABLE, ON BOTH SIDES. Each ink is one hue with
// one dial: dilution along the ink's own wash curve, 0 = the paper itself,
// 100 = the full-strength film. Each paper is one stock with one dial (owner
// order 2026-08-22, "paper needs a 0-100 slider too"): tint strength, 0 = the
// neutral bright-white ground, 100 = the stock at full strength. Physically
// honest -- a writer never had a hue slider, but every wash drawing is the
// same pigment at different concentrations and every tinted sheet is the same
// colorant at different loadings -- and it keeps every offered color ON a real
// locus rather than in an arbitrary RGB cube. Neither dial is a lerp; both
// obey the same Beer-Lambert absorption law, below.
//
// THE 7:1 FLOOR IS A CLAMP, NOT ADVICE -- AND IT IS NOW A SURFACE. Every ink x
// paper pair clears 7:1 at full density on the full-strength stock (the tables
// were derived under that constraint; the test re-measures the whole 8 x 6 x
// density x strength grid), and each slider stops where 7:1 would break at the
// OTHER slider's current value -- the PhosphorGrain budget pattern, in two
// dimensions. The rule is stated in full above floorDensityPct.
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
  // TOOTH: this stock's surface roughness, as a multiple of the shipped
  // Bright White's. It scales the letterpress sheet-tooth amplitude, so a
  // chamois shows more grain than a coated bright white. Bright White is
  // exactly 1.0 -- an untouched install renders the tooth it always did.
  // Per-stock derivation: docs/light-ink-picker.md section 6.
  float tooth;
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
    {"Bright White", "bright text stock (shipped)", {0xFB, 0xFB, 0xF9}, 1.00f},
    {"Cream", "cream trade-book stock", {0xF8, 0xF0, 0xD9}, 1.30f},
    {"Bone", "natural offset", {0xEF, 0xEA, 0xE0}, 1.45f},
    {"Chamois", "aged tan", {0xEC, 0xDA, 0xB7}, 1.80f},
    {"Press Gray", "cool press stock", {0xE9, 0xEA, 0xEC}, 1.60f},
    {"Sepia Toned", "toned sheet", {0xEE, 0xDF, 0xCC}, 1.50f},
};

inline constexpr double kContrastFloor = 7.0;
inline constexpr int kDensityMax = 100;
// The PAPER's dial, the ink density's twin (owner order 2026-08-22: "paper
// needs a 0-100 slider too"). 0 is the neutral bright-white ground -- row 0's
// own tone -- and 100 is the stock at full strength. The default is 100, so a
// stock reads as its table tone until the slider is touched and the shipped
// Bright White row stays byte-exact at every value.
inline constexpr int kPaperStrengthMax = 100;
inline constexpr int kPaperStrengthDefault = kPaperStrengthMax;

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

// --- The paper's tint strength, the SAME absorption model ------------------
//
// A stock's tint is a colorant carried in an otherwise white sheet -- pulp
// dye, a coating, or the oxidation of an aged one -- and a colorant is a
// SUBTRACTIVE FILTER over white. That is the same physics the ink's dilution
// obeys, so it gets the same law rather than a second one: absorbance is
// proportional to how much colorant the sheet carries, so transmittance
// EXPONENTIATES with strength. Per channel in linear light, against the
// neutral bright-white ground:
//
//   stockAt(s) = white_lin * (stock_lin / white_lin)^s
//
// The alternative -- a linear-light lerp toward white -- was rejected for the
// ink for a reason that applies here in miniature: the chord runs through the
// neutral, so a half-strength cream desaturates toward gray-white instead of
// staying a pale cream. Over the tiny gamut a paper covers the two curves are
// close (a few code values), but "one absorption law for both dials" is worth
// more than the difference, and the mid-strength hue is still measurably
// truer. Both ends are byte-exact.
//
// WHITE IS ROW 0'S OWN TONE, not #FFFFFF: the shipped Bright White #FBFBF9 IS
// the neutral ground (see the doc's honesty note about real bright stock), so
// Bright White is a no-op at every strength -- returned as an early exit
// rather than trusted to pow(1, s).
inline void paperAtStrength(int paperIdx, int strengthPct, uint8_t out[3]) {
  const int idx = clampPaperIndex(paperIdx);
  const Paper &stock = kPapers[idx];
  const Paper &white = kPapers[kPaperBrightWhite];
  if (idx == kPaperBrightWhite || strengthPct >= kPaperStrengthMax) {
    for (int c = 0; c < 3; c++) out[c] = stock.tone[c];
    return;
  }
  if (strengthPct <= 0) {
    for (int c = 0; c < 3; c++) out[c] = white.tone[c];
    return;
  }
  const double t = strengthPct / static_cast<double>(kPaperStrengthMax);
  for (int c = 0; c < 3; c++) {
    double sl = srgbToLinear(stock.tone[c]);
    double wl = srgbToLinear(white.tone[c]);
    if (sl < kLinearEpsilon) sl = kLinearEpsilon;
    if (wl < kLinearEpsilon) wl = kLinearEpsilon;
    out[c] = linearToSrgb(wl * std::pow(sl / wl, t));
  }
}

// THE STOCK'S TOOTH AT THIS STRENGTH (owner order 2026-08-22: "be sure to be
// adding the existing noise treatment to it"). The letterpress sheet pass
// already textures the whole surface; what it did not do is vary with the
// PAPER, so a coated bright white and an aged chamois wore the same grain.
// The factor is what multiplies letterpress::kToothAt100 for this sheet.
//
// LINEAR in the strength dial, deliberately -- unlike the tone. Tone is an
// absorption depth and exponentiates; tooth is "how much of this stock's
// SURFACE you asked for", and the honest reading of a slider at 40% is 40% of
// the way from the smooth ground to that stock's own texture. Monotone in
// both arguments, and exactly Bright White's 1.0 at strength 0, so the dial
// brings a stock's texture up with its tone and takes both away together.
inline float toothScaleFor(int paperIdx, int strengthPct) {
  const Paper &stock = kPapers[clampPaperIndex(paperIdx)];
  const float base = kPapers[kPaperBrightWhite].tooth;
  int s = strengthPct;
  if (s < 0) s = 0;
  if (s > kPaperStrengthMax) s = kPaperStrengthMax;
  const float t = static_cast<float>(s) / static_cast<float>(kPaperStrengthMax);
  return base + (stock.tooth - base) * t;
}

// The wash: ink `inkIdx` at `densityPct` (0..100) on paper `paperIdx` held at
// `paperStrengthPct`. densityPct is clamped to [0, 100]; indices fall back per
// the clamps above. The two ends return exact bytes -- stated as code, not
// left to floating-point luck, because "0% is the paper and 100% is the ink"
// is the contract every consumer leans on.
//
// paperStrengthPct is a TRAILING DEFAULTED argument on purpose: every call
// site written before the paper dial existed keeps meaning exactly what it
// meant, which is the stock at full strength.
inline void inkAtDensity(int inkIdx, int paperIdx, int densityPct,
                         uint8_t out[3],
                         int paperStrengthPct = kPaperStrengthDefault) {
  const Ink &ink = kInks[clampInkIndex(inkIdx)];
  uint8_t ground[3];
  paperAtStrength(paperIdx, paperStrengthPct, ground);
  if (densityPct >= kDensityMax) {
    for (int c = 0; c < 3; c++) out[c] = ink.full[c];
    return;
  }
  if (densityPct <= 0) {
    for (int c = 0; c < 3; c++) out[c] = ground[c];
    return;
  }
  const double d = densityPct / static_cast<double>(kDensityMax);
  for (int c = 0; c < 3; c++) {
    double il = srgbToLinear(ink.full[c]);
    double pl = srgbToLinear(ground[c]);
    if (il < kLinearEpsilon) il = kLinearEpsilon;
    if (pl < kLinearEpsilon) pl = kLinearEpsilon;
    out[c] = linearToSrgb(pl * std::pow(il / pl, d));
  }
}

// The contrast of a wash against its own paper, at that paper's strength.
inline double contrastAtDensity(int inkIdx, int paperIdx, int densityPct,
                                int paperStrengthPct = kPaperStrengthDefault) {
  uint8_t wash[3], ground[3];
  inkAtDensity(inkIdx, paperIdx, densityPct, wash, paperStrengthPct);
  paperAtStrength(paperIdx, paperStrengthPct, ground);
  return contrastRatio(wash, ground);
}

// --- THE 7:1 FLOOR IS A SURFACE, NOT A LINE --------------------------------
//
// With two dials the legal region is two-dimensional: contrast falls as the
// ink is DILUTED and falls again as the paper is TINTED, and either alone can
// cross 7:1. The rule, stated once and implemented as the two functions below:
//
//   THE SLIDER YOU ARE MOVING IS THE ONE THAT STOPS; THE OTHER HOLDS.
//
// Density has a FLOOR (dilute far enough and the wash meets its paper) and
// paper strength has a CEILING (tint far enough and the ground meets the
// ink), so the two clamps run in opposite directions and each is computed at
// the OTHER dial's current value. Changing the ink or the paper STOCK is not
// a slider move, so it re-clamps the DENSITY while the paper strength holds:
// the sheet is the thing the owner picked deliberately, and the ink is the
// variable that pays for it.
//
// The region is never empty. Density 100 is the ink itself, independent of
// the ground, and every one of the 48 pairs clears 7:1 at FULL paper strength
// by table construction -- so full density is legal at every strength, and a
// floor always exists. Symmetrically, if a state is legal then lowering the
// paper strength keeps it legal (a whiter ground can only raise contrast), so
// a ceiling always exists too.
//
// Both are found by SCAN rather than by inverting the formula, and the
// direction each scans in is not cosmetic. Contrast is exactly monotone in
// DENSITY (measured: zero inversions over the whole grid), so the first
// clearing percent IS the boundary. It is NOT exactly monotone in paper
// STRENGTH: the tone quantizes to a byte at every step, so the ratio ripples
// by up to 0.068 on its way down (13.29 -> 10.02 for Standard on Chamois).
// A scan DOWN from 100 would therefore return a ceiling with illegal
// strengths beneath it -- 3,300 of them across the grid, the worst 6.96:1.
// They are rounding wiggles rather than a legibility cliff, but "every
// reachable state clears 7:1" has to be checkable, so the ceiling is the
// PREFIX boundary: scan UP and stop at the first failure. It costs at most 19
// points of strength in the worst corner (Prussian Blue on Cream at 66%
// density) and it makes the guarantee exact instead of approximate.

// The smallest density whose wash clears 7:1 on this paper AT THIS STRENGTH.
inline int floorDensityPct(int inkIdx, int paperIdx,
                           int paperStrengthPct = kPaperStrengthDefault) {
  for (int pct = 0; pct <= kDensityMax; pct++) {
    if (contrastAtDensity(inkIdx, paperIdx, pct, paperStrengthPct) >=
        kContrastFloor)
      return pct;
  }
  return kDensityMax;
}

// The clamp the density slider and every stored density go through: never
// below the floor for this ink on this sheet, never above full strength.
inline int clampDensityPct(int inkIdx, int paperIdx, int densityPct,
                           int paperStrengthPct = kPaperStrengthDefault) {
  const int floor = floorDensityPct(inkIdx, paperIdx, paperStrengthPct);
  if (densityPct < floor) return floor;
  if (densityPct > kDensityMax) return kDensityMax;
  return densityPct;
}

// THE CEILING: the most tint this sheet can carry at this ink and density with
// every strength up to it also clearing 7:1 -- the prefix boundary, for the
// quantization reason above. 0 when even the bare white ground cannot clear
// the floor, which only a state the density clamp has not yet fixed can reach.
inline int maxPaperStrengthPct(int inkIdx, int paperIdx, int densityPct) {
  int last = 0;
  for (int pct = 0; pct <= kPaperStrengthMax; pct++) {
    if (contrastAtDensity(inkIdx, paperIdx, densityPct, pct) < kContrastFloor)
      break;
    last = pct;
  }
  return last;
}

// The clamp the paper slider and every stored strength go through.
inline int clampPaperStrengthPct(int inkIdx, int paperIdx, int densityPct,
                                 int paperStrengthPct) {
  const int ceiling = maxPaperStrengthPct(inkIdx, paperIdx, densityPct);
  if (paperStrengthPct < 0) return 0;
  if (paperStrengthPct > ceiling) return ceiling;
  return paperStrengthPct;
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
static_assert(kPapers[kPaperBrightWhite].tooth == 1.0f,
              "Bright White's tooth is the reference the sheet pass was "
              "calibrated on; moving it re-textures the shipped default");
static_assert(clampInkIndex(-1) == kInkStandard &&
                  clampInkIndex(kInkCount) == kInkStandard &&
                  clampPaperIndex(999) == kPaperBrightWhite,
              "unknown indices must fall back to the shipped rows");

}  // namespace lightink
