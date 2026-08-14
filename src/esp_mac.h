#pragma once
#include <cstdint>
#include <cstring>

#include "esp_err.h"

// Simulator stub: return a fixed fake MAC address
static inline int esp_efuse_mac_get_default(uint8_t mac[6]) {
  static const uint8_t fakeMac[6] = {0xDE, 0xAD, 0xBE, 0xEF, 0x00, 0x01};
  memcpy(mac, fakeMac, 6);
  return 0;
}

// The interface the firmware actually calls now. Upstream #2960 ("MAC address
// reading when WiFi is off") reads the MAC via esp_read_mac() instead of the
// efuse default above, because on device the two are not the same address.
// This shim reports the one fixed address for every type, which is all a
// simulator with no radio can offer, and keeps `pio run -e simulator` building
// against current firmware.
//
// esp_err.h is included rather than assumed: WifiSelectionActivity includes
// only <esp_mac.h>, so without it esp_err_t and ESP_OK are undeclared at the
// call site even though the simulator defines them elsewhere. That is exactly
// how this broke — six errors, all "undeclared identifier".
typedef enum {
  ESP_MAC_WIFI_STA = 0,
  ESP_MAC_WIFI_SOFTAP,
  ESP_MAC_BT,
  ESP_MAC_ETH,
} esp_mac_type_t;

static inline esp_err_t esp_read_mac(uint8_t* mac, esp_mac_type_t type) {
  (void)type;
  if (mac == nullptr) return -1;
  return esp_efuse_mac_get_default(mac) == 0 ? ESP_OK : -1;
}
