# Phosphor screen grain

> **SUPERSEDED IN PART, 2026-08-22.** The owner's doctrine order — *light mode
> is paper-and-ink emulation with a letterpress experience, dark mode is CRT
> emulation, "replace mottled noise in dark mode with hyperrealistic
> scanlines"* — **overturns this file's 2026-08-18 "no scanlines" ruling for
> dark mode**, and replaces the grain as the default texture in BOTH modes:
> letterpress (light) and scanlines (dark), each skipping the grain pass while
> its dial is on. The grain machinery, its dials, its env vars and its test all
> remain — any mode whose new dial is OFF falls back to exactly the behavior
> documented here, which is also what keeps the desktop canary byte-identical.
> The "What was ruled out" table below is kept as the historical record it is.
> See [docs/letterpress-and-scanlines.md](letterpress-and-scanlines.md).

Added 2026-08-18. Model in [`src/PhosphorGrain.h`](../src/PhosphorGrain.h),
composited in `HalDisplay::presentIfNeeded`, host-tested by
[`tests/phosphor_grain_test.cpp`](../tests/phosphor_grain_test.cpp).
Rendered proof (real captures, every strength and coverage):
`https://claude.ai/code/artifact/6254c879-9342-4586-80e6-0f049974b2bf`

## The question this answers

Owner, 2026-08-18: *"the colors and persistence looks good, but it is flat.
would it make sense to do some gaussian noise distribution of value? or
scanlines? or some other consideration? i am more interested in crt inspired
beauty than accuracy, but the physical limitations of phosphors is very
important to me to guide this."*

The palette gets the phosphor's **color** right (CIE locus → band broadening →
gamut map, `src/PanelPalette.h`) and the accumulator gets its **decay** right
(`trailMsForPreset`, MAXIMUM-blend GPU accumulator). What was left is that a
real tube has no uniform areas at all: its screen is a settled layer of
phosphor **crystals** a few microns across, laid down out of suspension, and
coverage varies from spot to spot.

## What was ruled out, and why

| Candidate | Verdict | Reason |
|---|---|---|
| Bloom / halation | **NO** — owner ruling | *"i don't want any halation/glow/bloom. it doesn't aid legibility. it distracts from it for me."* |
| Scanlines | **NO** — owner ruling | Also a technical objection: a raster artifact rather than a phosphor one (a vector scope and a radar PPI have grain and no scanlines), and a regular grid beats against the phone's 0.7955 minification — the ST-008 moire, measured at 8.14 levels. |
| Shadow mask / aperture grille | **NO** — physics | Triads belong to a COLOR tube. P1, P3, P39 and every other monochrome preset here is a continuous layer with no mask. This is the choice a knowledgeable eye would call wrong. |
| Powder grain | **YES** | The one treatment that is a property of the phosphor itself AND legibility-neutral: it changes how much light a patch emits, never where that light lands. |

## The model

**It only ever darkens.** Coverage variation is a deficit against an ideal,
fully covered screen: a thin spot emits less, never more. So the composite is
`SDL_BLENDMODE_MOD` with a multiplier in `(0, 1]`. That is the physics, and it
is also the bug class this repo has already shipped twice — the page-turn flash
(build 90, ADD summing two pages) and the gray-background report (accumulator
BLEND at alpha 128 over pale paper) were both an additive pass lifting pixels
the page had left dark. A multiplier structurally cannot do that.

Because it is multiplicative it is **emission-weighted for free**: on a
dark-ground phosphor palette the unlit ground has no light to take away, so the
ground stays the ground and the texture lands on the lit strokes — which is
what a real tube looks like in a dim room, and is why this costs no contrast.
Turning the dial up is how you texture the ground.

