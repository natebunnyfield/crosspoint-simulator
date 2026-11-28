// THE PICCO'S LIGHT ON THE FROZEN PAGE (TODO.md ST-012, src/FrontlitPage.h).
//
// Owner 2026-11-26: "for warmth setting on picco to adjust paper warmth and
// crt warmth; brightness adjusts ink and crt specific physics". Every failure
// mode here is a wrong color or an illegible page, which no compiler sees, so
// this pins four things:
//
//   1. THE ORIGIN. Off, and on at the firmware's defaults (60 / 50), both
//      pages are the frozen pair byte for byte, with the frozen decay. An
//      untouched Picco, and every other board, must not move.
//   2. THE FLOOR. Every setting on the whole grid clears 7:1: the light ink
//      against its sheet through the renderer's drift clamp, the dark trace
//      against its glass. Recomputed from the bytes, not trusted from the walk
//      that chose them.
//   3. THE DIRECTIONS. Warmth warms (paper and tube both lean red against
//      blue as it rises) and Brightness deepens the light ink and brightens the
//      dark trace, monotonically, and every step of Brightness moves both
//      pages (a ramp that started below the floor once spent a third of the
//      row on one value).
//   4. WARMTH IS NOT BRIGHTNESS. The tinted sheet keeps the frozen sheet's
//      luminance within a few percent across the whole Warmth row.
//   5. THE TUBE (owner 2026-11-27, docs/crt-gamut-plan-2026-11-27.md). Each
//      tube at 60/50 IS its JEDEC phosphor's page and decay; light off is the
//      Mixed tube whatever the row says; every tube clears 7:1 over the whole
//      grid; the light page does not follow the tube; Warmth tilts each tube
//      toward the warm guns, whose P38 brings its 1095 ms afterglow.
//   6. THE APP'S -100..300 (owner 2026-11-27). 0..100 is untouched (the
//      checks above); below 0 each step dims both pages, to 1.5:1 at -100;
//      above 100 the beam keeps rising and the ink deepening, still over 7:1.
//
//   c++ -std=c++17 -Isrc -Iios tests/frontlit_page_test.cpp -o
//   /tmp/frontlit_page_test
//   && /tmp/frontlit_page_test

#include <cmath>
#include <cstdio>
#include <cstring>
#include <string>

#include "FrontlitPage.h"
#include "TestCheck.h"
using testcheck::check;

namespace {

bool same(const unsigned char a[3], const unsigned char b[3]) {
  return std::memcmp(a, b, 3) == 0;
}

double lum(const unsigned char c[3]) {
  double l[3];
  for (int i = 0; i < 3; i++) l[i] = lightink::srgbToLinear(c[i]);
  return 0.2126 * l[0] + 0.7152 * l[1] + 0.0722 * l[2];
}

// Red over blue in linear light: the warmth of a tone.
double redOverBlue(const unsigned char c[3]) {
  return lightink::srgbToLinear(c[0]) /
         std::max(1e-6, lightink::srgbToLinear(c[2]));
}

std::string at(int b, int w) {
  char buf[48];
  std::snprintf(buf, sizeof buf, " (brightness %d, warmth %d)", b, w);
  return buf;
}

}  // namespace

