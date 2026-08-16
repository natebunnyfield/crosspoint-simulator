# The pad's outlines, made actually black and white

**Date:** 2026-08-16
**Branch:** `bw-outlines` (simulator repo)
**Base:** `0835bdc` — *fix(ios): the Dark Mode setting follows the system appearance*
**Owner ask, verbatim:** "making black and white outlines actually black and white"
**Status:** measured and verified on the iOS Simulator; **not run on a physical
device**.

Everything below that is called *measured* was read back out of a screenshot
with `PIL`, not inferred from the source. Everything inferred is labelled.

---

## 1. How to measure a pad colour at all, and the trap in it

`CROSSPOINT_SIM_SCREENSHOTS` captures the **panel**, not the pad — the pad is
`paintPad` in `ios/CrossPointIOSShim.cpp:1063`, which only exists in the iOS
target. So a pad colour can only be measured by building the app, running it on
an iOS Simulator, and screenshotting the device:

```bash
xcrun simctl io <udid> screenshot --type=png shot.png
```

**Use a device whose render resolution equals its panel resolution.** The first
run of this was done on the **iPhone 13 mini**, which renders at 1125×2436 and
downsamples to a 1080×2340 panel. The pad's stroke is one device pixel
(`CrossPointIOSShim.cpp:1091` — `const float hairline = 1.0f`), and the
downsample smears it across three rows so it never reaches its own tone
anywhere. Measured on the 13 mini, the default light stroke:

```
y=1707  #FAFAF8
y=1708  #ECECEA     <- the peak; the palette says #D9D9D7
y=1709  #EAEAE8
```

The total ink is right (1 + 15 + 17 = 33 levels, against a nominal 34) and the
colour is wrong everywhere. On the **iPhone Air** simulator (`crosspoint-x3-air`,
native 1260×2736, no downsampling) the same band contains **exactly two tones**
and the stroke is exact. Every number in this document is from the Air.

This is not a bug in the pad. It is a warning about the measuring instrument:
**on a downsampling phone no outline setting can ever produce its nominal
colour**, including the black-and-white one this change adds.

---

## 2. What the outlines actually were (measured, before)

`padContrastPreset` unset, `panelPalettePreset` = Default, iPhone Air, pad band
= the bottom 28% of the screen.

| appearance | field (paper) | **outline, measured** | tones in the pad band |
|---|---|---|---|
| light | `#FBFBF9` | **`#D9D9D7`** | exactly 2 |
| dark | `#121212` | **`#333333`** | exactly 2 |

Those are levels −1 / +1 of the contrast ladder — 1.364:1 and 1.483:1 — and they
are exactly what `ios/PadPalette.h` documents. **The ladder was doing what it was
designed to do.** The owner looking at a grey hairline and calling it grey was
reading the design correctly, not finding a fault.

Mechanism, for the record:

- `ios/PadPalette.h:105-112` — the shipped `hairline` tones, `#D9D9D7` / `#333333`.
- `ios/PadPalette.h:195-206` — the four delta tables; index `−1 + kContrastOffset`
  is `−34`, `+1 + kContrastOffset` is `+33`.
- `ios/CrossPointIOSShim.cpp:702` and `:845` — the live palette, built with
  `makePaletteOn(dark, outline, fill, panel.paper)`.
- `ios/CrossPointIOSShim.cpp:1120` — `setRGB(r, p.hairline)` then a rounded fill,
  with the face laid back inside it one pixel in.

---

## 3. The real defect: "black" and "white" were neither

This is the part the ask exposes, and it is a genuine bug rather than a taste
question.

The header has claimed since the ladder was written that **−9 is `#000000` and
+9 is `#FFFFFF` in both appearances** (`ios/PadPalette.h:53-55`, and Root.plist
prints those two rows as "20.27:1 — black" and "18.73:1 — white"). That was true
while the field was a constant: the deltas are `−251` / `+6` in light and `−18` /
`+237` in dark, which clamp to the gamut ends **on `#FBFBF9` and `#121212`**.

Then the panel's paper became a dial — `src/PanelPalette.h`, eleven presets plus
four Custom hex fields — and `makePaletteOn` was correctly changed to derive the
pad from whatever paper the owner picked. **A fixed delta cannot reach a fixed
endpoint from an arbitrary start.** Nothing warned; every wrong answer clamped
into a plausible near-miss.

**Measured** (iPhone Air, `padOutlineContrast* = ±9`):

| page colour | appearance | row label | painted |
|---|---|---|---|
| Default | light | 20.27:1 — black | `#000000` ✅ |
| Default | dark | 18.73:1 — white | `#FFFFFF` ✅ |
| Green CRT | light | 20.27:1 — black | `#000000` ✅ |
| **Green CRT** | **dark** | **18.73:1 — white** | **`#EDFFED`** ❌ |

**Computed for the rest** (the arithmetic is `field + delta`, clamped; the four
measured rows above confirm computed == painted, so the table is inference on a
verified model, not a guess). Reproduced exactly by
`tests/pad_palette_test.cpp` §4b, which reports **57 failures** against the old
resolver and 0 against the new one:

