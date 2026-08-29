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
    // Paused counts as speaking here: the engine is still holding an
    // utterance, and leaving it held is how you get speech back the moment
    // something calls continueSpeaking.
    if (state_ == State::Speaking || state_ == State::Paused)
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

  // THE SAME PAGE AGAIN IS NOT A PAGE TURN.
  //
  // The reader re-renders on things that do not move the position:
  // ActivityManager requests an update on EVERY subactivity pop ("ensure the
  // popped activity gets re-rendered"), and an appearance change reaches
  // crosspointRequestRender() the same way. Each of those republishes the
  // current page byte for byte. Without this branch pageArrived treated it as
  // new -- stop, clear the highlight, start again at offset 0 -- so opening
  // chapter selection and coming back re-spoke the page from its first word.
  // Measured 2026-08-28 on a real book: publishes #3 and #4 byte-identical
  // across one Confirm/Back round trip.
  //
  // Rects are REPLACED rather than kept: the text is what identifies the page,
  // while the geometry can legitimately move under it (a palette change
  // re-dithers the same layout). Speech and the highlight carry on untouched.
  if (!page.cleared && !page.utf8.empty() && page.utf8 == pageText_ &&
      (state_ == State::Speaking || state_ == State::Paused)) {
    rects_ = page.rects;
    return out;
  }

  if (state_ == State::Speaking || state_ == State::Paused)
    out.push_back({Action::StopUtterance});
  appendClear(out, highlightActive_);

  // "Nothing to read" and "the reader exited" are DIFFERENT, and collapsing
  // them is what stalled hands-free reading. A book opens on a cover wrapper
  // that captures no words, so with read-aloud on the first publish of every
  // book was empty -- and this returned no start and no turn, leaving speech
  // dead until a page was turned by hand. `cleared` means the reader left;
  // that alone ends speech.
  if (page.cleared) {
    rects_.clear();
    textBytes_ = 0;
    resumeOffset_ = 0;
    pageText_.clear();
    skippedTextless_ = 0;
    state_ = State::Off;
    return out;
  }

  // A textless page is WALKED PAST, silently (owner 2026-08-28: "skip it
  // silently"). The bound is what stops a run of full-page plates turning for
  // ever; end of book cannot loop here, because that screen publishes nothing
  // at all rather than publishing an empty page.
  if (page.utf8.empty()) {
    rects_.clear();
    textBytes_ = 0;
    resumeOffset_ = 0;
    pageText_.clear();
    if (skippedTextless_ < kMaxConsecutiveSkips) {
      skippedTextless_++;
      out.push_back({Action::TurnPageForward});
      state_ = State::AwaitingNextPage;
      return out;
    }
    // The bound LATCHES: it is cleared only when a page with words arrives,
    // never here. Resetting it at the limit made the counter oscillate --
    // twelve turns, one stop, twelve more -- which is the runaway it exists to
    // prevent, wearing a bound's clothes. Caught by the 40-blank-page test.
    state_ = State::Off;
    return out;
  }

  skippedTextless_ = 0;
  pageText_ = page.utf8;
  rects_ = page.rects;
  textBytes_ = static_cast<uint32_t>(page.utf8.size());
  scanCursor_ = 0;
  resumeOffset_ = 0;
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
  // Paused included: an interruption (a call, another app taking the session)
  // cancels a held utterance just as readily as a speaking one.
  if (state_ != State::Speaking && state_ != State::Paused)
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
  // Where a stop or a rate change would pick up again. Set BEFORE the dedupe
  // return so it is right even when the highlight has nothing to say.
  resumeOffset_ = r.byteOffset;
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

void ReadAloudCore::beginAt(uint32_t byteOffset, std::vector<Action> &out) {
  // A resume point can outlive the page it came from only if something has
  // gone wrong upstream, but the clamp is one compare and the alternative is
  // an utterance starting past the end of the string.
  if (byteOffset >= textBytes_)
    byteOffset = 0;
  Action start{Action::StartUtterance};
  start.utteranceByteOffset = byteOffset;
  out.push_back(start);
  resumeOffset_ = byteOffset;
  scanCursor_ = 0; // rectContaining resumes from here; the jump may be backwards
  const int i = rectContaining(byteOffset);
  if (i >= 0) {
    const ReadAloudWordRect &r = rects_[static_cast<size_t>(i)];
    highlightActive_ = true;
    highlightOffset_ = r.byteOffset;
    highlightLen_ = r.byteLen;
    Action hl{Action::SetHighlight};
    hl.highlightByteOffset = r.byteOffset;
    hl.highlightByteLen = r.byteLen;
    out.push_back(hl);
  }
  state_ = State::Speaking;
}

std::vector<ReadAloudCore::Action> ReadAloudCore::toggleSpeech() {
  std::vector<Action> out;
  if (!enabled_)
    return out;
  switch (state_) {
    case State::Speaking:
      out.push_back({Action::PauseUtterance});
      state_ = State::Paused;
      // The highlight STAYS. It is the answer to "where was I", which is the
      // one thing the owner wants while paused.
      break;
    case State::Paused:
      out.push_back({Action::ResumeUtterance});
      state_ = State::Speaking;
      break;
    case State::Off:
      // Nothing is held, so this is a start, not a resume — from the last word
      // speech was known to be on. Needs a page: with no text there is nothing
      // to say and the gesture is reported unhandled.
      if (textBytes_ > 0)
        beginAt(resumeOffset_, out);
      break;
    case State::AwaitingNextPage:
      // A page turn is in flight and the rects on hand belong to the page
      // already turned away from. Toggling into that is how you get speech
      // starting on a page that is no longer on screen.
      break;
  }
  return out;
}

std::vector<ReadAloudCore::Action> ReadAloudCore::restartAtCurrentWord() {
  std::vector<Action> out;
  if (!enabled_ || state_ != State::Speaking)
    return out;
  out.push_back({Action::StopUtterance});
  // Only clear when beginAt has no rect to light instead: the word does not
  // move, so a clear/set pair on the same range is a repaint for nothing.
  if (rectContaining(resumeOffset_) < 0)
    appendClear(out, highlightActive_);
  beginAt(resumeOffset_, out);
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
    const bool live = state_ == State::Speaking || state_ == State::Paused;
    // TAP-TO-STOP. Keyed on the highlighted BYTE RANGE, not the rect, so
    // either fragment of a line-wrapped word counts as "the word you are
    // hearing" — which is what a finger aiming at it means.
    if (live && highlightActive_ && highlightOffset_ == r.byteOffset &&
        highlightLen_ == r.byteLen) {
      out.push_back({Action::StopUtterance});
      appendClear(out, highlightActive_);
      resumeOffset_ = r.byteOffset; // magic tap carries on from here
      state_ = State::Off;
      return out;
    }
    if (live)
      out.push_back({Action::StopUtterance});
    beginAt(r.byteOffset, out);
    return out;
  }
  return out;
}
