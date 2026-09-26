# Albo: carrying the 400 spacing answers to every weight (2026-09-26)

Owner, 2026-09-26: *"interpolated based on my answers what changes would be
applicable to all of albo fonts (thin, black, italic, bold italic, etc)"*.

This is an **architecture choice for the owner**. It lays out four options, all
measured. **No shipped default changed.** Every arm was built in scratch by
post-processing TTFs built from HEAD. Nothing under `tools/wedge_serif/outlines/`
was edited.

- **Surveyed:** HEAD `3b02bed` (round 396, B2 the default spacing). The build
  of HEAD was checked against `bench/fonts-2026-09-26-r396/` with
  `cmp_outlines --advances` and is IDENTICAL.
- **Units:** font units (1000 per em). "White" is `rsb + kern + lsb`, with the
  kern read by HarfBuzz with ligatures off (`gap_measure.py`'s measure, the one
  B2 is fitted against).
- **Tags:** each claim is marked **[measured]**, **[repo]** (read from a file,
  with file:line) or **[inf]** (inferred, not measured).
- **Proof page:** https://claude.ai/artifact/36H7WJUVHoQujtZsmXYRhb
- **Instruments:** `tools/wedge_serif/weights_transfer/`:
  - `common.py`
  - `refs_weight.py` → `refs_weight.txt`
  - `vs400.py` → `vs400.txt`
  - `transfer.py`
  - `measure.py` → `measure.txt`
  - `render.py`
  - `census-bigrams.json` (the `pair_census.py` output these read)

## 0. The answer

| arm | what it does | Bold 700 moves | Bold Italic 700 moves | gates | evidence for it |
|---|---|---|---|---|---|
| **a. units (today)** | the 400's correction is added as the same number of units at every weight | 0 | 0 | clean on the four shipped cuts | the references keep text white roughly level across weights, and so does Albo (§3) |
| b. stem-scaled | correction × stem_W / stem_400 | 7.02 mean, 37 max, 66% of text pairs ≥ 4 | 4.28 mean, **9 pairs under the 0.012 em floor** | **fails** on the Bold Italic | contradicted by 21 reference cuts: white does not follow the stem |
| c. rhythm (counter) | correction × the n's counter ratio (Tracy's control) | 0.60 mean (×0.92) | 1.94 mean (×0.74) | clean | the references' white shrinks toward the counter ratio (median ×0.91 against a counter ×0.77) |
| d. B2 on each cut | the B2 model re-measured on each cut's own shapes; kerns re-derived | 1.50 mean, +0.49 looser | 3.78 mean, **+3.52 looser** | clean | none at those weights; it extrapolates a model fitted on one weight |

Moves are census-weighted mean |Δwhite| against today, over the pairs in his own
books seen at least 50 times. **[measured]**

**Recommendation: keep arm a (units), do not adopt b, and treat c and d as
questions that need his eye on the Bold rather than as fits.**

- **Arm b is ruled out on two counts.** The references contradict it, and it
  puts nine Bold Italic pairs under the 0.012 em floor.
- **Arm c changes almost nothing on the roman** (0.6 units on average, max 5).
  On the italic it trims his corrections by a quarter.
- **Arm d is the only arm that changes the kerns by shape,** but it loosens the
  Bold Italic by 3.5 units on average. No answer at 700 supports that.
- **What this cannot settle is the Bold Italic** (§2b). Its white already
  differs from the Italic's by a standard deviation of 10.5 units per pair,
  before any arm moves. That is his own repeatability (10.83). Of the four
  styles, it is the only one where the 400's answers do not in effect reach
  the page.
- **The cheapest decisive next step is one active-bench session on the Bold
  Italic,** using the pairs where arms a and d disagree most as its
  candidates. His answers there choose between a and d on data rather than on
  doctrine. **[inf]**

## 1. Inventory: what Albo can build today

**[repo]** unless marked otherwise.

