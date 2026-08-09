#include "HalPowerManager.h"

#include "HalGPIO.h"

#include <cstdlib>

HalPowerManager powerManager;

void HalPowerManager::begin() {}
void HalPowerManager::startDeepSleep(HalGPIO &gpio) const { gpio.startDeepSleep(); }
void HalPowerManager::setPowerSaving(bool enable) {}
// A flat 100% meant the low-battery paths -- the warning, the sleep-screen
// battery art, anything gated on a threshold -- could not run (S-001).
// CROSSPOINT_SIM_BATTERY=<0-100> sets it; unset keeps the old 100 so every
// existing screenshot run is unchanged.
uint16_t HalPowerManager::getBatteryPercentage() const {
  static const uint16_t pct = [] {
    const char *v = std::getenv("CROSSPOINT_SIM_BATTERY");
    if (!v) return static_cast<uint16_t>(100);
    const long n = std::strtol(v, nullptr, 10);
    return static_cast<uint16_t>(n < 0 ? 0 : (n > 100 ? 100 : n));
  }();
  return pct;
}

HalPowerManager::Lock::Lock() {}
HalPowerManager::Lock::~Lock() {}
