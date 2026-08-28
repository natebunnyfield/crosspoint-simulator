// Native UIKit gesture recognizers for every zen verb that MOVES.
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
//       -> NATIVE RECOGNIZERS for all motion, SDL for the deliberate tap only.
//
// DIVISION OF LABOR (one owner per gesture): EVERY multi-finger gesture and
// all swipes are Apple; SDL keeps the 1-finger deliberate tap alone.
//   * everything that travels — 1- and 2-finger swipes, pinch/spread — and
//     the multi-finger taps (2-finger select, 4-finger power) are THESE
//     recognizers, active only while zen is on. Recognition is Apple's; this
//     file only maps a recognized gesture to gpio.queueButtonTap.
//   * the 3-FINGER ZEN TOGGLE is a recognizer too (owner 2026-08-22: "be
//     sure to swap 3 finger tap to apple", retiring the SDL ZenGesture
//     detector) — but unlike the verb recognizers it stays ENABLED IN BOTH
//     MODES, because it must fire while zen is OFF to get in. It calls the
//     shim's CrossPointZen_toggleFromRecognizer(), which also spoils the SDL
//     tap candidate and classifier so a toggle cannot leak a page-forward
//     tap — the one seam the native move creates.
//   * the 1-finger deliberate TAP stays on the SDL classifier (ZenVerbs.h)
//     with its pure-tested gates (28 px slop, 400 ms).
//   * the ONE-FINGER HOLD TO TOGGLE (owner 2026-08-27, "holding down one
//     finger longer than five seconds toggles zen and single finger modes",
//     retuned to THREE seconds by him the same day) is a
//     second always-enabled recognizer beside the 3-finger tap, for the same
//     reason: it toggles BOTH ways, so it must fire while zen is off. Its
//     collision with the zen long-press select is resolved in
//     ios/ZenHoldRouting.h — see the note above holdSelect: below.
//
// NO DOUBLE FIRE, BY CONSTRUCTION. A touch that fires a swipe recognizer has
// traveled far past the classifier's 28 px tap slop, so the classifier
// answers None for it; a deliberate tap stays inside the slop, which no swipe
// recognizer recognizes. The classifier no longer classifies motion at all —
// its only verb is the tap.
//
// COEXISTENCE. cancelsTouchesInView=NO and delaysTouchesBegan/Ended=NO on
// every recognizer, so SDL receives the finger stream untouched — the tap,
// the 3-finger toggle and the pad all live on the SDL finger stream.
//
// VOICEOVER. VoiceOver intercepts touches system-side and delivers its own
// gesture vocabulary before the app's recognizers see anything; with VO on,
// these recognizers simply do not receive the raw stream, the same as every
// other app-level recognizer. Attaching them steals nothing from VO — the
// accessibility surface stays CrossPointAccessibility's.
//
// WHAT EACH GESTURE DOES IS NOT IN THIS FILE. Owner ruling 2026-08-28
// (T-025): the bindings are Settings.app rows, in three groups -- above the
// paper, below the paper, and multi-finger -- and the rule lives in
// ios/GestureBindings.h, pure and truth-tabled in
// tests/gesture_bindings_test.cpp. This file recognizes and reports; it decides
// nothing. Three consequences worth knowing before editing here:
//
//   * THE SHIPPED DEFAULTS ARE WHAT THIS FILE USED TO HARDCODE, gesture by
//     gesture, so an install that never opens the setting behaves exactly as
//     build 156 did. They are written out beside gesturebind::defaultAction.
//   * ON THE PAPER IS FIXED and has no row: the tap and the swipes page, the
//     hold selects. Only the strip ABOVE the sheet and the band BELOW it are
//     configurable, judged from the landing point against the two boundaries
//     the layout already publishes (g_cardTopPx and the paper's bottom).
//   * ZEN SCOPE IS UNCHANGED and is a property of the GESTURE, never of the
//     action bound to it. The same two gestures fire outside zen as before --
//     the 3-finger tap and the hold above the paper -- whatever they hold. Zen
//     may be left unbound entirely, deliberately and with no guard: the
//     configuration is in Settings.app, outside the reader, so it is always
//     recoverable.
//
// VERIFICATION. UIKit recognizers cannot be driven by pushed SDL events (they
// live above SDL, on the UIKit touch pipeline, which neither SDL_PushEvent
// nor simctl can synthesize into) — so the recognizer paths are
// device-confirm only, which is acceptable now that the recognition itself is
// Apple's. What CAN be proven off-device: the wiring compiles, attaches (the
// "[zen] recognizers attached" log at first zen enable), and the SDL tap path
// still works with recognizers attached.

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
// gesture, and is what the one `[zen] toggle` line reports — two gestures reach
// this now (the 3-finger tap and the one-finger hold) and a log that cannot
// tell them apart is a log that cannot confirm either on device.
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
// it) can gate on zen the way the verb recognizers do.
bool g_zenOn = false;

