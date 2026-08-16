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
  kPresetCoolGray = 4,      // cool paper, near-neutral cold ink
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
  kPresetSoft = 13,
  // Appended 2026-08-16 by owner ruling, closing out the CRT group. Same
  // APPEND-ONLY rule as above -- the Settings row ORDER is free and is where
  // the grouping happens, so neither of these had to be inserted anywhere.
  kPresetSepiaCrt = 14,  // NOT a phosphor. A toned tube -- see its case
  kPresetBlueCrt = 15,   // P11 phosphor
};

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
         preset == kPresetCoolGray || preset == kPresetSolarized ||
         preset == kPresetGreenCrt || preset == kPresetAmberCrt ||
         preset == kPresetNord || preset == kPresetGruvboxLight ||
         preset == kPresetSoft ||
         preset == kPresetLatte || preset == kPresetRedCrt ||
         preset == kPresetGrayCrt || preset == kPresetSepiaCrt ||
         preset == kPresetBlueCrt;
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
  case kPresetCoolGray:
    return dark ? Palette{{0xDC, 0xE3, 0xE8}, {0x10, 0x14, 0x1A}}
                : Palette{{0x1F, 0x24, 0x29}, {0xE8, 0xEC, 0xEF}};
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
  case kPresetSoft:
    return dark ? Palette{{0xAE, 0xAE, 0xAE}, {0x00, 0x00, 0x00}}
                : Palette{{0x48, 0x48, 0x48}, {0xFF, 0xFF, 0xFF}};
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
  // Dictionary of Colour, 1930, via Wikipedia's Sepia (color)). Two deliberate
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
  case kPresetSepiaCrt:
    return dark ? Palette{{0xFF, 0xCC, 0xAF}, {0x1A, 0x15, 0x12}}
                : Palette{{0x66, 0x3B, 0x11}, {0xFF, 0xDF, 0xCE}};
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

}  // namespace panelpalette
