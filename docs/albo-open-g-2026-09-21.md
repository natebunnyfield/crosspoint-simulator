# The open-loop roman g — ten options

2026-09-21. Owner: *"make an open loop 'g' in roman based on other albo roman
lowercase. take ten passes at giving me a variety of options."*

**EXPLORATION ONLY. Nothing here ships.** The default build is `ALBO_G_STYLE=bent`
— the letter round 327 left on the page — and it is **byte-identical with this
work in the tree**, proved by comparing every glyph's `RecordingPen` output
against a build of `HEAD`'s own `stems.py` in an isolated copy: **0 of 493
glyphs differ**, for `bent` and for `plain` both. (md5 cannot answer this:
fontTools stamps `head.modified`, so two identical drawings always hash
differently — `docs/albo-method.md` §7.)

Code: `tools/wedge_serif/outlines/glyphs/stems.py`, the `ROUND 327 — THE
OPEN-LOOP ROMAN g` block. Build one:

```
cd tools/wedge_serif
env ALBO_G_STYLE=open ALBO_G_OPEN=<option> FJORD_STEM=66.9 FJORD_CONTRAST=0.892 \
    PYTHON_GIL=0 python3 -m outlines.build <outdir> --style Regular
```

Every dial is separately overridable (`ALBO_G_OPEN_FRM`, `_REACH`, `_DEPTH`,
`_TIPDEG`, `_C1`, `_C2`, `_W0`, `_FLOOR`, `_END`, `_PROF`, `_EAR`, `_EAR_AT`,
`_RX`, `_CUT_W`, `_CUT_AT`, `_CUT_ARC`, `_WEDGE_SIDE`, `_WEDGE_SCALE`, and the
arc's `_RUN`/`_R`/`_SWEEP`), so an option is a set of dial values and never a
private code path.

Figures (PNG, native pixels; the one enlargement is integer NEAREST and says
so on the page): `01-goa-280px.png` (all ten, x-height 280 px, each beside the
o and the a), `02-words-46px.png`, `03-words-13px-x6-nearest.png`,
`04-words-13px-native.png`, `per-option/*.png`, plus the ladders
`ear-ladder.png`, `wedge-ladder.png`, `curl-ladder.png`, `curl-ladder2.png`,
`out-ladder.png` and the reference sheet `refs-og.png`.

**They live in the session scratchpad and will not survive it** —
`…/scratchpad/albo/openg/` — and neither will the four instruments written for
this round (`measure.py` the chamfer-ridge / advance / depth / q-IoU / mouth
report, `wall.py` the perpendicular wall profile, `refg.py` the reference
survey, `render.py` the figures). **Every number in this file is therefore
stated with its method, not with a path**, so it can be re-derived; the
sections below say exactly what each measure does. Nothing was added to
`tools/wedge_serif/` but the one block in `stems.py`.

---

## 1. What an open-loop g is, in THIS face

It is the **`q`'s skeleton with the stem's foot replaced by a hook**: a full
x-height bowl — the **o's** ring, not the binocular g's 0.66-xh bowl — whose
right wall carries on past the baseline and curls instead of closing into a
second bowl. Every part is one the face already owns:

| part | what it is |
|---|---|
| the bowl | `ring()` at the o's centreline radius, its weight scale and its hairline floor (`rounds.O_RX × O_RX_ADJ`, `O_W_ADJ`, `O_FLOOR_ADJ`) |
| the tail | a stroke on `PR.bowl_widths` — the profile the o's ring, the a's hood and the e's arm are all drawn on |
| its end | the j's run-out to a point · the c's lower terminal (0.70 of the pen into the family's 20° cut) · the c's TOP finial with the y-tail's floor (`PR.finial_widths` / `PR.finial_cut` / `rounds.c_top_width`) · the v/y/x diagonal end wedge (`PR.end_wedge`) |
| the ear | `g_g`'s ear, unchanged — or moved, or absent |

### THE ONE RULE decides the root, and it is the only thing here that is not taste

`docs/albo-method.md` §1 and §1b. The tail leaves the bowl **on the ring's own
centreline, with the ring's own clockwise tangent, and at the ring's own width
there** (`G_OPEN_W0 = 1.0` means exactly `bowl_th` of that tangent). A union
*adds*, it does not blend: two edges arriving at an angle leave a notch on one
side and a spur on the other that no width can tune away. Leaving tangent, at
the matching width, means the silhouette runs out of the bowl into the tail
with nothing to see. **All ten options raise no `g` finding from
`cmp_contour_hairs.py`** — see §5.

---

## 2. What the references measure

Four faces whose g is genuinely single-storey and open, measured in **Albo
design units** (normalised to x-height 429) with `scratchpad/albo/openg/refg.py`
and `wall.py`. Gill Sans and Charter Italic were pulled from the reference set
after being rendered: **both are looped, not open** — a fact the numbers alone
did not say and the picture did.

| | Futura | Verdana | Trebuchet | Skia |
|---|---|---|---|---|
| g depth ÷ that face's own p | **1.00** | **1.03** | **1.00** | **1.00** |
| left wall / right wall on the counter's centre row | 101 / 95 | 74 / 72 | 78 / 78 | 66 / 62 |

**Every reference open-loop g reaches its own face's descender exactly.**
Albo's p is −281 and its y −299, so an open g that stops at −180 is a
departure, not a default. That single measurement changed eight of the ten
options' depth between the first cut and the second.

The walls are compared as a **ratio against each face's own o**, because Albo's
o runs 36–73 units (its own contrast) where Futura's runs 70–118. Reference
band, at the angles that matter (0° = due east, 90° = the crown):

| deg | 0 | 285 | 300 | 315 | 330 | 345 |
|---|---|---|---|---|---|---|
| Futura | 0.96 | 0.89 | 0.74 | 1.08 | 1.15 | 0.98 |
| Verdana | 0.97 | 0.92 | 0.77 | 1.17 | 0.96 | 0.97 |
| Trebuchet | 1.00 | 0.91 | 0.93 | 0.91 | 0.96 | 0.98 |
| Skia | 0.94 | 0.95 | 1.12 | 1.04 | 0.95 | 0.94 |

So a real open g is **thin at 300°** (the bay under the bowl, where the tail's
crotch is) and **a little heavy at 315°** (where the descender leaves). That is
the shape the shoulder cut in §4 was fitted to.

---

## 3. The ten

Each is one design decision, not one dial value. `ALBO_G_OPEN=<key>`.

| # | key | the decision | terminal |
|---|---|---|---|
| 1 | `j` | the **j's tail**, transplanted: down the bowl's right wall, then the j's own circular turn (its radius, its 118° of sweep) | run out to a point |
| 2 | `y` | the **y's tail**: one long cubic sweeping left across the whole letter. The widest reach of the ten | the c's top finial on the y's floor |
| 3 | `c` | **short and shallow** — a stub hook. The depth axis at its minimum | the c's lower terminal, 0.70 pen into the 20° cut |
| 4 | `wedge` | stopped by a **SERIF** rather than by a taper | the v/y/x diagonal end wedge, upper corner, 0.75 |
| 5 | `deep` | the **full descender** in one near-vertical drop with a late, tight turn | the 20° cut |
| 6 | `curl` | **part-closed**: the hook turns and comes back up, a loop that was never shut | the 20° cut |
| 7 | `out` | the tail **hooks RIGHT** — the e's arm direction given to a descender | the c's top finial |
| 8 | `o` | the bowl is **the o's exactly** (rx 1.00, where the rest run 0.94) | the 20° cut |
| 9 | `hair` | the tail **runs out as a true hairline** — the pen lifting. The contrast axis | the 20° cut |
| 10 | `bare` | **NO EAR**. The canonical single-storey g | the c's top finial |

### The numbers

Stroke weight is the **chamfer ridge** (the method of `scratchpad/albo/contrast.py`:
the distance transform over the ink, doubled, is the local width; the top 20%
of it is the ridge), median, in design units, against the median of the face's
body letters `o n c e a u s b d p h m r` (60.0). Advance is `hmtx` against the o
(545). Depth is the glyph's minimum y, against the roman p (−281) and y (−299).
q-IoU is ink overlap against this face's own q, both rasterised at one x-height
and aligned on their counters' centroids. Mouth is the shortest white from the
tail's tip to the bowl or to the tail's own first 60%.

| arm | ridge (5% / 95%) | vs body | advance | ÷ o | depth | ÷ p | q-IoU | mouth | gate |
|---|---|---|---|---|---|---|---|---|---|
| *bent (ships today)* | *52.4 (42.4 / 70.0)* | *−12.6%* | *512* | *0.939* | *−260* | *0.93* | *0.125* | *148* | *clean* |
| 1 `j` | 60.0 (52.4 / 80.0) | +0.0% | 508 | 0.932 | −265 | 0.94 | 0.637 | 134 | clean |
| 2 `y` | 60.0 (52.4 / 78.3) | +0.0% | 508 | 0.932 | −276 | 0.98 | 0.558 | 184 | clean |
| 3 `c` | 60.0 (52.4 / 80.0) | +0.0% | 508 | 0.932 | **−180** | **0.64** | 0.584 | 100 | clean |
| 4 `wedge` | 60.0 (52.4 / 80.0) | +0.0% | 508 | 0.932 | −229 | 0.82 | 0.577 | 139 | clean |
| 5 `deep` | 60.0 (52.4 / 80.0) | +0.0% | 508 | 0.932 | **−282** | **1.00** | 0.627 | 132 | clean |
| 6 `curl` | 60.0 (50.0 / 78.3) | +0.0% | 508 | 0.932 | −226 | 0.80 | **0.547** | **66** | clean |
| 7 `out` | 60.0 (52.4 / 78.3) | +0.0% | **537** | **0.985** | −287 | 1.02 | **0.651** | 75 | clean |
| 8 `o` | 61.2 (52.4 / 80.0) | **+2.0%** | 527 | 0.967 | −267 | 0.95 | 0.623 | 157 | clean |
| 9 `hair` | 60.0 (52.4 / 79.2) | +0.0% | 508 | 0.932 | −273 | 0.97 | 0.616 | 176 | clean |
| 10 `bare` | 60.0 (52.4 / 79.9) | +0.0% | **495** | **0.908** | −284 | 1.01 | 0.577 | 161 | clean |

**Nine of the ten land on the face's body colour to the measure's resolution
(+0.0%)**, and the tenth is +2.0%. That is the shoulder cut of §4 doing its
work, and it is worth stating because the first cut read **+4% to +11%** and
one arm's lower-right wall was **+63%** of the o's.

Wall ratio against Albo's own o, at the angles the references disagree on:

| arm | 0 | 285 | 300 | 315 | 330 | 345 |
|---|---|---|---|---|---|---|
| `j` | 1.03 | 0.87 | 0.68 | **1.29** | 0.96 | 1.02 |
| `y` | 1.03 | 0.87 | 0.69 | 1.17 | 0.98 | 0.99 |
| `c` | 1.03 | 0.87 | 1.28 | 1.12 | 0.95 | 0.99 |
| `wedge` | 1.03 | 0.89 | 0.70 | 1.21 | 0.97 | 1.01 |
| `deep` | 1.03 | 0.85 | 0.68 | **1.31** | 0.98 | 1.02 |
| `curl` | 1.03 | 0.87 | 1.17 | 1.06 | 0.95 | 1.01 |
| `out` | 1.03 | 0.87 | 1.26 | 1.15 | 0.98 | 0.99 |
| `o` | 1.03 | 0.85 | 0.66 | **1.29** | 0.96 | 1.02 |
| `hair` | 1.03 | 0.87 | 0.70 | 1.14 | 0.95 | 0.99 |
| `bare` | 1.03 | 0.89 | 0.70 | 1.17 | 0.95 | 0.99 |

Reference band at 315° is 0.91–1.17. **`j`, `deep` and `o` sit at 1.29–1.31 —
outside it**, and the reason is structural: those three drop most steeply, so
the tail runs beside the ring for longest. It is the residue of the fault in
§4, not a new one, and the lever is `ALBO_G_OPEN_CUT_W` (0.55 today).

### The q test

An open-loop g is a bowl with a descender and so is this face's q. Measured as
ink overlap with the counters aligned, with two controls whose answer is known:

| | IoU |
|---|---|
| o against itself | 1.000 |
| **o against q** (a q IS an o with a stem — the yardstick) | **0.599** |
| p against q (mirror images) | 0.414 |
| **the binocular g against q** | **0.125** |
| the ten open g's against q | **0.547 – 0.651** |

**Every open-loop g is four to five times more like the q than the binocular g
is, and five of the ten are more like it than the o is.** Whatever tells a
reader g from q is carried entirely by the tail's last third. That is the real
cost of this letter and it is not visible at display size — it is visible at
13 px, in `03-words-13px-x6-nearest.png`.

---

## 4. The fault that took the longest, and its cure

Rooting the tail on the ring's centreline makes the *departure* clean, but
**below** the root the two run side by side: the ring's centreline turns left
toward the bowl's floor while the tail carries on down, so the union spans from
the ring's inner edge to the tail's outer one.

It nearly went unmeasured, because the obvious instrument lies. A **row-wise**
ink width inflates wherever the stroke is not vertical — the same trap
`docs/albo-g-anatomy.md` round 323 records for the g's waist ("the row runs
ALONG the stroke and the number inflates"). Rows through the first cut read
80.4 at y 107 and **112.6** at y 51 against the o's 71.9 and 76.1, and most of
that was the stroke's angle. Measured **perpendicular** — a chamfer ridge on a
ray from the counter's centroid — the real fault is narrow and large:

| deg | 0 | 45 | 285 | 300 | 315 | 330 | 345 |
|---|---|---|---|---|---|---|---|
| the o | 71 | 57 | 40 | 48 | 57 | 68 | 72 |
| first cut | 73 | 67 | 41 | 49 | **93** | 80 | 75 |

**+63% at 315°**, against a reference band that tops out at 1.17.

**The cure is the p's, not a new one.** `bowl_stem` eases the ring's stroke to
`NEAR_STEM_W` within 90 units of the stem's edge "so the crotches clear", and
the a's bowl does the same at its own stem. Here the ring's width is cut on a
raised cosine centred on `G_OPEN_CUT_AT` — the shape round 324 gave the bent
g's loop shoulder — so the tail carries the weight through the sector it shares
with the ring and the rest of the ring is untouched. At `CUT_W` 1.0 the bowl is
the o's ring exactly.

---

## 5. What was checked and found CLEAN

- **`cmp_contour_hairs.py --letters` on all ten**: 52 glyphs swept, **1 with
  findings** in every arm — the `h`, which the **baseline raises too** (a HAIR
  at (160, 316), arms 6.32 / 168.00). **No `g` row in any arm.** The full
  (non-`--letters`) sweep also returns **13 with findings** in every arm, the
  baseline's count, but the row SET moves by two — see §6.8, which is the cut's
  phase counter and not the g.
- **`cmp_touch.py` on all ten**: 5,197 pairs, **1 touching (`VI`), 3 below the
  0.012 em floor, 14 exempt — identical to the baseline in every arm.** No g
  pair moved, including the far-reaching `y` and `out` tails. Worth checking
  because `docs/albo-method.md` §5 is about exactly this: a redrawn letter's
  *relationships* go stale silently.
- **The default is inert.** `bent` and `plain` both build byte-identical to
  `HEAD`'s own `stems.py`, 0 of 493 glyphs different, compared as outlines.
- **Colour.** Nine arms at +0.0% of the body median, one at +2.0%.
- **The bowl is the o's.** With the shoulder cut off (`CUT_W=1.0`) the ring
  measures the o's walls at every angle but the shared sector.

## 6. What was rejected, and why

1. **Rooting the tail low**, on the bowl's underside (`frm` −45 to −60), so the
   ring and the tail never run side by side and no shoulder cut is needed. The
   ring's clockwise tangent at −45° is **42° off vertical** and at −60° it is
   **55°**, so a stroke leaving *tangent* there heads down-LEFT and a deep
   descender then needs an S-bend to straighten. The alternative to the S is to
   leave NOT tangent, which is the notch rule again. Rejected on the geometry
   before anything was built.

2. **A wide shoulder cut.** At `CUT_AT` 320° over a 62° arc the cut reaches the
   bowl's widest point and its floor: g/o reads **0.87 at 0°** and **0.85 at
   345°** where the four references hold 0.94–1.00. 310° / 36° touches neither
   (0° 1.03, 345° 0.99) and still brings 315° from 1.57 down to 1.17. Grid of
   four fitted against the reference band; `310 / 36 / 0.55` won on the two
   columns that bind -- 315 degrees (1.17 against 1.23, 1.26, 1.32) and 285
   degrees (0.89 against 0.84, 0.92, 0.81) -- and no other column separated
   them.

3. **A tail that folds back on itself** to close the loop properly (tip at
   `reach` +0.12 to +0.42, pointing up-RIGHT). The centreline crosses itself and
   `stroke()`'s offset edges cross with it, which leaves **white slivers inside
   the stroke** — three built, all three broken, in `curl-ladder.png`.
   `stroke(..., pieces=True)` is the face's own cure for a self-crossing
   centreline (the ampersand, the at-sign) and is the way in if this is ever
   wanted; the shape it makes is not this letter. `curl` as shipped stops at the
   tightest mouth that does not fold: **66 units**, from a four-rung ladder
   (tipdeg 96 / 80 / 68 / 56 → mouth 133 / 120 / 109 / 66).

4. **The right-hooking tail (`out`) is not a g.** Worst q-IoU of the ten
   (0.651, against the o/q yardstick of 0.599), and at 13 px "a foggy gauge"
   reads **"a foqqy qauqe"** — look at row 7 of
   `03-words-13px-x6-nearest.png`. Three rungs were laddered (reach 1.06 / 1.30
   / 1.22 with matching depth and tip direction) and set beside the real `q` in
   `out-ladder.png`; all three read as a q with a decorated foot. It ships as an
   option because the owner named the axis, not because it works.

5. **The wedge terminal on the tail's LOWER corner** (`wedge_side` +1, at 0.90
   and 0.60 of the family's diagonal end wedge). The serif hangs off the tip as
   a droop and reads as a fault rather than as a serif; the upper corner
   (`−1`, 0.75) reads as the family's rising bar-end wedge. The stroke also has
   to arrive near full width — the first version's tail ended at 0.80 of the
   pen and there was nothing for the wedge to sit on.

6. **The ear at `g_g`'s own 44°.** `g_g` roots its ear at 44° on a bowl 0.66 of
   the x-height tall; on a FULL x-height bowl the same angle is a different
   place on the letter. Laddered at 30 / 44 / 58 / 70 (`ear-ladder.png`): a nub
   on the right wall / a spur / an ear on the shoulder / a flag off the crown.
   **52° ships** — 0.79 of the way up from the bowl's centre, against the
   binocular g's own ear at 0.61 of its bowl. *The angle that matches the number
   is not the angle that matches the place.* Moving it also narrowed the letter
   by 19 units (527 → 508), because the ear's root moved left.

7. **The first depth set.** Eight of the ten stopped between −180 and −253
   before the references were measured. Every reference open g reaches its own
   face's descender; eight were re-aimed. `c` was left shallow **on purpose** —
   it is the depth axis's low end — and is the one arm outside the reference
   band at 0.64 of the p.

8. **NOT a rejection, but the instrument note this round is worth most for.**
   **Changing one glyph re-cuts every glyph built after it.** `outlines/cut.py`
   is explicit about it — *"contours are cut in glyph order with one running
   phase counter"* — and the binocular g has **3 contours** (an outer and two
   counters) where every open g has **2**. One contour fewer shifts the phase
   for the whole rest of the font, so a build with an open g differs from the
   baseline in **211 glyphs**: `n`, `o`, `alpha`, `oe`, `sigma`, `Sigma`,
   `Euro`, the figures and most of the composites among them. They are not
   redesigned — the advance is identical in 209 of the 211 and the point count
   moves by ones, which is a re-phased projection and nothing else.

   The proof that it is the phase and not the g: **all ten arms produce the
   identical segment count for every one of those glyphs** (`n` 170 in all ten
   against the baseline's 168, `alpha` 179 against 177, `uni2081` 55 against
   57) although the ten g's are ten different drawings. A shape cannot do that;
   a shared counter can.

   Two consequences. The full glitch sweep's row set moves — `alpha` and `oe`
   in, `sigma` and `uni2081` out, the same swap in all ten arms, the count
   unchanged at 13 — and none of it is a fault this work introduced. And
   **any future A/B of one letter is only clean for that letter**: compare the
   `--letters` arm, or compare the glyph itself, and never read a whole-font
   outline diff as evidence about the letter you changed.

---

## 7. Ranking, and why

Judged on the word images (`01`, `02`, `03`), not on the table.

1. **`y` — the y's tail.** The face's own descender idiom at full size: the
   sweep is generous, the terminal is a family primitive, and on a page the g's
   tail then shares a rhythm with the y's and the j's. Second-least confusable
   with the q of the ten (0.558). Its cost: the finial reads as a heavy drop at
   display size, and the tail reaches furthest left of the ten — its leftmost
   ink stops **39 units inside the bowl's own left edge** where `j`, `c` and
   `deep` stop 143 inside — so it is the arm whose spacing would need watching
   first. It does not touch anything today: `cmp_touch.py` is identical to the
   baseline, and the left bearing does not move (every arm's ink starts at
   x 26, as the binocular g's does).
2. **`bare` — no ear.** The calmest word image and the narrowest advance by 13
   units (0.908 × the o), depth exactly the p's. The cost is a family trait: the
   a and the binocular g both put something at that shoulder.
3. **`j` — the j's tail.** The most literally built from this face's own parts,
   and the run-out to a point is the j's own. The point is 0.18 of the pen; at
   13 px it is the arm most likely to lose its last few units.
4. **`hair` — the pen lifting.** The most beautiful at display size and the one
   most at risk at 13 px on the four-level pipeline. `rounds.O_FLOOR_ADJ` exists
   because hairs were dropping to gray at that size, and this tail has no floor
   at all. It is a legibility trade and his to rule, not mine.
5. **`deep`.** Correct by the references' own rule (1.00 × the p) and the most
   q-like of the good arms (0.627), because a long near-vertical descender *is*
   a q's stem for most of its length.
6. **`wedge`.** Distinctive, and the only arm whose tail stops on a serif; the
   upturned flag still reads slightly foreign on a curve.
7. **`curl`.** The most distinct from the q (0.547) and the most interesting
   drawing, but it half-abandons the premise — a mouth of 66 units reads as a
   loop, not as an open tail.
8. **`o`.** 20 units wider and +2% heavier for no gain the eye collects; 0.94 is
   the better bowl.
9. **`c`.** Reads truncated. Every reference goes to the descender.
10. **`out`.** Fails the q test, measured and visible at reading size.

---

## 8. A note on provenance

The measurements of Futura, Verdana, Trebuchet, Skia, Gill Sans and Charter
Italic are **research** (`docs/albo-method.md` §1d: measuring a reference is
research, shipping its numbers is derivation). Nothing was traced: the bowl is
Albo's own `ring()` on Albo's own `O_RX`, and every tail width comes from
`PR.bowl_widths` — the family's profile at the stroke's own tangent. What the
references contributed is two decisions: **how deep the tail goes** (as a
fraction of the face's own p), and **what the wall may do at 300° and 315°**.

A parallel task committed **round 327** (the bent g's connector, two cubics
through a waist) to the same file while this was being drawn; the control
figures and the `bent` identity proof above are against that commit, not
against round 326.
