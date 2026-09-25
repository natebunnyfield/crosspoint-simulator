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
  std::vector<float> tooth;  // the press's kiss per panel pixel
  std::vector<float> inkRow, inkDil;  // the page's ink, and blur scratch
  std::vector<float> interior;        // ink blurred one device pixel
  uint32_t veilSeed = 0;
  int scale = 1;
  SDL_Texture *pressTarget = nullptr;  // the faded letterpress field
  int pressW = 0, pressH = 0;

  SDL_Texture *defocus = nullptr;

  SDL_Texture *glow[3] = {nullptr, nullptr, nullptr};
  uint64_t glowSeq = ~0ull;
  SDL_Texture *lift = nullptr;
};

inline Textures &textures() {
  static Textures t;
  return t;
}

inline void destroyAll() {
  Textures &t = textures();
  if (!t.veil && !t.lift && !t.defocus && !t.pressTarget && !t.glow[0] &&
      !t.glow[1] && !t.glow[2])
    return;
  if (t.pressTarget) SDL_DestroyTexture(t.pressTarget);
  if (t.veil) SDL_DestroyTexture(t.veil);
  for (SDL_Texture *&g : t.glow)
    if (g) SDL_DestroyTexture(g), g = nullptr;
  if (t.lift) SDL_DestroyTexture(t.lift);
  if (t.defocus) SDL_DestroyTexture(t.defocus);
  t = Textures{};
}

