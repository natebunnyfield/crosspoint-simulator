// CrossPoint X3 -> iPhone harness.
//
// THE MODEL. The iPhone impersonates X3 peripherals; it is not a new CrossPoint
// board. There are two surfaces and exactly one translation point between them:
//
//   harness layer (this file)  draws an on-screen button pad and reads touches
//                              on it. Lives outside the simulated device.
//   device layer (HalGPIO)     sees only the X3's seven GPIO buttons, by index.
//
// The harness translates the first into the second by calling HalGPIO's
// platform-neutral live-injection API, gpio.injectButtonDown/Up(BTN_*). The
// device layer cannot tell an injected button from a keyboard one, so no
// #if TARGET_OS_IPHONE appears in HalGPIO or the firmware.
//
// hasTouch() stays false for X3 and iPhone touches become BUTTON events, never
// touch events. Hit-testing happens HERE, above SDL; no coordinate is ever handed
// to the firmware. Letting one reach the hasTouch() branch would make the
// firmware take X4-Pro-only paths and we would be testing a device that does not
// exist.
//
// ONE CONTROL PER PHYSICAL BUTTON, and nothing else. Each is down-on-touch and
// up-on-lift, so it expresses a genuine hold -- which is what page-turn
// autorepeat and long-press-to-sleep need.
//
// PURE PASSTHROUGH, enforced by construction: the finger->button decisions
// live in PadCore (ios/PadCore.h), whose API cannot express time, so no
// gesture is ever widened, stretched, or delayed. (A POWER "tap-to-sleep"
// stretch used to live here; it kept the injected button down 600 ms past the
// finger, which read as a stuck control and desynced the pad from the device.
// Sleep is a real 400 ms hold now, exactly like the hardware.)
//
// There are no timed gestures on this surface (the movable-pad grabber, once
// the only one, was removed 2026-08-02). If a future chrome gesture needs a
// timer, it belongs out here in the harness -- never in PadCore.
//
// WHY AN EVENT WATCH, NOT A POLL LOOP. HalGPIO::update() owns the SDL event pump
// for the whole simulator and must keep owning it -- two pollers would split
// events between them. SDL_AddEventWatch observes events as they are queued
// without consuming them, so the harness sees finger events that HalGPIO simply
// ignores, and neither steals from the other.
//
// WHY NOT SDL_PushEvent. The pad used to inject by pushing synthetic
// SDL_EVENT_KEY_DOWN / _UP. Measured, not assumed: SDL_PushEvent delivers an
// event to the queue but does NOT update SDL's internal keyboard state array,
// which is written only on the real-input path. Edge reads (wasPressed /
// wasReleased) came off the dequeued event and worked; every level read
// (isPressed, getHeldTime, getPowerButtonHeldTime) consults
// SDL_GetKeyboardState() and stayed false, so nothing timed off a HELD button
// could fire -- long-press-to-sleep and the reader's font-family hold both died
// there. injectButtonDown/Up writes the press edge, the held level and the press
// timestamp together, so a hold expressed by a finger survives all the way down.

#include "CrossPointHarness.h"

#include <SDL3/SDL.h>

#include <cstdint>

#include "CrossPointAppearance.h"
#include "CrossPointPrefs.h"
#include "CrossPointAccessibility.h"
#include "CrossPointKeyboardBar.h"
#include "CrossPointReadAloud.h"
#include "HalDisplay.h"
#include "HalGPIO.h"
#include "PadCore.h"
#include "SimulatorBuildIdentity.h"
#include "SimulatorOverlay.h"

