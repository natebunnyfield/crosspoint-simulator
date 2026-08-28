# Known bugs and open defects — simulator

Running list for this repo, in the same format the firmware's `BUGS.md` uses.

It exists because simulator defects had nowhere to live. GitHub issues are
disabled on `natebunnyfield/crosspoint-simulator`, upstream
`crosspoint-reader/crosspoint-simulator` carries none, and the firmware's
`BUGS.md` is for firmware — so simulator findings survived only in `CLAUDE.md`
prose and agent memory. That is how `CLAUDE.md` accumulated the confidently
wrong claims it has since had to correct.

IDs are `S-NNN` so they never collide with the firmware's `B-NNN`.

A bug leaves OPEN only when there is evidence it is fixed. A passing build is
not evidence for anything you cannot observe headlessly — see the device-feel
rule in the project guide.

Format: `**[id] Title** — severity · where · status`, then what breaks, how it
was found, and what closing it requires.


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

---

## OPEN

### [S-027] Returning from a video call leaves the screen blank for a long time — FIXED 2026-08-28, unconfirmed on device
**severity: high (looks like a hang) · scope: iOS present · filed 2026-08-27 from the device · fixed 2026-08-28**

Owner: *"while on a video call, returning to app takes a while to get out of
blank screen."*

Unverified mechanism, written down so the next session starts from a hypothesis
rather than from zero. An e-ink firmware presents RARELY — that is the whole
shape of this codebase — so anything that loses the drawable and then waits for
the firmware's next natural render will show blank for as long as the reader
happens to sit still, which on a page of text is unbounded. A video call is the
strong case for it: iOS resizes for the call banner, and the app is a
`SDL_uikitmetalview` whose layer is re-created.

Where to look first, in order:
- whether `UIApplicationDidBecomeActiveNotification` (or SDL's
  `SDL_EVENT_WILL_ENTER_FOREGROUND` / `SDL_EVENT_DID_ENTER_FOREGROUND`) reaches
  anything that calls `SimulatorOverlay::requestPresent()`. This repo has been
  bitten by exactly this three times already — the keyboard height, the palette
  change, and the appearance flip all stored new state and presented nothing.
- whether the panel texture survives the layer re-creation, or whether it needs
  re-uploading from `pixelBuf` rather than re-presenting a dead texture.
- the call banner changes the safe-area insets, so the zen/pad layout recomputes;
  if that path early-returns on an unchanged inset it may also skip the present.

**Do not fix this by polling.** The fix is a present on the foreground edge, not
a timer.

## The filed hypothesis was WRONG, and the right answer was next door

The guess above — that nothing calls `requestPresent()` on the foreground edge —
is false. `SDL_EVENT_DID_ENTER_FOREGROUND` has both a present AND a
**settle window**: `repaintAfterForeground()` re-asks every 200 ms for 2 s,
with constants measured against timed screenshots, because a present issued
while the surface is still settling returns success and is then DISCARDED on
Metal. That reasoning was already written down; what was missing is who else
needs it.

**A video call never backgrounds the app.** The call banner RESIZES the window —
once when it appears, once when it goes — and `SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED`
asked for exactly ONE present each time. One present is the thing the
foreground path already knew was not enough. An app that draws only when the
panel changes has no second frame coming, so the discarded frame is the only
frame there was, and the stale or blank image stood until something else forced
a redraw.

So: same failure, same fix, previously reachable from only one of its two
causes. Both now call `armSettleRepaint()`. The budget is reused rather than
re-derived — it was measured for the foreground case and the size case has no
measurements of its own, so inventing a second number would be inventing device
feel.

Device-confirm only: no host reproduces a Metal surface discarding a present.

### [S-026] The bottom-right rocker flashes when a DIFFERENT button is pressed
**severity: medium (visible, wrong) · scope: iOS pad overlay · filed 2026-08-27 from the device · NOT YET REPRODUCED**

Owner: *"bottom right rocker switch is flashing on a subsequent press of another
button."*

So pressing button A repaints button B's pressed state. Two candidates, both
cheap to distinguish once reproduced:

1. **A stale pressed-index.** The pad draws a highlight for whichever index it
   believes is down; if the release path clears the *drawn* state later than it
   clears the *logical* state (or not at all), the next press repaints the
   previous button for one frame. The bottom-right cell being the one that shows
   it is a hint: it may simply be the last cell in the draw order.
2. **The synthetic-tap path.** `queueButtonTap` schedules a press/release pair
   inside `update()`; a tap whose release lands in a later frame than the next
   press begins would overlap two highlights.

Note this is a PAD-OVERLAY bug, not a firmware one — the device has physical
buttons and nothing to repaint. Reproduce with `CROSSPOINT_SIM_TAP_PAD` and
`CROSSPOINT_SIM_LOG_PRESENTS=1`, looking for a present whose pad state does not
match the button that caused it.

### [S-025] The CRT page fade stalls and resumes when a redraw runs
**severity: medium (the effect reads as broken) · scope: page fade / present loop · filed 2026-08-27 from the device · NOT YET REPRODUCED**

Owner: *"there's a stutter lag hold on redraw for crt fade (the fade does not
account for time spent redrawing and it pauses and resumes in a visibly awkward
way)."*

**FIRST HYPOTHESIS CHECKED AND WRONG, 2026-08-27 — recorded so it is not
re-derived.** The obvious guess is that the fade is an accumulator advanced once
per frame, which a slow present would starve. It is not. `HalDisplay.cpp:3039`
computes `age = SDL_GetTicks() - lastInteractionMs` and derives alpha from that
age, so the fade is ALREADY a pure function of wall time, evaluated at present.
A late present therefore lands on the correct alpha for the wall clock, not a
stale one, and the fix "make it wall-clock" has nothing to do.

**The surviving lead is COST PER FADE STEP, not the clock.** The fade wakes once
per QUANTIZED alpha step (`pagefade::nextStepAgeMs`, `pageFadeStepDueMs`) and
each wake sets `pendingPresent` — so every visible step of the fade pays a full
present. With the as-shipped dials a present is not cheap: measured 51–53 ms of
panel field even with the sheet served from cache, and ~130 ms when the seed
moves and the sheet rebuilds. A fade whose every step costs 50 ms cannot look
smooth, and a step that coincides with a real redraw costs both.

That also explains the shape of the complaint precisely — "pauses and resumes"
rather than "runs at the wrong speed". The VALUES are right (wall clock); the
DELIVERY of them is lumpy.

**SECOND HYPOTHESIS ALSO WRONG - MEASURED 2026-08-28.** The cost theory above
is disproved by the instrument this repo already has.
`CROSSPOINT_SIM_LOG_TIMING=1`, as-shipped dials, dark ground, a 3 s fade:

```
[timing] #51 total 14.25 ms | accum cache 11.43 | panel off | sheet off | scanlines off | grain cache 0.00
[timing] #57 total  2.64 ms | accum cache  1.99 | panel off | sheet off | scanlines off | grain cache 0.00
```

**Every field reads `cache` or `off` on every fade present - nothing rebuilds**
- and a present costs **2.6-14.7 ms**, not the ~50 the cost theory needed. The
sheet is not rebuilt per fade step, so there is nothing there to make cheaper.
The dominant line is the trail accumulator, and it is a cached draw.

**What the data DOES show is the step SCHEDULE.** Present-to-present intervals
across one fade, in ms:

```
64  194  133  192  191  188  301  344  474  772  2083
```

They lengthen, and they must: alpha follows 10^(-age/fade), so the time to the
next QUANTIZED step grows as the curve flattens. `nextStepAgeMs` is correct and
doing exactly its job - but late in a fade the picture changes once every two
seconds, and each change is one code value.

The remaining question is PERCEPTUAL rather than mechanical, and reading the
code again will not answer it: whether the awkwardness is those late sparse
steps, the unevenness of the early ones (194/133/192 is not a smooth cadence),
or something that appears only on Metal at 120 Hz. Recorded as measured rather
than guessed a third time.

**Two hypotheses are now disproved and must not be re-proposed**: it is not a
per-frame accumulator (the age is wall-clock), and it is not field rebuild cost
(everything is cached). Related: S-019, whose fix - waking once per quantized
step instead of every frame - is what produced this schedule.

### [S-019] The app averages 50% of a core for minutes at a stretch on the phone
**severity: medium (battery) · scope: iOS present loop · filed 2026-08-22 from the device's own diagnostics · HALF FIXED and NARROWED 2026-08-25**

**2026-08-25: reproduced, measured, and split in two.** Everything below the
original entry is the 2026-08-22 filing and stands as the report. What the
measurement found is that there were two separate render loops behind it, one
of which is now fixed and the other of which is a design cost the owner has to
price. Method: desktop `simulator_x3`, `SDL_VIDEODRIVER=dummy` (software
renderer, render scale 1), `CROSSPOINT_SIM_AS_SHIPPED=1`, `/usr/bin/time -l`
for CPU and `CROSSPOINT_SIM_LOG_PRESENTS=1` for the present count. A software
renderer at 1x overstates the per-present cost against the phone's Metal and
understates its pixel count; the present COUNTS are the platform-independent
half and they are what is quoted.

