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
survive renumbering, and the mapping from JEDEC compounds to this repo's pure
rows is **approximate by construction** — sometimes exact (P4's
`(Zn,Cd)S:Cu,Al` IS P22G), sometimes only a behavioral cousin (P7's long
`(Zn,Cd)S:Cu` layer has no pure row; P34 is the nearest long yellow-green). A
loaded recipe therefore does not reproduce the shipped premix byte-for-byte.
The section footer in the modal says so, so the difference reads as stated
rather than as a bug.

| Premix | Recipe |
|---|---|
| P4 | Blend: P22B + P22G, 3:3 |
| P6 | Blend: P22B + P20, 3:3 |
| P18 | Blend: P16 + P13, 3:3 |
| P23 | Blend: P22B + P20, 3:4 (warm — weighted toward the yellow) |
| P40 | Blend: P22B + P34, 3:3 |
| P7 | Cascade: flash P22B, persistence P34 |
| P14 | Cascade: flash P22B, persistence P26 |
| P17 | Cascade: flash P15, persistence P28 |

The test pins that every premix has a recipe, every component resolves to a
real pure row (never a premix), and P4's exact-compound match stays exact.

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

- **Desktop parity.** The Mac's `settings.json` cannot express a mix; a
  mix-built page shows on the Mac only through the four custom hex fields if
  copied by hand, without the glow. The keys are documented above if it is ever
  wanted.
- **Unconfirmed on the phone.** Everything below the math is UIKit and only
  runs there. The modal, the live apply, the sheet detents and the sliders all
  need eyes on a device.
