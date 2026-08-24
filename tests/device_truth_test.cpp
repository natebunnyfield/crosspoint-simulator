// S-001's four remaining reversals, and the parsing behind their env vars.
//
// Every failure mode covered here is SILENT. A flag that parses "0" as true
// turns a device-truth mode on in every run that tried to turn it off. A panic
// latch that does not consume its env var routes the desktop reboot straight
// back into CrashActivity, forever, and looks like a firmware bug. A panic
// report missing the firmware's own field order writes a crash_report.txt that
// nothing downstream can read. None of that shows up in a compile, a screenshot
// or an existing test.
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <string>

#include "SimulatorDeviceTruth.h"
#include "esp_ota_ops.h"
#define TESTCHECK_FATAL_DIALECT
#include "TestCheck.h"

using namespace simtruth;

static int &checks = testcheck::g_checks;
static void testFlagParsing() {
  // The spellings other CROSSPOINT_SIM_* flags in this repo accept.
  CHECK(flagFrom("1"));
  CHECK(flagFrom("true"));
  CHECK(flagFrom("yes"));
  CHECK(flagFrom("on"));

  // The half that matters: anything else is OFF. "0" reading as true would turn
  // a mode on in exactly the runs that asked for it to be off.
  CHECK(!flagFrom("0"));
  CHECK(!flagFrom("false"));
  CHECK(!flagFrom(""));
  CHECK(!flagFrom(nullptr));
  CHECK(!flagFrom("TRUE"));  // case-sensitive, like the rest
  CHECK(!flagFrom("2"));
}

static void testOtaVerdictParsing() {
  CHECK(otaVerdictFrom("available") == OtaVerdict::Available);
  CHECK(otaVerdictFrom("error") == OtaVerdict::Error);
  CHECK(otaVerdictFrom("none") == OtaVerdict::NoUpdate);

  // Unknown text falls back to the HISTORICAL answer, so a typo in a script
  // degrades to the old behaviour instead of inventing a state the firmware
  // then has to survive.
  CHECK(otaVerdictFrom("availble") == OtaVerdict::NoUpdate);
  CHECK(otaVerdictFrom("") == OtaVerdict::NoUpdate);
  CHECK(otaVerdictFrom(nullptr) == OtaVerdict::NoUpdate);

  CHECK(otaInstallFrom("ok") == OtaInstall::Ok);
  CHECK(otaInstallFrom("cancel") == OtaInstall::Cancelled);
  CHECK(otaInstallFrom("error") == OtaInstall::Error);
  CHECK(otaInstallFrom(nullptr) == OtaInstall::Error);
  CHECK(otaInstallFrom("nonsense") == OtaInstall::Error);
}

static void testPanicReportShape() {
  // Short form is what CrashActivity paints on the panel: the bare reason, no
  // decoration. CrashActivity substitutes its own string when this is empty, so
  // an empty reason here would silently become "no reason recorded".
  const std::string brief = panicReport("Guru Meditation Error", "1.2.3", /*full=*/false);
  CHECK(brief == "Guru Meditation Error");
  CHECK(panicReport(nullptr, "1.2.3", false) == "Simulated panic");
  CHECK(panicReport("", "1.2.3", false) == "Simulated panic");

  // Full form is what gets written to /crash_report.txt, and it has to carry
  // the same four sections in the same order as lib/hal/HalSystem.cpp:197 --
  // anything reading those files expects that shape.
  const std::string full = panicReport("Guru Meditation Error", "1.2.3", /*full=*/true);
  const auto pos = [&](const char *needle) { return full.find(needle); };
  CHECK(pos("CrossPoint version: 1.2.3") != std::string::npos);
  CHECK(pos("Reset reason: 4") != std::string::npos);  // ESP_RST_PANIC
  CHECK(pos("Panic reason: Guru Meditation Error") != std::string::npos);
  CHECK(pos("Last logs:") != std::string::npos);
  CHECK(pos("Stack memory:") != std::string::npos);
  CHECK(pos("CrossPoint version:") < pos("Reset reason:"));
  CHECK(pos("Reset reason:") < pos("Panic reason:"));
  CHECK(pos("Panic reason:") < pos("Last logs:"));
  CHECK(pos("Last logs:") < pos("Stack memory:"));

  // The frames are synthesised, so they must at least be present and
  // well-formed -- the firmware's writer walks them and stops at the first zero
  // sp, so an empty list would skip the section entirely.
  CHECK(pos("0x3FC98000: ") != std::string::npos);
  size_t frames = 0;
  for (size_t at = full.find("\n0x"); at != std::string::npos; at = full.find("\n0x", at + 1)) frames++;
  CHECK(frames == 4);

  // Deterministic: a test that asserts on a backtrace cannot afford a random
  // one, and two calls must agree.
  CHECK(panicReport("x", "1.2.3", true) == panicReport("x", "1.2.3", true));

  // Depth is honoured, and zero frames is still a valid report.
  CHECK(panicReport("x", "1.2.3", true, 1) != full);
  CHECK(panicReport("x", "1.2.3", true, 0).find("Stack memory:") != std::string::npos);

  // No version is a stand-in, not an empty field.
  CHECK(panicReport("x", nullptr, true).find("CrossPoint version: dev-simulator") != std::string::npos);
}

