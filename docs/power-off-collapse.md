# The tube switching off, and coming back on

*(The filename predates the second half. It is kept because five places in two
repos link to it, and a dead link costs more than a stale name.)*

Two animations, **one Settings row**, and the second one fires only when the
first one ran. Part one is the collapse at sleep; part two is BZZT THONK at
wake. Owner ruling 2026-08-23: *"show crt powering on animation if power off
animation is enabled"*, refined the same day to *"only when there's a dot there,
then do the 'bzzt thonk' screen warmup animation."*

## Part one: the power-off collapsing dot

2026-08-23. Roadmap item **D8**, "the one delight I would ship"
([surface-roadmap.md](surface-roadmap.md) §3). Model:
[src/PowerOffCollapse.h](../src/PowerOffCollapse.h). Test:
[tests/power_off_collapse_test.cpp](../tests/power_off_collapse_test.cpp).
Drawn by `SimulatorOverlay::stepPowerOffCollapse()` in
[src/SurfacePower.cpp](../src/SurfacePower.cpp) (it moved out of
`HalDisplay.cpp` on 2026-08-25), stepped from `HalGPIO::startDeepSleep`.

**Dark mode only. Off by default. The one surface dial that is an iOS Settings
row rather than a frozen value.**

**It squeezes the screen that was there.** Owner ruling 2026-08-24: *"when power
off collapse is enabled, don't switch to showing sleep screen. use the existing
screen as source for the effect."* The page, the menu, whatever was on the glass
— that is what the tube switches off showing. See
[The source is the page, not the sleep screen](#the-source-is-the-page-not-the-sleep-screen).

## What it is

Cutting mains power drains a CRT's deflection supplies faster than its EHT
reservoir and its cathode drive, so for a moment the beam is still writing while
the sweeps are already collapsing. The vertical yoke gives out first: the raster
squeezes to a bright horizontal LINE at the centre. Then the horizontal sweep
dies and the line shrinks to a stationary DOT. Then the last of the beam current
bleeds away and the dot fades over roughly a second. Tube makers considered the
dot dangerous enough to the phosphor to patent spot-killer circuits against it.

The brightness rise is not a flourish — it is the same light. Cathode current
does not fall while the sweep collapses, so the same energy per frame lands on a
shrinking area. `gainAt` is `1 / verticalScale`, capped at 3x.

## Settings: A ROW, and why this one earns it

Every other surface dial has an answer that is simply right. This one has a
**trade**: turning it on means the tube switches off at sleep and the glass stays
DARK for the whole sleep, instead of holding the sleep screen — which is a real
feature with a book cover or a clock on it. Nobody may make that trade on the
owner's behalf, which is also why it ships OFF.

Since 2026-08-24 the trade is the whole of it: the sleep screen is not shown even
for the instant before the collapse. That is the ruling above, and it makes the
row's meaning simpler rather than larger — with it on, sleep is the tube going
out; with it off, sleep is the sleep screen.

It is also the shape the surviving Settings.app rows have after the 2026-08-23
purge: Zen Mode, the two sleep toggles, Read Aloud, Diagnostics — all behaviour
switches, no appearance dials. `Sleep > Power-Off Collapse`,
`PSToggleSwitchSpecifier`, default `false`.

`CROSSPOINT_SIM_POWEROFF_COLLAPSE=1` is the desktop override, and
`powerOffCollapse` in `settings.json` is the same value for a packaged Mac app.

## Where it runs, and why it cannot delay sleep

The animation does **not** run before the device sleeps. It runs INSIDE the
sleep loop:

    firmware enterDeepSleep()
      -> activityManager.goToSleep()      the sleep screen is rendered
      -> display.deepSleep()              displaySleeping = true, then present:
                                          FLUSHED with the dial off,
                                          DROPPED when the collapse will run
      -> powerManager.startDeepSleep()
           -> HalGPIO::startDeepSleep()   the terminal loop, 10 ms ticks
                processSyntheticEvents()
                queued taps -> wake
                quitRequested -> return
                wake edge -> rebootAsPowerWake()
                SDL_PollEvent -> real key -> rebootAsPowerWake()
                SimulatorOverlay::stepPowerOffCollapse()    <-- here
                SDL_Delay(10)

Nothing waits for it. The firmware has already handed over, every wake check
runs *before* it on every iteration, and a wake arriving mid-collapse abandons it
on the same iteration it arrives. The frames it draws are frames that would
otherwise not exist. It returns false the moment there is nothing left to draw —
disabled, a pale page, or finished — and then it is one predictable branch per
tick for the rest of the sleep.

It never fires on an ordinary page render because it is not in `presentIfNeeded`
at all.

## The source is the page, not the sleep screen

Owner ruling 2026-08-24. Two things carry it, and they are **not** redundant.

**1. The sleep screen never reaches the glass.** `presentIfNeeded` drops every
present from `deepSleep()` onward while the collapse is going to run — dropped
rather than held, because a frame left owed would land on the iOS wake, where the
reboot is a `longjmp` and `pendingPresent` survives it. The panel texture
therefore still holds the page the reader was looking at, the glass still shows
it, and the collapse squeezes that. With the dial off, or on a pale page, the
sleep screen flushes exactly as it always did. `[power] sleep screen dropped` vs
`[power] sleep screen flushed` says which happened.

**2. A kept copy of that page** (`sleepSourcePixels`, moved from `HalDisplay.cpp`
to `src/SurfacePower.cpp:94` on 2026-08-25 with the rest of the collapse's
drawing code), which the collapse re-uploads on the frame it starts. This is
what makes (1) immune to timing. The sleep screen's own present is held for
`kPresentHoldMs` and is
normally *still held* when `deepSleep()` runs — measured 2026-08-24, 30 ms of
hold with about 5 ms of it spent — but nothing guarantees the firmware reaches
`deepSleep()` inside that window, and one slow sleep entry would arm the veto a
frame late and silently put the sleep screen back into the collapse. The copy is
taken beside the ghost's, on the same guard as the polarity latch, and only when
`pixelBufSeq` moves: one copy per page turn, and none at all with the dial off.

## The polarity latch — the non-obvious bug, and why it survived the ruling

The obvious gate, "is the page dark right now", is **wrong**, and it was written
that way first.

By the time the sleep loop runs, the firmware has drawn its SLEEP SCREEN, and it
draws that in LIGHT polarity even when the reader was dark. Measured 2026-08-23:
`inverted=0, paper F9F9F8`, on a run whose every page turn had built a scanline
field. Asking "is the page dark" at the moment of collapse therefore answers
about the sleep screen, and a dark-mode-only artifact never fires once.

So `presentIfNeeded` latches `lastReadingDarkGround` on every present that is
not part of going to sleep, and the collapse consults that: the tube you were
looking at, not the screen that replaced it. `CROSSPOINT_SIM_LOG_POWER=1` reports
the bail reason once, because four of the five ways this returns false are silent
by nature.

**The 2026-08-24 ruling does not retire it, and that was checked rather than
assumed.** Suppressing the sleep screen's *present* does not suppress the
firmware's `setInverted(false)`: `SleepActivity::onEnter` calls it before it
draws anything, presents or no presents
(`crosspoint-reader/src/activities/boot_sleep/SleepActivity.cpp:45`), and
`panelIsDarkGround()` reads `display.isInverted()` live. So the question is still
answered by the sleep screen if it is asked at collapse time. What changed is
what the flag *means*: it is now the polarity of the frame the copy above kept,
latched on the same present and by the same guard, rather than a stand-in for a
frame nobody kept.

**A hazard found while proving this, pre-existing and NOT fixed here.** If a
present of the sleep screen does slip in before `displaySleeping` is set, that
present latches `lastReadingDarkGround` PALE and the collapse declines
altogether — `[power] collapse not drawn: the page being read was a pale ground`,
with the dial on and a dark page. Reproduced 2026-08-24 by scheduling a
screenshot inside the sleep-entry window, which forces the held frame out early:
4 of 12 runs. Ordinary use does not force that present, and every unforced run
took the hold. It is left alone deliberately — the fix is a decision about what
signal replaces "is the page dark", which is a larger question than this ruling
asked, and the kept copy already protects the *source* whichever way the race
goes.

## The shape of the animation

| Phase | Duration | What happens |
|---|---|---|
| Vertical collapse | 130 ms | the raster squeezes to a line; quadratic in time (the deflection amplitude follows the supply's discharge, so most of the travel is late); brightness rises to the 3x cap |
| Horizontal collapse | 190 ms | the line closes to a dot; the picture is gone |
| Fade | 700 ms | `10^(-t/tau)`, remapped onto [1, 0] so it keeps the curve's shape AND lands exactly on nothing |
| **Total** | **1020 ms** | measured on the desktop at 1028 ms |

`t = 0` is the **identity** — scales exactly 1, gain exactly 1, no line — so the
first frame of a collapse is byte-identical to the frame already on the glass and
the animation can never flash on its opening frame. The terminal state is exactly
black, not nearly black: a dot left at one part in a thousand would sit on the
glass all night.

## Drawing

`presentIfNeeded`'s own order — field, picture, chrome, glass — repeated, so the
frame the collapse opens with is the frame the present closed with:

1. clear to the **field colour** (`SimulatorOverlay::clearColor`, the paper
   tone), then fill the page's own rect black, because what the raster vacates
   is unlit glass and not paper;
2. the panel, squeezed about the presented page's centre;
3. the same panel again, additively, at `(gain-1)/(gainMax-1)` alpha — a colour
   mod cannot express a rise, `SDL_SetTextureColorMod` only ever attenuates;
4. the line/dot rect, in the live phosphor's own ink tone, additive;
5. the **chrome**, through `SimulatorOverlay::overlayDraw` — the button pad and
   the bezel on a phone, nothing on the desktop;
6. the **surround veil**, four black rects AROUND the page at `surroundVeil`
   (never one rect over it: veiling the page would undo the raster);
7. the **glass** — `scanTexture` or `grainTexture`, whichever the last present
   built, over the whole output;
8. `SDL_RenderPresent`.

### Panel and paper are painted at the same time — the 2026-08-25 report

Owner: *"panel and paper need to be painted at the same time on power collapse
and any other time, hold panel update if needed."*

Steps 1, 5, 6 and 7 above are that fix; before it there were only four draws,
over a clear to BLACK. That clear is a second, smaller composite than the one
`presentIfNeeded` had just put on the glass — no glass field, no chrome, no
paper surround — so all three vanished on the collapse's OPENING frame, before
the raster had moved at all. That is exactly the flash `stateAt`'s t = 0
identity exists to forbid, and the identity was only ever true of the MODEL:
nothing checked that the draw delivered it.

Measured on the desktop, X3 at 1x, dark, `CROSSPOINT_SIM_AS_SHIPPED=1` with
`CROSSPOINT_SIM_SCANLINES=0 CROSSPOINT_SIM_GRAIN=300` so the glass field is
large enough to see, `CROSSPOINT_SIM_GRAIN_SEED=7`, same `fs_/.crosspoint`
restored before each arm. Both frames come from ONE run: the last present and
the collapse's opening frame, identified by the `[present] #N` lines around each
capture.

| | last present → opening collapse frame | pixels moved >4 levels | ground of the page |
|---|---|---|---|
| before | mean luminance 36.83 → **47.32** (+28%) | **85.6%** | one flat tone over **80.4%** of the band |
| after | mean luminance 36.83 → **36.35** (−1.3%) | 25.5% | the same textured spread as the present (11.6 / 9.6 / 6.5% against 12.2 / 10.1 / 6.8%) |

The 25.5% that still move after the fix are glyph edges: that capture lands
about 20 ms in (rows 8–782 rather than 0–791), so the raster has already
squeezed by 2%. The ground — which the squeeze cannot move — is unchanged, and
that is the claim.

The argument for black was never wrong, only mistimed. A tube with no supplies
IS an unlit screen, so the surround still ends black; it now gets there on the
raster's own curve (`poweroff::State::surroundVeil`), which is zero at t = 0.
This is the exact mirror of the warm-up, which had already found and fixed both
halves of the same problem in the other direction — "PUT THE GLASS BACK ON"
(2026-08-23, a 2.7% luminance step at the handover) and "THE CHROME COMES UP
AFTER THE PAGE". The collapse simply never got either.

`[power] collapse composite:` reports what the opening frame was made of —
field colour, chrome drawn or not, which glass texture — once per run, because
a missing glass texture makes the guarantee silently false again and that is
precisely how this bug was produced.

### ...and "any other time" — checked, and the everyday paths are already atomic

Recorded so the next session does not pay for this again. Every other moment
where the page and the sheet could disagree was measured or traced, and none of
them splits across two frames:

| Moment | What was checked | Result |
|---|---|---|
| page turn, light | `CROSSPOINT_SIM_LOG_TIMING=1` across two turns | `panel BUILD 53.6 / sheet BUILD 32.3` on the SAME present, three times out of three. No frame carries a new panel field over a cached sheet |
| page turn, dark | same | `scanlines BUILD 38.3 \| readback yes 4.6` — the raster's readback is of the frame composed in that present, so it cannot describe an earlier page |
| screen entry | the sheet's cache key (`ensureSheetToothTexture`) | keyed on the screen identity, rebuilt in the present that first draws the new screen |
| palette change, polarity flip | `setPanelPalette` / `setPanelDark` | both the panel's reconvert and every field's cache key move together; the field keys carry `live.paper` and the ink→paper budget |
| the two-store race on those setters | thread audit | `simsettings::pollSettingsFile()` (desktop) and `applyPanel()` (iOS) both run on the MAIN thread, in the same loop as `presentIfNeeded`, so a present cannot land between `setClearColor` and the reconvert request |
| keyboard show/hide | the fields' `scaleKey` | the panel's presented scale changes, which is in the key, so the sheet rebuilds in the same present |
| text entry | `holdForTextEntry` in `ensureLetterpressTexture` | the panel field DOES hold its old glyphs while a field is open — deliberately, owner 2026-08-24 "remove eink delay", and the sheet holds with it because its key carries no seq |

So no present hold was added, and none is needed: the everyday composite is
already built and presented in one pass. The hold the owner authorised would
have been spent on a problem that is not there, and would have cost the ~130 ms
sheet rebuild on every page turn.

**The scales are in SCREEN terms and the dst rect is not.**
`SDL_RenderTextureRotated` turns the landscape framebuffer about the dst rect's
own centre, so in portrait the rect's width becomes the screen's HEIGHT and its
height the screen's width. Squeezing the picture vertically therefore narrows the
rect. Getting this backwards collapses the page sideways, which is a different
television.

## Photographing it headlessly

The collapse never goes through `presentIfNeeded`, so the due-screenshot check
runs inside `stepPowerOffCollapse` too. Without that the one moment this feature
exists for is the one moment headless QA cannot see — the same hole
`CROSSPOINT_SIM_LOG_PRESENTS` fills for the page-turn flash.

**And it keeps running after the animation ends.** The sleep loop owns the
thread, so `presentIfNeeded` is not called for the whole sleep, and since
2026-08-24 its own capture is behind the veto — so the terminal black screen
would otherwise be the one state a script cannot ask for. The finished branch
redraws black and captures rather than reading back a presented buffer, whose
contents are undefined.

**Which path took a capture is observable, and that is how a frame is proved to
be the collapse's.** With `CROSSPOINT_SIM_LOG_PRESENTS=1`, a capture serviced by
`presentIfNeeded` is followed immediately by its `[present] #N` line; one
serviced by the collapse has no line after it. Use this rather than guessing from
the timestamps — the tick at which the sleep loop starts moves by tens of ms
between runs, and a due screenshot forces a present, which perturbs the very
window being aimed at.

    CROSSPOINT_SIM_AS_SHIPPED=1 CROSSPOINT_SIM_DARK=1 \
    CROSSPOINT_SIM_POWEROFF_COLLAPSE=1 CROSSPOINT_SIM_LOG_POWER=1 \
    CROSSPOINT_SIM_INPUT_SCRIPT='3000:QTAP:RIGHT;4500:QTAP:POWER;9000:QUIT' \
    CROSSPOINT_SIM_SCREENSHOTS='5030:a.bmp;5090:b.bmp;5320:c.bmp;6000:d.bmp' \
      .pio/build/simulator_x3/program

One caveat, measured: under the dummy video driver and the software renderer each
collapse frame costs enough that a loop iteration runs ~130 ms, so the 130 ms
vertical phase lands in one or two frames and is hard to catch. That is the
renderer, not the feature; on Metal or on a phone the same phase gets ~8 frames.

## Measured, 2026-08-23

Desktop, X3 at 2x render scale, output 1056x1584, `CROSSPOINT_SIM_AS_SHIPPED=1`,
CRT White dark:

| Frame | Mean luminance | Lit geometry |
|---|---|---|
| picture | 47.879 | the whole 1056x1584 |
| line | 0.621 | rows 788–793, cols 148–906 |
| dot | 0.0024 | rows 788–793, cols 524–529 |
| fading | 0.0014 | the same 6x6 |
| final | 0.0002 | nothing above luminance 8 |

Duration 1028 ms, from the `[power]` log. Cost to a page turn: **zero** — it
never runs during one.

## Measured again, 2026-08-24 — the source

Desktop X3, 1x, output 528x792, `CROSSPOINT_SIM_DARK=1`,
`CROSSPOINT_SIM_GRAIN_SEED=7`, same `fs_/.crosspoint` restored before every arm.
Every collapse frame below is proven to have come from `stepPowerOffCollapse`
rather than from `presentIfNeeded`: with `CROSSPOINT_SIM_LOG_PRESENTS=1` a
capture made by the present path is followed immediately by its own `[present]`
line, and these have none.

| Frame | Mean luminance | Lit geometry | What it is |
|---|---|---|---|
| last present before sleep | 40.020 | the whole 528x792 | the page being read |
| collapse, early | 40.752 | rows 73–718 | the same page, squeezed to 81.6% |
| collapse, mid | 28.420 | rows 246–545 | the same page, squeezed to 37.9% |
| line | 0.827 | rows 394–396, cols 6–520 | |
| line closing | 0.148 | rows 394–396, cols 217–308 | |
| dot | 0.0024 | rows 394–396, cols 262–264 | 3 px = `kDotWidthFrac` x 528 |
| final | 0.00000 | nothing above luminance 8 | exactly black |

**It is the page and not the sleep screen, in numbers.** Undo the vertical
squeeze on the early frame by nearest-neighbour and correlate it against each
candidate (brightness-normalised, so the collapse's own gain does not enter):

| Collapse frame | vs the reading page | vs the sleep screen |
|---|---|---|
| early (81.6% height) | **+0.8925** | −0.0319 |
| mid (37.9% height) | **+0.6208** | −0.0175 |

For scale, the reading page and the sleep screen correlate −0.0195 with each
other: they are unrelated pictures, and the collapse is squeezing the first one.
With the dial OFF the same run holds the sleep screen instead — the stock logo
screen, mean 41.864, a different image in 100% of its pixels.

**Light polarity is untouched, byte for byte.** With `CROSSPOINT_SIM_DARK=0` the
dial-on and dial-off arms produce identical captures (md5
`6b7fcf2e…` reading, `e13bd4a1…` sleep screen), the log says
`sleep screen flushed` in both, and the collapse declines on a pale ground. The
veto's condition includes the collapse actually running, so a build that never
switches the tube off cannot lose its sleep screen.

## The contrast floor does not apply, and the substitute does

Every other pass here is held to 7:1 because it composites over a page being
read. This one composites over a page nobody is reading — it fires only after
the firmware has gone to sleep, and its terminal state is a dark screen. The
structural guarantee in its place is the pair the test pins: the first frame is
the untouched sleep screen **exactly**, and the last is exactly black.

## Failure modes the test exists for

- a first frame that is not the identity is a FLASH at sleep, the exact bug class
  the present-coalescing work spent a day on;
- a terminal state that is nearly-off leaves a lit dot on the glass all night;
- a non-monotone collapse reads as a bounce rather than as a failure;
- an uncapped gain is a white bar;
- a disabled animation that is not bit-exact identity changes what sleep looks
  like for every install that never turned it on.

Two more live outside the model, because they are about the SOURCE and the
model has no opinion about where its picture comes from — both are silent, and
both are checked by capture rather than by a unit test. (The veto is still in
`HalDisplay.cpp:2698`; the kept copy it protects moved to `src/SurfacePower.cpp`
on 2026-08-25, per the correction above.)

- a veto that fires when the collapse will not run takes the sleep screen away
  from an install that wants it, and nothing in the app says so (the light-mode
  byte-identity arm above is what catches this);
- a veto that arms a frame late puts the sleep screen back into the collapse,
  looking exactly like the feature never changed (the kept copy is what stops
  this, and the correlation figures are what would catch it).

**Status: SHIPPED — UNCONFIRMED on device.** The frames above are desktop
captures under the software renderer. What has not been observed is the thing
this feature is for: the collapse at 60 Hz on glass, and whether the wake still
feels immediate while it is running. Nor has the 2026-08-24 source change been
seen on a phone — where the sleep path is an in-process `longjmp` rather than an
`execvp`, so the dropped frame's `pendingPresent` clearing is the part to watch.

---

# Part two: BZZT THONK, the tube coming back

2026-08-23, the same day and the same switch. Model:
[src/PowerOnWarmUp.h](../src/PowerOnWarmUp.h). Test:
[tests/power_on_warm_up_test.cpp](../tests/power_on_warm_up_test.cpp).
Composited inside `HalDisplay::presentIfNeeded`, which calls
`simpower::compositeWarmUp()` in
[src/SurfacePower.cpp](../src/SurfacePower.cpp); `powerOnWarmUpFrame()` steps it
there. Both halves moved out of `HalDisplay.cpp` on 2026-08-25.

**Dark mode only. The same `Sleep > Power-Off Collapse` row, read through the
same atomic. No second row.**

## The trigger is a STATE, not an event — and what the state actually is

The first version fired on a power WAKE. The owner's refinement replaced that:
*"only when there's a dot there."* Not "was this a wake" — the tube must have
been switched off, by the collapse, on this glass.

So the honest question is what the glass holds after a collapse. **Measured
2026-08-23: nothing.** Brightest channel anywhere on the panel once the collapse
finishes is **19/255**, and that is the grain field over black, not a dot. The
collapse ends at *exactly* zero on purpose — "a dot left at one part in a
thousand would sit on the glass all night" — and that is an owner-facing trade
the Settings row exists for, so it was not reversed to make the trigger literal.

Two things carry the owner's sentence instead:

1. **A recorded state.** `stepPowerOffCollapse` sets `CROSSPOINT_SIM_TUBE_OFF`
   on the frame it *starts* — past every one of its own bails, so the flag means
   "this glass really did collapse to a dot". `HalDisplay::begin()` consumes it
   once per boot. It travels as an environment variable because it has to cross
   a reboot in two different ways: the desktop wake is `execvp`, where `environ`
   is what the child inherits and every static is reborn, and the iOS wake is a
   `longjmp`, where the statics survive but nothing is inherited. One mechanism
   covers both. The consume is what stops a second launch inheriting a
   switch-off that already had its warm-up.
2. **The DOT phase.** The animation opens by *relighting* the dot, at exactly
   `kDotWidthFrac` and exactly the panel centre — the collapse's own constants,
   pinned against them by the test. So on the glass there *is* a dot, and the
   warm-up starts from it. The seam is literal without leaving a lit pixel on
   an OLED for eight hours.

That gate also answers the polarity question for free. The collapse only ever
runs on a dark ground, so a boot that armed this was looking at a dark tube; a
cold launch, a wake with the dial off, a wake from a light page, a firmware
restart and a document-open relaunch all miss it, because none of them
collapsed.

**What it comes back TO, since 2026-08-24.** The page the collapse squeezed.
Measured on a full sleep/wake cycle that day, `wake-0-reading.png` against
`wake-4-settled.png`: the settled post-wake frame reproduces the pre-sleep page
to within **3 code values**, worst pixel, over 528x792 — mean absolute
difference 1.03, and **not one pixel** differs by more than 4.

It is NOT byte-identical, and the first writeup of this claimed it was, from a
comparison of the wrong pair (`dark-1-reading` against `wake-0-reading`, which
are the same capture and so prove nothing about the wake). What accounts for the
residue is documented and expected: `grainSeed()` is deliberately re-rolled on
every launch and across the iOS longjmp reboot, because two runs of the app are
two tubes, and on a dark page the scanline field's phase jitter, thickness
jitter and mottle all hang off it. The known figure for that is ~2.2 code values
between two runs at identical dials, which is what this is. Pin
`CROSSPOINT_SIM_GRAIN_SEED` and it goes away; a wake in ordinary use does not,
and should not.

The two halves also still meet at the dot — the
collapse's last lit pixels are rows 394–396, cols 262–264, and the warm-up's
relit dot is rows 394–396, cols 262–264. Before the ruling, the tube collapsed a
sleep screen and opened onto a page; now the picture that goes out is the picture
that comes back.

**The reverse of the collapse's polarity trap was checked, not assumed.** The
collapse had to latch `lastReadingDarkGround` because the firmware draws its
sleep screen in LIGHT polarity. The wake path does *not* have the mirror of
that: measured 2026-08-23, the wake's `Boot` activity enters and exits in 9 ms
**without presenting at all**, so the first post-wake present is already the
reading polarity. `lastReadingDarkGround` is therefore a guard here rather than
a latch, and its bail is logged.

`CROSSPOINT_SIM_POWERON_WARMUP=1` arms it on a plain desktop launch (the only
way to photograph it without a whole sleep/wake cycle) and `=0` suppresses it.
It is a QA hatch, not a second setting.

## Where it fires, and why it does not delay the wake

**On a wake out of a collapse, and nowhere else.** A cold launch is deliberately
left alone: it already spends its own latency on SDL, the card scan, the font
registry and pagination, and the collapse does not fire when the app QUITS
either, so a warm-up at launch would be an unpaired half.

Unlike the collapse, this one **is** a present — the firmware is booting
underneath it and the page has to be ready when the raster arrives. Nothing
waits for it: `presentIfNeeded` composes the finished page exactly as it always
did, and this pass then decides how much of it the tube can currently show. It
self-requests its next frame the way the beam and the glow trail do, and stops
asking the moment it is done.

**The heater is free.** The clock starts at the first frame that can show
anything, *less whatever of the heater the boot has already spent* — a cold
cathode and a booting firmware are the same dark glass, and charging the owner
twice for it is the one thing this must not do. Measured: **1357 ms** from the
`execvp` wake to the first present on the desktop, so the 50 ms heater is spent
seventeen times over before there is a frame. An in-process iOS wake may beat
it, which is why the phase exists rather than being assumed away.

## Skipping

Any fresh press abandons it and the page appears at once
(`SimulatorOverlay::cancelPowerOnWarmUp`, called from `HalGPIO`'s event pump and
from `injectButtonDown`). The collapse never needs this because the sleep loop
checks for wakes before it steps; this one stands between the owner and a page
he just asked for.

**Only a press DOWN may skip.** The release of the very tap that woke the device
can still be in the queue when the rebooted firmware starts pumping — on iOS it
is not even a new queue — so accepting an UP would skip the warm-up on every
wake, silently, and only on the phone.

## The shape

| Phase | Duration | What happens |
|---|---|---|
| Heater | 50 ms | nothing; the glass is black. Credited against the boot |
| **Dot** | 35 ms | the collapse's dot, relit at its own width, steady and full |
| **BZZT** | 140 ms | the gate flickers in seven unequal bursts, crackle streaks across the glass, and the line punches out sideways in four discrete steps |
| **THONK** | 120 ms | the raster slams to full height, overshoots into overscan by ~12%, bounces once under, and lands |
| Settle | 50 ms | the supplies sag ~6% under the finished page and recover to exactly nominal |
| **Total** | **395 ms** | measured on the desktop at 397–410 ms |

Neither beat is a ramp. The bzzt's line widens in *steps*, one per lit burst; the
thonk *overshoots* rather than easing in. A monotone ease-out passes every other
check and reads as a fade on the glass, which is the one thing the owner ruled
out — so the test pins the overshoot and the step count directly.

`t = 0` is **black**, which is exactly where the collapse left the glass, so the
two halves join with no seam. `t >= total` is the **identity**, exactly.

**It is not the collapse played backwards, except where it is.** Switching off,
the vertical yoke dies first (raster → line) and the horizontal second (line →
dot). Coming up, the supplies arrive in the order they can: a dot, then the line
scan, then the field scan. That ordering *is* the mirror, and it is why this
model has a `horizontalScale` where the first attempt did not. What is **not**
mirrored is the fade: a turn-on has no long decay, and giving it one was the
first attempt's mistake.

## The lesson that cost the crackle: a model finer than a frame is a lie

The first bzzt gate had **nine** bursts inside 80 ms. Four of them were 1.6 to
4 ms long. At 60 Hz — and at the desktop's ~14 ms present cadence — a burst
shorter than one frame falls *between* two frames and is never drawn. The model
was perfect, every unit test passed, and the rendered result was one dark gap
and one steady line. There was no crackle at all.

`kMinBurstMs` (one frame at 60 Hz) is now a constant and the test sweeps every
burst against it. `kBzztMs` was widened from 80 to 140 ms specifically to make
seven bursts fit above that floor. Nothing but a frame-length check can see this
class of bug: the state function is correct at every instant it is asked about.

## Drawing

Composited at the very end of `presentIfNeeded`, **after the grain and the
scanlines**, and that placement is not taste: the scanline field is built from a
READBACK of the composed frame and cached against the framebuffer's seq, so a
black or half-open frame reaching that readback would bake an all-dark
beam-current map and hold it until the next page turn.

- **Heater / Dot / Bzzt / Thonk** clear to **black** and discard the frame just
  composed — a tube with no raster is not a dark page, it is an unlit screen,
  and the surround has to go with the picture. Then: the picture (once the
  raster has height to carry it), the dot/line rect in the live phosphor's ink,
  the crackle streaks, and finally the glass field again.
- **Settle** keeps the composed frame and applies two things: four black rects
  *around* the page for the chrome veil, and a whole-output `SDL_BLENDMODE_MOD`
  rect for the sag.

**Putting the glass back on is not cosmetic.** The black clear throws away the
scanline/grain field, and without redrawing it the raster's own texture
*appears* at the handover — measured as a **2.7%** step in mean luminance
between the last thonk frame and the first settle frame. Both fields are fixed
to the GLASS rather than to the page, so redrawing them over a scaled raster is
not an approximation: they are the screen, not the picture.

**The chrome comes up after the page.** The letterbox margins on a desktop and
the button pad on a phone are not part of the firmware's raster and cannot be
scaled with it, so the veil holds them dark across the handover and lifts them
over the settle. Four rects *around* the page, never one over it — veiling the
page would undo the raster that just slammed open. On the desktop the panel
fills the window, so all four rects are zero-area and the veil is a no-op; it
exists for the phone.

**The settle may only darken.** `driveAt` touches nominal *exactly* at both ends
and never exceeds it, which is what lets that phase be a MOD pass over a page
someone is reading. The overshoot lives in the thonk, where the caller owns the
draw and expresses it over black. An additive pass over a dark ground is the
page-flash and gray-background bug class.

## The contrast floor does not apply, and the substitutes do

Like the collapse, this composites over a page in transition rather than one
being read, and it is over in 395 ms. The structural guarantees in place of a
7:1 floor are three, all pinned by the test:

- the first frame is **exactly black** — the state the collapse left;
- the last frame is the **identity**, exactly;
- the settle phase is **darken-only**, exactly nominal at both ends.

## Measured, 2026-08-23

Desktop X3, 528x792 output, `CROSSPOINT_SIM_AS_SHIPPED=1`, CRT White dark,
`CROSSPOINT_SIM_GRAIN_SEED=7`. Frames dumped one per present via
`CROSSPOINT_SIM_LOG_SCREEN` + `CROSSPOINT_SIM_SCREEN_DUMP`.

| Frame | Widest lit run on the centre band | Raster rows lit | Mean luminance |
|---|---|---|---|
| dot | **3 px (0.6% of width)** — `kDotWidthFrac` exactly | — | 0.005 |
| bzzt burst 1 | 134 px (25.4%) | — | 0.84 |
| bzzt gap | 0 | 0 | 0.000 |
| bzzt burst 2 | 265 px (50.2%) | — | 0.81 |
| bzzt gap | 0 | 0 | 0.000 |
| bzzt burst 3 | 396 px (75.0%) | — | 0.86 |
| bzzt gap | 0 | 0 | 0.000 |
| bzzt burst 4 | 528 px (100%) | — | 0.91 |
| thonk opening | full width | 337 / 792 | 34.25 |
| thonk overscan | full width | 792 (clipped) | 52.82 |
| thonk bounce | full width | 783 / 792 | 56.55 |
| settle sag | full width | 792 | 51.26 |
| **final** | full width | 792 | **55.356** |
| **dial off, same tick, same seed** | full width | 792 | **55.356** |

The last two rows are **byte-identical**, md5 `878aa8a0…` — the animation's
terminal state is the frame the same launch would have shown with the row off.

Four discrete width steps with three dark gaps between them: that is the bzzt.
A raster that reaches 792 rows, then 783, then 792: that is the thonk's bounce.

**Cost to a page turn: zero.** After it has run, `powerOnWarmUpFrame()` leaves on
its first line — two boolean loads. Measured over 60 presents around a page turn
long after the warm-up finished: median total present **2.48 ms** with it armed
against **2.39 ms** without (min 2.35 / 2.36, max 11.67 / 12.39). Within noise.

**The real wake path, end to end:** collapse finishes after 1034 ms → `execvp`
reboot → `[power] warm-up: boot already spent 50 of the 50 ms heater` → dot
relit at 3 px → `[power] warm-up finished after 402 ms`.

**The skip:** a `QTAP` mid-bzzt logs `[power] warm-up not drawn: a press skipped
it` and the next captured frame is the whole page at 55.356 — nominal.

**Light mode declines:** `[power] warm-up not drawn: the page this boot presents
is a pale ground`, and every frame is the untouched light page.

## Photographing it headlessly

The collapse needs its own screenshot hook because it never goes through
`presentIfNeeded`. This one does, so the ordinary hooks work — but at ~14 ms per
present the phases are short enough that a fixed screenshot schedule drifts
between runs. Dump every frame instead:

    CROSSPOINT_SIM_AS_SHIPPED=1 CROSSPOINT_SIM_DARK=1 \
    CROSSPOINT_SIM_POWEROFF_COLLAPSE=1 CROSSPOINT_SIM_POWERON_WARMUP=1 \
    CROSSPOINT_SIM_GRAIN_SEED=7 CROSSPOINT_SIM_LOG_POWER=1 \
    CROSSPOINT_SIM_LOG_SCREEN=1 CROSSPOINT_SIM_SCREEN_DUMP=./qa \
    CROSSPOINT_SIM_SCREEN_DUMP_AFTER_MS=0 CROSSPOINT_SIM_SCREEN_DUMP_COUNT=34 \
    CROSSPOINT_SIM_INPUT_SCRIPT='2500:QUIT' \
      .pio/build/simulator_x3/program

`CROSSPOINT_SIM_GRAIN_SEED` must be pinned for any A/B, as everywhere else.

**Figure rule for this feature:** the whole-frame captures are CONTEXT — their
subject is where light is on the glass, which is geometry. The dot and the line
steps are SPARSE subjects (a 3x3 dot is 7.7% of the tightest crop that shows any
margin at all, and that is its arithmetic ceiling), so they ship as tight
native-pixel crops magnified by an integer NEAREST factor with the factor named,
never as a page band.

## Failure modes the test exists for

- a last frame that is not the identity leaves every post-wake page permanently
  dim, and nothing in the app ever says so;
- a drive above nominal in the settle is an additive pass over a dark ground;
- a first frame that is not black is a flash at wake, and a seam;
- a bzzt whose bursts are equal is a strobe, not a fault;
- a bzzt burst shorter than a frame is never drawn — see above, it shipped once;
- a thonk that does not overshoot is a fade wearing the word's clothes, and no
  screenshot can tell those two apart;
- a dot that drifts from the collapse's own `kDotWidthFrac` breaks the seam the
  owner's trigger is named for;
- a disabled animation that is not bit-exact identity changes what every wake
  looks like for every install that never turned this on.

**Status: SHIPPED — UNCONFIRMED on device.** Everything above is desktop capture
under the software renderer at ~14 ms per present. What has not been observed is
the thing this feature is for: the bzzt at 60 Hz on glass, whether seven bursts
in 140 ms read as electrical rather than as a stutter, whether the thonk's
overscan is felt or only measured, and whether the wake still feels immediate
with 395 ms of tube in front of it.
