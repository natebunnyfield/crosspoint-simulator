// Host test for src/PaperDefects.h, and for the budget arithmetic it shares
// with src/Letterpress.h.
//
// Every failure mode here is invisible to a compiler and to every other test in
// this repo. A defect layer that LIFTS instead of darkening is the page-flash
// bug class. A dial-0 that is nearly-off instead of bit-exact silently changes
// every install that turned it off. A mark that outlives the paper's remaining
// budget puts a reading page under 7:1 -- and the tooth's clamp is CONDITIONAL,
// so an arithmetic that assumes it always bites asserts a bound the tooth does
// not obey above a budget of 0.5. A page whose seed still carries grainSeed()
// looks completely correct and fails the one claim the feature exists for.
//
// Same reason phosphor_grain, letterpress, panel_palette and pad_palette have
// theirs.

#include "PaperDefects.h"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

#include "Letterpress.h"

static int failures = 0;

static void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    failures++;
  }
}

// --- the sheet, exactly as HalDisplay builds it -----------------------------
//
// Tooth first, per pixel, then each mark over its own bounding box. Held here
// rather than only in HalDisplay.cpp because the safety claim is about the
// COMPOSITE: neither layer alone is what a reader looks at.
struct Sheet {
  int w = 0, h = 0;
  std::vector<uint8_t> r, g, b;
};

// inknessAt: 0 is bare paper, 1 is solid ink. A null function means bare sheet
// everywhere, which is the worst case for the paper's contrast floor.
template <typename InkFn>
static Sheet buildSheet(const letterpress::Params &lp,
                        const paperdefects::Params &dp, int w, int h,
                        InkFn inknessAt) {
  Sheet s;
  s.w = w;
  s.h = h;
  s.r.resize(static_cast<size_t>(w) * h);
  s.g.resize(s.r.size());
  s.b.resize(s.r.size());
  for (int y = 0; y < h; ++y)
    for (int x = 0; x < w; ++x) {
      const uint8_t m = letterpress::sheetToothMultiplierAt(lp, x, y, w, h);
      const size_t i = static_cast<size_t>(y) * w + x;
      s.r[i] = s.g[i] = s.b[i] = m;
    }
  paperdefects::Mark marks[paperdefects::kMaxMarks];
  const int n = paperdefects::generate(dp, w, h, marks);
  for (int k = 0; k < n; ++k) {
    int x0, y0, x1, y1;
    if (!paperdefects::bounds(marks[k], w, h, x0, y0, x1, y1)) continue;
    for (int y = y0; y < y1; ++y)
      for (int x = x0; x < x1; ++x) {
        float mult[3];
        if (!paperdefects::multiplierAt(marks[k], x, y, mult)) continue;
        paperdefects::applyInkMask(mult, inknessAt(x, y));
        const size_t i = static_cast<size_t>(y) * w + x;
        auto fold = [](uint8_t base, float f) {
          const int v = static_cast<int>(static_cast<float>(base) * f + 0.5f);
          return static_cast<uint8_t>(v < 0 ? 0 : (v > 255 ? 255 : v));
        };
        s.r[i] = fold(s.r[i], mult[0]);
        s.g[i] = fold(s.g[i], mult[1]);
        s.b[i] = fold(s.b[i], mult[2]);
      }
  }
  return s;
}

static Sheet bareSheet(const letterpress::Params &lp,
                       const paperdefects::Params &dp, int w, int h) {
  return buildSheet(lp, dp, w, h, [](int, int) { return 0.0f; });
}

static bool sameSheet(const Sheet &a, const Sheet &b) {
  return a.w == b.w && a.h == b.h && a.r == b.r && a.g == b.g && a.b == b.b;
}

// Mean LUMINANCE darkening of the composite, over bare paper. The figure the
// contrast floor is denominated in.
static double meanDarkening(const Sheet &s) {
  double sum = 0.0;
  for (size_t i = 0; i < s.r.size(); ++i)
    sum += 0.2126 * s.r[i] + 0.7152 * s.g[i] + 0.0722 * s.b[i];
  return 1.0 - sum / (255.0 * static_cast<double>(s.r.size()));
}

static float lumOf(int r, int g, int b) {
  auto ch = [](int v) {
    const float f = static_cast<float>(v) / 255.0f;
    return f <= 0.04045f ? f / 12.92f
                         : std::pow((f + 0.055f) / 1.055f, 2.4f);
  };
  return 0.2126f * ch(r) + 0.7152f * ch(g) + 0.0722f * ch(b);
}

