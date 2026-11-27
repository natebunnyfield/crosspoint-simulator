#pragma once
// THE LETTERPRESS FIELD, REBUILT ONLY WHERE THE INK MOVED.
//
// The light page's panel field (src/SurfaceSheet.cpp, ensureLetterpressTexture)
// is content-locked, so every new frame rebuilt all of it: 1600x960 at the
// phone's 2x, ~54 ms on the main thread per menu step on the iOS Simulator
// (crosspoint-reader docs/menu-nav-lag-2026-11-27.md) -- for a cursor move
// that changes two rows. The main thread is also the firmware's loop, so for
// those 54 ms no press was read either.
//
// letterpress::multiplierAt is a pure function of the page's Params, the 3x3
// inkness window around a pixel, and the pixel's position. So when only the
// pixels change, a pixel's multiplier can only change if something inside its
// 3x3 window did: the bounding box of the changed inkness, grown by one pixel,
// covers every multiplier that can differ, and everything outside it is
// already in the texture. Rebuilding that box is BIT-IDENTICAL to rebuilding
// the whole field; tests/letterpress_dirty_test.cpp proves it against the full
// rebuild over random edits.
//
// Header-only: cmake/CrossPointSources.cmake is generated, and a new .cpp here
// would go stale in it.
#include <cstdint>
#include <cstring>

#include "Letterpress.h"

namespace letterdirty {

struct Rect {
  int x = 0;
  int y = 0;
  int w = 0;
  int h = 0;
  bool empty() const { return w <= 0 || h <= 0; }
};

// The pixels whose 3x3 window holds a changed inkness: the bounding box of the
// changed pixels, grown by one on every side and clamped to the field. Empty
// when nothing changed (a repaint of the same frame).
inline Rect changedRect(const uint8_t *before, const uint8_t *after, int w,
                        int h) {
  int minX = w, minY = h, maxX = -1, maxY = -1;
  for (int y = 0; y < h; ++y) {
    const uint8_t *a = before + static_cast<size_t>(y) * w;
    const uint8_t *b = after + static_cast<size_t>(y) * w;
    if (std::memcmp(a, b, static_cast<size_t>(w)) == 0) continue;
    int l = 0;
    while (a[l] == b[l]) ++l;
    int r = w - 1;
    while (a[r] == b[r]) --r;
    if (l < minX) minX = l;
    if (r > maxX) maxX = r;
    if (y < minY) minY = y;
    maxY = y;
  }
  if (maxY < 0) return Rect{};
  const int x0 = minX > 0 ? minX - 1 : 0;
  const int y0 = minY > 0 ? minY - 1 : 0;
  const int x1 = maxX < w - 1 ? maxX + 1 : w - 1;
  const int y1 = maxY < h - 1 ? maxY + 1 : h - 1;
  return Rect{x0, y0, x1 - x0 + 1, y1 - y0 + 1};
}

// The field's ARGB pixels over `r`, written row by row to `out` (pitch in
// pixels). The one loop both the whole build (r = the field) and the partial
// one run, so the two cannot drift apart.
inline void fillField(const letterpress::Params &p, const uint8_t *inkness,
                      int w, int h, const Rect &r, uint32_t *out,
                      int outPitchPx) {
  auto tAt = [&](int x, int y) {
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (x >= w) x = w - 1;
    if (y >= h) y = h - 1;
    return static_cast<float>(inkness[static_cast<size_t>(y) * w + x]) / 255.0f;
  };
  for (int y = r.y; y < r.y + r.h; ++y) {
    uint32_t *row = out + static_cast<size_t>(y - r.y) * outPitchPx;
    for (int x = r.x; x < r.x + r.w; ++x) {
      float win[3][3];
      for (int dy = -1; dy <= 1; ++dy)
        for (int dx = -1; dx <= 1; ++dx)
          win[dy + 1][dx + 1] = tAt(x + dx, y + dy);
      const uint32_t m = letterpress::multiplierAt(p, win, x, y, w, h);
      // Achromatic, like the grain: pressed ink is MORE of its own pigment
      // and a deboss shadow is LESS of the paper's light, not a different
      // color.
      row[x - r.x] = 0xFF000000u | (m << 16) | (m << 8) | m;
    }
  }
}

}  // namespace letterdirty
