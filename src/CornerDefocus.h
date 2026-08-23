#pragma once

// CORNER DEFOCUS -- the beam spot grows and goes elliptical off-axis, for the
// DARK page.
//
// DOCTRINE (2026-08-22): dark mode is a CRT. The raster this modulates is
// src/Scanlines.h; design and sources: docs/corner-defocus.md.
//
// THE MECHANISM. A deflected beam lands further from the gun and at an oblique
// angle, so the spot is both LARGER and ELLIPTICAL, its long axis pointing
// radially outward. Dynamic-focus circuits drive the focus electrode from a
// signal proportional to X^2 + Y^2, which is why the correction -- and
// therefore the residual error -- is a PARABOLA in the radius and not a linear
// ramp. That is the whole model:
//
//     a(r) = 1 + kRadial     * r^2      (the long, radial axis)
//     b(r) = 1 + kTangential * r^2      (the short, tangential axis)
//
// with r normalized to 1 at the screen corner.
//
// WHY ELLIPTICITY RATHER THAN AN ISOTROPIC BLUR. An isotropic blur reads as
// "the corner text is worse"; an ellipse reads as character, because it is
// direction-dependent in the way a real tube's is. The scanline field only ever
// samples the spot's VERTICAL extent (a scan line is the spot dragged
// horizontally, so its profile across the raster is the spot's height), and the
// vertical semi-axis of an ellipse whose long axis points along (dx, dy) is a
// closed form -- sigmaScaleAt below. The consequence is the physically right
// one and it falls out for free: the raster softens most at the TOP and BOTTOM
// corners, where the radial direction is nearly vertical, and least at the left
// and right edges, where the spot grows sideways and the lines stay crisp.
//
// MAGNITUDES. TG18 gives no spot size in mm for a monochrome tube -- it states
// only the direction ("the corners always yield lower values than the center",
// section 4.5.4.2.1) and one hard limit: the corner ASTIGMATISM RATIO, long
// axis over short, must stay under 1.5 for primary-class reading. The shipped
// constants put it at 1.23, inside that bound with room, and the widely
// repeated "0.1-0.2 mm centre vs 0.3-0.5 mm corner" figure is deliberately NOT
// used: it is a colour-convergence number, not a mono spot size.
//
// IT ONLY EVER SOFTENS. The scale is >= 1 everywhere, so the field it feeds can
// only widen a beam, never narrow one -- there is no setting at which a corner
// is sharper than the centre. It also cannot fight the raster it modulates: a
// wider spot fills more of its own line pitch, so the structure fades toward a
// uniform dimming at the corners, which is what defocus physically does to a
// raster. It cannot add light, and it cannot move a pixel -- no resample, which
// is what separates it from the geometry warp the roadmap rules out (D2).
//
// Pure and clock-free; tests/corner_defocus_test.cpp is the only instrument.

#include <cmath>
#include <cstdint>

namespace cornerdefocus {

// STRENGTH IS A PERCENTAGE OF STANDARD. 0 off (bit-exact), 100 the shipped
// tube. The rungs above it exist for measurement runs and for the desktop env
// override; the app ships 100 frozen.
constexpr int kStrengthOff = 0;
constexpr int kStrengthStandard = 100;
constexpr int kStrengthMax = 200;

// Fractional growth of each semi-axis at the corner, at 100%.
//
// CHOSEN under the one hard published bound: (1 + kRadial) / (1 + kTangential)
// is the corner astigmatism ratio and TG18 caps it at 1.5 for primary class.
// 1.45 / 1.18 = 1.229. Both axes grow, because both do on a real tube; the
// radial one grows more, which is what makes the spot an ellipse rather than a
// bigger circle.
constexpr float kRadial = 0.45f;
constexpr float kTangential = 0.18f;

// The bound TG18 sets, kept here so the test asserts against the source rather
// than against the constants above.
constexpr float kMaxAstigmatismRatio = 1.5f;

inline int clampStrength(int percent) {
  if (percent < kStrengthOff) return kStrengthOff;
  if (percent > kStrengthMax) return kStrengthMax;
  return percent;
}

struct Params {
  int strengthPercent = kStrengthOff;
};

inline float strengthFraction(const Params &p) {
  return static_cast<float>(clampStrength(p.strengthPercent)) /
         static_cast<float>(kStrengthStandard);
}

inline bool isOff(const Params &p) {
  return clampStrength(p.strengthPercent) == kStrengthOff;
}

// The corner astigmatism ratio this setting produces -- long axis over short,
// the quantity TG18 bounds.
inline float astigmatismRatio(const Params &p) {
  const float s = strengthFraction(p);
  return (1.0f + kRadial * s) / (1.0f + kTangential * s);
}

// The largest vertical scale any pixel can receive, for the caller's cache
// range. Reached at the top and bottom corners, where radial is vertical.
inline float maxSigmaScale(const Params &p) {
  if (isOff(p)) return 1.0f;
  return 1.0f + kRadial * strengthFraction(p);
}

// THE ANSWER: the multiplier on the beam spot's VERTICAL sigma at output pixel
// (x, y) of a w x h screen. Exactly 1.0f at the centre, exactly 1.0f
// everywhere when the strength is off, and never below 1.0f.
//
// Derived rather than fitted. With the radial unit vector (rx, ry) = (dx, dy)/r
// and the tangential one (-ry, rx), an ellipse with semi-axes a along radial
// and b along tangential has vertical semi-axis
//
//     sqrt( a^2 * ry^2 + b^2 * rx^2 ) = sqrt( (a^2 dy^2 + b^2 dx^2) / r^2 )
//
// which is a and b themselves at the top/bottom and left/right edges
// respectively, and a == b == 1 at r = 0.
inline float sigmaScaleAt(const Params &p, int x, int y, int w, int h) {
  if (isOff(p) || w <= 0 || h <= 0) return 1.0f;
  const float dx =
      (2.0f * (static_cast<float>(x) + 0.5f) - static_cast<float>(w)) /
      static_cast<float>(w);
  const float dy =
      (2.0f * (static_cast<float>(y) + 0.5f) - static_cast<float>(h)) /
      static_cast<float>(h);
  const float r2 = dx * dx + dy * dy;
  if (r2 <= 1e-12f) return 1.0f;
  // Normalized so r = 1 at the corner, where dx^2 + dy^2 = 2.
  float rn2 = r2 * 0.5f;
  if (rn2 > 1.0f) rn2 = 1.0f;
  const float s = strengthFraction(p);
  const float a = 1.0f + kRadial * s * rn2;
  const float b = 1.0f + kTangential * s * rn2;
  const float sy = std::sqrt((a * a * dy * dy + b * b * dx * dx) / r2);
  return sy < 1.0f ? 1.0f : sy;
}

}  // namespace cornerdefocus
