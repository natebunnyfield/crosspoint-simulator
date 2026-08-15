// Unit tests for PadPalette: the button pad's contrast ladder and its presets.
//
// WHY THIS EXISTS AT ALL. Every failure mode in that header is SILENT. A rung
// that resolves to the field paints nothing; a preset that misses the shipped
// level changes the look of a pad nobody asked to change; and a Root.plist row
// labelled "3.01:1" whose tone measures 1.36:1 is a lie told to the one person
// the labels are for. None of the three produces an error, a log line, or a
// crash — the app builds clean and looks plausible. So the ladder is checked
// here, on a host, including against the shipped plist.
//
// THE sRGB MATH IS IN THE TEST, NOT IN THE APP. Contrast ratios are recomputed
// from scratch here, per WCAG 2.x relative luminance, and compared with both the
// table and the label. That is the whole point of precomputing the tones: the
// phone never does this arithmetic, and the only place that checks it is a
// process with no frame budget.
//
// Build + run (no framework, no CMake):
//   c++ -std=c++17 -Iios tests/pad_palette_test.cpp -o /tmp/pad_palette_test \
//     && /tmp/pad_palette_test ios/Settings.bundle/Root.plist

#include "PadPalette.h"

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <map>
#include <set>
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

using namespace padpalette;

// --- sRGB contrast, recomputed independently of the app --------------------

static double srgbLinear(int c) {
  const double v = c / 255.0;
  return v <= 0.04045 ? v / 12.92 : std::pow((v + 0.055) / 1.055, 2.4);
}

static double luminance(const uint8_t rgb[3]) {
  return 0.2126 * srgbLinear(rgb[0]) + 0.7152 * srgbLinear(rgb[1]) +
         0.0722 * srgbLinear(rgb[2]);
}

static double contrastRatio(const uint8_t a[3], const uint8_t b[3]) {
  double la = luminance(a), lb = luminance(b);
  if (la < lb) std::swap(la, lb);
  return (la + 0.05) / (lb + 0.05);
}

struct Tone {
  uint8_t c[3];
};

static Tone toneAt(const uint8_t *field, const int16_t *table, int level) {
  Tone t{};
  for (int i = 0; i < 3; i++)
    t.c[i] = toneChannel(field[i], table[clampLevel(level) + kContrastOffset]);
  return t;
}

static std::string hex(const uint8_t c[3]) {
  char buf[8];
  std::snprintf(buf, sizeof(buf), "%02X%02X%02X", c[0], c[1], c[2]);
  return buf;
}

// --- The four ladders, named --------------------------------------------

struct Ladder {
  const char *key;       // Root.plist key
  const uint8_t *field;  // 3 channels
  const int16_t *table;
  bool dark;
  int defaultLevel;
  int accessibleLevel;
  int blackLevel;
  int whiteLevel;
};

static const Ladder kLadders[] = {
    {"padOutlineContrastLight", kLightPalette.field, kOutlineDeltaLight, false, -1,
     -4, -9, 9},
    {"padFillContrastLight", kLightPalette.field, kFillDeltaLight, false, -1, -5,
     -9, 9},
    {"padOutlineContrastDark", kDarkPalette.field, kOutlineDeltaDark, true, 1, 4,
     -9, 9},
    {"padFillContrastDark", kDarkPalette.field, kFillDeltaDark, true, 1, 5, -9, 9},
};

// --- A very small Root.plist reader ---------------------------------------
//
// Deliberately not plistlib/NSDictionary: this test has to run on Linux CI and
// on a Mac with no Xcode, and the file it reads is a flat, hand-maintained
// XML plist. It scans for the specifier dict with a given <key>Key</key> and
// pulls its parallel Titles/Values arrays back out.

struct Spec {
  bool found = false;
  long defaultValue = 0;
  std::vector<std::string> titles;
  std::vector<long> values;
};

static std::string slurp(const std::string &path) {
  std::ifstream in(path, std::ios::binary);
  std::ostringstream ss;
  ss << in.rdbuf();
  return ss.str();
}

// Pull the contents of <array> ... </array> following `arrayKey` inside [from,to).
static std::vector<std::string> readArray(const std::string &s, size_t from,
                                          size_t to, const char *arrayKey,
                                          const char *elemTag) {
  std::vector<std::string> out;
  const std::string keyTag = std::string("<key>") + arrayKey + "</key>";
  size_t k = s.find(keyTag, from);
  if (k == std::string::npos || k >= to) return out;
  size_t a = s.find("<array>", k);
  size_t z = s.find("</array>", a);
  if (a == std::string::npos || z == std::string::npos || z > to) return out;
  const std::string open = std::string("<") + elemTag + ">";
  const std::string close = std::string("</") + elemTag + ">";
  size_t p = a;
  while ((p = s.find(open, p)) != std::string::npos && p < z) {
    size_t e = s.find(close, p);
    if (e == std::string::npos || e > z) break;
    out.push_back(s.substr(p + open.size(), e - p - open.size()));
    p = e + close.size();
  }
  return out;
}

