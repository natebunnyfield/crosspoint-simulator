#pragma once

// SCANLINES -- the raster structure of a monochrome CRT, for the DARK page.
//
// DOCTRINE (owner order 2026-08-22): dark mode is CRT emulation -- phosphors,
// gun mixes, fade persistence -- and its screen texture is now SCANLINES,
// replacing the mottled grain. Light mode is letterpress (src/Letterpress.h).
// Design, research and the succession over the 2026-08-18 "no scanlines"
// ruling: docs/letterpress-and-scanlines.md and docs/phosphor-grain.md.
//
// THE MODEL, in the order the physics happens:
//
//   - A scan line is the beam's spot dragged horizontally; the spot's vertical
//     profile is close to GAUSSIAN. A line is untouched at its centre and the
//     gap between lines is where the darkening lives.
//   - LINE PITCH IS TIED TO THE SOURCE RASTER: a scan line every N logical
//     page rows. In device pixels the base (N = 1) pitch is exactly the
//     panel's presentation scale (~2.39 on an iPhone, 2.0 on the 2x Mac app,
//     1.0 at 1:1 -- where the structure correctly self-attenuates toward a
//     uniform dimming, which is what a real tube looks like once its lines
//     cannot be resolved). Emulating a fixed ~500-line tube instead would lay
//     a SECOND, unrelated lattice over 792 content rows -- the ST-008 failure
//     class by construction. High-resolution monochrome page CRTs are the
//     honest fiction here (the Macintosh Portrait Display was a 640x870
//     monochrome raster tube).
//   - PITCH SIZE IS AN OWNER SETTING (owner order 2026-08-22, from build 126:
//     "scanlines need a sizing setting in ios settings"). It is offered as
//     MULTIPLES of the source-row pitch -- 1x, 1.5x, 2x, 3x -- never as
//     absolute pixels: a simple rational multiple of the lattice the panel
//     already resamples on repeats its phase every 1 or 2 source rows, so the
//     raster and the text rows keep a fixed relationship and no long-period
//     difference frequency can exist. An absolute pixel pitch would be a free
//     ratio against a per-device presentation scale, which is the rejected
//     fixed-tube design wearing a settings row.
//   - BLOOM: spot size grows with beam current, so bright content WIDENS the
//     lit part of its line and thins the gap. This is the hyperrealism most
//     fakes skip, and it is why the field is content-aware (`level`).
//     Structurally it can only darken LESS -- never lift.
//   - IRREGULARITY: each line sits fractionally off pitch and varies slightly
//     in thickness (scan geometry and focus are not perfect).
//   - The owner's "variable mottled noise" rides ON the structure: the same
//     low-frequency value-noise field the grain used modulates the line DEPTH,
//     so the raster goes blotchy the way a real screen's coating is uneven --
//     it is not a separate speckle layer.
//
// WHY NO MOIRE (the ST-008 lesson, applied to a periodic field): generated at
// OUTPUT size and drawn 1:1, like the grain -- and because the period is a
// non-integer number of device pixels, each device-pixel row takes the BOX
// INTEGRAL of the continuous profile over its extent (an erf pair per nearby
// line) rather than a point sample. Exact sampling has no long-period beat;
// the test pins per-period stability.
//
// WHY IT ONLY DARKENS. Same modulate contract as PhosphorGrain and
// Letterpress; the gap is a deficit against the line, and an additive pass is
// the page-flash bug class.
//
// ONE DIAL. The mottle depth is FOLDED into the intensity ladder
// (mottleDepthFor): blotchiness varies with how visible the structure is, and
// the reduced-settings ruling allows one row. 0 is bit-exact off. Persisted as
// the meaningful percent.
//
// Pure and clock-free; tests/scanlines_test.cpp is the only instrument.

#include <cmath>
#include <cstdint>

#include "GaussianLine.h"
#include "PhosphorGrain.h"  // hash3 / unitFromHash / valueNoise, all pure

