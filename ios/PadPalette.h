#pragma once

// The button pad's palette, its contrast ladder and its presets.
//
// PURE AND HOST-TESTABLE, on the same terms as PadCore.h: no SDL, no UIKit, no
// clock, no I/O. Everything here is constexpr, so the whole ladder is a
// compile-time artifact and `tests/pad_palette_test.cpp` can exercise it on a
// Mac or a Linux box without a phone. It was lifted out of
// CrossPointIOSShim.cpp for exactly that reason: every failure mode in here is
// silent (a tone that equals the field draws nothing, a label that disagrees
// with its tone lies to the owner, a preset that misses the shipped level
// changes the look of a pad nobody asked to change), and a silent failure with
// no host test is one that ships.
//
// --- Hollow controls -------------------------------------------------------
//
// Each control is a one-device-pixel stroke around nothing: the face IS the
// field, so at rest the pad is seven outlines on the same tone as the page's
// paper. A press lays a WASH inside the outline -- the fill changes and the
// stroke never moves.
//
// This reverses what the pad used to do, and the reversal is the point. The old
// arrangement put the face AWAY from the field (lighter than the paper in light
// appearance, darker than the background in dark) and spent the contrast on a
// ring. Two ceilings killed that: the field sits 4 levels below white in light
// and 18 above black in dark, so in light the face had almost nowhere to go and
// in dark the ring had to shout to clear the field. Both tones now step TOWARD
// mid-gray -- darker than the paper, lighter than 121212 -- which is the roomy
// direction in both appearances. One rule where there used to be two mirrored
// ones. (Apple's system ramp is still no help here and is still not used: it
// runs the wrong way in dark, systemGray6 1C1C1E being lighter than
// systemBackground 121212, and it is blue-tinted at every step against this
// app's warm paper.)
//
// THE PRESS IS THE ONLY FEEDBACK, the controls being unlabelled, and it is a
// large-area change rather than a loud one. At the default the wash is 14/255
// against a 34/255 stroke, but it covers a 58.8 pt cell where the stroke covers
// a line, and area is what makes it read.
//
// Every pair that must be told apart is >= 13/255 at the defaults, the floor
// below which a step is not reliably visible on a phone. Verified:
//   light  stroke/field 34, wash/field 14, stroke/wash 20
//   dark   stroke/field 33, wash/field 14, stroke/wash 19
//
// --- The dial --------------------------------------------------------------
//
// THE TONES BELOW ARE THE DEFAULTS OF A DIAL, not fixed constants. Both of them
// are owner-settable, separately for each appearance, through Settings >
// CrossPoint X3 (Root.plist -> CrossPointPrefs_padOutlineContrast /
// _padFillContrast -> the delta tables below), and a preset row above them sets
// all four at once (CrossPointPrefs_padContrastPreset).
//
// THE SCALE IS SIGNED AND FIELD-RELATIVE, and -9/+9 ARE THE ABSOLUTE GAMUT ENDS
// IN BOTH APPEARANCES: -9 is #000000 and +9 is #FFFFFF whether the field is
// paper or ink, and now on ANY paper the owner has chosen, not only the shipped
// one -- see toneChannelAt below, and the page-colour interaction it fixes. 0
// puts the tone ON the field, so the control draws nothing. Everything between
// is a rung chosen for its measured sRGB contrast ratio against that
// appearance's field.
//
// WHY SIGNED AND FIELD-RELATIVE RATHER THAN AN ABSOLUTE 0-100% LIGHTNESS SCALE.
// Three reasons, in order of weight:
//   1. It is the only parameterisation in which "invisible" is a FIXED
//      coordinate. 0 means "equal to the field" in both appearances; on an
//      absolute scale invisible would be 98% in light and 7% in dark, i.e. a
//      number the owner has to look up, and the Transparent preset would have
//      to store two different values to mean one thing.
//   2. Every persisted value keeps its meaning. The four keys already hold
//      -9..+9 on this scale, so re-deriving the endpoints migrates nothing,
//      where a 0-100 scale would silently reinterpret whatever is stored.
//   3. An absolute scale buys nothing where it might seem to. The crowding
//      near the light field is an 8-BIT problem -- FBFBF9 is four levels off
//      white -- and no reparameterisation adds tones that sRGB does not have.
//      What actually fixes it is not spending nine rungs on those four levels,
//      which is what the ladder below does.
//
// ACCESSIBLE ONLY IF ASKED, and the number is on the row. WCAG 1.4.11 wants 3:1
// against the adjacent color for the visual information that identifies a
// control, and the exemption it grants a labeled button does not apply to a pad
// that has none. The default strokes measure 1.364:1 in light and 1.483:1 in
// dark -- deliberately, this being a reading surface -- but 3:1 is a row rather
// than a rebuild, and now also a named preset: level -4 in light (929290,
// 3.01:1) and +4 in dark (616161, 3.02:1) hit it exactly for the stroke, -5 and
// +5 for the wash. The ladder runs on past it to 20.27:1 and 18.73:1.

