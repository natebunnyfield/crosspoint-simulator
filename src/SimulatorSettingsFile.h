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
  "phosphorGrainMottleDepth": 90
}
)";
}

}  // namespace simsettings
