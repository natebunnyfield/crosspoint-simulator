#pragma once

// THE TURNED PAGE'S LANDSCAPE, decided purely (docs/turned-page-landscape-plan-2026-10-04.md).
//
// A wide-table page ([T-021] in the firmware's TODO.md) is drawn on an ordinary
// portrait page with its TABLE turned clockwise -- header down the page's right
// edge -- so the reader turns the device COUNTER-clockwise to read it. The
// firmware publishes when one is up (HalGPIO::publishTurnedPage, read through
// SimulatorOverlay::turnedPageShowing). While it is, the iOS app accepts
// landscape; turned counter-clockwise, the app rotates, the page is presented
// as the panel's native landscape frame (HalDisplay substitutes
// LandscapeCounterClockwise -- on this page that frame IS the table the right
// way up), and the pad splits to the two side margins (G3). On the next upright
// page the app snaps back to portrait.
//
// THE DIRECTION WAS MIXED UP FOR ONE BUILD. TestFlight 304 flipped the page to
// read after a clockwise turn and rotated the phone on a clockwise turn, from a
// reading of the 2026-08-19 ruling as the reader's turn; the owner, 2026-10-04:
// "the iphone would need to be turned ccw not clockwise, you've mixed things
// up". "Clockwise" names the TABLE's rotation on the page; the device's turn is
// always the opposite one (crosspoint-reader docs/ui-conventions.md).
//
// Everything here is pure, because every way it fails is silent: a wrong hint
// leaves the phone unable to rotate (or rotating on every page), and a wrong
// rect puts a control under the page or the Dynamic Island. Host-tested by
// tests/turned_page_landscape_test.cpp.
//
// Owner rulings it encodes, 2026-10-04 (all in the plan doc):
//   Q1  rotate the app with the phone while a turned page shows;
//   Q2  snap back to portrait on the next upright page, even held sideways;
//   Q3  the pad beside the page when zen is off; zen keeps no pad;
//   Q3b G3: the pad SPLIT, today's left half (Back/Select, Power) in the left
//       margin, its right half (Left/Right, Up/Down) in the right; paper on the
//       panel only;
//   Q4  the zone gestures follow the landscape page's edges;
//   Q5  phone and iPad.
// Standing ruling 2026-08-19, corrected 2026-10-04: the table turns clockwise,
// so the reader turns the phone COUNTER-clockwise, and the phone gains exactly
// that one landscape -- UIInterfaceOrientationLandscapeRight, the home edge on
// the RIGHT (UIKit's interface orientations are named for where the content
// rotates, so "Right" is the counter-clockwise DEVICE turn). Verified in the
// iOS Simulator by its own screen capture, which is in DEVICE coordinates: the
// app's landscape puts the UI's top along the device's right edge.

