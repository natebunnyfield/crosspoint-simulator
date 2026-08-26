#include "SurfacePower.h"

// THE POWER PATH'S COMPOSITING. Read src/SurfacePower.h first: it says what
// this boundary is and why the bindings below carry the original names.
//
// Everything under "the moved code" is verbatim from src/HalDisplay.cpp as of
// ddcfee6 -- not one expression retyped, because the gate on this extraction is
// that the collapse and the warm-up render byte-identical frames.

#include "HalDisplay.h"
#include "PowerOffCollapse.h"
#include "PowerOnWarmUp.h"
#include "SimulatorRebootResets.h"

#include <atomic>
#include <cstdlib>
#include <mutex>
#include <vector>

// The same alias HalDisplay.cpp declares, for the same reason.
using PanelPalette = panelpalette::Palette;

// --- BOUND STATE ------------------------------------------------------------
//
// One line per piece of HalDisplay.cpp the power path reads. Nothing here is
// owned by this file; every name is the name the moved code already used, so
// the bodies below need no edits at all. The size of this list is the honest
// measure of how entangled the power path was with the monolith.
static SDL_Renderer *&sdl_renderer = simpower::rendererRef();
static SDL_Texture *&texture = simpower::panelTextureRef();
static SDL_Texture *&scanTexture = simpower::scanFieldRef();
static SDL_Texture *&grainTexture = simpower::grainFieldRef();
static int &sheetPanelX = simpower::panelXRef();
static int &sheetPanelY = simpower::panelYRef();
static int &sheetPanelW = simpower::panelWRef();
static int &sheetPanelH = simpower::panelHRef();
static int &sheetPanelOrientation = simpower::panelOrientationRef();
static std::mutex &pixelBufMutex = simpower::pixelBufLockRef();
static std::atomic<bool> &lastReadingDarkGround =
    simpower::lastReadingDarkGroundRef();
static std::atomic<bool> &pendingPresent = simpower::pendingPresentRef();
static const SDL_RendererLogicalPresentation &kLogicalPresentation =
    simpower::logicalPresentationRef();

static bool (&powerLogWanted)() = simpower::powerLogWanted;
static bool (&hasDueScreenshot)() = simpower::hasDueScreenshot;
static void (&captureDueScreenshots)() = simpower::captureDueScreenshots;
static PanelPalette (&livePanelPalette)(bool) = simpower::livePanelPalette;
static bool (&isPortraitOrientation)(GfxRenderer::Orientation) =
    simpower::isPortraitOrientation;
static void (&getLogicalPresentationSize)(GfxRenderer::Orientation, int *,
                                          int *) =
    simpower::getLogicalPresentationSize;

// Three of HalDisplay.cpp's SimulatorOverlay-scoped statics, bound in that
// namespace so the moved bodies keep spelling them exactly as they did. These
// are references with internal linkage, not second definitions.
namespace SimulatorOverlay {
static std::atomic<uint32_t> &clearColor = simpower::overlayClearColorRef();
static DrawFn &overlayDraw = simpower::overlayDrawRef();
static std::atomic<bool> &powerOffCollapse = simpower::powerOffCollapseRef();
}  // namespace SimulatorOverlay

// --- the moved code ---------------------------------------------------------

// --- THE PAGE THE COLLAPSE SQUEEZES -----------------------------------------
//
// Owner ruling 2026-08-24: "when power off collapse is enabled, don't switch to
// showing sleep screen. use the existing screen as source for the effect." The
// tube switches off showing what was on it, which is the page, the menu, or
// whatever the reader was looking at -- never the screen the firmware drew to
// replace it.
//
// Two things carry that and they are not redundant. presentIfNeeded DROPS every
// present from deep-sleep entry onward (see the veto there), so the sleep screen
// reaches neither the glass nor `texture`; this copy is what makes that immune
// to timing. The sleep screen's own present is held for kPresentHoldMs and is
// normally still held when deepSleep() runs -- measured 2026-08-24, 30 ms of
// hold with ~5 ms of it spent -- but nothing GUARANTEES the firmware reaches
// deepSleep() inside that window, and one slow sleep-entry would arm the veto a
// frame late and silently put the sleep screen back in the collapse. The
// collapse re-uploads this copy on the frame it starts, so the source is the
// reading page whichever way that race went.
//
// Kept only while the dial is on, and re-copied only when the picture actually
// changes: one copy per page turn, not one per present. It used to sit beside
// `ghostPixels` in presentIfNeeded and share its shape and its cost; that copy
// went on 2026-08-26 when the phosphor moved to the whole glass
// (docs/whole-glass-crt.md), and this one stayed, because what the collapse
// wants is the PANEL FRAMEBUFFER of the reading page and not the composed
// screen. The reason for its placement is unchanged -- SDL_UpdateTexture
// overwrites `texture` in place, so a frame worth keeping has to be copied
// before the next one lands.
static std::vector<uint32_t> sleepSourcePixels;
static uint64_t sleepSourceSeq = 0;