// THE ONE-FINGER HOLD PAIR. Declared up here because the delegate that lets
// them recognize SIMULTANEOUSLY has to name them, and the delegate is a method
// on the handler below.
//
//   g_lpHold    0.75 s, ALWAYS ON (rides beside the 3-finger tap)
//               above the paper -> toggle; on it -> select, zen only
//
// Without the delegate the pair does not work at all: UIGestureRecognizer's
// default -canPreventGestureRecognizer: is YES, so the 0.75 s recognizer
// reaching .began would prevent the longer one from ever recognizing — in zen the
// toggle would simply never fire, silently, which is precisely the failure the
// routing header exists to make impossible.
UILongPressGestureRecognizer *g_lpHold = nil;

// The routing state for the hold in flight (ios/ZenHoldRouting.h). One hold at
// a time by construction: a second finger poisons it.
zenhold::Hold g_hold;

// Who owns g_hold for the hold currently in flight. Latched at .began of the
// toggle recognizer and NOT re-read during the gesture: the toggle flips
// g_zenOn under us, so re-asking would hand the .ended to the wrong owner and
// leave the tracker dirty — the very failure this exists to fix.
bool g_holdSelfManaged = false;

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

// WHAT THIS GESTURE IS BOUND TO RIGHT NOW. Two fetches and one pure call: the
// stored integer from Settings.app, and gesturebind::actionFor to resolve it
// against the zen gate and this gesture's default. Nothing decides anything
// here -- see ios/GestureBindings.h, which owns the whole rule.
gesturebind::Action liveAction(gesturebind::Gesture g) {
  return gesturebind::actionFor(
      g, g_zenOn, CrossPointPrefs_gestureBinding(static_cast<int>(g)));
}

// WHERE A ONE-FINGER GESTURE LANDED. locationInView is in POINTS and the
// published boundaries are in DEVICE PIXELS, so one has to be converted; the
// view's own contentScaleFactor is the conversion the rest of the layout
// already uses.
//
// This is the SAME hit test the one-finger hold has used since 2026-08-27, with
// one boundary added -- deliberately not a second one written beside it. The
// horizontal swipes are the only travelling gestures that consult it, and a
// horizontal swipe barely moves in y, so the recognition point and the landing
// point sit in the same band.
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
  const int btn = gesturebind::buttonFor(a);
  if (btn == gesturebind::kNoButton) return;  // Unset never reaches here
  SDL_Log("[zen] %s -> %s (button %d)", what, gesturebind::actionName(a), btn);
  gpio.queueButtonTap(static_cast<uint8_t>(btn), 60);
}
}  // namespace

@interface CPXZenGestureHandler : NSObject <UIGestureRecognizerDelegate>
@end

@implementation CPXZenGestureHandler

