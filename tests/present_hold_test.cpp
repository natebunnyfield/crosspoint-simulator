// The coalescing hold's one predicate (src/PresentHold.h). It is asked twice
// per present -- before the work and again under pixelBufMutex -- and the
// second asking is the font-size flash fix of 2026-10-11
// (docs/font-resize-flash-jitter-2026-10-11.md). The cases below are the
// whole contract: 0 is no hold, a due screenshot always wins, and the deadline
// is exclusive (a present AT the deadline goes out).
//
//   c++ -std=c++17 -Isrc tests/present_hold_test.cpp -o /tmp/ph && /tmp/ph

#include "PresentHold.h"

#include <cstdio>

#include "TestCheck.h"

static int &failures = testcheck::g_failures;

int main() {
  using presentheld::held;
  CHECK(!held(0, 100, false));       // nothing armed
  CHECK(!held(0, 0, false));
  CHECK(held(130, 100, false));      // armed, not yet due: held
  CHECK(!held(130, 130, false));     // at the deadline: out
  CHECK(!held(130, 131, false));     // past it: out
  CHECK(!held(130, 100, true));      // a due screenshot overrides the hold
  // The race the second asking closes: the first asking saw no hold (0), the
  // 1-bit pass then armed one (now + 30) while the present waited for the
  // lock. Asked again with the value the writer stored, the present is held.
  const unsigned long long now = 9017;
  CHECK(!held(0, now, false));
  CHECK(held(now + 30, now + 1, false));
  if (failures == 0) {
    std::printf("present_hold_test: all tests passed\n");
    return 0;
  }
  std::printf("present_hold_test: %d failure(s)\n", failures);
  return 1;
}