| page colour | "black" (−9) | "white" (+9) |
|---|---|---|
| Default light | `#000000` ✅ | `#FFFFFF` ✅ |
| Default dark | `#000000` ✅ | `#FFFFFF` ✅ |
| High Contrast light | `#040404` ❌ | `#FFFFFF` ✅ |
| High Contrast dark | `#000000` ✅ | `#EDEDED` ❌ |
| Sepia light | `#000000` ✅ | `#F8EDD6` ❌ |
| Sepia dark | `#0A0500` ❌ | `#FFFFFD` ❌ |
| Cool Gray light | `#000000` ✅ | `#EEF2F5` ❌ |
| Cool Gray dark | `#000208` ❌ | `#FDFFFF` ❌ |
| Solarized light | `#020000` ❌ | `#FFFCE9` ❌ |
| Solarized dark | `#001924` ❌ | `#EDFFFF` ❌ |
| Green CRT light | `#000000` ✅ | `#E2F5DE` ❌ |
| Green CRT dark | `#000800` ❌ | `#EDFFED` ❌ |
| Amber CRT light | `#000000` ✅ | `#FBECCE` ❌ |
| Amber CRT dark | `#080000` ❌ | `#FFFDED` ❌ |
| Nord light | `#000000` ✅ | `#F2F5FA` ❌ |
| Nord dark | `#1C222E` ❌ | `#FFFFFF` ✅ |
| Gruvbox Light light | `#000000` ✅ | `#FFF7CD` ❌ |
| Gruvbox Light dark | `#161616` ❌ | `#FFFFFF` ✅ |
| Latte light | `#000000` ✅ | `#F5F7FB` ❌ |
| Latte dark | `#0C0C1C` ❌ | `#FFFFFF` ✅ |

**Default — and only Default — was honest at both ends**, in either appearance:
18 of the 20 palette halves got at least one end wrong, 24 wrong cells in the
outline ladder alone. High Contrast, the palette whose entire premise *is* the
gamut ends, painted `#040404` for black on its white paper and `#EDEDED` for
white on its black one.

The thresholds, for anyone re-deriving this: in dark, `+9` reaches white only if
every paper channel is ≥ 18 and `−9` reaches black only if every channel is ≤ 18;
in light the two are ≥ 249 and ≤ 251.

---

## 4. What was changed

Three things, none of which removes anything.

### (c) The two end rungs are absolute — `ios/PadPalette.h`

`toneChannelAt(field, table, level)` resolves `−9` to `#000000` and `+9` to
`#FFFFFF` on **any** field; every rung between them is still a delta on the
field. `makePaletteOn` paints through it.

This is the bug fix, and it is a prerequisite for anything else: without it a
"black and white" preset cannot produce white on a Green CRT page.

New compile-time guards assert the ends on papers that are **not** the shipped
one (Green CRT dark, High Contrast light, Sepia dark). The previous eight
`static_assert`s all passed throughout the defect, because all eight were
written against the two shipped fields.

`tonesDistinct` now runs over **levels** through the resolver rather than over
raw table entries, so the no-dead-zone guard covers the ends too.

### (b) A new preset — Black & White

`kPresetBlackWhite = 4`, appended (the value persists as an integer in
`NSUserDefaults`, so inserting would re-point saved choices).

- **outline** at the absolute gamut end away from the field: `#000000` light,
  `#FFFFFF` dark, on every page colour.
- **wash** left on the 3:1 rung (`−5` / `+5`). Deliberate: a stroke covers a line
  and a wash covers a 58.8 pt cell, so `±9` on the fill would flip the whole
  interior of a held control to solid black or solid white — a *different*
  control appearing under the finger rather than the same one filling.

### (a) It is the default — `ios/Settings.bundle/Root.plist`

`padContrastPreset` `DefaultValue` 1 → 4, and the fallback in
`ios/CrossPointPrefs.mm:160` with it (that branch only runs if Root.plist is
unreadable, so a drift there is invisible until a packaging fault exposes it).

**Why all three rather than just the preset.** The ask is that the outlines *be*
black and white, not that a row exists which would make them so. A preset the
owner has to go and find does not answer it. Making it the default does, and it
costs nothing that a preset would not have cost, because **the preset row is
itself the undo**: `Current` is still in the list, still resolves to the same
±1 levels, and still paints `#D9D9D7` / `#333333` byte-for-byte (pinned by
`pad_palette_test` §1 and §7b). Accessible, Transparent and all four fine
pickers are untouched.

`migratePadPresetForExistingCustomisation` (`CrossPointPrefs.mm:113`) is
unaffected and still does the right thing: an install whose fine pickers were
customised is migrated to `Custom` and keeps its look; only a genuinely
untouched install moves to Black & White.

---

## 5. What it looks like (measured, after)

Preset = Black & White. Outline read back out of the pad band:

| page colour | appearance | field | **outline, measured** |
|---|---|---|---|
| Default | light | `#FBFBF9` | **`#000000`** |
| Default | dark | `#121212` | **`#FFFFFF`** |
| Green CRT | light | `#DCEFD8` | **`#000000`** |
| Green CRT | dark | `#001A00` | **`#FFFFFF`** |
| Sepia | dark | `#1C1710` | **`#FFFFFF`** |
| Amber CRT | dark | `#1A1000` | **`#FFFFFF`** |
| Solarized | light | `#FDF6E3` | **`#000000`** |

