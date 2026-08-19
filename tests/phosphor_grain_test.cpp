// Host test for src/PhosphorGrain.h.
//
// Every failure mode of this file is a wrong PICTURE. It cannot fail to
// compile, it cannot throw, and the desktop build will render something either
// way -- so a known-answer test is the only instrument that can see it at all.
// Same reason PadPalette and PanelPalette have theirs.

#include "PhosphorGrain.h"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

using namespace phosphorgrain;

static int failures = 0;

static void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    failures++;
  }
}

static void checkNear(double got, double want, double tol, const char *what) {
  if (!(std::fabs(got - want) <= tol)) {
    std::printf("FAIL: %s (got %.6f, want %.6f +/- %.6f)\n", what, got, want,
                tol);
    failures++;
  }
}

struct Stats {
  double mean = 0.0;
  double stddev = 0.0;
  int lo = 255;
  int hi = 0;
};

// Statistics of the multiplier over a rectangle, as a FRACTION (0..1).
static Stats sample(const Params &p, int w, int h, int x0, int y0, int x1,
                    int y1) {
  Stats s;
  double sum = 0.0, sum2 = 0.0;
  int n = 0;
  for (int y = y0; y < y1; ++y) {
    for (int x = x0; x < x1; ++x) {
      const int m = multiplierAt(p, x, y, w, h);
      if (m < s.lo) s.lo = m;
      if (m > s.hi) s.hi = m;
      const double f = m / 255.0;
      sum += f;
      sum2 += f * f;
      n++;
    }
  }
  s.mean = sum / n;
  s.stddev = std::sqrt(sum2 / n - s.mean * s.mean);
  return s;
}

