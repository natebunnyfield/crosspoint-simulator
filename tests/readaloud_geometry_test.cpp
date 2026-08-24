// Where a published page lands on the glass (src/ReadAloudGeometry.h).
//
// Every failure mode here is SILENT: the text is right, nothing logs, nothing
// crashes, and the only symptom is an assistive technology skipping elements it
// believes are off-screen -- which surfaces as "No speakable content could be
// found on the screen" over a page that is published, correct and on screen.
// That message has now cost two investigations, so the arithmetic gets a
// known-answer test with the phone's real numbers in it.

#include "ReadAloudGeometry.h"

#include <cmath>
#include <cstdio>
#include <initializer_list>
#include <cstdlib>
#include "TestCheck.h"
using testcheck::check;

static int &g_failures = testcheck::g_failures;

static void checkNear(double got, double want, double tol, const char *what) {
  if (std::fabs(got - want) > tol) {
    std::printf("FAIL: %s -- got %.6f, want %.6f\n", what, got, want);
    g_failures++;
  }
}

int main() {
  using readaloud::PanelGeometryPts;
  using readaloud::panelGeometryPts;

  // ---- 1. Not answerable before the first present -------------------------
  //
  // The container's self-heal is LEVEL-triggered off exactly this: a rebuild
  // that races the first frame must report "not yet" rather than a plausible
  // zero, or it clears the retry and nothing tries again until the next page
  // turn -- the reported shape of "Speak Screen sometimes needs a page turn
  // before it works".
  {
    PanelGeometryPts g;
    check(!panelGeometryPts(0, 0, 0, 0, 528, 3.0, &g), "zero panel is not answerable");
    check(!panelGeometryPts(102, 1980, 0, 1584, 528, 3.0, &g), "zero width is not answerable");
    check(!panelGeometryPts(102, 1980, 1056, 0, 528, 3.0, &g), "zero height is not answerable");
    check(!panelGeometryPts(102, 1980, 1056, 1584, 0, 3.0, &g),
          "zero logical height is not answerable");
    check(!panelGeometryPts(102, 1980, 1056, 1584, 528, 3.0, nullptr), "null out is refused");
  }

  // ---- 2. The iPhone Air, X3, measured 2026-08-23 -------------------------
  //
  // From a live run: [zen] panel 1056x1584 at 102,396 on a 1260x2736 px screen
  // at scale 3. The container logged frame=(34,132 352x528) pt and the AX
  // runtime served exactly that. These are those numbers.
  {
    PanelGeometryPts g;
    check(panelGeometryPts(/*left*/ 102, /*bottom*/ 396 + 1584, /*w*/ 1056, /*h*/ 1584,
                           /*logicalHeight*/ 528, /*screenScale*/ 3.0, &g),
          "the presented panel is answerable");
    checkNear(g.x0, 34.0, 1e-9, "x0 is the panel's left edge in points");
    checkNear(g.y0, 132.0, 1e-9, "y0 is the panel's TOP edge in points");
    checkNear(g.scale, 2.0 / 3.0, 1e-9, "one logical panel px is 2/3 pt at 2x render, 3x screen");

    // The whole page must map to exactly the panel's on-screen box. A logical
    // rect spanning the portrait width (LOGICAL_HEIGHT) and the portrait
    // height (LOGICAL_WIDTH) is the page; if this does not land on the panel,
    // every element inside it is displaced by the same error.
    checkNear(528 * g.scale, 1056 / 3.0, 1e-9, "the page's width fills the panel's width");
    checkNear(792 * g.scale, 1584 / 3.0, 1e-9, "the page's height fills the panel's height");
  }

  // ---- 3. The render scale must NOT appear in the answer -------------------
  //
  // iOS has shipped 1x, 2x and 3x within a fortnight, and 3x was retired on
  // 2026-08-23. The scale is derived from the PRESENTED width, so the same
  // page presented at the same size answers identically whatever the
  // framebuffer behind it was. Using DISPLAY_HEIGHT (which carries
  // CROSSPOINT_RENDER_SCALE) instead of LOGICAL_HEIGHT is the mistake this
  // pins: it once put the read-aloud highlight at half size on the phone.
  {
    // The render scale is not an input at all -- that IS the design, and this
    // states it as an assertion rather than a comment: the presented rect and
    // the LOGICAL unit are the whole answer. Passing DISPLAY_HEIGHT (the
    // logical height times CROSSPOINT_RENDER_SCALE) is therefore the one way
    // to get this wrong, so each shipped render scale is checked to produce a
    // visibly different, wrong answer.
    PanelGeometryPts right;
    check(panelGeometryPts(102, 1980, 1056, 1584, 528, 3.0, &right), "answerable in logical px");
    for (int renderScale : {2, 3}) {
      PanelGeometryPts wrong;
      check(panelGeometryPts(102, 1980, 1056, 1584, 528 * renderScale, 3.0, &wrong),
            "answerable with DISPLAY_HEIGHT");
      checkNear(wrong.scale, right.scale / renderScale, 1e-9,
                "DISPLAY_HEIGHT divides the scale by the render scale");
      check(std::fabs(wrong.scale - right.scale) > 0.3,
            "and the difference is large enough that a frame check catches it");
    }
  }

  // ---- 4. bottom is an EDGE, not an origin --------------------------------
  //
  // SimulatorOverlay publishes panelBottomPx as y + h. Reading it as the
  // origin puts the page a whole panel below itself, which on a phone is
  // entirely off the bottom of the screen -- the off-screen-frames case the
  // container still carries a warning for.
  {
    PanelGeometryPts g;
    check(panelGeometryPts(0, 1584, 1056, 1584, 528, 1.0, &g), "top-aligned panel is answerable");
    checkNear(g.y0, 0.0, 1e-9, "a panel whose bottom edge is its own height starts at y=0");
  }

  // ---- 5. A screen that reports no scale is a 1x screen -------------------
  //
  // Not a divide by zero, and not a NaN frame: UIScreen.scale has been seen
  // as 0 on a window that is not yet in a scene, and a NaN accessibilityFrame
  // is skipped by every assistive technology without a word.
  {
    PanelGeometryPts g;
    check(panelGeometryPts(102, 1980, 1056, 1584, 528, 0.0, &g), "a scale-less screen is answerable");
    checkNear(g.scale, 2.0, 1e-9, "no reported scale means 1x");
    checkNear(g.x0, 102.0, 1e-9, "points are device pixels at 1x");
    check(!std::isnan(g.x0) && !std::isnan(g.y0) && !std::isnan(g.scale), "no NaN escapes");
    check(panelGeometryPts(102, 1980, 1056, 1584, 528, -2.0, &g), "a negative scale is answerable");
    checkNear(g.scale, 2.0, 1e-9, "a negative reported scale also means 1x");
  }

  // ---- 6. The scale is strictly positive whenever the call succeeds -------
  //
  // A zero scale collapses every element frame to a point at the panel's
  // origin. Assistive tech reports that as no content.
  {
    const int widths[] = {1, 264, 528, 1056, 1584};
    const int screenScales[] = {1, 2, 3};
    for (int w : widths) {
      for (int ss : screenScales) {
        PanelGeometryPts g;
        check(panelGeometryPts(0, 100, w, 100, 528, ss, &g), "answerable");
        check(g.scale > 0, "the scale is never zero when the call succeeds");
      }
    }
  }

  if (g_failures == 0) {
    std::printf("readaloud_geometry_test: all checks passed\n");
    return 0;
  }
  std::printf("readaloud_geometry_test: %d FAILURE(S)\n", g_failures);
  return 1;
}
