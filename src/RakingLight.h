#pragma once

// RAKING LIGHT -- the light page lit from a direction the reader's hand sets.
// Spike 2026-09-25 (owner ruling: first spike of
// docs/research-novel-reading-interfaces-2026-09-24.md, idea F28); reworked
// 2026-09-26 on the owner's report "improve simulation of raking to be based
// on variable settings. it is not visible as is and the page itself could be
// light sensitive too." Design, measurements and what is left:
// docs/raking-light-spike-2026-09-25.md.
//
// TWO THINGS ANSWER THE LAMP, in two passes:
//
//   1. THE INK'S RELIEF (EdgeField, panel space). src/Letterpress.h lights the
//      deboss from ONE fixed direction, `lightDot = (gx + gy) * 0.707`, a light
//      from the FRAMEBUFFER's top-left. This makes that direction live, and
//      gives the shadow a depth the STRENGTH dial can raise well past what the
//      fixed light draws -- the 2026-09-25 spike kept it capped at today's
//      depth and the owner could not see it (measured: 1.4-2.6% of pixels
//      moved, by a mean of 0.16-0.35 levels, across the whole tilt range).
//
//   2. THE SHEET'S RELIEF AND THE LAMP'S FALLOFF (LampField, output space, the
//      whole glass). The paper itself answers the lamp: a lamp at a finite
//      distance lights the near side of the sheet more than the far side, and
//      the sheet's own low relief -- the formation clouds the sheet pass already
//      draws, plus finer fiber-clump octaves (not the laid furrows: tried and
//      withdrawn, see SurfaceSheet.cpp) -- is shaded on the slopes that face
//      away from the lamp.
//      One MOD texture at half resolution (the relief is smooth by
//      construction; there is nothing at pixel scale for it to lose), drawn
//      over page, card and pad alike, because it is one sheet under one lamp.
//
// WHAT IT DOES NOT CHANGE, and why each is safe:
//
//   - FLAT PAPER AND FLAT INK, in the PANEL field. The deboss and the relief
//     both multiply the Sobel gradient, which is exactly zero away from an
//     edge, so every pixel of the panel field that the contrast-floor proofs
//     reason about is bit-identical to the fixed light at every direction.
//   - THE PAPER BUDGET. The lamp field is a fifth consumer of what the tooth
//     left the paper (after the wires and the show-through, before the marks):
//     its darkening is capped PER PIXEL at lampBudget() of that remainder, and
//     the marks receive what it leaves. So the page-mean paper darkening stays
//     inside letterpress::paperBudget by construction, at every light and every
//     dial, and the darkest lamp pixel on its own still clears the floor.
//   - DARKEN-ONLY, both passes. Multipliers in (0, 1]; no lift anywhere. The
//     ink side of a wall facing the lamp gives back part of its OWN squeeze rim
//     (kRingReliefAt100), which is the one "brightening" and it is bounded by
//     what the letterpress itself added.
//   - THE PAPER TOOTH's per-pixel noise. White noise has no lit side. The
//     fiber-scale relief the lamp reveals is the LampField's finest octave
//     (a few px), not the tooth hash.
//
// THE LAMP. Fixed in the ROOM, not on the phone. At the pose the reader holds
// when the feature starts (the NEUTRAL, the first CoreMotion gravity sample)
// the lamp stands at exactly today's azimuth, at the elevation the LAMP HEIGHT
// dial sets. When the phone tilts, gravity rotates in the phone's frame, and so
// does the lamp, by the same rotation (no yaw; gravity cannot see yaw) scaled
// by the TILT RANGE dial. Tilting toward the lamp raises it and the relief
// fades; tilting away lowers it toward grazing and every shadow lengthens. The
// RAKE is cot(elevation) against cot(35 degrees), capped at kRakeMax: at the
// reference lamp it is exactly 1, which is the fixed light's own depth.
//
// QUANTIZED, because both fields are CPU-built. kDirections azimuth steps and
// kRakeLevelsPerUnit rake levels per unit, with hysteresis at every boundary so
// a hand's tremor cannot relight a field every frame. A change of level
// re-lights the edge pixels of the panel field and the lattice of the lamp
// field and re-uploads both; nothing is rebuilt.
//
// Pure and clock-free (the smoothing takes its dt as an argument): every
// failure mode here is a wrong picture or a field that thrashes, and
// tests/raking_light_test.cpp is the only instrument that can see either.

#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>

#include "Letterpress.h"
#include "PhosphorGrain.h"  // valueNoise / hash3, all pure

