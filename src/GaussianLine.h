#pragma once

// A GAUSSIAN LINE, BOX-INTEGRATED OVER A PIXEL -- the arithmetic under both
// combs in this repo.
//
// Two structures here are a periodic set of Gaussian lines sampled by pixels
// that have WIDTH: the CRT's raster (src/Scanlines.h, horizontal, in output
// space) and a laid sheet's chain and laid wires (src/LaidStructure.h,
// vertical, in panel space). Point-sampling either one beats against the
// sampling lattice -- that beat is ST-008, measured at 8.14 code values -- so
// both integrate the profile across the pixel instead. This is the integral.
//
// The two headers carried BYTE-IDENTICAL definitions of it on 2026-08-23,
// differing only in whether the interval's ends were called y0/y1 or v0/v1.
// Both were correct; that is why it is worth fixing now. Their own combs stay
// where they are, because they differ in real ways (the raster is one comb with
// bloom and defocus, the sheet is two combs at different pitches with a page
// phase), and only this bottom layer is shared.
//
// Float, and per-pixel: this is on both render paths.

#include <cmath>

namespace gaussline {

// The standard normal CDF. 0.70710678 is 1/sqrt(2): erf's argument is z/sqrt(2).
inline float phi(float z) { return 0.5f * (1.0f + std::erf(z * 0.70710678f)); }

// Integral over [a, b] of a PEAK-1 Gaussian centered at c with spread sigma.
// 2.50662827 is sqrt(2*pi), which un-normalizes the CDF difference: a unit
// Gaussian integrates to 1, and these profiles are specified by their PEAK
// (a line center reads exactly its nominal depth) rather than by their area.
inline float lineIntegral(float a, float b, float c, float sigma) {
  return sigma * 2.50662827f * (phi((b - c) / sigma) - phi((a - c) / sigma));
}

}  // namespace gaussline
