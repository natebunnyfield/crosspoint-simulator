// THE ZEN READING GOAL -- src/ReadingAllowance.h.
//
// Every failure here is silent: a clock that counts a menu or counts outside
// zen, a decay that starts a minute early, a zen start that does not restart.
// Each case below names the wrong implementation it exists to catch.

#include "ReadingAllowance.h"

#include <cmath>
#include <cstdio>
#include <vector>

using namespace readingallowance;

static int failures = 0;
static void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    failures++;
  }
}
static bool near(double a, double b) { return std::fabs(a - b) < 1e-9; }

int main() {
  // THE LAST MINUTE. Ten minutes: clean through 9:00, half gone at 9:30, spent
  // at 10:00 and after. Catches a decay spread over the whole allowance.
  check(near(decayFraction(0, 10), 0), "10 min: 0 s is clean");
  check(near(decayFraction(540, 10), 0), "10 min: 9:00 is still clean");
  check(decayFraction(540.5, 10) > 0, "10 min: decay begins just after 9:00");
  check(near(decayFraction(570, 10), 0.5), "10 min: 9:30 is half");
  check(near(decayFraction(600, 10), 1), "10 min: 10:00 is spent");
  check(near(decayFraction(5000, 10), 1), "10 min: spent stays spent");
  // Off never decays, however long the book is read.
  check(near(decayFraction(1e7, 0), 0), "off: never decays");
  check(near(decayFraction(1e7, -3), 0), "negative: treated as off");
  // Monotone across the window, sampled every tenth of a second.
  double prev = -1;
  bool mono = true;
  for (int t = 0; t <= 7200; t++) {
    const double f = decayFraction(t / 10.0 + 500, 10);
    if (f < prev) mono = false;
    prev = f;
  }
  check(mono, "decay is monotone");
  // An allowance shorter than a minute cannot start its decay before zero.
  check(near(decayFraction(0, 1), 0), "1 min: clean at 0");
  check(near(decayFraction(30, 1), 0.5), "1 min: decays over the whole minute");

  // THE SESSION: zen starting restarts it, reading accumulates, a stall is
  // capped. Owner 2026-09-24: "no matter the book ... zen mode starting up
  // again restarts it".
  {
    Session z;
    check(z.step(true, true, 0.5), "the first pass in zen is a start (a launch into zen)");
    z.step(true, true, 0.5);
    check(near(z.seconds, 1.0), "reading in zen accumulates");
    z.step(true, false, 0.5);
    check(near(z.seconds, 1.0), "a menu in zen adds nothing");
    z.step(true, true, 3600.0);
    check(near(z.seconds, 1.0 + kMaxStepSeconds), "a stall is capped at one step");
    z.step(true, true, -5.0);
    z.step(true, true, std::nan(""));
    check(near(z.seconds, 1.0 + kMaxStepSeconds), "negative and NaN steps add nothing");
    // Leaving zen does not reset; the time just stops being counted by the
    // caller (counts() is false outside zen). Coming BACK is what restarts.
    check(!z.step(false, false, 0.5), "leaving zen is not a restart");
    check(near(z.seconds, 1.0 + kMaxStepSeconds), "leaving zen keeps the clock");
    check(z.step(true, true, 0.25), "re-entering zen is a restart");
    check(near(z.seconds, 0.25), "re-entering zen starts from zero");
    check(!z.step(true, true, 0.25), "staying in zen is not a restart");
  }
  // THE BOOK DOES NOT MATTER: there is no key to switch on. A spent session
  // stays spent across a book change, which is the point of the ruling.
  {
    Session z;
    z.step(true, true, 0.0);
    for (int i = 0; i < 300; i++) z.step(true, true, 1.0);
    check(near(decayFraction(z.seconds, 5), 1.0), "five minutes in zen spends the goal");
    check(near(decayFraction(240.0, 5), 0.0), "4:00 of 5 is still clean");
    check(near(decayFraction(270.0, 5), 0.5), "4:30 of 5 is half");
  }
  check(kDefaultMinutes == 5, "the goal ships at five minutes");

  // IS THIS READING? Only zen, a book page, awake, in front.
  check(counts(true, true, false, false, false), "zen, a book page, in front counts");
  check(!counts(false, true, false, false, false), "a book page OUTSIDE zen does not count");
  check(!counts(true, false, false, false, false), "a menu does not count");
  check(!counts(true, true, true, false, false), "asleep does not count");
  check(!counts(true, true, false, true, false), "the sleep screen does not count");
  check(!counts(true, true, false, false, true), "inactive does not count");

  // QUANTIZE: 0 exactly when clean, 120 exactly when spent, so the renderer's
  // "t > 0" test and "fully gone" test are both exact.
  check(quantize(0) == 0 && quantize(-1) == 0, "clean quantizes to 0");
  check(quantize(1) == 120 && quantize(2) == 120, "spent quantizes to 120");
  check(quantize(0.001) >= 0 && quantize(0.5) == 60, "midpoint is 60");

  // THE LIGHT PICTURE (v2, the viscous starved press): exactly clean at
  // t = 0, gone at t = 1, only ever losing ink, a stroke's EDGE holding longer
  // than its middle (edge pressure at the type's shoulder), and every
  // incidental term (a robbed roller, the roller's thin band, a skipped patch)
  // starving a pixel EARLIER, never later.
  {
    using namespace readingallowance::picture;
    bool clean0 = true, gone1 = true, mono = true, edgeHolds = true, incidental = true;
    for (int y = 0; y < 60; y++)
      for (int x = 0; x < 60; x++) {
        PressSample p{};
        p.tooth = phosphorgrain::unitFromHash(phosphorgrain::hash3(x, y, 1u));
        p.form = phosphorgrain::valueNoise(x / 20.0f, y / 20.0f, 2u);
        p.plate = phosphorgrain::valueNoise(x / 15.0f, y / 15.0f, 3u);
        p.blob = blobAt(x, y, 1, 4u);
        if (p.blob < 0.0f || p.blob > 1.0f) clean0 = false;
        for (float in : {0.5f, 1.0f}) {
          p.interior = in;
          if (printedFraction(p, 0.0f) != 1.0f) clean0 = false;
          if (printedFraction(p, 1.0f) != 0.0f) gone1 = false;
          float prev = 2.0f;
          for (int k = 0; k <= 120; k++) {
            const float r = printedFraction(p, k / 120.0f);
            if (r > prev + 1e-6f) mono = false;
            prev = r;
          }
        }
        for (int k = 1; k < 120; k++) {
          PressSample e = p, c = p; e.interior = 0.5f; c.interior = 1.0f;
          if (printedFraction(e, k / 120.0f) + 1e-6f < printedFraction(c, k / 120.0f)) edgeHolds = false;
          PressSample r = c; r.depletion = 1.0f; r.band = 1.0f; r.skip = 1.0f;
          if (printedFraction(r, k / 120.0f) > printedFraction(c, k / 120.0f) + 1e-6f) incidental = false;
        }
      }
    check(clean0, "viscous press: t = 0 prints everything (blob in [0,1])");
    check(gone1, "viscous press: t = 1 prints nothing");
    check(mono, "viscous press: ink only ever leaves");
    check(edgeHolds, "viscous press: a stroke's edge holds longer than its middle");
    check(incidental, "viscous press: a robbed roller, its band and a skip starve earlier");
    check(pressLeft(0.0f) == 1.0f && pressLeft(1.0f) == 0.0f && pressLeft(0.5f) > 0.8f,
          "viscous press: the impression holds until late, then goes");
    check(blobAt(10, 10, 1, 1u) == blobAt(10, 10, 1, 1u) && blobAt(10, 10, 1, 1u) != blobAt(10, 10, 1, 2u),
          "viscous press: the split field belongs to the page's sheet");
    // inkness reads a pixel against the page's own palette.
    const panelpalette::Palette pal{{0x5C, 0x33, 0x2B}, {0xF9, 0xF3, 0xE9}};
    check(inkness(0xFF5C332Bu, pal) == 1.0f, "inkness: the ink is full ink");
    check(inkness(0xFFF9F3E9u, pal) == 0.0f, "inkness: the paper is none");
    // The glow counts only light ABOVE the ground: a flat ground page glows
    // nothing, so the dark ground itself never blooms.
    std::vector<uint32_t> flat(64 * 64, 0xFF171B1Bu), out;
    int ow = 0, oh = 0;
    const uint8_t ground[3] = {0x17, 0x1B, 0x1B};
    excessGlow(flat.data(), 64, 64, 4, 2, 2, ground, out, ow, oh);
    bool dark = ow == 16 && oh == 16;
    for (uint32_t px : out) dark = dark && (px & 0xFFFFFFu) == 0;
    check(dark, "glow: a bare ground emits no excess");
  }

  if (failures == 0) std::printf("reading_allowance: all passed\n");
  return failures == 0 ? 0 : 1;
}
