// Pins traillayers (src/TrailLayers.h): which layer each deposit goes into and
// what color each layer is drawn. R-38, owner report 2026-11-27: every new
// deposit turned the older ghosts back from the tail tint to the ink color,
// because the one accumulator was recolored by the age of the NEWEST deposit.
//
// The model below is the trail's arithmetic per pixel (fade, deposit, settle,
// composite, on both blend paths), with every decision taken from the real
// header. The burst cases fail against the single-accumulator decision.
#include <cmath>
#include <cstdio>

#include "../src/TrailLayers.h"
#include "TestCheck.h"

using namespace traillayers;

namespace {

// The shipped dark mix (src/FrozenPage.h darkMix(), printed 2026-11-27).
constexpr uint8_t kInk[3] = {0xcf, 0xd4, 0xcc};
constexpr uint32_t kTail = 0x613b27;
constexpr Ramp kShipped = {true, 400.0f, 1095.4f};

// One pixel of each layer, and the layers' shared decision state.
struct Sim {
  Ramp ramp;
  uint32_t tail;
  bool maxBlend; // Metal; false = SDL software renderer's ADD fallback
  State s;
  float young = 0.0f, settled = 0.0f; // this pixel's light in each layer
  uint64_t lastMs = 0;

  void depositInto(float &layer, float d) const {
    if (maxBlend)
      layer = std::fmax(layer, d);
    else
      layer = std::fmin(255.0f, layer + d * 96.0f / 255.0f);
  }
  void mergeYoung() {
    if (maxBlend)
      settled = std::fmax(settled, young);
    else
      settled = std::fmin(255.0f, settled + young);
    young = 0.0f;
    applySettle(s);
  }
  // One present at `now`, depositing `d` at this pixel when `deposit` is set.
  void present(uint64_t now, bool deposit, float d) {
    const float keep =
        std::pow(10.0f, -static_cast<float>(now - lastMs) / ramp.trailMs);
    young *= keep;
    settled *= keep;
    lastMs = now;
    if (settleDue(s, now, ramp))
      mergeYoung();
    if (deposit) {
      const Deposit plan = planDeposit(s, now, ramp);
      switch (plan) {
      case Deposit::IntoSettled:
        depositInto(settled, d);
        break;
      case Deposit::NewYoung:
        young = 0.0f;
        depositInto(young, d);
        break;
      case Deposit::IntoYoung:
        depositInto(young, d);
        break;
      case Deposit::SettleThenNewYoung:
        mergeYoung();
        young = 0.0f;
        depositInto(young, d);
        break;
      }
      applyDeposit(s, plan, now);
    }
  }
  // What this pixel's trail puts on the glass, per channel.
  void composite(uint64_t now, float out[3]) const {
    uint8_t modY[3], modS[3];
    tintMod(kInk, tail, youngT(s, now, ramp), modY);
    tintMod(kInk, tail, settledT(s, now, ramp), modS);
    for (int c = 0; c < 3; c++) {
      const float y = s.youngLive ? young * modY[c] / 255.0f : 0.0f;
      const float st = s.settledLive ? settled * modS[c] / 255.0f : 0.0f;
      out[c] = maxBlend ? std::fmax(y, st) : (y + st) * 96.0f / 255.0f;
    }
  }
  // Where on the ramp this pixel's light is drawn: the layer holding it.
  float lightT(uint64_t now) const {
    if (s.youngLive && young > 0.0f && !(s.settledLive && settled >= young))
      return youngT(s, now, ramp);
    return settledT(s, now, ramp);
  }
};

// A burst: the ghost pixel is lit only by the first deposit (the cover that
// left the screen); every later deposit leaves it dark, as a frame that does
// not light it. Presents every 16 ms. Returns false at the first present where
// the ghost brightens in any channel or its light moves back up the ramp.
bool ghostNeverRises(bool maxBlend, const uint64_t *deposits, int n,
                     const Ramp &ramp) {
  Sim sim{ramp, kTail, maxBlend, {}, 0.0f, 0.0f, 0};
  float prev[3] = {0, 0, 0};
  float prevT = 0.0f;
  int next = 0;
  for (uint64_t now = 16; now <= 3000; now += 16) {
    const bool dep = next < n && now >= deposits[next];
    sim.present(now, dep, next == 0 ? 255.0f : 0.0f);
    if (dep)
      next++;
    float out[3];
    sim.composite(now, out);
    const float t = sim.lightT(now);
    if (next > 1 || (next == 1 && !dep)) {
      for (int c = 0; c < 3; c++) {
        if (out[c] > prev[c] + 1e-4f) {
          std::printf("  ghost rose at %llu ms, channel %d: %.3f -> %.3f\n",
                      (unsigned long long)now, c, prev[c], out[c]);
          return false;
        }
      }
      if (t < prevT - 1e-6f) {
        std::printf("  ghost moved back on the ramp at %llu ms: %.3f -> %.3f\n",
                    (unsigned long long)now, prevT, t);
        return false;
      }
    }
    for (int c = 0; c < 3; c++)
      prev[c] = out[c];
    prevT = t;
  }
  return true;
}

// The single accumulator the trail was, for one deposit: the reference look of
// an isolated fade, which the fix must not change.
void oldIsolated(bool maxBlend, uint64_t now, uint64_t at, float a,
                 const Ramp &ramp, uint32_t tail, float out[3]) {
  uint8_t mod[3];
  tintMod(kInk, tail, rampT(static_cast<float>(now - at), ramp), mod);
  for (int c = 0; c < 3; c++) {
    const float v = a * mod[c] / 255.0f;
    out[c] = maxBlend ? v : v * 96.0f / 255.0f;
  }
}

} // namespace

