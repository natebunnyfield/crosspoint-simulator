# Which Albo letters are optical outliers, and a metric for "well fitted" (2026-09-26)

Owner, 2026-09-26: *"give me the likely letters that would benefit from being
redone because optically they are outliers (likely k x s y and many others)
determine a metric for what is well fitted"*.

- **Audited build:** round 402 (`bdfd477`). Regular and Italic are the shipped
  `bench/fonts-2026-09-26-r402/` files. Bold and BoldItalic were rebuilt from a
  `git archive HEAD` snapshot. A snapshot rebuild of Regular and Italic is
  outline- and advance-IDENTICAL to the shipped pair (`cmp_outlines.py
  --advances`), so the snapshot builder is trusted for the validation builds.
- **Rendering:** as the reader renders since round 401. FreeType with
  NO HINTING. For colour and legibility, the converter's 2-bit levels (the top
  nibble, cut at >=12/8/4). For geometry, an exact unhinted raster at 1200 ppem.
- **Read-only** on `outlines/`. Nothing in the font changed.
- **Code:** `tools/wedge_serif/fit_audit/`. **Numbers:** `fit_audit/results/`.
- **Confidence:** every number below is measured unless it is marked [inf].

---

## 0. The answer

- **The metric** (section 1). A glyph fits when it deviates from its
  CONSTRUCTION FAMILY no more than the same letter deviates from its family in
  six reference serifs. That is checked on eight axes: colour, stroke,
  proportion, vertical, sidebearings, spacing fight, legibility and cross-cut
  consistency. The axes combine into one score, F. **F >= 2.0 is a flag.**
  One axis at 3 sigma reaches the flag on its own.
- **Validation** (section 2). The pre-fix builds of 37 letters he later fixed
  were rebuilt from git. The metric flagged **10 of the 37**; chance, at the
  same flag rate, would flag about 4.2. **12 of the 37** were in their cut's
  top 10; chance would give about 6. After the fix, the score fell in 28 of 37.
  - **The misses are informative.** Ten of them are two family-wide passes:
    the italic bowls b d p q a, and the italic arches h m n r u. A metric that
    compares a letter with its own family cannot see a change made to the
    whole family. The pre-fix bowls were also not thin against the references:
    his picks moved them past the references, toward less contrast.
  - **False alarms.** 3 of 4 negative controls flag. These are the roman Q
    tail and S that he reverted in round 225, and the approved italic g. Each
    one is a deliberate choice that the metric reads as a deviation.
- **k x s y** (section 4):
  - **y: confirmed** in all four cuts (rank 6, 7, 2 and 4).
  - **k: confirmed** in Regular (rank 12) and Bold (rank 7), borderline in
    Italic (rank 17). Much of the k's score is its leg kicking 22 to 35 units
    below the baseline, which is the ruled R/K/k kick.
  - **s: confirmed in Regular only** (rank 9, from contrast). It is clean in
    Italic and Bold.
  - **x: refuted.** It is not flagged in any cut: rank 25, 29, 16 and 44.
    Bold x comes closest, at F 1.90.
- **Top outliers per cut** (section 3), with their leading axis:

| cut | flagged | worst, in order (leading axis) |
|---|---|---|
| Regular | 14 of 62 | **e** (contrast), **t** (spacing), **j** (spacing), Q (width, ruled), I (thin, wedge serif), **y** (contrast), **S** (spacing, stroke), J (thin), **s** (contrast), 6 (figure height), l (thin), **k** (kick, contrast), **a** (spacing), 8 (figure height) |
| Italic | 9 of 62 | **F** (spacing, stroke), g (descender, approved), **j** (spacing), **O** (spacing), **W** (stroke), J (thin), **y** (descender, stroke), **N** (stroke), **7** (thin) |
| Bold | 15 of 62 | **e** (contrast), **y** (contrast), I (thin), Q (width), **T** (light stem), **t** (contrast), k (kick), **2** (contrast), 8, 6 (figure height), **N**, K (kick), **z** (thin), **r**, **P** |
| BoldItalic | 6 of 62 | g (descender), **1** (contrast), **q** (sidebearing balance), **y** (light, deep), **W**, **V** (heavy) |

Letters in bold have no ruling behind their deviation that I could find.
Letters in plain type do have one; section 5 lists each ruling.

---

## 1. The metric

### 1a. Axes and sub-axes

Each axis has one or more measured sub-axes. The axis takes whichever of its
sub-axes deviates most, and the table in section 3 names that sub-axis, so the
reason for a flag is visible.

| axis | sub-axes | how it is measured | weight |
|---|---|---|---|
| **a colour** | `col1x`, `col2x` | 2-bit rendered ink in the reading band (baseline to x-height, or to cap height for a capital), over linear advance × band height. Averaged over the reader's sizes: 8–18 pt at 150 dpi, so 16.7–37.5 ppem, plus the phone's 2x tier. | 1.0 |
| **b stroke** | `stroke`, `thin`, `cut` | Chamfer-ridge thickness, the method of `cmp_weight_survey.py`, on an exact Euclidean distance transform. Italics are unsheared first (checked: the italic l leans 12.99° before and 0.00° after). p50, p10, and p90/p10. | 1.0 |
| **c proportion** | `width`, `open` | Ink width over reference height (unsheared). `open` is 1 − ink / convex hull, which covers apertures and counters. | 0.75 |
| **d vertical** | `top`, `bot` | Ink top and bottom against the glyph's own line: x-height, ascender, cap height or the figure ascender, and the baseline or descender. The class is decided from the outline. | 0.5 |
| **e bearings** | `balance`, `loose` | White between the advance edges and the ink, row by row across the reading band, as set. Each row is clipped at 0.6 of the band. `balance` is (L − R)/(L + R) and `loose` is (L + R)/band. | 0.5 |
| **f spacing fight** | `b2_bearing`, `b2_kern`, `bench_push` | Taken from `spacing_b2.json` and his bench answers at HEAD (details below). | 0.75 |
| **g legibility** | `legib` | Apple Vision error rate per glyph on the reader's renders (details below), as relative log-odds. | 1.0 |
| **h cross-cut** | `xcut` | The part of the glyph's a–c misfit that its weight partner (Regular with Bold, Italic with BoldItalic) does not share. | 0.5 |

