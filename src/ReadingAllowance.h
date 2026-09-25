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

// How much of the letterpress impression (rim, deboss, pressure) remains.
// The PRESS is not what is failing -- the ink is -- so the impression holds
// until the very end: a starved plate still bites, and the blind deboss of an
// uninked letter is what a starved sheet actually shows. It goes only at the
// close, because the page must end unreadable.
inline float pressLeft(float t) {
  if (t <= 0.0f) return 1.0f;
  if (t >= 1.0f) return 0.0f;
  return 1.0f - t * t * t;
}

// ---- VERSION 2 (owner 2026-09-24, fourth ruling: "incorporate more physical
// ink and paper and plate simulation. it shouldn't be this faint, it should be
// incidental and viscous. research how"). What the research says a starved
// letterpress sheet looks like, and what each term below models:
//
//  * TRANSFER. Walker & Fetsko's ink-transfer model: the fraction of paper a
//    film covers is 1 - exp(-k x) in the film thickness x; the paper's
//    contact scales k. A thin film misses the sheet's VALLEYS -- the classic
//    "salty" print: white pinholes in the solids, following the paper.
//  * VISCOUS. Letterpress ink is a stiff paste; where it transfers it prints
//    at full body, and where it does not the paper is bare. So a pixel prints
//    or it does not, decided against a CLUSTERED field (ink splits into cells
//    and filaments, not white noise) -- never a uniform fade. The film
//    thinning only greys what prints by a little.
//  * STARVATION IS INCIDENTAL, not uniform. The form rollers lose ink to what
//    they inked just before: a line under a heavy line is starved ("light
//    print ghost", the roller robbed by the elements ahead of it), and the
//    roller's own circumference leaves bands where its film was thinner.
//  * EDGE PRESSURE. The sheet wraps the type's shoulder, so a stroke's EDGE
//    bites harder than its middle: under starvation letters go salty in the
//    middle and hold their outline.
struct PressSample {
  float interior;   // ink blurred one device pixel: 1 deep in a stroke, ~0.5 at its edge
  float tooth;      // the paper's tooth, 0..1 ('TOOT')
  float form;       // the sheet's formation, 0..1 ('FORM')
  float plate;      // the plate pressure, 0..1 ('PLTE')
  float blob;       // the ink's clustered split field, 0.06..1 ('VISC')
  float depletion;  // ink the roller spent on the rows just above, 0..1
  float band;       // the roller circumference's thin band, 0..1
  float skip = 0.0f;  // word-sized patches of the form the roller skipped, 0..1 ('SKIP')
};

// The per-pixel terms the per-STEP pass needs, precomputed per page: how much
// the roller was robbed here (`robbed`, the incidental terms' weighted sum),
// the paper's `contact`, and the split field `blob`. Three numbers, so the
// renderer can keep them as bytes (the review measured 53 MB of 32-byte
// samples at 2x).
inline float robbedOf(const PressSample &p) {
  const float skip = std::max(0.0f, (p.skip - 0.55f) * 2.2f);
  return 0.55f * p.band + 0.60f * p.depletion + 0.60f * skip;
}
inline float contactOf(const PressSample &p) {
  return 0.40f * p.tooth + 0.15f * p.form + 0.25f * p.plate + 0.20f * (1.0f - p.interior);
}

// The fraction of a pixel's ink that prints at decay t, from its three
// terms; `supplyBase` is (1 - t)^1.25, computed once per step. 1 at t = 0,
// 0 at t = 1.
inline float printedRaw(float robbed, float contact, float blob, float t,
                        float supplyBase) {
  if (t <= 0.0f) return 1.0f;
  if (t >= 1.0f) return 0.0f;
  float supply = supplyBase * (1.0f - t * robbed);
  if (supply < 0.0f) supply = 0.0f;
  // Walker-Fetsko coverage, normalized to the full film's so t = 0 is clean.
  const float kk = 4.0f * (0.35f + contact);
  const float cover = (1.0f - std::exp(-kk * supply)) / (1.0f - std::exp(-kk));
  // SLOPE 5 AGAINST A SMOOTH FIELD (owner 2026-09-24: "improve the jagged
  // pixelated look of light ink effect"). Pass 4's slope 28 against a field
  // with a per-pixel hash in it made every decision a hard per-pixel one:
  // single-pixel salt with stair-stepped edges. The field is smooth now
  // (blobAt), so 5 gives a transition about half a pixel wide -- the cells
  // print solid and their edges are antialiased, which is not faint. The
  // blob's range (0.06..0.80) keeps t -> 0 exactly clean and t -> 1 exactly
  // empty with no offset term.
  const float kept = std::clamp((cover - 0.92f * blob) * 5.0f, 0.0f, 1.0f);
  const float body = 0.90f + 0.10f * std::min(1.0f, supply * 3.0f);
  return kept * body;
}

