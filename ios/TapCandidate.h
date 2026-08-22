#pragma once

#include <cmath>
#include <cstdint>

// The page-tap candidate: a finger that landed on NO pad control may become a
// read-aloud word tap, a palette-chip tap, or a keyboard-chip tap on lift.
// Extracted from the shim's event watch (2026-08-21 input-lifecycle audit,
// findings #1 and #3) so the arm/spoil rules are provable on a host — the SDL
// event watch itself cannot be compiled off-device, and every failure mode
// here is silent:
//
//   * a candidate that stays LATCHED after a gesture-consuming exit (the zen
//     toggle's early break was one) leaves the chips and read-aloud taps dead
//     until backgrounding, because arming is gated on "no candidate armed";
//   * a candidate that FIRES while additional fingers are down gives one
//     gesture two effects (the word tap, then the last lift's zen toggle).
//
// The rule for both is the same as the zen classifier's spoil-on-multi
// discipline: a chip tap or word tap is a ONE-finger gesture, so a second
// concurrent finger spoils the candidate outright, and every consuming exit
// (toggle resolved, mixer sheet up, backgrounding, wake) clears it.
//
// Pure and clock-free like PadCore beside it: the caller supplies coordinates
// and its own timestamps, and reads back where/when the tap went down.
// Tested by tests/tap_candidate_test.cpp.
namespace tapcand {

class Candidate {
 public:
  // A finger landed. `onControl` = it hit a pad slot (controls own their own
  // taps and never arm a candidate); `concurrent` = fingers on the glass
  // INCLUDING this one. Any second finger spoils whatever was armed and
  // prevents arming — audit #3's fix, and the reason audit #1's latch cannot
  // recur through the multi-finger path.
  void fingerDown(long long id, float x, float y, uint64_t tMs, bool onControl,
                  int concurrent) {
    if (concurrent > 1) {
      id_ = kNone;
      return;
    }
    if (!onControl && id_ == kNone) {
      id_ = id;
      x_ = x;
      y_ = y;
      downMs_ = tMs;
    }
  }

  // Travel past the slop makes it a swipe, not a tap.
  void fingerMove(long long id, float x, float y, float slopPx) {
    if (id != id_) return;
    if (std::fabs(x - x_) > slopPx || std::fabs(y - y_) > slopPx) id_ = kNone;
  }

  // The lift. True = fire the tap (at downX/downY, recorded at the DOWN).
  // ALWAYS clears when the id matches, whatever the answer — no exit path may
  // leave the id latched (audit #1). A cancelled lift (iOS took the touch) is
  // not a tap.
  bool fingerUp(long long id, bool cancelled) {
    if (id != id_) return false;
    id_ = kNone;
    return !cancelled;
  }

  // Gesture-consuming exits: the zen toggle resolved, the mixer sheet is up,
  // the app backgrounded, a wake began. Whatever was armed is nobody's tap
  // now. Idempotent.
  void spoil() { id_ = kNone; }

  bool armed() const { return id_ != kNone; }
  bool armedAs(long long id) const { return id_ != kNone && id_ == id; }
  float downX() const { return x_; }
  float downY() const { return y_; }
  uint64_t downMs() const { return downMs_; }

 private:
  static constexpr long long kNone = -1;
  long long id_ = kNone;
  float x_ = 0, y_ = 0;
  uint64_t downMs_ = 0;
};

}  // namespace tapcand