namespace {

// --- The X3's seven buttons ------------------------------------------------
//
// One control per HalGPIO::BTN_* index, and nothing else. There is no control
// for the simulator's own SLEEP (`S`): that is a harness command, not a button
// the hardware has. There is no HOME either -- hasHomeKey() is X4-Pro-only.
//
// PLACEMENT is specified, not derived. Nothing in this source tree encodes where
// the buttons physically sit on the X3 chassis -- the SDK describes them only
// electrically (six on a resistor ladder across two ADC pins, POWER on its own
// digital pin; BoardConfig InputPins, InputStyle::XteinkAdcLadder). See
// layoutPad() for the arrangement.
//
// SIZING: full-height controls are 60-96 pt squares, comfortably over the HIG
// 44 pt minimum. The bottom row is a deliberate exception -- half-height
// (34-40 pt), approved as-shown 2026-08-02; see the trade-off note above
// layoutPad(). Bands stay inset clear of the Dynamic Island at the top and the
// home indicator at the bottom.
//
// The controls are UNLABELLED -- no glyph, no text. The pad names nothing about
// what each button does, which puts the whole affordance on the pressed state;
// see the palette below for how that is paid for.
struct PadButton {
  uint8_t button;  // HalGPIO::BTN_*
  const char *name;
  SDL_FRect rect{};
};

PadButton g_pad[] = {
    {HalGPIO::BTN_BACK, "BACK"},
    {HalGPIO::BTN_POWER, "POWER"},
    {HalGPIO::BTN_UP, "UP"},
    {HalGPIO::BTN_LEFT, "LEFT"},
    {HalGPIO::BTN_CONFIRM, "CONFIRM"},
    {HalGPIO::BTN_RIGHT, "RIGHT"},
    {HalGPIO::BTN_DOWN, "DOWN"},
};
constexpr int kPadBack = 0, kPadPower = 1, kPadUp = 2, kPadLeft = 3,
              kPadConfirm = 4, kPadRight = 5, kPadDown = 6;
constexpr int kPadCount = 7;

// The keyboard chip. NOT a PadButton and deliberately not in g_pad: it presses
// no hardware button, so it is not a control the rule above is about -- it is
// the way back from a state the platform has no way out of. It is drawn only
// while a text field is open with the keyboard down, and it sits in the bottom
// row's middle columns, which the pad has always left empty. Tapping it and
// tapping the page do the same thing; the chip exists to say so.
SDL_FRect g_kbChip{};

bool g_padLaidOut = false;
float g_ptScale = 3.0f;
SDL_WindowID g_windowId = 0;

// All finger->button decisions. The SDL adapter below owns NO button state:
// PadCore decides, applyActions() injects. Unit-tested in
// tests/pad_core_test.cpp.
PadCore g_core(kPadCount);

// The grabber (a drag handle that let the rows follow the finger) is GONE —
// owner-approved layout 2026-08-02 removed it along with its hold timer and
// offset machinery. The pad is fixed: top row hugs the panel, bottom row is
// anchored at the screen's bottom edge.

// The single translation point between the two layers. Called from the event
// watch, which runs inside SDL_PumpEvents inside HalGPIO::update() -- i.e. after
// beginFrame() has cleared the frame's edge latches and before the firmware
// reads them, exactly the window the SDL keyboard path writes in.
void applyActions(const std::vector<PadCore::Action> &actions) {
  for (const PadCore::Action &a : actions) {
    if (a.type == PadCore::Action::Press)
      gpio.injectButtonDown(g_pad[a.slot].button);
    else
      gpio.injectButtonUp(g_pad[a.slot].button);
    SDL_Log("[harness] %s %s", g_pad[a.slot].name,
            a.type == PadCore::Action::Press ? "down" : "up");
  }
  if (!actions.empty()) SimulatorOverlay::requestPresent();
}

// --- Layout ----------------------------------------------------------------
//
// All dimensions in points, converted once. HIG minimums are expressed in
// points, so laying out in pixels would silently shrink the targets on a device
// with a different scale factor.
// Owner-approved layout 2026-08-02 (mockups: pad_layout_review artifact):
//
//     [Back|Select]      [Left|Right]        <- front rockers, full squares,
//                                               hugging the panel's bottom edge
//     [Power]              [Up|Down]         <- half-height row, anchored at
//                                               the screen bottom, clear of the
//                                               home indicator
//
// UP/DOWN are the X3's SIDE buttons (MappedInputManager keeps them fixed as
// page-turn/Up/Down; main.cpp calls BTN_UP the "left side button") — fused
// into one rocker at the right. BACK/SELECT/LEFT/RIGHT are the FRONT buttons
// (the remappable frontButton* set), fused pairs as on the chassis. Fused
// pairs share an edge -- no gap inside a pair, a wide gap between pairs.
//
// KNOWN TRADE-OFF, approved as-shown: the half-height row's targets run
// 34-40pt tall, under the 44pt HIG minimum. If page-turns feel cramped on
// device, the agreed fallback is invisible hit-slop extending the bottom-row
// targets upward -- visuals unchanged.
//
// The top row hugs the panel (SimulatorOverlay::panelBottomPx) so thumbs rest
// at the page; before the first present it falls back to sitting just above
// the bottom row.
// KEYBOARD CLEARANCE (owner ruling 2026-08-09: "move panel up so ios full
// keyboard would not overlap it (can be dynamic, if needed to be)").
//
// The iOS keyboard covers the bottom ~25% of the screen and used to bury the
// firmware's own key grid and the lower pad rows -- the panel did not move.
// This is the dynamic answer: the harness publishes the keyboard's height as
// it animates, layoutPad* adds it to the reserved bottom band, and the panel's
// existing top-aligned fit lifts the page clear. Zero when no keyboard is up,
// so the ordinary reading layout is byte-identical to before.
//
// Point coordinates, like everything else in this file.
float g_keyboardHeightPt = 0.0f;

// Where the TABLET's side rocker rows sit: a fixed distance UP FROM THE BOTTOM
// EDGE, in points (owner ruling 2026-08-09, iPad only). Not a fraction of
// screen height -- that moves the buttons to a different physical spot on
// every device, which was the complaint. Points are near enough physical
// across iOS devices, so one number puts the row under the same thumb on every
// iPad.
//
// The PHONE does not use this. It is held differently -- one hand, thumb
// sweeping up from the bottom corner -- and its owner-approved layout hugs the
// panel instead. Applying this there moved a row nobody asked to move.
//
// 448 pt: the owner's 450 from an iPad Pro, snapped to the 8 pt grid (56 x 8)
// on their ruling. The 2 pt difference is invisible; grid alignment is free.
//
// No keyboard clamp, by ruling: "0 buffer from keyboard, no logic. keep it
// simple." At 450 the row clears a portrait iPad Pro keyboard (~400 pt) by
// 20 pt anyway, and every shorter keyboard by more.
constexpr float kThumbRowFromBottom = 448.0f;

constexpr float kOptimalSquare = 60.0f;      // owner-picked target size
constexpr float kHomeInsetFallback = 34.0f;  // when the safe area is unreadable
constexpr float kHomeInsetMin = 16.0f;  // floor for home-button devices (safe area 0)

// iPad (family 2) — owner-approved spec 2026-08-03 (ios/README.md, "iPad
// (family 2)"), implemented 2026-08-04. The tablet's spare dimension is WIDTH,
// so the pad moves into the side margins and the panel takes the full safe
// height, centered:
//
//   [Back|Select]  <- left margin,  |  [Left|Right]  <- right margin,
//      vertically centered          |     vertically centered
//   [Power]        <- bottom-left   |  [Up|Down]     <- bottom-right, same
//      in the same margin column    |     margin columns, half height
//
// None of the phone constraints apply here: no reserved bottom band (the pad
// is beside the page, not under it), no chassis gap (nothing hugs the panel's
// bottom edge), no kPipLift (a corner PiP window parks over margins or page,
// never over a control), no kTopReserve (the centered panel clears the status
// bar by construction).
//
// Cell = min(60 pt, margin fit): a fused pair is two cells wide, so the cell
// halves the margin when the margin is tighter than 2x60 — 60 pt everywhere
// except iPad mini portrait, whose 108 pt margin gives 54 pt cells.
//
// The panel is CENTERED by construction: this function replicates HalDisplay's
// manual fit over the full safe height, then sets the top and bottom insets to
// sandwich the panel exactly — availH equals the panel height, so HalDisplay's
// own fit lands on the same scale and its top margin term collapses to the
// band edge. One relayout after the first present settles the published
// panelBottom, same as the phone path.
void layoutPadTablet(float W, float H, float S) {
  float safeTop = 0.0f, safeBottom = 0.0f;
  if (SDL_Window *win = SDL_GetWindowFromID(g_windowId)) {
    int lw = 0, lh = 0;
    SDL_Rect safe{};
    if (SDL_GetWindowSize(win, &lw, &lh) && lh > 0 &&
        SDL_GetWindowSafeArea(win, &safe)) {
      safeTop = static_cast<float>(safe.y);
      safeBottom = static_cast<float>(lh - (safe.y + safe.h));
    }
  }

  // Panel fit, in device pixels, over the full safe height. The firmware
  // renders the X3 portrait, so the portrait framebuffer mapping applies
  // (logical width = DISPLAY_HEIGHT). Fractional scale below 1 is kept, same
  // as HalDisplay's fallback for windows shorter than the panel.
  const float logW = static_cast<float>(HalDisplay::DISPLAY_HEIGHT);
  const float logH = static_cast<float>(HalDisplay::DISPLAY_WIDTH);
  const float outWpx = W * S, outHpx = H * S;
  // The keyboard eats from the bottom of the usable height, so the centered
  // panel shrinks and rises rather than sitting under the keys.
  //
  // TABLET ONLY. "Overlap, not shrink" (owner ruling 2026-08-10) is an iPhone
  // ruling -- see the phone path -- and the reason it does not carry here is
  // that a tablet has the room. The panel is 1056x1584 device px at 2x, and an
  // iPad Pro clears that in the ~1900 px left after a 400 pt keyboard, so
  // reserving the height moves the page up without costing it a single integer
  // scale. On a phone the same reservation costs one, which is 40% of the text.
  const float availPx =
      SDL_max(1.0f, (H - safeTop - safeBottom - g_keyboardHeightPt) * S);
  float scale = SDL_min(outWpx / logW, availPx / logH);
  if (scale >= 1.0f) scale = SDL_floorf(scale);
  const float panelWpx = logW * scale, panelHpx = logH * scale;
  const float topPx = safeTop * S + (availPx - panelHpx) / 2.0f;
  SimulatorOverlay::setTopInset(static_cast<int>(topPx));
  SimulatorOverlay::setBottomInset(
      static_cast<int>(SDL_max(0.0f, outHpx - topPx - panelHpx)));

  const float margin = (W - panelWpx / S) / 2.0f;
  const float cell = SDL_min(kOptimalSquare, margin / 2.0f);
  const float half = cell / 2.0f;
  const float leftX = (margin - 2.0f * cell) / 2.0f;
  const float rightX = W - margin + leftX;
  const float midY = H - kThumbRowFromBottom - cell / 2.0f;
  // The keyboard lifts the bottom row with it. Without this the row -- POWER
  // and the page-turn rocker -- sits UNDER the keyboard and cannot be reached
  // while typing (the keyboard is its own window and eats the touches).
  //
  // KEPT on the tablet, dropped on the phone, and the asymmetry is the same one
  // kThumbRowFromBottom rests on: here the pad lives in the MARGINS BESIDE the
  // page, so lifting it costs the page nothing. The phone's pad is a band below
  // the page, and lifting that paints controls over the text.
  const float lowerY =
      H - g_keyboardHeightPt - SDL_max(safeBottom, kHomeInsetMin) - half;

  auto place = [&](int idx, float x, float y, float w, float h) {
    g_pad[idx].rect = {x * S, y * S, w * S, h * S};
  };

  place(kPadBack, leftX, midY, cell, cell);
  place(kPadConfirm, leftX + cell, midY, cell, cell);
  place(kPadLeft, rightX, midY, cell, cell);
  place(kPadRight, rightX + cell, midY, cell, cell);

  place(kPadPower, leftX, lowerY, cell, half);
  place(kPadUp, rightX, lowerY, cell, half);
  place(kPadDown, rightX + cell, lowerY, cell, half);

  // The keyboard chip, one cell wide and centred under the page -- the same
  // rule as the phone, in the only horizontal space the tablet's side-margin
  // pad leaves free. It rides with the lifted row so it stays clear of the
  // keyboard it toggles.
  g_kbChip = {((W - cell) / 2.0f) * S, lowerY * S, cell * S, half * S};
}

// Called from the keyboard notifications (CrossPointHarness). Height in
// POINTS, 0 when the keyboard is down. Cheap enough to call per frame of the
// animation: the relayout only fires when the integer point height changes.
extern "C" void CrossPointIOS_setKeyboardHeight(float heightPt) {
  if (heightPt < 0.0f) heightPt = 0.0f;
  const int before = static_cast<int>(g_keyboardHeightPt);
  g_keyboardHeightPt = heightPt;
  // An e-ink firmware presents rarely, so without this the new height changes
  // nothing on screen until the firmware happens to render a page. Storing it
  // silently is what made the keyboard-clearance lift look like it was not
  // working: the panel did move, on whatever render came next. Same guard as
  // the relayout, so the animation's intermediate frames cost one present each
  // and no more.
  if (static_cast<int>(heightPt) != before) SimulatorOverlay::requestPresent();
}

void layoutPad(int outW, int outH) {
  const float S = g_ptScale;
  const float W = static_cast<float>(outW) / S;
  const float H = static_cast<float>(outH) / S;

  static const bool s_isPad = CrossPointAppearance_isPad() == 1;
  if (s_isPad) {
    layoutPadTablet(W, H, S);
    return;
  }

  constexpr float kMargin = 20.0f;      // side inset
  constexpr float kGap = 16.0f;
  // Panel -> top row gap MATCHES THE CHASSIS (owner ruling 2026-08-02): on the
  // X3 the front buttons' top edge sits 11.6 mm below the panel window, 14.8%
  // of the 78.2 mm panel height (measured from Xteink's straight-on product
  // renders; the firmware repo's docs/hardware-dimensions.md holds the full
  // table and methodology). Expressed as a ratio of the PRESENTED panel height
  // so the proportion holds at any device scale; kGap is the pre-first-present
  // fallback only.
  constexpr float kPanelGapRatio = 11.6f / 78.2f;
  // ...and then the WHOLE PAD is lifted this far back off the chassis figure
  // (owner ruling 2026-08-04). A system Picture-in-Picture window parks in a
  // bottom corner, and at the pad's chassis position the top row cleared such a
  // window's top edge by 6.7 pt on an iPhone Air -- close enough to read as a
  // collision. 12 pt takes that to 18.7 pt and, more to the point, takes the
  // width the window can be pinched to before it covers the top row from 50% of
  // the screen to 55%.
  //
  // It comes out of the panel gap and NOTHING ELSE: both rows move up together,
  // the reserved band below (setBottomInset) is unchanged, so the page neither
  // moves nor changes scale -- the pad just sits higher in the space it already
  // had. A flat point value rather than a ratio because what it buys clearance
  // from is a system window sized in points, not a proportion of the panel.
  //
  // The cost is chassis fidelity, and the honest unit for it is millimetres:
  // the Air presents 6.75 pt per real millimetre, so this leaves 66.3 pt =
  // 9.8 mm of the X3's 11.6 mm. Below about 4 mm the pad stops reading as a
  // control surface under the page and starts reading as a border around it;
  // this is well clear of that.
  constexpr float kPipLift = 12.0f;
  constexpr float kRowClear = kGap;     // top row keeps at least this above the bottom row

  // STRICT SQUARE GRID, cell constrained to the optimum (owner ruling
  // 2026-08-02): the cell no longer stretches with device width. The COLUMN
  // COUNT absorbs the width instead -- cols is the integer count whose square
  // lands closest to kOptimalSquare, never fewer than the five the top row
  // needs. Cells touch and run flush margin to margin, so wider devices gain
  // empty middle columns rather than fatter buttons (55.8pt cell / 6 cols on
  // SE and 13 mini, 58.8/6 on 16, 57.1/7 on 16 Pro Max).
  //
  // Rocker/button column assignments count from the grid's ends, so they hold
  // for any cols >= 5: top row Back|Select in columns 0-1 and Left|Right in
  // cols-2..cols-1; bottom row Power in column 0, Up|Down in cols-2..cols-1
  // at half height.
  //
  // The cell sets the band height (below), the band comes out of the panel's
  // space, and the panel scale is floored to an integer
  // (CROSSPOINT_SIM_PIXEL_EXACT). The build is iPhone-only, portrait-only
  // (TARGETED_DEVICE_FAMILY 1, UISupportedInterfaceOrientations = Portrait).
  // If iPad (family 2) is ever enabled, the fix is not a different cell -- it
  // is to put the pad BESIDE the panel in a landscape window, where the spare
  // width is.
  const float usable = W - 2 * kMargin;
  const int cols =
      SDL_max(5, static_cast<int>(SDL_roundf(usable / kOptimalSquare)));
  const float kSquare = usable / static_cast<float>(cols);
  const float kHalf = kSquare / 2.0f;

  // Bottom inset from the system safe area (home indicator), with a fallback
  // when the window is unreadable and a floor so home-button devices (safe
  // area 0) still keep a margin off the screen edge.
  float bottomInset = kHomeInsetFallback;
  if (SDL_Window *win = SDL_GetWindowFromID(g_windowId)) {
    int lw = 0, lh = 0;
    SDL_Rect safe{};
    if (SDL_GetWindowSize(win, &lw, &lh) && lh > 0 &&
        SDL_GetWindowSafeArea(win, &safe))
      bottomInset = static_cast<float>(lh - (safe.y + safe.h));
  }
  bottomInset = SDL_max(bottomInset, kHomeInsetMin);

  // Bottom row: half-height, anchored at the bottom of the screen. maxUpper
  // derives from lowerY, so the top row follows automatically and the two rows
  // keep their spacing.
  //
  // NOT keyboard-aware, unlike the tablet path (owner ruling 2026-08-10: the
  // keyboard OVERLAPS, it does not push). The phone's pad is a band BELOW the
  // page, so lifting it clear of the keyboard would paint controls over the
  // text -- and since the panel no longer shrinks either, there is nowhere for
  // a lifted band to go. While the keyboard is up it covers the page's lower
  // edge and the pad alike; the bar above it puts it away in one tap, and the
  // keyboard chip brings it back.
  const float lowerY = H - bottomInset - kHalf - kPipLift;

  // Top row hugs the panel at the chassis-matched gap less the lift, clamped
  // clear of the bottom row and never over the page.
  //
  // UNCHANGED, deliberately: kThumbRowFromBottom is an iPad-only ruling (owner,
  // 2026-08-09 -- "rockers should only have been moved up on ipad"). The phone
  // keeps the owner-approved 2026-08-02 arrangement, where the top row sits
  // just under the page because that is where a phone is held. A tablet is
  // gripped by its sides, which is why its rockers needed a fixed thumb
  // distance and this does not.
  const float maxUpper = lowerY - kRowClear - kSquare;
  const int panelBottomPx = SimulatorOverlay::panelBottomPx();
  const int panelHeightPx = SimulatorOverlay::panelHeightPx();
  const float panelGap =
      panelHeightPx > 0 ? (static_cast<float>(panelHeightPx) / S) * kPanelGapRatio : kGap;
  float upperY;
  if (panelBottomPx > 0) {
    const float panelBottom = static_cast<float>(panelBottomPx) / S;
    upperY = panelBottom + panelGap - kPipLift;
    if (upperY < panelBottom) upperY = panelBottom;
    if (upperY > maxUpper) upperY = maxUpper;
  } else {
    upperY = maxUpper;
  }

  auto place = [&](int idx, float x, float y, float w, float h) {
    g_pad[idx].rect = {x * S, y * S, w * S, h * S};
  };

  const auto colX = [&](int c) { return kMargin + c * kSquare; };

  // Top row: the two fused front rockers at the grid's ends.
  place(kPadBack, colX(0), upperY, kSquare, kSquare);
  place(kPadConfirm, colX(1), upperY, kSquare, kSquare);
  place(kPadLeft, colX(cols - 2), upperY, kSquare, kSquare);
  place(kPadRight, colX(cols - 1), upperY, kSquare, kSquare);

  // Bottom row: POWER in the first column, the fused side rocker at the end.
  place(kPadPower, colX(0), lowerY, kSquare, kHalf);
  place(kPadUp, colX(cols - 2), lowerY, kSquare, kHalf);
  place(kPadDown, colX(cols - 1), lowerY, kSquare, kHalf);

  // The keyboard chip: ONE cell wide, centred in the bottom row (owner ruling
  // 2026-08-10). Dead centre rather than on the column grid -- with an even
  // column count no cell straddles the middle, and a control that is not one of
  // the seven should not pretend to sit in their grid. The bottom row leaves
  // columns 1..cols-3 empty in every layout (cols is at least 5), so one cell
  // in the middle always clears POWER and the side rocker, and the reserved
  // band below is untouched.
  g_kbChip = {((W - kSquare) / 2.0f) * S, lowerY * S, kSquare * S, kHalf * S};

  // Reserve the pad's band out of the panel's space: the chassis-ratio gap
  // plus both rows and the home inset. The gap term makes this DERIVED from
  // the presented panel height, which the band itself influences -- but the
  // loop converges: the panel scale is floored to an integer, so the band can
  // only move the panel between discrete scales, and one extra relayout after
  // the first present settles it (panelBottom-change already triggers that
  // relayout in paintPad). Before the first present the kGap fallback keeps
  // the band close to its old constant value.
  // The keyboard is NOT added on top (owner ruling 2026-08-10): it overlaps the
  // page rather than shrinking it. Reserving its height here dropped the panel
  // an integer scale -- about 40% of the page on a phone -- to uncover a lower
  // edge not worth that much of the text.
  SimulatorOverlay::setBottomInset(static_cast<int>(
      (panelGap + kSquare + kRowClear + kHalf + bottomInset) * S));

  // Keep the page clear of the status bar and the Dynamic Island. The panel's
  // manual fit is top-aligned, so without a top band it starts at the very top
  // of the screen and the first lines render under the cut-out. Taken from the
  // system rather than a constant like kHomeInset because the top inset is what
  // varies most across devices (Island vs notch vs neither). SDL reports the
  // safe area in window (point) coordinates, hence the * S into device pixels.
  //
  // FLOORED AT kTopReserve (owner ruling 2026-08-04). The safe area is the
  // minimum the system asks for, not a margin: on an iPhone Air it reads 74 pt,
  // which puts the first line of text 5 pt below the Island rather than clear
  // of it. 80 pt is a floor rather than a replacement, so a device whose safe
  // area is deeper still gets its own value.
  //
  // What this does NOT do is clear a floating Picture-in-Picture window parked
  // in a top corner: that wants 159.2 pt (the safe area, the window's own 11 pt
  // inset and a small window's 74.2 pt height), and mockups/pip-envelope.html
  // has the reason it is not taken -- at 159.2 the reserve plus the band below
  // total 382.5 pt of the 384 available before the page halves to 1x, and the
  // pad, which hangs off the page's bottom edge, follows it down into the
  // bottom-corner windows.
  //
  // Cost of the 6 pt: the page's bottom edge moves down with its top, so the
  // top row does too, and the clearance kPipLift bought falls 18.7 -> 12.7 pt
  // at the reference window size. Both bands still fit twice over -- the budget
  // goes from 86.7 pt of headroom to 80.7.
  constexpr float kTopReserve = 80.0f;
  float topInset = 0.0f;
  if (SDL_Window *win = SDL_GetWindowFromID(g_windowId)) {
    SDL_Rect safe{};
    if (SDL_GetWindowSafeArea(win, &safe) && safe.y > 0)
      topInset = static_cast<float>(safe.y);
  }
  topInset = SDL_max(topInset, kTopReserve);
  SimulatorOverlay::setTopInset(static_cast<int>(topInset * S));
}

// --- Appearance ------------------------------------------------------------
//
// HOLLOW CONTROLS. Each control is a one-device-pixel stroke around nothing:
// the face IS the field, so at rest the pad is seven outlines on the same tone
// as the page's paper. A press lays a WASH inside the outline -- the fill
// changes and the stroke never moves.
//
// This reverses what the pad used to do, and the reversal is the point. The old
// arrangement put the face AWAY from the field (lighter than the paper in light
// appearance, darker than the background in dark) and spent the contrast on a
// ring. Two ceilings killed that: the field sits 4 levels below white in light
// and 18 above black in dark, so in light the face had almost nowhere to go and
// in dark the ring had to shout to clear the field. Both tones now step TOWARD
// mid-gray -- darker than the paper, lighter than 121212 -- which is the roomy
// direction in both appearances. One rule where there used to be two mirrored
// ones. (Apple's system ramp is still no help here and is still not used: it
// runs the wrong way in dark, systemGray6 1C1C1E being lighter than
// systemBackground 121212, and it is blue-tinted at every step against this
// app's warm paper.)
//
// THE PRESS IS THE ONLY FEEDBACK, the controls being unlabelled, and it is a
// large-area change rather than a loud one. At the default the wash is 14/255
// against a 34/255 stroke, but it covers a 58.8 pt cell where the stroke covers
// a line, and area is what makes it read.
//
// Every pair that must be told apart is >= 13/255 at the defaults, the floor
// below which a step is not reliably visible on a phone. Verified:
//   light  stroke/field 34, wash/field 14, stroke/wash 20
//   dark   stroke/field 33, wash/field 14, stroke/wash 19
//
// THE TONES BELOW ARE THE DEFAULTS OF A DIAL, not fixed constants. Both of them
// are owner-settable, separately for each appearance, through Settings >
// CrossPoint X3 (Root.plist -> CrossPointPrefs_padOutlineContrast /
// _padFillContrast -> the delta tables below). The scale is signed: 0 puts the
// tone ON the field so the control draws nothing, negative goes darker,
// positive lighter, +/-9 is the end of the gamut. The shipped tones are the
// +/-1 rows, which is why the light defaults are -1 and the dark +1 and why a
// pad left alone is pixel-identical to what shipped before the dial existed.
//
// ACCESSIBLE ONLY IF ASKED, and the number is on the row. WCAG 1.4.11 wants 3:1
// against the adjacent color for the visual information that identifies a
// control, and the exemption it grants a labeled button does not apply to a pad
// that has none. The default strokes measure 1.36:1 in light and 1.48:1 in dark
// -- deliberately, this being a reading surface -- but 3:1 is now a row rather
// than a rebuild: level -4 in light (929290) and +4 in dark (616161) hit it
// exactly, and the ladder runs on past it to 20.3:1 and 18.7:1 at the ends. The
// mitigation this comment used to propose (paint stronger for the first few
// launches, settle after) is unnecessary now that the owner can just turn it up.
struct Palette {
  Uint8 field[3];     // behind the panel and the pad
  Uint8 hairline[3];  // the stroke: control outlines and pair ticks
  Uint8 face[3];      // control interior at rest: EQUAL to the field, i.e. hollow
  Uint8 faceDown[3];  // the wash, laid inside the stroke while held
};

// The field matches the panel's paper tone (HalDisplay's PanelPalette:
// 2D2D2D-on-FBFBF9 light, E0E0DE-on-121212 dark — change them together), so
// the page floats edgeless in the field in both appearances. `face` repeats it
// on purpose: paintPad's existing stroke-then-face draw paints a hollow control
// when the two are equal, so nothing structural is needed to get an outline.
//
// `hairline` and `faceDown` here are the DEFAULT (+/-1) tones. The live palette
// is built by makePalette() from `field` plus a delta out of the tables below;
// the static_asserts pin the two together, so these four lines stay the honest
// documentation of what ships rather than drifting into decoration.
constexpr Palette kLightPalette{{0xFB, 0xFB, 0xF9},
                                {0xD9, 0xD9, 0xD7},
                                {0xFB, 0xFB, 0xF9},
                                {0xED, 0xED, 0xEB}};
constexpr Palette kDarkPalette{{0x12, 0x12, 0x12},
                               {0x33, 0x33, 0x33},
                               {0x12, 0x12, 0x12},
                               {0x20, 0x20, 0x20}};

// --- The contrast ladder ---------------------------------------------------
//
// PRECOMPUTED, NOT DERIVED AT RUNTIME. Each entry is a delta added to every
// channel of the field and clamped; the rungs were chosen for their measured
// sRGB contrast ratio against that field, so the arithmetic that produced them
// is relative-luminance work that has no business running on a phone every
// frame. The ratios each row lands on are the ones Root.plist prints as its row
// labels -- the two must be read together, and neither is a guess.
//
// Indexed by level + kContrastOffset, i.e. -9 first and +9 last.
//
//   light outline  -9 000000 20.3:1 | -8 292927 14:1 | -7 40403E 10:1
//                  -6 565654  7:1   | -5 747472 4.5:1| -4 929290  3:1
//                  -3 B4B4B2  2:1   | -2 C3C3C1 1.7:1| -1 D9D9D7 1.36:1 (default)
//                  +1 DEDEDC 1.3:1  | +2 E3E3E1 1.24:1| +3 E7E7E5 1.2:1
//                  +4 EBEBE9 1.15:1 | +5 EFEFED 1.11:1| +6 F2F2F0 1.08:1
//                  +7 F5F5F3 1.05:1 | +8 F7F7F5 1.04:1| +9 F9F9F7 1.02:1
//   light fill     -9 000000 20.3:1 | -8 40403E 10:1 | -7 565654   7:1
//                  -6 747472 4.5:1  | -5 929290  3:1 | -4 B4B4B2   2:1
//                  -3 CFCFCD 1.5:1  | -2 DEDEDC 1.3:1| -1 EDEDEB 1.13:1 (default)
//   dark outline   +9 FFFFFF 18.7:1 | +8 DFDFDF 14:1 | +7 BEBEBE 10:1
//                  +6 9F9F9F  7:1   | +5 7D7D7D 4.5:1| +4 616161  3:1
//                  +3 474747  2:1   | +2 3D3D3D 1.7:1| +1 333333 1.5:1 (default)
//   dark fill      +9 FFFFFF 18.7:1 | +8 BEBEBE 10:1 | +7 9F9F9F   7:1
//                  +6 7D7D7D 4.5:1  | +5 616161  3:1 | +4 474747   2:1
//                  +3 343434 1.5:1  | +2 2A2A2A 1.3:1| +1 202020 1.15:1 (default)
//
// THE FILL LADDER IS GENTLER at the low end than the outline's -- 1.3 / 1.5 / 2
// where the outline runs 1.7 / 2 / 3 -- because a wash covers a whole cell and
// a stroke covers a line, and equal ratios do not read as equal emphasis.
//
// THE OTHER DIRECTION IS WHERE THE RESOLUTION LIVES NOW. It used to run to each
// appearance's opposite gamut end, which on the light side was a dead zone by
// construction -- the paper is 4 levels off white, so +1..+9 spanned FBFBF9 ->
// FFFFFD, i.e. 1.00:1 to 1.03:1, and several rows were pixel-identical. Nine of
// nineteen rows bought nothing, while the two rows an owner most wants to choose
// between -- the default and invisible -- were ADJACENT INTEGERS with nothing in
// between. Reported exactly that way: "missing all the steps between default and
// invisible".
//
// So the dead rows were spent on that gap instead. Light +1..+9 and dark -1..-8
// now step from just under the default down to just above invisible, which is
// the whole range a reading surface actually cares about.
//
// Dark keeps -9 = BLACK (field 121212 + -18 = 000000). It is only 1.12:1 against
// the field and so reads as a LOW-contrast row, which is why it sits at the end
// of the list rather than the top -- but on an OLED panel it is the one tone
// that vanishes into a true-black page, and it was previously reachable only by
// picking a row labeled "Darker than the field -- 1.12:1", which named a ratio
// and never said black. It says black now.
//
// Root.plist orders its rows most-visible -> invisible (then black, for dark),
// which is display order only: Titles and Values are parallel arrays, so the
// stored integers are unchanged and an existing selection still means what it
// meant. The +/-1 default rows are untouched, which the static_asserts pin.
constexpr int kContrastMin = -9;
constexpr int kContrastMax = 9;
constexpr int kContrastOffset = -kContrastMin;
constexpr int kContrastLevels = kContrastMax - kContrastMin + 1;

constexpr int16_t kOutlineDeltaLight[kContrastLevels] = {
    -251, -210, -187, -165, -135, -105, -71, -56, -34, 0,
    -29,  -24,  -20,  -16,  -12,  -9,   -6,  -4,  -2};
constexpr int16_t kFillDeltaLight[kContrastLevels] = {
    -251, -187, -165, -135, -105, -71, -44, -29, -14, 0,
    -12,  -10,  -8,   -7,   -6,   -5,  -4,  -3,  -2};
constexpr int16_t kOutlineDeltaDark[kContrastLevels] = {
    -18, 2,  5,  8,  11,  15,  19,  23,  28,  0,
    33,  43, 53, 79, 107, 141, 172, 205, 237};
constexpr int16_t kFillDeltaDark[kContrastLevels] = {
    -18, 2,  4,  5,  6,  7,   8,   10,  12,  0,
    14,  24, 34, 53, 79, 107, 141, 172, 237};

constexpr int clampLevel(int level) {
  return level < kContrastMin ? kContrastMin
                              : (level > kContrastMax ? kContrastMax : level);
}

constexpr Uint8 toneChannel(Uint8 field, int16_t delta) {
  return static_cast<Uint8>(field + delta < 0
                                ? 0
                                : (field + delta > 255 ? 255 : field + delta));
}

constexpr bool toneIs(const Uint8 (&field)[3], int16_t delta, Uint8 r, Uint8 g,
                      Uint8 b) {
  return toneChannel(field[0], delta) == r && toneChannel(field[1], delta) == g &&
         toneChannel(field[2], delta) == b;
}

constexpr bool toneMatches(const Uint8 (&field)[3], int16_t delta,
                           const Uint8 (&want)[3]) {
  return toneIs(field, delta, want[0], want[1], want[2]);
}

// THE TABLES CANNOT DRIFT FROM THE PALETTE ABOVE OR FROM THE COMMENT.
// +/-1 must reproduce the shipped tones exactly (this is what makes an untouched
// pad pixel-identical), +/-4 must land on the 3:1 rung the accessibility note
// names, and +/-9 must reach the gamut end.
static_assert(toneMatches(kLightPalette.field,
                          kOutlineDeltaLight[-1 + kContrastOffset],
                          kLightPalette.hairline),
              "light outline level -1 must be the shipped D9D9D7 stroke");
static_assert(toneMatches(kLightPalette.field,
                          kFillDeltaLight[-1 + kContrastOffset],
                          kLightPalette.faceDown),
              "light fill level -1 must be the shipped EDEDEB wash");
static_assert(toneMatches(kDarkPalette.field,
                          kOutlineDeltaDark[1 + kContrastOffset],
                          kDarkPalette.hairline),
              "dark outline level +1 must be the shipped 333333 stroke");
static_assert(toneMatches(kDarkPalette.field, kFillDeltaDark[1 + kContrastOffset],
                          kDarkPalette.faceDown),
              "dark fill level +1 must be the shipped 202020 wash");
static_assert(toneIs(kLightPalette.field,
                     kOutlineDeltaLight[-4 + kContrastOffset], 0x92, 0x92, 0x90),
              "light outline level -4 must be 929290, the 3:1 rung");
static_assert(toneIs(kDarkPalette.field, kOutlineDeltaDark[4 + kContrastOffset],
                     0x61, 0x61, 0x61),
              "dark outline level +4 must be 616161, the 3:1 rung");
static_assert(toneIs(kLightPalette.field,
                     kOutlineDeltaLight[-9 + kContrastOffset], 0, 0, 0) &&
                  toneIs(kLightPalette.field,
                         kFillDeltaLight[-9 + kContrastOffset], 0, 0, 0),
              "light level -9 must reach black");
static_assert(toneIs(kDarkPalette.field, kOutlineDeltaDark[9 + kContrastOffset],
                     0xFF, 0xFF, 0xFF) &&
                  toneIs(kDarkPalette.field, kFillDeltaDark[9 + kContrastOffset],
                         0xFF, 0xFF, 0xFF),
              "dark level +9 must reach white");

// The live palette. `field` and `face` come straight from the appearance's
// constants -- only the stroke and the wash are on a dial.
Palette makePalette(bool dark, int outlineLevel, int fillLevel) {
  const Palette &base = dark ? kDarkPalette : kLightPalette;
  const int16_t *outline = dark ? kOutlineDeltaDark : kOutlineDeltaLight;
  const int16_t *fill = dark ? kFillDeltaDark : kFillDeltaLight;
  const int oi = clampLevel(outlineLevel) + kContrastOffset;
  const int fi = clampLevel(fillLevel) + kContrastOffset;
  Palette p = base;
  for (int c = 0; c < 3; c++) {
    p.face[c] = base.field[c];
    p.hairline[c] = toneChannel(base.field[c], outline[oi]);
    p.faceDown[c] = toneChannel(base.field[c], fill[fi]);
  }
  return p;
}

bool g_dark = false;
Palette g_palette = kLightPalette;
const Palette &palette() { return g_palette; }

// THE FIELD AND THE PANEL BOTH FOLLOW THE APPEARANCE.
//
// In light mode the field is white because a blank e-ink page is white, so the
// panel edge disappears. In dark mode the field goes to systemBackground dark
// and the panel renders white-on-black: this app is a reading surface first
// and a simulator second, and a full-brightness white page inside a dark UI is
// exactly what dark appearance exists to prevent.
//
// The inversion is a HOST presentation choice layered on the device's output,
// not a device behavior -- a fact worth keeping straight, both halves checked
// rather than assumed: no X3 can invert its panel, and nothing in the firmware
// or the SDK calls setInverted/toggleInverted/isInverted; the trio exists only
// in the simulator's HalDisplay, which applies the flip while converting the
// 1bpp framebuffer to pixels. The device layer keeps drawing black-on-white
// and cannot tell the difference, so no firmware path changes underneath us.
//
// Immediacy lives inside HalDisplay, not here. Conversion runs on the render
// task only when the firmware refreshes, so flipping the flag alone would not
// show until the next page render -- which on e-ink may be never. setInverted
// therefore posts an atomic reconvert request that presentIfNeeded (main
// thread) services from HalDisplay's cached last frame, so the new polarity
// lands on the very next present. SimulatorOverlay::setPanelDark is the single
// entry point; it also honors the CROSSPOINT_SIM_DARK override, which is what
// lets the headless desktop tests drive the exact mechanics this path uses.
//
// Known cost, accepted for now: inversion is polarity-blind, so book covers
// and other images render as negatives in dark mode.
// The live appearance. UIKit first, SDL only as a fallback -- SDL's theme is a
// cache refreshed from a deprecated callback that an SDL app does not reliably
// receive, so it is stale exactly when it matters. See CrossPointAppearance.h.
bool systemIsDark() {
  const int uikit = CrossPointAppearance_isDark();
  if (uikit >= 0) return uikit != 0;
  return SDL_GetSystemTheme() == SDL_SYSTEM_THEME_DARK;
}

// What applyTheme last published. -1 = nothing yet, so the first call always
// applies. Read by pollAppearance to stay edge-triggered; kept here rather than
// as a local static in the poll so that applyTheme's other callers (startup and
// the SDL theme watch) also satisfy the edge and cannot cause a double apply.
int g_appliedDark = -1;

// What makePalette was last called with. Out of range on purpose so the first
// pollPadContrast after a theme change cannot mistake a stale level for a match;
// applyTheme writes them itself, so in practice the poll is already satisfied.
int g_appliedOutline = kContrastMin - 1;
int g_appliedFill = kContrastMin - 1;

void applyTheme() {
  g_dark = systemIsDark();
  g_appliedDark = g_dark ? 1 : 0;
  // The levels are per-appearance, so a light->dark flip changes which pair is
  // in force. Read them here rather than leaving it to the next poll: the
  // palette this call publishes has to be the finished one.
  g_appliedOutline = CrossPointPrefs_padOutlineContrast(g_appliedDark);
  g_appliedFill = CrossPointPrefs_padFillContrast(g_appliedDark);
  g_palette = makePalette(g_dark, g_appliedOutline, g_appliedFill);
  const Palette &p = palette();
  SimulatorOverlay::setClearColor(p.field[0], p.field[1], p.field[2]);
  SimulatorOverlay::setPanelDark(g_dark);
  // The firmware presents only when it has new panel content, which on an e-ink
  // device is rare, so without this the new appearance would not appear until
  // the next page render. (setPanelDark's reconvert also raises a present, but
  // only when the polarity actually changed; the field color must repaint
  // regardless.)
  SimulatorOverlay::requestPresent();
}

// When the app last returned to the foreground, on the SDL_GetTicks clock, or 0
// once the settle window below has elapsed. See presentationWatch.
Uint64 g_foregroundAt = 0;

// A watch of its own, deliberately not a case inside padWatch: everything here
// is a painting concern and none of it reads input. Both cases only write a
// flag and a handful of atomics -- no renderer call happens on this thread; the
// reconvert and the repaint run later on the main thread inside
// presentIfNeeded.
bool SDLCALL presentationWatch(void * /*userdata*/, SDL_Event *e) {
  switch (e->type) {
  case SDL_EVENT_SYSTEM_THEME_CHANGED:
    // SDL raises this from UIKit's traitCollectionDidChange. Kept because it
    // costs nothing and is the correct mechanism, but it is not load-bearing
    // any more -- pollAppearance below reads UIKit directly every frame.
    applyTheme();
    break;
  case SDL_EVENT_DID_ENTER_FOREGROUND:
    HalDisplay::setBackgrounded(false);
    g_foregroundAt = SDL_GetTicks();
    SimulatorOverlay::requestPresent();
    break;
  default:
    break;
  }
  return true;  // never filter anything out
}

// BELT AND BRACES for the theme case of the watch above.
//
// SDL raises SDL_EVENT_SYSTEM_THEME_CHANGED from UIKit's traitCollectionDidChange
// on its own view controller, which is deprecated as of iOS 17 (Apple's
// replacement is registerForTraitChanges:withHandler:) and which UIKit only
// delivers as part of a view update pass -- something an SDL app, drawing
// straight through Metal, has no reason to run.
//
// HONEST ABOUT WHAT WAS MEASURED, because the comment is worth more than the
// theory: on iOS 26.5 that callback still fires, and SDL's cached theme was
// never once observed disagreeing with UIKit (sampled at 1 Hz across repeated
// flips, including flips made while backgrounded). So this poll is not
// correcting a wrong answer today -- it is removing the dependency on a
// deprecated callback, and it applies the change within one frame of the app
// resuming rather than up to a second later, which is when SDL's event arrived.
// The watch stays installed for the same reason in reverse: it costs nothing and
// it is the right mechanism if SDL ever adopts registerForTraitChanges.
//
// EDGE-TRIGGERED, and it has to be. applyTheme writes atomics and calls
// requestPresent(); running it every frame would force a present every frame on
// a panel whose whole presentation model assumes it presents rarely. The steady
// state here is one UIKit read and an integer compare.
//
// Main thread only -- it is called from main()'s loop alongside presentIfNeeded()
// for the same reason that one is. It reads no SDL events, so HalGPIO keeps sole
// ownership of the pump, and it holds no timer, so nothing here can drift into
// PadCore's clock-free territory.
void pollAppearance() {
  const int want = systemIsDark() ? 1 : 0;
  if (want == g_appliedDark) return;
  applyTheme();
  SDL_Log("[harness] appearance -> %s", g_dark ? "dark" : "light");
}

// The pad's two tones, on the same terms as pollAppearance above and for the
// same reasons.
//
// SETTINGS.APP IS A SEPARATE APP, so a change to these arrives while CrossPoint
// is backgrounded and there is no event to hang it on -- iOS posts
// NSUserDefaultsDidChangeNotification only for changes this process made.
// Reading the level here costs a dictionary lookup in an in-memory store, and
// the repaint is EDGE-TRIGGERED on the applied level: without that this would
// force a present every frame on a panel whose presentation model assumes it
// presents rarely.
//
// Main thread only, pumps no SDL events, holds no timer -- the same three
// constraints pollAppearance lives under.
void pollPadContrast() {
  const int dark = g_dark ? 1 : 0;
  const int outline = CrossPointPrefs_padOutlineContrast(dark);
  const int fill = CrossPointPrefs_padFillContrast(dark);
  if (outline == g_appliedOutline && fill == g_appliedFill) return;
  g_appliedOutline = outline;
  g_appliedFill = fill;
  g_palette = makePalette(g_dark, outline, fill);
  SimulatorOverlay::requestPresent();
  SDL_Log("[harness] pad contrast (%s) -> outline %+d, fill %+d",
          g_dark ? "dark" : "light", outline, fill);
}

// THE FIRST FRAMES AFTER A FOREGROUND RETURN ARE THROWN AWAY, so keep asking.
//
// This is the half of the stale-appearance bug that detection alone does not
// fix, and it is not appearance-specific: iOS suspends the process while the app
// is backgrounded and shows a snapshot of the last frame during the return
// transition, and a frame presented into that transition never reaches the
// glass. Measured on iOS 26.5, with the presentation path instrumented:
// SDL_RenderPresent returns success (driver=metal) at resume+65 ms and the
// screen keeps the pre-background image; the same present a second or so later
// lands. An app that redraws continuously never notices, because its next frame
// is a sixtieth of a second away. This one presents ONLY when the panel changes,
// so the discarded frame is the only frame there will be, and the stale image
// stands until the user touches a control -- which is exactly the reported
// symptom.
//
// So: after SDL_EVENT_DID_ENTER_FOREGROUND, re-ask for a present on a slow
// cadence until the window has settled. Each one re-uploads a cached frame on an
// otherwise idle screen; a dozen of them, once per foreground return, is not a
// cost worth optimising. The window is bounded and clears itself.
//
// The constants are measured, not guessed: repaints at 200 ms intervals were
// logged against timed screenshots, the screen had caught up by the +1 s
// screenshot, and 2 s leaves margin for hardware slower than the Simulator.
// Do not tighten these to the measured minimum -- the failure mode is silent and
// only visible to the user.
constexpr Uint64 kForegroundSettleMs = 2000;
constexpr Uint64 kForegroundRepaintMs = 200;

void repaintAfterForeground() {
  if (g_foregroundAt == 0) return;  // steady state: one load and a compare
  const Uint64 now = SDL_GetTicks();
  if (now - g_foregroundAt > kForegroundSettleMs) {
    g_foregroundAt = 0;
    return;
  }
  static Uint64 lastRepaint = 0;
  if (now - lastRepaint < kForegroundRepaintMs) return;
  lastRepaint = now;
  SimulatorOverlay::requestPresent();
}

// --- Painting --------------------------------------------------------------

void setRGB(SDL_Renderer *r, const Uint8 c[3]) {
  SDL_SetRenderDrawColor(r, c[0], c[1], c[2], 255);
}

void fillRect(SDL_Renderer *r, float x, float y, float w, float h) {
  const SDL_FRect rect{x, y, w, h};
  SDL_RenderFillRect(r, &rect);
}

void fillRoundRect(SDL_Renderer *r, const SDL_FRect &b, float rad) {
  const int h = static_cast<int>(b.h);
  for (int i = 0; i < h; i++) {
    const float y = static_cast<float>(i);
    float inset = 0.0f;
    if (y < rad) {
      const float d = rad - y;
      inset = rad - SDL_sqrtf(SDL_max(0.0f, rad * rad - d * d));
    } else if (y > b.h - rad) {
      const float d = y - (b.h - rad);
      inset = rad - SDL_sqrtf(SDL_max(0.0f, rad * rad - d * d));
    }
    fillRect(r, b.x + inset, b.y + y, b.w - 2 * inset, 1);
  }
}

// The software keyboard's toggle.
//
// Drawn ONLY while the firmware has a text field open (owner ruling
// 2026-08-10) -- in every other state this paints nothing, so the pad the owner
// approved is untouched whenever the feature is not in play. It has to be a
// toggle rather than only a way back, because the dismiss bar rides on the
// keyboard and leaves with it, so a control that could only raise would be
// half a switch.
//
// WORDLESS, like every control beside it. The pad names nothing, and a label
// here would be the only text on screen outside the page. The chevron points
// the way the keyboard is about to move -- up to summon it, down to dismiss --
// which is the same convention as iOS's own dismiss key.
void paintKeyboardChip(SDL_Renderer *r, const Palette &p, float radius,
                       float hairline) {
  if (!gpio.isTextEntryActive()) return;
  const SDL_FRect &c = g_kbChip;
  if (c.w <= 0 || c.h <= 0) return;
  const bool keyboardUp = gpio.isHostKeyboardVisible();

  // Same stroke-then-face construction as the controls, so it belongs to the
  // pad rather than sitting on top of it.
  setRGB(r, p.hairline);
  fillRoundRect(r, c, radius);
  setRGB(r, p.face);
  fillRoundRect(r, {c.x + hairline, c.y + hairline, c.w - 2 * hairline,
                    c.h - 2 * hairline},
                radius - hairline);

  const float glyphH = c.h * 0.52f;
  const float chevH = glyphH * 0.26f;
  const float bodyH = glyphH * 0.56f;
  const float bodyW = bodyH * 1.75f;
  const float cx = c.x + c.w / 2.0f;
  const float top = c.y + (c.h - glyphH) / 2.0f;

  // The chevron as stacked one-pixel rows: no geometry API, and it stays crisp
  // at any density instead of being resampled from a rotated rect.
  setRGB(r, p.hairline);
  const float arm = SDL_max(1.0f, SDL_roundf(chevH * 0.42f));
  for (float i = 0; i < chevH; i += 1.0f) {
    // Points where the keyboard is about to go. Converged at the top spreading
    // down is "^" (summon); the mirror is "v" (dismiss), which is the glyph iOS
    // puts on its own dismiss key.
    const float off = keyboardUp ? chevH - i : i;
    fillRect(r, cx - off - arm / 2, top + i, arm, 1);
    fillRect(r, cx + off - arm / 2, top + i, arm, 1);
  }

  // The keyboard: a solid body with the keys PUNCHED back out in the face
  // tone. Punching rather than stroking each key is what keeps it legible at
  // this size -- outlines this small close up into a grey smear.
  const float bx = cx - bodyW / 2.0f;
  const float by = top + glyphH - bodyH;
  setRGB(r, p.hairline);
  fillRoundRect(r, {bx, by, bodyW, bodyH}, bodyH * 0.2f);

  setRGB(r, p.face);
  const float gap = SDL_max(1.0f, SDL_roundf(bodyH * 0.13f));
  const float innerW = bodyW - gap * 2;
  const float keyH = (bodyH - gap * 4) / 3.0f;
  const float keyW = (innerW - gap * 3) / 4.0f;
  for (int row = 0; row < 2; row++)
    for (int col = 0; col < 4; col++)
      fillRect(r, bx + gap + col * (keyW + gap), by + gap + row * (keyH + gap),
               keyW, keyH);
  // The space bar, inset a key's width either side so the bottom row reads as
  // a keyboard and not as a third row of squares.
  fillRect(r, bx + gap + keyW * 0.5f, by + gap + 2 * (keyH + gap),
           innerW - keyW, keyH);
}

void paintPad(SDL_Renderer *r, int outW, int outH) {
  // SimulatorOverlay holds a single draw callback, so the pad's painter is
  // also the dispatch point for the read-aloud word highlight. First, so the
  // pad never paints under it (their areas are disjoint anyway: highlight on
  // the panel, pad in the reserved band).
  CrossPointReadAloud_paintHighlight(r, outW, outH, g_dark ? 1 : 0);

  // Relayout when the panel's published bottom edge moves (first present,
  // orientation change) as well as on size changes.
  static int s_layoutPanelBottom = -1;
  static int s_layoutKeyboardPt = -1;
  const int panelBottom = SimulatorOverlay::panelBottomPx();
  const int keyboardPt = static_cast<int>(g_keyboardHeightPt);
  if (!g_padLaidOut || panelBottom != s_layoutPanelBottom ||
      keyboardPt != s_layoutKeyboardPt) {
    layoutPad(outW, outH);
    g_padLaidOut = true;
    s_layoutPanelBottom = panelBottom;
    s_layoutKeyboardPt = keyboardPt;
  }
  const Palette &p = palette();
  const float S = g_ptScale;
  const float radius = 12.0f * S;

  // ONE DEVICE PIXEL, not half a point. `S * 0.5f` is 1.5 px on a 3x phone,
  // which cannot land on the pixel grid: the stroke is antialiased across two
  // rows and arrives lighter and softer than the palette above says, so the
  // constant stops describing what is on the glass. A whole pixel is exact at
  // every scale, and it is the rule UIKit itself uses for separators.
  const float hairline = 1.0f;

  // A stroke with the face inset inside it. The stroke stays put while held, so
  // the face changing tone reads as the control filling rather than as the
  // control being redrawn. Pressed paint comes straight from PadCore's finger
  // state -- the moment no finger holds a control, it paints released.

  // Fill one half of a rocker: rounded on the outer end, SQUARE on the shared
  // edge -- a rounded fill then a square patch over the inner end's corners.
  auto fillHalf = [&](const SDL_FRect &half, bool leftHalf, float rad) {
    fillRoundRect(r, half, rad);
    const SDL_FRect patch{leftHalf ? half.x + half.w - rad : half.x, half.y,
                          rad, half.h};
    SDL_RenderFillRect(r, &patch);
  };

  // The three fused pairs paint as ONE capsule each -- a single hairline
  // ring around the union with only the outer corners rounded (no pinched
  // notch where two rounded squares would meet), a hairline divider marking
  // the two targets, and the pressed half shading independently. Up|Down is
  // half-height; the same union/divider math holds because a pair shares y/h.
  const int pairs[3][2] = {
      {kPadBack, kPadConfirm}, {kPadLeft, kPadRight}, {kPadUp, kPadDown}};
  bool inPair[kPadCount] = {};
  for (const auto &pr : pairs) {
    const SDL_FRect &a = g_pad[pr[0]].rect;
    const SDL_FRect &b = g_pad[pr[1]].rect;
    inPair[pr[0]] = inPair[pr[1]] = true;

    const SDL_FRect uni{a.x, a.y, (b.x + b.w) - a.x, a.h};
    setRGB(r, p.hairline);
    fillRoundRect(r, uni, radius);

    // The two halves MEET at the seam, with no stroke left showing between
    // them. They used to stop a half-hairline short on that edge, so the
    // capsule underneath painted a full-height divider whether one was wanted
    // or not -- which is why simply shortening the divider rect below did
    // nothing. The tick is now the only thing marking the seam.
    const float innerR = radius - hairline;
    const SDL_FRect innerL{a.x + hairline, a.y + hairline, a.w - hairline,
                           a.h - 2 * hairline};
    const SDL_FRect innerRt{b.x, b.y + hairline, b.w - hairline,
                            b.h - 2 * hairline};
    setRGB(r, g_core.isDown(pr[0]) ? p.faceDown : p.face);
    fillHalf(innerL, /*leftHalf=*/true, innerR);
    setRGB(r, g_core.isDown(pr[1]) ? p.faceDown : p.face);
    fillHalf(innerRt, /*leftHalf=*/false, innerR);

    // Divider between the two targets, same tone as the stroke -- a CENTRE TICK
    // over 34% of the pair's inner height, not the full span. The seam only has
    // to say "two targets here"; a full-height rule doubles the ink in the
    // middle of the pad, which is exactly where the eye already is.
    setRGB(r, p.hairline);
    const float innerH = a.h - 2 * hairline;
    const float tickH = innerH * 0.34f;
    const SDL_FRect div{b.x - hairline / 2, a.y + hairline + (innerH - tickH) / 2,
                        hairline, tickH};
    SDL_RenderFillRect(r, &div);
  }

  for (int i = 0; i < kPadCount; i++) {
    if (inPair[i]) continue;
    const PadButton &b = g_pad[i];
    setRGB(r, p.hairline);
    fillRoundRect(r, b.rect, radius);

    const SDL_FRect inner{b.rect.x + hairline, b.rect.y + hairline,
                          b.rect.w - 2 * hairline, b.rect.h - 2 * hairline};
    setRGB(r, g_core.isDown(i) ? p.faceDown : p.face);
    fillRoundRect(r, inner, radius - hairline);
  }

  paintKeyboardChip(r, p, radius, hairline);
}

// The chip is not in g_pad -- it presses no hardware button -- so it needs its
// own test. Live only while a field is open, which is the only time it is drawn.
bool hitKeyboardChip(float x, float y) {
  if (!gpio.isTextEntryActive()) return false;
  const SDL_FRect &c = g_kbChip;
  return c.w > 0 && c.h > 0 && x >= c.x && x < c.x + c.w && y >= c.y &&
         y < c.y + c.h;
}

int padHitTest(float x, float y) {
  for (int i = 0; i < kPadCount; i++) {
    const SDL_FRect &r = g_pad[i].rect;
    if (x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h) return i;
  }
  return -1;
}

// Read-aloud tap candidate: a finger that landed on NO pad slot may become a
// word tap. Down records it, dragging past the slop cancels it (a drag must
// not start speech), a clean lift hands the DOWN coordinates to the adapter
// (CrossPointReadAloud_tapAtScreen rejects anything outside the panel or off
// a word). Cancelled by the same events that reset the pad. No timers: a tap
// is down + up without movement, however long the hold — the pad's own
// design, and PadCore itself stays untouched.
long long g_tapFingerId = -1;
float g_tapDownX = 0.0f, g_tapDownY = 0.0f;

// Finger coordinates arrive normalized; the pad needs pixels, and the harness
// does not own the renderer, so it asks the window the event came from.
bool windowPixelSize(SDL_WindowID id, float *w, float *h) {
  SDL_Window *win = SDL_GetWindowFromID(id ? id : g_windowId);
  if (!win) return false;
  int pw = 0, ph = 0;
  if (!SDL_GetWindowSizeInPixels(win, &pw, &ph) || pw <= 0 || ph <= 0)
    return false;
  *w = static_cast<float>(pw);
  *h = static_cast<float>(ph);
  return true;
}

bool SDLCALL padWatch(void * /*userdata*/, SDL_Event *e) {
  float outW = 0, outH = 0;

  switch (e->type) {
    case SDL_EVENT_FINGER_DOWN: {
      if (!windowPixelSize(e->tfinger.windowID, &outW, &outH)) break;
      const float fx = e->tfinger.x * outW, fy = e->tfinger.y * outH;

      const int hit = padHitTest(fx, fy);
      if (hit >= 0) g_windowId = e->tfinger.windowID;
      if (hit < 0 && g_tapFingerId == -1) {
        g_tapFingerId = e->tfinger.fingerID;
        g_tapDownX = fx;
        g_tapDownY = fy;
      }
      applyActions(g_core.fingerDown(hit >= 0 ? hit : PadCore::kNoSlot,
                                     e->tfinger.fingerID));
      break;
    }

    case SDL_EVENT_FINGER_MOTION: {
      // A tap candidate that drags past the slop is a swipe, not a tap.
      if (e->tfinger.fingerID == g_tapFingerId &&
          windowPixelSize(e->tfinger.windowID, &outW, &outH)) {
        const float x = e->tfinger.x * outW, y = e->tfinger.y * outH;
        const float slop = 12.0f * g_ptScale;
        if (SDL_fabsf(x - g_tapDownX) > slop ||
            SDL_fabsf(y - g_tapDownY) > slop)
          g_tapFingerId = -1;
      }
      // Dragging off a control cancels it, matching how a system button behaves
      // and how a real key behaves when your thumb slides off it.
      const int slot = g_core.heldSlot(e->tfinger.fingerID);
      if (slot == PadCore::kNoSlot) break;
      if (!windowPixelSize(e->tfinger.windowID, &outW, &outH)) break;
      const float x = e->tfinger.x * outW;
      const float y = e->tfinger.y * outH;
      const SDL_FRect &r = g_pad[slot].rect;
      if (x < r.x || x >= r.x + r.w || y < r.y || y >= r.y + r.h)
        applyActions(g_core.fingerLeftSlot(e->tfinger.fingerID));
      break;
    }

    // CANCELED alongside UP: iOS cancels touches for its own gestures (home
    // indicator swipe, Control Center pull, an incoming call). Without this the
    // slot stays latched down forever, and PadCore ignores every later press on
    // it — a second, permanent way for POWER to stop working until force quit.
    case SDL_EVENT_FINGER_UP:
    case SDL_EVENT_FINGER_CANCELED:
      if (e->tfinger.fingerID == g_tapFingerId) {
        g_tapFingerId = -1;
        // A CANCELED finger (Control Center pull, incoming call) is not a tap.
        if (e->type == SDL_EVENT_FINGER_UP) {
          // ONLY THE CHIP TOGGLES THE KEYBOARD. A tap anywhere else does not,
          // however empty that part of the screen looks (owner bug report
          // 2026-08-11: "ios keyboard is popping up when I tap on negative
          // empty space, it needs to only pop up when show keyboard is
          // tapped").
          //
          // It used to raise on any off-pad tap, on the theory that a bigger
          // target is kinder. It is not: the margins around the panel and the
          // band around the pad are most of the screen, so putting the phone
          // down, adjusting a grip, or resting a thumb threw the keyboard back
          // up over the page. A control that fires when you touch nothing in
          // particular is not a control.
          if (hitKeyboardChip(g_tapDownX, g_tapDownY)) {
            gpio.setHostKeyboardVisible(!gpio.isHostKeyboardVisible());
            SimulatorOverlay::requestPresent();
          } else
            CrossPointReadAloud_tapAtScreen(g_tapDownX, g_tapDownY);
        }
      }
      applyActions(g_core.fingerUp(e->tfinger.fingerID));
      break;

    // The software keyboard's REAL state, from UIKit by way of SDL. SHOWN is
    // where the dismiss bar gets attached: SDL raises it from inside
    // -startTextInput, before becomeFirstResponder, which is the cheapest
    // moment to hand the field an accessory view.
    case SDL_EVENT_SCREEN_KEYBOARD_SHOWN:
      CrossPointKeyboardBar_install();
      SimulatorOverlay::requestPresent(); // the chip has to go away
      break;

    // HIDDEN is how a dismissal we did NOT initiate gets noticed -- iPad's own
    // dismiss key, or a hardware keyboard connecting. Without it the harness
    // would go on believing the keyboard is up: no chip, and no way back.
    //
    // Gated on a field being open, because the hide that follows a field
    // closing is our own and means nothing. By then the firmware's flag is
    // already false (setTextEntryActive runs before pumpHostTextInput issues
    // the stop), so that case lands here as a no-op.
    case SDL_EVENT_SCREEN_KEYBOARD_HIDDEN:
      if (gpio.isTextEntryActive()) gpio.setHostKeyboardVisible(false);
      SimulatorOverlay::requestPresent(); // ...and here it has to appear
      break;

    // Backgrounding must not leave a key stuck down: the finger is gone, and a
    // stuck POWER would read as a long press.
    case SDL_EVENT_WILL_ENTER_BACKGROUND:
      // Read-aloud keeps the process alive with the screen locked, and it
      // turns pages while it reads -- so the firmware goes on rendering. Stop
      // presenting: Metal work submitted from the background is grounds for
      // termination.
      HalDisplay::setBackgrounded(true);
      [[fallthrough]];
    case SDL_EVENT_WINDOW_FOCUS_LOST:
      g_tapFingerId = -1;
      applyActions(g_core.reset());
      break;

    // The pad is laid out from the output size, so a size change invalidates it.
    case SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED: {
      g_padLaidOut = false;
      SimulatorOverlay::requestPresent();
      break;
    }

    default:
      break;
  }
  return true;  // never filter anything out
}

}  // namespace

