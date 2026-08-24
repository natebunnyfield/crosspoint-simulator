// Host test for src/PanelSource.h -- WHERE EACH POLARITY'S TONES COME FROM.
//
// Written against owner P1, 2026-08-23: "ink is not being picked up. recreate,
// review and fix sourcing for light and dark to be more accurate on load,
// switch etc." The bug was reproduced on an iPhone Air simulator before a line
// was changed, and the numbers in this file are that measurement.
//
// WHY THIS TEST HAD TO ASSERT VALUES. tests/chip_tint_source_test.py already
// guarded this area, and it passed through the whole bug, because it asserts a
// delegation CHAIN -- "does the keyboard bar call panelForPrefs" -- and never a
// tone. A single reader over a store that two writers corrupt is still one
// reader; the chain was intact the entire time the light page was rendering a
// color nobody chose. So every case below drives the real decision functions
// with the real ink and phosphor tables and compares the RESULTING BYTES.
//
// THE THREE PATHS THE OWNER NAMED are each an explicit case: load (a store read
// cold), switch (the same store asked for the other polarity), and the editor
// sequences that are the actual defect. There is no separate "relaunch" case
// because a relaunch IS load -- these functions hold no state, which is half
// of why the decision was pulled out of the two .mm editors in the first place.
//
//   c++ -std=c++17 -Isrc -Iios tests/panel_source_test.cpp \
//     -o /tmp/panel_source_test && /tmp/panel_source_test

#include <cstdio>
#include <cstring>

#include "GunMixCsv.h"
#include "LightInkPalette.h"
#include "PadPalette.h"
#include "PanelPalette.h"
#include "PanelSource.h"
#include "PhosphorMix.h"

static int failures = 0;

static void check(bool ok, const char *what) {
  if (ok) return;
  std::printf("FAIL %s\n", what);
  failures++;
}

static void checkRgb(const unsigned char got[3], unsigned r, unsigned g,
                     unsigned b, const char *what) {
  if (got[0] == r && got[1] == g && got[2] == b) return;
  std::printf("FAIL %s: got %02X%02X%02X, want %02X%02X%02X\n", what, got[0],
              got[1], got[2], r, g, b);
  failures++;
}

static void checkInt(int got, int want, const char *what) {
  if (got == want) return;
  std::printf("FAIL %s: got %d, want %d\n", what, got, want);
  failures++;
}

static bool same(const panelpalette::Palette &a,
                 const panelpalette::Palette &b) {
  return std::memcmp(a.ink, b.ink, 3) == 0 &&
         std::memcmp(a.paper, b.paper, 3) == 0;
}

static unsigned pack(const unsigned char c[3]) {
  return (unsigned(c[0]) << 16) | (unsigned(c[1]) << 8) | unsigned(c[2]);
}

// --- the two editors, as the .mm files perform them -------------------------
//
// These mirror ios/CrossPointLightInkPicker.mm's applySelection and
// ios/CrossPointPaletteMixer.mm's applyGuns, in their order: claim the shared
// Custom slot (which freezes the OTHER polarity), then write your own two
// fields. The claim itself is the shipped function; the tests/panel_source_
// test.py companion is what pins that the real editors still call it and still
// write only their own polarity's keys.

static void inkPickerApplies(panelsource::Store &s, int ink, int paper,
                             int densityPct) {
  const panelsource::Claim claim =
      panelsource::claimCustom(s.preset, /*editingDark=*/false);
  if (claim.freezeOther) {
    const panelpalette::Palette frozen =
        panelsource::panelFor(s, claim.freezeDark);
    const int d = claim.freezeDark ? 1 : 0;
    s.customInk[d] = int(pack(frozen.ink));
    s.customPaper[d] = int(pack(frozen.paper));
    if (claim.freezeDark) s.darkSnapshotPreset = claim.rememberPhosphor;
    s.preset = panelpalette::kPresetCustom;
  }
  unsigned char wash[3], ground[3];
  lightink::inkAtDensity(ink, paper, densityPct, wash);
  lightink::paperAtStrength(paper, lightink::kPaperStrengthDefault, ground);
  s.customInk[0] = int(pack(wash));
  s.customPaper[0] = int(pack(ground));
}

static void mixerApplies(panelsource::Store &s, int preset, int weight) {
  const panelsource::Claim claim =
      panelsource::claimCustom(s.preset, /*editingDark=*/true);
  if (claim.freezeOther) {
    const panelpalette::Palette frozen =
        panelsource::panelFor(s, claim.freezeDark);
    const int d = claim.freezeDark ? 1 : 0;
    s.customInk[d] = int(pack(frozen.ink));
    s.customPaper[d] = int(pack(frozen.paper));
    if (claim.freezeDark) s.darkSnapshotPreset = claim.rememberPhosphor;
    s.preset = panelpalette::kPresetCustom;
  }
  phosphormix::Component c{};
  c.preset = preset;
  c.weight = weight;
  const phosphormix::Result r = phosphormix::mixBlend(&c, 1);
  s.customInk[1] = int(pack(r.dark.ink));
  s.customPaper[1] = int(pack(r.dark.paper));
  s.mixActive = true;
}

// ...and the Presets list, as ios/CrossPointPresetList.mm performs it through
// CrossPointPrefs_selectPanelPreset: one shared protocol, three fields.
static void presetSelected(panelsource::Store &s, int preset) {
  s = panelsource::applyRelease(s, panelsource::releaseCustom(preset));
}

// --- THE FOUR GUNS, AS THE STORE HOLDS THEM ---------------------------------
//
// Owner request 2026-08-23: "selecting a preset should set the guns' values
// too." The gun recipe is a SECOND store (phosphorGunAssign + phosphorMixBlend,
// ios/GunStore.h) and a selection now writes it, so this test carries it too --
// the round trip below is only worth asserting end to end.
struct Guns {
  int preset[phosphormix::kMaxComponents];
  int weight[phosphormix::kMaxComponents];
};

