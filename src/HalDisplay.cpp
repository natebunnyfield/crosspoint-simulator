#include "HalDisplay.h"
#include "SimulatorRebootResets.h"

#include <GfxRenderer.h>
#include <Logging.h>
#include <SDL3/SDL.h>

#include "CornerDefocus.h"
#include "FieldSelection.h"
#include "GlassCapture.h"
#include "GrayscalePreview.h"
#include "LaidStructure.h"
#include "Letterpress.h"
#include "LightInkPalette.h"
#include "PaperDefects.h"
#include "PageFade.h"
#include "TrailLifetime.h"
#include "PanelPalette.h"
#include "PhosphorGrain.h"
#include "Srgb.h"
#include "SurfacePower.h"
#include "SurfaceSheet.h"
#include "SurfaceTube.h"
#include "Scanlines.h"
#include "FrozenPage.h"
#include "ShowThrough.h"
#include "ReadingArm.h"
#include "ReadingLog.h"
#include "SimulatorBuildIdentity.h"
#include "SimulatorDeviceTruth.h"
#include "SimulatorOverlay.h"

// PHASE 2's stop switch (docs/reading-experiments.md §7, Decision 1) lives in
// Settings.app, which is iOS-only -- CrossPointPrefs.mm compiles into the
// CrossPointX3 APP target (ios/CMakeLists.txt), not this file's
// crosspoint_core static library, so a call to its getter has to be compiled
// out entirely wherever that app target does not exist, the desktop
// PlatformIO build first among them. Same local detection, same reasoning, as
// CrossPointPrefs_renderScale()/CrossPointPrefs_wantsScreenAwake() in
// src/simulator_main.cpp -- there is no shared macro for this because those
// two calls are the only precedent, and this file is not compiled by the app
// target either, so the detection has to be repeated here rather than reused.
#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif
#if defined(__APPLE__) && TARGET_OS_IPHONE
#include "CrossPointPrefs.h"
#define CROSSPOINT_HAL_READING_EXPERIMENT_GATE 1
#else
#define CROSSPOINT_HAL_READING_EXPERIMENT_GATE 0
#endif

#include <array>
#include <cmath>
#include <atomic>
#include <climits>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <mutex>
#include <random>
#include <string>
#include <thread>
#include <vector>

static SDL_Window *window = nullptr;
static SDL_Renderer *sdl_renderer = nullptr;
static SDL_Texture *texture = nullptr;
// THE GLASS AS IT LAST STOOD -- the whole composed frame at OUTPUT resolution:
// the page, the letterpress over it, the surround the page sits on and the
// button pad, everything a viewer could see, and NOT the trail already drawn
// over them (see captureGlass for why that exclusion is the whole ballgame).
//
// It replaced a PANEL-sized copy of the previous framebuffer -- the "ghost" --
// on 2026-08-26, and the reason is the owner's ruling that day: "apply
// persistence and other crt effects equally to paper and panel." A panel-sized
// previous frame can only ever feed a panel-sized effect. Two consumers:
//
//   glassPrevTexture       the beam's old picture, in COLOUR, drawn 1:1
//   glassIntensityTexture  max(r,g,b) of the same frame -- the phosphor
//                          deposit, so the composite's colour mod can paint the
//                          trail toward a cascade's surviving layer (a multiply
//                          can only REMOVE channels, so a coloured deposit's
//                          trail could never change hue -- owner 2026-08-21)
//
// Null whenever neither effect is on, which is the desktop default.
static SDL_Texture *glassPrevTexture = nullptr;
static SDL_Texture *glassIntensityTexture = nullptr;
static int glassW = 0, glassH = 0;
// The pixelBufSeq the capture belongs to, and whether one has ever landed.
static uint64_t glassSeq = 0;
static bool glassHasPicture = false;
// How long a ghost lives, in ms. 0 = the effect is off entirely.
static std::atomic<float> glowTrailMs{0.0f};

// BEAM PAINT: how long the new frame takes to sweep in from the top, in ms.
// 0 is off, and off is the default and the whole desktop behaviour.
//
// A CRT does not swap pictures, it DRAWS them -- one line at a time, top to
// bottom, at the field rate. Everything above the beam is the new frame and
// everything below it is still the old one. That is a different claim from the
// glow: the glow says what happens to a pixel AFTER it is lit, the beam says
// the picture arrives progressively rather than at once.
static std::atomic<float> beamPaintMs{0.0f};

// PAGE FADE (ST-010): how long the page takes to decay after the last thing the
// reader did, in milliseconds. 0 is off, and off is the default.
//
// Distinct from the glow, and the distinction is the whole feature. The glow
// fades the PREVIOUS page out as the next arrives -- a transition, over in a
// fraction of a second. This fades the page you are CURRENTLY READING, over
// seconds or minutes, the way a phosphor screen goes on dimming after the beam
// has moved on.
//
// It decays toward the PAPER, not toward a mid grey: a phosphor dying, which is
// what was asked for. That falls out for free -- the field behind the panel is
// already cleared to the paper tone, so alpha on the panel texture IS a fade
// toward paper, in the right direction for both polarities.
//
// AND IT STOPS AT A FLOOR. A page that fades to nothing is a page you cannot
// finish reading, so the decay runs to kPageFadeFloor and holds there until
// something re-energises it. Any input does (notePageInteraction), which is the
// e-ink equivalent of the beam coming back round.
static std::atomic<float> pageFadeMs{0.0f};
// WHEN THE FADE OWES ITS NEXT FRAME (SDL ticks), 0 when it owes none. The fade
// is the one animation whose steps are minutes apart rather than milliseconds,
// so it cannot drive itself by re-arming pendingPresent every present without
// drawing hundreds of identical frames between the ones that differ. It parks
// the due time here instead and presentIfNeeded's gate wakes on it.
static std::atomic<uint64_t> pageFadeStepDueMs{0};
static std::atomic<uint64_t> lastInteractionMs{0};

// HOW FAR it fades, as a percentage of that floor that is KEPT. 100 is the
// legible floor and the default -- an install that never touches this renders
// exactly what the paragraph above describes. 0 is fully transparent: the page
// goes all the way to paper and is gone. Owner-elected, and the legibility
// numbers it gives up are written out at pagefade::floorFor().
static std::atomic<int> pageFadeDepth{pagefade::kDepthFull};

// 0.75, and the number is measured rather than chosen. The first draft of this
// said 0.55 and claimed it held "every one above 6:1" -- it does not: at 0.55
// the worst row (Blue, P11) falls to 2.88:1, below even WCAG AA for LARGE text.
// Swept across every phosphor row in both polarities, worst case against the
// row's own paper:
//
//   floor 0.55 -> 2.88:1     floor 0.70 -> 4.04:1
//   floor 0.60 -> 3.23:1     floor 0.75 -> 4.49:1   <- AA body text, 4.5:1
//   floor 0.65 -> 3.62:1     floor 0.80 -> 4.99:1
//
// So 0.75 is the DEEPEST fade that still leaves a page of prose at the body-text
// bar. A floor of 0 would be prettier and unreadable, which is the trade this
// setting exists to make carefully.
static constexpr float kPageFadeFloor = 0.75f;
static uint64_t beamStartedAt = 0;

// The tint a two-layer phosphor's trail decays toward, packed 0x00RRGGBB, or
// kNoGlowTail when the trail simply dims. See setPanelGlowTail.
static constexpr uint32_t kNoGlowTail = 0xFFFFFFFFu;
static std::atomic<uint32_t> glowTailTint{kNoGlowTail};
// When the trail's hue handover completes, ms after a deposit -- the moment
// everything faster than the surviving phosphor has died. 0 = unknown, and the
// recolor ramps across the whole trail as it always did.
static std::atomic<float> glowTailOnsetMs{0.0f};
// WHAT `texture` ALREADY HOLDS. See the upload in presentIfNeeded: a trail
// present re-uploaded an unchanged framebuffer 60-80 times per page turn, and
// this triple is the "already there" test. Main thread only, like the upload.
// The texture POINTER is part of the key because applyWindowGeometryIfNeeded
// recreates the texture and a fresh STREAMING texture holds nothing.
static SDL_Texture *uploadedTexture = nullptr;
static uint64_t uploadedSeq = 0;
static size_t uploadedLive = 0;

// The pixelBufSeq the last PRESENTED frame was drawn from. A seq this has not
// seen means the firmware (or a polarity reconvert) wrote a new picture, which
// is what starts a beam sweep and what lands a phosphor deposit.
static uint64_t presentedSeq = 0;
// Render the simulator at full panel size. The previous 0.5x window was too
// small. With 1:1 pixel mapping, the simulator can be used for testing fine
// details.
//
// CROSSPOINT_SIM_WINDOW_SCALE overrides it (1-4). The window is sized in
// LOGICAL panel pixels, so at CROSSPOINT_RENDER_SCALE > 1 a headless run
// (SDL_VIDEODRIVER=dummy, no Retina backing store) presents the larger
// framebuffer into a panel-sized surface and CROSSPOINT_SIM_SCREENSHOTS
// captures it downsampled. Setting this to RENDER_SCALE makes the capture
// 1:1 with the framebuffer, which is what a rasterisation comparison needs.
static int simulatorWindowScale() {
  static const int scale = [] {
    const char *env = std::getenv("CROSSPOINT_SIM_WINDOW_SCALE");
    if (!env || env[0] == '\0')
      return 1;
    const int v = std::atoi(env);
    return (v >= 1 && v <= 4) ? v : 1;
  }();
  return scale;
}

// CROSSPOINT_SIM_DEVICE_PIXELS=1: size the window so one panel pixel lands on
// one DEVICE pixel. A window sized in logical points shows each panel pixel
// across contentScale^2 device pixels on a HiDPI display -- physically about
// twice the panel's real size on a Retina Mac, which reads as "zoomed 2x"
// next to the hardware. Dividing the point size by the display content scale
// undoes that; CROSSPOINT_SIM_WINDOW_SCALE then multiplies on top, so
// SCALE=2 + DEVICE_PIXELS=1 is an exact 2x-device-pixel presentation.
//
// Opt-in, not the default: the full-panel-size window is a deliberate desktop
// choice (see the comment above simulatorWindowScale) and headless capture
// geometry depends on it. The Mac app bundles set this via LSEnvironment.
static bool simulatorWantsDevicePixels() {
  static const bool wants = [] {
    const char *env = std::getenv("CROSSPOINT_SIM_DEVICE_PIXELS");
    return env && env[0] == '1';
  }();
  return wants;
}

// Pixel buffer written by the render task, read by the main thread for
// SDL_RenderPresent. On macOS, SDL calls must happen on the main thread.
static uint32_t
    pixelBuf[HalDisplay::DISPLAY_WIDTH * HalDisplay::DISPLAY_HEIGHT];
static std::mutex pixelBufMutex;
// Bumped by every writer of pixelBuf. The glow needs to know "is this a NEW
// picture?", and asking the PIXELS that question cost a memcmp over the whole
// active framebuffer on every present -- ~15 MB at 3x, and while a trail is
// alive it presents every frame. The writers already know, so they say so, and
// the comparison is one integer. Under pixelBufMutex like the buffer itself.
static uint64_t pixelBufSeq = 0;
// The pixelBufSeq produced by a POLARITY RECONVERT, or 0. A reconvert rewrites
// every pixel from the cached planes, so it bumps the seq exactly like a new
// page -- and until 2026-08-30 the CRT beam read that bump as new content and
// armed a fresh sweep. The sweep then revealed the NEW palette over the OLD one
// top-down across 55 ms, so a dark/light switch rendered frames with the top of
// the page in one palette and the rest in the other. Captured on video: one
// frame with a paragraph's first line dark-on-cream and every line below it
// light-on-dark, the sheet's own geometry never moving. Owner, 2026-08-30:
// "be sure not to flash from Zen mode to out of Zen mode for any reason,
// period" -- reported AS a zen flash, because that is what it looks like.
// S-031. The texture still uploads and the frame still presents; only the beam
// is withheld, because there is no new picture to sweep IN.
static uint64_t reconvertSeq = 0;
static std::atomic<bool> pendingPresent{false};
// THE GLASS'S SECOND INPUT (src/GlassCapture.h). Bumped by every present
// request that is not one of the two self-driving loops (the sweep and the
// trail re-arm pendingPresent directly, below, and change nothing the capture
// should see). Sampled once at the TOP of each present and compared against
// the generation the glass was captured at, so a present the overlay asked
// for -- the pad laid out, a keyboard, a zen toggle -- re-reads the glass even
// though the page did not move. S-035: the first present of a session composes
// a BLACK glass (zen band over a zero geometry), the pad's own layout requests
// the real frame one present later with the same page seq, and the seq-only
// gate kept the black one for the first sweep to reveal.
static std::atomic<uint64_t> glassDirtyGen{0};
static uint64_t glassGen = 0;  // the generation glassPrevTexture was read at
static inline void requestDirtyPresent() {
  glassDirtyGen.fetch_add(1, std::memory_order_relaxed);
  pendingPresent.store(true);
}
// Set when the inversion flag changes so presentIfNeeded (main thread) re-runs
// the framebuffer-to-pixel conversion from the cached last frame. Without it a
// polarity flip would wait for the next firmware refresh -- which on an e-ink
// device may never come.
static std::atomic<bool> pendingReconvert{false};
// Written by HalGPIO::update() (which owns SDL event polling); read by
// shouldQuit().
std::atomic<bool> quitRequested{false};

// CROSSPOINT_SIM_LOG_POWER=1: grep-able [power] lines at every station of the
// sleep -> wake -> reboot path. Added for the 2026-08-21 device report (a
// corrupted band frozen across the top of the page after a power press); this
// is the instrumentation the NEXT power report gets read against. Off by
// default and costs one getenv at stations that fire at most once per
// sleep/wake, never per frame.
static bool powerLogWanted() {
  const char *e = std::getenv("CROSSPOINT_SIM_LOG_POWER");
  return e && e[0] == '1';
}
// CROSSPOINT_SIM_LOG_TIMING=1: what a present actually costs, per pass.
//
// The roadmap's prerequisite (docs/surface-roadmap.md section 4c): a page turn
// pays for one or two panel-field builds, a sheet-field build and a
// full-output GPU readback, all on the main thread inside presentIfNeeded, and
// nothing had ever measured it -- so every proposal that adds a fifth field
// was being argued blind. The measured table is in that section, and three of
// its four assumptions were wrong: the readback is 2-6% of a page turn rather
// than the top cost, the panel field is 490 ms of a 700 ms page turn at 3x,
// and it rebuilds 1.3 times per page rather than twice because the present
// hold usually swallows the 1-bit pass.
//
// LATCHED, not read per present, and that is the whole point of the shape. An
// instrument that adds a getenv and a clock read to every pass it measures
// cannot report the cost of those passes honestly. Unset, every station below
// is a branch on a bool that is false and no clock is read at all.
// CROSSPOINT_SIM_LOG_PRESENTS / _LOG_SCREEN: LATCHED, for the reason spelled out
// at timingLogWanted() below and for one more that is specific to these two.
// Between them they were read SIX times per present -- five in presentIfNeeded
// alone -- and getenv on this platform takes a lock and walks `environ`. Unset,
// each is now a branch on a bool. It also makes them behave like every other
// instrument here: read once, at the first present, so a run cannot change
// instrument mid-flight and report two different things under one name.
static bool presentLogWanted() {
  static const bool wanted = [] {
    const char *e = std::getenv("CROSSPOINT_SIM_LOG_PRESENTS");
    return e && e[0] == '1';
  }();
  return wanted;
}
static bool screenLogWanted() {
  static const bool wanted = [] {
    const char *e = std::getenv("CROSSPOINT_SIM_LOG_SCREEN");
    return e && e[0] == '1';
  }();
  return wanted;
}
static bool timingLogWanted() {
  static const bool wanted = [] {
    const char *e = std::getenv("CROSSPOINT_SIM_LOG_TIMING");
    return e && e[0] == '1';
  }();
  return wanted;
}

// One pass's verdict for this present, and the whole present's stations.
// MOVED to src/SurfaceTiming.h on 2026-08-25: the surface passes are moving
// into their own translation units and each writes its own station, so the
// type has to be visible from more than one file. The env read below, the one
// instance and the [timing] line are still this file's.
using simtiming::PassTiming;
using simtiming::PresentTiming;
// Main thread only: every writer is either presentIfNeeded or an ensure*()
// that only presentIfNeeded calls.
static PresentTiming timingFrame;

// One-shot latches so the first update/refresh/present AFTER an in-process
// reboot announce themselves. Armed by the reboot Registrar below; checked
// (a plain bool) before any env read, so the off cost is nil.
static bool powerLogFirstRefresh = false;
static bool powerLogFirstPresent = false;
// Log-once for the sleep-screen veto below. At namespace scope rather than as a
// static local, because an iOS wake is a longjmp and a function-local static
// survives it -- a second sleep in one session would then drop its frames
// silently. Cleared at the reboot boundary with the rest.
static bool powerLogSleepVetoSaid = false;

// The display is on its way into deep sleep (HalDisplay::deepSleep has run;
// the firmware's only caller goes straight into the sleep loop from there and
// leaves it only through a reboot -- main.cpp:610). While this is set,
// presentIfNeeded treats the beam and the glow trail as OFF, so every present
// that still lands settles to the full sleep screen instead of freezing a
// transient on the glass. It cannot be a one-shot settle in deepSleep() itself:
// the sleep screen's antialiasing compose arrives on the render task ~15-50 ms
// AFTER deepSleep()'s flush, and its present restarted the beam -- proven by
// the [power] boundary log (sleep entry: beamStartedAt=0; reboot boundary:
// beamStartedAt=12207, accumLastAddMs=12220, both timestamps after the flush).
// Cleared at the in-process reboot boundary by the Registrar below; the
// desktop wake is execvp, where a fresh process clears it for free.
static std::atomic<bool> displaySleeping{false};

// See presentIfNeeded for why this is not simply panelIsDarkGround() at the
// moment it is read. Defaults false: a build that never presents a dark page
// never switches a tube off.
static std::atomic<bool> lastReadingDarkGround{false};

// --- THE POWER PATH LIVES IN src/SurfacePower.cpp ---------------------------
//
// The page the collapse squeezes, the flags saying whether this boot owes a
// warm-up, and the compositing of both animations moved there on 2026-08-25
// (Tier 2, docs/refactor-plan-2026-08-24.md). What stays here is the state they
// read -- the renderer, the panel texture, the presented rect, the two glass
// fields, the polarity latch above -- handed across by src/SurfacePower.h's
// accessors, defined further down this file.


static int currentWindowWidth = 0;
static int currentWindowHeight = 0;

// Presentation policy.
//
// The desktop window is 1:1 with the panel, so letterbox + linear filtering is
// right there: Bayer-dithered pixels average to a correct-looking gray, which is
// what the e-ink panel actually reads like to the eye.
//
// CROSSPOINT_SIM_PIXEL_EXACT flips both. When the panel is scaled up (the phone
// presents it at 2x), a fractional scale or a linear filter greys the dither and
// every rendering judgment made against it is a lie. Integer scale plus
// nearest-neighbor keeps one framebuffer pixel exactly N screen pixels.
//
// Keyed on the intent, not on the platform, so a desktop build can ask for exact
// pixels too.
//
// THAT ARGUMENT ONLY HOLDS WHEN MAGNIFYING, and the code applied it to both
// directions by omission. Below 1x -- which is where a 3x render scale lands on
// every iPhone, see panelScaleModeFor() -- point-sampling is not fidelity, it is
// undersampling: the panel has more pixels than the glass, so some are simply
// not drawn. Greying the dither is then the CORRECT answer rather than a lie,
// because averaging is exactly what the eye does to a page shown smaller than
// 1:1. Measured on the LightGray selection fill at the iPhone Air's 0.7955:
// nearest leaves 13.42 levels of low-frequency beat (the ST-008 moire), bilinear
// 3.29, an exact box filter 1.15, and at 1:1 all three are 0.
#if defined(CROSSPOINT_SIM_PIXEL_EXACT) && CROSSPOINT_SIM_PIXEL_EXACT
static constexpr SDL_RendererLogicalPresentation kLogicalPresentation =
    SDL_LOGICAL_PRESENTATION_INTEGER_SCALE;
static constexpr SDL_ScaleMode kPanelScaleMode = SDL_SCALEMODE_NEAREST;
#else
static constexpr SDL_RendererLogicalPresentation kLogicalPresentation =
    SDL_LOGICAL_PRESENTATION_LETTERBOX;
static constexpr SDL_ScaleMode kPanelScaleMode = SDL_SCALEMODE_LINEAR;
#endif

// The step a BELOW-1x panel scale is quantised to on the manual-placement path
// (presentIfNeeded). Above 1x the step is 1 and the panel is pixel-exact; below
// it, the point is only that the panel land on WHOLE device pixels, so this is
// the coarsest step for which it does.
//
// With scale = n / kPixelQuantum the presented panel is
// (DISPLAY_HEIGHT/g)*n x (DISPLAY_WIDTH/g)*n device pixels, whole by
// construction, and both halves of the dst rect (which is offset by half the
// framebuffer's dimensions from the panel's center) stay whole because the
// halving is folded into the quantum: g/2 rather than g. On X3 at 2x render
// scale that is gcd(1584, 1056)/2 = 264, i.e. steps of 0.38% -- far finer than
// the ~5% a small phone is short by, so quantising costs nothing visible.
static constexpr int gcdOf(int a, int b) { return b == 0 ? a : gcdOf(b, a % b); }
// Computed from the ACTIVE framebuffer, so it stopped being constexpr when the
// render scale did. The gcd differs per scale -- 264 at 2x on X3, 396 at 3x,
// 132 at 1x -- and using the ceiling's quantum at a lower scale would quantise
// to steps the presented panel does not actually land on, which is the whole
// fault this constant exists to prevent.
static float pixelQuantum() {
  const float q = static_cast<float>(
      gcdOf(HalDisplay::activeWidth(), HalDisplay::activeHeight()) / 2);
  return q >= 1.0f ? q : 1.0f;
}

// The texture filter for a given presented panel scale.
//
// Split from kPanelScaleMode because the two directions want opposite things
// and only the magnifying one was ever chosen deliberately (see above). At or
// above 1x the policy is unchanged, byte for byte. Below 1x the panel is being
// resampled no matter what this returns, so the only question is whether the
// resample is filtered or aliased, and bilinear is the filtered one the GPU
// already has.
//
// An exact box filter would be better still (1.15 vs 3.29 residual on the
// selection dither) because bilinear's kernel is one source texel wide while
// the footprint here is ~1.26 -- but that needs a software pass over the
// framebuffer and a second texture, and this recovers the large majority of it
// for two lines and no per-present cost.
static SDL_ScaleMode panelScaleModeFor(float scale) {
  return scale < 1.0f ? SDL_SCALEMODE_LINEAR : kPanelScaleMode;
}

namespace {

struct GrayscalePreviewState {
  std::array<uint8_t, HalDisplay::BUFFER_SIZE> bwBase{};
  std::array<uint8_t, HalDisplay::BUFFER_SIZE> lsbPlane{};
  std::array<uint8_t, HalDisplay::BUFFER_SIZE> msbPlane{};
  bool bwBaseValid = false;
  bool lsbValid = false;
  bool msbValid = false;
};

GrayscalePreviewState grayscalePreviewState;
std::array<uint8_t, HalDisplay::BUFFER_SIZE> frameBufferStorage{};
// ATOMIC rather than a plain bool (2026-08-29, the last unfulfilled sub-item
// of S-004): getFrameBuffer()/lendFrameBufferStorage()/
// returnFrameBufferStorage() are reached from firmware code with no
// pixelBufMutex of their own in the loop -- unlike frameBufferStorage's other
// readers/writers a few lines below, which do hold it. Hardening, not a fix
// for an observed bug: nothing has shown these three racing in practice.
std::atomic<bool> frameBufferLent{false};

struct ScreenshotEvent {
  unsigned long atMs;
  std::string path;
  bool handled = false;
};

std::vector<ScreenshotEvent> screenshotEvents;
bool screenshotEventsInitialized = false;
const std::thread::id simulatorMainThread = std::this_thread::get_id();

// Same reason as the GPIO one: re-read CROSSPOINT_SIM_SCREENSHOTS after an
// in-process reboot, so the promoted *_AFTER_WAKE schedule is actually honored.
const simreset::Registrar gDisplayRebootReset{[] {
  screenshotEventsInitialized = false;
  screenshotEvents.clear();
  // The loan does not survive a reboot. A reboot can land mid-book-build --
  // every file transfer ends in the firmware's silentRestart() -- and the
  // longjmp abandons the borrower's stack with the loan still open, so
  // getFrameBuffer() answered nullptr for the rest of the session: a frozen
  // panel. Take the storage back exactly as returnFrameBufferStorage() would.
  frameBufferStorage.fill(0xFF);
  frameBufferLent = false;
  // The page fade's clock. lastInteractionMs rides SDL_GetTicks, which no
  // reboot re-bases, so with the shipped 5-minute fade a device slept longer
  // than that woke up already dimmed until the first touch. A boot is an
  // interaction: the owner just pressed POWER.
  lastInteractionMs.store(SDL_GetTicks());
  // The panel upload's "already there" key. On iOS the reboot is a longjmp and
  // the window, the renderer and `texture` all survive it, so the key would
  // still be true and the skip would still be correct -- but the whole point of
  // this registry is that a static which outlives a reboot is a trap, and one
  // redundant upload on the first post-reboot present is not worth reasoning
  // about a second time.
  uploadedTexture = nullptr;
  uploadedSeq = 0;
  uploadedLive = 0;
}};

void initializeScreenshotEvents() {
  if (screenshotEventsInitialized)
    return;
  screenshotEventsInitialized = true;

  const char *schedule = std::getenv("CROSSPOINT_SIM_SCREENSHOTS");
  if (!schedule || schedule[0] == '\0')
    return;

  const std::string spec(schedule);
  size_t start = 0;
  while (start < spec.size()) {
    const size_t end = spec.find(';', start);
    const std::string item = spec.substr(
        start, end == std::string::npos ? std::string::npos : end - start);
    const size_t colon = item.find(':');
    if (colon != std::string::npos && colon + 1 < item.size()) {
      screenshotEvents.push_back(
          {std::strtoul(item.substr(0, colon).c_str(), nullptr, 10),
           item.substr(colon + 1)});
    }
    if (end == std::string::npos)
      break;
    start = end + 1;
  }
}

bool hasDueScreenshot() {
  initializeScreenshotEvents();
  const unsigned long now = millis();
  for (const auto &event : screenshotEvents) {
    if (!event.handled && event.atMs <= now)
      return true;
  }
  return false;
}

bool saveRendererBmp(const std::string &path) {
  int width = 0;
  int height = 0;
  if (!SDL_GetCurrentRenderOutputSize(sdl_renderer, &width, &height) ||
      width <= 0 || height <= 0) {
    std::cerr << "[SIM] Cannot determine screenshot size: " << SDL_GetError()
              << std::endl;
    return false;
  }

  // Read the WHOLE OUTPUT, not the logical viewport. SDL_RenderReadPixels(NULL)
  // reads the current viewport, which under logical presentation is the panel's
  // letterboxed rect -- so on a host that reserves bands for its own chrome (the
  // phone) the capture silently cropped to the page and could not show where the
  // page sat on the screen or what was in the bands. That is precisely what a
  // capture is wanted for when the placement itself is in question. On desktop
  // the window IS the panel, so the two rects coincide and this changes nothing.
  int logW = 0, logH = 0;
  SDL_RendererLogicalPresentation logMode = SDL_LOGICAL_PRESENTATION_DISABLED;
  SDL_GetRenderLogicalPresentation(sdl_renderer, &logW, &logH, &logMode);
  if (logMode != SDL_LOGICAL_PRESENTATION_DISABLED)
    SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                     SDL_LOGICAL_PRESENTATION_DISABLED);

