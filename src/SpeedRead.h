#pragma once

// SPEED READ -- RSVP (rapid serial visual presentation), a spike. Owner
// 2026-09-25: "speedrun was supposed to be that one word speed read". The
// book's words shown ONE AT A TIME in one fixed spot, at a set words-per-
// minute, each placed so its optimal recognition point (ORP) sits on a fixed
// focal mark and the eye never moves -- the Spritz arrangement.
//
// Everything that decides WHICH word, FOR HOW LONG and WHERE ITS PIVOT IS lives
// here, pure, so tests/speed_read_test.cpp can drive it. The words come from
// the read-aloud page channel (src/ReadAloudChannel.h: the page text plus one
// rect per word, in logical portrait panel pixels); the pixels each word is
// drawn with are cut from the rendered page by src/HalDisplay.cpp, which is the
// only part of this that touches SDL. docs/speed-read-rsvp-2026-09-25.md.

#include <algorithm>
#include <cstdint>
#include <string>
#include <vector>

#include "ReadAloudChannel.h"

namespace speedread {

inline constexpr int kDefaultWpm = 300;
inline constexpr int kMinWpm = 100;
inline constexpr int kMaxWpm = 1000;
// A page with no words on it (a cover, an image) is dwelt on this long before
// the next page is asked for.
inline constexpr uint64_t kEmptyPageDwellMs = 1500;
// A page turn asked for and never answered this long is the end of the book.
inline constexpr uint64_t kTurnTimeoutMs = 4000;

// One word as displayed: its text and every rect it was laid out in (a word
// the layout hyphen-split across lines publishes one rect per fragment, all
// sharing its byte range -- see ReadAloudWordRect).
struct Word {
  std::string text;
  std::vector<ReadAloudWordRect> frags;
  bool paragraphEnd = false;
};

// UTF-8 code points in s (continuation bytes 10xxxxxx are not counted).
inline int codepoints(const std::string &s) {
  int n = 0;
  for (unsigned char c : s)
    if ((c & 0xC0) != 0x80) n++;
  return n;
}

inline bool isAsciiPunct(unsigned char c) {
  return c < 0x80 && !((c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') ||
                       (c >= 'a' && c <= 'z'));
}

// Leading and trailing punctuation, in code points. Only ASCII punctuation and
// the typographic quotes/dashes a book actually carries are stripped; any
// other non-ASCII code point counts as a letter (accented Latin, etc.).
inline bool isPunctCp(const std::string &s, size_t at, size_t &len) {
  const unsigned char c = static_cast<unsigned char>(s[at]);
  if (c < 0x80) {
    len = 1;
    return isAsciiPunct(c);
  }
  // U+2018/2019/201C/201D quotes, U+2013/2014 dashes, U+2026 ellipsis:
  // E2 80 {98,99,9C,9D,93,94,A6}. U+00AB/00BB guillemets: C2 {AB,BB}.
  if (c == 0xE2 && at + 2 < s.size() &&
      static_cast<unsigned char>(s[at + 1]) == 0x80) {
    const unsigned char d = static_cast<unsigned char>(s[at + 2]);
    len = 3;
    return d == 0x98 || d == 0x99 || d == 0x9C || d == 0x9D || d == 0x93 ||
           d == 0x94 || d == 0xA6;
  }
  if (c == 0xC2 && at + 1 < s.size()) {
    const unsigned char d = static_cast<unsigned char>(s[at + 1]);
    len = 2;
    return d == 0xAB || d == 0xBB;
  }
  len = (c >= 0xF0) ? 4 : (c >= 0xE0) ? 3 : 2;
  return false;
}

// Code points of leading punctuation, letters (the core), trailing punctuation.
struct Anatomy {
  int lead = 0, core = 0, trail = 0;
};
inline Anatomy anatomy(const std::string &w) {
  std::vector<bool> punct;
  for (size_t i = 0; i < w.size();) {
    size_t len = 1;
    punct.push_back(isPunctCp(w, i, len));
    i += std::max<size_t>(len, 1);
  }
  Anatomy a;
  const int n = static_cast<int>(punct.size());
  while (a.lead < n && punct[a.lead]) a.lead++;
  while (a.trail < n - a.lead && punct[n - 1 - a.trail]) a.trail++;
  a.core = n - a.lead - a.trail;
  return a;
}

// THE ORP, as an index into the word's letters. OpenSpritz's table
// (github.com/Miserlou/OpenSpritz, spritz.js, the `bestLetter` switch, fetched
// 2026-09-25): length 1 -> 1st letter, 2-5 -> 2nd, 6-9 -> 3rd, 10-13 -> 4th,
// longer -> 5th. Zero-based here. It encodes the optimal viewing position
// (O'Regan 1981; Brysbaert & Nazir 2005): slightly left of a word's centre.
inline int orpIndex(int letters) {
  if (letters <= 1) return 0;
  if (letters <= 5) return 1;
  if (letters <= 9) return 2;
  if (letters <= 13) return 3;
  return 4;
}

// The ORP as a GLYPH index into the whole word, punctuation included -- what
// the pixel crop is segmented by. Leading punctuation shifts it right; a word
// that is all punctuation pivots on its middle.
inline int orpGlyph(const std::string &w) {
  const Anatomy a = anatomy(w);
  if (a.core == 0) return (a.lead + a.trail) / 2;
  return a.lead + orpIndex(a.core);
}

inline bool endsSentence(const std::string &w) {
  // Look past closing quotes/brackets: `end."` and `end.)` both end one.
  for (size_t i = w.size(); i-- > 0;) {
    const unsigned char c = static_cast<unsigned char>(w[i]);
    if (c == '.' || c == '!' || c == '?') return true;
    if (c == '"' || c == '\'' || c == ')' || c == ']') continue;
    // U+201D / U+2019 closing quotes end in 0x9D / 0x99 after E2 80.
    if ((c == 0x9D || c == 0x99) && i >= 2 &&
        static_cast<unsigned char>(w[i - 1]) == 0x80 &&
        static_cast<unsigned char>(w[i - 2]) == 0xE2) {
      i -= 2;
      continue;
    }
    // U+2026 ellipsis
    if (c == 0xA6 && i >= 2 && static_cast<unsigned char>(w[i - 1]) == 0x80 &&
        static_cast<unsigned char>(w[i - 2]) == 0xE2)
      return true;
    return false;
  }
  return false;
}

inline bool endsClause(const std::string &w) {
  if (w.empty()) return false;
  const unsigned char c = static_cast<unsigned char>(w.back());
  if (c == ',' || c == ';' || c == ':') return true;
  // em/en dash at the end: E2 80 94 / 93
  return w.size() >= 3 && static_cast<unsigned char>(w[w.size() - 3]) == 0xE2 &&
         static_cast<unsigned char>(w[w.size() - 2]) == 0x80 &&
         (c == 0x94 || c == 0x93);
}

// HOW LONG A WORD STAYS UP, in ms. The base interval is 60000 / wpm; the
// multipliers are the standard RSVP ones (OpenSpritz splices a word with , : -
// ( or over 8 characters -- punctuation counted -- and no '.' in TWICE more, so
// it is up three times as long: re-fetched 2026-09-25; Spritz's own pauses are
// unpublished), made
// gentler for clauses and length and stronger at a sentence's end, with an
// extra beat at a paragraph break:
//   sentence end . ! ? ...   x2.0
//   clause , ; : dash        x1.5
//   letters over 8           +0.1 per letter, at most +0.8
//   paragraph end            +1.5
inline double durationMs(const Word &w, int wpm) {
  wpm = std::clamp(wpm, kMinWpm, kMaxWpm);
  const double base = 60000.0 / wpm;
  double mult = 1.0;
  if (endsSentence(w.text))
    mult = 2.0;
  else if (endsClause(w.text))
    mult = 1.5;
  const int letters = anatomy(w.text).core;
  if (letters > 8) mult += std::min(0.8, 0.1 * (letters - 8));
  if (w.paragraphEnd) mult += 1.5;
  return base * mult;
}

// THE PAGE'S WORDS from its capture. Rects sharing a byteOffset are one word
// (hyphen-split fragments); a word whose text is empty or whitespace is
// dropped; punctuation stays attached because the capture already glued it.
//
// A PARAGRAPH END is inferred from the layout, since the capture carries no
// paragraph markers: the word is the last on its line and either the line
// was NOT FORCED -- the next word would have fitted after it -- or the next
// line starts indented past the page's left edge, or the next line sits more
// than 1.4 line heights below this one. "Stops short of the right edge" is not
// the test: on a ragged-right page most lines stop short, and the first cut
// of this (measured 2026-09-25 on the owner's own book) paused on "pricing"
// and "your" mid-sentence for a paragraph's beat.
inline std::vector<Word> wordsFromPage(const std::string &utf8,
                                       const std::vector<ReadAloudWordRect> &rects) {
  std::vector<Word> words;
  for (const ReadAloudWordRect &r : rects) {
    if (!words.empty() && !words.back().frags.empty() &&
        words.back().frags.front().byteOffset == r.byteOffset) {
      words.back().frags.push_back(r);
      continue;
    }
    if (r.byteOffset >= utf8.size()) continue;
    const size_t len = std::min<size_t>(r.byteLen, utf8.size() - r.byteOffset);
    std::string t = utf8.substr(r.byteOffset, len);
    const bool blank = std::all_of(t.begin(), t.end(), [](unsigned char c) {
      return c == ' ' || c == '\t' || c == '\n' || c == '\r';
    });
    if (t.empty() || blank || r.w == 0 || r.h == 0) continue;
    words.push_back(Word{std::move(t), {r}, false});
  }
  if (words.empty()) return words;
  int minX = 1 << 30, maxRight = 0;
  for (const Word &w : words)
    for (const auto &f : w.frags) {
      minX = std::min<int>(minX, f.x);
      maxRight = std::max<int>(maxRight, f.x + f.w);
    }
  for (size_t i = 0; i + 1 < words.size(); i++) {
    const ReadAloudWordRect &a = words[i].frags.back();
    const ReadAloudWordRect &b = words[i + 1].frags.front();
    if (b.y == a.y) continue; // same line: not a line end
    const int h = std::max<int>(1, a.h);
    // Unforced break: this line had room for the next word (and a space of a
    // quarter line height). A next word the layout hyphen-split was placed
    // across the break, so that break was forced.
    const bool shortLine = words[i + 1].frags.size() == 1 &&
                           a.x + a.w + h / 4 + b.w <= maxRight;
    const bool indented = b.x > minX + h / 3;                // first-line indent
    const bool gap = (b.y - a.y) * 10 > h * 14;              // paragraph space
    words[i].paragraphEnd = shortLine || indented || gap;
  }
  // The page's last word: no next word to test against, so a paragraph end
  // only if its line stops more than a quarter of the measure short.
  const ReadAloudWordRect &z = words.back().frags.back();
  words.back().paragraphEnd = (maxRight - (z.x + z.w)) * 4 > (maxRight - minX);
  return words;
}

// RELATIVE GLYPH WIDTHS, for placing the pivot when letters touch. Adobe's
// Times-Roman AFM advance widths (units per 1000) -- a serif book face's
// proportions, which is what a reading font is; the crop's own inked extent
// supplies the scale, so only the RATIOS matter. Anything not listed (accented
// letters, other scripts) is 500.
inline float glyphWidth(uint32_t cp) {
  static const short lower[26] = {444, 500, 444, 500, 444, 333, 500, 500, 278,
                                  278, 500, 278, 778, 500, 500, 500, 500, 333,
                                  389, 278, 500, 500, 722, 500, 500, 444};
  static const short upper[26] = {722, 667, 667, 722, 611, 556, 722, 722, 333,
                                  389, 722, 611, 889, 722, 722, 556, 722, 667,
                                  556, 611, 722, 722, 944, 722, 722, 611};
  if (cp >= 'a' && cp <= 'z') return lower[cp - 'a'];
  if (cp >= 'A' && cp <= 'Z') return upper[cp - 'A'];
  if (cp >= '0' && cp <= '9') return 500;
  switch (cp) {
  case '.': case ',': case ':': case ';': return 250;
  case '\'': case 0x2018: case 0x2019: return 333;
  case '"': return 408;
  case 0x201C: case 0x201D: return 444;
  case '-': return 333;
  case 0x2013: return 500;
  case 0x2014: return 1000;
  case '!': case '?': case '(': case ')': return 333;
  default: return 500;
  }
}

// The word's glyphs' relative widths, one per code point.
inline std::vector<float> glyphWidths(const std::string &w) {
  std::vector<float> out;
  for (size_t i = 0; i < w.size();) {
    const unsigned char c = static_cast<unsigned char>(w[i]);
    uint32_t cp = c;
    size_t len = 1;
    auto cont = [&](size_t k) { return static_cast<uint32_t>(w[i + k]) & 0x3Fu; };
    if (c >= 0xF0 && i + 3 < w.size()) {
      len = 4;
      cp = ((c & 0x07u) << 18) | (cont(1) << 12) | (cont(2) << 6) | cont(3);
    } else if (c >= 0xE0 && i + 2 < w.size()) {
      len = 3;
      cp = ((c & 0x0Fu) << 12) | (cont(1) << 6) | cont(2);
    } else if (c >= 0xC0 && i + 1 < w.size()) {
      len = 2;
      cp = ((c & 0x1Fu) << 6) | cont(1);
    }
    out.push_back(glyphWidth(cp));
    i += len;
  }
  return out;
}

// WHERE THE PIVOT LETTER SITS in a word's crop, in crop columns, from the
// crop's own ink. `ink` is per-column ink (any non-negative measure); columns
// above `threshold` are ink. When the ink falls into exactly as many separate
// runs as the word has glyphs, the pivot glyph's run centre is exact. Letters
// that touch (serifs, kerning, ligatures) merge runs; then the inked extent is
// shared out by the glyphs' relative widths (glyphWidths above) and the pivot
// is the centre of its share -- wrong only by how far the book's face departs
// from Times' proportions.
inline float pivotX(const std::vector<float> &ink,
                    const std::vector<float> &widths, int pivot,
                    float threshold) {
  const int n = static_cast<int>(ink.size());
  const int glyphs = static_cast<int>(widths.size());
  if (n == 0) return 0.0f;
  if (glyphs == 0) return n / 2.0f;
  pivot = std::clamp(pivot, 0, glyphs - 1);
  std::vector<std::pair<int, int>> runs;
  for (int x = 0; x < n;) {
    if (ink[x] <= threshold) { x++; continue; }
    const int s = x;
    while (x < n && ink[x] > threshold) x++;
    runs.push_back({s, x - 1});
  }
  float a = 0.0f, b = static_cast<float>(n);
  if (!runs.empty()) {
    if (static_cast<int>(runs.size()) == glyphs)
      return 0.5f * (runs[pivot].first + runs[pivot].second + 1);
    a = static_cast<float>(runs.front().first);
    b = static_cast<float>(runs.back().second + 1);
  }
  float total = 0.0f, before = 0.0f;
  for (int i = 0; i < glyphs; i++) {
    if (i < pivot) before += widths[i];
    total += widths[i];
  }
  if (total <= 0.0f) return a + (pivot + 0.5f) / glyphs * (b - a);
  return a + (before + 0.5f * widths[pivot]) / total * (b - a);
}

// A hyphen-split word's crop is its fragments side by side, and the first one
// ends in a hyphen the rejoined text does not carry. The split point is not
// published, so it is estimated from the fragments' widths; the hyphen is
// inserted there and the pivot index moved past it when it falls after.
inline void addSplitHyphen(std::vector<float> &widths, int &pivot,
                           float firstFragShare) {
  float total = 0.0f;
  for (float w : widths) total += w;
  float acc = 0.0f;
  size_t at = widths.size();
  for (size_t i = 0; i < widths.size(); i++) {
    if (acc + widths[i] / 2 > firstFragShare * total) { at = i; break; }
    acc += widths[i];
  }
  widths.insert(widths.begin() + static_cast<long>(at), glyphWidth('-'));
  if (static_cast<size_t>(pivot) >= at) pivot++;
}

// THE READER: which word is up, when it changes, and when to ask for the next
// page. Driven by a millisecond clock (SDL_GetTicks on the host). step()
// reports what changed; the host presents on `changed` and presses page-
// forward on `requestTurn`.
class Reader {
public:
  struct Event {
    bool changed = false;     // the displayed word (or pause state) moved
    bool requestTurn = false; // press page-forward, once
  };

  void setWpm(int wpm) { wpm_ = std::clamp(wpm, kMinWpm, kMaxWpm); }
  int wpm() const { return wpm_; }

  // A new page's words. `samePage` is a re-render of the page already up (the
  // firmware re-publishes on every render, not only on a page turn): the
  // position is kept, only the geometry is refreshed.
  void pageArrived(std::vector<Word> words, uint64_t now, bool samePage) {
    if (samePage && words.size() == words_.size()) {
      words_ = std::move(words);
      // awaitingTurn_ is KEPT: a re-render of the same page is not the turn
      // arriving, and clearing it here made the next step ask for a second
      // turn at once -- two pages at a time on a USB-edge or appearance
      // repaint (adversarial review, build 213).
      return;
    }
    words_ = std::move(words);
    index_ = 0;
    shownAt_ = now;
    arrivedAt_ = now;
    awaitingTurn_ = false;
    finished_ = false;
    hasPage_ = true;
  }
  // The reader left the book.
  void clear() {
    words_.clear();
    hasPage_ = false;
    awaitingTurn_ = false;
    finished_ = false;
    index_ = 0;
  }

  Event step(uint64_t now) {
    Event e;
    if (!hasPage_ || paused_ || finished_) return e;
    if (awaitingTurn_) {
      if (now - turnAskedAt_ >= kTurnTimeoutMs) {
        finished_ = true; // no page came: the end of the book
        e.changed = true;
      }
      return e;
    }
    if (words_.empty()) {
      if (now - arrivedAt_ >= kEmptyPageDwellMs) askTurn(now, e);
      return e;
    }
    // One word per step at most: a stalled main loop resumes where it was
    // rather than flashing through the words it missed. The next word's clock
    // starts when this one was DUE, not when the loop noticed, so a loop that
    // runs late by a frame (a present on the desktop's software renderer costs
    // ~100 ms) does not slow the whole page down; a stall longer than a word
    // restarts the schedule from now instead of racing to catch up.
    const double due = durationMs(words_[index_], wpm_);
    if (static_cast<double>(now - shownAt_) >= due) {
      if (index_ + 1 < words_.size()) {
        index_++;
        const uint64_t dueAt = shownAt_ + static_cast<uint64_t>(due);
        shownAt_ = (now - dueAt) < static_cast<uint64_t>(due) ? dueAt : now;
        e.changed = true;
      } else {
        askTurn(now, e);
      }
    }
    return e;
  }

  void togglePause(uint64_t now) {
    paused_ = !paused_;
    if (!paused_) {
      shownAt_ = now; // the current word gets its full time again
      // ...and so do the two other clocks a pause stopped. Without these a
      // pause taken while a turn was pending (or on an empty page) came back
      // to a timeout that had run on through the pause: resume after 4 s on a
      // pending turn read as the end of the book (2026-09-25, found writing
      // the pause test).
      arrivedAt_ = now;
      turnAskedAt_ = now;
      if (finished_) finished_ = false, awaitingTurn_ = false;
    }
  }
  bool paused() const { return paused_; }
  void setPaused(bool p, uint64_t now) {
    if (p != paused_) togglePause(now);
  }

  void backWord(uint64_t now) {
    if (index_ > 0) index_--;
    shownAt_ = now;
    awaitingTurn_ = false;
  }
  // To the start of the current sentence; if already there (or on its first
  // word's heels), to the start of the previous one.
  void backSentence(uint64_t now) {
    if (words_.empty()) return;
    auto startOf = [&](size_t i) {
      while (i > 0 && !endsSentence(words_[i - 1].text)) i--;
      return i;
    };
    size_t s = startOf(index_);
    if (s == index_ && index_ > 0) s = startOf(index_ - 1);
    index_ = s;
    shownAt_ = now;
    awaitingTurn_ = false;
  }

  bool hasPage() const { return hasPage_; }
  bool awaitingTurn() const { return awaitingTurn_; }
  bool finished() const { return finished_; }
  size_t index() const { return index_; }
  size_t count() const { return words_.size(); }
  const Word *current() const {
    return index_ < words_.size() ? &words_[index_] : nullptr;
  }

private:
  void askTurn(uint64_t now, Event &e) {
    awaitingTurn_ = true;
    turnAskedAt_ = now;
    e.requestTurn = true;
  }

  std::vector<Word> words_;
  size_t index_ = 0;
  uint64_t shownAt_ = 0, arrivedAt_ = 0, turnAskedAt_ = 0;
  int wpm_ = kDefaultWpm;
  bool paused_ = false, awaitingTurn_ = false, finished_ = false,
       hasPage_ = false;
};

} // namespace speedread