static Guns freshGuns() {
  Guns g{};
  for (int i = 0; i < phosphormix::kMaxComponents; i++) {
    g.preset[i] = phosphormix::kDefaultGunPreset[i];
    g.weight[i] = phosphormix::kDefaultGunWeight[i];
  }
  return g;
}

static bool sameGuns(const Guns &a, const Guns &b) {
  for (int i = 0; i < phosphormix::kMaxComponents; i++)
    if (a.preset[i] != b.preset[i] || a.weight[i] != b.weight[i]) return false;
  return true;
}

// What the mixer computes from a stored recipe: weight 0 means the gun is off
// and its component is absent, exactly as ios/CrossPointPaletteMixer.mm's
// computeGuns does it.
static phosphormix::Result mixOf(const Guns &g) {
  phosphormix::Component c[phosphormix::kMaxComponents];
  int n = 0;
  for (int i = 0; i < phosphormix::kMaxComponents; i++) {
    if (g.weight[i] <= 0) continue;
    c[n].preset = g.preset[i];
    c[n].weight = g.weight[i];
    n++;
  }
  return phosphormix::mixBlend(c, n);
}

// ...and the Presets list WITH the seed, as CrossPointPrefs_selectPanelPreset
// performs it: the release first, then the seed, and the seed only when the
// release applied. Note what is NOT here -- nothing sets mixActive. The guns
// are seeded to MATCH the preset, never switched on; turning them on would put
// a blend on screen under a preset's name, which is S-020 again.
static void presetSelectedWithGuns(panelsource::Store &s, Guns &g, int preset) {
  const panelsource::Release r = panelsource::releaseCustom(preset);
  s = panelsource::applyRelease(s, r);
  if (!r.apply) return;
  const phosphormix::GunSeed seed =
      phosphormix::seedForPreset(r.preset, g.preset);
  if (!seed.apply) return;
  for (int i = 0; i < phosphormix::kMaxComponents; i++) {
    g.preset[i] = seed.preset[i];
    g.weight[i] = seed.weight[i];
  }
}

// THE WRONG WAY TO WRITE THE SAME FEATURE, kept because it is the one this
// test exists to reject. Moving only the integer looks correct on screen and
// in the store; what it leaves behind is a mix flag that outranks the frozen
// phosphor at the NEXT claim.
static void naiveSelected(panelsource::Store &s, int preset) {
  s.preset = preset;
}


// ONLY WHAT THIS PAGE CAN BE -- owner ruling 2026-08-23, "only show presets
// available in that mode". The partition must be TOTAL (every preset belongs to
// exactly one editor) and must match the doctrine (a decay means a tube), or a
// preset becomes unreachable from both lists, which is how the presets were
// lost in the first place.
static void testPresetOfferPartition() {
  using namespace panelpalette;
  int dark = 0, light = 0;
  for (int i = 0; i < kPresetInfoCount; i++) {
    const int p = kPresetInfo[i].preset;
    const bool inDark = presetOfferedInDark(p);
    // Total: exactly one list offers it. (The predicate is a bool, so this
    // checks the DOCTRINE rather than the tautology: a trail implies dark.)
    check(inDark == (trailMsForPreset(p) > 0.0f),
          "a preset is offered where its own decay says it belongs");
    (inDark ? dark : light)++;
  }
  check(dark + light == kPresetInfoCount,
        "every preset is offered in exactly one appearance");
  // Neither list may be empty, or an editor ships a Presets button opening
  // nothing.
  check(dark > 0 && light > 0,
        "both lists have rows -- neither editor opens an empty list");
  std::printf("panel_source_test: preset offers %d dark / %d light\n",
              dark, light);
}


