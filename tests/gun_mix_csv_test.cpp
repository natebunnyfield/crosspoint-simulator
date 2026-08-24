// Host test for src/GunMixCsv.h -- the four-gun mixer's CSV codec.
//
// Exists because of the duplicated-guns bug (owner report 2026-08-22): the
// iOS mixer matched phosphorMixBlend weights to guns BY PRESET, so two guns
// sharing a phosphor both loaded whichever shared pair parsed last --
// "40:70,40:10,24:50,21:0" opened as 10/10/50/off, and the first save then
// destroyed the 70 for good. Every failure mode here is a silently wrong
// stored recipe, which no compiler and no screenshot of a fresh mix can see.

#include "GunMixCsv.h"

#include <cstdio>
#include <cstring>
#include <string>
#include "TestCheck.h"
using testcheck::check;

using namespace gunmix;

static int &failures = testcheck::g_failures;
static bool same4(const int a[4], const int b[4]) {
  return std::memcmp(a, b, 4 * sizeof(int)) == 0;
}

int main() {
  // The shipped default assignment: P22R, P22G, P22B, P45.
  const int defaults[kGunCount] = {
      panelpalette::kPresetRedCrt, panelpalette::kPresetP22GCrt,
      panelpalette::kPresetBlueTvCrt, panelpalette::kPresetWhiteCrt};

  // --- THE BUG, PINNED: duplicates keep their OWN weights ------------------
  {
    const int guns[kGunCount] = {40, 40, 24, 21};  // R and G both P22G
    int presets[kGunCount] = {0, 0, 0, 0};
    check(parseAssign("40,40,24,21", presets), "duplicate assignment parses");
    check(same4(presets, guns), "duplicate assignment lands per gun");
    int w[kGunCount] = {-1, -1, -1, -1};
    check(parseWeights("40:70,40:10,24:50,21:0", presets, w),
          "duplicate blend parses");
    check(w[0] == 70 && w[1] == 10 && w[2] == 50 && w[3] == 0,
          "duplicated guns keep DISTINCT weights (the 2026-08-22 collapse)");
  }

  // --- round-trip: encode then parse is the identity, duplicates included --
  {
    const int presets[kGunCount] = {40, 40, 40, 21};
    const int w[kGunCount] = {100, 1, 0, 33};
    check(encodeAssign(presets) == "40,40,40,21", "assign encodes in gun order");
    check(encodeBlend(presets, w) == "40:100,40:1,40:0,21:33",
          "blend encodes positionally, weight-0 guns included");
    int p2[kGunCount] = {0, 0, 0, 0};
    int w2[kGunCount] = {-1, -1, -1, -1};
    check(parseAssign(encodeAssign(presets), p2) && same4(p2, presets),
          "assign round-trips");
    check(parseWeights(encodeBlend(presets, w), p2, w2) && same4(w2, w),
          "blend round-trips with duplicates");
  }

  // --- assignment fallback is WHOLE ----------------------------------------
  {
    int p[kGunCount] = {9, 9, 9, 9};
    const int untouched[kGunCount] = {9, 9, 9, 9};
    check(!parseAssign("", p) && same4(p, untouched), "empty assign refused");
    check(!parseAssign("40,24,21", p) && same4(p, untouched),
          "three entries refused");
    check(!parseAssign("40,24,21,11,6", p) && same4(p, untouched),
          "five entries refused");
    check(!parseAssign("40,24,x,21", p) && same4(p, untouched),
          "junk entry refused");
    check(!parseAssign("40,,24,21", p) && same4(p, untouched),
          "empty entry refused");
    // Preset 0 is Custom -- a slot, not a phosphor; 4 is a plain palette row.
    check(!parseAssign("40,0,24,21", p) && same4(p, untouched),
          "non-mixable preset refused");
    check(!parseAssign("40,-1,24,21", p) && same4(p, untouched),
          "negative preset refused");
  }

  // --- weights fallback is WHOLE, per the store's philosophy ---------------
  {
    int w[kGunCount] = {7, 7, 7, 7};
    const int untouched[kGunCount] = {7, 7, 7, 7};
    check(!parseWeights("", defaults, w) && same4(w, untouched),
          "empty blend refused");
    check(!parseWeights("11:50,40:50,24:50", defaults, w) && same4(w, untouched),
          "short blend refused (three pairs)");
    check(!parseWeights("11:50,40:50,24:50,21:0,6:9", defaults, w) &&
              same4(w, untouched),
          "long blend refused (five pairs)");
    check(!parseWeights("11:50,40:50,24:50,21", defaults, w) &&
              same4(w, untouched),
          "pair with no colon refused");
    check(!parseWeights("11:50,40:x,24:50,21:0", defaults, w) &&
              same4(w, untouched),
          "junk weight refused");
    // A blend written against a DIFFERENT assignment: the cross-check fails
    // and the whole set falls back -- matching it up by preset instead is
    // exactly the collapse this codec forbids.
    check(!parseWeights("40:50,11:50,24:50,21:0", defaults, w) &&
              same4(w, untouched),
          "reordered presets refused, not re-matched");
    // The legacy store from the removed four-tab UI ("6:3,15:1") is short and
    // foreign: refused whole, guns keep their defaults -- same outcome the
    // by-preset load gave it.
    check(!parseWeights("6:3,15:1", defaults, w) && same4(w, untouched),
          "legacy two-pair recipe refused whole");
  }

  // --- clamping ------------------------------------------------------------
  {
    int w[kGunCount] = {0, 0, 0, 0};
    check(parseWeights("11:999,40:-5,24:100,21:0", defaults, w),
          "out-of-range weights still parse");
    check(w[0] == kWeightMax && w[1] == 0 && w[2] == 100 && w[3] == 0,
          "weights clamp to 0..kWeightMax");
  }

  if (failures) { std::printf("%d failure(s)\n", failures); return 1; }
  std::printf("gun_mix_csv: all checks passed\n");
  return 0;
}
