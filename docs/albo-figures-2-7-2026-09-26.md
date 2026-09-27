# The 2 and the 7, traced from the reference faces (2026-09-26, round 406)

Owner, 2026-09-26: *"give me options of redoing the 2 and 7 based on tracing
other reference fonts, both roman and italic"*.

- **Nothing ships.** Four new option letters, `o p q r`, in both styles for both
  figures. `FIG_SHIP_ROM` / `FIG_SHIP_IT` are unchanged. Built from `52ef9f8` +
  this change; the default build of all four cuts is **outline- and
  advance-IDENTICAL** to the control (`cmp_outlines.py --advances`, 530 of 530
  glyphs, Regular, Italic, Bold, BoldItalic).
- Each arm moves **exactly 9 glyphs**: `two`, `seven`, their superiors and
  inferiors, `onehalf`, `twothirds`, `seveneighths`.
- **Drive it:** `ALBO_FIG_2=<letter> ALBO_FIG_7=<letter>` with the build
  environment from `build_env.sh`. The two dials are independent, so the
  recommendation below mixes letters.
- **Code:** `tools/wedge_serif/outlines/glyphs/figures.py`, tables
  `TWO_TRACE_ROM`, `TWO_TRACE_IT`, `SEVEN_TRACE_ROM`, `SEVEN_TRACE_IT`, plus the
  new levers in `g_two` and `g_seven`.
- **Instruments:** `tools/wedge_serif/instruments/fig27_trace.py` (the
  measurement) and `fig27_sheet.py` (the one-image sheet).
- **Confidence:** every number here is measured on built fonts unless it is
  marked [inf].

---

## 0. The answer

| style | letter | 2 traces | 7 traces |
|---|---|---|---|
| roman | o | Georgia | Georgia |
| roman | p | Palatino | Palatino |
| roman | q | Hoefler Text | Hoefler Text |
| roman | r | Big Caslon | Big Caslon |
| italic | o | Flanker Griffo | Flanker Griffo |
| italic | p | Palatino Italic | Palatino Italic |
| italic | q | Georgia Italic | Georgia Italic |
| italic | r | Poetica | Poetica |

**Recommended:**

- **Italic: `o` for both figures (Flanker Griffo).**
  - The fit audit's two italic figure flags both clear. The 2 goes from
    F 1.61 to 0.00. The 7 goes from F 2.00 to 0.76.
  - In BoldItalic the 7 goes from 1.48 to 0.50.
  - Every gate is clean in all four cuts.
  - The cost: it sets aside three rulings on the italic 7. These are round 212
    (the curve to an upright foot), round 215 (the press) and round 219 (the
    tapering bar and the thinning leg). Flanker does none of the three.
- **Roman: the 2 from `q` (Hoefler Text) and the 7 from `p` (Palatino).**
  - The roman 2 is not flagged today (F 0.00). `q` keeps it clean (0.06) and
    brings the **Bold 2's contrast flag** from F 2.99 down to 0.70 (0.31 as a
    lone arm).
  - `p` is the best-fitting 7 of the five, today's included: F 0.69 goes to
    0.32, and the Bold goes from 1.46 to 1.02.
  - The cost: in running text the 7 reads lighter by color (see §4).
- Measured as one set (`2q 7p` roman, `2o 7o` italic):
  - the Italic flag list loses the 7 (9 flagged to 8);
  - the Bold flag list loses the 2 (15 to 12);
  - Regular and BoldItalic are unchanged in count (14, 6);
  - every gate is clean in all four cuts.

## Owner ruling, 2026-09-26

- **Roman:** *"\* 2 from q + 7 from p"* wins. It shipped as round 407
  ([albo-round-407-2026-09-26.md](albo-round-407-2026-09-26.md)):
  `FIG_SHIP_ROM` 2 → `q` and 7 → `p`, in Regular and Bold. The roman 7 reads
  about 15% lighter by color than the other figures (−15% against −5% before),
  and he accepted that.
- **Italic:** *"need variations on p"* (Palatino Italic). These are round 408,
  in the section at the end of this file.

---

## 1. The references and what "tracing" means here

Tracing is **measurement, not copying**. `fig27_trace.py` renders each
reference's own old-style 2 and 7 with FreeType, NO HINTING. It unshears each
italic by its **measured** slant (the `l`'s axis, as `refs_registry.py`
requires) and scales so the face's x-height lands on Albo's 429 units, at
2 px per unit. It then reads the skeleton and the weight, with every stroke over
**that face's own n stem**. The arms are Albo's own pen construction, set to
those numbers and re-measured with the **same function** on the built font. No
outline point of any reference is used.

