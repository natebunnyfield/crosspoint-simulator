#pragma once
#include <cmath>

// ST-010: how bright the page you are READING should be, given how long it is
// since the reader last did anything.
//
// Pure and host-testable for the same reason PanelPalette and PadPalette are:
// every failure mode here is silent. A floor that is too low is a page you
// cannot finish reading and no compiler will say so; a curve that never reaches
// its floor is a render loop that never stops asking for frames; a fade that
// does not reset on input is a device that appears to be dying.
namespace pagefade {

// The deepest fade that still leaves a page of prose at the WCAG AA body-text
// bar. Swept across every phosphor row in both polarities, worst case (Blue,
// P11) against its own paper:
//
//   0.55 -> 2.88:1     0.70 -> 4.04:1
//   0.60 -> 3.23:1     0.75 -> 4.49:1   <- AA body text is 4.5:1
//   0.65 -> 3.62:1     0.80 -> 4.99:1
//
// The first draft used 0.55 and claimed it held everything above 6:1. It does
// not, and the measurement is why this constant is here rather than inline.
inline constexpr float kFloor = 0.75f;

// THE FLOOR IS PER-PALETTE, not one constant, and Solarized is why.
//
// kFloor above is the deepest fade the PHOSPHOR rows tolerate. Solarized is
// exempt from this repo's 7:1 rule by design (4.13:1 light), and fading it to
// kFloor drops it to 2.73:1 -- worse than AA large text. A page the owner chose
// for its softness must not become the one page the fade makes unreadable.
//
// So the floor is computed against the pair actually on screen: fade as deep as
// kFloor when there is contrast to spend, and less when there is not. Returns
// a value in [kFloor, 1]; 1 means "this palette cannot afford to fade at all".
inline float floorFor(const unsigned char ink[3], const unsigned char paper[3]) {
  auto lin = [](double c) {
    c /= 255.0;
    return c <= 0.04045 ? c / 12.92 : std::pow((c + 0.055) / 1.055, 2.4);
  };
  auto lum = [&](double r, double g, double b) {
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  };
  const double paperL = lum(paper[0], paper[1], paper[2]);
  // Walk up from the deepest fade until the pair clears AA body text.
  for (int step = 0; step <= 25; step++) {
    const float a = kFloor + step * 0.01f;
    if (a >= 1.0f) break;
    const double l = lum(ink[0] * a + paper[0] * (1 - a),
                         ink[1] * a + paper[1] * (1 - a),
                         ink[2] * a + paper[2] * (1 - a));
    double hi = l, lo = paperL;
    if (hi < lo) { const double t = hi; hi = lo; lo = t; }
    if ((hi + 0.05) / (lo + 0.05) >= 4.5) return a;
  }
  return 1.0f;
}

// 1.0 fresh, decaying to kFloor. Exponential, like the glow and for the same
// reason: light does not die linearly. At age == fadeMs the decay term is at
// 10%, so one "fade period" is when it has all but settled.
inline float alphaFor(float ageMs, float fadeMs, float floor = kFloor) {
  if (fadeMs <= 0.0f) return 1.0f;   // off
  if (ageMs <= 0.0f) return 1.0f;
  const float decay = std::pow(10.0f, -ageMs / fadeMs);
  const float a = floor + (1.0f - floor) * decay;
  return a < floor ? floor : (a > 1.0f ? 1.0f : a);
}

// Whether the fade is still moving. Once it is within one 8-bit step of the
// floor it has arrived, and something has to stop asking for frames or a
// settled page presents forever.
inline bool stillMoving(float ageMs, float fadeMs, float floor = kFloor) {
  return fadeMs > 0.0f && alphaFor(ageMs, fadeMs, floor) > floor + 1.0f / 255.0f;
}

}  // namespace pagefade
