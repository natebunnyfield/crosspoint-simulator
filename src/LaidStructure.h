#pragma once

// LAID STRUCTURE -- chain and laid lines for a laid PAPER stock, on the LIGHT
// page (doctrine 2026-08-22: light mode is paper-and-ink emulation).
//
// A hand mould's cover is a screen of closely spaced LAID wires with sparse
// perpendicular CHAIN wires stitching them to the mould's ribs, and the sheet
// records both: less pulp settles over every wire, so the paper is thinner --
// and reads darker in the furrow -- along each line. The measured geometry
// (Heritage Science 11 (2023), averages from van Staalduinen et al. 2006;
// docs/paper-colorimetry-sources.md section 3c):
//
//   - LAID lines: 5-15 per cm, typically ~1 mm pitch.
//   - CHAIN lines: 26-39 mm apart on measured pages (15-50 mm quoted range),
//     perpendicular to the laids, and DARKER -- they sit on top of the laid
//     wires and leave a larger imprint, "described as a shadow".
//   - ANTIQUE laid adds a soft dark STRIP along each chain line: before the
//     early 1800s the chain wires were attached directly to the wooden ribs,
//     which sucked extra pulp onto the rib line.
//
// WHERE IT OPERATES, and why: OUTPUT size, drawn 1:1, folded into the sheet
// field -- never into the panel framebuffer. At ~1.9 px the laid pitch is a
// regular lattice squarely in ST-008 territory: written into the framebuffer
// it would beat against the phone's fractional minification. Same cure as
// src/Scanlines.h, copied deliberately: each output row/column takes the BOX
// INTEGRAL of the continuous line profile over its own extent (an erf pair
// per nearby line), so exact sampling leaves no long-period beat, and where
// the pitch cannot be resolved the structure self-attenuates toward a uniform
// faint toning -- which is what an unresolvable laid sheet actually looks
// like.
//
// WHY IT ONLY DARKENS. Same modulate contract as PhosphorGrain, Letterpress
// and Scanlines: a furrow is less pulp over the wire, a deficit; an additive
// pass is the page-flash bug class.
//
// WHOSE DIAL IT IS: the PAPER's, not a new setting. The field applies only
// when the selected stock carries lightink::Paper::laid (Laid Antique today;
// a future laid row inherits the flag), and it rides the paper-strength
// slider the way tooth and formation do, so dialing the stock away takes its
// wires with it. CROSSPOINT_SIM_LAIDLINES is the desktop/env override, the
// letterpress idiom.
//
// PER-PAGE DETERMINISM: the seed is pageSheetSeed() -- the page's identity --
// so page 47 is the same sheet forever, and each line's phase jitter hashes
// off that seed, so sheet-to-sheet the wire positions differ the way two
// sheets from one mould stack do not quite register.
//
// Pure and clock-free; tests/laid_structure_test.cpp is the only instrument.

#include <cmath>
#include <cstdint>

#include "PhosphorGrain.h"  // hash3 / unitFromHash, pure

