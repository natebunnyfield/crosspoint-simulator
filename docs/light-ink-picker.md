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
untouched — it remains dark mode's picker). The page-color chip used to branch
on the live appearance: light opened this picker, dark opened the gun mixer.

> **FROZEN 2026-08-24.** That chip is gone and this drawer no longer opens on
> the phone (owner: *"remove the color button from single finger (not zen) mode
> ui"*). The light page is frozen at **Sanguine `5C332B` on India `F9F3E9`**,
> derived in [src/FrozenPage.h](../src/FrozenPage.h). Everything below still
> describes the model correctly — only the way in is gone. See §8.

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

Eight rows **as first shipped; ten more were appended 2026-08-22 — see §9,
which is the authoritative table.** APPEND-ONLY indices, the PanelPalette rule: a choice persists as an
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

> **The paper table below is the ORIGINAL six, kept because §5 and §6 quote its
> hex values. Six more were appended 2026-08-22 — see §9b for those. For contrast
> figures go straight to §9e, which is the complete 17 x 12 grid recomputed by
> the test on every run; the 8 x 6 grid that used to sit here was a subset of it
> and is deleted (2026-08-23) so a top-down reader cannot mistake it for the
> current one.**

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

Every pair clears 7:1 at full density, so no offered combination can be
illegible — same posture as the preset list's floor. **The figures are in §9e**,
for all 17 inks x 12 papers; the 8 x 6 subset that used to be printed here said
the same thing about the same pairs and is deleted rather than kept in two
places.

**The density floor is the PhosphorGrain budget pattern:** the slider clamps
exactly where 7:1 would break on the CURRENT paper, per ink. Computed floors
(minimum density %, from `lightink::floorDensityPct`, pinned by test). This
table is KEPT rather than deleted with the contrast grid above, because no later
section reprints the floors — it is the original 8 x 6 corner of a surface that
is now 17 x 12, and the test is the authority for the rest:

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

**The formation now varies with the stock too (2026-08-22 paper research).**
`lightink::formationScaleFor(paper, strength)` is `toothScaleFor`'s exact
twin: each stock carries a formation factor that scales the formation DEPTH,
linear in the strength dial, exactly 1.0 at strength 0 and for Bright White
everywhere. Unlike tooth the factor may sit **below** 1.0 — a filler-loaded or
premium-coated sheet reads more even than the reference, and dialing one in
legitimately calms the clouds. The ladder, with its one measured anchor:

| Paper | Formation | Basis |
|---|---|---|
| Kozo | **1.90** | **Measured**: handmade kozo's formation index 131 vs 60–97 for nine machine sheets (Hirai et al. 2003) — the 1.5–2x band, the only instrumented rung. |
| Laid Antique | 1.50 | Hand mould, no machine drainage — high, second to kozo. Chosen. |
| Newsprint | 1.40 | Fast groundwood furnish. Chosen. |
| Chamois | 1.30 | Aged uncoated. Chosen. |
| Bone / Sepia / Azzurrata | 1.15–1.20 | Open uncoated sheets. Chosen. |
| Cream | 1.10 | Fine uncoated. Chosen. |
| Bright White / Press Gray | **1.00** | The reference (static_assert on Bright White). |
| Vellum | 0.80 | Skin, not a fibre suspension: no flocs, only the hide's unevenness. |
| India / Brightened White | **0.70** | Filler-evened calendered thin sheet; premium coated. The floor. |

The product `formation dial x formationScaleFor` is what the picker pushes
through `SimulatorOverlay::setPaperFormation` (the overlay clamps at the
model's max, so kozo at the default 55% dial saturates at 1.0 rather than
overswinging); the desktop `settings.json` still carries a raw percent, since
it has no paper picker.

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
therefore freezes the currently-RESOLVED dark pair into the dark hex fields
once, before the preset first moves to Custom — the dark page keeps rendering
the same tones.

**REVISED 2026-08-23, owner P1 ("ink is not being picked up ... fix sourcing for
light and dark to be more accurate on load, switch etc").** Two things about the
paragraph above were wrong, and both were fixed the same day.

1. **The freeze is not this file's any more.** It is
   `CrossPointPrefs_claimCustomFor(editingDark)`, one protocol both editors
   call, decided by [src/PanelSource.h](../src/PanelSource.h). It had to be
   shared because the mixer had no freeze at all: `applyGuns` wrote all FOUR hex
   fields, so a gun moved in dark mode overwrote whatever ink had been chosen
   here. Measured on an iPhone Air simulator: an applied Payne's Gray stored
   `panelInkLight=323D47` and rendered page text at (30,37,43); one gun move
   rewrote it to `6E0500` and the same text measured (64,3,0) — a red — while
   `lightInkIndex` still read 15 and this picker still showed Payne's Gray as
   the chosen row. That is the owner's report, in pixels.

2. **The phosphor loss was never an acceptable cost, and is no longer paid.**
   The old text called it "known, accepted": after the freeze the dark page kept
   a named CRT's color but not its decay, because `pollPanelGlow` read the
   preset integer and Custom names no phosphor. Measured: White CRT's 283 ms
   emissive trail became 0 ms reflective the moment an ink was picked, and
   stayed that way across relaunches. The claim now freezes the phosphor with
   the tones, into `panelDarkSnapshotPreset`, and the glow asks
   `crosspoint::glowPresetForPrefs()`. A gun mix still carries its own decay and
   still wins.

Pinned by `tests/panel_source_test.cpp` (bytes, both polarities, load / switch /
both editor orders) and `tests/panel_source_test.py` (each editor writes only
its own polarity's keys). Both fail against the pre-fix tree.

### 7a. The road back: a Presets button, and what it hands over (2026-08-23)

Owner ruling, same day: **"add a Presets row back to the pickers."** The claim
above only points the shared integer AT Custom, and the Settings.app palette row
left with the other page rows on 2026-08-22 — so from the first ink pick, the
fifty-two named presets were unreachable as presets. Nothing in the app could
write a name back.

The control is a **Presets bar button** in this drawer's nav bar, opposite Done,
which pushes [ios/CrossPointPresetList.mm](../ios/CrossPointPresetList.mm) — the
same list the mixer pushes. A bar button rather than a row in the scroll for two
reasons: it costs the drawer no vertical space, and the mixer has none to give
(medium detent, pinned since 2026-08-21), so this is the one shape both editors
can carry identically.

The list is this drawer's paper grid, re-used: a wrapped grid of swatch cells
under family headings, three across, each cell painted in the preset's own paper
with its name in the preset's own ink. **Every preset is offered here and in the
mixer both** — a preset defines BOTH appearances, so filtering either list would
remove a choice that used to be reachable from Settings.app. What differs is the
preview: this drawer renders the light page, so its cells show light pairs.

Selection is the exact inverse of the claim
(`CrossPointPrefs_selectPanelPreset` → `panelsource::releaseCustom`): the preset
integer moves to the name, and the two keys that only speak while the slot is
Custom — `phosphorMixActive` and `panelDarkSnapshotPreset` — are **cleared**,
not left. Leaving them is the trap: the glow asks the mix flag before the frozen
phosphor, so a blend from a page that is no longer on screen would own the decay
of a preset chosen after it. The four hex fields ARE left, because a named
preset ignores them and the next claim re-freezes whichever polarity it does not
own.

This drawer's readout says so. While a named preset is in force it reads
`Preset <name> — tap an ink to take over` instead of describing an ink the page
is not using: the picker showing Payne's Gray over a page that was not Payne's
Gray is exactly what the owner reported as S-020, and it would have been
reintroduced pointing the other way.

Measured on an iPhone Air simulator, 2026-08-23 (screenshots at native pixels,
`[harness] panel palette` lines quoted):

| station | light page | dark page | glow |
|---|---|---|---|
| White CRT selected | `304248` on `F8FDFF` | `B6EFFF` on `182327` | preset 21, 283 ms |
| Payne's Gray picked | `323D47` on `FBFBF9` | `B6EFFF` on `182327` (frozen) | preset 21, 283 ms |
| Green CRT selected | `0B3D0B` on `DCEFD8` | `33FF33` on `001A00` | preset 6, 400 ms |

The dark crop before and after the ink pick differs by a mean of 0.0 levels
(max 1) — the freeze — and by a mean of 63.9 after the preset selection.

## 8. The drawer WAS the paper instrument (2026-08-22), and the sheet is FROZEN (2026-08-23)

Owner order, 2026-08-22: "make tooth, formation, pressure and all other paper
variables sliders in the 'color button' drawer." Every constant the light page's
surface was built from became a live control, and the sheet became a
`UIScrollView` with three labeled groups.

Owner ruling, 2026-08-23, sent with a screenshot of the drawer at the values he
had settled on: **"set Paper, tooth, formation, defects and press to these
parameter values, then remove sliders and option to set this in app."** So the
instrument served exactly one day, and its job is done: the numbers it was for
finding have been found, and they are now constants.

| Parameter | FROZEN at | Was |
|---|---|---|
| Paper (stock tint strength) | **100** — full, then through `clampPaperStrengthPct` | 0..ceiling slider |
| Tooth | **300 %** of the stock's own `toothScaleFor` factor | 0..400 % slider |
| Formation | **80 %** of the stock's own `formationScaleFor` factor | 0..100 % slider |
| Defects | **0** — a fresh, unmarked sheet | 0..100 slider (and a Settings row before that) |
| Sheet drift | **100** — `lightink::kPaperDriftMax` | 0..100 slider |
| Ink squeeze | **100 %** | 0..200 % slider |
| Deboss | **100 %** | 0..200 % slider |
| Plate pressure | **100 %** | 0..200 % slider |

What stays in the drawer: the ink list with its family headings and swatches,
the **Density** slider, the **paper STOCK grid** (choosing the stock is not the
same control as the strength slider), Done, and the summary readout.

**Sheet drift is the one he did not name**, because it landed after the build
his screenshot came from. Frozen at the top of its range by a ruling later the
same day — the leaves of a book measure slightly differently now, always.
It is deliberately **not** `lightink::kPaperDriftDefault`: that constant still
means "the model ships this off", the desktop and the tests read it as such, and
the app's frozen value simply differs from it.

**How a value is frozen** (the shape, and it is not negotiable): the getter
returns its constant **without consulting `NSUserDefaults`**. Not "keep the read
and change the default" — an install that stored a different value before the
control was removed must not keep rendering it, and with the slider gone there
is no way to change it back. The precedent is `ios/CrossPointPrefs.mm`'s own
frozen getters from earlier the same day; `ios/CrossPointLightInkPicker.mm`
follows it exactly. The seven `lightPaperStrengthPercent` / `paperToothPercent`
/ `paperFormationPercent` / `paperDriftPercent` / `press*Percent` keys and the
`paperDefectsPercent` key are **deleted**, along with
`CrossPointPrefs_setPaperDefectsPercent` — a key naming a value nothing consults
is worse than no key.

**The paper strength is RE-DERIVED, not carried.** `clampPaperStrengthPct` is a
ceiling that moves with the ink, so every change re-runs the frozen request of
100 through it (`reclampSelection`). Carrying the last clamped value instead
would ratchet: a dark ink lowers the strength, and with no slider left nothing
could ever raise it again. The re-clamp runs BEFORE `applySelection`, because
that is what writes the hex fields the page renders from.

**The 7:1 floor at the frozen set.** Drift at the top of its range used to be a
worst case and is now every page, so `tests/light_ink_test.cpp` sweeps it: every
ink on every stock, every density from the floor up, at drift 100 with tooth
300 % and formation 80 % painted on the DARKEST leaf. Worst measured
2026-08-23 — model **7.001:1** (Verdigris on Kozo), textured **7.000:1**
(Standard on India, mean sheet darkening over 64x64; the same figure converges
to 7.0000 ± 0.0002 at 512x512). The frozen set sits exactly ON the floor, which
is what `letterpress::paperBudget` is for — it clamps the tooth amplitude to
whatever 7:1 leaves, so raising the tooth dial buys texture out of a budget
rather than out of legibility.

Rulings from the instrument's one day that are still load-bearing:

**Tooth is a MULTIPLIER, not a replacement.** A stock has its own roughness
(`toothScaleFor`), and the frozen 300 % rides on it, so a chamois still reads as
a chamois. Setting it to replace the stock factor would have made the stock
grid's texture half of its meaning disappear.

**`kPressCells` stays a constant.** Cells are texture scale, not taste. Same
posture as the grain's mottle cells.

**The frozen press parts are 100 % of standard**, which is a state the shipped
`Letterpress` master could already select on its own. Nothing the frozen sheet
renders is outside the ladder that existed before the drawer did.

**Layout.** Manual frames stay; they are frames inside the scroll view's content.
The sheet keeps **medium** as its opening detent and **large** beside it — the
ink list alone is longer than a medium detent.

The frozen values are pushed at LAUNCH by the shim
(`CrossPointInkPicker_pushPaperDials`, edge-triggered on
`CrossPointInkPicker_paperDialSignature`), because the drawer may never be opened
and the sheet still has a texture; the tooth, the formation and the wires still
move when the owner picks a different stock.

`CROSSPOINT_SIM_AS_SHIPPED=1` seeds the whole frozen set on the desktop
(`src/HalDisplay.cpp`) — tooth 300, formation 80, defects 0, drift 100, press
100/100/100, wires 0. The desktop's own `CROSSPOINT_SIM_PAPER_*` env vars and
`settings.json` keys are unchanged and still reach the setters: the freeze is an
iOS-app ruling, not a model change.

Design and citations for the marks themselves: [paper-defects.md](paper-defects.md).

## 9. The 2026-08-22 expansion — nine more inks, six more papers, and families

Owner order (verbatim): *"add more papers and inks and make suggestions on where
there are gaps to be filled, enhancements to be made or anything else that I
should consider."* The suggestions half is a separate document,
[surface-roadmap.md](surface-roadmap.md). This section is the additions.

**Sourcing, and it is a step up from §1.** §1 was written without web access and
said so. This round had it, and the sources are recorded in two companion
documents in this repo — [ink-colorimetry-sources.md](ink-colorimetry-sources.md)
(the standards-grade measurements) and
[ink-palette-research.md](ink-palette-research.md) (the pigment history and the
particle-size regime rule). Four rows below are now a **published
spectrophotometric measurement used verbatim** rather than a derivation. The
labels are used strictly:

- **MEASURED** — an instrument reading published with its conditions. The
  backbone here is Richard Kirk / FilmLight's spectrophotometry of 100 Winsor &
  Newton watercolours *on paper* at three densities each, published as CIE
  L\*a\*b\*, plus the ISO/FOGRA characterization datasets.
- **ATLAS** — a name matched to a physical color atlas by a competent authority:
  Maerz & Paul's *A Dictionary of Color* (1930) → the NBS/ISCC *Dictionary of
  Color Names* block → that block's published Munsell renotation → sRGB. Real
  published colorimetry, reached through a 1950s expert's visual judgment.
- **RECONSTRUCTED** — this repo's, from a constraint that is measured (a dye's
  absorption maximum) plus a density choice that is not.

Where a row is not MEASURED, the anchor is still the recognized hue carried down
**its own line in linear light at constant chromaticity** to clear the 7:1 floor
— the rule §1 states, and the reason the anchors are darker than the famous
swatch.

**And a warning the sources are emphatic about**, carried here because it is the
main way a table like this goes wrong: most "pigment hex codes" circulating on
the web are color-*name* centroids or paint-brand marketing, not measurements of
the material. Three that were checked and **rejected**: verdigris `#43B3AE`
(no source cited anywhere; it is the patina on a bronze statue, not the
pigment), Van Dyke brown `#44362F` (cited to a house-paint company), and Davy's
gray `#555555` (traceable to a real ISCC-NBS block, but that block has chroma
*zero* and the measured paint is 21 b\* units away from neutral).

### 9a. The nine new inks

Rows 8–16. Append-only, so nothing above them moves; `tests/light_ink_test.cpp`
now pins the original eight rows' names and bytes literally, which is the only
thing that can catch a row being re-pointed or inserted.

| # | Ink | Anchor | Label | Family | Era, mechanism, and why it is here |
|---|-----|--------|-------|--------|------------------------------------|
| 8 | Bone Black | `#39342D` | **MEASURED** | Blacks | Charred bone: only ~10% carbon in an ~84% calcium-hydroxyapatite matrix (CI Pigment Black 9). It is here because it is **genuinely a different black from lamp black**, which the table already had as Carbon Black — and the difference is now measured rather than asserted: W&N Ivory/Bone Black masstone L\* 21.87 / a\* 0.73 / **b\* +5.13**, against Lamp Black's L\* 9.81 / −0.03 / **b\* −0.18**. Bone black is warmer at *every* density, by Δb\* 5 to 9. The warmth is the *matrix*, not the carbon. |
| 9 | Van Dyke Brown | `#4D3B31` | **MEASURED** | Browns | Cassel/Kassel earth: a lignite or peat earth, 60–90% organic humic matter rather than an iron oxide (CI Natural Brown 8). Named for Anthony van Dyck (d. 1641). W&N Vandyke Brown masstone L\* 26.55 / a\* 6.24 / b\* 9.20. It is the third brown deliberately: sepia is the red-leaning one, bistre/walnut the yellow-leaning one, and Van Dyke the *dark neutral* between. Also the table's cautionary tale — it is famously fugitive, it greys in alkali, and it cracks the films it is bound into. |
| 10 | Sanguine | `#5C332B` | **ATLAS** | Browns | Red chalk: natural hematite (Fe₂O₃) in a clay matrix, cut into sticks. Leonardo was the first major artist to use it as a drawing medium, late 15th c.; then Michelangelo and Raphael. The anchor is unusually clean: Maerz & Paul's **`red chalk`, `red ochre` and `rubrica` all map to the same ISCC-NBS block 43, Moderate Reddish Brown, Munsell 9R 3.4/5.2** — a triple convergence, carried down to reading density. Filed under Browns rather than Reds because that is what an iron-oxide red *is* at body-text density. |
| 11 | Vermilion | `#6D2812` | **MEASURED** | Reds | Mercury(II) sulfide, HgS; the natural mineral is cinnabar, the dry-process synthetic is documented from roughly the 8th–9th century (CI Pigment Red 106). **This is the red of rubrication**, which §1 recorded as unavailable at a 7:1 floor — it is available *at density*. Anchored on the measured W&N Vermilion masstone L\* 50.16 / a\* 45.82 / b\* 46.00, hue angle ≈45°, which settles that vermilion is a scarlet-**orange** and not a crimson. Its own historical defect is blackening to metacinnabar, and the mechanism is now known to be chloride ions from surface dirt rather than light alone. |
| 12 | Madder Lake | `#68243C` | ATLAS | Reds | A lake: alizarin and purpurin from *Rubia tinctorum* root, precipitated onto an alum substrate — the substrate is what turns a dyestuff into a pigment. It earns a row beside Oxblood and Vermilion because it is the **cool** red: measured Rose Madder sits at hue ≈25° against vermilion's ≈45°. Anchored on Maerz & Paul `madder lake` → ISCC-NBS block 255, Strong Purplish Red, 7.3RP 4.4/11.4, because at reading density the measured pink-crimson and the measured vermilion converge to within 5 code values and two rows that look alike is what this table forbids. |
| 13 | Copying Violet | `#591B83` | **RECONSTRUCTED** | Blues & violets | Methyl violet / crystal violet, a triarylmethane aniline dye first made in 1861. The purple of **copying ink, indelible pencils, carbon paper, hectographs and spirit duplicators** — every mimeographed worksheet before the photocopier. **The only reconstructed row in the table**, and deliberately labeled: no measured Lab or reflectance for a hectograph, ditto or copying-pencil impression exists in the conservation or forensic literature. What *is* measured is the dye — crystal violet's absorption maximum is **590 nm** in water, which removes the orange-yellow and puts the survivor on the **blue** side of the purple locus. The hue is sourced; the lightness and chroma are this repo's. |
| 14 | Verdigris | `#2C412C` | ATLAS | Greens | Basic copper acetate, made by standing copper over fermenting grape skins (CI Pigment Green 20). The principal green of medieval manuscripts, and **the sibling to iron gall's famous defect**: copper(II) ions migrate through the sheet in humidity and catalyze both oxidation and hydrolysis of cellulose, eating holes clean through the leaf. It is also the one pigment where the alkaline-buffering reflex is *contraindicated*. The table had no green at all; anchored on Maerz & Paul `verdigris [green]` → ISCC-NBS block 136, 0.5G 5.5/4.8, carried deep because a light green cannot clear 7:1 on any sheet. |
| 15 | Payne's Gray | `#323D47` | **MEASURED** | Grays | Not a pigment but a **mix**, attributed to the English watercolorist William Payne, c. 1790 — classically Prussian blue with a crimson lake and sometimes an ochre; today phthalo blue, lamp black and quinacridone. Watercolorists use it *instead of black* because it darkens without deadening, which is the same argument this app's own eased-ink ruling makes. W&N Payne's Gray masstone L\* 25.24 / a\* −1.97 / **b\* −7.56**: unambiguously a cool blue-gray, and the anchor needed no scaling at all because the paint's own masstone already sits at reading density. |
| 16 | Davy's Gray | `#423C29` | **MEASURED** | Grays | Powdered slate, sold under that name by Winsor & Newton and named for Henry Davy; the current formulation is slate plus lamp black plus chromium oxide green. **The measurement overturns the folklore here, which is why this row exists in the form it does.** The circulated `#555555` is a chroma-*zero* ISCC-NBS centroid; the measured paint is L\* 51.88 / a\* −1.17 / **b\* +20.71** — an olive, barely green and strongly yellow, about 21 b\* units from the neutral everyone repeats. This row is olive because the spectrophotometer says so. It also sets the table's minimum contrast and is the honest edge of the offered range. |

**No modern printer's-ink row, and that is a measurement rather than an
oversight.** It was the obvious candidate and the numbers closed it: ISO
2846-1:2017 Table 1 puts the offset process black at **L\* 18.0 / a\* 0.8 /
b\* 0.0 → `#2D2C2C`**, which is **one code value from the shipped Standard row's
`#2D2D2D`**. FOGRA51's measured K100 solid on premium coated is `#2B2B29`, two
code values away. The row already exists; it is row 0, and the "shipped e-ink
tone" turns out to be standardized printer's ink to within a rounding error. The
*uncoated* variant is a different color — FOGRA52 measures L\* 32.69 → `#4F4C4D`
— and it cannot be offered at all, because it reaches only **6.18:1 on Chamois**.
Two findings fall out of that pair and both are worth keeping: a single-ink
offset black is not black (L\* 16 is a quarter of the way up the lightness
scale — body text in K-only offset is `#2B2B29`, not `#000000`, and the genuinely
dark black of print is the four-color overprint, which is also visibly *warm* at
b\* +4.89); and **on uncoated book paper it only reaches L\* 33**, which is why
a paperback's text never looks as black as a coated page's.

**One model limitation, stated because the sources make it unavoidable.** A
soot black's warm/cool character is a **particle-size effect that flips with
density**: fine carbon reads blue in masstone and brown in dilute tint, coarse
carbon the opposite, measured at Δb\* ≈ 6.5 at matched lightness. This table
stores one hue per ink and dilutes it along a fixed locus, so it cannot express
that flip — every carbon row here is its *masstone* character held all the way
down. Bone Black is exempt, because its warmth is the calcium-phosphate matrix
rather than the particle size and really is constant. Recorded so no future
comment claims a constant warm/cool for a carbon ink.

**Grouping, and why it is presentation only.** Seventeen rows is a wall. The
picker now emits a heading per family — **BLACKS, GRAYS, BROWNS, BLUES &
VIOLETS, REDS, GREENS** — and the display order is **derived** from a `group`
field by `lightink::buildInkDisplayOrder`, never stored. Three consequences, all
of them the point:

- **No stored value moves.** A selection is still the table index. This is the
  separation the preset picker already uses ("the display order in `Root.plist`
  is independent of that integer"), applied to a C++ table.
- **Appending a row cannot desynchronize anything.** There is no hand-written
  order list to forget; a new ink lands at the bottom of its own family, and the
  test proves the result is a permutation with every family contiguous and
  non-empty.
- **Standard still leads.** Row 0 is the default and the test pins that it is the
  first row displayed, because a default buried under a heading is a different
  default.

The order is **borrowed, not invented**: blacks and grays adjacent, browns their
own family and never filed under reds, is R.D. Harley's ordering in *Artists'
Pigments c.1600–1835* and Winsor & Newton's own chart order, collapsed for a set
that is mostly blacks and browns because this is a table of *reading* inks. Note
that the Colour Index's numbers within a hue (PBk6, 7, 8, 9…) are
**chronological, not chromatic** — they are not an ordering to copy. Sanguine is
filed under Browns because that is what it paints at reading density: the
grouping is by what the row *looks like*, not what the mineral is called.

### 9b. The six new papers

| # | Paper | Tone | Tooth | Stock, and the claim |
|---|-------|------|-------|----------------------|
| 6 | India | `#F9F3E9` | **1.12** | Bible/India paper: a very thin (22–40 gsm) rag or flax sheet loaded with mineral filler for opacity, warm-white, pressed extremely smooth. Oxford University Press's primary histories date the first India-paper printing to **1842** and the commercial arrival to **1874** — the widely repeated 1875 appears in neither. **The smoothest stock in the table after the coated reference**, and the anchor is a real negative: delfort publishes brightness for its thin-print grades but prints a literal "–" in the CIE-whiteness column, which is a mill telling you not to model bible paper as a blue-white sheet. Its defining characteristic, show-through, the model cannot yet render at all — [surface-roadmap.md](surface-roadmap.md) §1a, where it is the top item. |
| 7 | Vellum | `#F9E7D7` | 1.22 | Calfskin. Creamy and faintly pink rather than yellow, and — the part worth having — **unevenly toned**: hair side and flesh side differ, the hair side showing higher saturation and lower reflectance. **No published absolute CIE Lab for parchment exists**, and that is a searched-for negative rather than a gap: the conservation literature reports aging *deltas* and never a baseline, and manufacturer-to-manufacturer variation swamps species variation (modern calf parchment from one supplier reads dark, from another light). The constraints that *are* sourced — darker and warmer than rag paper, positive b\* — are what this tone honors. Note the trade's homonym: a paper sold with a "vellum finish" is an unrelated thing. |
| 8 | Laid Antique | `#E3DBCA` | **1.85** | Handmade or mould-made laid: the sheet that carries chain and laid lines from the mould's wires; wove displaced it only around 1810, so laid reads as pre-1800 and deliberately archaic after. The anchor is a purchasing standard rather than a study — the US GPO's JCP A120, *50% Cotton Laid-Finish Antique Text*, specifies **72% ±2 brightness with optical brighteners expressly not permitted**, against **≥88%** for its modern laid grade. That 16-point gap plus the OBA prohibition *is* the visual difference, and it is why this row is warm: **antique stocks have positive b\*, modern brightened stocks negative** — the single axis that separates old paper from new. **The chain and laid lines are rendered as of 2026-08-22** — `src/LaidStructure.h`, generated at output size exactly because of the ST-008 hazard this cell used to name, gated on the row's `laid` flag and riding the paper slider; measured geometry (laid ~1 mm pitch, chains 26–39 mm, chains darker, the antique strip along each chain) in [paper-colorimetry-sources.md](paper-colorimetry-sources.md) §3c. |
| 9 | Kozo | `#EEE6C3` | **1.95** | Unbleached Japanese washi from the inner bast of *Broussonetia papyrifera*. Two independent measured gamuts converge here, which makes it the best-anchored of the six: Edo-through-contemporary washi at **L\* 60–85 with a\* toward negative and b\* toward positive**, and 227 undyed Korean hanji samples at **L\* mean 88.2, a\* −3..+3, b\* 0–20**, where "yellowness is the main characteristic" and most sheets read greener than redder. Structurally the roughest thing in the table: very long fibres, formed by hand, never calendered. **This row takes the "roughest offered" title from Chamois**, which held it only while it was the only non-machine sheet; Chamois' own 1.80 is unchanged, so nothing already selected re-textures. Scope note (C3, [paper-colorimetry-sources.md](paper-colorimetry-sources.md) §1d): the tone's *depth* (b\* +18) is a reconstruction — measured *white* kozo sits at b\* +2..+3 — while the hue SIGN and the surface claims are instrumental, and the formation claim is the best-measured in the table: handmade kozo scored the worst formation index of ten shoji sheets, **131 vs 60–97** (Hirai, Yokoyama & Gunji 2003), which is what tops the formation ladder at 1.90x. |
| 10 | Azzurrata | `#E0E0ED` | 1.55 | *Carta azzurra*, the blue-tinted Italian writing and drawing stock — first recorded in northern Italy in **1389**, taken up by artists a century later, and the support Carpaccio, Titian and Tintoretto drew on; Aldus Manutius printed the first book on it in Venice, 1514. **Two corrections the sources force.** It was tinted by **blue-dyed rags — indigo and woad — not smalt**; smalt was primarily a Dutch 17th–18th-c. *whitening* additive, a different practice and a later one. And **red fibres are present in almost every blue rag paper**, added deliberately to bulk the pulp and adjust the tone, which is why the sheet reads **gray-violet rather than pure blue** — an optical mixture of blue and red fibre, not a flat blue field. This row is the table's only cool option with real chroma; Press Gray is a neutral. |
| 11 | Newsprint | `#DEDCD3` | 1.70 | Groundwood/mechanical pulp: high lignin, rough, and the gray-buff cast no rag sheet has. The best-resolved stock in the set — Norske Skog's own NorNews sheet gives **ISO brightness 57%, L\* 82 / a\* −1.1 / b\* +5.3 (ISO 5631, C/2°), PPS 4.5 µm** from one document, and ISO 12647-3's normative standard-newsprint aim independently lands at **L\* 82 / a\* 0 / b\* +3**. **Correction C1 (2026-08-22 research pass): the row's story changed from "a lift we own" to a measured grade with a name.** FOGRA51's registry sibling **FOGRA48 improved newsprint (INP)** measures **88 / 0 / +2 → `#DEDDD9`** — within 6 code values of this row on every channel — and clears the floor (worst ink 7.78:1), so to measurement precision this row *is* improved newsprint. What the floor excludes is **standard newsprint**: FOGRA42 SNP at **82.38 / 0.11 / 3.28 → `#CFCDC7`** reaches only ~6.7:1. Bytes unchanged; [paper-colorimetry-sources.md](paper-colorimetry-sources.md) §1a, §5 C1. |
| 12 | Brightened White | `#EFF0FC` | **1.05** | **Appended 2026-08-22 (research G1/I3): the OBA-brightened modern page the table lacked.** FOGRA51's measured M1 substrate — **Lab 95.00 / 1.50 / −6.00**, the reference white the 2013-era print industry proofs against — derived through the same pipeline as every ink. The only row whose negative b\* is *earned* by brighteners rather than dye (the b\*-sign rule of §2 of the sources doc), which is also why its blue channel sits ABOVE the bright-white ground's and the tint ramp's monotonicity is stated per channel now, not as a blanket luminance rule. Tooth 1.05 (coated-era smooth, and the strict-rise test needs it off exactly 1.00), formation 0.70 (premium coated, optically even — tied lowest with India). Re-proven by the test rather than trusted from the research: 7:1 against all 17 inks (worst **9.34:1**, Van Dyke) and ≥ 8 code values from every other row (nearest: Press Gray, ΔB 16). |

### 9c. The findings, which are the part worth keeping

**The shipped Walnut & Bistre row sets a hard darkness floor on every future
paper, and it is why there is no real newsprint here.** This is the answer to
"should any pairing be excluded rather than clamped", and it is arithmetic, not
taste:

- Full-density contrast is a fixed number per pair — the density slider cannot
  rescue it, because density 100 *is* the ink. So a new paper is legal only if
  every existing ink already clears 7:1 on it.
- The binding ink is Walnut & Bistre, relative luminance **0.0458**. Solving
  `(Yₚ + 0.05) / (0.0458 + 0.05) ≥ 7` gives **Yₚ ≥ 0.6203**, i.e. **L\* ≥ 82.9**.
  Every paper this table will ever offer must be lighter than that, forever,
  unless a shipped ink row changes — which the append-only rule forbids.
- **Real fresh newsprint sits below that line.** At the measured L\* 82 it reaches
  **6.81:1** against Walnut & Bistre. The Newsprint row therefore carries the
  mills' measured *hue* (a\* −1.1, b\* +5.3) at **L\* 87.8** — a lift of nearly
  six lightness units, named here rather than quietly rendered as a lie.
- **Aged newsprint is further out and is not offered.** A real 1913 wood-pulp
  book page measures **L\* 83.1 / a\* +3.6 / b\* +18.9** — b\* more than triples
  from fresh and a\* crosses from green to red, which is the aging trajectory in
  numbers. It clears the floor at exactly **7.03:1**, with no margin for the
  sheet-tooth budget to spend, so it stays out.

**My recommendation on exclusion, since the order asked:** do **not** add a
per-pair exclusion mechanism to buy the dark stocks. It costs a new kind of state
(a legality table the picker grays rows out from), it makes two independent lists
conditional on each other, and it buys three or four stocks that are by
construction the least legible on offer. *Every ink on every paper, always* is
worth more than an aged newsprint. If the dark end is ever wanted badly enough,
the honest lever is a **second floor** — an owner-visible AAA/AA choice that
drops `kContrastFloor` from 7.0 to 4.5 and re-derives every clamp, which is one
constant and a re-run of the sweep. A deliberate, labeled, reversible reduction
in contrast, not a hidden exception.

**The floor also confines every paper to an eleven-L\* band**, from Bright White's
98.6 down to the 87.8 the newest row sits at. Twelve stocks inside eleven
lightness units is crowded, which is why the six new tones are placed by **a\*
and b\*** — pink, olive, violet, buff — rather than by lightness, and why the
test now requires eight code values of separation between every pair rather than
mere byte-inequality.

**Coated art paper was considered and rejected as a duplicate.** A gloss art
sheet is smoother and brighter than the reference, and the model's tooth scale
*starts* at the reference: `kPapers[kPaperBrightWhite].tooth == 1.0f` is a
`static_assert` and the test forbids any stock smoother than it. Bright White is
already described as coated, calendered bright text stock. Measured PPS confirms
there would be nothing to render: Sappi's gloss art is 0.6–0.8 µm against
newsprint's 4.5 — but note the trade lesson that came with it, that **"coated"
is the wrong axis**: the same mill's coated *matte* runs 3.2–4.0 µm and its bulky
matte 4.5, rougher than newsprint. Gloss is the smooth thing, not coated.

**The greenish cast of mid-century pulp paperbacks: real, misdescribed, and still
not shipped.** It is a greenish **yellow**, not a green-gray, and the mechanism
is manufacturing rather than aging — bleached mechanical pulp measures a\* ≈ −2
riding on b\* ≈ +6 to +10, and blue shading dye added without a red correction
"generally produces a slight color shift towards green" (which is why the correct
shading dye for paper is violet). Two things rule it out as a row: aging pushes
*away* from green (the 1913 page is a\* +3.6, firmly red), so a green cast is
as-manufactured and not the aged look the row would be for; and no colorimetry of
paperback stock exists anywhere, so the row would be an invention wearing a
mechanism. Recorded as a negative result so it is not re-proposed — and if it is
ever wanted, the anchor is ISO 12647-2:2004 paper type 5, **L\* 88 / a\* 0 /
b\* +6**, pulled to a\* −1.5..−2, and **never** with a negative b\*.

**A test assumption had to be narrowed, and it was a real one.** The hue-retention
check asserted that a wash keeps the ink's channel *order* at 50% density for any
pair of channels differing at all. That was safe while every colored ink was
strongly chromatic and is wrong for a near-neutral one: a five-code-value blue
lean, washed to half density on a tan sheet, comes back **yellow** — because a
near-neutral ink at half density on a tan sheet *is* a tan wash. That is the
correct answer and the model should not be asked to invent a blue that is not
there. The check now applies only to channel pairs separated by more than 12 code
values. Payne's Gray and Davy's Gray hit the same edge, which is what makes it a
rule rather than a special case.

**Two new guards, because the failure modes are silent.** Byte-inequality is not
distinctness — two stocks a code value apart is a row that costs a tap and shows
nothing — so every pair of inks and every pair of papers must now differ by at
least **8** code values on some channel, which is what the tables were placed to
clear. And the pre-2026-08-22 rows are written out **literally** in the test, so
a re-pointed or inserted row fails loudly instead of silently re-coloring an
owner's saved choice.

### 9d. The picker, at seventeen and twelve (thirteen since 2026-08-22)

Two layout changes, both forced by the row counts:

- **The ink list gained family headings** (§9a) and stays one column, because the
  era note needs the width. Seventeen rows plus six headings is about 520 pt of
  scroll content — long, but the sheet is already a `UIScrollView` with a `large`
  detent.
- **The stock swatches wrap.** One row of `kPaperCount` cells was fine at six and
  is a **24 pt sliver at twelve** — under the 44 pt minimum touch target, with the
  name shrunk past reading. The grid is now a fixed **six per row** over as many
  rows as the table needs, and the cell height rose from 40 to 44. A thirteenth
  stock now costs a row of sheet height rather than a millimetre off every
  existing cell.

### 9e. Full-density contrast, all 17 x 12

Recomputed by the test on every run, and printed in display (family) order.
Minimum in bold; every pair clears 7:1, so no offered combination can be
illegible.

| Ink \ Paper | Bright White | Cream | Bone | Chamois | Press Gray | Sepia Toned | India | Vellum | Laid Antique | Kozo | Azzurrata | Newsprint |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Standard | 13.29 | 12.10 | 11.49 | 10.02 | 11.44 | 10.53 | 12.48 | 11.44 | 10.00 | 10.98 | 10.53 | 10.02 |
| Carbon Black | 16.40 | 14.93 | 14.17 | 12.36 | 14.11 | 12.99 | 15.39 | 14.11 | 12.34 | 13.54 | 12.99 | 12.36 |
| Bone Black | 11.90 | 10.84 | 10.28 | 8.97 | 10.24 | 9.43 | 11.17 | 10.24 | 8.96 | 9.83 | 9.43 | 8.97 |
| Payne's Gray | 10.70 | 9.74 | 9.25 | 8.07 | 9.21 | 8.48 | 10.04 | 9.21 | 8.05 | 8.84 | 8.48 | 8.07 |
| Davy's Gray | 10.61 | 9.66 | 9.17 | 8.00 | 9.13 | 8.41 | 9.96 | 9.13 | 7.99 | 8.77 | 8.41 | 8.00 |
| Sepia | 13.08 | 11.91 | 11.31 | 9.86 | 11.26 | 10.37 | 12.28 | 11.26 | 9.84 | 10.81 | 10.36 | 9.87 |
| Walnut & Bistre | 10.58 | 9.64 | 9.15 | 7.98 | 9.11 | 8.39 | 9.93 | 9.11 | 7.96 | 8.74 | 8.38 | 7.98 |
| Van Dyke Brown | 10.21 | 9.30 | 8.82 | 7.70 | 8.79 | 8.09 | 9.58 | 8.78 | **7.68** | 8.43 | 8.09 | 7.70 |
| Sanguine | 10.32 | 9.40 | 8.92 | 7.78 | 8.88 | 8.18 | 9.69 | 8.88 | 7.77 | 8.53 | 8.18 | 7.78 |
| Iron Gall | 14.05 | 12.79 | 12.14 | 10.59 | 12.09 | 11.13 | 13.18 | 12.09 | 10.57 | 11.60 | 11.13 | 10.59 |
| Indigo | 10.79 | 9.83 | 9.32 | 8.13 | 9.29 | 8.55 | 10.13 | 9.28 | 8.12 | 8.91 | 8.55 | 8.14 |
| Prussian Blue | 13.05 | 11.89 | 11.28 | 9.84 | 11.23 | 10.34 | 12.25 | 11.23 | 9.82 | 10.78 | 10.34 | 9.84 |
| Copying Violet | 10.62 | 9.67 | 9.17 | 8.00 | 9.14 | 8.41 | 9.96 | 9.13 | 7.99 | 8.77 | 8.41 | 8.01 |
| Oxblood | 14.00 | 12.75 | 12.10 | 10.55 | 12.05 | 11.09 | 13.14 | 12.05 | 10.53 | 11.56 | 11.09 | 10.56 |
| Vermilion | 10.33 | 9.41 | 8.93 | 7.79 | 8.89 | 8.18 | 9.69 | 8.89 | 7.77 | 8.53 | 8.18 | 7.79 |
| Madder Lake | 10.63 | 9.68 | 9.19 | 8.02 | 9.15 | 8.43 | 9.98 | 9.15 | 8.00 | 8.78 | 8.42 | 8.02 |
| Verdigris | 10.67 | 9.72 | 9.22 | 8.04 | 9.18 | 8.46 | 10.02 | 9.18 | 8.03 | 8.81 | 8.45 | 8.05 |

The minimum is **Van Dyke Brown on Laid Antique at 7.68:1** — a measured pigment
masstone on the sheet the GPO says carries no brighteners. That corner is where
the table was designed toward rather than an accident: Van Dyke's anchor is a
measurement that was *not* darkened to buy margin, and Laid Antique is as dark as
the floor allows. Every ink's density floor and every paper's strength ceiling
are recomputed and printed by `tests/light_ink_test.cpp` on each run; the full
17 x 12 x 101 x 101 grid — 2.1 million (density, strength) states — is swept for
holes above a floor and states below a ceiling, as §5 describes.

### 9f. Renders

Proof images, lossless PNG at native device pixels (X3, render scale 1, 528x792,
no resampling), letterpress 100%, formation 55, defects 30, grain seed pinned:

- `SHEET-new-inks.png` — every new ink at full density, each on **Bright White**
  (left of its pair) and on **Chamois** (right). Eighteen 1:1 crops of the device
  framebuffer, tiled without resampling.
- `SHEET-new-papers.png` — every new paper at full tint with its own tooth
  factor, each under **Standard** ink and under **Iron Gall**. Twelve 1:1 crops.

Method, so the captures are reproducible: X3 desktop env, `SDL_VIDEODRIVER=dummy`,
`CROSSPOINT_SIM_DARK=0`, `CROSSPOINT_SIM_LETTERPRESS=100`,
`CROSSPOINT_SIM_PAPER_TOOTH=<stock tooth x 100>`,
`CROSSPOINT_SIM_PAPER_FORMATION=55`, `CROSSPOINT_SIM_PAPER_DEFECTS=30`,
`CROSSPOINT_SIM_GRAIN_SEED=7`, the pair driven through
`CROSSPOINT_SIM_PANEL_INK_LIGHT` / `_PAPER_LIGHT`, and the reader's progress
restored from a snapshot before every run so all 30 frames show the same page.
Every capture has a distinct md5, which is the cheap proof that the env pair
actually reached the renderer in each cell rather than one of them silently
falling back to the default.

## The preset list shows only this page's presets

Owner ruling 2026-08-23: *"only show presets available in that mode."* The ink
picker offers the **10 paper palettes**; the 42 phosphors belong to the mixer.
The rule is `panelpalette::presetOfferedInDark` and the reasoning is in
`docs/phosphor-mixer.md` -- it filters which editor OFFERS a preset, never what
a preset defines.

---

**Note on the tables in this document.** They were generated by printf blocks in
`tests/light_ink_test.cpp`, which were removed on 2026-08-23 as assertion-free
output written into a log the runner deletes on success. The numbers here are
correct as of that date and are not regenerated by anything in the repo today.
`git show 2e2b318:tests/light_ink_test.cpp` restores the generator if a future
change to the ink or paper tables needs these rebuilt.
