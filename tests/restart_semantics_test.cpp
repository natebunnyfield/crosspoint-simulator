// Pins what SimulatorLifecycle::rebootAsFirmwareRestart() does to the
// environment, which is the part that decides whether the rebooted firmware
// comes up correctly.
//
// Two things are easy to get wrong here and both are silent:
//
//   1. Reusing rebootAsPowerWake() would leave CROSSPOINT_SIM_WAKE_REASON=power
//      set, and the firmware would boot believing someone pressed POWER to wake
//      it. A restart is nobody pressing anything.
//   2. Leaving the input script in place would have an automated run replay
//      from the top after the restart, restart again, and loop forever.
//
// This exercises the desktop opt-out path (the function returns rather than
// rebooting), so the assertions can run in-process. The reboot mechanism itself
// -- longjmp on iOS, execvp on desktop -- is covered by tests/test_sleep_wake.sh
// for the wake path and is not re-tested here.
//
//   c++ -std=c++20 -Isrc tests/restart_semantics_test.cpp src/SimulatorLifecycle.cpp
//       -o /tmp/restart_semantics_test && /tmp/restart_semantics_test

#include "SimulatorLifecycle.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>

namespace {

void expect(bool cond, const char *what) {
  if (!cond) {
    std::fprintf(stderr, "FAIL: %s\n", what);
    std::exit(1);
  }
}

bool isSet(const char *name) {
  const char *v = std::getenv(name);
  return v != nullptr;
}

// Opted out, the call must be inert: no reboot, and nothing disturbed.
void testOptedOutIsInert() {
  setenv("CROSSPOINT_SIM_FIRMWARE_RESTART", "0", 1);
  setenv("CROSSPOINT_SIM_INPUT_SCRIPT", "2000:HOME;9000:QUIT", 1);
  setenv("CROSSPOINT_SIM_WAKE_REASON", "power", 1);

  SimulatorLifecycle::rebootAsFirmwareRestart();  // returns

  expect(std::string(std::getenv("CROSSPOINT_SIM_INPUT_SCRIPT") ?: "") ==
             "2000:HOME;9000:QUIT",
         "an inert restart leaves the input script alone");
  expect(std::string(std::getenv("CROSSPOINT_SIM_WAKE_REASON") ?: "") == "power",
         "an inert restart leaves the wake reason alone");

  unsetenv("CROSSPOINT_SIM_WAKE_REASON");
  unsetenv("CROSSPOINT_SIM_INPUT_SCRIPT");
}

// consumeWakeReason() is what the firmware asks "why am I awake". A restart
// must not answer "because POWER was pressed", so the restart path clears it.
// Verified through the public reader rather than the variable, since that is
// what the firmware actually sees.
void testRestartIsNotAWake() {
  setenv("CROSSPOINT_SIM_WAKE_REASON", "power", 1);
  expect(SimulatorLifecycle::consumeWakeReason() ==
             SimulatorLifecycle::WakeReason::PowerButton,
         "precondition: a power wake reads as PowerButton");

  // Now the restart path, opted in so it reaches the env work. It will attempt
  // to reboot after that; on this build the jump is unarmed and argv unset, so
  // it reports and returns instead -- which is exactly the seam this test uses.
  setenv("CROSSPOINT_SIM_FIRMWARE_RESTART", "1", 1);
  setenv("CROSSPOINT_SIM_WAKE_REASON", "power", 1);
  SimulatorLifecycle::rebootAsFirmwareRestart();

  expect(!isSet("CROSSPOINT_SIM_WAKE_REASON"),
         "a restart clears the wake reason rather than claiming a POWER press");
  expect(SimulatorLifecycle::consumeWakeReason() ==
             SimulatorLifecycle::WakeReason::None,
         "the firmware sees no wake reason after a restart");
}

// A script that drives the firmware into a restart must not come back to life
// in the rebooted instance and do it again.
void testRestartCannotLoopAnInputScript() {
  setenv("CROSSPOINT_SIM_FIRMWARE_RESTART", "1", 1);
  setenv("CROSSPOINT_SIM_INPUT_SCRIPT", "2000:HOME;5000:ENTER", 1);
  setenv("CROSSPOINT_SIM_INPUT_SCRIPT_AFTER_WAKE", "1000:QUIT", 1);

  SimulatorLifecycle::rebootAsFirmwareRestart();

  expect(!isSet("CROSSPOINT_SIM_INPUT_SCRIPT"),
         "the pre-restart script is cleared, so it cannot replay");
  expect(!isSet("CROSSPOINT_SIM_INPUT_SCRIPT_AFTER_WAKE"),
         "the after-wake script is cleared too: a restart is not a wake, so "
         "promoting it would run a schedule meant for a different event");
}

}  // namespace

int main() {
  testOptedOutIsInert();
  testRestartIsNotAWake();
  testRestartCannotLoopAnInputScript();
  std::printf("restart_semantics_test: all checks passed\n");
  return 0;
}
