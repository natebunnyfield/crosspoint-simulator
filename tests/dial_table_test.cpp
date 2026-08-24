// THE DIAL TABLE, AND THE ONE THING THAT COULD NOT BE TESTED BEFORE IT.
//
// src/SimulatorDials.h says what every host-side surface dial is worth: what an
// unseeded desktop renders, and what the iOS app ships. The second half is the
// interesting one, because CROSSPOINT_SIM_AS_SHIPPED exists to REPRODUCE THE
// APP on a desktop -- and if its numbers are not the app's numbers, every bug
// hunt run through it is measuring a machine nobody owns.
//
// That happened twice on 2026-08-23, in one day:
//
//   the beam    the app hard-set 55 ms on 2026-08-22; the seed still said 67,
//               so every desktop reproduction of a beam or page-turn report
//               swept 21% slower than the phone.
//   the grain   three of its four arguments were wrong -- 100/8/30 against the
//               app's 160/5/90 -- so a "the coating looks wrong" report was
//               reproduced against a different coating.
//
// Both were found by a human reading two files side by side. Nothing failed.
// Nothing could fail, because the two records had no third party comparing
// them: the app's values lived in ObjC that no host test can compile, and the
// seed's lived in a C++ block that no phone runs.
//
// SO THIS TEST READS THE SHIPPED iOS SOURCES AS TEXT. That is the repo's own
// precedent -- pad_palette_test and panel_palette_test read the shipped
// Root.plist for exactly this reason -- and it is deliberately NOT solved by
// making CrossPointPrefs.mm return simdials::kDials[].shippedValue. That would
// remove the second record, and a test comparing a value to itself proves
// nothing. Two independent records, mechanically compared, is the whole design.
//
// Run from the repo root, or pass the ios/ directory:
//   c++ -std=c++17 -Isrc tests/dial_table_test.cpp -o /tmp/dial_table_test \
//     && /tmp/dial_table_test [ios-dir]
//
// TO SEE IT WORK: change any shippedValue in src/SimulatorDials.h, or any
// frozen constant in ios/CrossPointPrefs.mm, and re-run. It names the dial, the
// two numbers, and the file the second one came from.

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>

#include "SimulatorDials.h"
#include "SimulatorSettingsFile.h"
#include "TestCheck.h"
using testcheck::check;
using testcheck::checkEq;

