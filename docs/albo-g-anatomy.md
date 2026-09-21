# The binocular g, measured — the scan, Flanker, Pagella, and Albo

2026-09-16. Owner: *"do a better job connecting the ear of 'g', refer to scans
and reference fonts"*, then *"redo 'g' based on flanker, pagella and the scan
detail"*.

The instrument is **`tools/wedge_serif/cmp_aldine_g.py`**. Re-run it rather than
trusting a number copied out of here:

```
PYTHON_GIL=0 python3 cmp_aldine_g.py --xh 400 \
    --ttf refs/flanker-griffo-italic.otf --ttf refs/texgyrepagella-italic.otf \
    --ttf <built>/Albo-Italic.ttf
```

## Why it measures a raster

Every other Albo instrument measures outlines, which is right while the
reference is a font. One of the three references here is a **photograph of a
printed page**, and a figure taken off a Bézier is not comparable with one
taken off ink unless the same procedure produced both. So everything is
measured on a bitmap at a fixed x-height, whatever it was drawn from — a font
is rendered to one, the scan crop is thresholded into one — and the two then
answer the same questions. This is `aldine_targets.py`'s doctrine applied to a
letter that needed it.

## What the scan cannot say, and why

**The g of "rodigium" touches the following i.** The ear runs right out of the
bowl's top and the i descends from the x-line to the baseline exactly where the
ear is going; on the page they are one blob of ink. A crop wide enough to hold
the whole ear holds most of an i with it — measured that way the g came out
**756 units wide with a 304-unit "ear"**, which is an i. The crop therefore
stops at x 271 and the scan is asked only what it can answer alone: the two
counters, the neck, and the stroke weights. **The ear's reach, depth and angle
come from Flanker and Pagella**, which are outlines with no neighbour touching
them. That is a limit of this evidence, not a judgment about the ear.

## The measurement

All figures in Albo design units, x-height 429, unsheared, at a 400 px raster.

| | the scan | Flanker | Pagella | Albo BEFORE | Albo r176 |
|---|---|---|---|---|---|
| bowl counter w × h | 177 × 284 | 240 × 313 | 183 × 226 | 195 × 257 | 195 × 257 |
| loop counter w × h | 316 × 227 | 262 × 247 | 236 × 202 | 315 × **150** | 319 × **207** |
| **loop/bowl counter h** | **0.80** | **0.79** | 0.89 | **0.58** | **0.80** |
| bowl stroke L / R | 54 / 70 | 72 / 68 | 54 / 58 | 69 / 65 | 69 / 65 |
| loop stroke L / R | 70 / — | 73 / 49 | 49 / 58 | 75 / 27 | 75 / 26 |
| **neck ink at the waist** | **90** | **84** | 50 | **45** | **78** |
| **crown x, frac of width** | **0.52** | **0.70** | 0.65 | **0.85** | **0.68** |
| ear reach past the crown | 184 | 199 | 182 | **95** | 205 |
| ear drop below the crown | 32 | 17 | 42 | 50 | 42 |
| ear depth, mid | — | 128 | 107 | 62 | 123 |
| ear top slope, deg | −9.9 | −4.9 | −13 | **−28** | −12 |

## The three faults it named

1. **The loop's counter was half shut** — 150 units against a bowl of 257, a
   ratio of 0.58 where all three references hold about four fifths. The loop's
   outer cannot go lower (it is already on the descender), so the room came
   from its top rising (`G_LTOP` −20 → 14) and its own ring thinning at the two
   ends the pen travels fastest through (`G_LRING` 90: 50 → 38, 270: 72 → 58).

2. **The neck was too thin at the waist** — 45 against the scan's 90 and
   Flanker's 84. Round 173 thinned it on the owner's instruction, and that
   instruction was about an **overrun into the counter** rather than about
   colour; round 174's trim cures the overrun, so the weight goes back toward
   the references without the fault coming with it. `G_NECK_SCALE` 0.80 → 1.15.

3. **The letter's highest ink was the ear's own tip**, out at 0.85 of the
   width, because the ear was launched off the bowl's upper-right flank at −28°.
   In all three references the highest ink is the **bowl**, at 0.52–0.70, and
   the ear then leaves it nearly level. That is the whole of "stuck on": a
   stroke standing above the letter instead of leaving it.

## The negative result worth keeping: moving the root did NOT fix it

