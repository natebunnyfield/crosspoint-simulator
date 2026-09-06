#include "CrossPointVolumeButtons.h"

#import <AVFoundation/AVFoundation.h>
#import <MediaPlayer/MediaPlayer.h>
#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include <cstddef>
#include <cstdint>
#include <mutex>
#include <vector>

#include "CrossPointPrefs.h"
#include "CrossPointReadAloud.h"
#include "HalGPIO.h"
#include "VolumePageTurn.h"

extern "C" void CrossPointZenRecognizers_fireGesture(int gesture);

// The volume-rocker adapter. Owner, 2026-09-05: "add ios app setting for
// hardware volume buttons and any volume changes to control back and forward
// pages (front button rocker switch) default to off", plus, the same day,
// "option to flip volume buttons (default to off)" -- Settings.bundle's
// second row in this group, read in drain() below alongside the enable
// toggle and passed to volumepage::buttonFor() to swap which side is which.
//
// HOW, since iOS has no volume-button API: while the setting is on and the
// app is active, an audio session is held and AVAudioSession.outputVolume is
// observed by KVO. A change is read for its DIRECTION (ios/VolumePageTurn.h),
// the matching front button is pressed through gpio.queueButtonTap -- the
// same route the read-aloud page turn and the accessibility scroll take, and
// the ONLY route by which an edge raised outside HalGPIO::update() reaches the
// firmware (HalGPIO.h says why) -- and the level is put back where it was
// through the slider inside an offscreen MPVolumeView, so the next press has
// somewhere to go. That view being in the hierarchy is also what stops iOS
// drawing its volume bezel over the page on every turn.
//
// Everything below runs on the main thread EXCEPT the KVO callback, which
// AVFoundation delivers on whatever thread changed the volume and which
// therefore only enqueues the new level; perFrame drains it. Same shape as the
// read-aloud adapter's delegate queue, for the same reason: queueButtonTap's
// pending list is main-thread-only by contract (HalGPIO.cpp).
//
// THE AUDIO SESSION IS SHARED WITH READ-ALOUD, and the rule is: read-aloud
// owns it whenever it is speaking or paused (Playback / SpokenAudio, so its
// speech survives the ring switch and the lock); this adapter BORROWS it under
// Ambient -- mixes with whatever is playing, claims no background time -- only
// while read-aloud is not holding it, and hands it straight back when
// read-aloud wants it. The observer does not care which category is active,
// only that some session is; the category matters to the owner's podcast.

static_assert(volumepage::kBtnLeft == HalGPIO::BTN_LEFT, "BTN_LEFT");
static_assert(volumepage::kBtnRight == HalGPIO::BTN_RIGHT, "BTN_RIGHT");

namespace {

std::mutex g_levelMutex;
std::vector<float> g_levels;  // KVO thread -> drained by perFrame
// Presses that arrive while nothing drains (the firmware's sleep loop) are
// dropped at the wake, not banked; the cap only bounds the vector meanwhile.
constexpr size_t kMaxQueuedLevels = 32;

bool g_armed = false;
bool g_sessionTaken = false;  // this adapter activated the session (not read-aloud)
int g_lastEnabled = -1;       // pref edge, for the log; -1 = re-log
float g_resting = volumepage::kMidLevel;   // where the level is put back to
float g_previous = volumepage::kMidLevel;  // the last level the observer saw
bool g_restorePending = false;
int g_restoreTicks = 0;
// ~0.5 s at the main loop's ~1 kHz (SDL_Delay(1)): how long a restore's echo
// is waited for before the expectation is dropped. Without this a restore
// that produced no event (the level was already there; no slider found)
// would leave the expectation armed forever and swallow the next real press
// that happened to land on the resting level.
constexpr int kRestoreEchoTimeoutTicks = 500;

void *kVolumeContext = &kVolumeContext;

MPVolumeView *g_volumeView = nil;
UISlider *g_slider = nil;

}  // namespace