| face | figures | glyphs read | slant (measured) | n stem (units at xh 429) |
|---|---|---|---|---|
| Georgia | old-style by default | `two` `seven` | 0.0 | 81.0 |
| Hoefler Text | old-style | `two.oldstyle` `seven.oldstyle` | 0.0 | 90.0 |
| Palatino | old-style alternates | `twooldstyle` `sevenoldstyle` | -0.1 | 73.5 |
| Big Caslon | old-style by default | `two` `seven` | 0.0 | 75.5 |
| Charter | **lining only** | `two` `seven` | 0.0 | 74.0 |
| Baskerville | **lining only** | `two` `seven` | 0.0 | 74.5 |
| Georgia Italic | old-style | `two` `seven` | 13.1 | 79.5 |
| Hoefler Text Italic | old-style | `two.oldstyle` `seven.oldstyle` | **13.4 (off its `I`)** | 109.0 (suspect) |
| Palatino Italic | old-style alternates | `twooldstyle` `sevenoldstyle` | 12.0 | 69.5 |
| Flanker Griffo Italic | `onum` | `two.onum` `seven.onum` | 11.8 | 82.0 |
| Poetica | old-style by default | `two` `seven` | 9.2 | 66.0 |
| TeX Gyre Pagella Italic | old-style alternates | `two.oldstyle` `seven.oldstyle` | 11.8 | 71.0 |
| Charter Italic | **lining only** | `two` `seven` | 11.2 | 71.0 |
| Baskerville Italic | **lining only** | `two` `seven` | 16.9 | 67.5 |

Notes on the table:

- **Hoefler Text Italic's `l` is not a bare stem.** Read the `l`'s way, the
  face measures 21.0 degrees (15.0 on the upper half). Unsheared by 21 its
  figures leaned left, which is how the problem was caught. Its `I` reads 13.4
  and 13.2, and `post` says 13.5. Its n stem, 109, is also out of line with every
  other face, so **no arm traces Hoefler Italic**. Its row is kept for the
  record.
- **Charter and Baskerville have no old-style figures on this machine**, in
  either style (checked by glyph name; neither face carries an alternate).
  Their shapes are measured and tabled, but no arm traces them: a lining 2 or 7
  squeezed into an old-style box is a different figure. Big Caslon takes the
  fourth roman slot because it is old-style by default.
  - Charter would add little. Its 7 (bar 0.91, leg 0.76 even, 27 degrees) sits
    within 0.1 n of today's Albo on every axis but the beak.
- **There are no scan crops of figures.** The `aldine_autofit.SOURCES` crops
  are all letters. Poetica is the italic shape fallback, as the owner ruled on
  2026-09-16.
- Georgia and Hoefler Text are the fit audit's figure panel (its only two
  old-style faces), so the roman `o` and `q` arms are traced from the same
  faces the audit compares against.

### 1a. The 2, measured (units at xh 429; strokes / n stem)

`arc` is the arc's horizontal thickness at its widest point. `crown` is the
vertical thickness at the top. `slash` is the perpendicular thickness at its
angle from horizontal. `over` is how far the base runs past the arc's right
edge. `hang` is how far down the left terminal reaches, as a fraction of the
height.

| face | w | top | arc | crown | slash | angle | base | over | hang |
|---|---|---|---|---|---|---|---|---|---|
| Georgia | 408 | 481 | 1.20 | 0.45 | 0.51 | 28 | 0.95 | 22 | 0.40 |
| Hoefler Text | 401 | 461 | 1.04 | 0.90 | 0.42 | 44 | 0.84 | 38 | 0.31 |
| Palatino | 406 | 431 | 1.07 | 0.90 | 0.51 | 36 | 0.94 | 46 | 0.27 |
| Big Caslon | 375 | 438 | 1.03 | 1.13 | 0.29 | 49 | 1.01 | 62 | 0.34 |
| Charter (lining) | 413 | 610 | 1.16 | 0.65 | 0.67 | 42 | 0.95 | 20 | 0.29 |
| Baskerville (lining) | 410 | 704 | 1.17 | 0.42 | 0.46 | 47 | 0.85 | -8 | 0.38 |
| **Albo today** | 362 | 442 | 1.07 | 0.62 | **0.61** | 41 | 0.87 | 26 | **0.41** |
| **o** (Georgia) | 362 | 438 | 1.20 | 0.48 | 0.49 | 42 | 0.95 | 21 | 0.40 |
| **p** (Palatino) | 363 | 447 | 1.03 | 0.85 | 0.55 | 43 | 0.93 | 44 | 0.30 |
| **q** (Hoefler) | 362 | 447 | 1.04 | 0.80 | 0.48 | 42 | 0.84 | 37 | 0.32 |
| **r** (Big Caslon) | 366 | 450 | 0.92 | 0.89 | 0.40 | 46 | 1.01 | 61 | 0.35 |

