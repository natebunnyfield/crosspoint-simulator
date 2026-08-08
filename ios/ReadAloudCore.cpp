#include "ReadAloudCore.h"

namespace {

// Fat-finger margin for tap hit-testing, in logical panel pixels: rects are
// glyph-tight and a fingertip is not.
constexpr int kTapInflatePx = 2;

void appendClear(std::vector<ReadAloudCore::Action> &out, bool &active) {
  if (!active)
    return;
  active = false;
  out.push_back({ReadAloudCore::Action::ClearHighlight});
}

} // namespace

std::vector<ReadAloudCore::Action> ReadAloudCore::setEnabled(bool enabled) {
  std::vector<Action> out;
  if (enabled_ == enabled)
    return out;
  enabled_ = enabled;
  if (!enabled_) {
    if (state_ == State::Speaking)
      out.push_back({Action::StopUtterance});
    appendClear(out, highlightActive_);
    state_ = State::Off;
  }
  // Enabling emits nothing: the next page render publishes, and pageArrived
  // starts speech.
  return out;
}

std::vector<ReadAloudCore::Action>
ReadAloudCore::pageArrived(const ReadAloudPage &page) {
  std::vector<Action> out;
  if (!enabled_)
    return out;
  if (state_ == State::Speaking)
    out.push_back({Action::StopUtterance});
  appendClear(out, highlightActive_);
  if (page.cleared || page.utf8.empty()) {
    rects_.clear();
    textBytes_ = 0;
    state_ = State::Off;
    return out;
  }
  rects_ = page.rects;
  textBytes_ = static_cast<uint32_t>(page.utf8.size());
  scanCursor_ = 0;
  Action start{Action::StartUtterance};
  start.utteranceByteOffset = 0;
  out.push_back(start);
  state_ = State::Speaking;
  return out;
}

std::vector<ReadAloudCore::Action> ReadAloudCore::utteranceFinished() {
  std::vector<Action> out;
  if (state_ != State::Speaking)
    return out;
  appendClear(out, highlightActive_);
  out.push_back({Action::TurnPageForward});
  state_ = State::AwaitingNextPage;
  return out;
}

std::vector<ReadAloudCore::Action> ReadAloudCore::utteranceCanceled() {
  std::vector<Action> out;
  if (state_ != State::Speaking)
    return out;
  appendClear(out, highlightActive_);
  state_ = State::Off;
  return out;
}

std::vector<ReadAloudCore::Action> ReadAloudCore::pageTimeout() {
  std::vector<Action> out;
  if (state_ != State::AwaitingNextPage)
    return out;
  appendClear(out, highlightActive_);
  state_ = State::Off;
  return out;
}

int ReadAloudCore::rectContaining(uint32_t byteOffset) {
  if (rects_.empty())
    return -1;
  if (scanCursor_ >= static_cast<int>(rects_.size()))
    scanCursor_ = 0;
  // Backwards jump (tap on an earlier word): restart the scan.
  if (byteOffset < rects_[static_cast<size_t>(scanCursor_)].byteOffset)
    scanCursor_ = 0;
  for (int i = scanCursor_; i < static_cast<int>(rects_.size()); i++) {
    const ReadAloudWordRect &r = rects_[static_cast<size_t>(i)];
    if (byteOffset < r.byteOffset)
      return -1; // in an inter-word gap; rects are in reading order
    if (byteOffset < r.byteOffset + r.byteLen) {
      scanCursor_ = i;
      return i;
    }
  }
  return -1;
}

std::vector<ReadAloudCore::Action>
ReadAloudCore::willSpeakByte(uint32_t absoluteByteOffset) {
  std::vector<Action> out;
  if (state_ != State::Speaking)
    return out;
  const int i = rectContaining(absoluteByteOffset);
  if (i < 0)
    return out;
  const ReadAloudWordRect &r = rects_[static_cast<size_t>(i)];
  if (highlightActive_ && highlightOffset_ == r.byteOffset &&
      highlightLen_ == r.byteLen)
    return out; // same word (or another fragment of it): nothing new
  highlightActive_ = true;
  highlightOffset_ = r.byteOffset;
  highlightLen_ = r.byteLen;
  Action a{Action::SetHighlight};
  a.highlightByteOffset = r.byteOffset;
  a.highlightByteLen = r.byteLen;
  out.push_back(a);
  return out;
}

std::vector<ReadAloudCore::Action> ReadAloudCore::tapAtLogical(int x, int y) {
  std::vector<Action> out;
  if (!enabled_ || rects_.empty() || state_ == State::AwaitingNextPage)
    return out;
  for (size_t i = 0; i < rects_.size(); i++) {
    const ReadAloudWordRect &r = rects_[i];
    if (x < static_cast<int>(r.x) - kTapInflatePx ||
        x >= static_cast<int>(r.x) + static_cast<int>(r.w) + kTapInflatePx ||
        y < static_cast<int>(r.y) - kTapInflatePx ||
        y >= static_cast<int>(r.y) + static_cast<int>(r.h) + kTapInflatePx)
      continue;
    if (state_ == State::Speaking)
      out.push_back({Action::StopUtterance});
    Action start{Action::StartUtterance};
    start.utteranceByteOffset = r.byteOffset;
    out.push_back(start);
    highlightActive_ = true;
    highlightOffset_ = r.byteOffset;
    highlightLen_ = r.byteLen;
    Action hl{Action::SetHighlight};
    hl.highlightByteOffset = r.byteOffset;
    hl.highlightByteLen = r.byteLen;
    out.push_back(hl);
    scanCursor_ = static_cast<int>(i);
    state_ = State::Speaking;
    return out;
  }
  return out;
}
