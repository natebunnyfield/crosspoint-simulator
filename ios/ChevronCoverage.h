// The keyboard chip's chevron, as coverage rather than as pixels.
//
// Extracted from paintKeyboardChip() for the reason PadCore and PadPalette were:
// the arithmetic is the part worth pinning, and it cannot be reached from a host
// test while it lives inside a function that needs SDL, a renderer and a live
// window. Nothing here draws; the caller turns coverage into rects.
//
// WHAT SHAPE THIS IS. The chevron used to be stacked one-pixel rows with the
// offset stepping a whole pixel per row, which made every edge hard -- measured
// off the Metal renderer at iPhone numbers, it came back with exactly two levels,
// 0 and 255. This describes the shape that loop was APPROXIMATING, so it can be
// rasterised by coverage instead: a pair of sheared bands, where a point `u`
// below the apex is covered by the left arm over [cx - u - arm/2, cx - u + arm/2]
// and by the right arm over the mirror of that.
//
// Same extents, same horizontal weight, same square end cuts, same flat overlap
// at the apex. The only thing that changes is edge quality -- which is the point,
// and also the limit of what may change here, because every proportion in it is
// owner-approved (CrossPointIOSShim.cpp carries the rulings).
#pragma once

#include <algorithm>
#include <cmath>

namespace chevron {

struct Geometry {
  float cx = 0.0f;     // horizontal centre of the glyph, device px
  float top = 0.0f;    // top edge of the glyph box, device px
  float chevH = 0.0f;  // arm run; the arms are 45 degrees, so this is both axes
  float arm = 1.0f;    // HORIZONTAL width of an arm (perpendicular is arm/sqrt2)
  // Which way the chevron points. False is "^" (summon the keyboard), true is
  // "v" (dismiss) -- named for the state, not the glyph, matching the caller.
  bool keyboardUp = false;
};

// Coverage of the pixel column [px, px + 1) by the chevron, at one sample
// height. Exact: per scanline each arm is a closed interval, so this is an
// interval overlap and not an approximation.
inline float coverageAtRow(const Geometry &g, const int px, const float sy) {
  const float halfArm = g.arm / 2.0f;
  const float u = g.keyboardUp ? (g.top + g.chevH - sy) : (sy - g.top);
  if (u < 0.0f || u > g.chevH) return 0.0f;

  const float lo0 = g.cx - u - halfArm, hi0 = g.cx - u + halfArm;
  const float lo1 = g.cx + u - halfArm, hi1 = g.cx + u + halfArm;
  const float a = static_cast<float>(px), b = a + 1.0f;

  const float c0 = std::max(0.0f, std::min(b, hi0) - std::max(a, lo0));
  const float c1 = std::max(0.0f, std::min(b, hi1) - std::max(a, lo1));

  // UNION, not sum. Within arm/2 of the apex the two arms overlap; adding their
  // coverages there would push the pixel past full ink, and the notch below the
  // apex -- the thing that makes it read as a chevron rather than a triangle --
  // would fill in.
  const float outer = std::max(0.0f, std::min(b, std::max(hi0, hi1)) - std::max(a, std::min(lo0, lo1)));
  return std::min(outer, c0 + c1);
}

// Coverage of the whole pixel, sampled in y. Exact in x already; only the arms'
// ends vary within a row, so a handful of subsamples is the whole of it.
inline float coverage(const Geometry &g, const int px, const int py, const int subY = 4) {
  float cov = 0.0f;
  for (int k = 0; k < subY; ++k) {
    cov += coverageAtRow(g, px, static_cast<float>(py) + (k + 0.5f) / static_cast<float>(subY));
  }
  return std::min(1.0f, cov / static_cast<float>(subY));
}

// The pixel box worth visiting. Half-open in neither direction: both bounds are
// inclusive, because a partially covered edge pixel is still a pixel to paint.
struct Bounds {
  int x0, x1, y0, y1;
};

inline Bounds bounds(const Geometry &g) {
  const float halfArm = g.arm / 2.0f;
  return Bounds{static_cast<int>(std::floor(g.cx - g.chevH - halfArm)),
                static_cast<int>(std::ceil(g.cx + g.chevH + halfArm)),
                static_cast<int>(std::floor(g.top)),
                static_cast<int>(std::ceil(g.top + g.chevH))};
}

}  // namespace chevron
