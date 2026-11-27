// Pins src/ScanlinesDirty.h: recomputing only the pixels whose beam-current
// bucket changed must give EXACTLY the field a whole rebuild gives. The
// shipping build (src/SurfaceTube.cpp) keeps the last field, its bucket map
// and its (row, level, anchor) table, and refills the changed pixels; this does
// the same in memory and compares every pixel with a whole rebuild from the new
// map, with the corner defocus off (the shipped one-anchor table) and on (the
// three-anchor, interpolated one). crosspoint-reader
// docs/menu-nav-lag-2026-11-27.md (O6) has the measurement.
#include <cstdint>
#include <cstdio>
#include <random>
#include <vector>

#include "../src/CornerDefocus.h"
#include "../src/ScanlinesDirty.h"
#include "TestCheck.h"

namespace {

constexpr int W = 97;  // odd sizes, so no edit lines up with the pitch
constexpr int H = 61;

struct Setup {
  scanlines::Params params;
  int anchors = 1;
  std::vector<float> rowT;
  std::vector<uint8_t> map;  // empty: defocus off
  scandirty::Defocus df;
};

Setup makeSetup(int defocusPercent) {
  Setup s;
  // The phone's frozen page: Subtle intensity, Extreme bloom, Fine pitch.
  s.params.intensityPercent = 50;
  s.params.seed = 7u ^ 0x5343414Eu;
  s.params.pitchPx = 2.0f;
  s.params.mottleDepth = scanlines::mottleDepthFor(50);
  s.params.bloomGain = scanlines::bloomGainFor(scanlines::kBloomExtreme);
  s.params.budgetMeanDarkening = 0.4f;
  float step = 0.0f;
  if (defocusPercent > 0) {
    // The map as SurfaceTube.cpp's ensureDefocusMap builds it (input data
    // here; what is under test is that both builds read the same one).
    cornerdefocus::Params cd;
    cd.strengthPercent = defocusPercent;
    const float span = cornerdefocus::maxSigmaScale(cd) - 1.0f;
    s.map.assign(static_cast<size_t>(W) * H, 0);
    for (int y = 0; y < H; ++y)
      for (int x = 0; x < W; ++x) {
        const float t = (cornerdefocus::sigmaScaleAt(cd, x, y, W, H) - 1.0f) / span;
        const int v = static_cast<int>(t * 255.0f + 0.5f);
        s.map[static_cast<size_t>(y) * W + x] =
            static_cast<uint8_t>(v < 0 ? 0 : (v > 255 ? 255 : v));
      }
    s.anchors = 3;
    step = span / 2.0f;
    s.df = scandirty::Defocus{s.map.data(), span, step};
  }
  scandirty::buildRowTable(s.params, H, s.anchors, step, s.rowT);
  return s;
}

std::vector<uint32_t> whole(const Setup &s, const std::vector<uint8_t> &bucket) {
  std::vector<uint32_t> f(static_cast<size_t>(W) * H, 0);
  scandirty::refill(s.params, s.rowT.data(), s.anchors, bucket.data(), nullptr,
                    s.df, W, H, f.data());
  return f;
}

// The kept field of `before`, refilled where `next` moved -- what the texture
// holds after a partial build.
std::vector<uint32_t> partial(const Setup &s, const std::vector<uint8_t> &before,
                              const std::vector<uint8_t> &next,
                              const std::vector<uint8_t> &prevClaimed,
                              scandirty::Rect *rect = nullptr) {
  std::vector<uint32_t> f = whole(s, before);
  const scandirty::Rect r =
      scandirty::refill(s.params, s.rowT.data(), s.anchors, next.data(),
                        prevClaimed.data(), s.df, W, H, f.data());
  if (rect) *rect = r;
  return f;
}

void run(int defocusPercent) {
  const Setup s = makeSetup(defocusPercent);

  // The table is content-free and deterministic: a kept one is the one a
  // whole rebuild would make.
  std::vector<float> again;
  scandirty::buildRowTable(s.params, H, s.anchors, s.df.step, again);
  CHECK(again == s.rowT);

  std::mt19937 rng(20261127u + static_cast<unsigned>(defocusPercent));
  std::uniform_int_distribution<int> level(0, 15);
  std::vector<uint8_t> base(static_cast<size_t>(W) * H);
  for (auto &v : base) v = static_cast<uint8_t>(level(rng) < 3 ? 12 : 1);

  // Nothing moved: nothing recomputed, nothing uploaded.
  {
    scandirty::Rect r;
    CHECK(partial(s, base, base, base, &r) == whole(s, base));
    CHECK(r.empty());
  }

  // One pixel: exactly that pixel, no neighbor -- a pixel reads only its own
  // bucket.
  {
    auto next = base;
    next[30 * W + 40] = static_cast<uint8_t>((next[30 * W + 40] + 7) % 16);
    scandirty::Rect r;
    CHECK(partial(s, base, next, base, &r) == whole(s, next));
    CHECK(r.x == 40 && r.y == 30 && r.w == 1 && r.h == 1);
    // THE COMPARISON CAN FAIL: claim the changed pixel did not change, and the
    // kept field is stale there.
    CHECK(partial(s, base, next, next) != whole(s, next));
  }

  // A menu step: two row bands change level (the old highlight, the new one),
  // and a trail's scattered pixels drift by one bucket.
  {
    auto next = base;
    for (int y = 10; y < 16; ++y)
      for (int x = 0; x < W; ++x) next[static_cast<size_t>(y) * W + x] = 3;
    for (int y = 16; y < 22; ++y)
      for (int x = 0; x < W; ++x) next[static_cast<size_t>(y) * W + x] = 9;
    std::uniform_int_distribution<int> any(0, W * H - 1);
    for (int i = 0; i < 40; ++i) {
      auto &v = next[static_cast<size_t>(any(rng))];
      v = static_cast<uint8_t>(v > 0 ? v - 1 : 1);
    }
    CHECK(partial(s, base, next, base) == whole(s, next));
  }

  // Every pixel changed.
  {
    std::vector<uint8_t> next(base.size());
    for (size_t i = 0; i < next.size(); ++i)
      next[i] = static_cast<uint8_t>((base[i] + 1) % 16);
    scandirty::Rect r;
    CHECK(partial(s, base, next, base, &r) == whole(s, next));
    CHECK(r.x == 0 && r.y == 0 && r.w == W && r.h == H);
  }

  // Chained random edits, as consecutive frames are: the kept field must stay
  // equal to a whole rebuild at every step.
  std::vector<uint32_t> kept = whole(s, base);
  std::uniform_int_distribution<int> cx(0, W - 1), cy(0, H - 1), sz(1, 14);
  for (int trial = 0; trial < 300; ++trial) {
    auto next = base;
    const int edits = 1 + trial % 5;
    for (int e = 0; e < edits; ++e) {
      const int x0 = cx(rng), y0 = cy(rng), ew = sz(rng), eh = sz(rng);
      for (int y = y0; y < y0 + eh && y < H; ++y)
        for (int x = x0; x < x0 + ew && x < W; ++x)
          next[static_cast<size_t>(y) * W + x] = static_cast<uint8_t>(level(rng));
    }
    scandirty::refill(s.params, s.rowT.data(), s.anchors, next.data(),
                      base.data(), s.df, W, H, kept.data());
    CHECK(kept == whole(s, next));
    base = next;
  }
}

}  // namespace

int main() {
  run(0);    // defocus off: the shipped table
  run(100);  // defocus on: three anchors, interpolated
  if (testcheck::g_failures != 0) {
    std::printf("scanlines_dirty_test: %d check(s) FAILED\n", testcheck::g_failures);
    return 1;
  }
  std::printf("scanlines_dirty_test: all checks passed (600 chained edits)\n");
  return 0;
}
