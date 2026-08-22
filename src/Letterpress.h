#pragma once

// LETTERPRESS -- what pressed ink on paper looks like, for the LIGHT page.
//
// DOCTRINE (owner order 2026-08-22): light mode is paper-and-ink emulation
// with a letterpress experience; dark mode is CRT emulation. This header is
// the light half. The dark half is src/Scanlines.h. Design and research:
// docs/letterpress-and-scanlines.md.
//
// WHAT THE EYE SEES IN A LETTERPRESS PAGE, and which parts survive at this
// app's render scales (3x supersampled, presented at ~0.72-1.0):
//
//   - INK SQUEEZE. The press forces ink outward from under the face of the
//     type, so ink pools at the stroke's PERIMETER: a darker rim around every
//     glyph edge, the stroke's centre fractionally lighter. This is the
//     letterpress signature and the lead effect here.
//   - DEBOSS SHADOW. The type bites into the paper; under light from the
//     top-left (the UI convention) the depression's top-left wall is shadowed.
//     Rendered SHADOW-ONLY: the highlight half would need an additive pass,
//     which is the page-flash bug class, and near-white paper has no headroom
//     to lift anyway.
//   - PLATE PRESSURE. Impression is never even across a forme; a low-frequency
//     field over the page. Expressed as heavy areas darkening the ink -- the
//     representable half of the phenomenon.
//   - IN-STROKE IRREGULARITY and PAPER TOOTH. High-frequency, an order below
//     the ring: solid ink is not a fill and paper is not a fill. Aperiodic by
//     construction, so neither can beat against the fractional presentation
//     (the ST-008 moire needs a REGULAR lattice; noise has none).
//
// WHY IT ONLY DARKENS. Same contract as PhosphorGrain: the composite is a
// modulate, a multiplier in (0, 1]. Ink squeeze is more pigment, a deboss
// shadow is less light, pressure and tooth are density -- all deficits. An
// additive pass is the bug class this repo has shipped twice.
//
// WHERE IT OPERATES. Present time, PANEL space, off the framebuffer's own
// luminance edges -- it does not touch the glyph compose. Letterpress is a
// property of the PAGE, not the glass, so unlike the grain it covers the
// panel only: ink squash on the bezel would be as wrong as the grainy
// rectangle was in reverse. Content-locked and aperiodic, so scaling with the
// panel cannot moire.
//
// ONE DIAL. Ring and deboss scale linearly together -- they are the same
// physical variable, packing pressure -- and the paper's tooth rides at HALF
// proportion (sqrt of the dial): a harder press does not make the paper
// toothier. 0 is bit-exact off. Persisted as the meaningful percent.
//
// Pure and clock-free, like PhosphorGrain: every failure mode is a wrong
// PICTURE, and tests/letterpress_test.cpp is the only instrument that can see
// one.

#include <cmath>
#include <cstdint>

#include "PhosphorGrain.h"  // hash3 / unitFromHash / valueNoise, all pure

