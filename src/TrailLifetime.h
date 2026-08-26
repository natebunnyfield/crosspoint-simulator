#pragma once

#include <algorithm>
#include <cstdint>

// WHEN A PHOSPHOR TRAIL STOPS BEING ABLE TO CHANGE A PIXEL.
//
// The glow accumulator is composited MAXIMUM over the page (see the composite in
// HalDisplay::presentIfNeeded and the S-016 note beside it), so it stops
// mattering long before it reaches black: the moment its brightest possible
// pixel, after the colour mod that paints it, sits at or below the darkest tone
// the destination can hold, max(dst, src) is dst for EVERY pixel and the present
// is byte-identical to the one before it. Every field composited afterwards --
// the scanlines, the grain, the warm-up -- is a deterministic function of that
// destination, so an unchanged destination gives an unchanged frame.
//
// The constant this replaces was `trailMs * 2.4f`, and its comment says where
// 2.4 came from: "a deposit is spent once it has decayed below one 8-bit step",
// which is 10^-2.4 of full scale. That is the right figure for a trail
// composited against BLACK, and the trail is never composited against black. On
// the shipped dark pair (E0E0DE ink on 121212 paper) the paper is 8% of the ink,
// so the honest figure is ~1.04 trails and the 1.4 trails between the two are
// presents that cannot move a pixel.
//
// MEASURED, 2026-08-26, dark page turn on the as-shipped dials, X3 at 1x,
// trail 1095 ms: the last frame that differed from its predecessor landed 846 ms
// after the deposit; the remaining 1782 ms of the 2628 ms trail were 15
// consecutive byte-identical presents -- 64% of the trail's wall time, spent
// redrawing one picture.
//
// PURE AND HOST-TESTED for the reason every model in this repo is: the failure
// mode is a wrong picture. Cut the trail one present early and a visible ghost
// pops off the glass; the compiler sees nothing and no rendered page announces
// it. tests/trail_lifetime_test.cpp sweeps it.
namespace trail {

// The accumulator channel value at or below which the trail cannot change one
// presented pixel.
//
// `modCeiling` is the brightest colour mod the trail will ever be drawn with:
// the live ink, taken per channel against a cascade phosphor's tail tint,
// because the mod ramps between the two over the trail and either end may be
// the brighter one. `dstFloor` is the darkest value each channel of the
// destination can hold -- the panel's tones are LERPed between ink and paper,
// so that is their per-channel minimum.
//
// The draw is src = a * mod[c] / 255 composited MAXIMUM, so it is invisible
// while a * mod[c] / 255 <= dstFloor[c] for every channel, i.e. while
// a <= min_c(255 * dstFloor[c] / mod[c]).
inline float invisibleAtOrBelow(const uint8_t modCeiling[3],
                                const uint8_t dstFloor[3]) {
  float a = 255.0f;
  for (int c = 0; c < 3; c++) {
    const float m = static_cast<float>(modCeiling[c]);
    // A channel the mod zeroes can never light, so it constrains nothing.
    if (m <= 0.0f) continue;
    const float limit = 255.0f * static_cast<float>(dstFloor[c]) / m;
    if (limit < a) a = limit;
  }
  return a;
}

// One present's fade applied to a scalar UPPER BOUND on the accumulator's
// brightest channel. `drop` is the alpha the fade's black FillRect actually
// used, so the bound tracks the same schedule the texture does however the
// present cadence wanders.
//
// THE +0.5 IS THE WHOLE REASON THIS IS A FUNCTION AND NOT A MULTIPLY. The fade
// is dst *= (255-drop)/255 evaluated in the renderer's own arithmetic. SDL's
// software blitter truncates, so the real value falls FASTER than a float model
// -- which is why the desktop canary measures the trail dead at 0.77 trails.
// A GPU rasteriser rounds to nearest instead, and that error compounds: the
// recurrence e <- e*k + 0.5 settles at 0.5*255/drop, about 16 of 255 at the
// shipped cadence. A model without the term would call the trail dead while a
// Metal backend still held a visible ghost, and the desktop is exactly the
// platform on which that bug could not be reproduced.
//
// Clamped non-increasing: for a small `drop` the +0.5 exceeds the decay and the
// naive expression would GROW. A bound that never rises is still a valid upper
// bound on a quantity that never rises, and a bound that rises is a trail that
// never ends.
inline float fadePeakBound(float peak, int drop) {
  if (drop <= 0) return peak;
  if (drop >= 255) return 0.0f;
  const float next = peak * static_cast<float>(255 - drop) / 255.0f + 0.5f;
  return next < peak ? next : peak;
}

}  // namespace trail