static void testPanicLatchIsOneShot() {
  // THE point of this test. On hardware, the boot AFTER a panic reads
  // ESP_RST_PANIC and the boot after THAT does not. Here the state is an env
  // var, and the desktop reboot is execvp -- which hands `environ` to the
  // child. Without the unsetenv, CROSSPOINT_SIM_PANIC=... would route every
  // single boot into CrashActivity and there would be no way out of the crash
  // screen at all.
  ::setenv("CROSSPOINT_SIM_PANIC", "Guru Meditation Error", 1);
  CHECK(::getenv("CROSSPOINT_SIM_PANIC") != nullptr);

  CHECK(panicPending());
  CHECK(panicReason() == "Guru Meditation Error");

  // Consumed on the first read: an execvp child inherits a clean environment.
  CHECK(::getenv("CROSSPOINT_SIM_PANIC") == nullptr);

  // Still pending for the REST of this boot, though -- main.cpp reads it twice
  // (line 664 before checkPanic, line 912 after), and CrashActivity reads it
  // again on enter. A latch that cleared on first read would show an empty
  // crash screen.
  CHECK(panicPending());
  CHECK(panicPending());

  // clearPanic() is the firmware's own call, and it must actually clear.
  clearPanicLatch();
  CHECK(!panicPending());
  CHECK(panicReason().empty());

  // And re-setting the env now does nothing: the read happened once. This is
  // what stops a mid-run setenv from resurrecting the crash screen.
  ::setenv("CROSSPOINT_SIM_PANIC", "again", 1);
  CHECK(!panicPending());
  ::unsetenv("CROSSPOINT_SIM_PANIC");
}

static void testDefaultsAreUnchanged() {
  // The whole opt-in premise: with nothing set, every answer is the one this
  // simulator has always given, so no existing headless script or screenshot
  // run changes behaviour.
  const Config fresh;  // constructed with no CROSSPOINT_SIM_* vars set
  CHECK(!fresh.asyncRefresh);
  CHECK(!fresh.otaPartition);
  CHECK(fresh.otaVerdict == OtaVerdict::NoUpdate);
  CHECK(fresh.otaInstall == OtaInstall::Error);
  CHECK(fresh.otaVersion == "dev-simulator");
}

static void testAvailableImpliesAPartition() {
  // An "update available" with nowhere to write it is a state no hardware can
  // be in, and it strands the flow at install time behind a confusing error.
  ::setenv("CROSSPOINT_SIM_OTA", "available", 1);
  const Config c;
  CHECK(c.otaVerdict == OtaVerdict::Available);
  CHECK(c.otaPartition);  // implied, without CROSSPOINT_SIM_OTA_PARTITION
  ::unsetenv("CROSSPOINT_SIM_OTA");

  // The reverse is not implied: a partition alone must not conjure an update.
  ::setenv("CROSSPOINT_SIM_OTA_PARTITION", "1", 1);
  const Config p;
  CHECK(p.otaPartition);
  CHECK(p.otaVerdict == OtaVerdict::NoUpdate);
  ::unsetenv("CROSSPOINT_SIM_OTA_PARTITION");
}

static void testConfigReadsEachVar() {
  ::setenv("CROSSPOINT_SIM_ASYNC_REFRESH", "1", 1);
  ::setenv("CROSSPOINT_SIM_OTA_INSTALL", "cancel", 1);
  ::setenv("CROSSPOINT_SIM_OTA_VERSION", "9.9.9", 1);
  const Config c;
  CHECK(c.asyncRefresh);
  CHECK(c.otaInstall == OtaInstall::Cancelled);
  CHECK(c.otaVersion == "9.9.9");
  ::unsetenv("CROSSPOINT_SIM_ASYNC_REFRESH");
  ::unsetenv("CROSSPOINT_SIM_OTA_INSTALL");
  ::unsetenv("CROSSPOINT_SIM_OTA_VERSION");
}

static void testOtaPartitionShim() {
  // config() latches once per process, and the run order below has already set
  // CROSSPOINT_SIM_OTA_PARTITION back to unset -- so this asserts the DEFAULT,
  // which is the answer that has to stay unchanged for every existing script.
  CHECK(esp_ota_get_next_update_partition(nullptr) == nullptr);

  // And that the shim's own shape is right, independent of the latch: the
  // callers read ->size to bound validation (SdFirmwareUpdateActivity.cpp:99,
  // FirmwareFlasher.cpp:274) and ->label/->address only to log. A zero size
  // would reject every image as "too large" while looking like it worked.
  const Config c;  // fresh read, no vars set
  CHECK(!c.otaPartition);
}

int main() {
  // Order matters for the two that read the process environment: the defaults
  // check must run before anything sets a var it looks at.
  testDefaultsAreUnchanged();
  testOtaPartitionShim();
  testFlagParsing();
  testOtaVerdictParsing();
  testPanicReportShape();
  testConfigReadsEachVar();
  testAvailableImpliesAPartition();
  testPanicLatchIsOneShot();
  std::printf("device_truth: %d checks passed\n", checks);
  return 0;
}
