# Albo: imperfections that improve legibility

**Owner, 2026-09-16:** *"add to md file explaining this font as 'imperfections
that improve legibility'."*

That phrase is the face's argument, and this file is where it is written down,
because the argument is not visible in any one letter. It is visible in the
rulings, and a ruling that lives only in a transcript gets re-litigated by the
next pass — usually by somebody helpfully "fixing" the very thing that makes
the face work.

## The claim

A letter drawn perfectly is harder to read than a letter drawn by a hand.

Not more beautiful, not more characterful — **harder to read**. A page of type
is recognised as word images, and a word image is built out of the differences
between its letters. Every symmetry you leave in a face is a difference the
reader does not get: two identical arches are one arch to the eye, and it has
to count them. Every perfectly straight edge is a shape with no information in
it past its two ends. Every letter that is another letter rotated is a letter
the reader resolves late.

Albo's chain is **handwriting → metal → Albo**, and the target is the *metal*.
A punchcutter did not draw a shape and reproduce it twenty-six times. He cut
twenty-six punches, and the differences between them are not noise sitting on
top of a design — they *are* the design, because they are what a reader
navigates by.

So: imperfections, deliberately, where they earn their keep.

## What this rules out, which is most of the ways to do it

**It is a TABLE, never a jitter.** `life()` in `primitives.py` re-rolls per
build. A defect that moves from one build to the next is noise; a defect that
stays is a cut. This is the single rule that separates this face from a
distressed one, and it is also the cheapest to break — a random offset is one
line of code and it undoes the entire argument, because a cut you cannot point
at twice is not a cut.

**A cut placed where the pen is already thick is not a cut, it is a lump.**
Round 153 learned this on the Q. The 225° hand mark was cut as the letter's
heaviest press on the reasoning that the nib's own thick already falls there,
so the two would agree. They did agree, and that was the fault: the cut stacked
on the pen *and* on the tail's join, and the lower left became the heaviest
thing in the letter by thirteen units on a stroke of ninety. Put presses where
the stroke is not already at its maximum.

**Magnitudes are 2 to 7 units at a cap of 674** — under a twentieth of a
stroke's own width. At 13 pt none of it is a feature. What it does is stop two
halves of a letter being the same half.

**An imperfection that costs legibility is a defect.** The face keeps helpful
defects; it does not keep fractures, spurs, slivers, cracks, stray counters or
trapped white. Those have their own gate (`cmp_aldine_glitch.py`, seven
measured classes) and the distinction between the two is the whole discipline:
one is a cutter's hand, the other is a union artifact, and they look identical
in a diff.

## What is actually cut, and why each one earns it

| Where | What | Why it reads better |
|---|---|---|
| **Q**, six cuts by angle round the ring | graver lifts at 60°, over-corrects at 105°, longest flat at 150°, hardest press at 225°, bottom pulled in at 285°, ground squared at 340° | a superellipse on a nib is a machine's O: every quadrant is the same quadrant, and the only thing varying is the pen's angle |
| **R**, five cuts by fraction along the traced strokes | the bowl's lower arm wanders, the flank presses *below* the nib's own thickest, the crown lifts, the leg's elbow takes more and gives it back before the tip | the two sides of a traced curve were the same curve |
| **X**, both diagonals' midpoints displaced, in *different* directions by different amounts | thick sags below its chord, thin lifts | two straight lines crossing is the one construction with no hand in it — every quarter a mirror of another, twice over. Equal opposite bows would only be a second symmetry |
| **a**, the top left | a single cubic from the stem connector down to eight o'clock, tangent-continuous with the ring at both ends | the peak lands on the connector and the top falls away, which is what the scan does and what an even arch cannot |
| **Y / P**, the hairline gap | about eight units of white where two strokes meet, held over 0.04 cap on the Y and 0.10 on the P | it shows the reader two strokes *meeting* instead of one moulded shape. Full account: [albo-hairline-gap.md](albo-hairline-gap.md) |
| **m**, three arches | the right one wider and shorter, the middle stem rounded and lifted off the baseline | three identical arches are one arch counted three times |
| **g**, the lower loop | rotated onto the alphabet's stress axis | it was the only lowercase letter carrying two different axes |

## The negative results, which are half the value

These were built, measured, looked at, and thrown away. They are recorded so
they are not re-proposed, and because each one marks a boundary of the claim.

**The g's bowl is stressed 45° off the alphabet and that is correct.** Rotating
it onto the a's and the o's axis puts its weight on the upper *left* — and no
g in any reference has that, because a g's bowl sits on a neck leaving its
bottom left and the ink has to be there to leave from. *An imperfection that
fights the letter's own construction is just an error.*

**The a's ten droops could never have drooped.** All ten were radial pushes on
the outer contour, and a radial push on a superellipse gives a shallower curve
— never a straight line. The scan has no shallower curve there; it has one flat
chord. *Check that the mechanism can express the thing before laddering its
parameters.*

**Averaging a corner gives a rounded corner, not a curve.** Three rounds went
into the a's top left: lerp toward a chord (tangent-discontinuous), the same
plus smoothing passes (a rounded corner at 7, the droop eaten by 12), and
finally one cubic whose handles run along the ring's own tangents —
continuous *by construction* rather than by smoothing.

**Hand-cutting a letter does not make its edges stop being straight.** The X
was hand cut in round 165 and still reports a 381-unit straight run: its
diagonals are bowed at their middles, but their two *sides* stay parallel. A
displaced control point moves a stroke; it does not vary the stroke's width.
Those are different mechanisms and only the second one removes a straight edge.

## The gates, and why imperfection needs them more than regularity does

A regular face can be checked by eye — anything that looks wrong is wrong. A
face whose defects are deliberate cannot, because the question is never "is
this irregular" but "is this the irregularity we chose". So each claim has an
instrument:

| Gate | What it holds |
|---|---|
| `cmp_aldine_metrics.py` | every letter within 10% of its measured target; the target describes the DRAWING and follows the owner's rulings |
| `cmp_cap_weight.py` | each italic capital carries its own roman's weight, with named exemptions carrying their reason |
| `cmp_aldine_glitch.py` | seven classes of union artifact, thresholds derived from the font's own thinnest legitimate stroke |
| `cmp_aldine_straight.py` | every dead straight run over 0.30 x-height — **44 of 62 glyphs** as of round 168 |

That last one is the open front. Straightness is the largest remaining
regularity in the face and the hardest to remove, because a stroke's sides are
straight whenever its width is constant, and constant width is the default
everywhere a stroke is not explicitly profiled.

## Where the line is

Not everything irregular is wanted, and three cases mark the edge:

1. **A gap at every junction is a mannerism, not a hand.** The hairline is on
   the Y and the P. The B's two bowls, the R's bowl arm, the K's leg and the
   D's bowl foot are all candidates and all deliberately untouched: the Y's
   reads as character *because* it is nearly alone.
2. **The roman is not the italic.** Cuts made for the Aldine italic stop at the
   italic. The roman ships in Albo Regular and has its own argument.
3. **The owner rules on renders, not on measurements.** Every number in this
   file exists to make a ruling repeatable, not to make it. When a measurement
   and his eye disagree, the measurement is the thing that gets re-examined —
   the Y's stem weight is the worked example: the gate's whole-letter mean said
   0.99 and level, while the letter's own stem was the lightest in the
   alphabet, because the Y spends on an arm what other capitals spend on a
   second stem.
