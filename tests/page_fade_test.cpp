// Unit tests for pagefade -- ST-010's decay of the page you are reading.
//
// WHY: every failure here is silent. Too low a floor is an unreadable page and
// no compiler says so; a curve that never reaches its floor is a render loop
// that never stops; a fade that does not reset on input is a device that looks
// like it is dying. None of that shows up in a screenshot of one frame.
//
//   c++ -std=c++17 -Isrc tests/page_fade_test.cpp -o /tmp/pf && /tmp/pf

#include "PageFade.h"
#include "PanelPalette.h"

#include <cmath>
#include <cstdio>
#include <utility>
#include "TestCheck.h"

static int &failures = testcheck::g_failures;
static double lin(double c) {
  c /= 255.0;
  return c <= 0.04045 ? c / 12.92 : std::pow((c + 0.055) / 1.055, 2.4);
}
static double lum(const unsigned char c[3]) {
  return 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2]);
}
static double ratio(double a, double b) {
  if (a < b) std::swap(a, b);
  return (a + 0.05) / (b + 0.05);
}

int main() {
  using namespace pagefade;

  // OFF is exactly off. Not "very slow" -- a page that dims at all when the
  // setting is off is a bug nobody would attribute to this feature.
  CHECKM(alphaFor(0.0f, 0.0f) == 1.0f, "off fades at 0 ms");
  CHECKM(alphaFor(600000.0f, 0.0f) == 1.0f, "off fades after ten minutes");
  CHECKM(!stillMoving(1000.0f, 0.0f), "off still asks for frames");

  // Fresh is full, and monotonically dimmer from there.
  CHECKM(alphaFor(0.0f, 3000.0f) == 1.0f, "a fresh page is not already dim");
  float prev = 1.0f;
  for (float age = 0.0f; age <= 30000.0f; age += 250.0f) {
    const float a = alphaFor(age, 3000.0f);
    CHECKM(a <= prev + 1e-6f, "the fade brightened at %.0f ms", age);
    prev = a;
  }

  // IT STOPS. Both that the value reaches the floor and that the loop stops
  // asking -- the second is what keeps a settled page from presenting forever.
  CHECKM(alphaFor(1e6f, 3000.0f) == kFloor, "the fade does not settle");
  CHECKM(!stillMoving(1e6f, 3000.0f), "a settled page still asks for frames");
  CHECKM(stillMoving(0.0f, 3000.0f), "a fresh page does not animate");

  // The floor is where the fade lands, and one fade period gets most of the way.
  const float atOne = alphaFor(3000.0f, 3000.0f);
  CHECKM(atOne < kFloor + 0.05f, "one fade period barely moved (%.3f)", atOne);
  CHECKM(atOne > kFloor, "one fade period already hit the floor exactly");

  // THE FLOOR IS LEGIBLE AT THE DEFAULT DEPTH, and this is the check the
  // constant exists for: every phosphor row, both polarities, faded ink against
  // its own paper must clear WCAG AA body text. At 0.55 (the first draft) Blue
  // lands at 2.88:1.
  //
  // "At the default depth" is the whole qualification the depth setting added.
  // floorFor() is called here with no depth argument ON PURPOSE -- that is the
  // path an install which never opens the setting takes, and it has to stay
  // exactly what it was.
  double worst = 99.0;
  const char *worstName = "";
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
    const panelpalette::PresetInfo &r = panelpalette::kPresetInfo[i];
    for (int d = 0; d < 2; d++) {
      const panelpalette::Palette p = panelpalette::presetPalette(r.preset, d != 0);
      const float fl = floorFor(p.ink, p.paper);
      unsigned char faded[3];
      for (int k = 0; k < 3; k++)
        faded[k] = static_cast<unsigned char>(p.ink[k] * fl +
                                              p.paper[k] * (1.0f - fl));
      const double cr = ratio(lum(faded), lum(p.paper));
      // A palette that CANNOT afford to fade (floorFor == 1) is left alone, so
      // its contrast is its own baseline and this feature has not touched it.
      // Solarized is that row: 4.13:1 by design, exempt from the 7:1 rule.
      if (fl >= 1.0f) {
        const double base = ratio(lum(p.ink), lum(p.paper));
        CHECKM(std::abs(cr - base) < 0.01,
               "%s does not fade, so its contrast must be untouched", r.name);
        continue;
      }
      if (cr < worst) { worst = cr; worstName = r.name; }
    }
  }
  CHECKM(worst >= 4.45, "the faded floor drops %s to %.2f:1, below AA body text",
         worstName, worst);

  // AND THE PER-PALETTE FLOOR ACTUALLY BINDS somewhere, or it is dead code
  // dressed as care: Solarized is the row that cannot afford the full fade.
  const panelpalette::Palette sol =
      panelpalette::presetPalette(panelpalette::kPresetSolarized, false);
  CHECKM(floorFor(sol.ink, sol.paper) > kFloor,
         "Solarized takes the deep floor, which measured 2.73:1");
  const panelpalette::Palette green =
      panelpalette::presetPalette(panelpalette::kPresetGreenCrt, true);
  CHECKM(floorFor(green.ink, green.paper) == kFloor,
         "a CRT row no longer gets the full fade");
  std::printf("  worst faded contrast: %.2f:1 (%s)\n", worst, worstName);

  // --- DEPTH -------------------------------------------------------------
  //
  // The setting is "how much of that legible floor to keep", 100 down to 0.
  // Three things have to be true and none of them is visible in a screenshot:
  // the default must not have moved, deeper must actually BE deeper, and 0 must
  // reach nothing rather than merely nearly-nothing.

  // 1. THE DEFAULT IS UNCHANGED, for every palette in both polarities. This is
  //    the assertion that protects the install that never opens the setting.
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
    const panelpalette::PresetInfo &r = panelpalette::kPresetInfo[i];
    for (int d = 0; d < 2; d++) {
      const panelpalette::Palette p = panelpalette::presetPalette(r.preset, d != 0);
      const float legible = legibleFloorFor(p.ink, p.paper);
      CHECKM(floorFor(p.ink, p.paper) == legible,
             "%s (%s): the default depth moved the floor", r.name,
             d ? "dark" : "light");
      CHECKM(floorFor(p.ink, p.paper, kDepthFull) == legible,
             "%s (%s): depth 100 is not the legible floor", r.name,
             d ? "dark" : "light");
      // Out of range cannot invent a state: over-full is full, negative is 0.
      CHECKM(floorFor(p.ink, p.paper, 1000) == legible,
             "%s: an over-range depth is not clamped to full", r.name);
      CHECKM(floorFor(p.ink, p.paper, -5) == 0.0f,
             "%s: a negative depth is not clamped to transparent", r.name);
    }
  }

  // 2. DEEPER IS DEEPER, strictly, on a row that fades at all -- and on the row
  //    that does NOT fade at the default, because owner election is exactly
  //    what the depth setting is for.
  const int depths[5] = {100, 75, 50, 25, 0};
  for (const panelpalette::Palette *pal : {&green, &sol}) {
    const float legible = legibleFloorFor(pal->ink, pal->paper);
    float prevFloor = 2.0f;
    for (int di = 0; di < 5; di++) {
      const float f = floorFor(pal->ink, pal->paper, depths[di]);
      CHECKM(f < prevFloor, "depth %d did not fade deeper than the step above",
             depths[di]);
      CHECKM(std::abs(f - legible * depths[di] / 100.0f) < 1e-5f,
             "depth %d is not that proportion of the legible floor", depths[di]);
      prevFloor = f;
    }
  }
  // Solarized does not fade at the default and DOES at every step below it.
  // That is the guard being bypassed by election, stated as a test so nobody
  // re-clamps it and calls the re-clamp a fix.
  CHECKM(floorFor(sol.ink, sol.paper) >= 1.0f,
         "Solarized fades at the default depth, which it must not");
  CHECKM(floorFor(sol.ink, sol.paper, 50) < 1.0f,
         "Solarized ignores an explicitly chosen deeper fade");

  // 3. FULLY TRANSPARENT REACHES NOTHING. Not 0.02, not "one step above the
  //    floor" -- alpha 0, or the option does not do what its row says.
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
    const panelpalette::PresetInfo &r = panelpalette::kPresetInfo[i];
    for (int d = 0; d < 2; d++) {
      const panelpalette::Palette p = panelpalette::presetPalette(r.preset, d != 0);
      const float f = floorFor(p.ink, p.paper, 0);
      CHECKM(f == 0.0f, "%s: fully transparent left a floor of %.4f", r.name, f);
      CHECKM(alphaFor(1e6f, 3000.0f, f) == 0.0f,
             "%s: fully transparent settles at %.4f, not 0", r.name,
             alphaFor(1e6f, 3000.0f, f));
      CHECKM(!stillMoving(1e6f, 3000.0f, f),
             "%s: a fully transparent page never stops asking for frames", r.name);
      CHECKM(stillMoving(0.0f, 3000.0f, f),
             "%s: a fully transparent fade never starts", r.name);
    }
  }

  // And the price of each step, printed rather than asserted at a bar, because
  // below the default there IS no bar -- that is the owner's ruling. The
  // numbers are here so the comment in PageFade.h can be checked against them.
  for (int di = 0; di < 5; di++) {
    double dworst = 99.0;
    const char *dname = "";
    for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
      const panelpalette::PresetInfo &r = panelpalette::kPresetInfo[i];
      for (int d = 0; d < 2; d++) {
        const panelpalette::Palette p =
            panelpalette::presetPalette(r.preset, d != 0);
        const float fl = floorFor(p.ink, p.paper, depths[di]);
        if (depths[di] == 100 && fl >= 1.0f) continue;  // this row does not fade
        unsigned char faded[3];
        for (int k = 0; k < 3; k++)
          faded[k] = static_cast<unsigned char>(p.ink[k] * fl +
                                                p.paper[k] * (1.0f - fl));
        const double cr = ratio(lum(faded), lum(p.paper));
        if (cr < dworst) { dworst = cr; dname = r.name; }
      }
    }
    std::printf("  depth %3d%%: worst settled contrast %.2f:1 (%s)\n",
                depths[di], dworst, dname);
  }
  // The default is the only depth that clears AA body text, and the deepest
  // reaches the paper exactly.
  CHECKM(floorFor(green.ink, green.paper, 0) == 0.0f,
         "the deepest setting is not fully transparent");

  if (failures) {
    std::printf("\n%d failure(s)\n", failures);
    return 1;
  }
  std::printf("page_fade: all checks passed\n");
  return 0;
}
