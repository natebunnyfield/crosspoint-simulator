// Ink rounding: the press rounds the type's corners and (optionally) spreads
// its ink, on the four-level page image. Every failure mode is a wrong
// picture, so this is the only instrument that can see one. Pins:
//   - 0/0 is bit-exact off and reports so (the pass must not be entered);
//   - the output is ALWAYS one of GrayscalePreview's four levels, at every
//     rung, including heavy -- the 2026-08-24 "keep 4 levels" ruling;
//   - a convex corner LOSES ink and a concave corner GAINS it (that is what
//     rounding is), while a straight edge far from any corner stays put;
//   - a 3 px stem (a 14 pt body stroke at the shipped 2x) keeps its width at
//     standard rounding with no spread, and its counter stays open;
//   - spread makes strokes heavier, never lighter;
//   - the kernel is normalized, so a uniform field is unchanged at any rung.

#include "InkRounding.h"

#include <cstdio>
#include <cstring>
#include <vector>

#include "TestCheck.h"

#define CHECK(x) testcheck::check((x), #x)

namespace {

using GrayscalePreview::kBlack;
using GrayscalePreview::kWhite;

constexpr int W = 64, H = 64;

std::vector<uint8_t> blank() { return std::vector<uint8_t>(W * H, kWhite); }

void fillRect(std::vector<uint8_t> &img, int x0, int y0, int x1, int y1, uint8_t v) {
  for (int y = y0; y < y1; y++)
    for (int x = x0; x < x1; x++) img[y * W + x] = v;
}

uint8_t at(const std::vector<uint8_t> &img, int x, int y) { return img[y * W + x]; }

bool fourLevel(uint8_t v) {
  return v == kWhite || v == GrayscalePreview::kLight || v == GrayscalePreview::kDark ||
         v == kBlack;
}

int inkWidthOfRow(const std::vector<uint8_t> &img, int y) {
  int n = 0;
  for (int x = 0; x < W; x++)
    if (at(img, x, y) != kWhite) n++;
  return n;
}

bool run(std::vector<uint8_t> &img, int rounding, int spread) {
  std::vector<int32_t> scratch;
  return inkrounding::roundLevels(img.data(), W, H, rounding, spread, scratch);
}

}  // namespace

