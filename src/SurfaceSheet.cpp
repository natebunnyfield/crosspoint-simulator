#include "SurfaceSheet.h"

// THE LIGHT PAGE'S COMPOSITING. Read src/SurfaceSheet.h first: it says what
// this boundary is and why the bindings below carry the original names.
//
// Everything under "the moved code" is verbatim from src/HalDisplay.cpp as of
// cab969b -- not one expression retyped, because the gate on this extraction is
// that a rendered page is byte-identical to the one before the split.

#include "HalDisplay.h"

#include <Logging.h>

#include "FieldSelection.h"
#include "LaidStructure.h"
#include "Letterpress.h"
#include "LightInkPalette.h"
#include "PaperDefects.h"
#include "PhosphorGrain.h"
#include "ShowThrough.h"
#include "SimulatorOverlay.h"
#include "SimulatorRebootResets.h"

#include <atomic>
#include <cstdint>
#include <cstdlib>
#include <mutex>
#include <vector>

// The same alias HalDisplay.cpp declares, for the same reason.
using PanelPalette = panelpalette::Palette;
using simtiming::PresentTiming;

// --- BOUND STATE ------------------------------------------------------------
//
// One line per piece of HalDisplay.cpp the sheet reads. Nothing here is owned
// by this file; every name is the name the moved code already used, so the
// bodies below need no edits at all.
static SDL_Renderer *&sdl_renderer = simsheet::rendererRef();
static int &sheetPanelX = simsheet::panelXRef();
static int &sheetPanelY = simsheet::panelYRef();
static int &sheetPanelW = simsheet::panelWRef();
static int &sheetPanelH = simsheet::panelHRef();
static int &sheetPanelOrientation = simsheet::panelOrientationRef();
static uint32_t *const pixelBuf = simsheet::pixelBufData();
static uint64_t &pixelBufSeq = simsheet::pixelBufSeqRef();
static std::mutex &pixelBufMutex = simsheet::pixelBufLockRef();
static PresentTiming &timingFrame = simsheet::timingFrameRef();

static bool (&timingLogWanted)() = simsheet::timingLogWanted;
static uint32_t (&pageSheetSeed)() = simsheet::pageSheetSeed;
static PanelPalette (&livePanelPalette)(bool) = simsheet::livePanelPalette;
static float (&srgbLumOf)(const unsigned char[3]) = simsheet::srgbLumOf;

// Nine of HalDisplay.cpp's SimulatorOverlay-scoped dial statics, bound in that
// namespace so the moved bodies keep spelling them exactly as they did. These are
// references with internal linkage, not second definitions.
namespace SimulatorOverlay {
static std::atomic<int> &letterpressStrength = simsheet::letterpressStrengthRef();
static std::atomic<int> &paperToothPct = simsheet::paperToothPctRef();
static std::atomic<int> &paperFormationPct = simsheet::paperFormationPctRef();
static std::atomic<int> &paperDefectsPct = simsheet::paperDefectsPctRef();
static std::atomic<int> &laidLinesStrength = simsheet::laidLinesStrengthRef();
static std::atomic<int> &showThroughStrength = simsheet::showThroughStrengthRef();
static std::atomic<int> &pressRingPct = simsheet::pressRingPctRef();
static std::atomic<int> &pressDebossPct = simsheet::pressDebossPctRef();
static std::atomic<int> &pressPressurePct = simsheet::pressPressurePctRef();
}  // namespace SimulatorOverlay