// --- THE TUBE WARMING UP: what this boot inherited --------------------------
//
// The warm-up fires on a WAKE and on nothing else, and the signal it fires on
// is not "was this a power wake" but the stricter "did the tube actually go
// dark" -- the collapse sets kTubeOffEnv on the frame it starts, so the animated
// switch-OFF is what licenses the animated switch-ON. That gate answers the
// polarity question for free: the collapse only ever runs on a dark ground, so
// a build that woke into a pale page cannot have armed this.
//
// It travels as an ENVIRONMENT VARIABLE because it has to cross a reboot in two
// different ways: the desktop wake is execvp, where environ is what the child
// inherits and every static is reborn, and the iOS wake is a longjmp, where the
// statics survive but nothing is inherited from anywhere. One mechanism covers
// both. It is consumed (unset) once per boot, so a second launch cannot inherit
// a switch-off that already had its warm-up.
static constexpr const char *kTubeOffEnv = "CROSSPOINT_SIM_TUBE_OFF";

static bool warmUpArmed = false;       // this boot follows a tube switch-off
static uint64_t warmUpBootMs = 0;      // when this boot's display came up
static uint64_t warmUpStartedAt = 0;   // 0 until the first frame that shows it
static bool warmUpFinished = false;
// Log-once, at NAMESPACE scope rather than as a static local inside the bail
// lambda: an iOS wake is a longjmp and a function-local static survives it, so a
// second sleep/wake in one session would decline SILENTLY. begin() clears it
// with the rest. (The collapse's own bail still has the lambda-local shape; it
// is pre-existing and out of this change's scope.)
static bool warmUpBailSaid = false;
// Written from the firmware task (HalGPIO's event pump), read on the main
// thread. Every other flag here is main-thread only.
static std::atomic<bool> warmUpCanceled{false};

