// Host test for src/Scanlines.h.
//
// Every failure mode of this file is a wrong PICTURE -- a beat against the
// fractional presentation (the ST-008 class), a bloom that lifts instead of
// sparing, a mottle that nets brightening, a tight palette dragged under the
// floor. Same reason PhosphorGrain has its test.

#include "Scanlines.h"
#include "ContrastFloor.h"

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
    // Swept across the SIZE ladder too: a coarser pitch darkens the page more
    // (the mean gap grows with the pitch), so a floor proved at one pitch says
    // nothing about the others. The budget cap is pitch-independent, which is
    // exactly the claim under test.
    const int rungs[] = {0, 50, 100, 150};
    const int sizes[] = {kSizeFine, kSizeMedium, kSizeCoarse, kSizeChunky};
    for (const auto &page : pages) {
      const float li = lum(page.r, page.g, page.b);
      const float lp = lum(page.pr, page.pg, page.pb);
      for (const int r : rungs) {
        for (const int sz : sizes) {
          Params p;
          p.intensityPercent = r;
          p.pitchPx = pitchFor(kPhonePitch, sz);
          p.mottleDepth = mottleDepthFor(r);
          p.budgetMeanDarkening =
              0.8f * phosphorgrain::darkeningBudget(li, lp);
          const double mInk = meanRows(p, 0, 600, li) / 255.0;
          const double mPaper = meanRows(p, 0, 600, lp) / 255.0;
          const float ratio =
              (li * static_cast<float>(mInk) + 0.05f) /
              (lp * static_cast<float>(mPaper) + 0.05f);
          check(ratio >= static_cast<float>(wcag::kContrastFloorAAA) - 0.05f,
                "no offered rung at any size drops a dark page under the "
                "contrast floor");
        }
      }
    }
  }

  // --- THE PITCH LADDER: MULTIPLES OF THE SOURCE-ROW PITCH -----------------
  // Owner order 2026-08-22 ("scanlines need a sizing setting"). Offered as
  // MULTIPLES of the lattice the panel already resamples on -- 1x, 1.5x, 2x,
  // 3x -- never absolute pixels. pitchFor is the whole seam: Params keeps one
  // final device-pixel pitch, so nothing downstream can hold two numbers that
  // disagree.
  {
    check(pitchFor(kPhonePitch, kSizeFine) == kPhonePitch,
          "the default size is exactly the source-row pitch (build 126)");
    check(std::fabs(pitchFor(kPhonePitch, kSizeMedium) - kPhonePitch * 1.5f) <
              1e-4f,
          "Medium is one line per 1.5 source rows");
    check(std::fabs(pitchFor(kPhonePitch, kSizeCoarse) - kPhonePitch * 2.0f) <
              1e-4f,
          "Coarse is one line per 2 source rows");
    check(std::fabs(pitchFor(kPhonePitch, kSizeChunky) - kPhonePitch * 3.0f) <
              1e-4f,
          "Chunky is one line per 3 source rows");
    check(pitchFor(kPhonePitch, 0) == kPhonePitch &&
              pitchFor(kPhonePitch, -400) == kPhonePitch,
          "a nonsense size clamps to the finest pitch, never to zero lines");
    check(pitchFor(kPhonePitch, 9000) == kPhonePitch * 3.0f,
          "the size clamps at the coarsest offered rung");
    check(pitchFor(0.0f, kSizeChunky) == 0.0f,
          "no source-row pitch is no pitch, not a divide");
  }

  // --- EVERY RUNG IS ITS OWN SETTING, AND COARSER MEANS MORE RASTER --------
  // Two things, both silent if wrong: a rung that renders like its neighbour
  // is a decoration row, and a ladder that is not monotone in coarseness means
  // the labels lie about which way the dial goes. Measured on the shipped
  // entry point at a flat dark ground.
  {
    const int sizes[] = {kSizeFine, kSizeMedium, kSizeCoarse, kSizeChunky};
    double prevDark = -1.0, prevPitch = -1.0;
    bool monotone = true, distinct = true, structural = true;
    for (const int sz : sizes) {
      Params p;
      p.intensityPercent = kIntensityStandard;
      p.pitchPx = pitchFor(kPhonePitch, sz);
      p.phaseJitterFrac = 0.0f;
      p.thickJitter = 0.0f;
      if (p.pitchPx <= prevPitch) monotone = false;
      prevPitch = p.pitchPx;
      // Line structure has to stay RESOLVED as the pitch coarsens -- the "is
      // 3x chunky vintage or stripes with gaps" question. Peak-to-peak down
      // one stretch of panel, and the DUTY: sigma is a fraction of pitch, so
      // the lit fraction must not drift as the lines fatten.
      int lo = 255, hi = 0, lit = 0, n = 0;
      for (int y = 0; y < 600; ++y) {
        const int m = multiplierAt(p, 0, y, W, H, 0.06f);
        if (m < lo) lo = m;
        if (m > hi) hi = m;
      }
      for (int y = 0; y < 600; ++y) {
        const int m = multiplierAt(p, 0, y, W, H, 0.06f);
        if (m > (lo + hi) / 2) lit++;
        n++;
      }
      const double duty = static_cast<double>(lit) / n;
      if (hi - lo < 40 || duty < 0.35 || duty > 0.70) structural = false;
      const double darkening = 255.0 - meanRows(p, 0, 600, 0.06f);
      if (darkening < prevDark) monotone = false;
      if (prevDark >= 0.0 && darkening - prevDark < 1.0) distinct = false;
      prevDark = darkening;
    }
    check(monotone, "coarser size is never less raster, and never less pitch");
    check(distinct, "every offered size is visibly its own setting");
    check(structural,
          "every size keeps resolved lines at a ~half-lit duty: chunky, not "
          "stripes with gaps");
  }

  // --- NO RUNG BEATS: THE ST-008 PIN, GENERALIZED OVER THE LADDER ----------
  // The original pin was a single pitch. Every rung has to hold it, or the
  // sizing setting is a way to ask for the moire back. Window means ~10
  // periods wide, flat down the whole panel; jitter off so this measures the
  // integrator rather than the intended irregularity.
  {
    for (const int sz : {kSizeFine, kSizeMedium, kSizeCoarse, kSizeChunky}) {
      Params p;
      p.intensityPercent = kIntensityStandard;
      p.pitchPx = pitchFor(kPhonePitch, sz);
      p.phaseJitterFrac = 0.0f;
      p.thickJitter = 0.0f;
      const int win = static_cast<int>(10.0f * p.pitchPx + 0.5f);
      double lo = 255.0, hi = 0.0;
      for (int y0 = 0; y0 + win <= H; y0 += win) {
        const double m = meanRows(p, y0, y0 + win, 0.0f);
        if (m < lo) lo = m;
        if (m > hi) hi = m;
      }
      check(hi - lo < 255.0 * 0.015,
            "no offered size introduces a long-period beat down the panel");
    }
  }

  // --- THE PITCH IS THE ONLY THING THE SIZE CHANGES ------------------------
  // A size of 100 must be BIT-EXACT what build 126 shipped, and OFF must stay
  // bit-exact off at every size -- an install that turned scanlines off cannot
  // start seeing them because a second dial exists.
  {
    Params shipped;
    shipped.intensityPercent = kIntensityStandard;
    shipped.pitchPx = kPhonePitch;
    shipped.mottleDepth = mottleDepthFor(kIntensityStandard);
    Params viaSize = shipped;
    viaSize.pitchPx = pitchFor(kPhonePitch, kSizeFine);
    bool same = true;
    for (int y = 0; y < H; y += 5)
      for (int x = 0; x < W; x += 29)
        if (multiplierAt(shipped, x, y, W, H, 0.3f) !=
            multiplierAt(viaSize, x, y, W, H, 0.3f))
          same = false;
    check(same, "size 100 is bit-exact the pitch build 126 shipped");

    bool offClear = true;
    for (const int sz : {kSizeFine, kSizeMedium, kSizeCoarse, kSizeChunky}) {
      Params off;
      off.intensityPercent = kIntensityOff;
      off.pitchPx = pitchFor(kPhonePitch, sz);
      off.mottleDepth = kMottleDepthMax;
      for (int y = 0; y < H; y += 7)
        for (int x = 0; x < W; x += 41)
          for (float level : {0.0f, 0.5f, 1.0f})
            if (multiplierAt(off, x, y, W, H, level) != 255) offClear = false;
    }
    check(offClear, "off is bit-exact off at every size");
  }

  // --- THE BLOOM LADDER ----------------------------------------------------
  // Owner order 2026-08-22 ("add another ios app settings for selecting bloom
  // values with scanlines"). Off has to be BIT-EXACT off, which for bloom
  // means the field stops depending on `level` at all -- a tiny residual gain
  // would leave a content-aware raster that the row claims is not one.
  {
    check(bloomGainFor(kBloomStandard) == kBloomGain,
          "Standard is exactly the gain build 126 shipped");
    check(bloomGainFor(kBloomOff) == 0.0f, "Off is a zero gain, exactly");
    check(bloomGainFor(-50) == 0.0f && bloomGainFor(9000) ==
              kBloomGain * static_cast<float>(kBloomExtreme) / 100.0f,
          "the bloom percent clamps to the ladder's ends");

    Params off;
    off.intensityPercent = kIntensityStandard;
    off.pitchPx = kPhonePitch;
    off.mottleDepth = mottleDepthFor(kIntensityStandard);
    off.bloomGain = bloomGainFor(kBloomOff);
    bool contentBlind = true;
    for (int y = 0; y < H; y += 3)
      for (int x = 0; x < W; x += 37)
        for (float level : {0.25f, 0.5f, 1.0f})
          if (multiplierAt(off, x, y, W, H, level) !=
              multiplierAt(off, x, y, W, H, 0.0f))
            contentBlind = false;
    check(contentBlind,
          "bloom Off leaves a field that cannot see the page at all");

    // Monotone and distinct, INTEGRATED OVER THE LEVEL RANGE -- which is the
    // only measure that tells the ladder apart, and the fact is worth stating
    // rather than hiding behind a passing check. At full white the shipped
    // gain ALREADY closes the gap completely (37.2 levels spared at 1x), so
    // Standard, Strong and Extreme are identical there and a level-1.0 test
    // would call three real rungs decoration. What the upper rungs actually
    // buy is the MID-TONES: at level 0.2 the sparing runs 5.0 / 9.9 / 19.5 /
    // 35.3 across Subtle / Standard / Strong / Extreme. Averaged over levels
    // 0.1..1.0 the ladder is 0 / 13.4 / 24.3 / 31.6 / 35.2.
    const int rungs[] = {kBloomOff, kBloomSubtle, kBloomStandard, kBloomStrong,
                         kBloomExtreme};
    double prev = -1.0;
    bool monotone = true, distinct = true;
    for (const int r : rungs) {
      Params p;
      p.intensityPercent = kIntensityStandard;
      p.pitchPx = kPhonePitch;
      p.phaseJitterFrac = 0.0f;
      p.thickJitter = 0.0f;
      p.bloomGain = bloomGainFor(r);
      const double dark = meanRows(p, 0, 600, 0.0f);
      double spared = 0.0;
      for (int i = 1; i <= 10; ++i)
        spared += meanRows(p, 0, 600, static_cast<float>(i) / 10.0f) - dark;
      spared /= 10.0;
      if (spared < prev) monotone = false;
      if (prev >= 0.0 && spared - prev < 1.0) distinct = false;
      prev = spared;
    }
    check(monotone, "more bloom never spares a row less, at any brightness");
    check(distinct,
          "every offered bloom rung is its own setting once measured across "
          "the level range, not only at full white where it saturates");
  }

  // --- BLOOM IS A FRACTION OF PITCH, NOT A PIXEL COUNT ---------------------
  // Two claims, and they are not the same claim.
  //
  // (a) THE GEOMETRY IS EXACTLY PROPORTIONATE. Bloom widens sigma, and sigma
  //     is kSigmaFrac * pitch, so the spot's width AS A FRACTION OF PITCH is
  //     identical at every size by construction. This is what makes a per-rung
  //     retune unnecessary; it is an identity, and it is pinned exactly.
  // (b) THE RENDERED EFFECT IS ONLY NEARLY SO, and the reason is the pixel
  //     grid rather than the bloom. A device-pixel row is 42% of a 2.39 px
  //     pitch but 14% of a 7.16 px one, so the box integral smears the fine
  //     raster more and leaves it less to spare. Measured at Subtle, the
  //     fraction of available darkening that bloom returns runs 0.645 / 0.557
  //     / 0.527 / 0.507 across the four sizes -- a 0.138 spread, monotone with
  //     pitch, which is the sampling and not a scale error. Pinned at 0.20 so
  //     a genuine pixel-count regression (which would run the other way and
  //     much further) still fails.
  {
    for (const int sz : {kSizeFine, kSizeMedium, kSizeCoarse, kSizeChunky}) {
      const float pitch = pitchFor(kPhonePitch, sz);
      for (const int b : {kBloomSubtle, kBloomStandard, kBloomStrong}) {
        const float sigmaAtFull =
            kSigmaFrac * pitch * (1.0f + bloomGainFor(b) * 1.0f);
        check(std::fabs(sigmaAtFull / pitch -
                        kSigmaFrac * (1.0f + bloomGainFor(b))) < 1e-6f,
              "the bloomed spot is the same fraction of pitch at every size");
      }
    }
    for (const int b : {kBloomSubtle, kBloomStandard, kBloomStrong}) {
      double lo = 1e9, hi = -1e9;
      for (const int sz : {kSizeFine, kSizeMedium, kSizeCoarse, kSizeChunky}) {
        Params p;
        p.intensityPercent = kIntensityStandard;
        p.pitchPx = pitchFor(kPhonePitch, sz);
        p.phaseJitterFrac = 0.0f;
        p.thickJitter = 0.0f;
        p.bloomGain = bloomGainFor(b);
        const double dark = 255.0 - meanRows(p, 0, 600, 0.0f);
        const double bright = 255.0 - meanRows(p, 0, 600, 1.0f);
        const double frac = dark > 0.0 ? (dark - bright) / dark : 0.0;
        if (frac < lo) lo = frac;
        if (frac > hi) hi = frac;
      }
      check(hi - lo < 0.20,
            "bloom reads proportionate at every pitch: the residual spread is "
            "the pixel grid, not a pixel-count bloom");
    }
  }

  // --- BLOOM CANNOT LIFT A PIXEL, AT ANY RUNG OR SIZE ----------------------
  // The darken-only doctrine. Bloom redistributes within the line -- it
  // darkens the gap LESS near bright content -- and an additive pass is the
  // page-flash bug class. 255 is untouched; nothing may exceed it, and no
  // level may ever read brighter than the same pixel unmodulated.
  {
    bool neverLifts = true;
    for (const int b : {kBloomOff, kBloomSubtle, kBloomStandard, kBloomStrong,
                        kBloomExtreme})
      for (const int sz : {kSizeFine, kSizeCoarse, kSizeChunky}) {
        Params p;
        p.intensityPercent = kIntensityMax;
        p.pitchPx = pitchFor(kPhonePitch, sz);
        p.mottleDepth = kMottleDepthMax;
        p.bloomGain = bloomGainFor(b);
        for (int y = 0; y < 800; ++y)
          for (int x = 0; x < W; x += 53)
            for (float level : {0.0f, 0.5f, 1.0f})
              if (multiplierAt(p, x, y, W, H, level) > 255) neverLifts = false;
      }
    check(neverLifts, "no bloom rung at any size lifts a pixel above 1.0");
  }

  // --- THE FLOOR, SWEPT OVER THE WHOLE BLOOM x PITCH MATRIX ----------------
  // Bloom spares the INK (bright in dark mode) more than the ground, so it can
  // only widen the ratio -- but "can only" is the sort of claim that is worth
  // one loop rather than one sentence.
  {
    auto lum = [](int r, int g, int b) {
      auto ch = [](int v) {
        const float f = v / 255.0f;
        return f <= 0.04045f ? f / 12.92f : std::pow((f + 0.055f) / 1.055f, 2.4f);
      };
      return 0.2126f * ch(r) + 0.7152f * ch(g) + 0.0722f * ch(b);
    };
    const struct { int r, g, b, pr, pg, pb; } pages[] = {
        {0x8B, 0x92, 0xFF, 0x00, 0x06, 0x1A},  // P11, 7.4:1 -- the tight one
        {0xFF, 0x6F, 0x6C, 0x1A, 0x03, 0x00},  // P22R
    };
    for (const auto &page : pages) {
      const float li = lum(page.r, page.g, page.b);
      const float lp = lum(page.pr, page.pg, page.pb);
      for (const int r : {0, 50, 100, 150})
        for (const int sz : {kSizeFine, kSizeMedium, kSizeCoarse, kSizeChunky})
          for (const int b : {kBloomOff, kBloomSubtle, kBloomStandard,
                              kBloomStrong, kBloomExtreme}) {
            Params p;
            p.intensityPercent = r;
            p.pitchPx = pitchFor(kPhonePitch, sz);
            p.mottleDepth = mottleDepthFor(r);
            p.bloomGain = bloomGainFor(b);
            p.budgetMeanDarkening =
                0.8f * phosphorgrain::darkeningBudget(li, lp);
            const double mInk = meanRows(p, 0, 600, li) / 255.0;
            const double mPaper = meanRows(p, 0, 600, lp) / 255.0;
            const float ratio = (li * static_cast<float>(mInk) + 0.05f) /
                                (lp * static_cast<float>(mPaper) + 0.05f);
            check(ratio >= static_cast<float>(wcag::kContrastFloorAAA) - 0.05f,
                  "no bloom x pitch x intensity combination drops a dark page "
                  "under the contrast floor");
          }
    }
  }

  // --- THE FIELD IS GLASS, NOT PHOSPHOR: NO PERSISTENCE --------------------
  // Owner ruling 2026-08-22: "scanlines should not be persisting, that is
  // handled by crt guns." The raster is a static screen structure; the light
  // behind it decays, the structure does not. The model has no clock at all,
  // so the pin that matters is that nothing in it CACHES: hash the whole field,
  // evaluate a few thousand calls at other params, hash it again. A hidden
  // static -- the shape a "make it evolve" change would take -- moves the
  // second hash.
  {
    Params p;
    p.intensityPercent = kIntensityStandard;
    p.pitchPx = kPhonePitch;
    p.mottleDepth = mottleDepthFor(kIntensityStandard);
    auto hashField = [&](const Params &q) {
      uint64_t h = 1469598103934665603ull;
      for (int y = 0; y < 400; ++y)
        for (int x = 0; x < W; x += 13) {
          h ^= multiplierAt(q, x, y, W, H, 0.2f);
          h *= 1099511628211ull;
        }
      return h;
    };
    const uint64_t first = hashField(p);
    // Everything a decaying page does to this module: different levels, a
    // different pitch, a different intensity, a different seed.
    for (int k = 0; k < 40; ++k) {
      Params q = p;
      q.pitchPx = pitchFor(kPhonePitch, kSizeFine + k * 5);
      q.intensityPercent = 50 + k;
      q.seed ^= static_cast<uint32_t>(k);
      (void)multiplierAt(q, k, k * 3, W, H, static_cast<float>(k % 11) / 10.0f);
    }
    check(hashField(p) == first,
          "the field is time-invariant: nothing in the model carries state "
          "between calls, so a fading page cannot fade or drift the raster");

    // ...and the light behind it IS allowed to move: the same static field
    // must give different answers for different content levels, which is what
    // makes the ghost decay VISIBLE through an unchanging raster.
    Params bright = p;
    check(hashField(p) != hashField(bright) ||
              multiplierAt(p, 0, 100, W, H, 0.0f) !=
                  multiplierAt(p, 0, 100, W, H, 1.0f),
          "a static field still modulates changing light behind it");
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
