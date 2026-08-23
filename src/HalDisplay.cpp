#include "HalDisplay.h"
#include "SimulatorRebootResets.h"

#include <GfxRenderer.h>
#include <Logging.h>
#include <SDL3/SDL.h>

#include "CornerDefocus.h"
#include "GrayscalePreview.h"
#include "LaidStructure.h"
#include "Letterpress.h"
#include "LightInkPalette.h"
#include "PaperDefects.h"
#include "PageFade.h"
#include "PanelPalette.h"
#include "PhosphorGrain.h"
#include "Srgb.h"
#include "PowerOffCollapse.h"
#include "Scanlines.h"
#include "ShowThrough.h"
#include "SimulatorDeviceTruth.h"
#include "SimulatorOverlay.h"

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
// The PREVIOUS panel image, held so it can be faded out on top of the new one.
// Null whenever the glow is off, which is the desktop default and costs nothing.
static SDL_Texture *ghostTexture = nullptr;
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

// Whether ghostTexture has been written since the glow was last turned on. The
// texture outlives ghostPixels, so "we have a texture" is not the same question
// as "it holds a picture" -- see where this is read.
static bool ghostHasPicture = false;
// The tint a two-layer phosphor's trail decays toward, packed 0x00RRGGBB, or
// kNoGlowTail when the trail simply dims. See setPanelGlowTail.
static constexpr uint32_t kNoGlowTail = 0xFFFFFFFFu;
static std::atomic<uint32_t> glowTailTint{kNoGlowTail};
// When the trail's hue handover completes, ms after a deposit -- the moment
// everything faster than the surviving phosphor has died. 0 = unknown, and the
// recolor ramps across the whole trail as it always did.
static std::atomic<float> glowTailOnsetMs{0.0f};
// When the ghost was captured, on the SDL_GetTicks clock. 0 = no ghost.
static Uint64 ghostStartedAt = 0;
// The pixels the ghost was captured from -- kept because SDL_UpdateTexture
// overwrites `texture` in place, so the old picture has to be copied BEFORE the
// new one lands, and a pixel copy is cheaper and simpler than a render target.
static std::vector<uint32_t> ghostPixels;
// The pixelBufSeq the ghost copy was taken at.
static uint64_t ghostSeq = 0;
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
static std::atomic<bool> pendingPresent{false};
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
static bool timingLogWanted() {
  static const bool wanted = [] {
    const char *e = std::getenv("CROSSPOINT_SIM_LOG_TIMING");
    return e && e[0] == '1';
  }();
  return wanted;
}

// One pass's verdict for this present. A cache HIT is as interesting as a
// build: "the sheet rebuilt twice this page" and "the sheet was served" are
// the two answers the field-keying work exists to distinguish, and a bare
// duration cannot tell them apart.
struct PassTiming {
  bool built = false;   // the field was regenerated this present
  bool served = false;  // a cached field was drawn
  double ms = 0.0;      // wall time of the regeneration, 0 when served
};
struct PresentTiming {
  PassTiming letterpress, sheet, grain, scanlines;
  bool readback = false;  // SDL_RenderReadPixels of the whole output
  double readbackMs = 0.0;
  uint64_t startNs = 0;
  double flipMs = 0.0;  // SDL_RenderPresent itself
};
// Main thread only: every writer is either presentIfNeeded or an ensure*()
// that only presentIfNeeded calls.
static PresentTiming timingFrame;

// One-shot latches so the first update/refresh/present AFTER an in-process
// reboot announce themselves. Armed by the reboot Registrar below; checked
// (a plain bool) before any env read, so the off cost is nil.
static bool powerLogFirstRefresh = false;
static bool powerLogFirstPresent = false;

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
bool frameBufferLent = false;

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

