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
#include "PanelPalette.h"
#include "PhosphorMix.h"
#include "SimulatorDials.h"
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
//
// TABLE-DRIVEN since 2026-08-23. This was twenty hand-written lines naming each
// key, its desktop default and its setter; those three facts now come from
// simdials::kDials, and the file that names them also drives the boot seed and
// the as-shipped block. See src/SimulatorDials.h for why.
//
// AN ABSENT KEY IS NOT THE SAME THING AS A KEY SET TO THE DEFAULT, and the
// difference is the whole of the rule below. The watcher re-reads the file
// about once a second, so applying a default for a key nobody wrote silently
// overwrote whatever seeded the dial at boot -- which meant
// CROSSPOINT_SIM_AS_SHIPPED undid itself a second after it ran, the exact
// divergence that switch exists to prevent. Found 2026-08-23 after it cost two
// rounds of wrong measurements. An explicit key still wins in both modes: a
// value the owner typed is a decision, a missing key is not.
//
// THE GRAIN IS ALL-OR-NOTHING, because its setter takes its four arguments
// together: a file naming ANY of the four is deciding all four. That is the
// kMultiArg flag, and it is handled here as group presence rather than as a
// special case, so the next multi-argument dial needs no code in this file.
void applyDials(const Values &v) {
  simdials::Values dials = simdials::desktopDefaults();
  bool present[simdials::kDialCount] = {false};
  for (int i = 0; i < simdials::kDialCount; i++) {
    const auto it = v.find(simdials::kDials[i].settingsKey);
    if (it == v.end()) continue;
    dials.v[i] = static_cast<int>(it->second);
    present[i] = true;
  }

  // A group counts as named when ANY of its rows was.
  bool groupPresent[simdials::kDialCount] = {false};
  for (int i = 0; i < simdials::kDialCount; i++)
    if (present[i]) groupPresent[simdials::kDials[i].group] = true;

  const bool asShipped = asShippedWanted();
  for (int i = 0; i < simdials::kDialCount; i++) {
    const simdials::Id id = static_cast<simdials::Id>(i);
    if (!simdials::isGroupLeader(id)) continue;
    if (groupPresent[i] || !asShipped)
      SimulatorOverlay::applyDialGroup(id, dials);
  }
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
