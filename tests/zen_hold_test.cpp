// The ONE-FINGER HOLD's two thresholds and three outcomes (ios/ZenHoldRouting.h).
//
// Owner ruling 2026-08-27: a hold of 0.75 s .. 5 s fires SELECT on the lift; a
// hold that reaches 5 s fires the zen TOGGLE at the 5 s mark under the finger
// and the lift is then silent. Exactly one action per hold, never both.
//
// This test exists for the same reason tests/text_entry_enter_test.cpp does:
// both inversions of a two-way routing rule are invisible at runtime. A select
// that stops firing reads as "the phone did not deliver the gesture"; a select
// that fires alongside the toggle reads as "the toggle misfired". Neither shows
// up in a screenshot and neither can be driven off-device — UIKit recognizers
// live above SDL, so no scripted run and no simctl can reach them. So the
// recognizer is reduced to reporting events, and the whole decision is here.
//
// The sweep is the boundaries the owner named plus the two poisons: just under
// and just over each threshold, a cancelled touch, a second finger mid-hold,
// and that the tracker comes back clean for the next hold.
#include "ZenHoldRouting.h"

#include <cstdio>

#include "TestCheck.h"
using testcheck::check;

namespace {

using zenhold::Action;
using zenhold::Hold;

int &failures = testcheck::g_failures;

void checkAction(Action got, Action want, const char *what) {
  if (got != want) {
    std::printf("FAIL: %s (got '%s', want '%s')\n", what,
                zenhold::actionName(got), zenhold::actionName(want));
    failures++;
  }
}

// One clean hold of `holdMs`, with the 5 s deadline delivered if it is reached
// — which is exactly what the pair of recognizers does on the phone.
Action cleanHold(uint32_t holdMs) {
  Hold h;
  const uint32_t t0 = 10'000;
  h.begin(t0);
  Action deadline = Action::None;
  if (holdMs >= zenhold::kToggleMs) deadline = h.deadline();
  const Action lift = h.release(t0 + holdMs);
  // Never two actions from one hold.
  if (deadline != Action::None && lift != Action::None) {
    std::printf("FAIL: hold of %u ms fired BOTH '%s' and '%s'\n", holdMs,
                zenhold::actionName(deadline), zenhold::actionName(lift));
    failures++;
  }
  return deadline != Action::None ? deadline : lift;
}

}  // namespace

