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
//
// And, from the PAPER dial (owner order 2026-08-22, "paper needs a 0-100
// slider too. and be sure to be adding the existing noise treatment to it"):
//   * The 7:1 floor swept as a SURFACE: the whole 8 inks x 6 papers x 101
//     densities x 101 strengths grid, checked against both clamps. That is
//     ~490k contrast evaluations and it is the only instrument that can see a
//     hole in a two-dimensional legal region.
//   * The tint ramp is byte-exact at both ends, monotone, non-degenerate, and
//     Bright White is bit-exact at EVERY strength -- the no-op row.
//   * The tooth factor rises with the stock's roughness AND with the strength
//     dial, is exactly 1.0 at strength 0 for every stock (the smooth ground),
//     and Bright White is exactly 1.0 everywhere.
//   * The sheet pass actually USES it: a rougher factor darkens more, a 0
//     factor is a bit-exact smooth sheet, and the paper budget still holds.
//
// And, from THE FROZEN SHEET (owner ruling 2026-08-23, docs/light-ink-picker.md
// section 8 -- the drawer's paper instrument was removed and its values became
// constants):
//   * The 7:1 floor swept AT the frozen set, which is the only place it now
//     matters: every ink on every stock at every reachable density, with drift
//     at the TOP of its range (every page, not a worst case) and the frozen
//     tooth and formation painted on the DARKEST leaf.
//
// And, from SHEET-TO-SHEET DRIFT (docs/surface-roadmap.md 1c):
//   * Off is bit-exact off at every seed and on every stock, and the bound is
//     EXACT -- the 7:1 clamps take it as the darkest leaf, so an offset able
//     to exceed it would put a page under the floor with nothing to catch it.
//   * Page 47 is the same tint forever, pinned as literals: the offsets are a
//     pure function of the page seed, so a leaf survives a relaunch.
//   * Every offset in the range actually occurs over a book's worth of leaves
//     (the first draft's lightness term could not reach the ends of its own
//     dial) and the draw carries no net darkening bias.
//   * The drift moves the GROUND only: the drifted ratio is the PUBLISHED
//     wash against a drifted sheet, which is what makes the all-negative leaf
//     provably the darkest -- re-measured over the whole 125-leaf box.
//   * The 2-D floor surface re-swept at the top of the drift dial, every
//     strength, both clamps, plus the restored-backup clamp order.

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "LightInkPalette.h"
#include "Letterpress.h"
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
  // wherever the full-strength channels actually differ BY A HUE'S WORTH. This
  // is what separates a dilution curve from a chord toward the paper's
  // neutral: the linear lerp fails it for the deep blues on warm papers.
  //
  // kHueThreshold is not a fudge for a failing case, and the 2026-08-22 ink
  // additions are what made it necessary to say so. The original check asserted
  // the order for ANY pair that differed at all, which was safe while every
  // colored ink was strongly chromatic. It is wrong for a near-neutral one:
  // Printer's Ink is 1A1C1F, five code values of blue lean, and a 50% wash of
  // it on Chamois is 565550 -- YELLOW, because a near-neutral ink at half
  // density on a tan sheet is a tan wash. That is the correct answer and the
  // model should not be asked to invent a blue that is not there. So the claim
  // is narrowed to what it always meant: a pair separated by more than a few
  // code values carries a hue, and the hue survives dilution. Under the
  // threshold there is nothing to preserve, and the sheet legitimately wins.
  constexpr int kHueThreshold = 12;
  for (int i = 0; i < kInkCount; i++) {
    const uint8_t *f = kInks[i].full;
    if (f[0] == f[1] && f[1] == f[2]) continue;  // neutral: no order to keep
    for (int p = 0; p < kPaperCount; p++) {
      uint8_t wash[3];
      inkAtDensity(i, p, 50, wash);
      for (int a = 0; a < 3; a++) {
        for (int b = a + 1; b < 3; b++) {
          if (std::abs(static_cast<int>(f[a]) - static_cast<int>(f[b])) <
              kHueThreshold)
            continue;
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

  // --- APPEND-ONLY: the rows that shipped before 2026-08-22 are BYTE-PINNED -
  //
  // The single most valuable assertion in this file, and the only one that can
  // see the failure it guards. A choice persists as an integer; if row 5's
  // bytes change, every owner who picked Oxblood silently gets something else,
  // and nothing -- not the compiler, not the contrast sweep, not the ramp
  // checks -- notices, because the new bytes are perfectly legal. Inserting a
  // row instead of appending has the same signature. So the pre-existing table
  // is written out here literally: a diff to any of it is a diff to this test.
  //
  // NEW ROWS ARE APPENDED HERE TOO, at the bottom, when they ship. Nothing is
  // ever edited in place.
  {
    struct PinnedInk { int idx; const char *name; uint8_t rgb[3]; };
    static const PinnedInk kPinnedInks[] = {
        {kInkStandard, "Standard", {0x2D, 0x2D, 0x2D}},
        {kInkCarbonBlack, "Carbon Black", {0x1E, 0x1C, 0x1A}},
        {kInkIronGall, "Iron Gall", {0x1B, 0x2A, 0x3C}},
        {kInkSepia, "Sepia", {0x3E, 0x2A, 0x18}},
        {kInkWalnutBistre, "Walnut & Bistre", {0x4B, 0x3A, 0x15}},
        {kInkOxblood, "Oxblood", {0x4F, 0x15, 0x11}},
        {kInkIndigo, "Indigo", {0x2A, 0x3B, 0x5C}},
        {kInkPrussianBlue, "Prussian Blue", {0x0B, 0x30, 0x50}},
    };
    struct PinnedPaper { int idx; const char *name; uint8_t rgb[3]; float tooth; };
    static const PinnedPaper kPinnedPapers[] = {
        {kPaperBrightWhite, "Bright White", {0xFB, 0xFB, 0xF9}, 1.00f},
        {kPaperCream, "Cream", {0xF8, 0xF0, 0xD9}, 1.30f},
        {kPaperBone, "Bone", {0xEF, 0xEA, 0xE0}, 1.45f},
        {kPaperChamois, "Chamois", {0xEC, 0xDA, 0xB7}, 1.80f},
        {kPaperPressGray, "Press Gray", {0xE9, 0xEA, 0xEC}, 1.60f},
        {kPaperSepiaToned, "Sepia Toned", {0xEE, 0xDF, 0xCC}, 1.50f},
        // Appended when they shipped, per the block comment above.
        {kPaperBrightenedWhite, "Brightened White", {0xEF, 0xF0, 0xFC}, 1.05f},
    };
    for (const PinnedInk &pin : kPinnedInks) {
      CHECK(std::strcmp(kInks[pin.idx].name, pin.name) == 0,
            "ink row %d used to be %s and is now %s -- rows APPEND, never move",
            pin.idx, pin.name, kInks[pin.idx].name);
      CHECK(std::memcmp(kInks[pin.idx].full, pin.rgb, 3) == 0,
            "ink row %d (%s) changed bytes: %02X%02X%02X, was %02X%02X%02X",
            pin.idx, pin.name, kInks[pin.idx].full[0], kInks[pin.idx].full[1],
            kInks[pin.idx].full[2], pin.rgb[0], pin.rgb[1], pin.rgb[2]);
    }
    for (const PinnedPaper &pin : kPinnedPapers) {
      CHECK(std::strcmp(kPapers[pin.idx].name, pin.name) == 0,
            "paper row %d used to be %s and is now %s", pin.idx, pin.name,
            kPapers[pin.idx].name);
      CHECK(std::memcmp(kPapers[pin.idx].tone, pin.rgb, 3) == 0,
            "paper row %d (%s) changed bytes", pin.idx, pin.name);
      CHECK(std::fabs(kPapers[pin.idx].tooth - pin.tooth) < 1e-6f,
            "paper row %d (%s) changed tooth: %.2f, was %.2f -- a shipped "
            "stock silently re-textures",
            pin.idx, pin.name, kPapers[pin.idx].tooth, pin.tooth);
    }
  }

  // --- the ink FAMILIES and the derived display order -----------------------
  //
  // Grouping is presentation, so none of it may touch a stored value. What can
  // still go wrong is silent: a row with a group nobody renders disappears from
  // the picker entirely, and a heading with no rows under it is a stray label.
  {
    int seen[kInkGroupCount] = {0};
    for (int i = 0; i < kInkCount; i++) {
      CHECK(kInks[i].group >= 0 && kInks[i].group < kInkGroupCount,
            "%s has group %d, which no heading renders", kInks[i].name,
            kInks[i].group);
      if (kInks[i].group >= 0 && kInks[i].group < kInkGroupCount)
        seen[kInks[i].group]++;
    }
    for (int g = 0; g < kInkGroupCount; g++)
      CHECK(seen[g] > 0, "group %s has no inks -- a heading with nothing under it",
            kInkGroupNames[g]);

    int order[kInkCount];
    buildInkDisplayOrder(order);
    int count[kInkCount] = {0};
    for (int s = 0; s < kInkCount; s++) {
      CHECK(order[s] >= 0 && order[s] < kInkCount, "display slot %d is %d", s,
            order[s]);
      if (order[s] >= 0 && order[s] < kInkCount) count[order[s]]++;
    }
    for (int i = 0; i < kInkCount; i++)
      CHECK(count[i] == 1,
            "%s appears %d times in the display order -- it must be a "
            "permutation, or a row is missing from the picker",
            kInks[i].name, count[i]);
    // Grouped: the family index never decreases down the list, so every family
    // is one contiguous run under one heading.
    int prevGroup = -1;
    for (int s = 0; s < kInkCount; s++) {
      const int g = kInks[order[s]].group;
      CHECK(g >= prevGroup, "display order leaves and re-enters group %s",
            kInkGroupNames[g]);
      if (g > prevGroup) prevGroup = g;
    }
    // ...and within a family, table (append) order, so a new row lands at the
    // bottom of its family rather than in the middle of it.
    for (int s = 1; s < kInkCount; s++)
      if (kInks[order[s]].group == kInks[order[s - 1]].group)
        CHECK(order[s] > order[s - 1],
              "%s and %s are out of table order inside %s", kInks[order[s - 1]].name,
              kInks[order[s]].name, kInkGroupNames[kInks[order[s]].group]);
    // Row 0 is the default and must be the first thing the owner sees.
    CHECK(order[0] == kInkStandard,
          "the default ink must lead the list, got %s", kInks[order[0]].name);
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

  // ...and byte-inequality is NOT distinctness. This is the phosphor-preset
  // lesson (docs/crt-phosphor-presets.md: two rows may paint the same page only
  // if they DECAY differently, and here nothing decays): a stock one code value
  // off another is a row that costs a tap and shows nothing. The separation is
  // measured as the largest per-channel difference, which is the thing an eye
  // comparing two flat swatches side by side actually uses.
  {
    constexpr int kMinSeparation = 8;
    auto maxChannelDelta = [](const uint8_t *x, const uint8_t *y) {
      int d = 0;
      for (int c = 0; c < 3; c++) {
        const int e = std::abs(static_cast<int>(x[c]) - static_cast<int>(y[c]));
        if (e > d) d = e;
      }
      return d;
    };
    for (int a = 0; a < kPaperCount; a++)
      for (int b = a + 1; b < kPaperCount; b++)
        CHECK(maxChannelDelta(kPapers[a].tone, kPapers[b].tone) >=
                  kMinSeparation,
              "papers %s and %s differ by only %d code values -- one of them "
              "is a row that does nothing",
              kPapers[a].name, kPapers[b].name,
              maxChannelDelta(kPapers[a].tone, kPapers[b].tone));
    for (int a = 0; a < kInkCount; a++)
      for (int b = a + 1; b < kInkCount; b++)
        CHECK(maxChannelDelta(kInks[a].full, kInks[b].full) >= kMinSeparation,
              "inks %s and %s differ by only %d code values", kInks[a].name,
              kInks[b].name, maxChannelDelta(kInks[a].full, kInks[b].full));
    // Names are what the picker shows; two rows called the same thing is a UI
    // bug that no color check can see.
    for (int a = 0; a < kInkCount; a++) {
      CHECK(kInks[a].name[0] && kInks[a].era[0], "ink row %d has an empty label",
            a);
      for (int b = a + 1; b < kInkCount; b++)
        CHECK(std::strcmp(kInks[a].name, kInks[b].name) != 0,
              "two inks are both called %s", kInks[a].name);
    }
    for (int a = 0; a < kPaperCount; a++) {
      CHECK(kPapers[a].name[0] && kPapers[a].note[0],
            "paper row %d has an empty label", a);
      for (int b = a + 1; b < kPaperCount; b++)
        CHECK(std::strcmp(kPapers[a].name, kPapers[b].name) != 0,
              "two papers are both called %s", kPapers[a].name);
    }
  }

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

  // === THE PAPER DIAL ======================================================

  // --- the tint ramp: exact ends, monotone, non-degenerate, white is a no-op
  for (int p = 0; p < kPaperCount; p++) {
    uint8_t at0[3], at100[3];
    paperAtStrength(p, 0, at0);
    paperAtStrength(p, 100, at100);
    CHECK(std::memcmp(at0, kPapers[kPaperBrightWhite].tone, 3) == 0,
          "%s at strength 0 must be the bright-white ground exactly",
          kPapers[p].name);
    CHECK(std::memcmp(at100, kPapers[p].tone, 3) == 0,
          "%s at strength 100 must be the stock exactly", kPapers[p].name);

    // MONOTONE PER CHANNEL, toward that channel's own end -- the true
    // Beer-Lambert invariant, and since Brightened White the honest one: an
    // OBA sheet's blue channel sits ABOVE the ground's (brighteners lift
    // blue), so its blue legitimately RISES with loading while the sheet's
    // luminance still ends lower than it began. The old blanket "luminance
    // never rises" tripped on one-code-value quantization upticks exactly
    // there; per-channel direction plus the end-to-end luminance drop below
    // is strictly stronger everywhere else.
    int distinct = 0;
    uint8_t prev[3] = {0, 0, 0};
    bool first = true;
    for (int t = 0; t <= kPaperStrengthMax; t++) {
      uint8_t tone[3];
      paperAtStrength(p, t, tone);
      if (p == kPaperBrightWhite)
        CHECK(std::memcmp(tone, kPapers[kPaperBrightWhite].tone, 3) == 0,
              "Bright White must be bit-exact at strength %d -- it IS the "
              "ground, so its slider is a no-op at every value",
              t);
      if (!first) {
        for (int c = 0; c < 3; c++) {
          const bool falling =
              kPapers[p].tone[c] <= kPapers[kPaperBrightWhite].tone[c];
          CHECK(falling ? tone[c] <= prev[c] : tone[c] >= prev[c],
                "%s: channel %d moves against its own colorant at strength %d",
                kPapers[p].name, c, t);
        }
      }
      if (first || std::memcmp(tone, prev, 3) != 0) distinct++;
      std::memcpy(prev, tone, 3);
      first = false;
    }
    CHECK(relativeLuminance(kPapers[p].tone) <=
              relativeLuminance(kPapers[kPaperBrightWhite].tone) + 1e-12,
          "%s: a loaded sheet may lean blue but must not end LIGHTER than the "
          "bare ground",
          kPapers[p].name);
    if (p == kPaperBrightWhite) {
      CHECK(distinct == 1, "Bright White's ramp must be one color, got %d",
            distinct);
    } else {
      // A paper spans far less range than an ink wash does -- Bone moves ~12
      // code values -- so the bar is only that the dial is not decoration.
      CHECK(distinct >= 8, "%s: only %d distinct tones across the tint ramp",
            kPapers[p].name, distinct);
    }
  }

  // --- THE 2-D FLOOR: the whole ink x paper x density x strength grid ------
  // The clamps must land INSIDE the legal region from anywhere, and the
  // region under a clamped ceiling must have no holes -- with two dials, a
  // clamp that is right at the endpoints and wrong in between is exactly the
  // failure no compiler and no single-dial test can see.
  {
    long checked = 0;
    for (int i = 0; i < kInkCount; i++) {
      for (int p = 0; p < kPaperCount; p++) {
        for (int t = 0; t <= kPaperStrengthMax; t++) {
          // Full density is legal at EVERY strength: that is what makes the
          // density floor always exist, so it is asserted rather than assumed.
          CHECK(contrastAtDensity(i, p, kDensityMax, t) >= kContrastFloor,
                "%s at full density on %s at strength %d is %.2f:1",
                kInks[i].name, kPapers[p].name, t,
                contrastAtDensity(i, p, kDensityMax, t));
          const int f = floorDensityPct(i, p, t);
          CHECK(contrastAtDensity(i, p, f, t) >= kContrastFloor,
                "%s on %s at strength %d: floor %d does not clear 7:1",
                kInks[i].name, kPapers[p].name, t, f);
          if (f > 0)
            CHECK(contrastAtDensity(i, p, f - 1, t) < kContrastFloor,
                  "%s on %s at strength %d: floor %d is not minimal",
                  kInks[i].name, kPapers[p].name, t, f);
          // Everything at or above the floor clears it (the suffix property).
          for (int d = f; d <= kDensityMax; d++) {
            checked++;
            if (contrastAtDensity(i, p, d, t) < kContrastFloor) {
              CHECK(false,
                    "%s on %s at strength %d, density %d: %.3f:1 -- a HOLE "
                    "above the floor",
                    kInks[i].name, kPapers[p].name, t, d,
                    contrastAtDensity(i, p, d, t));
              break;
            }
          }
        }
        // ...and the mirror: everything at or below the ceiling clears it,
        // for every density the density clamp can leave behind.
        //
        // Densities below the BARE GROUND's floor are excluded, and that is
        // the honest statement rather than a dodge: if a wash cannot clear 7:1
        // even on plain white, no amount of paper dial makes it legal and the
        // ceiling is undefined (reported as 0). Those states exist only until
        // the density clamp runs, which the clamp-order block below proves.
        for (int d = 0; d <= kDensityMax; d++) {
          const int c = maxPaperStrengthPct(i, p, d);
          if (contrastAtDensity(i, p, d, 0) < kContrastFloor) {
            CHECK(c == 0,
                  "%s on %s density %d: nothing is legal, the ceiling must "
                  "report 0, got %d",
                  kInks[i].name, kPapers[p].name, d, c);
            continue;
          }
          for (int t = 0; t <= c; t++) {
            checked++;
            if (contrastAtDensity(i, p, d, t) < kContrastFloor) {
              CHECK(false,
                    "%s on %s density %d: strength %d is %.3f:1 under a "
                    "ceiling of %d -- a HOLE below the ceiling",
                    kInks[i].name, kPapers[p].name, d, t,
                    contrastAtDensity(i, p, d, t), c);
              break;
            }
          }
          CHECK(clampPaperStrengthPct(i, p, d, 999) == c,
                "clamp above the ceiling must land on it");
          CHECK(clampPaperStrengthPct(i, p, d, -5) == 0,
                "clamp below 0 must land on the bare ground");
        }
      }
    }
    std::printf("2-D floor sweep: %ld (density, strength) states checked\n",
                checked);
  }

  // --- the clamp ORDER loadSelection uses lands legal from any integers ----
  // The rule is "the slider you move stops, the other holds", but a restored
  // backup moves neither: strength is pinned to its ceiling for the stored
  // density, then density to its floor at the result. From ANY pair.
  {
    const int probes[] = {-50, 0, 1, 37, 64, 99, 100, 250};
    for (int i = 0; i < kInkCount; i++)
      for (int p = 0; p < kPaperCount; p++)
        for (const int rd : probes)
          for (const int rt : probes) {
            const int t = clampPaperStrengthPct(i, p, rd, rt);
            const int d = clampDensityPct(i, p, rd, t);
            CHECK(contrastAtDensity(i, p, d, t) >= kContrastFloor,
                  "%s on %s: stored (%d, %d) clamps to (%d, %d) at %.2f:1 -- "
                  "below the floor",
                  kInks[i].name, kPapers[p].name, rd, rt, d, t,
                  contrastAtDensity(i, p, d, t));
          }
  }

  // --- the tooth factor ----------------------------------------------------
  {
    CHECK(kPapers[kPaperBrightWhite].tooth == 1.0f,
          "Bright White is the reference stock and must be exactly 1.0");
    for (int p = 0; p < kPaperCount; p++) {
      CHECK(toothScaleFor(p, 0) == 1.0f,
            "%s at strength 0 is the smooth ground and must be exactly 1.0x",
            kPapers[p].name);
      CHECK(std::fabs(toothScaleFor(p, 100) - kPapers[p].tooth) < 1e-6f,
            "%s at strength 100 must be the stock's own factor", kPapers[p].name);
      CHECK(kPapers[p].tooth >= 1.0f,
            "%s: no stock may be SMOOTHER than the reference -- the shipped "
            "default is the smoothest offered",
            kPapers[p].name);
      // Monotone in the strength dial, and strictly so for a stock that is
      // not the reference (a flat rung is a slider position that does nothing).
      float prev = -1.0f;
      for (int t = 0; t <= kPaperStrengthMax; t++) {
        const float f = toothScaleFor(p, t);
        CHECK(f >= prev - 1e-6f, "%s: tooth falls at strength %d",
              kPapers[p].name, t);
        prev = f;
      }
      if (p != kPaperBrightWhite)
        CHECK(toothScaleFor(p, 100) > toothScaleFor(p, 50) &&
                  toothScaleFor(p, 50) > toothScaleFor(p, 0),
              "%s: the tooth must RISE with the tint, or the dial only "
              "recolors the sheet",
              kPapers[p].name);
      // Out of range is clamped, not extrapolated.
      CHECK(toothScaleFor(p, 900) == toothScaleFor(p, 100) &&
                toothScaleFor(p, -9) == toothScaleFor(p, 0),
            "%s: tooth factor must clamp outside 0..100", kPapers[p].name);
    }
    // Uncoated stocks are rougher than the coated bright white, and the
    // ordering the doc states holds. KOZO is the roughest offered as of the
    // 2026-08-22 additions -- unbleached washi is a mat of long bast fibre with
    // no calendering at all, and it is genuinely rougher than an aged trade
    // sheet. Chamois held this title while it was the only aged stock; the
    // claim moved rather than the number, and Chamois' own 1.80 is unchanged
    // so no shipped selection re-textures.
    CHECK(kPapers[kPaperChamois].tooth > kPapers[kPaperCream].tooth &&
              kPapers[kPaperCream].tooth > kPapers[kPaperBrightWhite].tooth,
          "the stock ordering must be bright white < cream < chamois");
    CHECK(kPapers[kPaperKozo].tooth > kPapers[kPaperChamois].tooth,
          "unbleached kozo must be rougher than an aged trade sheet");
    CHECK(kPapers[kPaperIndia].tooth < kPapers[kPaperCream].tooth,
          "India paper is the smoothest stock after the coated reference");
    for (int p = 0; p < kPaperCount; p++)
      if (p != kPaperKozo)
        CHECK(kPapers[kPaperKozo].tooth >= kPapers[p].tooth,
              "Kozo is documented as the roughest offered, but %s is rougher",
              kPapers[p].name);
  }

  // --- the formation factor (2026-08-22 paper research) --------------------
  // toothScaleFor's twin for the sheet's cloudiness. Same shape -- exactly 1.0
  // at strength 0, the stock's own value at 100, monotone in between, clamped
  // outside -- but the destination MAY sit below 1.0, because a filler-evened
  // or premium-coated sheet is legitimately calmer than the reference. The
  // ladder's one measured anchor: handmade kozo scored formation index 131
  // against 60-97 for nine machine sheets (Hirai et al. 2003), which is what
  // justifies roughly 1.5-2x and the top rung.
  {
    CHECK(kPapers[kPaperBrightWhite].formation == 1.0f,
          "Bright White is the formation reference and must be exactly 1.0");
    for (int p = 0; p < kPaperCount; p++) {
      CHECK(kPapers[p].formation > 0.0f && kPapers[p].formation <= 2.0f,
            "%s: formation %.2f out of the sane band", kPapers[p].name,
            kPapers[p].formation);
      CHECK(formationScaleFor(p, 0) == 1.0f,
            "%s at strength 0 is the reference sheet and must be exactly 1.0",
            kPapers[p].name);
      CHECK(std::fabs(formationScaleFor(p, 100) - kPapers[p].formation) < 1e-6f,
            "%s at strength 100 must be the stock's own factor",
            kPapers[p].name);
      // Monotone TOWARD the stock's value, whichever side of 1.0 it sits on.
      const bool rising = kPapers[p].formation >= 1.0f;
      float prev = rising ? -1.0f : 2.0f;
      for (int t = 0; t <= kPaperStrengthMax; t++) {
        const float f = formationScaleFor(p, t);
        CHECK(rising ? f >= prev - 1e-6f : f <= prev + 1e-6f,
              "%s: formation moves against its own stock at strength %d",
              kPapers[p].name, t);
        prev = f;
      }
      CHECK(formationScaleFor(p, 900) == formationScaleFor(p, 100) &&
                formationScaleFor(p, -9) == formationScaleFor(p, 0),
            "%s: formation factor must clamp outside 0..100", kPapers[p].name);
    }
    // The ladder the research argues: kozo highest (measured), laid antique
    // above everything else, calendered India and Brightened White the floor.
    CHECK(kPapers[kPaperKozo].formation >= 1.5f &&
              kPapers[kPaperKozo].formation <= 2.0f,
          "kozo's formation must sit in the measured 1.5-2x band");
    for (int p = 0; p < kPaperCount; p++) {
      if (p != kPaperKozo)
        CHECK(kPapers[kPaperKozo].formation > kPapers[p].formation,
              "kozo must top the formation ladder, but %s matches or beats it",
              kPapers[p].name);
      if (p != kPaperKozo && p != kPaperLaidAntique)
        CHECK(kPapers[kPaperLaidAntique].formation > kPapers[p].formation,
              "laid antique must be second on the formation ladder, but %s "
              "matches or beats it",
              kPapers[p].name);
      CHECK(kPapers[p].formation >=
                kPapers[kPaperBrightenedWhite].formation - 1e-6f,
            "Brightened White must sit at the formation floor, but %s is "
            "calmer",
            kPapers[p].name);
      CHECK(kPapers[p].formation >= kPapers[kPaperIndia].formation - 1e-6f,
            "India must sit at the formation floor, but %s is calmer",
            kPapers[p].name);
    }
    // ...and the factor is only real if it changes the sheet's cloudiness:
    // block-mean spread at the kozo-scaled depth must beat the India-scaled
    // one, same instrument as the formation structure check below.
    {
      const float dial = letterpress::kFormationDepthDefault;
      auto spreadAt = [&](float scale) {
        letterpress::Params lp;
        lp.strengthPercent = letterpress::kStrengthStandard;
        lp.toothScale = 1.5f;
        lp.formationDepth = letterpress::clampFormationDepth(dial * scale);
        const int BW = 256, BH = 256, BLK = 32;
        double lo = 1e9, hi = -1e9;
        for (int by = 0; by < BH; by += BLK)
          for (int bx = 0; bx < BW; bx += BLK) {
            double s = 0.0;
            for (int y = by; y < by + BLK; y++)
              for (int x = bx; x < bx + BLK; x++)
                s += letterpress::sheetToothMultiplierAt(lp, x, y, BW, BH);
            s /= BLK * BLK;
            if (s < lo) lo = s;
            if (s > hi) hi = s;
          }
        return hi - lo;
      };
      const double cloudy =
          spreadAt(formationScaleFor(kPaperKozo, kPaperStrengthMax));
      const double calm =
          spreadAt(formationScaleFor(kPaperIndia, kPaperStrengthMax));
      CHECK(cloudy > calm * 1.5,
            "the formation factor must reach the sheet: kozo's clouds (%.3f) "
            "should clearly beat India's (%.3f)",
            cloudy, calm);
    }
  }

  // --- the sheet pass actually uses it -------------------------------------
  // The factor is only real if it changes pixels. Mean darkening of the
  // output-wide tooth field must RISE with the factor, a 0 factor must be a
  // bit-exact smooth sheet, and the paper budget must still hold at the
  // roughest stock -- swept against Chamois under the darkest ink, the
  // tightest pair this picker can select.
  {
    const int W = 64, H = 64;
    auto meanOf = [&](float toothScale, float formation, int strength) {
      letterpress::Params lp;
      lp.strengthPercent = strength;
      lp.toothScale = toothScale;
      lp.formationDepth = formation;
      double sum = 0.0;
      for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++)
          sum += letterpress::sheetToothMultiplierAt(lp, x, y, W, H);
      return sum / (W * H);
    };
    const double flat = meanOf(0.0f, 0.0f, letterpress::kStrengthStandard);
    CHECK(flat == 255.0,
          "a tooth factor of 0 must be a bit-exact smooth sheet, got %.3f",
          flat);
    // PAIRWISE, not down the table: the rows are in display order, not tooth
    // order, so "each row darker than the last" would be asserting the wrong
    // thing. A rougher stock must darken more than a smoother one, whichever
    // rows they are.
    double mean[kPaperCount];
    for (int p = 0; p < kPaperCount; p++) {
      mean[p] = meanOf(kPapers[p].tooth, letterpress::kFormationDepthDefault,
                       letterpress::kStrengthStandard);
      CHECK(mean[p] < 255.0, "%s must actually texture the sheet",
            kPapers[p].name);
    }
    for (int a = 0; a < kPaperCount; a++)
      for (int b = 0; b < kPaperCount; b++) {
        if (kPapers[a].tooth <= kPapers[b].tooth) continue;
        CHECK(mean[a] < mean[b],
              "%s (%.2fx) must wear more tooth than %s (%.2fx), but the sheet "
              "means are %.3f and %.3f -- the factor is not reaching the field",
              kPapers[a].name, kPapers[a].tooth, kPapers[b].name,
              kPapers[b].tooth, mean[a], mean[b]);
      }
    // ...and the strength dial moves it, for one stock, end to end.
    const double atNone =
        meanOf(toothScaleFor(kPaperChamois, 0),
               letterpress::kFormationDepthDefault, letterpress::kStrengthStandard);
    const double atFull =
        meanOf(toothScaleFor(kPaperChamois, 100),
               letterpress::kFormationDepthDefault, letterpress::kStrengthStandard);
    CHECK(atFull < atNone,
          "Chamois at full tint must wear more tooth than at none (%.3f vs "
          "%.3f)",
          atFull, atNone);
    // Formation is bit-exact off at depth 0, and adds no net darkening when on
    // -- it swings the amplitude symmetrically, it does not deepen it.
    {
      letterpress::Params a, b;
      a.toothScale = b.toothScale = kPapers[kPaperChamois].tooth;
      b.formationDepth = 0.0f;
      a.formationDepth = 0.0f;
      bool same = true;
      for (int y = 0; y < 16 && same; y++)
        for (int x = 0; x < 16; x++)
          if (letterpress::sheetToothMultiplierAt(a, x, y, W, H) !=
              letterpress::sheetToothMultiplierAt(b, x, y, 0, 0)) {
            same = false;
            break;
          }
      CHECK(same, "formation depth 0 must render bit-exactly as no formation");
      const double even =
          meanOf(kPapers[kPaperChamois].tooth, 0.0f,
                 letterpress::kStrengthStandard);
      const double clouded =
          meanOf(kPapers[kPaperChamois].tooth,
                 letterpress::kFormationDepthDefault,
                 letterpress::kStrengthStandard);
      CHECK(std::fabs(even - clouded) < 1.0,
            "formation must not change the sheet's MEAN darkening (%.3f vs "
            "%.3f)",
            even, clouded);
      // ...but it must carry real low-frequency structure, which only BLOCK
      // means can see: per-pixel spread cannot tell a cloudy sheet from an
      // even one.
      letterpress::Params c;
      c.toothScale = kPapers[kPaperChamois].tooth;
      c.formationDepth = letterpress::kFormationDepthDefault;
      letterpress::Params e = c;
      e.formationDepth = 0.0f;
      const int BW = 256, BH = 256, BLK = 32;
      double spreadC = 0.0, spreadE = 0.0;
      double loC = 1e9, hiC = -1e9, loE = 1e9, hiE = -1e9;
      for (int by = 0; by < BH; by += BLK)
        for (int bx = 0; bx < BW; bx += BLK) {
          double sc = 0.0, se = 0.0;
          for (int y = by; y < by + BLK; y++)
            for (int x = bx; x < bx + BLK; x++) {
              sc += letterpress::sheetToothMultiplierAt(c, x, y, BW, BH);
              se += letterpress::sheetToothMultiplierAt(e, x, y, BW, BH);
            }
          sc /= BLK * BLK;
          se /= BLK * BLK;
          if (sc < loC) loC = sc;
          if (sc > hiC) hiC = sc;
          if (se < loE) loE = se;
          if (se > hiE) hiE = se;
        }
      spreadC = hiC - loC;
      spreadE = hiE - loE;
      CHECK(spreadC > spreadE * 2.0,
            "formation must show as block-mean structure (%.3f levels vs "
            "%.3f without it)",
            spreadC, spreadE);
    }
    // The floor, through the sheet pass, at the roughest stock and the
    // heaviest press: the flat sheet must still clear 7:1 against its ink.
    for (int i = 0; i < kInkCount; i++) {
      for (int p = 0; p < kPaperCount; p++) {
        uint8_t ground[3], wash[3];
        paperAtStrength(p, kPaperStrengthMax, ground);
        const int d = floorDensityPct(i, p, kPaperStrengthMax);
        inkAtDensity(i, p, d, wash, kPaperStrengthMax);
        const float li = (float)relativeLuminance(wash);
        const float lp = (float)relativeLuminance(ground);
        const int rungs[] = {0, 50, 100, 200, 400};
        for (const int r : rungs) {
          letterpress::Params lp2;
          lp2.strengthPercent = r;
          lp2.paperDarkenBudget = letterpress::paperBudget(li, lp);
          lp2.toothScale = toothScaleFor(p, kPaperStrengthMax);
          lp2.formationDepth = letterpress::kFormationDepthDefault;
          double sum = 0.0;
          for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++)
              sum += letterpress::sheetToothMultiplierAt(lp2, x, y, W, H);
          const double m = sum / (W * H * 255.0);
          const double ratio = (lp * m + 0.05) / (li + 0.05);
          CHECK(ratio >= kContrastFloor - 0.05,
                "%s on %s at press %d%%: the textured sheet falls to %.3f:1",
                kInks[i].name, kPapers[p].name, r, ratio);
        }
      }
    }
  }

  // --- SHEET-TO-SHEET DRIFT (docs/surface-roadmap.md 1c) -------------------
  //
  // Every failure mode here is either an invisible dial, a page that is not
  // the same page it was yesterday, or a leaf sitting under the contrast
  // floor -- and no compiler and no other test in this repo can see any of
  // the three.
  {
    // OFF IS BIT-EXACT OFF, at every seed and for every stock. A dial whose
    // zero moves a code value is not off; it is a permanently drifted page
    // nobody chose.
    for (int p = 0; p < kPaperCount; p++) {
      for (uint32_t seed = 0; seed < 4000; seed++) {
        int off[3];
        paperDriftOffsets(seed, kPaperDriftOff, off);
        CHECK(off[0] == 0 && off[1] == 0 && off[2] == 0,
              "drift off must be exactly 0, seed %u gave %d/%d/%d", seed,
              off[0], off[1], off[2]);
        uint8_t out[3];
        paperDrifted(kPapers[p].tone, seed, kPaperDriftOff, out);
        CHECK(std::memcmp(out, kPapers[p].tone, 3) == 0,
              "%s at drift 0 must be byte-exact, got %02X%02X%02X",
              kPapers[p].name, out[0], out[1], out[2]);
      }
    }
    CHECK(maxDriftCodeValues(kPaperDriftOff) == 0,
          "the bound at dial 0 must be 0 code values");
    CHECK(maxDriftCodeValues(kPaperDriftMax) == kPaperDriftCodeValuesAt100,
          "the bound at dial 100 must be %d code values",
          kPaperDriftCodeValuesAt100);

    // THE BOUND IS EXACT, not approximate. The 7:1 clamps take it as the
    // darkest sheet the dial can produce, so an offset able to exceed it
    // would put a leaf under the floor with nothing to catch it.
    for (int dial = 0; dial <= kPaperDriftMax; dial++) {
      const int bound = maxDriftCodeValues(dial);
      for (uint32_t seed = 0; seed < 2000; seed++) {
        int off[3];
        paperDriftOffsets(seed, dial, off);
        for (int c = 0; c < 3; c++)
          CHECK(off[c] >= -bound && off[c] <= bound,
                "dial %d, seed %u, channel %d: offset %d exceeds the bound %d",
                dial, seed, c, off[c], bound);
      }
    }

    // DETERMINISTIC. Page 47 is the same tint forever, including across a
    // relaunch: the offsets are a pure function of the page seed and of
    // nothing else -- no clock, no launch salt, no call count. Pinned as
    // literals, so a "harmless" change to the hash or to the 3:1 split fails
    // here rather than silently reprinting the book.
    {
      const uint32_t kPage47 = 47u;
      const int kPinnedPage47[3] = {-1, -2, -2};
      int a[3], b[3];
      paperDriftOffsets(kPage47, kPaperDriftMax, a);
      for (int rep = 0; rep < 100; rep++) {
        paperDriftOffsets(kPage47, kPaperDriftMax, b);
        CHECK(a[0] == b[0] && a[1] == b[1] && a[2] == b[2],
              "seed 47 must give one answer forever, got %d/%d/%d then "
              "%d/%d/%d",
              a[0], a[1], a[2], b[0], b[1], b[2]);
      }
      CHECK(a[0] == kPinnedPage47[0] && a[1] == kPinnedPage47[1] &&
                a[2] == kPinnedPage47[2],
            "seed 47 at dial 100 is pinned at %d/%d/%d, got %d/%d/%d",
            kPinnedPage47[0], kPinnedPage47[1], kPinnedPage47[2], a[0], a[1],
            a[2]);
      uint8_t tone[3];
      paperDrifted(kPapers[kPaperCream].tone, kPage47, kPaperDriftMax, tone);
      uint8_t expect[3];
      applyPaperDrift(kPapers[kPaperCream].tone, kPinnedPage47, expect);
      CHECK(std::memcmp(tone, expect, 3) == 0,
            "page 47's Cream must be %02X%02X%02X, got %02X%02X%02X", expect[0],
            expect[1], expect[2], tone[0], tone[1], tone[2]);
    }

    // IT SHIFTS THE PAPER AND NOTHING ELSE. The wash the picker publishes is
    // computed on the nominal sheet and a leaf's drift does not reprint it, so
    // the contrast at a given (ink, density, strength) differs from the
    // undrifted one ONLY in the ground.
    for (int i = 0; i < kInkCount; i++)
      for (int p = 0; p < kPaperCount; p++)
        for (int t = 0; t <= kPaperStrengthMax; t += 25)
          for (int d = 0; d <= kDensityMax; d += 10) {
            uint8_t ground[3], wash[3], leaf[3];
            paperAtStrength(p, t, ground);
            inkAtDensity(i, p, d, wash, t);  // the tone the picker publishes
            paperWorstDrift(ground, kPaperDriftMax, leaf);
            CHECK(std::fabs(contrastAtDensity(i, p, d, t, kPaperDriftMax) -
                            contrastRatio(wash, leaf)) < 1e-9,
                  "%s on %s d%d t%d: the drifted ratio must be the PUBLISHED "
                  "wash against a drifted ground -- nothing may reprint the "
                  "ink",
                  kInks[i].name, kPapers[p].name, d, t);
          }

    // IT IS REAL, AND IT IS SMALL. Over a book's worth of leaves the offsets
    // must actually vary (a constant offset is a global tint, which is the
    // palette dial) and must carry no net darkening or lightening bias (a
    // biased draw reads as the whole book being off-tone).
    {
      long sum = 0;
      int seen[2 * kPaperDriftCodeValuesAt100 + 1] = {0};
      const int kLeaves = 20000;
      for (uint32_t seed = 0; seed < (uint32_t)kLeaves; seed++) {
        int off[3];
        paperDriftOffsets(seed, kPaperDriftMax, off);
        sum += off[1];
        seen[off[1] + kPaperDriftCodeValuesAt100]++;
      }
      for (int v = 0; v < 2 * kPaperDriftCodeValuesAt100 + 1; v++)
        CHECK(seen[v] > kLeaves / 100,
              "offset %d occurs %d times in %d leaves -- the dial cannot "
              "reach it in practice",
              v - kPaperDriftCodeValuesAt100, seen[v], kLeaves);
      const double mean = (double)sum / kLeaves;
      CHECK(std::fabs(mean) < 0.05,
            "the lightness draw is biased: mean offset %.4f over %d leaves",
            mean, kLeaves);
      std::printf("sheet drift: mean %.4f over %d leaves, "
                  "-2/-1/0/+1/+2 = %d/%d/%d/%d/%d\n",
                  mean, kLeaves, seen[0], seen[1], seen[2], seen[3], seen[4]);
    }

    // THE DARKEST LEAF IS THE ALL-NEGATIVE ONE -- and it is EVERY leaf that is
    // checked here, not just the eight corners, because the whole box is
    // cheap at this bound. The wash is held at the tone the picker publishes
    // (computed on the nominal sheet), which is what makes the ratio
    // monotone in the ground and lets the clamp evaluate one sheet instead of
    // a minimum over 125. This is the measurement that licenses that.
    {
      const int densities[] = {40, 70, 100};
      const int strengths[] = {0, 50, 100};
      const int bound = maxDriftCodeValues(kPaperDriftMax);
      for (int i = 0; i < kInkCount; i++)
        for (int p = 0; p < kPaperCount; p++)
          for (const int d : densities)
            for (const int t : strengths) {
              uint8_t base[3], wash[3];
              paperAtStrength(p, t, base);
              washOnGround(i, base, d, wash);
              uint8_t worstTone[3];
              paperWorstDrift(base, kPaperDriftMax, worstTone);
              const double worst = contrastRatio(wash, worstTone);
              CHECK(std::fabs(worst - contrastAtDensity(i, p, d, t,
                                                        kPaperDriftMax)) < 1e-9,
                    "contrastAtDensity must report the darkest leaf's ratio");
              for (int r = -bound; r <= bound; r++)
                for (int g = -bound; g <= bound; g++)
                  for (int b = -bound; b <= bound; b++) {
                    const int off[3] = {r, g, b};
                    uint8_t tone[3];
                    applyPaperDrift(base, off, tone);
                    const double c = contrastRatio(wash, tone);
                    CHECK(c >= worst - 1e-9,
                          "%s on %s d%d t%d: leaf %d/%d/%d is %.4f:1, below "
                          "the all-negative %.4f:1 the clamp assumes",
                          kInks[i].name, kPapers[p].name, d, t, off[0], off[1],
                          off[2], c, worst);
                  }
            }
    }

    // THE REGION IS STILL NEVER EMPTY. Full density has to stay legal at
    // every strength on the darkest leaf, or the density clamp has nowhere to
    // land.
    {
      double worst = 1e9;
      int wi = 0, wp = 0, wt = 0;
      for (int i = 0; i < kInkCount; i++)
        for (int p = 0; p < kPaperCount; p++)
          for (int t = 0; t <= kPaperStrengthMax; t++) {
            const double c =
                contrastAtDensity(i, p, kDensityMax, t, kPaperDriftMax);
            if (c < worst) {
              worst = c;
              wi = i;
              wp = p;
              wt = t;
            }
          }
      CHECK(worst >= kContrastFloor,
            "%s at full density on %s at strength %d is %.3f:1 on the darkest "
            "leaf -- full density must stay legal everywhere",
            kInks[wi].name, kPapers[wp].name, wt, worst);
      std::printf("sheet drift: worst full-density pair on the darkest leaf is "
                  "%s on %s at strength %d, %.3f:1\n",
                  kInks[wi].name, kPapers[wp].name, wt, worst);
    }

    // THE CLAMPS MOVE THE RIGHT WAY. Drift can only cost contrast, so the
    // density floor may only rise and the paper ceiling may only fall.
    for (int i = 0; i < kInkCount; i++)
      for (int p = 0; p < kPaperCount; p++)
        for (int t = 0; t <= kPaperStrengthMax; t += 10) {
          CHECK(floorDensityPct(i, p, t, kPaperDriftMax) >=
                    floorDensityPct(i, p, t, kPaperDriftOff),
                "%s on %s at strength %d: the drifted floor is below the "
                "undrifted one",
                kInks[i].name, kPapers[p].name, t);
          CHECK(maxPaperStrengthPct(i, p, t, kPaperDriftMax) <=
                    maxPaperStrengthPct(i, p, t, kPaperDriftOff),
                "%s on %s at density %d: the drifted ceiling is above the "
                "undrifted one",
                kInks[i].name, kPapers[p].name, t);
        }

    // THE 2-D FLOOR SURFACE, RE-SWEPT AT THE TOP OF THE DRIFT DIAL. Same
    // shape as the undrifted sweep above -- suffix property on density,
    // PREFIX property on strength, because byte quantization makes contrast
    // non-monotone in strength and a scan down from 100 would return a
    // ceiling with illegal strengths beneath it.
    {
      long checked = 0;
      for (int i = 0; i < kInkCount; i++) {
        for (int p = 0; p < kPaperCount; p++) {
          for (int t = 0; t <= kPaperStrengthMax; t++) {
            const int f = floorDensityPct(i, p, t, kPaperDriftMax);
            CHECK(contrastAtDensity(i, p, f, t, kPaperDriftMax) >=
                      kContrastFloor,
                  "%s on %s at strength %d: drifted floor %d does not clear "
                  "7:1",
                  kInks[i].name, kPapers[p].name, t, f);
            for (int d = f; d <= kDensityMax; d++) {
              checked++;
              if (contrastAtDensity(i, p, d, t, kPaperDriftMax) <
                  kContrastFloor) {
                CHECK(false,
                      "%s on %s at strength %d, density %d: %.3f:1 on the "
                      "darkest leaf -- a HOLE above the drifted floor",
                      kInks[i].name, kPapers[p].name, t, d,
                      contrastAtDensity(i, p, d, t, kPaperDriftMax));
                break;
              }
            }
          }
          for (int d = 0; d <= kDensityMax; d++) {
            const int c = maxPaperStrengthPct(i, p, d, kPaperDriftMax);
            if (contrastAtDensity(i, p, d, 0, kPaperDriftMax) <
                kContrastFloor) {
              CHECK(c == 0,
                    "%s on %s density %d: nothing is legal on the darkest "
                    "leaf, the ceiling must report 0, got %d",
                    kInks[i].name, kPapers[p].name, d, c);
              continue;
            }
            for (int t = 0; t <= c; t++) {
              checked++;
              if (contrastAtDensity(i, p, d, t, kPaperDriftMax) <
                  kContrastFloor) {
                CHECK(false,
                      "%s on %s density %d: strength %d is %.3f:1 under a "
                      "drifted ceiling of %d -- a HOLE below it",
                      kInks[i].name, kPapers[p].name, d, t,
                      contrastAtDensity(i, p, d, t, kPaperDriftMax), c);
                break;
              }
            }
            CHECK(clampPaperStrengthPct(i, p, d, 999, kPaperDriftMax) == c,
                  "the drifted clamp above the ceiling must land on it");
          }
        }
      }
      std::printf("2-D floor sweep at drift %d%%: %ld (density, strength) "
                  "states checked\n",
                  kPaperDriftMax, checked);
    }

    // AND THE CLAMP ORDER STILL LANDS LEGAL from any stored integers with the
    // drift dial in play -- the restored-backup path.
    {
      const int probes[] = {-50, 0, 37, 100, 250};
      for (int i = 0; i < kInkCount; i++)
        for (int p = 0; p < kPaperCount; p++)
          for (const int rd : probes)
            for (const int rt : probes) {
              const int t =
                  clampPaperStrengthPct(i, p, rd, rt, kPaperDriftMax);
              const int d = clampDensityPct(i, p, rd, t, kPaperDriftMax);
              CHECK(contrastAtDensity(i, p, d, t, kPaperDriftMax) >=
                        kContrastFloor,
                    "%s on %s: stored (%d, %d) clamps to (%d, %d) at %.2f:1 on "
                    "the darkest leaf",
                    kInks[i].name, kPapers[p].name, rd, rt, d, t,
                    contrastAtDensity(i, p, d, t, kPaperDriftMax));
            }
    }
  }

  // --- THE FROZEN SHEET (owner ruling 2026-08-23) --------------------------
  //
  // The iOS drawer's paper instrument is gone: paper strength 100, tooth 300%,
  // formation 80%, defects 0, sheet drift 100, press 100/100/100, and no
  // control anywhere that reaches any of them. The constants below are the
  // ones ios/CrossPointLightInkPicker.mm freezes; they are repeated here
  // because a host test cannot compile Objective-C++, and this is the one
  // place a change there has to be mirrored.
  //
  // Drift at the TOP of its range used to be a worst case and is now every
  // page, so the floor sweep has to run there: for every ink on every stock at
  // every density the drawer can still reach, the darkest leaf under the
  // frozen tooth and formation must clear 7:1. Mean sheet darkening is the
  // instrument, matching letterpress_test's own floor sweep -- the field is
  // noise, and the floor is a property of the page rather than of one pixel.
  {
    constexpr int kFrozenPaperStrengthPct = 100;
    constexpr int kFrozenToothPct = 300;
    constexpr int kFrozenFormationPct = 80;
    constexpr int kFrozenDriftPct = kPaperDriftMax;
    constexpr int kFrozenLetterpressPct = 100;  // CrossPointPrefs, frozen too
    const int W = 64, H = 64;
    auto lum = [](const uint8_t c[3]) {
      auto ch = [](uint8_t v) {
        const float f = v / 255.0f;
        return f <= 0.04045f ? f / 12.92f
                             : std::pow((f + 0.055f) / 1.055f, 2.4f);
      };
      return 0.2126f * ch(c[0]) + 0.7152f * ch(c[1]) + 0.0722f * ch(c[2]);
    };
    double worstModel = 1e9, worstSheet = 1e9;
    int worstModelInk = 0, worstModelPaper = 0, worstSheetInk = 0,
        worstSheetPaper = 0;
    for (int i = 0; i < kInkCount; i++)
      for (int p = 0; p < kPaperCount; p++) {
        // The strength the picker derives: the frozen request through the
        // ceiling clamp, at full density, carrying the drift.
        const int strength = clampPaperStrengthPct(
            i, p, kDensityMax, kFrozenPaperStrengthPct, kFrozenDriftPct);
        const int floorPct = floorDensityPct(i, p, strength, kFrozenDriftPct);
        for (int d = floorPct; d <= kDensityMax; d++) {
          const double model =
              contrastAtDensity(i, p, d, strength, kFrozenDriftPct);
          if (model < worstModel) {
            worstModel = model;
            worstModelInk = i;
            worstModelPaper = p;
          }
          CHECK(model >= kContrastFloor - 0.005,
                "frozen sheet: %s %d%% on %s %d%% at drift %d falls to %.3f:1",
                kInks[i].name, d, kPapers[p].name, strength, kFrozenDriftPct,
                model);
        }
        // ...and the same pair with the frozen TOOTH and FORMATION painted on
        // the darkest leaf. The budget is computed from that leaf, not the
        // nominal sheet, which is what makes this a check and not a tautology.
        uint8_t ground[3], wash[3], leaf[3];
        paperAtStrength(p, strength, ground);
        washOnGround(i, ground, floorDensityPct(i, p, strength,
                                                kFrozenDriftPct),
                     wash);
        paperWorstDrift(ground, kFrozenDriftPct, leaf);
        letterpress::Params lp;
        lp.strengthPercent = kFrozenLetterpressPct;
        lp.paperDarkenBudget = letterpress::paperBudget(lum(wash), lum(leaf));
        lp.toothScale =
            toothScaleFor(p, strength) * (kFrozenToothPct / 100.0f);
        lp.formationDepth = letterpress::clampFormationDepth(
            formationScaleFor(p, strength) * (kFrozenFormationPct / 100.0f));
        double sum = 0.0;
        for (int y = 0; y < H; y++)
          for (int x = 0; x < W; x++)
            sum += letterpress::sheetToothMultiplierAt(lp, x, y, W, H);
        const double meanMul = sum / (W * H * 255.0);
        const double ratio = (lum(leaf) * meanMul + 0.05) / (lum(wash) + 0.05);
        if (ratio < worstSheet) {
          worstSheet = ratio;
          worstSheetInk = i;
          worstSheetPaper = p;
        }
        CHECK(ratio >= kContrastFloor - 0.05,
              "frozen sheet: tooth %d%% + formation %d%% on the darkest leaf "
              "drags %s on %s to %.3f:1",
              kFrozenToothPct, kFrozenFormationPct, kInks[i].name,
              kPapers[p].name, ratio);
      }
    std::printf("frozen sheet worst: model %.3f:1 (%s on %s), textured "
                "%.3f:1 (%s on %s)\n",
                worstModel, kInks[worstModelInk].name,
                kPapers[worstModelPaper].name, worstSheet,
                kInks[worstSheetInk].name, kPapers[worstSheetPaper].name);
  }

  // --- the reference tables, printed (docs/light-ink-picker.md mirrors) ----
  std::printf("paper tint ramp and tooth (strength 0/50/100):\n");
  for (int p = 0; p < kPaperCount; p++) {
    std::printf("  %-13s", kPapers[p].name);
    for (int t = 0; t <= 100; t += 50) {
      uint8_t tone[3];
      paperAtStrength(p, t, tone);
      std::printf(" %02X%02X%02X", tone[0], tone[1], tone[2]);
    }
    std::printf("   tooth %.2f/%.2f/%.2f\n", toothScaleFor(p, 0),
                toothScaleFor(p, 50), toothScaleFor(p, 100));
  }
  std::printf("density floor at paper strength 0/50/100:\n");
  for (int i = 0; i < kInkCount; i++) {
    std::printf("  %-16s", kInks[i].name);
    for (int p = 0; p < kPaperCount; p++)
      std::printf(" %02d/%02d/%02d", floorDensityPct(i, p, 0),
                  floorDensityPct(i, p, 50), floorDensityPct(i, p, 100));
    std::printf("\n");
  }
  std::printf("max paper strength at density 100/90/80:\n");
  for (int i = 0; i < kInkCount; i++) {
    std::printf("  %-16s", kInks[i].name);
    for (int p = 0; p < kPaperCount; p++)
      std::printf(" %3d/%3d/%3d", maxPaperStrengthPct(i, p, 100),
                  maxPaperStrengthPct(i, p, 90), maxPaperStrengthPct(i, p, 80));
    std::printf("\n");
  }

  if (failures) {
    std::printf("%d FAILURES\n", failures);
    return 1;
  }
  std::printf("light_ink_test: all checks passed\n");
  return 0;
}
