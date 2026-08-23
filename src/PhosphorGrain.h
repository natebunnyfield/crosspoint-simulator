#pragma once

// PHOSPHOR GRAIN -- the spatial texture a real screen has and a flat fill does
// not.
//
// WHY THIS EXISTS. The palette gets the phosphor's COLOUR right and the
// accumulator gets its DECAY right, and the page still reads as flat, because
// the one thing left is that a real tube has no uniform areas at all. Its
// screen is a settled layer of phosphor CRYSTALS a few microns across, laid
// down out of suspension; coverage varies from spot to spot, so emission
// varies with it. That variation is what your eye reads as "a screen" rather
// than "a fill".
//
// WHY IT ONLY DARKENS. Coverage variation is a deficit against an ideal, fully
// covered screen: a thin spot emits LESS light, it does not emit more. So the
// model here is a multiplier in (0, 1] and the composite is a plain modulate.
// That is not only the physics, it is the bug class this repo has already paid
// for twice -- the page-turn flash and the grey-background report were both an
// ADDITIVE pass lifting pixels the page had left dark. A multiplier cannot do
// that: where there is no light, grain has nothing to take away, so the ground
// stays exactly the ground.
//
// WHY IT IS APPLIED AT PRESENT TIME, IN DEVICE PIXELS, OVER THE WHOLE SURFACE.
// The panel is MINIFIED on a phone (0.7955 on an iPhone Air at 3x). A regular
// pattern baked into the framebuffer beats against that resample -- measured at
// 8.14 levels for the selection dither, ST-008. Grain generated at output
// resolution and drawn 1:1 cannot beat against anything, because nothing
// resamples it. It covers the app's whole surface, not just the page: one sheet
// of glass over the panel, the pad and the bezel alike (owner 2026-08-18).
//
// WHY NO BLOOM AND NO SCANLINES. Owner ruling 2026-08-18: halation/glow/bloom
// spreads light across glyph edges and costs legibility, and scanlines are a
// RASTER artifact rather than a phosphor one (a vector scope and a radar PPI
// have grain and no scanlines at all). Grain is the one treatment that is both
// a property of the phosphor itself and legibility-neutral -- it modulates how
// much light a patch emits, never where that light lands.
//
// Pure and clock-free on purpose, like PanelPalette and PadPalette: every
// failure mode here is a wrong PICTURE, which no compiler and no other test in
// this repo can see. tests/phosphor_grain_test.cpp is the only thing that can.

#include <cstdint>

#include "ContrastFloor.h"