**The shell does not idle-spin, and that lead is dead.** An idle as-shipped
dark reader presents **once in 30 seconds** and sits at **0.1% of a core**.
`sample` on the main thread puts 5922 of 6103 samples in `nanosleep`, under
`loop() -> HalPowerManager::lightSleep -> delay(50)`: the FIRMWARE's own loop
blocks for 50 ms at a time, so `simulator_main.cpp`'s `SDL_Delay(1)` never sets
the pace when nothing is happening, and its "~1 kHz" comment describes a rate
the loop only reaches when the firmware asks to spin. The simulator's
`lightSleep()` (`src/HalPowerManager.h:41`) is unconditional -- always
`delay(50)`, always true -- so it never takes the firmware's WiFi/USB decline
branches and the idle cadence is IDENTICAL on desktop and iOS. Also ruled out:
`EpubReaderActivity::skipLoopDelay()` was not spinning in any of these runs
(present intervals were 15-16 ms, which is `delayWallClock(10)` plus a present,
not the ~6 ms a 1 kHz spin gives), and the phosphor accumulator does terminate
(`accumLive` is bounded, and an idle page logs `live=0`).

**LOOP 1 -- THE PAGE FADE. Fixed 2026-08-25.** With a fade set (the owner's own
`settings.json` carries `pageFadeSeconds: 300`, `pageFadeDepthPercent: 75`) an
idle app presented **507 times in 30 seconds and burned 10.3% of a core**, on a
page nobody was looking at, for the whole length of the fade. `HalDisplay.cpp`
re-armed `pendingPresent` on every present while `pagefade::stillMoving`. But
what reaches the glass is `round(alpha * 255)`, and over a 300 s fade that curve
moves **0.008 of a code value per 60 Hz frame** -- so about 127 of every 128 of
those frames were bit-identical to the one before. Fixed by scheduling the next
present at the wall-clock instant the QUANTIZED alpha actually changes
(`pagefade::nextStepAgeMs`, parked in `pageFadeStepDueMs` and woken by a new
gate at the top of `presentIfNeeded`). A fade of any length now costs at most
255 presents in total, which `tests/page_fade_test.cpp` asserts.

| 30 idle seconds, fade at 300 s / depth 75 | presents | user CPU |
|---|---|---|
| before | 507 | 3.12 s (10.3% of a core) |
| after | 23 | 1.12 s |
| no fade at all, for scale | 1 | 0.96 s |

The fade's own cost is 2.16 s per 30 s before and 0.16 s after: **13.5x**.
Pixel proof, same script and same card, against the pre-fix binary: captures at
8,000 ms and 30,000 ms are BYTE-IDENTICAL; the one at 15,000 ms differs by a
maximum of **1** code value on 9.7% of bytes, which is one alpha step -- the
schedule rounds up to whole milliseconds, so a capture between two steps can
sit one step behind. The two `tools/capture_arm.sh` gate baselines
(`53aaf43c38cc834f501525b5973d2566` dark, `3f4773ed9d77fac0da90d6d2fb4aba72`
light) are unchanged, and 54/54 host tests pass.

**This is the loop that fits build 107**, whose report is dated 2026-08-20 --
inside the window where Page Fade was a row in Settings.app (it landed 1514fe0
on 08-17 and was frozen OFF by bc74bd8 on 08-23). Commit f7a0b5f, 2026-08-20,
records the symptom in passing without recognising it: *"presents run
continuously at ~15 ms."* Note the phone CANNOT hit this today --
`CrossPointPrefs_pageFadeSeconds()` returns 0 without consulting NSUserDefaults
-- so for iOS this half was already fixed in passing by the freeze, and what is
fixed here is the desktop, and the loop itself for whenever the row comes back.
The four reports from 2026-08-15 (builds 76-79) predate the fade entirely and
are NOT explained by it.

**LOOP 2 -- THE PHOSPHOR TRAIL. Live on the phone, and an owner decision.**
A dark page turn costs **84 presents spread over 2.63 seconds**. Present #2
builds the scanline field (39 ms); #3 through #84 are all cache hits whose cost
is the composite itself, 4-12 ms each on this renderer. The window is
`accumLive`'s `trailMs * 2.4` -- 2628 ms at the shipped 1095 ms trail -- and
during the first second the firmware polls at 100 Hz, so the app composites the
whole surface about 62 times before dropping to the 20 Hz light-sleep cadence.
Measured end to end: a page turn every 3 seconds for a minute is **38% of a
core** (24.25 s of CPU over 64 s, ~1.2 s per page turn). That is the shape of
the report, and it is untouched by the fade fix (1575 presents after, 1576
before). Two levers, neither taken without a ruling:

- **Cap the animation's frame rate.** The accumulator's decay is TIME-based
  (`dt` since `accumLastFadeMs`), so a cap changes neither the trail's duration
  nor its end state -- only how many intermediate frames are drawn. 30 Hz would
  take 84 presents to about 53.
- **Bound the live window by when the trail can no longer alter a pixel,**
  instead of a flat 2.4 trails. The accumulator composites with MAXIMUM under a
  colour mod of the ink, so its ceiling is `decay x ink`; once that is at or
  below the paper tone it cannot change any pixel, because every pixel under it
  is at least paper. For the shipped `E0E0DE` on `121212` that is 18/224, i.e.
  **1.10 trails, not 2.4** -- a 54% shorter window, worth about 22 of the 84
  presents. Provably bit-identical, but it needs a pixel A/B inside the tail
  before it ships.

**iOS DOES NOT DIFFER HERE, and that is measured rather than argued.** The same
page-turn session was run on the iOS Simulator (iPhone 13 mini, Metal renderer,
`simctl launch` with `SIMCTL_CHILD_CROSSPOINT_SIM_INPUT_SCRIPT` driving one
`QTAP:RIGHT` every 3 s for a minute) against a fresh `build-simsdk` build:

| one page turn every 3 s, dark, 60 s | presents/turn | CPU |
|---|---|---|
| desktop, software renderer, render scale 1 | 83 | 24.25 s / 64 s = **38% of a core** |
| iOS Simulator, Metal, render scale 3 | 65 | 20.8 s / 60 s = **35% of a core** |

Nine times the pixels on a GPU lands within three points of the software
renderer at 1x, which says the cost is carried by the NUMBER OF PRESENTS and
not by what each one paints -- so the lever is the count, not the resolution.
(That tree's CMake cache is stale at 3x where the app ships 2x, so the iOS
figure if anything overstates the shipped cost; it was not reconfigured because
a render-scale define is PUBLIC on `crosspoint_core` and would rebuild
everything.) Idle on the same iOS build is **0.6% of a core** and effectively
no presents, matching the desktop exactly -- as it must, because
`HalPowerManager::lightSleep` is this repo's own header and is unconditional on
both platforms.

**Close by** taking one of those two rulings and re-verifying with a
cpu_resource-free week on the phone. Do NOT close on the fade fix alone.

**THE ORIGINAL FILING, 2026-08-22, unchanged:**

King's crash-report store (pulled over pymobiledevice3, Developer Mode
enabled 2026-08-22) holds five `CrossPointX3.cpu_resource` reports — builds
76, 78, 78, 79 (all 2026-08-15) and **107** (2026-08-20):

```
Event:  cpu usage
CPU:    90 seconds cpu time over 179 seconds (50% cpu average),
        exceeding limit of 50% cpu over 180 seconds
Action taken: none
```

The heaviest stack is the main run loop into app code (unsymbolicated —
release build, dSYM not to hand), which is the shape of the SDL
present/compose loop repainting every frame whether or not anything changed.
iOS only diagnoses at this rate ("action: none"), but half a core for the
length of a reading session is battery, and the phone was at 9% when it came
in for this checkup.

**Close by** symbolicating one report against the build-107 archive's dSYM to
confirm the loop, then making the present loop event-driven when the screen
is static — the firmware's e-ink model already knows when nothing repaints;
the shell should idle with it. Re-verify with a fresh cpu_resource-free week
on the phone.

The same pull's full disposition, for the record: five real crash reports,
all build 110, all the SAME `objc_retain(0x1)` in `-[UIViewController
setTitle:]` — the palette-mixer crash already found on-device and sidestepped
in build 111 (`CrossPointPaletteMixer.mm` carries the note); and seventeen
JetsamEvent appearances, every one `long-idle-exit` housekeeping, zero
memory-pressure kills. No unknown crashes.


### [S-016] The whole screen flashes on some CRT palettes — FIXED 2026-08-19, unconfirmed on the phone
**severity: medium · scope: ios display · reported 2026-08-19**

Owner, from the phone: "there's still a bug with the full screen flashing on
some crts." SOME, not all — which was the whole clue. Narrowed by the owner on
2026-08-19 to "the long persistence ones", and that identifies the mechanism
exactly.

**CAUSE: the DEPOSIT into the accumulator was `SDL_BLENDMODE_ADD`.**

The composite to screen was changed to MAXIMUM back when the page-turn flash was
fixed, with an explicit argument — a pixel lit in two frames is one phosphor
being re-excited, not two emitters stacked, so it cannot exceed full emission.
That argument applies word for word to the deposit and was never carried across.
The deposit kept summing, unbounded.