int main() {
  // THE R-38 BURST, on both blend paths: presses 150 ms apart, then a pause,
  // then one more. The cover ghost must only ever dim and move toward the tail.
  const uint64_t burst[] = {16, 160, 320, 464, 1200};
  CHECK(ghostNeverRises(true, burst, 5, kShipped));
  CHECK(ghostNeverRises(false, burst, 5, kShipped));
  // Tighter presses (one per 48 ms), and a whole-trail ramp (onset unknown).
  const uint64_t tight[] = {16, 64, 112, 160, 208, 256, 304, 352, 400};
  CHECK(ghostNeverRises(true, tight, 9, kShipped));
  CHECK(ghostNeverRises(false, tight, 9, kShipped));
  const Ramp wholeTrail = {true, 0.0f, 1095.4f};
  CHECK(ghostNeverRises(true, burst, 5, wholeTrail));
  CHECK(ghostNeverRises(false, burst, 5, wholeTrail));

  // AN ISOLATED FADE IS UNCHANGED: same level and same color multiply at every
  // present as the single accumulator, on both paths, across the handover to
  // the settled layer at 400 ms and to the end of the trail.
  for (int path = 0; path < 2; path++) {
    const bool maxBlend = path == 0;
    Sim sim{kShipped, kTail, maxBlend, {}, 0.0f, 0.0f, 0};
    float a = 0.0f; // the old accumulator
    uint64_t last = 0;
    bool same = true;
    for (uint64_t now = 16; now <= 2600; now += 16) {
      const bool dep = now == 16;
      sim.present(now, dep, 255.0f);
      a *= std::pow(10.0f, -static_cast<float>(now - last) / kShipped.trailMs);
      last = now;
      if (dep)
        a = maxBlend ? 255.0f : 96.0f;
      float got[3], want[3];
      sim.composite(now, got);
      oldIsolated(maxBlend, now, 16, a, kShipped, kTail, want);
      for (int c = 0; c < 3; c++)
        if (std::fabs(got[c] - want[c]) > 1e-3f)
          same = false;
    }
    CHECK(same);
  }

  // WITHOUT A TAIL the young layer is never used, so a burst is exactly the
  // single accumulator it always was.
  {
    const Ramp noTail = {false, 0.0f, 1095.4f};
    State s;
    bool allSettled = true;
    for (uint64_t at : burst) {
      if (planDeposit(s, at, noTail) != Deposit::IntoSettled)
        allSettled = false;
      applyDeposit(s, planDeposit(s, at, noTail), at);
    }
    CHECK(allSettled);
    CHECK(!s.youngLive);
  }

  // EXACT when deposits land after the young layer's ramp has ended: the
  // earlier light is already settled (drawn at the tail, where it belongs) and
  // the new light starts a fresh young layer at the ink.
  {
    State s;
    applyDeposit(s, planDeposit(s, 0, kShipped), 0);
    CHECK(s.youngLive);
    CHECK(settleDue(s, 400, kShipped));
    applySettle(s);
    CHECK(planDeposit(s, 500, kShipped) == Deposit::NewYoung);
    applyDeposit(s, Deposit::NewYoung, 500);
    CHECK(youngT(s, 500, kShipped) == 0.0f);
  }

  // THE APPROXIMATION IS BOUNDED: mid-ramp, whichever light is misplaced is
  // misplaced by at most half the ramp, and only forward.
  {
    State s;
    applyDeposit(s, Deposit::NewYoung, 0);
    // 100 ms in (t 0.25): the new light joins the young layer, starting at
    // 0.25.
    CHECK(planDeposit(s, 100, kShipped) == Deposit::IntoYoung);
    // 300 ms in (t 0.75): the young light settles early (0.75 -> 1) instead.
    CHECK(planDeposit(s, 300, kShipped) == Deposit::SettleThenNewYoung);
    // Joining never moves the young clock, so the light already there stays
    // put.
    applyDeposit(s, Deposit::IntoYoung, 100);
    CHECK(s.youngAtMs == 0);
  }

  // A tail that goes away (a palette change) folds the young layer into the
  // settled one at the next present: one color, one layer.
  {
    State s;
    applyDeposit(s, Deposit::NewYoung, 0);
    const Ramp noTail = {false, 0.0f, 1095.4f};
    CHECK(settleDue(s, 16, noTail));
  }

  if (testcheck::g_failures != 0) {
    std::printf("trail_layers_test: %d check(s) FAILED\n",
                testcheck::g_failures);
    return 1;
  }
  std::printf("trail_layers_test: all checks passed\n");
  return 0;
}
