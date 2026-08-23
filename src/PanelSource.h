#pragma once

// WHERE THE PAGE'S TWO TONES COME FROM -- for BOTH polarities, on every path.
//
// This file exists because of an owner P1, 2026-08-23: "ink is not being picked
// up. recreate, review and fix sourcing for light and dark to be more accurate
// on load, switch etc." It was reproduced exactly as reported, and the mechanism
// was not the reader: it was that the page's tones had TWO writers and no
// owner.
//
// THE DOCTRINE (2026-08-22, docs/light-ink-picker.md): light mode is paper and
// ink, edited by the historical-ink picker; dark mode is the CRT, edited by the
// gun mixer. The page-color chip branches on the live appearance and opens one
// or the other. Two editors, two polarities, one each.
//
// THE STORE THEY SHARE does not have that shape. It is one preset integer plus
// four hex fields -- ink and paper for each appearance -- and "Custom" is a
// single value of that one integer meaning "read the hex fields". So a polarity
// is not a thing either editor can own; it is a convention, and the convention
// was broken in both directions:
//
//   1. The MIXER wrote all four fields (ios/CrossPointPaletteMixer.mm applyGuns,
//      the `r.light.*` writes). Touching a slider in dark mode therefore threw
//      away the light page's chosen ink. MEASURED on an iPhone Air simulator,
//      2026-08-23: Payne's Gray applied in light stored panelInkLight=323D47 and
//      the page's darkest text measured (30,37,43); one gun move in dark mode
//      rewrote panelInkLight to 6E0500 and the same text measured (64,3,0) -- a
//      red -- while lightInkIndex still read 15 and the picker still showed
//      Payne's Gray as chosen. That is the report, in pixels.
//
//   2. Pointing the preset at Custom for ONE polarity's sake silently changed
//      the OTHER. The ink picker already knew this for the tones and froze the
//      dark pair before flipping (its "dark snapshot"), but nothing froze the
//      dark page's PHOSPHOR: pollPanelGlow reads the preset integer, and Custom
//      names no phosphor, so a light-mode ink pick turned a 283 ms White CRT
//      trail into 0 ms reflective and left it that way across relaunches.
//      Measured in the same session, from the app's own [glow] line.
//
// So: ONE definition of "what is each polarity painted in, and what is the dark
// page's phosphor", plus ONE definition of what an editor must freeze before it
// claims the Custom slot. Pure and host-tested (tests/panel_source_test.cpp) for
// exactly the reason PanelPalette.h and PadPalette.h are: every failure mode
// here is a wrong COLOR on one appearance, which no compiler sees, no other test
// here sees, and the owner sees immediately.
//
// The iOS adapter is ios/PanelPrefs.h -- it fills the Store from NSUserDefaults
// and calls these. Nothing else may decide any of this.

#include "PanelPalette.h"

namespace panelsource {

// Everything the two editors persist that decides what the page looks like.
// Deliberately plain data: the adapter reads NSUserDefaults, this file decides.
struct Store {
  // The shared preset integer. kPresetCustom means "the four hex fields".
  int preset = panelpalette::kPresetDefault;

  // Indexed [light, dark], packed 0xRRGGBB or panelpalette::kInvalidColor.
  int customInk[2] = {panelpalette::kInvalidColor, panelpalette::kInvalidColor};
  int customPaper[2] = {panelpalette::kInvalidColor,
                        panelpalette::kInvalidColor};

  // Is a phosphor MIX the dark page's source? (phosphorMixActive; the mixer
  // owns its own decay and tail and answers for them itself.)
  bool mixActive = false;

