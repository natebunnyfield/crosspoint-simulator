// iOS backend for sim_host_battery: the phone's own battery, shown in the
// firmware's header instead of the simulator's flat 100 %.
//
// Why it exists: the emulated e-ink header draws a battery icon and a
// percentage a few millimetres below iOS's status bar, which draws the real
// one. Until now the two disagreed on every device -- the HAL stub answered
// 100 % and "charging" forever (S-001's fix gave it env vars, which a phone
// has no way to set).
//
// EVERYTHING HERE RUNS ON THE MAIN THREAD. `UIDevice` is main-thread-only, and
// the firmware asks for the battery from its render task, so this file never
// answers a question -- it only ever pushes. `sim_host_battery` holds the
// atomics the render task reads. Same split, and the same reason, as the
// appearance and keyboard adapters.
//
// THE SIMULATOR REPORTS -1. `batteryLevel` is -1 and `batteryState` is Unknown
// on an iOS Simulator unless the device menu has been used to set them, so the
// publish below passes those straight through as "unknown" and the firmware
// falls back to exactly the behaviour it had before this file existed. That is
// deliberate: a simulator run should keep rendering the reproducible 100 %
// every screenshot in this repo was captured against.

#include "CrossPointHostBattery.h"

#import <UIKit/UIKit.h>

#include <SDL3/SDL.h>

#include "SimHostBattery.h"

namespace {

// UIKit's level is 0.0-1.0 and -1.0 when unknown. Rounding rather than
// truncating, because the firmware prints this number next to iOS's own and
// truncation would show 87 % against the status bar's 88 % for most of every
// percent.
int percentFromDevice(UIDevice *device) {
  const float level = device.batteryLevel;
  if (level < 0.0f) return -1;
  const int pct = static_cast<int>(level * 100.0f + 0.5f);
  return pct < 0 ? 0 : (pct > 100 ? 100 : pct);
}

// 1 charging, 0 on battery, -1 unknown.
//
// FULL COUNTS AS CHARGING, because it means the cable is in -- and the cable is
// exactly what the firmware's bolt is drawing (LyraTheme::fillBatteryIcon asks
// gpio.isUsbConnected(), not the percentage). A phone at 100 % on the charger
// showing no bolt would be the same disagreement this file exists to end.
int chargingFromDevice(UIDevice *device) {
  switch (device.batteryState) {
    case UIDeviceBatteryStateCharging:
    case UIDeviceBatteryStateFull:
      return 1;
    case UIDeviceBatteryStateUnplugged:
      return 0;
    case UIDeviceBatteryStateUnknown:
    default:
      return -1;
  }
}

void publishNow() {
  UIDevice *device = UIDevice.currentDevice;
  const int pct = percentFromDevice(device);
  const int chg = chargingFromDevice(device);
  sim_host_battery::publish(pct, chg);
}

}  // namespace

void CrossPointHostBattery_start(void) {
  static bool started = false;
  if (started) return;
  started = true;

  UIDevice *device = UIDevice.currentDevice;
  // Without this `batteryLevel` is -1 and `batteryState` is Unknown, and the
  // two notifications below never fire. It costs nothing to leave on for the
  // app's lifetime and there is no matching teardown, which is why there is no
  // stop().
  device.batteryMonitoringEnabled = YES;

  NSNotificationCenter *center = NSNotificationCenter.defaultCenter;
  for (NSNotificationName name in @[ UIDeviceBatteryLevelDidChangeNotification,
                                     UIDeviceBatteryStateDidChangeNotification ]) {
    [center addObserverForName:name
                        object:device
                         queue:NSOperationQueue.mainQueue
                    usingBlock:^(NSNotification *) {
                      publishNow();
                    }];
  }

  // The first reading. Enabling monitoring populates the properties
  // synchronously, but the level notification only fires on a CHANGE -- iOS
  // posts it at 1 % granularity and a charging phone can sit on one level for
  // minutes -- so without this the header would keep the stub's 100 % until
  // the battery happened to move.
  publishNow();
  SDL_Log("[battery] host battery monitoring on: %d%%, charging %d",
          sim_host_battery::percent(), sim_host_battery::charging());
}