namespace laidstructure {

// STRENGTH IS A PERCENTAGE OF STANDARD, the letterpress ladder shape. The
// paper slider maps 0..100 straight onto it; the clamp leaves headroom for a
// measurement run. 0 is bit-exact off.
constexpr int kStrengthOff = 0;
constexpr int kStrengthStandard = 100;
constexpr int kStrengthMax = 400;

// The measured geometry, in millimeters on the sheet.
constexpr float kLaidPitchMm = 1.0f;    // 5-15 lines/cm measured; ~1 mm typical
constexpr float kChainPitchMm = 32.0f;  // middle of the measured 26-39 mm
constexpr float kChainSigmaMm = 0.7f;   // the chain wire's shadow width
constexpr float kStripSigmaMm = 4.0f;   // the antique rib strip, wide and soft

// mm -> SOURCE-LOGICAL panel px. NO physical panel dimension exists anywhere
// in this repo (BoardConfig.h carries geometry in pixels only), so this is a
// stated ASSUMPTION, held in exactly one named constant: the research pass
// (docs/paper-colorimetry-sources.md section 3c) read the 528x792 logical
// sheet as a folio-scale handmade sheet at 1.85 px/mm, which puts the laid
// pitch at ~1.9 logical px -- the ST-008 figure the placement argument above
// is built on. If a real panel-size constant ever lands, it replaces this one
// line.
constexpr float kPxPerMmSource = 1.85f;

// Depths at 100%, as darkening fractions of the paper's light. CHOSEN like
// every letterpress amplitude -- no sheet was photographed for this repo --
// but the ORDERING is the measured claim: chains darker than laids, the strip
// softer than either.
constexpr float kDepthAt100 = 0.045f;     // laid furrow, at line center
constexpr float kDepthMax = 0.10f;
constexpr float kChainDepthRatio = 1.8f;  // chain line, relative to laid
constexpr float kStripDepthRatio = 0.5f;  // antique strip, relative to laid

// The laid profile's spread as a fraction of ITS pitch (the furrows tile the
// sheet); the chain and strip spreads are physical widths in mm, because a
// wire's shadow does not grow with the 32 mm between wires.
constexpr float kLaidSigmaFrac = 0.30f;

// Per-line phase jitter, as a fraction of the line's own pitch. Overridable
// in Params so the test can isolate the integrator's exactness.
constexpr float kPhaseJitterFrac = 0.10f;

// Same floor as letterpress: structure, not a defect.
constexpr float kMinMultiplier = 0.25f;

// Conservative bound on the mean of the composite normalized field (laid +
// chain + strip, in units where a laid line center is 1). The laid comb's own
// mean is sigma*sqrt(2pi)/pitch ~ 0.75 of peak (the overlap that makes the
// unresolvable case a faint even toning), the chain and strip combs add
// ~0.26; measured composite means sit under 1.05 at every offered pitch and
// the test pins that they stay under THIS figure, which is what turns a
// paper budget into a depth cap the same way scanlines::kMaxMeanGap does.
constexpr float kMeanFieldBound = 1.15f;

inline int clampStrength(int percent) {
  if (percent < kStrengthOff) return kStrengthOff;
  if (percent > kStrengthMax) return kStrengthMax;
  return percent;
}

struct Params {
  int strengthPercent = kStrengthStandard;
  uint32_t seed = 0x4C414944u;  // 'LAID'
  // OUTPUT pixels per SOURCE-LOGICAL panel pixel -- the presentation scale
  // with the render scale divided out, the same quantity the scanlines pass
  // measures for its base pitch. 1.0 is the desktop's device-exact window.
  float outPxPerSourcePx = 1.0f;
  // Largest MEAN darkening this field may put on the paper (what the sheet's
  // tooth left of the palette's budget, shared with the defect layer). 1.0
  // means "no constraint".
  float budgetMeanDarkening = 1.0f;
  // Overridable for tests; the shipped value is the constant.
  float phaseJitterFrac = kPhaseJitterFrac;
};

inline float laidPitchPx(const Params &p) {
  return kLaidPitchMm * kPxPerMmSource * p.outPxPerSourcePx;
}
inline float chainPitchPx(const Params &p) {
  return kChainPitchMm * kPxPerMmSource * p.outPxPerSourcePx;
}

inline float depthFor(int percent) {
  const float d = kDepthAt100 * static_cast<float>(clampStrength(percent)) /
                  static_cast<float>(kStrengthStandard);
  return d > kDepthMax ? kDepthMax : d;
}

// The palette's budget as a depth cap: mean darkening is at most
// depth * kMeanFieldBound, so capping the depth there keeps the flat sheet's
// mean at or above the floor structurally -- scanlines' effectiveDepth shape.
inline float effectiveDepth(const Params &p) {
  float d = depthFor(p.strengthPercent);
  const float budget = p.budgetMeanDarkening;
  if (budget < 1.0f && d * kMeanFieldBound > budget) d = budget / kMeanFieldBound;
  return d < 0.0f ? 0.0f : d;
}

// What this field will spend of the paper budget, for the layer AFTER it (the
// defect pass): its depth cap times the mean-field bound. 0 when off, so a
// build with no laid stock selected leaves the defect budget byte-identical.
inline float meanDarkeningBound(const Params &p) {
  if (clampStrength(p.strengthPercent) == kStrengthOff) return 0.0f;
  return effectiveDepth(p) * kMeanFieldBound;
}

inline float phi(float z) { return 0.5f * (1.0f + std::erf(z * 0.70710678f)); }

// Integral over [v0, v1] of a peak-1 Gaussian centered at c with spread sigma.
inline float lineIntegral(float v0, float v1, float c, float sigma) {
  return sigma * 2.50662827f * (phi((v1 - c) / sigma) - phi((v0 - c) / sigma));
}

// Box integral over pixel [v, v+1) of a jittered comb of peak-1 Gaussians:
// pitch apart, each line's center offset by its own hashed jitter plus a
// whole-sheet phase from the page seed. `lane` separates the laid comb from
// the chain comb in hash space.
inline float combBoxIntegral(float pitch, float sigma, float v, uint32_t seed,
                             uint32_t lane, float jitterFrac) {
  if (pitch <= 0.0f || sigma <= 0.0f) return 0.0f;
  const float pagePhase =
      (phosphorgrain::unitFromHash(
           phosphorgrain::hash3(seed, lane, 0x50484153u)) -  // 'PHAS'
       0.5f) *
      pitch;
  const int i0 = static_cast<int>(std::floor((v - pagePhase) / pitch)) - 3;
  float sum = 0.0f;
  for (int i = i0; i <= i0 + 6; ++i) {
    const uint32_t li = static_cast<uint32_t>(i + 0x10000);
    const float uJit =
        phosphorgrain::unitFromHash(phosphorgrain::hash3(li, lane, seed));
    const float c = (static_cast<float>(i) + 0.5f) * pitch + pagePhase +
                    (uJit - 0.5f) * 2.0f * jitterFrac * pitch;
    sum += lineIntegral(v, v + 1.0f, c, sigma);
  }
  return sum;
}

// The comb's value through the pixel row centered on an unjittered line -- the
// normalizer that makes a line center read EXACTLY its nominal depth
// (scanlines' baseCenterTransmission, same purpose).
inline float combPeak(float pitch, float sigma) {
  if (pitch <= 0.0f || sigma <= 0.0f) return 1.0f;
  float sum = 0.0f;
  for (int i = -3; i <= 3; ++i)
    sum += lineIntegral(-0.5f, 0.5f, static_cast<float>(i) * pitch, sigma);
  return sum > 1e-6f ? sum : 1.0f;
}

// Normalized LAID darkness for output row y: 1 at a laid line's center,
// less between lines, near-uniform ~0.75 when the pitch is unresolvable.
// x-independent, so a caller may cache it per row.
inline float rowLaidDarkness(const Params &p, float y) {
  const float pitch = laidPitchPx(p);
  const float sigma = kLaidSigmaFrac * pitch;
  const float d = combBoxIntegral(pitch, sigma, y, p.seed, 0x4C444C4Eu,  // 'LDLN'
                                  p.phaseJitterFrac) /
                  combPeak(pitch, sigma);
  return d > 1.0f ? 1.0f : (d < 0.0f ? 0.0f : d);
}

// Normalized CHAIN darkness for output column x, in laid-line units: the
// chain comb at kChainDepthRatio plus the antique strip at kStripDepthRatio,
// both centered on the same (jittered) chain positions. y-independent, so a
// caller may cache it per column.
inline float colChainDarkness(const Params &p, float x) {
  const float pitch = chainPitchPx(p);
  const float mmPx = kPxPerMmSource * p.outPxPerSourcePx;
  const float chainSigma = kChainSigmaMm * mmPx;
  const float stripSigma = kStripSigmaMm * mmPx;
  const uint32_t lane = 0x43484C4Eu;  // 'CHLN' -- one lane: strip rides the
                                      // chain's own jittered centers
  const float chain =
      combBoxIntegral(pitch, chainSigma, x, p.seed, lane, p.phaseJitterFrac) /
      combPeak(pitch, chainSigma);
  const float strip =
      combBoxIntegral(pitch, stripSigma, x, p.seed, lane, p.phaseJitterFrac) /
      combPeak(pitch, stripSigma);
  float d = kChainDepthRatio * chain + kStripDepthRatio * strip;
  const float cap = kChainDepthRatio + kStripDepthRatio;
  return d > cap ? cap : (d < 0.0f ? 0.0f : d);
}

// Fold the two axes into the final modulate value -- split out so a caller
// may cache rowLaidDarkness per row and colChainDarkness per column and still
// run the exact shipped math; the test pins combine(row, col) == multiplierAt.
inline uint8_t combine(const Params &p, float rowDark, float colDark) {
  const float depth = effectiveDepth(p);
  float m = 1.0f - depth * (rowDark + colDark);
  if (m < kMinMultiplier) m = kMinMultiplier;
  if (m > 1.0f) m = 1.0f;
  return static_cast<uint8_t>(m * 255.0f + 0.5f);
}

// THE ANSWER: the 0..255 modulate value for one OUTPUT pixel. 255 is
// untouched; strength 0 returns 255 everywhere, so OFF is bit-exact.
inline uint8_t multiplierAt(const Params &p, int x, int y) {
  if (clampStrength(p.strengthPercent) == kStrengthOff ||
      p.outPxPerSourcePx <= 0.0f)
    return 255;
  return combine(p, rowLaidDarkness(p, static_cast<float>(y)),
                 colChainDarkness(p, static_cast<float>(x)));
}

}  // namespace laidstructure
