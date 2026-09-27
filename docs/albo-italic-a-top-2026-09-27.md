# The italic a's top: where it is tallest, against Aldine and chancery references (2026-09-27)

Owner: *"need options to make italic 'a' droopier from the left top being the tallest point and matching historical references for handwritten and aldine a. try this time."*

## Measured (instruments/a_top_profile.py)

Each a rasterised at 600 ppem unhinted, unsheared by its OWN stem's slant (line fitted to the stem's left edge), top contour read per column. Heights in x-heights (the x's top), positions as a fraction of the unsheared ink width.

| a | top at 30% | crown (tallest) | at | valley at the stem join | stem top |
|---|---|---|---|---|---|
| Albo Italic, round 418 | 0.938 | 0.978 | 0.39 | 0.920 | 0.953 |
| Flanker Griffo Italic (Aldine) | 0.989 | 1.000 | 0.38 | 0.963 | 0.963 |
| Cancelleresca Bastarda (hand) | 0.978 | 0.996 | 0.36 | 0.982 | 0.996 |
| TeX Gyre Pagella Italic | 0.962 | 0.997 | 0.42 | 0.979 | 0.993 |
| Poetica | -- | -- | -- | -- | -- |

Poetica's slant fit failed (its stem's left edge is not a clean run at those rows); it is left out rather than reported wrong.

What the references share: the TALLEST point is the upper LEFT of the bowl (0.36-0.42 of the width), the top there is FULL (0.96-0.99 xh at 30% of the width), and the top falls from it to the stem. Albo's crown was already on the left but low, and its upper left fell away early (0.938) -- the top read as an arch rather than a shoulder.

## The lever

`ALBO_ALD_A_FLAT`, the handle length of the cubic that replaces the ring's top from the stem connector (58 deg) to the left side (186 deg), round 167. 0.34 as shipped; toward 0.55 the cubic reproduces the arc and past it bulges, which fills the upper left and moves the crown left. The valley at the join does not move with it, so the slope from the crown to the stem -- the droop -- lengthens. `ALBO_ALD_A_TOP` lowers the whole bowl to keep the crown near the x-height. The radial HAND pushes (`ALBO_ALD_A_HAND`) barely move the top: a 14-unit push at 140 deg moved the top at 30% by -0.005 -- the same finding as round 165's ten rejected droops.

Build-free evaluator: `instruments/a_top_eval.py` (draws from the builders UPRIGHT, so it must not re-straighten -- the first cut did and read the bowl's inner edge as the stem).

## Options drawn (Italic and BoldItalic; font-measured, Italic)

| option | env | top at 30% | crown at | valley | droop |
|---|---|---|---|---|---|
| today | -- | 0.938 | 0.978 @ 0.39 | 0.920 | 0.058 |
| Aldine (Flanker) | FLAT 0.55, TOP 445, HAND +10 at 60 deg | 0.978 | 0.996 @ 0.34 | 0.920 | 0.076 |
| chancery hand | FLAT 0.55, TOP 445 | 1.004 | 1.018 @ 0.35 | 0.891 | 0.127 |
| droopiest | FLAT 0.65, TOP 432 | 1.025 | 1.025 @ 0.30 | 0.862 | 0.164 |

All touch 0, hairs PASS in both italics. Not matched: the references' join is shallow (0.963-0.982); every option keeps Albo's deeper join (0.86-0.92).

## Rejected, and the correction (same day)

Owner on the three ring-dial options above: *"none are what i asked for. it needs to be almost triangular"*, then *"top right is the high corner"*, *"top left is not a corner"*, and *"yes but rounded. look at earlier provided reference and research yourself"*.

What the measurements above got wrong was the premise: "left top being the tallest point" was read as the BOWL's top left. The reference scan (`aldine_autofit.SOURCES['a']`, the owner's own crop of a printed Aldine a) shows it plainly: the high corner is the STEM's top, the stem stands well above the bowl, and the bowl is a small rounded TEARDROP hung on the stem, its point joining the stem below the stem's top, its left and bottom one round movement. No ring dial can make that -- a ring has no point -- so it is drawn.

