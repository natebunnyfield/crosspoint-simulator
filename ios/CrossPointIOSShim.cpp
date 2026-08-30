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
#include "GestureBindings.h"
#include "TapCandidate.h"
#include "ZenPrefSync.h"
#include "ZenVerbs.h"

#include <SDL3/SDL.h>

#include <cstdint>
#include <limits>

#include "CrossPointAppearance.h"
#include "AppearanceSeed.h"
#include "CrossPointPrefs.h"
#include "CrossPointAccessibility.h"
#include "ChevronCoverage.h"
#include "CrossPointKeyboardBar.h"
#include "PanelPrefs.h"
#include "PhosphorGrain.h"
#include "LightInkPalette.h"  // kPaperStrengthDefault, for the APPLY_INK script
// The firmware owns the Dark Mode SETTING; the system owns the APPEARANCE.
// applyTheme() below is where the two are reconciled.
#include "CrossPointSettings.h"
#include "CrossPointReadAloud.h"

// Ask the firmware to RE-RENDER the current activity. Declared rather than
// included: ActivityManager.h holds unique_ptr<Activity> and would drag the
// whole activity header set into the harness for one call. Defined in
// src/SimulatorRenderRequest.cpp on the firmware side.
void crosspointRequestRender();
// The page-color mixer (CrossPointPaletteMixer.mm). present() opens the modal;
// glowForCustom() is the Custom slot's mix-aware glow branch.
extern "C" void CrossPointMixer_present(void);
// True while the mixer sheet is on screen. The sheet is a pageSheet with an
// undimmed medium detent, so UIKit passes every touch OUTSIDE the sheet
// through to the SDL view underneath (2026-08-21 audit, finding #6): without
// this gate, page taps kept reaching the pad, the tap candidate and the zen
// paths while the tray was up.
extern "C" bool CrossPointMixer_isPresented(void);
// The LIGHT-appearance page-color picker (CrossPointLightInkPicker.mm):
// historical inks at variable density on proven papers. The chip branches on
// the live appearance -- light opens this, dark opens the gun mixer
// (docs/light-ink-picker.md). Same sheet discipline, same presented-flag
// contract, so every gate below checks both.
extern "C" void CrossPointInkPicker_present(void);
// The named-preset list both editors push (CrossPointPresetList.mm). Only its
// headless hook is needed here; the UI entry points are the drawers' own.
extern "C" void CrossPointPresetList_selectForTest(int preset);
extern "C" bool CrossPointInkPicker_isPresented(void);
extern "C" void CrossPointInkPicker_applyForTest(int ink, int paper,
                                                 int density,
                                                 int paperStrength);
// The sheet's roughness for the STORED paper selection, seeded at launch by
// pollPaperTooth below -- the picker may never be opened and the paper still
// has a texture.
extern "C" int CrossPointInkPicker_paperToothPercent(void);
// ...and the rest of the paper instrument, same argument one step further: the
// drawer may never be opened, and Settings.app can move the Defects row without
// the drawer ever coming up. The signature is a cheap change detector so the
// poll stays edge-triggered.
extern "C" void CrossPointInkPicker_pushPaperDials(void);
extern "C" uint32_t CrossPointInkPicker_paperDialSignature(void);
// Zen's motion gestures are native UIKit recognizers now
// (CrossPointZenRecognizers.mm); enabled only while zen is on.
extern "C" void CrossPointZenRecognizers_setEnabled(bool on);
// Defined at the foot of this file; declared here because the SDL finger path
// above it can now reach the zen toggle too -- a deliberate tap may be bound to
// it (T-025).
extern "C" void CrossPointZen_toggleFromRecognizer(const char *source);
extern "C" void CrossPointMixer_applyGunsForTest(int r, int g, int b, int w);
extern "C" bool CrossPointMixer_glowForCustom(float *trailMs,
                                              unsigned char tail[3],
                                              bool *hasTail,
                                              float *tailOnsetMs);

#include "HalDisplay.h"
#include "HalGPIO.h"
#include "PadCore.h"
#include "PadPalette.h"
#include "PanelPalette.h"
#include "SimHostScreen.h"
#include "SimulatorBuildIdentity.h"
#include "SimulatorOverlay.h"

namespace {

// Forward declaration: defined below (near windowPixelSize, which it calls).
// Used by pollZenMode() and pollReaderInsets(), both defined earlier in this
// file than the definition that needs windowPixelSize in scope.
void zenPreWarmLayout();

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
// SIZING: all controls are on the 8 pt square grid. Heights are kSquare
// rounded to the nearest 8 pt multiple (kCellH), so they range from 48-64 pt
// across devices -- comfortably over the HIG 44 pt minimum. Bands stay inset
// clear of the Dynamic Island at the top and the home indicator at the bottom.
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

// THE PAGE-COLOR BUTTON IS GONE, 2026-08-24. Owner ruling: "remove the color
// button from single finger (not zen) mode ui."
//
// It sat beside POWER on the phone and in the tablet pad's empty column, was
// drawn ALWAYS (changing the page color was tied to no firmware state), and a
// tap or a hold opened the light-mode ink picker or the dark-mode gun mixer
// depending on the live appearance. Its layout, its paint, its hit test and its
// synthetic-tap hatch all left with it; the two drawers did NOT -- they are
// whole and still reachable from CROSSPOINT_SIM_OPEN_INKPICKER /
// CROSSPOINT_SIM_OPEN_MIXER, because "for now" is reversible and the page it
// used to edit is frozen rather than gone (src/FrozenPage.h).
//
// DO NOT CONFUSE IT WITH THE KEYBOARD CHIP ABOVE, which stays. That one is the
// only way to put the iPhone's software keyboard away -- an off-pad tap does
// nothing and iPhone's keyboard carries no dismiss key of its own -- so
// removing it would trap a reader in a text field with 40% of the screen gone.
// They were told apart by what each is gated on and what each does: the
// keyboard chip draws and hit-tests only while `gpio.isTextEntryActive()`, is
// centered in the bottom row, carries a chevron glyph, and toggles
// `setHostKeyboardVisible`; the color button was unconditional, sat in column 1
// beside POWER, was a bare unmarked capsule, and called
// CrossPointMixer_present() / CrossPointInkPicker_present().

bool g_padLaidOut = false;

// ZEN READING MODE (owner ruling 2026-08-19). A three-finger tap on the page
// toggles it -- or, since 2026-08-27, a ONE-FINGER HOLD OF FIVE SECONDS
// (owner: "holding down one finger longer than five seconds toggles zen and
// single finger modes"; "single finger mode" is his term for not-zen). Both
// gestures are always-enabled recognizers in CrossPointZenRecognizers.mm and
// both land here through CrossPointZen_toggleFromRecognizer, which names which
// one fired. In zen the pad stops drawing and stops hit-testing entirely, the
// paper extends down toward where the top rocker row would begin, and input
// becomes the GESTURE LANGUAGE of 2026-08-22 (which replaced the original
// screen-thirds tap zones). Every gesture that MOVES — one- and two-finger
// swipes, pinch/spread — plus the multi-finger taps are native UIKit
// recognizers now (CrossPointZenRecognizers.mm; owner: "let's use apple for
// swiping instead"); the one-finger deliberate TAP stays on ZenVerbs.h and
// this file's SDL finger path. Everything comes back on the next three-finger
// tap or five-second hold.
// CROSSPOINT_SIM_ZEN=1 starts in zen. The three-finger gesture cannot be driven
// from CROSSPOINT_SIM_INPUT_SCRIPT -- its TAP feeds the FIRMWARE's touch state
// (HalGPIO::beginTouch), not SDL finger events, so it never reaches this file --
// and simctl cannot inject multi-touch either. Without this hook the zen LAYOUT
// could not be captured off-device at all, and the geometry is the half that
// has pixels to check.
bool g_zen = std::getenv("CROSSPOINT_SIM_ZEN") != nullptr;
// The page's rect on the last present, in device pixels -- the zen hit-test
// needs it, and it is the same rect the pad already anchors to.
SDL_FRect g_zenPanel{};
// The top rocker row's top edge in device pixels, 8pt-grid snapped: how far the
// paper reaches in zen. Published by layoutPad so the painter and the hit test
// read one number.
float g_zenRowTopPx = 0.0f;
// The PAPER in zen -- the page plus the strip below it, down to that row. The
// zen zones are measured against this rather than the page, so the thirds line
// up with what the reader can actually see.
SDL_FRect g_zenPaper{};
// THE PAPER'S BOTTOM EDGE in device px -- the boundary the gesture zones split
// on below, as the card top is the one above. It is the old top-rocker line
// (g_zenRowTopPx), which is the same `line` the zen painter cuts the sheet at
// and therefore the same edge the eye sees; the fallback is the panel's own
// bottom, exactly as the painter's is.
//
// ONE DEFINITION, TWO CALLERS: the SDL finger path in this file, and the UIKit
// recognizers through CrossPointZen_paperBottomPx() at the foot of the file.
// Writing it twice is how the finger and the picture start disagreeing about
// where the paper ends.
inline float zenPaperBottomPx() {
  if (g_zenRowTopPx > 0.0f) return g_zenRowTopPx;
  return g_zenPanel.y + g_zenPanel.h;
}

// The zen GESTURE LANGUAGE replaced the zen tap zones on 2026-08-22 (owner:
// The classifier -- pure, host-tested -- lives in ZenVerbs.h with the full
// succession note (zones -> hand-rolled verbs -> native recognizers for all
// motion). Since the "let's use apple for swiping instead" ruling it owns
// exactly ONE verb, the one-finger deliberate tap; the shim feeds it finger
// events and forwards that verb to gpio.queueButtonTap on the last lift.
// Multi-finger and moving gestures are CrossPointZenRecognizers.mm's.
zenverbs::Classifier g_zenVerbs;
// WHERE THE DELIBERATE TAP LANDED, in device px. The classifier resets itself
// on the last lift, so the landing point has to be kept beside it -- and it is
// the LANDING point rather than the lift that decides the zone, which is the
// same rule the zen zones have used since 2026-08-22. (The two are within the
// classifier's 28 px slop of each other by construction, so this is a matter of
// stating which one is meant, not of a measurable difference.)
float g_zenTapDownY = 0.0f;
// The visible paper card's top edge in device px, published by the layout
// pass; the zen band math reads it as the TOP BAND the eye actually sees.
float g_cardTopPx = 0.0f;
// In zen the panel is PLACED within the sheet rather than top-aligned: this
// many device px of the reserved band are moved from the bottom inset to the
// top inset, so the fit box height -- and therefore the page's scale -- is
// UNCHANGED (the 2026-08-19 no-resize ruling), while the page rides lower.
// Computed each layout pass from the selected band ratio and the measured
// content insets; converges over two passes like the band itself.
float g_zenPanelShiftPx = 0.0f;
// The value of the shift consumed by THIS layout pass (band and top inset
// must agree; see the snapshot comment at the band).
float g_zenShiftThisPass = 0.0f;
// The paper->ink visual gap in device px, published by the zen placement pass.
// It is the diameter of the construction's top-margin circle. THE PHONE's
// corner radius is still that circle's radius (owner 2026-08-22, "use the
// circle that determines the height gap between paper and text to make the
// corner radius of the paper") -- unchanged. THE TABLET's is not, as of
// 2026-08-29: the owner replaced the identity there with a flat unit/16
// (see paintTopBezel and paintBottomFillets, which now fork the divisor on
// CrossPointAppearance_isPad()). g_paperGapPx itself is still the same
// module on both platforms -- only what each platform DOES with it changed.
float g_paperGapPx = 0.0f;
float g_ptScale = 3.0f;
SDL_WindowID g_windowId = 0;

// Height of the black band above the page, in device pixels; 0 = no band.
// Written by layoutPad (phone path only), read by paintTopBezel.
float g_topBezelPx = 0.0f;

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
// Owner-approved layout 2026-08-02 (mockups: pad_layout_review artifact),
// updated 2026-08-11 (side rocker grown to full height, 8 pt grid):
//
//     [Back|Select]      [Left|Right]        <- front rockers, full squares,
//                                               hugging the panel's bottom edge
//     [Power]              [Up|Down]         <- full-height row (same as top),
//                                               bottom edge anchored at the
//                                               screen bottom, clear of the
//                                               home indicator
//
// UP/DOWN are the X3's SIDE buttons (MappedInputManager keeps them fixed as
// page-turn/Up/Down; main.cpp calls BTN_UP the "left side button") — fused
// into one rocker at the right. BACK/SELECT/LEFT/RIGHT are the FRONT buttons
// (the remappable frontButton* set), fused pairs as on the chassis. Fused
// pairs share an edge -- no gap inside a pair, a wide gap between pairs.
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
// Floor for the pad's OUTER edge on the tablet. A portrait iPad reports a
// horizontal safe area of 0 -- there is no notch to describe -- but the display
// still has a corner radius, so a capsule placed at x=0 is clipped by it. 16 pt
// on the same 8 pt grid the rest of this layout uses.
constexpr float kPadEdgeMin = 16.0f;
// kPaletteHoldMs lived here until 2026-08-20: tap and hold both open the
// mixer now, so there is no second gesture to time.

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
  // The HORIZONTAL safe area was never read here, only the vertical, and that
  // is what put the outer capsules under the screen's rounded corners -- see
  // kPadEdgeMin below.
  float safeLeft = 0.0f, safeRight = 0.0f;
  if (SDL_Window *win = SDL_GetWindowFromID(g_windowId)) {
    int lw = 0, lh = 0;
    SDL_Rect safe{};
    if (SDL_GetWindowSize(win, &lw, &lh) && lh > 0 && lw > 0 &&
        SDL_GetWindowSafeArea(win, &safe)) {
      safeTop = static_cast<float>(safe.y);
      safeBottom = static_cast<float>(lh - (safe.y + safe.h));
      safeLeft = static_cast<float>(safe.x);
      safeRight = static_cast<float>(lw - (safe.x + safe.w));
    }
  }

  // Panel fit, in device pixels, over the full safe height. The firmware
  // renders the X3 portrait, so the portrait framebuffer mapping applies
  // (logical width = DISPLAY_HEIGHT). Fractional scale below 1 is kept, same
  // as HalDisplay's fallback for windows shorter than the panel.
  // ACTIVE, not the ceiling: at a lower render scale the framebuffer is
  // smaller than DISPLAY_* and fitting the ceiling's dimensions would size the
  // panel for a picture that is not there.
  const float logW = static_cast<float>(HalDisplay::activeHeight());
  const float logH = static_cast<float>(HalDisplay::activeWidth());
  const float outWpx = W * S, outHpx = H * S;
  // THE KEYBOARD OVERLAPS ON EVERY DEVICE NOW, tablet included (owner ruling
  // 2026-08-19: "when ios keyboard is up on ipad, use the iphone pattern for
  // showing/hiding").
  //
  // This reverses the tablet-only lift that stood here. That lift was argued
  // from headroom -- a tablet has the room to reserve 400 pt without costing
  // the panel an integer scale, where a phone does not -- and the argument was
  // sound but answered the wrong question. The point is not whether the page
  // CAN move, it is that the page moving is a different interaction from the
  // one the phone teaches, and one pattern across the range beats a better
  // pattern on one device. The way back is the same on both now: the dismiss
  // bar riding the keyboard, or the chip in the pad's bottom row.
  const float availPx = SDL_max(1.0f, (H - safeTop - safeBottom) * S);
  float scale = SDL_min(outWpx / logW, availPx / logH);
  if (scale >= 1.0f) scale = SDL_floorf(scale);
  const float panelWpx = logW * scale, panelHpx = logH * scale;

  // AN AREA ABOVE THE PAPER (owner ruling 2026-08-29: "improving ipad pro
  // layout, including needing an area above paper (currently goes to screen
  // edge)"). Measured before this landed:
  // ios/mockups/ipad-BEFORE-portrait-page-2026-08-29.png -- the paper's
  // cream tone ran to the physical top edge, behind the status bar, with no
  // card and no margin at all; this function used to center the panel with
  // no card top published, so paintTopBezel below never had a band to draw.
  //
  // CORRECTED 2026-08-29, same day. The first pass here applied "1 up top,
  // 2 below" to the WRONG gap: it reused the phone's zen circle verbatim,
  // which splits the margin INSIDE the sheet (paper edge to ink -- the slack
  // plus the firmware's ink insets, computed below g_zenRowTopPx in
  // layoutPad), not the band the owner was pointing at. His words were "an
  // area above paper (currently goes to screen edge)" -- the space OUTSIDE
  // the sheet, between the physical top edge and the paper. Owner, from the
  // render: "I said 1 up top and 2 below was best. that seems to be have
  // been ignored." Measured off that build's own capture (luminance
  // run-lengths down the centre column of
  // ipad-AFTER-portrait-page-2026-08-29.png): 64 px above the card (0.17
  // circle units of THAT build -- kPadEdgeMin, the floor, doing all the
  // work; the 1-unit term never reached the outer placement at all) against
  // 781 px below (2.04 units) -- a rendered ~1:12 split, not 1:2.
  //
  // THE CORRECTED CONSTRUCTION splits the OUTER space directly, in exactly
  // the ratio asked, off the height actually left over once the panel's own
  // (already scale-fit) height is set aside -- "the card takes what is
  // left":
  //
  //   unit  = (outHpx - panelHpx) / 3
  //   above = 1 * unit
  //   below = 2 * unit
  //
  // No ink-inset term enters this at all: that term still belongs to the
  // phone's zen placement (a different question -- the margin INSIDE the
  // sheet) and is untouched there. The panel is top-aligned immediately
  // below the 1-unit band.
  //
  // FLOORED, still: hiding the status bar (see
  // CrossPointAppearance_hideStatusBarOnIPad, added the same day) makes
  // SDL_GetWindowSafeArea report safeTop 0 on this iPad Pro from the SECOND
  // layout pass onward -- there is no notch here, so the status bar was the
  // only reason iOS reserved anything at the top, and once it is confirmed
  // hidden the safe area collapses to nothing. In practice the derived unit
  // (measured ~194 pt on an iPad Pro 13 M4 portrait) dwarfs both floor terms
  // below; they exist for the degenerate case -- a very short available
  // height, or a device with a genuine notch/Island -- where the derived
  // unit alone would not be enough. kPadEdgeMin (16 pt) is reused rather
  // than a new constant because it already plays this exact role sideways on
  // this same function -- the floor for an iPad edge inset the system safe
  // area legitimately reports as 0.
  const float unit = SDL_max(0.0f, (outHpx - panelHpx) / 3.0f);
  const float cardTopPx = SDL_max(unit, SDL_max(safeTop, kPadEdgeMin) * S);
  // THE CORNER RADIUS is struck from THIS circle -- the outer 1-unit band
  // above the card -- not the ink-inset one the first pass carried over from
  // the phone's zen placement; a different circle from the one the 2026-08-22
  // identity was coined for, on this path.
  //
  // THE DIVISOR CHANGED, 2026-08-29 -- TABLET ONLY. The 2026-08-22 identity
  // (owner: "use the circle that determines the height gap between paper and
  // text to make the corner radius of the paper", radius = half the circle's
  // diameter) held for this circle too, until the owner overrode it here
  // specifically: "change the corner radius rounding to be 1/16 of unit."
  // `paintTopBezel` and `paintBottomFillets` now fork the divisor on
  // `CrossPointAppearance_isPad()` -- 16 here, the original 2 unchanged on
  // the phone's own circle (the ink-gap one, set in layoutPad's zen block,
  // which this ruling does not touch).
  g_paperGapPx = unit;
  const float topPx = cardTopPx;
  const float belowPx = SDL_max(0.0f, outHpx - cardTopPx - panelHpx);
  SDL_Log("[pad] tablet top band: unit=%.1fpx (1:2 split) card=%.1fpx "
          "panelTop=%.1fpx panelH=%.0fpx below=%.1fpx (%.2fx unit)",
          unit, cardTopPx, topPx, panelHpx, belowPx,
          unit > 0.0f ? belowPx / unit : 0.0f);
  g_cardTopPx = cardTopPx;
  // Unconditional on the tablet (unlike the phone's cut-out gate): paints the
  // same black band + squircle corners paintTopBezel already draws for the
  // phone, off the SAME g_topBezelPx/g_paperGapPx globals -- no new paint
  // code, see paintTopBezel below.
  g_topBezelPx = cardTopPx;
  SimulatorOverlay::setTopInset(static_cast<int>(topPx));
  SimulatorOverlay::setBottomInset(static_cast<int>(belowPx));

