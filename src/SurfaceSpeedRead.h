#pragma once

// SPEED READ's host half: the channel reader, the clock and the drawing. The
// decisions (which word, how long, where its pivot is) are src/SpeedRead.h,
// pure and host-tested; this file is the SDL side and is included ONLY by
// src/HalDisplay.cpp, main thread only. Header-only on purpose, like
// SurfaceAllowance.h: a new .cpp here would leave the generated iOS source
// list (cmake/CrossPointSources.cmake) stale.
//
// THE WORDS ARE CUT FROM THE PAGE ITSELF. The read-aloud channel already
// carries each displayed word's rect (logical portrait panel pixels), so each
// RSVP frame is that word's own pixels -- the book's font, its hinting, its
// antialiasing, the owner's ink on the owner's paper -- lifted out of the
// landscape framebuffer, magnified and placed so its pivot letter sits on the
// focal ticks. No font renderer, no second rasterization to disagree with the
// page. docs/speed-read-rsvp-2026-09-25.md.

#include <SDL3/SDL.h>

#include <GfxRenderer.h>

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <mutex>
#include <string>
#include <vector>

#include "HalGPIO.h"
#include "PanelPalette.h"
#include "SpeedRead.h"

namespace simspeedread {

// A publish arrives BEFORE the reader paints (EpubReaderActivity captures, then
// renders), and an antialiased page is written twice 13-22 ms apart. So a
// page's words are taken only once a pixel write newer than the publish has
// landed and the buffer has then been quiet this long.
inline constexpr uint64_t kSettleMs = 60;
// ...or this long after the publish whatever the pixels did: a re-render that
// changed nothing may write no pixels at all.
inline constexpr uint64_t kSettleTimeoutMs = 1500;
// Magnification of a word, in LOGICAL panel pixels per logical pixel. A 18 pt
// line (~36 px) becomes ~81 px tall; a word too wide for the frame shrinks.
inline constexpr float kMagnify = 2.25f;
// The focal point, as fractions of the page: the Spritz frame sits a little
// left of centre so the long right half of a word has room.
inline constexpr float kFocalX = 0.38f;
inline constexpr float kFocalY = 0.42f;

struct State {
  std::atomic<bool> enabled{false};
  std::atomic<int> wpm{speedread::kDefaultWpm};
  std::atomic<bool> tapToggle{false};
  std::atomic<bool> showing{false};
  // Read-aloud turns pages itself when its speech ends; with both on, each
  // page end got two page-forward presses (adversarial review, build 213).
  // While this is set speed read leaves the turn to read-aloud.
  std::atomic<bool> readAloudTurns{false};

  speedread::Reader reader;
  uint32_t lastGen = 0;
  bool hasPending = false;
  ReadAloudPage pending;
  uint64_t pendingSeenAt = 0;
  std::string curUtf8;
  std::vector<ReadAloudWordRect> curRects;
  uint64_t pageVersion = 0;