int main() {
  // ---- The truth table, at the boundaries the owner named. ----
  //
  // 0.75 s is the select threshold and it did NOT move (owner 2026-08-22, from
  // device: "long tap select is too fast. make at least 1.5x longer"). Only
  // when it fires changed.
  checkAction(cleanHold(0), Action::None, "instant lift: nothing");
  checkAction(cleanHold(399), Action::None, "a tap: nothing (that is ZenVerbs')");
  checkAction(cleanHold(749), Action::None, "just under 0.75 s: nothing");
  checkAction(cleanHold(750), Action::Select, "exactly 0.75 s: select");
  checkAction(cleanHold(751), Action::Select, "just over 0.75 s: select");
  checkAction(cleanHold(2500), Action::Select, "mid-window: select");
  checkAction(cleanHold(4999), Action::Select, "just under 5 s: select");
  checkAction(cleanHold(5000), Action::Toggle, "exactly 5 s: toggle, not select");
  checkAction(cleanHold(5001), Action::Toggle, "just over 5 s: toggle, not select");
  checkAction(cleanHold(30'000), Action::Toggle, "a very long hold: toggle");

  // ---- The lift after a toggle is SILENT, and says so through both gates. ----
  //
  // The latch and the elapsed-time check are deliberately redundant: the lift
  // and the 5 s deadline can arrive in either order at the boundary, and a
  // recognizer's .ended can be delivered before the paired recognizer's .began
  // on the same run loop turn.
  {
    Hold h;
    h.begin(1000);
    checkAction(h.deadline(), Action::Toggle, "deadline under the finger toggles");
    checkAction(h.release(6100), Action::None, "the lift after a toggle is silent");
  }
  {
    // Latch alone, with a short elapsed time: if the deadline somehow fires
    // early, the lift still must not select.
    Hold h;
    h.begin(1000);
    checkAction(h.deadline(), Action::Toggle, "early deadline toggles");
    checkAction(h.release(2000), Action::None,
                "a 1 s lift after a toggle still selects nothing");
  }
  {
    // Elapsed alone, with no deadline delivered (the recognizer failed for
    // movement, say): a >= 5 s hold must not fall back to select.
    Hold h;
    h.begin(1000);
    checkAction(h.release(7000), Action::None,
                "6 s with no deadline delivered: still no select");
  }

  // ---- The deadline fires at most once per hold. ----
  //
  // Two toggles cancel out, which on device reads as the gesture doing nothing.
  {
    Hold h;
    h.begin(1000);
    checkAction(h.deadline(), Action::Toggle, "first deadline toggles");
    checkAction(h.deadline(), Action::None, "second deadline is a no-op");
  }

  // ---- Poisons: neither action fires. ----
  //
  // Same discipline as ZenVerbs.h — a touch iOS takes for its own gesture, or
  // a hand that lands a second finger, is not a deliberate hold.
  {
    Hold h;
    h.begin(1000);
    h.cancel();
    checkAction(h.deadline(), Action::None, "cancelled: the deadline is silent");
    checkAction(h.release(6000), Action::None, "cancelled: the lift is silent");
  }
  {
    Hold h;
    h.begin(1000);
    h.cancel();
    checkAction(h.release(2000), Action::None,
                "cancelled inside the select window: no select");
  }
  {
    Hold h;
    h.begin(1000);
    h.noteTouches(2);
    checkAction(h.release(2000), Action::None, "a second finger kills the select");
  }
  {
    Hold h;
    h.begin(1000);
    h.noteTouches(2);
    checkAction(h.deadline(), Action::None, "a second finger kills the toggle");
  }
  {
    Hold h;
    h.begin(1000);
    h.noteTouches(1);
    checkAction(h.release(2000), Action::Select, "one finger throughout: select");
  }

  // ---- The tracker recovers. A sticky poison would mean select never fires
  // again, with nothing on screen or in the log to say why. ----
  {
    Hold h;
    h.begin(1000);
    h.cancel();
    checkAction(h.release(2000), Action::None, "poisoned hold: nothing");
    h.begin(10'000);
    checkAction(h.release(11'000), Action::Select, "the next hold selects again");
  }
  {
    Hold h;
    h.begin(1000);
    checkAction(h.deadline(), Action::Toggle, "hold one toggles");
    checkAction(h.release(6000), Action::None, "hold one's lift is silent");
    h.begin(20'000);
    checkAction(h.release(21'000), Action::Select,
                "the hold after a toggle selects again");
  }

  // ---- An IDLE tracker answers the deadline. ----
  //
  // Out of zen the select recognizer is DISABLED, so nothing calls begin() —
  // but the 5 s toggle is always enabled and must still fire. This is the case
  // a tracker that gated the deadline on active() would silently break in one
  // mode only.
  {
    Hold h;
    checkAction(h.deadline(), Action::Toggle, "idle tracker: the toggle still fires");
  }
  {
    // ...and it must not be poisoned by a hold that ended long ago.
    Hold h;
    h.begin(1000);
    h.cancel();
    (void)h.release(2000);
    checkAction(h.deadline(), Action::Toggle,
                "a previous hold's poison does not survive into the next toggle");
  }

  // ---- A lift with no begin() fires nothing. ----
  {
    Hold h;
    checkAction(h.release(9000), Action::None, "a lift with no hold: nothing");
  }

  // ---- The pure predicates, addressed directly. ----
  checkAction(zenhold::onRelease(749, false, false), Action::None, "pure: 749 ms");
  checkAction(zenhold::onRelease(750, false, false), Action::Select, "pure: 750 ms");
  checkAction(zenhold::onRelease(4999, false, false), Action::Select, "pure: 4999 ms");
  checkAction(zenhold::onRelease(5000, false, false), Action::None, "pure: 5000 ms");
  checkAction(zenhold::onRelease(2000, true, false), Action::None, "pure: poisoned");
  checkAction(zenhold::onRelease(2000, false, true), Action::None, "pure: toggled");
  checkAction(zenhold::onToggleDeadline(false, false), Action::Toggle,
              "pure deadline: clean");
  checkAction(zenhold::onToggleDeadline(true, false), Action::None,
              "pure deadline: poisoned");
  checkAction(zenhold::onToggleDeadline(false, true), Action::None,
              "pure deadline: already toggled");

  check(zenhold::kSelectMs == 750, "the select threshold is still the owner's 0.75 s");
  check(zenhold::kToggleMs == 5000, "the toggle threshold is the owner's 5 s");
  check(zenhold::kSelectMs < zenhold::kToggleMs,
        "the select window opens before the toggle deadline");

  if (failures == 0) {
    std::printf("zen_hold_test: all checks passed\n");
    return 0;
  }
  std::printf("zen_hold_test: %d FAILURES\n", failures);
  return 1;
}
