// Unit tests for ReadAloudCore: the pure, clock-free state machine behind
// read-aloud TTS. The contracts under test, per .claude/PLAN-tts-read-aloud.md:
//
//   * finished turns the page; CANCELED NEVER DOES — that difference is the
//     whole reason didFinish and didCancel stay distinct in the adapter.
//   * highlight is keyed on the spoken word's BYTE RANGE and deduped, so a
//     line-wrapped word (several rects, one range) emits one action.
//   * taps start speech at a rect's byteOffset, are inflated for fat
//     fingers, and are ignored in AwaitingNextPage where rects are stale.
//   * byte offsets are UTF-8; the multibyte page below drifts if anyone
//     counts characters instead of bytes.
//
// Build + run (no framework, no SDL):
//   c++ -std=c++17 -Iios tests/read_aloud_core_test.cpp ios/ReadAloudCore.cpp -o /tmp/read_aloud_core_test && /tmp/read_aloud_core_test

#include "ReadAloudCore.h"

#include <cstdio>
#include <string>
#include <vector>

static int failures = 0;
#define CHECK(cond)                                                        \
  do {                                                                     \
    if (!(cond)) {                                                         \
      std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);          \
      failures++;                                                          \
    }                                                                      \
  } while (0)

using Action = ReadAloudCore::Action;
using State = ReadAloudCore::State;

static bool same(const std::vector<Action> &got,
                 const std::vector<Action> &want) {
  if (got.size() != want.size()) return false;
  for (size_t i = 0; i < got.size(); i++) {
    if (got[i].type != want[i].type) return false;
    if (got[i].utteranceByteOffset != want[i].utteranceByteOffset) return false;
    if (got[i].highlightByteOffset != want[i].highlightByteOffset) return false;
    if (got[i].highlightByteLen != want[i].highlightByteLen) return false;
  }
  return true;
}

static Action start(uint32_t off) {
  Action a{Action::StartUtterance};
  a.utteranceByteOffset = off;
  return a;
}
static Action stop() { return Action{Action::StopUtterance}; }
static Action turn() { return Action{Action::TurnPageForward}; }
static Action hl(uint32_t off, uint32_t len) {
  Action a{Action::SetHighlight};
  a.highlightByteOffset = off;
  a.highlightByteLen = len;
  return a;
}
static Action clearHl() { return Action{Action::ClearHighlight}; }

// A multibyte page: “Hello” café world
//   bytes 0-8   “Hello”   (curly quotes are 3 bytes each: 3+5+3 = 11... see below)
// Laid out explicitly so the offsets in this file are checked arithmetic, not
// guesses:
//   \xE2\x80\x9C H e l l o \xE2\x80\x9D   -> byteOffset 0, byteLen 11
//   (space, byte 11)
//   c a f \xC3\xA9                        -> byteOffset 12, byteLen 5
//   (space, byte 17)
//   w o r l d                             -> byteOffset 18, byteLen 5
static ReadAloudPage multibytePage() {
  ReadAloudPage p;
  p.utf8 = "\xE2\x80\x9CHello\xE2\x80\x9D caf\xC3\xA9 world";
  p.rects = {
      {10, 40, 60, 14, 0, 11},  // “Hello”
      {80, 40, 40, 14, 12, 5},  // café
      {10, 60, 44, 14, 18, 5},  // world (next line)
  };
  p.generation = 1;
  return p;
}

// A page whose middle word is line-wrapped: two rects, one byte range.
static ReadAloudPage wrappedPage() {
  ReadAloudPage p;
  p.utf8 = "a consideration b";
  p.rects = {
      {10, 40, 10, 14, 0, 1},    // a
      {30, 40, 60, 14, 2, 13},   // consid- (fragment 1)
      {10, 60, 70, 14, 2, 13},   // eration (fragment 2, same range)
      {90, 60, 10, 14, 16, 1},   // b
  };
  p.generation = 1;
  return p;
}

static ReadAloudPage clearedPage() {
  ReadAloudPage p;
  p.cleared = true;
  p.generation = 9;
  return p;
}