**Applied at present time, in device pixels, drawn 1:1.** Not baked into the
1bpp→ARGB conversion. The panel is MINIFIED on a phone (0.7955 on an iPhone Air
at 3x); a regular field written into the framebuffer beats against that
resample. A field generated at the OUTPUT size and drawn 1:1 is never resampled,
so it cannot beat against anything. It is also fixed to the GLASS: it does not
rotate with the orientation, and it does NOT re-roll per frame (animated noise
is beam-current noise, a different phenomenon, and it would make a still page
crawl).

**It goes on LAST, over the WHOLE APP SURFACE** — and "last" includes after the
overlay. Owner ruling 2026-08-18: *"apply the grain to the ios app background
too, not just the panel."* It is one sheet of glass. Texturing only the page
left a grainy rectangle floating on a clean ground, which is the one arrangement
no physical screen has, so the field now covers the page, the button pad, the
bezel and the letterbox margins alike.

**The vignette follows the SCREEN, and that is a ruling, not a side effect.**
Owner 2026-08-19, asked directly because the full-surface change moved it there
without anyone choosing: corner dimming now darkens the pad's outer buttons and
the bezel along with the page. Kept, on the same one-glass argument that moved
the grain out past the panel — a vignette is a property of the tube's face, not
of the page on it. The dimming is capped at 30% (a real tube's corner runs
70-85% of centre), so the outermost pad buttons sit at worst about a third
darker than the middle ones.

Two alternatives were offered and declined: splitting the vignette so only the
grain's amplitude rises screen-wide while the darkening stays inside the panel
rect, and dropping the Vignette coverage entirely. Neither should be re-proposed.

There is no headless proof of this one and there cannot be: the pad is drawn by
the iOS overlay, which does not exist on the desktop, so nothing off-phone
renders it.

The ordering that already put it after the beam, the accumulator and the fade
was the physics — all of those are light leaving the phosphor, and its coverage
gates them — and extending past the overlay is that same argument applied to the
chrome the harness paints. A side effect worth knowing: a Vignette now darkens
the corners of the SCREEN rather than of the page, which is what a vignette
physically is.

Off-phone this is a no-op. The desktop has no chrome outside the panel, so the
output rect and the panel rect are the same and the frames are bit-identical —
verified by hash across the change.

### Numbers

| Constant | Value | Note |
|---|---|---|
| `kRealisticSigma` | 0.035 | RMS emission variation at 1x. **CHOSEN, not measured** — see below. |
| `kCellPx` | 1 | device pixels per grain cell — owner ruling 2026-08-19 |
| `kVignetteGain` | 3.0 | corner grain amplitude vs center |
| `kVignetteDim` / `kVignetteDimMax` | 0.10 / 0.30 | corner dimming at 1x, and its cap |
| blotch size / depth | owner-set | see below — no longer constants |
| `kMaxEffectiveSigma` | 0.45 | ceiling after the coverage gain multiplies in |
| `kMinMultiplier` | 0.05 | a dead pixel is a defect, not grain |

`kRealisticSigma` is **chosen, not measured**, and the file says so. Published
phosphor-screen specs give particle size and coating weight, not a granularity
RMS at viewing distance, and there is no tube here to photograph. 3.5% is where
texture is visible on an OLED at arm's length while moving mean luminance by
0.8σ = 2.8%, inside a rounding step of the page's contrast ratio. It is a taste
anchor with a physical justification, not a measurement.

`kCellPx` is **1**, chosen by the owner from five cell sizes rendered side by
side at the shipped settings — and it overturns what this document used to say.

The old argument was acuity: a single crystal subtends far below what an eye
resolves, so what you see on a real tube is the aggregate at the finest
resolvable scale, and therefore a 1px cell "renders as a uniform slight dimming
— the flatness this exists to fix."

Measured, that last step is simply false. Pixel-to-pixel difference on the White
page:

| cell | 1 | 2 | 3 | 4 | 6 |
|---|---|---|---|---|---|
| adjacent | **2.32** | 1.15 | 0.77 | 0.58 | 0.40 |
| 5 px apart | 2.31 | 2.29 | 2.29 | 2.27 | 1.92 |

