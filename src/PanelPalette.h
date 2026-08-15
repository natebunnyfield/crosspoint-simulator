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
//
// None is below 7:1, which is deliberate: this is a page of body text, and the
// dial exists to change its CHARACTER, not to let someone make it unreadable by
// picking from a list. The Custom fields below have no such floor, because a
// typed hex value is an explicit act.
enum Preset : int {
  kPresetCustom = 0,        // read the four hex fields instead
  kPresetDefault = 1,       // the shipped tones; the default, hence pixel-identical
  kPresetHighContrast = 2,  // #000000 on #FFFFFF, and its inverse
  kPresetSepia = 3,         // warm paper, warm-black ink
  kPresetCoolGray = 4,      // cool paper, near-neutral cold ink
};

constexpr bool isKnownPreset(int preset) {
  return preset == kPresetCustom || preset == kPresetDefault ||
         preset == kPresetHighContrast || preset == kPresetSepia ||
         preset == kPresetCoolGray;
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