`ALBO_ALD_A_TRI` (aldine.py `_a_tri`): an ellipse for the round, and a top edge that leaves the stem at `A_TRI_JY` and meets the ellipse TANGENTIALLY (aimed along the tangent from a point `A_TRI_BOW` above the join, so it bows up and still has no knee -- a catmull through a corner of points made one, and a straight tangent read as a hard wedge). Widths off the 50-degree nib by direction, averaged over +/-10 samples. Three drawings failed on the way and are the record: a hard triangle with the top-left as a corner (the premise the owner corrected), a straight-topped wedge with a knee at the turn, and a teardrop whose round ended short of the stem (a step at the join).

| option | join on the stem | top bow | round half-height |
|---|---|---|---|
| wdg | 0.82 xh | 0.07 xh | 0.31 xh |
| dro | 0.72 xh | 0.07 xh | 0.27 xh |
| rnd | 0.82 xh | 0.13 xh | 0.34 xh |

All touch 0, hairs PASS in both italics. Moves a and every a-built glyph (accents, ae, ordfeminine). Not done: the scan's stem top rises to the right (a flag); Albo's stays flat. `dro` sits low enough on its stem to start reading as a d.

## Three passes on the teardrop: fit, counter, contrast (same day)

Owner: *"take three passes and increase the fit and style. adjust size of counter and contrast. give me as many options as will likely help."* Instrument: `instruments/a_fit.py` -- from the builders, upright: colour (ink inside the x-height band / (ink width x xh)), counter (area of the holes), and a round letter's contrast (the heaviest run on a horizontal cut through the counter's centroid over the lightest run on a vertical cut through it).

**Pass 1, the finding.** `mid` (join 0.85), Italic: colour 0.379 against the d's 0.349 and the o's 0.344 (too dark); counter 38,258 against the d's 57,678 (0.66 -- a third too small; today's a is 50,282); contrast **0.91** against the o's 1.30 and the d's 1.95 -- INVERTED: the family's 50-degree nib puts the weight on the bottom and the hairline on the sides, where the d and q (their widths keyed by angle off Flanker) are heavy at the sides and thin at top and bottom.

**Pass 2, contrast.** `A_TRI_PHI`, the stress the widths are read at: 15 degrees gives 1.49 at the same weight; 0 and -15 are no better (1.49, 1.44) and darker.

**Pass 3, colour and counter together.** Thinner broad and hairline open the counter and lighten the letter at once; the round's width alone barely moves the counter, because the stem caps it. The Bold Italic needs its own values: the Italic's carried to it read colour 0.540 (d 0.481) and counter 0.69 of the d's.

| preset | Italic: colour / counter (x d) / contrast | BoldItalic: colour / counter (x d) / contrast |
|---|---|---|
| today | 0.398 / 0.87 / 1.64 | 0.527 / 0.82 / 1.60 |
| mid (last round) | 0.379 / 0.66 / 0.91 | 0.589 / 0.42 / 1.43 (at phi 15) |
| **fit** | 0.348 / 0.85 / 1.58 | 0.494 / 0.94 / 1.90 |
| opn | 0.361 / 0.90 / 1.55 | 0.507 / 0.98 / 1.98 |
| con | 0.364 / 0.82 / 1.67 | 0.514 / 0.88 / 1.99 |
| trg | 0.333 / 0.77 / 1.55 | 0.470 / 0.85 / 1.84 |

References for the targets: Italic d 0.349 / 57,678 / 1.95, o 0.344 / 57,596 / 1.30; BoldItalic d 0.481 / 43,077 / 1.89, o 0.473 / 39,598 / 1.16. Every preset: join 0.82 xh, bow 0.10, join weight 0.85, phi 15; (RY, RX, W, THIN) per weight in `_TRI_SET`. All touch 0, hairs PASS in both italics.

## Triangular, heavier, with line contrast (same day)