**Axis f: spacing fight.** Three sub-axes:

- `b2_bearing` is \|lsb\| + \|rsb\| of the glyph's B2 identity coefficients.
  It says how far the rule-built fitting was from what he wanted.
- `b2_kern` is the mean \|kern\| over the B2 kerns the glyph is in. It is the
  part that the bearings could not absorb.
- `bench_push` is a t-like consistency of his bench deltas on each side of the
  glyph: \|mean d\| · √n / (sd + 4), taking the larger side. A glyph he pushes
  the same way pair after pair has a wrong sidebearing, while noise cancels
  out.

**Axis g: legibility.** Apple Vision is the index's own `visionocr`, with
language correction off. The text is 1,078 seeded items (dictionary words and 90 digit groups), the same
for every face, so that every letter, capital and figure is covered. There are
four stresses:

- 16.7 ppem with a 1.1 px blur;
- 16.7 ppem with a 1.6 px blur;
- 11 ppem clean;
- 9 ppem clean.

At the reader's clean sizes every face reads close to 100%, so nothing would
separate the glyphs without the stresses.

### 1b. From measurements to a score

1. **Robust z within the family.** For every sub-axis and every face, the
   glyph gets a robust z against its construction family in that face. The
   families are the 2026-09-18 ledger's: round `acegos CGOQS`, diagonal
   `vwxyz AVWXYZ`, figure `0–9`, and stem for everything else. The centre is
   the median; the scale is 1.4826 × MAD, shrunk toward the pooled MAD because
   a family of five has a noisy MAD (`albo-method.md` §1f).
   - Each scale has a **floor**, and the floor was added after the first run
     failed. Every flat letter sits on the baseline at exactly 0, so the MAD is
     0, and the figures' bottoms read as **15 million sigma**. The floor is
     0.015 reference heights for vertical: 6 units, or 0.1 px at 16.7 ppem.
     It is 3–5% of the face's median for weights.
2. **Excess over the references.**
   `e = (z_Albo − median_r z_r) / sqrt(1 + s_r²)`. Here r ranges over Georgia,
   Charter, Times, Baskerville, Hoefler Text and Palatino in the matching cut,
   and s_r is their spread.
   - This is the misfit ledger's lesson built in. On 2026-09-21, two of that
     ledger's three headline findings dissolved once they were measured against
     a real face: a 7 is light in every face, and an 8 is dark in every face.
   - **Figures are compared only with Georgia and Hoefler**, whose default
     figures are old-style, as Albo's are. None of the six faces exposes an
     `onum` lookup to fontTools.
   - The **legibility** z also carries the glyph's own counting noise, as a
     binomial standard error in the denominator.
   - The **spacing** axis has no reference. It is a robust z within the case,
     and only extra fight counts.
3. **The score.** `F = sqrt( Σ_axes w · max(0, |e| − 1)² )`.
   - Inside 1 sigma is ordinary variation and costs nothing. Beyond it the cost
     grows as the square.
   - So one axis at 3 sigma gives F = 2.0 by itself, and a letter flagged for a
     single reason stays visible.
4. **The weights, and why.**
   - Colour, stroke and legibility get **1**. They are what a reader sees at
     reading size, and "legible" is in the brief.
   - Proportion gets **0.75**. It is visible, but the references disagree most
     here.
   - Spacing fight gets **0.75**. It is his own evidence, but spacing already
     corrects it.
   - Vertical gets **0.5**. At 16.7 ppem, 1 px is 60 units, so a few units of
     overshoot are sub-pixel at 1x.
   - Bearings get **0.5**. They overlap the spacing fight.
   - Cross-cut gets **0.5**. It is derived from a–c.
   - **The weights were set before validation and were not tuned on it.**

### 1c. Re-running it

```bash
tools/wedge_serif/fit_audit/run_all.sh WORKDIR KLI_DIR PY
```

- `PY` needs numpy, scipy, freetype-py, uharfbuzz, pillow and fontTools. The
  asdf 3.14t python has no scipy.
- `KLI_DIR` is a `kept-legibility-index` checkout, which supplies
  `ocr/visionocr`.
- The script rebuilds every snapshot from `git archive` into
  `WORKDIR/fonts/<tag>/` and measures 84 faces. That is 16 Albo builds, up to
  four cuts each, plus the 24 reference faces.
- Wall time was about 5 minutes on this Mac: 24 s to build, 73 s for geometry,
  159 s for OCR.
- The pieces:
  - `common.py`: families, the reference panel, the robust z;
  - `geom.py` and `run_geom.py`: axes a–e;
  - `legib.py`: axis g;
  - `spacing.py`: axis f, read from a git revision so a concurrent refit
    cannot move the ruler. This run read `3041fce`, whose spacing tables and
    answers are byte-identical to `bdfd477`'s;
  - `score.py`: the metric;
  - `validate.py`: section 2;
  - `report.py`: the section 3 tables;
  - `proof.py`: the proof page.

---

## 2. Validation: would it have found the letters he already fixed?

### 2a. Method

- For each ruled fix, the build before and the build after were rebuilt from
  their commits. `cmp_outlines` confirmed that each fix moved the letters
  named here; for example, 393→395 moved exactly `a b d p q s y 6` and their
  composites in the italic.
- The metric was then run on the **pre-fix** build **without axis f**. His
  spacing answers postdate most of these fixes, and using them would be
  hindsight.
- **CAUGHT** means F >= 2.0 in the letter's own cut.
- Numbers: `results/validation.json`.

### 2b. Every case

