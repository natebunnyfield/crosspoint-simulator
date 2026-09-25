// THE READING SPEEDRUN -- src/Speedrun.h.
//
// Splits, gold splits and the run delta are numbers nothing else checks: a
// flip-through that set an unbeatable best, a menu that ended the run, a book
// change that kept the old delta -- each would show a confident wrong number.

#include "Speedrun.h"

#include <cmath>
#include <cstdio>

using namespace speedrun;

static int failures = 0;
static void check(bool ok, const char *what) {
  if (!ok) { std::printf("FAIL: %s\n", what); failures++; }
}
static bool near(double a, double b) { return std::fabs(a - b) < 1e-9; }

static void readFor(Run &r, PageKey k, double secs) {
  for (int i = 0; i < static_cast<int>(secs * 10 + 0.5); i++) r.step(true, k, true, 0.1);
}

int main() {
  const PageKey p1{7, 0, 1}, p2{7, 0, 2}, p3{7, 0, 3};
  Run r;
  readFor(r, p1, 10); readFor(r, p2, 8); r.step(true, p3, true, 0.0);
  check(r.splits == 2, "two pages read are two splits");
  check(near(r.best[p1], 10) && near(r.best[p2], 8), "first reads set the bests");
  check(near(r.runDelta, 0), "no bests to beat, no delta");
  check(std::fabs(r.runSecs - 18) < 1e-6, "the run clock is the sum");

  // Second run over the same pages: faster on p1, slower on p2.
  Run s; s.parse(r.serialize());
  readFor(s, p1, 7); readFor(s, p2, 9); s.step(true, p3, true, 0.0);
  check(std::fabs(s.runDelta - (-3 + 1)) < 1e-6, "delta sums (time - best) over splits");
  check(std::fabs(s.best[p1] - 7) < 1e-6 && std::fabs(s.best[p2] - 8) < 1e-6, "only a faster split replaces a best");
  check(s.golds == 1, "a beaten best is a gold split");

  // A flip-through neither counts nor records.
  Run f; f.parse(s.serialize());
  readFor(f, p1, 0.3); f.step(true, p2, true, 0.0);
  check(f.splits == 0 && std::fabs(f.best[p1] - 7) < 1e-6, "a page under a second is not a split");

  // A menu pauses; it does not end the split or the run.
  Run m;
  readFor(m, p1, 3); m.step(false, p1, false, 0.5); readFor(m, p1, 2);
  check(std::fabs(m.pageSecs - 5) < 1e-6 && m.splits == 0, "a menu pauses the page");

  // Not-reading steps (asleep, background) add nothing; a stall is capped.
  Run c; c.step(true, p1, true, 3600.0);
  check(std::fabs(c.pageSecs - kMaxStepSeconds) < 1e-9, "a stall is capped");
  c.step(true, p1, false, 1.0);
  check(std::fabs(c.pageSecs - kMaxStepSeconds) < 1e-9, "not reading adds nothing");

  // A new book is a new run.
  Run b; readFor(b, p1, 5); readFor(b, p2, 5);
  b.step(true, PageKey{99, 0, 1}, true, 0.0);
  check(b.splits == 0 && near(b.runSecs, 0), "a different book starts a new run");

  // Live page delta.
  Run l; l.parse("0000000000000007 0 1 6.00\n");
  readFor(l, p1, 4);
  check(std::fabs(l.pageDelta() - (-2)) < 1e-6, "the live page delta is time minus best");
  check(std::isnan(Run{}.pageDelta()), "no best, no delta");

  check(clock(125.9) == "02:05" && delta(-2.04) == "-2.0" && delta(1.0) == "+1.0",
        "formatting");

  if (failures == 0) std::printf("speedrun: all passed\n");
  return failures == 0 ? 0 : 1;
}
