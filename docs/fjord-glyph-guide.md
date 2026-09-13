# Drawing glyphs for Fjord: the guide for the next agent

Fjord is a humanist wedge-serif text face for the CrossPoint reader, built
by code, not by hand: every glyph is Python that draws strokes with a
broad-nib pen model and hands polygons to a TrueType builder. This guide is
what an agent (Sonnet or any other) needs to add or redraw a glyph so that it
reads as the same hand and sets into even, harmonious words. It is the
current state as of 2026-09-12, round 51. The dated history and every
ruling's origin is `docs/wedge-serif-exploration.md`; the code map and the
traps are `tools/wedge_serif/README.md`. Read all three before touching a
glyph. Where this guide and a later round entry disagree, the later entry
wins; update this guide when that happens.

## 0. The next job: a full rebuild (owner, 2026-09-12)

Asked what the next agent will do first, the owner answered: **"full
rebuild as the current characters are crude."** So this guide is not a
manual for patching the round-51 glyphs; it is the record of the hand, the
proportions and the rulings that a rebuilt set must still obey, plus the
instruments that judge it. What "crude" points at, and what a rebuild keeps
versus redraws, is being asked of the owner one question at a time; the
answers land in this section as they arrive.

- **What is crude** (his answer, three of four offered): the STROKE
  CONSTRUCTION (strokes as offset polygons with buried ends and patched
  joins), the LETTER SHAPES (proportions and forms still off the
  references), and the SERIFS AND TERMINALS (the bracket wedges and cut ends
  read mechanical). NOT the cut: the faceted one-in-four linear outline is
  not what he means and stays.
- **How to draw the rebuild** (his answer): **designed outlines** -- each
  glyph drawn as its own contours with tuned control points, the way a type
  designer works; the pen model of §2 becomes the REFERENCE for weights and
  stress, not the generator; real joins, no buried ends, no patched
  junctions; the linear cut of §2 applied on top of the finished outline.
  Counters remain explicit reverse-wound contours (a hole is a contour
  wound the other way; nonzero fill). The stroke helpers of §2 are then the
  measuring stick (what thickness a stroke should have at an angle), the
  rulings of §3 stay the constraints, and §4's instruments still judge.
- **What stays fixed** (his answer, three of four offered): the
  PROPORTIONS (x-height 415, capitals 1.625 xh, ascender 762, descender 250,
  stem 82 and cap stem 1.137, contrast 0.60 at 26°, overshoots 14 and 12 at
  the ink's edge, lowercase width 0.938 / o counter 1.036); the RULINGS ON
  SPECIFIC LETTERS (the §3 table: G3 g, the e's dials, no J bar, the kick
  angles, the D-family bowls with the bottom opened, the 8 to the 6, the 3 to
  the 5, the two-sided I and U tops, the fitting rule and the spacing
  readout); and the WEDGE SERIF FAMILY (bracketed wedges at the round-30
  sizes, pointing where they point -- their curves may be redrawn, the
  family may not). Everything else -- the strokes' actual outlines, the
  joins, the terminals' curves, the bowls' shapes within their boxes -- is
  drawn again.
- **The shape references** (his answer, verbatim "garamond, garalde,
  edgar"): EB Garamond 400 (`scratchpad wedge/ref/EBGaramond-400.ttf`, fetch
  line in the exploration doc, round 24), the garaldes on disk -- Van den
  Keere and Dante MT in the reader repo's `lib/EpdFont/local_fonts/` -- and
  Edgar (same directory). Overlay every rebuilt glyph on all of them
  (`cmp_garamond.py`, `cmp_vdk.py`, and `overlay_stier.py` restricted to
  those faces); where they disagree, the garalde median is the target and
  the owner's picture decides.
- **Contrast** (his answer): **move toward the references** -- the pen's
  `contrast` from 0.60 to about 0.45 (thins 20–25% lighter; the o's hairline
  from 0.128 xh toward 0.10; Garamond is 0.075), still above Garamond's,
  and CHECKED ON THE READER'S FOUR-LEVEL PIPELINE (13 pt at 2x, 8x
  supersampled, quantized to 255/200/96/0) before it is ruled -- a true
  hairline breaks up on e-ink. This amends the §3 proportions row; the
  exact value is his call from a render of three contrasts.
