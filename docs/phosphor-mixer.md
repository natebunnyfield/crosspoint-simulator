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

## Mix candidates — 36 blends in the 127 ms–1.1 s window

Owner request 2026-08-21, placement ruled "just the proof html page": a curated
exploration, not presets and not a library table. Recorded here so the next
session does not regenerate them — every one was computed by the shipped core
(`mixBlend` over 2–3 pure rows, P10 excluded as ever), selected from 715,118
in-window blends for mutual distinctness and fade spread. White means chroma
C\* < 20 on a bright ink; warm needs b\* > 6 **and** a\* > −4 (the first
classifier split on b\* alone and called mint-green "warm"); cool is the
mirror; colored requires C\* ≥ 28. The CSV column is the mixer's own
`preset:weight` form — paste it into `settings.json`'s `phosphorMixBlend` or
rebuild it in the Blend tab.

**Warm whites**

| Name | Recipe | Dark pair | Fade | CSV |
|---|---|---|---|---|
| Ivory Rose | P11 2 : P22R 3 : P53 2 | `BCB0A7` on `0E0C0B` | 283 ms | `15:2,11:3,54:2` |
| Candle | P28 5 : P45 9 : P56 2 | `DADBCD` on `1B1B1C` | 283 ms | `46:5,21:9,23:2` |
| Dusk Linen | P3 7 : P45 5 : P47 3 | `DBC9C1` on `16171B` | 322 ms | `7:7,21:5,22:3` |
| Parchment | P3 1 : P45 1 : P56 1 | `EAC5B4` on `1E1514` | 322 ms | `7:1,21:1,23:1` |
| Clay | P11 1 : P1 1 : P13 3 | `D4B4B0` on `120809` | 400 ms | `15:1,6:1,31:3` |
| Hearth | P1 3 : P16 5 : P22R 9 | `D7A5A6` on `120809` | 400 ms | `6:3,34:5,11:9` |
| Sandstone | P11 2 : P20 1 : P28 2 | `C3C2AA` on `0E0F0D` | 400 ms | `15:2,38:1,46:2` |
| Amber Veil | P11 1 : P20 1 : P22R 2 | `CEAA9A` on `110B09` | 400 ms | `15:1,38:1,11:2` |
| Lamplight | P12 2 : P28 5 : P45 5 | `E4D4B2` on `191917` | 693 ms | `30:2,46:5,21:5` |
| Old Paper | P19 3 : P45 5 : P56 9 | `EDBFBF` on `211112` | 1.1 s | `37:3,21:5,23:9` |
| Firelight | P2 3 : P16 3 : P26 7 | `D3BEA7` on `110B09` | 1.1 s | `26:3,34:3,44:7` |
| Tungsten | P11 2 : P22R 5 : P39 3 | `C4B18F` on `101407` | 1.1 s | `15:2,11:5,19:3` |

**Neutral whites**

| Name | Recipe | Dark pair | Fade | CSV |
|---|---|---|---|---|
| Moonstone | P28 1 : P45 9 : P56 2 | `CCE2E9` on `1B1E21` | 283 ms | `46:1,21:9,23:2` |
| Dove | P16 2 : P22R 5 : P24 5 | `BBC4B6` on `0E0E0D` | 283 ms | `34:2,11:5,42:5` |
| Fog | P3 9 : P11 7 : P45 9 | `CCC3D1` on `14171A` | 322 ms | `7:9,15:7,21:9` |
| Silverpoint | P11 7 : P1 5 : P25 5 | `ACBDBE` on `090D0E` | 400 ms | `15:7,6:5,43:5` |
| Limestone | P3 2 : P12 2 : P45 5 | `DAD4CA` on `191B1B` | 693 ms | `7:2,30:2,21:5` |
| Gallery | P11 2 : P2 2 : P22R 3 | `BCB0A8` on `0E0C0B` | 1.1 s | `15:2,26:2,11:3` |

**Cool whites**

