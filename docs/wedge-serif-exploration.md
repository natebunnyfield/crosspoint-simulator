# Wedge-serif exploration ("fjord")

## STATE, 2026-09-12 (read this first; the log below is dated history)

- **What this is.** A humanist wedge serif for longform reading on the X3
  and the iOS app, designed by evolution: populations rendered, the owner
  marks keepers, each round narrows or diverges on his ruling. Fifty-one
  rounds so far, all on 2026-09-12. Code map and traps:
  [`tools/wedge_serif/README.md`](../tools/wedge_serif/README.md). **How to
  draw a glyph that belongs -- the pen, the serif family, the proportions,
  the rulings, the judging loop:**
  [`docs/fjord-glyph-guide.md`](fjord-glyph-guide.md).
- **The font is `Fjord-Regular.ttf`, 93 glyphs** (A–Z a–z 0–9, 30 marks
  including a real & and @), built by `tools/wedge_serif/round20.py` from
  `alphabet2.py` (lowercase), `round17.py` (`cp_glyphs`: the counterpunched
  o d b p q g e a the font actually uses, the linear cut pen, `E_VARIANTS`
  and `G_VARIANTS`) and `latin.py` (capitals, figures, marks). Design B5.9
  (`round19.DESIGN`: x-height 415, ascender 762, descender 250, stem 82,
  contrast 0.60 at 26°, overshoot 14, arches 12, `lc_width` 0.938). Latest
  files in `build/fjord-fonts/` (gitignored); specimen at
  https://claude.ai/code/artifact/98ccf1e8-527d-4571-9138-4286e0d398fd.
- **Standing rulings** (each with its round): pictures never prose; the
  sentence never the word; vectors never bitmaps; diverge when asked,
  converge on his ruling; defects are his call; body face, humanist rhythm;
  he names the letters, one ask per round; **no spacing page** (25). Caps at
  1.625 xh (26); overshoot is the ink's edge, 14 rounds / 12 arches (27,
  30); lowercase width 0.938, o counter 1.036, capitals untouched (35); one
  wedge family (30); kicks A 65 R 60 k 56 K 37, all different (31, 32, 36);
  H N U right-stem wedges point out, the U's and the I's two-sided (32, 36,
  51); J bar removed (36, reversing 21); the g is G3 on the nib (40, 42);
  the e at 5° / 0.72 pen / 0.62 xh / 330° / blunt (39, 46); D B P R bowls
  one ring construction with the bottom opened (36, 45, 47); the 3's bottom
  after the 5's (44); the 8 to the 6's circle (49); punctuation and figures
  fitted on their full extent (41); fourteen glyphs matched to Van den
  Keere's strokes on the same construction (42).
- **Measured and left alone**: word weight is ascender count and descender
  length, not stroke weight (36, 46); the two levers are the descender and
  the pen's contrast on the rounds, the owner's to pull.
- **Next**: bold and italic; accents (Latin-1, Extended-A); kerning;
  hinting and vertical metrics; the reader route (README).

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


## Round 15 (2026-09-12): seed 73, clean, Garamond widths, quiet joins

Owner: *"seed 73 and let's make several versions that do not have any gaps
or stray marks. let's resize o and other letters to match garamond better.
adjust g and any other characters to have a less distracting overlap area
(counterpunch inspired)."* Three changes, each with its mechanism:

- **Gaps and strays.** Two causes found: a bracketed wedge has 14 vertices
  and the scissors decimated it to three, which is a spike; and jitter moved
  serifs off their stems, which is a gap. `round15.CleanCut`: polygons under
  20 vertices are never decimated, get one rounding pass and a third of the
  jitter; every polygon is grown a few units after the cut so joins
  re-close; polygons under 350 units² of area are dropped as slivers. (The
  threshold was first 12, which still decimated the wedges; the proof render
  did not change until it was 20.)
- **Garamond widths.** `width` 0.9 → 1.0 and `n_width` 340 → 380 on B5.9,
  so the o is ~450 wide on the 415 x-height (Adobe Garamond's o is ~430 on
  397) and the n's ink ~437.
- **Quiet joins.** In `alphabet2.py`: the bowls of b d p q now sweep 312°
  (was 284°) so their tapered ends land inside the stem instead of 40 units
  short of it; the g's stem starts at 0.42 of the x-height, where the bowl's
  right side is already vertical, so the two no longer double up over the
  bowl's upper half, and its top wedge became a short ear.

Six TTFs (c1 fine, c2 finer, c3 medium, c4 facets, c5 steady hand, c6
heavier). Page: https://claude.ai/code/artifact/d0e4de7e-6239-40d2-8596-c5ac673c3452


## Round 16 (2026-09-12): hairline-throughs, and the e's bar

Owner, on round 15: *"V23a-73c5 but address the gaps and hairline-throughs.
inktraps like the H crossbar are good but the crossbar of the e needs to
connect more. make six versions of how to address this. we are making a
text font here, not a display face."* (First read as "line through the s";
he corrected it mid-turn: hairline-throughs.)

**The mechanism.** A stroke is one polygon, left side out and right side
back. At a tight curve, or where the scissors jitter a vertex, the two sides
fold over each other and the polygon crosses itself; under the nonzero fill
the folded part winds the other way and cancels: a white hairline through
the stroke. It is the same failure the brush pens hit in round 12, now on
the default pen after the cut.

**The e.** Its bar stopped at the bowl's inner edge and the bowl's tapered
start did not reach it. The bar now runs `e_bar_overlap` (0.45 stem) into
both strokes and the bowl begins at the bar's own height.

