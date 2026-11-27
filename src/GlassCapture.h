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
  bool deferToNext = false;  // this present completes a new frame on the
                             // glass -- it landed whole, or its sweep reached
                             // the foot -- so its readback waits for the next
                             // present, which the caller requests
};

// True when this present should read the output back into the glass.
// Rule 1: never mid-sweep, unless the size is stale (a half-swept frame
// records mostly the OLD page and hands it back as the new one; a size change
// overrides because there is no coherent old picture to sweep from once the
// glass has changed shape). Rule 2: capture when there is no picture, when the
// page moved, when the size moved, or when anything other than a self-driving
// loop asked for this present.
//
// Rule 3 (2026-11-27): the present that COMPLETES a frame -- the one where it
// lands whole, or where its sweep reaches the foot of the glass -- does not
// read back; the next present does. The readback sits before the flip, so
// taking it here held the frame's last rows off the glass for ~35 ms (iOS
// Simulator, iPhone 17) on every menu step. The next present composes the same
// glass from cache, so it reads back the same picture.
inline bool shouldCapture(const Inputs &in) {
  if (in.beamSweeping && !in.sizeStale) return false;
  if (!in.hasPicture || in.sizeStale) return true;
  if (in.deferToNext) return false;
  if (in.glassSeq != in.presentSeq) return true;
  return in.glassGen != in.presentGen;
}

// WHETHER A NEW PICTURE ARRIVED, for the two consumers of the previous glass.
// `reconvertOnly` is a polarity flip: the panel's sequence moved but the page
// did not, so there is nothing to sweep in and -- the half that was missing
// until 2026-09-04 -- nothing that left the glass to deposit as afterglow.
// A light->dark flip deposited the light page (captured at absolute
// intensity) into the accumulator and the whole glass flashed and faded.
//
// `captureIsCurrent`: the capture holds the picture this present REPLACES
// (its seq is the one the glass was showing). A sweep paints the new frame
// down over the capture, so a stale capture puts an OLDER picture back on
// the screen first. That happened on every fast menu step (2026-11-27,
// docs/menu-nav-lag-2026-11-27.md): the coalescing hold blocks every present,
// including the one that would finish a sweep and re-capture, so with presses
// under ~165 ms apart on the iOS Simulator each new sweep started over the
// glass from BEFORE the burst and the selection jumped back to where the
// burst began: 9 of the 11 sweeps. Such a frame lands whole instead (and is read
// back on the next present, rule 3 above).
inline bool shouldArmBeam(const bool contentChanged, const bool hasPicture,
                          const bool reconvertOnly,
                          const bool captureIsCurrent) {
  return contentChanged && hasPicture && !reconvertOnly && captureIsCurrent;
}

struct DepositInputs {
  bool contentChanged;  // the panel sequence moved since the last present
  bool hasPicture;      // a glass capture exists
  bool freshGlass;      // this glass has not been deposited yet
  bool sizeMatches;     // the intensity texture exists at the output size
  bool reconvertOnly;   // the sequence moved for a polarity flip, not a page
  bool darkGround;      // the page is a tube (dark polarity), not paper
};

// A LIGHT page is paper, and paper leaves no phosphor: the accumulator is
// never composited on a pale ground, so a light deposit was invisible -- but
// it sat in the texture, still warm, and a light->dark flip inside 2.4 trails
// of the last light page turn composited it over the new dark page (the
// firmware's own Dark Mode row is exactly that sequence: arrow onto the row,
// which re-renders the list, then Confirm). Measured +17.6 luma on the flip
// frame with the light deposit 272 ms old (adversarial review 2026-09-04,
// second pass). So the ground gates the deposit itself.
inline bool shouldDeposit(const DepositInputs &in) {
  return in.contentChanged && in.hasPicture && in.freshGlass && in.sizeMatches &&
         !in.reconvertOnly && in.darkGround;
}

}  // namespace glasscapture