  const float margin = (W - panelWpx / S) / 2.0f;

  // THE OUTER CAPSULES USED TO TOUCH BOTH SCREEN EDGES, and on a rounded display
  // that means they are clipped. `cell` was min(kOptimalSquare, margin / 2), so
  // the moment the margin was tighter than 2x60 -- every iPad in portrait --
  // cell became exactly margin/2, which collapsed leftX to 0 and put the right
  // pair's outer edge exactly on W. Reported on iPad Pro 13 portrait, visible on
  // Home with no keyboard involved.
  //
  // The band each pair gets is inset on its OUTER side by the horizontal safe
  // area, floored at kPadEdgeMin for the devices that report 0 there (portrait
  // iPads have no notch, so the safe area does not describe the corner radius).
  // Same shape as kHomeInsetMin does for the bottom edge.
  const float edge = SDL_max(SDL_max(safeLeft, safeRight), kPadEdgeMin);
  const float band = SDL_max(0.0f, margin - edge);
  const float cell = SDL_min(kOptimalSquare, band / 2.0f);
  // Snapped to the 8 pt grid, matching what the phone path already does for
  // kPowerH (owner ruling 2026-08-11). The tablet was simply never updated when
  // the phone was: 30 pt on a standard iPad, 27 on a mini. Now 32 and 24.
  const float half = SDL_roundf(cell / 2.0f / 8.0f) * 8.0f;
  // Centred inside each inset band, so the pair is symmetric about the band and
  // the outer capsule stops `edge` short of the screen rather than on it.
  const float bandPad = (band - 2.0f * cell) / 2.0f;
  const float leftX = edge + bandPad;
  const float rightX = W - margin + bandPad;
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
      H - SDL_max(safeBottom, kHomeInsetMin) - half;

  auto place = [&](int idx, float x, float y, float w, float h) {
    g_pad[idx].rect = {x * S, y * S, w * S, h * S};
  };

  place(kPadBack, leftX, midY, cell, cell);
  place(kPadConfirm, leftX + cell, midY, cell, cell);
  place(kPadLeft, rightX, midY, cell, cell);
  place(kPadRight, rightX + cell, midY, cell, cell);

  // The tablet pad's horizontal geometry, once per layout. This is the line
  // that shows whether the outer capsules clear the screen edge -- leftX must
  // be >= edge, and rightX + 2*cell must be <= W - edge. They were 0 and W
  // exactly until 2026-08-17.
  SDL_Log("[pad] tablet W=%.0f margin=%.1f edge=%.1f cell=%.1f leftX=%.1f "
          "rightPairEnd=%.1f (clearance L=%.1f R=%.1f)",
          W, margin, edge, cell, leftX, rightX + 2.0f * cell, leftX,
          W - (rightX + 2.0f * cell));

  place(kPadPower, leftX, lowerY, cell, half);
  // The page-color button used to take the column beside POWER here. Removed
  // 2026-08-24; that column is empty again, which is what it was before the
  // button existed.
  // THE SIDE ROCKER STAYS. Retired on 2026-08-19 under "for ipad iphone and all
  // devices, lose the side button ui", and RESTORED the same day when the owner
  // saw it missing: he had called this control "the critically important side
  // rocker in the ios sim" hours earlier, and the ruling it was cut under was
  // about the e-ink panel's drawn side-button HINTS (T-011 in the firmware),
  // not the pad's real control. On iOS the pad is the only input there is.
  place(kPadUp, rightX, lowerY, cell, half);
  place(kPadDown, rightX + cell, lowerY, cell, half);

  // The keyboard chip, one cell wide and centerd under the page -- the same
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

  // 16, not 20 (owner ruling 2026-08-11, from the drawn options). On the 8 pt
  // grid, and the tighter inset buys every column a little width back.
  constexpr float kMargin = 16.0f;      // side inset
  constexpr float kGap = 16.0f;
  // Panel -> top row gap MATCHES THE CHASSIS (owner ruling 2026-08-02): on the
  // X3 the front buttons' top edge sits 11.6 mm below the panel window, 14.8%
  // of the 78.2 mm panel height (measured from Xteink's straight-on product
  // renders; the firmware repo's docs/hardware-dimensions.md holds the full
  // table and methodology). Expressed as a ratio of the PRESENTED panel height
  // so the proportion holds at any device scale; kGap is the pre-first-present
  // fallback only.
  constexpr float kPanelGapRatio = 11.6f / 78.2f;
  // WHICH EDGE the 11.6 mm is measured to, on OUR rocker: its BOTTOM (owner
  // ruling 2026-08-11, "measure from bottom of top rocker buttons instead of
  // center (same ~11mm distance)").
  //
  // The chassis figure is panel -> slot TOP, and the code used to apply it to
  // our rocker's top as well. That only lines up if the two are the same
  // height, and they are nowhere near: the real slot is 2.8 mm -- about 19 pt
  // here -- while a touchable rocker has to be 64. Anchoring our much taller
  // control by its bottom edge instead puts the part of it your thumb comes to
  // rest against where the device's button is, and lets the extra height grow
  // upward into the space above rather than pushing the whole control down.
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
  // 8, not 12 (owner ruling 2026-08-11, chosen from the drawn options over my
  // advice to leave it). It costs 4 pt of the picture-in-picture clearance the
  // 2026-08-04 tuning bought -- the corner PiP window now clears the bottom row
  // by ~14.7 pt rather than ~18.7 -- and buys the 8 pt grid. Recorded so the
  // next person reads a decision rather than a stray number.
  constexpr float kPipLift = 8.0f;
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
  // 8 pt grid snap for control heights. kSquare (derived from usable/cols) is
  // not generally a multiple of 8; rounding it keeps heights on-grid while
  // widths stay device-exact. The difference is sub-pixel on all supported
  // devices (55.83 → 56 pt on iPhone 13 mini).
  const float kCellH = SDL_roundf(kSquare / 8.0f) * 8.0f;

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

  // Bottom row: full height (kCellH), anchored at the bottom of the screen.
  // The BOTTOM EDGE is fixed at H - bottomInset - kPipLift; the top edge
  // grows UPWARD from there (owner ruling 2026-08-11: grow from the bottom).
  // maxUpper derives from lowerY, so the top row follows automatically and
  // the two rows keep their spacing.
  //
  // NOT keyboard-aware, unlike the tablet path (owner ruling 2026-08-10: the
  // keyboard OVERLAPS, it does not push). The phone's pad is a band BELOW the
  // page, so lifting it clear of the keyboard would paint controls over the
  // text -- and since the panel no longer shrinks either, there is nowhere for
  // a lifted band to go. While the keyboard is up it covers the page's lower
  // edge and the pad alike; the bar above it puts it away in one tap, and the
  // keyboard chip brings it back.
  const float lowerY = H - bottomInset - kCellH - kPipLift;

