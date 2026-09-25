// Host test for src/RakingLight.h, and for the split of letterpress::
// multiplierAt into termsAt + a combiner that it needed.
//
// Every failure mode here is a wrong picture or a thrashing field:
//   - the split changes the SHIPPED letterpress by one code value somewhere
//     (the feature is off by default, so this is the one that ships);
//   - a tilt deepens a shadow past what the fixed light could ever draw, or
//     touches flat paper, which every contrast-floor proof assumes it cannot;
//   - the light turns the wrong way for the tilt, or does not come back to
//     exactly today's when the phone does;
//   - the edge-only recompose disagrees with a full per-pixel light;
//   - quantization without hysteresis flips on a tremor.
// No compiler and no other test sees any of these.

#include "Letterpress.h"
#include "RakingLight.h"

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <vector>

#include "TestCheck.h"
using testcheck::check;

static int &failures = testcheck::g_failures;

namespace legacy {
using namespace letterpress;
// VERBATIM the body of letterpress::multiplierAt as of dbe49da, before the
// termsAt split. Kept here, frozen, so the split is compared against the
// arithmetic that shipped rather than against itself.
inline uint8_t legacyMultiplierAt(const Params &p, const float win[3][3], int x,
                            int y, int w, int h) {
  const int strength = clampStrength(p.strengthPercent);
  if (strength == kStrengthOff || w <= 0 || h <= 0) return 255;
  const float s = static_cast<float>(strength) /
                  static_cast<float>(kStrengthStandard);

  const float t = win[1][1];  // inkness at the pixel itself

  // Sobel, normalized so a full paper-to-ink step is magnitude 1.
  const float gx = ((win[0][2] + 2.0f * win[1][2] + win[2][2]) -
                    (win[0][0] + 2.0f * win[1][0] + win[2][0])) * 0.25f;
  const float gy = ((win[2][0] + 2.0f * win[2][1] + win[2][2]) -
                    (win[0][0] + 2.0f * win[0][1] + win[0][2])) * 0.25f;
  float gmag = std::sqrt(gx * gx + gy * gy);
  if (gmag > 1.0f) gmag = 1.0f;

  // INK SQUEEZE: the rim of the stroke, weighted onto the ink side.
  const float ring = kRingAt100 * clampScale(p.ringScale) * s * gmag * t;

  // DEBOSS SHADOW: the paper side of edges whose ink lies toward the
  // bottom-right -- i.e. the top-left walls of the depression, the ones a
  // top-left light cannot reach. grad points from paper toward ink, so the
  // shadowed walls are where grad . (1,1)/sqrt(2) is positive.
  float lightDot = (gx + gy) * 0.70710678f;
  if (lightDot < 0.0f) lightDot = 0.0f;
  if (lightDot > 1.0f) lightDot = 1.0f;
  const float deboss =
      kDebossAt100 * clampScale(p.debossScale) * s * lightDot * (1.0f - t);

  const float nx = (static_cast<float>(x) + 0.5f) / static_cast<float>(w);
  const float ny = (static_cast<float>(y) + 0.5f) / static_cast<float>(h);

  // PLATE PRESSURE: only the heavy half (light pressure would brighten).
  const float v = phosphorgrain::valueNoise(nx * kPressCells, ny * kPressCells,
                                            p.seed ^ 0x504C5445u);
  float heavy = v * 2.0f - 1.0f;
  if (heavy < 0.0f) heavy = 0.0f;
  // The ratio runs through pressAmpScale -- the widened dial (see above).
  // clampScale first, then the widening, so the drawer's 0..2 stays the
  // stored range and the widening has one definition.
  const float press = kPressAt100 * pressAmpScale(clampScale(p.pressScale)) *
                      s * heavy * t;

  // IN-STROKE IRREGULARITY (ink) and PAPER TOOTH (paper), both uniform noise
  // in [0, amplitude]. Tooth rides sqrt of the dial and is clamped to the
  // paper's budget: mean darkening of a uniform [0,a] is a/2, so a <= 2*budget
  // keeps the flat page at or above the floor by construction.
  const float u = phosphorgrain::unitFromHash(phosphorgrain::hash3(
      static_cast<uint32_t>(x), static_cast<uint32_t>(y),
      p.seed ^ 0x544F4F54u));
  const float irregular = kIrregularAt100 * s * u * t;
  const float toothAmp = clampedToothAmp(p);
  const float tooth = p.includeTooth ? toothAmp * u * (1.0f - t) : 0.0f;

  float m = 1.0f - (ring + deboss + press + irregular + tooth);
  if (m < kMinMultiplier) m = kMinMultiplier;
  if (m > 1.0f) m = 1.0f;
  return static_cast<uint8_t>(m * 255.0f + 0.5f);
}
}  // namespace legacy

