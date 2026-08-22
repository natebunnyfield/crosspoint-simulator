// Host test for src/LightInkPalette.h -- the light page's historical-ink
// picker core. Same bar as panel_palette_test: every failure mode here is a
// wrong COLOR or a broken floor, and no compiler and no other test can see
// either.
//
//   c++ -std=c++17 -Isrc tests/light_ink_test.cpp -o /tmp/light_ink_test && /tmp/light_ink_test
//
// What is pinned, and why:
//   * OFF/default byte-exact: Standard ink at 100% on Bright White is the
//     shipped 2D2D2D-on-FBFBF9 -- an untouched install changes nothing.
//   * Every ink x paper pair >= 7:1 at full density (the floor sweep).
//   * The floor is exact: at floorDensityPct the pair clears 7:1, one percent
//     below it does not, and the clamp lands exactly there.
//   * The dilution ramp ends AT the paper and AT the ink, byte-exact, is
//     luminance-monotone, and is non-degenerate (a slider whose steps paint
//     the same color is decoration).
//   * The Beer-Lambert model keeps each colored ink's channel ORDER at half
//     density -- the "reads correctly at 30-70%" claim, quantified. A linear
//     lerp regression would not fail compilation; it fails this.
//   * Unknown indices fall back to the shipped rows.
//   * No two inks and no two papers are the same bytes -- a duplicate row is
//     decoration.

#include <cmath>
#include <cstdio>
#include <cstring>

#include "LightInkPalette.h"
#include "PadPalette.h"

static int failures = 0;

#define CHECK(cond, ...)                                                       \
  do {                                                                         \
    if (!(cond)) {                                                             \
      std::printf("FAIL %s:%d: ", __FILE__, __LINE__);                         \
      std::printf(__VA_ARGS__);                                                \
      std::printf("\n");                                                       \
      failures++;                                                              \
    }                                                                          \
  } while (0)

using namespace lightink;

