# Albo's weight, letter by letter — 2026-09-17

Owner, 2026-09-17: *"do a full survey of all roman and italic letters and
numerals"*, asked in the same breath as *"increase thickness of bottom loop
enough to match visual weight of other letters"*. This is that question asked of
all 124 glyphs at once: **is any letter lighter, heavier or flatter than the
face it belongs to?**

Re-run it with `tools/wedge_serif/cmp_weight_survey.py`, which is the ledger —
the numbers below are its output, not a transcription:

```bash
cd tools/wedge_serif
PYTHON_GIL=0 python3 cmp_weight_survey.py --roman <roman.ttf> --italic <italic.ttf> --tol 0.15
```

## What is measured, and the trap in measuring it

The glyph is rasterised UNSHEARED at a fixed x-height, a chamfer distance
transform is taken over the ink, and the ridge of that transform is the stroke's
centreline; local thickness is twice the distance there. This is the method
`cmp_g_strokes.py` established, including its one rule: **no percentile
threshold on the ridge**, because keeping only the thick samples deletes every
thin stroke from the sample and reports a face as far less contrasted than it is.

    thin      the 10th percentile of thickness along the centreline
    stroke    the median -- what the letter's weight reads as
    thick     the 90th percentile
    contrast  thick / thin, the letter's own cut
    colour    ink over (advance x reference height), IN THE READING BAND

**The first cut of `colour` was wrong and is worth recording.** It divided the
letter's whole ink by (advance × x-height), which reads an `f` at 0.77 and an
`l` at 0.57 against an `o`'s 0.39 — the ascender's ink counted against a box
that stops at the x-height. What sets a word's colour is the band the word is
read in, so the ink is now taken from the baseline up to the reference height
and nothing above or below it counts.

**And grouping by CASE flags shape families rather than faults.** A stem letter's
ridge is almost all stem, so its median IS the stem; a round letter's ridge
includes its thins, so its median sits lower by construction. Grouped by case,
53 of 124 glyphs came out "more than 15% off" — which measures the alphabet, not
the drawing. The tables below group by **construction family** instead, which is
the comparison that means something.

### Roman

| family | n | stroke | contrast | colour | more than 20% off its family |
|---|---|---|---|---|---|
| stem | 29 | 79.0 | 1.95 | 0.308 | — |
| round | 11 | 62.5 | 1.83 | 0.305 | `S`+34% |
| diag | 11 | 61.0 | 1.90 | 0.261 | `X`-38% `x`-26% `A`-22% `V`-22% `Y`+33% `z`+63% |
| figure | 10 | 70.4 | 2.06 | 0.215 | `7`-33% |

### Italic

| family | n | stroke | contrast | colour | more than 20% off its family |
|---|---|---|---|---|---|
| stem | 29 | 66.2 | 2.46 | 0.311 | `p`-24% `T`-22% `P`+22% `H`+23% `E`+30% |
| round | 11 | 53.4 | 2.88 | 0.271 | `e`-31% `O`+24% |
| diag | 11 | 42.1 | 2.81 | 0.260 | `z`-36% `X`-30% `y`-23% `Z`+34% `A`+39% `Y`+92% |
| figure | 10 | 60.6 | 2.82 | 0.214 | `7`-32% `1`+22% |
## The findings, ranked

### 1. The two z's are not the same letter's z

| | thin | stroke | thick | contrast |
|---|---|---|---|---|
| roman `z` | 72.3 | **99.3** | 103.9 | 1.44 |
| italic `z` | 24.1 | **27.1** | 67.7 | 2.81 |

The roman z is the **heaviest lowercase in the face** and very nearly monoline;
the italic z is **the lightest glyph in the face**, 73% lighter than its roman.
Set side by side at 300 px they do not read as one typeface's z, and at 16 px
`zigzag` shows it plainly: the roman z's are the darkest marks in the line and
the italic z's fall out of it.

It is not a bug in either drawing — it is the pen model behaving consistently.
The z's main stroke is a diagonal, and at the roman's nib angle that diagonal
runs across the nib (thick) while at the italic's it runs along it (thin). The
fault is that nothing arbitrates between them, and 27 units at a 429 x-height is
about one pixel at 16 px.

### 2. The italic runs 16% lighter than the roman, and unevenly