namespace rakinglight {

// --- CHOSEN CONSTANTS (not measured; no lamp was photographed) -------------
constexpr int kDirections = 32;
constexpr float kStepDeg = 360.0f / kDirections;  // 11.25
// Rake levels per unit of rake, and the rake's ceiling (a lamp at grazing).
constexpr int kRakeLevelsPerUnit = 8;
constexpr float kRakeMax = 3.0f;
constexpr int kRakeLevelMax = static_cast<int>(kRakeMax * kRakeLevelsPerUnit);
// How far past a quantization midpoint the continuous value must travel before
// the level moves. 0.15 of a step: ~1.7 degrees of azimuth, 1.9% of a rake unit.
constexpr float kHysteresis = 0.15f;
// The lamp elevation at which the rake is exactly 1 -- today's fixed light.
constexpr float kRefElevationDeg = 35.0f;
constexpr float kMinElevationDeg = 5.0f;
// The share of the ink-squeeze rim a wall facing the lamp gives back.
constexpr float kRingReliefAt100 = 0.35f;
// CoreMotion gravity low-pass, seconds (the research plan's 0.3 s).
constexpr float kSmoothingTauSec = 0.3f;

constexpr float kPi = 3.14159265358979f;
constexpr float kDegToRad = kPi / 180.0f;

// --- THE FOUR DIALS ---------------------------------------------------------
//
// 0..200 each, Settings.app sliders (the Ink group's shape). 100 is the
// shipped default on every one, chosen so the effect is plainly visible at
// default rather than provable-but-invisible, which is what the spike shipped.
constexpr int kDialMax = 200;
constexpr int kDialDefault = 100;

struct Dials {
  int strengthPct = kDialDefault;    // the ink relief's gain over today's
  int lampHeightPct = kDialDefault;  // the lamp's elevation at the neutral
  int tiltRangePct = kDialDefault;   // degrees of lamp per degree of tilt
  int pagePct = kDialDefault;        // how much the sheet itself answers
};

inline int clampPct(int pct) {
  if (pct < 0) return 0;
  if (pct > kDialMax) return kDialMax;
  return pct;
}

// STRENGTH: the deboss shadow's depth as a multiple of the fixed light's.
// 0 is today's depth (the feature adds nothing to the ink), 100 is three times
// it, 200 five times. Linear above today's so the slider has no dead half.
constexpr float kStrengthGainAt100 = 2.0f;
inline float strengthGain(int pct) {
  return 1.0f + static_cast<float>(clampPct(pct)) / 100.0f * kStrengthGainAt100;
}

// LAMP HEIGHT: the neutral pose's lamp elevation. 0 is a low desk lamp (12
// degrees, rake capped at kRakeMax), 100 is today's 35 degrees (rake exactly
// 1), 200 is 58 degrees (rake 0.44, the relief fades).
constexpr float kLampElevationMinDeg = 12.0f;
constexpr float kLampElevationSpanPer100 = 23.0f;
inline float lampElevationDeg(int pct) {
  return kLampElevationMinDeg +
         static_cast<float>(clampPct(pct)) / 100.0f * kLampElevationSpanPer100;
}

// TILT RANGE: degrees of lamp rotation per degree of phone tilt. Physical is
// 1; 100 gives 2, so a comfortable 20-degree wrist tilt sweeps ~40 degrees of
// lamp, which is what it takes to see it on a 6-inch page. 0 pins the lamp:
// a raking light that does not follow the hand, which is still a raking light.
constexpr float kTiltGainAt100 = 2.0f;
inline float tiltGain(int pct) {
  return static_cast<float>(clampPct(pct)) / 100.0f * kTiltGainAt100;
}

// PAGE: how much of the lamp's budget the sheet spends. At 100 the far corner
// of the sheet sits at kPageAt100 of the budget under the reference lamp and
// the shaded slopes add on top; at 200 the far half clips at the budget.
constexpr float kPageAt100 = 0.7f;
inline float pageFactor(int pct) {
  return static_cast<float>(clampPct(pct)) / 100.0f * kPageAt100;
}

// The rake for a lamp elevation: cot(e) against the reference, capped. At the
// reference elevation the two tangents are the same expression, so the
// quotient is exactly 1.0f -- which is what makes "neutral is today's light"
// a statement about bytes rather than about rounding.
inline float rakeForElevation(float elevDeg) {
  if (!(elevDeg > kMinElevationDeg)) elevDeg = kMinElevationDeg;
  if (elevDeg > 90.0f) elevDeg = 90.0f;
  const float r = std::tan(kRefElevationDeg * kDegToRad) / std::tan(elevDeg * kDegToRad);
  if (!(r > 0.0f)) return 0.0f;
  return r > kRakeMax ? kRakeMax : r;
}

// The inverse, for the lamp field: rake 0 is straight overhead.
inline float elevationForRake(float rake) {
  if (!(rake > 0.0f)) return 90.0f;
  const float e = std::atan(std::tan(kRefElevationDeg * kDegToRad) / rake) / kDegToRad;
  return e < kMinElevationDeg ? kMinElevationDeg : e;
}

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
// (clockwise on screen, positive) and `rake` cot(elevation) against the
// reference lamp's, in [0, kRakeMax].
struct Continuous {
  float deltaDeg = 0.0f;
  float rake = 1.0f;
};

// The light at the neutral pose: today's azimuth, the dial's elevation.
inline Continuous neutralLight(const Dials &d) {
  Continuous c;
  c.rake = rakeForElevation(lampElevationDeg(d.lampHeightPct));
  return c;
}

// `neutral` and `g` are CoreMotion gravity in DEVICE coordinates (+x toward
// the screen's right edge, +y toward its top, +z out of the glass -- the same
// axes ios/TiltGestures.h states). `refAzDeg` is referenceScreenAzimuthDeg for
// the current orientation. At g == neutral the answer is EXACTLY
// neutralLight(d).
inline Continuous lightFromGravity(const Vec3 &neutral, const Vec3 &g,
                                   float refAzDeg, const Dials &d) {
  const Continuous rest = neutralLight(d);
  const float ln = len3(neutral), lg = len3(g);
  if (!(ln > 0.1f) || !(lg > 0.1f)) return rest;  // no reading: today's light
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
  if (angle < 1e-4f || s < 1e-6f) return rest;
  const float gain = tiltGain(d.tiltRangePct);
  if (!(gain > 0.0f)) return rest;  // the lamp is pinned
  axis = {axis.x / s, axis.y / s, axis.z / s};
  float a = angle * gain;
  if (a > kPi) a = kPi;

  // The lamp at the neutral pose, in device axes: azimuth refAz clockwise
  // from the top, so +x = sin, +y (toward the top) = cos.
  const float e0 = lampElevationDeg(d.lampHeightPct) * kDegToRad;
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
  // The lamp's elevation in the phone's frame. Below the page's horizon (the
  // page turned away past grazing) it is held at grazing: the shadows are as
  // long as they get and stay there, rather than snapping off.
  float z = L.z;
  if (z > 1.0f) z = 1.0f;
  const float elev = z > 0.0f ? std::asin(z) / kDegToRad : 0.0f;
  out.rake = rakeForElevation(elev);
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
  int dir = 0;                      // 0..kDirections-1, 0 = today's direction
  int rake = kRakeLevelsPerUnit;    // 0..kRakeLevelMax, 8 = the reference depth
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
  const float cont = wrapDeg(c.deltaDeg) / kStepDeg;  // (-16, 16]
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
  if (r > kRakeMax) r = kRakeMax;
  const float contR = r * kRakeLevelsPerUnit;
  out.rake = static_cast<int>(std::lround(contR));
  if (out.rake > kRakeLevelMax) out.rake = kRakeLevelMax;
  if (prev && std::fabs(contR - static_cast<float>(prev->rake)) <
                  0.5f + kHysteresis)
    out.rake = prev->rake;
  return out;
}

// --- THE PER-PIXEL LIGHTING OF THE INK -------------------------------------

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
  s.rake = static_cast<float>(q.rake) / static_cast<float>(kRakeLevelsPerUnit);
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

// THE ANSWER, lit from `S` with the strength dial's `gain`. Off (strength 0)
// is the caller's to short-circuit with letterpress::Terms::off, exactly as
// multiplierAt does. At gain 1 and rake <= 1 this is the spike's lighting and
// no pixel is darker than the fixed light's own worst case; above that the
// deboss deepens by exactly gain * rake, which is the point.
inline uint8_t multiplierFor(const Edge &e, const Shadow &S, float gain) {
  const float d = e.gx * S.dx + e.gy * S.dy;
  float shade = d;
  if (shade < 0.0f) shade = 0.0f;
  if (shade > 1.0f) shade = 1.0f;
  float lit = -d;
  if (lit < 0.0f) lit = 0.0f;
  if (lit > 1.0f) lit = 1.0f;
  const float deboss = e.depth * shade * S.rake * gain;
  const float reliefRake = S.rake > 1.0f ? 1.0f : S.rake;
  const float ring = e.ring * (1.0f - kRingReliefAt100 * lit * reliefRake);
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
        const uint32_t m = multiplierFor(e, any, 1.0f);
        field[i] = 0xFF000000u | (m << 16) | (m << 8) | m;
      }
    }
  }

  void relight(const Shadow &S, float gain) {
    for (size_t k = 0; k < edges.size(); ++k) {
      const uint32_t m = multiplierFor(edges[k], S, gain);
      field[edgeIndex[k]] = 0xFF000000u | (m << 16) | (m << 8) | m;
    }
  }
};

