# Raking light: tilt the phone to move the light across the letterpress (spike, 2026-09-25)

**Reworked 2026-09-26 -- read the dated section at the foot first.** The
spike below shipped an edge-only relight the owner could not see; the rework
adds four sliders and makes the sheet itself answer the lamp. Everything above
that section describes the spike as it was, and where the two disagree the
2026-09-26 section is current.

Owner ruling 2026-09-25: the first spike from
[research-novel-reading-interfaces-2026-09-24.md](research-novel-reading-interfaces-2026-09-24.md)
is **F28, raking light that follows your hand**. The letterpress deboss is lit
from a direction set by the device's tilt, so the relief of the impression moves
as it would under a desk lamp.

**Status: built and host-tested, desktop-verified. Device feel UNCONFIRMED.**
Nobody has tilted a phone running it yet. The iOS adapter compiles
(`-fsyntax-only` against the iPhoneOS SDK) but has not been linked into an
archive or run on a device. Surveyed at main `dbe49da`.

## What it is

- **Model:** `src/RakingLight.h` (pure, clock-free). **Test:**
  `tests/raking_light_test.cpp` (`run_all.sh -k raking_light`).
- **Where the light was fixed:** `letterpress::multiplierAt` computed
  `lightDot = (gx + gy) * 0.707`, a light from the framebuffer's top-left.
  **Finding:** the reader's default orientation is Portrait, and in Portrait
  the framebuffer's top-left is the screen's top-RIGHT (verified against
  `outputToPanel` in `SurfaceSheet.cpp`, and pinned in the test for all four
  orientations). So on the phone the deboss has always been lit from the
  top-right, not the top-left its comment says. That comment now says so.
- **The lamp:** fixed in the room, not on the phone. The pose the reader holds
  when the feature starts is the NEUTRAL (the first CoreMotion gravity sample,
  as `ios/TiltGestures.h` does it). At the neutral the lamp is at exactly
  today's direction, 35 degrees above the page. When the phone tilts, the lamp
  turns in the phone's frame by the same rotation gravity did: the minimal
  rotation from neutral to current gravity (gravity cannot see yaw), scaled by
  a gain of 2. Its in-plane direction gives the azimuth, and its in-plane reach
  gives the RAKE (relief depth). The rake is capped at today's depth.
  - Right edge down: the light swings counter-clockwise, toward the raised left
    side, and fades as the page turns toward the lamp.
  - Left edge down: the light swings clockwise and stays at full depth.
  - Both are asserted in the test.
- **Quantized:** 16 directions (22.5 degree steps, with index 0 on today's
  direction) and 9 rake levels. There is 0.15 of a step of hysteresis at every
  boundary, and a 0.3 s low-pass on gravity. Only a change of quantized level
  asks for a present.
- **What moves per pixel:** the deboss shadow falls on the paper side of the
  depression's walls that face away from the lamp, as before, but the lamp
  direction is now `shadowFor(dir)`. New: the ink side of a wall that faces the
  lamp gets back up to 35% of its ink-squeeze rim (`kRingReliefAt100`). That is
  what makes the ink squeeze catch light as well as the deboss.
- **Deliberately not lit: the paper tooth.** It is per-pixel uniform noise with
  no height field, so it has no lit side. Faking one would be a new effect, not
  this one.

## Plumbing

| Piece | Where |
|---|---|
| Split of `multiplierAt` into `termsAt` + combiner (byte-identical) | `src/Letterpress.h` |
| State, cache key, edge-only relight, the four `SimulatorOverlay` functions, the desktop hatch | `src/SurfaceSheet.cpp` (`rakingOn`, `rakingPacked`, `letterTexRaking`, `rakeField`) |
| Declarations | `src/SimulatorOverlay.h` (after `setPressPressure`), `src/SurfaceSheet.h` (`stepRakingLight`) |
| Dial row `RakingLightOn` (key `rakingLight`, env `CROSSPOINT_SIM_RAKING_LIGHT`, ships 0, desktop 0) | `src/SimulatorDials.h`; one `case` in `applyDialGroup` (`src/HalDisplay.cpp`) |
| Desktop hatch step, once per main-loop pass | one line in `HalDisplay::presentIfNeeded`, just after `screenshotDue` |
| iOS: its own `CMMotionManager` at 30 Hz, running only while `rakingLightWanted()` (switch on, light page, letterpress on), stopped on resign-active; it also polls the pref | `ios/CrossPointRakingLight.mm` (new, added to both lists in `ios/CMakeLists.txt`); 4 lines in `ios/CrossPointIOSShim.cpp` |
| Settings row: group **Raking Light**, toggle **Raking Light (Experimental)**, off | `ios/Settings.bundle/Root.plist` (after Ink: Plate Pressure); `CrossPointPrefs_rakingLight()` at the end of `ios/CrossPointPrefs.mm`/`.h`; pinned in `tests/dial_table_test.cpp` |

