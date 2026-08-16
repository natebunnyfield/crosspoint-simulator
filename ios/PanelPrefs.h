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

}  // namespace crosspoint