// --- Public entry points ---------------------------------------------------
//
// CrossPointHarness_prepareFilesystem lives in CrossPointFsPrep.cpp: it is
// plain POSIX and is compiled and exercised on a desktop host, which the
// SDL-facing code in this file cannot be.

void CrossPointHarness_begin() {
  // IDEMPOTENT ACROSS WAKES. On iOS a deep-sleep wake longjmps back through
  // setup() (SimulatorLifecycle, CROSSPOINT_SIM_REBOOT_IN_PROCESS), which
  // calls this again. Event watches must be registered exactly once: each
  // SDL_AddEventWatch call stacks another live callback, so N wakes would run
  // every finger event through N watches. State refreshes (theme, layout,
  // released buttons) re-run every call; registrations do not.
  static bool s_watchesInstalled = false;

  // THIS FILE IS IN THE APP TARGET; the firmware and the HAL are in
  // crosspoint_core. A cross-cutting define set on only one of the two builds
  // a binary whose halves disagree, compiles clean, and shows up as a bug in
  // something distant (CROSSPOINT_RENDER_SCALE: 15 builds of 1x glyphs;
  // SIMULATOR_DEVICE_X3: every calendar sleep screen falling back to the stock
  // logo). Compare and die here rather than ship that again. Cheap, and the
  // matching line is a useful thing to have in a log. See
  // src/SimulatorBuildIdentity.h.
  static bool s_identityChecked = false;
  if (!s_identityChecked) {
    verifyBuildIdentityMatchesCore(localBuildIdentity(), "iOS harness");
    s_identityChecked = true;
  }

  // Touches must arrive as finger events only. Left on, SDL also synthesises
  // mouse events from the same touch, and HalGPIO consumes mouse events.
  SDL_SetHint(SDL_HINT_TOUCH_MOUSE_EVENTS, "0");
  SDL_SetHint(SDL_HINT_MOUSE_TOUCH_EVENTS, "0");

  // NOT set, and it must stay that way: SDL_HINT_RETURN_KEY_HIDES_IME makes
  // Return call SDL_StopTextInput (SDL_uikitviewcontroller.m:664-667). Return
  // types a line break in a multi-line field -- owner ruling, and the whole
  // point of src/TextEntryKeyRouting.h -- so a hint that dismissed the keyboard
  // on every newline would undo it. Dismissing is the accessory bar's job.

  // Points-to-pixels, so HIG dimensions stay honest on any device scale.
  int count = 0;
  SDL_Window **windows = SDL_GetWindows(&count);
  if (windows && count > 0) {
    g_windowId = SDL_GetWindowID(windows[0]);
    int pw = 0, ph = 0, lw = 0, lh = 0;
    SDL_GetWindowSizeInPixels(windows[0], &pw, &ph);
    SDL_GetWindowSize(windows[0], &lw, &lh);
    if (lw > 0 && pw > 0) g_ptScale = static_cast<float>(pw) / lw;
    SDL_Log("[harness] window %dx%d pt, %dx%d px, scale %.2f", lw, lh, pw, ph,
            g_ptScale);
  }
  if (windows) SDL_free(windows);

  SimulatorOverlay::setDrawCallback(paintPad);

  // A wake begins with no fingers on glass; drop any state a pre-sleep touch
  // left behind, and relayout against the (possibly rotated) window.
  applyActions(g_core.reset());
  g_padLaidOut = false;

  // Appearance. SDL_Init has already run (HalDisplay::begin calls it), so the
  // theme is populated and can be read straight away; the watch keeps it current
  // if the user flips the system between light and dark while the app is up.
  applyTheme();
  SDL_Log("[harness] appearance: %s, pad contrast outline %+d fill %+d",
          g_dark ? "dark" : "light", g_appliedOutline, g_appliedFill);

  // Same idempotence contract as this function: creates once, refreshes the
  // pref edge on every wake.
  CrossPointReadAloud_begin();
  // Same idempotent-across-wakes contract; installs the accessibility
  // container over the SDL view.
  CrossPointAccessibility_begin();

  SimulatorOverlay::requestPresent();

  if (!s_watchesInstalled) {
    if (!SDL_AddEventWatch(presentationWatch, nullptr))
      SDL_Log("[harness] presentation watch failed: %s", SDL_GetError());
    if (!SDL_AddEventWatch(padWatch, nullptr))
      SDL_Log("[harness] SDL_AddEventWatch failed: %s", SDL_GetError());
    else
      SDL_Log("[harness] button pad installed");
    s_watchesInstalled = true;
  }
}

void CrossPointHarness_perFrame() {
  pollAppearance();
  pollPadContrast();
  repaintAfterForeground();
  CrossPointReadAloud_perFrame();
}
