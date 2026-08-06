#include "SimulatorLifecycle.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
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

  unsetenv(kWakeReasonEnv);
  if (std::strcmp(value, "power") == 0) {
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
    std::longjmp(gRebootJump, 1);
  }
  std::fputs("SimulatorLifecycle: reboot jump not armed\n", stderr);
#endif

  if (!gArgv || !gArgv[0]) {
    std::fputs("SimulatorLifecycle: missing argv for reboot\n", stderr);
    _exit(1);
  }
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
  // still closer to hardware than today's do-nothing, but it is a behaviour
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

} // namespace SimulatorLifecycle
