// The turned page's landscape: the iOS half that changes what UIKit may rotate to
// (docs/turned-page-landscape-plan-2026-10-04.md; the decision itself is pure, in
// src/TurnedPageLandscape.h, host-tested).
//
// Polled once a frame from CrossPointHarness_perFrame on the main thread, which
// is the only thread UIKit and SDL's hints are touched from here -- and, while
// the firmware sleeps, from the harness's sleep tick on that same thread, since
// the sleep loop never returns to perFrame and sleeping from a turned page is a
// snap-back like any other (CrossPointIOSShim.cpp sleepTick). It does work
// only on a CHANGE of the wanted hint: SDL_SetHint, then ask UIKit to re-query
// the root view controller's supported orientations. SDL answers that query by
// re-reading the hint (SDL_uikitwindow.m, UIKit_GetSupportedOrientations), so:
//   * a turned page arrives -> the phone gains the landscape of a
//     COUNTER-clockwise turn (the table is turned clockwise), and if
//     the phone is already held that way iOS rotates at once;
//   * it leaves -> landscape is no longer supported and iOS rotates back to
//     portrait at once, even with the phone still sideways (owner, Q2: "snap
//     back").
// The iPad's hint never changes (it rotates freely by its own ruling); only the
// presentation does, and that is the shim's layout, not this file.
#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include <cstdlib>
#include <cstring>
#include <string>

#include "CrossPointAppearance.h"
#include "SimulatorOverlay.h"
#include "TurnedPageLandscape.h"

extern SDL_Window *simulatorWindow();

namespace {

bool forceLandscapeFromEnv() {
  // QA hatch, read once: CROSSPOINT_SIM_FORCE_TURNED_LANDSCAPE=1 makes a turned
  // page force the rotation (the iOS Simulator cannot be turned from a script).
  static const bool force = [] {
    const char *e = std::getenv("CROSSPOINT_SIM_FORCE_TURNED_LANDSCAPE");
    return e && e[0] == '1';
  }();
  return force;
}

void requestOrientationUpdate() {
  SDL_Window *window = simulatorWindow();
  if (!window) return;
  UIWindow *uiWindow = (__bridge UIWindow *)SDL_GetPointerProperty(
      SDL_GetWindowProperties(window), SDL_PROP_WINDOW_UIKIT_WINDOW_POINTER, NULL);
  UIViewController *root = uiWindow.rootViewController;
  if (!root) {
    SDL_Log("[orient] no root view controller -- the orientation change waits "
            "for the next device turn");
    return;
  }
  [root setNeedsUpdateOfSupportedInterfaceOrientations];
}

}  // namespace

extern "C" void CrossPointOrientation_poll(void) {
  static const bool isPad = CrossPointAppearance_isPad() == 1;
  const bool turned = SimulatorOverlay::turnedPageShowing();
  const char *want = turnedpage::hintFor(isPad, turned, forceLandscapeFromEnv());
  static std::string applied;   // empty until the first poll: always compare against the live hint first
  if (applied.empty()) {
    const char *live = SDL_GetHint(SDL_HINT_ORIENTATIONS);
    applied = live ? live : "";
  }
  if (applied == want) return;
  applied = want;
  SDL_SetHint(SDL_HINT_ORIENTATIONS, want);
  SDL_Log("[orient] turned page %s -> hint \"%s\"", turned ? "up" : "down", want);
  requestOrientationUpdate();
}
