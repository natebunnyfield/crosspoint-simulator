#pragma once

// RAKING LIGHT -- the letterpress impression lit from a direction the reader's
// hand sets. Spike, 2026-09-25 (owner ruling: first spike of
// docs/research-novel-reading-interfaces-2026-09-24.md, idea F28). Design,
// measurements and what is left: docs/raking-light-spike-2026-09-25.md.
//
// WHAT IT CHANGES. src/Letterpress.h lights the deboss from ONE fixed
// direction: `lightDot = (gx + gy) * 0.707`, i.e. a light from the
// FRAMEBUFFER's top-left. This header makes that direction live. Tip the phone
// and the room's lamp, which does not move, arrives at the page from a
// different side, so the shadowed walls of the impression move round the
// letters as they do under a real desk lamp.
//
// WHAT IT DOES NOT CHANGE, and why each is safe:
//
//   - FLAT PAPER AND FLAT INK. The deboss and the relief both multiply the
//     Sobel gradient, which is exactly zero away from an edge, so every pixel
//     the contrast-floor proofs reason about (flat paper against flat ink) is
//     bit-identical to the fixed light at every direction. Nothing in
//     letterpress::paperBudget, fieldselect or the composite moves.
//   - THE DEEPEST SHADOW. A unit light direction times a rake in [0, 1] can
//     never push `shade` past the legacy lightDot's own ceiling of 1, so no
//     pixel under any light is darker than the fixed light's worst case at that
//     pixel. Tilting redistributes the shadow round the glyph; it never deepens
//     it. tests/raking_light_test.cpp proves both properties per pixel.
//   - THE PAPER TOOTH. Uniform per-pixel noise has no slope, so it has no lit
//     side. Lighting it would need a height field the model does not have; the
//     spike doc records it as not done rather than faked.
//
// WHAT IT ADDS. The INK side of the edge now catches light too: where the
// stroke's wall faces the lamp, the ink-squeeze rim is reduced by up to
// kRingReliefAt100 of itself. That is the only "brightening" in the model and
// it is bounded twice: relative to the letterpress it removes at most a
// fraction of the rim it itself added, and the multiplier stays <= 1, so
// relative to the unpressed page it is still darken-only.
//
// THE LAMP. A lamp fixed in the ROOM, not on the phone. At the pose the reader
// holds when the feature starts (the NEUTRAL, captured from CoreMotion's
// gravity, as ios/TiltGestures.h does) the lamp stands at exactly today's
// direction, elevation kLampElevationDeg above the page -- so switching the
// feature on does not move the shadow at all. When the phone tilts, gravity
// rotates in the phone's frame, and so does the lamp, by the same rotation:
// the minimal rotation taking the neutral gravity to the current one (no yaw;
// gravity cannot see yaw, and a reader turns with the phone anyway), scaled by
// kTiltGain so a wrist's worth of tilt sweeps a useful arc. Tilting TOWARD the
// lamp raises it overhead and the relief fades; tilting away rakes it and the
// relief returns to -- never past -- today's depth.
//
// QUANTIZED, because the field is CPU-built per page. 16 directions (22.5
// degrees, the lattice anchored ON today's direction so index 0 is exact) and
// 9 rake levels, with hysteresis at every boundary so a hand's tremor cannot
// flip a field every frame. A change of level recomposes only the EDGE pixels
// of an already-built page (EdgeField below), so a tilt costs a pass over the
// edges and a texture upload, not a rebuild.
//
// Pure and clock-free (the smoothing takes its dt as an argument): every
// failure mode here is a wrong picture or a field that thrashes, and
// tests/raking_light_test.cpp is the only instrument that can see either.

#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>

#include "Letterpress.h"

