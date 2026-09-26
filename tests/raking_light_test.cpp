// Host test for src/RakingLight.h, and for the split of letterpress::
// multiplierAt into termsAt + a combiner that it needed.
//
// Every failure mode here is a wrong picture or a thrashing field:
//   - the split changes the SHIPPED letterpress by one code value somewhere
//     (the feature is off by default, so this is the one that ships);
//   - a tilt touches flat paper in the panel field, which every contrast-floor
//     proof assumes it cannot, or deepens a shadow past strength * rake;
//   - the light turns the wrong way for the tilt, or does not come back to
//     exactly today's when the phone does;
//   - the edge-only recompose disagrees with a full per-pixel light;
//   - quantization without hysteresis flips on a tremor;
//   - the lamp field lifts a pixel, or darkens one past its budget, or puts the
//     bright side of the sheet away from the lamp, or shades the wrong slope;
//   - the 7:1 floor breaks at some corner of the four dials and the light.
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

// sRGB byte -> relative luminance, the WCAG way (what srgbLumOf does).
float lin(int c) {
  const float v = static_cast<float>(c) / 255.0f;
  return v <= 0.04045f ? v / 12.92f : std::pow((v + 0.055f) / 1.055f, 2.4f);
}
float lumOf(int r, int g, int b) {
  return 0.2126f * lin(r) + 0.7152f * lin(g) + 0.0722f * lin(b);
}