namespace phosphorgrain {

// HOW THE GRAIN IS SPREAD ACROSS THE SCREEN. Amplitude is modulated spatially;
// these are the shapes it is modulated by. Persisted as INTEGERS by the iOS
// Settings app, so rows APPEND and never insert.
enum Coverage : int {
  // Uniform. The default: a screen coated evenly, and the safe answer for the
  // non-phosphor presets that also pass through here.
  Even = 0,
  // Grain rises toward the rim and the corners dim slightly. Both halves are
  // real: a settled coating thins at the edge of the plate, and the beam
  // reaches a corner at an angle and over a longer throw, so corner brightness
  // on a real tube runs 70-85% of center. The middle of the page -- the part
  // being read -- is left at the even amplitude.
  Vignette = 1,
  // Low-frequency blotches. Deposition mottle: the suspension does not settle
  // perfectly flat, so coverage wanders over centimetres as well as microns.
  // This is the one that most kills "flat", because the eye reads large-scale
  // unevenness as a physical surface.
  Mottled = 2,
  // Both.
  VignetteMottled = 3,
  kCoverageCount = 4
};

// STRENGTH IS A PERCENTAGE OF REALISTIC, and the owner asked for 0x to 10x.
constexpr int kStrengthOff = 0;
constexpr int kStrengthRealistic = 100;
constexpr int kStrengthMax = 1000;

// The RMS emission variation a realistic screen gets, as a fraction.
//
// SAY WHAT THIS IS: it is CHOSEN, not measured. Published phosphor-screen specs
// give particle size (a few microns) and coating weight, not a granularity RMS
// at viewing distance, and this repo has no tube to photograph. 3.5% is the
// value that is visible as texture on an OLED at arm's length without moving
// the mean luminance enough to matter (mean attenuation 0.8*sigma = 2.8%, and
// the page keeps its contrast ratio to within a rounding step). Treat it as a
// taste anchor with a physical justification, not as a measurement.
constexpr float kRealisticSigma = 0.035f;

// GRAIN CELL SIZE IN DEVICE PIXELS. One, by owner ruling 2026-08-19 after
// looking at 1/2/3/4/6 rendered side by side at the shipped settings.
//
// THIS OVERTURNS WHAT THIS COMMENT USED TO SAY, and the old claim is worth
// keeping visible because it was wrong in a checkable way. It argued for 2 on
// acuity grounds -- a single crystal subtends far below what an eye resolves,
// so what you see is the aggregate at the finest resolvable scale -- and then
// asserted that "a 1px cell renders as a uniform slight dimming, which is
// exactly the flatness this is here to fix."
//
// Measured, it is the opposite. Pixel-to-pixel difference on the White page:
//
//   cell   1      2      3      4      6
//   adj    2.32   1.15   0.77   0.58   0.40
//
// 1px has the MOST per-pixel variation, not the least; the aggregate argument
// was about what the eye integrates, and the eye integrating a field is not the
// same as the field being flat. The reasoning was plausible and the render
// disagreed, so the render wins.
constexpr int kCellPx = 1;

// THE MOTTLE, and both halves of it are now owner-set rather than constants.
//
// How many blotches across the long edge, and how hard they swing the grain's
// amplitude (+/- this fraction). Build 98 hardcoded 8 and 0.70; measuring that
// against the alternatives showed the cell count barely registers while the
// depth is the whole effect, and that 0.70 is far more swing than the page
// wants -- so the offered depths are an order of magnitude below it. Owner
// ruling 2026-08-18: cells 8/16/32, depth 0/0.03/0.1/0.3.
//
// Depth 0 is exact: it makes a Mottled coverage render byte-for-byte as Even.
// 5, owner ruling 2026-08-20, and no longer settable -- the picker row went
// with it. The count is a texture property rather than a taste one: it decides
// the SIZE of the blotches relative to the page, and a reader who moves it is
// changing how big the paper's fibres look, which is not a question anyone
// wanted asked twice.
constexpr int kMottleCellsDefault = 5;
constexpr float kMottleDepthDefault = 0.90f;  // owner ruling 2026-08-20
constexpr int kMottleCellsMin = 2;
constexpr int kMottleCellsMax = 256;
constexpr float kMottleDepthMax = 1.0f;

inline int clampMottleCells(int cells) {
  if (cells < kMottleCellsMin) return kMottleCellsMin;
  if (cells > kMottleCellsMax) return kMottleCellsMax;
  return cells;
}
inline float clampMottleDepth(float depth) {
  if (!(depth > 0.0f)) return 0.0f;   // also catches NaN
  if (depth > kMottleDepthMax) return kMottleDepthMax;
  return depth;
}
// Corner grain amplitude as a multiple of center, under Vignette.
constexpr float kVignetteGain = 3.0f;
// Corner DIMMING at 1x, and the cap it saturates to as strength is raised. 0.10
// puts the corner at 90% of center, deliberately short of the 70-85% real tubes
// measure: this is a page of text, not a monitor test card. The cap is 0.30 --
// 70% of center, the BOTTOM of that measured range -- so even the 10x setting
// stops where a real tube stops rather than running the corner to black.
constexpr float kVignetteDim = 0.10f;
constexpr float kVignetteDimMax = 0.30f;

// Ceiling on the effective sigma after the coverage gain has been applied.
//
// Without it the two dials MULTIPLY and the extremes stop being a look: at 10x
// under Vignette the corner sees sigma 1.05, every texel there clamps to
// kMinMultiplier, and the page loses its corners entirely. 0.45 is where the
// half-normal still leaves a corner readable while being unmistakably grainy.
constexpr float kMaxEffectiveSigma = 0.45f;

// Never take a texel all the way out. A zero multiplier is a dead pixel, which
// is a defect rather than grain, and at 10x the tail would produce a scatter of
// them.
constexpr float kMinMultiplier = 0.05f;

// Truncation of the normal, in sigmas. Bounded exactly by construction below.
constexpr float kSigmaClamp = 3.0f;

// --- PER-PALETTE AMPLITUDE ------------------------------------------------
//
// A LOW-CONTRAST PAGE CANNOT AFFORD TEXTURE, and a high-contrast one can carry
// a lot. Owner ruling 2026-08-18, after noticing the grain was NOT
// phosphor-specific when he expected it to be. It is also the better physics:
// phosphors differ in particle size and coating weight, so one field for all
// 52 palettes was the simplification, not the accurate answer.
//
// The budget is measured, not guessed: for a given ink/paper pair, how large a
// sigma the page can take before its MEAN attenuation drags contrast down to
// the floor this repo holds named presets to. Measured across the shortlist it
// spans 7.2% (P11 Blue, already at 7.4:1) to 71.9% (P4 Gray at 13.9:1) -- a
// tenfold spread that one constant cannot represent.
//
// Pure, and deliberately expressed in LUMINANCES rather than palettes: this
// header knows nothing about PanelPalette and must not start to.
constexpr float kContrastFloor = static_cast<float>(wcag::kContrastFloorAAA);

// The budget's reference point, and the two clamps around it.
//
// kReferenceBudget is the median across the shortlisted phosphors, so a typical
// page still gets kRealisticSigma at 1x and the setting keeps meaning what it
// said. The clamps stop the extremes running away: without kMaxScale a
// 13.9:1 page would take twenty times the coating of the reference, and
// without kMinScale P11 Blue would land near 0.5% and read as "grain is broken
// on blue" rather than "blue is a page with no room for it".
constexpr float kReferenceBudget = 0.54f;
constexpr float kMinAmplitudeScale = 0.35f;
constexpr float kMaxAmplitudeScale = 1.60f;

// Contrast after a uniform multiply. Both tones scale, so the ratio walks
// toward 1 rather than holding -- which is why darkening costs contrast at all.
inline float contrastAfter(float inkLum, float paperLum, float m) {
  const float a = inkLum * m + 0.05f;
  const float b = paperLum * m + 0.05f;
  return a > b ? a / b : b / a;
}

// The largest sigma this pair can take before its mean attenuation (0.8*sigma,
// the half-normal's mean) brings contrast to the floor. 0 when the pair is
// already at or under it -- a page that starts below the floor gets no grain
// budget at all rather than a negative one.
inline float darkeningBudget(float inkLum, float paperLum) {
  if (contrastAfter(inkLum, paperLum, 1.0f) <= kContrastFloor) return 0.0f;
  float lo = 0.0f, hi = 1.0f;              // m, the surviving multiplier
  for (int i = 0; i < 40; i++) {
    const float mid = (lo + hi) * 0.5f;
    if (contrastAfter(inkLum, paperLum, mid) >= kContrastFloor) hi = mid;
    else lo = mid;
  }
  return (1.0f - hi) / 0.8f;
}

// What multiplies kRealisticSigma for this page. 1.0 is the reference page.
inline float amplitudeScaleFor(float inkLum, float paperLum) {
  const float scale = darkeningBudget(inkLum, paperLum) / kReferenceBudget;
  if (!(scale > kMinAmplitudeScale)) return kMinAmplitudeScale;  // also NaN
  if (scale > kMaxAmplitudeScale) return kMaxAmplitudeScale;
  return scale;
}

inline int clampStrength(int strengthPercent) {
  if (strengthPercent < kStrengthOff) return kStrengthOff;
  if (strengthPercent > kStrengthMax) return kStrengthMax;
  return strengthPercent;
}

inline Coverage clampCoverage(int coverage) {
  if (coverage < 0 || coverage >= kCoverageCount) return Even;
  return static_cast<Coverage>(coverage);
}

// The RMS emission variation for a given strength. Linear in the dial, so "2x"
// means twice the texture and 0 means none.
inline float sigmaFor(int strengthPercent, float amplitudeScale = 1.0f) {
  return kRealisticSigma * amplitudeScale *
         (static_cast<float>(clampStrength(strengthPercent)) /
          static_cast<float>(kStrengthRealistic));
}

// Integer hash. Deterministic across runs and platforms (unsigned wraparound
// only, no floats) because the grain is a property of the SCREEN: it must not
// crawl from frame to frame. Animated noise is beam-current noise, a different
// phenomenon, and it would flicker a page that is meant to sit still.
inline uint32_t hash3(uint32_t x, uint32_t y, uint32_t salt) {
  uint32_t h = x * 0x8DA6B343u ^ y * 0xD8163841u ^ salt * 0xCB1AB31Fu;
  h ^= h >> 15;
  h *= 0x2C1B3C6Du;
  h ^= h >> 12;
  h *= 0x297A2D39u;
  h ^= h >> 15;
  return h;
}

inline float unitFromHash(uint32_t h) {
  return static_cast<float>(h & 0xFFFFFFu) / static_cast<float>(0x1000000u);
}

// Approximately normal, EXACTLY bounded to [-3, +3], unit variance.
// Irwin-Hall with n = 3: the sum of three uniforms has variance 3/12 = 1/4, so
// sigma is 1/2 and the range is +/-1.5; scaling by 2 gives sigma 1 and the
// clamp falls out of the construction rather than being applied afterwards.
inline float gaussFrom(uint32_t x, uint32_t y, uint32_t salt) {
  const float u0 = unitFromHash(hash3(x, y, salt));
  const float u1 = unitFromHash(hash3(x, y, salt ^ 0x9E3779B9u));
  const float u2 = unitFromHash(hash3(x, y, salt ^ 0x85EBCA6Bu));
  return (u0 + u1 + u2 - 1.5f) * 2.0f;
}

// Smooth value noise on a coarse lattice, in [0, 1]. Used for the mottle.
inline float valueNoise(float cx, float cy, uint32_t salt) {
  const int x0 = static_cast<int>(cx < 0.0f ? cx - 1.0f : cx);
  const int y0 = static_cast<int>(cy < 0.0f ? cy - 1.0f : cy);
  const float fx = cx - static_cast<float>(x0);
  const float fy = cy - static_cast<float>(y0);
  const float sx = fx * fx * (3.0f - 2.0f * fx);
  const float sy = fy * fy * (3.0f - 2.0f * fy);
  auto at = [&](int ix, int iy) {
    return unitFromHash(hash3(static_cast<uint32_t>(ix + 4096),
                              static_cast<uint32_t>(iy + 4096), salt));
  };
  const float a = at(x0, y0), b = at(x0 + 1, y0);
  const float c = at(x0, y0 + 1), d = at(x0 + 1, y0 + 1);
  const float top = a + (b - a) * sx;
  const float bot = c + (d - c) * sx;
  return top + (bot - top) * sy;
}

struct Params {
  int strengthPercent = kStrengthRealistic;
  Coverage coverage = Even;
  uint32_t seed = 0x43524F53u;  // 'CROS'
  // Only read when the coverage includes mottle. Held here rather than as file
  // constants because they are settings now, and because a pure function that
  // reads globals cannot be tested at more than one setting.
  int mottleCells = kMottleCellsDefault;
  float mottleDepth = kMottleDepthDefault;
  // What this page can afford, from amplitudeScaleFor(). 1.0 is the reference
  // page; the default keeps a caller that does not set it on the old behavior.
  float amplitudeScale = 1.0f;
  // ...and the HARD ceiling from darkeningBudget(), which is what actually
  // makes the floor guarantee structural. The scale alone is not enough: a
  // Vignette multiplies sigma by up to kVignetteGain at the rim, and 3x on a
  // page with almost no room takes it under the floor anyway. 1.0 means "no
  // constraint", for a caller that does not know the palette.
  float budgetSigma = 1.0f;
};

// How much the grain amplitude is scaled at this point on the screen, and how
// much the screen is dimmed there. nx/ny run 0..1 across the panel.
struct CoverageAt {
  float amplitudeGain;  // multiplies sigma
  float dim;            // 0..1, subtracted from the multiplier
};

inline CoverageAt coverageAt(const Params &p, float nx, float ny) {
  CoverageAt out{1.0f, 0.0f};
  const Coverage cov = clampCoverage(p.coverage);
  const bool vignette = cov == Vignette || cov == VignetteMottled;
  const bool mottle = cov == Mottled || cov == VignetteMottled;
  if (vignette) {
    // r = 0 at center, 1 at a corner.
    const float dx = (nx - 0.5f) * 2.0f;
    const float dy = (ny - 0.5f) * 2.0f;
    float r2 = (dx * dx + dy * dy) * 0.5f;
    if (r2 > 1.0f) r2 = 1.0f;
    out.amplitudeGain *= 1.0f + (kVignetteGain - 1.0f) * r2;
    float dim = kVignetteDim * (static_cast<float>(clampStrength(p.strengthPercent)) /
                                static_cast<float>(kStrengthRealistic));
    if (dim > kVignetteDimMax) dim = kVignetteDimMax;
    out.dim = dim * r2;
  }
  if (mottle) {
    const float depth = clampMottleDepth(p.mottleDepth);
    if (depth > 0.0f) {
      const float cells = static_cast<float>(clampMottleCells(p.mottleCells));
      const float v = valueNoise(nx * cells, ny * cells, p.seed ^ 0x4D4F5454u);
      out.amplitudeGain *= 1.0f + depth * (v * 2.0f - 1.0f);
    }
  }
  return out;
}

// THE ANSWER: the 0..255 modulate value for one output pixel of the panel.
// 255 is "this texel is untouched"; strength 0 returns 255 everywhere, so OFF
// is a bit-exact no-op rather than an almost-no-op.
inline uint8_t multiplierAt(const Params &p, int x, int y, int w, int h) {
  const int strength = clampStrength(p.strengthPercent);
  if (strength == kStrengthOff || w <= 0 || h <= 0) return 255;

  const float nx = (static_cast<float>(x) + 0.5f) / static_cast<float>(w);
  const float ny = (static_cast<float>(y) + 0.5f) / static_cast<float>(h);
  const CoverageAt cov = coverageAt(p, nx, ny);

  const uint32_t cx = static_cast<uint32_t>(x / kCellPx);
  const uint32_t cy = static_cast<uint32_t>(y / kCellPx);
  // Half-normal: coverage is a deficit, so only the magnitude is used.
  float z = gaussFrom(cx, cy, p.seed);
  if (z < 0.0f) z = -z;

  float sigma = sigmaFor(strength, p.amplitudeScale) * cov.amplitudeGain;
  if (sigma > kMaxEffectiveSigma) sigma = kMaxEffectiveSigma;
  // The page's own ceiling, applied AFTER the coverage gain -- that ordering is
  // the whole point, since the gain is what breaches it.
  if (p.budgetSigma > 0.0f && sigma > p.budgetSigma) sigma = p.budgetSigma;
  float m = 1.0f - z * sigma - cov.dim;
  if (m < kMinMultiplier) m = kMinMultiplier;
  if (m > 1.0f) m = 1.0f;
  return static_cast<uint8_t>(m * 255.0f + 0.5f);
}

}  // namespace phosphorgrain
