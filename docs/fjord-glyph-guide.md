# Drawing glyphs for Albo (Fjord until round 58): the guide for the next agent

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

## 00. The target, restated by the owner (2026-09-13, round 58)

**Ruled the same day:** the family is **Albo**, and the bowls are profile B,
"Albertus-like firm" -- w = hair + (max - hair)·|sin φ|^1.6 with hair 0.70
stem, max 1.00 stem, vertical stress, joins into stems tapering to 0.85 of the
hair, round end k 1.9 -- the default in `outlines/primitives.py`
(`DEFAULT_BOWL`). **Round 62 defaults (owner, from the sliders): stem 84, contrast 0.80, asc 770, desc 256, xh 429, cut 115, width 100, serif 100** -- every number below that says 82 or 94 for the stem, 0.60 for the contrast, 415 for the x-height, 762/250 for the extenders is history; `outlines/pen.py` is the authority. **Albo is a variable font too** (round 61): every design constant a new glyph reads from `pen.py` (S, XH, ASC, DESC, WF, WL, WD, the pen) is an axis master's parameter, so a glyph must be drawn FROM those names and never from a literal, or it will not move with the sliders; and its topology (contour count) must hold across the axis ranges in the STATE section of the exploration doc, or `variable.py` clamps that glyph. **Stem 94** (round 59, from the weight ladder; the pen's
`stem` was 82 from round 1 to 58, and every "82" below is that history). This supersedes the round-57 bowl paragraph in §2 below,
which stays as the measured record of what was rejected.

**The goal, in his words (2026-09-13):** "make a wedge serif long text
font for eink reading. build off of english word image, not individual
character. preserve any defects that help." Three consequences: every
judgment is made on words and sentences at 13 pt on the four-level e-ink
pipeline, never on a letter alone; a letter is right when the word image is
right; and an irregularity is not removed because it is irregular -- if it
helps the word read (a firmer join, an uneven stem, a heavier bottom) it stays,
and only he rules it a defect. Albertus Medium is on disk since round 58
(`scratchpad wedge/ref/Albertus-Medium.ttf`) as the STROKE reference:
measured O 1.40:1, D 1.18:1, arches never thinner than the stem, stems
flaring 5-8% toward their ends.

