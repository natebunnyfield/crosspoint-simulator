// Host test for src/CornerDefocus.h and the scanline field it modulates.
//
// Every failure mode here is a wrong PICTURE. A scale below 1 SHARPENS the
// corner, which no tube does. An isotropic scale reads as "the corner text is
// worse" rather than as character, and only a directional test can tell the
// two apart. A field that forgets to divide the defocus out of the
// normalization LIFTS the corners, which is the page-flash bug class wearing
// a physics argument. And an "off" that is nearly-off silently changes every
// dark page that never asked for this.

#include "CornerDefocus.h"

#include "Scanlines.h"

#include <cmath>
#include <cstdio>
#include <vector>

using namespace cornerdefocus;

static int failures = 0;

static void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    failures++;
  }
}

// The phone's own geometry: an iPhone-class output at the shipped 2x render
// scale, and the source-row pitch that follows from it.
static constexpr int W = 1260, H = 2736;
static constexpr float kPitch = 2.39f;

int main() {
  // --- OFF IS BIT-EXACT OFF -------------------------------------------------
  {
    Params off;
    off.strengthPercent = kStrengthOff;
    bool allOne = true;
    for (int y = 0; y < H; y += 37)
      for (int x = 0; x < W; x += 29)
        if (sigmaScaleAt(off, x, y, W, H) != 1.0f) allOne = false;
    check(allOne, "strength 0 is exactly 1.0 at every pixel, not nearly 1.0");
    check(maxSigmaScale(off) == 1.0f, "strength 0 has exactly no span");
    check(isOff(off), "strength 0 reports itself off");

    // ...and the scanline field it feeds is byte-identical with the scale at 1.
    scanlines::Params sp;
    sp.intensityPercent = 100;
    sp.pitchPx = kPitch;
    sp.mottleDepth = scanlines::mottleDepthFor(100);
    bool identical = true;
    for (int y = 0; y < 400; ++y)
      for (int x = 0; x < W; x += 211)
        for (float level : {0.0f, 0.5f, 1.0f})
          if (scanlines::multiplierAt(sp, x, y, W, H, level) !=
              scanlines::multiplierAt(sp, x, y, W, H, level, 1.0f))
            identical = false;
    check(identical,
          "a sigma scale of exactly 1 leaves the raster byte-identical");
  }

  // --- IT ONLY EVER SOFTENS -------------------------------------------------
  {
    for (const int rung : {0, 50, 100, 150, 200}) {
      Params p;
      p.strengthPercent = rung;
      float lo = 10.0f, hi = 0.0f;
      for (int y = 0; y < H; y += 13)
        for (int x = 0; x < W; x += 11) {
          const float s = sigmaScaleAt(p, x, y, W, H);
          if (s < lo) lo = s;
          if (s > hi) hi = s;
        }
      check(lo >= 1.0f, "no pixel is ever sharper than the centre");
      check(hi <= maxSigmaScale(p) + 1e-4f,
            "no pixel exceeds the declared maximum spot growth");
    }
  }

  // --- THE CENTRE IS EXACTLY UNTOUCHED, AT EVERY STRENGTH -------------------
  {
    for (const int rung : {50, 100, 200}) {
      Params p;
      p.strengthPercent = rung;
      // Even-dimension screens have no pixel exactly on the axis, so this is
      // the strongest available statement: the two centre pixels are within a
      // ten-thousandth of unity.
      const float s = sigmaScaleAt(p, W / 2, H / 2, W, H);
      check(std::fabs(s - 1.0f) < 1e-3f,
            "the on-axis spot is the reference spot");
    }
  }

  // --- THE PARABOLA, NOT A RAMP --------------------------------------------
  // The correction circuits drive focus from X^2 + Y^2, so the residual is
  // quadratic in the radius. A linear ramp would put half the growth at half
  // the radius; a parabola puts a quarter of it there. Measured down the
  // vertical axis, where the growth is purely radial.
  {
    Params p;
    p.strengthPercent = kStrengthStandard;
    const float atEdge = sigmaScaleAt(p, W / 2, 0, W, H) - 1.0f;
    const float atHalf = sigmaScaleAt(p, W / 2, H / 4, W, H) - 1.0f;
    check(atEdge > 0.0f, "the top edge is defocused at all (test premise)");
    check(atHalf / atEdge < 0.35f,
          "the growth is quadratic in the radius, not linear");
    check(atHalf / atEdge > 0.15f,
          "...and quadratic rather than a step at the very edge");
  }

  // --- IT IS AN ELLIPSE, NOT A BIGGER CIRCLE -------------------------------
  // The one claim that separates "character" from "the corner is blurry". The
  // long axis is RADIAL, so the VERTICAL extent the raster samples grows at
  // the top and bottom of the screen and grows far less at the left and right,
  // where the spot spreads sideways instead.
  {
    Params p;
    p.strengthPercent = kStrengthStandard;
    const float top = sigmaScaleAt(p, W / 2, 0, W, H);
    const float side = sigmaScaleAt(p, 0, H / 2, W, H);
    check(top > side + 0.02f,
          "the vertical extent grows at the top edge and not at the side");
    // Both edges are at the same normalized radius, so an ISOTROPIC model
    // would make these equal -- which is exactly the failure this pins.
    check(std::fabs(top - side) > 1e-3f,
          "the spot is elliptical rather than isotropic");
    // ...and at the corner both contribute, so it sits between them.
    const float corner = sigmaScaleAt(p, 0, 0, W, H);
    check(corner > side, "a corner is softer than the side at the same radius");
  }

  // --- TG18'S ONE HARD NUMBER ----------------------------------------------
  // "The astigmatism ratio must be < 1.5 for primary class." It is the only
  // published bound this model has, so it is asserted against the source's
  // figure rather than against the constants.
  {
    for (const int rung : {50, 100, 150, 200}) {
      Params p;
      p.strengthPercent = rung;
      check(astigmatismRatio(p) < kMaxAstigmatismRatio,
            "no offered strength exceeds TG18's corner astigmatism limit");
      check(astigmatismRatio(p) > 1.0f,
            "every offered strength actually produces an ellipse");
    }
    Params off;
    off.strengthPercent = kStrengthOff;
    check(astigmatismRatio(off) == 1.0f, "off is a perfectly round spot");
  }

  // --- MONOTONE IN THE DIAL -------------------------------------------------
  {
    float last = 0.0f;
    bool mono = true;
    for (const int rung : {0, 25, 50, 100, 150, 200}) {
      Params p;
      p.strengthPercent = rung;
      const float s = sigmaScaleAt(p, 0, 0, W, H);
      if (s < last - 1e-6f) mono = false;
      last = s;
    }
    check(mono, "a higher strength is never a sharper corner");
  }

  // --- THE FIELD SOFTENS WITHOUT LIFTING -----------------------------------
  // THE claim of the whole item, and the one no compiler and no screenshot can
  // see: a defocused corner must lose CONTRAST in the raster while losing no
  // LIGHT. The period-mean of the transmission is linear in sigma, so
  // rowTransmission divides it back out; without that division a wide spot's
  // integral simply grows and the corners read as lit.
  {
    scanlines::Params sp;
    sp.intensityPercent = 100;
    sp.pitchPx = kPitch;
    sp.mottleDepth = 0.0f;  // isolate the raster from the blotching
    auto stats = [&](float scale, double &mean, double &swing) {
      double sum = 0.0;
      double lo = 1e9, hi = -1e9;
      const int y0 = 900, y1 = 900 + 400;
      for (int y = y0; y < y1; ++y) {
        const double t = scanlines::rowTransmission(sp, static_cast<float>(y),
                                                    0.0f, scale);
        sum += t;
        if (t < lo) lo = t;
        if (t > hi) hi = t;
      }
      mean = sum / (y1 - y0);
      swing = hi - lo;
    };
    double m1 = 0.0, s1 = 0.0, m2 = 0.0, s2 = 0.0;
    stats(1.0f, m1, s1);
    stats(1.45f, m2, s2);
    check(s1 > 0.2, "the focused raster has structure to lose (test premise)");
    check(s2 < s1 * 0.75,
          "a defocused corner loses raster contrast");
    check(std::fabs(m2 - m1) < 0.03,
          "a defocused corner loses no light -- it softens, it does not lift");
  }

  // --- THE DEFOCUSED PAGE STILL CLEARS 7:1 ---------------------------------
  // It spends no budget by construction (the mean is preserved above), but the
  // claim is worth measuring rather than deducing, on the same five pages the
  // scanline sweep uses -- including the two tightest this repo ships.
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
    for (const auto &page : pages) {
      const float li = lum(page.r, page.g, page.b);
      const float lp = lum(page.pr, page.pg, page.pb);
      for (const int rung : {0, 50, 100, 150}) {
        for (const int dRung : {0, 50, 100, 200}) {
          Params cd;
          cd.strengthPercent = dRung;
          scanlines::Params sp;
          sp.intensityPercent = rung;
          sp.pitchPx = kPitch;
          sp.mottleDepth = scanlines::mottleDepthFor(rung);
          sp.budgetMeanDarkening =
              0.8f * phosphorgrain::darkeningBudget(li, lp);
          // Measured AT THE CORNER, which is where the scale is largest.
          double sumInk = 0.0, sumPaper = 0.0;
          int n = 0;
          for (int y = 0; y < 600; ++y) {
            const float scale = sigmaScaleAt(cd, 0, y, W, H);
            sumInk += scanlines::multiplierAt(sp, 0, y, W, H, li, scale);
            sumPaper += scanlines::multiplierAt(sp, 0, y, W, H, lp, scale);
            n++;
          }
          const float ratio =
              (li * static_cast<float>(sumInk / n / 255.0) + 0.05f) /
              (lp * static_cast<float>(sumPaper / n / 255.0) + 0.05f);
          check(ratio >= 7.0f - 0.05f,
                "no defocus setting drops a corner under the contrast floor");
        }
      }
    }
  }

  if (failures == 0) std::printf("corner_defocus_test: all checks passed\n");
  return failures == 0 ? 0 : 1;
}