  // Top row hugs the panel at the chassis-matched gap less the lift, clamped
  // clear of the bottom row and never over the page.
  //
  // UNCHANGED, deliberately: kThumbRowFromBottom is an iPad-only ruling (owner,
  // 2026-08-09 -- "rockers should only have been moved up on ipad"). The phone
  // keeps the owner-approved 2026-08-02 arrangement, where the top row sits
  // just under the page because that is where a phone is held. A tablet is
  // gripped by its sides, which is why its rockers needed a fixed thumb
  // distance and this does not.
  const float maxUpper = lowerY - kRowClear - kCellH;
  const int panelBottomPx = SimulatorOverlay::panelBottomPx();
  const int panelHeightPx = SimulatorOverlay::panelHeightPx();
  const float panelGap =
      panelHeightPx > 0 ? (static_cast<float>(panelHeightPx) / S) * kPanelGapRatio : kGap;
  float upperY;
  if (panelBottomPx > 0) {
    const float panelBottom = static_cast<float>(panelBottomPx) / S;
    // Snapped to the 8 pt grid the pad aligns to (owner ruling 2026-08-11:
    // "always align everything on a square grid"). The BOTTOM distance is what
    // gets snapped, because it is the measured quantity; the top edge follows
    // and lands on the grid too, since the row height is itself a multiple of 8.
    //
    // kPipLift is NOT applied here. It was a fudge that nudged the row up from
    // a top-edge target, and against a bottom-edge target it would double-count.
    const float bottomGap = SDL_roundf((panelHeightPx / S) * kPanelGapRatio / 8.0f) * 8.0f;
    upperY = panelBottom + bottomGap - kCellH;
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
  place(kPadBack, colX(0), upperY, kSquare, kCellH);
  place(kPadConfirm, colX(1), upperY, kSquare, kCellH);
  place(kPadLeft, colX(cols - 2), upperY, kSquare, kCellH);
  place(kPadRight, colX(cols - 1), upperY, kSquare, kCellH);

  // Bottom row: POWER in the first column, the fused side rocker at the end.
  //
  // POWER STAYS HALF HEIGHT, and this is a ruling, not an oversight. The
  // 2026-08-11 instruction named the side button rocker and nothing else; POWER
  // was grown to match it anyway, on the reasoning that one short key beside
  // full-height ones looks inconsistent. The owner's answer: "changing power
  // button was a fuckup". The half-height bottom row is itself owner-approved
  // (2026-08-02, see the trade-off note above layoutPad), so a short POWER is
  // the design rather than a loose end to tidy. Do not grow it again without a
  // ruling that says POWER.
  //
  // It hangs from the row's BOTTOM edge, so it shares a baseline with the
  // full-height rocker beside it instead of floating in the middle of the row.
  const float kPowerH = SDL_roundf(kCellH / 2.0f / 8.0f) * 8.0f;
  place(kPadPower, colX(0), lowerY + (kCellH - kPowerH), kSquare, kPowerH);
  // The page-color button used to hang from POWER's baseline in column 1.
  // Removed 2026-08-24; column 1 is empty again, which is what it was before
  // the button existed. POWER is unchanged -- it keeps its half height and its
  // bottom-edge hang, which is a ruling of its own (see above).
  // The side rocker, restored 2026-08-19 -- see the note in the phone layout.
  place(kPadUp, colX(cols - 2), lowerY, kSquare, kCellH);
  place(kPadDown, colX(cols - 1), lowerY, kSquare, kCellH);

  // The keyboard chip: 48pt square, matching the "Hide keyboard" bar button's
  // size (kButton in CrossPointKeyboardBar.mm -- change one, change the other,
  // same pairing that file's glyph comment already enforces for the artwork)
  // so the toggle reads as one control in two states rather than growing
  // between them. Centerd in the bottom row (owner ruling 2026-08-10) -- dead
  // center rather than on the column grid, since with an even column count no
  // cell straddles the middle and a control that is not one of the seven
  // should not pretend to sit in their grid. The bottom row leaves columns
  // 1..cols-3 empty in every layout (cols is at least 5), so the chip always
  // clears POWER and the side rocker, and the reserved band below is
  // untouched.
  constexpr float kChipSide = 48.0f;
  g_kbChip = {((W - kChipSide) / 2.0f) * S, (lowerY + (kCellH - kChipSide) / 2.0f) * S,
              kChipSide * S, kChipSide * S};

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
  // Both rows are now kCellH tall, so the reserved band grows from
  // (kSquare + kHalf) to (kCellH + kCellH). On iPhone 13 mini this adds
  // ~28 pt to the band. The panel has enough vertical headroom that its
  // integer scale is unaffected.
  // ZEN DOES NOT RESIZE THE PAGE (owner ruling 2026-08-19: "do not resize with
  // zen"). The first version shrank this band so the page itself grew down to
  // the row -- but that re-fits the panel, and on a phone the fit is a
  // FRACTIONAL minification of the 3x framebuffer, so zen quietly changed how
  // every pixel of the page was resampled (measured: 0.6212 -> 0.6818).
  // What zen extends is the PAPER, painted below the page in paintPad. The
  // page's own geometry is byte-identical in both modes.
  const float band = panelGap + kCellH + kRowClear + kCellH + bottomInset;
  // The zen placement shift moves pixels from this bottom reserve to the top
  // inset below, in equal measure, so the panel's fit box never changes size
  // -- but consuming it here, BEFORE `want` below has had a chance to update
  // it for THIS pass, is what cost a visible flicker (docs/zen-mode.md,
  // "less flickering of layout when zen mode is enabled/disabled",
  // 2026-08-29). `want`'s own computation is deliberately independent of
  // `band`/this pass's shift (see its comment: "computed absolutely...
  // reading it would feed the loop its own output"), so nothing between here
  // and there needs the OLD value published first. Moved below, after `want`
  // has updated g_zenPanelShiftPx, so THIS pass's own present already uses
  // the converged shift instead of the previous pass's leftover.

  // How far the paper reaches in zen: the top rocker row's top edge, snapped
  // DOWN to the 8pt grid, PLUS four cells.
  //
  // The row's top edge alone was the first ruling, and measured on an iPhone
  // Air it made the page bottom-heavy the WRONG way: 84 px of paper above the
  // first ink against 45 px below the last, so the sheet read as sliding off
  // the bottom of the screen. The bottom band cannot be fixed by moving this
  // edge up -- up is where the ink is. Owner ruling 2026-08-20, picking cell 82
  // of 8 on that device: go four cells PAST the old line, giving 141 px below
  // the ink against 84 px above.
  //
  // Four CELLS rather than 96 px so it holds on any device: the grid is in
  // points, so this is 32 pt everywhere and lands on the grid by construction.
  // Nothing is drawn in that band in zen -- the row the old line protected is
  // one of the things zen hides -- so there is nothing left to run into.
  // SUPERSEDED 2026-08-21 (owner: "extend the bottom margin of paper in zen
  // mode to an optimal and proven distance"): the +4-cells rule above gave
  // 141 px of paper below the ink and left 624 px (208 pt) of black glass
  // under the sheet on an iPhone Air, measured. The proven distance is the
  // boundary this code already trusted as its clamp: the HOME INDICATOR'S
  // inset, the system's own safe floor, adopted after the bug where the
  // paper's corners ran off-glass. The paper now extends TO that floor --
  // maximal glass, a boundary Apple defines, no third arbitrary constant.
  // (History: row-top alone read as sliding off the screen; row-top + 4 cells
  // was the 2026-08-20 pick, 141 px below vs 84 above; both kept above for
  // the record.)
  // The floor alone (above) overshot: it left the black band BELOW the sheet
  // (120 px) smaller than the band above it (204 px), which is the exact
  // sliding-off-the-bottom read the 2026-08-20 ruling fixed. The proven
  // proportion is Van de Graaf's: a page's bottom margin is TWICE its top
  // (1/9 against 2/9 of the height -- the classical canon Tschichold
  // demonstrated). Applied to the sheet on the glass: the black band below
  // the paper = 2x the band above it. Anchored to the panel-top rect
  // (g_zenPaper.y, 241 px on an iPhone Air) via a phi multiplier that lands
  // the VISIBLE card bands at 204:408 device px -- measured exactly 1:2 --
  // and still clamped to the home-indicator floor. Owner ask 2026-08-21:
  // "extend the bottom margin of paper in zen mode to an optimal and proven
  // distance", after rejecting the bare floor ("there is a geometry to it").
  // The proportion is a CONSTANT again: top black band : bottom black band =
  // 1:2, Van de Graaf's canon, anchored to the VISIBLE paper card's top edge.
  // A five-rung ladder (1:2, 2:3, 3:5, 5:8, 1:phi — the Fibonacci convergents
  // walking toward phi) shipped as a setting on 2026-08-21 and was reduced to
  // 1:2 by owner order 2026-08-22 ("let's remove the option for every ratio
  // but 1:2"); a one-option row is decoration, so the row died with the other
  // four rungs (Root.plist, CrossPointPrefs).
  const float mult = 2.0f;
  const float gridPx = 8.0f * S;
  const float topBandPx = g_cardTopPx > 0 ? g_cardTopPx : 68.0f * S;
  // NOT grid-snapped: the neighboring rungs (5:8 and 1:phi) differ by under
  // 4 px on a phone, and the 24 px snap rendered them identical -- a settings
  // row that paints the same pixels as its neighbor is decoration. The floor
  // keeps its snap; the ratio edge is exact.
  const float ratioToPx = SDL_roundf(H * S - mult * topBandPx);
  const float floorToPx =
      SDL_floorf(((H - bottomInset) * S) / gridPx) * gridPx;
  g_zenRowTopPx = SDL_min(ratioToPx, floorToPx);
  // PANEL PLACEMENT WITHIN THE SHEET (owner 2026-08-22: "place the panel
  // where it is best within the paper, based on the ratio and the rendered
  // content"). The band ratio also governs where the page sits: the
  // VISUAL margins -- paper edge to ink, not to the panel's bounds -- split
  // top : bottom = 1 : r.
  //
  // The ink insets come from the FIRMWARE now: EpubReaderActivity publishes
  // its final text-block insets (top after the cap-ink trim) in framebuffer
  // px through HalGPIO::publishReaderTextInsets, and they scale to device px
  // by the same presented factor the panel itself was scaled by. The two
  // constants below are the documented FALLBACK for the window before the
  // first page render publishes anything: they were measured from real full
  // pages at this device class (docs/zen-page-margins.md §4) and are exact
  // only at the config they were measured at -- which is precisely why the
  // published values replace them (2026-08-22 layout exactness pass).
  {
    constexpr float kInkTopInsetPx = 60.0f;
    constexpr float kInkBottomInsetPx = 35.0f;
    float inkTopPx = kInkTopInsetPx;
    float inkBottomPx = kInkBottomInsetPx;
    const char *inkSrc = "fallback";
    {
      int t = 0, r = 0, b = 0, l = 0;
      // Portrait presented height corresponds to the framebuffer's WIDTH
      // (the firmware renders the X3 landscape and the presentation rotates),
      // same mapping the panel fit above uses (logH = activeWidth()).
      const float fbPortraitH = static_cast<float>(HalDisplay::activeWidth());
      const float presentedH =
          static_cast<float>(SimulatorOverlay::panelHeightPx());
      if (SimulatorOverlay::readerTextInsetsPx(t, r, b, l) &&
          fbPortraitH > 0 && presentedH > 0) {
        const float toDevice = presentedH / fbPortraitH;
        inkTopPx = t * toDevice;
        inkBottomPx = b * toDevice;
        inkSrc = "published";
      }
    }
    SDL_Log("[zen] ink insets (%s): top=%.1fpx bottom=%.1fpx", inkSrc,
            inkTopPx, inkBottomPx);
    const float paperTopPx = topBandPx;
    const float panelHPx =
        static_cast<float>(SimulatorOverlay::panelHeightPx());
    // GATED ON ZEN, added 2026-08-30. The condition here used to be purely
    // geometric, and the shift it computes is consumed only in zen
    // (`g_zenShiftThisPass = g_zen ? ... : 0.0f`, below) -- so with zen OFF
    // this block ran, produced a `want` it then threw away, and on the way
    // there set `g_padLaidOut = false` and called requestPresent().
    //
    // The inputs are the FIRMWARE'S PUBLISHED INK INSETS, which change on
    // every page turn because every page's text block ends somewhere
    // different. So each page turn outside zen forced a full relayout and an
    // extra present for a value that could not be used: the panel re-fit for
    // one frame and settled back. Owner, 2026-08-30: "there is still a flash
    // on page change ... it's an odd quick resizing to the paper" -- with zen
    // disabled, which is what made the zen-only pre-warm (pollReaderInsets,
    // itself `if (!g_zen) return;`) unable to cover it.
    //
    // In zen nothing changes: same condition, same arithmetic, same shift.
    if (g_zen && panelHPx > 0 && g_zenRowTopPx > paperTopPx + panelHPx) {
      const float slack = g_zenRowTopPx - paperTopPx - panelHPx;
      const float visTotal = slack + inkTopPx + inkBottomPx;
      const float aboveVis = visTotal / (1.0f + mult);
      // THE MODULE. Owner 2026-08-22: "use the circle that determines the
      // height gap between paper and text to make the corner radius of the
      // paper." That gap IS a circle in the construction -- one circle above
      // the ink, two below -- so the sheet's corners are struck with the same
      // circle: radius = half the gap. The card's curve and its top margin
      // stop being two unrelated numbers.
      g_paperGapPx = aboveVis;
      const float panelTopWant = paperTopPx + aboveVis - inkTopPx;
      // The non-zen panel top is the card top plus the 12 pt paper margin --
      // computed absolutely rather than read back from the overlay, because
      // the published panel top already contains the previous pass's shift
      // and reading it would feed the loop its own output. The shift is the
      // difference, never negative (the page never rises above its non-zen
      // position) and never more than the band can give.
      const float panelTopNonZen = g_cardTopPx + 12.0f * S;
      float want = panelTopWant - panelTopNonZen;
      if (want < 0.0f) want = 0.0f;
      const float bandPx = band * S;
      if (want > bandPx - 8.0f * S) want = bandPx - 8.0f * S;
      if (SDL_fabsf(want - g_zenPanelShiftPx) > 0.5f) {
        // The whole computation, printed on every CHANGE of its answer -- the
        // 2026-08-22 convergence bug was debugged blind because nothing said
        // what shift was wanted or which panelH/insets produced it.
        SDL_Log("[zen] shift %.1f -> %.1fpx (panelH=%.0f slack=%.0f "
                "ink=%.1f/%.1f %s want=%.1f)",
                g_zenPanelShiftPx, want, panelHPx, slack, inkTopPx,
                inkBottomPx, inkSrc, want);
        g_zenPanelShiftPx = want;
        g_padLaidOut = false;  // consume the new value in a full, atomic pass
        // ...and ASK for that pass: relayout happens inside a present, and an
        // e-ink firmware may not present again for minutes. The overlay rule,
        // one level deeper than the poll that already follows it.
        SimulatorOverlay::requestPresent();
      }
    } else if (!g_zen) {
      g_zenPanelShiftPx = 0.0f;
    }
  }
  // NOW consume the shift -- `want` above has already updated
  // g_zenPanelShiftPx for THIS pass, not the previous one (see the comment
  // where this used to sit, above `band`). Same pairing rule as before: the
  // band (here) and the top inset (`topInset += g_zenShiftThisPass / S`,
  // below) must consume the SAME shift, or the fit box changes height inside
  // a single pass and the panel re-fits at a NEW SCALE -- the no-resize
  // ruling broken by the very code built to honor it. That shipped in build
  // 123, from the two consumers reading the shift at different times across
  // a relayout; moving BOTH to read it here, together, after it is fresh,
  // removes the earlier failure mode (a stale read at the FIRST consumer)
  // without reopening it.
  g_zenShiftThisPass = g_zen ? g_zenPanelShiftPx : 0.0f;
  const float shiftPt = g_zenShiftThisPass / S;
  SimulatorOverlay::setBottomInset(static_cast<int>((band - shiftPt) * S));
  SDL_Log("[zen] %s band=%.1fpt topRowY=%.1fpt paperTo=%.0fpx panelH=%dpx panelW=%dpx",
          g_zen ? "on " : "off", band, upperY, g_zenRowTopPx,
          SimulatorOverlay::panelHeightPx(), SimulatorOverlay::panelWidthPx());

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
  float safeTop = 0.0f;
  if (SDL_Window *win = SDL_GetWindowFromID(g_windowId)) {
    SDL_Rect safe{};
    if (SDL_GetWindowSafeArea(win, &safe) && safe.y > 0)
      safeTop = static_cast<float>(safe.y);
  }
  // OWNER 2026-08-17: "extend top up to dynamic island (too short currently)."
  //
  // The page used to take max(safeArea, kTopReserve), so on a cut-out phone the
  // 80 pt reserve always won and the page began ~24 pt BELOW the Island's lower
  // edge (measured: Island 20.0-56.3 pt, page top 80.0 pt). That gap is dead
  // black with nothing in it.
  //
  // The safe area is exactly the line iOS puts below the cut-out, so on a
  // cut-out device it is now taken as-is and the page runs up to the Island.
  // A phone with no cut-out reports the classic 20 pt status bar and keeps the
  // reserve -- moving ITS page up 60 pt is a change nobody asked for.
  //
  // WHAT THIS GIVES UP, stated because it was a deliberate choice and is now
  // reversed: the 80 pt reserve was sized to clear a floating Picture-in-Picture
  // window parked in a top corner (see the note above and
  // mockups/pip-envelope.html). At the safe area the page no longer clears one.
  //
  // OWNER 2026-08-18: "move panel down (without moving others) to be more clear
  // of rounded corners at top." So the safe area is taken PLUS ONE 8 pt STEP,
  // and the number has a measurement behind it rather than a taste.
  //
  // The display's own corner shape is shipped with the simulator, as the
  // framebuffer mask of the device profile
  // (`iPhone Air.simdevicetype/Contents/Resources/*.pdf`, a squircle path in
  // half-device-pixel units). Flattened and converted to points, its top-left
  // corner runs 88.5 pt across and 88.2 pt DOWN -- so at the safe area the
  // screen edge is still curving, and the black margin beside the page's own
  // rounded corner is pinched rather than constant. How far in the screen edge
  // still sits, measured off that path:
  //
  //     y = 55 pt: 1.71 pt      y = 72 pt: 0.21 pt
  //     y = 68 pt: 0.39 pt      y = 76 pt: 0.10 pt   <- under a third of a px
  //
  // 8 pt is the smallest step on the pad's grid (owner ruling 2026-08-11,
  // "always align everything on a square grid") that gets the page's top edge
  // to where the display's curve is done to within a third of a device pixel,
  // so the band beside the page's top corners reads as an even margin. It is
  // still 4 pt above the old 80 pt reserve, so the 2026-08-17 "extend top up to
  // dynamic island" ruling is trimmed, not undone.
  //
  // NOTHING ELSE MOVES, and that is the constraint the owner named. The panel
  // is HEIGHT-limited on this phone (scale 0.7323 comes from availH, not from
  // the width), so the 8 pt comes off the panel's HEIGHT and its bottom edge --
  // which is what the pad hangs from (SimulatorOverlay::panelBottomPx) -- stays
  // where it is. Verified by decoded screenshot, not by argument: the bottom
  // row, POWER, the palette chip and the keyboard chip are pixel-identical, and
  // the top row moves 4 device pixels (1.3 pt) -- the residue of the scale
  // quantum (6 px of panel height) plus the derived band's own shrink, an order
  // of magnitude under the 8 pt the page moved.
  // On a phone where the panel is WIDTH-limited the slack sits below
  // the page instead and the pad WOULD follow it down; there is no such device
  // in the profile list today (every one is short of height), and if one
  // appears this is the line that has to grow a case for it.
  //
  // OWNER 2026-08-18 (second ruling of the day): "both bring paper background
  // behind panel closer to dynamic island and also bring panel down so it not
  // too close to background edge." TWO moves, in OPPOSITE directions, and the
  // pair is the whole point:
  //
  //   * the CARD (the paper field the page sits on) goes UP, to the safe area;
  //   * the PAGE goes DOWN, to one margin below the card's own top edge.
  //
  // Until now those two were the same number -- the black band ended exactly
  // where the page began -- so there was no paper above the page at all, only
  // black. They are now separate: kCardTop is where black stops and paper
  // starts, topInset is where the page starts.
  //
  // WHY THE CARD STOPS AT THE SAFE AREA AND NOT HIGHER. The safe area IS the
  // line iOS draws below the cut-out; nothing public reports where the Island
  // actually ends (Apple DTS, docs/ios-dynamic-island.md §2), so any tighter
  // number would be a guess dressed as a measurement. On this phone the Island
  // ends at 56.3 pt and the safe area at 68.0, so the pill keeps 11.7 pt of
  // black below it -- Apple's own margin, not slack of ours. Going past it is
  // what puts the Island back in a pale field, which is the 2026-08-17 bug
  // ("a distracting hole above the panel") this band exists to prevent.
  //
  // WHY THE PAGE SITS 12 pt BELOW THE CARD'S TOP. The page already floats in
  // paper on three sides: the fit leaves ~18 pt of field either side of it on
  // this phone (panel 1148 px wide in a 1260 px window) and the pad's band
  // below. The top was the one edge where the page ran straight into the black.
  //
  // 16 pt would match those side margins more closely and was tried FIRST. It
  // MOVES THE PAD, which the owner ruled out: the pad's top row hangs at a
  // chassis-matched gap below the page, round(panelHeight * 11.6/78.2 / 8) * 8,
  // and that snap flips from 88 to 80 pt the moment the presented panel falls
  // under 566.27 pt tall. At a 16 pt margin the panel lands on 566.0 -- ONE
  // DEVICE PIXEL past the boundary -- and the top row jumped 22 px (7.3 pt).
  // Measured, not predicted: build, screenshot, decode.
  //
  // 12 pt leaves the panel ~570 pt, keeps the gap in its 88 pt bucket, and puts
  // the page's top edge at 80.0 pt -- which is both a whole 8 pt step from the
  // screen's top edge and, by coincidence worth noting, the old kTopReserve
  // line this file spent two rulings moving away from and back toward.
  //
  // So the page moves DOWN 4 pt and the paper above it goes from nothing to
  // 12 pt. The visible change is the margin, not the 4 pt.
  //
  // The card's rounded top corners are still cut by paintTopBezel, and they now
  // belong to the PAPER, not to the page -- at 12 pt deep the fillet has pulled
  // in to 12.1 pt of the 55 pt extent, inside the page's own ~19 pt side
  // margin, so the corner never bites the page.
  const float kCardTop = safeTop;      // black ends, paper begins
  const float kPaperMargin = 12.0f;    // paper above the page
  topInset = safeTop > 20.0f ? kCardTop + kPaperMargin : kTopReserve;
  g_cardTopPx = (safeTop > 20.0f ? kCardTop : topInset) * S;
  if (g_zen) topInset += g_zenShiftThisPass / S;
  SDL_Log("[layout] safe top %.1f pt -> card top %.1f pt, page top %.1f pt (%s)",
          safeTop, safeTop > 20.0f ? kCardTop : topInset, topInset,
          safeTop > 20.0f ? "paper card below the cut-out" : "reserve");
  SimulatorOverlay::setTopInset(static_cast<int>(topInset * S));

  // THE BEZEL BAND: where the black stops and the paper CARD's rounded top
  // corners start, in device pixels, or 0 for "do not paint one". paintTopBezel
  // reads it; see the comment on that function for why the band exists at all.
  //
  // This is kCardTop, NOT topInset. They were the same number until 2026-08-18
  // and the page's own top edge doubled as the card's; now the card comes up to
  // the safe area and the page sits kPaperMargin below it, so a band painted to
  // topInset would swallow the paper margin that ruling asked for.
  //
  // ONLY ON A DEVICE WITH A CUT-OUT. There is no public API that reports a
  // notch or a Dynamic Island -- Apple's DTS answer is that none exists and
  // that none is wanted (docs/ios-dynamic-island.md) -- so the only signal is
  // the safe area, and a top inset deeper than the classic 20 pt status bar is
  // the standard read of it. A home-button iPhone reports 20 and gets no band:
  // it has no hole to hide, and 80 pt of black above the page would be a
  // change nobody asked for on that hardware.
  g_topBezelPx = safeTop > 20.0f ? kCardTop * S : 0.0f;
}

// --- Appearance ------------------------------------------------------------
//
// THE PALETTE, THE CONTRAST LADDER AND THE PRESETS LIVE IN PadPalette.h, which
// is pure (no SDL, no UIKit, no clock) so tests/pad_palette_test.cpp can check
// every rung, every preset and every Root.plist label on a host. The design
// record -- hollow controls, why the fine end sits in the field's roomy
// direction, why the scale is signed and field-relative rather than an absolute
// 0-100% lightness, the WCAG 1.4.11 position, and the rejected alternatives --
// is the comment at the top of that header. What stays here is only the live
// state and the polling that keeps it current.
using padpalette::Palette;

bool g_dark = false;
Palette g_palette = padpalette::kLightPalette;
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
int g_appliedOutline = padpalette::kContrastMin - 1;
int g_appliedFill = padpalette::kContrastMin - 1;

// The four fine pickers and the preset row above them collapse into the two
// levels actually painted. Custom is the only state in which the fine pickers
// are read at all -- see PadPalette.h for why the preset overrides rather than
// writes them.
padpalette::Levels currentLevels(bool dark) {
  // ACCESSIBLE ONLY (owner order 2026-08-22: "switch to Accessible only for
  // button colors", alongside removing the Button Pad rows from Settings.app).
  // The stored padContrastPreset and the four fine pickers are ignored;
  // PadPalette's other presets and its machinery stay for the library and its
  // tests — only this app's choice is pinned.
  //
  // NOT PINNED HERE, though it was until 2026-08-23, and that is what made it a
  // bug: this was not a single resolution point. ios/PanelPrefs.h resolved the
  // pad a second time for the UIKit HIDE chip and went on handing the raw
  // stored contrasts to makePaletteOn, so the chip drew Current's +/-1 hairline
  // beside a pad drawn at Accessible's -4/+4 — two halves of one gesture, 4-5x
  // apart in contrast, under a header comment promising one definition.
  return crosspoint::padLevelsForPrefs(dark);
}

// --- The panel's own two tones ---------------------------------------------
//
// The presets, the hex parsing, the interpolation and the guards live in
// src/PanelPalette.h, pure and host-tested, for the same reasons PadPalette.h
// is: every failure mode here is a wrong COLOR, which no compiler and no other
// test in this repo can see. What stays here is the live state and the polling.
//
// The panel's PAPER is also the pad's FIELD. That is not a coincidence to be
// tidied away -- it is what makes the page float edgeless in the surround, and
// it is why the pad is rebuilt with makePaletteOn(..., panel.paper) rather than
// makePalette(): the pad's rungs are relative deltas, so they follow whatever
// paper the owner picked and stay a fixed step from it.
panelpalette::Palette currentPanel(bool dark) {
  // Delegates to ios/PanelPrefs.h, which the UIKit keyboard bar also uses. One
  // definition on purpose: the show chip is painted from this and the hide chip
  // from that, and they have to agree.
  return crosspoint::panelForPrefs(dark);
}


uint64_t packPanel(const panelpalette::Palette &p) {
  return (static_cast<uint64_t>(panelpalette::pack(p.ink)) << 24) |
         static_cast<uint64_t>(panelpalette::pack(p.paper));
}

// What applyPanel last published, packed, so the poll compares six bytes with
// one integer compare. The sentinel cannot be a real pair (a packed pair uses
// 48 bits), so the first call always applies.
uint64_t g_appliedPanel = ~0ull;

// Publish the panel tones and rebuild the pad on top of the new paper. Does NOT
// request a present: setPanelPalette raises one itself when the tones it is
// given are the ones currently on screen, and every caller here follows with a
// present of its own for the field.
void applyPanel(const panelpalette::Palette &panel) {
  g_appliedPanel = packPanel(panel);
  SimulatorOverlay::setPanelPalette(g_dark, panel.ink, panel.paper);
  g_palette = padpalette::makePaletteOn(g_dark, g_appliedOutline, g_appliedFill,
                                        panel.paper);
  const Palette &p = palette();
  SimulatorOverlay::setClearColor(p.field[0], p.field[1], p.field[2]);
  // The HIDE chip lives in the keyboard's accessory bar and is UIKit, not SDL,
  // so nothing repaints it on its own. The SHOW chip beside the pad is redrawn
  // from `panel.paper` every frame; without this the two halves of the same
  // gesture carried different tones the moment a non-default palette was
  // chosen. Cheap and idempotent, and a no-op while the keyboard is down.
  CrossPointKeyboardBar_refreshTint();
}

// Seed SETTINGS.darkMode from the system on the next applyTheme. Set only by
// pollAppearance, when the SYSTEM appearance actually changed.
// SEEDED ONCE, ON A FRESH INSTALL ONLY -- not on every launch.
//
// Seeding at every startup was the second half of the same bug: a relaunch is
// not the phone changing its mind, but it looked like one, so the stored
// setting was overwritten and an in-app toggle never survived being backgrounded.
// A settings file that already exists means the owner has been here and their
// choice stands; no file means first run, and the phone's appearance is the
// only sensible opening guess.
bool firstEverLaunch() {
  const char *sd = std::getenv("CROSSPOINT_SIM_SD");
  if (!sd || !*sd) return false;  // unknown: assume not, and leave the setting alone
  const std::string settings = std::string(sd) + "/.crosspoint/settings.json";
  FILE *f = std::fopen(settings.c_str(), "rb");
  if (!f) return true;
  std::fclose(f);
  return false;
}

// Whether this launch may write the system appearance into SETTINGS.darkMode.
//
// NOT simply firstEverLaunch() any more (owner 2026-08-28: "when booted into
// system dark mode, be in dark mode"). That rule could not see a change made
// while the app was CLOSED -- pollAppearance initialises its "last system" from
// the system itself, so on the first tick nothing has changed and the stored
// setting wins. Install in light, switch the phone to dark, reopen, and the app
// came up light.
//
// The question neither "always seed" nor "seed once" can answer is *did the
// system change since we last looked*, so the answer we last acted on is now
// remembered across launches, separately from the owner's setting. The rule is
// ios/AppearanceSeed.h; this is only where it is asked.
bool decideSeedDarkFromSystem() {
  const int stored = CrossPointPrefs_lastSeenSystemDark();
  const int now = systemIsDark() ? 1 : 0;
  const bool seed =
      appearanceseed::shouldSeedFromSystem(firstEverLaunch(), stored, now);
  // Recorded on EVERY launch, seeded or not: recording only when seeding would
  // leave an install that predates this rule stuck at "never recorded" for
  // ever, and a later system change invisible with it.
  CrossPointPrefs_setLastSeenSystemDark(appearanceseed::valueToRemember(now));
  SDL_Log("[harness] appearance seed: stored=%s system=%s -> %s", 
          stored < 0 ? "none" : (stored ? "dark" : "light"),
          now ? "dark" : "light", seed ? "SEED" : "keep setting");
  return seed;
}

bool g_seedDarkFromSystem = decideSeedDarkFromSystem();

void applyTheme() {
  // ONE SOURCE OF TRUTH, and it is the firmware's own setting.
  //
  // This used to read systemIsDark() directly, which made the pad and the field
  // follow iOS while the PAGE followed SETTINGS.darkMode -- two authorities for
  // one question. Toggling Dark Mode inside CrossPoint then inverted the page
  // and left the pad on the system's appearance, which is the "ios dark mode is
  // the opposite of dark mode in crosspoint" the owner reported; and because
  // every applyTheme wrote the system value back over the setting, the in-app
  // control did not stick at all. Verified before changing anything: with iOS
  // light and darkMode=1 stored, the app came up light.
  //
  // Now the system SEEDS the setting -- at startup, and whenever the phone's
  // appearance actually changes -- and everything reads the setting from there,
  // so an in-app toggle moves the whole screen and survives.
  if (g_seedDarkFromSystem) {
    const uint8_t wantSystem = systemIsDark() ? 1 : 0;
    if (SETTINGS.darkMode != wantSystem) {
      SETTINGS.darkMode = wantSystem;
      SETTINGS.saveToFile();
      SDL_Log("[harness] SETTINGS.darkMode -> %u (system appearance)", wantSystem);
    }
    g_seedDarkFromSystem = false;
  }
  g_dark = SETTINGS.darkMode != 0;
  g_appliedDark = g_dark ? 1 : 0;

  // Carry the system appearance into the firmware's OWN Dark Mode setting.
  //
  // Without this the two disagree, visibly and in the direction that reads as a
  // bug: the panel follows iOS immediately (setPanelDark, below) while
  // SETTINGS.darkMode keeps whatever was last stored, so System > Dark Mode in
  // the Settings screen shows Off over a dark page. It is also the setting the
  // firmware re-applies for itself -- main.cpp runs
  // `display.setInverted(SETTINGS.darkMode != 0)` during setup, AFTER the
  // harness has installed -- so a stale value does not merely display wrong, it
  // gets pushed back onto the panel and undoes the appearance the phone asked
  // for.
  //
  // Guarded on change, per the SPIFFS write rule: a repaint runs this, and a
  // settings file rewritten on every present would be a real cost on device
  // even though this path is host-only.
  // The levels are per-appearance, so a light->dark flip changes which pair is
  // in force. Read them here rather than leaving it to the next poll: the
  // palette this call publishes has to be the finished one.
  const padpalette::Levels lv = currentLevels(g_dark);
  g_appliedOutline = lv.outline;
  g_appliedFill = lv.fill;
  // BEFORE setPanelDark, which reads the live panel palette to pick the field
  // it clears to. Publishing after it would flip the polarity onto the previous
  // appearance's tones and show them for one present.
  applyPanel(currentPanel(g_dark));
  SimulatorOverlay::setPanelDark(g_dark);
  // The firmware presents only when it has new panel content, which on an e-ink
  // device is rare, so without this the new appearance would not appear until
  // the next page render. (setPanelDark's reconvert also raises a present, but
  // only when the polarity actually changed; the field color must repaint
  // regardless.)
  SimulatorOverlay::requestPresent();

  // ...and re-RENDER the activity, which requestPresent() does not do.
  //
  // requestPresent only pushes the framebuffer that already exists to the
  // screen. Anything the firmware DREW from a value this call just changed is
  // still the old pixels -- most visibly the System > Dark Mode row, which
  // keeps painting "Off" over a dark page until the owner navigates away and
  // back. The panel polarity flip inverts those pixels, so the stale row is
  // perfectly legible and perfectly wrong, which is the worst version of it.
  //
  // Deferred (immediate=false) on purpose: it sets a flag the manager reads at
  // the end of its loop, so this is safe from the harness thread and safe
  // before any activity exists -- applyTheme runs once at install, before
  // setup().
  crosspointRequestRender();
}

// When the app last returned to the foreground, on the SDL_GetTicks clock, or 0
// once the settle window below has elapsed. See presentationWatch.
// When the drawing surface last changed under us, and therefore when the
// settle-repaint window opened. Foregrounding is one cause; a WINDOW SIZE
// change is the other, and it was missed until 2026-08-28 (S-027).
Uint64 g_foregroundAt = 0;

// Open the settle window. Both callers have the same problem -- a present
// issued in the moment after the surface changes can be accepted and then
// discarded -- so both need the same answer, and a single present is not it.
inline void armSettleRepaint() { g_foregroundAt = SDL_GetTicks(); }

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
    armSettleRepaint();
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
  // Two things can move dark mode, and both have to land: the phone's own
  // appearance (which reseeds the setting) and the firmware's Dark Mode row
  // (which does not). Watching only the first is what let an in-app toggle
  // leave the pad behind.
  // Initialised from the system on the FIRST poll, not to -1. Starting at -1
  // made that first tick look like the phone had just changed appearance, which
  // reseeded the setting and overwrote the owner's stored choice on every
  // launch -- the same overwrite this fix exists to remove, reintroduced one
  // function further down. A function-local static initialises on first call,
  // so this is exactly "what the system was when we started".
  static int s_lastSystem = systemIsDark() ? 1 : 0;
  const int sys = systemIsDark() ? 1 : 0;
  if (sys != s_lastSystem) {
    s_lastSystem = sys;
    g_seedDarkFromSystem = true;
    // Keep the cross-launch memory in step with what we are about to act on,
    // or the next launch compares against a stale answer and re-seeds over a
    // choice the owner may have made since.
    CrossPointPrefs_setLastSeenSystemDark(sys);
    applyTheme();
    SDL_Log("[harness] appearance -> %s (system)", g_dark ? "dark" : "light");
    return;
  }
  const int want = SETTINGS.darkMode != 0 ? 1 : 0;
  if (want == g_appliedDark) return;
  applyTheme();
  SDL_Log("[harness] appearance -> %s (setting)", g_dark ? "dark" : "light");
}

