#pragma once

// THE ZEN READING GOAL -- five minutes of reading, then the page gives out.
//
// Owner 2026-09-24, in two rulings. First (the per-book allowance, since
// replaced): *"I think I want a timer on the book that makes it harder and
// harder to read as time passes, ultimately making it unreadable at the end"*,
// then *"starting at last minute, do too much emission for dark and for light,
// do too light of ink."* Then, the same day, the shape that ships: *"change
// this to goal of read 5 minutes a day, no matter the book. it only applies in
// zen mode and zen mode starting up again restarts it."* So:
//
//   * ONE CLOCK, whatever the book. It runs only while a book page is on the
//     glass IN ZEN -- not in a menu, not asleep, not in the background, not
//     with zen off.
//   * ZEN STARTING RESTARTS IT. Every off->on edge of zen, and a launch into
//     zen (which is zen starting), gives a fresh clock. Nothing persists: a
//     reader who wants another five minutes leaves zen and comes back.
//   * THE LAST MINUTE. The page is untouched until one minute remains, then
//     decays over that minute to unreadable -- the light page as ink pressed
//     too lightly, the dark page as a tube emitting too much -- and stays so
//     until zen is left. Leaving zen shows the page clean at once.
//
// WHY A PURE HEADER, like the rest of the family here: every way this can be
// wrong is silent. A clock that also counts the Home screen, a restart that
// never fires, a decay that starts at the wrong second -- all of them compile,
// render and log nothing. This file holds every one of those decisions and
// nothing that touches SDL, so the test can drive them.
//
// Rendering lives in src/SurfaceAllowance.h; the setting is a Settings.app
// row on the phone (CrossPointPrefs_readingAllowanceMinutes) and
// CROSSPOINT_SIM_READING_ALLOWANCE on the desktop, through src/SimulatorDials.h.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "PanelPalette.h"
#include "PhosphorGrain.h"