1px has the *most* per-pixel variation, not the least. The aggregate argument was
about what the eye integrates, and the eye integrating a field is not the same
as the field being flat. The reasoning was plausible and the render disagreed.

Worth keeping the second row too: structure at 5px is flat through cell 4 and
only drops at 6, so anything past 4 is removing the effect rather than the
noise. That is the fact the choice was made against, not in spite of.

`kMaxEffectiveSigma` exists because the two dials otherwise MULTIPLY: at 10x
under Vignette the corner saw σ = 1.05, every texel there clamped to
`kMinMultiplier`, and the page lost its corners. Caught by the test's
"even at 10x the corner keeps most of its light" check, before it shipped.

## The mottle became two settings

Build 98 hardcoded 8 blotches across the page at a depth of 0.70. Measuring that
against the alternatives (48 captures, one rebuild per variant, all six
shortlisted phosphors — artifact `df228c9c`) showed two things:

- **Cell count barely registers.** At a fixed depth, 4, 8, 16 and 32 cells span
  only +0.28 to +0.45 percentage points of blotching, three of which are inside
  measurement noise of each other.
- **Depth is the whole effect**, and 0.70 was far more swing than the page
  wants: 0.35 → 0.70 → 1.00 moves it +0.14 → +0.42 → +0.71.

Owner ruling 2026-08-18 therefore replaced both constants with settings, and set
the offered depths an order of magnitude below what shipped:

| Row | Key | Offered | Default |
|---|---|---|---|
| Blotch Size | `phosphorGrainMottleCells` | 8, 16, 32 | 8 |
| Blotch Depth | `phosphorGrainMottleDepth` | 0, 0.03, 0.10, 0.30 | 0.10 |

Depth persists in **hundredths** (0, 3, 10, 30) because a picker stores integers
and 0 is a real choice that `-integerForKey:` cannot tell from an absent key.

**Depth 0 is exact.** A Mottled coverage at depth 0 renders byte-for-byte what
Even renders, and Vignette+Mottled at depth 0 renders exactly Vignette —
asserted in the host test at every cell count, and confirmed end to end by two
identical frame hashes. Without that, the bottom of the dial would be a silent
floor rather than off.

The same ruling cut the strength ladder to four: **Off, 0.3×, 1×, 3×**
(`0, 30, 100, 300`). The old 0.25×/0.5×/2×/5×/7×/10× rows are gone from the
picker. An install already holding one of those integers keeps rendering it —
the clamp still accepts 0..1000 — it simply has no row to show for it.

Worth recording for whoever revisits the top of that dial: at the old 10×
setting, **P11 Blue and P22R Red fell to 5.6:1**, under this repo's 7:1 floor
for a named preset. Nothing dropped under WCAG AA's 4.5:1, and the grain pass is
not covered by `panel_palette_test`, which is why it went unnoticed. The four
offered strengths do not go near it.

## The amplitude is per-palette

Owner ruling 2026-08-18, after noticing the grain was **not** phosphor-specific
when he expected it to be. It is also the better physics: phosphors differ in
particle size and coating weight, so one field for all 52 palettes was the
simplification, not the accurate answer.

**A low-contrast page cannot afford texture; a high-contrast one can.**
`darkeningBudget()` measures how large a sigma a given ink/paper pair can take
before its mean attenuation drags contrast to the 7:1 floor. Across the
shortlist that spans **7.2% (P11 Blue, already at 7.4:1) to 71.9% (P4 Gray at
13.9:1)** — a tenfold range one constant cannot represent.

`amplitudeScaleFor()` turns that budget into a multiplier on `kRealisticSigma`,
normalised so a median page still gets 3.5% at 1× and clamped either side.
Measured off the shipped renderer, all at 1×:

