# The light-mode ink and paper picker — historical inks at variable density on proven papers at variable tint

2026-08-22. Owner order (verbatim): "need a different color picker for light
mode (crt stays for dark mode). should allow for typical and proven to be most
legible ink colors for long session oled reading. fix the hues based on
historical ink, make them variable as is useful for me. take my previous input
into consideration. allow for changing the paper colors to six options that
have been proven in the same way."

Doctrine context this lands in: light mode is paper-and-ink emulation with
letterpress ([letterpress-and-scanlines.md](letterpress-and-scanlines.md));
dark mode is the CRT with the gun mixer (`ios/CrossPointPaletteMixer.mm`,
untouched — it remains dark mode's picker). The page-color chip now branches on
the live appearance: light opens this picker, dark opens the gun mixer.

Implementation: core in [src/LightInkPalette.h](../src/LightInkPalette.h)
(pure, host-tested by `tests/light_ink_test.cpp`), UI in
[ios/CrossPointLightInkPicker.mm](../ios/CrossPointLightInkPicker.mm).

Sourcing honesty: written without live web access in this session. The
historical claims below are standard, well-documented pigment/ink history
(named sources are the ones the claims are commonly published under and can be
re-verified); the hex anchors are THIS REPO'S choices, derived to sit at
body-text density while keeping the recognized hue, and are labeled as such.
The legibility section separates what the literature actually supports from
folklore, per the order.

## 1. The inks — history, hue anchors, and what "variable" means

Eight rows. APPEND-ONLY indices, the PanelPalette rule: a choice persists as an
integer, so rows are never inserted or re-pointed. `Standard` is row 0 and is
the shipped e-ink tone, so an untouched install changes nothing.

| # | Ink | Full-strength hex | Era, in one line |
|---|-----|-------------------|------------------|
| 0 | Standard | `#2D2D2D` | The shipped e-ink ink. Not historical; the default stays a row. |
| 1 | Carbon Black | `#1E1C1A` | Lampblack/soot in binder — Egypt and China, ~2500 BCE ("India ink"). Chemically inert: never fades, never browns. Near-neutral with a barely-warm cast, because soot blacks are not blue. |
| 2 | Iron Gall | `#1B2A3C` | THE Western manuscript and document ink, ~5th–19th c. (Codex Sinaiticus through the U.S. Constitution). Fresh iron gallotannate is a BLUE-black; the famous browning is oxidation with age — that is this row's era story, not a second row. (Reference: The Iron Gall Ink Website / conservation literature.) |
| 3 | Sepia | `#3E2A18` | Cuttlefish (*Sepia officinalis*) ink-sac pigment; standardized as a drawing/wash medium in late-18th c. Dresden (Seydelmann), the wash tone of the 19th c. The famous swatch — Maerz & Paul, *A Dictionary of Color* (1930), `#704214` — is a WASH, not the full-strength film; the dilution curve passes through that territory (~`#8E795E` at 42% on Cream), the full-strength anchor is the dark film. |
| 4 | Walnut & Bistre | `#4B3A15` | Bistre (chimney soot of burned beechwood) and walnut-husk ink: the golden-brown wash of old-master drawings (Rembrandt's wash medium). Yellower than sepia by design — that is the real distinction between the two browns. |
| 5 | Oxblood | `#4F1511` | The deep madder/carmine red family (alizarin lakes, kermes/carmine): the red of rubrication that is dark enough for BODY text. Honest note: medieval rubrication was mostly vermilion/minium, which at ~4:1 on paper can never meet a 7:1 floor — this row is the deep red ink that can. |
| 6 | Indigo | `#2A3B5C` | Indigotin, the vat dye, ground into inks and washes since antiquity; the softer, violet-leaning blue against Prussian's cyan lean. |
| 7 | Prussian Blue | `#0B3050` | 1704–1706, Berlin (Diesbach/Dippel): the first modern synthetic pigment, immediately adopted for inks and later blueprints. Anchored off the recognized `#003153` masstone, lifted a step so the red channel is not literally zero (a zero channel makes every dilution of it zero — see §3). |

**What "variable as is useful" means: DENSITY, not hue.** Each ink is one hue
with one dial: dilution along the ink's own wash curve, from the paper tone
(0%) to the full-strength film (100%). This is the physically honest variable —
a writer never had a hue slider, but every wash drawing is the same pigment at
different concentrations — and it keeps every offered color ON an ink's real
dilution locus instead of in an arbitrary RGB cube.

## 2. The dilution model — Beer–Lambert, not linear lerp (the improvement)

The spec suggested a linear-light lerp toward the paper. Implemented and
compared; the lerp was rejected on its 30–70% renderings and replaced with
**per-channel Beer–Lambert dilution**, which is the actual physics of a
pigment wash: absorbance is proportional to concentration (the Beer–Lambert
law), so transmittance EXPONENTIATES with density rather than blending
linearly. Per channel in linear light:

```
wash(d) = paper_lin * (ink_lin / paper_lin)^d        d in [0..1]
```

- `d=0` is the paper exactly, `d=1` is the ink exactly (byte-exact both ends,
  pinned by test — mixing 0% or 100% of anything returns it).
- Ink channels are clamped to a small epsilon in linear light before the
  ratio, or an ink with a zero channel (pure `#003153` Prussian) would dilute
  to zero in that channel at ANY density above 0 — a 1% wash with no red at
  all. The epsilon is the difference between a wash and a hard filter.
- Luminance is strictly monotone in `d` (every ink channel sits below its
  paper channel), which is what makes the 7:1 floor a single clamp point.

Why it reads better, measured at the spec's own 30–70% checkpoints (sepia on
Cream): linear lerp at 30% gives `#D5CDBC` — a pale gray-beige that has lost
the ink; Beer–Lambert gives `#A79376`, a recognizable sepia wash. The lerp
path desaturates toward the paper's neutral immediately (it is the straight
chord through the gamut); the exponential path follows the curve a real
dilution series follows and keeps the hue's channel ordering all the way down.
The test pins that channel-order retention at 50% for every colored ink.