  // SDL3's SDL_RenderReadPixels returns a new surface rather than filling a
  // caller-provided buffer, so the intermediate vector and the
  // CreateRGBSurfaceWithFormatFrom wrapper the SDL2 path needed are both gone.
  SDL_Surface *surface = SDL_RenderReadPixels(sdl_renderer, nullptr);

  if (logMode != SDL_LOGICAL_PRESENTATION_DISABLED)
    SDL_SetRenderLogicalPresentation(sdl_renderer, logW, logH, logMode);

  if (!surface) {
    std::cerr << "[SIM] Cannot create screenshot surface: " << SDL_GetError()
              << std::endl;
    return false;
  }

  // SDL3 returns true on success where SDL2 returned 0.
  const bool saved = SDL_SaveBMP(surface, path.c_str());
  if (!saved) {
    std::cerr << "[SIM] Cannot save screenshot " << path << ": "
              << SDL_GetError() << std::endl;
  } else {
    std::cerr << "[SIM] Saved screenshot: " << path << std::endl;
  }
  SDL_DestroySurface(surface);
  return saved;
}

void captureDueScreenshots() {
  const unsigned long now = millis();
  for (auto &event : screenshotEvents) {
    if (event.handled || event.atMs > now)
      continue;
    event.handled = true;
    saveRendererBmp(event.path);
  }
}

// Panel palette: the 1bpp/AA framebuffer is presented as tinted ink on tinted
// paper rather than raw #000-on-#FFF. One palette per polarity; "inverted"
// (dark mode) swaps to light ink on dark paper, so the grayscale ramp needs no
// separate 255-level flip -- the ink->paper lerp direction IS the inversion.
//
// THE TONES ARE A DIAL NOW, not constants; the definitions, the presets, the
// interpolation and the guards live in src/PanelPalette.h, and the host sets
// them through SimulatorOverlay::setPanelPalette. Both polarities default to
// exactly what this file used to hardcode, so a build that never calls the
// setter -- every desktop build -- renders byte-identical pixels.
//
// PACKED INTO ONE ATOMIC PER POLARITY. The render task reads these while the
// main thread (the iOS settings poll) writes them, and a Palette is six bytes
// that must change together: reading a new ink beside an old paper for one
// frame would show a page nobody chose. 48 bits fit in a uint64_t, so the whole
// pair is one lock-free load.
using PanelPalette = panelpalette::Palette;

constexpr uint64_t packPalette(const PanelPalette &p) {
  return (static_cast<uint64_t>(panelpalette::pack(p.ink)) << 24) |
         static_cast<uint64_t>(panelpalette::pack(p.paper));
}
PanelPalette unpackPalette(uint64_t v) {
  PanelPalette p{};
  panelpalette::unpackInto(static_cast<uint32_t>((v >> 24) & 0xFFFFFFu), p.ink);
  panelpalette::unpackInto(static_cast<uint32_t>(v & 0xFFFFFFu), p.paper);
  return p;
}

std::atomic<uint64_t> panelPackedLight{packPalette(panelpalette::kDefaultLight)};
std::atomic<uint64_t> panelPackedDark{packPalette(panelpalette::kDefaultDark)};

// Is the page currently painted on a DARK ground? The glow asks, because a
// phosphor's additive behavior only makes sense against one -- see the blend
// choice in presentIfNeeded. Measured off the live paper rather than off the
// appearance flag, so a custom palette with a dark paper in light mode still
// gets the emissive treatment.
bool panelIsDarkGround();

// The pair the HOST published -- the stock's own tone, before this page's
// sheet drift. Only two callers want it: the letterbox clear color (the device
// around the sheet, not the sheet) and the drift itself.
PanelPalette publishedPanelPalette(bool dark) {
  return unpackPalette(dark ? panelPackedDark.load() : panelPackedLight.load());
}

} // namespace

// THE HOST HALF OF A LEDGER LINE -- what the page was PAINTED with, as against
// the typography the firmware laid it out with.
//
// Declared in ReadingLog.h and defined HERE because this file is the only one
// that knows the live polarity and the live pair. Putting it the other way
// round would make ReadingLog.h include the display, and a pure model that
// cannot be compiled in a host test with no SDL is not a pure model.
//
// The PUBLISHED pair, not the drifted one: the drift is a per-leaf offset of at
// most two code values (LightInkPalette.h), so recording it would give every
// page its own config id and shatter the very comparison the ledger exists to
// make. The sheet a page is printed on is not a setting.
namespace readinglog {
HostSnapshot hostSnapshot() {
  HostSnapshot h;
  const SimulatorBuildIdentity id = localBuildIdentity();
  h.device = id.device;
  h.renderScale = cp::renderScale();
  h.panelW = id.logicalWidth;
  h.panelH = id.logicalHeight;
  h.dark = display.isInverted();
  const PanelPalette pal = publishedPanelPalette(h.dark);
  h.ink = (static_cast<uint32_t>(pal.ink[0]) << 16) | (static_cast<uint32_t>(pal.ink[1]) << 8) |
          static_cast<uint32_t>(pal.ink[2]);
  h.paper = (static_cast<uint32_t>(pal.paper[0]) << 16) | (static_cast<uint32_t>(pal.paper[1]) << 8) |
            static_cast<uint32_t>(pal.paper[2]);
  // experiment / arm / armSeed -- Phase 2's stop switch (docs/reading-
  // experiments.md §7, Decision 1: owner ruling 2026-08-29, "yes -- add the
  // row, default off"). See CROSSPOINT_HAL_READING_EXPERIMENT_GATE above for
  // why this is guarded rather than an unconditional call.
  //
  // armCount is pinned at 1: no arm-to-setting mapping has been built or
  // ruled on (docs §7's ranking of font size / line spacing / family is a
  // recommendation for FUTURE work, not an implementation this repo has). By
  // readingarm::armIndex()'s own documented contract, armCount<=1 always
  // answers 0 -- "an experiment with one arm is not an experiment, and the
  // safe reading of that is 'leave the settings alone'" -- so switching the
  // row on changes nothing the reader sees today; it only starts naming a
  // (still inert) experiment in the log, so the stop switch already exists
  // for the day real variation lands, instead of arriving at the same time
  // as a behavior change that would need one.
#if CROSSPOINT_HAL_READING_EXPERIMENT_GATE
  if (CrossPointPrefs_readingExperimentsEnabled()) {
    (void)readingarm::armIndex(/*seed=*/0, /*bookKey=*/0, /*spineIndex=*/0,
                               /*armCount=*/1);
    h.experiment = "phase2_gate";
    h.arm = "0";
  }
#endif
  return h;
}
} // namespace readinglog

namespace {

// THE TONES THIS PAGE IS PAINTED IN -- the published pair with the leaf's own
// sheet-to-sheet drift folded in. Defined below pageSheetSeed(), because that
// is where the page identity is turned into a seed; declared here because
// everything from the 1bpp->ARGB conversion down reads it.
//
// THE DRIFT LIVES HERE AND NOWHERE ELSE, and that is the whole design choice.
// This function is already the single read point for "what color is the
// page": the framebuffer conversion, the letterpress and sheet contrast
// budgets, the grain's amplitude, the page fade's floor and every field cache
// key all come through it. Applying the offset at the one read means no
// consumer can be forgotten and none can be told twice -- and every field key
// already folds live.paper, so a drifted page rebuilds its fields and can
// never be served a neighbouring leaf's. The alternative, drifting the tone
// where the host publishes it, would put the offset in two places at once
// (iOS PanelPrefs and the desktop settings watch) and leave the desktop and
// the phone free to disagree about what page 47 looks like.
PanelPalette livePanelPalette(bool dark);

bool panelIsDarkGround() {
  const PanelPalette pal = livePanelPalette(display.isInverted());
  // Rec.601-ish luma is plenty for "is this closer to black than to white".
  const int luma = (pal.paper[0] * 299 + pal.paper[1] * 587 + pal.paper[2] * 114) / 1000;
  return luma < 128;
}

// Whether the page claims to be EMITTING light rather than reflecting it, which
// decides how a partly-covered pixel is mixed. Set by the host per palette (the
// iOS shim, from whether the preset names a phosphor) and by
// CROSSPOINT_SIM_PANEL_EMISSIVE for a desktop run. Default false: an e-ink page
// reflects, and every previously shipped pixel must stay exactly where it was.
std::atomic<bool> panelEmissive{false};

// THE FULL-SCREEN FLASH, and why a present can be held back.
//
// A page with antialiased text is painted TWICE. The firmware displays the
// 1-bit page, then TextAntiAliasing::overlay renders the two grayscale planes
// over it and calls displayGrayBuffer, which composes the real page some 13-22
// ms later (measured, desktop, reader page turn). Both hit the screen. The first
// one is a hard black-and-white rendering of the page you are about to get, and
// on a 60 Hz screen it reads as a full-screen flash.
//
// On the device that first pass is not a choice -- an e-ink panel has to drive
// every pixel hard before it can hold an intermediate level, and you watch it
// happen. Reproducing it here reproduces the PROCESS rather than the result,
// and the phone has none of the physics that made it necessary.
//
// So a present is held for a short window, and a compose landing inside that
// window releases it -- the composed page presents, the 1-bit one never does.
// Nothing is dropped: the frame stays OWED (pendingPresent is not consumed), so
// if no compose follows -- every menu, every 1-bit screen -- the deadline
// expires and that same frame presents, at most kPresentHoldMs late.
//
// It has to cover EVERY paint rather than just the grayscale ones, and that was
// measured rather than assumed: the first version armed only in
// displayGrayscaleBase, which the reader never calls. The BW pass arrives
// through plain displayBuffer, and the only signal that a compose is coming
// arrives after it -- so there is nothing to key on, and the hold is
// unconditional.
std::atomic<uint64_t> presentHoldUntil{0};

// Which producer wrote the pixels currently in pixelBuf: 'B' the 1-bit pass,
// 'G' the composed grayscale one. Diagnostic only, read by the present log --
// but it is the diagnostic that distinguishes "the flash is gone" from "the
// composed page is gone", which a present COUNT alone cannot.
std::atomic<char> lastPixelWriter{'?'};

// Longer than the widest observed gap (22 ms) with margin. The cost when no
// compose follows is that a 1-bit screen paints this many ms late, which is
// under two frames and nothing a person can see; the alternative is the flash.
// CROSSPOINT_SIM_PRESENT_FLASH=1 restores the old behaviour for anyone who
// wants the device's process rather than its result.
constexpr uint64_t kPresentHoldMs = 30;

// How long a flash stays on screen once presentFlash asks for one. The
// composed pass is only 13-22 ms behind the 1-bit pass, and presents run
// continuously at ~15 ms, so WITHOUT a deadline the flash is one or two frames
// -- which is what "it didn't work" was: it fired every time, too briefly to
// register. 70 ms is ~4 frames at 60 Hz and reads as a blink.
constexpr uint64_t kPresentFlashMs = 70;
std::atomic<uint64_t> presentFlashUntil{0};

// AND THE EXTENSION, which is the half that makes this work at 3x.
//
// 30 ms was measured against an 800x480 panel, where a compose takes 13-22 ms.
// At 3x the framebuffer is 2376x1584 and a compose measures 115-271 ms, so the
// deadline expired every single time and the 1-bit frame presented -- the flash
// came straight back, on the phone only. It could not be reproduced on the
// desktop because there the firmware renders and presents on ONE thread, so
// nothing can slip in between the two passes; on iOS the render task is a real
// thread and the display link presents concurrently.
//
// A deadline alone cannot be right at every render scale, so it is no longer
// asked to be. When the firmware starts writing AA plane strips we KNOW a
// compose is coming -- that signal arrives after the 1-bit paint and well
// before the composed frame -- so the hold is extended to cover it. Still
// bounded: if a compose is abandoned mid-way the page must recover rather than
// sit on the previous frame forever.
constexpr uint64_t kPresentHoldExtendedMs = 2000;

// OWNER-SETTABLE as of 2026-08-19, and no longer read once at first use.
//
// It was a `static const bool` initialised from the env on first call, which is
// exactly the shape that cannot become a setting: the first present latches it
// for the life of the process. Now an atomic, written through
// SimulatorOverlay::setPresentFlash, with the env still overriding so a headless
// run can force either behaviour.
std::atomic<bool> presentFlashFlag{false};

bool presentFlashWanted() { return presentFlashFlag.load(); }

// level: 0 = ink, 255 = paper (the pre-inversion grayscale convention).
//
// The emissive ramp is CACHED, because its transfer function is two std::pow
// calls per channel and this is called once per pixel per frame -- 1.2M pow
// calls a frame at 792x528, which is not a thing to do sixty times a second.
// Both callers (renderBwPixels, composeGrayscalePreview) hold pixelBufMutex for
// the whole loop, which is what makes a plain static safe here; if a third
// caller ever appears outside that lock, this needs its own.
// THE WHOLE 256-LEVEL RAMP, RESOLVED ONCE PER FRAME.
//
// This was a per-pixel function that did an atomic load and a cache-key compare
// on every pixel. At 3x that is 3.76 MILLION atomic loads per compose, and a
// compose measured 115-271 ms -- which mattered far beyond tidiness: the
// present hold that suppresses the page-turn flash is a DEADLINE, and a compose
// that takes 115 ms against a 30 ms deadline means the 1-bit frame presents
// every single time. The flash came back on the phone and could not be
// reproduced on the desktop, where render and present share a thread and
// nothing can slip in between them.
//
// So the ramp is built once, by whoever is about to write a frame, and indexed
// per pixel. Both writers hold pixelBufMutex for their whole loop.
struct LevelRamp {
  uint32_t lut[256];
  explicit LevelRamp(const PanelPalette &p) {
    if (panelEmissive.load()) {
      for (int i = 0; i < 256; i++)
        lut[i] = panelpalette::colorForLevelEmissive(static_cast<uint8_t>(i), p);
    } else {
      for (int i = 0; i < 256; i++)
        lut[i] = panelpalette::colorForLevel(static_cast<uint8_t>(i), p);
    }
  }
  uint32_t operator[](uint8_t level) const { return lut[level]; }
};

uint32_t panelColor(uint8_t level, const PanelPalette &p) {
  return panelEmissive.load() ? panelpalette::colorForLevelEmissive(level, p)
                              : panelpalette::colorForLevel(level, p);
}

// CROSSPOINT_SIM_PANEL_{INK,PAPER}_{LIGHT,DARK} force a tone, on the same terms
// as CROSSPOINT_SIM_DARK and for the same reason: the desktop has no
// Settings.app, so without this the only way to see a non-default palette --
// or to capture a screenshot proving one -- is a phone. Applied on EVERY
// setPanelPalette call, so a forced tone survives any number of host settings
// changes and both paths exercise identical mechanics from that line down.
// Unset or unparseable leaves the caller's value alone.
void applyPanelPaletteEnv(bool dark, PanelPalette &p) {
  const char *inkVar =
      dark ? "CROSSPOINT_SIM_PANEL_INK_DARK" : "CROSSPOINT_SIM_PANEL_INK_LIGHT";
  const char *paperVar = dark ? "CROSSPOINT_SIM_PANEL_PAPER_DARK"
                              : "CROSSPOINT_SIM_PANEL_PAPER_LIGHT";
  const int ink = panelpalette::parseHexRgb(std::getenv(inkVar));
  const int paper = panelpalette::parseHexRgb(std::getenv(paperVar));
  if (ink >= 0) panelpalette::unpackInto(static_cast<uint32_t>(ink), p.ink);
  if (paper >= 0)
    panelpalette::unpackInto(static_cast<uint32_t>(paper), p.paper);
}

bool getBit(const uint8_t *buffer, int x, int y) {
  const int byteIdx = (y * HalDisplay::activeWidth() + x) / 8;
  const int bitIdx = 7 - (x % 8);
  return (buffer[byteIdx] & (1 << bitIdx)) != 0;
}

// Both writers return the sequence number they produced, FROM UNDER THEIR OWN
// LOCK: reconvertLastFrame() hands it to presentIfNeeded as reconvertSeq. It
// used to be re-read under a second lock acquisition, and a render-task page
// landing in the gap would have been mistaken for the reconvert -- its sweep
// withheld, its trail still deposited (adversarial review 2026-09-04).
uint64_t renderBwPixels(const uint8_t *fb) {
  const std::lock_guard<std::mutex> lock(pixelBufMutex);
  const uint64_t seq = ++pixelBufSeq;
  const PanelPalette pal = livePanelPalette(display.isInverted());
  const LevelRamp ramp(pal);
  const uint32_t ink = ramp[0];
  const uint32_t paper = ramp[255];
  for (int y = 0; y < HalDisplay::activeHeight(); y++) {
    for (int x = 0; x < HalDisplay::activeWidth(); x++) {
      const bool white = getBit(fb, x, y);
      pixelBuf[y * HalDisplay::activeWidth() + x] = white ? paper : ink;
    }
  }
  lastPixelWriter.store('B');
  if (presentFlashWanted()) {
    // Show this pass, and set the deadline the compose below will wait for.
    presentFlashUntil.store(SDL_GetTicks() + kPresentFlashMs);
    presentHoldUntil.store(0);
  } else {
    presentHoldUntil.store(SDL_GetTicks() + kPresentHoldMs);
  }
  requestDirtyPresent();
  return seq;
}

void clearGrayscalePlanes() {
  grayscalePreviewState.lsbPlane.fill(0);
  grayscalePreviewState.msbPlane.fill(0);
  grayscalePreviewState.lsbValid = false;
  grayscalePreviewState.msbValid = false;
}

void snapshotBwBase(const uint8_t *fb) {
  memcpy(grayscalePreviewState.bwBase.data(), fb, HalDisplay::activeBufferSize());
  grayscalePreviewState.bwBaseValid = true;
  clearGrayscalePlanes();
}

void copyPlane(std::array<uint8_t, HalDisplay::BUFFER_SIZE> &dst,
               const uint8_t *src, bool &valid) {
  if (!src) {
    valid = false;
    dst.fill(0);
    return;
  }
  memcpy(dst.data(), src, HalDisplay::activeBufferSize());
  valid = true;
}

uint64_t composeGrayscalePreview() {
  const uint64_t composeStart = SDL_GetTicks();
  // ARM THE HOLD BEFORE ANY PIXEL IS WRITTEN. The compose overwrites pixelBuf
  // IN PLACE, so by the time the tail runs the flash frame is already gone and
  // holding there freezes the NEW page instead -- measured 2026-08-20: the
  // 1-bit frame presented at 12175 ms and the composed one at 12190, with the
  // 64 ms hold landing after it. Setting it here suppresses every present from
  // the first overwritten pixel to the deadline, which is the flash's length.
  {
    const uint64_t flashUntil = presentFlashUntil.load();
    if (flashUntil > composeStart) presentHoldUntil.store(flashUntil);
  }
  const std::lock_guard<std::mutex> lock(pixelBufMutex);
  const PanelPalette pal = livePanelPalette(display.isInverted());
  const LevelRamp ramp(pal);
  const uint8_t *bwBase = grayscalePreviewState.bwBaseValid
                              ? grayscalePreviewState.bwBase.data()
                              : display.getFrameBuffer();
  if (!bwBase) {
    // Buffer lent out: keep the last presented frame. RELEASE THE HOLD ANYWAY.
    // The plane-strip writes pushed the deadline out to 2 s on the promise that
    // a compose was coming; this is that compose declining, and without the
    // release the page freezes on the previous frame for the full two seconds.
    //
    // The seq bump also used to happen ABOVE this return, which told the next
    // present that the content had changed when it had not -- depositing a
    // duplicate of the current page into the accumulator and restarting the
    // beam. It now happens only on the path that actually writes pixels.
    presentHoldUntil.store(0);
    requestDirtyPresent();
    return 0;
  }
  const uint64_t seq = ++pixelBufSeq;
  for (int y = 0; y < HalDisplay::activeHeight(); y++) {
    for (int x = 0; x < HalDisplay::activeWidth(); x++) {
      const bool baseWhite = getBit(bwBase, x, y);
      const bool lsbActive =
          grayscalePreviewState.lsbValid &&
          getBit(grayscalePreviewState.lsbPlane.data(), x, y);
      const bool msbActive =
          grayscalePreviewState.msbValid &&
          getBit(grayscalePreviewState.msbPlane.data(), x, y);

      const uint8_t level =
          GrayscalePreview::previewLevel(baseWhite, msbActive, lsbActive);

      // No 255-level flip for inversion: the dark palette's ink->paper
      // direction already runs light-on-dark (see PanelPalette above).
      pixelBuf[y * HalDisplay::activeWidth() + x] = ramp[level];
    }
  }
  // The real page is ready, so whatever hold the base pass armed is over: this
  // frame presents at the first opportunity and the 1-bit one never does.
  // Env-gated AA audit. It exists because "the antialiasing looks bad" and "the
  // antialiasing is not there" look identical on a phone, and the second was the
  // truth: the planes were populated and the decode threw them away. Counting
  // the LEVELS the compose actually produces is the only thing that separates
  // the two.
  if (const char *e = std::getenv("CROSSPOINT_SIM_LOG_AA")) {
    if (e[0] == '1') {
      int flagged = 0, lv[256] = {0};
      for (int y = 0; y < HalDisplay::activeHeight(); y++)
        for (int x = 0; x < HalDisplay::activeWidth(); x++) {
          const bool bw = getBit(bwBase, x, y);
          const bool l = grayscalePreviewState.lsbValid &&
                         getBit(grayscalePreviewState.lsbPlane.data(), x, y);
          const bool m = grayscalePreviewState.msbValid &&
                         getBit(grayscalePreviewState.msbPlane.data(), x, y);
          if (l || m) flagged++;
          lv[GrayscalePreview::previewLevel(bw, m, l)]++;
        }
      int levels = 0;
      for (int i = 0; i < 256; i++)
        if (lv[i]) levels++;
      SDL_Log("[aa] %d flagged px -> %d distinct levels", flagged, levels);
      for (int i = 0; i < 256; i++)
        if (lv[i]) SDL_Log("[aa]   level %3d: %d px", i, lv[i]);
    }
  }
  if (presentLogWanted())
      SDL_Log("[compose] %llu ms for %dx%d",
              (unsigned long long)(SDL_GetTicks() - composeStart),
              HalDisplay::activeWidth(), HalDisplay::activeHeight());
  lastPixelWriter.store('G');
  // The composed frame WAITS OUT the flash. Holding it here is the whole
  // mechanism: the 1-bit frame is already on screen and the idle repaints keep
  // re-presenting it, so suppressing this one is what gives the flash length.
  const uint64_t flashUntil = presentFlashUntil.load();
  if (flashUntil <= SDL_GetTicks()) presentHoldUntil.store(0);
  requestDirtyPresent();
  return seq;
}

// Re-run the last framebuffer-to-pixel conversion after an inversion change,
// from the cached copies snapshotted by the render task. Runs on the main
// thread (presentIfNeeded); safe because the pixel/state buffers already
// tolerate the render task racing a present -- worst case is one torn frame
// that the next real render replaces.
//
// If grayscale AA planes were composited after the BW base, they are still
// cached alongside it (snapshotBwBase clears them on every fresh BW frame), so
// the reconversion keeps the AA gray levels instead of degrading to the BW
// base. If the render task happens to be mid-way through writing new planes,
// the recompose may briefly show them partially applied; the render task's own
// compose lands right after and corrects it.
// Returns the sequence the reconvert produced, 0 when nothing was written.
uint64_t reconvertLastFrame() {
  if (!grayscalePreviewState.bwBaseValid)
    return 0; // nothing presented yet; the first real render reads the new flag
  if (grayscalePreviewState.lsbValid || grayscalePreviewState.msbValid)
    return composeGrayscalePreview();
  return renderBwPixels(grayscalePreviewState.bwBase.data());
}

} // namespace

static bool isPortraitOrientation(GfxRenderer::Orientation orientation) {
  return orientation == GfxRenderer::Portrait ||
         orientation == GfxRenderer::PortraitInverted;
}

// The desktop window is sized in LOGICAL panel pixels, not framebuffer pixels.
// At RENDER_SCALE > 1 the framebuffer is bigger than the panel; sizing the
// window from it would give a window RENDER_SCALE times too large. Keeping the
// window at the logical size and letting SDL map the larger texture into it is
// also exactly what makes the extra detail visible: with
// SDL_WINDOW_HIGH_PIXEL_DENSITY a 528x792-point window has a 1056x1584-pixel
// backing store on a Retina display, so a 2x framebuffer lands 1:1 on screen.
static void getLogicalWindowSize(GfxRenderer::Orientation orientation,
                                 int *width, int *height) {
  const bool isPortrait = isPortraitOrientation(orientation);
  const int panelW = HalDisplay::activeWidth() / cp::renderScale();
  const int panelH = HalDisplay::activeHeight() / cp::renderScale();
  float w = static_cast<float>((isPortrait ? panelH : panelW) *
                               simulatorWindowScale());
  float h = static_cast<float>((isPortrait ? panelW : panelH) *
                               simulatorWindowScale());
  if (simulatorWantsDevicePixels()) {
    // One panel pixel -> one device pixel: shrink the point size by the
    // display's content scale (2.0 on Retina, 1.0 elsewhere). Read from the
    // primary display because the window may not exist yet on the first call.
    const float s = SDL_GetDisplayContentScale(SDL_GetPrimaryDisplay());
    if (s > 1.0f) {
      w /= s;
      h /= s;
    }
  }
  *width = static_cast<int>(SDL_roundf(w));
  *height = static_cast<int>(SDL_roundf(h));
}

// The logical presentation space is the FRAMEBUFFER's, not the window's. The
// dst rects in presentIfNeeded are in framebuffer pixels (kW/kH include
// RENDER_SCALE), so the logical size handed to SDL must match them and only
// the WINDOW size may track CROSSPOINT_SIM_WINDOW_SCALE / _DEVICE_PIXELS.
// Passing the window size here instead is the 2x-zoom bug: at RENDER_SCALE=2
// with a 1x window the texture was drawn double-size into a panel-sized
// logical space and only its top-left quarter was visible. The two sizes
// coincide at RENDER_SCALE=1 and at WINDOW_SCALE==RENDER_SCALE, which is why
// the plain desktop build and the phone/2x presentations never showed it.
static void getLogicalPresentationSize(GfxRenderer::Orientation orientation,
                                       int *width, int *height) {
  const bool isPortrait = isPortraitOrientation(orientation);
  *width = isPortrait ? HalDisplay::activeHeight() : HalDisplay::activeWidth();
  *height = isPortrait ? HalDisplay::activeWidth() : HalDisplay::activeHeight();
}