int main() {
  const int W = 512, H = 512;

  // --- OFF IS BIT-EXACT OFF -------------------------------------------------
  // Not "almost 255". An install that turns grain off must render byte-for-byte
  // what it rendered before this feature existed, on every coverage.
  for (int c = 0; c < kCoverageCount; ++c) {
    Params off{kStrengthOff, static_cast<Coverage>(c), 0x43524F53u};
    bool allClear = true;
    for (int y = 0; y < H; y += 3)
      for (int x = 0; x < W; x += 3)
        if (multiplierAt(off, x, y, W, H) != 255) allClear = false;
    check(allClear, "strength 0 is a bit-exact no-op on every coverage");
  }

  // --- THE DIAL IS THE DIAL ------------------------------------------------
  checkNear(sigmaFor(kStrengthRealistic), kRealisticSigma, 1e-7,
            "1x is exactly the realistic sigma");
  checkNear(sigmaFor(kStrengthOff), 0.0, 1e-7, "0x is zero sigma");
  checkNear(sigmaFor(kStrengthMax), kRealisticSigma * 10.0f, 1e-6,
            "10x is ten times realistic");
  checkNear(sigmaFor(-500), 0.0, 1e-7, "negative strength clamps to off");
  checkNear(sigmaFor(99999), kRealisticSigma * 10.0f, 1e-6,
            "strength above max clamps to 10x");
  check(clampCoverage(-1) == Even && clampCoverage(kCoverageCount) == Even,
        "an out-of-range coverage integer falls back to Even, not to garbage");

  // --- IT ONLY EVER DARKENS ------------------------------------------------
  // The whole reason this is a modulate and not an add: a multiplier above 1
  // would lift pixels the page left dark, which is the grey-background and
  // page-flash bug class this repo has already shipped twice.
  {
    Params p{kStrengthMax, VignetteMottled, 0x43524F53u};
    Stats s = sample(p, W, H, 0, 0, W, H);
    check(s.hi <= 255, "grain never brightens a texel, even at 10x");
    check(s.lo >= static_cast<int>(kMinMultiplier * 255.0f),
          "grain never extinguishes a texel: a dead pixel is a defect, not "
          "grain");
  }

  // --- IT IS FIXED TO THE GLASS, NOT TO THE FRAME --------------------------
  // Same pixel, same answer, every call. Animated noise is beam-current noise,
  // a different phenomenon, and it would make a still page flicker.
  {
    Params p{kStrengthRealistic, Mottled, 0x43524F53u};
    bool stable = true;
    for (int i = 0; i < 4; ++i)
      for (int y = 0; y < H; y += 61)
        for (int x = 0; x < W; x += 37)
          if (multiplierAt(p, x, y, W, H) != multiplierAt(p, x, y, W, H))
            stable = false;
    check(stable, "grain is deterministic for a given pixel");
  }

  // --- THE CELL IS kCellPx WIDE -------------------------------------------
  // If this regressed to 1 the grain would drop below acuity and read as a
  // uniform dimming, which is exactly the flatness the feature exists to fix.
  {
    Params p{kStrengthRealistic, Even, 0x43524F53u};
    bool cellsHold = true;
    for (int y = 0; y < H; y += kCellPx * 7)
      for (int x = 0; x < W; x += kCellPx * 7)
        for (int dy = 0; dy < kCellPx; ++dy)
          for (int dx = 0; dx < kCellPx; ++dx)
            if (multiplierAt(p, x + dx, y + dy, W, H) !=
                multiplierAt(p, x, y, W, H))
              cellsHold = false;
    check(cellsHold, "a grain cell is kCellPx square and uniform inside");
    check(multiplierAt(p, 0, 0, W, H) != multiplierAt(p, kCellPx, 0, W, H) ||
              multiplierAt(p, 0, 0, W, H) !=
                  multiplierAt(p, 0, kCellPx, W, H),
          "adjacent cells differ (the field is noise, not a constant)");
  }

  // --- THE DISTRIBUTION IS THE ONE CLAIMED --------------------------------
  // Half-normal attenuation: mean deficit ~ 0.8*sigma, spread ~ 0.6*sigma.
  // Bounds are loose because the generator is Irwin-Hall n=3 (exactly bounded
  // at +/-3 sigma by construction) rather than a true normal.
  {
    Params p{kStrengthRealistic, Even, 0x43524F53u};
    Stats s = sample(p, W, H, 0, 0, W, H);
    const double sigma = sigmaFor(kStrengthRealistic);
    const double deficit = 1.0 - s.mean;
    check(deficit > 0.70 * sigma && deficit < 0.90 * sigma,
          "mean attenuation is the half-normal's ~0.8 sigma");
    check(s.stddev > 0.50 * sigma && s.stddev < 0.70 * sigma,
          "spread is the half-normal's ~0.6 sigma");
    check(deficit < 0.05,
          "at realistic strength the page loses under 5% of its light");
  }

  // --- 10x IS TEN TIMES, NOT 'MORE' ---------------------------------------
  {
    Params one{kStrengthRealistic, Even, 0x43524F53u};
    Params ten{kStrengthMax, Even, 0x43524F53u};
    const double d1 = 1.0 - sample(one, W, H, 0, 0, W, H).mean;
    const double d10 = 1.0 - sample(ten, W, H, 0, 0, W, H).mean;
    checkNear(d10 / d1, 10.0, 0.5, "the dial is linear from 0x to 10x");
  }

  // --- VIGNETTE LEAVES THE READING AREA ALONE ------------------------------
  // Ruling: grain rises at the rim, and the middle of the page -- the part
  // being read -- is exactly what Even would have drawn there.
  {
    Params even{kStrengthRealistic, Even, 0x43524F53u};
    Params vig{kStrengthRealistic, Vignette, 0x43524F53u};
    check(multiplierAt(vig, W / 2, H / 2, W, H) ==
              multiplierAt(even, W / 2, H / 2, W, H),
          "vignette is a no-op at the exact center");

    Stats center = sample(vig, W, H, W * 3 / 8, H * 3 / 8, W * 5 / 8, H * 5 / 8);
    Stats corner = sample(vig, W, H, 0, 0, W / 8, H / 8);
    check(corner.mean < center.mean,
          "the corner is dimmer than the center under Vignette");
    check(corner.stddev > center.stddev * 1.5,
          "the corner is grainier than the center under Vignette");

    // The corner dim is bounded: this is a page of text, not a monitor test
    // card, and a real tube's corner runs 70-85% of center.
    Stats c10 = sample(Params{kStrengthMax, Vignette, 0x43524F53u}, W, H, 0, 0,
                       W / 8, H / 8);
    check(c10.mean > 0.35,
          "even at 10x the corner keeps most of its light");
  }

  // --- MOTTLE IS LOW-FREQUENCY, AND COSTS NOTHING ON AVERAGE ---------------
  // Blotches are what stop the page reading as a fill. The instrument is the
  // spread of BLOCK means: per-pixel spread cannot tell a blotchy field from an
  // even one, which is the whole point of the distinction.
  {
    Params even{kStrengthMax, Even, 0x43524F53u};
    Params mot{kStrengthMax, Mottled, 0x43524F53u};
    // The deepest offered swing, so the structure is unambiguous.
    mot.mottleCells = 8;
    mot.mottleDepth = 0.30f;
    auto blockSpread = [&](const Params &p) {
      std::vector<double> means;
      const int B = 32;
      for (int by = 0; by + B <= H; by += B)
        for (int bx = 0; bx + B <= W; bx += B)
          means.push_back(sample(p, W, H, bx, by, bx + B, by + B).mean);
      double m = 0.0;
      for (double v : means) m += v;
      m /= means.size();
      double v2 = 0.0;
      for (double v : means) v2 += (v - m) * (v - m);
      return std::sqrt(v2 / means.size());
    };
    const double evenSpread = blockSpread(even);
    const double motSpread = blockSpread(mot);
    check(motSpread > evenSpread * 1.5,
          "Mottled carries real low-frequency structure; Even does not");

    const double evenMean = sample(even, W, H, 0, 0, W, H).mean;
    const double motMean = sample(mot, W, H, 0, 0, W, H).mean;
    checkNear(motMean, evenMean, 0.05,
              "mottle redistributes grain, it does not add a net dimming");
  }

  // --- DEPTH 0 IS EXACTLY EVEN --------------------------------------------
  // The offered depths start at 0, and 0 has to mean "no blotches at all"
  // rather than "very few": a Mottled coverage at depth 0 must render
  // byte-for-byte what Even renders, or the setting has a silent floor.
  {
    Params even{kStrengthRealistic, Even, 0x43524F53u};
    for (const int cells : {8, 16, 32}) {
      Params mot{kStrengthRealistic, Mottled, 0x43524F53u};
      mot.mottleCells = cells;
      mot.mottleDepth = 0.0f;
      bool identical = true;
      for (int y = 0; y < H; y += 5)
        for (int x = 0; x < W; x += 5)
          if (multiplierAt(mot, x, y, W, H) != multiplierAt(even, x, y, W, H))
            identical = false;
      check(identical, "mottle depth 0 is bit-exact Even at every cell count");
    }
    Params vm{kStrengthRealistic, VignetteMottled, 0x43524F53u};
    vm.mottleDepth = 0.0f;
    Params vig{kStrengthRealistic, Vignette, 0x43524F53u};
    bool same = true;
    for (int y = 0; y < H; y += 7)
      for (int x = 0; x < W; x += 7)
        if (multiplierAt(vm, x, y, W, H) != multiplierAt(vig, x, y, W, H))
          same = false;
    check(same, "depth 0 leaves Vignette+Mottled exactly Vignette");
  }

  // --- BOTH MOTTLE DIALS ACTUALLY BITE -------------------------------------
  // Each offered value must produce a different field from its neighbours, or
  // a settings row is decoration.
  {
    auto fieldOf = [&](int cells, float depth) {
      Params p{kStrengthRealistic, Mottled, 0x43524F53u};
      p.mottleCells = cells; p.mottleDepth = depth;
      std::vector<uint8_t> f;
      for (int y = 0; y < H; y += 4)
        for (int x = 0; x < W; x += 4) f.push_back(multiplierAt(p, x, y, W, H));
      return f;
    };
    const float depths[] = {0.0f, 0.03f, 0.10f, 0.30f};
    for (const int cells : {8, 16, 32})
      for (int i = 1; i < 4; i++)
        check(fieldOf(cells, depths[i]) != fieldOf(cells, depths[i - 1]),
              "each offered mottle depth differs from the one below it");
    for (const float d : {0.03f, 0.10f, 0.30f}) {
      check(fieldOf(8, d) != fieldOf(16, d) && fieldOf(16, d) != fieldOf(32, d),
            "each offered cell count differs from its neighbour");
    }
  }

  // --- THE PARAMETERS ARE CLAMPED, NOT TRUSTED -----------------------------
  {
    check(clampMottleCells(0) == kMottleCellsMin &&
              clampMottleCells(1 << 20) == kMottleCellsMax,
          "a garbage cell count clamps rather than dividing by zero");
    check(clampMottleDepth(-1.0f) == 0.0f && clampMottleDepth(9.0f) == kMottleDepthMax,
          "a garbage depth clamps into range");
    check(clampMottleDepth(std::nanf("")) == 0.0f,
          "NaN depth falls back to no mottle rather than propagating");
  }

  // --- A DIFFERENT SEED IS A DIFFERENT SCREEN ------------------------------
  {
    Params a{kStrengthRealistic, Even, 0x43524F53u};
    Params b{kStrengthRealistic, Even, 0x43524F54u};
    int differ = 0;
    for (int y = 0; y < H; y += kCellPx)
      for (int x = 0; x < W; x += kCellPx)
        if (multiplierAt(a, x, y, W, H) != multiplierAt(b, x, y, W, H)) differ++;
    check(differ > (W / kCellPx) * (H / kCellPx) / 4,
          "the seed actually re-rolls the field");
  }

  // --- DEGENERATE GEOMETRY IS NOT A CRASH AND NOT A BLACK PAGE -------------
  {
    Params p{kStrengthMax, VignetteMottled, 0x43524F53u};
    check(multiplierAt(p, 0, 0, 0, 0) == 255, "a zero-sized panel is untouched");
    check(multiplierAt(p, 0, 0, -4, 10) == 255,
          "a negative-sized panel is untouched");
  }

  if (failures == 0) std::printf("phosphor_grain_test: all checks passed\n");
  return failures ? 1 : 0;
}
