// THE FROZEN PAGE, IN BYTES -- both appearances and the tube's decay.
//
// Owner ruling 2026-08-24: "take out paper and crt settings for now. set them
// to sanguine and india paper and attached image for crt." The image was a
// screenshot of the gun mixer, and its own readout at those four guns is the
// check this file performs:
//
//   dark CFD4CC on 171B1B - light 483835 on F9F5F2 - fade 1095 ms
//
// The DARK half of that line is what the app now freezes. The LIGHT half is
// what the same blend renders in light appearance and is deliberately NOT the
// frozen light page -- light freezes at Sanguine on India, which is 5C332B on
// F9F3E9. Both are pinned here, because getting that distinction wrong is the
// single most likely way to freeze the wrong thing and it looks correct.
//
// WHY A TEST AND NOT A COMMENT. ios/FrozenPage.h states the INPUTS -- four gun
// assignments with weights, an ink index, a stock index -- and derives every
// tone from the pure models. That is the right way round (a hand-typed hex pair
// is a second record, which is what drifted twice on 2026-08-23), but it means
// nothing in the source says what the page actually looks like, and a wrong
// weight or a transposed gun compiles perfectly. This is the third party that
// compares the derivation with the number the owner read off his screen.
//
// It compiles ios/FrozenPage.h directly, which is possible because that header
// is plain C++ over src/ models with no Objective-C in it -- the same reason
// ios/PadPalette.h is host-tested.
//
//   c++ -std=c++17 -Isrc -Iios tests/frozen_page_test.cpp -o /tmp/frozen_page_test
//   && /tmp/frozen_page_test

#include <cmath>
#include <cstdio>
#include <string>

#include "FrozenPage.h"
#include "LightInkPalette.h"
#include "PanelPalette.h"
#include "TestCheck.h"
using testcheck::check;
using testcheck::checkEq;

namespace {

std::string hexOf(const uint8_t c[3]) {
  char buf[8];
  std::snprintf(buf, sizeof buf, "%02X%02X%02X", c[0], c[1], c[2]);
  return buf;
}

// The contrast ratio the whole light-page model is swept against. Restated here
// rather than imported, because the point is to check the FROZEN pair against
// the floor independently of the clamp that produced it.
double relativeLuminance(const uint8_t c[3]) {
  double lin[3];
  for (int i = 0; i < 3; i++) {
    const double s = c[i] / 255.0;
    lin[i] = s <= 0.04045 ? s / 12.92 : std::pow((s + 0.055) / 1.055, 2.4);
  }
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}

double contrastOf(const panelpalette::Palette &p) {
  const double a = relativeLuminance(p.ink) + 0.05;
  const double b = relativeLuminance(p.paper) + 0.05;
  return a > b ? a / b : b / a;
}

}  // namespace

int main() {
  // ------------------------------------------------------------- the guns ---
  // Read off the owner's screenshot, gun by gun, in the mixer's R/G/B/W order.
  // Pinned by preset AND weight: a transposed pair renders a different page and
  // there is no control left on the phone that could show it.
  checkEq(frozenpage::kGunPreset[0], panelpalette::kPresetP38Crt,
          "R gun is P38 Radar Amber");
  checkEq(frozenpage::kGunPreset[1], panelpalette::kPresetWhiteCrt,
          "G gun is P45 White");
  checkEq(frozenpage::kGunPreset[2], panelpalette::kPresetP20Crt,
          "B gun is P20 Yellow-Green Long");
  checkEq(frozenpage::kGunPreset[3], panelpalette::kPresetRedCrt,
          "W gun is P22R Red");
  checkEq(frozenpage::kGunWeight[0], 19, "R weight");
  checkEq(frozenpage::kGunWeight[1], 88, "G weight");
  checkEq(frozenpage::kGunWeight[2], 17, "B weight");
  checkEq(frozenpage::kGunWeight[3], 36, "W weight");

  // ------------------------------------------------------- the dark page ---
  // THE MIXER'S OWN READOUT at those guns. If these two lines fail, the frozen
  // recipe no longer produces the page the owner chose.
  const panelpalette::Palette dark = frozenpage::darkPair();
  checkEq(hexOf(dark.ink), std::string("CFD4CC"),
          "dark ink -- the mixer's readout at the frozen guns");
  checkEq(hexOf(dark.paper), std::string("171B1B"),
          "dark paper -- the mixer's readout at the frozen guns");

  // The decay, which is the other half of what a phosphor blend IS: a blend
  // dies at its slowest component's rate, and P38 is the Long one. The mixer's
  // readout said "fade 1095 ms"; it is a float, so the assertion is on the
  // rounded millisecond the readout prints.
  const phosphormix::Result &mix = frozenpage::darkMix();
  checkEq(static_cast<int>(mix.trailMs + 0.5f), 1095,
          "the frozen blend's fade, as the mixer's readout states it");
  check(mix.hasTail,
        "the frozen blend hands over to a tail -- its components' persistences "
        "differ by more than 1.5x, so what lingers is not the color that was "
        "painted. Losing this makes the page fade in the wrong hue.");
  checkEq(hexOf(mix.tail), std::string("613B27"),
          "what the afterglow decays toward");
  checkEq(static_cast<int>(mix.tailOnsetMs + 0.5f), 400,
          "when the handover completes -- the last non-survivor's death");

  // ------------------------------------------------------ the light page ---
  // Sanguine on India. NOT the light half of the mixer's readout (483835 on
  // F9F5F2), which is what the owner had BEFORE this ruling.
  checkEq(frozenpage::kLightInk, static_cast<int>(lightink::kInkSanguine),
          "the frozen ink is Sanguine");
  checkEq(frozenpage::kLightPaper, static_cast<int>(lightink::kPaperIndia),
          "the frozen stock is India");
  const panelpalette::Palette light = frozenpage::lightPair();
  checkEq(hexOf(light.ink), std::string("5C332B"), "light ink");
  checkEq(hexOf(light.paper), std::string("F9F3E9"), "light paper");
  check(hexOf(light.ink) != std::string("483835") &&
            hexOf(light.paper) != std::string("F9F5F2"),
        "the light page must NOT be the blend's light rendition (483835 on "
        "F9F5F2). That pair is what the owner's store held when he ruled, and "
        "freezing it would be freezing the state he asked to be replaced.");

  // ------------------------------------------------------- the selection ---
  // The clamps ran and left the request intact. Checked rather than assumed:
  // clampPaperStrengthPct is a ceiling that moves with the ink and
  // clampDensityPct a floor that moves with the sheet, so a frozen pair that
  // silently lost density would look like a deliberate wash.
  const frozenpage::LightSelection sel = frozenpage::lightSelection();
  checkEq(sel.density, lightink::kDensityMax,
          "Sanguine on India clears the legibility floor at full density");
  checkEq(sel.paperStrength, lightink::kPaperStrengthMax,
          "...and the sheet clears it at full strength");

  // ...and the pair that results actually clears 7:1, which is the invariant
  // those clamps exist for. Independent of them on purpose: this recomputes the
  // ratio from the two bytes rather than trusting the function that chose them.
  check(contrastOf(light) >= 7.0,
        "the frozen light page must clear the 7:1 floor -- it is the page, and "
        "no control on the phone can change it");
  check(contrastOf(dark) >= 7.0,
        "the frozen dark page must clear the 7:1 floor for the same reason");

  if (testcheck::g_failures) {
    std::printf("%d failure(s)\n", testcheck::g_failures);
    return 1;
  }
  std::printf("frozen page: Sanguine on India, and the owner's four guns\n");
  return 0;
}
