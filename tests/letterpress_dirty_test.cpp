// Pins src/LetterpressDirty.h: rebuilding the letterpress field only inside
// changedRect() must give EXACTLY the field a whole rebuild gives, for any edit.
// The shipping build (src/SurfaceSheet.cpp) starts from the texture holding the
// previous page's field and overwrites that box; this does the same in memory
// and compares every pixel against a whole rebuild of the new page.
// crosspoint-reader docs/menu-nav-lag-2026-11-27.md has the measurement.
#include <cstdio>
#include <cstdint>
#include <random>
#include <vector>

#include "../src/LetterpressDirty.h"
#include "TestCheck.h"

namespace {

constexpr int W = 97;  // odd sizes, so no edit lines up with anything
constexpr int H = 61;

std::vector<uint32_t> whole(const letterpress::Params &p,
                            const std::vector<uint8_t> &ink) {
  std::vector<uint32_t> f(static_cast<size_t>(W) * H);
  letterdirty::fillField(p, ink.data(), W, H, letterdirty::Rect{0, 0, W, H},
                         f.data(), W);
  return f;
}

// The old field, with `r` rebuilt from the new inkness, as the texture holds
// it after a partial upload.
std::vector<uint32_t> patched(const letterpress::Params &p,
                              const std::vector<uint8_t> &oldInk,
                              const std::vector<uint8_t> &newInk,
                              const letterdirty::Rect &r) {
  std::vector<uint32_t> f = whole(p, oldInk);
  if (r.empty()) return f;
  std::vector<uint32_t> part(static_cast<size_t>(r.w) * r.h);
  letterdirty::fillField(p, newInk.data(), W, H, r, part.data(), r.w);
  for (int y = 0; y < r.h; ++y)
    for (int x = 0; x < r.w; ++x)
      f[static_cast<size_t>(r.y + y) * W + r.x + x] =
          part[static_cast<size_t>(y) * r.w + x];
  return f;
}

bool samePartialAsWhole(const letterpress::Params &p,
                        const std::vector<uint8_t> &oldInk,
                        const std::vector<uint8_t> &newInk) {
  const letterdirty::Rect r =
      letterdirty::changedRect(oldInk.data(), newInk.data(), W, H);
  return patched(p, oldInk, newInk, r) == whole(p, newInk);
}

}  // namespace

int main() {
  letterpress::Params p;
  p.strengthPercent = 68;  // the phone's shipped Impression
  p.seed = 0x5EEDu;
  p.paperDarkenBudget = 0.305f;
  p.includeTooth = false;  // as the panel field builds it
  p.ringScale = 0.93f;
  p.debossScale = 0.99f;
  p.pressScale = 1.25f;

  std::mt19937 rng(20261127u);
  std::uniform_int_distribution<int> byte(0, 255);
  std::vector<uint8_t> base(static_cast<size_t>(W) * H);
  // Mostly paper with strokes of ink, like a page: the edge terms (ring,
  // deboss) only fire where the inkness steps.
  for (auto &v : base) v = (byte(rng) < 40) ? 255 : 0;

  // Nothing changed (a repaint of the same frame): an empty box.
  CHECK(letterdirty::changedRect(base.data(), base.data(), W, H).empty());

  // One interior pixel: a 3x3 box around it.
  {
    auto next = base;
    next[30 * W + 40] ^= 0xFF;
    const auto r = letterdirty::changedRect(base.data(), next.data(), W, H);
    CHECK(r.x == 39 && r.y == 29 && r.w == 3 && r.h == 3);
    CHECK(samePartialAsWhole(p, base, next));
    // THE GROWTH IS LOAD-BEARING: the pixel's neighbors see it through the
    // Sobel window, so a box of the changed pixel alone leaves them stale.
    CHECK(patched(p, base, next, letterdirty::Rect{40, 30, 1, 1}) !=
          whole(p, next));
  }

  // The four corners: the growth clamps to the field.
  for (const int idx : {0, W - 1, (H - 1) * W, H * W - 1}) {
    auto next = base;
    next[static_cast<size_t>(idx)] ^= 0xFF;
    const auto r = letterdirty::changedRect(base.data(), next.data(), W, H);
    CHECK(r.x >= 0 && r.y >= 0 && r.x + r.w <= W && r.y + r.h <= H);
    CHECK(r.w == 2 && r.h == 2);
    CHECK(samePartialAsWhole(p, base, next));
  }

  // A menu step: one band (the old selection) cleared, another filled.
  {
    auto next = base;
    for (int y = 0; y < H; ++y)
      for (int x = 20; x < 32; ++x) next[static_cast<size_t>(y) * W + x] = 0;
    for (int y = 0; y < H; ++y)
      for (int x = 32; x < 44; ++x) next[static_cast<size_t>(y) * W + x] = 128;
    CHECK(samePartialAsWhole(p, base, next));
  }

  // Two edits far apart: one box spanning both.
  {
    auto next = base;
    next[3 * W + 5] ^= 0xFF;
    next[57 * W + 90] ^= 0xFF;
    const auto r = letterdirty::changedRect(base.data(), next.data(), W, H);
    CHECK(r.x == 4 && r.y == 2 && r.w == 88 && r.h == 57);
    CHECK(samePartialAsWhole(p, base, next));
  }

  // Random edits of every size, partial must equal whole every time.
  int sweeps = 0;
  for (int trial = 0; trial < 300; ++trial) {
    auto next = base;
    std::uniform_int_distribution<int> cx(0, W - 1), cy(0, H - 1), sz(1, 12);
    const int edits = 1 + trial % 4;
    for (int e = 0; e < edits; ++e) {
      const int x0 = cx(rng), y0 = cy(rng), ew = sz(rng), eh = sz(rng);
      for (int y = y0; y < y0 + eh && y < H; ++y)
        for (int x = x0; x < x0 + ew && x < W; ++x)
          next[static_cast<size_t>(y) * W + x] = static_cast<uint8_t>(byte(rng));
    }
    CHECK(samePartialAsWhole(p, base, next));
    ++sweeps;
    base = next;  // chained, as consecutive frames are
  }

  std::printf("letterpress_dirty_test: %d random edits, %d failures\n", sweeps,
              testcheck::g_failures);
  return testcheck::g_failures == 0 ? 0 : 1;
}