namespace {
// Draw the panel scaled by (sx, sy) about the PRESENTED page's centre, in
// output pixels. BOTH halves of the tube's life use it -- the collapse squeezes
// the raster shut at sleep, the warm-up opens it at wake -- which is why it
// sits above presentIfNeeded rather than beside either one.
//
// The scales are in SCREEN terms and the dst rect is not: SDL_RenderTextureRotated
// turns the landscape framebuffer about the dst rect's own centre, so in
// portrait the rect's width becomes the screen's HEIGHT and its height the
// screen's width. Scaling the picture vertically therefore narrows the rect.
// Getting this backwards runs the raster sideways, which is a different
// television.
void drawPanelAtRasterScale(SDL_Texture *tex, float sx, float sy) {
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

// Advance the warm-up by one frame, and say what the tube can currently show.
// An inactive state is the identity: the caller draws the ordinary present.
//
// WHERE THE CLOCK STARTS, and why the heater costs nothing. The animation is
// timed from the first frame that can show it, less whatever of the heater the
// boot has ALREADY spent -- a cold cathode and a booting firmware are the same
// dark glass, and charging the owner twice for it would be the one thing this
// feature must not do. Measured on the desktop: 1357 ms from the execvp wake to
// the first present, so the 80 ms heater is spent seventeen times over before
// there is a frame. An in-process iOS wake may beat it, which is exactly why
// the phase exists rather than being assumed away.
//
// THE COST TO A PAGE TURN IS TWO BOOLEANS. Every ordinary present -- every
// build that never turned the dial on, and every present after this has run
// once -- leaves on the first line.
poweron::State powerOnWarmUpFrame() {
  const poweron::State idle;  // active = false: nothing to draw
  // SAY WHY, ONCE. Four of the five ways this declines are silent by nature,
  // and an owner who turned the row on and saw nothing at wake has no way to
  // tell "off" from "not a wake" from "a pale page" -- the same hole the
  // collapse's bail log fills.
  const auto bail = [&](const char *why) {
    if (!warmUpBailSaid && powerLogWanted()) {
      warmUpBailSaid = true;
      SDL_Log("[power] warm-up not drawn: %s", why);
    }
    return idle;
  };
  if (!warmUpArmed || warmUpFinished) return idle;
  if (!SimulatorOverlay::powerOffCollapse.load())
    return bail("the dial is off");
  if (warmUpCanceled.load()) {
    warmUpFinished = true;
    return bail("a press skipped it");
  }
  // The reverse of the collapse's polarity trap, and MEASURED rather than
  // assumed (2026-08-23): the wake's Boot activity exits without presenting, so
  // the first post-wake present is already the reading polarity and this is a
  // guard rather than a latch. It needs no lastReadingDarkGround-style memory
  // because the arming flag already carries one -- the collapse only ever runs
  // on a dark ground, so a boot that armed this was a dark tube.
  if (!lastReadingDarkGround.load())
    return bail("the page this boot presents is a pale ground");
  if (sheetPanelW <= 0 || sheetPanelH <= 0)
    return bail("no presented panel rect yet");

  const uint64_t now = SDL_GetTicks();
  if (warmUpStartedAt == 0) {
    const uint64_t bootAge = now >= warmUpBootMs ? now - warmUpBootMs : 0;
    const uint64_t heater = static_cast<uint64_t>(poweron::kHeaterMs);
    const uint64_t credit = bootAge < heater ? bootAge : heater;
    warmUpStartedAt = now - credit;
    if (powerLogWanted())
      SDL_Log("[power] warm-up: boot already spent %u of the %u ms heater",
              (unsigned)credit, (unsigned)heater);
  }

  poweron::Params pp;
  pp.enabled = true;
  const poweron::State st =
      poweron::stateAt(pp, static_cast<float>(now - warmUpStartedAt));
  if (st.finished) {
    warmUpFinished = true;
    if (powerLogWanted())
      SDL_Log("[power] warm-up finished after %u ms; the page is untouched now",
              (unsigned)(now - warmUpStartedAt));
    return idle;  // this frame IS the ordinary present, byte for byte
  }
  // A warm-up only warms up if something presents while it does, and an e-ink
  // firmware presents once per page. Same self-driving arrangement as the beam
  // and the glow trail, and it stops asking the moment it is done -- which is
  // what keeps this from becoming a permanent render loop.
  pendingPresent.store(true);
  return st;
}
}  // namespace

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

// PUT THE READING PAGE BACK IN THE PANEL TEXTURE. presentIfNeeded has been
// dropping frames since deepSleep(), so `texture` should already hold it and
// this is a no-op re-upload of identical pixels -- it is here for the one case
// where it is not: a sleep-screen present that beat the veto by a frame. Called
// once, on the frame the collapse starts, and nothing else writes the panel
// texture while the device is asleep. Silent when there is no copy (the dial
// was turned on after the last present), which leaves the previous behaviour
// rather than a black panel.
void restoreSleepSourceFrame() {
  if (!texture) return;
  const std::lock_guard<std::mutex> lock(pixelBufMutex);
  const size_t live = static_cast<size_t>(HalDisplay::activeWidth()) *
                      HalDisplay::activeHeight();
  if (sleepSourcePixels.size() != live) return;
  SDL_UpdateTexture(texture, nullptr, sleepSourcePixels.data(),
                    HalDisplay::activeWidth() * sizeof(uint32_t));
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
  if (collapseFinished) {
    // THE GLASS IS BLACK FOR THE REST OF THE SLEEP, AND THAT IS PHOTOGRAPHABLE.
    // The sleep loop owns the thread, so presentIfNeeded is not running, and
    // from 2026-08-24 its own capture is behind the sleep-screen veto -- so
    // without this the terminal state is the one state headless QA cannot ask
    // for, which is the same hole the due-screenshot check below fills for the
    // animation itself. Redrawn rather than read back: a presented backbuffer's
    // contents are undefined, and a garbage capture is worse than none.
    if (sdl_renderer && hasDueScreenshot()) {
      SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                       SDL_LOGICAL_PRESENTATION_DISABLED);
      SDL_SetRenderDrawColor(sdl_renderer, 0, 0, 0, 255);
      SDL_RenderClear(sdl_renderer);
      captureDueScreenshots();
      SDL_RenderPresent(sdl_renderer);
    }
    return false;
  }
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
  if (collapseStartedAt == 0) {
    collapseStartedAt = now;
    // THE SOURCE IS THE PAGE, NOT THE SLEEP SCREEN (owner, 2026-08-24).
    restoreSleepSourceFrame();
    // THE TUBE IS GOING DARK, so the next boot owes it a warm-up. Set here
    // rather than at sleep ENTRY because this is the first frame that actually
    // switches the tube off: every reason this function bails -- the dial, a
    // pale page, no frame yet -- has already been checked above, so the flag
    // means what it says and the warm-up needs no gate of its own.
    setenv(kTubeOffEnv, "1", 1);
  }
  poweroff::Params pp;
  pp.enabled = true;
  const poweroff::State st =
      poweroff::stateAt(pp, static_cast<float>(now - collapseStartedAt));

  SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                   SDL_LOGICAL_PRESENTATION_DISABLED);
  int outW = 0, outH = 0;
  SDL_GetCurrentRenderOutputSize(sdl_renderer, &outW, &outH);
  // PANEL AND PAPER ARE ONE PICTURE, AND THEY GO OUT TOGETHER (owner report
  // 2026-08-25: "panel and paper need to be painted at the same time on power
  // collapse and any other time, hold panel update if needed").
  //
  // This used to clear the whole output to BLACK and draw the raw panel on it,
  // which is a second, smaller composite than the one presentIfNeeded had just
  // put on the glass: no glass field, no chrome, no paper surround. All three
  // therefore disappeared on the collapse's OPENING frame, before the raster
  // had moved at all -- measured on the desktop at 1x with the as-shipped
  // dials, 100% of pixels stepping by exactly +1 code value with zero geometry
  // change, which is the dropped scanline field and nothing else. On a phone
  // the same frame also loses the letterboxed paper surround and the whole
  // button pad at once.
  //
  // The argument for black was never wrong, only mistimed: a tube with no
  // supplies IS an unlit screen. So the surround still ends black -- it just
  // gets there on the raster's own curve (poweroff::State::surroundVeil, zero
  // at t = 0), which makes the opening frame the identity this model has
  // always promised. It is the exact mirror of the warm-up, which lifts the
  // same chrome during Settle for the same reason.
  //
  // The order below is presentIfNeeded's order, deliberately -- field, picture,
  // chrome, glass. Reordering it is how the two composites drift apart again.
  const uint32_t collapseField = SimulatorOverlay::clearColor.load();
  SDL_SetRenderDrawColor(sdl_renderer, static_cast<Uint8>(collapseField >> 16),
                         static_cast<Uint8>(collapseField >> 8),
                         static_cast<Uint8>(collapseField), 255);
  SDL_RenderClear(sdl_renderer);
  // ...and the PAGE's own rect is unlit glass from the first frame the raster
  // leaves it, because what the picture vacates is not paper. At t = 0 the
  // picture covers this exactly, so it costs the identity nothing.
  {
    const SDL_FRect page = {
        static_cast<float>(sheetPanelX), static_cast<float>(sheetPanelY),
        static_cast<float>(sheetPanelW), static_cast<float>(sheetPanelH)};
    // The blend mode is set rather than inherited: this is the first draw of
    // the frame and the mode is whatever the last present happened to leave.
    // Every mode gives black here today, which is exactly the kind of accident
    // that stops being true when a pass is added above.
    SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_NONE);
    SDL_SetRenderDrawColor(sdl_renderer, 0, 0, 0, 255);
    SDL_RenderFillRect(sdl_renderer, &page);
  }

  if (st.showPicture) {
    SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_NONE);
    SDL_SetTextureAlphaMod(texture, 255);
    SDL_SetTextureColorMod(texture, 255, 255, 255);
    drawPanelAtRasterScale(texture, st.horizontalScale, st.verticalScale);
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
      drawPanelAtRasterScale(texture, st.horizontalScale, st.verticalScale);
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

  // THE CHROME, exactly where presentIfNeeded draws it and by the same call.
  // On a phone this is the button pad and the bezel; on the desktop the hook is
  // null and this whole block costs a branch. Logical presentation is already
  // disabled here, which is the state the painter is documented to want.
  if (SimulatorOverlay::overlayDraw && outW > 0)
    SimulatorOverlay::overlayDraw(sdl_renderer, outW, outH);

  // THE SURROUND GOING DARK, as four rects AROUND the page rather than one over
  // it -- veiling the page would undo the raster that is the whole animation.
  // Copied in shape from the warm-up's Settle branch on purpose: the two are
  // the same chrome moving in opposite directions, and a reader comparing them
  // should find the same four rects.
  if (st.surroundVeil > 0.0f) {
    int a = static_cast<int>(st.surroundVeil * 255.0f + 0.5f);
    if (a < 0) a = 0;
    if (a > 255) a = 255;
    SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_BLEND);
    SDL_SetRenderDrawColor(sdl_renderer, 0, 0, 0, static_cast<Uint8>(a));
    const float px = static_cast<float>(sheetPanelX);
    const float py = static_cast<float>(sheetPanelY);
    const float pw = static_cast<float>(sheetPanelW);
    const float ph = static_cast<float>(sheetPanelH);
    const SDL_FRect around[4] = {
        {0.0f, 0.0f, static_cast<float>(outW), py},
        {0.0f, py + ph, static_cast<float>(outW), outH - (py + ph)},
        {0.0f, py, px, ph},
        {px + pw, py, outW - (px + pw), ph},
    };
    for (const SDL_FRect &r : around)
      if (r.w > 0.0f && r.h > 0.0f) SDL_RenderFillRect(sdl_renderer, &r);
    SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_NONE);
  }

  // PUT THE GLASS BACK ON -- the same sentence, and the same two lines, as the
  // warm-up's handover. The clear above threw away the field the scanline (or
  // grain) pass drew into the frame presentIfNeeded last put up, and without
  // this the collapse's opening frame is that page with its screen texture
  // taken off. Both fields are fixed to the GLASS rather than to the page, so
  // re-drawing one over a squeezed raster is not an approximation: it is the
  // screen the picture is behind. At most one of the two ever exists -- each
  // present destroys the field it did not select -- so this needs no dial read
  // to pick between them, and null means the dials are off and there is
  // nothing to restore.
  {
    SDL_Texture *glass = scanTexture ? scanTexture : grainTexture;
    // SAY WHAT THE OPENING FRAME WAS MADE OF, ONCE. The whole point of this
    // block is that the collapse's first frame equals the last present, and a
    // missing glass texture makes that silently false again -- which is exactly
    // how the 2026-08-25 report was produced. One line, on the power log.
    static bool saidGlass = false;
    if (!saidGlass && powerLogWanted()) {
      saidGlass = true;
      SDL_Log("[power] collapse composite: field %06X, chrome %s, glass %s, "
              "out %dx%d, page %dx%d at %d,%d",
              (unsigned)collapseField,
              SimulatorOverlay::overlayDraw ? "drawn" : "none",
              scanTexture ? "scanlines" : (grainTexture ? "grain" : "NONE"),
              outW, outH, sheetPanelW, sheetPanelH, sheetPanelX, sheetPanelY);
    }
    if (glass && outW > 0 && outH > 0) {
      const SDL_FRect full = {0.0f, 0.0f, static_cast<float>(outW),
                              static_cast<float>(outH)};
      SDL_RenderTexture(sdl_renderer, glass, nullptr, &full);
    }
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

// A second SimulatorOverlay block rather than one: everything above is the
// collapse, moved whole and in its original order, and this is the warm-up's
// one public entry point, which lived elsewhere in HalDisplay.cpp. The seam is
// where the two moves meet.
namespace SimulatorOverlay {
// A FRESH PRESS ABANDONS THE WARM-UP. It is the one animation in this repo
// standing between the owner and a page he just asked for, so it has to be
// droppable; the collapse never needs this because the sleep loop checks for
// wakes before it steps.
//
// Only a press DOWN may skip. The release of the very tap that woke the device
// can still be in the queue when the rebooted firmware starts pumping events --
// on iOS the queue is not even a new one -- so accepting an UP would skip the
// warm-up on every wake, silently, and only on the phone.
void cancelPowerOnWarmUp() {
  if (warmUpFinished || !warmUpArmed) return;
  warmUpCanceled.store(true);
  // Bring the page at once rather than at the firmware's next render: the whole
  // point of a skip is that the reader stops waiting.
  pendingPresent.store(true);
}
}  // namespace SimulatorOverlay

namespace simpower {
// HalDisplay::begin()'s arming block, called from the same place and above the
// same idempotent early return.
void armPowerOnWarmUp() {
  // THE WARM-UP'S ARMING, and it is ABOVE the idempotent return below on
  // purpose: iOS wakes by re-entering setup() with the window already built, so
  // everything past that return is skipped on exactly the boot this feature
  // exists for. Consume rather than peek, so a launch that is not a wake cannot
  // inherit a switch-off that already had its warm-up.
  {
    const char *armed = std::getenv(kTubeOffEnv);
    warmUpArmed = armed && armed[0] == '1';
    unsetenv(kTubeOffEnv);
    // The desktop's way in without a sleep cycle: 1 arms the warm-up on a plain
    // launch (which is the only way to photograph it in one run), 0 suppresses
    // it. Unset is the honest path -- a wake, and nothing else.
    if (const char *env = std::getenv("CROSSPOINT_SIM_POWERON_WARMUP"))
      warmUpArmed = env[0] == '1';
    warmUpStartedAt = 0;
    warmUpFinished = false;
    warmUpBailSaid = false;
    warmUpCanceled.store(false);
    warmUpBootMs = SDL_GetTicks();
  }
}
// presentIfNeeded's keep/drop of the collapse's source page. CALLED WITH
// pixelBufMutex HELD -- do not lock in here.
void keepSleepSourceFrame(const uint32_t *pixelBuf, size_t live,
                          uint64_t pixelBufSeq, bool sleepSettled) {
    // KEEP THIS PAGE FOR THE COLLAPSE. Same guard as the polarity latch above
    // and for the same reason: what the fiction wants is the tube the reader
    // was looking at. Keyed on the seq rather than copied every present, so a
    // glow trail redrawing the same picture 60 times a second pays nothing.
    if (SimulatorOverlay::powerOffCollapse.load()) {
      if (!sleepSettled &&
          (sleepSourceSeq != pixelBufSeq || sleepSourcePixels.size() != live)) {
        sleepSourcePixels.assign(pixelBuf, pixelBuf + live);
        sleepSourceSeq = pixelBufSeq;
      }
    } else if (!sleepSourcePixels.empty()) {
      // Turned off: drop the copy rather than keep paying for it, exactly as
      // the ghost does.
      sleepSourcePixels.clear();
      sleepSourceSeq = 0;
    }
}
// presentIfNeeded's BZZT THONK pass, called from the same point in the same
// order -- after the grain and the scanlines. See the call site for why.
void compositeWarmUp(GfxRenderer::Orientation orientation,
                     bool scanlinesActive) {
  // --- BZZT THONK: THE TUBE WARMING UP (roadmap D8's other half) ------------
  //
  // The model is src/PowerOnWarmUp.h; this is the draws it implies. Unlike the
  // collapse, this one IS a present -- the firmware is booting underneath it
  // and the page has to be ready when the raster arrives -- so it composites
  // here rather than owning its own frame.
  //
  // AFTER THE GRAIN AND THE SCANLINES, and that placement is not taste. The
  // scanline field is built from a READBACK of the composed frame and cached
  // against the framebuffer's seq, so a black or half-open frame reaching that
  // readback would bake an all-dark beam-current map and hold it until the next
  // page turn. Everything above therefore composes the finished page normally;
  // this decides how much of it the tube is currently able to show.
  const poweron::State warm = powerOnWarmUpFrame();
  if (warm.active) {
    SDL_SetRenderLogicalPresentation(sdl_renderer, 0, 0,
                                     SDL_LOGICAL_PRESENTATION_DISABLED);
    int outW = 0, outH = 0;
    if (SDL_GetCurrentRenderOutputSize(sdl_renderer, &outW, &outH) &&
        outW > 0 && outH > 0) {
      const float cx = static_cast<float>(sheetPanelX) + sheetPanelW * 0.5f;
      const float cy = static_cast<float>(sheetPanelY) + sheetPanelH * 0.5f;
      float lh = static_cast<float>(outH) * poweron::kLineHeightFrac;
      if (lh < 1.0f) lh = 1.0f;

      if (warm.phase != poweron::Phase::Settle) {
        // BLACK, and the frame just composed goes with it. Same argument the
        // collapse makes: a tube with no raster is not a dark page, it is an
        // unlit screen, and the surround has to go with the picture or the
        // dot lights up inside a lit rectangle.
        SDL_SetRenderDrawColor(sdl_renderer, 0, 0, 0, 255);
        SDL_RenderClear(sdl_renderer);
        const PanelPalette live = livePanelPalette(true);

        // THE PICTURE, once the raster has height to carry it (the thonk).
        // Blended rather than opaque, because in the overshoot the raster is
        // OVERSCANNED and genuinely dimmer -- same beam over more glass -- and
        // the alpha is what expresses that.
        if (warm.showPicture) {
          const float lit = warm.drive < 1.0f ? warm.drive : 1.0f;
          SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_BLEND);
          SDL_SetTextureAlphaMod(texture,
                                 static_cast<Uint8>(lit * 255.0f + 0.5f));
          drawPanelAtRasterScale(texture, warm.horizontalScale,
                                 warm.verticalScale);
          // The rise, as a second additive draw of the same picture -- the
          // cathode is delivering the same current into a raster that is not
          // yet full. A colour mod cannot express it: SDL_SetTextureColorMod
          // only ever attenuates.
          if (warm.drive > 1.0f) {
            const float over =
                (warm.drive - 1.0f) / (poweron::kGainMax - 1.0f);
            int a = static_cast<int>(over * 255.0f + 0.5f);
            if (a > 255) a = 255;
            SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_ADD);
            SDL_SetTextureAlphaMod(texture, static_cast<Uint8>(a < 0 ? 0 : a));
            drawPanelAtRasterScale(texture, warm.horizontalScale,
                                   warm.verticalScale);
          }
          SDL_SetTextureBlendMode(texture, SDL_BLENDMODE_NONE);
          SDL_SetTextureAlphaMod(texture, 255);
        }

        // THE DOT, THEN THE LINE. One rect at two widths, in the live
        // phosphor's own colour, because the beam does not change what it is
        // made of on the way in either. It is the collapse's own bar run
        // backwards: relit as a dot, punched out sideways through the bzzt,
        // and dissolving into the raster during the thonk rather than being
        // replaced by it -- so the two never cross-fade through a gap.
        if (warm.lineAlpha > 0.0f && warm.lineWidthFrac > 0.0f) {
          float lw = static_cast<float>(sheetPanelW) * warm.lineWidthFrac;
          if (lw < 1.0f) lw = 1.0f;
          const SDL_FRect bar = {cx - lw * 0.5f, cy - lh * 0.5f, lw, lh};
          const int a = static_cast<int>(warm.lineAlpha * 255.0f + 0.5f);
          SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_ADD);
          SDL_SetRenderDrawColor(sdl_renderer, live.ink[0], live.ink[1],
                                 live.ink[2],
                                 static_cast<Uint8>(a > 255 ? 255 : a));
          SDL_RenderFillRect(sdl_renderer, &bar);
          SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_NONE);
        }

        // THE CRACKLE -- the bzzt's interference, full width across the GLASS
        // rather than across the page, because a supply fault is not a
        // property of the picture. Placed from the burst index, so the streaks
        // jump with each burst instead of crawling through it.
        if (warm.crackle > 0.0f) {
          const int a = static_cast<int>(warm.crackle * 190.0f + 0.5f);
          SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_ADD);
          SDL_SetRenderDrawColor(sdl_renderer, live.ink[0], live.ink[1],
                                 live.ink[2],
                                 static_cast<Uint8>(a > 255 ? 255 : a));
          for (int i = 0; i < poweron::kCrackleStreaks; ++i) {
            const float y = poweron::crackleRowFrac(warm.crackleBurst, i) *
                            static_cast<float>(outH);
            const SDL_FRect streak = {0.0f, y, static_cast<float>(outW),
                                      lh * 0.5f < 1.0f ? 1.0f : lh * 0.5f};
            SDL_RenderFillRect(sdl_renderer, &streak);
          }
          SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_NONE);
        }

        // PUT THE GLASS BACK ON. The clear above threw away the field the
        // scanline/grain pass had just drawn, and without this the raster's own
        // texture APPEARS at the handover -- measured 2026-08-23 as a 2.7% step
        // in mean luminance between the last thonk frame and the first settle
        // frame, which is a pop where there should be none. Both fields are
        // fixed to the GLASS rather than to the page, so re-drawing them over a
        // scaled raster is not an approximation: they are the screen, not the
        // picture. Dark mode only, so the two light-mode fields cannot be live.
        SDL_Texture *glass = scanlinesActive ? scanTexture : grainTexture;
        if (glass) {
          const SDL_FRect full = {0.0f, 0.0f, static_cast<float>(outW),
                                  static_cast<float>(outH)};
          SDL_RenderTexture(sdl_renderer, glass, nullptr, &full);
        }
      } else {
        // THE CHROME COMES UP AFTER THE PAGE. The letterbox margins on a
        // desktop and the button pad on a phone are not part of the firmware's
        // raster and cannot be scaled with it, so holding them dark across the
        // handover and lifting them here is what keeps the pad from appearing
        // whole in one frame. Four rects around the page, not one over it:
        // veiling the page would undo the raster that just slammed open.
        if (warm.surroundVeil > 0.0f) {
          int a = static_cast<int>(warm.surroundVeil * 255.0f + 0.5f);
          if (a > 255) a = 255;
          SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_BLEND);
          SDL_SetRenderDrawColor(sdl_renderer, 0, 0, 0,
                                 static_cast<Uint8>(a < 0 ? 0 : a));
          const float px = static_cast<float>(sheetPanelX);
          const float py = static_cast<float>(sheetPanelY);
          const float pw = static_cast<float>(sheetPanelW);
          const float ph = static_cast<float>(sheetPanelH);
          const SDL_FRect around[4] = {
              {0.0f, 0.0f, static_cast<float>(outW), py},
              {0.0f, py + ph, static_cast<float>(outW), outH - (py + ph)},
              {0.0f, py, px, ph},
              {px + pw, py, outW - (px + pw), ph},
          };
          for (const SDL_FRect &r : around)
            if (r.w > 0.0f && r.h > 0.0f) SDL_RenderFillRect(sdl_renderer, &r);
          SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_NONE);
        }
        // THE SUPPLIES COMING TO REST, as a MOD pass over the whole app
        // surface: darken-only, the same rule the grain, the scanlines and the
        // letterpress all obey. src/PowerOnWarmUp.h's driveAt is what
        // guarantees this branch never needs to LIFT -- an additive pass over
        // a dark ground is the page-flash bug class -- and it touches nominal
        // exactly at both ends, so neither the handover nor the last frame
        // steps.
        if (warm.drive < 1.0f) {
          int m = static_cast<int>(warm.drive * 255.0f + 0.5f);
          if (m < 0) m = 0;
          if (m > 255) m = 255;
          SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_MOD);
          SDL_SetRenderDrawColor(sdl_renderer, static_cast<Uint8>(m),
                                 static_cast<Uint8>(m), static_cast<Uint8>(m),
                                 255);
          const SDL_FRect full = {0.0f, 0.0f, static_cast<float>(outW),
                                  static_cast<float>(outH)};
          SDL_RenderFillRect(sdl_renderer, &full);
          SDL_SetRenderDrawBlendMode(sdl_renderer, SDL_BLENDMODE_NONE);
        }
      }
    }
    int logW = 0, logH = 0;
    getLogicalPresentationSize(orientation, &logW, &logH);
    SDL_SetRenderLogicalPresentation(sdl_renderer, logW, logH,
                                     kLogicalPresentation);
  }
}
}  // namespace simpower
