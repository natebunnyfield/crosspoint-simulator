#pragma once

// THE PICCO PAD'S OPTIONAL UP/DOWN PAIR, decided purely (tests/picco_pad_test.cpp).
//
// Owner 2026-11-27, asking "where is up down button group in picco app?", then:
// "just match x3 app and make it an ios app setting (default off)". So, with
// Settings > Buttons > Up/Down Buttons on, the Picco app shows the X3 pad's
// Up|Down pair in the place the X3 pad gives it -- the row the Picco's rocker
// vacated when it moved up into the arrows' slot (CrossPointIOSShim.cpp
// layoutPad, Picco block) -- pressing the X3's side pair
// (HalGPIO::BTN_HOST_SIDE_UP / _DOWN): font size on a tap and family on a hold
// in a book, Up and Down elsewhere, as on the X3.
//
// Three rules, each silent on a phone if wrong:
//   * OFF places nothing, so the pad is today's pixel for pixel.
//   * IT NEVER SITS ON ANOTHER CONTROL (owner: it must not overlap or displace
//     POWER, the slide switch, the keyboard chip, Select or the rocker). A
//     collision refuses the pair and names the control, rather than moving
//     anything.
//   * Up is the LEFT half, as on the X3 pad -- not the Picco rocker's swapped
//     halves (layoutPad: the rocker's left half is previous there).
//
// Free of SDL so it can be host-tested; the shim converts SDL_FRect.
namespace piccopad {

struct Rect {
  float x = 0, y = 0, w = 0, h = 0;
};

constexpr bool empty(Rect r) { return r.w <= 0.0f || r.h <= 0.0f; }

// Strict overlap: rects that only share an edge do not overlap (the pad's
// fused pairs abut by construction).
constexpr bool overlaps(Rect a, Rect b) {
  return !empty(a) && !empty(b) && a.x < b.x + b.w && b.x < a.x + a.w &&
         a.y < b.y + b.h && b.y < a.y + a.h;
}

struct Pair {
  bool placed = false;
  Rect up{};    // the LEFT half: presses the side Up key
  Rect down{};  // the RIGHT half: presses the side Down key
  int collidesWith = -1;  // index into `others` of the first collision, or -1
};

// `x3Up` / `x3Down`: where the X3 pad puts its Up and Down halves in this
// layout (layoutPadImpl's kPadUp / kPadDown, before the Picco block moves the
// rocker). `others`: every control the pair must stay clear of.
constexpr Pair sidePair(bool enabled, Rect x3Up, Rect x3Down,
                        const Rect* others, int count) {
  Pair p{};
  if (!enabled || empty(x3Up) || empty(x3Down)) return p;
  for (int i = 0; i < count; ++i) {
    if (overlaps(x3Up, others[i]) || overlaps(x3Down, others[i])) {
      p.collidesWith = i;
      return p;
    }
  }
  p.placed = true;
  p.up = x3Up;
  p.down = x3Down;
  return p;
}

}  // namespace piccopad
