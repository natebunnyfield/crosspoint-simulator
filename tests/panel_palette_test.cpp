// Unit tests for PanelPalette: the page's ink and paper, its presets, and the
// hex parsing behind the Custom fields.
//
// WHY THIS EXISTS AT ALL. Every failure mode in that header is a wrong COLOR,
// and a wrong color is invisible to a compiler, to the linker, and to every
// other test in this repo. The three that would actually hurt:
//
//   1. The default pair drifts. Then every install that never opened the
//      setting renders differently, silently, with nothing in any log to say so.
//      The whole promise of the feature is that it changes nothing until asked.
//   2. The interpolation changes shape. The panel's intermediate 2-bit grays are
//      MIXED from the two ends, so a rewrite in floating point (or one rounding
//      instead of truncating) moves every gray on the page by a level while both
//      endpoints still look exactly right.
//   3. A bad hex field resolves to something instead of falling back. "Ink and
//      paper both black" is a blank page with no error, reachable from one
//      mistyped character in Settings.app.
//
// THE sRGB MATH IS IN THE TEST, NOT IN THE APP, exactly as in
// pad_palette_test.cpp: the presets claim measured contrast ratios in their
// Settings.app row labels, and the only place that arithmetic is checked is a
// process with no frame budget. The plist labels are read from the shipped file
// so a preset and its printed ratio cannot drift apart.
//
// Build + run (no framework, no CMake):
//   c++ -std=c++17 -Isrc tests/panel_palette_test.cpp -o /tmp/panel_palette_test \
//     && /tmp/panel_palette_test ios/Settings.bundle/Root.plist

#include "PanelPalette.h"

#include <cctype>
#include <cstring>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

static int failures = 0;
#define CHECK(cond)                                                            \
  do {                                                                         \
    if (!(cond)) {                                                             \
      std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);              \
      failures++;                                                              \
    }                                                                          \
  } while (0)

#define CHECKM(cond, ...)                                                      \
  do {                                                                         \
    if (!(cond)) {                                                             \
      std::printf("FAIL %s:%d: ", __FILE__, __LINE__);                         \
      std::printf(__VA_ARGS__);                                                \
      std::printf("\n");                                                       \
      failures++;                                                              \
    }                                                                          \
  } while (0)

using namespace panelpalette;

// --- sRGB contrast, recomputed independently of the app --------------------

static double srgbLinear(int c) {
  const double v = c / 255.0;
  return v <= 0.04045 ? v / 12.92 : std::pow((v + 0.055) / 1.055, 2.4);
}

static double luminance(const uint8_t (&rgb)[3]) {
  return 0.2126 * srgbLinear(rgb[0]) + 0.7152 * srgbLinear(rgb[1]) +
         0.0722 * srgbLinear(rgb[2]);
}

static double contrast(const Palette &p) {
  const double a = luminance(p.ink);
  const double b = luminance(p.paper);
  const double hi = a > b ? a : b;
  const double lo = a > b ? b : a;
  return (hi + 0.05) / (lo + 0.05);
}

// --- 1. The shipped tones, byte for byte -----------------------------------
//
// These are the numbers HalDisplay.cpp hardcoded before the dial existed. They
// are spelled out as literals here rather than compared against the constants,
// because comparing a constant to itself proves nothing about drift.

