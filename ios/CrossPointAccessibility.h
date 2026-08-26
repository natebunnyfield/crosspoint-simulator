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

// Publish a page that RENDERED WITH NO CAPTURABLE TEXT -- a book's cover
// wrapper (an <img> and nothing else), a dropped illustration -- together with
// the words that truthfully describe it, or nothing at all.
//
// Owner ruling 2026-08-23: make the cover speak something. `utf8` comes from
// spokenpage::forPage (src/SpokenPageText.h), which is where the honesty rules
// live; an empty `utf8` means nothing true is known about this page, and this
// then behaves exactly as it always did -- no element, and iOS correctly
// reports that there is nothing to speak.
//
// NOT the same event as the reader leaving: the channel has always
// distinguished them (ReadAloudChannel::publish sets `cleared` only for
// publish(nullptr)), and a page still on screen keeps its element.
void CrossPointAccessibility_setFallbackPage(const char *utf8, unsigned len);

// True when what assistive technology can reach is no longer what it should be,
// so the adapter must re-push the page it is already holding. LEVEL-triggered
// and asked every frame: the firmware publishes a page once, when it renders
// one, and an e-ink reader can go minutes without rendering another -- so
// anything lost in between is invisible until the next page turn, and what the
// owner gets meanwhile is "No speakable content could be found on the screen"
// over a page that is on the glass.
//
// The decision is src/ReadAloudExposure.h, pure and host-tested
// (tests/readaloud_exposure_test.cpp), because every way it can be wrong is
// silent. Use the _textPage_ form for a page the adapter holds TEXT for: it
// additionally requires the per-line elements VoiceOver reads, which a textless
// page correctly does not have.
bool CrossPointAccessibility_exposureOutOfStep(void);
bool CrossPointAccessibility_textPageOutOfStep(void);

// True when elements are currently published. This used to be half the text
// page's self-heal condition; it is now one term inside
// CrossPointAccessibility_textPageOutOfStep() above, which is where it belongs
// -- a caller that had to remember to OR it in is exactly how the textless page
// ended up with a weaker heal than the text page. Kept exported because it
// answers "is the container vending anything" without deciding anything, which
// is what a probe wants.
bool CrossPointAccessibility_hasElements(void);

// Re-raise the container if SDL has added a view over it, or reinstall it if a
// wake tore the hierarchy down. Called every frame; a pointer compare when
// nothing has moved.
void CrossPointAccessibility_keepFront(void);

// A page turn was requested by an assistive technology (accessibilityScroll
// on the page view). The next publish posts PageScrolled instead of
// ScreenChanged, which is what tells continuous reading to keep going.
void CrossPointAccessibility_notePageTurnRequested(void);

// Diagnostic: one line answering every link of the Speak Screen chain at once
// -- assistive tech on, page held, rects held, panel geometry, page view
// installed, page view in the window, elements published. Throttled to changes
// of that shape. Called every frame from the read-aloud adapter's drain.
//
// `fallbackBytes` is the textless-page substitute the adapter is holding, and
// it is the link the 2026-08-23 cover ruling added: `page=0B rects=0 fb=0B` is
// a page nothing can name, `page=0B rects=0 fb=48B` is a cover that speaks.
void CrossPointAccessibility_logChain(unsigned pageBytes, unsigned rectCount,
                                      unsigned fallbackBytes);

// Diagnostic: log what an assistive technology would actually reach.
void CrossPointAccessibility_dumpTree(void);

// The reader left: drop the elements so assistive tech stops offering a page
// that is no longer on screen.
void CrossPointAccessibility_clear(void);
