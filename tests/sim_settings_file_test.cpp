// Host test for src/SimulatorSettingsFile.h.
//
// Every failure mode here is a dial that silently does not apply, which no
// compile and no screenshot can see — the app just keeps rendering what it
// rendered before and the owner concludes the setting does nothing.

#include "SimulatorSettingsFile.h"

#include <cstdio>
#include <string>

using namespace simsettings;
static int failures = 0;
static void check(bool ok, const char *what) {
  if (!ok) { std::printf("FAIL: %s\n", what); failures++; }
}

int main() {
  // --- THE SHIPPED TEMPLATE MUST PARSE TO THE SHIPPED DEFAULTS -------------
  // It is written on first run and is the only documentation most people will
  // read, so a comment or a trailing brace that broke it would ship a file that
  // describes settings it does not apply.
  {
    // The injected palette list is a COMMENT block, so a template built with one
    // must parse to exactly the same values as one built without. That is the
    // property worth pinning: a 52-row comment that swallowed a key would be
    // invisible until someone noticed a dial no longer applied.
    const Values v = parse(defaultsTemplate(""));
    const Values withList = parse(defaultsTemplate(
        "  // 6 = CRT Green (P1 phosphor)\n  // 21 = CRT White (P45)\n"));
    check(v == withList, "the palette comment block changes no value");
    check(intOr(v, "panelPalettePreset", -1) == 21, "template: palette 21");
    check(intOr(v, "pageFadeSeconds", -1) == 300, "template: fade 300 s");
    check(intOr(v, "pageFadeDepthPercent", -1) == 75, "template: depth 75");
    check(intOr(v, "beamPaintMs", -1) == 67, "template: beam 67 ms");
    check(intOr(v, "presentFlash", -1) == 0, "template: flash off");
    check(intOr(v, "phosphorGrainPercent", -1) == 100, "template: grain 100");
    check(intOr(v, "phosphorGrainCoverage", -1) == 3, "template: coverage 3");
    check(intOr(v, "phosphorGrainMottleCells", -1) == 8, "template: cells 8");
    check(intOr(v, "phosphorGrainMottleDepth", -1) == 30, "template: depth 30");
    check(intOr(v, "darkMode", -1) == 1, "template: dark");
  }

  // --- ZERO IS A VALUE, ABSENCE IS NOT -------------------------------------
  // Most of these dials treat 0 as a real choice — grain off, fade off, flash
  // off — so a missing key must return the CALLER'S default and not zero.
  {
    const Values v = parse(R"({"phosphorGrainPercent": 0})");
    check(intOr(v, "phosphorGrainPercent", 100) == 0, "an explicit 0 is kept");
    check(intOr(v, "beamPaintMs", 67) == 67, "an absent key keeps the default");
  }

  // --- ONE BAD LINE COSTS ONE LINE ----------------------------------------
  // A hand-edited file will have typos. The alternative to tolerance is one
  // stray character silently reverting every dial at once.
  {
    const Values v = parse(R"({
      "panelPalettePreset": 6,
      "beamPaintMs": ,
      "phosphorGrainCoverage" 2,
      "pageFadeSeconds": 30,
    })");
    check(intOr(v, "panelPalettePreset", -1) == 6, "a good key before the bad one survives");
    check(intOr(v, "pageFadeSeconds", -1) == 30, "a good key after the bad one survives");
    check(intOr(v, "beamPaintMs", 67) == 67, "a valueless key falls back");
    check(intOr(v, "phosphorGrainCoverage", -1) == 2, "a missing colon still parses");
  }

  // --- QUOTED VALUES ARE SKIPPED, NOT GUESSED -----------------------------
  {
    const Values v = parse(R"({"panelPalettePreset": "twenty-one", "beamPaintMs": 17})");
    check(intOr(v, "panelPalettePreset", 21) == 21,
          "a quoted value leaves the dial at its default rather than 0");
    check(intOr(v, "beamPaintMs", -1) == 17, "and the next key still lands");
  }

  // --- COMMENTS, NEGATIVES, EMPTY -----------------------------------------
  {
    check(parse("").empty(), "an empty file parses to nothing, not to zeros");
    check(parse("garbage with no braces at all").empty(), "junk yields nothing");
    const Values v = parse("{ // \"panelPalettePreset\": 99\n \"beamPaintMs\": -5 }");
    check(intOr(v, "panelPalettePreset", 21) == 21, "a commented-out key is ignored");
    check(intOr(v, "beamPaintMs", 0) == -5, "a negative parses (clamping is the setter's job)");
  }

  if (failures == 0) std::printf("sim_settings_file_test: all checks passed\n");
  return failures ? 1 : 0;
}
