// THE DAILY READING ALLOWANCE -- src/ReadingAllowance.h.
//
// Every failure here is silent: a clock that counts a menu, a decay that starts
// a minute early, a day that never turns, a ledger that loses a book on reload.
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

  // THE LEDGER: per book, per day, clamped steps.
  Ledger l;
  const int d1 = dayKey(2026, 9, 24), d2 = dayKey(2026, 9, 25);
  check(d1 == 20260924, "dayKey is YYYYMMDD");
  l.add(d1, 0xAAAAu, 0.5);
  l.add(d1, 0xAAAAu, 0.5);
  l.add(d1, 0xBBBBu, 0.25);
  check(near(l.used(d1, 0xAAAAu), 1.0), "book A accumulates");
  check(near(l.used(d1, 0xBBBBu), 0.25), "book B is its own clock");
  check(near(l.used(d1, 0xCCCCu), 0.0), "an unread book has used nothing");
  // A stall (the process suspended without the background edge) is capped.
  l.add(d1, 0xAAAAu, 3600.0);
  check(near(l.used(d1, 0xAAAAu), 1.0 + kMaxStepSeconds), "a stall is capped at one step");
  // A clock that went backwards, or NaN, adds nothing.
  l.add(d1, 0xAAAAu, -5.0);
  l.add(d1, 0xAAAAu, std::nan(""));
  check(near(l.used(d1, 0xAAAAu), 1.0 + kMaxStepSeconds), "negative and NaN steps add nothing");

  // Round trip: a relaunch must not hand a book its minutes back.
  const Ledger r = Ledger::parse(l.serialize());
  Ledger r2 = r;
  check(r.day == d1, "round trip keeps the day");
  check(near(r2.used(d1, 0xAAAAu), l.used(d1, 0xAAAAu)), "round trip keeps book A");
  check(near(r2.used(d1, 0xBBBBu), 0.25), "round trip keeps book B");
  // A 64-bit key survives with its top bit set.
  Ledger big;
  big.add(d1, 0xF123456789ABCDEFull, 1.0);
  Ledger big2 = Ledger::parse(big.serialize());
  check(near(big2.used(d1, 0xF123456789ABCDEFull), 1.0), "a top-bit key round-trips");
  // Garbage lines are skipped, not fatal.
  Ledger g = Ledger::parse("day 20260924\nnonsense\n00000000000000aa 12.5\n\n");
  check(near(g.used(d1, 0xAAu), 12.5), "garbage lines are skipped");

  // MIDNIGHT: the next day starts empty, for every book.
  check(near(l.used(d2, 0xAAAAu), 0.0), "a new day refills book A");
  check(near(l.used(d2, 0xBBBBu), 0.0), "a new day refills book B");
  // A ledger loaded on a later day is stale as a whole.
  Ledger stale = Ledger::parse("day 20260901\n00000000000000aa 999\n");
  check(near(stale.used(d1, 0xAAu), 0.0), "a stale file refills");

  // IS THIS READING? Only a book page, awake, in front.
  check(counts(true, false, false, false), "a book page in front counts");
  check(!counts(false, false, false, false), "a menu does not count");
  check(!counts(true, true, false, false), "asleep does not count");
  check(!counts(true, false, true, false), "the sleep screen does not count");
  check(!counts(true, false, false, true), "the background does not count");

  // QUANTIZE: 0 exactly when clean, 120 exactly when spent, so the renderer's
  // "t > 0" test and "fully gone" test are both exact.
  check(quantize(0) == 0 && quantize(-1) == 0, "clean quantizes to 0");
  check(quantize(1) == 120 && quantize(2) == 120, "spent quantizes to 120");
  check(quantize(0.001) >= 0 && quantize(0.5) == 60, "midpoint is 60");

  // THE LIGHT PICTURE. At the first instant of the last minute EVERY pixel
  // keeps all of its ink -- the first curve started its threshold at 0.15 and
  // 4.6% of the ink dropped by up to 59% the moment the minute began
  // (adversarial review). At the end NONE survives, or the spent page reads.
  {
    using namespace readingallowance::picture;
    bool allKept = true, noneLeft = true, mono = true;
    for (int y = 0; y < 200; y++)
      for (int x = 0; x < 200; x++) {
        const float tooth = toothAt(x, y);
        if (tooth < 0.0f || tooth > 1.0f) allKept = false;
        if (inkRetained(tooth, 0.0f) < 1.0f) allKept = false;
        if (inkRetained(tooth, 1.0f) > 0.0f) noneLeft = false;
        float prev = 2.0f;
        for (int k = 0; k <= 120; k++) {
          const float r = inkRetained(tooth, k / 120.0f);
          if (r > prev + 1e-6f) mono = false;
          prev = r;
        }
      }
    check(allKept, "light: t = 0 keeps every pixel's ink (and tooth in [0,1])");
    check(noneLeft, "light: t = 1 leaves no ink anywhere");
    check(mono, "light: ink only ever leaves");
    check(veilAlpha(0.0f, 0.5f, 1.0f) == 0.0f, "light: a paper pixel is never veiled");
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
