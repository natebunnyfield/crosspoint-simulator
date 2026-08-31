// Native UIKit gesture recognizers for every gesture in the configurable set.
//
// Owner rulings, 2026-08-22, verbatim. After the device report "two finger
// left and right swap is not working most of the time, spread and pinch never
// worked": "are these not ios standard gestures?" — and then, extending it to
// one-finger motion as well: "let's use apple for swiping instead". The
// ergonomics point is the owner's: the hand-rolled thresholds mis-modeled
// real hands (a thumb-anchored pinch drifts its centroid; a real two-finger
// swipe converges and diverges while it translates), and Apple's recognition
// engine already models them. The succession is:
//
//   tap zones (2026-08-19..22)
//     -> hand-rolled verb classifier (ZenVerbs.h, all gestures)
//       -> NATIVE RECOGNIZERS for all motion, SDL for the deliberate tap only
//         -> the set re-cut to 17 configurable gestures (2026-08-28)
//
// THE SET, and what it deliberately does NOT contain, is enumerated in
// ios/GestureBindings.h. The short version, because it decides what this file
// installs: single taps only (1 and 2 fingers), swipes on 1 and 2 fingers in
// all four directions, long presses on 1 and 2 fingers, pinch, rotation, shake.
// No double or triple taps, no three-, four- or five-finger gestures, no
// screen-edge pans.
//
// **THE 3-FINGER TAP AND THE 4-FINGER TAP ARE GONE**, and their recognizers are
// REMOVED rather than left installed-but-unbound: an installed recognizer still
// consumes touches and can still fail a competing gesture, so leaving one for a
// gesture nobody can bind is not a neutral act. The owner was shown that the
// trim costs the three-finger zen toggle and the four-finger power tap, and
// chose it.
//
// **NO CONDITIONAL INSTALLATION, AND NO FAILURE REQUIREMENTS.** With no
// multi-tap in the set there is nothing to disambiguate: a single tap never has
// to wait for a double tap that cannot exist, so every recognizer here is
// installed once and left alone. (A double-tap recognizer would put roughly
// 300 ms on every single tap, which is why the set does not have one; that is
// recorded at the set's definition in GestureBindings.h rather than defended
// with machinery here.)
//
// **BUT INSTALLING A RECOGNIZER IS STILL NOT FREE, and the delegate is what
// pays for it.** Five of the seventeen gestures ship bound to Nothing, and three
// of those five overlap gestures the app already had -- rotation over pinch
// above all, since a real pinch always carries a few degrees of twist and
// UIKit's default is that whichever recognizes first prevents the rest. An
// inert rotation would therefore have cost the owner pinches he has today. The
// one rule in the delegate below is: **a gesture that ships doing nothing may
// never prevent one that ships doing something.** Between two rows that both
// ship bound the answer is NO, which is what UIKit does with no delegate at
// all, so nothing about the pre-2026-08-28 arbitration moves.
//
// DIVISION OF LABOR (one owner per gesture): every two-finger gesture, every
// swipe, every long press, pinch and rotation are Apple's. SDL keeps the
// 1-finger deliberate TAP alone, with its pure-tested gates (28 px slop,
// 400 ms) in ZenVerbs.h.
//   * the ONE-FINGER HOLD (owner 2026-08-27, "holding down one finger longer
//     than five seconds toggles zen and single finger modes", retuned to THREE
//     seconds by him the same day, and to 0.75 s where it now sits) is the one
//     always-enabled RECOGNIZER: its ABOVE-the-paper row toggles zen, so it has
//     to fire while zen is off as well as while zen is on. Its collision with
//     the zen long-press select is resolved by POSITION (GestureBindings.h's
//     zones), not by duration.
//   * the SHAKE (owner 2026-08-29, "making shake gesture work in single-finger
//     mode") is always on too, but it is not a recognizer at all -- see the
//     CPXShakeCatcher class comment below for its own mechanism (first-responder
//     status, not .enabled).
//
// NO DOUBLE FIRE, BY CONSTRUCTION. A touch that fires a swipe recognizer has
// traveled far past the classifier's 28 px tap slop, so the classifier
// answers None for it; a deliberate tap stays inside the slop, which no swipe
// recognizer recognizes.
//
// COEXISTENCE. cancelsTouchesInView=NO and delaysTouchesBegan/Ended=NO on
// every recognizer, so SDL receives the finger stream untouched — the tap
// and the pad both live on the SDL finger stream.
//
// VOICEOVER. VoiceOver intercepts touches system-side and delivers its own
// gesture vocabulary before the app's recognizers see anything; with VO on,
// these recognizers simply do not receive the raw stream, the same as every
// other app-level recognizer. Attaching them steals nothing from VO — the
// accessibility surface stays CrossPointAccessibility's.
//
// WHAT EACH GESTURE DOES IS NOT IN THIS FILE. The bindings are Settings.app
// rows and the rule lives in ios/GestureBindings.h, pure and truth-tabled in
// tests/gesture_bindings_test.cpp. This file recognizes and reports; it decides
// nothing. Three consequences worth knowing before editing here:
//
//   * THE SHIPPED DEFAULTS ARE WHAT THIS FILE USED TO HARDCODE, gesture by
//     gesture, so an install that never opens the setting behaves as build 157
//     did apart from the two removals above. They are written out beside
//     gesturebind::defaultAction.
//   * ON THE PAPER IS FIXED and has no row: a landing point between the two
//     boundaries is simply one nothing overrides. Only the strip ABOVE the
//     sheet and the band BELOW it are configurable, judged from the landing
//     point against the two boundaries the layout already publishes
//     (g_cardTopPx and the paper's bottom), and only for SINGLE-FINGER
//     gestures.
//   * ZEN SCOPE is a property of the GESTURE, never of the action bound to it.
//     Two cases fire outside zen — the hold above the paper, and the shake
//     (added 2026-08-29) — whatever either holds.
//
// VERIFICATION. UIKit recognizers cannot be driven by pushed SDL events (they
// live above SDL, on the UIKit touch pipeline, which neither SDL_PushEvent
// nor simctl can synthesize into) — so the recognizer paths are
// device-confirm only, which is acceptable now that the recognition itself is
// Apple's. What CAN be proven off-device: the wiring compiles, attaches (the
// "[zen] recognizers attached" log at first zen enable, which ENUMERATES what
// was actually installed), and the SDL tap path still works with recognizers
// attached.

