#include "SimulatorLifecycle.h"
#include "SimulatorRebootResets.h"
#include "freertos/semphr.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <unistd.h>

namespace {

constexpr const char *kWakeReasonEnv = "CROSSPOINT_SIM_WAKE_REASON";
constexpr const char *kInputScriptEnv = "CROSSPOINT_SIM_INPUT_SCRIPT";
constexpr const char *kInputScriptAfterWakeEnv =
    "CROSSPOINT_SIM_INPUT_SCRIPT_AFTER_WAKE";
constexpr const char *kScreenshotsEnv = "CROSSPOINT_SIM_SCREENSHOTS";
constexpr const char *kScreenshotsAfterWakeEnv =
    "CROSSPOINT_SIM_SCREENSHOTS_AFTER_WAKE";
char **gArgv = nullptr;

#if CROSSPOINT_SIM_REBOOT_IN_PROCESS
std::jmp_buf gRebootJump;
bool gRebootJumpArmed = false;
#endif

// CROSSPOINT_SIM_LOG_POWER=1: the lifecycle station of the [power] path (the
// display and GPIO halves live in HalDisplay.cpp / HalGPIO.cpp). fprintf, not
// SDL_Log, because this TU is compiled SDL-free by restart_semantics_test.
bool powerLogWanted() {
  const char *e = std::getenv("CROSSPOINT_SIM_LOG_POWER");
  return e && e[0] == '1';
}

void promoteAfterWakeValue(const char *target, const char *afterWake) {
  const char *value = std::getenv(afterWake);
  if (value) {
    setenv(target, value, 1);
  } else {
    unsetenv(target);
  }
  unsetenv(afterWake);
}

} // namespace