| face | w | top | arc | crown | slash | angle | base | over | hang |
|---|---|---|---|---|---|---|---|---|---|
| Georgia Italic | 402 | 474 | 1.19 | 0.43 | 0.55 | 24 | 0.94 | 14 | 0.39 |
| Hoefler Italic (suspect) | 361 | 444 | 0.84 | 0.69 | 0.35 | 45 | 0.67 | 30 | 0.29 |
| Palatino Italic | 345 | 430 | 0.94 | 0.79 | 0.47 | 42 | 0.73 | 62 | 0.23 |
| Flanker Griffo | 378 | 436 | 0.89 | 0.87 | 0.37 | 37 | 0.85 | 24 | 0.25 |
| Poetica | 338 | 441 | 1.00 | 1.02 | 0.40 | 52 | 0.78 | 82 | 0.29 |
| Pagella Italic | 370 | 424 | 1.03 | 0.83 | 0.50 | 39 | 0.80 | 70 | 0.28 |
| **Albo today** | 326 | 442 | 1.09 | 0.74 | 0.49 | 48 | **0.71** | **10** | **0.42** |
| **o** (Flanker) | 329 | 449 | 0.84 | 0.81 | 0.52 | 48 | 0.84 | 24 | 0.38 |
| **p** (Palatino It) | 333 | 444 | 0.89 | 0.78 | 0.54 | 52 | 0.72 | 60 | 0.26 |
| **q** (Georgia It) | 325 | 440 | 1.18 | 0.53 | 0.56 | 52 | 0.93 | 13 | 0.40 |
| **r** (Poetica) | 354 | 449 | 0.93 | 0.91 | 0.42 | 56 | 0.78 | 79 | 0.35 |

What the references agree on and Albo does not:

- The roman slash is heavy: 0.61 of the n against 0.29–0.51.
- The italic base is the lightest and shortest in the set: 0.71 and 10 units,
  against 0.73–0.94 and 14–82.
- Both terminals hang lowest of all (0.41 and 0.42 against 0.23–0.40).

### 1b. The 7, measured

`bar` is the bar's thickness at 35% of the width. `beak` is how far ink hangs
under the bar's left end. `leg top` and `leg low` are the leg's perpendicular
thickness in its upper and lower quarters. `angle` is measured from vertical.
`bow` is the sagitta over length. `foot` is the leg's center at its lowest row,
as a fraction of the width.

| face | w | top | bottom | bar | beak | leg top | leg low | angle | bow | foot | flare |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Georgia | 409 | 467 | -159 | 0.91 | 97 | 0.56 | 0.59 | 27.6 | 0.000 | 0.21 | 0.91 |
| Hoefler Text | 388 | 445 | -235 | 0.99 | 65 | 0.40 | 0.49 | 22.5 | 0.000 | 0.27 | 1.06 |
| Palatino | 414 | 428 | -218 | 1.02 | 106 | 0.52 | 0.85 | 29.0 | -0.002 | 0.16 | 1.32 |
| Big Caslon | 412 | 429 | -225 | 1.02 | 79 | 0.25 | 0.56 | 23.9 | 0.000 | 0.32 | 1.27 |
| Charter (lining) | 410 | 598 | -33 | 0.91 | 82 | 0.76 | 0.77 | 27.2 | 0.000 | 0.21 | 1.01 |
| Baskerville (lining) | 383 | 704 | -18 | 0.93 | 58 | 0.46 | 0.89 | 20.8 | 0.000 | 0.31 | 1.06 |
| **Albo today** | 402 | 425 | -208 | 1.02 | **43** | 0.67 | 0.68 | 23.0 | 0.000 | 0.30 | 0.99 |
| **o** (Georgia) | 401 | 425 | -208 | 0.90 | 99 | 0.58 | 0.60 | 25.8 | 0.000 | 0.22 | 1.01 |
| **p** (Palatino) | 400 | 425 | -212 | 0.95 | 114 | 0.54 | 0.84 | 27.8 | 0.000 | 0.16 | 1.07 |
| **q** (Hoefler) | 401 | 425 | -206 | 1.03 | 64 | 0.39 | 0.45 | 24.8 | 0.000 | 0.28 | 1.00 |
| **r** (Big Caslon) | 400 | 425 | -206 | 1.01 | 80 | 0.30 | 0.50 | 23.5 | 0.000 | 0.33 | 1.06 |