#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include "CrossPointPrefs.h"
#include "GestureBindings.h"
#include "HalGPIO.h"
#include "ZenHoldRouting.h"

extern "C" bool CrossPointMixer_isPresented(void);
extern "C" bool CrossPointInkPicker_isPresented(void);
// The shim's toggle: flip g_zen, refit, present, and spoil the SDL-side tap
// candidate and classifier for the fingers that did it. The argument names the
// gesture, and is what the one `[zen] toggle` line reports — several gestures
// can reach this (any binding may be pointed at it), and a log that cannot tell
// them apart is a log that cannot confirm any of them on device.
extern "C" void CrossPointZen_toggleFromRecognizer(const char *source);
// The shim's spoil, without the toggle: the long-press select needs the same
// candidate/classifier reset the toggle performs, for the same finger-also-
// streams-into-SDL reason.
extern "C" void CrossPointZen_spoilTapCandidate(void);
extern "C" float CrossPointZen_cardTopPx(void);
// ...and the paper's BOTTOM edge, the other boundary the zones split on. Both
// come from the layout pass, in device pixels, and neither is a new rect: this
// is g_zenPaper's bottom (g_zenRowTopPx, the top of the old rocker row), which
// layoutPad already publishes in BOTH modes.
extern "C" float CrossPointZen_paperBottomPx(void);