namespace letterpress {

// STRENGTH IS A PERCENTAGE OF STANDARD. Offered rungs: 0 (off), 50 (subtle,
// the light-mode default), 100 (standard), 200 (heavy). The clamp leaves
// headroom above the ladder, same shape as the grain's.
constexpr int kStrengthOff = 0;
constexpr int kStrengthStandard = 100;
constexpr int kStrengthMax = 400;

// The components at 100%, as darkening fractions. CHOSEN, not measured -- no
// press was photographed for this repo. The ring dominates by design; the
// noise terms sit an order below it so the page reads as printed, not dirty.
constexpr float kRingAt100 = 0.30f;    // ink-side rim, at a full edge
constexpr float kDebossAt100 = 0.15f;  // paper-side shadow, top-left walls
constexpr float kPressAt100 = 0.06f;   // low-frequency plate pressure, ink only
constexpr float kIrregularAt100 = 0.04f;  // in-stroke density, ink only
constexpr float kToothAt100 = 0.03f;   // paper tooth amplitude (rides sqrt)

// Blotches across the page long edge for the pressure field. A texture-scale
// property like the grain's mottle cells, not a taste dial.
constexpr int kPressCells = 4;

// Never take a texel out entirely; a black speck is a defect, not impression.
constexpr float kMinMultiplier = 0.25f;

// This repo's floor for a named preset. Same figure as phosphorgrain's.
constexpr float kContrastFloor = 7.0f;

inline int clampStrength(int strengthPercent) {
  if (strengthPercent < kStrengthOff) return kStrengthOff;
  if (strengthPercent > kStrengthMax) return kStrengthMax;
  return strengthPercent;
}

// --- THE PAPER'S BUDGET ----------------------------------------------------
//
// Letterpress darkens the INK side hard (which RAISES a light page's contrast)
// and the PAPER side only faintly (tooth) -- but a page already close to the
// floor cannot afford even faintly. Latte light is 7.06:1; two percent off the
// paper takes it under 7:1. So, like the grain's budgetSigma, the caller hands
// in the largest MEAN paper darkening this palette can take and the tooth is
// clamped to it, structurally. Luminances in, same contract as phosphorgrain:
// this header knows nothing about PanelPalette and must not start to.
//
// The worst case for the ratio is paper darkened while ink is not, so that is
// what is solved: (paper*m + 0.05) / (ink + 0.05) >= floor.
inline float paperBudget(float inkLum, float paperLum) {
  if (paperLum <= 0.0f) return 0.0f;
  const float need = kContrastFloor * (inkLum + 0.05f) - 0.05f;
  const float m = need / paperLum;
  if (m >= 1.0f) return 0.0f;      // already at or under the floor: no budget
  if (m <= 0.0f) return 1.0f;      // paper could go to nothing (never in sRGB)
  return 1.0f - m;
}

struct Params {
  int strengthPercent = kStrengthStandard;
  uint32_t seed = 0x50524553u;  // 'PRES'
  // Largest mean darkening the PAPER can take, from paperBudget(). 1.0 means
  // "no constraint", for a caller that does not know the palette.
  float paperDarkenBudget = 1.0f;
  // Whether multiplierAt paints the paper TOOTH itself, or leaves it to the
  // sheet pass (sheetToothMultiplierAt below). Default true keeps the original
  // single-pass model; HalDisplay passes false for the panel field now that
  // the tooth is drawn output-wide -- see the 2026-08-22 seam note there.
  bool includeTooth = true;
};

// THE ANSWER: the 0..255 modulate value for one panel pixel, from its 3x3
// inkness window. win[row][col], row 0 up, col 0 left; inkness is 0 at paper,
// 1 at ink (the caller normalizes framebuffer luminance between the live
// pair's luminances). 255 means "untouched"; strength 0 returns 255
// everywhere, so OFF is bit-exact.
inline uint8_t multiplierAt(const Params &p, const float win[3][3], int x,
                            int y, int w, int h) {
  const int strength = clampStrength(p.strengthPercent);
  if (strength == kStrengthOff || w <= 0 || h <= 0) return 255;
  const float s = static_cast<float>(strength) /
                  static_cast<float>(kStrengthStandard);
  const float sHalf = std::sqrt(s);

  const float t = win[1][1];  // inkness at the pixel itself

  // Sobel, normalized so a full paper-to-ink step is magnitude 1.
  const float gx = ((win[0][2] + 2.0f * win[1][2] + win[2][2]) -
                    (win[0][0] + 2.0f * win[1][0] + win[2][0])) * 0.25f;
  const float gy = ((win[2][0] + 2.0f * win[2][1] + win[2][2]) -
                    (win[0][0] + 2.0f * win[0][1] + win[0][2])) * 0.25f;
  float gmag = std::sqrt(gx * gx + gy * gy);
  if (gmag > 1.0f) gmag = 1.0f;

  // INK SQUEEZE: the rim of the stroke, weighted onto the ink side.
  const float ring = kRingAt100 * s * gmag * t;

  // DEBOSS SHADOW: the paper side of edges whose ink lies toward the
  // bottom-right -- i.e. the top-left walls of the depression, the ones a
  // top-left light cannot reach. grad points from paper toward ink, so the
  // shadowed walls are where grad . (1,1)/sqrt(2) is positive.
  float lightDot = (gx + gy) * 0.70710678f;
  if (lightDot < 0.0f) lightDot = 0.0f;
  if (lightDot > 1.0f) lightDot = 1.0f;
  const float deboss = kDebossAt100 * s * lightDot * (1.0f - t);

  const float nx = (static_cast<float>(x) + 0.5f) / static_cast<float>(w);
  const float ny = (static_cast<float>(y) + 0.5f) / static_cast<float>(h);

  // PLATE PRESSURE: only the heavy half (light pressure would brighten).
  const float v = phosphorgrain::valueNoise(nx * kPressCells, ny * kPressCells,
                                            p.seed ^ 0x504C5445u);
  float heavy = v * 2.0f - 1.0f;
  if (heavy < 0.0f) heavy = 0.0f;
  const float press = kPressAt100 * s * heavy * t;

  // IN-STROKE IRREGULARITY (ink) and PAPER TOOTH (paper), both uniform noise
  // in [0, amplitude]. Tooth rides sqrt of the dial and is clamped to the
  // paper's budget: mean darkening of a uniform [0,a] is a/2, so a <= 2*budget
  // keeps the flat page at or above the floor by construction.
  const float u = phosphorgrain::unitFromHash(phosphorgrain::hash3(
      static_cast<uint32_t>(x), static_cast<uint32_t>(y),
      p.seed ^ 0x544F4F54u));
  const float irregular = kIrregularAt100 * s * u * t;
  float toothAmp = kToothAt100 * sHalf;
  const float budget = p.paperDarkenBudget;
  if (budget < 0.5f && toothAmp > 2.0f * budget) toothAmp = 2.0f * budget;
  if (toothAmp < 0.0f) toothAmp = 0.0f;
  const float tooth = p.includeTooth ? toothAmp * u * (1.0f - t) : 0.0f;

  float m = 1.0f - (ring + deboss + press + irregular + tooth);
  if (m < kMinMultiplier) m = kMinMultiplier;
  if (m > 1.0f) m = 1.0f;
  return static_cast<uint8_t>(m * 255.0f + 0.5f);
}

// --- THE SHEET'S TOOTH -----------------------------------------------------
//
// Owner, 2026-08-22 (device report on build 126): "make sure panel and paper
// actually match visually, in color and texture with light mode." The panel
// field above textured only the PAGE, so the paper card painted around it was
// dead flat while the page had tooth -- the 'grainy rectangle on a clean
// ground' failure in reverse, the exact arrangement the grain pass was moved
// output-wide to avoid. Paper properties belong to the whole sheet; glyph
// properties belong to the page. So the components split:
//
//   ring, deboss, pressure, in-stroke   PANEL space (multiplierAt, with
//                                       includeTooth=false) -- all carried by
//                                       ink or its edges, zero on flat paper,
//                                       so the panel boundary shows nothing.
//   paper tooth                         OUTPUT space, this function, drawn
//                                       over the whole sheet -- page, card,
//                                       pad -- one paper, one tooth field.
//
// (Plate pressure is ink-carried by model -- its term multiplies inkness --
// so it is zero on bare sheet on BOTH sides of the boundary: continuous with
// nothing to extend.)
//
// Same amplitude, same sqrt(dial) ride, same paper budget clamp and the same
// 'TOOT' seed lane as the in-panel term it replaces, so the darken-only and
// off-bit-exact invariants and the contrast floor argument carry over
// unchanged: mean darkening of uniform [0,a] noise is a/2 <= budget. A pure
// hash of output coordinates is stationary -- no lattice, no seam, and (per
// ST-008) noise drawn 1:1 at output size cannot moire.
inline uint8_t sheetToothMultiplierAt(const Params &p, int x, int y) {
  const int strength = clampStrength(p.strengthPercent);
  if (strength == kStrengthOff) return 255;
  const float s = static_cast<float>(strength) /
                  static_cast<float>(kStrengthStandard);
  float toothAmp = kToothAt100 * std::sqrt(s);
  const float budget = p.paperDarkenBudget;
  if (budget < 0.5f && toothAmp > 2.0f * budget) toothAmp = 2.0f * budget;
  if (toothAmp < 0.0f) toothAmp = 0.0f;
  const float u = phosphorgrain::unitFromHash(phosphorgrain::hash3(
      static_cast<uint32_t>(x), static_cast<uint32_t>(y),
      p.seed ^ 0x544F4F54u));
  float m = 1.0f - toothAmp * u;
  if (m < kMinMultiplier) m = kMinMultiplier;
  if (m > 1.0f) m = 1.0f;
  return static_cast<uint8_t>(m * 255.0f + 0.5f);
}

}  // namespace letterpress