static void applyWindowGeometryIfNeeded(GfxRenderer::Orientation orientation) {
  if (!window || !sdl_renderer)
    return;

  int winW = 0;
  int winH = 0;
  getLogicalWindowSize(orientation, &winW, &winH);
  if (winW == currentWindowWidth && winH == currentWindowHeight)
    return;

  int logW = 0;
  int logH = 0;
  getLogicalPresentationSize(orientation, &logW, &logH);
  SDL_SetWindowSize(window, winW, winH);
  SDL_SetRenderLogicalPresentation(sdl_renderer, logW, logH,
                                   kLogicalPresentation);
  currentWindowWidth = winW;
  currentWindowHeight = winH;
}

namespace SimulatorOverlay {
static DrawFn overlayDraw = nullptr;
// Packed 0xRRGGBB. Defaults to the light panel's paper tone, so a host that
// never calls setClearColor (every desktop build) shows the panel seamlessly
// against its field.
static std::atomic<uint32_t> clearColor{0xFBFBF9u};
// Bottom band (device px) reserved for overlay chrome; see SimulatorOverlay.h.
static std::atomic<int> bottomInset{0};
// Top band (device px) reserved for host furniture -- status bar / Dynamic
// Island; see SimulatorOverlay.h.
static std::atomic<int> topInset{0};
void setDrawCallback(DrawFn fn) { overlayDraw = fn; }
void setClearColor(unsigned char r, unsigned char g, unsigned char b) {
  clearColor.store((static_cast<uint32_t>(r) << 16) |
                   (static_cast<uint32_t>(g) << 8) | static_cast<uint32_t>(b));
}
void setBottomInset(int px) {
  if (bottomInset.exchange(px > 0 ? px : 0) != px)
    requestPresent();
}
void setTopInset(int px) {
  const int v = px > 0 ? px : 0;
  if (topInset.exchange(v) != v)
    requestPresent();
}
// Written by presentIfNeeded (main thread) on the manual-placement path.
static std::atomic<int> panelBottom{0};
static std::atomic<int> panelHeight{0};
static std::atomic<int> panelLeft{0};
static std::atomic<int> panelWidth{0};
int panelBottomPx() { return panelBottom.load(); }
int panelHeightPx() { return panelHeight.load(); }
int panelLeftPx() { return panelLeft.load(); }
int panelWidthPx() { return panelWidth.load(); }
void requestPresent() { requestDirtyPresent(); }
// The single entry point for panel polarity (see SimulatorOverlay.h). The env
// override is applied here, on every call, so a forced polarity survives any
// number of platform theme changes, and so the headless env path and the iOS
// theme path exercise identical mechanics from this line down.
void setPanelDark(bool dark) {
  if (const char *forced = std::getenv("CROSSPOINT_SIM_DARK")) {
    if (forced[0] == '1' && forced[1] == '\0')
      dark = true;
    else if (forced[0] == '0' && forced[1] == '\0')
      dark = false;
    // Anything else (including empty) is treated as unset: follow the caller.
  }
  // The field follows the panel's paper tone, so the page has no visible edge
  // in either polarity. Hosts that call setClearColor themselves (the iOS
  // harness) use the same values, so the double write is idempotent. Reads the
  // LIVE palette rather than a constant, so a host that has set a custom paper
  // still gets an edgeless page after a polarity flip.
  //
  // The PUBLISHED tone, not the drifted one: the field is the device around
  // the sheet, and a surround that stepped with every page turn would be the
  // chrome flicker the drift's bound exists to avoid.
  const PanelPalette pal = publishedPanelPalette(dark);
  setClearColor(pal.paper[0], pal.paper[1], pal.paper[2]);
  display.setInverted(dark);
}

// See SimulatorOverlay.h. Writes the packed pair for ONE polarity, applies the
// env override on top (same contract as setPanelDark), and asks the main thread
// to reconvert the cached frame -- inversion's mechanism, reused, because a
// palette change has exactly inversion's problem: the tones are applied while
// converting the 1bpp framebuffer to pixels, and an e-ink firmware may not
// render again for minutes.
//
// The reconvert is requested only when the polarity being written is the one on
// screen. Writing the other polarity's pair is a store and nothing else, so the
// harness can publish both on every settings change without forcing a present.
void setPanelGlow(float trailMs) {
  // Same escape hatch as the palette: a desktop or headless run has no Settings
  // app, so the only way to reach this is the environment.
  if (const char *env = std::getenv("CROSSPOINT_SIM_PANEL_GLOW_MS")) {
    const float v = static_cast<float>(std::atof(env));
    if (v >= 0.0f) trailMs = v;
  }
  if (trailMs < 0.0f) trailMs = 0.0f;
  glowTrailMs.store(trailMs);
}

void setPageFade(float fadeMs) {
  if (const char *env = std::getenv("CROSSPOINT_SIM_PAGE_FADE_MS")) {
    const float parsed = static_cast<float>(std::atof(env));
    if (parsed >= 0.0f) fadeMs = parsed;
  }
  if (fadeMs < 0.0f) fadeMs = 0.0f;
  pageFadeMs.store(fadeMs);
  lastInteractionMs.store(SDL_GetTicks());
  requestDirtyPresent();
}

// ONE ENV PARSER for every integer dial below.
//
// strtol with the end pointer checked, never atoi: atoi answers 0 for anything
// it cannot parse, and 0 is a REAL SETTING for every dial here -- the grain
// switched off, a perfectly smooth sheet, a fully transparent page. A typo in
// a variable's VALUE would therefore look like the setting doing nothing,
// which is the one failure mode none of these can report.
//
// `minAccepted` is the floor a parsed value must reach to be believed at all,
// and the callers do not agree about it -- which is a real difference between
// them, not a tidiness problem, so it is a parameter rather than a rule:
//
//   0 (the default)   most dials. 0 is a choice; a negative one is not.
//   1                 setScanlineSize ONLY. Its 0 clamps to the finest pitch,
//                     so a typo and a deliberate 0 render identically and the
//                     0 has to be refused instead.
//   kAcceptAnyValue   the grain's coverage, cell count and mottle depth, which
//                     have always taken a NEGATIVE env value and let the pure
//                     model clamp it. Preserved deliberately: the strength dial
//                     beside them refuses negatives and these three do not, and
//                     a refactor is not the place to decide which is right.
//
// This sits ABOVE every caller on purpose. It used to sit in the middle of
// them, so the six dials defined above it each carried their own copy of the
// four lines below -- not because they differed, but because the helper was
// not in scope yet.
constexpr int kAcceptAnyValue = INT_MIN;

static int envPercentOr(const char *name, int fallback, int minAccepted = 0) {
  if (const char *env = std::getenv(name)) {
    char *end = nullptr;
    const long parsed = std::strtol(env, &end, 10);
    if (end != env && parsed >= minAccepted) return static_cast<int>(parsed);
  }
  return fallback;
}

void setPageFadeDepth(int depthPercent) {
  // 0 here is FULLY TRANSPARENT, not a harmless default -- see envPercentOr.
  depthPercent = envPercentOr("CROSSPOINT_SIM_PAGE_FADE_DEPTH", depthPercent);
  if (depthPercent < 0) depthPercent = 0;
  if (depthPercent > pagefade::kDepthFull) depthPercent = pagefade::kDepthFull;
  pageFadeDepth.store(depthPercent);
  // Repaint rather than wait: a settled page is already sitting at the OLD
  // floor and the firmware may not render again for minutes, so without this
  // the new depth would first appear at some unrelated page turn.
  requestDirtyPresent();
}

void notePageInteraction() {
  if (pageFadeMs.load() <= 0.0f) return;
  lastInteractionMs.store(SDL_GetTicks());
  // Come back at once rather than at the next page: the whole point is that
  // touching the device re-energises what you were reading.
  requestDirtyPresent();
}

void setBeamPaint(float sweepMs) {
  if (const char *env = std::getenv("CROSSPOINT_SIM_BEAM_MS")) {
    const float parsed = static_cast<float>(std::atof(env));
    if (parsed >= 0.0f) sweepMs = parsed;
  }
  if (sweepMs < 0.0f) sweepMs = 0.0f;
  beamPaintMs.store(sweepMs);
}

// PHOSPHOR GRAIN. Strength as a percentage of realistic (100 = realistic and
// the default, 0 = off, 1000 = the 10x the owner asked for) and which coverage
// shape spreads it. See src/PhosphorGrain.h for what those mean and why grain
// is the one CRT treatment that survived the 2026-08-18 ruling.
static std::atomic<int> grainStrength{phosphorgrain::kStrengthRealistic};
static std::atomic<int> grainCoverage{phosphorgrain::Even};
// The mottle's two dials. Depth is carried as HUNDREDTHS because that is how
// Settings.app persists it -- a picker stores integers, and 0/3/10/30 says
// exactly what the owner chose where a float would invite rounding drift.
static std::atomic<int> grainMottleCells{phosphorgrain::kMottleCellsDefault};
static std::atomic<int> grainMottleDepthPct{
    static_cast<int>(phosphorgrain::kMottleDepthDefault * 100.0f + 0.5f)};
// THE 2026-08-22 DOCTRINE SPLIT: light mode is paper-and-ink (letterpress),
// dark mode is CRT (scanlines, superseding the mottled grain there). Both
// default OFF so a build that never calls the setters -- every desktop build
// -- renders byte-for-byte what it always did; the iOS defaults live in
// CrossPointPrefs. See src/Letterpress.h, src/Scanlines.h and
// docs/letterpress-and-scanlines.md.
static std::atomic<int> letterpressStrength{letterpress::kStrengthOff};
// The SHEET's roughness, as a percent of the reference stock, from
// lightink::toothScaleFor(). 100 is the shipped Bright White, so a build that
// never calls the setter draws the tooth it always drew.
static std::atomic<int> paperToothPct{100};
// THE REST OF THE PAPER INSTRUMENT (owner order 2026-08-22: "make tooth,
// formation, pressure and all other paper variables sliders in the color
// button drawer"). Every one of these seeds at the value that reproduces what
// this repo already drew, so a desktop build -- which calls none of the
// setters -- is byte-identical.
//
// Formation is the exception worth naming: the SHEET pass has always passed
// letterpress::kFormationDepthDefault, so that, and not 0, is the unchanged
// value here.
static std::atomic<int> paperFormationPct{
    static_cast<int>(letterpress::kFormationDepthDefault * 100.0f + 0.5f)};
static std::atomic<int> paperDefectsPct{paperdefects::kDialOff};
// SHEET-TO-SHEET DRIFT: how far this leaf's paper tone may sit from the
// stock's. Off is the shipped value on both platforms, and off is bit-exact.
static std::atomic<int> paperDriftPct{lightink::kPaperDriftDefault};
// CHAIN AND LAID LINES, for a stock that carries them (lightink::Paper::laid;
// the iOS picker pushes the paper-strength percent for a laid stock and 0 for
// everything else). Off is the desktop default, so the canary is unchanged.
static std::atomic<int> laidLinesStrength{laidstructure::kStrengthOff};
// The press's three PART ratios, as percents of the standard press. 100 is the
// shipped composition, so an unseeded build renders exactly what it did.
static std::atomic<int> pressRingPct{100};
static std::atomic<int> pressDebossPct{100};
static std::atomic<int> pressPressurePct{100};
static std::atomic<int> scanlinesIntensity{scanlines::kIntensityOff};
// The raster's PITCH, as a percent of the source-row pitch. kSizeFine (100) is
// one line per page row -- build 126's only behaviour -- so an unseeded build
// renders exactly what it did before this dial existed.
static std::atomic<int> scanlineSize{scanlines::kSizeFine};
// How far beam current widens the spot, as a percent of the standard gain.
// kBloomStandard is what build 126 shipped.
static std::atomic<int> scanlineBloom{scanlines::kBloomStandard};

// SHOW-THROUGH (light), CORNER DEFOCUS (dark) and the POWER-OFF COLLAPSE
// (dark, at sleep) -- the 2026-08-23 roadmap items 1a, D3 and D8. All three
// default OFF here, so a build that never calls their setters draws exactly
// what this repo drew before they existed; the iOS shim pushes the first two
// as frozen constants and the third from its Settings row.
static std::atomic<int> showThroughStrength{showthrough::kStrengthOff};
static std::atomic<int> cornerDefocusStrength{cornerdefocus::kStrengthOff};
static std::atomic<bool> powerOffCollapse{false};

void setPresentFlash(bool wanted) {
  if (const char *env = std::getenv("CROSSPOINT_SIM_PRESENT_FLASH"))
    wanted = env[0] == '1';
  if (presentFlashFlag.exchange(wanted) == wanted) return;
  // Repaint rather than wait: the next page turn might be minutes away on an
  // e-ink firmware, and the owner just changed how one looks.
  requestDirtyPresent();
}

void setPhosphorGrain(int strengthPercent, int coverage, int mottleCells,
                      int mottleDepthHundredths) {
  strengthPercent = envPercentOr("CROSSPOINT_SIM_GRAIN", strengthPercent);
  // These three take kAcceptAnyValue, unlike the strength above them: they have
  // always passed a negative env value straight to the pure model's clamp. See
  // envPercentOr.
  coverage =
      envPercentOr("CROSSPOINT_SIM_GRAIN_COVERAGE", coverage, kAcceptAnyValue);
  mottleCells = envPercentOr("CROSSPOINT_SIM_GRAIN_MOTTLE_CELLS", mottleCells,
                             kAcceptAnyValue);
  // Hundredths here too, so the env path and the Settings path carry the same
  // units and a headless run reproduces exactly what the phone shows.
  mottleDepthHundredths =
      envPercentOr("CROSSPOINT_SIM_GRAIN_MOTTLE_DEPTH", mottleDepthHundredths,
                   kAcceptAnyValue);
  const int s = phosphorgrain::clampStrength(strengthPercent);
  const int c = static_cast<int>(phosphorgrain::clampCoverage(coverage));
  const int mc = phosphorgrain::clampMottleCells(mottleCells);
  const int md = static_cast<int>(
      phosphorgrain::clampMottleDepth(
          static_cast<float>(mottleDepthHundredths) / 100.0f) * 100.0f + 0.5f);
  // BOTH exchanges, unconditionally. Written as `a.exchange(s) != s ||
  // b.exchange(c) != c` this short-circuits: a changed strength makes the left
  // side true and the coverage is NEVER STORED. That shipped for exactly one
  // measurement -- all four coverage settings rendered byte-identical frames,
  // because the only call that ever changes coverage also changes strength.
  const bool strengthChanged = grainStrength.exchange(s) != s;
  const bool coverageChanged = grainCoverage.exchange(c) != c;
  const bool cellsChanged = grainMottleCells.exchange(mc) != mc;
  const bool depthChanged = grainMottleDepthPct.exchange(md) != md;
  if (!strengthChanged && !coverageChanged && !cellsChanged && !depthChanged)
    return;
  // Repaint rather than wait. The field is regenerated lazily by the present
  // path, but an e-ink firmware may not render for minutes, so without this the
  // new grain would first appear at some unrelated page turn.
  requestDirtyPresent();
}

void setLetterpress(int strengthPercent) {
  strengthPercent = envPercentOr("CROSSPOINT_SIM_LETTERPRESS", strengthPercent);
  const int s = letterpress::clampStrength(strengthPercent);
  if (letterpressStrength.exchange(s) == s) return;
  requestDirtyPresent();
}

void setPaperTooth(int percentOfReference) {
  percentOfReference =
      envPercentOr("CROSSPOINT_SIM_PAPER_TOOTH", percentOfReference);
  int pct = percentOfReference;
  if (pct < 0) pct = 0;
  if (pct > 400) pct = 400;
  if (paperToothPct.exchange(pct) == pct) return;
  requestDirtyPresent();
}

void setPaperFormation(int depthPercent) {
  depthPercent = envPercentOr("CROSSPOINT_SIM_PAPER_FORMATION", depthPercent);
  const int pct = static_cast<int>(
      letterpress::clampFormationDepth(static_cast<float>(depthPercent) /
                                       100.0f) * 100.0f + 0.5f);
  if (paperFormationPct.exchange(pct) == pct) return;
  requestDirtyPresent();
}

void setPaperDefects(int dialPercent) {
  dialPercent = envPercentOr("CROSSPOINT_SIM_PAPER_DEFECTS", dialPercent);
  const int pct = paperdefects::clampDial(dialPercent);
  if (paperDefectsPct.exchange(pct) == pct) return;
  requestDirtyPresent();
}

void setPaperDrift(int dialPercent) {
  dialPercent = envPercentOr("CROSSPOINT_SIM_PAPER_DRIFT", dialPercent);
  const int pct = lightink::clampPaperDriftPct(dialPercent);
  if (paperDriftPct.exchange(pct) == pct) return;
  // The panel's own tones change, so the cached frame has to be reconverted --
  // the palette path's mechanism, for the same reason: an e-ink firmware may
  // not render again for minutes and the page would otherwise keep the tone it
  // was converted in.
  pendingReconvert.store(true);
  requestDirtyPresent();
}

void setLaidLines(int strengthPercent) {
  strengthPercent = envPercentOr("CROSSPOINT_SIM_LAIDLINES", strengthPercent);
  const int pct = laidstructure::clampStrength(strengthPercent);
  if (laidLinesStrength.exchange(pct) == pct) return;
  requestDirtyPresent();
}

static int clampPartPercent(int pct) {
  const int cap =
      static_cast<int>(letterpress::kPartScaleMax * 100.0f + 0.5f);
  if (pct < 0) return 0;
  return pct > cap ? cap : pct;
}

void setPressRing(int percentOfStandard) {
  percentOfStandard =
      envPercentOr("CROSSPOINT_SIM_PRESS_RING", percentOfStandard);
  const int pct = clampPartPercent(percentOfStandard);
  if (pressRingPct.exchange(pct) == pct) return;
  requestDirtyPresent();
}

void setPressDeboss(int percentOfStandard) {
  percentOfStandard =
      envPercentOr("CROSSPOINT_SIM_PRESS_DEBOSS", percentOfStandard);
  const int pct = clampPartPercent(percentOfStandard);
  if (pressDebossPct.exchange(pct) == pct) return;
  requestDirtyPresent();
}

void setPressPressure(int percentOfStandard) {
  percentOfStandard =
      envPercentOr("CROSSPOINT_SIM_PRESS_PRESSURE", percentOfStandard);
  const int pct = clampPartPercent(percentOfStandard);
  if (pressPressurePct.exchange(pct) == pct) return;
  requestDirtyPresent();
}

void setScanlines(int intensityPercent) {
  intensityPercent = envPercentOr("CROSSPOINT_SIM_SCANLINES", intensityPercent);
  const int s = scanlines::clampIntensity(intensityPercent);
  if (scanlinesIntensity.exchange(s) == s) return;
  requestDirtyPresent();
}

void setScanlineSize(int percentOfRowPitch) {
  // THE ONE DIAL WITH A MINIMUM: 0 here would clamp to the finest pitch, which
  // is indistinguishable from the setting doing nothing, so a parsed 0 is read
  // as a typo and refused rather than believed.
  percentOfRowPitch =
      envPercentOr("CROSSPOINT_SIM_SCANLINE_PITCH", percentOfRowPitch,
                   /*minAccepted=*/1);
  const int s = scanlines::clampSize(percentOfRowPitch);
  if (scanlineSize.exchange(s) == s) return;
  requestDirtyPresent();
}

void setScanlineBloom(int percentOfStandard) {
  percentOfStandard =
      envPercentOr("CROSSPOINT_SIM_SCANLINE_BLOOM", percentOfStandard);
  const int s = scanlines::clampBloom(percentOfStandard);
  if (scanlineBloom.exchange(s) == s) return;
  requestDirtyPresent();
}

void setShowThrough(int percentOfStandard) {
  percentOfStandard =
      envPercentOr("CROSSPOINT_SIM_SHOW_THROUGH", percentOfStandard);
  const int s = showthrough::clampStrength(percentOfStandard);
  if (showThroughStrength.exchange(s) == s) return;
  requestDirtyPresent();
}

void setCornerDefocus(int percentOfStandard) {
  percentOfStandard =
      envPercentOr("CROSSPOINT_SIM_CORNER_DEFOCUS", percentOfStandard);
  const int s = cornerdefocus::clampStrength(percentOfStandard);
  if (cornerDefocusStrength.exchange(s) == s) return;
  requestDirtyPresent();
}

void setPowerOffCollapse(bool enabled) {
  if (const char *env = std::getenv("CROSSPOINT_SIM_POWEROFF_COLLAPSE"))
    enabled = env[0] == '1';
  // No present: nothing about a live page changes, and this one is read only
  // once the firmware has already gone to sleep.
  powerOffCollapse.store(enabled);
}

// --- THE DIAL TABLE'S APPLIERS ---------------------------------------------
//
// The one place a simdials::Id becomes a setter call. Everything above this
// line is the dial itself -- its atomic, its clamp, its env override, its
// present-or-reconvert contract -- and everything that used to hand-write a
// LIST of these calls (the boot seed, the settings watcher, the as-shipped
// block) now goes through here instead. See src/SimulatorDials.h.
//
// NO `default:` LABEL, on purpose. A row added to the table without a case
// here is then a -Wswitch warning at the next build, rather than a dial that
// compiles, ships, and quietly does nothing.
void applyDialGroup(simdials::Id group, const simdials::Values &v) {
  using namespace simdials;
  switch (group) {
    // SECONDS in the table, MILLISECONDS at the setter.
    case PageFadeSeconds:
      setPageFade(static_cast<float>(v[PageFadeSeconds]) * 1000.0f);
      break;
    case PageFadeDepthPercent:
      setPageFadeDepth(v[PageFadeDepthPercent]);
      break;
    case BeamPaintMs:
      setBeamPaint(static_cast<float>(v[BeamPaintMs]));
      break;
    case PresentFlash:
      setPresentFlash(v[PresentFlash] != 0);
      break;
    // THE MULTI-ARGUMENT ONE. Its four rows arrive as one call, which is why
    // they share a group: the setter stores all four or none, and splitting it
    // into four calls would repaint three times and (worse) let a caller push
    // half a grain setting.
    case GrainPercent:
      setPhosphorGrain(v[GrainPercent], v[GrainCoverage], v[GrainMottleCells],
                       v[GrainMottleDepth]);
      break;
    // The other three grain rows ride their leader above. Listed rather than
    // swept into a default, so the switch stays exhaustive.
    case GrainCoverage:
    case GrainMottleCells:
    case GrainMottleDepth:
      break;
    case LetterpressPercent:
      setLetterpress(v[LetterpressPercent]);
      break;
    case PaperToothPercent:
      setPaperTooth(v[PaperToothPercent]);
      break;
    case PaperFormationPercent:
      setPaperFormation(v[PaperFormationPercent]);
      break;
    case PaperDefectsPercent:
      setPaperDefects(v[PaperDefectsPercent]);
      break;
    // kReconverts: the setter also raises pendingReconvert, because this one
    // moves the page's own tones rather than compositing over them.
    case PaperDriftPercent:
      setPaperDrift(v[PaperDriftPercent]);
      break;
    case LaidLinesPercent:
      setLaidLines(v[LaidLinesPercent]);
      break;
    case PressRingPercent:
      setPressRing(v[PressRingPercent]);
      break;
    case PressDebossPercent:
      setPressDeboss(v[PressDebossPercent]);
      break;
    case PressPressurePercent:
      setPressPressure(v[PressPressurePercent]);
      break;
    case ScanlinesPercent:
      setScanlines(v[ScanlinesPercent]);
      break;
    case ScanlineSizePercent:
      setScanlineSize(v[ScanlineSizePercent]);
      break;
    case ScanlineBloomPercent:
      setScanlineBloom(v[ScanlineBloomPercent]);
      break;
    case ShowThroughPercent:
      setShowThrough(v[ShowThroughPercent]);
      break;
    case CornerDefocusPercent:
      setCornerDefocus(v[CornerDefocusPercent]);
      break;
    // kNoPresent: the setter deliberately asks for no repaint -- nothing about
    // a live page changes, and this is read only once the firmware is asleep.
    case PowerOffCollapseOn:
      setPowerOffCollapse(v[PowerOffCollapseOn] != 0);
      break;
  }
}

void applyDials(const simdials::Values &v) {
  for (int i = 0; i < simdials::kDialCount; i++) {
    const simdials::Id id = static_cast<simdials::Id>(i);
    if (simdials::isGroupLeader(id)) applyDialGroup(id, v);
  }
}

void setPanelEmissive(bool emissive) {
  if (const char *env = std::getenv("CROSSPOINT_SIM_PANEL_EMISSIVE"))
    emissive = env[0] == '1';
  if (panelEmissive.exchange(emissive) == emissive)
    return;
  // The ramp the page is drawn with just changed, and an e-ink firmware may not
  // render again for minutes -- so reconvert the cached frame rather than let
  // the new curve wait for the next page turn. Same contract as a palette or a
  // polarity change.
  pendingReconvert.store(true);
  requestDirtyPresent();
}

void setPanelGlowTail(const unsigned char tint[3], float onsetMs) {
  // The onset stores first and unconditionally: the env override below forces
  // the TINT only, and an onset of 0 is the old whole-trail ramp.
  glowTailOnsetMs.store(onsetMs > 0.0f ? onsetMs : 0.0f);
  // Same escape hatch as every other knob here: a desktop or headless run has
  // no Settings app, and without this the cascade's whole point -- that the
  // trail is a different color from the page -- could only be seen on a phone.
  if (const char *env = std::getenv("CROSSPOINT_SIM_PANEL_GLOW_TAIL")) {
    const int packed = panelpalette::parseHexRgb(env);
    if (packed >= 0) {
      glowTailTint.store(static_cast<uint32_t>(packed));
      return;
    }
  }
  glowTailTint.store(tint ? ((static_cast<uint32_t>(tint[0]) << 16) |
                             (static_cast<uint32_t>(tint[1]) << 8) |
                             static_cast<uint32_t>(tint[2]))
                          : kNoGlowTail);
}

void setPanelPalette(bool dark, const unsigned char ink[3],
                     const unsigned char paper[3]) {
  PanelPalette p{{ink[0], ink[1], ink[2]}, {paper[0], paper[1], paper[2]}};
  applyPanelPaletteEnv(dark, p);
  const uint64_t packed = packPalette(p);
  std::atomic<uint64_t> &slot = dark ? panelPackedDark : panelPackedLight;
  if (slot.exchange(packed) == packed)
    return;
  if (display.isInverted() != dark)
    return;  // the other polarity: nothing on screen changed
  setClearColor(p.paper[0], p.paper[1], p.paper[2]);
  pendingReconvert.store(true);
  // reconvertLastFrame() raises the present itself, but only once a frame has
  // been cached; the field color must repaint regardless, so ask here too.
  requestPresent();
}
} // namespace SimulatorOverlay

// The window, for the one caller outside this file: HalGPIO's
// pumpHostTextInput() has to hand SDL_StartTextInput a window, and on a phone
// that call is what raises the software keyboard. A free function rather than
// a HalDisplay method for the same reason SimulatorOverlay is free functions --
// the HAL's public surface must mirror the firmware's, and an e-ink board has
// no window handle to expose. Null before begin(); callers retry.
SDL_Window *simulatorWindow() { return window; }

HalDisplay::HalDisplay() {}
HalDisplay::~HalDisplay() {}

#if defined(SIMULATOR_DISPLAY_UC8179)
#define SIMULATOR_CONTROLLER_TITLE "UC8179"
#elif defined(SIMULATOR_DISPLAY_UC8279)
#define SIMULATOR_CONTROLLER_TITLE "UC8279"
#else
#define SIMULATOR_CONTROLLER_TITLE "SSD1677"
#endif

