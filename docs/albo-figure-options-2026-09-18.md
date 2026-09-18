# Albo's numerals, remade as OPTIONS — 2026-09-18

Owner, 2026-09-18: *"improve both 7s"*; *"redo all numerals to fit together and
read well in long numbers"*; *"subagent to remake numerals based on reference
fonts that have old style figures and give me multiple options for each to
choose from."*

Nothing here is shipped. Every dial defaults to **today's drawing** and both
styles build **byte-identical** at the defaults — 470 glyphs, outlines and
hmtx, against the round-225 italic and against a same-tree control for the
roman. The owner chooses; a winner then ships by changing one letter in
`FIG_SHIP_ROM` / `FIG_SHIP_IT` in
[tools/wedge_serif/outlines/glyphs/figures.py](../tools/wedge_serif/outlines/glyphs/figures.py)
and nothing else.

**Everything in this file is measured.** The per-digit detail, the ladders and
the negative results live beside the code they belong to, in `figures.py`; this
is the map and the reference table.

---

## 1. How to drive it

```bash
cd tools/wedge_serif
# one digit
ALBO_FIG_7=c ALBO_ITALIC=aldine FJORD_SLANT=13 FJORD_CONTRAST=0.80 \
  FJORD_WIDTH=95 FJORD_CUT=0 PYTHON_GIL=0 python3 -m outlines.build <dir> --style Italic
# every digit at once, which is how the option sheet is built
ALBO_FIG_SET=b FJORD_SLANT=0 FJORD_CONTRAST=0.80 FJORD_WIDTH=95 FJORD_CUT=0 \
  PYTHON_GIL=0 python3 -m outlines.build <dir> --style Medium
```

`ALBO_FIG_0` … `ALBO_FIG_9` take `a|b|c|d`, read once at import; `ALBO_FIG_SET`
sets all ten. An unknown letter falls back to `a` rather than raising, so a
typo in a sheet script cannot silently build a third thing.

**The option letter means a different thing in each style, deliberately.** The
roman's 7 and the italic's 7 are not the same problem: the italic's carries
five of the owner's own rulings from rounds 211–219 and every option keeps all
five, while the roman's has never been touched.

---

## 2. The references, measured at ONE x-height (429 units)

Which faces on this machine actually carry old-style figures, found by
rendering `0123456789` and testing whether 3 4 5 7 9 descend and 6 8 ascend:

| face | how it is reached | verdict |
|---|---|---|
| **Flanker Griffo Italic** | `onum` feature | old-style, and **TABULAR** — all ten advances are 513 |
| **TeX Gyre Pagella Italic** | `onum` | old-style |
| **Poetica Std Regular** | default | old-style |
| **Coelacanth Italic** | default | old-style |
| **Georgia**, **Georgia Italic** | default | old-style |
| **Big Caslon** | default | old-style |
| Hoefler Text, Baskerville | — | **no `onum`, lining only.** Checked and ruled out |

Reached by rewriting each font's cmap for `0`–`9` to its `onum` glyphs
(`mk_osf.py` in the round's scratch dir), so every existing instrument measures
the old-style set by codepoint.

### 2a. Advance as a ratio of the 0's — what makes a long number read evenly

| d | Flanker | Pagella | Poetica | Coelacanth | Georgia | Georgia it | Big Caslon | **median¹** | Albo rom | Albo it |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| 1 | 1.000 | 0.919 | 0.778 | 0.736 | 0.700 | 0.700 | 0.593 | **0.736** | 0.623 | **0.552** |
| 2 | 1.000 | 0.970 | 0.944 | 0.885 | 0.910 | 0.910 | 0.818 | 0.910 | 0.909 | 0.907 |
| 3 | 1.000 | 0.933 | 0.845 | 0.771 | 0.899 | 0.899 | 0.743 | 0.872 | 0.826 | 0.861 |
| 4 | 1.000 | 1.065 | 1.050 | 0.920 | 0.920 | 0.920 | 1.034 | 0.985 | 0.925 | 0.855 |
| 5 | 1.000 | 0.899 | 0.778 | 0.720 | 0.861 | 0.861 | 0.737 | **0.820** | **0.911** | **0.941** |
| 6 | 1.000 | 0.951 | 0.994 | 0.986 | 0.922 | 0.922 | 0.961 | 0.956 | 0.978 | 1.006 |
| 7 | 1.000 | 0.968 | 0.863 | 0.835 | 0.819 | 0.809 | 0.833 | 0.834 | 0.824 | 0.842 |
| 8 | 1.000 | 0.917 | 0.977 | 0.917 | 0.971 | 0.971 | 0.912 | 0.944 | 0.976 | 0.954 |
| 9 | 1.000 | 0.957 | 0.959 | 0.940 | 0.922 | 0.922 | 0.961 | 0.950 | 0.992 | **1.044** |

¹ median of the six NON-tabular faces. Albo's outliers are the **1** (far too
narrow, worst in the italic), the **5** (too wide in both) and the **9** (too
wide, worst in the italic).