// --- WHAT "THE GUNS FOR THIS PRESET" IS, PRESET BY PRESET -------------------
//
// Owner request 2026-08-23: "selecting a preset should set the guns' values
// too." Every assertion here is about a stored RECIPE, which nothing on screen
// shows until a slider is moved -- a wrong seed is silent at the moment it is
// made and jumps the page one gesture later. Same failure shape as the mix flag
// the release protocol clears, so it is asserted the same way: in values, and
// against the alternative implementation as well as the shipped one.
static void testGunSeedPerPreset() {
  using namespace panelpalette;
  const Guns defaults = freshGuns();
  int pure = 0, premix = 0, cascade = 0, paper = 0;

  for (int i = 0; i < kPresetInfoCount; i++) {
    const PresetInfo &in = kPresetInfo[i];
    const phosphormix::GunSeed s =
        phosphormix::seedForPreset(in.preset, defaults.preset);

    // THE PARTITION IS TOTAL AND MATCHES THE DOCTRINE. Only two things refuse:
    // a cascade premix (no blend is two layers in sequence) and a row with no
    // phosphor (a paper page, which is the light picker's, not the mixer's).
    // A third refusal reason means a phosphor row has lost its recipe.
    if (!in.phosphor) {
      checkInt(s.reason, phosphormix::SeedNoPhosphor,
               "a paper row refuses because it names no phosphor");
      check(!s.apply, "a paper row seeds nothing");
      check(!presetOfferedInDark(in.preset),
            "a row with no phosphor is the LIGHT picker's, so a preset chosen "
            "there can never reach the guns");
      paper++;
      continue;
    }
    check(presetOfferedInDark(in.preset),
          "a phosphor row is the mixer's, so its seed is reachable");

    if (phosphormix::isMixablePreset(in.preset)) {
      checkInt(s.reason, phosphormix::SeedPurePhosphor,
               "a pure phosphor seeds one gun at full");
      check(s.apply, "a pure phosphor seeds");
      pure++;

      // FAITHFUL, AND EXACTLY SO: one component IS resolve() of that preset, in
      // both polarities, so the recipe the mixer shows is not an approximation
      // of where the page is -- it is where the page is. This is the property
      // that makes the next gun move a nudge instead of a jump.
      Guns g{};
      for (int k = 0; k < phosphormix::kMaxComponents; k++) {
        g.preset[k] = s.preset[k];
        g.weight[k] = s.weight[k];
      }
      const phosphormix::Result r = mixOf(g);
      check(same(r.dark, presetPalette(in.preset, true)),
            "the seeded mix renders the preset's DARK pair byte for byte");
      check(same(r.light, presetPalette(in.preset, false)),
            "...and its LIGHT pair, which is what makes the seed honest in "
            "both appearances");
      checkInt(int(r.trailMs), int(trailMsForPreset(in.preset)),
               "...and decays at the preset's own rate");

      // Exactly one gun carries it, at the ceiling; the rest are off but keep
      // their assignment. A weight the codec would clamp is a seed that reads
      // back as something else.
      int lit = 0;
      for (int k = 0; k < phosphormix::kMaxComponents; k++) {
        if (s.weight[k] == 0) continue;
        lit++;
        checkInt(s.weight[k], phosphormix::kGunWeightMax,
                 "the carrier gun is at the slider ceiling");
        checkInt(k, s.carrier, "the lit gun is the reported carrier");
        checkInt(s.preset[k], migratePreset(in.preset),
                 "the carrier holds the preset itself");
      }
      checkInt(lit, 1, "a pure phosphor lights exactly one gun");
    } else if (phosphormix::recipeFor(in.phosphor) &&
               phosphormix::recipeFor(in.phosphor)->mode == phosphormix::Blend) {
      checkInt(s.reason, phosphormix::SeedBlendPremix,
               "a blend premix seeds its fitted recipe");
      check(s.apply, "a blend premix seeds");
      premix++;

      // RATIO-EXACT AGAINST THE TABLE. kPremixRecipes was refitted by
      // exhaustive search to dE 3.8-9.6 against the shipped premix pair
      // (2026-08-21); mixBlend normalizes by the total, so only ratios render
      // and a ROUNDED seed would be a different mixture from the one that was
      // fitted. The integer scale is what keeps it the same one.
      const phosphormix::PremixRecipe *r = phosphormix::recipeFor(in.phosphor);
      phosphormix::Component raw[3];
      int n = 0;
      const char *const pn[3] = {r->a, r->b, r->c};
      const int rw[3] = {r->weightA, r->weightB, r->weightC};
      for (int k = 0; k < 3 && pn[k]; k++) {
        raw[n].preset = phosphormix::presetForPhosphor(pn[k]);
        raw[n].weight = rw[k];
        check(raw[n].preset >= 0 && phosphormix::isMixablePreset(raw[n].preset),
              "every component the recipe table names resolves to a usable "
              "ingredient -- the branch that refuses a broken recipe is a "
              "guard, not a live path");
        n++;
      }
      const phosphormix::Result want = phosphormix::mixBlend(raw, n);
      Guns g{};
      for (int k = 0; k < phosphormix::kMaxComponents; k++) {
        g.preset[k] = s.preset[k];
        g.weight[k] = s.weight[k];
      }
      const phosphormix::Result got = mixOf(g);
      check(same(got.dark, want.dark) && same(got.light, want.light),
            "the seeded premix recipe renders exactly what the fitted table "
            "renders -- the scale is integer for this reason");
      checkInt(int(got.trailMs), int(want.trailMs),
               "...and decays identically");
    } else {
      // THE THREE CASCADES. A cascade is two layers in sequence: the flash
      // layer paints the page, the persistence layer is what lingers, in its
      // own color. No blend is both -- zero the persistence gun and there is no
      // afterglow, give it weight and it tints a page the cascade never tints.
      // So the guns are LEFT, and the mixer's readout says why.
      checkInt(s.reason, phosphormix::SeedCascadePremix,
               "a cascade premix refuses because no blend is a cascade");
      check(!s.apply, "a cascade premix seeds nothing");
      cascade++;
      // ...and the refusal is the honest one rather than a missing table row:
      // the recipe EXISTS, it is simply a Cascade.
      const phosphormix::PremixRecipe *r = phosphormix::recipeFor(in.phosphor);
      check(r && r->mode == phosphormix::Cascade,
            "the refused rows are the cascades, not rows whose recipe is gone");
    }
  }

  checkInt(pure + premix + cascade + paper, kPresetInfoCount,
           "every preset falls in exactly one seed category");
  check(pure > 0 && premix > 0 && cascade > 0 && paper > 0,
        "all four categories have members -- a category with none means the "
        "case below it has never run");
  std::printf(
      "panel_source_test: gun seeds %d pure / %d blend premix / %d cascade "
      "refused / %d paper refused\n",
      pure, premix, cascade, paper);
}

// EVERY SEED MUST SURVIVE THE STORE. The recipe is written as two CSVs whose
// weights are cross-checked against the assignment, and gunmix::parseAssign
// rejects a set that is not four MIXABLE presets -- whole, falling back to the
// defaults. A seed that cannot be read back is silently discarded on the next
// launch, which is indistinguishable from not seeding at all.
static void testGunSeedSurvivesTheStore() {
  Guns g = freshGuns();
  int seeded = 0;
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
    const int preset = panelpalette::kPresetInfo[i].preset;
    const phosphormix::GunSeed s = phosphormix::seedForPreset(preset, g.preset);
    // Fed forward deliberately: the assignments a seed leaves are the input to
    // the next one, so a seed that emits an unwritable set poisons every
    // selection after it rather than only its own.
    if (s.apply)
      for (int k = 0; k < phosphormix::kMaxComponents; k++) {
        g.preset[k] = s.preset[k];
        g.weight[k] = s.weight[k];
      }
    if (!s.apply) continue;
    seeded++;
    int backP[gunmix::kGunCount], backW[gunmix::kGunCount];
    for (int k = 0; k < gunmix::kGunCount; k++) { backP[k] = -1; backW[k] = -1; }
    check(gunmix::parseAssign(gunmix::encodeAssign(s.preset), backP),
          "a seeded assignment parses back -- if it does not, the next launch "
          "silently reverts to the default guns");
    check(gunmix::parseWeights(gunmix::encodeBlend(s.preset, s.weight), backP,
                               backW),
          "a seeded blend parses back against its own assignment");
    bool identical = true;
    for (int k = 0; k < gunmix::kGunCount; k++)
      identical = identical && backP[k] == s.preset[k] && backW[k] == s.weight[k];
    check(identical, "the recipe read back is the recipe written");
  }
  check(seeded > 30, "the sweep actually seeded something");
}

