// Host test for src/PowerOffCollapse.h.
//
// Every failure mode here is a wrong PICTURE at the one moment nobody is
// watching the logs. A first frame that is not the identity is a FLASH at
// sleep -- the exact bug class the present-coalescing work spent a day on. A
// terminal state that is nearly-off leaves a lit dot on the glass for the whole
// night. A non-monotone collapse reads as a bounce rather than as a failure. An
// uncapped gain is a white bar. And a disabled animation that is not bit-exact
// identity would change what sleep looks like for every install that never
// turned this on.

#include "PowerOffCollapse.h"

#include <cmath>
#include <cstdio>
#include "TestCheck.h"
using testcheck::check;

using namespace poweroff;

static int &failures = testcheck::g_failures;

int main() {
  Params on;
  on.enabled = true;
  Params off;  // enabled defaults false

  // --- OFF IS BIT-EXACT OFF -------------------------------------------------
  {
    bool identity = true;
    for (float t = -50.0f; t < totalMs() + 500.0f; t += 7.0f) {
      const State s = stateAt(off, t);
      if (s.active || s.finished || s.verticalScale != 1.0f ||
          s.horizontalScale != 1.0f || s.gain != 1.0f || !s.showPicture ||
          s.dotAlpha != 0.0f || s.dotWidthFrac != 0.0f ||
          s.surroundVeil != 0.0f)
        identity = false;
    }
    check(identity,
          "a disabled collapse is the identity at every time, exactly");
  }

  // --- THE FIRST FRAME IS THE SLEEP SCREEN, UNTOUCHED -----------------------
  // If t = 0 were anything else the animation would open with a step, which on
  // a page display is a flash.
  {
    const State s = stateAt(on, 0.0f);
    check(s.verticalScale == 1.0f && s.horizontalScale == 1.0f,
          "the collapse opens at full size, exactly");
    check(s.gain == 1.0f, "the collapse opens at unit brightness, exactly");
    check(s.dotAlpha == 0.0f, "there is no line on the opening frame");
    check(s.showPicture, "the opening frame shows the picture");
    check(!s.finished, "the opening frame is not the last one");
    // AND THE PAPER IS STILL PAPER. Owner report 2026-08-25, "panel and paper
    // need to be painted at the same time on power collapse": the caller used
    // to black out the whole output on this frame, so the letterboxed surround,
    // the button pad and the glass's own field all went before the raster had
    // moved. Measured before the fix, desktop 1x with the grain field up:
    // the opening frame's mean luminance jumped 36.83 -> 47.32 and 85.6% of
    // pixels moved by more than four code values, with the page's textured
    // ground replaced by ONE flat tone across 80% of it.
    check(s.surroundVeil == 0.0f,
          "the chrome outside the page is untouched on the opening frame");
    // Negative elapsed (a clock that has not started) is the same frame.
    const State before = stateAt(on, -100.0f);
    check(before.verticalScale == 1.0f && before.gain == 1.0f,
          "a clock that has not started shows the untouched picture");
    check(before.surroundVeil == 0.0f,
          "a clock that has not started leaves the chrome alone too");
  }

  // --- THE CHROME GOES OUT WITH THE PICTURE, NOT AHEAD OF IT ---------------
  // The veil is the paper half of "painted at the same time": it rides the
  // raster's own curve, so there is no instant at which the page is whole and
  // the surround is not. Monotone for the same reason the scales are -- a
  // surround that came back would read as the tube reviving.
  {
    bool mono = true, everAhead = false;
    float prev = -1.0f;
    for (float t = 0.0f; t <= totalMs(); t += 1.0f) {
      const State s = stateAt(on, t);
      if (s.surroundVeil < prev - 1e-6f) mono = false;
      if (s.surroundVeil < 0.0f || s.surroundVeil > 1.0f) mono = false;
      // NEVER DARKER THAN THE RASTER HAS CLOSED, in the raster's own units:
      // the vertical sweep runs 1 -> kLineScale, so the fraction of it already
      // spent is (1 - v) / (1 - kLineScale). The chrome may match that and may
      // not lead it, which is the whole failure this exists to forbid -- a
      // surround that goes dark first IS the flash the owner reported.
      const float closed =
          (1.0f - s.verticalScale) / (1.0f - kLineScale);
      if (s.surroundVeil > closed + 1e-3f) everAhead = true;
      prev = s.surroundVeil;
    }
    check(mono, "the chrome only ever darkens, and stays in 0..1");
    check(!everAhead, "the chrome never goes dark ahead of the raster");
    check(stateAt(on, kVerticalMs).surroundVeil == 1.0f,
          "by the time the picture is a line the surround is fully dark");
    check(stateAt(on, totalMs()).surroundVeil == 1.0f,
          "the surround is still dark on the last frame");
  }

  // --- IT ONLY EVER CLOSES --------------------------------------------------
  {
    float lastV = 2.0f, lastH = 2.0f;
    bool vMono = true, hMono = true;
    for (float t = 0.0f; t <= totalMs(); t += 1.0f) {
      const State s = stateAt(on, t);
      if (s.verticalScale > lastV + 1e-6f) vMono = false;
      if (s.horizontalScale > lastH + 1e-6f) hMono = false;
      lastV = s.verticalScale;
      lastH = s.horizontalScale;
    }
    check(vMono, "the raster never grows back vertically");
    check(hMono, "the line never grows back horizontally");
  }

  // --- THE ORDER IS THE ORDER THE CIRCUIT FAILS IN --------------------------
  // Vertical first (raster to line), then horizontal (line to dot). Getting
  // this backwards is a different television.
  {
    const State mid1 = stateAt(on, kVerticalMs * 0.75f);
    check(mid1.verticalScale < 0.8f,
          "the vertical sweep has collapsed most of the way by three quarters");
    check(mid1.horizontalScale == 1.0f,
          "the horizontal sweep is untouched while the vertical one dies");

    const State mid2 = stateAt(on, kVerticalMs + kHorizontalMs * 0.5f);
    check(mid2.horizontalScale < 1.0f && mid2.horizontalScale > kDotWidthFrac,
          "the line is closing during the second phase");
    check(!mid2.showPicture,
          "the picture is gone once there is only a line left");
    check(mid2.dotAlpha == 1.0f, "the line is at full brightness while it closes");
  }

  // --- THE BRIGHTNESS RISE IS THE SAME LIGHT, AND IT IS CAPPED --------------
  {
    float maxGain = 0.0f;
    bool everBelowOne = false;
    for (float t = 0.0f; t <= totalMs(); t += 1.0f) {
      const State s = stateAt(on, t);
      if (s.gain > maxGain) maxGain = s.gain;
      if (s.gain < 1.0f) everBelowOne = true;
    }
    check(maxGain <= kGainMax + 1e-6f, "the gain is capped");
    check(!everBelowOne, "the collapse never DIMS the picture on its way out");
    // It is 1/scale while that is under the cap -- the statement that the
    // cathode current does not change while the raster shrinks.
    const State s = stateAt(on, kVerticalMs * 0.4f);
    if (s.gain < kGainMax - 1e-4f)
      check(std::fabs(s.gain - 1.0f / s.verticalScale) < 1e-3f,
            "the gain is the reciprocal of the squeeze while it is under the cap");
  }

  // --- IT ENDS EXACTLY DARK, AND SAYS SO ------------------------------------
  {
    const State end = stateAt(on, totalMs());
    check(end.dotAlpha == 0.0f, "the dot ends at exactly nothing, not nearly");
    check(end.finished, "the last frame reports itself finished");
    check(!end.showPicture, "there is no picture left at the end");
    const State past = stateAt(on, totalMs() * 4.0f);
    check(past.dotAlpha == 0.0f && past.finished,
          "past the end it stays exactly dark");
    // ...and nothing before the end claims to be finished, or the caller stops
    // stepping mid-collapse and freezes a half-drawn frame on the glass.
    bool earlyFinish = false;
    for (float t = 0.0f; t < totalMs() - 1.0f; t += 1.0f)
      if (stateAt(on, t).finished) earlyFinish = true;
    check(!earlyFinish, "nothing before the end reports itself finished");
  }

  // --- THE FADE IS CONTINUOUS AT BOTH ENDS ---------------------------------
  // A jump at the hand-over from the closing line to the fading dot, or a step
  // off a tenth of full brightness at the end, are both visible.
  {
    const State a = stateAt(on, kVerticalMs + kHorizontalMs - 0.5f);
    const State b = stateAt(on, kVerticalMs + kHorizontalMs + 0.5f);
    check(std::fabs(a.dotAlpha - b.dotAlpha) < 0.02f,
          "the line hands over to the fading dot without a step");
    const State nearEnd = stateAt(on, totalMs() - 1.0f);
    check(nearEnd.dotAlpha < 0.01f,
          "the fade arrives at nothing rather than stepping off a tenth");
    // Monotone down, all the way.
    float last = 2.0f;
    bool mono = true;
    for (float t = kVerticalMs + kHorizontalMs; t <= totalMs(); t += 0.5f) {
      const State s = stateAt(on, t);
      if (s.dotAlpha > last + 1e-6f) mono = false;
      last = s.dotAlpha;
    }
    check(mono, "the dot only ever dims");
  }

  // --- IT IS BOUNDED, AND SHORT ENOUGH TO BE A DELIGHT ---------------------
  // An animation that outlives the reader's attention at a sleep tap is an
  // interruption, not a flourish -- and it is also the whole wake budget it
  // would be competing with if it were ever allowed to block.
  {
    check(totalMs() > 500.0f, "the collapse is slow enough to be seen");
    check(totalMs() < 1500.0f, "the collapse is over in well under two seconds");
    check(kVerticalMs < kHorizontalMs,
          "the vertical sweep dies first and fastest");
    check(kFadeMs > kVerticalMs + kHorizontalMs,
          "most of the time is the dot fading, which is what is remembered");
  }

  if (failures == 0) std::printf("power_off_collapse_test: all checks passed\n");
  return failures == 0 ? 0 : 1;
}