namespace {

int &g_failures = testcheck::g_failures;

std::string slurp(const std::string &path) {
  std::ifstream f(path);
  if (!f) {
    std::printf("FAIL: cannot read %s\n", path.c_str());
    g_failures++;
    return {};
  }
  std::ostringstream ss;
  ss << f.rdbuf();
  return ss.str();
}

// --- the scrapers ----------------------------------------------------------
//
// Narrow on purpose. Each one looks for the exact shape the shipped file uses
// and reports a MISS rather than guessing, because a scraper that silently
// finds nothing is a test that silently passes -- the failure mode this whole
// file is written against.

constexpr int kNotFound = INT_MIN;

// The body of `int <fn>(void) { ... }`, up to the closing brace at column 0 or
// the end of a same-line body.
std::string bodyOf(const std::string &src, const std::string &fn) {
  const std::string sig = "int " + fn + "(void) {";
  const size_t at = src.find(sig);
  if (at == std::string::npos) return {};
  const size_t from = at + sig.size();
  // A same-line body ends at the first `}`; a multi-line one at `\n}`.
  const size_t nl = src.find('\n', from);
  const size_t sameLineEnd = src.find('}', from);
  if (sameLineEnd != std::string::npos && (nl == std::string::npos || sameLineEnd < nl))
    return src.substr(from, sameLineEnd - from);
  const size_t end = src.find("\n}", from);
  return end == std::string::npos ? std::string() : src.substr(from, end - from);
}

// The LAST `return <int>;` in a function body. Last, not first, because
// CrossPointPrefs_cornerDefocusPercent carries a probe branch above the value
// it actually ships -- and the shipped value is the fallthrough.
int frozenReturn(const std::string &src, const std::string &fn) {
  const std::string body = bodyOf(src, fn);
  if (body.empty()) return kNotFound;
  int value = kNotFound;
  size_t at = 0;
  while ((at = body.find("return ", at)) != std::string::npos) {
    at += 7;
    const char *p = body.c_str() + at;
    if (*p == '-' || (*p >= '0' && *p <= '9')) value = std::atoi(p);
  }
  return value;
}

// `<symbol> : @(<int>)` inside the registerDefaults dictionary.
int registeredDefault(const std::string &src, const std::string &symbol) {
  const std::string needle = symbol + " : @(";
  const size_t at = src.find(needle);
  if (at == std::string::npos) return kNotFound;
  return std::atoi(src.c_str() + at + needle.size());
}

// The DefaultValue of a Root.plist toggle, as 0/1.
int plistToggleDefault(const std::string &src, const std::string &key) {
  const std::string needle = "<string>" + key + "</string>";
  const size_t at = src.find(needle);
  if (at == std::string::npos) return kNotFound;
  // DefaultValue precedes Key in every specifier this bundle writes.
  const size_t dv = src.rfind("<key>DefaultValue</key>", at);
  if (dv == std::string::npos) return kNotFound;
  const size_t t = src.find("<true/>", dv);
  const size_t f = src.find("<false/>", dv);
  if (t != std::string::npos && t < at) return 1;
  if (f != std::string::npos && f < at) return 0;
  return kNotFound;
}

// A literal assignment: `<decl> = <number>`.
double literalAfter(const std::string &src, const std::string &decl) {
  const size_t at = src.find(decl);
  if (at == std::string::npos) return static_cast<double>(kNotFound);
  return std::atof(src.c_str() + at + decl.size());
}

const simdials::Dial &row(simdials::Id id) { return simdials::kDials[id]; }

// The shipped value of one dial, against a number scraped from an iOS source.
void pinShipped(simdials::Id id, int fromIos, const char *whereFrom) {
  const simdials::Dial &d = row(id);
  if (fromIos == kNotFound) {
    std::printf("FAIL: %s -- could not find the app's value in %s (the scraper "
                "missed; the shape it looks for has changed)\n",
                d.name, whereFrom);
    g_failures++;
    return;
  }
  if (d.shippedValue == fromIos) return;
  std::printf("FAIL: %s -- CROSSPOINT_SIM_AS_SHIPPED seeds %d, the app pushes "
              "%d (%s). One of the two moved without the other.\n",
              d.name, d.shippedValue, fromIos, whereFrom);
  g_failures++;
}

}  // namespace

