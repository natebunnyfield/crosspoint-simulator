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
// WHY IT IS APPLIED AT PRESENT TIME, IN DEVICE PIXELS. The panel is MINIFIED on
// a phone (0.7955 on an iPhone Air at 3x). A regular pattern baked into the
// framebuffer beats against that resample -- measured at 8.14 levels for the
// selection dither, ST-008. Grain generated at output resolution and drawn 1:1
// cannot beat against anything, because nothing resamples it.
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

// GRAIN CELL SIZE IN DEVICE PIXELS. Not 1, and the reason is acuity rather than
// cost: a single phosphor crystal subtends far below what an eye can resolve at
// any sane viewing distance, so what you actually see on a real tube is the
// AGGREGATE at the finest scale you can resolve -- not the grains. On a ~460ppi
// phone a 2px cell is about 0.11 mm, which is where that aggregate lands. A 1px
// cell renders as a uniform slight dimming, which is exactly the flatness this
// is here to fix.
constexpr int kCellPx = 2;

// How many blotches across the long edge, for the mottled coverages.
constexpr int kMottleCells = 8;
// Peak amplitude swing the mottle applies to the grain, +/- this fraction.
constexpr float kMottleDepth = 0.70f;
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
inline float sigmaFor(int strengthPercent) {
  return kRealisticSigma *
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
    const float v = valueNoise(nx * static_cast<float>(kMottleCells),
                               ny * static_cast<float>(kMottleCells),
                               p.seed ^ 0x4D4F5454u);
    out.amplitudeGain *= 1.0f + kMottleDepth * (v * 2.0f - 1.0f);
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

  float sigma = sigmaFor(strength) * cov.amplitudeGain;
  if (sigma > kMaxEffectiveSigma) sigma = kMaxEffectiveSigma;
  float m = 1.0f - z * sigma - cov.dim;
  if (m < kMinMultiplier) m = kMinMultiplier;
  if (m > 1.0f) m = 1.0f;
  return static_cast<uint8_t>(m * 255.0f + 0.5f);
}

}  // namespace phosphorgrain