// The pad's two tones, on the same terms as pollAppearance above and for the
// same reasons.
//
// EDGE-TRIGGERED ON THE RESOLVED LEVELS, not on the raw preferences. That is
// what makes the preset row free: switching Current -> Accessible changes the
// levels and repaints, while editing a fine picker under a non-Custom preset
// changes nothing and correctly repaints nothing.
//
// SETTINGS.APP IS A SEPARATE APP, so a change to these arrives while CrossPoint
// is backgrounded and there is no event to hang it on -- iOS posts
// NSUserDefaultsDidChangeNotification only for changes this process made.
// Reading the level here costs a dictionary lookup in an in-memory store, and
// the repaint is EDGE-TRIGGERED on the applied level: without that this would
// force a present every frame on a panel whose presentation model assumes it
// presents rarely.
// (pollZenRatio lived here 2026-08-21..22, watching the zenBottomRatio rung;
// it died with the setting when the band was fixed at 1:2.)

// Re-fit the zen sheet when the firmware's published ink insets appear or
// move. The placement block reads SimulatorOverlay::readerTextInsetsPx at
// LAYOUT time, but the first layout runs before the reader has rendered a
// page — the log then honestly says "fallback" — and nothing else would
// trigger a relayout on a boot that resumes straight into a book with zen
// already on, so the published values would sit unread forever. Edge-triggered
// on the published pair, same discipline as every poll here: one relayout per
// change (the first publish, then only a margin or font-size change), not one
// per frame.
void pollReaderInsets() {
  if (!g_zen) return;
  static int s_top = std::numeric_limits<int>::min();
  static int s_bottom = std::numeric_limits<int>::min();
  int t = 0, r = 0, b = 0, l = 0;
  if (!SimulatorOverlay::readerTextInsetsPx(t, r, b, l)) return;
  if (t == s_top && b == s_bottom) return;
  s_top = t;
  s_bottom = b;
  g_padLaidOut = false;  // force the relayout that re-places the zen sheet
  // Pre-warm BEFORE requesting the present, same reason as the toggle sites
  // (see zenPreWarmLayout()'s comment): otherwise the very first present
  // after real ink insets replace the fallback ones repeats the flicker this
  // fix targets, one step after entering zen instead of on it.
  zenPreWarmLayout();
  SimulatorOverlay::requestPresent();
  SDL_Log("[zen] published ink insets %d/%d fb-px -> relayout", t, b);
}

// Zen mode: keeps live g_zen and the STORED zenModeEnabled preference synced
// in BOTH directions via zensync::decide (ios/ZenPrefSync.h) — see that
// header for why a shared `synced` tracker is what stops a write in one
// direction from being read back as a change in the other. Two real
// triggers reach the sync protocol: Settings.app (an external edit reaches
// this poll as `ApplyToLive`) and a gesture toggle that already changed
// `g_zen` directly (CrossPointZen_toggleFromRecognizer, the one-finger hold
// above the paper — reaches here as `WriteToStore` so the row stops lying
// about it). The app's own launch seed (`first`) and CROSSPOINT_SIM_ZEN are
// handled OUTSIDE that protocol, not as a third trigger of it — see the
// `envForced` gate below for why the sync protocol must never run at all
// while the env var is set.
//
// ADDED 2026-08-29 (owner: "keep zen mode ios app setting reflective of
// active value"). Before this, CrossPointPrefs_zenModeEnabled() had no
// setter at all (grep confirmed zero writers besides Settings.app itself),
// so a gesture toggle left the row wrong from that moment on, and the next
// visit to Settings.app could silently revert a toggle the reader had
// already made.
void pollZenMode() {
  static bool s_synced = false;
  static bool s_first = true;
  const bool first = s_first;
  const bool envForced = std::getenv("CROSSPOINT_SIM_ZEN") != nullptr;
  const bool storedPref = CrossPointPrefs_zenModeEnabled() != 0;

  if (first) {
    s_first = false;
    // Logged because the seed is otherwise silent, and a wrong launch state
    // (zen defaults ON, owner 2026-08-22) has no other trace to debug from.
    SDL_Log("[zen] seed: pref=%d env=%s -> %s", storedPref ? 1 : 0,
            envForced ? "set" : "unset",
            (envForced ? g_zen : storedPref) ? "on" : "off");
    if (!envForced && g_zen != storedPref) {
      g_zen = storedPref;
      g_padLaidOut = false;  // in case a layout pass beat this first poll
    }
    CrossPointZenRecognizers_setEnabled(g_zen);
    s_synced = g_zen;
    return;
  }

  // CROSSPOINT_SIM_ZEN wins the boot seed above and STAYS THE HEADLESS HOOK
  // for the rest of the process -- the store-sync protocol below must never
  // run while it is set. Adversarial review 2026-08-29 caught the failure
  // mode directly: without this gate, decide()'s very next poll sees the
  // (unchanged) stored pref still disagreeing with the env-forced g_zen,
  // sees live still equal to `synced` (both left at the value the seed set
  // two lines above), concludes the STORE must be the side that moved, and
  // silently reverts the env override back to the stale stored value one
  // frame after boot -- exactly the class of bug this whole mechanism exists
  // to prevent, just aimed at the wrong side. This restores the pre-existing
  // guarantee ("the env var, when set, wins that one and stays the headless
  // hook") that a naive port of the old edge-triggered poll would have kept
  // by accident and this rewrite nearly lost on purpose.
  if (envForced) return;

  const zensync::Action action =
      zensync::decide(storedPref, g_zen, s_synced, /*first=*/false);
  if (action == zensync::Action::None) return;

  switch (action) {
    case zensync::Action::ApplyToLive:
      // Settings.app changed the row; make live match it.
      g_zen = storedPref;
      g_padLaidOut = false;  // the band changes, so the page must be refitted
      SDL_Log("[zen] %s (setting)", g_zen ? "on" : "off");
      CrossPointZenRecognizers_setEnabled(g_zen);
      // Publish the converged geometry BEFORE the present that will show
      // it — see zenPreWarmLayout()'s own comment for why the ordinary
      // draw-time pass (paintPad -> layoutPad) is one present too late to
      // avoid a visibly mismatched intermediate frame.
      zenPreWarmLayout();
      SimulatorOverlay::requestPresent();
      break;
    case zensync::Action::WriteToStore:
      // Live already changed (a gesture) and already asked for its own
      // present; this call's only job is to stop Settings.app's row from
      // lying about it. No relayout, no present — nothing on screen changes
      // here. (Never reached while CROSSPOINT_SIM_ZEN is set — the gate
      // above returns before this switch runs at all.)
      CrossPointPrefs_setZenModeEnabled(g_zen ? 1 : 0);
      SDL_Log("[zen] %s (gesture -> settings)", g_zen ? "on" : "off");
      break;
    case zensync::Action::None:
      break;  // unreachable: the early return above already handled it
  }
  s_synced = g_zen;
}

void pollPadContrast() {
  const padpalette::Levels lv = currentLevels(g_dark);
  if (lv.outline == g_appliedOutline && lv.fill == g_appliedFill) return;
  g_appliedOutline = lv.outline;
  g_appliedFill = lv.fill;
  // On the CURRENT paper, not the shipped one -- the rungs are relative, so the
  // pad has to be rebuilt against whatever the panel is showing.
  g_palette = padpalette::makePaletteOn(g_dark, lv.outline, lv.fill,
                                        currentPanel(g_dark).paper);
  SimulatorOverlay::requestPresent();
  SDL_Log("[harness] pad contrast (%s) -> preset %d, outline %+d, fill %+d",
          g_dark ? "dark" : "light", CrossPointPrefs_padContrastPreset(),
          lv.outline, lv.fill);
}

// The panel's ink and paper, on exactly the terms pollPadContrast runs on and
// for the same reasons: Settings.app is a separate process, so a change arrives
// while CrossPoint is backgrounded with no notification to hang it on, and the
// repaint has to be EDGE-TRIGGERED or a panel whose whole presentation model
// assumes it presents rarely would present every frame.
//
// Edge-triggered on the RESOLVED PAIR rather than on the raw preferences, which
// is what makes the preset row free: switching Default -> Sepia changes the
// pair and repaints, while editing a hex field under a named preset changes
// nothing and correctly repaints nothing.
//
// Main thread only, pumps no SDL events, holds no timer.
// THE GLOW'S SPEED IS THE PHOSPHOR'S OWN, COMPRESSED.
//
// The arithmetic moved to panelpalette::trailMsForPreset() -- a pure, tested
// function -- after the flat multiplier that used to live here shipped a
// TWENTY SECOND trail for P7 and made the cascade look broken on the phone.
// See the comment at that function for why the span is compressed rather than
// scaled, and tests/panel_palette_test.cpp for what is pinned about it.
//
// Nothing about the choice is host-specific, which is the other half of why it
// does not belong in an iOS-only .cpp: it could not be exercised anywhere but
// on a phone, and it was not.

// Set by the mixer when the mix changes UNDER the Custom preset: the dedupe
// below is on the preset integer, which does not move during a mix edit.
std::atomic<bool> g_glowDirty{false};

void pollPanelGlow() {
  static int s_appliedPreset = -1;
  // THE PHOSPHOR THE PAGE CLAIMS TO BE, not the raw stored preset.
  //
  // They differ whenever an editor has claimed the Custom slot for the OTHER
  // polarity: the dark page then keeps a named phosphor's tones, frozen, and
  // this read used to lose the phosphor with the integer -- picking a
  // light-mode ink turned a 283 ms White CRT trail into 0 ms reflective and
  // left it that way across relaunches (owner P1 2026-08-23, measured from the
  // app's own [glow] line). crosspoint::glowPresetForPrefs answers Custom only
  // when the MIXER owns the decay, which is the branch below.
  const int preset = crosspoint::glowPresetForPrefs();
  if (preset == s_appliedPreset && !g_glowDirty.exchange(false)) return;
  s_appliedPreset = preset;

  // NO SWITCH. Owner ruling 2026-08-17: "remove setting always have it on for
  // crts." A CRT palette is a claim that the page is a tube, and a tube glows --
  // the two were never separate choices, and a switch to turn a phosphor's
  // behavior off while keeping its color is a setting for a thing nobody
  // wants. Every other palette gets 0, because a page of e-ink does not decay.
  float trail = panelpalette::trailMsForPreset(preset);
  const unsigned char *tail = nullptr;
  const char *why = "not a phosphor";
  // THE CUSTOM SLOT MAY BE A MIX. Plain Custom has no phosphor and gets 0, but
  // an active mix carries its own decay -- a blend dies at its slowest
  // component's rate, a cascade at its persistence layer's -- and its own tail
  // tint. The mixer owns that store; asked here so a relaunch, a preset trip
  // away and back, and a settings change all converge on one answer.
  static unsigned char s_mixTail[3];
  // When the mix's hue handover completes -- the fast components' death, which
  // for the reported P46+P33 mix is ~17 ms into a 2828 ms fade. 0 for every
  // plain preset: their recolor keeps the old whole-trail ramp.
  float tailOnsetMs = 0.0f;
  if (preset == panelpalette::kPresetCustom) {
    float mixTrail = 0.0f;
    bool hasTail = false;
    float mixOnset = 0.0f;
    if (CrossPointMixer_glowForCustom(&mixTrail, s_mixTail, &hasTail,
                                      &mixOnset)) {
      trail = mixTrail;
      if (hasTail) {
        tail = s_mixTail;
        tailOnsetMs = mixOnset;
      }
      why = "phosphor mix";
    }
  }
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
    const panelpalette::PresetInfo &info = panelpalette::kPresetInfo[i];
    if (info.preset != preset) continue;
    if (!info.phosphor) break;
    why = info.persistence ? info.persistence : "class only";
    // A cascade phosphor's trail is a different color from its page. Pushed
    // alongside the duration because they are one property of one phosphor.
    tail = info.afterglow;
    break;
  }
  // Logged on EVERY change, including to zero. The first version logged only
  // when it found a phosphor, so "the glow did nothing" and "the glow was never
  // asked for" looked identical from the outside -- which is exactly the state
  // this was stuck in while being debugged. The TAIL is logged for the same
  // reason: build 85's cascade was reported dead from the phone and the log
  // could not say whether the afterglow had been pushed at all.
  SDL_Log("[glow] preset %d -> %.0f ms trail, tail %s, %s (%s)", preset, trail,
          tail ? "yes" : "none", trail > 0.0f ? "emissive" : "reflective", why);
  // A phosphor page emits; an e-ink page reflects. Pushed from the same row as
  // the trail because it is the same claim -- see SimulatorOverlay.
  SimulatorOverlay::setPanelEmissive(trail > 0.0f);
  SimulatorOverlay::setPanelGlow(trail);
  SimulatorOverlay::setPanelGlowTail(tail, tailOnsetMs);
}

// Cheap and edge-triggered, like every other poll here: reading an integer out
// of NSUserDefaults every frame is fine, pushing it every frame is not -- the
// setter is what the render path reads.
// HARD SET, not a setting (owner 2026-08-22: "hard set beam paint to 55ms,
// remove ios setting"). 55 ms is the shipped sweep now -- between the 33 ms
// that is barely visible and the 67 ms that shipped, tuned on device. The
// desktop keeps CROSSPOINT_SIM_BEAM_MS for QA sweeps, which setBeamPaint
// still honors; the phone has no dial.
void pollBeamPaint() {
  static bool s_applied = false;
  if (s_applied) return;
  s_applied = true;
  constexpr float kBeamPaintMs = 55.0f;
  SDL_Log("[beam] %.0f ms sweep (fixed)", kBeamPaintMs);
  SimulatorOverlay::setBeamPaint(kBeamPaintMs);
}

// Same edge-triggered shape as the others: read cheaply every frame, push only
// on change, because the setter is what the render path reads.
void pollPageFade() {
  static int s_applied = -1;
  const int secs = CrossPointPrefs_pageFadeSeconds();
  if (secs == s_applied) return;
  s_applied = secs;
  SDL_Log("[fade] page fade %d s", secs);
  SimulatorOverlay::setPageFade(static_cast<float>(secs) * 1000.0f);
}

// How far that fade goes. Same edge-triggered shape; separate from the poll
// above because the two settings are independently chosen and either can change
// without the other.
void pollPageFadeDepth() {
  static int s_applied = -1;
  const int pct = CrossPointPrefs_pageFadeDepthPercent();
  if (pct == s_applied) return;
  s_applied = pct;
  SDL_Log("[fade] page fade depth %d%% of the legible floor%s", pct,
          pct == 0 ? " (fully transparent)" : "");
  SimulatorOverlay::setPageFadeDepth(pct);
}

void pollPresentFlash() {
  static int s_applied = -1;
  const int on = CrossPointPrefs_presentFlash();
  if (on == s_applied) return;
  s_applied = on;
  SDL_Log("[flash] page-turn flash %s", on ? "ON (the 1-bit pass lands first)"
                                           : "off (composed frames only)");
  SimulatorOverlay::setPresentFlash(on != 0);
}

void pollPhosphorGrain() {
  static int s_strength = -1;
  static int s_coverage = -1;
  static int s_cells = -1;
  static int s_depth = -1;
  // Reads the ACTIVE appearance's value, so the poll's own comparison below
  // repaints on a light/dark flip as well as on a settings change -- the two
  // arrive by different routes and both have to land.
  const int strength = CrossPointPrefs_phosphorGrainPercent(g_dark ? 1 : 0);
  const int coverage = CrossPointPrefs_phosphorGrainCoverage();
  const int cells = phosphorgrain::kMottleCellsDefault;
  const int depth = CrossPointPrefs_phosphorGrainMottleDepth();
  if (strength == s_strength && coverage == s_coverage && cells == s_cells &&
      depth == s_depth)
    return;
  s_strength = strength;
  s_coverage = coverage;
  s_cells = cells;
  s_depth = depth;
  static const char *const kCoverageNames[] = {"even", "vignette", "mottled",
                                               "vignette+mottled"};
  SDL_Log("[grain] screen grain %d%% of realistic, coverage %s, blotches %d x %.2f",
          strength, kCoverageNames[coverage >= 0 && coverage < 4 ? coverage : 0],
          cells, depth / 100.0);
  SimulatorOverlay::setPhosphorGrain(strength, coverage, cells, depth);
}

// THE 2026-08-22 DOCTRINE DIALS. Same edge-triggered shape as the polls
// around them: letterpress is the light page's surface, scanlines the dark
// one's, and HalDisplay itself gates each on the live appearance and skips
// the grain while its mode's dial is on -- so these only carry the numbers.
void pollLetterpress() {
  static int s_applied = -1;
  const int pct = CrossPointPrefs_letterpressPercent();
  if (pct == s_applied) return;
  s_applied = pct;
  SDL_Log("[letterpress] %d%% of standard%s", pct,
          pct == 0 ? " (off)" : " (light pages only)");
  SimulatorOverlay::setLetterpress(pct);
}

