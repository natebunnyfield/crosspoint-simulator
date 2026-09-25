# Raking light: tilt the phone to move the light across the letterpress (spike, 2026-09-25)

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