#if defined(SIMULATOR_DEVICE_STICKY)
static constexpr const char *WINDOW_TITLE =
    "Simulator - Seeed Sticky (SSD1677)";
#elif defined(SIMULATOR_DEVICE_X4_PRO)
static constexpr const char *WINDOW_TITLE =
    "Simulator - XTEINK X4 Pro (" SIMULATOR_CONTROLLER_TITLE ")";
#elif defined(SIMULATOR_DEVICE_X3)
#if defined(SIMULATOR_DISPLAY_UC8279)
static constexpr const char *WINDOW_TITLE = "Simulator - XTEINK X3 (UC8279d)";
#else
static constexpr const char *WINDOW_TITLE = "Simulator - XTEINK X3 (UC8253)";
#endif
#else
static constexpr const char *WINDOW_TITLE =
    "Simulator - XTEINK X4 (" SIMULATOR_CONTROLLER_TITLE ")";
#endif

#undef SIMULATOR_CONTROLLER_TITLE

// WHETHER THIS RENDERER'S ALPHA BLEND ROUNDS TO NEAREST OR TRUNCATES --
// measured, not assumed. trail::fadePeakBound's `roundBias` term exists
// SPECIFICALLY because SDL's software blitter (the desktop canary, all three
// packaged Mac apps) truncates while a GPU rasteriser rounds, and the wrong
// guess in either direction is a real bug: assume truncate on a rounding
// backend and the bound calls a trail dead while a Metal ghost is still on
// the glass; assume round on a truncating one and the bound overstates how
// long the trail can still move a pixel by ~16 of 255, every step (see
// src/TrailLifetime.h). Probed ONCE per process, immediately after the
// renderer exists: render a known value into a throwaway 1x1 target, apply
// exactly the fade's own operation (SDL_BLENDMODE_BLEND, a black fill at one
// alpha) at a `drop` chosen so truncate and round-to-nearest predict two
// DIFFERENT 8-bit results, and read the pixel back. Never per frame -- this
// is a one-shot answer about the backend, not a per-present measurement.
static float measureTrailFadeRoundBias(SDL_Renderer *renderer) {
  if (!renderer) return 0.5f;  // can't measure: keep the conservative guess
  SDL_Texture *probe = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888,
                                         SDL_TEXTUREACCESS_TARGET, 1, 1);
  if (!probe) return 0.5f;

  SDL_Texture *restore = SDL_GetRenderTarget(renderer);
  SDL_SetRenderTarget(renderer, probe);

  const int startValue = 200;
  const int drop = 128;  // truncate((255-128)/255 * 200) = 99; round() = 100
  SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE);
  SDL_SetRenderDrawColor(renderer, static_cast<Uint8>(startValue),
                         static_cast<Uint8>(startValue),
                         static_cast<Uint8>(startValue), 255);
  SDL_RenderFillRect(renderer, nullptr);

  // THE EXACT OPERATION the real fade performs -- see the accumulator's own
  // fade beside its trail::fadePeakBound call, further down this file.
  SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND);
  SDL_SetRenderDrawColor(renderer, 0, 0, 0, static_cast<Uint8>(drop));
  SDL_RenderFillRect(renderer, nullptr);

  SDL_Surface *shot = SDL_RenderReadPixels(renderer, nullptr);
  SDL_SetRenderTarget(renderer, restore);
  SDL_DestroyTexture(probe);

  float bias = 0.5f;
  if (shot) {
    SDL_Surface *conv = SDL_ConvertSurface(shot, SDL_PIXELFORMAT_ARGB8888);
    SDL_DestroySurface(shot);
    if (conv && conv->w >= 1 && conv->h >= 1) {
      const uint32_t px = *reinterpret_cast<const uint32_t *>(conv->pixels);
      const int measured = static_cast<int>((px >> 16) & 0xFFu);  // R
      const int truncated = static_cast<int>(static_cast<float>(startValue) *
                                             static_cast<float>(255 - drop) /
                                             255.0f);
      bias = (measured > truncated) ? 0.5f : 0.0f;
      SDL_Log("[trail] fade rounding measured: %s (start=%d drop=%d -> "
              "measured %d, truncate predicts %d)",
              bias > 0.0f ? "ROUNDS to nearest" : "TRUNCATES", startValue,
              drop, measured, truncated);
    }
    if (conv) SDL_DestroySurface(conv);
  }
  return bias;
}

// The measured answer, read by every trail::fadePeakBound call site in this
// file. Defaults to the old conservative 0.5f (assume rounding) so a build
// that somehow reaches a fade before begin() has run is unchanged.
static float trailFadeRoundBias = 0.5f;

void HalDisplay::begin() {
  // THE WARM-UP'S ARMING, and it is ABOVE the idempotent return below on
  // purpose: iOS wakes by re-entering setup() with the window already built, so
  // everything past that return is skipped on exactly the boot this feature
  // exists for. KEEP THIS CALL ABOVE THAT RETURN. The consume-once of
  // CROSSPOINT_SIM_TUBE_OFF is inside it, in src/SurfacePower.cpp.
  simpower::armPowerOnWarmUp();

  // Idempotent, because setup() can run more than once in one process.
  //
  // A deep-sleep wake is a chip reset on hardware and a process relaunch on
  // desktop, so begin() would normally see a clean machine. Where the simulator
  // instead re-enters setup() in-process (iOS, which cannot exec -- see
  // SimulatorLifecycle.h), a second call would create a SECOND window and
  // renderer, leaving the visible one orphaned and the panel frozen. Reuse what
  // already exists; presentIfNeeded() re-applies the window geometry every
  // present, so orientation still self-corrects after a wake.
  if (window && sdl_renderer && texture) {
    return;
  }

  // Boot geometry, once. This line exists because the render scale was twice
  // believed shipped while the framebuffer silently stayed 1x (a define that
  // never reached this TU); the compiled truth must be observable at runtime.
  LOG_INF("DISP", "Framebuffer %dx%d, render scale %d (ceiling %d)",
          activeWidth(), activeHeight(), cp::renderScale(),
          static_cast<int>(RENDER_SCALE));

  // SDL3 returns true on success where SDL2 returned 0.
  if (!SDL_Init(SDL_INIT_VIDEO)) {
    std::cerr << "SDL could not initialize! SDL_Error: " << SDL_GetError()
              << std::endl;
    return;
  }

  int winW = 0;
  int winH = 0;
  extern GfxRenderer renderer;
  getLogicalWindowSize(renderer.getOrientation(), &winW, &winH);

  // SDL_WINDOW_HIGH_PIXEL_DENSITY lets the renderer use full Retina/HiDPI pixels
  // on macOS so we get crisp 1:1 rendering instead of a blurry upscale.
  // SDL3 drops the x/y arguments and shows windows by default.
  window = SDL_CreateWindow(WINDOW_TITLE, winW, winH,
                            SDL_WINDOW_HIGH_PIXEL_DENSITY);
  sdl_renderer = SDL_CreateRenderer(window, nullptr);

  // Which backend actually won. A nullptr driver name takes the first entry of
  // SDL_render.c's render_drivers[], and the build turns SDL_GPU off on the
  // strength of Metal outranking it there -- so print the answer rather than
  // leave the next reader to re-derive it from SDL's source.
  if (sdl_renderer) {
    const char* rendererName = SDL_GetRendererName(sdl_renderer);
    SDL_Log("[panel] renderer: %s", rendererName ? rendererName : "(unknown)");
    trailFadeRoundBias = measureTrailFadeRoundBias(sdl_renderer);
  }

  // Rendering logic runs in FRAMEBUFFER coordinates (see
  // getLogicalPresentationSize); SDL maps that space into the window's
  // drawable pixels, whatever size the window chose above.
  int logW = 0;
  int logH = 0;
  getLogicalPresentationSize(renderer.getOrientation(), &logW, &logH);
  SDL_SetRenderLogicalPresentation(sdl_renderer, logW, logH,
                                   kLogicalPresentation);
  currentWindowWidth = winW;
  currentWindowHeight = winH;

  texture = SDL_CreateTexture(sdl_renderer, SDL_PIXELFORMAT_ARGB8888,
                              SDL_TEXTUREACCESS_STREAMING, activeWidth(),
                              activeHeight());

  // SDL3 replaced the global SDL_HINT_RENDER_SCALE_QUALITY hint with a
  // per-texture setting, which must therefore come after the texture exists.
  // See kPanelScaleMode above for why the choice is not unconditional.
  SDL_SetTextureScaleMode(texture, kPanelScaleMode);

  // Seed both polarities with the shipped tones, THROUGH the setter, so that
  // the CROSSPOINT_SIM_PANEL_* env override is applied on a build that never
  // publishes a palette of its own -- which is every desktop build, there being
  // no Settings.app on a Mac. With the vars unset this is exactly the pair the
  // atomics already hold, so it is a no-op and the desktop stays byte-identical.
  // The iOS harness publishes the owner's choice over the top a moment later.
  SimulatorOverlay::setPanelPalette(false, panelpalette::kDefaultLight.ink,
                                    panelpalette::kDefaultLight.paper);
  SimulatorOverlay::setPanelPalette(true, panelpalette::kDefaultDark.ink,
                                    panelpalette::kDefaultDark.paper);

  // Seed the glow through ITS setter for exactly the same reason, and it is not
  // a theoretical one: the first version of this omitted the call, so
  // CROSSPOINT_SIM_PANEL_GLOW_MS was read by a function no desktop build ever
  // called and the effect could not be turned on off-phone at all. 0 is off, so
  // with the var unset this is a no-op.
  SimulatorOverlay::setPanelGlow(0.0f);
  // And the cascade tail, which had the identical hole: nullptr is "the trail
  // keeps the tone it was drawn in", so with the var unset this is a no-op.
  SimulatorOverlay::setPanelGlowTail(nullptr);
  // And the emission flag, for the third time. Anything whose only caller is a
  // phone needs its env override seeded here or it is dead on the desktop.
  SimulatorOverlay::setPanelEmissive(false);
  // ...AND EVERY SURFACE DIAL, from the table.
  //
  // This used to be nineteen hand-written calls, numbered in their comments up
  // to "fifteenth" because each one was added for the same reason and the
  // reason had to be restated every time. The reason is: a dial whose only
  // caller is a phone must still be pushed through its setter here, or its
  // CROSSPOINT_SIM_* override is read by a function no desktop build ever
  // calls and the dial cannot be exercised off-phone at all. That has been a
  // real bug twice -- the glow and the fade both shipped that way, which is how
  // the first fade measurement showed no fade.
  //
  // Every value is simdials::kDials[].desktopDefault, and every one of those is
  // what this repo already drew, so with no env var set this whole call is a
  // no-op and the desktop canary stays byte-identical. Five dials that were
  // NEVER seeded here get their env override on the desktop for the first time
  // (tooth, formation, defects, laid wires and the three press ratios); they
  // reached the atomics only through the settings file before, about a second
  // after boot.
  SimulatorOverlay::applyDials(simdials::desktopDefaults());

  // Default appearance is light, so a desktop build stays byte-identical to
  // what it always rendered; CROSSPOINT_SIM_DARK is applied inside
  // setPanelDark, which is what lets a headless run force either polarity. A
  // host with a real appearance to follow (the iOS harness) calls
  // setPanelDark again with it once the harness installs.
  SimulatorOverlay::setPanelDark(false);

  // CROSSPOINT_SIM_AS_SHIPPED=1 seeds the dials the iOS app actually ships
  // with, in one switch, instead of a dozen env vars reconstructed by hand.
  //
  // This exists because the divergence has cost real time. The desktop seeds
  // every dial at its historical value -- deliberately, so the canary and every
  // headless capture stay byte-identical to what this repo always drew -- while
  // the app ships CRT White with letterpress and scanlines on, a heavily
  // textured sheet, and a 55 ms beam. Reproducing an owner report therefore
  // means rebuilding his settings from memory, and on 2026-08-19 that went
  // wrong twice in one bug hunt.
  //
  // THE DIAL VALUES NO LONGER LIVE HERE. They are simdials::kDials[].
  // shippedValue, checked against the app's own frozen constants by
  // tests/dial_table_test.cpp -- because writing them out here by hand is
  // exactly what drifted twice on 2026-08-23 (the beam at 67 against the app's
  // 55, and three of the grain's four arguments at 100/8/30 against 160/5/90).
  //
  // THE PAGE IS NOT HAND-WRITTEN EITHER, since 2026-08-24. It used to be, on
  // the argument that the palette, the emission flag, the glow and the polarity
  // are one coherent choice rather than 23 independent numbers -- true, and
  // beside the point: a hand-written coherent choice drifts exactly like a
  // hand-written number. It did, the same day it was frozen. The app moved to
  // Sanguine on India and the owner's four-gun mix while this block still said
  // CRT White, so `AS_SHIPPED` -- the documented way to reproduce an owner
  // report -- painted a page that ships nowhere: India's tooth, formation and
  // show-through over a paper tone that is not India's, and a dark page off by
  // a nearly 4x trail. Found by adversarial review, not by any test, because
  // this half was deliberately outside the dial table's reach.
  //
  // It now reads src/FrozenPage.h, which is the SAME definition the iOS app
  // renders from -- that file moved out of ios/ for this, since it is pure C++
  // and its four dependencies were already here. One definition, so the two
  // cannot disagree again.
  //
  // It does NOT change any default, and it runs LAST on purpose: the first
  // version sat above the ordinary seeds and they overwrote it, so the log said
  // as-shipped while the grain was still at the desktop's Even/0.10.
  const bool asShipped = [] {
    const char *e = std::getenv("CROSSPOINT_SIM_AS_SHIPPED");
    return e && e[0] == '1';
  }();
  if (asShipped) {
    LOG_INF("DISP", "as-shipped: seeding the iOS app's own defaults");
    // BOTH polarities, because both are frozen now. The light pair was never
    // seeded at all, so an as-shipped LIGHT run kept the repo's historical
    // 2D2D2D-on-FBFBF9 while the app rendered Sanguine on India.
    const panelpalette::Palette shippedDark = frozenpage::darkPair();
    const panelpalette::Palette shippedLight = frozenpage::lightPair();
    SimulatorOverlay::setPanelPalette(true, shippedDark.ink, shippedDark.paper);
    SimulatorOverlay::setPanelPalette(false, shippedLight.ink, shippedLight.paper);
    SimulatorOverlay::setPanelEmissive(true);
    // The mix's decay, not a preset's: the app's dark page is a four-gun blend
    // in the Custom slot, so glowPresetForPrefs answers kPresetCustom and the
    // mixer owns the trail. Seeding a preset's trail here is what left the
    // desktop 283 ms against the app's 1095.
    const phosphormix::Result &shippedMix = frozenpage::darkMix();
    SimulatorOverlay::setPanelGlow(shippedMix.trailMs);
    if (shippedMix.hasTail)
      SimulatorOverlay::setPanelGlowTail(shippedMix.tail, shippedMix.tailOnsetMs);
    SimulatorOverlay::applyDials(simdials::shippedValues());
    // LAST, and after the dials: the grain's shipped strength is the DARK one
    // (the app stores a strength per appearance and the desktop carries a
    // single atomic), so the polarity this selects is the one those numbers
    // describe.
    SimulatorOverlay::setPanelDark(true);
  }

}

void HalDisplay::begin(bool /*seamless*/) { begin(); }

void HalDisplay::clearScreen(uint8_t color) const {
  // getFrameBuffer() returns null while the buffer is lent out. Skipping the
  // clear is right: whoever holds the loan owns the pixels, and the next draw
  // after they hand it back repaints anyway.
  uint8_t *fb = getFrameBuffer();
  if (!fb) return;
  memset(fb, color, activeBufferSize());
}

void HalDisplay::drawImage(const uint8_t *imageData, uint16_t x, uint16_t y,
                           uint16_t w, uint16_t h, bool) const {
  uint8_t *fb = getFrameBuffer();
  if (!fb) return;  // buffer lent out; see clearScreen
  const uint16_t imageWidthBytes = w / 8;
  for (uint16_t row = 0; row < h; row++) {
    const uint16_t destY = y + row;
    if (destY >= activeHeight())
      break;
    const uint32_t destOffset =
        static_cast<uint32_t>(destY) * activeWidthBytes() + (x / 8);
    const uint32_t srcOffset = static_cast<uint32_t>(row) * imageWidthBytes;
    for (uint16_t col = 0; col < imageWidthBytes; col++) {
      if ((x / 8 + col) >= activeWidthBytes())
        break;
      fb[destOffset + col] = imageData[srcOffset + col];
    }
  }
}

void HalDisplay::drawImageTransparent(const uint8_t *imageData, uint16_t x,
                                      uint16_t y, uint16_t w, uint16_t h,
                                      bool) const {
  uint8_t *fb = getFrameBuffer();
  if (!fb) return;  // buffer lent out; see clearScreen
  const uint16_t imageWidthBytes = w / 8;
  for (uint16_t row = 0; row < h; row++) {
    const uint16_t destY = y + row;
    if (destY >= activeHeight())
      break;
    const uint32_t destOffset =
        static_cast<uint32_t>(destY) * activeWidthBytes() + (x / 8);
    const uint32_t srcOffset = static_cast<uint32_t>(row) * imageWidthBytes;
    for (uint16_t col = 0; col < imageWidthBytes; col++) {
      if ((x / 8 + col) >= activeWidthBytes())
        break;
      fb[destOffset + col] &= imageData[srcOffset + col];
    }
  }
}

void HalDisplay::setInverted(bool value) {
  if (inverted.exchange(value) == value)
    return;
  // Inversion is applied at conversion time, so already-presented pixels keep
  // the old polarity until reconverted. Ask the main thread to redo the
  // conversion from the cached frame so the change is visible immediately.
  pendingReconvert.store(true);
}

bool HalDisplay::toggleInverted() {
  const bool value = !inverted.load();
  setInverted(value);
  return value;
}

bool HalDisplay::isInverted() const { return inverted.load(); }

void HalDisplay::displayBuffer(RefreshMode mode, bool turnOffScreen) {
  refreshDisplay(mode, turnOffScreen);
  if (std::this_thread::get_id() == simulatorMainThread) {
    presentIfNeeded();
  }
}

void HalDisplay::displayBufferAsync(RefreshMode mode) {
  // SDL presentation is already handed off to the main thread. The framebuffer
  // conversion itself remains synchronous, so advertise no genuine overlap.
  refreshDisplay(mode, false);
}

void HalDisplay::waitRefreshComplete() {}

// S-001: the device supports the overlapped page turn and this said it did not,
// so EpubReaderActivity.cpp:1593's `overlapRefresh` branch has never executed in
// a simulator run. Opt-in rather than flipped outright, because the presentation
// here genuinely is synchronous -- displayBufferAsync() above converts on the
// calling thread -- so this advertises a CAPABILITY the firmware can then
// exercise, not an overlap this HAL actually performs. What it buys is that the
// branch runs at all; what it cannot show is a timing win that does not exist
// off-device.
//
// The `!inverted` term mirrors the device rather than being invented here:
// FreeInkDisplay::supportsAsyncRefresh() (freeink-sdk .../FreeInkDisplay.cpp:557)
// is `!_inverted && !_inversionDirty && _driver->supportsAsyncDisplay()`, and
// the X3's drivers (Uc8253X3, Ssd1677) both answer true -- so on hardware the
// capability comes and goes with dark mode. Without this term a test would see
// the overlapped path stay available through an inversion flip, which is the
// one thing the device is guaranteed not to do.
bool HalDisplay::supportsAsyncRefresh() const {
  return simtruth::asyncRefreshEnabled() && !inverted.load();
}

void HalDisplay::displayWindow(int, int, int, int) {
  refreshDisplay(RefreshMode::FAST_REFRESH, false);
}

// Called from the render task (background thread): convert framebuffer to
// pixels and flag for present.
void HalDisplay::refreshDisplay(RefreshMode /*mode*/, bool /*turnOffScreen*/) {
  if (powerLogFirstRefresh) {
    powerLogFirstRefresh = false;
    if (powerLogWanted())
      SDL_Log("[power] first refreshDisplay after reboot");
  }
  const uint8_t *fb = getFrameBuffer();
  // Lent out: there is nothing coherent to convert, and presenting a half-owned
  // buffer would show a torn frame. The lender's own refresh follows.
  if (!fb) return;
  snapshotBwBase(fb);
  renderBwPixels(fb);
}

// Called from the main thread (simulator_main.cpp) to push pixels to SDL.
namespace {
// Main thread writes it on the SDL background events; presentIfNeeded reads it
// on the same thread. Atomic anyway, because the render task's requestPresent
// path runs concurrently.
std::atomic<bool> g_backgrounded{false};
}  // namespace

void HalDisplay::setBackgrounded(const bool backgrounded) {
  const bool was = g_backgrounded.exchange(backgrounded);
  if (was == backgrounded)
    return;
  SDL_Log("[DISPLAY] %s -- GPU presents %s", backgrounded ? "backgrounded" : "foregrounded",
          backgrounded ? "suspended" : "resumed");
  if (!backgrounded) {
    // Whatever the firmware drew while we were away is still owed.
    SimulatorOverlay::requestPresent();
  }
}

// The ghost is created lazily and matches the panel texture's format and size.
// Lazy because the glow is off by default and every desktop build would
// otherwise carry a second full-panel texture for nothing.
// THE PERSISTENCE BUFFER, and why one previous frame was never enough.
//
// Reported: "if I flip through pages rapidly, the persistence buffer is not
// affected by all pages, just the most recent pages." Correct, and it was a
// limitation of the model rather than a bug in it: the first glow kept ONE
// previous frame and one start time, so each new page threw the last one away.
// Flip four pages quickly and only the fourth-from-last ever glowed.
//
// A phosphor does not work that way. Every frame the beam writes deposits
// energy, each deposit decays on its own from the moment it lands, and what you
// see is the SUM. So the ghost is now an accumulator that lives on the GPU:
// each present multiplies it down by the decay for the elapsed time, and each
// new page ADDS the frame it replaced. Ten pages in a second leave ten
// contributions in it, each already faded by its own age -- which falls out of
// the arithmetic for free, because a uniform multiply applied over time is
// exactly what per-contribution exponential decay is.
//
// IT IS SIZED TO THE OUTPUT, NOT TO THE PANEL (2026-08-26, owner: "apply
// persistence and other crt effects equally to paper and panel"). It held the
// panel framebuffer until then, so the afterglow stopped dead at the page's
// edge and the surround and the button pad -- two thirds of a phone's glass --
// never glowed at all. That is the arrangement the grain ruling already
// rejected for texture on 2026-08-18: it is ONE SHEET OF GLASS, and a tube's
// whole face is phosphor.
//
// Being output-space is also what makes the trail stay WHERE THE LIGHT WAS
// EMITTED. The panel rect moves -- zen mode places the page within the sheet,
// a keyboard coming up relayouts it -- and a panel-space accumulator was drawn
// through the CURRENT rect, so the ghost of the old page teleported to the new
// position with it. In output space the deposit keeps the coordinates it was
// laid down at, which is the only thing a phosphor can do.
static SDL_Texture *accumTexture = nullptr;
static int accumW = 0, accumH = 0;
static uint64_t accumLastFadeMs = 0;
static uint64_t accumLastAddMs = 0;
// An UPPER BOUND on the accumulator's brightest channel, carried on the CPU so
// the trail can be stopped the moment it cannot change a pixel without reading
// the texture back. Set to full scale by every deposit, stepped by every fade
// with the same alpha the fade used. See src/TrailLifetime.h.
static float accumPeakBound = 0.0f;
// It is only meaningful beside the texture it tracks, and an iOS reboot is a
// longjmp that keeps the static and destroys nothing. Registered here rather
// than in the display's own reset above because that block runs before this
// declaration.
const simreset::Registrar gAccumPeakReset{[] { accumPeakBound = 0.0f; }};

static void destroyGlassTextures();
// THE GLASS CAPTURE AND THE SEQ IT BELONGS TO, for the same reason. The desktop
// reboot is execvp and re-initialises every static for free; iOS longjmps back
// into setup() in the SAME process, so a texture pointer and a sequence number
// from the previous boot would both survive it -- and the sequence would then
// make the first new picture look like one already captured. The textures are
// dropped rather than kept because the renderer they belong to may not.
const simreset::Registrar gGlassCaptureReset{[] {
  destroyGlassTextures();
  presentedSeq = 0;
}};

// The accumulator value at or below which the composite is a no-op, for the
// palette and the phosphor that are live RIGHT NOW.
//
// The mod CEILING is per channel against the cascade tail, because the draw
// ramps the mod between the ink and the tail over the trail and either end may
// be the brighter one in a given channel -- a green ink handing over to an
// orange tail is brighter in red at the end and in green at the start.
//
// The destination FLOOR is the panel's own per-channel minimum, since every
// tone it can show is a LERP between the ink and the paper. The page fade is
// the one thing that can put something else under the trail: it blends the
// panel toward the cleared field, so while it is live the field's tones join
// the minimum. Off (the shipped state, and the desktop default) that term is
// not consulted at all.
static float trailInvisibleAtOrBelow() {
  const PanelPalette live = livePanelPalette(display.isInverted());
  uint8_t modCeiling[3];
  uint8_t dstFloor[3];
  const uint32_t tail = glowTailTint.load();
  const bool fading = pageFadeMs.load() > 0.0f;
  const uint32_t fieldColor = SimulatorOverlay::clearColor.load();
  for (int c = 0; c < 3; c++) {
    const uint8_t ink = live.ink[c];
    const uint8_t paper = live.paper[c];
    modCeiling[c] = ink;
    if (tail != kNoGlowTail) {
      const uint8_t t = static_cast<uint8_t>((tail >> (16 - 8 * c)) & 0xFF);
      if (t > modCeiling[c]) modCeiling[c] = t;
    }
    uint8_t floorC = ink < paper ? ink : paper;
    if (fading) {
      const uint8_t f = static_cast<uint8_t>((fieldColor >> (16 - 8 * c)) & 0xFF);
      if (f < floorC) floorC = f;
    }
    dstFloor[c] = floorC;
  }
  return trail::invisibleAtOrBelow(modCeiling, dstFloor);
}

// The [power] boundary station. Runs immediately before the in-process reboot's
// longjmp (desktop execvp resets everything for free and never gets here). It
// only REPORTS: deepSleep() below settles the beam and the glow on the way
// down, so anything nonzero here is state that would have crossed into the next
// boot and is worth a line in the log. The one-shot latches arm the
// first-refresh / first-present stations for the boot that follows.
const simreset::Registrar gPowerLogBoundary{[] {
  powerLogFirstRefresh = true;
  powerLogFirstPresent = true;
  powerLogSleepVetoSaid = false;
  // The boot on the other side of the jump is awake, whatever it renders.
  displaySleeping.store(false);
  if (!powerLogWanted()) return;
  SDL_Log("[power] reboot boundary: beamStartedAt=%llu glassSeq=%llu "
          "accumLastAddMs=%llu pendingPresent=%d holdUntil=%llu flashUntil=%llu",
          (unsigned long long)beamStartedAt, (unsigned long long)glassSeq,
          (unsigned long long)accumLastAddMs, (int)pendingPresent.load(),
          (unsigned long long)presentHoldUntil.load(),
          (unsigned long long)presentFlashUntil.load());
}};

