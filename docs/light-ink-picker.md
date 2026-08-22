# The light-mode ink picker — historical inks at variable density on proven papers

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

## 5. How it applies, and what dark mode keeps

Selection applies LIVE through the existing custom light fields
(`panelInkLight`/`panelPaperLight` + preset Custom), so the whole downstream —
letterpress, pad-on-paper, the keyboard chips — follows for free through
`crosspoint::panelForPrefs()`. Persistence is three new append-only integer
keys (`lightInkIndex`, `lightInkDensityPercent`, `lightPaperIndex`), with the
applied result mirrored into the light hex fields — the mixer's storage
discipline.

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