| face | w | top | bottom | bar | beak | leg top | leg low | angle | bow | foot | flare |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Georgia Italic | 403 | 460 | -156 | 0.88 | 98 | 0.57 | 0.61 | 27.3 | 0.000 | 0.22 | 1.03 |
| Hoefler Italic (suspect) | 352 | 436 | -220 | 0.74 | 60 | 0.33 | 0.39 | 21.9 | 0.000 | 0.24 | 1.04 |
| Palatino Italic | 356 | 430 | -206 | 0.88 | 90 | 0.54 | 0.80 | 20.3 | -0.003 | 0.31 | 1.23 |
| Flanker Griffo | 405 | 423 | -310 | 0.84 | 102 | 0.73 | 0.74 | 24.2 | 0.000 | 0.18 | 1.12 |
| Poetica | 294 | 442 | -136 | 1.00 | 63 | 0.38 | 0.76 | 19.8 | -0.007 | 0.30 | 1.52 |
| Pagella Italic | 364 | 428 | -188 | 0.94 | 4 | 0.50 | 0.77 | 20.4 | -0.004 | 0.36 | 1.25 |
| **Albo today** | 363 | 412 | -200 | 0.84 | **30** | **0.80** | **0.62** | 23.5 | **-0.033** | 0.28 | 0.97 |
| **o** (Flanker) | 364 | 412 | -210 | 0.96 | 79 | 0.73 | 0.74 | 24.7 | 0.000 | 0.18 | 0.99 |
| **p** (Palatino It) | 364 | 412 | -200 | 0.97 | 58 | 0.55 | 0.79 | 23.6 | -0.034 | 0.30 | 1.15 |
| **q** (Georgia It) | 363 | 412 | -208 | 1.00 | 52 | 0.57 | 0.60 | 23.9 | 0.000 | 0.22 | 1.02 |
| **r** (Poetica) | 364 | 412 | -212 | 1.02 | 55 | 0.42 | 0.73 | 22.0 | 0.000 | 0.30 | 1.32 |

What the references agree on and Albo does not:

- **The beak.** Every reference but Pagella hangs 58–106 units of ink under the
  bar's left end. Albo hangs 43 (roman) and 30 (italic).
- **The leg.**
  - The roman references' legs are light under the bar and swell or hold toward
    the foot. Albo's is even at 0.67, heavier at the top than every old-style
    reference.
  - The italic references' legs are **straight** (bow 0.000 to -0.007) and
    swell or hold. Albo's curves (-0.033) and **thins** (0.80 to 0.62). No
    reference italic 7 thins toward its foot.
- **The bar.** The italic references' bars are flat (0.95–1.00 of themselves
  across the span). Albo's tapers to 0.74 by round 219's ruling.

---

## 2. The levers added, and what each defaults to

All of them default to the constant they replace. The default build is
byte-identical (§0).

| lever | figure | what it moves | default |
|---|---|---|---|
| `rx_k` | 2 | the arc's half-width over the drawn width | 0.46 |
| `ry_k` | 2 | the arc's half-height over its half-width | 0.95 |
| `t_start` | 2 | the angle the arc starts at, in degrees (lower means the left terminal hangs less) | 190 |
| `foot_x` | 2 | where the slash lands on the base, × S | 0.5 |
| `con`, `stress` | 2 | the arc's cut and nib axis, via `PR.bowl_widths` | roman 1.0 / 0; italic FIG_CON / FIG_STRESS |
| `beak` | 7 | the bar's hanging wedge, its hang × this. It replaces the bar's own wedge | off |
| `sink` | 7 | the descender's depth: the foot rises, the top holds | 0. **No arm uses it** (§5) |

---

## 3. Gates, every arm, all four cuts

Tools: `cmp_contour_hairs` (letters and full sweep), `cmp_touch` (5,000+ pairs,
figures included), `cmp_counter_dents` (Bold and BoldItalic against the
control), `cmp_aldine_glitch --ttf` (Italic), `approved.py --check`, and
`cmp_contours --check`.

| arm | hairs (4 cuts) | touching | under 0.012 em | dents 700 | glitch | approved | contours |
|---|---|---|---|---|---|---|---|
| control | 0 | 0 | 0 | 0 | 2 (Y, ﬆ; pre-existing) | ok | unchanged |
| o | 0 | 0 | 0 | 0 | same 2, byte-identical report | ok | unchanged |
| p | 0 | 0 | **1: BoldItalic `q2` 0.0111** | 0 | same 2 | ok | unchanged |
| q | 0 | 0 | 0 | 0 | same 2 | ok | unchanged |
| r | 0 | 0 | 0 | 0 | same 2 | ok | unchanged |
| **recommended set** | 0 | 0 | 0 | 0 | same 2 | ok | unchanged |

The tightest pair containing a 2 or a 7 (em), per cut, as Regular / Italic /
Bold / BoldItalic:

