#pragma once

// Where the published page lands on the glass, in SCREEN POINTS.
//
// Pure, and a free header, for the same reason PanelPalette.h and
// PhosphorGrain.h are: it lives in ios/CrossPointAccessibility.mm otherwise,
// which compiles nowhere but a Mac and runs nowhere but a phone -- and every
// failure mode of this arithmetic is SILENT. A wrong scale puts every
// accessibility frame and every read-aloud highlight in the wrong place while
// the text itself is perfectly correct, so nothing logs, nothing crashes, and
// the only symptom is an assistive technology quietly skipping elements it
// considers off-screen. That has shipped twice: once as a half-size highlight
// (DISPLAY_HEIGHT used where LOGICAL_HEIGHT was meant) and once as the
// off-screen-frames warning the container still carries.
//
// The three inputs are all things the simulator already publishes:
//   * SimulatorOverlay::panelLeftPx / panelBottomPx / panelWidthPx /
//     panelHeightPx -- the PRESENTED panel rect, in DEVICE pixels.
//   * HalDisplay::LOGICAL_HEIGHT -- the panel's logical portrait WIDTH (the
//     landscape framebuffer's height), which is the unit ReadAloudWordRect
//     uses. NOT DISPLAY_HEIGHT: that one is multiplied by
//     CROSSPOINT_RENDER_SCALE, and the render scale has been 1, 2 and 3 on
//     iOS within a fortnight. Deriving the scale from the PRESENTED width
//     makes the answer independent of it -- which is the property this header
//     exists to hold on to.
//   * the screen's backing scale, because accessibilityFrame is in points.

#include <cmath>

namespace readaloud {

struct PanelGeometryPts {
  // Top-left of the presented page, in screen points.
  double x0 = 0;
  double y0 = 0;
  // Multiply a ReadAloudWordRect's logical panel pixels by this to get points.
  double scale = 0;
};

// False when the panel has not presented yet (every dimension is 0 until the
// first present) or when the build's logical geometry is nonsense. The caller
// must treat false as "not answerable YET" and retry -- a rebuild that races
// the first frame is normal, and the container's level-triggered self-heal
// depends on this returning false rather than a plausible zero.
inline bool panelGeometryPts(int panelLeftPx, int panelBottomPx, int panelWidthPx,
                            int panelHeightPx, int logicalHeight, double screenScale,
                            PanelGeometryPts *out) {
  if (!out) return false;
  if (panelWidthPx <= 0 || panelHeightPx <= 0) return false;
  if (logicalHeight <= 0) return false;
  // A screen that reports no scale is a 1x screen, not a divide-by-zero.
  const double s = screenScale > 0 ? screenScale : 1.0;
  out->scale = (static_cast<double>(panelWidthPx) / logicalHeight) / s;
  out->x0 = panelLeftPx / s;
  // panelBottom is published as an EDGE (y + h), so the top is recovered by
  // subtracting the height. Reading it as an origin puts the page a full panel
  // below itself, which on a phone is entirely off the bottom of the screen.
  out->y0 = (panelBottomPx - panelHeightPx) / s;
  return true;
}

}  // namespace readaloud