static void ensureAccumTexture(int outW, int outH) {
  if (accumTexture && accumW == outW && accumH == outH) return;
  if (accumTexture) {
    // The glass changed shape (a rotation, a window resize). There is no honest
    // way to carry emitted light across that, so the buffer is dropped and the
    // bound with it -- keeping a stale bound would hold the present loop open
    // for a trail that no longer exists.
    SDL_DestroyTexture(accumTexture);
    accumTexture = nullptr;
    accumW = accumH = 0;
    accumPeakBound = 0.0f;
  }
  if (outW <= 0 || outH <= 0 || !sdl_renderer) return;
  accumTexture = SDL_CreateTexture(sdl_renderer, SDL_PIXELFORMAT_ARGB8888,
                                   SDL_TEXTUREACCESS_TARGET, outW, outH);
  if (!accumTexture) {
    LOG_ERR("DISP", "glow: no accumulator texture (%s)", SDL_GetError());
    return;
  }
  accumW = outW;
  accumH = outH;
  // Additive on the way to the screen: the accumulator holds EMITTED LIGHT, and
  // light adds. Cleared once here so the first page does not inherit garbage.
  SDL_SetTextureBlendMode(accumTexture, SDL_BLENDMODE_ADD);
  SDL_Texture *prev = SDL_GetRenderTarget(sdl_renderer);
  SDL_SetRenderTarget(sdl_renderer, accumTexture);
  SDL_SetRenderDrawColor(sdl_renderer, 0, 0, 0, 255);
  SDL_RenderClear(sdl_renderer);
  SDL_SetRenderTarget(sdl_renderer, prev);
  accumLastFadeMs = SDL_GetTicks();
}

// CAPTURE THE GLASS -- one readback per new picture, and the three rules that
// make it safe.
//
// WHAT: the composed frame at OUTPUT resolution, read back immediately after
// the button pad is painted and BEFORE the accumulator is drawn over it. That
// exclusion is not an optimisation, it is the whole thing: a capture taken
// after the trail would deposit the trail back into itself next time, and a
// buffer that re-deposits its own contents at full strength never decays.
//
// WHEN: once per pixelBufSeq, and NOT WHILE THE BEAM IS SWEEPING. During a
// sweep the glass is old below the beam line and new above it, so a capture
// taken on the content-change present itself would record most of the OLD page
// and hand it back as "the picture that was on screen" -- the previous frame,
// twice, and the one before it lost. Waiting for the first present after the
// sweep completes costs nothing (the trail is driving presents anyway) and the
// picture it records is the finished one.
//
// WHY A READBACK AT ALL, when the panel's own pixels are already in RAM: the
// pad and the surround have no framebuffer. They are painted by the overlay
// hook straight onto the output, and the composed glass is the only place they
// exist as pixels. See docs/crt-beam-and-flash.md for the alternative that was
// priced and rejected -- re-rendering the composition into the accumulator,
// which cannot reach the pad because the overlay draws colour, not intensity.
//
// COST: one full-output readback, one CPU pass over it and two uploads, per
// NEW PICTURE -- never per present, so a trail pays it once and then touches no
// pixel data at all. Measured on the desktop canary at 2x, 528x792 output:
// 2.6 ms of the 60-odd ms a dark page turn already spends. It replaced a
// framebuffer-sized copy, intensity pass and two framebuffer-sized uploads
// (1584x1056, four times the pixels), so on the canary it is cheaper than what
// it removed.
static bool ensureGlassTextures(int outW, int outH) {
  if (glassPrevTexture && glassW == outW && glassH == outH) return true;
  if (glassPrevTexture) SDL_DestroyTexture(glassPrevTexture);
  if (glassIntensityTexture) SDL_DestroyTexture(glassIntensityTexture);
  glassPrevTexture = glassIntensityTexture = nullptr;
  glassW = glassH = 0;
  glassHasPicture = false;
  if (outW <= 0 || outH <= 0 || !sdl_renderer) return false;
  glassPrevTexture =
      SDL_CreateTexture(sdl_renderer, SDL_PIXELFORMAT_ARGB8888,
                        SDL_TEXTUREACCESS_STREAMING, outW, outH);
  glassIntensityTexture =
      SDL_CreateTexture(sdl_renderer, SDL_PIXELFORMAT_ARGB8888,
                        SDL_TEXTUREACCESS_STREAMING, outW, outH);
  if (!glassPrevTexture || !glassIntensityTexture) {
    LOG_ERR("DISP", "glass: could not create the capture textures (%s)",
            SDL_GetError());
    if (glassPrevTexture) SDL_DestroyTexture(glassPrevTexture);
    if (glassIntensityTexture) SDL_DestroyTexture(glassIntensityTexture);
    glassPrevTexture = glassIntensityTexture = nullptr;
    return false;
  }
  // The beam's copy is the picture itself and is drawn opaque; the deposit's is
  // light and is composed MAXIMUM, which ignores both blend factors.
  SDL_SetTextureBlendMode(glassPrevTexture, SDL_BLENDMODE_NONE);
  SDL_SetTextureScaleMode(glassPrevTexture, SDL_SCALEMODE_NEAREST);
  SDL_SetTextureScaleMode(glassIntensityTexture, SDL_SCALEMODE_NEAREST);
  glassW = outW;
  glassH = outH;
  return true;
}

static void destroyGlassTextures() {
  if (glassPrevTexture) SDL_DestroyTexture(glassPrevTexture);
  if (glassIntensityTexture) SDL_DestroyTexture(glassIntensityTexture);
  glassPrevTexture = glassIntensityTexture = nullptr;
  glassW = glassH = 0;
  glassSeq = 0;
  glassGen = 0;
  glassHasPicture = false;
}

// Read the output back and fill both copies. Assumes logical presentation is
// already DISABLED by the caller, so the readback is the real output rect.
static bool captureGlass(int outW, int outH) {
  if (!ensureGlassTextures(outW, outH)) return false;
  SDL_Surface *shot = SDL_RenderReadPixels(sdl_renderer, nullptr);
  SDL_Surface *conv =
      shot ? SDL_ConvertSurface(shot, SDL_PIXELFORMAT_ARGB8888) : nullptr;
  if (shot) SDL_DestroySurface(shot);
  if (!conv) return false;
  if (conv->w != outW || conv->h != outH) {
    SDL_DestroySurface(conv);
    return false;
  }
  SDL_UpdateTexture(glassPrevTexture, nullptr, conv->pixels, conv->pitch);
  // max(r,g,b), white on black. The deposit has to be INTENSITY so that the
  // composite's colour mod can paint the trail any colour it likes -- see the
  // glassIntensityTexture comment where it is declared.
  static std::vector<uint32_t> intensityBuf;
  intensityBuf.resize(static_cast<size_t>(outW) * outH);
  // THE DEPOSIT IS THE EXCITATION, NOT THE ABSOLUTE LEVEL (owner ruling
  // 2026-08-27, adopting the fix measured on 2026-08-26).
  //
  // Unexcited phosphor emits nothing, so the PAPER tone is the tube's dark
  // state and not light. Depositing it as light made a paper pixel come back
  // as max(paper) * ink[c]/255, which is <= paper[c] only where the paper
  // happens to lie on the ink's hue ray. On 42 of the 52 presets it does not,
  // and the trail LIFTED the whole ground -- measured on Metal, +29 R / +27 G
  // worst (Cascade), over the entire face. Rescaling into the paper..ink span
  // makes a paper pixel deposit 0, so the ground is left exactly where it was.
  //
  // THE SCALE FACTOR IS inkMax, NOT 255, AND THAT IS THE COMPENSATION.
  // Excitation scaled to 255 would make an ink pixel deposit 255 where it
  // deposits inkMax today -- 1.203x for the shipped pair (212 -> 255), which
  // is the "0.83x compensation" the ruling was held on. Scaling to inkMax
  // instead applies that compensation EXACTLY and per preset, rather than as
  // one constant fitted to one pair: an ink pixel deposits what it always
  // deposited, for every preset, while a paper pixel stops lifting the ground.
  // The brightest ghost pixel is therefore unchanged everywhere -- including
  // on the ten presets whose ink peaks below 255, which a fixed 0.83 would
  // have DARKENED.
  //
  // span <= 0 is the LIGHT polarity, where the ink is darker than the paper.
  // No trail is composited on a pale ground at all, so the old absolute
  // intensity is kept there rather than inventing a meaning for it.
  const PanelPalette gpal = livePanelPalette(display.isInverted());
  int paperMax = 0, inkMax = 0;
  for (int c = 0; c < 3; c++) {
    if (gpal.paper[c] > paperMax) paperMax = gpal.paper[c];
    if (gpal.ink[c] > inkMax) inkMax = gpal.ink[c];
  }
  const int exciteSpan = inkMax - paperMax;
  for (int y = 0; y < outH; y++) {
    const uint32_t *src = reinterpret_cast<const uint32_t *>(
        static_cast<uint8_t *>(conv->pixels) +
        static_cast<size_t>(y) * conv->pitch);
    uint32_t *dst = intensityBuf.data() + static_cast<size_t>(y) * outW;
    for (int x = 0; x < outW; x++) {
      const uint32_t px = src[x];
      uint32_t m = (px >> 16) & 0xFFu;
      const uint32_t g = (px >> 8) & 0xFFu;
      const uint32_t b = px & 0xFFu;
      if (g > m) m = g;
      if (b > m) m = b;
      if (exciteSpan > 0) {
        int e = (static_cast<int>(m) - paperMax) * inkMax / exciteSpan;
        if (e < 0) e = 0;
        if (e > 255) e = 255;
        m = static_cast<uint32_t>(e);
      }
      dst[x] = 0xFF000000u | (m << 16) | (m << 8) | m;
    }
  }
  SDL_UpdateTexture(glassIntensityTexture, nullptr, intensityBuf.data(),
                    outW * static_cast<int>(sizeof(uint32_t)));
  SDL_DestroySurface(conv);
  glassHasPicture = true;
  return true;
}

// A FRESH SCREEN EVERY LAUNCH. Owner ruling 2026-08-18: "generate new grain
// every start of app."
//
// The field must not re-roll per FRAME -- that is beam-current noise, a
// different phenomenon, and it makes a still page crawl. Per LAUNCH is the
// opposite case: two runs of the app are two screens, and a coating that came
// out of the box identical every time is the one thing a settled powder never
// does. Rolled once, lazily, and held for the life of the process.
//
// It is registered as a reboot reset so the iOS in-process relaunch re-rolls
// too. The desktop reboot is execvp and gets a new process (and so a new seed)
// for free; without the reset the phone would keep one screen across every
// relaunch of a session and the two platforms would disagree.
//
// CROSSPOINT_SIM_GRAIN_SEED pins it, which is what a reproducible capture or a
// proof sheet needs -- a randomised field makes two runs incomparable.
static std::atomic<uint32_t> grainSeedValue{0};

static uint32_t grainSeed() {
  uint32_t s = grainSeedValue.load();
  if (s != 0) return s;
  if (const char *env = std::getenv("CROSSPOINT_SIM_GRAIN_SEED")) {
    char *end = nullptr;
    const unsigned long parsed = std::strtoul(env, &end, 10);
    if (end != env) s = static_cast<uint32_t>(parsed);
  }
  if (s == 0) {
    std::random_device rd;
    s = static_cast<uint32_t>(rd()) ^ (static_cast<uint32_t>(SDL_GetTicks()) << 1);
  }
  if (s == 0) s = 0x43524F53u;  // 0 is the "not yet rolled" sentinel
  grainSeedValue.store(s);
  return s;
}

// Re-roll on the iOS in-process reboot. The desktop reboot is execvp and gets a
// new process, so a fresh field falls out for free there; the phone longjmps
// into the same one and would otherwise keep a single coating for the whole
// session, which is the two platforms disagreeing about what "start of app"
// means.
const simreset::Registrar gGrainSeedReset{[] { grainSeedValue.store(0); }};

// THE GRAIN FIELD -- the coating on the glass -- moved to src/SurfaceTube.cpp
// on 2026-08-25. What stayed here is above: the SEED, because pageSheetSeed()
// (the LIGHT page's per-leaf identity) is built on it, so moving it would make
// the paper depend on the tube.

// sRGB relative luminance of a palette tone -- the same weights the contrast
// floor and the grain's budget use. It was hoisted to this point because an
// earlier arrangement put it 78 lines below its first caller, which therefore
// carried a byte-identical lambda copy of it. Every caller now lives in
// another translation unit and reaches it through the accessors below; it
// stays here because BOTH the sheet and the tube want it, and giving either
// one the definition would make the other depend on it. The curve is
// src/Srgb.h's; this is only the WCAG weighting over it.
static float srgbLumOf(const unsigned char c[3]) {
  return srgb::relativeLuminance(c);
}

// --- THE PAGE'S OWN SEED ---------------------------------------------------
//
// How many no-identity presents to tolerate before the warning below. The
// firmware's first activity enters within ~10 ms of the display coming up and
// the simulator presents at tens of hertz, so this is orders of magnitude more
// slack than a healthy boot needs and still trips within a second on a build
// whose firmware has no publisher.
static constexpr int kNoIdentityGrace = 120;
//
// A SHEET IS NOT A SCREEN. grainSeed() is deliberately re-rolled every launch
// (and across the iOS in-process reboot) because two runs of the app are two
// tubes -- and that is exactly wrong for paper. A book is not re-printed when
// you close it, so a page you turn back to must be the same sheet, including
// after a relaunch.
//
// So the LIGHT page's two fields seed from the SCREEN's IDENTITY: a page of a
// book from HalGPIO::publishReaderPageIdentity, a system screen from
// HalGPIO::publishScreenIdentity, resolved to one seed by the latch both write
// (SimulatorOverlay::sheetIdentitySeed). NOTE what is NOT in the hash:
// grainSeed(). Mixing it in would leave the field differing per page AND per
// launch, which looks like the feature and is not it.
//
// SYSTEM SCREENS GOT THIS ON 2026-08-24 and did not have it before, which is
// worth stating because the code reads as though they always did. Until then
// only readers published, so Home, Settings, the pickers and the file lists all
// fell to the branch below -- a per-LAUNCH sheet, and a show-through that was
// bit-exact dead there because the verso map promotes on a seed CHANGE. See
// src/SheetIdentity.h for the measurements and for why readers do not publish
// from onEnter().
//
// This is provable because in light mode with letterpress on the grain pass is
// SKIPPED (see presentIfNeeded), so a light page is fully determined by this
// number and nothing else random survives. docs/paper-defects.md.
static uint32_t pageSheetSeed() {
  uint32_t seed = 0;
  if (SimulatorOverlay::sheetIdentitySeed(seed)) return seed;

  // SAY SO, BUT NOT ON THE FIRST PRESENT. This branch is legitimate for
  // pre-channel firmware, and that is exactly why it shipped as a bug: build
  // 127 was archived against a firmware checkout one commit behind the
  // publisher, so this fired on every page and the whole app -- home screen,
  // every page of every book -- wore one sheet. Nothing in any log said so,
  // and the picture is subtle enough that "the flaws are not changing" was the
  // only symptom.
  //
  // The warning it grew then fired on the FIRST no-identity present, which
  // meant it fired on every launch that booted to Home and asserted, falsely,
  // that the firmware does not call the publisher. A diagnostic that is wrong
  // on most runs is not read on the run where it is right, so it now waits:
  // a healthy firmware publishes within the first activity entry, a few
  // milliseconds in, where a build with no publisher at all never does.
  static int presentsWithNoIdentity = 0;
  static bool warned = false;
  if (!warned && ++presentsWithNoIdentity > kNoIdentityGrace) {
    warned = true;
    SDL_Log("[paper] no sheet identity after %d presents -- every sheet will "
            "use the launch seed. The firmware calls neither "
            "publishReaderPageIdentity nor publishScreenIdentity; per-page "
            "paper is INACTIVE.",
            kNoIdentityGrace);
  }
  return grainSeed() ^ 0x50524553u;  // 'PRES', the pre-identity behaviour
}

// See the declaration above for why the drift lives at this one read.
//
// LIGHT ONLY. Sheet-to-sheet variation is a property of stock; a phosphor
// screen is one screen, and the dark page's ground is glass, not paper. Off is
// the default and off is a bit-exact early return, so a build that never
// touches the dial -- every desktop build, and an untouched install -- reads
// exactly the pair the host published, and pageSheetSeed() is not even called.
namespace {
PanelPalette livePanelPalette(bool dark) {
  const PanelPalette pal = publishedPanelPalette(dark);
  const int driftPct = SimulatorOverlay::paperDriftPct.load();
  if (dark || driftPct <= lightink::kPaperDriftOff) return pal;
  PanelPalette out = pal;
  // paperDriftedForPair, not paperDrifted: a page reached through this
  // resolver can be a NAMED PRESET's raw bytes (panelpalette::resolve),
  // which never passed through LightInkPalette.h's density/strength floor
  // clamps -- so the drift applied here must carry its own budget clamp
  // rather than assume one was already applied upstream.
  // docs/composition-test-2026-08-29.md.
  lightink::paperDriftedForPair(pal.ink, pal.paper, pageSheetSeed(), driftPct,
                                out.paper);
  return out;
}
}  // namespace

// THE LIGHT PAGE'S TWO FIELDS -- the letterpress plate, the sheet, the inkness
// plane between them and the show-through maps -- moved to
// src/SurfaceSheet.cpp on 2026-08-25. What stayed here is above: the page's
// SEED and the drift folded into livePanelPalette(), because that is the one
// palette read every consumer of the page's colour goes through, the dark
// passes included.

// The PRESENTED page rect in OUTPUT pixels, plus the orientation it was
// presented in -- what SurfaceSheet.cpp's outputToPanel inverts, and what the
// power path's collapse squeezes. Written by presentIfNeeded's layout pass
// below; both readers are in other translation units, reaching them through
// simsheet::panelXRef() / simpower::panelXRef().
//
// F2: on the desktop these were never computed. manualPlacement is
// `inset > 0 || topBand > 0` and the desktop keeps both at 0, so only the iOS
// path ever filled the panel rect; the letterbox branch works in LOGICAL units
// (which is right for the beam's clip rect, and wrong for a field drawn with
// logical presentation disabled). So the letterbox branch fills these from
// SDL_GetRenderLogicalPresentationRect instead, which is the same rect in real
// output pixels. Publishing geometry only; it changes no drawing.
static int sheetPanelX = 0, sheetPanelY = 0, sheetPanelW = 0, sheetPanelH = 0;
static int sheetPanelOrientation = GfxRenderer::Portrait;

// --- SCANLINES AND CORNER DEFOCUS (dark mode) -------------------------------
//
// Moved to src/SurfaceTube.cpp on 2026-08-25, with the grain field, for the
// reason at the top of src/SurfaceTube.h. The base PITCH is still computed
// here, in presentIfNeeded, because it comes from the presentation scale the
// sheet's lattice is derived from too -- one number, one place.

// --- THE POWER PATH'S WINDOW ONTO THIS FILE ---------------------------------
//
// src/SurfacePower.h says why these return references: SurfacePower.cpp binds
// file-scope references to them under the ORIGINAL NAMES, so every body that
// moved there is byte-identical to the one that left here. They sit at this
// point in the file because it is the first point past which every referent is
// defined. The two GLASS fields it wants are no longer among them -- they moved
// to src/SurfaceTube.cpp on 2026-08-25 and the two accessors below forward
// there, so unit 1 did not have to be edited by unit 3 to follow them.
namespace simpower {
SDL_Renderer *&rendererRef() { return sdl_renderer; }
SDL_Texture *&panelTextureRef() { return texture; }
SDL_Texture *&scanFieldRef() { return simtube::scanFieldRef(); }
SDL_Texture *&grainFieldRef() { return simtube::grainFieldRef(); }
int &panelXRef() { return sheetPanelX; }
int &panelYRef() { return sheetPanelY; }
int &panelWRef() { return sheetPanelW; }
int &panelHRef() { return sheetPanelH; }
int &panelOrientationRef() { return sheetPanelOrientation; }
std::mutex &pixelBufLockRef() { return pixelBufMutex; }
std::atomic<bool> &lastReadingDarkGroundRef() { return lastReadingDarkGround; }
std::atomic<bool> &pendingPresentRef() { return pendingPresent; }
std::atomic<uint32_t> &overlayClearColorRef() {
  return SimulatorOverlay::clearColor;
}
SimulatorOverlay::DrawFn &overlayDrawRef() {
  return SimulatorOverlay::overlayDraw;
}
std::atomic<bool> &powerOffCollapseRef() {
  return SimulatorOverlay::powerOffCollapse;
}
const SDL_RendererLogicalPresentation &logicalPresentationRef() {
  return kLogicalPresentation;
}

// These four are file-static or anonymous-namespace functions, so the power
// path cannot take their address from another translation unit. The wrappers
// are the whole of the indirection; `::` reaches the anonymous namespace's
// members through the implicit using-directive.
bool powerLogWanted() { return ::powerLogWanted(); }
bool hasDueScreenshot() { return ::hasDueScreenshot(); }
void captureDueScreenshots() { ::captureDueScreenshots(); }
panelpalette::Palette livePanelPalette(bool dark) {
  return ::livePanelPalette(dark);
}
bool isPortraitOrientation(GfxRenderer::Orientation orientation) {
  return ::isPortraitOrientation(orientation);
}
void getLogicalPresentationSize(GfxRenderer::Orientation orientation,
                                int *width, int *height) {
  ::getLogicalPresentationSize(orientation, width, height);
}
}  // namespace simpower

// --- WHAT THE SHEET REACHES BACK FOR ----------------------------------------
//
// The other half of src/SurfaceSheet.h's boundary. Same shape and same reason
// as simpower above: references, so every body that moved into
// SurfaceSheet.cpp is the body that left this file.
namespace simsheet {
SDL_Renderer *&rendererRef() { return sdl_renderer; }
int &panelXRef() { return sheetPanelX; }
int &panelYRef() { return sheetPanelY; }
int &panelWRef() { return sheetPanelW; }
int &panelHRef() { return sheetPanelH; }
int &panelOrientationRef() { return sheetPanelOrientation; }
uint32_t *pixelBufData() { return pixelBuf; }
uint64_t &pixelBufSeqRef() { return pixelBufSeq; }
std::mutex &pixelBufLockRef() { return pixelBufMutex; }
simtiming::PresentTiming &timingFrameRef() { return timingFrame; }
bool timingLogWanted() { return ::timingLogWanted(); }
uint32_t pageSheetSeed() { return ::pageSheetSeed(); }
panelpalette::Palette livePanelPalette(bool dark) {
  return ::livePanelPalette(dark);
}
float srgbLumOf(const unsigned char c[3]) { return ::srgbLumOf(c); }
std::atomic<int> &letterpressStrengthRef() {
  return SimulatorOverlay::letterpressStrength;
}
std::atomic<int> &paperToothPctRef() { return SimulatorOverlay::paperToothPct; }
std::atomic<int> &paperFormationPctRef() {
  return SimulatorOverlay::paperFormationPct;
}
std::atomic<int> &paperDefectsPctRef() {
  return SimulatorOverlay::paperDefectsPct;
}
std::atomic<int> &laidLinesStrengthRef() {
  return SimulatorOverlay::laidLinesStrength;
}
std::atomic<int> &showThroughStrengthRef() {
  return SimulatorOverlay::showThroughStrength;
}
std::atomic<int> &pressRingPctRef() { return SimulatorOverlay::pressRingPct; }
std::atomic<int> &pressDebossPctRef() {
  return SimulatorOverlay::pressDebossPct;
}
std::atomic<int> &pressPressurePctRef() {
  return SimulatorOverlay::pressPressurePct;
}
}  // namespace simsheet

// --- THE TUBE'S WINDOW ONTO THIS FILE ---------------------------------------
//
// src/SurfaceTube.h says why these return references. Same construction as the
// two blocks above, and it sits beside them for the same reason: this is past
// the point where every referent is defined.
namespace simtube {
SDL_Renderer *&rendererRef() { return sdl_renderer; }
uint64_t &pixelBufSeqRef() { return pixelBufSeq; }
simtiming::PresentTiming &timingFrameRef() { return timingFrame; }
bool timingLogWanted() { return ::timingLogWanted(); }
uint32_t grainSeed() { return ::grainSeed(); }
panelpalette::Palette livePanelPalette(bool dark) {
  return ::livePanelPalette(dark);
}
float srgbLumOf(const unsigned char c[3]) { return ::srgbLumOf(c); }
std::atomic<int> &grainStrengthRef() { return SimulatorOverlay::grainStrength; }
std::atomic<int> &grainCoverageRef() { return SimulatorOverlay::grainCoverage; }
std::atomic<int> &grainMottleCellsRef() {
  return SimulatorOverlay::grainMottleCells;
}
std::atomic<int> &grainMottleDepthPctRef() {
  return SimulatorOverlay::grainMottleDepthPct;
}
std::atomic<int> &scanlinesIntensityRef() {
  return SimulatorOverlay::scanlinesIntensity;
}
std::atomic<int> &scanlineBloomRef() { return SimulatorOverlay::scanlineBloom; }
std::atomic<int> &cornerDefocusStrengthRef() {
  return SimulatorOverlay::cornerDefocusStrength;
}
}  // namespace simtube