namespace rakinglight {

// --- CHOSEN CONSTANTS (not measured; no lamp was photographed) -------------
constexpr int kDirections = 16;
constexpr float kStepDeg = 360.0f / kDirections;  // 22.5
constexpr int kRakeLevels = 8;                    // rake in 0..8 eighths
// How far past a quantization midpoint the continuous value must travel before
// the level moves. 0.15 of a step: ~3.4 degrees of azimuth, 1.9% of rake.
constexpr float kHysteresis = 0.15f;
// Degrees of lamp rotation per degree of phone tilt. Physical is 1; 2 makes a
// comfortable 20-degree wrist tilt sweep the light through ~40 degrees of
// elevation change, which is what it takes to see it on a 6-inch page.
constexpr float kTiltGain = 2.0f;
// The lamp's elevation above the page at the neutral pose. Low enough that the
// light rakes, high enough that tilting away from it has somewhere to go
// before it is at grazing.
constexpr float kLampElevationDeg = 35.0f;
// The share of the ink-squeeze rim a wall facing the lamp gives back.
constexpr float kRingReliefAt100 = 0.35f;
// CoreMotion gravity low-pass, seconds (the research plan's 0.3 s).
constexpr float kSmoothingTauSec = 0.3f;

constexpr float kPi = 3.14159265358979f;
constexpr float kDegToRad = kPi / 180.0f;

// --- WHERE TODAY'S LIGHT IS, ON THE SCREEN ---------------------------------
//
// Letterpress.h's fixed light is framebuffer top-left; the presentation rotates
// the framebuffer by the firmware orientation (src/SurfaceSheet.cpp
// outputToPanel is the authority for the mapping), so on the SCREEN it comes
// from a different corner per orientation. Azimuth convention everywhere in
// this file: the direction the light comes FROM, degrees clockwise from the
// top of the screen. Orientation ints are GfxRenderer::Orientation:
// 0 Portrait, 1 LandscapeClockwise, 2 PortraitInverted, 3 LandscapeCCW.
inline float referenceScreenAzimuthDeg(int orientation) {
  switch (orientation) {
    case 0: return 45.0f;    // Portrait: framebuffer top-left = screen top-RIGHT
    case 1: return 135.0f;   // LandscapeClockwise: screen bottom-right
    case 2: return 225.0f;   // PortraitInverted: screen bottom-left
    default: return 315.0f;  // LandscapeCCW, the native panel: top-left
  }
}

inline float wrapDeg(float d) {  // into (-180, 180]
  while (d > 180.0f) d -= 360.0f;
  while (d <= -180.0f) d += 360.0f;
  return d;
}

// --- FROM GRAVITY TO A LIGHT -----------------------------------------------

struct Vec3 {
  float x = 0.0f, y = 0.0f, z = 0.0f;
};

inline float dot3(const Vec3 &a, const Vec3 &b) {
  return a.x * b.x + a.y * b.y + a.z * b.z;
}
inline Vec3 cross3(const Vec3 &a, const Vec3 &b) {
  return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z,
          a.x * b.y - a.y * b.x};
}
inline float len3(const Vec3 &a) { return std::sqrt(dot3(a, a)); }

// Where the light is, relative to today's: `deltaDeg` is the azimuth offset
// (clockwise on screen, positive) and `rake` the relief's depth as a fraction
// of today's, in [0, 1].
struct Continuous {
  float deltaDeg = 0.0f;
  float rake = 1.0f;
};

// `neutral` and `g` are CoreMotion gravity in DEVICE coordinates (+x toward
// the screen's right edge, +y toward its top, +z out of the glass -- the same
// axes ios/TiltGestures.h states). `refAzDeg` is referenceScreenAzimuthDeg for
// the current orientation. At g == neutral the answer is EXACTLY {0, 1}.
inline Continuous lightFromGravity(const Vec3 &neutral, const Vec3 &g,
                                   float refAzDeg) {
  const float ln = len3(neutral), lg = len3(g);
  if (!(ln > 0.1f) || !(lg > 0.1f)) return {};  // no reading: today's light
  const Vec3 n{neutral.x / ln, neutral.y / ln, neutral.z / ln};
  const Vec3 v{g.x / lg, g.y / lg, g.z / lg};
  Vec3 axis = cross3(n, v);
  const float s = len3(axis);
  float c = dot3(n, v);
  if (c > 1.0f) c = 1.0f;
  if (c < -1.0f) c = -1.0f;
  const float angle = std::atan2(s, c);
  // Unmoved, or flipped over (antiparallel: the axis is undefined and the
  // page faces the floor) -- neither has a meaningful new light.
  if (angle < 1e-4f || s < 1e-6f) return {};
  axis = {axis.x / s, axis.y / s, axis.z / s};
  float a = angle * kTiltGain;
  if (a > kPi) a = kPi;

  // The lamp at the neutral pose, in device axes: azimuth refAz clockwise
  // from the top, so +x = sin, +y (toward the top) = cos.
  const float e0 = kLampElevationDeg * kDegToRad;
  const float az0 = refAzDeg * kDegToRad;
  const Vec3 L0{std::cos(e0) * std::sin(az0), std::cos(e0) * std::cos(az0),
                std::sin(e0)};
  // Rodrigues: the lamp turns in the phone's frame exactly as gravity did.
  const float ca = std::cos(a), sa = std::sin(a);
  const Vec3 kxl = cross3(axis, L0);
  const float kdl = dot3(axis, L0);
  const Vec3 L{L0.x * ca + kxl.x * sa + axis.x * kdl * (1.0f - ca),
               L0.y * ca + kxl.y * sa + axis.y * kdl * (1.0f - ca),
               L0.z * ca + kxl.z * sa + axis.z * kdl * (1.0f - ca)};

  Continuous out;
  const float inPlane = std::sqrt(L.x * L.x + L.y * L.y);
  if (inPlane < 1e-4f) {  // straight overhead: no side to rake from
    out.rake = 0.0f;
    return out;
  }
  const float az = std::atan2(L.x, L.y) / kDegToRad;
  out.deltaDeg = wrapDeg(az - refAzDeg);
  // Relief follows the lamp's in-plane reach, CAPPED at today's: at grazing it
  // is today's depth, never more (the deboss is already budgeted at it).
  float r = inPlane / std::cos(e0);
  if (r > 1.0f) r = 1.0f;
  if (r < 0.0f) r = 0.0f;
  out.rake = r;
  return out;
}

