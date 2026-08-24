# The phosphor mixer

Added 2026-08-20. Math in [`src/PhosphorMix.h`](../src/PhosphorMix.h) (pure,
host-tested by `tests/phosphor_mix_test.cpp`), UI in
[`ios/CrossPointPaletteMixer.mm`](../ios/CrossPointPaletteMixer.mm).

## SUPERSEDED UI: the P22 gun mixer (2026-08-21)

Owner, after using the shipped modal on device: *"the mixer ui sucks and
doesn't actually mix colors. let's keep it simple and just make a ui for only
p22. ignore everything else for now."* Then, clarifying the observed failure:
*"I'm not seeing colors actually mixed together. the 'flash' is the only color
I see and its persistence is affected by the other color."*

Two separate facts behind that report, both verified on the iOS Simulator the
same day:

1. **The page's live path was fine.** A `defaults write` of the four custom hex
   fields while the app ran repainted the page within a frame (magenta probe,
   pixel-verified). The break was in what the old four-tab UI wrote, not in the
   poll.
2. **The glow told the truth the page didn't.** `CrossPointMixer_glowForCustom`
   computes from the CSV directly, so persistence responded while color did
   not — and P22G's trail is 63 ms against P22R/P22B's 283 ms, so any two-gun
   mix carries a color-shifting tail in the slower gun's dark ink. "The flash
   in one color with the other's persistence" is exactly a working glow over a
   never-updated page.

The whole four-tab UI (Presets / Blend / Parts / Cascade tables, banded
ingredient shelf, premix recipe loader) is REMOVED from
`ios/CrossPointPaletteMixer.mm`. What replaced it is the one mixer a real
color tube had: **three gun sliders** — P22R (preset 11), P22G (40), P22B (24),
weights 0–100, 0 = gun off — live-applying through `phosphormix::mixBlend`
into the Custom slot as they move, the page behind the medium-detent sheet
being the preview. Verified end-to-end headlessly: `CROSSPOINT_SIM_MIX_GUNS=
"80,60,10"` drives `CrossPointMixer_applyGunsForTest` (the sliders' own apply
function) and the rendered page pixel matched the core's computed paper
(F3EFE7 warm white, minus grain).

**The core is untouched.** All three modes, the fitted premix recipes, the
bands, the sort — everything below the UI stays, tests included, and the
desktop `settings.json` keys still read any stored mix. "Ignore everything
else FOR NOW" is a narrowing of the UI, not a deletion of the model; the
sections below record the full design for when it comes back.

### 2026-08-21: four assignable guns (RGBW)

Same day, the gun mixer grew from three fixed P22 guns to **four assignable
guns** named **R / G / B / W** — the industry-standard four-emitter channel
scheme (owner delegated the naming pick). Each gun's name row is now a menu
button: any preset passing `phosphormix::isMixablePreset` can be assigned,
with the menu grouped into the core's persistence bands (`trailBand` /
`trailBandName`) and ordered within each band by `shelfSortKey` — the same
grouping and order as the shelves below. Defaults: R=P22R (11), G=P22G (40),
B=P22B (24), W=P45 (`kPresetWhiteCrt`, 21). **W ships at weight 0**, so a
fresh open renders the same page the three-gun build did. Assignments persist
in a new `phosphorGunAssign` CSV of four preset ints; `phosphorMixBlend`
stays the mix of record, now carrying all four "preset:weight" pairs
(weight-0 guns included, as before). The hand-placed Done button is gone: the
sheet is now a `UINavigationController` with a standard nav-bar Done item (no
title string is ever set — the build 110 crash sidestep holds).
`CROSSPOINT_SIM_MIX_GUNS` takes "r,g,b,w" (a three-value CSV still parses,
w=0; assignments are always the defaults).

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

The long-press half went with the four-tab UI on 2026-08-21, but the table
below is live again from 2026-08-23: it is what `seedForPreset` loads into the
guns when a blend premix is selected. See "Selecting a preset seeds the guns".

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

The computed result is written into the **Custom slot's DARK hex fields**
(`panelInkDark`/`panelPaperDark`), and `panelPalettePreset` is pointed at Custom
through `CrossPointPrefs_claimCustomFor(/*editingDark=*/1)` — so `resolve()`,
the pad tint and the keyboard chips all keep working without learning anything.

**DARK ONLY, since 2026-08-23.** It used to write all four, which was correct
while this was the editor for both appearances and became a bug on 2026-08-22
when the doctrine split them: light is paper and ink with its own historical-ink
picker (`docs/light-ink-picker.md`), dark is the CRT and keeps this mixer. The
chip's branch moved and this write did not, so every gun move in dark mode
silently overwrote the light page's chosen ink — owner P1, "ink is not being
picked up". Measured: an applied Payne's Gray (`panelInkLight` `323D47`, page
text (30,37,43)) became `6E0500` and (64,3,0) after one slider move.