  // THE PHOSPHOR THE DARK PAGE WAS FROZEN FROM, when an editor pointed the
  // preset at Custom for the other polarity's sake. kPresetCustom -- which is
  // also what an absent key reads as -- means "no phosphor", which is the
  // historical answer and the right one for an install that never had one.
  int darkSnapshotPreset = panelpalette::kPresetCustom;
};

// THE PAIR ONE POLARITY IS PAINTED IN. The single reader; the SDL side paints
// the page, the pad and the SHOW chip from it, and UIKit paints the HIDE chip.
constexpr panelpalette::Palette panelFor(const Store &s, bool dark) {
  const int d = dark ? 1 : 0;
  // A NAMED preset owns BOTH polarities -- that is what choosing one in
  // Settings.app means, and honoring a stale per-polarity override under it
  // would make the row stop working for half the app. resolve() ignores the
  // custom colors unless the preset is Custom, so they are handed over
  // unconditionally and it decides.
  return panelpalette::resolve(s.preset, dark, s.customInk[d],
                               s.customPaper[d]);
}

// THE PRESET THE GLOW IS SOURCED FROM -- i.e. which phosphor, if any, the page
// claims to be. Not always s.preset, and that difference is bug 2 above.
//
// An active MIX answers for itself (the mixer computes its own trail, tail and
// onset from the stored blend), so this returns Custom for it and the caller
// asks the mixer. With no mix, a Custom slot means some editor froze the dark
// page's tones from a named preset -- and the phosphor has to be frozen with
// them, or picking a light-mode ink kills the dark page's trail.
constexpr int glowPreset(const Store &s) {
  const int preset = panelpalette::migratePreset(s.preset);
  if (preset != panelpalette::kPresetCustom) return preset;
  if (s.mixActive) return panelpalette::kPresetCustom;  // the mixer answers
  return panelpalette::migratePreset(s.darkSnapshotPreset);
}

// WHAT AN EDITOR MUST FREEZE BEFORE IT CLAIMS THE CUSTOM SLOT.
//
// One definition for both editors, because the failure is invisible from inside
// either one: the ink picker had this for the dark tones and the mixer did not
// have it at all, and each looked complete on its own.
struct Claim {
  // Does the preset have to move to Custom, and therefore does the other
  // polarity have to be frozen first? False when the slot is already Custom --
  // then the other polarity's fields are an owner's choice, not an inherited
  // default, and overwriting them is exactly bug 1.
  bool freezeOther = false;
  // Which polarity to freeze: the one this editor does NOT own.
  bool freezeDark = false;
  // ...and, when that polarity is the dark one, the phosphor to remember with
  // it. kPresetCustom when there is nothing to remember.
  int rememberPhosphor = panelpalette::kPresetCustom;
};

constexpr Claim claimCustom(int storedPreset, bool editingDark) {
  Claim c{};
  const int preset = panelpalette::migratePreset(storedPreset);
  if (preset == panelpalette::kPresetCustom) return c;
  c.freezeOther = true;
  c.freezeDark = !editingDark;
  if (c.freezeDark) c.rememberPhosphor = preset;
  return c;
}

// --- pinned here as well as in the test, so a wrong answer cannot compile ----

// A named preset owns both polarities, whatever the hex fields hold.
static_assert(panelFor(Store{panelpalette::kPresetDefault,
                             {0x112233, 0x445566},
                             {0x778899, 0xAABBCC},
                             false,
                             panelpalette::kPresetCustom},
                       false)
                      .ink[0] == 0x2D,
              "a named preset must ignore the custom fields");

// Custom takes each polarity's own two fields, independently.
static_assert(panelFor(Store{panelpalette::kPresetCustom,
                             {0x323D47, 0xB6EFFF},
                             {0xFBFBF9, 0x182327},
                             false,
                             21},
                       false)
                      .ink[0] == 0x32,
              "custom light must be the light fields");
static_assert(panelFor(Store{panelpalette::kPresetCustom,
                             {0x323D47, 0xB6EFFF},
                             {0xFBFBF9, 0x182327},
                             false,
                             21},
                       true)
                      .ink[0] == 0xB6,
              "custom dark must be the dark fields");

// A frozen dark page keeps its phosphor; an active mix answers for itself.
static_assert(glowPreset(Store{panelpalette::kPresetCustom,
                               {0, 0},
                               {0, 0},
                               false,
                               21}) == 21,
              "the frozen phosphor must survive the move to Custom");
static_assert(glowPreset(Store{panelpalette::kPresetCustom,
                               {0, 0},
                               {0, 0},
                               true,
                               21}) == panelpalette::kPresetCustom,
              "an active mix must answer for its own decay");

// The light editor freezes dark AND its phosphor; the dark editor freezes light
// and has no phosphor to remember. Neither freezes anything once Custom is set.
static_assert(claimCustom(21, /*editingDark=*/false).freezeDark &&
                  claimCustom(21, false).rememberPhosphor == 21,
              "the ink picker must freeze the dark page and its phosphor");
static_assert(claimCustom(21, /*editingDark=*/true).freezeOther &&
                  !claimCustom(21, true).freezeDark &&
                  claimCustom(21, true).rememberPhosphor ==
                      panelpalette::kPresetCustom,
              "the mixer must freeze the light page, and has no phosphor to "
              "remember for it");
static_assert(!claimCustom(panelpalette::kPresetCustom, false).freezeOther &&
                  !claimCustom(panelpalette::kPresetCustom, true).freezeOther,
              "an already-Custom slot holds owner choices in both polarities");

}  // namespace panelsource