Desktop QA hatches (the Mac has no tilt). Each one implies the switch is on:

- `CROSSPOINT_SIM_RAKING_LIGHT_AZIMUTH=<deg>[,<rake 0..1>]` sets the screen
  degrees the light comes FROM, clockwise from the top.
- `CROSSPOINT_SIM_RAKING_LIGHT_SWEEP=<seconds per turn>` sweeps the light
  round the page.
- `CROSSPOINT_SIM_LOG_RAKING=1` logs each light change and each relight's cost.

## Cost: build once, relight many

A tilt must not rebuild the field. The field is ~1.67 Mpx at 2x and CPU-built,
and a full rebuild costs 170-190 ms. So `rakinglight::EdgeField` builds the page
once. It bakes every flat pixel, where the gradient is zero and the answer is
the same under any light, and keeps only the edge pixels' terms: the gradient,
the rim, the shadow depth, and the sum of everything direction-free. A change of
light relights the edges and re-uploads the texture.

Measured on the desktop X3 build at `CROSSPOINT_RENDER_SCALE=2`, 1584x1056
framebuffer, `CROSSPOINT_SIM_LOG_TIMING=1`, with a 4 s sweep (a quantized step
every 250 ms, 60 relights), on the real page below:

| | ms |
|---|---|
| Edge pixels kept | 114,737 of 1,672,704 (6.9%): ~2.75 MB of terms, plus the 6.7 MB field kept between builds |
| Full field build, switch OFF (legacy loop), first present | 171.9 |
| Full field build, switch ON (terms + edge list), first present | 193.2 (one sample each, about +12%) |
| **Relight + upload, first 3 steps** | **1.26-1.66** (relight 1.0-1.2, upload 0.2-0.4) |
| Relight + upload, steady state (median of 60) | 10.9 (relight ~9.9, upload ~1.0) |

The step from ~1.3 ms to ~10 ms happened about one second into the run. It
happened in every pass on the same thread at the same moment: the trail
accumulator's cached composite went from 14 to 41 ms too. The likely cause is
that macOS moved a windowless, dummy-driver process off the performance cores.
That is inferred, not measured. Either way a relight is 17-150x cheaper than
the rebuild it replaces, and it runs only when the quantized light changes, not
every frame. **Phone cost is unmeasured.** The same code runs on the main
thread there, where the app is foreground.

## What was checked

All measured 2026-09-25, from a clean clone of the firmware card. That meant
`cp -c` of `~/src/crosspoint-reader`, with its `platformio.ini` pointed at this
worktree, so the real firmware checkout and its `platformio.ini` were never
touched. The page was pinned to the frozen shipped light page (`5C332B` on
`F9F3E9`), with a `settings.json` holding the dial table's shipped values,
`CROSSPOINT_SIM_GRAIN_SEED=12345`, and `readerActivityLoadCount` reset before
every launch.

**OFF is bit-exact.** A 2x render with the switch off is md5-identical to the
same render from an unmodified `dbe49da` build:
`980ea0f8105259ccaaf177877c13a92c` for both. The same held at 1x with
letterpress off. Tests prove the split in `Letterpress.h` against a frozen copy
of the pre-split body: 1,000,000 random windows and params, 0 differ.

**Neutral is today's direction.** Switch on with no motion, and switch on at
azimuth 45 on screen, give the same md5. Against OFF they differ only by the
ink-side relief: mean 0.044 levels, max 7, 1.8% of pixels.