| fix | letter | pre-fix F, rank | leading axis | post-fix F |
|---|---|---|---|---|
| r395 thick/thin picks | Italic b d p q a s | 1.09 / 0.88 / 0.00 / 0.54 / 0.60 / 0.72; ranks 18–53 | stroke cut, low | fell on 5 of 6 |
| | **Italic y** | **2.06, #3** | vertical (the descender) | 1.84 |
| | Italic 6 | 1.92, #8 | stroke cut | 1.42 |
| | Regular x, Y, 3 | 1.08, 1.51, 0.63 | — | — |
| | **Regular e** | **5.97, #1** | stroke cut | 3.77 |
| | **Regular 8** | **2.68, #5** | vertical | 2.05 |
| r393 | Regular R, BoldItalic j | 0.34, 0.00 | — | — |
| r391 arch hairline | Italic h m n r u | 0.00–0.49 | — | — |
| r391 hairline floors | **Regular s, t, y** | **10.42 #1, 2.79 #6, 9.09 #2** | stroke cut | 2.47, 2.26, 3.15 |
| r398 | **BoldItalic g** | **5.65, #1** | vertical (descender) | 5.60 (the fix was weight, not depth) |
| r400 | **Regular e** | **4.20, #1** | stroke cut | 4.14 (the fix was a hinting window, 2 units) |
| r373 | Regular X | 1.69, #14 | stroke | 0.75 |
| | **Regular I** | **3.43, #5** | thin | 3.75 |
| | Italic f | 0.83 | — | 0.64 |
| r378 | Italic 4, BoldItalic 4; Bold 4 5 7 widths | 0.48–1.49 | — | — |
| r224 (kept) | **Regular X** | **3.11, #6** | legibility +3.3 | 1.37 |
| | Italic z, A, k | 0.10, 1.24, 1.82 (#6) | — | 0.10, 1.19, 0.69 |

### 2c. Summary

- **Caught 10 of 37 at F >= 2.0.** The median flag rate in those pre-fix cuts
  is 11%, so chance would catch about **4.2**.
- **12 of 37** were in their cut's top 10; chance gives about **6.0**.
- The median pre-fix rank percentile is **32%**, against 50% for chance.
- The score **fell after the fix in 28 of 37**.

### 2d. Sensitivity (`validate.py --variants`, `results/variants.json`)

| reference normalization | F >= 1.5 | F >= 2.0 | F >= 2.5 |
|---|---|---|---|
| **full (shipped)** | 14/37 (chance 7.8) | **10/37 (chance 4.2)** | 9/37 (chance 2.4) |
| difference only | 18/37 (13.1) | 13/37 (7.8) | 9/37 (4.8) |
| none (family z only) | 18/37 (13.7) | 14/37 (8.4) | 10/37 (6.0) |

- Dropping the references catches more letters, but it flags more of
  everything: the lift over chance falls from 2.4× to 1.7×.
- **The reference term is what makes the flag mean something.** The shipped
  choice is the one with the best lift. That was not tuned: it was the
  a-priori design.

### 2e. What the misses teach

- **Family-wide passes are invisible by construction**: 10 of the 27 misses.
  - Round 391 raised the hairline of all five italic arches (h m n r u), and
    round 395 raised the crowns of all four italic bowls plus the a.
  - A metric that compares a letter with its own family cannot see a change
    made to the whole family.
  - Measured against the references, the pre-fix bowls were **not** thin:

    | italic | thin / stem of b d p q a |
    |---|---|
    | **Albo r393** | 0.51 0.46 0.51 0.46 0.42 |
    | Albo r395 (his picks) | 0.63 0.64 0.61 0.63 0.64 |
    | Georgia | 0.41 0.38 0.36 0.36 0.38 |
    | Times | 0.35 0.34 0.30 0.28 0.32 |
    | Baskerville | 0.40 0.41 0.38 0.38 0.37 |
    | Palatino | 0.40 0.38 0.39 0.41 0.35 |
    | Charter | 0.58 0.51 0.49 0.51 0.51 |
    | Hoefler | 0.92 0.76 0.68 0.76 0.73 |

  - His picks moved the face past five of the six references, toward less
    contrast. **That is a style direction (the Albertus look), not a fit
    correction**, and no fit metric should be expected to propose it.
- **Width and figure-set fixes** (round 378's Bold figure widths). Those were
  set against Albo's own 400, not against the family, and the figure panel has
  only two old-style references (section 6).
- **Serif-scale fixes** (the R's balance, the BoldItalic j's crumpled head,
  the italic f) are local shape defects. They do not register as family-level
  weight, proportion or position.

### 2f. False alarms

| control | result |
|---|---|
| Roman Q and S at r223, fixed in round 224 and reverted in round 225 | Both flagged: F 4.19 (width) and F 4.52 (cut). The Q's tail is his ruling. |
| Italic g, approved (`approved.json`) | Flagged, **F 4.60**, from its descender. At −194 it is 88–125 units shallower than j, p, q and y. The 09-18 ledger found this and he approved the letter anyway. |
| Regular g, approved | Clean (F 1.19–1.50). |

**A flag is a place to look, not a verdict.** Section 5 lists which flags are
rulings.

---

## 3. The ranking, round 402

Every lowercase, capital and figure in all four cuts: 248 glyphs. The top 20
per cut are below. The full order is at the foot of each table, and every
number is in `results/fit-r402.json`.

Cells are the signed axis excess e. A positive value means more of the thing
than the letter should have: heavier, more contrasted, taller, wider, looser.
A negative value means less.

- **a** colour
- **b** stroke
- **c** proportion
- **d** vertical
- **e** bearings
- **f** spacing fight (only more counts; n/a for bolds and figures, which were
  never benched)
- **g** legibility
- **h** cross-cut

#### Regular: 14 of 62 flagged

| rank | glyph | F | a | b | c | d | e | f | g | h | why |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **e** | 4.31 | -0.5 | +5.3 | +0.5 | +0.8 | -0.2 | +1.5 | -0.9 | +0.2 | stroke +5.3 (cut) |
| 2 | **t** | 4.20 | -0.5 | +1.9 | -0.0 | +0.8 | +0.1 | +5.7 | +0.6 | +0.3 | spacing +5.7 (b2_bearing); stroke +1.9 (cut) |
| 3 | **j** | 4.18 | +0.8 | -0.5 | -0.7 | -1.3 | -3.1 | +5.5 | +0.3 | +0.5 | spacing +5.5 (b2_kern); bearings -3.1 (balance) |
| 4 | **Q** | 4.17 | -0.3 | -1.3 | +5.8 | +0.3 | -0.3 | +0.0 | -0.2 | +1.2 | proportion +5.8 (width) |
| 5 | **I** | 3.84 | +1.2 | +4.6 | -2.4 | +0.1 | -0.8 | +0.0 | +0.7 | +0.8 | stroke +4.6 (thin); proportion -2.4 (open) |
| 6 | **y** | 3.13 | +0.3 | +4.1 | -0.4 | -1.1 | -0.5 | +0.0 | +0.0 | +0.1 | stroke +4.1 (cut) |
| 7 | **S** | 2.81 | +0.0 | +2.8 | -0.2 | +0.6 | +0.7 | +3.5 | +0.5 | +0.5 | spacing +3.5 (b2_kern); stroke +2.8 (stroke) |
| 8 | **J** | 2.78 | -1.0 | +3.5 | -0.7 | +0.0 | +2.7 | +0.0 | +0.4 | +1.2 | stroke +3.5 (thin); bearings +2.7 (balance) |
| 9 | **s** | 2.68 | -0.6 | +3.3 | +0.2 | +1.3 | +1.2 | +0.0 | -0.2 | +3.0 | stroke +3.3 (cut); cross-cut +3.0 |
| 10 | **6** | 2.47 | -0.4 | -1.4 | +0.4 | +4.0 | +1.3 | n/a | +2.2 | +0.5 | vertical +4.0 (top); legibility +2.2 |
| 11 | **l** | 2.32 | +0.1 | +3.3 | -0.7 | -0.2 | -0.6 | +1.0 | -0.5 | +1.7 | stroke +3.3 (thin) |
| 12 | **k** | 2.27 | -0.7 | +2.5 | -0.2 | -3.3 | -0.4 | +0.0 | +0.7 | +2.0 | vertical -3.3 (bot); stroke +2.5 (cut) |
| 13 | **a** | 2.18 | -0.4 | +1.7 | -0.4 | -0.9 | -0.5 | +3.4 | +1.2 | +0.9 | spacing +3.4 (b2_bearing) |
| 14 | **8** | 2.05 | -0.3 | +0.8 | +0.2 | +3.9 | +0.8 | n/a | +0.1 | +0.5 | vertical +3.9 (top) |
| 15 | 4 | 1.67 | +0.5 | -2.2 | +0.7 | +2.6 | -0.2 | n/a | +0.0 | +1.1 | stroke -2.2; vertical +2.6 |
| 16 | F | 1.62 | -0.2 | +1.5 | -0.3 | +0.1 | -1.2 | +0.0 | +2.5 | +0.1 | legibility +2.5 |
| 17 | g | 1.50 | +0.0 | +2.1 | -0.2 | -1.2 | -2.4 | +0.0 | +0.7 | +0.6 | stroke +2.1; bearings -2.4 |
| 18 | E | 1.46 | +0.1 | -1.3 | +0.0 | +0.1 | -2.1 | +0.0 | +2.2 | +0.0 | legibility +2.2; bearings -2.1 |
| 19 | K | 1.36 | -0.5 | +0.9 | +0.2 | -2.6 | -0.8 | +1.9 | +0.0 | +0.4 | vertical -2.6 (bot) |
| 20 | n | 1.26 | -0.3 | +1.4 | +0.3 | +0.5 | +0.8 | +2.4 | -0.6 | +1.3 | spacing +2.4 |

Full order: e t j Q I y S J s 6 l k a 8 4 F g E K n m p o X x z i C 7 Y O D W 0 N f 9 3 M Z V R 1 v L G c u r A H 5 b d h q w B P T U 2

#### Italic: 9 of 62 flagged

| rank | glyph | F | a | b | c | d | e | f | g | h | why |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **F** | 5.19 | +0.2 | +4.1 | -0.6 | +0.5 | +0.8 | +5.3 | +0.8 | +3.5 | spacing +5.3 (b2_kern); stroke +4.1 (stroke) |
| 2 | **g** | 4.60 | +0.7 | -0.5 | -0.2 | +7.5 | -0.9 | +0.0 | +0.2 | +0.1 | vertical +7.5 (bot) |
| 3 | **j** | 3.09 | +0.9 | +1.1 | +0.8 | -0.3 | -0.7 | +4.6 | +0.0 | +0.9 | spacing +4.6 (b2_kern) |
| 4 | **O** | 2.54 | +0.0 | -1.0 | +0.8 | -0.2 | -0.7 | +3.9 | -0.2 | +0.5 | spacing +3.9 (b2_kern) |
| 5 | **W** | 2.37 | -0.6 | +3.1 | +1.1 | +0.5 | -1.1 | +2.1 | -0.4 | +0.9 | stroke +3.1; spacing +2.1 (bench_push) |
| 6 | **J** | 2.31 | +0.6 | +2.8 | -0.7 | +0.0 | -2.1 | +2.4 | -0.1 | +1.2 | stroke +2.8 (thin); spacing +2.4 |
| 7 | **y** | 2.01 | -0.0 | -2.4 | -0.2 | -3.1 | -0.9 | +1.0 | +0.5 | +0.0 | vertical -3.1 (bot); stroke -2.4 |
| 8 | **N** | 2.01 | +0.7 | +3.0 | -0.5 | +1.0 | +0.3 | +0.0 | -0.1 | +1.7 | stroke +3.0 |
| 9 | **7** | 2.00 | +1.5 | -2.9 | +0.7 | +0.7 | +1.5 | n/a | -1.3 | +0.6 | stroke -2.9 (thin) |
| 10 | P | 1.97 | +0.2 | -0.5 | -0.2 | +0.5 | +0.4 | +3.3 | -0.4 | +0.0 | spacing +3.3 (b2_kern) |
| 11 | M | 1.87 | -0.1 | +2.9 | -0.6 | +0.8 | +0.3 | +0.0 | -0.0 | +1.2 | stroke +2.9 |
| 12 | I | 1.74 | -0.9 | -2.1 | -2.5 | +0.5 | +1.0 | +0.3 | -0.4 | +0.9 | proportion -2.5; stroke -2.1 |
| 13 | Y | 1.62 | -0.2 | -2.6 | -1.0 | -1.4 | -1.1 | +0.0 | -0.2 | +0.8 | stroke -2.6 (cut) |
| 14 | 2 | 1.61 | -0.5 | -2.6 | +0.8 | +0.6 | -1.1 | n/a | -0.2 | +1.5 | stroke -2.6 |
| 15 | E | 1.52 | +0.2 | -0.4 | -0.5 | +0.5 | -3.1 | +0.3 | +0.3 | +0.0 | bearings -3.1 (balance) |
| 16 | v | 1.51 | +0.5 | +1.9 | -2.3 | +1.5 | +0.2 | +0.4 | -0.6 | +0.4 | proportion -2.3 |
| 17 | k | 1.47 | +0.2 | +0.7 | -0.9 | -0.5 | +1.0 | +2.7 | +0.4 | +0.6 | spacing +2.7 (b2_bearing) |
| 18 | 6 | 1.42 | -0.1 | -1.4 | -0.1 | +2.9 | +1.0 | n/a | +0.4 | +1.1 | vertical +2.9 |
| 19 | U | 1.35 | +0.8 | +1.4 | +0.3 | -0.2 | -2.4 | +2.0 | -0.8 | +0.3 | bearings -2.4 |
| 20 | V | 1.34 | -0.2 | +2.2 | +1.6 | +0.7 | -0.8 | +0.0 | -0.9 | +0.8 | stroke +2.2 |

Full order: F g j O W J y N 7 P M I Y 2 E v k 6 U V 1 f T 8 b o A L x R e 3 G D n S a w s 5 l r Q p H q 9 z d i Z m X 4 c h t u B C K 0

#### Bold: 15 of 62 flagged

| rank | glyph | F | a | b | c | d | e | f | g | h | why |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **e** | 5.93 | -0.5 | +6.9 | +0.6 | +0.7 | -0.2 | n/a | -0.5 | +1.6 | stroke +6.9 (cut) |
| 2 | **y** | 3.72 | +0.4 | +4.6 | -0.4 | -2.1 | -0.4 | n/a | -0.0 | +0.5 | stroke +4.6 (cut); vertical -2.1 |
| 3 | **I** | 3.71 | +1.1 | +4.6 | -1.8 | +0.1 | -1.1 | n/a | -0.1 | +2.1 | stroke +4.6 (thin) |
| 4 | **Q** | 3.16 | -0.5 | -1.1 | +4.6 | +0.2 | -0.6 | n/a | -0.1 | +0.4 | proportion +4.6 (width) |
| 5 | **T** | 3.13 | -0.5 | -3.8 | +0.3 | +0.1 | -0.4 | n/a | -1.1 | +2.9 | stroke -3.8 (stroke); cross-cut +2.9 |
| 6 | **t** | 3.08 | +0.2 | +3.9 | -1.0 | -2.0 | -0.4 | n/a | -0.3 | +2.0 | stroke +3.9 (cut) |
| 7 | **k** | 3.03 | -0.2 | -0.5 | -0.2 | -5.3 | +0.5 | n/a | +0.5 | +0.3 | vertical -5.3 (bot) |
| 8 | **2** | 2.99 | -0.4 | +3.5 | -0.1 | +0.5 | +0.7 | n/a | -0.2 | +3.3 | stroke +3.5 (cut); cross-cut +3.3 |
| 9 | **8** | 2.66 | -0.0 | -0.3 | -0.2 | +4.8 | +0.2 | n/a | -0.4 | +0.1 | vertical +4.8 (top) |
| 10 | **6** | 2.65 | -0.3 | -0.8 | -0.3 | +4.8 | +0.6 | n/a | +0.8 | +0.3 | vertical +4.8 (top) |
| 11 | **N** | 2.59 | +1.0 | +3.5 | -0.3 | +1.0 | -0.8 | n/a | +0.8 | +2.0 | stroke +3.5 (thin) |
| 12 | **K** | 2.55 | -0.1 | +1.6 | +0.2 | -4.5 | -0.6 | n/a | +0.5 | +0.7 | vertical -4.5 (bot) |
| 13 | **z** | 2.32 | -0.6 | -2.9 | +0.8 | -2.3 | +1.1 | n/a | +1.8 | +1.8 | stroke -2.9 (thin); vertical -2.3 |
| 14 | **r** | 2.03 | +0.1 | +2.8 | -0.4 | +0.2 | +2.1 | n/a | +0.7 | +1.9 | stroke +2.8 (thin); bearings +2.1 |
| 15 | **P** | 2.03 | +0.4 | +2.9 | -0.4 | +0.1 | +1.2 | n/a | -0.6 | +2.0 | stroke +2.9 |
| 16 | x | 1.90 | -0.4 | +2.0 | -0.6 | +2.5 | +2.4 | n/a | +1.7 | +1.2 | vertical +2.5 (top); stroke +2.0 |
| 17 | g | 1.89 | +0.0 | +1.9 | -0.4 | -2.8 | +2.5 | n/a | -0.8 | +0.2 | vertical -2.8; bearings +2.5 |
| 18 | L | 1.88 | -0.2 | +2.7 | -0.6 | +0.1 | +0.7 | n/a | -1.5 | +1.8 | stroke +2.7 (thin) |
| 19 | 3 | 1.81 | -0.7 | +2.8 | -0.8 | +0.8 | +0.4 | n/a | -0.0 | +1.4 | stroke +2.8 |
| 20 | j | 1.74 | +1.2 | -0.7 | -0.6 | -2.3 | -2.9 | n/a | +1.6 | +0.6 | bearings -2.9 |

Full order: e y I Q T t k 2 8 6 N K z r P x g L 3 j H J 7 a S 4 Z 5 R F M X w G C f l 0 s B E i h n Y V b c D m W o 9 O 1 A u d p q v U

#### BoldItalic: 6 of 62 flagged

| rank | glyph | F | a | b | c | d | e | f | g | h | why |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **g** | 5.60 | +0.9 | +0.5 | -0.1 | +8.9 | -0.8 | n/a | +0.2 | +0.4 | vertical +8.9 (bot) |
| 2 | **1** | 2.78 | +0.7 | +3.5 | -1.4 | +0.2 | +0.6 | n/a | +0.2 | +2.6 | stroke +3.5 (cut); cross-cut +2.6 |
| 3 | **q** | 2.50 | +1.7 | +0.4 | +0.8 | +2.3 | +4.2 | n/a | +0.3 | +1.1 | bearings +4.2 (balance) |
| 4 | **y** | 2.37 | -0.2 | -3.0 | -0.4 | -2.8 | -0.8 | n/a | +0.8 | +0.6 | stroke -3.0; vertical -2.8 |
| 5 | **W** | 2.29 | +0.0 | +3.3 | +0.2 | -0.7 | -1.0 | n/a | -0.6 | +0.2 | stroke +3.3 |
| 6 | **V** | 2.21 | -0.8 | +3.2 | +1.4 | -0.9 | -0.5 | n/a | -1.2 | +0.9 | stroke +3.2 |
| 7 | S | 1.89 | -0.6 | +1.2 | +1.0 | -3.6 | +1.0 | n/a | -1.4 | +0.7 | vertical -3.6 (bot) |
| 8 | o | 1.77 | -0.3 | +2.8 | +0.8 | -0.6 | -0.7 | n/a | -0.1 | +1.0 | stroke +2.8 (cut) |
| 9 | r | 1.75 | -0.1 | +2.6 | +0.5 | +1.7 | +1.0 | n/a | -0.3 | +1.5 | stroke +2.6 (cut) |
| 10 | N | 1.74 | +1.1 | +2.7 | -0.7 | +0.8 | +0.3 | n/a | -0.4 | +1.4 | stroke +2.7 (thin) |
| 11 | I | 1.73 | -0.6 | +2.5 | -1.9 | +0.6 | +0.8 | n/a | -0.5 | +0.4 | stroke +2.5 (thin) |
| 12 | s | 1.69 | -0.4 | +1.1 | +0.2 | -3.4 | +0.9 | n/a | -0.6 | +0.0 | vertical -3.4 (bot) |
| 13 | G | 1.67 | +0.2 | -0.9 | +0.5 | -3.4 | -0.7 | n/a | -0.1 | +0.5 | vertical -3.4 (bot) |
| 14 | f | 1.63 | -0.6 | -1.4 | +0.9 | +3.2 | +1.1 | n/a | -0.3 | +1.1 | vertical +3.2 (top) |
| 15 | v | 1.58 | +0.2 | +2.3 | -2.1 | +1.1 | -0.1 | n/a | +0.0 | +1.1 | stroke +2.3; proportion -2.1 |
| 16 | 7 | 1.48 | +1.4 | -2.3 | -1.1 | +1.5 | +1.7 | n/a | -0.9 | +1.2 | stroke -2.3 (thin) |
| 17 | 6 | 1.46 | +0.2 | -1.2 | -0.3 | +3.0 | +0.7 | n/a | +0.2 | +0.2 | vertical +3.0 |
| 18 | 5 | 1.42 | -0.5 | +1.4 | -0.1 | -0.5 | +2.9 | n/a | -0.7 | +0.6 | bearings +2.9 |
| 19 | b | 1.41 | -0.0 | -1.5 | +0.9 | -2.8 | -0.2 | n/a | +0.1 | +0.8 | vertical -2.8 (top) |
| 20 | 4 | 1.25 | +0.9 | -2.2 | -0.4 | +0.5 | -0.8 | n/a | -0.0 | +1.2 | stroke -2.2 (thin) |

Full order: g 1 q y W V S o r N I s G f v 7 6 5 b 4 U w 8 k H L J Y Q C T M A n E O d Z m 3 F i e x l X u z K 9 2 R a D B t h c j p P 0

---

## 4. The owner's guess: k x s y

| | Regular | Italic | Bold | BoldItalic | verdict |
|---|---|---|---|---|---|
| **y** | #6, F 3.13, cut +4.1 | #7, F 2.01, descender −3.1, stroke −2.4 | #2, F 3.72, cut +4.6 | #4, F 2.37, stroke −3.0, descender −2.8 | **CONFIRMED, every cut** |
| **k** | #12, F 2.27, below baseline −3.3, cut +2.5 | #17, F 1.47, spacing +2.7 | #7, F 3.03, below baseline −5.3 | #24, F 1.13 | **CONFIRMED in the romans**, mostly for its kick |
| **s** | #9, F 2.68, cut +3.3, cross-cut +3.0 | #39, F 0.29 | #39, F 0.65 | #12, F 1.69 | **CONFIRMED in Regular only** |
| **x** | #25, F 0.97 | #29, F 0.59 | #16, F 1.90 | #44, F 0.33 | **REFUTED**: not an outlier in any cut |

**y**

- The roman y has **more contrast** than any diagonal in the face should: its
  cut is 2.71 against the family, and its thin is the tail.
- The italic y is **deep and light**:
  - its descender reaches −319 where p and q stop at −282, 37 units lower;
  - BoldItalic is 54 units lower still, at −337;
  - its stroke median is −2.4 sigma.
- The y's descender is the tail he set to 30 in round 395 (Cancelleresca's
  26 was the source). [inf] The depth is a separate lever from that width.

**k**

- The roman k's leg kicks **22 units below the baseline** in Regular and 35
  in Bold. Every flat letter stops at −1, and none of the six references goes below −6.
  K does the same: −28 and −47.
- That is the ruled R/K/k kick (rounds 138 and 228). So the part of the flag
  that is not a ruling is the k's **arm contrast**: cut 3.26 against its stem
  family, +2.5 sigma in Regular.
- At stress sizes the reader confuses k with h and l (Regular 13 + 10;
  Italic k>l 16, k>d 12). Relative to the rest of the face that is not an
  outlier: legibility is +0.4 to +0.8.
- The italic k scores on spacing. B2's k identity is (−5, −17) in the italic,
  and his bench pushes the k's right side consistently: −29.5 units on
  average over 4 pairs, t 6.0, the highest in the italic.

**s**

- The Regular s is the roman's most contrasted round: cut 2.71, where o is
  1.98.
- The cross-cut term (+3.0) says the Bold s does not share it. Round 391's
  0.33 S floor did not bring the 400 into line with its own 700.
- The italic and bold s are clean.

**x**

- Round 395 raised the roman x's light diagonal to the full pen (his pick).
  It now sits inside its family on every axis in Regular.
- The Bold x's top stands 13–16 units above its family (x 461; v 448,
  w 445, y 447), which is +2.5 sigma, with stroke thin +2.0. That is the
  closest the x comes to a flag, at F 1.90. The Regular x is 451 against
  v 443.

