// Host test for src/ShowThrough.h and the per-stock opacity it rides on.
//
// Every failure mode here is a wrong PICTURE or a broken floor. A pass that
// LIFTS is the page-flash bug class. An "off" that is nearly-off is a silent
// change to every install that never asked for this. A mirror applied in the
// wrong space is a page that shows through upside down, which reads as noise
// rather than as a leaf. A downsample that point-samples instead of averaging
// puts the 1-bit dither's lattice into a low-frequency field, which is ST-008
// arriving through the back door. And a share of the paper budget taken
// without being declared puts a reading page under 7:1. None of that compiles
// differently.

#include "ShowThrough.h"

#include "Letterpress.h"
#include "LightInkPalette.h"
#include "ContrastFloor.h"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>
#include "TestCheck.h"
using testcheck::check;

using namespace showthrough;

static int &failures = testcheck::g_failures;

// A synthetic page: horizontal ink bands on a paper ground, the statistics a
// real text block has (a line band every kLinePitch, ink for part of it).
// The pitch is the app's own: a body line at the shipped 2x render scale is
// ~44 framebuffer pixels tall with ~18 of ink, and the blur is tuned against
// that. A tighter synthetic grid would fail this test for being unlike a page.
static constexpr int FBW = 512, FBH = 528;
static constexpr int kLinePitch = 44;
static constexpr int kInkRows = 18;

static void makeTextPage(std::vector<uint8_t> &out, int leftMargin) {
  out.assign(static_cast<size_t>(FBW) * FBH, 0);
  for (int y = 0; y < FBH; ++y) {
    if ((y % kLinePitch) >= kInkRows) continue;  // between lines: bare paper
    uint8_t *row = out.data() + static_cast<size_t>(y) * FBW;
    for (int x = leftMargin; x < FBW - 40; ++x)
      row[x] = ((x / 3) % 2) ? 255 : 0;  // a dithered stroke pattern
  }
}

