// Host test for src/Scanlines.h.
//
// Every failure mode of this file is a wrong PICTURE -- a beat against the
// fractional presentation (the ST-008 class), a bloom that lifts instead of
// sparing, a mottle that nets brightening, a tight palette dragged under the
// floor. Same reason PhosphorGrain has its test.

#include "Scanlines.h"

#include <cmath>
#include <cstdio>
#include <vector>

using namespace scanlines;

static int failures = 0;

static void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    failures++;
  }
}

// The iPhone Air case from the ST-008 writeup: 3x render presented at 0.7955.
static constexpr float kPhonePitch = 3.0f * 0.7955f;
static constexpr int W = 512, H = 2048;

static double meanRows(const Params &p, int y0, int y1, float level) {
  double sum = 0.0;
  int n = 0;
  for (int y = y0; y < y1; ++y) {
    sum += multiplierAt(p, W / 2, y, W, H, level);
    n++;
  }
  return n ? sum / n : 255.0;
}

int main() {
  // --- OFF IS BIT-EXACT OFF -------------------------------------------------
  {
    Params off;
    off.intensityPercent = kIntensityOff;
    off.pitchPx = kPhonePitch;
    off.mottleDepth = kMottleDepthMax;
    bool allClear = true;
    for (int y = 0; y < H; y += 3)
      for (int x = 0; x < W; x += 37)
        for (float level : {0.0f, 0.5f, 1.0f})
          if (multiplierAt(off, x, y, W, H, level) != 255) allClear = false;
    check(allClear, "intensity 0 is a bit-exact no-op at every level and pitch");
  }

  // --- IT ONLY EVER DARKENS, AND NEVER TO NOTHING --------------------------
  {
    Params p;
    p.intensityPercent = kIntensityMax;
    p.pitchPx = kPhonePitch;
    p.mottleDepth = kMottleDepthMax;
    int lo = 255, hi = 0;
    for (int y = 0; y < H; y += 1)
      for (int x = 0; x < W; x += 61) {
        const int m = multiplierAt(p, x, y, W, H, 0.0f);
        if (m < lo) lo = m;
        if (m > hi) hi = m;
      }
    check(hi <= 255, "scanlines never brighten a texel");
    check(lo >= static_cast<int>(kMinMultiplier * 255.0f),
          "scanlines never extinguish a texel");
  }

  // --- THERE IS ACTUAL LINE STRUCTURE AT A RESOLVABLE PITCH ----------------
  // ...and it SELF-ATTENUATES at 1:1, where a real tube's lines also vanish.
  {
    Params p;
    p.intensityPercent = kIntensityStandard;
    p.pitchPx = kPhonePitch;
    p.phaseJitterFrac = 0.0f;
    p.thickJitter = 0.0f;
    int lo = 255, hi = 0;
    for (int y = 0; y < 200; ++y) {
      const int m = multiplierAt(p, 0, y, W, H, 0.0f);
      if (m < lo) lo = m;
      if (m > hi) hi = m;
    }
    check(hi - lo > 40, "a 2.39 px pitch renders visible line structure");

    Params one = p;
    one.pitchPx = 1.0f;
    lo = 255;
    hi = 0;
    for (int y = 0; y < 200; ++y) {
      const int m = multiplierAt(one, 0, y, W, H, 0.0f);
      if (m < lo) lo = m;
      if (m > hi) hi = m;
    }
    check(hi - lo < 12,
          "at 1:1 the structure self-attenuates toward a uniform dimming");
  }

  // --- NO BEAT AGAINST THE FRACTIONAL PRESENTATION (ST-008) ----------------
  // The period is a non-integer number of device pixels, so a point-sampled
  // comb would alias against the row lattice at a long period. Box
  // integration is the fix; pin it: window means (~10 periods wide) must be
  // flat down the whole panel.
  {
    Params p;
    p.intensityPercent = kIntensityStandard;
    p.pitchPx = kPhonePitch;
    p.phaseJitterFrac = 0.0f;
    p.thickJitter = 0.0f;
    const int win = static_cast<int>(10.0f * kPhonePitch + 0.5f);
    double lo = 255.0, hi = 0.0;
    for (int y0 = 0; y0 + win <= H; y0 += win) {
      const double m = meanRows(p, y0, y0 + win, 0.0f);
      if (m < lo) lo = m;
      if (m > hi) hi = m;
    }
    check(hi - lo < 255.0 * 0.015,
          "per-window means are stable down the panel: no long-period beat");
  }

  // --- BLOOM: BRIGHT CONTENT THINS THE GAP, AND ONLY EVER SPARES -----------
  {
    Params p;
    p.intensityPercent = kIntensityStandard;
    p.pitchPx = kPhonePitch;
    p.phaseJitterFrac = 0.0f;
    p.thickJitter = 0.0f;
    bool monotone = true, everyRowSpared = true;
    double gapGain = 0.0;
    for (int y = 0; y < 200; ++y) {
      int prev = -1;
      for (float level : {0.0f, 0.25f, 0.5f, 0.75f, 1.0f}) {
        const int m = multiplierAt(p, 0, y, W, H, level);
        if (prev >= 0 && m < prev) monotone = false;
        prev = m;
      }
      const int dark = multiplierAt(p, 0, y, W, H, 0.0f);
      const int bright = multiplierAt(p, 0, y, W, H, 1.0f);
      if (bright < dark) everyRowSpared = false;
      gapGain += bright - dark;
    }
    check(monotone, "more beam current never darkens a row");
    check(everyRowSpared, "bloom spares; it never costs a row light");
    check(gapGain / 200.0 > 10.0,
          "full brightness visibly thins the gap (the hyperrealism)");
  }

  // --- THE MOTTLE RIDES THE STRUCTURE, WITHOUT NET BRIGHTENING -------------
  // Block means: per-pixel spread cannot tell a blotchy field from an even
  // one (the phosphor_grain lesson). Depth 0 is bit-exact the plain field.
  {
    Params plain;
    plain.intensityPercent = kIntensityStandard;
    plain.pitchPx = kPhonePitch;
    Params mottled = plain;
    mottled.mottleDepth = mottleDepthFor(kIntensityStandard);

    bool depthZeroExact = true;
    Params zero = plain;
    zero.mottleDepth = 0.0f;
    for (int y = 0; y < H; y += 7)
      for (int x = 0; x < W; x += 31)
        if (multiplierAt(zero, x, y, W, H, 0.0f) !=
            multiplierAt(plain, x, y, W, H, 0.0f))
          depthZeroExact = false;
    check(depthZeroExact, "mottle depth 0 is bit-exact the plain raster");

    double blockLo = 255.0, blockHi = 0.0, meanPlain = 0.0, meanMottled = 0.0;
    const int bw = W / 4, bh = H / 8;
    for (int by = 0; by < 8; ++by)
      for (int bx = 0; bx < 4; ++bx) {
        double sum = 0.0;
        int n = 0;
        for (int y = by * bh; y < (by + 1) * bh; y += 3)
          for (int x = bx * bw; x < (bx + 1) * bw; x += 17) {
            sum += multiplierAt(mottled, x, y, W, H, 0.0f);
            meanPlain += multiplierAt(plain, x, y, W, H, 0.0f);
            n++;
          }
        meanMottled += sum;
        const double m = sum / n;
        if (m < blockLo) blockLo = m;
        if (m > blockHi) blockHi = m;
      }
    check(blockHi - blockLo > 2.0,
          "the mottle carries real low-frequency structure on the raster");
    check(meanMottled <= meanPlain + std::abs(meanPlain) * 0.01,
          "the mottle redistributes depth; it never nets a brightening");
  }

  // --- THE LADDER IS MONOTONE, EVERY RUNG DISTINCT, MOTTLE FOLDED ----------
  {
    const int rungs[] = {0, 50, 100, 150};
    double prev = -1.0;
    bool monotone = true, distinct = true;
    float prevMottle = -1.0f;
    bool mottleMonotone = true;
    for (const int r : rungs) {
      Params p;
      p.intensityPercent = r;
      p.pitchPx = kPhonePitch;
      p.mottleDepth = mottleDepthFor(r);
      const double darkening = 255.0 - meanRows(p, 0, 400, 0.0f);
      if (darkening < prev) monotone = false;
      if (prev >= 0.0 && darkening - prev < 1.0) distinct = false;
      prev = darkening;
      if (mottleDepthFor(r) < prevMottle) mottleMonotone = false;
      prevMottle = mottleDepthFor(r);
    }
    check(monotone, "more dial is never less raster");
    check(distinct, "every offered rung is visibly its own setting");
    check(mottleMonotone, "the folded mottle depth is monotone in the dial");
    check(mottleDepthFor(0) == 0.0f, "off folds to zero mottle, exactly");
  }

  // --- NO OFFERED RUNG TAKES ANY DARK PALETTE UNDER THE FLOOR --------------
  // The same five pages the grain sweeps, including the two tightest (P11
  // Blue 7.4:1 and P22R). The budget cap on the depth is what holds it,
  // structurally. Text is BRIGHT in dark mode, so its rows bloom and are
  // spared more than the ground -- both means are measured through the real
  // entry point.
  {
    auto lum = [](int r, int g, int b) {
      auto ch = [](int v) {
        const float f = v / 255.0f;
        return f <= 0.04045f ? f / 12.92f : std::pow((f + 0.055f) / 1.055f, 2.4f);
      };
      return 0.2126f * ch(r) + 0.7152f * ch(g) + 0.0722f * ch(b);
    };
    const struct { int r, g, b, pr, pg, pb; } pages[] = {
        {0xC9, 0xE7, 0xFF, 0x14, 0x18, 0x1A},  // P4, 13.9:1
        {0x00, 0xFF, 0x97, 0x00, 0x19, 0x0A},  // P22G
        {0xFF, 0xB0, 0x00, 0x1A, 0x10, 0x00},  // P3
        {0x8B, 0x92, 0xFF, 0x00, 0x06, 0x1A},  // P11, 7.4:1 -- the tight one
        {0xFF, 0x6F, 0x6C, 0x1A, 0x03, 0x00},  // P22R
    };
    const int rungs[] = {0, 50, 100, 150};
    for (const auto &page : pages) {
      const float li = lum(page.r, page.g, page.b);
      const float lp = lum(page.pr, page.pg, page.pb);
      for (const int r : rungs) {
        Params p;
        p.intensityPercent = r;
        p.pitchPx = kPhonePitch;
        p.mottleDepth = mottleDepthFor(r);
        p.budgetMeanDarkening =
            0.8f * phosphorgrain::darkeningBudget(li, lp);
        const double mInk = meanRows(p, 0, 600, li) / 255.0;
        const double mPaper = meanRows(p, 0, 600, lp) / 255.0;
        const float ratio =
            (li * static_cast<float>(mInk) + 0.05f) /
            (lp * static_cast<float>(mPaper) + 0.05f);
        check(ratio >= 7.0f - 0.05f,
              "no offered rung drops a dark page under the contrast floor");
      }
    }
  }

  // --- THE CACHE SPLIT IS THE SAME MATH ------------------------------------
  // HalDisplay caches rowTransmission per (row, level bucket); combine() must
  // reproduce multiplierAt exactly or the shipped path silently diverges from
  // the tested one.
  {
    Params p;
    p.intensityPercent = 150;
    p.pitchPx = kPhonePitch;
    p.mottleDepth = 0.3f;
    bool same = true;
    for (int y = 0; y < 300; y += 2)
      for (int x = 0; x < W; x += 41)
        for (float level : {0.0f, 0.6f, 1.0f})
          if (multiplierAt(p, x, y, W, H, level) !=
              combine(p, rowTransmission(p, static_cast<float>(y), level), x, y,
                      W, H))
            same = false;
    check(same, "combine(rowTransmission) is exactly multiplierAt");
  }

  // --- FIXED TO THE GLASS, DIFFERENT SEED IS A DIFFERENT SCREEN ------------
  {
    Params a;
    a.intensityPercent = kIntensityStandard;
    a.pitchPx = kPhonePitch;
    a.mottleDepth = 0.3f;
    Params b = a;
    b.seed ^= 1u;
    bool stable = true;
    int differ = 0;
    for (int y = 0; y < 400; ++y)
      for (int x = 0; x < W; x += 47) {
        if (multiplierAt(a, x, y, W, H, 0.0f) !=
            multiplierAt(a, x, y, W, H, 0.0f))
          stable = false;
        if (multiplierAt(a, x, y, W, H, 0.0f) !=
            multiplierAt(b, x, y, W, H, 0.0f))
          differ++;
      }
    check(stable, "the raster is deterministic for a given pixel");
    check(differ > 400, "the seed actually re-rolls the screen");
  }

  // --- DEGENERATE GEOMETRY -------------------------------------------------
  {
    Params p;
    p.intensityPercent = kIntensityMax;
    p.pitchPx = kPhonePitch;
    check(multiplierAt(p, 0, 0, 0, 0, 0.0f) == 255,
          "a zero-sized surface is untouched");
    Params zeroPitch = p;
    zeroPitch.pitchPx = 0.0f;
    check(multiplierAt(zeroPitch, 0, 0, W, H, 0.0f) == 255,
          "a zero pitch is untouched rather than a divide");
  }

  if (failures == 0) std::printf("scanlines_test: all checks passed\n");
  return failures ? 1 : 0;
}
