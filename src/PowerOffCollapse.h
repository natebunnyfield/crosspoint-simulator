#pragma once

// THE POWER-OFF COLLAPSING DOT -- what a CRT does when its supplies die, for
// the DARK page, at SLEEP.
//
// DOCTRINE (2026-08-22): dark mode is a CRT. This is the one piece of pure
// delight in that fiction: it carries no information, improves no reading, and
// is the single artifact everybody who ever switched off a tube remembers.
// Design and the sleep-path argument: docs/power-off-collapse.md.
//
// THE MECHANISM, in the order the circuit fails. Cutting mains power drains the
// deflection supplies faster than the EHT reservoir and the cathode drive, so
// for a moment the beam is still writing while the sweeps are already
// collapsing. The vertical yoke gives out first: the raster squeezes to a
// bright horizontal LINE at the centre. Then the horizontal sweep dies and the
// line shrinks to a stationary DOT. Then the last of the beam current bleeds
// away and the dot fades over roughly a second. (Tube makers considered the dot
// dangerous enough to the phosphor to patent spot-killer circuits against it.)
//
// THE BRIGHTNESS RISE IS NOT A FLOURISH, IT IS THE SAME LIGHT. Cathode current
// does not fall while the sweep collapses, so the same energy per frame lands
// on a shrinking area and the line is genuinely brighter than the picture was.
// gainAt is 1 / verticalScale, which is that statement, capped -- see kGainMax.
//
// WHAT IT SQUEEZES IS THE SCREEN THAT WAS THERE. Owner ruling 2026-08-24:
// "when power off collapse is enabled, don't switch to showing sleep screen.
// use the existing screen as source for the effect." The firmware still draws
// its sleep screen -- this is host-side and reaches no device -- but from
// deep-sleep entry onward HalDisplay drops every present and keeps the page the
// reader was looking at, so the tube switches off showing what was on it.
//
// WHY IT CANNOT DELAY SLEEP. The animation does not run before the device
// sleeps; it runs INSIDE the sleep loop, after HalDisplay::deepSleep() has run
// and the firmware has handed control to HalGPIO::startDeepSleep. Nothing waits
// for it: a wake edge arriving in the middle of the collapse is serviced on the
// same iteration it arrives, because
// the loop checks for wakes before it steps this. The frames it draws are frames
// that would otherwise not exist.
//
// WHY IT ENDS BLACK AND STAYS BLACK. A tube that has been switched off is dark.
// That is also why this is the one dial in the surface stack that is a settings
// row rather than a frozen constant, and why it defaults OFF: turning it on
// trades the sleep screen -- a real feature, with a book cover or a clock on it
// -- for the shutdown. Nobody may make that trade on the owner's behalf. Since
// 2026-08-24 the trade is the whole of it: the sleep screen is not shown even
// for the instant before the collapse, because the collapse's source is the
// page it replaced.
//
// AND THE OTHER HALF READS THAT DECISION. Because this ends at EXACTLY zero
// rather than leaving a lit dot, src/PowerOnWarmUp.h cannot trigger off "is
// there a dot on the glass" -- it triggers off a flag this animation records on
// the frame it starts, and it RELIGHTS the dot at kDotWidthFrac as its own first
// beat. The four constants below are shared across that seam and pinned against
// it by tests/power_on_warm_up_test.cpp; if they drift, the two halves stop
// meeting. Same Settings row, both directions.
//
// Pure and clock-free; tests/power_off_collapse_test.cpp is the only
// instrument. The caller owns the clock, exactly as it owns the render.

#include <cmath>
#include <cstdint>

