#pragma once

// PAPER DEFECTS -- the marks a real sheet of historical paper carries.
//
// Owner order 2026-08-22, on top of the letterpress doctrine: foxing, red rag
// flecks, BLUE MARKS, brown stains, fly specks and wax spots, on a page that is
// THE SAME SHEET every time you turn back to it. Research, citations, the
// determinism model and the negative results: docs/paper-defects.md.
//
// THE WORD IS "BLUE MARKS" -- blue ink, blue dye, blue rag fibre. Not the Mars
// pigment family; the string "mars" appears nowhere in this repo's code, docs
// or settings strings, deliberately.
//
// WHAT THIS FILE IS. A pure, clock-free model that turns a page seed and a
// 0..100 dial into a deterministic list of MARKS, plus the per-channel
// multiplier each mark paints. It is folded into the SHEET field
// (HalDisplay::ensureSheetToothTexture) as a second rasterizing pass over each
// mark's own bounding box, so one texture, one upload, one draw, and the cost
// is proportional to the marks' area rather than the sheet's.
//
// PER-CHANNEL, and that is new here. Every other field in this repo is
// achromatic because a coverage deficit in a phosphor emits less of its OWN
// colour. A foxing spot is not that: it is a different substance ON the sheet,
// and it is brown. SDL_BLENDMODE_MOD multiplies channels independently, so a
// coloured mark is legal and still strictly darkening.
//
// WHY IT NEEDS ITS OWN FLOOR. letterpress::kMinMultiplier = 0.25 exists
// SPECIFICALLY to forbid specks -- "Never take a texel out entirely; a black
// speck is a defect, not impression". A fly speck IS the thing that comment
// forbids. So this layer gets its own, lower, per-channel floor and its own
// function, and never rides sheetToothMultiplierAt.
//
// WHY IT NEEDS ITS OWN BUDGET ARITHMETIC. letterpress::paperBudget is the
// largest MEAN paper darkening the live palette can take before 7:1 breaks, and
// the TOOTH already spends against it. Defects take what is LEFT
// (letterpress::remainingPaperBudget), and generate() enforces that
// structurally by scaling every mark's depth -- see kProfileMean below. A
// palette at the floor leaves nothing and the marks correctly vanish.
//
// Pure and host-tested for the same reason PhosphorGrain, Letterpress and
// PanelPalette are: every failure mode is a wrong PICTURE or an illegible page,
// and no compiler and no other test in this repo can see either.

#include <cmath>
#include <cstdint>

#include "PhosphorGrain.h"  // hash3 / unitFromHash / valueNoise, all pure

