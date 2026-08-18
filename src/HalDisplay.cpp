#include "HalDisplay.h"
#include "SimulatorRebootResets.h"

#include <GfxRenderer.h>
#include <Logging.h>
#include <SDL3/SDL.h>

#include "GrayscalePreview.h"
#include "PageFade.h"
#include "PanelPalette.h"
#include "SimulatorDeviceTruth.h"
#include "SimulatorOverlay.h"

#include <array>
#include <atomic>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <mutex>
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

PanelPalette livePanelPalette(bool dark) {
  return unpackPalette(dark ? panelPackedDark.load() : panelPackedLight.load());
}

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

bool presentFlashWanted() {
  static const bool wanted = [] {
    const char *env = std::getenv("CROSSPOINT_SIM_PRESENT_FLASH");
    return env && env[0] == '1';
  }();
  return wanted;
}

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
  if (!presentFlashWanted())
    presentHoldUntil.store(SDL_GetTicks() + kPresentHoldMs);
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
  presentHoldUntil.store(0);
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
  const PanelPalette pal = livePanelPalette(dark);
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

void setPanelGlowTail(const unsigned char tint[3]) {
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
  // Fourth time. Seed every host-only dial through its setter, or its env
  // override is dead on the desktop and cannot be tested there.
  SimulatorOverlay::setBeamPaint(0.0f);
  // Fifth time. Every host-only dial needs seeding through its setter or its
  // env override is dead on the desktop -- and this one had exactly that bug
  // for one build, which is how the first fade measurement showed no fade.
  SimulatorOverlay::setPageFade(0.0f);

  // Default appearance is light, so a desktop build stays byte-identical to
  // what it always rendered; CROSSPOINT_SIM_DARK is applied inside
  // setPanelDark, which is what lets a headless run force either polarity. A
  // host with a real appearance to follow (the iOS harness) calls
  // setPanelDark again with it once the harness installs.
  SimulatorOverlay::setPanelDark(false);
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

void HalDisplay::presentIfNeeded() {
  // Nothing may touch the GPU while backgrounded. Return BEFORE clearing
  // pendingPresent so the frame stays owed and lands on the way back in.
  if (g_backgrounded.load())
    return;

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

  extern GfxRenderer renderer;
  const GfxRenderer::Orientation orientation = renderer.getOrientation();
  applyWindowGeometryIfNeeded(orientation);

  // PHOSPHOR GLOW. The old picture has to be copied before SDL_UpdateTexture
  // overwrites `texture` in place, so this sits above the upload rather than
  // below it. Only when the content actually CHANGED: a re-present of the same
  // frame (a window resize, a screenshot) must not restart a trail, or the page
  // would ghost while nothing happened.
  const float trailMs = glowTrailMs.load();
  const float beamMs = beamPaintMs.load();
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
        // The page that was just replaced is what glows. Added at full
        // strength, 1:1 -- both textures are the panel's own size.
        SDL_SetTextureBlendMode(ghostTexture, SDL_BLENDMODE_ADD);
        SDL_SetTextureAlphaMod(ghostTexture, 255);
        SDL_SetTextureColorMod(ghostTexture, 255, 255, 255);
        SDL_RenderTexture(sdl_renderer, ghostTexture, nullptr, nullptr);
        accumLastAddMs = now;
      }
      SDL_SetRenderTarget(sdl_renderer, restore);
      // Still emitting? A deposit is spent once it has decayed below one 8-bit
      // step, which is 10^-2.4 trails. Past that the accumulator is black and
      // asking for more frames would be a permanent render loop.
      accumLive = accumLastAddMs != 0 &&
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
    const float floor = pagefade::floorFor(live.ink, live.paper);
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
      SDL_SetTextureBlendMode(accumTexture, SDL_BLENDMODE_ADD);
      SDL_SetTextureAlphaMod(accumTexture, 255);
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
    const uint32_t tail = glowTailTint.load();
    if (tail != kNoGlowTail && darkGround) {
      const float age = static_cast<float>(SDL_GetTicks() - accumLastAddMs);
      float t = trailMs > 0.0f ? age / trailMs : 1.0f;  // 0 fresh, 1 a trail old
      if (t > 1.0f) t = 1.0f;
      auto ramp = [&](int shift) {
        const float target = static_cast<float>((tail >> shift) & 0xFF) / 255.0f;
        return static_cast<Uint8>((1.0f - t + t * target) * 255.0f + 0.5f);
      };
      SDL_SetTextureColorMod(accumTexture, ramp(16), ramp(8), ramp(0));
    } else {
      SDL_SetTextureColorMod(accumTexture, 255, 255, 255);
    }
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
        SDL_DestroySurface(conv);
      }
      if (shot) SDL_DestroySurface(shot);
      int logW2 = 0, logH2 = 0;
      getLogicalPresentationSize(orientation, &logW2, &logH2);
      SDL_SetRenderLogicalPresentation(sdl_renderer, logW2, logH2,
                                       kLogicalPresentation);
    }
  }
  SDL_RenderPresent(sdl_renderer);
}

bool HalDisplay::shouldQuit() const { return quitRequested.load(); }

void HalDisplay::deepSleep() {
  // Flush any held base pass first. Sleep is the one caller with no "next
  // pass": the loop stops here, so a frame still inside the hold window would
  // be the frame nobody ever sees -- and it is the sleep screen.
  presentHoldUntil.store(0);
  presentIfNeeded();
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
