// Unit tests for FontFamilyStepChannel: the consume-once hand-off between a
// host shake (iOS zen, or SHAKE in CROSSPOINT_SIM_INPUT_SCRIPT) and the
// reader's font-family cycle. The contract under test: nothing to consume on
// an idle channel, exactly one consume per inject, a burst of injects between
// polls collapses to ONE step (the reader re-paginates per step, so a queue
// here would turn one shake into a storm of SD loads), and the reboot reset
// drops a pending step so it cannot land on the next boot's reader.
//
// Build + run (no framework, no SDL):
//   c++ -std=c++17 -Isrc tests/font_family_step_channel_test.cpp -o /tmp/font_family_step_channel_test && /tmp/font_family_step_channel_test

#include "FontFamilyStepChannel.h"

#include <cstdio>
#include "TestCheck.h"

static int &failures = testcheck::g_failures;
int main() {
  // --- idle channel: nothing to consume --------------------------------------
  {
    FontFamilyStepChannel ch;
    CHECK(!ch.consume());
    CHECK(!ch.consume());  // and asking twice invents nothing
  }

  // --- inject -> consume once, then dry --------------------------------------
  {
    FontFamilyStepChannel ch;
    ch.inject();
    CHECK(ch.consume());
    CHECK(!ch.consume());
  }

  // --- a burst between polls collapses to one step ---------------------------
  {
    FontFamilyStepChannel ch;
    ch.inject();
    ch.inject();
    ch.inject();
    CHECK(ch.consume());
    CHECK(!ch.consume());
  }

  // --- steps do not go stale: inject after a drain works again ---------------
  {
    FontFamilyStepChannel ch;
    ch.inject();
    CHECK(ch.consume());
    ch.inject();
    CHECK(ch.consume());
    CHECK(!ch.consume());
  }

  // --- the reboot boundary drops a pending step ------------------------------
  {
    FontFamilyStepChannel ch;
    ch.inject();
    ch.resetForReboot();
    CHECK(!ch.consume());
    // and the channel still works after the reboot
    ch.inject();
    CHECK(ch.consume());
  }

  if (failures == 0) {
    std::printf("font_family_step_channel_test: all tests passed\n");
    return 0;
  }
  std::printf("font_family_step_channel_test: %d failure(s)\n", failures);
  return 1;
}
