#pragma once

// THE ZEN READING GOAL'S CLOCK AND ITS PICTURE -- the SDL half of
// src/ReadingAllowance.h. Read that file first: it holds every decision about
// WHEN (the last minute, the zen restart, what counts as reading), and this
// one only keeps the clock running and draws what the model says.
//
// HEADER-ONLY, included by src/HalDisplay.cpp alone, for the reason
// FirmwareLogFile.h and ReadingLog.h are: cmake/CrossPointSources.cmake is
// generated from the firmware's compile database, and a new .cpp here would go
// stale in it the moment anyone regenerated it.
//
// THE TWO PICTURES the owner ruled (2026-09-24, from the mock-up page's options
// G and I):
//
//   LIGHT -- "too light of ink", redone on the page's own simulation (owner,
//   the same day: "take full advantage of the letterpress and ink and paper
//   simulation"). The starved plate kisses the sheet's tooth, its formation
//   and the plate's heavy patches first, a stroke's edges go before its core,
//   what survives thins toward the paper in the ink's own hue, and the
//   letterpress impression recedes with the pressure. Drawn as a paper-colored
//   veil whose alpha is the ink LOST at each pixel, over a letterpress field
//   composited at a fading weight -- so a paper pixel is never touched and the
//   sheet's own tooth, drawn later over the whole glass, stands.
//
//   DARK -- "too much emission". The beam overdriven: the glyphs bloom, swell
//   into one another, and the ground itself lifts toward the phosphor until the
//   page washes out. Drawn as three additive glows of the page's own EXCESS
//   light over its ground (so the dark ground itself never blooms), then a
//   ground lift in the ink's own colour.
//
// Both are drawn over the PANEL only, inside the beam's clip, right after the
// letterpress -- the same place and the same rotation as the page, because the
// decay is a property of this page and not of the glass.

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <vector>

#include "PanelPalette.h"
#include "ReadingAllowance.h"

namespace simallowance {

// The pure pixel math (tooth, ink retained, inkness, veil alpha, the excess
// glow) lives in src/ReadingAllowance.h so the host test can reach it.
using namespace readingallowance::picture;

// ---------------------------------------------------------------------------
// THE CLOCK -- main thread only (presentIfNeeded), so no locks. One session,
// restarted whenever zen starts; nothing persists (owner 2026-09-24).
// ---------------------------------------------------------------------------

struct Clock {
  readingallowance::Session session;
  uint64_t lastTickMs = 0;
  int lastStep = -1;         // quantized decay the glass last showed
};

inline Clock &clock() {
  static Clock c;
  return c;
}

// CROSSPOINT_SIM_READING_ALLOWANCE_USED=<seconds>: every zen start begins that
// far into the session. The headless way to render the decay at a chosen
// instant without waiting four minutes.
inline double qaPresetSeconds() {
  static const char *env = std::getenv("CROSSPOINT_SIM_READING_ALLOWANCE_USED");
  return env && env[0] ? std::atof(env) : 0.0;
}

// One pass of the main loop. Steps the session and returns the decay the
// glass should show (0 whenever zen is off or no book page is up). `stepChanged`
// is set when that decay has moved a quantum since the glass last showed it --
// the caller's cue to present.
inline double tick(bool zen, bool reading, bool bookPage, int minutes,
                   uint64_t nowMs, bool &stepChanged) {
  Clock &c = clock();
  stepChanged = false;
  const double dt =
      c.lastTickMs == 0 ? 0.0 : static_cast<double>(nowMs - c.lastTickMs) / 1000.0;
  c.lastTickMs = nowMs;
  if (c.session.step(zen, reading && minutes > 0, dt)) {
    const double preset = qaPresetSeconds();
    if (preset > 0.0) c.session.seconds = preset;
  }
  const double f = (zen && bookPage && minutes > 0)
                       ? readingallowance::decayFraction(c.session.seconds, minutes)
                       : 0.0;
  const int step = readingallowance::quantize(f);
  if (step != c.lastStep) {
    // A move between two clean states (the first pass's -1 -> 0) needs no
    // present; any move that has decay on either side does.
    stepChanged = step > 0 || c.lastStep > 0;
    c.lastStep = step;
  }
  return f;
}

// ---------------------------------------------------------------------------
// THE PICTURES -- main thread, inside presentIfNeeded.
// ---------------------------------------------------------------------------

struct Textures {
  SDL_Texture *veil = nullptr;
  int veilW = 0, veilH = 0;
  uint64_t veilSeq = ~0ull;
  int veilStep = -1;
  std::vector<uint32_t> veilPixels;
  // Per-page byte planes (mask, robbed, contact, blob): 4 bytes a pixel.
  std::vector<uint8_t> qMask, qRobbed, qContact, qBlob;
  uint32_t veilSeed = 0;
  int scale = 1;
  SDL_Texture *pressTarget = nullptr;  // the faded letterpress field
  int pressW = 0, pressH = 0;

