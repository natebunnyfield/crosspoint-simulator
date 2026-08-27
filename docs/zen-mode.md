# Zen mode

Three-finger tap on the page toggles it — or a **one-finger hold of five
seconds**, either way in or out (owner 2026-08-27, verbatim: *"holding down one
finger longer than three seconds toggles zen and single finger modes."* "Single
finger mode" is his own term for NOT-zen; he disambiguated it on 2026-08-22,
*"remove the color button from single finger (not zen) mode ui"*). The pad's
chrome goes away and what is left is a sheet of paper on black.

## The gestures

Every one of these is a native UIKit recognizer
([ios/CrossPointZenRecognizers.mm](../ios/CrossPointZenRecognizers.mm)) except
the one-finger deliberate tap, which is the SDL classifier
([ios/ZenVerbs.h](../ios/ZenVerbs.h)) — owner 2026-08-22, *"let's use apple for
swiping instead"* / *"please use apple for this so everything works as
expected."*

| Gesture | Live in | Does |
|---|---|---|
| **1-finger hold, 3 s** | **zen AND not-zen** | **toggles zen, at the 3 s mark, under the finger** |
| 3-finger tap | zen and not-zen | toggles zen |
| 1-finger deliberate tap (≤28 px, ≤400 ms) | zen only | page forward |
| 1-finger hold, 0.75 s ≤ hold < 3 s | zen only | Select (`BTN_CONFIRM`) **on the lift** |
| 1-finger swipe left / right | zen only | page forward / back |
| 2-finger swipe left / right | zen only | font +1 / −1 |
| 2-finger swipe down / up | zen only | Select / Back |
| pinch / spread (on the lift) | zen only | font −1 / +1 |
| 2-finger tap | zen only | Select |
| 4-finger tap | zen only | Power |
| shake | zen only | font family step |

The two always-on rows are always on for the same reason: they toggle **both
ways**, so they have to fire while zen is off. Everything else is enabled only
while zen is on (`CrossPointZenRecognizers_setEnabled`).

The 3-finger tap **stays**. Two ways in is deliberate — removing it would be
removing capability nobody asked to lose.

## The collision on one hold, and how it was ruled (2026-08-27)

The three-second hold and the zen long-press select are the **same physical
gesture** with two thresholds. A hold on its way to three seconds crosses 0.75 s,
so in zen one hold wanted to fire two things: a Select and then a toggle.

**Owner ruling, 2026-08-27: the select fires on the LIFT, not while held.**