And with the app's whole `NSUserDefaults` domain **deleted** — a genuinely
untouched install, no key written for anything:

| appearance | field | **outline, measured** |
|---|---|---|
| light | `#FBFBF9` | **`#000000`** |
| dark | `#121212` | **`#FFFFFF`** |

---

## 6. The interaction with the coloured page palettes

The parent question was whether a pure-white outline is right on Green CRT's
`#001A00` paper. Rendered, looked at, and the answer is **asymmetric**:

**Black on a tinted LIGHT paper is fine.** Green CRT light (`#DCEFD8` paper,
`#0B3D0B` ink): the black outline sits comfortably beside the panel's own dark
green chrome. Nothing reads as foreign. Same for Solarized light.

**White on a tinted DARK paper fights the palette.** Green CRT dark and Amber
CRT dark both show it clearly: the pad's white capsules are the **only
non-phosphor element on the screen**, brighter and cooler than anything the
palette contains, and they read as another app's chrome parked under a CRT page.
The pad band holds exactly two tones, `#001A00` and `#FFFFFF`, while the panel
above it is drawing `#33FF33` — three tones on a screen whose palette specifies
two.

The mechanism, which is why light and dark differ:

| palette | paper | chroma of paper | B/W vs paper | palette's own ink vs paper |
|---|---|---|---|---|
| Green CRT dark | `#001A00` | 0.102 | 18.30:1 | 13.50:1 |
| Amber CRT dark | `#1A1000` | 0.102 | 18.78:1 | 10.25:1 |
| Solarized dark | `#002B36` | 0.212 | 15.01:1 | 4.75:1 |
| Default dark | `#121212` | 0.000 | 18.73:1 | 14.17:1 |
| Green CRT light | `#DCEFD8` | 0.090 | 17.38:1 | 10.31:1 |
| Default light | `#FBFBF9` | 0.008 | 20.27:1 | 13.29:1 |

A tinted **light** paper is a high-luminance, low-chroma tint, and black is a
plausible extension of its own dark ink. A tinted **dark** paper is a
*saturated hue at low luminance*, and white is the maximum-luminance **neutral**
— precisely the thing the palette went out of its way to exclude. The clash is
hue, not contrast: white wins the contrast comparison by 5 points and still
looks wrong.

**Proposed rule, NOT implemented** (it is a new design, and the owner asked for
black and white, not for this): on a monochrome page, "the two ends" arguably
means *that page's* two ends — paper and **ink** — not the sRGB gamut's. An
outline at `#33FF33` on Green CRT dark would be perfectly in-palette at 13.50:1,
which clears every bar the pad has ever set. That would be a fifth preset
("Page Ink"), not a change to Black & White, whose name commits it to `#000000`
and `#FFFFFF`. See the open questions.

---

## 7. Verified vs not verified

**Verified**

- Baseline and post-change outline hexes, read out of iPhone Air screenshots at
  native 1260×2736 (§2, §5). Pad band contains exactly two tones in every case.
- The default lands on Black & White with the app's defaults domain deleted.
- `tests/run_all.sh`: **20 passed, 0 skipped**.
- `pad_palette_test` fails **57 times** against the old resolver and 0 against the
  new one, so the new coverage is not vacuous. The five new `static_assert`s
  also fail to compile against the old resolver, by name.
- `pio run -e simulator` from the firmware repo: SUCCESS, before and after.
- The iOS app builds clean for `arm64-apple-ios`.

**NOT verified**

- **Nothing here has run on a physical iPhone.** Everything is the iOS
  Simulator.
- Only the **outline** was rendered. The Black & White **wash** (the pressed
  state) is covered by unit tests and by the ladder's arithmetic, but no
  screenshot in this pass shows a control being held.
- §3's second table is produced by running the test against the pre-fix
  resolver, i.e. it is the model's own output, not 20 separate screenshots. Four
  of its cells (the ones in the first table) were confirmed against real pixels;
  the rest are inference on that verified model.

---

## 8. Open questions for the owner

1. **Should white outlines follow a tinted dark palette's hue instead of being
   pure white?** §6 says a pure-white pad fights Green CRT and Amber CRT. The
   fix would be a *fifth* preset that puts the outline on the page's own ink
   (`#33FF33` on Green CRT dark, 13.50:1), leaving Black & White meaning
   literally black and white. Not built.
2. **Is the default change wanted, or should Black & White be opt-in?** It is
   the default here on the reading that "make my outlines black and white" means
   the pad, not a settings row. One tap to `Current` restores the old grey
   exactly; nothing was removed.
3. **Nothing has been run on a physical phone.** On a downsampling panel (the
   13 mini does this in the Simulator, and any phone whose render size exceeds
   its panel does it in hardware) the 1-px stroke is blended and *no* setting
   reaches its nominal colour — see §1. Worth a look on the real device before
   this is called done.