int main() {
  // --- disabled: pages are ignored entirely ---------------------------------
  {
    ReadAloudCore core;
    CHECK(core.pageArrived(multibytePage()).empty());
    CHECK(core.state() == State::Off);
    // ...and so are taps, even on a word.
    CHECK(core.tapAtLogical(15, 45).empty());
  }

  // --- enable then page: speak from the top ---------------------------------
  {
    ReadAloudCore core;
    CHECK(core.setEnabled(true).empty()); // enabling alone speaks nothing
    auto a = core.pageArrived(multibytePage());
    CHECK(same(a, {start(0)}));
    CHECK(core.state() == State::Speaking);
  }

  // --- highlight tracks words by byte range, deduped, gaps silent -----------
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(multibytePage());
    CHECK(same(core.willSpeakByte(0), {hl(0, 11)}));   // “Hello” begins
    CHECK(core.willSpeakByte(5).empty());              // still inside “Hello”
    CHECK(core.willSpeakByte(11).empty());             // inter-word space
    CHECK(same(core.willSpeakByte(12), {hl(12, 5)}));  // café — after multibyte
    CHECK(same(core.willSpeakByte(18), {hl(18, 5)}));  // world
  }

  // --- a wrapped word emits ONE highlight for both fragments ----------------
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(wrappedPage());
    CHECK(same(core.willSpeakByte(2), {hl(2, 13)}));
    // Bytes later in the word land in fragment territory; same range, silent.
    CHECK(core.willSpeakByte(9).empty());
    CHECK(same(core.willSpeakByte(16), {hl(16, 1)}));
  }

  // --- finished: clear highlight, turn the page, await ----------------------
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(multibytePage());
    core.willSpeakByte(0);
    auto a = core.utteranceFinished();
    CHECK(same(a, {clearHl(), turn()}));
    CHECK(core.state() == State::AwaitingNextPage);
    // The next page starts speech again: the hands-free loop.
    auto b = core.pageArrived(multibytePage());
    CHECK(same(b, {start(0)}));
    CHECK(core.state() == State::Speaking);
  }

  // --- CANCELED NEVER TURNS THE PAGE ----------------------------------------
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(multibytePage());
    core.willSpeakByte(0);
    auto a = core.utteranceCanceled();
    CHECK(same(a, {clearHl()}));
    CHECK(core.state() == State::Off);
    // And a second cancel (stale) does nothing.
    CHECK(core.utteranceCanceled().empty());
  }

  // --- manual page turn mid-speech: stop, then speak the new page -----------
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(multibytePage());
    core.willSpeakByte(0);
    auto a = core.pageArrived(wrappedPage());
    CHECK(same(a, {stop(), clearHl(), start(0)}));
    CHECK(core.state() == State::Speaking);
  }

  // --- cleared page (reader exited): stop, off ------------------------------
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(multibytePage());
    core.willSpeakByte(0);
    auto a = core.pageArrived(clearedPage());
    CHECK(same(a, {stop(), clearHl()}));
    CHECK(core.state() == State::Off);
    // Rects are gone with the page: a tap now does nothing.
    CHECK(core.tapAtLogical(15, 45).empty());
  }

  // --- timeout in AwaitingNextPage: off; a later page restarts --------------
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(multibytePage());
    core.utteranceFinished();
    auto a = core.pageTimeout();
    CHECK(a.empty()); // highlight already cleared by finished
    CHECK(core.state() == State::Off);
    // The owner turns the page by hand after the book ended: reads again.
    CHECK(same(core.pageArrived(multibytePage()), {start(0)}));
  }
  // ...and timeout in any other state is a stale no-op.
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(multibytePage());
    CHECK(core.pageTimeout().empty());
    CHECK(core.state() == State::Speaking);
  }

  // --- disable mid-speech: stop, clear, off ---------------------------------
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(multibytePage());
    core.willSpeakByte(0);
    auto a = core.setEnabled(false);
    CHECK(same(a, {stop(), clearHl()}));
    CHECK(core.state() == State::Off);
  }

  // --- tap while off (speech not started): start at the tapped word ---------
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(multibytePage());
    core.utteranceCanceled(); // owner stopped it; page + rects still held
    auto a = core.tapAtLogical(85, 45); // inside café's rect
    CHECK(same(a, {start(12), hl(12, 5)}));
    CHECK(core.state() == State::Speaking);
  }

  // --- tap while speaking: stop, jump, highlight ----------------------------
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(multibytePage());
    core.willSpeakByte(0);
    auto a = core.tapAtLogical(12, 65); // inside world's rect (next line)
    CHECK(same(a, {stop(), start(18), hl(18, 5)}));
    CHECK(core.state() == State::Speaking);
    // The jumped-to word is already highlighted: its own bytes are deduped.
    CHECK(core.willSpeakByte(18).empty());
    // ...and a backwards jump (tap on the FIRST word) resets the scan.
    auto b = core.tapAtLogical(15, 45);
    CHECK(same(b, {stop(), start(0), hl(0, 11)}));
    CHECK(same(core.willSpeakByte(12), {hl(12, 5)}));
  }

  // --- tap misses: gaps and margins do nothing ------------------------------
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(multibytePage());
    CHECK(core.tapAtLogical(75, 45).empty());  // between “Hello” and café
    CHECK(core.tapAtLogical(400, 700).empty()); // margin
    CHECK(core.state() == State::Speaking);     // untouched
  }

  // --- tap inflation: 1px outside a rect edge still hits --------------------
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(multibytePage());
    core.utteranceCanceled();
    // café's rect starts at x=80; x=79 is outside the rect, inside the +2px.
    auto a = core.tapAtLogical(79, 45);
    CHECK(same(a, {start(12), hl(12, 5)}));
  }

  // --- tap in AwaitingNextPage is ignored: those rects were turned away from -
  {
    ReadAloudCore core;
    core.setEnabled(true);
    core.pageArrived(multibytePage());
    auto fin = core.utteranceFinished();
    CHECK(same(fin, {turn()})); // no highlight was active
    CHECK(core.tapAtLogical(15, 45).empty());
    CHECK(core.state() == State::AwaitingNextPage);
  }

  // --- a page without rects speaks but cannot highlight or take taps --------
  {
    ReadAloudCore core;
    core.setEnabled(true);
    ReadAloudPage p;
    p.utf8 = "plain text, FW-A era";
    p.generation = 1;
    CHECK(same(core.pageArrived(p), {start(0)}));
    CHECK(core.willSpeakByte(0).empty());
    CHECK(core.tapAtLogical(15, 45).empty());
  }

  if (failures) {
    std::printf("%d failure(s)\n", failures);
    return 1;
  }
  std::printf("read_aloud_core_test: all passed\n");
  return 0;
}
