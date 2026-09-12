# Ink rounding and ink spread: the press reshapes the type

Status 2026-09-11, later the same day: **SHIPPED to TestFlight as six
Settings.app sliders, UNCONFIRMED on device.** Owner ruling on the proof page
below: *"ios app settings for rounding, spread and all other ink effects
0-200."* Model in `src/InkRounding.h`, host test `tests/ink_rounding_test.cpp`,
wired into the level-to-pixel conversion in `src/HalDisplay.cpp`, two rows in
`src/SimulatorDials.h` (`CROSSPOINT_SIM_INK_ROUNDING`,
`CROSSPOINT_SIM_INK_SPREAD`; `inkRoundingPercent` / `inkSpreadPercent` in
`settings.json`). On the phone: the **Ink** group in `Root.plist`, six
`PSSliderSpecifier` rows 0..200 -- Corner Rounding 0, Ink Spread 0, Impression
(the letterpress master, frozen at 100 since 2026-08-23 and live again) 100,
Ink Squeeze 100, Deboss Shadow 100, Plate Pressure 100. "All other ink
effects" was read as the letterpress master and its three press parts; the
paper effects (tooth, formation, drift, show-through, wires, defects) are the
sheet, not ink, and stay frozen. Rounding and spread shipped at 0 in build 187; since 2026-09-12 (owner, from
a screenshot of the six sliders: "default corner rounding to 45 and spread to
55, add labels") they ship at **45 and 55**, and each slider sits in its own
titled group -- `Ink: Corner Rounding`, `Ink: Spread`, ... -- because iOS draws
a `PSSliderSpecifier` with no title at all, so the group header is its label.
The desktop's TABLE default is 0, but a fresh desktop does not render 0: its
first-run `settings.json` carries the phone's values and the watcher applies
the file a second after writing it (verified from a clean directory on
2026-09-12, after this doc had claimed the opposite for a day). Bit-exact off
on the desktop is `CROSSPOINT_SIM_INK_ROUNDING=0 CROSSPOINT_SIM_INK_SPREAD=0`,
or a settings.json that names the keys at 0.

**Standing ruling 2026-09-12: a stored 0 migrates once.** A phone that opened
the Ink group on build 187 or 188 has 0 WRITTEN for both keys, and a written
value beats a registered default forever. Asked "migrate or slide by hand",
the owner chose the one-shot migration. `src/InkDefaultsMigration.h` decides
(pure, `tests/ink_defaults_migration_test.cpp`), `migrateInkDefaultsOnce` in
`ios/CrossPointPrefs.mm` applies it from `ensureDefaults`, gated by the hidden
`inkDefaultsMigration` marker at version 1. Only a written 0 moves, each key
on its own; a 0 chosen after the marker is set stays 0.
Getters in `ios/CrossPointPrefs.mm` (`inkSliderPercent`, shipped fallback per
row so a lost store cannot flatten the page), poll in
`ios/CrossPointIOSShim.cpp` (`pollInkEffects`), and the light drawer's press
parts now delegate to the same getters so its one apply cannot fight the
slider.

Proof page (native-pixel crops, one page at every rung):
https://claude.ai/code/artifact/7454f4d1-41c8-475a-aa9a-287a6848af58

## The ask

Owner, 2026-09-11, after build 186 carried Atkinson Hyperlegible Soft on trial
(Namesake's cut of Hyperlegible Next with every corner rounded in the
outlines): *"instead of Soft version of one font, let's make an ios settings
for rounding sharp corners and other letterpress simulation effects."* So the
rounding moves out of one font's outlines and into the renderer, where every
family gets it.

## What it is, and where it had to go

A morphological pass on the four-level page image: blur the ink coverage with
a small Gaussian, re-threshold with a gain derived so that a straight edge
lands exactly where it was (the pixel whose center is 0.5 px inside the ink
sees Phi(0.5/sigma) and is mapped back to full ink; its mirror back to paper),
requantize to exactly the four levels. A convex corner pixel sees
Phi(0.5/sigma)^2 and stays below full ink: that is the rounding. Concave
corners gain.

It lives **inside the framebuffer-to-pixel conversion**, before the palette
ramp, and NOT in the surface stack, because rounding a convex corner REMOVES
ink and every surface pass is a darken-only modulate. It is the one place a
pass lightens a pixel, and only because it reshapes ink rather than lighting
paper. Light pages only, following the letterpress doctrine. Both `setInk*`
setters raise `pendingReconvert`, the same mechanism as an inversion change,
because a new value changes nothing until the cached frame is converted again.

**Four levels in, four levels out** is a hard constraint (owner 2026-08-24,
"keep 4 levels, fidelity is the point"); the test pins it at every rung.

## Measured, 2026-09-11

X3 desktop simulator at the shipped 2x render scale (1056x1584 page), light,
as-shipped dials, `CROSSPOINT_SIM_GRAIN_SEED=7`, one prose page of
`ai-engineering-from-zero.epub`, card restored between arms. Ink fraction is
the whole page; the crop stats are a 200x65 px crop of "wrong." against the
baseline capture.

| Arm | sigma px | page ink | vs base | crop px moved >4 | compose ms |
|---|---|---|---|---|---|
| Off (baseline) | 0 | 7.64% | — | 0 | 24 |
| Rounding 50 (Subtle) | 0.75 | 7.39% | −3% | 1.4% | 135 |
| Rounding 100 (Standard) | 1.5 | 6.74% | −12% | 4.0% | 194 |
| Rounding 150 (Heavy) | 2.25 | 5.56% | −27% | 7.5% | 194 |
| Rounding 200 (ceiling, not a rung) | 3.0 | 4.64% | −39% | 10.0% | 200 |
| Spread 100 alone | 0.75 (spread floor) | 8.19% | +7% | 5.8% | 136 |
| Rounding 100 + Spread 100 | 1.5 | 8.48% | +11% | 7.8% | 197 |
| Rounding 150 + Spread 100 | 2.25 | 8.55% | +12% | 8.6% | 195 |

**What the eye said, from the 6x crops.** Standard rounding is visible and
reads as rounder type. Heavy alone breaks hairlines (the w's thin strokes, the
g's lower loop): a blur-and-threshold starves any feature thinner than about
2 sigma, which is ink starvation, not rounding. The combined arm (Standard +
Spread) is the one that looks like a press: corners rounded, hairlines intact,
slightly heavier. Spread is what pays the ink back.

## Negative results (do not re-derive)

- **The first ladder was 0.6 px at 100 and moved nothing the eye could see.**
  Subtle (0.3 px) changed zero pixels on a real page and Standard (0.6)
  changed 0.4% of a text crop. The page is already antialiased, so a corner is
  only visibly rounder once sigma is about one device pixel (the phone
  presents 2x at ~0.8). Recalibrated to 1.5 px at 100.
- **A fixed gain softened every edge into a 2 px ramp at heavy.** The gain has
  to be derived from sigma (above); the test caught this as mid-side pixels
  moving.
- **Spread as a global bias turned the whole sheet light gray** (81% of a
  text crop moved by 24 levels). It is now applied only where the blurred
  coverage is above zero; the test pins paper far from ink bit-exact at
  spread 200.
- **The fixed-point vertical pass carried two weight sums and was divided by
  one** — every near-ink pixel saturated black. Caught by the stem-width test.
- **Per-pixel "spread never lightens" is false** once a blur is involved: a
  faint 1 px fringe next to nothing can fall under the white threshold. The
  invariant that holds is total ink and stem width.
- **Skipping rows with no ink within the kernel radius does not pay** on a
  text page at this size; the compose went from 120 to 130 ms at the same
  sigma. Rows are not where the paper is.

## Cost

First version: 130–200 ms per compose on the desktop against 24 ms without,
processing the whole page. Second version, the one shipped: a NEAR mask (the
ink mask dilated by the kernel radius, two linear sweeps) and both blur passes
run only where it is set, integer over padded planes with no clamp in the
inner loop. **42–70 ms per compose** at Standard on the same page, output
pixel-identical to the first version (0 differing pixels on three arms). Still
unmeasured on a phone. A page turn there already costs ~130 ms of sheet
rebuild; this adds roughly a third of that. If it has to come down further:
the near fraction on a text page is the lever (a run list per row instead of a
byte mask, and a smaller kernel reach -- 2.5 sigma instead of 3 -- are the two
cuts not taken).

## Standing rulings, 2026-09-12

- **The defaults are the owner's slider positions.** Afternoon of the same
  day, from a screenshot of the six sliders set by hand: *"set defaults to
  these."* Read off the screenshot by pixel (knob center against the track,
  +/-2): Corner Rounding **27**, Spread **106**, Impression **68**, Squeeze
  **93**, Deboss Shadow **99**, Plate Pressure **125**. These replace the
  morning's 45 / 55 / 100 / 100 / 100 / 100 in `Root.plist`, the dial table,
  the getter fallbacks, the unreadable-plist registration, the migration's
  targets and the Mac template's two rounding rows. No second migration: an
  install that holds the morning's values keeps them, and the owner's own
  phone already holds these.

- **The phone reports the cost itself.** Asked whether each compose should
  write its cost to the diagnostics log: *yes.* While the Settings.app
  Diagnostics Log switch is on (or `CROSSPOINT_SIM_DIAGNOSTICS=1`), every
  antialiased compose logs `[compose] N ms for WxH (ink rounding ran: M ms,
  rounding R spread S)` through the SDL_Log tee into
  `diagnostics/firmware.log`; off, the line costs nothing (`firmwarelog::armed()`
  is polled, never cached). Proven headlessly on the desktop the same day:
  compose 50 ms, rounding 25 ms at 45/55 on a 1584x1056 page, and the line
  present in the teed file. Turn the switch on, turn a page, share the file.
- **The Mac apps match the phone.** The desktop `settings.json` template
  (`src/SimulatorSettingsFile.h`) ships `inkRoundingPercent` 45 and
  `inkSpreadPercent` 55, so a first-run Finder-launched bundle draws what the
  phone draws; an existing file keeps its values. **The command-line canary
  does NOT stay at 0**: it too writes and applies that template on first run,
  which this entry first claimed otherwise; asked about it, the owner ruled
  *desktop matches the phone everywhere* (2026-09-12). The other
  Ink values in that template (letterpress and the press parts at 0) are the
  desktop's historical seeds and were NOT part of this ruling.
- **Light only.** Asked whether Corner Rounding and Ink Spread should also
  apply on the dark page (a CRT's beam spot rounds corners too), or whether
  the dark page should get its own Beam Spot slider: *light only, as
  shipped.* Dark stays the tube -- scanlines, glow, beam. Do not re-propose a
  dark-page rounding pass; the polarity gate in `writePixelsFromLevels` is a
  ruling, not an omission.

## Found on the way, and what it turned out to be

`tests/test_note_editor_repaint.sh` failed on the current firmware pin with
"the typed text did not reach the note buffer", and failed identically on the
tree before this work. This section first blamed the firmware's `[NOTEEDIT]
no bonded keyboard; on-screen keyboard only` line as a new gate on host-typed
text. **That reading was wrong**, and it was wrong because it was inferred
from a log line rather than read from the code. Traced 2026-09-12 on the
owner's ruling: that line dates from 2026-08-06 (`c6faf1ace`) and only decides
whether BLE starts; host typing still drains through `consumeTypedText`. What
moved was the SAVE log, in firmware `fa7f0aaae` (2026-09-10, atomic note
saves): `saved %u/%u bytes` became `saved %u bytes to %s`, and the test's
grep for the old shape was what failed -- eleven bytes had plainly reached
the buffer. The test now greps the new line and additionally fails on a
`short write saving` line (simulator `e83cbed`). Lesson, again: a log line is
a symptom, not a mechanism.

## Decisions, as ruled 2026-09-11

All three below were answered by one ruling: every ink effect is its own
0..200 row; rounding and spread default 0; the letterpress master returns as
a row with its three parts. Kept for the record of what was asked.

### The questions as put

1. Which rows reach Settings.app: rounding alone, rounding + spread as two
   rows, or one coupled "Press" row where spread rises with rounding so the
   page's ink is conserved.
2. Which rung ships as default (0 today; the combined Standard arm is the
   candidate).
3. Whether the letterpress master (Off/Subtle/Standard/Heavy, frozen at
   Standard since 2026-08-23) returns as a row alongside, since the ask names
   "other letterpress simulation effects".
