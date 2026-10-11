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

}  // namespace presentheld
