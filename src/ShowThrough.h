#pragma once

// SHOW-THROUGH -- the other side of the leaf, faintly visible through it, for
// the LIGHT page.
//
// DOCTRINE (2026-08-22): light mode is paper and ink. This is the paper
// phenomenon that carries INFORMATION rather than texture -- every other pass
// on the sheet is stationary noise, and this one is a picture of another page.
// Design, provenance and the honesty problem below: docs/show-through.md.
//
// THE MODEL, in the order the physics happens:
//
//   - The verso is printed on the BACK of this sheet, so what reaches the
//     recto is the verso MIRRORED left-to-right. mirrorOutputX is that, and it
//     is applied in PRESENTED space rather than in the framebuffer, because the
//     framebuffer is landscape and the page is usually rotated into it -- a
//     mirror about the framebuffer's x axis is a mirror about the page's
//     VERTICAL axis, which is upside-down show-through.
//   - Light crossing the sheet scatters through its thickness, so the image is
//     heavily blurred: line bands survive, letters do not. That is exactly what
//     the eye reads on a real page, and it is also what makes shipping the
//     WRONG page honest (see the doc).
//   - It DARKENS ONLY. Ink on the far side removes light that would otherwise
//     have come back out of this side; there is no arrangement in which the
//     verso brightens the recto. Same modulate contract as PhosphorGrain,
//     Letterpress and Scanlines -- an additive pass is the page-flash bug class.
//   - IT SCALES WITH THE STOCK'S OPACITY. A bible sheet shows a great deal and
//     a calfskin vellum almost none, and gating on the stock is the difference
//     between the feature and a uniform smudge. The per-stock number lives with
//     the other paper properties (lightink::showThroughScaleFor); this header
//     stays ignorant of the paper TABLE and takes a scalar, the same contract
//     Letterpress::Params::toothScale has.
//
// WHY THE MAP IS COARSE, AND WHY THAT IS NOT A SHORTCUT. The field is a heavy
// blur of the verso, so its bandwidth is a fraction of the page's. Building it
// at kCellPx x kCellPx BOX AVERAGES is a correct prefilter for that bandwidth
// (it is the only prefilter -- point-sampling a 1-bit dithered page at 1/8
// would alias the dither, which is the ST-008 failure class arriving through
// the back door), and it makes the whole pass affordable: the blur runs on a
// map ~1/64 the size of the framebuffer.
//
// WHY IT COSTS THE PAPER BUDGET. It darkens paper, so it is the fourth
// consumer of the 7:1 headroom the tooth, the wires and the marks already
// share. meanDarkeningBound is its declared share; HalDisplay subtracts it
// before the marks are generated, so the composite cannot breach the floor by
// construction and a page with show-through OFF is byte-identical to one from
// before this file existed.
//
// Pure and clock-free; tests/show_through_test.cpp is the only instrument.

#include <cmath>
#include <cstddef>
#include <cstdint>

