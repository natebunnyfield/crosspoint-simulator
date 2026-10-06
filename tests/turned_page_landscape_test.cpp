// Tests for src/TurnedPageLandscape.h: the turned page's landscape, decided
// purely (docs/turned-page-landscape-plan-2026-10-04.md).
//
// The contract under test, and the silent failure each part exists for:
//   * hintFor -- the phone gains landscape ONLY while a turned page is up, and
//     only the one a COUNTER-clockwise turn produces (LandscapeRight: the table
//     is turned clockwise on the page; owner 2026-10-04, correcting build 304,
//     "the iphone would need to be turned ccw not clockwise"); it drops it the
//     moment the page goes (the snap-back, owner Q2). The iPad's hint never
//     changes and must equal the string simulator_main.cpp sets at startup, or
//     the first poll would "change" it and ask UIKit to re-query for nothing.
//     The QA force is inert on upright pages; on the iPad it forces its own two
//     landscapes.
//   * presentLandscape -- needs BOTH a turned page and a landscape window: an
//     iPad held landscape on an upright page keeps its own layout.
//   * Channel -- the latch the firmware publishes into: a change is reported
//     (it is what asks the host for a present), a repeat is not, and a
//     non-reader screen entering clears it -- the chapter list pushed over a
//     turned page never runs the reader's onExit, and was presented turned
//     until that clear existed (review finding 2). The reset is the reboot's.
//   * layoutFor -- the G3 split (owner Q3b): every control inside the screen
//     and clear of the safe areas (the Dynamic Island sits in a landscape side
//     inset), outside the box the panel is fitted into, the left half
//     (Back/Select, Power) left of it and the right half (Left/Right, Up/Down)
//     right of it, no two controls overlapping, each at least the HIG's 44 pt;
//     and zen shows no pad and gives the page the width.
//
// Build + run (no framework, no SDL):
//   c++ -std=c++20 -Isrc tests/turned_page_landscape_test.cpp -o /tmp/tpl && /tmp/tpl

#include "TurnedPageChannel.h"
#include "TurnedPageLandscape.h"

#include <cstdio>
#include <cstring>

#include "TestCheck.h"

static int &failures = testcheck::g_failures;
using testcheck::check;

static bool overlaps(const turnedpage::Rect &a, const turnedpage::Rect &b) {
  return a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h;
}