// --- THE SHEET UNDER THE LAMP ----------------------------------------------
//
// The lamp field's share of what the tooth, the wires and the show-through
// left the paper. Every pixel of the field darkens by at most this, so the
// marks (which take the rest) and the floor argument see one number.
constexpr float kLampShare = 0.75f;
inline float lampBudget(float paperLeftAfterShowThrough) {
  const float b = kLampShare * paperLeftAfterShowThrough;
  return b > 0.0f ? b : 0.0f;
}

// The lamp's distance from the sheet's center, in half-diagonals of the glass.
// A desk lamp ~40 cm from a phone: chosen, and it sets how uneven the light
// across the sheet is (63% corner to corner at the reference elevation).
constexpr float kLampDistance = 4.0f;
// A slope of one RMS unit facing squarely away from the reference lamp darkens
// by this fraction of the budget (times the page factor). Chosen so the
// shaded slopes read under the falloff rather than as a second noise. It was
// 0.5 in the first cut and the whole-page render read as hatched plaster.
constexpr float kReliefAt100 = 0.35f;
// The relief's octaves: the formation's own 3 cells (the same seed lane and
// lattice as letterpress::sheetToothMultiplierAt, so the lamp reveals the
// clouds the sheet already has), then fiber clumps at 12 and 48 cells across
// the sheet's SHORT side. Amplitudes halve per octave. The clump octaves are
// ROTATED off the screen's axes: value noise on a square lattice has its
// ridges along the lattice, and a directional derivative of it draws that
// lattice as a diagonal hatch (measured on the first cut, 2026-09-26). Two
// unrelated angles keep the two octaves from lining up with each other too.
constexpr int kFormationCells = letterpress::kFormationCells;
constexpr int kClumpCells1 = 12;
constexpr int kClumpCells2 = 48;
constexpr float kClumpRotate1Deg = 23.0f;
constexpr float kClumpRotate2Deg = 61.0f;
// The gradient is stored as int8 in units of 1/kGradScale RMS: +-4 RMS fits.
constexpr float kGradScale = 32.0f;
// The falloff is evaluated on a coarse grid and interpolated -- it is smooth.
constexpr int kFalloffGrid = 16;

