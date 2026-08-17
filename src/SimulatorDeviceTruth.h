#pragma once

#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <string>

#include "SimulatorRebootResets.h"

// The four remaining reversals from S-001: places where this simulator answered
// the OPPOSITE of the hardware, so a firmware path looked exercised when it had
// never once run.
//
// THE PROBLEM THESE SOLVE. The simulator is the project's only pre-device gate.
// A stub that returns the safe-looking answer does not merely fail to test a
// branch -- it reports the branch as covered. Four of those survived the
// 2026-08-08 pass that fixed the heap and the battery:
//
//   supportsAsyncRefresh() -> false      device: supported. The overlapped page
//                                        turn (EpubReaderActivity.cpp:1593) has
//                                        never executed in a simulator run.
//   isRebootFromPanic()    -> false      device: 225 lines of panic capture.
//                                        CrashActivity compiles in and cannot
//                                        be entered (main.cpp:828).
//   next update partition  -> nullptr    device: valid. SD firmware update says
//                                        "Invalid firmware" before reading a
//                                        byte (SdFirmwareUpdateActivity.cpp:92).
//   OTA check              -> NO_UPDATE  device: a real check. The whole
//                                        available -> download -> install flow
//                                        is unreachable.
//
// OPT-IN, always, and for the same reason the heap budget is: the default has to
// stay byte-for-byte what every existing headless script and screenshot run
// already sees. Turning device-truth on is a thing a test asks for.
//
//   CROSSPOINT_SIM_ASYNC_REFRESH=1        overlapped page turn is available
//   CROSSPOINT_SIM_PANIC=<reason>         this boot follows a panic with <reason>
//   CROSSPOINT_SIM_OTA_PARTITION=1        a real next-update partition exists
//   CROSSPOINT_SIM_OTA=none|available|error
//   CROSSPOINT_SIM_OTA_VERSION=<string>   what the check reports as latest
//   CROSSPOINT_SIM_OTA_INSTALL=error|ok|cancel
//
// THE PANIC LATCH FIRES ONCE, which is not a nicety. On hardware a panic reboot
// is followed by a NORMAL boot: esp_reset_reason() reads ESP_RST_PANIC on the
// boot after the crash and something else on the boot after that. Here the state
// lives in an env var that the desktop reboot (execvp) would hand straight to
// the child, so CROSSPOINT_SIM_PANIC=... would route every boot into
// CrashActivity forever and never let go. latchPanic() therefore unsetenv()s on
// the first read -- unsetenv edits `environ`, which is what execvp passes on --
// and registers a simreset for the iOS longjmp path, which never re-reads env at
// all. One panic, then the device recovers, exactly as the hardware does.
//
// The decisions are pure functions so tests/device_truth_test.cpp can assert on
// them without an environment: every failure mode here is a stub quietly telling
// the truth's opposite, which no compiler and no screenshot can see.
namespace simtruth {

// ---------------------------------------------------------------- pure part

enum class OtaVerdict : uint8_t { NoUpdate, Available, Error };
enum class OtaInstall : uint8_t { Error, Ok, Cancelled };

// Unknown text is NOT an error: it falls back to the historical answer, so a
// typo in a script degrades to the old behaviour rather than inventing a state
// the firmware then has to survive.
inline OtaVerdict otaVerdictFrom(const char *s) {
  if (!s || !*s) return OtaVerdict::NoUpdate;
  if (std::strcmp(s, "available") == 0) return OtaVerdict::Available;
  if (std::strcmp(s, "error") == 0) return OtaVerdict::Error;
  return OtaVerdict::NoUpdate;
}

inline OtaInstall otaInstallFrom(const char *s) {
  if (!s || !*s) return OtaInstall::Error;
  if (std::strcmp(s, "ok") == 0) return OtaInstall::Ok;
  if (std::strcmp(s, "cancel") == 0) return OtaInstall::Cancelled;
  return OtaInstall::Error;
}

// "1"/"true"/"yes"/"on" are true; everything else, including "0" and unset, is
// false. Same spelling the other CROSSPOINT_SIM_* flags in this repo accept.
inline bool flagFrom(const char *s) {
  if (!s || !*s) return false;
  return std::strcmp(s, "1") == 0 || std::strcmp(s, "true") == 0 ||
         std::strcmp(s, "yes") == 0 || std::strcmp(s, "on") == 0;
}

// esp_reset_reason_t value the firmware's isRebootFromPanic() tests for. Named
// here rather than magic-numbered at the call site because the sim has no
// esp_reset_reason() to read it from.
constexpr int kResetReasonPanic = 4;  // ESP_RST_PANIC

// The panic report, in the firmware's own format (lib/hal/HalSystem.cpp:197).
// `full` false is what CrashActivity shows on the panel -- the bare reason --
// and `full` true is what checkPanic() writes to /crash_report.txt.
//
// The stack frames are synthesised and DETERMINISTIC: a fake backtrace is more
// honest than an empty one (the firmware's writer, its rotation and the SD dump
// path all walk the frames, and an empty list skips them entirely), and a
// reproducible one is the only kind a test can assert on.
inline std::string panicReport(const char *reason, const char *version, bool full,
                               size_t stackDepth = 4) {
  const char *msg = (reason && *reason) ? reason : "Simulated panic";
  if (!full) return std::string(msg);

  std::string info;
  info += "CrossPoint version: ";
  info += (version && *version) ? version : "dev-simulator";

  char resetLine[40];
  std::snprintf(resetLine, sizeof(resetLine), "\nReset reason: %d", kResetReasonPanic);
  info += resetLine;

  info += "\n\nPanic reason: ";
  info += msg;
  info += "\n\nLast logs:\n";
  info += "[SIM] panic injected via CROSSPOINT_SIM_PANIC\n";
  info += "\n\nStack memory:\n";

  auto hex = [](uint32_t v) {
    char b[9];
    std::snprintf(b, sizeof(b), "%08X", v);
    return std::string(b);
  };
  // A plausible ESP32-C3 DRAM stack window, walking down 0x20 a frame.
  constexpr uint32_t kStackTop = 0x3FC98000u;
  for (size_t i = 0; i < stackDepth; i++) {
    const uint32_t sp = kStackTop - static_cast<uint32_t>(i) * 0x20u;
    info += "0x" + hex(sp) + ": ";
    for (size_t j = 0; j < 8; j++) {
      info += "0x" + hex(sp + static_cast<uint32_t>(j) * 4u) + " ";
    }
    info += "\n";
  }
  return info;
}

// --------------------------------------------------------------- env part

struct Config {
  bool asyncRefresh = false;
  bool otaPartition = false;
  OtaVerdict otaVerdict = OtaVerdict::NoUpdate;
  OtaInstall otaInstall = OtaInstall::Error;
  std::string otaVersion;

