// The live system appearance, asked of UIKit rather than read from SDL's
// cache. See CrossPointAppearance.h for what that buys and what it does not.

#include "CrossPointAppearance.h"

#import <UIKit/UIKit.h>

namespace {

int styleOf(UITraitCollection *tc) {
  if (!tc) return -1;
  switch (tc.userInterfaceStyle) {
    case UIUserInterfaceStyleDark:
      return 1;
    case UIUserInterfaceStyleLight:
      return 0;
    default:
      return -1;  // UIUserInterfaceStyleUnspecified
  }
}

// Cached because the caller runs at the main loop's ~1 kHz and the window never
// changes: this app has exactly one, created by SDL. Walking connectedScenes
// every frame would allocate a set enumerator per frame to rediscover the same
// pointer. __weak so a scene teardown cannot leave this dangling, and so a nil
// read simply re-resolves.
__weak UIWindow *g_window = nil;

UIWindow *resolveWindow() {
  UIWindow *cached = g_window;
  if (cached) return cached;
  UIWindow *fallback = nil;
  for (UIScene *scene in UIApplication.sharedApplication.connectedScenes) {
    if (![scene isKindOfClass:UIWindowScene.class]) continue;
    for (UIWindow *w in ((UIWindowScene *)scene).windows) {
      if (w.isKeyWindow) {
        g_window = w;
        return w;
      }
      if (!fallback) fallback = w;
    }
  }
  g_window = fallback;
  return fallback;
}

}  // namespace

// THE WINDOW IS THE SOURCE, not UITraitCollection.currentTraitCollection.
//
// currentTraitCollection is only contractual INSIDE a UIKit view-update
// callback -- UIKit sets it around calls like traitCollectionDidChange and
// layoutSubviews, and its value outside those is not promised. This is called
// from main()'s loop, which is nowhere near a view update, so the window's own
// traitCollection is the source and currentTraitCollection is kept only as a
// fallback for the startup frames, before SDL has created a window.
//
// MEASURED, on iOS 26.5 in the Simulator: the window, the window scene,
// currentTraitCollection and [UIScreen mainScreen] (the one SDL reads) were
// sampled together at 1 Hz across repeated light/dark flips, including flips
// made while the app was backgrounded. They never disagreed -- so this probe is
// not correcting a wrong answer from SDL on that OS, it is removing the
// DEPENDENCY on a deprecated callback firing at all. What it does buy, measured:
// the poll applies the change within one ~1 kHz frame of the app resuming, ~65
// ms, and consistently wins the race against SDL's event, which arrived up to a
// second later.
int CrossPointAppearance_isPad(void) {
  return UIDevice.currentDevice.userInterfaceIdiom == UIUserInterfaceIdiomPad
             ? 1
             : 0;
}