namespace {
// Tracks the flag CrossPointZenRecognizers_setEnabled was last given, so the
// shake catcher (a UIResponder, not a recognizer — .enabled does not exist for
// it) can gate on zen the way the recognizers do.
bool g_zenOn = false;

// The routing state for the ONE-finger hold in flight (ios/ZenHoldRouting.h).
// One hold at a time by construction: a second finger poisons it.
zenhold::Hold g_hold;

// THE BUTTON INDICES AGREE ACROSS THE HEADER BOUNDARY. GestureBindings.h is
// pure by design and cannot include the HAL, so it mirrors these seven numbers;
// a renumbering on either side has to fail the build rather than press the
// wrong key on a phone, which is the one failure here nobody would trace back
// to a header.
static_assert(gesturebind::kBtnBack == HalGPIO::BTN_BACK, "BTN_BACK");
static_assert(gesturebind::kBtnConfirm == HalGPIO::BTN_CONFIRM, "BTN_CONFIRM");
static_assert(gesturebind::kBtnLeft == HalGPIO::BTN_LEFT, "BTN_LEFT");
static_assert(gesturebind::kBtnRight == HalGPIO::BTN_RIGHT, "BTN_RIGHT");
static_assert(gesturebind::kBtnUp == HalGPIO::BTN_UP, "BTN_UP");
static_assert(gesturebind::kBtnDown == HalGPIO::BTN_DOWN, "BTN_DOWN");
static_assert(gesturebind::kBtnPower == HalGPIO::BTN_POWER, "BTN_POWER");

// THE INSTALLED SET. Two parallel arrays rather than a map: the only two
// questions asked of it are "which row did this object come from" (once per
// firing, over a set of thirteen) and "walk everything installed". Built once
// -- see the header comment for why nothing here is conditional.
NSMutableArray<UIGestureRecognizer *> *g_installed = nil;
NSMutableArray<NSNumber *> *g_installedRow = nil;
// Two-finger holds that have already fired for the gesture in flight. UIKit
// re-delivers .began on some paths, and two toggles in one gesture cancel out
// -- which reads on device as the gesture doing nothing at all. The ONE-finger
// hold has its own richer latch in zenhold::Hold and is not in here.
NSMutableSet<UIGestureRecognizer *> *g_holdFired = nil;

// WHAT THIS GESTURE IS BOUND TO RIGHT NOW. Two fetches and one pure call: the
// stored integer from Settings.app, and gesturebind::actionFor to resolve it
// against the zen gate and this gesture's default. Nothing decides anything
// here -- see ios/GestureBindings.h, which owns the whole rule.
gesturebind::Action liveAction(gesturebind::Gesture g) {
  return gesturebind::actionFor(
      g, g_zenOn, CrossPointPrefs_gestureBinding(static_cast<int>(g)));
}

// MUST THIS RECOGNIZER STAY ENABLED WHILE ZEN IS OFF? Derived from the rule
// rather than listed here, so the always-on case lives in exactly one file: the
// one-finger hold says so through its ABOVE-the-paper row, which is the row
// that toggles zen today.
bool rowIsAlwaysOn(gesturebind::Gesture g) {
  return gesturebind::firesOutsideZen(g) ||
         gesturebind::firesOutsideZen(
             gesturebind::zoneRowFor(g, gesturebind::Zone::AbovePaper)) ||
         gesturebind::firesOutsideZen(
             gesturebind::zoneRowFor(g, gesturebind::Zone::BelowPaper));
}

// Which row an installed recognizer came from, or Count for an object this file
// did not install (nothing else attaches to the SDL view today, but a nil-safe
// answer costs one comparison and a wrong-row dispatch would press a button
// nobody asked for).
gesturebind::Gesture rowOf(UIGestureRecognizer *g) {
  if (!g_installed) return gesturebind::Gesture::Count;
  const NSUInteger i = [g_installed indexOfObjectIdenticalTo:g];
  if (i == NSNotFound) return gesturebind::Gesture::Count;
  return static_cast<gesturebind::Gesture>(g_installedRow[i].intValue);
}

// WHERE A ONE-FINGER GESTURE LANDED. locationInView is in POINTS and the
// published boundaries are in DEVICE PIXELS, so one has to be converted; the
// view's own contentScaleFactor is the conversion the rest of the layout
// already uses.
//
// This is the SAME hit test the one-finger hold has used since 2026-08-27. The
// travelling gestures that consult it are the four one-finger swipes, and a
// swipe's recognition point sits within a fingertip of its landing point in the
// axis that matters: a horizontal swipe barely moves in y, and a VERTICAL swipe
// is judged where UIKit recognized it, which is the honest answer to "where did
// this gesture happen" for a gesture that crosses zones by definition.
gesturebind::Zone zoneOf(UIGestureRecognizer *g, float *yPxOut) {
  const CGPoint loc = [g locationInView:g.view];
  const CGFloat scale = g.view ? g.view.contentScaleFactor : 1.0;
  const float yPx = static_cast<float>(loc.y * scale);
  if (yPxOut) *yPxOut = yPx;
  return gesturebind::zoneFor(yPx, CrossPointZen_cardTopPx(),
                              CrossPointZen_paperBottomPx());
}

// ONE PLACE WHERE A RESOLVED ACTION BECOMES SOMETHING THAT HAPPENS, shared by
// the recognizers and the shake catcher so the two cannot drift. `what` names
// the gesture and is what the `[zen]` log prints -- on device that line is the
// only confirmation that a binding took effect, so it says the gesture, the
// zone it was judged in and the action it resolved to.
void performGestureAction(gesturebind::Action a, const char *what) {
  // The palette sheets leave the view under them hit-testable (pageSheet with
  // an undimmed medium detent); a gesture on the exposed page must not drive
  // the reader while a tray is up. Same rule as the shim's finger gate, and it
  // comes FIRST so the log says why nothing happened.
  if (CrossPointMixer_isPresented() || CrossPointInkPicker_isPresented()) {
    SDL_Log("[zen] %s swallowed (palette sheet presented)", what);
    return;
  }
  if (a == gesturebind::Action::Nothing) {
    // Either the owner cleared this binding or the gesture is zen-only and zen
    // is off. Logged rather than silent: "the gesture did nothing" and "the
    // phone never delivered the gesture" look identical on a device, and
    // telling them apart is what this line is for.
    SDL_Log("[zen] %s -> nothing", what);
    return;
  }
  if (a == gesturebind::Action::ToggleZen) {
    // The shim's toggle: flip g_zen, refit, present, and spoil the SDL-side tap
    // candidate and classifier for the fingers that did it.
    CrossPointZen_toggleFromRecognizer(what);
    return;
  }
  if (a == gesturebind::Action::FontFamilyStep) {
    SDL_Log("[zen] %s -> font family step", what);
    gpio.injectFontFamilyStep();
    return;
  }
  if (a == gesturebind::Action::FontFamilyStepBack) {
    // WIRED 2026-08-29. The channel carries a signed delta and
    // HalGPIO::consumeFontFamilyStep() returns it (0 none, +1 next, -1
    // previous); the reader passes the sign straight to
    // cycleReaderFontFamily(int delta), which has always taken one -- a held
    // side button calls it with -1 (EpubReaderActivity.cpp:601). The device
    // no-op in lib/hal/HalGPIO.h returns 0, so the poll still folds away on
    // hardware.
    SDL_Log("[zen] %s -> font family step BACK", what);
    gpio.injectFontFamilyStep(-1);
    return;
  }

  const int btn = gesturebind::buttonFor(a);
  if (btn == gesturebind::kNoButton) return;  // Unset never reaches here
  SDL_Log("[zen] %s -> %s (button %d)", what, gesturebind::actionName(a), btn);
  gpio.queueButtonTap(static_cast<uint8_t>(btn), 60);
}

UISwipeGestureRecognizerDirection uikitSwipeDir(gesturebind::Dir d) {
  switch (d) {
    case gesturebind::Dir::Left: return UISwipeGestureRecognizerDirectionLeft;
    case gesturebind::Dir::Right: return UISwipeGestureRecognizerDirectionRight;
    case gesturebind::Dir::Up: return UISwipeGestureRecognizerDirectionUp;
    case gesturebind::Dir::Down: return UISwipeGestureRecognizerDirectionDown;
    case gesturebind::Dir::None: break;
  }
  return UISwipeGestureRecognizerDirectionRight;
}
}  // namespace