namespace {

uint32_t rng = 0x12345678u;
uint32_t next() {
  rng ^= rng << 13;
  rng ^= rng >> 17;
  rng ^= rng << 5;
  return rng;
}
float unit() { return static_cast<float>(next() & 0xFFFFFF) / 16777215.0f; }

// A synthetic antialiased page: a disc, a horizontal bar, a vertical bar and a
// diagonal stroke, 4x4 supersampled so the edges carry every inkness level a
// real AA glyph edge does. Edges in all directions, so a light from any side
// finds walls to shade.
struct SynthPage {
  static constexpr int W = 96, H = 80;
  std::vector<float> t;
  static bool inked(float x, float y) {
    const float dx = x - 28.0f, dy = y - 26.0f;
    if (dx * dx + dy * dy < 14.0f * 14.0f && dx * dx + dy * dy > 7.0f * 7.0f)
      return true;                                          // an 'o'
    if (x > 50 && x < 88 && y > 12 && y < 18) return true;  // a crossbar
    if (x > 60 && x < 66 && y > 12 && y < 70) return true;  // a stem
    const float d = (x - y * 0.6f) - 14.0f;                 // a diagonal
    if (y > 46 && y < 76 && d > 0 && d < 5) return true;
    return false;
  }
  SynthPage() : t(static_cast<size_t>(W) * H) {
    for (int y = 0; y < H; ++y)
      for (int x = 0; x < W; ++x) {
        int n = 0;
        for (int sy = 0; sy < 4; ++sy)
          for (int sx = 0; sx < 4; ++sx)
            n += inked(x + (sx + 0.5f) / 4.0f, y + (sy + 0.5f) / 4.0f);
        // Quantized through a byte, the way SurfaceSheet's inkness plane is.
        const uint8_t b = static_cast<uint8_t>(n / 16.0f * 255.0f + 0.5f);
        t[static_cast<size_t>(y) * W + x] = b / 255.0f;
      }
  }
  void window(int x, int y, float win[3][3]) const {
    for (int dy = -1; dy <= 1; ++dy)
      for (int dx = -1; dx <= 1; ++dx) {
        int sx = x + dx, sy = y + dy;
        if (sx < 0) sx = 0;
        if (sy < 0) sy = 0;
        if (sx >= W) sx = W - 1;
        if (sy >= H) sy = H - 1;
        win[dy + 1][dx + 1] = t[static_cast<size_t>(sy) * W + sx];
      }
  }
};

letterpress::Params heavyParams(uint32_t seed) {
  letterpress::Params p;
  p.strengthPercent = letterpress::kOfferedStrengthMax;
  p.seed = seed;
  p.includeTooth = false;  // what SurfaceSheet's panel field passes
  p.ringScale = letterpress::kPartScaleMax;
  p.debossScale = letterpress::kPartScaleMax;
  p.pressScale = letterpress::kPartScaleMax;
  return p;
}

}  // namespace