int main() {
  // --- default byte-exact --------------------------------------------------
  {
    uint8_t out[3];
    inkAtDensity(kInkStandard, kPaperBrightWhite, 100, out);
    CHECK(out[0] == 0x2D && out[1] == 0x2D && out[2] == 0x2D,
          "Standard@100 must be 2D2D2D, got %02X%02X%02X", out[0], out[1],
          out[2]);
    CHECK(kPapers[kPaperBrightWhite].tone[0] == 0xFB &&
              kPapers[kPaperBrightWhite].tone[1] == 0xFB &&
              kPapers[kPaperBrightWhite].tone[2] == 0xF9,
          "Bright White must be FBFBF9");
  }

  // --- full-density floor sweep, every pair --------------------------------
  for (int i = 0; i < kInkCount; i++) {
    for (int p = 0; p < kPaperCount; p++) {
      const double c = contrastAtDensity(i, p, 100);
      CHECK(c >= kContrastFloor,
            "%s on %s is %.2f:1 at full density -- below the 7:1 floor",
            kInks[i].name, kPapers[p].name, c);
    }
  }

  // --- the floor is exact, and the clamp lands on it -----------------------
  for (int i = 0; i < kInkCount; i++) {
    for (int p = 0; p < kPaperCount; p++) {
      const int f = floorDensityPct(i, p);
      CHECK(f > 0 && f <= 100, "%s on %s: floor %d out of range", kInks[i].name,
            kPapers[p].name, f);
      CHECK(contrastAtDensity(i, p, f) >= kContrastFloor,
            "%s on %s: floor %d does not clear 7:1", kInks[i].name,
            kPapers[p].name, f);
      if (f > 0)
        CHECK(contrastAtDensity(i, p, f - 1) < kContrastFloor,
              "%s on %s: %d already clears 7:1, floor is not minimal",
              kInks[i].name, kPapers[p].name, f - 1);
      CHECK(clampDensityPct(i, p, 0) == f, "clamp below floor must land on it");
      CHECK(clampDensityPct(i, p, f) == f, "clamp at floor must hold");
      CHECK(clampDensityPct(i, p, 100) == 100, "clamp at 100 must hold");
      CHECK(clampDensityPct(i, p, 250) == 100, "clamp above 100 must cap");
    }
  }

  // --- ramp: byte-exact ends, monotone luminance, non-degenerate -----------
  for (int i = 0; i < kInkCount; i++) {
    for (int p = 0; p < kPaperCount; p++) {
      uint8_t at0[3], at100[3];
      inkAtDensity(i, p, 0, at0);
      inkAtDensity(i, p, 100, at100);
      CHECK(std::memcmp(at0, kPapers[p].tone, 3) == 0,
            "%s on %s: density 0 must be the paper exactly", kInks[i].name,
            kPapers[p].name);
      CHECK(std::memcmp(at100, kInks[i].full, 3) == 0,
            "%s on %s: density 100 must be the ink exactly", kInks[i].name,
            kPapers[p].name);

      double prevY = 1e9;
      int distinct = 0;
      uint8_t prev[3] = {255, 255, 255};
      bool first = true;
      for (int d = 0; d <= 100; d++) {
        uint8_t wash[3];
        inkAtDensity(i, p, d, wash);
        const double y = relativeLuminance(wash);
        CHECK(y <= prevY + 1e-12,
              "%s on %s: luminance rises at density %d -- ramp not monotone",
              kInks[i].name, kPapers[p].name, d);
        prevY = y;
        if (first || std::memcmp(wash, prev, 3) != 0) {
          distinct++;
          std::memcpy(prev, wash, 3);
          first = false;
        }
      }
      // 101 samples must paint a real ramp. The span ink..paper is ~200 code
      // values of luminance, so well over half the steps should move at least
      // one channel; 60 distinct colors is a loose but real lower bound.
      CHECK(distinct >= 60, "%s on %s: only %d distinct colors across the ramp",
            kInks[i].name, kPapers[p].name, distinct);
    }
  }

  // --- the model keeps hue at mid density ----------------------------------
  // For every ink whose full-strength channels are not all equal, the CHANNEL
  // ORDER at 50% density on every paper must match the full-strength order
  // wherever the full-strength channels actually differ. This is what
  // separates a dilution curve from a chord toward the paper's neutral: the
  // linear lerp fails it for the deep blues on warm papers.
  for (int i = 0; i < kInkCount; i++) {
    const uint8_t *f = kInks[i].full;
    if (f[0] == f[1] && f[1] == f[2]) continue;  // neutral: no order to keep
    for (int p = 0; p < kPaperCount; p++) {
      uint8_t wash[3];
      inkAtDensity(i, p, 50, wash);
      for (int a = 0; a < 3; a++) {
        for (int b = a + 1; b < 3; b++) {
          if (f[a] == f[b]) continue;
          const bool fullOrder = f[a] > f[b];
          const bool washOrder = wash[a] > wash[b];
          if (wash[a] == wash[b]) continue;  // a tie is not an inversion
          CHECK(fullOrder == washOrder,
                "%s on %s: channel order flips at 50%% (full %02X%02X%02X, "
                "wash %02X%02X%02X)",
                kInks[i].name, kPapers[p].name, f[0], f[1], f[2], wash[0],
                wash[1], wash[2]);
        }
      }
    }
  }

  // --- unknown indices fall back -------------------------------------------
  {
    uint8_t out[3], std100[3];
    inkAtDensity(kInkStandard, kPaperBrightWhite, 100, std100);
    inkAtDensity(-3, 99, 100, out);
    CHECK(std::memcmp(out, std100, 3) == 0,
          "unknown indices must fall back to Standard on Bright White");
    CHECK(floorDensityPct(-1, -1) == floorDensityPct(kInkStandard, kPaperBrightWhite),
          "floor for unknown indices must be the fallback pair's floor");
  }

  // --- no duplicate rows ---------------------------------------------------
  for (int a = 0; a < kInkCount; a++)
    for (int b = a + 1; b < kInkCount; b++)
      CHECK(std::memcmp(kInks[a].full, kInks[b].full, 3) != 0,
            "inks %s and %s are the same bytes", kInks[a].name, kInks[b].name);
  for (int a = 0; a < kPaperCount; a++)
    for (int b = a + 1; b < kPaperCount; b++)
      CHECK(std::memcmp(kPapers[a].tone, kPapers[b].tone, 3) != 0,
            "papers %s and %s are the same bytes", kPapers[a].name,
            kPapers[b].name);

  // --- the sheet tone IS the resolved paper (owner 2026-08-22: "make sure ---
  // panel and paper actually match visually, in color..."). The card, the
  // letterbox clear and the pad's field all reach the screen through
  // padpalette::makePaletteOn(..., paper).field (applyPanel ->
  // setClearColor(p.field); the zen strip reads currentPanel().paper
  // directly), so byte-for-byte preservation of the paper through that call is
  // the color half of the seam. Pinned for the shipped default and for every
  // paper this picker can select, in both appearances.
  for (int p = 0; p < kPaperCount; p++) {
    for (int dark = 0; dark <= 1; dark++) {
      const padpalette::Palette pad =
          padpalette::makePaletteOn(dark != 0, -1, -1, kPapers[p].tone);
      CHECK(std::memcmp(pad.field, kPapers[p].tone, 3) == 0,
            "pad field must be %s's paper byte-for-byte (dark=%d)",
            kPapers[p].name, dark);
    }
  }

  // --- the reference tables, printed (docs/light-ink-picker.md mirrors) ----
  std::printf("full-density contrast / floor pct:\n");
  for (int i = 0; i < kInkCount; i++) {
    std::printf("  %-16s", kInks[i].name);
    for (int p = 0; p < kPaperCount; p++)
      std::printf(" %5.2f/%02d", contrastAtDensity(i, p, 100),
                  floorDensityPct(i, p));
    std::printf("\n");
  }

  if (failures) {
    std::printf("%d FAILURES\n", failures);
    return 1;
  }
  std::printf("light_ink_test: all checks passed\n");
  return 0;
}
