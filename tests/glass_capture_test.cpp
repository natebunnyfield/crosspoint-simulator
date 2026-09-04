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

  std::printf("glass_capture_test: all checks passed\n");

  // THE DEPOSIT GATE (2026-09-04). A page turn deposits the previous glass as
  // afterglow; a polarity flip must not -- it bumps the sequence, so every
  // other input reads exactly like a page turn, and the light page went into
  // the accumulator at full intensity on every dark-mode switch.
  using glasscapture::shouldDeposit;
  CHECK(shouldDeposit({true, true, true, true, false}));
  CHECK(!shouldDeposit({true, true, true, true, true}));
  CHECK(!shouldDeposit({false, true, true, true, false}));  // nothing new
  CHECK(!shouldDeposit({true, false, true, true, false}));  // no glass yet
  CHECK(!shouldDeposit({true, true, false, true, false}));  // already deposited
  CHECK(!shouldDeposit({true, true, true, false, false}));  // size stale
  // And the beam agrees with it, so a reconvert neither sweeps nor glows.
  CHECK(glasscapture::shouldArmBeam(true, true, false));
  CHECK(!glasscapture::shouldArmBeam(true, true, true));
  CHECK(!glasscapture::shouldArmBeam(false, true, false));
  CHECK(!glasscapture::shouldArmBeam(true, false, false));

  return 0;
}
