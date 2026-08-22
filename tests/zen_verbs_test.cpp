// The zen gesture language (owner 2026-08-22; ZenVerbs.h carries the ruling
// verbatim). Pure tests are the ONLY coverage multi-finger gestures get: the
// harness's input script drives the firmware's touch state rather than SDL
// finger events, and neither simctl nor any existing hook can synthesize two
// moving fingers. Every rule the classifier enforces is pinned here or it
// ships on a code reading.
#include "ZenVerbs.h"

#include "ZenGesture.h"

#include <cstdio>

namespace {

using zenverbs::Classifier;
using zenverbs::Verb;

int failures = 0;

void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    failures++;
  }
}

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

  // ---- THE MAPPING, verb by verb (owner order 2026-08-22 verbatim in
  // ZenVerbs.h) ----
  checkVerb(oneFinger(c, 0, 0, 100), Verb::Down, "1-finger tap -> Down");
  checkVerb(oneFinger(c, -80, 5, 200), Verb::Down, "1-finger swipe left -> Down");
  checkVerb(oneFinger(c, 80, -5, 200), Verb::Up, "1-finger swipe right -> Up");
  checkVerb(twoFinger(c, -80, 0, -80, 0), Verb::Right, "2-finger swipe left -> Right");
  checkVerb(twoFinger(c, 80, 0, 80, 0), Verb::Left, "2-finger swipe right -> Left");
  checkVerb(twoFinger(c, 0, 80, 0, 80), Verb::Select, "2-finger swipe down -> Select");
  checkVerb(twoFinger(c, 0, -80, 0, -80), Verb::Back, "2-finger swipe up -> Back");
  checkVerb(nFingerTap(c, 4), Verb::Power, "4-finger tap -> Power");

  // ---- The tap gate: the shipped deliberate-tap constants ----
  checkVerb(oneFinger(c, 28, 0, 100), Verb::Down,
            "28 px of travel is still a tap");
  checkVerb(oneFinger(c, 29, 0, 100), Verb::None,
            "29 px of travel is not a tap (and not yet a swipe)");
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

  // ---- Swipe gates ----
  checkVerb(oneFinger(c, 59, 0, 200), Verb::None, "59 px is below the swipe floor");
  checkVerb(oneFinger(c, 60, 0, 200), Verb::Up, "60 px is a swipe");
  checkVerb(oneFinger(c, -80, 41, 200), Verb::None,
            "diagonal-ambiguous (|dom| < 2|cross|) -> nothing");
  checkVerb(oneFinger(c, -80, 40, 200), Verb::Down,
            "exactly 2:1 dominant/cross still classifies");
  checkVerb(oneFinger(c, 0, 80, 200), Verb::None, "1-finger swipe down -> nothing");
  checkVerb(oneFinger(c, 0, -80, 200), Verb::None, "1-finger swipe up -> nothing");
  checkVerb(oneFinger(c, 80, 0, 700), Verb::Up, "700 ms swipe is in time");
  checkVerb(oneFinger(c, 80, 0, 701), Verb::None, "701 ms swipe is too slow");

  // ---- 2-finger direction from AVERAGED vectors ----
  checkVerb(twoFinger(c, -90, 0, -50, 0), Verb::Right,
            "uneven fingers average to a left swipe (avg -70, stretch 40)");
  // A MORE uneven pair (-100/-40) stretches the pair by exactly 60 px --
  // opposed motion at the pinch floor while the centroid also travels: that is
  // the ambiguity cell, and it fires nothing rather than guessing.
  checkVerb(twoFinger(c, -100, 0, -40, 0), Verb::None,
            "swipe so uneven it reads as half a spread -> nothing");
  checkVerb(twoFinger(c, -70, 0, -40, 0), Verb::None,
            "average below the floor (avg -55) -> nothing");
  {
    // One finger lifts EARLY: still counts two (peak), and its final position
    // still contributes to the average.
    Classifier d;
    d.fingerDown(1, 400, 500, 1000);
    d.fingerDown(2, 600, 500, 1010);
    d.fingerMove(1, 320, 500);
    checkVerb(d.fingerUp(1, 320, 500, 1150), Verb::None, "early lift answers nothing");
    d.fingerMove(2, 520, 500);
    checkVerb(d.fingerUp(2, 520, 500, 1300), Verb::Right,
              "2-finger swipe left with one early lift still counts 2 -> Right");
  }
  {
    // A 2-finger TAP is no verb.
    Classifier d;
    checkVerb(nFingerTap(d, 2), Verb::Select,
              "2-finger tap -> Confirm (owner 2026-08-22)");
  }

  // ---- Pinch / spread (owner amendment 2026-08-22) ----
  // Fingers converge 80 px each, centroid fixed: FontDown.
  checkVerb(twoFinger(c, 80, 0, -80, 0), Verb::FontDown,
            "pinch (fingers converge) -> FontDown");
  checkVerb(twoFinger(c, -80, 0, 80, 0), Verb::FontUp,
            "spread (fingers diverge) -> FontUp");
  // Asymmetric pinch: one finger does the work, centroid drifts 25 px (< 28),
  // distance shrinks 50... make it shrink >= 60: finger 1 moves +60 toward 2.
  checkVerb(twoFinger(c, 60, 0, 0, 0), Verb::None,
            "one-sided 60 px converge moves the centroid 30 px -> ambiguous");
  // |dd| = 50 (under the pinch floor) while the centroid travels 75: the
  // coordinator's matrix says this is the SWIPE cell, and rightward it is.
  checkVerb(twoFinger(c, 100, 0, 50, 0), Verb::Left,
            "centroid >= 60 with distance change under 60 -> still a swipe");
  // The ambiguity cell: both opposed and common motion large.
  checkVerb(twoFinger(c, 140, 0, 0, 0), Verb::None,
            "distance shrinks 140 while centroid travels 70 -> nothing");
  // Both small: no verb (already covered by avg-below-floor above, pinned
  // explicitly for the matrix).
  checkVerb(twoFinger(c, 20, 0, -20, 0), Verb::Select,
            "40 px converge, still centroid: each finger under the tap slop -> a slightly wiggly 2-finger tap = Select (was nothing before the 2-tap mapping)");
  // Opposed VERTICAL motion of horizontally-separated fingers barely changes
  // their distance (sqrt(200^2+80^2)-200 = 15 px) and moves no centroid:
  // nothing, not a phantom pinch.
  checkVerb(twoFinger(c, 0, -40, 0, 40), Verb::None,
            "opposed vertical wiggle across a horizontal pair -> nothing");
  {
    // A true vertical pinch: fingers separated vertically, converging. The
    // axis must not matter.
    Classifier d;
    d.fingerDown(1, 500, 300, 1000);
    d.fingerDown(2, 500, 700, 1000);
    d.fingerMove(1, 500, 380);
    d.fingerMove(2, 500, 620);
    d.fingerUp(1, 500, 380, 1200);
    checkVerb(d.fingerUp(2, 500, 620, 1200), Verb::FontDown,
              "vertical pinch -> FontDown");
  }

  // ---- Peak-count rules ----
  checkVerb(nFingerTap(c, 3), Verb::None, "3-finger tap is the toggle's, not ours");
  checkVerb(nFingerTap(c, 5), Verb::None, "5-finger tap -> nothing");
  {
    // 3-finger swipe: nothing.
    Classifier d;
    d.fingerDown(1, 300, 500, 1000);
    d.fingerDown(2, 400, 500, 1000);
    d.fingerDown(3, 500, 500, 1000);
    d.fingerMove(1, 380, 500);
    d.fingerMove(2, 480, 500);
    d.fingerMove(3, 580, 500);
    d.fingerUp(1, 380, 500, 1200);
    d.fingerUp(2, 480, 500, 1200);
    checkVerb(d.fingerUp(3, 580, 500, 1200), Verb::None, "3-finger swipe -> nothing");
  }
  {
    // 4-finger swipe: nothing.
    Classifier d;
    for (int i = 1; i <= 4; ++i) d.fingerDown(i, 200.0f + 80 * i, 500, 1000);
    for (int i = 1; i <= 4; ++i) d.fingerMove(i, 280.0f + 80 * i, 500);
    Verb v = Verb::None;
    for (int i = 1; i <= 4; ++i) v = d.fingerUp(i, 280.0f + 80 * i, 500, 1200);
    checkVerb(v, Verb::None, "4-finger swipe -> nothing");
  }
  {
    // A rolling hand: touched exceeds peak, so nothing -- even though each
    // contact alone would have been a clean tap.
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
  {
    // Cancel of ONE finger of two poisons the whole gesture.
    Classifier d;
    d.fingerDown(1, 400, 500, 1000);
    d.fingerDown(2, 600, 500, 1000);
    d.fingerMove(1, 320, 500);
    d.fingerMove(2, 520, 500);
    d.fingerUp(1, 320, 500, 1100, /*cancelled=*/true);
    checkVerb(d.fingerUp(2, 520, 500, 1200), Verb::None,
              "one cancelled finger poisons the 2-finger swipe");
  }

  // ---- No state leaks back-to-back ----
  {
    Classifier d;
    checkVerb(oneFinger(d, -80, 0, 200), Verb::Down, "swipe left");
    checkVerb(oneFinger(d, 0, 0, 100), Verb::Down, "then a clean tap");
    checkVerb(nFingerTap(d, 5), Verb::None, "then a 5-finger nothing");
    checkVerb(nFingerTap(d, 4), Verb::Power, "then a 4-finger power tap");
    checkVerb(twoFinger(d, -80, 0, 80, 0), Verb::FontUp, "then a spread");
    checkVerb(oneFinger(d, 80, 0, 200), Verb::Up, "then a swipe right");
  }

  // ---- One owner per gesture: the 3-finger toggle vs the classifier ----
  {
    // The SAME event sequence fed to both: the toggle fires, the classifier
    // answers None, so a three-finger tap can never both toggle zen and press
    // a button.
    zengesture::Detector toggle;
    Classifier d;
    const zengesture::Rect page{0, 100, 600, 800};
    toggle.fingerDown(300, 400); d.fingerDown(1, 300, 400, 1000);
    toggle.fingerDown(320, 410); d.fingerDown(2, 320, 410, 1005);
    toggle.fingerDown(340, 400); d.fingerDown(3, 340, 400, 1010);
    bool toggled = false;
    toggled |= toggle.fingerUp(300, 400, page);
    checkVerb(d.fingerUp(1, 300, 400, 1100), Verb::None, "toggle lift 1: no verb");
    toggled |= toggle.fingerUp(320, 410, page);
    checkVerb(d.fingerUp(2, 320, 410, 1100), Verb::None, "toggle lift 2: no verb");
    toggled |= toggle.fingerUp(340, 400, page);
    checkVerb(d.fingerUp(3, 340, 400, 1100), Verb::None, "toggle lift 3: no verb");
    check(toggled, "the three-finger toggle itself fired");

    // And the other way: the verbs the classifier DOES own never fire the
    // toggle (wrong finger count for it).
    zengesture::Detector t2;
    Classifier d2;
    t2.fingerDown(300, 400);
    d2.fingerDown(1, 300, 400, 1000);
    bool t2fired = t2.fingerUp(300, 400, page);
    checkVerb(d2.fingerUp(1, 300, 400, 1050), Verb::Down, "1-finger tap -> Down");
    check(!t2fired, "a 1-finger tap does not toggle zen");

    zengesture::Detector t3;
    Classifier d3;
    for (int i = 1; i <= 4; ++i) {
      t3.fingerDown(200.0f + 80 * i, 400);
      d3.fingerDown(i, 200.0f + 80 * i, 400, 1000);
    }
    bool t3fired = false;
    Verb v3 = Verb::None;
    for (int i = 1; i <= 4; ++i) {
      t3fired |= t3.fingerUp(200.0f + 80 * i, 400, page);
      v3 = d3.fingerUp(i, 200.0f + 80 * i, 400, 1100);
    }
    checkVerb(v3, Verb::Power, "4-finger tap -> Power");
    check(!t3fired, "a 4-finger tap does not toggle zen (peak 4)");
  }

  if (failures == 0) {
    std::printf("zen_verbs_test: all checks passed\n");
    return 0;
  }
  std::printf("zen_verbs_test: %d FAILURES\n", failures);
  return 1;
}
