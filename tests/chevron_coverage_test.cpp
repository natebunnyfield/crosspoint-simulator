// The keyboard chip's chevron: does it antialias, and is it still the same shape?
//
// The chevron was drawn as stacked one-pixel rows with the offset stepping a
// whole pixel per row. Measured off the Metal renderer at iPhone numbers
// (402x874 pt @3x), that came back with exactly two levels -- 0 and 255 -- which
// made it the only unantialiased diagonal on a screen full of coverage-
// antialiased UIKit chrome, and that is what "jagged" was.
//
// Two halves, and BOTH are needed. Antialiasing alone is easy to get by drawing
// a different, softer shape; the value of the fix is that it antialiases WITHOUT
// changing anything the owner approved. So this pins the edge quality and the
// geometry together, and either one regressing fails.
//
// Host test, no SDL: ChevronCoverage.h is pure arithmetic, extracted for exactly
// this reason (same move as PadCore.h and PadPalette.h).
//
//   c++ -std=c++17 -Iios -o /tmp/chevron tests/chevron_coverage_test.cpp && /tmp/chevron

#include "ChevronCoverage.h"

#include <cmath>
#include <cstdio>
#include <string>
#include <vector>
#include "TestCheck.h"
using testcheck::check;

static int &failures = testcheck::g_failures;

// The real numbers: a 48 pt chip on a 3x phone is 144 device px, and
// paintKeyboardChip derives the glyph from that exactly this way.
static chevron::Geometry phoneGeometry(const bool keyboardUp) {
  const float chipH = 48.0f * 3.0f;
  const float glyphH = chipH * 0.52f;
  const float chevH = glyphH * 0.26f;
  // cx and top carry the sub-pixel phase of the real placement; top is
  // deliberately fractional, because that is what it is on the device and a
  // whole-number stand-in would hide every phase bug.
  return chevron::Geometry{76.0f, 38.56f, chevH,
                           std::max(1.0f, std::roundf(chevH * 0.42f)), keyboardUp};
}

int main() {
  for (const bool up : {false, true}) {
    const chevron::Geometry g = phoneGeometry(up);
    const chevron::Bounds b = chevron::bounds(g);
    const std::string tag = up ? " [dismiss/v]" : " [summon/^]";

    // ---- Coverage is coverage -------------------------------------------
    int partials = 0, solids = 0;
    for (int py = b.y0; py <= b.y1; ++py) {
      for (int px = b.x0; px <= b.x1; ++px) {
        const float c = chevron::coverage(g, px, py);
        check(c >= 0.0f && c <= 1.0f, "coverage out of [0,1] at " + std::to_string(px) + "," +
                                          std::to_string(py) + tag);
        if (c > 0.05f && c < 0.95f) ++partials;
        if (c > 0.999f) ++solids;
      }
    }

    // THE REGRESSION THIS FILE EXISTS FOR. The old construction could only ever
    // produce 0 or 1; a partial pixel is proof the edge is being covered rather
    // than stepped. A generous count, so this fails on "no antialiasing at all"
    // and not on a tweak to the sampling.
    check(partials > 20, "too few partially covered pixels (" + std::to_string(partials) +
                             ") -- the edge is not antialiased" + tag);
    check(solids > 50, "too few fully inked pixels (" + std::to_string(solids) +
                           ") -- the glyph is washed out rather than antialiased" + tag);

    // ---- ...and the shape is the old shape -------------------------------
    // Horizontal extent: the arms reach chevH either side of centre, plus half
    // an arm of width. Allow one pixel of slack for the partial edge pixel.
    int minX = b.x1 + 1, maxX = b.x0 - 1;
    for (int py = b.y0; py <= b.y1; ++py) {
      for (int px = b.x0; px <= b.x1; ++px) {
        if (chevron::coverage(g, px, py) <= 0.0f) continue;
        if (px < minX) minX = px;
        if (px > maxX) maxX = px;
      }
    }
    const float wantMin = g.cx - g.chevH - g.arm / 2.0f;
    const float wantMax = g.cx + g.chevH + g.arm / 2.0f;
    check(std::fabs(minX - wantMin) <= 1.0f,
          "left extent moved: " + std::to_string(minX) + " vs " + std::to_string(wantMin) + tag);
    check(std::fabs((maxX + 1) - wantMax) <= 1.0f,
          "right extent moved: " + std::to_string(maxX + 1) + " vs " + std::to_string(wantMax) + tag);

    // Weight: across the middle of an arm, well away from the apex overlap and
    // both ends, the total coverage on a row must equal the arm's width.
    const float sy = up ? g.top + g.chevH * 0.25f : g.top + g.chevH * 0.75f;
    float rowInk = 0.0f;
    for (int px = b.x0; px <= b.x1; ++px) rowInk += chevron::coverageAtRow(g, px, sy);
    check(std::fabs(rowInk - 2.0f * g.arm) < 0.01f,
          "arm weight changed: " + std::to_string(rowInk) + " vs " +
              std::to_string(2.0f * g.arm) + tag);

    // The apex is FLAT and exactly one arm wide -- the old shape's blunt top,
    // kept on purpose. It is the most visible proportion in the glyph and the
    // one a "smoother" chevron would quietly round off.
    const float apexY = up ? g.top + g.chevH - 0.01f : g.top + 0.01f;
    float apexInk = 0.0f;
    for (int px = b.x0; px <= b.x1; ++px) apexInk += chevron::coverageAtRow(g, px, apexY);
    check(std::fabs(apexInk - g.arm) < 0.05f,
          "apex is no longer one arm wide: " + std::to_string(apexInk) + " vs " +
              std::to_string(g.arm) + tag);

    // Union, not sum. Just below the apex the two arms overlap; if that were
    // added rather than unioned the row would carry two arms' worth of ink and
    // the notch would fill in.
    float overlapInk = 0.0f;
    const float overlapY = up ? g.top + g.chevH - g.arm / 4.0f : g.top + g.arm / 4.0f;
    for (int px = b.x0; px <= b.x1; ++px) overlapInk += chevron::coverageAtRow(g, px, overlapY);
    check(overlapInk < 2.0f * g.arm,
          "apex overlap is being summed, not unioned: " + std::to_string(overlapInk) + tag);

    // Nothing outside the glyph box.
    check(chevron::coverage(g, b.x0 - 2, b.y0) == 0.0f, "ink left of the box" + tag);
    check(chevron::coverage(g, g.cx, b.y0 - 2) == 0.0f, "ink above the box" + tag);
    check(chevron::coverage(g, g.cx, b.y1 + 2) == 0.0f, "ink below the box" + tag);
  }

  if (failures == 0) std::printf("chevron_coverage: all checks passed\n");
  return failures == 0 ? 0 : 1;
}