  SDL_Texture *defocus = nullptr;

  SDL_Texture *glow[3] = {nullptr, nullptr, nullptr};
  uint64_t glowSeq = ~0ull;
  int glowW = 0, glowH = 0;
  SDL_Texture *lift = nullptr;
  SDL_Texture *halo = nullptr;
  SDL_Texture *retrace = nullptr;
  int retraceW = 0, retraceH = 0;
};

inline Textures &textures() {
  static Textures t;
  return t;
}

inline void destroyAll() {
  Textures &t = textures();
  if (!t.veil && !t.lift && !t.defocus && !t.pressTarget && !t.halo && !t.retrace && !t.glow[0] &&
      !t.glow[1] && !t.glow[2])
    return;
  if (t.pressTarget) SDL_DestroyTexture(t.pressTarget);
  if (t.veil) SDL_DestroyTexture(t.veil);
  for (SDL_Texture *&g : t.glow)
    if (g) SDL_DestroyTexture(g), g = nullptr;
  if (t.lift) SDL_DestroyTexture(t.lift);
  if (t.defocus) SDL_DestroyTexture(t.defocus);
  if (t.halo) SDL_DestroyTexture(t.halo);
  if (t.retrace) SDL_DestroyTexture(t.retrace);
  t = Textures{};
}

// LIGHT: the starved press. Rebuilt per PAGE (the ink, its interior, and the
// press's kiss off the page's own sheet seed) and per decay STEP (the alpha
// only). `pixels` is the presented panel (w*h ARGB), a copy the caller took
// under the pixel lock. See picture::printedFraction for the model.
template <typename DrawPanel>
inline void drawLight(SDL_Renderer *r, const uint32_t *pixels, int w, int h,
                      int scale, uint64_t seq, uint32_t sheetSeed, double f,
                      const panelpalette::Palette &pal, SDL_ScaleMode mode,
                      DrawPanel &&drawPanel) {
  Textures &t = textures();
  const int step = readingallowance::quantize(f);
  if (!t.veil || t.veilW != w || t.veilH != h || t.scale != scale) {
    t.scale = scale;
    if (t.veil) SDL_DestroyTexture(t.veil);
    t.veil = SDL_CreateTexture(r, SDL_PIXELFORMAT_ARGB8888,
                               SDL_TEXTUREACCESS_STREAMING, w, h);
    if (!t.veil) return;
    SDL_SetTextureBlendMode(t.veil, SDL_BLENDMODE_BLEND);
    t.veilW = w;
    t.veilH = h;
    t.veilSeq = ~0ull;
  }
  const bool newPage = t.veilSeq != seq || t.veilSeed != sheetSeed;
  if (newPage || t.veilStep != step) {
    const size_t n = static_cast<size_t>(w) * h;
    if (newPage) {
      // Per PAGE: the ink, the stroke interior (ink box-blurred one device
      // pixel), what the roller spent on the rows above (ghosting), and each
      // inked pixel's three terms -- kept as BYTES, with the float scratch
      // freed at the end. The adversarial review of 2026-09-24 measured the
      // first version at ~95 MB and hundreds of ms per page turn at 2x; the
      // noise is now evaluated only where there is ink (~15% of a page).
      std::vector<float> ink(n), tmp(n), interior(n), colSum(n);
      for (size_t i = 0; i < n; i++) ink[i] = inkness(pixels[i], pal);
      const int sc = std::max(1, scale);
      const int rad = sc;
      for (int y = 0; y < h; y++) {
        const float *row = &ink[static_cast<size_t>(y) * w];
        for (int x = 0; x < w; x++) {
          float sum = 0; int c = 0;
          for (int k = std::max(0, x - rad); k <= std::min(w - 1, x + rad); k++, c++) sum += row[k];
          tmp[static_cast<size_t>(y) * w + x] = sum / c;
        }
      }
      for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
          float sum = 0; int c = 0;
          for (int k = std::max(0, y - rad); k <= std::min(h - 1, y + rad); k++, c++)
            sum += tmp[static_cast<size_t>(k) * w + x];
          interior[static_cast<size_t>(y) * w + x] = sum / c;
        }
      // DEPLETION: the mean ink in the WIN framebuffer columns before this
      // one (the roller runs down the page = +x on the landscape framebuffer),
      // over a band of rows. Prefix sums along x of the row-band mean.
      const int win = 28 * sc, half = 6 * sc;
      for (int y = 0; y < h; y++) {
        float run = 0;
        const int y0 = std::max(0, y - half), y1 = std::min(h - 1, y + half);
        for (int x = 0; x < w; x++) {
          float v = 0; int c = 0;
          for (int k = y0; k <= y1; k += sc, c++) v += ink[static_cast<size_t>(k) * w + x];
          run += v / c;
          colSum[static_cast<size_t>(y) * w + x] = run;
        }
      }
      const uint32_t phase = phosphorgrain::hash3(sheetSeed, 0x524F4Cu, 7u);
      const float ph = static_cast<float>(phase & 0xFFFF) / 65535.0f;
      t.qMask.assign(n, 0);
      t.qRobbed.assign(n, 0);
      t.qContact.assign(n, 0);
      t.qBlob.assign(n, 0);
      for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
          const size_t i = static_cast<size_t>(y) * w + x;
          // Masked to the ink and one device pixel around it, so bare paper
          // is never veiled. The veil takes away (1 - printed) of WHATEVER ink
          // is there (an ink-weighted veil left a ghost).
          const float mask = std::min(1.0f, 6.0f * std::max(ink[i], interior[i]));
          if (mask <= 0.0f) continue;
          t.qMask[i] = static_cast<uint8_t>(mask * 255.0f + 0.5f);
          const int x0 = std::max(0, x - win), x1 = std::max(0, x - 1 - rad);
          float dep = 0.0f;
          if (x1 > x0) dep = (colSum[static_cast<size_t>(y) * w + x1] -
                              colSum[static_cast<size_t>(y) * w + x0]) / (x1 - x0);
          PressSample ps;
          ps.interior = interior[i];
          ps.tooth = smoothToothAt(x, y, sc, sheetSeed);
          const float nx = (x + 0.5f) / w, ny = (y + 0.5f) / h;
          ps.form = phosphorgrain::valueNoise(nx * 3.0f, ny * 3.0f, sheetSeed ^ 0x464F524Du);
          ps.plate = phosphorgrain::valueNoise(nx * 4.0f, ny * 4.0f, sheetSeed ^ 0x504C5445u);
          ps.depletion = std::min(1.0f, dep * 4.0f);
          ps.band = 0.5f + 0.5f * std::sin(6.2831853f * (nx * 2.7f + ph));
          ps.skip = phosphorgrain::valueNoise(x / (40.0f * sc), y / (40.0f * sc),
                                              sheetSeed ^ 0x534B4950u);
          t.qRobbed[i] = static_cast<uint8_t>(std::min(1.0f, robbedOf(ps) / 1.75f) * 255.0f + 0.5f);
          t.qContact[i] = static_cast<uint8_t>(std::min(1.0f, contactOf(ps)) * 255.0f + 0.5f);
          t.qBlob[i] = static_cast<uint8_t>(blobAt(x, y, sc, sheetSeed) * 255.0f + 0.5f);
        }
    }
    t.veilSeq = seq;
    t.veilSeed = sheetSeed;
    t.veilStep = step;
    const float tf = static_cast<float>(step) / 120.0f;
    const float supplyBase = tf > 0.0f && tf < 1.0f ? std::pow(1.0f - tf, 1.25f) : 0.0f;
    t.veilPixels.resize(n);
    const uint32_t rgb = (static_cast<uint32_t>(pal.paper[0]) << 16) |
                         (static_cast<uint32_t>(pal.paper[1]) << 8) | pal.paper[2];
    for (size_t i = 0; i < n; i++) {
      const uint8_t m = t.qMask[i];
      if (m == 0) { t.veilPixels[i] = rgb; continue; }   // bare paper: alpha 0
      const float printed = printedRaw(t.qRobbed[i] * (1.75f / 255.0f),
                                       t.qContact[i] * (1.0f / 255.0f),
                                       t.qBlob[i] * (1.0f / 255.0f), tf, supplyBase);
      const float a = (m * (1.0f / 255.0f)) * (1.0f - printed);
      t.veilPixels[i] = (static_cast<uint32_t>(a * 255.0f + 0.5f) << 24) | rgb;
    }
    SDL_UpdateTexture(t.veil, nullptr, t.veilPixels.data(), w * 4);
  }
  SDL_SetTextureScaleMode(t.veil, mode);
  drawPanel(t.veil);
}

