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
//      against its sheet through the renderer's drift clamp, the dark trace against its
//      glass. Recomputed from the bytes, not trusted from the walk that chose
//      them.
//   3. THE DIRECTIONS. Warmth warms (paper and tube both lean red against
//      blue as it rises) and Brightness deepens the light ink and brightens the
//      dark trace, monotonically, and every step of Brightness moves both
//      pages (a ramp that started below the floor once spent a third of the
//      row on one value).
//   4. WARMTH IS NOT BRIGHTNESS. The tinted sheet keeps the frozen sheet's
//      luminance within a few percent across the whole Warmth row.
//
//   c++ -std=c++17 -Isrc -Iios tests/frontlit_page_test.cpp -o /tmp/frontlit_page_test
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

  if (testcheck::g_failures) {
    std::printf("%d failure(s)\n", testcheck::g_failures);
    return 1;
  }
  std::printf(
      "frontlit page: frozen at 60/50 and off; worst %.2f:1 light, %.2f:1 "
      "dark; sheet luminance within %.1f%%\n",
      worstLight, worstDark, worstDrift * 100.0);
  return 0;
}