int main() {
  // Off is bit-exact off and says so.
  {
    auto a = blank();
    fillRect(a, 10, 10, 30, 30, kBlack);
    auto b = a;
    CHECK(!run(b, inkrounding::kOff, inkrounding::kSpreadOff));
    CHECK(memcmp(a.data(), b.data(), a.size()) == 0);
  }

  // Four levels out at every rung, on a picture with every input level and
  // every kind of corner in it.
  for (int rung : {inkrounding::kSubtle, inkrounding::kStandard, inkrounding::kHeavy,
                   inkrounding::kMax}) {
    for (int spread : {inkrounding::kSpreadOff, inkrounding::kSpreadStandard,
                       inkrounding::kSpreadMax}) {
      auto img = blank();
      fillRect(img, 8, 8, 40, 40, kBlack);
      fillRect(img, 20, 20, 30, 30, kWhite);  // a counter
      fillRect(img, 44, 8, 60, 12, GrayscalePreview::kDark);
      fillRect(img, 44, 16, 60, 20, GrayscalePreview::kLight);
      CHECK(run(img, rung, spread));
      bool ok = true;
      for (uint8_t v : img) ok = ok && fourLevel(v);
      CHECK(ok && "every output pixel is one of the four levels");
    }
  }

  // A uniform field is unchanged at any rung: the kernel is normalized.
  for (int rung : {inkrounding::kSubtle, inkrounding::kStandard, inkrounding::kHeavy}) {
    auto ink = std::vector<uint8_t>(W * H, kBlack);
    auto paper = blank();
    run(ink, rung, 0);
    run(paper, rung, 0);
    bool inkOk = true, paperOk = true;
    for (uint8_t v : ink) inkOk = inkOk && v == kBlack;
    for (uint8_t v : paper) paperOk = paperOk && v == kWhite;
    CHECK(inkOk && "solid ink stays solid ink");
    CHECK(paperOk && "clean paper stays clean paper");
  }

  // Rounding: a solid square's convex corner loses ink; an L's concave corner
  // gains some; a straight edge mid-side stays where it was.
  {
    auto sq = blank();
    fillRect(sq, 16, 16, 48, 48, kBlack);
    run(sq, inkrounding::kHeavy, 0);
    CHECK(at(sq, 16, 16) != kBlack && "convex corner pixel is no longer full ink");
    CHECK(at(sq, 32, 16) == kBlack && "top edge mid-side is still full ink");
    CHECK(at(sq, 32, 15) == kWhite && "paper just above the edge is still paper");
    CHECK(at(sq, 32, 32) == kBlack && "interior is untouched");

    auto el = blank();
    fillRect(el, 16, 16, 48, 24, kBlack);  // horizontal bar
    fillRect(el, 16, 16, 24, 48, kBlack);  // vertical bar -> concave corner at (24,24)
    const uint8_t before = at(el, 24, 24);
    CHECK(before == kWhite);
    run(el, inkrounding::kHeavy, 0);
    CHECK(at(el, 24, 24) != kWhite && "concave corner picks up ink");
  }

  // A 3 px stem at standard rounding, no spread: width preserved (measured
  // mid-stem, away from the ends), and a 3 px counter stays open.
  {
    auto stem = blank();
    fillRect(stem, 30, 8, 33, 56, kBlack);
    run(stem, inkrounding::kStandard, 0);
    CHECK(inkWidthOfRow(stem, 32) == 3 && "3 px stem keeps its width at standard");

    auto o = blank();
    fillRect(o, 20, 20, 44, 44, kBlack);
    fillRect(o, 30, 30, 33, 33, kWhite);  // 3 px counter
    run(o, inkrounding::kStandard, 0);
    bool open = false;
    for (int y = 30; y < 33; y++)
      for (int x = 30; x < 33; x++) open = open || at(o, x, y) != kBlack;
    CHECK(open && "a 3 px counter is still open at standard");
  }

  // Spread only makes ink heavier: with rounding off and spread at standard
  // every pixel is at least as dark as before, and a stem gets wider.
  {
    auto a = blank();
    fillRect(a, 30, 8, 33, 56, kBlack);
    fillRect(a, 40, 8, 43, 56, GrayscalePreview::kLight);
    auto b = a;
    CHECK(run(b, inkrounding::kOff, inkrounding::kSpreadStandard));
    // Not per pixel -- spread rides a blur, and a faint 1 px fringe next to
    // nothing can fall under the white threshold -- but in TOTAL: the page
    // carries at least as much ink, and a solid stem never narrows.
    long inkA = 0, inkB = 0;
    for (size_t i = 0; i < a.size(); i++) {
      inkA += 255 - a[i];
      inkB += 255 - b[i];
    }
    CHECK(inkB >= inkA && "spread never lowers the page's total ink");
    CHECK(inkWidthOfRow(b, 32) >= inkWidthOfRow(a, 32) && "spread does not narrow a stem");
  }

  // Spread never touches clean paper: a page with one word keeps every paper
  // pixel far from the word bit-exact at the top of the spread range.
  {
    auto a = blank();
    fillRect(a, 20, 20, 30, 40, kBlack);
    auto b = a;
    run(b, inkrounding::kOff, inkrounding::kSpreadMax);
    CHECK(at(b, 50, 50) == kWhite && "paper far from ink stays paper under max spread");
    CHECK(at(b, 5, 5) == kWhite);
    CHECK(at(b, 25, 30) == kBlack && "ink interior stays ink under max spread");
  }

  // Clamps hold: out-of-range dials fold to the range, NaN-free.
  CHECK(inkrounding::clampRounding(-5) == 0);
  CHECK(inkrounding::clampRounding(999) == inkrounding::kMax);
  CHECK(inkrounding::clampSpread(999) == inkrounding::kSpreadMax);
  CHECK(inkrounding::sigmaFor(0) == 0.0f);
  CHECK(inkrounding::kernelFor(0.0f).radius == 0);
  CHECK(inkrounding::kernelFor(10.0f).radius == inkrounding::kMaxKernelRadius);

  if (testcheck::g_failures == 0) std::printf("ink_rounding_test: all checks passed\n");
  return testcheck::g_failures ? 1 : 0;
}
