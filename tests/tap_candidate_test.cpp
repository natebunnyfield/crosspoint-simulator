// The page-tap candidate's arm/spoil lifecycle (ios/TapCandidate.h),
// extracted from the shim's SDL event watch after the 2026-08-21
// input-lifecycle audit. Both audit findings it fixes were SILENT: a latched
// candidate leaves the palette chip, keyboard chip and read-aloud taps dead
// until backgrounding (arming is gated on "none armed"), and a candidate
// firing while more fingers are down gives one gesture two effects. The SDL
// watch itself cannot be compiled off-device; this pure core can.
#include "TapCandidate.h"

#include <cstdio>

namespace {

int failures = 0;

void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    failures++;
  }
}

constexpr float kSlop = 36.0f;  // the shim passes 12 pt * scale; value free

}  // namespace

int main() {
  using tapcand::Candidate;

  // ---- The plain tap: arm, lift, fire — and the DOWN coordinates are what
  // fire, not the lift's. ----
  {
    Candidate c;
    c.fingerDown(7, 100, 200, 5000, /*onControl=*/false, /*concurrent=*/1);
    check(c.armedAs(7), "off-control finger arms");
    check(c.downX() == 100 && c.downY() == 200 && c.downMs() == 5000,
          "down coordinates and time recorded");
    check(c.fingerUp(7, /*cancelled=*/false), "clean lift fires");
    check(!c.armed(), "fired candidate is cleared");
  }

  // ---- AUDIT #1: a gesture-consuming exit (the zen toggle's early break)
  // must clear the candidate, or the chips and read-aloud go dead forever. ----
  {
    Candidate c;
    c.fingerDown(7, 100, 200, 5000, false, 1);
    c.spoil();  // the toggle resolved / mixer presented / backgrounded
    check(!c.armed(), "spoil clears the candidate");
    check(!c.fingerUp(7, false), "the spoiled finger's lift fires nothing");
    // The regression the audit found: after the latch, NOTHING could re-arm.
    c.fingerDown(8, 300, 400, 6000, false, 1);
    check(c.armedAs(8), "a later tap re-arms after a spoil");
    check(c.fingerUp(8, false), "and fires");
  }

  // ---- AUDIT #3: a second concurrent finger spoils the candidate, so the
  // candidate can never fire mid-multi-finger-gesture (the word-tap-then-
  // zen-toggle double effect). ----
  {
    Candidate c;
    c.fingerDown(1, 100, 200, 5000, false, 1);
    check(c.armed(), "first finger arms");
    c.fingerDown(2, 150, 250, 5030, false, 2);  // second finger of a gesture
    check(!c.armed(), "a second concurrent finger spoils");
    check(!c.fingerUp(1, false), "the candidate finger's early lift fires nothing");
    check(!c.fingerUp(2, false), "the other finger fires nothing either");
  }
  {
    // And a finger landing while others are down never arms, so finger 3 of
    // a 3-finger tap cannot become a fresh candidate after the spoil.
    Candidate c;
    c.fingerDown(1, 100, 200, 5000, false, 1);
    c.fingerDown(2, 150, 250, 5030, false, 2);
    c.fingerDown(3, 200, 300, 5060, false, 3);
    check(!c.armed(), "no arming while multiple fingers are down");
  }

  // ---- A finger on a control never arms; the pad owns its own taps. ----
  {
    Candidate c;
    c.fingerDown(4, 100, 200, 5000, /*onControl=*/true, 1);
    check(!c.armed(), "a control press is not a page-tap candidate");
    check(!c.fingerUp(4, false), "and its lift fires nothing");
    // Only one candidate at a time: the first off-control finger holds it.
    c.fingerDown(5, 100, 200, 6000, false, 1);
    c.fingerUp(5, false);
    check(!c.armed(), "cleared again after the cycle");
  }

  // ---- Drag past the slop is a swipe, not a tap. ----
  {
    Candidate c;
    c.fingerDown(6, 100, 200, 5000, false, 1);
    c.fingerMove(6, 100 + kSlop, 200, kSlop);  // exactly at the slop: keeps
    check(c.armed(), "movement within the slop keeps the candidate");
    c.fingerMove(6, 100 + kSlop + 1, 200, kSlop);
    check(!c.armed(), "movement past the slop spoils");
    check(!c.fingerUp(6, false), "and the lift fires nothing");
    // Another finger's movement never spoils the candidate.
    c.fingerDown(9, 50, 50, 7000, false, 1);
    c.fingerMove(6, 500, 500, kSlop);
    check(c.armedAs(9), "a stranger's movement does not spoil");
  }

  // ---- A cancelled lift (iOS took the touch) is not a tap — but it still
  // clears, so nothing stays latched. ----
  {
    Candidate c;
    c.fingerDown(7, 100, 200, 5000, false, 1);
    check(!c.fingerUp(7, /*cancelled=*/true), "a cancelled lift fires nothing");
    check(!c.armed(), "and clears");
  }

  // ---- Spoil is idempotent (backgrounding may fire twice: WILL_ENTER_
  // BACKGROUND then FOCUS_LOST). ----
  {
    Candidate c;
    c.spoil();
    c.spoil();
    check(!c.armed(), "spoil on empty is harmless");
  }

  if (failures == 0) {
    std::printf("tap_candidate_test: all checks passed\n");
    return 0;
  }
  std::printf("tap_candidate_test: %d FAILURES\n", failures);
  return 1;
}
