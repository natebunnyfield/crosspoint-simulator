#pragma once

// PHOSPHOR MIXING -- the model behind the iOS page-color mixer.
//
// Owner ruling 2026-08-20: the page-color button opens a modal that lets him
// "select which phosphors I want to mix together", seeing "the exact color of
// dark and light, ink and paper, and time to fades for each phosphor". All
// three combination models were wanted ("allow all options"):
//
//   BLEND    the phosphor powders are mixed on one screen. Colors combine in
//            LINEAR light, weighted; every component decays at its own rate, so
//            what lingers shifts toward the longest-lived component's color.
//            This is not an invention: P4 white IS a blend (ZnS:Ag blue plus
//            (Zn,Cd)S:Cu,Al yellow), so any blend the owner builds is a
//            plausible tube.
//   PARTS    no physics, full control: ink from one phosphor, paper from
//            another, trail from a third.
//   CASCADE  two layers in sequence, exactly how P7/P14/P17 physically work:
//            the flash layer paints the page, the persistence layer is what
//            lingers -- in ITS color, which is the whole point of a cascade.
//
// The result lands in the CUSTOM preset slot (owner: "one live mix slot"), so
// everything downstream -- resolve(), the pad tint, the keyboard chips -- keeps
// working without learning anything new. Only the glow needs a mix-aware
// branch, because Custom has no phosphor and would otherwise get trail 0.
//
// Pure and PanelPalette-only on purpose: every failure mode is a wrong color or
// a wrong decay, which no compiler sees. tests/phosphor_mix_test.cpp does.

#include <cmath>

#include "PanelPalette.h"

namespace phosphormix {

enum Mode : int { Blend = 0, Parts = 1, Cascade = 2 };

// --- PREMIXED PHOSPHORS ARE NOT COMPONENTS ---------------------------------
// Owner ruling 2026-08-20: "be sure to not allow premix phosphors to be mixed,
// instead, make those preset mixes." A phosphor that is already a blend or a
// cascade is a RECIPE, not an ingredient -- mixing P4 into a blend would be
// mixing a mixture, and the result stops corresponding to any powder.
//
// The list is decided by the JEDEC composition strings this repo ships in
// kPresetInfo: an explicit "+" or a second compound is a powder blend (P4, P6,
// P18, P23, P40), and an afterglow layer is a cascade (P7, P14, P17). A solid
// solution like P35's ZnS,ZnSe:Ag is ONE crystal lattice, not a powder mix, so
// it stays a valid ingredient.
inline bool isPremixPhosphor(const char *pnum) {
  if (!pnum) return false;
  static const char *const kPremix[] = {"P4",  "P6",  "P7",  "P14",
                                        "P17", "P18", "P23", "P40"};
  for (const char *m : kPremix) {
    const char *a = m;
    const char *b = pnum;
    while (*a && *b && *a == *b) { a++; b++; }
    if (*a == 0 && *b == 0) return true;
  }
  return false;
}

inline bool isPremixPreset(int preset) {
  preset = panelpalette::migratePreset(preset);
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++)
    if (panelpalette::kPresetInfo[i].preset == preset)
      return isPremixPhosphor(panelpalette::kPresetInfo[i].phosphor);
  return false;
}

// A usable INGREDIENT: a real phosphor row that is not itself a mix.
inline bool isMixablePreset(int preset) {
  preset = panelpalette::migratePreset(preset);
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++)
    if (panelpalette::kPresetInfo[i].preset == preset)
      return panelpalette::kPresetInfo[i].phosphor != nullptr &&
             !isPremixPhosphor(panelpalette::kPresetInfo[i].phosphor);
  return false;
}

constexpr int kMaxComponents = 4;

struct Component {
  int preset = -1;   // a panelpalette preset integer; <0 = slot unused
  int weight = 1;    // blend only; relative, clamped to >= 1 when used
};

struct Result {
  panelpalette::Palette dark;
  panelpalette::Palette light;
  float trailMs = 0.0f;
  bool hasTail = false;
  unsigned char tail[3] = {0, 0, 0};  // what the afterglow decays TOWARD
};

// --- linear light ----------------------------------------------------------
// Mixing emitted light is physically additive, and additive means LINEAR.
// Averaging sRGB bytes darkens every mixture (the gamma curve is convex); a
// 50/50 blend of two phosphors at equal brightness must be as bright as either,
// not dimmer than both.

inline float toLinear(unsigned char c) {
  const float f = static_cast<float>(c) / 255.0f;
  return f <= 0.04045f ? f / 12.92f : std::pow((f + 0.055f) / 1.055f, 2.4f);
}

inline unsigned char fromLinear(float v) {
  if (v <= 0.0f) return 0;
  if (v >= 1.0f) return 255;
  const float f =
      v <= 0.0031308f ? v * 12.92f : 1.055f * std::pow(v, 1.0f / 2.4f) - 0.055f;
  const int b = static_cast<int>(f * 255.0f + 0.5f);
  return static_cast<unsigned char>(b < 0 ? 0 : (b > 255 ? 255 : b));
}

namespace detail {

inline panelpalette::Palette paletteOf(int preset, bool dark) {
  // Through resolve() rather than presetPalette(): resolve is the one door
  // every other consumer uses, and it migrates replaced integers first.
  return panelpalette::resolve(preset, dark, panelpalette::kInvalidColor,
                               panelpalette::kInvalidColor);
}

inline void blendChannel(const panelpalette::Palette *pals, const float *w,
                         int n, float total, bool paper,
                         unsigned char out[3]) {
  for (int c = 0; c < 3; c++) {
    float sum = 0.0f;
    for (int i = 0; i < n; i++)
      sum += w[i] * toLinear(paper ? pals[i].paper[c] : pals[i].ink[c]);
    out[c] = fromLinear(sum / total);
  }
}

}  // namespace detail