void renderBwPixels(const uint8_t *fb) {
  const std::lock_guard<std::mutex> lock(pixelBufMutex);
  pixelBufSeq++;
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
  pendingPresent.store(true);
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

void composeGrayscalePreview() {
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
    pendingPresent.store(true);
    return;
  }
  pixelBufSeq++;
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
  if (const char *e = std::getenv("CROSSPOINT_SIM_LOG_PRESENTS"))
    if (e[0] == '1')
      SDL_Log("[compose] %llu ms for %dx%d",
              (unsigned long long)(SDL_GetTicks() - composeStart),
              HalDisplay::activeWidth(), HalDisplay::activeHeight());
  lastPixelWriter.store('G');
  // The composed frame WAITS OUT the flash. Holding it here is the whole
  // mechanism: the 1-bit frame is already on screen and the idle repaints keep
  // re-presenting it, so suppressing this one is what gives the flash length.
  const uint64_t flashUntil = presentFlashUntil.load();
  if (flashUntil <= SDL_GetTicks()) presentHoldUntil.store(0);
  pendingPresent.store(true);
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
void reconvertLastFrame() {
  if (!grayscalePreviewState.bwBaseValid)
    return; // nothing presented yet; the first real render reads the new flag
  if (grayscalePreviewState.lsbValid || grayscalePreviewState.msbValid)
    composeGrayscalePreview();
  else
    renderBwPixels(grayscalePreviewState.bwBase.data());
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
void requestPresent() { pendingPresent.store(true); }
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
  pendingPresent.store(true);
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
  pendingPresent.store(true);
}

void notePageInteraction() {
  if (pageFadeMs.load() <= 0.0f) return;
  lastInteractionMs.store(SDL_GetTicks());
  // Come back at once rather than at the next page: the whole point is that
  // touching the device re-energises what you were reading.
  pendingPresent.store(true);
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
  pendingPresent.store(true);
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
  pendingPresent.store(true);
}

void setLetterpress(int strengthPercent) {
  strengthPercent = envPercentOr("CROSSPOINT_SIM_LETTERPRESS", strengthPercent);
  const int s = letterpress::clampStrength(strengthPercent);
  if (letterpressStrength.exchange(s) == s) return;
  pendingPresent.store(true);
}

void setPaperTooth(int percentOfReference) {
  percentOfReference =
      envPercentOr("CROSSPOINT_SIM_PAPER_TOOTH", percentOfReference);
  int pct = percentOfReference;
  if (pct < 0) pct = 0;
  if (pct > 400) pct = 400;
  if (paperToothPct.exchange(pct) == pct) return;
  pendingPresent.store(true);
}

void setPaperFormation(int depthPercent) {
  depthPercent = envPercentOr("CROSSPOINT_SIM_PAPER_FORMATION", depthPercent);
  const int pct = static_cast<int>(
      letterpress::clampFormationDepth(static_cast<float>(depthPercent) /
                                       100.0f) * 100.0f + 0.5f);
  if (paperFormationPct.exchange(pct) == pct) return;
  pendingPresent.store(true);
}

void setPaperDefects(int dialPercent) {
  dialPercent = envPercentOr("CROSSPOINT_SIM_PAPER_DEFECTS", dialPercent);
  const int pct = paperdefects::clampDial(dialPercent);
  if (paperDefectsPct.exchange(pct) == pct) return;
  pendingPresent.store(true);
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
  pendingPresent.store(true);
}

void setLaidLines(int strengthPercent) {
  strengthPercent = envPercentOr("CROSSPOINT_SIM_LAIDLINES", strengthPercent);
  const int pct = laidstructure::clampStrength(strengthPercent);
  if (laidLinesStrength.exchange(pct) == pct) return;
  pendingPresent.store(true);
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
  pendingPresent.store(true);
}

void setPressDeboss(int percentOfStandard) {
  percentOfStandard =
      envPercentOr("CROSSPOINT_SIM_PRESS_DEBOSS", percentOfStandard);
  const int pct = clampPartPercent(percentOfStandard);
  if (pressDebossPct.exchange(pct) == pct) return;
  pendingPresent.store(true);
}

void setPressPressure(int percentOfStandard) {
  percentOfStandard =
      envPercentOr("CROSSPOINT_SIM_PRESS_PRESSURE", percentOfStandard);
  const int pct = clampPartPercent(percentOfStandard);
  if (pressPressurePct.exchange(pct) == pct) return;
  pendingPresent.store(true);
}

void setScanlines(int intensityPercent) {
  intensityPercent = envPercentOr("CROSSPOINT_SIM_SCANLINES", intensityPercent);
  const int s = scanlines::clampIntensity(intensityPercent);
  if (scanlinesIntensity.exchange(s) == s) return;
  pendingPresent.store(true);
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
  pendingPresent.store(true);
}

void setScanlineBloom(int percentOfStandard) {
  percentOfStandard =
      envPercentOr("CROSSPOINT_SIM_SCANLINE_BLOOM", percentOfStandard);
  const int s = scanlines::clampBloom(percentOfStandard);
  if (scanlineBloom.exchange(s) == s) return;
  pendingPresent.store(true);
}

void setShowThrough(int percentOfStandard) {
  percentOfStandard =
      envPercentOr("CROSSPOINT_SIM_SHOW_THROUGH", percentOfStandard);
  const int s = showthrough::clampStrength(percentOfStandard);
  if (showThroughStrength.exchange(s) == s) return;
  pendingPresent.store(true);
}

void setCornerDefocus(int percentOfStandard) {
  percentOfStandard =
      envPercentOr("CROSSPOINT_SIM_CORNER_DEFOCUS", percentOfStandard);
  const int s = cornerdefocus::clampStrength(percentOfStandard);
  if (cornerDefocusStrength.exchange(s) == s) return;
  pendingPresent.store(true);
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
  pendingPresent.store(true);
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

void HalDisplay::begin() {
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
  // What stays hand-written is the PAGE, which is not a dial: the palette, the
  // emission flag, the glow and the polarity are one coherent choice -- the app
  // ships CRT White -- rather than 23 independent numbers.
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
    SimulatorOverlay::setPanelPalette(
        true, panelpalette::presetPalette(panelpalette::kPresetWhiteCrt, true).ink,
        panelpalette::presetPalette(panelpalette::kPresetWhiteCrt, true).paper);
    SimulatorOverlay::setPanelEmissive(true);
    SimulatorOverlay::setPanelGlow(
        panelpalette::trailMsForPreset(panelpalette::kPresetWhiteCrt));
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
static SDL_Texture *accumTexture = nullptr;
static uint64_t accumLastFadeMs = 0;
static uint64_t accumLastAddMs = 0;

// The [power] boundary station. Runs immediately before the in-process reboot's
// longjmp (desktop execvp resets everything for free and never gets here). It
// only REPORTS: deepSleep() below settles the beam and the glow on the way
// down, so anything nonzero here is state that would have crossed into the next
// boot and is worth a line in the log. The one-shot latches arm the
// first-refresh / first-present stations for the boot that follows.
const simreset::Registrar gPowerLogBoundary{[] {
  powerLogFirstRefresh = true;
  powerLogFirstPresent = true;
  // The boot on the other side of the jump is awake, whatever it renders.
  displaySleeping.store(false);
  if (!powerLogWanted()) return;
  SDL_Log("[power] reboot boundary: beamStartedAt=%llu ghostStartedAt=%llu "
          "accumLastAddMs=%llu pendingPresent=%d holdUntil=%llu flashUntil=%llu",
          (unsigned long long)beamStartedAt, (unsigned long long)ghostStartedAt,
          (unsigned long long)accumLastAddMs, (int)pendingPresent.load(),
          (unsigned long long)presentHoldUntil.load(),
          (unsigned long long)presentFlashUntil.load());
}};

static void ensureAccumTexture() {
  if (accumTexture) return;
  accumTexture = SDL_CreateTexture(sdl_renderer, SDL_PIXELFORMAT_ARGB8888,
                                   SDL_TEXTUREACCESS_TARGET, HalDisplay::activeWidth(),
                                   HalDisplay::activeHeight());
  if (!accumTexture) {
    LOG_ERR("DISP", "glow: no accumulator texture (%s)", SDL_GetError());
    return;
  }
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

static void ensureGhostTexture() {
  if (ghostTexture || !sdl_renderer)
    return;
  ghostTexture = SDL_CreateTexture(sdl_renderer, SDL_PIXELFORMAT_ARGB8888,
                                   SDL_TEXTUREACCESS_STREAMING,
                                   HalDisplay::activeWidth(),
                                   HalDisplay::activeHeight());
  if (!ghostTexture) {
    LOG_ERR("DISP", "glow: could not create the ghost texture (%s)",
            SDL_GetError());
    return;
  }
  SDL_SetTextureBlendMode(ghostTexture, SDL_BLENDMODE_BLEND);
}

// The INTENSITY copy of the ghost, for the accumulator's deposit. The deposit
// used to be the page's own pixels -- green ink on black -- and the tail
// recolor is a color MULTIPLY, which can only remove channels: green times an
// orange tail is olive, never orange, so a mixed page's fade could never
// change hue toward the surviving phosphor (owner report 2026-08-21, P46+P33).
// Depositing intensity (max(r,g,b), white-on-black) lets the present-time mod
// paint the trail ANY color: ink at first, the tail by the handover. The
// accumulator is only ever composed on a DARK ground (see the `!darkGround ->
// accumLive = false` gate in presentIfNeeded), where every level is the ink
// scaled toward black, so intensity x ink reconstructs the old picture.
static SDL_Texture *ghostIntensityTexture = nullptr;
static void ensureGhostIntensityTexture() {
  if (ghostIntensityTexture || !sdl_renderer)
    return;
  ghostIntensityTexture = SDL_CreateTexture(
      sdl_renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STREAMING,
      HalDisplay::activeWidth(), HalDisplay::activeHeight());
  if (!ghostIntensityTexture)
    LOG_ERR("DISP", "glow: could not create the intensity ghost (%s)",
            SDL_GetError());
}

// THE GRAIN FIELD, generated at the OUTPUT SIZE and drawn 1:1 over the whole
// app surface -- panel, pad, bezel and letterbox margins alike.
//
// That "1:1" is the whole reason this is a present-time pass and not something
// baked into the 1bpp->ARGB conversion. The panel is MINIFIED on a phone
// (0.7955 on an iPhone Air at 3x); a regular field written into the framebuffer
// beats against that resample, measured at 8.14 levels for the selection dither
// (ST-008). A field the size of the presented rect is never resampled at all.
//
// Regenerated only when the rect or either dial changes -- so a page turn costs
// one textured quad, not 2.4M hash evaluations. It is a property of the glass:
// it must NOT be re-rolled per frame, or a still page crawls.
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

static SDL_Texture *grainTexture = nullptr;
static int grainTexW = 0, grainTexH = 0;
static uint32_t grainTexSeed = 0;
static int grainTexStrength = -1, grainTexCoverage = -1;
static int grainTexCells = -1, grainTexDepth = -1;
static int grainTexAmplitude = -1;

static void destroyGrainTexture() {
  if (!grainTexture) return;
  SDL_DestroyTexture(grainTexture);
  grainTexture = nullptr;
  grainTexW = grainTexH = 0;
  grainTexStrength = grainTexCoverage = -1;
  grainTexCells = grainTexDepth = -1;
  grainTexAmplitude = -1;
  grainTexSeed = 0;
}

// sRGB relative luminance of a palette tone -- the same weights the contrast
// floor and the grain's budget use. Defined HERE, above its first caller,
// because the previous arrangement put it 78 lines below and the first caller
// therefore carried a byte-identical lambda copy of it. The curve is
// src/Srgb.h's; this is only the WCAG weighting over it.
static float srgbLumOf(const unsigned char c[3]) {
  return srgb::relativeLuminance(c);
}

// True when there is a field ready to draw over a w x h rect.
static bool ensureGrainTexture(int w, int h) {
  const int strength = SimulatorOverlay::grainStrength.load();
  const int coverage = SimulatorOverlay::grainCoverage.load();
  const int cells = SimulatorOverlay::grainMottleCells.load();
  const int depthPct = SimulatorOverlay::grainMottleDepthPct.load();
  const uint32_t seed = grainSeed();
  // WHAT THIS PAGE CAN AFFORD. Measured off the LIVE palette, so the field
  // follows a polarity flip and a palette change without anything else being
  // told. sRGB relative luminance, the same weights the contrast floor uses.
  const PanelPalette live = livePanelPalette(display.isInverted());
  const float inkLum = srgbLumOf(live.ink);
  const float paperLum = srgbLumOf(live.paper);
  const float amplitude = phosphorgrain::amplitudeScaleFor(inkLum, paperLum);
  const float budget = phosphorgrain::darkeningBudget(inkLum, paperLum);
  const int amplitudeKey = static_cast<int>(amplitude * 1000.0f + 0.5f);
  if (strength == phosphorgrain::kStrengthOff || w <= 0 || h <= 0 ||
      !sdl_renderer) {
    destroyGrainTexture();
    return false;
  }
  if (grainTexture && grainTexW == w && grainTexH == h &&
      grainTexStrength == strength && grainTexCoverage == coverage &&
      grainTexCells == cells && grainTexDepth == depthPct &&
      grainTexSeed == seed && grainTexAmplitude == amplitudeKey) {
    if (timingLogWanted()) timingFrame.grain.served = true;
    return true;
  }
  const uint64_t grainT0 = timingLogWanted() ? SDL_GetTicksNS() : 0;
  destroyGrainTexture();

  grainTexture = SDL_CreateTexture(sdl_renderer, SDL_PIXELFORMAT_ARGB8888,
                                   SDL_TEXTUREACCESS_STATIC, w, h);
  if (!grainTexture) {
    LOG_ERR("DISP", "grain: no field texture (%s)", SDL_GetError());
    return false;
  }
  const phosphorgrain::Params params{
      strength, phosphorgrain::clampCoverage(coverage), seed,
      phosphorgrain::clampMottleCells(cells),
      static_cast<float>(depthPct) / 100.0f, amplitude, budget};
  std::vector<uint32_t> field(static_cast<size_t>(w) * h);
  for (int y = 0; y < h; ++y) {
    uint32_t *row = field.data() + static_cast<size_t>(y) * w;
    for (int x = 0; x < w; ++x) {
      const uint32_t m = phosphorgrain::multiplierAt(params, x, y, w, h);
      // Achromatic: grain is a coverage deficit, and a thin patch of phosphor
      // emits LESS of its own color, not a different one. Tinting it would be
      // inventing a second phosphor.
      row[x] = 0xFF000000u | (m << 16) | (m << 8) | m;
    }
  }
  if (!SDL_UpdateTexture(grainTexture, nullptr, field.data(),
                         static_cast<int>(w * sizeof(uint32_t)))) {
    LOG_ERR("DISP", "grain: could not upload the field (%s)", SDL_GetError());
    destroyGrainTexture();
    return false;
  }
  // MODULATE: dst = dst * src. See PhosphorGrain.h for why it can only darken.
  SDL_SetTextureBlendMode(grainTexture, SDL_BLENDMODE_MOD);
  // Drawn 1:1, so the filter never runs -- pinned to NEAREST anyway so a
  // half-pixel rect can never smear the field into a gray wash.
  SDL_SetTextureScaleMode(grainTexture, SDL_SCALEMODE_NEAREST);
  grainTexW = w;
  grainTexH = h;
  grainTexStrength = strength;
  grainTexCoverage = coverage;
  grainTexCells = cells;
  grainTexDepth = depthPct;
  grainTexSeed = seed;
  grainTexAmplitude = amplitudeKey;
  if (timingLogWanted()) {
    timingFrame.grain.built = true;
    timingFrame.grain.ms =
        static_cast<double>(SDL_GetTicksNS() - grainT0) / 1.0e6;
  }
  if (const char *e = std::getenv("CROSSPOINT_SIM_LOG_PRESENTS"))
    if (e[0] == '1')
      SDL_Log("[grain] field %dx%d strength %d coverage %d mottle %d x %.2f "
              "seed %u amplitude %.2fx",
              w, h, strength, coverage, cells,
              static_cast<double>(depthPct) / 100.0, seed,
              static_cast<double>(amplitude));
  return true;
}

// --- THE PAGE'S OWN SEED ---------------------------------------------------
//
// A SHEET IS NOT A SCREEN. grainSeed() is deliberately re-rolled every launch
// (and across the iOS in-process reboot) because two runs of the app are two
// tubes -- and that is exactly wrong for paper. A book is not re-printed when
// you close it, so a page you turn back to must be the same sheet, including
// after a relaunch.
//
// So the LIGHT page's two fields seed from the page's IDENTITY, published by
// every reader activity through HalGPIO::publishReaderPageIdentity. NOTE what
// is NOT in the hash: grainSeed(). Mixing it in would leave the field differing
// per page AND per launch, which looks like the feature and is not it.
//
// No identity published (a cold boot into a menu, Settings, anything that is
// not a reader) falls back to the launch seed, exactly as before this existed.
// Nothing clears the latch, so walking out of a book keeps the last page's
// paper rather than snapping to a launch seed -- see HalGPIO.h.
//
// This is provable because in light mode with letterpress on the grain pass is
// SKIPPED (see presentIfNeeded), so a light page is fully determined by this
// number and nothing else random survives. docs/paper-defects.md.
static uint32_t pageSheetSeed() {
  uint64_t bookKey = 0;
  int spine = 0, page = 0;
  if (!SimulatorOverlay::readerPageIdentity(bookKey, spine, page)) {
    // SAY SO ONCE. This branch is legitimate for pre-channel firmware, and
    // that is exactly why it shipped as a bug: build 127 was archived against
    // a firmware checkout one commit behind the publisher, so this fired on
    // every page and the whole app -- home screen, every page of every book --
    // wore one sheet. Nothing in any log said so, and the picture is subtle
    // enough that "the flaws are not changing" was the only symptom. A build
    // that never sees an identity now announces it the first time.
    static bool warned = false;
    if (!warned) {
      warned = true;
      SDL_Log("[paper] no page identity published -- every sheet will use the "
              "launch seed. The firmware does not call "
              "publishReaderPageIdentity; per-page paper is INACTIVE.");
    }
    return grainSeed() ^ 0x50524553u;  // 'PRES', the pre-identity behaviour
  }
  return phosphorgrain::hash3(static_cast<uint32_t>(bookKey & 0xFFFFFFFFu),
                              static_cast<uint32_t>(bookKey >> 32) ^
                                  static_cast<uint32_t>(spine),
                              static_cast<uint32_t>(page));
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
  lightink::paperDrifted(pal.paper, pageSheetSeed(), driftPct, out.paper);
  return out;
}
}  // namespace

// THE PAGE'S INKNESS, hoisted out of ensureLetterpressTexture so the SHEET pass
// can mask its defects against the glyphs (a mark never sits on a letter: ink
// is printed ON the paper). It was a function-local vector in PANEL space; the
// sheet is built in OUTPUT space, so the sheet pass also needs the inverse of
// the presentation transform -- outputToPanel(), below.
//
// Published rather than recomputed because the two passes run in the SAME
// present, panel first: ensureLetterpressTexture writes it, ensureSheetTooth
// Texture reads whatever is current. That snapshot is keyed to pixelBufSeq,
// which increments TWICE per displayed page (the 1-bit pass, then the AA
// compose), so the sheet masks against the first pass's glyph shapes while the
// compose paints slightly softer edges -- a sub-pixel difference at glyph
// boundaries, under a mask that is already a fade. Keying the sheet on the seq
// instead would regenerate a ~3.4 Mpx field twice per page turn, which is the
// cost this arrangement exists to avoid.
static std::vector<uint8_t> sheetInkness;
static int sheetInknessW = 0, sheetInknessH = 0;

// --- SHOW-THROUGH: THE OTHER SIDE OF THE LEAF ------------------------------
//
// Two blurred, downsampled copies of the inkness plane above: the leaf being
// read (`rectoVerso`) and the leaf before it (`versoMap`, which is what shows
// through). The promotion happens on the PAGE SEED, not on pixelBufSeq: the
// seq increments twice per displayed page (1-bit pass, then the AA compose),
// and promoting on it would put the SAME page behind itself half the time.
//
// THE SOURCE IS THE INKNESS PLANE, NOT ghostPixels. The roadmap proposed
// ghostPixels -- a whole previous framebuffer that HalDisplay already keeps --
// and it is the wrong source on three counts: it is only maintained while the
// phosphor trail or the beam is on (both dark-mode ideas, both off on a paper
// page), it is ARGB that would have to be re-projected onto the palette's
// ink/paper axis to be useful, and it is a copy of the previous FRAME rather
// than of the previous PAGE. The letterpress pass already computes exactly the
// quantity wanted, per page, in light mode, for free.
//
// WHAT SHOWS THROUGH PAGE N IS PAGE N+1, AND THIS IS PAGE N-1. Stated in the
// code as well as the doc because it is the one dishonesty in the feature: a
// show-through is never legible, and what the eye reads off it -- the measure,
// the line grid, the paragraph rag, the chapter opening's white -- is right for
// either neighbour. Rendering N+1 truthfully would cost a second pagination and
// a second render per page turn on a device whose whole design is to render
// rarely. docs/show-through.md, section "the honesty problem".
static std::vector<uint8_t> versoMap;
static std::vector<uint8_t> rectoVerso;
static int versoMapW = 0, versoMapH = 0;
static uint32_t versoSeed = 0;
static bool versoSeeded = false;
// Bumped on every promotion, so the sheet field's cache key can see that the
// leaf behind this one changed even when nothing else did.
static uint64_t versoGeneration = 0;

// The two maps are per-LAUNCH state about a book, not about a tube, so they do
// NOT survive the iOS in-process reboot: a wake starts a fresh session and the
// first page it draws has nothing behind it yet. Same contract the grain seed
// has, for the opposite reason.
const simreset::Registrar gVersoReset{[] {
  versoMap.clear();
  rectoVerso.clear();
  versoMapW = versoMapH = 0;
  versoSeed = 0;
  versoSeeded = false;
  versoGeneration = 0;
}};

// Promote and rebuild, from the inkness plane the letterpress pass just made.
// A no-op when the dial is off, so nothing is paid for a feature nobody asked
// for -- and the maps are dropped, because a 26 kB pair kept alive for a
// disabled dial is state that can go stale.
static void updateVersoMaps(const std::vector<uint8_t> &inkness, int w, int h,
                            uint32_t seed) {
  if (SimulatorOverlay::showThroughStrength.load() <= showthrough::kStrengthOff) {
    if (!versoMap.empty()) {
      versoMap.clear();
      rectoVerso.clear();
      versoMapW = versoMapH = 0;
      versoSeeded = false;
    }
    return;
  }
  const int mw = showthrough::mapDim(w), mh = showthrough::mapDim(h);
  if (mw <= 0 || mh <= 0) return;
  if (versoMapW != mw || versoMapH != mh) {
    versoMapW = mw;
    versoMapH = mh;
    versoMap.assign(static_cast<size_t>(mw) * mh, 0);
    rectoVerso.assign(static_cast<size_t>(mw) * mh, 0);
    versoSeeded = false;
  }
  if (!versoSeeded || seed != versoSeed) {
    // A NEW LEAF: what was the recto is now the back of the sheet in hand.
    versoMap = rectoVerso;
    versoSeed = seed;
    versoSeeded = true;
    ++versoGeneration;
  }
  showthrough::downsample(inkness.data(), w, h, rectoVerso.data());
  static std::vector<uint8_t> scratch;
  scratch.resize(rectoVerso.size());
  showthrough::blur(rectoVerso.data(), mw, mh, scratch.data());
}

// --- LETTERPRESS (light mode) ----------------------------------------------
//
// A MOD texture at FRAMEBUFFER size, drawn through the same rotation and dst
// rect as the panel itself -- letterpress is a property of the PAGE, not the
// glass, so unlike the grain it covers the panel only. Content-locked and
// aperiodic, so scaling with the panel cannot beat against the presentation
// (the ST-008 moire needs a regular lattice). Regenerated only when the
// content, the dial, the palette or the launch seed changes: a still page
// costs nothing. Model and reasoning: src/Letterpress.h.
static SDL_Texture *letterpressTexture = nullptr;
static int letterTexW = 0, letterTexH = 0;
static uint64_t letterTexSeq = 0;
static int letterTexStrength = -1;
static uint32_t letterTexKey = 0;
// The press's three PART percents are cache keys too. They were not, and that
// was the live half of the dead plate-pressure dial (2026-08-22 audit): a
// drawer slider stored its value and asked for a present, the present found
// seq, strength and palette unchanged, and served the cached field -- the new
// ratio first painted at some unrelated page turn.
static int letterTexRing = -1, letterTexDeboss = -1, letterTexPress = -1;

static void destroyLetterpressTexture() {
  if (!letterpressTexture) return;
  SDL_DestroyTexture(letterpressTexture);
  letterpressTexture = nullptr;
  letterTexW = letterTexH = 0;
  letterTexSeq = 0;
  letterTexStrength = -1;
  letterTexKey = 0;
  letterTexRing = letterTexDeboss = letterTexPress = -1;
}

static bool ensureLetterpressTexture() {
  const int strength = SimulatorOverlay::letterpressStrength.load();
  const int w = HalDisplay::activeWidth();
  const int h = HalDisplay::activeHeight();
  if (strength <= 0 || w <= 0 || h <= 0 || !sdl_renderer) {
    destroyLetterpressTexture();
    return false;
  }
  const PanelPalette live = livePanelPalette(display.isInverted());
  const uint32_t seed = pageSheetSeed();
  const uint32_t palKey =
      phosphorgrain::hash3(static_cast<uint32_t>(live.ink[0]) << 16 |
                               static_cast<uint32_t>(live.ink[1]) << 8 |
                               live.ink[2],
                           static_cast<uint32_t>(live.paper[0]) << 16 |
                               static_cast<uint32_t>(live.paper[1]) << 8 |
                               live.paper[2],
                           seed);
  // The part ratios join the cache check -- see the statics' comment.
  const int ringPct = SimulatorOverlay::pressRingPct.load();
  const int debossPct = SimulatorOverlay::pressDebossPct.load();
  const int pressPct = SimulatorOverlay::pressPressurePct.load();
  // Read the frame and its seq together, under the lock, so the key can never
  // describe pixels from a different frame than the ones read.
  std::vector<uint8_t> inkness;
  uint64_t seq = 0;
  {
    const std::lock_guard<std::mutex> lock(pixelBufMutex);
    seq = pixelBufSeq;
    if (letterpressTexture && letterTexW == w && letterTexH == h &&
        letterTexSeq == seq && letterTexStrength == strength &&
        letterTexKey == palKey && letterTexRing == ringPct &&
        letterTexDeboss == debossPct && letterTexPress == pressPct) {
      if (timingLogWanted()) timingFrame.letterpress.served = true;
      return true;
    }
    // INKNESS: where each pixel sits on the ink->paper segment, 255 = ink.
    // Projection in byte space, because pixelBuf's grays are integer-lerped
    // between exactly these two tones.
    const float dr = static_cast<float>(live.paper[0]) - live.ink[0];
    const float dg = static_cast<float>(live.paper[1]) - live.ink[1];
    const float db = static_cast<float>(live.paper[2]) - live.ink[2];
    const float denom = dr * dr + dg * dg + db * db;
    if (denom < 1.0f) return false;  // degenerate palette: no edges to find
    inkness.resize(static_cast<size_t>(w) * h);
    for (size_t i = 0; i < inkness.size(); ++i) {
      const uint32_t px = pixelBuf[i];
      const float pr = static_cast<float>((px >> 16) & 0xFF) - live.ink[0];
      const float pg = static_cast<float>((px >> 8) & 0xFF) - live.ink[1];
      const float pb = static_cast<float>(px & 0xFF) - live.ink[2];
      float t = 1.0f - (pr * dr + pg * dg + pb * db) / denom;
      if (t < 0.0f) t = 0.0f;
      if (t > 1.0f) t = 1.0f;
      inkness[i] = static_cast<uint8_t>(t * 255.0f + 0.5f);
    }
  }

  // Hand the snapshot to the sheet pass before anything can fail below: the
  // defect mask wants the CURRENT glyphs even on a frame where the texture
  // upload goes wrong.
  sheetInkness = inkness;
  sheetInknessW = w;
  sheetInknessH = h;
  // ...and the same plane, blurred down, for the NEXT leaf to show through.
  updateVersoMaps(inkness, w, h, seed);

  // REUSED, not destroyed and recreated. The field is per-PAGE now, so this
  // runs on every page turn rather than on a dial change; a STATIC texture of
  // ~3.4 Mpx destroyed and reallocated per turn is a driver allocation nobody
  // asked for. Only a size change needs a new texture.
  if (!letterpressTexture || letterTexW != w || letterTexH != h) {
    destroyLetterpressTexture();
    letterpressTexture =
        SDL_CreateTexture(sdl_renderer, SDL_PIXELFORMAT_ARGB8888,
                          SDL_TEXTUREACCESS_STATIC, w, h);
    if (!letterpressTexture) {
      LOG_ERR("DISP", "letterpress: no field texture (%s)", SDL_GetError());
      return false;
    }
  }
  letterpress::Params params;
  params.strengthPercent = strength;
  params.seed = seed;
  params.paperDarkenBudget =
      letterpress::paperBudget(srgbLumOf(live.ink), srgbLumOf(live.paper));
  // NO TOOTH IN THE PANEL FIELD (owner 2026-08-22: "make sure panel and paper
  // actually match visually, in color and texture with light mode"). The
  // paper's tooth is a property of the SHEET and is drawn output-wide by the
  // sheet-tooth pass below, over card and page alike -- putting it here as
  // well textured the page's paper twice and left the card flat, which is the
  // visible rectangle that report is about. What stays here is everything
  // carried by ink or its edges (ring, deboss, pressure, in-stroke), all of
  // which are zero on flat paper, so the panel boundary contributes nothing.
  params.includeTooth = false;
  // The press's three PARTS, from the drawer's Press group. Composed
  // multiplicatively with the master strength above, so each quantity has one
  // stored value; 100% each is the shipped composition.
  params.ringScale = static_cast<float>(ringPct) / 100.0f;
  params.debossScale = static_cast<float>(debossPct) / 100.0f;
  params.pressScale = static_cast<float>(pressPct) / 100.0f;
  const uint64_t letterT0 = SDL_GetTicksNS();
  std::vector<uint32_t> field(static_cast<size_t>(w) * h);
  auto tAt = [&](int x, int y) {
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (x >= w) x = w - 1;
    if (y >= h) y = h - 1;
    return static_cast<float>(inkness[static_cast<size_t>(y) * w + x]) / 255.0f;
  };
  for (int y = 0; y < h; ++y) {
    uint32_t *row = field.data() + static_cast<size_t>(y) * w;
    for (int x = 0; x < w; ++x) {
      float win[3][3];
      for (int dy = -1; dy <= 1; ++dy)
        for (int dx = -1; dx <= 1; ++dx)
          win[dy + 1][dx + 1] = tAt(x + dx, y + dy);
      const uint32_t m = letterpress::multiplierAt(params, win, x, y, w, h);
      // Achromatic, like the grain: pressed ink is MORE of its own pigment and
      // a deboss shadow is LESS of the paper's light, not a different colour.
      row[x] = 0xFF000000u | (m << 16) | (m << 8) | m;
    }
  }
  if (!SDL_UpdateTexture(letterpressTexture, nullptr, field.data(),
                         static_cast<int>(w * sizeof(uint32_t)))) {
    LOG_ERR("DISP", "letterpress: could not upload the field (%s)",
            SDL_GetError());
    destroyLetterpressTexture();
    return false;
  }
  SDL_SetTextureBlendMode(letterpressTexture, SDL_BLENDMODE_MOD);
  letterTexW = w;
  letterTexH = h;
  letterTexSeq = seq;
  letterTexStrength = strength;
  letterTexKey = palKey;
  letterTexRing = ringPct;
  letterTexDeboss = debossPct;
  letterTexPress = pressPct;
  if (timingLogWanted()) {
    timingFrame.letterpress.built = true;
    timingFrame.letterpress.ms =
        static_cast<double>(SDL_GetTicksNS() - letterT0) / 1.0e6;
  }
  if (const char *e = std::getenv("CROSSPOINT_SIM_LOG_PRESENTS"))
    if (e[0] == '1')
      SDL_Log("[letterpress] field %dx%d strength %d seed %u budget %.3f "
              "in %.1f ms",
              w, h, strength, seed,
              static_cast<double>(params.paperDarkenBudget),
              static_cast<double>(SDL_GetTicksNS() - letterT0) / 1.0e6);
  return true;
}

// --- THE SHEET (light mode) ------------------------------------------------
//
// The paper half of the letterpress, at OUTPUT size, drawn 1:1 over the whole
// app surface -- the one-sheet ruling applied to paper (owner 2026-08-22:
// "make sure panel and paper actually match visually, in color and texture
// with light mode"). It carries TWO things: the sheet's tooth, and the marks
// the sheet itself carries (src/PaperDefects.h -- foxing, red rag flecks, blue
// marks, brown stains, fly specks, wax spots).
//
// THIS COMMENT USED TO SAY "never per page", and both halves of that sentence
// are now the opposite (owner order 2026-08-22, the per-page paper work). It
// was:
//
//     Content-independent by construction (a pure hash of output coordinates),
//     so it regenerates only when the size, the dial or the palette budget
//     changes -- never per page.
//
// The field is now CONTENT-DEPENDENT (defects are masked by the page's inkness,
// because a mark never sits on a glyph) and PER-PAGE (its seed is the page's
// identity, so a page you turn back to is the same sheet -- see pageSheetSeed
// above and docs/paper-defects.md). Exactly ONE rebuild per displayed page: the
// cache key folds the page seed, and NOT pixelBufSeq, which increments twice
// per page and would rebuild a ~3.4 Mpx field twice per turn.
//
// The rebuild is two passes: the tooth per pixel as before, then each mark over
// its OWN bounding box. The extra cost is proportional to the marks' area, not
// the sheet's, which is what makes a per-page rebuild affordable at all. The
// texture is REUSED across rebuilds and destroyed only on a size change, for
// the same reason.
static SDL_Texture *sheetToothTexture = nullptr;
static int sheetTexW = 0, sheetTexH = 0;
static int sheetTexStrength = -1;
static int sheetTexTooth = -1;
static int sheetTexFormation = -1;
static int sheetTexDefects = -1;
// The laid dial and the presentation scale it converts through (milli-px per
// source px) are cache keys too, or a stock change or a window rescale would
// serve a field with the wrong wires -- the letterpress part-ratio lesson.
static int sheetTexLaid = -1;
static int sheetTexScaleKey = -1;
// Show-through's dial, and the generation of the leaf BEHIND this one. The
// generation is the load-bearing half: everything else about a page can be
// unchanged while the verso is a different page, and without it the field
// would keep the previous leaf's show-through forever.
static int sheetTexShowThrough = -1;
static uint64_t sheetTexVersoGen = 0;
static uint32_t sheetTexKey = 0;

// The PRESENTED page rect in OUTPUT pixels, plus the orientation it was
// presented in -- what outputToPanel below inverts.
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

static void destroySheetToothTexture() {
  if (!sheetToothTexture) return;
  SDL_DestroyTexture(sheetToothTexture);
  sheetToothTexture = nullptr;
  sheetTexW = sheetTexH = 0;
  sheetTexStrength = -1;
  sheetTexTooth = -1;
  sheetTexFormation = -1;
  sheetTexDefects = -1;
  sheetTexLaid = -1;
  sheetTexScaleKey = -1;
  sheetTexShowThrough = -1;
  sheetTexVersoGen = 0;
  sheetTexKey = 0;
}

// OUTPUT PIXEL -> FRAMEBUFFER PIXEL. The inverse of the presentation, and it is
// not a scale: drawPanel rotates the landscape framebuffer by 90 / -90 / 180
// depending on orientation, about the dst rect's centre.
//
// Derived rather than fitted. A clockwise quarter turn sends framebuffer pixel
// (x, y) to (kH-1-y, x) in the presented image, so the inverse of a presented
// normalized (u, v) is fbX = v*kW, fbY = (1-u)*kH; counter-clockwise is the
// same relation the other way round, and 180 is a double flip.
//
// Returns false when the point is outside the presented page -- which is bare
// SHEET (the card, the pad, the bezel), inkness 0, full defect. That is the
// correct physics under the one-sheet ruling and it is what stops a mark
// halting dead at the page's edge.
static bool outputToPanel(int ox, int oy, int &fx, int &fy) {
  if (sheetPanelW <= 0 || sheetPanelH <= 0) return false;
  const float u = (static_cast<float>(ox) + 0.5f -
                   static_cast<float>(sheetPanelX)) /
                  static_cast<float>(sheetPanelW);
  const float v = (static_cast<float>(oy) + 0.5f -
                   static_cast<float>(sheetPanelY)) /
                  static_cast<float>(sheetPanelH);
  if (u < 0.0f || u >= 1.0f || v < 0.0f || v >= 1.0f) return false;
  const float kW = static_cast<float>(HalDisplay::activeWidth());
  const float kH = static_cast<float>(HalDisplay::activeHeight());
  float fxf = 0.0f, fyf = 0.0f;
  switch (sheetPanelOrientation) {
  case GfxRenderer::Portrait:
    fxf = v * kW;
    fyf = (1.0f - u) * kH;
    break;
  case GfxRenderer::PortraitInverted:
    fxf = (1.0f - v) * kW;
    fyf = u * kH;
    break;
  case GfxRenderer::LandscapeClockwise:
    fxf = (1.0f - u) * kW;
    fyf = (1.0f - v) * kH;
    break;
  default:
    fxf = u * kW;
    fyf = v * kH;
    break;
  }
  fx = static_cast<int>(fxf);
  fy = static_cast<int>(fyf);
  if (fx < 0) fx = 0;
  if (fy < 0) fy = 0;
  if (fx >= sheetInknessW) fx = sheetInknessW - 1;
  if (fy >= sheetInknessH) fy = sheetInknessH - 1;
  return true;
}

// Inkness at an OUTPUT pixel: 0 on bare sheet, 1 under solid ink.
static float sheetInknessAt(int ox, int oy) {
  if (sheetInkness.empty() || sheetInknessW <= 0 || sheetInknessH <= 0)
    return 0.0f;
  int fx = 0, fy = 0;
  if (!outputToPanel(ox, oy, fx, fy)) return 0.0f;
  return static_cast<float>(
             sheetInkness[static_cast<size_t>(fy) * sheetInknessW + fx]) /
         255.0f;
}

static bool ensureSheetToothTexture(int w, int h, float outPxPerSourcePx) {
  const int strength = SimulatorOverlay::letterpressStrength.load();
  if (strength <= 0 || w <= 0 || h <= 0 || !sdl_renderer) {
    destroySheetToothTexture();
    return false;
  }
  const int toothPct = SimulatorOverlay::paperToothPct.load();
  const int formationPct = SimulatorOverlay::paperFormationPct.load();
  const int defectsPct = SimulatorOverlay::paperDefectsPct.load();
  const int laidPct = SimulatorOverlay::laidLinesStrength.load();
  const int showPct = SimulatorOverlay::showThroughStrength.load();
  const int scaleKey = static_cast<int>(outPxPerSourcePx * 1000.0f + 0.5f);
  const PanelPalette live = livePanelPalette(display.isInverted());
  letterpress::Params params;
  params.strengthPercent = strength;
  params.seed = pageSheetSeed();  // 'PRES' lane folded into the page identity
  params.paperDarkenBudget =
      letterpress::paperBudget(srgbLumOf(live.ink), srgbLumOf(live.paper));
  // The STOCK's roughness and the sheet's cloudiness -- the paper half of the
  // 2026-08-22 picker. Both live on the sheet pass alone: the panel field's
  // components are carried by ink, and paper is not a property of ink.
  params.toothScale = static_cast<float>(toothPct) / 100.0f;
  params.formationDepth = static_cast<float>(formationPct) / 100.0f;
  const uint32_t key = phosphorgrain::hash3(
      static_cast<uint32_t>(live.paper[0]) << 16 |
          static_cast<uint32_t>(live.paper[1]) << 8 | live.paper[2],
      static_cast<uint32_t>(params.paperDarkenBudget * 65535.0f), params.seed);
  if (sheetToothTexture && sheetTexW == w && sheetTexH == h &&
      sheetTexStrength == strength && sheetTexTooth == toothPct &&
      sheetTexFormation == formationPct && sheetTexDefects == defectsPct &&
      sheetTexLaid == laidPct && sheetTexScaleKey == scaleKey &&
      sheetTexShowThrough == showPct && sheetTexVersoGen == versoGeneration &&
      sheetTexKey == key) {
    if (timingLogWanted()) timingFrame.sheet.served = true;
    return true;
  }
  // REUSED across rebuilds -- see the block comment. Only a size change costs a
  // new texture, because this now runs once per PAGE.
  if (!sheetToothTexture || sheetTexW != w || sheetTexH != h) {
    destroySheetToothTexture();
    sheetToothTexture =
        SDL_CreateTexture(sdl_renderer, SDL_PIXELFORMAT_ARGB8888,
                          SDL_TEXTUREACCESS_STATIC, w, h);
    if (!sheetToothTexture) {
      LOG_ERR("DISP", "sheet: no field texture (%s)", SDL_GetError());
      return false;
    }
  }
  const uint64_t t0 = SDL_GetTicksNS();

  // THE PAPER'S BUDGET, SPLIT FOUR WAYS, HOISTED HERE BECAUSE SHOW-THROUGH
  // FOLDS INTO THE FIRST LOOP. What the tooth left is shared, in this order:
  // the wires take half of it, show-through takes half of what remains, and
  // the marks take the rest. Every share is a MEAN bound, and each pass clamps
  // its own depth to fit, so the composite cannot breach the palette's 7:1
  // floor by construction. With both new consumers at zero the marks receive
  // exactly the number they received before either existed -- which is what
  // keeps a wove sheet with show-through off byte-identical.
  laidstructure::Params laidParams;
  laidParams.strengthPercent = laidPct;
  laidParams.seed = params.seed;
  laidParams.outPxPerSourcePx = outPxPerSourcePx;
  const float paperLeft = letterpress::remainingPaperBudget(params);
  laidParams.budgetMeanDarkening = 0.5f * paperLeft;
  float afterWires = paperLeft - laidstructure::meanDarkeningBound(laidParams);
  if (afterWires < 0.0f) afterWires = 0.0f;

  showthrough::Params stParams;
  stParams.strengthPercent = showPct;
  // The STOCK's factor is already folded into the percent by the pusher (the
  // iOS light picker composes lightink::showThroughScaleFor into it, the way
  // it composes tooth and formation), so this stays 1.0 and there is exactly
  // one authority for how thin the sheet is.
  stParams.stockScale = 1.0f;
  stParams.budgetMeanDarkening = 0.5f * afterWires;

  std::vector<uint32_t> field(static_cast<size_t>(w) * h);

  // THE LEAF BEHIND THIS ONE, resampled onto a coarse OUTPUT-space lattice.
  //
  // Built on a lattice and interpolated rather than inverted per pixel: the
  // field is a heavy blur, so it has no detail a 4 px grid can lose, and
  // inverting the presentation transform (outputToPanel -- a rotation, a
  // divide and four clamps) 3.4 million times is the cost this avoids. The
  // MIRROR is applied here, in presented pixels, because it is the back of the
  // sheet -- see showthrough::mirrorOutputX for why it cannot be done in the
  // framebuffer, which is landscape.
  const bool showThroughLive =
      showthrough::effectiveDepth(stParams) > 0.0f && !versoMap.empty() &&
      versoMapW > 0 && versoMapH > 0 && sheetPanelW > 0 && sheetPanelH > 0 &&
      sheetInknessW > 0 && sheetInknessH > 0;
  const int gcell = showthrough::kOutCellPx;
  const int gw = w / gcell + 2, gh = h / gcell + 2;
  std::vector<uint8_t> stGrid;
  if (showThroughLive) {
    stGrid.assign(static_cast<size_t>(gw) * gh, 255);
    const float fbW = static_cast<float>(HalDisplay::activeWidth());
    const float fbH = static_cast<float>(HalDisplay::activeHeight());
    for (int gy = 0; gy < gh; ++gy) {
      const int oy = gy * gcell;
      uint8_t *grow = stGrid.data() + static_cast<size_t>(gy) * gw;
      for (int gx = 0; gx < gw; ++gx) {
        const int ox = gx * gcell;
        int fx = 0, fy = 0;
        float density = 0.0f;
        if (outputToPanel(
                showthrough::mirrorOutputX(ox, sheetPanelX, sheetPanelW), oy,
                fx, fy))
          density = showthrough::sampleAt(
              versoMap.data(), versoMapW, versoMapH,
              (static_cast<float>(fx) + 0.5f) / fbW,
              (static_cast<float>(fy) + 0.5f) / fbH);
        grow[gx] = showthrough::multiplierAt(stParams, density);
      }
    }
  }

  for (int y = 0; y < h; ++y) {
    uint32_t *row = field.data() + static_cast<size_t>(y) * w;
    const int gy = y / gcell;
    const float ty = static_cast<float>(y - gy * gcell) /
                     static_cast<float>(gcell);
    const uint8_t *g0 =
        showThroughLive ? stGrid.data() + static_cast<size_t>(gy) * gw : nullptr;
    const uint8_t *g1 = g0 ? g0 + gw : nullptr;
    for (int x = 0; x < w; ++x) {
      uint32_t m = letterpress::sheetToothMultiplierAt(params, x, y, w, h);
      if (g0) {
        const int gx = x / gcell;
        const float tx = static_cast<float>(x - gx * gcell) /
                         static_cast<float>(gcell);
        const float a = static_cast<float>(g0[gx]) +
                        (static_cast<float>(g0[gx + 1]) -
                         static_cast<float>(g0[gx])) * tx;
        const float b = static_cast<float>(g1[gx]) +
                        (static_cast<float>(g1[gx + 1]) -
                         static_cast<float>(g1[gx])) * tx;
        const uint32_t st =
            static_cast<uint32_t>(a + (b - a) * ty + 0.5f);
        if (st < 255) m = m * st / 255u;
      }
      row[x] = 0xFF000000u | (m << 16) | (m << 8) | m;
    }
  }

  // THE WIRES. Chain and laid lines, folded into the same field when the
  // selected stock carries them (laidPct is 0 for every wove stock, and 0 is
  // a bit-exact skip). Achromatic like the tooth -- a furrow is less pulp,
  // not a different color -- and generated HERE, at output size, because at
  // ~1.9 px the laid pitch in the framebuffer would beat against the phone's
  // fractional minification (ST-008; src/LaidStructure.h). Its budget is HALF
  // of what the tooth left; the other half stays with the defect layer below,
  // so the three paper passes jointly stay inside the palette's floor.
  if (laidPct > 0 && outPxPerSourcePx > 0.0f) {
    // The erf work is separable: laid darkness is x-independent, chain
    // darkness y-independent, and the host test pins combine(row, col) ==
    // multiplierAt, so the caches run the exact shipped math.
    std::vector<float> rowD(static_cast<size_t>(h));
    std::vector<float> colD(static_cast<size_t>(w));
    for (int y = 0; y < h; ++y)
      rowD[y] = laidstructure::rowLaidDarkness(laidParams,
                                               static_cast<float>(y));
    for (int x = 0; x < w; ++x)
      colD[x] = laidstructure::colChainDarkness(laidParams,
                                                static_cast<float>(x));
    for (int y = 0; y < h; ++y) {
      uint32_t *row = field.data() + static_cast<size_t>(y) * w;
      for (int x = 0; x < w; ++x) {
        const uint32_t m = laidstructure::combine(laidParams, rowD[y], colD[x]);
        if (m == 255) continue;
        const uint32_t px = row[x];
        auto mul = [m](uint32_t base) { return base * m / 255u; };
        row[x] = 0xFF000000u | (mul((px >> 16) & 0xFF) << 16) |
                 (mul((px >> 8) & 0xFF) << 8) | mul(px & 0xFF);
      }
    }
  }

  // THE MARKS. Folded into the SAME field, per channel: MOD multiplies channels
  // independently, so a brown foxing spot is legal and still strictly
  // darkening. Their budget is what the tooth LEFT (letterpress::
  // remainingPaperBudget, which reproduces the tooth's CONDITIONAL clamp),
  // MINUS what the wires and the show-through above will spend of it (both 0
  // by default, so a wove sheet with show-through off has byte-identical
  // marks), and
  // paperdefects::generate scales every mark's depth to fit it -- so the
  // composite cannot breach the palette's contrast floor by construction.
  paperdefects::Params dp;
  dp.dialPercent = defectsPct;
  dp.seed = params.seed;
  dp.remainingBudget =
      afterWires - showthrough::meanDarkeningBound(stParams);
  if (dp.remainingBudget < 0.0f) dp.remainingBudget = 0.0f;
  paperdefects::Mark marks[paperdefects::kMaxMarks];
  const int markCount = paperdefects::generate(dp, w, h, marks);
  for (int k = 0; k < markCount; ++k) {
    int x0, y0, x1, y1;
    if (!paperdefects::bounds(marks[k], w, h, x0, y0, x1, y1)) continue;
    for (int y = y0; y < y1; ++y) {
      uint32_t *row = field.data() + static_cast<size_t>(y) * w;
      for (int x = x0; x < x1; ++x) {
        float mult[3];
        if (!paperdefects::multiplierAt(marks[k], x, y, mult)) continue;
        // INK MASKS DEFECTS: ink is printed ON the paper, so a mark fades to
        // nothing under a glyph. This is also what protects legibility at every
        // dial setting.
        paperdefects::applyInkMask(mult, sheetInknessAt(x, y));
        const uint32_t px = row[x];
        auto fold = [](uint32_t base, float f) {
          const int v = static_cast<int>(static_cast<float>(base) * f + 0.5f);
          return static_cast<uint32_t>(v < 0 ? 0 : (v > 255 ? 255 : v));
        };
        row[x] = 0xFF000000u |
                 (fold((px >> 16) & 0xFF, mult[0]) << 16) |
                 (fold((px >> 8) & 0xFF, mult[1]) << 8) |
                 fold(px & 0xFF, mult[2]);
      }
    }
  }

  if (!SDL_UpdateTexture(sheetToothTexture, nullptr, field.data(),
                         static_cast<int>(w * sizeof(uint32_t)))) {
    LOG_ERR("DISP", "sheet: could not upload the field (%s)", SDL_GetError());
    destroySheetToothTexture();
    return false;
  }
  SDL_SetTextureBlendMode(sheetToothTexture, SDL_BLENDMODE_MOD);
  // Drawn 1:1 at output size; NEAREST states that, same as the grain.
  SDL_SetTextureScaleMode(sheetToothTexture, SDL_SCALEMODE_NEAREST);
  sheetTexW = w;
  sheetTexH = h;
  sheetTexStrength = strength;
  sheetTexTooth = toothPct;
  sheetTexFormation = formationPct;
  sheetTexDefects = defectsPct;
  sheetTexLaid = laidPct;
  sheetTexScaleKey = scaleKey;
  sheetTexShowThrough = showPct;
  sheetTexVersoGen = versoGeneration;
  sheetTexKey = key;
  if (timingLogWanted()) {
    timingFrame.sheet.built = true;
    timingFrame.sheet.ms = static_cast<double>(SDL_GetTicksNS() - t0) / 1.0e6;
  }
  // A PER-PAGE rebuild is exactly when this wants instrumenting: without a
  // number here, "does the paper cost a page turn" is guesswork.
  if (const char *e = std::getenv("CROSSPOINT_SIM_LOG_PRESENTS"))
    if (e[0] == '1')
      SDL_Log("[sheet] field %dx%d seed %u tooth %d%% formation %d%% "
              "laid %d%% (scale %.3f) showthrough %d%% (depth %.4f, verso gen "
              "%llu, %s) defects %d%% (%d marks, budget left %.4f) in %.1f ms",
              w, h, params.seed, toothPct, formationPct, laidPct,
              static_cast<double>(outPxPerSourcePx), showPct,
              static_cast<double>(showthrough::effectiveDepth(stParams)),
              static_cast<unsigned long long>(versoGeneration),
              showThroughLive ? "live" : "no verso yet", defectsPct, markCount,
              static_cast<double>(dp.remainingBudget),
              static_cast<double>(SDL_GetTicksNS() - t0) / 1.0e6);
  return true;
}

// --- SCANLINES (dark mode) -------------------------------------------------
//
// A MOD texture at OUTPUT size, drawn 1:1 over the whole app surface -- one
// raster covers the glass, the same one-sheet ruling the grain followed. The
// per-row erf work is x-independent, so it is cached per (row, level bucket)
// and folded per pixel through scanlines::combine, which the host test pins
// as exactly multiplierAt.
//
// A/B CAPTURES OF THIS FIELD MUST PIN CROSSPOINT_SIM_GRAIN_SEED. The raster's
// phase jitter, thickness jitter and mottle all hang off grainSeed(), which is
// re-rolled every launch, so two runs of the same dials differ by ~2.2 code
// values before any dial is touched -- which is larger than the corner-defocus
// effect being measured. Cost a wrong reading on 2026-08-23. Bloom levels come from reading back the composed
// backbuffer at regeneration time, so the beam-current model sees the true
// light -- palette, fade and accumulator included. Regenerated per content
// seq (page turns), never per frame: a still page must not crawl.
static SDL_Texture *scanTexture = nullptr;
static int scanTexW = 0, scanTexH = 0;
static uint64_t scanTexSeq = 0;
static int scanTexIntensity = -1;
static uint32_t scanTexKey = 0;
static int scanTexPitchKey = -1;
static int scanTexBloom = -1;
static int scanTexDefocus = -1;

// --- CORNER DEFOCUS --------------------------------------------------------
//
// The per-pixel vertical sigma scale, cached as a normalized byte. It depends
// on the OUTPUT SIZE and the dial and on nothing else -- not the page, not the
// palette, not the content -- so it is built once and read on every page turn
// thereafter. That is the whole reason this item is affordable: computing an
// ellipse's vertical semi-axis (a divide and a square root) 3.4 million times
// per page turn would have cost more than the raster it modulates.
//
// Stored as (scale - 1) / (max - 1) so the byte spans the useful range at full
// precision whatever the strength; scaleOf inverts it.
static std::vector<uint8_t> defocusMap;
static int defocusMapW = 0, defocusMapH = 0;
static int defocusMapStrength = -1;

static bool ensureDefocusMap(int w, int h, const cornerdefocus::Params &cd) {
  if (cornerdefocus::isOff(cd) || w <= 0 || h <= 0) {
    defocusMap.clear();
    defocusMapW = defocusMapH = 0;
    defocusMapStrength = -1;
    return false;
  }
  if (defocusMapW == w && defocusMapH == h &&
      defocusMapStrength == cd.strengthPercent)
    return true;
  const float span = cornerdefocus::maxSigmaScale(cd) - 1.0f;
  if (span <= 0.0f) return false;
  defocusMap.assign(static_cast<size_t>(w) * h, 0);
  for (int y = 0; y < h; ++y) {
    uint8_t *row = defocusMap.data() + static_cast<size_t>(y) * w;
    for (int x = 0; x < w; ++x) {
      const float t = (cornerdefocus::sigmaScaleAt(cd, x, y, w, h) - 1.0f) / span;
      const int v = static_cast<int>(t * 255.0f + 0.5f);
      row[x] = static_cast<uint8_t>(v < 0 ? 0 : (v > 255 ? 255 : v));
    }
  }
  defocusMapW = w;
  defocusMapH = h;
  defocusMapStrength = cd.strengthPercent;
  return true;
}

// How many defocus anchors the (row, level, defocus) table carries when the
// dial is on. The OFF path keeps its own 16-bucket table over the LEVEL alone,
// untouched and bit-exact.
//
// IT HAS TO BE A SECOND AXIS, and the cheaper thing that is not was tried and
// measured wrong. Bloom and defocus both scale the same sigma, so the obvious
// economy is to bucket their PRODUCT and keep one axis. That is arithmetically
// identical inside rowTransmissionRaw and WRONG at the normalization: the
// defocus divides back out (mean-preserving, which is the whole point) and the
// bloom must not (it spares light, which is ITS whole point). Collapsed onto
// one axis the divide hits both, and the measured result was a raster softened
// by 27% AT THE CENTRE, where the defocus scale is exactly 1 -- an effect
// uniform across the screen wearing the name of one that is not.
//
// Three anchors span a range of only 0.45 (1.0 at the centre to 1.45 at the
// corner), interpolated per pixel; the transmission is smooth enough in sigma
// over that span that the sampling error stays under a tenth of a code value,
// measured. Cost is 3x the erf work, which is ~8% of this pass.
// Five anchors were measured first and cost +13.5 ms per page turn against
// three at +6; the extra accuracy was not visible.
static constexpr int kDefocusAnchors = 3;

static void destroyScanTexture() {
  if (!scanTexture) return;
  SDL_DestroyTexture(scanTexture);
  scanTexture = nullptr;
  scanTexW = scanTexH = 0;
  scanTexSeq = 0;
  scanTexIntensity = -1;
  scanTexKey = 0;
  scanTexPitchKey = -1;
  scanTexBloom = -1;
  scanTexDefocus = -1;
}

static bool ensureScanlinesTexture(int w, int h, float pitchPx) {
  const int intensity = SimulatorOverlay::scanlinesIntensity.load();
  if (intensity <= 0 || w <= 0 || h <= 0 || pitchPx <= 0.0f || !sdl_renderer) {
    destroyScanTexture();
    return false;
  }
  const PanelPalette live = livePanelPalette(display.isInverted());
  const uint32_t seed = grainSeed() ^ 0x5343414Eu;  // 'SCAN'
  const uint32_t palKey =
      phosphorgrain::hash3(static_cast<uint32_t>(live.ink[0]) << 16 |
                               static_cast<uint32_t>(live.ink[1]) << 8 |
                               live.ink[2],
                           static_cast<uint32_t>(live.paper[0]) << 16 |
                               static_cast<uint32_t>(live.paper[1]) << 8 |
                               live.paper[2],
                           seed);
  const int pitchKey = static_cast<int>(pitchPx * 1000.0f + 0.5f);
  const int bloom = SimulatorOverlay::scanlineBloom.load();
  cornerdefocus::Params cd;
  cd.strengthPercent = SimulatorOverlay::cornerDefocusStrength.load();
  const uint64_t seq = pixelBufSeq;
  if (scanTexture && scanTexW == w && scanTexH == h && scanTexSeq == seq &&
      scanTexIntensity == intensity && scanTexKey == palKey &&
      scanTexPitchKey == pitchKey && scanTexBloom == bloom &&
      scanTexDefocus == cd.strengthPercent) {
    if (timingLogWanted()) timingFrame.scanlines.served = true;
    return true;
  }
  const uint64_t scanT0 = timingLogWanted() ? SDL_GetTicksNS() : 0;

  scanlines::Params params;
  params.intensityPercent = intensity;
  params.seed = seed;
  params.pitchPx = pitchPx;
  params.mottleDepth = scanlines::mottleDepthFor(intensity);
  params.bloomGain = scanlines::bloomGainFor(bloom);
  params.budgetMeanDarkening =
      0.8f * phosphorgrain::darkeningBudget(srgbLumOf(live.ink),
                                            srgbLumOf(live.paper));

  // The beam-current map: 16 brightness buckets off the composed frame.
  // Everything already drawn this present -- page, chrome, letterbox -- is
  // exactly the light the raster carries, so nothing needs the panel rect or
  // the orientation arithmetic.
  std::vector<uint8_t> bucket(static_cast<size_t>(w) * h, 0);
  // THE READBACK, timed on its own line. It is the one GPU->CPU stall in the
  // whole present and the roadmap's first-named cost, so it is reported apart
  // from the field build it feeds rather than buried inside it.
  const uint64_t readT0 = timingLogWanted() ? SDL_GetTicksNS() : 0;
  if (SDL_Surface *snap = SDL_RenderReadPixels(sdl_renderer, nullptr)) {
    SDL_Surface *conv = snap;
    if (snap->format != SDL_PIXELFORMAT_ARGB8888)
      conv = SDL_ConvertSurface(snap, SDL_PIXELFORMAT_ARGB8888);
    if (conv) {
      const int cw = conv->w < w ? conv->w : w;
      const int chh = conv->h < h ? conv->h : h;
      for (int y = 0; y < chh; ++y) {
        const uint32_t *src = reinterpret_cast<const uint32_t *>(
            static_cast<const uint8_t *>(conv->pixels) +
            static_cast<size_t>(y) * conv->pitch);
        uint8_t *dst = bucket.data() + static_cast<size_t>(y) * w;
        for (int x = 0; x < cw; ++x) {
          const uint32_t px = src[x];
          const uint32_t luma = 54u * ((px >> 16) & 0xFF) +
                                183u * ((px >> 8) & 0xFF) + 19u * (px & 0xFF);
          dst[x] = static_cast<uint8_t>((luma >> 8) >> 4);  // 0..15
        }
      }
      if (conv != snap) SDL_DestroySurface(conv);
    }
    SDL_DestroySurface(snap);
  }
  if (timingLogWanted()) {
    timingFrame.readback = true;
    timingFrame.readbackMs =
        static_cast<double>(SDL_GetTicksNS() - readT0) / 1.0e6;
  }

  // CORNER DEFOCUS decides which of two tables the raster is built from, and
  // the OFF branch is the original code untouched -- not a special case of the
  // new one -- so a build with the dial at zero is byte-identical to one from
  // before this existed.
  const bool defocusLive = ensureDefocusMap(w, h, cd);
  const float defocusSpan = cornerdefocus::maxSigmaScale(cd) - 1.0f;
  const float defocusStep =
      defocusLive ? defocusSpan / static_cast<float>(kDefocusAnchors - 1)
                  : 0.0f;

  // Per-(row, level bucket [, defocus anchor]) transmission: the erf work,
  // done once per row rather than once per pixel.
  const int anchors = defocusLive ? kDefocusAnchors : 1;
  std::vector<float> rowT(static_cast<size_t>(h) * 16 * anchors);
  for (int y = 0; y < h; ++y)
    for (int b = 0; b < 16; ++b) {
      const float level = (static_cast<float>(b) + 0.5f) / 16.0f;
      float *cell = rowT.data() + (static_cast<size_t>(y) * 16 + b) * anchors;
      for (int d = 0; d < anchors; ++d)
        cell[d] = scanlines::rowTransmission(
            params, static_cast<float>(y), level,
            1.0f + defocusStep * static_cast<float>(d));
    }

  destroyScanTexture();
  scanTexture = SDL_CreateTexture(sdl_renderer, SDL_PIXELFORMAT_ARGB8888,
                                  SDL_TEXTUREACCESS_STATIC, w, h);
  if (!scanTexture) {
    LOG_ERR("DISP", "scanlines: no field texture (%s)", SDL_GetError());
    return false;
  }
  std::vector<uint32_t> field(static_cast<size_t>(w) * h);
  for (int y = 0; y < h; ++y) {
    uint32_t *row = field.data() + static_cast<size_t>(y) * w;
    const float *tRow = rowT.data() + static_cast<size_t>(y) * 16 * anchors;
    const uint8_t *bRow = bucket.data() + static_cast<size_t>(y) * w;
    const uint8_t *dRow =
        defocusLive ? defocusMap.data() + static_cast<size_t>(y) * w : nullptr;
    for (int x = 0; x < w; ++x) {
      float t;
      if (dRow) {
        // Interpolated between the two bracketing anchors: an anchor edge on a
        // field this smooth would otherwise draw a contour across the screen.
        const float fa =
            (defocusSpan * (static_cast<float>(dRow[x]) / 255.0f)) /
            (defocusStep > 0.0f ? defocusStep : 1.0f);
        int a0 = static_cast<int>(fa);
        if (a0 < 0) a0 = 0;
        if (a0 > anchors - 1) a0 = anchors - 1;
        const int a1 = a0 + 1 < anchors ? a0 + 1 : a0;
        const float fr = fa - static_cast<float>(a0);
        const float *cell = tRow + static_cast<size_t>(bRow[x]) * anchors;
        t = cell[a0] + (cell[a1] - cell[a0]) * fr;
      } else {
        t = tRow[bRow[x]];
      }
      const uint32_t m = scanlines::combine(params, t, x, y, w, h);
      row[x] = 0xFF000000u | (m << 16) | (m << 8) | m;
    }
  }
  if (!SDL_UpdateTexture(scanTexture, nullptr, field.data(),
                         static_cast<int>(w * sizeof(uint32_t)))) {
    LOG_ERR("DISP", "scanlines: could not upload the field (%s)",
            SDL_GetError());
    destroyScanTexture();
    return false;
  }
  SDL_SetTextureBlendMode(scanTexture, SDL_BLENDMODE_MOD);
  // Drawn 1:1; pinned to NEAREST so a half-pixel rect can never smear the
  // raster into a gray wash.
  SDL_SetTextureScaleMode(scanTexture, SDL_SCALEMODE_NEAREST);
  scanTexW = w;
  scanTexH = h;
  scanTexSeq = seq;
  scanTexIntensity = intensity;
  scanTexKey = palKey;
  scanTexPitchKey = pitchKey;
  scanTexBloom = bloom;
  scanTexDefocus = cd.strengthPercent;
  if (timingLogWanted()) {
    timingFrame.scanlines.built = true;
    timingFrame.scanlines.ms =
        static_cast<double>(SDL_GetTicksNS() - scanT0) / 1.0e6;
  }
  if (const char *e = std::getenv("CROSSPOINT_SIM_LOG_PRESENTS"))
    if (e[0] == '1')
      SDL_Log("[scanlines] field %dx%d intensity %d pitch %.3f px/line "
              "mottle %.2f bloom %d%% defocus %d%% (corner spot %.3fx, "
              "astigmatism %.3f) seed %u budget %.3f",
              w, h, intensity, static_cast<double>(pitchPx),
              static_cast<double>(params.mottleDepth), bloom,
              cd.strengthPercent,
              static_cast<double>(cornerdefocus::maxSigmaScale(cd)),
              static_cast<double>(cornerdefocus::astigmatismRatio(cd)), seed,
              static_cast<double>(params.budgetMeanDarkening));
  return true;
}

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

  // Service inversion changes first: reconverting sets pendingPresent, so the
  // repolarized pixels ride the present below instead of waiting for the
  // firmware to refresh.
  if (pendingReconvert.exchange(false))
    reconvertLastFrame();

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
  if (!displaySleeping.load()) lastReadingDarkGround = panelIsDarkGround();

  // The timing frame is armed HERE, past every early return, so a present that
  // was held or coalesced away is not reported as a free one.
  if (timingLogWanted()) {
    timingFrame = PresentTiming{};
    timingFrame.startNs = SDL_GetTicksNS();
  }

  extern GfxRenderer renderer;
  const GfxRenderer::Orientation orientation = renderer.getOrientation();
  applyWindowGeometryIfNeeded(orientation);

  // PHOSPHOR GLOW. The old picture has to be copied before SDL_UpdateTexture
  // overwrites `texture` in place, so this sits above the upload rather than
  // below it. Only when the content actually CHANGED: a re-present of the same
  // frame (a window resize, a screenshot) must not restart a trail, or the page
  // would ghost while nothing happened.
  // Entering deep sleep: whatever presents from here on is the frame the glass
  // holds for the whole sleep, so the beam and the trail are treated as OFF and
  // the existing off-paths below settle everything (ghost dropped, accumulator
  // destroyed, no self-requested next frame). See displaySleeping's comment for
  // the owner report this closes and why deepSleep() cannot settle it alone.
  const bool sleepSettled = displaySleeping.load();
  const float trailMs = sleepSettled ? 0.0f : glowTrailMs.load();
  const float beamMs = sleepSettled ? 0.0f : beamPaintMs.load();
  // The beam needs the PREVIOUS frame for the same reason the glow does -- it
  // is what is still on screen below the sweep -- so the capture is gated on
  // either wanting it, not on the glow alone.
  const bool wantPrevFrame = trailMs > 0.0f || beamMs > 0.0f;
  bool contentChanged = false;
  {
    const std::lock_guard<std::mutex> lock(pixelBufMutex);
    const size_t live = static_cast<size_t>(activeWidth()) * activeHeight();
    if (wantPrevFrame) {
      // One integer, not 15 MB. A seq the ghost has not seen means the firmware
      // (or a polarity reconvert) wrote a new picture since the last capture.
      contentChanged = pixelBufSeq != ghostSeq || ghostPixels.size() != live;
      ghostSeq = pixelBufSeq;
      if (contentChanged) {
        ensureGhostTexture();
        if (ghostTexture && !ghostPixels.empty() &&
            ghostPixels.size() == live) {
          // Upload the PREVIOUS pixels; `texture` is about to become the new
          // ones on the very next line.
          SDL_UpdateTexture(ghostTexture, nullptr, ghostPixels.data(),
                            activeWidth() * sizeof(uint32_t));
          // The deposit's copy is INTENSITY, not color -- see
          // ensureGhostIntensityTexture. Only the glow deposits, so only the
          // glow pays for the conversion; the beam keeps the colored ghost.
          if (trailMs > 0.0f) {
            ensureGhostIntensityTexture();
            if (ghostIntensityTexture) {
              static std::vector<uint32_t> intensityBuf;
              intensityBuf.resize(live);
              for (size_t i = 0; i < live; i++) {
                const uint32_t px = ghostPixels[i];
                uint32_t m = (px >> 16) & 0xFFu;
                const uint32_t g = (px >> 8) & 0xFFu;
                const uint32_t b = px & 0xFFu;
                if (g > m) m = g;
                if (b > m) m = b;
                intensityBuf[i] = 0xFF000000u | (m << 16) | (m << 8) | m;
              }
              SDL_UpdateTexture(ghostIntensityTexture, nullptr,
                                intensityBuf.data(),
                                activeWidth() * sizeof(uint32_t));
            }
          }
          ghostStartedAt = SDL_GetTicks();
          beamStartedAt = ghostStartedAt;
          ghostHasPicture = true;
        }
        ghostPixels.assign(pixelBuf, pixelBuf + live);
      }
    } else if (!ghostPixels.empty()) {
      // Turned off: drop the copy rather than keep paying for it.
      ghostPixels.clear();
      ghostStartedAt = 0;
      beamStartedAt = 0;
      ghostHasPicture = false;
    }
    // Pitch is the ACTIVE row stride. pixelBuf is allocated for the ceiling,
    // so at a lower scale the live picture occupies a prefix of it and the
    // ceiling's pitch would stride past every row.
    SDL_UpdateTexture(texture, nullptr, pixelBuf,
                      activeWidth() * sizeof(uint32_t));
  }

  // FADE THE ACCUMULATOR BY ELAPSED TIME, THEN DEPOSIT THE PAGE JUST REPLACED.
  //
  // Order matters and is physical: what is already in there has been decaying
  // since the last present, and the frame being replaced starts decaying only
  // from now. Fading first and adding second is what makes a contribution's
  // age its own.
  bool accumLive = false;
  if (trailMs > 0.0f && ghostTexture) {
    ensureAccumTexture();
    if (accumTexture) {
      const uint64_t now = SDL_GetTicks();
      const float dt = static_cast<float>(now - accumLastFadeMs);
      accumLastFadeMs = now;
      SDL_Texture *restore = SDL_GetRenderTarget(sdl_renderer);
      SDL_SetRenderTarget(sdl_renderer, accumTexture);
      // dst *= 10^(-dt/trail), expressed as a blend against black. This is the
      // SAME curve the single-ghost version used; it is just applied to a
      // running sum instead of to one frame.
      if (dt > 0.0f) {
        const float keep = SDL_powf(10.0f, -dt / trailMs);
        const int drop = static_cast<int>((1.0f - keep) * 255.0f + 0.5f);
        if (drop > 0) {
          SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_BLEND);
          SDL_SetRenderDrawColor(sdl_renderer, 0, 0, 0,
                                 static_cast<Uint8>(SDL_min(255, drop)));
          SDL_RenderFillRect(sdl_renderer, nullptr);
        }
      }
      // ONLY IF THE GHOST ACTUALLY HOLDS A PICTURE. The upload above is
      // skipped when ghostPixels is empty -- the first content change after the
      // glow turns on -- and a STREAMING texture's contents are undefined until
      // written. Depositing it anyway put garbage into the accumulator at the
      // exact moment the owner picked a phosphor, and on a re-entry it
      // deposited the last page of the PREVIOUS phosphor session, because
      // ghostTexture outlives ghostPixels.
      if (contentChanged && ghostHasPicture) {
        // The page that was just replaced is what glows. Deposited at full
        // strength, 1:1 -- both textures are the panel's own size.
        //
        // MAXIMUM, NOT ADD -- and this is S-016. The COMPOSITE to screen was
        // changed to MAXIMUM for a reason that applies word for word here and
        // was never carried across: a pixel lit in two frames is one phosphor
        // being re-excited, not two emitters stacked, so it cannot exceed full
        // emission. The deposit kept summing.
        //
        // Unbounded, and the bound that mattered was the decay. A short trail
        // drains the buffer to near black before the next deposit lands, so the
        // sum never builds; a long one does not. At P7's 2828 ms with content
        // changing every 100 ms, `keep` is 10^(-100/2828) = 0.92 per frame and
        // the running sum tends toward roughly 12x a single page. At P45's
        // 283 ms it settles near 1.8x. That is precisely the report -- "it seems
        // to be the long persistence ones" -- and it is why the short-trail
        // palettes looked fine.
        //
        // Same fallback shape as the composite: if the renderer cannot compose
        // MAXIMUM, take ADD at reduced strength rather than nothing, because
        // half a trail beats no trail.
        static SDL_BlendMode depositMax = SDL_ComposeCustomBlendMode(
            SDL_BLENDFACTOR_ONE, SDL_BLENDFACTOR_ONE, SDL_BLENDOPERATION_MAXIMUM,
            SDL_BLENDFACTOR_ONE, SDL_BLENDFACTOR_ONE, SDL_BLENDOPERATION_MAXIMUM);
        // The INTENSITY copy, so the composite's color mod can recolor the
        // trail toward the tail (see ensureGhostIntensityTexture). Falling
        // back to the colored ghost only if the intensity texture could not be
        // created: a wrongly-tinted trail beats no trail.
        SDL_Texture *deposit =
            ghostIntensityTexture ? ghostIntensityTexture : ghostTexture;
        if (depositMax == SDL_BLENDMODE_INVALID ||
            !SDL_SetTextureBlendMode(deposit, depositMax)) {
          SDL_SetTextureBlendMode(deposit, SDL_BLENDMODE_ADD);
          SDL_SetTextureAlphaMod(deposit, 96);
        } else {
          SDL_SetTextureAlphaMod(deposit, 255);
        }
        SDL_SetTextureColorMod(deposit, 255, 255, 255);
        SDL_RenderTexture(sdl_renderer, deposit, nullptr, nullptr);
        accumLastAddMs = now;
      }
      SDL_SetRenderTarget(sdl_renderer, restore);
      // Still emitting? A deposit is spent once it has decayed below one 8-bit
      // step, which is 10^-2.4 trails. Past that the accumulator is black and
      // asking for more frames would be a permanent render loop.
      // AND ONLY ON A GROUND THAT SHOWS IT. A pale page draws no trail at all
      // (see the draw below), so keeping the accumulator "live" there bought
      // ~30 presents per redraw -- a full clear, a 15 MB texture upload and a
      // render-target pass each, for a picture identical to the last one.
      // Measured by the audit; it is pure waste and it is also battery.
      accumLive = panelIsDarkGround() && accumLastAddMs != 0 &&
                  static_cast<float>(now - accumLastAddMs) < trailMs * 2.4f;
    }
  } else if (accumTexture) {
    // Glow turned off: drop the buffer rather than keep paying for it.
    SDL_DestroyTexture(accumTexture);
    accumTexture = nullptr;
    accumLastAddMs = 0;
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
    if (pagefade::stillMoving(age, fadeMs, floor)) pendingPresent.store(true);
  }
  if (const char *e = std::getenv("CROSSPOINT_SIM_LOG_PRESENTS"))
    if (e[0] == '1' && fadeMs > 0.0f)
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

  // THE BEAM. How far down the visible page the sweep has got, 0..1.
  //
  // The clip rect is in the CURRENT render coordinate space, which is the same
  // space the panel rect was computed in -- output pixels on the manual path,
  // logical units under SDL's letterbox -- so the same rect serves both. It is
  // also why the clip is expressed against the VISIBLE page rather than against
  // the texture: in portrait the texture is rotated, so a band of texture rows
  // is a band of screen COLUMNS, and clipping in texture space would sweep
  // sideways.
  float beamProgress = 1.0f;
  const bool beamActive =
      beamMs > 0.0f && beamStartedAt != 0 && ghostTexture && !ghostPixels.empty();
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
    // not been repainted yet, so it is not a ghost of anything.
    SDL_SetTextureBlendMode(ghostTexture, SDL_BLENDMODE_NONE);
    SDL_SetTextureAlphaMod(ghostTexture, 255);
    SDL_SetTextureColorMod(ghostTexture, 255, 255, 255);
    drawPanel(ghostTexture);
    // ...and above it, only as much of the new frame as the beam has written.
    const int swept =
        static_cast<int>(static_cast<float>(visible.h) * beamProgress);
    const SDL_Rect clip = {visible.x, visible.y, visible.w, swept};
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

  // The ghost goes ON TOP of the new page and fades out, which is what a
  // phosphor does: the old picture is still emitting while the new one is
  // written over it. Same rects and the same rotation as the panel above, so it
  // lands exactly on the panel however the panel was placed.
  // THE ACCUMULATOR GOES ON TOP of the new page, which is what a phosphor does:
  // everything written recently is still emitting while the new page is drawn
  // over it. Same rects and rotation as the panel, so it lands exactly on the
  // panel however the panel was placed.
  //
  // This draws the SUM of every recent page, not the last one. Flipping ten
  // pages in a second leaves ten deposits in there, each already faded by its
  // own age.
  if (const char *e = std::getenv("CROSSPOINT_SIM_LOG_PRESENTS"))
    if (e[0] == '1')
      SDL_Log("[accum] trail %.0f live=%d tex=%d changed=%d lastAdd=%llu",
              trailMs, (int)accumLive, accumTexture ? 1 : 0,
              (int)contentChanged, (unsigned long long)accumLastAddMs);
  if (accumLive && accumTexture) {
    // Whatever filter the panel ended up with, the trail must match: they are
    // the same picture moments apart, and a different resample would make the
    // trail shimmer against the page it is fading off.
    SDL_ScaleMode panelMode = kPanelScaleMode;
    SDL_GetTextureScaleMode(texture, &panelMode);
    SDL_SetTextureScaleMode(accumTexture, panelMode);

    const bool darkGround = panelIsDarkGround();

    // A PHOSPHOR ADDS LIGHT, and the accumulator is a buffer OF LIGHT: black
    // wherever nothing has been emitted. That composites one way and one way
    // only -- additively, onto a dark ground.
    //
    // IT USED TO CROSS-DISSOLVE ON A PALE GROUND, and that was wrong from the
    // moment this became an accumulator (build 90). The single-ghost version it
    // replaced held a real PICTURE -- the previous frame, paper and all -- so
    // blending it over a pale page was a sensible dissolve. The accumulator
    // holds light on black, so blending it at alpha 128 over a pale page draws
    // 50% BLACK across the whole sheet: the page turns gray and the previous
    // page's text hangs there inside it. Reported from the phone with a
    // screenshot, on the CRT schemes in light mode.
    //
    // So on a pale ground there is no trail at all. That is not a regression
    // against the pre-accumulator behaviour so much as an admission of what the
    // comment here already said: a glowing page is a dark-ground idea, and
    // adding light to white paper cannot express it.
    if (!darkGround) {
      accumLive = false;
    } else {
      // MAXIMUM, NOT ADD -- and this is the difference between a trail and a
      // flash.
      //
      // Measured on screen: with ADD, the frame at a page turn is the
      // arithmetic SUM of the old page and the new one. 99.77% of the page is
      // brighter than either, and |frame - (old+new)| averages 0.11 of a level.
      // Mean page luminance jumped 38.6 -> 71.8, +86%, decaying over a second.
      // That is the flash the owner reported, and it survived the double-draw
      // fix because ADD was doing it honestly all along.
      //
      // The physics were wrong, not the arithmetic. A pixel lit in BOTH frames
      // is one phosphor being re-excited, not two emitters stacked -- it cannot
      // exceed full emission. Summing says otherwise and doubles the page.
      // Taking the MAXIMUM is the saturating model: a pixel the new page lights
      // stays exactly as bright as the new page draws it, and a pixel only the
      // OLD page lit still shows, decaying, which is the whole point of the
      // trail.
      //
      // SDL_BLENDOPERATION_MAXIMUM ignores the blend factors, so the accumulator
      // is composited unscaled. If a renderer cannot compose it (the call
      // fails), fall back to ADD at reduced strength rather than to nothing:
      // half a trail beats a flash.
      static SDL_BlendMode maxBlend = SDL_ComposeCustomBlendMode(
          SDL_BLENDFACTOR_ONE, SDL_BLENDFACTOR_ONE, SDL_BLENDOPERATION_MAXIMUM,
          SDL_BLENDFACTOR_ONE, SDL_BLENDFACTOR_ONE, SDL_BLENDOPERATION_MAXIMUM);
      if (maxBlend == SDL_BLENDMODE_INVALID ||
          !SDL_SetTextureBlendMode(accumTexture, maxBlend)) {
        SDL_SetTextureBlendMode(accumTexture, SDL_BLENDMODE_ADD);
        SDL_SetTextureAlphaMod(accumTexture, 96);
      } else {
        SDL_SetTextureAlphaMod(accumTexture, 255);
      }
    }

    // A CASCADE PHOSPHOR CHANGES COLOUR AS IT DIES, and with an accumulator
    // that is an APPROXIMATION and is marked as one: the buffer holds deposits
    // of many ages mixed together, and one colour multiply cannot give each its
    // own point on the ramp. It is driven by the age of the NEWEST deposit,
    // which is the one carrying most of the brightness. Getting this exact
    // needs two accumulators running at the two layers' decay rates -- the
    // honest model of what a cascade physically is -- and that is worth doing
    // if this ever looks wrong.
    //
    // ONLY ON THE ADDITIVE PATH: on pale paper the same multiply hits the paper
    // too and the whole decaying frame washes green, which is a stain, not a
    // longer-lived layer.
    // THE ACCUMULATOR HOLDS INTENSITY, so the color mod is what paints the
    // trail -- and its ramp starts at the live INK, not white. The old deposit
    // held the page's own pixels and the mod ramped white -> tail, and a
    // multiply can only remove channels: green ink times an orange tail is
    // olive, never orange, so the tail mathematically could not win (owner
    // report 2026-08-21: a P46 green + P33 orange mix fades green for the
    // whole 2.8 s). No tail = a constant ink mod, which with intensity
    // deposits reproduces the single-phosphor look exactly.
    const uint32_t tail = glowTailTint.load();
    const PanelPalette livePal = livePanelPalette(display.isInverted());
    Uint8 mod[3] = {255, 255, 255};
    if (darkGround) {
      for (int c = 0; c < 3; c++) mod[c] = livePal.ink[c];
      if (tail != kNoGlowTail) {
        const float age = static_cast<float>(SDL_GetTicks() - accumLastAddMs);
        // The handover happens when the FAST phosphors die, not at the end of
        // the whole fade: for the reported mix that is ~17 ms into 2828, so
        // the ramp runs over the published ONSET when one exists. Presets
        // that never set one (onset 0) keep the old whole-trail timing.
        const float onset = glowTailOnsetMs.load();
        float t = onset > 0.0f
                      ? age / onset
                      : (trailMs > 0.0f ? age / trailMs : 1.0f);
        if (t < 0.0f) t = 0.0f;
        if (t > 1.0f) t = 1.0f;
        for (int c = 0; c < 3; c++) {
          const float target = static_cast<float>((tail >> (16 - 8 * c)) & 0xFF);
          mod[c] = static_cast<Uint8>(
              (1.0f - t) * static_cast<float>(mod[c]) + t * target + 0.5f);
        }
      }
    }
    SDL_SetTextureColorMod(accumTexture, mod[0], mod[1], mod[2]);
    if (const char *e = std::getenv("CROSSPOINT_SIM_LOG_PRESENTS"))
      if (e[0] == '1')
        SDL_Log("[accum2] darkGround=%d drawn=%d age=%u", (int)darkGround,
                (int)accumLive,
                (unsigned)(SDL_GetTicks() - accumLastAddMs));
    if (accumLive) drawPanel(accumTexture);

    // A fade only animates if something presents while it fades, and the
    // firmware will not: an e-ink reader draws a page and stops. So the trail
    // asks for its own next frame, and stops asking the moment it is done --
    // which is what keeps this from becoming a permanent render loop.
    pendingPresent.store(true);
  }


  if (beamSweeping) {
    SDL_SetRenderClipRect(sdl_renderer, nullptr);
    // A sweep only sweeps if something presents while it does, and an e-ink
    // firmware presents once per page. Same self-driving arrangement as the
    // glow's trail, and it stops asking the moment the beam reaches the bottom.
    pendingPresent.store(true);
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
  if (!display.isInverted() &&
      SimulatorOverlay::letterpressStrength.load() > 0) {
    if (ensureLetterpressTexture()) {
      SDL_ScaleMode panelMode = kPanelScaleMode;
      SDL_GetTextureScaleMode(texture, &panelMode);
      SDL_SetTextureScaleMode(letterpressTexture, panelMode);
      drawPanel(letterpressTexture);
    }
  } else if (letterpressTexture) {
    destroyLetterpressTexture();
  }

  // Overlay chrome lives in the letterboxed margins, which the panel's logical
  // coordinate space cannot address -- so drop logical presentation, hand the
  // painter real pixels, then restore it for the next frame.
  if (SimulatorOverlay::overlayDraw) {
    SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                     SDL_LOGICAL_PRESENTATION_DISABLED);
    int outW = 0, outH = 0;
    if (SDL_GetCurrentRenderOutputSize(sdl_renderer, &outW, &outH) && outW > 0)
      SimulatorOverlay::overlayDraw(sdl_renderer, outW, outH);
    int logW = 0, logH = 0;
    getLogicalPresentationSize(orientation, &logW, &logH);
    SDL_SetRenderLogicalPresentation(sdl_renderer, logW, logH,
                                     kLogicalPresentation);
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
  const bool darkNow = display.isInverted();
  const bool scanlinesActive =
      darkNow && SimulatorOverlay::scanlinesIntensity.load() > 0;
  const bool letterpressActive =
      !darkNow && SimulatorOverlay::letterpressStrength.load() > 0;

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
      if (ensureScanlinesTexture(outW, outH, pitch)) {
        const SDL_FRect full = {0.0f, 0.0f, static_cast<float>(outW),
                                static_cast<float>(outH)};
        SDL_RenderTexture(sdl_renderer, scanTexture, nullptr, &full);
      }
    }
    int logW = 0, logH = 0;
    getLogicalPresentationSize(orientation, &logW, &logH);
    SDL_SetRenderLogicalPresentation(sdl_renderer, logW, logH,
                                     kLogicalPresentation);
  } else if (scanTexture) {
    destroyScanTexture();
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
        ensureSheetToothTexture(outW, outH, outPxPerSourcePxAt(outW, outH))) {
      const SDL_FRect full = {0.0f, 0.0f, static_cast<float>(outW),
                              static_cast<float>(outH)};
      SDL_RenderTexture(sdl_renderer, sheetToothTexture, nullptr, &full);
    }
    int logW = 0, logH = 0;
    getLogicalPresentationSize(orientation, &logW, &logH);
    SDL_SetRenderLogicalPresentation(sdl_renderer, logW, logH,
                                     kLogicalPresentation);
  } else if (sheetToothTexture) {
    destroySheetToothTexture();
  }

  if (SimulatorOverlay::grainStrength.load() != phosphorgrain::kStrengthOff &&
      !scanlinesActive && !letterpressActive) {
    SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                     SDL_LOGICAL_PRESENTATION_DISABLED);
    int outW = 0, outH = 0;
    if (SDL_GetCurrentRenderOutputSize(sdl_renderer, &outW, &outH) && outW > 0 &&
        outH > 0 && ensureGrainTexture(outW, outH)) {
      const SDL_FRect full = {0.0f, 0.0f, static_cast<float>(outW),
                              static_cast<float>(outH)};
      SDL_RenderTexture(sdl_renderer, grainTexture, nullptr, &full);
    }
    int logW = 0, logH = 0;
    getLogicalPresentationSize(orientation, &logW, &logH);
    SDL_SetRenderLogicalPresentation(sdl_renderer, logW, logH,
                                     kLogicalPresentation);
  } else if (grainTexture) {
    destroyGrainTexture();
  }

  if (screenshotDue) {
    captureDueScreenshots();
  }
  // Opt-in present counter: the flash is a present that should not exist, and
  // counting presents is the only way to see it headlessly (a screenshot
  // deliberately overrides the hold, so it cannot photograph its own absence).
  if (const char *env = std::getenv("CROSSPOINT_SIM_LOG_PRESENTS")) {
    if (env[0] == '1') {
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
  if (const char *env = std::getenv("CROSSPOINT_SIM_LOG_SCREEN")) {
    if (env[0] == '1') {
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
    SDL_Log("[timing] #%d total %.2f ms | panel %s %.2f | sheet %s %.2f | "
            "scanlines %s %.2f | grain %s %.2f | readback %s %.2f | "
            "flip %.2f",
            ++n, total, tag(timingFrame.letterpress),
            timingFrame.letterpress.ms, tag(timingFrame.sheet),
            timingFrame.sheet.ms, tag(timingFrame.scanlines),
            timingFrame.scanlines.ms, tag(timingFrame.grain),
            timingFrame.grain.ms, timingFrame.readback ? "yes" : "-",
            timingFrame.readbackMs, timingFrame.flipMs);
  }
}

// --- THE POWER-OFF COLLAPSING DOT (dark mode, at sleep) --------------------
//
// Roadmap D8. The model is src/PowerOffCollapse.h; this is the four draws it
// implies. It lives HERE rather than inside presentIfNeeded because it is not
// a present: the firmware has already gone, the page is not going to change
// again, and every frame below is one the app would not otherwise have drawn.
//
// It runs from HalGPIO::startDeepSleep's loop -- see the header's note on why
// that is the one place it cannot delay sleep.
namespace {
uint64_t collapseStartedAt = 0;
bool collapseFinished = false;

// The iOS wake is a longjmp back into setup() in the SAME process, so without
// this a second sleep in one session would find the animation already spent
// and show nothing. The desktop wake is execvp and clears it for free.
const simreset::Registrar gCollapseReset{[] {
  collapseStartedAt = 0;
  collapseFinished = false;
}};

// Draw the panel scaled by (sx, sy) about the PRESENTED page's centre, in
// output pixels.
//
// The scales are in SCREEN terms and the dst rect is not: SDL_RenderTextureRotated
// turns the landscape framebuffer about the dst rect's own centre, so in
// portrait the rect's width becomes the screen's HEIGHT and its height the
// screen's width. Squeezing the picture vertically therefore narrows the rect.
// Getting this backwards collapses the page sideways, which is a different
// television.
void drawCollapsedPanel(SDL_Texture *tex, float sx, float sy) {
  const float kW = static_cast<float>(HalDisplay::activeWidth());
  const float kH = static_cast<float>(HalDisplay::activeHeight());
  if (kW <= 0.0f || kH <= 0.0f || sheetPanelW <= 0 || sheetPanelH <= 0) return;
  const bool portrait = isPortraitOrientation(
      static_cast<GfxRenderer::Orientation>(sheetPanelOrientation));
  const float base =
      portrait ? static_cast<float>(sheetPanelW) / kH
               : static_cast<float>(sheetPanelW) / kW;
  const float cx = static_cast<float>(sheetPanelX) + sheetPanelW * 0.5f;
  const float cy = static_cast<float>(sheetPanelY) + sheetPanelH * 0.5f;
  const float dw = kW * base * (portrait ? sy : sx);
  const float dh = kH * base * (portrait ? sx : sy);
  const SDL_FRect dst = {cx - dw * 0.5f, cy - dh * 0.5f, dw, dh};
  switch (sheetPanelOrientation) {
  case GfxRenderer::Portrait:
    SDL_RenderTextureRotated(sdl_renderer, tex, nullptr, &dst, 90.0, nullptr,
                             SDL_FLIP_NONE);
    break;
  case GfxRenderer::PortraitInverted:
    SDL_RenderTextureRotated(sdl_renderer, tex, nullptr, &dst, -90.0, nullptr,
                             SDL_FLIP_NONE);
    break;
  case GfxRenderer::LandscapeClockwise:
    SDL_RenderTextureRotated(sdl_renderer, tex, nullptr, &dst, 180.0, nullptr,
                             SDL_FLIP_NONE);
    break;
  default:
    SDL_RenderTexture(sdl_renderer, tex, nullptr, &dst);
  }
}
}  // namespace

namespace SimulatorOverlay {
bool stepPowerOffCollapse() {
  // SAY WHY, ONCE. Four of the five ways this returns false are silent by
  // nature -- an owner who turned the row on and saw nothing has no way to
  // tell "off" from "light page" from "no geometry yet", and neither did the
  // first attempt at photographing it headlessly.
  const auto bail = [](const char *why) {
    static bool said = false;
    if (!said && powerLogWanted()) {
      said = true;
      SDL_Log("[power] collapse not drawn: %s", why);
    }
    return false;
  };
  if (!powerOffCollapse.load()) return bail("the dial is off");
  if (collapseFinished) return false;
  if (!sdl_renderer || !texture) return bail("no renderer or no frame");
  // A PAPER PAGE DOES NOT SWITCH OFF. Same gate the accumulator uses: this is
  // a CRT artifact, and on a pale ground it would be a page being eaten.
  if (!lastReadingDarkGround.load())
    return bail("the page being read was a pale ground");
  // Nothing has been presented yet, so there is no geometry to collapse and no
  // picture to collapse it from.
  if (sheetPanelW <= 0 || sheetPanelH <= 0)
    return bail("no presented panel rect yet");

  const uint64_t now = SDL_GetTicks();
  if (collapseStartedAt == 0) collapseStartedAt = now;
  poweroff::Params pp;
  pp.enabled = true;
  const poweroff::State st =
      poweroff::stateAt(pp, static_cast<float>(now - collapseStartedAt));

  SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                   SDL_LOGICAL_PRESENTATION_DISABLED);
  int outW = 0, outH = 0;
  SDL_GetCurrentRenderOutputSize(sdl_renderer, &outW, &outH);
  // BLACK, not the field colour. A tube with no supplies is not a dark page,
  // it is an unlit screen, and the surround has to go with the picture or the
  // collapse happens inside a lit rectangle.
  SDL_SetRenderDrawColor(sdl_renderer, 0, 0, 0, 255);
  SDL_RenderClear(sdl_renderer);

  if (st.showPicture) {
    SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_NONE);
    SDL_SetTextureAlphaMod(texture, 255);
    SDL_SetTextureColorMod(texture, 255, 255, 255);
    drawCollapsedPanel(texture, st.horizontalScale, st.verticalScale);
    // THE BRIGHTNESS RISE, as a second additive draw of the same picture --
    // the cathode is still delivering the same current into a smaller raster.
    // A colour mod cannot express it: SDL_SetTextureColorMod only ever
    // attenuates.
    if (st.gain > 1.0f) {
      const float over = (st.gain - 1.0f) / (poweroff::kGainMax - 1.0f);
      const int a = static_cast<int>(over * 255.0f + 0.5f);
      SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_ADD);
      SDL_SetTextureAlphaMod(
          texture, static_cast<Uint8>(a < 0 ? 0 : (a > 255 ? 255 : a)));
      drawCollapsedPanel(texture, st.horizontalScale, st.verticalScale);
      SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_NONE);
      SDL_SetTextureAlphaMod(texture, 255);
    }
  }

  // THE LINE, THEN THE DOT. One rect: the same object at two widths, in the
  // live phosphor's own colour, because the beam does not change what it is
  // made of on the way out.
  if (st.dotAlpha > 0.0f && st.dotWidthFrac > 0.0f) {
    const PanelPalette live = livePanelPalette(true);
    float lw = static_cast<float>(sheetPanelW) * st.dotWidthFrac;
    float lh = static_cast<float>(outH) * poweroff::kLineHeightFrac;
    if (lw < 1.0f) lw = 1.0f;
    if (lh < 1.0f) lh = 1.0f;
    const float cx = static_cast<float>(sheetPanelX) + sheetPanelW * 0.5f;
    const float cy = static_cast<float>(sheetPanelY) + sheetPanelH * 0.5f;
    const SDL_FRect bar = {cx - lw * 0.5f, cy - lh * 0.5f, lw, lh};
    const int a = static_cast<int>(st.dotAlpha * 255.0f + 0.5f);
    SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_ADD);
    SDL_SetRenderDrawColor(sdl_renderer, live.ink[0], live.ink[1], live.ink[2],
                           static_cast<Uint8>(a > 255 ? 255 : a));
    SDL_RenderFillRect(sdl_renderer, &bar);
    SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_NONE);
  }

  // THE COLLAPSE CANNOT BE PHOTOGRAPHED FROM presentIfNeeded, because it never
  // goes through it -- so the due-screenshot check runs here too. Without this
  // the one moment this feature exists for is the one moment headless QA
  // cannot see, which is the same hole CROSSPOINT_SIM_LOG_PRESENTS exists to
  // fill for the page-turn flash.
  if (hasDueScreenshot()) captureDueScreenshots();
  SDL_RenderPresent(sdl_renderer);
  if (st.finished) {
    collapseFinished = true;
    if (powerLogWanted())
      SDL_Log("[power] collapse finished after %u ms; the glass stays dark",
              (unsigned)(now - collapseStartedAt));
    return false;
  }
  return true;
}
}  // namespace SimulatorOverlay

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
  // be the frame nobody ever sees -- and it is the sleep screen.
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
    SDL_Log("[power] sleep screen flushed; transients settle while sleeping");
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
