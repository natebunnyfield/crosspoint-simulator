// Unit tests for trail -- when a phosphor trail stops being able to change a
// pixel, and therefore when the present loop that drives it may stop.
//
// WHY: both failure modes are silent and neither is visible on the platform
// that would be used to check. Stop one present too early and a visible ghost
// pops off the glass -- which no compiler, no test of the renderer and no
// single screenshot can see. Stop too late and the loop burns a core redrawing
// one picture, which looks exactly like working software. And the SAFE side of
// that judgement is renderer-dependent: SDL's software blitter truncates its
// blends, so the desktop canary measures the trail dying EARLIER than a
// rounding GPU backend does. A model tuned on the desktop ships a ghost to the
// phone.
//
//   c++ -std=c++17 -Isrc tests/trail_lifetime_test.cpp -o /tmp/tl && /tmp/tl

#include "TrailLifetime.h"

#include <cmath>
#include <cstdio>
#include "TestCheck.h"

static int &failures = testcheck::g_failures;

// The shipped dark pair: E0E0DE ink on 121212 paper.
static const uint8_t kInk[3] = {0xE0, 0xE0, 0xDE};
static const uint8_t kPaper[3] = {0x12, 0x12, 0x12};

// A reference simulation of what the renderer actually stores, so the bound can
// be checked against the thing it bounds rather than against itself. Two
// arithmetics, because the two backends disagree and the bound has to cover
// both: SDL's software blitter truncates, a GPU rasteriser rounds to nearest.
static int stepTrunc(int v, int drop) { return (v * (255 - drop)) / 255; }
static int stepRound(int v, int drop) {
  return static_cast<int>(std::floor(static_cast<double>(v) * (255 - drop) /
                                         255.0 +
                                     0.5));
}

