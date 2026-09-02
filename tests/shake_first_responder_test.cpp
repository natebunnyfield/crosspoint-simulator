// ios/ShakeFirstResponder.h: when the shake catcher may take first responder.
// Four states, one answer that must be NO -- a field open with its keyboard
// up -- and a device where the wrong answer is a keyboard that quietly
// vanishes on every zen toggle (audit 2026-09-02, finding 2).
#include <cstdio>

#include "ShakeFirstResponder.h"

static int failures = 0;
#define CHECK(cond, msg)                                     \
  do {                                                       \
    if (!(cond)) {                                           \
      std::printf("FAIL: %s (%s)\n", msg, #cond);           \
      ++failures;                                            \
    }                                                        \
  } while (0)

int main() {
  // No field open: the shake owns the status, keyboard flag irrelevant (it
  // is false whenever no field is open, HalGPIO.h, but the decision must not
  // depend on that invariant).
  CHECK(shakeresp::shouldClaim(false, false), "no field, keyboard down -> claim");
  CHECK(shakeresp::shouldClaim(false, true), "no field, stale keyboard flag -> claim");
  // Field open, keyboard put away with the chip: the text field is not
  // showing anything the reader is using; the shake may claim.
  CHECK(shakeresp::shouldClaim(true, false), "field open, keyboard down -> claim");
  // THE case: field open, keyboard up. Claiming here resigns SDL's text field
  // and the keyboard goes with it.
  CHECK(!shakeresp::shouldClaim(true, true), "field open, keyboard up -> must NOT claim");

  static_assert(!shakeresp::shouldClaim(true, true), "constexpr: the typing state yields");
  static_assert(shakeresp::shouldClaim(false, false), "constexpr: the idle state claims");

  if (failures) {
    std::printf("%d failure(s)\n", failures);
    return 1;
  }
  std::printf("shake_first_responder: OK\n");
  return 0;
}
