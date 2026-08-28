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
//   * the 1-finger deliberate TAP (page forward) stays on the SDL classifier
//     (ZenVerbs.h) with its pure-tested gates (28 px slop, 400 ms).
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
// VERIFICATION. UIKit recognizers cannot be driven by pushed SDL events (they
// live above SDL, on the UIKit touch pipeline, which neither SDL_PushEvent
// nor simctl can synthesize into) — so the recognizer paths are
// device-confirm only, which is acceptable now that the recognition itself is
// Apple's. What CAN be proven off-device: the wiring compiles, attaches (the
// "[zen] recognizers attached" log at first zen enable), and the SDL tap path
// still works with recognizers attached.

#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

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
}  // namespace

@interface CPXZenGestureHandler : NSObject <UIGestureRecognizerDelegate>
@end

@implementation CPXZenGestureHandler

- (void)queueButton:(uint8_t)button as:(const char *)what {
  // The mixer sheet leaves the view under it hit-testable (pageSheet with an
  // undimmed medium detent); a gesture on the exposed page must not drive the
  // reader while the tray is up. Same rule as the shim's finger gate.
  if (CrossPointMixer_isPresented() || CrossPointInkPicker_isPresented()) {
    SDL_Log("[zen] recognizer %s swallowed (palette sheet presented)", what);
    return;
  }
  SDL_Log("[zen] recognizer %s -> button %d", what, (int)button);
  gpio.queueButtonTap(button, 60);
}

// One action for every swipe: each recognizer carries exactly one direction
// and one touch count, so reading them back is unambiguous. Mapping is the
// CURRENT post-swap table (owner 2026-08-22, "reading on one finger, sizing
// on two"): one finger drives the PAGE (front Left/Right), two fingers drive
// FONT SIZE — on this fork a SIDE tap is the font-size step
// (longPressButtonBehavior is constexpr FONT_SIZE_STEP), so BTN_DOWN steps
// the font +1 and BTN_UP steps it -1.
- (void)swipe:(UISwipeGestureRecognizer *)g {
  const bool two = g.numberOfTouchesRequired >= 2;
  switch (g.direction) {
    case UISwipeGestureRecognizerDirectionLeft:
      if (two)
        [self queueButton:HalGPIO::BTN_DOWN as:"2-swipe left (font +1)"];
      else
        [self queueButton:HalGPIO::BTN_RIGHT as:"1-swipe left (page forward)"];
      break;
    case UISwipeGestureRecognizerDirectionRight:
      if (two)
        [self queueButton:HalGPIO::BTN_UP as:"2-swipe right (font -1)"];
      else
        [self queueButton:HalGPIO::BTN_LEFT as:"1-swipe right (page back)"];
      break;
    case UISwipeGestureRecognizerDirectionDown:
      if (two) [self queueButton:HalGPIO::BTN_CONFIRM as:"2-swipe down (select)"];
      break;
    case UISwipeGestureRecognizerDirectionUp:
      if (two) [self queueButton:HalGPIO::BTN_BACK as:"2-swipe up (back)"];
      break;
    default:
      break;
  }
}

// One step per gesture, on the lift — not continuous. The reader repaginates
// per step, so a continuous pinch would queue a storm of font steps.
- (void)pinch:(UIPinchGestureRecognizer *)g {
  if (g.state != UIGestureRecognizerStateEnded) return;
  if (g.scale > 1.0)
    [self queueButton:HalGPIO::BTN_DOWN as:"spread (font +1)"];
  else if (g.scale < 1.0)
    [self queueButton:HalGPIO::BTN_UP as:"pinch (font -1)"];
}

- (void)twoTap:(UITapGestureRecognizer *)g {
  [self queueButton:HalGPIO::BTN_CONFIRM as:"2-finger tap (select)"];
}

- (void)fourTap:(UITapGestureRecognizer *)g {
  [self queueButton:HalGPIO::BTN_POWER as:"4-finger tap (power)"];
}

