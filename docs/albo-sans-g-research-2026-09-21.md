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

## Round 328 — the tail is traced, not dialled

Owner, on the ten: *"needs to hook back up like a 'g' typically does. you are
making weird tails on an 'o' instead. stop and do much better based on traced
models of other fonts."* Correct on every count, and the trace says so.

Eight single-storey sans g's had their DESCENDER CENTRELINE traced —
skeletonised, the run at or below the baseline ordered from bowl to tip
(`scratchpad/albo/tailtrace.py`). **Every one has the same three-part shape,
and not one of the ten dialled arms had it:**

| | deepest at x | tip x | tip y | rise back up |
|---|---|---|---|---|
| the eight traced | −14…+17 | −147…−190 | −59…−147 | 17…113 |
| the ten dialled | −49…+177 | −53…−184 | **−207…−267** | 0…77 |

The tail goes down the bowl's RIGHT, reaches its deepest point under the bowl's
**centre**, then travels left and **back up**. The dialled arms ended within
20–60 units of the bottom: they descend and stop, which is exactly why they
read as a tail stuck on an o.

**This also corrects the earlier survey in this file.** What it called "tip x,
−31 to +6" was measured as the ink at the deepest ROW — that is the DEEPEST
POINT, not the tip. The real tips are at −147…−190. The rest of that survey
stands; that one column was mislabelled and the conclusion drawn from it (that
`o` was the arm inside the band) was drawn from the wrong quantity.

The models are frozen in `stems.py` as `G_OPEN_TAILS`, normalised so each one's
own depth is 1.0, and selected by `ALBO_G_OPEN=futura|avenir|helvetica|verdana|din`.
Built: deepest x **−20…+5**, tip x **−138…−190** — inside the traced band on
both — at the face's own descender, with the face's own pen, all five clean on
`cmp_contour_hairs.py`.

### Two scaling bugs, both caught by measuring the built letter

1. **Anchoring the model's first point at the ring root** hung the whole tail
   high: the model's start is ON the baseline, Albo's root is 164 units above
   it, so the letters built 118 units deep against a 280 target and their tips
   came back up to the baseline. The scale is taken from the root down to the
   descender line instead.
2. **Scaling x by the vertical factor.** The model's x is in units of its own
   depth but it MEANS bowl-relative position — its first point is the bowl's
   right edge. Scaled vertically, ±1.0 became ±441 units and the tips ran to
   x −715. X is matched to Albo's own ring at the root.

## Round 329 — a bpqd serif instead of the ear

Owner: *"make some bpqd style serifs to choose from, not the ear"*.

`b d p q` are all one function, `bowl_stem`, and every one of them finishes its
stem with **`stem(..., top='left')`** — a single wedge on the bowl side of the
stem's top. So the serif is taken from that same call rather than drawn again:
a short stem stub stands on the ring at `ALBO_G_OPEN_SER_AT` (38°) and carries
the family's own top, with the ring as the wall it stands on. `foot=None`
always — that end is a join, not a foot.

`ALBO_G_OPEN_EAR` now takes, besides `g` (the old diagonal ear) and `none`:

| key | `stem(top=)` | what it is |
|---|---|---|
| `dtop` | `'left'` | **the d's and q's own top serif** — the wedge points into the bowl |
| `btop` | `'right'` | the wedge the other way, off the bowl |
| `both` | `'both'` | a full flat serif, both wedges |
| `plus` | `'left+'` | the d's, plus the small 0.4 × 0.6 counter-wedge (the I's, the U's right stem) |
| `flat` | `None` | the stub squared off, no wedge at all |

