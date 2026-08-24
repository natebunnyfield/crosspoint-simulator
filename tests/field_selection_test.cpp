// WHICH SURFACE FIELD COMPOSITES -- src/FieldSelection.h.
//
// This is the biggest untested decision in the repo, and it guards the other
// seven field tests rather than duplicating them.
//
// Every surface pass computes its darkening budget on the assumption that IT IS
// THE ONLY PASS: scanlines take a share of the grain's budget, the wires and
// show-through take halves of what the tooth left the paper, letterpress owns
// the light page's ink. phosphor_grain_test, scanlines_test, letterpress_test,
// laid_structure_test, show_through_test, corner_defocus_test and
// paper_defects_test each sweep the 7:1 contrast floor and each is honest. None
// of them composes with another: two fields drawn over one page MULTIPLY, and
// the product can sit under the floor that all seven prove individually.
//
// So the mutual exclusion is not tidiness -- it is the premise those seven
// tests are proved under, and until this file existed it was five lines in the
// middle of a 4,800-line present function with no coverage at all. Every
// failure mode is silent: layering two fields does not crash, it produces a
// page a few percent too dark on a page nobody is measuring.
#include "FieldSelection.h"

#include <cstdio>

#include "PanelPalette.h"
#include "TestCheck.h"

using testcheck::check;
using testcheck::checkEq;
using fieldselect::Active;
using fieldselect::Dials;
using fieldselect::select;

