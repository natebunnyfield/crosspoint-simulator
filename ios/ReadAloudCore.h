#pragma once

#include <cstdint>
#include <string>
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
      PauseUtterance,  // hold the current utterance where it is
      ResumeUtterance, // continue the held utterance
      TurnPageForward, // schedule a page-forward button tap
      SetHighlight,    // highlight every rect carrying [offset, offset+len)
      ClearHighlight,
    };
    Type type;
    uint32_t utteranceByteOffset = 0; // StartUtterance
    uint32_t highlightByteOffset = 0; // SetHighlight
    uint32_t highlightByteLen = 0;    // SetHighlight
  };

  // Paused is NOT Off: the utterance still exists inside the speech engine and
  // resuming continues it mid-word, so no byte offset is involved. Off means
  // there is no utterance and starting again means starting a new one.
  enum class State { Off, Speaking, Paused, AwaitingNextPage };

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
  // tapped word — EXCEPT on the word being spoken right now, which STOPS.
  // That asymmetry is the whole point: without it there is no way to shut the
  // reader up with a finger, and re-tapping the word you are hearing is what
  // a reader reaches for first. Ignored while disabled, while no page with
  // rects is held, and in AwaitingNextPage — the held rects belong to the
  // page that was just turned away from.
  std::vector<Action> tapAtLogical(int x, int y);

  // The system play/pause gesture (VoiceOver's two-finger double tap, routed
  // here by accessibilityPerformMagicTap). Speaking -> paused, paused ->
  // speaking, and from a full stop it starts again AT THE WORD IT STOPPED ON,
  // which is what makes tap-to-stop and this pair up into a usable control.
  // Returns no actions when there is nothing to toggle, so the adapter can
  // report the gesture unhandled and let the system look elsewhere.
  std::vector<Action> toggleSpeech();

  // Re-speak from the current word. The one thing an utterance cannot change
  // once it is speaking is its RATE, so a speaking-rate change has to be
  // applied by starting a new utterance; doing it from the current word is
  // what keeps that from sounding like a page reset. No-op unless speaking:
  // paused and stopped speech pick the new rate up on their next utterance
  // anyway, and neither should start talking because a slider moved.
  std::vector<Action> restartAtCurrentWord();

  State state() const { return state_; }

private:
  int rectContaining(uint32_t byteOffset);
  // Emit StartUtterance at `byteOffset` (plus its SetHighlight when a rect
  // owns that byte) and enter Speaking. Shared by tap, magic tap and restart;
  // pageArrived deliberately does NOT use it — a fresh page starts at byte 0
  // with no highlight until the engine reports the first word.
  void beginAt(uint32_t byteOffset, std::vector<Action> &out);

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
  // Where speech would pick up again: the last word it was known to be on.
  // Tracked SEPARATELY from the highlight because stopping clears the
  // highlight and the resume point has to outlive it — that is what lets a
  // magic tap after a tap-to-stop carry on from the same word.
  uint32_t resumeOffset_ = 0;
  // The page currently held, kept so an IDENTICAL republish can be recognised
  // and ignored. The reader re-renders on things that do not move the
  // position -- ActivityManager requests an update on every subactivity pop,
  // and an appearance change forces one too -- and without this the same page
  // arrived twice and speech restarted from its first word.
  std::string pageText_;
  // Consecutive textless pages skipped. A page with no words is walked past
  // rather than spoken (owner 2026-08-28), and a run of plates would
  // otherwise turn forever; this bounds it.
  int skippedTextless_ = 0;
  static constexpr int kMaxConsecutiveSkips = 12;
};
