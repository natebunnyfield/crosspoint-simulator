# Zen mode

Three-finger tap on the page toggles it — or a **one-finger hold of 0.75 s above
the paper**, either way in or out. The pad's chrome goes away and what is left is
a sheet of paper on black.

(The hold's history is worth a line: the owner asked for it on 2026-08-27 as
*"holding down one finger longer than three seconds toggles zen and single finger
modes"* — "single finger mode" is his own term for NOT-zen, disambiguated on
2026-08-22, *"remove the color button from single finger (not zen) mode ui"* —
and then replaced the duration split with a POSITION split the same day.)

**The two sections marked SUPERSEDED are a DATED RECORD of shapes that are gone,
not a description of the code.** They name `holdSelect:`, `holdToggle:`,
`release()`, `onToggleDeadline()`, `toggled_` and `g_holdSelfManaged`, and none
of those exists any more; the log lines they quote cannot be emitted. They are
kept because each records a real cost that was paid to learn something. The live
rule is "The gestures", "The bindings are Settings.app rows" and "The hold splits
by POSITION" above them, plus
[ios/GestureBindings.h](../ios/GestureBindings.h).

## The gestures

Every one of these is a native UIKit recognizer
([ios/CrossPointZenRecognizers.mm](../ios/CrossPointZenRecognizers.mm)) except
the one-finger deliberate tap, which is the SDL classifier
([ios/ZenVerbs.h](../ios/ZenVerbs.h)) — owner 2026-08-22, *"let's use apple for
swiping instead"* / *"please use apple for this so everything works as
expected."*

**WHAT EACH ONE DOES IS CONFIGURABLE from Settings.app** since T-025 (owner
2026-08-28) — see the next section. The table is the **shipped defaults**, which
are exactly what build 156 did.

| Gesture | Live in | Default action |
|---|---|---|
| **1-finger hold, 0.75 s, ABOVE the paper** | **zen AND not-zen** | **toggles zen, under the finger** |
| **3-finger tap** | **zen and not-zen** | **toggles zen** |
| 1-finger deliberate tap (≤28 px, ≤400 ms) | zen only | page forward (`BTN_RIGHT`) |
| 1-finger hold, 0.75 s, ON or BELOW the paper | zen only | Select (`BTN_CONFIRM`) |
| 1-finger swipe left / right | zen only | page forward / back |
| 2-finger swipe left / right | zen only | `BTN_DOWN` / `BTN_UP` |
| 2-finger swipe down / up | zen only | Select / Back |
| pinch / spread (on the lift) | zen only | `BTN_UP` / `BTN_DOWN` |
| 2-finger tap | zen only | Select |
| 4-finger tap | zen only | Power |
| shake | zen only | font family step |

