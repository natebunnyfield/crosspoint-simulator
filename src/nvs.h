#pragma once

#include <stdint.h>

#include "esp_err.h"

using nvs_handle_t = uint32_t;

constexpr int NVS_READONLY = 0;
constexpr int NVS_READWRITE = 1;

inline esp_err_t nvs_open(const char * /*name*/, int /*mode*/, nvs_handle_t *handle) {
  *handle = 1;
  return ESP_OK;
}

inline esp_err_t nvs_get_u8(nvs_handle_t /*handle*/, const char * /*key*/, uint8_t * /*value*/) { return ESP_FAIL; }
inline esp_err_t nvs_set_u8(nvs_handle_t /*handle*/, const char * /*key*/, uint8_t /*value*/) { return ESP_OK; }
inline esp_err_t nvs_commit(nvs_handle_t /*handle*/) { return ESP_OK; }
inline void nvs_close(nvs_handle_t /*handle*/) {}