@interface CPXZenGestureHandler : NSObject <UIGestureRecognizerDelegate>
@end

@implementation CPXZenGestureHandler

// A ONE-FINGER GESTURE, resolved through the LAYERS and performed.
//
// Two rows are read, never one: the zone's override (if the landing point is in
// a zone that has one) and the global row. ios/GestureBindings.h decides which
// wins -- a blank override falls through, a set one takes precedence, and an
// explicit Nothing in a zone is an override that means "not here", not a blank.
// This method only fetches and reports.
- (void)oneFinger:(gesturebind::OneFinger)kind at:(UIGestureRecognizer *)g {
  float yPx = 0.0f;
  const gesturebind::Zone z = zoneOf(g, &yPx);
  const gesturebind::Gesture zoneRow = gesturebind::zoneGesture(kind, z);
  const gesturebind::Gesture globalRow = gesturebind::globalGesture(kind);
  // A landing point between the boundaries has no override row at all -- the
  // paper is simply where nothing overrides (owner 2026-08-28: "there is no 'on
  // the paper', it's just normal configuration"). Nothing is read for it,
  // because reading a key that does not exist would be the first step toward
  // one existing.
  const int zoneStored =
      zoneRow == gesturebind::Gesture::Count
          ? 0
          : CrossPointPrefs_gestureBinding(static_cast<int>(zoneRow));
  const int globalStored =
      CrossPointPrefs_gestureBinding(static_cast<int>(globalRow));
  const gesturebind::Action a =
      gesturebind::oneFingerAction(kind, z, g_zenOn, zoneStored, globalStored);
  // The log says which LAYER answered, because "the override did not take" and
  // "the phone did not deliver the gesture" look identical on a device and this
  // is the only line that can tell them apart.
  const bool overridden =
      zoneRow != gesturebind::Gesture::Count &&
      gesturebind::resolve(zoneRow, zoneStored) != gesturebind::Action::Inherit;
  char what[160];
  SDL_snprintf(what, sizeof(what),
               "%s %s (y=%.0f, paper %.0f..%.0f, zen %s, %s)",
               gesturebind::oneFingerName(kind), gesturebind::zoneName(z), yPx,
               CrossPointZen_cardTopPx(), CrossPointZen_paperBottomPx(),
               g_zenOn ? "on" : "off",
               overridden ? "zone override" : "global layer");
  performGestureAction(a, what);
}

// ONE ROW, ONE RECOGNIZER, so reading a firing back is unambiguous: the object
// itself names its row. Single-finger rows go through the layered path; every
// other row is one global binding.
- (void)dispatch:(UIGestureRecognizer *)g {
  const gesturebind::Gesture which = rowOf(g);
  if (which == gesturebind::Gesture::Count) return;
  const gesturebind::OneFinger kind = gesturebind::row(which).kind;
  if (kind != gesturebind::OneFinger::Count) {
    [self oneFinger:kind at:g];
    return;
  }
  performGestureAction(liveAction(which), gesturebind::gestureName(which));
}

- (void)tap:(UITapGestureRecognizer *)g {
  [self dispatch:g];
}

- (void)swipe:(UISwipeGestureRecognizer *)g {
  [self dispatch:g];
}

// One step per gesture, on the lift — not continuous. The reader repaginates
// per step, so a continuous pinch would queue a storm of font steps.
//
// PINCH AND SPREAD ARE TWO ROWS off one recognizer: they are one gesture to
// UIKit and two to a reader, and the owner enumerated them separately.
- (void)pinch:(UIPinchGestureRecognizer *)g {
  if (g.state != UIGestureRecognizerStateEnded) return;
  if (g.scale == 1.0) return;
  const gesturebind::Gesture which = g.scale > 1.0
                                         ? gesturebind::Gesture::Spread
                                         : gesturebind::Gesture::Pinch;
  performGestureAction(liveAction(which), gesturebind::gestureName(which));
}

// ROTATION FOLLOWS PINCH'S PRECEDENT EXACTLY, and deliberately: it is the other
// continuous two-finger recognizer, and a slow rotation reported continuously
// would queue the same storm of font steps a continuous pinch would. One step,
// on the lift. WHICH of the two rows fires is read from the measured angle and
// from nowhere else — UIKit reports rotation in radians in VIEW space, where +y
// is down, so a positive angle is clockwise on the glass. (The table used to
// carry a `sign` field saying the same thing; nothing read it, so flipping it
// changed nothing and failed nothing, and it is gone.)
//
// Pinch and rotation DO recognize simultaneously while rotation ships inert —
// see the delegate below, and note that it is what stops a twisty pinch being
// arbitrated away from the font step the owner actually has bound. Bind rotation
// and a twist that also squeezes will do both things; that is the cost of having
// asked for both, and the Two Fingers group's footer says so.
- (void)rotate:(UIRotationGestureRecognizer *)g {
  if (g.state != UIGestureRecognizerStateEnded) return;
  if (g.rotation == 0.0) return;
  const gesturebind::Gesture which =
      g.rotation > 0.0 ? gesturebind::Gesture::RotateClockwise
                       : gesturebind::Gesture::RotateCounterClockwise;
  performGestureAction(liveAction(which), gesturebind::gestureName(which));
}