static void testDefaultsAreTheShippedTones() {
  CHECK(kDefaultLight.ink[0] == 0x2D && kDefaultLight.ink[1] == 0x2D &&
        kDefaultLight.ink[2] == 0x2D);
  CHECK(kDefaultLight.paper[0] == 0xFB && kDefaultLight.paper[1] == 0xFB &&
        kDefaultLight.paper[2] == 0xF9);
  CHECK(kDefaultDark.ink[0] == 0xE0 && kDefaultDark.ink[1] == 0xE0 &&
        kDefaultDark.ink[2] == 0xDE);
  CHECK(kDefaultDark.paper[0] == 0x12 && kDefaultDark.paper[1] == 0x12 &&
        kDefaultDark.paper[2] == 0x12);

  // ...and every road that does not involve the owner typing something must
  // arrive at exactly them. This is the "nothing changes for someone who never
  // opens the setting" promise, enumerated.
  // The sentinels must be values no preset has TAKEN. 7 sat here until
  // 2026-08-15, when Amber CRT was appended and claimed it -- the test failed
  // loudly, which is the frozen-enum hazard working as intended. Anything
  // chosen here has to stay ahead of the enum. It moved 7 -> 11 then, and
  // 11 -> 13 on 2026-08-16 when Red CRT (11) and Gray CRT (12) were appended,
  // then 13 -> 14 the same day when Soft (13) was appended, then 14 -> 16 the
  // same day again when Sepia CRT (14) and Blue CRT (15) were appended, then
  // 16 -> 17 on 2026-08-17 when Reading (16) was appended, then 17 -> 19 the
  // same day when Reading Warm (17) and Reading Cool (18) replaced Soft and
  // Cool Gray, then 19 -> 24 the same day again when the five remaining
  // phosphors (19-23) landed, then 24 -> 26 the same day AGAIN when P22B (24)
  // and the P7 cascade (25) closed the family out -- until the owner asked for
  // every remaining JEDEC phosphor and 26-55 landed in one go. TENTH walk, and
  // the biggest: whoever appends the next preset moves it again.
  const int roads[] = {kPresetDefault, 56, -1, 999};
  for (int preset : roads) {
    const Palette l = resolve(preset, false, kInvalidColor, kInvalidColor);
    const Palette d = resolve(preset, true, kInvalidColor, kInvalidColor);
    CHECKM(pack(l.ink) == pack(kDefaultLight.ink) &&
               pack(l.paper) == pack(kDefaultLight.paper),
           "preset %d (light) must resolve to the shipped tones", preset);
    CHECKM(pack(d.ink) == pack(kDefaultDark.ink) &&
               pack(d.paper) == pack(kDefaultDark.paper),
           "preset %d (dark) must resolve to the shipped tones", preset);
  }

  // Custom with nothing typed is the same road. A first launch after an upgrade
  // that somehow lands on Custom must not blank the page.
  const Palette c = resolve(kPresetCustom, false, kInvalidColor, kInvalidColor);
  CHECK(pack(c.ink) == pack(kDefaultLight.ink));
  CHECK(pack(c.paper) == pack(kDefaultLight.paper));
}

// --- 2. The ramp -----------------------------------------------------------
//
// The interpolation IS the 2-bit gray handling: the panel's intermediate levels
// are mixed from the two ends, so this is what proves a custom palette still
// produces a graded page rather than two colors and nothing between.

static void testRamp() {
  // The ends are the palette, exactly, for every preset and both appearances.
  const int presets[] = {kPresetDefault, kPresetHighContrast, kPresetSepia,
                         kPresetCoolGray};
  for (int preset : presets) {
    for (int d = 0; d < 2; d++) {
      const Palette p = presetPalette(preset, d != 0);
      CHECKM(colorForLevel(0, p) == (0xFF000000u | pack(p.ink)),
             "preset %d dark=%d: level 0 must be the ink exactly", preset, d);
      CHECKM(colorForLevel(255, p) == (0xFF000000u | pack(p.paper)),
             "preset %d dark=%d: level 255 must be the paper exactly", preset,
             d);
    }
  }

  // MONOTONIC AND NON-DEGENERATE on the default light pair: 256 levels must not
  // collapse into two. A lerp written with the multiply and the divide the wrong
  // way round passes both endpoint checks above and fails here.
  int distinct = 1;
  uint32_t prev = colorForLevel(0, kDefaultLight);
  for (int level = 1; level <= 255; level++) {
    const uint32_t here = colorForLevel(static_cast<uint8_t>(level),
                                        kDefaultLight);
    CHECKM(((here >> 16) & 0xFF) >= ((prev >> 16) & 0xFF),
           "light ramp went backwards at level %d", level);
    if (here != prev) distinct++;
    prev = here;
  }
  CHECKM(distinct > 200, "the default light ramp collapsed to %d tones",
         distinct);

  // The dark pair runs the OTHER way, and that is the whole inversion mechanism
  // -- there is no separate 255-level flip anywhere in HalDisplay.
  CHECK(((colorForLevel(0, kDefaultDark) >> 16) & 0xFF) >
        ((colorForLevel(255, kDefaultDark) >> 16) & 0xFF));

  // TRUNCATING INTEGER DIVISION, pinned on a value where rounding differs.
  // ink 0x2D=45, paper 0xF9=249: 45 + 204*128/255 = 147.4 -> 147, not 148.
  CHECKM(colorForLevel(128, kDefaultLight) == 0xFF949493u,
         "midpoint gray is %06X, expected 949493 -- the arithmetic changed "
         "shape and every gray on the page moved with it",
         colorForLevel(128, kDefaultLight) & 0xFFFFFF);

  // A custom pair grades too. Sanity against the one implementation mistake
  // that would make the feature look like it works: taking the ink for level 0
  // and the paper for everything else.
  const Palette custom = resolve(kPresetCustom, false, 0x102030, 0xE0D0C0);
  CHECK(colorForLevel(0, custom) == 0xFF102030u);
  CHECK(colorForLevel(255, custom) == 0xFFE0D0C0u);
  CHECK(colorForLevel(128, custom) != 0xFF102030u);
  CHECK(colorForLevel(128, custom) != 0xFFE0D0C0u);
}