int main() {
  using namespace rakinglight;

  // ------------------------------------------------ 1. THE SPLIT IS EXACT --
  // The letterpress this feature leaves OFF is the one that ships, so the
  // termsAt refactor must not move one code value. A million random windows
  // over random params, plus every corner of the part/strength ranges.
  {
    long mismatches = 0, n = 0;
    for (int trial = 0; trial < 1000000; ++trial) {
      letterpress::Params p;
      const int pick = static_cast<int>(next() % 8);
      p.strengthPercent = pick == 0 ? 0 : static_cast<int>(next() % 420);
      p.seed = next();
      p.paperDarkenBudget = unit();
      p.includeTooth = (next() & 1) != 0;
      p.toothScale = unit() * 3.0f;
      p.ringScale = unit() * 2.2f;
      p.debossScale = unit() * 2.2f;
      p.pressScale = unit() * 2.2f;
      float win[3][3];
      // Half the windows are hard 0/1 (1-bit glyph interiors), half AA.
      const bool hard = (next() & 1) != 0;
      for (auto &row : win)
        for (float &v : row) v = hard ? static_cast<float>(next() & 1) : unit();
      const int w = 1 + static_cast<int>(next() % 1600);
      const int h = 1 + static_cast<int>(next() % 1100);
      const int x = static_cast<int>(next() % w), y = static_cast<int>(next() % h);
      ++n;
      if (letterpress::multiplierAt(p, win, x, y, w, h) !=
          legacy::legacyMultiplierAt(p, win, x, y, w, h))
        ++mismatches;
    }
    std::printf("raking_light_test: split vs legacy, %ld windows, %ld differ\n",
                n, mismatches);
    check(mismatches == 0,
          "letterpress::multiplierAt after the termsAt split is byte-identical "
          "to the pre-split body over a million random windows");
  }

  // --------------------------------------- 2. WHERE TODAY'S LIGHT IS -------
  // referenceScreenAzimuthDeg must agree with SurfaceSheet.cpp's
  // outputToPanel: a screen direction (sx, sy) (y down) lands in the
  // framebuffer as below, and today's light-from is framebuffer (-1, -1).
  {
    struct Map {
      int orient;
      int a, b, c, d;  // fb = (a*sx + b*sy, c*sx + d*sy)
    } maps[] = {
        {0, 0, 1, -1, 0},   // Portrait: fx = v, fy = 1 - u
        {1, -1, 0, 0, -1},  // LandscapeClockwise: fx = 1 - u, fy = 1 - v
        {2, 0, -1, 1, 0},   // PortraitInverted: fx = 1 - v, fy = u
        {3, 1, 0, 0, 1},    // LandscapeCCW: identity
    };
    for (const Map &m : maps) {
      const float az = referenceScreenAzimuthDeg(m.orient) * kDegToRad;
      const float sx = std::sin(az), sy = -std::cos(az);  // light-from, y down
      const float fx = m.a * sx + m.b * sy, fy = m.c * sx + m.d * sy;
      check(std::fabs(fx + 0.70710678f) < 1e-4f &&
                std::fabs(fy + 0.70710678f) < 1e-4f,
            "reference screen azimuth maps to framebuffer top-left for "
            "orientation " + std::to_string(m.orient));
    }
    check(referenceScreenAzimuthDeg(0) == 45.0f,
          "in the reader's default Portrait, today's light comes from the "
          "screen's top-RIGHT");
  }

  // ------------------------------------- 3. GRAVITY TO LIGHT, PHYSICALLY ---
  {
    const float ref = referenceScreenAzimuthDeg(0);
    // A reading pose: phone tipped back ~40 degrees from flat.
    const Vec3 neutral{0.0f, -0.64f, -0.77f};
    const Continuous same = lightFromGravity(neutral, neutral, ref);
    check(same.deltaDeg == 0.0f && same.rake == 1.0f,
          "at the neutral pose the light is EXACTLY today's");
    check(quantize(same, nullptr) == Quantized{},
          "and quantizes to index 0, full rake");

    // Roll the right edge DOWN: gravity's x goes positive. The lamp is fixed
    // in the room, so the raised LEFT edge now faces it more: the light's
    // azimuth swings counter-clockwise (negative delta) from top-right.
    auto rolled = [&](float deg) {
      const float a = deg * kDegToRad;
      // rotate the neutral about the device's y axis
      return Vec3{neutral.x * std::cos(a) - neutral.z * std::sin(a), neutral.y,
                  neutral.x * std::sin(a) + neutral.z * std::cos(a)};
    };
    const Continuous right = lightFromGravity(neutral, rolled(-12.0f), ref);
    const Continuous left = lightFromGravity(neutral, rolled(12.0f), ref);
    std::printf("raking_light_test: roll +-12 deg -> delta %.1f / %.1f deg, "
                "rake %.2f / %.2f\n",
                static_cast<double>(right.deltaDeg),
                static_cast<double>(left.deltaDeg),
                static_cast<double>(right.rake), static_cast<double>(left.rake));
    check((right.deltaDeg < 0.0f) != (left.deltaDeg < 0.0f),
          "rolling the two ways swings the light opposite ways");
    check(std::fabs(right.deltaDeg) > 10.0f && std::fabs(left.deltaDeg) > 10.0f,
          "a 12-degree roll moves the light by more than a quantization step");
    // Which way is right: gravity x positive = right edge down.
    const Vec3 rightDown{0.2f, -0.62f, -0.76f};
    const Continuous rd = lightFromGravity(neutral, rightDown, ref);
    check(rd.deltaDeg < 0.0f,
          "right edge down: the lamp arrives more from the raised LEFT side "
          "(counter-clockwise from top-right)");
    check(rd.rake < 1.0f,
          "right edge down turns the page toward a top-right lamp: it climbs "
          "overhead and the relief fades");
    const Vec3 leftDown{-0.2f, -0.62f, -0.76f};
    const Continuous ld = lightFromGravity(neutral, leftDown, ref);
    check(ld.deltaDeg > 0.0f && ld.rake == 1.0f,
          "left edge down: clockwise, and raked -- capped at today's depth");

    // Every pose, every orientation: rake in [0,1], delta in (-180,180].
    bool bounded = true;
    for (int i = 0; i < 20000; ++i) {
      const Vec3 g{unit() * 2 - 1, unit() * 2 - 1, unit() * 2 - 1};
      for (int o = 0; o < 4; ++o) {
        const Continuous c =
            lightFromGravity(neutral, g, referenceScreenAzimuthDeg(o));
        if (!(c.rake >= 0.0f && c.rake <= 1.0f) ||
            !(c.deltaDeg > -180.0f && c.deltaDeg <= 180.0f))
          bounded = false;
      }
    }
    check(bounded, "every pose yields a rake in [0,1] and a wrapped azimuth");
    const Continuous none = lightFromGravity(Vec3{}, neutral, ref);
    check(none.deltaDeg == 0.0f && none.rake == 1.0f,
          "no reading yet (zero gravity) is today's light, not a guess");
  }

  // ------------------------------------------------- 4. QUANTIZATION -------
  {
    Quantized z;
    const Quantized a = quantize({kStepDeg * 0.6f, 1.0f}, &z);
    check(a.dir == 0, "0.6 of a step past today's stays put (hysteresis)");
    const Quantized b = quantize({kStepDeg * 0.7f, 1.0f}, &z);
    check(b.dir == 1, "0.7 of a step moves one direction");
    const Quantized c = quantize({kStepDeg * 0.55f, 1.0f}, &b);
    check(c.dir == 1, "and coming back 0.15 of a step does not flip it back");
    const Quantized wrapA = quantize({179.0f, 1.0f}, nullptr);
    const Quantized wrapB = quantize({-179.0f, 1.0f}, nullptr);
    check(wrapA.dir == 8 && wrapB.dir == 8, "+-179 degrees both quantize to 8");
    const Quantized held = quantize({-170.0f, 1.0f}, &wrapA);
    check(held.dir == 8, "hysteresis is circular across the wrap");
    const Quantized r = quantize({0.0f, 0.62f}, &z);
    check(r.rake == 5, "rake 0.62 -> 5/8 (from 8, far past the band)");
    const Quantized r2 = quantize({0.0f, 0.57f}, &r);
    check(r2.rake == 5, "rake 0.57 holds at 5 (inside the band)");
    for (int d = 0; d < kDirections; ++d)
      for (int k = 0; k <= kRakeLevels; ++k) {
        const Quantized q{d, k};
        if (unpack(pack(q)) != q || pack(q) <= 0) {
          check(false, "pack/unpack round trip and never zero");
          d = kDirections;
          break;
        }
      }
    const Shadow s0 = shadowFor(Quantized{});
    check(std::fabs(s0.dx - 0.70710678f) < 1e-6f &&
              std::fabs(s0.dy - 0.70710678f) < 1e-6f && s0.rake == 1.0f,
          "index 0 is today's shadow direction (1,1)/sqrt2 at full rake");
    const Shadow s4 = shadowFor(Quantized{4, 8});
    check(s4.dx < -0.7f && s4.dy > 0.7f,
          "four steps clockwise turns the shadow a quarter turn clockwise");
  }

  // ----------------------------- 5. PER-PIXEL: FLAT UNTOUCHED, NO DEEPER ---
  {
    const SynthPage page;
    const int W = SynthPage::W, H = SynthPage::H;
    bool flatExact = true, neverDeeper = true, neverAboveOne = true;
    long edgePx = 0;
    double worstMeanPaper = 0.0, fixedMeanPaper = 0.0;
    for (int seedIx = 0; seedIx < 3; ++seedIx) {
      const letterpress::Params p = heavyParams(0x50524553u + seedIx * 977u);
      for (int d = 0; d < kDirections; ++d)
        for (int k = 0; k <= kRakeLevels; ++k) {
          const Shadow S = shadowFor(Quantized{d, k});
          double sumPaper = 0.0;
          long nPaper = 0;
          for (int y = 0; y < H; ++y)
            for (int x = 0; x < W; ++x) {
              float win[3][3];
              page.window(x, y, win);
              const letterpress::Terms T =
                  letterpress::termsAt(p, win, x, y, W, H);
              const Edge e = edgeOf(T);
              const uint8_t m = multiplierFor(e, S);
              const uint8_t fixed =
                  letterpress::multiplierAt(p, win, x, y, W, H);
              if (T.gx == 0.0f && T.gy == 0.0f) {
                if (m != fixed) flatExact = false;
              } else if (d == 0 && k == kRakeLevels && seedIx == 0) {
                ++edgePx;
              }
              // The fixed light's own ceiling at this pixel: full shade and
              // the full rim, which no light can exceed.
              float worst = 1.0f - (e.ring + e.depth + e.rest);
              if (worst < letterpress::kMinMultiplier)
                worst = letterpress::kMinMultiplier;
              const uint8_t worstB =
                  static_cast<uint8_t>(worst * 255.0f + 0.5f);
              if (m < worstB) neverDeeper = false;
              if (fixed < worstB) neverDeeper = false;  // sanity on the bound
              if (m > 255) neverAboveOne = false;
              if (T.t == 0.0f) {
                sumPaper += (255.0 - m) / 255.0;
                ++nPaper;
                if (d == 0 && k == kRakeLevels)
                  fixedMeanPaper += (255.0 - fixed) / 255.0;
              }
            }
          const double mean = nPaper ? sumPaper / nPaper : 0.0;
          if (mean > worstMeanPaper) worstMeanPaper = mean;
        }
    }
    // fixedMeanPaper was summed over 3 seeds x all paper pixels; normalize.
    long paperPx = 0;
    for (float v : page.t) paperPx += (v == 0.0f);
    fixedMeanPaper /= (3.0 * paperPx);
    std::printf("raking_light_test: synthetic page %d edge px of %d; paper "
                "mean darkening, fixed light %.5f, worst raking light %.5f\n",
                static_cast<int>(edgePx), W * H, fixedMeanPaper, worstMeanPaper);
    check(edgePx > 0, "the synthetic page has edges to light");
    check(flatExact,
          "every FLAT pixel (zero gradient) is byte-identical to the fixed "
          "light under all 16 x 9 lights -- the pixels every contrast-floor "
          "proof reasons about do not move");
    check(neverDeeper,
          "no pixel under any light is darker than the fixed light's own "
          "worst case at that pixel (full shade + full rim)");
    check(neverAboveOne, "the multiplier never exceeds 1: darken-only");
    // The page-mean paper darkening is the deboss spent on the paper side of
    // edges. Tilting moves it round the letters; on a page with walls in all
    // directions it must stay within 2x of today's (it is ~1x on a page whose
    // edges are isotropic).
    check(worstMeanPaper <= 2.0 * fixedMeanPaper + 1e-6,
          "no light spends more than twice today's paper-side shadow, page-mean");
    // The 7:1 floor needs nothing further here: letterpress_test proves it on
    // FLAT paper against FLAT ink, and flatExact above shows those pixels are
    // the fixed light's to the byte under every raking light.
  }

  // ------------------------------ 6. THE EDGE FIELD RE-LIGHTS EXACTLY ------
  {
    const SynthPage page;
    const int W = SynthPage::W, H = SynthPage::H;
    const letterpress::Params p = heavyParams(0xC0FFEEu);
    auto termsAt = [&](int x, int y) {
      float win[3][3];
      page.window(x, y, win);
      return letterpress::termsAt(p, win, x, y, W, H);
    };
    EdgeField f;
    f.build(W, H, termsAt);
    bool exact = true;
    // Relight through a sequence of lights, including repeats and jumps, and
    // compare each to a from-scratch per-pixel lighting.
    const Quantized seq[] = {{0, 8}, {5, 8}, {5, 3}, {15, 0}, {8, 8}, {0, 8}};
    for (const Quantized &q : seq) {
      const Shadow S = shadowFor(q);
      f.relight(S);
      for (int y = 0; y < H && exact; ++y)
        for (int x = 0; x < W; ++x) {
          const uint32_t m = multiplierFor(edgeOf(termsAt(x, y)), S);
          const uint32_t want = 0xFF000000u | (m << 16) | (m << 8) | m;
          if (f.field[static_cast<size_t>(y) * W + x] != want) {
            exact = false;
            break;
          }
        }
    }
    check(exact, "EdgeField::relight equals a full per-pixel lighting after "
                 "every light in a sequence");
    check(!f.edges.empty() && f.edges.size() < static_cast<size_t>(W) * H / 2,
          "only a minority of pixels are edges, which is the whole saving");
    // Strength 0: every pixel white, no edges kept.
    letterpress::Params off = p;
    off.strengthPercent = 0;
    EdgeField g;
    g.build(W, H, [&](int x, int y) {
      float win[3][3];
      page.window(x, y, win);
      return letterpress::termsAt(off, win, x, y, W, H);
    });
    bool allWhite = g.edges.empty();
    for (uint32_t v : g.field) allWhite = allWhite && v == 0xFFFFFFFFu;
    check(allWhite, "strength 0 builds an all-white field with no edges");
  }

  // ----------------------------------------------------- 7. SMOOTHING ------
  {
    const Vec3 a{0, 0, -1}, b{0, -1, 0};
    const Vec3 first = smooth(a, b, 0.05f, false);
    check(first.y == -1.0f, "the first sample passes through");
    Vec3 s = a;
    for (int i = 0; i < 6; ++i) s = smooth(s, b, 0.05f, true);  // 0.3 s
    check(s.y < -0.55f && s.y > -0.75f,
          "after one time constant the low-pass is ~63% of the way");
    const Vec3 still = smooth(a, b, 0.0f, true);
    check(still.y == -1.0f, "a non-positive dt takes the sample");
  }

  if (failures == 0) std::printf("raking_light_test: PASS\n");
  return failures == 0 ? 0 : 1;
}
