#pragma once

// Bonjour advertisement for the firmware's web server.
//
// IMPORTANT, and it corrects an earlier assumption in ios/WIFI.md: this does
// NOT make `http://crosspoint.local/` resolve, and nothing an app can do will.
// ESP-IDF's mDNS claims a HOSTNAME; Bonjour's DNSServiceRegister publishes a
// SERVICE. The two are different records:
//
//   ESP32   MDNS.begin("crosspoint")  ->  crosspoint.local resolves to the device
//   Apple   DNSServiceRegister(...)   ->  crosspoint._http._tcp.local is browsable,
//                                         pointing at the host's OWN name
//                                         (Someones-iPhone.local), which is the
//                                         only hostname the device may claim
//
// Claiming an arbitrary .local hostname needs DNSServiceRegisterRecord against a
// name the daemon will not cede to an app, so the firmware's primary painted
// URL stays unreachable on Apple platforms. What this DOES buy is genuine
// discovery: the server shows up in Finder's Network, in Safari's Bonjour
// bookmarks, and under `dns-sd -B _http._tcp`. The reachable address remains
// the IP, which is why getting the port into the painted IP URL matters more
// than the hostname line does.
//
// Registration is deliberately tied to whether the server is actually reachable
// (crosspoint_simulator::bindAllInterfaces()): advertising a service that only
// listens on loopback would be an invitation to a connection that cannot work.

class MDNSClass {
public:
  bool begin(const char *hostname);
  void end();
  void addService(const char *service, const char *proto, int port);

private:
  void *serviceRef_ = nullptr;  // DNSServiceRef; void* to keep dns_sd.h out of
                                // every translation unit that includes this.
};
extern MDNSClass MDNS;