// --- 3. Custom, and every way a field can be wrong -------------------------

static void testHexParsing() {
  CHECK(parseHexRgb("2D2D2D") == 0x2D2D2D);
  CHECK(parseHexRgb("#2d2d2d") == 0x2D2D2D);
  CHECK(parseHexRgb("0X2D2D2D") == 0x2D2D2D);
  CHECK(parseHexRgb("\t 2D2D2D \n") == 0x2D2D2D);
  CHECK(parseHexRgb("000000") == 0x000000);
  CHECK(parseHexRgb("ffffff") == 0xFFFFFF);

  // Everything a Settings.app text field can actually hold when it is wrong.
  const char *junk[] = {"",     " ",       "#",       "2D2D2",  "2D2D2D2",
                        "GGGGGG", "#GGGGGG", "2D 2D 2D", "red",  "0x2D2D2",
                        "#2D2D2D#", "2D2D2D;"};
  for (const char *s : junk)
    CHECKM(parseHexRgb(s) == kInvalidColor, "\"%s\" must not parse", s);
  CHECK(parseHexRgb(nullptr) == kInvalidColor);
}

static void testCustomFallsBackPerField() {
  // ONE TYPO COSTS ONE COLOR, NOT THE PAGE. This is the behavior the Settings
  // footer promises, so it is pinned rather than left to the reader of resolve().
  const Palette inkOnly = resolve(kPresetCustom, false, 0x112233, kInvalidColor);
  CHECK(pack(inkOnly.ink) == 0x112233u);
  CHECKM(pack(inkOnly.paper) == pack(kDefaultLight.paper),
         "an unparseable paper must fall back to the default paper alone");

  const Palette paperOnly =
      resolve(kPresetCustom, true, kInvalidColor, 0x445566);
  CHECK(pack(paperOnly.paper) == 0x445566u);
  CHECK(pack(paperOnly.ink) == pack(kDefaultDark.ink));

  // The custom fields are IGNORED under a named preset -- that is what makes
  // switching to a preset and back non-destructive.
  const Palette named = resolve(kPresetSepia, false, 0x000000, 0x000000);
  CHECK(pack(named.ink) == pack(presetPalette(kPresetSepia, false).ink));
  CHECK(pack(named.paper) == pack(presetPalette(kPresetSepia, false).paper));
}

// --- 4. The presets, and the ratios their Settings rows print --------------

