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

int main() {
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
