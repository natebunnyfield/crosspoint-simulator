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
// ONE MASTER DIAL. Ring and deboss scale linearly together -- they are the same
// physical variable, packing pressure -- and the paper's tooth rides at HALF
// proportion (sqrt of the dial): a harder press does not make the paper
// toothier. 0 is bit-exact off. Persisted as the meaningful percent.
//
// ...with THREE PART RATIOS riding on it (p.ringScale / p.debossScale /
// p.pressScale, owner order 2026-08-22 with the paper instrument). The master
// stays the Settings.bundle row; the parts are the drawer's Press group. They
// compose multiplicatively, so each quantity has exactly one stored value and
// neither control is a second authority over the other. All default to 1.0.
//
// ...but the tooth has a SECOND input, and it is not the press: which paper
// this is. p.toothScale carries the stock's own roughness (owner order
// 2026-08-22, with the paper slider), and p.formationDepth its cloudiness.
// Both default to the shipped reference, so a caller that knows nothing about
// paper stocks renders exactly what this header always drew.
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

// THE PART RATIOS' CEILING, and it is not a taste number -- it is the
// no-new-worst-case bound. The master dial's top OFFERED rung is 200 (Heavy)
// and clampStrength's ceiling is kStrengthMax = 400, so a part ratio of 2.0 on
// the heaviest offered press lands exactly on a state the master ladder could
// already reach on its own. Any state the drawer can select, the shipped
// Letterpress row could already select; tests/paper_defects_test.cpp proves it
// term by term rather than leaving it as this paragraph.
//
// ...for RING and DEBOSS. PRESSURE is exempt since the 2026-08-22 widening
// (kPressWidenAboveStandard below): its top now exceeds what the master
// ladder alone could reach, deliberately. That does not reopen any contrast
// argument, because the press term is carried by INK (it multiplies t, is
// exactly zero on bare paper, and darkening ink RAISES a light page's
// contrast); the floor arguments all live on the paper side. The exemption is
// pinned in both tests rather than left here.
constexpr float kPartScaleMax = 2.0f;
constexpr int kOfferedStrengthMax = 200;

inline float clampPartScale(float s) {
  if (!(s > 0.0f)) return 0.0f;  // also catches NaN
  if (s > kPartScaleMax) return kPartScaleMax;
  return s;
}

// --- THE PRESSURE DIAL'S WIDENED RANGE (2026-08-22 audit fix) --------------
//
// The shipped Plate Pressure slider was a near-dead control, measured: the
// FULL 0..200% sweep moved 0.39% of rendered pixels by at most 8 code values.
// The mechanism is the press term's own gates -- kPressAt100 * ratio * s *
// heavy * t caps at 0.12 of the INK's light across the whole dial, and ink at
// the shipped #2D2D2D has only ~45 code values for a multiplier to act on, so
// 0.12 of it is five levels in the heaviest blotch and less than one at
// typical `heavy`. The physical effect is honestly subtle at this scale, so
// the fix is the honest one: the dial's MAPPED RANGE is widened to span what
// the model CAN show, not a different effect wearing the name. Below the
// standard ratio the mapping is the identity -- 1.0 stays byte-exact the
// shipped standard press, and the master ladder (which sweeps `s` at ratio 1)
// is untouched -- and above it each step buys kPressWidenAboveStandard times
// the amplitude, so 200% reaches 8x standard: ~0.48 of the ink's light in the
// heaviest blotch, a visibly uneven forme. Safe by construction: the term is
// ink-carried (zero on bare paper, so no paper-budget or floor argument
// moves) and the kMinMultiplier clamp still bounds it.
constexpr float kPressWidenAboveStandard = 7.0f;

inline float pressAmpScale(float ratio) {
  if (ratio <= 1.0f) return ratio;
  return 1.0f + (ratio - 1.0f) * kPressWidenAboveStandard;
}