namespace poweroff {

// The three phases, in milliseconds. Ordered by which supply dies first, and
// the totals are the ones the artifact is remembered at: a collapse quick
// enough to read as a failure rather than a transition, and a dot that lingers.
constexpr float kVerticalMs = 130.0f;    // raster -> line
constexpr float kHorizontalMs = 190.0f;  // line -> dot
constexpr float kFadeMs = 700.0f;        // dot -> nothing

inline float totalMs() { return kVerticalMs + kHorizontalMs + kFadeMs; }

// The vertical scale the raster is allowed to reach before the line takes over.
// Not zero: at zero there is nothing to draw, and the handover to the line
// needs the picture to already BE a line.
constexpr float kLineScale = 0.012f;

// Cap on the brightness rise. The physical 1/scale diverges as the raster
// closes, and past this the line is a white bar with no structure left in it.
constexpr float kGainMax = 3.0f;

// The dot's width as a fraction of the line's full width, and the line's
// thickness as a fraction of the screen height. Both are floors on the drawn
// geometry, so a collapse on a small screen still has something to see.
constexpr float kDotWidthFrac = 0.006f;
constexpr float kLineHeightFrac = 0.004f;

struct Params {
  // OFF IS THE DEFAULT AND OFF IS BIT-EXACT: stateAt returns the identity
  // state -- full picture, unit gain, no dot -- at every elapsed time, so a
  // caller that steps a disabled animation draws exactly what it drew before.
  bool enabled = false;
};

struct State {
  // Is anything to be drawn other than the untouched frame?
  bool active = false;
  // Has the animation run out? The caller stops stepping and leaves the glass
  // as this state left it.
  bool finished = false;
  // The picture, squeezed about the panel's centre. 1 = untouched.
  float verticalScale = 1.0f;
  float horizontalScale = 1.0f;
  // Additive brightening of the squeezed picture, 1 = none.
  float gain = 1.0f;
  // Draw the picture at all? False once it has become the line.
  bool showPicture = true;
  // The line / dot: its width as a fraction of the page width, and its
  // brightness, 0..1. Zero width means there is no line yet.
  float dotWidthFrac = 0.0f;
  float dotAlpha = 0.0f;
  // How dark the chrome OUTSIDE the page is. 0 = normal, 1 = fully dark.
  //
  // THE PAPER GOES OUT WITH THE PICTURE, NOT AHEAD OF IT. Owner report
  // 2026-08-25: "panel and paper need to be painted at the same time on power
  // collapse and any other time." The caller used to clear the whole output to
  // black on the collapse's FIRST frame -- so the letterboxed paper surround,
  // the button pad and the glass's own scanline field all vanished in the
  // frame before the raster had moved at all. Measured on the desktop at 1x:
  // 100% of pixels stepped by +1 code value between the last present and the
  // opening collapse frame, with zero geometry change, which is precisely the
  // opening flash this model's t = 0 identity exists to forbid.
  //
  // Same field, same sense and the same 1 = dark convention as
  // poweron::State::surroundVeil, because this IS that animation run
  // backwards: the warm-up lifts the chrome during Settle, this one takes it
  // down during the vertical collapse. Keeping the two names and polarities
  // identical is what lets the two draw sites be read against each other.
  float surroundVeil = 0.0f;
};

// THE ANSWER: what the glass shows `elapsedMs` after the tube was switched off.
//
// t = 0 is the IDENTITY -- scales exactly 1, gain exactly 1, no dot -- so the
// first frame of a collapse is byte-identical to the frame already on the glass
// and the animation can never flash on its opening frame.
inline State stateAt(const Params &p, float elapsedMs) {
  State s;
  if (!p.enabled) return s;
  if (elapsedMs < 0.0f) elapsedMs = 0.0f;
  s.active = true;

  if (elapsedMs < kVerticalMs) {
    // THE VERTICAL SWEEP DIES. Squeeze toward the centre line. Quadratic in
    // time rather than linear: the deflection amplitude follows the supply's
    // discharge, so most of the travel happens late.
    const float u = elapsedMs / kVerticalMs;
    const float k = u * u;
    s.verticalScale = 1.0f + (kLineScale - 1.0f) * k;
    s.horizontalScale = 1.0f;
    s.showPicture = true;
    // Same light into less height.
    float g = 1.0f / (s.verticalScale > 1e-4f ? s.verticalScale : 1e-4f);
    if (g > kGainMax) g = kGainMax;
    s.gain = g;
    // The line emerges from the picture rather than replacing it, so the two
    // never cross-fade through a gap.
    s.dotWidthFrac = 1.0f;
    s.dotAlpha = k;
    // The chrome outside the page goes out on the SAME curve the raster
    // closes on -- k, not u -- so the paper and the panel are always one
    // picture. At k = 0 that is the identity, which is the whole point.
    s.surroundVeil = k;
    return s;
  }

  if (elapsedMs < kVerticalMs + kHorizontalMs) {
    // THE HORIZONTAL SWEEP DIES. The line closes to a dot; the picture is gone,
    // there is nothing left of it to squeeze.
    const float u = (elapsedMs - kVerticalMs) / kHorizontalMs;
    const float k = u * u;
    s.verticalScale = kLineScale;
    s.horizontalScale = 1.0f + (kDotWidthFrac - 1.0f) * k;
    s.showPicture = false;
    s.gain = kGainMax;
    s.dotWidthFrac = s.horizontalScale;
    s.dotAlpha = 1.0f;
    // The picture is already a line by now; everything that is not the line is
    // unlit glass.
    s.surroundVeil = 1.0f;
    return s;
  }

  // THE BEAM BLEEDS AWAY. Exponential, the same 10^(-t/tau) curve the phosphor
  // trail uses and for the same reason: light does not die linearly.
  const float age = elapsedMs - kVerticalMs - kHorizontalMs;
  s.verticalScale = kLineScale;
  s.horizontalScale = kDotWidthFrac;
  s.showPicture = false;
  s.gain = kGainMax;
  s.dotWidthFrac = kDotWidthFrac;
  s.surroundVeil = 1.0f;
  if (age >= kFadeMs) {
    // EXACTLY off, not nearly off: the terminal state is a black screen, and a
    // dot left at one part in a thousand would sit on the glass all night.
    s.dotAlpha = 0.0f;
    s.finished = true;
    return s;
  }
  // 10^(-age/tau) falls to a tenth over the fade; remapped onto [1, 0] so the
  // curve keeps its shape AND lands exactly on nothing, rather than stepping
  // off a tenth of full brightness at the end.
  const float decay = std::pow(10.0f, -age / kFadeMs);
  float a = (decay - 0.1f) / 0.9f;
  if (a < 0.0f) a = 0.0f;
  if (a > 1.0f) a = 1.0f;
  s.dotAlpha = a;
  return s;
}

}  // namespace poweroff
