#pragma once

// THE DESKTOP'S SETTINGS FILE — the Mac and Linux answer to iOS's
// Settings.bundle.
//
// Owner ruling 2026-08-19: "mac app needs the same settings available to it that
// ios has (especially page color)." On iOS every dial lives in NSUserDefaults
// and is polled each frame; the desktop had no equivalent at all, so a palette
// could only be chosen by an env var set before launch — and a packaged .app
// can only bake those in at build time, through LSEnvironment. Changing the page
// color meant rebuilding the bundle.
//
// This is a flat JSON object of numbers, using THE SAME KEYS iOS uses, watched
// by mtime so an edit applies within a second without a relaunch.
//
// Pure and dependency-free on purpose. A JSON library is not worth a build-flag
// change in every consuming platformio.ini, and the file is a flat map of
// numbers, so the parser below is the whole grammar it needs. It is also why
// this can be host-tested: every failure mode is a setting that silently does
// not apply.

#include <cctype>
#include <cstdlib>
#include <map>
#include <string>

namespace simsettings {

// Parsed key -> number. Absent keys are absent; the caller keeps its default
// rather than being handed a zero, which is a real value for most of these
// dials (grain off, fade off, palette High Contrast).
using Values = std::map<std::string, double>;

// TOLERANT BY DESIGN. A settings file is hand-edited, so a trailing comma, a
// missing brace or a stray line must cost that line and not the whole file —
// the alternative is one typo silently reverting every dial at once.
inline Values parse(const std::string &text) {
  Values out;
  size_t i = 0;
  const size_t n = text.size();
  while (i < n) {
    // find a quoted key
    while (i < n && text[i] != '"') {
      // a // comment runs to end of line, even though JSON has no comments:
      // this file is meant to be edited by a person.
      if (text[i] == '/' && i + 1 < n && text[i + 1] == '/') {
        while (i < n && text[i] != '\n') i++;
      }
      i++;
    }
    if (i >= n) break;
    const size_t keyStart = ++i;
    while (i < n && text[i] != '"') i++;
    if (i >= n) break;
    const std::string key = text.substr(keyStart, i - keyStart);
    i++;
    while (i < n && (std::isspace(static_cast<unsigned char>(text[i])) || text[i] == ':')) i++;
    // A quoted VALUE is skipped rather than guessed at: these dials are all
    // numbers, and "true" is not one.
    if (i < n && text[i] == '"') {
      i++;
      while (i < n && text[i] != '"') i++;
      i++;
      continue;
    }
    const size_t numStart = i;
    while (i < n && (std::isdigit(static_cast<unsigned char>(text[i])) ||
                     text[i] == '-' || text[i] == '+' || text[i] == '.'))
      i++;
    if (i == numStart) continue;   // not a number: skip this key
    out[key] = std::atof(text.substr(numStart, i - numStart).c_str());
  }
  return out;
}

// A QUOTED value for one specific key, for the mix's component list -- the one
// setting that is not a number. Returns empty when absent. Kept narrow on
// purpose: the parser stays a map of numbers, and this scans the raw text for
// exactly one key rather than growing a string type.
inline std::string quotedValue(const std::string &text, const char *key) {
  const std::string needle = std::string("\"") + key + "\"";
  size_t at = text.find(needle);
  if (at == std::string::npos) return {};
  at = text.find(':', at + needle.size());
  if (at == std::string::npos) return {};
  size_t q1 = text.find('"', at);
  if (q1 == std::string::npos) return {};
  size_t q2 = text.find('"', q1 + 1);
  if (q2 == std::string::npos) return {};
  return text.substr(q1 + 1, q2 - q1 - 1);
}

// Read with a default, so a missing or malformed key leaves the dial alone.
inline int intOr(const Values &v, const char *key, int fallback) {
  const auto it = v.find(key);
  if (it == v.end()) return fallback;
  return static_cast<int>(it->second);
}

// The file written on first run, so there is something to edit rather than a
// blank. Values here are the iOS defaults, so a fresh desktop install and a
// fresh phone install describe the same app.
// The file written on first run, so there is something to edit rather than a
// blank. Values are the iOS defaults, so a fresh desktop install and a fresh
// phone install describe the same app.
//
// `paletteComment` is injected rather than hardcoded because the palette list
// is 52 rows long and lives in kPresetInfo. Spelling it out here would be a
// second copy that goes stale the first time a preset is appended -- and this
// header stays free of PanelPalette so it can be host-tested on its own.
inline std::string defaultsTemplate(const std::string &paletteComment) {
  return std::string(R"({
  // CrossPoint simulator - desktop settings. Edited while running and applied
  // within a second; no relaunch. Same keys as the iOS Settings app.
  //
  // Every value each key accepts is listed above it. A line you break costs
  // that line only, and a key you delete falls back to its default.

  // ---------------------------------------------------------------- PAGE ---
)") + paletteComment + R"(  "panelPalettePreset": 21,

  // 1 = dark page, 0 = light. Each palette defines both, so this picks which
  // half of the chosen preset is drawn.
  "darkMode": 1,

  // ---------------------------------------------------------------- FADE ---
  // Seconds the page takes to fade after the last input, the way a phosphor
  // goes on dimming after the beam has moved on.
  //   0 = off   15   30   60 = 1 min   120 = 2 min   300 = 5 min
  "pageFadeSeconds": 300,

  // How much of the legible floor is KEPT when it has finished fading.
  //   100 = readable, stops while you can still read it
  //    75 = dim, past readable but plainly still there
  //    50 = ghost, the shape of the page rather than the words
  //    25 = faint, only just visible
  //     0 = fully transparent, the page disappears
  "pageFadeDepthPercent": 75,

  // ---------------------------------------------------------------- BEAM ---
  // Milliseconds for the beam to sweep a new page in from the top. A CRT does
  // not swap pictures, it draws them.
  //   0 = off, arrives at once      17 = 60 Hz, a real field sweep
  //   33 = 30 Hz, just visible      67 = slow enough to watch
  //   150 = deliberate              300 = a wipe, not a tube
  "beamPaintMs": 67,

  // Whether the 1-bit pass may reach the screen ahead of the antialiased
  // compose that follows it. An antialiased page is painted twice; normally
  // only the composed frame lands.
  //   0 = off, the page arrives composed
  //   1 = on, the 1-bit pass lands first, like the panel itself
  "presentFlash": 0,

  // --------------------------------------------------------------- GRAIN ---
  // The screen is a settled layer of phosphor crystals with uneven coverage.
  // Strength as a percentage of what a real one has.
  //   0 = off   30 = 0.3x, barely there   100 = 1x, realistic   300 = 3x
  // The amplitude is scaled per palette on top of this: a page with less
  // contrast to spare gets less coating.
  "phosphorGrainPercent": 100,

  // How the grain is spread across the screen.
  //   0 = Even, coated uniformly
  //   1 = Vignette, grainier at the rim with dimmed corners
  //   2 = Mottled, blotchy the way a coating settles
  //   3 = both
  "phosphorGrainCoverage": 3,

  // How hard the blotches swing the grain, in hundredths. Their SIZE is not
  // settable -- see kMottleCellsDefault.
  //   0 = off, no blotching at all       3 = 0.03, a suggestion
  //   10 = 0.10, visible                90 = 0.90, plainly a coated surface
  "phosphorGrainMottleDepth": 90,

  // ---------------------------------------------- LETTERPRESS / SCANLINES ---
  // The 2026-08-22 doctrine: light mode is paper and ink (letterpress), dark
  // mode is a CRT (scanlines instead of the mottled grain). While either is
  // active in its mode the grain above is skipped; set it to 0 to get the old
  // grain back for comparison. Both 0 here so the desktop renders what it
  // always did; the iOS app defaults both to 50.
  // Letterpress, percent of standard: ink-squeeze rim, deboss shadow, plate
  // pressure, paper tooth.
  //   0 = off   50 = subtle   100 = standard   200 = heavy
  "letterpressPercent": 0,

  // THE PAPER INSTRUMENT. Everything the light page's sheet is made of, as
  // live dials (owner order 2026-08-22). Each default below is what this
  // simulator already drew, so a file without these keys renders exactly what
  // it always did -- which is why paperDefectsPercent is 0 here and 30 in the
  // iOS app.
  //
  // How rough the SHEET is, as a percent of the reference stock. 100 is the
  // shipped Bright White; the iOS picker derives this from the chosen paper
  // and its strength, so setting it here is the desktop's way in.
  "paperToothPercent": 100,

  // The sheet's FORMATION -- its cloudiness, the low-frequency fibre
  // distribution you see holding a sheet to a light. A symmetric swing on the
  // tooth's amplitude, so it costs nothing against the contrast floor.
  //   0 = a perfectly even sheet (no real stock)   55 = the shipped reference
  //   100 = the model's maximum
  "paperFormationPercent": 55,

  // PAPER DEFECTS: how marked the sheet is. An INCIDENCE dial -- turning it up
  // gives an older book, not a dirtier ink. Foxing, red rag flecks, blue marks,
  // brown stains, fly specks and wax spots, masked by the page's own ink so a
  // mark never sits on a glyph. docs/paper-defects.md.
  //   0 = a fresh sheet (bit-exact off)   30 = the iOS default   100 = used
  "paperDefectsPercent": 0,

  // SHEET-TO-SHEET DRIFT: how far one leaf's paper tone may sit from the
  // stock's. A book is printed from several reams and ages unevenly, so no two
  // leaves measure the same; every page here measures identically without
  // this. Derived from the same page identity the tooth, the wires and the
  // marks use, so a page is the same leaf across a relaunch, and it moves the
  // PAPER only. +/-2 code values at 100, because this tone is the whole page's
  // ground. docs/surface-roadmap.md section 1c.
  //   0 = one tone per book (bit-exact off, both platforms)   100 = +/-2
  "paperDriftPercent": 0,

  // THE PRESS'S THREE PARTS, as percents of the standard press. The
  // letterpressPercent above is the MASTER; these are the per-component ratios
  // and compose multiplicatively with it, so there is one stored value per
  // quantity. 200 is the ceiling, and it is the no-new-worst-case bound rather
  // than taste. All carried by ink or its edges, so none touches the paper's
  // contrast budget.
  //   ring     the ink-squeeze rim, the letterpress signature
  //   deboss   the shadowed walls of the type's bite
  //   pressure the unevenness of impression across the forme
  "pressRingPercent": 100,
  "pressDebossPercent": 100,
  "pressPressurePercent": 100,
  // ...note the pressure dial's mapped range is WIDENED above 100: the
  // physical effect (heavy areas darkening ink) is subtle at this scale, so
  // 100..200 spans 1x..8x of the standard amplitude while 0..100 stays the
  // identity. src/Letterpress.h, pressAmpScale.

  // CHAIN AND LAID LINES, for a laid stock. The iOS picker derives this from
  // the chosen paper (only Laid Antique carries wires today) and its
  // strength; this raw percent is the desktop's way in, since this file has
  // no paper picker. 0 = off (bit-exact, the historical rendering);
  // 100 = standard. Measured geometry -- laid ~1 mm pitch, chains 26-39 mm,
  // chains darker, antique strip along each chain: src/LaidStructure.h and
  // docs/paper-colorimetry-sources.md section 3c.
  "laidLinesPercent": 0,

  // Scanlines, percent of standard: one scan line per page row, Gaussian
  // beam, bright-content bloom, blotch depth folded into the dial.
  //   0 = off   50 = subtle   100 = standard   150 = deep
  "scanlinesPercent": 0,

  // Scanline SIZE: the line pitch, as a percent of the SOURCE-ROW pitch.
  // Multiples of the page's own row lattice, never absolute pixels -- an
  // absolute pitch is a free ratio against a per-device presentation scale,
  // which is the second lattice this design exists to avoid.
  //   100 = 1 line per page row (the shipped pitch)   150 = 1 per 1.5 rows
  //   200 = 1 per 2 rows                              300 = 1 per 3 rows
  "scanlineSizePercent": 100,

  // Scanline BLOOM: how far beam current widens the lit band, as a percent of
  // the standard gain. A fraction of the pitch, so it stays proportionate at
  // every scanline size. It can only spare light, never add it.
  //   0 = off (the field stops being content-aware)   50 = subtle
  //   100 = standard (the shipped tube)   200 = strong   400 = extreme
  "scanlineBloomPercent": 100,

  // --------------------------------------------------------- PHOSPHOR MIX ---
  // The same mixer the iOS page-color modal drives, through the same math. A
  // mix OWNS the page and its glow while active; panelPalettePreset is ignored.
  //   -1 = off (use panelPalettePreset above)
  //    0 = blend    weighted mixture of up to 4 pure phosphors
  //    1 = parts    ink, paper and fade from three donors
  //    2 = cascade  a flash layer that paints, a persistence layer that lingers
  // Premixed phosphors (P4 P6 P7 P14 P17 P18 P23 P40) are not ingredients --
  // pick them as presets instead. Every phosphor's integer is in the palette
  // list at the top of this file.
  "phosphorMixMode": -1,

  // Blend: "preset:weight" pairs, comma-separated, weights 1-9.
  // e.g. "6:3,15:1" is P1 green 3 parts to P11 blue 1 part.
  "phosphorMixBlend": "",

  // Parts: which preset donates each role.
  "phosphorMixInkFrom": -1,
  "phosphorMixPaperFrom": -1,
  "phosphorMixTrailFrom": -1,

  // Cascade: the flash paints the page, the persistence lingers in its color.
  "phosphorMixFlash": -1,
  "phosphorMixPersist": -1
}
)";
}

}  // namespace simsettings
