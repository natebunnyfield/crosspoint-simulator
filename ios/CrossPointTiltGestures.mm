// The CoreMotion half of the four tilts. Everything decidable without
// CoreMotion is in ios/TiltGestures.h and proved by tests/tilt_gestures_test.cpp;
// this file is the adapter and holds no thresholds of its own.

#import <CoreMotion/CoreMotion.h>
#import <Foundation/Foundation.h>

#include <SDL3/SDL.h>

#include "GestureBindings.h"
#include "TiltGestures.h"

extern "C" int CrossPointPrefs_gestureBinding(int gesture);
extern "C" void CrossPointZenRecognizers_fireGesture(int gesture);
extern "C" void CrossPointTiltGestures_begin(void);
extern "C" void CrossPointTiltGestures_perFrame(void);
extern "C" void CrossPointTiltGestures_appWillResignActive(void);

namespace {

CMMotionManager *g_motion = nil;
tiltgesture::Neutral g_neutral;
bool g_armed = true;
int g_lastBound = -1;

// The same question the volume rocker asks, and for the same reason: a stream
// nobody has bound is battery spent on nothing.
bool anyTiltBound() {
  return tiltgesture::anyTiltBound([](gesturebind::Gesture g) {
    const int stored = CrossPointPrefs_gestureBinding(static_cast<int>(g));
    const gesturebind::Action inZen = gesturebind::actionFor(g, true, stored);
    if (inZen != gesturebind::Action::Nothing) return inZen;
    return gesturebind::actionFor(g, false, stored);
  });
}

// 20 Hz. Fast enough that a deliberate wrist movement is caught inside a
// frame or two, slow enough not to wake the CPU for nothing -- and the
// hysteresis in TiltGestures.h, not the rate, is what stops repeats.
constexpr double kUpdateInterval = 1.0 / 20.0;

void startStream() {
  if (g_motion) return;
  g_motion = [[CMMotionManager alloc] init];
  if (!g_motion.deviceMotionAvailable) {
    SDL_Log("[TILT] device motion unavailable -- the four tilt rows cannot fire");
    g_motion = nil;
    return;
  }
  g_motion.deviceMotionUpdateInterval = kUpdateInterval;
  [g_motion startDeviceMotionUpdates];
  // NEUTRAL IS CAPTURED ON THE NEXT SAMPLE, not here: deviceMotion is nil for
  // the first few milliseconds after starting, and capturing (0,0) would make
  // "flat" the origin -- the exact assumption TiltGestures.h exists to avoid.
  g_neutral = {};
  g_armed = true;
  SDL_Log("[TILT] motion stream started");
}

void stopStream() {
  if (!g_motion) return;
  [g_motion stopDeviceMotionUpdates];
  g_motion = nil;
  g_neutral = {};
  g_armed = true;
  SDL_Log("[TILT] motion stream stopped");
}

}  // namespace

void CrossPointTiltGestures_begin(void) {
  // Re-log and re-evaluate on the next perFrame: a wake is exactly when the
  // owner may have bound or unbound a row in Settings.app.
  g_lastBound = -1;
}

void CrossPointTiltGestures_appWillResignActive(void) {
  // Backgrounded: no reason to hold the accelerometer, and the pose on return
  // is a new pose, so neutral is recaptured rather than carried across.
  stopStream();
  g_lastBound = -1;
}

void CrossPointTiltGestures_perFrame(void) {
  const int bound = anyTiltBound() ? 1 : 0;
  if (bound != g_lastBound) {
    g_lastBound = bound;
    if (bound) {
      startStream();
    } else {
      stopStream();
    }
  }
  if (!g_motion) return;

  CMDeviceMotion *dm = g_motion.deviceMotion;
  if (!dm) return;  // not yet sampling
  const float gx = static_cast<float>(dm.gravity.x);
  const float gy = static_cast<float>(dm.gravity.y);

  if (!g_neutral.captured) {
    g_neutral = {gx, gy, true};
    SDL_Log("[TILT] neutral captured at (%.2f, %.2f)", gx, gy);
    return;
  }

  const tiltgesture::Decision d = tiltgesture::decide(gx, gy, g_neutral, g_armed);
  switch (d.outcome) {
    case tiltgesture::Outcome::Fire:
      g_armed = false;
      SDL_Log("[TILT] %s at (%.2f, %.2f)", gesturebind::gestureName(d.gesture), gx, gy);
      CrossPointZenRecognizers_fireGesture(static_cast<int>(d.gesture));
      break;
    case tiltgesture::Outcome::Rearm:
      g_armed = true;
      break;
    case tiltgesture::Outcome::None:
      break;
  }
}