  // The crop cache: one texture per displayed word.
  SDL_Texture *tex = nullptr;
  uint64_t texPage = ~0ull;
  size_t texIndex = ~size_t(0);
  int texW = 0, texH = 0;
  float texPivot = 0.0f;
  int texLineH = 0; // the word's line height in crop pixels (fixed guides)
};

inline State &st() {
  static State s;
  return s;
}

inline bool enabled() { return st().enabled.load(); }
inline bool showing() { return st().showing.load(); }

inline void destroyTexture() {
  State &s = st();
  if (s.tex) SDL_DestroyTexture(s.tex);
  s.tex = nullptr;
  s.texPage = ~0ull;
  s.texIndex = ~size_t(0);
}

// On/off. Capture is asked for through the channel's PEEKER flag, OR'd with
// the read-aloud consumer's own -- never written over it.
inline void setReadAloudTurns(bool on) { st().readAloudTurns.store(on); }

inline void setEnabled(bool on) {
  State &s = st();
  if (s.enabled.exchange(on) == on) return;
  gpio.setReadAloudPeekerWanted(on);
  if (on) {
    // Re-read the page the channel already holds: the cursor still names it
    // from the last time the mode was on, and peek hands a page over once per
    // generation, so without this an off->on on one page would show nothing
    // until the next page turn.
    s.lastGen = 0;
    // NO RE-RENDER IS ASKED FOR. The phone captures every page anyway
    // (CrossPointReadAloud_perFrame), and the desktop seeds this before the
    // first loop(). A desktop toggle made mid-page therefore starts at the next
    // page render. Asking the firmware directly (crosspointRequestRender) was
    // tried and refused: upstream firmware has no such symbol, a weak
    // reference does not link on Mach-O, and a weak DEFINITION here could
    // stop the strong one being pulled out of the iOS static archive, silently
    // breaking the appearance re-render that depends on it.
  } else {
    s.reader.clear();
    s.hasPending = false;
    s.curUtf8.clear();
    s.curRects.clear();
    destroyTexture();  // nothing to show; do not hold the word crop
  }
  SDL_Log("[speedread] %s", on ? "on" : "off");
}

inline void setWpm(int wpm) {
  st().wpm.store(std::clamp(wpm, speedread::kMinWpm, speedread::kMaxWpm));
}

// A tap on the glass while a word is up: pause or resume. True when the tap
// was taken (the caller then does nothing else with it).
inline bool takeTap() {
  if (!enabled() || !showing()) return false;
  st().tapToggle.store(true);
  return true;
}

inline bool sameRects(const std::vector<ReadAloudWordRect> &a,
                      const std::vector<ReadAloudWordRect> &b) {
  if (a.size() != b.size()) return false;
  for (size_t i = 0; i < a.size(); i++)
    if (a[i].x != b[i].x || a[i].y != b[i].y || a[i].w != b[i].w ||
        a[i].h != b[i].h || a[i].byteOffset != b[i].byteOffset ||
        a[i].byteLen != b[i].byteLen)
      return false;
  return true;
}

// Once per main-loop pass. Returns true when the glass owes a present.
inline bool step(uint64_t now, bool onReaderPage, uint64_t lastPixelWriteMs) {
  State &s = st();
  if (!s.enabled.load()) {
    const bool was = s.showing.exchange(false);
    return was;
  }
  bool dirty = false;
  ReadAloudPage pg;
  if (gpio.peekReadAloudPage(s.lastGen, pg)) {
    if (pg.cleared) {
      s.reader.clear();
      s.hasPending = false;
      s.curUtf8.clear();
      s.curRects.clear();
      dirty = true;
    } else {
      s.pending = std::move(pg);
      s.hasPending = true;
      s.pendingSeenAt = now;
    }
  }
  if (s.hasPending) {
    const bool same = s.reader.hasPage() && s.pending.utf8 == s.curUtf8 &&
                      sameRects(s.pending.rects, s.curRects);
    const bool painted = lastPixelWriteMs >= s.pending.publishedAtMs &&
                         now >= lastPixelWriteMs + kSettleMs;
    if (same || painted || now - s.pendingSeenAt >= kSettleTimeoutMs) {
      s.reader.pageArrived(
          speedread::wordsFromPage(s.pending.utf8, s.pending.rects), now, same);
      if (!same) {
        s.pageVersion++;
        SDL_Log("[speedread] page gen=%u: %zu words", s.pending.generation,
                s.reader.count());
      }
      s.curUtf8 = std::move(s.pending.utf8);
      s.curRects = std::move(s.pending.rects);
      s.hasPending = false;
      dirty = true;
    }
  }
  s.reader.setWpm(s.wpm.load());
  if (s.tapToggle.exchange(false)) {
    s.reader.togglePause(now);
    SDL_Log("[speedread] %s", s.reader.paused() ? "paused" : "resumed");
    dirty = true;
  }
  if (onReaderPage) {
    const speedread::Reader::Event e = s.reader.step(now);
    if (e.changed) {
      dirty = true;
      // CROSSPOINT_SIM_SPEED_READ_LOG=1: one line per word, the headless way
      // to measure the effective rate against the nominal one.
      static const bool logWords = [] {
        const char *v = SDL_getenv("CROSSPOINT_SIM_SPEED_READ_LOG");
        return v && v[0] == '1';
      }();
      if (logWords && s.reader.current())
        SDL_Log("[speedread] t=%llu word %zu/%zu \"%s\"%s",
                static_cast<unsigned long long>(now), s.reader.index() + 1,
                s.reader.count(), s.reader.current()->text.c_str(),
                s.reader.current()->paragraphEnd ? " PARA" : "");
    }
    if (e.requestTurn) {
      if (s.readAloudTurns.load()) {
        SDL_Log("[speedread] end of page -> read-aloud turns the page");
      } else {
        SDL_Log("[speedread] end of page -> page forward");
        gpio.queueButtonTap(HalGPIO::BTN_RIGHT, 60);
      }
    }
  }
  const bool show = onReaderPage && s.reader.hasPage() &&
                    s.reader.current() != nullptr;
  if (s.showing.exchange(show) != show) dirty = true;
  return dirty;
}

// The framebuffer pixel under logical (x, y) at render scale S -- the firmware's
// own rotateCoordinates (GfxRenderer.cpp), in device space.
inline bool fbIndex(int orientation, int x, int y, int fbW, int fbH,
                    size_t &out) {
  int fx, fy;
  switch (orientation) {
  case GfxRenderer::Portrait: fx = y; fy = fbH - 1 - x; break;
  case GfxRenderer::PortraitInverted: fx = fbW - 1 - y; fy = x; break;
  case GfxRenderer::LandscapeClockwise:
    fx = fbW - 1 - x;
    fy = fbH - 1 - y;
    break;
  default: fx = x; fy = y; break;
  }
  if (fx < 0 || fy < 0 || fx >= fbW || fy >= fbH) return false;
  out = static_cast<size_t>(fy) * fbW + fx;
  return true;
}

inline float lumOf(uint32_t argb) {
  return 0.2126f * ((argb >> 16) & 0xFF) + 0.7152f * ((argb >> 8) & 0xFF) +
         0.0722f * (argb & 0xFF);
}

// Build the current word's crop texture if the word changed.
inline void ensureCrop(SDL_Renderer *r, const uint32_t *pixelBuf,
                       std::mutex &pixelLock, int fbW, int fbH, int S,
                       int orientation, const panelpalette::Palette &pal) {
  State &s = st();
  const speedread::Word *w = s.reader.current();
  if (!w) return;
  if (s.tex && s.texPage == s.pageVersion && s.texIndex == s.reader.index())
    return;
  destroyTexture();
  int cw = 0, ch = 0;
  for (const auto &f : w->frags) {
    cw += f.w * S;
    ch = std::max(ch, f.h * S);
  }
  if (cw <= 0 || ch <= 0) return;
  const uint32_t paperArgb = 0xFF000000u | (uint32_t(pal.paper[0]) << 16) |
                             (uint32_t(pal.paper[1]) << 8) | pal.paper[2];
  std::vector<uint32_t> img(static_cast<size_t>(cw) * ch, paperArgb);
  {
    const std::lock_guard<std::mutex> lock(pixelLock);
    int ox = 0;
    for (const auto &f : w->frags) {
      for (int yy = 0; yy < f.h * S; yy++)
        for (int xx = 0; xx < f.w * S; xx++) {
          size_t idx;
          if (fbIndex(orientation, f.x * S + xx, f.y * S + yy, fbW, fbH, idx))
            img[static_cast<size_t>(yy) * cw + ox + xx] = pixelBuf[idx];
        }
      ox += f.w * S;
    }
  }
  // The pivot, from the crop's own ink (speedread::pivotX).
  const float paperLum = lumOf(paperArgb);
  std::vector<float> ink(cw, 0.0f);
  for (int yy = 0; yy < ch; yy++)
    for (int xx = 0; xx < cw; xx++)
      ink[xx] += std::fabs(lumOf(img[static_cast<size_t>(yy) * cw + xx]) -
                           paperLum) / 255.0f;
  std::vector<float> widths = speedread::glyphWidths(w->text);
  int pivotGlyph = speedread::orpGlyph(w->text);
  if (w->frags.size() > 1)
    speedread::addSplitHyphen(widths, pivotGlyph,
                              static_cast<float>(w->frags[0].w) * S / cw);
  const float pivot = speedread::pivotX(ink, widths, pivotGlyph, 0.35f * S);
  s.tex = SDL_CreateTexture(r, SDL_PIXELFORMAT_ARGB8888,
                            SDL_TEXTUREACCESS_STATIC, cw, ch);
  if (!s.tex) return;
  SDL_UpdateTexture(s.tex, nullptr, img.data(), cw * 4);
  SDL_SetTextureScaleMode(s.tex, SDL_SCALEMODE_LINEAR);
  SDL_SetTextureBlendMode(s.tex, SDL_BLENDMODE_NONE);
  s.texW = cw;
  s.texH = ch;
  s.texPivot = pivot;
  s.texLineH = w->frags.front().h * S;
  s.texPage = s.pageVersion;
  s.texIndex = s.reader.index();
}

// Draw the frame over the page, in OUTPUT pixels (logical presentation
// disabled by the caller). `px..ph` is the page's rect on the glass.
inline void draw(SDL_Renderer *r, const uint32_t *pixelBuf,
                 std::mutex &pixelLock, int fbW, int fbH, int S,
                 int orientation, float px, float py, float pw, float ph,
                 const panelpalette::Palette &pal) {
  State &s = st();
  if (!s.showing.load() || pw <= 0 || ph <= 0) return;
  ensureCrop(r, pixelBuf, pixelLock, fbW, fbH, S, orientation, pal);
  const bool portrait = orientation == GfxRenderer::Portrait ||
                        orientation == GfxRenderer::PortraitInverted;
  const float logicalW = static_cast<float>(portrait ? fbH : fbW) / S;
  const float u = pw / logicalW; // output px per logical px

  SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_NONE);
  SDL_SetRenderDrawColor(r, pal.paper[0], pal.paper[1], pal.paper[2], 255);
  const SDL_FRect page{px, py, pw, ph};
  SDL_RenderFillRect(r, &page);