// One step of a first-order low-pass on gravity. dt in seconds; a first sample
// (or a dt that is not positive) is taken as-is.
inline Vec3 smooth(const Vec3 &prev, const Vec3 &sample, float dtSec,
                   bool havePrev) {
  if (!havePrev || !(dtSec > 0.0f)) return sample;
  const float alpha = dtSec / (kSmoothingTauSec + dtSec);
  return {prev.x + (sample.x - prev.x) * alpha,
          prev.y + (sample.y - prev.y) * alpha,
          prev.z + (sample.z - prev.z) * alpha};
}

// --- QUANTIZED -------------------------------------------------------------

struct Quantized {
  int dir = 0;                 // 0..kDirections-1, 0 = today's direction
  int rake = kRakeLevels;      // 0..kRakeLevels, kRakeLevels = today's depth
  bool operator==(const Quantized &o) const {
    return dir == o.dir && rake == o.rake;
  }
  bool operator!=(const Quantized &o) const { return !(*this == o); }
};

// One int, for an atomic. Never zero, so 0 can mean "none yet".
inline int pack(const Quantized &q) { return 1 + q.dir + 32 * q.rake; }
inline Quantized unpack(int v) {
  Quantized q;
  if (v <= 0) return q;
  v -= 1;
  q.dir = v % 32;
  q.rake = v / 32;
  return q;
}

inline Quantized quantize(const Continuous &c, const Quantized *prev) {
  Quantized out;
  // Direction: nearest lattice point, unless the previous one is still within
  // half a step plus the hysteresis band (circularly).
  const float cont = wrapDeg(c.deltaDeg) / kStepDeg;  // (-8, 8]
  int nearest = static_cast<int>(std::lround(cont));
  nearest = ((nearest % kDirections) + kDirections) % kDirections;
  out.dir = nearest;
  if (prev) {
    float d = cont - static_cast<float>(prev->dir);
    while (d > kDirections / 2.0f) d -= kDirections;
    while (d <= -kDirections / 2.0f) d += kDirections;
    if (std::fabs(d) < 0.5f + kHysteresis) out.dir = prev->dir;
  }
  float r = c.rake;
  if (!(r > 0.0f)) r = 0.0f;
  if (r > 1.0f) r = 1.0f;
  const float contR = r * kRakeLevels;
  out.rake = static_cast<int>(std::lround(contR));
  if (prev && std::fabs(contR - static_cast<float>(prev->rake)) <
                  0.5f + kHysteresis)
    out.rake = prev->rake;
  return out;
}

// A light straight from a screen azimuth (the desktop's QA hatch): full rake,
// no hysteresis.
inline Quantized fromScreenAzimuth(float azDeg, int orientation) {
  Continuous c;
  c.deltaDeg = wrapDeg(azDeg - referenceScreenAzimuthDeg(orientation));
  c.rake = 1.0f;
  return quantize(c, nullptr);
}

// --- THE PER-PIXEL LIGHTING ------------------------------------------------

