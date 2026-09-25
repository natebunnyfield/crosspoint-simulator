// The CoreMotion half of the raking light (spike 2026-09-25). Everything
// decidable without CoreMotion -- the lamp, the rotation, the quantization,
// the hysteresis, the smoothing -- is in src/RakingLight.h and proved by
// tests/raking_light_test.cpp; the state it drives lives in
// src/SurfaceSheet.cpp. This file is the adapter and holds no thresholds.
//
// Its own CMMotionManager, not the tilt gestures': the two streams have
// different lives (tilts run while a tilt row is bound, this while the switch
// is on AND the page is light AND the letterpress is on), and sharing one
// manager would couple a gesture's battery decision to a picture's.

#import <CoreMotion/CoreMotion.h>
#import <Foundation/Foundation.h>

#include <SDL3/SDL.h>

#include "SimulatorOverlay.h"

extern "C" int CrossPointPrefs_rakingLight(void);
extern "C" void CrossPointRakingLight_perFrame(void);
extern "C" void CrossPointRakingLight_appWillResignActive(void);

namespace {

CMMotionManager *g_motion = nil;
int g_lastPref = -1;

// 30 Hz into a 0.3 s low-pass: fast enough that the light follows a wrist
// without visible stepping lag, slow enough that the per-frame hook reads a
// sample the manager already has. The quantizer's hysteresis, not this rate,
// is what keeps a still hand from re-lighting the page.
constexpr double kUpdateInterval = 1.0 / 30.0;

void startStream() {
  if (g_motion) return;
  g_motion = [[CMMotionManager alloc] init];
  if (!g_motion.deviceMotionAvailable) {
    SDL_Log("[raking] device motion unavailable -- the light stays fixed");
    g_motion = nil;
    return;
  }
  g_motion.deviceMotionUpdateInterval = kUpdateInterval;
  [g_motion startDeviceMotionUpdates];
  // The first sample after a start is the new neutral: the reader's pose now
  // is lit exactly as the page always was.
  SimulatorOverlay::resetRakingLightNeutral();
  SDL_Log("[raking] motion stream started");
}

void stopStream() {
  if (!g_motion) return;
  [g_motion stopDeviceMotionUpdates];
  g_motion = nil;
  SDL_Log("[raking] motion stream stopped");
}

}  // namespace

void CrossPointRakingLight_appWillResignActive(void) {
  // Backgrounded: no reason to hold the accelerometer, and the pose on return
  // is a new pose, so the neutral is recaptured when the stream restarts.
  stopStream();
}

void CrossPointRakingLight_perFrame(void) {
  // The Settings row, edge-triggered into the dial's setter -- the same poll
  // shape as every other row, kept here so the shim gains one call, not a
  // poll function.
  const int pref = CrossPointPrefs_rakingLight();
  if (pref != g_lastPref) {
    g_lastPref = pref;
    SimulatorOverlay::setRakingLight(pref != 0);
  }

  if (!SimulatorOverlay::rakingLightWanted()) {
    stopStream();
    return;
  }
  startStream();
  if (!g_motion) return;
  CMDeviceMotion *dm = g_motion.deviceMotion;
  if (!dm) return;  // not yet sampling
  SimulatorOverlay::setRakingLightGravity(static_cast<float>(dm.gravity.x),
                                          static_cast<float>(dm.gravity.y),
                                          static_cast<float>(dm.gravity.z),
                                          SDL_GetTicks());
}