int main() {
  using namespace frontlitpage;
  const panelpalette::Palette frozenLight = frozenpage::lightPair();
  const panelpalette::Palette frozenDark = frozenpage::darkPair();
  const phosphormix::Result &frozenMix = frozenpage::darkMix();

  // 1. THE ORIGIN.
  for (const Light l : {Light{60, 50, true}, Light{60, 50, false},
                        Light{0, 0, false}, Light{100, 100, false}}) {
    const std::string where = at(l.brightness, l.warmth) +
                              (l.on ? " light on" : " light off");
    check(isNeutral(l), "neutral" + where);
    const panelpalette::Palette lp = lightPair(l);
    const Dark d = darkPage(l);
    check(same(lp.ink, frozenLight.ink) && same(lp.paper, frozenLight.paper),
          "light page is the frozen Sanguine on India" + where);
    check(same(d.mix.dark.ink, frozenDark.ink) &&
              same(d.mix.dark.paper, frozenDark.paper),
          "dark page is the frozen four-gun pair" + where);
    check(d.mix.trailMs == frozenMix.trailMs, "frozen decay" + where);
    check(bloomPercent(l, 400) == 400, "frozen bloom" + where);
  }

  // 2. THE FLOOR, over the whole grid.
  double worstLight = 99.0, worstDark = 99.0;
  for (int b = 0; b <= kMax; b += 2) {
    for (int w = 0; w <= kMax; w += 2) {
      const Light l{b, w, true};
      const panelpalette::Palette lp = lightPair(l);
      unsigned char leaf[3];
      lightink::paperWorstDriftForPair(lp.ink, lp.paper,
                                       lightink::kPaperDriftMax, leaf);
      const double cl = lightink::contrastRatio(lp.ink, leaf);
      const panelpalette::Palette dp = darkPair(l);
      const double cd = lightink::contrastRatio(dp.ink, dp.paper);
      worstLight = std::min(worstLight, cl);
      worstDark = std::min(worstDark, cd);
      if (cl < lightink::kContrastFloor)
        check(false, "light page under 7:1" + at(b, w));
      if (cd < lightink::kContrastFloor)
        check(false, "dark page under 7:1" + at(b, w));
      const int bloom = bloomPercent(l, scanlines::kBloomMax);
      if (bloom < 0 || bloom > scanlines::kBloomMax)
        check(false, "bloom outside the dial" + at(b, w));
    }
  }

  // 3. THE DIRECTIONS.
  for (int w = 0; w <= kMax; w += 25) {
    double lastInk = 2.0, lastTrace = -1.0;
    for (int b = 0; b <= kMax; b += 5) {
      const Light l{b, w, true};
      const double ink = lum(lightPair(l).ink);
      const double trace = lum(darkPair(l).ink);
      if (!(ink < lastInk))
        check(false, "light ink must deepen as Brightness rises" + at(b, w));
      if (!(trace > lastTrace))
        check(false, "dark trace must brighten as Brightness rises" + at(b, w));
      lastInk = ink;
      lastTrace = trace;
    }
  }
  for (int b = 0; b <= kMax; b += 25) {
    double lastPaper = -1.0, lastTube = -1.0;
    for (int w = 0; w <= kMax; w += 5) {
      const Light l{b, w, true};
      const double paper = redOverBlue(lightPair(l).paper);
      const double tube = redOverBlue(darkPair(l).ink);
      if (!(paper > lastPaper))
        check(false, "paper must warm as Warmth rises" + at(b, w));
      if (!(tube > lastTube))
        check(false, "tube must warm as Warmth rises" + at(b, w));
      lastPaper = paper;
      lastTube = tube;
    }
  }

  // 4. WARMTH IS NOT BRIGHTNESS.
  const double sheet = lum(frozenLight.paper);
  double worstDrift = 0.0;
  for (int w = 0; w <= kMax; w++) {
    const double l = lum(lightPair(Light{60, w, true}).paper);
    worstDrift = std::max(worstDrift, std::fabs(l - sheet) / sheet);
  }
  check(worstDrift < 0.03, "the tinted sheet keeps the frozen luminance");

  // 5. THE TUBE.
  const int kTubePhosphor[kTubeCount] = {
      -1,
      panelpalette::kPresetBlueCrt,    // Blue: P11
      panelpalette::kPresetBlueTvCrt,  // Pale Blue: P22B
      panelpalette::kPresetP22GCrt,    // Green: P22G
      panelpalette::kPresetP28Crt,     // Yellow: P28
      panelpalette::kPresetAmberCrt,   // Amber: P3
      panelpalette::kPresetRedCrt,     // Red: P22R
      panelpalette::kPresetRedProjCrt, // Pale Red: P56
  };
  double worstTube = 99.0;
  for (int t = 1; t < kTubeCount; t++) {
    const std::string name = " (tube " + std::to_string(t) + ")";
    const panelpalette::Palette jedec = panelpalette::resolve(
        kTubePhosphor[t], true, panelpalette::kInvalidColor,
        panelpalette::kInvalidColor);
    const Light home{60, 50, true, t};
    check(!isNeutral(home), "a tube is not the frozen page" + name);
    const Dark d = darkPage(home);
    check(same(d.mix.dark.ink, jedec.ink) &&
              same(d.mix.dark.paper, jedec.paper),
          "at 60/50 the tube is its phosphor's page" + name);
    check(d.mix.trailMs == panelpalette::trailMsForPreset(kTubePhosphor[t]) &&
              !d.mix.hasTail,
          "at 60/50 the tube decays as its phosphor" + name);
    for (const Light off : {Light{60, 50, false, t}, Light{0, 100, false, t},
                            Light{100, 0, false, t}}) {
      const Dark o = darkPage(off);
      check(isNeutral(off) && same(o.mix.dark.ink, frozenDark.ink) &&
                same(o.mix.dark.paper, frozenDark.paper) &&
                o.mix.trailMs == frozenMix.trailMs,
            "light off is the Mixed tube" + name +
                at(off.brightness, off.warmth));
    }
    const Dark warm = darkPage(Light{60, 100, true, t});
    check(warm.mix.trailMs ==
              panelpalette::trailMsForPreset(panelpalette::kPresetP38Crt),
          "the warm tilt brings P38's afterglow" + name);
    for (int b = 0; b <= kMax; b += 2) {
      for (int w = 0; w <= kMax; w += 2) {
        const Light l{b, w, true, t};
        const panelpalette::Palette dp = darkPair(l);
        const double cd = lightink::contrastRatio(dp.ink, dp.paper);
        worstTube = std::min(worstTube, cd);
        if (cd < lightink::kContrastFloor)
          check(false, "tube under 7:1" + name + at(b, w));
        const panelpalette::Palette lp = lightPair(l);
        const panelpalette::Palette lp0 = lightPair(Light{b, w, true});
        if (!same(lp.ink, lp0.ink) || !same(lp.paper, lp0.paper))
          check(false,
                "the light page does not follow the tube" + name + at(b, w));
      }
    }
  }
  // Mixed is today's page everywhere, not only at the origin.
  for (int b = 0; b <= kMax; b += 10)
    for (int w = 0; w <= kMax; w += 10) {
      const Dark m = darkPage(Light{b, w, true, kTubeMixed});
      const Dark ref = computeDarkPage(Light{b, w, true});
      if (!same(m.mix.dark.ink, ref.mix.dark.ink) ||
          !same(m.mix.dark.paper, ref.mix.dark.paper))
        check(false, "Mixed is the four-gun tube" + at(b, w));
    }

  // 6. THE APP'S WIDER BRIGHTNESS (owner 2026-11-27: "let brightness go from
  //    -100 to 300, keeping current 0 to 100 as is"). The byte the firmware
  //    stores is the step: 0 -> -100, 32 -> 60 (its default), 80 -> 300
  //    (crosspoint-reader src/SettingsList.h withShown(-100, 5), {0, 80, 1}).
  check(brightnessFromStored(0) == -100 && brightnessFromStored(32) == 60 &&
            brightnessFromStored(80) == 300 && brightnessFromStored(200) == 300 &&
            brightnessFromStored(-3) == -100 && kMaxStoredBrightness == 80,
        "stored step decodes as the firmware's row shows it");
  double worstAt100Down = 0.0;
  for (int tube = 0; tube < kTubeCount; tube++)
    for (int w = 0; w <= kMax; w += 25) {
      const std::string name = " tube " + std::to_string(tube);
      // Below 0: contrast falls every step, from the floor toward 1:1.
      double prevL = 1e9, prevD = 1e9;
      for (int b = 0; b >= kMinBrightness; b -= 5) {
        const Light l{b, w, true, tube};
        const panelpalette::Palette lp = lightPair(l);
        const Dark d = darkPage(l);
        const double cl = lightink::contrastRatio(lp.ink, lp.paper);
        const double cd = lightink::contrastRatio(d.mix.dark.ink, d.mix.dark.paper);
        if (b < 0 && !(cl < prevL && cd < prevD))
          check(false, "below 0 every step dims both pages" + name + at(b, w));
        if (!same(lp.paper, lightPair(Light{0, w, true, tube}).paper) ||
            !same(d.mix.dark.paper, darkPage(Light{0, w, true, tube}).mix.dark.paper))
          check(false, "below 0 only the mark moves, not the sheet or glass" +
                           name + at(b, w));
        prevL = cl;
        prevD = cd;
      }
      const Light bottom{kMinBrightness, w, true, tube};
      const double cl = lightink::contrastRatio(lightPair(bottom).ink, lightPair(bottom).paper);
      const Dark db = darkPage(bottom);
      const double cd = lightink::contrastRatio(db.mix.dark.ink, db.mix.dark.paper);
      worstAt100Down = std::max(worstAt100Down, std::max(cl, cd));
      check(std::fabs(cl - kUnderFloorContrast) < 0.05 && std::fabs(cd - kUnderFloorContrast) < 0.05,
            "-100 is 1.5:1 on both pages, faint but not gone (Settings is on this page too)" + name +
                at(-100, w));
      check(db.beam > 0.0 && db.beam < 1.0, "-100 dims the beam" + name);
      // Above 100: the beam and ink keep rising; nothing falls below the floor.
      double prevBeam = darkPage(Light{100, w, true, tube}).beam;
      double prevLum = lum(lightPair(Light{100, w, true, tube}).ink);
      for (int b = 105; b <= kMaxBrightness; b += 5) {
        const Light l{b, w, true, tube};
        const Dark d = darkPage(l);
        const panelpalette::Palette lp = lightPair(l);
        if (!(d.beam > prevBeam)) check(false, "above 100 the beam rises" + name + at(b, w));
        if (!(lum(lp.ink) <= prevLum)) check(false, "above 100 the ink deepens" + name + at(b, w));
        if (lightink::contrastRatio(d.mix.dark.ink, d.mix.dark.paper) < lightink::kContrastFloor ||
            lightContrast(lp.ink, lp.paper) < lightink::kContrastFloor)
          check(false, "above 100 still clears 7:1" + name + at(b, w));
        if (bloomPercent(l, 400) > scanlines::kBloomMax)
          check(false, "bloom stays capped" + name + at(b, w));
        prevBeam = d.beam;
        prevLum = lum(lp.ink);
      }
    }

  std::printf("at -100 the clearest page is %.2f:1\n", worstAt100Down);
  if (testcheck::g_failures) {
    std::printf("%d failure(s)\n", testcheck::g_failures);
    return 1;
  }
  std::printf(
      "frontlit page: frozen at 60/50 and off; worst %.2f:1 light, %.2f:1 "
      "dark, %.2f:1 over the seven tubes; sheet luminance within %.1f%%\n",
      worstLight, worstDark, worstTube, worstDrift * 100.0);
  return 0;
}
