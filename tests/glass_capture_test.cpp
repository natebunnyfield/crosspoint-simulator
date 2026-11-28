// Pins glasscapture::shouldCapture (src/GlassCapture.h) -- the decision behind
// S-035's black un-swept region. The scenario that found it is the first case:
// two presents of the SAME page, the first composed before the harness laid
// the pad out (black glass), the second requested by that layout. The old gate
// kept the black one. Every case here fails against the seq-only gate.
#include <cstdio>
#include "../src/GlassCapture.h"
#include "TestCheck.h"

using glasscapture::Inputs;
using glasscapture::shouldCapture;

int main() {
  // First present of a session: no picture yet -> capture (it will be black;
  // that is the harness's first frame, and the next case is what repairs it).
  CHECK(shouldCapture({false, false, false, 0, 1, 0, 0}));

  // THE S-035 CASE. Same page (seq 1 == 1), but the overlay's layout during
  // present #1 requested present #2 (gen 0 -> 1). Must re-capture, or the
  // black frame is what the first sweep of the session reveals.
  CHECK(shouldCapture({false, false, true, 1, 1, 0, 1}));

  // Settled: same page, same generation -> nothing new to read back.
  CHECK(!shouldCapture({false, false, true, 1, 1, 1, 1}));

  // A trail-driven present (the accumulator asked for it itself): the gen does
  // not move, so no readback per decay frame.
  CHECK(!shouldCapture({false, false, true, 3, 3, 7, 7}));

  // A new page captures regardless of the generation.
  CHECK(shouldCapture({false, false, true, 1, 2, 1, 1}));

  // Mid-sweep: never, whatever else changed -- a half-swept frame is mostly
  // the old page.
  CHECK(!shouldCapture({true, false, true, 1, 2, 1, 5}));
  CHECK(!shouldCapture({true, false, false, 0, 1, 0, 0}));

  // ...unless the size is stale, which overrides the sweep gate.
  CHECK(shouldCapture({true, true, true, 1, 1, 1, 1}));
  CHECK(shouldCapture({false, true, true, 1, 1, 1, 1}));

  // An overlay request that lands mid-sweep is NOT lost: the sweep ends, the
  // gen still differs from the captured one, and the next present captures.
  CHECK(shouldCapture({false, false, true, 2, 2, 1, 2}));

  // RULE 3 (2026-11-27). The present that completes a frame (it lands whole,
  // or its sweep reaches the foot) held its flip ~35 ms for the readback. It
  // is read back on the NEXT present (same picture, served from cache).
  CHECK(!shouldCapture({false, false, true, 5, 7, 1, 1, true}));
  CHECK(shouldCapture({false, false, true, 5, 7, 1, 1, false}));
  // ...but never at the cost of the two captures that cannot wait: no picture
  // yet, and a glass that changed size.
  CHECK(shouldCapture({false, false, false, 0, 7, 1, 1, true}));
  CHECK(shouldCapture({false, true, true, 5, 7, 1, 1, true}));

  // THE DEPOSIT GATE (2026-09-04). A page turn deposits the previous glass as
  // afterglow; a polarity flip must not -- it bumps the sequence, so every
  // other input reads exactly like a page turn, and the light page went into
  // the accumulator at full intensity on every dark-mode switch.
  using glasscapture::shouldDeposit;
  CHECK(shouldDeposit({true, true, true, true, false, true}));
  CHECK(!shouldDeposit({true, true, true, true, true, true}));
  CHECK(!shouldDeposit({false, true, true, true, false, true}));  // nothing new
  CHECK(!shouldDeposit({true, false, true, true, false, true}));  // no glass yet
  CHECK(!shouldDeposit({true, true, false, true, false, true}));  // already deposited
  CHECK(!shouldDeposit({true, true, true, false, false, true}));  // size stale
  // A LIGHT page turn is paper and deposits nothing -- or the warm light
  // deposit rides into the next dark flip (review 2026-09-04, second pass).
  CHECK(!shouldDeposit({true, true, true, true, false, false}));
  // And the beam agrees with it, so a reconvert neither sweeps nor glows.
  CHECK(glasscapture::shouldArmBeam(true, true, false, true));
  CHECK(!glasscapture::shouldArmBeam(true, true, true, true));
  CHECK(!glasscapture::shouldArmBeam(false, true, false, true));
  CHECK(!glasscapture::shouldArmBeam(true, false, false, true));

  // THE STALE SWEEP (2026-11-27, docs/menu-nav-lag-2026-11-27.md). A fast
  // menu step arrives before the previous frame's sweep reached its finishing
  // present, so the capture still holds the picture from before that frame.
  // Sweeping over it would put the older picture back on the glass, so the
  // new frame lands whole. Fails against the three-input gate, which armed.
  CHECK(!glasscapture::shouldArmBeam(true, true, false, false));
  // ...and once that frame has landed whole and been captured, the next one
  // sweeps again.
  CHECK(glasscapture::shouldArmBeam(true, true, false, true));
  // A stale capture changes nothing for a present with no new picture.
  CHECK(!glasscapture::shouldArmBeam(false, true, false, false));

  // THE FADE CUT (2026-11-27, owner report with a recording from the Picco
  // app: "fading out is not smooth as it should be"). A press lands while the
  // previous step's afterglow is still fading, so the new frame arms a sweep.
  // Below the beam the glass is the old frame's capture, which holds no trail;
  // a trail clipped to the swept band took the live afterglow off everything
  // the beam had not reached, in one frame (recording frames 456-457: the old
  // page's ghost gone, back at 458 under the beam). Under MAXIMUM -- Metal,
  // the phone -- the trail is drawn over the whole glass during the sweep.
  using glasscapture::clipTrailToSweptBand;
  CHECK(!clipTrailToSweptBand(true, true));
  // The ADD fallback (the desktop's software renderer) keeps the clip: there
  // the fresh deposit would light the old frame a second time (x1.175).
  CHECK(clipTrailToSweptBand(true, false));
  // No sweep, no clip, on either blend.
  CHECK(!clipTrailToSweptBand(false, true));
  CHECK(!clipTrailToSweptBand(false, false));

  // The exit code is the gate (run_all.sh reads nothing else). This used to
  // print "all checks passed" mid-file and return 0 whatever CHECK counted,
  // so a broken rule failed loudly and passed the suite (adversarial review,
  // 2026-11-27).
  if (testcheck::g_failures != 0) {
    std::printf("glass_capture_test: %d check(s) FAILED\n", testcheck::g_failures);
    return 1;
  }
  std::printf("glass_capture_test: all checks passed\n");
  return 0;
}
