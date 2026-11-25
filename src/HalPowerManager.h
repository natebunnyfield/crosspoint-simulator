#pragma once

#include <Arduino.h>
#include <InputManager.h>
#include <Logging.h>
#include <freertos/semphr.h>

#include <cassert>

#include "HalGPIO.h"

class HalPowerManager;
extern HalPowerManager powerManager; // Singleton

class HalPowerManager {
  int normalFreq = 0; // MHz
  bool isLowPower = false;

  enum LockMode { None, NormalSpeed };
  LockMode currentLockMode = None;
  SemaphoreHandle_t modeMutex = nullptr; // Protect access to currentLockMode

public:
  static constexpr int LOW_POWER_FREQ = 10; // MHz
  // Upstream's light-sleep work (firmware #2525) replaced this with the four
  // constants below. This fork has not merged #2525, so main.cpp:818 still
  // reads IDLE_POWER_SAVING_MS -- dropping it breaks `pio run -e simulator`
  // outright. Both sets are kept so the shim builds against the fork's
  // firmware today and against #2525 whenever it lands.
  static constexpr unsigned long IDLE_POWER_SAVING_MS = 3000; // ms
  static constexpr unsigned long IDLE_DOWNCLOCK_MS = 500;
  static constexpr unsigned long IDLE_LIGHT_SLEEP_MS = 1000;
  static constexpr unsigned long BATTERY_POLL_MS = 1500;
  static constexpr unsigned long LIGHT_SLEEP_SLICE_MS = 50;
  static constexpr unsigned long BUSY_SLEEP_SLICE_MS = 20;

  void begin();

  // Control CPU frequency for power saving
  void setPowerSaving(bool enabled);

  bool lightSleep(const HalGPIO &) const {
    delay(50);
    return true;
  }
  bool onEinkBusyWaitSlice(int8_t, uint8_t) { return false; }
  void noteMainLoopIteration() {}
  void noteRenderWaitBegin() {}
  void noteRenderWaitEnd() {}

  // Setup wake up GPIO and enter deep sleep
  // Should be called inside main loop() to handle the currentLockMode
  // wakeOnHeldButton: the Picco's main.cpp passes whether its USB hold ended on
  // a held Power press (lib/hal/HalPowerManager.h:86). The host's deep-sleep
  // loop wakes on any press, so it changes nothing here.
  void startDeepSleep(HalGPIO &gpio, bool wakeOnHeldButton = false) const;

#if FREEINK_DEVICE_PICCO
  // Device: light-sleeps while USB powers the Picco so it can draw a charge
  // strip, returning true when Power ended the hold. The host has no charger
  // to watch and its deep-sleep loop is already the sleep, so it reports "no
  // USB hold" and main.cpp goes straight to that loop.
  bool holdWhileUsbPowered(HalGPIO &, void (*)(bool, uint16_t)) const {
    return false;
  }
#endif

  // Get battery percentage (range 0-100)
  uint16_t getBatteryPercentage() const;

  // RAII helper class to manage power saving locks
  // Usage: create an instance of Lock in a scope to disable power saving, for
  // example when running a task that needs full performance. When the Lock
  // instance is destroyed (goes out of scope), power saving will be re-enabled.
  class Lock {
    friend class HalPowerManager;
    bool valid = false;

  public:
    explicit Lock();
    ~Lock();

    // Non-copyable and non-movable
    Lock(const Lock &) = delete;
    Lock &operator=(const Lock &) = delete;
    Lock(Lock &&) = delete;
    Lock &operator=(Lock &&) = delete;
  };
};