void HalDisplay::presentIfNeeded() {
  // Nothing may touch the GPU while backgrounded. Return BEFORE clearing
  // pendingPresent so the frame stays owed and lands on the way back in.
  if (g_backgrounded.load())
    return;

  if (powerLogFirstPresent) {
    powerLogFirstPresent = false;
    if (powerLogWanted())
      SDL_Log("[power] first presentIfNeeded after reboot: pendingPresent=%d "
              "beamStartedAt=%llu accumLastAddMs=%llu",
              (int)pendingPresent.load(), (unsigned long long)beamStartedAt,
              (unsigned long long)accumLastAddMs);
  }

  // THE SLEEP SCREEN DOES NOT REACH THE GLASS WHEN THE TUBE IS ABOUT TO SWITCH
  // OFF. Owner ruling 2026-08-24 -- see sleepSourcePixels for the sentence and
  // for why the kept copy exists alongside this. From deepSleep() onward every
  // frame the firmware offers is part of going to sleep, so it is DROPPED here:
  // `texture` keeps the page the reader was looking at, the glass keeps showing
  // it, and the collapse squeezes that.
  //
  // DROPPED, not held. A frame left owed would land on the iOS wake, where the
  // reboot is a longjmp and pendingPresent survives it -- the sleep screen would
  // then flash on the far side of a warm-up the owner skipped.
  //
  // Only when the collapse will actually run. With the dial off, or on a pale
  // page, the sleep screen flushes exactly as it always did, which is the whole
  // point of the sleep screen: an e-ink panel holds it with the power off.
  if (displaySleeping.load() && SimulatorOverlay::powerOffCollapse.load() &&
      lastReadingDarkGround.load()) {
    pendingPresent.store(false);
    presentHoldUntil.store(0);
    if (!powerLogSleepVetoSaid && powerLogWanted()) {
      powerLogSleepVetoSaid = true;
      SDL_Log("[power] sleep screen dropped: the collapse keeps the page that "
              "was on the glass");
    }
    return;
  }

  // Service inversion changes first: reconverting sets pendingPresent, so the
  // repolarized pixels ride the present below instead of waiting for the
  // firmware to refresh.
  if (pendingReconvert.exchange(false)) {
    // Mark the seq this produced so the beam trigger and the trail deposit
    // below can tell a repolarization from a page. The writer reports it from
    // under its own lock; a page written by the render task after that has a
    // different number and is treated as the page it is.
    const uint64_t produced = reconvertLastFrame();
    if (produced != 0) {
      const std::lock_guard<std::mutex> lock(pixelBufMutex);
      reconvertSeq = produced;
    }
  }

  const bool screenshotDue = hasDueScreenshot();

  // COALESCE. See presentHoldUntil: an antialiased page's composed pass is
  // 13-22 ms behind its 1-bit pass, and presenting the 1-bit one is the
  // full-screen flash. The frame is left OWED (pendingPresent stays set) rather
  // than dropped, so if no compose follows the deadline expires and this same
  // frame presents -- late, but never lost.
  //
  // A due screenshot overrides the hold: headless QA asks for a capture at a
  // wall-clock instant and must not silently receive a frame from 40 ms later.
  const uint64_t holdUntil = presentHoldUntil.load();
  if (holdUntil != 0 && !screenshotDue) {
    if (SDL_GetTicks() < holdUntil)
      return;  // pendingPresent untouched: still owed, lands next pass
    presentHoldUntil.store(0);
  }

  // THE PAGE FADE'S OWN WAKE. It parks the wall-clock instant its next
  // quantized alpha step is due (see the block that computes it) rather than
  // asking for every frame in between; this is what turns that parked time back
  // into a present. An atomic load and a compare per main-loop pass, on a loop
  // that is otherwise doing nothing.
  {
    const uint64_t fadeDue = pageFadeStepDueMs.load();
    if (fadeDue != 0 && SDL_GetTicks() >= fadeDue) {
      pageFadeStepDueMs.store(0);
      // Direct, like the sweep's and the trail's re-arm: a fade step is the
      // page dimming in place, and the glass (GlassCapture.h) is for what the
      // NEXT page sweeps in over -- the dimmed step is not worth a readback.
      pendingPresent.store(true);
    }
  }

  if (!pendingPresent.exchange(false) && !screenshotDue)
    return;

  if (!texture || !sdl_renderer)
    return;

  // THE POLARITY YOU WERE READING IN, latched on every present that is not part
  // of going to sleep.
  //
  // It exists for the power-off collapse, and it exists because the obvious
  // test is wrong: by the time the sleep loop runs, the firmware has drawn its
  // SLEEP SCREEN, and it draws that in LIGHT polarity even when the reader was
  // dark (measured 2026-08-23: inverted=0, paper F9F9F8, on a run whose every
  // page turn had built a scanline field). Asking "is the page dark" at the
  // moment of collapse therefore answers about the sleep screen, and a
  // dark-mode-only artifact never fires. What the fiction wants is the tube the
  // reader was looking at.
  //
  // THE 2026-08-24 RULING DOES NOT RETIRE THIS, checked rather than assumed.
  // Suppressing the sleep screen's PRESENT does not suppress the firmware's
  // setInverted(false) -- SleepActivity::onEnter calls it before it draws
  // anything, presents or no presents -- so panelIsDarkGround() still answers
  // about the sleep screen at collapse time. What did change is what this flag
  // means: it is now the polarity of the frame sleepSourcePixels kept, latched
  // on the same present and by the same guard, rather than a stand-in for a
  // frame nobody kept.
  // ...AND NOT ONCE THE SLEEP SCREEN HAS ANNOUNCED ITSELF. displaySleeping is
  // set in deepSleep(), which is LATE: SleepActivity::onEnter has already
  // called setInverted(false) by then, so any present landing in between
  // latched PALE and the collapse declined -- blaming the palette, on a page
  // that was a tube. Only the 30 ms present hold stood between that and a
  // shipped bug, and CROSSPOINT_SIM_PRESENT_FLASH=1 spends it every time
  // (reproduced by adversarial review, 2026-08-24). The screen identity the
  // base Activity publishes arrives BEFORE the inversion, so this is the edge
  // rather than the margin.
  if (!displaySleeping.load() && !SimulatorOverlay::sleepScreenEntered())
    lastReadingDarkGround = panelIsDarkGround();

  // The timing frame is armed HERE, past every early return, so a present that
  // was held or coalesced away is not reported as a free one.
  if (timingLogWanted()) {
    timingFrame = PresentTiming{};
    timingFrame.startNs = SDL_GetTicksNS();
  }

  extern GfxRenderer renderer;
  const GfxRenderer::Orientation orientation = renderer.getOrientation();
  applyWindowGeometryIfNeeded(orientation);

  // IS THIS A NEW PICTURE? Both CRT transients hang off that one question: a
  // beam sweep starts when the firmware writes a page, and a phosphor deposit
  // lands at the same instant. A re-present of the SAME frame (a window resize,
  // a screenshot, a trail's own self-requested frame) must do neither, or the
  // page would ghost while nothing happened.
  //
  // One integer, not 15 MB. The previous PICTURE is no longer kept here at all
  // -- it is captured from the composed glass at the foot of this function (see
  // captureGlass), because the surround and the pad have no framebuffer and a
  // panel-sized copy could never carry them.
  //
  // Entering deep sleep: whatever presents from here on is the frame the glass
  // holds for the whole sleep, so the beam and the trail are treated as OFF and
  // the existing off-paths below settle everything (capture dropped,
  // accumulator destroyed, no self-requested next frame). See displaySleeping's
  // comment for the owner report this closes and why deepSleep() cannot settle
  // it alone.
  const bool sleepSettled = displaySleeping.load();
  const float trailMs = sleepSettled ? 0.0f : glowTrailMs.load();
  const float beamMs = sleepSettled ? 0.0f : beamPaintMs.load();
  // The beam needs the PREVIOUS frame for the same reason the glow does -- it
  // is what is still on screen below the sweep -- so the capture is gated on
  // either wanting it, not on the glow alone.
  const bool wantPrevFrame = trailMs > 0.0f || beamMs > 0.0f;
  // Sampled BEFORE anything draws: the overlay's layout may request the next
  // present from inside this one, and that request must stay unconsumed.
  const uint64_t dirtyGenAtStart =
      glassDirtyGen.load(std::memory_order_relaxed);
  bool contentChanged = false;
  // WHETHER TO ARM, decided here (needs pixelBufSeq/reconvertSeq under the
  // lock); WHEN, deferred past every synchronous field rebuild this present
  // will do -- see the write site below, and S-035 / docs/zen-mode.md
  // mechanism #8 for the frame this replaces: arming HERE, before
  // ensureLetterpressField()'s up-to-265ms cache-miss rebuild, let the sweep's
  // clock burn through the entire 55ms beam budget before the clip that reads
  // it was ever built, landing a swept sliver nowhere near the panel.
  bool beamShouldArm = false;
  // A polarity reconvert bumps the seq without changing what the page says.
  // Decided under the lock, consumed by the beam arm here AND the trail
  // deposit below (src/GlassCapture.h, glasscapture::shouldArmBeam /
  // shouldDeposit). The deposit half was missing until 2026-09-04: a
  // light->dark flip deposited the LIGHT page's glass -- captured at its
  // absolute intensity -- into the phosphor accumulator, and the whole glass
  // flashed bright and faded over the trail. Measured on the desktop: every
  // pixel lifted 23 levels on the flip frame. No new picture came IN, so none
  // left the glass either.
  bool reconvertOnly = false;
  {
    const std::lock_guard<std::mutex> lock(pixelBufMutex);
    const size_t live = static_cast<size_t>(activeWidth()) * activeHeight();
    if (wantPrevFrame) {
      contentChanged = pixelBufSeq != presentedSeq;
      presentedSeq = pixelBufSeq;
      // A sweep can only start from a picture there is something to sweep OVER
      // -- and it must be a NEW picture; sweeping a reconvert paints the new
      // palette over the old one in bands (S-031). presentedSeq is still
      // advanced above, so the frame presents normally; only the sweep is
      // withheld -- and a sweep already in flight is abandoned, or its
      // remaining frames ARE that split-palette picture.
      reconvertOnly = reconvertSeq != 0 && pixelBufSeq == reconvertSeq;
      beamShouldArm = glasscapture::shouldArmBeam(contentChanged, glassHasPicture,
                                                  reconvertOnly);
      if (reconvertOnly) beamStartedAt = 0;
    } else if (glassPrevTexture) {
      // Both effects turned off: drop the capture rather than keep paying for
      // it, and stop any sweep in flight.
      destroyGlassTextures();
      beamStartedAt = 0;
    }
    // KEEP THIS PAGE FOR THE COLLAPSE. Same guard as the polarity latch above
    // and for the same reason: what the fiction wants is the tube the reader
    // was looking at. The keep itself is src/SurfacePower.cpp's, and it is
    // called with pixelBufMutex ALREADY HELD -- which is why the buffer and the
    // seq are passed rather than reached for.
    simpower::keepSleepSourceFrame(pixelBuf, live, pixelBufSeq, sleepSettled);

    // Pitch is the ACTIVE row stride. pixelBuf is allocated for the ceiling,
    // so at a lower scale the live picture occupies a prefix of it and the
    // ceiling's pitch would stride past every row.
    //
    // ONLY WHEN THE PICTURE MOVED. A phosphor trail presents 60-80 times per
    // page turn and the panel framebuffer is IDENTICAL on all but the first of
    // them -- only the accumulator's brightness moves -- yet this re-uploaded
    // the whole thing every time: 1.7 MB at 1x, 6.7 MB at 2x, 15 MB at the
    // phone's 3x, on the main thread, per present. It is the largest per-frame
    // cost in the whole trail and it draws nothing. Measured on a dark page
    // turn at 2x, dummy driver: 15.94 ms per trail present before, 11.75 ms
    // after, all of it out of the non-draw half (5.24 -> 1.05 ms).
    //
    // BIT-IDENTICAL BY CONSTRUCTION, in the strict sense: the skip is taken
    // only when the same texture OBJECT was last written from the same seq of
    // the same-sized buffer, so the bytes being skipped are the bytes already
    // in it. Keying on the texture pointer rather than on the seq alone is what
    // makes a window resize safe -- applyWindowGeometryIfNeeded destroys and
    // recreates `texture`, and a fresh STREAMING texture's contents are
    // undefined until written.
    //
    // The seq is bumped by both pixel writers (renderBwPixels and the
    // grayscale compose) and by nothing else, so a polarity reconvert -- which
    // goes through renderBwPixels -- is a change like any other.
    if (texture != uploadedTexture || pixelBufSeq != uploadedSeq ||
        live != uploadedLive) {
      const uint64_t upT0 = timingLogWanted() ? SDL_GetTicksNS() : 0;
      SDL_UpdateTexture(texture, nullptr, pixelBuf,
                        activeWidth() * sizeof(uint32_t));
      uploadedTexture = texture;
      uploadedSeq = pixelBufSeq;
      uploadedLive = live;
      if (timingLogWanted()) {
        timingFrame.upload.built = true;
        timingFrame.upload.ms =
            static_cast<double>(SDL_GetTicksNS() - upT0) / 1.0e6;
      }
    } else if (timingLogWanted()) {
      timingFrame.upload.served = true;
    }
  }


  // How much of the ghost is still emitting, 0 once it has decayed away.
  //
  // EXPONENTIAL, and the exponent is not a taste knob -- the source figure IS
  // the curve. Persistence is published as the time to decay to 10% of peak
  // (see panelpalette::PresetInfo), so the decay is 10^(-age/trail): exactly
  // 10% left at t = trail, a tenth of that again one trail later. The first
  // version was linear "to avoid a long tail", which threw away the only shape
  // information the source actually gave and is why it read as a cheap
  // cross-dissolve rather than as light dying.
  //
  // Cut off at 1/255 rather than at t = trail, because below one 8-bit step
  // there is nothing left to draw and continuing would hold the present loop
  // open for an invisible tail.
  // The ghost's own alpha computation lived here and is GONE with the block it
  // fed: the accumulator owns decay now (it multiplies itself down every
  // present), and keeping a second, independent fade of the same texture is
  // what produced the double draw this removes.
  // Clear to the field color, not the default black. On desktop the window is
  // exactly panel-sized so this never shows, but wherever the panel is
  // letterboxed (the phone presents it at 2x inside a taller screen) it is the
  // surround. It defaults to white, matching a blank e-ink page so the panel
  // edge is invisible; SimulatorOverlay::setClearColor lets a host that has an
  // appearance to follow say otherwise.
  const uint32_t field = SimulatorOverlay::clearColor.load();
  SDL_SetRenderDrawColor(sdl_renderer, static_cast<Uint8>(field >> 16),
                         static_cast<Uint8>(field >> 8),
                         static_cast<Uint8>(field), 255);
  SDL_RenderClear(sdl_renderer);

  // For portrait modes the landscape panel texture must be rotated to fill the
  // portrait window. SDL_RenderTextureRotated rotates around the center of dst,
  // so dst must stay landscape-oriented and be offset so its center coincides
  // with the window center. After rotation the result fills the portrait window.
  //
  // Portrait rotateCoordinates stores content rotated 90° CCW in the physical
  // buffer, so we rotate +90° CW here to undo it. PortraitInverted stores
  // content rotated 90° CW → undo with -90°.
  //
  // SDL3 renamed RenderCopy/RenderCopyEx to RenderTexture/RenderTextureRotated
  // and takes float rects; the arithmetic is unchanged.
  const float kW = static_cast<float>(activeWidth());
  const float kH = static_cast<float>(activeHeight());
  SDL_FRect portraitDst = {(kH - kW) / 2.0f, kW / 2.0f - kH / 2.0f, kW, kH};
  SDL_FRect landscapeDst = {0.0f, 0.0f, kW, kH};

  // With a reserved bottom band (SimulatorOverlay::setBottomInset), SDL's
  // letterbox cannot be used -- it always centres in the WHOLE output -- so
  // logical presentation is dropped and the panel is fitted manually into the
  // space above the band, in device pixels. The dst rect is landscape-shaped
  // and centered on the panel's display center in both orientations: for
  // landscape it IS the display area, for portrait the rotation about its
  // center turns it into one.
  const int inset = SimulatorOverlay::bottomInset.load();
  const int topBand = SimulatorOverlay::topInset.load();
  const bool manualPlacement = inset > 0 || topBand > 0;
  // The presented page rect, hoisted out of the manual-placement block because
  // the beam clips against it. Left at zero on the letterbox path, which fills
  // it from the logical size instead.
  int panelRectX = 0, panelRectY = 0, panelRectW = 0, panelRectH = 0;
  if (manualPlacement) {
    SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                     SDL_LOGICAL_PRESENTATION_DISABLED);
    int outW = 0, outH = 0;
    SDL_GetCurrentRenderOutputSize(sdl_renderer, &outW, &outH);
    const bool portrait = isPortraitOrientation(orientation);
    const float logW = portrait ? kH : kW;
    const float logH = portrait ? kW : kH;
    const float availH =
        SDL_max(1.0f, static_cast<float>(outH - inset - topBand));
    float scale = SDL_min(static_cast<float>(outW) / logW, availH / logH);
    // Keep the pixel-exact policy honest on this path too.
    //
    // ABOVE 1x the answer is the whole number below: one framebuffer pixel
    // covers exactly N screen pixels and the dither survives.
    //
    // BELOW 1x there is no such answer, and this is the honest statement of
    // the trade-off: a small phone genuinely cannot fit the page (an iPhone 13
    // mini leaves 1500 px of height for a 1584 px page once the status-bar band
    // and the pad's band are taken, an SE leaves 822), the next integer
    // reciprocal (1/2) is far too small to drop to, so the panel is decimated
    // by nearest-neighbor and some framebuffer rows and columns are simply not
    // drawn. Nothing here can avoid that.
    //
    // What it CAN do is put the result on whole device pixels, by quantising
    // the scale to kPixelQuantum steps. Two things follow, and neither is
    // cosmetic: the decimation phase is then identical for every row and
    // column instead of the rect sitting half a pixel off the grid, and the
    // page's edges land where the chrome anchored to them is drawn (the pad
    // hangs off panelBottom, which is an integer). The quantisation itself
    // costs under half a percent of the panel -- far less than the ~5% the
    // phone is short by.
    if (kLogicalPresentation == SDL_LOGICAL_PRESENTATION_INTEGER_SCALE) {
      if (scale >= 1.0f) {
        scale = SDL_floorf(scale);
      } else {
        // HYSTERESIS, and it is load-bearing. The band the host reserves is
        // DERIVED from the panel height published below -- the phone's pad
        // hangs off the page's bottom edge at a fraction of its height -- so
        // what is decided here comes back as a change in availH. That loop's
        // gain is well under 1 and settles on its own while the scale is
        // continuous; quantised, a fixed point that falls between two steps
        // flips between them forever, and because every flip requests a
        // present, an app that should present once per page presents on every
        // frame instead. Measured on an iPhone SE before this clause: an
        // endless 548x822 <-> 544x816 flip at the display rate.
        //
        // So hold the current step until the fit leaves it by a whole step --
        // which the loop's own residual (a fraction of a step) never does, and
        // a real change (rotation, a keyboard coming up) always does. The cost
        // is that a genuine one-step change is ignored: 0.4% of the panel,
        // smaller than the quantisation it rides on.
        static float heldScale = 0.0f;
        static int heldOutW = -1, heldOutH = -1;
        if (outW != heldOutW || outH != heldOutH) {
          heldScale = 0.0f;
          heldOutW = outW;
          heldOutH = outH;
        }
        if (heldScale > 0.0f &&
            SDL_fabsf(scale - heldScale) <= 1.0f / pixelQuantum()) {
          scale = heldScale;
        } else {
          scale =
              SDL_max(1.0f, SDL_floorf(scale * pixelQuantum())) / pixelQuantum();
          heldScale = scale;
        }
      }
    }
    // The filter follows the scale that was just settled, not the build flag.
    // Set here rather than at texture creation because `scale` is only known
    // once the host's reserved bands are in; it is a cheap per-present setter
    // and SDL only touches the sampler when the value changes.
    SDL_SetTextureScaleMode(texture, panelScaleModeFor(scale));

    // TOP-ALIGNED, not centered: the pad sits directly under the panel's
    // bottom edge (published below), so slack space goes under the pad
    // instead of splitting above and below the page. The alignment is to the
    // BOTTOM of the reserved top band, never to y=0 -- on a phone that band is
    // the status bar and the Island, and the page must start below it.
    //
    // Floored, and the panel rect below is built in whole pixels, because the
    // dst rect is derived from them: a half-pixel top margin puts the whole
    // page half a pixel off the grid, which is the thing the quantisation
    // above exists to avoid.
    const float topMargin = SDL_floorf(
        topBand + SDL_min(16.0f, (availH - logH * scale) / 2.0f));
    // The PRESENTED panel rect -- what the page actually occupies on the glass,
    // in device pixels. Everything else here derives from it, so it is computed
    // once, in integers, rather than recovered from the dst rect (which is a
    // different shape; see below).
    const int panelPxW = static_cast<int>(logW * scale);
    const int panelPxH = static_cast<int>(logH * scale);
    const int panelPxX = (outW - panelPxW) / 2;
    const int panelPxY = static_cast<int>(topMargin);
    // NOT the presented rect: dst is LANDSCAPE-shaped in every orientation,
    // because SDL_RenderTextureRotated rotates it about its own center and the
    // texture is the landscape framebuffer. In portrait it therefore reaches
    // outside the window horizontally by design -- a negative dst.x on a phone
    // is normal, and reading it as a screen rect is how this was once
    // mis-diagnosed as the panel rendering off-screen. Only its CENTRE is
    // meaningful, and that is the panel rect's center.
    const float cx = panelPxX + panelPxW / 2.0f;
    const float cy = panelPxY + panelPxH / 2.0f;
    portraitDst = {cx - kW * scale / 2.0f, cy - kH * scale / 2.0f, kW * scale,
                   kH * scale};
    landscapeDst = portraitDst;
    panelRectX = panelPxX;
    panelRectY = panelPxY;
    panelRectW = panelPxW;
    panelRectH = panelPxH;
    // ...and the same rect for the SHEET pass, which draws in output pixels
    // with logical presentation disabled and has to invert this transform to
    // find the page's ink. Same numbers on this path; the letterbox branch
    // below recovers them from SDL instead.
    sheetPanelX = panelPxX;
    sheetPanelY = panelPxY;
    sheetPanelW = panelPxW;
    sheetPanelH = panelPxH;
    sheetPanelOrientation = orientation;
    SimulatorOverlay::panelBottom.store(panelPxY + panelPxH);
    SimulatorOverlay::panelHeight.store(panelPxH);
    SimulatorOverlay::panelLeft.store(panelPxX);
    SimulatorOverlay::panelWidth.store(panelPxW);

    // Report the presented geometry once, and again whenever it changes.
    //
    // THE RECT LOGGED IS THE PRESENTED PANEL, not the dst rect handed to SDL.
    // The dst rect is landscape-shaped and rotated about its center, so in
    // portrait it legitimately starts left of x=0 and is wider than the screen.
    // Logging it invited exactly one wrong conclusion -- "dst -252 on a 1080 px
    // screen, the panel is being drawn off-screen on small phones" -- and a
    // debugging session was spent on a panel that was on screen the whole time.
    // What a reader needs is where the page landed, so that is what this
    // prints, and OFF-SCREEN now means the page really does leave the window.
    //
    // A fractional panel scale, or a panel off the pixel grid, damages the
    // Bayer dither -- the firmware's grays are a dot grid with a period of a
    // few device pixels, so anything short of 1 texel : N whole device pixels
    // beats against it. That is invisible in a screenshot (which is captured
    // pre-composite) and hard to eyeball on glass, so the numbers are logged
    // rather than left to be inferred. FRACTIONAL alone is expected on a phone
    // too short for a 1x page and is not a fault; OFF-GRID is.
    //
    // If SCALE IS INTEGRAL AND THE PANEL IS WHOLE but grays still shimmer on
    // device, the resample is happening BELOW the app: check that outW x outH
    // is the panel's true native pixel size. iPadOS Display Zoom renders the
    // whole screen at a smaller logical size and upscales it to the panel by a
    // non-integer factor, which no arithmetic in here can see or undo.
    {
      static float lastScale = -1.0f;
      static int lastOutW = -1, lastOutH = -1;
      if (scale != lastScale || outW != lastOutW || outH != lastOutH) {
        lastScale = scale;
        lastOutW = outW;
        lastOutH = outH;
        const bool wholeScale = scale == SDL_floorf(scale);
        const bool wholeDst = portraitDst.x == SDL_floorf(portraitDst.x) &&
                              portraitDst.y == SDL_floorf(portraitDst.y);
        const bool onScreen = panelPxX >= 0 && panelPxY >= 0 &&
                              panelPxX + panelPxW <= outW &&
                              panelPxY + panelPxH <= outH;
        SDL_Log("[panel] out %dx%d px, scale %.4f%s, panel %dx%d at %d,%d%s%s, "
                "filter %s",
                outW, outH, scale, wholeScale ? "" : " (FRACTIONAL)", panelPxW,
                panelPxH, panelPxX, panelPxY, wholeDst ? "" : " (OFF-GRID)",
                onScreen ? "" : " (OFF-SCREEN)",
                panelScaleModeFor(scale) == SDL_SCALEMODE_NEAREST ? "nearest"
                                                                  : "linear");
      }
    }
  }

  // THE PAGE FADE. Alpha on the panel texture over a field already cleared to
  // the paper tone IS a fade toward paper -- no second buffer, no per-pixel
  // work, and correct in both polarities because the field follows the palette.
  //
  // Exponential like the glow, and for the same reason: light does not die
  // linearly. It runs from full to kPageFadeFloor over the configured time and
  // then holds, so the page keeps being readable however long it is left.
  float pageAlpha = 1.0f;
  const float fadeMs = pageFadeMs.load();
  if (fadeMs > 0.0f) {
    const float age =
        static_cast<float>(SDL_GetTicks() - lastInteractionMs.load());
    // 10^(-age/fade) reaches 10% at the configured time; remap that decay onto
    // [1, floor] so "one fade period" is when it has settled.
    // The floor follows the palette on screen: a low-contrast page (Solarized)
    // cannot afford the deep fade and is left alone rather than made unreadable.
    const PanelPalette live = livePanelPalette(inverted.load());
    // ...scaled by the owner's chosen depth, which at the default (100) leaves
    // the legible floor exactly as it was and at 0 fades the page away.
    const float floor =
        pagefade::floorFor(live.ink, live.paper, pageFadeDepth.load());
    pageAlpha = pagefade::alphaFor(age, fadeMs, floor);
    // Keep presenting while it is still moving. Once it is within one 8-bit
    // step of the floor it has arrived and the loop stops asking -- otherwise
    // this would be a permanent render loop for a picture that is not changing.
    //
    // ...AND NOT ONE FRAME BEFORE THE NEXT ONE DIFFERS. What reaches the glass
    // is round(alpha * 255), and over a five-minute fade that moves 0.008 of a
    // code value per frame: re-arming unconditionally drew ~127 bit-identical
    // frames for every frame that changed, at 10.3% of a core, for as long as
    // the fade ran (S-019). pagefade::nextStepAgeMs says when the quantized
    // alpha actually moves; the wake is serviced at the top of this function.
    // The sequence of DISTINCT frames, and the wall time each lands at, are
    // unchanged -- only the duplicates are gone.
    //
    // NOTHING RE-ARMS pendingPresent HERE, deliberately. nextStepAgeMs either
    // names an age STRICTLY LATER than the one just drawn or says there is no
    // step left; re-arming on the second answer would be the render loop this
    // removes, reintroduced at the last millisecond of the fade -- and
    // stillMoving() and "a quantized step remains" disagree in a band one
    // eighth of a code value wide, which float arithmetic will find.
    const float nextAge = pagefade::stillMoving(age, fadeMs, floor)
                              ? pagefade::nextStepAgeMs(age, fadeMs, floor)
                              : -1.0f;
    pageFadeStepDueMs.store(nextAge > age
                                ? lastInteractionMs.load() +
                                      static_cast<uint64_t>(nextAge)
                                : 0);
  } else {
    pageFadeStepDueMs.store(0);
  }
  if (presentLogWanted() && fadeMs > 0.0f)
      SDL_Log("[fade] age %u ms -> alpha %.3f", 
              (unsigned)(SDL_GetTicks() - lastInteractionMs.load()), pageAlpha);
  SDL_SetTextureBlendMode(texture, pageAlpha < 1.0f ? SDL_BLENDMODE_BLEND
                                                    : SDL_BLENDMODE_NONE);
  SDL_SetTextureAlphaMod(texture,
                         static_cast<Uint8>(pageAlpha * 255.0f + 0.5f));

  // Draw the panel texture in whatever orientation is live. Factored out
  // because the beam draws the panel TWICE -- the old frame, then the new one
  // clipped to the swept band -- and the rotation arithmetic must not be
  // duplicated to do it.
  auto drawPanel = [&](SDL_Texture *tex) {
    switch (orientation) {
    case GfxRenderer::Portrait:
      SDL_RenderTextureRotated(sdl_renderer, tex, nullptr, &portraitDst, 90.0,
                               nullptr, SDL_FLIP_NONE);
      break;
    case GfxRenderer::PortraitInverted:
      SDL_RenderTextureRotated(sdl_renderer, tex, nullptr, &portraitDst, -90.0,
                               nullptr, SDL_FLIP_NONE);
      break;
    case GfxRenderer::LandscapeClockwise:
      SDL_RenderTextureRotated(sdl_renderer, tex, nullptr, &landscapeDst, 180.0,
                               nullptr, SDL_FLIP_NONE);
      break;
    default:
      SDL_RenderTexture(sdl_renderer, tex, nullptr, &landscapeDst);
    }
  };

  // WHICH FIELD COMPOSITES THIS PRESENT -- decided ONCE, here, before the first
  // of the three draw sites. src/FieldSelection.h holds the rule and the
  // argument; the short version is that each field's darkening budget assumes
  // it is the only pass, so "at most one" is what makes those budgets true.
  //
  // COMPUTED ONCE ON PURPOSE. The letterpress predicate below and the grain
  // suppression sixty lines further down used to be two independent reads of
  // the same two mutable values -- `display.isInverted()` and an atomic, either
  // of which another thread can move mid-present. Agreeing by construction
  // costs nothing; disagreeing draws letterpress AND grain over one page, which
  // is the exact budget breach the exclusion exists to prevent, and it would
  // show up as a page a few percent too dark on no particular frame.
  const fieldselect::Active fields = fieldselect::select(
      {display.isInverted(), SimulatorOverlay::scanlinesIntensity.load(),
       SimulatorOverlay::letterpressStrength.load(),
       SimulatorOverlay::grainStrength.load()});

  // ENTER AND LEAVE THE GLASS -- device pixels, the whole app surface, no
  // logical presentation. Every whole-sheet pass below goes through this pair.
  //
  // LEAVING IS NOT SYMMETRIC, and that asymmetry is the one trap here. On the
  // MANUAL placement path (the phone) logical presentation is already disabled
  // when this function reaches the panel draw, and the panel's dst rects are in
  // output pixels -- so "restoring" SDL's letterbox there would move the page
  // off its integer scale. Only the letterbox path has anything to restore.
  auto enterGlassSpace = [&](int *w, int *h) -> bool {
    SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                     SDL_LOGICAL_PRESENTATION_DISABLED);
    *w = 0;
    *h = 0;
    return SDL_GetCurrentRenderOutputSize(sdl_renderer, w, h) && *w > 0 &&
           *h > 0;
  };
  auto leaveGlassSpace = [&]() {
    if (manualPlacement) return;
    int logW = 0, logH = 0;
    getLogicalPresentationSize(orientation, &logW, &logH);
    SDL_SetRenderLogicalPresentation(sdl_renderer, logW, logH,
                                     kLogicalPresentation);
  };

  // PREWARM, before the sweep's clock starts. ensureLetterpressField() is a
  // cache-miss rebuild -- 240-265ms the first time this session needs it,
  // which is exactly the session's first real content change -- and it used
  // to run AFTER beamProgress was sampled, so the frame that finally reached
  // the glass was clipped against a clock that had not yet paid for the 265ms
  // spent building it (S-035, docs/zen-mode.md mechanism #8). Called here,
  // its cost lands BEFORE the arm below and before beamProgress is read, so
  // by the time either fires the field is already built -- the later call at
  // the draw site (unchanged) is then a cache hit. Gated on fields.letterpress
  // like that draw site; a degenerate palette or a zero strength makes this a
  // cheap no-op (ensureLetterpressTexture's own early-outs).
  if (fields.letterpress) simsheet::ensureLetterpressField();

  // ARM HERE, not at content-change detection (beamShouldArm, set above under
  // the pixel lock) -- this is the point past every synchronous rebuild the
  // sweep's own clip depends on staying fresh against, so the clock starts
  // against the frame that is actually about to be drawn and flipped rather
  // than one that took up to ~265ms longer to build. One write site, one read
  // site (beamProgress, immediately below) -- no second sample to desync the
  // clip's set/clear pairing the way the reverted first attempt did.
  if (beamShouldArm) beamStartedAt = SDL_GetTicks();

  // THE BEAM. How far down the GLASS the sweep has got, 0..1.
  //
  // IT SWEEPS THE WHOLE FACE, not the page's rectangle (2026-08-26, the same
  // owner ruling that moved the phosphor: "apply persistence and other crt
  // effects equally to paper and panel"). A tube has one gun and one raster;
  // there is no arrangement in which the picture arrives progressively and the
  // surround around it arrives all at once. So the old picture underneath is
  // the whole composed glass, and the band the new frame is clipped to spans
  // the output rather than the panel rect.
  //
  // The clip rect is in the CURRENT render coordinate space. On the manual path
  // that is output pixels and the band is the glass outright; under SDL's
  // letterbox it is logical units, where the page IS the whole window and the
  // two statements coincide. It is also why the clip is expressed against the
  // VISIBLE page rather than against the texture: in portrait the texture is
  // rotated, so a band of texture rows is a band of screen COLUMNS, and
  // clipping in texture space would sweep sideways.
  float beamProgress = 1.0f;
  const bool beamActive = beamMs > 0.0f && beamStartedAt != 0 &&
                          glassPrevTexture && glassHasPicture;
  if (beamActive) {
    beamProgress =
        static_cast<float>(SDL_GetTicks() - beamStartedAt) / beamMs;
    if (beamProgress >= 1.0f) {
      beamProgress = 1.0f;
      beamStartedAt = 0;
    }
  }
  const bool beamSweeping = beamActive && beamProgress < 1.0f;

  SDL_Rect visible;
  if (manualPlacement) {
    visible = {panelRectX, panelRectY, panelRectW, panelRectH};
  } else {
    int logW = 0, logH = 0;
    getLogicalPresentationSize(orientation, &logW, &logH);
    visible = {0, 0, logW, logH};
    // THE SAME RECT IN OUTPUT PIXELS, for the sheet pass. `visible` is in
    // LOGICAL units here -- correct for the beam's clip, which is applied in
    // the current render coordinate space -- but the sheet is drawn with
    // logical presentation disabled, so it needs the real letterboxed rect.
    // Without this the desktop divided by a zero panel width (F2: the four
    // panelRect values were only ever filled on the manual/iOS path).
    SDL_FRect present = {0.0f, 0.0f, 0.0f, 0.0f};
    if (SDL_GetRenderLogicalPresentationRect(sdl_renderer, &present) &&
        present.w > 0.0f && present.h > 0.0f) {
      sheetPanelX = static_cast<int>(present.x);
      sheetPanelY = static_cast<int>(present.y);
      sheetPanelW = static_cast<int>(present.w);
      sheetPanelH = static_cast<int>(present.h);
    } else {
      sheetPanelX = sheetPanelY = 0;
      sheetPanelW = logW;
      sheetPanelH = logH;
    }
    sheetPanelOrientation = orientation;
  }

  if (beamSweeping) {
    // Below the beam the OLD picture is still up -- opaque, not blended: it has
    // not been repainted yet, so it is not a ghost of anything. Drawn 1:1 in
    // device pixels, because that is the space it was captured in.
    int gw = 0, gh = 0;
    const bool gotGlass = enterGlassSpace(&gw, &gh);
    if (gotGlass) {
      const SDL_FRect full = {0.0f, 0.0f, static_cast<float>(gw),
                              static_cast<float>(gh)};
      SDL_SetTextureBlendMode(glassPrevTexture, SDL_BLENDMODE_NONE);
      SDL_SetTextureAlphaMod(glassPrevTexture, 255);
      SDL_SetTextureColorMod(glassPrevTexture, 255, 255, 255);
      SDL_RenderTexture(sdl_renderer, glassPrevTexture, nullptr, &full);
    }
    leaveGlassSpace();
    // ...and above it, only as much of the new frame as the beam has written.
    SDL_Rect sweep = visible;
    if (manualPlacement && gotGlass) sweep = {0, 0, gw, gh};
    const int swept =
        static_cast<int>(static_cast<float>(sweep.h) * beamProgress);
    const SDL_Rect clip = {sweep.x, sweep.y, sweep.w, swept};
    SDL_SetRenderClipRect(sdl_renderer, &clip);
  }

  switch (orientation) {
  case GfxRenderer::Portrait:
    // dst center = window center, landscape-sized panel texture.
    SDL_RenderTextureRotated(sdl_renderer, texture, nullptr, &portraitDst, 90.0,
                             nullptr, SDL_FLIP_NONE);
    break;
  case GfxRenderer::PortraitInverted:
    SDL_RenderTextureRotated(sdl_renderer, texture, nullptr, &portraitDst,
                             -90.0, nullptr, SDL_FLIP_NONE);
    break;
  case GfxRenderer::LandscapeClockwise:
    SDL_RenderTextureRotated(sdl_renderer, texture, nullptr, &landscapeDst,
                             180.0, nullptr, SDL_FLIP_NONE);
    break;
  default:
    SDL_RenderTexture(sdl_renderer, texture, nullptr, &landscapeDst);
  }

  // LETTERPRESS -- the LIGHT page's surface treatment (doctrine 2026-08-22:
  // light is paper and ink, dark is CRT). Drawn over the PANEL only, through
  // the same drawPanel rotation and dst as the page itself, because ink
  // squash is a property of the paper and not of the glass -- the one-sheet
  // argument that moved the grain OUT past the overlay runs the other way
  // here. Content-locked and aperiodic, so scaling with the panel cannot
  // beat against the presentation. MOD blend: it can only darken. Its filter
  // copies the panel texture's live one, so the ring gets whatever treatment
  // the glyph edges themselves get at this scale.
  //
  // IT MOVED INSIDE THE BEAM'S CLIP on 2026-08-26. The old picture under a
  // sweep used to be the raw previous FRAMEBUFFER, which carries no surface
  // treatment, so drawing the letterpress over the whole panel was the only way
  // the un-swept half got any. The old picture is now the composed GLASS and
  // already has its letterpress in it, so an unclipped pass would print the
  // squeeze twice below the beam line.
  if (fields.letterpress) {
    if (simsheet::ensureLetterpressField()) {
      SDL_ScaleMode panelMode = kPanelScaleMode;
      SDL_GetTextureScaleMode(texture, &panelMode);
      SDL_SetTextureScaleMode(simsheet::letterpressField(), panelMode);
      drawPanel(simsheet::letterpressField());
    }
  } else if (simsheet::letterpressField()) {
    simsheet::destroyLetterpressField();
  }

  if (beamSweeping) {
    // CLEARED BEFORE THE OVERLAY, not after it. SDL keeps the clip in the
    // coordinate space it was set in, and the overlay changes that space; the
    // overlay re-states its own band in device pixels below.
    SDL_SetRenderClipRect(sdl_renderer, nullptr);
    // A sweep only sweeps if something presents while it does, and an e-ink
    // firmware presents once per page. Same self-driving arrangement as the
    // glow's trail, and it stops asking the moment the beam reaches the bottom.
    pendingPresent.store(true);
  }

  // Overlay chrome lives in the letterboxed margins, which the panel's logical
  // coordinate space cannot address -- so drop logical presentation, hand the
  // painter real pixels, then restore it for the next frame.
  //
  // THE SWEEP COVERS IT TOO. The pad is on the same sheet of glass as the page
  // and the raster reaches it last, so while the beam is running the pad is
  // only drawn as far down as the beam has got; everything below is the pad as
  // the previous frame left it, already on screen from the glass draw above.
  if (SimulatorOverlay::overlayDraw) {
    SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                     SDL_LOGICAL_PRESENTATION_DISABLED);
    int outW = 0, outH = 0;
    if (SDL_GetCurrentRenderOutputSize(sdl_renderer, &outW, &outH) && outW > 0) {
      // ONLY ON THE MANUAL PATH, and the reason is that this band and the
      // panel's are stated in two coordinate systems. The panel's clip is set
      // in the CURRENT render space; on the manual path that is output pixels
      // and the two bands are the same screen rows, but under SDL's letterbox
      // it is LOGICAL units covering only the letterboxed sub-rect, so a band
      // at the same FRACTION lands on different rows and the page's beam line
      // and the pad's would disagree by the margin. Unreachable today (the
      // desktop registers no overlay painter and iOS always places manually),
      // and left as a guard rather than as arithmetic because a host that
      // letterboxes AND paints chrome does not exist to test against.
      const bool sweepChrome = beamSweeping && manualPlacement;
      SDL_Rect clip = {0, 0, outW,
                       static_cast<int>(static_cast<float>(outH) * beamProgress)};
      if (sweepChrome) SDL_SetRenderClipRect(sdl_renderer, &clip);
      SimulatorOverlay::overlayDraw(sdl_renderer, outW, outH);
      if (sweepChrome) SDL_SetRenderClipRect(sdl_renderer, nullptr);
    }
    int logW = 0, logH = 0;
    getLogicalPresentationSize(orientation, &logW, &logH);
    SDL_SetRenderLogicalPresentation(sdl_renderer, logW, logH,
                                     kLogicalPresentation);
  }

  // ------------------------------------------------------------------------
  // THE PHOSPHOR, OVER THE WHOLE GLASS.
  //
  // Four things happen here, in this order, and the order is the physics and
  // not a convenience:
  //
  //   FADE     what is already in the buffer has been decaying since the last
  //            present.
  //   DEPOSIT  the picture that was on the glass until this present starts
  //            decaying only from NOW, so it is added after the fade. That is
  //            what makes each contribution's age its own.
  //   CAPTURE  the glass as it now stands, ready to be the next deposit --
  //            and taken here, BEFORE the accumulator is drawn, because a
  //            capture that included the trail would deposit the trail back
  //            into itself and nothing would ever decay.
  //   DRAW     the sum, MAXIMUM, over everything.
  //
  // WHY IT SITS HERE. Before 2026-08-26 this ran immediately after the page was
  // drawn, above the letterpress and above the overlay, and the buffer was the
  // panel's own size: the afterglow stopped at the page's edge and the pad and
  // the surround never glowed at all. The owner's ruling that day -- "apply
  // persistence and other crt effects equally to paper and panel" -- is the
  // 2026-08-18 grain ruling restated (it is one sheet of glass, and a grainy
  // rectangle on a clean ground is an arrangement no physical screen has).
  // So the pass moved down past the overlay, exactly where the grain sits, and
  // stayed ABOVE the scanlines, the sheet and the grain, because those are
  // COVERAGE and everything under them is light the coverage gates.
  bool accumLive = false;
  {
    int gw = 0, gh = 0;
    const bool inGlass = wantPrevFrame && enterGlassSpace(&gw, &gh);
    if (inGlass) {
      if (trailMs > 0.0f) {
        ensureAccumTexture(gw, gh);
        if (accumTexture) {
          const uint64_t now = SDL_GetTicks();
          const uint64_t accumT0 = timingLogWanted() ? SDL_GetTicksNS() : 0;
          const float dt = static_cast<float>(now - accumLastFadeMs);
          SDL_Texture *restore = SDL_GetRenderTarget(sdl_renderer);
          SDL_SetRenderTarget(sdl_renderer, accumTexture);
          // dst *= 10^(-dt/trail), expressed as a blend against black. This is
          // the SAME curve the single-ghost version used; it is just applied to
          // a running sum instead of to one frame.
          if (dt > 0.0f) {
            const float keep = SDL_powf(10.0f, -dt / trailMs);
            const int drop = static_cast<int>((1.0f - keep) * 255.0f + 0.5f);
            if (drop > 0) {
              SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_BLEND);
              SDL_SetRenderDrawColor(sdl_renderer, 0, 0, 0,
                                     static_cast<Uint8>(SDL_min(255, drop)));
              SDL_RenderFillRect(sdl_renderer, nullptr);
              // The scalar shadow of that fill: see src/TrailLifetime.h. It is
              // stepped with the SAME `drop` the texture just took, so it stays
              // a valid upper bound however the present cadence wanders.
              accumPeakBound = trail::fadePeakBound(accumPeakBound, drop,
                                                    trailFadeRoundBias);
              // THE CLOCK ADVANCES ONLY WHEN THE FADE ACTUALLY APPLIED, and
              // this used to be an unconditional `accumLastFadeMs = now` above
              // the drop computation. `drop` is a ROUNDED 8-bit alpha, so a
              // present that lands less than about 1 ms after the last one
              // rounds it to zero -- and the old placement then threw that
              // millisecond away. Nothing decayed and the elapsed time could
              // never be recovered, so a trail driven by a fast enough present
              // loop simply stops fading.
              //
              // It cannot happen at 60 Hz (dt 16 ms gives drop 8 on the shipped
              // 1095 ms trail) which is why it has never been seen, and it is
              // precisely what raising the refresh rate walks toward: at 120 Hz
              // drop is 4-5, and every further doubling halves it again.
              // Leaving the clock alone lets dt accumulate until the fade is
              // representable, which is both correct and MORE accurate -- one
              // larger multiply rounds once where several small ones round
              // several times.
              accumLastFadeMs = now;
            }
          }
          // THE DEPOSIT IS THE GLASS THAT WAS THERE, as intensity. Only if a
          // capture has actually landed and is the size of the buffer it is
          // going into: a STREAMING texture's contents are undefined until
          // written, and depositing one anyway put garbage into the accumulator
          // at the exact moment the owner picked a phosphor.
          //
          // MAXIMUM, NOT ADD -- and this is S-016. A pixel lit in two frames is
          // one phosphor being re-excited, not two emitters stacked, so it
          // cannot exceed full emission. The deposit kept summing, and with a
          // long trail (P7 at 2828 ms, content changing every 100 ms) the
          // running sum tends toward roughly 12x a single page -- precisely the
          // owner's report that it was "the long persistence ones".
          //
          // Same fallback shape as the composite: if the renderer cannot
          // compose MAXIMUM, take ADD at reduced strength rather than nothing,
          // because half a trail beats no trail.
          // ONCE PER CAPTURED GLASS, not once per content change. An
          // ANTIALIASED PAGE IS WRITTEN TWICE -- a 1-bit base pass, then the
          // composed one 13-22 ms later -- so the seq moves twice per page
          // turn, and the second of those arrives while the beam is still
          // sweeping and therefore before a new capture has been taken. Without
          // this the same picture is deposited twice, which on a renderer
          // without MAXIMUM (see the blend report below) DOUBLES it: measured,
          // the integrated trail energy of two runs of the same binary differed
          // by 4x depending on whether the second write landed inside the
          // sweep.
          //
          // It is also the more honest model. The 1-bit pass is never presented
          // at all -- the present hold coalesces it, which is what the page-turn
          // flash work bought -- and a frame that never reached the glass
          // cannot have left phosphor on it.
          static uint64_t depositedGlassSeq = 0;
          static bool everDeposited = false;
          const bool freshGlass = !everDeposited || depositedGlassSeq != glassSeq;
          const bool canDeposit = glasscapture::shouldDeposit(
              {contentChanged, glassHasPicture, freshGlass,
               glassIntensityTexture != nullptr && glassW == gw && glassH == gh,
               reconvertOnly, panelIsDarkGround()});
          if (canDeposit) {
            static SDL_BlendMode depositMax = SDL_ComposeCustomBlendMode(
                SDL_BLENDFACTOR_ONE, SDL_BLENDFACTOR_ONE,
                SDL_BLENDOPERATION_MAXIMUM, SDL_BLENDFACTOR_ONE,
                SDL_BLENDFACTOR_ONE, SDL_BLENDOPERATION_MAXIMUM);
            SDL_Texture *deposit = glassIntensityTexture;
            const bool gotMax =
                depositMax != SDL_BLENDMODE_INVALID &&
                SDL_SetTextureBlendMode(deposit, depositMax);
            if (!gotMax) {
              SDL_SetTextureBlendMode(deposit, SDL_BLENDMODE_ADD);
              SDL_SetTextureAlphaMod(deposit, 96);
            } else {
              SDL_SetTextureAlphaMod(deposit, 255);
            }
            // SAID ONCE, AND WORTH THE LINE. Measured 2026-08-26: SDL's
            // SOFTWARE renderer -- the desktop canary and the Mac apps -- does
            // not compose SDL_BLENDOPERATION_MAXIMUM, so it takes the ADD
            // fallback here and at the composite, while the phone's Metal
            // backend takes MAXIMUM. That is not a cosmetic difference: ADD
            // BRIGHTENS a pixel the old frame and the new one both lit, and
            // MAXIMUM leaves it alone. Every trail-brightness figure ever
            // measured on this machine is therefore the fallback path, and a
            // page that brightens under a trail on the desktop is expected
            // rather than a bug. Without this line the two platforms look like
            // the same code disagreeing about arithmetic.
            static bool saidDeposit = false;
            if (!saidDeposit) {
              saidDeposit = true;
              SDL_Log("[accum] deposit blend: %s",
                      gotMax ? "MAXIMUM" : "ADD fallback (no MAXIMUM here)");
            }
            SDL_SetTextureColorMod(deposit, 255, 255, 255);
            SDL_RenderTexture(sdl_renderer, deposit, nullptr, nullptr);
            accumLastAddMs = now;
            depositedGlassSeq = glassSeq;
            everDeposited = true;
            // FULL SCALE, unconditionally, and not the panel's brightest tone.
            // The deposit is MAXIMUM of an 8-bit texture so 255 is the true
            // ceiling, and the ADD fallback a line above can saturate there
            // outright.
            accumPeakBound = 255.0f;
          }
          SDL_SetRenderTarget(sdl_renderer, restore);
          // Still emitting? A deposit is spent once it has decayed below one
          // 8-bit step, which is 10^-2.4 trails. Past that the accumulator is
          // black and asking for more frames would be a permanent render loop.
          // AND ONLY ON A GROUND THAT SHOWS IT. A pale page draws no trail at
          // all (see the draw below), so keeping the accumulator "live" there
          // bought ~30 presents per redraw for a picture identical to the last
          // one. Measured by the audit; it is pure waste and it is also
          // battery.
          //
          // ...AND ONLY WHILE IT CAN STILL CHANGE A PIXEL. src/TrailLifetime.h
          // has the argument; the short version is that 2.4 trails is the decay
          // to one 8-bit step against BLACK, and the accumulator is composited
          // MAXIMUM over a page whose darkest tone is the PAPER. On the shipped
          // dark pair the paper is 8% of the ink, so the last 1.4 of those
          // trails were presents that could not move a pixel -- measured, 15
          // consecutive byte-identical frames, 64% of the trail's wall time.
          //
          // The 2.4 stays as a backstop so this can only ever shorten the loop,
          // never lengthen it: a palette whose paper is pure black makes
          // invisibleAtOrBelow() zero, and without the backstop that is a
          // render loop with no end.
          accumLive = panelIsDarkGround() && accumLastAddMs != 0 &&
                      accumPeakBound > trailInvisibleAtOrBelow() &&
                      static_cast<float>(now - accumLastAddMs) < trailMs * 2.4f;
          if (timingLogWanted()) {
            timingFrame.accum.built = canDeposit;
            timingFrame.accum.served = !canDeposit;
            timingFrame.accum.ms =
                static_cast<double>(SDL_GetTicksNS() - accumT0) / 1.0e6;
          }
        }
      } else if (accumTexture) {
        // Glow turned off: drop the buffer rather than keep paying for it.
        SDL_DestroyTexture(accumTexture);
        accumTexture = nullptr;
        accumW = accumH = 0;
        accumLastAddMs = 0;
      }

      // CAPTURE, once per new picture and never during a sweep. See
      // captureGlass for the three rules; the one that is easy to lose is that
      // a capture taken on the content-change present itself, with the beam
      // running, records mostly the OLD page and hands it back as if it were
      // the new one.
      // A SIZE CHANGE OVERRIDES THE SWEEP GATE. Rule 2 holds the capture back
      // while the beam runs, and on a rotation or a window resize mid-sweep
      // that starved it: the beam went on stretching an old-sized
      // glassPrevTexture NEAREST across the new output, and because the deposit
      // requires glassW == gw that page's phosphor was skipped outright. So a
      // mismatched size captures immediately and ABANDONS the sweep with it --
      // there is no coherent old picture to sweep from once the glass has
      // changed shape, and a half-swept capture is the lesser evil only while
      // the two agree.
      const bool glassSizeStale = glassW != gw || glassH != gh;
      if (glasscapture::shouldCapture({beamSweeping, glassSizeStale,
                                       glassHasPicture, glassSeq, presentedSeq,
                                       glassGen, dirtyGenAtStart})) {
        const uint64_t capT0 = timingLogWanted() ? SDL_GetTicksNS() : 0;
        if (glassSizeStale) beamStartedAt = 0;
        if (captureGlass(gw, gh)) {
          glassSeq = presentedSeq;
          glassGen = dirtyGenAtStart;
        }
        if (timingLogWanted()) {
          timingFrame.glass.built = true;
          timingFrame.glass.ms =
              static_cast<double>(SDL_GetTicksNS() - capT0) / 1.0e6;
        }
      } else if (timingLogWanted()) {
        timingFrame.glass.served = glassHasPicture;
      }

      // THE ACCUMULATOR GOES ON TOP, which is what a phosphor does: everything
      // written recently is still emitting while the new frame is drawn over
      // it. 1:1 in device pixels -- it was captured in this space, so it lands
      // where the light was actually emitted, which is what lets a ghost stay
      // put when the page itself moves (zen, a keyboard coming up).
      //
      // This draws the SUM of every recent frame, not the last one. Flipping
      // ten pages in a second leaves ten deposits in there, each already faded
      // by its own age.
      if (presentLogWanted())
        SDL_Log("[accum] trail %.0f live=%d tex=%d changed=%d lastAdd=%llu",
                trailMs, (int)accumLive, accumTexture ? 1 : 0,
                (int)contentChanged, (unsigned long long)accumLastAddMs);
      if (accumLive && accumTexture) {
        const bool darkGround = panelIsDarkGround();

        // A PHOSPHOR ADDS LIGHT, and the accumulator is a buffer OF LIGHT:
        // black wherever nothing has been emitted. That composites one way and
        // one way only -- additively, onto a dark ground.
        //
        // IT USED TO CROSS-DISSOLVE ON A PALE GROUND, and that was wrong from
        // the moment this became an accumulator (build 90). The single-ghost
        // version it replaced held a real PICTURE -- the previous frame, paper
        // and all -- so blending it over a pale page was a sensible dissolve.
        // The accumulator holds light on black, so blending it at alpha 128
        // over a pale page draws 50% BLACK across the whole sheet: the page
        // turns gray and the previous page's text hangs there inside it.
        // Reported from the phone with a screenshot, on the CRT schemes in
        // light mode.
        //
        // So on a pale ground there is no trail at all. That is not a
        // regression against the pre-accumulator behaviour so much as an
        // admission of what the comment here already said: a glowing page is a
        // dark-ground idea, and adding light to white paper cannot express it.
        if (!darkGround) {
          accumLive = false;
        } else {
          // MAXIMUM, NOT ADD -- and this is the difference between a trail and
          // a flash.
          //
          // Measured on screen: with ADD, the frame at a page turn is the
          // arithmetic SUM of the old page and the new one. 99.77% of the page
          // is brighter than either, and |frame - (old+new)| averages 0.11 of a
          // level. Mean page luminance jumped 38.6 -> 71.8, +86%, decaying over
          // a second. That is the flash the owner reported, and it survived the
          // double-draw fix because ADD was doing it honestly all along.
          //
          // The physics were wrong, not the arithmetic. A pixel lit in BOTH
          // frames is one phosphor being re-excited, not two emitters stacked
          // -- it cannot exceed full emission. Summing says otherwise and
          // doubles the page. Taking the MAXIMUM is the saturating model.
          //
          // SDL_BLENDOPERATION_MAXIMUM ignores the blend factors, so the
          // accumulator is composited unscaled. If a renderer cannot compose it
          // (the call fails), fall back to ADD at reduced strength rather than
          // to nothing: half a trail beats a flash.
          static SDL_BlendMode maxBlend = SDL_ComposeCustomBlendMode(
              SDL_BLENDFACTOR_ONE, SDL_BLENDFACTOR_ONE,
              SDL_BLENDOPERATION_MAXIMUM, SDL_BLENDFACTOR_ONE,
              SDL_BLENDFACTOR_ONE, SDL_BLENDOPERATION_MAXIMUM);
          const bool gotMax =
              maxBlend != SDL_BLENDMODE_INVALID &&
              SDL_SetTextureBlendMode(accumTexture, maxBlend);
          if (!gotMax) {
            SDL_SetTextureBlendMode(accumTexture, SDL_BLENDMODE_ADD);
            SDL_SetTextureAlphaMod(accumTexture, 96);
          } else {
            SDL_SetTextureAlphaMod(accumTexture, 255);
          }
          static bool saidComposite = false;
          if (!saidComposite) {
            saidComposite = true;
            SDL_Log("[accum] composite blend: %s",
                    gotMax ? "MAXIMUM" : "ADD fallback (no MAXIMUM here)");
          }
        }

        // A CASCADE PHOSPHOR CHANGES COLOUR AS IT DIES, and with an accumulator
        // that is an APPROXIMATION and is marked as one: the buffer holds
        // deposits of many ages mixed together, and one colour multiply cannot
        // give each its own point on the ramp. It is driven by the age of the
        // NEWEST deposit, which is the one carrying most of the brightness.
        // Getting this exact needs two accumulators running at the two layers'
        // decay rates -- the honest model of what a cascade physically is --
        // and that is worth doing if this ever looks wrong.
        //
        // ONLY ON THE ADDITIVE PATH: on pale paper the same multiply hits the
        // paper too and the whole decaying frame washes green, which is a
        // stain, not a longer-lived layer.
        //
        // THE ACCUMULATOR HOLDS INTENSITY, so the colour mod is what paints the
        // trail -- and its ramp starts at the live INK, not white. A coloured
        // deposit could not work: the recolour is a multiply and a multiply can
        // only remove channels, so green ink times an orange tail is olive,
        // never orange, and a mixed page's fade could never change hue toward
        // the surviving phosphor (owner report 2026-08-21, P46+P33).
        const uint32_t tail = glowTailTint.load();
        const PanelPalette livePal = livePanelPalette(display.isInverted());
        Uint8 mod[3] = {255, 255, 255};
        if (darkGround) {
          for (int c = 0; c < 3; c++) mod[c] = livePal.ink[c];
          if (tail != kNoGlowTail) {
            const float age =
                static_cast<float>(SDL_GetTicks() - accumLastAddMs);
            // The handover happens when the FAST phosphors die, not at the end
            // of the whole fade: for the reported mix that is ~17 ms into 2828,
            // so the ramp runs over the published ONSET when one exists.
            // Presets that never set one (onset 0) keep the old whole-trail
            // timing.
            const float onset = glowTailOnsetMs.load();
            float t = onset > 0.0f
                          ? age / onset
                          : (trailMs > 0.0f ? age / trailMs : 1.0f);
            if (t < 0.0f) t = 0.0f;
            if (t > 1.0f) t = 1.0f;
            for (int c = 0; c < 3; c++) {
              const float target =
                  static_cast<float>((tail >> (16 - 8 * c)) & 0xFF);
              mod[c] = static_cast<Uint8>(
                  (1.0f - t) * static_cast<float>(mod[c]) + t * target + 0.5f);
            }
          }
        }
        SDL_SetTextureColorMod(accumTexture, mod[0], mod[1], mod[2]);
        if (presentLogWanted())
          SDL_Log("[accum2] darkGround=%d drawn=%d age=%u", (int)darkGround,
                  (int)accumLive,
                  (unsigned)(SDL_GetTicks() - accumLastAddMs));
        if (accumLive) {
          const SDL_FRect full = {0.0f, 0.0f, static_cast<float>(gw),
                                  static_cast<float>(gh)};
          // CLIPPED TO THE SWEPT BAND WHILE THE BEAM RUNS, and this is not a
          // detail. Below the beam line the glass still holds the PREVIOUS
          // frame -- the raster has not repainted it yet -- and that frame
          // already showed whatever trail it showed at the time. Compositing
          // this present's accumulator over it would light the old picture a
          // second time, and on a renderer without MAXIMUM (the desktop, see
          // the blend report above) the ADD fallback then BRIGHTENS the whole
          // un-swept region by up to 18% for the length of the sweep.
          // Measured: the un-swept band came back as the previous page's exact
          // pixel histogram with every level scaled by 1.175.
          SDL_Rect band = {0, 0, gw,
                           static_cast<int>(static_cast<float>(gh) *
                                            beamProgress)};
          if (beamSweeping) SDL_SetRenderClipRect(sdl_renderer, &band);
          SDL_RenderTexture(sdl_renderer, accumTexture, nullptr, &full);
          if (beamSweeping) SDL_SetRenderClipRect(sdl_renderer, nullptr);
          // A fade only animates if something presents while it fades, and the
          // firmware will not: an e-ink reader draws a page and stops. So the
          // trail asks for its own next frame, and stops asking the moment it
          // is done -- which is what keeps this from becoming a permanent
          // render loop.
          pendingPresent.store(true);
        }
      }
      leaveGlassSpace();
    } else {
      if (accumTexture) {
        // Neither effect is on any more (or the glass has no size): drop the
        // buffer rather than keep paying for it.
        SDL_DestroyTexture(accumTexture);
        accumTexture = nullptr;
        accumW = accumH = 0;
        accumLastAddMs = 0;
        accumPeakBound = 0.0f;
      }
      // enterGlassSpace() DISABLES logical presentation before it can fail, so
      // a zero-sized output would otherwise leave the letterbox path off for
      // the rest of this present. The passes below each restore it anyway; this
      // is the belt, and it costs one call on a path that never runs.
      if (wantPrevFrame) leaveGlassSpace();
    }
  }

  // THE GRAIN GOES ON LAST -- and "last" now means after the OVERLAY too, over
  // the whole app surface rather than just the panel.
  //
  // Owner ruling 2026-08-18: "apply the grain to the ios app background too,
  // not just the panel." It is one sheet of glass. Texturing only the page made
  // the panel a grainy rectangle floating on a clean ground, which is the one
  // arrangement no physical screen has. So the field is generated at the OUTPUT
  // size and drawn over everything -- page, pad, bezel, letterbox margins.
  //
  // The ordering that puts it after the beam, the accumulator and the fade was
  // always the physics (all of those are light leaving the phosphor, and its
  // coverage gates them); extending past the overlay is the same argument
  // applied to the chrome the harness paints.
  //
  // Still drawn with logical presentation disabled, in real output pixels, 1:1.
  // That is not cosmetic: at any other scale a regular field beats against the
  // phone's 0.7955 minification -- the ST-008 moire, measured at 8.14 levels.
  // Covering the full output makes this simpler than it was, since there is no
  // longer a panel rect to recover from two different coordinate spaces.
  //
  // It is fixed to the GLASS: it does not rotate with the orientation, and a
  // Vignette now darkens the corners of the SCREEN rather than of the page,
  // which is what a vignette physically is.
  // THE 2026-08-22 DOCTRINE SPLIT decides what texture the glass gets:
  // SCANLINES in dark mode (the CRT half), LETTERPRESS -- drawn above, in
  // panel space -- in light mode (the paper half). While either is active the
  // grain pass is SKIPPED: the doctrine replaces it, not layers over it. The
  // grain machinery stays compiled and its dials intact, so any mode whose
  // new dial is OFF falls back to exactly the old grain behavior -- which is
  // what keeps the desktop canary byte-identical (the desktop seeds both new
  // dials off) -- and A/B against the old look is one env var
  // (CROSSPOINT_SIM_SCANLINES=0 CROSSPOINT_SIM_GRAIN=100).
  //
  // The decision itself is `fields`, taken once above the letterpress draw.
  // These two names are kept because the warm-up's glass pick further down
  // reads one of them, and because "scanlinesActive" says what it means at the
  // three sites that ask.
  const bool scanlinesActive = fields.scanlines;
  const bool letterpressActive = fields.letterpress;

  // OUTPUT pixels per SOURCE-logical panel pixel -- the presentation scale
  // with the render scale divided out. Computed in ONE place because two
  // consumers now derive lattices from it: the scanlines' base pitch (one
  // scan line per source row) and the laid field's mm conversion. Two copies
  // of this arithmetic would be two chances for the raster and the wires to
  // disagree about what scale the panel presents at.
  auto outPxPerSourcePxAt = [&](int outW, int outH) -> float {
    const int srcRows = (isPortraitOrientation(orientation) ? activeWidth()
                                                            : activeHeight()) /
                        cp::renderScale();
    if (srcRows <= 0) return 0.0f;
    if (manualPlacement && panelRectH > 0)
      return static_cast<float>(panelRectH) / static_cast<float>(srcRows);
    int logW = 0, logH = 0;
    getLogicalPresentationSize(orientation, &logW, &logH);
    if (logW <= 0 || logH <= 0) return 0.0f;
    float s = SDL_min(static_cast<float>(outW) / logW,
                      static_cast<float>(outH) / logH);
    if (kLogicalPresentation == SDL_LOGICAL_PRESENTATION_INTEGER_SCALE &&
        s >= 1.0f)
      s = SDL_floorf(s);
    return s * static_cast<float>(logH) / static_cast<float>(srcRows);
  };

  if (scanlinesActive) {
    SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                     SDL_LOGICAL_PRESENTATION_DISABLED);
    int outW = 0, outH = 0;
    if (SDL_GetCurrentRenderOutputSize(sdl_renderer, &outW, &outH) &&
        outW > 0 && outH > 0) {
      // THE BASE PITCH IS THE PRESENTATION SCALE: one scan line per SOURCE row
      // (logical page rows, render scale divided out), so the raster carries
      // the page's own lattice and cannot beat against a second one. See
      // src/Scanlines.h for why a fixed ~500-line tube was rejected. The
      // owner's size dial then takes a simple MULTIPLE of that pitch
      // (scanlines::pitchFor, applied once below), which is phase-locked to
      // the same lattice and so inherits the same guarantee. The scale itself
      // comes from the shared lambda above.
      float pitch = outPxPerSourcePxAt(outW, outH);
      pitch = scanlines::pitchFor(pitch, SimulatorOverlay::scanlineSize.load());
      if (simtube::ensureScanlinesField(outW, outH, pitch)) {
        const SDL_FRect full = {0.0f, 0.0f, static_cast<float>(outW),
                                static_cast<float>(outH)};
        SDL_RenderTexture(sdl_renderer, simtube::scanField(), nullptr, &full);
      }
    }
    int logW = 0, logH = 0;
    getLogicalPresentationSize(orientation, &logW, &logH);
    SDL_SetRenderLogicalPresentation(sdl_renderer, logW, logH,
                                     kLogicalPresentation);
  } else if (simtube::scanField()) {
    simtube::destroyScanField();
  }

  // THE SHEET'S TOOTH -- the paper half of the letterpress, over the WHOLE
  // output, after the overlay, exactly where the grain draws: page, card, pad,
  // one sheet of paper (owner 2026-08-22, "make sure panel and paper actually
  // match visually, in color and texture with light mode"). The panel-space
  // letterpress field above carries no tooth any more, so the paper texture
  // inside and outside the page's rect is this one field and cannot seam.
  if (letterpressActive) {
    SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                     SDL_LOGICAL_PRESENTATION_DISABLED);
    int outW = 0, outH = 0;
    if (SDL_GetCurrentRenderOutputSize(sdl_renderer, &outW, &outH) &&
        outW > 0 && outH > 0 &&
        simsheet::ensureSheetField(outW, outH,
                                   outPxPerSourcePxAt(outW, outH))) {
      const SDL_FRect full = {0.0f, 0.0f, static_cast<float>(outW),
                              static_cast<float>(outH)};
      SDL_RenderTexture(sdl_renderer, simsheet::sheetField(), nullptr,
                        &full);
    }
    int logW = 0, logH = 0;
    getLogicalPresentationSize(orientation, &logW, &logH);
    SDL_SetRenderLogicalPresentation(sdl_renderer, logW, logH,
                                     kLogicalPresentation);
  } else if (simsheet::sheetField()) {
    simsheet::destroySheetField();
  }

  if (fields.grain) {
    SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                     SDL_LOGICAL_PRESENTATION_DISABLED);
    int outW = 0, outH = 0;
    if (SDL_GetCurrentRenderOutputSize(sdl_renderer, &outW, &outH) && outW > 0 &&
        outH > 0 && simtube::ensureGrainField(outW, outH)) {
      const SDL_FRect full = {0.0f, 0.0f, static_cast<float>(outW),
                              static_cast<float>(outH)};
      SDL_RenderTexture(sdl_renderer, simtube::grainField(), nullptr, &full);
    }
    int logW = 0, logH = 0;
    getLogicalPresentationSize(orientation, &logW, &logH);
    SDL_SetRenderLogicalPresentation(sdl_renderer, logW, logH,
                                     kLogicalPresentation);
  } else if (simtube::grainField()) {
    simtube::destroyGrainField();
  }

  // --- BZZT THONK: THE TUBE WARMING UP (roadmap D8's other half) ------------
  //
  // The draws are in src/SurfacePower.cpp; the call sits exactly where they did,
  // and that placement is not taste. AFTER THE GRAIN AND THE SCANLINES: the
  // scanline field is built from a READBACK of the composed frame and cached
  // against the framebuffer's seq, so a black or half-open frame reaching that
  // readback would bake an all-dark beam-current map and hold it until the next
  // page turn. Everything above therefore composes the finished page normally;
  // this decides how much of it the tube is currently able to show.
  simpower::compositeWarmUp(orientation, scanlinesActive);

  if (screenshotDue) {
    captureDueScreenshots();
  }
  // Opt-in present counter: the flash is a present that should not exist, and
  // counting presents is the only way to see it headlessly (a screenshot
  // deliberately overrides the hold, so it cannot photograph its own absence).
  if (presentLogWanted()) {
    {
      static int n = 0;
      // Sampled mean luminance of what is being presented, so a frame that is
      // mostly PAPER (a clear, a base pass) is distinguishable from a frame
      // that is a page. A count and a producer tag cannot tell those apart,
      // and "is there a flash-only draw" is exactly that question.
      double lum = 0.0;
      int samples = 0;
      {
        const std::lock_guard<std::mutex> lock(pixelBufMutex);
        const size_t live =
            static_cast<size_t>(activeWidth()) * activeHeight();
        for (size_t i = 0; i < live; i += 97) {
          const uint32_t px = pixelBuf[i];
          lum += 0.2126 * ((px >> 16) & 0xFF) + 0.7152 * ((px >> 8) & 0xFF) +
                 0.0722 * (px & 0xFF);
          samples++;
        }
      }
      SDL_Log("[present] #%d at %u ms, frame from %c, mean luma %.1f", ++n,
              SDL_GetTicks(), lastPixelWriter.load(),
              samples ? lum / samples : 0.0);
    }
  }
  // DIAGNOSIS ONLY (CROSSPOINT_SIM_LOG_SCREEN=1), no behaviour change.
  //
  // The [present] line above samples pixelBuf -- the PANEL FRAMEBUFFER -- so it
  // cannot see anything the composition adds: the field clear, the page-fade
  // alpha, the glow accumulator, the beam clip, or the overlay. A flash that
  // lives in any of those is invisible to it. This reads back what is actually
  // about to be shown, immediately before the present, and reports the mean
  // luminance of the whole output and of a band inside the page.
  if (screenLogWanted()) {
    {
      const uint64_t t0 = SDL_GetTicks();
      SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                       SDL_LOGICAL_PRESENTATION_DISABLED);
      SDL_Surface *shot = SDL_RenderReadPixels(sdl_renderer, nullptr);
      SDL_Surface *conv =
          shot ? SDL_ConvertSurface(shot, SDL_PIXELFORMAT_ARGB8888) : nullptr;
      if (conv) {
        const int w = conv->w, h = conv->h;
        auto bandMean = [&](int y0, int y1) {
          double sum = 0.0;
          int n2 = 0;
          for (int y = y0; y < y1; y += 7) {
            const uint32_t *row = reinterpret_cast<const uint32_t *>(
                static_cast<uint8_t *>(conv->pixels) +
                static_cast<size_t>(y) * conv->pitch);
            for (int x = 0; x < w; x += 7) {
              const uint32_t px = row[x];
              sum += 0.2126 * ((px >> 16) & 0xFF) + 0.7152 * ((px >> 8) & 0xFF) +
                     0.0722 * (px & 0xFF);
              n2++;
            }
          }
          return n2 ? sum / n2 : 0.0;
        };
        const int py0 = panelRectH > 0 ? panelRectY : 0;
        const int py1 = panelRectH > 0 ? panelRectY + panelRectH : h;
        static int m = 0;
        SDL_Log("[screen] #%d at %u ms, out %dx%d, whole %.2f, page %.2f, "
                "readback %u ms",
                ++m, (unsigned)t0, w, h, bandMean(0, h),
                bandMean(py0 < 0 ? 0 : py0, py1 > h ? h : py1),
                (unsigned)(SDL_GetTicks() - t0));
        // Optional: write the frames themselves. CROSSPOINT_SIM_SCREEN_DUMP is
        // a directory; dumping starts at CROSSPOINT_SIM_SCREEN_DUMP_AFTER_MS
        // and stops after CROSSPOINT_SIM_SCREEN_DUMP_COUNT frames, because a
        // frame is 13 MB and the question only needs the ones around a change.
        if (const char *dir = std::getenv("CROSSPOINT_SIM_SCREEN_DUMP")) {
          static int dumped = 0;
          const char *afterEnv = std::getenv("CROSSPOINT_SIM_SCREEN_DUMP_AFTER_MS");
          const char *countEnv = std::getenv("CROSSPOINT_SIM_SCREEN_DUMP_COUNT");
          const uint64_t after = afterEnv ? std::strtoull(afterEnv, nullptr, 10) : 0;
          const int cap = countEnv ? std::atoi(countEnv) : 40;
          if (t0 >= after && dumped < cap) {
            char path[1024];
            SDL_snprintf(path, sizeof(path), "%s/screen_%03d_%06u.bmp", dir,
                         dumped, (unsigned)t0);
            SDL_SaveBMP(conv, path);
            dumped++;
          }
        }
        SDL_DestroySurface(conv);
      }
      if (shot) SDL_DestroySurface(shot);
      int logW2 = 0, logH2 = 0;
      getLogicalPresentationSize(orientation, &logW2, &logH2);
      SDL_SetRenderLogicalPresentation(sdl_renderer, logW2, logH2,
                                       kLogicalPresentation);
    }
  }
  const uint64_t flipT0 = timingLogWanted() ? SDL_GetTicksNS() : 0;
  SDL_RenderPresent(sdl_renderer);
  if (timingLogWanted()) {
    const uint64_t end = SDL_GetTicksNS();
    timingFrame.flipMs = static_cast<double>(end - flipT0) / 1.0e6;
    const double total =
        static_cast<double>(end - timingFrame.startNs) / 1.0e6;
    // BUILD / cache / off per pass, because a duration alone cannot say which
    // of the three a 0.0 ms pass was, and "off" and "served from cache" are
    // different answers to "what does a page turn cost".
    auto tag = [](const PassTiming &p) {
      return p.built ? "BUILD" : (p.served ? "cache" : "off");
    };
    static int n = 0;
    SDL_Log("[timing] #%d total %.2f ms | upload %s %.2f | accum %s %.2f | "
            "glass %s %.2f | panel %s %.2f | sheet %s %.2f | "
            "scanlines %s %.2f | grain %s %.2f | readback %s %.2f | "
            "flip %.2f",
            ++n, total, tag(timingFrame.upload), timingFrame.upload.ms,
            tag(timingFrame.accum), timingFrame.accum.ms,
            tag(timingFrame.glass), timingFrame.glass.ms,
            tag(timingFrame.letterpress),
            timingFrame.letterpress.ms, tag(timingFrame.sheet),
            timingFrame.sheet.ms, tag(timingFrame.scanlines),
            timingFrame.scanlines.ms, tag(timingFrame.grain),
            timingFrame.grain.ms, timingFrame.readback ? "yes" : "-",
            timingFrame.readbackMs, timingFrame.flipMs);
  }
}

