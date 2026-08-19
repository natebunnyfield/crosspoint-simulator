# Phosphor screen grain

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
resample. A field generated at the presented rect's size and drawn 1:1 is never
resampled, so it cannot beat against anything. It is also fixed to the GLASS:
it does not rotate with the orientation, and it does NOT re-roll per frame
(animated noise is beam-current noise, a different phenomenon, and it would make
a still page crawl).

**It goes on LAST**, over the panel and everything composited into it — the
beam's swept band, the accumulator's trail, the faded page. That order is the
physics: all of those are light leaving the phosphor, and the coverage of that
phosphor decides how much gets out.

### Numbers

| Constant | Value | Note |
|---|---|---|
| `kRealisticSigma` | 0.035 | RMS emission variation at 1x. **CHOSEN, not measured** — see below. |
| `kCellPx` | 2 | device pixels per grain cell |
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

`kCellPx` is 2 and not 1 for **acuity**, not cost: a single crystal subtends far
below what an eye resolves at any sane distance, so what you see on a real tube
is the aggregate at the finest scale you CAN resolve. A 1px cell renders as a
uniform slight dimming — the flatness this exists to fix.

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