// Zen long-press = select (owner 2026-08-22: "in zen mode, long tap is select
// button (please use apple for this so everything works as expected)").
//
// SUPERSEDED 2026-08-27, and the superseded note is kept rather than deleted
// because it was a device-feel ruling and reversing one deserves a record.
// It read:
//
//   > Fires at RECOGNITION (.began, UIKit's default ~0.5 s and default
//   > movement allowance), not at release — the expected iOS long-press feel.
//
// It cannot stand beside the hold-to-toggle (owner 2026-08-27, "holding down
// one finger longer than five seconds toggles zen and single finger modes",
// retuned to three seconds the same day), because a multi-second hold crosses
// 0.75 s on its way there: firing at
// .began means one hold fires BOTH a select and a toggle. The owner ruled,
// presented with that cost explicitly: **select fires on LIFT.** A hold of
// 0.75 s .. kToggleMs selects when the finger comes up; a hold that reaches it
// toggles zen under the finger and the lift is silent. Exactly one action per
// hold. The 0.75 s threshold itself did NOT move — it was set from device feel
// on 2026-08-22 ("long tap select is too fast. make at least 1.5x longer") and
// only WHEN it fires changed.
//
// The routing is ios/ZenHoldRouting.h, pure and truth-tabled in
// tests/zen_hold_test.cpp, because both of its inversions are silent: a select
// that stops firing reads as a gesture the phone did not deliver, and a select
// that fires alongside the toggle reads as the toggle misfiring. This method
// only reports events into it.
//
// The SPOIL stays at .began. No double fire with the SDL deliberate tap is
// already true by construction (the tap's 400 ms ceiling answers None for
// anything held to 0.75 s), but the same finger streams into SDL, so spoiling
// at recognition keeps that from depending on event ordering — the same
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
      // WHERE IT LANDED decides what it does. locationInView is in POINTS and
      // g_cardTopPx is in DEVICE pixels, so one of them has to be converted;
      // the view's own contentScaleFactor is the conversion the rest of the
      // layout already uses.
      //
      // Read at .began rather than remembered from touch-down: UIKit's
      // allowableMovement (10 pt, left at the default) bounds how far the
      // finger can have drifted and still be recognized, so the two points are
      // within a fingertip of each other. A touch that drifts further than that
      // never reaches .began at all.
      const CGPoint loc = [g locationInView:g.view];
      const CGFloat scale = g.view ? g.view.contentScaleFactor : 1.0;
      const float yPx = static_cast<float>(loc.y * scale);
      const float paperTopPx = CrossPointZen_cardTopPx();
      const zenhold::Zone zone = yPx < paperTopPx ? zenhold::Zone::AbovePaper
                                                  : zenhold::Zone::OnPaper;
      const zenhold::Action a = g_hold.resolve(zone, g_zenOn);
      SDL_Log("[zen] hold at y=%.0f px (paper top %.0f) %s, zen %s -> %s", yPx,
              paperTopPx, zone == zenhold::Zone::AbovePaper ? "ABOVE" : "on",
              g_zenOn ? "on" : "off", zenhold::actionName(a));
      if (a == zenhold::Action::Toggle)
        CrossPointZen_toggleFromRecognizer("one-finger hold above the paper");
      else if (a == zenhold::Action::Select)
        [self queueButton:HalGPIO::BTN_CONFIRM as:"hold on the paper (select)"];
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
  if (CrossPointMixer_isPresented() || CrossPointInkPicker_isPresented()) {
    SDL_Log("[zen] recognizer 3-finger toggle swallowed (palette sheet presented)");
    return;
  }
  CrossPointZen_toggleFromRecognizer("3-finger tap");
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
  if (!g_zenOn) return;  // shake is a zen verb only
  if (CrossPointMixer_isPresented() || CrossPointInkPicker_isPresented()) {
    SDL_Log("[zen] shake swallowed (palette sheet presented)");
    return;
  }
  SDL_Log("[zen] shake -> font family step");
  gpio.injectFontFamilyStep();
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
              "(zen-only: 6 swipes, pinch, 2-tap, 4-tap; always on: 3-tap "
              "toggle, 1-finger hold %.2f s -> toggle above the paper / "
              "select on it; shake catcher installed)",
              zenhold::kHoldMs / 1000.0);
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
