#pragma once

// The panel's two tones -- the ink a fully-black source pixel becomes and the
// paper a fully-white one becomes -- plus the presets and the parsing that turn
// an owner's choice into that pair.
//
// PURE AND HOST-TESTABLE, on the same terms as ios/PadPalette.h: no SDL, no
// UIKit, no clock, no I/O, everything constexpr. `tests/panel_palette_test.cpp`
// exercises the whole thing on a Mac or a Linux box with no phone and no
// window. That matters here more than usual, because every failure mode is a
// wrong COLOR, and a wrong color is invisible to a compiler and to every
// existing test in this repo.
//
// --- Why the pair is a dial at all -----------------------------------------
//
// The framebuffer is 1bpp (plus the two AA planes), so the panel has no colors
// of its own: it has a LEVEL, 0..255, and this file says what level 0 and level
// 255 look like. Everything between is interpolated. That is the whole reason
// the intermediate 2-bit gray targets need no separate table -- change the two
// ends and the four grays the panel actually renders move with them, in the
// right proportion, for free. Hardcoding an intermediate would break exactly
// that, so do not.
//
// It is also why INVERSION needs no 255-level flip: the dark palette's
// ink->paper direction already runs light-on-dark, so the same lerp serves both
// polarities. See HalDisplay.cpp's composeGrayscalePreview.
//
// --- The defaults are load-bearing -----------------------------------------
//
// kDefaultLight / kDefaultDark are the exact tones this app has always
// rendered. They are what the Default preset selects, what an untouched install
// gets, and what every desktop build gets (there is no Settings.app on a Mac),
// so a build with this file in it must be pixel-identical to the build before
// it for anyone who never opens the setting. The static_asserts at the bottom
// pin them byte-for-byte; do not "tidy" the hex.

#include <cmath>
#include <cstdint>