// LIGHT: the letterpress field at a FADING weight -- the impression receding
// with the pressure. MOD cannot take an alpha, so the field is first composed
// over white at `pressLeft` into a target the page's size, and that is what
// MODs the page: white * (1 - a) + field * a, i.e. every darkening term of the
// press scaled by a. Returns false (and the caller draws the field at full
// strength) if the renderer cannot make a target.
template <typename DrawPanel>
inline bool drawFadedField(SDL_Renderer *r, SDL_Texture *field, int w, int h,
                           float left, SDL_ScaleMode mode, DrawPanel &&drawPanel) {
  Textures &t = textures();
  if (!t.pressTarget || t.pressW != w || t.pressH != h) {
    if (t.pressTarget) SDL_DestroyTexture(t.pressTarget);
    t.pressTarget = SDL_CreateTexture(r, SDL_PIXELFORMAT_ARGB8888,
                                      SDL_TEXTUREACCESS_TARGET, w, h);
    if (!t.pressTarget) return false;
    t.pressW = w;
    t.pressH = h;
  }
  SDL_Texture *prev = SDL_GetRenderTarget(r);
  if (!SDL_SetRenderTarget(r, t.pressTarget)) return false;
  Uint8 dr = 0, dg = 0, db = 0, da = 255;
  SDL_GetRenderDrawColor(r, &dr, &dg, &db, &da);
  SDL_SetRenderDrawColor(r, 255, 255, 255, 255);
  SDL_RenderClear(r);
  SDL_SetRenderDrawColor(r, dr, dg, db, da);
  SDL_BlendMode fieldBlend = SDL_BLENDMODE_MOD;
  SDL_GetTextureBlendMode(field, &fieldBlend);
  Uint8 fieldAlpha = 255;
  SDL_GetTextureAlphaMod(field, &fieldAlpha);
  SDL_SetTextureBlendMode(field, SDL_BLENDMODE_BLEND);
  SDL_SetTextureAlphaMod(field, static_cast<Uint8>(std::clamp(left, 0.0f, 1.0f) * 255.0f + 0.5f));
  SDL_RenderTexture(r, field, nullptr, nullptr);
  SDL_SetTextureBlendMode(field, fieldBlend);
  SDL_SetTextureAlphaMod(field, fieldAlpha);
  SDL_SetRenderTarget(r, prev);
  SDL_SetTextureBlendMode(t.pressTarget, SDL_BLENDMODE_MOD);
  SDL_SetTextureScaleMode(t.pressTarget, mode);
  drawPanel(t.pressTarget);
  return true;
}