// The KVO sink. Never decides anything and never touches HalGPIO: it may be
// called off the main thread.
@interface CPVolumeObserver : NSObject
@end

@implementation CPVolumeObserver
- (void)observeValueForKeyPath:(NSString *)keyPath
                      ofObject:(id)object
                        change:(NSDictionary<NSKeyValueChangeKey, id> *)change
                       context:(void *)context {
  if (context != kVolumeContext) {
    [super observeValueForKeyPath:keyPath ofObject:object change:change context:context];
    return;
  }
  id value = change[NSKeyValueChangeNewKey];
  if (![value isKindOfClass:NSNumber.class]) return;
  const float level = [(NSNumber *)value floatValue];
  std::lock_guard<std::mutex> lock(g_levelMutex);
  if (g_levels.size() < kMaxQueuedLevels) g_levels.push_back(level);
}
@end

namespace {

CPVolumeObserver *g_observer = nil;

// Same resolver as CrossPointAccessibility.mm: the key window of the first
// window scene, or the first window there is.
UIWindow *resolveWindow() {
  UIWindow *fallback = nil;
  for (UIScene *scene in UIApplication.sharedApplication.connectedScenes) {
    if (![scene isKindOfClass:UIWindowScene.class]) continue;
    for (UIWindow *w in ((UIWindowScene *)scene).windows) {
      if (w.isKeyWindow) return w;
      if (!fallback) fallback = w;
    }
  }
  return fallback;
}

UISlider *sliderInside(MPVolumeView *view) {
  for (UIView *sub in view.subviews)
    if ([sub isKindOfClass:UISlider.class]) return (UISlider *)sub;
  return nil;
}

// The offscreen MPVolumeView, attached only while armed. OFFSCREEN, NOT
// HIDDEN: iOS suppresses its own volume bezel while an MPVolumeView is in the
// visible hierarchy, a hidden one does not count, and without the suppression
// every page turn flashes the system's volume HUD over the page. Attached only
// while armed because that suppression is app-wide: with the setting OFF the
// owner's volume presses must look exactly as they did before this file
// existed, HUD included.
void attachVolumeView() {
  if (g_volumeView && g_volumeView.superview) return;
  UIWindow *window = resolveWindow();
  if (!window) {
    SDL_Log("[VOLUME] no window to host the volume view yet");
    return;
  }
  if (!g_volumeView) {
    g_volumeView = [[MPVolumeView alloc]
        initWithFrame:CGRectMake(-2000.0, -2000.0, 120.0, 40.0)];
    g_volumeView.userInteractionEnabled = NO;
  }
  [window addSubview:g_volumeView];
  g_slider = sliderInside(g_volumeView);
  if (!g_slider)
    // Loud, because the failure it leaves is silent: pages turn until the
    // level reaches an end of the range, then one direction goes quiet.
    SDL_Log("[VOLUME] MPVolumeView has no UISlider subview -- the level cannot "
            "be put back after a press, so the rocker will go dead at the end "
            "of the range");
}

void detachVolumeView() {
  if (g_volumeView) [g_volumeView removeFromSuperview];
  g_slider = nil;
}

// Write `level` back to the system through the slider. The KVO event that
// write produces is expected and ignored (volumepage::judge's Echo).
void restoreTo(float level) {
  if (!g_slider) attachVolumeView();
  if (!g_slider) return;
  g_restorePending = true;
  g_restoreTicks = 0;
  [g_slider setValue:level animated:NO];
  // The slider inside MPVolumeView pushes its value to the system on the
  // control action, not on the setter alone.
  [g_slider sendActionsForControlEvents:UIControlEventTouchUpInside];
}

void takeAudioSession() {
  // Read-aloud's Playback session serves the observer just as well, and it
  // must not be re-categorised out from under a page being spoken.
  if (CrossPointReadAloud_holdsAudioSession()) return;
  AVAudioSession *session = [AVAudioSession sharedInstance];
  NSError *err = nil;
  // AMBIENT: the rocker must address THIS app's output volume for KVO to see
  // a press at all (with no session active the buttons move the ringer), and
  // nothing here ever plays a sound -- so the category that mixes with the
  // owner's podcast and asks for no background time is the honest one.
  [session setCategory:AVAudioSessionCategoryAmbient
                  mode:AVAudioSessionModeDefault
               options:0
                 error:&err];
  if (err) SDL_Log("[VOLUME] audio session category failed: %s",
                   err.localizedDescription.UTF8String);
  err = nil;
  [session setActive:YES error:&err];
  if (err) {
    SDL_Log("[VOLUME] audio session activate failed: %s -- the rocker will "
            "not be heard until it succeeds",
            err.localizedDescription.UTF8String);
    return;
  }
  g_sessionTaken = true;
}

void releaseAudioSession() {
  if (!g_sessionTaken) return;
  g_sessionTaken = false;
  // Read-aloud took it over after us; it is read-aloud's to release now.
  if (CrossPointReadAloud_holdsAudioSession()) return;
  NSError *err = nil;
  [[AVAudioSession sharedInstance] setActive:NO error:&err];
  if (err) SDL_Log("[VOLUME] audio session deactivate failed: %s",
                   err.localizedDescription.UTF8String);
}

// Where the level is now, and where it will rest. Called on arm and after a
// wake: both are moments the phone may have been at a volume this adapter
// did not set.
void baseline(const char *why) {
  const float observed = [AVAudioSession sharedInstance].outputVolume;
  g_resting = volumepage::restingLevel(observed);
  g_previous = observed;
  g_restorePending = false;
  {
    std::lock_guard<std::mutex> lock(g_levelMutex);
    g_levels.clear();
  }
  SDL_Log("[VOLUME] %s: level %.4f, resting %.4f%s", why, observed, g_resting,
          volumepage::atEnd(observed) ? " (moved off the end of the range)"
                                      : "");
  if (g_resting != observed) restoreTo(g_resting);
}

void arm() {
  if (g_armed) return;
  takeAudioSession();
  attachVolumeView();
  if (!g_observer) g_observer = [[CPVolumeObserver alloc] init];
  [[AVAudioSession sharedInstance] addObserver:g_observer
                                    forKeyPath:@"outputVolume"
                                       options:NSKeyValueObservingOptionNew
                                       context:kVolumeContext];
  g_armed = true;
  baseline("armed");
}

void disarm(const char *why) {
  if (!g_armed) return;
  [[AVAudioSession sharedInstance] removeObserver:g_observer
                                       forKeyPath:@"outputVolume"
                                          context:kVolumeContext];
  g_armed = false;
  g_restorePending = false;
  {
    std::lock_guard<std::mutex> lock(g_levelMutex);
    g_levels.clear();
  }
  detachVolumeView();
  releaseAudioSession();
  SDL_Log("[VOLUME] disarmed (%s)", why);
}

void drain() {
  std::vector<float> levels;
  {
    std::lock_guard<std::mutex> lock(g_levelMutex);
    levels.swap(g_levels);
  }
  for (const float level : levels) {
    const volumepage::Verdict v =
        volumepage::judge(g_previous, level, g_restorePending, g_resting);
    const float previous = g_previous;
    g_previous = level;
    switch (v) {
      case volumepage::Verdict::Echo:
        g_restorePending = false;
        break;
      case volumepage::Verdict::Next:
      case volumepage::Verdict::Prev: {
        // Read live, same as the enable toggle in perFrame: a change made in
        // Settings.app while the app was backgrounded takes effect on the
        // very next press after returning.
        // 2026-09-06: the press no longer means "page turn". It fires the
        // gestureVolumeUp / gestureVolumeDown ROW, and what that row does is
        // the owner's binding -- resolved live, so a change made in
        // Settings.app while the app was backgrounded takes effect on the very
        // next press. Routed through the recognizers' own dispatch so it takes
        // the zen gate and the palette-sheet swallow with every other gesture,
        // rather than injecting a button behind them.
        const gesturebind::Gesture row = volumepage::gestureFor(v);
        CrossPointZenRecognizers_fireGesture(static_cast<int>(row));
        SDL_Log("[VOLUME] %.4f -> %.4f: %s", previous, level,
                gesturebind::gestureName(row));
        restoreTo(g_resting);
        break;
      }
      case volumepage::Verdict::None:
        break;
    }
  }
  if (g_restorePending && ++g_restoreTicks > kRestoreEchoTimeoutTicks) {
    // The echo never came. Ask the session where the level actually is
    // rather than assuming the restore landed.
    g_restorePending = false;
    g_previous = [AVAudioSession sharedInstance].outputVolume;
  }
}

}  // namespace

