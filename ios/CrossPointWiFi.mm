// iOS backend for sim_wifi_host: the real network the phone is on.
//
// The phone impersonates the X3's radio the way the pad impersonates its GPIO
// pins -- by supplying the RESULT the firmware expects (an associated station
// with an address) rather than the mechanism. What iOS will not expose is
// absent here rather than invented: there is no scan, and no soft AP. See
// ios/WIFI.md for why those have no implementation at any entitlement tier.
//
// Two APIs, because no single one answers everything:
//
//   * NWPathMonitor -- connectivity and interface type. No entitlement, updates
//     continuously, and it is the only one of the two that notices the network
//     dropping.
//   * NEHotspotNetwork.fetchCurrent -- SSID and signal strength. Needs the
//     Access WiFi Information entitlement plus Location permission, is
//     asynchronous, and returns nil on the iOS Simulator. That last point is
//     why the Simulator cannot QA this file.
//
// getifaddrs() supplies the address. Deliberately not restricted to en0: with
// Personal Hotspot up and no WiFi association the phone's own address lives on
// a bridge interface instead, and that is exactly the case the hotspot fallback
// exists for.

#include "SimWiFiHost.h"

#import <Foundation/Foundation.h>
#import <Network/Network.h>
#import <NetworkExtension/NetworkExtension.h>

#include <arpa/inet.h>
#include <ifaddrs.h>
#include <net/if.h>
#include <sys/socket.h>

#include <atomic>
#include <mutex>
#include <string>

namespace sim_wifi_host {
namespace {

std::mutex g_mutex;
Network g_current;
std::atomic<bool> g_started{false};

// Normalised 0..1 -> dBm. The firmware's barsForRssi() bands at -85/-75/-65/-55
// rising and -88/-78/-68/-58 falling, so the range has to span that with room
// at both ends for the hysteresis to have somewhere to sit. -100..-40 does.
//
// The absolute number is synthesised, but it is a monotone function of a real
// measurement: the bars move when the signal moves and at no other time, which
// is the whole of what that UI claims. Reporting a constant would have been the
// alternative, and a gauge that never moves is worse than a rescaled one.
int dbmFromStrength(double strength) {
  if (strength < 0.0) strength = 0.0;
  if (strength > 1.0) strength = 1.0;
  return static_cast<int>(-100.0 + strength * 60.0);
}

// First usable IPv4 on a non-loopback, running interface, preferring en0.
//
// The preference matters and the fallback matters more: en0 is the WiFi station
// address in the normal case, but under Personal Hotspot the phone is not
// associated with anything and its address is on the hotspot bridge. Treating a
// missing en0 as "no address" would blank the one screen the fallback exists to
// serve.
bool copyLocalIPv4(uint8_t out[4]) {
  ifaddrs *list = nullptr;
  if (getifaddrs(&list) != 0 || !list) return false;

  bool found = false;
  bool foundPreferred = false;

  for (ifaddrs *ifa = list; ifa != nullptr; ifa = ifa->ifa_next) {
    if (!ifa->ifa_addr || ifa->ifa_addr->sa_family != AF_INET) continue;
    if (!(ifa->ifa_flags & IFF_UP) || !(ifa->ifa_flags & IFF_RUNNING)) continue;
    if (ifa->ifa_flags & IFF_LOOPBACK) continue;

    const auto *addr = reinterpret_cast<const sockaddr_in *>(ifa->ifa_addr);
    const uint32_t host = ntohl(addr->sin_addr.s_addr);
    if (host == 0) continue;

    const bool preferred = ifa->ifa_name && std::string(ifa->ifa_name) == "en0";
    if (found && !preferred) continue;

    out[0] = static_cast<uint8_t>((host >> 24) & 0xFF);
    out[1] = static_cast<uint8_t>((host >> 16) & 0xFF);
    out[2] = static_cast<uint8_t>((host >> 8) & 0xFF);
    out[3] = static_cast<uint8_t>(host & 0xFF);
    found = true;
    foundPreferred = preferred;
    if (foundPreferred) break;
  }

  freeifaddrs(list);
  return found;
}

// SSID and signal strength. Asynchronous, so it writes into the cache rather
// than returning; callers read the cache. Both fields stay untouched on
// failure, so a transient denial does not blank a good reading.
void refreshHotspotInfo() {
  [NEHotspotNetwork fetchCurrentWithCompletionHandler:^(NEHotspotNetwork *network) {
    if (!network) return;
    std::lock_guard<std::mutex> lock(g_mutex);
    g_current.ssid = network.SSID ? std::string(network.SSID.UTF8String) : std::string();
    g_current.rssiDbm = dbmFromStrength(network.signalStrength);
  }];
}

}  // namespace

bool available() { return true; }

void begin() {
  // Idempotent: the firmware reaches WiFi through several entry points and any
  // of them may be first. exchange() rather than a check-then-set so two task
  // threads racing here cannot both start a monitor.
  if (g_started.exchange(true)) return;

  nw_path_monitor_t monitor = nw_path_monitor_create();
  nw_path_monitor_set_queue(
      monitor, dispatch_get_global_queue(QOS_CLASS_UTILITY, 0));
  nw_path_monitor_set_update_handler(monitor, ^(nw_path_t path) {
    const bool satisfied = nw_path_get_status(path) == nw_path_status_satisfied;
    const bool wifi = nw_path_uses_interface_type(path, nw_interface_type_wifi);

    {
      std::lock_guard<std::mutex> lock(g_mutex);
      g_current.connected = satisfied;
      g_current.isWifi = wifi;
      g_current.hasIpv4 = satisfied && copyLocalIPv4(g_current.ipv4);
      if (!satisfied) {
        g_current.ssid.clear();
        g_current.rssiDbm = 0;
      }
    }

    // The path change is the signal that the SSID may have changed too;
    // fetchCurrent has no callback of its own.
    if (satisfied && wifi) refreshHotspotInfo();
  });
  nw_path_monitor_start(monitor);
}

Network current() {
  begin();  // first caller wins; every later one is a no-op
  std::lock_guard<std::mutex> lock(g_mutex);
  return g_current;
}

}  // namespace sim_wifi_host