`claimCustomFor` is the shared protocol both editors use: it freezes the OTHER
polarity's currently-rendered pair (and, when that polarity is dark, its
phosphor) before the shared preset integer moves, and does nothing at all once
the slot is already Custom — by then both polarities hold owner choices.
Decided in [src/PanelSource.h](../src/PanelSource.h), pinned by
`tests/panel_source_test.cpp` and `tests/panel_source_test.py`.

The mixer's LIGHT swatch is **gone** (owner 2026-08-23, "drop the light swatch
entirely"). It previewed the blend's light rendition, which is a true property
of the phosphor mix but stopped being what the light page renders the day the
doctrine split handed light to its own ink picker — and, once this editor claims
the Custom slot, the light pair is frozen rather than computed, so the swatch
was previewing a page that could not appear. The dark ground now takes the whole
swatch row; row height and everything below it are unchanged. `Result::light` is
untouched: a preset still defines both appearances and `claimCustomFor` still
needs the light pair to freeze. The hex readout below the swatch still prints
`light XXXXXX on YYYYYY` — it is a recipe number, not a preview, and the ruling
named the swatch.

Two additions only:

- `pollPanelGlow` asks `CrossPointMixer_glowForCustom()` when the preset is
  Custom, because plain Custom has no phosphor and would get trail 0 while a
  mix has its own decay and tail.
- The poll dedupes on the preset integer, which does not move while editing a
  mix already on Custom — `CrossPointMixer_glowChanged()` marks it dirty.

The mix itself persists in `phosphorMix*` NSUserDefaults keys (mode, a
`preset:weight` CSV for the blend, role assignments for the others). Picking a
plain preset sets `phosphorMixActive` to NO but leaves the recipe stored, so
moving any gun afterwards restores it.

## Getting back to a named preset (2026-08-23)

Owner ruling: **"add a Presets row back to the pickers."** `claimCustomFor` only
ever points the shared integer AT Custom, and the Settings.app palette row left
with the other page rows on 2026-08-22 — so one gun move made every named preset
unreachable as a preset.

A **Presets bar button** now sits opposite Done and pushes
[ios/CrossPointPresetList.mm](../ios/CrossPointPresetList.mm), the same list the
light-mode ink picker pushes. Pushed onto this sheet's own navigation
controller, so nothing about the sheet changes: it is still medium-detent-only
with no grabber (owner 2026-08-21, "the color tray is very slideable"). The
cells preview the **dark** pairs here, because this is the dark page's editor;
every preset is offered in both lists, since a preset defines both appearances.

Selection is `panelsource::releaseCustom`, the inverse of the claim: both
polarities go back to the preset, and `phosphorMixActive` and
`panelDarkSnapshotPreset` are cleared rather than left. Clearing the mix flag is
the load-bearing half — `glowPreset` asks it BEFORE the frozen phosphor, so a
stale mix would own the decay of a preset chosen after it, and would only start
doing so at the NEXT claim, long after the change that caused it.

Moving a gun after selecting a preset claims the slot back and resumes the
recipe — with the light page frozen at the preset's own light pair, through the
same shared claim. What the recipe *is* at that moment changed on 2026-08-23:
see the next section.

While a named preset is in force, this sheet's readout names the preset rather
than the mix's hex: the mix is still a valid recipe and is simply not what is on
screen, and a drawer describing a page it no longer owns is the lie S-020
shipped.

Measured on an iPhone Air simulator, 2026-08-23: with a P22R-only mix in force
(`FF6F6C` on `1A0300`, glow "phosphor mix"), selecting White CRT gave
`[harness] panel palette (dark) -> preset 21, ink B6EFFF, paper 182327` and
`[glow] preset 21 -> 283 ms trail ... (Medium)`, with `phosphorMixActive` false
and `phosphorMixBlend` still `11:100,40:0,24:0,21:0`. A light-mode ink pick
after that froze phosphor 21, not the dead mix.

## Selecting a preset seeds the guns (2026-08-23)

Owner request: **"selecting a preset should set the guns' values too."** Until
this landed, a selection moved the page and left the stored recipe untouched, so
opening the mixer afterwards showed a blend from some earlier session and the
first slider move *jumped* the page to it instead of nudging it.

The rule is one sentence: **seed the guns when, and only when, the preset's page
is a four-gun blend of pure phosphors; otherwise leave the stored recipe exactly
as it is.** The decision is `phosphormix::seedForPreset`
([src/PhosphorMix.h](../src/PhosphorMix.h), pure and host-tested); the store
adapter is [ios/GunStore.h](../ios/GunStore.h), which is now the only file that
names `phosphorGunAssign` and `phosphorMixBlend`; the caller is
`CrossPointPrefs_selectPanelPreset`, immediately after the release.