The obvious fix for fault 3 — root the ear further left, onto the crown — was
built at 0.12, 0.28 and 0.40 × the bowl's rx and **every one of them opened a
notch**. Up on the crown the ring's own tangent is horizontal, the ear's
underside runs along it, and two edges grazing at a few degrees leave a concave
white wedge where they cross. `cmp_aldine_glitch` passes all three, because a
wedge like that is one contour and not two islands — it has to be looked at.

So the root **stays out on the upper-right flank**, where the ring's outward
normal is nearly perpendicular to the ear and the union is an honest
T-junction, which is where it always was. What changed is the **slope**: the
ear leaves nearly level (a 12° fall against 28) and runs the reference's
distance, so its top edge stays under the crown for its whole length.

## The other negative result: the ear as a second ink island

At hand-cut depths of 20 units and up (round 175's ladder), the bowl's press
walked out from under the ear's root and the ear became a **detached second ink
island**, 7,060 units of blade off the letter's top right. `cmp_aldine_glitch`
caught that one; no proof image at reading size did. The ear's root now takes
the same radial displacement `keyed_ring` gives the bowl's contour at its own
angle, so the burial depth is constant at every hand depth.

## Dials

`G_LTOP`, `G_LRING`, `G_NECK_SCALE`, and the ear's `G_EAR_ROOT` / `G_EAR_RY` /
`G_EAR_Y` / `G_EAR_BOW` / `G_EAR_TIP`, all in
`tools/wedge_serif/outlines/glyphs/aldine.py` with their reasoning beside them.
Every one takes an `ALBO_ALD_*` env override.

---

# The lower loop — does it taper like a brush?

2026-09-16. Owner, with a fresh scan crop: *"compare scan to italic g. does the
bottom loop taper as a brush stroke would?"*

Instrument: **`tools/wedge_serif/cmp_g_loop.py`**. From the loop counter's
centroid a ray is walked outward every 5°; the ink run it crosses is the stroke's
width there, normalised by the counter's own radius so a photograph and an
outline compare. **The 70–120° sector is excluded** — that is where the neck
crosses the ring, and a ray there measures the neck instead of the loop.

| | contrast (thick/thin) | change per 5° (×100) | thickest at | thinnest at |
|---|---|---|---|---|
| the scan | **12.3 : 1** | **7.6** | 180° (left) | 345° |
| Flanker | 4.1 : 1 | 2.7 | 40° | 290° |
| Coelacanth | 4.4 : 1 | 3.6 | 40° | 125° |
| Pagella | 4.3 : 1 | 2.9 | 65° | 290° |
| **Albo** | 3.9 : 1 | **2.1** | 205° | **0° (right)** |

Coelacanth Italic was added to `refs/` on the owner's instruction after this was
first measured, and it does not change the finding — it agrees with the other
two outline references and puts more distance between them and Albo on the
`change` column, which is the column that matters.

## The answer: barely, and not where it should

Albo's *contrast ratio* is in line with the two digital revivals — 3.9 against
4.2 and 4.0 — so on that number alone the loop looks fine. Three other readings
say it is not:

1. **Its change is the slowest of the four (2.1).** The width is more nearly
   constant round the ring than any reference, which is the signature of a
   compass rather than a brush.
2. **Its thin is in the wrong place.** Flanker and Pagella both put the thinnest
   point at 285–290° — the bottom-right, where the stroke is climbing back
   toward the neck and the pen is lifting. Albo's thinnest is at **0°**, dead
   right, and its right flank stays heavy all the way up.
3. **It never resolves to a hairline.** In both references and in the scan the
   loop *exits* thin — the stroke runs out as it returns to the neck. Albo's
   loop closes on itself as a ring of near-even weight; there is no lift.

The scan's 12.3 : 1 is inflated — it is one impression, with ink spread and a
thin that may be a near-break in the ink — so it should be read as a direction
and not as a target. The direction is unambiguous, and the two outline
references agree with it.

**Not fixed in this round.** `aldine.py` was owned by another task when this was
measured. The fix is `G_LRING`, the loop's keyed width table: its thin needs to
move from the right round to roughly 285°, and the run from the bottom up to the
neck needs to fall much further than it now does.


---

## CORRECTION, same day — the contrast figures above came from a bad instrument

The ray-from-the-counter's-centroid method used for the table above **produces
spurious zeros**: a ray that escapes through the neck, or through any gap in the
wall, returns a width of 0 and the contrast ratio computed from it is garbage.
It was caught reading Albo's `6` at 880:1 and the `g` at 544:1 on runs that
differed only in which sector was excluded. Three separate readings from it were
wrong by that mechanism.

**So the contrast column above (scan 12.3, Flanker 4.1, Coelacanth 4.4, Albo
3.9) should not be used, and neither should the claim that Albo's loop "changes
width most slowly".** Those were that instrument's output.

Re-measured with **local stroke thickness** — a chamfer distance transform over
the ink, the stroke's width at a point being twice the distance to the nearest
background, which shoots no rays and cannot escape — over the loop alone, below
the baseline, binned by angle about the loop's own centroid:

| | contrast | thickest at | thinnest at |
|---|---|---|---|
| Albo | 1.74 | 180–200° | **20°** |
| Coelacanth | 1.75 | 80° | **300°** |
| Flanker | 1.70 | 80° | **320°** |

**The three agree on how MUCH the loop varies — 1.70, 1.74, 1.75 — and disagree
entirely on WHERE.** Albo's loop is thickest on the left and thinnest on the
right; both references are thickest up at 80° and thinnest at the bottom-right,
300–320°, where the stroke sweeps up and out of the loop. Albo's own numeral
**6**, which the owner named as the target, thins in the same bottom-right place
the references do.

So the surviving finding is the one about POSITION, and the fix changes with it:
the loop does not need more contrast, it needs its **axis rotated roughly 100–120°**
so the thin lands where the pen is lifting. That is `G_LRING`'s keyed table,
re-phased rather than re-scaled.

---

# Round 182 — the brush strokes, and why every previous fix was the wrong lever

2026-09-17. Owner: *"copy off coelacanth for g until you understand how the
brush strokes underlie the form. take the time to get it fully and stop fucking
around."*

He is right that the preceding rounds were churn. `G_LRING` width tables, a
thin-at-angle dial, a run-out depth — all of them tuning **how wide** the stroke
is, when `docs/italic-g-strokes.md` had already written down the rule on
2026-09-14:

> When a stroke comes out the wrong weight, check its **direction** before its
> width. In a pen model the width **is** a function of where the stroke is going.

## The instrument

`tools/wedge_serif/cmp_g_strokes.py`. The glyph is rasterised unsheared; a
chamfer distance transform is taken over the ink; the ridge of that transform is
the stroke's centreline and the local thickness is twice the distance there; the
local direction comes from the principal axis of the neighbouring ridge points.
Binning thickness by direction gives **the pen's own signature**.

A face drawn on one pen has **one signature for the whole letter** — a run at
15° is thin wherever in the letter it happens. A face whose widths were declared
per-region does not.

**The instrument's own bug, which inverted its first answer:** the ridge test
kept only ink in the top 38% of the distance range. That is not a mild filter —
it *deletes every thin stroke from the sample*, because a thin stroke's distance
is small all along it. It reported Coelacanth's contrast as 1.50:1 with thin and
thick 45° apart; the real figures are below, and a broad nib must give 90°.

## What it found

| | bowl | loop | apart |
|---|---|---|---|
| Coelacanth | 15° | 30° | 15° |
| Flanker | 15° | 15° | **0°** |
| **Albo (before)** | **15°** | **75°** | **60°** |

Albo's bowl was already a real pen and agreed with both references exactly. **Its
loop was a different pen, 60° off its own bowl** — and the loop's profile was
not a pen curve at all but noise:

```
Albo loop   … 75  28  34  40 102  42 …     adjacent 15° bins
Coelacanth  … 52  78  94  93  90  88 …
```

That jumping is the fingerprint of a declared width table standing in for a pen,
and **no amount of re-tuning that table could have fixed it.**

## The cause

`keyed_ring` takes `keys` that declare a width **at an angle round the ring**. A
pen gives a width **for the direction the stroke runs**. On a circle those agree.
On this loop — a skewed egg, warped further by a hand-cut table — they do not.

## The fix

`keyed_ring` gains a `pen=(thick, thin_fraction, target)` option that takes its
widths from `nib_widths_closed` instead of the table, keeping the skew, the hand
table and the outer contour the neck-trim needs. Both the bowl and the loop now
use it — *one pen for the whole letter* is the claim, and a half-penned g does
not make it.

The bowl needed it too, and that is the subtle half: it was already **thin** in
the right place (15°) while its **thick** sat at 75° against Coelacanth's 105°.
A keyed table can land the thin correctly and still put the thick 30° away,
because in a table those are two independent entries and in a pen they are one
decision.

| | before | after | Coelacanth |
|---|---|---|---|
| whole letter | 0°/60°, 1.57:1 | **30°/120°, 2.83:1** | 15°/105°, 2.80:1 |
| thin↔thick | 60° apart | **90° apart** | 90° apart |

The contrast dial is set by measuring the built font, not by reading the number:
2.30 in measures 2.83 out, because the hand tables add on top and the ridge
sampling takes junctions in.

Gates: touch 0 of 5,193, metrics 0, cap weight 0, glitch 0 of 119, straight 38
of 62. With both pens off the font is round 181 to the bit — 0 of 119 glyphs
differ.

## The bowl's size, and the axis lever — 2026-09-17 (round 203)

The owner asked for a smaller top loop and for options that move the bowl's
axis. Both halves were measured before anything was drawn, and the second half
found the lever in a different place from where it was looked for.

**Size.** The bowl came down one notch, to **rx 144 / ry 152** (from 150/158,
−4%). That is not taste, it is the floor: the glitch gate reads the outline
pinching at the connector's join past about −5%, 2.2 units at −9% and worse at
−15%. Smaller than this needs the connector re-placed by hand, which is vertex
work in the bench and not a dial.

| | rx / ry | change | gate |
|---|---|---|---|
| round 202 | 150 / 158 | — | clean |
| **shipped** | **144 / 152** | −4% | clean |
| B | 136 / 143 | −9% | PINCH, 2.2 units |
| C | 128 / 135 | −15% | PINCH |

**Where each round letter is thickest**, so "in step with the others" is a
number rather than an impression:

| o | a | q | e | b | g bowl | d | g loop |
|---|---|---|---|---|---|---|---|
| 40° | 40° | 40° | 30° | 30° | 30° | 20° | 20° |

The bowl is **not** the outlier — it sits with the e and the b, in the middle of
a face that spans 20–40°. The letter at the edge is the **lower loop**, at 20°.

**`G_SKEW` does not move the axis.** Measured at four values: the thickest point
stayed at 30° in every one. Shearing a ring into an egg changes its shape, and a
pen-drawn ring takes its stress from the NIB, not from the ring — so the skew
moves where the ring is fat, never where the stroke is heavy. What it did do was
collapse the bowl's thin from 24 units to **4** past 0.16, which is the kind of
damage that reads as a broken letter rather than a moved axis.

The lever is the nib's angle, and `nib_widths_closed` had always taken one —
only the dial was missing. `ALBO_ALD_G_BOWL_PHI` and `ALBO_ALD_G_LOOP_PHI`
(both 50.0, the family's) are threaded through `keyed_ring(..., _phi=)`.
Verified on the built font: phi 38 → 30°, 50 → 30°, **64 → 40°**, which is the
o's. So the axis is now reachable per ring, and reachable in the bench
(`scratchpad/ged`, published) where the two rings have an axis and a contrast
slider each and the same live g is set into words.

Gates at the shipped values: glitch 0 of 119, touch 0 of 5,193.

## Even counters, smaller loops, and a welded connector — 2026-09-17 (rounds 204–205)

Three owner instructions in one arc, each with a measurement that changed what
was built.

### The counter is a shape, not the residue of the wall

*"smooth out counters to be even oval, handcut the letter slightly."*

`ring_from` builds a counter by pushing the outer inward by the stroke's width
at each point, so every step in the width table, every hand press and every fast
turn lands in the white as a facet. At the owner's contrast (3.25 bowl, 3.7
loop) that was most of what the counter was: the bowl had a point at its lower
left and a straight run down its right, the loop four flats.

`PR.ovalise` fits the counter's own ellipse (least-squares conic) and pulls each
point onto it, guarded so no point is pulled far enough to thin the wall past 16
units. The outer does not move, so ALL of the contrast now lives in the wall —
which is what a pen does: even white, uneven black. **The white is not paid
for**: bowl counter 31,110 → 31,018 design units, loop 49,538 → 49,608. The
ellipse averages the shape it replaces rather than shrinking it.

The handcut is `G_CUT`, a four-angle table pressed into the FINISHED oval,
alongside the existing `G_HAND` press on the outer. A ladder at 3/5/8 units of
counter cut (with 8/13/18 on the outer) costs 0.0% / 1.4% / 2.7% more ink; 3
ships.

### Each loop shrinks about the edge it is pinned by

*"anchor top loop to where current sits at top ... anchor bottom loop on top
sitting on baseline as it is now."*

`G_BSCALE` and `G_LSCALE`, both 0.9 as shipped. The bowl is scaled about its
CROWN (`G_CY + G_RY` held, the centre rises to meet it); the loop about its TOP
(`lt` held, `lb` raised), which is the edge resting on the baseline. Verified:
the loop's top holds at 72.4 → 72.5 units across the whole ladder.

**The scaling is applied on the DIALS, not at `keyed_ring`.** The connector's
start, its bowl-exit ride, the ear's root and the export each read
`G_CY`/`G_RX`/`G_RY` for themselves, so a scale applied at the ring shrinks the
bowl and leaves all four pointing at the ring it used to be.

**A literal vertex list cannot follow a ring that moves.** `G_NECK_PTS` is in
absolute design units, so the first shrink pulled the bowl's floor 18 units off
its first vertex and the glitch gate read the join closing to 2.24 units of ink.
Each vertex now takes the bowl's transform at the bowl end and the loop's at the
loop end, blended along the run (`G_NECK_FOLLOW`).

What the two scales bought and spent, measured at a 16 px x-height:

| | ring-to-ring white | bowl counter, short way | `eggy` vs the face's own descenders |
|---|---|---|---|
| round 204 | 1.62 px | 5.79 px | +30% |
| shipped, 0.9 / 0.9 | **2.74 px** | 4.77 px | **+16%** |
| (0.82 loop, laddered) | — | — | −1% |

"Reads evenly" was given a number: ink in the descender band against ink in the
x-height band, with `yappy` as the control, since the face already owns a
descender rhythm in its y and p. The loop reaches that rhythm at 0.82 and is
still 16% heavy at the owner's 0.9. Note 0.94 measured slightly WORSE than no
change at all — the loop narrows faster than it shallows, so the same ink lands
in a shorter band.

### The join was a crack, and only one of three cures worked

*"make sure the connector blends perfectly so it appears to be continuous
strokes."*

Walking the finished outline and measuring the turn over a ±6 sample window, the
worst corner at the joins was **141°**. Three cures, in the order tried:

| | worst join corner |
|---|---|
| abutted (round 204) | 141° |
| **weld** — each end moved onto the ring's own centreline, carrying the ring's wall | 139° |
| **+ tangent approach** — a control point on the ring's tangent | 59°, plus new kinks |
| **+ closing** — `geom.close_corners`, dilate 10 units then erode 10 | **45°** |

The weld barely moved the number and is still required: without it the closing
has a 141° corner to work on, and the weld's first version — aimed by the width
TABLE — put a tooth through the bowl's counter, because after `ovalise` the
table no longer describes the wall. The weld measures the BUILT contours
(`_RING_GEOM`) instead, taking the ring's real centreline and its real wall at
the angle the owner's own vertex names, and holds that wall across the whole
welded span so the band and the ring are the same width everywhere they overlap.

The **closing** is what actually closes a corner: a dilate-then-erode rounds
concave corners to the radius and returns convex ones where they were. Radius is
a ceiling rather than a taste — a closing bridges any white channel narrower
than twice its radius, and the white between the loops is 73.6 units; at 18 it
begins eating the open bay under the bowl. 10 costs 0.7% more ink.

The **tangent approach measured worse than doing nothing** and ships at 0
(`G_WELD_TANG`): the extra control point bends the span BEFORE the weld and the
catmull kinks there instead.

Gates on the shipped letter: glitch 0 of 119, touch 0 of 5,193.

**And an instrument note: md5 is not an identity test for these builds.** A font
carries a timestamp, so two byte-identical drawings hash differently. Compare
the glyph's `RecordingPen` output instead — that is what proved `G_BSCALE` /
`G_LSCALE` inert at 1.0.

## Round 227 — the italic g is redrawn in the roman's construction

Owner 2026-09-18: *"redraw 'g' to be the roman style of the italic 'g'"*, then
*"reduce far right extension ear of italic 'g' to improve legibility"*.

`ALBO_ALD_G_STYLE=roman` (the default now; `cursive` rebuilds the binocular g
of rounds 197–225 byte for byte). Measured on a correctly unsheared raster —
**`cmp_aldine_g.py` unsheared with the wrong sign until this round** (round
224's bug, in a third place: the roman g at slant 0 came out upright and every
italic leaned ~25°), so its width, crown and ear columns above this section
were taken on a doubly sheared g and are not comparable to these:

| | bowl counter | loop counter | ear past bowl | descender |
|---|---|---|---|---|
| cursive g (rounds 197–225) | 149 × 208 | 228 × 182 | **76** | −194 |
| **roman-style g (ships)** | 154 × 227 | 179 × 249 | **42** | **−305** |
| Albo roman g | 213 × 207 | 246 × 225 | 33 | −305 |
| Flanker | 174 × 314 | 265 × 247 | 55 | — |
| Pagella | 172 × 227 | 241 × 202 | 55 | — |

The ear was laddered 0.80 / 1.00 / 1.15 / 1.30 → 23 / 42 / 58 / 72: at 0.80 it
disappears at 13 px; 1.15 re-widens the letter; 1.30 is the fault. Loop depth
0.44 / 0.47 / 0.50 / 0.53 → −271 / −288 / −305 / −321; 0.50 is the roman's own
figure (p q −282, y −297). Pen signature: bowl and loop on one axis, 15°/105°
at 2.6–2.8:1 — the cursive arm had the loop on a second pen. Rounds 197/205's
"loop on the baseline" are superseded for the loop's depth by this ruling.

## Round 323 — the bent g is back, and the waist figure is not what it looks like

2026-09-21. Owner: *"there was a recent earlier version of italic g with a bend,
find and use that"*. That is the **cursive** arm, rounds 197–225, kept byte for
byte; `ALBO_ALD_G_STYLE` defaults to `cursive` again. Round 227 had replaced it
on his own instruction (*"redraw 'g' to be the roman style of the italic 'g'"*),
so this supersedes that round for the STYLE only — its Q ruling stands.

### "Neck ink at the waist" measures ALONG a flat connector

**The most important thing in this file.** `cmp_aldine_g.py`'s waist figure is
the **total ink on a row** between the two counters. Where the connector is
steep that is about its thickness; where it is FLAT — which is exactly what a
bend gives — the row runs along the stroke and the number inflates. The two
constructions here are not comparable on it, and round 322 recommended driving
the neck to a waist of 83 on the strength of that.

Measured PERPENDICULAR to the connector (chamfer ridge in the band between the
counters, x2), at xh 400 in Albo units:

| | perpendicular | the row figure |
|---|---|---|
| Flanker | **24** | 68 |
| Pagella | **22** | 26 |
| the bent g, as it ships | **24** | 40 |
| the roman arm (rounds 227–322) | 39 | 40 |
| bent g, `ALBO_ALD_G_NECK_W` 32 | 42 | 77 |
| bent g, `ALBO_ALD_G_NECK_W` 36 | 50 | 90 |

**The references' connectors are THIN, and the bent g already matches Flanker
exactly.** Following round 322's recommendation would have put Albo's connector
at roughly twice the reference. It ships unchanged.

### The loop came back with it

The roman arm had drifted to a loop counter **1.17** the bowl's width and
**1.06** its height — taller than the bowl, where all three references hold
about four fifths. The bent letter reads **1.55 / 0.88**, inside the reference
band (Flanker 1.53/0.79, Pagella 1.40/0.89). The S1b/S3b loop repairs built in
round 322 are unnecessary.

### Two corrections to round 322

1. `ALBO_ALD_G_NECK_W` is **not dead**. It reads 21 → 40, 32 → 78, 44 → 108
   once its own arm is selected. It does nothing only while another arm draws
   the letter, which is how it was first measured.
2. The waist recommendation above.

### Still open

The **roman** g is unchanged and still the stacked-circles construction, and it
has **no loop dials** — its radii are literals in `stems.py`. Giving it the same
loop means adding them first.

`ALBO_ALD_G_COMPOUND=1` and `ALBO_ALD_G_ONE_STROKE=1` render overlapping spurs
through the loop; they are faults, not alternatives.

Page: `claude.ai/artifact/X33i91w3AfcZoJXh9pa486`.

## Round 324 — the bent g built in the roman, and its shoulder cut back

2026-09-21. Owner: *"make a roman version of this, but reduce the lower loop
top heaviness"*. `ALBO_G_STYLE=bent` in `outlines/glyphs/stems.py`; `plain` is
the shipping letter and remains the default. Nothing is ported from `aldine` —
the construction is rebuilt on the roman's own pen and proportions.

### What was actually copied

Two properties, both measured off the italic rather than described: the loop is
**wide and shallow**, and the connector **dives left out of the bowl and bends**
into it instead of running down the letter's left wall.

| | loop/bowl w | loop/bowl h | width |
|---|---|---|---|
| roman today | 1.14 | 1.01 | 425 |
| **roman bent** | **1.34** | **0.79** | 461 |
| the italic bent g | 1.55 | 0.88 | 374 |
| Flanker | 1.53 | 0.79 | 408 |
| the scan | 1.79 | 0.80 | 390 |

The height ratio lands on Flanker and the scan exactly. The width ratio stops
at 1.34: reaching 1.53 widens a letter already at 461 units. A deliberate stop.

### THE HEAVINESS IS AT 150 DEGREES, NOT 55

The first cut was aimed at the upper RIGHT because that is where both reference
italics carry their mass — **which was reading their geometry onto a different
letter**. Their connector comes down the middle into the loop's top; this one
dives left and enters at the upper left, so the mass is where it lands. Wall
thickness ray-cast from the loop counter's centroid, 0 = east, 90 = top:

| | 0 | 30 | 60 | 90 | 120 | 150 | 180 | 210 |
|---|---|---|---|---|---|---|---|---|
| roman today | 69 | 54 | 37 | 33 | 38 | 53 | 68 | 54 |
| the italic bent g | 68 | 89 | 88 | 69 | 26 | 30 | 69 | 85 |
| Flanker | 48 | 69 | 71 | 82 | 27 | 48 | 35 | 61 |

`G_BENT_TOP_W` cuts the ring's own width on a raised cosine centred at
`G_BENT_TOP_AT` (150) over `G_BENT_TOP_ARC`, so the rest of the ring is
untouched. Measured at 150 degrees: **1.00 → 79, 0.80 → 69, 0.65 → 63,
0.50 → 57**.

### Two negative results

**`ALBO_G_BENT_PHI` cannot rotate the loop's stress and is left at 0.** At phi
0, 14 and −14 the wall reads 67/50/37/33, 66/44/36/36 and 65/58/44/36 at
0/30/60/90 — the thick stays due east and west. The family's bowl profile is a
function of how vertical the tangent is (round 58's switch), not of a nib
angle, so rotating the tangent handed to `bowl_th` changes the width but not
where the width falls. The dial is kept, documented, so this is not re-derived.

**The first dive failed the contour gate.** At `G_BENT_DIVE` 0.42 the neck
grazes the loop's outer left edge and leaves a **HAIR at (107, 9)** — a
reversal past 150° with a sub-8-unit arm. The plain roman g is CLEAN, so it was
introduced here. 0.36 clears it and is the default; entering the loop at 172°
instead of 163° also clears it, and the dive is the cheaper of the two because
the entry angle is what gives the elbow its shape.

### Also worth knowing

`ring_from(outer, widths_fn=...)` is how a ring gets per-angle widths: the
outer is pre-resampled here with `geom.resample` so the index the function is
handed maps back to a known point, which is the same trick the ampersand's ear
uses. `ring()` itself has no per-angle lever.

Page: `claude.ai/artifact/XmB9amhkmvtQBV8LAucPeW`.

### Round 325 — it ships

Owner, immediately after: *"need a roman bent g. please do what I keep
asking."* Round 324 built the letter and left it behind the flag for a ruling,
which was the mistake — the ask was for the letter, not for a ladder.
`ALBO_G_STYLE` defaults to **`bent`** and `ALBO_G_BENT_TOP_W` to **0.65**
(the loop's shoulder at 150 degrees: 79 → 63 units, below the plain g's own 68
at 180). `plain` still builds the letter that shipped up to round 324.

Verified on the default build: the `g` raises no `cmp_contour_hairs.py`
finding, and the whole-face `--letters` sweep returns the same rows it did
before the change — no new fault anywhere else in the roman.
