#pragma once

#include "esp_err.h"
#include "esp_partition.h"

#include "SimulatorDeviceTruth.h"

// S-001: this returned nullptr unconditionally, and every caller reads that as
// "no next-update partition" -- so SdFirmwareUpdateActivity.cpp:92 printed
// "Invalid firmware" before reading a byte of the file, FirmwareFlasher.cpp:262
// returned NO_PARTITION, and OtaUpdater.cpp:135 never got as far as a write. The
// firmware's whole image-validation path (header, segment table, XOR checksum,
// SHA256 trailer) sits BEHIND this call and was therefore unreachable.
//
// CROSSPOINT_SIM_OTA_PARTITION=1 hands back a real one, sized like the X3's OTA
// slot. The write side deliberately stays honest: esp_partition_write() and
// esp_partition_erase_range() still return ESP_FAIL, which is a failure mode the
// firmware handles and reports, so nothing here pretends a flash succeeded. What
// the partition unlocks is everything up to the first byte written -- which is
// where all the validation lives.
inline const esp_partition_t *esp_ota_get_next_update_partition(const esp_partition_t *) {
  if (!simtruth::otaPartitionEnabled()) return nullptr;
  // These four numbers are READ OFF the firmware's own partitions.csv, not
  // chosen -- `app1, app, ota_1, 0x650000, 0x640000`. Inventing them is not a
  // harmless approximation: the first version of this shim guessed a 0x1F0000
  // slot, and the very first real image put on the card (4,492,880 bytes) came
  // back "firmware exceeds partition (2031616 bytes)". That is a NEW wrong
  // answer in place of the old one -- every genuine build would fail validation
  // for a reason no device has. If the partition table changes, change these.
  static const esp_partition_t slot = [] {
    esp_partition_t p{};
    p.type = ESP_PARTITION_TYPE_APP;
    p.subtype = ESP_PARTITION_SUBTYPE_APP_OTA_1;
    p.address = 0x650000u;
    p.size = 0x640000u;
    std::snprintf(p.label, sizeof(p.label), "app1");
    return p;
  }();
  return &slot;
}

inline esp_err_t esp_ota_mark_app_valid_cancel_rollback() {
  return ESP_OK;
}