// THE SHEET'S ROUGHNESS, from the stored paper selection (owner order
// 2026-08-22: "be sure to be adding the existing noise treatment to it"). The
// picker pushes this the moment a finger moves, so the poll is here for the
// launch seed and for any path that writes the keys without going through the
// picker -- an edge-triggered read costs a defaults lookup per frame and the
// alternative is a sheet that wears the reference stock's tooth until someone
// opens the modal.
void pollPaperTooth() {
  static uint32_t s_applied = 0;
  static bool s_seeded = false;
  const uint32_t sig = CrossPointInkPicker_paperDialSignature();
  if (s_seeded && sig == s_applied) return;
  s_applied = sig;
  s_seeded = true;
  // The picker logs the whole composition -- it is the one place that knows
  // every dial, and duplicating the read here is the shape that lets the log
  // and the applied values drift apart.
  CrossPointInkPicker_pushPaperDials();
}

// Intensity, pitch size AND bloom, edge-triggered on the TRIPLE: the last two
// are only meaningful with the intensity that renders them, and separate
// caches would let a size or bloom change alone go unapplied until the next
// intensity change.
void pollScanlines() {
  static int s_applied = -1;
  static int s_appliedSize = -1;
  static int s_appliedBloom = -1;
  const int pct = CrossPointPrefs_scanlinesPercent();
  const int size = CrossPointPrefs_scanlineSizePercent();
  const int bloom = CrossPointPrefs_scanlineBloomPercent();
  if (pct == s_applied && size == s_appliedSize && bloom == s_appliedBloom)
    return;
  s_applied = pct;
  s_appliedSize = size;
  s_appliedBloom = bloom;
  SDL_Log("[scanlines] %d%% of standard, pitch %d%% of the row lattice, "
          "bloom %d%%%s",
          pct, size, bloom, pct == 0 ? " (off)" : " (dark pages only)");
  SimulatorOverlay::setScanlines(pct);
  SimulatorOverlay::setScanlineSize(size);
  SimulatorOverlay::setScanlineBloom(bloom);
}

// CORNER DEFOCUS and the POWER-OFF COLLAPSE, the two 2026-08-23 dark-mode
// items. Frozen and Settings-backed respectively, but both are polled the same
// way: the toggle can move in Settings.app while the app is foregrounded, and
// the frozen one still needs its one push. Edge-triggered on the pair, the
// scanline poll's shape.
//
// SHOW-THROUGH IS NOT HERE. It is a paper dial, so it rides
// CrossPointInkPicker_pushPaperDials with the tooth, the formation and the
// wires -- the stock's own factor has to multiply into it, and the picker is
// the one place that knows which stock is chosen.
void pollDarkSurfaceItems() {
  static int s_defocus = -1;
  static int s_collapse = -1;
  const int defocus = CrossPointPrefs_cornerDefocusPercent();
  const int collapse = CrossPointPrefs_powerOffCollapse();
  if (defocus == s_defocus && collapse == s_collapse) return;
  s_defocus = defocus;
  s_collapse = collapse;
  SDL_Log("[crt] corner defocus %d%%%s, power-off collapse %s", defocus,
          defocus == 0 ? " (off)" : " (dark pages only)",
          collapse ? "ON -- the glass stays dark through sleep" : "off");
  SimulatorOverlay::setCornerDefocus(defocus);
  SimulatorOverlay::setPowerOffCollapse(collapse != 0);
}