---

## 5. Recommended redo list

"Rulings behind them" means a flag whose leading axis matches something he
ruled. Those are listed so they are not re-raised, not proposed.

### 5a. Worth a redo (no ruling found behind the deviation)

| # | cut | glyph | axis a fix would target | what the number says |
|---|---|---|---|---|
| 1 | Regular, Bold | **e** | b stroke (cut) | Thin 21.7 against stroke 38.8. The bar and tail run far lighter than its own o, which is 38.3 thin and 55.5 stroke. Any raise must keep the round-400 mouth gate green (`etrace/e_hint_gate.py`). |
| 2 | all four | **y** | b stroke, d vertical | Roman: contrast. Italic: descender 37 units past p/q, and light. |
| 3 | Regular | **t** | f spacing | B2 identity (+10, −14), the largest bearing correction in the roman. His bench pushes the t's right side −18 units on average over 18 pairs (t 5.5). Cut +1.9. The rule-built fitting misreads the t's crossbar and tail. [inf] A drawing change to the tail/bar extents would let the bearings go back toward the rule. |
| 4 | Regular, Italic | **j** | f spacing, e bearings | Kerns into the j run +22 to +31 in the roman (`aj bj ej ij nj oj`) and +8 to +20 in the italic, so the hook tucks under the letter before it. Roman balance −3.1. |
| 5 | Regular | **S** | f spacing, b stroke | B2's S+lowercase kerns run +24 to +35 on 9 pairs (`Sa Sc Se Sh Si So Sp St Su`), so the S is fitted far too tight. Its stroke is +2.8 heavy. The 09-18 ledger's "+27%" S was re-cut in round 224 and reverted in 225, so ask before touching the drawing; the fitting half is free. |
| 6 | Regular | **s** | b stroke (cut), h cross-cut | See section 4. |
| 7 | Regular, Bold | **k** | b stroke (the arm) | See section 4. The kick is ruled. |
| 8 | Regular | **a** | f spacing | B2 identity (+12, −5): the a's left side is 12 units tight against his eye. |
| 9 | Italic | **F** | f spacing, b stroke | Kerns F+lowercase −26 to −39 (`Fa Fe Fl Fr`), stroke +4.1, and the BoldItalic F does not share it (cross-cut +3.5). |
| 10 | Italic | **O** | f spacing | `On Op Or` need +23 to +30: the italic O is fitted tight. |
| 11 | Italic, BoldItalic | **W** (and BI **V**) | b stroke | Heavy for the diagonal family: +3.1 and +3.3. |
| 12 | Italic, Bold | **N** | b stroke | Heavy (+3.0). In the Bold the thin is +3.5, so the N is flatter than its family. |
| 13 | Italic | **7** | b stroke (thin) | −2.9, light. The italic 7's colour question was ruled in round 212; this is its thin. |
| 14 | Bold | **T** | b stroke | Stem −3.8 sigma light, and the Regular T does not share it (+2.9). |
| 15 | Bold | **t 2 z r P** | b stroke | t, 2, r and P have contrast or thin excess, each unshared by the Regular (cross-cut +1.9 to +3.3). The z is light (thin −2.9). |
| 16 | BoldItalic | **1**, **q** | b stroke; e bearings | The 1's contrast is unshared by the Italic. The q's balance is +4.2, so its white piles on the left. |