The bound that mattered was the DECAY, which is why only long trails showed it.
A short trail drains the buffer to near black before the next deposit lands, so
the sum never builds. At P7's 2828 ms with content changing every 100 ms, `keep`
is 10^(-100/2828) = 0.92 per frame and the running sum tends toward roughly 12x
a single page; at P45's 283 ms it settles near 1.8x.

**Fixed** by depositing with the same saturating MAXIMUM blend, with the same
ADD-at-reduced-strength fallback the composite uses. Measured on P7 with content
changing every 200 ms, before and after, same script and same binary otherwise:

| | peak | mean |
|---|---|---|
| ADD (before) | 35.53 | 23.09 |
| MAXIMUM (after) | 31.04 | 17.85 |

Peak down 12.6%, mean down 22.7%. The desktop understates it — it cannot drive
content changes as fast as a finger can, and the theoretical 12x needs sustained
rapid change — so treat those figures as the direction confirmed rather than the
magnitude.

**UNCONFIRMED on the phone.** The flash is a thing the owner sees; nothing here
has seen it.

**Why the first hunt missed it, kept because the metric was the mistake.** With the phone's own settings forced by env — glow at the preset's
trail, beam 67 ms, page fade 5 min at Dim, grain 1x Vignette+Mottled — across
P45, P19, P7, P22G and P11:

| | |
|---|---|
| worst single-frame excursion above BOTH neighbours | **1.26 levels** (P45) |
| the same with glow and beam off | 0.00 |

A first pass reported ratios of 1.6x to 2.8x and that was a MEASUREMENT ERROR:
min/max across a run spans different SCREENS, and Home with book covers is
simply brighter than a reader page. A flash is a frame brighter than the ones
either side of it, so the excursion above both neighbours is the metric, and by
it nothing off-phone flashes.

**Why the desktop cannot show it.** At render scale 3 with
`CROSSPOINT_SIM_LOG_PRESENTS=1`, every present logs `frame from B` — the BASE
pass — and `CROSSPOINT_SIM_LOG_AA=1` prints nothing at all. The grayscale
compose never runs, so the two-pass paint that present coalescing exists to
merge does not happen here. The flash this project already fixed once was
exactly a base-then-compose pair reaching the screen; if this is a relative, the
desktop is blind to it by construction. Same lesson as the last three flash
hunts — the instrument has to overlap the shipped path.

**What would crack it, cheapest first: which palettes, and on what action.** If
it is the long-trail rows it is the accumulator; if it is the pale-ground rows
it is the `panelIsDarkGround()` gate that disables the trail; if it is the
cascades (P7, P14, P17) it is the tail colour multiply. Those are three
different pieces of code and the report as it stands fits all three.

---

## FIXED

### [S-023] Speak Screen goes permanently deaf at the first reboot of a session — FIXED 2026-08-26
**severity: high · scope: ios read-aloud / accessibility · owner report from the phone 2026-08-26**

Owner, verbatim: *"'no speakable content could be found on the screen' error is
happening again"*, then the correction that dated it: *"it was broken before
today."* He sent his device's `a11y.log`, which is decisive and rules out the
2026-08-09 shape (iOS never asking) outright:

```
[    87.0] 69 word rects -> 14 line elements; first "summer and never got home."
[   112.2] 43 word rects -> 9 line elements; first "Chapter 1 — Port Talon"
[  1401.9] page cleared (reader left)
[  3738.5] CHAIN wants=1 page=0B rects=0 fb=0B geo=1 view=1 inWindow=1 elements=0
[  3746.0] TEXTINPUT scroll next -> page turn
[  3748.5] CHAIN wants=1 page=0B rects=0 fb=0B ... elements=0
```

iOS **is** asking (`scroll next` fired and turned the page), the view is
installed and in the window — the app simply has nothing, on both sources, from
t=3738 to the end of the session, on a book that was healthy at t=112.

**What broke.** One flag with two writers that had drifted apart, across a
boundary that resets one of them and not the other.

`ios/CrossPointReadAloud.mm` seeded the firmware's capture flag in **two**
places. `CrossPointReadAloud_begin()` seeded it from
`CrossPointPrefs_readAloudEnabled()`, which was right until capture became
unconditional on the phone (build 42, the fix for the *previous* incarnation of
this same message) and was never updated with it — a Speak Screen user leaves
the Read Aloud (Experimental) toggle OFF, so begin() seeded **false** on every
boot. `CrossPointReadAloud_perFrame()` then corrected it to true, but only on
the edge `g_lastCaptureWanted != 1`.

On the first boot that edge fires and the chain is healthy. The iOS reboot is a
`longjmp` back into `setup()` in the same process:

| | what happens |
|---|---|
| boot 1 | begin() seeds `false`; perFrame's edge fires and sets it TRUE. Healthy. |
| REBOOT | `simreset::runAll()` → `ReadAloudChannel::resetForReboot()`, which deliberately leaves `wanted_` alone ("the consumer re-seeds it"). Every static in the adapter survives — `g_lastCaptureWanted` at 1. |
| boot 2 | `CrossPointHarness_begin()` → `CrossPointReadAloud_begin()` seeds `false` **again**. perFrame's edge is already satisfied, so nothing ever sets it back. |

`HalGPIO::readAloudCaptureWanted()` is then false for the life of the process,
`EpubReaderActivity::captureReadAloudPage` returns at its first line, and
nothing is ever published — which is also why `fb=0B`: the textless-page
fallback (`g_fallbackUtf8`) is only computed inside the drain's `if (got)`
block, so a channel that never delivers starves the substitute as well. One
root, both halves of his log.

Every file transfer, every font download and every sleep/wake crosses that
boundary, so the phone reaches boot 2 in the course of ordinary use. His gap was
39 minutes.

**Reproduced and fixed, both arms measured on an iPhone Air simulator
(`crosspoint-x3-air`), 2026-08-26**, same script both times — open the book,
turn pages, POWER-hold to sleep, POWER-tap to wake (the longjmp), turn pages
again:

| | before the reboot | `[power] longjmp reboot` | after |
|---|---|---|---|
| pre-fix build | `page=746B rects=151`, `790B/165`, `780B/156` | crossed | `page=0B rects=0 fb=0B` at +0.0 s, +5 s, +10 s, +15 s, across two page turns |
| fixed build | `page=812B rects=158 elements=22` | crossed | `page=812B rects=158 elements=22`, then `746B/151` after a turn |

The `[READALOUD] page capture wanted (always, on iOS)` line is its own
discriminator: it prints **once** in the pre-fix run and **twice** — once per
boot — in the fixed one.

**The fix, and why it is two changes rather than one.** Registering the static
would have fixed the instance; both were taken because the class is what keeps
coming back.

* `CrossPointReadAloud_begin()` seeds `true` unconditionally, joining the
  `g_last*` re-arm list that `g_lastEnabled` and `g_lastRatePercent` were
  already in. It must stay in begin() rather than moving to a reset registrar:
  begin() runs *before the first `loop()`*, and a book resumed at boot renders
  its first page inside that iteration.
* `perFrame` pushes the flag **every frame** instead of behind the edge. The
  setter is one atomic store (`ReadAloudChannel::setWanted`), so the guard was
  buying nothing measurable and cost this; the static now throttles only the
  log.

**Held by `tests/readaloud_reboot_seed_test.py`**, which fails on all three of
its properties against the pre-fix file. Its third assertion is the general one:
every `int g_last* = -1;` edge cache declared in the adapter must be re-armed in
`begin()`. Source-level because the live check needs UIKit, a booted phone and a
reboot mid-run — see `docs/speak-screen-chain.md` for that run.

**Audited for siblings and found clean.** Nine other edge-cached statics cross
the same boundary (`g_appliedDark`/`Outline`/`Fill`, `pollBeamPaint`,
`pollPageFade`, `pollPanelGlow`, `pollLetterpress`, `pollPaperTooth`,
`pollScanlines`). None has this bug, and the reason is precise rather than
lucky: the read-aloud flag is the only one whose *mirrored state is actively
re-written on the far side of the boundary*. `gDisplayRebootReset` does not
touch the surface dials — they are atomics in `HalDisplay` that survive the
longjmp — so a stale poll edge is suppressing a push of a value that is already
applied. `applyTheme()` writes `g_appliedDark` unconditionally on every
`CrossPointHarness_begin()`, so the appearance edge is re-armed by construction.
`fontFamilyStepChannel` has no wanted flag and no consumer-side edge at all.
**A stale edge is only a bug where something else resets what it mirrors** — that
is the shape to look for, not the static by itself.

### [S-020] A gun moved in dark mode throws away the light page's chosen ink — FIXED 2026-08-23
**severity: high · scope: ios palette sourcing · owner P1 from the phone 2026-08-23**

Owner, verbatim: *"p1 bug: ink is not being picked up. recreate, review and fix
sourcing for light and dark to be more accurate on load, switch etc."*

