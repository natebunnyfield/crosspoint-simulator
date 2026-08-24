// Covers the branch WiFiClass takes when a real radio is behind it -- the iOS
// path -- plus a guard that the desktop path is untouched by its presence.
//
// This test exists because the real backend (ios/CrossPointWiFi.mm) is
// iOS-only: it cannot be compiled, let alone run, anywhere else, and there is
// no paired device. Without this the phone's branch would ship with no
// coverage at all. So SimWiFiHost.h lets CROSSPOINT_SIM_HOST_WIFI be forced on
// and this file supplies a scriptable backend in place of NWPathMonitor and
// NEHotspotNetwork.
//
// What it does NOT cover: whether iOS reports what we think it reports.
// Interface selection, entitlement failures and signal-strength granularity are
// device-verify items in ios/WIFI.md, not testable here.
//
//   c++ -std=c++20 -Isrc -DCROSSPOINT_SIM_HOST_WIFI=1
//       tests/wifi_host_test.cpp -o /tmp/wifi_host_test && /tmp/wifi_host_test

#include "SimWiFiHost.h"

#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>

#if !CROSSPOINT_SIM_HOST_WIFI
#error "build with -DCROSSPOINT_SIM_HOST_WIFI=1; see the header comment"
#endif

// Stand-in backend. The real one is asynchronous and cached; this is the same
// shape with the scheduling removed.
namespace sim_wifi_host {
namespace {
Network g_scripted;
bool g_availableFlag = true;
}  // namespace

bool available() { return g_availableFlag; }
Network current() { return g_scripted; }
void begin() {}

void testSetNetwork(const Network &n) { g_scripted = n; }
void testSetAvailable(bool v) { g_availableFlag = v; }
}  // namespace sim_wifi_host

#include "WiFi.h"
#include "TestCheck.h"
using testcheck::expect;

WiFiClass WiFi;

namespace {

sim_wifi_host::Network onWifi(const char *ssid, int dbm) {
  sim_wifi_host::Network n;
  n.connected = true;
  n.isWifi = true;
  n.ssid = ssid;
  n.rssiDbm = dbm;
  n.ipv4[0] = 192;
  n.ipv4[1] = 168;
  n.ipv4[2] = 1;
  n.ipv4[3] = 42;
  n.hasIpv4 = true;
  return n;
}

// On WiFi the "scan" reports exactly the one real network, so the firmware's
// list has a true row to show and its saved-network match has something to hit.
void testOnWifiReportsOneRealNetwork() {
  sim_wifi_host::testSetNetwork(onWifi("Home Network", -58));

  expect(WiFi.scanNetworks() == 1, "scan reports one network");
  expect(WiFi.scanComplete() == 1, "scanComplete agrees with scanNetworks");
  expect(std::string(WiFi.SSID(0).c_str()) == "Home Network", "row 0 is the real SSID");
  expect(WiFi.RSSI(0) == -58, "row 0 carries the real signal");
  expect(std::string(WiFi.SSID().c_str()) == "Home Network", "current SSID");
  expect(WiFi.RSSI() == -58, "current RSSI");
  expect(WiFi.status() == WL_CONNECTED, "connected");

  // The address the firmware paints and QR-encodes for a peer. 127.0.0.1 here
  // would make the file-transfer screen useless, which is the bug this exists
  // to prevent.
  expect(std::string(WiFi.localIP().toString().c_str()) == "192.168.1.42",
         "localIP is the real LAN address, not loopback");

  // There is no second network to describe, ever.
  expect(std::string(WiFi.SSID(1).c_str()).empty(), "no row 1");
  expect(WiFi.RSSI(1) == 0, "no signal for a row that does not exist");
}

// The firmware turns encryptionType into "prompt the user for a password"
// (WifiSelectionActivity.cpp:165 -> 223). On a host radio no password can be
// used -- begin() cannot change an association iOS already made -- so anything
// other than OPEN stops the join behind a mandatory secret that is then
// discarded. This is the difference between a one-step join and a dead end.
void testTheJoinNeverAsksForAPassword() {
  sim_wifi_host::testSetNetwork(onWifi("Home Network", -58));
  expect(WiFi.encryptionType(0) == WIFI_AUTH_OPEN,
         "the current network needs no credential from the user");
}

// begin() is a status read, not an action: the app cannot change the phone's
// association, so asking for another network must not make it claim to be on
// one.
void testBeginDoesNotInventTheRequestedNetwork() {
  sim_wifi_host::testSetNetwork(onWifi("Home Network", -58));

  expect(WiFi.begin("Some Other Network", "hunter2") == WL_CONNECTED,
         "begin reports the real status");
  expect(std::string(WiFi.SSID().c_str()) == "Home Network",
         "begin did not adopt the SSID it was handed");
}

// Off WiFi there is nothing true to report. WIFI_SCAN_FAILED is what
// WifiSelectionActivity already handles, by offering manual SSID entry.
void testOffWifiFailsTheScanHonestly() {
  sim_wifi_host::Network cellular;
  cellular.connected = true;
  cellular.isWifi = false;
  sim_wifi_host::testSetNetwork(cellular);
  expect(WiFi.scanNetworks() == WIFI_SCAN_FAILED, "cellular fails the scan");

  sim_wifi_host::testSetNetwork(sim_wifi_host::Network{});
  expect(WiFi.scanNetworks() == WIFI_SCAN_FAILED, "offline fails the scan");
  expect(WiFi.status() == WL_DISCONNECTED, "offline is disconnected");
  expect(std::string(WiFi.localIP().toString().c_str()) == "0.0.0.0",
         "no address when offline");

  // Associated but SSID withheld (entitlement or Location denied) is not a
  // network we can put in a list -- the row would have no name.
  sim_wifi_host::Network nameless = onWifi("", -58);
  sim_wifi_host::testSetNetwork(nameless);
  expect(WiFi.scanNetworks() == WIFI_SCAN_FAILED,
         "a nameless association is not a listable network");
}

// An app cannot raise an access point on iOS. The firmware already handles a
// false return; the menu entry is gated off besides.
void testSoftApRefuses() {
  sim_wifi_host::testSetNetwork(onWifi("Home Network", -58));
  expect(WiFi.softAP("CrossPoint-Reader") == false, "softAP refuses");
}

// The whole hook is gated on available(); with it false, every desktop branch
// must behave exactly as it did before this file existed.
void testDesktopPathIsUntouched() {
  sim_wifi_host::testSetAvailable(false);

  expect(WiFi.begin("anything") == WL_CONNECTED, "desktop begin connects");
  expect(WiFi.scanNetworks() == 2, "desktop scan returns the built-in pair");
  expect(WiFi.RSSI() == -45, "desktop RSSI");
  expect(WiFi.RSSI(1) == -62, "desktop scan-row RSSI");
  expect(std::string(WiFi.localIP().toString().c_str()) == "127.0.0.1",
         "desktop localIP stays loopback");
  expect(WiFi.softAP("ap") == true, "desktop softAP still succeeds");

  sim_wifi_host::testSetAvailable(true);
}

}  // namespace

int main() {
  testOnWifiReportsOneRealNetwork();
  testTheJoinNeverAsksForAPassword();
  testBeginDoesNotInventTheRequestedNetwork();
  testOffWifiFailsTheScanHonestly();
  testSoftApRefuses();
  testDesktopPathIsUntouched();
  std::printf("wifi_host_test: all checks passed\n");
  return 0;
}
