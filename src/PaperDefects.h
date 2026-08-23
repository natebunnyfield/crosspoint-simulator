#pragma once

// PAPER DEFECTS -- the marks a real sheet of historical paper carries.
//
// Owner order 2026-08-22, on top of the letterpress doctrine: foxing, red rag
// flecks, BLUE MARKS, brown stains, fly specks and wax spots, on a page that is
// THE SAME SHEET every time you turn back to it. Research, citations, the
// determinism model and the negative results: docs/paper-defects.md.
//
// SECOND ORDER, same day, after seeing a render: "raise the defect ceiling so
// 100% is actually distracting. be sure to include examples of flecks and marks
// and other paper making realism." The measured complaint was exact -- at dial
// 100 the strongest mark on a page moved a pixel by ~36 of 255 across a soft
// bloom, which is not what "distracting and not very legible" means.
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
// structurally by scaling every mark's depth -- see the budget scale below. A
// palette at the floor leaves nothing and the marks correctly vanish.
//
// WHAT THE BOUND ACTUALLY CONSTRAINS, and why the old ceiling was nowhere near
// it. The budget is denominated in MEAN luminance darkening over the sheet. The
// shipped table spent 0.00038 of it at dial 100 on a 792x528 sheet against the
// 0.483 the repo-default palette leaves -- a factor of about 1270 unspent. The
// marks were faint because their TINTS were faint, not because the safety
// argument made them faint. Sparse deep marks cost almost nothing in the mean:
// a fly speck is near-black and costs 6% of a budget that was already 1/1000
// spent. So the ceiling here is set by TASTE, and the floor is still set by the
// same structural scale it always was.
//
// Pure and host-tested for the same reason PhosphorGrain, Letterpress and
// PanelPalette are: every failure mode is a wrong PICTURE or an illegible page,
// and no compiler and no other test in this repo can see either.

#include <cmath>
#include <cstdint>

#include "PhosphorGrain.h"  // hash3 / unitFromHash / valueNoise, all pure

