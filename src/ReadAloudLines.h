#pragma once

// Grouping the page's per-word rects into per-LINE labels.
//
// Speak Screen and VoiceOver read one element at a time, concatenating them, so
// the element has to be a line -- per-word elements put a pause after every
// word. This turns the channel's word rects into the line labels an assistive
// technology is handed.
//
// A free header with no UIKit and no HAL state, for the same reason
// ReadAloudChannel.h is: the iOS builder cannot be compiled or run anywhere but
// a phone, and this is the part that can actually be wrong. It has been:
// labels arrived starting mid-word ("est of enriching our global cultural"),
// and there was no way to see that off-device. tests/readaloud_lines_test.cpp
// pins it, and CROSSPOINT_SIM_READALOUD_DUMP=1 prints it from the desktop
// simulator against a real book.

#include <algorithm>
#include <cstdint>
#include <string>
#include <vector>

#include "ReadAloudChannel.h"

namespace readaloud {

struct LineLabel {
  std::string text;
  // Union of the line's rects, in the same logical portrait pixels the rects
  // use. The iOS builder maps this to screen points.
  uint16_t x = 0, y = 0, w = 0, h = 0;
  // Byte range into the page text, kept so a caller can map a label back.
  uint32_t byteOffset = 0;
  uint32_t byteEnd = 0;
};

// Group `rects` into lines by their y, in publish order.
//
// The rects arrive in reading order, so a run of equal y IS a line and no
// sorting is needed or wanted -- sorting would reorder a line whose fragments
// share a byte range.
//
// THE BYTE RANGE IS THE UNION OF THE LINE'S RECTS, and a hyphen-split word
// deliberately widens it: the firmware publishes one rect per visual fragment,
// both carrying the whole word's byteOffset/byteLen, so the word reads whole on
// both lines rather than being cut into "inter" and "est". Overlapping labels
// on consecutive lines are the intended consequence.
inline std::vector<LineLabel> groupIntoLines(const std::string &text,
                                             const std::vector<ReadAloudWordRect> &rects) {
  std::vector<LineLabel> out;
  size_t i = 0;
  while (i < rects.size()) {
    const uint16_t lineY = rects[i].y;

    LineLabel line;
    line.byteOffset = rects[i].byteOffset;
    line.byteEnd = rects[i].byteOffset + rects[i].byteLen;
    uint16_t left = rects[i].x;
    uint16_t right = static_cast<uint16_t>(rects[i].x + rects[i].w);
    uint16_t top = rects[i].y;
    uint16_t bottom = static_cast<uint16_t>(rects[i].y + rects[i].h);

    size_t j = i;
    while (j < rects.size() && rects[j].y == lineY) {
      const ReadAloudWordRect &r = rects[j];
      line.byteOffset = std::min(line.byteOffset, r.byteOffset);
      line.byteEnd = std::max(line.byteEnd, static_cast<uint32_t>(r.byteOffset) + r.byteLen);
      left = std::min(left, r.x);
      right = std::max(right, static_cast<uint16_t>(r.x + r.w));
      top = std::min(top, r.y);
      bottom = std::max(bottom, static_cast<uint16_t>(r.y + r.h));
      j++;
    }
    i = j;

    // A range past the end of the text is a capture bug, not something to
    // paper over with a clamp that would ship a truncated label silently.
    if (line.byteOffset >= line.byteEnd || line.byteEnd > text.size()) continue;

    line.text = text.substr(line.byteOffset, line.byteEnd - line.byteOffset);
    if (line.text.empty()) continue;
    line.x = left;
    line.y = top;
    line.w = static_cast<uint16_t>(right - left);
    line.h = static_cast<uint16_t>(bottom - top);
    out.push_back(std::move(line));
  }
  return out;
}

}  // namespace readaloud