int main() {
  using namespace turnedpage;

  // --- the hint -------------------------------------------------------------
  check(std::strcmp(hintFor(false, false, false), "Portrait") == 0,
        "phone, upright page: portrait only");
  check(std::strcmp(hintFor(false, true, false), "Portrait LandscapeRight") == 0,
        "phone, turned page: portrait plus the landscape of a counter-clockwise turn");
  check(std::strstr(hintFor(false, true, false), "LandscapeLeft") == nullptr,
        "phone never gains the clockwise turn's landscape (owner 2026-10-04: turned ccw)");
  check(std::strcmp(hintFor(false, true, true), "LandscapeRight") == 0,
        "phone, turned page, QA force: landscape only, so iOS rotates by itself");
  check(std::strcmp(hintFor(false, false, true), "Portrait") == 0,
        "the QA force is inert on an upright page");
  // The iPad's string must be simulator_main.cpp's startup hint, byte for byte.
  const char *pad = "Portrait LandscapeLeft LandscapeRight";
  check(std::strcmp(hintFor(true, false, false), pad) == 0, "iPad, upright: unchanged");
  check(std::strcmp(hintFor(true, true, false), pad) == 0, "iPad, turned: unchanged");
  check(std::strcmp(hintFor(true, true, true), "LandscapeLeft LandscapeRight") == 0,
        "iPad, turned page, QA force: its two landscapes only");
  check(std::strcmp(hintFor(true, false, true), pad) == 0,
        "iPad: the QA force is inert on an upright page");

  // --- the latch -----------------------------------------------------------
  {
    Channel ch;
    check(!ch.showing(), "channel starts upright");
    check(!ch.publish(false), "publishing upright over upright is no change");
    check(ch.publish(true), "a turned page arriving is a change");
    check(ch.showing(), "and it shows");
    check(!ch.publish(true), "the same turned page again is no change");
    check(ch.screenEntered(), "a screen pushed over it clears it, as a change");
    check(!ch.showing(), "and the page no longer shows");
    check(!ch.screenEntered(), "a second screen over nothing turned is no change");
    check(ch.publish(true), "the reader redrawing the page after the pop turns it again");
    ch.reset();
    check(!ch.showing(), "the reboot's reset clears it");
    check(ch.publish(true), "and a turned page after the reboot is a change again");
  }

  // --- when the landscape presentation applies --------------------------------
  check(presentLandscape(true, 2736, 1260), "turned page, landscape window: yes");
  check(!presentLandscape(true, 1260, 2736), "turned page, portrait window: no (not turned yet)");
  check(!presentLandscape(false, 2752, 2064), "iPad landscape, upright page: its own layout");
  check(!presentLandscape(false, 1260, 2736), "upright page, portrait window: no");

  // --- the G3 layout, at the sizes it ships on --------------------------------
  struct Case {
    const char *name;
    float W, H, sL, sR, sT, sB;
    bool isPad;
  };
  const Case cases[] = {
      {"iPhone Air", 912, 420, 62, 62, 0, 21, false},
      {"iPhone 13 mini", 812, 375, 50, 50, 0, 21, false},
      {"iPhone SE", 667, 375, 0, 0, 0, 0, false},
      {"iPhone 16 Pro Max", 956, 440, 62, 62, 0, 21, false},
      {"iPad Pro 13", 1376, 1032, 0, 0, 24, 20, true},
      {"iPad mini", 1133, 744, 0, 0, 24, 20, true},
  };
  for (const Case &c : cases) {
    char what[256];
    const Layout L = layoutFor(c.W, c.H, c.sL, c.sR, c.sT, c.sB, false, c.isPad);
    const Rect panelBox{L.insetLeft, L.insetTop, c.W - L.insetLeft - L.insetRight,
                        c.H - L.insetTop - L.insetBottom};
    std::snprintf(what, sizeof what, "%s: the pad is shown out of zen", c.name);
    check(L.padShown, what);
    std::snprintf(what, sizeof what, "%s: the panel box is still a real box", c.name);
    check(panelBox.w > 200 && panelBox.h > 200, what);
    const Rect ctl[] = {L.back, L.confirm, L.left, L.right, L.power, L.up, L.down};
    const char *names[] = {"Back", "Select", "Left", "Right", "Power", "Up", "Down"};
    for (int i = 0; i < 7; i++) {
      const Rect &r = ctl[i];
      std::snprintf(what, sizeof what, "%s: %s inside the screen and clear of the safe areas",
                    c.name, names[i]);
      check(r.x >= c.sL && r.y >= c.sT && r.x + r.w <= c.W - c.sR && r.y + r.h <= c.H - c.sB,
            what);
      std::snprintf(what, sizeof what, "%s: %s outside the panel's box", c.name, names[i]);
      check(!overlaps(r, panelBox), what);
      std::snprintf(what, sizeof what, "%s: %s at least 44 pt wide (HIG)", c.name, names[i]);
      check(r.w >= 44.0f, what);
      // POWER stays half height by ruling (2026-08-11); on the iPad the whole
      // bottom row is half height, as the tablet's own layout draws it.
      const bool halfByRuling = i == 4 || (c.isPad && (i == 5 || i == 6));
      if (!halfByRuling) {
        std::snprintf(what, sizeof what, "%s: %s at least 44 pt tall (HIG)", c.name, names[i]);
        check(r.h >= 44.0f, what);
      }
      for (int j = i + 1; j < 7; j++) {
        std::snprintf(what, sizeof what, "%s: %s and %s do not overlap", c.name, names[i],
                      names[j]);
        check(!overlaps(r, ctl[j]), what);
      }
    }
    // G3: today's left half on the left of the page, its right half on the right.
    const float panelL = panelBox.x, panelR = panelBox.x + panelBox.w;
    std::snprintf(what, sizeof what, "%s: Back/Select and Power left of the page", c.name);
    check(L.back.x + 2 * L.back.w <= panelL && L.power.x + L.power.w <= panelL, what);
    std::snprintf(what, sizeof what, "%s: Left/Right and Up/Down right of the page", c.name);
    check(L.left.x >= panelR && L.up.x >= panelR, what);
    std::snprintf(what, sizeof what, "%s: the pairs are fused (no gap inside a pair)", c.name);
    check(L.back.x + L.back.w == L.confirm.x && L.left.x + L.left.w == L.right.x &&
              L.up.x + L.up.w == L.down.x,
          what);
    std::snprintf(what, sizeof what, "%s: the keyboard chip clear of every control", c.name);
    bool chipClear = true;
    for (const Rect &r : ctl) chipClear = chipClear && !overlaps(L.chip, r);
    check(chipClear && !overlaps(L.chip, panelBox), what);

    // The iPad keeps the tablet's thumb row: 448 pt up from the bottom edge.
    if (c.isPad) {
      std::snprintf(what, sizeof what, "%s: the front pairs on the tablet's thumb row", c.name);
      check(L.back.y + L.back.h / 2 == c.H - kThumbRowFromBottom &&
                L.left.y + L.left.h / 2 == c.H - kThumbRowFromBottom,
            what);
      // THUMB REACH (owner 2026-10-06): POWER and the rocker hang just under the
      // front pairs, not on the bottom edge ~65 mm away (past a thumb's reach).
      std::snprintf(what, sizeof what, "%s: POWER and the rocker hang under the front pairs", c.name);
      check(L.power.y == L.back.y + L.back.h + kRowClear && L.up.y == L.power.y &&
                L.down.y == L.power.y,
            what);
    } else {
      // THUMB REACH (owner 2026-10-06): each side's 2x2 block centered on the
      // safe area's height, where two-handed thumbs rest -- not at the bottom.
      const float blockMid = (L.back.y + (L.up.y + L.up.h)) / 2.0f;
      const float safeMid = (L.insetTop + (c.H - L.insetBottom)) / 2.0f;
      std::snprintf(what, sizeof what, "%s: the button blocks centered on the height", c.name);
      check(blockMid - safeMid < 0.5f && safeMid - blockMid < 0.5f, what);
    }
    // Zen: no pad, and the page gets the margins back.
    const Layout Z = layoutFor(c.W, c.H, c.sL, c.sR, c.sT, c.sB, true, c.isPad);
    std::snprintf(what, sizeof what, "%s: zen shows no pad", c.name);
    check(!Z.padShown, what);
    std::snprintf(what, sizeof what, "%s: zen's side insets are only the safe areas", c.name);
    check(Z.insetLeft < L.insetLeft && Z.insetRight < L.insetRight &&
              Z.insetLeft <= (c.sL > kEdgeMin ? c.sL : kEdgeMin) &&
              Z.insetRight <= (c.sR > kEdgeMin ? c.sR : kEdgeMin),
          what);
  }

  if (failures == 0) std::printf("turned_page_landscape: all checks passed\n");
  return failures == 0 ? 0 : 1;
}
