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
  // and the P7 cascade (25) closed the family out. Nine walks, nine catches,
  // zero shipped collisions; whoever appends the next preset moves it again.
  const int roads[] = {kPresetDefault, 26, -1, 999};
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

  // Every OFFERED preset, and only those -- a retired number resolves to
  // Default, so leaving one here reports "identical to Default" and hides what
  // the check is for.
  const int all[] = {kPresetDefault,     kPresetHighContrast, kPresetSepia,
                     kPresetReadingCool, kPresetSolarized,    kPresetGreenCrt,
                     kPresetAmberCrt,    kPresetNord,         kPresetGruvboxLight,
                     kPresetLatte,       kPresetRedCrt,       kPresetGrayCrt,
                     kPresetReadingWarm, kPresetReading,      kPresetBlueCrt,
                     kPresetGreenLongCrt, kPresetGreenFastCrt, kPresetWhiteCrt,
                     kPresetBlueFastCrt,  kPresetRedProjCrt,   kPresetBlueTvCrt,
                     kPresetCascadeCrt};
  for (size_t i = 0; i < sizeof(all) / sizeof(all[0]); i++)
    for (size_t j = i + 1; j < sizeof(all) / sizeof(all[0]); j++)
      for (int d = 0; d < 2; d++) {
        const Palette a = presetPalette(all[i], d != 0);
        const Palette b = presetPalette(all[j], d != 0);
        CHECKM(pack(a.ink) != pack(b.ink) || pack(a.paper) != pack(b.paper),
               "presets %d and %d paint identically (dark=%d)", all[i], all[j],
               d);
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

  // The preset row.
  const size_t key = xml.find("<string>panelPalettePreset</string>");
  CHECKM(key != std::string::npos,
         "panelPalettePreset: no specifier in Root.plist");
  if (key == std::string::npos) return;
  const size_t specStart = xml.rfind("<dict>", key);
  const size_t specEnd = xml.find("</dict>", key);

  const std::vector<std::string> titles =
      arrayAfter(xml, specStart, specEnd, "Titles");
  const std::vector<std::string> values =
      arrayAfter(xml, specStart, specEnd, "Values");
  CHECKM(titles.size() == values.size() && !values.empty(),
         "panelPalettePreset: %zu titles vs %zu values", titles.size(),
         values.size());
  if (titles.size() != values.size()) return;

  bool sawCustom = false;
  for (size_t i = 0; i < values.size(); i++) {
    const int preset = std::atoi(values[i].c_str());
    CHECKM(isKnownPreset(preset), "Root.plist offers unknown preset %d", preset);
    if (preset == kPresetCustom) {
      sawCustom = true;
      continue;
    }
    // If the row prints a ratio, it must be the ratio the tones measure. A
    // label that lies is worse than no label: it is the only information the
    // owner has about a choice they cannot preview.
    const size_t colon = titles[i].find(":1");
    if (colon == std::string::npos) continue;
    size_t start = colon;
    while (start > 0 && (isdigit(titles[i][start - 1]) ||
                         titles[i][start - 1] == '.'))
      start--;
    const double claimed = std::atof(titles[i].substr(start, colon - start).c_str());
    const double light = contrast(presetPalette(preset, false));
    const double dark = contrast(presetPalette(preset, true));
    // The row prints ONE number for a preset that has two halves, so it is
    // allowed to match either -- but it must match one of them to a rounding
    // step, not sit between them decoratively.
    CHECKM(std::fabs(claimed - light) < 0.06 || std::fabs(claimed - dark) < 0.06,
           "Root.plist row \"%s\" claims %.2f:1; preset %d measures %.2f:1 "
           "light / %.2f:1 dark",
           titles[i].c_str(), claimed, preset, light, dark);
  }
  CHECK(sawCustom);

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
  for (size_t i = 0; i < values.size(); i++) {
    const int offered = std::atoi(values[i].c_str());
    CHECKM(offered != kPresetSepiaCrt,
           "Root.plist still offers the retired preset 14");
    CHECKM(offered != kPresetSoft && offered != kPresetCoolGray,
           "Root.plist still offers a replaced preset (%d)", offered);
  }

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

  // THE CYCLE ORDER IS THE SETTINGS ORDER. The page-color button beside POWER
  // steps through panelpalette::kPresetInfo, and the owner asked for it to cycle
  // "in the order that they appear in page colors setting" -- which is this
  // Root.plist row order. Two hand-kept lists of fifteen rows, so they are
  // checked against each other rather than trusted: a mismatch is not an error
  // anywhere, it just means the button skips around the list.
  {
    std::vector<int> plistOrder;
    for (size_t i = 0; i < values.size(); i++) {
      const int preset = std::atoi(values[i].c_str());
      if (preset != kPresetCustom) plistOrder.push_back(preset);
    }
    CHECKM(plistOrder.size() == static_cast<size_t>(kPresetInfoCount),
           "Root.plist offers %zu presets, kPresetInfo has %d -- the button's "
           "cycle and the Settings list disagree on WHICH presets exist",
           plistOrder.size(), kPresetInfoCount);
    const size_t n = plistOrder.size() < static_cast<size_t>(kPresetInfoCount)
                         ? plistOrder.size()
                         : static_cast<size_t>(kPresetInfoCount);
    for (size_t i = 0; i < n; i++) {
      CHECKM(plistOrder[i] == kPresetInfo[i].preset,
             "row %zu: Root.plist has preset %d, kPresetInfo has %d (%s . %s) "
             "-- the button would cycle out of the order the setting shows",
             i, plistOrder[i], kPresetInfo[i].preset, kPresetInfo[i].family,
             kPresetInfo[i].name);
    }
  }

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

  // DefaultValue must be Default. This is the row that decides whether an
  // untouched install is pixel-identical, and it is one character wide.
  const size_t dv = xml.find("<key>DefaultValue</key>", specStart);
  CHECKM(dv != std::string::npos && dv < specEnd,
         "panelPalettePreset has no DefaultValue");
  if (dv != std::string::npos && dv < specEnd) {
    const size_t open = xml.find("<integer>", dv);
    const size_t close = xml.find("</integer>", open);
    CHECKM(std::atoi(xml.substr(open + 9, close - open - 9).c_str()) ==
               kPresetDefault,
           "panelPalettePreset DefaultValue must be %d (Default)",
           kPresetDefault);
  }

  // The four Custom fields, and their seeded defaults. A seed that does not
  // parse, or that is not the shipped tone, means the owner's first visit to
  // Custom silently changes the page.
  struct Field {
    const char *key;
    uint32_t want;
  };
  const Field fields[] = {{"panelInkLight", pack(kDefaultLight.ink)},
                          {"panelPaperLight", pack(kDefaultLight.paper)},
                          {"panelInkDark", pack(kDefaultDark.ink)},
                          {"panelPaperDark", pack(kDefaultDark.paper)}};
  for (const Field &f : fields) {
    const std::string needle = std::string("<string>") + f.key + "</string>";
    const size_t at = xml.find(needle);
    CHECKM(at != std::string::npos, "%s: no specifier in Root.plist", f.key);
    if (at == std::string::npos) continue;
    const size_t start = xml.rfind("<dict>", at);
    const size_t end = xml.find("</dict>", at);
    const size_t d = xml.find("<key>DefaultValue</key>", start);
    CHECKM(d != std::string::npos && d < end, "%s has no DefaultValue", f.key);
    if (d == std::string::npos || d >= end) continue;
    const size_t open = xml.find("<string>", d);
    const size_t close = xml.find("</string>", open);
    const std::string seeded = xml.substr(open + 8, close - open - 8);
    CHECKM(static_cast<uint32_t>(parseHexRgb(seeded.c_str())) == f.want,
           "%s is seeded \"%s\"; expected %06X", f.key, seeded.c_str(), f.want);
    // The field must be a text field: no other specifier type can carry a hex
    // color, and a PSMultiValueSpecifier here would silently store an index.
    CHECKM(xml.find("PSTextFieldSpecifier", start) < end,
           "%s must be a PSTextFieldSpecifier", f.key);
  }
}

int main(int argc, char **argv) {
  testDefaultsAreTheShippedTones();
  testRamp();
  testHexParsing();
  testCustomFallsBackPerField();
  testPresetsAreLegible();
  testRootPlist(argc > 1 ? argv[1] : "ios/Settings.bundle/Root.plist");

  if (failures) {
    std::printf("\n%d failure(s)\n", failures);
    return 1;
  }
  std::printf("panel_palette: all checks passed\n");
  return 0;
}