// THE LONG PRESSES. Two of them: the ONE-finger one is routed by WHERE IT
// LANDED, and the two-finger one is a plain global binding.
//
// SUPERSEDED, and kept because reversing a device-feel ruling deserves a record.
// The 2026-08-22 ruling was *"in zen mode, long tap is select button (please use
// apple for this so everything works as expected)"* -- fired at RECOGNITION
// (.began, the stock iOS long-press feel). On 2026-08-27 a second, longer hold
// was added to toggle zen, one hold crossed both thresholds, and the select was
// moved to the LIFT so a long hold could suppress it -- which worked and cost
// the feel. Splitting by POSITION the same day removed the collision at its
// root: a touch is either above the paper or it is not, so the two actions can
// share one threshold and the select fires under the finger again. The 0.75 s
// itself has never moved ("long tap select is too fast. make at least 1.5x
// longer", 2026-08-22).
//
// The SPOIL stays at .began, and only for the one-finger hold: no double fire
// with the SDL deliberate tap is already true by construction (the tap's 400 ms
// ceiling answers None for anything held to 0.75 s), but the same finger streams
// into SDL, so spoiling at recognition keeps that from depending on event
// ordering. A two-finger hold never had a tap candidate to spoil -- the
// candidate is spoiled by the second finger before it can arm.
- (void)hold:(UILongPressGestureRecognizer *)g {
  const gesturebind::Gesture which = rowOf(g);
  if (which == gesturebind::Gesture::Count) return;

  if (gesturebind::row(which).fingers > 1) {
    switch (g.state) {
      case UIGestureRecognizerStateBegan:
        // The latch, for the same reason zenhold::Hold::claim() exists: UIKit
        // re-delivers .began on some paths and two toggles in one gesture
        // cancel out, which reads on device as the gesture doing nothing.
        if ([g_holdFired containsObject:g]) break;
        [g_holdFired addObject:g];
        performGestureAction(liveAction(which),
                             gesturebind::gestureName(which));
        break;
      case UIGestureRecognizerStateEnded:
      case UIGestureRecognizerStateCancelled:
      case UIGestureRecognizerStateFailed:
        [g_holdFired removeObject:g];
        break;
      default:
        break;
    }
    return;
  }

  switch (g.state) {
    case UIGestureRecognizerStateBegan: {
      g_hold.begin();
      g_hold.noteTouches(static_cast<int>(g.numberOfTouches));
      CrossPointZen_spoilTapCandidate();
      if (CrossPointMixer_isPresented() || CrossPointInkPicker_isPresented()) {
        SDL_Log("[zen] hold swallowed (palette sheet presented)");
        g_hold.cancel();
        break;
      }
      // WHERE IT LANDED decides which of the three zones it is in, and the
      // zone decides which row (or the global layer) answers. Read at .began
      // rather than remembered from touch-down: UIKit's allowableMovement
      // (10 pt, left at the default) bounds how far the finger can have
      // drifted and still be recognized, so the two points are within a
      // fingertip of each other. A touch that drifts further never reaches
      // .began at all.
      //
      // A poisoned hold resolves to nothing without consulting the store: a
      // second finger on the glass is not a deliberate press.
      float yPx = 0.0f;
      const gesturebind::Zone z = zoneOf(g, &yPx);
      const gesturebind::Gesture zoneRow =
          gesturebind::zoneGesture(gesturebind::OneFinger::Hold, z);
      const gesturebind::Gesture globalRow =
          gesturebind::globalGesture(gesturebind::OneFinger::Hold);
      const int zoneStored =
          zoneRow == gesturebind::Gesture::Count
              ? 0
              : CrossPointPrefs_gestureBinding(static_cast<int>(zoneRow));
      const int globalStored =
          CrossPointPrefs_gestureBinding(static_cast<int>(globalRow));
      const gesturebind::Action a =
          g_hold.poisoned()
              ? gesturebind::Action::Nothing
              : gesturebind::oneFingerAction(gesturebind::OneFinger::Hold, z,
                                             g_zenOn, zoneStored, globalStored);
      SDL_Log("[zen] hold at y=%.0f px (paper %.0f..%.0f) %s, zen %s -> %s", yPx,
              CrossPointZen_cardTopPx(), CrossPointZen_paperBottomPx(),
              gesturebind::zoneName(z), g_zenOn ? "on" : "off",
              gesturebind::actionName(a));
      // The gesture string carries the ZONE, because it is also what the
      // `[zen] toggle` line reports as the toggle's source -- and a toggle log
      // that cannot say which gesture and which zone produced it is a log that
      // cannot confirm the binding on device.
      char what[96];
      SDL_snprintf(what, sizeof(what), "hold %s", gesturebind::zoneName(z));
      // claim() is the latch that survives UIKit re-delivering .began (it does
      // on some paths, and two toggles in one gesture cancel out -- which reads
      // on device as the gesture doing nothing at all). It is asked only when
      // something is actually going to happen, so an unbound hold leaves the
      // tracker unlatched exactly as a poisoned one does.
      if (a != gesturebind::Action::Nothing && g_hold.claim())
        performGestureAction(a, what);
      break;
    }
    case UIGestureRecognizerStateChanged:
      // Poison only. The action already fired at .began and is latched, so a
      // second finger arriving now cannot un-fire it -- it can only stop a
      // re-delivered .began from firing again.
      g_hold.noteTouches(static_cast<int>(g.numberOfTouches));
      break;
    case UIGestureRecognizerStateCancelled:
    case UIGestureRecognizerStateFailed:
      g_hold.cancel();
      break;
    default:
      break;
  }
}