| cut | stem (`FJORD_STEM`) | env | status |
|---|---|---|---|
| **Regular 400** | 66.9 | `FJORD_CONTRAST=0.892` (width 100, cut default) | ships; `build_env.sh` `ALBO_ROM_ENV` |
| **Italic 400** | 66.9 | `ALBO_ITALIC=aldine FJORD_CONTRAST=0.80 FJORD_WIDTH=95 FJORD_SLANT=13` | ships; `ALBO_ITA_ENV` |
| **Bold 700** | 116 | `FJORD_SLANT=0 FJORD_CONTRAST=0.80 FJORD_WIDTH=95 FJORD_CUT=0` | ships; `ALBO_BLD_ENV` |
| **BoldItalic 700** | 116 | aldine, slant 13, contrast 0.80, width 95, cut 0 | ships; `ALBO_BIT_ENV` |
| ExtraLight 200 | 43.8 | the Bold's env at stem 43.8, `--style ExtraLight` | **buildable, not shipped**; family cut per the 2026-09-19 ruling ("only test and ship 200 400 700 900"), no reader slot; recipe in `albo_dial_grid.py:10,21-24` |
| Black 900 | 148 | the Bold's env at stem 148, `--style Black` | **buildable, not shipped**, same ruling |
| 100 / 300 / 500 / 600 / 800 | — | the stem axis still takes any value | **out of scope by ruling** (`docs/albo-family-2026-09-19.md`, "the family is FOUR weights") |
| italic 200 / 900 | — | — | **out of scope by ruling** ("italic is just 400 and 700") |
| variable font | — | `outlines/variable.py` still exists | **retired 2026-09-14** (static 400 + kern + liga) |

So there is no Thin and no italic Black. The owner's "thin, black" maps to the
200 and the 900 in roman. All six cuts were built from a HEAD snapshot in about
2 s each. **[measured]**

Two facts that matter for any transfer:

1. **The roman 400 is not on the other roman cuts' axes.** It is built at
   width 100 and contrast 0.892. The 200, 700 and 900 are built at width 95 and
   contrast 0.80. So "the 400 → the 700" is a stem change plus a width change
   plus a contrast change, not a pure weight step. **[repo]**
   - Measured, the ExtraLight's n counter (236 units) is *smaller* than the
     Regular's (254), although its stem is thinner. **[measured]**
2. **The reader's installed TTFs are not HEAD.**
   `~/src/crosspoint-reader/lib/EpdFont/local_fonts/Albo/*.ttf`, dated
   2026-09-26 12:21, differ from the HEAD build in 88 outlines and 106
   advances. This is most likely round 397 in progress by the agent that owns
   `outlines/`. **[inf, not investigated]** Everything here is measured
   against HEAD.

## 2. Today's propagation

### 2a. The mechanism [repo]

- **Roman lowercase and marks.** `SPACING_FIT` defaults to `b2`
  (`outlines/build.py:529`), which loads `spacing_b2.json` into `ROM_LC_ADJ`
  and `ROM_PUNCT_FIT` (`build.py:530-541`). `fit()` then adds them to each
  glyph's bearings with **no weight term** (`build.py:1018-1019`).
- **The base bearing does not depend on the weight either.**
  `capbear = REF["Hbear"]/2 * C * pen.WIDTH` (`build.py:990`) follows the width
  axis but not `pen.S`, the stem (`pen.py:42`).
- **Italic.** `ALD_LC_ADJ` is folded into `ALD_BEARING_ADJ` (`build.py:692-694`)
  and added to the fixed `ALD.BEARINGS` table in `fit_aldine`
  (`build.py:753-755`). The same holds: units, no weight term.
- **Kerns.** B2's kerns are added to what each pair carries, for every cut of a
  style (`outlines/kern.py:621-635`). So are the holds (`kern.py:862-869`).
