#pragma once

// The owner's chosen panel pair, resolved from Settings.app.
//
// ONE definition, because there are now two consumers and they must not be able
// to disagree: the SDL side paints the page, the pad and the SHOW chip from it
// (CrossPointIOSShim.cpp), and the UIKit side paints the HIDE chip in the
// keyboard's accessory bar (CrossPointKeyboardBar.mm). Those two chips are the
// same control in two halves of the same gesture, so a divergence is visible
// immediately and reads as a bug -- which is exactly what it was: the hide chip
// carried hardcoded default tones while the show chip followed the palette, so
// choosing any non-default preset split them (owner, 2026-08-15: "match hide
// keyboard color to show keyboard color").
//
// Header-only and inline rather than a .cpp: CrossPointKeyboardBar.mm is
// Objective-C++ and the shim is C++, so both can include this directly, and
// neither build needs a new translation unit.

#include "CrossPointPrefs.h"
#include "PadPalette.h"
#include "PanelPalette.h"
#include "PanelSource.h"

namespace crosspoint {

// The stored state the page's appearance is decided from, gathered in one
// place. THE DECISIONS ARE NOT HERE -- they are in src/PanelSource.h, pure and
// host-tested, because every failure mode is a wrong color on one appearance
// (owner P1 2026-08-23, "ink is not being picked up ... fix sourcing for light
// and dark"). This function only fetches; that file only decides.
//
// Read live on every call, per frame on the SDL side. Two integer reads and
// four short strings out of NSUserDefaults is not a cost worth caching, and a
// cache is the shape that goes stale across an appearance switch.
inline panelsource::Store panelStoreFromPrefs() {
  panelsource::Store s{};
  s.preset = CrossPointPrefs_panelPalettePreset();
  for (int d = 0; d < 2; d++) {
    s.customInk[d] = CrossPointPrefs_panelCustomColor(d, 1);
    s.customPaper[d] = CrossPointPrefs_panelCustomColor(d, 0);
  }
  s.mixActive = CrossPointPrefs_phosphorMixActive() != 0;
  s.darkSnapshotPreset = CrossPointPrefs_darkSnapshotPreset();
  return s;
}

// The pair for one appearance.
inline panelpalette::Palette panelForPrefs(bool dark) {
  return panelsource::panelFor(panelStoreFromPrefs(), dark);
}

// Which phosphor the page claims to be, for pollPanelGlow. NOT simply the
// stored preset: a Custom slot that some editor froze from a named phosphor
// still IS that phosphor, and reading the raw integer is what turned a
// light-mode ink pick into a dead dark-mode trail. Returns kPresetCustom when
// the mixer owns the answer -- it computes its own decay from the stored blend.
inline int glowPresetForPrefs() {
  return panelsource::glowPreset(panelStoreFromPrefs());
}

// The two keyboard chips' tones: THE PAD'S OWN, as of 2026-08-17.
//
// REVERSAL, and recorded as one because it overturns an explicit instruction.
// The chips were light gray by owner instruction restated 2026-08-16 ("why
// isn't the keyboard hide and show buttons light grey as was previously
// instructed?"), and this file argued for it at length. On 2026-08-17 the owner
// asked for the opposite: "match show/hide keyboard button outline with rest of
// app." The later instruction wins. The old reasoning is kept below ONLY so
// that nobody re-derives the light-gray rule from first principles and quietly
// reverts this -- it is superseded, not advice.
//
// So the chips take the PAD's palette now -- whatever outline and fill contrast
// the owner has set, Black & White default included -- and stop being a special
// case. Still ONE definition for both, because the SHOW chip is SDL and the
// HIDE chip is UIKit and a divergence between them is invisible to every test
// here except tests/chip_tint_source_test.py.
//
// --- SUPERSEDED 2026-08-17 ---------------------------------------------------
//   The two keyboard chips' own tones, and deliberately NOT the pad's.
//   
//   THE CHIPS ARE LIGHT GRAY. Owner instruction, restated 2026-08-16 after they
//   had gone black and white: "why isn't the keyboard hide and show buttons light
//   grey as was previously instructed?"
//   
//   They went black and white by inheritance, not by decision. Both chips were
//   painted with the PAD's `hairline`, and on 2026-08-16 the pad's default preset
//   became Black & White (padpalette::kPresetBlackWhite) by a separate owner
//   ruling -- "the shipped gray outline ... was asked to be actually black and
//   white". That ruling is about the pad's CONTROLS. The chip is not one of them:
//   CrossPointIOSShim.cpp says so in as many words where it is declared -- "NOT a
//   PadButton and deliberately not in g_pad: it presses no hardware button". So
//   the two instructions do not conflict once the chip stops borrowing a tone
//   meant for the buttons beside it.
//   
//   The level is kPresetCurrent's, +/-1, which IS the gray that shipped before:
//   #D9D9D7 on #FBFBF9 in light, #333333 on #121212 in dark. Taken as a level
//   rather than as those literals so the chip still follows a custom paper -- the
//   rungs are relative to the field, which is the panel's paper.
//   
//   ONE definition for the same reason panelForPrefs above is one: the SHOW chip
//   is SDL and the HIDE chip is UIKit, and tests/chip_tint_source_test.py exists
//   because a divergence between them is invisible to every other test here.
// --- end superseded ----------------------------------------------------------

// The pad's two levels. Delegated to padpalette::shippedLevels so that the SDL
// side (the pad, the SHOW chip) and the UIKit side (the HIDE chip) cannot
// resolve them differently -- which they did, from 2026-08-22 until this was
// written: the shim pinned Accessible and this file went on handing the raw
// stored contrasts to makePaletteOn, so the two chips sat 4-5x apart in
// contrast under a header comment promising one definition.
inline padpalette::Levels padLevelsForPrefs(bool dark) {
  const int d = dark ? 1 : 0;
  return padpalette::shippedLevels(dark, CrossPointPrefs_padOutlineContrast(d),
                                   CrossPointPrefs_padFillContrast(d));
}

inline padpalette::Palette padPaletteForPrefs(bool dark) {
  const padpalette::Levels lv = padLevelsForPrefs(dark);
  return padpalette::makePaletteOn(dark, lv.outline, lv.fill,
                                   panelForPrefs(dark).paper);
}

// The name both chips call, so the two halves cannot drift apart. It is now
// simply the pad's palette.
inline padpalette::Palette chipPaletteForPrefs(bool dark) {
  return padPaletteForPrefs(dark);
}

}  // namespace crosspoint
