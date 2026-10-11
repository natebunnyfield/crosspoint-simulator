// pageink (src/PageInkRows.h): the page's own first and last ink rows, measured
// from the display's landscape level buffer in PORTRAIT rows, which is what
// the zen paper is placed from since 2026-10-11 (owner: "only one circle unit
// above the optical visual first text on the page, and two units below the
// lowest text"). Silent failure modes this pins: the portrait/landscape axis
// swapped (the paper would hug the page's SIDES), a dark page read as all ink
// (background taken as a constant instead of the corners' value), a blank page
// reported as ink at row 0 (the paper placed one circle above nothing), and a
// torn read of first/last across two pages.
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>

#include "PageInkRows.h"

static std::vector<uint8_t> blank(int w, int h, uint8_t bg) {
  return std::vector<uint8_t>(static_cast<size_t>(w) * h, bg);
}

int main() {
  // Landscape 10 wide x 6 tall; portrait rows are framebuffer COLUMNS.
  const int w = 10, h = 6;
  {
    auto b = blank(w, h, 3);              // light page: 3 = white level
    b[2 * w + 4] = 0;                     // ink at column 4 (portrait row 4)
    b[5 * w + 7] = 1;                     // a lighter level at column 7, still ink
    const auto r = pageink::inkRowsPortrait(b.data(), w, h);
    assert(r.any && r.first == 4 && r.last == 7);
  }
  {
    // Dark page: background 0, ink is the LIGHT level. Same rows must come out.
    auto b = blank(w, h, 0);
    b[1 * w + 2] = 3; b[4 * w + 8] = 2;
    const auto r = pageink::inkRowsPortrait(b.data(), w, h);
    assert(r.any && r.first == 2 && r.last == 8);
  }
  {
    // Blank page: no ink, and the channel clears so the layout falls back.
    auto b = blank(w, h, 3);
    const auto r = pageink::inkRowsPortrait(b.data(), w, h);
    assert(!r.any);
    pageink::InkRowsChannel ch;
    ch.publish(pageink::Rows{1, 5, true});
    int f = 0, l = 0;
    assert(ch.read(f, l) && f == 1 && l == 5);
    ch.publish(r);
    assert(!ch.read(f, l));
  }
  {
    // One corner holding ink does not become the background: majority of four.
    auto b = blank(w, h, 3);
    b[0] = 0;                              // top-left corner ink
    b[3 * w + 5] = 0;
    const auto r = pageink::inkRowsPortrait(b.data(), w, h);
    assert(r.any && r.first == 0 && r.last == 5);
  }
  {
    // A full-width rule across every column reads first 0 .. last w-1.
    auto b = blank(w, h, 3);
    for (int x = 0; x < w; x++) b[3 * w + x] = 0;
    const auto r = pageink::inkRowsPortrait(b.data(), w, h);
    assert(r.any && r.first == 0 && r.last == w - 1);
  }
  {
    // The channel never tears: a read returns one publish's pair, whole.
    pageink::InkRowsChannel ch;
    ch.publish(pageink::Rows{100, 700, true});
    ch.publish(pageink::Rows{250, 690, true});
    int f = 0, l = 0;
    assert(ch.read(f, l));
    assert((f == 100 && l == 700) || (f == 250 && l == 690));
    assert(f == 250 && l == 690);
  }
  std::puts("page_ink_rows: ok");
  return 0;
}