// How many usable components a list holds.
inline int usableCount(const Component *comps, int n) {
  int count = 0;
  for (int i = 0; i < n && i < kMaxComponents; i++)
    if (comps[i].preset >= 0) count++;
  return count;
}

// --- BLEND -----------------------------------------------------------------
// Weighted linear-light average of inks and papers, in both polarities. The
// trail is the SLOWEST component's -- the visible afterglow lasts until the
// last phosphor has gone dark -- and what lingers is that component's dark ink,
// because everything faster has already died out of the mixture. A tail is only
// reported when the components' persistences actually differ; a blend of
// equal-speed phosphors dims without changing color.
inline Result mixBlend(const Component *comps, int n) {
  Result r;
  panelpalette::Palette darks[kMaxComponents];
  panelpalette::Palette lights[kMaxComponents];
  float w[kMaxComponents];
  float trails[kMaxComponents];
  int used = 0;
  float total = 0.0f;
  int slowest = -1;
  float slowestTrail = -1.0f, fastestTrail = 1e9f;
  for (int i = 0; i < n && i < kMaxComponents; i++) {
    if (comps[i].preset < 0) continue;
    // Premixes are recipes, not ingredients -- silently skipped here, and the
    // UI never offers them, so reaching this line means a stored recipe went
    // stale rather than a user action.
    if (!isMixablePreset(comps[i].preset)) continue;
    darks[used] = detail::paletteOf(comps[i].preset, true);
    lights[used] = detail::paletteOf(comps[i].preset, false);
    w[used] = static_cast<float>(comps[i].weight < 1 ? 1 : comps[i].weight);
    trails[used] = panelpalette::trailMsForPreset(comps[i].preset);
    total += w[used];
    if (trails[used] > slowestTrail) { slowestTrail = trails[used]; slowest = used; }
    if (trails[used] < fastestTrail) fastestTrail = trails[used];
    used++;
  }
  if (used == 0) {
    r.dark = panelpalette::kDefaultDark;
    r.light = panelpalette::kDefaultLight;
    return r;
  }
  detail::blendChannel(darks, w, used, total, false, r.dark.ink);
  detail::blendChannel(darks, w, used, total, true, r.dark.paper);
  detail::blendChannel(lights, w, used, total, false, r.light.ink);
  detail::blendChannel(lights, w, used, total, true, r.light.paper);
  r.trailMs = slowestTrail > 0.0f ? slowestTrail : 0.0f;
  if (used > 1 && slowest >= 0 && slowestTrail > fastestTrail * 1.5f) {
    r.hasTail = true;
    for (int c = 0; c < 3; c++) r.tail[c] = darks[slowest].ink[c];
  }
  return r;
}

// --- PARTS -----------------------------------------------------------------
// Ink from one phosphor, paper from another, trail from a third. Both
// polarities follow the same assignment, so dark and light stay siblings. No
// tail: nothing here is a mixture, so nothing changes color as it dies.
inline Result mixParts(int inkFrom, int paperFrom, int trailFrom) {
  Result r;
  // Same rule as the blend: a premix cannot donate a part. Fall back to the
  // default rather than silently using a mixture as an ingredient.
  if (!isMixablePreset(inkFrom) || !isMixablePreset(paperFrom) ||
      !isMixablePreset(trailFrom)) {
    r.dark = panelpalette::kDefaultDark;
    r.light = panelpalette::kDefaultLight;
    return r;
  }
  const panelpalette::Palette inkD = detail::paletteOf(inkFrom, true);
  const panelpalette::Palette inkL = detail::paletteOf(inkFrom, false);
  const panelpalette::Palette papD = detail::paletteOf(paperFrom, true);
  const panelpalette::Palette papL = detail::paletteOf(paperFrom, false);
  for (int c = 0; c < 3; c++) {
    r.dark.ink[c] = inkD.ink[c];
    r.light.ink[c] = inkL.ink[c];
    r.dark.paper[c] = papD.paper[c];
    r.light.paper[c] = papL.paper[c];
  }
  r.trailMs = panelpalette::trailMsForPreset(trailFrom);
  if (r.trailMs < 0.0f) r.trailMs = 0.0f;
  return r;
}

// --- CASCADE ---------------------------------------------------------------
// The flash layer paints the page -- its palette, unchanged, both polarities.
// The persistence layer is what lingers: its trail, and its DARK INK as the
// tail tint, which is exactly how the shipped P7/P14/P17 rows are built
// (kCascadeAfterglow is P7's persistence layer's emission).
inline Result mixCascade(int flashFrom, int persistFrom) {
  Result r;
  if (!isMixablePreset(flashFrom) || !isMixablePreset(persistFrom)) {
    r.dark = panelpalette::kDefaultDark;
    r.light = panelpalette::kDefaultLight;
    return r;
  }
  r.dark = detail::paletteOf(flashFrom, true);
  r.light = detail::paletteOf(flashFrom, false);
  r.trailMs = panelpalette::trailMsForPreset(persistFrom);
  if (r.trailMs < 0.0f) r.trailMs = 0.0f;
  const panelpalette::Palette p = detail::paletteOf(persistFrom, true);
  r.hasTail = true;
  for (int c = 0; c < 3; c++) r.tail[c] = p.ink[c];
  return r;
}

}  // namespace phosphormix
