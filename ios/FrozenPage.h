#pragma once

// THE PAGE'S TWO APPEARANCES, FROZEN -- and the only place either one is named.
//
// OWNER RULING 2026-08-24: "take out paper and crt settings for now. set them
// to sanguine and india paper and attached image for crt." The image was a
// screenshot of the gun mixer, and the four guns below are read off it.
//
// WHAT "TAKE OUT ... FOR NOW" MEANT HERE. The page-color chip is gone from the
// pad (ios/CrossPointIOSShim.cpp) and nothing on the phone opens either drawer
// any more. THE DRAWERS THEMSELVES ARE INTACT -- CrossPointLightInkPicker.mm,
// CrossPointPaletteMixer.mm, CrossPointPresetList.mm and all of their machinery
// are still compiled, still correct, and still reachable from the diagnostic
// env hooks a QA run uses (CROSSPOINT_SIM_OPEN_INKPICKER / _OPEN_MIXER). What
// was removed is the ENTRY POINT, not the capability: "for now" is explicitly
// reversible, and deleting two working editors to honour a temporary ruling is
// a one-way door this repo does not open.
//
// THE FREEZE DISCIPLINE, copied exactly from ios/CrossPointPrefs.mm's seven
// frozen getters and for the same reason: every consumer below answers from
// THIS FILE and never from NSUserDefaults. An install that stored a different
// ink, a different stock or a different recipe before its control went away
// must not keep rendering it -- and with the control gone there would be no way
// to change it back. That is not hypothetical here: the owner's own store held
// 483835 on F9F5F2 when he ruled, which is neither of the pairs below.
//
// THE INPUTS ARE FROZEN, NOT THE OUTPUTS. Every tone here is DERIVED, by the
// same pure model the drawers drive: the light pair from lightink:: and the
// dark pair from phosphormix::mixBlend. Writing the six resolved hex bytes out
// by hand would be a second record of what the models already say, and a second
// record is what drifted twice on 2026-08-23 (docs/surface-roadmap.md 4e). It
// also means a model retune carries the frozen page with it instead of silently
// leaving it behind.
//
// THE CHECK. At the frozen recipe the mixer's own readout says
//   dark CFD4CC on 171B1B - light 483835 on F9F5F2 - fade 1095 ms
// and darkPair()/darkMix() reproduce exactly that. The light half of that line
// is what the owner had BEFORE this ruling and is deliberately not what
// lightPair() answers -- light freezes at Sanguine on India, 5C332B on F9F3E9.

#include "GunMixCsv.h"
#include "LightInkPalette.h"
#include "PanelPalette.h"
#include "PhosphorMix.h"

namespace frozenpage {

// --- THE LIGHT PAGE: Sanguine ink on India paper ---------------------------
//
// Stated as the picker's own three integers rather than as a pair of hex
// strings, because that is what the drawer would have stored and it is what
// every other light-page consumer needs: the STOCK decides the tooth, the
// formation, the show-through and the wires, none of which a resolved pair can
// answer for. India is a thin, warm, very smooth bible stock -- 1.12x tooth,
// 0.70x formation and 3.0x show-through against the reference sheet.
inline constexpr int kLightInk = lightink::kInkSanguine;
inline constexpr int kLightPaper = lightink::kPaperIndia;
// Full density on a sheet at full strength, which is what an untouched picker
// has always meant. Both still run through the model's clamps below rather than
// being taken as final: those clamps are what hold the 7:1 legibility floor
// against the chosen ink and stock, and a frozen pair that skipped them would
// be a page nobody can read with no control left to fix it.
inline constexpr int kLightDensityRequest = lightink::kDensityMax;
inline constexpr int kLightPaperStrengthRequest = lightink::kPaperStrengthMax;

// --- THE DARK PAGE: a four-gun phosphor blend ------------------------------
//
// NOT a named preset. Owner's screenshot, gun by gun; the mixer's channel order
// is R, G, B, W (ios/CrossPointPaletteMixer.mm kGunLabel).
inline constexpr int kGunPreset[gunmix::kGunCount] = {
    panelpalette::kPresetP38Crt,    // R -- P38 Radar Amber, (Zn,Mg)F2:Mn, Long
    panelpalette::kPresetWhiteCrt,  // G -- P45 White viewfinder, Medium
    panelpalette::kPresetP20Crt,    // B -- P20 Yellow-Green Long, 1-100 ms
    panelpalette::kPresetRedCrt,    // W -- P22R Red, Y2O2S:Eu, Medium
};
inline constexpr int kGunWeight[gunmix::kGunCount] = {19, 88, 17, 36};

// The blend, resolved ONCE. mixBlend is linear-light math over four palettes;
// cheap, but this is asked from the SDL side on a poll, so it is computed on
// first use and kept.
//
// A ZERO-WEIGHT GUN IS AN ABSENT COMPONENT, not a component at zero -- the same
// rule computeGuns applies in the mixer, and the core clamps weights below 1,
// so omission is the only honest zero. All four guns are lit here; the loop
// stays so the shape cannot go wrong if a weight is ever taken to 0.
inline const phosphormix::Result &darkMix() {
  static const phosphormix::Result r = [] {
    phosphormix::Component comps[gunmix::kGunCount];
    int n = 0;
    for (int g = 0; g < gunmix::kGunCount; g++) {
      if (kGunWeight[g] <= 0) continue;
      comps[n].preset = kGunPreset[g];
      comps[n].weight = kGunWeight[g];
      n++;
    }
    return phosphormix::mixBlend(comps, n);
  }();
  return r;
}

// --- the resolved selections -----------------------------------------------

// The light page's selection AFTER the model's two clamps, in the order the
// invariant needs: the paper strength is pinned to its ceiling for the
// requested density first, then the density to its floor at the resulting
// strength. Both carry the sheet DRIFT, because the floor has to hold for the
// darkest leaf the drift can produce and the app freezes drift at the top of
// its range -- so that is every page, not a worst case.
struct LightSelection {
  int ink = kLightInk;
  int paper = kLightPaper;
  int density = kLightDensityRequest;
  int paperStrength = kLightPaperStrengthRequest;
};

inline LightSelection lightSelection() {
  static const LightSelection s = [] {
    LightSelection out;
    const int drift = lightink::kPaperDriftMax;
    out.paperStrength = lightink::clampPaperStrengthPct(
        kLightInk, kLightPaper, kLightDensityRequest,
        kLightPaperStrengthRequest, drift);
    out.density = lightink::clampDensityPct(kLightInk, kLightPaper,
                                            kLightDensityRequest,
                                            out.paperStrength, drift);
    return out;
  }();
  return s;
}

// The two tones each appearance is painted in. Both derived; neither typed.
inline panelpalette::Palette lightPair() {
  static const panelpalette::Palette p = [] {
    const LightSelection s = lightSelection();
    panelpalette::Palette out{};
    lightink::inkAtDensity(s.ink, s.paper, s.density, out.ink, s.paperStrength);
    lightink::paperAtStrength(s.paper, s.paperStrength, out.paper);
    return out;
  }();
  return p;
}

inline panelpalette::Palette darkPair() { return darkMix().dark; }

}  // namespace frozenpage