- control: `24` .042, `42` .079, `24` .041, `72` .067
- o: `24` .046, `42` .072, `24` .045, `72` .047
- p: `24` .035, `42` .042, `24` .033, `72` .026
- q: `24` .038, `42` .081, `24` .035, `72` .059
- r: `24` .026, `24` .039, `24` .025, `24` .050
- recommended: `24` .038, `42` .072, `24` .035, `72` .047

The pattern: a longer base overhang (`p`, `r`) brings the `24` and `72` pairs
closest.

---

## 4. Weight and color (`cmp_weight_survey`), against the other eight figures

`off` is the figure's value over the median of 0 1 3 4 5 6 8 9 in the same cut.
Stroke is the ridge median. Color is ink per advance.

| cut | arm | 2 stroke | 2 color | 7 stroke | 7 color | 7 cut |
|---|---|---|---|---|---|---|
| Regular | today | -3% | -14% | -14% | -5% | 1.53 |
| | o | -4% | -15% | +11% | -16% | 1.56 |
| | p | +11% | -17% | +16% | -15% | 1.88 |
| | q | -10% | -24% | +16% | -19% | 2.65 |
| | r | +7% | -17% | +24% | -21% | 3.35 |
| Italic | today | **-25%** | **-25%** | -7% | -16% | 1.75 |
| | **o** | **-3%** | -16% | +17% | -15% | 1.32 |
| | p | -15% | -25% | -1% | -19% | 1.81 |
| | q | +5% | -12% | -1% | -21% | 1.73 |
| | r | -3% | -21% | +17% | -25% | 2.66 |
| Bold | today | -4% | 0% | -14% | +1% | 2.57 |
| | q | -1% | -6% | -45% | -14% | 2.74 |
| | p | +4% | 0% | -7% | -9% | 3.00 |
| BoldItalic | today | **-37%** | -13% | -10% | -12% | 2.14 |
| | **o** | **-1%** | +2% | -7% | -10% | 2.36 |

Reading it:

- **The italic 2 is today's lightest figure by stroke** (-25% in the 400, -37%
  in the 700). Flanker's 2 (`o`) puts it on the family, at -3% and -1%.
- **Every roman 7 arm reads lighter by color than today's** (-15% to -21%
  against -5%). The stroke median rises at the same time.
  - The references' legs are lighter under the bar than Albo's. The beak adds
    little ink for its length. [inf] The stroke median rises because the bar
    and beak now dominate the ridge sample.
  - The fit audit's own finding from 2026-09-21 stands: *a 7 is light in every
    face*. The audit, which measures against the references, prefers `p`
    (§5). Take `p`'s -15% as the reference behavior, not as a defect. The
    owner's eye rules.
- The stroke medians of the 7 flip between the bar and the leg, as round 229
  recorded for the 4, so color is the measure to judge them by.

---

## 5. The fit audit per arm (`fit_audit/`, F >= 2.0 is a flag)

Axes a–f and h were measured on each build (`run_geom.py`, then
`score.py --tag`).

**The legibility axis (g) is round 402's, not re-measured.** OCR needs the
`kept-legibility-index` checkout, which is not on this machine. A change to
legibility is therefore invisible here.

| cut | control 2 / 7 | o | p | q | r |
|---|---|---|---|---|---|
| Regular | 0.00 / 0.69 | 0.01 / 1.28 | 0.00 / **0.32** | 0.06 / 1.66 | 0.61 / **2.94** (cut +3.9) |
| Italic | **1.61** / **2.00** | **0.00 / 0.76** | 0.56 / **2.19** (thin) | 0.55 / 1.82 | 0.08 / **2.99** (thin) |
| Bold | **2.99** / 1.46 | 1.95 / **2.13** | **3.13** / 1.02 | **0.31** / 1.27 | **2.45** / **3.92** |
| BoldItalic | 0.17 / 1.48 | 0.09 / **0.50** | 0.85 / 0.85 | 0.11 / **2.09** | 0.24 / 0.70 |

Recommended set: Regular 0.06 / 0.32, Italic 0.00 / 0.76, Bold 0.70 / 1.02,
BoldItalic 0.09 / 0.50.

The arms that fail it fail on the reference's own trait:

- **Big Caslon's contrast (`r`) is past Albo's family.** Its leg at 0.25 of the
  n under the bar gives the 7 a cut of 3.35, where Albo's figures run
  1.5–2.6.
- **Palatino Italic's and Poetica's thin leg tops read thin against the
  family** (b thin -3.1, -3.8). Today's italic 7 is already flagged thin
  (-2.9).

---

## 6. Negative results, each measured