namespace paperdefects {

// THE DIAL IS INCIDENCE, not depth. Turning it up gives an older book, not a
// dirtier ink: the counts scale, the tints and depths do not.
constexpr int kDialOff = 0;
constexpr int kDialDefault = 30;
constexpr int kDialMax = 100;

inline int clampDial(int dialPercent) {
  if (dialPercent < kDialOff) return kDialOff;
  if (dialPercent > kDialMax) return kDialMax;
  return dialPercent;
}

// THIS LAYER'S OWN FLOOR, per channel, and deliberately far below
// letterpress::kMinMultiplier. A fly speck is frass: it really is nearly black
// and really is a few pixels across. Not zero, because a hole in the sheet is a
// different phenomenon and this is not it.
constexpr float kMinMultiplier = 0.04f;

enum Kind : int {
  Foxing = 0,      // iron/fungal oxidation, clustered, edge-biased, ragged
  RedRag,          // dyed rag shives from the beater, short and oriented
  BlueMark,        // blue rag fibre, blue ink, laundry-blue offset
  BrownStain,      // tannin migration and old water damage, large and soft
  FlySpeck,        // insect frass, hard-edged and near-black
  WaxSpot,         // candle wax / sebum, locally translucent, very shallow
  kKindCount
};

// One kind's constants. `tint` is the per-channel MULTIPLIER at the mark's
// centre at full depth; `radius*` are fractions of the sheet's short edge;
// `count` is how many appear at dial 100.
struct KindInfo {
  const char *name;
  float tint[3];
  float radiusMin;   // fraction of min(w, h)
  float radiusMax;
  float aspectMin;   // ry / rx
  float aspectMax;
  int countAt100;
  float profileMean; // mean of the radial profile over the mark's footprint
};

// The quartic bump (1 - u^2)^2 integrates to exactly 1/3 of its peak over its
// own footprint: int_0^1 (1-s)^2 ds = 1/3 after s = u^2. Every soft mark uses
// it, so its mean is a CONSTANT rather than a measurement -- which is what
// makes the safety bound in generate() analytic.
constexpr float kSoftProfileMean = 1.0f / 3.0f;
// The fly speck is a hard disc with a short ramp: f = min(1, (1-u^2)/0.3).
// Mean = 0.7 + (1/0.3) * int_0.7^1 (1-s) ds = 0.7 + 0.15 = 0.85.
constexpr float kHardProfileMean = 0.85f;
constexpr float kSpeckRamp = 0.3f;

// CHOSEN, not measured -- no sheet was photographed for this repo, same honesty
// as Letterpress.h's component table. The ratios are what the sources describe:
// flecks are the commonest thing in rag paper, foxing next, blue and brown
// occasional, frass and wax rare.
constexpr KindInfo kKinds[kKindCount] = {
    // name          tint (r,g,b)              rMin     rMax     aspect      n  profile
    {"foxing",       {1.00f, 0.93f, 0.86f}, 0.0055f, 0.0170f, 0.65f, 1.00f, 14, kSoftProfileMean},
    {"red rag",      {1.00f, 0.90f, 0.90f}, 0.0016f, 0.0042f, 0.16f, 0.36f, 22, kSoftProfileMean},
    {"blue mark",    {0.92f, 0.94f, 1.00f}, 0.0018f, 0.0060f, 0.20f, 0.90f,  5, kSoftProfileMean},
    {"brown stain",  {0.97f, 0.92f, 0.85f}, 0.0300f, 0.0850f, 0.55f, 1.00f,  3, kSoftProfileMean},
    {"fly speck",    {0.10f, 0.10f, 0.11f}, 0.0010f, 0.0024f, 0.70f, 1.00f,  6, kHardProfileMean},
    {"wax spot",     {0.965f, 0.965f, 0.96f}, 0.0120f, 0.0320f, 0.60f, 1.00f, 2, kSoftProfileMean},
};

// A hard cap so the rasterizer's storage is a fixed array. Well above the 52
// marks dial 100 asks for, including foxing's satellites.
constexpr int kMaxMarks = 256;

struct Params {
  int dialPercent = kDialOff;
  // THE PAGE SEED. On the identity path this is hash3 of (bookKey, spine,
  // page) with no launch term at all -- that is the whole headline claim, and
  // mixing grainSeed() back in would silently falsify it.
  uint32_t seed = 0x44454653u;  // 'DEFS'
  // What letterpress::remainingPaperBudget(...) left. 1.0 means "no
  // constraint", for a caller that does not know the palette; 0 means the
  // palette is at the floor and there is nothing to spend.
  float remainingBudget = 1.0f;
};

struct Mark {
  int kind = 0;
  float cx = 0.0f, cy = 0.0f;   // centre, in sheet pixels
  float rx = 1.0f, ry = 1.0f;   // radii, in sheet pixels
  float cosA = 1.0f, sinA = 0.0f;  // orientation
  float depth = 0.0f;           // 0..1 scale on the kind's tint deficit
  uint32_t salt = 0;            // this mark's own texture lane
};

// sRGB relative luminance of a per-channel DEFICIT -- the same weights the
// contrast floor uses everywhere else in this repo. Deliberately linear in the
// deficit rather than a gamma round-trip: the floor argument is about mean
// multiplier, and a mean of multipliers is what the budget is denominated in.
inline float lumDeficitOf(const float tint[3]) {
  const float d = 0.2126f * (1.0f - tint[0]) + 0.7152f * (1.0f - tint[1]) +
                  0.0722f * (1.0f - tint[2]);
  return d > 0.0f ? d : 0.0f;
}

// The mean luminance darkening ONE mark contributes over the whole sheet, as an
// exact upper bound: peak deficit x profile mean x footprint / sheet area. An
// ellipse's area is pi*rx*ry and the affine change of variables leaves the
// profile mean unchanged, so this is closed form rather than sampled.
inline float markDarkeningBound(const Mark &m, int w, int h) {
  if (w <= 0 || h <= 0) return 0.0f;
  const KindInfo &k = kKinds[m.kind];
  const float area = 3.14159265f * m.rx * m.ry;
  return area * k.profileMean * m.depth * lumDeficitOf(k.tint) /
         (static_cast<float>(w) * static_cast<float>(h));
}

inline float meanDarkeningBound(const Mark *marks, int n, int w, int h) {
  float sum = 0.0f;
  for (int i = 0; i < n; ++i) sum += markDarkeningBound(marks[i], w, h);
  return sum;
}

// How many marks of one kind at this dial. Linear in the dial and rounded, so
// the ladder is visible: at 30 the six kinds give 4/7/2/1/2/1 = 17 marks
// against 52 at 100, which is a difference a test can measure rather than
// squint at.
inline int countFor(int kind, int dialPercent) {
  const int dial = clampDial(dialPercent);
  if (dial == kDialOff) return 0;
  const float n = static_cast<float>(kKinds[kind].countAt100) *
                  static_cast<float>(dial) / 100.0f;
  int c = static_cast<int>(n + 0.5f);
  if (c < 0) c = 0;
  return c;
}

// THE MARK LIST, deterministic in (seed, dial, sheet size) and nothing else.
//
// Two structural things happen here rather than in the rasterizer:
//
//   * FOXING CLUSTERS. Foxing is damp-driven and does not arrive as isolated
//     dots; each generated spot may carry one or two satellites within a couple
//     of radii. Satellites are ordinary marks and are counted in the total, so
//     the budget below sees them.
//   * THE BUDGET SCALE. The bound above is summed over the whole list, and if
//     it exceeds p.remainingBudget every depth is scaled by the ratio. The
//     rendered mean is then <= the bound by four independent margins:
//     overlapping multiplicative marks satisfy (1-a)(1-b) >= 1-a-b so the sum
//     over-counts; foxing's edge noise only REDUCES the profile; the per-channel
//     floor only RAISES the multiplier; and ink masking raises it further.
//
// Returns the number written to `out`, which must hold kMaxMarks.
inline int generate(const Params &p, int w, int h, Mark *out) {
  if (!out || w <= 0 || h <= 0) return 0;
  const int dial = clampDial(p.dialPercent);
  if (dial == kDialOff) return 0;
  const float shortEdge =
      static_cast<float>(w < h ? w : h);
  int n = 0;

  for (int kind = 0; kind < kKindCount; ++kind) {
    const KindInfo &k = kKinds[kind];
    const int count = countFor(kind, dial);
    for (int i = 0; i < count && n < kMaxMarks; ++i) {
      const uint32_t base = phosphorgrain::hash3(
          static_cast<uint32_t>(kind) * 0x9E3779B9u,
          static_cast<uint32_t>(i) + 1u, p.seed ^ 0x4D41524Bu);  // 'MARK'
      float u = phosphorgrain::unitFromHash(base);
      float v = phosphorgrain::unitFromHash(
          phosphorgrain::hash3(base, 0x1u, p.seed));
      // FOXING IS EDGE-BIASED: damp reaches the block's edges first, so the
      // position is pushed outward by a curve that leaves the centre sparse
      // without ever emptying it.
      if (kind == Foxing) {
        auto toEdge = [](float t) {
          const float c = t * 2.0f - 1.0f;
          const float s = c < 0.0f ? -1.0f : 1.0f;
          return 0.5f + 0.5f * s * std::sqrt(std::fabs(c));
        };
        u = toEdge(u);
        v = toEdge(v);
      }
      const float rUnit = phosphorgrain::unitFromHash(
          phosphorgrain::hash3(base, 0x2u, p.seed));
      const float aUnit = phosphorgrain::unitFromHash(
          phosphorgrain::hash3(base, 0x3u, p.seed));
      const float angUnit = phosphorgrain::unitFromHash(
          phosphorgrain::hash3(base, 0x4u, p.seed));
      const float dUnit = phosphorgrain::unitFromHash(
          phosphorgrain::hash3(base, 0x5u, p.seed));

      Mark m;
      m.kind = kind;
      m.cx = u * static_cast<float>(w);
      m.cy = v * static_cast<float>(h);
      m.rx = (k.radiusMin + rUnit * (k.radiusMax - k.radiusMin)) * shortEdge;
      if (m.rx < 0.75f) m.rx = 0.75f;  // never sub-pixel: that is a no-op mark
      m.ry = m.rx * (k.aspectMin + aUnit * (k.aspectMax - k.aspectMin));
      if (m.ry < 0.75f) m.ry = 0.75f;
      const float ang = angUnit * 3.14159265f;
      m.cosA = std::cos(ang);
      m.sinA = std::sin(ang);
      // Depth 0.55..1.0: no mark is at full strength by default, and none is so
      // faint it is a wasted rasterization.
      m.depth = 0.55f + 0.45f * dUnit;
      m.salt = phosphorgrain::hash3(base, 0x6u, p.seed);
      out[n++] = m;

      if (kind != Foxing) continue;
      // ...and its satellites.
      const uint32_t sc = phosphorgrain::hash3(base, 0x7u, p.seed);
      const int satellites = static_cast<int>(sc % 3u);
      for (int s = 0; s < satellites && n < kMaxMarks; ++s) {
        const uint32_t sh =
            phosphorgrain::hash3(base, 0x10u + static_cast<uint32_t>(s), p.seed);
        const float dx = (phosphorgrain::unitFromHash(sh) * 2.0f - 1.0f) * 2.6f;
        const float dy =
            (phosphorgrain::unitFromHash(sh ^ 0x5BD1E995u) * 2.0f - 1.0f) * 2.6f;
        Mark sat = m;
        sat.cx = m.cx + dx * m.rx;
        sat.cy = m.cy + dy * m.ry;
        sat.rx = m.rx * (0.35f + 0.4f * phosphorgrain::unitFromHash(sh >> 8));
        if (sat.rx < 0.75f) sat.rx = 0.75f;
        sat.ry = sat.rx * (m.ry / (m.rx > 0.0f ? m.rx : 1.0f));
        if (sat.ry < 0.75f) sat.ry = 0.75f;
        sat.depth = m.depth * 0.8f;
        sat.salt = sh;
        out[n++] = sat;
      }
    }
  }

  // THE BUDGET SCALE. Structural, not advisory: after this the rendered mean
  // paper darkening from defects cannot exceed what the palette had left.
  const float budget = p.remainingBudget > 0.0f ? p.remainingBudget : 0.0f;
  const float bound = meanDarkeningBound(out, n, w, h);
  if (bound > budget) {
    const float scale = bound > 0.0f ? budget / bound : 0.0f;
    for (int i = 0; i < n; ++i) out[i].depth *= scale;
  }
  return n;
}

// The mark's bounding box in sheet pixels, inclusive of x0/y0 and exclusive of
// x1/y1, already clipped to the sheet. Returns false when nothing is visible.
inline bool bounds(const Mark &m, int w, int h, int &x0, int &y0, int &x1,
                   int &y1) {
  // A rotated ellipse's axis-aligned extent. Cheap over-estimate by the larger
  // radius would double the rasterized area of a long red-rag fleck, which is
  // the commonest mark, so the exact form is worth the two multiplies.
  const float ex = std::sqrt(m.rx * m.rx * m.cosA * m.cosA +
                             m.ry * m.ry * m.sinA * m.sinA);
  const float ey = std::sqrt(m.rx * m.rx * m.sinA * m.sinA +
                             m.ry * m.ry * m.cosA * m.cosA);
  x0 = static_cast<int>(std::floor(m.cx - ex));
  y0 = static_cast<int>(std::floor(m.cy - ey));
  x1 = static_cast<int>(std::ceil(m.cx + ex)) + 1;
  y1 = static_cast<int>(std::ceil(m.cy + ey)) + 1;
  if (x0 < 0) x0 = 0;
  if (y0 < 0) y0 = 0;
  if (x1 > w) x1 = w;
  if (y1 > h) y1 = h;
  return x0 < x1 && y0 < y1;
}

// The per-channel multiplier this ONE mark paints at (x, y). Writes 1,1,1 and
// returns false when the pixel is outside the footprint, so a caller can skip
// the fold. Strictly in (0, 1]: this layer can only ever darken, same contract
// as every other field in this repo.
inline bool multiplierAt(const Mark &m, int x, int y, float mult[3]) {
  mult[0] = mult[1] = mult[2] = 1.0f;
  const float dx = static_cast<float>(x) + 0.5f - m.cx;
  const float dy = static_cast<float>(y) + 0.5f - m.cy;
  const float rxv = (dx * m.cosA + dy * m.sinA) / (m.rx > 0.0f ? m.rx : 1.0f);
  const float ryv = (-dx * m.sinA + dy * m.cosA) / (m.ry > 0.0f ? m.ry : 1.0f);
  float u2 = rxv * rxv + ryv * ryv;
  if (u2 >= 1.0f) return false;

  const KindInfo &k = kKinds[m.kind];
  float f;
  if (m.kind == FlySpeck) {
    // A hard disc with a short ramp. Frass is a particle, not a diffusion.
    const float s = 1.0f - u2;
    f = s >= kSpeckRamp ? 1.0f : s / kSpeckRamp;
  } else {
    const float s = 1.0f - u2;
    f = s * s;
  }
  if (m.kind == Foxing) {
    // A RAGGED EDGE. Foxing is fungal and metallic in a fibre mat; a clean
    // ellipse reads as a printed dot. The noise can only REDUCE f, which is
    // also what keeps the analytic bound above an upper bound.
    const float nx = (static_cast<float>(x) - m.cx) / (m.rx * 0.42f);
    const float ny = (static_cast<float>(y) - m.cy) / (m.ry * 0.42f);
    f *= 0.30f + 0.70f * phosphorgrain::valueNoise(nx, ny, m.salt);
  }
  if (f <= 0.0f) return false;

  const float d = f * m.depth;
  for (int c = 0; c < 3; ++c) {
    float v = 1.0f - d * (1.0f - k.tint[c]);
    if (v < kMinMultiplier) v = kMinMultiplier;
    if (v > 1.0f) v = 1.0f;
    mult[c] = v;
  }
  return true;
}

// INK MASKS DEFECTS. A mark sits ON the sheet; ink is printed on top of it, so
// the multiplier lerps to 1 as inkness goes to 1. Physically right, and it is
// what protects legibility at every dial setting. inkness is 0 at bare paper,
// 1 at solid ink.
inline void applyInkMask(float mult[3], float inkness) {
  float t = inkness;
  if (t < 0.0f) t = 0.0f;
  if (t > 1.0f) t = 1.0f;
  // Bare paper is EXACT, not almost-exact: 1 - (1 - m) * 1 is not m in float,
  // and a mask that perturbs every unmasked texel by one ulp would make "the
  // same page is the same sheet" depend on which pixels happened to be near a
  // rounding boundary.
  if (t == 0.0f) return;
  for (int c = 0; c < 3; ++c) mult[c] = 1.0f - (1.0f - mult[c]) * (1.0f - t);
}

}  // namespace paperdefects