// The POWER-OFF COLLAPSING DOT and the POWER-ON WARM-UP are in
// src/SurfacePower.cpp (moved 2026-08-25). SimulatorOverlay::stepPowerOffCollapse()
// is defined there and is still stepped from HalGPIO::startDeepSleep's terminal
// loop -- the one place that can draw after the app is asleep without delaying
// it, and the reason the collapse is not a present.

bool HalDisplay::shouldQuit() const { return quitRequested.load(); }

void HalDisplay::deepSleep() {
  if (powerLogWanted())
    SDL_Log("[power] sleep entry: beamMs=%.0f beamStartedAt=%llu sweeping=%d "
            "trailMs=%.0f accumLastAddMs=%llu pendingPresent=%d holdUntil=%llu "
            "writer=%c",
            (double)beamPaintMs.load(), (unsigned long long)beamStartedAt,
            (int)(beamPaintMs.load() > 0.0f && beamStartedAt != 0),
            (double)glowTrailMs.load(), (unsigned long long)accumLastAddMs,
            (int)pendingPresent.load(),
            (unsigned long long)presentHoldUntil.load(), lastPixelWriter.load());
  // Flush any held base pass first. Sleep is the one caller with no "next
  // pass": the loop stops here, so a frame still inside the hold window would
  // be the frame nobody ever sees -- and it is the sleep screen. When the
  // collapse is going to run there is no frame to flush and presentIfNeeded's
  // veto (below displaySleeping) drops it instead; the ordering here is what
  // makes that work, since the flag is set before the present.
  presentHoldUntil.store(0);
  // SETTLE EVERY PRESENT FROM HERE ON, not just the one below. The frames
  // presented after this call are the last ones: presents stop shortly after
  // the sleep loop starts, so a beam mid-sweep would freeze half-composited on
  // the glass for the whole sleep and past the wake until the firmware's first
  // post-wake render. That was the owner's corrupted band (2026-08-21;
  // reproduced as a top band of the sleep screen double-exposed over the
  // previous page, byte-identical from sleep entry to 1.2 s past the wake
  // tap). A one-shot settle here is NOT enough -- the sleep screen's AA
  // compose lands on the render task tens of ms later and its present started
  // a fresh sweep -- so the flag makes presentIfNeeded settle for as long as
  // the sleep lasts. Completing the beam and retiring the glow is also the
  // physics: by the time the tube is dark, the sweep has finished and the
  // phosphor has decayed. Desktop builds seed both dials to 0, so this is a
  // no-op there and the canary is unchanged.
  displaySleeping.store(true);
  presentIfNeeded();
  if (powerLogWanted())
    SDL_Log("[power] sleep screen %s; transients settle while sleeping",
            powerLogSleepVetoSaid ? "dropped" : "flushed");
}

