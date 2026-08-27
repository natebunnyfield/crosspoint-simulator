# Open work

Things to do that are not defects. Defects live in [BUGS.md](BUGS.md); this file
is for work that was asked for, or found and ruled worth doing, and has not
landed.

It exists so this repo has the same two trackers the firmware does — `BUGS.md`
for what is broken, `TODO.md` for what is merely owed. Before it existed, the
non-defect findings from the 2026-08-06 audit had nowhere to go and sat in a
plan file on a branch that was later deleted.

Format: `### [ST-NNN] Title` then what it is, why, and what "done" looks like.
An item leaves this file when it ships or when it is ruled out — not when it is
started.


## Where the rest of the work lives

Four trackers across two repos. Run the firmware repo's
`scripts/tracker-check.sh` for all of them with open counts and the next free
id — do not hand-pick an id.

| Tracker | Ids | Holds |
|---|---|---|
| `../crosspoint-reader/TODO.md` | `T-` | Firmware work that is owed |
| `../crosspoint-reader/BUGS.md` | `B-` | Firmware defects |
| **TODO.md** / [BUGS.md](BUGS.md) | `ST-` / `S-` | This repo, owed / broken |

Each tracker holds only its own prefix. Some items are paired across repos —
`ST-007` and the firmware's `T-016` are one job, and neither is done alone.

## What is on TestFlight

**build-110**, uploaded 2026-08-21 at 02:53. Simulator `2572cfe`+link-fixes
(`main` at the upload was the two-link-bug fix commit), firmware worktree at
`f1dbdb325` (1.5.4-BD — the settings reduction). 85.8 MB.

On top of build-109 it carries the ENTIRE phosphor mixer arc, none of which any
earlier build had: the page-color chip opening the mixer modal (tap or hold —
cycling is gone, superseded 2026-08-20), Blend/Parts/Cascade with premixes as
preset mixes, long-press loading fitted recipes, the persistence-banded shelf
sorted trail-then-hue, the tab-switch fix (browsing a tab no longer blanks the
page), and the desktop settings.json parity including the mix keys. Plus the
firmware settings reduction.

It took four deploy attempts, recorded here so the pattern is known: #1 died
because the shipping worktree was moved under the running archive; #2 died at
LINK on two mixer bugs invisible to desktop builds (extern "C" inside an
anonymous namespace; C-linkage declaration of the firmware's C++
crosspointRequestRender) — misdiagnosed first as a stale source set; #3 was
killed carrying the same code; #4 shipped with the fixes after arm64-ios
symbol-resolution verification. Anything only the iOS target compiles must be
verified by compiling AND resolving symbols for arm64-ios.

Firmware releases the same night: 1.5.3-BD (font work) and 1.5.4-BD (settings
reduction), both Latest in sequence on GitHub. Mac apps at build 111, all
three, at the reduction commit.

The build number comes from the highest `build-*` tag plus one, so tags are the
record — `git tag --list 'build-*' | sort -t- -k2 -n | tail -5`.

---

## Standing ruling: the iOS pad's side rocker stays

**2026-08-19.** `62b1ae5` retired the on-glass Up|Down rocker on every device
under "for ipad iphone and all devices, lose the side button ui". `409b3c9` put
it back the same day, on the owner's word, and it is not to be cut again without
a ruling that names THIS control specifically.

The confusion is worth keeping, because the two things sound identical and are
not:

| | What it is | Status |
|---|---|---|
| The firmware's side-button HINTS | drawn labels on the e-ink page, naming what the physical buttons do | removed, [T-011] |
| The iOS pad's side ROCKER | an actual touch control, and on iOS the pad is the only input there is | **stays** |

A ruling about the first is not a ruling about the second. Removing the second
is removing capability, which is keep-and-ask.

## OPEN

### [ST-011] Zen reading mode — BUILT 2026-08-19, gesture unverified off-device
**scope: ios display · asked 2026-08-19 · built the same day**

Owner: "a zen reader mode… toggleable by a single three finger tap on the panel.
in it the page background raises up to 0px above the top row of rocker buttons
(stick to 8px grid, and use rounded corners). in zen mode, tapping on the left
third of the panel moves back a page, and the right two thirds moves forward a
page, above the panel is power button, below the panel is Select button for the
right two thirds and Back button is left third."

**Built.** Three-finger tap toggles; the pad stops drawing AND stops
hit-testing; the page grows down to the top rocker row; its bottom corners are
rounded with the same n=2.8 squircle the top pair already uses; and the screen
becomes three zones — above the page POWER, the page itself left-third back /
right-two-thirds forward, below the page left-third Back / right-two-thirds
Select. Captures: `ios/mockups/zen-mode-2026-08-19.png` (on) and
`zen-mode-off-2026-08-19.png`.

**Two things the owner should know, because both are judgement calls made
without him:**

1. **0 px and the 8 pt grid cannot both hold.** On an iPhone 13 mini the top row
   starts 170 pt from the bottom, and 170 is not a multiple of 8. The band is
   CEILED to the grid, so the page stops **6 pt above** the row rather than
   exactly on it — erring on the side that never covers the row. He asked for
   both; the grid was the one he said to stick to.
2. **The page moves only 8 pt.** It already reached to within 8 pt of the top
   row, so raising it to the row buys almost nothing visually — what actually
   makes zen look different is the pad disappearing. Recorded because "raises
   up to" sounds like a bigger change than it is, and the capture shows it.

**The gesture's RULE is now tested; its DELIVERY still is not.** The decision —
what counts as a three-finger tap — is a pure state machine in
`ios/ZenGesture.h`, covered by `tests/zen_gesture_test.cpp` (10 checks, in
`run_all.sh`). The shim calls that same unit, so the tested path and the shipped
path are one thing.

**Extracting it immediately found a false positive that a code reading had
missed:** a hand ROLLING across the page — one finger lifting while two more
land — passes through a peak of three without ever being a three-finger tap, and
fired zen. The rule now counts fingers that took part, not just the peak, and a
four-finger roll is rejected. That bug was in the version already shipped in
build-106.

What remains unverifiable here is only whether iOS delivers three simultaneous
finger events to this watcher at all: `CROSSPOINT_SIM_INPUT_SCRIPT` cannot drive
it (its `TAP` feeds the FIRMWARE's touch state, not SDL finger events) and
`simctl` cannot inject multitouch. `CROSSPOINT_SIM_ZEN=1` starts in zen so the
layout can still be captured.

**Done looks like:** a three-finger tap on the page toggles zen on a real phone,
and each of the five zones does what it says.

**2026-08-27 — a SECOND way to toggle, and the collision it caused.** Owner:
*"holding down one finger longer than five seconds toggles zen and single finger
modes"* ("single finger mode" is his own term for not-zen, disambiguated
2026-08-22). Built as a second always-enabled `UILongPressGestureRecognizer`
beside the 3-finger tap, which STAYS. It collided with the zen long-press select
(0.75 s), because a five-second hold crosses 0.75 s on its way and one hold
wanted to fire two things. **Owner ruling the same day: select fires on the
LIFT** — 0.75 s to under 5 s selects on release, 5 s or more toggles under the
finger and the release is silent, exactly one action per hold. That knowingly
reverses the 2026-08-22 `.began` stock-feel ruling; the superseded note is kept
beside its replacement in `CrossPointZenRecognizers.mm`. Rule pure in
`ios/ZenHoldRouting.h`, truth-tabled in `tests/zen_hold_test.cpp` (in
`run_all.sh`). Still device-confirm only, for the same reason the rest of ST-011
is: UIKit recognizers live above SDL where no script and no `simctl` reaches.
Full account and the log lines to watch: `docs/zen-mode.md`.

