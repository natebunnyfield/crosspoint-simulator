// Host test for THE WHOLE COMPOSITE -- docs/surface-roadmap.md section 8.
//
// Eleven surface passes exist now, each with its own dial and each proved
// against the 7:1 contrast floor by its own test: phosphor_grain, scanlines,
// letterpress, laid_structure, show_through, corner_defocus, paper_defects,
// light_ink (the frozen-sheet sweep), field_selection (the mutual-exclusion
// property itself). Every one of those proofs is honest and every one of them
// assumes IT IS THE ONLY PASS SPENDING THE PAPER'S BUDGET. Nothing before this
// file walked every dial to its maximum AT ONCE, through fieldselect::select
// and the real budget-sharing chain SurfaceSheet.cpp actually calls
// (src/SurfaceSheet.cpp ~596-722), and asked whether the composite still
// clears the floor. "Individually safe and jointly over" is the exact failure
// the defect layer (paperdefects::remainingBudget) was written to rescue the
// sheet from once already; this is the test that catches the NEXT pass that
// gets the composition wrong, per the roadmap doc's own argument for writing
// it.
//
// SCOPE, deliberately narrow: this sweeps testpalettes.h's shipped PAGES (ink
// + paper as the panel actually resolves them), not the full ink x paper
// stock grid -- that grid, and the frozen tooth/formation/drift floor on it,
// is light_ink_test.cpp's job and already exhaustive. What this file adds is
// the layers light_ink_test does NOT include: the wires, the show-through and
// the defects, stacked on top of the tooth and formation, all at their
// dial-defined maxima, with fieldselect::select() deciding what is live
// rather than the test hand-assembling a combination the code cannot
// actually produce.
//
// WHY THE BUDGET CALLS AND NOT A FULL RASTER. Every consumer past the tooth
// (laidstructure::meanDarkeningBound, showthrough::meanDarkeningBound,
// paperdefects::meanDarkeningBound) is itself an analytic, structurally
// enforced upper bound on what that pass can spend of the share it is handed
// -- that is what "budget" means in this codebase, and it is what each of
// those passes' own test proves individually. This file sums those same
// calls, in the same order production spends them, and separately measures
// the tooth+formation mean through the real per-pixel entry point
// (letterpress::sheetToothMultiplierAt) the way letterpress_test's own
// frozen-sheet block does. If any pass ever stopped honoring its declared
// share, this is the test that would catch the sum exceeding paperBudget()
// even though every pass still passes alone.

#include <cmath>
#include <cstdint>
#include <cstdio>

#include "ContrastFloor.h"
#include "FieldSelection.h"
#include "LaidStructure.h"
#include "Letterpress.h"
#include "LightInkPalette.h"
#include "PaperDefects.h"
#include "PhosphorGrain.h"
#include "Scanlines.h"
#include "ShowThrough.h"
#include "TestPalettes.h"

#include "TestCheck.h"
using testcheck::check;

static int &failures = testcheck::g_failures;

