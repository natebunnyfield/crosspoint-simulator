#pragma once

#include <cmath>

#include "GestureBindings.h"

// THE FOUR TILTS -- the whole decision, in one pure header.
//
// Owner ruling 2026-09-06: *"add rotate and tilt etc gestures"*, narrowed the
// same day to the FOUR TILTS alone. A device-level rotation and a face-down
// gesture were both offered and declined, so this file has no roll-through-90
// case and no face-down case, and their absence is a ruling rather than an
// omission.
//
// WHY A PURE HEADER. Everything CoreMotion gives is a gravity vector; every
// way this can be wrong is silent on a device -- a tilt that fires while the
// owner shifts in a chair, a tilt that fires forever while the phone is held
// at an angle, a tilt that never re-arms because "neutral" was assumed to be
// flat. None of CMMotionManager exists on a host to prove it against, so the
// arithmetic lives here and ios/CrossPointTiltGestures.mm is a thin adapter.
// Same discipline as GestureBindings.h and VolumePageTurn.h.
namespace tiltgesture {

// NEUTRAL IS CAPTURED, NOT ASSUMED FLAT. A reader in bed holds the phone at
// 40 degrees and a reader at a desk holds it at 10; if neutral were flat, the
// first would sit permanently past any useful threshold and the second would
// need an exaggerated motion to reach one. So the pose held when the gestures
// arm becomes the origin, and a tilt is measured as a DEPARTURE from it.
struct Neutral {
  float x = 0.0f;  // gravity components at arming time, normalized
  float y = 0.0f;
  bool captured = false;
};

// HOW FAR IS A TILT, and how far back is "returned". Two thresholds, not one,
// because a single threshold chatters: a pose resting exactly at the boundary
// fires on every sample of sensor noise. The gap is the hysteresis.
//
// kEnterG is in units of gravity along one axis: sin(20 degrees) = 0.34, which
// is a deliberate, visible movement of the wrist rather than a drift. kLeaveG
// = sin(9 degrees) = 0.16, so the phone must come most of the way back before
// the same tilt can fire again. Both are measured from the captured neutral,
// so they are relative angles, not absolute ones.
constexpr float kEnterG = 0.34f;
constexpr float kLeaveG = 0.16f;

// ONE TILT AT A TIME. A diagonal motion crosses both axes, and firing two
// bound actions from one wrist movement is never what was meant -- so the
// LARGER departure wins and the other axis is ignored until the pose returns.
// The margin stops a 45-degree motion from being decided by sensor noise: the
// winning axis must lead by this much or neither fires.
constexpr float kAxisMargin = 0.08f;

// What a sample decides.
enum class Outcome { None, Fire, Rearm };

struct Decision {
  Outcome outcome = Outcome::None;
  gesturebind::Gesture gesture = gesturebind::Gesture::Count;
};

// THE AXES. CoreMotion's gravity is in device coordinates: +x is toward the
// right edge of the screen in portrait, +y toward the top, +z out of the
// glass. Tilting the phone LEFT (left edge down) makes gravity's x component
// go NEGATIVE, and tilting it AWAY from the reader (top edge down) makes y go
// negative -- so "forward" is -y, which is the direction a page would fall
// away from you. These four constants are the only place that mapping is
// stated; the adapter passes raw components and reads back a row.
constexpr gesturebind::Gesture kLeft = gesturebind::Gesture::TiltLeft;
constexpr gesturebind::Gesture kRight = gesturebind::Gesture::TiltRight;
constexpr gesturebind::Gesture kForward = gesturebind::Gesture::TiltForward;
constexpr gesturebind::Gesture kBack = gesturebind::Gesture::TiltBack;

// One sample. `armed` is false while a previous tilt is still being held --
// the caller owns that bit, so this stays a pure function of its inputs.
//
// Returns Fire with the row to send, Rearm when the pose has come back inside
// kLeaveG on both axes, or None while nothing has changed. A Fire does NOT
// re-arm: the caller sets armed=false and waits for the Rearm.
constexpr Decision decide(float gx, float gy, const Neutral& n, bool armed) {
  const float dx = gx - n.x;
  const float dy = gy - n.y;
  const float ax = dx < 0 ? -dx : dx;
  const float ay = dy < 0 ? -dy : dy;

  if (!armed) {
    if (ax < kLeaveG && ay < kLeaveG) return {Outcome::Rearm, gesturebind::Gesture::Count};
    return {};
  }

  const bool xWins = ax >= ay + kAxisMargin;
  const bool yWins = ay >= ax + kAxisMargin;

  if (xWins && ax >= kEnterG) return {Outcome::Fire, dx < 0 ? kLeft : kRight};
  if (yWins && ay >= kEnterG) return {Outcome::Fire, dy < 0 ? kForward : kBack};
  return {};
}

// IS ANY TILT ROW BOUND? CoreMotion updates cost battery, so the motion
// manager runs only while at least one of the four rows points at something.
// Zen state is not consulted, for the same reason the volume rocker's arming
// does not consult it: a row bound only outside zen still needs the stream
// running or the first tilt after leaving zen is lost.
template <typename LiveAction>
constexpr bool anyTiltBound(LiveAction live) {
  return live(kLeft) != gesturebind::Action::Nothing ||
         live(kRight) != gesturebind::Action::Nothing ||
         live(kForward) != gesturebind::Action::Nothing ||
         live(kBack) != gesturebind::Action::Nothing;
}

}  // namespace tiltgesture
