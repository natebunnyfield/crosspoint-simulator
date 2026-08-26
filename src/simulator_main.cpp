
#include <SDL3/SDL.h>
#include <unistd.h>

#include <cstdlib>
#include <string>
#include <utility>
#include <vector>

#include "Arduino.h"
#include "CrossPointSettings.h"
#include "HalDisplay.h"
#include "HalGPIO.h"
#include "SimulatorDocumentOpen.h"
#include "ReadingLog.h"
#include "SimulatorLifecycle.h"
#include "SimulatorOverlay.h"
#include "SimulatorRebootResets.h"
#include "SimulatorSettingsWatch.h"

#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif

// On iOS, SDL renames main() and calls it from UIApplicationMain, so the entry
// point below is reached the same way as on desktop -- but the working
// directory, the input source and the process lifetime all differ. Those three
// are the only iOS-specific lines in the simulator; HalGPIO and the firmware are
// untouched.
#if defined(__APPLE__) && TARGET_OS_IPHONE
#define CROSSPOINT_SIM_IOS 1
#include <SDL3/SDL_main.h>

#include "CrossPointAppearance.h"
#include "CrossPointHarness.h"
#include "CrossPointPrefs.h"
#else
#define CROSSPOINT_SIM_IOS 0
#endif

extern void setup();
extern void loop();
extern HalDisplay display; // defined in main.cpp

// Apply Settings > System > Keep Screen Awake to the host's idle timer.
//
// Mechanism, on iOS: SDL_DisableScreenSaver() sets the video device's
// suspend_screensaver flag and calls the driver's SuspendScreenSaver hook
// (SDL_video.c). The UIKit driver installs UIKit_SuspendScreenSaver for that
// hook (src/video/uikit/SDL_uikitvideo.m), whose entire body is
// `app.idleTimerDisabled = (_this->suspend_screensaver != false)` on
// [UIApplication sharedApplication]. So this IS the iOS API, reached through
// SDL -- no Objective-C and no new iOS surface in this repo. On macOS the same
// two entry points route to the Cocoa driver instead, so the desktop build gets
// the equivalent behavior for free.
//
// IMPORTANT: SDL_VideoInit disables the screensaver *by default* unless
// SDL_HINT_VIDEO_ALLOW_SCREENSAVER is set -- SDL's rationale is that most SDL
// programs are games or media players. Nothing in this repo sets that hint, so
// before this setting existed the app unconditionally held the screen awake.
// Honouring a default-OFF setting is therefore a genuine behavior change on
// the first frame, not a no-op.
//
// Edge-triggered by construction: the per-frame cost is a byte load and an
// integer compare, and SDL is only entered when the owner actually flips the
// row. The -1 sentinel guarantees the first call after startup always applies,
// which is what makes this cover "at startup" as well as "on change".
//
// Main thread only. It is called from main()'s loop alongside presentIfNeeded()
// for the same reason that one is: UIKit/Cocoa must not be touched off-thread.
// It is not in PadCore (which is pure and SDL-free) and it does not read the
// SDL event queue, so HalGPIO keeps sole ownership of the event pump.
// ON iOS THE SOURCE OF TRUTH IS Settings > CrossPoint X3, not the firmware row.
// Sleep behavior is a property of the phone, not of the reader, and it is also
// power-state dependent there — the owner sets it separately for battery and
// for charging, which a single firmware boolean cannot express.
//
// The firmware's "Keep Screen Awake" row is deliberately left alone for now and
// therefore has no effect on iOS. That is a known, temporary overlap: two
// controls for one behavior, pending a ruling on what the firmware row should
// become. Do not "fix" it by deleting either side without that ruling. On the
// desktop simulator the firmware row is still the only control and still works.
static void applyKeepScreenAwake() {
  static int8_t applied = -1;  // -1 = nothing applied yet
#if CROSSPOINT_SIM_IOS
  const int8_t want = CrossPointPrefs_wantsScreenAwake() ? 1 : 0;
#else
  const int8_t want = SETTINGS.keepScreenAwake ? 1 : 0;
#endif
  if (want == applied) return;
  applied = want;
  if (want) {
    SDL_DisableScreenSaver();  // keep the host display on
  } else {
    SDL_EnableScreenSaver();   // let the host dim/lock normally
  }
}