- **The only weight-aware spacing** is a set of clearance kerns gated on
  `pen.S > 84` (`kern.py:738`, `753`, `759`, `846`, `877`). These are the
  Bold Italic's q pairs, the Bold's QQ, and the B2 + Bold Italic `qj`. **None
  of them is a spacing judgment.** The comment at `kern.py:720-726` says so
  outright: *"The bench's bearings are fitted on the 400 and applied at every
  weight, so a bearing that is right there can be wrong at stem 116."*

**Confirmed on the built fonts [measured].** B2 against the `bench` arm moves
the `e` by −2 in advance and −7 in lsb, and the `o` by −7 and −6. The
movement is identical at the Regular and the Bold, and every composite
(`eacute`, `odieresis`) follows its base.

### 2b. What that does to the white, cut by cut [measured]

Measured on today's HEAD cuts against the 400 of their style (`vs400.py`),
census-weighted over the text pairs in his books seen at least 50 times.

| cut vs its 400 | bbox white Δ mean / sd | pairs off by ≥ 10 | x-band row gap Δ mean / sd | 2-D closest approach Δ mean / sd |
|---|---|---|---|---|
| ExtraLight 200 | −2.0 / 1.4 | 0.0% | −11.6 / 9.6 | −6.1 / 6.2 |
| Bold 700 | −2.2 / 2.2 | 1.9% | −15.2 / 18.3 | −2.6 / 7.4 |
| Black 900 | −2.2 / 2.9 | 1.9% | −19.1 / 27.4 | −1.7 / 10.1 |
| **BoldItalic 700** | −0.8 / **10.5** | **24.7%** | −6.0 / 9.0 | −0.1 / 8.5 |

The ink columns come from `local_ai/features.py` and cover 336 lowercase pairs
seen at least 300 times.

What this shows:

- **The roman bearings do carry his answers to the 200/700/900 almost
  exactly.**
  - The bbox white is within 2 units, except for two things, both of which are
    drawings rather than transfers:
    - the f pairs (`fo fi fr fe` +11 at 700, +15 at 900), and
    - the j pairs (`bj ej aj oj` +31..+49), from the Bold's redrawn j head
      (round 393).
  - What *does* change at weight is the INK inside the gap. The x-band row gap
    closes by 15 units at 700 and 19 at 900, concentrated in `c e s t`:
    - at 700: `ct` −74, `es` −59, `et` −59, `rs` −65, `st` −51;
    - at 900: `ct` −107, `es` −91.
  - Their open terminals fill in as the stem grows. By
    `docs/albo-spacing-method.md`'s rule, that open white belongs to the
    letter, not to the gap. **[inf]**
- **The Bold Italic does NOT carry them.** The units are the same, but a
  quarter of the text pairs sit 10 or more units away from the Italic's white.
  The largest are the s pairs: `as` +27, `us` +28, `ns` +24, `is` +21, `es` +18.
  - `qu` −90 is the bbox reading the Bold Italic q's foot. On ink it is the
    weight-gated clearance, not a gap.
  - The cause is the letter drawings: round 269 evened the Bold Italic
    letter by letter. `fit_aldine` reads a band extreme off a different shape
    and then adds the same table to it. **[inf]**

## 3. What real families do [measured]

`refs_weight.py` measures each cut against its own family's regular (or
italic), over 10 serif families on this Mac: Palatino, Baskerville, Charter,
Iowan Old Style, Georgia, Times, Cochin, Hoefler Text, Superclarendon and
TeX Gyre Pagella. That gives 15 roman and 6 italic comparisons. Each cut is
measured as:

- the n's stem and counter at mid x-height;
- the n's mean sidebearing;
- the census-weighted white over the 120 commonest lowercase pairs in his
  books.

Each value is divided by the cut's own x-height. The full table is in
`refs_weight.txt`.

