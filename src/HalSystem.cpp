#include "HalSystem.h"

#include <Logging.h>

#include "HalStorage.h"
#include "SimulatorDeviceTruth.h"

// S-001: this used to answer "no panic, ever". On hardware there are 225 lines
// of panic capture behind these four calls, and `CrashActivity` is routed to
// from main.cpp:828 on exactly one condition -- isRebootFromPanic(). A constant
// false meant the activity compiled in and could not be entered, so the crash
// screen has never once been seen in the project's only pre-device gate.
//
// CROSSPOINT_SIM_PANIC=<reason> makes this boot the boot after a panic. It is
// one-shot by construction (see SimulatorDeviceTruth.h): a reboot out of the
// crash screen has to land somewhere other than the crash screen, or the
// simulator is a loop rather than a device.

void HalSystem::begin() {}
void HalSystem::restart() { exit(0); }

void HalSystem::checkPanic() {
  if (!simtruth::panicPending()) return;
  // The device writes the full report to a fixed path on the card before the
  // crash screen shows, and people go looking for that file. Write it here too,
  // so the artifact a support request asks for exists in the simulated card.
  const std::string info = simtruth::panicReport(simtruth::panicReason().c_str(),
                                                 "dev-simulator", /*full=*/true);
  if (Storage.writeFile("/crash_report.txt", String(info.c_str()))) {
    LOG_INF("SYS", "[SIM] dumped injected panic to /crash_report.txt (%zu bytes)", info.size());
  } else {
    LOG_ERR("SYS", "[SIM] failed to write /crash_report.txt");
  }
}

void HalSystem::clearPanic() { simtruth::clearPanicLatch(); }

std::string HalSystem::getPanicInfo(bool full) {
  if (!simtruth::panicPending()) return {};
  return simtruth::panicReport(simtruth::panicReason().c_str(), "dev-simulator", full);
}

bool HalSystem::isRebootFromPanic() { return simtruth::panicPending(); }