// Latch the render scale before ANYTHING reads panel geometry.
//
// This is the one setting in the app that cannot be applied live: the factor
// sizes the SDL texture HalDisplay::begin() creates and picks which hi-res
// glyph tier setup() registers, and both are committed for the life of the
// process. RenderScale.h has the full argument. Everything downstream reads
// cp::renderScale(), so the only requirement is that this run FIRST -- before
// setup(), before begin(), before a single font is registered.
//
// Deliberately NOT inside the setjmp target below. A deep-sleep wake re-runs
// setup() against a live process with the texture and the font maps already
// built, so re-reading the setting there would change the arithmetic out from
// under geometry that cannot follow it. The owner's new choice takes effect on
// the next real launch, which is what the Settings footer says.
static void latchRenderScale() {
// A build whose ceiling is 1, or one that opted out with
// CROSSPOINT_RENDER_SCALE_RUNTIME=0, has no setter to call: cp::renderScale()
// is a constexpr function there and the factor is already decided. The log
// line below still runs, so "which scale is this binary at" is answerable the
// same way in both shapes.
#if defined(CROSSPOINT_RENDER_SCALE_RUNTIME) && CROSSPOINT_RENDER_SCALE_RUNTIME
#if CROSSPOINT_SIM_IOS
  cp::setRenderScale(CrossPointPrefs_renderScale());
#else
  // Desktop: an env var, matching CROSSPOINT_SIM_WINDOW_SCALE and the rest of
  // the simulator's knobs. Unset means "the ceiling this binary was compiled
  // at", i.e. exactly the behaviour before this existed.
  const char *env = SDL_getenv("CROSSPOINT_SIM_RENDER_SCALE");
  if (env && env[0] != '\0') {
    cp::setRenderScale(std::atoi(env));
  }
#endif
#endif
  LOG_INF("MAIN", "Render scale %d (ceiling %d)", cp::renderScale(),
          cp::kRenderScaleMax);
}

// A DESKTOP WINDOW WITH BANDS, for QA only. Nothing here is on by default.
//
// The phone reserves a top band for the status bar and a bottom band for the
// button pad (SimulatorOverlay::setTopInset / setBottomInset) and the panel is
// then FITTED between them; the desktop has always taken the plain letterbox
// path, where the window is exactly panel-sized and there is no surround at
// all. That makes the canary the platform on which anything about the SURROUND
// cannot be reproduced -- and the whole-glass phosphor and beam (2026-08-26)
// live out there. See docs/whole-glass-crt.md section 8.
//
// One env var per band, each a SCHEDULE. "120" reserves 120 device pixels from
// boot; "120;5200:360" reserves 120 and grows it to 360 at 5200 ms on the
// SDL_GetTicks clock, which is the only way this machine can photograph what a
// live trail does when the PAGE MOVES under it -- zen mode placing the panel
// within the sheet, or a keyboard coming up. Unset (the default) is a no-op and
// the desktop keeps the letterbox path byte for byte. Both setters clamp a
// negative to 0, so a malformed step can only ever mean "no band".
namespace {
struct BandSchedule {
  std::vector<std::pair<uint64_t, int>> steps;
  size_t next = 0;
  void parse(const char *env) {
    steps.clear();
    next = 0;
    if (!env || !*env) return;
    const std::string s(env);
    size_t i = 0;
    while (i <= s.size()) {
      const size_t semi = s.find(';', i);
      const std::string part =
          s.substr(i, semi == std::string::npos ? semi : semi - i);
      if (!part.empty()) {
        const size_t colon = part.find(':');
        if (colon == std::string::npos)
          steps.emplace_back(0, std::atoi(part.c_str()));
        else
          steps.emplace_back(std::strtoull(part.c_str(), nullptr, 10),
                             std::atoi(part.c_str() + colon + 1));
      }
      if (semi == std::string::npos) break;
      i = semi + 1;
    }
  }
  // The value to apply now, or -1 when nothing is due. Steps are consumed in
  // WRITTEN order and only the last one consumed is returned, so a schedule
  // whose timestamps are out of order SWALLOWS the earlier entries:
  // "5000:100;1000:200" applies 200 at t=5000 and never applies 100. Write them
  // in time order.
  //
  // The clock is SDL_GetTicks, which the reboot does NOT rebase (simclock
  // rebases the Arduino millis() epoch, not this one). After an iOS wake every
  // step is already due and the whole schedule collapses to its last entry on
  // the first loop iteration -- so a band schedule cannot photograph anything
  // across a sleep/wake.
  int due(uint64_t nowMs) {
    int v = -1;
    while (next < steps.size() && steps[next].first <= nowMs)
      v = steps[next++].second;
    return v;
  }
};
BandSchedule g_topBand, g_bottomBand;
bool g_bandsParsed = false;

// THE REASON THIS IS NOT A FUNCTION-LOCAL STATIC IN main(). The desktop reboot
// is execvp and re-initialises everything for free; iOS longjmps back into
// setup() in the SAME process, where `g_bandsParsed` would still be set and a
// consumed schedule would never replay -- the exact shape
// src/SimulatorRebootResets.h exists for. Re-parsed rather than merely rewound,
// so a reboot that promoted a different environment picks it up.
const simreset::Registrar gBandScheduleReset{[] { g_bandsParsed = false; }};
}  // namespace

