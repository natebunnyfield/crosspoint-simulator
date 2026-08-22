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

extern "C" bool CrossPointMixer_isPresented(void);
// The shim's toggle: flip g_zen, refit, present, and spoil the SDL-side tap
// candidate and classifier for the same three fingers.
extern "C" void CrossPointZen_toggleFromRecognizer(void);

@interface CPXZenGestureHandler : NSObject
@end

@implementation CPXZenGestureHandler

- (void)queueButton:(uint8_t)button as:(const char *)what {
  // The mixer sheet leaves the view under it hit-testable (pageSheet with an
  // undimmed medium detent); a gesture on the exposed page must not drive the
  // reader while the tray is up. Same rule as the shim's finger gate.
  if (CrossPointMixer_isPresented()) {
    SDL_Log("[zen] recognizer %s swallowed (mixer presented)", what);
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

- (void)threeTap:(UITapGestureRecognizer *)g {
  if (CrossPointMixer_isPresented()) {
    SDL_Log("[zen] recognizer 3-finger toggle swallowed (mixer presented)");
    return;
  }
  SDL_Log("[zen] recognizer 3-finger tap -> toggle");
  CrossPointZen_toggleFromRecognizer();
}

@end

namespace {

CPXZenGestureHandler *g_handler = nil;
// The zen-only VERB recognizers: enabled tracks the zen flag.
NSArray<UIGestureRecognizer *> *g_recognizers = nil;
// The 3-finger TOGGLE: attached with the rest but ALWAYS enabled — it is the
// way INTO zen, so it must fire while the verb recognizers are off.
UITapGestureRecognizer *g_toggle = nil;

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

      SDL_Log("[zen] recognizers attached "
              "(6 swipes, pinch, 2-tap, 4-tap; 3-tap toggle always on)");
    }
    for (UIGestureRecognizer *r in g_recognizers)
      r.enabled = on ? YES : NO;
    SDL_Log("[zen] verb recognizers %s", on ? "enabled" : "disabled");
  });
}
