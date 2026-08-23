#include "SimulatorSettingsWatch.h"

#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif

#if defined(TARGET_OS_IPHONE) && TARGET_OS_IPHONE
namespace simsettings {
void pollSettingsFile() {}   // the phone has NSUserDefaults
}
#else

#include <SDL3/SDL.h>
#include <sys/stat.h>

#include <cstdio>
#include <string>
#include <vector>

#include "HalDisplay.h"
#include "HalStorage.h"
#include "CornerDefocus.h"
#include "PanelPalette.h"
#include "PhosphorGrain.h"
#include "PhosphorMix.h"
#include "Letterpress.h"
#include "LightInkPalette.h"
#include "PaperDefects.h"
#include "Scanlines.h"
#include "ShowThrough.h"
#include "SimulatorOverlay.h"
#include "SimulatorSettingsFile.h"

namespace simsettings {
namespace {

// Beside the simulated card, not inside it: a host setting is not a file the
// firmware should ever see, and Manage Files lists everything on the card.
std::string settingsPath() {
  std::string root = simulatorStorageRootForHost();
  while (!root.empty() && root.back() == '/') root.pop_back();
  const size_t slash = root.find_last_of('/');
  const std::string parent = slash == std::string::npos ? std::string(".")
                                                        : root.substr(0, slash);
  return parent + "/settings.json";
}

// Every palette, as a comment block, generated from kPresetInfo so it cannot
// go stale the way a hand-written list of 52 rows would. The order is
// kPresetInfo's own -- the shortlist first, then the families -- which is also
// the order the iOS picker and the firmware's cycle button use.
std::string paletteComment() {
  std::string out =
      "  // The page's two tones. Every preset below; the integer is what is\n"
      "  // stored, and it never changes meaning even when the list is\n"
      "  // reordered. Rows marked * are the shortlist at the head of the\n"
      "  // iOS picker. A CRT preset also switches the page to emissive and\n"
      "  // gives it that phosphor's glow.\n";
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
    const panelpalette::PresetInfo &info = panelpalette::kPresetInfo[i];
    char line[220];
    const float trail = panelpalette::trailMsForPreset(info.preset);
    if (trail > 0.0f)
      std::snprintf(line, sizeof line, "  //%s%4d = %s %s (%s, %.0f ms trail)\n",
                    i < 6 ? " *" : "  ", info.preset, info.family, info.name,
                    info.note, static_cast<double>(trail));
    else
      std::snprintf(line, sizeof line, "  //%s%4d = %s %s (%s)\n",
                    i < 6 ? " *" : "  ", info.preset, info.family, info.name,
                    info.note);
    out += line;
  }
  return out;
}

void writeTemplateIfMissing(const std::string &path) {
  struct stat st{};
  if (stat(path.c_str(), &st) == 0) return;
  // ...and NOT while reproducing the app. The template names every dial, so
  // writing it makes every key PRESENT -- which defeats the whole of the
  // absent-key rule below and silently un-does the as-shipped seed one second
  // after boot. The first fix for that missed this: it was measured on a
  // machine whose settings.json predated the template, so no key was present
  // and the guard appeared to work. On a fresh machine it did not.
  //
  // A file the owner has already written still wins, in both modes. This
  // declines only to CREATE one.
  if (asShippedWanted()) return;
  FILE *f = std::fopen(path.c_str(), "w");
  if (!f) return;
  std::fputs(defaultsTemplate(paletteComment()).c_str(), f);
  std::fclose(f);
  SDL_Log("[settings] wrote a starting file at %s", path.c_str());
}

std::string readAll(const std::string &path) {
  FILE *f = std::fopen(path.c_str(), "rb");
  if (!f) return {};
  std::string out;
  char buf[4096];
  size_t got;
  while ((got = std::fread(buf, 1, sizeof buf, f)) > 0) out.append(buf, got);
  std::fclose(f);
  return out;
}

// The mix, from the same keys iOS persists, through the same core. A recipe
// typed here and one built on the phone compute the same page and the same
// glow, because both go through PhosphorMix.h -- that identity is the whole
// point of the parity ruling (owner 2026-08-21).
//
// Returns true when a mix is ACTIVE, in which case it owns the palette and the
// glow and the preset key is ignored. phosphorMixMode: -1 off, 0 blend,
// 1 parts, 2 cascade.
void applyDials(const Values &v);

bool applyMix(const Values &v, const std::string &raw) {
  const int mode = intOr(v, "phosphorMixMode", -1);
  if (mode < phosphormix::Blend || mode > phosphormix::Cascade) return false;

  phosphormix::Result r;
  if (mode == phosphormix::Parts) {
    r = phosphormix::mixParts(intOr(v, "phosphorMixInkFrom", -1),
                              intOr(v, "phosphorMixPaperFrom", -1),
                              intOr(v, "phosphorMixTrailFrom", -1));
  } else if (mode == phosphormix::Cascade) {
    r = phosphormix::mixCascade(intOr(v, "phosphorMixFlash", -1),
                                intOr(v, "phosphorMixPersist", -1));
  } else {
    // "preset:weight,preset:weight" -- the same CSV iOS stores.
    phosphormix::Component comps[phosphormix::kMaxComponents];
    int n = 0;
    const std::string csv = quotedValue(raw, "phosphorMixBlend");
    size_t at = 0;
    while (at < csv.size() && n < phosphormix::kMaxComponents) {
      size_t end = csv.find(',', at);
      if (end == std::string::npos) end = csv.size();
      const std::string pair = csv.substr(at, end - at);
      at = end + 1;
      const size_t colon = pair.find(':');
      if (colon == std::string::npos) continue;
      comps[n].preset = std::atoi(pair.substr(0, colon).c_str());
      comps[n].weight = std::atoi(pair.substr(colon + 1).c_str());
      n++;
    }
    if (n == 0) return false;   // blend mode with no components is no mix
    r = phosphormix::mixBlend(comps, n);
  }

  const bool dark = intOr(v, "darkMode", 1) != 0;
  SimulatorOverlay::setPanelDark(dark);
  const panelpalette::Palette &pal = dark ? r.dark : r.light;
  SimulatorOverlay::setPanelPalette(dark, pal.ink, pal.paper);
  SimulatorOverlay::setPanelEmissive(r.trailMs > 0.0f);
  SimulatorOverlay::setPanelGlow(r.trailMs);
  SimulatorOverlay::setPanelGlowTail(r.hasTail ? r.tail : nullptr,
                                     r.hasTail ? r.tailOnsetMs : 0.0f);
  SDL_Log("[settings] phosphor mix active (mode %d): %02X%02X%02X on "
          "%02X%02X%02X, trail %.0f ms%s",
          mode, pal.ink[0], pal.ink[1], pal.ink[2], pal.paper[0], pal.paper[1],
          pal.paper[2], static_cast<double>(r.trailMs),
          r.hasTail ? ", tinted tail" : "");
  return true;
}

void apply(const Values &v) {
  // Polarity first: the palette is resolved FOR a polarity, so setting the
  // tones before the appearance would push the wrong pair for one frame.
  // AS-SHIPPED LEAVES THE TONES ALONE TOO. The absent-key rule below covers the
  // dials; the polarity and the palette are the other half of what the seed
  // sets, and re-applying a default here put a Default dark pair over the
  // seed's White CRT one second after boot (measured: 67% of bytes moved).
  const bool haveDark = v.find("darkMode") != v.end();
  const bool havePreset = v.find("panelPalettePreset") != v.end();
  if (asShippedWanted() && !haveDark && !havePreset) return applyDials(v);

  const bool dark = intOr(v, "darkMode", 1) != 0;
  SimulatorOverlay::setPanelDark(dark);

  const int preset = intOr(v, "panelPalettePreset", panelpalette::kPresetDefault);
  const panelpalette::Palette pal = panelpalette::resolve(
      preset, dark, panelpalette::kInvalidColor, panelpalette::kInvalidColor);
  SimulatorOverlay::setPanelPalette(dark, pal.ink, pal.paper);

  // A CRT palette is a claim that the page is a tube, and a tube glows — the
  // same rule pollPanelGlow follows on the phone, so the two agree without a
  // second decision. Every non-phosphor palette gets 0.
  const float trail = panelpalette::trailMsForPreset(preset);
  SimulatorOverlay::setPanelEmissive(trail > 0.0f);
  SimulatorOverlay::setPanelGlow(trail);
  const unsigned char *tail = nullptr;
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++)
    if (panelpalette::kPresetInfo[i].preset == preset)
      tail = panelpalette::kPresetInfo[i].afterglow;
  SimulatorOverlay::setPanelGlowTail(tail);

