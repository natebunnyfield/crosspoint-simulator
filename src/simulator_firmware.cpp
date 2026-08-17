#include <Logging.h>

#include "network/FirmwareFlasher.h"
#include "network/OtaBootSwitch.h"

// S-014: only the WRITE half is stubbed now.
//
// `validateImageFile()` and `resultName()` used to be faked here, because they
// shared a translation unit with the flasher and the firmware's
// `build_src_filter` had to drop the whole file. The firmware split the
// read-only half into `network/FirmwareImageValidator.cpp`, so the REAL
// validator now compiles into this build and runs against a real file on the
// simulated card -- magic, segment table, XOR checksum and SHA256 trailer, the
// last of which needs the mbedtls shim to be a genuine SHA-256 (it was an XOR
// fold until 2026-08-16; see src/mbedtls/sha256.h).
//
// What stays stubbed is everything that would write: `flashFromSdPath()` here,
// and `ota_boot::switchTo()` below. Those fail honestly rather than pretending,
// which is a failure mode the firmware already handles and reports.
namespace firmware_flash {
Result flashFromSdPath(const char *, ProgressCb onProgress, void *ctx, bool) {
  LOG_DBG("FLASH",
          "[SIM] Firmware flashing is not supported in the native simulator");
  if (onProgress)
    onProgress(1, 1, ctx);
  return Result::WRITE_FAIL;
}
} // namespace firmware_flash

namespace ota_boot {
uint32_t computeSeqCrc(uint32_t) { return 0; }
bool switchTo(const esp_partition_t *) {
  LOG_DBG("FLASH", "[SIM] Boot partition switching is not supported in the "
                   "native simulator");
  return false;
}
} // namespace ota_boot
