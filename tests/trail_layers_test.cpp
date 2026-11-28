// Pins traillayers (src/TrailLayers.h): which layer each deposit goes into and
// what color each layer is drawn. R-38, owner report 2026-11-27: every new
// deposit turned the older ghosts back from the tail tint to the ink color,
// because the one accumulator was recolored by the age of the NEWEST deposit.
//
// The model below is the trail's arithmetic per pixel -- fade, deposit, the
// young layer starting over or dropped, composite, on both blend paths -- with
// every decision taken from the real header. It runs over EVERY phosphor that
// has a tail (the preset table's afterglow rows, resolved the way the iOS shim
// resolves them, and the shipped frozen mix), because the tail can be brighter
// than the ink in a channel (P7 green, P14 red, P17 red and green) and the
// first version of this fix brightened exactly those.
//
// Properties, every present, every case, both paths:
//   1. A pixel lit only by the newest deposit is never brighter than its source
//      frame drew it (the ink, at the path's own strength).
//   2. A ghost is never drawn above its own ramp at its age, in any channel.
//   3. At a deposit, a ghost the deposit does not light never brightens.
//   4. Dropping the young layer changes no pixel.
//   5. Nothing is brighter than the single accumulator drew it -- which on the
//      ADD fallback is the cap: two layers must not add the same light twice.
//   6. An isolated fade is the single accumulator, value for value.
#include <cmath>
#include <cstdio>
#include <vector>

#include "../src/FrozenPage.h"
#include "../src/PanelPalette.h"
#include "../src/TrailLayers.h"
#include "TestCheck.h"

using namespace traillayers;

namespace {

struct Case {
  const char *name;
  uint8_t ink[3];
  uint32_t tail;
  Ramp ramp;
};

// Every phosphor whose trail has a tail, resolved as ios/CrossPointIOSShim.cpp
// pushes it: the preset's dark ink, its afterglow, its trail, onset 0 (a plain
// preset has none, so the ramp is the whole trail). Plus the shipped mix.
std::vector<Case> tailedCases() {
  std::vector<Case> out;
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
    const panelpalette::PresetInfo &info = panelpalette::kPresetInfo[i];
    if (!info.afterglow)
      continue;
    Case k{};
    k.name = info.phosphor;
    const panelpalette::Palette p =
        panelpalette::presetPalette(info.preset, true);
    for (int c = 0; c < 3; c++)
      k.ink[c] = p.ink[c];
    k.tail = (static_cast<uint32_t>(info.afterglow[0]) << 16) |
             (static_cast<uint32_t>(info.afterglow[1]) << 8) |
             info.afterglow[2];
    k.ramp = {true, 0.0f, panelpalette::trailMsForPreset(info.preset)};
    out.push_back(k);
  }
  const phosphormix::Result &m = frozenpage::darkMix();
  Case k{};
  k.name = "shipped mix";
  for (int c = 0; c < 3; c++)
    k.ink[c] = m.dark.ink[c];
  k.tail = (static_cast<uint32_t>(m.tail[0]) << 16) |
           (static_cast<uint32_t>(m.tail[1]) << 8) | m.tail[2];
  k.ramp = {m.hasTail, m.tailOnsetMs, m.trailMs};
  out.push_back(k);
  return out;
}

constexpr float kAddStrength = 96.0f / 255.0f; // the ADD fallback's alpha

// One pixel: which deposits light it (at full scale), and its light in each
// layer. `old` is the single accumulator, run alongside as the reference.
struct Pixel {
  std::vector<int> litBy;
  float settled = 0, young = 0, old = 0;
  bool lit(int j) const {
    for (int x : litBy)
      if (x == j)
        return true;
    return false;
  }
};

struct Sim {
  Case k;
  bool maxBlend;
  std::vector<uint64_t> at; // deposit times
  State s;
  std::vector<Pixel> px;
  uint64_t lastMs = 0;
  int next = 0;

