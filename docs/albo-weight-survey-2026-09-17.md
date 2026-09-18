# Albo's weight, letter by letter — 2026-09-17

> **2026-09-18, later: every ITALIC number in this file was measured at 26° of
> shear** — `cmp_weight_survey.py`'s `--slant` sign was inverted (see
> `docs/albo-method.md`, instrument bug 6) — and every stroke lying on a glyph's
> bounding-box edge, in BOTH styles, read up to twice its width (bug 7). The
> rulings recorded below were made on pictures and stand. The numbers do not;
> the ones that carried a decision were re-measured on the fixed instrument in
> `docs/albo-misfit-audit-2026-09-18.md`'s correction table (the 6/7/8 match
> survives at 65.1 / 65.5 / 63.2; the roman `z` and `Z` were never heavy).
> `cmp_weight_survey.py` re-runs the whole ledger correctly now.


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

### Round 214 — the 7 reverted, moved halfway, and microserifed

*"Revert 7 to last version, but move it halfway to center. Keep the curve. Redo
the tail to be microserifed."* Round 213's fully centred foot is out; round 212's
taper (0.84 → 0.58) and its curve are back.

**Halfway is a measured point, not a feeling.** Round 212's foot sat at 0.06 of
the figure's own ink and round 213's at 0.40, so halfway is 0.23; the shipped
foot reads **0.24**. The dial is not linear in that ratio — 0.56 of the drawn
width gives 0.15, not the 0.23 a straight line through the earlier sweep
predicts, because the microserif kicks left and pulls the foot's measured centre
with it — so it was measured rather than interpolated.

**The microserif is the family's diagonal end wedge at 0.25 of its 0.9**, on the
foot's left. The 1's flag takes the same wedge at 0.15, which is the owner's own
ruling from round 75 (*"reduce the top spur on 1 into a microserif"*); at 0.15
on the 7 it is a nub you have to look for, and at 0.38 a notch opens above it.
Side matters: on the right (+1) the wedge leaves a re-entrant corner against the
taper, on the left it does not.

**And the weight had to be re-matched a second time.** Moving the foot changes
how much of the letter's centreline is bar, so round 212's 1.65 / 1.02 read
+18% at the new position. 1.30 / 0.86 puts it back at **53.4** — the 6's exactly.
That is twice in three rounds that a shape change silently moved a weight that
was previously matched: the stroke median is a function of the geometry, not a
property of the dials, so it has to be re-measured after every move.

Gates: glitch 0 of 119, touch 0 of 5,193, roman byte-identical.

### Round 215 — the 7 back to 212, and two feet that are strokes rather than slabs

*"Revert 7 and adjust line width according to legibility."* Then, on the
ladder: *"212 wins but needs serif on end."* And separately: *"change big serif
on 1 to brushed."*

**The revert is proven, not asserted.** Round 214's halfway foot and its end
wedge are out. `SEVEN_FOOT_X` goes back to 0.30, the wedge dial is deleted, and
bar/diagonal return to **1.65 / 1.02**. The rebuilt italic is byte-identical to
round 212 across **every** glyph, checked against a worktree build of `2308faa`
rather than against the dials.

**The width ladder, and what it preferred.** Six arms, measured on a raster the
script builds itself — `tools/wedge_serif/cmp_seven_legibility.py`. Four
numbers, each naming a way a 7 actually fails on a panel: `leg_min` (the
darkest pixel in the weakest row of the lower stroke — low means the leg greys
out), `leg_mass`, the junction `aperture`, and `d1`, the 7's distance from the
1 at the same size.

| arm | bar/diag | 13px leg_min | d1 | ink7/ink6 |
|---|---|---|---|---|
| A | 1.35 / 0.83 | 0.361 | 0.601 | 0.592 |
| B | 1.50 / 0.93 | 0.385 | 0.594 | 0.656 |
| **C = round 212** | **1.65 / 1.02** | **0.381** | **0.591** | **0.714** |
| D | 1.80 / 1.11 | 0.402 | 0.584 | 0.771 |
| E | 1.45 / 1.14 | 0.414 | 0.618 | 0.739 |
| F | 1.85 / 0.92 | 0.381 | 0.568 | 0.696 |

