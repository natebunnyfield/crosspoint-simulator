# Albo's most critically poor characters: the list, the references, the harness (2026-09-26)

Owner, 2026-09-26: *"give me options for the most critically poor characters
(all faces). trace other reference fonts and come up original solutions too.
take three passes."*

**Owner ruling mid-pass, 2026-09-26 (reaffirming 2026-09-13): glyph drawing is
not delegated -- the main session draws.** So this document is MEASUREMENT AND
REFERENCE PREP: the refreshed list (section 1), what each character measures
against each reference face (section 3, the tables to draw from), rendered
reference sheets (section 4), and the render + gate harness (section 5). The
arms already drawn before the ruling are committed behind default-off dials so
nothing is lost, and are recorded in section 6 as measurements, not proposals.

- **Commits:** `fcb81d4` (roman/Bold arms + instruments), `39dc1b8` (italic
  arms), and the commit carrying this doc (tables, sheets, harness).
- **Unset = today.** With every dial unset, all four cuts are outline- and
  advance-IDENTICAL to HEAD (`cmp_outlines.py --advances`), checked at both
  arm commits.
- **Baseline:** round 409 (`f71dddf`). Round 409 RESIZED THE ITALIC mid-pass
  (nib 0.92, set width 1.15, spacing refit), which changed the italic half of
  the list (section 1).
- **Confidence:** every number is measured by the named instrument unless it
  is marked [inf].

## 1. The list, on round 409

The fit audit (`docs/albo-fit-audit-2026-09-26.md`, F >= 2.0 flags), re-run on
a `git archive` build of `f71dddf`, spacing read at the same commit. Bold =
unruled; plain = a ruling stands behind the deviation.

