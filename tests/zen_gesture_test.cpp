// The three-finger tap that toggles zen (ST-011).
//
// This exists because the gesture cannot be exercised on a host any other way:
// the harness's input script drives the FIRMWARE's touch state rather than SDL
// finger events, and simctl cannot inject multitouch. Without it the toggle
// would ship on nothing but a code reading.
#include "ZenGesture.h"

#include <cstdio>

namespace {

int failures = 0;

void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    failures++;
  }
}

const zengesture::Rect kPage{0, 100, 600, 800};

// Three fingers down, three up, all on the page and none of them moving.
bool cleanThreeFingerTap(zengesture::Detector &d) {
  d.fingerDown(300, 400);
  d.fingerDown(320, 410);
  d.fingerDown(340, 400);
  bool fired = false;
  fired |= d.fingerUp(300, 400, kPage);
  fired |= d.fingerUp(320, 410, kPage);
  fired |= d.fingerUp(340, 400, kPage);
  return fired;
}

}  // namespace

int main() {
  {
    zengesture::Detector d;
    check(cleanThreeFingerTap(d), "a clean three-finger tap on the page fires");
    check(d.activeFingers() == 0, "no fingers left down afterwards");
  }
  {
    // It has to be repeatable: zen is a toggle, so the SECOND tap matters as
    // much as the first, and stale state is exactly how a toggle gets stuck on.
    zengesture::Detector d;
    check(cleanThreeFingerTap(d), "first tap fires");
    check(cleanThreeFingerTap(d), "second tap fires too (the toggle is repeatable)");
  }
  {
    zengesture::Detector d;
    d.fingerDown(300, 400);
    check(!d.fingerUp(300, 400, kPage), "one finger is not the gesture");
  }
  {
    zengesture::Detector d;
    d.fingerDown(300, 400);
    d.fingerDown(320, 400);
    bool fired = d.fingerUp(300, 400, kPage);
    fired |= d.fingerUp(320, 400, kPage);
    check(!fired, "two fingers are not the gesture");
  }
  {
    zengesture::Detector d;
    for (int i = 0; i < 4; i++) d.fingerDown(300.0f + i * 10, 400);
    bool fired = false;
    for (int i = 0; i < 4; i++) fired |= d.fingerUp(300.0f + i * 10, 400, kPage);
    check(!fired, "FOUR fingers are not the gesture -- a hand resting must not toggle");
  }
  {
    zengesture::Detector d;
    d.fingerDown(300, 400);
    d.fingerDown(320, 400);
    d.fingerDown(340, 400);
    d.fingerMoved(300, 600);  // a drag
    bool fired = false;
    fired |= d.fingerUp(300, 600, kPage);
    fired |= d.fingerUp(320, 400, kPage);
    fired |= d.fingerUp(340, 400, kPage);
    check(!fired, "three fingers DRAGGING is a scroll, not a tap");
  }
  {
    zengesture::Detector d;
    d.fingerDown(300, 400);
    d.fingerDown(320, 400);
    d.fingerDown(340, 400);
    bool fired = false;
    fired |= d.fingerUp(300, 400, kPage);
    fired |= d.fingerUp(320, 400, kPage);
    fired |= d.fingerUp(340, 50, kPage);  // above the page
    check(!fired, "lifting off the page does not fire");
  }
  {
    zengesture::Detector d;
    d.fingerDown(300, 400);
    d.fingerDown(320, 400);
    d.fingerDown(340, 400);
    bool fired = false;
    fired |= d.fingerUp(300, 400, kPage);
    fired |= d.fingerUp(320, 400, kPage, /*cancelled=*/true);
    fired |= d.fingerUp(340, 400, kPage);
    check(!fired, "a CANCELLED touch (Control Centre, a call) is not a lift");
  }
  {
    // Fingers rarely land together: the middle one often arrives a frame late,
    // and one may lift before the others. Peak count is what matters.
    zengesture::Detector d;
    d.fingerDown(300, 400);
    d.fingerDown(320, 400);
    bool fired = d.fingerUp(300, 400, kPage);  // one leaves early
    check(!fired, "an early lift while others are down does not fire");
    d.fingerDown(340, 400);  // and a third arrives
    d.fingerDown(360, 400);
    fired |= d.fingerUp(320, 400, kPage);
    fired |= d.fingerUp(340, 400, kPage);
    fired |= d.fingerUp(360, 400, kPage);
    check(!fired, "a rolling four-finger sequence does not fire");
  }
  {
    // Small roll as fingers lift: within the slop, still a tap.
    zengesture::Detector d;
    d.fingerDown(300, 400);
    d.fingerDown(320, 400);
    d.fingerDown(340, 400);
    d.fingerMoved(322, 405);
    bool fired = false;
    fired |= d.fingerUp(300, 400, kPage);
    fired |= d.fingerUp(322, 405, kPage);
    fired |= d.fingerUp(340, 400, kPage);
    check(fired, "a small roll within the slop is still a tap");
  }

  if (failures == 0) std::printf("zen_gesture_test: all checks passed\n");
  return failures == 0 ? 0 : 1;
}