  applyDials(v);
}

// The dials that are not the page's tones or its glow -- shared by the preset
// path and the mix path.
void applyDials(const Values &v) {
  // These four were left outside the absent-key rule when it was added and so
  // still reset the seed a second after boot. Same rule, same reason.
  const auto has = [&v](const char *k) { return v.find(k) != v.end(); };
  if (has("pageFadeSeconds") || !asShippedWanted())
    SimulatorOverlay::setPageFade(
        static_cast<float>(intOr(v, "pageFadeSeconds", 0)) * 1000.0f);
  if (has("pageFadeDepthPercent") || !asShippedWanted())
    SimulatorOverlay::setPageFadeDepth(intOr(v, "pageFadeDepthPercent", 100));
  if (has("beamPaintMs") || !asShippedWanted())
    SimulatorOverlay::setBeamPaint(
        static_cast<float>(intOr(v, "beamPaintMs", 0)));
  if (has("presentFlash") || !asShippedWanted())
    SimulatorOverlay::setPresentFlash(intOr(v, "presentFlash", 0) != 0);
  // Grain's four arguments arrive together, so it is all-or-nothing under the
  // rule: if the file names ANY of them the file is deciding, otherwise the
  // seed keeps what it set. The cell count gains a key here -- it had none, so
  // no file could express the 8 the app ships and this call always passed the
  // model default of 5.
  if (has("phosphorGrainPercent") || has("phosphorGrainCoverage") ||
      has("phosphorGrainMottleCells") || has("phosphorGrainMottleDepth") ||
      !asShippedWanted()) {
    SimulatorOverlay::setPhosphorGrain(
        intOr(v, "phosphorGrainPercent", phosphorgrain::kStrengthRealistic),
        intOr(v, "phosphorGrainCoverage", phosphorgrain::Even),
        intOr(v, "phosphorGrainMottleCells", phosphorgrain::kMottleCellsDefault),
        intOr(v, "phosphorGrainMottleDepth",
              (int)(phosphorgrain::kMottleDepthDefault * 100.0f)));
  }
  // An ABSENT key is not the same thing as a key set to the default, and the
  // difference is the whole of this lambda. The watcher re-reads the file about
  // once a second, so applying a default for a key nobody wrote silently
  // overwrote whatever seeded the dial at boot -- which meant
  // CROSSPOINT_SIM_AS_SHIPPED undid itself a second after it ran, the exact
  // divergence that switch exists to prevent. Found 2026-08-23 after it cost
  // two rounds of wrong measurements. An explicit key still wins in both modes:
  // a value the owner typed is a decision, a missing key is not.
  const auto dial = [&v](const char *key, int fallback, void (*set)(int)) {
    const auto it = v.find(key);
    if (it != v.end()) {
      set(static_cast<int>(it->second));
    } else if (!asShippedWanted()) {
      set(fallback);
    }
  };

  // The 2026-08-22 doctrine dials. 0 is the desktop default for both -- a file
  // without the keys renders what the desktop always rendered.
  dial("letterpressPercent", 0, SimulatorOverlay::setLetterpress);
  // The paper instrument. Same keys and same units as the iOS app, so a
  // settings.json and a phone cannot disagree about what a sheet looks like.
  // Defaults are the desktop's historical values, not the app's.
  dial("paperToothPercent", 100, SimulatorOverlay::setPaperTooth);
  dial("paperFormationPercent",
       static_cast<int>(letterpress::kFormationDepthDefault * 100.0f + 0.5f),
       SimulatorOverlay::setPaperFormation);
  dial("paperDefectsPercent", paperdefects::kDialOff,
       SimulatorOverlay::setPaperDefects);
  dial("paperDriftPercent", lightink::kPaperDriftDefault,
       SimulatorOverlay::setPaperDrift);
  // A raw percent, not a paper index: the desktop file has no ink/paper
  // picker, so laidness cannot be derived here the way the phone derives it.
  // 0 is the historical desktop rendering.
  dial("laidLinesPercent", 0, SimulatorOverlay::setLaidLines);
  dial("pressRingPercent", 100, SimulatorOverlay::setPressRing);
  dial("pressDebossPercent", 100, SimulatorOverlay::setPressDeboss);
  dial("pressPressurePercent", 100, SimulatorOverlay::setPressPressure);
  dial("scanlinesPercent", 0, SimulatorOverlay::setScanlines);
  dial("scanlineSizePercent", scanlines::kSizeFine,
       SimulatorOverlay::setScanlineSize);
  dial("scanlineBloomPercent", scanlines::kBloomStandard,
       SimulatorOverlay::setScanlineBloom);
  // The 2026-08-23 roadmap items. Off is the desktop's historical rendering
  // for all three, so a file without the keys is unchanged.
  dial("showThroughPercent", showthrough::kStrengthOff,
       SimulatorOverlay::setShowThrough);
  dial("cornerDefocusPercent", cornerdefocus::kStrengthOff,
       SimulatorOverlay::setCornerDefocus);
  // A flag rather than a percent, so it takes the int dial's shape through a
  // thunk instead of a second lookup path.
  dial("powerOffCollapse", 0,
       [](int on) { SimulatorOverlay::setPowerOffCollapse(on != 0); });
}

}  // namespace

void pollSettingsFile() {
  static std::string path;
  static bool started = false;
  static time_t lastMtime = 0;
  static uint64_t lastCheckMs = 0;

  const uint64_t now = SDL_GetTicks();
  if (started && now - lastCheckMs < 1000) return;   // one stat a second
  lastCheckMs = now;

  if (!started) {
    started = true;
    path = settingsPath();
    writeTemplateIfMissing(path);
  }

  struct stat st{};
  if (stat(path.c_str(), &st) != 0) return;
  if (st.st_mtime == lastMtime) return;
  lastMtime = st.st_mtime;

  const std::string raw = readAll(path);
  const Values v = parse(raw);
  if (v.empty()) {
    SDL_Log("[settings] %s parsed to nothing — leaving every dial alone",
            path.c_str());
    return;
  }
  SDL_Log("[settings] applied %zu keys from %s", v.size(), path.c_str());
  if (applyMix(v, raw)) {
    // The mix owns the page and the glow; the remaining dials (fade, beam,
    // flash, grain) still apply from the same file.
    applyDials(v);
    return;
  }
  apply(v);
}

}  // namespace simsettings
#endif