static Spec readSpec(const std::string &s, const char *key) {
  Spec spec;
  const std::string want = std::string("<string>") + key + "</string>";
  size_t k = s.find(want);
  if (k == std::string::npos) return spec;
  // The enclosing <dict> starts before k and ends at the next </dict>.
  size_t begin = s.rfind("<dict>", k);
  size_t end = s.find("</dict>", k);
  if (begin == std::string::npos || end == std::string::npos) return spec;
  spec.found = true;

  size_t d = s.find("<key>DefaultValue</key>", begin);
  if (d != std::string::npos && d < end) {
    size_t i = s.find("<integer>", d);
    size_t j = s.find("</integer>", i);
    if (i != std::string::npos && j != std::string::npos && j < end)
      spec.defaultValue = std::strtol(s.substr(i + 9, j - i - 9).c_str(), nullptr, 10);
  }
  spec.titles = readArray(s, begin, end, "Titles", "string");
  for (const std::string &v : readArray(s, begin, end, "Values", "integer"))
    spec.values.push_back(std::strtol(v.c_str(), nullptr, 10));
  return spec;
}

// The label format Root.plist uses: 3 decimals below 2:1, 2 decimals above,
// because two adjacent fine rungs round to the same string at 2 decimals and a
// settings row that cannot be told from the one above it is the defect this
// whole ladder is arranged to avoid.
static std::string formatRatio(double r) {
  char buf[32];
  std::snprintf(buf, sizeof(buf), r < 2.0 ? "%.3f:1" : "%.2f:1", r);
  return buf;
}