// THE STATUS BAR IS HIDDEN GLOBALLY IN Info.plist.in (UIStatusBarHidden=YES,
// UIViewControllerBasedStatusBarAppearance=NO) AND THAT ALONE ALREADY HIDES IT
// ON iPHONE -- measured 2026-08-29, a fresh Debug build on an iPhone Air
// simulator (iOS 26.5) shows no clock/Wi-Fi/battery on Home or in a book.
//
// THE SAME BUILD, ON AN iPad Pro 13 (M4) SIMULATOR, SAME iOS, SHOWS THEM
// ANYWAY. Measured, not assumed: ios/mockups/ipad-BEFORE-portrait-page-2026-08-29.png
// is that exact screenshot. SDL's own view controller
// (SDL_uikitviewcontroller.m) implements `prefersStatusBarHidden` correctly --
// it returns YES whenever the window carries SDL_WINDOW_FULLSCREEN or
// SDL_WINDOW_BORDERLESS -- but that method is never CONSULTED while
// UIViewControllerBasedStatusBarAppearance is NO, which is the global default
// here, on both devices. So the two devices are running the identical static
// declaration, and only one of them honors it. The iPad's own multitasking
// chrome (this app requests UIRequiresFullScreen, but that key has been
// deprecated since iOS 26 -- see the build warning -- and iPadOS is a
// documented candidate for showing a persistent status bar as system window
// chrome regardless of app preference) is the leading candidate, not proven
// further here.
//
// THE FIX IS THE IMPERATIVE, PER-WINDOW-SCENE CALL, iPad-only. It does not
// touch the shared Info.plist keys or src/HalDisplay.cpp's SDL_CreateWindow
// flags (both iPhone and desktop-shared), so iPhone's already-working path is
// untouched. Deprecated since iOS 13 in favor of the view-controller-based
// appearance system, but it remains the documented workaround for exactly a
// static declaration that iOS is not honoring, and it still requires
// UIViewControllerBasedStatusBarAppearance=NO to take effect -- which the
// plist already sets, globally, so no plist change was needed either.
//
// PROVE IT, DO NOT ASSUME IT: this call's effect is verified by re-running the
// exact screenshot above after this lands (ios/mockups/ipad-AFTER-*.png) --
// see docs/ipad-layout-2026-08-29.md for whether it actually worked. If iOS
// is truly withholding the status bar as system multitasking chrome, this call
// will be silently ineffective and the doc says so.
void CrossPointAppearance_hideStatusBarOnIPad(void) {
  static bool applied = false;
  if (applied) return;
  if (UIDevice.currentDevice.userInterfaceIdiom != UIUserInterfaceIdiomPad) return;
  @autoreleasepool {
    UIWindow *window = resolveWindow();
    if (!window) return;  // no window yet: do not latch, ask again next call
    applied = true;
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
    [UIApplication.sharedApplication setStatusBarHidden:YES
                                           withAnimation:UIStatusBarAnimationNone];
#pragma clang diagnostic pop
    NSLog(@"[statusbar] iPad: imperative hide applied");
  }
}

// THE RADIUS IS ASKED FOR, NOT LOOKED UP.
//
// Every published way to get this number before iOS 26 was the private
// UIScreen._displayCornerRadius or a hardcoded per-model table, and both are
// still what the popular packages do. iOS 26's UICornerRadius adds a supported
// third road: containerConcentricRadius is resolved by UIKit against the view's
// container, so a view the exact size of the window resolves to the window's
// own corners, which are the display's. The number is never handed over
// directly -- it is applied -- so the probe reads it back off the layer UIKit
// configured.
//
// The probe view is never drawn: it is hidden, non-interactive, added only long
// enough for one layout pass, and removed. Cached because the display's radius
// cannot change for the life of the process, and because a failed probe would
// otherwise repeat the whole dance on every frame.
double CrossPointAppearance_displayCornerRadius(void) {
  static double cached = -1.0;
  if (cached >= 0.0) return cached;
  @autoreleasepool {
    UIWindow *window = resolveWindow();
    if (!window) return 0.0;  // no window yet: do not cache, ask again later
    double radius = 0.0;
    if (@available(iOS 26.0, *)) {
      UIView *probe = [[UIView alloc] initWithFrame:window.bounds];
      probe.hidden = YES;
      probe.userInteractionEnabled = NO;
      probe.cornerConfiguration = [UICornerConfiguration
          configurationWithUniformRadius:[UICornerRadius
                                             containerConcentricRadius]];
      [window addSubview:probe];
      [probe layoutIfNeeded];
      [window layoutIfNeeded];
      radius = probe.layer.cornerRadius;
      [probe removeFromSuperview];
    }
    cached = radius;
    NSLog(@"[corner] display corner radius probe: %.2f pt (window %.0fx%.0f)",
          radius, window.bounds.size.width, window.bounds.size.height);
    return cached;
  }
}

int CrossPointAppearance_isDark(void) {
  // Property getters can hand back autoreleased objects. main()'s loop is not a
  // UIKit callback, so there is no pool being drained around it -- at ~1 kHz an
  // unbounded pool would be a slow leak. Draining our own is a few nanoseconds.
  @autoreleasepool {
    const int fromWindow = styleOf(resolveWindow().traitCollection);
    if (fromWindow >= 0) return fromWindow;
    return styleOf(UITraitCollection.currentTraitCollection);
  }
}