| | contrast | amplitude |
|---|---|---|
| P4 Gray | 13.9:1 | **1.33×** |
| P22G TV Green | 13.8:1 | **1.30×** |
| P3 Amber | 10.3:1 | **0.87×** |
| P11 Blue | 7.4:1 | **0.35×** (clamped) |

The clamps earn their place. Without `kMaxAmplitudeScale` a 13.9:1 page would
take twenty times the reference coating; without `kMinAmplitudeScale` P11 lands
near 0.5% and reads as "grain is broken on blue" rather than "blue is a page
with no room for it".

**The floor guarantee is structural, and the scale alone did not deliver it.**
The first version clamped only the amplitude and the test caught two breaches
immediately: a Vignette multiplies sigma by up to `kVignetteGain` at the rim,
and 3× on a page with almost no room goes under anyway. So `Params::budgetSigma`
is a hard ceiling applied **after** the coverage gain — that ordering is the
whole point, since the gain is what breaches it. The test sweeps every offered
strength against five pages including the two tightest and asserts none drops
below 7:1, which is exactly the failure the old global constant shipped at 10×.

The budget is measured off the **live** palette, so the field follows a polarity
flip and a palette change with nothing else being told. `PhosphorGrain.h` still
knows nothing about `PanelPalette` — it takes two luminances.

## A fresh screen every launch

Owner ruling 2026-08-18: *"generate new grain every start of app."*

The seed was a constant, so every install and every launch got the same coating
— which is the one thing a settled powder never does. It is now rolled once per
process from `std::random_device` mixed with the tick count, held for the life
of that process, and re-rolled on the iOS in-process reboot via a
`simreset::Registrar` (the desktop reboot is `execvp`, so a new process gives it
a new field for free; without the reset the phone would keep one coating for a
whole session and the two platforms would disagree about what "start of app"
means).

Per LAUNCH, never per FRAME. Re-rolling each frame is beam-current noise, a
different phenomenon, and it makes a still page crawl.

**`CROSSPOINT_SIM_GRAIN_SEED` pins it**, and any repeatable capture needs it:
with the seed free, two headless runs produce different frames and cannot be
compared. Verified both ways — two unpinned launches hash differently, two
launches at seed 12345 hash identically.

## The shipped defaults changed

Owner ruling 2026-08-18, from the settings screen he was actually running. A
fresh install no longer opens on the historical e-ink page:

| Row | was | now |
|---|---|---|
| Palette | Neutral · Default | **CRT · White** — P45 viewfinder, 12.8:1 |
| Page Fade | Off | **5 min** |
| Page Fade Depth | Readable (100) | **Dim** (75) |
| Beam Paint | Off | **67 ms** |
| Screen Grain | 1× | 1× (unchanged) |
| Grain Coverage | Even | **Vignette + Mottled** |
| Blotch Size | 8 | 8 (unchanged) |
| Blotch Depth | 0.10 | **0.30** |

`panel_palette_test` used to assert the palette default was `kPresetDefault`,
guarding "an untouched install is pixel-identical." That premise is retired on
purpose; the assertion now pins `kPresetWhiteCrt` instead, because its real job
is unchanged — the default must never move by accident, only by decision.

**This is the iOS default only.** The desktop seeds every one of these dials to
off through its setters (`setPageFade(0)`, `setBeamPaint(0)`, grain at Even),
which is what keeps the canary and every headless capture rendering what they
always did.

## The settings

Two rows, iOS Settings.app only — none of this reaches device firmware.

| Row | Key | Stored | Default |
|---|---|---|---|
| Screen Grain | `phosphorGrainPercent` | percentage of realistic, 0..1000 | 100 |
| Grain Coverage | `phosphorGrainCoverage` | `phosphorgrain::Coverage` integer | 0 (Even) |

Strength persists as the **meaningful value**, not a row index, so the picker
can gain steps without re-pointing an existing choice. Coverage persists as the
enum, so rows APPEND and never insert.