namespace {

constexpr int W = 64, H = 64;

float lum(int r, int g, int b) {
  auto ch = [](int v) {
    const float f = v / 255.0f;
    return f <= 0.04045f ? f / 12.92f : std::pow((f + 0.055f) / 1.055f, 2.4f);
  };
  return 0.2126f * ch(r) + 0.7152f * ch(g) + 0.0722f * ch(b);
}

// The worst-case stock multipliers, SCANNED across the real paper table
// rather than named by hand -- a future row moves this ceiling the same way
// TestPalettes.h moves the palette ceiling, instead of silently under-testing
// it. All three ride lightink::kPaperStrengthMax, the paper-strength dial's
// own ceiling.
float worstToothScale() {
  float worst = 0.0f;
  for (int i = 0; i < lightink::kPaperCount; ++i) {
    const float s = lightink::toothScaleFor(i, lightink::kPaperStrengthMax);
    if (s > worst) worst = s;
  }
  return worst;
}

float worstShowThroughScale() {
  float worst = 0.0f;
  for (int i = 0; i < lightink::kPaperCount; ++i) {
    const float s =
        lightink::showThroughScaleFor(i, lightink::kPaperStrengthMax);
    if (s > worst) worst = s;
  }
  return worst;
}

// --- LIGHT: letterpress panel/tooth + formation + wires + show-through + ---
// --- defects, all pinned to their maximum, stacked the way SurfaceSheet.cpp
// --- stacks them -------------------------------------------------------
void testLightCompositionHoldsTheFloor() {
  const float toothScaleMax = worstToothScale();
  const float showThroughScaleMax = worstShowThroughScale();

  for (const auto &page : testpalettes::kLightSweep) {
    // Let the SELECTOR decide what is live -- the property under test is
    // that pinning every dial cannot make two doctrine fields draw at once,
    // not an assumption that letterpress is the only thing pinned.
    fieldselect::Dials dials;
    dials.dark = false;
    dials.scanlinesIntensity = scanlines::kIntensityMax;   // left set from a
    dials.grainStrength = phosphorgrain::kStrengthMax;     // dark page; must
                                                             // not draw here
    dials.letterpressStrength = letterpress::kStrengthMax;
    const fieldselect::Active active = fieldselect::select(dials);
    check(active.letterpress && !active.scanlines && !active.grain,
          "light palette selects letterpress only, per fieldselect::select, "
          "even with the other two dials left pinned to their maxima");
    if (!active.letterpress) continue;

    // Drift at the top of its range, applied to the PAPER only -- the same
    // worst-leaf construction light_ink_test's frozen-sheet block uses. The
    // wash does not drift; only the ground does (docs/surface-roadmap.md
    // 1c). paperWorstDriftForPair, not paperWorstDrift: kLightSweep's pages
    // are panelpalette::resolve() bytes -- a NAMED PRESET, exactly the path
    // that never passes through LightInkPalette.h's density/strength floor
    // clamps -- so this is the same budget-clamped bound
    // HalDisplay.cpp::livePanelPalette now actually renders
    // (docs/composition-test-2026-08-29.md), not the raw dial maximum.
    const uint8_t inkBytes[3] = {static_cast<uint8_t>(page.r),
                                  static_cast<uint8_t>(page.g),
                                  static_cast<uint8_t>(page.b)};
    const uint8_t paperBytes[3] = {static_cast<uint8_t>(page.pr),
                                    static_cast<uint8_t>(page.pg),
                                    static_cast<uint8_t>(page.pb)};
    uint8_t leaf[3];
    lightink::paperWorstDriftForPair(inkBytes, paperBytes,
                                     lightink::kPaperDriftMax, leaf);
    const float inkLum = lum(page.r, page.g, page.b);
    const float paperLum = lum(leaf[0], leaf[1], leaf[2]);

    letterpress::Params lp;
    lp.strengthPercent = letterpress::kStrengthMax;
    lp.paperDarkenBudget = letterpress::paperBudget(inkLum, paperLum);
    lp.toothScale = toothScaleMax;
    lp.formationDepth = letterpress::kFormationDepthMax;
    lp.includeTooth = false;  // production draws tooth in the SHEET pass

    // 1. TOOTH + FORMATION -- measured through the real entry point, mean
    //    over a flat-paper grid, the way letterpress_test's frozen-sheet
    //    block measures it. Formation is a symmetric swing and should not
    //    move the mean; this IS that claim, at the maximum swing.
    double sum = 0.0;
    for (int y = 0; y < H; ++y)
      for (int x = 0; x < W; ++x)
        sum += letterpress::sheetToothMultiplierAt(lp, x, y, W, H);
    const double toothMeanMul = sum / (W * H * 255.0);
    const double toothDarkening = 1.0 - toothMeanMul;

    // 2. WIRES, 3. SHOW-THROUGH, 4. DEFECTS -- the exact share chain
    // SurfaceSheet.cpp::ensureSheetToothTexture walks: wires take
    // kSheetShareStep of what the tooth left, show-through takes
    // kSheetShareStep of what THAT leaves, defects take the rest. Every
    // number here is the SAME budget call the layer's own test proves
    // against, not a re-derivation.
    const float paperLeft = letterpress::remainingPaperBudget(lp);

    laidstructure::Params laidParams;
    laidParams.strengthPercent = laidstructure::kStrengthMax;
    laidParams.outPxPerSourcePx = 1.0f;
    laidParams.budgetMeanDarkening = fieldselect::kSheetShareStep * paperLeft;
    const float laidBound = laidstructure::meanDarkeningBound(laidParams);
    float afterWires = paperLeft - laidBound;
    if (afterWires < 0.0f) afterWires = 0.0f;

    showthrough::Params stParams;
    stParams.strengthPercent = showthrough::kStrengthMax;
    stParams.stockScale = showThroughScaleMax;
    stParams.budgetMeanDarkening = fieldselect::kSheetShareStep * afterWires;
    const float showThroughBound = showthrough::meanDarkeningBound(stParams);

    paperdefects::Params dp;
    dp.dialPercent = paperdefects::kDialMax;
    dp.remainingBudget = afterWires - showThroughBound;
    if (dp.remainingBudget < 0.0f) dp.remainingBudget = 0.0f;
    paperdefects::Mark marks[paperdefects::kMaxMarks];
    const int markCount = paperdefects::generate(dp, W, H, marks);
    const float defectsBound =
        paperdefects::meanDarkeningBound(marks, markCount, W, H);

    // THE COMPOSITE. Each consumer's bound is structurally clamped to the
    // share it was handed -- that clamp is what each layer's own test
    // proves -- so the telescoping sum can never legitimately exceed
    // paperBudget(). Assert the INVARIANT through the real functions rather
    // than trusting the arithmetic that predicts it.
    const double totalDarkening =
        toothDarkening + laidBound + showThroughBound + defectsBound;
    const bool withinBudget =
        totalDarkening <= static_cast<double>(lp.paperDarkenBudget) + 1e-3;
    check(withinBudget,
          "light composite: tooth+formation+wires+show-through+defects "
          "together never oversubscribe the palette's paper budget");

    // ...and the number that actually matters: the resulting page still
    // clears 7:1 with every sheet-layer dial pinned to its maximum
    // SIMULTANEOUSLY -- the exact claim "individually safe and jointly
    // over" would violate.
    const double multiplier = 1.0 - totalDarkening;
    const double ratio = (paperLum * multiplier + 0.05) / (inkLum + 0.05);
    const bool clearsFloor = ratio >= wcag::kContrastFloorAAA - 0.05;
    check(clearsFloor,
          "light composite: every sheet-layer dial at max still clears the "
          "7:1 floor");
    if (!withinBudget || !clearsFloor) {
      std::printf(
          "  %s: darkening=%.4f budget=%.4f ratio=%.3f:1 (tooth=%.4f "
          "wires<=%.4f show<=%.4f defects<=%.4f)\n",
          page.name, totalDarkening,
          static_cast<double>(lp.paperDarkenBudget), ratio, toothDarkening,
          static_cast<double>(laidBound),
          static_cast<double>(showThroughBound),
          static_cast<double>(defectsBound));
    }
  }
}

// --- DARK: scanlines alone, both doctrine-excluded dials left pinned -------
void testDarkCompositionHoldsTheFloor() {
  // Dark mode's doctrine field is scanlines alone; fieldselect::select
  // excludes the grain whenever it is live, and there is no second dark-mode
  // sheet layer that stacks the way the light side's four do (corner
  // defocus MODULATES the same scanline field rather than drawing its own --
  // see src/CornerDefocus.h -- and is mean-preserving by construction, so it
  // is not a second budget consumer here). scanlines_test.cpp already proves
  // the floor at every pitch; what this test adds is going through the
  // SELECTOR -- proving the exclusion holds rather than assuming it -- with
  // ALL THREE dials pinned to their maxima simultaneously, the composition
  // question this file exists for.
  const float pitches[] = {2.0f, 3.0f * 0.7955f, 6.0f};
  const int W2 = 512, H2 = 2048;
  const int rows = 600;

  for (const auto &page : testpalettes::kDarkSweep) {
    fieldselect::Dials dials;
    dials.dark = true;
    dials.scanlinesIntensity = scanlines::kIntensityMax;
    dials.letterpressStrength = letterpress::kStrengthMax;  // left set from a
    dials.grainStrength = phosphorgrain::kStrengthMax;      // light page and
                                                              // grain; must
                                                              // not draw here
    const fieldselect::Active active = fieldselect::select(dials);
    check(active.scanlines && !active.letterpress && !active.grain,
          "dark palette selects scanlines only, per fieldselect::select, "
          "even with the other two dials left pinned to their maxima");
    if (!active.scanlines) continue;

    const float inkLum = lum(page.r, page.g, page.b);
    const float paperLum = lum(page.pr, page.pg, page.pb);
    const float budget = fieldselect::kRasterBudgetShare *
                          phosphorgrain::darkeningBudget(inkLum, paperLum);

    for (const float pitch : pitches) {
      scanlines::Params sp;
      sp.intensityPercent = scanlines::kIntensityMax;
      sp.pitchPx = pitch;
      sp.mottleDepth = scanlines::mottleDepthFor(scanlines::kIntensityMax);
      sp.budgetMeanDarkening = budget;

      double sumInk = 0.0, sumPaper = 0.0;
      for (int y = 0; y < rows; ++y) {
        sumInk += scanlines::multiplierAt(sp, W2 / 2, y, W2, H2, inkLum);
        sumPaper += scanlines::multiplierAt(sp, W2 / 2, y, W2, H2, paperLum);
      }
      const double mInk = (sumInk / rows) / 255.0;
      const double mPaper = (sumPaper / rows) / 255.0;
      const double ratio = (inkLum * mInk + 0.05) / (paperLum * mPaper + 0.05);
      const bool clearsFloor = ratio >= wcag::kContrastFloorAAA - 0.05;
      check(clearsFloor,
            "dark composite: scanlines at max, with letterpress and grain "
            "left pinned, still clears the 7:1 floor");
      if (!clearsFloor)
        std::printf("  %s @ pitch %.3f: ratio=%.3f:1\n", page.name, pitch,
                    ratio);
    }
  }
}

}  // namespace

int main() {
  testLightCompositionHoldsTheFloor();
  testDarkCompositionHoldsTheFloor();

  if (failures) {
    std::printf("%d failure(s)\n", failures);
    return 1;
  }
  std::printf("composition_test: all checks passed\n");
  return 0;
}
