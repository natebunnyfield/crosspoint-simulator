#pragma once

#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif

// Overridable so the in-process branch can be typechecked off-device; it is
// otherwise compiled only for iOS, where nothing in this environment can build
// it. Same escape hatch as CROSSPOINT_SIM_HOST_WIFI and CROSSPOINT_SIM_HOST_HTTP.
#ifndef CROSSPOINT_SIM_REBOOT_IN_PROCESS
#if defined(__APPLE__) && TARGET_OS_IPHONE
#define CROSSPOINT_SIM_REBOOT_IN_PROCESS 1
#else
#define CROSSPOINT_SIM_REBOOT_IN_PROCESS 0
#endif
#endif

#if CROSSPOINT_SIM_REBOOT_IN_PROCESS
#include <csetjmp>
#endif

namespace SimulatorLifecycle {

enum class WakeReason { None, PowerButton };

void initProcessArgs(char** argv);
WakeReason consumeWakeReason();
[[noreturn]] void rebootAsPowerWake();

// ESP.restart(): the firmware asking for a plain reset, NOT a deep-sleep wake.
//
// The distinction matters and is why this is not just a call to
// rebootAsPowerWake(). That function sets CROSSPOINT_SIM_WAKE_REASON=power, and
// the firmware reads it as "the user pressed POWER to wake the device". A
// restart is nobody pressing anything -- CrossPointWebServerActivity calls it on
// the way out of file transfer to defragment the heap -- so claiming a button
// press would send the firmware down the wrong boot path.
//
// May or may not return: it does not return when it reboots, and returns
// immediately when the platform declines to (see the .cpp for which do).
// Callers must treat it as possibly-returning, which ESP.restart()'s Arduino
// signature already does.
void rebootAsFirmwareRestart();

// The simulator relaunching itself to open a document Finder just handed it.
//
// Separate from both functions above because it is neither of the things they
// model. It is not a wake, so it must not set the power-wake reason. And it is
// not the firmware calling ESP.restart(), so it is not subject to that path's
// desktop opt-in: rebootAsFirmwareRestart() defaults off on desktop because
// execvp() loses the RTC_NOINIT globals the firmware restarts *for*, whereas
// this restart carries its intent in APP_STATE on the card, which a new process
// reads on the way up. Nothing is lost by exec'ing, so nothing gates it.
//
// Returns only on failure.
void rebootForDocumentOpen();

#if CROSSPOINT_SIM_REBOOT_IN_PROCESS
// A deep-sleep wake is a chip reset on real hardware, and on desktop it is a
// process relaunch via execvp(). Neither is available on iOS: the sandbox denies
// process-exec, so the exec falls through to _exit() -- which iOS reports as a
// crash, and which in practice leaves the app frozen on the sleep screen.
//
// So the wake is performed in-process instead: rebootAsPowerWake() longjmps back
// to a setjmp() in main() placed ahead of setup(), and setup() runs again. That
// models the reset closely enough, provided the things setup() touches are
// idempotent -- see HalDisplay::begin() (reuses its window) and xTaskCreate()
// (dedupes by task name, because a real reset leaves exactly one render task).
//
// The jump skips destructors for every frame between main() and the sleep loop,
// exactly as execvp() would. Anything those frames owned is leaked for the life
// of the process. On hardware that memory is wiped by the reset; here it is not,
// so a very long sleep/wake cycle count will grow the heap.
std::jmp_buf& rebootJumpBuffer();

// Arm the jump. Until this is called, rebootAsPowerWake() has nowhere to go and
// falls back to the exec path, so an early wake cannot jump into a frame that
// does not exist yet.
void armRebootJump();
#endif

}  // namespace SimulatorLifecycle