  const float fx = std::round(px + kFocalX * pw);
  const float cy = std::round(py + kFocalY * ph);
  const float margin = 0.05f * pw;
  const float lineH = (s.texLineH > 0 ? s.texLineH / float(S) : 36.0f) * u *
                      kMagnify; // nominal word band, output px
  const float t = std::max(1.0f, std::round(u * 1.5f));

  // Spritz's frame: two rules with a notch at the focal point.
  SDL_SetRenderDrawColor(r, pal.ink[0], pal.ink[1], pal.ink[2], 255);
  const float top = std::round(cy - lineH * 0.8f);
  const float bot = std::round(cy + lineH * 0.8f);
  const SDL_FRect rules[4] = {
      {px + margin, top, pw - 2 * margin, t},
      {px + margin, bot - t, pw - 2 * margin, t},
      {fx - std::floor(t / 2), top, t, std::round(lineH * 0.22f)},
      {fx - std::floor(t / 2), bot - std::round(lineH * 0.22f), t,
       std::round(lineH * 0.22f)},
  };
  SDL_RenderFillRects(r, rules, 4);

  if (s.tex && s.texW > 0) {
    float k = u * kMagnify / S; // output px per crop px
    const float leftRoom = fx - px - margin;
    const float rightRoom = px + pw - margin - fx;
    if (s.texPivot > 0 && s.texPivot * k > leftRoom) k = leftRoom / s.texPivot;
    if (s.texW - s.texPivot > 0 && (s.texW - s.texPivot) * k > rightRoom)
      k = rightRoom / (s.texW - s.texPivot);
    const SDL_FRect dst{fx - s.texPivot * k, cy - s.texH * k / 2.0f,
                        s.texW * k, s.texH * k};
    SDL_RenderTexture(r, s.tex, nullptr, &dst);
  }

  // The readout: wpm, place on the page, and state.
  char b[96];
  const char *state = s.reader.finished() ? "   end"
                      : s.reader.paused() ? "   paused"
                                          : "";
  std::snprintf(b, sizeof b, "%d wpm   %zu/%zu%s", s.reader.wpm(),
                s.reader.index() + 1, s.reader.count(), state);
  const float sc = std::max(1.0f, std::floor(u * 1.5f));
  const float tw = std::strlen(b) * SDL_DEBUG_TEXT_FONT_CHARACTER_SIZE * sc;
  SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_BLEND);
  SDL_SetRenderDrawColor(r, pal.ink[0], pal.ink[1], pal.ink[2], 150);
  SDL_SetRenderScale(r, sc, sc);
  SDL_RenderDebugText(r, (px + (pw - tw) / 2) / sc,
                      std::round(bot + lineH * 0.9f) / sc, b);
  SDL_SetRenderScale(r, 1.0f, 1.0f);
}

} // namespace simspeedread