namespace readingallowance {

// How long the decay takes, counted back from the end of the goal.
inline constexpr double kDecaySeconds = 60.0;

// The largest clock step one pass may add. The main loop runs many times a
// second; a longer gap means the process was stalled or suspended (iOS does not
// always deliver the background edge before it stops scheduling us), and that
// time was not reading. Capped rather than discarded so a slow frame is not
// lost either.
inline constexpr double kMaxStepSeconds = 1.0;

// The options the Settings row offers, in minutes. 0 is Off.
inline constexpr int kOptions[] = {0, 5, 10, 15, 20, 30, 45, 60};
inline constexpr int kDefaultMinutes = 5;
inline constexpr int kMaxMinutes = 24 * 60;

// How far into the decay `usedSeconds` of a `allowanceMinutes` allowance is:
// 0 until the last minute begins, 1 once it is spent. An allowance of one
// minute or less decays over the whole of it. Off (<= 0) is always 0.
inline double decayFraction(double usedSeconds, int allowanceMinutes) {
  if (allowanceMinutes <= 0) return 0.0;
  const double total = static_cast<double>(allowanceMinutes) * 60.0;
  const double window = total < kDecaySeconds ? total : kDecaySeconds;
  const double start = total - window;
  if (usedSeconds <= start) return 0.0;
  if (usedSeconds >= total) return 1.0;
  return (usedSeconds - start) / window;
}

// ONE ZEN SESSION'S CLOCK. `step` is called on every main-loop pass with
// whether zen is on and whether this moment is reading; an off->on edge of zen
// (including the first pass that sees zen on, which is a launch into zen)
// starts the clock again from zero.
struct Session {
  double seconds = 0.0;
  bool lastZen = false;
  // True when this step restarted the clock -- the caller's cue to re-seed a
  // QA preset and to present the page clean.
  bool step(bool zen, bool reading, double dt) {
    const bool restarted = zen && !lastZen;
    if (restarted) seconds = 0.0;
    lastZen = zen;
    if (reading && dt > 0.0) seconds += dt > kMaxStepSeconds ? kMaxStepSeconds : dt;
    return restarted;
  }
};

// IS THIS READING? Every condition as one predicate so it cannot be
// half-applied. Zen must be on (the goal "only applies in zen mode"), a book
// page must be the sheet on glass (not Home, not Settings, not a chapter
// list), the device must be awake (neither the sleep screen nor the sleep
// loop), and the app must be in front and active.
inline bool counts(bool zen, bool readerPageOnGlass, bool asleep,
                   bool sleepScreen, bool inactive) {
  return zen && readerPageOnGlass && !asleep && !sleepScreen && !inactive;
}

// The decay drives a picture that only changes when a present happens, and an
// e-ink firmware presents once per page. Quantizing tells the caller when the
// picture has moved enough to be worth a present: 120 steps over the minute is
// a step every half second, below what the eye reads as stepping on a fade.
inline int quantize(double fraction) {
  if (fraction <= 0.0) return 0;
  if (fraction >= 1.0) return 120;
  return static_cast<int>(fraction * 120.0 + 0.5);
}

namespace picture {

// ---------------------------------------------------------------------------
// THE PICTURES' PURE PIXEL MATH -- no SDL, so the test can drive it. The
// SDL half that draws with it is src/SurfaceAllowance.h.
// ---------------------------------------------------------------------------

// A fixed tooth field in [0,1], one value per panel pixel: a 1 px octave for
// the paper's grain and a 3 px octave for its clumps. Deterministic in (x, y)
// alone, so a page decays the same way every time it is looked at and a stroke
// that has broken stays broken rather than shimmering.
inline float toothAt(int x, int y) {
  auto h = [](uint32_t a, uint32_t b) {
    uint32_t v = a * 0x9E3779B1u ^ b * 0x85EBCA77u;
    v ^= v >> 15;
    v *= 0x2C1B3C6Du;
    v ^= v >> 12;
    v *= 0x297A2D39u;
    v ^= v >> 15;
    return static_cast<float>(v & 0xFFFFu) / 65535.0f;
  };
  const float fine = h(static_cast<uint32_t>(x), static_cast<uint32_t>(y));
  const float coarse =
      h(static_cast<uint32_t>(x / 3) + 7919u, static_cast<uint32_t>(y / 3) + 104729u);
  return 0.45f * fine + 0.55f * coarse;
}

// How far, in device pixels, the letterpress reaches outside a stroke.
inline constexpr int kReach = 2;

// How much of a pixel's ink SURVIVES at decay t, given its tooth: 1 = all of
// it, 0 = none. The mock-up's option G, as the owner saw it.
inline float inkRetained(float tooth, float t) {
  // The threshold starts BELOW the lowest tooth, so t = 0 retains every
  // pixel's ink: the first version started it at 0.15 and 4.6% of the ink lost
  // up to 59% of itself the instant the last minute began (adversarial review).
  float starve = (tooth - (-0.25f + 1.2f * t)) * 4.0f + 1.0f - 1.2f * t;
  starve = std::clamp(starve, 0.0f, 1.0f);
  return starve * (1.0f - 0.55f * t);
}

// How much ink a presented pixel carries, 0 (paper) .. 1 (full ink), read
// against the page's own palette on the channel with the widest ink/paper
// spread (a single channel keeps a tinted ink from reading as half ink).
inline float inkness(uint32_t argb, const panelpalette::Palette &pal) {
  int best = 0, span = 0;
  for (int c = 0; c < 3; c++) {
    const int s = std::abs(static_cast<int>(pal.paper[c]) - pal.ink[c]);
    if (s > span) {
      span = s;
      best = c;
    }
  }
  if (span == 0) return 0.0f;
  const int shift = 16 - 8 * best;
  const int v = static_cast<int>((argb >> shift) & 0xFFu);
  const float k = static_cast<float>(v - pal.paper[best]) /
                  static_cast<float>(pal.ink[best] - pal.paper[best]);
  return std::clamp(k, 0.0f, 1.0f);
}

// The LIGHT veil's alpha at one pixel: the ink this pixel loses.
inline float veilAlpha(float ink, float tooth, float t) {
  return ink * (1.0f - inkRetained(tooth, t));
}

// ---- THE STARVED PRESS (owner 2026-09-24: "redo the decay in light mode to
// take full advantage of the letterpress and ink and paper simulation, it
// seems lacking currently"). The first light decay starved the ink against a
// private noise field of its own, so the break-up had nothing to do with the
// paper the page is drawn on or the plate that printed it. This one reads the
// SAME lanes the letterpress model reads (src/Letterpress.h), seeded by the
// page's own sheet identity:
//
//   the paper's TOOTH ('TOOT', per panel pixel) -- a starved plate kisses the
//     high spots of the sheet first and misses the valleys;
//   the sheet's FORMATION ('FORM', 3 cells) -- the cloudy, thicker regions of
//     the sheet take the kiss better than the thin ones;
//   the PLATE PRESSURE ('PLTE', 4 cells) -- where the press bears down
//     heaviest, ink survives longest;
//
// and the STROKE'S INTERIOR (the page's own inkness, blurred one device pixel):
// a light impression drops the edges of a stroke first, so the letters thin
// before they break. What survives is a thinner film, so it pales toward the
// paper -- in the ink's own hue, because the veil is the paper's color over
// the ink. The IMPRESSION recedes with the pressure (pressLeft below), so the
// squeeze rim and the deboss go with the ink instead of printing a ghost of
// every letter on a spent page.

// How well a starved plate still prints at panel pixel (x, y), 0..1.
inline float kissAt(int x, int y, int w, int h, uint32_t seed) {
  const float u = phosphorgrain::unitFromHash(phosphorgrain::hash3(
      static_cast<uint32_t>(x), static_cast<uint32_t>(y), seed ^ 0x544F4F54u));
  const float nx = (static_cast<float>(x) + 0.5f) / static_cast<float>(w > 0 ? w : 1);
  const float ny = (static_cast<float>(y) + 0.5f) / static_cast<float>(h > 0 ? h : 1);
  const float form = phosphorgrain::valueNoise(nx * 3.0f, ny * 3.0f, seed ^ 0x464F524Du);
  const float plate = phosphorgrain::valueNoise(nx * 4.0f, ny * 4.0f, seed ^ 0x504C5445u);
  return 0.60f * u + 0.15f * form + 0.25f * plate;
}

// The fraction of a pixel's ink that survives at decay t, from the press's
// kiss there and how deep inside its stroke it sits (0 at the edge, 1 deep).
// Exactly 1 at t = 0 and exactly 0 at t = 1 for every input.
inline float starvedRetained(float kiss, float interior, float t) {
  if (t <= 0.0f) return 1.0f;
  if (t >= 1.0f) return 0.0f;
  const float score = 0.65f * kiss + 0.35f * interior;
  // A soft, wide ramp (slope 2.5, threshold -0.4 -> 1.4): the first cut
  // (slope 5, -0.3 -> 1.3) held the page nearly clean to 4:24 and blank by
  // 4:50, so the starvation read as a cut rather than as a minute.
  const float threshold = -0.40f + 1.80f * t;
  const float kept = std::clamp((score - threshold) * 2.5f + 1.0f, 0.0f, 1.0f);
  // A thinner film pales what is left -- but only by 40%: starved letterpress
  // reads as dark fragments on the sheet's high spots, not as uniformly faint
  // type, and at 55% the break-up disappeared into the fade.
  return kept * (1.0f - 0.40f * t);
}

// How much of the letterpress impression (rim, deboss, pressure) remains.
inline float pressLeft(float t) {
  if (t <= 0.0f) return 1.0f;
  if (t >= 1.0f) return 0.0f;
  return std::pow(1.0f - t, 1.5f);
}

// Box-downsample the page's excess light over `ground` by `factor`, then blur
// it with `passes` separable box passes of radius `radius`. Output is
// premultiplied-style RGB in [0,255] per texel, alpha 255. `src` is w*h ARGB.
inline void excessGlow(const uint32_t *src, int w, int h, int factor,
                       int radius, int passes, const uint8_t ground[3],
                       std::vector<uint32_t> &out, int &ow, int &oh) {
  ow = std::max(1, w / factor);
  oh = std::max(1, h / factor);
  std::vector<float> acc(static_cast<size_t>(ow) * oh * 3, 0.0f);
  const float inv = 1.0f / static_cast<float>(factor * factor);
  for (int y = 0; y < oh * factor; y++) {
    const uint32_t *row = src + static_cast<size_t>(y) * w;
    float *arow = &acc[static_cast<size_t>(y / factor) * ow * 3];
    for (int x = 0; x < ow * factor; x++) {
      const uint32_t p = row[x];
      float *a = arow + (x / factor) * 3;
      for (int c = 0; c < 3; c++) {
        const int v = static_cast<int>((p >> (16 - 8 * c)) & 0xFFu) - ground[c];
        if (v > 0) a[c] += static_cast<float>(v) * inv;
      }
    }
  }
  std::vector<float> tmp(acc.size());
  for (int pass = 0; pass < passes && radius > 0; pass++) {
    const float n = 1.0f / static_cast<float>(2 * radius + 1);
    for (int y = 0; y < oh; y++)
      for (int x = 0; x < ow; x++)
        for (int c = 0; c < 3; c++) {
          float s = 0;
          for (int k = -radius; k <= radius; k++) {
            const int xx = std::clamp(x + k, 0, ow - 1);
            s += acc[(static_cast<size_t>(y) * ow + xx) * 3 + c];
          }
          tmp[(static_cast<size_t>(y) * ow + x) * 3 + c] = s * n;
        }
    for (int y = 0; y < oh; y++)
      for (int x = 0; x < ow; x++)
        for (int c = 0; c < 3; c++) {
          float s = 0;
          for (int k = -radius; k <= radius; k++) {
            const int yy = std::clamp(y + k, 0, oh - 1);
            s += tmp[(static_cast<size_t>(yy) * ow + x) * 3 + c];
          }
          acc[(static_cast<size_t>(y) * ow + x) * 3 + c] = s * n;
        }
  }
  out.assign(static_cast<size_t>(ow) * oh, 0xFF000000u);
  for (size_t i = 0; i < out.size(); i++) {
    uint32_t px = 0xFF000000u;
    for (int c = 0; c < 3; c++) {
      const int v = std::clamp(static_cast<int>(acc[i * 3 + c] + 0.5f), 0, 255);
      px |= static_cast<uint32_t>(v) << (16 - 8 * c);
    }
    out[i] = px;
  }
}

}  // namespace picture

}  // namespace readingallowance