**The measure preferred E and the owner ruled C.** E wins both legibility
numbers because its diagonal is the fattest of the set — but a fatter diagonal
is the round-189 ruling (*"thin out diagonal and thicken top bar"*) run
backwards, and E's bar/diagonal ratio is 1.27 against 212's 1.62. Recorded as a
negative result: on this figure the legibility measure and the contrast ruling
point in opposite directions, and the ruling wins.

**THE INSTRUMENT'S FIRST CUT WAS A NO-OP AND SAID SO CONVINCINGLY.** It averaged
each measure over nine sub-pixel phases, because a per-pixel number on a 13 px
raster otherwise reports which phase of the grid the stroke landed on. PIL
**floors a float xy in `ImageDraw.text`** — measured, the ink sum is identical
at ox 0.00 / 0.33 / 0.66 — so the average was the same number nine times, and
two columns of the table were phase noise wearing an average's clothes. The
script rasterises the outline itself now: filled at 16x and box-downsampled,
which is coverage AA (what the panel's four-level path does) and where a
fractional offset means something. The sixth instrument bug of this series, and
like the other five it produced believable numbers.

**Both feet are now the stroke, not an object on it.** This is the s's idiom
from round 209 — his own ruling, *"serif needs to hang low off of current brush
stroke, not be a weird finial"* — applied twice.

The **7** thins monotonically as it always did and then presses back out over
the last 6% of the run: `SEVEN_FOOT_FLARE` 1.45 at `SEVEN_FOOT_FLARE_T` 0.94.
The first cut forced the taper to bottom out at the flare point and spread from
there, which put a **pinch** in the leg — at 330 px the 7 grew a knee the 6's
tail does not have, and past 1.55 it read as a defect. There is no waist now;
the serif is only the press.

The **1**'s foot was the family's chiselled bracket (`stem(foot='both')`, whose
right half the italic exit already replaced in round 103), so what stood there
was one long pointed slab sweeping left — the only slab foot among the figures.
It is a press now too: `ONE_FOOT_BRUSH` 1.45 over `ONE_FOOT_BRUSH_H` 0.20 of S.

**A bracket and a press are distinguishable in one measurement**, which is what
made this rulable rather than arguable. Ink width across the 1's foot, by height
above the baseline:

| | h0 | h10 | h25 | h50 |
|---|---|---|---|---|
| round 212, the slab | 148 | **160** | 149 | 94 |
| now, the press | 142 | 145 | 136 | 90 |

The bracket is **widest above the baseline** and pinches into the stem; the
press is widest **at** the baseline and only narrows. Left reach past the stem
goes 67 → 61 units, so the foot is slightly smaller than the slab it replaced
and not larger — the ladder's 1.90 reached **82**, wider than the thing he asked
to change, and was rejected on that number.

Weight: the 7's stroke median is **54.2**, unchanged, still +0% of the figures'
median; its advance grows 490 → 506 because the press is ink the fitter sees.
The 1 is unmoved at 73.8.

Gates: glitch 0 of 119, touch 0 of 5,193, the 290-glyph sweep reports round
212's same 13 pre-existing findings, roman byte-identical. Eight italic glyphs
move: the 1, the 7 and the superscript, subscript and fraction variants built
from the same two functions.

### Round 217 — the 1's flag becomes a curve

*"Turn top left stroke of 1 to simple thick curve."*

It was a straight run on the bowl profile, ending in a taper with the family's
diagonal end wedge at a sixth of its 0.9 — the microserif he ruled in round 75
(*"reduce the top spur on 1 into a microserif"*). It is now an arc.

**Three dials do the sentence, and each word is one of them.** *Curve*:
`ONE_FLAG_CURVE` bows the stroke perpendicular to its own chord. *Thick*:
`ONE_FLAG_W` on the profile. *Simple*: the end wedge is dropped, because a
microserif on the end of a curve is the finial he ruled out on the s in round
209.

**HE PICKED THE ARM I HAD WRITTEN OFF — see round 218 below.** I shipped +0.18
at 1.25 and recorded −0.18 as a negative result, "bows it the wrong way and the
flag sags". His ruling: *"−0.18 w1.15 wins."* He is right, and the reason my
reading was wrong is instructive: bowed the other way the flag's UNDERSIDE goes
concave, which is what a pen actually leaves when it sweeps in and lifts, and
"sagging" was me reading the outline rather than the stroke. This is the third
entry in this file where a measure or a judgment of mine and his reading of the
page diverged, and the standing rule held all three times.

**ROUND 75'S MICROSERIF STANDS IN THE ROMAN and is superseded only in the
italic.** `ONE_FLAG_WEDGE` is untouched; the curve gates it off. Anyone
restoring it to the italic is undoing this round, not fixing a regression.

**AND THE WEIGHT MULTIPLIER LEAKED INTO THE ROMAN ON THE FIRST CUT** — the
curve was gated on `pen.ITALIC` and the width was not, so the roman's 1 got a
25% heavier flag. Caught by diffing every glyph of both builds, which is the
same leak and the same catch as `SEVEN_BAR_W` in round 213. Gating the shape
and forgetting the weight is now a pattern rather than an accident: the gate
belongs on the whole branch.

The 1's advance moves 300 → 305 and its left bearing 20 → 13, because the
thicker arc reaches further left and the fitter sees it.

Five italic glyphs move: the 1 and its superscript, subscript and two fraction
variants. Gates: glitch 0 of 119, touch 0 of 5,197, the 290-glyph sweep reports
the same 13 pre-existing findings, roman byte-identical in outlines and metrics.
Figure spacing holds at 1.34× spread after round 216's refit.

### Round 218 — the flag bows the other way, and the exit is cut back

*"−0.18 w1.15 wins."* Then: *"reduce length of bottom right serif."*

**The bow is negative.** `ONE_FLAG_CURVE` −0.18 at `ONE_FLAG_W` 1.15 — the arm
round 217 built and rejected. Bowed this way the flag's underside is concave and
it reads as an entry the pen swept in and lifted off; bowed the other way it
reads as a drawn arc. Both were on the ladder and only one of them is written.

**The exit flick is the FAMILY's, and now the 1's is not.** The bottom right is
round 103's calligraphic exit, drawn on every italic stem at `S × pen.IT_EXIT`
— every i, m, n and u foot comes from that one number, so shortening it for the
1 would have re-footed the whole lowercase. `stem()` gains `it_exit_len`, a
per-call scale defaulting to 1.0, and `ONE_EXIT_LEN` is **0.70** — his own
number off the ladder (0.80 barely changes it, 0.50 is a tick, 0.35 stops
reading as a flick at all). Measured, the flick's reach past the stem's own
right edge goes **+9 units to +1**: it is still the letter's right edge, but
only just.

Five italic glyphs move, the 1 and its four variants; the n is byte-identical,
which is the point of the new parameter. The 1's advance goes 300 → 290 and its
left bearing 20 → 2, because the concave flag reaches further left than the
convex one did.

Gates: glitch 0 of 119, touch 0 of 5,197, roman byte-identical in outlines and
metrics, figure spacing holds at 1.31×.

### Round 219 — the 7 was the most monolinear glyph in the face

*"Adjust 7's strokes so it varies pleasantly and fitting rest of font."*

**The complaint has a number, and this file already held it.** `thin` is the
10th percentile of thickness along a glyph's centreline, so `thin ÷ stroke` is
how much a letter modulates *within itself*. The italic reads:

| | o | 6 | a | v | s | 9 | 8 | z | **7** |
|---|---|---|---|---|---|---|---|---|---|
| thin ÷ stroke | 0.40 | 0.42 | 0.46 | 0.55 | 0.60 | 0.65 | 0.78 | 0.89 | **0.94** |

The 7 was the least modulated glyph in the italic: its bar was a constant-width
slab and its leg held one width for 84% of its run, so 90% of the letter's ridge
sat at a single thickness.

**Two changes, one per stroke.** The bar tapers, 1.0 at the wedge end to
**0.55** at the mitre where the leg takes over — `bar()` gained a `prof`
argument for it, which keeps the named edge straight and moves the other, so the
figure's top line stays flat and the underside rises. The leg's existing taper
starts at **0.55** of its run instead of 0.84.

**THE LEG IS THINNED BY STARTING ITS TAPER EARLIER AND NOT BY A WAIST, and both
were built.** A local waist reads as a *knee* — round 215's finding on this same
letter — and it also moves the weight: at waist 0.85 the stroke median fell 54.2
→ 51.2. Starting the existing taper earlier is monotone, so there is no knee and
the median holds at 53.4.

**AND THICKENING THE LEG'S HEAD DOES NOTHING FOR THE RATIO.** Three arms put
1.14–1.22 into the top of the leg on the theory that it should carry the bar's
weight down: `thin` went 51.2 → 56.4 and `stroke` 54.2 → 59.5, so `thin ÷
stroke` went **0.94 → 0.95** and the figure simply got heavier. Only removing
ink where the letter is already thin moves that number. Recorded because it is
the intuitive move and it is wrong.

Shipped: thin 51.2 → **44.4**, ratio 0.94 → **0.83**, stroke **53.4** (held),
colour 0.184 → 0.171. The `thick` figure falls 162.6 → 110.6, which is not a
lost thick — that number was the *junction blob* where a flat bar met a flat
diagonal, and the taper is what dissolves it.

Three italic glyphs move: the 7 and its superscript and subscript. Gates: glitch
0 of 119, touch 0 of 5,197, roman byte-identical in outlines and metrics, figure
spacing holds at 1.31×. `bar(prof=None)` is byte-identical across the whole
font, proven on a build.

### Round 224 — the merged pass: roman Q S X, italic z A k, and the instrument

Owner: *"take a pass at improving all of Albo regular and italic, then show me
a complete specimen."* Two agents, one per style, one file each; the lead
gated and merged.

**Roman** (`caps_straight.py`): the **Q**'s tail gets a dial, `ALBO_ROM_Q_TAIL`
0.50 — its reach 1.80 → 1.08 cap heights; all fourteen of its touching pairs
clear (the roman's collision list goes 19 → 4, every survivor an `f` pair or
`VI`, all pre-existing); the join is untouched, the tail's departure tangent is
exactly as it was. The **S** is rebuilt on the round family's own bowl profile
(`ALBO_ROM_S_BOWL` 1.0, spine 0.82, bottom 0.12, crown +3) — 84.3 → 77.5, cut
2.95 → 1.48, top 699 → 690 on the O's line. The **X**'s thin raised 0.72 →
0.90 (`ALBO_ROM_X_THIN`), 45.2 → 51.2. **Z and W not touched** — both findings
were the instrument (above). Eight roman glyphs, outlines only.

**Italic** (`aldine.py`): the **z**'s diagonal 27 → 36 (`ALBO_ALD_Z_DIAG`) —
the reference split on whether a z's diagonal is thicker than its bars
(Flanker 0.87, Coelacanth 1.00, Poetica 0.71, Pagella 0.68) and round 135's own
words settle it on Flanker; 0.67 → 0.88, colour 0.255 → 0.282, no longer the
palest lowercase diagonal. The **A**'s apex 712 → **695** (`ALBO_ALD_CAP_A_FLAG_Y`
0.96): every reference and Albo's own roman overshoot the flat line by 10–17;
the italic was +32, and the tall thing was the flag, not the apex. The **k**'s
head 806 → **774** (`ALBO_ALD_K_ASC` 0.958), onto the h/l line — it was the only
face with the k proud, and the module comment claiming b d h l shared the call
was wrong and is corrected. Thirteen italic outlines (three letters and their
composites), four metrics.

