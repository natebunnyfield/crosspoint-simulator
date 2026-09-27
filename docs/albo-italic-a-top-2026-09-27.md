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