**The gesture is live ANYWHERE on the glass, pad included — owner ruling
2026-08-27, asked and re-asked, same answer both times.** Out of zen the pad
carries real holds of its own (hold-to-sleep on POWER, page-turn autorepeat on
the rocker), so a hold that runs past five seconds there now does its pad job
AND toggles zen. That was put to him as a choice against a page-only hit-test
against the published `g_zenPanel`/`g_zenPaper` rects, which would have left
both pad holds untouched; he took the simple rule. So this is a KNOWN overlap
and not a defect to re-file: the ask said "holding down one finger" with no
location, and it is live with no location. If a pad hold ever needs protecting,
the fix is one hit-test in `ios/ZenHoldRouting.h` and nothing else moves.


### [ST-010] Fade the text away naturally over time after a page turn — SHIPPED 2026-08-17, unverified on the phone
**scope: ios display · asked 2026-08-17 · built 2026-08-17 · depth added 2026-08-18**

**Shipped as `Page Fade`**: Off / 15 s / 30 s / 1 min / 2 min / 5 min, stored as
the duration in seconds. **The default is 5 min as of 2026-08-19** — it shipped
Off, and the owner's own setting became the shipped default in build 100. The three design questions this entry raised,
answered:

- **Where does it stop?** At a floor, and any input re-energises it
  (`notePageInteraction`, hooked to both the SDL event path and the synthetic
  `injectButtonDown` path so headless runs behave like fingers). *Superseded in
  part 2026-08-18: the floor is still where it stops, but HOW FAR down that
  floor sits is now the owner's, down to nothing — see the depth setting below.*
- **Toward paper or toward grey?** **Paper** — a phosphor dying, which is what
  was asked. It falls out for free: the field behind the panel is already
  cleared to the paper tone, so alpha on the panel texture *is* a fade toward
  paper, correct in both polarities.
- **How long?** A setting rather than the phosphor's own figure. P7's minute is
  the only published number in range and hanging the feature off one row would
  have made it unreachable from every other palette.

**The floor is PER-PALETTE, and that is the part worth keeping.** 0.75 is the
deepest fade the phosphor rows tolerate (worst case Blue/P11 at 4.49:1, the AA
body-text bar). Solarized is exempt from this repo's 7:1 rule by design and
falls to **2.73:1** at that floor — the one page the fade would have made
unreadable. `pagefade::floorFor()` computes the floor from the pair on screen,
so a palette with no contrast to spend does not fade at all. Every fading row
measures ≥ 4.50:1; the non-fading one is left byte-identical.

**Measured** on a real page turn at 3x, dark Green CRT, fade 3 s: fresh ink
`(40,205,40)`, settled `(38,197,38)` — exactly the predicted 197 — and back to
`(46,235,46)` a tenth of a second after a button press.

**HOW FAR it fades is a SECOND setting, added 2026-08-18.** Owner: "create
another setting for Page Fade that includes current value and fully transparent
and three steps in between." The first setting is how LONG; this one is how
DEEP.

**Shipped as `Page Fade Depth`**, stored as `pageFadeDepthPercent` — the
percentage of the palette's legible floor that is KEPT, 100 (default) / 75 / 50
/ 25 / 0. The stored number is the proportion itself, not a row index, following
`pageFadeSeconds` and `beamPaintMs`, so the rows can be retuned without a
migration. Storing a proportion rather than an absolute alpha is what keeps the
per-palette adaptation alive at every step: `pagefade::floorFor()` is now
`legibleFloorFor() * depth/100`, so a low-contrast page still fades less far
than a high-contrast one at the same setting.

**RULING: below 100 the legibility guard is bypassed, by owner election.** The
whole reason `floorFor()` exists is that a flat 0.75 drops Solarized to 2.73:1;
the depth setting hands that back deliberately, and it is not a bug to be
clamped. The cost is measured rather than asserted — worst case across every
preset in both polarities, printed by `tests/page_fade_test.cpp`:

| Depth | Worst settled contrast | |
|---|---|---|
| 100 % | 4.50:1 (Red) | AA body text — **the default, unchanged** |
| 75 % | 2.73:1 (Solarized) | below AA body text, still readable |
| 50 % | 1.88:1 (Solarized) | a ghost of the page |
| 25 % | 1.28:1 (Blue) | barely present |
| 0 % | 1.00:1 | the page is gone; that is the option |

The override is written out where someone would go to undo it — the comment
above `pagefade::floorFor()` in [src/PageFade.h](src/PageFade.h), which names
the ruling and carries that table.

**Measured headlessly**, same rig as above (X3 desktop binary, 3x render, dark
Green CRT `33FF33` on `001A00`, fade 3 s, settled at 12 s), ink pixel per depth:

| Depth | Predicted ink | Measured | |
|---|---|---|---|
| 100 % | 197.8 | `(38,197,38)` | identical to the 2026-08-17 measurement |
| 75 % | 154.8 | `(28,154,28)` | |
| 50 % | 111.9 | `(19,112,19)` | |
| 25 % | 68.9 | `(9,69,9)` | |
| 0 % | 26 (= paper) | `(0,26,0)` | the ONLY color in the frame — 418 176 of 418 176 px |

With `CROSSPOINT_SIM_PAGE_FADE_DEPTH` unset the capture is **byte-identical** to
depth 100, which is the proof the default did not move.

**Found while building it:** the panel had been drawn TWICE per present since
the beam work (build 90). Invisible with opaque blending, which is why nothing
caught it, but it doubled the panel fill cost and made the fade composite
twice — 0.75 alpha rendering as 0.94. Removed.

`tests/page_fade_test.cpp` pins the curve, the settle, the loop stopping, and
the legibility of every palette's floor at the DEFAULT depth — plus, since
2026-08-18, that depth 100 leaves every palette's floor bit-for-bit where it
was, that each step down is strictly deeper, that Solarized (which does not fade
at all at the default) does fade when a deeper step is chosen, and that 0 is
alpha 0 rather than nearly-0.

Owner: "make an option to fade away text naturally over time after page turn".