// A light on the SCREEN: where it comes from, and how high it stands.
struct Light {
  float azDeg = 45.0f;    // clockwise from the top, the direction it comes FROM
  float elevDeg = kRefElevationDeg;
};

inline Light lightFor(const Quantized &q, int orientation) {
  Light L;
  L.azDeg = referenceScreenAzimuthDeg(orientation) +
            static_cast<float>(q.dir) * kStepDeg;
  L.elevDeg = elevationForRake(static_cast<float>(q.rake) /
                               static_cast<float>(kRakeLevelsPerUnit));
  return L;
}

// Irradiance at a point of the sheet from a lamp at kLampDistance in the
// direction `L`, relative units. p in half-diagonals, screen axes (y down, z
// out of the glass).
inline float irradiance(const Light &L, float px, float py) {
  const float e = L.elevDeg * kDegToRad, az = L.azDeg * kDegToRad;
  const float lx = std::cos(e) * std::sin(az), ly = -std::cos(e) * std::cos(az),
              lz = std::sin(e);
  const float dx = kLampDistance * lx - px, dy = kLampDistance * ly - py,
              dz = kLampDistance * lz;
  const float r2 = dx * dx + dy * dy + dz * dz;
  const float r = std::sqrt(r2);
  return dz / (r2 * r);  // cos(incidence) / r^2, with cos = dz / r
}

