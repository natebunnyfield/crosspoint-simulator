#pragma once

// THE PICCO'S FRONTLIGHT, ON A PAGE THAT HAS NO LIGHT (TODO.md ST-012).
//
// Owner 2026-11-26, verbatim: "future todo: for warmth setting on picco to
// adjust paper warmth and crt warmth; brightness adjusts ink and crt specific
// physics". Built 2026-11-27 on "connect brightness and warmth as described in
// the earlier todo".
//
// The phone has no frontlight, so the firmware's Brightness and Warmth rows
// (CrossPointSettings::frontlightBrightness / frontlightWarmth, 0..100, 0 the
// coolest) drive the simulated page instead. PURE: no SDL, no atomics, no
// SimulatorOverlay; the host test compiles it directly.
//
// THE FROZEN PAGE IS THE ORIGIN. At the firmware's defaults (60 / 50), and
// whenever the light is off, every function here answers src/FrozenPage.h byte
// for byte -- returned from there, not recomputed, so a rounding difference
// cannot move the page nobody asked to move. The frozen-page ruling froze the
// page's INPUTS; this file moves them only along the two axes the owner named.
//
// LIGHT PAGE (Sanguine on India):
//   Warmth     tints the PAPER the way a warm or cool light does: India's tone
//              times an illuminant, renormalized to India's own luminance, so
//              warmth never brightens or dims the sheet. The ink is untouched
//              (owner: warmth adjusts PAPER warmth).
//   Brightness sets the INK's depth on the Beer-Lambert law the picker's
//              density dial already uses (lightink::washOnGround), continued
//              past full strength: 60 is the frozen Sanguine, 0 the thinnest
//              wash that still clears 7:1 on this sheet, 100 a deeper-than-full
//              charge. Linear between those three points, so every step of the
//              row moves the page (a ramp that started below the floor spent
//              the bottom third of the row on one clamped value).
// DARK PAGE (the four-gun phosphor blend):
//   Warmth     re-weights the GUNS: the two warm phosphors (P38 amber, P22R
//              red) against the two cool ones (P45 white, P20 yellow-green),
//              so the tube's own phosphors make the warmth and the afterglow
//              tail follows through the mixer.
//   Brightness is the BEAM: the trace's emission (the ink, in linear light),
//              the scanline bloom, and how long the afterglow stays visible.
//              Same three points: 0 the dimmest trace that clears 7:1 on this
//              glass, 60 the frozen trace, 100 an overdriven one.
//
// THE 7:1 FLOOR HOLDS AT EVERY SETTING (lightink::kContrastFloor): a light-page
// ink is never thinner than the floor against its tinted sheet (after the drift
// budget the renderer applies, which lightink shrinks to fit the floor), and a
// dark-page beam is never dimmer than the floor against its glass.
//
// AT THE BOTTOM OF BRIGHTNESS BOTH PAGES GO FLAT, by construction. Brightness 0
// puts the ink or trace ON the floor, and every texture field spends only the
// contrast above it (src/FieldSelection.h, src/Scanlines.h): the light sheet's
// tooth and formation have nothing left, and the dark page's scanlines fall to
// about 6% of their depth at 0 and about 80% at 5, full from 10 (measured by
// the 2026-11-27 adversarial review). THOSE THREE FIGURES ARE WARMTH 50 ONLY:
// Warmth moves the trace and the glass, so the headroom that caps the depth
// moves too. At Warmth 100 the scanlines are 0% at 0, 35% at 5, 67% at 10, 95%
// at 15 and full from 20; at Warmth 0 they are 10% at 0 and full from 5. The
// table for every step is in docs/frontlit-page-2026-11-27.md.

#include <algorithm>
#include <cmath>

#include "FrontlitLight.h"
#include "FrozenPage.h"
#include "GunMixCsv.h"
#include "LightInkPalette.h"
#include "PanelPalette.h"
#include "PhosphorMix.h"
#include "Scanlines.h"

