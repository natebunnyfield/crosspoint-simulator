#pragma once
// THE SCANLINE FIELD, REBUILT ONLY WHERE THE BEAM CURRENT CHANGED.
//
// The dark page's raster (src/SurfaceTube.cpp, ensureScanlinesTexture) was
// rebuilt whole for every new frame: the (row, level) transmission table and
// every output pixel, ~26 ms of main thread per menu step on the desktop at 1x
// (crosspoint-reader docs/menu-nav-lag-2026-11-27.md, O6). The main thread is
// also the firmware's loop.
//
// WHAT A PIXEL DEPENDS ON, which is what makes a partial rebuild exact. A
// field pixel is
//     combine(params, T(y, bucket(x, y), defocus(x, y)), x, y, w, h)
// where bucket is that ONE pixel's beam-current level (16 buckets of the
// composed frame read back at build time), T is the per-(row, level, anchor)
// transmission table, and defocus is a per-pixel map of the output size and the
// dial. Nothing reads a neighbor's bucket: rowTransmission sums the nearby
// LINES at the pixel's own level, not the levels of nearby pixels. So with the
// parameters, the size and the dial unchanged, a pixel can only change where
// its own bucket did, and recomputing exactly those pixels into the previous
// field gives the field a whole rebuild would. The bucket is compared rather
// than the ink, because it is read off the COMPOSED frame -- the phosphor
// trail, the beam's sweep and the overlay all reach it -- so "where the ink
// moved" would not be exact; "where the bucket moved" is, by construction.
// tests/scanlines_dirty_test.cpp proves it against the whole rebuild.
//
// The arithmetic below is the loop it replaced in SurfaceTube.cpp, statement
// for statement; both the whole and the partial build run it.
//
// Header-only: cmake/CrossPointSources.cmake is generated, and a new .cpp here
// would go stale in it.
#include <cstddef>
#include <cstdint>
#include <vector>

#include "Scanlines.h"

namespace scandirty {

struct Rect {
  int x = 0;
  int y = 0;
  int w = 0;
  int h = 0;
  bool empty() const { return w <= 0 || h <= 0; }
};

// The defocus inputs: the per-pixel map (nullptr when the dial is off, which
// selects the one-anchor table), and the span and anchor step it decodes with.
struct Defocus {
  const uint8_t *map = nullptr;
  float span = 0.0f;
  float step = 0.0f;
};

// The per-(row, level bucket [, defocus anchor]) transmission: the erf work,
// once per row rather than once per pixel. Depends on the parameters, the
// height and the anchors only -- not on the page.
inline void buildRowTable(const scanlines::Params &params, int h, int anchors,
                          float defocusStep, std::vector<float> &rowT) {
  rowT.assign(static_cast<size_t>(h) * 16 * anchors, 0.0f);
  for (int y = 0; y < h; ++y)
    for (int b = 0; b < 16; ++b) {
      const float level = (static_cast<float>(b) + 0.5f) / 16.0f;
      float *cell = rowT.data() + (static_cast<size_t>(y) * 16 + b) * anchors;
      for (int d = 0; d < anchors; ++d)
        cell[d] = scanlines::rowTransmission(
            params, static_cast<float>(y), level,
            1.0f + defocusStep * static_cast<float>(d));
    }
}

inline uint32_t pixelAt(const scanlines::Params &params, const float *tRow,
                        int anchors, uint8_t bucket, const uint8_t *dRow,
                        const Defocus &df, int x, int y, int w, int h) {
  float t;
  if (dRow) {
    // Interpolated between the two bracketing anchors: an anchor edge on a
    // field this smooth would otherwise draw a contour across the screen.
    const float fa = (df.span * (static_cast<float>(dRow[x]) / 255.0f)) /
                     (df.step > 0.0f ? df.step : 1.0f);
    int a0 = static_cast<int>(fa);
    if (a0 < 0) a0 = 0;
    if (a0 > anchors - 1) a0 = anchors - 1;
    const int a1 = a0 + 1 < anchors ? a0 + 1 : a0;
    const float fr = fa - static_cast<float>(a0);
    const float *cell = tRow + static_cast<size_t>(bucket) * anchors;
    t = cell[a0] + (cell[a1] - cell[a0]) * fr;
  } else {
    t = tRow[bucket];
  }
  const uint32_t m = scanlines::combine(params, t, x, y, w, h);
  return 0xFF000000u | (m << 16) | (m << 8) | m;
}

// Recomputes into `field` (w*h, row pitch w) every pixel whose bucket differs
// from `prev` -- every pixel when `prev` is nullptr -- and returns the bounding
// box of what it recomputed (empty when nothing changed). The caller uploads
// that box from `field`.
inline Rect refill(const scanlines::Params &params, const float *rowT,
                   int anchors, const uint8_t *bucket, const uint8_t *prev,
                   const Defocus &df, int w, int h, uint32_t *field) {
  int minX = w, minY = h, maxX = -1, maxY = -1;
  for (int y = 0; y < h; ++y) {
    uint32_t *row = field + static_cast<size_t>(y) * w;
    const float *tRow = rowT + static_cast<size_t>(y) * 16 * anchors;
    const uint8_t *bRow = bucket + static_cast<size_t>(y) * w;
    const uint8_t *pRow = prev ? prev + static_cast<size_t>(y) * w : nullptr;
    const uint8_t *dRow = df.map ? df.map + static_cast<size_t>(y) * w : nullptr;
    for (int x = 0; x < w; ++x) {
      if (pRow && pRow[x] == bRow[x]) continue;
      row[x] = pixelAt(params, tRow, anchors, bRow[x], dRow, df, x, y, w, h);
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      maxY = y;
    }
  }
  if (maxY < 0) return Rect{};
  return Rect{minX, minY, maxX - minX + 1, maxY - minY + 1};
}

}  // namespace scandirty