// --- THE SHEET'S FORMATION -------------------------------------------------
//
// Owner order 2026-08-22, on the paper slider: "be sure to be adding the
// existing noise treatment to it." Read against what light mode actually did:
// the tooth already covered the whole surface (the 2026-08-22 seam fix), so
// the gap was not coverage. It was that the sheet had no LOW-FREQUENCY
// structure at all. Every existing low-frequency term -- plate pressure here,
// the grain's mottle -- multiplies INKNESS or belongs to the dark page, so
// bare paper was pure white noise: a fine tooth on a perfectly even sheet,
// which no real stock is. Paper FORMATION (the cloudiness you see holding a
// sheet to a light, from fibres flocculating in the headbox) is the missing
// half, and it is exactly the phenomenon the grain's Mottled coverage models
// for a phosphor screen.
//
// So it is built the same way, out of the SAME primitive -- one noise
// implementation in this repo -- and it MODULATES the tooth's amplitude
// rather than adding a darkening of its own. That choice is what keeps the
// paper budget structural: a symmetric +/- swing on the amplitude leaves the
// mean darkening exactly a/2, so the contrast-floor argument carries over
// with nothing new to prove.
//
// Cells is a texture-scale property (how big the cloud is relative to the
// sheet), not a taste dial, same posture as kPressCells and the grain's
// blotch count. Depth is a Params field defaulting to 0, so the pure model's
// old behavior is bit-exact and only a caller that asks gets formation.
constexpr int kFormationCells = 3;
constexpr float kFormationDepthDefault = 0.55f;
constexpr float kFormationDepthMax = 1.0f;

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
  // THE STOCK'S OWN ROUGHNESS, as a multiple of the reference sheet's
  // (owner 2026-08-22: the paper slider brings a stock's texture up with its
  // tone). Supplied by lightink::toothScaleFor(); 1.0 is the shipped Bright
  // White, so a caller that does not set it renders what it always did. This
  // header stays ignorant of the paper TABLE -- it takes a number, the same
  // contract paperDarkenBudget has with the palette.
  float toothScale = 1.0f;
  // Paper formation: how hard the sheet's cloudiness swings the tooth's
  // amplitude, +/- this fraction. 0 is bit-exact "no formation", and is the
  // default so the model's old renderings are unchanged.
  float formationDepth = 0.0f;
  // THE PRESS'S THREE PARTS, as multiples of the constants above (owner order
  // 2026-08-22, with the paper instrument: "make tooth, formation, pressure
  // and all other paper variables sliders"). kRingAt100, kDebossAt100 and
  // kPressAt100 are the STANDARD press; these are the per-component ratios the
  // drawer dials, composing multiplicatively with the master strength dial so
  // there is exactly one stored value per quantity and no duplicate authority.
  //
  // All three default to 1.0, so every pre-existing caller and every existing
  // rendering is bit-exact. APPENDED, never inserted, for the same reason the
  // preset integers are append-only: the aggregate initialisers in
  // tests/letterpress_test.cpp are positional.
  //
  // kPressCells is NOT among them and stays a constant -- cells are texture
  // scale, and a dial on them would be decoration (owner ruling, same order).
  float ringScale = 1.0f;
  float debossScale = 1.0f;
  float pressScale = 1.0f;
};

// A non-negative scale, NaN included. The three press ratios and the tooth
// scale all take this: a negative multiplier would turn a darkening into a
// lift, which is the bug class this whole header is written against.
inline float clampScale(float s) {
  if (!(s > 0.0f)) return 0.0f;  // also catches NaN
  return s;
}

inline float clampFormationDepth(float depth) {
  if (!(depth > 0.0f)) return 0.0f;  // also catches NaN
  if (depth > kFormationDepthMax) return kFormationDepthMax;
  return depth;
}

// --- THE TOOTH'S SHARE OF THE BUDGET ---------------------------------------
//
// Hoisted out of the two places that used to inline it, because a SECOND paper
// layer (src/PaperDefects.h) now has to know what the tooth already spent. Two
// copies of this arithmetic would be two chances to disagree, and a
// disagreement here is a page under the contrast floor that nothing else can
// see.
//
// The clamp is CONDITIONAL, and that is the load-bearing detail: above a budget
// of 0.5 the tooth is not clamped at all. A caller computing "what is left"
// while assuming the clamp always bites asserts a bound the tooth does not
// obey. Reproduced here once, exactly, so it cannot be got wrong twice.
inline float nominalToothAmp(const Params &p) {
  const int strength = clampStrength(p.strengthPercent);
  const float s =
      static_cast<float>(strength) / static_cast<float>(kStrengthStandard);
  return kToothAt100 * std::sqrt(s) * clampScale(p.toothScale);
}

inline float applyToothBudgetClamp(float toothAmp, float budget) {
  if (budget < 0.5f && toothAmp > 2.0f * budget) toothAmp = 2.0f * budget;
  if (toothAmp < 0.0f) toothAmp = 0.0f;
  return toothAmp;
}

inline float clampedToothAmp(const Params &p) {
  return applyToothBudgetClamp(nominalToothAmp(p), p.paperDarkenBudget);
}