DISTINCT FROM ST-009, and worth keeping apart. ST-009 fades the PREVIOUS page
out as the next one arrives -- a transition, over in a fraction of a second.
This is the CURRENT page fading while you read it: the text you are looking at
decays over seconds or minutes after the turn that drew it, the way a real
phosphor screen goes on dimming after the beam has moved on.

That makes it the first effect here that changes a page nobody is interacting
with, which is where the design questions are:

- **Where does it stop?** A page that fades to nothing is a page you cannot
  finish reading. Either it decays to a floor (still legible, just dimmer) or
  something re-energises it -- a tap, a scroll, the next turn.
- **Does it fade toward the paper or toward the ink?** Toward paper is a
  phosphor dying. Toward a mid grey is what tired e-ink actually looks like.
  They are different effects and only the first is what was asked for.
- **How long?** ST-009's trails run 40-660 ms from the published persistence.
  This is a different order of magnitude -- P7's yellow-green layer is over a
  minute, which is the only published figure in the right range and is a good
  argument for hanging this off P7 rather than off a global setting.

**Mechanism is already mostly built.** ST-009 put a ghost texture and an alpha
blend in `presentIfNeeded`; this needs the same blend applied to the LIVE
texture against the paper tone, on a much longer clock, plus something to keep
presenting while it decays.

**Do the cost fix first — see ST-009's note below.** A slow fade means a present
every frame for as long as the fade lasts, which is exactly the case where the
full-framebuffer memcmp gets expensive.

**Done looks like:** an option, off by default, where the page dims after a turn
to a legible floor and comes back on interaction; the floor and the clock both
stated; and a measurement of what it costs per frame on the phone.

### [ST-009] A glow-and-fade option for the CRT palettes — SHIPPED, unverified on the phone
**scope: ios display · asked 2026-08-17 · closed 2026-08-19**

**Both halves shipped, and the "option" half was ruled away rather than built.**
The GLOW is `SimulatorOverlay::setPanelGlow`, driven by `pollPanelGlow` straight
from the palette preset — there is no switch, by owner ruling 2026-08-17
("remove setting always have it on for crts"): a CRT palette is a claim that the
page is a tube, and a tube glows, so the two were never separate choices. Every
non-phosphor palette gets 0. The FADE shipped separately as ST-010's `Page Fade`.

Trail lengths come from `panelpalette::trailMsForPreset`, which is where the
crds reference below actually landed — one number per phosphor rather than one
global alpha.

Owner: "make an option for crts to have a pleasant glow and fade. (use crds web
phase scope for reference)".

**The reference, read rather than remembered.** `~/src/crds` already does this,
and does it the cheap way: instead of clearing the canvas each frame it fills it
with the palette background at a low alpha, so what was drawn before decays
toward the ground rather than vanishing.

| Where | What |
|---|---|
| `js/oldtime/crt-viz-helpers.js:221` | "of clearRect to produce phosphor afterglow" |
| `js/oldtime/viz-worker.js:862` | "Per-frame canvas alpha — controls trail length / phosphor afterglow" |
| `js/oldtime/viz-worker.js:968` | "Fade trail (CRT phosphor afterglow) — fade toward palette bg" |
| `js/oldtime/i18n.js:1078` | `lissajousPersistence` — the PHASE SCOPE's control. "Lower values keep a longer phosphor trail; higher values clear faster. Applied via `vizCtx.fillRect` with `crtBgFade(alpha)`. Default 0.18. Range 0.05 to 0.60." |
| `js/oldtime/i18n.js:1066` | `strobeArcsBgFade`, same mechanism, default 0.20 |

So the parameter is ONE number — per-frame alpha toward the paper tone — and
crds has already found the useful range (0.05–0.60) and the default (0.18) by
use. Do not re-derive them.

**CORRECTION, owner 2026-08-17: "this panel is eink on the eink device, but
oled on my phone."** The first version of this entry argued the fade would cost
continuous presents and therefore battery, treating the panel as e-ink
everywhere. That is wrong on the device this ships to. The X3 is e-ink; the
phone is an OLED running the harness's ~1 kHz loop already, and it is the phone
this feature is for. Presenting per frame while a trail decays is not a new cost
there -- it is what the harness does anyway.

Where it lives is still `presentIfNeeded` (`src/HalDisplay.cpp`) rather than the
framebuffer: the firmware renders a page and may not render again for minutes,
so the decay has to be a presentation-layer blend from the cached frame, the
same place the inversion re-convert already works from. That part of the first
version stands; the battery argument does not.

**SCOPE, owner: "glow is for entire ui/ux including page turns."** Not just a
palette change. Every transition the panel makes -- page turn, menu move,
selection, entering an activity -- decays into the next. On a phosphor screen
that is simply what happens when the beam repaints, so applying it to page turns
is the authentic case rather than the expensive edge case the first version
treated it as.

**THE SPEED IS PER PHOSPHOR, not one global number.** This is the part that
makes it more than a fade effect: each CRT row now carries its own published
persistence, so Green decays like P1 and Blue like P11, and two rows of the same
hue become genuinely different experiences.

Source, already encoded in `panelpalette::PresetInfo`: Patrick Jankowiak
(KD5OEI), *Cathode Ray Tube Phosphors Of Interest To The Experimenter*, rev.
20100226.1844, `labguysworld.com/crt_phosphor_research.pdf` — persistence there
is defined as **time to decay to 10% of peak**.

| Row | Phosphor | Published persistence | `decayMs` |
|---|---|---|---|
| CRT · Green | P1 | 20 ms | 20 |
| CRT · Amber | P3 | 13 ms | 13 |
| CRT · Gray | P4 | not over 7% of peak after 33 ms | 33 |
| CRT · Blue | P11 | 2 ms | 2 |
| CRT · Red | P22R | "Medium" (class only, no figure) | 0 |

`decayMs` is 0 where the table gives only a CLASS rather than a number, so the
glow has to fall back rather than have a figure invented for it. Do not fill
that in from memory.

**A real decay is 2–33 ms, which is one to two frames.** Taken literally the
effect would be invisible: at 60 Hz a 2 ms P11 trail is gone before the next
frame. So the honest design is a SCALED persistence -- the published figures set
the RATIO between rows (P4 is 16x P11), and one global multiplier makes the
family visible. crds's `lissajousPersistence` (default 0.18, range 0.05–0.60)
is the shape of that multiplier, not the value to copy.

**COST, found while building it and not yet fixed.** The "did the content
change?" test is a `memcmp` over the whole active framebuffer on every present.
At 3x that is 1584x2376x4 = ~15 MB compared per frame, plus a 15 MB copy on each
change -- and while a trail is alive it asks for a present every frame, so the
comparison runs at the loop rate. It is guarded behind the glow being ON, so it
costs nothing today, but it is the most likely reason the effect would feel bad
on a phone rather than not appear at all. The fix is to stop asking the pixels:
`refreshDisplay` already knows a new frame arrived, so a counter bumped there is
one integer compare instead of 15 MB. Do this before ST-010, which fades for far
longer and would pay it for the whole fade.