- **Taking a reference's descender depth breaks the family, so no arm does.**
  - The first build set `sink` to each reference's depth: Georgia -159,
    Flanker -310, Poetica -136.
  - The fit audit then flagged every such 7 on its vertical axis, z -5.5 to
    +6.4 and F up to 4.94 (Italic `r`).
  - The 3 4 5 9 keep Albo's depth, and one figure cannot leave the line alone.
    Depth is a family-wide question, and the lever is left in place for that.
- **The beak has two ceilings.**
  - **Ceiling 1: thin.** Past about 3.5× in the italic, the wedge's long thin
    bracket drags the 7's p10 ridge down. Flanker's own 102 units (4.5×)
    scored F 2.02 (thin -2.9), where 3.5× scores 0.78.
    - Italic `o`, laddered: 2.0, 0.92; 2.5, 0.86; 3.5, 0.78; 4.0, 1.66.
    - Italic `p`: 2.0, 2.16; 2.5, 2.14; 3.5, 2.83; 4.0, 3.13.
    - Italic `q`: 2.0, 1.78; 2.5, 1.73; 3.5, 2.03; 4.0, 2.68.
  - **Ceiling 2: hairs.** At particular lengths the wedge's apex turns past the
    hairs gate's 165 degrees: 3.0× in the italic (166.2 degrees in `seven` and
    its inferior), 2.7× on Poetica's bar (in `uni2077`). The shipped values
    (italic 3.5 / 2.5 / 2.5 / 2.3) were laddered clear of both.
- **Georgia's 2 slash angle cannot be traced on this skeleton.** Georgia's
  slash runs at 28 degrees and Albo's at 42. Georgia's neck is a long curve,
  and this 2's slash is solved on the arc's tangent.
  - Tried: `ry_k` 0.80, 1.10, 1.20; `rx_k` 0.40; `foot_x` -0.8; `con` 0.0 to
    1.6; `stress` -25.
  - The angle moved only between 38 and 42 degrees.
- **The 2's width is not the arm's to set.** `build.solve_widths` aims the 2's
  ink at `round20.REF`, so a width drawn in `figures.py` is undone. A longer
  overhang (`over`) therefore narrows the body.
  - The references' 2s are 375–408 wide in the roman against Albo's 362.
  - Moving that needs `build.py`, which is outside this round's partition.
- **Lifting the italic 2's terminal costs bearing in the BoldItalic.**
  - `t_start` 160 moves the italic 2's left edge, and the fitter's percentile
    edge moves with it. The 2's lsb fell by about 30 units (to -12 through -21).
  - `q2` touched in the BoldItalic (-0.0061 em on `o`, -0.0132 on `r`).
  - Laddered on `p`: `t_start` 150, 160, 170, 180, 165 read `q2` at 0.0064 (R2),
    0.0111, -0.0003, -0.0046, 0.0054.
  - `o` and `r` were moved to 184 and 186 (touching gone). `p` stays at 160 and
    carries the one under-floor pair in §3.
  - The fix for that pair is a `q2` kern or a bearing, both outside
    `figures.py`.
- **`con` below 1 on the roman arc does not thicken the crown enough.** At 0.3
  the crown reached 0.86 and at 0.0 it reached 0.97, but the arc fell with it
  (monoline). Palatino's and Hoefler's heavy crown under a full arc is an
  **oblique axis**: `stress` -30 gives crown 0.85 with arc 1.03. That is what
  `p` and `q` use.

## 7. Checked and found CLEAN

- The default build: IDENTICAL in all four cuts, outlines and advances.
- Contour census unchanged for every arm, so no phase shifts in later glyphs.
- `approved.py`: both approved `g`s unchanged under every arm.
- Counter dents at 700: 0 under every arm.
- The glitch sweep: byte-identical report to the control under every arm.
- The hairs gate (full sweep, superiors and inferiors included): 0 under every
  final arm.
- `cmp_touch`: 0 touching under every final arm and the recommended set.

## 8. Not done

- **`docs/albo-STATE.md` was not regenerated.** It cites `figures.py` line
  numbers, which this change moves. It was already out of date at `52ef9f8`,
  and the round-403 agent has `marks.py` open. Regenerate it once both land.
- `cmp_seven_legibility.py` was not run.
- The legibility axis was not re-measured (§5).
- No kerns or bearings were changed; see §6 for the one pair they would fix.
- Italic `FIG_HAND` presses (`aldine.py`) apply to these arms as to any
  figure. Nothing went wrong in the glitch sweep, but a winner wants its press
  checked by eye (the round-229 caveat).

## 9. Re-running it