int main(int argc, char **argv) {
  const std::string plistPath =
      argc > 1 ? argv[1] : "ios/Settings.bundle/Root.plist";

  // --- 1. Current is the shipped look, exactly ----------------------------
  //
  // THE COMPATIBILITY GUARANTEE. If this fails, an untouched install no longer
  // paints what it painted before presets existed.
  {
    const Levels light = presetLevels(kPresetCurrent, false);
    const Levels dark = presetLevels(kPresetCurrent, true);
    const Palette pl = makePalette(false, light.outline, light.fill);
    const Palette pd = makePalette(true, dark.outline, dark.fill);
    CHECK(std::memcmp(pl.hairline, kLightPalette.hairline, 3) == 0);
    CHECK(std::memcmp(pl.faceDown, kLightPalette.faceDown, 3) == 0);
    CHECK(std::memcmp(pl.field, kLightPalette.field, 3) == 0);
    CHECK(std::memcmp(pl.face, kLightPalette.field, 3) == 0);  // hollow
    CHECK(std::memcmp(pd.hairline, kDarkPalette.hairline, 3) == 0);
    CHECK(std::memcmp(pd.faceDown, kDarkPalette.faceDown, 3) == 0);
    CHECK(std::memcmp(pd.field, kDarkPalette.field, 3) == 0);
    CHECK(std::memcmp(pd.face, kDarkPalette.field, 3) == 0);
    // Spelled out, so a table edit that keeps the asserts happy but moves these
    // still fails here.
    CHECKM(hex(pl.hairline) == "D9D9D7", "light stroke %s", hex(pl.hairline).c_str());
    CHECKM(hex(pl.faceDown) == "EDEDEB", "light wash %s", hex(pl.faceDown).c_str());
    CHECKM(hex(pd.hairline) == "333333", "dark stroke %s", hex(pd.hairline).c_str());
    CHECKM(hex(pd.faceDown) == "202020", "dark wash %s", hex(pd.faceDown).c_str());
  }

  // --- 2. Transparent draws nothing ---------------------------------------
  for (bool dark : {false, true}) {
    const Levels lv = presetLevels(kPresetTransparent, dark);
    CHECK(lv.outline == 0 && lv.fill == 0);
    const Palette p = makePalette(dark, lv.outline, lv.fill);
    CHECKM(std::memcmp(p.hairline, p.field, 3) == 0, "transparent stroke %s != field",
           hex(p.hairline).c_str());
    CHECKM(std::memcmp(p.faceDown, p.field, 3) == 0, "transparent wash %s != field",
           hex(p.faceDown).c_str());
    CHECK(std::memcmp(p.face, p.field, 3) == 0);
  }

  // --- 3. Accessible really is 3:1 ----------------------------------------
  //
  // Measured, not asserted from a table index: the whole claim of the row is a
  // number, so the number is what gets checked.
  for (bool dark : {false, true}) {
    const Levels lv = presetLevels(kPresetAccessible, dark);
    const Palette p = makePalette(dark, lv.outline, lv.fill);
    const double stroke = contrastRatio(p.hairline, p.field);
    const double wash = contrastRatio(p.faceDown, p.field);
    CHECKM(stroke >= 3.0 && stroke < 3.1, "%s accessible stroke %s is %.3f:1",
           dark ? "dark" : "light", hex(p.hairline).c_str(), stroke);
    CHECKM(wash >= 3.0 && wash < 3.1, "%s accessible wash %s is %.3f:1",
           dark ? "dark" : "light", hex(p.faceDown).c_str(), wash);
  }

  // --- 4. Full gamut, both ends, both appearances, both roles --------------
  for (const Ladder &L : kLadders) {
    const Tone black = toneAt(L.field,
                              L.table, L.blackLevel);
    const Tone white = toneAt(L.field,
                              L.table, L.whiteLevel);
    CHECKM(black.c[0] == 0 && black.c[1] == 0 && black.c[2] == 0,
           "%s level %+d is %s, not #000000", L.key, L.blackLevel,
           hex(black.c).c_str());
    CHECKM(white.c[0] == 255 && white.c[1] == 255 && white.c[2] == 255,
           "%s level %+d is %s, not #FFFFFF", L.key, L.whiteLevel,
           hex(white.c).c_str());
  }

  // --- 5. No dead zone: every rung of a ladder paints its own pixels -------
  for (const Ladder &L : kLadders) {
    std::map<std::string, int> seen;
    for (int lvl = kContrastMin; lvl <= kContrastMax; lvl++) {
      const Tone t =
          toneAt(L.field, L.table, lvl);
      const std::string h = hex(t.c);
      auto it = seen.find(h);
      CHECKM(it == seen.end(), "%s: levels %+d and %+d both paint %s", L.key,
             it == seen.end() ? 0 : it->second, lvl, h.c_str());
      seen[h] = lvl;
    }
  }

  // --- 6. Unknown preset resolves to Current, never to invisible ----------
  for (int bogus : {-5, 4, 99, 1000}) {
    for (bool dark : {false, true}) {
      const Levels lv = resolveLevels(bogus, dark, 7, 7);
      const Levels cur = presetLevels(kPresetCurrent, dark);
      CHECKM(lv.outline == cur.outline && lv.fill == cur.fill,
             "preset %d resolved to %+d/%+d", bogus, lv.outline, lv.fill);
    }
  }

  // --- 7. Custom, and only Custom, reads the fine pickers ------------------
  {
    CHECK(resolveLevels(kPresetCustom, false, -6, -3).outline == -6);
    CHECK(resolveLevels(kPresetCustom, false, -6, -3).fill == -3);
    CHECK(resolveLevels(kPresetCustom, true, 5, 8).outline == 5);
    CHECK(resolveLevels(kPresetCustom, true, 5, 8).fill == 8);
    // Out-of-range prefs are clamped, not indexed with.
    CHECK(resolveLevels(kPresetCustom, false, -400, 400).outline == kContrastMin);
    CHECK(resolveLevels(kPresetCustom, false, -400, 400).fill == kContrastMax);
    // A preset ignores them entirely.
    CHECK(resolveLevels(kPresetTransparent, false, -9, -9).outline == 0);
    CHECK(resolveLevels(kPresetAccessible, true, 0, 0).outline == 4);
  }

  // --- 8. Root.plist agrees with the tables, row by row --------------------
  //
  // The labels are the product here — an honestly-labelled control is the whole
  // design — so each one is recomputed from the tone its own Value selects.
  {
    const std::string plist = slurp(plistPath);
    CHECKM(!plist.empty(), "could not read %s (pass the path as argv[1])",
           plistPath.c_str());
    if (!plist.empty()) {
      for (const Ladder &L : kLadders) {
        const Spec spec = readSpec(plist, L.key);
        CHECKM(spec.found, "%s: no specifier in Root.plist", L.key);
        if (!spec.found) continue;
        CHECKM(spec.titles.size() == spec.values.size(),
               "%s: %zu titles vs %zu values", L.key, spec.titles.size(),
               spec.values.size());
        CHECKM(spec.values.size() == (size_t)kContrastLevels,
               "%s: %zu rows, expected %d", L.key, spec.values.size(),
               kContrastLevels);
        CHECKM(spec.defaultValue == L.defaultLevel,
               "%s: DefaultValue %ld, expected %d", L.key, spec.defaultValue,
               L.defaultLevel);

        std::set<long> got;
        for (size_t i = 0; i < spec.values.size() && i < spec.titles.size(); i++) {
          const long lvl = spec.values[i];
          got.insert(lvl);
          const Tone t = toneAt(L.field,
                                L.table, (int)lvl);
          const double r = contrastRatio(
              t.c, L.field);
          const std::string want = formatRatio(r);
          const std::string &title = spec.titles[i];
          CHECKM(title.rfind(want, 0) == 0,
                 "%s level %+ld (%s) measures %s but the row says \"%s\"", L.key,
                 lvl, hex(t.c).c_str(), want.c_str(), title.c_str());

          // The named rows have to be on the rows they name.
          const bool isBlack = t.c[0] == 0 && t.c[1] == 0 && t.c[2] == 0;
          const bool isWhite = t.c[0] == 255 && t.c[1] == 255 && t.c[2] == 255;
          if (lvl == 0)
            CHECKM(title.find("invisible") != std::string::npos,
                   "%s level 0 is not labelled invisible: \"%s\"", L.key,
                   title.c_str());
          else if (isBlack)
            CHECKM(title.find("black") != std::string::npos,
                   "%s: %s is not labelled black: \"%s\"", L.key, hex(t.c).c_str(),
                   title.c_str());
          else if (isWhite)
            CHECKM(title.find("white") != std::string::npos,
                   "%s: %s is not labelled white: \"%s\"", L.key, hex(t.c).c_str(),
                   title.c_str());
          else if (lvl == L.defaultLevel)
            CHECKM(title.find("default") != std::string::npos,
                   "%s level %+d is not labelled default: \"%s\"", L.key,
                   L.defaultLevel, title.c_str());
          else if (lvl == L.accessibleLevel)
            CHECKM(title.find("accessible") != std::string::npos,
                   "%s level %+d is not labelled accessible: \"%s\"", L.key,
                   L.accessibleLevel, title.c_str());
        }
        for (int lvl = kContrastMin; lvl <= kContrastMax; lvl++)
          CHECKM(got.count(lvl) == 1, "%s: level %+d appears %zu times in Values",
                 L.key, lvl, got.count(lvl));

        std::set<std::string> uniqueTitles(spec.titles.begin(), spec.titles.end());
        CHECKM(uniqueTitles.size() == spec.titles.size(),
               "%s: two rows print the same label", L.key);
      }

      // The preset row itself.
      const Spec preset = readSpec(plist, "padContrastPreset");
      CHECKM(preset.found, "padContrastPreset: no specifier in Root.plist");
      if (preset.found) {
        CHECKM(preset.defaultValue == kPresetCurrent,
               "padContrastPreset default is %ld, not Current(%d)",
               preset.defaultValue, kPresetCurrent);
        std::set<long> vals(preset.values.begin(), preset.values.end());
        CHECK(vals.count(kPresetCurrent) == 1);
        CHECK(vals.count(kPresetAccessible) == 1);
        CHECK(vals.count(kPresetTransparent) == 1);
        CHECKM(vals.count(kPresetCustom) == 1,
               "Custom must stay reachable: the four fine pickers are otherwise "
               "unreachable and that is a removed capability");
        CHECK(preset.titles.size() == preset.values.size());
        for (long v : preset.values)
          CHECKM(isKnownPreset((int)v), "Root.plist offers unknown preset %ld", v);
      }
    }
  }

  // --- 9. The measured table, printed ------------------------------------
  //
  // Not an assertion: this is the report. Every number quoted in PadPalette.h's
  // comment and in Root.plist's labels comes from this output.
  std::printf("\n");
  for (const Ladder &L : kLadders) {
    std::printf("=== %s (field %s)\n", L.key, hex(L.field).c_str());
    for (int lvl = kContrastMin; lvl <= kContrastMax; lvl++) {
      const Tone t =
          toneAt(L.field, L.table, lvl);
      const double r =
          contrastRatio(t.c, L.field);
      std::printf("  %+3d  %s  %7.3f:1%s%s\n", lvl, hex(t.c).c_str(), r,
                  lvl == L.defaultLevel ? "  default" : "",
                  lvl == L.accessibleLevel ? "  accessible" : "");
    }
  }

  std::printf("\n%s (%d failure%s)\n", failures ? "FAILED" : "pad_palette_test OK",
              failures, failures == 1 ? "" : "s");
  return failures ? 1 : 0;
}
