// ios/SleepTouch.h: what a finger on the glass means while the firmware is
// asleep. Two rules, each a truth table small enough to state whole, and a
// device where the wrong answer is a tap that does nothing on a dark glass
// (S-039) or a wake that comes up in the other zen mode.
#include <cstdio>

#include "SleepTouch.h"

static int failures = 0;
#define CHECK(cond, msg)                                     \
  do {                                                       \
    if (!(cond)) {                                           \
      std::printf("FAIL: %s (%s)\n", msg, #cond);           \
      ++failures;                                            \
    }                                                        \
  } while (0)

int main() {
  // THE RULE: asleep, in zen, a finger is the power button.
  CHECK(sleeptouch::fingerDownWakes(true, true), "zen, asleep -> the finger wakes");
  // Awake in zen the finger is the deliberate tap, the classifier's business.
  CHECK(!sleeptouch::fingerDownWakes(true, false), "zen, awake -> ordinary path");
  // Out of zen the pad exists and its POWER capsule is the wake, as on the
  // device; a finger on the page while asleep stays ignored.
  CHECK(!sleeptouch::fingerDownWakes(false, true),
        "pad, asleep -> ordinary path (POWER capsule)");
  CHECK(!sleeptouch::fingerDownWakes(false, false), "pad, awake -> ordinary path");

  // While asleep only a press can reach the firmware, and a press is a wake.
  CHECK(sleeptouch::actionAllowedWhileAsleep(true, true),
        "asleep, button -> perform (it is the wake)");
  CHECK(!sleeptouch::actionAllowedWhileAsleep(true, false), "asleep, host action -> swallow");
  // Awake, every action is performed as before.
  CHECK(sleeptouch::actionAllowedWhileAsleep(false, true), "awake, button -> perform");
  CHECK(sleeptouch::actionAllowedWhileAsleep(false, false), "awake, host action -> perform");

  static_assert(sleeptouch::fingerDownWakes(true, true), "constexpr: the sleeping zen glass wakes");
  static_assert(!sleeptouch::fingerDownWakes(false, true),
                "constexpr: the pad keeps its POWER capsule");
  static_assert(!sleeptouch::actionAllowedWhileAsleep(true, false),
                "constexpr: the zen toggle cannot fire on a sleeping device");

  if (failures) {
    std::printf("%d failure(s)\n", failures);
    return 1;
  }
  std::printf("sleep_touch: OK\n");
  return 0;
}