| Total hold | Fires |
|---|---|
| < 0.75 s | nothing here (that is the deliberate tap's window, ≤400 ms) |
| 0.75 s .. < 3 s | **Select**, on the lift |
| ≥ 3 s | **zen toggle**, at the 3 s mark under the finger; the lift is silent |

Exactly one action per hold, never both. What a reader feels: hold past five
seconds and zen flips under the finger, and letting go does nothing more.

**This reverses a device-feel ruling knowingly.** On 2026-08-22 the select was
put on `.began` precisely because that is the stock iOS long-press feel
(*"please use apple for this so everything works as expected"*). It cannot
survive beside a longer hold on the same finger, and the owner accepted the cost
when it was presented. The superseded note is kept beside its replacement in
`CrossPointZenRecognizers.mm` rather than deleted.

**The 0.75 s threshold did not move.** It was itself set from the device
(2026-08-22: *"long tap select is too fast. make at least 1.5x longer"*). Only
*when* it fires changed.

## The hold was dead in single-finger mode, and why (2026-08-27)

Owner, from the device: *"currently it does not work in single finger mode."*
Reported hours after it shipped in build 147, and correct.

**The mechanism.** `zenhold::Hold` is one tracker shared by both hold
recognizers, but only `holdSelect:` ever drove its lifecycle — and that
recognizer is **zen-only**. Out of zen nothing called `begin()` and nothing
called `release()`, so the tracker kept whatever the last zen hold left in it.
`onToggleDeadline()` answers `None` when either `poisoned_` or `toggled_` is
set, and out of zen neither could ever be cleared. Two ordinary sequences latch
it permanently:

- exit zen with the **3-finger tap** — no finger ever lifts through the select
  recognizer, so `release()` never runs and `toggled_` stays true;
- let any zen hold get a **second finger** on it — `poisoned_` stays true.

From that moment the hold worked in zen and did nothing at all out of it, which
is exactly the shape of the report.

**What makes it interesting** is that the code had already reasoned about this
and stopped one step short. `release()` carries a comment saying an idle tracker
must never carry a previous hold's poison, *because the toggle deadline is asked
on holds this tracker never saw begin*. That is the right analysis. What it
missed is that out of zen `release()` is never reached either, so the cleaning
it describes never runs. The adversarial pass also cleared this specific claim —
its clean-item 2 asserted the toggle still fires out of zen — so two independent
readers accepted a false statement about the one mode neither could exercise.

**The fix.** When zen is off, `holdToggle:` owns the whole lifecycle: `begin()`
on `.began`, `release()` on the lift. `g_holdSelfManaged` latches that ownership
**at `.began` and is not re-read**, because toggling flips `g_zenOn` under the
gesture and the `.ended` that follows must go to whoever took the `.began`. In
zen the branch does nothing and `holdSelect:` keeps the tracker as before.

**What is provable off-device** is the property the fix leans on — that
`begin()` scrubs an inherited poison and an inherited toggle latch — and
`tests/zen_hold_test.cpp` pins both, verified by mutation: deleting either
scrub from `begin()` fails exactly one named check. The recognizer wiring itself
is UIKit and reaches no host test, so the fix is device-confirm only. Watch for
`[zen] hold-toggle fired (tracker self-managed, zen off)`.

## Where the hold is live: everywhere, pad included (2026-08-27)

The hold is not hit-tested. It fires wherever the finger lands — the page, the
surround, and the **button pad**.

Out of zen the pad carries holds of its own: hold-to-sleep on POWER, page-turn
autorepeat on the rocker. So a pad hold that runs past three seconds now does its
pad job *and* toggles zen. This was put to the owner as a choice — a page-only
gate, hit-testing the landing point against the already-published `g_zenPanel` /
`g_zenPaper` rects, would have left both pad holds exactly as they were. He was
asked, and asked again on the same day, and chose the ungated rule both times.

So the overlap is **ruled, not overlooked**, and it should not be re-filed as a
defect. The ask was *"holding down one finger"* with no location named, and the
gesture is live with no location. Should a pad hold ever need protecting, the
whole fix is one hit-test in `ios/ZenHoldRouting.h`; nothing else moves, because
the routing rule already takes the landing point.

**Cancelled and multi-finger holds fire neither.** A touch iOS takes for its own
gesture, or a second finger landing mid-hold, poisons the whole hold — the same
discipline `ZenVerbs.h` applies to a hand rolling across the glass.

The rule is pure and lives in
[ios/ZenHoldRouting.h](../ios/ZenHoldRouting.h), truth-tabled in
`tests/zen_hold_test.cpp` (in `run_all.sh`). It is a header rather than an `if`
in the recognizer action because **both inversions are silent**: a select that
stops firing reads as a gesture the phone did not deliver, and a select that
fires alongside the toggle reads as the toggle misfiring. Same precedent as
`src/TextEntryKeyRouting.h`, which exists because both inversions of the
Return-key rule shipped as bugs.

**Two recognizers, and they must be allowed to recognize together.**
`UIGestureRecognizer`'s default `-canPreventGestureRecognizer:` is `YES`, so the
0.75 s recognizer reaching `.began` would otherwise prevent the 3 s one from
ever recognizing — in zen the toggle would simply be dead. A delegate grants
simultaneity to **that pair only**, named explicitly so no other pair's
exclusivity changes by accident.

**Movement allowance is Apple's default (10 pt) on both**, and that is the first
thing to suspect if a device report says the three-second hold does not fire:
`allowableMovement` applies only *until* a long press is recognized, so a finger
that drifts past 10 pt inside the three seconds fails the recognizer. It was left
at the default because 10 pt on the phone's 3x display scale is 30 device px, which
is the 28 px slop `ZenVerbs.h` already calls a deliberate touch — the repo's own
answer to the same question — and because inventing a number here would be
inventing device feel.

### Status: SHIPPED — UNCONFIRMED on device

UIKit recognizers live above SDL, so no `CROSSPOINT_SIM_INPUT_SCRIPT` run and no
`simctl` can drive them. What is proven off-device is the routing (the truth
table) and that the wiring compiles and attaches. **What to watch in the log:**

```
[zen] recognizers attached (zen-only: 6 swipes, pinch, 2-tap, 4-tap, 1-finger
      hold 0.75 s -> select ON LIFT; always on: 3-tap toggle, 1-finger hold
      3.0 s -> toggle; shake catcher installed)
[zen] toggle -> on (3 s one-finger hold)      <- the three-second hold worked
[zen] toggle -> off (3-finger tap)            <- the old gesture still works
[zen] one-finger hold 1240 ms -> select       <- a short hold selects on lift
[zen] one-finger hold 6100 ms -> none         <- and a long one does not
[zen] one-finger hold cancelled -> nothing
```

A three-second hold that produces **no** `[zen]` line at all means the recognizer
never recognized — drift past `allowableMovement` is the leading suspect. A
`[zen] toggle` line with a `[zen] one-finger hold ... -> select` beside it for
the same hold would mean the routing broke, which is what the truth table exists
to prevent.

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