namespace frontlitpage {

inline int clampPct(int v) { return v < 0 ? 0 : (v > kMax ? kMax : v); }

// Off, or on at the defaults: the frozen page, untouched.
inline bool isNeutral(const Light &l) {
  return !l.on || (clampPct(l.brightness) == kDefaultBrightness &&
                   clampPct(l.warmth) == kDefaultWarmth);
}

// -1 (coolest) .. 0 (frozen) .. +1 (warmest).
inline double warmthAxis(const Light &l) {
  return (clampPct(l.warmth) - kDefaultWarmth) / static_cast<double>(kDefaultWarmth);
}

// --- tuning ------------------------------------------------------------------
//
// Chosen by eye against rendered pages, not derived; the renders are the
// judge. Each is a ratio in LINEAR light against the frozen page.
//
// The illuminant at the two ends of Warmth, per channel R, G, B, before the
// luminance renormalization. Warm leans to a cream/peach (blue falls most),
// cool to a blue-white.
inline constexpr double kPaperWarmEnd[3] = {1.0, 0.86, 0.58};
inline constexpr double kPaperCoolEnd[3] = {0.90, 1.0, 1.20};
// The ink's Beer-Lambert depth at Brightness 100 (1.0 is full strength, the
// frozen ink).
inline constexpr double kInkDepthMax = 1.6;
// The warm/cool gun ratio at the ends of Warmth: the warm guns are multiplied,
// the cool ones divided, by up to this.
inline constexpr double kGunWarmthRatio = 3.0;
// The beam's emission at Brightness 100, as a multiple of the frozen trace in
// linear light. Channels that would pass 1.0 clip, which reads as an overdriven
// trace whitening, which it is.
inline constexpr double kBeamMax = 1.4;
// The afterglow's visible length follows the beam's emission with this
// exponent: a brighter deposit takes longer to fall below sight.
inline constexpr double kTrailExponent = 0.5;

// --- shared helpers ----------------------------------------------------------

inline double lin(unsigned char v) { return lightink::srgbToLinear(v); }
inline unsigned char enc(double l) {
  return lightink::linearToSrgb(l < 0.0 ? 0.0 : (l > 1.0 ? 1.0 : l));
}
inline double luminanceLin(const double l[3]) {
  return 0.2126 * l[0] + 0.7152 * l[1] + 0.0722 * l[2];
}

// --- LIGHT PAGE ----------------------------------------------------------------

// India under a warmer or cooler light, at India's own luminance.
inline void tintedPaper(const Light &l, unsigned char out[3]) {
  const panelpalette::Palette frozen = frozenpage::lightPair();
  const double t = warmthAxis(l);
  const double *end = t >= 0.0 ? kPaperWarmEnd : kPaperCoolEnd;
  const double a = std::fabs(t);
  double p[3];
  for (int c = 0; c < 3; c++) p[c] = lin(frozen.paper[c]) * std::pow(end[c], a);
  // Renormalize to the frozen sheet's luminance, then clip. A clipped channel
  // loses a hair of luminance and so a little contrast; harmless, because the
  // ink's floor is searched against this tinted sheet afterwards.
  double base[3];
  for (int c = 0; c < 3; c++) base[c] = lin(frozen.paper[c]);
  const double k = luminanceLin(base) / luminanceLin(p);
  for (int c = 0; c < 3; c++) out[c] = enc(p[c] * k);
}

// Sanguine at Beer-Lambert depth d on the untinted sheet it is printed on (the
// picker's ground: lightink::inkAtDensity at the frozen stock and strength).
inline void inkAtDepth(double d, unsigned char out[3]) {
  const frozenpage::LightSelection s = frozenpage::lightSelection();
  unsigned char ground[3];
  lightink::paperAtStrength(s.paper, s.paperStrength, ground);
  const lightink::Ink &ink = lightink::kInks[lightink::clampInkIndex(s.ink)];
  for (int c = 0; c < 3; c++) {
    double il = lin(ink.full[c]), gl = lin(ground[c]);
    if (il < lightink::kLinearEpsilon) il = lightink::kLinearEpsilon;
    if (gl < lightink::kLinearEpsilon) gl = lightink::kLinearEpsilon;
    out[c] = enc(gl * std::pow(il / gl, d));
  }
}

// The contrast the floor is held against, through the same drift clamp the
// renderer uses (lightink::paperWorstDriftForPair shrinks the drift to fit
// the floor, so at the floor this is plain ink-on-paper contrast and the
// drift is off).
inline double lightContrast(const unsigned char ink[3],
                            const unsigned char paper[3]) {
  unsigned char worst[3];
  lightink::paperWorstDriftForPair(ink, paper, lightink::kPaperDriftMax, worst);
  return lightink::contrastRatio(ink, worst);
}

// The thinnest depth whose wash clears 7:1 on this sheet (lightContrast).
// Monotone in depth, so the first passing step is the floor.
inline double floorInkDepth(const unsigned char paper[3]) {
  unsigned char ink[3];
  for (double d = 0.0; d < 1.0; d += 0.005) {
    inkAtDepth(d, ink);
    if (lightContrast(ink, paper) >= lightink::kContrastFloor) return d;
  }
  return 1.0;
}

// Three points, linear between: 0 -> floor, 60 -> 1 (frozen), 100 -> max.
inline double rampFor(const Light &l, double floor, double max) {
  const int b = clampPct(l.brightness);
  if (b >= kDefaultBrightness)
    return 1.0 + (max - 1.0) * (b - kDefaultBrightness) /
                     static_cast<double>(kMax - kDefaultBrightness);
  return floor + (1.0 - floor) * b / static_cast<double>(kDefaultBrightness);
}

// The iOS harness asks for both pages several times per frame (the palette,
// glow and scanline polls), always at the same light, so each page keeps the
// last answer per thread. Today every caller is on the main thread (the
// firmware loop, the iOS polls and the desktop's change hook share it);
// thread_local keeps the answer consistent if that ever changes.
inline bool sameLight(const Light &a, const Light &b) {
  return a.on == b.on && clampPct(a.brightness) == clampPct(b.brightness) &&
         clampPct(a.warmth) == clampPct(b.warmth);
}

inline panelpalette::Palette computeLightPair(const Light &l) {
  panelpalette::Palette out{};
  tintedPaper(l, out.paper);
  double d = rampFor(l, floorInkDepth(out.paper), kInkDepthMax);
  inkAtDepth(d, out.ink);
  // The floor was found on a 0.005 grid; one more guard step settles any
  // rounding at the boundary.
  while (lightContrast(out.ink, out.paper) < lightink::kContrastFloor &&
         d < kInkDepthMax) {
    d += 0.005;
    inkAtDepth(d, out.ink);
  }
  return out;
}

inline panelpalette::Palette lightPair(const Light &l) {
  if (isNeutral(l)) return frozenpage::lightPair();
  thread_local bool have = false;
  thread_local Light last;
  thread_local panelpalette::Palette cached;
  if (!have || !sameLight(l, last)) {
    cached = computeLightPair(l);
    last = l;
    have = true;
  }
  return cached;
}

// --- DARK PAGE -----------------------------------------------------------------

// The frozen guns, warmth re-weighted. Warm: P38 amber (R) and P22R red (W);
// cool: P45 white (G) and P20 yellow-green (B). Weights are scaled by 100 so
// the ratio keeps its resolution through mixBlend's integer weights.
inline bool isWarmGun(int g) { return g == 0 || g == 3; }

inline phosphormix::Result reweightedMix(const Light &l) {
  const double f = std::pow(kGunWarmthRatio, warmthAxis(l));
  phosphormix::Component comps[gunmix::kGunCount];
  int n = 0;
  for (int g = 0; g < gunmix::kGunCount; g++) {
    if (frozenpage::kGunWeight[g] <= 0) continue;
    const double scale = isWarmGun(g) ? f : 1.0 / f;
    comps[n].preset = frozenpage::kGunPreset[g];
    comps[n].weight = std::max(
        1, static_cast<int>(std::lround(frozenpage::kGunWeight[g] * 100.0 * scale)));
    n++;
  }
  return phosphormix::mixBlend(comps, n);
}

inline void scaleEmission(const unsigned char in[3], double k,
                          unsigned char out[3]) {
  for (int c = 0; c < 3; c++) out[c] = enc(lin(in[c]) * k);
}

struct Dark {
  phosphormix::Result mix;  // dark.ink is the beam-scaled trace
  double beam = 1.0;        // the emission multiple actually applied
};

inline Dark computeDarkPage(const Light &l) {
  Dark d;
  d.mix = reweightedMix(l);
  const panelpalette::Palette base = d.mix.dark;
  // The dimmest beam whose trace clears 7:1 against this glass. Monotone in
  // the beam, so the first passing step is the floor.
  double floor = 1.0;
  unsigned char probe[3];
  for (double k = 0.05; k < 1.0; k += 0.005) {
    scaleEmission(base.ink, k, probe);
    if (lightink::contrastRatio(probe, base.paper) >= lightink::kContrastFloor) {
      floor = k;
      break;
    }
  }
  double k = rampFor(l, floor, kBeamMax);
  scaleEmission(base.ink, k, d.mix.dark.ink);
  while (lightink::contrastRatio(d.mix.dark.ink, base.paper) <
             lightink::kContrastFloor &&
         k < kBeamMax) {
    k += 0.005;
    scaleEmission(base.ink, k, d.mix.dark.ink);
  }
  d.beam = k;
  // The afterglow is the same emission dying: its tint dims and brightens with
  // the beam, and it stays visible longer when the deposit was brighter.
  if (d.mix.hasTail) scaleEmission(d.mix.tail, k, d.mix.tail);
  d.mix.trailMs *= static_cast<float>(std::pow(k, kTrailExponent));
  return d;
}

inline Dark darkPage(const Light &l) {
  if (isNeutral(l)) {
    Dark d;
    d.mix = frozenpage::darkMix();
    return d;
  }
  thread_local bool have = false;
  thread_local Light last;
  thread_local Dark cached;
  if (!have || !sameLight(l, last)) {
    cached = computeDarkPage(l);
    last = l;
    have = true;
  }
  return cached;
}

inline panelpalette::Palette darkPair(const Light &l) { return darkPage(l).mix.dark; }

// The scanline bloom for this beam, from the value the app ships. Bloom is the
// trace's own light spilling into the gaps, so it follows the emission; capped
// at the dial's maximum, which is where the shipped value already sits.
inline int bloomPercent(const Light &l, int shippedBloom) {
  if (isNeutral(l)) return shippedBloom;
  const double k = darkPage(l).beam;
  const int v = static_cast<int>(std::lround(shippedBloom * k));
  return std::clamp(v, 0, scanlines::kBloomMax);
}

}  // namespace frontlitpage
