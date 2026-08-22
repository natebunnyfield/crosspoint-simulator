#pragma once

#include <cmath>
#include <cstdint>

// The zen gesture language (owner ruling 2026-08-22, verbatim): "let's switch
// to tap is Down button, swipe right is Up, swipe left is Down, two finger
// swipe left is Right, two finger swipe is right is Left, two finger swipe
// down is Select button, two finger swipe up is Back button, four finger tap
// is Power button." Amended the same day: "pinch and spread control font size
// (go one size up, go one size down)."
//
// This REPLACES the zen tap zones (the screen thirds and the above/below-paper
// bands, shipped 2026-08-19..22). It also SUPERSEDES the same-day no-swipe
// ruling ("need to disable all swiping, we want all taps to be as deliberate
// as possible", owner 2026-08-22) -- the swipes are back, as the language
// itself, but the deliberate-tap DISCIPLINE survives here as the tap gate:
// the shipped constants (28 px slop, 400 ms) still decide what counts as a
// tap, and anything ambiguous fires NOTHING rather than the nearest verb.
//
// Same discipline as PadCore and ZenGesture beside it: pure, clock-free, no
// SDL types, so the rules are provable off-device. The caller feeds finger
// events with positions, ids and its own millisecond timestamps; the
// classifier answers on the LAST lift with at most one verb per gesture.
//
// THE RULES, each one a way a real hand fails a gesture:
//
//   * finger count is the PEAK concurrent fingers, and every finger that
//     touched must have been part of that peak (touched == peak). A hand
//     rolling across the glass -- lift one, land another -- is not any
//     gesture.
//   * TAP: every finger's whole-gesture excursion stays within 28 px and the
//     gesture (first down to last lift) takes at most 400 ms. One finger is
//     Down; four is Power; two, three (the zen toggle's count, owned by
//     ZenGesture), five and up are nothing.
//   * SWIPE: at most 700 ms, direction from the AVERAGE of the fingers'
//     down-to-final vectors (a finger that lifts early contributes its final
//     position), dominant-axis travel >= 60 px with the dominant axis at
//     least twice the cross axis -- a diagonal is ambiguous and fires
//     nothing. One finger: left is Down, right is Up, vertical is nothing.
//     Two fingers: left is Right, right is Left, down is Select, up is Back.
//     Three or more fingers swiping is nothing.
//   * PINCH / SPREAD (two fingers only): the inter-finger distance changes by
//     at least 60 px while the centroid stays within 28 px -- opposed motion,
//     where a swipe is common motion. Shrinking is FontDown (one size down),
//     growing is FontUp (one size up). Distance and centroid both large, or
//     both small, is ambiguous and fires nothing.
//   * a cancelled finger (iOS takes touches for its own gestures) poisons the
//     whole gesture. So does an eleventh finger.
namespace zenverbs {

enum class Verb {
  None,
  Down,      // 1-finger tap, 1-finger swipe left
  Up,        // 1-finger swipe right
  Left,      // 2-finger swipe right
  Right,     // 2-finger swipe left
  Select,    // 2-finger swipe down, 2-finger tap
  Back,      // 2-finger swipe up
  Power,     // 4-finger tap
  FontUp,    // 2-finger spread
  FontDown,  // 2-finger pinch
};

// The deliberate-tap gate, unchanged from the zone tracker it replaces.
constexpr float kTapSlopPx = 28.0f;
constexpr uint64_t kTapMaxMs = 400;
// TOUCH_SWIPE_MIN_PX precedent (src/HalGPIO.cpp).
constexpr float kSwipeMinPx = 60.0f;
constexpr float kSwipeAxisRatio = 2.0f;
constexpr uint64_t kSwipeMaxMs = 700;
// Pinch: opposed travel past the swipe threshold, centroid within the tap slop.
constexpr float kPinchMinPx = 60.0f;
constexpr float kPinchCentroidMaxPx = 28.0f;

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
  Verb fingerUp(int64_t id, float x, float y, uint64_t tMs, bool cancelled = false) {
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
    // passes through low peaks without ever being any of these gestures.
    if (touched_ != peak_ || touched_ == 0) return Verb::None;
    const uint64_t durMs = tMs >= firstDownMs_ ? tMs - firstDownMs_ : 0;

    bool allWithinTapSlop = true;
    float sumDx = 0, sumDy = 0;
    for (int i = 0; i < touched_; ++i) {
      if (slots_[i].excursion > kTapSlopPx) allWithinTapSlop = false;
      sumDx += slots_[i].lastX - slots_[i].downX;
      sumDy += slots_[i].lastY - slots_[i].downY;
    }

    if (allWithinTapSlop && durMs <= kTapMaxMs) {
      // Three fingers belong to the zen toggle (ZenGesture.h); answering None
      // here is what keeps one gesture from having two owners.
      if (peak_ == 1) return Verb::Down;
      if (peak_ == 2) return Verb::Select;   // owner 2026-08-22: "confirm is
                                             // also two finger tap"
      if (peak_ == 4) return Verb::Power;
      return Verb::None;
    }

    if (durMs > kSwipeMaxMs) return Verb::None;
    const float avgDx = sumDx / static_cast<float>(touched_);
    const float avgDy = sumDy / static_cast<float>(touched_);

    if (peak_ == 2) {
      // Opposed vs common motion: a pinch changes the inter-finger distance
      // while the centroid stays put; a swipe moves the centroid while the
      // distance holds. Final positions, so a finger that lifted early still
      // counts where it ended.
      const float d0 = std::hypot(slots_[1].downX - slots_[0].downX,
                                  slots_[1].downY - slots_[0].downY);
      const float d1 = std::hypot(slots_[1].lastX - slots_[0].lastX,
                                  slots_[1].lastY - slots_[0].lastY);
      const float dd = d1 - d0;
      const float centroid = std::hypot(avgDx, avgDy);
      if (std::fabs(dd) >= kPinchMinPx) {
        if (centroid < kPinchCentroidMaxPx)
          return dd > 0 ? Verb::FontUp : Verb::FontDown;
        return Verb::None;  // both opposed and common motion: ambiguous
      }
    } else if (peak_ != 1) {
      return Verb::None;  // 3+ finger swipes are nobody's gesture
    }

    const float ax = std::fabs(avgDx), ay = std::fabs(avgDy);
    if (ax >= ay) {
      if (ax < kSwipeMinPx || ax < kSwipeAxisRatio * ay) return Verb::None;
      if (peak_ == 1) return avgDx < 0 ? Verb::Down : Verb::Up;
      return avgDx < 0 ? Verb::Right : Verb::Left;
    }
    if (ay < kSwipeMinPx || ay < kSwipeAxisRatio * ax) return Verb::None;
    if (peak_ == 1) return Verb::None;  // no vertical 1-finger verb
    return avgDy > 0 ? Verb::Select : Verb::Back;
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

// The verb's button, in the firmware's terms. Kept beside the classifier so
// the mapping is testable; the shim only forwards it to queueButtonTap.
// FontUp/FontDown have no row here: they resolve to the SIDE pair (see the
// shim), because on this fork a side-button tap IS the font-size step
// (CrossPointSettings.h: longPressButtonBehavior is constexpr FONT_SIZE_STEP,
// sideButtonLayout constexpr PREV_NEXT, so PageForward/BTN_DOWN steps +1 and
// PageBack/BTN_UP steps -1 in EpubReaderActivity::stepReaderFontSize, clamped
// at the ramp ends with no wrap and no settings write when already there).
inline const char *verbName(Verb v) {
  switch (v) {
    case Verb::Down: return "down";
    case Verb::Up: return "up";
    case Verb::Left: return "left";
    case Verb::Right: return "right";
    case Verb::Select: return "select";
    case Verb::Back: return "back";
    case Verb::Power: return "power";
    case Verb::FontUp: return "font up";
    case Verb::FontDown: return "font down";
    case Verb::None: break;
  }
  return "none";
}

}  // namespace zenverbs