void CrossPointVolumeButtons_resetForReboot(void) {
  if (!g_armed) return;
  // Presses made while the firmware slept were queued with nobody draining;
  // a page turn out of them would land in the boot that is waking. Drop them
  // and re-read the level, which those presses moved.
  baseline("reboot");
  SDL_Log("[VOLUME] reset for reboot");
}

// IS EITHER ROCKER ROW BOUND? Holding an audio session and putting the level
// back after every press is the part App Store review has rejected apps for,
// so it happens only while the owner has actually asked for it -- which, since
// 2026-09-06, is a binding rather than a switch. Zen state is deliberately not
// consulted: a row bound only outside zen still needs the session held, or the
// first press after leaving zen has nothing to report.
static bool volumeRowsBound(void) {
  using gesturebind::Action;
  using gesturebind::Gesture;
  for (Gesture g : {Gesture::VolumeUp, Gesture::VolumeDown}) {
    const int stored = CrossPointPrefs_gestureBinding(static_cast<int>(g));
    if (gesturebind::actionFor(g, true, stored) != Action::Nothing) return true;
    if (gesturebind::actionFor(g, false, stored) != Action::Nothing) return true;
  }
  return false;
}

void CrossPointVolumeButtons_begin(void) {
  static bool s_installed = false;
  if (!s_installed) {
    s_installed = true;
    SDL_Log("[VOLUME] adapter installed (rows %s)",
            volumeRowsBound() ? "bound" : "unbound");
  }
  // Re-log the setting on the next perFrame -- a wake is exactly when the
  // owner may have changed it in Settings. Arming itself is level-driven from
  // perFrame and needs no re-seed.
  g_lastEnabled = -1;
}

