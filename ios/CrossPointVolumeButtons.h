#pragma once

// The hardware volume rocker as the firmware's page rocker: a volume-up press
// is the front RIGHT button (next page), volume-down the front LEFT (previous
// page), behind a Settings.app toggle that ships OFF. The decision half is
// ios/VolumePageTurn.h (pure, host-tested); this adapter is the platform half:
// the AVAudioSession KVO observer, the offscreen MPVolumeView that puts the
// level back, and the per-frame pump that injects the press.
//
// Declared with plain C linkage so CrossPointIOSShim.cpp can call into it
// without dragging AVFoundation and MediaPlayer into the shared build. ALL
// entry points are main thread only, like CrossPointReadAloud.h.

#ifdef __cplusplus
extern "C" {
#endif

// The in-process reboot boundary, called from CrossPointHarness_begin BEFORE
// _begin re-seeds; a no-op on the first boot. Drops rocker presses queued
// while the firmware was asleep (a press during sleep must not turn a page
// in the boot that wakes) and re-baselines against the level the phone is
// actually at now.
void CrossPointVolumeButtons_resetForReboot(void);

// Idempotent across deep-sleep wakes, same contract as CrossPointHarness_begin
// (which calls it). Nothing is armed here: the observer follows the setting
// and the app's foreground state from _perFrame, so a wake simply re-evaluates.
void CrossPointVolumeButtons_begin(void);

// The per-frame pump, called from CrossPointHarness_perFrame: arms the
// observer on the edge of (setting ON and app active), disarms it on the
// other edge, and drains the KVO queue into gpio.queueButtonTap. Cheap when
// off -- one pref read.
void CrossPointVolumeButtons_perFrame(void);

// The app is leaving the foreground (padWatch's SDL_EVENT_WILL_ENTER_BACKGROUND
// case, which SDL raises from applicationWillResignActive). Tears the observer
// down NOW rather than on the next frame, because the next frame may never
// come: without read-aloud holding an audio session the process is suspended
// shortly after. _perFrame re-arms on return once the app is active again.
void CrossPointVolumeButtons_appWillResignActive(void);

// Read-aloud has just handed the audio session back
// (CrossPointReadAloud.mm's releaseAudioSessionWhenIdle). The observer only
// receives outputVolume changes while SOME session is active, so if the
// rocker is armed it takes the session again here, under its own category.
// A no-op unless armed.
void CrossPointVolumeButtons_audioSessionReleased(void);

#ifdef __cplusplus
}
#endif
