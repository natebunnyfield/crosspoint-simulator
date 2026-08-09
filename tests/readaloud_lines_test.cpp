// readaloud::groupIntoLines -- the word rects an assistive technology is handed
// as per-line labels.
//
// WHY THIS IS A HOST TEST
//
// The grouping used to live inside ios/CrossPointAccessibility.mm, which cannot
// be compiled or run anywhere but a phone. That is also the only part of the
// path that has actually been wrong, and being unable to see it produced two
// fixes shipped on reasoning. It is a free function now, so this test and the
// desktop dump (CROSSPOINT_SIM_READALOUD_DUMP=1) both reach it.
//
// Build:
//   c++ -std=c++17 -Isrc tests/readaloud_lines_test.cpp -o /tmp/ral && /tmp/ral

#include "ReadAloudLines.h"

#include <cassert>
#include <cstdio>
#include <string>
#include <vector>

namespace {

using readaloud::groupIntoLines;

ReadAloudWordRect wr(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint32_t off, uint16_t len) {
  return ReadAloudWordRect{x, y, w, h, off, len};
}

}  // namespace

int main() {
  // --- one line, several words ---
  {
    const std::string text = "the quick brown fox";
    const std::vector<ReadAloudWordRect> rects = {
        wr(10, 100, 30, 20, 0, 3), wr(45, 100, 50, 20, 4, 5), wr(100, 100, 50, 20, 10, 5),
        wr(155, 100, 25, 20, 16, 3)};
    const auto lines = groupIntoLines(text, rects);
    assert(lines.size() == 1);
    assert(lines[0].text == "the quick brown fox" && "a line's label is its whole span, not its first word");
    // Union of the rects, so the highlight covers the line.
    assert(lines[0].x == 10 && lines[0].y == 100);
    assert(lines[0].w == 170 && lines[0].h == 20);
  }

  // --- two lines, split by y ---
  {
    const std::string text = "first line second line";
    const std::vector<ReadAloudWordRect> rects = {wr(10, 100, 40, 20, 0, 5),  wr(55, 100, 30, 20, 6, 4),
                                                  wr(10, 130, 55, 20, 11, 6), wr(70, 130, 30, 20, 18, 4)};
    const auto lines = groupIntoLines(text, rects);
    assert(lines.size() == 2);
    assert(lines[0].text == "first line");
    assert(lines[1].text == "second line");
    assert(lines[0].y == 100 && lines[1].y == 130);
  }

  // --- a hyphen-split word reads WHOLE on both lines ---
  //
  // The firmware publishes one rect per visual fragment, both carrying the
  // joined word's byteOffset/byteLen (EpubReaderActivity::captureReadAloudPage).
  // The two labels therefore overlap, deliberately: speech that said "inter"
  // then "est of" would be worse than saying the word twice.
  {
    const std::string text = "the interest of readers";
    const std::vector<ReadAloudWordRect> rects = {
        wr(10, 100, 30, 20, 0, 3),    // "the"
        wr(45, 100, 60, 20, 4, 8),    // "inter-" fragment, carries all of "interest"
        wr(10, 130, 40, 20, 4, 8),    // "est" fragment, same byte range
        wr(55, 130, 20, 20, 13, 2),   // "of"
        wr(80, 130, 60, 20, 16, 7),   // "readers"
    };
    const auto lines = groupIntoLines(text, rects);
    assert(lines.size() == 2);
    assert(lines[0].text == "the interest" && "the word must not be cut to its prefix");
    assert(lines[1].text == "interest of readers" && "nor to its suffix -- the second line repeats it whole");
    // Never "inter" / "est": a reader hearing either half alone is the bug.
    assert(lines[0].text.find("inter ") == std::string::npos);
    assert(lines[1].text.substr(0, 3) != "est" && "a label starting mid-word is the reported symptom");
  }

  // --- rects out of order on the y axis are NOT sorted ---
  //
  // Publish order is reading order. Sorting by y would reorder a hyphen-split
  // word's fragments, which share a byte range and must stay with their lines.
  {
    const std::string text = "alpha beta";
    const std::vector<ReadAloudWordRect> rects = {wr(10, 200, 40, 20, 0, 5), wr(10, 100, 40, 20, 6, 4)};
    const auto lines = groupIntoLines(text, rects);
    assert(lines.size() == 2);
    assert(lines[0].text == "alpha" && lines[0].y == 200 && "publish order wins over y order");
    assert(lines[1].text == "beta");
  }

  // --- a range past the end of the text is DROPPED, not clamped ---
  //
  // Clamping would ship a silently truncated label, which is exactly the class
  // of failure this path keeps producing. A bad range means the capture is
  // wrong and the line is better absent than half-right.
  {
    const std::string text = "short";
    const std::vector<ReadAloudWordRect> rects = {wr(10, 100, 40, 20, 0, 99)};
    assert(groupIntoLines(text, rects).empty());
  }

  // --- degenerate inputs ---
  {
    assert(groupIntoLines("", {}).empty());
    assert(groupIntoLines("text", {}).empty());
    // Zero-length range: nothing to say.
    assert(groupIntoLines("text", {wr(0, 0, 10, 10, 2, 0)}).empty());
  }

  // --- every line of a real-shaped page produces a non-empty label ---
  {
    std::string text;
    std::vector<ReadAloudWordRect> rects;
    for (int line = 0; line < 20; line++) {
      for (int word = 0; word < 8; word++) {
        if (!text.empty()) text.push_back(' ');
        const uint32_t off = static_cast<uint32_t>(text.size());
        text += "word";
        rects.push_back(wr(static_cast<uint16_t>(10 + word * 60), static_cast<uint16_t>(100 + line * 30), 50, 20,
                           off, 4));
      }
    }
    const auto lines = groupIntoLines(text, rects);
    assert(lines.size() == 20 && "one element per line, not per word -- per-word pauses after every word");
    for (const auto &l : lines) {
      assert(!l.text.empty());
      assert(l.text.substr(0, 4) == "word" && "every label starts at a word boundary");
    }
  }

  std::puts("readaloud_lines: PASS");
  return 0;
}
