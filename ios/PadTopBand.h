#pragma once

#include <algorithm>

// THE IPAD BAND ABOVE THE PAPER -- extracted from layoutPadTablet
// (ios/CrossPointIOSShim.cpp) so the floor that keeps it alive can be host
// tested, the way ios/HostKeyboardState.h and ios/ZenPrefSync.h were
// extracted for the identical reason: every failure mode in this area is
// SILENT.
//
// Owner ruling 2026-08-29 (docs/ipad-layout-2026-08-29.md, "AN AREA ABOVE THE
// PAPER" and the two RULINGs at its foot): the tablet gets a black band above
// the paper, split 1 unit above the panel to 2 units below it, off the height
// left over once the panel's own scale-fit height is set aside --
//
//   unit  = max(0, (outHpx - panelHpx) / 3)
//   above = 1 * unit
//   below = 2 * unit
//
// THE FLOOR IS THE PART THAT IS NOT OBVIOUS FROM READING THE FORMULA. Hiding
// the status bar (CrossPointAppearance_hideStatusBarOnIPad) makes
// SDL_GetWindowSafeArea report safeTop == 0 on the very next layout pass --
// this iPad has no notch, so the status bar was the only reason iOS reserved
// anything at the top, and once it is confirmed hidden the safe area
// collapses to nothing. In ordinary operation the derived `unit` (~194 pt on
// an iPad Pro 13 M4 portrait) dwarfs the floor and nothing here is visible;
// the floor exists for the DEGENERATE case -- a very short available height
// (unit collapses toward 0, as happens whenever panelHpx approaches outHpx),
// or a device with a genuine notch/Island that safeTop would otherwise cover
// for. Found by measurement, not by reading the code: a boot log reading
// `card=0.0px` and a screenshot with no band at all, on the very launch pass
// after the status-bar fix took effect, from a build that had NOT yet floored
// cardTopPx. Owner, asked whether 16 pt (kPadEdgeMin) is the right floor now
// that the status bar is confirmed hidden: "keep 16 pt, and add a test." This
// header, and tests/pad_top_band_test.cpp, are that test.
//
// PURE ON PURPOSE. No SDL, no UIKit -- SDL_GetWindowSafeArea cannot be driven
// from a host at all, which is exactly why the decision has to live somewhere
// a host test CAN drive it directly, the same reasoning HostKeyboardState.h
// and ZenPrefSync.h give for themselves.
namespace padtopband {

struct Result {
  float unit;       // the 1-unit outer band, in device px -- also the corner
                     // radius circle (paintTopBezel, paintBottomFillets) and
                     // the horizontal paper-to-panel gap unit (g_paperGapPx).
  float cardTopPx;   // where black ends and paper begins, in device px.
  float belowPx;     // the reserved band below the panel, in device px --
                      // always 2x `unit` unless the floor bound cardTopPx,
                      // in which case it is whatever height is left over.
};

// `outHpx`/`panelHpx` are already in DEVICE pixels (W*S / the panel's own
// scale-fit height). `safeTop`/`kPadEdgeMin` are in POINTS -- the same units
// SDL_GetWindowSafeArea reports and layoutPadTablet's own kPadEdgeMin
// constant is declared in -- and are converted to device px by `* S` here,
// exactly as the inline construction this was extracted from did.
inline Result compute(float outHpx, float panelHpx, float safeTop,
                      float kPadEdgeMin, float scale) {
  const float unit = std::max(0.0f, (outHpx - panelHpx) / 3.0f);
  // THE FLOOR: cardTopPx can never fall below kPadEdgeMin (nor below whatever
  // the system safe area legitimately reports), converted to device px.
  // Removing this max() is exactly the regression this header exists to
  // catch -- see tests/pad_top_band_test.cpp's "the floor is load-bearing"
  // case, which fails against a copy of this function with the max() taken
  // out.
  const float cardTopPx =
      std::max(unit, std::max(safeTop, kPadEdgeMin) * scale);
  const float belowPx = std::max(0.0f, outHpx - cardTopPx - panelHpx);
  return Result{unit, cardTopPx, belowPx};
}

}  // namespace padtopband