void pollPanelPalette() {
  const panelpalette::Palette panel = currentPanel(g_dark);
  if (packPanel(panel) == g_appliedPanel) return;
  applyPanel(panel);
  SimulatorOverlay::requestPresent();

  // ...AND RE-RENDER, for the same reason applyTheme does it on an appearance
  // change: requestPresent only pushes the framebuffer that already exists.
  // Anything the firmware DREW using a value this changed is still the old
  // pixels -- the palette picker's own preview row and the Settings screen it
  // sits on are drawn by the firmware, not by us, and a page whose grays were
  // dithered for the previous pair keeps that dither until something redraws
  // it. Owner 2026-08-18: "refresh page on events like page color change."
  //
  // Deferred, not immediate: it sets a flag the activity manager reads at the
  // end of its loop, so it is safe from this thread and safe before any
  // activity exists.
  crosspointRequestRender();

  // THE STORED PRESET IS NO LONGER PART OF THE ANSWER, so it is no longer
  // logged: since 2026-08-24 both pages are frozen (src/FrozenPage.h) and
  // panelStoreFromPrefs consults NSUserDefaults for nothing. Printing the
  // stored integer beside tones it did not decide is exactly the kind of log
  // line that costs an investigation.
  SDL_Log("[harness] panel palette (%s) -> frozen, ink %02X%02X%02X, "
          "paper %02X%02X%02X",
          g_dark ? "dark" : "light", panel.ink[0], panel.ink[1], panel.ink[2],
          panel.paper[0], panel.paper[1], panel.paper[2]);
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
// Named for the foreground case it was measured against; it now also covers a
// window SIZE change, which has the identical failure and no measurements of
// its own. Reusing the measured budget beats inventing a second one.
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

// THE PAGE'S ROUNDED CORNERS START BELOW THE DYNAMIC ISLAND.
//
// The field is cleared edge to edge (HalDisplay's SDL_RenderClear), so on a
// pale page the Island sat as a black pill in a white field with nothing
// around it -- a hole punched above the page, which is exactly how the owner
// described it (2026-08-17: "there's not a distracting hole above the panel").
//
// The fix is one band and two fillets: fill from y=0 down to the reserved top
// inset in BLACK, the tone the Island itself renders, then knock the field's
// two upper corners out to that same black. The Island then sits in solid
// ground instead of in a field, and the page's card begins below it with its
// own rounded corners -- the screen's corners, moved down.
//
// PURE BLACK, not the field and not a palette tone. The point is that the
// Island stops being visible as a separate shape, and the Island is #000000.
// In dark mode the field is 121212-ish, so the band still reads as a distinct
// card edge, which is the same thing the owner asked for in the other polarity.
//
// THE BAND'S BOTTOM IS THE SAFE AREA TOP (kCardTop in layoutPad), so it is
// guaranteed to clear the cut-out without measuring it: the safe area top is
// the system's own promise to clear the Island. No API reports the Island's
// frame (docs/ios-dynamic-island.md), and this does not need one.
//
// It is NOT the page's top inset. Since 2026-08-18 the page sits a paper margin
// lower than the band's bottom, so the corners this rounds are the PAPER CARD's
// -- the field the page floats in -- and the page's own top edge is below them.
//
// THE RADIUS is asked of UIKit -- CrossPointAppearance_displayCornerRadius,
// which resolves a container-concentric corner against the window and so lands
// on the display's own radius, public API only. kCornerFallback covers a probe
// that answers 0: it is the radius of the phones this app is built for, and an
// approximate corner reads far better here than a square one.
// The paper card's corner radius, both pairs. On the 8 pt grid the pad aligns
// to, and deliberately ONE number: the top and bottom pairs sit on the same
// rectangle, so any difference between them is visible precisely there.
constexpr float kPaperCornerPt = 8.0f;

// CROSSPOINT_SIM_IPAD_CORNER_RADIUS_UNIT_DIV -- TEMPORARY QA hatch,
// 2026-08-30, same shape as CROSSPOINT_SIM_IPAD_PAPER_GAP_UNIT_DIV in
// paintPad (and CROSSPOINT_SIM_GRAIN_SEED elsewhere in this file): unset is a
// strict no-op -- the shipped tablet divisor (16) or the phone's (2) applies
// exactly as if this hatch did not exist. Tablet only; read once, cached for
// the life of the process, so ONE build sweeps every variant across many
// launches rather than a rebuild per divisor (owner, 2026-08-30: "the owner
// has asked for an HTML page of different corner radii so he can pick one by
// eye, rather than taking unit/16 on faith").
//
// The value names the DENOMINATOR n in radius = unit/n (unit is
// g_paperGapPx on the tablet path). A value <= 0 (including the literal
// "0") requests the degenerate "squared off" case -- radius 0 -- which is
// worth seeing as the other end of the sweep, not an error: parsed as a
// request rather than rejected, and handled by the caller as "no curve",
// never as "no override".
bool tabletRadiusDivisorOverride(float *outDivisor) {
  static bool s_read = false;
  static bool s_has = false;
  static float s_div = 0.0f;
  if (!s_read) {
    s_read = true;
    if (const char *e =
            std::getenv("CROSSPOINT_SIM_IPAD_CORNER_RADIUS_UNIT_DIV")) {
      double v = 0.0;
      if (std::sscanf(e, "%lf", &v) == 1) {
        s_has = true;
        s_div = static_cast<float>(v);
      }
    }
  }
  if (s_has) *outDivisor = s_div;
  return s_has;
}

// One shared answer for "what does THIS platform divide the circle module
// by to get the corner radius" -- used by both paintTopBezel and
// paintBottomFillets so the top and bottom pairs cannot answer differently
// (same reasoning as kPaperCornerPt above: one rectangle, one radius). 16 on
// tablet (owner, 2026-08-29: "change the corner radius rounding to be 1/16
// of unit" -- REPLACING the 2026-08-22 identity, radius = half the module's
// diameter, i.e. divisor 2, for the tablet path specifically), unchanged at
// 2 on the phone, whose own circle (the paper-to-ink gap, set in layoutPad's
// zen block) this ruling does not touch. The QA hatch above overrides the
// tablet's 16 only; a hatch value <= 0 signals "squared off" (radius 0)
// rather than "no override" -- see the two call sites for how that is told
// apart from an unset hatch.
float cornerRadiusDivisorFor(bool isPad) {
  float divisor = isPad ? 16.0f : 2.0f;
  if (isPad) {
    float override_ = 0.0f;
    if (tabletRadiusDivisorOverride(&override_)) divisor = override_;
  }
  return divisor;
}

// THE TABLET'S CORNER RADIUS: four cells of the 8 pt grid (owner, 2026-08-30,
// "64 wins", picked by eye off a rendered sweep of every radius between 50 and
// 100 px that is commensurate with the paper's own geometry).
//
// EXPRESSED IN GRID CELLS, NOT AS A DIVISOR OF THE MODULE, and that is the
// substantive part. 64 px is what unit/6.09375 happens to produce on an iPad
// Pro 13, where the module measures 390 px -- an arithmetic accident of one
// device's layout. The property the owner actually chose is visible in the
// sweep table: 64 is FOUR CELLS of the 16 px (8 pt) grid the pad aligns to.
// Cells survive a different module; a fractional divisor does not.
//
// The 2026-08-29 "1/16 of unit" ruling is superseded for the tablet, not
// contradicted: it asked for a smaller corner than the old half-module and
// this is smaller still on the reference device (64 px against 195). The
// divisor path stays live for the phone and for the QA hatch.
//
// Returns < 0 when this platform has no cell answer, so the caller keeps the
// module/divisor path rather than being handed a sentinel it must decode.
constexpr float kPadCornerCells = 4.0f;
float padCornerRadiusPx(bool isPad) {
  if (!isPad) return -1.0f;
  float unused = 0.0f;
  // The QA hatch still wins on the tablet: a sweep asks for module/n, and a
  // build that answered 64 px to every divisor could not sweep at all.
  if (tabletRadiusDivisorOverride(&unused)) return -1.0f;
  return kPadCornerCells * kPaperCornerPt * g_ptScale;
}

// `paperX`/`paperW`: where the paper's own left/right edges are, for the
// corner cut only -- NOT the band fill, which always covers the full output
// width (above the paper it is black regardless of any horizontal margin).
// Phone (and the pre-2026-08-29 tablet) pass 0/outW, the screen's own edges,
// unchanged. The tablet's horizontal margin (added the same day as this
// comment, see the "SQUARE MODULE, HORIZONTAL" block in paintPad) passes the
// paper's actual inset edges instead, so the rounded corner lands where the
// paper now really starts rather than where the glass does.
void paintTopBezel(SDL_Renderer *r, int outW, float paperX, float paperW) {
  const float bandH = SDL_floorf(g_topBezelPx);
  if (bandH <= 0.0f || outW <= 0 || paperW <= 0.0f) return;

  // 8 pt -- THE SAME RADIUS THE BOTTOM PAIR USES (owner ruling 2026-08-20:
  // "use the bottom corner radius on the top of the paper too").
  //
  // This replaces the display's own radius, which UIKit reports as ~55 pt and
  // which used to be asked for here so the card's corners ran with the glass.
  // They are one rectangle: a 165 px curve at the top against a 24 px curve at
  // the bottom does not read as a sheet of paper, it reads as two different
  // objects. Matching them is what makes it a card. The probe
  // (CrossPointAppearance_displayCornerRadius) stays available for anything
  // that genuinely needs the glass radius; nothing does today.
  // The radius is the module's, when the placement has published one; the 8 pt
  // constant remains the fallback for the pre-first-placement frames only.
  //
  // NOT GATED ON ZEN (owner 2026-08-23: "make top corners of not zen mode
  // match top corner radius of zen mode"). The gate used to be
  // `g_zen && g_paperGapPx > 0`, so the same card was struck with a 106 px
  // curve in zen and a 24 px one out of it -- two different objects on one
  // screen, which is the same complaint the 2026-08-20 ruling fixed between
  // the top and bottom pairs. The module is mode-independent by construction:
  // layoutPad publishes g_paperGapPx from the card top, the panel height and
  // the firmware's ink insets, none of which zen changes (the no-resize
  // ruling), so the two modes read one number rather than agreeing by
  // coincidence. Reading it here changes no geometry -- the fit box, the band
  // and the shift are all decided before this paints.
  // THE DIVISOR FORKS BY PLATFORM, 2026-08-29. The 2026-08-22 identity
  // (radius = half the module's diameter) still holds on the PHONE -- its
  // own circle, the paper-to-ink gap, untouched. On the TABLET the owner
  // replaced it: "change the corner radius rounding to be 1/16 of unit."
  // `cornerRadiusDivisorFor()` decides which divisor applies to whichever
  // circle `g_paperGapPx` holds (see that global's own comment for which
  // platform means which circle) -- kept as one shared lookup (including the
  // 2026-08-30 QA sweep hatch) so this painter and paintBottomFillets cannot
  // answer differently.
  static const bool s_isPad = CrossPointAppearance_isPad() == 1;
  const float kRadiusDivisor = cornerRadiusDivisorFor(s_isPad);
  static float s_radiusPx = -1.0f;
  static float s_radiusFrom = -1.0f;
  const float module = g_paperGapPx > 0.0f ? g_paperGapPx : 0.0f;
  const float padPx = padCornerRadiusPx(s_isPad);
  if (s_radiusPx < 0.0f || module != s_radiusFrom) {
    s_radiusFrom = module;
    // padPx >= 0: the tablet's four-cell answer (see padCornerRadiusPx), which
    // is not derived from the module at all. Below that, the module paths:
    // module <= 0 is pre-first-layout, the 8 pt fallback; module > 0 with
    // kRadiusDivisor <= 0 is the QA hatch's explicit "squared off" request --
    // radius 0, a real answer, not a missing one; otherwise the ordinary
    // module/divisor curve.
    if (padPx >= 0.0f) {
      s_radiusPx = padPx;
    } else if (module <= 0.0f) {
      s_radiusPx = kPaperCornerPt * g_ptScale;
    } else if (kRadiusDivisor <= 0.0f) {
      s_radiusPx = 0.0f;
    } else {
      s_radiusPx = module / kRadiusDivisor;
    }
    // "the circle module" rather than naming one gap: it is the paper-to-ink
    // gap on the phone (layoutPad's zen block) and the outer 1-unit band
    // above the card on the tablet (layoutPadTablet, corrected 2026-08-29) --
    // one identity through 2026-08-22, forked by platform since 2026-08-29
    // (see kRadiusDivisor above).
    SDL_Log("[bezel] band %.0f px, corner %.1f px (%s, /%.1f)", bandH,
            s_radiusPx,
            module <= 0.0f ? "8 pt fallback" : "circle module",
            kRadiusDivisor);
  }

  SDL_SetRenderDrawColor(r, 0, 0, 0, 255);
  fillRect(r, 0.0f, 0.0f, static_cast<float>(outW), bandH);

  // The two fillets: the sliver OUTSIDE each top corner arc, filled to the same
  // black. Same scanline arithmetic as fillRoundRect, inverted -- fillRoundRect
  // paints the inside of the arc, this paints what it leaves over.
  // A SQUIRCLE, NOT A CIRCLE, and the exponent is measured off Apple's own
  // display mask rather than taken from folklore.
  //
  // Every simulator device type ships the mask as a vector PDF (named by
  // `framebufferMask` in its profile.plist). Flattening the iPhone Air's path
  // and fitting |u|^n + |v|^n = 1 to the corner gives an extent of 87.45 x
  // 88.37 pt and **n = 2.8**, mean residual 0.014 -- a close fit, and a long
  // way from the circle this used to draw. The commonly repeated "iOS squircles
  // are n = 5" does not match this mask at all; 5 was tried and fits far worse.
  //
  // The difference is not subtle where it matters. Inset from the page's edge
  // at a given depth, this curve against the circle it replaces:
  //
  //     depth   squircle   circle
  //       1 pt    62.05     44.56
  //       4 pt    46.24     34.41
  //      16 pt    22.84     16.22
  //      50 pt     3.12      0.23
  //
  // The circle pulled in too fast and left the page's corner cutting across the
  // glass's curve instead of running with it.
  //
  // The EXTENT stays whatever s_radiusPx resolved to: this changes the shape of
  // the page's corner, not its size, which is what "shaped properly" asked for.
  constexpr float kCornerExponent = 2.8f;
  const float rad = SDL_min(s_radiusPx, paperW / 2.0f);
  const int rows = static_cast<int>(rad);
  for (int i = 0; i < rows; i++) {
    const float y = static_cast<float>(i);
    // v: how much of the corner's depth is still ahead, 1 at the top edge and
    // 0 where the curve meets the straight side.
    const float v = (rad - y) / rad;
    const float u = SDL_powf(SDL_max(0.0f, 1.0f - SDL_powf(v, kCornerExponent)),
                             1.0f / kCornerExponent);
    const float inset = rad * (1.0f - u);
    if (inset <= 0.0f) continue;
    fillRect(r, paperX, bandH + y, inset, 1.0f);
    fillRect(r, paperX + paperW - inset, bandH + y, inset, 1.0f);
  }
}

// The page's BOTTOM corners, for zen mode. paintTopBezel rounds the top pair
// against the glass; in zen the page ends in open space rather than against the
// pad, so the bottom pair has to be rounded too or the raised page reads as a
// slab with two sharp corners under two soft ones.
//
// Deliberately the same curve as the top: kCornerExponent 2.8, measured off
// Apple's own display mask (the derivation is in paintTopBezel and is not
// repeated). A different radius or a circle here would be visible precisely
// because the two pairs sit on one rectangle.
// The panel's own paper tone -- the page's background, which on a CRT palette is
// nothing like the pad's field. panelpalette resolves the pair; this is its
// light/dark half for the appearance in force.
void setRGBFromPanelPaper(SDL_Renderer *r) {
  // currentPanel() already resolves the pair for the appearance in force, and
  // `paper` is what a fully-white source pixel becomes -- i.e. the page's own
  // background, which is exactly what the strip has to match.
  const panelpalette::Palette pal = currentPanel(g_dark);
  SDL_SetRenderDrawColor(r, pal.paper[0], pal.paper[1], pal.paper[2], 255);
}

void paintBottomFillets(SDL_Renderer *r, int outW, const SDL_FRect &panel,
                       bool intoBlack) {
  if (panel.w <= 0.0f || panel.h <= 0.0f) return;
  constexpr float kCornerExponent = 2.8f;
  // Same module as the top pair -- they are one rectangle (the 2026-08-20
  // ruling that matched them survives; only the number's SOURCE changed).
  // Same platform-forked divisor as paintTopBezel too, as of 2026-08-29: /2
  // on the phone (the 2026-08-22 identity, untouched), /16 on the tablet
  // (owner: "change the corner radius rounding to be 1/16 of unit"), plus
  // the 2026-08-30 QA sweep hatch -- shared through cornerRadiusDivisorFor()
  // rather than kept as a second literal, so the top and bottom pairs cannot
  // drift apart. See the divisor comment in paintTopBezel for the full
  // account.
  static const bool s_isPad = CrossPointAppearance_isPad() == 1;
  const float kRadiusDivisor = cornerRadiusDivisorFor(s_isPad);
  // NOT GATED ON ZEN, for the same reason paintTopBezel stopped being gated on
  // 2026-08-23: the module is mode-independent by construction, and gating one
  // pair and not the other strikes ONE rectangle with two different curves --
  // exactly the complaint the 2026-08-20 ruling fixed between these two
  // painters. The comment above has claimed "they cannot drift apart" since
  // 2026-08-29 while this line still read `g_zen && ...`; they drifted.
  //
  // Measured 2026-08-30, which is how it was caught: outside zen this fell to
  // kPaperCornerPt * scale = 24 px while the top pair drew module/divisor, and
  // it made the QA divisor sweep silently produce three identical 24 px
  // captures for unit/16, unit/4 and unit/2 -- the /16 one agreeing only
  // because 384/16 is also 24.
  const bool hasModule = g_paperGapPx > 0.0f;
  const float padPx = padCornerRadiusPx(s_isPad);
  const float moduleRad = padPx >= 0.0f          ? padPx
                          : !hasModule           ? kPaperCornerPt * g_ptScale
                          : kRadiusDivisor <= 0.0f ? 0.0f
                                                   : g_paperGapPx / kRadiusDivisor;
  const float rad = SDL_min(moduleRad, panel.w / 2.0f);
  // A fillet must be painted in whatever the corner is being cut OUT of: the
  // field normally, black in zen, where the surround below the paper is black by
  // ruling. The wrong one leaves two pale nicks on a dark screen, which reads as
  // a rendering fault rather than as a corner.
  if (intoBlack) {
    SDL_SetRenderDrawColor(r, 0, 0, 0, 255);
  } else {
    const Palette &p = palette();
    setRGB(r, p.field);
  }
  const int rows = static_cast<int>(rad);
  const float bottom = panel.y + panel.h;
  for (int i = 0; i < rows; i++) {
    const float y = static_cast<float>(i);
    // Mirrored: v is 1 at the bottom edge and 0 where the curve meets the side.
    const float v = (rad - y) / rad;
    const float u = SDL_powf(SDL_max(0.0f, 1.0f - SDL_powf(v, kCornerExponent)),
                             1.0f / kCornerExponent);
    const float inset = rad * (1.0f - u);
    if (inset <= 0.0f) continue;
    const float rowY = bottom - 1.0f - y;
    fillRect(r, panel.x, rowY, inset, 1.0f);
    fillRect(r, panel.x + panel.w - inset, rowY, inset, 1.0f);
  }
  (void)outW;
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
// cyclePalette() lived here until 2026-08-20. Owner ruling replaced the
// chip's cycling with the mixer modal (CrossPointPaletteMixer.mm) for both tap
// and hold, so the ring-stepping function is gone with its callers. The 500 ms
// hold threshold went with it.
//
// paintPaletteChip() lived here until 2026-08-24, when the button itself was
// removed ("remove the color button from single finger (not zen) mode ui"). It
// drew a bare unmarked capsule identical to POWER -- which was itself a ruling
// taken three times, the last being "remove color button icon", after versions
// that filled it with the live palette and then added a half-disc to tell it
// apart. Recorded because it is the answer to "should the button get a glyph"
// if it ever comes back: no, and it was asked and answered.

void paintKeyboardChip(SDL_Renderer *r, const Palette &p, float radius,
                       float hairline) {
  if (!gpio.isTextEntryActive()) return;
  const SDL_FRect &c = g_kbChip;
  if (c.w <= 0 || c.h <= 0) return;
  const bool keyboardUp = gpio.isHostKeyboardVisible();

  // THE PAD'S OWN PALETTE, owner instruction 2026-08-17: "match show/hide
  // keyboard button outline with rest of app." This reverses the light-gray
  // rule the chip carried until now -- see ios/PanelPrefs.h, which keeps the
  // superseded reasoning so it is not re-derived and re-applied.
  //
  // `p` is the palette the pad is drawn with and it is now simply used.
  const Palette chip = p;

  // Same stroke-then-face construction as the controls, so it belongs to the
  // pad rather than sitting on top of it.
  setRGB(r, chip.hairline);
  fillRoundRect(r, c, radius);
  setRGB(r, chip.face);
  fillRoundRect(r, {c.x + hairline, c.y + hairline, c.w - 2 * hairline,
                    c.h - 2 * hairline},
                radius - hairline);

  const float glyphH = c.h * 0.52f;
  const float chevH = glyphH * 0.26f;
  const float bodyH = glyphH * 0.56f;
  const float bodyW = bodyH * 1.75f;
  const float cx = c.x + c.w / 2.0f;
  const float top = c.y + (c.h - glyphH) / 2.0f;

  // The chevron, rasterized by COVERAGE. No geometry API, no rotated rect to
  // resample -- the original reasons stand, and this keeps them.
  //
  // WHAT WAS WRONG. It was stacked one-pixel rows with the offset stepping by a
  // whole pixel per row, so every edge was hard: measured off the Metal renderer
  // at iPhone numbers (402x874pt @3x), the chevron came back with exactly two
  // levels, 0 and 255, and nothing in between. That makes it the only
  // unantialiased diagonal on the screen -- the dismiss bar above it, the system
  // keyboard, every SF Symbol beside it are all coverage-antialiased -- and an
  // aliased edge among smooth ones reads as jagged even when the steps are a
  // single device pixel.
  //
  // WHAT IT IS NOT. Not the block-scaling the firmware renderer has at
  // RENDER_SCALE > 1: the overlay is painted with logical presentation dropped
  // (HalDisplay.cpp:960-965), so these coordinates are already real device
  // pixels, and SDL_WINDOW_HIGH_PIXEL_DENSITY (HalDisplay.cpp:571) means the
  // drawable is the native 3x backing store. Nothing here was being upscaled.
  //
  // THE SHAPE IS UNCHANGED, deliberately -- blurring the old boundary would only
  // blur a staircase, since `off` WAS the integer row index. ChevronCoverage.h
  // holds the shape and the argument for it, and tests/chevron_coverage_test.cpp
  // pins that it still antialiases and still has the old extents and weight.
  // Points where the keyboard is about to go. Converged at the top spreading
  // down is "^" (summon); the mirror is "v" (dismiss), which is the glyph iOS
  // puts on its own dismiss key.
  const chevron::Geometry chev{cx, top, chevH,
                               SDL_max(1.0f, SDL_roundf(chevH * 0.42f)),
                               keyboardUp};
  const chevron::Bounds bb = chevron::bounds(chev);

  // Partial coverage needs alpha, and every other painter here draws opaque, so
  // the blend mode is put back rather than left changed for whatever paints next.
  SDL_BlendMode prevBlend = SDL_BLENDMODE_NONE;
  SDL_GetRenderDrawBlendMode(r, &prevBlend);
  SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_BLEND);
  for (int py = bb.y0; py <= bb.y1; py++) {
    // Runs of equal coverage collapse into one rect, which keeps this near the
    // draw-call count of the loop it replaces. It only runs while a text field
    // is open, which is the only time the chip exists at all.
    int runStart = bb.x0;
    int runAlpha = 0;
    for (int px = bb.x0; px <= bb.x1 + 1; px++) {
      const int alpha =
          px > bb.x1 ? 0
                     : static_cast<int>(SDL_lroundf(chevron::coverage(chev, px, py) * 255.0f));
      if (alpha == runAlpha) continue;
      if (runAlpha > 0) {
        SDL_SetRenderDrawColor(r, chip.hairline[0], chip.hairline[1], chip.hairline[2],
                               static_cast<Uint8>(runAlpha));
        fillRect(r, static_cast<float>(runStart), static_cast<float>(py),
                 static_cast<float>(px - runStart), 1);
      }
      runStart = px;
      runAlpha = alpha;
    }
  }
  SDL_SetRenderDrawBlendMode(r, prevBlend);
  setRGB(r, chip.hairline);

  // The keyboard: a solid body with the keys PUNCHED back out in the face
  // tone. Punching rather than stroking each key is what keeps it legible at
  // this size -- outlines this small close up into a gray smear.
  const float bx = cx - bodyW / 2.0f;
  const float by = top + glyphH - bodyH;
  setRGB(r, chip.hairline);
  fillRoundRect(r, {bx, by, bodyW, bodyH}, bodyH * 0.2f);

  setRGB(r, chip.face);
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
    // BEFORE the call, not after. layoutPad clears g_padLaidOut when the zen
    // shift changes, to schedule the one extra pass that consumes the new
    // value; setting true after the call clobbered that request. The clobber
    // was invisible while the panel moved every present (a changed
    // panelBottom re-fires this gate on its own), which is the whole boot
    // convergence -- but the published-insets relayout changes NOTHING this
    // pass (the snapshot holds the old shift, correctly), so the panel does
    // not move, the gate never fires again, and the recomputed shift sat
    // unconsumed forever. That was the stable wrong fixed point.
    g_padLaidOut = true;
    layoutPad(outW, outH);
    s_layoutPanelBottom = panelBottom;
    s_layoutKeyboardPt = keyboardPt;
  }

  // SQUARE MODULE, HORIZONTAL -- superseded twice the same day. First ask
  // (owner, from a render: "right now, it is unusually and incoherently wide
  // (full screen width)... make fit a sensible grid horizontally spaced or
  // based on a square grid with horizontal and vertical," choosing a square
  // module over a screen-tiling grid or an independent 8 pt horizontal grid:
  // "square module is best") shipped the card with a FULL unit's gap to the
  // panel on each side -- measured 115 px card-to-panel gap on an iPad Pro 13
  // portrait (unit=389.3px, card 1286px vs panel 1056px). Second ask, from
  // THAT render, confirmed twice: "there should be less paper... needs to be
  // skinnier. just to be clear." Taken to its limit rather than softened:
  // **THE CARD IS NOW EXACTLY THE PANEL** -- card-to-panel gap 0 px on both
  // axes (vertically it was already 0; the zen paper's own y/h have always
  // equaled the panel's). The screen margin is whatever falls out of that,
  // not something aimed at: (2064-1056)/2 = 504 px portrait on that device.
  //
  // g_paperGapPx (the vertical unit) is UNTOUCHED by this -- it still governs
  // the outer top/bottom band split (layoutPadTablet) and, as of 2026-08-29,
  // the corner radius at unit/16 (paintTopBezel, paintBottomFillets); the
  // horizontal card size no longer reads it at all.
  //
  // Phone's zen paper still bleeds to the glass (tabletMarginPx collapses to
  // 0), untouched -- that is the 2026-08-20 ruling this does NOT reverse; it
  // was measured wrong for a screen this size, not wrong in general.
  static const bool s_isPad = CrossPointAppearance_isPad() == 1;
  float tabletMarginPx = 0.0f;
  if (s_isPad) {
    const float panelWpx =
        static_cast<float>(SimulatorOverlay::panelWidthPx());
    tabletMarginPx =
        SDL_max(0.0f, (static_cast<float>(outW) - panelWpx) / 2.0f);
  }

  // CROSSPOINT_SIM_IPAD_PAPER_GAP_UNIT_DIV -- kept as a study hatch for a
  // NONZERO card-to-panel gap now that zero is the shipped default (this is
  // the mechanism that produced the eight-variant sweep in
  // docs/ipad-layout-2026-08-29.md, all of which the owner's final ruling
  // went past). gapPx = g_paperGapPx / divisor, re-deriving the screen margin
  // from it exactly as before; unset leaves the zero-gap default above
  // untouched. Tablet only; read once, cached.
  if (s_isPad && g_paperGapPx > 0.0f) {
    static float s_gapDiv = 0.0f;
    static bool s_gapDivRead = false;
    if (!s_gapDivRead) {
      s_gapDivRead = true;
      if (const char *e =
              std::getenv("CROSSPOINT_SIM_IPAD_PAPER_GAP_UNIT_DIV")) {
        double v = 0.0;
        if (std::sscanf(e, "%lf", &v) == 1 && v > 0.0)
          s_gapDiv = static_cast<float>(v);
      }
    }
    if (s_gapDiv > 0.0f) {
      const float gapPx = g_paperGapPx / s_gapDiv;
      const float panelWpx =
          static_cast<float>(SimulatorOverlay::panelWidthPx());
      const float cardWpx = panelWpx + 2.0f * gapPx;
      tabletMarginPx =
          SDL_max(0.0f, (static_cast<float>(outW) - cardWpx) / 2.0f);
      SDL_Log("[pad] tablet paper-gap hatch: div=%.2f gap=%.1fpx "
              "panelW=%.0fpx cardW=%.1fpx margin=%.1fpx",
              s_gapDiv, gapPx, panelWpx, cardWpx, tabletMarginPx);
    }
  }

  // After the layout block, because layoutPad is what publishes the band's
  // height, and before the pad, whose controls are all below the page.
  paintTopBezel(r, outW, tabletMarginPx,
                static_cast<float>(outW) - 2.0f * tabletMarginPx);

  // The page's presented rect, for the zen hit-test. Recorded every present,
  // zen or not, so entering zen never waits a frame for geometry.
  g_zenPanel = {static_cast<float>(SimulatorOverlay::panelLeftPx()),
                static_cast<float>(SimulatorOverlay::panelBottomPx() -
                                   SimulatorOverlay::panelHeightPx()),
                static_cast<float>(SimulatorOverlay::panelWidthPx()),
                static_cast<float>(SimulatorOverlay::panelHeightPx())};
  // The presented POSITION, logged on change. HalDisplay's [panel] line only
  // prints when the scale or the output size changes, so a shift-only move --
  // which is the entire zen placement mechanism -- was invisible in every log
  // this was debugged from. A settled layout prints nothing here.
  {
    static SDL_FRect s_lastZenPanel{-1.0f, -1.0f, -1.0f, -1.0f};
    if (g_zenPanel.x != s_lastZenPanel.x || g_zenPanel.y != s_lastZenPanel.y ||
        g_zenPanel.w != s_lastZenPanel.w || g_zenPanel.h != s_lastZenPanel.h) {
      s_lastZenPanel = g_zenPanel;
      SDL_Log("[zen] panel %.0fx%.0f at %.0f,%.0f", g_zenPanel.w, g_zenPanel.h,
              g_zenPanel.x, g_zenPanel.y);
    }
  }

  if (g_zen) {
    // Nothing below the page draws in zen -- no capsules, no chips.
    //
    // THE PAPER ENDS at the old top-rocker line, and everything below it is
    // BLACK (owner ruling 2026-08-19). That is a CONTRACTION of the paper, not
    // an extension: left alone the paper tone runs to the bottom of the screen,
    // because the pad's field matches the page's paper by design -- measured on
    // an iPhone Air, page (215,233,211) against field (215,233,211), no edge
    // anywhere on the screen. Black is what gives the paper an edge to have
    // corners on, and on an OLED it is the darkest a night page can be.
    const SDL_FRect &q = g_zenPanel;
    // THE PAPER IS THE FULL WIDTH OF THE SCREEN ON THE PHONE, not the page's
    // rect. The page is 1056 px wide on a 1260 px screen, and the pad's field
    // is the SAME tone as the page's paper by design (measured 215,233,211
    // against 215,233,211), so what the eye reads as one sheet runs edge to
    // edge. Cutting the corners out of the page's rect put two notches at
    // x=102 and x=1158, mid-field, eight pixels of nothing in the middle of
    // the paper -- which is what the 2026-08-20 screenshot caught. The
    // corners that exist are the SCREEN's.
    //
    // The sheet BLEEDS TO THE GLASS -- it is not a card floating on black
    // (owner ruling 2026-08-20, picked off a side-by-side of live renders).
    // The bounded version cost 204 px of width to margin and read as a smaller
    // object on a screen, where this reads as the screen being paper. STILL
    // TRUE ON THE PHONE (tabletMarginPx is 0 there, unchanged).
    //
    // THE TABLET IS THE OPPOSITE CALL, same day (owner, from a render): "it is
    // unusually and incoherently wide (full screen width)... make fit a
    // sensible grid." The 2026-08-20 reasoning was measured on an iPhone,
    // where 204 px is nearly a fifth of the width; the identical full-bleed
    // sheet on an iPad Pro reads as an unbounded slab rather than a page, per
    // the owner's own screenshot. `tabletMarginPx` (computed above -- as of
    // 2026-08-29, directly from the panel's own width, zero card-to-panel
    // gap, no longer from `g_paperGapPx`) insets the paper on tablet only; it
    // is 0 on phone, so this collapses to the line above exactly.
    g_zenPaper = {tabletMarginPx, q.y,
                 static_cast<float>(outW) - 2.0f * tabletMarginPx, q.h};
    const float line = g_zenRowTopPx > 0.0f ? g_zenRowTopPx : q.y + q.h;

    SDL_SetRenderDrawColor(r, 0, 0, 0, 255);
    const SDL_FRect below{0.0f, line, static_cast<float>(outW),
                          static_cast<float>(outH) - line};
    if (below.h > 0.0f) SDL_RenderFillRect(r, &below);

    // THE SIDE MARGINS THEMSELVES: with the paper now narrower than the
    // screen on tablet, the strip left of paperX and right of paperX+paperW,
    // for the paper's own row (q.y..line), is no longer covered by anything
    // -- `below` only reaches downward, and the SDL_RenderClear at the top of
    // this present already painted that strip the PAPER'S tone, not black.
    // Zero cost on phone: tabletMarginPx == 0 collapses both rects to zero
    // width and SDL_RenderFillRect is a no-op on them.
    if (tabletMarginPx > 0.0f && line > q.y) {
      const SDL_FRect leftMargin{0.0f, q.y, tabletMarginPx, line - q.y};
      const SDL_FRect rightMargin{static_cast<float>(outW) - tabletMarginPx,
                                  q.y, tabletMarginPx, line - q.y};
      SDL_RenderFillRect(r, &leftMargin);
      SDL_RenderFillRect(r, &rightMargin);
    }

    // THE PAPER ENDS AT THE LINE, in both directions. This is the whole rect
    // the corners are cut out of, so it has to follow the line even when the
    // line is ABOVE the page's own bottom edge -- the contraction case, which
    // is the usual one. Leaving it at the panel's height put the fillets down
    // inside the black band where nothing could see them, and what the eye read
    // as the paper's edge was the band's straight top: a slab with two sharp
    // bottom corners, which is the bug in the 2026-08-20 screenshot.
    g_zenPaper.h = SDL_max(0.0f, line - q.y);

    // Only when the line falls BELOW the page does paper have to be painted
    // in: the strip between the page's bottom edge and the line. The PAGE is
    // never resized -- its fit is identical in both modes.
    if (line > q.y + q.h) {
      const SDL_FRect strip{g_zenPaper.x, q.y + q.h, g_zenPaper.w,
                           line - (q.y + q.h)};
      setRGBFromPanelPaper(r);
      SDL_RenderFillRect(r, &strip);
    }

    // Top corners belong to paintTopBezel; the bottom pair is cut out of black.
    paintBottomFillets(r, outW, g_zenPaper, /*intoBlack=*/true);
    return;
  }

  const Palette &p = palette();
  const float S = g_ptScale;
  // 8 pt — the 8 pt grid the pad aligns to. CrossPointKeyboardBar.mm already
  // uses cornerRadius = 8 with that exact comment. 12 pt was the old value;
  // it was not on any square grid (12 / 8 = 1.5).
  const float radius = 8.0f * S;

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
  // TWO pairs, and the dimension must say two. It said three while listing two
  // -- left over from when Up|Down was the third -- so the trailing row
  // zero-initialised to {0, 0}, and kPadBack is 0. That painted a whole extra
  // capsule over the Back half of the left rocker, with a divider tick at that
  // half's own edge: the rocker's line stopped looking centred, which is
  // exactly what it looked like on the phone. Sized from the initialiser now,
  // so removing a pair can never leave a phantom one behind again.
  const int pairs[][2] = {
      {kPadBack, kPadConfirm}, {kPadLeft, kPadRight}, {kPadUp, kPadDown}};
  bool inPair[kPadCount] = {};
  for (const auto &pr : pairs) {
    const SDL_FRect &a = g_pad[pr[0]].rect;
    const SDL_FRect &b = g_pad[pr[1]].rect;
    inPair[pr[0]] = inPair[pr[1]] = true;

    // A RETIRED OR NOT-YET-LAID-OUT PAIR DRAWS NOTHING -- the same guard the
    // single-button loop below has always had, which this loop did not.
    //
    // A retired slot has a zero rect (the side-rocker ruling: hasEdgeSideButtons
    // is false on X4, and g_padLaidOut is cleared on every size change, so the
    // rects are momentarily zero after a resize as well). The single loop skips
    // those. This one went on to compute a union and two inner halves from
    // them, and `a.w - hairline` on a zero rect is NEGATIVE -- as is
    // `a.h - 2 * hairline` -- so what reached SDL_RenderFillRect was a
    // negative-extent rect, while fillHalf's `patch` kept a POSITIVE width
    // beside a negative height. That is a fill whose result is the renderer's
    // business rather than ours, at the origin corner of the pad.
    //
    // Not confirmed as the cause of S-026 (a stray flash on the bottom-right
    // rocker) -- that is still unreproduced -- but it is a defect on its own
    // terms, it is in the exact code that has already produced one phantom
    // capsule (see the pairs-table note above), and the guard costs a compare.
    if (a.w <= 0.0f || a.h <= 0.0f || b.w <= 0.0f || b.h <= 0.0f) continue;

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
    // A retired slot has a zero rect and draws nothing. See the side-rocker
    // ruling in the layout functions.
    if (b.rect.w <= 0.0f || b.rect.h <= 0.0f) continue;
    setRGB(r, p.hairline);
    fillRoundRect(r, b.rect, radius);

    const SDL_FRect inner{b.rect.x + hairline, b.rect.y + hairline,
                          b.rect.w - 2 * hairline, b.rect.h - 2 * hairline};
    setRGB(r, g_core.isDown(i) ? p.faceDown : p.face);
    fillRoundRect(r, inner, radius - hairline);
  }

  paintKeyboardChip(r, p, radius, hairline);
}

