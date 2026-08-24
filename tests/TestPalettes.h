#pragma once
//
// THE PALETTES THE FIELD SWEEPS ARE MEASURED AGAINST -- derived from the REAL
// table rather than transcribed from it.
//
// Seven field tests (phosphor_grain, scanlines, corner_defocus, letterpress,
// laid_structure, paper_defects, and the two narrower sweeps inside scanlines
// and letterpress) prove that no offered rung of their dial drags a shipped
// page under the 7:1 contrast floor. Each of them used to carry its own
// hand-typed copy of the ink/paper bytes, and NONE of them included
// PanelPalette.h -- so retuning a preset left every one of those sweeps
// proving a page the app no longer ships, and staying green while it did.
//
// Everything here goes through panelpalette::resolve(), the same entry point
// the page itself is painted from and the one phosphor_mix_test.cpp already
// used. A retuned preset now moves the sweep with it.
//
// The bytes each row resolved to when this header was introduced (2026-08-23)
// are recorded in the comments, so a change to one is visible in a diff of the
// test output rather than only in the palette table.
//
#include "PanelPalette.h"

namespace testpalettes {

// The shape the five field sweeps loop over: `page.r/g/b` is the ink and
// `page.pr/pg/pb` the paper, which is the member naming those loops already
// use. `name` is new and unread by most of them; it costs nothing and makes a
// future failure message able to say which page failed.
struct Page {
  const char *name;
  int r, g, b;     // ink
  int pr, pg, pb;  // paper
};

constexpr Page pageFrom(int preset, bool dark, const char *name) {
  const panelpalette::Palette p = panelpalette::resolve(preset, dark, -1, -1);
  return Page{name, p.ink[0],   p.ink[1],   p.ink[2],
              p.paper[0], p.paper[1], p.paper[2]};
}

// A literal page that corresponds to NO current preset. Used only where a
// sweep deliberately probes tones the app does not ship (see kExtraLightProbes
// below); anything that IS a shipped page must come from pageFrom().
constexpr Page pageLiteral(const char *name, int r, int g, int b, int pr,
                           int pg, int pb) {
  return Page{name, r, g, b, pr, pg, pb};
}

// --- THE DARK SWEEP ------------------------------------------------------
// The shipped shortlist's dark tones, spanning the contrast range: the
// roomiest page in the set and the two tightest this repo ships. P11 Blue and
// P22R Red are load-bearing -- they are the pair that fell to 5.6:1 under the
// since-removed global sigma, which is the regression these sweeps exist for.
inline constexpr Page kDarkP4 =
    pageFrom(panelpalette::kPresetGrayCrt, true, "P4, 13.9:1");  // C9E7FF/14181A
inline constexpr Page kDarkP22G =
    pageFrom(panelpalette::kPresetP22GCrt, true, "P22G");        // 00FF97/00190A
inline constexpr Page kDarkP3 =
    pageFrom(panelpalette::kPresetAmberCrt, true, "P3");         // FFB000/1A1000
inline constexpr Page kDarkP11 =
    pageFrom(panelpalette::kPresetBlueCrt, true,
             "P11, 7.4:1 -- the tight one");                     // 8B92FF/00061A
inline constexpr Page kDarkP22R =
    pageFrom(panelpalette::kPresetRedCrt, true, "P22R");         // FF6F6C/1A0300

inline constexpr Page kDarkSweep[] = {kDarkP4, kDarkP22G, kDarkP3, kDarkP11,
                                      kDarkP22R};
inline constexpr int kDarkSweepCount =
    static_cast<int>(sizeof(kDarkSweep) / sizeof(kDarkSweep[0]));

// The two tightest of the above, on their own, for the sweeps that only care
// about the worst case.
inline constexpr Page kDarkTightest[] = {kDarkP11, kDarkP22R};
inline constexpr int kDarkTightestCount =
    static_cast<int>(sizeof(kDarkTightest) / sizeof(kDarkTightest[0]));

// --- THE LIGHT SWEEP -----------------------------------------------------
// The shipped light pages, spanning 21:1 down to Latte's 7.06:1 -- which has
// almost no room at all and is what the paper budget's clamp is holding.
inline constexpr Page kLightDefault =
    pageFrom(panelpalette::kPresetDefault, false, "Default, 13.3:1");
inline constexpr Page kLightHighContrast =
    pageFrom(panelpalette::kPresetHighContrast, false, "High Contrast, 21:1");
inline constexpr Page kLightSepia =
    pageFrom(panelpalette::kPresetSepia, false, "Sepia, 10.2:1");
inline constexpr Page kLightGruvbox =
    pageFrom(panelpalette::kPresetGruvboxLight, false, "Gruvbox Light, 10.2:1");
inline constexpr Page kLightLatte =
    pageFrom(panelpalette::kPresetLatte, false, "Latte, 7.06:1 -- the tight one");

inline constexpr Page kLightSweep[] = {kLightDefault, kLightHighContrast,
                                       kLightSepia, kLightGruvbox, kLightLatte};
inline constexpr int kLightSweepCount =
    static_cast<int>(sizeof(kLightSweep) / sizeof(kLightSweep[0]));

// Latte on its own, by name, for the sweeps that quote it as THE tight page.
inline constexpr Page kLightTightest = kLightLatte;

// --- THE OTHER SHAPE -----------------------------------------------------
// paper_defects_test.cpp loops over ink[]/paper[] arrays rather than named
// channels. Same source, second projection.
struct Pal {
  const char *name;
  int ink[3];
  int paper[3];
};

constexpr Pal palFrom(int preset, bool dark, const char *name) {
  const panelpalette::Palette p = panelpalette::resolve(preset, dark, -1, -1);
  return Pal{name,
             {p.ink[0], p.ink[1], p.ink[2]},
             {p.paper[0], p.paper[1], p.paper[2]}};
}

constexpr Pal palLiteral(const char *name, int ir, int ig, int ib, int pr,
                         int pg, int pb) {
  return Pal{name, {ir, ig, ib}, {pr, pg, pb}};
}

// The light sweep in Pal shape. The first three rows ARE shipped presets --
// they were transcribed under different names ("black on white" is High
// Contrast, "repo default" is Default) and are now derived.
//
// The last three are NOT presets and never were: checked against every row of
// kPresetInfo in both appearances, none of them matches, and no literal in
// src/ or ios/ carries those bytes either. They are deliberate synthetic
// probes -- two historical ink-on-stock pairs and one page parked just above
// the floor to force the CLAMPED regime, which the sweep asserts it reaches
// (`sawTight > 0`). Dropping them would silently stop testing that branch, so
// they stay as explicit literals here rather than being quietly lost.
inline constexpr Pal kLightPals[] = {
    palFrom(panelpalette::kPresetHighContrast, false, "black on white"),
    palFrom(panelpalette::kPresetDefault, false, "repo default"),
    palFrom(panelpalette::kPresetLatte, false, "latte"),
    // Not preset-derived -- synthetic probes, see the note above.
    palLiteral("sepia ink on tan", 0x3A, 0x2E, 0x22, 0xEA, 0xDF, 0xC6),
    palLiteral("iron gall on rag", 0x2A, 0x2A, 0x3A, 0xF2, 0xEC, 0xDC),
    palLiteral("at the floor", 0x5A, 0x5A, 0x5A, 0xE8, 0xE8, 0xE8),
};
inline constexpr int kLightPalsCount =
    static_cast<int>(sizeof(kLightPals) / sizeof(kLightPals[0]));

}  // namespace testpalettes