Median across the 62 letters: the italic's stroke is **−16%** against the
roman's. That much is ordinary — an italic is a lighter, quicker hand. The
spread is not: `z` −73%, `y` −47%, `w` −43%, `T` −43%, `4` −37%, `f` −36% at one
end, and `A` **+24%**, `N` +10%, `Z` +9% at the other. Two letters (`M`, `O`)
match exactly.

### 3. The italic's diagonals are its weak family

Family stroke medians, italic: stem 66.2, round 53.4, **diag 42.1**, figure
60.6. The diagonals are 36% under the stems and carry the widest spread in the
face (`Y` +92%, `A` +39%, `Z` +34% against `z` −36%, `X` −30%, `y` −23%). The
roman's diagonals are 23% under its stems with a tighter spread.

### 4. Two hairlines are at the edge of what survives printing

`X` italic: thin **15.1** units, contrast **6.75** — the most extreme cut in the
face. `s` roman: thin **16.6**, contrast 5.05. At a 16 px x-height those are
about 0.6 px. Everything else in the face sits between 20 and 90.

### 5. The `7` is the lightest figure in both styles, consistently

Colour 0.132 roman and 0.128 italic, against the next lightest at 0.20 and the
figure median at 0.215. Consistent across both styles, so it is the design
rather than a slip — but in a run of figures the 7 reads as a gap.

### 6. What the g's lower loop cost and bought (round 206)

The owner's instruction was *"increase thickness of bottom loop enough to match
visual weight of other letters"*. Measured before: the loop's stroke ran **36.8**
units against the round letters' median of **46.7** (o 53.4, a 49.7, c 46.7,
s 45.2, e 36.9) — the lightest thing in the face. `G_LOOP_PEN` 64 → **84** puts
it at **48.9**, inside that band.

**Two measures disagreed about this letter and both are true.** By stroke
thickness the loop was the lightest thing in the face; by COLOUR its descender
band was already the darkest (0.205 against `p` 0.187, `q` 0.166, `y` 0.129),
because the loop is a large ring — a lot of ink spread thinly. Raising the pen
to match the o's stroke exactly (pen ~96-104) takes that band to 0.27-0.29, half
again as dark as the p. 84 is the value that matches the rounds' STROKE without
making the g the darkest letter on the page.

The ceiling is mechanical rather than aesthetic: at **96** the thickening crown
closes on the connector and the glitch gate reads 2.83 units of white left; at
**104** that white is gone, which **no gate can see**, because a filled bay has
no concave corner. This is the same trap the compound-path attempt hit in round
196.

After the change the **bowl is now the lighter half of the g** — 42.3 against
the loop's 48.9 — and the letter as a whole still measures 42.9 against the
rounds' 53.4. Nothing was done about that; it is his call.

## What was checked and found clean

- **The roman's stems.** 29 glyphs, median 79.0, and not one of them more than
  20% off it. The roman's stem weight is as uniform as a drawn face gets.
- **Colour by family.** Roman stem 0.308 against round 0.305; italic stem 0.311
  against round 0.271. The roman's two main families are within 1% of each other
  in blackness, which is what a text face wants.
- **Figures against each other.** Apart from the 7, both styles' figures sit
  within 20% of their median, and their advances are within 10% of one another
  (348-532 roman, 311-603 italic) — they will set in columns.
- **The `O`/`M` pair** is bit-identical in weight across the two styles, which
  is a useful anchor: it says the two builds share a scale and the −16% is real
  and not an artefact of measuring two different rasters.

## The s, put on the face's weight — round 208

Owner: *"increase thickness of bottom loop"* was the g; this is the letter he
came back to three times — *"you need enlarge the bottom serif of the s too, not
just thicken one stroke. work optically"*, then *"try harder and just make the s
work optically to match the weight of all letters"*, then *"keep the contrast
and brush strokes evident"*.

**The yardstick that settled it is a RATIO, not a stroke width.** Each font's own
s against its own o, by ink area in the reading band:

| | s/o ink area |
|---|---|
| Flanker Griffo | 0.82 |
| Pagella | 0.81 |
| Coelacanth | 0.73 |
| Cancelleresca | 0.70 |
| Poetica | 0.67 |
| **Albo, before** | **0.64** |
| **Albo, shipped** | **0.80** |

