// Proves the split-brain guard in src/SimulatorBuildIdentity.{h,cpp} actually
// fires. A guard that never runs is worth nothing, and this one only runs on a
// build that is already broken — so it has to be exercised deliberately.
//
// Build + run (X3 macros, matching the iOS target):
//   c++ -std=c++17 -DSIMULATOR -DSIMULATOR_DEVICE_X3 -DCROSSPOINT_RENDER_SCALE=2 \
//       -Isrc <firmware includes> tests/build_identity_test.cpp \
//       src/SimulatorBuildIdentity.cpp -o /tmp/build_identity_test
//   /tmp/build_identity_test
//
// The mismatch cases run in a forked child, because the guard's whole job is
// to abort the process.

#include <sys/wait.h>
#include <unistd.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>

#include "SimulatorBuildIdentity.h"
#include "TestCheck.h"
using testcheck::check;

namespace {

int &g_failures = testcheck::g_failures;

// Runs verifyBuildIdentityMatchesCore in a child and reports whether it died.
bool abortsOn(const SimulatorBuildIdentity &local) {
  fflush(nullptr);
  const pid_t pid = fork();
  if (pid == 0) {
    // Child. stderr is noisy by design; the parent only cares how it exits.
    freopen("/dev/null", "w", stderr);
    freopen("/dev/null", "w", stdout);
    verifyBuildIdentityMatchesCore(local, "test harness");
    _exit(0);
  }
  int status = 0;
  waitpid(pid, &status, 0);
  return WIFSIGNALED(status) || (WIFEXITED(status) && WEXITSTATUS(status) != 0);
}

} // namespace

int main() {
  const SimulatorBuildIdentity core = coreBuildIdentity();

  // The core must report what this TU was compiled with — the test is built
  // with the iOS target's macros.
  check(std::strcmp(core.device, "X3") == 0, "core reports X3");
  check(core.logicalWidth == 792 && core.logicalHeight == 528,
        "core reports 792x528 logical");
  check(core.renderScale == 2, "core reports 2x render scale");

  // Agreement path: must NOT abort.
  check(!abortsOn(localBuildIdentity()), "matching identity survives");

  // Each field on its own must be enough to kill the process. The device field
  // is the 2026-08-06 sleep-screen bug; renderScale is the 15-build 1x bug.
  SimulatorBuildIdentity wrongDevice = core;
  wrongDevice.device = "X4";
  check(abortsOn(wrongDevice), "device mismatch aborts");

  SimulatorBuildIdentity wrongGeometry = core;
  wrongGeometry.logicalWidth = 800;
  wrongGeometry.logicalHeight = 480;
  check(abortsOn(wrongGeometry), "geometry mismatch aborts");

  SimulatorBuildIdentity wrongScale = core;
  wrongScale.renderScale = 1;
  check(abortsOn(wrongScale), "render scale mismatch aborts");

  if (g_failures == 0) {
    std::printf("build_identity_test: all tests passed\n");
    return 0;
  }
  std::printf("build_identity_test: %d failure(s)\n", g_failures);
  return 1;
}