// WHAT IS LEFT for a second paper layer. The mean darkening of uniform [0, a]
// noise is a/2, so that is the tooth's share; anything else painted on bare
// paper must fit in the remainder or the two are individually safe and jointly
// over the floor. Never negative: a palette at the floor leaves nothing, and
// the defect layer correctly vanishes there.
//
// Formation is not subtracted. It is a SYMMETRIC swing on the amplitude, so it
// is mean-preserving by construction -- the reason it was built that way.
inline float remainingPaperBudget(const Params &p) {
  const float r = p.paperDarkenBudget - clampedToothAmp(p) * 0.5f;
  return r > 0.0f ? r : 0.0f;
}

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

  const float t = win[1][1];  // inkness at the pixel itself

  // Sobel, normalized so a full paper-to-ink step is magnitude 1.
  const float gx = ((win[0][2] + 2.0f * win[1][2] + win[2][2]) -
                    (win[0][0] + 2.0f * win[1][0] + win[2][0])) * 0.25f;
  const float gy = ((win[2][0] + 2.0f * win[2][1] + win[2][2]) -
                    (win[0][0] + 2.0f * win[0][1] + win[0][2])) * 0.25f;
  float gmag = std::sqrt(gx * gx + gy * gy);
  if (gmag > 1.0f) gmag = 1.0f;

  // INK SQUEEZE: the rim of the stroke, weighted onto the ink side.
  const float ring = kRingAt100 * clampScale(p.ringScale) * s * gmag * t;

  // DEBOSS SHADOW: the paper side of edges whose ink lies toward the
  // bottom-right -- i.e. the top-left walls of the depression, the ones a
  // top-left light cannot reach. grad points from paper toward ink, so the
  // shadowed walls are where grad . (1,1)/sqrt(2) is positive.
  float lightDot = (gx + gy) * 0.70710678f;
  if (lightDot < 0.0f) lightDot = 0.0f;
  if (lightDot > 1.0f) lightDot = 1.0f;
  const float deboss =
      kDebossAt100 * clampScale(p.debossScale) * s * lightDot * (1.0f - t);

  const float nx = (static_cast<float>(x) + 0.5f) / static_cast<float>(w);
  const float ny = (static_cast<float>(y) + 0.5f) / static_cast<float>(h);

  // PLATE PRESSURE: only the heavy half (light pressure would brighten).
  const float v = phosphorgrain::valueNoise(nx * kPressCells, ny * kPressCells,
                                            p.seed ^ 0x504C5445u);
  float heavy = v * 2.0f - 1.0f;
  if (heavy < 0.0f) heavy = 0.0f;
  // The ratio runs through pressAmpScale -- the widened dial (see above).
  // clampScale first, then the widening, so the drawer's 0..2 stays the
  // stored range and the widening has one definition.
  const float press = kPressAt100 * pressAmpScale(clampScale(p.pressScale)) *
                      s * heavy * t;

  // IN-STROKE IRREGULARITY (ink) and PAPER TOOTH (paper), both uniform noise
  // in [0, amplitude]. Tooth rides sqrt of the dial and is clamped to the
  // paper's budget: mean darkening of a uniform [0,a] is a/2, so a <= 2*budget
  // keeps the flat page at or above the floor by construction.
  const float u = phosphorgrain::unitFromHash(phosphorgrain::hash3(
      static_cast<uint32_t>(x), static_cast<uint32_t>(y),
      p.seed ^ 0x544F4F54u));
  const float irregular = kIrregularAt100 * s * u * t;
  const float toothAmp = clampedToothAmp(p);
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
// Same sqrt(dial) ride, same paper budget clamp and the same 'TOOT' seed lane
// as the in-panel term it replaces, so the darken-only and off-bit-exact
// invariants and the contrast floor argument carry over unchanged: mean
// darkening of uniform [0,a] noise is a/2 <= budget. A pure hash of output
// coordinates is stationary -- no lattice, no seam, and (per ST-008) noise
// drawn 1:1 at output size cannot moire.
//
// Two things ride ON that amplitude now (owner 2026-08-22): the STOCK's own
// roughness, p.toothScale, so a chamois wears more tooth than a coated bright
// white and the paper slider brings a stock's texture up with its tone; and
// the sheet's FORMATION, a low-frequency swing described above. Both multiply
// the amplitude before the budget clamp, so neither can breach the floor.
// FORMATION needs the sheet's SIZE, so w/h joined the signature -- defaulted
// to 0, which means "no formation field" and leaves every pre-existing call
// byte-identical. The tooth itself is stationary and needs neither.
inline uint8_t sheetToothMultiplierAt(const Params &p, int x, int y, int w = 0,
                                      int h = 0) {
  const int strength = clampStrength(p.strengthPercent);
  if (strength == kStrengthOff) return 255;
  const float s = static_cast<float>(strength) /
                  static_cast<float>(kStrengthStandard);
  float toothAmp = nominalToothAmp(p);
  // The sheet's cloudiness, as a symmetric swing ON the tooth's amplitude --
  // so it costs no extra mean darkening and the budget clamp below still
  // bounds every point. Same primitive and same shape as the grain's mottle.
  const float depth = clampFormationDepth(p.formationDepth);
  if (depth > 0.0f && w > 0 && h > 0) {
    const float nx = (static_cast<float>(x) + 0.5f) / static_cast<float>(w);
    const float ny = (static_cast<float>(y) + 0.5f) / static_cast<float>(h);
    const float v = phosphorgrain::valueNoise(
        nx * static_cast<float>(kFormationCells),
        ny * static_cast<float>(kFormationCells), p.seed ^ 0x464F524Du);
    toothAmp *= 1.0f + depth * (v * 2.0f - 1.0f);
  }
  toothAmp = applyToothBudgetClamp(toothAmp, p.paperDarkenBudget);
  const float u = phosphorgrain::unitFromHash(phosphorgrain::hash3(
      static_cast<uint32_t>(x), static_cast<uint32_t>(y),
      p.seed ^ 0x544F4F54u));
  float m = 1.0f - toothAmp * u;
  if (m < kMinMultiplier) m = kMinMultiplier;
  if (m > 1.0f) m = 1.0f;
  return static_cast<uint8_t>(m * 255.0f + 0.5f);
}

}  // namespace letterpress
