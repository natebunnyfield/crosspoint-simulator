#include "SurfaceTube.h"

// THE DARK PAGE'S COMPOSITING. Read src/SurfaceTube.h first: it says what this
// boundary is and why the bindings below carry the original names.
//
// Everything under "the moved code" is verbatim from src/HalDisplay.cpp as of
// aa16f90 -- not one expression retyped, because the gate on this extraction is
// that a rendered page is byte-identical to the one before the split.

#include "HalDisplay.h"

#include <Logging.h>

#include "CornerDefocus.h"
#include "FieldSelection.h"
#include "PhosphorGrain.h"
#include "Scanlines.h"
#include "SimulatorOverlay.h"

#include <atomic>
#include <cstdint>
#include <cstdlib>
#include <vector>

// The same alias HalDisplay.cpp declares, for the same reason.
using PanelPalette = panelpalette::Palette;
using simtiming::PresentTiming;

// --- BOUND STATE ------------------------------------------------------------
//
// One line per piece of HalDisplay.cpp the tube reads. Nothing here is owned by
// this file except the two fields themselves; every other name is the name the
// moved code already used, so the bodies below need no edits at all.
static SDL_Renderer *&sdl_renderer = simtube::rendererRef();
static uint64_t &pixelBufSeq = simtube::pixelBufSeqRef();
static PresentTiming &timingFrame = simtube::timingFrameRef();

static bool (&timingLogWanted)() = simtube::timingLogWanted;
static uint32_t (&grainSeed)() = simtube::grainSeed;
static PanelPalette (&livePanelPalette)(bool) = simtube::livePanelPalette;
static float (&srgbLumOf)(const unsigned char[3]) = simtube::srgbLumOf;

// HalDisplay.cpp's SimulatorOverlay-scoped dial statics, bound in that
// namespace so the moved bodies keep spelling them exactly as they did. These
// are references with internal linkage, not second definitions.
namespace SimulatorOverlay {
static std::atomic<int> &grainStrength = simtube::grainStrengthRef();
static std::atomic<int> &grainCoverage = simtube::grainCoverageRef();
static std::atomic<int> &grainMottleCells = simtube::grainMottleCellsRef();
static std::atomic<int> &grainMottleDepthPct = simtube::grainMottleDepthPctRef();
static std::atomic<int> &scanlinesIntensity = simtube::scanlinesIntensityRef();
static std::atomic<int> &scanlineBloom = simtube::scanlineBloomRef();
static std::atomic<int> &cornerDefocusStrength = simtube::cornerDefocusStrengthRef();
}  // namespace SimulatorOverlay

// --- the moved code ---------------------------------------------------------

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
      fieldselect::kRasterBudgetShare *
      phosphorgrain::darkeningBudget(srgbLumOf(live.ink),
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

// --- THE ENTRY POINTS -------------------------------------------------------
//
// Thin forwarders, so HalDisplay.cpp's call sites read the same shape they read
// for the sheet. The internal names above are the ones that moved; these are
// the only new spellings in this file.
namespace simtube {
bool ensureGrainField(int w, int h) { return ensureGrainTexture(w, h); }
SDL_Texture *grainField() { return grainTexture; }
void destroyGrainField() { destroyGrainTexture(); }
SDL_Texture *&grainFieldRef() { return grainTexture; }
bool ensureScanlinesField(int w, int h, float pitchPx) {
  return ensureScanlinesTexture(w, h, pitchPx);
}
SDL_Texture *scanField() { return scanTexture; }
void destroyScanField() { destroyScanTexture(); }
SDL_Texture *&scanFieldRef() { return scanTexture; }
}  // namespace simtube