// A GESTURE THAT SHIPS INERT MAY NEVER PREVENT ONE THAT SHIPS BOUND.
//
// This is the only thing the delegate does, and it exists because installing a
// recognizer is not free. UIGestureRecognizer's -canPreventGestureRecognizer:
// defaults to YES, so a recognizer that recognizes first stops the others --
// and the 2026-08-28 re-cut ADDED three shapes that overlap gestures the app
// already had:
//
//   * ROTATION vs PINCH. Both continuous, both two-finger. A real pinch always
//     carries a few degrees of twist, so the arbitration can go to rotation --
//     and rotation ships bound to Nothing while pinch ships bound to the font
//     step. Without this the owner would lose pinches he has today, on a
//     gesture he has already reported as not working once (2026-08-22).
//   * THE 2-FINGER HOLD vs THE 2-FINGER SWIPES. A swipe that starts with a
//     pause crosses 0.75 s and begins the hold, which then fails the swipe.
//   * The one-finger VERTICAL swipes, which overlap nothing today but are new
//     for the same reason.
//
// So: simultaneity is granted iff EITHER side ships inert
// (gesturebind::shipsInert). Between two rows that both ship bound the answer is
// NO, which is byte-for-byte what UIKit does with no delegate -- so arbitration
// among the gestures that existed before the re-cut is untouched, and the
// "defaults reproduce the previous build" property is true of the RECOGNIZERS
// and not only of the bindings table.
//
// It is keyed on the DEFAULT rather than on the live binding deliberately: the
// answer is then a constant of the build, so nothing has to be rebuilt when a
// binding changes in Settings.app -- which the app cannot be told about anyway
// while it is backgrounded. The alternative, installing only BOUND rows, was
// priced and rejected for exactly that reason; see gesturebind::shipsInert.
//
// (Two hold recognizers of the same touch count used to need a delegate of a
// different kind: the shorter press reaching .began stopped the longer one ever
// recognizing, and the zen toggle would have been silently dead. Splitting that
// rule by POSITION instead of by DURATION removed the pair; the two long
// presses that exist now differ in TOUCH COUNT and are mutually exclusive by
// construction.)
- (BOOL)gestureRecognizer:(UIGestureRecognizer *)a
    shouldRecognizeSimultaneouslyWithGestureRecognizer:(UIGestureRecognizer *)b {
  return gesturebind::shipsInert(rowOf(a)) || gesturebind::shipsInert(rowOf(b));
}

@end

// THE SHAKE CATCHER (owner 2026-08-22: "change reader font on shake in zen
// mode"; extended 2026-08-29: "making shake gesture work in single-finger
// mode"). Shake is not a gesture recognizer: UIKit delivers it as a MOTION
// event to the first responder, and SDL's view controller never overrides
// canBecomeFirstResponder (UIResponder's default NO — verified in
// SDL_uikitviewcontroller.m, whose only becomeFirstResponder is the hidden
// text field that raises the keyboard). So the seam is a small invisible
// responder view on the SDL view: zero frame, draws nothing, touches
// disabled, made first responder from the moment it attaches — in EITHER zen
// state, not only while zen is on. It fires the HAL's font-family step
// channel (HalGPIO::injectFontFamilyStep — consume-once, the reader polls it
// and cycles the family); SHAKE in CROSSPOINT_SIM_INPUT_SCRIPT drives the same
// channel headlessly.
//
// **This was zen-only until 2026-08-29, gated in TWO independent places**, and
// both had to move together or the fix would look complete and still not
// work: gesturebind::firesOutsideZen(Shake) (the action-resolution gate, in
// ios/GestureBindings.h) and this file's first-responder assignment, which
// used to run only inside `if (on)` in CrossPointZenRecognizers_setEnabled —
// so even with the action gate open, a shake landing while zen was off had no
// first responder to deliver the motion event to at all. See docs/zen-mode.md
// for the traced mechanism.
//
// Known ceiling, stated rather than hidden: motion events reach the FIRST
// responder only, so if something else takes that status (the keyboard's text
// field is the one candidate), a shake during that span is dropped. Zen has no
// text fields, but the reader outside zen can have one open; each
// CrossPointZenRecognizers_setEnabled call re-asserts the status, in both zen
// states now, which is the same recovery this always relied on.
@interface CPXShakeCatcher : UIView
@end

@implementation CPXShakeCatcher

- (BOOL)canBecomeFirstResponder {
  return YES;
}

- (void)motionEnded:(UIEventSubtype)motion withEvent:(UIEvent *)event {
  if (motion != UIEventSubtypeMotionShake) {
    [super motionEnded:motion withEvent:event];
    return;
  }
  // Fires in EITHER zen state (owner 2026-08-29: "making shake gesture work
  // in single-finger mode" -- his own term for not-zen, docs/zen-mode.md).
  // The gate is the GESTURE's, not this method's:
  // gesturebind::firesOutsideZen(Shake) is now true, so actionFor resolves
  // whatever the shake is bound to regardless of g_zenOn. (Before this it was
  // false and actionFor always answered Nothing out of zen, whatever the
  // shake was bound to -- see docs/zen-mode.md for the full trace.) The
  // palette-sheet swallow is inside performGestureAction with every other
  // gesture's.
  performGestureAction(liveAction(gesturebind::Gesture::Shake),
                       gesturebind::gestureName(gesturebind::Gesture::Shake));
}

