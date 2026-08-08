#pragma once

// The page, exposed to iOS assistive technology (ST-004).
//
// The panel is one opaque GPU texture: to UIKit it is a single view with no
// text in it, so VoiceOver, Speak Screen, Braille displays and Switch Control
// all see nothing at all. This publishes the SAME page the read-aloud channel
// already carries as UIAccessibilityElements, which is what those technologies
// read.
//
// NOT a second channel consumer -- the contract is one per build. The read-aloud
// adapter owns the drain and hands the page here (CrossPointReadAloud.mm), so
// there is exactly one reader of HalGPIO's channel on iOS.
//
// Elements are per LINE, not per word. Speak Screen reads elements in order and
// concatenates them; per-word elements would produce a pause after every word.
// A line is the natural unit for reading aloud and a reasonable one for
// VoiceOver's swipe-to-next.
//
// Read-aloud (the app's own speech, with highlight and tap-to-start) is a
// SEPARATE feature behind its own default-off toggle. This is deliberately
// independent: an owner running VoiceOver gets the page whether or not they
// have turned read-aloud on.

#include <vector>

#include "ReadAloudChannel.h"

// Install the accessibility container over the SDL view. Idempotent across
// deep-sleep wakes, same contract as the other harness begins. Main thread.
void CrossPointAccessibility_begin(void);

// True when an assistive technology that reads the screen is running, so the
// firmware's page capture is worth paying for. The read-aloud adapter ORs this
// with its own toggle when it sets setReadAloudCaptureWanted().
bool CrossPointAccessibility_wantsPage(void);

// Publish the current page. Called by the read-aloud adapter's drain, on the
// main thread, with the page it just took off the channel.
void CrossPointAccessibility_setPage(const char *utf8, unsigned len,
                                     const ReadAloudWordRect *rects,
                                     unsigned rectCount);

// The reader left: drop the elements so assistive tech stops offering a page
// that is no longer on screen.
void CrossPointAccessibility_clear(void);