### 5b. Flagged, with a ruling behind the deviation (do not re-raise)

- **Q** (Regular and Bold width): round 225, *"the roman Q keeps its tail"*.
- **Italic and BoldItalic g** (descender −194): the Italic g is approved
  (`approved.json`). The BoldItalic g took the Italic's drawing in round 398
  on the weight axis only.
- **k and K below the baseline**: the kicks, rounds 138 and 228.
- **I, l and J "thin"** (Regular +4.6, +3.3, +3.5; Bold I +4.6): these are the
  only stems with no hairline. Albo's serifs are wedges, not hairlines, so
  their p10 is the stem. This is the face's construction, not a defect.
  Round 373 set the I's wedges to his numbers.
- **6 and 8 "figure height"** (+3.9 to +4.8, every cut): this rests on two
  old-style references only. Albo's ascending figures top at 637–639, which
  is 177 above its x-height figures at 460; Georgia's gap is 170, Hoefler's
  226. [inf] Round 373b put every figure on the baseline and nobody has ruled
  on figure heights since. **Weak; ask before drawing.**

---

## 6. Checked and found CLEAN

- **Colour (a) never reaches 3 sigma in any cut**, on any glyph.
  - As rendered at the reader's sizes in 2-bit, no letter is too black or too
    pale for its family, beyond what references show.
  - That retires the 09-18 ledger's colour rows: the roman T, L, J and C, and
    both 8s.
