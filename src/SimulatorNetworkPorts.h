#pragma once

#include <cerrno>
#include <cstdint>
#include <cstdlib>
#include <cstring>

#include <netinet/in.h>

#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif

namespace crosspoint_simulator {

inline int httpPort() {
  constexpr int DEFAULT_HTTP_PORT = 8080;
  constexpr int MIN_UNPRIVILEGED_PORT = 1024;
  constexpr int MAX_HTTP_PORT = 65534;

  const char *configured = std::getenv("CROSSPOINT_SIM_HTTP_PORT");
  if (!configured || !*configured)
    return DEFAULT_HTTP_PORT;

  errno = 0;
  char *end = nullptr;
  const long parsed = std::strtol(configured, &end, 10);
  if (errno != 0 || end == configured || *end != '\0' ||
      parsed < MIN_UNPRIVILEGED_PORT || parsed > MAX_HTTP_PORT) {
    return DEFAULT_HTTP_PORT;
  }
  return static_cast<int>(parsed);
}

inline int mapFirmwarePort(int firmwarePort) {
  if (firmwarePort == 80)
    return httpPort();
  if (firmwarePort == 81)
    return httpPort() + 1;
  return firmwarePort;
}

// Which interfaces the firmware's servers listen on.
//
// Loopback is the right default on a desktop: the simulator's web UI is a
// development convenience and binding 0.0.0.0 would publish a file browser onto
// whatever network the developer's machine is sitting on. On a phone it is the
// opposite -- the whole point of the file-transfer screen is that a peer on the
// same WiFi reaches it, and a loopback-only server is reachable by nothing.
//
// So the default is keyed on platform, and CROSSPOINT_SIM_BIND_ALL overrides
// either way ("0" forces loopback, anything else non-empty forces all).
inline bool bindAllInterfaces() {
  const char *configured = std::getenv("CROSSPOINT_SIM_BIND_ALL");
  if (configured && *configured)
    return std::strcmp(configured, "0") != 0;
#if defined(__APPLE__) && TARGET_OS_IPHONE
  return true;
#else
  return false;
#endif
}

inline uint32_t bindAddressHostOrder() {
  return bindAllInterfaces() ? INADDR_ANY : INADDR_LOOPBACK;
}

// For log lines, so a failed bind names the address it actually tried.
inline const char *bindAddressLabel() {
  return bindAllInterfaces() ? "0.0.0.0" : "127.0.0.1";
}

} // namespace crosspoint_simulator