namespace SimulatorLifecycle {

void initProcessArgs(char **argv) { gArgv = argv; }

WakeReason consumeWakeReason() {
  const char *value = std::getenv(kWakeReasonEnv);
  if (!value) {
    return WakeReason::None;
  }

  // Copy before unsetting. getenv() hands back a pointer INTO the environment
  // block, and unsetenv() frees that storage on macOS -- so comparing `value`
  // after the unsetenv below is a use-after-free that reads an empty string,
  // and the wake silently degrades to WakeReason::None. Measured: a program
  // that setenv()s "power", getenv()s it, then unsetenv()s reads "" from the
  // saved pointer immediately afterwards.
  //
  // It survived because the two callers differ in where the variable came from:
  // a value inherited across execvp() lives in the original environ block,
  // which unsetenv() unlinks without freeing, so the stale read happened to
  // still see "power". Only a value planted with setenv() in the same process
  // -- which is what restart_semantics_test does -- lands in malloc'd storage
  // that is actually freed. Same undefined behavior either way.
  const std::string reason(value);
  unsetenv(kWakeReasonEnv);
  if (reason == "power") {
    return WakeReason::PowerButton;
  }
  return WakeReason::None;
}

#if CROSSPOINT_SIM_REBOOT_IN_PROCESS
std::jmp_buf &rebootJumpBuffer() { return gRebootJump; }
void armRebootJump() { gRebootJumpArmed = true; }
#endif

[[noreturn]] void rebootAsPowerWake() {
  setenv(kWakeReasonEnv, "power", 1);
  // A deep-sleep wake is a fresh process. Do not replay the pre-sleep script,
  // which would otherwise put every relaunched process back to sleep forever.
  // Tests can provide an explicit post-wake schedule when they need to capture
  // or terminate the relaunched instance.
  promoteAfterWakeValue(kInputScriptEnv, kInputScriptAfterWakeEnv);
  promoteAfterWakeValue(kScreenshotsEnv, kScreenshotsAfterWakeEnv);

#if CROSSPOINT_SIM_REBOOT_IN_PROCESS
  // Preferred on iOS: re-enter setup() rather than exec a new process, which
  // the sandbox forbids. See the header for what this costs.
  if (gRebootJumpArmed) {
    if (powerLogWanted())
      std::fprintf(stderr, "[power] longjmp reboot (power wake)\n");
    // A longjmp is not a new process: every static in this binary survives it.
    // Put the ones that cache env-derived state back so setup() re-reads them.
    simreset::runAll();
    // The jump skips destructors, so any RenderLock held right now never gives
    // its mutex back and the render task blocks forever on the first frame
    // after the reboot. Drop every lock and wake the waiters; the threads that
    // held them are being abandoned with their stacks anyway.
    simsemphr::forceReleaseAllForReboot();
    std::longjmp(gRebootJump, 1);
  }
  std::fputs("SimulatorLifecycle: reboot jump not armed\n", stderr);
#endif

  if (!gArgv || !gArgv[0]) {
    std::fputs("SimulatorLifecycle: missing argv for reboot\n", stderr);
    _exit(1);
  }
  if (powerLogWanted())
    std::fprintf(stderr, "[power] execvp reboot (power wake)\n");
  execvp(gArgv[0], gArgv);

  std::perror("execvp");
  _exit(1);
}

void rebootAsFirmwareRestart() {
  // Whether a firmware restart actually reboots the simulator.
  //
  // On iOS: yes, and it is faithful. The in-process reboot longjmps back into
  // setup() without leaving the process, so the firmware's RTC_NOINIT globals
  // -- silentRebootMagic and silentRebootTarget, which carry "come back up on
  // Home" -- survive exactly as RTC memory survives a reset on hardware.
  //
  // On desktop: opt-in, because the reboot there is execvp() and those globals
  // do NOT survive a new process. The firmware would reboot but lose the target
  // it rebooted FOR, landing on the normal boot path instead of Home. That is
  // still closer to hardware than today's do-nothing, but it is a behavior
  // change to a build that is the canary for everything else, and any QA script
  // that passes through file transfer would relaunch mid-run. So desktop keeps
  // the old no-op until someone can verify the real thing, and this variable is
  // how they do it.
  const char *enabled = std::getenv("CROSSPOINT_SIM_FIRMWARE_RESTART");
  const bool set = enabled && *enabled;
  const bool optedOut = set && std::strcmp(enabled, "0") == 0;

#if CROSSPOINT_SIM_REBOOT_IN_PROCESS
  const bool shouldReboot = !optedOut; // default on
#else
  const bool shouldReboot = set && !optedOut; // default off
#endif

  if (!shouldReboot) {
    return;
  }

  // A restart is not a wake. Leaving the wake reason unset is the whole point
  // of this function existing separately from rebootAsPowerWake().
  unsetenv(kWakeReasonEnv);

  // Loop safety, and the reason this cannot simply reuse the sleep path's
  // promotion: a script that drives the firmware into a restart would otherwise
  // replay from the top in the rebooted instance and restart again, forever.
  // Clearing is the conservative choice -- an automated run that triggers a
  // restart ends up idle rather than looping, which is visible instead of
  // silent.
  unsetenv(kInputScriptEnv);
  unsetenv(kInputScriptAfterWakeEnv);

#if CROSSPOINT_SIM_REBOOT_IN_PROCESS
  if (gRebootJumpArmed) {
    // A longjmp is not a new process: every static in this binary survives it.
    // Put the ones that cache env-derived state back so setup() re-reads them.
    simreset::runAll();
    // The jump skips destructors, so any RenderLock held right now never gives
    // its mutex back and the render task blocks forever on the first frame
    // after the reboot. Drop every lock and wake the waiters; the threads that
    // held them are being abandoned with their stacks anyway.
    simsemphr::forceReleaseAllForReboot();
    std::longjmp(gRebootJump, 1);
  }
  std::fputs("SimulatorLifecycle: restart requested before jump armed\n", stderr);
  return;
#else
  if (!gArgv || !gArgv[0]) {
    std::fputs("SimulatorLifecycle: missing argv for restart\n", stderr);
    return;
  }
  execvp(gArgv[0], gArgv);
  std::perror("execvp");
  return;
#endif
}

void rebootForDocumentOpen() {
  // Not a wake. Same reasoning as rebootAsFirmwareRestart(): claiming a POWER
  // press would send the firmware down the wrong boot path.
  unsetenv(kWakeReasonEnv);

  // Same loop safety as the restart path. A QA script that drives the simulator
  // into a document open would otherwise replay from the top in the relaunched
  // process and open it again, forever.
  unsetenv(kInputScriptEnv);
  unsetenv(kInputScriptAfterWakeEnv);

#if CROSSPOINT_SIM_REBOOT_IN_PROCESS
  // iOS: same in-process jump as rebootAsPowerWake(), for the same reason --
  // the sandbox forbids execvp() outright, it is not merely undesirable here.
  // The header's old "nothing is lost by exec'ing, so nothing gates it"
  // reasoning was about desktop only; on iOS exec never works regardless of
  // what would be lost.
  if (gRebootJumpArmed) {
    simreset::runAll();
    simsemphr::forceReleaseAllForReboot();
    std::longjmp(gRebootJump, 1);
  }
  std::fputs("SimulatorLifecycle: reboot jump not armed for document open\n", stderr);
  return;
#else
  if (!gArgv || !gArgv[0]) {
    std::fputs("SimulatorLifecycle: missing argv for document open\n", stderr);
    return;
  }
  execvp(gArgv[0], gArgv);
  std::perror("execvp");
#endif
}

} // namespace SimulatorLifecycle