namespace panelpalette {

struct Palette {
  uint8_t ink[3];    // what a fully-black source pixel becomes (level 0)
  uint8_t paper[3];  // what a fully-white source pixel becomes (level 255)
};

// THE SHIPPED TONES. Changing either line changes what every existing install
// renders; that is a ruling, not a tidy-up.
inline constexpr Palette kDefaultLight{{0x2D, 0x2D, 0x2D}, {0xFB, 0xFB, 0xF9}};
inline constexpr Palette kDefaultDark{{0xE0, 0xE0, 0xDE}, {0x12, 0x12, 0x12}};

// --- Presets ---------------------------------------------------------------
//
// One row selects BOTH appearances, the way the pad's preset row does: a
// reading surface that changed character when the phone went dark would be a
// worse answer than one that keeps its identity in both. Each preset therefore
// names a light pair and a dark pair, and the dark half is not a numeric
// inversion of the light half -- an inverted sepia is a bruise. They were
// picked as pairs.
//
// Measured sRGB contrast, ink on paper (the same arithmetic PadPalette's ladder
// is built from; tests/panel_palette_test.cpp recomputes all eight):
//
//   Default        13.29:1 light   14.17:1 dark
//   High Contrast  21.00:1 both    -- the gamut ends, no tint at all
//   Sepia          10.23:1 light   12.79:1 dark
//   Cool Gray      13.17:1 light   14.24:1 dark
//   Solarized       4.13:1 light    4.75:1 dark   <-- exempt, see below
//   Green CRT      10.31:1 light   13.50:1 dark
//   Amber CRT      10.13:1 light   10.25:1 dark
//   Nord           10.84:1 light    9.25:1 dark
//   Gruvbox Light  10.22:1 light   10.75:1 dark
//   Latte           7.06:1 light   11.34:1 dark
//   Soft            9.15:1 light    9.47:1 dark
//   Red CRT        10.22:1 light    7.33:1 dark
//   Gray CRT       11.14:1 light   13.92:1 dark
//   Sepia CRT       7.59:1 light   12.51:1 dark
//   Blue CRT       10.18:1 light    7.35:1 dark
//
// None is below 7:1 except Solarized, which is deliberate: this is a page of body text, and the
// dial exists to change its CHARACTER, not to let someone make it unreadable by
// picking from a list. The Custom fields below have no such floor, because a
// typed hex value is an explicit act.
enum Preset : int {
  kPresetCustom = 0,        // read the four hex fields instead
  kPresetDefault = 1,       // the shipped tones; the default, hence pixel-identical
  kPresetHighContrast = 2,  // #000000 on #FFFFFF, and its inverse
  kPresetSepia = 3,         // warm paper, warm-black ink
  // RETIRED 2026-08-17: REPLACED by Reading Cool (18), not deleted. See
  // migratePreset -- a stored 4 follows the replacement forward rather than
  // falling back to Default, because the owner replaced this row rather than
  // removing it. The number itself is never reused.
  kPresetCoolGray = 4,      // retired; do not reuse this number
  // Appended 2026-08-15 by owner ruling. APPEND ONLY: the value persists as an
  // integer in NSUserDefaults, so inserting a row re-points every saved choice
  // at a different palette.
  kPresetSolarized = 5,       // Ethan Schoonover's, both halves, authentic
  kPresetGreenCrt = 6,        // P1 phosphor
  kPresetAmberCrt = 7,        // P3 phosphor
  kPresetNord = 8,            // cool pale minimal
  kPresetGruvboxLight = 9,    // warm pale minimal
  kPresetLatte = 10,          // neutral pale minimal (Catppuccin Latte)
  // Appended 2026-08-16 by owner ruling. Same APPEND-ONLY rule as above.
  kPresetRedCrt = 11,         // P22R phosphor -- see the caveat at its case
  kPresetGrayCrt = 12,        // P4 phosphor
  // Pure grounds, EASED ink. High Contrast's white and black pages without
  // High Contrast's 21:1 -- the owner asked for "a white background and a black
  // background but chill on the contrast" (2026-08-16). The ground is the thing
  // being preserved here, so both papers stay at the gamut ends and only the
  // ink moves inward, to a matched ~9:1 in both halves.
  // RETIRED 2026-08-17: REPLACED by Reading Warm (17). Same treatment as 4.
  kPresetSoft = 13,  // retired; do not reuse this number
  // Appended 2026-08-16 by owner ruling, closing out the CRT group. Same
  // APPEND-ONLY rule as above -- the Settings row ORDER is free and is where
  // the grouping happens, so neither of these had to be inserted anywhere.
  // RETIRED 2026-08-17 by owner ruling ("remove sepia phosphor"). The constant
  // stays and 14 is NEVER REUSED: a preset persists as its integer, so handing
  // 14 to something else would silently change what an install that had chosen
  // Sepia CRT is showing. It is absent from isKnownPreset and from the palette
  // switch, so a stored 14 now resolves to Default -- the same answer every
  // unknown integer gets, which is the one safe landing.
  kPresetSepiaCrt = 14,  // retired; do not reuse this number
  kPresetBlueCrt = 15,   // P11 phosphor
  // Appended 2026-08-17. Asked for as "one more neutral page color that is for
  // optimal reading paragraphs of text on iphone air screen", so it is tuned
  // for an OLED phone reading long-form rather than for a look:
  //
  //   PAPER OFF PURE WHITE. #F0EFEC, not #FFFFFF. An OLED at reading brightness
  //   drives a full-white field hard, and it is the field -- not the glyphs --
  //   that fills the retina for a page of paragraphs. Four levels down from
  //   white is enough to take the glare off and still read as paper.
  //   INK DARKER THAN DEFAULT. #202020 against Default's #2D2D2D. The panel is
  //   two-bit and the glyph edges are antialiased into it, so a darker ink is
  //   what keeps small type crisp once the paper has been dimmed.
  //   BLACK AT NIGHT. #000000 ground, because on OLED that is pixels off: no
  //   backlight bleed, no halation ring around the type, and less power. The
  //   ink is eased to #C2C2C0 rather than white, which is the pairing that
  //   stops light-on-dark type blooming.
  //
  // 14.2:1 light and 11.8:1 dark -- inside the comfortable band rather than at
  // High Contrast's 21:1, which is the ratio that tires eyes over paragraphs.
  kPresetReading = 16,
  // Appended 2026-08-17, replacing Soft and Cool Gray by owner ruling. The same
  // page as Reading with the paper's TEMPERATURE moved and nothing else: all
  // three sit at 13.8-14.3:1 light and ~11.8:1 dark, so switching between them
  // changes the warmth of the sheet and never the legibility. Paper spans (max
  // channel minus min) are 4, 20 and 12 -- far enough apart to tell at a glance,
  // which the first attempt at these was not.
  kPresetReadingWarm = 17,
  kPresetReadingCool = 18,
  // The rest of the phosphors, appended 2026-08-17 ("now add remaining crts").
  // They were held back until the glow existed, because until a page decays at
  // the phosphor's own rate a second green next to P1 is just a second green --
  // see docs/crt-phosphor-presets.md section 9. Now the difference between them
  // is WHEN they stop emitting, which is the thing that made them different
  // machines to sit in front of.
  kPresetGreenLongCrt = 19,  // P39, the long-persistence green
  kPresetGreenFastCrt = 20,  // P31, the oscilloscope green
  kPresetWhiteCrt = 21,      // P45
  kPresetBlueFastCrt = 22,   // P47
  kPresetRedProjCrt = 23,    // P56
  kPresetBlueTvCrt = 24,     // P22B, the blue gun of a color tube
  // P7, the cascade. Appended last because it is the only preset whose TRAIL is
  // a different color from its page -- see kCascadeAfterglow and the tint hook
  // in SimulatorOverlay.
  kPresetCascadeCrt = 25,
  // Appended 2026-08-17 by owner ruling: "be sure to include all possible
  // phosphors", which overturns the §5 near-duplicate rejection recorded in
  // docs/crt-phosphor-presets.md. Some of these paint the SAME PAGE as each
  // other -- P19/P26/P33/P38 are all 590-595 nm fluoride:Mn and derive to
  // identical bytes -- and that is now deliberate: they are distinguished by
  // PERSISTENCE, which the glow renders. Same APPEND-ONLY rule as every block
  // above.
kPresetP2Crt = 26,  // P2 ZnS:Cu(Ag), blue-green, Long
  kPresetP5Crt = 27,  // P5 CaWO4:W, blue, Very Short
  kPresetP6Crt = 28,  // P6 ZnS:Ag+ZnS:CdS:Ag, white, Short
  kPresetP10Crt = 29,  // P10 KCl, green-absorbing scotophor, Long
  kPresetP12Crt = 30,  // P12 Zn(Mg)F2:Mn, orange, Medium/long
  kPresetP13Crt = 31,  // P13 MgSi2O6:Mn, reddish-orange, Medium
  kPresetP14Crt = 32,  // P14 ZnS:Ag on ZnS:CdS:Cu, blue with orange persistence, Medium/long
  kPresetP15Crt = 33,  // P15 ZnO:Zn, blue-green, Extremely Short
  kPresetP16Crt = 34,  // P16 CaMgSi2O6:Ce, blue-purple, Very Short
  kPresetP17Crt = 35,  // P17 ZnO,ZnCdS:Cu, blue-yellow, Blue-Short, Yellow-Long
  kPresetP18Crt = 36,  // P18 CaMgSi2O6:Ti, BeSi2O6:Mn, white, Medium to Short
  kPresetP19Crt = 37,  // P19 (KF,MgF2):Mn, orange-yellow, Long
  kPresetP20Crt = 38,  // P20 (Zn,Cd)S:Ag or (Zn,Cd)S:Cu, yellow-green, 1-100 ms
  kPresetP21Crt = 39,  // P21 MgF2:Mn2+, reddish, not published
  kPresetP22GCrt = 40,  // P22G (Zn,Cd)S:Cu,Al, green, Short
  kPresetP23Crt = 41,  // P23 ZnS:Ag+(Zn,Cd)S:Ag, white, Short
  kPresetP24Crt = 42,  // P24 ZnO:Zn, green, 1-10 us
  kPresetP25Crt = 43,  // P25 CaSi2O6:Pb:Mn, orange, Medium
  kPresetP26Crt = 44,  // P26 (KF,MgF2):Mn, orange, Long
  kPresetP27Crt = 45,  // P27 ZnPO4:Mn, reddish orange, Medium
  kPresetP28Crt = 46,  // P28 (Zn,Cd)S:Cu,Cl, yellow, Medium
  kPresetP33Crt = 47,  // P33 MgF2:Mn, orange, > 1 sec
  kPresetP34Crt = 48,  // P34 not published, bluish green-yellow green, Very Long
  kPresetP35Crt = 49,  // P35 ZnS,ZnSe:Ag, blue-white, Medium Short
  kPresetP38Crt = 50,  // P38 (Zn,Mg)F2:Mn, orange-yellow, Long
  kPresetP40Crt = 51,  // P40 ZnS:Ag+(Zn,Cd)S:Cu, white, Long
  kPresetP43Crt = 52,  // P43 Gd2O2S:Tb, yellow-green, Medium
  kPresetP46Crt = 53,  // P46 Y3Al5O12:Ce, green, Very short (70 ns)
  kPresetP53Crt = 54,  // P53 Y3Al5O12:Tb, yellow-green, Short
  kPresetP55Crt = 55,  // P55 ZnS:Ag,Al, blue, Short
};

// A retired preset that was REPLACED rather than removed. Stored choices follow
// the replacement forward; the integers themselves are still never reused.
//
// This is the difference between the two kinds of retirement in this file.
// Sepia CRT (14) was deleted outright and has nowhere to go, so it lands on
// Default like any unknown integer. Soft and Cool Gray were swapped for the
// warm and cool Reading pages, and an install that had chosen "the cool one"
// should keep having chosen the cool one.
constexpr int migratePreset(int preset) {
  if (preset == kPresetSoft) return kPresetReadingWarm;
  if (preset == kPresetCoolGray) return kPresetReadingCool;
  return preset;
}

// Solarized is DELIBERATELY low contrast -- that is the palette's whole thesis,
// and raising it to clear the 7:1 floor the other rows meet would produce
// something that is no longer Solarized. It is therefore the one named preset
// exempt from that floor, by name rather than by loosening the floor for
// everyone. tests/panel_palette_test.cpp pins both the exemption list and the
// measured ratios, so a future palette cannot join it silently.
constexpr bool isLowContrastByDesign(int preset) {
  return preset == kPresetSolarized;
}

constexpr bool isKnownPreset(int preset) {
  return preset == kPresetCustom || preset == kPresetDefault ||
         preset == kPresetHighContrast || preset == kPresetSepia ||
         preset == kPresetReadingWarm || preset == kPresetSolarized ||
         preset == kPresetGreenCrt || preset == kPresetAmberCrt ||
         preset == kPresetNord || preset == kPresetGruvboxLight ||
         preset == kPresetReadingCool || preset == kPresetGreenLongCrt ||
         preset == kPresetGreenFastCrt || preset == kPresetWhiteCrt ||
         preset == kPresetBlueFastCrt || preset == kPresetRedProjCrt ||
         preset == kPresetBlueTvCrt || preset == kPresetCascadeCrt ||
         preset == kPresetLatte || preset == kPresetRedCrt ||
         preset == kPresetGrayCrt || preset == kPresetReading ||
         preset == kPresetBlueCrt ||
preset == kPresetP2Crt ||
         preset == kPresetP5Crt ||
         preset == kPresetP6Crt ||
         preset == kPresetP10Crt ||
         preset == kPresetP12Crt ||
         preset == kPresetP13Crt ||
         preset == kPresetP14Crt ||
         preset == kPresetP15Crt ||
         preset == kPresetP16Crt ||
         preset == kPresetP17Crt ||
         preset == kPresetP18Crt ||
         preset == kPresetP19Crt ||
         preset == kPresetP20Crt ||
         preset == kPresetP21Crt ||
         preset == kPresetP22GCrt ||
         preset == kPresetP23Crt ||
         preset == kPresetP24Crt ||
         preset == kPresetP25Crt ||
         preset == kPresetP26Crt ||
         preset == kPresetP27Crt ||
         preset == kPresetP28Crt ||
         preset == kPresetP33Crt ||
         preset == kPresetP34Crt ||
         preset == kPresetP35Crt ||
         preset == kPresetP38Crt ||
         preset == kPresetP40Crt ||
         preset == kPresetP43Crt ||
         preset == kPresetP46Crt ||
         preset == kPresetP53Crt ||
         preset == kPresetP55Crt;
}

// The pair a named preset selects. kPresetCustom has no pair of its own -- the
// caller reads the hex fields -- and is answered with Default's, so a miswired
// caller degrades to the shipped look rather than to something unreadable.
// Anything UNKNOWN answers Default's for the same reason: a value from a
// restored backup written by a future build must not produce a blank page.
constexpr Palette presetPalette(int preset, bool dark) {
  switch (preset) {
  case kPresetHighContrast:
    return dark ? Palette{{0xFF, 0xFF, 0xFF}, {0x00, 0x00, 0x00}}
                : Palette{{0x00, 0x00, 0x00}, {0xFF, 0xFF, 0xFF}};
  case kPresetSepia:
    return dark ? Palette{{0xE8, 0xD9, 0xBC}, {0x1C, 0x17, 0x10}}
                : Palette{{0x3B, 0x32, 0x28}, {0xF2, 0xE7, 0xD0}};
  // Reading, with the paper pulled COOL. 13.84:1 light, 11.80:1 dark -- the
  // same band as the other two, so this is a temperature choice and not a
  // legibility one. Replaced Cool Gray, whose job it inherits.
  case kPresetReadingCool:
    return dark ? Palette{{0xBC, 0xC3, 0xCA}, {0x00, 0x00, 0x00}}
                : Palette{{0x1D, 0x21, 0x26}, {0xE8, 0xEE, 0xF4}};
  // Solarized, unmodified: base00 on base3 light, base0 on base03 dark -- the
  // body-text pairing Schoonover specifies. One row carries both variants
  // rather than two rows carrying one each, because every preset's dark half
  // must be light-on-dark (a "Solarized Light" row that stayed light would hand
  // back a blinding page at night, and the polarity assertion would reject it).
  // So picking this gives Solarized Light by day and Solarized Dark by night.
  case kPresetSolarized:
    return dark ? Palette{{0x83, 0x94, 0x96}, {0x00, 0x2B, 0x36}}
                : Palette{{0x65, 0x7B, 0x83}, {0xFD, 0xF6, 0xE3}};
  // P1 phosphor. The DARK half is the authentic article -- green on a black
  // tube. The light half cannot be, since a lit CRT has no light mode, so it
  // keeps the hue instead: deep phosphor green on a paper tinted the same way.
  case kPresetGreenCrt:
    return dark ? Palette{{0x33, 0xFF, 0x33}, {0x00, 0x1A, 0x00}}
                : Palette{{0x0B, 0x3D, 0x0B}, {0xDC, 0xEF, 0xD8}};
  // P3 phosphor, same construction as the green.
  case kPresetAmberCrt:
    return dark ? Palette{{0xFF, 0xB0, 0x00}, {0x1A, 0x10, 0x00}}
                : Palette{{0x4A, 0x2E, 0x00}, {0xF5, 0xE6, 0xC8}};
  case kPresetNord:
    return dark ? Palette{{0xD8, 0xDE, 0xE9}, {0x2E, 0x34, 0x40}}
                : Palette{{0x2E, 0x34, 0x40}, {0xEC, 0xEF, 0xF4}};
  case kPresetGruvboxLight:
    return dark ? Palette{{0xEB, 0xDB, 0xB2}, {0x28, 0x28, 0x28}}
                : Palette{{0x3C, 0x38, 0x36}, {0xFB, 0xF1, 0xC7}};
  case kPresetLatte:
    return dark ? Palette{{0xCD, 0xD6, 0xF4}, {0x1E, 0x1E, 0x2E}}
                : Palette{{0x4C, 0x4F, 0x69}, {0xEF, 0xF1, 0xF5}};
  // P22R (Y2O2S:Eu), CIE x=0.647 y=0.343, peak 611 nm -- measured by Phosphor
  // Technology Ltd, and corroborated by the EBU/Rec.709 red primary at
  // (0.640, 0.330), which IS this phosphor standardized.
  //
  // BE HONEST ABOUT WHAT THIS ROW IS. A red monochrome TERMINAL never shipped:
  // Wikipedia's Monochrome monitor article enumerates the options as green
  // (P1), amber (P3) and white (P4) and names no red, and no red P-number in
  // the JEDEC list carries "data display" as its application. What did exist as
  // a physically monochrome red CRT is the RED TUBE OF A THREE-TUBE PROJECTOR
  // (P56, Y2O3:Eu, x=0.650 y=0.346 -- the same europium red one designation
  // over), plus the red gun of every color tube and a beam-penetration display
  // driven at low anode voltage. So this is a real phosphor rendered as a page,
  // not a terminal anyone sat in front of. The radar oranges (P19/P26/P33/P38)
  // were considered and rejected: they emit at 590-595 nm, which is Amber CRT's
  // territory, not red.
  //
  // AND THE DARK HALF CANNOT BE THE REAL COLOR. Red carries only 0.2126 of the
  // sRGB luminance coefficient, so #FF1B00 -- P22R at the brightest luminance
  // sRGB can render that chromaticity -- measures 5.41:1 against PURE BLACK.
  // Not 7:1 on any tube, at any tint, ever. The floor therefore forces the
  // trace 14.9% toward D65 in linear light (same dominant wavelength, lower
  // purity -- which is also what a real trace does when the beam saturates the
  // phosphor), giving #FF6F6C at 7.33:1. The light half has no such problem
  // and keeps full purity in the ink.
  case kPresetRedCrt:
    return dark ? Palette{{0xFF, 0x6F, 0x6C}, {0x1A, 0x03, 0x00}}
                : Palette{{0x6E, 0x05, 0x00}, {0xFF, 0xE2, 0xE1}};
  // P4, the monochrome TV and monitor white -- "page white", and the one the
  // sources agree reads BLUISH next to a warmer phosphor. There is no published
  // CIE point for P4 itself; what is published is the JEDEC white region every
  // P4 screen must fall inside, a parallelogram with corners (0.273, 0.282),
  // (0.267, 0.303), (0.286, 0.326) and (0.290, 0.303) referenced to 6500 K
  // +7 MPCD (US4512912). Its centroid, (0.279, 0.3035), is what this row uses;
  // note it sits below and left of D65 (0.3127, 0.3290), so JEDEC white is
  // DEFINITIONALLY cooler than daylight -- the blue cast is the specification,
  // not a liberty. A white data-display CRT patented separately (US4377768)
  // puts its screen at (0.275, 0.295), ~10,600 K, which agrees.
  //
  // Called Gray rather than White because the page it makes is a gray page. It
  // is deliberately a stronger cool tint than Cool Gray, which is a neutral
  // page that merely leans cold: a P4 page derived honestly from the JEDEC
  // centroid lands right on top of Cool Gray unless the tint is allowed to
  // show, and two rows that paint nearly the same page is a control that
  // appears to do nothing. Paper spread (max channel minus min) is 24 here
  // against Cool Gray's 7 and Green CRT's 23 -- tinted like the family, three
  // times the neutral row.
  //
  // THE LIGHT PAPER IS PULLED BACK ON PURPOSE, and the first attempt is worth
  // recording because it renders wrong in a way arithmetic does not show. The
  // dark ink is the JEDEC centroid at the brightest luminance sRGB can carry
  // it (#C9E7FF); tinting THAT to the family's paper luminance needs only an
  // 18% blend toward D65 and yields #D4ECFF, which measures a perfectly legal
  // 10.23:1 and reads on the panel as a SKY BLUE page, not a gray one. Blending
  // 52.5% instead gives #E7F4FF at 11.14:1 -- the same hue direction, a quarter
  // of the saturation, and a page that looks like a white-phosphor tube.
  // Green and Amber never hit this because their phosphors sit so far outside
  // sRGB that reaching page luminance desaturates them anyway.
  case kPresetGrayCrt:
    return dark ? Palette{{0xC9, 0xE7, 0xFF}, {0x14, 0x18, 0x1A}}
                : Palette{{0x2D, 0x35, 0x3C}, {0xE7, 0xF4, 0xFF}};
  // Pure white and pure black grounds, ink eased off the opposite end. NOT a
  // softened Default: Default's paper is #FBFBF9 and its ink #2D2D2D, so it is
  // already off both ends. This one keeps the ends and spends the whole
  // relaxation on the ink.
  // Reading, with the paper pulled WARM -- the cream of a paperback rather than
  // the amber of the CRT rows. 14.26:1 light, 11.70:1 dark. Replaced Soft.
  case kPresetReadingWarm:
    return dark ? Palette{{0xC6, 0xC1, 0xB6}, {0x00, 0x00, 0x00}}
                : Palette{{0x21, 0x1E, 0x19}, {0xF4, 0xED, 0xE0}};
  // SEPIA IS NOT A PHOSPHOR, and this row does not pretend otherwise. There is
  // no sepia P-number: sepia is a PHOTOGRAPHIC TONING process, in which the
  // metallic silver of a finished black-and-white print is converted to silver
  // sulfide -- done for archival life (the sulfide is "at least 50% more
  // stable than silver", Wikipedia, Photographic print toning) and warm brown
  // as a side effect. Wikipedia's Monochrome monitor article enumerates the
  // screen colors as green (P1), amber (P3) and white (P4) and names no sepia;
  // int10h's monochrome survey names none either. So this row is a TONED TUBE:
  // the P4 monochrome page put through the toning bath, which is a thing you
  // could actually have done to a photograph of a screen, rather than an
  // invented phosphor.
  //
  // THE DARK HALF CANNOT BE BROWN, and that is physics rather than a gamut
  // limit. "Brown exists as a color perception only in the presence of a
  // brighter color contrast" (Wikipedia, Brown) -- brown IS dark orange, seen
  // against something brighter. A trace on an unlit tube is the brightest
  // thing in the frame, so it has nothing to be dark against and simply reads
  // as orange. A toned print's bright end is a warm cream, so the dark half
  // takes the toned HIGHLIGHT (#FFCCAF) rather than a sepia that cannot exist.
  // The sepia hue driven to full emission would be #FF9D3B, which is an orange
  // dE2000 10.4 from Amber CRT's #FFB000 -- i.e. Amber with extra steps.
  //
  // The tone axis is the sepia pigment itself, #704214 (Maerz and Paul, A
  // Dictionary of Color, 1930, via Wikipedia's Sepia (color)). Two deliberate
  // departures from the other CRT rows, both taken to keep this row from
  // painting a page one of its neighbours already paints:
  //
  //   * The light INK sits at luminance 0.060, not the family's 0.034. Toning
  //     tones the shadows too, so a toned print's dark end is a BROWN, not a
  //     black -- and at the family's ink luminance the sepia axis lands on
  //     #54300C, dE2000 4.2 from Amber CRT's #4A2E00, which is a duplicate.
  //     Lifting it to #663B11 costs contrast (7.59:1) and buys dE2000 7.3.
  //   * The light PAPER is derived from the toned highlight, not from the
  //     pigment. Blending #704214 up to page luminance washes the hue out
  //     entirely -- #E9E7E5, channel spread 4, a NEUTRAL page. This is the
  //     mirror of the trap Gray CRT hit: there the honest derivation was too
  //     saturated, here it is too weak, and both were only visible in pixels.
  //
  // Honest about the result: at dE2000 10.3 from Sepia's paper and 10.5 from
  // Amber CRT's it is more distinct from both than THEY are from each other
  // (2.4), but the warm quadrant of this list is crowded and a careful eye
  // will group all three.
  case kPresetReading:
    return dark ? Palette{{0xC2, 0xC2, 0xC0}, {0x00, 0x00, 0x00}}
                : Palette{{0x20, 0x20, 0x20}, {0xF0, 0xEF, 0xEC}};
  // P11 (ZnS:Ag,Cl or ZnS:Zn), CIE x=0.147 y=0.076, peak 460 nm -- Phosphor
  // Technology Ltd grade BE for the chromaticity, Wikipedia's phosphor table
  // for the composition and the application: "Display tubes and VFDs;
  // Oscilloscopes (for fast photographic recording)". Blue was the
  // PHOTOGRAPHIC phosphor, because blue is where film is most sensitive.
  //
  // Same honesty as Red CRT: no blue monochrome TERMINAL shipped either. What
  // P11 was is a real display-tube phosphor and the same ZnS:Ag chemistry as
  // the blue gun of every color tube (P22B). A page, not a machine anyone sat
  // in front of.
  //
  // AND THE FLOOR BITES HARDER HERE THAN ANYWHERE. Blue carries only 0.0722 of
  // the sRGB luminance coefficient -- a third of red's 0.2126. P11 rendered at
  // the brightest luminance sRGB can carry that chromaticity is #0038FF, whose
  // relative luminance is 0.1005, so against PURE BLACK it measures 3.01:1.
  // Not 7:1, not 5:1, not on any tube at any tint. The trace is therefore
  // blended 25.8% toward D65 in linear light -- the same construction Red CRT
  // used, and the same physical excuse (a saturating beam loses purity) --
  // giving #8B92FF at 7.35:1, a hair above Red CRT's 7.33:1.
  // The five added 2026-08-17. Each derived the same way as the rows above --
  // published CIE -> xyY at Y=1 -> XYZ -> linear sRGB -> normalise -> encode,
  // then lifted toward white until it clears the ~10:1 band the CRT family sits
  // in, which is the treatment Red CRT already needed.
  //
  // P39 has NO published chromaticity, and takes P1's: it is Zn2SiO4:Mn,As at
  // 525 nm against P1's Zn2SiO4:Mn at 525 nm -- the same emitter with an
  // arsenic co-activator added for persistence. Same light, longer tail, which
  // is exactly why it belongs next to P1 rather than instead of it.
  case kPresetGreenLongCrt:
    return dark ? Palette{{0x00, 0xFF, 0x00}, {0x00, 0x27, 0x00}}
                : Palette{{0x00, 0x4A, 0x00}, {0xF1, 0xFF, 0xF1}};
  case kPresetGreenFastCrt:
    return dark ? Palette{{0x3D, 0xFF, 0x6F}, {0x03, 0x27, 0x0A}}
                : Palette{{0x0B, 0x4A, 0x1B}, {0xF2, 0xFF, 0xF3}};
  case kPresetWhiteCrt:
    return dark ? Palette{{0xB6, 0xEF, 0xFF}, {0x18, 0x23, 0x27}}
                : Palette{{0x30, 0x42, 0x48}, {0xF8, 0xFD, 0xFF}};
  case kPresetBlueFastCrt:
    return dark ? Palette{{0xB0, 0xB4, 0xFF}, {0x03, 0x05, 0x27}}
                : Palette{{0x1D, 0x2B, 0x99}, {0xF2, 0xF2, 0xFF}};
  case kPresetRedProjCrt:
    return dark ? Palette{{0xFF, 0xA5, 0xA4}, {0x27, 0x01, 0x00}}
                : Palette{{0x7B, 0x08, 0x00}, {0xFF, 0xF1, 0xF1}};
  case kPresetBlueTvCrt:
    return dark ? Palette{{0xAF, 0xB0, 0xFF}, {0x00, 0x00, 0x27}}
                : Palette{{0x00, 0x09, 0xA9}, {0xF1, 0xF1, 0xFF}};
  // P7 is a CASCADE: a ZnS:Ag flash on a (Zn,Cd)S:Cu layer, and the table calls
  // its fluorescence "Blue-White" rather than blue. Neither layer has a
  // published chromaticity here, so both are borrowed on CHEMISTRY rather than
  // guessed -- the flash from P11 (ZnS:Ag, same activator) pulled well toward
  // white, and the persistent layer's hue from P31 (ZnS:Cu, the same copper
  // activator, with cadmium shifting it yellower).
  //
  // The page is therefore the FLASH; what it decays to is the afterglow tint
  // below, which is the whole point of the row.
case kPresetP2Crt:  // P2, 10.1:1 / 13.6:1
    return dark ? Palette{{0x00, 0xFF, 0x6A}, {0x00, 0x19, 0x05}}
                : Palette{{0x00, 0x48, 0x19}, {0xE1, 0xFF, 0xE5}};
  case kPresetP5Crt:  // P5, 10.0:1 / 10.0:1
    return dark ? Palette{{0xBF, 0xA8, 0xFF}, {0x07, 0x00, 0x19}}
                : Palette{{0x46, 0x00, 0x90}, {0xE8, 0xE1, 0xFF}};
  case kPresetP6Crt:  // P6, 10.0:1 / 14.0:1
    return dark ? Palette{{0xBF, 0xDC, 0xFF}, {0x10, 0x14, 0x19}}
                : Palette{{0x35, 0x3E, 0x4A}, {0xF1, 0xF7, 0xFF}};
  case kPresetP10Crt:  // P10, 11.9:1 / 10.0:1
    return dark ? Palette{{0xC9, 0xB6, 0xDE}, {0x14, 0x11, 0x19}}
                : Palette{{0x3A, 0x23, 0x52}, {0xF2, 0xF0, 0xEA}};
  case kPresetP12Crt:  // P12, 10.1:1 / 10.3:1
    return dark ? Palette{{0xFF, 0xA4, 0x72}, {0x19, 0x08, 0x00}}
                : Palette{{0x5A, 0x2C, 0x04}, {0xFF, 0xE9, 0xE1}};
  case kPresetP13Crt:  // P13, 10.0:1 / 10.0:1
    return dark ? Palette{{0xFF, 0x9B, 0xA5}, {0x19, 0x00, 0x03}}
                : Palette{{0x70, 0x00, 0x1D}, {0xFF, 0xE1, 0xE3}};
  case kPresetP14Crt:  // P14, 10.0:1 / 10.1:1
    return dark ? Palette{{0xD3, 0xA3, 0xFF}, {0x0F, 0x02, 0x19}}
                : Palette{{0x4E, 0x1B, 0x6E}, {0xF0, 0xE3, 0xFF}};
  case kPresetP15Crt:  // P15, 10.1:1 / 14.9:1
    return dark ? Palette{{0x00, 0xFF, 0xCA}, {0x00, 0x19, 0x12}}
                : Palette{{0x00, 0x47, 0x37}, {0xE1, 0xFF, 0xF3}};
  case kPresetP16Crt:  // P16, 10.0:1 / 10.0:1
    return dark ? Palette{{0xBA, 0xA9, 0xFF}, {0x05, 0x00, 0x19}}
                : Palette{{0x3F, 0x00, 0x96}, {0xE6, 0xE1, 0xFF}};
  case kPresetP17Crt:  // P17, 10.0:1 / 12.4:1
    return dark ? Palette{{0xDF, 0xB9, 0xFF}, {0x15, 0x0F, 0x19}}
                : Palette{{0x43, 0x36, 0x4E}, {0xF8, 0xF0, 0xFF}};
  case kPresetP18Crt:  // P18, 10.0:1 / 14.8:1
    return dark ? Palette{{0xCB, 0xE4, 0xFF}, {0x12, 0x15, 0x19}}
                : Palette{{0x37, 0x3F, 0x48}, {0xF3, 0xF9, 0xFF}};
  case kPresetP19Crt:  // P19, 10.1:1 / 10.3:1
    return dark ? Palette{{0xFF, 0xA4, 0x72}, {0x19, 0x08, 0x00}}
                : Palette{{0x5A, 0x2C, 0x04}, {0xFF, 0xE9, 0xE1}};
  case kPresetP20Crt:  // P20, 10.1:1 / 14.9:1
    return dark ? Palette{{0x7C, 0xFF, 0x00}, {0x07, 0x19, 0x00}}
                : Palette{{0x1E, 0x47, 0x00}, {0xE7, 0xFF, 0xE1}};
  case kPresetP21Crt:  // P21, 10.0:1 / 10.0:1
    return dark ? Palette{{0xFF, 0x9D, 0x96}, {0x19, 0x02, 0x01}}
                : Palette{{0x68, 0x18, 0x0A}, {0xFF, 0xE3, 0xE1}};
  case kPresetP22GCrt:  // P22G, 10.1:1 / 14.6:1
    return dark ? Palette{{0x00, 0xFF, 0x97}, {0x00, 0x19, 0x0A}}
                : Palette{{0x00, 0x48, 0x27}, {0xE1, 0xFF, 0xEB}};
  case kPresetP23Crt:  // P23, 10.1:1 / 16.1:1
    return dark ? Palette{{0xEA, 0xF1, 0xFF}, {0x16, 0x17, 0x19}}
                : Palette{{0x3E, 0x40, 0x45}, {0xFA, 0xFC, 0xFF}};
  case kPresetP24Crt:  // P24, 10.1:1 / 14.9:1
    return dark ? Palette{{0x00, 0xFF, 0xC7}, {0x00, 0x19, 0x11}}
                : Palette{{0x00, 0x47, 0x36}, {0xE1, 0xFF, 0xF3}};
  case kPresetP25Crt:  // P25, 10.0:1 / 10.0:1
    return dark ? Palette{{0xFF, 0x9C, 0x9B}, {0x19, 0x01, 0x01}}
                : Palette{{0x6C, 0x0F, 0x0C}, {0xFF, 0xE2, 0xE1}};
  case kPresetP26Crt:  // P26, 10.0:1 / 10.0:1
    return dark ? Palette{{0xFF, 0xA1, 0x84}, {0x19, 0x06, 0x01}}
                : Palette{{0x5E, 0x26, 0x06}, {0xFF, 0xE6, 0xE1}};
  case kPresetP27Crt:  // P27, 10.0:1 / 10.0:1
    return dark ? Palette{{0xFF, 0x9B, 0xA5}, {0x19, 0x00, 0x02}}
                : Palette{{0x70, 0x00, 0x1D}, {0xFF, 0xE1, 0xE3}};
  case kPresetP28Crt:  // P28, 10.1:1 / 13.2:1
    return dark ? Palette{{0xFF, 0xC6, 0x00}, {0x19, 0x11, 0x00}}
                : Palette{{0x4D, 0x39, 0x00}, {0xFF, 0xF2, 0xE1}};
  case kPresetP33Crt:  // P33, 10.1:1 / 10.3:1
    return dark ? Palette{{0xFF, 0xA4, 0x72}, {0x19, 0x08, 0x00}}
                : Palette{{0x5A, 0x2C, 0x04}, {0xFF, 0xE9, 0xE1}};
  case kPresetP34Crt:  // P34, 10.1:1 / 14.7:1
    return dark ? Palette{{0x00, 0xFF, 0xA8}, {0x00, 0x19, 0x0D}}
                : Palette{{0x00, 0x48, 0x2D}, {0xE1, 0xFF, 0xED}};
  case kPresetP35Crt:  // P35, 10.1:1 / 12.5:1
    return dark ? Palette{{0x9E, 0xC9, 0xFF}, {0x0B, 0x11, 0x19}}
                : Palette{{0x2E, 0x3C, 0x4F}, {0xEC, 0xF3, 0xFF}};
  case kPresetP38Crt:  // P38, 10.1:1 / 10.3:1
    return dark ? Palette{{0xFF, 0xA4, 0x72}, {0x19, 0x08, 0x00}}
                : Palette{{0x5A, 0x2C, 0x04}, {0xFF, 0xE9, 0xE1}};
  case kPresetP40Crt:  // P40, 10.1:1 / 16.5:1
    return dark ? Palette{{0xD2, 0xFC, 0xFF}, {0x13, 0x19, 0x19}}
                : Palette{{0x37, 0x43, 0x44}, {0xF5, 0xFE, 0xFF}};
  case kPresetP43Crt:  // P43, 10.0:1 / 14.5:1
    return dark ? Palette{{0x00, 0xFF, 0x5B}, {0x00, 0x19, 0x03}}
                : Palette{{0x00, 0x48, 0x14}, {0xE1, 0xFF, 0xE4}};
  case kPresetP46Crt:  // P46, 10.1:1 / 14.6:1
    return dark ? Palette{{0x00, 0xFF, 0x97}, {0x00, 0x19, 0x0A}}
                : Palette{{0x00, 0x48, 0x27}, {0xE1, 0xFF, 0xEB}};
  case kPresetP53Crt:  // P53, 10.0:1 / 14.5:1
    return dark ? Palette{{0x00, 0xFF, 0x63}, {0x00, 0x19, 0x04}}
                : Palette{{0x00, 0x48, 0x16}, {0xE1, 0xFF, 0xE5}};
  case kPresetP55Crt:  // P55, 10.0:1 / 10.0:1
    return dark ? Palette{{0xBC, 0xA9, 0xFF}, {0x06, 0x00, 0x19}}
                : Palette{{0x41, 0x00, 0x94}, {0xE6, 0xE1, 0xFF}};
  case kPresetCascadeCrt:
    return dark ? Palette{{0xC4, 0xC6, 0xFF}, {0x00, 0x03, 0x27}}
                : Palette{{0x00, 0x22, 0xA9}, {0xF1, 0xF2, 0xFF}};
  case kPresetBlueCrt:
    return dark ? Palette{{0x8B, 0x92, 0xFF}, {0x00, 0x06, 0x1A}}
                : Palette{{0x00, 0x1F, 0x9E}, {0xE5, 0xE7, 0xFF}};
  case kPresetDefault:
  case kPresetCustom:
  default:
    return dark ? kDefaultDark : kDefaultLight;
  }
}

// --- Custom colors ---------------------------------------------------------
//
// A HEX STRING, NOT A COLOR WELL, and that is a platform limit rather than a
// choice: a Settings.bundle has exactly six specifier types and none of them is
// a color picker. PSTextFieldSpecifier is the only one that can carry an
// arbitrary color, so Custom is four text fields. See ios/Settings.bundle.
//
// Accepts "RRGGBB", "#RRGGBB" and "0xRRGGBB", either case, with surrounding
// whitespace. Returns 0xRRGGBB packed, or kInvalidColor for anything else --
// including an empty field, which is what a text field the owner cleared holds.
// The caller substitutes the default for an invalid value, so a typo shows the
// shipped tone rather than a black page.
//
// Deliberately NOT accepting 3-digit shorthand: #FFF and #FFFFFF are the same
// color to a web browser, and someone typing three digits here has more likely
// mistyped six.
inline constexpr int kInvalidColor = -1;

constexpr int hexDigit(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  return -1;
}

constexpr bool isSpace(char c) {
  return c == ' ' || c == '\t' || c == '\n' || c == '\r';
}

constexpr int parseHexRgb(const char *s) {
  if (!s) return kInvalidColor;
  while (isSpace(*s)) s++;
  if (*s == '#') {
    s++;
  } else if (s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) {
    s += 2;
  }
  int value = 0;
  for (int i = 0; i < 6; i++) {
    const int d = hexDigit(s[i]);
    if (d < 0) return kInvalidColor;
    value = (value << 4) | d;
  }
  const char *tail = s + 6;
  while (isSpace(*tail)) tail++;
  if (*tail != '\0') return kInvalidColor;
  return value;
}

constexpr uint32_t pack(const uint8_t (&rgb)[3]) {
  return (static_cast<uint32_t>(rgb[0]) << 16) |
         (static_cast<uint32_t>(rgb[1]) << 8) | static_cast<uint32_t>(rgb[2]);
}

constexpr void unpackInto(uint32_t packed, uint8_t (&rgb)[3]) {
  rgb[0] = static_cast<uint8_t>((packed >> 16) & 0xFF);
  rgb[1] = static_cast<uint8_t>((packed >> 8) & 0xFF);
  rgb[2] = static_cast<uint8_t>(packed & 0xFF);
}

// Resolve a preset plus the two custom colors for ONE appearance into the pair
// actually painted. `customInk` / `customPaper` are packed 0xRRGGBB or
// kInvalidColor; they are consulted only when the preset is Custom, and each is
// substituted INDEPENDENTLY -- a valid ink beside an unparseable paper still
// gives the owner their ink on the default paper, rather than throwing both
// away over one typo.
constexpr Palette resolve(int preset, bool dark, int customInk,
                          int customPaper) {
  // Replaced presets follow their replacement before anything else looks at the
  // number. Done HERE, in the one function every consumer goes through, rather
  // than at each caller -- the picker, the cycle button and the page would
  // otherwise have to remember separately, and the one that forgot would show a
  // different palette from the others.
  preset = migratePreset(preset);
  Palette p = presetPalette(isKnownPreset(preset) ? preset : kPresetDefault,
                            dark);
  if (preset != kPresetCustom) return p;
  if (customInk >= 0) unpackInto(static_cast<uint32_t>(customInk), p.ink);
  if (customPaper >= 0) unpackInto(static_cast<uint32_t>(customPaper), p.paper);
  return p;
}

// --- The pixel ------------------------------------------------------------
//
// level: 0 = ink, 255 = paper (the pre-inversion grayscale convention the
// framebuffer and the AA planes are written in). Returns opaque 0xAARRGGBB.
//
// THE INTEGER ARITHMETIC IS THE CONTRACT, not an implementation detail. It is
// exactly what HalDisplay's panelColor did before this file existed, so the
// default palette reproduces every previously-shipped pixel byte-for-byte --
// including the intermediate 2-bit grays, which are the levels most likely to
// drift if anyone rewrites this in floating point. Truncating division, no
// rounding, no gamma.
constexpr uint32_t colorForLevel(uint8_t level, const Palette &p) {
  uint32_t argb = 0xFF000000u;
  for (int c = 0; c < 3; c++) {
    const uint8_t v = static_cast<uint8_t>(
        p.ink[c] + (static_cast<int>(p.paper[c]) - p.ink[c]) * level / 255);
    argb |= static_cast<uint32_t>(v) << (16 - 8 * c);
  }
  return argb;
}

// THE SAME LEVEL, BLENDED AS LIGHT RATHER THAN AS CODE VALUES.
//
// Reported from the phone against build 85: "the antialiasing on the sans serif
// fonts looks bad in crt". It is, and the reason is the line above.
//
// An antialiased edge pixel is a pixel the glyph only PARTLY covers, and the
// panel encodes that coverage as a level. On a phosphor, half coverage means
// half the light -- and light adds linearly, while sRGB code values do not. The
// integer lerp above therefore under-lights every edge pixel on a dark page: for
// the cascade's dark pair (C4C6FF ink on 000327 paper) level 128 comes out at
// code 98 where half the light is code 146. Nearly a third of the ramp is
// missing, so stems get a hard fringe instead of a soft one -- worst on a sans
// serif, whose long straight verticals are almost entirely edge pixels at these
// sizes, and which has no bracketing to hide it.
//
// So: decode both ends to linear light, mix THERE, re-encode. The endpoints are
// untouched by construction (mixing 0% or 100% of anything returns it exactly),
// which is what keeps a palette's own two tones exact while its ramp changes.
//
// NOT the default path, and not constexpr. colorForLevel above stays the
// byte-for-byte contract for every e-ink palette -- a real e-ink panel's grays
// are pigment, not emission, and its shipped look must not move. This applies
// where the page claims to be a tube. HalDisplay caches the 256-entry ramp per
// palette, so the transfer function runs 768 times per palette change and never
// per pixel.
inline float srgbToLinear(float c) {
  return c <= 0.04045f ? c / 12.92f : std::pow((c + 0.055f) / 1.055f, 2.4f);
}
inline float linearToSrgb(float c) {
  return c <= 0.0031308f ? c * 12.92f
                         : 1.055f * std::pow(c, 1.0f / 2.4f) - 0.055f;
}

inline uint32_t colorForLevelEmissive(uint8_t level, const Palette &p) {
  const float t = static_cast<float>(level) / 255.0f;
  uint32_t argb = 0xFF000000u;
  for (int c = 0; c < 3; c++) {
    const float ink = srgbToLinear(static_cast<float>(p.ink[c]) / 255.0f);
    const float paper = srgbToLinear(static_cast<float>(p.paper[c]) / 255.0f);
    const float mixed = ink + (paper - ink) * t;
    float out = linearToSrgb(mixed) * 255.0f + 0.5f;
    if (out < 0.0f) out = 0.0f;
    if (out > 255.0f) out = 255.0f;
    argb |= static_cast<uint32_t>(out) << (16 - 8 * c);
  }
  return argb;
}

// --- Guards ----------------------------------------------------------------
//
// The Default preset and an untouched Custom must both be the shipped tones, or
// the "nothing changes for someone who never opens the setting" promise is
// broken silently and in pixels.
static_assert(presetPalette(kPresetDefault, false).paper[0] == 0xFB &&
                  presetPalette(kPresetDefault, false).paper[1] == 0xFB &&
                  presetPalette(kPresetDefault, false).paper[2] == 0xF9 &&
                  presetPalette(kPresetDefault, false).ink[0] == 0x2D &&
                  presetPalette(kPresetDefault, false).ink[1] == 0x2D &&
                  presetPalette(kPresetDefault, false).ink[2] == 0x2D,
              "Default (light) must be the shipped 2D2D2D-on-FBFBF9");
static_assert(presetPalette(kPresetDefault, true).paper[0] == 0x12 &&
                  presetPalette(kPresetDefault, true).paper[1] == 0x12 &&
                  presetPalette(kPresetDefault, true).paper[2] == 0x12 &&
                  presetPalette(kPresetDefault, true).ink[0] == 0xE0 &&
                  presetPalette(kPresetDefault, true).ink[1] == 0xE0 &&
                  presetPalette(kPresetDefault, true).ink[2] == 0xDE,
              "Default (dark) must be the shipped E0E0DE-on-121212");
static_assert(resolve(kPresetCustom, false, kInvalidColor, kInvalidColor)
                      .paper[0] == 0xFB &&
                  resolve(kPresetCustom, false, kInvalidColor, kInvalidColor)
                          .ink[0] == 0x2D,
              "Custom with both fields unparseable must fall back to the "
              "shipped tones, not to black on black");
static_assert(resolve(999, false, kInvalidColor, kInvalidColor).ink[0] == 0x2D,
              "an unknown preset must resolve as Default");

// The two ends of the ramp are the palette itself, and the midpoint is the
// midpoint. If any of these three moves, so has every gray on the panel.
static_assert(colorForLevel(0, kDefaultLight) == 0xFF2D2D2Du,
              "level 0 must be the ink exactly");
static_assert(colorForLevel(255, kDefaultLight) == 0xFFFBFBF9u,
              "level 255 must be the paper exactly");
// Truncating division, spelled out: 45 + (251-45)*128/255 = 148 on R and G,
// 45 + (249-45)*128/255 = 147 on B. A rewrite in floating point rounds the
// first to 148 and the second to 148 too, and the whole page shifts a level.
static_assert(colorForLevel(128, kDefaultLight) == 0xFF949493u,
              "the midpoint gray must stay integer-truncated");

static_assert(parseHexRgb("FBFBF9") == 0xFBFBF9, "bare hex");
static_assert(parseHexRgb("#fbfbf9") == 0xFBFBF9, "leading # and lowercase");
static_assert(parseHexRgb("0xFBFBF9") == 0xFBFBF9, "0x prefix");
static_assert(parseHexRgb("  FBFBF9  ") == 0xFBFBF9, "surrounding whitespace");
static_assert(parseHexRgb("") == kInvalidColor, "an empty field is not a color");
static_assert(parseHexRgb("FFF") == kInvalidColor, "no 3-digit shorthand");
static_assert(parseHexRgb("FBFBF9F") == kInvalidColor, "too long");
static_assert(parseHexRgb("GGGGGG") == kInvalidColor, "not hex");
static_assert(parseHexRgb(nullptr) == kInvalidColor, "null is not a color");

// --- What the presets are CALLED, and the order they are offered in --------
//
// Until 2026-08-17 the names existed only as row titles in
// ios/Settings.bundle/Root.plist, which was fine while Settings.app was the
// only picker. It is not any more: the in-app palette picker needs the same
// names in the same order, and two hand-kept lists of fifteen rows drift.
//
// The ORDER here is the display order, grouped by family, and it is
// deliberately not the enum order -- a preset persists as its integer, so the
// enum can only ever be appended to, while the offered order is free to be
// whatever reads best. That separation is the whole reason a saved choice
// survives a re-grouping.
//
// Custom is not in this table. It has no tones of its own until the four hex
// fields are filled, so it has nothing to preview and is presented separately.
struct PresetInfo {
  int preset;
  const char *family;  // the group heading it sits under
  const char *name;    // the preset itself
  const char *note;    // what makes it different, in a few words

