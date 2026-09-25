// SPEED READ (RSVP) -- the pure model (src/SpeedRead.h) and the read-aloud
// channel's FAN-OUT that feeds it (src/ReadAloudChannel.h peek()).
//
// Two silent failure modes this exists for: a peeker that DRAINS the channel
// steals pages from read-aloud (it would go quiet on every page speed read saw
// first), and a pivot/duration table that drifts from its cited source.
//
//   c++ -std=c++17 -Isrc tests/speed_read_test.cpp -o /tmp/sr && /tmp/sr

#include "SpeedRead.h"

#include <cstdio>
#include <string>
#include <vector>

#include "TestCheck.h"

static int &failures = testcheck::g_failures;

using speedread::Reader;
using speedread::Word;

static ReadAloudWordRect R(uint16_t x, uint16_t y, uint16_t w, uint32_t off,
                           uint16_t len, uint16_t h = 30) {
  return ReadAloudWordRect{x, y, w, h, off, len};
}

// Build a capture from words laid out left to right on lines.
struct Cap {
  std::string text;
  std::vector<ReadAloudWordRect> rects;
  void word(const std::string &w, uint16_t x, uint16_t y, uint16_t wpx) {
    if (!text.empty()) text.push_back(' ');
    rects.push_back(R(x, y, wpx, static_cast<uint32_t>(text.size()),
                      static_cast<uint16_t>(w.size())));
    text += w;
  }
};