- **Descender** (his answer): **pick from a render** -- before the glyphs
  are redrawn, set a paragraph at 13 pt on the 2x reader with the reader's
  line spacing in three builds, descender 250 / 290 / 330 (0.60 / 0.70 /
  0.78 of the ascender), the g p q j y and the line spacing both visible,
  and put the three on one Artifact page; his pick becomes the §3 row. The
  same page can carry the three contrasts of the previous point.
- **Delivery** (his answer): **the whole set first, then rounds** -- the
  agent redraws all 93 glyphs as designed outlines under the constraints
  above, ships ONE specimen (the standing URL, the running-text paragraphs,
  the overlays on the three references, the TTF), and from there the owner
  names what to fix, one ask per round, as rounds 25–51 ran. Not letter
  groups, not one glyph at a time, not competing candidates.

**The rebuild's order of work, then:** (1) the contrast and descender
render, his two picks; (2) the whole set as designed outlines, the pen as
the weight reference, the wedge family kept, the §3 rulings kept, every
glyph overlaid on Garamond, Van den Keere, Dante and Edgar as it is drawn;
(3) the linear cut applied; (4) the fitting rule and the o-counter check;
(5) one specimen, the TTF, a doc round with every number; (6) his rounds.

## 1. What you are making, and for whom

- A **text face for longform reading** on an e-ink panel at 13 pt on a 2x
  render (a 54 px em) and on the iOS app. Not a display face. Everything is
  judged at reading size in sentences, then checked large for joins.
- **Vector TrueType only.** The deliverable is `Fjord-Regular.ttf`, built by
  `tools/wedge_serif/round20.py`. No raster tricks, no bitmap treatments.
- **The owner judges pictures, never prose.** Every change ships as a
  before/after PNG at native pixels (an Artifact page), the specimen page
  republished at its standing URL, and the TTF sent. A description of a
  change is not a deliverable; a render is.
- **He decides what is fixed.** Defects can be charm. When he asks for
  options, diverge (make distinct designs he can pick from); when he rules,
  converge on the ruling; never narrow a population on your own judgment,
  never "improve" a letter he did not name.

## 2. The hand: the pen model (the brush strokes)

Every stroke is the path of a broad nib. `alphabet2.Pen(stem, contrast,
stress, power)` gives the stroke's thickness from the tangent angle φ of the
centerline:

    thickness(φ) = hair + (stem − hair) · |sin(φ − stress)| ^ power

with the shipping design `stem` 82, `contrast` 0.60 (so `hair` = 49),
`stress` 26° and `power` 0.95. In practice: a vertical runs 77 units, a
horizontal 55, a 45° down-right diagonal 79, a down-LEFT diagonal thins
toward the hairline. That last fact shapes several letters: a neck or a leg
running down-left (the g's neck, the K's and R's legs, the j's tail) thins
to nothing on the pen alone, so those strokes either take a **weight floor**
(a profile that never drops below a fraction of the stem: the K's arm 0.47,
the R's leg 1.05, the j's tail 0.6 through its turn) or are **routed** so the
nib is broad along them (the G3 g's neck drops near-vertically before it
turns, and carries no floor). Prefer routing to floors: a floor is a patch on
the hand, a route is the hand.

`A.outline(pts, pen, profile, cut0, cut1)` turns a centerline (a list of
points from `line`, `bez`, `ellipse`, `catmull`) into one polygon: the pen's
thickness at each point, times `profile(t)` in 0..1 along the stroke. The
profiles compose (`compose(f, g)`):

- `taper_in(amount, span)` / `taper_out(amount, span)`: thin to
  (1 − amount) over the first/last `span` of the stroke. Joins into another
  stroke taper in; terminals that end in a point taper out.
