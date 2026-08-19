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
#include "PhosphorGrain.h"
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

void writeTemplateIfMissing(const std::string &path) {
  struct stat st{};
  if (stat(path.c_str(), &st) == 0) return;
  FILE *f = std::fopen(path.c_str(), "w");
  if (!f) return;
  std::fputs(defaultsTemplate(), f);
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

void apply(const Values &v) {
  // Polarity first: the palette is resolved FOR a polarity, so setting the
  // tones before the appearance would push the wrong pair for one frame.
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

  SimulatorOverlay::setPageFade(
      static_cast<float>(intOr(v, "pageFadeSeconds", 0)) * 1000.0f);
  SimulatorOverlay::setPageFadeDepth(intOr(v, "pageFadeDepthPercent", 100));
  SimulatorOverlay::setBeamPaint(static_cast<float>(intOr(v, "beamPaintMs", 0)));
  SimulatorOverlay::setPresentFlash(intOr(v, "presentFlash", 0) != 0);
  SimulatorOverlay::setPhosphorGrain(
      intOr(v, "phosphorGrainPercent", phosphorgrain::kStrengthRealistic),
      intOr(v, "phosphorGrainCoverage", phosphorgrain::Even),
      intOr(v, "phosphorGrainMottleCells", phosphorgrain::kMottleCellsDefault),
      intOr(v, "phosphorGrainMottleDepth", 10));
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

  const Values v = parse(readAll(path));
  if (v.empty()) {
    SDL_Log("[settings] %s parsed to nothing — leaving every dial alone",
            path.c_str());
    return;
  }
  SDL_Log("[settings] applied %zu keys from %s", v.size(), path.c_str());
  apply(v);
}

}  // namespace simsettings
#endif