**What broke.** The 2026-08-22 doctrine split gave each appearance its own
editor — light is paper and ink (`ios/CrossPointLightInkPicker.mm`), dark is the
CRT (`ios/CrossPointPaletteMixer.mm`), and the page-color chip branches on the
live appearance (`ios/CrossPointIOSShim.cpp:2555`). They share ONE store: a
preset integer plus four hex fields, two per appearance. The mixer was left
`untouched` by that split — `docs/light-ink-picker.md` says so in as many words —
and went on writing **all four** fields from the blend
(`CrossPointPaletteMixer.mm` `applyGuns`, the `r.light.*` writes). So one gun
move in dark mode replaced whatever ink had been chosen in light.

Second half, same shared-slot cause: pointing the preset at Custom for the light
page cost the DARK page its phosphor. The ink picker already froze the dark
TONES, but `pollPanelGlow` (`CrossPointIOSShim.cpp:1483`) read the preset
integer raw, and Custom names no phosphor — so a light-mode ink pick turned
White CRT's 283 ms emissive trail into 0 ms reflective, and kept it that way
across relaunches.

**Reproduced first, on an iPhone Air simulator (`663B0B14`), 2026-08-23**, with
`CROSSPOINT_SIM_APPLY_INK` and `CROSSPOINT_SIM_MIX_GUNS` driving the editors'
own apply functions:

| step | `panelInkLight` | page text, measured |
|---|---|---|
| Payne's Gray applied in light | `323D47` | (30, 37, 43) |
| relaunch (load) | `323D47` | (30, 37, 43) |
| dark, then light again (switch) | `323D47` | (30, 37, 43) |
| **one gun moved in dark mode** | **`6E0500`** | **(64, 3, 0)** — a red |

`lightInkIndex` still read 15 throughout, so the picker went on showing Payne's
Gray as the chosen row while the page rendered a color nobody picked. The glow
half came off the app's own log: `[glow] preset 21 -> 283 ms trail ... emissive`
at boot, `[glow] preset 0 -> 0 ms trail ... reflective` six seconds later, after
one ink pick.

**Fix.** The decision moved to `src/PanelSource.h` — pure, host-tested — and
`ios/PanelPrefs.h` only fetches. One editor per polarity, neither writing the
other's fields, and one shared claim protocol
(`CrossPointPrefs_claimCustomFor(editingDark)`) that freezes the other
polarity's currently-rendered pair **and its phosphor**
(`panelDarkSnapshotPreset`, append-only, 0 = none) before the shared preset
integer moves — and does nothing once the slot is already Custom. The glow asks
`crosspoint::glowPresetForPrefs()`.

**Verified after, same device, same sequence**: the light page measured
(30, 36, 43) on load, after a light↔dark switch, and after the same gun move that
used to destroy it; the store kept `panelInkLight=323D47`; and the trail stayed
283 ms emissive through the ink pick and across a relaunch. Native-pixel PNGs of
each step were captured with the run.

