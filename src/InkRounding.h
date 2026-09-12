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
// COST. The page is mostly paper, and paper far from ink is unchanged by
// construction, so rows whose (2r+1)-row band holds no ink are skipped whole
// (interline space, margins, the blank half of a chapter's last page). The
// two passes are integer, over zero-padded rows, so the inner loops carry no
// clamp. Measured on a 1056x1584 text page before this: 120 ms per compose
// at sigma 0.6 and 195 ms at 1.2 -- five to eight times the compose itself.
inline bool roundLevels(uint8_t *levels, int w, int h, int roundingPercent,
                        int spreadPercent, std::vector<int32_t> &scratch) {
  const float sigma = sigmaForPass(roundingPercent, spreadPercent);
  const float spread = kSpreadAt100 * static_cast<float>(clampSpread(spreadPercent)) / 100.0f;
  if (sigma <= 0.0f) return false;
  if (w <= 0 || h <= 0) return false;
  const Kernel k = kernelFor(sigma);
  const int r = k.radius;
  const size_t n = static_cast<size_t>(w) * static_cast<size_t>(h);
  const int pw = w + 2 * r;  // padded row width
  // scratch: [0, h) row flags, then h*pw horizontal results, then a padded row.
  scratch.assign(static_cast<size_t>(h) + n + static_cast<size_t>(h) * pw + pw, 0);
  int32_t *rowInk = scratch.data();
  int32_t *hpass = rowInk + h;      // h * pw, zero-padded
  int32_t *cov = hpass + static_cast<size_t>(h) * pw;  // n, final coverage*4096
  // Which rows hold any ink at all.
  for (int y = 0; y < h; y++) {
    const uint8_t *row = levels + static_cast<size_t>(y) * w;
    int32_t any = 0;
    for (int x = 0; x < w && !any; x++) any = row[x] != GrayscalePreview::kWhite;
    rowInk[y] = any;
  }
  // Which rows need work: within r of an inked row.
  std::vector<uint8_t> active(static_cast<size_t>(h), 0);
  for (int y = 0; y < h; y++) {
    if (!rowInk[y]) continue;
    for (int yy = std::max(0, y - r); yy <= std::min(h - 1, y + r); yy++) active[yy] = 1;
  }
  // Horizontal pass on active rows, into the padded plane (pad = clamp: the
  // page beyond the panel is the same tone as its border, so the pad column
  // repeats the edge pixel).
  for (int y = 0; y < h; y++) {
    int32_t *out = hpass + static_cast<size_t>(y) * pw;
    if (!active[y]) continue;
    const uint8_t *row = levels + static_cast<size_t>(y) * w;
    // padded copy of the row's coverage (0..255)
    int32_t *pad = cov;  // reuse cov's first row as the padded staging row
    for (int i = 0; i < r; i++) pad[i] = 255 - row[0];
    for (int x = 0; x < w; x++) pad[r + x] = 255 - row[x];
    for (int i = 0; i < r; i++) pad[r + w + i] = 255 - row[w - 1];
    for (int x = 0; x < w; x++) {
      int32_t acc = 0;
      const int32_t *src = pad + x;
      for (int i = 0; i <= 2 * r; i++) acc += src[i] * k.w[i];
      out[r + x] = acc;  // coverage * 4096, 0..1044480
    }
  }
  // Vertical pass, then gain, bias and requantize, on active rows only.
  const float gain = gainFor(sigma);
  // Two passes, two weight sums: the accumulator is coverage * 4096 * 4096.
  const float inv = 1.0f / (255.0f * static_cast<float>(1 << kWeightShift) *
                            static_cast<float>(1 << kWeightShift));
  for (int y = 0; y < h; y++) {
    if (!active[y]) continue;
    uint8_t *row = levels + static_cast<size_t>(y) * w;
    for (int x = 0; x < w; x++) {
      int64_t acc = 0;
      for (int i = -r; i <= r; i++) {
        const int yy = std::max(0, std::min(h - 1, y + i));
        const int32_t *src = active[yy] ? hpass + static_cast<size_t>(yy) * pw + r + x : nullptr;
        // An inactive row is pure paper by construction: coverage 0.
        if (src) acc += static_cast<int64_t>(*src) * k.w[i + r];
      }
      const float c = static_cast<float>(acc) * inv;
      if (c <= 0.0f) continue;  // clean paper stays clean paper, bit-exact
      const float biased = c + spread;
      row[x] = quantize4(0.5f + (biased - 0.5f) * gain);
    }
  }
  return true;
}

}  // namespace inkrounding