Four categories, exhaustive over the shipped table (34 + 5 + 3 + 10 = 52):

| Category | Rows | Seed |
|---|---|---|
| Pure phosphor | 34 | one gun at 100, the other three at 0 |
| Blend premix | P4 P6 P18 P23 P40 | its fitted recipe from `kPremixRecipes` |
| Cascade premix | P7 P14 P17 | none — the guns are left |
| No phosphor (paper) | 10 | none — the guns are left |

**The pure case is EXACT.** `mixBlend` of one component is `resolve()` of that
preset, in both polarities, byte for byte — so the recipe the mixer shows is not
an approximation of where the page is, it is where the page is, and the next gun
move is a nudge.

**The blend premixes reuse the fitted table above**, which was refitted for
exactly this ("a long-press loads it into the mixer as an editable recipe"). The
weights scale by an **integer** factor so the ratios survive intact — `mixBlend`
normalizes by the total, so only ratios render, and a rounded seed would be a
different mixture from the one the table was fitted to. P23's 9:4 becomes 99:44,
P18's 2:7:1 becomes 28:98:14. A premix page and its seed therefore differ by the
fit's ΔE and by nothing the seed adds.

**The cascades are a refusal, not a gap.** A cascade is two layers in sequence:
the flash layer paints the page, the persistence layer is what lingers, in its
own color. No blend is both — zero the persistence gun and there is no
afterglow; give it weight and it tints a page the cascade never tints. Seeding
one would put a recipe in the mixer that renders a *different* page from the one
on screen, which is S-020 pointing the other way. The test asserts the refusal
against the naive alternative, so the choice has to keep earning itself.

**A paper preset touches nothing**, for the same reason plus the doctrine: paper
rows are exactly the rows the light ink picker offers
(`presetOfferedInDark` is false there), light is paper and ink, and the guns are
the dark page's editor.

**The mix is not switched on.** `phosphorMixActive` stays false and the preset
goes on owning the page; the guns are seeded to *match*, not activated.

**The assignment is disturbed as little as possible.** A phosphor already on a
gun lights that gun — selecting White with the shipped assignment lights W and
reads as itself — and only a phosphor on no gun displaces one, which is gun 0.
The other guns keep their phosphor at weight 0.

Measured on an iPhone Air simulator (`663B0B14`), 2026-08-23, from a clean
install, reading `Library/Preferences/com.natebunnyfield.crosspoint.x3.plist`:

| Step | `panelPalettePreset` | `phosphorGunAssign` | `phosphorMixBlend` | `phosphorMixActive` |
|---|---|---|---|---|
| one gun moved | 0 (Custom) | `11,40,24,21` | `11:100,40:20,24:0,21:0` | true |
| select White (P45) | 21 | `11,40,24,21` | `11:0,40:0,24:0,21:100` | false |
| select White Warm (P23) | 41 | `21,23,24,21` | `21:99,23:44,24:0,21:0` | false |
| select Cascade (P7) | 25 | `21,23,24,21` | `21:99,23:44,24:0,21:0` | false |
| select Sepia (paper) | 3 | `21,23,24,21` | `21:99,23:44,24:0,21:0` | false |

White landed on the W gun it was already assigned to. The two refusals left the
recipe byte for byte. The page followed the preset in every case: Green CRT's
page measured modal paper `CDE0CB` and ink `062206` against its `0B3D0B` on
`DCEFD8` pair (the light surface stack darkens both), Sepia's `EDE2CC` /
`231D18` against `3B3228` on `F2E7D0`.

The readout says which case a preset is: `Preset White — the guns are set to
it / move one to take over`, against `Preset Cascade — a cascade, not a blend /
the guns keep their own recipe`. It compares the arrays to the seed rather than
trusting `seed.apply`, because a readout that trusts its own reasoning instead
of the store is the exact shape of the bug this area was rewritten for.

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

## The preset list shows only this page's presets

Owner ruling 2026-08-23: *"only show presets available in that mode."*

The mixer offers the **42 phosphors**; the light ink picker offers the **10
papers**. The partition falls out of the table rather than needing a flag --
`panelpalette::presetOfferedInDark` is `trailMsForPreset(preset) > 0`, because a
preset with a decay IS a tube -- and it is the 2026-08-22 doctrine restated, not
a new rule.

What it filters is the OFFERING, not the definition. Every preset still resolves
both appearances, so choosing Green CRT here sets the light page too. The reason
to filter is that a phosphor listed under a paper page previews a rendition that
page will never show, and the reverse.

`tests/panel_source_test.cpp` pins the partition as TOTAL and non-empty on both
sides: a preset offered by neither list would be unreachable, which is the exact
way the presets were lost before this list existed.