### 2b. Height, cut and stroke

| face | 8's top ÷ x-height | 8 against its own 6 | 0's cut | 8's cut | 7's cut |
|---|---|---|---|---|---|
| Flanker | 1.45 | 620 / 644 | 2.91 | 2.78 | 1.28 |
| Pagella | 1.45 | 622 / 622 | 2.45 | 2.05 | 1.76 |
| Poetica | 1.31 | 562 / 562 | 2.65 | 2.75 | 2.38 |
| Coelacanth | 1.53 | 657 / 656 | 2.33 | 2.31 | 2.25 |
| Georgia | 1.48 | 633 / 633 | 3.07 | 2.38 | 2.06 |
| Big Caslon | 1.54 | 659 / 660 | 1.23 | 5.29 | 4.25 |
| **Albo roman** | **1.21** | **520 / 617** | **1.54** | **1.52** | **1.37** |
| **Albo italic** | **1.31** | **561 / 639** | 2.12 | **1.31** | 1.62 |

**Three findings, and they are the whole brief in numbers.**

1. **The 8 is short.** Every reference tops its 8 on its 6's line. Albo's roman
   8 is **97 units short of its own 6** and stands 1.21 x-heights where the
   references run 1.31–1.54. In a run like `1889` the 8s sit in a dip. This is
   also the owner's own ruling of 2026-09-13 (round 64, *"make it shorter so
   counters can match other numerals or optical circles"*), so it is offered,
   not shipped.
2. **The roman is flat.** Its 0 cuts 1.54 and its 8 1.52 where the references
   run 2.05–3.07; its 7 is the flattest glyph in the style.