uint8_t *HalDisplay::getFrameBuffer() const {
  if (frameBufferLent) {
    return nullptr;
  }
  return frameBufferStorage.data();
}

uint8_t *HalDisplay::lendFrameBufferStorage(uint32_t *sizeOut) {
  if (sizeOut) {
    *sizeOut = frameBufferLent ? 0 : activeBufferSize();
  }
  if (frameBufferLent) {
    return nullptr;
  }
  frameBufferLent = true;
  return frameBufferStorage.data();
}

void HalDisplay::returnFrameBufferStorage() {
  if (!frameBufferLent) {
    return;
  }
  frameBufferStorage.fill(0xFF);
  frameBufferLent = false;
}

void HalDisplay::copyGrayscaleBuffers(const uint8_t *lsbBuffer,
                                      const uint8_t *msbBuffer) {
  copyGrayscaleLsbBuffers(lsbBuffer);
  copyGrayscaleMsbBuffers(msbBuffer);
}
void HalDisplay::displayGrayscaleBase(RefreshMode fallback,
                                      bool turnOffScreen) {
  displayBuffer(fallback, turnOffScreen);
}
void HalDisplay::preconditionGrayscale() {}
void HalDisplay::preconditionGrayscale(uint16_t, uint16_t, uint16_t, uint16_t) {
}
void HalDisplay::copyGrayscaleLsbBuffers(const uint8_t *lsbBuffer) {
  // The whole-frame AA fallback (no strip support / OOM) reaches the planes
  // through here instead, and needs the same extension or it flashes on every
  // page while the strip path does not.
  if (!presentFlashWanted() && presentHoldUntil.load() != 0)
    presentHoldUntil.store(SDL_GetTicks() + kPresentHoldExtendedMs);
  copyPlane(grayscalePreviewState.lsbPlane, lsbBuffer,
            grayscalePreviewState.lsbValid);
}
void HalDisplay::copyGrayscaleMsbBuffers(const uint8_t *msbBuffer) {
  copyPlane(grayscalePreviewState.msbPlane, msbBuffer,
            grayscalePreviewState.msbValid);
}
void HalDisplay::cleanupGrayscaleBuffers(const uint8_t *bwBuffer) {
  if (bwBuffer) {
    snapshotBwBase(bwBuffer);
  } else {
    grayscalePreviewState.bwBaseValid = false;
    grayscalePreviewState.bwBase.fill(0);
    clearGrayscalePlanes();
  }
}
void HalDisplay::displayGrayBuffer(bool, const unsigned char *, bool) {
  composeGrayscalePreview();
}

void HalDisplay::writeGrayscalePlaneStrip(bool lsbPlane, const uint8_t *rows,
                                          uint16_t yStart, uint16_t numRows) {
  if (!rows || numRows == 0 || yStart >= activeHeight()) {
    return;
  }

  // A compose is now guaranteed: hold the 1-bit frame until it lands. Only
  // extends a hold that is already armed, so a stray plane write on a screen
  // that never painted cannot stall anything.
  if (!presentFlashWanted() && presentHoldUntil.load() != 0)
    presentHoldUntil.store(SDL_GetTicks() + kPresentHoldExtendedMs);

  const uint16_t rowsToCopy =
      (yStart + numRows > activeHeight()) ? (activeHeight() - yStart) : numRows;
  const size_t offset = static_cast<size_t>(yStart) * activeWidthBytes();
  const size_t byteCount =
      static_cast<size_t>(rowsToCopy) * activeWidthBytes();
  auto &plane = lsbPlane ? grayscalePreviewState.lsbPlane
                         : grayscalePreviewState.msbPlane;
  memcpy(plane.data() + offset, rows, byteCount);
  if (lsbPlane) {
    grayscalePreviewState.lsbValid = true;
  } else {
    grayscalePreviewState.msbValid = true;
  }
}
bool HalDisplay::supportsStripGrayscale() const { return true; }

uint16_t HalDisplay::getDisplayWidth() const { return activeWidth(); }
uint16_t HalDisplay::getDisplayHeight() const { return activeHeight(); }
uint16_t HalDisplay::getDisplayWidthBytes() const {
  return activeWidthBytes();
}
uint32_t HalDisplay::getBufferSize() const { return activeBufferSize(); }

HalDisplay display;