```bash
cd tools/wedge_serif
PYTHON_GIL=0 python3 instruments/fig27_trace.py --refs              # the references
source build_env.sh
env "${ALBO_ROM_ENV[@]}" ALBO_FIG_2=q ALBO_FIG_7=p PYTHON_GIL=0 python3 -m outlines.build OUT --style Regular
env "${ALBO_ITA_ENV[@]}" ALBO_FIG_2=o ALBO_FIG_7=o PYTHON_GIL=0 python3 -m outlines.build OUT --style Italic
PYTHON_GIL=0 python3 instruments/fig27_trace.py --albo OUT            # the same measure on the build
uv run --no-project --with uharfbuzz --with freetype-py --with numpy --with pillow --with fonttools \
  python instruments/fig27_sheet.py --today CONTROL --arm o=DIR ... --out sheet.png
```

---

# Round 408: six variations on the italic `p` (Palatino Italic)

Owner, 2026-09-26, on round 406's sheet: *"need variations on p"*. This round
is **italic only and nothing ships**. `FIG_SHIP_IT` is unchanged.

**The letters.** `s t u w x y` are added to `TWO_OPT_IT` / `SEVEN_OPT_IT`, and
each changes **one thing** against `p`:

- `s t u` change the 7 and draw `p`'s 2.
- `w x y` change the 2 and draw `p`'s 7.

So `ALBO_FIG_2=X ALBO_FIG_7=X` on an italic build gives the variation whole. On
a roman build these letters draw option `a`, not the shipped figure, so use them
on italic builds only.

**Proof the default is untouched.** The default build of all four cuts is
IDENTICAL to round 407's, outlines and advances. Every row is written as
`dict(<p's row>, change)` and was proved outline-identical to its flat-dict
first build.

## The italic 7 rulings, per arm

| arm | round 212: curve to an upright foot | round 215: pressed foot | round 219: tapering bar, thinning leg |
|---|---|---|---|
| today | keeps | keeps | keeps |
| p | keeps | keeps | **sets aside**: bar near flat (0.92 against 0.55); leg swells, where 219's thins |
| s: beak shallow | keeps | keeps | sets aside, as p |
| t: leg straight | **sets aside** | keeps | sets aside, as p |
| u: leg even | keeps | keeps | sets aside the bar; the leg neither thins nor swells |
| w x y (2 only) | as p | as p | as p |

## What each one measures

Measured with `fig27_trace.py`, in units at x-height 429, with strokes over the
n stem.

| arm | the one change | 2: arc / crown / slash / base / hang | 7: beak / leg top → low / bow |
|---|---|---|---|
| today | — | 1.09 / 0.74 / 0.49 / 0.71 / 0.42 | 30 / 0.80 → 0.62 / −0.033 |
| p | — | 0.89 / 0.78 / 0.54 / 0.72 / 0.26 | 58 / 0.55 → 0.79 / −0.034 |
| s | 7: beak shallow (`beak` 2.5 → 1.6) | as p | **38** / 0.56 → 0.80 / −0.035 |
| t | 7: leg straight (`curve` 0) | as p | 58 / 0.55 → 0.78 / **0.000** |
| u | 7: leg even (`diag_w` 0.80, `leg_taper` 1.0) | as p | 58 / **0.63 → 0.63** / −0.034 |
| w | 2: terminal hangs as today (`t_start` 190) | 1.02 / 0.67 / 0.55 / 0.73 / **0.37** | as p |
| x | 2: base heavier (`base_w` 1.25 → 1.40) | 1.00 / 0.71 / 0.53 / **0.81** / 0.26 | as p |
| y | 2: arc and slash heavier (`top_w` 1.15, `slash_k` 0.84) | **1.10 / 0.90 / 0.62** / 0.72 / 0.27 | as p |

## Weight against the other eight italic figures

From `cmp_weight_survey`: stroke / color, each relative to the median of the
other eight italic figures.

| arm | Italic 2 | Italic 7 | BoldItalic 2 | BoldItalic 7 |
|---|---|---|---|---|
| today | −25% / −25% | −7% / −16% | −37% / −13% | −10% / −12% |
| p | −15% / −25% | −1% / −19% | −21% / −7% | −4% / −15% |
| s | as p | +1% / −20% | as p | −4% / −15% |
| t | as p | +13% / −20% | as p | −1% / −15% |
| u | as p | −22% / −17% | as p | −25% / −12% |
| w | −15% / −22% | as p | −22% / −5% | as p |
| x | −11% / −24% | as p | −20% / −3% | as p |
| y | **−11% / −17%** | as p | −14% / **+2%** | as p |

`y` is the variation that brings the italic 2 toward its family, at −17%
against today's −25%. `u`'s stroke median of −22% reads the even, thinner leg
as the 7's typical stroke. Judge the 7 by color, which moves only 2 points.

