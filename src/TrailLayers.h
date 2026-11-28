#pragma once
// WHICH LAYER OF THE TRAIL A DEPOSIT GOES INTO, AND WHAT COLOR EACH LAYER IS
// DRAWN -- the decision half of the phosphor trail's two accumulators. Pure, so
// tests/trail_layers_test.cpp can drive it; HalDisplay.cpp owns the textures.
//
// R-38 (owner report 2026-11-27, ruled "Fix it"): a cascade phosphor's trail
// changes color as it dies, from the ink toward the tail tint. The trail was
// ONE accumulator recolored by ONE multiply, timed by the age of the NEWEST
// deposit. A new deposit reset that age to zero, so every older ghost still in
// the buffer jumped from the dim tail tint back to the full ink color. On the
// shipped mix (cfd4cc ink, 613b27 tail, 400 ms onset) a ghost brightened about
// threefold at every key press while it should have been fading.
//
// THE FIX IS TWO LAYERS, each drawn at its own point on the ramp:
//   * YOUNG holds light still handing over from ink to tail, all of it on ONE
//     clock (youngAtMs). It is drawn at rampT(its age).
//   * SETTLED holds light whose handover is complete. It is drawn at the tail
//     (t = 1), which is exact for everything in it, whatever its age.
// Young light moves into settled the moment its ramp ends, where both layers
// draw the same color, so the move is invisible.
//
// THE ONE APPROXIMATION is a deposit that lands while the young layer is still
// mid-ramp: two clocks would need three layers (settled, the young light, the
// new light). With two, one of them is misplaced on the ramp, and the choice is
// made so that NOTHING ALREADY ON THE GLASS EVER MOVES BACKWARD:
//   * IntoYoung: the new light joins the young layer and starts at its t. The
//     ghosts already there do not change at all; the new ghost starts that far
//     along the ramp, never further back.
//   * SettleThenNewYoung: the young light moves to settled early (its t jumps
//     FORWARD to 1, toward the tail) and the new light starts a fresh young
//     layer at t = 0, exactly.
// Whichever misplaces light by less on the ramp is taken, so the error is at
// most half the ramp, and only in that window. A deposit landing after the
// young layer's ramp has ended (400 ms on the shipped mix), and every isolated
// fade, is exact. Neither choice ever raises a ghost's level or moves its tint
// back toward the ink, which is the owner's report.
//
// WITHOUT A TAIL there is one color for the whole trail, so the young layer is
// never used: every deposit goes into settled, and the trail is exactly the
// single accumulator it always was.
#include <cstdint>

namespace traillayers {

// The packed tint meaning "this phosphor has no tail; the trail only dims".
// Same value as HalDisplay.cpp's kNoGlowTail.
constexpr uint32_t kNoTail = 0xFFFFFFFFu;

struct Ramp {
  bool hasTail;  // the phosphor recolors as it dies
  float onsetMs; // when the handover completes; 0 = unknown
  float trailMs; // the whole trail
};

// How long the ink-to-tail handover lasts: the published onset when there is
// one, otherwise the whole trail (the recolor ramp it always had).
inline float rampMs(const Ramp &r) {
  return r.onsetMs > 0.0f ? r.onsetMs : r.trailMs;
}

// Where light deposited `ageMs` ago sits on the ramp: 0 = ink, 1 = tail.
// The formula the single accumulator used, unchanged.
inline float rampT(float ageMs, const Ramp &r) {
  const float len = rampMs(r);
  float t = len > 0.0f ? ageMs / len : 1.0f;
  if (t < 0.0f)
    t = 0.0f;
  if (t > 1.0f)
    t = 1.0f;
  return t;
}

// The color multiply for a layer at ramp position t: the live ink, LERPed
// toward the tail. With no tail it is the ink whatever t is. Rounded as the
// draw always rounded it.
inline void tintMod(const uint8_t ink[3], uint32_t tail, float t,
                    uint8_t out[3]) {
  for (int c = 0; c < 3; c++) {
    if (tail == kNoTail) {
      out[c] = ink[c];
      continue;
    }
    const float target = static_cast<float>((tail >> (16 - 8 * c)) & 0xFFu);
    out[c] = static_cast<uint8_t>((1.0f - t) * static_cast<float>(ink[c]) +
                                  t * target + 0.5f);
  }
}

struct State {
  bool youngLive = false; // the young layer holds light
  uint64_t youngAtMs = 0; // the young layer's clock: its oldest light's deposit
  bool settledLive = false; // the settled layer may hold visible light
  uint64_t newestAtMs = 0;  // the newest deposit, either layer
};

enum class Deposit : uint8_t {
  IntoSettled, // no tail: one layer, as it always was
  NewYoung,    // the young layer was empty: a fresh one, exact
  IntoYoung,   // join the mid-ramp young layer (new light starts at its t)
  SettleThenNewYoung, // young -> settled first (its t jumps forward), then
                      // fresh
};

inline float youngT(const State &s, uint64_t nowMs, const Ramp &r) {
  return rampT(static_cast<float>(nowMs - s.youngAtMs), r);
}

// Settled light is past its handover, so it is drawn at the tail. With no tail
// tintMod ignores t.
inline float settledT(const State &, uint64_t, const Ramp &) { return 1.0f; }

// The young layer's light has finished handing over (or the tail went away,
// and both layers are one color): move it into settled now. Same color in both
// layers at that moment, so nothing on the glass changes.
inline bool settleDue(const State &s, uint64_t nowMs, const Ramp &r) {
  if (!s.youngLive)
    return false;
  if (!r.hasTail)
    return true;
  return youngT(s, nowMs, r) >= 1.0f;
}

inline Deposit planDeposit(const State &s, uint64_t nowMs, const Ramp &r) {
  if (!r.hasTail)
    return Deposit::IntoSettled;
  if (!s.youngLive)
    return Deposit::NewYoung;
  const float t = youngT(s, nowMs, r);
  if (t >= 1.0f)
    return Deposit::SettleThenNewYoung;
  // IntoYoung misplaces the NEW light by t (it starts that far along the ramp);
  // settling misplaces the YOUNG light by 1 - t (it jumps to the tail). Take
  // the smaller; both move light forward only.
  return t < 1.0f - t ? Deposit::IntoYoung : Deposit::SettleThenNewYoung;
}

inline void applySettle(State &s) {
  s.youngLive = false;
  s.settledLive = true;
}

inline void applyDeposit(State &s, Deposit d, uint64_t nowMs) {
  switch (d) {
  case Deposit::IntoSettled:
    s.settledLive = true;
    break;
  case Deposit::SettleThenNewYoung:
    applySettle(s);
    s.youngLive = true;
    s.youngAtMs = nowMs;
    break;
  case Deposit::NewYoung:
    s.youngLive = true;
    s.youngAtMs = nowMs;
    break;
  case Deposit::IntoYoung:
    // The young clock stays: the light already there must not move back.
    break;
  }
  s.newestAtMs = nowMs;
}

} // namespace traillayers
