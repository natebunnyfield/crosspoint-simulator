#pragma once

// INK ROUNDING -- what a press does to the CORNERS of type, for the LIGHT page.
//
// Owner ask 2026-09-11, after a trial build carried Atkinson Hyperlegible Soft
// (a cut with every sharp corner rounded in the outlines): "instead of Soft
// version of one font, let's make an ios settings for rounding sharp corners
// and other letterpress simulation effects." So the rounding moves out of one
// font's outlines and into the renderer, where every family gets it.
//
// WHAT IT MODELS. Ink on an absorbent sheet does not hold a sharp corner: it
// wicks into the fiber, so every convex corner of a glyph fills out into an
// arc and every concave corner (the crotch of a v, the junction of a serif)
// fills IN. The printing trade's name for the tonal half of this is dot gain
// (25-30% on uncoated stock, ISO 12647); docs/surface-roadmap.md section 1b
// asked for it and priced it. This header is the SHAPE half plus the tonal
// half, in one pass.
//
// HOW. A morphological closing/opening at once: blur the ink coverage with a
// small Gaussian, then re-threshold it. A corner of radius 0 comes out with
// radius ~ the blur's sigma; a straight edge comes back where it was, so a
// stem's width does not change (spread aside). The re-threshold has GAIN so
// the blur does not soften the edge it just rounded -- the output is as crisp
// as the input, only the corners moved.
//
// FOUR LEVELS IN, FOUR LEVELS OUT. Owner ruling 2026-08-24: "Keep 4 levels --
// fidelity is the point." The blur produces a continuum; the output is
// requantized to exactly GrayscalePreview's four (0, 96, 200, 255) so the page
// is still a 2-bit e-ink page with rounder type, not a deeper render sneaking
// in under another name. tests/ink_rounding_test.cpp pins that.
//
// WHERE IT OPERATES. On the LEVEL image, panel space, before the palette ramp
// -- inside the framebuffer-to-pixel conversion, NOT in the darken-only surface
// stack. It has to be here: rounding a convex corner REMOVES ink, and the
// surface passes are modulates that can only add darkness. It is the one
// place in this repo a pass is allowed to lighten a pixel, and it can do so
// only because it is reshaping the ink, not lighting the paper. Runs on the
// render task once per page, and again on a reconvert.
//
// TWO DIALS, one physical variable each:
//   roundingPercent -- the blur sigma, i.e. the corner radius. 0 is bit-exact
//                      off (the pass is skipped entirely). 100 is the shipped
//                      standard; the offered rungs are 0/50/100/200.
//   spreadPercent   -- the threshold bias, i.e. dot gain. Strokes get heavier
//                      by a per-page constant; counters can close at small
//                      sizes if this is pushed, which is why its ceiling is
//                      low and the test checks a 3 px stem stays open.
//
// Pure and clock-free, like PhosphorGrain and Letterpress: every failure mode
// is a wrong picture.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>

#include "GrayscalePreview.h"