namespace showthrough {

// STRENGTH IS A PERCENTAGE OF STANDARD, composed multiplicatively with the
// stock's own factor -- the tooth/formation shape. 0 is off (bit-exact),
// 100 is the reference sheet's own show-through.
constexpr int kStrengthOff = 0;
constexpr int kStrengthStandard = 100;
constexpr int kStrengthMax = 300;

// Peak darkening under SOLID verso ink on the reference sheet, and the cap.
//
// 0.055 is the measured order of magnitude rather than a taste choice: ISO 2471
// opacity for an ordinary book text stock is ~0.94, so ~6% of the incident
// light crosses the sheet, and print-through measurements on offset book papers
// (ISO 2834 family) put the reflectance loss behind a solid at a few percent.
// The cap exists because the ladder multiplies by the stock factor and Kozo's
// is 3.7x: without it a washi page would be a gray wash rather than a thin one.
constexpr float kDepthAt100 = 0.055f;
constexpr float kDepthMax = 0.22f;

// Conservative bound on the MEAN verso density over a page, used to convert a
// depth into a mean darkening for the budget split. A page of body text sits
// near 0.10 after the blur; 0.35 covers a chapter opening, a full-page image
// and a menu screen with a selection fill. Same role kMaxMeanGap plays for
// scanlines.
constexpr float kMaxMeanVerso = 0.35f;

// The floor a multiplier may reach. Show-through cannot extinguish a page.
constexpr float kMinMultiplier = 0.70f;

// --- THE MAP ---------------------------------------------------------------

// Framebuffer pixels per verso cell. 8 at the app's 2x render scale is 4
// SOURCE page pixels, roughly a sixth of a body-text line height -- coarse
// enough to be affordable, fine enough that the LINE BAND structure the eye
// actually reads survives the downsample.
constexpr int kCellPx = 8;

// Output pixels per node of the caller's resampling grid. The field is
// low-frequency by construction, so the caller may build it on this lattice and
// bilinearly interpolate per pixel instead of inverting the presentation
// transform once per pixel. 4 keeps the interpolation error under one code
// value at every offered strength.
constexpr int kOutCellPx = 4;

// Blur passes of the binomial [1 4 6 4 1] kernel, separable, on the map. Two
// passes is sigma ~1.41 cells; with the cell's own box that is an effective
// ~11 framebuffer pixels of spread -- letters gone, line bands intact.
constexpr int kBlurPasses = 2;

inline int mapDim(int px) {
  if (px <= 0) return 0;
  return (px + kCellPx - 1) / kCellPx;
}

inline int clampStrength(int percent) {
  if (percent < kStrengthOff) return kStrengthOff;
  if (percent > kStrengthMax) return kStrengthMax;
  return percent;
}

// BOX-AVERAGE the inkness plane into the map. `inkness` is the letterpress
// pass's own 0..255 plane (255 = solid ink) in FRAMEBUFFER space; `out` must
// hold mapDim(w) * mapDim(h) bytes. Partial edge cells average only the pixels
// they actually cover, so a page whose height is not a multiple of kCellPx does
// not fade out along its last row.
inline void downsample(const uint8_t *inkness, int w, int h, uint8_t *out) {
  const int mw = mapDim(w), mh = mapDim(h);
  if (!inkness || !out || mw <= 0 || mh <= 0) return;
  for (int my = 0; my < mh; ++my) {
    const int y0 = my * kCellPx;
    const int y1 = (y0 + kCellPx < h) ? y0 + kCellPx : h;
    for (int mx = 0; mx < mw; ++mx) {
      const int x0 = mx * kCellPx;
      const int x1 = (x0 + kCellPx < w) ? x0 + kCellPx : w;
      uint32_t sum = 0, n = 0;
      for (int y = y0; y < y1; ++y) {
        const uint8_t *row = inkness + static_cast<std::size_t>(y) * w;
        for (int x = x0; x < x1; ++x) {
          sum += row[x];
          n++;
        }
      }
      out[static_cast<std::size_t>(my) * mw + mx] =
          n ? static_cast<uint8_t>((sum + n / 2) / n) : 0;
    }
  }
}

// Separable binomial blur, in place, using `scratch` (same size). CLAMPED at
// the edges rather than wrapped: the sheet has an edge, and wrapping would
// carry the last line of text onto the head margin.
inline void blur(uint8_t *map, int mw, int mh, uint8_t *scratch) {
  if (!map || !scratch || mw <= 0 || mh <= 0) return;
  auto at = [&](const uint8_t *src, int x, int y) -> int {
    if (x < 0) x = 0;
    if (x >= mw) x = mw - 1;
    if (y < 0) y = 0;
    if (y >= mh) y = mh - 1;
    return src[static_cast<std::size_t>(y) * mw + x];
  };
  for (int pass = 0; pass < kBlurPasses; ++pass) {
    for (int y = 0; y < mh; ++y)
      for (int x = 0; x < mw; ++x)
        scratch[static_cast<std::size_t>(y) * mw + x] = static_cast<uint8_t>(
            (at(map, x - 2, y) + 4 * at(map, x - 1, y) + 6 * at(map, x, y) +
             4 * at(map, x + 1, y) + at(map, x + 2, y) + 8) /
            16);
    for (int y = 0; y < mh; ++y)
      for (int x = 0; x < mw; ++x)
        map[static_cast<std::size_t>(y) * mw + x] = static_cast<uint8_t>(
            (at(scratch, x, y - 2) + 4 * at(scratch, x, y - 1) +
             6 * at(scratch, x, y) + 4 * at(scratch, x, y + 1) +
             at(scratch, x, y + 2) + 8) /
            16);
  }
}

// Bilinear sample of the map at normalized FRAMEBUFFER coordinates, 0..1.
// Returns the verso density, 0 at bare paper and 1 under solid ink.
inline float sampleAt(const uint8_t *map, int mw, int mh, float u, float v) {
  if (!map || mw <= 0 || mh <= 0) return 0.0f;
  if (u < 0.0f) u = 0.0f;
  if (u > 1.0f) u = 1.0f;
  if (v < 0.0f) v = 0.0f;
  if (v > 1.0f) v = 1.0f;
  const float fx = u * static_cast<float>(mw) - 0.5f;
  const float fy = v * static_cast<float>(mh) - 0.5f;
  int x0 = static_cast<int>(std::floor(fx));
  int y0 = static_cast<int>(std::floor(fy));
  const float tx = fx - static_cast<float>(x0);
  const float ty = fy - static_cast<float>(y0);
  auto px = [&](int x, int y) -> float {
    if (x < 0) x = 0;
    if (x >= mw) x = mw - 1;
    if (y < 0) y = 0;
    if (y >= mh) y = mh - 1;
    return static_cast<float>(map[static_cast<std::size_t>(y) * mw + x]) / 255.0f;
  };
  const float a = px(x0, y0) + (px(x0 + 1, y0) - px(x0, y0)) * tx;
  const float b = px(x0, y0 + 1) + (px(x0 + 1, y0 + 1) - px(x0, y0 + 1)) * tx;
  return a + (b - a) * ty;
}

// THE MIRROR, in PRESENTED output pixels: the point on the verso that lies
// directly behind output column `ox` of a page occupying [panelX, panelX+panelW).
// Applied here rather than in framebuffer space because the framebuffer is
// landscape and the page is rotated into it -- see the header comment.
inline int mirrorOutputX(int ox, int panelX, int panelW) {
  if (panelW <= 0) return ox;
  return 2 * panelX + panelW - 1 - ox;
}

// --- THE FIELD -------------------------------------------------------------

struct Params {
  int strengthPercent = kStrengthStandard;
  // The chosen stock's factor, from lightink::showThroughScaleFor(). 1.0 is
  // the reference sheet, so a caller that does not know the paper renders the
  // reference's show-through.
  float stockScale = 1.0f;
  // Largest MEAN darkening the paper can still take once the tooth and the
  // wires have spent theirs. 1.0 means "no constraint".
  float budgetMeanDarkening = 1.0f;
};

// Peak darkening under solid verso ink, after the ladder, the stock and the
// palette's remaining budget. 0 when off, exactly.
inline float effectiveDepth(const Params &p) {
  const int s = clampStrength(p.strengthPercent);
  if (s == kStrengthOff) return 0.0f;
  float scale = p.stockScale;
  if (scale < 0.0f) scale = 0.0f;
  float d = kDepthAt100 * static_cast<float>(s) /
            static_cast<float>(kStrengthStandard) * scale;
  if (d > kDepthMax) d = kDepthMax;
  const float budget = p.budgetMeanDarkening;
  if (budget < 1.0f && d * kMaxMeanVerso > budget) d = budget / kMaxMeanVerso;
  return d < 0.0f ? 0.0f : d;
}

// What this pass declares it will spend of the shared paper budget, so the
// marks can be generated against what is left. Conservative by construction:
// the real mean is depth * (mean verso density), and kMaxMeanVerso bounds the
// second factor for any page.
inline float meanDarkeningBound(const Params &p) {
  return effectiveDepth(p) * kMaxMeanVerso;
}

// THE ANSWER: the 0..255 modulate value for one pixel, given the verso density
// under it. 255 is untouched; strength 0 (or a stock that passes no light)
// returns 255 for every density, so OFF is bit-exact.
inline uint8_t multiplierAt(const Params &p, float versoDensity) {
  const float depth = effectiveDepth(p);
  if (depth <= 0.0f) return 255;
  if (versoDensity < 0.0f) versoDensity = 0.0f;
  if (versoDensity > 1.0f) versoDensity = 1.0f;
  float m = 1.0f - depth * versoDensity;
  if (m < kMinMultiplier) m = kMinMultiplier;
  if (m > 1.0f) m = 1.0f;
  return static_cast<uint8_t>(m * 255.0f + 0.5f);
}

}  // namespace showthrough
