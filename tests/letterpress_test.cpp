// Host test for src/Letterpress.h.
//
// Every failure mode of this file is a wrong PICTURE -- a ring that lifts
// instead of darkens, a deboss with no direction, tooth that drags a tight
// palette under the floor. No compiler and no other test can see any of it.
// Same reason PhosphorGrain, PadPalette and PanelPalette have theirs.

#include "Letterpress.h"

#include <cmath>
#include <cstdio>
#include <vector>

using namespace letterpress;

static int failures = 0;

static void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    failures++;
  }
}

// A synthetic page: 64x64 of paper with a filled 24x24 ink square at [20,44).
// Inkness is exactly 0 or 1, the way a 1-bit glyph interior is.
struct Page {
  static constexpr int N = 64;
  float t[N][N];
  Page() {
    for (int y = 0; y < N; ++y)
      for (int x = 0; x < N; ++x)
        t[y][x] = (x >= 20 && x < 44 && y >= 20 && y < 44) ? 1.0f : 0.0f;
  }
  void window(int x, int y, float win[3][3]) const {
    for (int dy = -1; dy <= 1; ++dy)
      for (int dx = -1; dx <= 1; ++dx) {
        int sx = x + dx, sy = y + dy;
        if (sx < 0) sx = 0;
        if (sy < 0) sy = 0;
        if (sx >= N) sx = N - 1;
        if (sy >= N) sy = N - 1;
        win[dy + 1][dx + 1] = t[sy][sx];
      }
  }
};

static uint8_t at(const Params &p, const Page &pg, int x, int y) {
  float win[3][3];
  pg.window(x, y, win);
  return multiplierAt(p, win, x, y, Page::N, Page::N);
}

static double meanOver(const Params &p, const Page &pg, int x0, int y0, int x1,
                       int y1) {
  double sum = 0.0;
  int n = 0;
  for (int y = y0; y < y1; ++y)
    for (int x = x0; x < x1; ++x) {
      sum += at(p, pg, x, y);
      n++;
    }
  return sum / n;
}