int main() {
  // --- OFF IS BIT-EXACT OFF -------------------------------------------------
  {
    Params off;
    off.strengthPercent = kStrengthOff;
    off.stockScale = 4.0f;
    bool allClear = true;
    for (int i = 0; i <= 100; ++i)
      if (multiplierAt(off, static_cast<float>(i) / 100.0f) != 255)
        allClear = false;
    check(allClear, "strength 0 is a bit-exact no-op at every verso density");
    check(effectiveDepth(off) == 0.0f, "strength 0 has exactly zero depth");
    check(meanDarkeningBound(off) == 0.0f,
          "strength 0 declares exactly zero of the paper budget");

    // ...and a stock that passes no light is off too, whatever the dial.
    Params opaque;
    opaque.strengthPercent = kStrengthMax;
    opaque.stockScale = 0.0f;
    bool opaqueClear = true;
    for (int i = 0; i <= 100; ++i)
      if (multiplierAt(opaque, static_cast<float>(i) / 100.0f) != 255)
        opaqueClear = false;
    check(opaqueClear, "a fully opaque stock shows nothing through, exactly");
  }

  // --- IT ONLY EVER DARKENS, AND NEVER TO NOTHING --------------------------
  {
    for (const int rung : {0, 50, 100, 200, 300}) {
      for (const float scale : {0.25f, 1.0f, 3.7f}) {
        Params p;
        p.strengthPercent = rung;
        p.stockScale = scale;
        int lo = 255, hi = 0;
        for (int i = 0; i <= 100; ++i) {
          const int m = multiplierAt(p, static_cast<float>(i) / 100.0f);
          if (m < lo) lo = m;
          if (m > hi) hi = m;
        }
        check(hi <= 255, "show-through never brightens a pixel");
        check(lo >= static_cast<int>(kMinMultiplier * 255.0f),
              "show-through never extinguishes a pixel");
      }
    }
    // Bare paper on the verso is EXACTLY untouched at every setting, or the
    // margins of every page would carry a uniform tint.
    Params p;
    p.strengthPercent = kStrengthMax;
    p.stockScale = 3.7f;
    check(multiplierAt(p, 0.0f) == 255,
          "zero verso density leaves the recto exactly alone");
  }

  // --- MONOTONE IN THE DENSITY, AND IN BOTH DIALS --------------------------
  {
    Params p;
    p.strengthPercent = kStrengthStandard;
    p.stockScale = 1.0f;
    int prev = 256;
    bool mono = true;
    for (int i = 0; i <= 100; ++i) {
      const int m = multiplierAt(p, static_cast<float>(i) / 100.0f);
      if (m > prev) mono = false;
      prev = m;
    }
    check(mono, "more ink on the verso is never less show-through");

    float lastDepth = -1.0f;
    bool depthMono = true;
    for (const int rung : {0, 50, 100, 150, 200}) {
      Params q;
      q.strengthPercent = rung;
      const float d = effectiveDepth(q);
      if (d < lastDepth) depthMono = false;
      lastDepth = d;
    }
    check(depthMono, "the strength ladder is monotone");

    lastDepth = -1.0f;
    depthMono = true;
    for (const float scale : {0.25f, 0.5f, 1.0f, 1.33f, 3.0f}) {
      Params q;
      q.strengthPercent = kStrengthStandard;
      q.stockScale = scale;
      const float d = effectiveDepth(q);
      if (d < lastDepth) depthMono = false;
      lastDepth = d;
    }
    check(depthMono, "a thinner stock is never less show-through");
  }

  // --- THE CAP HOLDS ------------------------------------------------------
  {
    Params p;
    p.strengthPercent = kStrengthMax;
    p.stockScale = 100.0f;  // absurd on purpose
    check(effectiveDepth(p) <= kDepthMax + 1e-6f,
          "no stock and no dial can take the depth past its cap");
  }

  // --- THE DOWNSAMPLE IS A BOX AVERAGE, NOT A POINT SAMPLE -----------------
  // This is the ST-008 lesson applied to a downsample. The page below is a
  // 1-bit dither at a 3 px period, and a point sample of it at a stride of 8
  // would return either 0 or 255 depending on phase -- carrying the dither's
  // lattice into a field that is supposed to have no lattice at all. The box
  // average returns the local COVERAGE, which is what a sheet actually passes.
  {
    std::vector<uint8_t> page;
    makeTextPage(page, 40);
    const int mw = mapDim(FBW), mh = mapDim(FBH);
    std::vector<uint8_t> map(static_cast<size_t>(mw) * mh);
    downsample(page.data(), FBW, FBH, map.data());

    // Inside a LINE BAND, well away from the margins, no cell may be a
    // saturated 0 or 255: every one straddles both dither phases, whatever its
    // phase against the 3 px stroke pattern. (Cells that sit wholly BETWEEN
    // lines are correctly 0 -- that is bare paper, not a sampling failure.)
    int extremes = 0, counted = 0;
    for (int my = 0; my < mh; ++my) {
      const int y0 = my * kCellPx;
      if (y0 % kLinePitch + kCellPx > kInkRows) continue;  // not all ink rows
      for (int mx = 8; mx < mw - 8; ++mx) {
        const int v = map[static_cast<size_t>(my) * mw + mx];
        counted++;
        if (v == 0 || v == 255) extremes++;
      }
    }
    check(counted > 0 && extremes == 0,
          "the downsample averages the dither rather than sampling it");

    // The LEFT MARGIN is empty on the verso and must stay empty: show-through
    // that follows the text block's shape is the entire point.
    double marginSum = 0.0;
    int marginN = 0;
    for (int my = 0; my < mh; ++my)
      for (int mx = 0; mx < 3; ++mx) {
        marginSum += map[static_cast<size_t>(my) * mw + mx];
        marginN++;
      }
    check(marginN > 0 && marginSum / marginN < 1.0,
          "a bare margin downsamples to nothing");
  }

  // --- THE BLUR KILLS LETTERS AND KEEPS LINE BANDS -------------------------
  {
    std::vector<uint8_t> page;
    makeTextPage(page, 40);
    const int mw = mapDim(FBW), mh = mapDim(FBH);
    std::vector<uint8_t> map(static_cast<size_t>(mw) * mh);
    std::vector<uint8_t> scratch(map.size());
    downsample(page.data(), FBW, FBH, map.data());

    // Horizontal variation INSIDE a line band, before and after: the letters.
    auto rowSwing = [&](int my) {
      int lo = 255, hi = 0;
      for (int mx = 10; mx < mw - 10; ++mx) {
        const int v = map[static_cast<size_t>(my) * mw + mx];
        if (v < lo) lo = v;
        if (v > hi) hi = v;
      }
      return hi - lo;
    };
    // Vertical variation down a column: the line grid.
    auto colSwing = [&](int mx) {
      int lo = 255, hi = 0;
      for (int my = 4; my < mh - 4; ++my) {
        const int v = map[static_cast<size_t>(my) * mw + mx];
        if (v < lo) lo = v;
        if (v > hi) hi = v;
      }
      return hi - lo;
    };
    const int colBefore = colSwing(mw / 2);
    blur(map.data(), mw, mh, scratch.data());
    const int rowAfter = rowSwing(mh / 2);
    const int colAfter = colSwing(mw / 2);

    check(colBefore > 40,
          "the unblurred map has a line grid to preserve (test premise)");
    check(colAfter > 12,
          "the blur keeps the LINE BAND structure -- what the eye reads");
    check(rowAfter < colAfter,
          "the blur takes the letters out harder than the lines");
  }

  // --- THE BLUR CANNOT INVENT INK, AND CANNOT MOVE IT OFF THE SHEET --------
  {
    std::vector<uint8_t> page;
    makeTextPage(page, 40);
    const int mw = mapDim(FBW), mh = mapDim(FBH);
    std::vector<uint8_t> map(static_cast<size_t>(mw) * mh);
    std::vector<uint8_t> scratch(map.size());
    downsample(page.data(), FBW, FBH, map.data());
    double before = 0.0;
    for (uint8_t v : map) before += v;
    blur(map.data(), mw, mh, scratch.data());
    double after = 0.0;
    int peak = 0;
    for (uint8_t v : map) {
      after += v;
      if (v > peak) peak = v;
    }
    // Edge clamping conserves rather than loses, and the rounding is symmetric,
    // so the totals stay within a fraction of a percent.
    check(std::fabs(after - before) / (before + 1.0) < 0.02,
          "the blur conserves the verso's total ink");
    check(peak <= 255, "the blur cannot push a cell past solid ink");
  }

  // --- BILINEAR SAMPLING, AND THE EDGES --------------------------------------
  {
    // A 2x2 map with known corners: the sample must interpolate between them
    // and must CLAMP outside rather than wrap.
    const uint8_t map[4] = {0, 255, 255, 0};
    check(std::fabs(sampleAt(map, 2, 2, 0.25f, 0.25f) - 0.0f) < 1e-5f,
          "a bilinear sample at a texel centre is that texel");
    check(std::fabs(sampleAt(map, 2, 2, 0.5f, 0.25f) - 0.5f) < 1e-3f,
          "a bilinear sample midway between two texels is their mean");
    check(sampleAt(map, 2, 2, -5.0f, 0.25f) == sampleAt(map, 2, 2, 0.0f, 0.25f),
          "sampling off the left edge clamps rather than wraps");
    check(sampleAt(map, 2, 2, 5.0f, 0.25f) == sampleAt(map, 2, 2, 1.0f, 0.25f),
          "sampling off the right edge clamps rather than wraps");
    check(sampleAt(nullptr, 2, 2, 0.5f, 0.5f) == 0.0f,
          "a map that does not exist shows nothing through");
  }

  // --- THE MIRROR IS AN INVOLUTION ON THE PAGE -----------------------------
  // It is the back of the sheet, so applying it twice is the sheet itself, and
  // the page's own edges must map to each other rather than off the page.
  {
    const int panelX = 137, panelW = 800;
    bool involution = true, inBounds = true, swapsEdges = true;
    for (int ox = panelX; ox < panelX + panelW; ++ox) {
      const int m = mirrorOutputX(ox, panelX, panelW);
      if (mirrorOutputX(m, panelX, panelW) != ox) involution = false;
      if (m < panelX || m >= panelX + panelW) inBounds = false;
    }
    if (mirrorOutputX(panelX, panelX, panelW) != panelX + panelW - 1)
      swapsEdges = false;
    if (mirrorOutputX(panelX + panelW - 1, panelX, panelW) != panelX)
      swapsEdges = false;
    check(involution, "mirroring the verso twice is the recto again");
    check(inBounds, "the mirror keeps every column on the page");
    check(swapsEdges, "the mirror swaps the page's left and right edges");
    check(mirrorOutputX(42, 0, 0) == 42,
          "a page with no width is not mirrored (no divide, no garbage)");
  }

  // --- THE PER-STOCK LADDER IS A RATIO OF TRANSMISSIONS ---------------------
  // The whole feature is that a bible paper shows a great deal through and a
  // calfskin almost nothing. If this ladder were flat the pass would be a
  // uniform smudge, and nothing else in the repo would notice.
  {
    using namespace lightink;
    check(std::fabs(showThroughScaleFor(kPaperBrightWhite, kPaperStrengthMax) -
                    1.0f) < 1e-5f,
          "the reference sheet is exactly 1.0x");
    check(showThroughScaleFor(kPaperIndia, kPaperStrengthMax) > 2.5f,
          "India paper shows far more through than the reference sheet");
    check(showThroughScaleFor(kPaperKozo, kPaperStrengthMax) >
              showThroughScaleFor(kPaperIndia, kPaperStrengthMax),
          "an open washi is thinner still than a bible sheet");
    check(showThroughScaleFor(kPaperVellum, kPaperStrengthMax) < 0.5f,
          "calfskin is nearly opaque");
    // At strength 0 every stock is the reference sheet, so the paper dial takes
    // a stock's thinness away with its tone -- the tooth/formation contract.
    bool zeroed = true;
    for (int i = 0; i < kPaperCount; ++i)
      if (std::fabs(showThroughScaleFor(i, 0) - 1.0f) > 1e-5f) zeroed = false;
    check(zeroed, "paper strength 0 is the reference sheet for every stock");
    // ...and monotone in between, or the slider would not read as one thing.
    bool ladderMono = true;
    for (int i = 0; i < kPaperCount; ++i) {
      const float target = showThroughScaleFor(i, kPaperStrengthMax);
      float last = 1.0f;
      for (int s = 0; s <= kPaperStrengthMax; s += 5) {
        const float v = showThroughScaleFor(i, s);
        if (target >= 1.0f ? (v < last - 1e-5f) : (v > last + 1e-5f))
          ladderMono = false;
        last = v;
      }
    }
    check(ladderMono, "the paper dial moves every stock's show-through one way");
    // Every opacity is a real fraction. A stock at 1.0 would be a mirror.
    bool sane = true;
    for (int i = 0; i < kPaperCount; ++i)
      if (!(kPapers[i].opacity > 0.5f && kPapers[i].opacity < 1.0f)) sane = false;
    check(sane, "every stock's opacity is a plausible ISO 2471 fraction");
  }

  // --- NO OFFERED SETTING TAKES ANY LIGHT PAGE UNDER THE FLOOR -------------
  // The tightest pairs this repo ships, measured through the real entry point
  // at the real mean verso density of a text page. Show-through darkens PAPER,
  // so it spends the same budget the tooth, the wires and the marks spend --
  // and the budget it is HANDED is what holds the floor, structurally.
  {
    auto lum = [](int r, int g, int b) {
      auto ch = [](int v) {
        const float f = v / 255.0f;
        return f <= 0.04045f ? f / 12.92f : std::pow((f + 0.055f) / 1.055f, 2.4f);
      };
      return 0.2126f * ch(r) + 0.7152f * ch(g) + 0.0722f * ch(b);
    };
    // The five tightest ink x paper pairs on the shipped tables, plus the
    // shipped default. Chamois is the darkest sheet and sets most floors.
    using namespace lightink;
    const struct { int ink, paper; } pairs[] = {
        {kInkStandard, kPaperBrightWhite}, {kInkWalnutBistre, kPaperChamois},
        {kInkVanDyke, kPaperChamois},      {kInkDavysGray, kPaperNewsprint},
        {kInkSanguine, kPaperLaidAntique}, {kInkVanDyke, kPaperKozo},
    };
    // A page's mean verso density after the blur, measured off the synthetic
    // text page above rather than assumed.
    std::vector<uint8_t> page;
    makeTextPage(page, 40);
    const int mw = mapDim(FBW), mh = mapDim(FBH);
    std::vector<uint8_t> map(static_cast<size_t>(mw) * mh);
    std::vector<uint8_t> scratch(map.size());
    downsample(page.data(), FBW, FBH, map.data());
    blur(map.data(), mw, mh, scratch.data());

    for (const auto &pair : pairs) {
      uint8_t ink[3], paper[3];
      paperAtStrength(pair.paper, kPaperStrengthMax, paper);
      inkAtDensity(pair.ink, pair.paper, kDensityMax, ink, kPaperStrengthMax);
      const float li = lum(ink[0], ink[1], ink[2]);
      const float lp = lum(paper[0], paper[1], paper[2]);
      // What the tooth, at its heaviest offered setting, leaves. Deliberately
      // pessimistic: the caller hands this pass HALF of that, and here it is
      // handed all of it.
      const float budget = letterpress::paperBudget(li, lp);
      for (const int rung : {0, 50, 100, 200, 300}) {
        for (int stock = 0; stock < kPaperCount; ++stock) {
          Params p;
          p.strengthPercent = rung;
          p.stockScale = showThroughScaleFor(stock, kPaperStrengthMax);
          p.budgetMeanDarkening = budget;
          // The MEAN multiplier over the whole sheet, at this page's densities.
          double sum = 0.0;
          for (uint8_t v : map)
            sum += multiplierAt(p, static_cast<float>(v) / 255.0f);
          const double mPaper = sum / (map.size() * 255.0);
          // Ink is masked by nothing here -- the harshest reading, since
          // darkening the ink would only raise the ratio.
          const float ratio = static_cast<float>(
              (lp * mPaper + 0.05) / (li + 0.05));
          check(ratio >= static_cast<float>(wcag::kContrastFloorAAA) - 0.05f,
                "no offered show-through on any stock drops a light page "
                "under the contrast floor");
        }
      }
    }
  }

  // --- THE DECLARED SHARE BOUNDS THE REAL ONE ------------------------------
  // meanDarkeningBound is what HalDisplay subtracts before the marks are
  // generated. If the real mean ever exceeded it the marks would be sized
  // against headroom that no longer exists.
  {
    std::vector<uint8_t> page;
    makeTextPage(page, 20);  // a wide, dense block -- near the worst case
    const int mw = mapDim(FBW), mh = mapDim(FBH);
    std::vector<uint8_t> map(static_cast<size_t>(mw) * mh);
    std::vector<uint8_t> scratch(map.size());
    downsample(page.data(), FBW, FBH, map.data());
    blur(map.data(), mw, mh, scratch.data());
    Params p;
    p.strengthPercent = kStrengthMax;
    p.stockScale = 3.7f;
    double sum = 0.0;
    for (uint8_t v : map) sum += 1.0 - multiplierAt(p, v / 255.0f) / 255.0;
    const double realMean = sum / map.size();
    check(realMean <= meanDarkeningBound(p) + 1e-6,
          "the declared share of the paper budget bounds the real one");
  }

  if (failures == 0) std::printf("show_through_test: all checks passed\n");
  return failures == 0 ? 0 : 1;
}