- `flare_end(amount, span)`: swell toward the end. Humanist terminals
  thicken before the cut.
- `entasis(amount)`: stems swell at both ends (design `flare` 0.14); the
  stroke that meets a stem's end must match that swell or a jog shows (the
  U's bowl does this with a bump over its first and last 15%).
- `cut0`/`cut1`: shear the end face to the pen angle (design `cut_deg` 20).
  A pen cut on a thin terminal makes a thorn; the C, S and lower terminals
  now end square with a flare, or in a beak.

The font is built through **`round17.pen_linear`**, the "hand-cut linear"
pen: it draws the same outline, removes the folds where the outline crosses
itself, then keeps one vertex in four on each side (seed 73, no jitter) --
that decimation IS the cut, the slightly faceted line the owner chose in
round 18. Both end faces of every stroke are kept (round 26; dropping the
first sample ate the start of every stroke and broke the j). A post-op
(`round17.Cut`) grows polygons a few units so joins re-close, and rounds any
polygon under 20 vertices -- see the traps.

**Counters are punched, not stroked.** A bowl (o b d p q, the g's bowl and
loop, the e's eye, the D B P R bowls, the figures' bowls, the @'s ring) is
`round17.ring(c, cx, cy, rx, ry, a0, a1, n, k, cut)`: it returns the OUTER
contour (the pen's outer edge, cut) and the INNER contour (the pen's inner
edge, clean), and the inner goes into the font as a `Hole` -- a contour wound
the other way. So a bowl carries the pen's stress (thick sides, thin top and
bottom) automatically, and the counter is exactly the pen's inner edge. A
bowl that meets a stem is **kept to the stem**: the outer contour is closed a
hair INSIDE the stem's inner edge, the counter AT the stem's inner edge
(`round17.bowl_stem`, `latin._bowl_ring`), so nothing of the ring pokes past
the stem. Ink traps at the crotches are a tooth on the counter contour and a
notch on the stem polygon (`round17.cp_glyphs`), never a cut with a paper
polygon (a hole outside ink renders filled).

**Serifs** are `bracket_wedge(P, d, nrm, th, length, depth, side, drop,
fillet)`: a wedge that grows out of a stroke's end along a concave fillet
(`fillet` 0.65). One family of sizes, in units of the design's `wedge_len`
(0.85 stem = 70 units) and `wedge_depth` (1.7 stem = 139 units):

| where | length × depth | side |
|---|---|---|
| stem tops, lowercase and capital | 1.0 × 1.0 | one wedge, pointing LEFT on a left or single stem; pointing RIGHT on a right-hand stem (H N U right stems, `top="right"`); the U's right stem and the I add a small wedge the other way (0.4 × 0.6, `right+` / `left+`) |
| stem feet | 0.85 × 1.0 | both sides on a single stem; `foot="left"` where a bowl or bar occupies the right (B D E L P R) |
| diagonal ends (A V W X Y K k v w x y) | 0.9 × 0.9 | the outer side |
| bar ends (E F L T Z z) | 0.85 × 0.9 | hanging DOWN from a top bar, rising from a bottom bar |
| beaks on C G S (upper terminal) | 0.85 × 0.85 at 1.15 pen, after a swell into a near-vertical face | the lip hangs below |
| M and W apexes | 0.9 × 1.0 | |
| the g's ear, the r's arm | pen strokes, not wedges (the G3 g's ear leaves the shoulder at the nib's angle) | |

**Stems** are `alphabet2.stem` (lowercase, stem weight `s`) and
`latin._cstem` (capitals, `CAP_STEM` = 1.137 × `s`, the garalde references'
median), both with entasis and the wedges above. **Legs** (K R k) are
`latin.kick(c, P, J, s, angle, bury)`: drawn foot-first from the baseline as
the A's right leg is, full weight, wedge foot on the outer side, thinning
into the junction J and buried a fifth of a stem past it.

