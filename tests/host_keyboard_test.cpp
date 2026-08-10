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
    assert(s.poll(kNoField) == Action::None);
    assert(s.poll(kNoField) == Action::None);

    // Field opens -> raise once, then stay put.
    fieldEdge(s);
    assert(s.poll(kFieldOpen) == Action::Start);
    assert(s.poll(kFieldOpen) == Action::None);
    assert(s.poll(kFieldOpen) == Action::None);

    // Field closes -> lower once.
    fieldEdge(s);
    assert(s.poll(kNoField) == Action::Stop);
    assert(s.poll(kNoField) == Action::None);
  }

  // --- the owner hides it, then asks for it back ---
  {
    State s;
    fieldEdge(s);
    assert(s.poll(kFieldOpen) == Action::Start);

    s.requestVisible(false);
    assert(s.suppressed());
    assert(!s.wants(kFieldOpen) && "hidden by request, though the field is open");
    assert(s.poll(kFieldOpen) == Action::Stop);
    assert(s.poll(kFieldOpen) == Action::None && "stays down until asked");

    s.requestVisible(true);
    assert(!s.suppressed());
    assert(s.poll(kFieldOpen) == Action::Start);
    assert(s.poll(kFieldOpen) == Action::None);
  }

  // --- suppression NEVER outlives the field, in either direction ---
  //
  // The bug this forbids: dismiss the keyboard once, and every text field for
  // the rest of the session opens without one, with nothing on screen saying
  // why and no setting to undo it.
  {
    State s;
    fieldEdge(s);
    assert(s.poll(kFieldOpen) == Action::Start);
    s.requestVisible(false);
    assert(s.poll(kFieldOpen) == Action::Stop);

    // Field closes with the hide still in force...
    fieldEdge(s);
    assert(!s.suppressed() && "the closing edge clears it");
    assert(s.poll(kNoField) == Action::None && "already down; nothing to do");

    // ...and the next field opens with a keyboard.
    fieldEdge(s);
    assert(s.poll(kFieldOpen) == Action::Start);
  }
  {
    // The same, when the hide is still in force as a NEW field opens directly
    // (activity to activity, no closed gap the caller polls in).
    State s;
    fieldEdge(s);
    assert(s.poll(kFieldOpen) == Action::Start);
    s.requestVisible(false);
    assert(s.poll(kFieldOpen) == Action::Stop);
    fieldEdge(s); // close
    fieldEdge(s); // open, without an intervening poll
    assert(!s.suppressed());
    assert(s.poll(kFieldOpen) == Action::Start);
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
    assert(s.poll(kFieldOpen) == Action::Start);
    assert(s.poll(kFieldOpen) == Action::None && "state says it is already up");

    s.requestVisible(true); // asked for, while we believe it is already up
    assert(s.poll(kFieldOpen) == Action::Restart);
    assert(s.poll(kFieldOpen) == Action::None && "one restart, not a loop");
  }

  // --- the armed restart is consumed exactly once, and only by a poll ---
  {
    State s;
    fieldEdge(s);
    assert(s.poll(kFieldOpen) == Action::Start);
    s.requestVisible(true);
    s.requestVisible(true); // twice; still one restart
    assert(s.poll(kFieldOpen) == Action::Restart);
    assert(s.poll(kFieldOpen) == Action::None);
  }
  {
    // A raise requested before there is a window: the caller returns early
    // WITHOUT polling, so the request must still be waiting when it can act.
    // This is why pumpHostTextInput() checks for the window first.
    State s;
    fieldEdge(s);
    s.requestVisible(true);
    // ... several frames with no window, and so no poll() at all ...
    assert(s.poll(kFieldOpen) == Action::Start && "the request survived");
  }

  // --- hiding when no field is open is inert ---
  //
  // The chip and the accessory bar only exist while a field is open, but a
  // queued tap could still land a frame late. It must not summon or dismiss
  // anything.
  {
    State s;
    s.requestVisible(false);
    assert(s.poll(kNoField) == Action::None);
    s.requestVisible(true);
    assert(s.poll(kNoField) == Action::None &&
           "a raise cannot summon a keyboard the firmware never asked for");
  }

  // --- wants() is what the harness paints the chip from ---
  {
    State s;
    assert(!s.wants(kNoField) && "no field, no keyboard, chip stays away");
    fieldEdge(s);
    assert(s.wants(kFieldOpen));
    s.requestVisible(false);
    assert(!s.wants(kFieldOpen) && "field open and keyboard down: chip shows");
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