// hitPaletteChip() went with the button on 2026-08-24. The keyboard chip's own
// test below is a different control and stays -- see the note at g_kbChip.
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

// Read-aloud / chip tap candidate: a finger that landed on NO pad slot may
// become a word tap or a chip tap. Down records it, dragging past the slop
// cancels it (a drag must not start speech), a clean lift hands the DOWN
// coordinates to the adapter (CrossPointReadAloud_tapAtScreen rejects
// anything outside the panel or off a word). No timers: a tap is down + up
// without movement, however long the hold — the pad's own design, and PadCore
// itself stays untouched. The arm/spoil lifecycle lives in TapCandidate.h
// (pure, tests/tap_candidate_test.cpp) because the 2026-08-21 audit found two
// silent failures in the inline version: a candidate latched forever by the
// zen toggle's early break (finding #1), and a candidate firing while more
// fingers were down, giving one gesture two effects (finding #3).
tapcand::Candidate g_tapCand;

// THE THREE-FINGER TAP, which is the only way in and out of zen, is a native
// UITapGestureRecognizer now (owner 2026-08-22: "be sure to swap 3 finger tap
// to apple"), attached in BOTH modes — it has to fire while zen is OFF to get
// in. CrossPointZenRecognizers.mm owns it and calls
// CrossPointZen_toggleFromRecognizer() below; the pure SDL detector it
// replaces (ZenGesture.h, archived 2026-08-22) is gone with the rest of the
// hand-rolled multi-finger recognition. The old page-landing constraint
// (last lift ON the page) retired with the detector.
float g_zenLastX = 0.0f, g_zenLastY = 0.0f;

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

// THE FLICKER FIX (owner bug report 2026-08-29, verbatim: "less flickering
// of layout when zen mode is enabled/disabled").
//
// Diagnosed by reading the present pipeline (docs/zen-mode.md has the
// mechanism and the device-log evidence): a `[zen] shift ...px` line and the
// `[zen] on band=...` summary land inside the SAME draw callback that
// HalDisplay had already fit the panel for, which is only possible if the
// fit used the OLD bottomInset/topInset while the callback was busy
// computing the NEW ones for the NEXT present. layoutPad()'s own
// draw-time call (from paintPad, itself HalDisplay::presentIfNeeded's
// overlay callback) runs AFTER that present's panel fit, so whatever it
// publishes via SimulatorOverlay::setBottomInset/setTopInset cannot reach
// the glass until the FOLLOWING present -- one full present too late. On
// that first present the CHROME (rows, bezel, keyboard chip) is drawn from
// THIS pass's freshly computed zen-target geometry while the PANEL (the
// actual page image) is still sitting at last pass's fit: a visibly
// mismatched frame, corrected a moment later by the present the callback
// just requested. That is the flicker.
//
// The fix is not to make the two-pass convergence faster; it is to stop the
// unconverged frame from reaching a present at all. Calling layoutPad()
// HERE -- synchronously, from the toggle/settings/inset-publish sites,
// BEFORE they ask for a present -- publishes the converged bottomInset and
// topInset a step earlier than the draw callback ever could, so the very
// next presentIfNeeded() call fits the panel from numbers that already
// match what the chrome is about to draw. layoutPad() is safe to call this
// way: it does no SDL drawing of its own (no SDL_Renderer* parameter at
// all), only geometry math and state publishing, and its DERIVED inputs
// (panelHeightPx(), g_cardTopPx, the published reader ink insets) are the
// same read-only values available from any call site or thread the main
// thread -- the shift target it computes does not depend on which present
// asked for it.
//
// This also depends on layoutPad's own intra-call ordering: the shift
// consumption (setBottomInset/setTopInset via g_zenShiftThisPass) now runs
// AFTER `want` has updated g_zenPanelShiftPx for THIS SAME call, not before
// it (see the comments at both ends of that move, in layoutPad). Without
// that reorder, THIS pre-warm call would itself publish the STALE shift on
// its first invocation and only correct it on a second call -- pre-warming
// alone does not help if the thing being pre-warmed is still one call
// behind its own answer.
void zenPreWarmLayout() {
  float outW = 0.0f, outH = 0.0f;
  if (windowPixelSize(g_windowId, &outW, &outH))
    layoutPad(static_cast<int>(outW), static_cast<int>(outH));
}

bool SDLCALL padWatch(void * /*userdata*/, SDL_Event *e) {
  float outW = 0, outH = 0;

  switch (e->type) {
    case SDL_EVENT_FINGER_DOWN: {
      // With the mixer sheet up, UIKit passes touches outside the sheet
      // through to this view (pageSheet, undimmed medium detent — audit #6).
      // The sheet is the only control surface then: feed NOTHING. Fingers
      // never enter the trackers, so their lifts are no-ops below.
      if (CrossPointMixer_isPresented() || CrossPointInkPicker_isPresented())
        break;
      if (!windowPixelSize(e->tfinger.windowID, &outW, &outH)) break;
      const float fx = e->tfinger.x * outW, fy = e->tfinger.y * outH;

      g_windowId = e->tfinger.windowID;
      // Fed in EVERY mode, acted on only in zen: a gesture in flight when the
      // three-finger toggle flips g_zen must not arrive at a half-seen
      // classifier.
      const bool firstFinger = g_zenVerbs.activeFingers() == 0;
      g_zenVerbs.fingerDown(e->tfinger.fingerID, fx, fy, SDL_GetTicks());
      // The first finger of the gesture is the one the classifier can answer
      // Verb::Down for; a later one only ever spoils it.
      if (firstFinger) g_zenTapDownY = fy;
      g_zenLastX = fx;
      g_zenLastY = fy;

      // In zen the pad does not exist: no slots, no hit test, no PadCore.
      // Every touch is either the deliberate tap or a native recognizer's
      // gesture (the 3-finger toggle included).
      if (g_zen) break;

      // A SECOND concurrent finger means this is a gesture (the 3-finger zen
      // toggle, or nothing), not a control press (audit #2/#3). Spoil the tap
      // candidate, release any held capsule NOW — so a thumb resting on
      // POWER during a 3-finger tap cannot accumulate a long-press span and
      // sleep the device — and press nothing for this finger. Presses the
      // FIRST finger already fired before a second landed cannot be recalled:
      // injectButtonDown edges drain into the firmware within the same
      // frame's update(), so suppression here is prospective, not
      // retroactive.
      const int concurrent = g_zenVerbs.activeFingers();
      if (concurrent > 1) {
        g_tapCand.spoil();
        applyActions(g_core.reset());
        break;
      }

      const int hit = padHitTest(fx, fy);
      g_tapCand.fingerDown(e->tfinger.fingerID, fx, fy, SDL_GetTicks(),
                           hit >= 0, concurrent);
      applyActions(g_core.fingerDown(hit >= 0 ? hit : PadCore::kNoSlot,
                                     e->tfinger.fingerID));
      break;
    }

    case SDL_EVENT_FINGER_MOTION: {
      if (windowPixelSize(e->tfinger.windowID, &outW, &outH))
        g_zenVerbs.fingerMove(e->tfinger.fingerID, e->tfinger.x * outW,
                              e->tfinger.y * outH);
      // A tap candidate that drags past the slop is a swipe, not a tap.
      if (windowPixelSize(e->tfinger.windowID, &outW, &outH))
        g_tapCand.fingerMove(e->tfinger.fingerID, e->tfinger.x * outW,
                             e->tfinger.y * outH, 12.0f * g_ptScale);

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
    case SDL_EVENT_FINGER_CANCELED: {
      if (windowPixelSize(e->tfinger.windowID, &outW, &outH)) {
        g_zenLastX = e->tfinger.x * outW;
        g_zenLastY = e->tfinger.y * outH;
      }
      {
        const bool cancelled = e->type == SDL_EVENT_FINGER_CANCELED;
        const bool zenBefore = g_zen;

        // The classifier resolves on the last lift, whatever happens. One
        // owner per gesture: the 3-finger toggle and every moving gesture are
        // native recognizers now (CrossPointZenRecognizers.mm), and the
        // classifier answers None for anything but one still finger, so none
        // of them can also fire this path (pinned in tests/zen_verbs_test.cpp).
        const zenverbs::Verb verb = g_zenVerbs.fingerUp(
            e->tfinger.fingerID, g_zenLastX, g_zenLastY, SDL_GetTicks(),
            cancelled);

        // Audit #6: with the mixer sheet up, gestures on the exposed page
        // are the sheet's business, nobody else's. The trackers were still
        // fed above so no per-finger state leaks past the sheet, but nothing
        // fires. (Fingers that went down after the sheet presented never
        // entered the trackers at all — see FINGER_DOWN.)
        if (CrossPointMixer_isPresented() || CrossPointInkPicker_isPresented()) {
          g_tapCand.spoil();
        } else if (zenBefore && verb == zenverbs::Verb::Down) {
          // THE DELIBERATE TAP, the one verb left on this path. Every gesture
          // that moves, and every multi-finger tap, is a native recognizer in
          // CrossPointZenRecognizers.mm now ("let's use apple for swiping
          // instead"); the classifier answers None for all of them, so a
          // swipe can never fire both a recognizer and this branch.
          //
          // WHAT IT DOES is ios/GestureBindings.h's answer since T-025 (owner
          // 2026-08-28). The model is LAYERED: a global Tap binding, which the
          // strip above the paper and the band below it may override. There is
          // no "on the paper" case -- a landing point between those boundaries
          // is simply one nothing overrides, so the global binding applies.
          // Its default is the front RIGHT button, per the swap ruling
          // ("reading on one finger", 2026-08-22), which is what the tap did
          // everywhere before any of this existed.
          //
          // THE SAME ZONE RULE THE RECOGNIZERS USE, off the same two published
          // boundaries. It is called here rather than in the recognizer file
          // because this verb is SDL's, not UIKit's -- one hit test, two
          // callers.
          const gesturebind::Zone zone =
              gesturebind::zoneFor(g_zenTapDownY, g_cardTopPx,
                                   zenPaperBottomPx());
          const gesturebind::Gesture zoneRow =
              gesturebind::zoneGesture(gesturebind::OneFinger::Tap, zone);
          const gesturebind::Gesture globalRow =
              gesturebind::globalGesture(gesturebind::OneFinger::Tap);
          const int zoneStored =
              zoneRow == gesturebind::Gesture::Count
                  ? 0
                  : CrossPointPrefs_gestureBinding(static_cast<int>(zoneRow));
          const int globalStored =
              CrossPointPrefs_gestureBinding(static_cast<int>(globalRow));
          const gesturebind::Action action = gesturebind::oneFingerAction(
              gesturebind::OneFinger::Tap, zone, /*zenOn=*/true, zoneStored,
              globalStored);
          SDL_Log("[zen] verb -> %s, tap landed %s (y=%.0f) -> %s",
                  zenverbs::verbName(verb), gesturebind::zoneName(zone),
                  g_zenTapDownY, gesturebind::actionName(action));
          if (action == gesturebind::Action::ToggleZen) {
            // Reached only if the owner points the tap at the toggle. The
            // shim's own toggle, not the recognizer entry point, because this
            // finger is already inside padWatch: spoiling the candidate is
            // still wanted and re-entering through the recognizer path would
            // be the same call by a longer road.
            CrossPointZen_toggleFromRecognizer("deliberate tap");
          } else if (action == gesturebind::Action::FontFamilyStep) {
            gpio.injectFontFamilyStep();
          } else {
            const int btn = gesturebind::buttonFor(action);
            if (btn != gesturebind::kNoButton) {
              gpio.queueButtonTap(static_cast<uint8_t>(btn), 60);
            } else if (action != gesturebind::Action::Nothing) {
              // A HOST ACTION THIS SITE DOES NOT KNOW. The recognizers'
              // performGestureAction is the fuller dispatcher; this branch is a
              // second, smaller copy because the deliberate tap is SDL's verb
              // and lives below UIKit. If a twelfth Action is ever appended,
              // that is the other place to teach -- and this says so out loud
              // rather than swallowing the gesture in silence, which is how a
              // new action would look exactly like a phone that stopped
              // delivering taps.
              SDL_Log("[zen] tap -> %s is not handled on the SDL tap path",
                      gesturebind::actionName(action));
            }
          }
          applyActions(g_core.fingerUp(e->tfinger.fingerID));
          break;
        }
      }

      {
        // A CANCELED finger (Control Center pull, incoming call) is not a
        // tap; fingerUp answers false for it and clears either way — no exit
        // path may leave the candidate latched (audit #1).
        const float candX = g_tapCand.downX(), candY = g_tapCand.downY();
        // The down TIMESTAMP had one reader, the page-color chip's log line,
        // and left with the chip on 2026-08-24. The candidate itself still
        // records it -- a tap is down + up without movement however long the
        // hold, so nothing here needs a duration.
        if (g_tapCand.fingerUp(e->tfinger.fingerID,
                               e->type == SDL_EVENT_FINGER_CANCELED)) {
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
          // THE PAGE-COLOR CHIP'S BRANCH WAS HERE until 2026-08-24 ("remove the
          // color button from single finger (not zen) mode ui"). A tap or a
          // hold opened the live appearance's drawer -- the gun mixer in dark,
          // the historical-ink picker in light. Both drawers still exist and
          // both pages are frozen (src/FrozenPage.h); what is gone is the way
          // in. A tap that lands where the button used to be now falls through
          // to the read-aloud word tap, which is what an empty part of the pad
          // band has always done.
          if (hitKeyboardChip(candX, candY)) {
            const bool want = !gpio.isHostKeyboardVisible();
            gpio.setHostKeyboardVisible(want);
            // Logged since 2026-08-24. This chip became the pad's ONLY
            // non-button control that day, and the one whose loss would trap a
            // reader in a text field; without a line here the difference
            // between "the tap missed" and "the toggle did nothing" is
            // invisible from outside, which is the state the page-color chip's
            // own crash investigation started in.
            SDL_Log("[kbchip] tap -> keyboard %s", want ? "up" : "down");
            SimulatorOverlay::requestPresent();
          } else
            CrossPointReadAloud_tapAtScreen(candX, candY);
        }
      }
      applyActions(g_core.fingerUp(e->tfinger.fingerID));
      break;
    }

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
      // Audit #5: everything per-touch and everything queued dies at this
      // boundary, not just PadCore. A queued tap that survived a
      // backgrounding used to fire its release with the whole background
      // span attached on return — which the firmware classifies as a long
      // press. The trackers reset too: their fingers are gone, and a
      // half-seen gesture must not resolve against touches from before the
      // background.
      g_tapCand.spoil();
      gpio.clearPendingButtonTaps();
      g_zenVerbs = zenverbs::Classifier{};
      applyActions(g_core.reset());
      break;

    // The pad is laid out from the output size, so a size change invalidates it.
    //
    // AND IT ARMS THE SETTLE WINDOW, which it did not until 2026-08-28 (S-027,
    // owner: "while on a video call, returning to app takes a while to get out
    // of blank screen"). This asked for exactly ONE present, and the comment
    // above repaintAfterForeground() already records why one is not enough: a
    // present issued while the surface is still settling returns success and is
    // then discarded, and an app that only draws when the panel changes has no
    // second frame coming.
    //
    // A call banner is precisely that case and it never backgrounds the app, so
    // the foreground path -- which HAS had the settle window since it was
    // measured -- never ran. The window resizes when the banner appears and
    // again when it goes, and each resize left the one present it asked for to
    // be thrown away. Same failure, same fix, now reached from both causes.
    case SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED: {
      g_padLaidOut = false;
      // AND THE RECTS GO WITH THE FLAG, on a SIZE change specifically.
      //
      // Clearing the flag alone schedules a relayout, but the relayout happens
      // in the PAINT path (see the layout gate in the overlay painter) while
      // finger events arrive through HalGPIO::update on a different cadence. So
      // between this event and the next present, padHitTest() was still walking
      // the OLD rects -- and it returns the first slot whose rect contains the
      // point, with no check that the geometry is current. A touch in that
      // window pressed whichever button used to be there, and the painter then
      // shaded that button rather than the one under the finger.
      //
      // That is a candidate mechanism for S-026, the bottom-right rocker
      // flashing on a press elsewhere, and it links it to S-027: a video call
      // resizes the window twice, so the reports may be one event seen twice.
      // Unproven -- neither is reproduced here -- but the behaviour is wrong on
      // its own terms.
      //
      // Zeroed rather than left stale, so padHitTest answers kNoSlot: during a
      // resize a tap does NOTHING, which is the right failure. Pressing the
      // wrong button is worse than dropping one tap in a window that lasts a
      // frame. Only THIS site invalidates geometry -- the zen toggle and the
      // band change also clear g_padLaidOut, but they do not move the output,
      // so their rects stay valid and their taps must keep working.
      for (auto &b : g_pad) b.rect = SDL_FRect{0, 0, 0, 0};
      armSettleRepaint();
      SimulatorOverlay::requestPresent();
      break;
    }

    default:
      break;
  }
  return true;  // never filter anything out
}

}  // namespace

// OUTSIDE the anonymous namespace, deliberately. This was defined inside it
// once, where extern "C" still gets internal linkage, and the mixer's
// reference to it killed the TestFlight archive at link -- a failure no
// desktop build can see, since only the iOS target compiles the mixer.
extern "C" void CrossPointMixer_glowChanged(void) { g_glowDirty.store(true); }