  Config() {
    asyncRefresh = flagFrom(std::getenv("CROSSPOINT_SIM_ASYNC_REFRESH"));
    otaPartition = flagFrom(std::getenv("CROSSPOINT_SIM_OTA_PARTITION"));
    otaVerdict = otaVerdictFrom(std::getenv("CROSSPOINT_SIM_OTA"));
    otaInstall = otaInstallFrom(std::getenv("CROSSPOINT_SIM_OTA_INSTALL"));
    if (const char *v = std::getenv("CROSSPOINT_SIM_OTA_VERSION")) otaVersion = v;
    if (otaVersion.empty()) otaVersion = "dev-simulator";
    // An `available` verdict with no partition to write to is a state the
    // hardware cannot be in, and it would strand the flow at install time with
    // a confusing error. Asking for the update implies the destination.
    if (otaVerdict == OtaVerdict::Available) otaPartition = true;
  }
};

inline const Config &config() {
  static const Config c;
  return c;
}

inline bool asyncRefreshEnabled() { return config().asyncRefresh; }
inline bool otaPartitionEnabled() { return config().otaPartition; }
inline OtaVerdict otaVerdict() { return config().otaVerdict; }
inline OtaInstall otaInstall() { return config().otaInstall; }
inline const std::string &otaVersion() { return config().otaVersion; }

// The one-shot panic latch. See the header comment for why it consumes the env.
inline std::string &panicSlot() {
  static std::string reason;
  return reason;
}
inline bool &panicLatched() {
  static bool latched = false;
  return latched;
}

inline void latchPanic() {
  static bool read = false;
  if (read) return;
  read = true;
  static const simreset::Registrar reg{[] {
    // The iOS reboot is a longjmp in the same process: nothing here would
    // otherwise go back, and the phone would panic on every reboot forever.
    panicLatched() = false;
    panicSlot().clear();
  }};
  if (const char *p = std::getenv("CROSSPOINT_SIM_PANIC")) {
    if (*p) {
      panicSlot() = p;
      panicLatched() = true;
    }
  }
  // Consume it so the desktop reboot's execvp child boots clean, the way the
  // boot after a real panic does.
  ::unsetenv("CROSSPOINT_SIM_PANIC");
}

inline bool panicPending() {
  latchPanic();
  return panicLatched();
}

inline const std::string &panicReason() {
  latchPanic();
  return panicSlot();
}

inline void clearPanicLatch() {
  latchPanic();
  panicLatched() = false;
  panicSlot().clear();
}

}  // namespace simtruth