Owner: *"traingular wins but needs heaviness and line contrast"*. The contrast lever was not the hairline: at `A_TRI_SMOOTH` 10 (the +/-10-sample width average that removed the first drawing's bumps) thinning the hairline from 0.64 to 0.48 moved the contrast 1.63 -> 1.67 -- the average was eating the thins. At 6 / 5 / 4 samples it reads 2.11 / 2.44 / 2.88. With the average short, the heavy return poked past the stem's right edge; a width cap on the return's second half (no point may reach past the stem's right edge, eased) removed it.

| ladder | Italic W / THIN / SMOOTH -> colour, contrast | BoldItalic W / THIN / SMOOTH -> colour, contrast |
|---|---|---|
| trg | 1.25 / 0.80 / 10 -> 0.333, 1.55 | 0.95 / 0.75 / 10 -> 0.470, 1.84 |
| h1 | 1.40 / 0.64 / 6 -> 0.342, 2.11 | 1.06 / 0.60 / 6 -> 0.474, 1.86 |
| h2 | 1.55 / 0.56 / 5 -> 0.355, 2.44 | 1.16 / 0.52 / 5 -> 0.488, 2.04 |
| h3 | 1.70 / 0.45 / 4 -> 0.368, 2.88 | 1.26 / 0.45 / 4 -> 0.502, 2.22 |

All touch 0, hairs PASS in both italics.

## The glob join, the bulge, the x-height (same day)

Owner: *"2.4 wins but it needs to bulge out a bit toward the top left and the top right corner needs to be a stylish glob join and it all needs to optically line up with x height for readable word image"*. Base: h2 (Italic W 1.55 / THIN 0.56 / SMOOTH 5; BoldItalic 1.16 / 0.52 / 5).

- `A_TRI_GLOB` -- a disc of this x the stem's width whose top sits on the o's top (`A_TRI_OTOP`, 436 units, both italics); the bowl's point runs into its centre, and the STEM STOPS AT THE GLOB'S CENTRE. The first cut left the stem's flat top standing and the disc showed as a bump above it; making the glob the stem's head is what reads as a join.
- `A_TRI_TOPFIT` -- the top edge's bow is SOLVED (bisection) so the bowl's own ink top, glob excluded, lands this many units above the o's top; 0 = on it.
- `A_TRI_BIAS` -- where the bow peaks: the cubic's first handle at this fraction toward the round; 0.55-0.70 carries the bulge toward the top left.

Built fonts, ink tops (a / o): 444-446 / 442 in the Italic, 444 / 444 in the BoldItalic -- within 4 units, under a tenth of a pixel at reading size. The stem no longer stands above the bowl, which is what had started the teardrop reading as a d.

| option | GLOB / BIAS | Italic colour, counter, contrast | BoldItalic colour, counter, contrast |
|---|---|---|---|
| g1 | 0.62 / 0.55 | 0.377, 45,902, 2.41 | 0.502, 34,086, 2.06 |
| g2 | 0.75 / 0.55 | 0.378, 45,485, 2.40 | 0.506, 33,296, 2.04 |
| g3 | 0.62 / 0.70 | 0.372, 44,439, 2.41 | 0.493, 33,252, 2.05 |

All touch 0, hairs PASS in both italics.

## Ascender and stress (same day)

Owner: *"the bigger glob wins but needs a small ascender, and the top left should be thin where the bottom left should be thick"* (and: *"please always uniquely label choices so i can refer to them"* -- options below carry their page labels). Base: g2 (glob 0.75).

- `A_TRI_ASC` -- the stem stands this many units above the o's top, over the glob. With the stem rising past it the centred glob stood out as a KNOB on the stem's right; under an ascender the glob now sits flush with the stem's right edge and swells only toward the bowl.
- The stress for "top left thin, bottom left thick" is the family nib's own neighbourhood: `A_TRI_PHI` 40-60 (the three-pass 15 made the sides heavy and top/bottom thin, which put weight on the top left).