The two always-on rows are always on for the same reason: they toggle **both
ways**, so they have to fire while zen is off. Everything else is enabled only
while zen is on (`CrossPointZenRecognizers_setEnabled`), or gated on the zen flag
where the gesture has no recognizer of its own (the shake catcher, the SDL tap,
and the hold's on- and below-the-paper zones).

The 3-finger tap **stays**. Two ways in is deliberate — removing it would be
removing capability nobody asked to lose.

**On `BTN_UP` / `BTN_DOWN` in that table:** this fork sets
`longPressButtonBehavior = FONT_SIZE_STEP`
(`../crosspoint-reader/src/CrossPointSettings.h:477`), which makes the side pair
the FONT controls inside a book —
`EpubReaderActivity.cpp:604` steps font SIZE on the release of a side button
that never crossed the hold threshold, and returns before `detectPageTurn` is
ever reached. So a gesture bound to Down makes text bigger in a book and scrolls
a screenful everywhere else; it turns pages only where the reader's long-press
setting is Off. That is what the Settings.app labels say, and it is why they do
not say "page forward".

## The bindings are Settings.app rows (T-025, owner 2026-08-28)

Owner: *"make gestures configureable in ios app settings. list all possible
gestures and give a well ordered, logically list of what they can be assigned
to."*

**Three groups, 18 rows.** The rule is
[ios/GestureBindings.h](../ios/GestureBindings.h) — pure, clock-free, free of
SDL and UIKit types, truth-tabled in `tests/gesture_bindings_test.cpp` for the
usual reason: every way it can be wrong is silent on a device and none of it can
be driven off-device, because UIKit's recognizers live above SDL where no input
script and no `simctl` can synthesize a touch.

| Group | Rows |
|---|---|
| **Above the Paper** | Tap · Swipe Left · Swipe Right · Hold |
| **Below the Paper** | Tap · Swipe Left · Swipe Right · Hold |
| **Multi-Finger** | Two-Finger Tap · Two-Finger Swipe Left / Right / Up / Down · Three-Finger Tap · Four-Finger Tap · Pinch · Spread · Shake |

**ON the paper is FIXED and is not in the settings at all** (owner ruling).
Reading gestures on the page stay reading gestures on the page: tap or swipe
left pages forward, swipe right pages back, hold selects. There is no row, no
key, and no prepared hook for it.

**What a row can be assigned to** is the firmware's button vocabulary, annotated
in the row label with what each does in a book and elsewhere: Back, Confirm,
Left, Right, Up, Down, Power — plus **Nothing**, plus the two host actions that
have no button and that a gesture already performed before this existed,
**Toggle Zen Mode** and **Next Reading Font**. Without those two the shipped
defaults could not have stated what the app already did.

**The owner's four rulings, implemented exactly:**

- **Zen may be left unbound.** No guard, no refusal, no warning. Clear every
  Toggle Zen Mode binding and zen is unreachable BY GESTURE, which is allowed —
  the configuration lives in iOS Settings.app, outside the reader, next to the
  Zen Mode switch itself, so it is always recoverable. The missing guard is a
  decision; `tests/gesture_bindings_test.cpp` pins it so nobody adds one back.
- **Two gestures may share one action.** No conflict detection, no moving, no UI
  refusal. Each gesture resolves independently and nothing knows what the others
  hold.
- **A gesture may be bound to Nothing.**
- **Zen scope is unchanged**, and it is a property of the GESTURE rather than of
  the action bound to it: you configure WHAT a gesture does, never WHEN. The two
  always-on gestures stay always-on whatever they hold, and binding a zen-only
  gesture to the toggle gets you only OUT of zen.

**The defaults reproduce build 156 gesture by gesture** — the property that
matters most, since there is no way to notice it has broken except by using the
app and feeling that something is wrong. A stored 0 (an unwritten key, or a
registration domain that never loaded because `Settings.bundle/Root.plist` was
unreadable) resolves to the default rather than to Nothing, so the worst a lost
store can do is render the app as it shipped rather than kill every gesture
including both ways into zen.

**A binding persists as an INTEGER**, so the action list APPENDS and never
inserts or re-points — the same discipline the palette presets follow, for the
same reason.

## The hold splits by POSITION, not duration (2026-08-27, final shape)

Owner: *"change long tap to only swap zen/singlefinger modes if tap held for
.75 sec above paper, if held below top of paper in zen mode, make it a select
after .75 before lift."*

| a 0.75 s one-finger hold landing... | zen off | zen on |
|---|---|---|
| **above the paper** (bezel / safe-area strip) | toggle INTO zen | toggle OUT of zen |
| **on or below the paper's top** | nothing | Select (`BTN_CONFIRM`) |

Both fire at 0.75 s **with the finger still down**. Nothing happens on the lift.

**T-025 (2026-08-28) split the lower half in two and made two of the three zones
assignable**; the table above is what the shipped defaults still produce, since
Hold-above defaults to the toggle and Hold-below to Select. It did NOT add a
second threshold, and must not.

"Above the paper" is the card's top edge — where black ends and paper begins
(`g_cardTopPx`), not the top of the text. "Below the paper" is past the sheet's
bottom edge (`g_zenRowTopPx`, the old top-rocker line — the same `line` the zen
painter cuts the sheet at, so the boundary the finger is judged against is the
edge the eye sees). Both are published by the layout pass in BOTH modes, which
is what makes the question answerable on a launch where zen has never been
entered.

Before the first layout the card top reads 0, and a 0 answers "everything is on
the paper" — the conservative direction, since a stray toggle is worse than a
missed one. The bottom edge has the same property before the first pass: a
bottom that is not BELOW the top makes `gesturebind::zoneFor` collapse to the
two-zone rule this section describes, so an unmeasured geometry cannot invent a
third zone out of a zero.

**The tablet is NOT that case, and an earlier draft of this paragraph said it
was.** `layoutPadTablet` publishes neither boundary, but `zenPaperBottomPx()`
falls back to the PANEL's bottom edge — the same fallback the zen painter uses —
so an iPad does get a below-the-paper zone from its first present, measured
against the page rather than a rocker row. Nothing follows from it at the shipped
defaults, since every Below binding resolves to what On the paper does.

### Why this shape, after two others in one day

1. A **5 s** hold toggled anywhere; a **0.75 s** hold selected in zen. A hold on
   its way to 5 s crosses 0.75 s, so one gesture wanted to fire two things.
2. The select moved to the **lift** so a long hold could suppress it. Correct,
   but it cost the stock iOS long-press feel the owner had asked for on
   2026-08-22 — the action no longer happened under the finger.
3. **Splitting by position removes the collision at its root.** The two actions
   can share a threshold because they can never both apply: a touch is either
   above the paper or it is not. So the select goes back to firing while held,
   and the 5 s wait is gone as well.

### What that deleted

- **One recognizer instead of two.** `g_lpHold`, always enabled.
- **The simultaneity delegate.** It existed only because UIKit's
  `-canPreventGestureRecognizer:` defaults to YES, so the shorter press stopped
  the longer one ever recognizing. With one hold recognizer there is no pair to
  exempt.
- **All the lift bookkeeping** — no release action, no elapsed-time arithmetic,
  no boot-tick underflow to fail closed against.

### The one thing carried forward deliberately

The select is gated on `g_zenOn` **in the action**, not by disabling the
recognizer. That is the fix for the defect shipped earlier the same day: the
select used to live on a zen-only recognizer which also owned the shared
tracker's lifecycle, so out of zen the tracker went stale and the toggle died in
one mode. Gating the ACTION rather than the RECOGNIZER makes that class of bug
unavailable.

## SUPERSEDED — the collision on one hold, and how it was ruled (2026-08-27)

**Nothing below this line describes the current code.** The symbols it names are
gone; see the banner at the top of this file.

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

## SUPERSEDED — the hold was dead in single-finger mode, and why (2026-08-27)

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
autorepeat on the rocker. So a pad hold that lands above the paper and runs past
0.75 s does its pad job *and* toggles zen. (The threshold was three seconds when
this was ruled; the ruling is about the absence of a gate, and it survived the
retune and the position split unchanged.) This was put to the owner as a choice — a page-only
gate, hit-testing the landing point against the already-published `g_zenPanel` /
`g_zenPaper` rects, would have left both pad holds exactly as they were. He was
asked, and asked again on the same day, and chose the ungated rule both times.

So the overlap is **ruled, not overlooked**, and it should not be re-filed as a
defect. The ask was *"holding down one finger"* with no location named, and the
recognizer is live with no location — what the landing point decides is WHICH
BINDING answers, not whether the gesture exists. Should a pad hold ever need
protecting, the whole fix is one hit-test in `ios/GestureBindings.h`; nothing
else moves, because the rule already takes the landing point. (Since T-025 there
is also a milder answer that needs no code: point the Above-the-Paper Hold row at
Nothing.)

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
