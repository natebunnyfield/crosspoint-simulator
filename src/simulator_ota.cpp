#include <Logging.h>

#if __has_include(<AppVersion.h>)
#include <AppVersion.h>
#endif

#ifdef CROSSINK_VERSION
#include <atomic>
#endif

#include "SimulatorDeviceTruth.h"
#include "network/OtaUpdater.h"

// S-001: checkForUpdate() was pinned to NO_UPDATE, so the available -> download
// -> install flow could not start. CROSSPOINT_SIM_OTA=available|error picks the
// verdict, CROSSPOINT_SIM_OTA_VERSION names the release, and
// CROSSPOINT_SIM_OTA_INSTALL=ok|error|cancel picks how the install ends. Default
// is the historical NO_UPDATE, so existing runs are unchanged.
//
// WORTH KNOWING BEFORE SPENDING TIME HERE: nothing in this fork calls
// OtaUpdater. Grepped 2026-08-16 across src/, lib/ and freeink-sdk/ -- the only
// references are its own header and .cpp. The one firmware-update path a user
// can actually reach is SdFirmwareUpdateActivity (SD card), which goes through
// esp_ota_get_next_update_partition() + FirmwareFlasher instead. So this stub
// now answers honestly, but the row in S-001 that called the network flow
// unreachable was true for a second reason it did not state: there is no caller
// to reach it with. The partition fix in esp_ota_ops.h is the half that unlocks
// a screen someone can open.

bool OtaUpdater::isUpdateNewer() const {
  return simtruth::otaVerdict() == simtruth::OtaVerdict::Available;
}

const std::string &OtaUpdater::getLatestVersion() const {
  return simtruth::otaVersion();
}

OtaUpdater::OtaUpdaterError OtaUpdater::checkForUpdate() {
  switch (simtruth::otaVerdict()) {
    case simtruth::OtaVerdict::Available:
      latestVersion = simtruth::otaVersion();
      otaUrl = "file:///sim/firmware.bin";
      otaSize = 1u << 20;  // a plausible ~1 MB image
      totalSize = otaSize;
      updateAvailable = true;
      LOG_INF("OTA", "[SIM] reporting update available: %s (%zu bytes)", latestVersion.c_str(), otaSize);
      return OK;
    case simtruth::OtaVerdict::Error:
      LOG_INF("OTA", "[SIM] reporting HTTP_ERROR for the release check");
      return HTTP_ERROR;
    case simtruth::OtaVerdict::NoUpdate:
      break;
  }
  LOG_DBG("OTA", "[SIM] OTA check is non-destructive; reporting no update");
  return NO_UPDATE;
}

namespace {
// Drive the progress callback the way a real download does, so a caller's
// progress UI is exercised rather than jumping straight to 100%.
void reportProgress(OtaUpdater::ProgressCallback onProgress, void *ctx, size_t &processed,
                    size_t &total) {
  total = 1u << 20;
  for (int step = 1; step <= 10; step++) {
    processed = total * static_cast<size_t>(step) / 10;
    if (onProgress) onProgress(ctx);
  }
}
}  // namespace

#ifdef CROSSINK_VERSION
OtaUpdater::OtaUpdaterError
OtaUpdater::installUpdate(ProgressCallback onProgress, void *ctx,
                          std::atomic<bool> *cancelRequested) {
  if (simtruth::otaVerdict() != simtruth::OtaVerdict::Available) {
    LOG_DBG("OTA", "[SIM] no update was reported; nothing to install");
    processedSize = 1;
    totalSize = 1;
    if (onProgress) onProgress(ctx);
    return INTERNAL_UPDATE_ERROR;
  }
  reportProgress(onProgress, ctx, processedSize, totalSize);
  if (cancelRequested && cancelRequested->load()) return CANCELLED_ERROR;
  switch (simtruth::otaInstall()) {
    case simtruth::OtaInstall::Ok:
      LOG_INF("OTA", "[SIM] install reported OK; no flash was written");
      return OK;
    case simtruth::OtaInstall::Cancelled:
      LOG_INF("OTA", "[SIM] install reported CANCELLED");
      return CANCELLED_ERROR;
    case simtruth::OtaInstall::Error:
      break;
  }
  LOG_INF("OTA", "[SIM] install reported INTERNAL_UPDATE_ERROR");
  return INTERNAL_UPDATE_ERROR;
}
#else
OtaUpdater::OtaUpdaterError
OtaUpdater::installUpdate(ProgressCallback onProgress, void *ctx) {
  if (simtruth::otaVerdict() != simtruth::OtaVerdict::Available) {
    LOG_DBG("OTA", "[SIM] no update was reported; nothing to install");
    processedSize = 1;
    totalSize = 1;
    if (onProgress) onProgress(ctx);
    return INTERNAL_UPDATE_ERROR;
  }
  reportProgress(onProgress, ctx, processedSize, totalSize);
  if (simtruth::otaInstall() == simtruth::OtaInstall::Ok) {
    LOG_INF("OTA", "[SIM] install reported OK; no flash was written");
    return OK;
  }
  LOG_INF("OTA", "[SIM] install reported INTERNAL_UPDATE_ERROR");
  return INTERNAL_UPDATE_ERROR;
}
#endif