3. **Six of the ten figures are stuck on the width solver's clamp.**
   `build.solve_widths` aims each figure's ink at `round20.REF[ch]['w'] × CAP ×
   WIDTH` and clamps the multiplier at 0.70. Built ÷ target, roman:

   | d | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
   |---|---|---|---|---|---|---|---|---|---|---|
   | built/target | 1.007 | 1.201² | 1.031 | **1.156** | 1.002 | **1.206** | 1.034 | 0.999 | **1.124** | 1.065 |

   ² the 1 is deliberately skipped by the solver, so its drawn width IS its
   built width.

   The 5 is **+20.6%** over the width the face already declares for it, the 3
   +15.6%, the 8 +12.4%. Only the drawn width can take those the rest of the
   way, which is what options `3b`, `5c` and `5d` do.

   **But the solver's targets are not the old-style faces' proportions**, and
   that matters for the 3: measured against the seven references, Albo's 3/0
   ink ratio (0.886) is already NARROWER than five of them. So `3b` is
   grounded in the solver and NOT in the references, and it is not recommended.
   Recorded so the next pass does not re-derive it.

---

## 3. The options

`a` is today's drawing in both styles, always.

| d | b | c | d |
|---|---|---|---|
| **0** | more cut (`con` 1.90 roman / 2.55 italic) — Georgia and Flanker run 2.9–3.1 | that cut **plus an oblique axis** (`stress` −26° / −46°) — Poetica, Coelacanth | a **squarer ring** (`k` 2.55) — Georgia's |
| **1** | the flag reaches further left | a broader flag, starting lower on the stem (0.635 D) | — |
| **2** | a long, heavy, flat base — Georgia's (`base_w` 1.50, overhang 26, arc lighter) | a thin arc into a full-width diagonal over a heavier base — Poetica, Coelacanth | — |
| **3** | narrower (`W` 282), onto the solver's target — **see the caveat above** | a **wider upper bowl** (`top_rx` 0.545), the two bowls more alike — Georgia, Big Caslon | — |
| **4** | the weight put back evenly | a thin diagonal against a thick stem and bar — Poetica, Coelacanth, and the file's own standing todo from round 75 | — |
| **5** | a shorter top flag (inset −78 against −24) | narrower (`W` 338), onto target | both |
| **6** | **the 9 turned through 180°** — Georgia and Big Caslon draw the pair as rotations | a bigger bowl and a shorter tail | — |
| **7** rom | heavier tapering bar over a thinner leg — Georgia's | **Flanker's**: heavier bar still, and the leg tapers along its own run | weight brought to the figure family |
| **7** it | MORE modulation (bar to 0.42, leg thinning from 0.45) | LESS, for a steadier column | heavier — answers the 7's COLOUR, which round 212 said a stroke match cannot |
| **8** | **taller, onto the 6's line** | more cut | both |
| **9** | a shorter tail reach (3 units past the bowl against 12.4) | a bigger bowl (0.325 of the height against 0.29) | both |

### 3a. The 6 as the 9 rotated

The one option in this round that is a construction and not a dial. Measured:
Georgia's 6 and 9 have the same ink width (423) and the same advance (504); Big
Caslon's are 417 and 464. Albo's are 379/462 roman and 447/536 italic — two
separate drawings that have drifted apart, so in `1969` the 6 and the 9 do not
look like each other. The arm builds `g_nine` at the 6's own figure height,
turns it about its bbox centre and lands it on the default 6's left and bottom.
Two consequences, both named rather than discovered: the 6 then takes the 9's
solved width multiplier (which is what makes the two equal, and leaves `W['6']`
inert), and the 9's terminal comes with it — the roman's wedge flag ends up at
the top right of the 6.

---

## 4. The recommended sets, and their numbers

**These are recommendations, not defaults.** `FIG_SHIP_ROM` and `FIG_SHIP_IT`
are all `a`.

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| **R1 roman** | b | b | a | c | c | d | c | d | d | d |
| **I1 italic** | b | b | a | a | b | d | a | c | d | d |

| measure | roman today | **R1** | italic today | **I1** |
|---|---|---|---|---|
| advance spread (max ÷ min of adv ÷ 0) | 1.60× | **1.44×** | 1.89× | 1.82× |
| …excluding the 1 | 1.21× | 1.22× — **unchanged, and honestly so**⁴ | 1.24× | **1.21×** |
| stroke, min–max ÷ the figures' median | 0.75–1.23 | **0.84–1.11** | 0.76–1.21 | 0.83–1.24³ |
| the 7's stroke | 51.9 (−22%) | **65.5 (−10%)** | 65.5 | 69.2 |
| the 7's cut | 1.37 | **1.45** | 1.62 | **1.83** |
| the 7's colour | 0.160 | **0.177** | 0.158 | 0.158 |
| the 8's top, against the 6's | 520 / 617 | **592 / 583** | 561 / 639 | **627 / 639** |
| the 0's cut | 1.54 | **2.37** | 2.12 | **3.18** |
| the 5's ink ÷ its target | 1.206 | **1.063** | — | — |
| `cmp_figure_space --body` spread | 1.53× | 1.52× | 1.31× | **1.26×** |

⁴ **the roman's gain is the 1 and only the 1.** Excluding it, the spread is
1.214× today and 1.217× in R1 — no better. The 5 comes in (0.911 → 0.822,
against a reference median of 0.820) and the 7 goes out with it (0.824 →
0.834), so the two ends trade places. The italic's gain is real on both counts,
because its 9 comes in as well. Stated because the headline 1.60× → 1.44× would
otherwise read as an evenness win across the set when it is a fix to one digit.

³ the italic I1 figure is the **4**, and it is the instrument rather than the
drawing: a 4 has three strokes and its ridge sample is bimodal, so the median
flips between the diagonal (~50) and the stem/bar (~88) on a 3% change in
either. The measure that answers "does the 4 read light" is its COLOUR — today
0.165 against a figure median of 0.184 (−10%), and 0.181 against 0.191 (−5%) in
I1. Use colour for the 4, not the stroke median.

### Gates, every arm and every set

| | glitch (`--ttf`) | `cmp_touch` | `cmp_figure_space --body` | `cmp_aldine_metrics` |
|---|---|---|---|---|
| italic, all arms and sets | 0 of 119 | **0 touching, 0 under the floor** | 1.26–1.31× | 0 outside 10% |
| roman, all arms and sets | 0 of 119 | 4 touching + 14 exempt (**the pre-existing Q pairs; not one added**) | 1.50–1.54× | n/a |

`cmp_aldine_metrics`'s TARGETS are letters only (a e i o u y), so no figure
option can move it; run once and recorded rather than per arm. The 290-glyph
sweep (`--all`) reports the control's own 13 italic and 12 roman pre-existing
findings on every arm — **not one added**, superscripts, subscripts and
fractions included, which is where a figure change would show up next.

### One interaction, named rather than discovered

**In the ITALIC the figures pass through `aldine.py` after `figures.py` does.**
Round 167's hand-cut (`_press`, the owner's *"make italic numerals handcut"*)
re-registers all ten as `_press(figures.g_<name>(c), FIG_HAND[ch])`, and its
cuts are placed as FRACTIONS of the glyph's own bbox. An option that changes a
figure's bounds therefore moves where those cuts land: the taller 8 (`8b`,
`8d`), the shorter tail (`9b`, `9d`) and above all the 6 drawn as the rotated 9
(`6b`), which is handed the 6's press over a 9's shape. Every arm was swept and
looked at and nothing has gone wrong — the cuts are 2 to 3.5 units — but **a
winner among those three wants its `FIG_HAND` row re-checked by eye**, in
`aldine.py`, which was outside this round's partition. The roman does not go
through `_press` at all.

---

## 5. Negative results, and the three instrument traps

Each of these cost a build or a wrong reading, and each is the kind of thing a
later pass would otherwise re-derive.

- **`k` below 2 is a POINTED lens, not a rounder ring.** `ring(k=)` is the
  superellipse exponent and 2.0 is a true ellipse, so `BOWL_K` 2.1 is already
  slightly squared. The first cut of option `0d` used 1.72 to make the 0
  "rounder, like Big Caslon's circle" and produced a lens with points at 12 and
  6 o'clock. Caught on the render, not in the code. **There is no rounder
  available above an ellipse**, so that arm went the other way: 2.55, Georgia's
  squarer ring.
- **The 3's upper bowl cannot be made TALLER.** Its radius sets where its sweep
  ends, and that end has to land on the lower bowl's start (0.41 w, 0.63 D) or
  the two terminals fork and leave a white slit at the waist — which a `top_r`
  of 0.240 duly produced, two visible prongs at 620 px. At that radius the
  ellipse's lowest point is 0.52 D, below the junction, and no sweep angle
  recovers it. The radius is pinned by the junction; the only axis left is
  WIDTH, which is what option `c` moves.
- **A tapered bar must be mitred at its OWN depth.** `x1` is where the
  diagonal's right edge crosses the bar's centreline; with `prof` the bar's
  depth at the mitre is `barw × mod`, so its centreline is higher, where the
  leaning edge is further right. Solved at the full depth the tapered bar stops
  short and leaves a re-entrant step. Measured as the largest rise in the
  rightmost-ink profile at a 900 px x-height: **roman 10 px before, 0 after**.
  The italic does NOT want the correction — its shipped 7 already carries 5 px
  and every option here reads 3 — so the fix is gated on `pen.ITALIC`.
- **A white-gap detector reads ZERO on all eight 7s.** The fault above is a
  re-entrant STEP in the outline, not a hole, and the first instrument written
  for it could not see it. It reported "0 broken rows" on arms whose defect was
  plain in the render. The right measure is monotonicity of the right
  silhouette. (Instrument bug eight in this project's series; same lesson as the
  other seven — validate on a case whose answer you already know, and when the
  number and the picture disagree, the picture wins.)
- **The roman 7's bar has a CLIFF at 1.50, and it is the fitter, not the eye.**
  `_body_edges` reads a glyph's left edge as the 20th percentile of its per-row
  ink extremes. The roman 7's left side is its own open white — the bar's
  underside — so while the bar is shallow that percentile lands on the LEG and
  the fitter gives the 7 a wide left bearing; once the bar is deep enough it
  lands on the BAR and the bearing collapses. Laddered on the tightest figure
  pair, everything else held: 1.28 / 1.36 / 1.42 / 1.45 / **1.48** all read
  0.0934 em; 1.52 and 1.56 read **0.0519**; 1.70 reads 0.0491. Every pair that
  closes is an `x7`. Option `b` stops one step under the cliff; option `c` goes
  past it deliberately, because Flanker's bar is that heavy, and the cost is
  recorded rather than hidden.
- **The italic 1 cannot be widened past about 0.58 of the 0's advance from
  inside `figures.py`.** Same mechanism: the flag occupies only the top ~28% of
  the 1's rows, so at the percentile the 1's left edge is still its stem and
  everything the flag adds is read as pure overhang and absorbed (0.75 of it in
  the italic, 0.45 in the roman). `O1`'s white in em, floor 0.012: 150 (today)
  0.0210 — 158 0.0167 — 162 0.0138 — 172 0.0052 UNDER — 182 −0.0019 TOUCHING.
  The references run 0.700 to 0.778. Reaching them needs the 1's left BEARING
  or a handful of `x1` kerns, and `build.py` and `kern.py` were outside this
  round's partition. **The roman has four times the headroom and takes it:**
  `b` reaches 0.692 and `c` 0.787 with `O1` at 0.0429 and 0.0471.
- **The 2's option `c` did not do what it was named.** "A thin arc for more
  contrast" measured the 2's cut DOWN (roman 1.78 → 1.61, italic 1.72 → 1.32),
  because the 2's thickest ink is the arc and not the base. It only raised the
  cut once the base went UP with the arc coming down (roman 1.93). The italic's
  2 still does not move (1.69) — its contrast is structural, and that is
  recorded rather than chased.
- **Weight and contrast pull opposite ways on the roman 7**, which is round
  215's finding on the italic arriving at the other style. At bar 1.48 and bar
  taper 0.74, laddering the leg: diag 0.58 → stroke 47.4 / cut 1.79 / colour
  0.148; 0.70 → 56.4 / 1.50 / 0.157; 0.82 → 56.4 / 1.29 / 0.165; 0.98 → 65.5 /
  1.24 / 0.177. There is no arm that is both heaviest and most modulated, so
  the three options take different corners of it.

---

## 6. The sheet

Per style, one PNG per digit with its options side by side at a 300 px
x-height and the option letters labelled, plus the long-number lines in each
candidate set at **13 px ×6 NEAREST** and at **40 px**:

    1,234,567,890 · 2026-09-18 · 49,503.77 · $78,703
    1970 1861 1917 2001 · 0123456789

All PNG at native pixels, integer NEAREST where magnified.

## 7. What was NOT done

* **No bearing or kern work.** `build.py` and `kern.py` were outside the
  partition, which is what caps the italic 1 (§5) and what leaves the roman's
  four pre-existing Q collisions alone.
* **The open/curved 4 is not re-offered.** It stands behind `FOUR_OPEN` and the
  owner reverted it on 2026-09-13.
* **The italic 1's shape is not re-opened** — the buried flag and microserif
  (round 75, roman), the curve and its bow (rounds 217–218), the brushed foot
  and the shortened exit (rounds 215, 218). Its options are width and fit only.
* **`cmp_seven_legibility.py` was not run** on the new roman arms. It is the
  right instrument for "does the leg grey out at 13 px" and would sharpen the
  choice between roman `7b`, `7c` and `7d`; the arms were judged on rendered
  long numbers instead.