**Done looks like:** a setting, off by default, that on a CRT palette decays
every panel transition including page turns; the decay speed derived from the
row's own published persistence rather than one global constant; and the
scaling multiplier stated, since the real figures are one to two frames long.

### [ST-005] Move the panel clear of the keyboard, and mock up the larger devices
**scope: iOS layout · asked 2026-08-08 · WAITING ON AN iPAD SCREENSHOT**

**Status 2026-08-19: no longer blocked on mockup approval.** Everything this
entry's main complaint asked for has since been built, by rulings made after it
was written:

| Piece | Where it landed |
|---|---|
| Tablet panel rises to clear the keyboard | `CrossPointIOSShim.cpp:308` — tablet-only, and the comment says why: 1056x1584 at 2x still clears in the ~1900 px left after a 400 pt keyboard, so reserving the height costs no integer scale |
| Phone overlaps instead of pushing | Owner ruling 2026-08-10 — the same reservation on a phone costs one scale, about 40% of the text |
| Pad capsules on the screen edges | Fixed 2026-08-17; `layoutPadTablet` reads the horizontal safe area, floored at `kPadEdgeMin` 16 pt |

What is left is the two sub-items below — the pads sitting inside the panel's
content area, and the pair buried under the system keyboard — and both were
written about the iPad layout BEFORE those three fixes. **Nobody knows whether
they survived**, because the tablet pad and the keyboard lift are iOS-only and
nothing off-phone renders them.

**2026-08-19, from an attempt to produce that screenshot: the iPad SIMULATOR
renders this after all.** The entry says nothing off-phone renders the tablet pad
and the keyboard lift. That is half wrong, and the half that is right is narrower
than it looked:

* The app builds, installs and runs on an iPad simulator, is drivable with
  `CROSSPOINT_SIM_INPUT_SCRIPT` through `SIMCTL_CHILD_`, and screenshots with
  `xcrun simctl io <udid> screenshot`. `ios/mockups/ipad-create-note-2026-08-19.png`
  is a real 2064x2752 capture of Create Note on an iPad Pro 13 — the real code,
  the real tablet layout, not a drawing. Two of the three overlap areas (the pad
  capsules against the panel, and the panel's own margins) can be judged from it.
* **What it does NOT show is the iOS SYSTEM keyboard**, which is the condition
  this entry actually turns on. Create Note on the iPad draws the firmware's own
  key grid; the system keyboard never rose, with a hardware keyboard connected or
  disconnected, and a scripted `TAP` into the text area did not raise it either.
  So the keyboard-lift question is still unanswered, and the pad-under-keyboard
  overlap cannot be judged from this capture.

**The mechanism is now known, which was the open question.** The system keyboard
is not raised by focus or by typing: it is toggled by tapping the **keyboard
chip** — `hitKeyboardChip()` at `CrossPointIOSShim.cpp:1724`, reached from the
finger-up handler at `:1845`, which flips `setHostKeyboardVisible`. The chip is a
48 pt square, dead-centre horizontally, in the pad's bottom row
(`g_kbChip`, `:629`), and it only exists while `gpio.isTextEntryActive()`.

So a scripted capture needs a `TAP` landing inside that 48 pt square, and
guessing normalised coordinates did not hit it in four tries. The next attempt
should log `g_kbChip` once (or compute it from `lowerY` and `kCellH` in the same
function) and tap its centre, rather than guessing.

Two gotchas that cost attempts here: opening `Simulator.app` re-orients the
device to landscape, and **quitting Simulator.app shuts the booted device down**
mid-run, so a screenshot after it returns nothing.

The capture pipeline itself works and is repeatable:

```
cmake -B build/ios-app -G Xcode -DCMAKE_SYSTEM_NAME=iOS \
  -DCMAKE_OSX_SYSROOT=iphonesimulator -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DCROSSPOINT_FIRMWARE_DIR=$HOME/src/crosspoint-reader -DCROSSPOINT_BUILD_FIRMWARE=ON
cmake --build build/ios-app --config Debug --target CrossPointX3
xcrun simctl install <udid> build/ios-app/ios/Debug-iphonesimulator/CrossPointX3.app
SIMCTL_CHILD_CROSSPOINT_SIM_INPUT_SCRIPT='6000:RIGHT;...;10000:CONFIRM' \
  xcrun simctl launch --terminate-running-process <udid> com.natebunnyfield.crosspoint.x3
```

**Agreed close-out, owner 2026-08-19:** an iPad screenshot — portrait, Create
Note, keyboard up, dark, matching the 2026-08-08 evidence so the two compare
directly. Check the three overlap areas against it, fix whatever survived, close
with the screenshot as evidence. The alternatives were considered and declined:
closing on the code reading alone (leaves a live defect untracked if one
survived), and building fresh mockups for the larger devices (they would be
drawings of intended geometry rather than captures, which is the prose-instead-
of-pixels trap).

Two related pieces.

**1. The panel should sit clear of where a full keyboard lands, in portrait.**
Today the on-screen keyboard covers the bottom of the screen — the button pad
and the lower rows of the firmware's own grid — and the panel deliberately does
NOT move or rescale under it (`ios/README.md`, verified: panel geometry is
identical with and without the keyboard up). That was the right call when the
only thing that mattered was keeping the text field visible, and it is now the
wrong one: with Create Note and Claude raising a keyboard (crosspoint-reader
`daf014be`), typing is a first-class activity and the pad disappearing under the
keyboard is a real loss.

The mechanism already exists: `SimulatorOverlay::setBottomInset` reserves a
bottom band and top-aligns the panel above it, publishing `panelBottomPx()` for
the pad to anchor to. So this is reserving a keyboard-sized band rather than
inventing placement. Watch out for: the panel must not rescale on every
keyboard show/hide (that would re-lay-out the firmware's page and could churn
the reader), the read-aloud highlight geometry reads the same accessors and must
follow, and the keyboard height is not a constant — it varies by device, by
language, and with the predictive bar.

**Second owner screenshot (2026-08-09, iPad portrait, light, Create Note,
iOS keyboard up) pins THREE repeated overlap areas:**

1. **Side-button hint brackets ↔ editor text.** The left `^` and right `v`
   hint brackets are drawn at the panel edges mid-height, and the note's text
   lines run straight through the left bracket. The editor reserves a right
   gutter for hints (`NoteEditorActivity` sideGutter) but the brackets render
   at panel-relative positions that cross the text column on the iPad aspect.
2. **iOS system keyboard ↔ the firmware's own key grid.** The system keyboard
   covers the grid's bottom rows (the dimmed shapes behind the suggestion bar
   are the buried pads/rows) — the panel does not move up. This is the core
   ST-005 clearance problem; the owner's note text in the screenshot says it
   verbatim.
