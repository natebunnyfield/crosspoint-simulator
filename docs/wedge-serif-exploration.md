# Wedge-serif exploration ("fjord")

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