// THE ZEN TOGGLE, called by the native 3-finger UITapGestureRecognizer
// (CrossPointZenRecognizers.mm; owner 2026-08-22 "be sure to swap 3 finger
// tap to apple"). Exactly what the retired SDL toggle branch did — flip,
// refit, log, present — plus the seam the native move creates: the same three
// fingers also stream into SDL, so the tap candidate and the classifier are
// spoiled here the way the toggle branch spoiled them (audit #1: a
// gesture-consuming exit clears the candidate, always). The classifier would
// answer None for a 3-finger gesture anyway (peak != 1); the reset makes that
// not depend on event ordering between UIKit's recognition and SDL's lifts.
// Runs on the main thread (recognizer action), the same thread the SDL pump
// and the overlay run on.
extern "C" void CrossPointZen_toggleFromRecognizer(const char *source) {
  g_zen = !g_zen;
  g_padLaidOut = false;  // the band changes, so the page must be refitted
  // ONE line per toggle, naming the DIRECTION and the gesture that did it.
  // Two gestures reach here since 2026-08-27 (the 3-finger tap and the 5 s
  // one-finger hold) and neither can be seen in a screenshot, so this line is
  // the whole of the device confirmation for both.
  SDL_Log("[zen] toggle -> %s (%s)", g_zen ? "on" : "off",
          source ? source : "unknown");
  g_tapCand.spoil();
  g_zenVerbs = zenverbs::Classifier{};
  // Audit #2's honest hammer: release anything PadCore still holds, so no
  // capsule press a straddling finger fired stays held into zen, where the
  // pad does not exist. reset() releases held slots and fires nothing else.
  applyActions(g_core.reset());
  CrossPointZenRecognizers_setEnabled(g_zen);
  // Publish the converged zen-target geometry BEFORE requesting the present
  // that will show it -- see zenPreWarmLayout()'s comment (2026-08-29 flicker
  // fix) for why the ordinary draw-time layout pass is one present too late
  // to avoid a visibly mismatched intermediate frame on this exact toggle.
  zenPreWarmLayout();
  SimulatorOverlay::requestPresent();
  // The stored zenModeEnabled preference does not follow g_zen by itself --
  // see ios/ZenPrefSync.h and pollZenMode() (2026-08-29, owner: "keep zen
  // mode ios app setting reflective of active value"). Nothing is written to
  // NSUserDefaults here directly: pollZenMode(), which already runs every
  // frame, notices g_zen has moved away from what it last synced and writes
  // the store on its own next call. Writing it here too would just be a
  // second writer racing the first for no benefit -- the frame budget this
  // needs to land in is a poll, not a present.
}

// Belt-and-suspenders for the zen one-finger hold (native recognizers,
// CrossPointZenRecognizers.mm): the tap classifier's 400 ms ceiling already
// answers None for a finger held to the 0.75 s recognition point, but the
// same finger streams into SDL, so the candidate is spoiled the way the
// 3-finger toggle spoils it rather than depending on event ordering between
// UIKit's recognition and SDL's lift. Called at RECOGNITION (0.75 s), which is
// still where it belongs even though the select itself now fires on the lift
// (owner 2026-08-27) -- the earlier the candidate dies, the fewer orderings
// there are to reason about. Main thread (recognizer action), same as the
// toggle above.
extern "C" void CrossPointZen_spoilTapCandidate(void) {
  g_tapCand.spoil();
  g_zenVerbs = zenverbs::Classifier{};
}

// THE TOP EDGE OF THE PAPER, in device pixels, for the hold's zone test
// (ios/ZenHoldRouting.h). This is where black ends and paper begins -- the card
// top, not the page top: above it is the bezel and the safe-area cut-out, and
// the owner's rule is "above paper", not "above the text".
//
// Published by the LAYOUT pass on every pass in BOTH modes, which is what makes
// the question answerable on the launch before zen has ever been entered. Zero
// before the first layout, and a zero answers "everything is on the paper" --
// the conservative direction, since a stray toggle is worse than a missed one.
extern "C" float CrossPointZen_cardTopPx(void) { return g_cardTopPx; }

// ...and the PAPER'S BOTTOM EDGE, the other boundary the zones split on. This
// is g_zenPaper's bottom, which is the old top-rocker line (g_zenRowTopPx) --
// the same `line` the zen painter cuts the sheet at, read from the same place
// rather than recomputed, so the boundary the finger is judged against is the
// edge the eye can see.
//
// Published by layoutPad on every pass in BOTH modes, like the card top -- on
// the PHONE path. `layoutPadTablet` STILL publishes no bottom boundary of its
// own (2026-08-29: it gained a published `g_cardTopPx`, the TOP boundary, when
// the tablet grew its own paper card -- see the "AN AREA ABOVE THE PAPER"
// comment in layoutPadTablet -- but nothing analogous exists below the panel,
// since the tablet's pad rows sit in the side margins rather than a band under
// the page, so there is no rocker row to target). The fallback below answers
// with the panel's own bottom (exactly as the painter's does), so a tablet
// gets a below-the-paper zone measured against the page's bottom edge rather
// than a rocker row. That is deliberate rather than accidental -- it is the
// painter's own definition of where the sheet ends -- and with the shipped
// defaults nothing follows from it, since every Below binding resolves to
// what OnPaper does.
//
// THE CONSEQUENCE OF THE 2026-08-29 CHANGE: the tablet's above-the-paper zone
// was previously unreachable (yPx is never negative, and paperTopPx was
// always 0), so `HoldAbove`'s "toggle zen" default -- the one row that fires
// outside zen -- could never trigger from a hold at the top of an iPad
// screen. It can now. Flagged, not silently accepted: this is a real
// behavior change on a shipped default, reported to the owner rather than
// decided here.
//
// Before the FIRST present of all, both boundaries are 0, and a bottom that is
// not below the top makes zoneFor() collapse to the two-zone rule this feature
// extended -- the conservative direction, since a geometry that has not been
// measured must not invent a third zone out of a zero.
extern "C" float CrossPointZen_paperBottomPx(void) {
  return zenPaperBottomPx();
}

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
    // WHAT THE PANEL CAN DO, AND WHETHER THIS BUILD IS ALLOWED TO USE IT.
    //
    // Owner directive 2026-08-26, "enable 120hz if possible on iphone air".
    // Two independent things have to be true and each is invisible on its own,
    // so both are read back from the running system and printed together:
    // UIScreen says what the display is capable of, and the bundle's own
    // Info.plist says whether CADisableMinimumFrameDuration lifted the 60 Hz
    // clamp iOS otherwise applies to every app. A ProMotion phone with no key
    // runs at 60 and looks fine; a key on a 60 Hz panel does nothing and also
    // looks fine. This line is the only thing that tells the two apart, and it
    // is the reason not to answer the question from a model name.
    //
    // Beside the [BUILD] identity check because it is the same kind of fact --
    // what this binary on this hardware actually is -- and the same log is
    // where anyone already looks for it.
    const int maxFps = sim_host_screen::maximumFramesPerSecond();
    const bool declared = sim_host_screen::highFrameRateDeclared();
    std::printf("[BUILD] display: %d Hz maximum, high frame rate %s -> app may "
                "present at up to %d Hz\n",
                maxFps, declared ? "DECLARED" : "not declared",
                declared ? maxFps : (maxFps > 60 ? 60 : maxFps));
    std::fflush(stdout);
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
  // left behind — the tap candidate and the gesture trackers included, since
  // this process longjmps through here with statics intact — and relayout
  // against the (possibly rotated) window.
  g_tapCand.spoil();
  g_zenVerbs = zenverbs::Classifier{};
  applyActions(g_core.reset());
  g_padLaidOut = false;
  // Recognizer enablement follows the live zen flag across wakes too.
  CrossPointZenRecognizers_setEnabled(g_zen);

  // Appearance. SDL_Init has already run (HalDisplay::begin calls it), so the
  // theme is populated and can be read straight away; the watch keeps it current
  // if the user flips the system between light and dark while the app is up.
  applyTheme();
  SDL_Log("[harness] appearance: %s, pad contrast outline %+d fill %+d",
          g_dark ? "dark" : "light", g_appliedOutline, g_appliedFill);

  // Owner ruling 2026-08-29: "remove clock, wifi and all system status" on
  // iPad. The static Info.plist declaration (UIStatusBarHidden,
  // UIViewControllerBasedStatusBarAppearance) already hides it on iPhone;
  // measured NOT to on iPad. See CrossPointAppearance.mm for the measurement
  // and why the fix is scoped there instead. No-op on iPhone.
  CrossPointAppearance_hideStatusBarOnIPad();

  // BEFORE _begin: on a wake the previous boot's speech is still running --
  // the longjmp abandoned the run mid-utterance -- and the old page must not
  // keep speaking (or phantom-turn pages) over the rebooted firmware. First
  // boot: no-op, nothing exists yet.
  CrossPointReadAloud_resetForReboot();
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
  // Before the pad: the pad is built on the panel's paper, so a palette change
  // must land first or the pad spends one frame on the previous field.
  pollPanelPalette();
  pollPanelGlow();
  pollBeamPaint();
  pollPageFade();
  pollPageFadeDepth();
  pollPresentFlash();
  // DIAGNOSTIC ONLY (CROSSPOINT_SIM_OPEN_MIXER=1): present the mixer shortly
  // after launch with no finger involved. Exists because the color chip's tap
  // crashed on a device (owner report 2026-08-21) and the iOS Simulator is the
  // one place a symbolicated crash can be produced on demand -- simctl cannot
  // synthesize a tap, so the trigger has to come from inside. A frame counter
  // rather than a timer: the pad's no-timers rule holds even for diagnostics.
  {
    static int s_openMixerCountdown = -2;
    if (s_openMixerCountdown == -2) {
      const char *e = std::getenv("CROSSPOINT_SIM_OPEN_MIXER");
      s_openMixerCountdown = (e && e[0] == '1') ? 120 : -1;  // ~2 s of frames
    }
    if (s_openMixerCountdown > 0 && --s_openMixerCountdown == 0) {
      SDL_Log("[mixer] diagnostic auto-open");
      CrossPointMixer_present();
    }
    // CROSSPOINT_SIM_OPEN_INKPICKER=1: same hook for the light picker, same
    // frame-counter shape, same reason (simctl cannot synthesize a tap).
    static int s_openInkPickerCountdown = -2;
    if (s_openInkPickerCountdown == -2) {
      const char *e = std::getenv("CROSSPOINT_SIM_OPEN_INKPICKER");
      s_openInkPickerCountdown = (e && e[0] == '1') ? 120 : -1;
    }
    if (s_openInkPickerCountdown > 0 && --s_openInkPickerCountdown == 0) {
      SDL_Log("[inkpicker] diagnostic auto-open");
      CrossPointInkPicker_present();
    }
    // CROSSPOINT_SIM_APPLY_INK="ink,paper,density": drive the picker's exact
    // apply path with no finger -- the mixer's applyGunsForTest pattern.
    static int s_applyInkCountdown = -2;
    // The fourth field is the PAPER STRENGTH and is optional -- it defaults to
    // full, so every three-field recipe written before the paper dial existed
    // still means exactly what it meant.
    static int s_applyInkArgs[4] = {0, 0, 100, lightink::kPaperStrengthDefault};
    if (s_applyInkCountdown == -2) {
      const char *e = std::getenv("CROSSPOINT_SIM_APPLY_INK");
      const int parsed =
          e ? std::sscanf(e, "%d,%d,%d,%d", &s_applyInkArgs[0],
                          &s_applyInkArgs[1], &s_applyInkArgs[2],
                          &s_applyInkArgs[3])
            : 0;
      s_applyInkCountdown = (parsed == 3 || parsed == 4) ? 120 : -1;
    }
    if (s_applyInkCountdown > 0 && --s_applyInkCountdown == 0) {
      CrossPointInkPicker_applyForTest(s_applyInkArgs[0], s_applyInkArgs[1],
                                       s_applyInkArgs[2], s_applyInkArgs[3]);
    }
    // CROSSPOINT_SIM_SELECT_PRESET=<int>: pick a NAMED PRESET through the exact
    // path the Presets list's cells take, with no finger. The other half of the
    // round trip APPLY_INK and MIX_GUNS drive -- those claim the shared Custom
    // slot, this is the only thing that hands it back -- so a headless run can
    // prove both directions in one launch sequence.
    static int s_selectPresetCountdown = -2;
    static int s_selectPreset = -1;
    if (s_selectPresetCountdown == -2) {
      const char *e = std::getenv("CROSSPOINT_SIM_SELECT_PRESET");
      // ~4 s, deliberately AFTER APPLY_INK's 120 and MIX_GUNS' 180: with all
      // three set, one launch walks the whole round trip in order -- claim the
      // slot from light, claim it from dark, then hand both back to a name --
      // with a page render between each.
      s_selectPresetCountdown =
          (e && std::sscanf(e, "%d", &s_selectPreset) == 1) ? 240 : -1;
    }
    if (s_selectPresetCountdown > 0 && --s_selectPresetCountdown == 0)
      CrossPointPresetList_selectForTest(s_selectPreset);
    // CROSSPOINT_SIM_TAP_CHIP=<ms>: one synthetic finger tap at the KEYBOARD
    // chip's center, `ms` after launch, through the FULL finger path -- the SDL
    // event watch, g_tapCand, hitKeyboardChip and the toggle, exactly as a
    // thumb runs them.
    //
    // IT USED TO AIM AT THE PAGE-COLOR CHIP, which was removed on 2026-08-24;
    // it was written because a device crash was reported against that tap and
    // the auto-opens above reproduced nothing. Re-aimed rather than deleted,
    // because the surviving chip is the one that MATTERS -- it is the only way
    // to dismiss the iPhone software keyboard -- and after the removal it had
    // no synthetic-tap path at all, so "does the chip still work" could only be
    // answered by a human with a finger. That is exactly the shape of claim
    // this repo does not accept.
    //
    // A TIME, not a frame count, and no default: a frame here is one
    // CrossPointHarness_perFrame and the app presents rarely, so 150 frames was
    // ~10 s on one device and ~2 s on another. The chip only hit-tests while a
    // field is open, so the caller has to schedule this AFTER the navigation
    // that opens one -- which is the whole point, and why the wall clock is the
    // honest unit. Logs whether the chip was live, so a miss reads as a miss
    // rather than as a broken toggle.
    //
    // ONE-SHOT ACROSS A REBOOT, deliberately, and therefore NOT registered in
    // src/SimulatorRebootResets.h -- unlike the schedules that file exists for.
    // The iOS reboot is a longjmp in the same process, so these statics survive
    // it and the tap does not fire twice. That is what is wanted here: a
    // diagnostic tap that re-armed itself would press the chip again on a
    // machine whose field is long closed. Same shape as the auto-opens above.
    static Uint64 s_tapChipAt = 0;
    static bool s_tapChipDone = true;
    static bool s_tapChipRead = false;
    if (!s_tapChipRead) {
      s_tapChipRead = true;
      const char *e = std::getenv("CROSSPOINT_SIM_TAP_CHIP");
      int ms = 0;
      if (e && std::sscanf(e, "%d", &ms) == 1 && ms > 0) {
        s_tapChipAt = static_cast<Uint64>(ms);
        s_tapChipDone = false;
      }
    }
    if (!s_tapChipDone && SDL_GetTicks() >= s_tapChipAt) {
      s_tapChipDone = true;
      float outW = 0, outH = 0;
      if (g_kbChip.w > 0 && windowPixelSize(g_windowId, &outW, &outH)) {
        const float cx = (g_kbChip.x + g_kbChip.w / 2) / outW;
        const float cy = (g_kbChip.y + g_kbChip.h / 2) / outH;
        SDL_Log("[kbchip] diagnostic tap at %.3f,%.3f (field %s, keyboard %s)",
                cx, cy, gpio.isTextEntryActive() ? "open" : "CLOSED -- the chip "
                                                            "does not hit-test",
                gpio.isHostKeyboardVisible() ? "up" : "down");
        SDL_Event down{};
        down.type = SDL_EVENT_FINGER_DOWN;
        down.tfinger.touchID = 99;
        down.tfinger.fingerID = 99;
        down.tfinger.x = cx;
        down.tfinger.y = cy;
        down.tfinger.windowID = g_windowId;
        SDL_PushEvent(&down);
        SDL_Event up = down;
        up.type = SDL_EVENT_FINGER_UP;
        SDL_PushEvent(&up);
      } else {
        SDL_Log("[kbchip] diagnostic tap skipped: the pad has not been laid out");
      }
    }
    // CROSSPOINT_SIM_TAP_PAD=<BUTTON NAME, e.g. BACK>: one synthetic finger
    // tap on that pad button, down ~2.5 s after launch and up 12 frames later.
    // The FULL finger path -- padWatch, padHitTest, PadCore, applyActions --
    // because simctl cannot synthesize a touch. Added for the build-120 "back
    // from Settings opens the book" investigation: it proves on the iOS
    // Simulator that one finger tap yields exactly ONE press and ONE release
    // injection, never two. ASSERT ON THE [harness] <NAME> down/up LOG LINES,
    // not on [ACT] transitions: this hook runs AFTER loop() on the firmware
    // thread, so the injected EDGES land in the gap the next beginFrame()
    // wipes (the queueButtonTap race, HalGPIO.h) and the firmware never acts
    // on them. A real thumb's events are pushed during update()'s pump inside
    // loop() and do not have this problem; end-to-end consumption is proven by
    // the desktop script driving the same injectButtonDown/Up API.
    static int s_tapPadCountdown = -2;
    static int s_tapPadSlot = -1;
    if (s_tapPadCountdown == -2) {
      const char *e = std::getenv("CROSSPOINT_SIM_TAP_PAD");
      s_tapPadCountdown = -1;
      if (e && e[0]) {
        for (int i = 0; i < kPadCount; ++i) {
          if (SDL_strcasecmp(e, g_pad[i].name) == 0) {
            s_tapPadSlot = i;
            s_tapPadCountdown = 150;
            break;
          }
        }
      }
    }
    if (s_tapPadCountdown > 0 && g_pad[s_tapPadSlot >= 0 ? s_tapPadSlot : 0].rect.w > 0) {
      const int tick = s_tapPadCountdown--;
      if (tick == 12 || tick == 1) {  // 12: finger down; 1: finger up
        float outW = 0, outH = 0;
        if (windowPixelSize(g_windowId, &outW, &outH)) {
          const SDL_FRect &r = g_pad[s_tapPadSlot].rect;
          SDL_Event ev{};
          ev.type = (tick == 12) ? SDL_EVENT_FINGER_DOWN : SDL_EVENT_FINGER_UP;
          ev.tfinger.touchID = 98;
          ev.tfinger.fingerID = 98;
          ev.tfinger.x = (r.x + r.w / 2) / outW;
          ev.tfinger.y = (r.y + r.h / 2) / outH;
          ev.tfinger.windowID = g_windowId;
          SDL_Log("[padtap] diagnostic %s finger %s",
                  g_pad[s_tapPadSlot].name, tick == 12 ? "down" : "up");
          SDL_PushEvent(&ev);
        }
      }
    }
    // CROSSPOINT_SIM_MIX_GUNS="r,g,b,w": call the sliders' own apply function
    // (CrossPointMixer_applyGunsForTest -> applyGuns) shortly after launch.
    // A three-value CSV still parses, with w treated as 0. Assignments are the
    // defaults; there is no env for them. Exists because the owner's report
    // "not seeing colors actually mixed"
    // (2026-08-21) needed the WRITE half of the mixer proven headlessly --
    // the poll half was proven live with defaults-write, but a slider cannot
    // be dragged by simctl, so the function it calls gets driven from inside.
    static int s_mixGunsCountdown = -2;
    static int s_mixGuns[4] = {0, 0, 0, 0};
    if (s_mixGunsCountdown == -2) {
      const char *e = std::getenv("CROSSPOINT_SIM_MIX_GUNS");
      int parsed = e ? sscanf(e, "%d,%d,%d,%d", &s_mixGuns[0], &s_mixGuns[1],
                              &s_mixGuns[2], &s_mixGuns[3])
                     : 0;
      if (parsed == 3) {
        s_mixGuns[3] = 0;
        parsed = 4;
      }
      if (parsed == 4)
        s_mixGunsCountdown = 180;  // ~3 s: after the first page render
      else
        s_mixGunsCountdown = -1;
    }
    if (s_mixGunsCountdown > 0 && --s_mixGunsCountdown == 0)
      CrossPointMixer_applyGunsForTest(s_mixGuns[0], s_mixGuns[1], s_mixGuns[2],
                                       s_mixGuns[3]);
  }
  pollPhosphorGrain();
  pollLetterpress();
  pollPaperTooth();
  pollScanlines();
  pollDarkSurfaceItems();
  pollReaderInsets();
  pollZenMode();
  pollPadContrast();
  repaintAfterForeground();
  CrossPointReadAloud_perFrame();
}
