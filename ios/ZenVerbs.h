#pragma once

#include <cmath>
#include <cstdint>

// The zen DELIBERATE TAP — the one gesture left on the SDL finger stream.
//
// Succession (all owner rulings, 2026-08-22): the tap ZONES (screen thirds,
// 2026-08-19..22) were replaced by a hand-rolled gesture LANGUAGE classified
// here ("let's switch to tap is Down button, swipe right is Up, ..."); the
// device then showed the hand-rolled thresholds mis-modeled real hands ("two
// finger left and right swap is not working most of the time, spread and
// pinch never worked"), and the owner moved every gesture that MOVES to
// Apple's recognition engine ("are these not ios standard gestures?", "let's
// use apple for swiping instead") — see ios/CrossPointZenRecognizers.mm for
// the recognizer set and the full mapping table. What stays here is exactly
// one verb: the ONE-FINGER DELIBERATE TAP, page forward.
//
// The deliberate-tap DISCIPLINE survives from the no-swipe ruling ("we want
// all taps to be as deliberate as possible"): the shipped constants (28 px
// slop, 400 ms) still decide what counts as a tap, and anything else fires
// NOTHING here — motion, multi-finger taps and the three-finger toggle all
// belong to the recognizers ("be sure to swap 3 finger tap to apple"). That
// split is also what makes a double fire impossible by construction: a touch
// that fires a swipe recognizer traveled far past the 28 px slop, so this
// classifier answers None for it, and a tap inside the slop is motion no
// swipe recognizer recognizes.
//
// Same discipline as PadCore and ZenGesture beside it: pure, clock-free, no
// SDL types, so the rules are provable off-device. The caller feeds finger
// events with positions, ids and its own millisecond timestamps; the
// classifier answers on the LAST lift with at most one verb per gesture.
//
// THE RULES, each one a way a real hand fails the tap:
//
//   * finger count is the PEAK concurrent fingers, and every finger that
//     touched must have been part of that peak (touched == peak). A hand
//     rolling across the glass -- lift one, land another -- is not a tap.
//   * exactly ONE finger. Two is the recognizers' select, three is the zen
//     toggle's (also a recognizer), four is the recognizers' power; all None
//     here.
//   * the finger's whole-gesture excursion stays within 28 px and the gesture
//     (down to lift) takes at most 400 ms. Anything that travels or lingers
//     is None — travel is the recognizers' domain now.
//   * a cancelled finger (iOS takes touches for its own gestures) poisons the
//     whole gesture. So does an eleventh finger.
namespace zenverbs {

enum class Verb {
  None,
  Down,  // 1-finger deliberate tap -> page forward (the swap ruling maps it
         // to the front Right button in the shim)
};

// The deliberate-tap gate, unchanged since the zone tracker.
constexpr float kTapSlopPx = 28.0f;
constexpr uint64_t kTapMaxMs = 400;

class Classifier {
 public:
  void fingerDown(int64_t id, float x, float y, uint64_t tMs) {
    if (active_ == 0) reset();
    if (active_ == 0) firstDownMs_ = tMs;
    active_++;
    if (active_ > peak_) peak_ = active_;
    if (touched_ >= kMaxFingers) {
      overflow_ = true;
      return;
    }
    Finger &f = slots_[touched_++];
    f.id = id;
    f.downX = f.lastX = x;
    f.downY = f.lastY = y;
    f.excursion = 0.0f;
    f.up = false;
  }

  void fingerMove(int64_t id, float x, float y) {
    Finger *f = find(id);
    if (!f) return;
    f->lastX = x;
    f->lastY = y;
    const float ex = std::fabs(x - f->downX), ey = std::fabs(y - f->downY);
    if (ex > f->excursion) f->excursion = ex;
    if (ey > f->excursion) f->excursion = ey;
  }

  // The classifier answers only when THIS lift is the last one.
  Verb fingerUp(int64_t id, float x, float y, uint64_t tMs,
                bool cancelled = false) {
    Finger *f = find(id);
    if (f) {
      fingerMove(id, x, y);
      f->up = true;
    }
    if (cancelled) cancelled_ = true;
    if (active_ > 0) active_--;
    if (active_ != 0) return Verb::None;  // fingers still down: not over yet
    const Verb v = classify(tMs);
    reset();
    return v;
  }

  int activeFingers() const { return active_; }

 private:
  struct Finger {
    int64_t id = 0;
    float downX = 0, downY = 0;
    float lastX = 0, lastY = 0;
    float excursion = 0;  // peak Chebyshev distance from the landing point
    bool up = false;
  };
  static constexpr int kMaxFingers = 10;

  Finger *find(int64_t id) {
    for (int i = 0; i < touched_; ++i)
      if (slots_[i].id == id && !slots_[i].up) return &slots_[i];
    return nullptr;
  }

  Verb classify(uint64_t tMs) const {
    if (cancelled_ || overflow_) return Verb::None;
    // Every participant must have been down at the peak: a rolling hand
    // passes through low peaks without ever being a tap.
    if (touched_ != peak_ || touched_ == 0) return Verb::None;
    // One finger only: every multi-finger gesture has another owner now
    // (recognizers; the 3-finger toggle is ZenGesture's).
    if (peak_ != 1) return Verb::None;
    const uint64_t durMs = tMs >= firstDownMs_ ? tMs - firstDownMs_ : 0;
    if (durMs > kTapMaxMs) return Verb::None;
    if (slots_[0].excursion > kTapSlopPx) return Verb::None;
    return Verb::Down;
  }

  void reset() {
    touched_ = 0;
    active_ = 0;
    peak_ = 0;
    overflow_ = false;
    cancelled_ = false;
    firstDownMs_ = 0;
  }

  Finger slots_[kMaxFingers];
  int touched_ = 0;
  int active_ = 0;
  int peak_ = 0;
  bool overflow_ = false;
  bool cancelled_ = false;
  uint64_t firstDownMs_ = 0;
};

inline const char *verbName(Verb v) {
  switch (v) {
    case Verb::Down: return "down";
    case Verb::None: break;
  }
  return "none";
}

}  // namespace zenverbs
