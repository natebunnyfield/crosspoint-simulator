// The four tilts' arming rule, proved on the host because none of it can be
// proved on a device: every failure mode is silent there.
#include <cassert>
#include <cstdio>

#include "../ios/TiltGestures.h"

using gesturebind::Gesture;
using tiltgesture::Decision;
using tiltgesture::Neutral;
using tiltgesture::Outcome;

static int failures = 0;
static void check(bool ok, const char* what) {
  if (!ok) { printf("FAIL: %s\n", what); ++failures; }
}

int main(int, char**) {
  const Neutral flat{0.0f, 0.0f, true};

  // 1. A held pose fires ONCE, not on every sample.
  Decision d = tiltgesture::decide(-0.5f, 0.0f, flat, true);
  check(d.outcome == Outcome::Fire && d.gesture == Gesture::TiltLeft, "left fires");
  d = tiltgesture::decide(-0.5f, 0.0f, flat, false);
  check(d.outcome == Outcome::None, "held tilt does not re-fire");

  // 2. It re-arms only after coming most of the way back.
  check(tiltgesture::decide(-0.20f, 0.0f, flat, false).outcome == Outcome::None,
        "half way back is not a re-arm");
  check(tiltgesture::decide(-0.05f, 0.0f, flat, false).outcome == Outcome::Rearm,
        "back near neutral re-arms");

  // 3. All four directions, with the sign convention pinned.
  check(tiltgesture::decide(0.5f, 0.0f, flat, true).gesture == Gesture::TiltRight, "right");
  check(tiltgesture::decide(0.0f, -0.5f, flat, true).gesture == Gesture::TiltForward, "forward");
  check(tiltgesture::decide(0.0f, 0.5f, flat, true).gesture == Gesture::TiltBack, "back");

  // 4. A diagonal fires NOTHING rather than two things.
  check(tiltgesture::decide(0.5f, 0.5f, flat, true).outcome == Outcome::None,
        "equal diagonal fires nothing");
  check(tiltgesture::decide(0.5f, 0.45f, flat, true).outcome == Outcome::None,
        "near-diagonal inside the margin fires nothing");
  check(tiltgesture::decide(0.5f, 0.2f, flat, true).gesture == Gesture::TiltRight,
        "a clear lead still fires");

  // 5. NEUTRAL IS CAPTURED, NOT FLAT -- the whole point. A reader holding the
  // phone at a steady angle is at rest, and the same wrist movement from there
  // fires the same row.
  const Neutral tipped{-0.40f, 0.0f, true};
  check(tiltgesture::decide(-0.40f, 0.0f, tipped, true).outcome == Outcome::None,
        "resting at the captured pose is not a tilt");
  check(tiltgesture::decide(-0.75f, 0.0f, tipped, true).gesture == Gesture::TiltLeft,
        "further left from a tipped neutral still fires left");
  check(tiltgesture::decide(-0.05f, 0.0f, tipped, true).gesture == Gesture::TiltRight,
        "coming back past neutral is a RIGHT tilt, not a left one");

  // 6. Hysteresis: the enter threshold is strictly beyond the leave one, or
  // the pair chatters at the boundary.
  check(tiltgesture::kEnterG > tiltgesture::kLeaveG, "enter beyond leave");

  // 7. anyTiltBound only counts the four tilt rows.
  auto none = [](Gesture) { return gesturebind::Action::Nothing; };
  check(!tiltgesture::anyTiltBound(none), "nothing bound -> no motion stream");
  auto oneBound = [](Gesture g) {
    return g == Gesture::TiltBack ? gesturebind::Action::Right : gesturebind::Action::Nothing;
  };
  check(tiltgesture::anyTiltBound(oneBound), "one bound row arms the stream");

  if (failures == 0) printf("tilt_gestures_test: all checks passed\n");
  return failures ? 1 : 0;
}