**Why nothing caught it.** `tests/chip_tint_source_test.py` guards this exact
area and passed through the whole bug: it asserts a delegation CHAIN and never a
tone, and the chain was intact the entire time. `tests/panel_source_test.cpp`
(bytes, both polarities, load / switch / both editor orders) and
`tests/panel_source_test.py` (each editor writes only its own polarity's keys)
now cover it; both fail against the pre-fix tree — 3 and 20 failures
respectively.

### [S-021] The pad's Accessible pin lived at one of its two resolution points — FIXED 2026-08-23
**severity: medium · scope: ios pad and keyboard chips · found 2026-08-23 while fixing S-020**

Owner order 2026-08-22 pinned the button pad to `kPresetAccessible`. The pin
went into `CrossPointIOSShim.cpp`'s `currentLevels()`, which feeds the pad and
the SDL SHOW chip. `ios/PanelPrefs.h`'s `padPaletteForPrefs` resolves the pad a
SECOND time, for the UIKit HIDE chip in the keyboard bar, and went on handing
the raw stored contrasts to `makePaletteOn` — the registered defaults, which are
the Current preset's ±1. So the hide chip drew a ±1 hairline beside a pad drawn
at Accessible's ∓4: the two halves of one gesture, 4–5× apart in contrast, under
a header comment in that very file promising one definition.

Separate defect from S-020 — different control, different mechanism — found in
the same file because the owner's report pointed at it. Both resolution points
call `padpalette::shippedLevels()` now, pinned by `tests/panel_source_test.cpp`
and by `tests/panel_source_test.py`.

### [S-022] Tapping Presets left the page under the sheet live for the rest of the session — FIXED 2026-08-23
**severity: high · scope: ios input gating · found by adversarial review 2026-08-23, hours after the Presets list shipped**

Both page-color drawers PUSH `ios/CrossPointPresetList.mm` onto their own
navigation controller. UIKit sends `viewDidDisappear:` to the PUSHING controller
when it does, and both controllers cleared their presented flag there
unconditionally — `g_mixerPresented`, `g_pickerPresented`. Nothing set it back:
there was no `viewDidAppear:` anywhere in the three files, and the flag was set
true exactly once, at presentation.

Those sheets are undimmed medium detents, deliberately, so the page above them
stays visible as the preview — which means UIKit passes every touch OUTSIDE the
sheet straight through to the SDL view. Five sites gate on the flags
(`CrossPointIOSShim.cpp`'s two finger paths, `CrossPointZenRecognizers.mm`'s
three recognizers). So the sequence "open a drawer, tap Presets, touch the page"
turned the page on a tap, drove font size on a swipe, and toggled zen on a
three-finger tap, while the owner believed he was in a color picker — and it
stayed that way until the sheet was dismissed.

The comment that stood at the clear said "the nav never pushes a second
controller, so disappearing means DISMISSED." That was true when it was written
and false twenty minutes later, which is the whole lesson: an invariant asserted
in prose does not hold itself.

Both controllers now reassert in `viewDidAppear:` and clear only when
`navigationController.topViewController == self`, so a push holds the gate and a
pop restores it. The sheet cannot be dismissed while the list is up
(`modalInPresentation` pins pull-down and the list carries no Done), so "top of
the stack" is the whole distinction. Each transition logs
(`[mixer] on screen; touch gate UP` / `covered by a push; touch gate HELD`), and
`tests/panel_source_test.py` fails an unconditional clear or a missing
`viewDidAppear:`.

Measured on an iPhone Air simulator (`663B0B14`) with
`CROSSPOINT_SIM_OPEN_MIXER=1 CROSSPOINT_SIM_OPEN_PRESETS=1`: gate UP at
presentation, `covered by a push; touch gate HELD` when the list arrives. The
dismiss and pop branches rest on UIKit's push/pop semantics rather than a probe
— neither can be driven headlessly, since there is no hook that taps Done.

### [S-018] iOS appearance and CrossPoint's Dark Mode disagree, and the setting never sticks — FIXED 2026-08-19
**severity: high · scope: ios display · reported from the phone 2026-08-19**

Owner: "fix when ios dark mode is the opposite of dark mode in crosspoint. it
seems to use some stuck fallback."

**Two authorities for one question.** `applyTheme` set `g_dark` from
`systemIsDark()`, so the pad and the field followed iOS — while the PAGE follows
`SETTINGS.darkMode`, which the firmware applies itself in `setup()`. Toggling
Dark Mode inside CrossPoint therefore inverted the page and left the pad on the
system's appearance: the two halves of one screen in opposite polarities.

**And the in-app control did not stick at all.** Every `applyTheme` wrote the
system value back over `SETTINGS.darkMode`. Reproduced before touching anything:
iOS light, `darkMode=1` stored, app launched — **came up light, and the file read
back 0.**

**Fixed by making the firmware's setting the single source of truth.** The system
now only SEEDS it: on a fresh install, and whenever the phone's appearance
actually changes while running. Everything else reads the setting, so an in-app
toggle moves the page, the pad and the field together and survives a relaunch.

**Two further overwrites were found while fixing it, each hiding behind the last:**

* seeding on every startup — a relaunch is not the phone changing its mind, but
  it was treated as one, so the stored choice was overwritten every launch.
  Seeding now happens only when there is no `settings.json` yet.
* `pollAppearance` starting its "last system appearance" at `-1`, which made its
  FIRST tick look like a change and reseeded immediately — the same overwrite,
  reintroduced one function further down. It initialises from the system now.

**Verified in the simulator, both directions:** iOS light with `darkMode=1`
stored renders the whole screen dark and the file still reads 1
(`ios/mockups/dark-mode-setting-respected-2026-08-19.png`); a live system flip to
light while running takes the app light and the file to 0.


### [S-017] The Back|Select rocker's divider sits hard left, not centred — FIXED 2026-08-19
**severity: medium · scope: ios display · reported from the phone 2026-08-19**

Owner, with a screenshot: "the left and center of it messed up. seems like the
dividing line stopped being centered… Back and Select rocker has a dividing line
on its left instead of centered."

**A phantom third pair, left behind by today's side-rocker removal.** `paintPad`
declares its rocker list as

```
const int pairs[3][2] = {{kPadBack, kPadConfirm}, {kPadLeft, kPadRight}};
```

— dimension **three**, two initialisers. The trailing row zero-initialises to
`{0, 0}`, and `kPadBack` is 0 (`CrossPointIOSShim.cpp:121`). So the loop ran a
third time with `a == b ==` the Back cell, painting an entire extra capsule over
the left rocker's Back half and a divider tick at *that half's* own edge. The
result reads exactly as reported: the seam on the left rocker is at the quarter
point rather than the middle.

Before today it was harmless — `Up|Down` was the third pair, and the array was
full. The ruling "lose the side button UI on all devices" removed that pair from
the initialiser and left the dimension at 3, which is what turned a correct
array into a self-overdraw.

**Fixed** by sizing from the initialiser, `const int pairs[][2]`, so removing a
pair can never leave a phantom one again.

**Verified by measurement, not by eye**, on an iPhone simulator in the same green
CRT palette as the report: left rocker edges 46-375 with its divider at 210
against a true centre of 210 (**0 px off**), right rocker 704-1033 with its
divider at 869 against 868. Capture kept at
`ios/mockups/pad-divider-centred-2026-08-19.png`.


### [S-015] `test_text_entry.sh` no longer reaches the field it tests — FIXED 2026-08-17
**severity: medium · scope: tests · found 2026-08-17 · fixed in ac88f12**

**Cause, and it was the same fault twice:** it navigated both lists with UP and
DOWN, which are the SIDE pair and page by a screenful. A one-screen menu has no
next screenful, so those presses moved nothing. Home now uses RIGHT (over-pressed,
since the row count follows the recents list), Settings uses LEFT counted
backwards from row 0 (that list wraps: LEFT x1 Colophon, LEFT x2 Device Owner).
Spacing was a third fault — 180 ms where ~900 ms is needed. Now PASSES.

It fails at case 1 against firmware `main`, and has failed since before the
B-028 work (confirmed by stashing that fix and re-running: identical failure).
The failure is its own navigation, not the channel it covers — which means the
host-keyboard channel currently has NO passing end-to-end guard on the
single-line side, and a real regression there would look exactly like this.

Two stale things, both in `NAV_TO_OWNER_FIELD`, and the second is only visible
once the first is fixed:

1. **Home navigation uses `DOWN`.** Lists navigate on the FRONT pair; the side
   buttons page by a screenful and a one-screen menu has no next screenful, so
   the fifteen `DOWN`s move nothing and the `ENTER` opens row 0 (`Recent
   Books`). See [docs/headless-qa.md](docs/headless-qa.md) — the same point that
   `test_note_editor_repaint.sh` was written against. Swapping `DOWN` for
   `RIGHT` gets it into Settings.
2. **The Settings tail count is stale.** With Home fixed, `6700:UP;7000:UP`
   lands on `FontSelect`, not Device Owner. The test's own comment predicted
   exactly this ("Colophon was added after it… keep asserting the activity
   rather than trusting the count"); something has since been appended or
   reordered again.

**Close by:** recounting the Settings tail against the current build and
switching Home to `RIGHT`. Both arms of case 4 (the daisywheel) and cases 5–6
(the RAWKEY path) use the same nav string, so one fix restores all six.

Only diagnosed here, not fixed — it surfaced while proving B-028 and repairing
it is a separate recount.

**VERIFIED FIXED 2026-08-18.** Re-run against a clean firmware worktree at
`f80b140b6` with a seeded `fs_`: PASSES, along with the other three shell tests.
This entry sat under `## OPEN` while its own title said FIXED, and CLAUDE.md
went on telling every new session the test was broken — for a day after it was
not. The lesson is the one at the top of this file pointed the other way: an
entry also may not STAY open once there is evidence it is fixed.

---

### [S-014] The image validator and the flasher are excluded from the simulator build — FIXED 2026-08-16
**severity: medium · scope: fidelity · found and FIXED 2026-08-16**

**Fixed by splitting the file, which is what the entry proposed.** The firmware
now has `src/network/FirmwareImageValidator.cpp` holding the READ-ONLY half —
`resultName()`, `runningPartitionChipId()`, `feedHashAndChecksum()` and
`validateImageFile()` — with the shared layout constants moved to
`src/network/FirmwareImageFormat.h` so neither file's existing unqualified uses
had to be rewritten. `FirmwareFlasher.cpp` keeps `flashFromSdPath()` alone and
stays excluded from the `simulator` env; the validator is not excluded, so the
real one compiles in. `platformio.ini` did not need editing at all, which also
means no build directory was wiped.

The simulator's `src/simulator_firmware.cpp` dropped its fake
`validateImageFile()` and `resultName()` (they would now be duplicate symbols)
and kept the `flashFromSdPath()` stub. One new shim was needed:
`esp_ota_get_running_partition()` returns null, which is honest AND safe —
`runningPartitionChipId()` caches `0xFFFF` on a failed read and
`validateImageFile()` explicitly skips the chip check on `0xFFFF`. So a host
validates everything about an image except which MCU it targets, which is the
one property a host cannot know.

**Proven both directions, through the real screen** (Home → Settings → SD
firmware update → file browser → pick a `.bin`):

| Image | Result |
|---|---|
| the genuine 4,492,880-byte `20260807T0857Z-crosspoint-f1459353.bin` | validation passes; the **"Update firmware?"** confirmation prompt appears, which is reachable only on `Result::OK` |
| the same file with **one byte flipped** at offset 2,246,440 | `validate: checksum mismatch computed=0x03 stored=0xFC` → `image validation failed: BAD_CHECKSUM` |

That pass is also the end-to-end proof that the mbedtls SHA-256 shim is now
real: the image carries a SHA-256 trailer, and the old XOR fold could not have
matched it under any reading.

Firmware TU count went 129 → 130, so `cmake/CrossPointSources.cmake` was
regenerated. Desktop, iOS and 22/22 host tests all green after.

**Original entry follows.**

Found while closing S-001's partition half, by driving the SD firmware update
screen to the end. With a partition now available the firmware gets as far as
`firmware_flash::validateImageFile()` and hits this:

```
[FW] Selected: /20260807T0857Z-crosspoint-f1459353.bin
[FLASH] [SIM] Firmware image validation is disabled in the native simulator
[FW] image validation failed: UNSUPPORTED_IN_SIMULATOR
```

The stub is [src/simulator_firmware.cpp:15](src/simulator_firmware.cpp), and it
is there because the firmware's own `platformio.ini` drops the real file from
the `simulator` env:

```ini
build_src_filter =
  -<network/FirmwareFlasher.cpp>    ; "Firmware-update code remains
  -<network/OtaBootSwitch.cpp>      ;  non-destructive in the simulator."
  -<network/OtaUpdater.cpp>
```

**The exclusion is right for two of those three and wrong for the validator.**
`flashFromSdPath()` and `switchTo()` write flash and move the boot pointer —
nothing a host should imitate. But `validateImageFile()` writes nothing at all:
it opens a file, checks the 0xE9 magic, walks the segment table, folds the XOR
checksum and compares a SHA-256 trailer. That is pure computation over a file on
the simulated card, it is the code most worth running before shipping a
firmware image, and it has never executed here once.

**Verified, not assumed:** `validateImageFile` is `src/network/FirmwareFlasher.cpp:107`
and its only side effect is `Storage.openFileForRead` + reads. The mbedtls
SHA-256 it needs is now real (see below); `SPI_FLASH_SEC_SIZE` is already
shimmed at [src/spi_flash_mmap.h](src/spi_flash_mmap.h).

**Close by:** splitting the validator out of `FirmwareFlasher.cpp` so the
simulator can compile it without the flash writer, or narrowing the src_filter
and letting the write side fail through the existing `esp_partition_write()`
`ESP_FAIL`. Either is a FIRMWARE change, and editing `platformio.ini` wipes
every build directory, so it wants its own pass rather than a rider on this one.

**Related and already fixed here:** the mbedtls SHA-256 shim
([src/mbedtls/sha256.h](src/mbedtls/sha256.h)) was a fake — `digest[i % 32] ^=
input[i]`, returning success. Every SHA-256 computed in this simulator was
silently wrong. It now uses CommonCrypto on macOS and OpenSSL on Linux, with
`tests/sha256_test.cpp` pinning it to the published FIPS-180-4 vectors. It had
no live caller (the only one is the excluded file above), so nothing was
observably broken by it — but the validator could never have passed its SHA
check, and that would have been the next wrong diagnosis.

---

### [S-001] The simulator reports the opposite of the device in six places
**severity: medium · scope: fidelity · found 2026-08-07** · heap + battery FIXED 2026-08-08 · **remaining four FIXED 2026-08-16**

Not crashes — false confidence. Each makes a firmware path look exercised when
it never ran, and the simulator is the project's only pre-device gate.

| Reports | Device | What it hides |
|---|---|---|
| ~~1 MB free heap~~ **FIXED 2026-08-08** (`CROSSPOINT_SIM_HEAP`, `CROSSPOINT_SIM_HEAP_FREE`) (`src/Arduino.h:41,51`) | ~380 KB, no PSRAM | every graceful-degradation gate: indexing pause, glyph prewarm, SD font streaming fallback, image/CSS/JPEG bailouts |
| ~~`supportsAsyncRefresh()` false~~ **FIXED 2026-08-16** (`CROSSPOINT_SIM_ASYNC_REFRESH=1`) | supported | was: the overlapped page turn had never executed in a simulator run |
| ~~no panic ever~~ **FIXED 2026-08-16** (`CROSSPOINT_SIM_PANIC=<reason>`) | 225 lines of panic handling | was: `CrashActivity` compiled in and could not be entered |
| ~~battery 100%, USB always connected~~ **FIXED 2026-08-08** — `CROSSPOINT_SIM_BATTERY=<0-100>`, `CROSSPOINT_SIM_USB=0`; default unchanged. Verified: at 7% unplugged the charging bolt is gone and the battery draws empty | real gauge + GPIO | was: charging bolt always drawn, plug/unplug repaint never fires |
| ~~`esp_ota_get_next_update_partition()` null~~ **FIXED 2026-08-16** (`CROSSPOINT_SIM_OTA_PARTITION=1`) | valid | was: SD firmware update showed "Invalid firmware" before reading a byte |
| ~~OTA pinned to NO_UPDATE~~ **FIXED 2026-08-16** (`CROSSPOINT_SIM_OTA=available\|error`) | real check | was: the available→download→install flow was unreachable — but see the caller note below |

**All four remaining reversals now answer honestly, opt-in.** The definitions
live in [src/SimulatorDeviceTruth.h](src/SimulatorDeviceTruth.h), pure and
host-tested by `tests/device_truth_test.cpp`, and every default is byte-for-byte
what this simulator always reported — so no existing headless script or
screenshot run changes behaviour. That is the same shape the heap budget took,
and for the same reason: turning device-truth on is a thing a test asks for.

**Proof each one now runs, rather than merely compiles:**

- **Overlapped page turn.** A/B on the same script: `CROSSPOINT_SIM_ASYNC_REFRESH=1`
  logs `Page render (tiled async)` twice, the identical run without it logs it
  zero times. First execution of `EpubReaderActivity.cpp:1593`'s branch in this
  simulator's history. The `!inverted` term mirrors the device rather than being
  invented: `FreeInkDisplay::supportsAsyncRefresh()` is
  `!_inverted && !_inversionDirty && _driver->supportsAsyncDisplay()`, and both
  X3 drivers (Uc8253X3, Ssd1677) answer true — so on hardware the capability
  comes and goes with dark mode, and now it does here too.
- **CrashActivity.** `CROSSPOINT_SIM_PANIC='Guru Meditation Error (LoadProhibited)'`
  produces `[ACT] Entering activity: Crash`, `Previous boot panicked: …` and a
  582-byte `/crash_report.txt` on the card. The control run with no env var
  enters it zero times. The latch is ONE-SHOT by construction — it `unsetenv`s
  on first read, so the desktop `execvp` reboot's child boots clean, exactly as
  the boot after a real panic does. Without that the crash screen would have no
  exit.
- **Next-update partition.** A/B through the real screen (Home → Settings → SD
  firmware update → file browser → pick the .bin). Off: `no next-update
  partition available`. On: the firmware gets past it into the real size check.
  **The first version of this shim invented the slot geometry and was caught by
  that very run** — a guessed 0x1F0000 rejected a genuine 4,492,880-byte image
  as "exceeds partition (2031616 bytes)", which is a NEW wrong answer wearing
  the old one's clothes. The numbers now come off the firmware's own
  `partitions.csv`: `app1, app, ota_1, 0x650000, 0x640000`.
- **OTA check.** Answers `available` / `error` / `none` with a version and an
  install outcome. **But nothing in this fork calls `OtaUpdater`** — grepped
  2026-08-16 across `src/`, `lib/` and `freeink-sdk/`, the only references are
  its own header and .cpp. So this row was unreachable for a second reason it
  never stated: there is no caller. The one firmware-update path a person can
  actually open is `SdFirmwareUpdateActivity`, which is the partition row above.

**Where the SD update path stops now:** at `validateImageFile()`, which is a
different stub and a different bug — filed as **S-014**.

---

### [S-011] `test_sleep_wake.sh` fails against current firmware `main` — the scripted POWER hold no longer sleeps
**severity: medium · scope: tests / firmware drift · found 2026-08-08** · FIXED 2026-08-08

**ROOT CAUSE FOUND 2026-08-17, and it was never firmware drift: the test was the
only one here that did not run HEADLESS.** It omitted `SDL_VIDEODRIVER=dummy`,
so it opened a real SDL window and its timing followed the window server, the
GPU and the machine's load — surfacing as "the 1ms wake tap was missed", which
is indistinguishable from a wake regression from the outside.

Measured both ways on the same tree and binary:

| | result |
|---|---|
| windowed | 2 of 3 FAILED |
| headless | 4 of 4 PASSED |

A first guess that the wake tap needed more headroom (6 s → 15 s) was wrong and
was reverted: it still failed windowed at 15 s. The two tests here that were
never flaky, `test_text_entry.sh` and `test_note_editor_repaint.sh`, both set
the variable. Dummy still renders, so the after-wake screenshot is captured
exactly as before.


The test's scenario (`2500:POWER:700` must enter deep sleep, a later 1 ms tap
must relaunch the process) no longer matches the firmware: against the fork's
`main` @ `4ded8fc`, the process neither sleeps nor relaunches — it idles until
killed, and the harness reports "never relaunched as a wake". Reproduced
byte-identically with the simulator at `origin/main` (`ebf2b54`, before any
read-aloud work), so this is firmware drift, not a simulator regression:
power-button semantics have grown options since the test was calibrated
(`SHORT_PWRBTN::PAGE_TURN`, the long-press behavior setting), and a 700 ms
hold no longer crosses the sleep threshold on the boot-into-reader path a
seeded card lands on.

Found running the full shell-test sweep after the read-aloud input changes —
which the bisect exonerates. `test_text_entry.sh` passes against the same
binary, and the sleep wake edge-latch itself is untouched.

**Close by:** recalibrating the test against the current firmware's power
semantics (which hold duration sleeps, from which screens), or pinning it to
a firmware ref it matches. Decide which behavior is intended before touching
either side.


**Fixed, and the cause was not firmware drift.** This entry blamed the power
semantics growing options. Reading the code says otherwise: sleep on a hold
needs `millis() >= allowSleepAt`, and `main.cpp:562` sets that to
**(end of setup) + 2000 ms**. Booting into Home, setup finishes in ~400 ms and
the test's 2500 ms press lands well clear. Booting into the READER, setup also
paginates — tens of seconds on the seed book's mono-file chapter — so
`allowSleepAt` moves past the press and the device never sleeps.

The defect was therefore in the test, not the firmware: it `cd`s into the
firmware checkout and runs against whatever state the working card happens to be
in, so the same binary passed or failed depending on what had been read last.
It now seeds `readerActivityLoadCount = 1` (the documented lever for a Home boot)
and restores the card afterwards.

Proved both directions: set the card to the boot-into-reader state that produced
the original failure and the test passes, and the card is byte-restored after.

Writing the restore also produced a small lesson worth keeping — the first
version trapped `rm -rf "$WORK"` BEFORE the restore, and the backup lives inside
`$WORK`, so cleanup ate the file the restore needed and silently left the seeded
state on the working card. Restore first, clean up second.

### [S-013] The in-process reboot orphans the parked accept worker
**severity: low · scope: iOS lifecycle · found 2026-08-08** · FIXED 2026-08-08


Every file transfer ends in `silentRestart()`. On iOS that is a `longjmp` back
into `setup()`, which skips destructors — so the `WebServer` whose handler
triggered the restart is never destroyed, and its accept worker, parked on the
dispatch condition variable, lives on forever holding a client socket. Each
transfer leaks one thread and one fd.

This is strictly better than what S-003 replaced (a cross-thread `longjmp`,
undefined behavior), and it is invisible on desktop, where the restart is
`execvp` and the whole process is replaced. But a long-lived phone doing many
transfers accumulates orphaned workers.

**Close by:** on the reboot reset path (`simreset::runAll()` /
`forceReleaseAllForReboot()`), also stop the server and join or detach its
worker before the jump — or have the reboot tear the server down explicitly
rather than leaving it to skipped destructors.


**Fixed.** Live `WebServer` instances register themselves, and a
`simreset::Registrar` stops each one immediately before the in-process jump —
beside the mutex release and the static resets that already run there. `stop()`
sets the abandoned flag, shuts the listening socket and joins, so the worker
exits instead of outliving the reboot.

Safe to call from that point precisely because of S-003: the handler that
triggered the restart runs on the main thread now, so the accept worker is only
ever accepting or parked, and `stop()` releases both. Under the pre-S-003
arrangement the worker WAS the handler and this could not have worked.

Verified: 12/12 simulator tests, and 10/10 requests still served after the
change — the registry does not disturb the normal path.

### [S-012] A throwing route handler hung the file-transfer server forever
**severity: high · scope: web server / threading · found + FIXED 2026-08-08**

Introduced by S-003's dispatch handoff (same day). `handleClient()` unlocked,
called `dispatchParkedRequest()`, then re-locked and set `dispatchDone = true`
to wake the accept worker parked on its condition variable. The signal was a
trailing statement, and route handlers are arbitrary `std::function<void()>`
with no no-throw contract — and this TU builds WITH exceptions, unlike the
device's `-fno-exceptions`. A handler that threw (`std::bad_alloc` under memory
pressure being the realistic case on a phone) skipped the signal, and the worker
waited forever. Every subsequent request parked behind it: one throw and the
whole server was dead until the app restarted.