  // --- Phosphor persistence, for the CRT rows -----------------------------
  //
  // Empty / 0 on everything that is not a phosphor. A page of e-ink does not
  // decay, and pretending it does would be the same kind of lie as an invented
  // chromaticity.
  //
  // SOURCE, so the next person does not re-derive it: Patrick Jankowiak
  // (KD5OEI), "Cathode Ray Tube Phosphors Of Interest To The Experimenter",
  // rev. 20100226.1844, labguysworld.com/crt_phosphor_research.pdf. Its
  // persistence column is defined as TIME TO DECAY TO 10% OF PEAK, which is
  // the number a fade wants.
  //
  // `persistence` is that table's own wording, verbatim. `decayMs` is the
  // figure the glow uses -- equal to the published number where the table gives
  // one, and where the table gives only a CLASS ("Medium") it is marked 0 and
  // the glow has to fall back rather than have a number invented for it.
  const char *phosphor;     // P-number, or nullptr
  const char *persistence;  // verbatim from the source table, or nullptr
  // The figure the glow uses. Where the source prints a NUMBER this is that
  // number. Where it prints only a CLASS -- "Medium", "Long", "Very short",
  // which is most of them -- this is that class read off the ladder below, and
  // the ladder is THIS REPO'S interpretation, not published data. The
  // `persistence` string above always says which you are looking at.
  //
  //   very short  0.05     short        0.5      medium short  1
  //   medium     10        long       150        very long   1000
  //
  // The ladder exists because the alternative was worse: mapping every
  // class-only row to one fallback made P39, whose entire identity is a long
  // tail, decay exactly like P45 and P56. The ordering is the source's own; only
  // the numbers between the rungs are ours.
  float decayMs;

