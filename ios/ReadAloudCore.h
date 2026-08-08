#pragma once

#include <cstdint>
#include <vector>

#include "../src/ReadAloudChannel.h"

// The pure decision logic behind read-aloud: channel pages, speech-engine
// events, and taps in; utterance/highlight/page-turn actions out.
// Deliberately AVSpeech-free, SDL-free and CLOCK-FREE, PadCore's discipline:
// time enters only as explicit inputs (pageTimeout, counted by the adapter),
// geometry only as logical panel coordinates the adapter already converted.
// Tested by tests/read_aloud_core_test.cpp; the AVSpeech adapter in
// CrossPointReadAloud.mm translates between this and the platform and holds
// no decision state of its own.
//
// Byte offsets are always offsets into the current page's UTF-8 text, the
// same space the channel's rects use. SetHighlight carries the spoken WORD'S
// RANGE, not a rect index: a line-wrapped word owns several rects sharing
// one range, and a painter keyed on the range lights every fragment with no
// special cases.
class ReadAloudCore {
public:
  struct Action {
    enum Type {
      StartUtterance,  // speak the page's text from utteranceByteOffset
      StopUtterance,   // stop current speech immediately
      TurnPageForward, // schedule a page-forward button tap
      SetHighlight,    // highlight every rect carrying [offset, offset+len)
      ClearHighlight,
    };
    Type type;
    uint32_t utteranceByteOffset = 0; // StartUtterance
    uint32_t highlightByteOffset = 0; // SetHighlight
    uint32_t highlightByteLen = 0;    // SetHighlight
  };

  enum class State { Off, Speaking, AwaitingNextPage };

  // The owner's toggle. Disabling stops speech; enabling waits for a page
  // (capture publishes at the next page render — see the plan's non-goals).
  std::vector<Action> setEnabled(bool enabled);

  // A channel page. cleared == true means the reader exited: stop.
  // While disabled, pages are ignored entirely.
  std::vector<Action> pageArrived(const ReadAloudPage &page);

  // Natural end of the utterance (didFinish). Turns the page.
  std::vector<Action> utteranceFinished();

  // The utterance was stopped (didCancel: our own stop, or the OS). Never
  // turns the page — that is the whole reason finish and cancel stay
  // distinct all the way down.
  std::vector<Action> utteranceCanceled();

  // The adapter waited too long in AwaitingNextPage (end of book).
  std::vector<Action> pageTimeout();

  // The speech engine is about to speak the word at this ABSOLUTE byte
  // offset (adapter has already rebased by the utterance's start).
  std::vector<Action> willSpeakByte(uint32_t absoluteByteOffset);

  // A tap at logical panel coordinates. Starts (or jumps) speech at the
  // tapped word. Ignored while disabled, while no page with rects is held,
  // and in AwaitingNextPage — the held rects belong to the page that was
  // just turned away from.
  std::vector<Action> tapAtLogical(int x, int y);

  State state() const { return state_; }

private:
  int rectContaining(uint32_t byteOffset);

  State state_ = State::Off;
  bool enabled_ = false;
  std::vector<ReadAloudWordRect> rects_;
  uint32_t textBytes_ = 0;
  // Resumable scan cursor for willSpeakByte: speech only moves forward
  // within an utterance, so the search resumes where the last word was
  // found; a backwards jump (tap on an earlier word) resets it.
  int scanCursor_ = 0;
  bool highlightActive_ = false;
  uint32_t highlightOffset_ = 0;
  uint32_t highlightLen_ = 0;
};