int main() {
  const Page pg;

  // --- OFF IS BIT-EXACT OFF -------------------------------------------------
  {
    Params off{kStrengthOff, 0x50524553u, 1.0f};
    bool allClear = true;
    for (int y = 0; y < Page::N; ++y)
      for (int x = 0; x < Page::N; ++x)
        if (at(off, pg, x, y) != 255) allClear = false;
    check(allClear, "strength 0 is a bit-exact no-op everywhere on the page");
  }

  // --- IT ONLY EVER DARKENS, AND NEVER TO NOTHING --------------------------
  {
    Params p{kStrengthMax, 0x50524553u, 1.0f};
    int lo = 255;
    for (int y = 0; y < Page::N; ++y)
      for (int x = 0; x < Page::N; ++x) {
        const int m = at(p, pg, x, y);
        if (m < lo) lo = m;
      }
    check(lo >= static_cast<int>(kMinMultiplier * 255.0f),
          "letterpress never extinguishes a texel, even at the clamp maximum");
  }

  // --- THE RING DARKENS THE INK-PAPER BOUNDARY, NOT THE FLAT AREAS ---------
  {
    Params p{kStrengthStandard, 0x50524553u, 1.0f};
    // Ink pixels ON the boundary vs deep interior.
    double rim = 0.0;
    int rimN = 0;
    for (int x = 21; x < 43; ++x) {
      rim += at(p, pg, x, 20);  // top row of the ink square
      rim += at(p, pg, x, 43);  // bottom row
      rimN += 2;
    }
    rim /= rimN;
    const double interior = meanOver(p, pg, 26, 26, 38, 38);
    check(rim < interior - 20.0,
          "the squeeze ring darkens the stroke's rim well below its interior");

    // Flat paper far from any edge: tooth only, which is bounded by its
    // amplitude at this rung.
    double paperLo = 255.0;
    for (int y = 0; y < 16; ++y)
      for (int x = 0; x < 16; ++x)
        if (at(p, pg, x, y) < paperLo) paperLo = at(p, pg, x, y);
    check(paperLo >= 255.0 * (1.0 - kToothAt100) - 1.0,
          "flat paper beyond the band carries only tooth, nothing else");

    // Flat ink interior: pressure + in-stroke noise only, no ring.
    double inkLo = 255.0;
    for (int y = 28; y < 36; ++y)
      for (int x = 28; x < 36; ++x)
        if (at(p, pg, x, y) < inkLo) inkLo = at(p, pg, x, y);
    check(inkLo >= 255.0 * (1.0 - kPressAt100 - kIrregularAt100) - 1.0,
          "flat ink carries only pressure and in-stroke noise, no ring");
  }

  // --- THE DEBOSS HAS A DIRECTION ------------------------------------------
  // Light from the top-left: the paper just ABOVE the glyph (its shadowed
  // top wall) darkens; the paper just BELOW it (the lit wall, whose highlight
  // a darken-only pass cannot paint) stays untouched but for tooth.
  {
    Params p{kStrengthStandard, 0x50524553u, 1.0f};
    double above = 0.0, below = 0.0;
    int n = 0;
    for (int x = 22; x < 42; ++x) {
      above += at(p, pg, x, 19);  // paper row above the top edge
      below += at(p, pg, x, 44);  // paper row below the bottom edge
      n++;
    }
    check(above / n < below / n - 10.0,
          "the deboss shadow falls on the top wall, not the bottom one");
  }

  // --- THE LADDER IS MONOTONE AND EVERY RUNG IS DISTINCT -------------------
  {
    const int rungs[] = {0, 50, 100, 200};
    double prev = -1.0;
    bool monotone = true, distinct = true;
    for (const int r : rungs) {
      Params p{r, 0x50524553u, 1.0f};
      const double darkening = 255.0 - meanOver(p, pg, 0, 0, Page::N, Page::N);
      if (darkening < prev) monotone = false;
      if (prev >= 0.0 && darkening - prev < 0.5) distinct = false;
      prev = darkening;
    }
    check(monotone, "more dial is never less letterpress");
    check(distinct, "every offered rung is visibly its own setting");
  }

  // --- NO OFFERED RUNG TAKES ANY LIGHT PALETTE UNDER THE FLOOR -------------
  // The ink side darkening RAISES a light page's contrast; the paper side is
  // the hazard, and Latte light (7.06:1) has almost no room. The budget clamp
  // is what holds it, structurally -- the same shape as the grain's
  // budgetSigma. Swept through the real entry point on flat paper.
  {
    auto lum = [](int r, int g, int b) {
      auto ch = [](int v) {
        const float f = v / 255.0f;
        return f <= 0.04045f ? f / 12.92f : std::pow((f + 0.055f) / 1.055f, 2.4f);
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
    const int rungs[] = {0, 50, 100, 200};
    for (const auto &page : pages) {
      const float li = lum(page.r, page.g, page.b);
      const float lp = lum(page.pr, page.pg, page.pb);
      for (const int r : rungs) {
        Params p{r, 0x50524553u, paperBudget(li, lp)};
        const double mPaper = meanOver(p, pg, 0, 0, 16, 16) / 255.0;
        const float ratio = (lp * static_cast<float>(mPaper) + 0.05f) /
                            (li + 0.05f);
        check(ratio >= kContrastFloor - 0.05f,
              "no offered rung drags flat paper under the contrast floor");
      }
    }
    // A pair already under the floor gets no paper budget at all.
    check(paperBudget(lum(0x80, 0x80, 0x80), lum(0x90, 0x90, 0x90)) == 0.0f,
          "a pair under the floor gets zero paper budget, not a negative one");
  }

  // --- FIXED TO THE PAGE, NOT TO THE FRAME ---------------------------------
  {
    Params p{kStrengthStandard, 0x50524553u, 1.0f};
    bool stable = true;
    for (int i = 0; i < 3; ++i)
      for (int y = 0; y < Page::N; y += 5)
        for (int x = 0; x < Page::N; x += 7)
          if (at(p, pg, x, y) != at(p, pg, x, y)) stable = false;
    check(stable, "letterpress is deterministic for a given pixel");
  }

  // --- A DIFFERENT SEED IS A DIFFERENT PRESSING ----------------------------
  {
    Params a{kStrengthStandard, 0x50524553u, 1.0f};
    Params b{kStrengthStandard, 0x50524554u, 1.0f};
    int differ = 0;
    for (int y = 0; y < Page::N; ++y)
      for (int x = 0; x < Page::N; ++x)
        if (at(a, pg, x, y) != at(b, pg, x, y)) differ++;
    check(differ > Page::N * Page::N / 8, "the seed actually re-rolls the noise");
  }

  // --- DEGENERATE GEOMETRY -------------------------------------------------
  {
    Params p{kStrengthMax, 0x50524553u, 1.0f};
    float win[3][3] = {{0, 0, 0}, {0, 1, 0}, {0, 0, 0}};
    check(multiplierAt(p, win, 0, 0, 0, 0) == 255,
          "a zero-sized panel is untouched");
    check(multiplierAt(p, win, 0, 0, -3, 5) == 255,
          "a negative-sized panel is untouched");
  }

  // --- THE SHEET SPLIT (owner 2026-08-22: "make sure panel and paper -------
  // actually match visually, in color and texture with light mode").
  // The panel field with includeTooth=false must leave FLAT PAPER untouched
  // exactly -- every remaining component is carried by ink or its edges -- so
  // the only texture on paper, inside or outside the page's rect, is the one
  // output-wide sheet field, and the boundary cannot seam by construction.
  {
    Params p{kStrengthMax, 0x50524553u, 1.0f, false};
    bool clean = true;
    for (int y = 0; y < 16; ++y)
      for (int x = 0; x < 16; ++x)
        if (at(p, pg, x, y) != 255) clean = false;
    check(clean, "panel field without tooth leaves flat paper bit-exact");
    // ...while the glyph-edge components still paint.
    check(at(p, pg, 30, 20) < 255,
          "panel field without tooth still darkens the stroke's rim");
  }

  // The sheet-tooth field itself: off is bit-exact, it only darkens, it is
  // real texture (not flat), and it is STATIONARY -- block means across an
  // arbitrary boundary agree, which is the no-discontinuity half of the seam
  // claim (the other half is the bit-exact flat paper above).
  {
    Params off{kStrengthOff, 0x50524553u, 1.0f};
    Params p{kStrengthStandard, 0x50524553u, 1.0f};
    bool offClean = true, darkenOnly = true;
    double sumL = 0.0, sumR = 0.0;
    int lo = 255, hi = 0;
    const int N = 64;
    for (int y = 0; y < N; ++y)
      for (int x = 0; x < 2 * N; ++x) {
        if (sheetToothMultiplierAt(off, x, y) != 255) offClean = false;
        const int m = sheetToothMultiplierAt(p, x, y);
        if (m > 255) darkenOnly = false;
        if (m < lo) lo = m;
        if (m > hi) hi = m;
        (x < N ? sumL : sumR) += m;
      }
    check(offClean, "sheet tooth at strength 0 is a bit-exact no-op");
    check(darkenOnly && hi <= 255, "sheet tooth can only darken");
    check(hi > lo, "sheet tooth carries real texture, not a flat fill");
    const double meanL = sumL / (N * N), meanR = sumR / (N * N);
    check(std::abs(meanL - meanR) < 1.0,
          "sheet tooth is stationary: block means agree across any boundary");
    // Mean darkening bounded by the model: uniform [0, a] noise means a/2,
    // with a = kToothAt100 at the standard rung.
    check(255.0 - meanL <= 255.0 * kToothAt100 / 2.0 + 1.0,
          "sheet tooth mean darkening stays within the model's amplitude");
  }

  // The sheet field obeys the same paper budget as the in-panel term did:
  // swept against the tight palette (Latte light, 7.06:1), the flat sheet
  // must hold the floor at every offered rung.
  {
    auto lum = [](int r, int g, int b) {
      auto ch = [](int v) {
        const float f = v / 255.0f;
        return f <= 0.04045f ? f / 12.92f : std::pow((f + 0.055f) / 1.055f, 2.4f);
      };
      return 0.2126f * ch(r) + 0.7152f * ch(g) + 0.0722f * ch(b);
    };
    const float li = lum(0x4C, 0x4F, 0x69);   // Latte ink
    const float lp = lum(0xEF, 0xF1, 0xF5);   // Latte paper
    const int rungs[] = {0, 50, 100, 200, 400};
    for (const int r : rungs) {
      Params p{r, 0x50524553u, paperBudget(li, lp)};
      double sum = 0.0;
      for (int y = 0; y < 64; ++y)
        for (int x = 0; x < 64; ++x) sum += sheetToothMultiplierAt(p, x, y);
      const double mPaper = sum / (64.0 * 64.0 * 255.0);
      const float ratio =
          (lp * static_cast<float>(mPaper) + 0.05f) / (li + 0.05f);
      check(ratio >= kContrastFloor - 0.05f,
            "no offered rung drags the flat SHEET under the contrast floor");
    }
  }

  if (failures == 0) std::printf("letterpress_test: all checks passed\n");
  return failures ? 1 : 0;
}