  // The color this phosphor's trail decays TOWARD, or nullptr when it simply
  // dims -- which is every phosphor here except the cascade. Three bytes RGB.
  // See SimulatorOverlay::setPanelGlowTail.
  const unsigned char *afterglow;
};

// P7's persistent layer. A file-scope array because PresetInfo holds a pointer:
// the trail is (Zn,Cd)S:Cu yellow-green while the page it came from is
// blue-white, and that difference IS the phosphor.
inline constexpr unsigned char kCascadeAfterglow[3] = {0x69, 0xFF, 0x87};

// P14 and P17 are cascades too, and their tails are NOT P7's green -- the JEDEC
// table names them "Blue with Orange persistence" and "Blue-Yellow, Blue-Short
// Yellow-Long". Sharing one constant would have made all three decay to the
// same hue and thrown away the only thing that distinguishes them.
inline constexpr unsigned char kCascadeAfterglowOrange[3] = {0xFF, 0x93, 0x81};
inline constexpr unsigned char kCascadeAfterglowYellow[3] = {0xFF, 0xE2, 0x81};

inline constexpr PresetInfo kPresetInfo[] = {
    // THE SHORTLIST, and it sits at the head of this table because the head of
    // this table IS the order Settings.app shows and the order the firmware's
    // cycle button walks -- tests/panel_palette_test.cpp pins those two
    // together, so a shortlist cannot be a plist-only rearrangement.
    //
    // Chosen by the owner in a controlled runoff, 2026-08-18: 42 presets ->
    // 38 distinct pages -> 12 perceptually separate choices (complete linkage
    // at dE 25), then a full round robin, 63 of 63 answered, one lit card at a
    // time on black. Kendall's coefficient of consistency 0.843 against the
    // 0.25 coin flips would give. docs/phosphor-shortlist-2026-08-18.md has the
    // numbers. NOTHING IS REMOVED -- these six are promoted, the other 46 rows
    // follow in the order they already had.
    //
    // Two of the six are PROVISIONAL. The runoff hid the labels and never
    // animated decay, so it chose PAGES, not presets: P33 stands for the
    // #FFA472 page that P12/P19/P33/P38 all paint (longest tail at 2828 ms, so
    // with the glow on the choice means something and with it off the four are
    // identical), and P22G stands for the #00FF97 page it shares with P46.
    // Settle both with a test that actually renders decay.
    {kPresetAmberCrt, "CRT", "Amber", "P3 phosphor", "P3", "13ms", 13.0f, nullptr},
    {kPresetP33Crt, "CRT", "Radar Orange Longest", "P33 MgF2:Mn", "P33", "> 1 sec", 1000.0f, nullptr},
    {kPresetP22GCrt, "CRT", "TV Green", "P22G (Zn,Cd)S:Cu,Al", "P22G", "Short", 0.5f, nullptr},
    {kPresetGrayCrt, "CRT", "Gray", "P4 phosphor", "P4",
     "not over 7% of peak after 33 ms", 33.0f, nullptr},
    {kPresetCascadeCrt, "CRT", "Cascade", "P7 blue-white to yellow-green", "P7",
     "BluWh-Short / Yel-Long, >1 minute in low ambient illumination", 1000.0f,
     kCascadeAfterglow},
    {kPresetBlueCrt, "CRT", "Blue", "P11 phosphor", "P11", "2ms", 2.0f, nullptr},
    // ...and the rest, in the P-number / persistence / hue order they had.
    {kPresetHighContrast, "Neutral", "High Contrast", "black on white", nullptr, nullptr, 0.0f, nullptr},
    {kPresetDefault, "Neutral", "Default", "e-ink", nullptr, nullptr, 0.0f, nullptr},
    {kPresetReading, "Neutral", "Reading", "long-form on OLED", nullptr, nullptr, 0.0f, nullptr},
    {kPresetReadingWarm, "Neutral", "Reading Warm", "warmer paper", nullptr, nullptr, 0.0f, nullptr},
    {kPresetReadingCool, "Neutral", "Reading Cool", "cooler paper", nullptr, nullptr, 0.0f, nullptr},
    {kPresetSepia, "Paper", "Sepia", "warm", nullptr, nullptr, 0.0f, nullptr},
    {kPresetGruvboxLight, "Paper", "Gruvbox Light", "warm pale", nullptr, nullptr, 0.0f, nullptr},
    {kPresetLatte, "Paper", "Latte", "neutral pale", nullptr, nullptr, 0.0f, nullptr},
    {kPresetNord, "Paper", "Nord", "cool pale", nullptr, nullptr, 0.0f, nullptr},
    {kPresetSolarized, "Paper", "Solarized", "low contrast by design", nullptr, nullptr, 0.0f, nullptr},
    // The only row with an afterglow: written blue-white, left behind
    {kPresetGreenCrt, "CRT", "Green", "P1 phosphor", "P1", "20ms", 20.0f, nullptr},
    {kPresetP2Crt, "CRT", "Blue-Green Long", "P2 ZnS:Cu(Ag)", "P2", "Long", 150.0f, nullptr},
    {kPresetP5Crt, "CRT", "Blue Fastest", "P5 CaWO4:W", "P5", "Very Short", 0.05f, nullptr},
    {kPresetP6Crt, "CRT", "White TV", "P6 ZnS:Ag+ZnS:CdS:Ag", "P6", "Short", 0.5f, nullptr},
    {kPresetP10Crt, "CRT", "Dark Trace", "P10 KCl", "P10", "Long", 150.0f, nullptr},
    {kPresetP12Crt, "CRT", "Orange Persistent", "P12 Zn(Mg)F2:Mn", "P12", "Medium/long", 60.0f, nullptr},
    {kPresetP13Crt, "CRT", "Red-Orange", "P13 MgSi2O6:Mn", "P13", "Medium", 10.0f, nullptr},
    {kPresetP14Crt, "CRT", "Cascade Orange", "P14 ZnS:Ag on ZnS:CdS:Cu", "P14", "Medium/long", 150.0f, kCascadeAfterglowOrange},
    {kPresetP15Crt, "CRT", "Blue-Green Fastest", "P15 ZnO:Zn", "P15", "Extremely Short", 0.05f, nullptr},
    {kPresetP16Crt, "CRT", "Violet", "P16 CaMgSi2O6:Ce", "P16", "Very Short", 0.05f, nullptr},
    {kPresetP17Crt, "CRT", "Cascade Yellow", "P17 ZnO,ZnCdS:Cu", "P17", "Blue-Short, Yellow-Long", 150.0f, kCascadeAfterglowYellow},
    {kPresetP18Crt, "CRT", "White Soft", "P18 CaMgSi2O6:Ti, BeSi2O6:Mn", "P18", "Medium to Short", 1.0f, nullptr},
    {kPresetP19Crt, "CRT", "Radar Orange", "P19 (KF,MgF2):Mn", "P19", "Long", 150.0f, nullptr},
    {kPresetP20Crt, "CRT", "Yellow-Green Long", "P20 (Zn,Cd)S:Ag or (Zn,Cd)S:Cu", "P20", "1-100 ms", 20.0f, nullptr},
    {kPresetP21Crt, "CRT", "Radar Red", "P21 MgF2:Mn2+", "P21", "not published", 150.0f, nullptr},
    {kPresetRedCrt, "CRT", "Red", "P22R phosphor", "P22R", "Medium", 10.0f, nullptr},
    {kPresetBlueTvCrt, "CRT", "Blue TV", "P22B color-tube gun", "P22B",
     "Medium", 10.0f, nullptr},
    {kPresetP23Crt, "CRT", "White Warm", "P23 ZnS:Ag+(Zn,Cd)S:Ag", "P23", "Short", 0.5f, nullptr},
    {kPresetP24Crt, "CRT", "VFD Green", "P24 ZnO:Zn", "P24", "1-10 us", 0.05f, nullptr},
    {kPresetP25Crt, "CRT", "Orange Lead", "P25 CaSi2O6:Pb:Mn", "P25", "Medium", 10.0f, nullptr},
    {kPresetP26Crt, "CRT", "Radar Orange Long", "P26 (KF,MgF2):Mn", "P26", "Long", 150.0f, nullptr},
    {kPresetP27Crt, "CRT", "Red-Orange Deep", "P27 ZnPO4:Mn", "P27", "Medium", 10.0f, nullptr},
    {kPresetP28Crt, "CRT", "Yellow", "P28 (Zn,Cd)S:Cu,Cl", "P28", "Medium", 10.0f, nullptr},
    {kPresetGreenFastCrt, "CRT", "Green Fast", "P31 oscilloscope", "P31",
     "Medium short 0.01-1 ms", 1.0f, nullptr},
    {kPresetP34Crt, "CRT", "Green Longest", "P34 not published", "P34", "Very Long", 1000.0f, nullptr},
    {kPresetP35Crt, "CRT", "Blue-White", "P35 ZnS,ZnSe:Ag", "P35", "Medium Short", 1.0f, nullptr},
    {kPresetP38Crt, "CRT", "Radar Amber", "P38 (Zn,Mg)F2:Mn", "P38", "Long", 150.0f, nullptr},
    {kPresetGreenLongCrt, "CRT", "Green Long", "P39, long persistence", "P39",
     "Long", 150.0f, nullptr},
    {kPresetP40Crt, "CRT", "White Long", "P40 ZnS:Ag+(Zn,Cd)S:Cu", "P40", "Long", 150.0f, nullptr},
    {kPresetP43Crt, "CRT", "Terbium Green", "P43 Gd2O2S:Tb", "P43", "Medium", 10.0f, nullptr},
    {kPresetWhiteCrt, "CRT", "White", "P45 viewfinder", "P45", "Medium", 10.0f, nullptr},
    // yellow-green, over a minute. "Very long" on the ladder.
{kPresetP46Crt, "CRT", "Green Fastest", "P46 Y3Al5O12:Ce", "P46", "Very short (70 ns)", 7e-05f, nullptr},
    {kPresetBlueFastCrt, "CRT", "Blue Fast", "P47, very short", "P47",
     "Very short", 0.05f, nullptr},
    {kPresetP53Crt, "CRT", "Projector Green", "P53 Y3Al5O12:Tb", "P53", "Short", 0.5f, nullptr},
    {kPresetP55Crt, "CRT", "Blue Projector", "P55 ZnS:Ag,Al", "P55", "Short", 0.5f, nullptr},
    {kPresetRedProjCrt, "CRT", "Red Projector", "P56 projection tube", "P56",
     "Medium", 10.0f, nullptr},
};

inline constexpr int kPresetInfoCount =
    static_cast<int>(sizeof(kPresetInfo) / sizeof(kPresetInfo[0]));

// HOW LONG A PHOSPHOR'S TRAIL RUNS ON SCREEN, from its decayMs above.
//
// This is a TASTE decision and it lives here, in a pure function, only because
// getting it wrong is silent: it shipped as a flat x20 multiplier inside the
// iOS shim, and P7 -- whose decayMs is 1000, this repo's reading of ">1 minute"
// -- therefore asked for a TWENTY SECOND trail. At 900 ms such a ghost is still
// at 90% of full and the cascade's color shift (which ramps with 1 - alpha) has
// barely begun, so the one phosphor whose whole identity is its afterglow was
// the one phosphor that appeared to do nothing. Reported from the phone against
// build 85. A desktop A/B missed it because the env override supplies the
// duration directly and never runs this arithmetic.
//
// The published span is 1:20000 (P47's 0.05 ms to P7's 1000). No single
// multiplier serves it: pick one that makes the fastest visible and the slowest
// is unusable; pick one that keeps the slowest usable and the fastest is a
// single frame. So the span is COMPRESSED as a square root, anchored so P1 --
// the archetype green tube, and the row every other figure was sanity-checked
// against -- keeps the 400 ms it already had.
//
// What survives compression is the ORDER, exactly (sqrt is monotone), and the
// rough sense of proportion. What does not survive is the literal ratio, and
// that is deliberate: 20 seconds is not a truer rendering of P7 than 2.8 is, it
// is just an unusable one.
inline constexpr float kTrailAnchorDecayMs = 20.0f;  // P1
inline constexpr float kTrailAnchorMs = 400.0f;

// constexpr sqrt by Newton-Raphson: std::sqrt is not constexpr before C++26 and
// this header is included by a C++17 translation unit (the iOS harness).
constexpr float constexprSqrt(float x) {
  if (x <= 0.0f) return 0.0f;
  float guess = x > 1.0f ? x : 1.0f;
  for (int i = 0; i < 24; i++) guess = 0.5f * (guess + x / guess);
  return guess;
}

// A FRAME IS THE FLOOR. P46 is published at 70 ns and P24 at 1-10 us; compressed
// honestly those are 0.7 ms and 6 ms, which is less than one frame at 60 Hz --
// a trail that is drawn zero times and therefore is not a trail. Clamping to a
// single frame is the smallest lie that keeps "very fast phosphor" meaning
// "one frame of ghost" instead of meaning nothing at all.
inline constexpr float kTrailFloorMs = 16.7f;

constexpr float trailMsForDecay(float decayMs) {
  if (decayMs <= 0.0f) return 0.0f;
  const float t = kTrailAnchorMs * constexprSqrt(decayMs / kTrailAnchorDecayMs);
  return t < kTrailFloorMs ? kTrailFloorMs : t;
}

// The trail for a preset: 0 for everything that is not a phosphor, because a
// page of e-ink does not decay.
constexpr float trailMsForPreset(int preset) {
  const int p = migratePreset(preset);
  for (int i = 0; i < kPresetInfoCount; i++) {
    if (kPresetInfo[i].preset != p) continue;
    if (!kPresetInfo[i].phosphor) return 0.0f;
    return trailMsForDecay(kPresetInfo[i].decayMs);
  }
  return 0.0f;
}

}  // namespace panelpalette