Albo's s was lighter than every reference, Poetica included — and Poetica is the
one round 133 fitted these keys to, which is how the deficit got in. The s's ink
WIDTH was never the problem (0.99 of its o against the references' 0.92–1.03);
it was a thin drawing of a correctly proportioned letter.

**Two measures had to be satisfied at once, and the first attempt sacrificed the
second.** Colour parity alone (putting the whole letter on the nib at a level
that matches the rounds) flattens the cut from 3.34 to 2.2, because the ratio
scales thick and thin together — and this face's s is supposed to be MORE
contrasted than its o, which is what the references do (s/o cut 1.14 Flanker,
1.42 Coelacanth) and what Albo does the other way round. `S_PEN_CON` re-spreads
the pen's widths about their geometric mean after the level is set, so weight
and cut are independent dials.

Shipped: the whole letter on the nib at **0.80** with the cut re-spread to
**5.4**, plus the foot below.

| | thin | thick | cut | colour | advance |
|---|---|---|---|---|---|
| s before | 24.5 | 81.9 | 3.34 | 0.285 | 310 |
| **s shipped** | 31.1 | 102.1 | **3.28** | **0.331** | 322 |
| the o | 22.3 | 100.1 | 4.50 | 0.384 | 368 |
| the e | 28.9 | 96.0 | 3.32 | 0.316 | 404 |
| the c | 30.9 | 88.7 | 2.87 | 0.271 | 337 |

The s now sits between the e and the o in colour where it sat 18% under the
rounds, and its cut is unchanged from the letter it replaces.

### The foot, and why three changes were needed rather than one

The bottom terminal is a disc whose radius is half the stroke's end width, so no
weight dial could reach it. Three things had to change together:

1. **The foot grows from the stroke, not as a ball added.** Scaling the disc
   alone (`S_CAP1_R`) left the arm arriving at its old width — a lump stuck on —
   and at 1.9x the handcut `DOT_STYLE` polygon that serves an i's dot was
   visibly faceted at that size. `S_FOOT` widens the PATH over its last stretch,
   which grows the ball for free and cannot step against it.
2. **The cap has to swallow the face.** At the shipped cap amount the trimmed
   end stood proud of its own disc and left a nick on top of the foot. `S_CAP1`
   1.00 clears it. This is the same trap already recorded in `cs_round_end` for
   the c.
3. **The stroke has to reach where the foot goes.** A shoulder survived both,
   because the arm pointed past where the ball hung. Extending the tail and
   filleting the junction with `geom.close_corners` — the pass that welded the
   g's connector in round 205 — makes it one curve.

### Negative results

- **`S_CAP1_R` alone**: rejected, above. It is left reachable and at 1.0.
- **A pen cut instead of a ball** (`S_CAP1=0`): the foot ends in a slanted
  blade, which is a cut stroke and not a serif.
- **A hairline floor to stop dropout** (`S_BASE_FLOOR` 30–36): it works and it
  flattens the letter — cut 2.29 at the weight that matches. Shipped at 0; the
  pen's own thin at this level clears the dropout threshold without it.
- **`close_corners` leaked into the `c`.** The c and the s end with identical
  code, and a `str.replace` without a count changed both — the c came back
  altered in a build that was supposed to touch one letter. Caught by diffing
  all 470 glyphs against the previous build rather than by reading the diff.
  The c is reverted; whether it WANTS that fillet at its own bottom terminal is
  a separate question, and its documented notch says it might.

Gates: glitch 0 of 119, touch 0 of 5,193. Six glyphs move — the s and its five
accented composites, which inherit it as TrueType components.

### The height and the top line — same round, his second look

*"The s is slightly too tall, reduce the top line's visual weight, especially up
its contrast."* All three were measurable and all three were true:

| | ink top | top arc | base | top ÷ base | cut | colour |
|---|---|---|---|---|---|---|
| s as first shipped | 449.4 | 51.1 | 54.6 | 0.94 | 3.28 | 0.331 |
| **s now** | **433.1** | **43.3** | 49.0 | **0.88** | **4.06** | 0.313 |
| the face's o | 437.2 | — | — | — | 4.50 | 0.384 |
| the face's e | 440.2 | — | — | — | 3.32 | 0.316 |
| Flanker's s | 438.2 | 34.7 | 38.7 | 0.89 | — | — |

The first version stood **12 units proud of the o** — and Flanker's s tops at
exactly its own o's height, so an s above the round letters' line is a fault
rather than an overshoot choice. `S_HEIGHT` scales the path about the baseline
(0.975); `S_TOP` is a width multiplier over the head and top arc only (0.86),
so the top line lightens without touching the spine or the foot; `S_PEN_CON`
goes 5.4 → 7.0, which puts the cut at 4.06 between the e's 3.32 and the o's
4.50.

Colour falls 0.331 → 0.313 doing it, which is the honest cost of a lighter top:
still above the e and far above the 0.285 it started at. Gates clean, six
glyphs moved.

## The italic's figures — round 211 (2026-09-18)

Owner: *"add appropriate line contrast and axis to 8 0 2 9 in italic ... make
bottom tail of 7 into a vertical taper like 6, change tails of 3 5 9 to match
their version of 6's tail."*

**The italic's figures were the ROMAN's drawings, sheared.** That is why they
were nearly monoline and why their stress was upright: a shear moves a shape,
not the pen that drew it. Measured before and after, with the italic's own
round letters as the target (o cut 4.64 at 102°, e 99°, a 91°):

| | cut before | cut now | axis before | axis now |
|---|---|---|---|---|
| 0 | 1.67 | **2.88** | 92° | 97° |
| 2 | 2.56 | **2.69** | 88° | 92° |
| 8 | 1.68 | **2.69** | 107° | 103° |
| 9 | 1.90 | **3.06** | 87° | 96° |

Three levers, all italic-only and all inert for the roman (proved: the roman
build is byte-identical across this round):

- **`FIG_CON`** re-spreads a ring's widths about their geometric mean, so the
  ratio goes to the power of it and the letter's COLOUR does not move — the 0's
  is 0.252 before and 0.253 after.
- **`FIG_STRESS`** rotates the NIB the widths are read from. `ring` already had
  a `rot`, and `rot` turns the superellipse and its tangents together, so the
  stress travels with the shape and the axis does not move — the same trap
  `G_SKEW` turned out to be on the g in round 203. Rotating the tangent before
  the width lookup is the real lever.
- **`FIG_OVAL`** pulls each ring's counter onto its own ellipse, which is round
  204's cure for the g's bowl and **the thing that made the contrast possible at
  all**. The 8's own note in this file says smoothing does not fix the pinch a
  swinging width puts in a counter, and it is right: at counter_smooth 6, 8 and
  10 the 8's counters were still dented. `EIGHT_CON` had been sitting at 1.0
  since the round that added it for exactly this reason.

### The tails

The 6's tail is a pen stroke whose profile runs out to 0.12 at the tip. The
others did not have one: the 3's and the 5's terminals THICKENED to 1.25 and
took a cut, the 7's lower stroke was a constant-width diagonal, and the 9's
ended on a sheared face with a wedge flag. Each now runs out — 0.45, 0.45, 0.30
and 0.35 of its width — and each is gated on `pen.ITALIC`.

### One thing the contrast broke, and how it was found

The 9's counter took a **notch** where its tail leaves the ring. The ladder that
located it is worth keeping, because three plausible causes were wrong:

- the ring's own contrast — swept 1.8, 1.5, 1.3, 1.0: the notch survived all four
- the ovalise — built with and without: present either way
- sinking the join DEEPER (`NINE_JOIN_SINK` 8 → 20 → 32 → 44): **worse at every
  step**, which is the diagnostic that named the cure

The tail leaves from a point sunk into the ring, and with the new cut the wall
is thin there, so the tail's inner edge crossed the counter. Sinking it the
other way — `NINE_JOIN_SINK_IT = -10`, so the join starts on the ring's own edge
and the tail runs ALONG the wall instead of through it — closes it. Italic only.

Gates: glitch 0 of 119, touch 0 of 5,193. Twenty-six italic glyphs move: the
figures and the superscript and fraction variants built from the same functions.
The **6's ring** takes the same contrast and axis as the others, which the ask
did not name — it goes through the same `fig_ring` and leaving it out would make
it the only figure on the roman's stress. Flagged rather than assumed.

### Round 212 — the 2's bar, the 7's foot, and three weights

Four more italic asks, all measured before they were moved:

**The 2's crossbar** — *"lower the crossbar of 2 from baseline to where the
crossbar of 4 is."* Ink-weighted over the rows each bar occupies, the 2's base
bar centred at **+43** and the 4's crossbar at **+7.3**; the drop is 42 units
(the bar's own wedge shifts its centre, so 36 of geometry lands 13.1 and 42
lands on the 4's). The slash's foot goes down with it or the stroke stops short
of its own bar. The 2's ink bottom goes 7 → −29, which makes it descend like the
0 rather than sit on the line: named, not assumed.

**The 7's foot** — *"curve 7 tail to be vertical and less thin so quickly."*
Both halves needed a dial. The taper starts at 0.84 of the run instead of 0.55
and ends at 0.58 of the width instead of 0.30. The curve is a cubic whose first
handle holds the diagonal's own line for 0.60 of the chord and whose second
stands above the foot; that second handle's LENGTH is what bends it, and it
saturates — 0.34 / 0.55 / 0.75 / 0.95 of the chord read −27.8° / −26.1° /
−25.4° / −25.3° from upright, so past about 0.55 the extra only puts a kink in
the flank. Shipped at 0.55, the foot at −26° where the straight run was −38°.

**8 and 7 to the 6** — *"match weight of 8 and 7 to 6."* The 6's stroke runs
53.4 units, the 8's ran 64.0 (+20%) and the 7's 41.4 (−23%). The 8's two rings
scale to 0.70 and the 7's bar and diagonal to 1.65 and 1.02; all three now read
53.4 / 54.2 / 54.2. **By COLOUR they do not converge and cannot**: the 6 is
0.255, the 8 0.292 and the 7 0.165, because a 7 is two strokes over a lot of
white and a figure's blackness is mostly its structure. The stroke is the
measure that answers his ask; the colour is recorded so nobody re-opens it.

**The 9's right flank** — *"clean up right side of 9."* The step was the tail's
own start standing proud of the ring's outer contour, and the ladder is worth
keeping because four plausible cures were wrong: a longer, thinner ENTRY taper
(three values — step unmoved); moving the EXIT angle down the ring (−35, −50 —
the step follows the join); the ring's contrast; and the ovalise. The tail
reaches full width at 6% of its path, which is still inside the wall. Burying
the join mid-wall (`NINE_JOIN_SINK_IT` 30) **and** holding the entry thin until
28% — so it is at full width only once it is clear of the ring — closes it with
the counter intact.

**One leak, caught by the diff and not by the eye.** `SEVEN_BAR_W` and
`SEVEN_DIAG_W` are shared with the roman, so setting their defaults for the
italic moved the roman's 7. The build comparison across all glyphs reported it;
the italic now takes its own `_IT` pair. Every other dial in this round was
gated on `pen.ITALIC` from the start, and the roman is byte-identical.

Gates: glitch 0 of 119, touch 0 of 5,193.

### Round 213 — the 7's foot, centred

*"Make 7 tail centered and taper more like 6."* Measured off the built outline,
the foot's centre as a fraction of the figure's own ink: the 7's sat at **0.06**
— hard against its left edge — where the 6's is 0.36 and the 4's 0.57. Shipped
at **0.40**, between the two. The taper starts at 0.65 of the run like the 6's
and ends at 0.25 (the 6 ends at 0.12; the 7's foot stands on the line and cannot
run out to a hair the way a tail flying up can).

**Two instrument notes, because the first number was wrong.** Measuring the foot
on the RASTER, relative to the ink's bounding box, reported 0.06 → 0.04 → 0.04
→ 0.04 across a sweep that plainly moved in the renders: the figure narrows as
the foot centres — the bar's right end is solved from where the diagonal crosses
it — so the box shrinks with the thing being measured and the ratio stands
still. Read off the outline instead it is 0.06 / 0.05 / 0.12 / 0.19, which
matches the pictures. The same trap as the round-208 yardstick that included the
letter it was judging.

And **the shape change undid the weight match**: a steeper, shorter tail leaves
more of the letter's centreline on the bar, so the same dials that read 54.2
last round read **68.5** at the new geometry. The 7's bar and diagonal come back
to 1.12 / 0.80 and it reads 54.2 again, +1% of the 6. Its colour falls to 0.145
against the 6's 0.255 — the structural gap recorded in round 212, now wider
because the letter carries less ink in the same box.

Gates: glitch 0 of 119, touch 0 of 5,193, roman byte-identical.