| label | ASC | PHI |
|---|---|---|
| C1 | 20 | 50 |
| C2 | 35 | 50 |
| C3 | 50 | 50 |
| D1 | 35 | 40 |
| D2 | 35 | 60 |

All touch 0, hairs PASS in both italics.

## B's word image on C2, the heel, top-left = bottom-right (same day)

Owner: *"match B word image better with a less thin top left line than showed, C2 with a globbier feel, add more area under bottom join to make a globby heel without to much visual weight (bottom right stroke of bowl should match top left)"*.

- On a broad pen the top-left (running down-left, 225 deg) and the bottom-right (running up-right, 45 deg) are the SAME axis, so the nib gives them the same width at any stress; `A_TRI_PHI` 45 is the stress that makes both the thins. They measured unequal (C2: 21.3 against 26.2) because the WIDTH AVERAGE pulled the bottom-right toward the heavy bottom beside it. Cutting the average to 2 samples matched them (21.3 / 21.6) but brought the edge bumps back.
- `A_TRI_DIRSM` smooths the pen's DIRECTION and reads the width off it: the thins stay thin, the edge stays smooth, and the two ends match -- 24.3 / 23.6 at hairline 1.20, 27.0 / 26.4 at 1.35 (C2's top-left was 21.3).
- `A_TRI_HEEL`: a disc x the stem's width, sitting on the baseline against the stem's left edge, filling under the bowl's return. The first placement (0.16 xh) put it INSIDE the counter as a separate dot.

| label | Italic THIN / GLOB / HEEL | BoldItalic THIN / GLOB / HEEL |
|---|---|---|
| E1 | 1.20 / 0.85 / 0.55 | 1.10 / 0.85 / 0.55 |
| E2 | 1.35 / 0.85 / 0.55 | 1.25 / 0.85 / 0.55 |
| E3 | 1.20 / 1.00 / 0.55 | 1.10 / 1.00 / 0.55 |
| E4 | 1.20 / 0.85 / 0.75 | 1.10 / 0.85 / 0.75 |

Common: ASC 35, PHI 45, DIRSM 8, BIAS 0.55, TOPFIT 0; W 1.55 Italic / 1.16 BoldItalic. All touch 0, hairs PASS.

## Reread: the cutout under the bottom join (same day)

Owner: *"reread my prompt, you went the wrong way with it and the little cutout on the bottom is gone, not bigger. look at reference image for what I meant."* "Add more area under bottom join" meant MORE WHITE: the small notch left of the stem, under where the bowl's bottom rejoins it -- the scan has it clearly, with the stem's foot spreading into a heel below. The E options' heel disc sat in exactly that notch and filled it. Now:

- `A_TRI_HEEL` moved to the stem's FOOT (centre just right of the stem's axis, on the baseline), so it never reaches up into the notch.
- The notch is opened by ending the round sooner (`A_TRI_T1`, the angle the return leaves the ellipse; 352 before), raising where the return enters the stem (`A_TRI_KY`), and narrowing the round (`A_TRI_RX`) so the return has to climb a diagonal into the stem. Measured by `instruments/a_cutout.py` (white left of the stem's left edge, baseline to 90 units, outside the counter): C2 672 units^2; T1/KY alone barely moved it (587-683) -- the round's bottom ran straight into the stem; with RX it opens: G1 1,882, G2 2,512, G3 3,191 (Italic). The BoldItalic's heavier strokes leave less: 347 / 598 / 969 / 574 for G1-G4.

| label | RX / T1 / KY / HEEL |
|---|---|
| G1 | 0.40 / 320 / 0.18 / -- |
| G2 | 0.38 / 315 / 0.22 / 0.55 |
| G3 | 0.36 / 310 / 0.26 / 0.55 |
| G4 | 0.38 / 315 / 0.22 / 0.70 |

Common: E1's (THIN 1.20 Italic / 1.10 BoldItalic, GLOB 0.85, ASC 35, PHI 45, DIRSM 8). All touch 0, hairs PASS.
