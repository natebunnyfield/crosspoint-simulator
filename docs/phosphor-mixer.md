# The phosphor mixer

Added 2026-08-20. Math in [`src/PhosphorMix.h`](../src/PhosphorMix.h) (pure,
host-tested by `tests/phosphor_mix_test.cpp`), UI in
[`ios/CrossPointPaletteMixer.mm`](../ios/CrossPointPaletteMixer.mm).

## The rulings, in the owner's words

- *"make a custom crt interface option when i press or hold down the page color
  button: bring up a modal that lets me select which phosphors I want to mix
  together, I need to see the exact color of dark and light, ink and paper, and
  time to fades for each phosphor"*
- Mix model: **"allow all options"** — Blend, Parts and Cascade all ship.
- Trigger: **"Both open the modal"** — tap and hold alike. This supersedes the
  2026-08-17 cycling ruling; `cyclePalette()` and the 500 ms hold are gone, and
  the modal's Presets tab is where stepping through palettes now lives.
- Persistence: **"One live mix slot"** — the mix occupies the Custom preset.
- *"be sure to not allow premix phosphors to be mixed, instead, make those
  preset mixes"*

## The three modes

| Mode | Page | Afterglow |
|---|---|---|
| **Blend** | weighted linear-light average of up to 4 phosphors' inks and papers, both polarities | lasts as long as the **slowest** component and dies toward **its** ink — the fast components have already gone dark. Only reported when persistences actually differ; equal-speed blends dim without changing color |
| **Parts** | ink from one phosphor, paper from another | trail length from a third; no tail — nothing here is a mixture |
| **Cascade** | the flash layer's palette, unchanged | the persistence layer's trail, dying toward its ink — exactly how the shipped P7/P14/P17 rows are built |

Blending is **linear light**, not byte averaging: mixed emission is additive,
and the gamma curve's convexity means an sRGB byte-average is darker than the
physical mixture. The test pins a 50/50 green–blue blend brighter than the byte
midpoint, and the single-component identity byte-exact.

## Premixes are recipes, not ingredients

From the JEDEC composition strings this repo ships: **P4, P6, P18, P23, P40**
are powder blends (an explicit `+` or a second compound) and **P7, P14, P17**
are cascades (afterglow layers). None of the eight can be selected as a mix
component — the core silently skips them and the UI never offers them — and the
Presets tab shows them under their own "Preset mixes" heading, picked whole.
P35's `ZnS,ZnSe:Ag` stays mixable: a solid solution is one crystal lattice, not
a powder mix.

## Preset mixes: tap applies, long-press loads

Owner ruling 2026-08-20 ("Both — tap applies, long-press loads"): tapping a
premix row selects it whole, exactly like any preset; a long-press loads its
**recipe** into the mixer for tweaking, switching to the right tab with the
components pre-filled.

The recipes live in `kPremixRecipes` (PhosphorMix.h), named by P-number so they
survive renumbering — and as of 2026-08-21 they are **fitted, not composition
maps**. The first table mapped each premix's JEDEC compounds to their nearest
pure rows (P4 = P22B + P22G, chemically exact) and missed the shipped premixes
by ΔE 26–47. The reason is structural: the shipped premix pages were derived
from JEDEC **white points** through the palette pipeline, while the component
rows went through that pipeline separately — the two constructions do not
commute, so blending the stylized rows cannot land on the stylized premix.
Chemistry-true recipes that render visibly wrong teach the wrong lesson, so on
the owner's "recompute the eight presets" they were refitted by exhaustive
search (pairs and triples, weights 1–9, CIELAB against the shipped dark pair).
One guardrail: P10 is excluded as a donor — a dark-trace screen absorbs, and
the unconstrained fit used it as a dimming agent.

| Premix | Fitted recipe | ΔE (was) |
|---|---|---|
| P4 | Blend: P13 1 : P45 6 : P5 1 | 4.8 (32.5) |
| P6 | Blend: P5 1 : P45 2 | 3.8 (41.6) |
| P18 | Blend: P5 2 : P45 7 : P56 1 | 4.7 (42.3) |
| P23 | Blend: P45 9 : P56 4 | 9.6 (46.8) |
| P40 | Blend: P28 1 : P45 6 | 8.4 (26.1) |
| P7 | Cascade: flash P47, persistence P34 | — |
| P14 | Cascade: flash P5, persistence P26 | — |
| P17 | Cascade: flash P5, persistence P19 | — |

The test pins that every premix has a recipe, every component resolves to a
real pure row (never a premix), no recipe uses P10, and every blend recipe's
computed dark ink lands within ΔE 12 of its shipped premix — the fit is the
contract now.

## How it lands in the pipeline

The computed result is written into the **Custom slot's four hex fields**
(`panelInkLight/panelPaperLight/panelInkDark/panelPaperDark`) and
`panelPalettePreset` is set to Custom — so `resolve()`, the pad tint and the
keyboard chips all keep working without learning anything. Two additions only:

- `pollPanelGlow` asks `CrossPointMixer_glowForCustom()` when the preset is
  Custom, because plain Custom has no phosphor and would get trail 0 while a
  mix has its own decay and tail.
- The poll dedupes on the preset integer, which does not move while editing a
  mix already on Custom — `CrossPointMixer_glowChanged()` marks it dirty.

The mix itself persists in `phosphorMix*` NSUserDefaults keys (mode, a
`preset:weight` CSV for the blend, role assignments for the others). Picking a
plain preset sets `phosphorMixActive` to NO but leaves the recipe stored, so
returning to a mix tab restores it.

## Every row shows the exact numbers

Four swatches per phosphor — dark ink, dark paper, light ink, light paper —
each with its hex value, plus the time to fade (`trailMsForPreset`). That is
verbatim what was asked for, and it is the same data the proof artifacts show.

## Not done, said plainly

## The shelf is banded by persistence

Owner ruling 2026-08-21: "group ingredient shelf by natural breaks of
persistence fade." The five bands are the data's own gaps, not round numbers —
sorting the 34 pure trails, the ratio jumps sit at 20→63 ms, 126→283,
400→693 and 1095→2828. `trailBand()` / `trailBandName()` in PhosphorMix.h are
the single definition; the mixer's Blend/Parts/Cascade shelves section by them
and the proof page groups its table the same way. The test pins that every pure
row lands in a band, no band is empty, and the edges sit in the gaps.

| Band | Range | Rows |
|---|---|---|
| Gone within a frame | ≤ 20 ms | 6 |
| A blink | 60–130 ms | 6 |
| A beat | 280–400 ms | 12 |
| Lingers | 0.7–1.1 s | 8 |
| Holds on | ~2.8 s | 2 |

- ~~Desktop parity~~ — **DONE 2026-08-21** (owner ruling, closing the gap his
  2026-08-19 parity ruling opened). `settings.json` carries the same
  `phosphorMix*` keys iOS persists — mode, the `preset:weight` blend CSV, the
  Parts and Cascade role assignments — and the watcher runs them through the
  identical `PhosphorMix.h` core, so a recipe typed on the Mac and one built on
  the phone compute the same page and the same glow. A mix OWNS the page while
  active; `panelPalettePreset` is ignored until `phosphorMixMode` returns to
  -1. Verified end to end: a typed P15+P33 blend reached the composed frame
  (hash changed against preset mode) and carried P33's 2828 ms trail with the
  tinted tail.
- **Unconfirmed on the phone.** Everything below the math is UIKit and only
  runs there. The modal, the live apply, the sheet detents and the sliders all
  need eyes on a device.