int main() {
  using namespace trail;

  // --- invisibleAtOrBelow ---------------------------------------------------

  // The shipped pair. The trail is drawn with the ink as its colour mod over a
  // page whose darkest tone is the paper, so it is invisible at
  // 255 * 18 / 224 = 20.49.
  {
    const float a = invisibleAtOrBelow(kInk, kPaper);
    CHECKM(std::fabs(a - 255.0f * 18.0f / 224.0f) < 0.01f,
           "shipped dark pair: threshold %.2f, expected 20.49", a);
    // ...and that it is NOT the 2.4-trail figure the constant it replaces came
    // from. 2.4 trails is the decay to one code value, i.e. a threshold of 1.
    CHECKM(a > 1.0f, "the threshold collapsed onto the decay-to-black figure");
  }

  // A PURE BLACK PAPER constrains nothing: max(dst, src) can differ for any
  // positive src, so the trail must run to the backstop. The caller keeps the
  // 2.4-trail bound for exactly this case; the model's job is to say zero
  // rather than to invent a floor.
  {
    const uint8_t black[3] = {0, 0, 0};
    CHECKM(invisibleAtOrBelow(kInk, black) == 0.0f,
           "a black paper claimed a nonzero invisibility threshold");
  }

  // A channel the mod ZEROES can never light, so it must not constrain. A pure
  // green phosphor over a black-in-red page is the case: red mod 0 would divide
  // by zero, or worse, pin the threshold at 0 and run every trail to the
  // backstop.
  {
    const uint8_t greenOnly[3] = {0, 0xE0, 0};
    const uint8_t paper[3] = {0, 0x12, 0x12};
    const float a = invisibleAtOrBelow(greenOnly, paper);
    CHECKM(std::fabs(a - 255.0f * 18.0f / 224.0f) < 0.01f,
           "a zeroed channel constrained the threshold (%.2f)", a);
  }

  // THE TIGHTEST CHANNEL WINS. Anything else is a channel still visibly
  // glowing after the trail has been declared over.
  {
    const uint8_t mod[3] = {0xFF, 0x40, 0x40};
    const uint8_t floorC[3] = {0x10, 0x40, 0x40};
    const float a = invisibleAtOrBelow(mod, floorC);
    const float red = 255.0f * 16.0f / 255.0f;
    CHECKM(std::fabs(a - red) < 0.01f, "the tightest channel did not win");
  }

  // A destination brighter than anything the mod can draw is invisible from the
  // first frame -- the threshold saturates at full scale rather than exceeding
  // it, because the accumulator itself cannot exceed 255.
  {
    const uint8_t dim[3] = {0x10, 0x10, 0x10};
    const uint8_t bright[3] = {0xF0, 0xF0, 0xF0};
    CHECKM(invisibleAtOrBelow(dim, bright) == 255.0f,
           "the threshold ran past full scale");
  }

  // --- fadePeakBound --------------------------------------------------------

  // It is an UPPER BOUND, and that is the whole contract. Run the two real
  // arithmetics against it for a long trail and check it never drops below
  // either. The rounding arm is the one that matters: it is the arm the desktop
  // cannot exercise.
  for (int drop = 1; drop <= 64; drop++) {
    float bound = 255.0f;
    int trunc = 255, round = 255;
    for (int n = 0; n < 400; n++) {
      bound = fadePeakBound(bound, drop);
      trunc = stepTrunc(trunc, drop);
      round = stepRound(round, drop);
      CHECKM(bound >= static_cast<float>(trunc) - 1e-3f,
             "drop %d step %d: bound %.2f below the truncating value %d", drop,
             n, bound, trunc);
      CHECKM(bound >= static_cast<float>(round) - 1e-3f,
             "drop %d step %d: bound %.2f below the rounding value %d", drop, n,
             bound, round);
    }
  }

  // A ROUNDING BACKEND HAS A FIXED POINT and the bound has to sit above it. At
  // drop 8 the stored value stops falling at 16 (16*247/255 = 15.5, which
  // rounds back to 16); a model that decays to zero would call that trail dead
  // while a real ghost sat in the buffer.
  {
    int round = 255;
    for (int n = 0; n < 2000; n++) round = stepRound(round, 8);
    CHECKM(round > 0, "the rounding reference decayed to zero: retune the test");
    float bound = 255.0f;
    for (int n = 0; n < 2000; n++) bound = fadePeakBound(bound, 8);
    CHECKM(bound >= static_cast<float>(round),
           "the bound (%.2f) sank under the rounding fixed point (%d)", bound,
           round);
  }

  // NON-INCREASING, always. For a small drop the decay is smaller than the
  // half-code rounding term, and the naive expression would grow -- a trail
  // that never ends, on exactly the slow-cadence runs where the loop is
  // cheapest to leave running and hardest to notice.
  for (int drop = 1; drop <= 254; drop++)
    for (float start : {255.0f, 128.0f, 32.0f, 8.0f, 1.0f, 0.0f}) {
      const float next = fadePeakBound(start, drop);
      CHECKM(next <= start, "drop %d grew the bound from %.2f to %.2f", drop,
             start, next);
      CHECKM(next >= 0.0f, "drop %d drove the bound negative", drop);
    }

  // drop 0 is "no time passed": it must be exactly a no-op, or a fast present
  // cadence would decay the bound faster than the texture it tracks.
  CHECKM(fadePeakBound(200.0f, 0) == 200.0f, "drop 0 moved the bound");
  CHECKM(fadePeakBound(200.0f, -3) == 200.0f, "a negative drop moved the bound");
  // A full drop clears the buffer outright.
  CHECKM(fadePeakBound(255.0f, 255) == 0.0f, "drop 255 left light behind");

  // --- the two together: the trail is SHORTER than the backstop, and not by so
  // little that the change was not worth making, nor so much that it undercuts
  // the measured death of a real trail.
  //
  // The measured run: trail 1095 ms, presents about 16 ms apart, so drop 8 per
  // present; the last frame that DIFFERED landed 846 ms after the deposit and
  // the backstop ran to 2628 ms.
  {
    const float threshold = invisibleAtOrBelow(kInk, kPaper);
    float bound = 255.0f;
    int steps = 0;
    while (bound > threshold && steps < 10000) {
      bound = fadePeakBound(bound, 8);
      steps++;
    }
    const double ms = steps * 16.0;
    CHECKM(steps < 10000, "the bound never reached the threshold");
    CHECKM(ms > 846.0,
           "the bound (%.0f ms) cuts inside the measured last visible change "
           "at 846 ms",
           ms);
    CHECKM(ms < 2628.0 * 0.85,
           "the bound (%.0f ms) saves less than 15%% of the 2628 ms backstop",
           ms);
  }

  if (failures == 0) std::printf("trail_lifetime_test: all checks passed\n");
  return failures ? 1 : 0;
}