struct LampField {
  int w = 0, h = 0;      // the output it covers
  int cell = 2;          // output px per lattice px
  int lw = 0, lh = 0;    // lattice
  std::vector<int8_t> gx, gy;   // height gradient, kGradScale per RMS
  std::vector<uint32_t> field;  // ARGB lattice pixels, MOD texture
  float falloffRef = 1.0f;      // (1 - Emin/Emax) under the reference lamp
  // What the last relight was asked for, so a caller can see what is live.
  Light lastLight;
  float lastBudget = 0.0f;

  // Build the relief's gradient for this output. `extraHeight(x, y)` adds a
  // caller's own height in OUTPUT pixels (the test's ramp); the shipping
  // caller passes 0 -- the laid furrows were tried here and withdrawn, see
  // SurfaceSheet.cpp ensureLampTexture.
  template <typename ExtraHeight>
  void build(int outW, int outH, int cellPx, uint32_t seed,
             ExtraHeight extraHeight) {
    w = outW;
    h = outH;
    cell = cellPx < 1 ? 1 : cellPx;
    lw = (w + cell - 1) / cell;
    lh = (h + cell - 1) / cell;
    const size_t n = static_cast<size_t>(lw) * lh;
    std::vector<float> height(n);
    const float shortSide = static_cast<float>(w < h ? w : h);
    const float c1 = std::cos(kClumpRotate1Deg * kDegToRad),
                s1 = std::sin(kClumpRotate1Deg * kDegToRad);
    const float c2 = std::cos(kClumpRotate2Deg * kDegToRad),
                s2 = std::sin(kClumpRotate2Deg * kDegToRad);
    for (int j = 0; j < lh; ++j) {
      for (int i = 0; i < lw; ++i) {
        const float x = (static_cast<float>(i) + 0.5f) * cell;
        const float y = (static_cast<float>(j) + 0.5f) * cell;
        const float nx = x / static_cast<float>(w), ny = y / static_cast<float>(h);
        float v = phosphorgrain::valueNoise(nx * kFormationCells,
                                            ny * kFormationCells,
                                            seed ^ 0x464F524Du);
        const float u = x / shortSide, vv = y / shortSide;
        v += 0.5f * phosphorgrain::valueNoise(
                        (u * c1 - vv * s1) * kClumpCells1,
                        (u * s1 + vv * c1) * kClumpCells1, seed ^ 0x524C4631u);
        v += 0.25f * phosphorgrain::valueNoise(
                         (u * c2 - vv * s2) * kClumpCells2,
                         (u * s2 + vv * c2) * kClumpCells2, seed ^ 0x524C4632u);
        v += extraHeight(x, y);
        height[static_cast<size_t>(j) * lw + i] = v;
      }
    }
    std::vector<float> fx(n), fy(n);
    double sumSq = 0.0;
    for (int j = 0; j < lh; ++j) {
      for (int i = 0; i < lw; ++i) {
        const int i0 = i > 0 ? i - 1 : i, i1 = i < lw - 1 ? i + 1 : i;
        const int j0 = j > 0 ? j - 1 : j, j1 = j < lh - 1 ? j + 1 : j;
        const size_t k = static_cast<size_t>(j) * lw + i;
        const float dx = (height[static_cast<size_t>(j) * lw + i1] -
                          height[static_cast<size_t>(j) * lw + i0]) /
                         static_cast<float>(i1 - i0 > 0 ? i1 - i0 : 1);
        const float dy = (height[static_cast<size_t>(j1) * lw + i] -
                          height[static_cast<size_t>(j0) * lw + i]) /
                         static_cast<float>(j1 - j0 > 0 ? j1 - j0 : 1);
        fx[k] = dx;
        fy[k] = dy;
        sumSq += static_cast<double>(dx) * dx + static_cast<double>(dy) * dy;
      }
    }
    const float rms = n ? static_cast<float>(std::sqrt(sumSq / n)) : 0.0f;
    gx.assign(n, 0);
    gy.assign(n, 0);
    if (rms > 0.0f) {
      for (size_t k = 0; k < n; ++k) {
        auto q = [&](float v) {
          float s = v / rms * kGradScale;
          if (s > 127.0f) s = 127.0f;
          if (s < -127.0f) s = -127.0f;
          return static_cast<int8_t>(std::lround(s));
        };
        gx[k] = q(fx[k]);
        gy[k] = q(fy[k]);
      }
    }
    field.assign(n, 0xFFFFFFFFu);
    // The reference falloff: the lamp at its reference elevation along the
    // sheet's diagonal. Normalizes the falloff so the reference lamp spans
    // exactly [0, 1] of the page factor and a lower lamp spans more.
    Light ref;
    ref.azDeg = std::atan2(static_cast<float>(w), static_cast<float>(h)) / kDegToRad;
    ref.elevDeg = kRefElevationDeg;
    float emin = 0.0f, emax = 0.0f;
    falloffRange(ref, emin, emax);
    falloffRef = emax > 0.0f ? 1.0f - emin / emax : 1.0f;
    if (!(falloffRef > 1e-6f)) falloffRef = 1.0f;
  }