  void add(float &layer) const {
    layer =
        maxBlend ? 255.0f : std::fmin(255.0f, layer + 255.0f * kAddStrength);
  }
  void composite(uint64_t now, const Pixel &p, float out[3]) const {
    uint8_t mS[3], mY[3], mYc[3];
    spanMod(k.ink, k.tail, k.ramp, now, s.settledOldestMs, s.settledNewestMs,
            mS);
    spanMod(k.ink, k.tail, k.ramp, now, s.youngOldestMs, s.youngNewestMs, mY);
    youngCompositeMod(mY, mS, maxBlend, mYc);
    for (int c = 0; c < 3; c++) {
      const float st = s.settledLive ? p.settled * mS[c] / 255.0f : 0.0f;
      const float y = s.youngLive ? p.young * mYc[c] / 255.0f : 0.0f;
      out[c] = maxBlend ? std::fmax(st, y) : (st + y) * kAddStrength;
    }
  }
  // Each light at its own age and its own point on the ramp: the exact model.
  void exact(uint64_t now, const Pixel &p, float out[3]) const {
    for (int c = 0; c < 3; c++)
      out[c] = 0.0f;
    for (int j = 0; j < next; j++) {
      if (!p.lit(j))
        continue;
      const float age = static_cast<float>(now - at[j]);
      const float keep = std::pow(10.0f, -age / k.ramp.trailMs);
      uint8_t m[3];
      tintMod(k.ink, k.tail, rampT(age, k.ramp), m);
      for (int c = 0; c < 3; c++) {
        const float v = 255.0f * keep * m[c] / 255.0f;
        out[c] = maxBlend ? std::fmax(out[c], v) : out[c] + v * kAddStrength;
      }
    }
  }
  // The single accumulator, recolored by the newest deposit's age.
  void single(uint64_t now, const Pixel &p, float out[3]) const {
    uint8_t m[3];
    tintMod(k.ink, k.tail,
            rampT(static_cast<float>(now - at[next - 1]), k.ramp), m);
    for (int c = 0; c < 3; c++)
      out[c] = p.old * m[c] / 255.0f * (maxBlend ? 1.0f : kAddStrength);
  }
};

int failuresHere = 0;
void fail(const Sim &sim, const char *what, uint64_t now, int c, float got,
          float bound) {
  if (failuresHere++ < 12)
    std::printf("  %s %s: %s at %llu ms, channel %d: %.3f > %.3f\n", sim.k.name,
                sim.maxBlend ? "MAX" : "ADD", what, (unsigned long long)now, c,
                got, bound);
}

// Runs one schedule. Pixel 0 is the ghost (lit by the first deposit only),
// pixel 1 static text (lit by every deposit), and pixel 2+j is lit by deposit j
// alone (what that frame took off the screen).
bool runCase(const Case &k, bool maxBlend, const std::vector<uint64_t> &at) {
  Sim sim{k, maxBlend, at, {}, {}, 0, 0};
  sim.px.resize(2 + at.size());
  sim.px[0].litBy = {0};
  for (int j = 0; j < static_cast<int>(at.size()); j++) {
    sim.px[1].litBy.push_back(j);
    sim.px[2 + j].litBy = {j};
  }
  const int before = failuresHere;
  const float eps = 0.02f;
  std::vector<float> prev(sim.px.size() * 3, 0.0f);
  for (uint64_t now = 16; now <= 6000; now += 16) {
    const float keep =
        std::pow(10.0f, -static_cast<float>(now - sim.lastMs) / k.ramp.trailMs);
    sim.lastMs = now;
    for (Pixel &p : sim.px) {
      p.settled *= keep;
      p.young *= keep;
      p.old *= keep;
    }
    // 4. dropping the young layer changes no pixel.
    if (dropYoungDue(sim.s, now, k.ramp)) {
      std::vector<float> kept;
      for (const Pixel &p : sim.px) {
        float o[3];
        sim.composite(now, p, o);
        kept.insert(kept.end(), o, o + 3);
      }
      applyDropYoung(sim.s);
      for (size_t i = 0; i < sim.px.size(); i++) {
        float o[3];
        sim.composite(now, sim.px[i], o);
        for (int c = 0; c < 3; c++)
          if (std::fabs(o[c] - kept[i * 3 + c]) > eps)
            fail(sim, "young drop changed a pixel", now, c, o[c],
                 kept[i * 3 + c]);
      }
    }
    const bool dep =
        sim.next < static_cast<int>(at.size()) && now >= at[sim.next];
    if (dep) {
      const int j = sim.next;
      sim.at[j] = now; // a deposit lands on the present, not the schedule
      const Deposit plan = planDeposit(sim.s, now, k.ramp);
      for (Pixel &p : sim.px) {
        if (plan == Deposit::NewYoung)
          p.young = 0.0f;
        if (!p.lit(j))
          continue;
        sim.add(p.settled);
        if (plan != Deposit::SettledOnly)
          sim.add(p.young);
        sim.add(p.old);
      }
      applyDeposit(sim.s, plan, now);
      sim.next++;
    }
    if (sim.next == 0)
      continue;
    for (size_t i = 0; i < sim.px.size(); i++) {
      const Pixel &p = sim.px[i];
      float got[3], ex[3], one[3];
      sim.composite(now, p, got);
      sim.exact(now, p, ex);
      sim.single(now, p, one);
      for (int c = 0; c < 3; c++) {
        // 2 (and 1, for a pixel whose only light is the newest deposit).
        if (got[c] > ex[c] + eps)
          fail(sim, "drawn above its own ramp", now, c, got[c], ex[c]);
        // 5.
        if (got[c] > one[c] + eps)
          fail(sim, "above the single accumulator", now, c, got[c], one[c]);
        // 3.
        if (dep && !p.lit(sim.next - 1) && got[c] > prev[i * 3 + c] + eps)
          fail(sim, "ghost brightened at a deposit", now, c, got[c],
               prev[i * 3 + c]);
        prev[i * 3 + c] = got[c];
      }
    }
  }
  return failuresHere == before;
}

} // namespace