// LIGHT: the starved press. Rebuilt per PAGE (the ink, its interior, and the
// press's kiss off the page's own sheet seed) and per decay STEP (the alpha
// only). `pixels` is the presented panel (w*h ARGB), a copy the caller took
// under the pixel lock. See picture::starvedRetained for the model.
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
      // The page's ink, the stroke interior (ink box-blurred one device pixel,
      // so a stroke's edge reads about half and its core 1), and the kiss.
      std::vector<float> &ink = t.inkRow;
      std::vector<float> &tmp = t.inkDil;
      ink.resize(n);
      tmp.resize(n);
      t.interior.resize(n);
      t.tooth.resize(n);
      for (size_t i = 0; i < n; i++) ink[i] = inkness(pixels[i], pal);
      const int rad = std::max(1, scale);
      for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
          float sum = 0; int c = 0;
          for (int k = std::max(0, x - rad); k <= std::min(w - 1, x + rad); k++, c++)
            sum += ink[static_cast<size_t>(y) * w + k];
          tmp[static_cast<size_t>(y) * w + x] = sum / c;
        }
      for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++) {
          float sum = 0; int c = 0;
          for (int k = std::max(0, y - rad); k <= std::min(h - 1, y + rad); k++, c++)
            sum += tmp[static_cast<size_t>(k) * w + x];
          t.interior[static_cast<size_t>(y) * w + x] = sum / c;
        }
      for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
          t.tooth[static_cast<size_t>(y) * w + x] = kissAt(x, y, w, h, sheetSeed);
    }
    t.veilSeq = seq;
    t.veilSeed = sheetSeed;
    t.veilStep = step;
    const float tf = static_cast<float>(step) / 120.0f;
    t.veilPixels.resize(n);
    const uint32_t rgb = (static_cast<uint32_t>(pal.paper[0]) << 16) |
                         (static_cast<uint32_t>(pal.paper[1]) << 8) | pal.paper[2];
    for (size_t i = 0; i < n; i++) {
      // The veil must take away (1 - retained) of WHATEVER ink is there: a
      // veil weighted by the pixel's own ink fraction leaves ink*(1-ink) of
      // it behind -- a quarter of every half-covered edge pixel, which read
      // as a ghost of the whole page at 5:00 (measured p5 214 against paper
      // 241). Masked to the ink and one device pixel around it, so bare paper
      // is never veiled.
      const float mask = std::min(1.0f, 6.0f * std::max(t.inkRow[i], t.interior[i]));
      const float a =
          mask * (1.0f - starvedRetained(t.tooth[i], t.interior[i], tf));
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
  SDL_SetRenderDrawColor(r, 255, 255, 255, 255);
  SDL_RenderClear(r);
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

// The three glows: (downsample factor, blur radius). The first is the swell --
// a glyph's own light spreading a device pixel or two, which fills the
// counters -- and the other two the halation.
struct GlowLevel {
  int factor, radius;
};
inline constexpr GlowLevel kGlow[3] = {{2, 1}, {4, 2}, {12, 2}};
// Each glow's gain over the minute. The swell PEAKS mid-minute and gives way:
// it is built from the sharp page, so held at full to the end it reprinted
// crisp letter shapes over the defocus and the spent page still read (measured
// on the first render with the defocus in). The wide halation only grows.
inline float glowGain(int level, float t) {
  switch (level) {
    case 0: return 2.2f * 4.0f * t * (1.0f - t);
    case 1: return 1.6f * t * (1.0f - 0.6f * t);
    default: return 1.4f * t;
  }
}
// How far the ground lifts toward the ink at t = 1.
inline constexpr float kLiftAtEnd = 0.80f;
// THE SPOT GROWS. An overdriven beam defocuses: the whole picture is replaced,
// by t = 1, with itself blurred past reading. Without this the swell and the
// glows only brightened the page -- the first render still read cleanly at
// 10:00, white type on a lifted ground. (downsample, radius, passes)
inline constexpr int kDefocusFactor = 6, kDefocusRadius = 2, kDefocusPasses = 3;

template <typename DrawPanel>
inline void drawDark(SDL_Renderer *r, const uint32_t *pixels, int w, int h,
                     uint64_t seq, double f, const panelpalette::Palette &pal,
                     DrawPanel &&drawPanel) {
  Textures &t = textures();
  const float tf = static_cast<float>(f);
  if (!t.lift) {
    t.lift = SDL_CreateTexture(r, SDL_PIXELFORMAT_ARGB8888,
                               SDL_TEXTUREACCESS_STATIC, 1, 1);
    if (t.lift) SDL_SetTextureBlendMode(t.lift, SDL_BLENDMODE_BLEND);
  }
  if (t.lift) {
    const uint32_t px = 0xFF000000u | (static_cast<uint32_t>(pal.ink[0]) << 16) |
                        (static_cast<uint32_t>(pal.ink[1]) << 8) | pal.ink[2];
    SDL_UpdateTexture(t.lift, nullptr, &px, 4);
    SDL_SetTextureAlphaMod(
        t.lift, static_cast<Uint8>(kLiftAtEnd * tf * tf * 255.0f + 0.5f));
  }
  if (t.glowSeq != seq) {
    t.glowSeq = seq;
    std::vector<uint32_t> out;
    {
      int ow = 0, oh = 0;
      const uint8_t zero[3] = {0, 0, 0};
      excessGlow(pixels, w, h, kDefocusFactor, kDefocusRadius, kDefocusPasses,
                 zero, out, ow, oh);
      if (t.defocus) SDL_DestroyTexture(t.defocus);
      t.defocus = SDL_CreateTexture(r, SDL_PIXELFORMAT_ARGB8888,
                                    SDL_TEXTUREACCESS_STATIC, ow, oh);
      if (t.defocus) {
        SDL_SetTextureBlendMode(t.defocus, SDL_BLENDMODE_BLEND);
        SDL_SetTextureScaleMode(t.defocus, SDL_SCALEMODE_LINEAR);
        SDL_UpdateTexture(t.defocus, nullptr, out.data(), ow * 4);
      }
    }
    for (int i = 0; i < 3; i++) {
      int ow = 0, oh = 0;
      excessGlow(pixels, w, h, kGlow[i].factor, kGlow[i].radius, 2, pal.paper,
                 out, ow, oh);
      if (t.glow[i]) {
        float gw = 0, gh = 0;
        SDL_GetTextureSize(t.glow[i], &gw, &gh);
        if (static_cast<int>(gw) != ow || static_cast<int>(gh) != oh) {
          SDL_DestroyTexture(t.glow[i]);
          t.glow[i] = nullptr;
        }
      }
      if (!t.glow[i]) {
        t.glow[i] = SDL_CreateTexture(r, SDL_PIXELFORMAT_ARGB8888,
                                      SDL_TEXTUREACCESS_STATIC, ow, oh);
        if (!t.glow[i]) continue;
        SDL_SetTextureBlendMode(t.glow[i], SDL_BLENDMODE_ADD);
        SDL_SetTextureScaleMode(t.glow[i], SDL_SCALEMODE_LINEAR);
      }
      SDL_UpdateTexture(t.glow[i], nullptr, out.data(), ow * 4);
    }
  }
  // The defocused picture over the sharp one, then the lift over both, so
  // the ground the glows land on is the lifted one.
  if (t.defocus) {
    const float a = std::clamp(tf * tf * (3.0f - 2.0f * tf), 0.0f, 1.0f);
    SDL_SetTextureAlphaMod(t.defocus, static_cast<Uint8>(a * 255.0f + 0.5f));
    drawPanel(t.defocus);
  }
  if (t.lift) drawPanel(t.lift);
  for (int i = 0; i < 3; i++) {
    if (!t.glow[i]) continue;
    // A gain above one is drawn as whole passes plus a remainder: alpha mod
    // cannot exceed 255, and ADD is linear in the number of passes.
    float g = glowGain(i, tf);
    while (g > 0.0f) {
      const float a = std::min(g, 1.0f);
      SDL_SetTextureAlphaMod(t.glow[i], static_cast<Uint8>(a * 255.0f + 0.5f));
      drawPanel(t.glow[i]);
      g -= 1.0f;
    }
  }
}

}  // namespace simallowance