3. **Harness pad buttons ↔ panel content.** The two pale rounded pads float
   mid-screen inside the panel's content area (left/right, ~mid-height) in
   this layout instead of sitting in reserved chrome, and a second pair is
   buried under the system keyboard.

   **The edge half of this is FIXED, 2026-08-17.** On iPad Pro 13 portrait the
   outer capsules were not merely close to the edges, they were ON them:
   `cell` was `min(kOptimalSquare, margin / 2)`, so any margin tighter than
   2x60 pt -- every iPad in portrait -- made `cell` exactly `margin/2`, which
   collapsed `leftX` to 0 and put the right pair's outer edge exactly on `W`.
   A rounded display then clipped both. `layoutPadTablet` now reads the
   HORIZONTAL safe area (it only ever read the vertical) and floors it at
   `kPadEdgeMin` = 16 pt, because a portrait iPad reports 0 there -- no notch to
   describe -- while still having a corner radius. Logged geometry after:
   `W=1032 margin=120.0 edge=16.0 cell=52.0 leftX=16.0 rightPairEnd=1016.0
   (clearance L=16.0 R=16.0)`; before, that line would have read leftX=0.0 and
   rightPairEnd=1032.0. The cell gives up 60 -> 52 pt to buy the clearance.

   Still open in this item: the pads sitting inside the panel's content area at
   all, and the pair buried under the system keyboard.

**Evidence, from a real iPad in portrait, dark, keyboard up:**
[ios/mockups/keyboard-clearance/ipad-portrait-keyboard-dark.png](ios/mockups/keyboard-clearance/ipad-portrait-keyboard-dark.png)
(owner-supplied 2026-08-08, 2048x2732). It shows three things the simulator
testing missed:

- the iOS keyboard takes the bottom **25%** of the screen and **cuts off the
  bottom rows of the firmware's own key grid** — the OK / backspace row is
  simply gone, so the owner cannot reach the key that commits the entry;
- there is a large band of dead black space ABOVE the panel. The panel does not
  need to shrink to clear the keyboard on an iPad; it needs to move up;
- ~~the pad capsules are nearly invisible against a black field in dark mode~~
  — **ANSWERED 2026-08-16.** The outline was never reaching the color its own
  row advertised: `PadPalette`'s +/-9 rungs were field-RELATIVE deltas that
  clamped, and a fixed delta cannot reach a fixed endpoint from an arbitrary
  start. Measured, 18 of 20 palette halves had at least one end wrong, and High
  Contrast -- whose entire premise is the gamut ends -- painted `#040404` and
  `#EDEDED`. `toneChannelAt()` makes +/-9 absolute on any field, and the new
  Black & White preset is the default, so the dark-mode outline is now actually
  `#FFFFFF`. See `docs/pad-outline-black-and-white.md`. Still open, and now the
  narrower question: pure white FIGHTS a tinted dark palette (on Green CRT dark
  the capsules are the only non-phosphor element on screen) -- that is hue, not
  contrast, and it is an owner ruling.

**2. Mockups for iPhone Air and iPad Pro, for approval.**

**RULED 2026-08-17: landscape on iPad ONLY, and it is enabled.** The owner chose
to skip the mockups and iterate from what actually happens, so landscape was
turned on for both and tried. The phone was then turned back off, because what
it does is not a layout: rotated, an iPhone put the panel as a small tile in the
lower-left corner with the entire pad stacked as a vertical column down the right
edge, labels rotated 90 degrees, and most of the screen empty. The phone pad
reserves a BAND BELOW the panel, and in a landscape window that band becomes a
column beside it. The tablet path already puts controls in the side margins,
which is why landscape is coherent there and not here.

**Info.plist is NOT what decides this, and that cost a wrong first fix.**
`UISupportedInterfaceOrientations~ipad` is set (the App Store reads it), but SDL
answers UIKit's `supportedInterfaceOrientations` itself from
`UIKit_GetSupportedOrientations` (`SDL_uikitwindow.m`): with `SDL_HINT_ORIENTATIONS`
unset and a resizable window it returns `UIInterfaceOrientationMaskAll`, and it
falls back to the app's declared orientations only when the intersection with
them is EMPTY -- it never intersects. So a portrait-only plist rotated anyway,
measured on the handset. `simulator_main.cpp` now sets the hint from
`CrossPointAppearance_isPad()` BEFORE the window is created, and logs it:
`[orient] isPad=0 hint=Portrait`. Setting it later does not work either --
UIKit asks once as the window comes up.

Still open here: the iPad's landscape layout is enabled but not designed. The
panel sits toward the top-left with a large empty middle; the tablet pad math
was written for a portrait margin.

**The app was portrait-only until 2026-08-17** — `Info.plist.in` lists exactly
`UIInterfaceOrientationPortrait`, plus `UIRequiresFullScreen`. So landscape is
not a layout tweak; it is enabling an orientation the harness has never run in,
and the geometry contract (`.claude/PLAN-tts-read-aloud.md`) says "portrait
only" in as many words. Mock it before building it.

Cover: iPhone Air and iPad Pro, portrait and landscape, each with and without
the keyboard up, showing where the panel, the pad and the text field sit. An
iPad in landscape is mostly empty either side of a 528x792 panel — what goes
there is the actual design question, and "nothing" is a legitimate answer.

**How to present them for approval** (this has gone wrong before): put the
mockups INTO the decision surface — `AskUserQuestion` option previews carrying
the rendered image, or an inline widget — rather than sending a file chip or a
link and asking a question in the same turn. A sent link does not count as the
owner having seen it. If that is impossible, the turn that delivers the visual
ends with "say seen", and the decision questions come in a LATER turn.

**Close by:** approved mockups, then the portrait keyboard-clearance change;
landscape only if the mockups earn it.

### [ST-004] The page as UIAccessibility elements — SHIPPED, unverified on device
**scope: accessibility · asked 2026-08-08 · in build-41**

The panel is one opaque GPU texture, so VoiceOver, Speak Screen, Braille and
Switch Control saw nothing at all. [ios/CrossPointAccessibility.mm](ios/CrossPointAccessibility.mm)
publishes the page the read-aloud channel already carries as accessibility
elements over a transparent, non-interactive container above the SDL view.

**Per LINE, not per word.** Speak Screen reads elements in sequence and
concatenates them; per-word elements would put a pause after every word. Word
rects sharing a `y` are merged, and the label is the text slice from the first
to the last byte offset on that line.

**Not a second channel consumer** — the contract is one per build. The read-aloud
adapter's existing drain hands the page over, so there is still exactly one
reader on iOS.

**Independent of the read-aloud toggle.** Capture is wanted when the toggle is
on OR an assistive technology is running, but SPEECH still follows the toggle
alone: turning VoiceOver on must not start the app talking over it. The two
edges are tracked separately for that reason.

**Verified in the simulator:** 125–140 word rects collapse to 20 line elements
per page, labels are whole lines ("off exactly at midnight. The little"), frames
land in the right place in points, elements rebuild on every page turn, and the
overlay does not steal touches — the pad still opens a book.

