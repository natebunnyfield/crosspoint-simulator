// S-002: the in-process (iOS) reboot is a longjmp, so every static in the
// binary survives it. Modules that cache env-derived state behind a
// `static bool ...Initialized` therefore never re-read it, and the
// *_AFTER_WAKE promotion in rebootAsPowerWake() has no effect on the only
// platform that takes that path.
//
// This pins the registry those resets run through. It cannot exercise the
// longjmp itself -- that would need the harness -- so it asserts the contract
// SimulatorLifecycle depends on: everything registered runs, in registration
// order, every time.

#include "SimulatorRebootResets.h"

#include <cassert>
#include <cstdio>
#include <string>
#include <vector>

int main() {
  // Mirrors the real shape: a module-scope flag latched on first use.
  static bool moduleInitialized = true;
  static std::vector<int> moduleSchedule{1, 2, 3};
  static bool textEntryLatched = true;

  std::vector<std::string> order;

  simreset::add([&] {
    order.push_back("gpio");
    moduleInitialized = false;
    moduleSchedule.clear();
    textEntryLatched = false;
  });
  simreset::add([&] { order.push_back("display"); });

  simreset::runAll();

  assert(!moduleInitialized && "the initialized flag must be cleared so setup() re-reads the env");
  assert(moduleSchedule.empty() && "a stale pre-sleep schedule must not survive the reboot");
  assert(!textEntryLatched && "a reboot mid-text-entry must not leave the keyboard channel on");
  assert(order.size() == 2);
  assert(order[0] == "gpio" && order[1] == "display" && "resets run in registration order");

  // A reboot can happen more than once in a process. Running again must be
  // safe and must not drop callbacks.
  moduleInitialized = true;
  order.clear();
  simreset::runAll();
  assert(!moduleInitialized && "a second in-process reboot must reset just like the first");
  assert(order.size() == 2 && "runAll must not consume the registry");

  std::puts("reboot_resets: PASS");
  return 0;
}