// A STORED ASSIGNMENT THE CODEC WOULD REJECT MUST NOT REACH THE OUTPUT.
// The load guarantees four mixable presets, so this is a guard rather than a
// live path -- but the failure it guards against is the silent one above, and
// the honest place to hold the line is where the value is produced.
static void testGunSeedRepairsABadAssignment() {
  const int junk[phosphormix::kMaxComponents] = {
      panelpalette::kPresetCustom,   // not a phosphor
      4242,                          // not a preset
      panelpalette::kPresetCascadeCrt,  // a premix: a recipe, not an ingredient
      panelpalette::kPresetLatte};   // a paper row
  const phosphormix::GunSeed s =
      phosphormix::seedForPreset(panelpalette::kPresetGreenCrt, junk);
  check(s.apply, "a pure phosphor still seeds over a junk assignment");
  for (int k = 0; k < phosphormix::kMaxComponents; k++)
    check(phosphormix::isMixablePreset(s.preset[k]),
          "every gun the seed emits is a usable ingredient, whatever the store "
          "held");
  int backP[gunmix::kGunCount];
  check(gunmix::parseAssign(gunmix::encodeAssign(s.preset), backP),
        "...so the repaired assignment is writable");
  // The slots it did not have to touch take the CHANNEL DEFAULT, not the junk.
  checkInt(s.preset[1], phosphormix::kDefaultGunPreset[1],
           "an unusable stored gun falls back to its channel default");
}