| Name | Recipe | Dark pair | Fade | CSV |
|---|---|---|---|---|
| North Sky | P28 1 : P45 9 | `BFEBF3` on `182225` | 283 ms | `46:1,21:9` |
| Harbor | P22G 7 : P11 9 : P28 3 | `90CACA` on `051012` | 283 ms | `40:7,15:9,46:3` |
| Frost | P3 1 : P45 9 : P47 7 | `B9D6F8` on `111926` | 322 ms | `7:1,21:9,22:7` |
| Glacier | P3 1 : P11 7 : P1 3 | `8CBBD2` on `030E13` | 400 ms | `7:1,15:7,6:3` |
| Pewter | P12 2 : P22B 1 : P45 3 | `D1D0DD` on `16181F` | 693 ms | `30:2,24:1,21:3` |
| Ice | P11 7 : P2 1 : P28 3 | `B1AFD3` on `090C13` | 1.1 s | `15:7,26:1,46:3` |

**Colored**

| Name | Recipe | Dark pair | Fade | CSV |
|---|---|---|---|---|
| Blue Beat | P11 9 : P22B 1 | `8F95FF` on `00051C` | 283 ms | `15:9,24:1` |
| Violet Beat | P5 9 : P35 5 : P56 9 | `D6AFE1` on `190412` | 283 ms | `27:9,49:5,23:9` |
| Orange Beat 2 | P22B 2 : P28 7 : P56 9 | `F8B494` on `1F0807` | 283 ms | `24:2,46:7,23:9` |
| Orange Beat | P3 9 : P22R 5 : P28 1 | `FFA03F` on `1A0C00` | 322 ms | `7:9,11:5,46:1` |
| Sky Beat | P22G 2 : P11 7 : P1 1 | `77BCE3` on `000E16` | 400 ms | `40:2,15:7,6:1` |
| Teal Beat | P1 1 : P24 9 : P45 7 | `7AF9DC` on `0C1E1C` | 400 ms | `6:1,42:9,21:7` |
| Gold Beat | P3 1 : P20 5 : P28 5 | `D1E100` on `131500` | 400 ms | `7:1,38:5,46:5` |
| Rose Ember | P11 2 : P12 1 : P22R 7 | `EE7D9A` on `160407` | 693 ms | `15:2,30:1,11:7` |
| Teal Long | P22G 1 : P2 2 : P15 1 | `00FF94` on `00190A` | 1.1 s | `40:1,26:2,33:1` |
| Gold Long | P22R 9 : P24 3 : P39 5 | `C0C476` on `111603` | 1.1 s | `11:9,42:3,19:5` |
| Chartreuse Long | P22G 3 : P20 5 : P26 3 | `A3EA6B` on `0C1503` | 1.1 s | `40:3,38:5,44:3` |
| Green Long | P1 1 : P39 9 | `0BFF0B` on `002600` | 1.1 s | `6:1,19:9` |

## Not done, said plainly

## The shelf is banded by persistence

Owner ruling 2026-08-21: "group ingredient shelf by natural breaks of
persistence fade." The five bands are the data's own gaps, not round numbers —
sorting the 34 pure trails, the ratio jumps sit at 20→63 ms, 126→283,
400→693 and 1095→2828. `trailBand()` / `trailBandName()` in PhosphorMix.h are
the single definition; the mixer's Blend/Parts/Cascade shelves section by them
and the proof page groups its table the same way. The test pins that every pure
row lands in a band, no band is empty, and the edges sit in the gaps.

**Within a band: trail, then hue, red first** (owner ruling 2026-08-21). A band
is nearly one persistence by construction, so trail splits its one or two real
steps and hue orders the rest — the wheel rotated +15° so the reds at 340–355°
wrap to the front, the palette list's own convention. `shelfSortKey()` is the
single definition; the mixer's shelves sort by it and the proof page uses the
same key from the dump. Two bugs the test caught in the first draft, kept as a
warning: the rotation ran the wrong way and put every red LAST, and a
"near-neutral whites last" case never fired because our whites are tinted
blue-whites at saturation ~0.29, inseparable from real blues — they now simply
sort as the blue-ish hues they are.

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