static void testPresetsAreLegible() {
  struct Row {
    int preset;
    const char *name;
  };
  const Row rows[] = {{kPresetDefault, "Default"},
                      {kPresetHighContrast, "High Contrast"},
                      {kPresetSepia, "Sepia"},
                      {kPresetReadingWarm, "Reading Warm"},
                      {kPresetSolarized, "Solarized"},
                      {kPresetGreenCrt, "Green CRT"},
                      {kPresetAmberCrt, "Amber CRT"},
                      {kPresetNord, "Nord"},
                      {kPresetGruvboxLight, "Gruvbox Light"},
                      {kPresetLatte, "Latte"},
                      {kPresetRedCrt, "Red CRT"},
                      {kPresetGrayCrt, "Gray CRT"},
                      {kPresetReadingCool, "Reading Cool"},
                      {kPresetReading, "Reading"},
                      {kPresetBlueCrt, "Blue CRT"}};
  for (const Row &r : rows) {
    for (int d = 0; d < 2; d++) {
      const Palette p = presetPalette(r.preset, d != 0);
      const double ratio = contrast(p);
      // 7:1 is WCAG AAA for body text. A NAMED preset is a curated choice and
      // has no business landing under it; the Custom fields deliberately have
      // no such floor, because typing a color is an explicit act.
      // Solarized is exempt BY NAME rather than by relaxing the floor: its low
      // contrast is the palette's thesis, and raising it would make it a
      // different palette. Everything else still has to clear 7:1, and the
      // exemption list is itself asserted below so a new row cannot join it by
      // accident.
      if (isLowContrastByDesign(r.preset)) {
        CHECKM(ratio >= 4.0,
               "%s (dark=%d) measures %.2f:1 -- exempt from the 7:1 floor, but "
               "still has to be readable",
               r.name, d, ratio);
      } else {
        CHECKM(ratio >= 7.0,
               "%s (dark=%d) measures %.2f:1, under the 7:1 floor "
               "a named preset must clear",
               r.name, d, ratio);
      }
      // A preset whose ink and paper are the same is a blank page.
      CHECKM(pack(p.ink) != pack(p.paper), "%s (dark=%d) has ink == paper",
             r.name, d);
    }
    // Light and dark halves must be opposite polarities, or "dark mode" hands
    // back a light page.
    CHECKM(luminance(presetPalette(r.preset, false).paper) >
               luminance(presetPalette(r.preset, false).ink),
           "%s light must be dark-on-light", r.name);
    CHECKM(luminance(presetPalette(r.preset, true).paper) <
               luminance(presetPalette(r.preset, true).ink),
           "%s dark must be light-on-dark", r.name);
  }

  // No two presets may paint the same page: a row that duplicates another is a
  // control that appears to do nothing.
  // Exactly one preset may be exempt. If a second ever is, that is a ruling and
  // it has to be made deliberately, not absorbed into a palette commit.
  {
    int exempt = 0;
    for (const Row &r : rows)
      if (isLowContrastByDesign(r.preset)) exempt++;
    CHECKM(exempt == 1, "%d presets claim the low-contrast exemption; only Solarized may", exempt);
    CHECKM(isLowContrastByDesign(kPresetSolarized), "Solarized lost its exemption");
  }

  // TWO ROWS MAY PAINT THE SAME PAGE, IF THEY DECAY DIFFERENTLY.
  //
  // This check used to be absolute -- no two presets may render identical tones
  // -- and it was right when colour was all a row had. The owner overturned it
  // on 2026-08-17 ("be sure to include all possible phosphors", after being
  // told they were near-duplicates), and the reason it is now safe is the glow:
  // P19, P26, P33 and P38 are all fluoride:Mn at 590-595 nm and derive to
  // byte-identical tones, but their trails run 1095 ms, 1095 ms, 2828 ms and
  // 1095 ms. A row that paints the same page AND decays the same way is still a
  // control that appears to do nothing, and that is what this now forbids.
  //
  // Driven off kPresetInfo rather than a hand-written list, because the old
  // hand list silently stopped covering anything appended after it -- thirty
  // rows landed without this check ever looking at them.
  // Identical means identical in BOTH polarities. P13 (640 nm) and P27 (635 nm)
  // collapse to the same light page and stay one byte apart in the dark one;
  // that row still does something, so it is not a duplicate.
  //
  // The ONE genuinely identical pair is listed by name below. Anything else
  // that collides has to be dealt with, not absorbed.
  auto isCataloguedTwin = [](const char *a, const char *b) {
    // P19 (KF,MgF2):Mn and P38 (Zn,Mg)F2:Mn are both published at 590 nm,
    // both "Orange-Yellow", both "Long". Different chemistry, no published
    // difference in EMISSION -- so deriving a difference would be inventing
    // one. They ship as twins because the owner asked for every phosphor in
    // the registry, and a catalogue that silently omits the second of an
    // identical pair is not the catalogue that was asked for.
    const bool p19p38 = (!std::strcmp(a, "P19") && !std::strcmp(b, "P38")) ||
                        (!std::strcmp(a, "P38") && !std::strcmp(b, "P19"));
    return p19p38;
  };
  for (int i = 0; i < kPresetInfoCount; i++) {
    for (int j = i + 1; j < kPresetInfoCount; j++) {
      const PresetInfo &a = kPresetInfo[i];
      const PresetInfo &b = kPresetInfo[j];
      bool sameBoth = true;
      for (int d = 0; d < 2 && sameBoth; d++) {
        const Palette pa = presetPalette(a.preset, d != 0);
        const Palette pb = presetPalette(b.preset, d != 0);
        sameBoth = pack(pa.ink) == pack(pb.ink) &&
                   pack(pa.paper) == pack(pb.paper);
      }
      if (!sameBoth) continue;
      // Two ordinary palettes with the same tones are a mistake however they
      // decay -- only a phosphor gets to be told apart by its trail.
      CHECKM(a.phosphor && b.phosphor,
             "%s and %s paint identically and are not both phosphors", a.name,
             b.name);
      if (!a.phosphor || !b.phosphor) continue;
      if (trailMsForPreset(a.preset) != trailMsForPreset(b.preset)) continue;
      CHECKM(isCataloguedTwin(a.phosphor, b.phosphor),
             "%s (%s) and %s (%s) paint identically AND decay identically -- "
             "one of them is a control that does nothing",
             a.name, a.phosphor, b.name, b.phosphor);
    }
  }
}

