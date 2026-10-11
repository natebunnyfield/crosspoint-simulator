#pragma once

#include <atomic>
#include <cstddef>
#include <cstdint>

// THE PAGE'S OWN INK, top and bottom, in presented (portrait) pixels.
//
// Owner, 2026-10-11, on a phone screenshot of a dedication page whose first
// line sat a third of a page below the paper's top edge: "the first text in a
// page does not have space above it, so that there is only one circle unit
// above the optical visual first text on the page, and two units below the
// lowest text." The zen paper (docs/zen-mode.md, C32) was placed from the
// insets the READER PUBLISHES -- the text block's margin less the cap-ink trim
// -- which is where the first line WOULD start on a body page. On the first
// page of a spine section the firmware drops the first line by its chapter
// sinkage (viewport / 5, snapped to whole lines; ChapterHtmlSlimParser.cpp,
// kChapterSinkageFraction, owner ruling 2026-08-22) and the published inset
// does not know it, so the paper sat one circle PLUS the sinkage above the
// first ink; and a page whose last line ends short had more than two circles
// below its lowest ink (docs/zen-mode.md measured 2.2-2.6). "Optical visual
// first text" is the ink itself, so the paper is now placed from the ink:
// this header measures it from the level buffer the display writes, in the
// same pixel write that commits the published insets, and the zen placement
// prefers it to the published pair when the page has any ink.
//
// Pure and header-only (host-tested, tests/page_ink_rows_test.cpp) for the
// usual reason: every failure mode is a wrong picture with no error.
namespace pageink {

struct Rows {
  int first = -1;  // first portrait row with ink, inclusive
  int last = -1;   // last portrait row with ink, inclusive
  bool any = false;
};

// The firmware renders a portrait page into the LANDSCAPE framebuffer with
// GfxRenderer's Portrait rotation (crosspoint-reader
// lib/GfxRenderer/GfxRenderer.cpp rotateCoordinates): a portrait pixel (px, py)
// lands at framebuffer (x = py, y = panelHeight - 1 - px). So a portrait ROW is
// a framebuffer COLUMN, and the first ink row of the presented page is the
// lowest framebuffer x holding a non-background pixel. The same mapping
// `ios/CrossPointIOSShim.cpp` uses for the published insets (fbPortraitH =
// activeWidth()).
//
// Background is whichever value the four corners agree on (majority of four),
// so a dark page (light ink on dark paper, the firmware's own dark mode) and a
// light page measure the same way without knowing the palette; the corners
// are always inside the panel's viewable margin, never ink.
inline uint8_t backgroundLevel(const uint8_t *levels, int w, int h) {
  if (w <= 0 || h <= 0) return 0;
  const uint8_t c[4] = {levels[0], levels[w - 1],
                        levels[static_cast<size_t>(h - 1) * w],
                        levels[static_cast<size_t>(h - 1) * w + (w - 1)]};
  int best = 0, bestCount = 0;
  for (int i = 0; i < 4; i++) {
    int n = 0;
    for (int j = 0; j < 4; j++) n += (c[j] == c[i]);
    if (n > bestCount) { bestCount = n; best = i; }
  }
  return c[best];
}

// `levels` is the display's row-major landscape level buffer (w * h, one byte
// per pixel, any level alphabet). Returns the portrait rows (= framebuffer
// columns) of the first and last ink. O(w * h), ~0.4 M byte reads on an X3,
// well under a millisecond beside the write it rides on.
inline Rows inkRowsPortrait(const uint8_t *levels, int w, int h) {
  Rows r;
  if (!levels || w <= 0 || h <= 0) return r;
  const uint8_t bg = backgroundLevel(levels, w, h);
  int first = -1, last = -1;
  for (int x = 0; x < w && first < 0; x++)
    for (int y = 0; y < h; y++)
      if (levels[static_cast<size_t>(y) * w + x] != bg) { first = x; break; }
  if (first < 0) return r;
  for (int x = w - 1; x >= first && last < 0; x--)
    for (int y = 0; y < h; y++)
      if (levels[static_cast<size_t>(y) * w + x] != bg) { last = x; break; }
  r.first = first; r.last = last; r.any = true;
  return r;
}

// The channel the pixel writer publishes into and the zen layout reads: one
// atomic, never torn (the ReaderInsetsChannel argument, src/ReaderInsetsChannel.h).
// `valid` false until a page with ink has been measured. A write of a page
// with no ink clears it, so the layout falls back to the published insets
// rather than placing the paper around a picture that is not there.
class InkRowsChannel {
 public:
  void publish(const Rows &r) {
    if (!r.any) { valid_.store(false, std::memory_order_release); return; }
    packed_.store((static_cast<uint64_t>(static_cast<uint32_t>(r.first)) << 32) |
                      static_cast<uint32_t>(r.last),
                  std::memory_order_release);
    valid_.store(true, std::memory_order_release);
  }
  bool read(int &first, int &last) const {
    if (!valid_.load(std::memory_order_acquire)) return false;
    const uint64_t p = packed_.load(std::memory_order_acquire);
    first = static_cast<int>(static_cast<uint32_t>(p >> 32));
    last = static_cast<int>(static_cast<uint32_t>(p & 0xffffffffu));
    return true;
  }
  void clear() { valid_.store(false, std::memory_order_release); }

 private:
  std::atomic<uint64_t> packed_{0};
  std::atomic<bool> valid_{false};
};

}  // namespace pageink