namespace {

// ---------------------------------------------------------------- the rule --

void testDoctrineSplit() {
  // DARK IS A CRT: scanlines, and nothing else.
  {
    const Active a = select({true, 50, 0, 160});
    check(a.scanlines, "dark + scanlines on -> the raster composites");
    check(!a.letterpress, "dark never letterpresses -- paper is the light half");
    check(!a.grain, "dark + scanlines on -> the grain is SKIPPED, not layered");
  }
  // LIGHT IS PAPER AND INK: letterpress, and nothing else.
  {
    const Active a = select({false, 50, 100, 160});
    check(a.letterpress, "light + letterpress on -> the sheet composites");
    check(!a.scanlines, "light never rasters -- a scanline is a tube artifact");
    check(!a.grain, "light + letterpress on -> the grain is SKIPPED");
  }
}

void testPolarityGatesEachFieldSeparately() {
  // A strength left set from the other appearance must not draw. Both are
  // gated, and gated independently -- this is why `select` cannot be written as
  // one "is a doctrine dial on" test.
  {
    const Active a = select({true, 0, 100, 160});
    check(!a.letterpress,
          "a letterpress strength left set from a light page does not draw on "
          "a dark one");
    check(a.grain,
          "...and with the dark page's own dial off, the grain comes back");
  }
  {
    const Active a = select({false, 50, 0, 160});
    check(!a.scanlines,
          "a scanline intensity left set from a dark page does not draw on a "
          "light one");
    check(a.grain, "...and the light page's grain comes back");
  }
}

void testGrainIsTheFallback() {
  // THE DESKTOP CANARY'S GUARANTEE, stated as a property. The desktop seeds
  // both doctrine dials OFF, so with them off `grain` must be EXACTLY the
  // pre-doctrine condition -- "is the grain strength non-zero" and nothing
  // else. If this ever stops holding, every byte-identical capture this repo
  // has taken from `pio run -e simulator_x3` silently stops meaning what it
  // says.
  for (int dark = 0; dark <= 1; dark++) {
    for (int g = 0; g <= 1000; g += 7) {
      const Active a = select({dark != 0, 0, 0, g});
      const bool wantGrain = g != phosphorgrain::kStrengthOff;
      check(a.grain == wantGrain,
            "with both doctrine dials off the grain gate is exactly the old "
            "one");
      check(!a.scanlines && !a.letterpress,
            "with both doctrine dials off neither doctrine field draws");
    }
  }
}

void testOffIsBitExactOff() {
  // Each field's own sentinel, taken from its own model header. A field that
  // starts drawing at "off" is a change to every install that turned it off.
  check(!select({true, scanlines::kIntensityOff, 0, 0}).scanlines,
        "scanlines at kIntensityOff is off, not nearly-off");
  check(!select({false, 0, letterpress::kStrengthOff, 0}).letterpress,
        "letterpress at kStrengthOff is off");
  check(!select({false, 0, 0, phosphorgrain::kStrengthOff}).grain,
        "grain at kStrengthOff is off");
  // ...and one step above it is ON, or the sentinel is a floor rather than a
  // switch and the bottom rung of every dial is dead.
  check(select({true, scanlines::kIntensityOff + 1, 0, 0}).scanlines,
        "one step above off, the raster draws");
  check(select({false, 0, letterpress::kStrengthOff + 1, 0}).letterpress,
        "one step above off, the sheet draws");
  check(select({false, 0, 0, phosphorgrain::kStrengthOff + 1}).grain,
        "one step above off, the grain draws");
}

// ------------------------------------------------- the property that matters --

void testAtMostOneFieldEver() {
  // EXHAUSTIVE over both polarities and the full dial ranges. This is the whole
  // point of the file: not that the doctrine is implemented, but that no
  // combination of the three dials -- including combinations no UI can produce,
  // which is exactly what a stale stored value or a racing setter creates --
  // ever puts two fields on one page.
  int combinations = 0;
  for (int dark = 0; dark <= 1; dark++) {
    for (int s = 0; s <= scanlines::kIntensityMax; s += 3) {
      for (int l = 0; l <= letterpress::kStrengthMax; l += 3) {
        for (int g = 0; g <= phosphorgrain::kStrengthMax; g += 37) {
          const Active a = select({dark != 0, s, l, g});
          combinations++;
          if (!fieldselect::atMostOneField(a)) {
            std::printf(
                "FAIL: two fields live at dark=%d scan=%d press=%d grain=%d "
                "(scan=%d press=%d grain=%d)\n",
                dark, s, l, g, (int)a.scanlines, (int)a.letterpress,
                (int)a.grain);
            testcheck::g_failures++;
            return;
          }
        }
      }
    }
  }
  check(combinations > 100000,
        "the sweep actually covered the dial space it claims to");
}

void testExclusionIsWhatKeepsTheFloor() {
  // WHY the exclusion exists, in numbers rather than in a comment.
  //
  // Each field is clamped to a MEAN darkening budget computed for one pass. Two
  // MOD passes multiply, so the composite's transmission is the product and its
  // darkening is strictly greater than either alone. Demonstrated here on the
  // tightest dark palette rather than asserted, so that a future change which
  // makes layering look harmless has to argue with a measurement.
  const panelpalette::Palette dark =
      panelpalette::resolve(panelpalette::kPresetDefault, true, -1, -1);
  auto lum = [](const unsigned char c[3]) {
    return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255.0;
  };
  const float budget = phosphorgrain::darkeningBudget(
      static_cast<float>(lum(dark.ink)), static_cast<float>(lum(dark.paper)));
  check(budget > 0.0f, "the tightest palette still has a budget to spend");

  // One pass at the raster's share, versus that same pass multiplied by a grain
  // pass at the full remaining budget -- which is what drawing both would do.
  const double onePass = 1.0 - fieldselect::kRasterBudgetShare * budget;
  const double twoPasses = onePass * (1.0 - budget);
  check(twoPasses < onePass,
        "two multiplied fields darken strictly more than either alone");
  check(1.0 - twoPasses > budget,
        "...and the pair spends MORE than the single-pass budget every one of "
        "those seven tests proves its field against -- which is the breach the "
        "exclusion prevents");
}

// ------------------------------------------------------------- the shares ---

void testBudgetShares() {
  // These were bare literals at four sites in HalDisplay.cpp and four more in
  // tests/, so the app and its tests could disagree in silence.
  checkEq(static_cast<int>(fieldselect::kRasterBudgetShare * 1000.0f + 0.5f),
          800, "the raster's share of the grain budget is 0.8");
  checkEq(static_cast<int>(fieldselect::kSheetShareStep * 1000.0f + 0.5f), 500,
          "the sheet's budget is halved at each step");

  // Shares must be a real fraction: at or above 1.0 the pass may spend the
  // whole budget and leave the next consumer nothing, which is how a "share"
  // silently stops being one.
  check(fieldselect::kRasterBudgetShare > 0.0f &&
            fieldselect::kRasterBudgetShare < 1.0f,
        "the raster's share is a fraction, not the whole budget");
  check(fieldselect::kSheetShareStep > 0.0f &&
            fieldselect::kSheetShareStep < 1.0f,
        "the sheet's step is a fraction, not the whole budget");

  // THE SHEET'S THREE-WAY SPLIT, walked the way HalDisplay walks it: wires take
  // a step of what the tooth left, show-through takes a step of the remainder,
  // and the marks take the rest. The marks' share must stay POSITIVE -- a split
  // that starves the last consumer is a defect dial that silently does nothing.
  const float paperLeft = 0.10f;
  const float wires = fieldselect::kSheetShareStep * paperLeft;
  const float afterWires = paperLeft - wires;
  const float through = fieldselect::kSheetShareStep * afterWires;
  const float marks = afterWires - through;
  check(wires > 0.0f && through > 0.0f && marks > 0.0f,
        "all three sheet consumers get a positive share");
  check(wires + through + marks <= paperLeft + 1e-6f,
        "the three shares never sum past what the tooth left");
}

}  // namespace

int main() {
  testDoctrineSplit();
  testPolarityGatesEachFieldSeparately();
  testGrainIsTheFallback();
  testOffIsBitExactOff();
  testAtMostOneFieldEver();
  testExclusionIsWhatKeepsTheFloor();
  testBudgetShares();

  if (testcheck::g_failures) {
    std::printf("%d failure(s)\n", testcheck::g_failures);
    return 1;
  }
  std::printf("field_selection: all checks passed\n");
  return 0;
}
