#include "HalPowerManager.h"

#include "HalGPIO.h"

#include "SimHostBattery.h"

#include <cstdlib>

HalPowerManager powerManager;

void HalPowerManager::begin() {}
void HalPowerManager::startDeepSleep(HalGPIO &gpio) const { gpio.startDeepSleep(); }
void HalPowerManager::setPowerSaving(bool enable) {}
// A flat 100% meant the low-battery paths -- the warning, the sleep-screen
// battery art, anything gated on a threshold -- could not run (S-001).
// CROSSPOINT_SIM_BATTERY=<0-100> sets it; unset keeps the old 100 so every
// existing screenshot run is unchanged.
//
// On a phone the HOST's own battery is published into sim_host_battery and
// wins over both, because the firmware's header sits a few millimetres from
// iOS's status bar and the two showing different numbers is the bug. The
// resolution order and why the env var is no longer latched into a static:
// src/SimHostBattery.h.
uint16_t HalPowerManager::getBatteryPercentage() const {
  return static_cast<uint16_t>(sim_host_battery::resolvedPercent());
}

HalPowerManager::Lock::Lock() {}
HalPowerManager::Lock::~Lock() {}