// The page seed exactly as HalDisplay computes it: no launch term at all.
static uint32_t pageSeed(uint64_t bookKey, int spine, int page) {
  return phosphorgrain::hash3(
      static_cast<uint32_t>(bookKey & 0xFFFFFFFFu),
      static_cast<uint32_t>(bookKey >> 32) ^ static_cast<uint32_t>(spine),
      static_cast<uint32_t>(page));
}

int main() {
  // ---------------------------------------------------------------- OFF ----
  {
    letterpress::Params lp;
    lp.strengthPercent = 100;
    lp.paperDarkenBudget = 0.5f;
    paperdefects::Params off;
    off.dialPercent = paperdefects::kDialOff;
    off.seed = 12345u;
    off.remainingBudget = letterpress::remainingPaperBudget(lp);
    paperdefects::Params on = off;
    on.dialPercent = paperdefects::kDialDefault;

    paperdefects::Mark marks[paperdefects::kMaxMarks];
    check(paperdefects::generate(off, 400, 300, marks) == 0,
          "dial 0 generates no marks at all");

    // BIT-EXACT: the sheet at dial 0 is byte-for-byte the tooth alone, which is
    // what keeps the desktop canary and every existing capture unchanged.
    const Sheet a = bareSheet(lp, off, 320, 240);
    letterpress::Params lpOnly = lp;
    paperdefects::Params none = off;
    const Sheet toothOnly = bareSheet(lpOnly, none, 320, 240);
    check(sameSheet(a, toothOnly), "dial 0 is bit-exact the tooth alone");
    check(!sameSheet(a, bareSheet(lp, on, 320, 240)),
          "dial 30 actually paints something");
  }

  // ------------------------------------------------------- DETERMINISM ----
  //
  // The headline claim. A page is the same sheet forever: same identity, same
  // field; any component of the identity moving, a different field. The seed
  // deliberately carries NO launch term, which is the half that a
  // launch-seeded build would still pass every other check in this file with.
  {
    letterpress::Params lp;
    lp.strengthPercent = 100;
    lp.paperDarkenBudget = 0.5f;
    paperdefects::Params p;
    p.dialPercent = 60;
    p.remainingBudget = letterpress::remainingPaperBudget(lp);

    const uint64_t bookA = 0x0123456789ABCDEFull;
    const uint64_t bookB = 0x0123456789ABCDEEull;  // one bit apart

    p.seed = pageSeed(bookA, 3, 17);
    const Sheet s1 = bareSheet(lp, p, 300, 220);
    p.seed = pageSeed(bookA, 3, 17);
    const Sheet s2 = bareSheet(lp, p, 300, 220);
    check(sameSheet(s1, s2), "same page identity -> byte-identical sheet");

    p.seed = pageSeed(bookA, 3, 18);
    check(!sameSheet(s1, bareSheet(lp, p, 300, 220)),
          "next page in the same spine is a different sheet");
    p.seed = pageSeed(bookA, 4, 17);
    check(!sameSheet(s1, bareSheet(lp, p, 300, 220)),
          "same page number in another spine is a different sheet");
    p.seed = pageSeed(bookB, 3, 17);
    check(!sameSheet(s1, bareSheet(lp, p, 300, 220)),
          "another book is a different sheet");

    // ...and the seed is not accidentally degenerate across a run of pages.
    std::vector<uint32_t> seen;
    for (int spine = 0; spine < 8; ++spine)
      for (int page = 0; page < 40; ++page)
        seen.push_back(pageSeed(bookA, spine, page));
    bool anyDup = false;
    for (size_t i = 0; i < seen.size() && !anyDup; ++i)
      for (size_t j = i + 1; j < seen.size() && !anyDup; ++j)
        if (seen[i] == seen[j]) anyDup = true;
    check(!anyDup, "320 consecutive page identities give 320 distinct seeds");
  }

  // ------------------------------------------------------- DARKEN ONLY ----
  //
  // A multiplier above 1 is the additive lift that produced both the page-flash
  // and the gray-background reports. Checked on every channel, at every dial,
  // over every mark this model can make.
  {
    for (int dial = 0; dial <= paperdefects::kDialMax; dial += 5) {
      for (uint32_t seed = 1; seed <= 24; ++seed) {
        paperdefects::Params p;
        p.dialPercent = dial;
        p.seed = seed * 2654435761u;
        p.remainingBudget = 1.0f;
        paperdefects::Mark marks[paperdefects::kMaxMarks];
        const int n = paperdefects::generate(p, 500, 380, marks);
        for (int k = 0; k < n; ++k) {
          int x0, y0, x1, y1;
          if (!paperdefects::bounds(marks[k], 500, 380, x0, y0, x1, y1))
            continue;
          for (int y = y0; y < y1; ++y)
            for (int x = x0; x < x1; ++x) {
              float m[3];
              if (!paperdefects::multiplierAt(marks[k], x, y, m)) {
                check(m[0] == 1.0f && m[1] == 1.0f && m[2] == 1.0f,
                      "a pixel outside a mark is exactly 1 on every channel");
                continue;
              }
              for (int c = 0; c < 3; ++c) {
                check(m[c] <= 1.0f, "a defect can only ever darken");
                check(m[c] >= paperdefects::kMinMultiplier,
                      "a defect never goes under its own floor");
              }
            }
        }
      }
    }
  }

  // ------------------------------------------------------ THE OWN FLOOR ----
  //
  // This layer's floor is DELIBERATELY below letterpress::kMinMultiplier, whose
  // comment forbids specks by name. A fly speck is that speck.
  {
    check(paperdefects::kMinMultiplier < letterpress::kMinMultiplier,
          "the defect floor sits below the letterpress floor");
    const float speckDeficit =
        1.0f - paperdefects::kKinds[paperdefects::FlySpeck].tint[1];
    check(1.0f - speckDeficit < letterpress::kMinMultiplier,
          "a fly speck at full depth is darker than letterpress may go");
  }

  // ----------------------------------------------------- THE INK MASK -----
  {
    float m[3] = {0.20f, 0.30f, 0.40f};
    paperdefects::applyInkMask(m, 1.0f);
    check(m[0] == 1.0f && m[1] == 1.0f && m[2] == 1.0f,
          "inkness 1 leaves the multiplier exactly 1 on every channel");
    float m2[3] = {0.20f, 0.30f, 0.40f};
    paperdefects::applyInkMask(m2, 0.0f);
    check(m2[0] == 0.20f && m2[1] == 0.30f && m2[2] == 0.40f,
          "inkness 0 leaves the multiplier untouched");
    float m3[3] = {0.20f, 0.20f, 0.20f};
    paperdefects::applyInkMask(m3, 0.5f);
    check(m3[0] > 0.20f && m3[0] < 1.0f, "the mask fades, it does not switch");
    // ...and the composite really is untouched under solid ink.
    letterpress::Params lp;
    lp.strengthPercent = 100;
    lp.paperDarkenBudget = 0.5f;
    paperdefects::Params dp;
    dp.dialPercent = 100;
    dp.seed = 77u;
    dp.remainingBudget = letterpress::remainingPaperBudget(lp);
    paperdefects::Params zero = dp;
    zero.dialPercent = 0;
    const Sheet inked =
        buildSheet(lp, dp, 240, 200, [](int, int) { return 1.0f; });
    const Sheet clean = bareSheet(lp, zero, 240, 200);
    check(sameSheet(inked, clean),
          "a fully inked sheet is byte-identical to no defects at all");
  }

  // -------------------------------------------------------- INCIDENCE -----
  {
    check(paperdefects::countFor(paperdefects::Foxing, 30) <
              paperdefects::countFor(paperdefects::Foxing, 100),
          "foxing is rarer at 30 than at 100");
    int total30 = 0, total100 = 0;
    for (int k = 0; k < paperdefects::kKindCount; ++k) {
      total30 += paperdefects::countFor(k, 30);
      total100 += paperdefects::countFor(k, 100);
    }
    check(total30 * 2 < total100,
          "the whole ladder is measurably sparser at 30 than at 100");
    for (int k = 0; k < paperdefects::kKindCount; ++k)
      check(paperdefects::countFor(k, 100) > 0,
            "every offered defect kind actually appears at dial 100");
    // Every rung differs from its neighbour somewhere, or the slider is
    // decoration between those two values.
    letterpress::Params lp;
    lp.strengthPercent = 100;
    lp.paperDarkenBudget = 0.5f;
    int painted[5] = {0, 0, 0, 0, 0};
    const int rungs[5] = {0, 25, 50, 75, 100};
    for (int i = 0; i < 5; ++i) {
      paperdefects::Params p;
      p.dialPercent = rungs[i];
      p.seed = 4242u;
      p.remainingBudget = letterpress::remainingPaperBudget(lp);
      paperdefects::Mark marks[paperdefects::kMaxMarks];
      painted[i] = paperdefects::generate(p, 800, 600, marks);
    }
    for (int i = 1; i < 5; ++i)
      check(painted[i] > painted[i - 1],
            "each dial rung paints strictly more than the one below it");
  }

  // ------------------------------------------------- BOUNDS ARE HONEST ----
  //
  // The rasterizer only visits each mark's bounding box, so a box that clips
  // the footprint silently truncates marks -- which looks like a rendering
  // artifact, not like a bug in a bounds function.
  {
    paperdefects::Params p;
    p.dialPercent = 100;
    p.remainingBudget = 1.0f;
    for (uint32_t seed = 1; seed <= 12; ++seed) {
      p.seed = seed * 40503u + 7u;
      paperdefects::Mark marks[paperdefects::kMaxMarks];
      const int n = paperdefects::generate(p, 400, 300, marks);
      for (int k = 0; k < n; ++k) {
        int x0, y0, x1, y1;
        const bool any = paperdefects::bounds(marks[k], 400, 300, x0, y0, x1, y1);
        for (int y = 0; y < 300; ++y)
          for (int x = 0; x < 400; ++x) {
            float m[3];
            if (!paperdefects::multiplierAt(marks[k], x, y, m)) continue;
            check(any && x >= x0 && x < x1 && y >= y0 && y < y1,
                  "every painted pixel lies inside the mark's bounding box");
          }
      }
    }
  }

  // ------------------------------------------------ THE SHARED BUDGET -----
  //
  // The proof with teeth, and F7's correction is the whole of it: the tooth's
  // clamp is CONDITIONAL (Letterpress.h clamps only when budget < 0.5), so both
  // regimes are swept EXPLICITLY rather than sampled and hoped over.
  {
    struct Pal { const char *name; int ink[3]; int paper[3]; };
    const Pal pals[] = {
        {"black on white",   {0x00, 0x00, 0x00}, {0xFF, 0xFF, 0xFF}},
        {"repo default",     {0x2D, 0x2D, 0x2D}, {0xFB, 0xFB, 0xF9}},
        {"latte",            {0x4C, 0x4F, 0x69}, {0xEF, 0xF1, 0xF5}},
        {"sepia ink on tan", {0x3A, 0x2E, 0x22}, {0xEA, 0xDF, 0xC6}},
        {"iron gall on rag", {0x2A, 0x2A, 0x3A}, {0xF2, 0xEC, 0xDC}},
        {"at the floor",     {0x5A, 0x5A, 0x5A}, {0xE8, 0xE8, 0xE8}},
    };
    int sawTight = 0, sawLoose = 0;
    const int strengths[] = {50, 100, 200, 400};
    const int tooths[] = {60, 100, 180, 400};
    const int dials[] = {0, 30, 60, 100};
    for (const Pal &pal : pals) {
      const float li = lumOf(pal.ink[0], pal.ink[1], pal.ink[2]);
      const float lp_ = lumOf(pal.paper[0], pal.paper[1], pal.paper[2]);
      const float budget = letterpress::paperBudget(li, lp_);
      if (budget < 0.5f) sawTight++; else sawLoose++;
      for (const int st : strengths)
        for (const int tooth : tooths)
          for (const int dial : dials) {
            letterpress::Params lp;
            lp.strengthPercent = st;
            lp.seed = 0x50524553u;
            lp.paperDarkenBudget = budget;
            lp.toothScale = static_cast<float>(tooth) / 100.0f;
            lp.formationDepth = 0.0f;  // isolated below; mean-preserving there
            const float remaining = letterpress::remainingPaperBudget(lp);
            check(remaining <= budget + 1e-6f,
                  "the remainder never exceeds the whole budget");
            check(remaining >= 0.0f, "the remainder is never negative");

            paperdefects::Params dp;
            dp.dialPercent = dial;
            dp.seed = pageSeed(0xFEEDFACEull, st, dial + tooth);
            dp.remainingBudget = remaining;

            const Sheet s = bareSheet(lp, dp, 340, 260);
            const double mean = meanDarkening(s);
            // THE BOUND: tooth (a/2, post-clamp) plus the defects' measured
            // share must fit inside what the palette can afford.
            check(mean <= static_cast<double>(budget) + 0.004,
                  "tooth + defects stay inside the palette's paper budget");
            // ...and the page really does still clear the floor -- for the
            // palettes that clear it to begin with. paperBudget() answers 0
            // for one that does NOT (the "at the floor" row is there
            // deliberately, to prove the layer vanishes rather than to be
            // rescued), and no amount of not-darkening can lift a palette the
            // owner chose under 7:1.
            if (budget > 0.0f) {
              const float ratio =
                  (lp_ * static_cast<float>(1.0 - mean) + 0.05f) / (li + 0.05f);
              check(ratio >= letterpress::kContrastFloor - 0.05f,
                    "no (palette, strength, tooth, dial) state drags the flat "
                    "sheet under 7:1");
            }
          }
    }
    check(sawTight > 0, "the sweep includes palettes in the clamped regime");
    check(sawLoose > 0, "the sweep includes palettes in the unclamped regime");
  }

  // A palette with NOTHING left hands the defect layer nothing, and it obeys.
  {
    letterpress::Params lp;
    lp.strengthPercent = 100;
    lp.paperDarkenBudget = 0.0f;
    paperdefects::Params dp;
    dp.dialPercent = 100;
    dp.seed = 999u;
    dp.remainingBudget = letterpress::remainingPaperBudget(lp);
    check(dp.remainingBudget == 0.0f, "a palette at the floor leaves nothing");
    paperdefects::Mark marks[paperdefects::kMaxMarks];
    const int n = paperdefects::generate(dp, 400, 300, marks);
    for (int k = 0; k < n; ++k)
      check(marks[k].depth == 0.0f,
            "with no budget left every mark is scaled to nothing");
    paperdefects::Params zero = dp;
    zero.dialPercent = 0;
    check(sameSheet(bareSheet(lp, dp, 200, 160), bareSheet(lp, zero, 200, 160)),
          "a zero-budget palette renders exactly the tooth alone");
  }

  // The analytic bound really does bound the rasterized mean.
  {
    for (uint32_t seed = 1; seed <= 10; ++seed) {
      letterpress::Params lp;
      lp.strengthPercent = letterpress::kStrengthOff;  // tooth out of the way
      paperdefects::Params dp;
      dp.dialPercent = 100;
      dp.seed = seed * 2246822519u;
      dp.remainingBudget = 1.0f;
      paperdefects::Mark marks[paperdefects::kMaxMarks];
      const int n = paperdefects::generate(dp, 400, 300, marks);
      const double bound = paperdefects::meanDarkeningBound(marks, n, 400, 300);
      const double measured = meanDarkening(bareSheet(lp, dp, 400, 300));
      check(measured <= bound + 1e-6,
            "the analytic bound is an UPPER bound on what is rendered");
      check(bound > 0.0, "dial 100 has a non-zero bound to bound");
    }
  }

  // ------------------------------------------- FORMATION IS MEAN-KEEPING --
  //
  // The reason it does not appear in remainingPaperBudget. A symmetric swing on
  // the tooth's AMPLITUDE leaves the mean darkening where it was, so the
  // contrast argument carries over with nothing new to prove -- but only if it
  // is actually symmetric, which nothing but a measurement can say.
  {
    letterpress::Params flat;
    flat.strengthPercent = 200;
    flat.paperDarkenBudget = 0.7f;
    flat.toothScale = 2.0f;
    paperdefects::Params none;
    none.dialPercent = 0;
    double worst = 0.0;
    for (uint32_t seed = 1; seed <= 8; ++seed) {
      flat.seed = seed * 2654435761u;
      flat.formationDepth = 0.0f;
      const double m0 = meanDarkening(bareSheet(flat, none, 512, 384));
      flat.formationDepth = letterpress::kFormationDepthMax;
      const double m1 = meanDarkening(bareSheet(flat, none, 512, 384));
      const double d = std::fabs(m1 - m0);
      if (d > worst) worst = d;
    }
    check(worst < 0.02, "formation at full depth is mean-preserving");
  }

  // --------------------------------------- THE PRESS PARTS: NO NEW WORST --
  //
  // F6's three new Params fields. The claim the drawer's ceiling rests on: any
  // (offered master rung, part ratio) state the drawer can reach produces a
  // term no larger than the SHIPPED master ladder could already reach on its
  // own at kStrengthMax. If this fails, the drawer has invented a new worst
  // case and every contrast argument in Letterpress.h has to be re-derived.
  {
    check(letterpress::kPartScaleMax *
                  static_cast<float>(letterpress::kOfferedStrengthMax) <=
              static_cast<float>(letterpress::kStrengthMax) + 1e-4f,
          "part ratio x heaviest offered press stays inside kStrengthMax");

    // A 3x3 window with a full paper->ink step, which maximises every gated
    // term at once.
    float win[3][3];
    for (int dy = 0; dy < 3; ++dy)
      for (int dx = 0; dx < 3; ++dx) win[dy][dx] = dx >= 1 ? 1.0f : 0.0f;

    letterpress::Params worstShipped;
    worstShipped.strengthPercent = letterpress::kStrengthMax;
    worstShipped.paperDarkenBudget = 1.0f;
    worstShipped.includeTooth = true;
    const int offered[] = {0, 50, 100, letterpress::kOfferedStrengthMax};
    const float ratios[] = {0.0f, 0.5f, 1.0f, 1.5f, letterpress::kPartScaleMax};
    for (int y = 0; y < 8; ++y)
      for (int x = 0; x < 8; ++x) {
        const uint8_t shipped =
            letterpress::multiplierAt(worstShipped, win, x, y, 8, 8);
        for (const int st : offered)
          for (const float r : ratios) {
            letterpress::Params p = worstShipped;
            p.strengthPercent = st;
            p.ringScale = letterpress::clampPartScale(r);
            p.debossScale = letterpress::clampPartScale(r);
            p.pressScale = letterpress::clampPartScale(r);
            const uint8_t got = letterpress::multiplierAt(p, win, x, y, 8, 8);
            check(got >= shipped,
                  "no drawer state darkens more than the shipped ladder's top");
          }
      }

    // The three parts are bit-exact off at 0 and bit-exact unchanged at 1.
    letterpress::Params base;
    base.strengthPercent = 100;
    base.paperDarkenBudget = 0.6f;
    letterpress::Params ones = base;
    ones.ringScale = ones.debossScale = ones.pressScale = 1.0f;
    letterpress::Params zeros = base;
    zeros.ringScale = zeros.debossScale = zeros.pressScale = 0.0f;
    bool identical = true, differs = false;
    for (int y = 0; y < 16; ++y)
      for (int x = 0; x < 16; ++x) {
        if (letterpress::multiplierAt(base, win, x, y, 16, 16) !=
            letterpress::multiplierAt(ones, win, x, y, 16, 16))
          identical = false;
        if (letterpress::multiplierAt(base, win, x, y, 16, 16) !=
            letterpress::multiplierAt(zeros, win, x, y, 16, 16))
          differs = true;
      }
    check(identical, "part ratio 1.0 is bit-exact the pre-existing rendering");
    check(differs, "part ratio 0 actually removes the press's contribution");

    // DEBOSS IS ZERO ON BARE PAPER, at every ratio. It is the only press term
    // that multiplies (1-t) rather than t, so it is the only one that could
    // reach the paper's budget -- and it cannot, because its edge gate is zero
    // where there is no edge.
    float flatWin[3][3];
    for (int dy = 0; dy < 3; ++dy)
      for (int dx = 0; dx < 3; ++dx) flatWin[dy][dx] = 0.0f;
    letterpress::Params noTooth = base;
    noTooth.includeTooth = false;
    noTooth.debossScale = letterpress::kPartScaleMax;
    noTooth.ringScale = letterpress::kPartScaleMax;
    noTooth.pressScale = letterpress::kPartScaleMax;
    for (int y = 0; y < 8; ++y)
      for (int x = 0; x < 8; ++x)
        check(letterpress::multiplierAt(noTooth, flatWin, x, y, 8, 8) == 255,
              "every press term is exactly nothing on bare paper");
  }

  // ------------------------------------------------------ VOCABULARY -----
  //
  // Owner's word, and it is checked rather than trusted: BLUE MARKS. The Mars
  // pigment family is a different thing and the string must not appear.
  {
    check(std::string(paperdefects::kKinds[paperdefects::BlueMark].name) ==
              "blue mark",
          "the blue defect is called a blue mark");
    for (int k = 0; k < paperdefects::kKindCount; ++k) {
      const std::string n = paperdefects::kKinds[k].name;
      check(n.find("mars") == std::string::npos &&
                n.find("Mars") == std::string::npos,
            "no defect is named after the Mars pigments");
    }
  }

  if (failures == 0) std::printf("paper_defects_test: all checks passed\n");
  return failures ? 1 : 0;
}