namespace scanlines {

// INTENSITY IS A PERCENTAGE OF STANDARD. Offered rungs: 0 (off), 50 (subtle,
// the dark-mode default), 100 (standard), 150 (deep). Clamp leaves headroom.
constexpr int kIntensityOff = 0;
constexpr int kIntensityStandard = 100;
constexpr int kIntensityMax = 300;

// Gap depth at 100%, and its cap. CHOSEN like kRealisticSigma was: deep
// enough to read as a raster at arm's length, short of a shutter grille.
constexpr float kDepthAt100 = 0.40f;
constexpr float kDepthMax = 0.60f;

// PITCH SIZE, as a percent of the SOURCE-ROW pitch. 100 is one scan line per
// page row -- what shipped in build 126, so the default changes nothing. The
// offered rungs are the simple ratios only; see pitchFor().
constexpr int kSizeFine = 100;    // 1 line per source row  (~2.39 px on phone)
constexpr int kSizeMedium = 150;  // 1 per 1.5 rows         (~3.58 px)
constexpr int kSizeCoarse = 200;  // 1 per 2 rows           (~4.77 px)
constexpr int kSizeChunky = 300;  // 1 per 3 rows           (~7.16 px)
constexpr int kSizeMin = kSizeFine;
constexpr int kSizeMax = kSizeChunky;

// Range clamp, not a snap: the four rungs above are what Settings.app offers,
// while CROSSPOINT_SIM_SCANLINE_PITCH may name anything between them for a
// measurement run. Same shape as clampIntensity against its own ladder.
inline int clampSize(int percentOfRowPitch) {
  if (percentOfRowPitch < kSizeMin) return kSizeMin;
  if (percentOfRowPitch > kSizeMax) return kSizeMax;
  return percentOfRowPitch;
}

// THE SEAM: the caller measures the panel's source-row pitch in device pixels
// and asks for it at the owner's size. Params::pitchPx stays the one final
// device-pixel pitch -- the model has no second degree of freedom to keep in
// step, and the ladder has exactly one definition, here, where the test can
// reach it.
inline float pitchFor(float sourceRowPitchPx, int sizePercent) {
  if (sourceRowPitchPx <= 0.0f) return 0.0f;
  return sourceRowPitchPx * static_cast<float>(clampSize(sizePercent)) /
         static_cast<float>(kSizeFine);
}

// Beam spot sigma as a fraction of pitch at zero beam current (FWHM ~0.52 of
// the pitch), and how far full brightness widens it.
//
// A FRACTION OF PITCH, AT EVERY RUNG -- deliberately not retuned per rung.
// A real tube's spot scales with its raster: fewer lines over the same screen
// height means a proportionally fatter beam, or the tube would show gaps
// between its own lines. Holding the fraction constant is that physics, and it
// is what makes a 7.16 px pitch read as CHUNKY (3.7 px lit, 3.4 px dark) rather
// than as thin stripes with gaps. Measured on a flat dark ground: line
// peak-to-peak 69/255 at 1x, 77 at 1.5x, 79 at 2x, 81 at 3x -- the duty cycle
// is the same 52% at all four, only the scale changes.
constexpr float kSigmaFrac = 0.22f;
constexpr float kBloomGain = 0.8f;

// BLOOM STRENGTH, as a percent of that standard gain (owner order 2026-08-22:
// "add another ios app settings for selecting bloom values with scanlines").
// 100 is kBloomGain itself -- the shipped behaviour -- so the default changes
// nothing.
//
// A FRACTION OF PITCH, NOT PIXELS, and that is the whole reason it needs no
// per-rung retune: bloom widens sigma, sigma is kSigmaFrac * pitch, so the
// widening is proportionate at every size. A coarse raster's fatter lines
// bloom by proportionately more absolute pixels, which is what a real tube
// does -- the same beam current on a coarser raster covers more of the screen.
//
// 0 is BIT-EXACT off: the level term is the ONLY place `level` enters the
// model, so a zero gain makes the field content-independent rather than
// nearly so.
constexpr int kBloomOff = 0;
constexpr int kBloomSubtle = 50;
constexpr int kBloomStandard = 100;  // kBloomGain, the shipped value
constexpr int kBloomStrong = 200;
constexpr int kBloomExtreme = 400;
constexpr int kBloomMax = kBloomExtreme;

inline int clampBloom(int percent) {
  if (percent < kBloomOff) return kBloomOff;
  if (percent > kBloomMax) return kBloomMax;
  return percent;
}

inline float bloomGainFor(int percent) {
  return kBloomGain * static_cast<float>(clampBloom(percent)) /
         static_cast<float>(kBloomStandard);
}

// Per-line imperfection: phase offset as a fraction of pitch, thickness as a
// +/- fraction of sigma. Overridable in Params so the test can isolate the
// integrator's exactness from the intended irregularity.
constexpr float kPhaseJitterFrac = 0.06f;
constexpr float kThickJitter = 0.08f;

// The mottle's blotch count shares the grain's 2026-08-20 ruling: a texture
// property, not a taste dial. Depth is folded into the ladder below.
constexpr int kMottleCells = 5;
constexpr float kMottleDepthMax = 0.40f;

constexpr float kMinMultiplier = 0.05f;

// Conservative bound on the mean gap fraction (1 - mean transmission) over a
// period at depth 1, worst thickness jitter. Used to turn a palette's mean
// darkening budget (phosphorgrain::darkeningBudget * 0.8) into a depth cap.
constexpr float kMaxMeanGap = 0.50f;

inline int clampIntensity(int percent) {
  if (percent < kIntensityOff) return kIntensityOff;
  if (percent > kIntensityMax) return kIntensityMax;
  return percent;
}

inline float depthFor(int percent) {
  const float d = kDepthAt100 * static_cast<float>(clampIntensity(percent)) /
                  static_cast<float>(kIntensityStandard);
  return d > kDepthMax ? kDepthMax : d;
}

// The folded mottle: monotone in the dial, 0 at off (bit-exact), capped.
// 50 -> 0.15, 100 -> 0.30, 150 -> 0.40.
inline float mottleDepthFor(int percent) {
  const float m = 0.003f * static_cast<float>(clampIntensity(percent));
  return m > kMottleDepthMax ? kMottleDepthMax : m;
}

struct Params {
  int intensityPercent = kIntensityStandard;
  uint32_t seed = 0x5343414Eu;  // 'SCAN'
  // Device pixels per scan line = the panel's presentation scale.
  float pitchPx = 2.0f;
  // Blotch swing on the line depth, from mottleDepthFor(). Held here rather
  // than derived inside so the core is testable at more than one value.
  float mottleDepth = 0.0f;
  // How far full beam current widens the spot, from bloomGainFor(). Held as
  // the gain rather than the percent for the same reason mottleDepth is.
  float bloomGain = kBloomGain;
  // Largest MEAN darkening the page can take (0.8 * darkeningBudget of the
  // live pair). 1.0 means "no constraint".
  float budgetMeanDarkening = 1.0f;
  // Irregularity, overridable for tests; the shipped values are the constants.
  float phaseJitterFrac = kPhaseJitterFrac;
  float thickJitter = kThickJitter;
};

// The box-integrated Gaussian line, shared with the laid sheet's combs: one
// definition in src/GaussianLine.h, named here so the field below reads the way
// it always did. This header's interval runs down the raster.
using gaussline::lineIntegral;
using gaussline::phi;

// Transmission of device-pixel row y (covering [y, y+1)) BEFORE normalization:
// the box integral of every nearby line's profile. `level` is the composed
// content's brightness under this pixel, 0..1; it widens the spot (bloom).
//
// `sigmaScale` is the off-axis defocus (src/CornerDefocus.h), a second and
// independent widening of the same spot. It is a trailing defaulted argument
// of exactly 1.0f, and a multiply by 1.0f is bit-exact in IEEE arithmetic, so
// every caller from before defocus existed gets byte-identical numbers.
inline float rowTransmissionRaw(const Params &p, float y, float level,
                                float sigmaScale = 1.0f) {
  const float pitch = p.pitchPx;
  if (pitch <= 0.0f) return 1.0f;
  if (level < 0.0f) level = 0.0f;
  if (level > 1.0f) level = 1.0f;
  if (sigmaScale < 1.0f) sigmaScale = 1.0f;
  // THE SUMMATION WINDOW IS FIXED AT +/-2 LINES, at every sigma. That is the
  // historical behaviour and it is deliberately not widened for the defocus,
  // for two reasons that point the same way. It keeps the OFF path bit-exact
  // by construction rather than by arithmetic luck; and it is the treatment
  // BLOOM already gets, so a spot widened by beam current and a spot widened
  // by deflection are integrated identically instead of one of them silently
  // costing more. Measured: widening it with the scale cost +93 ms per dark
  // page turn (the window grows with the product of bloom and defocus, so at
  // Extreme bloom it reached 27 lines) and moved the corner's mean by under a
  // twentieth of a code value. docs/corner-defocus.md.
  const int i0 = static_cast<int>(std::floor(y / pitch)) - 2;
  float sum = 0.0f;
  for (int i = i0; i <= i0 + 4; ++i) {
    const uint32_t li = static_cast<uint32_t>(i + 0x10000);
    const float uPhase = phosphorgrain::unitFromHash(
        phosphorgrain::hash3(li, 0x50484153u, p.seed));
    const float uThick = phosphorgrain::unitFromHash(
        phosphorgrain::hash3(li, 0x5448434Bu, p.seed));
    const float c = (static_cast<float>(i) + 0.5f) * pitch +
                    (uPhase - 0.5f) * 2.0f * p.phaseJitterFrac * pitch;
    float sigma = kSigmaFrac * pitch *
                  (1.0f + (uThick - 0.5f) * 2.0f * p.thickJitter) *
                  (1.0f + p.bloomGain * level) * sigmaScale;
    if (sigma < 1e-4f) sigma = 1e-4f;
    sum += lineIntegral(y, y + 1.0f, c, sigma);
  }
  return sum;
}

// What an unjittered, unbloomed line transmits through the pixel row centred
// on it -- the normalizer that makes a line centre EXACTLY untouched.
inline float baseCenterTransmission(float pitchPx) {
  if (pitchPx <= 0.0f) return 1.0f;
  const float sigma = kSigmaFrac * pitchPx;
  float sum = 0.0f;
  for (int i = -2; i <= 2; ++i)
    sum += lineIntegral(-0.5f, 0.5f, static_cast<float>(i) * pitchPx, sigma);
  return sum > 1e-6f ? sum : 1.0f;
}

// Normalized transmission, 0..1: 1 at a base line centre, small mid-gap,
// pulled toward 1 everywhere by bloom.
//
// THE DEFOCUS DIVIDES OUT, AND THAT IS THE POINT. The period-mean of the raw
// sum is the area under one line's profile divided by the pitch, which is
// LINEAR in sigma -- so dividing by sigmaScale leaves the mean where it was and
// removes only the modulation. Defocus therefore SOFTENS the raster without
// changing how much light the page loses to it: a corner is blurrier, not
// brighter and not darker, the 7:1 budget is untouched, and there is no way for
// this to become the corner-is-lit bug. Without the division a wide spot's
// integral would simply grow and the corners would read as lifted.
inline float rowTransmission(const Params &p, float y, float level,
                             float sigmaScale = 1.0f) {
  if (sigmaScale < 1.0f) sigmaScale = 1.0f;
  const float t = rowTransmissionRaw(p, y, level, sigmaScale) /
                  (baseCenterTransmission(p.pitchPx) * sigmaScale);
  return t > 1.0f ? 1.0f : (t < 0.0f ? 0.0f : t);
}

// The effective gap depth after the palette's budget: mean darkening is at
// most depth * kMaxMeanGap, so the cap keeps the page's mean at or above the
// contrast floor structurally, the same shape as the grain's budgetSigma.
inline float effectiveDepth(const Params &p) {
  float d = depthFor(p.intensityPercent);
  const float budget = p.budgetMeanDarkening;
  if (budget < 1.0f && d * kMaxMeanGap > budget) d = budget / kMaxMeanGap;
  return d < 0.0f ? 0.0f : d;
}

// Fold the mottle and the transmission into the final modulate value. Split
// out so a caller may cache rowTransmission per (row, level bucket) -- the
// erf work is x-independent -- and still run the exact shipped math.
inline uint8_t combine(const Params &p, float transmission, int x, int y,
                       int w, int h) {
  float depth = effectiveDepth(p);
  if (p.mottleDepth > 0.0f && w > 0 && h > 0) {
    const float nx = (static_cast<float>(x) + 0.5f) / static_cast<float>(w);
    const float ny = (static_cast<float>(y) + 0.5f) / static_cast<float>(h);
    const float v = phosphorgrain::valueNoise(nx * kMottleCells,
                                              ny * kMottleCells,
                                              p.seed ^ 0x4D4F5454u);
    depth *= 1.0f + p.mottleDepth * (v * 2.0f - 1.0f);
    if (depth < 0.0f) depth = 0.0f;
    if (depth > 1.0f) depth = 1.0f;
  }
  float m = 1.0f - depth * (1.0f - transmission);
  if (m < kMinMultiplier) m = kMinMultiplier;
  if (m > 1.0f) m = 1.0f;
  return static_cast<uint8_t>(m * 255.0f + 0.5f);
}

// THE ANSWER: the 0..255 modulate value for one OUTPUT pixel. 255 is
// untouched; intensity 0 returns 255 everywhere, so OFF is bit-exact.
//
// sigmaScale is the off-axis defocus at this pixel, from
// cornerdefocus::sigmaScaleAt. Defaulted to 1.0f -- the on-axis spot -- so a
// caller that does not model defocus is unchanged.
inline uint8_t multiplierAt(const Params &p, int x, int y, int w, int h,
                            float level, float sigmaScale = 1.0f) {
  if (clampIntensity(p.intensityPercent) == kIntensityOff || w <= 0 || h <= 0 ||
      p.pitchPx <= 0.0f)
    return 255;
  return combine(p, rowTransmission(p, static_cast<float>(y), level, sigmaScale),
                 x, y, w, h);
}

}  // namespace scanlines