**"I am not interested in recreating Van den Keere, I am interested in
making a wedge serif like Albertus, but more readable."** That is the
identity, and it was the round-1 brief ("a humanist wedge serif like
Albertus and Icone"). Everything below that says "match Van den Keere" or
"match Garamond" is about PROPORTIONS and fitting only -- x-height, cap
height, widths, bearings -- never about the strokes' character. The strokes
are Albertus's kind: glyphic, chiselled, low contrast, stems that flare
toward their ends, terminals that widen into wedges, bowls with modest
contrast and no hairlines, open counters -- made more readable for a text
face at 13 pt. The round-57 garalde bowl profile (hairline tops and
bottoms, 2.7:1) is NOT the target; round 58 in the exploration doc records
what replaced it. Neither Albertus nor Icone is on disk: their character is
stated here and judged on the owner's picture, never fitted to a file.

## 0000. Standing rule: the space inside and between (owner, 2026-09-13)

Owner, verbatim: **"always pay attention to the space inside and between
characters."** Every glyph is judged, and every round reported, on its
counters and apertures (the space inside -- open enough at 13 pt on the
four-level pipeline, never a counter under 0.6 stem, the o's counter 1.036
wide over tall as the optical circle) AND on its fitting (the space between
-- sidebearings by the fitting rule, the rhythm of stems in a word, no
collision and no hole in a common pair). A variant page states both for each
variant; a ruling that moves weight, contrast, width or x-height is checked
for what it did to the counters and the fit before it ships. This is the
word-image goal (§00) made concrete: the word is its whites as much as its
blacks.

**Proof-page rule, hardened 2026-09-13 (owner: "fix image stretch issue with html previews"):** every `<img>` on a proof page is displayed with `width:100%;max-width:375px;height:auto;image-rendering:pixelated;display:block`. The `height:auto` is not optional -- an image that carries `width`/`height` attributes without it keeps the attribute's height while the width shrinks to the phone, and the block renders stretched (the weights page shipped that way). If the image is wider than 750 px, still `height:auto`.

## 000. Reference faces on disk, measured (2026-09-13)

Owner, sending ITC Berkeley Oldstyle (Medium, Bold, both italics, plus a
Berkeley Oldstyle Bold TTF), Miju Goudy (Goudy Oldstyle by way of Sorts Mill
Goudy and Sukhumala) and Cheltenham Classic: "these for reference as well for
what a goudy text face can be." So the references are now three kinds:
Albertus for the STROKE character; the Goudy faces for what a warm, wide,
low-x-height humanist TEXT face does on a page (rhythm, fitting, the softness
of joins, the ball-less terminals); Van den Keere and Garamond for
proportions. All in the scratchpad `wedge/ref/` (`Albertus-Medium.ttf`,
`ITCBerkeley-*.otf`, `Berkeley-Oldstyle-Bold.ttf`, `miju-goudy/`,
`cheltenham-classic/`). Measured the same way as Albertus (bowl_rays at 1000
px, 147 common words at 13 pt through the four-level pipeline); Albo's x reads
0.442 because its wedge tips sit above the 0.415 design x-height:

| face | xh / em | cap/xh | stem / xh | O thick:thin | D | o | n arch min (of stem) | page ink 13 pt | ink at black |
|---|---|---|---|---|---|---|---|---|---|
| ITC Berkeley Medium | 0.426 | 1.49 | 0.17 | 2.9 | 2.4 | 3.0 | 0.39 | 0.126 | 0.639 |
| ITC Berkeley Bold | 0.426 | 1.49 | 0.24 | 3.5 | 2.5 | 3.3 | 0.44 | 0.148 | 0.702 |
| Miju Goudy Regular | 0.425 | 1.67 | 0.17 | 2.2 | 2.3 | 2.7 | 0.53 | 0.120 | 0.640 |
| Cheltenham Classic | 0.421 | 1.73 | 0.23 | 2.4 | 2.0 | 2.2 | 0.54 | 0.151 | 0.705 |
| Cheltenham Classic Medium | 0.420 | 1.74 | 0.24 | 2.0 | 1.7 | 1.9 | 0.67 | 0.159 | 0.721 |
| Albertus Medium | 0.531 | 1.44 | 0.20 | 1.4 | 1.2 | 1.7 | 0.97 | 0.180 | 0.755 |
| Albo (B, stem 82) | 0.415 | 1.63 | 0.20 | 1.4 | 1.35 | 1.4 | 0.48 | 0.122 | 0.696 |
| Albo stem 94 | 0.415 | 1.63 | 0.23 | 1.4 | 1.35 | 1.4 | 0.48 | 0.132 | 0.726 |

What the Goudy faces say for Albo: their x-heights are ours (0.42-0.43), so
Albertus's 0.531 is the outlier and not a proportion to chase; their weight at
text size comes from stem/xh 0.23-0.25 in the Bold and Medium cuts (Albo's
stem-94 ladder step is exactly that band) and from arches that never thin
past half the stem (Albo's arches go to 0.48, Berkeley Medium's to 0.39 --
the one place a Goudy is thinner than we are); their bowl contrast (2-3.5:1)
is what the Albertus ruling rejects, so it is not copied. ITC Berkeley Medium
at 13 pt keeps the least ink at black of everything measured (0.639) -- the
readability cost of a 3:1 bowl on this pipeline, recorded so the garalde
profile is not re-proposed.

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
  `contrast` UP from 0.60 (hair = stem × (1 − contrast); round 53's first
  page had this backwards and its three blocks differed 3% the wrong way),
  to about 0.70–0.78 (the o's hairline from 0.130 xh to 0.113 / 0.105;
  Garamond is 0.075), still above Garamond's, -- **and then picked at 0.60,
  as now, from the corrected render** (2026-09-13). The contrast lever is
  closed with the descender's; the rebuild's pen is the current pen.
  and CHECKED ON THE READER'S FOUR-LEVEL PIPELINE (13 pt at 2x, 8x
  supersampled, quantized to 255/200/96/0) before it is ruled -- a true
  hairline breaks up on e-ink. This amends the §3 proportions row; the
  exact value is his call from a render of three contrasts.
- **Descender** (his answer): **pick from a render** -- before the glyphs
  are redrawn, set a paragraph at 13 pt on the 2x reader with the reader's
  line spacing in three builds, descender 250 / 290 / 330 (0.60 / 0.70 /
  0.78 of the ascender), the g p q j y and the line spacing both visible,
  and put the three on one Artifact page; his pick becomes the §3 row. The
  same page can carry the three contrasts of the previous point. **Picked:
  250** (round 53). The g p q j y stay short by design; the weight passes'
  "descender lever" is closed.