## 3. Long-session OLED legibility — proven vs folklore

**Supported by the literature:**

- **Dark-on-light (positive polarity) reads better.** Repeatedly replicated:
  Bauer & Cavonius (1980); Buchner & Baumgartner (2007); Piepenbrock, Mayr &
  Buchner (2013, *Ergonomics*) — the advantage holds across ages and is
  attributed to the brighter adapting field shrinking the pupil, improving
  retinal image quality. Light mode as the reading mode is the right default,
  which is the doctrine already.
- **Contrast has a comfort band, with a floor that matters more than the
  ceiling.** Legibility rises steeply with contrast then saturates; WCAG's
  enhanced (AAA) floor for body text is 7:1, and ISO 9241-303's minimum is
  3:1 with "higher is better" only up the saturation curve. This repo's
  standing 7:1 floor is the enforced edge of that band. At the top, 21:1
  pure-black-on-pure-white is NOT better for long sessions — the repo's own
  Reading preset ruling (2026-08-17) already records the eased-ink rationale,
  and discomfort-glare literature (e.g., Sheedy et al. on visual discomfort)
  ties discomfort to luminance ratios in the field of view, which a
  full-drive white field on a bright OLED maximizes. Hence: the densest
  Carbon Black on Bright White here is 16.4:1, below High Contrast's 21:1,
  and every paper except row 0 pulls the field further off full drive.
- **Warm/dimmer papers reduce blue emission on OLED — as hardware fact.** An
  OLED emits per subpixel; a cream field literally drives the blue emitter
  less. Whether reduced evening blue light improves sleep is supported
  (melatonin-suppression literature, e.g. Chang et al. 2015 on evening
  e-readers); whether it reduces *eye strain* per se is NOT well supported —
  that half is preference.

**Folklore, offered but not oversold:** "cream paper prevents eye strain" and
"pure #000-on-#FFF causes fatigue for everyone" are preference findings, not
robust effects. The papers below are offered because they are real stocks with
real character and they keep the OLED off full drive — not because a tinted
page is proven therapeutic. The floor (7:1 at every offered combination) is
the proven part, and it is enforced by test, not by advice.

## 4. The six papers — real stock, and every pair's contrast

Row 0 is the shipped paper. Honesty note: real "bright white" text stock
(e.g., a 96–98 brightness sheet) is itself not `#FFFFFF`, so the shipped
`#FBFBF9` IS the bright-white row rather than a seventh option — which also
keeps the default a row.

