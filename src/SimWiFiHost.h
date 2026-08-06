#pragma once

// Host-provided WiFi facts, for platforms where the simulator sits on a real
// radio instead of inventing one.
//
// This is a free-function hook, deliberately NOT extra methods on WiFiClass --
// the same reasoning as SimulatorOverlay.h. WiFiClass mirrors the Arduino
// WiFi API the firmware compiles against, and "ask the host what network it is
// actually on" has no analog there. Keeping it outside means the public surface
// the firmware links against does not move.
//
// The contract is deliberately narrow. `available()` answers "is there a real
// radio behind this?" and gates everything else: when it is false -- every
// platform but iOS today -- WiFiClass keeps its existing env-var-driven
// behaviour verbatim, so CROSSPOINT_SIM_WIFI_* stays the QA harness for the
// firmware's failure branches and the desktop build cannot regress.
//
// See ios/WIFI.md for what iOS can and cannot answer, and why scanning and
// soft-AP are absent rather than faked.

#include <cstdint>
#include <string>

#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif

// Overridable so the host branch can be exercised off-device: the real backend
// is iOS-only and cannot be compiled or run on Linux, which would otherwise
// leave the branch WiFiClass takes on a phone with no test at all.
// tests/wifi_host_test.cpp defines this and supplies its own backend.
#ifndef CROSSPOINT_SIM_HOST_WIFI
#if defined(__APPLE__) && TARGET_OS_IPHONE
#define CROSSPOINT_SIM_HOST_WIFI 1
#else
#define CROSSPOINT_SIM_HOST_WIFI 0
#endif
#endif

namespace sim_wifi_host {

// What the host knows about the one network it is on. There is never more than
// one: iOS exposes the current association and nothing else, which is why
// scanning is absent from this interface rather than returning an empty list.
struct Network {
  bool connected = false;
  bool isWifi = false;  // false => satisfied over cellular/wired
  std::string ssid;     // empty when the entitlement or permission is missing
  int rssiDbm = 0;      // synthesised from a normalised strength; see current()
  uint8_t ipv4[4] = {0, 0, 0, 0};
  bool hasIpv4 = false;
};

#if CROSSPOINT_SIM_HOST_WIFI

// True when a real radio backs these answers.
bool available();

// The current association, or a default-constructed Network when offline.
//
// Cached: the iOS call behind the SSID and signal strength is asynchronous
// while WiFiClass::RSSI() is not, so this returns the last known values and a
// background refresh keeps them current. The firmware polls RSSI once a second
// on the file-transfer screen, so staleness of a second or two is invisible.
Network current();

// Start the background refresh. Idempotent; safe to call from any thread.
void begin();

#else

// Non-iOS: no host radio, and every call folds to a constant the optimiser can
// see through, so WiFiClass's existing branches survive unchanged.
inline bool available() { return false; }
inline Network current() { return Network{}; }
inline void begin() {}

#endif

}  // namespace sim_wifi_host