**ROOT CAUSE, found 2026-08-08 after two wrong fixes: the container reported
zero children.** `CPAccessibilityOverlay` overrode `-accessibilityElements`,
which reads like the obvious thing and is silently useless — UIKit answers
assistive technology through the `UIAccessibilityContainer` methods, and UIView
derives those from the STORED property, not from an override of its getter. So
the container sat in the tree, front-most and correctly framed, reporting
`accessibilityElementCount = 0`. Every build said "no speakable content could be
found on the screen", with or without a page turn, because as far as iOS was
concerned there were no children.

Fixed by implementing `accessibilityElementCount` /
`accessibilityElementAtIndex:` / `indexOfAccessibilityElement:` explicitly AND
setting the stored property, so both paths work.

**What actually found it:** `CrossPointAccessibility_dumpTree()`, which walks
the hierarchy with the same public API an assistive technology uses. Before:
`CPAccessibilityOverlay children=0 … reachable labeled elements: 0`. After:
`children=22` with real book text on each. Two prior fixes were reasoned from
what UIKit "should" do and were both wrong; the traversal answered it in one
run. The dump is kept, one-shot per launch, because it is the fastest way to
tell on a device whether the page or the traversal is at fault.

**The earlier timing fix (below) was real but not the cause** — it was masking
nothing, since nothing was reachable either way.

**Build 42 reported "no speakable content could be found on the screen" —
first diagnosis, incomplete.** The container and the elements were fine; the
page never reached them. Capture was gated on (toggle OR assistive tech), and
the firmware publishes a page only when it RENDERS one — so switching Speak
Screen on while a page was already drawn flipped capture to wanted and then
published nothing until the next page turn. An owner who opens a book and then
swipes gets an empty container every time.

Three changes: capture is now UNCONDITIONAL on iOS (a display-list walk per
render is noise on a phone, and correctness beats it); the adapter republishes
its cached page whenever the container is empty but a page is in hand; and the
container is re-raised every frame, because accessibility traversal is
front-to-back and SDL rebuilds its views across a wake. Verified: elements now
build with ZERO page turns and with every assistive flag reading 0.

**NOT verified, and it cannot be here: Speak Screen does not exist in this
simulator.** Its Spoken Content pane offers only Speak Selection and
Pronunciations — no Speak Screen row — so `UIAccessibilityIsSpeakScreenEnabled()`
reads 0 and the two-finger gesture does nothing. This needs a phone.

**Close by, on the device:** Settings > Accessibility > Spoken Content > Speak
Screen on, open a book, two-finger swipe down from the top. The log line
`[A11Y] assistive tech: speakScreen=1` confirms detection; `[A11Y] N word rects
-> M line elements` confirms the page reached it. Worth judging at the same
time: whether per-line is the right granularity for VoiceOver's swipe-to-next,
or whether it should be per-word there and per-line for Speak Screen.

---

## Carried over from the firmware's tracker

`T-004` in the firmware's [TODO.md](../crosspoint-reader/TODO.md) — "make the
simulator stop lying about the device" — is simulator work tracked there because
that is where it was raised. Its substance is `S-001` in this repo's
[BUGS.md](BUGS.md): six places where the simulator reports the opposite of the
hardware, of which the 1 MB free-heap constant is the one that matters, because
every graceful-degradation path on a 380 KB device is unreachable in the only
pre-device gate the project has.

---

## DONE

### [ST-008] Moire in the selection dot pattern on iPhone Air — CLOSED 2026-08-19, confirmed gone on the phone

**CLOSED: the owner checked a list on a current build, 2026-08-19 — "nothing
shimmers."** The bench repro below never worked and is kept as a negative
result, but it no longer decides anything: the entry was only ever about whether
the shimmer was visible, and it is not.

**Attempted repro 2026-08-19, and it FAILED — recorded so nobody pays for this
twice.** Built at `CROSSPOINT_RENDER_SCALE=3`, captured the raw framebuffer with
`CROSSPOINT_SIM_WINDOW_SCALE=3` (a real 1584x2376 frame), and resampled the whole
thing to 1260x1890 — the iPhone Air's exact 0.7955 — once NEAREST and once
BILINEAR, which is precisely the choice `panelScaleModeFor` makes. Measured on
the most strongly dithered block in the frame, three ways:

| metric | source 3x | NEAREST @ 0.7955 | BILINEAR @ 0.7955 |
|---|---|---|---|
| row-mean sd | 9.53 | 9.70 | 8.96 |
| local-mean envelope, 5 px window | 3.70 | 3.62 | 2.86 |
| aliasing envelope, 24 px window | 5.58 | 4.62 | 4.13 |

Nothing resembling the 8.14-vs-1.55 this entry records. The third row is the
right instrument — a window of five dither periods averages the dither out and
leaves only the beat — and by it NEAREST adds no beat at all.

What is NOT yet ruled out, in order of likelihood: (1) the block measured is not
a `LightGray` fill. `GfxRenderer.h:30` makes LightGray a DITHER (`GfxRenderer.cpp:1223`
— "both patterns have period 2 in logical"), so it renders as 1-bit black/white
and a captured frame of it has two levels, which is what was found — but plenty
of other 1-bit content looks identical to that search. (2) The original figure
was measured on a different path or scale. (3) The figure is wrong.

Also worth knowing for the next attempt: with `CROSSPOINT_SIM_WINDOW_SCALE=3`,
light and dark captures came back BYTE-IDENTICAL, so the palette was not being
applied on that path. Whatever screen those captures were of, it was not the one
intended.

**The cheap close-out is the phone, not the lab.** If a list with a selected row
shows no shimmer on a current build, the entry closes whether or not the bench
repro is ever made to work.
**scope: ios display · reported 2026-08-15 · cause found and ruled 2026-08-15 · MERGED and shipped in build-80**

**Status, checked 2026-08-16:** the `ios-aa` mitigation is on `main` —
`panelScaleModeFor()` is [src/HalDisplay.cpp:154](src/HalDisplay.cpp:154), called
at `:978`, and the `[panel]` log line at `:1059` prints which filter is live. It
was already in `build-80`, so build 81 is not what carries it. What is still
owed is one look at an actual iPhone Air: the beat amplitude figures below are
measured, but measured off the framebuffer, not off the handset. Confirm the dot
pattern reads clean and delete this entry.

Owner report: the grey dot pattern that marks a selected item now shows moire
on an iPhone Air, with the question "is it being scaled differently today?"

**Yes, and today.** `39faa5d` ("feat(ios): render at 3x") changed the render
scale, and build 76 (2026-08-15) is the first TestFlight build carrying it. The
scale question is now answered by arithmetic rather than by measuring the
handset, because `presentIfNeeded`'s own quantisation decides it:

| Build | Framebuffer | Presented on an iPhone Air | Scale | Resample |
|---|---|---|---|---|
| 75 (2x) | 1056x1584 | 1056x1584 | **1.0000** | none, pixel-exact |
| 76 (3x) | 1584x2376 | 1260x1890 | **0.7955** | nearest, MINIFYING |