**Joins.** A stroke that meets another never lands its square end ON the
other's edge; it is BURIED a fifth to a third of a stem inside (the arm and
leg of the K, the bowls into stems, the N's diagonal into both stems, the
A's thin stroke under the apex, the W's thin strokes inside the thick ones).
Where a thick stroke enters a thinner one, the thick one tapers into the
junction (`taper0`/`taper1` on `diag`) so its end stays inside. Abutting
edges seam in FreeType; overlap by half a stroke. A stem that ends exactly
where its curve begins fractures; overlap.

## 3. The proportions and the rulings (the visual principles)

All in font units on a 1000 em. These are rulings, not defaults: change
none without the owner's word, and record any change in the exploration doc.

| | value | origin |
|---|---|---|
| x-height | 415 | B5.9 design |
| capital height | 1.625 × x-height = 674 | Garamond's ratio, round 26 (was 0.941 of the ascender = 1.73 xh; every cap read tall) |
| ascender | 762 (b d h k l); the f and t lower | design |
| descender | 250 today; the rebuild picks 250 / 290 / 330 from a render at reading size (§0) | design; owner 2026-09-12 |
| overshoot of rounds | 14 units, measured at the INK'S EDGE | round 27 (it had been applied to the centerline and the rounds overshot 41) |
| overshoot of arches (n m h u) | 12 units at the ink's edge | round 30 ruling, from the arches page |
| lowercase width | 0.938 of the drawn widths; the o's counter 1.036 wide over tall | round 35 ruling; capitals untouched |
| stem | 82; capital stem 1.137 × | design; references' median |
| pen contrast | 0.60 today; the rebuild moves it toward the references, about 0.45, value to be picked from a render on the reader's pipeline (§0) | design; owner 2026-09-12 |
| wedge family | table in §2 | round 30 |
| kick angles | A 65°, R 60°, k 56°, K 37° -- all different, by ruling | rounds 31, 32, 36 |
| arches | peak with their outer edge at xh + 12; leave the stem at 0.52 of the x-height with a trap notch | rounds 27, 30 |
| e | bar rising 5°, 0.72 of the pen's thickness at that angle, top at 0.62 xh, arm to 330°, blunt nose | round 39 dials + round 46 |
| g | G3: bowl rx 185 (the o is 226), 0.70 xh tall; loop rx 215 × 0.45 desc, 30 right of the bowl; neck from 242° dropping near-vertically into the loop at 150°, no floor; ear a pen stroke at 48° | rounds 40, 42 |
| J | no bar; the I's top wedge; hook starts at the stem's weight | round 36 (reversed the earlier "keep the bar" ruling) |
| D B P R | bowls are the D's ring: half-ring from the stem's inner edge, k × 1.12 (squared shoulders), counter's lower half lifted by 0.3 of the horizontal stroke | rounds 36, 47 |
| 8 | two rings sized to the 6's outer bowl proportion, lower 0.60 of the height, upper 0.50 | round 49 |
| 3 | lower bowl takes the 5's sweep and terminal | round 44 |
| figures | old-style, in the references' boxes (`latin.FIG_BOX`) | round 20 |
| j | no top flag; tail one round arc holding stem weight through the turn, thinning to a point | rounds 22, 25 |
| bowls of b d p q | kept to the stem | round 18 |
| the g's bowl | clear of overhanging shapes | round 19 |

