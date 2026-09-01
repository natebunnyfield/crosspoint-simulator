// padtopband::compute -- the iPad's black band above the paper, and
// specifically the floor that keeps it from vanishing.
//
// WHY THIS IS A HOST TEST
//
// SDL_GetWindowSafeArea cannot be driven from a host at all, so the actual
// trigger (hiding the status bar, which makes it report safeTop == 0 on the
// very next layout pass -- docs/ipad-layout-2026-08-29.md, the "interaction
// nobody asked about") cannot be reproduced here directly. What CAN be
// driven, and is the part the real bug hid inside, is the arithmetic: given
// the inputs a layout pass would have handed it, does the floor still bind.
// Owner ruling 2026-08-29 (docs/ipad-layout-2026-08-29.md, foot): asked
// whether kPadEdgeMin (16 pt) is the right floor now that the status bar is
// confirmed hidden, against raising it or dropping it -- "keep 16 pt, and add
// a test." This is that test.
//
// Build:
//   c++ -std=c++17 -Iios -o /tmp/ptb tests/pad_top_band_test.cpp && /tmp/ptb

#include "PadTopBand.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include "TestCheck.h"

// CHECKM (not the fatal CHECK) throughout, deliberately -- a mutated copy
// with the floor removed should show EVERY assertion it breaks in one run,
// not stop at the first, which is what actually distinguishing "the floor
// case failed" from "the ratio case failed" needs. See main() below for
// where the count is turned into a process exit code.
static int &failures = testcheck::g_failures;

// A REIMPLEMENTATION OF THE BUG, not of the fix -- the exact formula
// layoutPadTablet carried before the floor was added
// (docs/ipad-layout-2026-08-29.md: "Fixed by flooring cardTopPx at
// kPadEdgeMin ... Re-measured after the floor landed"). Kept here, in the
// test rather than the header, so the shipped code never contains the
// regression it exists to catch -- the same reason readingarm_test.cpp and
// panel_source_test.cpp keep their own "naive" arms instead of a #ifdef in
// the model.
namespace unflooredRegression {
inline padtopband::Result compute(float outHpx, float panelHpx, float /*safeTop*/,
                                  float /*kPadEdgeMin*/, float /*scale*/) {
  const float unit = std::max(0.0f, (outHpx - panelHpx) / 3.0f);
  const float cardTopPx = unit;  // <-- the missing max(..., floor)
  const float belowPx = std::max(0.0f, outHpx - cardTopPx - panelHpx);
  return padtopband::Result{unit, cardTopPx, belowPx};
}
}  // namespace unflooredRegression

// --- 1. The shipped numbers, byte for byte -----------------------------
//
// Pinned against the REAL measured log line from docs/ipad-layout-2026-08-29.md
// §0 ("Re-measured, same device, same script"): an iPad Pro 13 (M4) portrait,
// status bar confirmed hidden (safeTop == 0), 2064x2752 device px at 2x --
//   [pad] tablet top band: unit=389.3px (1:2 split) card=389.3px
//   panelTop=389.3px panelH=1584px below=778.7px (2.00x unit)
// This is a non-regression pin on the EXTRACTION: the header must reproduce
// the exact numbers the inline code produced before it moved.
static void testShippedIPadProNumbers() {
  const padtopband::Result r =
      padtopband::compute(/*outHpx=*/2752.0f, /*panelHpx=*/1584.0f,
                          /*safeTop=*/0.0f, /*kPadEdgeMin=*/16.0f,
                          /*scale=*/2.0f);
  CHECKM(std::abs(r.unit - 389.333f) < 0.01f, "unit = %.3f, want ~389.333",
         r.unit);
  // The derived unit (389.3) is far larger than the floor (16*2=32), so the
  // unit path wins -- cardTopPx == unit exactly, matching the shipped log's
  // card=389.3px == panelTop=389.3px.
  CHECKM(std::abs(r.cardTopPx - r.unit) < 0.001f,
         "cardTopPx (%.3f) must equal unit (%.3f) when the derived unit "
         "exceeds the floor",
         r.cardTopPx, r.unit);
  CHECKM(std::abs(r.belowPx - 778.667f) < 0.01f, "belowPx = %.3f, want ~778.667",
         r.belowPx);
  // The doc's own ratio check: below is exactly 2x above (unit), to the float
  // division, not merely "about twice as much."
  CHECKM(std::abs(r.belowPx / r.unit - 2.0f) < 0.0001f,
         "below/unit = %.6f, want exactly 2.0", r.belowPx / r.unit);
}

