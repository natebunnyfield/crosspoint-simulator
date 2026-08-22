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

// Two behavioral pins ride on the mechanism test, both against the REAL
// registrars/seams rather than stand-ins:
//
//  - The millis()/micros() epoch re-base (2026-08-21 audit R1). The clock's
//    registrar lives in SimulatorLifecycle.cpp, which is compiled into this
//    test, so simreset::runAll() here runs the real thing: after the boundary
//    the Arduino clock must restart near 0, the way a chip reset zeroes the
//    tick counter -- otherwise every *_AFTER_WAKE schedule compares its
//    offsets against a clock already hours in and fires instantly, silently
//    defeating the re-parse resets this file exists to pin.
//
//  - ReadAloudChannel::resetForReboot (audit R6): a page published just
//    before the boundary must not deliver into the next boot's consumer.
//    (The GPIO registrar that calls it lives in SDL-heavy HalGPIO.cpp, so the
//    wiring is covered by the registry mechanism below plus the simulator
//    runs; the seam itself is pure and pinned here.)

#include "ReadAloudChannel.h"
#include "SimulatorClock.h"
#include "SimulatorRebootResets.h"

#include <cassert>
#include <chrono>
#include <cstdio>
#include <string>
#include <thread>
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

  // --- The millis()/micros() epoch re-base (audit R1) ----------------------
  // Fake a boot that has been up a while, then cross the boundary through the
  // real registry (SimulatorLifecycle.cpp's registrar is compiled in).
  (void)simclock::millisSinceEpoch(); // latch the epoch, i.e. "boot"
  std::this_thread::sleep_for(std::chrono::milliseconds(60));
  const unsigned long preRebootMs = simclock::millisSinceEpoch();
  const unsigned long preRebootUs = simclock::microsSinceEpoch();
  assert(preRebootMs >= 50 && "the pre-reboot clock must have advanced");
  simreset::runAll();
  const unsigned long postRebootMs = simclock::millisSinceEpoch();
  const unsigned long postRebootUs = simclock::microsSinceEpoch();
  assert(postRebootMs < preRebootMs &&
         "millis() must restart at the reboot boundary, like a chip reset");
  assert(postRebootMs < 50 &&
         "the rebooted clock must be near 0, not merely smaller");
  assert(postRebootUs < preRebootUs &&
         "micros() must restart with the same epoch");
  // ...and keep counting forward from there.
  std::this_thread::sleep_for(std::chrono::milliseconds(5));
  assert(simclock::millisSinceEpoch() >= postRebootMs &&
         "the re-based clock must still be monotonic");

  // --- ReadAloudChannel across the boundary (audit R6) ---------------------
  // A publish the reboot abandons must not deliver into the next boot.
  {
    ReadAloudChannel channel;
    channel.setWanted(true);
    const ReadAloudWordRect rect{10, 20, 30, 12, 0, 5};
    channel.publish("stale page", 10, &rect, 1);
    channel.resetForReboot();
    ReadAloudPage page;
    assert(!channel.consume(page) &&
           "a pre-reboot publish must not deliver after the boundary");
    assert(channel.wanted() &&
           "the wanted flag is the consumer's to re-seed, not the boundary's");
    // The channel still works for the boot that follows.
    channel.publish("fresh page", 10, nullptr, 0);
    assert(channel.consume(page) && page.utf8 == "fresh page" &&
           "the channel must keep working after the boundary");
    assert(!page.cleared);
  }

  std::puts("reboot_resets: PASS");
  return 0;
}