**Per-azimuth deltas against OFF** (whole 1056x1584 capture):

| light from | mean | max | >4 levels | page-mean level change |
|---|---|---|---|---|
| 0 (top) | 0.162 | 18 | 1.42% | +0.045 |
| 45 (neutral) | 0.044 | 7 | 0.19% | +0.032 |
| 90 (right) | 0.151 | 18 | 1.35% | +0.035 |
| 135 | 0.227 | 21 | 1.74% | +0.032 |
| 180 (bottom) | 0.310 | 26 | 2.28% | +0.045 |
| 225 | 0.347 | 22 | 2.60% | +0.033 |
| 270 (left) | 0.319 | 26 | 2.35% | +0.036 |
| 315 | 0.253 | 21 | 1.93% | +0.033 |
| 45 at rake 4/8 | 0.098 | 11 | 0.79% | +0.086 |

Every light leaves the page, on average, slightly LIGHTER than today (the rim
relief). None darkens it. The darkest pixel is unchanged (27).

**Contrast floor, 7:1.** The two properties every floor proof relies on are
proved per pixel in the host test, under all 16x9 lights, for three seeds, at
the heaviest offered press (strength 200, all parts at 2.0):

- Flat pixels (zero gradient) are byte-identical to the fixed light. That
  covers flat paper and flat ink, which are what `paperBudget`, `fieldselect`
  and `composition_test` reason about.
- No pixel is darker than the fixed light's own worst case at that pixel (full
  shade and full rim).

On the synthetic page the worst light's page-mean paper-side shadow was 0.00998
against the fixed light's 0.00895 (1.1x). The test allows up to 2x.

**Clean, and why:**

- The beam does not sweep on a relight. `beamShouldArm` fires on a content seq,
  and a relight is a present request, not a new seq.
- The text-entry hold still waives only the seq. A relight during typing
  relights the held field, which is consistent with the hold.
- The iOS in-process reboot resets the neutral through `SimulatorRebootResets`.

## What is left

1. **Device feel. UNCONFIRMED.** Turn on Settings > Raking Light, hold the
   phone as for reading, then roll it slowly left and right and tip it toward
   and away from you. What to observe:
   - The thin shadow inside the letters' edges moves round them.
   - Tipping toward the lamp (top-right at neutral) fades it.
   - Nothing flickers while the hand is still, which the hysteresis is there
     for.
   - Open questions: whether the gain of 2 feels right, and whether the
     35-degree lamp is too high or too low.
2. **Phone cost:** `CROSSPOINT_SIM_LOG_RAKING` lines in
   `diagnostics/firmware.log` give the relight ms on the device.
3. **The effect is subtle at 1:1** (max about 20 levels on edge pixels). It
   reads in motion rather than in a still. If it is too faint on glass, the
   lever is `kDebossAt100` or the Deboss Shadow slider. Do NOT raise the rake
   cap above 1: that would push the shadow past its budget.
4. **Not done:** tooth lighting (needs a height field); battery cost of the
   30 Hz stream (unmeasured); the settings-file template does not name
   `rakingLight` (legitimate, since the seed owns it).

## Proof figures (lossless PNG, native pixels)

- [raking-page-crops-1x.png](raking-light-spike-2026-09-25/raking-page-crops-1x.png)
  (EVIDENCE): 700x150 native crops at 1:1 with the 2x framebuffer, for OFF,
  45 (neutral), 135, 225, 315, and 45 at half rake.
- [raking-letters-x5.png](raking-light-spike-2026-09-25/raking-letters-x5.png)
  (EVIDENCE): "can d" magnified x5 nearest, lit from 45, 135, 225 and 315. The
  shadow sits on the paper just outside the stroke, on the side NEAREST the
  lamp. That is correct for a deboss: the depression's wall on the lamp's side
  faces away from it.
- [raking-diff-x8.png](raking-light-spike-2026-09-25/raking-diff-x8.png)
  (DIAGNOSTIC/CONTEXT): the signed difference against OFF, amplified x8 about
  mid-gray, for 135, 225 and 315. It shows where the shadow moved to and where
  it came from.

