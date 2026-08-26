// Whether the Speak Screen exposure has to be rebuilt (src/ReadAloudExposure.h).
//
// The predicate is a level check that runs every frame and re-pushes the page
// the harness already holds whenever the answer is yes. Every one of its
// failure modes is SILENT -- the page is captured, the text is right, nothing
// logs and nothing crashes -- and the symptom is iOS saying "No speakable
// content could be found on the screen" over a page that is on the glass.
//
// The three cases marked REGRESSION below each fail against the boolean this
// header replaced (`ios/CrossPointAccessibility.mm`'s modeChanged, which read:
//   if (builtMode < 0) return false;
//   if (wants != pageViewExists) return true;
//   return wants != (builtMode == 1);
// ) and each was found by reading the path rather than by any measurement --
// all three survived a full simulator sweep and Apple's own out-of-process AX
// probe, because none of them is reachable from a healthy launch.

#include "ReadAloudExposure.h"

#include <cstdio>
#include "TestCheck.h"
using testcheck::check;

using readaloud::ExposureState;
using readaloud::exposureOutOfStep;
using readaloud::textPageOutOfStep;

// A healthy reader showing a page of prose with Speak Screen on.
static ExposureState healthy() {
  ExposureState s;
  s.wantsPage = true;
  s.containerInstalled = true;
  s.pageViewExists = true;
  s.pageViewInWindow = true;
  s.builtMode = 1;
  s.containerHasElements = true;
  return s;
}

// A healthy TEXTLESS page -- a book's cover. No line elements by design (owner
// ruling 2026-08-23: VoiceOver's blank page stays byte-identical), so the page
// view carries the book's name and the container carries nothing.
static ExposureState healthyCover() {
  ExposureState s = healthy();
  s.containerHasElements = false;
  return s;
}

int main() {
  // ---- 1. A healthy exposure is left alone -------------------------------
  //
  // The most important assertion in the file. This predicate runs on every
  // frame, and a rebuild re-adds a subview and posts a screen-changed
  // notification -- so a false positive here is not a wasted branch, it is a
  // notification storm at the display rate aimed at the assistive technology
  // this whole chain exists to serve.
  check(!exposureOutOfStep(healthy()), "a healthy page is not rebuilt");
  check(!textPageOutOfStep(healthy()), "a healthy text page is not rebuilt");
  check(!exposureOutOfStep(healthyCover()), "a healthy cover is not rebuilt");

  // ---- 2. REGRESSION: a page published before the container existed -------
  //
  // Both push paths return early when the container is not installed, so the
  // page is dropped and builtMode stays at -1. The old predicate read that as
  // "nothing built, nothing stale" and returned false.
  //
  // The TEXT page survived it by accident: its caller also retries on an empty
  // container. The COVER cannot -- an empty container is its correct steady
  // state -- so the fallback was never pushed and the cover vended nothing for
  // the rest of the session. That is precisely the symptom the cover fallback
  // was written to end.
  {
    ExposureState s = healthy();
    s.builtMode = -1;
    s.pageViewExists = false;
    s.containerHasElements = false;
    check(exposureOutOfStep(s), "REGRESSION: a never-built exposure retries");
  }
  {
    ExposureState s = healthyCover();
    s.builtMode = -1;
    s.pageViewExists = false;
    check(exposureOutOfStep(s),
          "REGRESSION: a cover whose fallback was dropped retries");
  }
  // ...and it must still retry once the container arrives but before anything
  // has been pushed into it, which is the frame the whole self-heal exists for.
  {
    ExposureState s = healthyCover();
    s.builtMode = -1;
    s.pageViewExists = false;
    s.pageViewInWindow = false;
    s.containerInstalled = true;
    check(exposureOutOfStep(s), "a container with nothing in it yet retries");
  }

  // ---- 3. REGRESSION: the container was lost after a good build -----------
  //
  // It is held by a __weak pointer whose only strong reference is its
  // superview, so a window that drops it makes the pointer read nil. Every push
  // path returns early on a missing container rather than recreating one, so
  // nothing else in the harness notices.
  {
    ExposureState s = healthy();
    s.containerInstalled = false;
    check(exposureOutOfStep(s), "REGRESSION: a lost container is reinstalled");
  }

  // ---- 4. REGRESSION: the page view exists but is unreachable -------------
  //
  // "Does a page view object exist" is not "can anything reach it". A view
  // retained by a host that has itself been detached answers yes to the first
  // and no to the second, and assistive technology traversing from the window
  // finds nothing while every log line says the view is there. The CHAIN line
  // prints this as `view=1 ... inWindow=0`.
  {
    ExposureState s = healthy();
    s.pageViewInWindow = false;
    check(exposureOutOfStep(s), "REGRESSION: a detached page view is rebuilt");
  }
  {
    ExposureState s = healthyCover();
    s.pageViewInWindow = false;
    check(exposureOutOfStep(s), "REGRESSION: a detached cover page view is rebuilt");
  }

  // ---- 5. The original 2026-08-09 terms still hold ------------------------
  //
  // Speak Screen switched ON while the reader sat on one page: the elements
  // were built without a page view and the firmware will not publish another
  // until the owner turns a page.
  {
    ExposureState s = healthy();
    s.wantsPage = true;
    s.pageViewExists = false;
    s.pageViewInWindow = false;
    s.builtMode = 0;
    check(exposureOutOfStep(s), "assistive tech switched on mid-page rebuilds");
  }
  // ...and OFF, where the page view has to go: leaving it would put a whole-page
  // element in VoiceOver's path, re-reading a page the per-line elements
  // already cover.
  {
    ExposureState s = healthy();
    s.wantsPage = false;
    check(exposureOutOfStep(s), "assistive tech switched off mid-page rebuilds");
  }

  // ---- 6. With nothing wanted, the page view's reachability is moot -------
  //
  // A build with wantsPage false has no page view at all, so asking whether it
  // is in a window must not force an endless rebuild on every ordinary frame of
  // a VoiceOver-only session.
  {
    ExposureState s;
    s.wantsPage = false;
    s.containerInstalled = true;
    s.pageViewExists = false;
    s.pageViewInWindow = false;
    s.builtMode = 0;
    s.containerHasElements = true;
    check(!exposureOutOfStep(s), "a VoiceOver-only build is steady");
    check(!textPageOutOfStep(s), "a VoiceOver-only text page is steady");
  }

  // ---- 7. A text page with an empty container is always out of step -------
  //
  // The term that saved the text path from case 2. It belongs to the TEXT
  // predicate only: a cover has no elements and must not be rebuilt forever.
  {
    ExposureState s = healthy();
    s.containerHasElements = false;
    check(textPageOutOfStep(s), "a text page with no elements is rebuilt");
    check(!exposureOutOfStep(s), "...but that alone is not a cover's problem");
  }

  if (testcheck::g_failures == 0) std::printf("readaloud_exposure: all passed\n");
  return testcheck::g_failures == 0 ? 0 : 1;
}