**Fitting (how letters sit beside each other).** No kerning exists. Every
glyph's side bearings come from one rule (`round20.build`): the glyph's ink
is measured inside the x-height band (capitals: the cap band), the bearing
per side is `capbear × SIDE_FRACTION[type] + 17`, where `capbear` is half
the references' H bearing scaled to the cap height (≈30 units) and the side
types are straight 1.0, round 0.72, open 0.6, diagonal 0.45, punctuation
0.5 (`round19.SIDES` names each glyph's two sides). Non-letters and the g
are measured on their FULL extent (round 41: parentheses, slashes, the
question mark and the 3 and 5 had run past their advances). The f's hook
and the j's tail deliberately tuck under their neighbours. The word space is
1.7 n-counters minus 110 units (his readout). Capitals were ruled +34‰
letter-spacing and −110‰ word-spacing; the lowercase is fitted on the same
basis. **Do not make a spacing page**; he ruled it stopped.

**Rhythm.** The arches level with the rounds is what made words read even
(round 27: n m h had peaked 0.1 xh under the o and looked short). Weight per
letter has been measured twice against EB Garamond and Hoefler Text (rounds
36, 46): the remaining unevenness in common words is ascender count and
descender length, not stroke weight, and the two levers left are the
descender's length and the pen's contrast on the rounds -- both design
decisions for the owner, not fixes.

## 4. How a glyph is judged (harmonious word images)

The loop for any change: **edit → build → render → LOOK → measure → repeat**,
and the look is not optional; several fixes in this history passed every
number and failed the picture.

1. **Build**: `cd tools/wedge_serif && PYTHON_GIL=0 python3 round20.py
   <out_dir>` writes `Fjord-Regular.ttf` and `fjord-specimen.html` in about
   a second. Copy the previous TTF aside first as the "before".
2. **Render** with PIL at three sizes and look at each with the Read tool:
   - 13 pt on the 2x reader = 54 px em, in WORDS that contain the glyph
     with its usual neighbours (the exploration doc's rounds have lines to
     reuse; "egg", "ffi", "QU", "Kirk", "3.5%" are the collision cases);
   - 110–150 px x-height, the glyph in a word with a baseline and an
     x-height rule drawn, beside the same word in the reference face;
   - 600 px em or more for the joins: steps, notches, stubs, thorns.
3. **Measure**, with the instruments in `tools/wedge_serif/`:
   - `cmp_garamond.py` / `cmp_vdk.py`: every glyph overlaid on EB Garamond
     400 / Van den Keere at matched x-height, flags at width ±20%, height
     ±15%, mean stroke ±25%, top/bottom ±0.12 xh. Van den Keere is the
     current shape reference (round 42); Garamond the earlier one.
   - `overlay_stier.py`: the same over the nine humanist S-tier faces on
     disk; `fig_overlay.py`: the figures over their old-style sets.
   - `word_weight.py`: ink darkness per word and per letter at 54 px against
     the two references, plus outline area over the n's (compare AREAS
     between builds; raster darkness moves ±3% with the cut's phase).
   - the o's counter aspect (inner contour bbox) must stay 1.036; bearings
     on non-letters ≥ 20 a side; no contour of a glyph may cross into its
     own counter.
4. **Ship**: an Artifact page with the PNGs at native pixels (never JPEG,
   never smooth-scaled), the specimen republished at the standing URL, the
   TTF sent, a dated round entry appended to the exploration doc with the
   numbers, what was tried and failed, and what was left alone and why; then
   commit. One glyph or one ask per round.

**What "harmonious" has meant in practice.** The same hand: every stroke
from the same pen at the same stress; the same serif family at the same
sizes; joins that read as one stroke meeting another; rounds and arches
reaching the same overshoot; counters that are the pen's inner edge; the
figures' bowls in proportion to each other (the 8's to the 6's); bowls of
sibling letters built by one construction (B P R from the D's ring, the 3's
bottom from the 5's); nothing wider than its reference by more than the
family allows; no glyph whose ink runs past its advance unless ruled (f, j).

## 5. Recipe: adding a glyph

1. Find its family. A letter with a stem: `stem`/`_cstem` + wedges. A bowl:
   `ring` with a `Hole`, kept to its stem with `bowl_stem`/`_bowl_ring`. A
   diagonal: `diag`/`_diag` with `taper0`/`taper1` where it enters another
   stroke; a leg: `kick`. A bar: `bar(align="top"|"bottom")` so its edge,
   not its center, sits on the line. A terminal: flare + square end, or a
   beak (`_beak`), or a taper to a point; a pen cut only where the family
   already uses one.
2. Take the proportions from the nearest sibling and from the reference
   (measure Van den Keere's glyph with `cmp_vdk.py`'s overlay), never from
   taste: bowl radii, where the bar sits, where a leg springs from.
3. Draw with 40-sample lines or 100-sample arcs (anything decimating to
   under 20 vertices gets chamfered by the cut), bury every end that meets
   another stroke, keep bowls to their stems and counters clean.
4. Register it: lowercase in `alphabet2.GLYPHS` (and `round17.cp_glyphs` if
   it is one of o d b p q g e a -- those overrides are what the font uses);
   capitals, figures and marks in `latin.CAPS`/`FIGS`/`PUNCT`; its two side
   types in `round19.SIDES`; its character in `round19.CHARS` and the AGL
   name in `gname`. Figures get a `FIG_BOX` row. A new capital gets a width
   entry in `garalde_caps.json` if the solver is to size it.
5. Build, render at the three sizes, look, measure, ship as in §4.

For accents (not yet drawn: Latin-1 and Extended-A are the epub set), the
plan is composite marks on the same pen at the lowercase wedge's weight,
placed by a per-base anchor; nothing of that exists yet.

## 6. The bold: the next job (owner, 2026-09-12: "the bold" comes first)

The bold is a second WEIGHT of the same hand, not a new drawing. It comes
from the same code with different design parameters and the same rulings;
where a construction breaks under the heavier pen, the fix goes into the
shared code with a knob, never into a bold-only copy of a glyph.

1. **Parameters** (`round20.build(out_dir, style="Bold", over={...})`; start
   from `round4.bold_of` and measure): `stem` 82 → about 130 (×1.6), `contrast`
   0.60 → about 0.48 (the thins grow less than the thicks), `width` and
   `lc_width` × about 1.05 (a bold is a little wider), `n_width` unchanged --
   the n's stem-to-stem distance already grows with the stem
   (`nw = n_width·width + 0.9·(stem − 110)`), or its counter and, through the
   fitting rule, every letter gap close up. `CAP_STEM` stays 1.137 ×. Wedge
   sizes are in stem units and scale with it; check they do not read huge.
2. **What breaks first under a heavy pen, from this history**: counters --
   the o's counter aspect must stay 1.036 (solve `lc_width` for it, as round
   35 did); the e's eye (bar at 0.62 xh, 0.72 of the pen: the eye may close
   at 54 px -- measure it, and if it closes the bar's height or the eye's
   size is the owner's call, not the bar's thickness); the g's loop and neck
   (the neck is routed, not floored -- at a heavier stem it may need routing
   again); the a's bowl; the B's waist; every junction buried "a fifth of a
   stem" now buries more -- check the K arm, the R leg and the N for
   poke-through at 600 px; the ink traps (0.6 stem deep) start to show.