// --- 5. The shipped Root.plist ---------------------------------------------
//
// The only half no static_assert can do: the row LABELS in Settings.app claim
// contrast figures, and the Values array decides which preset a row selects.
// Both live in a plist the compiler never opens.

static std::string slurp(const char *path) {
  std::ifstream in(path);
  if (!in) return {};
  std::ostringstream ss;
  ss << in.rdbuf();
  return ss.str();
}

// Contents of <array>...</array> following `arrayKey`, within [from, to).
static std::vector<std::string> arrayAfter(const std::string &xml, size_t from,
                                           size_t to, const char *arrayKey) {
  std::vector<std::string> out;
  const std::string tag = std::string("<key>") + arrayKey + "</key>";
  const size_t k = xml.find(tag, from);
  if (k == std::string::npos || k >= to) return out;
  const size_t open = xml.find("<array>", k);
  const size_t close = xml.find("</array>", open);
  if (open == std::string::npos || close == std::string::npos) return out;
  size_t p = open;
  while (true) {
    const size_t s = xml.find('<', p + 1);
    if (s == std::string::npos || s >= close) break;
    const size_t e = xml.find('>', s);
    if (e == std::string::npos) break;
    const std::string tagName = xml.substr(s + 1, e - s - 1);
    if (tagName == "string" || tagName == "integer") {
      const size_t vEnd = xml.find('<', e);
      out.push_back(xml.substr(e + 1, vEnd - e - 1));
      p = vEnd;
    } else {
      p = e;
    }
  }
  return out;
}