**Measured and left, each with its ruling:** italic Y (three rulings, rounds
161/163/194; −6% on the fixed instrument); italic b 759 (rounds 193–194,
*".98 and .9 win"*); italic f +24 over the line (Flanker's is +29); the g's
descender (rounds 197/205, the loop anchored on the baseline by his word); the
italic 1 (+21% of a bowl-led median — a stem; its lever is `figures.py`); the
roman Y (`cmp_cap_weight` exempts it by name, round 163).

**One gate is red and is recorded rather than hidden.** `cmp_cap_weight`
reports M +0.06 (pre-existing), Q +0.06 (the roman Q lost a third of its ink
with the tail — a proportion, not a stroke), and **X −0.07**: the roman X was
raised toward its family and the italic X, at 0.79 of the capitals' median, is
now the lighter of the pair. The italic X is the next item, not an exemption.

Gates otherwise: italic glitch 0 of 119, touch 0 of 5,201, `cmp_aldine_metrics`
0 outside 10%, figures 1.31×; roman glitch 0 of 119, touch 4 (from 19).

### Round 225 — three rulings on the round-224 specimen, and the roman o

*"Leave the Q tail on roman long, it only needs to pair with other capitals and
'u'"* — `ALBO_ROM_Q_TAIL` back to 1.0; `Qu` +0.079 em and every capital clears
except `QQ` (kerned +72, roman only) and `QJ` (no English word; exempt). The
lowercase, figure and fence pairs the ruling accepts are exempt by name in
`cmp_touch.py`, so the roman gate reads 4 touching, all the f's arm and `VI`.
*"Leave S as it was because it looked and felt better"* — every S dial back to
round 223. *"Reduce most of the wobble effect"* — `ALBO_HAND_SCALE` 0.3, see
`docs/albo-imperfections.md`. *"'o' roman seems slightly too big and thin, but
not by much"* — `ALBO_ROM_O_RX` 0.95 / `ALBO_ROM_O_W` 1.08: width 485 → 471,
stroke 66.2 → 72.3 (0.81 → 0.89 of the n's stem), colour 0.308 → 0.335.

In flight as this is written: the numerals as OPTIONS from old-style
references (an agent in `figures.py`), and the italic Q's tail from the roman's
shortened construction plus the g redrawn in the roman's style with a shorter
ear (an agent in `aldine.py`).

### Rounds 226–228 — the wobble named, the italic Q and g, the roman R

**226 — the wobble is the polygon.** *"I don't see a wobble difference"*: the
imperfection layer moves the italic lowercase by zero units; what reads as
wobble is the export's dense polyline. Numbers and the three parked cures in
`docs/albo-method.md`. `ALBO_HAND_SCALE` stays 0.3.

**227 — the italic Q and g.** The Q's tail is the roman's construction at 0.50
(`ALBO_ALD_Q_TAIL_STYLE=roman`, `ALBO_ALD_Q_TAIL_ROM` 0.50): ink x 819 → 763,
every Q pair clear. The g is redrawn in the roman's two-storey construction
(`ALBO_ALD_G_STYLE=roman`; `cursive` rebuilds rounds 197–225): loop bottom
−194 → **−305** (rounds 197/205's baseline anchoring superseded by this ruling),
ear 76 → **42** units past the bowl (roman 33, Flanker 55), stroke 63.2 (−10%
of the lowercase, was −27%), colour 0.304 against the o's 0.316, one pen for
the whole letter. A third instrument had round 224's slant bug
(`cmp_aldine_g.py`); fixed.

**228 — the roman R kicks.** Fourteen dials in `caps_straight.py`,
`ALBO_ROM_R_KICK=0` is round 225 exactly: exit 17°, reach 0.730 cap (ink 0.733
vs the italic's 0.735), the pen's cut for a foot, junction −52 → −66° so the leg
springs where the italic's does. Ra / Re / Ro open 0.067 / 0.097 / 0.100 →
0.102 / 0.152 / 0.162 em; RY 0.167 wants a kern beside the other wide Y pairs.
