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
