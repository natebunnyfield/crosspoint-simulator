#pragma once

// THE sRGB TRANSFER FUNCTION, once.
//
// IEC 61966-2-1: a linear toe below the knee, a 2.4 power above it. Every
// palette decision in this repo -- the contrast floor, the grain's darkening
// budget, the letterpress paper budget, the phosphor mixer's linear-light
// blend, the emissive ramp, the fade's legible floor -- is arithmetic on
// LINEAR light, so this pair of curves sits under all of them.
//
// It had 23 copies across src/ and tests/ on 2026-08-23, two of them BYTE
// IDENTICAL 78 lines apart in HalDisplay.cpp (a lambda left behind when
// srgbLumOf was extracted). Not one of them was wrong, which is the point: a
// wrong copy of this is a page whose contrast floor is measured against a
// slightly different curve from the one that draws it, and nothing about the
// picture says so.
//
// BOTH PRECISIONS SHIP, deliberately. Nine production copies were float and
// six were double, and collapsing either into the other moves results by an
// ULP -- which for the 0..255 quantized paths is occasionally a whole code
// value, and a refactor is not allowed to change a pixel. The rule for new
// code: FLOAT on the render path (per-pixel, per-ramp-entry work, which is
// where every float copy already was), DOUBLE for colorimetry decided once
// (ink/paper table derivation, contrast checks -- where every double copy
// already was).
//
// Callers keep their own domain-shaped wrappers -- panelpalette::srgbToLinear
// takes a normalized float, lightink::srgbToLinear takes a byte -- because the
// unit conversion is part of what each one means. Those wrappers now forward
// here instead of restating the curve.
//
// The tests do NOT use this header, and that is not an oversight: a test that
// imports the transfer function it is checking cannot catch a wrong transfer
// function. Their local copies are an independent second derivation.

#include <cmath>

namespace srgb {

// Encoded 0..1 -> linear 0..1.
inline float toLinear(float c) {
  return c <= 0.04045f ? c / 12.92f : std::pow((c + 0.055f) / 1.055f, 2.4f);
}
inline double toLinear(double c) {
  return c <= 0.04045 ? c / 12.92 : std::pow((c + 0.055) / 1.055, 2.4);
}

// Linear 0..1 -> encoded 0..1. Unclamped: the callers clamp in their own
// output units (a byte, a code value), and clamping twice hides an out-of-range
// input from whoever produced it.
inline float fromLinear(float v) {
  return v <= 0.0031308f ? v * 12.92f
                         : 1.055f * std::pow(v, 1.0f / 2.4f) - 0.055f;
}
inline double fromLinear(double v) {
  return v <= 0.0031308 ? v * 12.92 : 1.055 * std::pow(v, 1.0 / 2.4) - 0.055;
}

// WCAG relative luminance of an encoded triple, the weights every contrast
// check in this repo uses. Bytes, because that is how a palette tone is
// carried everywhere it is measured.
inline float relativeLuminance(const unsigned char c[3]) {
  return 0.2126f * toLinear(static_cast<float>(c[0]) / 255.0f) +
         0.7152f * toLinear(static_cast<float>(c[1]) / 255.0f) +
         0.0722f * toLinear(static_cast<float>(c[2]) / 255.0f);
}

}  // namespace srgb
