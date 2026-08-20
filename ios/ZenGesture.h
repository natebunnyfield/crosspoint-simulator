#pragma once

#include <algorithm>
#include <cmath>

// The three-finger tap that toggles zen reading mode (ST-011), as a pure state
// machine so it can be TESTED. The shim's event handler cannot be: it needs SDL,
// a window, and UIKit delivering real multitouch, none of which exist off-device
// -- and the harness's own input script cannot drive it either, because its TAP
// feeds the firmware's touch state rather than SDL finger events.
//
// Same discipline as PadCore beside it: pure, clock-free, no SDL types. The
// caller feeds it events and asks one question.
//
// WHAT COUNTS AS THE GESTURE, and every clause is a way a real hand fails it:
//
//   * THREE fingers were down at once, AND exactly three touched at all. Peak
//     alone is not enough: a hand rolling across the page can lift one finger
//     and land two more, passing through a peak of three without ever being a
//     three-finger tap. The test caught that; counting participants kills it.
//   * every one of them lifted. A finger still on the glass means the gesture is
//     not over.
//   * none of them travelled past the slop. Three fingers dragging is a scroll
//     or a system gesture, not a tap.
//   * the last one lifted ON the page. The page is the target the owner named;
//     three fingers landing on the pad or the margins are not a zen toggle.
//   * nothing was cancelled. iOS cancels touches for its own gestures, and a
//     cancelled touch is not a lift.
namespace zengesture {

struct Rect {
  float x = 0, y = 0, w = 0, h = 0;
  bool contains(float px, float py) const {
    return w > 0 && h > 0 && px >= x && px < x + w && py >= y && py < y + h;
  }
};

class Detector {
 public:
  // Slop in device pixels. Generous on purpose: three fingers roll slightly as
  // they lift, and a tight budget rejects taps a person would call clean.
  explicit Detector(float slopPx = 44.0f) : slop_(slopPx) {}

  void fingerDown(float x, float y) {
    if (active_ == 0) {
      moved_ = false;
      cancelled_ = false;
      peak_ = 0;
      touched_ = 0;
    }
    active_++;
    touched_++;
    peak_ = std::max(peak_, active_);
    lastX_ = x;
    lastY_ = y;
  }

  void fingerMoved(float x, float y) {
    if (std::fabs(x - lastX_) > slop_ || std::fabs(y - lastY_) > slop_) moved_ = true;
  }

  // Returns true when THIS lift completes a qualifying three-finger tap.
  bool fingerUp(float x, float y, const Rect &page, bool cancelled = false) {
    lastX_ = x;
    lastY_ = y;
    if (cancelled) cancelled_ = true;
    active_ = std::max(0, active_ - 1);
    if (active_ != 0) return false;  // fingers still down: not over yet
    const bool fired = peak_ == 3 && touched_ == 3 && !moved_ && !cancelled_ &&
                       page.contains(x, y);
    peak_ = 0;
    touched_ = 0;
    moved_ = false;
    cancelled_ = false;
    return fired;
  }

  int activeFingers() const { return active_; }

 private:
  float slop_;
  int active_ = 0;
  int peak_ = 0;
  int touched_ = 0;  // how many fingers took part at all, not just at once
  bool moved_ = false;
  bool cancelled_ = false;
  float lastX_ = 0, lastY_ = 0;
};

}  // namespace zengesture