// The shadow's direction in FRAMEBUFFER space (y down), unit length, and the
// rake. Rotations commute with the presentation's rotation (all four
// orientations are proper rotations), so an azimuth offset on screen is the
// same offset here: today's shadow direction (1,1)/sqrt2 turned by dir steps.
struct Shadow {
  float dx = 0.70710678f, dy = 0.70710678f;
  float rake = 1.0f;
};

inline Shadow shadowFor(const Quantized &q) {
  Shadow s;
  const float ang = (45.0f + static_cast<float>(q.dir) * kStepDeg) * kDegToRad;
  s.dx = std::cos(ang);
  s.dy = std::sin(ang);
  s.rake = static_cast<float>(q.rake) / static_cast<float>(kRakeLevels);
  return s;
}

// The per-pixel terms that depend on the light, reduced from letterpress::Terms.
// `rest` is every direction-free darkening summed once (press + in-stroke +
// tooth), so a recompose adds three numbers rather than five.
struct Edge {
  float gx = 0.0f, gy = 0.0f;
  float ring = 0.0f;
  float depth = 0.0f;  // debossK * (1 - t): the shadow at full shade
  float rest = 0.0f;
};

inline Edge edgeOf(const letterpress::Terms &T) {
  Edge e;
  e.gx = T.gx;
  e.gy = T.gy;
  e.ring = T.ring;
  e.depth = T.debossK * (1.0f - T.t);
  e.rest = T.press + T.irregular + T.tooth;
  return e;
}

// THE ANSWER, lit from `S`. Off (strength 0) is the caller's to short-circuit
// with letterpress::Terms::off, exactly as multiplierAt does.
inline uint8_t multiplierFor(const Edge &e, const Shadow &S) {
  const float d = e.gx * S.dx + e.gy * S.dy;
  float shade = d;
  if (shade < 0.0f) shade = 0.0f;
  if (shade > 1.0f) shade = 1.0f;
  float lit = -d;
  if (lit < 0.0f) lit = 0.0f;
  if (lit > 1.0f) lit = 1.0f;
  const float deboss = e.depth * shade * S.rake;
  const float ring = e.ring * (1.0f - kRingReliefAt100 * lit * S.rake);
  float m = 1.0f - (ring + deboss + e.rest);
  if (m < letterpress::kMinMultiplier) m = letterpress::kMinMultiplier;
  if (m > 1.0f) m = 1.0f;
  return static_cast<uint8_t>(m * 255.0f + 0.5f);
}

// --- THE PAGE, BUILT ONCE AND RE-LIT MANY TIMES -----------------------------
//
// Most of a page is flat: paper with no ink near it, or the inside of a
// stroke. There the gradient is zero and the multiplier is the same under
// every light, so it is written once, at build. Only the EDGE pixels (a
// non-zero gradient) are kept, with their terms, and re-lit on a change of
// light. Measured cost is in the spike doc.
struct EdgeField {
  int w = 0, h = 0;
  std::vector<uint32_t> field;  // ARGB, the MOD texture's pixels
  std::vector<uint32_t> edgeIndex;
  std::vector<Edge> edges;

  // `termsAt(x, y)` returns letterpress::Terms for one pixel; the caller
  // supplies it so the window read stays where the inkness plane lives.
  template <typename TermsAt>
  void build(int width, int height, TermsAt termsAt) {
    w = width;
    h = height;
    field.assign(static_cast<size_t>(w) * h, 0xFFFFFFFFu);
    edgeIndex.clear();
    edges.clear();
    const Shadow any;  // irrelevant where the gradient is zero
    for (int y = 0; y < h; ++y) {
      for (int x = 0; x < w; ++x) {
        const letterpress::Terms T = termsAt(x, y);
        const size_t i = static_cast<size_t>(y) * w + x;
        if (T.off) continue;  // stays 0xFFFFFFFF, untouched
        const Edge e = edgeOf(T);
        if (T.gx != 0.0f || T.gy != 0.0f) {
          edgeIndex.push_back(static_cast<uint32_t>(i));
          edges.push_back(e);
          continue;  // written by relight()
        }
        const uint32_t m = multiplierFor(e, any);
        field[i] = 0xFF000000u | (m << 16) | (m << 8) | m;
      }
    }
  }

  void relight(const Shadow &S) {
    for (size_t k = 0; k < edges.size(); ++k) {
      const uint32_t m = multiplierFor(edges[k], S);
      field[edgeIndex[k]] = 0xFF000000u | (m << 16) | (m << 8) | m;
    }
  }
};

}  // namespace rakinglight