// A ONE-FINGER GESTURE, resolved by WHERE IT LANDED and performed. The zone is
// the only thing this adds over the multi-finger path: above and below the
// paper are Settings.app rows, and the paper itself is fixed by ruling.
- (void)oneFinger:(gesturebind::OneFinger)kind at:(UIGestureRecognizer *)g {
  float yPx = 0.0f;
  const gesturebind::Zone z = zoneOf(g, &yPx);
  const gesturebind::Gesture which = gesturebind::oneFingerGesture(kind, z);
  // Nothing is stored for the paper itself -- oneFingerAction ignores this
  // argument there, and reading a key that does not exist would be the first
  // step toward one existing.
  const int stored =
      which == gesturebind::Gesture::Count
          ? 0
          : CrossPointPrefs_gestureBinding(static_cast<int>(which));
  const gesturebind::Action a =
      gesturebind::oneFingerAction(kind, z, g_zenOn, stored);
  char what[128];
  SDL_snprintf(what, sizeof(what), "%s %s the paper (y=%.0f, top %.0f, bottom %.0f, zen %s)",
               gesturebind::oneFingerName(kind), gesturebind::zoneName(z), yPx,
               CrossPointZen_cardTopPx(), CrossPointZen_paperBottomPx(),
               g_zenOn ? "on" : "off");
  performGestureAction(a, what);
}