int main() {
  const std::vector<Case> cases = tailedCases();
  // P7, P14, P17 and the shipped mix. If the table grows a tail, it joins.
  CHECK(cases.size() >= 4);

  const std::vector<std::vector<uint64_t>> schedules = {
      {16, 160, 320, 464, 1200},                   // presses 150 ms apart
      {16, 64, 112, 160, 208, 256, 304, 352, 400}, // one per 48 ms
      {16, 1600},                                  // past half a long ramp
      {16, 1400, 1500},                            // the reviewer's P7 sweep
      {16, 900, 950, 1000, 2400, 2420, 3000},      // bursts inside a trail
  };
  for (const Case &k : cases)
    for (const auto &sched : schedules)
      for (int path = 0; path < 2; path++)
        CHECK(runCase(k, path == 0, sched));

  // 6. AN ISOLATED FADE IS THE SINGLE ACCUMULATOR, value for value, on both
  // paths and every tailed case: one deposit never makes a young layer.
  for (const Case &k : cases) {
    State s;
    CHECK(planDeposit(s, 16, k.ramp) == Deposit::SettledOnly);
    applyDeposit(s, Deposit::SettledOnly, 16);
    bool exactEverywhere = true;
    for (uint64_t now = 16; now <= 6000; now += 16) {
      uint8_t got[3], want[3];
      spanMod(k.ink, k.tail, k.ramp, now, s.settledOldestMs, s.settledNewestMs,
              got);
      tintMod(k.ink, k.tail, rampT(static_cast<float>(now - 16), k.ramp), want);
      for (int c = 0; c < 3; c++)
        if (got[c] != want[c])
          exactEverywhere = false;
    }
    CHECK(exactEverywhere);
    CHECK(!s.youngLive);
  }

  // WITHOUT A TAIL the young layer is never used: one layer, as it always was.
  {
    const Ramp noTail = {false, 0.0f, 1095.4f};
    State s;
    bool allSettled = true;
    for (uint64_t at : {16u, 160u, 320u}) {
      const Deposit d = planDeposit(s, at, noTail);
      if (d != Deposit::SettledOnly)
        allSettled = false;
      applyDeposit(s, d, at);
    }
    CHECK(allSettled);
    // A tail that goes away drops a live young layer at once.
    State t;
    applyDeposit(t, Deposit::SettledOnly, 0);
    applyDeposit(t, Deposit::NewYoung, 100);
    CHECK(dropYoungDue(t, 116, noTail));
  }

  // A deposit over visible older light gets a span of its own (exact), and the
  // trail's death starts every span afresh.
  {
    const Ramp r = {true, 400.0f, 1095.4f};
    State s;
    applyDeposit(s, planDeposit(s, 0, r), 0);
    CHECK(planDeposit(s, 200, r) == Deposit::NewYoung);
    applyDeposit(s, Deposit::NewYoung, 200);
    CHECK(s.youngOldestMs == 200 && s.settledOldestMs == 0);
    applyTrailDead(s);
    CHECK(!s.settledLive && !s.youngLive);
    CHECK(planDeposit(s, 3000, r) == Deposit::SettledOnly);
  }

  if (testcheck::g_failures != 0) {
    std::printf("trail_layers_test: %d check(s) FAILED\n",
                testcheck::g_failures);
    return 1;
  }
  std::printf("trail_layers_test: all checks passed\n");
  return 0;
}