int main() {
  testPresetOfferPartition();
  testGunSeedPerPreset();
  testGunSeedSurvivesTheStore();
  testGunSeedRepairsABadAssignment();
  // The install the owner had: the app's registered default preset is White
  // CRT (ios/CrossPointPrefs.mm registerDefaults, panelPalettePreset 21).
  constexpr int kWhiteCrt = panelpalette::kPresetWhiteCrt;
  // Payne's Gray, row 15, on Bright White at full density -- the exact pick
  // used to reproduce the report.
  constexpr int kPaynesGray = 15;
  const panelpalette::Palette crtLight =
      panelpalette::presetPalette(kWhiteCrt, false);
  const panelpalette::Palette crtDark =
      panelpalette::presetPalette(kWhiteCrt, true);

  // --- LOAD: an untouched install -----------------------------------------
  {
    panelsource::Store s{};
    s.preset = kWhiteCrt;
    check(same(panelsource::panelFor(s, false), crtLight),
          "an untouched install's light page is the named preset's light pair");
    check(same(panelsource::panelFor(s, true), crtDark),
          "an untouched install's dark page is the named preset's dark pair");
    checkInt(panelsource::glowPreset(s), kWhiteCrt,
             "an untouched install glows as the preset it names");
  }

  // --- LOAD: a named preset ignores stale hex in BOTH polarities -----------
  //
  // Both editors leave hex behind when the owner later picks a preset row in
  // Settings.app. Honoring it would make that row stop working for whichever
  // polarity had been edited -- a silently removed capability, and the exact
  // failure this test's subject is about, only pointing the other way.
  {
    panelsource::Store s{};
    s.preset = panelpalette::kPresetDefault;
    s.customInk[0] = 0x323D47;
    s.customPaper[0] = 0xFBFBF9;
    s.customInk[1] = 0xFF6F6C;
    s.customPaper[1] = 0x1A0300;
    s.darkSnapshotPreset = kWhiteCrt;
    s.mixActive = true;
    check(same(panelsource::panelFor(s, false),
               panelpalette::presetPalette(panelpalette::kPresetDefault, false)),
          "a named preset overrides stale light hex");
    check(same(panelsource::panelFor(s, true),
               panelpalette::presetPalette(panelpalette::kPresetDefault, true)),
          "a named preset overrides stale dark hex");
    checkInt(panelsource::glowPreset(s), panelpalette::kPresetDefault,
             "a named preset overrides a stale mix and a stale snapshot");
  }

  // --- THE REPORT: pick a light ink, then move a gun in dark ---------------
  //
  // This is the owner's sequence, and the assertion that would have caught the
  // bug. Before the fix the mixer wrote all four hex fields, so the light ink
  // measured 6E0500 -- a red -- after a single gun move, with the picker still
  // showing Payne's Gray as chosen.
  {
    panelsource::Store s{};
    s.preset = kWhiteCrt;

    inkPickerApplies(s, kPaynesGray, /*paper=*/0, /*densityPct=*/100);
    unsigned char wantInk[3], wantPaper[3];
    lightink::inkAtDensity(kPaynesGray, 0, 100, wantInk);
    lightink::paperAtStrength(0, lightink::kPaperStrengthDefault, wantPaper);
    checkRgb(panelsource::panelFor(s, false).ink, wantInk[0], wantInk[1],
             wantInk[2], "the light page takes the chosen ink");
    checkRgb(panelsource::panelFor(s, false).ink, 0x32, 0x3D, 0x47,
             "...which for Payne's Gray at full on Bright White is 323D47");
    // The freeze: dark keeps the tones AND the phosphor it had.
    check(same(panelsource::panelFor(s, true), crtDark),
          "picking a light ink leaves the dark page's tones alone");
    checkInt(panelsource::glowPreset(s), kWhiteCrt,
             "picking a light ink leaves the dark page's PHOSPHOR alone -- the "
             "half that used to be lost, turning a 283 ms trail into 0");

    // ...now the mixer, in dark, on the same store.
    const panelpalette::Palette lightBefore = panelsource::panelFor(s, false);
    mixerApplies(s, /*preset=*/panelpalette::kPresetGreenCrt, /*weight=*/100);
    check(same(panelsource::panelFor(s, false), lightBefore),
          "MOVING A GUN IN DARK MODE MUST NOT TOUCH THE LIGHT PAGE -- this is "
          "the reported bug");
    checkRgb(panelsource::panelFor(s, false).ink, 0x32, 0x3D, 0x47,
             "...the chosen ink is still the chosen ink");
    check(!same(panelsource::panelFor(s, true), crtDark),
          "the mixer does change the dark page");
    checkInt(panelsource::glowPreset(s), panelpalette::kPresetCustom,
             "an active mix answers for its own decay rather than deferring to "
             "the frozen phosphor");
  }

  // --- THE MIRROR: mix first, then pick an ink ----------------------------
  {
    panelsource::Store s{};
    s.preset = kWhiteCrt;
    mixerApplies(s, panelpalette::kPresetGreenCrt, 100);
    const panelpalette::Palette darkAfterMix = panelsource::panelFor(s, true);
    check(same(panelsource::panelFor(s, false), crtLight),
          "the mixer's claim freezes the light page at what was on screen, not "
          "at the blend's light rendition");

    inkPickerApplies(s, /*ink=*/2 /*Iron Gall*/, /*paper=*/0, 100);
    check(same(panelsource::panelFor(s, true), darkAfterMix),
          "PICKING A LIGHT INK MUST NOT TOUCH THE DARK PAGE, even when the dark "
          "page is a mix");
    checkInt(panelsource::glowPreset(s), panelpalette::kPresetCustom,
             "the mix still owns the decay after a light ink pick");
    unsigned char iron[3];
    lightink::inkAtDensity(2, 0, 100, iron);
    checkRgb(panelsource::panelFor(s, false).ink, iron[0], iron[1], iron[2],
             "and the light page is the newly chosen ink");
  }

  // --- THE ROUND TRIP: preset -> edit an ink -> preset again --------------
  //
  // Owner ruling 2026-08-23, "add a Presets row back to the pickers." Every
  // named preset became unreachable AS A PRESET on 2026-08-22, when the
  // Settings.app palette row left: from then on the only writer of the shared
  // integer was the claim, which can only ever point it AT Custom. This case is
  // the road back, and it asserts BYTES at every station because a selection
  // that looks right and leaves one Custom-only key behind is invisible until
  // the claim after it.
  {
    panelsource::Store s{};
    s.preset = kWhiteCrt;

    // 1. A named preset owns both polarities and glows as itself.
    check(same(panelsource::panelFor(s, false), crtLight),
          "round trip station 1: light is the preset's light pair");
    check(same(panelsource::panelFor(s, true), crtDark),
          "round trip station 1: dark is the preset's dark pair");
    checkInt(panelsource::glowPreset(s), kWhiteCrt,
             "round trip station 1: the phosphor is the preset's");

    // 2. Edit an ink: light becomes the ink, dark FREEZES with its phosphor,
    //    and the slot is Custom.
    inkPickerApplies(s, kPaynesGray, /*paper=*/0, /*densityPct=*/100);
    checkInt(s.preset, panelpalette::kPresetCustom,
             "round trip station 2: editing an ink claims the Custom slot");
    checkRgb(panelsource::panelFor(s, false).ink, 0x32, 0x3D, 0x47,
             "round trip station 2: light is the chosen ink");
    check(same(panelsource::panelFor(s, true), crtDark),
          "round trip station 2: dark is frozen at the preset's pair");
    checkInt(panelsource::glowPreset(s), kWhiteCrt,
             "round trip station 2: the frozen phosphor survives");

    // 3. Pick a preset again: BOTH polarities go back, byte for byte, and the
    //    phosphor is the new preset's -- not the frozen one, and not none.
    constexpr int kGreen = panelpalette::kPresetGreenCrt;
    presetSelected(s, kGreen);
    checkInt(s.preset, kGreen, "round trip station 3: the integer is the name");
    check(same(panelsource::panelFor(s, false),
               panelpalette::presetPalette(kGreen, false)),
          "round trip station 3: the LIGHT page is the preset's, over the ink "
          "that claimed the slot");
    check(same(panelsource::panelFor(s, true),
               panelpalette::presetPalette(kGreen, true)),
          "round trip station 3: the DARK page is the preset's, over the pair "
          "that was frozen into it");
    checkInt(panelsource::glowPreset(s), kGreen,
             "round trip station 3: THE PHOSPHOR FOLLOWS -- the half of S-020 "
             "that was the glow rather than the tones");
    check(panelpalette::trailMsForPreset(panelsource::glowPreset(s)) > 0.0f,
          "round trip station 3: ...and Green CRT is a phosphor, so it glows");
    checkInt(s.darkSnapshotPreset, panelpalette::kPresetCustom,
             "round trip station 3: the frozen-phosphor key is CLEARED, not "
             "left to contradict the preset");
    check(!s.mixActive,
          "round trip station 3: the mix flag is cleared with it");

    // ...and the store is now indistinguishable from a fresh install that had
    // simply chosen Green CRT. That is what "both polarities are that preset"
    // has to mean; stale hex under a name must not be reachable.
    panelsource::Store fresh{};
    fresh.preset = kGreen;
    check(same(panelsource::panelFor(s, false),
               panelsource::panelFor(fresh, false)) &&
              same(panelsource::panelFor(s, true),
                   panelsource::panelFor(fresh, true)) &&
              panelsource::glowPreset(s) == panelsource::glowPreset(fresh),
          "round trip station 3: the edited store now renders exactly as an "
          "untouched install that chose the same preset");

    // 4. ...and the trip runs again from there: the claim still works after a
    //    release, freezing the NEW preset's dark pair and phosphor.
    inkPickerApplies(s, /*ink=*/2 /*Iron Gall*/, 0, 100);
    check(same(panelsource::panelFor(s, true),
               panelpalette::presetPalette(kGreen, true)),
          "round trip station 4: the second claim freezes the NEW preset's "
          "dark pair");
    checkInt(panelsource::glowPreset(s), kGreen,
             "round trip station 4: ...and the NEW preset's phosphor");
  }

  // --- THE SAME TRIP THROUGH THE MIXER, which is where the mix flag bites ---
  //
  // A selection that only moved the integer would pass every assertion above:
  // glowPreset returns early on a named preset, so a stale mix is silent. It
  // speaks at the NEXT claim, and then it outranks the frozen phosphor -- the
  // dark page decays at the rate of a blend that is no longer reachable from
  // any control. Both halves are asserted here, the right one and the wrong.
  {
    panelsource::Store s{};
    s.preset = kWhiteCrt;
    mixerApplies(s, panelpalette::kPresetGreenCrt, 100);
    check(s.mixActive, "the mixer leaves a mix in force");
    checkInt(panelsource::glowPreset(s), panelpalette::kPresetCustom,
             "...which owns the decay while it does");

    panelsource::Store correct = s;
    presetSelected(correct, kWhiteCrt);
    panelsource::Store naive = s;
    naiveSelected(naive, kWhiteCrt);

    // On screen, immediately after the pick, the two are indistinguishable.
    check(same(panelsource::panelFor(correct, true),
               panelsource::panelFor(naive, true)) &&
              panelsource::glowPreset(correct) == panelsource::glowPreset(naive),
          "a naive selection is invisible at the moment it is made -- which is "
          "why this is asserted through the claim that follows it");

    // One ink pick later, it is not.
    inkPickerApplies(correct, kPaynesGray, 0, 100);
    inkPickerApplies(naive, kPaynesGray, 0, 100);
    checkInt(panelsource::glowPreset(correct), kWhiteCrt,
             "after a proper selection, the next claim freezes the SELECTED "
             "preset's phosphor");
    checkInt(panelsource::glowPreset(naive), panelpalette::kPresetCustom,
             "after a naive one, a mix nobody can reach answers instead -- the "
             "contradiction Release exists to prevent");
  }

  // --- THE ROUND TRIP WITH THE GUNS IN IT ---------------------------------
  //
  // Owner request 2026-08-23: "selecting a preset should set the guns' values
  // too." Stations: a preset seeds the guns; the page is still the PRESET and
  // not the blend; a gun move takes the page over exactly as before; and the
  // NEXT preset re-seeds rather than leaving the first one's recipe behind --
  // which is the whole complaint, since the mixer used to open on a recipe from
  // some earlier session.
  {
    panelsource::Store s{};
    s.preset = kWhiteCrt;
    Guns g = freshGuns();

    // 1. Select a preset that is on NO gun by default. The guns become it, and
    //    the page does not become the guns.
    constexpr int kGreen = panelpalette::kPresetGreenCrt;
    presetSelectedWithGuns(s, g, kGreen);
    check(!s.mixActive,
          "seeding the guns does NOT switch the mix on -- the preset still owns "
          "the page, and a blend on screen under a preset's name is S-020");
    check(same(panelsource::panelFor(s, true),
               panelpalette::presetPalette(kGreen, true)),
          "the dark page is still the preset's own pair, not the seeded mix's");
    check(same(mixOf(g).dark, panelpalette::presetPalette(kGreen, true)),
          "...and the seeded recipe would render that same pair if it were "
          "switched on, which is what 'the guns match' has to mean");
    checkInt(panelsource::glowPreset(s), kGreen,
             "the preset still owns the decay: a seeded recipe is not an active "
             "mix");

    // 2. Move a gun. The claim happens exactly as it did before the seed
    //    existed -- nothing about seeding changes the takeover.
    const panelpalette::Palette lightBefore = panelsource::panelFor(s, false);
    mixerApplies(s, panelpalette::kPresetRedCrt, 100);
    checkInt(s.preset, panelpalette::kPresetCustom,
             "moving a gun still claims the Custom slot");
    check(same(panelsource::panelFor(s, false), lightBefore),
          "...and still leaves the light page alone");

    // 3. Select a DIFFERENT preset. The guns follow it, rather than keeping the
    //    recipe the takeover left behind. This is the reported gap.
    constexpr int kAmber = 7;  // P3, on no default gun either
    const Guns beforeSecond = g;
    presetSelectedWithGuns(s, g, kAmber);
    check(!sameGuns(g, beforeSecond),
          "a second selection re-seeds the guns rather than leaving the first "
          "preset's recipe in place");
    check(same(mixOf(g).dark, panelpalette::presetPalette(kAmber, true)),
          "the guns are the NEW preset, byte for byte");
    check(!s.mixActive, "...and still off");

    // 4. The assignment the owner did not have to lose is not lost: only the
    //    gun that had to carry the preset moved, and the others kept their
    //    phosphor at weight 0.
    const phosphormix::GunSeed seed =
        phosphormix::seedForPreset(kAmber, beforeSecond.preset);
    for (int k = 0; k < phosphormix::kMaxComponents; k++) {
      if (k == seed.carrier) continue;
      checkInt(g.preset[k], beforeSecond.preset[k],
               "a gun the preset did not need keeps its assignment");
      checkInt(g.weight[k], 0, "...at weight 0");
    }

    // 5. A preset ALREADY on a gun lights that gun, rather than displacing a
    //    different one. With the shipped assignment, White is the W gun.
    Guns fresh = freshGuns();
    panelsource::Store s2{};
    s2.preset = panelpalette::kPresetCustom;
    presetSelectedWithGuns(s2, fresh, kWhiteCrt);
    checkInt(fresh.weight[3], phosphormix::kGunWeightMax,
             "selecting White lights the W gun it is already assigned to, not "
             "the R gun");
    checkInt(fresh.preset[0], phosphormix::kDefaultGunPreset[0],
             "...and leaves R holding P22R");
  }

  // --- A PRESET CHOSEN IN THE LIGHT PICKER MUST NOT TOUCH THE GUNS --------
  //
  // Deliberate, not incidental. The light picker offers exactly the rows with
  // no phosphor (panelpalette::presetOfferedInDark is false there), and the
  // guns are the DARK page's editor -- 2026-08-22 doctrine. A paper row names
  // no phosphor for them to hold, so there is nothing honest to seed.
  {
    for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
      const int preset = panelpalette::kPresetInfo[i].preset;
      if (panelpalette::presetOfferedInDark(preset)) continue;
      panelsource::Store s{};
      s.preset = panelpalette::kPresetCustom;
      Guns g = freshGuns();
      // ...and not only from the defaults: an owner who has built a mix must
      // keep it through every paper he tries.
      g.preset[0] = panelpalette::kPresetRedCrt;
      g.weight[0] = 37;
      g.weight[3] = 11;
      const Guns before = g;
      presetSelectedWithGuns(s, g, preset);
      checkInt(s.preset, panelpalette::migratePreset(preset),
               "a paper preset still selects for both appearances");
      check(sameGuns(g, before),
            "...and leaves the dark page's gun recipe byte for byte alone");
    }
  }

  // --- THE THREE CASCADES LEAVE THE GUNS ALONE, AND THAT IS THE ANSWER ----
  //
  // Not an oversight and not a TODO. A cascade is two layers in sequence; a
  // blend is one screen. Asserted against the ALTERNATIVE as well as the
  // shipped behavior: the obvious seed -- flash and persistence as two equal
  // guns -- renders a page the preset does not have, which is the failure mode
  // that would have shipped silently.
  {
    for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
      const panelpalette::PresetInfo &in = panelpalette::kPresetInfo[i];
      if (!in.phosphor) continue;
      const phosphormix::PremixRecipe *r = phosphormix::recipeFor(in.phosphor);
      if (!r || r->mode != phosphormix::Cascade) continue;

      panelsource::Store s{};
      s.preset = panelpalette::kPresetCustom;
      Guns g = freshGuns();
      const Guns before = g;
      presetSelectedWithGuns(s, g, in.preset);
      check(sameGuns(g, before),
            "a cascade premix leaves the stored recipe exactly as it was");

      // The refusal earns itself: the naive blend of the two layers is NOT the
      // cascade's page.
      Guns naive{};
      for (int k = 0; k < phosphormix::kMaxComponents; k++) {
        naive.preset[k] = phosphormix::kDefaultGunPreset[k];
        naive.weight[k] = 0;
      }
      naive.preset[0] = phosphormix::presetForPhosphor(r->a);
      naive.preset[1] = phosphormix::presetForPhosphor(r->b);
      naive.weight[0] = phosphormix::kGunWeightMax;
      naive.weight[1] = phosphormix::kGunWeightMax;
      check(!same(mixOf(naive).dark,
                  panelpalette::presetPalette(in.preset, true)),
            "...because blending the flash and persistence layers renders a "
            "different page from the cascade itself -- seeding it would put a "
            "recipe in the mixer that is not what is on screen");
    }
  }

  // --- CUSTOM IS NOT A ROW, AND NEITHER IS A NUMBER FROM THE FUTURE --------
  {
    panelsource::Store s{};
    s.preset = kWhiteCrt;
    inkPickerApplies(s, kPaynesGray, 0, 100);
    const panelsource::Store before = s;
    presetSelected(s, panelpalette::kPresetCustom);
    check(s.preset == before.preset && s.mixActive == before.mixActive &&
              s.darkSnapshotPreset == before.darkSnapshotPreset,
          "selecting Custom changes nothing: Custom is what an EDIT produces, "
          "and treating it as a row would clear the freeze that edit took");
    presetSelected(s, 4242);
    check(s.preset == before.preset,
          "an unknown integer selects nothing rather than a page the store "
          "cannot describe");
    // The retired numbers, which a list can never offer but a store can hold.
    for (int p = 0; p < 60; p++) {
      const int migrated = panelpalette::migratePreset(p);
      if (migrated == p) continue;
      panelsource::Store r{};
      r.preset = panelpalette::kPresetCustom;
      presetSelected(r, p);
      checkInt(r.preset, migrated,
               "selecting a retired preset selects its replacement");
    }
  }

  // --- SWITCH: the same store, asked for the other polarity ---------------
  //
  // Nothing here caches, so a switch is one more call. Asserted anyway, because
  // "is the light pair recomputed or is a cached dark pair re-pushed" is the
  // question the owner's report raises, and a future cache added for speed must
  // fail this rather than pass it.
  {
    panelsource::Store s{};
    s.preset = kWhiteCrt;
    inkPickerApplies(s, kPaynesGray, 0, 100);
    for (int trip = 0; trip < 4; trip++) {
      const bool dark = (trip % 2) != 0;
      const panelpalette::Palette p = panelsource::panelFor(s, dark);
      if (dark)
        check(same(p, crtDark), "dark survives repeated appearance switches");
      else
        checkRgb(p.ink, 0x32, 0x3D, 0x47,
                 "light survives repeated appearance switches");
    }
    // ...and a relaunch is the same read of the same bytes.
    const panelsource::Store reloaded = s;
    check(same(panelsource::panelFor(reloaded, false),
               panelsource::panelFor(s, false)),
          "a relaunch resolves the light page identically");
    check(same(panelsource::panelFor(reloaded, true),
               panelsource::panelFor(s, true)),
          "a relaunch resolves the dark page identically");
  }

  // --- THE CLAIM IS ONE-SHOT ----------------------------------------------
  //
  // A second claim by either editor must freeze nothing: by then both
  // polarities hold owner choices, and re-freezing is how one editor eats the
  // other's work. This is the property the mixer lacked entirely.
  {
    checkInt(panelsource::claimCustom(panelpalette::kPresetCustom, false)
                     .freezeOther
                 ? 1
                 : 0,
             0, "a light-editor claim on an already-Custom slot freezes nothing");
    checkInt(panelsource::claimCustom(panelpalette::kPresetCustom, true)
                     .freezeOther
                 ? 1
                 : 0,
             0, "a dark-editor claim on an already-Custom slot freezes nothing");
    const panelsource::Claim light = panelsource::claimCustom(kWhiteCrt, false);
    check(light.freezeOther && light.freezeDark,
          "the light editor freezes the DARK polarity");
    checkInt(light.rememberPhosphor, kWhiteCrt,
             "...and remembers its phosphor");
    const panelsource::Claim dark = panelsource::claimCustom(kWhiteCrt, true);
    check(dark.freezeOther && !dark.freezeDark,
          "the dark editor freezes the LIGHT polarity");
    checkInt(dark.rememberPhosphor, panelpalette::kPresetCustom,
             "...and has no phosphor to remember for a paper page");
  }

  // --- A RETIRED PRESET FOLLOWS ITS REPLACEMENT INTO THE FREEZE -----------
  //
  // The snapshot stores an integer and reads it back later, which is exactly
  // the shape panelpalette::migratePreset exists for. Freezing a raw number
  // that has since been re-pointed would revive a retired phosphor.
  {
    for (int p = 0; p < 60; p++) {
      const int migrated = panelpalette::migratePreset(p);
      if (migrated == p) continue;
      panelsource::Store s{};
      s.preset = panelpalette::kPresetCustom;
      s.darkSnapshotPreset = p;
      checkInt(panelsource::glowPreset(s), migrated,
               "a frozen phosphor follows its replacement");
      checkInt(panelsource::claimCustom(p, false).rememberPhosphor, migrated,
               "a claim freezes the replacement, not the retired number");
    }
  }

  // --- AN ABSENT SNAPSHOT IS "NO PHOSPHOR", NOT AN INVENTED ONE -----------
  //
  // Every install predating the key reads 0 there, and 0 is kPresetCustom. That
  // has to mean the historical answer -- a plain Custom slot has never glowed.
  {
    panelsource::Store s{};
    s.preset = panelpalette::kPresetCustom;
    checkInt(panelsource::glowPreset(s), panelpalette::kPresetCustom,
             "a Custom slot with no snapshot and no mix names no phosphor");
    checkInt(int(panelpalette::trailMsForPreset(panelsource::glowPreset(s))), 0,
             "...and therefore does not glow");
  }

  // --- PER-FIELD FALLBACK SURVIVES THE INDIRECTION ------------------------
  //
  // panelpalette::resolve substitutes ink and paper independently, so one
  // unparseable field cannot blank the page. Re-asserted through panelFor
  // because that is now the only way anyone reaches it.
  {
    panelsource::Store s{};
    s.preset = panelpalette::kPresetCustom;
    s.customInk[0] = 0x323D47;
    s.customPaper[0] = panelpalette::kInvalidColor;
    checkRgb(panelsource::panelFor(s, false).ink, 0x32, 0x3D, 0x47,
             "a valid ink survives an unparseable paper");
    checkRgb(panelsource::panelFor(s, false).paper,
             panelpalette::kDefaultLight.paper[0],
             panelpalette::kDefaultLight.paper[1],
             panelpalette::kDefaultLight.paper[2],
             "...and the paper falls back on its own");
  }

  // --- THE PAD'S TWO LEVELS, ONE ANSWER -----------------------------------
  //
  // Second bug found the same day: the Accessible pin lived at one of two
  // resolution points, so the SDL pad and SHOW chip drew -4/-5 while the UIKit
  // HIDE chip drew the stored Current levels (-1/-1). Both call
  // padpalette::shippedLevels now.
  {
    for (int outline = -9; outline <= 9; outline++) {
      for (int fill = -9; fill <= 9; fill++) {
        const padpalette::Levels l =
            padpalette::shippedLevels(false, outline, fill);
        const padpalette::Levels d =
            padpalette::shippedLevels(true, outline, fill);
        if (l.outline != -4 || l.fill != -5 || d.outline != 4 || d.fill != 5) {
          std::printf("FAIL the pad is not pinned at outline %d fill %d\n",
                      outline, fill);
          failures++;
          outline = 10;
          break;
        }
      }
    }
    // The pad's FIELD is the panel's paper, so a chosen ink's paper reaches the
    // pad. That seam is what makes one resolver matter.
    panelsource::Store s{};
    s.preset = panelpalette::kPresetCustom;
    s.customInk[0] = 0x323D47;
    s.customPaper[0] = 0xEEDFCC;  // Sepia Toned stock
    const padpalette::Levels lv = padpalette::shippedLevels(false, 0, 0);
    const padpalette::Palette pad = padpalette::makePaletteOn(
        false, lv.outline, lv.fill, panelsource::panelFor(s, false).paper);
    checkRgb(pad.field, 0xEE, 0xDF, 0xCC,
             "the pad's field is the page's paper, byte for byte");
  }

  if (failures) {
    std::printf("%d failure(s)\n", failures);
    return 1;
  }
  std::printf("panel source: light and dark each have exactly one owner\n");
  return 0;
}
