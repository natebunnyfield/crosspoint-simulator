// zensync::decide -- keeping the stored zenModeEnabled preference in sync
// with the live g_zen state in both directions, without the write-back
// direction re-triggering the read direction.
//
// WHY THIS IS A HOST TEST
//
// Neither NSUserDefaults nor a gesture recognizer exists on a host, so the
// two real triggers (a Settings.app edit, a one-finger hold above the paper)
// cannot be driven here at all. What CAN be driven, and is the part every
// failure mode above hides inside, is the decision: given where the store
// and the live state currently stand, which one should move. Truth-tabled
// here so the next change to pollZenMode() cannot silently reintroduce the
// echo loop this header exists to prevent.
//
// Build:
//   c++ -std=c++17 -Iios -o /tmp/zps tests/zen_pref_sync_test.cpp && /tmp/zps

#include "ZenPrefSync.h"

#include <cassert>
#include <cstdio>
#define TESTCHECK_FATAL_DIALECT
#include "TestCheck.h"

using zensync::Action;
using zensync::decide;

int main() {
  // --- boot ---
  // The very first call always seeds live FROM the store, whatever `synced`
  // happens to hold before anything has run -- there is no gesture yet to
  // have moved live away from it.
  CHECK(decide(/*storedPref=*/true, /*liveZen=*/false, /*synced=*/false,
               /*first=*/true) == Action::ApplyToLive);
  CHECK(decide(/*storedPref=*/false, /*liveZen=*/false, /*synced=*/false,
               /*first=*/true) == Action::ApplyToLive);

  // --- steady state: nothing changed ---
  CHECK(decide(true, true, true, false) == Action::None);
  CHECK(decide(false, false, false, false) == Action::None);

  // --- Settings.app edited the row while the app was backgrounded ---
  // synced still matches the OLD live value; the store is the one that
  // moved, so live must catch up to it.
  CHECK(decide(/*storedPref=*/true, /*liveZen=*/false, /*synced=*/false,
               false) == Action::ApplyToLive);
  CHECK(decide(/*storedPref=*/false, /*liveZen=*/true, /*synced=*/true,
               false) == Action::ApplyToLive);

  // --- a gesture toggled zen ---
  // synced still matches the OLD store value; live is the one that moved,
  // so the store must catch up to it. This is the direction that DID NOT
  // EXIST before this header: the bug this whole file fixes.
  CHECK(decide(/*storedPref=*/false, /*liveZen=*/true, /*synced=*/false,
               false) == Action::WriteToStore);
  CHECK(decide(/*storedPref=*/true, /*liveZen=*/false, /*synced=*/true,
               false) == Action::WriteToStore);

  // --- the feedback loop this header exists to prevent ---
  // After a WriteToStore is acted on, the caller sets synced := liveZen and
  // then re-reads the store on its NEXT poll. Simulate exactly that: the
  // store now equals what was written, and it must produce None, not another
  // ApplyToLive echoing the write straight back.
  {
    bool live = true;
    bool synced = false;
    CHECK(decide(/*storedPref=*/false, live, synced, false) ==
          Action::WriteToStore);
    // caller: write the store, then synced := live
    bool storedPref = live;
    synced = live;
    CHECK(decide(storedPref, live, synced, false) == Action::None);
    // ...and stays None over repeated polls with nothing new happening.
    CHECK(decide(storedPref, live, synced, false) == Action::None);
  }

  // Same for the read direction: after ApplyToLive is acted on (live :=
  // storedPref, synced := storedPref), the next poll must be None even
  // though `synced` started this whole sequence disagreeing with live.
  {
    bool storedPref = true;
    bool live = false;
    bool synced = false;
    CHECK(decide(storedPref, live, synced, false) == Action::ApplyToLive);
    live = storedPref;
    synced = storedPref;
    CHECK(decide(storedPref, live, synced, false) == Action::None);
  }

  // --- the CROSSPOINT_SIM_ZEN trap, found by adversarial review 2026-08-29
  // BEFORE it shipped, not after --- a caller must NEVER seed `synced` from
  // anything but this function's own answer. Demonstrate the failure mode a
  // naive caller would have hit, to pin the precondition rather than just
  // assert it in prose: an env override seeds live=true while the store
  // stays false, and a caller that (wrongly) set synced := live to "record"
  // that seed gets ApplyToLive right back -- reverting the override. This is
  // NOT a bug in decide() (every input here is internally consistent, and
  // the answer is the only sound one given what it was told); it is the
  // reason pollZenMode() must never call decide() at all while
  // CROSSPOINT_SIM_ZEN is set, which its own envForced gate now guarantees.
  {
    bool storedPref = false;  // unchanged; nothing ever writes it here
    bool live = true;         // env-forced at boot
    bool synced = live;       // the wrong thing a naive caller would do
    CHECK(decide(storedPref, live, synced, /*first=*/false) ==
          Action::ApplyToLive);  // <- would silently revert the env override
  }

  // NOTE ON THE "BOTH SIDES MOVED" CASE the header's comment names: with a
  // bool `synced`, storedPref != liveZen forces synced to equal exactly one
  // of them (a bool has only two values), so "neither side matches synced"
  // cannot actually occur -- the header's comment describes the reasoning
  // that makes WriteToStore the deliberate, stated answer whenever live is
  // the side that moved, not a third case this test could exercise
  // separately from the ones above.

  std::puts("zen_pref_sync_test: all checks passed");
  return 0;
}