A 3x framebuffer is 1584 px wide and no iPhone is; the fit is width-bound, so
this holds for every plausible status-bar and pad band. **Build 75 could not
moire and build 76 must** -- that is the cheap A/B, settled without the phone.

The selection fill is `Color::LightGray`: ink where both LOGICAL coordinates are
even (`GfxRenderer.cpp:1041`), which at scale 3 is a 3x3 block on a 6-pixel
period. Point-sampling that at 1.2571 source px per screen px beats at a
**21-device-pixel period** (~1.16 mm on this display). Measured amplitude in the
local mean, levels out of 255:

**The ratio, computed 2026-08-15** (fell out of the keyboard-chip chevron work;
arithmetic only, not yet seen on the handset). It answers the first bullet, and
it is worse than "not integer" -- **2x and 3x are on opposite sides of 1.0**:

| Render scale | Framebuffer (portrait) | Presented scale on a 1260 px-wide phone | Dither cell |
|---|---|---|---|
| 2x | 1056 x 1584 | 1260/1056 = 1.19 -> **floored to exactly 1.0** | 2x2 device px, everywhere |
| 3x | 1584 x 2376 | 1260/1584 = **0.795**, quantised to 315/396 | 3x3 nominal, lands on 2 **or** 3 px |

Both numbers come from `presentIfNeeded`'s manual-placement branch
(`src/HalDisplay.cpp:788-860`), which is the branch the phone always takes
because the pad reserves a bottom band. `scale >= 1` floors to a whole number,
so 2x presents the panel **1:1 with no resampling at all** and the dither is
untouched. Below 1 there is no integer to floor to; it quantises to
`kPixelQuantum` and decimates by nearest-neighbour
(`kPanelScaleMode = SDL_SCALEMODE_NEAREST`).

**That is the moire.** The dither is drawn through `GfxRenderer::drawPixel`,
which paints a `RENDER_SCALE x RENDER_SCALE` block, so at 3x a dither cell is
3x3 device pixels. Decimating a 3 px cell by 0.795 gives 2.39 px -- so cells
land on 2 pixels or 3 depending on their phase, and the phase walks across the
screen. A regular grid with a walking period is exactly a beat pattern. At 2x
the cell is 2x2 and the scale is exactly 1.0, so every cell is identical and no
beat exists -- which predicts the build 75 / build 76 A/B the second bullet asks
for, without needing the handset to run it.

Note the trade-off this exposes: 3x genuinely improves TEXT (glyphs come from 3x
font tables and survive decimation as detail) while it necessarily destroys the
DITHER (a 1-cell-period pattern cannot survive a 0.795 resample). So "3x or 2x"
is not the only fork in the road -- drawing the selection fill at device
resolution instead of as logical blocks would let both win, and it is the same
gap the firmware repo filed as B-027.

| Filter at 0.7955 | Beat amplitude | Peak-to-peak |
|---|---|---|
| nearest (shipped) | 8.14 | 13.42 |
| bilinear | 1.55 | 3.29 |
| exact box (area) | 0.37 | 1.15 |
| 2x at 1:1 | 0.00 | 0.00 |

**Mitigation on branch `ios-aa`:** `panelScaleModeFor()` in `HalDisplay.cpp`
returns `SDL_SCALEMODE_LINEAR` below 1x and leaves `kPanelScaleMode` untouched at
or above it. Verified live on the iOS Simulator -- the `[panel]` log now ends
`filter linear`, and the same build with the branch reverted logs `filter
nearest` and differs by up to 113 levels per pixel on the Home selection tile.
The same change is what turns the panel's four grey levels into ~17,000 for
text, since every tone beyond four has to come from the 3x geometry (the
`.cpfont` glyph data is 2 bits per pixel, quantised at build time in
`fontconvert_sdcard.py:1053-1087`).

**RULED 2026-08-15: bilinear, and stop there.** The owner chose option B off
the published comparison. The exact box filter -- 11.7x beat reduction instead
of bilinear's 4.1x -- is DECLINED: it costs a per-present software pass over
2.4 M pixels, a second buffer, and a restructure of `presentIfNeeded`'s update
order, and the residual it removes is a 0.6% ripple. Do not re-propose it as an
improvement; it was measured, offered and turned down. Reopen only if a future
panel size lands the presented scale somewhere bilinear genuinely fails.

**The old note said "do not soften the pattern until the scale question is
answered."** It is answered, and nothing here softens the pattern: the
framebuffer is untouched and still a faithful four-level panel image. Only the
optics of showing it smaller than 1:1 change.

### [ST-007] The README no longer describes what this repo is — DONE 2026-08-16
**scope: docs · opened 2026-08-15 · both halves landed 2026-08-16**

**Done, and the paired `T-016` with it.** This README now opens on the two
toolchains rather than "a desktop simulator", carries the desktop/iOS split
table, and gained sections for the host tests (22, one command), the headless-QA
pointer, the color dials, the host-keyboard Return contract, and a full
opt-in table of the state the host cannot otherwise produce. The firmware README
gained Manage Files, Create Note, Claude (key path, model, transcript), the two
text-entry styles, Bluetooth keyboards and text antialiasing — every one checked
against the tree first — plus a section pointing at `SCOPE.md` and
`docs/fork-sync.md` for what was deliberately removed.

**Three stale claims were found and corrected rather than reworded:**

| Claim | Reality |
|---|---|
| "renders the e-ink display in an SDL2 window" | SDL3 on both toolchains since the iOS port |
| `CROSSPOINT_SIM_FREE_HEAP`, `CROSSPOINT_SIM_MAX_ALLOC_HEAP` | **neither exists** — grep of `src/` returns nothing. The real ones are `CROSSPOINT_SIM_HEAP` and `CROSSPOINT_SIM_HEAP_FREE` |
| "14 presets plus Custom" (also in CLAUDE.md) | 15 named presets; Sepia CRT and Blue CRT were appended 2026-08-16 |

The last one is the interesting failure: the *test's* sentinel had already been
walked to 16 and was correct, while two prose files still said 14. A number
repeated in three places drifts in the two that nothing executes.

**Original entry follows.**

This fork has grown well past its README: an iOS target (135 firmware TUs + 20
sim TUs for `arm64-apple-ios`), the read-aloud page channel, host keyboard text
entry with the software-keyboard show/hide contract, pad contrast presets, panel
palette and dark-mode re-present, `SimulatorOverlay` chrome, and Mac App Store +
TestFlight packaging. It is also now **0 behind upstream** and 299 ahead — by a
wide margin the most developed simulator in the ecosystem, which the README does
not say.

A README that describes a smaller project than the one it ships is the first
thing a new contributor reads, and every stale line costs someone a session.

Paired with **T-016** in the firmware repo — the owner asked for both READMEs to
match what their repos actually provide, so neither is done until both are.

Check each claim against the tree before keeping it; no claim without a grep.

**Done looks like:** the README describes the desktop app, the iOS target and
the headless QA channels as they exist today, and lists nothing that is not
there.