static void testRootPlist(const char *path) {
  const std::string xml = slurp(path);
  if (xml.empty()) {
    std::printf("FAIL cannot read %s (run from the repo root)\n", path);
    failures++;
    return;
  }

  // THE PAGE-COLOR ROWS BELOW Zen Bottom Margin ARE OUT, DELIBERATELY (owner
  // order 2026-08-22: "remove all settings in app system settings below zen
  // bottom margin"). Every KEY keeps working — stored values, env overrides,
  // and the in-app chip/mixer still read and write them, and
  // CrossPointPrefs.mm registers the former defaults so an untouched install
  // renders identically — but Settings.app no longer offers the rows.
  // Asserted ABSENT so a future re-add is a conscious act, not a merge
  // accident. The pure phases above still pin every preset's tones, contrast,
  // migration and trail.
  const char *removedKeys[] = {
      "presentFlash",
      "phosphorGrainPercentLight",
      "phosphorGrainPercentDark",
      "phosphorGrainCoverage",
      "phosphorGrainMottleDepth",
      "panelPalettePreset",
      "panelInkLight",
      "panelPaperLight",
      "panelInkDark",
      "panelPaperDark",
  };
  for (const char *key : removedKeys)
    CHECKM(xml.find(std::string("<string>") + key + "</string>") ==
               std::string::npos,
           "%s: row is back in Root.plist (removed 2026-08-22)", key);

  // ...and the survivors are still there, so the absences above cannot be
  // satisfied by an empty or wrong file. The Page Colors group now ENDS at
  // Zen Bottom Margin; Read Aloud survives whole; the new Zen toggle sits at
  // the very top.
  const size_t zenToggle = xml.find("<string>zenModeEnabled</string>");
  CHECKM(zenToggle != std::string::npos,
         "zenModeEnabled (the Zen toggle) must be in Root.plist");
  CHECKM(xml.find("<string>zenBottomRatio</string>") != std::string::npos,
         "zenBottomRatio must stay in Root.plist");
  CHECKM(xml.find("<string>readAloudEnabled</string>") != std::string::npos,
         "the Read Aloud section must survive the removal");
  CHECKM(xml.find("<string>diagnosticsEnabled</string>") != std::string::npos,
         "diagnosticsEnabled sits inside Read Aloud and stays");
  CHECKM(zenToggle < xml.find("<string>allowSleepOnBattery</string>"),
         "the Zen toggle belongs at the very top of Settings");

  // A RETIRED preset must behave exactly like an unknown one, and must not come
  // back in the picker. 14 was Sepia CRT until 2026-08-17; the constant survives
  // only so the number is never handed to something else, because a preset
  // persists as its integer and an install that had chosen it would silently
  // start showing whatever took the number.
  CHECKM(!isKnownPreset(kPresetSepiaCrt),
         "preset 14 is retired and must not be known");
  {
    const Palette l = resolve(kPresetSepiaCrt, false, kInvalidColor, kInvalidColor);
    const Palette d = resolve(kPresetSepiaCrt, true, kInvalidColor, kInvalidColor);
    CHECKM(pack(l.ink) == pack(kDefaultLight.ink) &&
               pack(l.paper) == pack(kDefaultLight.paper) &&
               pack(d.ink) == pack(kDefaultDark.ink) &&
               pack(d.paper) == pack(kDefaultDark.paper),
           "a stored 14 must land on Default, the same as any unknown integer");
  }
  // (The "must not be offered in the picker" half of retirement is subsumed by
  // the row's absence, asserted above.)

  // REPLACED, not removed: a stored choice follows its replacement forward.
  // This is the half that separates the two kinds of retirement -- 14 was
  // deleted and lands on Default, while 4 and 13 were swapped for the cool and
  // warm Reading pages and must keep meaning "the cool one" / "the warm one".
  {
    struct { int stored; int expect; const char *what; } moved[] = {
        {kPresetSoft, kPresetReadingWarm, "Soft -> Reading Warm"},
        {kPresetCoolGray, kPresetReadingCool, "Cool Gray -> Reading Cool"},
    };
    for (const auto &m : moved) {
      CHECKM(!isKnownPreset(m.stored), "%s: the old number must not be offered",
             m.what);
      CHECKM(migratePreset(m.stored) == m.expect, "%s: migratePreset disagrees",
             m.what);
      for (int d = 0; d < 2; d++) {
        const Palette got = resolve(m.stored, d != 0, kInvalidColor, kInvalidColor);
        const Palette want = resolve(m.expect, d != 0, kInvalidColor, kInvalidColor);
        CHECKM(pack(got.ink) == pack(want.ink) &&
                   pack(got.paper) == pack(want.paper),
               "%s (dark=%d): a stored %d must resolve to %d", m.what, d,
               m.stored, m.expect);
      }
    }
    // And the deleted one must NOT be migrated anywhere.
    CHECKM(migratePreset(kPresetSepiaCrt) == kPresetSepiaCrt,
           "14 was deleted, not replaced -- it must not migrate");
  }

  // THE CYCLE ORDER used to be checked against this Root.plist row's order;
  // the row left Settings.app 2026-08-22, so panelpalette::kPresetInfo is now
  // the single definition of the cycle and there is no second list to drift
  // from. Its own invariants are still pinned below.

  // A CRT row without a usable decay is a phosphor that cannot glow, which is
  // the one thing the family is for. decayMs is allowed to come off the class
  // ladder, but it may not be zero.
  for (int i = 0; i < kPresetInfoCount; i++) {
    const PresetInfo &info = kPresetInfo[i];
    const bool isCrt = std::string(info.family) == "CRT";
    CHECKM(isCrt == (info.phosphor != nullptr),
           "%s . %s: the CRT family and having a phosphor must agree",
           info.family, info.name);
    if (!isCrt) continue;
    CHECKM(info.persistence != nullptr && info.decayMs > 0.0f,
           "%s (%s) has no usable decay -- it would not glow", info.name,
           info.phosphor);
    // Exactly one row is a cascade. If a second ever gains an afterglow this
    // does not fail -- but a NON-CRT row with one would mean the tint is being
    // pushed for a page that never glows.
    if (info.afterglow) {
      const Palette d = presetPalette(info.preset, true);
      const uint32_t glowPacked = (static_cast<uint32_t>(info.afterglow[0]) << 16) |
                                  (static_cast<uint32_t>(info.afterglow[1]) << 8) |
                                  static_cast<uint32_t>(info.afterglow[2]);
      CHECKM(glowPacked != pack(d.ink),
             "%s: an afterglow equal to the ink is not a cascade, it is a fade",
             info.name);
    }
  }

  // Every preset the cycle can reach must be a KNOWN one, or a press lands on a
  // stop that silently resolves to Default.
  for (int i = 0; i < kPresetInfoCount; i++) {
    CHECKM(isKnownPreset(kPresetInfo[i].preset) &&
               kPresetInfo[i].preset != kPresetCustom,
           "kPresetInfo[%d] is %d, which is not a nameable preset", i,
           kPresetInfo[i].preset);
    CHECKM(kPresetInfo[i].family && kPresetInfo[i].name && kPresetInfo[i].note,
           "kPresetInfo[%d] has a null string", i);
  }

  // The DefaultValue and Custom-field-seed checks left with their rows. The
  // shipped default itself (CRT White, with its registered fallback) is now
  // stated in CrossPointPrefs.mm's supplemental registerDefaults, not here.
}