| | stem ratio | counter ratio | white ratio | white per unit of stem growth |
|---|---|---|---|---|
| references, roman (median of 15) | ×1.60 | ×0.77 | **×0.91** | −0.068 (range −0.42 .. +0.44) |
| references, italic (median of 6) | ×1.54 | ×0.80 | **×0.96** | −0.040 |
| Albo Bold / Regular | ×1.68 | ×0.90 | ×0.95 | −0.095 |
| Albo Black / Regular | ×2.10 | ×0.89 | ×0.94 | −0.076 |
| Albo BoldItalic / Italic | ×1.52 | ×0.72 | ×0.96 | −0.076 |

- **White does not grow with the stem in real families.** In the median
  family it stays level or tightens a little.
  - Only Palatino and Pagella (the same design) loosen their bolds: ×1.28 and
    ×1.38.
  - Superclarendon holds the white constant to three decimals across Light,
    Regular, Bold and Black, which is exactly what Albo's fitting does.
- **Albo's total white already sits in the reference band** at every weight.
  So the question is only how his *corrections* should scale. The base does
  not need re-fitting for weight.

**Sources for the practice.**

- **Tracy, *Letters of Credit* (1986), p. 72.** The lowercase control is the
  n, and its starting sidebearing is half the space between its stems. The
  method is repeated for the H. This is the basis of arm c. Via the
  description in F. de Mello Vargas, *Approaches to applying spacing methods
  in seriffed and sans-serif typeface designs*, MA essay, Reading, 2007, §3.2.1
  (https://typeculture.com/wp-content/uploads/2016/02/tc_article_49.pdf), and
  https://github.com/n8willis/kernall/blob/master/tracy.md.
- **W. A. Dwiggins,** quoted in Vargas (2007): *"there is certainly a 'right'
  interval for a given weight and height of stem, varying as these dimensions
  vary."* This is the premise of arm b, stated as a hunch, not a rule.
- **HT Letterspacer.** Its Area, Depth and Overshoot are per-master custom
  parameters, with an "Interpolate parameters" action between masters
  (README, https://github.com/huertatipografica/HTLetterspacer). So the tool
  treats a weight as its own fitting problem rather than as a scaled copy.
- **Multiple-master practice (Glyphs, Adobe MM).** Sidebearings and kerning
  are set per master and interpolated linearly between masters. **[inf,
  general practice; no document quoted]** Albo's retired VF did this. The
  static cuts now take the 400's numbers in units instead.

## 4. The arms, plainly

C400 is what his answers put on the 400, read from HEAD's `spacing_b2.json`:

- the B2 lowercase and mark SIDES (identity bearings; the g is held at round
  340 and excluded);
- the B2 KERNS;
- on the held pairs: the holds plus his own post-bench kerns from rounds
  388-390, transcribed into `transfer.py` `EXPLICIT`.

Clearance kerns (`fT QQ q' q" qj`, the Bold Italic `qu`) are not his answers
and are never scaled.

How the arms are built:

- **Post-processing.** Each arm post-processes **today's built cut**
  (`transfer.py apply`):
  - A side delta translates the outline and changes the advance.
  - Composites follow their base and keep their marks in place.
  - Roman `fi ffi fl ffl` ride the i/l's right side, as the builder does.
  - Kern deltas go in one extra PairPos lookup under `kern`.
- **Check [measured]:** the Bold under arm b has **0 non-rigid glyphs**. Every
  outline only translates, so the contour-hair and counter-dent gates are
  invariant under every arm.

| arm | the rule | multiplier used [measured] |
|---|---|---|
| a. units | C_W = C400 | 1 |
| b. stem | C_W = C400 × stem_W / stem_400 | 200: 0.672 · 700: 1.719 · 900: 2.172 · BI 700: 1.565 |
| c. rhythm | C_W = C400 × counter_W / counter_400 (the n) | 200: 0.929 · 700: 0.921 · 900: 0.921 · BI 700: 0.743 |
| d. B2 per cut | kern_W = b2_fit's kern with each pair's 38 shape features re-measured on cut W | per pair |

**Arm c in plain words.** His correction is read as a fraction of the space
inside the letters. The Bold Italic's n has 26% less space inside, so it gets
26% less correction.

**Arm d in plain words.** B2 says each pair's correction is:

- a fixed preference of each glyph (identity terms, kept in units), plus
- a function of how the pair looks (shape features).

At the Bold the pair looks different, so the shape half is recomputed.

**How arm d was computed:**

- **The difference is evaluated, not absolute features.** It uses
  `shift = term(features on cut W) − term(features on the 400)`. Both cuts
  carry the same unit corrections, so a uniform shift cancels.
- **Kerns are re-derived with b2_fit.py's own rules:**
  `round(predict + shift − bearings)`, the 4-unit floor, and holds untouched.
- **Check.** The refit reproduced the shipped model: in-sample 7.71 roman and
  6.61 italic, identical to `spacing_b2.json`. It used all answers at HEAD,
  including session 2. **[measured]**
- **Caveat.** The features at 200, 700 and 900 lie outside the range the
  model was fitted on. At the ExtraLight it loosens by +2.84 on average,
  which nothing supports. **[inf]**

## 5. Measurements [measured]

### 5a. Moves against today and the touch gate

`cmp_touch.py` was run from the HEAD snapshot, default floor 0.012 em. The
first column is census-weighted mean |Δwhite| against today, in units.

| cut | arm | mean abs Δ | mean Δ | max | pairs ≥ 4 | touching / under the floor |
|---|---|---|---|---|---|---|
| ExtraLight | today | — | — | — | — | 0 / 1 (`VI` +0.0017 em) |
| ExtraLight | b | 3.23 | −0.88 | 17 | 37.8% | 0 / 1 (same) |
| ExtraLight | c | 0.54 | −0.03 | 4 | 0.1% | 0 / 1 (same) |
| ExtraLight | d | 3.05 | +2.84 | 11 | 50.0% | 0 / 1 (same) |
| Bold | today | — | — | — | — | 0 / 0 |
| Bold | b | 7.02 | +1.68 | 37 | 65.8% | 0 / 0 |
| Bold | c | 0.60 | −0.08 | 5 | 0.2% | 0 / 0 |
| Bold | d | 1.50 | +0.49 | 11 | 23.2% | 0 / 0 |
| Black | today | — | — | — | — | **1 / 1 (`QQ` −0.0040 em, touching)** |
| Black | b | 11.53 | +2.62 | 61 | 77.7% | 1 / 1 (same) |
| Black | c | 0.60 | −0.08 | 5 | 0.2% | 1 / 1 (same) |
| Black | d | 2.45 | +0.78 | 16 | 30.7% | 1 / 1 (same) |
| BoldItalic | today | — | — | — | — | 0 / 0 |
| BoldItalic | b | 4.28 | +1.36 | 23 | 48.0% | **0 / 9** (`qu` .0063, `qC` .0079, `qQ` .0093, `qj` .0101, …) |
| BoldItalic | c | 1.94 | −0.49 | 11 | 12.9% | 0 / 0 |
| BoldItalic | d | 3.78 | +3.52 | 13 | 58.0% | 0 / 0 |

Both 400s move 0.00 under every arm, by construction. Arm d changes 425 kern
glyph-pairs at the Bold, 601 at the Bold Italic, 482 at the 200 and 465 at the
900.

### 5b. The pairs he corrected most

The white in units under today / b / c / d. The full grid, with carrier words,
is on the proof page. The first eight are the pairs the brief named; the rest
rank highest by |his mean| × √readings.

| roman | 200 | 400 | 700 | 900 |
|---|---|---|---|---|
| um | 116/122/117/121 | 118 | 116/102/117/115 | 116/95/117/115 |
| ks | 108/114/109/109 | 110 | 108/95/109/110 | 108/86/109/111 |
| sw | 110/109/110/110 | 112 | 110/111/110/110 | 109/112/109/105 |
| bj | −48/−61/−51/−46 | −44 | −12/14/−15/−15 | 5/47/2/0 |
| aj | −43/−52/−46/−39 | −37 | −6/13/−9/−7 | 10/40/7/7 |
| ej | −43/−57/−46/−42 | −39 | −7/23/−10/−9 | 9/57/6/7 |
| he | 81/81/81/86 | 83 | 81/80/81/77 | 81/80/81/77 |
| sp | 97/96/97/99 | 99 | 97/99/97/96 | 96/100/96/90 |
| ed | 111/100/109/111 | 112 | 110/134/108/110 | 110/149/108/110 |
| ec | 113/101/111/113 | 114 | 112/138/109/112 | 112/154/109/112 |
| hy | 42/54/44/42 | 44 | 42/17/44/42 | 42/1/44/42 |

| italic | 400 | 700 |
|---|---|---|
| ks | 50 | 73/60/80/71 |
| sw | 91 | 88/93/86/91 |
| he | 95 | 94/93/93/100 |
| sp | −43 | −28/−18/−32/−26 |
| yo | 71 | 70/84/64/72 |
| ur | 94 | 97/110/91/100 |
| ee | 91 | 83/75/86/89 |
| je | 33 | 14/27/8/17 |
| et | 105 | 86/77/91/92 |

- **Arm b's stem multiplier turns his largest answers into jumps of 25-45
  units at the 900.** For example, `ec` goes from 112 to 154 and `hy` from 42
  to 1.
- **At the Bold Italic, today's white already departs from the Italic's** on
  `ks` (+23), `je` (−19) and `et` (−19). This is §2b's drawing difference,
  which no arm addresses.

## 6. Checked and found CLEAN [measured]

- **Contour hairs.** `cmp_contour_hairs.py --letters` passes on all six of
  today's cuts, including the unshipped 200 and 900 (52 glyphs each, 0
  findings). The arms only translate outlines (0 non-rigid glyphs), so they
  cannot change this.
- **Counter dents.** `cmp_counter_dents.py` finds 0 dents at 700, 900 and
  Bold Italic 700, today against arm d. The owner's ruling that "counters
  should not have indentations" at 700/900 still holds today.
- **Touch gate on the four shipped cuts.** Today: 0 touching and 0 under the
  floor. Arms c and d stay at 0 / 0.
- **The B2 refit** reproduced the shipped in-sample errors exactly.
- **The composite handling** keeps accents on their base: `eacute` and
  `odieresis` move exactly with `e` and `o`.

**Found NOT clean, and pre-existing:** the two unshipped cuts, neither of
which any gate covers today:

- the **Black's `QQ` touches** (−0.0040 em). The round-384 +4 for stem > 84 is
  sized to the Bold's tail;
- the **ExtraLight's `VI`** is under the floor (+0.0017 em).

Both are the same under every arm. They matter only if the 200 and 900 ever
ship.

## 7. How to re-run

```
V=<venv with numpy scipy sklearn uharfbuzz fonttools freetype-py pillow>
# six cuts from a clean HEAD snapshot (never the live outlines/ tree mid-round)
git archive HEAD tools/wedge_serif | tar -x -C $SNAP
# envs: build_env.sh for the four; 200 / 900 = the Bold's env at FJORD_STEM 43.8 / 148
cd tools/wedge_serif/weights_transfer
$V/bin/python refs_weight.py  TODAY_DIR          > refs_weight.txt
$V/bin/python vs400.py        TODAY_DIR          > vs400.txt
$V/bin/python transfer.py     TODAY_DIR FONTS_DIR   # writes b-stem/ c-rhythm/ d-b2/
$V/bin/python measure.py      FONTS_DIR $SNAP/tools/wedge_serif > measure.txt
$V/bin/python render.py       FONTS_DIR OUT_DIR
```

`FONTS_DIR/today` must hold the six HEAD cuts. `transfer.py` needs the
`local_ai/` modules (`b2_fit.py`, `features.py`) and reads `spacing_b2.json`
from git HEAD.