Found by the 2026-08-08 P0 audit, verified against the code: exceptions are
enabled in both the simulator and iOS builds, so the outcome is a hang rather
than an abort.

**Fixed** by moving the signal into a scope guard, so it fires on normal return
and on exception unwind alike. `tests/dispatch_signal_test.cpp` pins it, and its
FIRST assertion proves the trailing-statement form still hangs — if that ever
passes, the test has stopped exercising the bug. Verified against the running
server too: 20 consecutive requests all return 200 where a parked worker would
hang after the first.

Noted, not fixed here: `ESP.restart()` from a handler does not return, so the
guard is skipped (longjmp on iOS) or the whole process is replaced (execvp on
desktop). The parked worker is orphaned by the reboot — a per-transfer thread
and socket leak on iOS, but not the permanent hang the throw was. Tracked as
S-013.


**The heap half is fixed; the other five reversals stay open.**

`ESP.getFreeHeap()` returned a flat 1 MB, so the firmware's low-memory branches
— the background page build (`EpubReaderActivity.cpp:268`), the plane buffer
(`:1692`), retaining a mini font (`SdCardFont.cpp:121`), image decode
(`ImageBlock.cpp:152`), the JPEG path and the CSS parser (`CssParser.cpp:693`)
— could not run at all. [src/SimulatorHeap.h](src/SimulatorHeap.h) replaces it
with two opt-in modes:

    CROSSPOINT_SIM_HEAP=380000      a budget that counts down as the firmware allocates
    CROSSPOINT_SIM_HEAP_FREE=40000  a pinned free figure