| cut | flagged (F, leading sub-axis, excess) |
|---|---|
| Regular | e 4.32 (cut +5.3) · Q 4.20 (width) · I 3.96 (thin) · **M 3.83 (spacing: bench push +5.4)** · **j 3.70 (spacing: B2 kerns +4.9)** · **y 3.15 (cut +4.1)** · J 2.84 (thin) · S 2.82 (spacing +3.4; stroke +2.8) · **t 2.77 (spacing: B2 bearing +4.0)** · **s 2.64 (cut +3.2)** · 6 2.56 · l 2.36 · k 2.25 (kick) · **a 2.09 (spacing)** · 8 2.05 |
| Italic | **F 5.04 (stroke +4.4; spacing +4.6)** · g 4.71 (approved) · **j 4.17 (stroke +3.9, heavy)** · **t 2.60 (stroke +3.2, heavy)** · 7 1.99 · I 1.87 |
| Bold | e 4.93 · **y 4.04 (cut +5.0)** · I 3.57 · Q 3.16 · **t 3.12 (cut +3.9)** · k 3.04 · 6 2.67 · 8 2.66 · **N 2.52 (thin +3.4: flat)** · K 2.49 · z 2.16 (thin = a serif tip) · **r 2.00** · T 1.89 |
| BoldItalic | g 5.67 (approved's drawing) · **r 3.59 (cut +4.1)** · 1 2.73 (figure) · **y 2.32 (stroke -2.9; deep)** · **q 2.21 (bearing balance +3.4)** · S 2.12 · **V 1.96 · W 1.93 (near-monoline)** |

**What round 409 moved.** Before it (round 405) the italic list was
F g W k j J 7 N and the BoldItalic g r 1 q y W V. The resize thinned the italic
stem family (the hm letters' nib x 0.92) and left `j t f` on `ALD_WF_UP`, so
the italic **j** and **t** became its worst unruled letters; W and N dropped
under the flag.

**The characters chosen** (worst unruled, figures excluded -- another agent's):
roman **y** (Regular, Bold), **t** (Regular spacing, Bold contrast), **j**
(Regular), **s** (Regular), **N** (Bold), **T** (Bold); italic **j** and **t**
(Italic), **y** (Italic, BoldItalic), **r** (BoldItalic), **V W**
(BoldItalic), **F** (Italic), **q** (BoldItalic).

**Excluded, and why:** e (rounds 395/400), Q (round 225 tail), I l J (wedge
serifs, the construction), k K (the ruled kick), the approved g's, the
apostrophes (403/404), every figure (another agent), S (round 225 "leave S as
it was" and round 231 "at half"; its lead axis is spacing now), M and a
(spacing only -- the B2 tables), z Bold (its thin is a serif tip, fit audit
section 7).

## 2. What each character measures, in one line (details in section 3)

- **roman y** -- the tail's leftward run lies on the pen's THIN (round 391
  floor 0.33 S = 22 units): p10 0.67 of the diagonal family where every
  reference's y is 0.82-1.06. The references' tails run STRAIGHT down the right
  diagonal's line and turn only in the last third into a weighted terminal
  (Georgia, Times, Baskerville, Hoefler: a ball; Charter: an angled ball;
  Palatino: a small flat tip pointing up). In every reference the y's bottom
  is its p's (y-p 0 to -15).
- **roman t** -- conventional in raw numbers (left arm 1.00 n, right 1.71 n,
  bar 0.54 n; Georgia 0.96 / 1.51 / 0.52). The Bold's contrast flag is the
  eight corner spokes of two SQUARE bar ends plus the cut top (thinmap), not a
  thin bar. The Regular's flag is spacing (B2 (+10, -15)). The Bold t also has
  a 3-5 unit sliver on its right edge near the cut top ((197,539) (194,524)
  (199,520) (196,512)), present today.
- **roman j** -- the hook's reach left of the origin: Albo -82 against
  Georgia -66, Charter -70, Times -74, Baskerville -118, Palatino -29,
  Hoefler 0; Albo's stem stands 0.89 n from the origin where Georgia's,
  Charter's and Times' stand 1.31 n. The bearing rule fits the j on its
  x-height band (the stem only), so the hook's reach is never paid for and B2
  had to learn kerns (+22 to +31) before it.
- **roman s** -- DIRECTION BEFORE WIDTH: the top and bottom arcs run
  horizontal where the PEN is thin (34.5 at the 400), while the o and c are on
  the BOWL profile (hair 0.46 S since round 265, 30.8 units at the 400 -- the arm comments' "0.70 S" is stale). Its thin is 0.65 of its own o's; the
  references' 0.90-1.03. Its median is 0.84 of the o's; theirs 0.54-0.77.
- **roman N** -- flat: the thin stems are 0.74 / 0.73 of the H's stem where
  the references run 0.25-0.61 (Regular) and 0.22-0.55 (Bold); Charter is the
  nearest.
- **roman T (Bold)** -- the bar is 0.55 of the stem where every bold reference
  runs 0.26-0.42 (heavier, not lighter); the flag is a p50 falling between the
  bar's and the stem's ridge populations.
- **italic j, t** -- in all six reference italics (both weights) the j's and
  t's stems are the i's (0.94-1.11); Albo's are 1.34 / 1.27 (Italic), 1.06 /
  1.02 (BoldItalic). The f is the same (1.27) and unflagged.
- **italic y** -- the y's bottom is its p's in eleven of twelve reference
  cuts (0 +/- 2; Hoefler BI -13); Albo's is 35 below (Italic) and 50 below
  (BoldItalic) -- the finial the tail took in round 276 reaches 22-30 under the
  drop it replaced. The 700 reads light because that long hairline is most of
  the ridge.
- **italic r (BoldItalic)** -- the flag is its p10 landing on CORNER SPOKES
  (head tip, finial face, the foot's points), not a thin stroke; three arms
  that change only the arm's root swung F from 2.11 to 6.73. Reference arms:
  root 0.37-0.97 n, reach 1.18-1.84 n (Albo 0.87 / 1.65). Terminals: Georgia,
  Flanker, Times, Hoefler a ball; Charter a flat angled cut; Palatino a thin
  flag.
- **italic V, W (BoldItalic)** -- near-monoline: rising / falling 0.64 / 0.60
  where Georgia, Palatino, Times, Hoefler run 0.31-0.44 and Charter and
  Flanker 0.64-0.65 (Albo sits with Charter and Flanker). The W's flag is its
  MEDIAN: thinning its hairline pushes the p50 onto the thick strokes and makes
  it worse; the thick strokes are 1.16 n (references 0.98-1.08).
- **italic F** -- worst in the italic, for two reasons no drawing of its bars
  reaches: spacing (B2 F+lowercase kerns, inherent to an F) and its p50 sitting
  on the CAP STEM (58% of its ridge) while the stem family's median is
  lowercase, which round 409's nib made lighter. Bars 0.68 / 0.59 of the stem
  against 0.34-0.54; the top arm 3.23 stems past the stem, inside the
  references' 2.81-3.27.
- **italic q (BoldItalic)** -- bearing balance: rsb -50 (the descender foot
  runs right), lsb 2; references rsb +26 to +112, lsb -28 to +8. A fitting
  question as much as a drawing one.

## 3. Reference tables (per character, per cut, per reference face)

Generated by `instruments/poor_tables.py --albo <round-409 build>`: every face
unhinted, unsheared by its measured slant (`fig27_trace.Face`), scaled so its
x-height is Albo's 429, at 2 px per unit. `n` is that face's n stem; thin /
med / thick are the chamfer ridge's p10 / p50 / p90 over n; cut is p90/p10.
Albo's row is scaled by ITS x's top, which carries ~28 units of wedge over the
line, so Albo's heights read about 6% low here (the fit audit's lines do not
have that bias). Per-character columns are named in the tool's header.

**y -- Regular** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | y-p | tail@-.3/n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 467 | 420 | -284 | 32 | 37 | 61 | 0.40 | 0.75 | 1.05 | 2.60 | -17.00 | 0.46 |
| Georgia | 460 | 429 | -194 | -8 | -13 | 81 | 0.39 | 0.41 | 0.99 | 2.52 | 0.00 | 0.51 |
| Charter | 458 | 429 | -194 | -1 | -15 | 74 | 0.53 | 0.58 | 0.96 | 1.80 | 0.00 | 0.69 |
| Times | 468 | 429 | -208 | 6 | 6 | 78 | 0.48 | 0.51 | 0.97 | 2.02 | -2.00 | 2.27 |
| Baskerville | 496 | 429 | -264 | -5 | -0 | 74 | 0.32 | 0.34 | 0.98 | 3.04 | 0.00 | 0.35 |
| Hoefler | 512 | 429 | -282 | -20 | -30 | 90 | 0.36 | 0.42 | 0.98 | 2.74 | -14.50 | 0.40 |
| Palatino | 480 | 418 | -253 | 7 | 18 | 74 | 0.38 | 0.49 | 1.02 | 2.68 | -2.00 | 0.50 |

**y -- Bold** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | y-p | tail@-.3/n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 437 | 416 | -298 | 31 | 37 | 102 | 0.37 | 0.79 | 0.97 | 2.59 | -36 | 0.52 |
| Georgia | 526 | 429 | -192 | -12 | -16 | 142 | 0.28 | 0.95 | 0.96 | 3.37 | 0.00 | 1.43 |
| Charter | 476 | 428 | -194 | -4 | -19 | 109 | 0.39 | 0.50 | 0.95 | 2.47 | 0.00 | 1.68 |
| Times | 452 | 429 | -203 | 8 | 9 | 128 | 0.21 | 0.24 | 0.96 | 4.55 | -2.00 | 0.24 |
| Baskerville | 560 | 429 | -268 | 3 | 7 | 172 | 0.35 | 0.37 | 0.93 | 2.66 | -14.50 | 0.87 |
| Hoefler | 568 | 429 | -270 | -26 | -14 | 165 | 0.28 | 0.32 | 0.91 | 3.20 | -13.50 | 0.33 |
| Palatino | 485 | 418 | -240 | 11 | 10 | 112 | 0.31 | 0.45 | 1.03 | 3.27 | -4.50 | 0.52 |

**t -- Regular** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | L arm/n | R arm/n | bar/n | tail/n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 283 | 531 | -3 | 44 | 21 | 61 | 0.66 | 0.98 | 1.02 | 1.55 | 1.00 | 1.71 | 0.54 | 0.54 |
| Georgia | 290 | 561 | -10 | 6 | 11 | 81 | 0.52 | 0.98 | 1.01 | 1.95 | 0.96 | 1.51 | 0.52 | 0.52 |
| Charter | 266 | 512 | -3 | 22 | 9 | 74 | 0.57 | 1.00 | 1.00 | 1.76 | 0.76 | 1.84 | 0.56 | 0.50 |
| Times | 258 | 570 | -8 | 10 | -1 | 78 | 0.43 | 0.99 | 0.99 | 2.33 | 0.88 | 1.30 | 0.43 | 0.46 |
| Baskerville | 282 | 564 | -18 | 28 | 2 | 74 | 0.32 | 1.01 | 1.01 | 3.12 | 0.00 | 0.00 | 0.32 | 0.40 |
| Hoefler | 316 | 528 | -18 | 32 | 24 | 90 | 0.57 | 1.02 | 1.04 | 1.84 | 0.62 | 1.82 | 0.59 | 0.43 |
| Palatino | 269 | 567 | -6 | 20 | 7 | 74 | 0.57 | 0.99 | 1.02 | 1.79 | -0.03 | 0.03 | 0.57 | 0.52 |

**t -- Bold** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | L arm/n | R arm/n | bar/n | tail/n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 278 | 529 | -24 | 43 | 21 | 102 | 0.71 | 0.99 | 1.00 | 1.41 | 0.33 | 0.73 | 0.45 | 0.45 |
| Georgia | 346 | 558 | -12 | 0 | 5 | 142 | 0.33 | 1.01 | 1.01 | 3.04 | 0.55 | 0.85 | 0.33 | 0.36 |
| Charter | 296 | 528 | -4 | 17 | 2 | 109 | 0.49 | 1.01 | 1.01 | 2.08 | 0.52 | 1.19 | 0.49 | 0.46 |
| Times | 286 | 586 | -6 | 18 | 9 | 128 | 0.36 | 1.00 | 1.00 | 2.80 | 0.44 | 0.79 | 0.35 | 0.28 |
| Baskerville | 376 | 572 | -18 | 21 | -6 | 172 | 0.33 | 0.99 | 0.99 | 2.98 | 0.36 | 0.75 | 0.33 | 0.46 |
| Hoefler | 406 | 560 | -15 | -2 | 10 | 165 | 0.39 | 1.01 | 1.02 | 2.60 | 0.46 | 0.95 | 0.41 | 0.34 |
| Palatino | 276 | 582 | -10 | 20 | 6 | 112 | 0.50 | 0.98 | 1.00 | 1.98 | 0.00 | 0.93 | 0.51 | 0.50 |

**j -- Regular** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | stem lsb/n | hook reach/n | ink lsb |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 210 | 590 | -277 | -82 | 76 | 61 | 0.98 | 0.98 | 1.03 | 1.05 | 0.89 | 2.23 | -82 |
| Georgia | 259 | 660 | -194 | -66 | 66 | 81 | 0.99 | 1.00 | 1.00 | 1.01 | 1.31 | 2.12 | -66 |
| Charter | 251 | 632 | -194 | -70 | 55 | 74 | 0.98 | 1.00 | 1.00 | 1.02 | 1.31 | 2.25 | -70 |
| Times | 260 | 666 | -208 | -74 | 79 | 78 | 0.80 | 1.01 | 1.01 | 1.26 | 1.31 | 2.26 | -74 |
| Baskerville | 303 | 720 | -264 | -118 | 82 | 74 | 0.56 | 1.01 | 1.01 | 1.80 | 1.42 | 3.00 | -118 |
| Hoefler | 190 | 672 | -282 | -0 | 57 | 90 | 0.86 | 1.01 | 1.01 | 1.18 | 1.02 | 1.02 | -0.50 |
| Palatino | 186 | 626 | -252 | -29 | 55 | 74 | 0.73 | 1.05 | 1.06 | 1.45 | 0.98 | 1.37 | -29 |

**s -- Regular** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | s/o thin | s/o med | s/o thick |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 294 | 426 | -16 | 52 | 59 | 61 | 0.38 | 0.81 | 1.04 | 2.72 | 0.65 | 0.84 | 0.87 |
| Georgia | 319 | 442 | -12 | 32 | 34 | 81 | 0.42 | 0.57 | 1.04 | 2.47 | 1.03 | 0.66 | 0.93 |
| Charter | 282 | 438 | -8 | 38 | 37 | 74 | 0.51 | 0.70 | 1.02 | 1.98 | 0.97 | 0.77 | 0.89 |
| Times | 292 | 442 | -14 | 47 | 34 | 78 | 0.36 | 0.50 | 1.10 | 3.05 | 0.90 | 0.62 | 0.96 |
| Baskerville | 278 | 446 | -18 | 44 | 36 | 74 | 0.30 | 0.40 | 1.04 | 3.47 | 0.93 | 0.57 | 0.89 |
| Hoefler | 310 | 446 | -22 | 43 | 32 | 90 | 0.36 | 0.48 | 1.04 | 2.92 | 1.00 | 0.54 | 0.92 |
| Palatino | 323 | 432 | -12 | 33 | 29 | 74 | 0.35 | 0.44 | 1.05 | 2.97 | 0.90 | 0.55 | 0.89 |

**N -- Regular** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | thin/H | diag run/H |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 756 | 644 | -1 | 44 | 44 | 61 | 0.82 | 0.84 | 1.04 | 1.27 | 0.74 | 1.28 |
| Georgia | 665 | 618 | -6 | 10 | 8 | 81 | 0.52 | 0.52 | 1.08 | 2.08 | 0.45 | 1.18 |
| Charter | 590 | 598 | 0 | 23 | 23 | 74 | 0.65 | 0.65 | 1.03 | 1.58 | 0.61 | 1.15 |
| Times | 691 | 636 | -10 | -12 | 14 | 78 | 0.34 | 0.53 | 0.53 | 1.58 | 0.46 | 1.28 |
| Baskerville | 775 | 710 | -16 | 18 | 11 | 74 | 0.35 | 0.35 | 1.34 | 3.84 | 0.25 | 1.23 |
| Hoefler | 853 | 696 | -22 | 12 | 3 | 90 | 0.41 | 0.47 | 0.53 | 1.30 | 0.41 | 1.36 |
| Palatino | 704 | 632 | -16 | 22 | 31 | 74 | 0.41 | 0.54 | 0.60 | 1.47 | 0.47 | 1.28 |

**N -- Bold** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | thin/H | diag run/H |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 705 | 630 | -1 | 42 | 41 | 102 | 0.82 | 0.82 | 0.84 | 1.02 | 0.73 | 1.18 |
| Georgia | 722 | 614 | -4 | 12 | 8 | 142 | 0.36 | 0.36 | 0.40 | 1.12 | 0.33 | 1.23 |
| Charter | 602 | 592 | 0 | 23 | 15 | 109 | 0.59 | 0.59 | 1.01 | 1.71 | 0.55 | 1.12 |
| Times | 642 | 622 | -14 | 14 | 22 | 128 | 0.19 | 0.26 | 0.27 | 1.46 | 0.22 | 1.25 |
| Baskerville | 786 | 710 | -12 | 24 | 27 | 172 | 0.39 | 0.39 | 1.07 | 2.70 | 0.36 | 1.37 |
| Hoefler | 820 | 670 | -18 | 36 | 0 | 165 | 0.32 | 0.35 | 1.11 | 3.44 | 0.30 | 1.31 |
| Palatino | 696 | 622 | -12 | 35 | 27 | 112 | 0.35 | 0.46 | 0.51 | 1.46 | 0.40 | 1.31 |

**T -- Bold** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | bar/stem | w/cap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 596 | 630 | -1 | 30 | 31 | 102 | 0.62 | 0.62 | 1.13 | 1.81 | 0.55 | 0.95 |
| Georgia | 594 | 614 | 0 | 6 | 5 | 142 | 0.27 | 1.08 | 1.08 | 3.95 | 0.28 | 0.97 |
| Charter | 508 | 592 | 0 | 14 | 9 | 109 | 0.46 | 1.10 | 1.10 | 2.40 | 0.42 | 0.86 |
| Times | 558 | 622 | 0 | 34 | 34 | 128 | 0.28 | 1.17 | 1.17 | 4.17 | 0.26 | 0.90 |
| Baskerville | 710 | 710 | 0 | 29 | 32 | 172 | 0.74 | 1.08 | 1.08 | 1.46 | 0.35 | 1.00 |
| Hoefler | 722 | 678 | -5 | 14 | 15 | 165 | 0.31 | 1.16 | 1.16 | 3.74 | 0.42 | 1.06 |
| Palatino | 570 | 622 | 0 | 20 | 16 | 112 | 0.48 | 1.14 | 1.14 | 2.40 | 0.42 | 0.92 |

**y -- Italic** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | y-p | tail@-.3/n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 416 | 421 | -304 | -89 | 105 | 68 | 0.50 | 0.55 | 1.07 | 2.13 | -35 | 0.61 |
| Georgia It | 432 | 428 | -190 | -60 | 119 | 80 | 0.49 | 1.01 | 1.01 | 2.07 | 0.00 | 0.92 |
| Charter It | 444 | 429 | -192 | -93 | 69 | 72 | 0.57 | 0.83 | 0.87 | 1.54 | 1.00 | 0.90 |
| Palatino It | 417 | 428 | -248 | -68 | 100 | 68 | 0.33 | 0.77 | 0.98 | 3.01 | -1.50 | 0.61 |
| Flanker | 422 | 429 | -326 | -60 | 80 | 79 | 0.27 | 0.44 | 0.77 | 2.90 | 0.00 | 0.27 |
| Poetica | 388 | 429 | -288 | -86 | 52 | 63 | 0.41 | 0.85 | 1.04 | 2.52 | 2.50 | 0.80 |
| Pagella | 416 | 429 | -246 | -68 | 97 | 70 | 0.29 | 0.73 | 0.97 | 3.30 | 0.00 | 0.54 |

**y -- BoldItalic** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | y-p | tail@-.3/n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 430 | 420 | -312 | -100 | 102 | 95 | 0.46 | 0.51 | 1.02 | 2.20 | -50 | 0.56 |
| Georgia BI | 527 | 424 | -188 | -66 | 118 | 140 | 0.33 | 1.00 | 1.00 | 3.01 | 0.00 | 0.84 |
| Charter BI | 460 | 428 | -188 | -86 | 55 | 106 | 0.48 | 0.63 | 0.90 | 1.87 | 2.00 | 1.78 |
| Palatino BI | 456 | 430 | -246 | -60 | 107 | 104 | 0.26 | 0.81 | 0.95 | 3.57 | 0.00 | 0.22 |
| Flanker B | 450 | 429 | -313 | -72 | 75 | 120 | 0.52 | 0.75 | 0.77 | 1.49 | 0.00 | 0.53 |
| Times BI | 407 | 429 | -205 | -90 | 103 | 128 | 0.24 | 0.81 | 0.85 | 3.57 | -2.00 | 0.37 |
| Hoefler BI | 480 | 429 | -262 | -82 | 103 | 163 | 0.34 | 0.61 | 0.83 | 2.45 | -13.00 | 0.54 |

**j -- Italic** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | j/i | t/i | f/i |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 298 | 580 | -278 | -182 | 100 | 68 | 0.66 | 1.10 | 1.14 | 1.74 | 1.34 | 1.27 | 1.27 |
| Georgia It | 254 | 650 | -190 | -117 | 118 | 80 | 0.69 | 1.01 | 1.01 | 1.46 | 1.02 | 1.03 | 1.02 |
| Charter It | 202 | 620 | -191 | -85 | 120 | 72 | 0.79 | 0.94 | 0.95 | 1.20 | 0.96 | 0.99 | 0.94 |
| Palatino It | 160 | 636 | -248 | -36 | 126 | 68 | 0.62 | 0.87 | 0.93 | 1.50 | 1.03 | 0.99 | 1.01 |
| Flanker | 303 | 656 | -336 | -200 | 118 | 79 | 0.82 | 0.89 | 0.89 | 1.08 | 1.00 | 0.99 | 0.99 |
| Poetica | 282 | 652 | -288 | -156 | 69 | 63 | 0.51 | 0.97 | 0.98 | 1.91 | 1.11 | 1.04 | 1.10 |
| Pagella | 163 | 596 | -246 | -36 | 119 | 70 | 0.59 | 0.84 | 0.87 | 1.49 | 0.98 | 0.95 | 0.94 |

**j -- BoldItalic** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | j/i | t/i | f/i |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 314 | 587 | -278 | -174 | 97 | 95 | 0.63 | 1.06 | 1.07 | 1.70 | 1.06 | 1.02 | 1.01 |
| Georgia BI | 336 | 654 | -188 | -137 | 116 | 140 | 0.85 | 1.00 | 1.00 | 1.18 | 1.01 | 1.01 | 1.02 |
| Charter BI | 248 | 628 | -186 | -104 | 113 | 106 | 0.81 | 0.96 | 0.98 | 1.21 | 0.99 | 1.00 | 0.97 |
| Palatino BI | 208 | 630 | -250 | -35 | 128 | 104 | 0.44 | 0.88 | 0.95 | 2.19 | 0.99 | 0.99 | 1.01 |
| Flanker B | 335 | 646 | -322 | -212 | 107 | 120 | 0.84 | 0.93 | 0.93 | 1.11 | 1.00 | 1.00 | 1.00 |
| Times BI | 244 | 642 | -205 | -109 | 128 | 128 | 0.76 | 0.91 | 0.92 | 1.20 | 1.01 | 1.00 | 1.03 |
| Hoefler BI | 432 | 677 | -262 | -223 | 117 | 163 | 0.29 | 0.91 | 0.93 | 3.25 | 1.03 | 1.03 | 1.01 |

**r -- BoldItalic** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | arm reach/n | root/n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 328 | 408 | -1 | -28 | 84 | 95 | 0.46 | 1.01 | 1.05 | 2.31 | 1.65 | 0.87 |
| Georgia BI | 460 | 429 | 0 | -68 | 69 | 140 | 1.00 | 1.00 | 1.00 | 1.00 | 1.52 | 0.37 |
| Charter BI | 375 | 428 | 0 | -51 | 65 | 106 | 0.87 | 0.98 | 1.00 | 1.15 | 1.84 | 0.55 |
| Palatino BI | 338 | 431 | -14 | -50 | 63 | 104 | 0.26 | 0.87 | 0.92 | 3.49 | 1.38 | 0.79 |
| Flanker B | 414 | 429 | 0 | -93 | 56 | 120 | 0.42 | 0.94 | 1.09 | 2.59 | 1.80 | 0.97 |
| Times BI | 338 | 429 | 0 | -60 | 91 | 128 | 0.20 | 0.77 | 0.88 | 4.40 | 1.18 | 0.79 |
| Hoefler BI | 455 | 429 | -8 | -68 | 53 | 163 | 0.20 | 0.40 | 0.95 | 4.78 | 1.35 | 0.58 |

**V -- BoldItalic** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | rise/fall | fall/n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 734 | 630 | -22 | -77 | 101 | 95 | 0.69 | 0.77 | 1.08 | 1.58 | 0.64 | 1.17 |
| Georgia BI | 704 | 600 | -7 | -79 | 34 | 140 | 0.35 | 1.00 | 1.00 | 2.85 | 0.37 | 1.08 |
| Charter BI | 572 | 582 | -3 | -86 | 49 | 106 | 0.59 | 0.75 | 0.95 | 1.61 | 0.64 | 1.00 |
| Palatino BI | 614 | 619 | -4 | -74 | 63 | 104 | 0.30 | 0.47 | 1.03 | 3.47 | 0.44 | 1.09 |
| Flanker B | 864 | 700 | -9 | -62 | 94 | 120 | 0.34 | 0.72 | 1.11 | 3.25 | 0.65 | 1.20 |
| Times BI | 623 | 628 | -14 | -67 | 76 | 128 | 0.19 | 0.30 | 1.03 | 5.31 | 0.32 | 1.06 |
| Hoefler BI | 729 | 648 | -20 | -62 | 61 | 163 | 0.29 | 0.37 | 1.09 | 3.74 | 0.37 | 1.13 |

**W -- BoldItalic** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | rise/fall | fall/n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 936 | 633 | -24 | -53 | 85 | 95 | 0.67 | 1.11 | 1.14 | 1.69 | 0.60 | 1.16 |
| Georgia BI | 1008 | 600 | -7 | -68 | 35 | 140 | 0.34 | 1.00 | 1.02 | 3.01 | 0.35 | 1.07 |
| Charter BI | 806 | 582 | 0 | -72 | 64 | 106 | 0.57 | 0.88 | 0.94 | 1.64 | 0.64 | 0.98 |
| Palatino BI | 908 | 619 | -8 | -69 | 67 | 104 | 0.30 | 0.98 | 1.02 | 3.42 | 0.42 | 1.07 |
| Flanker B | 1158 | 700 | -9 | -60 | 100 | 120 | 0.34 | 0.72 | 1.11 | 3.25 | nan | nan |
| Times BI | 828 | 628 | -14 | -62 | 77 | 128 | 0.16 | 0.30 | 1.02 | 6.41 | 0.31 | 1.04 |
| Hoefler BI | 1062 | 648 | -20 | -66 | 65 | 163 | 0.32 | 0.37 | 1.01 | 3.15 | nan | nan |

**F -- Italic** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | top bar/stem | mid bar/stem | top arm/stem |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 328 | 635 | -1 | 33 | 95 | 68 | 0.59 | 1.01 | 1.04 | 1.75 | 0.68 | 0.59 | 3.23 |
| Georgia It | 477 | 608 | 0 | -16 | 65 | 80 | 0.40 | 1.14 | 1.16 | 2.88 | 0.34 | 0.50 | 3.27 |
| Charter It | 400 | 592 | 0 | -42 | 90 | 72 | 0.57 | 1.08 | 1.13 | 1.98 | 0.52 | 0.52 | 3.16 |
| Palatino It | 415 | 624 | 0 | -39 | 124 | 68 | 0.41 | 0.56 | 1.02 | 2.46 | 0.50 | 0.51 | 3.08 |
| Flanker | 518 | 700 | 0 | -42 | 129 | 79 | 0.44 | 1.18 | 1.19 | 2.69 | 0.38 | 0.38 | 3.22 |
| Poetica | 369 | 558 | -4 | 2 | 72 | 63 | 0.43 | 0.81 | 1.05 | 2.44 | 0.47 | 0.54 | 2.81 |
| Pagella | 414 | 616 | -3 | -44 | 125 | 70 | 0.36 | 0.56 | 1.00 | 2.80 | 0.52 | 0.54 | 3.12 |

**q -- BoldItalic** (poor_trace units, xh 429)

| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | lsb/n | rsb/n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Albo today | 474 | 414 | -262 | 2 | -50 | 95 | 0.52 | 1.02 | 1.18 | 2.26 | 0.03 | -0.53 |
| Georgia BI | 543 | 429 | -188 | -14 | 34 | 140 | 0.29 | 1.00 | 1.00 | 3.41 | -0.10 | 0.24 |
| Charter BI | 475 | 431 | -190 | -14 | 26 | 106 | 0.42 | 0.97 | 0.99 | 2.36 | -0.13 | 0.25 |
| Palatino BI | 366 | 430 | -246 | 8 | 112 | 104 | 0.33 | 0.91 | 0.95 | 2.88 | 0.07 | 1.08 |
| Flanker B | 448 | 429 | -313 | -28 | 78 | 120 | 0.71 | 0.93 | 0.93 | 1.32 | -0.23 | 0.65 |
| Times BI | 438 | 429 | -203 | -24 | 59 | 128 | 0.19 | 0.87 | 0.90 | 4.63 | -0.19 | 0.46 |
| Hoefler BI | 470 | 433 | -249 | -13 | 85 | 163 | 0.30 | 0.88 | 0.96 | 3.15 | -0.08 | 0.52 |

## 4. Reference sheets

`instruments/poor_refsheet.py --albo <build> --out DIR` -- one PNG per
character and cut, Albo round 409 first, then each reference of that cut, in
three bands: (1) reader size -- each face sized so its x-height equals Albo's
at 54 ppem, FreeType unhinted, the converter's 2-bit levels, native pixels;
(2) the same at 3x nearest; (3) drawing size -- unsheared at x-height 429
(143 px), one baseline, the baseline and x-height ruled. Seventeen sheets were
rendered from round 409 into the session scratchpad
`poorchars/refsheets/index.html` (not published); the tool regenerates them.

The per-arm word proofs (today above each arm, two words from his books at
54 px, the letter at 3x) are `instruments/poor_proof.py`, rendered to
`poorchars/proof/index.html`.

## 5. The render + gate harness

- `tools/wedge_serif/instruments/poor_harness/` -- `arm.sh` (build an arm
  from `git archive HEAD` plus the working glyph files, any env), `score.sh`
  (fit audit on one build: geometry, OCR legibility, F per cut, against a
  baseline tag), `redo.sh` (rebuild and rescore several arms, clearing their
  caches), `thinmap.py` and `ridgemap.py` (where the audit's p10 and p50 live
  on the letter), `cmpref.py` (a sub-axis against its family in every face).
  Its README carries the environment and two traps: tags are directory names
  on a case-insensitive disk (`t_pal` and `T_pal` are one directory -- it
  clobbered an arm here), and word-list loops need bash, not zsh.
- `instruments/poor_gates.sh BASE_DIR ARM_DIR "cuts"` -- every gate on an arm
  against its base, printing only deltas: moved glyphs, contour hairs
  `--letters` and full, cmp_touch, counter dents (700s), the glitch sweep on
  the moved letters, the contour census, approved.py, the unhinted e gate.
  `gates.sh` builds only the default font, so it cannot see an arm. It refuses
  an arm directory with no fonts (a zsh loop that did not split its list
  gated nothing and printed "no delta" before that line existed).
- `instruments/poor_pairs.py TODAY.ttf ARM.ttf --char c` -- the white on a
  letter's commonest corpus pairs as set (band, closest approach, whole-extent
  box), arm minus today; B2 is not refit.
- `instruments/poor_trace.py c --cut Cut --albo L=DIR --sheet out.png` --
  a letter's rows and ridge in every reference, one baseline.

## 6. The arms drawn before the ruling (record; default-off)

Every value below is a dial whose default is today. F is the fit metric,
today -> arm, per cut (roman arms against round 405, italic against round
409). "Gate" is poor_gates against the baseline. These are measurements of
what each construction does, NOT proposals.

| character | dial = value : what it draws | F today -> arm | gate |
|---|---|---|---|
| roman y | `ALBO_ROM_Y_TAIL` geo: tail straight 55% of the depth, tight hook up-left into the c's finial (Georgia/Charter) | 3.06/3.75 -> 0.95/0.37 | clean |
| | hoe: straight 68%, lower hook (Hoefler/Baskerville) | -> 0.66/0.57 | clean |
| | pal: straight 73%, short turn, square tip x1.15 (Palatino) | -> 0.72/0.95 | clean |
| | alb: no hook, flared chisel on the p's line (original, Albertus) | -> 1.50/0.99 | clean |
| | flr: today's path, floor 0.50 S (original) | -> 0.10/0.80 | clean |
| | (all arms at floor 0.50 S; round 391's ladder was 0.30/0.33/0.36) | | |
| roman t | `ALBO_ROM_T_OPT` pal: left arm a 0.35 S spur, pen-cut end | 2.77/3.09 -> 3.06/0.83 | clean |
| | hoe: bar tapered 0.75->1.10, right end cut | -> 3.18/0.80 | clean |
| | alb: bar at the arch hair 0.70 S, both ends cut, tail floor 0.50 (original) | -> 2.77/0.72 | clean |
| | wdg: hanging wedge left end (original) | -> 3.24/1.74 | st ligature reversal; dropped |
| roman j | `ALBO_ROM_J_OPT` geo -110 / pal -95 square / hoe -95 swell / fin -98 finial | 3.70/1.69 -> 3.69-3.85 / 1.52-2.17 (spacing is fixed; F cannot fall) | clean (fin at -102 set `(j` under the touch floor; -98 clears) |
| roman s | `ALBO_ROM_S_ARM` geo: floor 0.97 x the o's hair / pal: 0.85 / bwl: on the bowl profile (original) | 2.56/0.64 -> 0.55/0.79, 0.59/0.70, 0.54/0.70 | clean |
| roman N | `ALBO_ROM_N_OPT` cha: stems 0.57 CW / pal: 0.42 / wgt: x sqrt(66.9/S), 400 untouched (original) | 0.54/2.51 -> 0.14/0.37, 1.84/1.23, 0.54/0.09 | clean |
| roman T | `ALBO_ROM_T_BAR_K` 0.76, 700 only (Charter/Palatino bar/stem) | Bold 3.12 -> 0.82 (1.30 also clears: the p50 edge) | clean |
| italic j, t | `ALBO_ALD_JT_OPT` trc: stems = the i's / nib: x 0.92 (original) | j 4.17 -> 2.48, 2.84; t 2.60 -> 0.30, 1.08 | clean |
| italic y | `ALBO_ALD_Y_OPT` trc: ink bottom on the p / flb: trc + 700 hairline x1.25 / swa: trc, swash to x 60 (original; partly overrides the 2026-09-16 swash ruling) / chn: no swash (dropped) | 1.44/2.32 -> 0.79/2.11, 0.79/1.45, 0.75/1.90, 1.57/5.20 | trc, flb: **4y touches** in the BoldItalic (-0.0196 em); swa clean |
| italic r | `ALBO_ALD_R_OPT` geo: heavier root / fla: root higher / arc: the n's shoulder (original) | BI 3.59 -> 4.94, 2.11, 6.73 | clean |
| italic V, W | `ALBO_ALD_VW_OPT` (700 only) cha: hairline x0.68 / pal: x0.45 / wgt: x sqrt(66.9/S) / cap: wgt + falling x0.80 (original, round 272's rule) | V 1.96 -> 0.33, 2.01, 0.67, 1.15; W 1.93 -> 2.68, 1.44, 2.67, 0.53 | clean |
| italic F | `ALBO_IT_F_OPT` cha: bars x0.80 / geo: top x0.55, middle x0.78 / mod: modulated (original) | 5.04 -> 4.60, 5.03, 4.68 (BI 0.48 -> 1.37, 1.23, 2.74) | clean |

Pair white (poor_pairs, B2 unchanged): most arms move their commonest pairs
0-3 units. The exceptions: roman t pal -26 on at / it (the wrong way; he
wants +10 on the t's left); roman t alb +8 left, -3 right (both toward his
bench); every roman j arm +16 to +46 of box gap before the j (the white the
B2 kern had been buying); italic t trc +6 to +8; italic y +5 to +93 of box
gap (the swash tucks less). Scratchpad `poorchars/pairs/`.

## 7. The three passes, as run

1. **Pass 1** -- refreshed the list (round 405), traced each character in the
   six references of its cut, drew traced and original arms, scored them.
2. **Pass 2** -- every arm through F and every gate; changed: the roman y's
   arms put on one floor (the traced hooks alone had not moved p10: any hook
   turning left crosses the pen's thin) and their depths set against each
   reference's OWN p; the t's bar ends cut (square ends were the Bold flag)
   and hoe's left end back to square (ct ligature reversal); wdg dropped (st
   ligature reversal, weakest); the j's fin sweep eased (`(j` touch); T gated
   to the 700 (Regular legibility cost); the italic y's depths refit
   (overshoot), chn dropped, swa added; the italic r's raised arms withdrawn
   (a normalisation artefact, below); V/W cap added (the W's median); the F's
   arms rebuilt on round 409 (the first build was on a preview and moved 130
   glyphs -- the gate caught it). The italic half was re-baselined on round 409
   when it landed.
3. **Pass 3** -- one read-only adversarial review was launched on the two arm
   commits before the ruling arrived; it could not be stopped. Its findings
   are in section 10. Under the ruling nothing is redrawn on them.

## 8. What the fit metric cannot see, learned here

- **p10 on a short letter is corner spokes.** Bold t, BoldItalic r, partly
  Bold T: the ridge's p10 lands on the spokes a sharp corner leaves, so a
  "cut" flag moves with corner geometry, not stroke weight. Check with
  `thinmap.py` before drawing to a cut flag.
- **p50 on a two-population letter flips.** T, F, W: the median sits between
  bar/hairline and stem/thick; moving either side clears or worsens it. Check
  with `ridgemap.py`.
- **A family-wide change creates outsiders.** Round 409 thinned the italic
  stem family; j, t and F became outliers untouched.
- **|e| penalises better legibility too.** An arm that made the Regular t MORE
  legible than its family (legibility -3.0) scored worse for it.
- **poor_trace's Albo heights read ~6% low.** It scales every face by its x's
  top, and Albo's x carries ~28 units of wedge; pass 1 "raised" the italic r's
  arm to fix a gap that was this normalisation. Use the fit audit's lines, or
  scale Albo by 429 directly, for vertical claims.
- **Spacing-led flags cannot be moved by a drawing in this metric** (axis f
  reads the B2 tables at a fixed commit); judge them on the pair white.

## 9. Checked and found CLEAN

- Unset = today, all four cuts, outlines and advances, at both arm commits.
- Every arm moves only its letter plus that letter's composites and
  ligatures (cmp_outlines --verbose), except the F arms' first build (stale,
  rebuilt) and the roman T dial in the Regular (moves nothing, by design).
- Contour census unchanged for every arm (no re-cut of later glyphs).
- approved.py 2/2 and the unhinted e gate unchanged for every arm.
- Counter dents at the 700s unchanged for every arm.
- Glitch sweep: 0 findings on every moved letter, every arm.
- Contour hairs `--letters` and full: no new row except t hoe pass 1 (ct) and
  t wdg (st), both resolved as above.
- Touching: no new pair except roman j fin pass 1 (`(j`, resolved) and italic
  y trc/flb (`4y`, open).
- **Leak check, every dial set at once.** All six roman dials set together
  leave the Italic IDENTICAL; all five italic dials set together leave the
  Regular and the Bold IDENTICAL. The one leak it found: `ALBO_ROM_T_BAR_K`
  also reached the **BoldItalic T** (the aldine T borrows the roman `g_T`
  and the dial was gated on S > 84 only). Fixed in this doc's commit -- the
  dial is now `not pen.ITALIC` as well; BoldItalic identical, the Bold T arm
  unchanged. (Default builds were never affected.)

## 10. Pass 3: adversarial review

One read-only agent rebuilt all 35 arms from `39dc1b8` and tried to refute each.
It reported after the ruling, so NOTHING WAS REDRAWN on it; the findings stand
here as the record for whoever draws. Confirmed findings, most severe first:

1. **`ALBO_ROM_T_BAR_K` leaked into the BoldItalic T** (the aldine T is
   `_CS.g_T`). Found independently by this pass's leak check and FIXED in
   `b637b7c` (`not pen.ITALIC`).
2. **Italic y `trc` / `flb` fail cmp_touch in BOTH italics:** `4y` -0.0196 em
   (BoldItalic) and `qy` 0.0070 em (Italic, under the 0.012 floor). Only `4y`
   was recorded above; `swa` is clean.
3. **The roman j arms were scored with today's kerns into j still in the font**
   (aj +23, ej +26, oj +32, nj +22, ij +27), so the proofs double-correct; the
   arms cannot be judged until those kerns are refit. `hoe` also reintroduces a
   teardrop end that round 275 retired, unlabeled.
4. **Italic r:** the aldine comment "the path is today's in every arm since
   pass 2" is FALSE for geo/fla (their second and third knots sit at 0.60 /
   0.80 xh against today's 0.55 / 0.745); the fla gain is corner-spoke noise
   (p10 26.4 / 25.3 / 31.3 in base / geo / fla).
5. **Roman y:** every arm overrides round 391's 0.33 floor (0.50), so the
   skeletons are confounded with the floor -- `flr` alone gives Regular 0.10;
   `pal` and `alb` also drop round 275's finial on the tail. Unlabeled in the
   code.
6. **`s_bwl`:** the spine gets ~25% lighter (vertical run 53 -> 40 at the
   centre), so "nothing about the spine moves" is false for that arm; its
   premise "hair 0.70 S" is stale (0.46 since round 265). Measured s/o hair
   0.70 (the comment says 0.64).
7. **Roman t comments:** `hoe` cuts only the right end (the stems.py header
   was corrected in pass 2 but the pass-2 note "every arm cuts its ends" is
   false for hoe's left and pal's right).
8. **`vw_cap`:** the W's middle-apex spur (present today) stands further out,
   with a notch under it, because the crown's offset is not rescaled with the
   hairline; the glitch sweep does not see it. Lower confidence.
9. **`poor_gates.sh` compares counts and names only:** a touching pair that
   clears while another starts, or a second hair in a glyph that already had
   one, passes. Latent.
10. **`_VW_HAIR` in `a_W` is not reset in a try/finally.** Latent: an exception
   aborts the build rather than leaking.

Its verdicts, for the record: KEEP t_alb (Bold), s_geo, s_pal, N_cha, N_wgt,
jt_trc (jt_nib as the alternative), yi_swa, vw_cap; FIX (labels / refit)
roman y arms, t_pal, t_hoe, s_bwl, yi_trc, yi_flb, the roman j arms; DROP
t_wdg, j hoe / fin, N_pal, ri_geo, ri_arc, ri_fla (or relabel as metric
noise), vw_cha, vw_wgt, vw_pal, Fit_geo, Fit_mod; Fit_cha weak.

Checked CLEAN by the review: unset = today in all four cuts, plain and with
`FJORD_ADJ=all`; cross-style leaks (only finding 1); per-arm scope (letter +
its own composites/ligatures); the `cdiag` hairline test picks exactly the
thin arms of V and W and never runs for A N X M; VW_OPT inert at the 400; no
self-intersecting contour in any arm's letter (so no fold in the roman y's
hook); the italic F microserif stays attached; the italic y depths as
stated; the j reach numbers; the S interpolation ends; census, approved and
e-mouth gates unchanged everywhere.

The stale code comments in findings 4, 6 and 7 are NOT corrected in the code:
`aldine.py` is being edited by another agent (round 410 draft), and the
ruling stops arm work; they are corrected here.

## Files

- Dials: `outlines/glyphs/diagonals.py` (Y_TAIL), `stems.py` (T_OPT, J_OPT,
  S_ARM), `caps_straight.py` (N_OPT, T_BAR_K, IT_F_OPT), `aldine.py` (JT_OPT,
  Y_OPT, R_OPT, VW_OPT).
- Instruments: `instruments/poor_trace.py`, `poor_tables.py`,
  `poor_refsheet.py`, `poor_proof.py`, `poor_pairs.py`, `poor_gates.sh`,
  `poor_harness/`.
- Scratchpad (session, not published): `poorchars/refsheets/`,
  `poorchars/proof/`, `poorchars/fit-*.json`, `summary.txt`, `gates/`, `pairs/`.

## 11. Owner rulings, 2026-09-26 (roman y)

- *"for y, i do not see a difference"* — the four tail arms (geo at 0.33 and 0.50, hoe, alb) are sub-visible at reading size in both cuts. None ships; a y tail change must be large enough to see at 54 px before it is offered again.
- *"bold y needs to have a baseline cutout on the left stroke like regular"* — the Regular y shows a cut/notch where the left diagonal meets the tail at the baseline; the Bold y has none. A defect to fix in the Bold (see its construction in `diagonals.py` g_y and the Bold-only behavior).

## Roman s, visible arms (2026-09-26, after "always show me")

The first arms (geo / pal / ARM_K 1.3) only moved the hairline, 4-9 units --
invisible at 54 px, recorded as a negative result. Redrawn so each is visible
at reading size, `ALBO_ROM_S_ARM` (default `a`, today):

| arm | what | gates (Regular, Bold) |
|---|---|---|
| evn | traced, both halves of the finding: the o's hairline (0.97) AND the spine capped at 0.82 of the pen's max (`ALBO_ROM_S_EVEN_CAP`) | touch 0, hairs 0 |
| opn | original: 8% wider (`ALBO_ROM_S_OPEN_W`), upper bowl let out to 0.97 (`ALBO_ROM_S_OPEN_UP`) | touch 0, hairs 0 |
| bek | original, Albertus: a wedge beak on each end face, 0.13 xh (`ALBO_ROM_S_BEAK`) | touch 0, hairs 0 |

Built from the round 413 tree; sheet in the session scratchpad `rs/s.png`.

## N and T widths (2026-09-26, owner: "give me options with ideal widths for N and T")

Ink width over the H's and over the O's, six references (Georgia Charter Times Baskerville Hoefler Palatino, medians) against round 414:

| | refs /H | Albo /H | refs /O | Albo /O |
|---|---|---|---|---|
| N Regular | 1.015 | 1.018 | 1.080 | 1.136 |
| N Bold | 0.967 | 1.015 | 1.022 | 1.133 |
| T Regular | 0.841 | 0.863 | 0.888 | 0.963 |
| T Bold | 0.816 | 0.857 | 0.874 | 0.957 |

The N is on the H in the Regular and 5% wide in the Bold; the T is 2.5% / 5% wide. Against the O every one is 5-10% wide, which is the O being narrow (capital-widths doc), not the N or T alone.

A width scale applied in `g_N`/`g_T` does NOTHING (measured: 1.018 -> 1.015 at x0.93) because `solve_widths` re-solves each capital's ink to its reference target; the dial is `CAP_NT_WIDTH` on that target in `build.py` (`ALBO_ROM_N_W`, `_N_W_BOLD`, `ALBO_ROM_T_W`, `_T_W_BOLD`; 1.0 = today; roman only). Arms, all touch 0 / hairs 0:

- **vs H**: N 1.0 / 0.953, T 0.975 / 0.952 -> N/H 1.018 / 0.971, T/H 0.841 / 0.816 (on the medians)
- **vs O**: N 0.951 / 0.902, T 0.922 / 0.913 -> N/O 1.083 / 1.030, T/O 0.887 / 0.875
- **vs H + strokes**: vs H plus `ALBO_ROM_N_OPT=cha` and Bold `ALBO_ROM_T_BAR_K=0.76`

## Bold Italic V and W: ruled today (2026-09-27)

Owner: *"for V W bold italic, today seem okay, just use something close to A strokes"*. Measured on the ridge (`tools/wedge_serif/instruments/stroke_ridge.py`: 2 x the distance transform at its 3x3 local maxima, unhinted, 1000 ppem), round 418 BoldItalic:

| glyph | light (p10) | heavy (p90) |
|---|---|---|
| A | 66.6 | 120.1 |
| V (today) | 64.9 | 120.8 |
| W (today) | 64.4 | 122.8 |

Today's V and W are already within 3% of the A on both strokes (under 0.1 px at reading size), so today IS "close to A strokes" and nothing changes. The arms drawn for the poor-characters pass all move away from the A: cha 44.9 / 120.8, pal 30.0 / 120.8, wgt 49.4 / 121.3, cap 49.4 / 97.3 (V). `ALBO_ALD_VW_OPT` stays `a`.

## Roman t: defects found, fixed behind a dial, and four arms (2026-09-27, after round 419)

The last roman items on the list were the t (Regular spacing, Bold contrast)
and the j. Read at 300 px on round 419's build (`2e12e80`), the t carries two
CONSTRUCTION defects that no gate flags (contour hairs, glitch and touch all
pass on today):

1. **A 15-unit hair on the Bold's cut top.** `stem(cut_top=)` moves only the
   LAST right-edge point down to the cut line. The cut drops that corner by
   tan(20) x w / 2 = 22 units at the 700 (13 at the 400), and the entasis
   samples above the line stay, so the edge climbs to y 539 and falls back to
   520: points (194,524) (196,539) (197,539) (199,520). The 400's drop is under
   the sample spacing, so the Regular has none. Verified against the built
   outline. Other `cut_top` users were not audited here [open].
2. **An 8-unit bump inside the Bold's tail join.** The tail's centerline turns
   tighter than half its width (radius ~45 against a 55 half-width at the 700),
   so its inner offset folds back on itself (x 201 -> 210 -> 206 -> 211 over
   y 104..58) and `_unfold` leaves the lump: x 200 at y 75 against the stem's
   192. The Regular's offset edge is lumpy all along the turn for the same
   reason, and its outer edge has a chord corner at (118,55)-(135,29).

**Fix, `ALBO_ROM_T_CLEAN=1` (default 0 = today, outline- and advance-identical,
checked):** the stem is clipped by its cut's own half-plane; the tail starts at
the stem's width (R20's flush join, on `smooth_widths`), and BOTH tail edges are
redrawn as one cubic each from the stem's edge (vertical) to the terminal's
corner (along the tail's end direction), each solved so its lowest point is the
offset's own (counter depth and overshoot unchanged).

Three cheaper fixes were tried first and failed, recorded so they are not
retried: capping the tail's width at the stem's over its first quarter (the
cap's release at t=0.25 made a width jump, a new corner in the Regular);
replacing only the folded stretch of the inner edge with a quarter-round landing
at the offset's lowest point (the offset is still folded there in the 400: a
dent); landing it past the fold with the direction taken from neighbours
(the neighbours are folded: a straight chord then a flat).

**Arms** (`ALBO_ROM_T_END` a / fin / lng, `ALBO_ROM_T_BAR` a / cut / spr, both
only under T_CLEAN), page https://claude.ai/artifact/VEN7vtKzb9neeXxkzYJVpz:

| label | env | what |
|---|---|---|
| A | (none) | today |
| T1 | CLEAN=1 | defects fixed, today's shape |
| T2 | + END=fin | tail ends in the c's finial (round 275's family end) |
| T3 | + END=lng | tail 12% further right, end at 0.50 r instead of 0.60 r |
| T4 | + END=fin BAR=cut | T2, both bar ends on the pen cut |
| T5 | + END=fin BAR=spr | T2, left arm a 0.35 S spur (Palatino), ends cut |

Gates (`poor_gates.sh` against today, Regular + Bold): all five arms touch 0,
hairs `--letters` and full no delta, glitch 0, counter dents unchanged, e gate
ok. Moved: t, tbar, uniE004 (ct), uniFB06 (st), plus tcaron, uni0163, uni021B
under T2-T5. B2 not refit. Awaiting a pick.

**Ruled 2026-09-27: T5** (*"t5 wins"*), round 420.

## Roman a height (2026-09-27, owner: *"is 'a' too short though? show me comparisons"*)

Measured on round 419 + T5 (font units, unhinted bboxes; `ameas.py`-style
bbox read, session scratchpad). Albo's x carries ~22 units of wedge over the
line (bbox 451 Regular), so Albo is compared against its own o, not the x.

| face | a top / o top | ink width a / o |
|---|---|---|
| Albo Regular | 433 / 444 (-11) | 0.830 |
| Albo Bold | 438 / 444 (-6) | 0.799 |
| Georgia, Charter, Hoefler, Baskerville, Big Caslon | equal | 0.96, 0.96, 0.89, 0.99, 0.92 |
| Palatino | 0.995 | 0.91 |
| Georgia Bold, Charter Bold, Palatino Bold | equal, equal, 0.987 | 0.97, 0.97, 0.92 |

(An earlier reading in this session gave Charter Bold 1.10: that was
Charter.ttc index 2, the Bold ITALIC. The Bold is index 3.)

Dials (`stems.py`, default = today): `ALBO_ROM_A_RISE` / `_RISE_700` add to
the hood arc's two inner controls (crown rises ~0.8 / ~0.7 of it; 14 and 8
land the crown on 444); `ALBO_ROM_A_W` scales the a's leftward reach (hood
end, bowl left and bottom). Arms, all gates clean:

| label | env | a top | a/o width |
|---|---|---|---|
| A | -- | 433 / 438 | 0.830 / 0.799 |
| H1 | RISE 14, RISE_700 8 | 444 / 444 | same |
| H2 | H1 + W 1.08 | 444 / 444 | 0.882 / 0.847 |
| H3 | H1 + W 1.15 | 444 / 444 | 0.931 / 0.889 |

Awaiting a pick.

**Ruled 2026-09-27: A, as is** (*"as is, next"*). The a keeps its height and width; the dials stay default-off as the record.

## Roman j: the head and the hook, shown (2026-09-27, after round 420)

Read at 300 px on round 420 (`r420` build): the roman j's top is a flat cut
(`g_j`, "no top flag", rounds 22/25) where its i carries the family's left
wedge head; Georgia, Charter, Palatino and Hoefler (both weights) head their
j exactly as their i. The hook reaches 82 units left of the origin (Georgia
66, Charter 70; section 2) and ends in a 0.10 S blade.

New dial `ALBO_ROM_J_TOP=1` (default 0 = today, outline-identical, checked):
the roman j takes the i's head, `stem(top='left')`. It reverses the round-25
drawing, so it is offered, not fixed. Arms, page
https://claude.ai/artifact/4zPBXG8mUMnwE5tyyqmz5B:

| label | env |
|---|---|
| A | today |
| J1 | J_OPT=fin (arc to -98, c finial) |
| J2 | J1 + J_TOP=1 |
| J3 | J_OPT=hoe (teardrop) |
| J4 | J_OPT=pal (short, square tip) |
| J5 | J_TOP=1 alone |

Gates (poor_gates vs r420, Regular + Bold): all touch 0, hairs no delta,
glitch 0. At 54 px the head reads and widens the j's left side (J2 and J5 set
wider); the hook arms are subtle at 54 px and clear at drawing size. The
finial and teardrop ends (J1-J3) leave the tip pointing down-left -- flagged on
the page. B2 not refit. Awaiting a pick.

**Owner 2026-09-27: *"J2 but give me more variations on tail"*.** The tail
generalised (`stems.py` `J_K`, `ALBO_ROM_J_OPT=k1..k8`): an elliptical arc
(x / y radius factors, bottom held at -0.97 desc), sweep, end width, end type
(c finial / square face / pen cut / taper), finial swell. `k1` reproduces J2
byte-for-byte (checked). All with `ALBO_ROM_J_TOP=1`. Shown (same page, v2):
J2, K2 square face, K4 tucked, K5 straight drop, K6 wide sweep, K8 curl on the
pen cut. Cut before showing: k3 (-112 finial, reads as J2 with a blockier end)
and k7 (heavy square end, reads as K2). Measured: K6 and K8 put `(j` at
0.0115 / 0.0101 em, under cmp_touch's 0.012 floor (not touching) -- a
clearance kern if either wins. Seen at 300 px on the Bold: every sheared
finial end (J2, K5, K6) leaves a small upward point at the face's inner corner;
the square faces and the pen-cut curl do not. Awaiting a pick.

**Ruled 2026-09-27: K8 with J2's head** (*"K8 next"*), round 421.