## Gates, every variation and `p`, all four cuts

- **Hairs** (letters and full sweep): 0.
- **cmp_touch**: 0 touching and 0 under the floor, in all four cuts, for `p`,
  `s`, `t`, `u`, `w`, `x`, `y` and the default.
- **Counter dents** at 700: 0.
- **Glitch sweep**: the 2 pre-existing findings only.
- **approved.py**: 2 of 2 unchanged.
- **Contour census**: unchanged.
- **gates.sh**: UNCHANGED.

## `p`'s BoldItalic `q2` floor: fixed with a clearance kern

- **Fix.** `local_ai/clearance.py` was run on a build with the italic cuts at
  `p`. It took `q two` in the BoldItalic clearance block of
  `outlines/spacing_b2.json` from **+4 to +8**. `p`'s `q2` then reads above the
  floor, and so do `s`, `t`, `u` and `y`, which share `p`'s 2.
- **Effect on the shipped font.** This kern is in the SHIPPED BoldItalic too.
  Today's italic 2 already cleared `q2` at 0.0154 em with the +4, so the pair
  loosens by 4 units. That is the whole effect on the shipped font: outlines
  and advances are IDENTICAL in all four cuts. If `p` is not picked, the +4 can
  come back out.
- **Why no geometric fix.**
  - The closest approach is the 2's arc top-left against the q's shoulder, near
    the top of the 2. It is not at the base.
  - Trimming the base's left end (`base_x0` 0.15/0.30/0.45 S) made it worse:
    0.0068 and 0.0097 em.
  - Narrowing the arc (`rx_k` 0.44/0.42) gave 0.0082 and 0.0111.
  - Moving the terminal (`t_start` 155/158/162) gave 0.0111 or traded it for
    `R2` at 0.0078.
  - Every one moved the fitter's bearing along with the ink. The `base_x0` lever
    was removed rather than left dead.
- **The italic 2's BoldItalic bearing is fragile under almost any change.** A
  shorter base (`over` 30/36/44 against 62) dropped `q2` to 0.0011 or touching
  and put `R2` at 0.0064, which is why `x` changes the base's weight and not
  its length. `base_w` 1.45 and 1.60 dropped `q2` to 0.0025 and `R2` to
  0.0092; 1.30, 1.35 and 1.40 are clean. Whichever italic 2 is picked, run
  `clearance.py` on its build once more before shipping.

Sheet: `fig27-italic-p.png`, in the session scratchpad `fig27/`.


## Round 410 (draft) — the italic 2 and 7 in the italic's own pen, drawn by the main session

Owner 2026-09-26 on the round-408 variations: *"those are crappy variations. do better with more 7 leg tweaks and 2 that joins in a smoother way. i need albo style."* Then, on reflection, the standing rule of 2026-09-13 was restored: glyph drawing is not delegated. These arms are drawn in `outlines/glyphs/aldine.py` (`_fig7_pen`, `_fig2_pen`, after the figure registration loop), selected by `ALBO_IT_FIG7_PEN=a..f` / `ALBO_IT_FIG2_PEN=a|b|d|e`; unset = the shipped figures, byte-identical.

Why they are different in kind from rounds 406/408: the shipped italic figures are the ROMAN construction (`figures.py`, stroke/bar/diagonal on S) sheared; every italic lowercase is `d_pen` -- one catmull movement with a width table and the family finial. So the 7 IS the italic z's top ribbon (entry hook, crest, ease) with a z-like diagonal overlapping its end, the leg weighted like the z's diagonal (set width `FIGPEN_LEG` 46, heavier ends) because a down-left stroke on the 50-degree nib is nearly its thin edge; the 2 is a c-finial arc flowing over the shoulder into its neck as ONE movement, landing in a z-like bottom ribbon.

Arms: 7a straight leg, finial foot · 7b curve to an upright pressed foot (round 212/215 intent) · 7c swell mid-stroke, cut foot · 7d quill turn leaving the bar · 7e more upright · 7f long y-descender curve · 2a neck straight into a ribbon base · 2b one cursive stroke through the base · 2d base swells out of the neck · 2e rounder neck. (2c, a looped join, drew as a hairline knot at 54 px and was cut.)

Gates (fig_it_arms.py): every 2 arm clean in Italic and Bold Italic. Every 7 arm leaves `q7` under the floor in Bold Italic (0.006 em for 7a) -- the leg's foot sits further right than today's; 7c/7d/7f also touch one pair there, and 7e touches g7 q7 O7 in both italics. All are letter+7 descender pairs, fixable by `local_ai/clearance.py` kerns once an arm is picked. Hairs, dents, glitch and approved unchanged on every arm.