// THE TRAIL ARITHMETIC. It lived in an iOS-only .cpp as a flat x20 multiplier
// and shipped a 20-SECOND trail for P7, which is why the cascade -- the one
// phosphor whose identity is its afterglow -- was reported dead from the phone
// against build 85. Nothing on a host could run that code, so nothing on a host
// could catch it. Now it can.
static void testTrailTiming() {
  using namespace panelpalette;

  // Not a phosphor, no trail: a page of e-ink does not decay.
  CHECKM(trailMsForPreset(kPresetDefault) == 0.0f, "default has no trail");
  CHECKM(trailMsForPreset(kPresetSepia) == 0.0f, "sepia has no trail");
  // Through the migration, so a retired preset does not silently lose its row.
  CHECKM(trailMsForPreset(kPresetSoft) == 0.0f, "retired Soft migrates, no trail");

  // The anchor is P1 and it is exactly where it always was.
  const float p1 = trailMsForPreset(kPresetGreenCrt);
  CHECKM(p1 > 399.0f && p1 < 401.0f, "P1 anchors at 400 ms");

  // EVERY phosphor lands in a band a person can actually see: long enough not
  // to be one frame, short enough that the page resolves. The upper bound is
  // the bug -- 20000 ms would fail here.
  float slowest = 0.0f;
  const char *slowestName = "none";
  for (int i = 0; i < kPresetInfoCount; i++) {
    const PresetInfo &info = kPresetInfo[i];
    const float t = trailMsForPreset(info.preset);
    if (!info.phosphor) {
      CHECKM(t == 0.0f, "non-phosphor row has no trail");
      continue;
    }
    CHECKM(t >= 15.0f, "a phosphor trail is at least a frame");
    CHECKM(t <= 3000.0f, "a phosphor trail resolves within 3 s");
    if (t > slowest) { slowest = t; slowestName = info.phosphor; }
  }

  // P7 is AMONG the slowest. It no longer has that alone: P33 (">1 sec") and
  // P34 ("Very Long") read the same rung of the ladder, which is the honest
  // answer -- the sources do not distinguish them further. What must stay true
  // is that the very-long class is clearly longer than "Long".
  CHECKM(trailMsForPreset(kPresetCascadeCrt) >= slowest - 0.5f,
         "P7 is no longer among the longest trails (%s is)", slowestName);
  const float p39 = trailMsForPreset(kPresetGreenLongCrt);
  CHECKM(slowest > p39 * 1.5f, "P7 is clearly longer than P39, not merely equal");

  // ORDER IS THE PART THAT SURVIVES COMPRESSION. The literal ratio does not,
  // deliberately; the ranking is the source's own and must not be reshuffled.
  CHECKM(trailMsForPreset(kPresetBlueFastCrt) <
            trailMsForPreset(kPresetBlueCrt),
        "P47 is faster than P11");
  CHECKM(trailMsForPreset(kPresetBlueCrt) < trailMsForPreset(kPresetGreenCrt),
        "P11 is faster than P1");
  CHECKM(trailMsForPreset(kPresetGreenCrt) <
            trailMsForPreset(kPresetGreenLongCrt),
        "P1 is faster than P39");

  // Monotone in the input, which is what lets the ladder's rungs mean anything.
  float prev = -1.0f;
  for (float d : {0.05f, 0.5f, 1.0f, 2.0f, 10.0f, 20.0f, 150.0f, 1000.0f}) {
    const float t = trailMsForDecay(d);
    CHECKM(t > prev, "trail is monotone in decay");
    prev = t;
  }

  // The cascade is the only row with an afterglow, and it must not be the ink
  // it is drawn in or the shift is invisible.
  // THREE cascades now: P7 (yellow-green tail), P14 (orange) and P17 (yellow).
  // Each must carry its OWN afterglow -- sharing one constant would make all
  // three decay to the same hue and erase the only thing that separates them,
  // which is exactly the mistake the first draft of these rows made.
  int withTail = 0;
  for (int i = 0; i < kPresetInfoCount; i++) {
    const PresetInfo &info = kPresetInfo[i];
    if (!info.afterglow) continue;
    withTail++;
    // pack() takes an array; PresetInfo::afterglow is a pointer, so these are
    // packed by hand rather than by silently decaying to something else.
    auto pack3 = [](const unsigned char *c) {
      return (static_cast<uint32_t>(c[0]) << 16) |
             (static_cast<uint32_t>(c[1]) << 8) | c[2];
    };
    const Palette dark = presetPalette(info.preset, true);
    CHECKM(pack3(info.afterglow) != pack(dark.ink),
           "%s decays toward the ink it is drawn in", info.name);
    CHECKM(pack3(info.afterglow) != pack(dark.paper),
           "%s decays toward its own paper", info.name);
    for (int j = 0; j < kPresetInfoCount; j++) {
      if (j == i || !kPresetInfo[j].afterglow) continue;
      CHECKM(pack3(info.afterglow) != pack3(kPresetInfo[j].afterglow),
             "%s and %s decay toward the same hue", info.name,
             kPresetInfo[j].name);
    }
  }
  CHECKM(withTail == 3, "expected three cascade rows, found %d", withTail);
}


