#pragma once
#include <cstdint>

// Pure decode of the e-ink two-plane grayscale representation into the
// simulator's preview gray levels. Kept free of SDL and HalDisplay state so a
// plain host test can exercise it (the same way fstest/roottest exercised the
// storage layer).
//
// Representation recap (mirrors the firmware's GfxRenderer grayscale passes):
// the BW base frame paints every non-white pixel black, then two 1bpp planes
// are written where a set bit means "update this pixel toward a gray target":
//   MSB only  -> light gray
//   MSB + LSB -> dark gray
//   LSB only  -> dark gray (never emitted by current firmware, decoded anyway)
//   neither   -> pixel keeps its base color
// Plane flags only lighten base-black pixels; the firmware never flags a
// base-white pixel and the panel waveforms are not driven that way, so a white
// pixel stays white regardless of plane bits.
namespace GrayscalePreview {

// Preview levels, chosen to read like the panel's four optical gray levels.
constexpr uint8_t kWhite = 255;
constexpr uint8_t kLight = 200;
constexpr uint8_t kDark = 96;
constexpr uint8_t kBlack = 0;

// A FLAG WINS OVER THE BASE, in both polarities. The plane bits name an OPTICAL
// RESULT on the panel ("light gray", "dark gray"); they are not a modifier on
// whatever the base pass happened to paint.
//
// This used to return white for any base-white pixel, discarding its flags, on
// the reasoning that the firmware only ever flags base-black pixels. That is
// true in LIGHT mode and false in DARK mode, and the difference is in the
// firmware's own table (GlyphAa::planes, lib/GfxRenderer/GlyphAaPlanes.h):
//
//   light mode  baseInk = L0|L1|L2   every coverage level is painted as ink by
//                                    the base, so flags do arrive on black
//   dark mode   baseInk = L0 (or L0|L1)  partial-coverage levels are NOT
//                                    painted by the base -- they arrive WHITE
//                                    and flagged
//
// So in dark mode every partly-covered pixel -- which is every glyph edge --
// was thrown away and rendered as paper. The glyphs came out skeletal and hard
// edged with no antialiasing at all, which is what "the antialiasing on the
// sans serif fonts looks bad in crt" is: not a bad gradient, an absent one. A
// sans serif shows it worst because its long straight stems are almost entirely
// edge pixels at reading sizes.
//
// Light mode is unaffected by the reordering: there, a flagged pixel is already
// black, so the two orderings return the same level for every input the
// firmware actually emits.
constexpr uint8_t previewLevel(bool baseWhite, bool msbFlagged,
                               bool lsbFlagged) {
  if (msbFlagged)
    return lsbFlagged ? kDark : kLight;
  if (lsbFlagged)
    return kDark;
  return baseWhite ? kWhite : kBlack;
}

} // namespace GrayscalePreview