Measured: default still reports a flat 1048576 (every existing script is
untouched), the pin holds at its value, and the budget starts at 33,863 free of
380,000 and falls to 26,391 over ten seconds.

**Two honest limits, both found by measuring rather than assumed:**

- The accounting is **asymmetric**. Only a sized `operator delete` can know what
  to return, and `tests/heap_budget_test.cpp` caught libc++ freeing a
  `std::vector`'s buffer without going through it — so the budget drifts DOWN
  over a long run regardless of what the firmware frees. That is why the pin
  exists: a test wanting an exact number should state it, not allocate its way
  there. `malloc`/`free` are untracked, so vendored C (miniz, uzlib) is
  invisible.
- Fragmentation is not modelled, so `getMaxAllocHeap()` equals the free figure.
  Anything comparing the two — as `BleHidHost` does — is asking a question this
  cannot answer.

**Not demonstrated:** that a specific firmware branch fires under the pin. The
values the firmware reads definitely change, and the thresholds are now
crossable, but I did not get a book open under a low pin to watch one trigger.
The five remaining reversals in this entry are untouched.

### [S-002] Sleep/restart statics survive the iOS in-process reboot
**severity: medium · scope: iOS lifecycle · found 2026-08-07** · PARTIALLY FIXED 2026-08-07


`rebootAsPowerWake()` promotes the `*_AFTER_WAKE` schedules
(`src/SimulatorLifecycle.cpp:79`), but the consumers read the environment once
per *process* — `syntheticEventsInitialized` (`src/HalGPIO.cpp:186`) and
`screenshotEventsInitialized` (`src/HalDisplay.cpp:123`). Desktop re-execs, so
it works there; iOS longjmps into the same process, so the promotion is dead
code on the only platform that uses that path. `CLAUDE.md` states the promotion
unconditionally.

Two more of the same shape: `textEntryActive` survives a restart, leaving the
keyboard channel latched and the button map suppressed; and the jump skips
destructors, so a `RenderLock` held when `ESP.restart()` is called is never
released and the render task deadlocks on the first post-reboot frame.

**Close by:** resetting the process-scoped statics on the in-process reboot
path, and correcting the `CLAUDE.md` claim.


**Fixed for the statics half.** `src/SimulatorRebootResets.h` holds a registry
that `SimulatorLifecycle` runs immediately before both in-process jumps. HalGPIO
registers a reset for `syntheticEventsInitialized`, the pending
`syntheticEvents`, and `textEntryActive`; HalDisplay for
`screenshotEventsInitialized` and `screenshotEvents`. So the `*_AFTER_WAKE`
promotion now actually reaches its consumers on the phone, and a reboot taken
mid-text-entry no longer leaves the keyboard channel latched with the button map
suppressed.

`CLAUDE.md` no longer states the promotion unconditionally: it now says why the
desktop got it for free (`execvp` is a new process), and that anything caching
env-derived state behind a `static bool ...Initialized` must register a reset.

`tests/reboot_resets_test.cpp` pins the contract the lifecycle depends on —
everything registered runs, in registration order, and `runAll()` does not
consume the registry, because a process can reboot more than once.

**STILL OPEN, and why this entry stays:** the longjmp also skips destructors, so
a `RenderLock` held when `ESP.restart()` is called is never released and the
render task deadlocks on the first post-reboot frame. That is not a stale static
and a reset callback cannot fix it — it needs the lock either dropped before the
jump or made reentrant across it. Untouched here.

**Now fully fixed.** The statics half landed earlier; this closes the other one.

A `RenderLock` held when the longjmp fires never runs `xSemaphoreGive`, so the
mutex stayed locked by a thread that no longer existed and the render task
blocked forever on the first frame back. `std::recursive_mutex` offered no way
out — unlocking one you do not own is undefined, destroying one with a waiter
parked on it is worse — so the shim now implements the recursive mutex itself
over a plain mutex, a condition variable and an owner/count that
`simsemphr::forceReleaseAllForReboot()` can clear and wake. It runs beside
`simreset::runAll()` at both jump sites.

`tests/semphr_reboot_test.cpp` pins it, and writing it corrected the design
twice — both times because the test asserted the deadlock as a PRECONDITION and
the precondition failed:

1. Ownership by `TaskHandle_t` let any thread in. Threads not created through
   `xTaskCreate` share a handle, so an unrelated thread read as the holder
   re-entering.
2. Ownership by `std::thread::id` let the *probe* in. Thread ids are recycled
   once a thread ends — and a holder that ended without releasing is precisely
   this bug, so the replacement thread inherited its identity.

Ownership is now a per-thread token from a counter that only goes up. A give
from a non-holder is a no-op rather than a decrement, so a stale unwind after
the release cannot free somebody else's lock.

### [S-003] Route handlers run on the accept worker, not the firmware task
**severity: high · scope: web server / threading · found 2026-08-07** · FIXED 2026-08-08


`WebServer::handleClient()` is an empty function (`src/WebServer.cpp:677`), so
the firmware's poll does nothing and every route handler runs on
`impl_->worker` instead (`:643`). Two consequences: unsynchronised mutation of
firmware state and the framebuffer against the render task, and — worse —
`ESP.restart()` reached from a handler calls `std::longjmp(gRebootJump, 1)` on
iOS (`src/SimulatorLifecycle.cpp:146`) against a `setjmp` taken on the **main**
thread (`src/simulator_main.cpp:101`). Longjmp across threads is undefined
behavior, and `silentRestart()` is how every file transfer ends.

**Close by:** queueing handler invocations for `handleClient()` to drain on the
calling thread, which is what the device does.


**Fixed.** `handleClient()` is no longer empty. The accept worker now accepts
and parses only, parks the request behind a condition variable, and waits;
`handleClient()` drains it on the caller's thread and signals back, after which
the worker closes the socket. That is where the device runs handlers too.

The thread it lands on is the point: `loop()` runs on the MAIN thread
(`simulator_main.cpp:148`), which is the thread that took the `setjmp`. So a
handler calling `ESP.restart()` — which every file transfer does, via
`silentRestart()` — now longjmps on the right thread instead of committing
undefined behavior from a worker.

Two things the shape had to get right. The dispatch runs with the mutex
UNLOCKED, because a handler that restarts never returns and would otherwise
leave the worker blocked on a mutex nobody will release. And `stop()` sets an
abandoned flag before `join()`, or a worker parked on a dispatch that will never
be drained deadlocks the shutdown.