namespace paperdefects {

// THE DIAL IS AGE. Low, it is incidence alone -- how many marks, at the tints a
// young sheet carries. High, it is incidence AND substance: more marks, deeper
// marks, larger marks, and four kinds of damage a fresh sheet does not have.
constexpr int kDialOff = 0;
constexpr int kDialDefault = 30;
constexpr int kDialMax = 100;

inline int clampDial(int dialPercent) {
  if (dialPercent < kDialOff) return kDialOff;
  if (dialPercent > kDialMax) return kDialMax;
  return dialPercent;
}

// --- THE CURVE -------------------------------------------------------------
//
// The owner's brief has two ends and they pull opposite ways: 30 is "happens
// occasionally and not every page" and is ALREADY RIGHT, 100 is "distracting
// and not very legible" and is nowhere near. A single steeper linear law would
// have to move 30 to reach 100.
//
// So the dial is TWO terms, and only one of them is new:
//
//   incidence(d) = d / 100          the shipped linear law, untouched
//   surge(d)     = t^2, t = (d - 50) / 50, and exactly 0 at or below 50
//
// Everything the shipped model already did rides `incidence` and is bit-exact.
// Everything added here -- the deep tints, the larger radii, the extra counts,
// the deeper depth range, and all four new kinds -- rides `surge`, which is
// IDENTICALLY ZERO through the whole lower half of the dial. That is what
// makes "the bottom stays exactly where it is" a provable statement rather
// than an intention: at any dial <= 50 this model emits the same mark list,
// byte for byte, that shipped. tests/paper_defects_test.cpp pins it against
// frozen checksums taken from the shipped code.
//
// The square is chosen over a straight ramp because a straight ramp from 50
// would already be half-strength at 75, and the owner's word for the top is a
// QUARTER of the dial: surge(75) = 0.25, surge(90) = 0.64, surge(100) = 1. The
// visible change is concentrated where he asked for it.
constexpr int kSurgeStart = 50;

inline float surgeFor(int dialPercent) {
  const int d = clampDial(dialPercent);
  if (d <= kSurgeStart) return 0.0f;
  const float t = static_cast<float>(d - kSurgeStart) /
                  static_cast<float>(kDialMax - kSurgeStart);
  return t * t;
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
  // --- appended 2026-08-22 with the raised ceiling. APPEND ONLY: a kind's
  // integer is not persisted, but kKinds is indexed by it from three files.
  Shive,           // undigested wood-fibre splinter in cheap pulp
  // Crease and ClippingBurn lived here between 2026-08-22 and 2026-08-23 and
  // were REMOVED, not disabled: owner ruling, "anything with a long straight
  // line is too distracting." A fold's shadow and a clipping's acid edge are
  // both, essentially, a straight line drawn across the page, and the eye
  // tracks a line the way it does not track a blob. ShapeBand went with them.
  SetOff,          // a facing page's wet ink ghosted onto this one
  kKindCount
};

// HOW A MARK IS SHAPED. Three profiles, because the three things they draw are
// three different physical events.
enum Shape : int {
  ShapeBump = 0,  // soft quartic ellipse: a diffusion into the fibre mat
  ShapeDisc,      // hard ellipse with a short ramp: a particle sitting on top
  ShapeGhost,     // rotated rect, soft on both axes, striped like lines of type
};

// WHERE A MARK LANDS. Uniform unless the mechanism says otherwise.
enum Placement : int {
  PlaceUniform = 0,
  PlaceEdge,    // damp reaches the block's edges first (foxing)
  PlaceCenter,  // it is the TEXT BLOCK that offsets, and that is centred
};

// One kind's constants.
//
//   tint     -- per-channel MULTIPLIER at the mark's centre at full depth, at
//               surge 0. This is the SHIPPED column and none of it moved.
//   tintDeep -- the same at surge 1: the substance at full concentration.
//               Interpolated per mark in generate(), so the hue travels rather
//               than the old tint simply being scaled -- scaling a deficit
//               vector whose red channel is 1.00 can only ever produce a neon
//               orange, which is not what deep foxing looks like.
//   radiusMaxDeep -- the top of the size range at surge 1.
//   countAt100    -- incidence at dial 100 under the LINEAR law. Unchanged for
//                    the six shipped kinds; exactly 0 for the four new ones,
//                    which is what keeps dial <= 50 byte-identical.
//   countSurge    -- extra incidence, gated entirely behind the surge.
//   raggedAmp/Cells -- an edge-breaking noise multiply. It can only REDUCE the
//                    profile, which is what keeps the analytic bound an upper
//                    bound. Cells are separate per axis so a 400x2 px crease
//                    modulates along its length without dissolving across its
//                    width.
struct KindInfo {
  const char *name;
  int shape;
  int placement;
  float tint[3];
  float tintDeep[3];
  float radiusMin;      // fraction of min(w, h)
  float radiusMax;
  float radiusMaxDeep;
  float aspectMin;      // ry / rx
  float aspectMax;
  float angleSpan;      // multiple of pi the orientation may take
  int countAt100;
  int countSurge;
  float profileMean;    // mean of the profile over the mark's footprint
  float raggedAmp;
  float raggedCellsX;
  float raggedCellsY;
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

// The ghost is (1-u^2)^2 * (1-v^2)^2 over the same rect footprint. Each factor
// has mean 8/15 over [-1,1], so the product is (8/15)^2 = 0.2844, rounded up.
// Its stripe multiply only reduces further.
constexpr float kGhostProfileMean = 0.29f;

// The footprint AREA factor. An ellipse is pi*rx*ry; the rect shape is
// 4*rx*ry, and getting this wrong would under-state the bound by 27%.
inline float footprintFactorFor(int shape) {
  return shape == ShapeGhost ? 4.0f : 3.14159265f;
}

// CHOSEN, not measured -- no sheet was photographed for this repo, same honesty
// as Letterpress.h's component table. The ratios are what the sources describe:
// flecks are the commonest thing in rag paper, foxing next, blue and brown
// occasional, frass and wax rare, and the four damage kinds rarer still because
// they are things that happened TO a copy rather than things it was made with.
constexpr KindInfo kKinds[kKindCount] = {
    {"foxing", ShapeBump, PlaceEdge,
     {1.00f, 0.93f, 0.86f}, {0.62f, 0.40f, 0.24f},
     0.0055f, 0.0170f, 0.0340f, 0.65f, 1.00f, 1.0f, 14, 34,
     kSoftProfileMean, 0.70f, 0.42f, 0.42f},
    {"red rag", ShapeBump, PlaceUniform,
     {1.00f, 0.90f, 0.90f}, {0.80f, 0.32f, 0.34f},
     0.0016f, 0.0042f, 0.0075f, 0.16f, 0.36f, 1.0f, 22, 38,
     kSoftProfileMean, 0.0f, 0.0f, 0.0f},
    {"blue mark", ShapeBump, PlaceUniform,
     {0.92f, 0.94f, 1.00f}, {0.40f, 0.50f, 0.86f},
     0.0018f, 0.0060f, 0.0115f, 0.20f, 0.90f, 1.0f, 5, 11,
     kSoftProfileMean, 0.0f, 0.0f, 0.0f},
    {"brown stain", ShapeBump, PlaceUniform,
     {0.97f, 0.92f, 0.85f}, {0.72f, 0.58f, 0.42f},
     0.0300f, 0.0850f, 0.1450f, 0.55f, 1.00f, 1.0f, 3, 5,
     kSoftProfileMean, 0.0f, 0.0f, 0.0f},
    {"fly speck", ShapeDisc, PlaceUniform,
     {0.10f, 0.10f, 0.11f}, {0.05f, 0.05f, 0.055f},
     0.0010f, 0.0024f, 0.0044f, 0.70f, 1.00f, 1.0f, 6, 18,
     kHardProfileMean, 0.0f, 0.0f, 0.0f},
    {"wax spot", ShapeBump, PlaceUniform,
     {0.965f, 0.965f, 0.96f}, {0.86f, 0.855f, 0.83f},
     0.0120f, 0.0320f, 0.0520f, 0.60f, 1.00f, 1.0f, 2, 3,
     kSoftProfileMean, 0.0f, 0.0f, 0.0f},
    // --- the four appended kinds. countAt100 is 0 for every one of them: they
    // are reachable ONLY through the surge, which is what buys the byte-exact
    // lower half. See docs/paper-defects.md for the sources and the rejects.
    {"shive", ShapeDisc, PlaceUniform,
     {0.86f, 0.78f, 0.66f}, {0.40f, 0.29f, 0.17f},
     0.0022f, 0.0060f, 0.0110f, 0.12f, 0.30f, 1.0f, 0, 40,
     kHardProfileMean, 0.0f, 0.0f, 0.0f},
    {"set-off", ShapeGhost, PlaceCenter,
     {0.965f, 0.955f, 0.94f}, {0.72f, 0.68f, 0.60f},
     0.1800f, 0.2600f, 0.3400f, 0.70f, 1.10f, 0.05f, 0, 2,
     kGhostProfileMean, 0.70f, 2.00f, 0.160f},
};

// DEPTH. The shipped range is 0.55..1.0 and it is what surge 0 still renders.
// At surge 1 the FLOOR of the range rises: on a badly aged sheet few marks are
// faint, which is most of what separates "old paper" from "a page with some
// dots on it". The span narrows so the top stays exactly 1.0 and no new worst
// case is invented above what the tint table already bounds.
constexpr float kDepthMinLo = 0.55f;
constexpr float kDepthSpanLo = 0.45f;
constexpr float kDepthMinHi = 0.72f;
constexpr float kDepthSpanHi = 0.28f;

// A hard cap so the rasterizer's storage is a fixed array. Dial 100 asks for at
// most ~300 marks including foxing's satellites; this leaves real headroom, and
// the test asserts the cap is never reached (hitting it would silently starve
// the later kinds, which are exactly the new ones).
constexpr int kMaxMarks = 512;

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
  float depth = 0.0f;           // 0..1 scale on this mark's tint deficit
  // THE RESOLVED TINT, lerped kind.tint -> kind.tintDeep by the dial's surge.
  // It lives on the mark rather than being looked up from kKinds so that
  // multiplierAt and markDarkeningBound cannot disagree about which end of the
  // ramp a mark is on -- they are called from different files.
  float tint[3] = {1.0f, 1.0f, 1.0f};
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
// exact upper bound: peak deficit x profile mean x footprint / sheet area. The
// footprint is closed form for both the ellipse and the rect shapes, and the
// affine change of variables leaves the profile mean unchanged, so this is
// arithmetic rather than sampling.
inline float markDarkeningBound(const Mark &m, int w, int h) {
  if (w <= 0 || h <= 0) return 0.0f;
  const KindInfo &k = kKinds[m.kind];
  const float area = footprintFactorFor(k.shape) * m.rx * m.ry;
  return area * k.profileMean * m.depth * lumDeficitOf(m.tint) /
         (static_cast<float>(w) * static_cast<float>(h));
}

inline float meanDarkeningBound(const Mark *marks, int n, int w, int h) {
  float sum = 0.0f;
  for (int i = 0; i < n; ++i) sum += markDarkeningBound(marks[i], w, h);
  return sum;
}

// The LINEAR half of the incidence law, exactly as it shipped: how many marks
// of one kind the dial asks for before the surge is considered. Rounded, so the
// ladder is visible rather than something a test has to squint at.
inline int countFor(int kind, int dialPercent) {
  const int dial = clampDial(dialPercent);
  if (dial == kDialOff) return 0;
  const float n = static_cast<float>(kKinds[kind].countAt100) *
                  static_cast<float>(dial) / 100.0f;
  int c = static_cast<int>(n + 0.5f);
  if (c < 0) c = 0;
  return c;
}

// The SURGE half, which is where the raised ceiling lives. Fractional counts
// are resolved per PAGE by a Bernoulli draw rather than by rounding, so a kind
// whose expectation is 0.4 marks "happens occasionally and not every page" --
// the owner's own words for what the low end should feel like, applied to the
// rare damage kinds at the high end. Exactly 0 at any dial <= 50, on every
// kind, because surge is exactly 0 there.
inline int surgeCountFor(int kind, int dialPercent, uint32_t seed) {
  const float surge = surgeFor(dialPercent);
  if (surge <= 0.0f) return 0;
  const float x = static_cast<float>(kKinds[kind].countSurge) * surge;
  int whole = static_cast<int>(x);
  const float frac = x - static_cast<float>(whole);
  const uint32_t h = phosphorgrain::hash3(static_cast<uint32_t>(kind) + 1u,
                                          0x53524745u /* 'SRGE' */, seed);
  if (phosphorgrain::unitFromHash(h) < frac) whole += 1;
  return whole < 0 ? 0 : whole;
}

// The whole incidence law. This is what generate() uses.
inline int totalCountFor(int kind, int dialPercent, uint32_t seed) {
  return countFor(kind, dialPercent) + surgeCountFor(kind, dialPercent, seed);
}

// THE MARK LIST, deterministic in (seed, dial, sheet size) and nothing else.
//
// Three structural things happen here rather than in the rasterizer:
//
//   * FOXING CLUSTERS. Foxing is damp-driven and does not arrive as isolated
//     dots; each generated spot may carry one or two satellites within a couple
//     of radii. Satellites are ordinary marks and are counted in the total, so
//     the budget below sees them.
//   * THE SURGE. Above dial 50 the tint travels toward tintDeep, the size range
//     opens to radiusMaxDeep, the depth range's floor rises, and the extra
//     counts arrive. Below 50 every one of those terms is identically the
//     shipped value, which is why the lower half of the dial is byte-exact.
//   * THE BUDGET SCALE. The bound above is summed over the whole list, and if
//     it exceeds p.remainingBudget every depth is scaled by the ratio. The
//     rendered mean is then <= the bound by four independent margins:
//     overlapping multiplicative marks satisfy (1-a)(1-b) >= 1-a-b so the sum
//     over-counts; the ragged-edge noise only REDUCES the profile; the
//     per-channel floor only RAISES the multiplier; and ink masking raises it
//     further.
//
// Returns the number written to `out`, which must hold kMaxMarks.
inline int generate(const Params &p, int w, int h, Mark *out) {
  if (!out || w <= 0 || h <= 0) return 0;
  const int dial = clampDial(p.dialPercent);
  if (dial == kDialOff) return 0;
  const float surge = surgeFor(dial);
  const float shortEdge =
      static_cast<float>(w < h ? w : h);
  int n = 0;

  for (int kind = 0; kind < kKindCount; ++kind) {
    const KindInfo &k = kKinds[kind];
    const int count = totalCountFor(kind, dial, p.seed);
    // The size range and the depth range both open with the surge. Hoisted out
    // of the per-mark loop because they depend on the dial, not on the mark.
    const float radiusTop =
        k.radiusMax + (k.radiusMaxDeep - k.radiusMax) * surge;
    const float depthMin = kDepthMinLo + (kDepthMinHi - kDepthMinLo) * surge;
    const float depthSpan = kDepthSpanLo + (kDepthSpanHi - kDepthSpanLo) * surge;
    for (int i = 0; i < count && n < kMaxMarks; ++i) {
      const uint32_t base = phosphorgrain::hash3(
          static_cast<uint32_t>(kind) * 0x9E3779B9u,
          static_cast<uint32_t>(i) + 1u, p.seed ^ 0x4D41524Bu);  // 'MARK'
      float u = phosphorgrain::unitFromHash(base);
      float v = phosphorgrain::unitFromHash(
          phosphorgrain::hash3(base, 0x1u, p.seed));
      // FOXING IS EDGE-BIASED: damp reaches the block's edges first, so the
      // position is pushed outward by a curve that leaves the centre sparse
      // without ever emptying it. Set-off is the mirror case -- it is the TEXT
      // BLOCK that transfers, and that is centred -- and a clipping is laid
      // along one edge, across the page.
      auto toEdge = [](float t) {
        const float c = t * 2.0f - 1.0f;
        const float s = c < 0.0f ? -1.0f : 1.0f;
        return 0.5f + 0.5f * s * std::sqrt(std::fabs(c));
      };
      auto toCenter = [](float t) {
        const float c = t * 2.0f - 1.0f;
        const float s = c < 0.0f ? -1.0f : 1.0f;
        return 0.5f + 0.5f * s * c * c;
      };
      if (k.placement == PlaceEdge) {
        u = toEdge(u);
        v = toEdge(v);
      } else if (k.placement == PlaceCenter) {
        u = toCenter(u);
        v = toCenter(v);
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
      m.rx = (k.radiusMin + rUnit * (radiusTop - k.radiusMin)) * shortEdge;
      if (m.rx < 0.75f) m.rx = 0.75f;  // never sub-pixel: that is a no-op mark
      m.ry = m.rx * (k.aspectMin + aUnit * (k.aspectMax - k.aspectMin));
      if (m.ry < 0.75f) m.ry = 0.75f;
      // angleSpan 1.0 is the shipped full half-turn; the multiply by exactly
      // 1.0f is exact in float, so the six shipped kinds keep their angles.
      const float ang = angUnit * 3.14159265f * k.angleSpan;
      m.cosA = std::cos(ang);
      m.sinA = std::sin(ang);
      m.depth = depthMin + depthSpan * dUnit;
      for (int c = 0; c < 3; ++c)
        m.tint[c] = k.tint[c] + (k.tintDeep[c] - k.tint[c]) * surge;
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
  float ex, ey;
  if (kKinds[m.kind].shape == ShapeGhost) {
    // A rotated RECT reaches its corners, which is strictly further out than
    // the inscribed ellipse. Using the ellipse form here would clip the rect
    // kind along its diagonals, which reads as a rendering artifact rather
    // than as a bug in a bounds function.
    ex = std::fabs(m.rx * m.cosA) + std::fabs(m.ry * m.sinA);
    ey = std::fabs(m.rx * m.sinA) + std::fabs(m.ry * m.cosA);
  } else {
    // A rotated ellipse's axis-aligned extent. Cheap over-estimate by the
    // larger radius would double the rasterized area of a long red-rag fleck,
    // which is the commonest mark, so the exact form is worth the two
    // multiplies.
    ex = std::sqrt(m.rx * m.rx * m.cosA * m.cosA +
                   m.ry * m.ry * m.sinA * m.sinA);
    ey = std::sqrt(m.rx * m.rx * m.sinA * m.sinA +
                   m.ry * m.ry * m.cosA * m.cosA);
  }
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

  const KindInfo &k = kKinds[m.kind];
  float f;
  if (k.shape == ShapeGhost) {
    // SET-OFF. A soft rectangle the size of the facing page's text block,
    // striped along its short axis by the ragged multiply below, which is what
    // makes it read as ghosted LINES of type rather than as a smudge.
    if (rxv <= -1.0f || rxv >= 1.0f || ryv <= -1.0f || ryv >= 1.0f)
      return false;
    const float a = 1.0f - rxv * rxv;
    const float b = 1.0f - ryv * ryv;
    f = a * a * b * b;
  } else {
    float u2 = rxv * rxv + ryv * ryv;
    if (u2 >= 1.0f) return false;
    const float s = 1.0f - u2;
    if (k.shape == ShapeDisc) {
      // A hard disc with a short ramp. Frass is a particle, not a diffusion,
      // and so is a wood shive.
      f = s >= kSpeckRamp ? 1.0f : s / kSpeckRamp;
    } else {
      f = s * s;
    }
  }
  if (k.raggedAmp > 0.0f) {
    // A RAGGED EDGE. Foxing is fungal and metallic in a fibre mat; a clean
    // ellipse reads as a printed dot. The noise can only REDUCE f, which is
    // also what keeps the analytic bound above an upper bound. The cell counts
    // are per axis so set-off stripes horizontally rather than dissolving.
    const float nx = (static_cast<float>(x) - m.cx) / (m.rx * k.raggedCellsX);
    const float ny = (static_cast<float>(y) - m.cy) / (m.ry * k.raggedCellsY);
    f *= (1.0f - k.raggedAmp) +
         k.raggedAmp * phosphorgrain::valueNoise(nx, ny, m.salt);
  }
  if (f <= 0.0f) return false;

  const float d = f * m.depth;
  for (int c = 0; c < 3; ++c) {
    float v = 1.0f - d * (1.0f - m.tint[c]);
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
