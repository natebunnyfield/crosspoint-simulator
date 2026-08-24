// The zen DELIBERATE TAP, the one gesture left on the SDL classifier
// (ZenVerbs.h carries the succession: zones -> hand-rolled verbs -> native
// UIKit recognizers for all motion, owner 2026-08-22 "let's use apple for
// swiping instead"). Everything that MOVES and every multi-finger tap is a
// UIGestureRecognizer now (ios/CrossPointZenRecognizers.mm) and is
// device-confirm only — Apple's engine cannot be driven off-device. What
// these tests pin is the classifier's half of the no-double-fire argument:
// the tap gates (28 px slop, 400 ms), and that the classifier answers NONE
// for anything that travels or lands more than one finger — so a gesture a
// recognizer fires can never also fire this path.
#include "ZenVerbs.h"

#include <cstdio>
#include "TestCheck.h"
using testcheck::check;

namespace {

using zenverbs::Classifier;
using zenverbs::Verb;

int &failures = testcheck::g_failures;

const char *name(Verb v) { return zenverbs::verbName(v); }

void checkVerb(Verb got, Verb want, const char *what) {
  if (got != want) {
    std::printf("FAIL: %s (got '%s', want '%s')\n", what, name(got), name(want));
    failures++;
  }
}

// One finger: down at (x,y), optional travel to (x+dx,y+dy), lift at t=durMs.
Verb oneFinger(Classifier &c, float dx, float dy, uint64_t durMs) {
  c.fingerDown(1, 500, 500, 1000);
  if (dx != 0 || dy != 0) c.fingerMove(1, 500 + dx, 500 + dy);
  return c.fingerUp(1, 500 + dx, 500 + dy, 1000 + durMs);
}

// Two fingers landing 200 px apart horizontally, each traveling its own
// vector, lifting together at t=durMs.
Verb twoFinger(Classifier &c, float dx1, float dy1, float dx2, float dy2,
               uint64_t durMs = 200) {
  c.fingerDown(1, 400, 500, 1000);
  c.fingerDown(2, 600, 500, 1010);
  c.fingerMove(1, 400 + dx1, 500 + dy1);
  c.fingerMove(2, 600 + dx2, 500 + dy2);
  Verb v = c.fingerUp(1, 400 + dx1, 500 + dy1, 1000 + durMs);
  checkVerb(v, Verb::None, "first lift of two answers nothing");
  return c.fingerUp(2, 600 + dx2, 500 + dy2, 1000 + durMs);
}

// N motionless fingers, all down within 30 ms, all up at t=durMs.
Verb nFingerTap(Classifier &c, int n, uint64_t durMs = 120) {
  for (int i = 0; i < n; ++i)
    c.fingerDown(i + 1, 300 + 40.0f * i, 500, 1000 + 10 * i);
  Verb v = Verb::None;
  for (int i = 0; i < n; ++i)
    v = c.fingerUp(i + 1, 300 + 40.0f * i, 500, 1000 + durMs);
  return v;
}

}  // namespace