## 2026-09-26: variable settings, and the page answers the lamp

Owner report 2026-09-26, verbatim: *"improve simulation of raking to be based
on variable settings. it is not visible as is and the page itself could be
light sensitive too."* Surveyed at main `b40737c`; the desktop before/after
below was measured from a clean clone of the firmware card exactly as the
spike's section "What was checked" describes (as-shipped dials, the frozen
Sanguine-on-India light page, `CROSSPOINT_SIM_GRAIN_SEED=12345`, the card
restored and `readerActivityLoadCount` reset before every launch, the desktop
X3 at `CROSSPOINT_RENDER_SCALE=2`, 1056x1584 presented). The `before` binary
is `b40737c` unmodified; its OFF capture is md5 `980ea0f8105259ccaaf177877c13a92c`,
the same byte-for-byte as the spike's own OFF gate from `dbe49da`.

**Status: built, host-tested, desktop-rendered, iOS build compiles and links
(`cmake --build ... --target CrossPointX3`, 0 errors). Device feel
UNCONFIRMED. Nobody has tilted a phone running it.**

### 1. Why it was not visible: the "before", measured

The spike's whole effect was the deboss shadow -- one framebuffer pixel wide,
capped at today's depth (`kDebossAt100 * 0.99 * 0.68 = 0.10` of the paper's
light at a full-gradient edge, less on AA edges), moved from one side of each
stroke to the other. Across the FULL tilt range, whole capture, luminance,
against the neutral (what a tilt actually moved):

| before, vs neutral (az 45) | mean abs | max | >4 levels | >8 levels | mean signed |
|---|---|---|---|---|---|
| az 135 | 0.216 | 20 | 1.63% | 1.06% | -0.000 |
| az 225 (opposite) | 0.356 | 21 | 2.55% | 1.82% | +0.000 |
| az 315 | 0.244 | 21 | 1.83% | 1.23% | +0.001 |
| az 45 at half rake | 0.086 | 10 | 0.78% | 0.12% | +0.054 |

So the most any tilt could do was move 2.6% of the pixels by up to 21 levels,
with the page mean unchanged to three decimals, on edges the phone then
minifies (2x rendered, presented at ~0.8). That is the number behind "it is not
visible as is". It was also a design choice: the spike capped the rake at 1
("do NOT raise the rake cap above 1"), so a low lamp could never deepen the
shadow, and it lit nothing but the ink's edges.

### 2. What changed

Three things, all in `src/RakingLight.h` and `src/SurfaceSheet.cpp`; the model
stays pure and host-tested.

**The ink relief has a depth.** `multiplierFor(e, S, gain)`: the deboss is
`depth * shade * rake * gain`, with `gain` from the Strength slider and `rake`
no longer capped at 1 but at `kRakeMax = 3` (a lamp at grazing). At gain 1 and
rake <= 1 it is the spike's lighting to the byte (test 6 still proves no pixel
darker than the fixed light's worst case there); above that the shadow deepens
by exactly `gain * rake`, bounded by `kMinMultiplier`. The ink-side rim relief
is unchanged and still bounded by the rim itself.