@end

namespace {

CPXZenGestureHandler *g_handler = nil;
// The shake catcher: attached with the rest; first-responder status tracks
// the zen flag (see the class comment above).
CPXShakeCatcher *g_shake = nil;

UIView *sdlView(void) {
  int count = 0;
  SDL_Window **wins = SDL_GetWindows(&count);
  SDL_Window *win = (wins && count > 0) ? wins[0] : nullptr;
  SDL_free(wins);
  if (!win) return nil;
  UIWindow *uiWindow = (__bridge UIWindow *)SDL_GetPointerProperty(
      SDL_GetWindowProperties(win), SDL_PROP_WINDOW_UIKIT_WINDOW_POINTER,
      nullptr);
  return uiWindow.rootViewController.view;
}

void tameRecognizer(UIGestureRecognizer *r) {
  // SDL must keep seeing every touch: the deliberate tap and the pad both live
  // on the SDL finger stream.
  r.cancelsTouchesInView = NO;
  r.delaysTouchesBegan = NO;
  r.delaysTouchesEnded = NO;
}

void install(UIView *view, UIGestureRecognizer *r, gesturebind::Gesture g) {
  tameRecognizer(r);
  // Without this the simultaneity rule above is never asked, and a
  // ships-inert recognizer silently starts preventing a ships-bound one.
  r.delegate = g_handler;
  [view addGestureRecognizer:r];
  [g_installed addObject:r];
  [g_installedRow addObject:@(static_cast<int>(g))];
}

// Enabled tracks zen, except for the row that must fire on the way IN.
void applyEnabled(void) {
  for (NSUInteger i = 0; i < g_installed.count; ++i) {
    const gesturebind::Gesture g =
        static_cast<gesturebind::Gesture>(g_installedRow[i].intValue);
    g_installed[i].enabled = (g_zenOn || rowIsAlwaysOn(g)) ? YES : NO;
  }
}

// BUILD THE SET, ONCE, STRAIGHT FROM THE TABLE. Every global row that names a
// recognizer family gets exactly one object; the shake is a responder rather
// than a recognizer, and pinch/rotation each serve two rows off one object
// (they are one gesture to UIKit and two to a reader).
//
// Walking the table rather than writing thirteen constructors out means a row
// added to GestureBindings.h is installed by construction. A row whose family
// this switch does not handle is skipped in SILENCE only because the table's
// families are exhaustive here -- if that stops being true, the enumeration
// logged at the foot is what says so.
void buildRecognizers(UIView *view) {
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const gesturebind::Gesture g = static_cast<gesturebind::Gesture>(i);
    if (gesturebind::isZoneRow(g)) continue;  // an override, not a gesture
    const gesturebind::Row &r = gesturebind::row(g);
    switch (r.family) {
      case gesturebind::Family::Tap: {
        // The 1-finger tap belongs to SDL's classifier (ZenVerbs.h), which has
        // the deliberate-tap discipline the owner asked for; only the
        // two-finger tap is UIKit's.
        if (r.fingers < 2) continue;
        UITapGestureRecognizer *t =
            [[UITapGestureRecognizer alloc] initWithTarget:g_handler
                                                    action:@selector(tap:)];
        t.numberOfTapsRequired = 1;
        t.numberOfTouchesRequired = static_cast<NSUInteger>(r.fingers);
        install(view, t, g);
        break;
      }
      case gesturebind::Family::Swipe: {
        UISwipeGestureRecognizer *s =
            [[UISwipeGestureRecognizer alloc] initWithTarget:g_handler
                                                      action:@selector(swipe:)];
        s.direction = uikitSwipeDir(r.dir);
        s.numberOfTouchesRequired = static_cast<NSUInteger>(r.fingers);
        install(view, s, g);
        break;
      }
      case gesturebind::Family::LongPress: {
        // MOVEMENT ALLOWANCE IS APPLE'S DEFAULT (10 pt), deliberately, and it
        // is the first thing to suspect if a device report says a hold does not
        // fire: a finger that drifts past 10 pt inside the 0.75 s fails the
        // recognizer. Left at the default because 10 pt at the phone's display
        // scale is 30 device px, which is the 28 px slop ZenVerbs.h uses for a
        // deliberate touch -- the repo's own answer to the same question -- and
        // because inventing a number here would be inventing device feel.
        UILongPressGestureRecognizer *lp = [[UILongPressGestureRecognizer alloc]
            initWithTarget:g_handler
                    action:@selector(hold:)];
        lp.numberOfTouchesRequired = static_cast<NSUInteger>(r.fingers);
        lp.minimumPressDuration = zenhold::kHoldMs / 1000.0;
        install(view, lp, g);
        break;
      }
      case gesturebind::Family::Pinch: {
        // ONE UIPinchGestureRecognizer serves Pinch and Spread; it is
        // registered under the `Pinch` row and picks in/out from the scale.
        if (g != gesturebind::Gesture::Pinch) continue;
        install(view,
                [[UIPinchGestureRecognizer alloc] initWithTarget:g_handler
                                                          action:@selector
                                                          (pinch:)],
                g);
        break;
      }
      case gesturebind::Family::Rotate: {
        if (g != gesturebind::Gesture::RotateClockwise) continue;
        install(view,
                [[UIRotationGestureRecognizer alloc] initWithTarget:g_handler
                                                             action:@selector
                                                             (rotate:)],
                g);
        break;
      }
      case gesturebind::Family::Shake:
        break;  // the catcher below, not a recognizer
    }
  }

