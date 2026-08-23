# The power-off collapsing dot

2026-08-23. Roadmap item **D8**, "the one delight I would ship"
([surface-roadmap.md](surface-roadmap.md) §3). Model:
[src/PowerOffCollapse.h](../src/PowerOffCollapse.h). Test:
[tests/power_off_collapse_test.cpp](../tests/power_off_collapse_test.cpp).
Drawn by `SimulatorOverlay::stepPowerOffCollapse()` in `HalDisplay.cpp`, stepped
from `HalGPIO::startDeepSleep`.

**Dark mode only. Off by default. The one surface dial that is an iOS Settings
row rather than a frozen value.**

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
      -> display.deepSleep()              the held frame is flushed, transients settle
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

## The polarity latch — the non-obvious bug

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

## The shape of the animation

| Phase | Duration | What happens |
|---|---|---|
| Vertical collapse | 130 ms | the raster squeezes to a line; quadratic in time (the deflection amplitude follows the supply's discharge, so most of the travel is late); brightness rises to the 3x cap |
| Horizontal collapse | 190 ms | the line closes to a dot; the picture is gone |
| Fade | 700 ms | `10^(-t/tau)`, remapped onto [1, 0] so it keeps the curve's shape AND lands exactly on nothing |
| **Total** | **1020 ms** | measured on the desktop at 1028 ms |

`t = 0` is the **identity** — scales exactly 1, gain exactly 1, no line — so the
first frame of a collapse is byte-identical to the sleep screen and the
animation can never flash on its opening frame. The terminal state is exactly
black, not nearly black: a dot left at one part in a thousand would sit on the
glass all night.

## Drawing

Four draws over a black clear (black, not the field colour: a tube with no
supplies is not a dark page, it is an unlit screen, and the surround has to go
with the picture or the collapse happens inside a lit rectangle).

1. the panel, squeezed about the presented page's centre;
2. the same panel again, additively, at `(gain-1)/(gainMax-1)` alpha — a colour
   mod cannot express a rise, `SDL_SetTextureColorMod` only ever attenuates;
3. the line/dot rect, in the live phosphor's own ink tone, additive;
4. `SDL_RenderPresent`.

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

**Status: SHIPPED — UNCONFIRMED on device.** The frames above are desktop
captures under the software renderer. What has not been observed is the thing
this feature is for: the collapse at 60 Hz on glass, and whether the wake still
feels immediate while it is running.
