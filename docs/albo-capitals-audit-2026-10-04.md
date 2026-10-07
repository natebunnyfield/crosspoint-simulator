# Albo: the capitals' size, shape and contrast, measured (2026-10-04)

Owner todo (2026-10-03): *"make capitals the right size and shape and
contrast"*.

**Status: AUDIT.** This is the measurement the fixes are designed against.
Fix 1 (the Bold capitals' contrast) is out as OPTIONS C1-C4, not ruled:
`docs/albo-capitals-contrast-options-2026-10-06.md`.

## Method

`tools/wedge_serif/instruments/poor_trace.py` traced each of the 26 capitals
in all four cuts, against the six references its cut set names. It also
traced n, o, e, a, d, h, b, p, q and u for the lowercase. The references are
Georgia, Charter, Times, Baskerville, Hoefler Text and Palatino, in their
regular, italic, bold and bold italic.

- Every face is rendered unhinted, unsheared by its measured slant, and
  scaled to Albo's x-height of 429.
- Stroke thicknesses are the chamfer ridge's 10th, 50th and 90th percentiles,
  each over the SAME face's n stem.
- "Contrast" is p90 / p10.

Albo is round 476. The raw JSON is in
`tools/wedge_serif/bench/cap-audit-2026-10-04/`, one file per cut and letter.
Every number below is Albo divided by the reference median.

**Caveat on "thin".** The p10 is the thinnest tenth of all the stroke, and
serif tips count toward it. A face whose serifs taper to points reads thinner
there than one with blunt wedges. Read the thin and contrast columns as "how
heavy the light parts of the letter are", not as one named hairline.

## 1. Contrast: right in the 400s, too low in the bolds

| cut | lowercase contrast | capitals contrast | lowercase thin | capitals thin |
|---|---|---|---|---|
| Regular | 0.69 | 0.70 | 1.48 | 1.32 |
| Italic | 0.71 | 0.74 | 1.42 | 1.16 |
| **Bold** | 0.86 | **0.55** | 1.18 | **1.75** |
| **Bold Italic** | 0.76 | **0.48** | 1.62 | **2.06** |

- **In the Regular and the Italic,** the capitals' contrast is the lowercase's.
  Both are about 0.7 of the references', which is Albo's own low contrast (the
  Albertus model the owner chose). Against the face itself they are in line.
- **In the Bold and the Bold Italic,** the capitals carry about two thirds of
  the lowercase's contrast. Their light strokes are 1.75× and 2.06× the
  references', against the lowercase's 1.18× and 1.62×. **This is the largest
  inconsistency found:** the bold capitals' thins are much too heavy for the
  face they sit in.

## 2. Size (height against the x-height)

| | Regular | Italic | Bold | Bold Italic |
|---|---|---|---|---|
| median capital | 1.015 | 1.037 | 1.012 | 0.990 |
| N | **0.964** | **0.957** | **0.949** | **0.950** |
| tallest | X 1.043, K 1.041, Y 1.038, M 1.037 | X 1.066, G 1.065, S 1.053 | X 1.048, Y 1.047, M 1.045 | G 1.050, S 1.040, X 1.038 |

- **The N is short in every cut:** about 5% under its own cut's median
  capital.
- **The diagonal capitals stand 2–3% taller** than the stemmed ones in the
  Regular and the Bold. Their apexes overshoot.
- Overall, the capitals' size against the lowercase is close to the
  references' (+1.5% in the Regular).

## 3. Shape (ink width against the references)

| | Regular | Italic | Bold | Bold Italic |
|---|---|---|---|---|
| median capital | 1.020 | 0.911 | **0.907** | **0.833** |

- **Narrow:** I (0.60 R, 0.42 I, 0.65 B, 0.46 Z) and J (0.84 R) everywhere.
  In the bolds: B 0.82 / 0.68, E 0.88 / 0.67, F 0.83 / 0.66, P 0.87 / 0.75,
  R 0.84 / 0.83, L 0.87 / 0.81, X 0.83 / 0.83.
- **Wide:** Q (1.87 R, 1.70 B, from its long tail, which was ruled), T 1.17,
  W 1.16, Z 1.16, H 1.085 (Regular).
- **Why the bolds are narrow.** `build.solve_widths` drives every roman
  capital to the REGULAR references' median width at every weight, but bold
  references widen as they gain weight. The italic capitals take their own
  widths (aldine, `CAP_NARROW` 0.953), and the Bold Italic goes narrowest.

## 4. Weight (thick strokes over the face's own n stem)

The median is right in every cut (0.99 / 0.92 / 1.02 / 1.06). The outliers:
- **Light:** C, O, Q, G (0.82–0.87, Regular), Z 0.80 (Regular).
- **Heavy:** L 1.22 (Regular), and E, L, Z in the Bold (1.30–1.39).

## Proposed order of fixes (each as options, judged on pictures)

1. **The bold capitals' contrast.** Lighten their thin parts toward the bold
   lowercase's contrast.
2. **The bold capitals' widths.** A bold factor on the width target, and the
   Bold Italic's own widths.
3. **The N's height**, and the diagonals' apex overshoot.
4. **Single letters:** I, J narrow; T, W, Z wide; the light rounds and the
   heavy L / E / Z.

## Levers for fix 1, the Bold capitals' light strokes (found 2026-10-04, nothing changed)

Read from the builders, round 481. The bold capitals have five kinds of light
stroke, and each has its own dial.

- **Bars:** `pen.CAP_BAR` = the pen's horizontal x 1.18 (round 94). It is the
  pen's own width, so its ratio to the stem is the same at every weight. That
  is why the bars do not lighten as the face gets heavier. Per letter, in
  `outlines/glyphs/caps_straight.py`:
  - E and F: x 1.0;
  - H: 0.95;
  - A: 0.9;
  - G: 0.8;
  - L's foot: x 1.0;
  - Z: x 1.0;
  - T: 0.85 x `T_BAR_K`. `T_BAR_K` is 0.76 at the 700 only, from round 415,
    and is the precedent for a bold-only factor.
- **Bowls** (O, C, G, D, Q and the bowls of B P R): `primitives.ring` and
  `half_bowl` take the pen's width at each tangent. `ring` already has the
  per-letter contrast lever, `con`: it re-spreads the widths about their mean,
  so above 1 the thins thin without moving the family's `BOWL_HAIR` /
  `BOWL_MAX`. No capital passes it today.
  The lowercase o's hairline sits on an owner-ruled legibility floor
  (`O_FLOOR_ADJ` 0.50 x stem, rounds 92 and 265: the hairs went gray at 13 pt).
  A capital's hairline is the same kind of trade and is his to rule, not ours
  to tune.
- **Thin diagonals** (A V W X Y M K): `caps_straight.pw` makes the thin stroke
  0.72 x the pen's width at its angle. Above stem 84, `DIAG_CAP` caps only the
  THICK.
- **Thin stems:** the N, through `_n_thin`, traced from Charter at 0.57 of the
  cap stem (round 415, ruled). Already done.
- **Serifs:** the wedge family at the 400's size above stem 84 (round 277).
  They are blunt by design (the Albertus model).
  **The "thin" column overstates I, L, J and U**: their p10 is a stem or a
  wedge, because they have no hairline to lighten. They read 2.35-3.34x the
  references only because the references' serifs taper to points.

Ranked by the Bold's thin against the reference median (thin = p10 over the
n stem): I 3.34, L 2.97, J 2.90, U 2.35, H 2.08, E and F 2.04, Y 2.04,
Z 1.93, X 1.88, W 1.87, V 1.85, A 1.84, M 1.66, K 1.60, the rounds and the
bowled letters 1.46-1.55, T 1.24, N 1.00. Left out the serif-only four, the
gap is spread evenly over the bars, the diagonals and the bowls. That points
to one bold-only factor per kind, not letter fixes. A target that matches the
bold lowercase's contrast (0.86 of the references) needs the capitals' thins
at about 0.67x their current weight.