int main() {
  // --- ORP table: OpenSpritz's bestLetter switch, zero-based --------------
  {
    const int want[] = {0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4};
    for (int len = 0; len <= 16; len++)
      CHECKM(speedread::orpIndex(len) == want[len], "orpIndex(%d)=%d want %d",
             len, speedread::orpIndex(len), want[len]);
    CHECK(speedread::orpGlyph("a") == 0);
    CHECK(speedread::orpGlyph("the") == 1);
    CHECK(speedread::orpGlyph("reading") == 2);
    // Leading punctuation shifts the pivot glyph; trailing does not count
    // toward the length.
    CHECK(speedread::orpGlyph("\"reading,\"") == 3);
    CHECK(speedread::orpGlyph("\xE2\x80\x9CHello") == 2); // "Hello, curly quote
    CHECK(speedread::orpGlyph("it.") == 1);
    CHECK(speedread::codepoints("caf\xC3\xA9") == 4);
    CHECK(speedread::orpGlyph("caf\xC3\xA9") == 1);
  }

  // --- punctuation classes ------------------------------------------------
  {
    CHECK(speedread::endsSentence("end."));
    CHECK(speedread::endsSentence("end?\""));
    CHECK(speedread::endsSentence("end!\xE2\x80\x9D"));
    CHECK(speedread::endsSentence("so\xE2\x80\xA6"));
    CHECK(!speedread::endsSentence("mid,"));
    CHECK(!speedread::endsSentence("word"));
    CHECK(speedread::endsClause("mid,"));
    CHECK(speedread::endsClause("list;"));
    CHECK(speedread::endsClause("thus\xE2\x80\x94"));
    CHECK(!speedread::endsClause("end."));
  }

  // --- durations ----------------------------------------------------------
  {
    auto d = [](const char *t, bool para = false, int wpm = 300) {
      Word w{t, {}, para};
      return speedread::durationMs(w, wpm);
    };
    CHECK(d("word") == 200.0);                 // 60000/300
    CHECK(d("word", false, 600) == 100.0);
    CHECK(d("mid,") == 300.0);                 // x1.5
    CHECK(d("end.") == 400.0);                 // x2
    CHECK(d("end.", true) == 700.0);           // x2 + 1.5
    CHECK(d("extraordinarily") > 200.0 * 1.6); // 15 letters: +0.7
    CHECK(d("extraordinarily") < 200.0 * 1.8);
    CHECK(d("antidisestablishmentarianism") == 200.0 * 1.8); // capped +0.8
    CHECK(d("word", false, 5) == 600.0);       // clamped to 100 wpm
  }

  // --- words from a capture -----------------------------------------------
  {
    Cap c;
    // line 1 (full), line 2 ends short (paragraph end), line 3 indented
    c.word("The", 20, 10, 40);
    c.word("quick,", 70, 10, 70);
    c.word("brown", 150, 10, 300); // reaches the right edge (450)
    c.word("fox.", 20, 40, 45);    // short line -> paragraph end
    c.word("Then", 50, 70, 50);    // indented start
    c.word("more", 110, 70, 340);
    std::vector<Word> ws = speedread::wordsFromPage(c.text, c.rects);
    CHECK(ws.size() == 6);
    CHECK(ws[1].text == "quick,");
    CHECK(!ws[0].paragraphEnd && !ws[1].paragraphEnd);
    CHECK(!ws[2].paragraphEnd); // full line, next line not indented
    CHECK(ws[3].paragraphEnd);
    CHECK(!ws[5].paragraphEnd); // last word on a full line
  }
  {
    // RAGGED RIGHT: a line that stops short only because the next word would
    // not fit is NOT a paragraph end (the first cut paused mid-sentence here).
    Cap c;
    c.word("aaa", 20, 10, 380);   // ends at 400, 50 short of 450
    c.word("bbbbbb", 20, 40, 100); // would need 400+7+100 > 450: forced
    c.word("cc", 130, 40, 320);    // this line reaches 450
    c.word("dd", 20, 70, 30);      // last word: 400 short of 450
    std::vector<Word> ws = speedread::wordsFromPage(c.text, c.rects);
    CHECK(ws.size() == 4 && !ws[0].paragraphEnd && !ws[2].paragraphEnd);
    CHECK(ws[3].paragraphEnd);
  }
  {
    // Indent alone marks the break (the line above is full).
    Cap c;
    c.word("aaa", 20, 10, 430);
    c.word("bbb", 60, 40, 100);
    std::vector<Word> ws = speedread::wordsFromPage(c.text, c.rects);
    CHECK(ws.size() == 2 && ws[0].paragraphEnd);
  }
  {
    // Hyphen-split fragments share a byteOffset -> one word, two frags;
    // blank and zero-size rects are dropped.
    const std::string t = "hello continue   x";
    std::vector<ReadAloudWordRect> r = {R(20, 10, 60, 0, 5),
                                        R(300, 10, 90, 6, 8),
                                        R(20, 40, 50, 6, 8),
                                        R(100, 40, 20, 14, 3), // "   "
                                        R(130, 40, 0, 17, 1)}; // zero width
    std::vector<Word> ws = speedread::wordsFromPage(t, r);
    CHECK(ws.size() == 2);
    CHECK(ws[1].text == "continue" && ws[1].frags.size() == 2);
  }

  // --- pivot from column ink ---------------------------------------------
  {
    // three separate glyph runs: [2..5] [8..11] [14..17]
    std::vector<float> ink(20, 0.0f);
    for (int x : {2, 3, 4, 5, 8, 9, 10, 11, 14, 15, 16, 17}) ink[x] = 5.0f;
    const std::vector<float> three = {500, 500, 500};
    CHECK(speedread::pivotX(ink, three, 1, 0.5f) == 10.0f); // run centre
    // touching letters: 2 runs for 3 glyphs -> shared by width over [2, 18)
    ink[6] = ink[7] = 5.0f;
    float p = speedread::pivotX(ink, three, 1, 0.5f);
    CHECK(p > 9.9f && p < 10.1f);
    // unequal widths move it: "mil" = 778, 278, 278 -> centre of the i
    p = speedread::pivotX(ink, speedread::glyphWidths("mil"), 1, 0.5f);
    const float want = 2 + (778 + 139) / 1334.0f * 16;
    CHECKM(p > want - 0.01f && p < want + 0.01f, "mil pivot %f want %f", p, want);
    CHECK(speedread::pivotX({}, three, 1, 0.5f) == 0.0f);
    CHECK(speedread::glyphWidths("caf\xC3\xA9").size() == 4);
    CHECK(speedread::glyphWidths("\xE2\x80\x94").size() == 1 &&
          speedread::glyphWidths("\xE2\x80\x94")[0] == 1000);
    // a split word: "continue" split "con-" / "tinue" -> hyphen after "n"
    std::vector<float> w = speedread::glyphWidths("continue");
    int piv = speedread::orpGlyph("continue"); // 2, the 'n'
    speedread::addSplitHyphen(w, piv, 0.40f);
    CHECK(w.size() == 9 && w[3] == 333 && piv == 2);
    std::vector<float> w2 = speedread::glyphWidths("continue");
    int piv2 = 2;
    speedread::addSplitHyphen(w2, piv2, 0.15f); // "c-" / "ontinue"
    CHECK(w2[1] == 333 && piv2 == 3);
  }

  // --- the reader: advance, page turn, pause, back ------------------------
  {
    Cap c;
    c.word("One", 20, 10, 40);
    c.word("two.", 70, 10, 50);
    c.word("Three", 130, 10, 60);
    c.word("four", 200, 10, 250);
    Reader rd;
    rd.setWpm(600); // 100 ms base
    rd.pageArrived(speedread::wordsFromPage(c.text, c.rects), 1000, false);
    CHECK(rd.index() == 0 && rd.count() == 4);
    CHECK(!rd.step(1099).changed);
    CHECK(rd.step(1100).changed && rd.index() == 1);
    // "two." is a sentence end: 200 ms
    CHECK(!rd.step(1299).changed);
    CHECK(rd.step(1300).changed && rd.index() == 2);
    // a stall does not skip words: one per step
    CHECK(rd.step(5000).changed && rd.index() == 3);
    // end of page: ask for the turn exactly once
    Reader::Event e = rd.step(5100);
    CHECK(e.requestTurn && !e.changed && rd.awaitingTurn());
    CHECK(!rd.step(5200).requestTurn);
    // a re-render of the same page does not move the position, and does not
    // answer the pending turn: no second turn may be asked for
    rd.pageArrived(speedread::wordsFromPage(c.text, c.rects), 5300, true);
    CHECK(rd.index() == 3);
    CHECK(rd.awaitingTurn() && !rd.step(5350).requestTurn);
    // the new page restarts at its first word
    rd.pageArrived(speedread::wordsFromPage(c.text, c.rects), 5400, false);
    CHECK(rd.index() == 0 && !rd.awaitingTurn());
    // pause holds the word however long
    rd.togglePause(5400);
    CHECK(rd.paused() && !rd.step(99999).changed && rd.index() == 0);
    rd.togglePause(100000); // resume: the word gets its full time again
    CHECK(!rd.step(100099).changed);
    CHECK(rd.step(100100).changed && rd.index() == 1);
    // back a sentence: from "Three" to "Three" is a start -> previous sentence
    rd.step(100300);
    CHECK(rd.index() == 2);
    rd.backSentence(100300);
    CHECK(rd.index() == 0);
    rd.step(100400);
    rd.step(100600);
    rd.step(100700); // at "four"
    CHECK(rd.index() == 3);
    rd.backSentence(100700); // to the start of its sentence, "Three"
    CHECK(rd.index() == 2);
    rd.backWord(100700);
    CHECK(rd.index() == 1);
    rd.backWord(100700);
    rd.backWord(100700);
    CHECK(rd.index() == 0);
  }
  {
    // A loop that notices late keeps the schedule: the next word is timed
    // from when this one was DUE, so a 30 ms-late step does not slow the page.
    Cap c;
    c.word("aa", 20, 10, 40);
    c.word("bb", 70, 10, 40);
    c.word("cc", 120, 10, 40);
    Reader rd;
    rd.setWpm(600);
    rd.pageArrived(speedread::wordsFromPage(c.text, c.rects), 0, false);
    CHECK(rd.step(130).changed && rd.index() == 1); // due at 100
    CHECK(!rd.step(199).changed);
    CHECK(rd.step(200).changed && rd.index() == 2); // due at 200, not 230
  }
  {
    // An empty page dwells, then turns; an unanswered turn is the end.
    Reader rd;
    rd.pageArrived({}, 0, false);
    CHECK(!rd.step(speedread::kEmptyPageDwellMs - 1).requestTurn);
    CHECK(rd.step(speedread::kEmptyPageDwellMs).requestTurn);
    CHECK(!rd.finished());
    CHECK(rd.step(speedread::kEmptyPageDwellMs + speedread::kTurnTimeoutMs)
              .changed);
    CHECK(rd.finished());
    // cleared: nothing up, nothing happens
    rd.clear();
    CHECK(!rd.hasPage() && rd.current() == nullptr && !rd.step(1u << 30).changed);
  }

  // --- the channel fan-out: a peeker never steals from the consumer --------
  {
    ReadAloudChannel ch;
    uint32_t seen = 0;
    ReadAloudPage p;
    CHECK(!ch.peek(seen, p)); // nothing published yet
    ch.publish("a b", 3, nullptr, 0, 1234);
    CHECK(ch.peek(seen, p) && p.utf8 == "a b" && p.publishedAtMs == 1234);
    CHECK(!ch.peek(seen, p));           // once per generation
    CHECK(ch.consume(p) && p.utf8 == "a b"); // consumer still gets it
    CHECK(!ch.consume(p));
    ch.publish("c", 1, nullptr, 0);
    CHECK(ch.consume(p) && p.utf8 == "c"); // consumer first this time...
    CHECK(ch.peek(seen, p) && p.utf8 == "c"); // ...peeker still sees it
    // two peekers keep independent cursors
    uint32_t other = 0;
    CHECK(ch.peek(other, p) && p.utf8 == "c");
    // wanted: the peeker's flag is OR'd, never written over the consumer's
    CHECK(!ch.wanted());
    ch.setPeekerWanted(true);
    CHECK(ch.wanted() && !ch.drainerWanted());
    ch.setWanted(false); // the consumer turning itself off...
    CHECK(ch.wanted());  // ...does not switch the peeker's capture off
    ch.setPeekerWanted(false);
    ch.setWanted(true);
    CHECK(ch.wanted());
    // a clear reaches the peeker too
    ch.publish(nullptr, 0, nullptr, 0);
    CHECK(ch.peek(seen, p) && p.cleared);
    // reboot drops the page; a peeker sees nothing stale
    ch.publish("stale", 5, nullptr, 0);
    ch.resetForReboot();
    uint32_t fresh = 0;
    CHECK(!ch.peek(fresh, p));
  }

  if (failures) {
    std::printf("%d failure(s)\n", failures);
    return 1;
  }
  std::printf("speed_read_test: all passed\n");
  return 0;
}
