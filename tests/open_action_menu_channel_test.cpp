// Unit tests for OpenActionMenuChannel: the consume-once hand-off between a
// host gesture (bound to ios/GestureBindings.h's Action::OpenActionMenu, or
// OPENMENU in CROSSPOINT_SIM_INPUT_SCRIPT) and FileManagerActivity's per-item
// action menu. The contract under test: nothing to consume on an idle
// channel, exactly one consume per inject, a burst of injects between polls
// collapses to ONE open (mirroring FontFamilyStepChannel's reasoning -- this
// is fundamentally a single request, not a counted one), and the reboot
// reset drops a pending request so it cannot surface on the next boot's
// Manage Files.
//
// Build + run (no framework, no SDL):
//   c++ -std=c++17 -Isrc tests/open_action_menu_channel_test.cpp -o /tmp/open_action_menu_channel_test && /tmp/open_action_menu_channel_test

#include "OpenActionMenuChannel.h"

#include <cstdio>
#include "TestCheck.h"

static int &failures = testcheck::g_failures;
int main() {
  // --- idle channel: nothing to consume --------------------------------------
  {
    OpenActionMenuChannel ch;
    CHECK(!ch.consume());
    CHECK(!ch.consume());  // and asking twice invents nothing
  }

  // --- inject -> consume once, then dry --------------------------------------
  {
    OpenActionMenuChannel ch;
    ch.inject();
    CHECK(ch.consume());
    CHECK(!ch.consume());
  }

  // --- a burst between polls collapses to one open ----------------------------
  {
    OpenActionMenuChannel ch;
    ch.inject();
    ch.inject();
    ch.inject();
    CHECK(ch.consume());
    CHECK(!ch.consume());
  }

  // --- requests do not go stale: inject after a drain works again ------------
  {
    OpenActionMenuChannel ch;
    ch.inject();
    CHECK(ch.consume());
    ch.inject();
    CHECK(ch.consume());
    CHECK(!ch.consume());
  }

  // --- the reboot boundary drops a pending request ----------------------------
  {
    OpenActionMenuChannel ch;
    ch.inject();
    ch.resetForReboot();
    CHECK(!ch.consume());
    // and the channel still works after the reboot
    ch.inject();
    CHECK(ch.consume());
  }

  if (failures == 0) {
    std::printf("open_action_menu_channel_test: all tests passed\n");
    return 0;
  }
  std::printf("open_action_menu_channel_test: %d failure(s)\n", failures);
  return 1;
}