### [ST-006] iOS keyboard Return must insert a newline, not press Select — SHIPPED, unverified on the phone
**scope: iOS input · asked 2026-08-09 · fixed 2026-08-09 in `b15aec1`, entry never closed**

**Landed.** `src/TextEntryKeyRouting.h` answers the question once, for both the
event path and the level reads, and names this entry as the reason the
multi-line case exists. `tests/text_entry_enter_test.cpp` pins it and runs in
`tests/run_all.sh` (20/20 green on 2026-08-16). Return is a line break in the
note editor and Claude chat; a single-line field keeps it as Select, with the
host typist's commit on Cmd/Ctrl+Return.

**Still owed:** nobody has pressed Return on an actual iOS keyboard since. The
routing is shared with the desktop path rather than duplicated, so the fix is
the same code in both — but whether UIKit delivers `SDL_SCANCODE_RETURN` on
every keyboard layout is the one thing the host test cannot answer. Confirm on
the phone, then delete this entry.

**Original report follows.**

In Create Note with the iOS keyboard up, Return acts as the Select button
instead of inserting a line break. Mechanism: while text entry is active the
host-keyboard channel suppresses the scancode→button map for letters, but
Return still reaches BTN_CONFIRM. The channel already defines `\n` as the
commit byte for single-line fields (Wi-Fi password, owner name), so the fix is
to route Return INTO the typed-text channel as `\n` during text entry and let
the consumer decide: single-line fields keep treating it as commit, the
multi-line note editor inserts a real newline. Touches HalGPIO (simulator) and
NoteEditorActivity's typed-text handling (firmware). Owner report with
screenshot (iPad, 2026-08-09).


### [ST-001] `HalFrontlight` and `HalTiltSensor` mirror nothing — RULED KEEP
**scope: HAL surface · found 2026-08-06 · verified 2026-08-07**

`src/HalFrontlight.{h,cpp}` and `src/HalTiltSensor.{h,cpp}` have no counterpart
in the firmware's `lib/hal/`, which holds exactly six HAL classes — Clock,
Display, GPIO, PowerManager, Storage, System. Nothing in the firmware calls
either one, so neither is load-bearing today.

**They should not simply be deleted.** The frontlight is real X4 Pro hardware —
`CLAUDE.md` lists frontlight state among the X4 Pro capabilities, and the SDK
ships `freeink-sdk/libs/hardware/FrontlightManager/`. A simulator that drops it
will need it back the day the firmware grows a brightness control, and the
rebuild will be done by someone who does not know this file existed.

**Close by:** an owner ruling. Keeping them costs four small files; the honest
version of keeping them is a comment at the top of each saying it is a
placeholder ahead of the firmware, so the next reader does not mistake it for a
mirror of something that exists.

**Closed 2026-08-08 by doing what the close condition asked**: each file now
carries a header saying why it exists and that it is ruled KEEP, so the next
reader who greps for callers, finds none, and reaches for the delete key is
answered in place rather than having to find this file.

### [ST-002] The legacy web-server substitute looks dead and is not — RULED KEEP
**scope: cruft that must stay · found 2026-08-06 · verified 2026-08-07**

`src/CrossPointWebServer.cpp` is 1083 lines that current CrossPoint builds never
compile — they define `CROSSPOINT_SIMULATOR_PROJECT_WEBSERVER` and use the
firmware's own server against this library's `WebServer`/`WebSocketsServer`
shims instead.

Recorded here **because it reads as obvious cruft and is not.** The macro
disables only this reduced substitute; a downstream consumer that has not
adopted the firmware-owned server still links it. Deleting it breaks those
builds silently, at link time, in someone else's repo.

**Close by:** leave it, and add a header comment saying who still needs it.
Revisit only if every known consumer is confirmed to define the macro.

**Closed 2026-08-08 by doing what the close condition asked**: each file now
carries a header saying why it exists and that it is ruled KEEP, so the next
reader who greps for callers, finds none, and reaches for the delete key is
answered in place rather than having to find this file.


### [ST-003] Read-aloud TTS on the iOS harness — DONE
**scope: feature, two repos · asked 2026-08-07 · shipped 2026-08-08**

Apple speech reading the open book on the phone: page spoken in the owner's
Spoken Content voice, auto page-turn, per-word highlight, start from a tapped
word, behind a default-off toggle. Plan, contracts and gates:
[.claude/PLAN-tts-read-aloud.md](.claude/PLAN-tts-read-aloud.md).

WP-1 and WP-2 landed on Linux with gate G0; WP-3 (the AVSpeech adapter) had
never been compiled until 2026-08-08. It compiled and linked on the first real
build — the two defects were both GEOMETRY, and both were invisible everywhere
except on the phone:

- **The highlight scale used `HalDisplay::DISPLAY_HEIGHT`**, which is multiplied
  by `CROSSPOINT_RENDER_SCALE`. Desktop runs at 1x, where that constant equals
  the logical height and the code reads correct; iOS runs at 2x, so every
  highlight came out half-width at half the x-offset. `LOGICAL_HEIGHT` is the
  right constant. This is risk R5 in the plan, and it can only ever appear on
  the 2x build.
- **The firmware capture subtracted the font ascender from `PageLine::yPos`**,
  treating it as a baseline. It is the line's TOP (it is handed straight to
  `block->render()`), so every rect sat a full line high — the highlight lit the
  word above the one being spoken. On the first line it clamped to 0, which hid
  it. Measured against the rendered panel: yPos 0/54/90/126 put ink at
  15/68/104/137, i.e. `yPos + yOffset` plus a few px of leading.

The second one is now pinned by an ink-containment assertion in
`tests/test_read_aloud_capture.sh` — for each rect, the word's own ink band must
sit INSIDE the rect. An overlap test was tried first and was useless: a 26 px
shift against a 35 px line box still clips the word, so it passed on the broken
build.

**Verified on the iOS Simulator:** page spoken; hands-free across 8 consecutive
pages; manual page turn stops and re-speaks; BACK stops and clears; the Settings
toggle turns it off on the first frame after returning; tapping a word jumps to
it (`byteOff=543`, no page turn); the highlight sits exactly on the spoken word.

**NOT verified, and deliberately left so** (owner ruling 2026-08-08 — deferred
to the device pass rather than chased in the simulator):

| Gap | Why it is still open |
|---|---|
| Dark appearance highlight | reachable in the simulator; not run |
| A hyphen-split word lighting BOTH lines | reachable in the simulator; not run. The multi-rect path it exercises is covered by `read_aloud_core` host tests, but not on glass |
| End-of-book timeout | reachable in the simulator; not run |
| Ring/silent switch still audible | needs a physical phone — this is what `AVAudioSessionCategoryPlayback` is for (R6) |
| The owner's downloaded enhanced/Siri voice | needs a physical phone |

The first three are cheap and should ride along with the device pass, since the
phone has to come out for the last two regardless.