**Six cures** (`tools/wedge_serif/round16.py`, all on c5's cut, all keeping
the H's traps): h1 quads with no cut on the ink, the cut moved to the serifs;
h2 cut the DRAWING (decimate and jitter the centerline, then stroke and emit
overlapping quads, which cannot cancel); h3 the same, gently; h4 stems only,
curves left smooth; h5 as h2 with a pool of ink at each join of the e's bar;
h6 as h2 with the s's spine forced toward stem weight, offered as a proposal
because a humanist s carries its weight there and the pen alone makes it the
thinnest stroke. That spine change is OFF by default (`s_spine` 0); it was
briefly the default and was reverted as unasked.

One self-inflicted defect on the way: replacing the s function by slicing
to the next `def` swallowed the capital H, restored from git. Page:
https://claude.ai/code/artifact/e30c4c30-4ff8-4c73-a250-ab9d8c28ad1f


## Round 17 (2026-09-12): ink traps and counterpunches, hand-cut linear

Owner, on round 16: *"try using inktraps and counterpunches instead. we
want more handcut linear like scissors originally gave us. this is
optically effective wedge serif text font."* So the quad cures of round 16
are out (they smoothed the cut away) and the straight-cut, faceted outline
of the first scissors is back, with the joins and counters handled the way
a punchcutter would. `tools/wedge_serif/round17.py`, three constructions:

- **Linear pen.** `pen_linear` strokes the centerline, REMOVES THE FOLDS on
  each side (`unfold`: a side point that moves backward against the
  centerline's tangent is a fold and is dropped -- the folds were the
  hairline-throughs), then facets both sides with the same phase and a
  small jitter. One polygon per stroke, straight segments, no self-crossing.
- **Counterpunch.** A bowl is an OUTER contour (cut, faceted) around a
  COUNTER contour wound the other way (`Hole`), a hole under TrueType's
  nonzero rule: the counter is the punch, clean, keeping the pen's stress.
  `round12.orient` is replaced by `orient_with_holes` so a Hole keeps its
  winding. Done for o b d p q g, the eye of the e, the bowl of the a. k5
  facets the counters too (a punch cut with a graver).
- **Ink traps.** The arches of n m h u leave the stem at its inner edge and
  taper (`patch_arch`), so a notch opens at the crotch; the e's lower arm
  starts under the bar with a taper for the same notch. `trap` scales them
  (k2 has them at 1.6).

Two mistakes on the way, both mine and both found in the proof render:
the e's eye ended at 171° and its arm began at 203°, so 32° of the bowl were
missing (the arm now continues from the eye's own end); and the g's square
stem top met the ring where it had already curved inward, a visible step
(the stem tucks in at 0.3 x-height now).

Six TTFs: k1 cut 4/3 traps 1.0; k2 traps 1.6; k3 cut 3/2 (straighter); k4
cut 5/4 (rougher); k5 chiselled counters; k6 pure decimation, no jitter.
Page: https://claude.ai/code/artifact/ebe2a2f8-7afd-4d23-b8bb-583e59a4eb8d


## Round 18 (2026-09-12): k6, three bugs

Owner: *"V23a-73c5-k6. bugs: get rid of fractured lines across letters
like j and f. when an o shape extends past a vertical line (like pqbd),
keep it to the stem (lose the o part that goes beyond the stem). use
inktraps (research if you don't know how to chisel out when there is too
much intersection)."*

- **Fractures across j and f.** A stem ended exactly where its tail or hook
  began: two contours sharing an edge, and FreeType's antialiasing leaves a
  hairline on a shared edge (the conflation of round 12). Every stem that
  continues into a curve now runs half a stem into it (`alphabet2`: j f t
  u, and the g's stem into its tail).
- **Bowls kept to the stem.** The counterpunched ring's outer contour is
  clipped 0.06 stem inside the stem's inner edge (a hair of overlap, so no
  shared edge), its counter at the inner edge (`clip_line`).
- **Ink traps.** Three constructions were tried; the first two failed under
  the nonzero fill and are recorded so nobody tries them again. (1) A V
  wedge bitten out by two half-plane clips: the two pieces overlap, wind
  twice, and the counter cancels only one layer, so the bowls filled
  solid. (2) The same as a partition (clip, then clip the remainder): the
  pieces abut along the clip lines and every one of those lines seams, the
  j/f fracture again, radiating from the bites. (3) **What works, and is
  how a punchcutter does it:** a tooth on the counterpunch contour at each
  crotch (the counter's corner vertex pulled into the ink along the
  crotch's bisector) plus a matching notch on the stem polygon's own inner
  edge. Two simple polygons, no clipping. `trap_depth` scales it: t1 0.4,
  t2 0.6, t3 0.85 of the stem (Bell Centennial's order).
- Also the direction of the first bites was wrong (up into the wall, not
  down into the crotch) and an uncapped wedge ran across the counter and
  chewed the far wall. Both are in the log because both looked plausible
  in code.

Page: https://claude.ai/code/artifact/24c8643e-f48b-4883-bb93-73f8064699f0


## Round 19 (2026-09-12): the complete Latin set

Owner: *"i don't see a difference. let's make a complete latin alphabet
with punctuation and address the many issues that need addressing"*, and
mid-turn *"be sure that the bowl like g is clear of overhanging shapes
from outside."* On the trap depths: measured 1–4 differing pixels on a 13
pt line among t1/t2/t3 (6,288 ink px), so the three were the same font;
recorded as a miss and the trap question left open.

`tools/wedge_serif/latin.py`: A–Z (bracketed wedges both sides on the
capitals' stems, counterpunched O Q D and the figures' bowls, thin strokes
at 0.72–0.78 on the diagonals and the N M U's secondary stems), lining
figures at 0.92 cap height, and 30 punctuation marks including curly
quotes, en and em dashes, parentheses, brackets, ampersand, percent, at,
ellipsis. `round19.py` builds `Fjord-Regular.ttf` (93 glyphs, 30 KB) on
the k6 construction, fits capitals and figures on the cap band with
bearings x1.15, and writes the specimen page. The g lost its ear (the
bowl carries nothing over it).

Fixed from my own review of the FreeType render before publishing: the 9
was drawn backward (its curl ran the wrong way and read as a mirrored e);
the question mark was a lump; the parentheses were 260 units wide; the T's
bar and the W ran into their neighbors (the T because capitals were fitted
on the x-height band, under the bar).

**Issues that still need addressing, in the order I would take them:**
1. Only a regular. A bold (`round4.bold_of` on the design) and italics
   (none exist) are needed for the reader's four-style recipe.
2. No kerning. Pairs like Ta, Te, Vo, Wa, LT, "f." need it; the fitting rule
   alone leaves them open.
3. No accents (no diacritics, no composites): the epub `reading` interval
   needs Latin-1 and Latin Extended-A at least.
4. Old-style figures would suit a garalde text face; these are lining.
5. Ink traps at the bowl-stem crotches are too small to act; either widen
   the tooth to ~half a stem across the crotch or drop them.
6. The g without its ear can read as a q at small sizes; a hairline ear
   that sits OUTSIDE the bowl's outer contour is the classical answer.
7. The s (both cases) is the weakest letter; its spine wants weight and its
   terminals a firmer cut. The optional `s_spine` knob exists, off.
8. The ampersand and the at-sign are placeholders drawn to be legible, not
   designed.
9. Capitals are drawn to one width logic; C G O Q are wide against E F L,
   as in the classical model, but B P R S are a touch narrow.
10. No hinting and no gasp table: the reader rasterizes at 8–17 pt through
    its own pipeline, which is what the `.cpfont` tiers exist for, so this
    may not matter there; on the Mac it will.
11. Vertical metrics are a guess (hhea 900/−300); the reader's `metrics:`
    recipe will set the line.
12. The counters of b d p q are clipped at the stem with a straight
    vertical, which is right for a punch but shows as a flat inside edge
    at large sizes.

Page: https://claude.ai/code/artifact/98ccf1e8-527d-4571-9138-4286e0d398fd


## Round 20 (2026-09-12): capitals, figures and marks matched to the garalde

Owner: *"match uppercase to garamond sabon etc. do every step that
lowercase went through for the non-lowercase characters and punctuation."*
Then, mid-turn: *"make an html page lets me interactively adjust the
letter spacing so I can find a better starting value before we proceed."*

No Garamond or Sabon is on disk. References measured (a 1000 px em, medians
in `tools/wedge_serif/garalde_caps.json`): DanteMT-Regular, VandenKeere-
Regular, Hoefler Text, DovesType-Text.

| | median | applied |
|---|---|---|
| cap height / ascender | 0.941 | `capH = 0.941 asc` (was 0.94) |
| cap stem / lowercase stem | 1.137 | `CAP_STEM` on every capital stem and diagonal |
| figure height / cap height | 0.648 (old-style in 3 of 4) | old-style figures: 0 1 2 on the x-height, 6 8 rise, 3 4 5 7 9 descend, each drawn into its measured box (`FIG_BOX`) |
| H counter / cap height | 0.616 | (recorded; not applied) |
| H sidebearings / cap height | 0.084 total | cap and figure bearings = 0.042 capH per straight side, by side fraction (was 1.15x the lowercase rule, about four times too loose) |
| per-glyph ink widths / capH | A 1.03 B 0.81 C 0.93 D 1.08 E 0.85 F 0.75 G 1.03 H 1.16 … M 1.32 O 1.04 S 0.62 W 1.61 | `latin.W` multipliers solved in three passes at build time (`round20.solve_widths`), clamped 0.7–1.45 |
| marks | period 0.16 capH wide, hyphen 0.37 at 0.34 up, en 0.72, em 1.41, & 1.08, @ 1.21 | applied |

Then the same construction as the lowercase: linear pen, counterpunched
bowls (O Q D and the figures), stems into curves, no overhangs.

Two mistakes caught in the FreeType render: shifting the old-style figures
into their boxes rebuilt each contour as a plain list, so every
counterpunched figure lost its Hole and filled solid (`type(poly)(...)`
keeps it); and the 3 and 5 took their width from their box height, so the
width solver drove their multiplier to 0.3 and they collapsed (their radii
are width-driven now, and the solver is clamped).

The spacing page embeds the font with sliders for letter-spacing and
word-spacing in thousandths of an em, size and leading, and a readout; a
value of N‰ goes back into the file as N/2 units on each side of every
glyph. Page: https://claude.ai/code/artifact/a395c37d-54dd-4a48-8353-257baf7e2131
Specimen (same URL as round 19, updated):
https://claude.ai/code/artifact/98ccf1e8-527d-4571-9138-4286e0d398fd


## Round 21 (2026-09-12): the capitals redrawn, and the spacing readout

Owner: *"letter-spacing 34‰ word-spacing −110‰ (this was for CAPS spacing,
lowercase needs much less). keep the line across the J always. redo most
capitals because they are not down in the same style as lowercase and have
the wrong shape (U is weirdly high and short)."*

- **The U floated.** Its bottom curve was a cubic between two stems whose
  control points sat at the baseline, and a cubic bottoms out a tenth of the
  way up: 63 units above the line. The lowercase u had the same bug at 40
  units. Controls now go below the baseline by 0.55 of the start height.
  That is the "weirdly high and short".
- **Capitals redrawn** (`latin.py`, the capitals block): every stem through
  one `_cstem` that uses the lowercase's entasis, wedge and fillet at the cap
  weight; bowls of B P R as tapered strokes like the lowercase b's; diagonals
  thin at 0.72; garalde skeletons (low bar on the A, small upper bowl on the
  B, the E's middle arm short and high, splayed M with its apex on the
  baseline, thin verticals on the N, the R's leg straight to the line,
  pointed V W, the Y's arms at 0.45, beaks on C and G, a weighted spine on
  the S). Widths still solved to the references.
- **The J's line across** is a real bar at cap height now, so no serif style
  can drop it; the J descends a little and hooks left, as the garalde J does.
- **Spacing** applied as ruled: +17 units each side of every capital and
  figure, the space 110 units shorter. Lowercase untouched pending his value.


## Round 22 (2026-09-12): one spacing basis, cap serifs as lowercase, D, j, looptail g

Owner: *"reduce lowercase letter spacing to match uppercase's. and match the
uppercase serifs to the lowercase's, D is a mess as is on the left side.
remove black line across j stem. redo g to be looptail instead."*

- **Spacing.** Both cases now bear from the references' H bearing plus the
  owner's +17: `round20.build` uses one formula for every glyph (the
  lowercase's own n-counter rule, `A.bearing`, is no longer used for
  fitting; it remains the model's rule and the desktop pages' rule).
- **Cap serifs.** `_cstem` now draws exactly what `alphabet2.stem` draws: one
  wedge at the top pointing left, a foot both sides, the same lengths and
  drops; a `top="both"` or `"right"` is mapped to left.
- **D.** The first D closed its outer and counter at the stem's CENTER, so
  the ring's top and bottom, which sit above and below the stem's ends by
  half a stroke, poked out to the left. Now the bowl starts at the stem's
  inner edge and its ellipse is trimmed so the outer contour lands ON the
  cap height (`ry = C/2 − th_h/2`).
- **j.** The "black line across the stem" was the top wedge at the x-height,
  a heavy flag at text size; removed. (The i keeps its wedge.)
- **g.** Looptail: an upper bowl on the x-height (rx 168, ry 0.33 xh), a
  short ear out from the bowl's outer edge, a tapered link down the right,
  and a wide lower loop below the baseline open at its upper right. Nothing
  crosses the bowl.

## Round 23 (2026-09-12): "looptail means double storey g"

Round 22's looptail never reached the font: `round20.build` swaps in
`round17.cp_glyphs` (the counterpunched set the k6 construction uses) and
that set carried its own single-storey g, which overrode `alphabet2.g_g`.
The proof render should have caught it and I did not look at the g alone.
Now the double-storey g lives in `cp_glyphs` itself: an upper bowl on the
x-height (rx 160, ry 0.31 xh) and a lower loop below the baseline (rx 200,
ry 0.56 desc), each an outer contour around a struck counter; a tapered
link from the bowl's lower right into the loop's upper right; an ear out
from the bowl's outer edge. The first loop was 232 wide and two g's
touched; narrowed and given height.

**Trap for the next agent:** anything drawn in `alphabet2.py` for a letter
that `cp_glyphs` also defines (o d b p q g e a) is NOT what the font gets;
edit `round17.cp_glyphs`, or remove the letter from the override.

## Round 24 (2026-09-12): every glyph against Garamond

Owner: "compare all the characters you have made individually with garamond's
and see what is wildly off." No Garamond on disk, so the twin is **EB Garamond
at wght 400** (Google Fonts, OFL), instantiated from the variable file and
compared with its `onum` old-style figures (`*.osf`), not its default lining
set. `tools/wedge_serif/cmp_garamond.py` draws each glyph pair as SVG at matched
x-height (Fjord 415, Garamond 400 units), overlays them, and flags width ±20%,
height ±15%, mean stroke (2·area/perimeter) ±25%, top/bottom ±0.12 xh. Page:
`fjord-vs-garamond.html`. The reference font is not committed; fetch with

    curl -sSL -o EBGaramond.ttf "https://github.com/google/fonts/raw/main/ofl/ebgaramond/EBGaramond%5Bwght%5D.ttf"

**Whole-font, measured:**

| | Fjord | Garamond 400 |
|---|---|---|
| cap height / x-height | 1.73 | 1.63 |
| l stem (xh) | 0.195 | 0.175 |
| o hairline (xh) | 0.128 | 0.075 |
| o side (xh) | 0.182 | 0.205 |
| contrast (side/hairline) | 1.4 | 2.7 |
| lowercase width, median | +12% | — |

The mean stroke matches Garamond (−1%); it is the **thins that are 70% too
heavy** and the thicks slightly light. Every capital tops out ~0.11 xh above
Garamond's because the cap/xh ratio is higher, not because any one cap is
wrong.

**Wildly off, per glyph (55 of 93 flagged, worst first):** the four curly
quotes (half Garamond's size, 0.2–0.5 xh too low, thin); comma (−42% wide,
−31% tall); @ (+39% wide, +23% tall, +38% stroke); semicolon and colon (narrow,
thin); figures 3 5 8 0 9 2 (old-style set 20–28% too tall, top up to +0.29 xh,
3 and 5 also 28–44% wide); & (+25% tall, +30% stroke); = and - (hairline,
−33% tall); \ (short, +33% stroke); # (too tall both ways); … (small dots);
( ) (−33% wide, too straight); s (+46% wide), c (+33%), e (+31%), a (+25%),
j (+24%); f (−23%), I (−28%); z and Z overshoot the x-height / cap height by
+0.17 xh; K spikes +0.19 above cap; U sits 0.18 xh below the baseline; D stroke
−24%; t +0.14 too tall; [ ] descend 0.17 too far; ? +43% wide; ! narrow.

Not flagged and visually near: b d h i l m n o p q r u v w x y, A B C E F G H L
M N O P Q R S T V W X Y (the caps only carry the global cap-height offset), 1 4
6 7, period, hyphen-length dashes, brackets' width.

Nothing changed in the font this round; it is a measurement, for the owner to
mark.

## Round 25 (2026-09-12): j, z, T

Owner, on the Garamond comparison: "stop making spacing page. i think it's
best if I start with what works well, but for now fix j and z and T."

**Rulings:** the interactive spacing page (`fjord-spacing.html`) is NOT
refreshed or republished from here on. Fix order is the owner's, starting
from what works.

- **z** (`alphabet2.g_z`): both bars were centered ON the x-height and the
  baseline, so the letter overshot each by half a bar (+21% tall against
  Garamond), and the top-left wedge pointed up. Bars now sit inside the band
  (`yt = xh − th/2`, `yb = th/2`), the diagonal joins their centers, the
  top-left beak hangs down and the bottom-right one rises. No flags left.
- **j** (`alphabet2.g_j`): hook was 24% too wide, 0.15 xh deeper than
  Garamond's, and ended in a flared blob under a pen cut. Two attempts
  failed first: a bezier with `taper_out(0.55)` still ended blunt, and a
  longer bezier with `taper_out(0.88)` flicked -- the pen model thins any
  down-left diagonal, so the hook lost its weight exactly where a garalde j
  keeps it. Now a quarter-arc-and-a-bit (r 125, 0 to −118°) from the stem,
  with an absolute profile: stem weight through the turn, thinning to 10%
  only past the bottom. Lowest point at 0.97 of the descender. No flags left.
- **T** (`latin.g_T`): the bar was the pen's full horizontal, centered on the
  cap height (overshooting) and pen-cut at both ends under small wedges. Now
  0.62 of the horizontal, its TOP on the cap height, square ends, and a wedge
  the size of a stem's foot hanging from each arm; the stem stops inside the
  bar.

Nothing else moved. 53 of 93 glyphs still carry a Garamond flag, per round 24.

## Round 26 (2026-09-12): the j break, and the capitals' breaks and sizing

Owner: "there is a break on the j tail. fix it. then take on all the breaks
and bad sizing of the uppercase."

**The break had one cause, and it was the construction, not the j.**
`round17.pen_linear` decimates each side of a stroke's outline to one sample
in four and kept the LAST sample (`i == len - 1`) but not the first, so up to
four steps of every stroke's START face were dropped. The j's stem is drawn
bottom-up, so its bottom -- the half-stem overlap into the tail -- was eaten
(stem ended at −111 where the tail began at −128; traced through
`round20.draw` at each stage: original pen −158, linear pen −111). Both end
faces are kept now (`or i == 0`). This also closed the K arm, the N's top join
and the P/R bowl feet, which were the same loss at the other end of a stroke.

**Sizing.** `latin.capH` was 0.941 of the ascender = 1.73 x-heights; Garamond
is 1.625. It is now `xh * 1.625`. Round 24's per-cap "top" flags (every cap
+0.11 xh) are gone; the width solver re-fit every cap to the new height.

**Per letter** (`latin.py`): `bar()` gained `align` ('top' puts the bar's top
edge on y, 'bottom' its bottom edge); E F L Z bars use it, so none overshoots
the cap line or the baseline. K's arm now runs to the stem's center and starts
a third of a stem under the cap line (it stopped short and its serif spiked
+0.19 xh). U's bowl controls are solved so the centerline bottom is half a
stroke above −overshoot (it sat 0.18 xh under the baseline). Z's diagonal
joins the bars' centers. G's spur stem ends flush with its bar's top edge with
no wedge (the wedge under the bar left a notch).

Garamond flags: 53 → 39. Left on capitals, deliberately: Q width −19% (shares
O's width key), I −28% (Garamond's I has wide serifs), J bottom +0.21 xh
(Garamond's J descends further; the bar across is the ruling), D stroke −24%
(a long hairline in a big ring lowers the mean; the D reads fine).
Proof page: `fjord-caps.html`.

## Round 27 (2026-09-12): the arches were short

Owner: "seems like some lowercase characters are low of what they should be
(including h n m w) the seem short."

Measured on the built font, tops over the x-height: o c e s +0.10 xh, n m u
+0.002, Garamond o +0.035 and n +0.075. Two errors in one: the design's
14-unit overshoot was applied to the stroke's CENTERLINE, so every bowl added
half a hairline outside it and overshot 41 units; and the arches peaked with
their outer edge exactly on the x-height. Next to the rounds they were 0.1 xh
short.

Fix, in `alphabet2.ctx`: `over` is now the centerline's overshoot,
`over_edge − pen.th((1,0))/2`, and `over_edge` (the design's number) exists
for the two sites that mean the ink's edge (the layout band, the U's bottom).
Every bowl, ring and cap curve that read `c["over"]` now lands its ink at the
design's overshoot without a change at the site. The arches (`alphabet2._arch`
and `round17.patch_arch`) solve their control height so the curve's centerline
peaks at `xh + over`. The u's bottom and the a's hood and bowl are solved the
same way (u sat 0.11 xh under the baseline; a overshot 0.07 both ways).

After: o +0.034/−0.034, n +0.039, m +0.039, a +0.039/−0.031, u −0.039, caps
O C G S ±0.035. Garamond flags 39 → 38. Proof: `fjord-arches.html`.

## Round 28 (2026-09-12): the g, neck on the left

Owner: "take another pass at 'g' to make the connector stem be on the left
side instead and make the two ovals better match the rest of the lowercase
strokes and visual rhythm when in a word."

`round17.cp_glyphs.g_g` redrawn on Garamond's proportions: upper bowl rx 152
(narrower than the o), top at the rounds' overshoot, bottom at 0.36 xh; ear a
short flick off the bowl's upper right; lower loop rx 190, ry 0.42 desc,
centered 30 right of the bowl and its top at −0.05 desc so it closes under
the bowl; the neck leaves the bowl at 262° (a little left of bottom center),
drops, and swings left into the loop at 118°, pen weight with a floor of 0.6
stem. Two drafts failed first: a straight down-left link read as a stick (the
first from the bowl's left at 250°, the second with the loop 0.58 desc down),
so the neck now drops vertically before turning. The g is fitted on its FULL
extent in `round20.build` (`if ch == 'g'`): the band rule ignored the loop,
which is the g's widest part, and two loops touched in "egg". Proof:
`fjord-g.html`.

## Round 29 (2026-09-12): the arch-overshoot page

Owner: "make an arches interactive page so i can determine the right
overshoot for arches instead of making them exactly the same as loops."

`arch_over_edge` is a design knob (`alphabet2.ctx` → `c["arch_over"]`,
default = the rounds' overshoot; used by `alphabet2._arch` and
`round17.patch_arch`). `round20.build(over={...})` takes design overrides.
Nine builds at 0, 6, 12, 14, 18, 24, 30, 36, 42 units past the x-height
(measured n tops land 2 higher: the bezier's peak is not exactly at t=0.5),
the o at 14 in all nine, embedded in `fjord-arch-overshoot.html` behind a
slider with a large "hnmu o hnmu" under baseline and x-height rules and a
reading-size paragraph. Awaiting the owner's number; the spacing page stays
stopped, this is a different page.

## Round 30 (2026-09-12): arches at 12; kicks; the J bar; one wedge

**Ruling:** "arches, set to 12" -- `arch_over_edge=12` in `round19.DESIGN`
(the rounds stay at 14). The arch-overshoot page stays as a record.

Owner: "take multiple passes at making sure kicks of K k and R are not
disconnected and making all characters have the best possible consistent
wedge to them. J has an awful crossbar, as one of many examples."

Three passes, each rendered and looked at before the next:

1. **Legs.** K's leg started at 0.56 C where the arm passes at 0.67 C; k's
   at 0.56 xh under an arm at 0.63 xh; R's at 0.47 C under the bowl's lower
   curve. Each leg now starts ON the arm's centerline (`u` along the arm) or
   the bowl bezier's point at t = 0.8 (`latin._bowl_point`), pushed back
   along the leg so its end is buried. **J bar** rebuilt like the T's (0.62
   horizontal, top on the cap line, square ends, wedge hanging from the left
   end, stem stopping inside it); it had been centered on the cap line with
   pen-cut ends and a full-weight bar. **Wedges** unified: stem tops 1.0 × 1.0
   wl × wd, feet 0.85 × 1.0, diagonal ends 0.9 × 0.9 both cases (caps were
   0.8), bar ends 0.85 × 0.9 (were 0.7 × 0.8), C/G beaks 0.85 × 0.85 at 1.15
   of the pen (were 0.7 at 1.3, blobby), T arms 0.9 × 1.0 (were 1.0 × 1.1),
   M/W apexes 0.9 × 1.0 (were 0.85 and 0.7).
2. **Junction poke.** A leg thicker than its arm, buried a third of a stem,
   pushed its square end out the arm's far side. `diag`/`_diag` gained
   `taper0`: the leg thins to 55% over its first 22%, buried a fifth of a
   stem. Clean at 560 px.
3. **Reading size.** Legs still join at 13 pt (54 px em). Proof:
   `fjord-kicks.html`, with every seriffed glyph at 230 px for the wedge
   audit.

## Round 31 (2026-09-12): the kicks are the A's leg

Owner: "redo the kicks on K and R and k to match the flow of the lowerright
of A instead."

`latin.kick(c, P, J, s)`: a leg drawn exactly as the A's right leg -- foot-
first from the baseline at the A's angle (`KICK_ANGLE` 65°, the A's
(w − 0.3 s, 0) → (w/2 − 0.18 s, C)), full weight, `serif0=1` so the wedge
foot sits on the outer side as the A's does, straight, thinning into the
junction J over its last 22% (`diag`/`_diag` gained `taper1`). K and R call
it with their round-30 junctions; k does the same in `alphabet2.g_k`. The
foot's x follows from J and the angle, so all three narrowed; the width
solver re-fit K (1.15) and R (1.41). Round 30's tapered 49° legs with the
inward foot are gone. Proof: `fjord-kicks.html` (republished in place).

## Round 32 (2026-09-12): outward top wedges; K's leg; three kick angles

Owner: "the top right serif of caps needs to flare out, not inward. talking
about U N H. extend kick of K to match to arm better." Then: "kicks of R A
and K need to be at all different angles."

- `latin._cstem` `top="right"` now draws the top wedge pointing RIGHT
  (side −1); it used to map 'right' and 'both' to a left-pointing wedge. The
  right-hand stems of H, N and U use it. Other caps with a right stem: M's
  is a `diag` with its own serifs, unchanged.
- K's leg springs from the arm at u = 0.25 (was 0.42), buried 0.35 stem
  (`kick(..., bury=)`), so it runs along the arm to the stem.
- **Ruling: the kicks are at different angles.** `kick(angle=)`: A 65°
  (the reference, unchanged), R 60°, k 56° (`alphabet2.g_k`), K 52°.
  Garamond's order: K splayed widest, R more upright.
Proof: `fjord-hnuk.html`.

## Round 33 (2026-09-12): gaps and obvious issues in the capitals

Owner: "take a pass at fixing the gaps and obvious issues with capitals."
Audited at 330 px, then 600 px close-ups (ANPU, SCBR, EFGM), then 1400 px on
U P C. Fixed in `latin.py`:

- **A**: the thin stroke's square end poked past the thick one at the apex;
  it now ends inside it (w/2 − 0.06 s, C − 0.32 s).
- **N**: the diagonal's ends poked out of both stems; now (x0 + 0.1 s,
  C − 0.3 s) → (x1 − 0.1 s, 0.3 s).
- **B P R**: `_bowl_ctrl` puts both bowl ends a quarter cap stem INSIDE the
  stem (their tapered ends landed on the stem's center and nicked it), the top
  taper is 0.6 of the bottom's, and the bowls' outer edges sit ON the cap line
  and baseline (they were centered on them). `_bowl_point` shares the controls
  so R's leg still springs from the curve.
- **U**: the bowl ran at the lowercase pen's weight between a 1.137 left stem
  and a 0.78 right stem, and the stems' entasis swells their ends: a jog on
  each side. The bowl now runs at CAP_STEM·(1 − 0.22 t) and swells by the
  entasis amount over its first and last 15%.
- **C**: no pen cuts (the lower terminal was a thorn); the beak had been on
  `pts[-1]`, which is the LOWER terminal (the ellipse runs 38° → 322°), now on
  `pts[0]` as the G's.
- **S**: no pen cuts (both terminals were thorns); the C's beak on the top.
- **G**: the bar ended at xg + 0.5 s and its sheared end poked out of the
  spur; xg + 0.25 s.
Proof: `fjord-caps33.html`.

## Round 34 (2026-09-12): five condensed steps

Owner: "make five versions of this font that horizontally condense until the
o counter is an optical circle."

Measured on the round-33 o: outer 528 × 443, counter 375 × 335 (aspect
1.119). The counter's width is 2·226·wf − 77, so a 1.000 counter is wf 0.911
and the conventional optical circle (2% wider than tall) is wf 0.929. Five
equal steps, `width` = `condense` = 0.982 / 0.964 / 0.946 / 0.929 / 0.911 →
counter aspects 1.096 / 1.072 / 1.048 / 1.024 / 1.000; n advance 653 → 626.
`round20.solve_widths` multiplies the reference cap width by `condense`, or
the solver would have widened the capitals back. Files
`fonts/condensed/FjordC-C1..C5.ttf`, page `fjord-condensed.html` (all five
embedded, large "no o bog" and a paragraph each). Awaiting the owner's pick.

## Round 35 (2026-09-12): lowercase condensed to a 1.036 counter, capitals as is

**Ruling:** from the five condensed steps, "keep capitals as is, only
condense lowercase to 1.036 'wide over tall'."

`lc_width` is a design knob (`round19.DESIGN`, 0.938); `round20.draw` builds
a lowercase letter's context from `dict(p, width=p["lc_width"])` and
everything else from `p`. Not `condense` (that re-targets the capitals).
Measured on the build: o counter 375 × 335 (1.119) → 347 × 335 (1.036);
outer o 528 → 500 wide. Advances n 659 → 636, o 603 → 575, h 646 → 623;
H 868 and the space 353 unchanged. Proven by building knob-off and knob-on
from one state of the sources and comparing `glyf` coordinates and `hmtx`
for every glyph: 68 non-lowercase glyphs identical (A–Z, 0–9, 30 marks,
space, .notdef); 24 of 26 lowercase differ (i and l have no
width-dependent geometry). Note `round19.build`, the older builder, ignores
the knob; the font ships from `round20`. Proof `lc-proof.png`. Done by a
subagent scoped to `round20.py` and `round19.py`.

## Round 36 (2026-09-12): G J W joins; A J K D S U; e and g; word weight

Owner, three messages: "subagent for fixing the multiple overlap issue with
G J W"; "flatten the bottom left kick of 'A'; remove top bar of 'J'; fix the
arm vs kick unbalance of 'K'; make 'D' slightly more weighted by opening the
bottom; balance out visual weight of the 100 most common english words."

**Ruling reversed:** the J's bar across the top (kept "always" since round
21) is REMOVED; the J takes a plain top wedge like the I's.

Two subagents, partitioned by file: one in `latin.py` (G J W joins, then A J
K D), one in `alphabet2.py` and `round17.py` (measure ink darkness per word
and per letter at 54 px over the 100 most common words, adjust only outlier
lowercase letters). Results recorded below when they land.

## Round 37 (2026-09-12): Fjord over the humanist S tier

Owner: "make a transparent overlay comparison with all humanist s tier
fonts." `tools/wedge_serif/overlay_stier.py` → `fjord-stier-overlay.html`:
every Fjord glyph (black, 70%) over the same glyph from the nine humanist
faces of the S tier that are on disk, each at 28% in its own color, scaled to
one x-height, aligned on baseline and left ink edge, each face toggleable;
then one rhythm line per face. The faces: Coelacanth, Libris ADF, Almendra
Regular (the four Google files have hashed names; picked by the name table --
the glob had grabbed Bold Italic), Atkinson Hyperlegible Next 365, Inknut
Antiqua, Doves Type, Van den Keere, Dante MT, Edgar. Left out as not
humanist: TeX Gyre Schola, Libre Franklin, TeX Gyre Heros. Paths: the reader
repo's `lib/EpdFont/scripts/downloaded_fonts`, `instanced_fonts`, and
`local_fonts` (the commercial ones). **Trap:** x-heights are measured from
each face's x outline, not OS/2 -- Dante MT's `sxHeight` is 403 on a 2048 em
(it rendered at twice size); Fjord keeps its design 415 because its x carries
wedge tips 26 units above it. Fjord in the page is the round-33 build (the
agents' rounds 35–36 were not yet merged).

**Results, merged and rebuilt from one state of the sources (the proof page
`fjord-round36.html`, the agents' PNGs in the scratchpad).**

Capitals agent (`latin.py`): **G** -- the spur was three polygons (the bowl's
flared terminal poking 40 units past the stem, a stem whose foot stood below
the bowl's edge, a bar whose "flush" top differed from the stem's by the
jitter); the spur is now the bowl's own stroke, the arc stopping at 312° and
bending into a vertical run whose right edge is the bowl's outermost, its
profile ramping to CAP_STEM (`_ramp`), ending buried in the bar. **J** -- bar
removed (ruling reversed); the I's top wedge; the hook starts at the stem's
foot weight and the stem's last 6% tapers into it (its 100-unit foot had poked
12 units out both sides of a 77-unit hook). The J's hook now hangs ~160 units
into the previous letter's space, unmasked by the bar; "Jade", "Jigsaw" tuck
without collision, as Garamond's. **W** -- thin strokes end 0.35 s inside the
thick ones at the feet; the apex is the thick stroke's face with the thin's
wedge crowning it; 40-sample lines (see the trap). **A** -- the left leg's end
face pen-cut flat on the baseline and its wedge built by hand, tip on the
baseline (it rose 45 units). **K** -- junction u = 0.18 → 0.54 C, 59 units off
the stem; the leg angle solved so the foot lands 0.1 s past the arm's tip:
37.1° (arm 30.4°; A 65, R 60 stand); burial 0.1 s (0.2 and 0.35 poked above
the thin arm). **D** -- the counter's lower half lifted by
0.3·th_h·((cy − y)/ry)^1.5: bottom stroke 55 → 72 into the stem, sides and
outer contour unchanged. **S** -- profile +20% over t 0.52–0.96, peak 0.74.
**U** -- `_cstem` `top="right+"`: the full right wedge plus a left one at 0.4
length / 0.6 depth; H and N byte-identical.

**Trap (not fixed, shared code):** `round17.Cut` chaikin-rounds any polygon
under 20 vertices. A `diag()` stroke is a 30-sample line decimated one in
four, which keeps 18 or 20 vertices depending on the phase, so about three in
four diagonal strokes get their end-face corners cut 25% (12–20 units) at
random -- shared-corner constructions fail (the W apex moved 12 units). `g_W`
uses 40-sample lines; changing `diag` itself to 40 would touch every
diagonal capital and is left for a decision.

Lowercase agent (`alphabet2.py`, `round17.py`): word darkness (antialiased
ink over advance × asc..desc band at 54 px) is dominated by ascender count --
every darkest word has one (all, if, did, had, off), every lightest is
x-height-only with o r v w (or, over, our, very). So each letter's darkness
relative to its lowercase median was compared with EB Garamond 400 and
Hoefler Text; only letters off in the same direction in BOTH, for a stroke-
weight reason, were touched. Word spread is structural (sd 0.0114 → 0.0115).
A re-cut alone moves a 54 px reading ±3% (decimation phase), so outline-area
deltas are the honest figure. Changes: **i j** dot radius 0.50 → 0.62 stem
(+4%); **r** arm weight floor 0.78 stem (it climbed at the nib's thin angle
as a 33-unit hairline), flare 0.50/0.45, join taper 0.50 (+5.6%; still ~10%
under Garamond, whose r has a beaked arm -- a design change, stopped);
**e** bar rises 5° (`E_BAR_DEG`), thickness the pen's at that angle 53 → 50,
eye +2.7%, advance 502 → 493; **g** ear a `bracket_wedge` at 35° on the bowl
(`G_EAR_DEG`), the counter untouched. Left alone with reasons: o (matches
Garamond's o/n ratio), f (its ink is the wide bar and double foot), u, p, g,
t, x. `tools/wedge_serif/word_weight.py` is the instrument. The list the
owner pasted is 148 tokens ("their" twice), measured as 147.

**Six g variants** for the owner's pick, `round17.cp_glyphs.g_g` parameterized
by `G_VARIANTS[c["g_variant"]]` (default 0 = the round-28 g, byte-identical):
G1 wedge ear; G2 garalde (bowl rx 136, long neck, low flat loop, flat ear); G3
Jenson/Doves (bowl rx 200, round loop, short neck, tick ear); G4 narrow and
tall (bowl rx 122, loop rx 112, straight neck); G5 open loop (300° stroke,
tail cut 60° short of the neck); G6 heavy loop (constant 82-unit ring).
`fonts/g-variants/Fjord-G1..G6.ttf`, page `fjord-g-variants.html`. G2's long
neck reads as a diagonal at 54 px (the pen thinning a down-left stroke at the
0.6 floor); G4's loop reads small; G6's loop is the heaviest thing on its line.

## Round 38 (2026-09-12): ten e variants

Owner: "give me ten diverse options for 'e' in between before and after;
have a stronger counter inside, different crossbar, different noses."

`round17.E_VARIANTS`, selected by the design key `e_variant` (0 = the round
36 e, glyph-identical to the shipped build, checked by coordinate compare).
Knobs: `deg` bar tilt, `bar` height over xh (lower = bigger eye), `th` bar
thickness over the pen's at that angle (floor 0.42 stem), `end` where the
lower arm stops on the bowl, `nose` cut / flare / taper / beak / blunt.
E1 level 0.55 0.8 cut; E2 2.5°; E3 5° 0.62 flare; E4 3° 0.55 0.75 taper;
E5 level 1.2 beak; E6 5° 0.56 end 330 blunt; E7 8° end 305 cut; E8 3° 0.62
0.6 flare; E9 level 0.85 end 330 beak; E10 4° 0.54 0.9 end 312 taper.
`fonts/e-variants/FjordE-E1..E10.ttf`, page `fjord-e-variants.html`.
Awaiting the pick (and the g pick from round 36).

## Round 39 (2026-09-12): the e dials page

Owner: "for 'e': make an interactive page to adjust angle 0-8 degrees and
thickness (.62-1.2). keep with blunt nose. and any other options I missed."

`tools/wedge_serif/e_dials_page.py` → `fjord-e-dials.html`. Not fonts: the
e is drawn through the builder (`round20.draw` with `round17.E_VARIANTS[0]`
swapped per combination, blunt nose) for every point of a 9 × 10 × 5 × 3
grid -- angle 0..8° by 1, thickness 0.62..1.20 in ten steps, bar height
0.54/0.56/0.58/0.60/0.62 xh, arm end 305/318/330° -- 1,350 e outlines as
x-height-unit SVG paths with their advances (the builder's own bearing rule,
lc_width applied), and the page sets them into words with the current build's
other glyphs. The two dials the owner did not name, bar height and arm
length, are the e's remaining knobs. Each e is cut fresh (its decimation
phase differs from the shipped font's), so the outline is the shape, not the
byte-exact cut. Awaiting the four numbers.

## Round 40 (2026-09-12, in progress): the g is G3; Van den Keere strokes

**Ruling:** "g3 wins but it needs to match the underlying calligraphic
brush strokes." G3 (Jenson/Doves: bowl rx ~200, round loop, short neck, tick
ear) becomes the default `g_variant`; its parts must read as written by the
lowercase's nib -- rings with the o's stress, the neck's weight from the pen
at its angle (shape the path so the nib is broad along it rather than
forcing a floor), the ear a pen stroke, the loop-to-neck join continuous.
Handed to the Van den Keere agent, which owns `round17.py` for this round;
its brief also covers K C D Q R S f G 3 6 9 & @ against Van den Keere with
the construction held fixed. Results to follow.

**Ruling, the e (2026-09-12, from the dials page):** angle 5°, thickness
0.62 of the pen, bar height 0.62 xh, arm length 330°, blunt nose. Set as
`round17.E_VARIANTS[0]` (the bar's thickness floor lowered from 0.42 to 0.35
stem so 0.62 × the pen is not clipped by it). Applied by the round-40 agent,
which holds `round17.py`.

## Round 41 (2026-09-12): punctuation spacing

Owner: "update spacing for punctuation to prevent overlapping." Measured on
the build: ink past the advance box on ( ) [ ] / \ ? * % and the figures 3
and 5 (worst: `/` −101, `?` −95, `\` −93, `]` −84 units), because
`round20.build` measured every glyph's sides inside the x-height band and
those are widest above or below it. Now `if ch == 'g' or not ch.isalpha()`
fits on the full extent. After: no non-letter under 20 units a side. Letters
keep the band rule (f −36 right, j −90 left, J 3 left are the hook and tails
tucking under neighbours, as Garamond's do). Proof `fjord-punct.html`. The
TTF ships with round 40 when the Van den Keere agent's glyphs land.

## Round 42 (2026-09-12): the Van den Keere pass landed

Rounds 40 and 41's agent work, merged and rebuilt from one state of the
sources; proof `fjord-round42.html` (the agent's `vdk-proof.png`, 14 rows of
Van den Keere / before / after, and `vdk-overlay.html` from `cmp_vdk.py`, a
copy of `cmp_garamond.py` pointed at Van den Keere on its measured x top 401).
Owner: "better match the strokes of van den keere for: g K C D Q R S f G 3 6
9 & @. BE SURE TO RETAIN THE SAME APPROACH AS BEFORE FOR CONSISTENCY."

Van den Keere at a 1000 em: stem 82, cap 672, x 401. Per glyph:
- **C S G**: `_beak` -- the stroke swells into a near-vertical face (a −28°
  pen cut) with a short lip (`bracket_wedge` 0.4 × 0.7); lower terminals
  taper to a point (C to 0.34 C, S to 0.22 C); C's arc 43° → 334°. G's bar at
  0.42 C, 0.5 stem thick, short (1.1 cap stems left of the spur to 0.6 right).
- **K**: arm floor 0.47 stem (was the pen's 31-unit hairline), leg 1.1 cap
  stems, junction u 0.16, foot 0.5 s past the arm's tip. Kept: the arm cannot
  be VdK's 48° at the reference width with the family's wedge.
- **Q**: a swash tail from the ring's centerline at 250°, weight floor 1.05
  stems peaking at the belly, tip at 1.80 O-widths, 0.4 C down; advance stays
  the O's, the tail hangs under the next letter (rsb −432; "QU", "Qu" clear).
- **R**: leg 1.05 stems; a junction at t 0.9 tried and reverted (the solver
  pinned the bowl at 1.45).
- **D**: ring k × 1.12 (squarer shoulders, rounder belly); the round-36 heavier
  bottom kept by ruling.
- **f**: hook radius 150 → 200, flare 0.35 + cut, bar 0.8 × pen with its top on
  the x-height, 45 left / 120 right (VdK 149; the band sets the advance).
- **3**: default width 400 → 330 (it had pinned the solver at its 0.7 floor);
  two superellipse arcs, upper bowl smaller and right, pinch at 0.60 h.
  **6**: one stroke from the ring's leftmost point (vertical tangent, so the
  outline continues the bowl's) thinning to a point. **9**: the mirror, held
  at 0.9 stem through the turn.
- **&**: a garalde ampersand, one catmull stroke on the pen through 24 measured
  points; the arm ends in the family's wedge (VdK's is a flat serif).
  **@**: on the baseline at cap height (was at the x-height), ring at 0.85 pen
  (full pen went black at 13 pt), an a on the a's own construction inside.
- **g (G3 on the nib)**: bowl rx 185, 0.70 xh; loop rx 215 × 0.45 desc, centre
  +30; neck from 242° into the loop at 150° -- a near-vertical drop (8° lean)
  with NO floor, the nib giving 58–66 on its own; at 140° the loop's top
  hairline kinked into the neck. Ear a pen stroke off the shoulder at 48°
  rising 5°. Kept: depth (VdK's g descends 0.74 xh; the descender is 0.60).
  The old default g is `G_VARIANTS[7]`.
- **e**: `E_VARIANTS[0]` = 5°, bar 0.62, th 0.62, end 330, blunt; floor 0.35.

`cmp_vdk.py` flags on the 14: before 8 flagged, after 0; whole font 37 → 31
(the rest are punctuation, dots, s, I -- out of scope). Solver widths after:
C 0.92, G 0.88, K 0.99, R 1.33, S 0.97, 3 0.86, 6 0.73, 9 0.70.

## Round 44 (2026-09-12): the 3's bottom after the 5's

Owner: "without copying it exactly, match the bottom stroke of 3 to 5." The
5's bowl: center 0.5 w, rx 0.55 w, sweeps to −160°, `flare_end(0.25)` + pen
cut. The 3's was center 0.55 w, rx 0.45 w, stopped at −132° with
`flare_end(0.35)`, so its bottom curled into a knob. Now center 0.52 w, rx
0.52 w, to −156°, flare 0.25 + cut; the joint's `taper_in` stays. Solver
width for 3: 0.76. Proof `fjord-35.html`.

## Round 45 (2026-09-12): P and R bowls opened at the bottom

Owner: "open R and P counters the same way D was opened up recently." The
D (round 36) lifted its counter's lower edge by 0.3·th_h·((cy−y)/ry)^1.5.
`_bowl_stroke` gained `open_bottom`: over t 0.5–0.96 (a half-sine window)
the stroke thickens by open_bottom × th_h and its centerline shifts up by
half that, so the outer edge holds and only the counter's edge lifts. P and R
pass 0.3; B does not. Proof `fjord-pr.html`.

## Round 46 (2026-09-12): the e bar a little heavier; second weight pass

Owner: "increase the e crossbar thickness slightly; make sure the visual
weight of all lowercase letters is even in common words." `E_VARIANTS[0].th`
0.62 → 0.72 (at 5° the pen gives 51, so the bar goes 32 → 37 units). The
weight pass is re-run on this build by an agent scoped to `alphabet2.py` and
`round17.py`, same instrument and rule as round 36 (only letters off in the
same direction in both Garamond and Hoefler, for a stroke-weight reason).
Results below when they land.

## Round 47 (2026-09-12): B P R bowls on the D's ring

Owner: "the shape of the interior for B and P and R needs to resemble D much
more." `latin._bowl_ring(c, P, x, y_top, y_bot, rx, open_bottom, k_mult)`:
the D's construction generalized -- `round17.ring` half-ring from the stem's
inner edge, cy at the middle of y_top..y_bot, ry so the outer edges land ON
them, k × 1.12, the counter's lower half lifted by open_bottom × th_h,
both contours closed inside the stem. Returns (cx, cy, rx, ry). B: two rings
(upper without the lift), overlapping at the waist by 0.3 th_h each way; P
one ring; R one ring with the leg springing from the ring's centerline at
−52°. rx = 0.72 of the old bezier widths; the solver re-fit B 1.16, P 1.07,
R 1.10. `_bowl_stroke` / `_bowl_point` remain for reference, unused by the
capitals now. Proof `fjord-bpr.html`.

## Round 48 (2026-09-12): the 8 on two optical circles

Owner: "make 8 use more optical circles, big on bottom if needed." The 8 was
two stacked ovals, taller than wide (the width solver had pinned it at
0.76). Now `g_eight`: r1 = 0.240 D, r2 = 0.285 D + overshoot; each ring's x
radius solved from its y radius and the pen so the COUNTER is 1.02 wide over
tall (the o's rule): rx = (1.02·(2ry − th_h) + th_v)/2; measured after the
cut 1.007 and 1.010. Rings overlap at the waist by 0.05 D. The solver's W['8']
is now unused. Proof `fjord-8.html`.

## Round 49 (2026-09-12): the 8's circles sized to the 6's

Owner: "reduce both circles in 8 (especially the top) to match the circle in
6. use optical sense." The 6's circle is its OUTER bowl (411 × 419, 0.98
wide over tall, counter 258 × 312, on a bowl 0.635 of the figure height).
`g_eight` now sizes each ring's outer contour in that proportion --
`ring_for(h)`: ry = (h − th_h)/2, rx = (0.98 h − th_v)/2 -- lower h = 0.60 D,
upper 0.50 D, crossing at the waist by 0.10 D; upper top ON the figure
height, lower bottom at −overshoot. Measured: lower outer 394 × 377, counter
243 × 271; upper 329 × 338, counter 178 × 232. Round 48's circular-counter
rule is superseded (its rings were 460 and 428 wide against the 6's 411).
Proof `fjord-8.html` (republished in place).

## Round 50 (2026-09-12): the figures over the humanist old style

Owner: "compare 8 and all numbers with humanist old style figures."
`tools/wedge_serif/fig_overlay.py` → `fjord-figures-overlay.html`: Fjord's
0–9 over the OLD-STYLE figures of the humanist faces on disk, each face's
`onum` set where it has one (the proportional `.osf` preferred over the
tabular `.tosf`), its default set where that is already old-style (the 3
descends, or the 8 rises well above the 0). Eight faces qualify: EB Garamond,
Coelacanth, Almendra, Inknut Antiqua, Doves, Van den Keere, Dante MT, Edgar.
Libris ADF and Atkinson Next carry only lining figures and are left out. The
8's cell is boxed; a figure row per face follows.

## Round 51 (2026-09-12): a slight serif on the top right of the I

Owner: "put a slight serif on the top right of 'I'." `_cstem` `top="left+"`,
the mirror of `right+`: the full left wedge plus a small right one (0.4
length, 0.6 depth, 0.4 drop). The I only. Proof `fjord-I.html`.

**Round 46 results (the second weight pass, agent):** no lowercase letter
changed. On the round-46 build, measured at 54 px against EB Garamond 400
and Hoefler Text, plus outline area over the n's (spacing-independent), every
letter more than ~8% off in BOTH references is off for a structural reason:
g p q -- the descender (0.72 of the ascender over x-height; EB 0.93, HT
0.88); u -- the construction (three wedges to the n's five; a two-sided right
foot priced at +0.9% because the curve buries it; entasis on the left stem
+1.5%); t -- its bar is already heavier than both references (0.70 of the n's
stem vs 0.47/0.39), what they have is a longer tail; o -- darkness opposite
in the two references, area −6%, and its ring never exceeds the stem where a
garalde's rounds run heavier, which is the pen's contrast (global, off
limits); i -- dot already at Hoefler's proportion (a 0.70-stem dot would add
4.3%, not shipped); f j -- the tucked advances; a s -- width, not weight;
z y x -- ruled or not in the list. Darkest words: if all off did had life old
by like still; lightest: over or very never our even too two to now. Proof
`fjord-weight2.html`, tables in `scratchpad/wedge/wt2/`.

**Trap (README):** `pen_linear`'s decimation phase is one running counter
across every stroke in CHARS order, capitals first, so editing ANY capital
re-cuts every lowercase glyph after it: a B/P/R edit moved 66 glyphs with no
lowercase source touched and shifted 54 px darkness readings by up to ±3%.
Compare weight only between builds of the same capitals, or compare outline
areas, which do not move.

## Round 52 (2026-09-12): the docs, and eight rulings for the rebuild

Owner: "update all md files, including a detailed write up for how a sonnet
agent could generate characters for this font in the future ... ask me many
questions as needed." Written: `docs/fjord-glyph-guide.md` (the pen, the
serif family, the proportions with each ruling's round, the fitting rule,
the judging loop, a recipe, the bold, the open items); this doc's STATE
section, the README, the CLAUDE.md row and the memory brought to round 51.

Eight questions, one per turn, his answers (all in the guide's §0):
1. **The next job is a full rebuild** -- "full rebuild as the current
   characters are crude."
2. **Crude means** the stroke construction, the letter shapes, the serifs
   and terminals; NOT the cut.
3. **Drawn as designed outlines**, the pen a reference for weights, real
   joins, the linear cut on top.
4. **Kept fixed**: the proportions, the rulings on specific letters, the
   wedge serif family.
5. **Shape references**: "garamond, garalde, edgar" -- EB Garamond, Van den
   Keere and Dante, Edgar.
6. **Contrast moves toward the references** (about 0.45), checked on the
   reader's pipeline before ruling.
7. **Descender picked from a render** of 250 / 290 / 330 at reading size.
8. **Delivered as the whole set first**, one specimen, then rounds by name.

## Round 53 (2026-09-12): the rebuild's two picks, rendered

Owner: "go." Step 1 of the rebuild order: six builds of the current glyphs
(`round20.build(over=)`): descender 250 / 290 / 330 at contrast 0.60, and
contrast 0.60 / 0.50 / 0.42 at descender 250. Each set as five lines at 13 pt
on the 2x reader (54 px em), line 1.25 em, through the reader's four-level
pipeline (8x supersampled coverage quantized at 0.108 / 0.42 / 0.812 to
255 / 200 / 96 / 0). Page `fjord-rebuild-dials.html`; TTFs in
`fonts/dials/`. Awaiting the two picks; the rebuild agent starts on them.
Owner on the first page: "make it mobile friendly" -- the artifact viewer's
`img{max-width:100%}` had squashed the 1700 px sheet to the phone's width.
Rebuilt as six 750 px blocks wrapped to that width, shown at 375 CSS px
(native on a 2x phone). Rule added to the guide §4.
**Ruling (descender):** 250, as now. The g p q j y stay at their depth; the
weight-pass lever is closed.
**Correction (2026-09-13):** the first contrast blocks were built the wrong
way -- `Pen.hair = stem × (1 − contrast)`, so lowering the number THICKENS
the thins; 0.42 gave a hairline 12% heavier, and the owner rightly saw no
difference. Rebuilt at 0.60 / 0.70 / 0.78: o hairline 0.130 / 0.113 / 0.105
xh (2.9 / 2.5 / 2.4 px at 13 pt); large "oeca no" blocks added so the dial
can be seen. The guide's formula corrected.
**Ruling (contrast, 2026-09-13):** 0.60, as now. Both rebuild picks made:
descender 250, contrast 0.60 -- the rebuild's pen is the current pen. Step 2
begins: the whole set as designed outlines.

## Round 54 (2026-09-13): the rebuild -- all 93 glyphs as designed outlines

Owner: "go." Step 2 of the rebuild order, by one agent on the glyph guide:
`tools/wedge_serif/outlines/` -- a new package beside the round-17/20
generator (which still builds the round-51 font and is the "before").
`geom.py` (curves sampled at 11 units; unions on **shapely 2.1.2**, installed
this round -- `skia-pathops` still does not build on 3.14t), `pen.py` (the
pen as the reference: `check(outer, inner)` reports a drawn stroke against
it), `primitives.py` (stem as ONE solid with its wedges, the wedge family at
the ruled sizes, stroke, ring/ring_from, half_bowl for D B P R, diagonal,
bar, beak, trap, dot), `cut.py` (one-in-four, seed 73, every corner kept),
`build.py` (draw → 1.2-unit grow → contours → cut → the round-20 fit → TTF +
specimen), `glyphs/` by family, `cmp/` (dbg, look, checks, overlay4, the
mobile-friendly proof), `NOTES.md` (every decision and number).
Build: `cd tools/wedge_serif && PYTHON_GIL=0 python3 -m outlines.build
<out_dir>`.

Measured: o counter 353 × 340 = 1.036 (ruling held); no non-letter under 20
a side; ink past the advance only on the ruled tucks (f, j, J, Q) and the
q's right foot (−16, below the band). Word space 353. Weight at 54 px,
round 51 → rebuild: lowercase median −1.3%, word median −3.6%; arches
designed thinner over the shoulder (n −12, h −11, r −10), g +10, x +8, s +8.
Reference flags (cmp_garamond thresholds) round 51 → rebuild: Garamond
35 → 43, Van den Keere 32 → 41, Dante 67 → 69, Edgar 65 → 64 of 92; the
rise is the mean-stroke figure being measured honestly on one outline
(the old font's perimeter double-counted overlapping polygons), and every
diagonal letter now shows the kept 0.60 contrast as a +29–47% stroke flag.
Decisions stated in NOTES: entasis quartic (a straight waist); e radius 195
→ 186, t top 120 → 95 over the x-height, r reach 200 → 172; counters as
smoothed pen offsets of drawn outers; capitals, figures and marks looked at
through FreeType but not each overlaid by eye. The TTF is 16 KB (one outline
per solid) against 32 KB. Proof `fjord-rebuild.html` (27 PNG blocks at 750
px), overlays `fjord-overlay4.html`; the specimen at the standing URL now
carries the rebuild. His rounds by name follow.

## Round 55 (2026-09-13): the rebuild's regressions, found and fixed

Owner: "are you able to identify the regression issues where things look
much worse than before?" Every glyph rendered before (round 51) / after
(rebuild) at 150 px, the suspects at 500 px, plus a numeric diff (contour
counts, ink width, top, advance). Seven regressions, all construction, none
a ruled change; fixed by the rebuild agent in three passes, each re-rendered
to the same images and looked at:

1. **d q**: the bowl ran through the stem and out its far side, 18% wider --
   the record's stem placement copied with a sign error. Kept to the stem
   again; d ink 501 → 507, q 499 → 507.
2. **a b p u**: white nicks at the joins -- trap cutouts pointing into the
   strokes (b p, and the u's mirrored from the n's); removed. The a's hood
   crotch and a tooth in its counter (the pen-by-tangent offset stepping
   33 → 77 at the diagonal-to-round turn) redrawn.
3. **& %**: the ampersand's crossings became holes (`make_valid` on a
   self-crossing polygon); strokes are now unioned as overlapping pieces.
   The %'s rings used the centerline radius as the outer; counters restored
   (163 of 317).
4. **x**, then **v w y k A M N V W X Y K U** and **R**: thin diagonals had
   been 0.72 × the STEM; round 51's rule is 0.72 × the pen's width at the
   stroke's own angle (and the capital diagonals never carried the cap
   factor). Applied everywhere; every glyph within 8 units of round 51's ink
   widths; the R's leg 1.05 × pen at 60° (64, not the constant 92).
5. **5**: bar top-aligned instead of centered and its stem without the cap
   factor; top 433 → 460.
6. **s**: carried the capital S's spine boost and beak; round 51's lowercase
   s restored (ink 366).
7. **g**: the neck's square start face straddled the bowl's edge; it starts
   22 units inside now, the ear likewise.

After: o counter 1.036; flags Garamond 38 / VdK 35 / Dante 67 / Edgar 63
(round 51: 35 / 32 / 67 / 65); lowercase median darkness −3%, word median
−4%. The q's right foot 16 past its advance and the y's tail at −282 are the
record's geometry. Recorded in `outlines/NOTES.md` ("Regression pass"). The
specimen at the standing URL carries this build; his rounds by name follow.

## Round 56 (2026-09-13): the brush-stroke revision -- D B P R, then every letter

Owner: "D B P R all need a lot of brush stroke revision, after those do every
other letter." Against Van den Keere at 230 px the rebuild's bowls were
TUBES -- one thickness all round, the top and bottom as heavy as the side --
and the P's and B's lower bowls left a slit at the stem; the R's leg was a
straight uniform bar. Cause found by the agent: `half_bowl` looked up the
pen's tangent by an index from the pre-resampled path, so every width was
shifted and the top took the side's 77.

**Phase 1, D B P R** (`fjord-phase1-DBPR.html`): the bowl is a pen stroke --
the designed centerline (half superellipse, k × 1.12, outer edges on the
lines, the fixed widths) offset by `pen.th(tangent)/2` both sides, both ends
running 22 units into the stem and tapering to 0.42 of the pen over their
last 10%; the opened bottom lifts the lower centerline by half the extra and
adds the whole to the width so the outer edge holds. `pen.check` reads ~1.0
around the bowl, 1.09–1.33 through the opened lower half, 0.4 at the ends.
B upper bowl 0.86 of the lower, both ends meeting at 0.55 C as hairlines. R
leg foot-first on a cubic bowed 9 units, 1.05 × pen at 60° at the foot
thinning to 0.42 into the bowl, the A's foot wedge.

**Phase 2, every other letter** (seven pages, `fjord-phase2-*.html`): the
arches n m h u r on a designed centerline offset by the pen (hairline up the
stress, 55 over the top, full stem down the shoulder), thinning 0.30 into the
stem, trap notch kept; the a's counter as the pen's offset with the width
sequence averaged over ±4 samples at the tight turn; the U on round 51's
profile with entasis at the stems; 2 4 7 diagonals, the comma family, ! ( )
on the pen. Already on the pen and left alone: o c e, b d p q, g, s, f t,
the straight diagonals, C G S, O Q, J, the figures' arcs, & @ ? % *.

After: o counter 1.036; flags Garamond 35 / VdK 37 / Dante 68 / Edgar 64;
lowercase median darkness −2%, word median −4% against round 51. **For the
owner:** the pen at 26° puts a bowl's maximum at 2 o'clock (tangent 116°),
thins at 11 and 5; Van den Keere's D carries its weight at 4 o'clock. That is
the pen's definition (`stress`), not a drawing; moving it moves every round.
Recorded in `outlines/NOTES.md` ("Brush-stroke revision").

## Round 57 (2026-09-13): B and related -- the bowls' measured profile

Owner: "take another pass at B and related characters because your
understanding is wrong." Measured with `bowl_rays.py` (ray-cast thickness by
angle from the bowl's center, 0 = 3 o'clock): Van den Keere's D P B O peak
at 0° at 95–98 (the stem is 82), symmetric, falling to 32–46 at ±80°; Fjord's
peaked at +20° at 85 and fell only to 56–70. The 26° nib was the wrong model
for the bowls: their stress is vertical, their contrast ~2.7, and they run
heavier than the straights. Fitted `w = 34 + 63·|cos θ|^1.28`; handed to the
rebuild agent for D B P R; O C G Q and the lowercase bowls left for a ruling
(the reference's O has the same profile).

**Landed.** `outlines/primitives.half_bowl` is now Van den Keere's
construction, measured: a flat run from the stem along the top, a round end
(a semicircle of the bowl's half height, k 2.0), a flat run back; the width
at every point `bowl_profile(tangent) = 34 + 63·|sin φ|^1.7` (hair 0.42
stem, max 1.18 stem, vertical stress). The exponent is 1.7, not my fitted
1.28: the agent ran a 12-cell grid (round-end 0.65–1.0 × exponent 1.28–2.2)
against the D P R rays and 1.0 / 1.7 minimized the error (sum |Δ| 141 over
27 cells). The opened bottom is now a 0.06 asymmetry; the ends run 22 into
the stem easing to 0.7 of the hairline. Rays, VdK / Fjord (−80 … +80):
D 38 54 75 90 97 97 85 66 46 / 50 66 84 95 99 96 84 66 45; P 34 52 74 90 95
89 72 52 37 / 39 55 75 92 97 91 71 51 39; B (lower) 32 44 64 87 98 90 71 /
38 50 71 90 99 92 73; R 40 84 91 95 95 94 88 72 / 64 87 96 99 97 90 78 57.
Within 8 everywhere except the D's lower half (the opened-bottom ruling
keeps it ~10 heavier than VdK's, which is thinner at the bottom than the
top) and the R's rays that cross the leg's root. O C G Q and the lowercase
bowls untouched: VdK's O measures the same profile (max at 0°, 32 at ±80°),
ours the 26° nib's (max at +20°, 53–61 at ±80°) -- **for the owner's
ruling.** Proof `fjord-phase3-DBPR.html`; the specimen carries the build.
