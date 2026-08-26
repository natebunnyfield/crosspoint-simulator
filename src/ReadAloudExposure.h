#pragma once

// IS WHAT ASSISTIVE TECHNOLOGY CAN REACH STILL WHAT IT SHOULD BE?
//
// The Speak Screen chain (docs/speak-screen-chain.md) ends in two objects that
// live in the UIKit hierarchy: the `CPAccessibilityOverlay` container that
// vends the per-line elements, and the `CPPageTextInputView` that adopts
// `UITextInput` in its entirety -- the one thing Speak Screen consumes. The
// firmware publishes a page ONCE, when it renders it, and an e-ink reader can
// go minutes without rendering another. So anything that loses either object
// between two page turns is invisible until the next one, and what the owner
// sees in the meantime is "No speakable content could be found on the screen"
// over a perfectly good page.
//
// That is why the check is LEVEL-triggered rather than edge-triggered (owner
// report 2026-08-09, "Speak Screen sometimes needs a page turn before it
// works"). This header is the level: it asks "does the world match what it
// should be", every frame, from the state the harness can see -- and the
// harness re-pushes the page it is already holding whenever the answer is no.
//
// WHY IT IS A PURE HEADER AND NOT AN `if` IN THE .mm
//
// The same argument as HostKeyboardState.h and SpokenPageText.h beside it, and
// it has already been paid for once here. Every failure mode of this predicate
// is SILENT: nothing crashes, nothing renders differently, no compiler sees it,
// and the symptom arrives on someone else's phone as a sentence spoken by iOS.
// `ios/CrossPointAccessibility.mm` cannot be compiled anywhere but a Mac and
// cannot be single-stepped on a device, so the decision is moved somewhere a
// host test can enumerate every state in microseconds. The three defects the
// tests below pin were all found by reading, all three were one term of one
// boolean, and all three had passed every measurement ever taken of this chain
// -- see the notes on each.

namespace readaloud {

// Everything the harness knows about the exposure at this instant. All of it is
// a question the UIKit side can answer with a pointer compare.
struct ExposureState {
  // Speak Screen, VoiceOver or Switch Control is on (or a QA run forces it).
  // The page view exists only when this is true; the per-line elements are
  // built either way.
  bool wantsPage = false;
  // The container object is alive AND in the window. It is held by a __weak
  // pointer whose only strong reference is its superview, so "alive" and "in
  // the window" are the same fact: the instant the window drops it, the
  // pointer reads nil.
  bool containerInstalled = false;
  // Likewise for the page view, whose strong owner is the host view.
  bool pageViewExists = false;
  // ...and whether that host is still in a window. NOT implied by the above: a
  // host view that has itself been detached (a wake that rebuilds SDL's view)
  // can go on retaining the page view, so the pointer stays non-nil while
  // nothing on screen can reach it.
  bool pageViewInWindow = false;
  // Which mode the CURRENT elements were built in: -1 nothing has been built
  // yet, 0 built without a page view, 1 built with one.
  int builtMode = -1;
  // The container is vending at least one per-line element.
  bool containerHasElements = false;
};

// TRUE when the exposure has to be rebuilt from the page the harness holds.
//
// Read the terms in order; each one is a defect that shipped.
inline bool exposureOutOfStep(const ExposureState &s) {
  // 1. NOTHING WAS EVER PUSHED. `builtMode < 0` used to return FALSE here --
  //    "nothing has been built, so nothing can be stale" -- and that reading is
  //    wrong in the one case it decides. Both push paths bail out early when
  //    the container is not installed yet, so a page published before the
  //    container exists is DROPPED and leaves builtMode at -1. The text page
  //    survived that by accident, because its caller also retries on an empty
  //    container; the TEXTLESS page (a book's cover, which is the page every
  //    book opens on) has no elements by design, so an empty container is its
  //    normal state and cannot be its retry condition. `modeChanged()` was its
  //    only retry, and it answered "nothing to do" forever. The cover then sat
  //    there vending nothing -- which is the precise symptom the cover fallback
  //    was written to end (owner ruling 2026-08-23).
  if (s.builtMode < 0) return true;
  // 2. THE CONTAINER IS GONE. Same case, later: something removed it after a
  //    successful build. Nothing else in the harness will notice, because every
  //    push path returns early on a missing container rather than recreating
  //    one.
  if (!s.containerInstalled) return true;
  // 3. THE MODE MOVED under a page that is already on screen -- Speak Screen
  //    switched on while the reader sat on one page. This is the original 2026-
  //    08-09 term and it is unchanged.
  if (s.wantsPage != s.pageViewExists) return true;
  if (s.wantsPage != (s.builtMode == 1)) return true;
  // 4. THE PAGE VIEW EXISTS BUT NOTHING CAN REACH IT. The check above asks
  //    whether a page view OBJECT exists, which is not the same question --
  //    a view retained by a detached host answers yes and is unreachable from
  //    the window, so assistive technology traverses the hierarchy and finds
  //    nothing while every log line says the view is there. This is the shape
  //    the CHAIN line prints as `view=1 ... inWindow=0`.
  if (s.wantsPage && !s.pageViewInWindow) return true;
  return false;
}

// The same question for a page the harness holds TEXT for. Its container must
// also be vending the per-line elements VoiceOver reads; a textless page has
// none by design and must not be asked this.
inline bool textPageOutOfStep(const ExposureState &s) {
  return !s.containerHasElements || exposureOutOfStep(s);
}

}  // namespace readaloud