#include <cstdint>

namespace padpalette {

struct Palette {
  uint8_t field[3];     // behind the panel and the pad
  uint8_t hairline[3];  // the stroke: control outlines and pair ticks
  uint8_t face[3];      // control interior at rest: EQUAL to the field, i.e. hollow
  uint8_t faceDown[3];  // the wash, laid inside the stroke while held
};

// The field matches the panel's paper tone (HalDisplay's PanelPalette:
// 2D2D2D-on-FBFBF9 light, E0E0DE-on-121212 dark — change them together), so
// the page floats edgeless in the field in both appearances. `face` repeats it
// on purpose: paintPad's existing stroke-then-face draw paints a hollow control
// when the two are equal, so nothing structural is needed to get an outline.
//
// `hairline` and `faceDown` here are the DEFAULT (+/-1) tones. The live palette
// is built by makePalette() from `field` plus a delta out of the tables below;
// the static_asserts pin the two together, so these four lines stay the honest
// documentation of what ships rather than drifting into decoration.
inline constexpr Palette kLightPalette{{0xFB, 0xFB, 0xF9},
                                       {0xD9, 0xD9, 0xD7},
                                       {0xFB, 0xFB, 0xF9},
                                       {0xED, 0xED, 0xEB}};
inline constexpr Palette kDarkPalette{{0x12, 0x12, 0x12},
                                      {0x33, 0x33, 0x33},
                                      {0x12, 0x12, 0x12},
                                      {0x20, 0x20, 0x20}};

// --- The contrast ladder ---------------------------------------------------
//
// PRECOMPUTED, NOT DERIVED AT RUNTIME. Each entry is a delta added to every
// channel of the field and clamped; the rungs were chosen for their measured
// sRGB contrast ratio against that field, so the arithmetic that produced them
// is relative-luminance work that has no business running on a phone every
// frame. The ratios each row lands on are the ones Root.plist prints as its row
// labels -- the two must be read together, and neither is a guess.
// tests/pad_palette_test.cpp recomputes every ratio from the tables and checks
// it against the label Root.plist actually ships, so the pair cannot drift.
//
// Indexed by level + kContrastOffset, i.e. -9 first and +9 last.
//
//   light outline  -9 000000 20.27:1 | -8 292927 14.07:1| -7 40403E 10.03:1
//                  -6 565654  7.10:1 | -5 747472  4.52:1| -4 929290  3.01:1
//                  -3 B4B4B2  2.00:1 | -2 C3C3C1 1.704:1| -1 D9D9D7 1.364:1 (default)
//                  +1 DEDEDC 1.300:1 | +2 E3E3E1 1.240:1| +3 E7E7E5 1.195:1
//                  +4 EBEBE9 1.152:1 | +5 EFEFED 1.111:1| +6 F2F2F0 1.082:1
//                  +7 F5F5F3 1.054:1 | +8 F7F7F5 1.035:1| +9 FFFFFF 1.036:1 (white)
//   light fill     -9 000000 20.27:1 | -8 40403E 10.03:1| -7 565654  7.10:1
//                  -6 747472  4.52:1 | -5 929290  3.01:1| -4 B4B4B2  2.00:1
//                  -3 CFCFCD 1.506:1 | -2 DEDEDC 1.300:1| -1 EDEDEB 1.131:1 (default)
//                  +1 EFEFED 1.111:1 | +2 F1F1EF 1.092:1| +3 F3F3F1 1.072:1
//                  +4 F4F4F2 1.063:1 | +5 F5F5F3 1.054:1| +6 F6F6F4 1.044:1
//                  +7 F7F7F5 1.035:1 | +8 F8F8F6 1.026:1| +9 FFFFFF 1.036:1 (white)
//   dark outline   +9 FFFFFF 18.73:1 | +8 DFDFDF 14.06:1| +7 BEBEBE 10.08:1
//                  +6 9F9F9F  7.08:1 | +5 7D7D7D  4.55:1| +4 616161  3.02:1
//                  +3 474747  2.02:1 | +2 3D3D3D 1.725:1| +1 333333 1.483:1 (default)
//                  -1 2E2E2E 1.380:1 | -2 292929 1.288:1| -3 252525 1.222:1
//                  -4 212121 1.163:1 | -5 1D1D1D 1.111:1| -6 1A1A1A 1.076:1
//                  -7 171717 1.045:1 | -8 141414 1.017:1| -9 000000 1.121:1 (black)
//   dark fill      +9 FFFFFF 18.73:1 | +8 BEBEBE 10.08:1| +7 9F9F9F  7.08:1
//                  +6 7D7D7D  4.55:1 | +5 616161  3.02:1| +4 474747  2.02:1
//                  +3 343434 1.505:1 | +2 2A2A2A 1.305:1| +1 202020 1.150:1 (default)
//                  -1 1E1E1E 1.124:1 | -2 1C1C1C 1.099:1| -3 1A1A1A 1.076:1
//                  -4 191919 1.066:1 | -5 181818 1.055:1| -6 171717 1.045:1
//                  -7 161616 1.035:1 | -8 141414 1.017:1| -9 000000 1.121:1 (black)
//
// THE FILL LADDER IS GENTLER at the low end than the outline's -- 1.30 / 1.51 /
// 2.00 where the outline runs 1.70 / 2.00 / 3.01 -- because a wash covers a
// whole cell and a stroke covers a line, and equal ratios do not read as equal
// emphasis.
//
// THE FINE END LIVES IN THE FIELD'S ROOMY DIRECTION, which is why the sign does
// not mean "darker/lighter" once you are past +/-1. In light, +1..+8 are all
// DARKER than the paper and run from just under the default (1.300:1) to just
// over invisible (1.026:1); in dark, -1..-8 are all LIGHTER than 121212 and do
// the same. That is the range a reading surface actually cares about, and it
// used to be the dead zone: the ladder ran to the field's opposite gamut end,
// which on the light side meant +1..+9 spanning FBFBF9 -> FFFFFD, 1.000:1 to
// 1.030:1, with several rows PIXEL-IDENTICAL. Nine of nineteen rows bought
// nothing while the two rows an owner most wants to choose between -- the
// default and invisible -- were adjacent integers with nothing in between.
// Reported exactly that way: "missing all the steps between default and
// invisible". `kTonesDistinct` below is the guard that stops that returning.
//
// EACH APPEARANCE STILL REACHES ITS OPPOSITE GAMUT END, on exactly one row, at
// the magnitude the other direction ends on. Dark has always had -9 = BLACK;
// light now has +9 = WHITE, which is the change that makes the rule uniform
// (-9 = #000000 and +9 = #FFFFFF in BOTH appearances). Neither row is
// high-contrast against its own field -- black is 1.121:1 on 121212, white is
// 1.036:1 on FBFBF9, because that is how close each field already sits to that
// end -- so both sit at the END of Root.plist's list, after invisible, rather
// than at the top with the loud rungs. They are there because they are the one
// tone that vanishes into a true-black page on OLED, and the one tone that
// vanishes into a blown-out white page, and neither was reachable at all from a
// row that named a ratio and never said the color. They say the color now.
//
// Light +9 was 1.017:1 (F9F9F7) before this and is #FFFFFF now. That is the one
// rung this change spends: the finest light stroke is now +8 at 1.035:1, and
// the finest light wash +8 at 1.026:1.
//
// Root.plist orders its rows most-visible -> invisible -> gamut end, which is
// display order only: Titles and Values are parallel arrays, so the stored
// integers are unchanged and an existing selection still means what it meant.
// The +/-1 default rows are untouched, which the static_asserts pin.
inline constexpr int kContrastMin = -9;
inline constexpr int kContrastMax = 9;
inline constexpr int kContrastOffset = -kContrastMin;
inline constexpr int kContrastLevels = kContrastMax - kContrastMin + 1;

inline constexpr int16_t kOutlineDeltaLight[kContrastLevels] = {
    -251, -210, -187, -165, -135, -105, -71, -56, -34, 0,
    -29,  -24,  -20,  -16,  -12,  -9,   -6,  -4,  6};
inline constexpr int16_t kFillDeltaLight[kContrastLevels] = {
    -251, -187, -165, -135, -105, -71, -44, -29, -14, 0,
    -12,  -10,  -8,   -7,   -6,   -5,  -4,  -3,  6};
inline constexpr int16_t kOutlineDeltaDark[kContrastLevels] = {
    -18, 2,  5,  8,  11,  15,  19,  23,  28,  0,
    33,  43, 53, 79, 107, 141, 172, 205, 237};
inline constexpr int16_t kFillDeltaDark[kContrastLevels] = {
    -18, 2,  4,  5,  6,  7,   8,   10,  12,  0,
    14,  24, 34, 53, 79, 107, 141, 172, 237};

constexpr int clampLevel(int level) {
  return level < kContrastMin ? kContrastMin
                              : (level > kContrastMax ? kContrastMax : level);
}

constexpr uint8_t toneChannel(uint8_t field, int16_t delta) {
  return static_cast<uint8_t>(field + delta < 0
                                  ? 0
                                  : (field + delta > 255 ? 255 : field + delta));
}

// THE TWO END RUNGS ARE ABSOLUTE, NOT RELATIVE: -9 is #000000 and +9 is
// #FFFFFF on ANY field, and every rung between them is still a delta on the
// field. This is the resolver the live palette paints through.
//
// It is not a new rule -- it is the rule this file has stated since the ladder
// was written ("-9 IS #000000 AND +9 IS #FFFFFF whether the field is paper or
// ink", above), made true again. It WAS true while the field was a constant:
// -251 and +6 clamp to the ends on FBFBF9, -18 and +237 do on 121212, and every
// static_assert that pins it was written against those two fields. It stopped
// being true the moment the panel's paper became a dial (src/PanelPalette.h --
// eleven presets plus four Custom hex fields), because A FIXED DELTA CANNOT
// REACH A FIXED ENDPOINT FROM AN ARBITRARY START. Nothing warned: the tone
// still resolved, the row still printed its ratio, and the pad still drew an
// outline -- just not the color the row names.
//
// MEASURED, on an iPhone Air simulator at native 1260x2736 (no downsampling, so
// the stroke is exactly one unblended pixel), read back out of the screenshot:
//
//   Green CRT dark, field #001A00, outline level +9, row "18.73:1 -- white"
//     painted #EDFFED.
//
// It is not confined to the CRTs. +9 in dark is field+237, so it reaches white
// only if every channel of the paper is >= 18; -9 in dark is field-18, so it
// reaches black only if every channel is <= 18. In light the two thresholds are
// >= 249 and <= 251. Of the eleven page-colour presets only Default satisfies
// all four. Sepia, Cool Gray, Solarized, both CRTs, Nord, Gruvbox Light and
// Latte each miss at least one end -- and High Contrast, the palette whose
// entire premise IS the gamut ends, painted #040404 for "black" on its white
// paper and #EDEDED for "white" on its black one.
//
// CLAMPING IS WHAT HID IT. Every wrong answer was a plausible near-miss rather
// than a visibly broken color, which is exactly the silent failure this
// header's opening comment says the file exists to catch.
//
// The +/-9 entries of the delta tables are kept, and are still the tones the
// shipped fields produce, so the ratios Root.plist prints for those two rows go
// on being recomputed from them by tests/pad_palette_test.cpp.
constexpr uint8_t toneChannelAt(uint8_t field,
                                const int16_t (&table)[kContrastLevels],
                                int level) {
  return level <= kContrastMin ? 0
         : level >= kContrastMax
             ? 255
             : toneChannel(field, table[level + kContrastOffset]);
}

// Level-addressed forms of the two helpers below, for asserting the resolver
// itself rather than a raw table entry.
constexpr bool levelIs(const uint8_t (&field)[3],
                       const int16_t (&table)[kContrastLevels], int level,
                       uint8_t r, uint8_t g, uint8_t b) {
  return toneChannelAt(field[0], table, level) == r &&
         toneChannelAt(field[1], table, level) == g &&
         toneChannelAt(field[2], table, level) == b;
}

constexpr bool toneIs(const uint8_t (&field)[3], int16_t delta, uint8_t r,
                      uint8_t g, uint8_t b) {
  return toneChannel(field[0], delta) == r && toneChannel(field[1], delta) == g &&
         toneChannel(field[2], delta) == b;
}

constexpr bool toneMatches(const uint8_t (&field)[3], int16_t delta,
                           const uint8_t (&want)[3]) {
  return toneIs(field, delta, want[0], want[1], want[2]);
}

// --- Presets ---------------------------------------------------------------
//
// One row above the four fine pickers, setting all four at once. It is an
// OVERRIDE, not a writer: while it names anything but Custom the four pickers
// are not read, and selecting Custom hands control back to whatever they still
// hold. That shape was chosen over "the preset writes the four keys" because
// the app would be writing into a store Settings.app is displaying from another
// process -- there is no refresh to hang the write on, so the pickers would
// show yesterday's numbers -- and because not writing means the owner's own
// dialled-in values survive a detour through Accessible untouched.
//
// Current is the shipped look, and it stays selectable and unchanged, so a pad
// set to it is still pixel-identical to the build before presets existed.
// Accessible is the WCAG 1.4.11 3:1 rung against each appearance's field.
// Transparent is level 0 everywhere: tone equals field, nothing drawn.
//
// BLACK & WHITE is the outline at the absolute gamut end away from the field --
// #000000 in light, #FFFFFF in dark, on every page colour -- with the wash left
// on the 3:1 rung. It is the DEFAULT as of 2026-08-16, by owner ruling: the
// shipped grey outline measured #D9D9D7 on #FBFBF9 in light and #333333 on
// #121212 in dark, a 1.364:1 / 1.483:1 hairline, and was asked to be actually
// black and white. Nothing was removed to do it -- Current is one tap away and
// still resolves to the same +/-1 levels it always did, Accessible and
// Transparent are untouched, and Custom still reads all four fine pickers.
enum Preset : int {
  kPresetCustom = 0,
  kPresetCurrent = 1,
  kPresetAccessible = 2,
  kPresetTransparent = 3,
  // Appended 2026-08-16 by owner ruling ("making black and white outlines
  // actually black and white"). APPEND ONLY, for the same reason
  // panelpalette::Preset is append-only: the value persists as an integer in
  // NSUserDefaults, so inserting a row re-points every saved choice at a
  // different look.
  kPresetBlackWhite = 4,
};

struct Levels {
  int outline;
  int fill;
};

// Levels for a named preset. kPresetCustom has no levels of its own -- the
// caller reads the four pickers instead -- and is answered with Current's so a
// miswired caller degrades to the shipped look rather than to an invisible pad.
constexpr Levels presetLevels(int preset, bool dark) {
  switch (preset) {
  case kPresetTransparent:
    return {0, 0};
  case kPresetAccessible:
    // The 3:1 rung is at a different magnitude for stroke and wash because the
    // fill ladder is the gentler of the two (see above): -4/-5 in light,
    // +4/+5 in dark.
    return dark ? Levels{4, 5} : Levels{-4, -5};
  case kPresetBlackWhite:
    // THE OUTLINE AT THE GAMUT END AWAY FROM THE FIELD, which after
    // toneChannelAt above is #000000 in light and #FFFFFF in dark on every page
    // colour, not just the shipped one. That is the whole ask, in one row.
    //
    // THE WASH IS NOT TAKEN TO THE SAME END, and that is deliberate rather than
    // a half-measure. A stroke covers a line and a wash covers a 58.8 pt cell
    // (see the top of this file): -9/+9 on the fill would flip the whole
    // interior of a held control to solid black or solid white, which is a
    // different control appearing under the finger rather than the same one
    // filling. It sits on the 3:1 rung the Accessible preset uses -- 929290 in
    // light, 616161 in dark on the shipped paper -- so the press stays a wash
    // while reading clearly against a maximum-contrast stroke.
    return dark ? Levels{kContrastMax, 5} : Levels{kContrastMin, -5};
  case kPresetCurrent:
  case kPresetCustom:
  default:
    return dark ? Levels{1, 1} : Levels{-1, -1};
  }
}

constexpr bool isKnownPreset(int preset) {
  return preset == kPresetCustom || preset == kPresetCurrent ||
         preset == kPresetAccessible || preset == kPresetTransparent ||
         preset == kPresetBlackWhite;
}

// --- Guards ----------------------------------------------------------------
//
// THE TABLES CANNOT DRIFT FROM THE PALETTE ABOVE, FROM THE COMMENT, OR FROM THE
// PRESETS. +/-1 must reproduce the shipped tones exactly (this is what makes an
// untouched pad, and the Current preset, pixel-identical), the accessible rungs
// must land on 3:1, +/-9 must reach the gamut ends in BOTH appearances, and no
// two rungs of a ladder may resolve to the same pixels.

// A dead zone is a ladder with rows that paint identically. It is invisible in
// review -- the numbers all differ, the tones do not -- so it is a compile-time
// check rather than a habit. Quadratic over 19 entries, at compile time, once.
//
// Runs over LEVELS through toneChannelAt, not over raw table entries, so it
// checks the tones actually painted -- including the two absolute ends.
//
// On the SHIPPED fields only. It cannot be asserted for every field and must
// not be: on High Contrast light the paper IS #FFFFFF, so +9 (white) and 0
// (invisible) are the same pixels there by arithmetic, which is not a dead zone
// but the documented behaviour of the white row on a blown-out page.
constexpr bool tonesDistinct(const uint8_t (&field)[3],
                             const int16_t (&table)[kContrastLevels]) {
  for (int a = kContrastMin; a <= kContrastMax; a++) {
    for (int b = a + 1; b <= kContrastMax; b++) {
      if (toneChannelAt(field[0], table, a) == toneChannelAt(field[0], table, b) &&
          toneChannelAt(field[1], table, a) == toneChannelAt(field[1], table, b) &&
          toneChannelAt(field[2], table, a) == toneChannelAt(field[2], table, b))
        return false;
    }
  }
  return true;
}

static_assert(toneMatches(kLightPalette.field,
                          kOutlineDeltaLight[-1 + kContrastOffset],
                          kLightPalette.hairline),
              "light outline level -1 must be the shipped D9D9D7 stroke");
static_assert(toneMatches(kLightPalette.field,
                          kFillDeltaLight[-1 + kContrastOffset],
                          kLightPalette.faceDown),
              "light fill level -1 must be the shipped EDEDEB wash");
static_assert(toneMatches(kDarkPalette.field,
                          kOutlineDeltaDark[1 + kContrastOffset],
                          kDarkPalette.hairline),
              "dark outline level +1 must be the shipped 333333 stroke");
static_assert(toneMatches(kDarkPalette.field, kFillDeltaDark[1 + kContrastOffset],
                          kDarkPalette.faceDown),
              "dark fill level +1 must be the shipped 202020 wash");

// The four rungs the Accessible preset selects, one per (appearance, role).
static_assert(toneIs(kLightPalette.field,
                     kOutlineDeltaLight[-4 + kContrastOffset], 0x92, 0x92, 0x90),
              "light outline level -4 must be 929290, the 3:1 rung");
static_assert(toneIs(kLightPalette.field, kFillDeltaLight[-5 + kContrastOffset],
                     0x92, 0x92, 0x90),
              "light fill level -5 must be 929290, the 3:1 rung");
static_assert(toneIs(kDarkPalette.field, kOutlineDeltaDark[4 + kContrastOffset],
                     0x61, 0x61, 0x61),
              "dark outline level +4 must be 616161, the 3:1 rung");
static_assert(toneIs(kDarkPalette.field, kFillDeltaDark[5 + kContrastOffset], 0x61,
                     0x61, 0x61),
              "dark fill level +5 must be 616161, the 3:1 rung");

// FULL GAMUT, BOTH ENDS, BOTH APPEARANCES, BOTH ROLES. Eight cells; each is
// asserted on its own so a failure names the one that broke. Asserted through
// toneChannelAt (the resolver the pad paints through), not against a raw table
// entry -- the previous form passed for two years while the painted color on
// nine of eleven page colours was something else.
static_assert(levelIs(kLightPalette.field, kOutlineDeltaLight, -9, 0, 0, 0),
              "light outline level -9 must be #000000");
static_assert(levelIs(kLightPalette.field, kFillDeltaLight, -9, 0, 0, 0),
              "light fill level -9 must be #000000");
static_assert(levelIs(kLightPalette.field, kOutlineDeltaLight, 9, 0xFF, 0xFF, 0xFF),
              "light outline level +9 must be #FFFFFF");
static_assert(levelIs(kLightPalette.field, kFillDeltaLight, 9, 0xFF, 0xFF, 0xFF),
              "light fill level +9 must be #FFFFFF");
static_assert(levelIs(kDarkPalette.field, kOutlineDeltaDark, -9, 0, 0, 0),
              "dark outline level -9 must be #000000");
static_assert(levelIs(kDarkPalette.field, kFillDeltaDark, -9, 0, 0, 0),
              "dark fill level -9 must be #000000");
static_assert(levelIs(kDarkPalette.field, kOutlineDeltaDark, 9, 0xFF, 0xFF, 0xFF),
              "dark outline level +9 must be #FFFFFF");
static_assert(levelIs(kDarkPalette.field, kFillDeltaDark, 9, 0xFF, 0xFF, 0xFF),
              "dark fill level +9 must be #FFFFFF");

// AND ON A FIELD THAT IS NOT THE SHIPPED ONE, which is the whole point: the
// eight above passed while these did not exist. Three papers that each broke a
// different end before toneChannelAt, taken verbatim from src/PanelPalette.h:
// Green CRT dark (#001A00 -- gave #EDFFED for white, #000800 for black), High
// Contrast light (#FFFFFF -- gave #040404 for black) and Sepia dark (#1C1710 --
// gave #FFFFFD for white). tests/pad_palette_test.cpp sweeps all eleven
// presets; these three are here so the header cannot be edited into a build
// that compiles and lies.
inline constexpr uint8_t kGreenCrtDarkPaper[3] = {0x00, 0x1A, 0x00};
inline constexpr uint8_t kHighContrastLightPaper[3] = {0xFF, 0xFF, 0xFF};
inline constexpr uint8_t kSepiaDarkPaper[3] = {0x1C, 0x17, 0x10};

static_assert(levelIs(kGreenCrtDarkPaper, kOutlineDeltaDark, 9, 0xFF, 0xFF, 0xFF),
              "dark outline +9 must be #FFFFFF on the Green CRT paper too");
static_assert(levelIs(kGreenCrtDarkPaper, kOutlineDeltaDark, -9, 0, 0, 0),
              "dark outline -9 must be #000000 on the Green CRT paper too");
static_assert(levelIs(kHighContrastLightPaper, kOutlineDeltaLight, -9, 0, 0, 0),
              "light outline -9 must be #000000 on a pure white paper too");
static_assert(levelIs(kSepiaDarkPaper, kOutlineDeltaDark, 9, 0xFF, 0xFF, 0xFF),
              "dark outline +9 must be #FFFFFF on the Sepia paper too");
static_assert(levelIs(kSepiaDarkPaper, kFillDeltaDark, 9, 0xFF, 0xFF, 0xFF),
              "dark fill +9 must be #FFFFFF on the Sepia paper too");

static_assert(tonesDistinct(kLightPalette.field, kOutlineDeltaLight) &&
                  tonesDistinct(kLightPalette.field, kFillDeltaLight) &&
                  tonesDistinct(kDarkPalette.field, kOutlineDeltaDark) &&
                  tonesDistinct(kDarkPalette.field, kFillDeltaDark),
              "two rungs of one ladder paint the same pixels: that is the dead "
              "zone this ladder exists to avoid");

// The presets, pinned to the rungs they claim.
static_assert(presetLevels(kPresetCurrent, false).outline == -1 &&
                  presetLevels(kPresetCurrent, false).fill == -1 &&
                  presetLevels(kPresetCurrent, true).outline == 1 &&
                  presetLevels(kPresetCurrent, true).fill == 1,
              "Current must be the shipped +/-1 levels, or an untouched pad is "
              "no longer pixel-identical");
static_assert(presetLevels(kPresetAccessible, false).outline == -4 &&
                  presetLevels(kPresetAccessible, false).fill == -5 &&
                  presetLevels(kPresetAccessible, true).outline == 4 &&
                  presetLevels(kPresetAccessible, true).fill == 5,
              "Accessible must select the 3:1 rungs asserted above");
static_assert(presetLevels(kPresetBlackWhite, false).outline == kContrastMin &&
                  presetLevels(kPresetBlackWhite, true).outline == kContrastMax,
              "Black & White must put the OUTLINE on the absolute gamut end "
              "away from the field: that is the entire content of the preset");
static_assert(presetLevels(kPresetBlackWhite, false).fill == -5 &&
                  presetLevels(kPresetBlackWhite, true).fill == 5,
              "Black & White's wash must stay on the 3:1 rung, not follow the "
              "stroke to the gamut end (a solid cell is a different control)");
// The claim the preset's NAME makes, checked on a paper that is not the shipped
// one -- which is what the name was untrue on before.
static_assert(levelIs(kHighContrastLightPaper, kOutlineDeltaLight,
                      presetLevels(kPresetBlackWhite, false).outline, 0, 0, 0) &&
                  levelIs(kGreenCrtDarkPaper, kOutlineDeltaDark,
                          presetLevels(kPresetBlackWhite, true).outline, 0xFF,
                          0xFF, 0xFF),
              "Black & White must paint #000000 / #FFFFFF on ANY page colour");
static_assert(presetLevels(kPresetTransparent, false).outline == 0 &&
                  presetLevels(kPresetTransparent, false).fill == 0 &&
                  presetLevels(kPresetTransparent, true).outline == 0 &&
                  presetLevels(kPresetTransparent, true).fill == 0,
              "Transparent must be level 0, the tone that equals the field");
static_assert(kOutlineDeltaLight[0 + kContrastOffset] == 0 &&
                  kFillDeltaLight[0 + kContrastOffset] == 0 &&
                  kOutlineDeltaDark[0 + kContrastOffset] == 0 &&
                  kFillDeltaDark[0 + kContrastOffset] == 0,
              "level 0 must be a zero delta in every ladder, or Transparent "
              "draws something");

// The live palette, on an EXPLICIT field. `face` is the field by definition
// (that is what makes the control hollow) and the stroke and the wash are the
// field plus a delta -- so the whole pad follows whatever tone is passed here.
//
// THE FIELD IS AN ARGUMENT BECAUSE THE PANEL'S PAPER IS A DIAL. The field is
// the panel's paper (see kLightPalette above), and the owner can now set that
// paper to any color in Settings (src/PanelPalette.h). Baking the shipped paper
// in would leave a sepia page floating on a white field with a visible seam --
// the one thing the field exists to prevent -- and would put the pad's ladder
// on a tone that is no longer behind it.
//
// The ladder still works unchanged on any field, because every rung is a
// RELATIVE delta clamped into gamut: that is the second reason the scale is
// signed and field-relative rather than absolute (see the three reasons above;
// this is now a fourth). What a rung's measured CONTRAST RATIO comes out at
// does move with the field, so Root.plist's printed ratios are true of the
// shipped paper and approximate of a custom one. Named on the row.
constexpr Palette makePaletteOn(bool dark, int outlineLevel, int fillLevel,
                                const uint8_t (&field)[3]) {
  const Palette &base = dark ? kDarkPalette : kLightPalette;
  const int ol = clampLevel(outlineLevel);
  const int fl = clampLevel(fillLevel);
  Palette p = base;
  for (int c = 0; c < 3; c++) {
    p.field[c] = field[c];
    p.face[c] = field[c];
    // The table is chosen INSIDE the call, not hoisted into a local, for the
    // same reason makePalette below makes two calls rather than one: a
    // conditional operator over two arrays decays both to pointers, which will
    // not bind to toneChannelAt's reference parameter.
    p.hairline[c] = dark ? toneChannelAt(field[c], kOutlineDeltaDark, ol)
                         : toneChannelAt(field[c], kOutlineDeltaLight, ol);
    p.faceDown[c] = dark ? toneChannelAt(field[c], kFillDeltaDark, fl)
                         : toneChannelAt(field[c], kFillDeltaLight, fl);
  }
  return p;
}

// The shipped field. Every static_assert above is written against this, and an
// untouched install still comes through here, so the default pad is unchanged.
constexpr Palette makePalette(bool dark, int outlineLevel, int fillLevel) {
  // Two calls rather than a ternary on the field: a conditional operator over
  // two arrays decays both to pointers, which will not bind to the reference
  // parameter.
  return dark
             ? makePaletteOn(true, outlineLevel, fillLevel, kDarkPalette.field)
             : makePaletteOn(false, outlineLevel, fillLevel,
                             kLightPalette.field);
}

// Resolve the four Settings values into the two levels actually painted.
// `outlinePref`/`fillPref` are what the fine pickers hold for this appearance;
// they are consulted only when the preset is Custom.
constexpr Levels resolveLevels(int preset, bool dark, int outlinePref,
                               int fillPref) {
  if (preset == kPresetCustom)
    return {clampLevel(outlinePref), clampLevel(fillPref)};
  return presetLevels(isKnownPreset(preset) ? preset : kPresetCurrent, dark);
}

}  // namespace padpalette
