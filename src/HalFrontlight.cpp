#include "HalFrontlight.h"

#include <BoardConfig.h>

#include <algorithm>
#include <atomic>
#include <iostream>

#include "FrontlitLight.h"

// THE PICCO'S LIGHT REACHES THE PAGE (TODO.md ST-012, 2026-11-27). The X4 Pro
// and the Picco both carry a frontlight, so present() answers true for both,
// as the hardware does. Only the Picco's state is PUBLISHED to the hosts,
// which turn it into the page's paper, ink and tube (src/FrontlitPage.h); on
// every other board simfrontlight::current() stays off and nothing moves.
namespace {
std::atomic<int> g_brightness{frontlitpage::kDefaultBrightness};
std::atomic<int> g_warmth{frontlitpage::kDefaultWarmth};
std::atomic<bool> g_on{false};
std::atomic<int> g_tube{frontlitpage::kTubeMixed};
std::atomic<unsigned> g_generation{0};
std::atomic<simfrontlight::ChangedHook> g_hook{nullptr};

void publish(uint8_t brightness, uint8_t warmth, bool on, uint8_t tube) {
  if (!BoardConfig::isPicco()) return;
  // All four exchanges run, whichever changed.
  // The Picco app's byte is the Brightness STEP, not a percent
  // (FrontlitLight.h brightnessFromStored); the page model takes the shown
  // value.
  const int shown = frontlitpage::brightnessFromStored(brightness);
  bool changed = g_brightness.exchange(shown) != shown;
  if (g_warmth.exchange(warmth) != warmth) changed = true;
  if (g_on.exchange(on) != on) changed = true;
  if (g_tube.exchange(tube) != tube)
    changed = true;
  if (!changed) return;
  g_generation.fetch_add(1);
  if (simfrontlight::ChangedHook hook = g_hook.load()) hook();
}
}  // namespace

namespace simfrontlight {
frontlitpage::Light current() {
  frontlitpage::Light l;
  l.brightness = g_brightness.load();
  l.warmth = g_warmth.load();
  l.on = g_on.load();
  l.tube = g_tube.load();
  return l;
}
unsigned generation() { return g_generation.load(); }
void setChangedHook(ChangedHook hook) { g_hook.store(hook); }
}  // namespace simfrontlight

HalFrontlight &HalFrontlight::getInstance() {
  static HalFrontlight instance;
  return instance;
}

// The Picco's byte is the stored Brightness step (0..80, FrontlitLight.h); the
// X4 Pro's is still a percent.
static uint8_t clampBrightnessByte(uint8_t b) {
  const int top = BoardConfig::isPicco() ? frontlitpage::kMaxStoredBrightness : 100;
  return static_cast<uint8_t>(std::min<int>(b, top));
}

void HalFrontlight::begin(uint8_t brightness, uint8_t warmth, bool on) {
  if (!present())
    return;
  lastBrightness = clampBrightnessByte(brightness);
  lastWarmth = std::min<uint8_t>(warmth, 100);
  lit = on;
  std::cerr << "[SIM] " << (BoardConfig::isPicco() ? "Picco" : "X4 Pro")
            << " frontlight: " << (lit ? "on" : "off")
            << ", brightness="
            << (BoardConfig::isPicco()
                    ? frontlitpage::brightnessFromStored(lastBrightness)
                    : static_cast<int>(lastBrightness))
            << ", warmth=" << static_cast<unsigned>(lastWarmth) << "%"
            << std::endl;
  publish(lastBrightness, lastWarmth, lit, lastTube);
}

bool HalFrontlight::present() const {
  return BoardConfig::isX4Pro() || BoardConfig::isPicco();
}

bool HalFrontlight::hasColorTemperature() const { return present(); }

void HalFrontlight::setBrightness(uint8_t percent) {
  lastBrightness = clampBrightnessByte(percent);
  publish(lastBrightness, lastWarmth, lit, lastTube);
}

void HalFrontlight::setWarmth(uint8_t warmPercent) {
  lastWarmth = std::min<uint8_t>(warmPercent, 100);
  publish(lastBrightness, lastWarmth, lit, lastTube);
}

void HalFrontlight::setOn(bool on) {
  lit = present() && on;
  publish(lastBrightness, lastWarmth, lit, lastTube);
}

void HalFrontlight::setTube(uint8_t tube) {
  lastTube = tube < frontlitpage::kTubeCount ? tube : frontlitpage::kTubeMixed;
  publish(lastBrightness, lastWarmth, lit, lastTube);
}

uint8_t HalFrontlight::brightness() const { return lastBrightness; }

uint8_t HalFrontlight::warmth() const { return lastWarmth; }

bool HalFrontlight::isOn() const { return lit; }