**The rake is the lamp's elevation.** `rakeForElevation(e) = cot(e) / cot(35°)`,
exactly 1.0f at 35 degrees (the same `tan` expression over itself, so "neutral
is today's light" stays a statement about bytes). The gravity path now returns
the rotated lamp's true elevation (`asin(L.z)`), held at grazing (5 degrees)
below the horizon rather than snapping off. Quantization: **32** directions
(11.25 degrees, was 16) because the sheet's falloff is a smooth whole-page
gradient and 22.5-degree steps would show as jumps; 8 rake levels per unit up
to 24. `pack/unpack` still use `dir = v % 32`, which is why 32 is the ceiling.

**The sheet answers the lamp: the LAMP FIELD.** `rakinglight::LampField`, one
new MOD texture at HALF resolution (`kLampCellPx = 2`, LINEAR-scaled, since the
relief is smooth by construction and a nearest 2x would tile it), drawn over
the WHOLE output right after the sheet's tooth field -- page, card and pad,
one sheet under one lamp, the same ruling the tooth and the grain follow. Two
terms, both darken-only:

- *Falloff.* A lamp at `kLampDistance = 4` half-diagonals lights the near
  side of the sheet more than the far side: `E(p) = cos(incidence) / r^2`,
  evaluated on a 17x17 grid and interpolated, normalized so that under the
  reference lamp (35 degrees along the diagonal) the far corner is 1.0 of the
  page factor. At 35 degrees the corner-to-corner irradiance ratio is 0.37
  (`falloffRef` 0.705 on the desktop's 528x792 lattice); a lower lamp spans
  more and clips at the budget, a higher one less, straight overhead ~0.1
  (a faint radial vignette).
- *Relief.* A height field built once per page from the sheet's OWN formation
  clouds (the same `valueNoise` lattice and `'FORM'` seed lane as
  `letterpress::sheetToothMultiplierAt`, so the lamp reveals the clouds the
  sheet already has) plus two fiber-clump octaves at 12 and 48 cells across the
  short side. Not the laid furrows -- see the negative results.
  Its gradient is stored as int8 at RMS 1 (`kGradScale` 32 per unit) and the
  shading is Lambertian: slopes rising TOWARD the lamp face away from it and
  darken by `kReliefAt100 * rake * (grad . f)`. **The clump octaves are
  rotated 23 and 61 degrees off the screen's axes.** The first cut was not,
  and the whole-page render read as a diagonal hatch: value noise on a square
  lattice has its ridges along the lattice and a directional derivative draws
  the lattice. Rotating the two octaves by two unrelated angles removed it;
  `kReliefAt100` went 0.5 -> 0.35 at the same time because at 0.5 the sheet
  read as plaster. Both are chosen, not measured. The tooth's per-pixel hash
  stays unlit (white noise has no lit side); the finest lit structure is the
  48-cell octave, ~11 px on the desktop at 2x.

The two terms add, are scaled by the Page slider (`pageFactor`, 0.7 at 100),
clipped at 1, and multiplied by **the lamp's budget**: `lampBudget(afterShow)
= 0.75 * afterShow`, where `afterShow` is what the tooth, the wires and the
show-through leave the paper (the sheet pass's own chain). That is a PER-PIXEL
cap, not a mean bound, so the darkest lamp pixel alone clears the floor; the
marks receive `afterShow - lampBudget`, so the composite stays inside
`letterpress::paperBudget` by construction. With the switch off the share is 0
and the marks receive exactly what they did. On the shipped page: paper budget
0.293, after the tooth 0.251, after India's show-through 0.229, **lamp cap
0.172** of the paper's light (`[sheet] ... budget left 0.0573` in the log is
what the marks keep). The floor sweep in test 10 takes the wires' and
show-through's shares at their FULL declared bounds, three palettes (the
shipped page, the historical `2D2D2D/FBFBF9`, a pair at 7.01:1), and the
marks at their full share of what the lamp leaves -- so the chain is exactly
tight and the sweep can only pass if the lamp's darkest pixel stays inside the
share taken for it -- over every dial extreme and every light. The only slack
is the field's byte rounding (half a level of the paper's light, computed per
palette: 0.018-0.024 of a ratio point); worst margin +0.003. The first
version of the sweep left the marks out and had 25% of slack; the review
caught it.

**Switching on now changes the page at the neutral.** The spike's "neutral is
today's light" meant switching on moved nothing. That is no longer so on
either count: the ink's shadow at the neutral is the fixed light's DIRECTION
(dir 0, rake 1 at lamp height 100) but three times its depth, because Strength
ships at 100 -- it is exact only at Strength 0 (adversarial review 2026-09-26
caught the first wording of this) -- and the lamp field darkens the far side
of the sheet the moment the switch is on, because a darken-only falloff has
nowhere else to put the near side. Measured: the
neutral arm is a mean 20.9 levels darker than OFF (98% of pixels moved).
Deliberate -- the owner asked for the page to answer the lamp, and doctrine
forbids the lift that would keep the mean.

### 3. The four settings

Settings.app, one `PSSliderSpecifier` group each after the Raking Light
toggle (a slider has no title, the Ink group's precedent), 0..200, **all ship
100**, dial-table rows `Raking{Strength,LampHeight,TiltRange,Page}Percent`,
keys `raking*Percent`, env `CROSSPOINT_SIM_RAKING_{STRENGTH,LAMP_HEIGHT,TILT_RANGE,PAGE}`,
getters `CrossPointPrefs_raking*Percent` (absent key -> 100, pinned by
`tests/dial_table_test.cpp` against the plist DefaultValue AND the getter's
fallback literal), polled edge-triggered in `ios/CrossPointRakingLight.mm`.
Desktop default 100 too: none of them draws anything while the switch is off,
so every capture stays byte-identical (OFF md5 unchanged, above).

| Slider | 0 | 100 (ships) | 200 | Reaches |
|---|---|---|---|---|
| **Strength** | today's deboss depth (gain 1) | 3x | 5x | the panel field's edge relight only (`letterTexRakeGain` is a relight key, no rebuild) |
| **Lamp Height** | 12 degrees, rake capped at 3 | 35 degrees, rake exactly 1 | 58 degrees, rake 0.44 | the neutral light (and so the ink AND the sheet); re-derived from the last gravity sample on change |
| **Tilt Range** | 0: the lamp is pinned (a fixed raking lamp is still a raking lamp) | 2 degrees of lamp per degree of tilt (the spike's gain) | 4 | the gravity path only |
| **Page** | the sheet does not answer (the lamp field is white) | far corner at 0.7 of the lamp budget under the reference lamp, shaded slopes on top | 1.4: the far half clips at the budget | the lamp field only |

Measured at az 225 against the default, whole capture: strength 0 / 200 move
1.6% / 1.3% of pixels (edges only, max 37-38 levels); page 0 lifts the mean by
20.4 levels (back to the ink-only page) and page 200 lowers it 13.9; lamp 0
darkens 45% of pixels by a mean 6.7 (max 106 -- the deboss at rake 3 hits the
0.25 clamp) and lamp 200 lightens 88% by 6.5. So each slider moves the thing
its footer says it moves and nothing else.

### 4. The "after", measured

Default dials, same arms, against the neutral:

| after, vs neutral (az 45) | mean abs | max | >4 levels | >8 levels | mean signed |
|---|---|---|---|---|---|
| az 135 | 9.32 | 69 | 72.6% | 50.4% | +0.03 |
| az 225 (opposite) | 11.14 | 74 | 75.7% | 56.0% | +0.23 |
| az 315 | 7.23 | 73 | 63.0% | 35.3% | +0.15 |
| az 45 at half rake (tilted toward the lamp) | 6.64 | 37 | 88.1% | 22.2% | +6.64 |
| az 225 at rake 2 (tilted away) | 12.98 | 126 | 78.9% | 61.2% | -4.50 |

Before: a tilt moved at most 2.6% of pixels by a mean of 0.36 levels. After: a
tilt to the opposite side moves 76% of pixels by a mean of 11.1 levels, and
tilting away from the lamp deepens the shadows to 126 levels at the edges. The
page mean stays put across azimuths (the falloff swings, it does not sum) and
moves with rake, as it should.

Proof figures (lossless PNG at native pixels, native crops, integer NEAREST
where magnified, coverage and effect delta measured per figure) are in the
scratch proof directory `raking2/` named in the session, with `index.html`;
they are not checked in. Twelve figures: the OFF gate, a whole-page context,
the same native band before/after under four lights, the same letters x4
before/after, one figure per slider, and the signed difference maps.

### 5. Cost

`CROSSPOINT_SIM_LOG_TIMING=1 CROSSPOINT_SIM_LOG_RAKING=1`, desktop X3 at 2x,
software renderer, a 4 s sweep (a quantized step every 125 ms at 32
directions, 120 relights in 16 s):

| | ms |
|---|---|
| Lamp field gradient BUILD (once per page, 528x792 lattice) | 56-62 (build 55-60, relight 5, upload 0.04) |
| **Lamp field relight + upload, per step** (median of 120) | **6.6** (max 7.9) |
| **Edge relight + upload, per step** (median of 120) | **2.9** (max 4.5) |
| Present total on a relight present (median) | 40.5 |
| First present with everything built: panel 200 + sheet 106 + lamp 63 | 417 |

The lamp field's build is the one new per-page cost, ~60 ms on the desktop:
three noise octaves and a gradient over 0.42 Mpx. It is per PAGE TURN, not per
tilt, and it is not the field the tilt touches -- a tilt costs a lattice pass
and a 1.7 MB upload. On the phone the output is 1290x2796 (0.9 Mpx lattice),
so expect ~2.2x these figures: **phone cost unmeasured**. The sweep's step
count doubled with the directions (16 -> 32), which is the trade for a smooth
falloff; the hysteresis is unchanged.

### 6. Negative results, and what was checked clean

- **Axis-aligned clump octaves hatch the page.** Recorded above; the first cut
  is in this session's history, not in the tree. Rotation fixed it; a blur
  would have cost a pass.
- **A far-side rim shadow was considered and not drawn.** A raised paper rim
  around the bite would shadow the paper on the side AWAY from the lamp too.
  With no highlight to balance it (doctrine: no lift) a shadow on both sides
  of every stroke reads as a bold outline and blurs the one directional cue
  the deboss has. Not done.
- **Extending the bite's shadow past one pixel was considered and not done:**
  physically the wall's shadow falls onto the depression's floor, which is
  ink, so there is nothing to draw on the paper.
- **The laid furrows were in the height field and were taken out** on the
  adversarial review's arithmetic (2026-09-26): their pitch is ~3.7 output px
  on the desktop and ~4.5 on the phone, which a 2-px lattice aliases (the
  ST-008 beat in miniature); their height step per lattice point (~0.3) is an
  order above the finest noise octave's (~0.02), so after the RMS
  normalization the noise relief collapsed to a few int8 units and the "relief"
  on a laid stock was an aliased comb; and the two erf combs cost ~19M erf per
  page turn on the phone. The sheet field already draws the wires at full
  resolution, unaliased. Nothing shipped renders laid (India is wove).
- **Page 0 took the marks' budget** in the first cut, for a field that drew
  nothing; the share is now taken only when Page > 0 and that state is a
  sheet cache key. Invisible at the shipped defects 0; the review found it.
- **The tooth is still not lit,** for the spike's reason; the finest lit
  structure is the 48-cell octave.
- **The lamp field at 1:1 instead of half resolution** was not tried: the
  relief's finest octave is ~11 px, so a 2-px lattice loses nothing the eye
  can see, and the relight cost is a quarter.
- **Clean:** OFF is byte-identical before and after (md5 above, whole 2x
  capture). Flat panel pixels are byte-identical to the fixed light under every
  light and strength (test 6). The edge field's relight equals a full
  per-pixel lighting under a sequence of lights and gains (test 7). The
  quantizer's hysteresis is unchanged (test 5). The lamp field never lifts a
  pixel, never passes its budget, is white at page 0 and at budget 0, puts the
  bright side on the lamp's side for a top and a left lamp, shades a ramp
  rising toward the lamp and not the same ramp lit from the other side, and is
  a pure function of its inputs (test 9). `tests/run_all.sh`: 98 passed, 3
  skipped (the card-dependent sleep/wake shell tests), 0 failed.

### 7. What is left

1. **Device feel. UNCONFIRMED.** Settings > Raking Light on, all four sliders
   at 100. Hold the phone as for reading, then roll it slowly left and right
   and tip it toward and away from you. What to observe: the sheet's
   brightness slides across the page with the tilt (the whole glass, pad
   included); the letters' shadows deepen as you tip away from the lamp and
   fade as you tip toward it; nothing steps visibly at a still hand. If the
   sheet's texture reads as plaster, Page down; if the shadows are too heavy,
   Strength down; if the lamp swings too far for a comfortable tilt, Tilt
   Range down.
2. **Phone cost:** the `[raking]` lines in `diagnostics/firmware.log` give the
   lamp relight and the edge relight in ms; expect ~2.2x the desktop figures.
   The 30 Hz motion stream's battery cost is still unmeasured.
3. `kLampDistance`, `kReliefAt100`, the octave cells and the two rotation
   angles are chosen; no lamp or sheet was photographed.
