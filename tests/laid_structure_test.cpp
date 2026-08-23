// Host test for src/LaidStructure.h -- chain and laid lines for a laid stock.
//
// Every failure mode is a wrong PICTURE: a beat against the fractional
// presentation (the laid pitch is ~1.9 px, squarely ST-008), a field that
// lifts instead of darkens, a sheet that re-rolls its wires on every visit to
// the same page, or a tight palette dragged under the floor. Same reason
// scanlines and letterpress have theirs.
//
//   c++ -std=c++17 -Isrc tests/laid_structure_test.cpp -o /tmp/laid_structure_test && /tmp/laid_structure_test

#include "LaidStructure.h"

#include <cmath>
#include <cstdio>
#include <initializer_list>

#include "Letterpress.h"  // the budget arithmetic the sheet pass shares
#include "ContrastFloor.h"

using namespace laidstructure;

static int failures = 0;

static void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    failures++;
  }
}

int main() {
  // The two scales that matter: the desktop's device-exact window and the
  // phone's fractional presentation (3x render at 0.7955 -> 2.39 output px
  // per source px, the ST-008 number).
  const float kDesktopScale = 1.0f;
  const float kPhoneScale = 2.39f;

  // --- OFF IS BIT-EXACT OFF -------------------------------------------------
  {
    Params off;
    off.strengthPercent = kStrengthOff;
    off.outPxPerSourcePx = kPhoneScale;
    bool clean = true;
    for (int y = 0; y < 128 && clean; ++y)
      for (int x = 0; x < 128; ++x)
        if (multiplierAt(off, x, y) != 255) {
          clean = false;
          break;
        }
    check(clean, "strength 0 is a bit-exact no-op everywhere");
    check(meanDarkeningBound(off) == 0.0f,
          "an off field spends none of the defect layer's budget");
  }

  // --- IT ONLY EVER DARKENS, AND NEVER TO NOTHING --------------------------
  {
    Params p;
    p.strengthPercent = kStrengthMax;
    p.outPxPerSourcePx = kPhoneScale;
    int lo = 255, hi = 0;
    for (int y = 0; y < 256; ++y)
      for (int x = 0; x < 256; ++x) {
        const int m = multiplierAt(p, x, y);
        if (m < lo) lo = m;
        if (m > hi) hi = m;
      }
    check(hi <= 255, "the field can only darken");
    check(lo >= static_cast<int>(kMinMultiplier * 255.0f),
          "the field never extinguishes a texel, even at the clamp maximum");
    check(hi > lo, "the field carries real structure, not a flat fill");
  }

  // --- THE GEOMETRY IS THE MEASURED ONE ------------------------------------
  // Pitches derive from the mm constants through the one stated px/mm
  // assumption; chains land 26-39 mm apart and laids near 1 mm, and chains
  // read DARKER than laid lines -- the Heritage Science ordering.
  {
    Params p;
    p.strengthPercent = kStrengthStandard;
    p.outPxPerSourcePx = kDesktopScale;
    p.phaseJitterFrac = 0.0f;
    check(std::fabs(laidPitchPx(p) - kLaidPitchMm * kPxPerMmSource) < 1e-5f,
          "laid pitch is the mm figure through the stated px/mm");
    check(chainPitchPx(p) / laidPitchPx(p) > 26.0f &&
              chainPitchPx(p) / laidPitchPx(p) < 39.0f,
          "chain-to-laid pitch ratio sits inside the measured 26-39 band");

    // Sample the two normalized combs on their own axes. The laid comb at
    // 1.85 px pitch is heavily overlapped, so its swing is small; the chain
    // comb at ~59 px is fully resolved, so its peak must clearly beat the
    // laid comb's -- kChainDepthRatio carries the "chains darker" claim.
    float laidLo = 1e9f, laidHi = -1e9f, chainLo = 1e9f, chainHi = -1e9f;
    for (int y = 0; y < 400; ++y) {
      const float d = rowLaidDarkness(p, static_cast<float>(y));
      if (d < laidLo) laidLo = d;
      if (d > laidHi) laidHi = d;
    }
    for (int x = 0; x < 400; ++x) {
      const float d = colChainDarkness(p, static_cast<float>(x));
      if (d < chainLo) chainLo = d;
      if (d > chainHi) chainHi = d;
    }
    check(chainHi > laidHi, "a chain line is darker than a laid line");
    check(chainLo < 0.35f,
          "between chains the column darkness falls away -- the chains are "
          "lines, not a wash");
    // The antique strip: halfway out from a chain line the strip still holds
    // the column above the far-field floor. Locate the darkest column (a
    // chain center) and compare its shoulder against the farthest point.
    int cx = 0;
    float best = -1.0f;
    for (int x = 0; x < 400; ++x) {
      const float d = colChainDarkness(p, static_cast<float>(x));
      if (d > best) {
        best = d;
        cx = x;
      }
    }
    const int stripPx = static_cast<int>(kStripSigmaMm * kPxPerMmSource + 0.5f);
    const float shoulder =
        colChainDarkness(p, static_cast<float>(cx + stripPx));
    const float far = colChainDarkness(
        p, static_cast<float>(cx) + chainPitchPx(p) * 0.5f);
    check(shoulder > far + 0.05f,
          "the antique strip darkens the chain's shoulder above the far field");
  }

  // --- NO BEAT AGAINST THE FRACTIONAL PRESENTATION (ST-008) ----------------
  // The laid pitch is a non-integer number of output pixels at every scale
  // that matters; a point-sampled comb would alias against the row lattice at
  // a long period. Box integration is the fix; pin it exactly the way
  // scanlines_test pins its 2.39 px case: window means (~10 periods wide)
  // must be flat down the whole sheet, jitter off so this measures the
  // integrator rather than the intended irregularity.
  {
    for (const float scale : {kDesktopScale, kPhoneScale}) {
      Params p;
      p.strengthPercent = kStrengthStandard;
      p.outPxPerSourcePx = scale;
      p.phaseJitterFrac = 0.0f;
      const float pitch = laidPitchPx(p);
      const int win = static_cast<int>(10.0f * pitch + 0.5f);
      double lo = 1e9, hi = -1e9;
      for (int y0 = 0; y0 + win <= 2000; y0 += win) {
        double sum = 0.0;
        for (int y = y0; y < y0 + win; ++y)
          sum += rowLaidDarkness(p, static_cast<float>(y));
        sum /= win;
        if (sum < lo) lo = sum;
        if (sum > hi) hi = sum;
      }
      check(hi - lo < 0.015,
            "per-window laid means are stable down the sheet: no long-period "
            "beat");
    }
  }

  // --- PER-PAGE DETERMINISM -------------------------------------------------
  // The seed is the page's identity: the same page is the same sheet forever,
  // and a different page is a visibly different pressing of the same mould --
  // phase moves, geometry does not.
  {
    Params a, b;
    a.outPxPerSourcePx = b.outPxPerSourcePx = kPhoneScale;
    a.seed = 0x12345678u;
    b.seed = a.seed;
    bool stable = true;
    for (int y = 0; y < 128 && stable; y += 3)
      for (int x = 0; x < 128; x += 3)
        if (multiplierAt(a, x, y) != multiplierAt(b, x, y)) {
          stable = false;
          break;
        }
    check(stable, "one seed is one sheet, deterministically");
    b.seed = 0x12345679u;
    int differ = 0, n = 0;
    for (int y = 0; y < 256; y += 2)
      for (int x = 0; x < 256; x += 2) {
        if (multiplierAt(a, x, y) != multiplierAt(b, x, y)) differ++;
        n++;
      }
    check(differ > n / 16, "a different page seed re-phases the wires");
  }

  // --- THE MEAN-FIELD BOUND HOLDS, SO THE BUDGET CAP IS REAL ---------------
  // effectiveDepth turns a paper budget into a depth cap through
  // kMeanFieldBound; that only bounds the mean darkening if the composite
  // field's mean really stays under the constant, at every offered scale and
  // with the shipped jitter.
  {
    for (const float scale : {kDesktopScale, 2.0f, kPhoneScale, 3.0f}) {
      Params p;
      p.strengthPercent = kStrengthStandard;
      p.outPxPerSourcePx = scale;
      const int W = static_cast<int>(chainPitchPx(p) * 4.0f);
      const int H = static_cast<int>(laidPitchPx(p) * 200.0f);
      double sum = 0.0;
      for (int y = 0; y < H; ++y)
        sum += rowLaidDarkness(p, static_cast<float>(y));
      double rowMean = sum / H;
      sum = 0.0;
      for (int x = 0; x < W; ++x)
        sum += colChainDarkness(p, static_cast<float>(x));
      const double colMean = sum / W;
      check(rowMean + colMean < kMeanFieldBound,
            "the composite mean field stays under kMeanFieldBound");
    }
    // ...and the cap itself bites: a small budget caps the depth to it.
    Params tight;
    tight.strengthPercent = kStrengthMax;
    tight.budgetMeanDarkening = 0.02f;
    check(effectiveDepth(tight) * kMeanFieldBound <= 0.02f + 1e-6f,
          "a paper budget caps the depth structurally");
    check(meanDarkeningBound(tight) <= 0.02f + 1e-6f,
          "what the field reports spending never exceeds the budget");
  }

  // --- THE 7:1 FLOOR, THROUGH THE SHEET ARITHMETIC HalDisplay SHIPS --------
  // The sheet pass gives this field HALF of what the tooth leaves
  // (letterpress::remainingPaperBudget * 0.5, the other half staying with the
  // defect layer). Swept at the TOP of the dial on the same five light
  // palettes letterpress_test uses, including Latte light at 7.06:1 -- the
  // tightest -- the flat sheet with tooth AND wires must hold the floor.
  {
    auto lum = [](int r, int g, int b) {
      auto ch = [](int v) {
        const float f = v / 255.0f;
        return f <= 0.04045f ? f / 12.92f
                             : std::pow((f + 0.055f) / 1.055f, 2.4f);
      };
      return 0.2126f * ch(r) + 0.7152f * ch(g) + 0.0722f * ch(b);
    };
    const struct { int r, g, b, pr, pg, pb; } pages[] = {
        {0x2D, 0x2D, 0x2D, 0xFB, 0xFB, 0xF9},  // Default, 13.3:1
        {0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF},  // High Contrast, 21:1
        {0x3B, 0x32, 0x28, 0xF2, 0xE7, 0xD0},  // Sepia, 10.2:1
        {0x3C, 0x38, 0x36, 0xFB, 0xF1, 0xC7},  // Gruvbox Light, 10.2:1
        {0x4C, 0x4F, 0x69, 0xEF, 0xF1, 0xF5},  // Latte, 7.06:1 -- the tight one
    };
    const int rungs[] = {50, 100, 200, 400};
    for (const auto &page : pages) {
      const float li = lum(page.r, page.g, page.b);
      const float lp = lum(page.pr, page.pg, page.pb);
      letterpress::Params lps;
      lps.strengthPercent = letterpress::kStrengthStandard;
      lps.paperDarkenBudget = letterpress::paperBudget(li, lp);
      lps.toothScale = 1.85f;  // the laid stock's own roughness at full tint
      for (const int r : rungs) {
        Params p;
        p.strengthPercent = r;
        p.outPxPerSourcePx = kPhoneScale;
        p.budgetMeanDarkening =
            0.5f * letterpress::remainingPaperBudget(lps);
        // The joint flat sheet: tooth field times laid field, both at their
        // own budget share, over a block that spans several chain pitches.
        const int W = 512, H = 512;
        double sum = 0.0;
        for (int y = 0; y < H; ++y) {
          const float rowD = rowLaidDarkness(p, static_cast<float>(y));
          for (int x = 0; x < W; ++x) {
            const double tooth =
                letterpress::sheetToothMultiplierAt(lps, x, y, W, H) / 255.0;
            const double laid =
                combine(p, rowD, colChainDarkness(p, static_cast<float>(x))) /
                255.0;
            sum += tooth * laid;
          }
        }
        const double m = sum / (W * H);
        const double ratio = (lp * m + 0.05) / (li + 0.05);
        check(ratio >= wcag::kContrastFloorAAA - 0.05,
              "no offered rung drags a flat laid sheet under the contrast "
              "floor");
      }
    }
  }

  // --- THE CACHE SPLIT IS EXACT --------------------------------------------
  // HalDisplay caches rowLaidDarkness per row and colChainDarkness per column
  // and folds them through combine(); that is only legal if the split equals
  // multiplierAt everywhere.
  {
    Params p;
    p.strengthPercent = kStrengthStandard;
    p.outPxPerSourcePx = kPhoneScale;
    p.budgetMeanDarkening = 0.04f;
    bool same = true;
    for (int y = 0; y < 96 && same; ++y) {
      const float rowD = rowLaidDarkness(p, static_cast<float>(y));
      for (int x = 0; x < 96; ++x)
        if (combine(p, rowD, colChainDarkness(p, static_cast<float>(x))) !=
            multiplierAt(p, x, y)) {
          same = false;
          break;
        }
    }
    check(same, "combine(row, col) is exactly multiplierAt -- the cache split");
  }

  if (failures == 0) std::printf("laid_structure_test: all checks passed\n");
  return failures ? 1 : 0;
}