void CrossPointVolumeButtons_perFrame(void) {
  // The bindings, read live: Settings.app is a separate process, so a change
  // made there arrives with no event to hang it on (same as every other poll
  // in the harness).
  const int want = volumeRowsBound() ? 1 : 0;
  if (want != g_lastEnabled) {
    g_lastEnabled = want;
    SDL_Log("[VOLUME] %s", want ? "armed (a row is bound)" : "idle (both rows Nothing)");
  }
  // Armed only while the app is ACTIVE. Inactive covers Control Center and
  // the notification shade over the app as well as the background proper: a
  // volume change made there is the owner setting the volume, not turning a
  // page, and an Ambient session held from the background is a session the
  // system will end anyway. Level-triggered, so a return to the foreground
  // re-arms and re-baselines by itself.
  const bool shouldArm =
      want != 0 && UIApplication.sharedApplication.applicationState ==
                       UIApplicationStateActive;
  if (shouldArm && !g_armed)
    arm();
  else if (!shouldArm && g_armed)
    disarm(want ? "app not active" : "setting off");
  if (g_armed) drain();
}

void CrossPointVolumeButtons_appWillResignActive(void) {
  disarm("app resigning active");
}

void CrossPointVolumeButtons_audioSessionReleased(void) {
  if (!g_armed) return;
  takeAudioSession();
  SDL_Log("[VOLUME] audio session taken back from read-aloud");
}
