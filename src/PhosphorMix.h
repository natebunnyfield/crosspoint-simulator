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

// --- THE SHELF'S PERSISTENCE BANDS -----------------------------------------
// Owner ruling 2026-08-21: "group ingredient shelf by natural breaks of
// persistence fade." The breaks are the DATA's, not round numbers: sorting the
// 34 pure trails, the ratio gaps sit at 20->63 ms (3.2x), 126->283 (2.2x) and
// 1095->2828 (2.6x), plus the largest remaining seam at 400->693 (1.7x). Five
// bands. One definition here so the mixer UI and the proof page cannot drift.
constexpr int kTrailBandCount = 5;

inline int trailBand(float trailMs) {
  if (trailMs <= 21.0f) return 0;      // 16.7-20 ms: gone within a frame
  if (trailMs <= 130.0f) return 1;     // 63-127 ms: a blink
  if (trailMs <= 450.0f) return 2;     // 283-400 ms: a beat
  if (trailMs <= 1200.0f) return 3;    // 693-1095 ms: lingers
  return 4;                            // 2828 ms: holds on
}

inline const char *trailBandName(int band) {
  static const char *const kNames[kTrailBandCount] = {
      "Gone within a frame — under 20 ms",
      "A blink — 60 to 130 ms",
      "A beat — 280 to 400 ms",
      "Lingers — 0.7 to 1.1 s",
      "Holds on — nearly 3 s",
  };
  return band >= 0 && band < kTrailBandCount ? kNames[band] : "";
}

// --- PREMIX RECIPES --------------------------------------------------------
// Owner rulings 2026-08-20/21: tapping a preset mix applies it whole; a
// LONG-PRESS loads it into the mixer as an editable recipe — and the recipes
// are FITTED, not composition maps.
//
// The first table mapped each premix's JEDEC compounds to their nearest pure
// rows (P4 = P22B + P22G, which is chemically exact). Measured against the
// shipped premixes it was off by dE 26-47, and the reason is structural: the
// shipped premix pages were derived from JEDEC WHITE POINTS through the
// palette pipeline (band broadening, gamut mapping, contrast lift), while the
// component rows went through that pipeline separately — the two constructions
// do not commute, so blending the stylized rows cannot land on the stylized
// premix. Chemistry-true recipes that render visibly wrong teach the wrong
// lesson, so on "recompute the eight presets" the table was refitted by
// exhaustive search (pairs and triples of pure rows, weights 1-9) to minimize
// CIELAB distance to each shipped premix's dark pair. Fitted scores are dE
// 3.8-9.6 — a 4-8x improvement — and are pinned by the test.
//
// One physical guardrail: P10 is excluded as a donor. KCl is a dark-trace
// screen — it absorbs where every other row emits — and the unconstrained fit
// happily used it as a dimming agent, which is a fit artifact, not a recipe
// anyone should be handed.
//
// Components are named by P-number string, not preset integer, so the table
// survives renumbering; resolution goes through kPresetInfo at load time.
struct PremixRecipe {
  const char *phosphor;      // the premix row this recipe reconstructs
  Mode mode;                 // Blend or Cascade
  const char *a;             // blend component 1 / cascade flash
  const char *b;             // blend component 2 / cascade persistence
  const char *c;             // blend component 3, or nullptr (owner: "you need three")
  int weightA, weightB, weightC;
};

inline constexpr PremixRecipe kPremixRecipes[] = {
    // Blends, fitted 2026-08-21. Fit score in the comment is CIELAB
    // dE(ink) + 0.5*dE(paper) against the shipped dark pair.
    {"P4", Blend, "P13", "P45", "P5", 1, 6, 1},     // 4.8 (was 32.5)
    {"P6", Blend, "P5", "P45", nullptr, 1, 2, 0},   // 3.8 (was 41.6)
    {"P18", Blend, "P5", "P45", "P56", 2, 7, 1},    // 4.7 (was 42.3)
    {"P23", Blend, "P45", "P56", nullptr, 9, 4, 0}, // 9.6 (was 46.8)
    {"P40", Blend, "P28", "P45", nullptr, 1, 6, 0}, // 8.4 (was 26.1)
    // Cascades, fitted the same day: flash to the shipped page, persistence to
    // the shipped afterglow tint and trail.
    {"P7", Cascade, "P47", "P34", nullptr, 0, 0, 0},
    {"P14", Cascade, "P5", "P26", nullptr, 0, 0, 0},
    {"P17", Cascade, "P5", "P19", nullptr, 0, 0, 0},
};
inline constexpr int kPremixRecipeCount =
    static_cast<int>(sizeof(kPremixRecipes) / sizeof(kPremixRecipes[0]));

inline const PremixRecipe *recipeFor(const char *pnum) {
  if (!pnum) return nullptr;
  for (int i = 0; i < kPremixRecipeCount; i++) {
    const char *a = kPremixRecipes[i].phosphor;
    const char *b = pnum;
    while (*a && *b && *a == *b) { a++; b++; }
    if (*a == 0 && *b == 0) return &kPremixRecipes[i];
  }
  return nullptr;
}

}  // namespace phosphormix