// The fraction of a pixel's ink that prints at decay t. 1 at t = 0, 0 at t = 1.
inline float printedFraction(const PressSample &p, float t) {
  return printedRaw(robbedOf(p), contactOf(p), p.blob, t,
                    t > 0.0f && t < 1.0f ? std::pow(1.0f - t, 1.25f) : 0.0f);
}

// The clustered split field at panel pixel (x, y): two octaves of SMOOTH value
// noise, 2.2 and 1.1 device px cells, no per-pixel hash -- a hash made the
// break-up a per-pixel coin toss and the edges jagged (see printedRaw).
inline float blobAt(int x, int y, int scale, uint32_t seed) {
  const float c = 2.2f * static_cast<float>(scale > 0 ? scale : 1);
  const float v1 = phosphorgrain::valueNoise(static_cast<float>(x) / c,
                                             static_cast<float>(y) / c,
                                             seed ^ 0x56495343u);
  const float v2 = phosphorgrain::valueNoise(static_cast<float>(x) * 2.0f / c,
                                             static_cast<float>(y) * 2.0f / c,
                                             seed ^ 0x53504C54u);
  return 0.06f + 0.74f * (0.70f * v1 + 0.30f * v2);
}

// The paper's tooth as the starved plate FEELS it: the 'TOOT' lane smoothed
// to ~1.3 device px cells, so the kiss follows grains of paper rather than
// single pixels.
inline float smoothToothAt(int x, int y, int scale, uint32_t seed) {
  const float c = 1.3f * static_cast<float>(scale > 0 ? scale : 1);
  return phosphorgrain::valueNoise(static_cast<float>(x) / c,
                                   static_cast<float>(y) / c, seed ^ 0x544F4F54u);
}

// ---- THE OVERDRIVEN TUBE (owner 2026-09-25: rework the dark decay as the
// light one was -- research the physics, take passes). What an overdriven CRT
// actually does, from the service literature (repairfaq's TV FAQ, "blooming or
// breathing"; beam-current-limiter patents):
//
//  * FAT BEAM. Beam current rises with brightness and a high-current beam is a
//    wider, harder-to-focus spot, so BRIGHT strokes swell -- the letters grow
//    heavy and fill their counters before anything else goes.
//  * PHOSPHOR SATURATION. The swollen core clips toward white.
//  * HALATION. Light scattered inside the faceplate returns as a ring around
//    bright areas.
//  * HIGH-VOLTAGE SAG. Under the load the anode voltage drops, the beam loses
//    stiffness and focus -- the whole picture softens, late.
//  * BRIGHTNESS PAST CUTOFF. The black level lifts toward grey and the
//    retrace lines, normally blanked, show as faint diagonals.
//
// DarkSchedule says how much of each is on at decay t. Pure, so the test can
// pin the ordering: the swell first, then halation and lift, the defocus last.
struct DarkSchedule {
  float swell[3];   // blend weights of the three dilation radii, 0..1
  float halo;       // ring halo gain
  float defocus;    // whole-picture defocus, 0..1
  float lift;       // black level toward the phosphor, 0..1
  float retrace;    // retrace-line visibility, 0..1
};
inline float smoothstepf(float a, float b, float x) {
  const float u = std::clamp((x - a) / (b - a), 0.0f, 1.0f);
  return u * u * (3.0f - 2.0f * u);
}
inline DarkSchedule darkSchedule(float t) {
  DarkSchedule d{};
  if (t <= 0.0f) return d;
  t = std::min(t, 1.0f);
  // Pass 2: the first schedule had the page swollen past reading at 4:22
  // (t = 0.37) and the retrace lines loud by 4:30. A fat beam grows with the
  // overdrive, so the swell now spreads over the whole minute, and retrace is
  // a late, faint ghost.
  d.swell[0] = smoothstepf(0.05f, 0.45f, t);
  d.swell[1] = smoothstepf(0.35f, 0.75f, t);
  d.swell[2] = smoothstepf(0.60f, 0.95f, t);
  d.halo = 1.0f * smoothstepf(0.15f, 0.80f, t);
  d.defocus = smoothstepf(0.60f, 1.00f, t);
  d.lift = 0.60f * std::pow(t, 1.5f);
  d.retrace = 0.45f * smoothstepf(0.50f, 1.00f, t);
  return d;
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