int main(int argc, char **argv) {
  SimulatorLifecycle::initProcessArgs(argv);
  latchRenderScale();
#if CROSSPOINT_SIM_IOS
  // LANDSCAPE ON iPad ONLY (owner ruling 2026-08-17), and it has to be set
  // HERE -- before HalDisplay::begin() creates the window, because UIKit asks
  // for the supported orientations once as the window comes up.
  //
  // Info.plist does not decide this. SDL answers UIKit itself, from
  // UIKit_GetSupportedOrientations (SDL_uikitwindow.m): with this hint unset
  // and a resizable window it returns UIInterfaceOrientationMaskAll, and it
  // falls back to the app's declared orientations only when the intersection
  // with them is empty -- it never intersects. Measured, not reasoned: an
  // iPhone with Portrait-only in the plist rotated and laid itself out
  // landscape. The plist keys stay because the App Store reads them; this is
  // what the running app obeys.
  SDL_SetHint(SDL_HINT_ORIENTATIONS, CrossPointAppearance_isPad() == 1
                                         ? "Portrait LandscapeLeft LandscapeRight"
                                         : "Portrait");
  SDL_Log("[orient] isPad=%d hint=%s", CrossPointAppearance_isPad(),
          SDL_GetHint(SDL_HINT_ORIENTATIONS));

  // HalStorage's ./fs_ prefix relies on the CWD, which on iOS is the read-only
  // bundle. Must happen before setup() touches storage.
  CrossPointHarness_prepareFilesystem();

  // Where a deep-sleep wake lands. On desktop the wake is a process relaunch;
  // iOS cannot exec, so rebootAsPowerWake() jumps back here and setup() runs
  // again against the still-live process. Everything setup() touches has to
  // tolerate that -- HalDisplay::begin() reuses its window, xTaskCreate()
  // dedupes by task name.
  setjmp(SimulatorLifecycle::rebootJumpBuffer());
  SimulatorLifecycle::armRebootJump();
#endif
  // Before setup(), because a book handed to us by the OS (Finder on desktop,
  // Files/Mail/Share Sheet on iOS) has to be on the card and recorded in
  // APP_STATE before setup() reads that state and picks which activity to
  // open. No-op on any launch without a document.
  SimulatorDocumentOpen::captureLaunchDocument();

  // The reading ledger's launch boundary, and its once-per-launch export
  // service. AFTER the filesystem prep above, because the export marker is
  // looked for in the card root and on iOS that is the directory prep chdir()s
  // into; BEFORE setup(), because a fast book renders its first page inside the
  // first loop() iteration and a `page` line with no preceding `boot` line
  // would put that page in the previous session. Also reached by the iOS
  // longjmp reboot, which lands on the setjmp above -- so the per-launch config
  // latch is reset there rather than needing a SimulatorRebootResets entry.
  // See docs/reading-experiments.md.
  readinglog::publishBoot();
#if !CROSSPOINT_SIM_IOS
  // Headless read-aloud capture audit (.claude/PLAN-tts-read-aloud.md): "1"
  // logs a preview per publish, "2" additionally dumps full text and rects.
  // The wanted flag is set HERE, before setup() and the first loop(), because
  // a small book renders its first page inside the first loop() iteration —
  // a flag applied lazily from the main loop missed that page entirely.
  const int readAloudLog = [] {
    const char *v = SDL_getenv("CROSSPOINT_SIM_READALOUD_LOG");
    const int mode =
        (v && (v[0] == '1' || v[0] == '2') && v[1] == '\0') ? v[0] - '0' : 0;
    if (mode)
      gpio.setReadAloudCaptureWanted(true);
    return mode;
  }();
#endif
  setup();
#if CROSSPOINT_SIM_IOS
  // After setup(), because installing the gesture event watch needs SDL
  // initialized and HalDisplay::begin() is what calls SDL_Init.
  //
  // CALLED ON EVERY WAKE, deliberately not gated here. The function splits its
  // own work: registrations happen once (its s_watchesInstalled guard, so N
  // wakes cannot stack N event watches), while the state refreshes -- pad
  // reset, relayout, window scale, and the appearance -- re-run every call
  // because a wake is exactly when they have gone stale. A caller-side gate
  // used to skip the whole function after the first setup(), which made that
  // internal guard unreachable and meant a wake landed with the pre-sleep
  // appearance and layout still applied.
  CrossPointHarness_begin();
#endif
  // Startup application. setup() has loaded settings.json by now, and SDL is
  // initialized (HalDisplay::begin calls SDL_Init). Also covers the iOS wake
  // longjmp, which re-runs setup() and lands back here.
  applyKeepScreenAwake();

  // Parsed once per BOOT -- see gBandScheduleReset for why that is not "once
  // per process".
  if (!g_bandsParsed) {
    g_bandsParsed = true;
    g_topBand.parse(SDL_getenv("CROSSPOINT_SIM_TOP_INSET"));
    g_bottomBand.parse(SDL_getenv("CROSSPOINT_SIM_BOTTOM_INSET"));
    if (!g_topBand.steps.empty() || !g_bottomBand.steps.empty())
      SDL_Log("[panel] QA bands: %zu top step(s), %zu bottom step(s)",
              g_topBand.steps.size(), g_bottomBand.steps.size());
  }

  while (!display.shouldQuit()) {
    {
      const uint64_t nowMs = SDL_GetTicks();
      const int t = g_topBand.due(nowMs);
      if (t >= 0) SimulatorOverlay::setTopInset(t);
      const int b = g_bottomBand.due(nowMs);
      if (b >= 0) SimulatorOverlay::setBottomInset(b);
    }
    // Clear input edge latches once per frame. update() may be called many
    // times within loop(); edges must survive across those calls and only
    // reset here at the frame boundary.
    gpio.beginFrame();
    // The desktop's answer to the iOS Settings app: one stat a second, and a
    // reparse only when the file actually moved.
    simsettings::pollSettingsFile();
    loop();
    // Pick up a mid-run toggle from the Settings screen. No-op unless the value
    // actually changed; see applyKeepScreenAwake().
    applyKeepScreenAwake();
#if CROSSPOINT_SIM_IOS
    // Follow the system light/dark appearance, and repaint after a foreground
    // return (iOS throws away frames presented into that transition, and this
    // app presents too rarely to make another by itself). Same shape as
    // applyKeepScreenAwake above and here for the same reason: edge-triggered
    // inside, main thread only, no present forced unless something changed.
    CrossPointHarness_perFrame();
#endif
    // Raise or dismiss the host keyboard on the firmware's text-entry edge.
    // Here rather than in HalGPIO::update() because update() runs on the
    // firmware task and this ends in UIKit: on a phone it is what puts the
    // software keyboard on the glass. Edge-triggered inside; a no-op on every
    // frame that is not a transition.
    gpio.pumpHostTextInput();
#if !CROSSPOINT_SIM_IOS
    // Drain and log the capture (flag set before setup(), above — a lazy flag
    // missed any page rendered by the first loop() iteration). Desktop has no
    // speech consumer; iOS must not compile this — its harness is the
    // consumer and this drain would steal its pages.
    if (readAloudLog) {
      ReadAloudPage page;
      while (gpio.consumeReadAloudPage(page)) {
        SDL_Log("[READALOUD] page gen=%u cleared=%d bytes=%zu words=%zu | %.200s",
                page.generation, page.cleared ? 1 : 0, page.utf8.size(),
                page.rects.size(), page.utf8.c_str());
        if (readAloudLog >= 2 && !page.cleared) {
          SDL_Log("[READALOUD-TEXT] %s", page.utf8.c_str());
          for (const ReadAloudWordRect &r : page.rects)
            SDL_Log("[READALOUD-RECT] x=%u y=%u w=%u h=%u off=%u len=%u \"%.*s\"",
                    r.x, r.y, r.w, r.h, r.byteOffset, r.byteLen,
                    static_cast<int>(r.byteLen), page.utf8.c_str() + r.byteOffset);
        }
      }
    }
#endif
    // Open a book handed to us by the OS while the app was already running
    // (Finder double-click on desktop, Files/Mail/Share Sheet on iOS).
    // Relaunches when there is one, so this does not return in that case.
    SimulatorDocumentOpen::pumpPendingOpen();
    // SDL must be driven from the main thread on macOS.
    // The render task writes pixels and sets pendingPresent; we flush them
    // here.
    display.presentIfNeeded();
    // Yield to the OS so macOS delivers pending keyboard/window events to SDL.
    // Without this, the tight spin-loop starves the Cocoa event system and key
    // presses are only picked up sporadically. 1 ms also caps the loop at ~1
    // kHz, which matches realistic device behavior (the real ESP32-C3 is
    // limited by FreeRTOS tick rate and e-ink refresh time).
    SDL_Delay(1);
  }
  SDL_Quit();
#if CROSSPOINT_SIM_IOS
  // iOS treats _exit() as a crash, and an app that kills its own process is
  // reported as one. Return normally instead.
  return 0;
#else
  // Use _exit() instead of return/exit() to bypass C++ global destructors.
  // `activityManager` (and other globals in main.cpp) are constructed before
  // the render task thread starts, and the render task runs a [[noreturn]]
  // infinite loop.  If normal exit() runs global destructors while the render
  // thread is mid-render, the destructor races with the thread → SIGABRT/
  // SIGSEGV → "quit unexpectedly" dialog.  SDL is already torn down above, so
  // calling _exit(0) here is safe.
  _exit(0);
#endif
}
