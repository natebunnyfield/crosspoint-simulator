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

Verified both pairs on an iPhone Air, insets from each side by row:

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
