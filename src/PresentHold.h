#pragma once

#include <cstdint>

// IS A PRESENT HELD BY THE COALESCING HOLD? One predicate, asked twice by
// HalDisplay::presentIfNeeded: once before the present does any work, and
// again once it holds pixelBufMutex -- because the render task's 1-bit pass
// arms the hold INSIDE that lock, after writing the 1-bit frame, and a present
// that passed the first question while nothing was held would otherwise upload
// that frame (the font-size flash, 2026-10-11,
// docs/font-resize-flash-jitter-2026-10-11.md). Pure, so the rule that a due
// screenshot overrides the hold and that 0 means "no hold" is pinned by
// tests/present_hold_test.cpp rather than restated at each call site.
namespace presentheld {

constexpr bool held(uint64_t holdUntilMs, uint64_t nowMs, bool screenshotDue) {
  return holdUntilMs != 0 && !screenshotDue && nowMs < holdUntilMs;
}

// RELEASE AT THE END OF A RENDER PASS (owner ruling 2026-11-27, "Hold only
// before gray"; firmware docs/menu-nav-lag-2026-11-27.md O2). A firmware
// render() that follows its 1-bit frame with a gray pass runs it before it
// returns, so a hold that pass armed and that is still armed when render()
// returns is waiting for a compose that is not coming: a menu step, a 1-bit
// screen. Let the frame out then rather than at the 30 ms deadline. Not while
// the page-turn flash is on (CROSSPOINT_SIM_PRESENT_FLASH): that hold IS the
// flash, held on purpose.
//
// Only the hold THIS pass armed, and only while it is still that hold
// (adversarial review 2026-11-27, finding 4): the 1-bit pass can arm on any
// thread -- SleepActivity draws its gray covers on the main thread, outside
// the render lock -- so a render pass ending in between must not let that
// cover's 1-bit base out, nor clear a hold armed after this pass's.
// `armedThisPass` is the deadline this thread stored (0 = none); the caller
// clears it with a compare-and-swap on that same value.
constexpr bool releaseAtPassEnd(uint64_t holdUntilMs, uint64_t armedThisPass,
                                bool flashWanted) {
  return armedThisPass != 0 && holdUntilMs == armedThisPass && !flashWanted;
}

}  // namespace presentheld
