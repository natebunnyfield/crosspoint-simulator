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
inline const char *defaultsTemplate() {
  return R"({
  // CrossPoint simulator — desktop settings. Edited while running; applied
  // within a second. Same keys as the iOS Settings app.
  //
  // panelPalettePreset: 21 = CRT White (P45). 1 = the e-ink default.
  //   Every preset integer is listed in src/PanelPalette.h.
  "panelPalettePreset": 21,

  // Seconds the page takes to fade after the last input. 0 = off.
  "pageFadeSeconds": 300,
  // How much of the legible floor is KEPT: 100 = readable, 0 = transparent.
  "pageFadeDepthPercent": 75,

  // Milliseconds for the beam to sweep a new page in. 0 = arrives at once.
  "beamPaintMs": 67,
  // 1 = let the 1-bit pass reach the screen ahead of the composed one.
  "presentFlash": 0,

  // Screen grain. 0, 30, 100 or 300 (percent of realistic).
  "phosphorGrainPercent": 100,
  // 0 Even, 1 Vignette, 2 Mottled, 3 both.
  "phosphorGrainCoverage": 3,
  // Blotches across the page: 8, 16 or 32.
  "phosphorGrainMottleCells": 8,
  // Blotch depth in hundredths: 0, 3, 10 or 30.
  "phosphorGrainMottleDepth": 30,

  // 1 = dark page, 0 = light.
  "darkMode": 1
}
)";
}

}  // namespace simsettings