int main(int argc, char **argv) {
  const std::string iosDir = argc > 1 ? argv[1] : "ios";

  // ---------------------------------------------------------------- shape ---
  // The table's own consistency. None of this can be seen by a compiler: every
  // field is an int or a string in an aggregate initializer, so a row pasted
  // from its neighbour and half-edited compiles perfectly.
  for (int i = 0; i < simdials::kDialCount; i++) {
    const simdials::Dial &d = simdials::kDials[i];
    const std::string at = std::string("row ") + std::to_string(i) + " (" +
                           (d.name ? d.name : "?") + ")";
    checkEq(static_cast<int>(d.id), i, at + ": the id field must match its slot");
    check(d.name && d.name[0], at + ": needs a name");
    check(d.envVar && std::strncmp(d.envVar, "CROSSPOINT_SIM_", 15) == 0,
          at + ": every dial needs a CROSSPOINT_SIM_* override, or it cannot be "
               "exercised off-phone at all");
    check(d.settingsKey && d.settingsKey[0], at + ": needs a settings key");
    check(d.minValue <= d.maxValue, at + ": inverted clamp");
    // BOTH values must survive the clamp. A shipped value outside its own
    // clamp is a dial whose stated setting is not the one that renders -- and
    // it would look exactly like a correct table.
    check(d.desktopDefault >= d.minValue && d.desktopDefault <= d.maxValue,
          at + ": the desktop default is outside the setter's clamp");
    check(d.shippedValue >= d.minValue && d.shippedValue <= d.maxValue,
          at + ": the shipped value is outside the setter's clamp");
    check(simdials::isGroupLeader(simdials::kDials[d.group].id),
          at + ": names a group whose leader is not itself a leader");
  }

  // Names, env vars and settings keys are all UNIQUE. A duplicated key means
  // one dial silently shadows another in the settings file, and a duplicated
  // env var means one of them can never be set.
  for (int i = 0; i < simdials::kDialCount; i++)
    for (int j = i + 1; j < simdials::kDialCount; j++) {
      const simdials::Dial &a = simdials::kDials[i];
      const simdials::Dial &b = simdials::kDials[j];
      check(std::strcmp(a.name, b.name) != 0,
            std::string("duplicate dial name: ") + a.name);
      check(std::strcmp(a.envVar, b.envVar) != 0,
            std::string("duplicate env var: ") + a.envVar);
      check(std::strcmp(a.settingsKey, b.settingsKey) != 0,
            std::string("duplicate settings key: ") + a.settingsKey);
    }

  // Every key round-trips through the lookup the watcher uses, and a key that
  // names no dial is refused rather than landing on row 0.
  for (int i = 0; i < simdials::kDialCount; i++)
    checkEq(simdials::indexOfSettingsKey(simdials::kDials[i].settingsKey), i,
            std::string("indexOfSettingsKey(") + simdials::kDials[i].settingsKey +
                ")");
  checkEq(simdials::indexOfSettingsKey("noSuchDial"), -1,
          "an unknown settings key must not resolve");
  checkEq(simdials::indexOfSettingsKey(nullptr), -1,
          "a null settings key must not resolve");

  // ------------------------------------------------ the non-uniformities ---
  // Three dials do not share the others' shape, and each is flagged rather than
  // special-cased at three call sites. Pinned BY NAME, so a fourth one added
  // without a flag -- or a flag moved to the wrong row -- fails here instead of
  // being discovered by an audit six weeks later.
  {
    int multiArg = 0, reconverts = 0, noPresent = 0;
    for (int i = 0; i < simdials::kDialCount; i++) {
      const unsigned f = simdials::kDials[i].flags;
      if (f & simdials::kMultiArg) multiArg++;
      if (f & simdials::kReconverts) reconverts++;
      if (f & simdials::kNoPresent) noPresent++;
    }
    checkEq(multiArg, 4, "kMultiArg: exactly the grain's four rows");
    checkEq(reconverts, 1, "kReconverts: exactly the sheet drift");
    checkEq(noPresent, 1, "kNoPresent: exactly the power-off collapse");
  }
  check((row(simdials::PaperDriftPercent).flags & simdials::kReconverts) != 0,
        "the sheet drift moves the page's own tones, so its setter must be "
        "flagged kReconverts -- a present alone re-pushes pixels graded for the "
        "previous paper");
  check((row(simdials::PowerOffCollapseOn).flags & simdials::kNoPresent) != 0,
        "the power-off collapse asks for no present and must say so");
  // The grain's four rows are ONE setter call: all four name GrainPercent, and
  // nothing else does. Split them and the settings file can push half a grain
  // setting, which repaints three times and stores a state nobody chose.
  {
    int inGrainGroup = 0;
    for (int i = 0; i < simdials::kDialCount; i++)
      if (simdials::kDials[i].group == simdials::GrainPercent) inGrainGroup++;
    checkEq(inGrainGroup, 4, "the grain group is exactly four rows");
  }
  check(simdials::isGroupLeader(simdials::GrainPercent),
        "the grain's leader is the strength row");
  check(!simdials::isGroupLeader(simdials::GrainCoverage) &&
            !simdials::isGroupLeader(simdials::GrainMottleCells) &&
            !simdials::isGroupLeader(simdials::GrainMottleDepth),
        "the grain's other three rows must not be leaders");

  // ------------------------------------------------ the desktop's history ---
  // Every desktop default is what this repo already drew. That is what makes a
  // plain `pio run -e simulator_x3` byte-identical to every capture ever taken
  // from it, and it is the reason the seed can be applied unconditionally.
  // Pinned against the pure models rather than against literals, so a model
  // that retunes its own default carries the desktop with it.
  checkEq(row(simdials::PageFadeSeconds).desktopDefault, 0, "desktop fade off");
  checkEq(row(simdials::PageFadeDepthPercent).desktopDefault,
          pagefade::kDepthFull, "desktop fade depth full");
  checkEq(row(simdials::BeamPaintMs).desktopDefault, 0, "desktop beam off");
  checkEq(row(simdials::PresentFlash).desktopDefault, 0, "desktop flash off");
  checkEq(row(simdials::GrainPercent).desktopDefault,
          phosphorgrain::kStrengthRealistic, "desktop grain realistic");
  checkEq(row(simdials::GrainCoverage).desktopDefault, phosphorgrain::Even,
          "desktop grain coverage even");
  checkEq(row(simdials::GrainMottleCells).desktopDefault,
          phosphorgrain::kMottleCellsDefault, "desktop grain blotch size");
  checkEq(row(simdials::LetterpressPercent).desktopDefault,
          letterpress::kStrengthOff, "desktop letterpress off");
  checkEq(row(simdials::PaperToothPercent).desktopDefault, 100,
          "desktop tooth at the reference stock");
  checkEq(row(simdials::PaperFormationPercent).desktopDefault,
          static_cast<int>(letterpress::kFormationDepthDefault * 100.0f + 0.5f),
          "desktop formation at the model's reference");
  checkEq(row(simdials::PaperDefectsPercent).desktopDefault,
          paperdefects::kDialOff, "desktop sheet unmarked");
  checkEq(row(simdials::PaperDriftPercent).desktopDefault,
          lightink::kPaperDriftDefault, "desktop drift off");
  checkEq(row(simdials::LaidLinesPercent).desktopDefault,
          laidstructure::kStrengthOff, "desktop wires off");
  checkEq(row(simdials::PressRingPercent).desktopDefault, 100, "desktop ring");
  checkEq(row(simdials::PressDebossPercent).desktopDefault, 100, "desktop deboss");
  checkEq(row(simdials::PressPressurePercent).desktopDefault, 100,
          "desktop pressure");
  checkEq(row(simdials::ScanlinesPercent).desktopDefault,
          scanlines::kIntensityOff, "desktop scanlines off");
  checkEq(row(simdials::ScanlineSizePercent).desktopDefault, scanlines::kSizeFine,
          "desktop scanline pitch");
  checkEq(row(simdials::ScanlineBloomPercent).desktopDefault,
          scanlines::kBloomStandard, "desktop scanline bloom");
  checkEq(row(simdials::ShowThroughPercent).desktopDefault,
          showthrough::kStrengthOff, "desktop show-through off");
  checkEq(row(simdials::CornerDefocusPercent).desktopDefault,
          cornerdefocus::kStrengthOff, "desktop corner defocus off");
  checkEq(row(simdials::PowerOffCollapseOn).desktopDefault, 0,
          "desktop collapse off");

  // ---------------------------------------------------- as-shipped vs iOS ---
  // The point of the file. Each of these compares the table's shippedValue with
  // the number the iOS app actually pushes, read out of the shipped source.
  const std::string prefsPath = iosDir + "/CrossPointPrefs.mm";
  const std::string pickerPath = iosDir + "/CrossPointLightInkPicker.mm";
  const std::string shimPath = iosDir + "/CrossPointIOSShim.cpp";
  const std::string plistPath = iosDir + "/Settings.bundle/Root.plist";
  const std::string prefs = slurp(prefsPath);
  const std::string picker = slurp(pickerPath);
  const std::string shim = slurp(shimPath);
  const std::string plist = slurp(plistPath);
  if (prefs.empty() || picker.empty() || shim.empty() || plist.empty()) {
    std::printf("FAIL: pass the ios/ directory as argv[1], or run from the "
                "repo root\n");
    return 1;
  }

  // The frozen getters (2026-08-23: "make these settings the default and remove
  // them from ios app settings as options"). Each returns a literal and never
  // consults NSUserDefaults, so the literal IS what the app renders.
  pinShipped(simdials::PageFadeSeconds,
             frozenReturn(prefs, "CrossPointPrefs_pageFadeSeconds"),
             "CrossPointPrefs.mm");
  pinShipped(simdials::PageFadeDepthPercent,
             frozenReturn(prefs, "CrossPointPrefs_pageFadeDepthPercent"),
             "CrossPointPrefs.mm");
  pinShipped(simdials::LetterpressPercent,
             frozenReturn(prefs, "CrossPointPrefs_letterpressPercent"),
             "CrossPointPrefs.mm");
  pinShipped(simdials::PaperDefectsPercent,
             frozenReturn(prefs, "CrossPointPrefs_paperDefectsPercent"),
             "CrossPointPrefs.mm");
  pinShipped(simdials::ScanlinesPercent,
             frozenReturn(prefs, "CrossPointPrefs_scanlinesPercent"),
             "CrossPointPrefs.mm");
  pinShipped(simdials::ScanlineSizePercent,
             frozenReturn(prefs, "CrossPointPrefs_scanlineSizePercent"),
             "CrossPointPrefs.mm");
  pinShipped(simdials::ScanlineBloomPercent,
             frozenReturn(prefs, "CrossPointPrefs_scanlineBloomPercent"),
             "CrossPointPrefs.mm");
  // The corner defocus carries a temporary on-device probe branch above its
  // shipped value; frozenReturn takes the LAST return for exactly this reason.
  pinShipped(simdials::CornerDefocusPercent,
             frozenReturn(prefs, "CrossPointPrefs_cornerDefocusPercent"),
             "CrossPointPrefs.mm");

  // THE ONE DIAL THAT IS STILL A SETTINGS ROW. Its shipped value is the
  // registered default, which is what an install that never touches the switch
  // renders -- and that is what as-shipped must reproduce.
  pinShipped(simdials::PowerOffCollapseOn,
             plistToggleDefault(plist, "powerOffCollapse"),
             "Settings.bundle/Root.plist");

  // THE PAGE-TURN FLASH used to be the second of those rows and is not any
  // more: the 2026-08-22 sweep took it with the rest of the group and it has
  // had no writer since, so its getter was frozen on 2026-08-23 like the seven
  // above it. Scraped from the frozen constant now rather than from a
  // registerDefaults entry that no longer exists.
  pinShipped(simdials::PresentFlash,
             frozenReturn(prefs, "CrossPointPrefs_presentFlash"),
             "CrossPointPrefs.mm frozen getter");

  // THE GRAIN, all four -- also frozen 2026-08-23, and for the same reason:
  // rows with no writer left a stored value rendering forever with no way back.
  // The strength is the DARK figure because as-shipped forces a dark page; the
  // desktop carries one atomic for both appearances, so the polarity it selects
  // decides which of the app's two strengths is the one being reproduced.
  //
  // Two of the three are pinned as a TEXT match plus a value match rather than
  // through frozenReturn, which reads a leading integer literal and so cannot
  // see either a ternary or a symbol. That is deliberate on the source side:
  // the strength is genuinely two numbers, and the coverage names the model's
  // own enumerator so the app and the model cannot drift apart.
  check(prefs.find("int CrossPointPrefs_phosphorGrainPercent(int dark) { "
                   "return dark ? 160 : 60; }") != std::string::npos,
        "the app freezes the grain at 160 dark / 60 light; if that line moved, "
        "this test's record of the app's value has gone stale");
  checkEq(row(simdials::GrainPercent).shippedValue, 160,
          "screen grain: as-shipped against the app's frozen DARK value");
  check(prefs.find("return phosphorgrain::VignetteMottled;") !=
            std::string::npos,
        "the app freezes the grain coverage at the model's VignetteMottled; if "
        "that line moved, this test's record of the app's value has gone stale");
  checkEq(row(simdials::GrainCoverage).shippedValue,
          phosphorgrain::VignetteMottled,
          "grain coverage: as-shipped against the app's frozen value");
  pinShipped(simdials::GrainMottleDepth,
             frozenReturn(prefs, "CrossPointPrefs_phosphorGrainMottleDepth"),
             "CrossPointPrefs.mm frozen getter");
  // The blotch SIZE is not a stored setting on either side: the shim pushes the
  // model's own default. Pinned as a text match plus a value match, because a
  // scraped integer cannot see a symbol.
  check(shim.find("const int cells = phosphorgrain::kMottleCellsDefault;") !=
            std::string::npos,
        "the shim must push the model's blotch size; if that line moved, this "
        "test's record of the app's value has gone stale");
  checkEq(row(simdials::GrainMottleCells).shippedValue,
          phosphorgrain::kMottleCellsDefault,
          "grain blotch size: as-shipped against the model default the shim "
          "pushes");

  // THE BEAM. Hard-set in the shim, not a row -- this is the drift that shipped
  // for a day.
  {
    const double ms = literalAfter(shim, "constexpr float kBeamPaintMs = ");
    if (ms == static_cast<double>(kNotFound)) {
      std::printf("FAIL: could not find kBeamPaintMs in %s\n", shimPath.c_str());
      g_failures++;
    } else {
      pinShipped(simdials::BeamPaintMs, static_cast<int>(ms + 0.5),
                 "CrossPointIOSShim.cpp kBeamPaintMs");
    }
  }

  // THE PAPER INSTRUMENT'S FROZEN SIX, from the ink picker.
  pinShipped(simdials::PressRingPercent, frozenReturn(picker, "storedRingPct"),
             "CrossPointLightInkPicker.mm");
  pinShipped(simdials::PressDebossPercent,
             frozenReturn(picker, "storedDebossPct"),
             "CrossPointLightInkPicker.mm");
  pinShipped(simdials::PressPressurePercent,
             frozenReturn(picker, "storedPressurePct"),
             "CrossPointLightInkPicker.mm");
  // Drift returns a SYMBOL, not a literal: text match plus value match.
  check(picker.find("int storedDriftPct(void) { return lightink::kPaperDriftMax; }") !=
            std::string::npos,
        "the app freezes sheet drift at the TOP of its range; if that line "
        "moved, this test's record of the app's value has gone stale");
  checkEq(row(simdials::PaperDriftPercent).shippedValue, lightink::kPaperDriftMax,
          "sheet drift: as-shipped against the app's frozen value");

  // THE FOUR STOCK-DERIVED DIALS. What reaches the setter is the app's frozen
  // dial times the CHOSEN STOCK's own factor, so the shipped value here is a
  // product, not a constant. Proved rather than asserted: the app's default
  // stock is Bright White at full strength, and these are its factors.
  {
    const int paper = lightink::kPaperBrightWhite;
    const int strength = lightink::kPaperStrengthMax;
    const float tooth = lightink::toothScaleFor(paper, strength);
    const float formation = lightink::formationScaleFor(paper, strength);
    const float through = lightink::showThroughScaleFor(paper, strength);
    check(std::fabs(tooth - 1.0f) < 1e-6f,
          "the default stock's tooth factor is 1.00, which is why the shipped "
          "tooth is the frozen dial itself");
    check(std::fabs(formation - 1.0f) < 1e-6f,
          "the default stock's formation factor is 1.00");
    check(std::fabs(through - 1.0f) < 1e-6f,
          "the default stock's show-through factor is 1.00");
    check(!lightink::kPapers[paper].laid,
          "the default stock is wove, which is why the shipped wires are 0");

    const int frozenTooth = frozenReturn(picker, "storedToothPct");
    const int frozenFormation = frozenReturn(picker, "storedFormationPct");
    const int frozenThrough =
        frozenReturn(prefs, "CrossPointPrefs_showThroughPercent");
    pinShipped(simdials::PaperToothPercent,
               frozenTooth == kNotFound
                   ? kNotFound
                   : static_cast<int>(std::lround(tooth * frozenTooth)),
               "CrossPointLightInkPicker.mm storedToothPct x the stock's factor");
    pinShipped(simdials::PaperFormationPercent,
               frozenFormation == kNotFound
                   ? kNotFound
                   : static_cast<int>(std::lround(formation * frozenFormation)),
               "CrossPointLightInkPicker.mm storedFormationPct x the stock's "
               "factor");
    pinShipped(simdials::ShowThroughPercent,
               frozenThrough == kNotFound
                   ? kNotFound
                   : static_cast<int>(std::lround(through * frozenThrough)),
               "CrossPointPrefs.mm showThroughPercent x the stock's factor");
    pinShipped(simdials::LaidLinesPercent, 0,
               "the default stock is wove (CrossPointLightInkPicker.mm "
               "laidLinesPercentFor)");
  }

  // ------------------------------------------------- the desktop template ---
  // The starting settings.json the desktop writes on first run names each dial
  // by key. A dial whose key is renamed in the table leaves a dead line there
  // -- documented, editable, and silently doing nothing. Checked in the
  // template->table direction only: a dial the template does not YET name is
  // legitimate (the grain's blotch size is read but deliberately not written),
  // while a template line naming no dial is always a mistake.
  {
    // Everything in that file that is not a dial: the page's own two keys and
    // the phosphor mixer's recipe.
    static const char *const kNotDials[] = {
        "panelPalettePreset",   "darkMode",
        "phosphorMixMode",      "phosphorMixBlend",
        "phosphorMixInkFrom",   "phosphorMixPaperFrom",
        "phosphorMixTrailFrom", "phosphorMixFlash",
        "phosphorMixPersist",
    };
    const simsettings::Values tmpl = simsettings::parse(
        simsettings::defaultsTemplate(""));
    for (const auto &kv : tmpl) {
      bool known = simdials::indexOfSettingsKey(kv.first.c_str()) >= 0;
      for (const char *n : kNotDials)
        if (kv.first == n) known = true;
      check(known, "the desktop settings template names \"" + kv.first +
                       "\", which is no dial and no page key -- a renamed key "
                       "leaves a line that silently does nothing");
    }
  }

  // ------------------------------------------------------- the two fillers ---
  // desktopDefaults() and shippedValues() are what the seed and the as-shipped
  // block push. Trivial, and worth pinning: they are the only two places the
  // table becomes an argument list, and an off-by-one in either would seed
  // every dial with its neighbour's value.
  {
    const simdials::Values d = simdials::desktopDefaults();
    const simdials::Values s = simdials::shippedValues();
    for (int i = 0; i < simdials::kDialCount; i++) {
      const simdials::Id id = static_cast<simdials::Id>(i);
      checkEq(d[id], simdials::kDials[i].desktopDefault,
              std::string("desktopDefaults()[") + simdials::kDials[i].name + "]");
      checkEq(s[id], simdials::kDials[i].shippedValue,
              std::string("shippedValues()[") + simdials::kDials[i].name + "]");
    }
    // Not the same set. If they ever were, as-shipped would be a no-op and the
    // switch would be silently useless.
    bool anyDifferent = false;
    for (int i = 0; i < simdials::kDialCount; i++)
      if (d.v[i] != s.v[i]) anyDifferent = true;
    check(anyDifferent,
          "the desktop and the app must differ somewhere, or "
          "CROSSPOINT_SIM_AS_SHIPPED reproduces nothing");
  }

  // ---- THE TEMPLATE IS THE FOURTH RECORD, and it had no mechanical check ----
  //
  // SimulatorSettingsFile.h's defaultsTemplate() is the file a fresh desktop
  // gets on first run, and applyDials then overwrites the seed with any key
  // PRESENT in that file -- so the template is not documentation, it is what a
  // clean machine renders. The dial-table work unified the boot seed, the
  // watcher and the as-shipped block; the template was the one parallel record
  // it missed, and it drifted: a 5 min fade, 75% depth and a 67 ms beam that no
  // desktop default ever had. The dev box's own machine-written settings.json
  // carried exactly those, so every reproduction on it swept the beam 21% slow.
  //
  // Comparing the two records mechanically is the only thing that stops a fifth
  // drift. A key the template does not name is fine -- the seed then owns it --
  // but a key it DOES name must agree with the desktop default, or a fresh
  // machine and a seeded one disagree about the same dial.
  {
    const simsettings::Values tmpl =
        simsettings::parse(simsettings::defaultsTemplate(""));
    int compared = 0;
    for (int i = 0; i < simdials::kDialCount; i++) {
      const simdials::Dial &d = simdials::kDials[i];
      if (!d.settingsKey || !*d.settingsKey) continue;
      const auto it = tmpl.find(d.settingsKey);
      if (it == tmpl.end()) continue;  // not named: the seed owns it
      compared++;
      checkEq(static_cast<int>(it->second), d.desktopDefault,
              (std::string("template agrees with the desktop default for ") +
               d.name).c_str());
    }
    check(compared > 0,
          "the template names at least one dial -- a zero here would make this "
          "block vacuous, which is how the drift survived in the first place");
    std::printf("dial_table_test: template compared %d dials\n", compared);
  }

  if (g_failures) {
    std::printf("\n%d failure(s)\n", g_failures);
    return 1;
  }
  std::printf("dial_table_test: all checks passed (%d dials)\n",
              simdials::kDialCount);
  return 0;
}
