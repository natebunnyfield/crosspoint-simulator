#pragma once
// WHEN THE GLASS IS RE-CAPTURED -- the one decision behind every phosphor
// trail and beam sweep: is the picture in glassPrevTexture still the picture
// the eye last saw? Pure, host-tested (tests/glass_capture_test.cpp).
//
// The capture used to be gated on the panel's own sequence number alone: one
// readback per NEW PAGE, never during a sweep. That answered the wrong
// question. The glass is the COMPOSED output -- page, letterpress, pad,
// surround -- and the overlay repaints that composition without any page
// changing: a keyboard rising, a zen toggle, a pad relayout, and above all the
// FIRST PRESENT OF A SESSION, where the harness has not laid the pad out yet,
// paints the whole glass black (the zen band with a zero geometry is the full
// screen), and only its own layout, one present later, draws the real frame.
// Both presents carry the same sequence number, so the first capture -- the
// black one -- was kept, and the first page turn of every session swept the
// new page in over a black "previous frame". S-035, the half of it that the
// beam-arming fix did not touch.
//
// So the second input: a GENERATION that every present request outside the
// two self-driving loops bumps (SimulatorOverlay::requestPresent, the dial
// setters, the content path). A present that a sweep or a trail asked for
// itself changes nothing the capture should see; every other present may, and
// pays one readback (measured 2-6% of a dark page turn on a phone) to be sure.
#include <cstdint>

namespace glasscapture {

struct Inputs {
  bool beamSweeping;    // the beam is mid-sweep on this present
  bool sizeStale;       // the glass textures do not match the output size
  bool hasPicture;      // a capture has ever succeeded at this size
  uint64_t glassSeq;    // the panel sequence the glass was captured at
  uint64_t presentSeq;  // the panel sequence this present shows
  uint64_t glassGen;    // the request generation the glass was captured at
  uint64_t presentGen;  // the request generation sampled at the TOP of this
                        // present -- before the overlay draws, because the
                        // overlay's own layout may request the NEXT present,
                        // and that request must not be consumed by this one
};

// True when this present should read the output back into the glass.
// Rule 1: never mid-sweep, unless the size is stale (a half-swept frame
// records mostly the OLD page and hands it back as the new one; a size change
// overrides because there is no coherent old picture to sweep from once the
// glass has changed shape). Rule 2: capture when there is no picture, when the
// page moved, when the size moved, or when anything other than a self-driving
// loop asked for this present.
inline bool shouldCapture(const Inputs &in) {
  if (in.beamSweeping && !in.sizeStale) return false;
  if (!in.hasPicture || in.sizeStale) return true;
  if (in.glassSeq != in.presentSeq) return true;
  return in.glassGen != in.presentGen;
}

}  // namespace glasscapture