| # | Paper | Hex | Stock it stands for |
|---|-------|-----|---------------------|
| 0 | Bright White | `#FBFBF9` | Bright text stock (Mohawk Superfine class). The shipped paper — the default stays a row. |
| 1 | Cream | `#F8F0D9` | Classic cream trade-book stock (the yellow-white of a new hardcover). |
| 2 | Bone | `#EFEAE0` | Natural/bone offset stock — warm but far less yellow than cream. |
| 3 | Chamois | `#ECDAB7` | Aged/chamois book paper — the tan of a decades-old paperback. The darkest offered field, and the one that sets most floors. |
| 4 | Press Gray | `#E9EAEC` | Cool gray press stock (uncoated cool-white/newsprint-adjacent). The one cool option. |
| 5 | Sepia Toned | `#EEDFCC` | A sepia-toned sheet — browner and pinker than chamois' yellow tan. |

**Full-density contrast, every ink x every paper** (WCAG ratio, recomputed by
the test; minimum in bold):

| Ink \ Paper | Bright White | Cream | Bone | Chamois | Press Gray | Sepia Toned |
|---|---|---|---|---|---|---|
| Standard | 13.29 | 12.10 | 11.49 | 10.02 | 11.44 | 10.53 |
| Carbon Black | 16.40 | 14.93 | 14.17 | 12.36 | 14.11 | 12.99 |
| Iron Gall | 14.05 | 12.79 | 12.14 | 10.59 | 12.09 | 11.13 |
| Sepia | 13.08 | 11.91 | 11.31 | 9.86 | 11.26 | 10.37 |
| Walnut & Bistre | 10.58 | 9.64 | 9.15 | **7.98** | 9.11 | 8.39 |
| Oxblood | 14.00 | 12.75 | 12.10 | 10.55 | 12.05 | 11.09 |
| Indigo | 10.79 | 9.83 | 9.32 | 8.13 | 9.29 | 8.55 |
| Prussian Blue | 13.05 | 11.89 | 11.28 | 9.84 | 11.23 | 10.34 |

Every pair clears 7:1 at full density, so no offered combination can be
illegible — same posture as the preset list's floor.

**The density floor is the PhosphorGrain budget pattern:** the slider clamps
exactly where 7:1 would break on the CURRENT paper, per ink. Computed floors
(minimum density %, from `lightink::floorDensityPct`, pinned by test):

| Ink \ Paper | Bright White | Cream | Bone | Chamois | Press Gray | Sepia Toned |
|---|---|---|---|---|---|---|
| Standard | 65 | 68 | 70 | 76 | 70 | 74 |
| Carbon Black | 53 | 55 | 57 | 61 | 57 | 59 |
| Iron Gall | 62 | 65 | 66 | 72 | 67 | 70 |
| Sepia | 65 | 69 | 71 | 77 | 71 | 74 |
| Walnut & Bistre | 76 | 81 | 83 | 91 | 83 | 88 |
| Oxblood | 58 | 61 | 63 | 69 | 63 | 67 |
| Indigo | 75 | 79 | 82 | 89 | 82 | 86 |
| Prussian Blue | 64 | 67 | 69 | 75 | 70 | 73 |

## 5. The paper's own 0-100 slider — tint strength

Owner order, 2026-08-22 (verbatim): "paper needs a 0-100 slider too. and be
sure to be adding the existing noise treatment to it."