// THE EMISSIVE RAMP. Reported from the phone against build 85: "the
// antialiasing on the sans serif fonts looks bad in crt". An AA edge pixel is a
// partly-covered pixel, and on a phosphor partial coverage is partial LIGHT --
// which adds linearly, while sRGB code values do not. Blending in code space
// crushes every edge pixel on a dark page.
//
// Untestable anywhere else: it is a wrong COLOR on an intermediate level, which
// no compiler sees and no screenshot comparison in this repo would flag.
static void testEmissiveRamp() {
  using namespace panelpalette;
  const Palette cascadeDark = presetPalette(kPresetCascadeCrt, true);

  // ENDPOINTS ARE EXACT. A palette's own two tones are what the owner picked
  // and must not move because the ramp between them changed shape.
  CHECKM(colorForLevelEmissive(0, cascadeDark) ==
             (0xFF000000u | pack(cascadeDark.ink)),
         "emissive level 0 is the ink exactly");
  CHECKM(colorForLevelEmissive(255, cascadeDark) ==
             (0xFF000000u | pack(cascadeDark.paper)),
         "emissive level 255 is the paper exactly");

  // THE FIX ITSELF: a half-covered pixel is brighter than the code-space lerp
  // put it. If this ever fails equal, the emissive path has quietly become the
  // reflective one and the fringe is back.
  const uint32_t flat = colorForLevel(128, cascadeDark);
  const uint32_t lit = colorForLevelEmissive(128, cascadeDark);
  const int flatG = (flat >> 8) & 0xFF;
  const int litG = (lit >> 8) & 0xFF;
  CHECKM(litG > flatG + 20,
         "emissive midpoint is materially brighter than the code-space lerp "
         "(%d vs %d)", litG, flatG);

  // Monotone -- a ramp that reverses anywhere puts a band inside a glyph edge,
  // which is a fringe of its own. DIRECTION comes from the palette: a dark
  // palette runs bright ink to dark paper, so its ramp descends, and asserting
  // "ascending" here is how this test first failed 154 times against correct
  // code.
  const int inkG = (colorForLevelEmissive(0, cascadeDark) >> 8) & 0xFF;
  const int paperG = (colorForLevelEmissive(255, cascadeDark) >> 8) & 0xFF;
  const bool ascending = paperG > inkG;
  int prev = inkG;
  for (int level = 1; level <= 255; level++) {
    const int g =
        (colorForLevelEmissive(static_cast<uint8_t>(level), cascadeDark) >> 8) &
        0xFF;
    CHECKM(ascending ? (g >= prev) : (g <= prev),
           "emissive ramp is monotone at level %d", level);
    prev = g;
  }
  CHECKM(inkG != paperG, "the emissive ramp is not degenerate");

  // THE REFLECTIVE PATH IS UNTOUCHED. Every e-ink palette must render the exact
  // pixels it always did; this is the guard on that promise.
  CHECKM(colorForLevel(128, kDefaultLight) == 0xFF949493u,
         "the default palette's midpoint is unchanged by the emissive work");
}

int main(int argc, char **argv) {
  testDefaultsAreTheShippedTones();
  testRamp();
  testHexParsing();
  testCustomFallsBackPerField();
  testPresetsAreLegible();
  testTrailTiming();
  testEmissiveRamp();
  testRootPlist(argc > 1 ? argv[1] : "ios/Settings.bundle/Root.plist");

  if (failures) {
    std::printf("\n%d failure(s)\n", failures);
    return 1;
  }
  std::printf("panel_palette: all checks passed\n");
  return 0;
}
