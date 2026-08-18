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
//
// This is the LEGIBLE floor specifically. What the renderer actually uses is
// floorFor() below, which is this scaled by the owner's chosen depth.
inline float legibleFloorFor(const unsigned char ink[3],
                             const unsigned char paper[3]) {
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

// HOW DEEP the fade goes, as a PERCENTAGE OF THE LEGIBLE FLOOR THAT IS KEPT.
//
// 100 keeps the whole legible floor: exactly what legibleFloorFor() returns,
// which is what shipped before this setting existed and is the default. 0 keeps
// none of it -- the page fades to bare paper and disappears. The steps between
// are proportions of the same per-palette figure, so the adaptation above keeps
// working at every setting except the extreme: a low-contrast page still fades
// less far than a high-contrast one at the same depth.
//
// Stored as the PROPORTION, not as a row index and not as an absolute alpha.
// Same reasoning as pageFadeSeconds and beamPaintMs: the number is meaningful
// on its own, so the picker's rows can be retuned without a migration -- and
// unlike an absolute alpha, a proportion cannot silently strand one palette
// above or below its own floor when the palette changes.
inline constexpr int kDepthFull = 100;

// THE LEGIBILITY GUARD IS BYPASSED BELOW 100, AND THAT IS DELIBERATE.
// Owner ruling 2026-08-18: "create another setting for Page Fade that includes
// current value and fully transparent and three steps in between."
//
// Do not "fix" this by clamping back up to legibleFloorFor(). The measured cost
// of the deeper settings, worst case per depth (the numbers legibleFloorFor()
// exists to defend, at kFloor = 0.75):
//
//   depth 100 -> 4.50:1 (Red)        every row at AA body text   (the default)
//   depth  75 -> 2.73:1 (Solarized)  below AA body text, still readable
//   depth  50 -> 1.88:1 (Solarized)  a ghost of the page
//   depth  25 -> 1.28:1 (Blue)       barely present
//   depth   0 -> 1.00:1              the page is gone; this is the point of it
//
// Those are printed, not remembered: tests/page_fade_test.cpp sweeps every
// preset in both polarities at every depth and prints this table, so a new
// palette moves the figures here rather than quietly invalidating them.
//
// Solarized is the row the guard was written for -- 4.13:1 by design, 2.73:1 at
// a flat kFloor -- so it is also the row that suffers most here, and at depth 75
// it lands on precisely the 2.73:1 the guard was built to prevent. It does not
// fade at all at depth 100 (legibleFloorFor returns 1.0) and fades like every
// other row below it. An install that never opens this setting is unaffected:
// depth defaults to kDepthFull, and at kDepthFull this function returns
// legibleFloorFor() unchanged, byte for byte.
inline float floorFor(const unsigned char ink[3], const unsigned char paper[3],
                      int depthPercent = kDepthFull) {
  const float legible = legibleFloorFor(ink, paper);
  if (depthPercent >= kDepthFull) return legible;  // the shipped behaviour
  if (depthPercent <= 0) return 0.0f;              // fully transparent
  return legible * (static_cast<float>(depthPercent) / 100.0f);
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
