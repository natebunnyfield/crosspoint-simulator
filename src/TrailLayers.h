#pragma once
// THE PHOSPHOR TRAIL'S TWO LAYERS, AND THE COLOR EACH IS DRAWN -- the decision
// half. Pure, so tests/trail_layers_test.cpp can drive it; HalDisplay.cpp owns
// the textures.
//
// R-38 (owner report 2026-11-27, ruled "Fix it"): a cascade phosphor's trail
// changes color as it dies, from the ink toward the tail tint, along a ramp
// t(age) = age / rampMs. The trail was ONE accumulator recolored by ONE
// multiply timed by the age of the NEWEST deposit, so every deposit reset the
// color of every older ghost to the ink: on the shipped mix (cfd4cc ink, 613b27
// tail, 400 ms onset) about threefold brighter at every key press.
//
// THE MODEL NOW. Light deposited `a` ms ago is drawn, per channel, at
//   intensity(a) * m(t(a)),   m(t) = (1 - t) * ink + t * tail.
// A layer holding light of several ages cannot draw each at its own t. So a
// layer is drawn at the per-channel MINIMUM of m over the span of t its light
// covers (m is linear in t, so that is the smaller of its two ends). Nothing is
// ever drawn brighter than its own ramp says, in any channel, whether that
// channel falls toward the tail (the shipped mix, all three) or rises toward
// it (P7's green, P14's red, P17's red and green, and an independent review
// found both of the first version's shortcuts brightened those).
//
//   * SETTLED (accumTexture) is the trail exactly as it always was: EVERY
//     deposit goes into it, so its intensity is the single accumulator's, cap
//     and all, on both blend paths. Its span runs from the first deposit since
//     the trail was last dead to the newest.
//   * YOUNG (youngTexture) holds only recent light, so that light gets a span
//     of its own. It exists only with a tail, and only once a deposit lands
//     while older light is still visible -- an isolated fade never makes one,
//     and is drawn exactly as before at exactly the old cost.
//
// Composited, a pixel shows MAX(settled, young) on Metal and settled plus the
// young layer's EXCESS over settled's color on the ADD fallback (SDL's software
// renderer), because there the layers would otherwise add the same light twice.
// Either way no pixel is brighter than the single accumulator drew it, no
// deposit is brighter than the frame it came from (its own t is 0, so every
// span holding it ends at the ink), and no event -- a deposit, the young layer
// starting over or being dropped -- raises any channel of any light already on
// the glass: each only lowers a span's lower end or removes a layer whose
// light settled draws the same.
//
// What this costs in accuracy: light sharing a span with younger light is drawn
// toward the YOUNGER end in a channel that rises along the ramp, and toward the
// OLDER end in one that falls. Always darker than exact, never brighter.
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

// The color multiply for light at ramp position t: the live ink, LERPed
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

// The color multiply for a layer whose light was deposited between oldestMs
// and newestMs: per channel the smaller end of the ramp over that span, so no
// light in it is drawn brighter than its own ramp. A one-deposit span is exact.
inline void spanMod(const uint8_t ink[3], uint32_t tail, const Ramp &r,
                    uint64_t nowMs, uint64_t oldestMs, uint64_t newestMs,
                    uint8_t out[3]) {
  uint8_t older[3], newer[3];
  tintMod(ink, tail, rampT(static_cast<float>(nowMs - oldestMs), r), older);
  tintMod(ink, tail, rampT(static_cast<float>(nowMs - newestMs), r), newer);
  for (int c = 0; c < 3; c++)
    out[c] = older[c] < newer[c] ? older[c] : newer[c];
}

// What the young layer is composited with. On MAXIMUM, its own multiply: the
// brighter of the two layers wins per channel. On the ADD fallback the young
// layer's light is ALSO in settled, so only its excess over settled's multiply
// is added -- settled * mS + young * (mY - mS) is young * mY where only young
// light is, and never more than settled * max(mS, mY) anywhere.
inline void youngCompositeMod(const uint8_t modYoung[3],
                              const uint8_t modSettled[3], bool maxBlend,
                              uint8_t out[3]) {
  for (int c = 0; c < 3; c++)
    out[c] = maxBlend ? modYoung[c]
             : modYoung[c] > modSettled[c]
                 ? static_cast<uint8_t>(modYoung[c] - modSettled[c])
                 : 0;
}

struct State {
  bool settledLive = false;     // the trail is live: settled holds light
  uint64_t settledOldestMs = 0; // first deposit since the trail was last dead
  uint64_t settledNewestMs = 0; // newest deposit
  bool youngLive = false;       // the young layer holds light
  uint64_t youngOldestMs = 0;   // the young layer's span
  uint64_t youngNewestMs = 0;
};

enum class Deposit : uint8_t {
  SettledOnly, // no tail, or nothing older is visible: settled alone is exact
  NewYoung,    // the young layer starts over with this deposit alone
  IntoYoung,   // this deposit joins the young layer's span
};

// The young layer has nothing left to add: its span has reached settled's
// older end, so settled draws its light the same (or the tail went away).
inline bool dropYoungDue(const State &s, uint64_t nowMs, const Ramp &r) {
  if (!s.youngLive)
    return false;
  if (!r.hasTail)
    return true;
  return rampT(static_cast<float>(nowMs - s.youngOldestMs), r) >=
         rampT(static_cast<float>(nowMs - s.settledOldestMs), r);
}

inline Deposit planDeposit(const State &s, uint64_t nowMs, const Ramp &r) {
  if (!r.hasTail || !s.settledLive)
    return Deposit::SettledOnly;
  if (!s.youngLive)
    return Deposit::NewYoung;
  // Joining moves the young layer's light already there toward the new end of
  // its span; starting over leaves that light to settled's wider span. Take
  // whichever moves it less along the ramp. Both only ever darken.
  const float tYoung = rampT(static_cast<float>(nowMs - s.youngOldestMs), r);
  const float tSettled =
      rampT(static_cast<float>(nowMs - s.settledOldestMs), r);
  return tYoung < tSettled - tYoung ? Deposit::IntoYoung : Deposit::NewYoung;
}

inline void applyDeposit(State &s, Deposit d, uint64_t nowMs) {
  if (!s.settledLive) {
    s.settledLive = true;
    s.settledOldestMs = nowMs;
  }
  s.settledNewestMs = nowMs;
  switch (d) {
  case Deposit::SettledOnly:
    break;
  case Deposit::NewYoung:
    s.youngLive = true;
    s.youngOldestMs = nowMs;
    s.youngNewestMs = nowMs;
    break;
  case Deposit::IntoYoung:
    s.youngNewestMs = nowMs;
    break;
  }
}

inline void applyDropYoung(State &s) { s.youngLive = false; }

// The trail has died (nothing it holds can move a pixel): the next deposit
// starts both spans afresh.
inline void applyTrailDead(State &s) { s = State{}; }

} // namespace traillayers
