#pragma once

#include "esp_err.h"

enum wifi_ps_type_t {
  WIFI_PS_NONE = 0,
  WIFI_PS_MIN_MODEM = 1,
  WIFI_PS_MAX_MODEM = 2,
};

inline esp_err_t esp_wifi_set_ps(wifi_ps_type_t) { return ESP_OK; }
// HttpDownloader's power-save guard reads the mode before a download so it can
// put it back afterwards. The host has no radio, so it reports the IDF default.
inline esp_err_t esp_wifi_get_ps(wifi_ps_type_t* type) {
  if (type) *type = WIFI_PS_MIN_MODEM;
  return ESP_OK;
}
inline esp_err_t esp_wifi_stop() { return ESP_OK; }
