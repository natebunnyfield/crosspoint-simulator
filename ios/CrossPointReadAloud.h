#pragma once

// Read-aloud TTS: Apple speech (AVSpeechSynthesizer) speaking the page the
// firmware publishes over HalGPIO's read-aloud channel, with a per-word
// highlight and tap-to-start. The decision logic lives in ReadAloudCore
// (pure, host-tested); this adapter translates between it and the platform
// and holds no decision state of its own. See .claude/PLAN-tts-read-aloud.md.
//
// Declared with plain C linkage so CrossPointIOSShim.cpp can call into it
// without dragging AVFoundation into the shared build. ALL entry points are
// main thread only.

struct SDL_Renderer;

#ifdef __cplusplus
extern "C" {
#endif

// Create the synthesizer and delegate. Idempotent across deep-sleep wakes,
// same contract as CrossPointHarness_begin (which calls it).
void CrossPointReadAloud_begin(void);

// The per-frame pump, called from CrossPointHarness_perFrame: applies the
// Settings toggle on its edge, drains the page channel and the speech
// delegate's event queue into ReadAloudCore, and applies the resulting
// actions. Cheap when idle — a pref read and three empty-queue checks.
void CrossPointReadAloud_perFrame(void);

// Paint the active word highlight, called from the pad's overlay painter
// (SimulatorOverlay holds a single draw callback). No-op unless a word is
// highlighted. `dark` selects the appearance-matched wash.
void CrossPointReadAloud_paintHighlight(struct SDL_Renderer *r, int outWidthPx,
                                        int outHeightPx, int dark);

// A completed tap (down + up, no drag) at device-pixel screen coordinates,
// from padWatch. The adapter maps it into logical panel coordinates and
// starts (or jumps) reading at the tapped word; taps outside the panel or
// off any word do nothing. A tap on the word BEING SPOKEN stops reading —
// the only finger-reachable stop, and the reason a second tap is not simply
// another jump.
void CrossPointReadAloud_tapAtScreen(float xPx, float yPx);

// The system play/pause gesture. Returns 1 if it was consumed, 0 if there
// was nothing to toggle — which is what the caller returns from
// accessibilityPerformMagicTap so the system can look elsewhere.
//
// The adapter installs that handler itself, on the application delegate,
// which is where UIKit looks last and therefore the one place that catches
// the gesture wherever it started. This entry point is public anyway because
// the QA hook below drives it, and because a future in-app control (a
// headphone button, a lock-screen transport) wants the same door.
//
// Main thread only, like everything here.
int CrossPointReadAloud_magicTap(void);

#ifdef __cplusplus
}
#endif