Desktop/headless: `CROSSPOINT_SIM_GRAIN` and `CROSSPOINT_SIM_GRAIN_COVERAGE`,
seeded through `SimulatorOverlay::setPhosphorGrain` at init — the seventh dial
to need that, and the fifth time omitting it would have made the env override
dead code.

The coverages: **Even** (uniform, the default and the safe answer for the
non-phosphor presets that also pass through here), **Vignette** (grainier at the
rim with dimmed corners — a settled coating thins at the edge of the plate, and
the beam reaches a corner at an angle over a longer throw; real tubes measure
70-85% corner-to-center, and the cap here stops at the bottom of that range),
**Mottled** (low-frequency blotches — the suspension does not settle flat, so
coverage wanders over centimeters as well as microns; this is the one that most
kills flatness), and **Vignette + Mottled**.

## Measured on the composed frame

Sampled from `CROSSPOINT_SIM_SCREENSHOTS` captures — AFTER the fade, the
accumulator and the beam — not from `pixelBuf`. That distinction cost three
wrong flash measurements earlier in this project; the instrument has to overlap
the shipped path. X3, 528x792 native, P1 green (33FF33 on 001A00), reading page.

| Setting | Mean luma | Local Δ | Light lost |
|---|---|---|---|
| Off | 39.78 | **0.000** | — |
| 1/2x (50) | 31.81 | 0.472 | 1.9% |
| 1x (100) | 31.36 | 0.620 | 4.0% |
| 2x (200) | 30.44 | 0.911 | 6.8% |
| 3x (300) | 29.51 | 1.187 | 9.7% |
| 10x (1000) | 22.97 | 2.570 | 29.7% |

Off measures a local Δ of exactly 0.000: off is **bit-exact**, not nearly-off.
The 4.0% at 1x is above the model's 2.8% by about half a level, which is the
integer truncation in an 8-bit `dst*src/255` modulate — invisible, but it is why
the figures do not match the arithmetic exactly.

| Coverage at 3x | Mean luma | Local Δ | |
|---|---|---|---|
| Even | 29.51 | 1.187 | reference |
| Mottled | 29.42 | 1.201 | same mean — grain redistributed, not added |
| Vignette | 24.49 | 1.631 | corners dimmed |
| Vignette + Mottled | 24.34 | 1.646 | both |

## The bug this shipped with for one measurement

The four coverages first rendered **byte-identical** frames. Cause:

```cpp
const bool changed =
    grainStrength.exchange(s) != s || grainCoverage.exchange(c) != c;
```

`||` short-circuits. The only call that ever changes coverage also changes
strength, so the left side was true and the coverage **was never stored**. Two
separate `bool`s now. Nothing but comparing the rendered frames could see it:
the setter was called, the log line printed the right coverage, and the atomic
silently kept its old value.

## The blotch settings, 2026-08-20

Owner ruling, verbatim: *"default to 5 phosphorGrainMottleCells, remove that as
a setting, fix presentFlash (it didn't work on my first try), default
phosphorGrainMottleDepth to 90."*

| | was | now |
|---|---|---|
| `kMottleCellsDefault` | 8 | **5**, and no longer settable |
| `kMottleDepthDefault` | 0.10 | **0.90** |

**Cells is gone from both settings surfaces** — the `Root.plist` row and the
`settings.json` template key — not just defaulted. The count decides the SIZE of
the blotches relative to the page, which is a property of the paper rather than
a taste dial; depth (how hard they swing the grain) stays settable and is where
the taste lives. `clampMottleCells` and the min/max constants stay, because the
value still has to be sane where it is used.

Removing a settable value means the getter goes too: `CrossPointPrefs_-
phosphorGrainMottleCells` was deleted rather than left orphaned, and both
callers now read `phosphorgrain::kMottleCellsDefault` directly.

`sim_settings_file_test` asserts the template no longer carries the key, so a
re-added row fails the suite instead of quietly reappearing.
