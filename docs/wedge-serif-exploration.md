# Wedge-serif exploration ("fjord")

## STATE, 2026-09-12 (read this first; the log below is dated history)

- **What this is.** A humanist wedge serif for longform reading on the X3
  and the iOS app, designed by evolution: populations rendered, owner marks
  keepers, next round narrows or diverges on his ruling. Code and the map of
  it: [`tools/wedge_serif/README.md`](../tools/wedge_serif/README.md).
- **The design is B5.9**: `round10.steps()[-1][2]` -- Book-quiet lineage
  taken to the garalde brief (x-height 415, ascender 762, descender 250,
  stem 82, contrast 0.60 at 26°, wedges 0.85/1.7, arches at 0.52). Drawn by
  `alphabet2.py` (the second drawing model). Coverage: H, a–z, `. , -`.
- **Deliverables are TrueType files**, built by `round12.build`. 26 in
  round 12 (one per technique), 18 in round 13 (refinements of the three
  kept: V23 Scissors, V15 Rotating nib, V19 Gravity), 6 in round 14 (V23a
  cut six times, `round14.py`). Latest files in
  `build/fjord-fonts/` (gitignored) and in the zips sent to the owner.
- **Awaiting**: the owner's marks on round 14, six independent cuts of
  V23a (https://claude.ai/code/artifact/4f6b74f3-f8f0-4f66-89d6-e9706b5bc0be).
  Round 13's other refinements (V15, V19) stand unmarked.
- **Next, once a technique is chosen**: (1) the rest of the character set
  (capitals, digits, punctuation, accents -- the epub `reading` interval);
  (2) a bold (`round4.bold_of` on the params) and, if wanted, italics, which
  do not exist; (3) the reader route in the README ("Taking a font to the
  reader"); (4) an outline-boolean library if one can be built for this
  Python, which would make counterpunch real and let the naive o keep its
  seam in a font.
- **Standing rulings**: body face; humanist rhythm only; defects are knobs,
  the owner decides what is fixed; evaluate on the sentence, never a word;
  vectors, not bitmaps; diverge when asked, never narrow on your own.
- **Fitting rules**: the eight in "How letters fit together" below.

Owner ask 2026-09-12: *"let's explore making a humanist wedge serif like
Albertus and Icone. give me twenty diverse options with just the word 'fjord'
then I'll give feedback. consider readability and enjoyment and character. do
it a variety of styles. ask questions."*

## How the options are made

`tools/wedge_serif/wedge.py` is a parametric synthesizer: five fixed
skeletons (f j o r d, 1000 upm) drawn by a broad-nib pen model (stem weight,
contrast = hairline/stem, stress angle), a stem flare profile (entasis /
ends-only / none), triangular wedge serifs (length, depth, apex tip), a
terminal style (cut / wedge / teardrop / flare), bowl squareness
(superellipse exponent), proportions (x-height, ascender, descender, width)
and slant. Output is SVG polygons (one per stroke, overlapping, separately
filled) and a PIL raster sheet. Nothing is an existing font. `python3
tools/wedge_serif/wedge.py` writes `opt01..20.png` and `sheet.png` beside it.

Round 1 page: https://claude.ai/code/artifact/377acea3-966e-41c2-bcc6-5f938ff46a86

## Round 1 ruling, 2026-09-12: "keep these" (nine of twenty)

Marked on the sheet by hand. Kept: **3, 5, 8, 10, 11, 13, 14, 15, 19**.
Dropped: 1, 2, 4, 6, 7, 9, 12, 16, 17, 18, 20. Read of the drops: every
"pure flare, no wedge" cut went (1, 6, 16), both heavy cuts (4, 12), the
slant (9), the rounded/teardrop cuts (17), the extreme chisel (18), the
asymmetric one (20), the condensed (7) and the crisp Icone lineage (2).
What survived is the text-weight middle plus three deliberate outliers
(calligraphic 5, wide 8, reverse-stress 15) and the two proportion
extremes (classical 10, modern tall 11).

| # | Name | Round 1 | Blurb | Overrides on BASE |
|---|---|---|---|---|
| 1 | Albertus lineage | dropped | flared stems, no separate wedge, moderate contrast | `{'contrast': 0.5, 'stress': 15, 'flare': 0.55, 'flare_shape': 'ends', 'wedge_len': 0.0, 'terminal': 'flare'}` |
| 2 | Icone lineage | dropped | concave stems, crisp wedges, near-mono | `{'contrast': 0.25, 'stress': 10, 'flare': 0.35, 'wedge_len': 0.55, 'wedge_depth': 1.1, 'terminal': 'wedge', 'dot': 'wedge'}` |
| 3 | Text cut | KEPT | moderate everything, built for 11 pt | `{'xh': 500, 'stem': 105, 'contrast': 0.45, 'stress': 20, 'flare': 0.18, 'wedge_len': 0.4, 'wedge_depth': 0.7}` |
| 4 | Chisel | dropped | big triangular wedges, low contrast, Friz-Quadrata weight | `{'stem': 135, 'contrast': 0.3, 'stress': 12, 'flare': 0.12, 'wedge_len': 0.75, 'wedge_depth': 1.3, 'foot_scale': 1.0, 'terminal': 'wedge', 'dot': 'square'}` |
| 5 | Calligraphic | KEPT | high contrast, strong stress, small hooked wedges | `{'stem': 115, 'contrast': 0.8, 'stress': 30, 'flare': 0.2, 'wedge_len': 0.35, 'wedge_depth': 0.6, 'wedge_tip': 0.25, 'terminal': 'teardrop'}` |
| 6 | Monoline flare | dropped | Optima-like: almost no contrast, gentle swell, no wedge | `{'stem': 100, 'contrast': 0.1, 'stress': 0, 'flare': 0.4, 'flare_shape': 'ends', 'wedge_len': 0.0, 'terminal': 'flare'}` |
| 7 | Condensed | dropped | narrow, tall x-height, quick wedges | `{'xh': 530, 'stem': 105, 'contrast': 0.4, 'stress': 14, 'width': 0.78, 'flare': 0.22, 'wedge_len': 0.4, 'wedge_depth': 0.75}` |
| 8 | Wide | KEPT | extended, low x-height, generous bowls | `{'xh': 440, 'stem': 105, 'contrast': 0.5, 'width': 1.25, 'wedge_len': 0.45, 'wedge_depth': 0.8}` |
| 9 | Slanted | dropped | an upright's skeleton at 7 degrees, teardrop terminals | `{'stress': 25, 'wedge_len': 0.4, 'wedge_depth': 0.75, 'terminal': 'teardrop', 'slant': 7}` |
| 10 | Classical | KEPT | low x-height, long ascenders, quiet wedges, book weight | `{'xh': 430, 'asc': 760, 'desc': 250, 'stem': 95, 'contrast': 0.6, 'stress': 22, 'flare': 0.2, 'wedge_len': 0.35, 'wedge_depth': 0.65}` |
| 11 | Modern tall | KEPT | tall x-height, short ascenders, squarish bowls | `{'xh': 560, 'asc': 700, 'desc': 200, 'contrast': 0.4, 'stress': 12, 'flare': 0.2, 'wedge_len': 0.45, 'wedge_depth': 0.8, 'bowl_k': 2.6}` |
| 12 | Heavy display | dropped | bold, blunt wedges both sides of the foot | `{'stem': 165, 'contrast': 0.35, 'stress': 10, 'flare': 0.15, 'wedge_len': 0.4, 'wedge_depth': 0.9, 'foot_scale': 1.0, 'terminal': 'wedge', 'dot': 'square'}` |
| 13 | Light | KEPT | hairline weight, sharp long wedges | `{'stem': 62, 'contrast': 0.5, 'flare': 0.3, 'wedge_len': 0.8, 'wedge_depth': 1.2, 'terminal': 'wedge'}` |
| 14 | Squared humanist | KEPT | superellipse bowls, straight-sided wedges | `{'stem': 115, 'contrast': 0.35, 'stress': 8, 'flare': 0.1, 'wedge_len': 0.5, 'wedge_depth': 1.0, 'bowl_k': 3.2, 'dot': 'square'}` |
| 15 | Reverse stress | KEPT | rustic: the weight sits on the horizontals | `{'stem': 115, 'stress': 110, 'wedge_len': 0.45, 'wedge_depth': 0.8}` |
| 16 | Extreme flare | dropped | trumpet stems, no wedges, the ends do the talking | `{'contrast': 0.4, 'stress': 15, 'flare': 0.95, 'flare_shape': 'ends', 'wedge_len': 0.0, 'terminal': 'flare'}` |
| 17 | Rounded | dropped | soft round terminals and dots, low wedges | `{'contrast': 0.4, 'stress': 16, 'flare': 0.2, 'wedge_len': 0.3, 'wedge_depth': 0.7, 'wedge_tip': 0.3, 'terminal': 'teardrop'}` |
| 18 | Inscriptional | dropped | chisel-cut: sharp entasis and tipped wedges, high stress | `{'contrast': 0.6, 'stress': 28, 'flare': 0.45, 'wedge_len': 0.6, 'wedge_depth': 1.0, 'wedge_tip': 0.4, 'terminal': 'wedge'}` |
| 19 | Sturdy text | KEPT | low contrast, moderate wedges, medium weight, a screen face | `{'xh': 510, 'stem': 120, 'contrast': 0.3, 'stress': 14, 'flare': 0.18, 'wedge_len': 0.42, 'wedge_depth': 0.75}` |
| 20 | Asymmetric | dropped | wedges only on the left, feet only on the right; a hand's bias | `{'contrast': 0.5, 'stress': 20, 'flare': 0.3, 'flare_shape': 'ends', 'wedge_len': 0.5, 'wedge_depth': 0.9, 'foot_scale': 0.6, 'terminal': 'wedge'}` |

BASE: `{'xh': 480, 'asc': 720, 'desc': 220, 'stem': 110, 'contrast': 0.55, 'stress': 18, 'width': 1.0, 'flare': 0.25, 'flare_shape': 'entasis', 'wedge_len': 0.23, 'wedge_depth': 0.45, 'wedge_tip': 0.0, 'foot_scale': 0.8, 'terminal': 'cut', 'bowl_k': 2.0, 'dot': 'round', 'slant': 0, 'o_swell': 0}`

## Open questions (asked one at a time from here)

Answers land in this file as rulings.

- **Purpose (2026-09-12): body text on the reader.** Asked body / both /
  display: *body text on the reader*. So round 2 varies the kept text cuts
  (3, 10, 11, 13, 14, 19) at reading proportions and renders each at the
  real e-ink sizes as well (2x, four levels), with 5, 8 and 15 kept as
  flavor sources for terminals and rhythm rather than as directions.
- **Round 2 shape (2026-09-12): three lanes of six or seven.** Asked one
  lead / blends / three lanes: *three lanes*. Three of the kept text cuts
  each get six or seven variations; the lanes are named in the next ruling.
- **Lanes (2026-09-12): "keep all."** Offered four trios; the answer was
  to keep all nine. So round 2 is nine lanes of two variations each plus two
  blends (3 with 5's terminals; 19 with a milder reverse stress from 15),
  twenty in all, each shown large and at 13 pt on the reader's four-level
  e-ink at the shipped 2x.

## Round 2 (2026-09-12)

`tools/wedge_serif/round2.py`: nine lanes x two variations + two blends,
each rendered as vectors and at 13 pt on the reader's four-level e-ink at 2x
(54 px em, 8x supersampled coverage quantized to 255/200/96/0 at the same
thresholds the simulator's rounding pass uses). Page:
https://claude.ai/code/artifact/48f2c7ae-5d73-46c0-bf82-78d2403e1df1

## The test pangram (owner ask, 2026-09-12: "need long evocative pangram")

Composed here, all 26 letters verified by script, 154 characters:

> Beyond the quiet fjord, a jackdaw skims low over black water, while the
> last light of dusk hazes the zinc-gray peaks and a vixen crosses the
> frozen marsh.

Rendering it needs the other 21 lowercase skeletons (and punctuation), which
the synthesizer does not have yet: that is the round-3 job, after the round-2
ruling, and it is where the exploration stops being five letters and starts
being a face.

## Round 3 (2026-09-12): "skip to 3"

Round 2 was not judged; the owner skipped to the pangram. The whole
lowercase plus `. , -` now exists on the same pen (`tools/wedge_serif/alphabet.py`:
two-storey a, single-storey g, humanist arches, the s as three cubics,
tracking of 22 + 0.16 stem units because the bearings alone ran tight), and
`tools/wedge_serif/round3.py` sets the pangram in each of the nine kept cuts:
vectors, then 13 pt at 2x on the X3's 936 px measure at four levels, native
pixels, plus a 2x NEAREST magnification of the first two lines.
No uppercase yet; the sentence is set lowercase. Page:
https://claude.ai/code/artifact/879713d5-c572-458a-a526-531aa0ce0b41

## Round 3 ruling (2026-09-12): "keep 3 5 19 13"

Four lanes go on: **3 Text cut, 5 Calligraphic, 13 Light, 19 Sturdy text**.
8, 10, 11, 14, 15 are out. Three more rulings in the same message:

- **A regular and a bold.** Every lane gets a bold: stem about 1.6x the
  regular's, contrast eased, letters 5% wider so the counters survive; the
  wedges scale with the stem.
- **"Some characters like z need serifs."** The bar and diagonal letters
  (z, v, w, x, y, k) get wedge serifs at their free ends, on the same rule
  as the stems.
- **"The distance between characters should be the same as within their
  characters."** Fitting by the n: the gap between two adjacent stems equals
  the n's counter (400 x width minus one stem), so a straight side bears
  half of that; a round side bears 0.72 of a straight one, an open side
  0.6, a diagonal 0.45 (the classic optical reductions, so a round next to a
  straight reads as the same air). Bearings are computed from the ink
  extents in `alphabet.layout`, not typed per glyph.

## Round 4 (2026-09-12): regular and bold

`tools/wedge_serif/round4.py`. The four lanes as a regular and a bold each,
pangram, vectors and 13 pt e-ink. `bold_of`: stem x1.6, contrast −0.12,
width x1.05. Two things the first bold taught: the n's stem-to-stem distance
must grow with the stem (`c["nw"] = 400·width + 0.9·(stem − 110)`) or a bold's
counters close and, through the fitting rule, its letter gaps with them; and
the word space is now two letter gaps (`2.2 × n-counter`) because one gap
plus a bit vanished in the bold. The fitting rule as ruled runs open in text
(gap = the whole n counter); the fraction table in `alphabet.py` is the knob
if that is to tighten. Page:
https://claude.ai/code/artifact/d93988af-bbda-46cc-bb2b-5f7a04228517

## Round 4 ruling (2026-09-12): "let's take 3 and match it other s tier fonts somewhat"

Cut 3 is the direction. Measured the eight installed regulars on disk from
their outlines at a 1000 px em (`round5.py` header; Edgar, VandenKeere and
Doves are commercial and not on disk; Inknut's row was a broken read and is
excluded):

| | xh | asc | desc | stem | n-counter | o-width | avg adv | n adv |
|---|---|---|---|---|---|---|---|---|
| Coelacanth | 412 | 759 | 342 | 70 | 214 | 440 | 447 | 526 |
| TeXGyreSchola | 465 | 736 | 202 | 94 | 220 | 431 | 521 | 611 |
| LibreFranklin | 529 | 741 | 165 | 40 | 321 | 485 | 515 | 576 |
| LibrisADF | 487 | 732 | 195 | 82 | 192 | 387 | 418 | 474 |
| TeXGyreHeros | 523 | 728 | 218 | 83 | 251 | 473 | 489 | 556 |
| Almendra | 519 | 725 | 198 | 152 | 127 | 463 | 511 | 594 |
| AtkinsonHyperlegibleNext | 495 | 707 | 162 | 84 | 240 | 475 | 487 | 550 |
| **median** | **491** | **730** | **196** | **84** | **217** | **452** | **500** | **566** |

Two n's in those faces sit ~178 apart on a 220 counter: they fit at ~0.8 of
the counter, not 1.0. `alphabet.py` grew `n_width` and `fit` knobs. The
matched cut (`round5.MATCHED`): xh 495, asc 730, desc 200, stem 88, contrast
0.45, stress 20, flare 0.18, n_width 340; width and fit solved numerically so
the cut's own average advance and n advance land near 500 / 566 (got 517 /
548 at width 0.789, fit 0.907). **The trade this exposed:** the solver
narrowed the letters (o-width 387 against the S-tier 452) because the
fitting rule keeps the gaps wide; matching both the o-width and the advance
needs the fit to drop to ~0.6, which is further from "gap = the counter".
Open question, put to the owner next.

Page (matched regular and bold beside Coelacanth, LibrisADF and Atkinson
Next 365 on the same four-level pipeline):
https://claude.ai/code/artifact/90c27f0d-6bf3-4ff2-9dba-b9bfa83f6fc7

## Round 6 (2026-09-12): "try harder. there is no elegance"

Ruled on round 5, and correct: the first drawing model was stroked polygons
with a thickness corner (max of |sin| and the hairline), butted joins,
triangular serifs and kinked splines. `tools/wedge_serif/alphabet2.py` is a
second model, and the difference is the drawing, not the parameters:

- thickness is continuous: hair + (stem − hair)·|sin(φ − stress)|^1.15;
- every arch and bowl TAPERS into its stem (the n's shoulder leaves at 0.42
  of weight; bowls of b d p q leave and rejoin at 0.5 and end AT the stem,
  not in the air -- the first cut had them ending 60 units short);
- serifs are bracketed wedges: a concave fillet from the stem edge to an apex
  a little below the end; top serifs point LEFT (the first pass had the side
  sign flipped and drew a nub on the right);
- unseriffed ends take the pen-angle cut (12°); terminals flare 0.15–0.18
  into the cut and there are no ball terminals (tried, retired: a ball
  belongs to a different face);
- round letters overshoot 12; the o's loop overlaps itself by 10° so it has
  no seam; the s is one Catmull-Rom spline through eight points;
- the z's diagonal is forced to stem weight (a right-leaning nib makes that
  stroke a hairline; the scribe turns the pen);
- stems that continue into a curve (f j t u) carry no entasis, or the join
  steps.

Matched cut, this round: width 0.85 and fit 0.8 (the o back to ~415 wide;
average advance runs a little over the S-tier 500 -- that is the trade still
open). Page, regular and bold, with LibrisADF and Atkinson Next beside:
https://claude.ai/code/artifact/c521c007-77c0-4083-a160-3f4777a81292

## Round 7 (2026-09-12): diverge

Owner, on round 6: *"make the word images more elegant and balanced ... by
drawing inspiration from the S tier fonts, not revise the S tier fonts
through the same pipeline, but make the wedge serif into variations that I
can pick from. Right now everything's converging, and I need to diverge ...
an evolutionary approach."* So the S-tier faces are BRIEFS, not renders, and
the deliverable is a population.

`tools/wedge_serif/round7.py`: 24 word images on the second drawing model,
two per installed family (Coelacanth, Schola, LibreFranklin, LibrisADF,
Inknut, Heros, Almendra, Atkinson Next, Doves, Van den Keere, Edgar) plus
two wild cards, each hand-tuned on the family's character: proportions,
weight, contrast, stress, pen sharpness (`power`), serif style (`wedge` |
`flare`), wedge length/depth/drop, fillet strength, arch height, cut angle,
bowl squareness. Four axes were added to `alphabet2.py` for this
(`serif_style`, `arch_start`, `fillet`, `power`). Two defects fixed on the
way, both visible in every tile of the first render: the o's 10° overlap
self-crossed and filled even-odd (a white notch at the top; the o is now two
overlapping arcs), and the j's tail set its left bearing (bearings are now
measured in the x-height band only). Page:
https://claude.ai/code/artifact/28347595-899c-41db-8ee1-9269e5e37b5c

## Round 8 (2026-09-12): the evaluation sentence

Owner: *"I cannot judge this by a single word. It needs to be a sentence with
meaning behind it. Look at the most common words and combinations of
letters, digraphs, trigraphs, etcetera."* Six candidates were scored against
Norvig's top-50 bigrams, top-50 trigrams and the 200 commonest words; the
winner on all three:

> what we make of the time we have is the only thing that was ever ours to
> make, and the people we made it for are the ones who will remember how it
> went.

39/50 bigrams, 16/50 trigrams, 28 of its 34 words in the top 200, 21 distinct
letters, 152 characters. (The runner-up, "we do not remember the years so much
as the moments...", scored 31/14/25.) `tools/wedge_serif/round8.py` sets it in
all twenty-four of round 7, vectors and 13 pt e-ink. Lowercase only still.
Page: https://claude.ai/code/artifact/55871d98-a049-47c5-92ce-3b92d9f61cac

## How letters fit together in words (guidance, 2026-09-12)

Owner: *"we need to come up with some guidance on how characters fit
together in words. some e's seem much too big."* The rules the model now
follows, each one a knob in `alphabet2.py`:

1. **One unit of air.** The n's counter (its two stems' inner distance) is
   the unit. Two adjacent straight sides share one unit between them, scaled
   by `fit` (the S-tier faces measure at 0.8; the owner's original rule was
   1.0). Everything else is a fraction of that: a round side 0.72, an open
   side (c e f r t) 0.6, a diagonal 0.45. So `nin` and `non` carry the same
   air to the eye, and `nvn` does not fall apart.
2. **Fit on the x-height band.** A bearing is measured from the ink between
   the baseline and the x-height, never from a descender's tail or an
   ascender's hook: the eye spaces stems, and a j's tail or an f's hook
   overhangs its neighbors instead of pushing them away.
3. **Aperture is air.** An open letter's inside counts toward the space on
   its open side. The e was drawn on the o's full width and read too big:
   it is now 9% narrower than the o with its bar at 0.58 of the x-height,
   and the c follows. (Was: same width as o, bar at 0.54.)
4. **Counters must survive weight.** The n's stem-to-stem distance grows by
   0.9 of any stem growth, so a bolder cut keeps its counter and, through
   rule 1, its letter space; the first bold closed both.
5. **A word space is two units**, not one plus a bit: one plus a bit vanished
   in the bold.
6. **Round letters overshoot** the baseline and x-height by 12 (a knob; the
   hard cuts set it to 0 on purpose).
7. **Rhythm before shape.** Stems fall at close-to-even intervals along a
   word; the arches of n m h u leave their stems at 0.48–0.6 of the x-height
   (`arch_start`) and this is where a face's rhythm lives more than in the
   serifs.
8. **What fitting cannot fix:** a letter drawn too wide or too heavy for its
   neighbors. That is a drawing correction, not a bearing.

## Round 9 (2026-09-12): forty humanist cuts of "Hamburgers in a fjord."

Rulings from the same message: *restrict the rhythm to the humanist end of
the spectrums*; *there is a charm to naively putting shapes together and
having defects (like the gap in the o). let me decide what needs fixing*;
*forty variations with more intentionally designed letters that include
defects but take risks but stay legible and would work for longform text.*

So `tools/wedge_serif/round9.py`: eight humanist lineages (Venetian,
Jenson-warm, Dutch-sturdy, Calligraphic, Albertus-flare, Book-quiet,
Inscriptional, Open-large-x; stress 20–32, contrast 0.4–0.64, pen power
0.86–1.05, x-height 450–510) x five mutations (clean; naive o with its seam
and raw butted joins; no overshoot, square cuts, straight wedges; heavier
with deeper brackets; lighter, wider, longer wedges). The naive o is a KNOB
now (`naive_o`: the single self-crossing loop, filled even-odd, keeps the
seam the owner liked), as are `raw_joins` and `overshoot`. The string needed
a capital, so the model has an H (cap height 0.94 of the ascender, bracketed
wedges both sides, bar at 0.52). Each tile: vectors plus the same line at
13 pt on four-level e-ink. Page:
https://claude.ai/code/artifact/c2ae4aac-323b-4f7a-b6ca-b882ceba9d2e

## Round 9 ruling (2026-09-12): B5, and ten steps toward the garalde

*"let's take B5 and make ten iterations between that initial state to one
that matches garamond, sabon and other similar standard text face."* B5 =
Book-quiet lineage, lighter/wider/longer wedges (x-height 485, stem 79,
contrast 0.45 at 22°). The target is a garalde brief, not a render:
x-height 415, ascender 762, descender 250, stem 82, contrast 0.60 at 26°,
pen power 0.95, width 0.9, wedges 0.85 long / 1.7 deep / drop 0.28 with a
0.65 fillet, cut 20°, arches leaving the stem at 0.52, bowl exponent 2.1,
entasis 0.14, overshoot 14. `tools/wedge_serif/round10.py` interpolates
every numeric knob linearly, t = 0..1 in ten (B5.0 is B5 exactly, B5.9 the
target). Page: https://claude.ai/code/artifact/772404c3-3266-4977-9d33-1b055c1a8257

## Round 10 ruling (2026-09-12): B5.9, and assembly by technique

*"go with the last one. but now take a pass at different ways to assemble
those characters ... do all possible historical techniques, multiple
versions of one technique if it makes sense ... then come up with many more
experimental ways to achieve letterforms that have not previously been
done."* Design frozen at B5.9. `tools/wedge_serif/round11.py` separates
the DRAWING from the MAKING: a technique is either a pen model (replaces
`alphabet2.outline`, the centerline-to-ink step) or an impression model (a
raster pass over the drawn mask, the ink-meets-surface step), and the two
compose.

Historical, H01–H18: naive assembly; broad nib as a true translation pen at
26° and 40°; expert brush (pressure envelope, pointed entry/exit) at two
pressures; pointed pen (hairlines, swelling downstrokes); counterpunch
(counters found by flood fill, struck crisp and slightly large; outer form
dilated and softened) at two files; letterpress ink spread; heavy
impression with the crushed-paper halo (a gray the four levels can carry);
wood type (edge noise, squarer counters); incised stone (walls and trough);
constructed compass-and-rule (constant width, circular bowls); stencil
(two bridges); typewriter (560-unit cell, ribbon halo); phototype (bloom,
tight fit); the pixel era (18 px em, one bit); the panel's own Bayer dither.

Experimental, X01–X20: rotating nib (50° and 110° along each stroke),
ribbon (2.5 and 5 waves), gravity (sag toward the baseline), speed pen
(thickness from curvature), low-poly (1 in 7, 1 in 11), weathered,
halftone stroke, stitched, misregistered two-color, ghosted (the reader's
own defect), wax cast, scissors, and five crosses (brush then letterpress,
counterpunch then knife, pointed pen then pixels, naive then stencil,
gravity then halftone).

Every tile: lossless 150 px em plus the 13 pt four-level e-ink line. Page:
https://claude.ai/code/artifact/9f86acd2-3433-40ac-b1af-5321963cb565

## Round 11 ruling (2026-09-12): "what i need are vector font files"

*"you have misunderstood. what i need are vector font files, not bitmap
treatments. we are generating fonts for epub reading."* Round 11's raster
impression models are withdrawn as deliverables. `tools/wedge_serif/round12.py`
builds one TrueType file per technique from the B5.9 design with fontTools:
26 files, `Fjord-V01.ttf` … `Fjord-V26.ttf`, coverage H, a–z, `. , -`,
space, 1000 upm, advances from the fitting rule. Every technique is an
outline operation: the pen models from round 11 (broad nib at two angles,
brush at two pressures, pointed pen, constructed, rotating nib, ribbon,
gravity, speed pen) and outline models (spread by vertex-normal offset,
Chaikin rounding, decimation, jitter, Sutherland–Hodgman stencil bands,
monospace cell), plus crosses.

Three things learned building real files:
- **No boolean library builds on this Python** (3.14 free-threaded; skia-pathops
  fails to compile), so overlaps union by consistent winding under TrueType's
  nonzero rule. Counterpunch is therefore an approximation (swell + round,
  counters as the strokes leave them); the naive o's seam disappears in a
  font, because nonzero fills a self-crossing loop solid.
- **A pen whose outline crosses itself (brush, pointed, rotating, ribbon)
  cancels under nonzero and leaves slits.** Fixed by emitting one quad per
  centerline segment instead of one polygon per stroke, all wound the same
  way.
- **Abutting quads leave hairline seams in FreeType** even with exactly
  shared edges (checked in the glyf table): antialiasing conflation. Each
  quad now spans two segments so neighbors overlap by one; seams gone.
- Word space set to 1.7 n-counters (2.2 read as a gap in a text line).

Proof: every file parses in fontTools and renders through FreeType (PIL).
The page sets the line and the sentence IN the files:
https://claude.ai/code/artifact/95084fd1-960e-4b47-8fe0-e32fa35590a6
Files: `build/fjord-fonts/` (gitignored) and the zip sent to the owner.

Not yet: the reader route. To read an epub in one of these on the X3 or the
phone, the chosen TTF goes into `lib/EpdFont/local_fonts/`, gets a
`sd-fonts.yaml` recipe (four styles are expected; only a regular exists),
and `build-sd-fonts.py` cuts the `.cpfont` tiers; the seed tree and the iOS
bundle follow from there. That is the step after the pick.


## Round 13 (2026-09-12): refinements of V23, V15, V19

Owner: *"make multiple different refinements to v23 v15 v19."*
`tools/wedge_serif/round13.py`: six each. Scissors: decimation 4/6/8/5 with
jitter 4/6/3/9, a softened cut (one Chaikin pass after), and scissors on the
brush pen. Rotating nib: sweeps 30° and 70°, the 50° sweep from 14° and
from 34°, at contrast 0.45, and with letterpress spread. Gravity: sag 0.3
and 0.9, at contrast 0.5, on a 76 stem, softened, and combined with the
rotating nib (`pen_rot_grav`). Eighteen TTFs, all parse and render. Page:
https://claude.ai/code/artifact/39342925-e32c-4626-9646-f07e6f7dc7d3

## Round 13 ask (2026-09-12): the handoff

*"update or create all md files needed for future agents to learn and
continue from this work."* Done as: the STATE section at the top of this
file; `tools/wedge_serif/README.md` (the code map, how a font is built, the
limits and traps, the reader route); two rows in `CLAUDE.md`'s doc table; a
project memory of the owner's working rules for this work.


## Round 14 (2026-09-12): six cuts of V23a

Owner: *"remake the characters from scratch in v23a six times so I can see
what is possible. I need versions without identical defects."* The cause of
the identical defects: round 12/13 seeded the jitter by polygon index, so a
given glyph got the same snips in every file. `tools/wedge_serif/round14.py`:
each FONT has its own seed, each GLYPH its own random stream (a counter the
post op advances glyph by glyph), the decimation starts at a random phase,
the jitter amplitude varies ±30% per glyph, and each glyph gets a hand's
variation (±1.5% scale, ±0.6° tilt). Six TTFs; the glyf table proves six
distinct outlines of the a. Page:
https://claude.ai/code/artifact/4f6b74f3-f8f0-4f66-89d6-e9706b5bc0be
