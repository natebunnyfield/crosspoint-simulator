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

namespace crosspoint {

// The pair for one appearance. Reads the preset first and only touches the four
// custom hex fields when the preset actually is Custom -- resolve() would
// ignore them otherwise, and this runs per frame on the SDL side.
inline panelpalette::Palette panelForPrefs(bool dark) {
  const int preset = CrossPointPrefs_panelPalettePreset();
  if (preset != panelpalette::kPresetCustom)
    return panelpalette::resolve(preset, dark, panelpalette::kInvalidColor,
                                 panelpalette::kInvalidColor);
  const int d = dark ? 1 : 0;
  return panelpalette::resolve(preset, dark,
                               CrossPointPrefs_panelCustomColor(d, 1),
                               CrossPointPrefs_panelCustomColor(d, 0));
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

inline padpalette::Palette padPaletteForPrefs(bool dark) {
  const int d = dark ? 1 : 0;
  return padpalette::makePaletteOn(dark, CrossPointPrefs_padOutlineContrast(d),
                                   CrossPointPrefs_padFillContrast(d),
                                   panelForPrefs(dark).paper);
}

// The name both chips call, so the two halves cannot drift apart. It is now
// simply the pad's palette.
inline padpalette::Palette chipPaletteForPrefs(bool dark) {
  return padPaletteForPrefs(dark);
}

}  // namespace crosspoint
