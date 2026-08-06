#include "Arduino.h"
#include "ESPmDNS.h"
#include "SimulatorNetworkPorts.h"
#include "WiFi.h"

#if defined(__APPLE__)
#include <arpa/inet.h> // htons
#include <dns_sd.h>
#define CROSSPOINT_SIM_HAS_BONJOUR 1
#else
#define CROSSPOINT_SIM_HAS_BONJOUR 0
#endif

// Deliberately NOT <Logging.h>. It does `#define Serial MySerialImpl::instance`,
// which rewrites this file's own `HWCDC Serial;` definition below into
// `HWCDC MySerialImpl::instance;` and fails to compile with a conflicting
// declaration. This TU owns the Serial global, so it cannot also consume the
// macro that renames it; stderr directly is the way out.
#include <cstdio>

class SPIClass {};
class FS {};
class HalStorage {};

ESPMock ESP;
HWCDC Serial;
SPIClass SPI;
FS SD;
HalStorage Storage;
WiFiClass WiFi;
MDNSClass MDNS;

// See ESPmDNS.h for why this publishes a service rather than claiming a
// hostname, and what that does and does not make reachable.

bool MDNSClass::begin(const char *hostname) {
#if CROSSPOINT_SIM_HAS_BONJOUR
  end();

  // Only advertise a server a peer can actually open. On desktop the servers
  // bind loopback by default, so publishing would point the network at a socket
  // that refuses every connection from it.
  if (!crosspoint_simulator::bindAllInterfaces()) {
    std::fprintf(stderr, "[MDNS] [SIM] not advertising: server is loopback-only\n");
    return false;
  }

  const uint16_t port =
      static_cast<uint16_t>(crosspoint_simulator::mapFirmwarePort(80));
  DNSServiceRef ref = nullptr;
  const DNSServiceErrorType err =
      DNSServiceRegister(&ref, /*flags=*/0, /*interfaceIndex=*/0,
                         hostname && hostname[0] ? hostname : "CrossPoint",
                         "_http._tcp", /*domain=*/nullptr, /*host=*/nullptr,
                         htons(port), /*txtLen=*/0, /*txtRecord=*/nullptr,
                         /*callBack=*/nullptr, /*context=*/nullptr);
  if (err != kDNSServiceErr_NoError) {
    std::fprintf(stderr, "[MDNS] [SIM] DNSServiceRegister failed: %d\n",
                 static_cast<int>(err));
    return false;
  }

  serviceRef_ = ref;
  // The name is what a browser sees, NOT a hostname that resolves. Logged in
  // that form so nobody reads the line as "crosspoint.local now works".
  std::fprintf(stderr, "[MDNS] [SIM] advertising %s._http._tcp on port %u\n",
               hostname ? hostname : "CrossPoint", static_cast<unsigned>(port));
  return true;
#else
  (void)hostname;
  return false;
#endif
}

void MDNSClass::end() {
#if CROSSPOINT_SIM_HAS_BONJOUR
  if (serviceRef_) {
    DNSServiceRefDeallocate(static_cast<DNSServiceRef>(serviceRef_));
    serviceRef_ = nullptr;
  }
#endif
}

void MDNSClass::addService(const char *service, const char *proto, int port) {
  // begin() already publishes _http._tcp on the mapped port, which is the only
  // service the firmware exposes. A second registration for the same service
  // would advertise a duplicate, so this stays a no-op rather than doing
  // something subtly wrong.
  (void)service;
  (void)proto;
  (void)port;
}