namespace turnedpage {

// The SDL_HINT_ORIENTATIONS value the iOS host should hold.
//   phone: "Portrait" -- except while a turned page shows, when the
//          counter-clockwise landscape ("LandscapeRight") joins it. SDL re-reads the hint on every UIKit query
//          (SDL_uikitwindow.m, UIKit_GetSupportedOrientations), so changing it
//          and asking UIKit to re-query is the whole mechanism, and dropping it
//          is the snap-back: the current landscape stops being supported.
//   iPad:  unchanged, portrait and both landscapes always (ruling 2026-08-17);
//          the string must stay the one simulator_main.cpp sets at startup.
//   forceLandscape: a QA hatch (CROSSPOINT_SIM_FORCE_TURNED_LANDSCAPE=1). While
//          a turned page shows, the device supports landscape ONLY, so iOS
//          rotates the interface with no hand on the device -- a script cannot
//          turn the iOS Simulator. On the iPad that is both landscapes, its own
//          two. Inert on upright pages.
inline const char *hintFor(bool isPad, bool turned, bool forceLandscape) {
  if (isPad)
    return turned && forceLandscape ? "LandscapeLeft LandscapeRight"
                                    : "Portrait LandscapeLeft LandscapeRight";
  if (!turned) return "Portrait";
  return forceLandscape ? "LandscapeRight" : "Portrait LandscapeRight";
}

// Whether the landscape presentation applies: a turned page in a window wider
// than tall. Both halves are needed -- the phone only ever goes landscape while
// a turned page shows, but the iPad is landscape whenever it is held so, and an
// upright page there keeps the iPad's own landscape layout.
inline bool presentLandscape(bool turned, int winW, int winH) {
  return turned && winW > winH;
}

struct Rect {
  float x = 0, y = 0, w = 0, h = 0;
};

// The landscape layout, in POINTS. The four insets bound the panel (the host
// hands them to SimulatorOverlay as device pixels; the panel is fitted into the
// box they leave, centered). The controls are today's seven, split as G3.
struct Layout {
  float insetLeft = 0, insetRight = 0, insetTop = 0, insetBottom = 0;
  Rect back, confirm, left, right, power, up, down;
  Rect chip;           // the keyboard chip, above Back/Select in the left margin
  bool padShown = false;
};

// Constants shared with the portrait phone layout (CrossPointIOSShim.cpp), so a
// control is the same size turned as it is upright.
constexpr float kCell = 60.0f;        // kOptimalSquare: the owner-picked square
constexpr float kCellH = 64.0f;       // kCell snapped to the 8 pt grid, as kCellH upright
constexpr float kPowerH = 32.0f;      // POWER stays half height (ruling 2026-08-11)
constexpr float kMargin = 16.0f;      // the phone's side inset (ruling 2026-08-11)
constexpr float kRowClear = 16.0f;    // between the upper and lower rows
constexpr float kChip = 48.0f;        // the keyboard chip's square
constexpr float kEdgeMin = 8.0f;      // never closer than this to a screen edge
constexpr float kHalf = 32.0f;        // the tablet's half-height bottom row (layoutPadTablet)
constexpr float kHomeMin = 16.0f;     // kHomeInsetMin: the bottom floor on a device with no safe area
constexpr float kThumbRowFromBottom = 448.0f;   // the TABLET's thumb row (owner ruling 2026-08-09, iPad only)
constexpr float kBand = 2.0f * kCell + 2.0f * kMargin;   // one side's pad band

// W x H: the window in points (W > H). safe*: the window's safe-area insets in
// points (in landscape the Dynamic Island is in one side inset and the home
// indicator in the bottom one). zen: no pad, the page as large as the height
// allows; the bands are only the safe areas.
// isPad: the iPad keeps ITS OWN control placement (owner Q5: "its own landscape
// layout"): the front pairs on the tablet's thumb row, 448 pt up from the bottom
// edge (ruling 2026-08-09, iPad only), and POWER and the page rocker at half
// height along the bottom, exactly as layoutPadTablet places them. The phone
// keeps its own: full-height rows grown up from the bottom, POWER half height.
inline Layout layoutFor(float W, float H, float safeL, float safeR, float safeT,
                        float safeB, bool zen, bool isPad = false) {
  Layout L;
  const float edgeL = safeL > kEdgeMin ? safeL : kEdgeMin;
  const float edgeR = safeR > kEdgeMin ? safeR : kEdgeMin;
  L.insetTop = safeT > kEdgeMin ? safeT : kEdgeMin;
  L.insetBottom = safeB > kEdgeMin ? safeB : kEdgeMin;
  L.padShown = !zen;
  if (zen) {
    L.insetLeft = edgeL;
    L.insetRight = edgeR;
    return L;   // no controls: zen keeps no pad (Q3)
  }
  L.insetLeft = edgeL + kBand;
  L.insetRight = edgeR + kBand;
  const float xL = edgeL + kMargin;                     // left pair's left edge
  const float xR = W - edgeR - kMargin - 2.0f * kCell;  // right pair's left edge
  if (isPad) {
    const float bottom = safeB > kHomeMin ? safeB : kHomeMin;
    const float lowerY = H - bottom - kHalf;
    const float midY = H - kThumbRowFromBottom - kCell / 2.0f;
    L.back = {xL, midY, kCell, kCell};
    L.confirm = {xL + kCell, midY, kCell, kCell};
    L.left = {xR, midY, kCell, kCell};
    L.right = {xR + kCell, midY, kCell, kCell};
    L.power = {xL, lowerY, kCell, kHalf};
    L.up = {xR, lowerY, kCell, kHalf};
    L.down = {xR + kCell, lowerY, kCell, kHalf};
    L.chip = {xL + kCell - kChip / 2.0f, midY - kRowClear - kChip, kChip, kChip};
    return L;
  }
  // The phone: both rows anchored to the bottom of the safe area, the lower row
  // first, as the portrait phone grows its rows up from the bottom -- the thumbs
  // of a two-handed landscape grip rest low on the sides.
  const float lowerY = H - L.insetBottom - kCellH;
  const float upperY = lowerY - kRowClear - kCellH;
  L.back = {xL, upperY, kCell, kCellH};
  L.confirm = {xL + kCell, upperY, kCell, kCellH};
  L.left = {xR, upperY, kCell, kCellH};
  L.right = {xR + kCell, upperY, kCell, kCellH};
  L.power = {xL, lowerY + (kCellH - kPowerH), kCell, kPowerH};   // hangs from the row's bottom
  L.up = {xR, lowerY, kCell, kCellH};
  L.down = {xR + kCell, lowerY, kCell, kCellH};
  L.chip = {xL + kCell - kChip / 2.0f, upperY - kRowClear - kChip, kChip, kChip};
  return L;
}

}  // namespace turnedpage