// ---- DARK: THE OVERDRIVEN TUBE. picture::darkSchedule says how much of each
// failure is on; this builds the layers once per page and only moves alphas
// per step. Everything is at a reduced resolution and drawn LINEAR through
// drawPanel, which is what a fat, defocused beam looks like anyway.

// A plane of `coverage` (0..1) at w x h, box-downsampled by `f` from the
// page's excess light over `ground`, normalized by the ink's own excess.
inline void excessCoverage(const uint32_t *src, int w, int h, int f,
                           const uint8_t ground[3], const uint8_t ink[3],
                           std::vector<float> &out, int &ow, int &oh) {
  ow = std::max(1, w / f); oh = std::max(1, h / f);
  out.assign(static_cast<size_t>(ow) * oh, 0.0f);
  int span = 1;
  for (int c = 0; c < 3; c++) span = std::max(span, static_cast<int>(ink[c]) - ground[c]);
  const float inv = 1.0f / static_cast<float>(f * f * span);
  for (int y = 0; y < oh * f; y++)
    for (int x = 0; x < ow * f; x++) {
      const uint32_t px = src[static_cast<size_t>(y) * w + x];
      int best = 0;
      for (int c = 0; c < 3; c++)
        best = std::max(best, static_cast<int>((px >> (16 - 8 * c)) & 0xFFu) - ground[c]);
      if (best > 0) out[static_cast<size_t>(y / f) * ow + x / f] += best * inv;
    }
}
// Separable max (dilation) then box blur, radius in plane pixels.
inline void dilateBlur(std::vector<float> &p, int w, int h, int dil, int blur, int passes) {
  std::vector<float> tmp(p.size());
  auto pass = [&](bool isMax, int r) {
    for (int y = 0; y < h; y++)
      for (int x = 0; x < w; x++) {
        float acc = 0; int c = 0;
        for (int k = std::max(0, x - r); k <= std::min(w - 1, x + r); k++, c++) {
          const float v = p[static_cast<size_t>(y) * w + k];
          acc = isMax ? std::max(acc, v) : acc + v;
        }
        tmp[static_cast<size_t>(y) * w + x] = isMax ? acc : acc / c;
      }
    for (int y = 0; y < h; y++)
      for (int x = 0; x < w; x++) {
        float acc = 0; int c = 0;
        for (int k = std::max(0, y - r); k <= std::min(h - 1, y + r); k++, c++) {
          const float v = tmp[static_cast<size_t>(k) * w + x];
          acc = isMax ? std::max(acc, v) : acc + v;
        }
        p[static_cast<size_t>(y) * w + x] = isMax ? acc : acc / c;
      }
  };
  if (dil > 0) pass(true, dil);
  for (int i = 0; i < passes && blur > 0; i++) pass(false, blur);
}
inline SDL_Texture *uploadPlane(SDL_Renderer *r, SDL_Texture *tex, const std::vector<float> &p,
                                int w, int h, const uint8_t rgb[3], bool alphaFromPlane,
                                SDL_BlendMode mode) {
  if (tex) {
    float tw = 0, th = 0; SDL_GetTextureSize(tex, &tw, &th);
    if (static_cast<int>(tw) != w || static_cast<int>(th) != h) { SDL_DestroyTexture(tex); tex = nullptr; }
  }
  if (!tex) {
    tex = SDL_CreateTexture(r, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STATIC, w, h);
    if (!tex) return nullptr;
    SDL_SetTextureScaleMode(tex, SDL_SCALEMODE_LINEAR);
  }
  SDL_SetTextureBlendMode(tex, mode);
  std::vector<uint32_t> px(p.size());
  for (size_t i = 0; i < p.size(); i++) {
    const float v = std::clamp(p[i], 0.0f, 1.0f);
    if (alphaFromPlane) {
      px[i] = (static_cast<uint32_t>(v * 255.0f + 0.5f) << 24) |
              (static_cast<uint32_t>(rgb[0]) << 16) | (static_cast<uint32_t>(rgb[1]) << 8) | rgb[2];
    } else {
      px[i] = 0xFF000000u | (static_cast<uint32_t>(rgb[0] * v + 0.5f) << 16) |
              (static_cast<uint32_t>(rgb[1] * v + 0.5f) << 8) | static_cast<uint32_t>(rgb[2] * v + 0.5f);
    }
  }
  SDL_UpdateTexture(tex, nullptr, px.data(), w * 4);
  return tex;
}

