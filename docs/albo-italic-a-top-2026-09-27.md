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

## Globby for word legibility: three passes on G4, measured by OCR (same day)

Owner: *"G4 wins but take multiple passes at making it globby in a way that helps legibility of words"*. Measure: the Kept Legibility Index v3.1 (github.com/JessieSalas/kept-legibility-index at `aff8fb3`, re-cloned; `ocr/visionocr` built from `visionocr.swift`), run through `etrace/kli_e.py` on the session venv (uharfbuzz), 22 s a run; `instruments/a_kli.py` reduces it to the a's confusions (a read as x, x read as a). The index calls a grand difference under about a point a tie; `crowded` moves several points between runs of the same font.

**The finding that drove all three passes: G4 is read as d.** Italic, Apple Vision:

| font | grand | crowded | a misread | top | read as a |
|---|---|---|---|---|---|
| today | 86.1 | 59.3 | 88 | a>o 34, a>e 22, a>u 19 | 102 |
| G4 | 86.4 | 64.7 | **116** | **a>d 88** | 100 |

The 35-unit ascender over the glob is a d's ascender at reading size.

- **Pass 1, the ascender.** 20: 50 misreads; **10: 36**; 0: 48 (a>d 15 -- with no stem above, the glob itself reads as a d's shoulder); 0 with a bigger glob: 52.
- **Pass 2, glob and heel at ascender 10.** Globbier helps: glob 1.00 + heel 0.90: **25** (read-as-a 94); heel 0.90 alone 31; glob 1.00 alone 33; glob 0.70 36; heel 0.55 41.
- **Pass 3.** glob 1.15 + heel 1.10: 26 (read-as-a 92, the fewest; grand 86.8, crowded 65.7); ascender 5: 24; ascender 15: 27; the wider cutout (RX 0.36): 28. A plateau near 25.
- **Second reader.** Tesseract 5 on the same images (`--tess`): no a confusion in any candidate's top eight; i>a 68-80 across all, the drawing's i, not the a.
- **BoldItalic reverses the glob.** today 40, **H1 14**, H4 19, H2 24, H3 28: the heavier glob reads as a d at the bold weight. The best glob is per weight.

| label | ASC / GLOB / HEEL | Italic a-misread | BoldItalic a-misread |
|---|---|---|---|
| H1 | 10 / 0.85 / 0.70 | 36 | 14 |
| H2 | 10 / 1.00 / 0.90 | 25 | 24 |
| H3 | 10 / 1.15 / 1.10 | 26 | 28 |
| H4 | 5 / 1.00 / 0.90 | 24 | 19 |

Common: G4's (RX 0.38, T1 315, KY 0.22, THIN 1.20 / 1.10, PHI 45, DIRSM 8, BIAS 0.55). All touch 0, hairs PASS.

## Reshaping H2 for the word image, round 1 of several (same day)

Owner: *"reshape H2 until it is readable by you and me. it needs make a strong word image. this will take multiple passes from both of us."*

**My read of H2** (in confusable words -- dad, road, aura, idea, quad, quota, adage, aquaduct -- at 20 px x2 and 40 px, beside today and Flanker): it reads as a, but it is the DARKEST letter in each word (colour 0.385 against the d's 0.349) with a counter a quarter smaller than the d's (44.5k against 57.7k), so in "dad" and "quad" it sits as a knot among open rounds. Flanker's a keeps the o's openness.

**The conflict the passes found:** lightening and opening it to the d's colour (v4: 0.348, counter 51.7k) evens the word image to my eye but raised OCR misreads 25 -> 32 (a>o 7 -> 12): the darkness was part of what separated a from o. Resolved by moving the a's identity to its RIGHT side -- a stronger glob and heel on the lightened bowl:

| Italic | colour | counter | a misread (Vision) |
|---|---|---|---|
| H2 | 0.385 | 44.5k | 25 |
| v4 (light, open) | 0.348 | 51.7k | 32 |
| **J1** v4 + GLOB 1.05, HEEL 1.00 | 0.360 | 50.9k | **21** |
| J2 v4 + GLOB 1.25, HEEL 0.90, ASC 14 | 0.372 | 48.8k | 23 (a>o 3, the fewest) |
| J3 v4 + GLOB 1.15, HEEL 0.90 | 0.364 | 49.9k | 24 |

J1 is both more legible to OCR and lighter / more open than H2. v4's bowl: W 1.25, THIN 1.00, RX 0.43, RY 0.36 (Italic).

BoldItalic, where the glob works the other way (misread): today 40, H2 24, **K1 (H1's shape) 14**, K2 = K1 lightened to the d's colour (W 1.00, THIN 0.95, RX 0.43, RY 0.38, GLOB 0.85, HEEL 0.70; colour 0.500, counter 36.5k) 17, K3 20.

## No globs: thick and thin matched to the o (same day)

Owner, on J1-J3 / K1-K3: *"those all suck because they look amateurish with the globs. try again with the goal of appropriate thick and thin."*

Targets, ridge widths (2 x distance transform at its local maxima, `instruments/stroke_ridge.py` on fonts, `instruments/a_ridge_eval.py` on the upright geometry): the o is the reference -- Italic o hairline 20.9 / thick 66.2 upright (22.4 / 84.1 in the built font, sheared), BoldItalic o 29.7 / 97.7; Flanker's a 25.3 / 80.6. The bowl's own four widths (the `A_TRI_DEBUG` line):

| label | Italic top-left / bottom-right / left side / bottom | settings |
|---|---|---|
| L1 | 20.8 / 20.7 / 65.7 / 63.4 -- the o's | W 1.65, THIN 1.0, PHI 45 (BI: W 1.40, THIN 0.9 -> 32.2 / 30.6 / 98.4) |
| L2 | 20.2 / 21.7 / 71.6 / 68.5 | W 1.80 (more contrast) |
| L3 | 28.7 / 32.0 / 73.0 / 54.3 | PHI 35 (stress more upright) |
| L4 | as L1 | L1 without the join weight |
| M2 | as L1 | L1 + `A_TRI_HEAD` (the family's hm_head entry stroke across a cut stem top) at ASC 12 |

**OCR vs eye.** Vision misreads (Italic / BoldItalic): today 88 / 40; H2 (globs) 25 / 24; L1 56 / 67; L2 140 / 112; L3 53 / 76; L4 89 / 72; M1 (head at xh) 86 / 72; **M2 53 / 62**; M3 (join lowered to 0.72) 95 / 125. Without globs the a is read as o and, in the BoldItalic, as e (a>e 38-96) -- the globs were carrying its identity for the OCR. To my eye L1 and M2 are the cleanest word images of the series (even colour, no knot, the stem entry shared with n and i); the OCR ranks them below the globs and, in the BoldItalic, below today. Not resolved by measurement; the owner's eye decides.

## X-height and word image: variants of M2 and L1 (same day)

Owner: *"variants of M2 and other L1 with better xheight and word image use."*

**The x-height finding** (`instruments/a_xband.py`: ink in the band 0.85-1.05 xh over the letter's ink width, upright): L1's top band held 17.9 against o 23.6, d 25.3, n 22.3, u 20.8, e 26.1 (today's a 28.6), and its top was the STEM at 429 -- the bowl never reached the o's line (436). Cause: without a glob the bowl joins the stem at 0.82 xh, and the bow solver's range (-0.05..0.40) could not lift the top that far, so it stopped at the cap silently. Range widened to 0.90; with the join raised to 0.92 xh every variant's top lands at 436-437 and the band holds 27.6-28.4.

| label | what | band | Vision misread It / BI |
|---|---|---|---|
| M2 | last round | 21.1 | 53 / 62 |
| N1 | M2, head at the n's height, join 0.92 | 27.9 | 58 / 125 |
| N2 | N1 + ascender 8 | 28.2 | 52 / 120 (grand 87.2, crowded 71.0: best) |
| N3 | N2, join 0.88, bowl 4 over the line, bias 0.65 | 27.6 | 60 / **58** |
| N4 | L1 (flat stem top), join 0.92 | 28.0 | 81 / 75 |
| N6 | N4 + heavier top hairline (THIN 1.25 / 1.12) | 28.4 | **46** / 80 |
| (N5) | join 0.95, bias 0.65 | 19.9 | dropped |

BoldItalic: raising the join makes it read as e (N1, N2: a>e 84-92); no teardrop BoldItalic yet beats today's round a (40). All touch 0, hairs PASS.

## N3 matched to its neighbours; straight profile and flick (same day)

Owner: *"N3 wins, take multiple passes matching the other letters and maximizing word image"*, then mid-pass: *"make several versions with more of a bottom right flick and a near straight profile line like N1 or N4 top left did."*

**Pass 1 (N3 against its neighbours):** Italic colour 0.390 vs d 0.349, counter 0.82 of the d's; BoldItalic 0.541 vs 0.481, counter 0.71, heavy p90 150 vs the d's 118 -- both too dark and closed. Left bearing 17 against today's 29 and the o's 35.
**Pass 2 (lighter):** P2 (Italic W 1.40, THIN 0.95, RY 0.37; BoldItalic W 1.10, THIN 0.85, RY 0.40): misread **29 / 12** (N3 60 / 58; today 88 / 40) -- the first teardrop BoldItalic to beat today's.
**The bearing was a non-problem.** `A_TRI_DX` (shift the drawing inside its box) changed nothing: the build sets the left bearing off the ink's bounding box (`build.py` ~1042, `capbear * A_LEFT + 17` + the B2 adjustment), so a shift is normalised away. The low 17 is the bbox's pointed lower-left, not crowding: `instruments/pair_white.py` (mean white across 0.15-0.85 xh, HarfBuzz-shaped) gives P2 7-8 units MORE white than today on the a's left (na da oa ua ea ra) and the same on its right. No spacing change needed; the dial stays inert.
**Pass 3 (around P2):** Italic Q1-Q4 all worse (32-47); BoldItalic Q2 (W 1.10, THIN 0.78) 9.
**Straight profile + flick.** `A_TRI_BIAS` down (0.45 / 0.35 / 0.25) and the join up (0.92-0.94) with `A_TRI_TOPFIT` 0 straightens the top-left the way N1/N4 did; it also removed a nick on the counter's top edge that P2's bowed top had where the bowl met the head's tip (the hairs gate passes it -- under its thresholds -- but it is visible at 4x). `A_TRI_FLICK` sets the teardrop a's exit reach (the a ships 0.80 of the family's):

| label | JY / BIAS / FLICK | Italic misread | BoldItalic misread (grand, crowded) |
|---|---|---|---|
| R1 | 0.92 / 0.45 / 1.25 | 24 | 15 (92.0, 80.8) |
| **R2** | 0.92 / 0.35 / 1.50 | **16** | 17 (92.4, 84.0) |
| R3 | 0.94 / 0.25 / 1.50 | 28 | 19 (92.4, 83.8) |
| R4 | 0.92 / 0.35 / 1.25 | 36 | 15 (92.0, 80.9) |
| R5 | 0.94 / 0.25 / 1.25 | 38 | 16 (92.4, 84.6) |
| R6 | 0.94 / 0.25 / 1.75 | 32 | 18 (**92.8, 89.4**) |

Today BoldItalic: 40 (91.5, 74.4). R6's long exit widens the a and loosens the word after it. All touch 0, hairs PASS.

## P2 cleanup: the head's tip, the BoldItalic counter, the bottom-right stroke (same day)

Owner: *"P2 wins, take multiple pass at cleanup, especially bold italic counter and bottom right stroke to match other letters better."*

Seen at 300 px beside d q o u, P2 had three faults. (1) The HEAD's tip (hm_head's entry stroke) fell inside the bowl's counter and stood in it as a spike, both italics -- the hairs gate passes it. `A_TRI_HEADCLIP` subtracts the counter (holes of bowl + stem) from the head, so the tip ends on the counter's edge. (2) The BoldItalic counter is a narrow teardrop where the d and q have ovals -- its AREA is already 0.92 of the d's (39.7k / 43.1k), so the fault is shape, not size. (3) The bottom-right return into the stem runs at 45 degrees, the nib's thin direction, and comes out a hairline where the d and q meet their stems at a medium weight. `A_TRI_BRW` floors the return's width at this x the broad, from the round's lowest point, eased over the first third (the stem-edge cap still applies).

| label | what | misread It / BI | colour It / BI | counter It / BI |
|---|---|---|---|---|
| P2 | pick | 29 / 12 | 0.364 / 0.500 | -- / 39.7k |
| S1 | head clip | 30 / 15 | 0.363 / 0.500 | 52.2k / 39.7k |
| **S2** | S1 + return floor 0.50 / 0.55 | **23 / 13** | 0.369 / 0.503 | 51.7k / 39.2k |
| S3 | S2 + rounder counter (T1 330) | 30 / 21 | 0.368 / 0.504 | 52.6k / 39.7k |
| S4 | S2 + roundest counter (T1 335) | 36 / 36 | 0.363 / 0.497 | 54.2k / 41.3k |

The rounder counters match the d's shape and read as o more (a>o 12-24 in the BoldItalic): the pointed teardrop is part of what separates this a from the o. All touch 0, hairs PASS.