// --- 2. THE FLOOR IS LOAD-BEARING ---------------------------------------
//
// The exact scenario the bug shipped in: safeTop has collapsed to 0 (status
// bar confirmed hidden) AND the derived unit has also collapsed toward 0 (a
// very short available height -- outHpx == panelHpx is the limit of that,
// zero slack left over once the panel's own scale-fit height is taken out).
// Unfloored, cardTopPx would be exactly 0 here: the band vanishes, which is
// the "card=0.0px" boot log and the screenshot with no band at all that this
// header's own comment describes finding.
static void testFloorBindsWhenUnitCollapses() {
  const float outHpx = 1584.0f, panelHpx = 1584.0f;  // zero slack -> unit == 0
  const float safeTop = 0.0f;                        // status bar hidden, no notch
  const float kPadEdgeMin = 16.0f;
  const float scale = 2.0f;

  const padtopband::Result r =
      padtopband::compute(outHpx, panelHpx, safeTop, kPadEdgeMin, scale);
  CHECKM(r.unit == 0.0f, "unit must be exactly 0 when there is no slack (%.3f)",
         r.unit);
  // THE ASSERTION THIS WHOLE FILE EXISTS FOR: cardTopPx must NOT be 0 here.
  CHECKM(r.cardTopPx > 0.0f,
         "cardTopPx collapsed to %.3f -- the band above the paper would be "
         "invisible on a device whose safe area (correctly) reports 0",
         r.cardTopPx);
  CHECKM(std::abs(r.cardTopPx - kPadEdgeMin * scale) < 0.001f,
         "cardTopPx = %.3f, want exactly the floor (%.3f = kPadEdgeMin * scale)",
         r.cardTopPx, kPadEdgeMin * scale);

  // DEMONSTRATED, NOT JUST ASSERTED: run the exact pre-floor formula against
  // the SAME inputs and show it produces the bug this header fixes.
  const padtopband::Result broken =
      unflooredRegression::compute(outHpx, panelHpx, safeTop, kPadEdgeMin, scale);
  CHECKM(broken.cardTopPx == 0.0f,
         "the unfloored regression should reproduce card=0.0px exactly (got %.3f)",
         broken.cardTopPx);
  CHECKM(r.cardTopPx != broken.cardTopPx,
         "the shipped result must differ from the known-broken one");
}

// --- 3. The floor also covers a genuine notch/safe-area case ------------
//
// If the system safe area ever legitimately reports MORE than kPadEdgeMin
// (a future device with a real top cutout, unlike this iPad), the floor must
// track the LARGER of the two -- not silently prefer the constant.
static void testFloorTracksTheLargerSafeArea() {
  const float outHpx = 1584.0f, panelHpx = 1584.0f;  // unit == 0 again
  const float bigSafeTop = 40.0f;                    // > kPadEdgeMin (16)
  const padtopband::Result r =
      padtopband::compute(outHpx, panelHpx, bigSafeTop, /*kPadEdgeMin=*/16.0f,
                          /*scale=*/2.0f);
  CHECKM(std::abs(r.cardTopPx - bigSafeTop * 2.0f) < 0.001f,
         "cardTopPx = %.3f, want the safe area (%.3f), which is larger than "
         "the floor here",
         r.cardTopPx, bigSafeTop * 2.0f);
}

// --- 4. belowPx never goes negative --------------------------------------
//
// A pathological outHpx smaller than panelHpx (should not happen -- the
// scale-fit that produces panelHpx is bounded by outHpx -- but the formula
// must not hand back a negative reserved band if it ever does).
static void testBelowNeverNegative() {
  const padtopband::Result r =
      padtopband::compute(/*outHpx=*/100.0f, /*panelHpx=*/1584.0f,
                          /*safeTop=*/0.0f, /*kPadEdgeMin=*/16.0f,
                          /*scale=*/2.0f);
  CHECKM(r.belowPx >= 0.0f, "belowPx = %.3f, must never be negative", r.belowPx);
}

int main() {
  testShippedIPadProNumbers();
  testFloorBindsWhenUnitCollapses();
  testFloorTracksTheLargerSafeArea();
  testBelowNeverNegative();
  if (failures) {
    std::printf("\n%d failure(s)\n", failures);
    return 1;
  }
  std::puts("pad_top_band_test: all checks passed");
  return 0;
}