  // Min and max irradiance over the sheet, on the falloff grid.
  void falloffRange(const Light &L, float &emin, float &emax) const {
    emin = 1e30f;
    emax = 0.0f;
    const float halfDiag = 0.5f * std::sqrt(static_cast<float>(w) * w +
                                            static_cast<float>(h) * h);
    for (int gj = 0; gj <= kFalloffGrid; ++gj)
      for (int gi = 0; gi <= kFalloffGrid; ++gi) {
        const float px = (static_cast<float>(gi) / kFalloffGrid - 0.5f) * w / halfDiag;
        const float py = (static_cast<float>(gj) / kFalloffGrid - 0.5f) * h / halfDiag;
        const float e = irradiance(L, px, py);
        if (e < emin) emin = e;
        if (e > emax) emax = e;
      }
  }

  // Re-light the lattice. `budget` is the per-pixel darkening cap
  // (lampBudget()); 0 leaves the field white.
  void relight(const Light &L, const Dials &d, float budget) {
    lastLight = L;
    lastBudget = budget;
    const size_t n = static_cast<size_t>(lw) * lh;
    const float page = pageFactor(d.pagePct);
    if (!(budget > 0.0f) || !(page > 0.0f) || n == 0) {
      field.assign(n, 0xFFFFFFFFu);
      return;
    }
    // The falloff grid for this light, as darkening shape in [0, ~1.1].
    const int G = kFalloffGrid;
    std::vector<float> grid(static_cast<size_t>(G + 1) * (G + 1));
    float emin = 0.0f, emax = 0.0f;
    falloffRange(L, emin, emax);
    const float halfDiag = 0.5f * std::sqrt(static_cast<float>(w) * w +
                                            static_cast<float>(h) * h);
    for (int gj = 0; gj <= G; ++gj)
      for (int gi = 0; gi <= G; ++gi) {
        const float px = (static_cast<float>(gi) / G - 0.5f) * w / halfDiag;
        const float py = (static_cast<float>(gj) / G - 0.5f) * h / halfDiag;
        const float e = irradiance(L, px, py);
        grid[static_cast<size_t>(gj) * (G + 1) + gi] =
            emax > 0.0f ? (1.0f - e / emax) / falloffRef : 0.0f;
      }
    // The relief: slopes rising toward the lamp face away from it.
    const float az = L.azDeg * kDegToRad;
    const float fxl = std::sin(az), fyl = -std::cos(az);  // toward the lamp
    const float rake = rakeForElevation(L.elevDeg);
    const float reliefK = kReliefAt100 * rake / kGradScale;
    for (int j = 0; j < lh; ++j) {
      const float gyf = (static_cast<float>(j) + 0.5f) * cell / h * G;
      int gj = static_cast<int>(gyf);
      if (gj > G - 1) gj = G - 1;
      const float ty = gyf - gj;
      const float *g0 = grid.data() + static_cast<size_t>(gj) * (G + 1);
      const float *g1 = g0 + (G + 1);
      for (int i = 0; i < lw; ++i) {
        const float gxf = (static_cast<float>(i) + 0.5f) * cell / w * G;
        int gi = static_cast<int>(gxf);
        if (gi > G - 1) gi = G - 1;
        const float tx = gxf - gi;
        const float a = g0[gi] + (g0[gi + 1] - g0[gi]) * tx;
        const float b = g1[gi] + (g1[gi + 1] - g1[gi]) * tx;
        const float fall = a + (b - a) * ty;
        const size_t k = static_cast<size_t>(j) * lw + i;
        float relief = (static_cast<float>(gx[k]) * fxl +
                        static_cast<float>(gy[k]) * fyl) * reliefK;
        if (relief < 0.0f) relief = 0.0f;
        float shape = page * (fall + relief);
        if (shape > 1.0f) shape = 1.0f;
        if (shape < 0.0f) shape = 0.0f;
        const float m = 1.0f - budget * shape;
        const uint32_t v = static_cast<uint32_t>(m * 255.0f + 0.5f);
        field[k] = 0xFF000000u | (v << 16) | (v << 8) | v;
      }
    }
  }
};

}  // namespace rakinglight