// One action for every swipe: each recognizer carries exactly one direction
// and one touch count, so reading them back is unambiguous.
//
// THE MAPPING IS NO LONGER HERE. Since T-025 (owner 2026-08-28) every swipe is
// a row in Settings.app and the answer comes from ios/GestureBindings.h; the
// SHIPPED DEFAULTS are the mapping this switch used to hardcode, so an install
// that never opens the setting swipes exactly as it did before. That mapping is
// written out beside gesturebind::defaultAction, where the test can read it.
//
// One-finger swipes are LEFT and RIGHT only -- the app has never had a
// one-finger vertical swipe and none was added, so the two vertical cases fall
// through for one finger exactly as they always did.
- (void)swipe:(UISwipeGestureRecognizer *)g {
  const bool two = g.numberOfTouchesRequired >= 2;
  if (two) {
    gesturebind::Gesture which;
    switch (g.direction) {
      case UISwipeGestureRecognizerDirectionLeft:
        which = gesturebind::Gesture::TwoFingerSwipeLeft;
        break;
      case UISwipeGestureRecognizerDirectionRight:
        which = gesturebind::Gesture::TwoFingerSwipeRight;
        break;
      case UISwipeGestureRecognizerDirectionUp:
        which = gesturebind::Gesture::TwoFingerSwipeUp;
        break;
      case UISwipeGestureRecognizerDirectionDown:
        which = gesturebind::Gesture::TwoFingerSwipeDown;
        break;
      default:
        return;
    }
    performGestureAction(liveAction(which), gesturebind::gestureName(which));
    return;
  }
  switch (g.direction) {
    case UISwipeGestureRecognizerDirectionLeft:
      [self oneFinger:gesturebind::OneFinger::SwipeLeft at:g];
      break;
    case UISwipeGestureRecognizerDirectionRight:
      [self oneFinger:gesturebind::OneFinger::SwipeRight at:g];
      break;
    default:
      break;
  }
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

- (void)twoTap:(UITapGestureRecognizer *)g {
  performGestureAction(liveAction(gesturebind::Gesture::TwoFingerTap),
                       gesturebind::gestureName(gesturebind::Gesture::TwoFingerTap));
}

- (void)fourTap:(UITapGestureRecognizer *)g {
  performGestureAction(liveAction(gesturebind::Gesture::FourFingerTap),
                       gesturebind::gestureName(gesturebind::Gesture::FourFingerTap));
}

// THE ONE-FINGER HOLD, routed by WHERE IT LANDED.
//
// Three zones since T-025 (owner 2026-08-28) and two before it: above the paper
// and below it are Settings.app rows, the paper itself is fixed at Select. The
// rule is ios/GestureBindings.h; ios/ZenHoldRouting.h keeps only the 0.75 s
// threshold and the tracker for the hold in flight.
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
// The SPOIL stays at .began. No double fire with the SDL deliberate tap is
// already true by construction (the tap's 400 ms ceiling answers None for
// anything held to 0.75 s), but the same finger streams into SDL, so spoiling at
// recognition keeps that from depending on event ordering -- the same
// belt-and-suspenders as the 3-finger toggle.
- (void)hold:(UILongPressGestureRecognizer *)g {
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
      // zone decides which row (or the fixed paper) answers. Read at .began
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
      const gesturebind::Gesture which =
          gesturebind::oneFingerGesture(gesturebind::OneFinger::Hold, z);
      const int stored =
          which == gesturebind::Gesture::Count
              ? 0
              : CrossPointPrefs_gestureBinding(static_cast<int>(which));
      const gesturebind::Action a =
          g_hold.poisoned()
              ? gesturebind::Action::Nothing
              : gesturebind::oneFingerAction(gesturebind::OneFinger::Hold, z,
                                             g_zenOn, stored);
      SDL_Log("[zen] hold at y=%.0f px (paper %.0f..%.0f) %s, zen %s -> %s", yPx,
              CrossPointZen_cardTopPx(), CrossPointZen_paperBottomPx(),
              gesturebind::zoneName(z), g_zenOn ? "on" : "off",
              gesturebind::actionName(a));
      // claim() is the latch that survives UIKit re-delivering .began (it does
      // on some paths, and two toggles in one gesture cancel out -- which reads
      // on device as the gesture doing nothing at all). It is asked only when
      // something is actually going to happen, so an unbound hold leaves the
      // tracker unlatched exactly as a poisoned one does.
      // The gesture string carries the ZONE, because it is also what the
      // `[zen] toggle` line reports as the toggle's source -- and a toggle log
      // that cannot say which gesture and which zone produced it is a log that
      // cannot confirm the binding on device.
      char what[96];
      SDL_snprintf(what, sizeof(what), "hold %s the paper",
                   gesturebind::zoneName(z));
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

- (void)threeTap:(UITapGestureRecognizer *)g {
  performGestureAction(liveAction(gesturebind::Gesture::ThreeFingerTap),
                       gesturebind::gestureName(gesturebind::Gesture::ThreeFingerTap));
}

// NO SIMULTANEITY DELEGATE, and its absence is the point.
//
// Two hold recognizers used to need one. UIGestureRecognizer's default
// -canPreventGestureRecognizer: is YES, so the shorter press reaching .began
// stopped the longer one ever recognizing, and the toggle would have been
// silently dead in zen with nothing in the log to say so. Splitting the rule by
// POSITION instead of by DURATION leaves ONE hold recognizer, so there is no
// pair left to exempt and no delegate to get wrong.

@end

// THE SHAKE CATCHER (owner 2026-08-22: "change reader font on shake in zen
// mode"). Shake is not a gesture recognizer: UIKit delivers it as a MOTION
// event to the first responder, and SDL's view controller never overrides
// canBecomeFirstResponder (UIResponder's default NO — verified in
// SDL_uikitviewcontroller.m, whose only becomeFirstResponder is the hidden
// text field that raises the keyboard). So the seam is a small invisible
// responder view on the SDL view: zero frame, draws nothing, touches
// disabled, made first responder while zen is on. It fires the HAL's
// font-family step channel (HalGPIO::injectFontFamilyStep — consume-once, the
// reader polls it and cycles the family); SHAKE in
// CROSSPOINT_SIM_INPUT_SCRIPT drives the same channel headlessly.
//
// Known ceiling, stated rather than hidden: motion events reach the FIRST
// responder only, so if something else takes that status while zen is on (the
// keyboard's text field is the one candidate), a shake during that span is
// dropped. Zen has no text fields; each zen enable re-asserts the status.
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
  // Zen-only, and the gate is the GESTURE's, not this method's:
  // gesturebind::firesOutsideZen(Shake) is false, so actionFor answers Nothing
  // while zen is off whatever the shake is bound to. The palette-sheet swallow
  // is inside performGestureAction with every other gesture's.
  performGestureAction(liveAction(gesturebind::Gesture::Shake),
                       gesturebind::gestureName(gesturebind::Gesture::Shake));
}

@end

namespace {

CPXZenGestureHandler *g_handler = nil;
// The zen-only VERB recognizers: enabled tracks the zen flag.
NSArray<UIGestureRecognizer *> *g_recognizers = nil;
// The 3-finger TOGGLE: attached with the rest but ALWAYS enabled — it is the
// way INTO zen, so it must fire while the verb recognizers are off.
UITapGestureRecognizer *g_toggle = nil;
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
  // SDL must keep seeing every touch: the deliberate tap, the 3-finger
  // toggle and the pad all live on the SDL finger stream.
  r.cancelsTouchesInView = NO;
  r.delaysTouchesBegan = NO;
  r.delaysTouchesEnded = NO;
}

}  // namespace