int main() {
  Classifier c;

  // ---- THE ONE VERB ----
  checkVerb(oneFinger(c, 0, 0, 100), Verb::Down, "1-finger tap -> Down");

  // ---- The tap gate: the shipped deliberate-tap constants ----
  checkVerb(oneFinger(c, 28, 0, 100), Verb::Down,
            "28 px of travel is still a tap");
  checkVerb(oneFinger(c, 29, 0, 100), Verb::None,
            "29 px of travel is not a tap (a swipe is the recognizers')");
  {
    // 400 ms is a tap; 401 ms held still is a long-press, which is nothing.
    Classifier d;
    checkVerb(oneFinger(d, 0, 0, 400), Verb::Down, "400 ms is still a tap");
    checkVerb(oneFinger(d, 0, 0, 401), Verb::None, "401 ms motionless -> nothing");
  }
  // A finger that wanders out past the slop and RETURNS is not a tap: the
  // excursion is judged over the whole gesture, not the final position.
  {
    Classifier d;
    d.fingerDown(1, 500, 500, 1000);
    d.fingerMove(1, 540, 500);
    d.fingerMove(1, 500, 500);
    checkVerb(d.fingerUp(1, 500, 500, 1100), Verb::None,
              "out-and-back past the slop is not a tap");
  }

  // ---- Motion is the RECOGNIZERS' domain: every swipe answers None here.
  // This is the classifier's half of the no-double-fire construction — a
  // touch that fires a UISwipeGestureRecognizer traveled far past the slop,
  // so this path is guaranteed silent for it. ----
  checkVerb(oneFinger(c, -80, 5, 200), Verb::None, "1-finger swipe left -> None");
  checkVerb(oneFinger(c, 80, -5, 200), Verb::None, "1-finger swipe right -> None");
  checkVerb(oneFinger(c, 0, 80, 200), Verb::None, "1-finger swipe down -> None");
  checkVerb(oneFinger(c, 0, -80, 200), Verb::None, "1-finger swipe up -> None");
  checkVerb(twoFinger(c, -80, 0, -80, 0), Verb::None, "2-finger swipe -> None");
  checkVerb(twoFinger(c, 80, 0, -80, 0), Verb::None, "pinch -> None");
  checkVerb(twoFinger(c, -80, 0, 80, 0), Verb::None, "spread -> None");

  // ---- Multi-finger taps have another owner: the recognizers (2-tap
  // select, 3-tap zen toggle, 4-tap power). All None here — which is the
  // toggle-exclusion argument too: the same three fingers that fire the
  // native toggle can never also turn a page through this path. ----
  checkVerb(nFingerTap(c, 2), Verb::None, "2-finger tap is the recognizers'");
  checkVerb(nFingerTap(c, 3), Verb::None, "3-finger tap is the toggle's");
  checkVerb(nFingerTap(c, 4), Verb::None, "4-finger tap is the recognizers'");
  checkVerb(nFingerTap(c, 5), Verb::None, "5-finger tap -> nothing");

  // ---- Rolling hand: touched exceeds peak, so nothing -- even though each
  // contact alone would have been a clean tap. ----
  {
    Classifier d;
    d.fingerDown(1, 400, 500, 1000);
    checkVerb(d.fingerUp(1, 400, 500, 1050), Verb::Down, "first contact taps");
    d.fingerDown(2, 440, 500, 1100);
    d.fingerDown(3, 480, 500, 1110);
    checkVerb(d.fingerUp(2, 440, 500, 1150), Verb::None, "mid-roll answers nothing");
    d.fingerDown(4, 520, 500, 1160);
    Verb v = d.fingerUp(3, 480, 500, 1200);
    checkVerb(v, Verb::None, "still rolling");
    // Three fingers took part in this gesture but only two were ever down at
    // once: touched (3) != peak (2), so the roll is nothing.
    checkVerb(d.fingerUp(4, 520, 500, 1220), Verb::None,
              "a rolling hand (touched > peak) -> nothing");
  }

  // ---- Cancel ----
  {
    Classifier d;
    d.fingerDown(1, 500, 500, 1000);
    checkVerb(d.fingerUp(1, 500, 500, 1050, /*cancelled=*/true), Verb::None,
              "a cancelled tap fires nothing");
    // And the cancel does not leak into the next gesture.
    checkVerb(oneFinger(d, 0, 0, 100), Verb::Down, "clean tap after a cancel");
  }

  // ---- No state leaks back-to-back ----
  {
    Classifier d;
    checkVerb(oneFinger(d, -80, 0, 200), Verb::None, "swipe -> nothing");
    checkVerb(oneFinger(d, 0, 0, 100), Verb::Down, "then a clean tap");
    checkVerb(nFingerTap(d, 5), Verb::None, "then a 5-finger nothing");
    checkVerb(twoFinger(d, -80, 0, 80, 0), Verb::None, "then a spread nothing");
    checkVerb(oneFinger(d, 0, 0, 120), Verb::Down, "then a clean tap again");
  }

  // ---- One owner per gesture: the toggle's three fingers, seen through the
  // classifier as SDL still streams them, answer None on EVERY lift — not
  // just the last — so the native toggle can never leak a page-forward tap
  // through this path whatever the event ordering. ----
  {
    Classifier d;
    d.fingerDown(1, 300, 400, 1000);
    d.fingerDown(2, 320, 410, 1005);
    d.fingerDown(3, 340, 400, 1010);
    checkVerb(d.fingerUp(1, 300, 400, 1100), Verb::None, "toggle lift 1: no verb");
    checkVerb(d.fingerUp(2, 320, 410, 1100), Verb::None, "toggle lift 2: no verb");
    checkVerb(d.fingerUp(3, 340, 400, 1100), Verb::None, "toggle lift 3: no verb");
    // And the classifier recovers for the next gesture.
    checkVerb(oneFinger(d, 0, 0, 100), Verb::Down, "clean tap after the toggle");
  }

  if (failures == 0) {
    std::printf("zen_verbs_test: all checks passed\n");
    return 0;
  }
  std::printf("zen_verbs_test: %d FAILURES\n", failures);
  return 1;
}