Three more dials: `_SER_LEN` (the stub's height, × the stem), `_SER_SCALE`
(the wedge's size, × the family's) and `_SER_OVER` (how much of the ring's
overshoot the stub's top takes).

All five build clean on `cmp_contour_hairs.py`. Nothing ships.

## Round 330 — aligning the stem the way b d p q align it

Owner: *"take multiple passes at aligning the vertical stem with the serif in
the same way bdqp all do"*. Round 329 stood the stub on the ring at 38°, which
is not what those letters do.

`bowl_stem` does two things, and the second is the one that matters:

1. It places a **true vertical by rule** — the stem's centre half a stem INSIDE
   the ring's far centreline.
2. It **clips the ring to that stem's inner edge**, so the stem's inner edge IS
   the counter's edge and nothing pokes past the stem.

Measured on the open g: the **x was out by only 6.7 units** (0.10 stems). The
join was the whole misalignment — the counter's right edge was the RING's, at
378.4, where bpqd puts a straight wall at 344.9.

### The clip was a no-op, and the measurement is what caught it

Passes 1–3 (ring → x by rule → clip) all left the counter's right edge at
76–80 units off vertical against the d's 58.6. **The clip removed nothing**: at
a stub 1.05 stems tall the ring is already narrower than the stem's inner edge,
so there was no ink out there to cut. Nothing in the render said so; the number
did.

For the bpqd relationship the stem has to run down past the ring's **widest**
point. Departure from vertical over the counter's upper 60%, in Albo units:

| stub height | the g | the d |
|---|---|---|
| 1.05 stems | 80.5 | 58.6 |
| 2.40 | 76.1 | 58.6 |
| 3.40 | 76.1 | 58.6 |
| **4.50** | **57.7** | **58.6** |
| 5.60 | 56.9 | 58.6 |

**It converges at about 4.5 stems** — there the g's counter edge is the d's, to
within a unit, because it IS a straight stem edge and not a curve.
`ALBO_G_OPEN_SER_ALIGN` = `ring` (round 329) | `x` | `clip` (the default), with
`_SER_LEN` the stub's height. All build clean.

The trade to weigh: a 4.5-stem vertical is a real stem on the g's right, which
is what makes the join bpqd's — and also what starts to make the letter argue
with the d and the q. That one is an eye judgment, not a measurement.

## Round 331 — the letter rebuilt, not its parts adjusted

Owner: *"you are adjusting one part when you need rebuild the whole letter"*.
Right, and it explains every round before it.

`_g_open` was **the o's ring with things attached to it** — a tail rooted on the
ring at a tangent, a serif stub standing on the ring, a clip that cut nothing.
Every round moved one attachment. The open-g report even described the letter
as *"the q's skeleton with the stem's foot replaced by a hook"*, which is the
right description of the wrong code: **nothing in it was built on a stem.**

`b d p q` ARE a stem with a bowl clipped to it. `bowl_stem` places the stem
first, by rule, and intersects the ring with its inner edge. A single-storey g
is the same letter as the q with one difference — **the stem's foot is a hook
instead of a serif** — so `_g_qstem` builds it that way, and three things that
had to be dialled before now fall out of the construction:

| | dialled before | now |
|---|---|---|
| counter's right edge off vertical | 76–80, until a 4.5-stem stub was tuned | **g 61.2 · q 59.5 · d 58.6**, untuned |
| the serif's alignment | `_SER_ALIGN`, `_SER_AT`, `_SER_LEN` | `stem(top='left')`, the same call b d p q make |
| the tail's root | on the ring, at a tangent | the stem's foot |

The tail measures depth 278, deepest x **+11** (the traced models: −14…+17),
tip (−117, −130) and a rise of 148. It is inside the models' band on the
deepest point and a little short of it on the tip.

**And it retires a negative result.** The open-g work recorded that a tail
rooted low on the ring "needs an S-bend, because the ring's tangent is 42–55°
off vertical there". True, and a symptom rather than a finding: a g's tail
leaves a STEM going down, not a ring going sideways. Rooted on the stem there
is nothing to correct for.

`ALBO_G_OPEN_BUILD=qstem` is the default; `ring` keeps rounds 326–330 for the
record. Clean on `cmp_contour_hairs.py`. Nothing ships — `ALBO_G_STYLE` is
still `bent`.

## Round 332 — the counter, to the owner's own numbers

He dialled it on the bench (`scratchpad/albo/counter.html`, published as an
Artifact): **counter size 100.5%, below x-height 17**, with the baseline gap
left at 19.

As built the counter was 391 tall, 19 above the baseline and 19 below the
x-height. His figures are 393 / 19 / 17 — and **19 + 393 + 17 is the x-height
exactly**, so they are self-consistent.

The bench holds the OUTER still and moves only the counter, so that is what the
letter does: the ring's wall is thinned at the **top** by the 2 units the
counter grows, on a raised cosine so there is no step, and the bottom is
untouched. A taller ring would have raised the outer too and changed the
overshoot, which is not what he was looking at.

| | counter h | w | above baseline | below x-height | top wall |
|---|---|---|---|---|---|
| round 331 | 391 | 299 | 19 | 19 | 34 |
| **now** | **393** | 299 | **19** | **17** | **32** |
| he asked for | 393 | 300 | 19 | 17 | — |

**One unit off, and it is worth naming.** His 100.5% was a UNIFORM scale on the
bench, which widens the counter to 300 as well as heightening it. Holding the
bottom at 19 and the top at 17 fixes the HEIGHT; the width then depends on how
that height is reached, and growing the top alone leaves it at 299. A genuinely
uniform 100.5% would have to thin the left and right walls too, which the two
gap figures do not ask for.

The top wall goes 34 → 32, still above the family's own bowl hairline of 28.
`ALBO_G_QS_CTR_TOP` (2.0), `_CTR_BOT` and `_CTR_ARC`. Clean on the gate.

## Round 333 — the right stroke, and a claim of mine that did not survive

Owner: *"thin out right stoke to optically match the rest of the word image.
might just be 98% reduction but justify it"*. The justification did not come
out where I expected, twice.

**It is not physically wider.** At half the x-height the g's right stroke
measures **63.7** units; the u, d and n measure 63.7–64.4. Width up the
x-height, Albo units:

| at | 0.30 | 0.50 | 0.70 | 0.90 |
|---|---|---|---|---|
| g | 63.7 | 63.7 | 70.7 | **88.2** |
| d | 65.1 | 64.4 | 66.5 | 64.4 |
| n | 63.7 | 63.7 | 76.3 | 67.2 |

**And the 0.90 figure is not the serif, which is what I first told him.**
Removing the top serif entirely still reads **87.5** there; at 70% and 45% of
its size, 86.8. The rightmost run at 0.90 is the bowl's upper wall MERGED into
the stem — a join, not a stroke — so no stem or serif lever moves it.

Two other levers, both measured and both inert on this:

* `G_QS_STEM_W`: 1.00 / 0.98 / 0.96 / 0.94 give a right-band ink of 61.0 /
  60.7 / 59.8 / 58.7 (the d reads 58.2), so 0.94 matches the d overall — but it
  thins the 0.30–0.50 span that already matched everyone exactly.
* `G_OPEN_W0` (the tail's root): 0.92 and 0.84 change the band's foot third by
  **0.0 and +0.2** — nothing.

**So the cause of what he is seeing is not isolated**, and a 98% uniform
reduction moves the band by 0.3 points. Recorded as an open question rather
than fitted to a number. `ALBO_G_OPEN_QS_STEM_W` and `_QS_TOP_SCALE` exist and
are inert at 1.0.

### An instrument note

`_gof` prefixes `ALBO_G_OPEN_`, so these dials are `ALBO_G_OPEN_QS_STEM_W`, not
`ALBO_G_QS_STEM_W`. A whole ladder came back identical before that was spotted —
five builds reading exactly the same number is the signature of an env var that
never arrived, not of a dead dial.

## Round 334 — the hook extended left

Owner: *"extend hook on horizontal axis to the left to increase space inside
hook and match the visual top loop"*. `ALBO_G_OPEN_TRACE_X` scales the traced
model's x.

**There is no enclosed area to measure here.** The hook is open, so a flood of
the white inside it escapes around the outside (613 units wide at every
setting) and the largest inscribed circle escapes downward (1.5× the counter's
at every setting). Both were tried; neither means anything. The one figure that
does is how far left the hook reaches from the counter's centre, against how
far the counter itself reaches:

| `TRACE_X` | hook reaches left | the counter reaches |
|---|---|---|
| 1.00 (built) | **152** | 149 |
| 1.15 | 198 | 148 |
| 1.30 | 244 | 149 |
| 1.45 | 290 | 149 |

**As built the two already match** — 152 against 149. So the hook's space does
not read smaller because it reaches less far; it reads smaller because it is
bounded by an open curve rather than a closed ring. Extending it pushes the
hook past the bowl's own reach, which is a design choice and his eye to make.
All four are gate-clean.

**Ruled: 1.14** (owner, *"ship 1.14"*). Built, the hook reaches **195** units
left of the counter's centre against the counter's 148 — so it carries about a
third past the bowl's own reach, which is the point: he is matching what the
open curve and the closed ring LOOK like, not what they measure. It is the
default for `ALBO_G_OPEN_TRACE_X`; 1.0 rebuilds the traced models untouched.

The shipped roman is unaffected and was checked rather than assumed: a default
build differs from the previous commit's in **0 of 493 glyph outlines**. The
open g is still reached only by `ALBO_G_STYLE=open`.

## Round 335 — the roman ships open, the italic stays closed

Owner: *"ship open as default for roman, and closed for italic. but we need to
reduce the connector and bottom loop width to something manageable"*.

**`ALBO_G_STYLE` now defaults to `open`.** The roman's g is the single-storey
letter built as the q with a hooked foot (round 331), on the traced Futura tail
(round 328) at `TRACE_X` 1.14 (round 334). `bent` is the two-storey roman of
rounds 324–332 and `plain` the one before it. The g's advance goes **512 → 489**
against the o's 545, so the letter is narrower than the one it replaces.

The ITALIC is a separate construction in `aldine` and already ships the closed
binocular g (`ALBO_ALD_G_STYLE=cursive`, round 323). Nothing was needed there.

### What "manageable" is, measured

The connector's THICKNESS is not the problem: it measures **23** units, against
Flanker's 24 and Pagella's 22. It is the horizontal extents.

* the italic g's **ink is 483 units wide against a 444 advance** — it overhangs
  its neighbours by nearly 40 units;
* the lower loop's ink spans **357** where the upper bowl's counter is 145;
* `g ÷ o` is **1.12**, against the roman's new 0.90.

Three arms, on `ALBO_ALD_G_LRX` (the loop's radius, 194) and
`ALBO_ALD_G_NECK_L` (how far left the neck dives, 78):

| arm | LRX / NECK_L | advance | g ÷ o | ink width | loop width | connector |
|---|---|---|---|---|---|---|
| as built | 194 / 78 | 444 | 1.12 | 483 | 357 | 23 |
| a | 176 / 66 | 431 | 1.08 | 466 | 333 | 23 |
| b | 160 / 56 | 428 | 1.08 | 453 | 319 | 21 |
| **c** | 146 / 46 | 426 | **1.07** | **440** | **307** | 23 |

All four gate-clean. **c** brings the ink to within 14 units of the advance
where it started 39 over. Not ruled.


## Round 336 — the wrong open g shipped, corrected

Owner, on round 335: *"that's the wrong open 'g' use the most recent approved
one instead"*. Correct.

`ALBO_G_OPEN` defaulted to **`j`** — the open-g exploration's own first row —
and round 335 shipped the roman **without naming a row**, so it shipped `j`.
Every ruling the owner made was dialled and measured on **`futura`**, the
traced letter: the counter at 393 / 19 / 17 (round 332) and the hook at
`TRACE_X` 1.14 (round 334). The two are different letters — different tail,
different terminal — and their `g` outlines hash differently.

The default row is `futura` now, and the shipped roman's `g` outline is
**byte-identical to the approved build**.

**The failure worth keeping:** a ladder's dials were all made explicit in the
ladder commands (`ALBO_G_OPEN=futura ...`) and none of them was in the SHIP
build, which took the table's defaults instead. A ruling made on an
explicitly-parameterised build does not transfer to a default build unless the
defaults are moved to match — and nothing checks that, because both builds are
clean and both produce a plausible letter. The check that would have caught it
is the one that did: **hash the shipped glyph against the build the owner
actually approved.**