3. **Fitting**: the bearing rule is in cap-height units and does not change;
   the word space is 1.7 n-counters − 110, so it shrinks with the counter --
   measure a paragraph at 54 px against the regular's and expect to re-rule
   the word space with the owner.
4. **Judging**: the regular and the bold on the same line at 54 px (a bold
   word inside regular text is how a reader meets it); the darkness pass
   (`word_weight.py`) on the bold against the regular, not against Garamond;
   the S-tier overlay against the bolds of the same faces where they exist
   on disk (Dante, Van den Keere, Edgar have bolds in `local_fonts/`).
5. **Ship** as `Fjord-Bold.ttf` beside the regular, the specimen showing
   both, and the doc round recording every parameter and every construction
   knob added.

## 7. Open items, in the owner's court

- The bold is §6; the italic does not exist.
- Accents; kerning; hinting; vertical metrics for the reader's line.
- The pen's contrast (thins 70% heavier than Garamond's) and the descender
  length -- the two levers the weight passes found and did not pull.
- Ink traps at 0.6 stem are invisible at text size (rounds 18, 19).
- The `Cut` chamfer on diagonals under 20 vertices (round 36 trap): fixing
  `diag` to 40 samples touches every diagonal capital.
- The reader route (README, "Taking a font to the reader").