Verified against the running server: index, the file listing, a download and a
WebDAV PUT all succeed (the PUT's bytes land on the card), and the process exits
0 with nothing left alive. That the requests complete at all is itself the
thread evidence — `handleClient()` is now the only thing that dispatches, so if
it were not running they would hang.

### [S-004] `getFrameBuffer()` can return null and five callers dereference it
**severity: high · scope: display · found 2026-08-07** · FIXED 2026-08-07


`HalDisplay::getFrameBuffer()` returns `nullptr` while the buffer is lent out
(`src/HalDisplay.cpp:784`), and every consumer assumes non-null:
`clearScreen` goes straight into `memset(getFrameBuffer(), …)`
(`:532`), `refreshDisplay` into `snapshotBwBase` (`:612-614`), plus `drawImage`
(`:537`), `drawImageTransparent` (`:560`) and `composeGrayscalePreview`
(`:275`).

`frameBufferLent` is a **plain `bool`** at file scope (`:114`), written by the
borrower and read by the render thread with no synchronisation, so the window is
not even deterministic.

Dormant today: nothing in this repo calls `lendFrameBufferStorage`. It arms the
moment the firmware's decode path does.

**Close by:** deciding the contract — either the callers check, or the loan
blocks/copies instead of handing back null — and making the flag an atomic
either way.


**Fixed.** All five dereferences now check. The behavior on null is to skip,
not to substitute a buffer: whoever holds the loan owns those pixels, and the
lender's own refresh follows, so a skipped clear or blit repaints on the next
draw. `refreshDisplay` returning early matters most — converting a half-owned
buffer would have presented a torn frame rather than crashed, which is the worse
failure because it looks like a rendering bug somewhere else entirely.

`composeGrayscalePreview` keeps the last presented frame instead of compositing
from null.

### [S-010] `CROSSPOINT_NO_NETWORK` outlived the reason it existed
**severity: medium · scope: iOS features · FIXED 2026-08-07 · `d7e8b27`, firmware `f1459353`**

The flag excluded 16 TUs and gated Wi-Fi, File Transfer, font downloads and
Claude out of the iOS build. That was correct when it was written: the radio was
fake — `WiFi.scanNetworks()` returned a synthetic list and `localIP()` was
hardcoded to `127.0.0.1`, so File Transfer painted a QR code pointing at
loopback. That is B-008, the lying-control defect.

It stopped being correct at `4a98ba8`, which gave the target a real radio:
`CrossPointWiFi.mm` over NetworkExtension, in-process HTTP, Bonjour, and servers
bound to all interfaces on iOS. From then on the flag was suppressing features
that work — the mirror image of the defect it was introduced to fix.

Split into `CROSSPOINT_NO_DEVICE_FLASH`, which gates only OTA and SD Firmware
Update. Those write firmware to an ESP32 partition; no phone has one. The
exclusion list went from 16 TUs to 4.

Two conflations surfaced while mapping the guard sites, both accidental:
Bluetooth keyboard pairing sat inside the network guard (so Pair/Forget BT were
unavailable on iOS for no reason), and Download Fonts sat inside the OTA guard
(so it went out with firmware flashing rather than with networking). Both now
follow the surface they belong to.

**Verified:** `crosspoint_core` AND the `CrossPointX3` app target both link for
`arm64-apple-ios` with the network TUs restored — the app-target link is the
gate that matters, since a static library can hide unresolved symbols and that
is exactly where build 30 died. The two flash activities' absence is proven by
the same link: their rows and switch cases must be compiled out, or
`OtaUpdateActivity` could not resolve. Home renders all seven rows including
File Transfer and Claude; Settings shows Wi-Fi Networks. Device `gh_release` and
the desktop canary both build; 215/215 firmware tests, 6/6 simulator tests.

**Not confirmed on hardware:** that a transfer actually completes from another
machine. Linking is not the same as working.

**Depended on B-004.** Editing `platformio.ini` used to wipe every environment's
build directory, which is why this kind of change was avoided.

### [S-009] The pad contrast dial had its resolution in the wrong place
**severity: medium · scope: iOS settings · FIXED 2026-08-07 · `258bb14`**

Two reports, one cause: "missing all the steps between default and invisible",
and "I can't select black for dark".

Nine of the nineteen rows bought nothing, and the shim's own comment said so:
on the light side the paper is 4 levels off white, so `+1..+9` spanned
`FBFBF9 -> FFFFFD` — 1.00:1 to 1.03:1, several rows pixel-identical. Meanwhile
the two rows an owner most wants to choose between, the default (`-1`, 1.36:1)
and invisible (`0`), were **adjacent integers with nothing in between**. All the
resolution sat where nobody could see it and none where it mattered.

Those rows were spent on the gap instead. Light `+1..+9` now give 1.3 / 1.24 /
1.2 / 1.15 / 1.11 / 1.08 / 1.05 / 1.04 / 1.02; dark `-1..-8` give 1.38 / 1.29 /
1.22 / 1.16 / 1.11 / 1.08 / 1.04 / 1.02.

**Black was already reachable in dark** — level `-9` is field `121212` plus a
`-18` delta, i.e. `000000` — but its row read "Darker than the field — 1.12:1",
which names a ratio and never says black. Undiscoverable, not absent. It is
labeled `1.12:1 — black` now, and kept last because 1.12:1 against the field
really is low contrast; what earns it a row is that it vanishes into a
true-black page on OLED.

Ratios are computed from sRGB relative luminance rather than estimated, because
the delta tables and Root.plist's row labels have to agree — the standard the
existing comment sets. Root.plist is reordered strongest -> invisible, which is
display order only: `Titles` and `Values` are parallel arrays, so the stored
integers are unchanged and an existing selection still means what it meant.

**Verified:** the `+/-1` default rows are untouched, so a pad left alone is
pixel-identical; all six `static_assert`s (which pin the defaults and the 3:1,
black and white rungs) still hold, confirmed by compiling the shim rather than
by reading it; `plutil -lint` passes; every specifier still offers its own
DefaultValue. Both group footers, which described the old dead zone, were
rewritten — they were about to become false documentation.

### [S-008] `vTaskDelete` left the registry pointing at the handle it freed
**severity: high · scope: FreeRTOS shim · FIXED 2026-08-07 · `7370b10`**

`xTaskCreate` dedupes by task name on purpose — the iOS in-process reboot
re-runs `setup()` without tearing the process down, and a second `"render"`
task would orphan the first, leaving two threads writing one framebuffer. But
`vTaskDelete` freed the handle and left the registry entry behind, so the
create/delete/create sequence that reboot performs took the dedupe branch and
returned freed memory. The next `xTaskNotify()` is a use-after-free.

**Verified RED first** by `tests/task_registry_test.cpp`: without the erase only
one of two task bodies ran, because the stale dedupe returned early and never
spawned a thread. The assertion is behavioural rather than `new != old` — an
earlier version asserted pointer inequality and failed against the *fixed* code,
because the allocator reuses the just-freed block.

### [S-007] `String::toInt()` threw where Arduino returns 0
**severity: high · scope: Arduino shim · FIXED 2026-08-07 · `6f15ec6`**

It was `std::stoi`, which throws `invalid_argument` on empty or non-numeric
input and `out_of_range` past `INT_MAX`. Arduino's returns 0 and never throws,
so no firmware call site has a `try` — an uncaught exception took the whole
process down. `server.arg("page").toInt()` on a missing query arg reaches it
directly, since `argByName()` returns `String("")`.

Confirmed all three inputs throw under the old implementation. `strtol` matches
Arduino across six cases including `"12abc"` → 12.

### [S-006] `HalFile` leaked a `DIR*` for every directory it opened
**severity: medium · scope: storage · FIXED 2026-08-07 · `6f15ec6`**

`~HalFile` and `operator=(HalFile&&)` inlined only the fd half of `close()`, so
every `HalFile` holding a directory — `openNextFile()`, and `HalStorage::open()`
on a directory — leaked the handle. The SD font registry walks two roots and
Manage Files recurses, so a long session drifts toward `EMFILE`, which surfaces
as books that stop loading with an innocent file named in the log. Both now
delegate to `close()`, which already released both handles.

### [S-005] Long-press power-off fired while typing
**severity: medium · scope: input · SHIPPED 2026-08-07 · `fb49742` · UNCONFIRMED on device**

The text-entry suppression was implemented in `isPressed()` — with a comment
explaining why — and skipped in `getHeldTime()` and `getPowerButtonHeldTime()`.
POWER's host scancode is `p`, so with a text field open those two still read it
held. `buttonPressTime[]` compounded it: cleared only by `clearButtonState()` at
sleep entry, never on key-up, so a POWER press minutes earlier left a live
timestamp and the first `p` typed into a Wi-Fi password returned a hold of tens
of seconds — past the power-off threshold.

**Not headlessly verifiable, and not verified on device.**
`SDL_GetKeyboardState` is only written by the real-input path, so a synthetic
script cannot reproduce this at all. Compiles clean, desktop canary builds and
boots, six host tests pass — none of which is evidence the phone stops sleeping
mid-password.

**Close by:** on a build ≥ 33, tap POWER, open Settings > Device owner, and type
a word containing `p`. It should not sleep.

### [S-000] The deploy guard could not catch the bug it was written for
**severity: medium · scope: iOS deploy · FIXED 2026-08-07 · `94bd6a4`**

`ios/testflight.sh` regex'd every `GCC_PREPROCESSOR_DEFINITIONS` block in the
generated pbxproj and passed if **any** mentioned `SIMULATOR_DEVICE_X3`, with no
way to tell which target a block belonged to. Its own comment claimed "the
library's Release block is the one that governs", but no code selected that
block — so a define set `PRIVATE` on the app target alone still satisfied it,
which is exactly the split-brain build it exists to stop. That build shipped in
1–27.

Replaced with `xcodebuild -target crosspoint_core -showBuildSettings`, which is
scoped to the target and reports what the compiler is handed. Now also checks
`CROSSPOINT_RENDER_SCALE=2`, the other half of the same incident table.

**Verified** against the build-30 project: the two real defines report present,
while `SIMULATOR_DEVICE_X4_PRO` and `CROSSPOINT_RENDER_SCALE=1` report missing —
so the check reads real data rather than passing vacuously.
