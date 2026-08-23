# Zen mode

Three-finger tap on the page toggles it. The pad's chrome goes away and what is
left is a sheet of paper on black.

## The layout, and why each edge is where it is

Measured on an iPhone Air (1260x2736, 8 pt grid = 24 device px), home screen,
`CROSSPOINT_SIM_ZEN=1`:

```
paper   y 204 .. 1967      (bottom edge on grid cell 82)
ink     y 288 .. 1827
TOP     ink->paper   84 px = 3.50 cells
BOTTOM  ink->paper  141 px = 5.88 cells
```

**The page is never resized** (owner ruling 2026-08-19, *"do not resize with
zen"*). Zen changes only what is PAINTED around the page: the fit is a
fractional minification of the 3x framebuffer, so re-fitting the panel would
quietly change how every pixel of the text was resampled — measured 0.6212 ->
0.6818 the one time it was tried.

**Below the paper is black** (ruling 2026-08-19). Not decoration: the pad's
field is the same tone as the page's paper by design — measured 215,233,211
against 215,233,211 on an iPhone Air — so without the black there is no visible
edge anywhere on the screen and the sheet has nothing to have corners on. On an
OLED it is also the darkest a night page can be.

**The sheet BLEEDS TO THE GLASS.** It is not a card floating on black. Owner
ruling 2026-08-20, picked off a side-by-side of two live renders rather than a
description: the bounded version spent 204 px of the 1260 on margin and read as
a smaller object sitting on a screen, where the full-bleed one reads as the
screen being paper. The page itself is 1056 px wide either way — the page is
never resized in zen — so this is purely what the 204 px either side is painted
with, and it is paper. Black is for below the line only.

**The paper runs FOUR CELLS PAST the old top-rocker line** (ruling 2026-08-20).
The first version stopped at that line, which left 84 px of paper above the
first ink against 45 px below the last: bottom-heavy the wrong way, and the
sheet read as sliding off the bottom of the screen. The bottom band cannot be
fixed by moving that edge up, because up is where the ink is. Four CELLS rather
than 96 px so the rule holds on any device — the grid is in points, so it is 32
pt everywhere and lands on the grid by construction. Clamped so it never runs
under the home indicator.

## The corners, which took three attempts

The bottom pair has to be rounded or a raised sheet reads as a slab with two
sharp corners under two soft ones. Same curve as the top pair — `kCornerExponent
2.8`, off Apple's display mask — because the two pairs sit on one rectangle and
any difference is visible precisely there.

**Same RADIUS too, 8 pt, `kPaperCornerPt`** (owner ruling 2026-08-20: *"use the
bottom corner radius on the top of the paper too"*). The top pair used to ask
UIKit for the display's own radius — ~55 pt — so the card's corners ran with the
glass. On one rectangle that is a 165 px curve at the top against a 24 px curve
at the bottom, which reads as two different objects rather than as a sheet.
`CrossPointAppearance_displayCornerRadius` stays available; nothing calls it
today.

**Then the radius stopped being a constant** (owner 2026-08-22: *"use the circle
that determines the height gap between paper and text to make the corner radius
of the paper"*). `layoutPad` publishes the visual paper→ink gap as
`g_paperGapPx` and the corner is struck with the same circle: radius = half the
gap. On an iPhone Air that is 105.8 px against the 24 px constant it replaced.
The 8 pt constant survives only as the pre-first-placement fallback, which is
one boot pass — the `[bezel]` line logs which of the two is live.

**And it is not gated on zen** (owner 2026-08-23: *"paper bug: make top corners
of not zen mode match top corner radius of zen mode"*). It was: `paintTopBezel`
read the module only when `g_zen` was set, so the same card was struck with a
106 px curve in zen and a 24 px one out of it. The module is mode-independent by
construction — it is derived from the card top, the panel height and the
firmware's published ink insets, and zen changes none of them (the no-resize
ruling) — so the gate was suppressing a number that was already correct and
already being computed. Measured on an iPhone Air, top-left inset at the card's
first row, before and after:

| | non-zen | zen |
|---|---|---|
| before | 24 px | 106 px |
| after | 106 px | 106 px |

Light and dark alike, and the full 120-row inset profile is identical between
the two modes rather than merely equal at row 0. The panel's fit is untouched:
`[panel] out 1260x2736 px, scale 1.0000, panel 1056x1584 at 102,256` either
side of the change.

**The BOTTOM pair is zen-only, and stays that way.** `paintBottomFillets` is
called from the zen branch alone. Out of zen there is no bottom edge to round:
the pad's field is the paper tone and runs to the bottom of the glass, where the
display's own mask is the only curve. Measured in zen, the bottom pair's profile
is the top pair's, to the pixel.

Verified both pairs on an iPhone Air, insets from each side by row (at the 8 pt
constant, i.e. the fallback the table was measured at):

| row from edge | top pair | bottom pair |
|---|---|---|
| 0 | 24 | 24 |
| 1 | 13 | 13 |
| 2 | 10 | 10 |
| 3 | 8 | 8 |
| 4 | 7 | 7 |
| 5 | 6 | 6 |

Two ways to get this wrong, both shipped and both caught in a screenshot:

* **Cutting them out of the page's rect.** The page is 1056 px wide on a 1260 px
  screen. Because field and paper are the same tone, what the eye reads as one
  sheet runs edge to edge — so cutting at the page's edges put two 24 px notches
  at x=102 and x=1158, mid-field, eight pixels of nothing in the middle of the
  paper. **The corners that exist are the SCREEN's.**
* **Cutting them at the panel's bottom while the paper CONTRACTS.** With the
  line above the page's own bottom edge, the fillets landed inside the black
  band where nothing could see them, and what read as the paper's edge was the
  band's straight top. `g_zenPaper.h` must follow the line in BOTH directions,
  not just when paper is added.

Both are a superellipse, symmetric to the pixel on both sides.

## Checking it without a device

`CROSSPOINT_SIM_ZEN=1` forces zen at launch. It exists because the gesture
cannot be injected off-device: `CROSSPOINT_SIM_INPUT_SCRIPT`'s TAP feeds the
FIRMWARE's touch state, not SDL finger events, and `simctl` cannot inject
multi-touch either.

```bash
cmake -B build-simsdk -G Xcode -DCMAKE_SYSTEM_NAME=iOS \
  -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_SYSROOT=iphonesimulator \
  -DCROSSPOINT_FIRMWARE_DIR="$HOME/src/crosspoint-reader" \
  -DCROSSPOINT_BUILD_FIRMWARE=ON \
  -DCROSSPOINT_IOS_SEED_FONTS_DIR="$PWD/ios/seedfonts"
xcodebuild -project build-simsdk/crosspoint_simulator.xcodeproj \
  -scheme CrossPointX3 -configuration Release -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone Air (zen)' build
xcrun simctl install "iPhone Air (zen)" build-simsdk/ios/Release-iphonesimulator/CrossPointX3.app
SIMCTL_CHILD_CROSSPOINT_SIM_ZEN=1 xcrun simctl launch "iPhone Air (zen)" com.natebunnyfield.crosspoint.x3
xcrun simctl io "iPhone Air (zen)" screenshot zen.png
```

The `[zen]` log line reports the geometry every layout:
`[zen] on band=256.3pt topRowY=629.3pt paperTo=1968px panelH=1584px panelW=1056px`.