// Fat-beam radii, in 1/2-resolution pixels at render scale 1 (so a soften,
// then 2 and 4 device pixels): the three levels darkSchedule blends through.
inline constexpr int kSwellDil[3] = {0, 1, 2};

template <typename DrawPanel>
inline void drawDark(SDL_Renderer *r, const uint32_t *pixels, int w, int h,
                     int scale, uint64_t seq, double f, const panelpalette::Palette &pal,
                     DrawPanel &&drawPanel) {
  Textures &t = textures();
  const float tf = static_cast<float>(f);
  const DarkSchedule d = darkSchedule(tf);
  const int sc = std::max(1, scale);
  // PASS 5 -- PHOSPHOR SATURATION GROWS WITH THE OVERDRIVE. The swell layers
  // are baked WHITE and tinted per step: from the phosphor's own color toward
  // white, 15% early to 70% at the end (pass 1-4 used a fixed 45%, so the
  // first swell was already bleached and the last one not hot enough).
  const float sat = 0.15f + 0.55f * tf;
  uint8_t hot[3];
  for (int c = 0; c < 3; c++) hot[c] = static_cast<uint8_t>(pal.ink[c] + (255 - pal.ink[c]) * sat);
  const uint8_t white[3] = {255, 255, 255};
  if (!t.lift) {
    t.lift = SDL_CreateTexture(r, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STATIC, 1, 1);
    if (t.lift) SDL_SetTextureBlendMode(t.lift, SDL_BLENDMODE_BLEND);
  }
  if (t.lift) {
    const uint32_t px = 0xFF000000u | (static_cast<uint32_t>(pal.ink[0]) << 16) |
                        (static_cast<uint32_t>(pal.ink[1]) << 8) | pal.ink[2];
    SDL_UpdateTexture(t.lift, nullptr, &px, 4);
  }
  if (t.glowSeq != seq || t.glowW != w || t.glowH != h) {
    t.glowSeq = seq; t.glowW = w; t.glowH = h;
    // HV-sag defocus: the whole picture, blurred (unchanged from v1)
    {
      std::vector<uint32_t> out; int ow = 0, oh = 0;
      const uint8_t zero[3] = {0, 0, 0};
      excessGlow(pixels, w, h, 6 * sc, 2, 3, zero, out, ow, oh);
      if (t.defocus) SDL_DestroyTexture(t.defocus);
      t.defocus = SDL_CreateTexture(r, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STATIC, ow, oh);
      if (t.defocus) {
        SDL_SetTextureBlendMode(t.defocus, SDL_BLENDMODE_BLEND);
        SDL_SetTextureScaleMode(t.defocus, SDL_SCALEMODE_LINEAR);
        SDL_UpdateTexture(t.defocus, nullptr, out.data(), ow * 4);
      }
    }
    // FAT BEAM: the strokes' coverage at 1/2 resolution, dilated to three
    // radii and softened, drawn as solid swollen strokes in the hot phosphor
    std::vector<float> cov; int cw = 0, ch = 0;
    excessCoverage(pixels, w, h, 2 * sc, pal.paper, pal.ink, cov, cw, ch);
    for (int i = 0; i < 3; i++) {
      std::vector<float> lvl = cov;
      dilateBlur(lvl, cw, ch, kSwellDil[i], 1, i == 2 ? 2 : 1);
      // PASS 3 -- VIDEO-AMP SMEAR. An overloaded video amplifier cannot fall
      // as fast as it rose, so bright content trails along the scan line.
      // The scan runs across the PRESENTED page (+/-y on this landscape
      // framebuffer); a one-sided exponential trail, longer at the heavier
      // levels.
      if (i > 0) {
        const float keep = i == 1 ? 0.55f : 0.72f;
        for (int x = 0; x < cw; x++) {
          float run = 0.0f;
          for (int y = ch - 1; y >= 0; y--) {
            float &v = lvl[static_cast<size_t>(y) * cw + x];
            run = std::max(v, run * keep);
            v = run;
          }
        }
      }
      for (float &v : lvl) v = std::min(1.0f, v * 1.3f);
      t.glow[i] = uploadPlane(r, t.glow[i], lvl, cw, ch, white, true, SDL_BLENDMODE_BLEND);
    }
    // HALATION: a ring -- wide blur minus a narrower one -- at 1/8
    {
      std::vector<float> c8; int w8 = 0, h8 = 0;
      excessCoverage(pixels, w, h, 8 * sc, pal.paper, pal.ink, c8, w8, h8);
      std::vector<float> wide = c8, narrow = c8;
      dilateBlur(wide, w8, h8, 0, 3, 2);
      dilateBlur(narrow, w8, h8, 0, 1, 1);
      for (size_t i = 0; i < wide.size(); i++) wide[i] = std::max(0.0f, wide[i] - 0.7f * narrow[i]) * 3.0f;
      t.halo = uploadPlane(r, t.halo, wide, w8, h8, pal.ink, false, SDL_BLENDMODE_ADD);
    }
  }
  // RETRACE LINES: fixed per size -- faint diagonals the blanking no longer hides
  if (!t.retrace || t.retraceW != w || t.retraceH != h) {
    const int rw = std::max(1, w / (4 * sc)), rh = std::max(1, h / (4 * sc));
    std::vector<float> p(static_cast<size_t>(rw) * rh, 0.0f);
    const int lines = 12;
    for (int y = 0; y < rh; y++)
      for (int x = 0; x < rw; x++) {
        // a family of parallel diagonals, antialiased over one plane pixel
        const float u = (x + 0.35f * y) / static_cast<float>(rw) * lines;
        const float fr = u - std::floor(u);
        const float dist = std::min(fr, 1.0f - fr) * (static_cast<float>(rw) / lines);
        p[static_cast<size_t>(y) * rw + x] = std::max(0.0f, 1.0f - 1.6f * dist) * 0.5f;
      }
    t.retrace = uploadPlane(r, t.retrace, p, rw, rh, pal.ink, false, SDL_BLENDMODE_ADD);
    t.retraceW = w; t.retraceH = h;
  }
  auto draw = [&](SDL_Texture *tex, float a) {
    if (!tex || a <= 0.0f) return;
    while (a > 0.0f) {
      SDL_SetTextureAlphaMod(tex, static_cast<Uint8>(std::min(a, 1.0f) * 255.0f + 0.5f));
      drawPanel(tex);
      a -= 1.0f;
    }
  };
  draw(t.defocus, d.defocus);
  draw(t.lift, d.lift);
  draw(t.retrace, d.retrace);
  for (int i = 0; i < 3; i++) {
    if (t.glow[i]) SDL_SetTextureColorMod(t.glow[i], hot[0], hot[1], hot[2]);
    draw(t.glow[i], d.swell[i]);
  }
  draw(t.halo, d.halo);
}

}  // namespace simallowance