  applyEnabled();

  // WHAT IS ACTUALLY INSTALLED, enumerated from the array rather than described
  // from memory. This line is the only off-device confirmation that the attach
  // happened at all and that the set matches the table, and a stale
  // enumeration is worse than none -- so it is built from the array and cannot
  // go stale.
  NSMutableString *names = [NSMutableString string];
  for (NSUInteger i = 0; i < g_installed.count; ++i) {
    const gesturebind::Gesture g =
        static_cast<gesturebind::Gesture>(g_installedRow[i].intValue);
    if (names.length) [names appendString:@", "];
    [names appendFormat:@"%s%s", gesturebind::gestureName(g),
                        rowIsAlwaysOn(g) ? "*" : ""];
  }
  // Counted from the table, not typed in: an earlier version of this line
  // carried "(17 gestures, 12 zone overrides)" as a literal inside the very log
  // whose comment promises it cannot go stale.
  int globals = 0, zones = 0, inert = 0;
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const gesturebind::Gesture g = static_cast<gesturebind::Gesture>(i);
    if (gesturebind::isZoneRow(g)) {
      zones++;
    } else {
      globals++;
      if (gesturebind::shipsInert(g)) inert++;
    }
  }
  SDL_Log("[zen] recognizers attached: %lu objects for %d configurable rows "
          "(%d gestures, %d zone overrides; %d gestures ship inert and may not "
          "prevent a bound one); hold %.2f s; * = fires outside zen; the "
          "1-finger tap stays on the SDL classifier [%s]",
          (unsigned long)g_installed.count, gesturebind::kGestureCount, globals,
          zones, inert, zenhold::kHoldMs / 1000.0,
          names.length ? names.UTF8String : "none");
}

// WHAT EVERY GESTURE IS ACTUALLY BOUND TO, once, at attach. On a device this is
// the only way to see that a Settings.app change reached the app at all -- a
// binding that did not take looks exactly like a gesture the phone never
// delivered. Printed for every row, defaults included, so a report of "gesture
// X does nothing" can be answered from the log the owner already has.
void logBindings(void) {
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const gesturebind::Gesture which = static_cast<gesturebind::Gesture>(i);
    const int stored = CrossPointPrefs_gestureBinding(static_cast<int>(which));
    // A zone row printing `inherit` is the SHIPPED state, not a fault: it
    // means the global row above answers for that zone.
    // "set" MUST come from the PERSISTENT domain, not from the value.
    // -integerForKey: searches the registration domain too, and
    // ensureDefaults() registers every DefaultValue in Root.plist -- so an
    // untouched gesture answers with its shipped action and this line
    // printed `set` for every row on a clean install until it asked the
    // right question. That made the log say the opposite of the truth about
    // the one thing it exists to answer.
    SDL_Log("[zen]   %-28s -> %-16s (%s%s)", gesturebind::gestureName(which),
            gesturebind::actionName(gesturebind::resolve(which, stored)),
            CrossPointPrefs_gestureBindingIsExplicit(static_cast<int>(which))
                ? "set"
                : "default",
            gesturebind::firesOutsideZen(which) ? ", always on" : "");
  }
}

}  // namespace

// Attach on the first call IN EITHER STATE (the always-on row must be live from
// boot), then flip the zen-only recognizers' .enabled with the zen flag. Main
// queue: UIKit, and the callers sit on the SDL/firmware loop.
extern "C" void CrossPointZenRecognizers_setEnabled(bool on) {
  dispatch_async(dispatch_get_main_queue(), ^{
    if (!g_handler) {
      UIView *view = sdlView();
      if (!view) {
        SDL_Log("[zen] recognizers: no SDL view yet, will attach next call");
        return;
      }
      g_handler = [CPXZenGestureHandler new];
      g_installed = [NSMutableArray array];
      g_installedRow = [NSMutableArray array];
      g_holdFired = [NSMutableSet set];
      buildRecognizers(view);

      // The shake catcher: invisible (zero frame, no drawing, no touches —
      // shake arrives as a motion event, not a touch, so disabling user
      // interaction costs nothing) and parked on the SDL view so it sits in
      // the window's responder graph.
      g_shake = [[CPXShakeCatcher alloc] initWithFrame:CGRectZero];
      g_shake.userInteractionEnabled = NO;
      [view addSubview:g_shake];

      logBindings();
    }
    g_zenOn = on;
    applyEnabled();
    // First-responder status for the shake, asserted on EVERY call regardless
    // of `on` — the shake fires in both zen and single-finger mode since
    // 2026-08-29 (owner: "making shake gesture work in single-finger mode"),
    // so it must hold the status in either state, not only while zen is on.
    // Before this it resigned in the `else` branch, which was the second of
    // the two independent gates keeping the shake zen-only (the first is
    // gesturebind::firesOutsideZen(Shake) in GestureBindings.h) — resigning
    // here left nothing to become first responder out of zen even after that
    // gate opened. Still re-asserted on every call rather than once: SDL's
    // text field takes the status whenever the keyboard rises, and nothing
    // gives it back.
    const BOOL got = [g_shake becomeFirstResponder];
    SDL_Log("[zen] shake catcher %s first responder",
            got ? "is" : "FAILED to become");
    SDL_Log("[zen] verb recognizers %s", on ? "enabled" : "disabled");
  });
}
