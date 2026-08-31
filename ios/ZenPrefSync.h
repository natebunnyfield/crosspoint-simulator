#pragma once

// Keeps the STORED zenModeEnabled preference honest about the LIVE zen
// state -- whichever side changed it last -- so Settings.app's Zen Mode row
// never goes stale after a gesture toggle (the 0.75 s hold above the paper,
// CrossPointZen_toggleFromRecognizer in CrossPointIOSShim.cpp).
//
// Owner bug report, verbatim: "keep zen mode ios app setting reflective of
// active value." Reproduced by reading the code before this header existed:
// CrossPointPrefs_zenModeEnabled() was READ-ONLY (no setter existed at all --
// grep confirmed zero calls to any CrossPointPrefs_setZenModeEnabled, because
// the function did not exist), and the only writer of the `zenModeEnabled`
// key was Settings.app itself. A gesture toggle changed g_zen and nothing
// else; the store kept whatever it last held, so the row showed the WRONG
// value from that moment on, and the next visit to Settings.app could
// silently flip zen back to what the row (wrongly) still said, undoing a
// toggle the reader made minutes ago.
//
// WHY A SHARED TRACKER RATHER THAN A DIRECT WRITE FROM THE GESTURE HANDLER.
// A direct `CrossPointPrefs_setZenModeEnabled(g_zen)` call from the toggle
// handler would change what pollZenMode()'s NEXT poll of the store reads.
// With nothing telling that poll the change was its OWN echo, it is
// indistinguishable from an external Settings.app edit and would re-run the
// "apply the store to live" branch -- harmless only because it would
// reapply the SAME value it just wrote, which is luck, not a guarantee, and
// is exactly the shape of feedback loop that breaks the day either branch
// grows a real side effect (this file's `ApplyToLive` already carries a
// relayout and a present request). `synced` below is the value BOTH
// directions last agreed on; whichever side has moved away from it is the
// one that changed, and `decide()` walks the OTHER side to meet it -- so a
// write can never be read back as a fresh external change, and an external
// change can never be mistaken for an echo of our own write.
//
// Pure and UIKit-free like HostKeyboardState.h and GestureBindings.h, and
// for the identical reason stated in each: every way this can be wrong is
// silent on a device (a stale Settings row, or a gesture that quietly
// reverts on the next launch) and neither NSUserDefaults nor a gesture
// recognizer can be driven or watched from a host, so the decision has to
// live somewhere a host test CAN drive it.
namespace zensync {

enum class Action {
  None,          // store and live already agree; nothing to do
  ApplyToLive,   // the store changed (Settings.app) -- make live zen match it
  WriteToStore,  // live zen changed (a gesture) -- make the store match it
};

// `storedPref`: what CrossPointPrefs_zenModeEnabled() reads right now.
// `liveZen`: g_zen right now.
// `synced`: the value both sides were last made to agree on -- the
// caller's own bookkeeping, updated to the new agreed value after acting on
// whatever this function answers.
// `first`: true only for the very first call this process ever makes, so a
// fresh launch SEEDS live zen from the store (the existing boot behavior --
// registered default is ON, per Settings.bundle/Root.plist) rather than
// reading the initial `synced` as a gesture that already fired before the
// app had drawn a single frame.
//
// `synced` is a bool, so it can only ever equal ONE of the two disagreeing
// values (never neither, never both) -- which makes the answer total rather
// than a guess: if the store and the live state already agree, `synced`
// already equals both and there is nothing to reconcile. If they disagree,
// exactly one of them still matches `synced` -- that one has NOT moved
// since the last reconciliation, so the OTHER one is the fresh change, and
// it wins. There is no third, genuinely ambiguous case to resolve (a
// gesture and an external Settings.app edit landing in the same poll
// interval would still leave `synced` matching one side or the other, never
// neither) -- every disagreement this function is asked about has exactly
// one side that moved, by construction.
//
// THE PRECONDITION THIS TOTALITY ARGUMENT DEPENDS ON, found missing by
// adversarial review 2026-08-29: `synced` may ONLY ever be set to a value
// this function itself just told the caller to make true (i.e., to
// `storedPref` after acting on `ApplyToLive`, or to `liveZen` after acting
// on `WriteToStore`). CROSSPOINT_SIM_ZEN can seed `liveZen` to a value that
// deliberately, permanently DISAGREES with `storedPref` -- an env-forced
// launch state is not the output of any call to this function, so if a
// caller called `decide()` once to get past `first` and then set `synced :=
// liveZen` to match the env override, the totality argument above breaks
// silently: the NEXT call sees `storedPref != liveZen` (still true, nothing
// wrote the store) and `liveZen == synced` (both left at the env value) and
// concludes the STORE moved, quietly overwriting the env override. The fix
// is not in this function -- it is that `CrossPointIOSShim.cpp`'s
// `pollZenMode()` does NOT call `decide()` at all while
// `CROSSPOINT_SIM_ZEN` is set (its own `envForced` gate returns first), so
// this function is simply never asked to reconcile a disagreement it was
// never told to create. Any future caller of `decide()` must keep that
// same discipline: never seed `synced` from anything but this function's
// own answer.
constexpr Action decide(bool storedPref, bool liveZen, bool synced,
                         bool first) {
  if (first) return Action::ApplyToLive;
  if (storedPref == liveZen) return Action::None;
  if (liveZen != synced) return Action::WriteToStore;
  return Action::ApplyToLive;
}

}  // namespace zensync
