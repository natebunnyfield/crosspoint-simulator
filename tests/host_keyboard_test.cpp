// hostkbd::State -- showing and hiding the host's software keyboard while the
// firmware's text field stays open.
//
// WHY THIS IS A HOST TEST
//
// The feature is one atomic bool away from being invisible in the worst way.
// Its whole job is to lower a keyboard the firmware asked for and raise it
// again on request, and every way it can break leaves a build that compiles,
// runs, logs nothing unusual, and simply never shows a keyboard again. On
// desktop there is no software keyboard to watch at all; on a phone the state
// cannot be single-stepped. So the decision lives in a pure header and gets
// driven here, on the real object rather than a mirror of it.
//
// Build:
//   c++ -std=c++17 -Isrc tests/host_keyboard_test.cpp -o /tmp/hkt && /tmp/hkt

#include "HostKeyboardState.h"

#include <cassert>
#include <cstdio>
#define TESTCHECK_FATAL_DIALECT
#include "TestCheck.h"

namespace {

using hostkbd::Action;
using hostkbd::State;

constexpr bool kFieldOpen = true;
constexpr bool kNoField = false;

// The firmware's flag flipping, which is what setTextEntryActive() does.
void fieldEdge(State &s) { s.onFieldEdge(); }

} // namespace

int main() {
  // --- the ordinary life of a text field ---
  {
    State s;
    // Nothing open: nothing to do, however often we ask.
    CHECK(s.poll(kNoField) == Action::None);
    CHECK(s.poll(kNoField) == Action::None);

    // Field opens -> keyboard stays down, chip shows; nothing raises on its
    // own (owner ruling 2026-08-12).
    fieldEdge(s);
    CHECK(s.poll(kFieldOpen) == Action::None);
    CHECK(s.poll(kFieldOpen) == Action::None);

    // Owner taps the chip -> raise once, then stay put.
    s.requestVisible(true);
    CHECK(s.poll(kFieldOpen) == Action::Start);
    CHECK(s.poll(kFieldOpen) == Action::None);

    // Field closes -> lower once.
    fieldEdge(s);
    CHECK(s.poll(kNoField) == Action::Stop);
    CHECK(s.poll(kNoField) == Action::None);
  }

  // --- the owner asks for it, hides it, then asks for it back ---
  {
    State s;
    fieldEdge(s);
    CHECK(s.poll(kFieldOpen) == Action::None && "down until asked");

    s.requestVisible(true);
    CHECK(!s.suppressed());
    CHECK(s.poll(kFieldOpen) == Action::Start);

    s.requestVisible(false);
    CHECK(s.suppressed());
    CHECK(!s.wants(kFieldOpen) && "hidden by request, though the field is open");
    CHECK(s.poll(kFieldOpen) == Action::Stop);
    CHECK(s.poll(kFieldOpen) == Action::None && "stays down until asked");

    s.requestVisible(true);
    CHECK(!s.suppressed());
    CHECK(s.poll(kFieldOpen) == Action::Start);
    CHECK(s.poll(kFieldOpen) == Action::None);
  }

  // --- a manual show NEVER outlives the field, same as a manual hide never did ---
  //
  // The bug this forbids (the current, correct direction): tap the chip to
  // show the keyboard once, and every text field for the rest of the session
  // must NOT open with one already up -- that was the original bug this file
  // shipped to fix (owner report 2026-08-12: fields were opening with the
  // keyboard already up, unasked).
  {
    State s;
    fieldEdge(s);
    s.requestVisible(true);
    CHECK(s.poll(kFieldOpen) == Action::Start);

    // Field closes with the keyboard still up...
    fieldEdge(s);
    CHECK(s.suppressed() && "the closing edge resets to hidden");
    CHECK(s.poll(kNoField) == Action::Stop && "still up; lower it");

    // ...and the next field opens WITHOUT a keyboard.
    fieldEdge(s);
    CHECK(s.poll(kFieldOpen) == Action::None);
  }
  {
    // The same, when the show is still in force as a NEW field opens directly
    // (activity to activity, no closed gap the caller polls in).
    State s;
    fieldEdge(s);
    s.requestVisible(true);
    CHECK(s.poll(kFieldOpen) == Action::Start);
    fieldEdge(s); // close
    fieldEdge(s); // open, without an intervening poll
    CHECK(s.suppressed());
    // Nobody has told the platform to lower it yet -- the pending Start from
    // the old field is still "applied", so the very next poll has to Stop it
    // before the new field's hidden default counts as achieved.
    CHECK(s.poll(kFieldOpen) == Action::Stop);
    CHECK(s.poll(kFieldOpen) == Action::None);
  }

  // --- a raise while the platform hid it behind our back forces a restart ---
  //
  // iPad's own dismiss key, or a hardware keyboard connecting, lowers the
  // keyboard without changing anything here: the field is open, nothing is
  // suppressed, and the last thing we did was raise it. decide() would say
  // None, SDL still believes text input is active, and StartTextInput alone
  // would not call becomeFirstResponder again -- so the tap would do nothing.
  {
    State s;
    fieldEdge(s);
    s.requestVisible(true);
    CHECK(s.poll(kFieldOpen) == Action::Start);
    CHECK(s.poll(kFieldOpen) == Action::None && "state says it is already up");

    s.requestVisible(true); // asked for again, while we believe it is already up
    CHECK(s.poll(kFieldOpen) == Action::Restart);
    CHECK(s.poll(kFieldOpen) == Action::None && "one restart, not a loop");
  }

  // --- the armed restart is consumed exactly once, and only by a poll ---
  {
    State s;
    fieldEdge(s);
    s.requestVisible(true);
    CHECK(s.poll(kFieldOpen) == Action::Start);
    s.requestVisible(true);
    s.requestVisible(true); // twice; still one restart
    CHECK(s.poll(kFieldOpen) == Action::Restart);
    CHECK(s.poll(kFieldOpen) == Action::None);
  }
  {
    // A raise requested before there is a window: the caller returns early
    // WITHOUT polling, so the request must still be waiting when it can act.
    // This is why pumpHostTextInput() checks for the window first.
    State s;
    fieldEdge(s);
    s.requestVisible(true);
    // ... several frames with no window, and so no poll() at all ...
    CHECK(s.poll(kFieldOpen) == Action::Start && "the request survived");
  }

  // --- hiding when no field is open is inert ---
  //
  // The chip and the accessory bar only exist while a field is open, but a
  // queued tap could still land a frame late. It must not summon or dismiss
  // anything.
  {
    State s;
    s.requestVisible(false);
    CHECK(s.poll(kNoField) == Action::None);
    s.requestVisible(true);
    CHECK(s.poll(kNoField) == Action::None &&
           "a raise cannot summon a keyboard the firmware never asked for");
  }

  // --- wants() is what the harness paints the chip from ---
  {
    State s;
    CHECK(!s.wants(kNoField) && "no field, no keyboard, chip stays away");
    fieldEdge(s);
    CHECK(!s.wants(kFieldOpen) && "field just opened: keyboard stays down, chip shows");
    s.requestVisible(true);
    CHECK(s.wants(kFieldOpen) && "owner tapped the chip: keyboard comes up");
  }

  // --- the pure decision, pinned per branch ---
  {
    using hostkbd::decide;
    static_assert(decide(false, true, false) == Action::Start, "");
    static_assert(decide(false, true, true) == Action::Start,
                  "a raise from nothing is Start, not a spurious Restart");
    static_assert(decide(true, true, true) == Action::Restart, "");
    static_assert(decide(true, true, false) == Action::None, "");
    static_assert(decide(true, false, false) == Action::Stop, "");
    static_assert(decide(false, false, true) == Action::None,
                  "a stale force flag cannot raise a keyboard nobody wants");
    static_assert(hostkbd::wantsKeyboard(true, false), "");
    static_assert(!hostkbd::wantsKeyboard(true, true), "");
    static_assert(!hostkbd::wantsKeyboard(false, false), "");
  }

  std::puts("host_keyboard: PASS");
  return 0;
}