- **Legibility (g) never reaches 3 sigma** relative to the face.
  - The largest single confusion is still **a→e**: 376 of 2,176 a's in
    Regular (21%, against 1–14% in the six references) and 337 in Italic.
  - The a's own score is only +1.2. The reason is that Albo reads worse at
    9–11 px across the whole face (12.3% character error against Georgia's
    3.1% and Charter's 2.1%), and the a is in line with that.
  - **That is a face-wide small-size weight question, not a fit question.**
    See section 7.
- **Glyphs under F 1 in all four cuts:** c d h i u A B C D R Z 0 9.
  - 33 of 62 glyphs are never flagged in any cut.
- **The 2026-09-18 ledger, re-checked on round 402:**

| 09-18 finding | now | |
|---|---|---|
| italic Y (+92%, since corrected to −6%) | #13, F 1.62 | clean |
| italic z (light, flat) | #48, F 0.11 | **fixed** (round 224) |
| italic A (apex, weight) | #27, F 0.71 | clean |
| italic 1 (heavy) | #21, F 1.27 | clean |
| italic Z | #51, F 0.06 | clean |
| italic g descender −194 | #2, F 4.60 | **unchanged, and approved** |
| italic e (no overshoot, light) | #31, F 0.51 | clean |
| italic X (15-unit thin) | #53, F 0.05 | clean |
| italic E (heaviest capital) | #15, F 1.52 (balance, not weight) | clean on weight |
| italic 5, O | 5 #40 clean; **O #4, now on spacing, not weight** | changed reason |
| italic R right side tight | #30, F 0.53 | clean |
| italic f p T H P | f #22, p #44, T #23, H #45; P #10 (spacing) | clean but P |
| italic y | #7, F 2.01 | **still flagged** |
| italic ascender line ragged (47-unit spread) | b 756, d 771, h 772, k 769, l 772, f 787 | b still 15 units short; f +15; b scores #25, F 1.08 |
| italic u x-line +15 | u 431 = n m r z 431 | **fixed** |
| roman Q width, touching | #4, F 4.17 (width) | ruled; touching fixed by kerns (round 348) |
| roman Z, W, Y, X weights (instrument artifacts) | #40, #33, #30, #24 | clean |
| roman S | #7, F 2.81 (now spacing +3.5, stroke +2.8) | **still flagged** |
| roman 1, 4, 7 figures | #43, #15 (F 1.67), #29 | clean |
| roman z overshoot | #26, F 0.78 | clean |
| roman s 6 units proud | top 447 against o 444 (vertical +1.3) | clean on height; flagged on contrast |
| roman x overshoot +10 | #25, F 0.97 | clean |

---

## 7. What the metric cannot see

- **A change made to a whole family.** Every z is relative to the family, so
  a hairline thinned on all five arches reads as no misfit. This accounts for
  10 of the 27 validation misses. A face-level check would be needed: family
  medians against the references' family medians. It is not built.
- **Face-wide properties.** The 400's small-size legibility deficit
  (12.3% versus 2–7% for five of six references at 9–11 px, with Baskerville
  the outlier at 28%) and the overall contrast level are not per-glyph fit.
- **Local shape.** Joins, spurs, the j's crumpled head, a notch or a kink.
  Those are `cmp_joints.py`, `cmp_aldine_glitch.py`, `cmp_contour_hairs.py`
  and `albo_bumps.py`, which were not re-run here.
- **Serif-tip ridges.** `thin` is p10 of the whole ridge. On a letter with no
  hairline (I, l, J) the p10 is the stem. At the 700s, on x, z and 1, it is a
  serif tip (`albo-thick-thin-options` §1). Flags led by `thin` on those
  letters are the construction, not a thin stroke.
- **Figures against two references only.** None of the six system faces
  exposes old-style figures through `onum`, so the figure axes are a
  two-reference comparison with a fixed spread of 0.5.
- **Spacing for the bolds and the figures.** He never benched them, so axis f
  is n/a there, and their F is on seven axes.
- **Deliberate irregularity.** `docs/albo-imperfections.md` says a table, not
  a jitter. The cross-cut axis h is the metric's only nod to it: a deviation
  shared by both weights counts less than one found in only one weight. The
  metric still cannot tell a ruled deviation from an accident, which is why
  section 5b exists.
- **His eye.** The metric flagged 10 of 37 of his fixes, not 37. It is a
  screen for where to look, ranked, with a reason per letter. It is not a
  substitute for the word image.

## Files

- `tools/wedge_serif/fit_audit/`:
  - the code: `common.py`, `geom.py`, `run_geom.py`, `legib.py`, `spacing.py`,
    `score.py`, `validate.py`, `report.py`, `proof.py`;
  - `run_all.sh`, the whole pipeline.
- `tools/wedge_serif/fit_audit/results/`:
  - `fit-r402.json`: every glyph, every axis, every sub-axis;
  - `validation.json` and `variants.json`: section 2;
  - `spacing.json`: axis f inputs at `bdfd477`;
  - `legib.json`: per-glyph occurrences, errors and substitutions for all 84
    faces.
- The proof page is in the session scratchpad (`fitaudit/proof/index.html`).
  It shows the top 12 per cut, in words and between their family members, at
  27 px ×2 nearest and at 54 px, with a heat bar of the axis z-scores and each
  cut's alphabet colored by F. All images are lossless PNG with no fixed
  dimensions.