uint8_t gray(uint32_t argb) { return static_cast<uint8_t>(argb & 0xFF); }

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

  // --------------------------------------------------- 3. THE FOUR DIALS ---
  {
    const Dials def;
    check(strengthGain(0) == 1.0f, "strength 0 is today's deboss depth, exactly");
    check(std::fabs(strengthGain(100) - 3.0f) < 1e-6f, "strength 100 is 3x");
    check(std::fabs(strengthGain(200) - 5.0f) < 1e-6f, "strength 200 is 5x");
    check(strengthGain(-5) == 1.0f && strengthGain(900) == strengthGain(200),
          "strength clamps to 0..200");
    check(lampElevationDeg(100) == kRefElevationDeg,
          "lamp height 100 is the reference 35 degrees");
    check(rakeForElevation(lampElevationDeg(100)) == 1.0f,
          "...at which the rake is EXACTLY 1.0f (the fixed light's depth)");
    check(lampElevationDeg(0) < lampElevationDeg(200),
          "a lower slider is a lower lamp");
    check(rakeForElevation(lampElevationDeg(0)) == kRakeMax,
          "the lowest lamp reaches the rake cap");
    check(rakeForElevation(lampElevationDeg(200)) < 0.5f,
          "the highest lamp rakes under half as much");
    check(rakeForElevation(90.0f) == 0.0f && rakeForElevation(-3.0f) == kRakeMax,
          "overhead is rake 0; below the horizon is held at grazing");
    for (float r = 0.0f; r <= kRakeMax; r += 0.125f)
      check(std::fabs(rakeForElevation(elevationForRake(r)) - r) < 1e-3f,
            "elevationForRake inverts rakeForElevation at rake " +
                std::to_string(r));
    check(tiltGain(0) == 0.0f && std::fabs(tiltGain(100) - 2.0f) < 1e-6f,
          "tilt range 0 pins the lamp; 100 is the spike's gain of 2");
    check(pageFactor(0) == 0.0f && pageFactor(100) == kPageAt100,
          "page 0 is no sheet response; 100 is kPageAt100");
    const Continuous nl = neutralLight(def);
    check(nl.deltaDeg == 0.0f && nl.rake == 1.0f,
          "the default neutral light is today's, exactly");
    Dials low = def;
    low.lampHeightPct = 0;
    check(neutralLight(low).rake == kRakeMax,
          "the neutral light with a low lamp is a raking one");
  }

  // ------------------------------------- 4. GRAVITY TO LIGHT, PHYSICALLY ---
  {
    const float ref = referenceScreenAzimuthDeg(0);
    const Dials def;
    // A reading pose: phone tipped back ~40 degrees from flat.
    const Vec3 neutral{0.0f, -0.64f, -0.77f};
    const Continuous same = lightFromGravity(neutral, neutral, ref, def);
    check(same.deltaDeg == 0.0f && same.rake == 1.0f,
          "at the neutral pose the light is EXACTLY today's");
    check(quantize(same, nullptr) == Quantized{},
          "and quantizes to index 0, rake 8/8");

    // Roll the right edge DOWN: gravity's x goes positive. The lamp is fixed
    // in the room, so the raised LEFT edge now faces it more: the light's
    // azimuth swings counter-clockwise (negative delta) from top-right.
    auto rolled = [&](float deg) {
      const float a = deg * kDegToRad;
      // rotate the neutral about the device's y axis
      return Vec3{neutral.x * std::cos(a) - neutral.z * std::sin(a), neutral.y,
                  neutral.x * std::sin(a) + neutral.z * std::cos(a)};
    };
    const Continuous right = lightFromGravity(neutral, rolled(-12.0f), ref, def);
    const Continuous left = lightFromGravity(neutral, rolled(12.0f), ref, def);
    std::printf("raking_light_test: roll +-12 deg -> delta %.1f / %.1f deg, "
                "rake %.2f / %.2f\n",
                static_cast<double>(right.deltaDeg),
                static_cast<double>(left.deltaDeg),
                static_cast<double>(right.rake), static_cast<double>(left.rake));
    check((right.deltaDeg < 0.0f) != (left.deltaDeg < 0.0f),
          "rolling the two ways swings the light opposite ways");
    check(std::fabs(right.deltaDeg) > kStepDeg && std::fabs(left.deltaDeg) > kStepDeg,
          "a 12-degree roll moves the light by more than a quantization step");
    // Which way is right: gravity x positive = right edge down.
    const Vec3 rightDown{0.2f, -0.62f, -0.76f};
    const Continuous rd = lightFromGravity(neutral, rightDown, ref, def);
    check(rd.deltaDeg < 0.0f,
          "right edge down: the lamp arrives more from the raised LEFT side "
          "(counter-clockwise from top-right)");
    check(rd.rake < 1.0f,
          "right edge down turns the page toward a top-right lamp: it climbs "
          "overhead and the relief fades");
    const Vec3 leftDown{-0.2f, -0.62f, -0.76f};
    const Continuous ld = lightFromGravity(neutral, leftDown, ref, def);
    check(ld.deltaDeg > 0.0f && ld.rake > 1.0f,
          "left edge down: clockwise, and the lamp drops toward grazing -- "
          "the rake now GROWS past today's instead of being capped there");

    // The dials reach the gravity path.
    Dials pinned = def;
    pinned.tiltRangePct = 0;
    const Continuous p = lightFromGravity(neutral, leftDown, ref, pinned);
    check(p.deltaDeg == 0.0f && p.rake == 1.0f,
          "tilt range 0: the lamp does not move whatever the hand does");
    Dials wide = def;
    wide.tiltRangePct = 200;
    const Continuous wd = lightFromGravity(neutral, leftDown, ref, wide);
    check(std::fabs(wd.deltaDeg) > std::fabs(ld.deltaDeg),
          "tilt range 200 swings the light further for the same tilt");
    Dials high = def;
    high.lampHeightPct = 200;
    check(lightFromGravity(neutral, leftDown, ref, high).rake < ld.rake,
          "a higher lamp rakes less at the same tilt");

    // Every pose, every orientation: rake in [0,kRakeMax], delta in (-180,180].
    bool bounded = true;
    for (int i = 0; i < 20000; ++i) {
      const Vec3 g{unit() * 2 - 1, unit() * 2 - 1, unit() * 2 - 1};
      Dials d;
      d.lampHeightPct = static_cast<int>(next() % 201);
      d.tiltRangePct = static_cast<int>(next() % 201);
      for (int o = 0; o < 4; ++o) {
        const Continuous c =
            lightFromGravity(neutral, g, referenceScreenAzimuthDeg(o), d);
        if (!(c.rake >= 0.0f && c.rake <= kRakeMax) ||
            !(c.deltaDeg > -180.0f && c.deltaDeg <= 180.0f))
          bounded = false;
      }
    }
    check(bounded, "every pose and dial yields a bounded rake and a wrapped azimuth");
    const Continuous none = lightFromGravity(Vec3{}, neutral, ref, def);
    check(none.deltaDeg == 0.0f && none.rake == 1.0f,
          "no reading yet (zero gravity) is today's light, not a guess");
  }

  // ------------------------------------------------- 5. QUANTIZATION -------
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
    check(wrapA.dir == kDirections / 2 && wrapB.dir == kDirections / 2,
          "+-179 degrees both quantize to the opposite direction");
    const Quantized held = quantize({-175.0f, 1.0f}, &wrapA);
    check(held.dir == kDirections / 2, "hysteresis is circular across the wrap");
    const Quantized r = quantize({0.0f, 0.62f}, &z);
    check(r.rake == 5, "rake 0.62 -> 5/8 (from 8, far past the band)");
    const Quantized r2 = quantize({0.0f, 0.57f}, &r);
    check(r2.rake == 5, "rake 0.57 holds at 5 (inside the band)");
    check(quantize({0.0f, 9.0f}, nullptr).rake == kRakeLevelMax,
          "a rake past the cap quantizes to the top level");
    bool roundTrip = true;
    for (int d = 0; d < kDirections; ++d)
      for (int k = 0; k <= kRakeLevelMax; ++k) {
        const Quantized q{d, k};
        if (unpack(pack(q)) != q || pack(q) <= 0) roundTrip = false;
      }
    check(roundTrip, "pack/unpack round trip over every level, never zero");
    const Shadow s0 = shadowFor(Quantized{});
    check(std::fabs(s0.dx - 0.70710678f) < 1e-6f &&
              std::fabs(s0.dy - 0.70710678f) < 1e-6f && s0.rake == 1.0f,
          "index 0 is today's shadow direction (1,1)/sqrt2 at rake 1");
    const Shadow s8 = shadowFor(Quantized{kDirections / 4, kRakeLevelsPerUnit});
    check(s8.dx < -0.7f && s8.dy > 0.7f,
          "a quarter of the directions turns the shadow a quarter turn clockwise");
    check(shadowFor(Quantized{0, kRakeLevelMax}).rake == kRakeMax,
          "the top rake level is kRakeMax");
    const Light L0 = lightFor(Quantized{}, 0);
    check(L0.azDeg == 45.0f && std::fabs(L0.elevDeg - kRefElevationDeg) < 1e-3f,
          "the screen light for index 0 in Portrait is 45 degrees at 35 up");
  }

  // ----------------------------- 6. PER-PIXEL: FLAT UNTOUCHED, BOUNDED -----
  {
    const SynthPage page;
    const int W = SynthPage::W, H = SynthPage::H;
    bool flatExact = true, neverDeeperAtOne = true, neverAboveOne = true,
         boundedByGain = true;
    long edgePx = 0;
    const float gains[] = {1.0f, strengthGain(100), strengthGain(200)};
    for (int seedIx = 0; seedIx < 3; ++seedIx) {
      const letterpress::Params p = heavyParams(0x50524553u + seedIx * 977u);
      for (int d = 0; d < kDirections; d += 2)
        for (int k = 0; k <= kRakeLevelMax; k += 2)
          for (float gain : gains) {
            const Shadow S = shadowFor(Quantized{d, k});
            for (int y = 0; y < H; ++y)
              for (int x = 0; x < W; ++x) {
                float win[3][3];
                page.window(x, y, win);
                const letterpress::Terms T =
                    letterpress::termsAt(p, win, x, y, W, H);
                const Edge e = edgeOf(T);
                const uint8_t m = multiplierFor(e, S, gain);
                const uint8_t fixed =
                    letterpress::multiplierAt(p, win, x, y, W, H);
                if (T.gx == 0.0f && T.gy == 0.0f) {
                  if (m != fixed) flatExact = false;
                } else if (d == 0 && k == kRakeLevelsPerUnit && seedIx == 0 &&
                           gain == 1.0f) {
                  ++edgePx;
                }
                // The fixed light's own ceiling at this pixel: full shade and
                // the full rim, which no light at gain 1, rake <= 1 exceeds.
                float worst = 1.0f - (e.ring + e.depth + e.rest);
                if (worst < letterpress::kMinMultiplier)
                  worst = letterpress::kMinMultiplier;
                const uint8_t worstB =
                    static_cast<uint8_t>(worst * 255.0f + 0.5f);
                if (gain == 1.0f && S.rake <= 1.0f && m < worstB)
                  neverDeeperAtOne = false;
                if (fixed < worstB) neverDeeperAtOne = false;  // sanity
                // ...and above that the deboss is bounded by gain * rake.
                float bound = 1.0f - (e.ring + e.depth * gain * S.rake + e.rest);
                if (bound < letterpress::kMinMultiplier)
                  bound = letterpress::kMinMultiplier;
                if (m + 1 < static_cast<uint8_t>(bound * 255.0f + 0.5f))
                  boundedByGain = false;
                if (m > 255) neverAboveOne = false;
              }
          }
    }
    std::printf("raking_light_test: synthetic page %d edge px of %d\n",
                static_cast<int>(edgePx), W * H);
    check(edgePx > 0, "the synthetic page has edges to light");
    check(flatExact,
          "every FLAT pixel (zero gradient) is byte-identical to the fixed "
          "light under every light and every strength -- the pixels every "
          "contrast-floor proof reasons about do not move");
    check(neverDeeperAtOne,
          "at strength 0 and rake <= 1 no pixel is darker than the fixed "
          "light's own worst case (the spike's guarantee still holds there)");
    check(boundedByGain,
          "at any strength and rake the deboss is at most depth * gain * rake");
    check(neverAboveOne, "the multiplier never exceeds 1: darken-only");
  }

  // ------------------------------ 7. THE EDGE FIELD RE-LIGHTS EXACTLY ------
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
    // Relight through a sequence of lights and gains, including repeats and
    // jumps, and compare each to a from-scratch per-pixel lighting.
    struct Step { Quantized q; float gain; } seq[] = {
        {{0, 8}, 1.0f}, {{5, 8}, 3.0f}, {{5, 3}, 3.0f}, {{31, 0}, 5.0f},
        {{16, 24}, 5.0f}, {{0, 8}, 1.0f}};
    for (const Step &st : seq) {
      const Shadow S = shadowFor(st.q);
      f.relight(S, st.gain);
      for (int y = 0; y < H && exact; ++y)
        for (int x = 0; x < W; ++x) {
          const uint32_t m = multiplierFor(edgeOf(termsAt(x, y)), S, st.gain);
          const uint32_t want = 0xFF000000u | (m << 16) | (m << 8) | m;
          if (f.field[static_cast<size_t>(y) * W + x] != want) {
            exact = false;
            break;
          }
        }
    }
    check(exact, "EdgeField::relight equals a full per-pixel lighting after "
                 "every light and gain in a sequence");
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

  // ----------------------------------------------------- 8. SMOOTHING ------
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

  // ---------------------------------------------- 9. THE SHEET'S LAMP FIELD
  {
    // A portrait glass at the desktop 2x's presented size, lattice of 2.
    const int W = 528, H = 792;
    LampField lf;
    lf.build(W, H, 2, 0xC0FFEEu, [](float, float) { return 0.0f; });
    check(lf.lw == 264 && lf.lh == 396, "the lattice is the output over the cell");
    check(lf.falloffRef > 0.3f && lf.falloffRef < 0.9f,
          "the reference lamp's corner-to-corner falloff is a real fraction "
          "(measured: ~0.63 at kLampDistance 4, elevation 35)");
    std::printf("raking_light_test: lamp field %dx%d lattice, falloffRef %.3f\n",
                lf.lw, lf.lh, static_cast<double>(lf.falloffRef));
    // Gradient statistics: RMS one by construction, so |g| ~ kGradScale.
    double sq = 0.0;
    for (size_t k = 0; k < lf.gx.size(); ++k)
      sq += static_cast<double>(lf.gx[k]) * lf.gx[k] +
            static_cast<double>(lf.gy[k]) * lf.gy[k];
    const double rms = std::sqrt(sq / lf.gx.size());
    check(rms > kGradScale * 0.8 && rms < kGradScale * 1.2,
          "the stored gradient is normalized to about one RMS unit");

    const Dials def;
    const float budget = 0.12f;
    // (a) Darken-only, and never past the budget, at every light and dial.
    bool darkenOnly = true, withinBudget = true;
    for (int d = 0; d < kDirections; d += 4)
      for (int k = 0; k <= kRakeLevelMax; k += 4)
        for (int pg : {0, 100, 200}) {
          Dials dl = def;
          dl.pagePct = pg;
          lf.relight(lightFor(Quantized{d, k}, 0), dl, budget);
          const int floor = static_cast<int>((1.0f - budget) * 255.0f + 0.5f);
          for (uint32_t v : lf.field) {
            const int g = gray(v);
            if (g > 255) darkenOnly = false;
            if (g < floor) withinBudget = false;
            if (pg == 0 && g != 255) darkenOnly = false;  // page 0: nothing
          }
        }
    check(darkenOnly, "the lamp field never lifts a pixel, and page 0 is white");
    check(withinBudget, "no lamp pixel darkens past its budget, at any light");
    lf.relight(lightFor(Quantized{}, 0), def, 0.0f);
    bool white = true;
    for (uint32_t v : lf.field) white = white && v == 0xFFFFFFFFu;
    check(white, "budget 0 (a palette at the floor) leaves the field white");

    // (b) The bright side is the lamp's side. Light from the TOP (az 0):
    // the top band is lighter than the bottom band. From the LEFT (270): the
    // left band lighter than the right.
    auto bandMean = [&](int x0, int x1, int y0, int y1) {
      double s = 0.0;
      long n = 0;
      for (int j = y0; j < y1; ++j)
        for (int i = x0; i < x1; ++i) {
          s += gray(lf.field[static_cast<size_t>(j) * lf.lw + i]);
          ++n;
        }
      return s / n;
    };
    Light top;
    top.azDeg = 0.0f;
    top.elevDeg = kRefElevationDeg;
    lf.relight(top, def, budget);
    const double topBand = bandMean(0, lf.lw, 0, lf.lh / 8);
    const double botBand = bandMean(0, lf.lw, lf.lh * 7 / 8, lf.lh);
    check(topBand > botBand + 8.0,
          "light from the top: the top of the sheet is plainly lighter than "
          "the bottom (" + std::to_string(topBand) + " vs " +
              std::to_string(botBand) + ")");
    Light leftL;
    leftL.azDeg = 270.0f;
    leftL.elevDeg = kRefElevationDeg;
    lf.relight(leftL, def, budget);
    check(bandMean(0, lf.lw / 8, 0, lf.lh) > bandMean(lf.lw * 7 / 8, lf.lw, 0, lf.lh) + 8.0,
          "light from the left: the left of the sheet is lighter");
    // At the far corner under the default dials the falloff spends about
    // kPageAt100 of the budget -- the visibility the owner asked for.
    lf.relight(top, def, budget);
    const double farDark = 255.0 - botBand;
    check(farDark > budget * 255.0 * kPageAt100 * 0.6,
          "the far edge at default spends a good part of the budget (" +
              std::to_string(farDark) + " of " +
              std::to_string(budget * 255.0) + " levels)");
    // A higher lamp evens the light; a lower one does not make it MORE uneven
    // than the budget allows (it clips).
    Light high = top;
    high.elevDeg = 70.0f;
    lf.relight(high, def, budget);
    const double highSpread = bandMean(0, lf.lw, 0, lf.lh / 8) - bandMean(0, lf.lw, lf.lh * 7 / 8, lf.lh);
    check(highSpread < topBand - botBand,
          "a higher lamp lights the sheet more evenly");
    Light overhead = top;
    overhead.elevDeg = 90.0f;
    lf.relight(overhead, def, budget);
    check(std::fabs(bandMean(0, lf.lw, 0, lf.lh / 8) - bandMean(0, lf.lw, lf.lh * 7 / 8, lf.lh)) < 1.0,
          "straight overhead the top and bottom bands are the same");

    // (c) The relief shades the slope that faces AWAY from the lamp. Build a
    // field whose only height is a ramp rising toward +x, light it from the
    // right (az 90): the ramp faces away, so it darkens; light it from the
    // left: it faces the lamp, so it does not.
    LampField ramp;
    ramp.build(64, 64, 1, 1u, [](float x, float) { return x * 50.0f; });
    Dials noFall = def;
    Light fromRight;
    fromRight.azDeg = 90.0f;
    fromRight.elevDeg = kRefElevationDeg;
    Light fromLeft = fromRight;
    fromLeft.azDeg = 270.0f;
    // Compare the CENTER pixel, where the falloff of the two mirror lights
    // is identical, so only the relief separates them.
    const size_t center = static_cast<size_t>(ramp.lh / 2) * ramp.lw + ramp.lw / 2;
    ramp.relight(fromRight, noFall, budget);
    const int shaded = gray(ramp.field[center]);
    ramp.relight(fromLeft, noFall, budget);
    const int lit = gray(ramp.field[center]);
    check(shaded < lit,
          "a slope rising toward the lamp is shaded; the same slope lit from "
          "the other side is not (" + std::to_string(shaded) + " vs " +
              std::to_string(lit) + ")");
    // The relief is stronger under a lower lamp.
    Light lowRight = fromRight;
    lowRight.elevDeg = 15.0f;
    ramp.relight(lowRight, noFall, budget);
    check(gray(ramp.field[center]) <= shaded,
          "a lower lamp shades the same slope at least as hard");
    // Bit-exact repeat: the same light twice gives the same bytes.
    ramp.relight(fromRight, noFall, budget);
    const std::vector<uint32_t> once = ramp.field;
    ramp.relight(fromLeft, noFall, budget);
    ramp.relight(fromRight, noFall, budget);
    check(once == ramp.field, "relighting is a pure function of the light");
  }

  // ------------------------------------- 10. THE 7:1 FLOOR, AT THE EXTREMES
  // The sheet pass's own budget chain, reproduced: paperBudget -> the tooth's
  // mean -> the wires' and the show-through's DECLARED shares (taken at their
  // full share, the worst case) -> lampBudget of what is left -> the MARKS at
  // their full share of what the lamp leaves -> the field's per-pixel cap.
  // With every other consumer at its full share the chain is exactly tight,
  // so what this proves is that the lamp field's DARKEST pixel never exceeds
  // the share the sheet pass took out of the marks for it -- under every
  // light and dial, at three budgets. (Adversarial review 2026-09-26: without
  // the marks' share the sweep had 25% of slack and could not fail.) The
  // standard is the one every paper pass here is held to: the page-mean
  // paper darkening keeps flat paper at 7:1 against flat ink. Three palettes:
  // the frozen shipped page, the repo's historical light pair, and a pair one
  // hundredth above the floor.
  {
    struct Pal {
      const char *name;
      float ink, paper;
    } pals[] = {
        {"Sanguine on India (shipped)", lumOf(0x5C, 0x33, 0x2B), lumOf(0xF9, 0xF3, 0xE9)},
        {"2D2D2D on FBFBF9 (historical)", lumOf(0x2D, 0x2D, 0x2D), lumOf(0xFB, 0xFB, 0xF9)},
        {"a pair at 7.01:1", 0.05f, 7.01f * 0.10f - 0.05f},
    };
    LampField lf;
    lf.build(264, 396, 2, 0x50524553u, [](float, float) { return 0.0f; });
    float worstRatio = 1e9f, worstMargin = 1e9f;
    const char *worstWhere = "";
    for (const Pal &pal : pals) {
      // THE FIELD'S BYTE QUANTIZATION, per palette: a multiplier rounds to the
      // nearest 1/255, so the darkest pixel may overshoot its cap by half a
      // level of the paper's light. That is the only slack this sweep allows,
      // and it is computed rather than guessed: on the darkest ink here it is
      // 0.024 of a ratio point, on the shipped page 0.018.
      const float roundingRatio =
          pal.paper * (0.5f / 255.0f) / (pal.ink + 0.05f);
      for (int strength : {letterpress::kOfferedStrengthMax, 68, 1})
        for (float tooth : {1.0f, 3.36f}) {
          letterpress::Params p;
          p.strengthPercent = strength;
          p.toothScale = tooth;
          p.paperDarkenBudget = letterpress::paperBudget(pal.ink, pal.paper);
          const float toothMean = letterpress::clampedToothAmp(p) * 0.5f;
          const float left = letterpress::remainingPaperBudget(p);
          const float wires = 0.5f * left;             // the wires' full share
          const float show = 0.5f * (left - wires);    // show-through's
          const float afterShow = left - wires - show;
          const float lamp = lampBudget(afterShow);
          const float marks = afterShow - lamp;  // the marks' full share
          for (int d = 0; d < kDirections; d += 8)
            for (int k : {0, kRakeLevelsPerUnit, kRakeLevelMax})
              for (int pg : {0, 100, 200}) {
                Dials dl;
                dl.pagePct = pg;
                lf.relight(lightFor(Quantized{d, k}, 0), dl, lamp);
                int darkest = 255;
                for (uint32_t v : lf.field)
                  if (gray(v) < darkest) darkest = gray(v);
                const float lampDark = 1.0f - static_cast<float>(darkest) / 255.0f;
                const float paperMean =
                    pal.paper *
                    (1.0f - toothMean - wires - show - marks - lampDark);
                const float ratio = (paperMean + 0.05f) / (pal.ink + 0.05f);
                const float margin =
                    ratio - (letterpress::kContrastFloor - roundingRatio);
                if (margin < worstMargin) {
                  worstMargin = margin;
                  worstRatio = ratio;
                  worstWhere = pal.name;
                }
              }
        }
    }
    std::printf("raking_light_test: floor sweep worst ratio %.3f:1 (%s), "
                "margin over the floor less byte rounding %+.4f\n",
                static_cast<double>(worstRatio), worstWhere,
                static_cast<double>(worstMargin));
    check(worstMargin >= -1e-4f,
          "no light, dial or palette drags the page-mean paper under 7:1 (less "
          "the field's own byte rounding) with every other paper consumer at "
          "its full share and the lamp at its darkest pixel");
    // And the shipped page has a budget worth seeing: the lamp's cap at the
    // frozen palette and dials is at least 8% of the paper's light, else the
    // default cannot be "clearly visible".
    {
      letterpress::Params p;
      p.strengthPercent = 68;
      p.toothScale = 3.36f;
      p.paperDarkenBudget = letterpress::paperBudget(pals[0].ink, pals[0].paper);
      const float left = letterpress::remainingPaperBudget(p);
      // Wove (no wires) and India's show-through at its declared share.
      const float lamp = lampBudget(left - 0.5f * left);
      std::printf("raking_light_test: shipped page paper budget %.3f, after "
                  "tooth %.3f, lamp cap (worst-case show-through) %.3f\n",
                  static_cast<double>(p.paperDarkenBudget),
                  static_cast<double>(left), static_cast<double>(lamp));
      check(lamp >= 0.08f,
            "the shipped page leaves the lamp at least 8% of the paper's "
            "light, even with the show-through at its full declared share");
    }
  }

  if (failures == 0) std::printf("raking_light_test: PASS\n");
  return failures == 0 ? 0 : 1;
}