- **Delivery** (his answer): **the whole set first, then rounds** -- the
  agent redraws all 93 glyphs as designed outlines under the constraints
  above, ships ONE specimen (the standing URL, the running-text paragraphs,
  the overlays on the three references, the TTF), and from there the owner
  names what to fix, one ask per round, as rounds 25–51 ran. Not letter
  groups, not one glyph at a time, not competing candidates.

**Status (2026-09-13, round 54): the rebuild is built** --
`tools/wedge_serif/outlines/` is now the builder of the shipping font; its
`NOTES.md` is the record of every decision. The round-17/20 generator stays
as the reference construction. From here the owner's rounds by name apply to
`outlines/glyphs/*.py`, and §4's loop unchanged.

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

with the shipping design `stem` 82, `contrast` 0.60 -- `hair` = `stem` × (1 − `contrast`) = 33, so a HIGHER contrast number means THINNER thins --,
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

**The bowls do NOT follow the 26° nib -- measured, 2026-09-13.** The owner:
"take another pass at B and related characters because your understanding
is wrong." `tools/wedge_serif/bowl_rays.py` ray-casts a bowl's stroke
thickness by angle from its center. Van den Keere's D, P, B and O all peak
at 3 o'clock (vertical stress for the bowl strokes), symmetric above and
below, HEAVIER than the stem (97 against 82), and fall steeply to a true thin
at the top and bottom (32–46). The 26° pen gave a peak at 2 o'clock of 85
falling only to 60: a tube. Fitted bowl profile, θ from 3 o'clock:
`w = hair + (max − hair)·|cos θ|^1.28`, hair 0.42 stem, max 1.18 stem;
applied to D B P R in round 57; O C G Q and the lowercase bowls measure the
same in the reference and await the owner's ruling. The pen model of this
section is the reference for STEMS, DIAGONALS and ARCHES; the bowls have
their own measured profile.

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
| descender | 250, picked from the round-53 render against 290 and 330 | owner 2026-09-12 |
| overshoot of rounds | 14 units, measured at the INK'S EDGE | round 27 (it had been applied to the centerline and the rounds overshot 41) |
| overshoot of arches (n m h u) | 12 units at the ink's edge | round 30 ruling, from the arches page |
| lowercase width | 0.938 of the drawn widths; the o's counter 1.036 wide over tall | round 35 ruling; capitals untouched |
| stem | 82; capital stem 1.137 × | design; references' median |
| pen contrast | 0.60 (hair = 0.40 stem), picked from the round-53 render against 0.70 and 0.78 | owner 2026-09-13 |
| wedge family | table in §2 | round 30 |
| kick angles | A 65°, R 60°, k 56°, K 37° -- all different, by ruling | rounds 31, 32, 36 |
| arches | peak with their outer edge at xh + 12; leave the stem at 0.52 of the x-height with a trap notch | rounds 27, 30 |
| e | bar rising 5°, 0.72 of the pen's thickness at that angle, top at 0.62 xh, arm to 330°, blunt nose | round 39 dials + round 46 |
| g | G3: bowl rx 185 (the o is 226), 0.70 xh tall; loop rx 215 × 0.45 desc, 30 right of the bowl; neck from 242° dropping near-vertically into the loop at 150°, no floor; ear a pen stroke at 48° | rounds 40, 42 |
| J | no bar; the I's top wedge; hook starts at the stem's weight | round 36 (reversed the earlier "keep the bar" ruling) |
| D B P R | bowls are the D's ring: half-ring from the stem's inner edge, k × 1.12 (squared shoulders), counter's lower half lifted by 0.3 of the horizontal stroke | rounds 36, 47 |
| 8 | SHORTER than the ascending figures, both counters optical circles: the lower counter the 6's bowl counter's WIDTH at 1.036 wide over tall then x1.08 taller (`EIGHT_LOWER_TALL`), the upper 0.75 of the lower's width at 1.036 (`EIGHT_UPPER`); rings overlap by one bowl stroke (one waist band); bottom on the 0's line, top wherever the stack lands (~563 against the 6's 682); sides on the bowl profile unscaled; solved on the BUILT counter by `ring_for_counter`. His words: "make it shorter so counters can match other numerals or optical circles", "C wins but the bottom counter needs to be slightly taller", "1.08 wins" | rounds 66-69 |
| 1 | the flag's centerline ends buried 0.35 TH_V inside the stem (it ran 2 above the top, a nub); its tip takes a MICRO diagonal end wedge, 0.15 of the family's (`ONE_FLAG_WEDGE_SCALE`; owner: "1 needs a much smaller tip serif at top"); the flag itself on the bowl profile at 0.62 S so it is solid, not a pen hairline (it was the only free terminal among the figures with no serif) | round 77 |
| 2 | ONE stroke, chiselled: the round-49 arc continued by a STRAIGHT slash on the arc's own tangent (the arc's end angle solved so its tangent points at the base's left end), the arc at 0.82 of the profile and the slash growing to full by the base, the base bar 1.22 x the bar weight (`TWO_TOP_W`, `TWO_BASE_W`; owner: "rebalance 2 to be heavier on the bottom and lighter on the top"); lifted 8 units so the base bottoms on the baseline (`TWO_LIFT`; "push 2 back up to optical baseline"); the base the family's bar with its right wedge | round 81 |
| 3 | the lower counter opened halfway to the 5's: `THREE_BOT_RX` 0.62, `THREE_BOT_R` 0.315 -- counter 161 x 131 -> 187 x 137 (the 5's 215 x 143), 37 -> 51 white px at 54 px; advance 405 -> 433 because the 3's width multiplier sits at the solver's floor | round 77 |
| 4 | CLOSED again (round 82: "revert 4 to last closed version"; future todo from the owner: reduce the thickness of the 4's top-left stroke). The curved-open construction stays behind `FOUR_OPEN` / `FOUR_CURVED`: a cubic from a start clear of the stem's edge by 0.62 S, bowing left only 0.10 S (`FOUR_BOW`), at ONE weight (bowl profile floored 0.72 S, the pen cut at the start), arriving at the bar's left end running along it. Precedent measured on disk: Berkeley Oldstyle, Miju Goudy and Cheltenham bow it and round it into the bar; Dante, EB Garamond, Doves and Van den Keere keep a straight thin diagonal; all stand clear of the stem. A hooked, thin-started version was rejected as calligraphic. The straight-open and closed constructions are kept behind the constants | round 80 |
| 7 | the top-right corner is a MITRE: the bar's end face cut parallel to the diagonal and laid on its right edge, the diagonal starting inside the bar's band (the pen cut, the diagonal's square start and its proud right edge had made a spur with two notches) | round 77 |
| @ | the typical @ (owner: "FIGURE OUT WHAT A TYPICAL AT SYMBOL LOOKS LIKE AND TRY AGAIN"): measured on Berkeley, Albertus and the system faces, the stroke leaves the a's stem foot, hooks RIGHT and UP into the ring at 4 o'clock, climbs the right side, over the top, down the left, along the bottom, and ends at the lower right under where it began -- COUNTERCLOCKWISE (`AT_START_DEG` -38, `AT_SWEEP` 296). A single-storey a slanted 6 deg, its stem 0.40 rx right of centre; everything on the bowl profile. Six builds went the wrong way round first | round 81 |
| ? | the ORIGINAL question mark (rounds 19-76's seven-point hook) at Albertus weight (bowl profile floored 0.78 S) and 1.15 larger (`_q8`, `Q8_SCALE`, `Q8_FLOOR`; owner: "make the question mark back into its original question mark shape and albertus heavy, larger to read correctly in a sentence"); the seven others stay in `QUESTION_VARIANTS` | round 81 |
| K | round 51's K, untouched (owner, round 82: "leave K R Q M W as is, before agent was better") | round 82 |
| R | round 51's R, untouched (round 82) | round 82 |
| Q | round 42's Q, untouched (round 82; `Q_BELLY` stays at 1.0) | round 82 |
| M | round 51's M, untouched (round 82) | round 82 |
| W | round 51's W, untouched (round 82) | round 82 |
| S | the agent's bottom-left terminal at the top beak's 1.30 swell (owner: "keep S after") | round 77 |
| Z | the corners where the diagonal meets the bars: `Z_CORNER` 'blunt' (a bevel parallel to the diagonal, 0.45 S), 'mitre' (the bar run out to the diagonal's outer edge and cut on its line), 'wedge' (diagonal end wedges past the bars); **mitre ruled** (round 82: "Z mitre wins but extend the bottom right out to optically match the top's right edge") -- the bottom bar runs out to the top corner's x | round 82 |
| E, F | the top arm's wedge is its terminal, no pen cut on that end (the two fought: a double facet with an 8-unit ledge) | round 77 |
| k | the arm's end wedge at 1.15 of the family's diagonal end (`K_ARM_WEDGE`; owner round 84: "the top right serif needs to be slightly larger so visually balances and reads well"); arm 1.30, the leg off the arm's lower edge (round 75) | round 84 |
| z | the Z at x-height (owner round 84: "'z' is much worse ... I need better"): bars 0.62 S with the top's hanging wedge at the left and the bottom's rising wedge at the right, the DIAGONAL the heavy stroke at 1.05 S (Albertus and Berkeley both make it so), the corners mitred on the diagonal's outer edge, the bottom bar run out to the top corner's x (`Z_BAR`, `Z_DIAG` in diagonals.py) | round 84 |
| W (crown) | the apex crown at 0.6 of the family's wedge, seated 1.2 drops lower (`W_CROWN`, `W_CROWN_DROP`; owner: "lower and reduce the protuberance of the top middle connector") | round 84 |
| a (top right) | the stem stops at 0.66 xh and the hood takes over from 0.54 xh, leaning 22 wf right as it climbs, so the top right is the hood's curve, not the stem's corner (`A_STEM_TOP`, `A_HOOD_LEAN`; owner: "more of a curve than a rectangular corner") | round 84 |
| t | round 51's t restored (owner: "revert 't' before the triangle"): stem to xh + 95 sheared by the pen cut, plain bar, hooked tail | round 84 |
| x | the bottom-left serif (the thin diagonal's lower end) sized on the THICK diagonal's width at 1.15 of the family's diagonal end (`X_BL_WEDGE`, `X_BL_WIDTH`; owner 2026-09-14: "increase the visual weight of the bottom left serif in 'x'") | round 85 |
| e (arm) | `E_ARM_THIN` 0.92, no outward shift (owner 2026-09-14: "slightly reduce the visual weight of the bottom right tail stroke of 'e'"; 0.90 with a shift had been refused the day before) | round 85 |
| g (counter, neck) | the ear and the neck begin ON the ring's centerline and taper in (they began inside it and their square faces landed in the counter; owner: "clear out the inside counter of 'g' so it is an uninterrupted oval"); the neck on the bowl profile floored at 0.42 S with a 0.72 middle (`G_NECK`, `G_NECK_MID`; owner: "thin out the connector stroke between ovals in g to match the calligraphic style") | round 85 |
| z (bars) | `Z_BAR` 0.52 (was 0.62), the bars still aligned on the x-height and the baseline (owner: "slightly reduce the line thickness (while respecting the vertical grid) of the horizontal strokes in 'z'") | round 85 |
| 9 (join) | the tail's start sunk 8 units along the ring's radii (`NINE_JOIN_SINK`): the ring's outer fell to 381 and the tail's outer picked up at 386, a 4.6-unit re-entrant notch, now 0 | round 77 |
| 6 | the tail (the one thinning stroke, round 42) is floored at 0.55 of the stem through its run above the bowl, the floor under the pen before the profile, the tip's taper kept (`SIX_TAIL_FLOOR`; the tail thinned to 0.30 S = 1.5 px at 13 pt; he picked 0.55 from a ladder 0.55/0.70/0.85/1.00) | round 70 |
| 9 | round 71's flag-diag: the round-42 tail square-ended with a 0.9 x 0.9 diagonal end wedge rising from its upper corner at the tail's angle, tip 12.4 past the bowl; the tail thinned FROM ITS TOP EDGE to 0.60 of its width at the wedge end (`NINE_TAIL_TOP`), at full width where it leaves the ring and easing down over the first 70% of the run (`NINE_TAIL_EASE`), the 0.55 S floor binding at the thin end, bottom line and wedge fixed. His words: "flag-diag wins but it needs to thin out on top of tail to give more space", ".6 wins but the stroke needs to be thicker towards the loop", "eased over ~70% wins" | rounds 71-74 |
| & | round 68's round_bowl: open spiral top, the o's bowl below, the arm on a plain cut -- `g_ampersand` calls `ampersands.bred` with that entry's dials; the ten of round 67 and the ten bred of round 68 stay in `glyphs/ampersands.py` | rounds 67-72 |
| 5 | the top bar's rightmost ink ends 24 units INSIDE the bowl's rightmost ink (`FIVE_TOP_INSET = -24`; +11 was "much too far", the ladder -36/-24/-12/0 was built and he picked -24) | round 64 |
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
   never smooth-scaled) -- and MOBILE-FRIENDLY: he reads on a phone, and the
   artifact viewer squashes any image wider than the screen to fit. Render
   proof blocks 750 px wide, wrap the text to that width, and show them at
   `width:100%; max-width:375px; image-rendering:pixelated`, which on a 2x
   phone is one image pixel per screen pixel (round 53). A 1700 px sheet is
   for the desk only, the specimen republished at the standing URL, the
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