// --- the moved code ---------------------------------------------------------

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
  // OUTSIDE READING MODE THE MAPS FREEZE -- they are not cleared, and nothing
  // is promoted into them. Owner 2026-08-24: "do not have verso bleed outside
  // of reading mode."
  //
  // FREEZE rather than clear, which is the whole subtlety here. Clearing would
  // throw away the book's own verso every time you opened a menu, so coming
  // back to the page would show a blank back for one leaf. Returning early also
  // leaves versoSeed pinned to the page you left, so coming back to THAT page
  // promotes nothing -- it is the same leaf, and it is still the same leaf
  // after a trip through Settings.
  //
  // And it is what stops a MENU becoming the back of the next page you read.
  // The recto is downsampled below on every pass, so without this early return
  // the Settings screen would be the verso the next page turn promotes, and the
  // bleed inside reading mode would be showing something that was never a page.
  // That is the same ruling read the other way round.
  if (!SimulatorOverlay::sheetIsReaderPage()) return;
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
    // HOLD THE FIELD WHILE A TEXT FIELD IS OPEN. Owner 2026-08-24: "remove
    // eink delay." This pass is content-locked, so every keystroke was a new
    // seq and a full re-derivation -- measured that day in the note editor,
    // 53.6 ms of a 69 ms present, PER CHARACTER, with every other pass already
    // cached or off. On the phone the same pass covers four times the pixels.
    //
    // What is traded, stated plainly because it IS a fidelity loss: the field
    // keeps describing the glyphs it was built for, so while a line is being
    // typed the ink-squeeze rims and deboss sit where the PREVIOUS characters
    // were. It is faint and darken-only, and it re-registers on the first
    // present after the field closes, when the seq check applies again.
    //
    // Chosen over dropping the pass outright (owner picked it over that): the
    // paper stays visible the whole time, so nothing appears or disappears when
    // a keyboard opens. Deliberately NOT scoped to a HOST keyboard -- the seq
    // churn is the same whichever way characters arrive, and the firmware's own
    // on-screen grid pecking pays exactly the same 53.6 ms per pick.
    //
    // Only the SEQ is waived. Every other term still invalidates, so a palette
    // change, a dial move or a resize during text entry rebuilds normally.
    const bool holdForTextEntry =
        letterpressTexture && SimulatorOverlay::textEntryOpen();
    if (letterpressTexture && letterTexW == w && letterTexH == h &&
        (letterTexSeq == seq || holdForTextEntry) &&
        letterTexStrength == strength && letterTexKey == palKey &&
        letterTexRing == ringPct && letterTexDeboss == debossPct &&
        letterTexPress == pressPct) {
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

// The PRESENTED page rect these invert stayed in HalDisplay.cpp -- see
// simsheet::panelXRef() and the comment beside the statics there.

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
  // THE EFFECTIVE strength, not the dial. Off the reader this is kStrengthOff,
  // which is how the ruling reaches every consumer at once: stParams below, and
  // -- because sheetTexShowThrough is part of the sheet cache key -- the
  // invalidation too. Gating only the draw would have left a cached sheet with
  // the bleed baked into it being served on the screen that must not have it.
  const int showPct = SimulatorOverlay::sheetIsReaderPage()
                          ? SimulatorOverlay::showThroughStrength.load()
                          : showthrough::kStrengthOff;
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
  laidParams.budgetMeanDarkening = fieldselect::kSheetShareStep * paperLeft;
  float afterWires = paperLeft - laidstructure::meanDarkeningBound(laidParams);
  if (afterWires < 0.0f) afterWires = 0.0f;

  showthrough::Params stParams;
  stParams.strengthPercent = showPct;
  // The STOCK's factor is already folded into the percent by the pusher (the
  // iOS light picker composes lightink::showThroughScaleFor into it, the way
  // it composes tooth and formation), so this stays 1.0 and there is exactly
  // one authority for how thin the sheet is.
  stParams.stockScale = 1.0f;
  stParams.budgetMeanDarkening = fieldselect::kSheetShareStep * afterWires;

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

// --- THE ENTRY POINTS -------------------------------------------------------
//
// Thin, and deliberately named differently from the statics above so that the
// moved bodies keep spelling those exactly as they did.

namespace simsheet {

bool ensureLetterpressField() { return ensureLetterpressTexture(); }
SDL_Texture *letterpressField() { return letterpressTexture; }
void destroyLetterpressField() { destroyLetterpressTexture(); }

bool ensureSheetField(int w, int h, float outPxPerSourcePx) {
  return ensureSheetToothTexture(w, h, outPxPerSourcePx);
}
SDL_Texture *sheetField() { return sheetToothTexture; }
void destroySheetField() { destroySheetToothTexture(); }

}  // namespace simsheet
