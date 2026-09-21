# The single-storey g, measured off nine sans faces

2026-09-21. Owner: *"base this new g off of other sans serif 'g' research"*,
after ten open-loop options were drawn. Albo is a wedge serif, but the
single-storey g IS the sans idiom, so that is where the evidence is.

The instrument is `scratchpad/albo/sansg.py` — everything measured on a raster
at a fixed x-height, in Albo units, so a system font and a built Albo answer
the same question.

## Which faces actually have one

**Counting contours is the wrong test** and it put Gill Sans and Optima on the
list; both are binocular. Counting COUNTERS in the raster is right: a
single-storey g has one, a binocular has two. Nine qualified.

## What they measure

| | bowl w/h | g depth ÷ p | g depth ÷ xh | tip x | tail L | tail R |
|---|---|---|---|---|---|---|
| Futura | 0.87 | 1.00 | 0.53 | +6 | 223 | 237 |
| Avenir | 0.97 | 0.83 | 0.50 | −11 | 236 | 238 |
| Avenir Next | 0.94 | 1.00 | 0.47 | −18 | 273 | 272 |
| Verdana | 0.76 | 1.03 | 0.37 | −31 | 191 | 227 |
| Tahoma | 0.71 | 1.03 | 0.37 | −31 | 184 | 216 |
| Trebuchet | 0.88 | 1.00 | 0.37 | +6 | 194 | 231 |
| DIN Alternate | 0.64 | 1.03 | 0.41 | −14 | 192 | 202 |
| Helvetica | 0.74 | 1.06 | 0.42 | −8 | 216 | 224 |
| SF Rounded | 0.79 | 1.07 | 0.37 | 0 | 203 | 231 |

Three findings hold across all nine:

1. **The tail reaches the face's own descender.** g ÷ p is **1.01 mean, range
   0.83–1.07**; eight of nine sit at 1.00–1.07. Depth ÷ x-height varies a lot
   (0.37 geometric-screen to 0.53 Futura) and is therefore NOT the number to
   aim at — the face's own p is.
2. **The tip finishes under the bowl's centre**, tip x **−31 to +6**. Never far
   left, never right.
3. **The tail's span is near symmetric about the bowl's centre**, L/R ≈ 0.95.

Two and three together say something the numbers alone hide: **the tail travels
LEFT and comes BACK.** A tail that only swings left ends far left and has an
asymmetric span; these do not.

## Albo's ten scored against it

| arm | bowl | g ÷ p | tip x | L/R | inside the band? |
|---|---|---|---|---|---|
| j | 0.75 | 0.94 | +17 | 0.40 | tip just outside |
| y | 0.75 | 0.98 | −83 | **1.06** | symmetry yes, tip no |
| c | 0.75 | **0.64** | −43 | 0.45 | depth no |
| wedge | 0.75 | 0.81 | −34 | 0.58 | marginal |
| deep | 0.75 | 1.00 | −38 | 0.40 | tip just outside |
| curl | 0.75 | 0.80 | −109 | 1.03 | tip no |
| out | 0.75 | 1.02 | **+188** | 0.29 | no — it is a q |
| **o** | 0.81 | 0.95 | **−24** | 0.48 | **depth and tip yes** |
| hair | 0.75 | 0.97 | −34 | 0.71 | tip just outside |
| bare | 0.75 | 1.01 | −52 | 0.66 | tip no |

**`o` is the only one of the ten inside both the depth and the tip band.
`y` is the only one with the references' symmetry.** No arm has both.

## Why no arm has both, and what it would take

`ALBO_G_OPEN_REACH` sets the tip's x, and the tail ENDS where it swings, so
moving the tip toward the centre shortens the left reach in the same motion:
reach −0.92 → tip −83, L/R 1.06; −0.55 → −35, 0.63; −0.35 → −7, 0.42. The two
requirements trade directly against each other.

The references do not trade them because their tail is not monotone — it swings
left and **returns**. Three attempts to get that from the existing handles
(`tipdeg` toward the right, a long `c2`) **all overshot**: depth ÷ p went to
1.15, 1.37 and 1.37 against the references' 1.01, the tip went FURTHER left
(−106 to −211), and two of the three failed the contour gate (a HAIR at
(134, −273), a REVERSAL at (97, −413)). The handle drags the curve down and
left rather than curling it back.

**What it needs is the fix round 327 gave the binocular g's connector**: place
the tail's leftmost point explicitly and run two cubics through it with a
vertical tangent there, instead of steering one cubic by its handles. The same
fault (a single handle that saturates and folds) and the same cure. Not built.

## One figure from the open-g report that does not reproduce

It reported nine of the ten landing on the face's body colour at "+0.0%".
Measured with the chamfer ridge used elsewhere here, against o e n s c a d u,
they read **1.04–1.08×** the body letters; the shipping binocular g reads 0.89.
Its DEPTH claim, by contrast, reproduces exactly: g ÷ p ≈ 1.0 is real, and this
survey is where the evidence for it now lives.