namespace inkrounding {

constexpr int kOff = 0;
constexpr int kSubtle = 50;
constexpr int kStandard = 100;
constexpr int kHeavy = 150;
constexpr int kMax = 200;

constexpr int kSpreadOff = 0;
constexpr int kSpreadStandard = 100;
constexpr int kSpreadMax = 200;

// The corner radius at 100%, in PANEL pixels, at the 2x render scale the app
// ships (docs/ios-render-scale.md). MEASURED, not chosen: the first ladder
// had 0.6 here, and on a real page 0.3 (subtle) moved zero pixels, 0.6 moved
// 0.4% of the pixels in a text crop, and 1.2 was the first rung a reader
// could see in a 6x crop -- the page is antialiased already, so a corner is
// only visibly rounder once the sigma is about a device pixel (the phone
// presents 2x at ~0.8). So 1.2 is what the eye called "standard" and 1.5
// gives a little on top for the presentation minification.
constexpr float kSigmaAt100 = 1.5f;

// Spread has its own floor so it acts without rounding: dot gain IS a blur
// followed by a lower threshold, and with no blur there is nothing to push
// the edge into.
constexpr float kSpreadSigmaMin = 0.75f;

// Coverage bias at 100% spread, as a fraction of full ink, applied ONLY where
// the blurred coverage is above zero -- clean paper away from any ink stays
// bit-exact paper. The first version biased every pixel and turned the whole
// sheet light gray (81% of a text crop moved by 24 levels); the test now
// pins paper at spread 200.
constexpr float kSpreadAt100 = 0.12f;

// The kernel never reaches past this many pixels either side; above it the
// pass is spending on tails the eye cannot see.
constexpr int kMaxKernelRadius = 5;

inline int clampRounding(int p) { return std::max(kOff, std::min(kMax, p)); }
inline int clampSpread(int p) { return std::max(kSpreadOff, std::min(kSpreadMax, p)); }

inline float sigmaFor(int roundingPercent) {
  return kSigmaAt100 * static_cast<float>(clampRounding(roundingPercent)) / 100.0f;
}

inline float sigmaForPass(int roundingPercent, int spreadPercent) {
  const float s = sigmaFor(roundingPercent);
  if (clampSpread(spreadPercent) > 0) return std::max(s, kSpreadSigmaMin);
  return s;
}

// Re-threshold gain, DERIVED so that a straight edge stays exactly where it
// was: the pixel whose center is half a pixel inside the ink sees coverage
// Phi(0.5/sigma) after the blur, and the gain maps that back to full ink
// (>= the black threshold, 0.812) and its mirror outside back to clean paper
// (< the white threshold, 0.108). 0.45 is the larger of the two distances
// from 0.5, with margin. A convex corner pixel sees Phi(0.5/sigma)^2, which
// the same gain leaves BELOW full ink -- that is the rounding. Without this
// derivation the first version softened every edge into a 2 px ramp at heavy
// (the test caught it: mid-side pixels moved).
inline float normalCdf(float x) { return 0.5f * (1.0f + std::erf(x / std::sqrt(2.0f))); }
inline float gainFor(float sigma) {
  if (sigma <= 0.0f) return 1.0f;
  const float edge = normalCdf(0.5f / sigma) - 0.5f;
  return edge <= 0.0f ? 1.0f : std::max(1.0f, 0.45f / edge);
}

// Coverage of each of the four levels, as a fraction of full ink.
inline float coverageOf(uint8_t level) { return (255.0f - level) / 255.0f; }

// The nearest of the four levels to a coverage value. Boundaries are the
// midpoints between the four coverages, so a pixel that did not move stays.
inline uint8_t quantize4(float coverage) {
  const float c = std::max(0.0f, std::min(1.0f, coverage));
  constexpr float cLight = (255.0f - GrayscalePreview::kLight) / 255.0f;  // ~0.216
  constexpr float cDark = (255.0f - GrayscalePreview::kDark) / 255.0f;    // ~0.624
  if (c < cLight * 0.5f) return GrayscalePreview::kWhite;
  if (c < (cLight + cDark) * 0.5f) return GrayscalePreview::kLight;
  if (c < (cDark + 1.0f) * 0.5f) return GrayscalePreview::kDark;
  return GrayscalePreview::kBlack;
}

// Fixed-point kernel: weights sum to 1 << kWeightShift.
constexpr int kWeightShift = 12;

struct Kernel {
  int radius = 0;
  int32_t w[2 * kMaxKernelRadius + 1] = {};
};

inline Kernel kernelFor(float sigma) {
  Kernel k;
  if (sigma <= 0.0f) {
    k.radius = 0;
    k.w[0] = 1 << kWeightShift;
    return k;
  }
  k.radius = std::min(kMaxKernelRadius, static_cast<int>(std::ceil(3.0f * sigma)));
  float fw[2 * kMaxKernelRadius + 1];
  float sum = 0.0f;
  for (int i = -k.radius; i <= k.radius; i++) {
    const float v = std::exp(-0.5f * (i * i) / (sigma * sigma));
    fw[i + k.radius] = v;
    sum += v;
  }
  int32_t isum = 0;
  for (int i = 0; i <= 2 * k.radius; i++) {
    k.w[i] = static_cast<int32_t>(std::lround(fw[i] / sum * (1 << kWeightShift)));
    isum += k.w[i];
  }
  k.w[k.radius] += (1 << kWeightShift) - isum;  // land the rounding on the center
  return k;
}

// Round the corners of a w*h level image (values in {0, 96, 200, 255}), in
// place. `scratch` is resized as needed and may be reused across calls.
// Returns false, and touches nothing, when the pass is off.
//
// COST. Only pixels within the kernel's reach of ink can change, and on a
// text page that is a minority of the sheet. A NEAR mask is built first -- the
// ink mask dilated by r horizontally then vertically (two linear sweeps with a
// countdown, no per-pixel window) -- and both blur passes run only where it is
// set. A pixel outside it has no ink within r in any direction, so its
// horizontal blur is zero and the zero-initialised plane already holds its
// answer for the vertical taps of its neighbours. The passes are integer over
// a padded plane, so the inner loops carry no clamp and no branch. Measured
// before this (1056x1584 text page, desktop): 135-200 ms per compose against
// the compose's own 24; the first cut, skipping blank ROWS, bought nothing
// because rows are not where the paper is on a text page.
inline bool roundLevels(uint8_t *levels, int w, int h, int roundingPercent,
                        int spreadPercent, std::vector<uint32_t> &scratch) {
  const float sigma = sigmaForPass(roundingPercent, spreadPercent);
  const float spread = kSpreadAt100 * static_cast<float>(clampSpread(spreadPercent)) / 100.0f;
  if (sigma <= 0.0f) return false;
  if (w <= 0 || h <= 0) return false;
  const Kernel k = kernelFor(sigma);
  const int r = k.radius;
  const int pw = w + 2 * r;   // padded width
  const int ph = h + 2 * r;   // padded height
  const size_t pn = static_cast<size_t>(pw) * static_cast<size_t>(ph);
  const size_t n = static_cast<size_t>(w) * static_cast<size_t>(h);
  // scratch: padded coverage plane, padded horizontal-pass plane, near mask.
  scratch.assign(2 * pn + (n + 3) / 4, 0);
  uint32_t *cov = scratch.data();
  uint32_t *hp = cov + pn;
  uint8_t *near = reinterpret_cast<uint8_t *>(hp + pn);
  std::memset(near, 0, n);

  // Coverage into the padded plane, and the ink mask dilated by r along x.
  for (int y = 0; y < h; y++) {
    const uint8_t *row = levels + static_cast<size_t>(y) * w;
    uint32_t *crow = cov + static_cast<size_t>(y + r) * pw + r;
    uint8_t *nrow = near + static_cast<size_t>(y) * w;
    int reach = 0;  // pixels still within r to the right of the last ink
    // Pad columns repeat the edge pixel: the page beyond the panel is the
    // same tone as its border (a solid field must come back solid).
    for (int i = 1; i <= r; i++) {
      crow[-i] = 255u - row[0];
      crow[w - 1 + i] = 255u - row[w - 1];
    }
    for (int x = 0; x < w; x++) {
      const uint8_t v = row[x];
      crow[x] = 255u - v;
      if (v != GrayscalePreview::kWhite) {
        reach = 2 * r + 1;
        const int from = std::max(0, x - r);
        for (int xx = from; xx < x; xx++) nrow[xx] = 1;  // the r to the left
      }
      if (reach > 0) {
        nrow[x] = 1;
        reach--;
      }
    }
  }
  // Dilate the mask by r along y: a column sweep with the same countdown.
  for (int x = 0; x < w; x++) {
    int reach = 0;
    for (int y = 0; y < h; y++) {
      uint8_t &m = near[static_cast<size_t>(y) * w + x];
      if (m) {
        reach = r;
        // the r above: walk back only as far as the last set one
        for (int yy = y - 1; yy >= std::max(0, y - r); yy--) {
          uint8_t &u = near[static_cast<size_t>(yy) * w + x];
          if (u) break;
          u = 1;
        }
      } else if (reach > 0) {
        m = 1;
        reach--;
      }
    }
  }
  // Horizontal pass where near.
  for (int y = 0; y < h; y++) {
    const uint8_t *nrow = near + static_cast<size_t>(y) * w;
    const uint32_t *crow = cov + static_cast<size_t>(y + r) * pw;  // x offset 0 = pad
    uint32_t *orow = hp + static_cast<size_t>(y + r) * pw + r;
    for (int x = 0; x < w; x++) {
      if (!nrow[x]) continue;
      uint32_t acc = 0;
      const uint32_t *src = crow + x;
      for (int i = 0; i <= 2 * r; i++) acc += src[i] * static_cast<uint32_t>(k.w[i]);
      orow[x] = acc;  // <= 255 * 4096
    }
  }
  // Pad rows repeat the edge rows' horizontal results, for the same reason.
  for (int i = 1; i <= r; i++) {
    std::memcpy(hp + static_cast<size_t>(r - i) * pw, hp + static_cast<size_t>(r) * pw,
                static_cast<size_t>(pw) * sizeof(uint32_t));
    std::memcpy(hp + static_cast<size_t>(r + h - 1 + i) * pw,
                hp + static_cast<size_t>(r + h - 1) * pw,
                static_cast<size_t>(pw) * sizeof(uint32_t));
  }
  // Vertical pass where near, then bias, gain and requantize.
  const float gain = gainFor(sigma);
  const float inv = 1.0f / (255.0f * static_cast<float>(1 << kWeightShift) *
                            static_cast<float>(1 << kWeightShift));
  for (int y = 0; y < h; y++) {
    const uint8_t *nrow = near + static_cast<size_t>(y) * w;
    uint8_t *row = levels + static_cast<size_t>(y) * w;
    const uint32_t *col0 = hp + static_cast<size_t>(y) * pw + r;  // row y-r, x offset
    for (int x = 0; x < w; x++) {
      if (!nrow[x]) continue;
      uint64_t acc = 0;
      const uint32_t *src = col0 + x;
      for (int i = 0; i <= 2 * r; i++)
        acc += static_cast<uint64_t>(src[static_cast<size_t>(i) * pw]) *
               static_cast<uint32_t>(k.w[i]);
      const float c = static_cast<float>(acc) * inv;
      if (c <= 0.0f) continue;  // clean paper stays clean paper, bit-exact
      row[x] = quantize4(0.5f + (c + spread - 0.5f) * gain);
    }
  }
  return true;
}

}  // namespace inkrounding