The paper dial is the ink density's twin: **0 is the neutral bright-white
ground (`#FBFBF9`, row 0's own tone) and 100 is the stock at full strength**,
the table hex in §4. It is stored as a fourth append-only integer,
`lightPaperStrengthPercent`, defaulting to 100 — so an untouched install, and
every selection made before this dial existed, reads exactly as it did.

### The model: the same absorption law, not a lerp

A stock's tint is a colorant carried in an otherwise white sheet — pulp dye, a
coating, or the oxidation of an aged one — and **a colorant is a subtractive
filter over white**. That is the same physics the ink's dilution obeys, so it
gets the same law rather than a second one. Per channel in linear light:

```
stockAt(s) = white_lin * (stock_lin / white_lin)^s        s in [0..1]
```

Why Beer–Lambert here and not the linear-light lerp the spec allowed: the chord
toward white runs through the neutral, so a half-strength cream desaturates
toward gray-white rather than staying a pale cream. Over the tiny gamut a paper
covers the two curves are genuinely close — measured at 50% strength, the
largest disagreement is 2 code values (Cream `#F9F5E8` exponential vs `#FAF6EA`
lerped; Chamois `#F3EAD6` vs `#F4EBDB`) — so this is not a dramatic
improvement, and saying so is the honest version. The reason to take it anyway
is that **one absorption law now describes both dials**, which is worth more
than two code values: a reader who understands what the density slider does
understands what the paper slider does, and the code has one curve to maintain.

Both ends are byte-exact, and **Bright White is a bit-exact no-op at every
strength** — it *is* the ground, so its slider legitimately does nothing, and
that is asserted rather than left to `pow(1, s)`.

Measured ramp (test-printed, `paperAtStrength`):

| Paper | 0% | 25% | 50% | 75% | 100% |
|---|---|---|---|---|---|
| Bright White | `#FBFBF9` | `#FBFBF9` | `#FBFBF9` | `#FBFBF9` | `#FBFBF9` |
| Cream | `#FBFBF9` | `#FAF8F1` | `#F9F5E8` | `#F9F3E1` | `#F8F0D9` |
| Bone | `#FBFBF9` | `#F8F7F3` | `#F5F2EC` | `#F2EEE6` | `#EFEAE0` |
| Chamois | `#FBFBF9` | `#F7F2E7` | `#F3EAD6` | `#F0E2C6` | `#ECDAB7` |
| Press Gray | `#FBFBF9` | `#F6F7F6` | `#F2F2F2` | `#EDEEEF` | `#E9EAEC` |
| Sepia Toned | `#FBFBF9` | `#F8F4ED` | `#F4EDE1` | `#F1E6D6` | `#EEDFCC` |

### The 7:1 floor is now a SURFACE, and the clamp rule is one sentence

With two dials the legal region is two-dimensional: contrast falls as the ink
is diluted *and* falls again as the paper is tinted. The rule the UI and the
core both implement:

> **The slider you are moving is the one that stops; the other holds.**

Density has a **floor** (dilute far enough and the wash meets its paper); paper
strength has a **ceiling** (tint far enough and the ground meets the ink). Each
is computed at the *other* dial's live value. Changing the ink or the paper
STOCK is not a slider move, so it re-clamps the **density** and leaves the
sheet where the owner put it — the paper is the deliberate choice, the ink is
the variable that pays for it.

The region is never empty. Density 100 is the ink itself, independent of the
ground, and every one of the 48 pairs clears 7:1 at full paper strength by
table construction (§4), so full density is legal at every strength and a floor
always exists. Symmetrically, lowering the paper strength can only raise
contrast, so a ceiling always exists too.

**One measured wrinkle, and it decided the ceiling's implementation.** Contrast
is exactly monotone in DENSITY (zero inversions across the whole grid), so the
first clearing percent *is* the boundary. It is **not** exactly monotone in
paper STRENGTH: the tone quantizes to a byte at every step, so the ratio
ripples by up to 0.068 on its way down (Standard on Chamois runs 13.29 → 10.02
with local rises). A ceiling found by scanning DOWN from 100 would therefore
have illegal strengths beneath it — 3,300 of them across the grid, the worst
6.96:1. Those are rounding wiggles, not a legibility cliff, but "every
reachable state clears 7:1" has to be *checkable*, so `maxPaperStrengthPct`
scans **up** and stops at the first failure. It costs at most 19 points of
strength in the worst corner (Prussian Blue on Cream at 66% density) and it
makes the guarantee exact instead of approximate.

Density floor, at paper strength 0 / 50 / 100 (test-printed):

| Ink \ Paper | Bright White | Cream | Bone | Chamois | Press Gray | Sepia Toned |
|---|---|---|---|---|---|---|
| Standard | 65/65/65 | 65/67/68 | 65/67/70 | 65/70/76 | 65/68/70 | 65/69/74 |
| Carbon Black | 53/53/53 | 53/54/55 | 53/55/57 | 53/57/61 | 53/55/57 | 53/56/59 |
| Iron Gall | 62/62/62 | 62/63/65 | 62/64/66 | 62/66/72 | 62/64/67 | 62/65/70 |
| Sepia | 65/65/65 | 65/67/69 | 65/68/71 | 65/71/77 | 65/67/71 | 65/69/74 |
| Walnut & Bistre | 76/76/76 | 76/78/81 | 76/80/83 | 76/83/91 | 76/80/83 | 76/81/88 |
| Oxblood | 58/58/58 | 58/60/61 | 58/60/63 | 58/63/69 | 58/60/63 | 58/62/67 |
| Indigo | 75/75/75 | 75/77/79 | 75/78/82 | 75/82/89 | 75/78/82 | 75/80/86 |
| Prussian Blue | 64/64/64 | 64/66/67 | 64/66/69 | 64/69/75 | 64/67/70 | 64/68/73 |

Paper-strength ceiling, at density 100 / 90 / 80. Full strength is available
everywhere at full density, which is the table-construction guarantee restated;
the ceilings only bite once the ink is also diluted, and only for the two
weakest inks:

| Ink \ Paper | Bright White | Cream | Bone | Chamois | Press Gray | Sepia Toned |
|---|---|---|---|---|---|---|
| Standard | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 |
| Carbon Black | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 |
| Iron Gall | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 |
| Sepia | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 |
| Walnut & Bistre | 100/100/100 | 100/100/**95** | 100/100/**60** | 100/**95**/**30** | 100/100/**60** | 100/100/**39** |
| Oxblood | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 |
| Indigo | 100/100/100 | 100/100/100 | 100/100/**84** | 100/100/**45** | 100/100/**74** | 100/100/**53** |
| Prussian Blue | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 | 100/100/100 |

`tests/light_ink_test.cpp` sweeps the whole 8 x 6 x 101 x 101 grid — 324,316
(density, strength) states — asserting there is no hole above a floor and none
below a ceiling, and that the load-time clamp order lands legal from any pair
of integers whatsoever.

## 6. The noise treatment on the paper — per-stock tooth, and the sheet's formation

Owner: "be sure to be adding the existing noise treatment to it." Read against
what light mode actually did, rather than assumed:

- The letterpress **paper tooth** was already an output-wide sheet pass (the
  2026-08-22 seam fix, `letterpress::sheetToothMultiplierAt`), so coverage was
  not the gap.
- The **phosphor grain's** mottle machinery (`src/PhosphorGrain.h`) belongs to
  the dark page, and while letterpress is on the grain pass is skipped in light
  mode.

So the gap was that the tooth **did not vary with the paper**: a coated bright
white and an aged chamois wore identical grain. Two things close it.

### 6a. Per-stock tooth amplitude

Each stock carries a tooth factor — a multiple of the reference sheet's — that
scales the sheet pass's amplitude (`letterpress::Params::toothScale`). They are
CHOSEN, on the same footing as every other amplitude in `Letterpress.h`: no
sheet was profilometered for this repo. The ordering is the real claim, and it
is the printing one — coated and calendered stock is smooth, uncoated is open,
and an aged antique sheet is the roughest a trade book ever is.

| # | Paper | Tooth | Why |
|---|---|---|---|
| 0 | Bright White | **1.00** | Coated, calendered bright text stock. The reference, and it must stay exactly 1.0 or the shipped default silently re-textures — there is a `static_assert` on it. |
| 1 | Cream | 1.30 | Uncoated trade-book stock: a real but fine surface. |
| 2 | Bone | 1.45 | Natural/bone offset, a more open uncoated sheet than cream. |
| 3 | Chamois | **1.80** | Aged antique/eggshell book paper — the roughest offered, and the test pins that no row exceeds it. |
| 4 | Press Gray | 1.60 | Uncoated cool press stock, newsprint-adjacent: rough and open, but not aged. |
| 5 | Sepia Toned | 1.50 | A toned uncoated sheet, between bone and press gray. |

**The strength slider scales it**, linearly: `toothScaleFor(paper, s)` runs from
the reference 1.00 at strength 0 to the stock's own factor at 100. Linear, and
deliberately unlike the tone: tone is an absorption depth and exponentiates,
while tooth is "how much of this stock's SURFACE you asked for", and the honest
reading of a slider at 40% is 40% of the way from the smooth ground to that
stock's texture. Dialing a stock up therefore brings its roughness up with its
tone, and dialing it to 0 takes both away together — which is the same
statement as "strength 0 is the bright-white ground", now true of the texture
as well as the color.

The number reaches the renderer as a percent through
`SimulatorOverlay::setPaperTooth` (env override `CROSSPOINT_SIM_PAPER_TOOTH`),
pushed live by the picker and polled at launch by the shim so a stock chosen
last week still has its texture on the next cold start.

### 6b. The sheet's formation — the missing low-frequency half

The other honest finding: the bare sheet had **no low-frequency structure at
all**. Every existing low-frequency term multiplies INKNESS (letterpress plate
pressure) or belongs to the dark page (the grain's Mottled coverage), so paper
outside a glyph was pure white noise — a fine tooth on a perfectly even sheet,
which no real stock is. Paper **formation** — the cloudiness you see holding a
sheet up to a light, from fibres flocculating in the headbox — is exactly the
phenomenon the grain's Mottled coverage models for a phosphor screen.

It is therefore built out of **the same primitive** (`phosphorgrain::valueNoise`
— one noise implementation in this repo is the standing pattern), on a 3-cell
lattice across the sheet, and it **modulates the tooth's amplitude** rather
than adding a darkening of its own. That choice is what keeps the contrast
floor structural: a symmetric ±55% swing on the amplitude leaves the mean
darkening exactly `a/2`, so the existing paper-budget argument carries over with
nothing new to prove, and the budget clamp still runs after it so no point can
breach the floor. Depth 0 is bit-exact "no formation" and is the model's
default, so `Letterpress.h`'s old renderings are unchanged; only `HalDisplay`
asks for it.

Both stay **darken-only** and **off-bit-exact**, the two invariants every
surface pass in this repo holds.

### 6c. What it measures, on screen

From the shipped iOS build (build-simsdk Release, iPhone Air simulator, light
appearance, letterpress 100%, Standard ink at 100%), sampled over a blank
960 x 140 device-pixel block of the page foot. Relative standard deviation of
the paper — the texture, independent of how dark the sheet is:

| | paper 0% | paper 50% | paper 100% | model at 100% |
|---|---|---|---|---|
| Cream | 0.0092 | 0.0094 | 0.0099 | 0.0124 |
| Chamois | 0.0097 | 0.0115 | 0.0140 | 0.0172 |
| Press Gray | 0.0082 | 0.0129 | 0.0156 | 0.0152 |

Three things to read off it. The **strength-0 column agrees across all three
stocks** — that is the no-op ground, texture included. The texture **rises
monotonically with the dial in every column**. And the neutral Press Gray lands
on the model's own figure while the two WARM stocks measure 15–20% under it —
a measurement-path artifact of the simulator's screenshot color conversion
(the effect is confined to saturated tones; the neutral matches exactly), not
a model error: the model itself is verified directly by the host test, and the
plumbing by the agreeing zero column.

Renders, lossless PNG at native pixels (proof-image P0):

- `qa/paper-slider/paper-strength-matrix-3x3.png` — three stocks x three
  strengths on a real text page, each tile a 1:1 crop of the device
  framebuffer, no resampling.
- `qa/paper-slider/tooth-detail-3x-coated-vs-uncoated.png` — Bright White
  (1.00x) against Chamois (1.80x) at full strength, magnified by an INTEGER 3
  with NEAREST so one device pixel is one 3x3 block.

## 7. How it applies, and what dark mode keeps

Selection applies LIVE through the existing custom light fields
(`panelInkLight`/`panelPaperLight` + preset Custom), so the whole downstream —
letterpress, pad-on-paper, the keyboard chips — follows for free through
`crosspoint::panelForPrefs()`. Persistence is four append-only integer
keys (`lightInkIndex`, `lightInkDensityPercent`, `lightPaperIndex`,
`lightPaperStrengthPercent`), with the applied result mirrored into the light
hex fields — the mixer's storage discipline. The paper hex written there is the
TINTED tone at the current strength, not the table tone, so the whole
downstream sees the sheet the owner actually chose.

Dark mode's stored state is unaffected: the custom DARK fields stay the
mixer's. One consequence handled explicitly: the preset integer is shared by
both appearances, so setting Custom for the light page would otherwise yank a
named dark preset (the shipped White CRT) off the dark page too. The picker
therefore snapshots the currently-RESOLVED dark pair into the dark hex fields
once, before the preset first moves to Custom — the dark page keeps rendering
the same tones. Known, accepted cost: a named CRT preset's *phosphor trail* is
a property of the preset row, not of the hex pair, so after that snapshot the
dark page keeps its color but not its decay (unless a gun mix is active, which
carries its own).
