#pragma once

#include "esp_err.h"

#include <cstdint>
#include <cstring>

typedef enum {
  ESP_MAC_WIFI_STA,
  ESP_MAC_WIFI_SOFTAP,
  ESP_MAC_BT,
  ESP_MAC_ETH,
  ESP_MAC_IEEE802154,
  ESP_MAC_BASE,
  ESP_MAC_EFUSE_FACTORY,
  ESP_MAC_EFUSE_CUSTOM,
  ESP_MAC_EFUSE_EXT,
} esp_mac_type_t;

static const uint8_t SIMULATOR_MAC[6] = {0xDE, 0xAD, 0xBE, 0xEF, 0x00, 0x01};

// Simulator stub: return a fixed fake MAC address
static inline esp_err_t esp_efuse_mac_get_default(uint8_t mac[6]) {
  if (!mac) return ESP_ERR_INVALID_ARG;
  memcpy(mac, SIMULATOR_MAC, sizeof(SIMULATOR_MAC));
  return ESP_OK;
}

// The interface the firmware actually calls now. Upstream #2960 ("MAC address
// reading when WiFi is off") reads the MAC via esp_read_mac() instead of the
// efuse default above, because on device the two are not the same address.
// This shim reports the one fixed address, which is all a simulator with no
// radio can offer, and keeps `pio run -e simulator` building against current
// firmware. Only ESP_MAC_WIFI_STA is answered — that is the only type the
// firmware asks for (WifiSelectionActivity.cpp:66, :425).
//
// esp_err.h is included rather than assumed: WifiSelectionActivity includes
// only <esp_mac.h>, so without it esp_err_t and ESP_OK are undeclared at the
// call site even though the simulator defines them elsewhere. That is exactly
// how this broke — six errors, all "undeclared identifier".
static inline esp_err_t esp_read_mac(uint8_t mac[6], esp_mac_type_t type) {
  if (type != ESP_MAC_WIFI_STA) return ESP_ERR_INVALID_ARG;
  return esp_efuse_mac_get_default(mac);
}