// Attach on the first call IN EITHER STATE (the toggle must be live from
// boot, or there is no way into zen), then flip the verb recognizers'
// .enabled with the zen flag; the toggle stays enabled. Main queue: UIKit,
// and the callers sit on the SDL/firmware loop.
extern "C" void CrossPointZenRecognizers_setEnabled(bool on) {
  dispatch_async(dispatch_get_main_queue(), ^{
    if (!g_recognizers) {
      UIView *view = sdlView();
      if (!view) {
        SDL_Log("[zen] recognizers: no SDL view yet, will attach next call");
        return;
      }
      g_handler = [CPXZenGestureHandler new];
      NSMutableArray<UIGestureRecognizer *> *rs = [NSMutableArray array];

      const UISwipeGestureRecognizerDirection dirs[4] = {
          UISwipeGestureRecognizerDirectionLeft,
          UISwipeGestureRecognizerDirectionRight,
          UISwipeGestureRecognizerDirectionUp,
          UISwipeGestureRecognizerDirectionDown};
      // 1-finger: left/right only (pages). 2-finger: all four directions.
      for (int touches = 1; touches <= 2; ++touches) {
        for (int i = 0; i < (touches == 1 ? 2 : 4); ++i) {
          UISwipeGestureRecognizer *s = [[UISwipeGestureRecognizer alloc]
              initWithTarget:g_handler
                      action:@selector(swipe:)];
          s.direction = dirs[i];
          s.numberOfTouchesRequired = touches;
          [rs addObject:s];
        }
      }

      UIPinchGestureRecognizer *p = [[UIPinchGestureRecognizer alloc]
          initWithTarget:g_handler
                  action:@selector(pinch:)];
      [rs addObject:p];

      UITapGestureRecognizer *t2 = [[UITapGestureRecognizer alloc]
          initWithTarget:g_handler
                  action:@selector(twoTap:)];
      t2.numberOfTapsRequired = 1;
      t2.numberOfTouchesRequired = 2;
      [rs addObject:t2];

      UITapGestureRecognizer *t4 = [[UITapGestureRecognizer alloc]
          initWithTarget:g_handler
                  action:@selector(fourTap:)];
      t4.numberOfTapsRequired = 1;
      t4.numberOfTouchesRequired = 4;
      [rs addObject:t4];

      for (UIGestureRecognizer *r in rs) {
        tameRecognizer(r);
        [view addGestureRecognizer:r];
      }
      g_recognizers = rs;

      // The toggle, separate from the verb set: always enabled (see above).
      g_toggle = [[UITapGestureRecognizer alloc]
          initWithTarget:g_handler
                  action:@selector(threeTap:)];
      g_toggle.numberOfTapsRequired = 1;
      g_toggle.numberOfTouchesRequired = 3;
      tameRecognizer(g_toggle);
      [view addGestureRecognizer:g_toggle];

      // THE ONE-FINGER HOLD. One recognizer, one threshold, two zones.
      //
      // ALWAYS ENABLED, like the 3-finger tap and unlike everything in the verb
      // set: above the paper it toggles, so it has to fire while zen is OFF or
      // there is no way back in. Below the paper it selects, and `hold:` gates
      // that on g_zenOn rather than on the recognizer being disabled -- which
      // is deliberate. The previous shape kept the select on a zen-only
      // recognizer, and because that recognizer owned the shared tracker's
      // lifecycle, the tracker went stale out of zen and the toggle died in one
      // mode. Gating the ACTION rather than the RECOGNIZER is what makes that
      // class of bug impossible here.
      //
      // There is no second hold recognizer now, so no simultaneity delegate:
      // the pair used to need one because UIKit's -canPreventGestureRecognizer:
      // defaults to YES and the shorter press would stop the longer one ever
      // recognizing.
      //
      // MOVEMENT ALLOWANCE IS APPLE'S DEFAULT (10 pt), deliberately, and it is
      // the first thing to suspect if a device report says the hold does not
      // fire: a finger that drifts past 10 pt inside the 0.75 s fails this
      // recognizer. Left at the default because 10 pt at the phone's display
      // scale is 30 device px, which is the 28 px slop ZenVerbs.h uses for a
      // deliberate touch -- the repo's own answer to the same question -- and
      // because inventing a number here would be inventing device feel.
      g_lpHold = [[UILongPressGestureRecognizer alloc]
          initWithTarget:g_handler
                  action:@selector(hold:)];
      g_lpHold.numberOfTouchesRequired = 1;
      g_lpHold.minimumPressDuration = zenhold::kHoldMs / 1000.0;
      tameRecognizer(g_lpHold);
      [view addGestureRecognizer:g_lpHold];

      // The shake catcher: invisible (zero frame, no drawing, no touches —
      // shake arrives as a motion event, not a touch, so disabling user
      // interaction costs nothing) and parked on the SDL view so it sits in
      // the window's responder graph.
      g_shake = [[CPXShakeCatcher alloc] initWithFrame:CGRectZero];
      g_shake.userInteractionEnabled = NO;
      [view addSubview:g_shake];

      // This line enumerates what is actually installed, so it has to move
      // whenever the set does — it is the only off-device confirmation that
      // the attach happened at all, and a stale enumeration is worse than
      // none.
      SDL_Log("[zen] recognizers attached "
              "(zen-only: 6 swipes, pinch, 2-tap, 4-tap; always on: 3-tap, "
              "1-finger hold %.2f s; shake catcher installed; %d bindings "
              "configurable in Settings.app)",
              zenhold::kHoldMs / 1000.0, gesturebind::kGestureCount);
      // WHAT EVERY GESTURE IS ACTUALLY BOUND TO, once, at attach. On a device
      // this is the only way to see that a Settings.app change reached the app
      // at all -- a binding that did not take looks exactly like a gesture the
      // phone never delivered. Printed for every row, defaults included, so a
      // report of "gesture X does nothing" can be answered from the log the
      // owner already has.
      for (int i = 0; i < gesturebind::kGestureCount; ++i) {
        const gesturebind::Gesture which = static_cast<gesturebind::Gesture>(i);
        const int stored =
            CrossPointPrefs_gestureBinding(static_cast<int>(which));
        // "set" MUST come from the PERSISTENT domain, not from the value.
        // -integerForKey: searches the registration domain too, and
        // ensureDefaults() registers every DefaultValue in Root.plist -- so an
        // untouched gesture answers with its shipped action and this line
        // printed `set` for all 18 rows on a clean install until it asked the
        // right question. That made the log say the opposite of the truth about
        // the one thing it exists to answer.
        SDL_Log("[zen]   %-26s -> %-16s (%s%s)", gesturebind::gestureName(which),
                gesturebind::actionName(gesturebind::resolve(which, stored)),
                CrossPointPrefs_gestureBindingIsExplicit(static_cast<int>(which))
                    ? "set"
                    : "default",
                gesturebind::firesOutsideZen(which) ? ", always on" : "");
      }
    }
    g_zenOn = on;
    for (UIGestureRecognizer *r in g_recognizers)
      r.enabled = on ? YES : NO;
    // First-responder status for the shake, asserted per enable rather than
    // once: SDL's text field takes the status whenever the keyboard rises,
    // and nothing gives it back.
    if (on) {
      const BOOL got = [g_shake becomeFirstResponder];
      SDL_Log("[zen] shake catcher %s first responder",
              got ? "is" : "FAILED to become");
    } else {
      [g_shake resignFirstResponder];
    }
    SDL_Log("[zen] verb recognizers %s", on ? "enabled" : "disabled");
  });
}
