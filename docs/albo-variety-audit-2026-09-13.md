# Albo: which serifs and which counters are the same as each other

2026-09-13. Owner, verbatim: *"run an audit that evaluates which serifs and
counters are exactly the same as others, we need variety throughout this font
for it to work."*

**The headline. 129 of the font's 144 serifs (90%) are byte-for-byte copies of
at least one other serif, and the three biggest groups — 58 identical feet, 28
identical stem tops, 16 identical diagonal ends — cover every letter of the
common set `e t a o i n s h r d l u` that carries a serif at all.** The cut
hides some of it and not enough: post-cut, 125 of 144 are still inside an exact
group, the 58 feet only splitting into 22 / 18 / 18 by facet phase. The
counters come off far better: 29 holes in the font, and only four true twin
pairs — O/Q, b/p, d/q and the two halves of the `%` — every one of which is
literally the same call made twice.

Nothing here is changed. This is a finding pass; the recommendations in §5 are
for the owner to rule on.

- The instrument: [`tools/wedge_serif/outlines/cmp/variety.py`](../tools/wedge_serif/outlines/cmp/variety.py), re-runnable.
- The picture (a twin group per block, serifs at 4×): the generated
  `albo-variety.html` beside the built TTF.

```bash
cd tools/wedge_serif
PYTHON_GIL=0 python3 -W ignore -m outlines.cmp.variety <font.ttf> <out_dir>
```

Built at the round-65 defaults: stem 84, contrast 0.95, x-height 429,
ascender 770, descender 280, cut 87, serif 92 — so `WL` 65.7 and `WD` 131.4
units, and the numbers below move with those. 92 glyphs drawn.

---

## 1. Method

### 1a. Construction level — from the code, by running it

Reading the glyph files does not answer the question, because a glyph's serifs
are mostly ones it never names: `stem(x, 0, xh, top='left', foot='both')` draws
three bracketed wedges and `stems.py` mentions none of them. So every primitive
that makes a serif or a counter (`wedge`, `stem`, `ring`, `ring_from`,
`half_bowl`, `beak`, `dot`, `bar`, `diag_wedge`, `end_wedge`, `diagonal`, and
the glyph-module helpers `o_ring` / `cap_ring` / `fig_ring`) is **wrapped for
the length of one build** in every namespace that imported it, and every call is
recorded with the numeric arguments the code actually computed — not the
expressions it was written as. Calls are then grouped by rounded argument
signature. `solve_widths()` runs first with recording off, so the three
width-solving passes do not pollute the census.

### 1b. Outline level — the shape each serif ends up being

**The serif window.** Every `wedge()` call carries the frame it was drawn in:
`A`, the stroke's corner at the end; `d`, the unit direction out of the stroke's
end; `sd`, the unit normal out of the stroke on the wedge's side. The window is
the rectangle in that frame

    u ∈ [−WD/2, +WD/2] along sd        (−65.7 … +65.7)
    v ∈ [−WD,   +WD/2] along d         (−131.4 … +65.7)

— a `WD × 1.5 WD` box (131 × 197 units) sitting on the stem edge at `A`. It
contains the apex, which reaches `WL` = 65.7 out along `sd`, and the whole
bracket, which runs `depth` ≤ `WD` back along the edge. The **glyph's finished
ink** is clipped to it and mapped into the frame, so every serif in the font
arrives aligned on its own stem edge and its own end face, whatever direction
the stroke actually points. A foot and a top wedge on the same stem land on top
of each other — which is the point: they *should* differ, and if they do not the
comparison says so.

**The counters.** Every closed inner contour of every glyph, translated so its
centroid is the origin and **not scaled** — an o's counter and a b's counter
that are the same size and the same shape are the finding. A second, softer pass
normalizes each counter to one area first and reports what is merely
*scale*-similar.

**The two numbers.** For each pair: the area of the symmetric difference over
the mean area, as a percentage; and the Hausdorff distance between the two
boundaries, over `WD` for a serif and over √area for a counter. **≤ 2% symmetric
difference is EXACT** ("the same serif"), **2–8% is NEAR**. Pairs are joined into
groups by connected component, so a group of five is five serifs no reader can
separate.

**Pre-cut and post-cut answer different questions, and both are reported.** The
cut (`cut.blend`, seed 73, one running phase counter over the glyph order) gives
every contour its own facet phase, so two true copies come out of it with
different facets. **A post-cut comparison therefore understates the
repetition**; the pre-cut designed outline is where a true copy lives, and the
post-cut number says how much of the sameness the cut is already hiding. Do not
read the post-cut list as the answer.

The geometry is taken from the builder in design space (untranslated,
unrounded), reproducing `build.build`'s cut exactly with the same `Cutter(73, 4)`
over the same glyph order, so the serif frames recorded at level 1 line up with
the outlines at level 2. The `.ttf` argument is the built font it corresponds to.

---

## 2. Construction level: identical parameter sets

234 distinct signatures in all. Every signature made more than once, largest
first. **The count is calls; the letter list is deduplicated**, so "×32 … 25
letters" means some letters make that call twice (`foot='both'` is two calls with
opposite `sd`, and `m` has three stems).

| n | primitive | signature | glyphs |
|---|---|---|---|
| 32 | wedge | **foot**, 0.85×WL × 1.0×WD, drop 0.6, out 180° (left), end −90° | `1 4 B D E F H I K L N P R T Y a b f h i k l m n p q r` |
| 29 | wedge | **foot**, 0.85×WL × 1.0×WD, drop 0.6, out 0° (right), end −90° | `1 4 F H I K N P R T Y a d f h i k l m n p q r u` |
| 26 | wedge | **stem top**, 1.0×WL × 1.0×WD, drop 1.0, out 180° (left), end +90° | `B D E F H I J K L N P R U b d h i k l m n p q r u` |
| 5 | wedge | **bar end**, 0.85×WL × 0.9×WD, drop 0, rising from a bottom bar | `2 E L Z z` |
| 5 | stem | cap stem, x 47.75, 0→674.4, `top='left' foot='both'` | `F H K P R` |
| 5 | ring | rx 204.9 ry 170.2 — the 8's two rings and their solve | `8` (5 calls) |
| 5 | dot | r 46.2 at (46.2, 46.2) | `! , : ; …` |
| 4 | stem | cap stem, x 47.75, 0→674.4, `top='left' foot='left'` | `B D E L` |
| 4 | wedge | **bar end**, hanging from a top bar, end 0° | `5 E F T` |
| 4 | wedge | **bar end**, hanging from a top bar, end 180° | `7 T Z z` |
| 4 | stem | lowercase, x 42, 0→429, `top='left' foot='both'` | `i m n r` |
| 4 | dot | r 42 at (58.8, 628.2) | `‘ ’ “ ”` |
| 3 | wedge | **stem top**, out 0° (right-hand stem) | `H N U` |
| 3 | stem | lowercase, x 42, 0→770, `top='left' foot='both'` | `h k l` |
| 2 | wedge | **apex**, 0.9×WL × 1.0×WD | `M W` |
| 2 | ring + cap_ring | rx 350.1 ry 351.2 | `O Q` |
| 2 | ring | rx 238.9 ry 228.5, centre 200.7 | `b p` |
| 2 | ring | rx 238.9 ry 228.5, centre 238.9 | `d q` |
| 2 | ring + fig_ring | rx 204.9 ry 209.6 | `6 8` |
| 2 | stem | x 375.0, 0→283.1, `foot='both'`, ent_span (0,429) | `h n` |
| 2 | wedge | diagonal end, 0.9×0.9, out 119° | `9` (both flags) |
| 2 | dot | the two upper quote dots | `“ ”` |
| 2 | dot | the colon/semicolon upper dot | `: ;` |

Read down the first three rows: **the whole serif family is three calls.** That
is the family working as designed — the guide's §2 table says stem tops are
1.0×1.0 and feet 0.85×1.0 — and it is also the entire finding, because "as
designed" here means "with no variation of any kind whatsoever, in 87 of 144
serifs."

Three things worth naming in the rest of it:

- **`O`/`Q` and `b`/`p` and `d`/`q` are one drawing each.** `bowl_stem` in
  `glyphs/stems.py` takes `rx_c = 214 * wf` for all four of b d p q; the only
  difference between the pair members is which side the stem is on. `Q` is `O`
  plus a tail over an untouched `cap_ring`.
- **The 8's rings are solved, not drawn** — five `ring` calls with one signature
  is `ring_for_counter` iterating, not five identical serifs.
- **Nine dots share two radii.** `. , : ; ! ? … ' " ‘ ’ “ ”` are drawn from
  `S*0.55` or `S*0.5`; five of them are the same circle at the same place.

---

## 3. Outline level: the twin lists

### 3a. Serifs, PRE-CUT — the designed outline, where a true copy lives

144 serifs. **15 exact groups covering 129 of them.** Only 15 serifs in the
whole font have no twin.

| n | family | the serifs (glyph#index in draw order) |
|---|---|---|
| **58** | foot | `B#2 D#2 E#2 F#2 F#3 H#2 H#3 H#5 H#6 I#3 I#4 K#2 K#3 L#2 N#2 N#3 P#2 P#3 R#2 R#3 T#3 T#4 Y#3 Y#4 a#2 b#2 d#2 f#1 f#2 h#2 h#3 h#4 h#5 i#2 i#3 k#2 k#3 l#2 l#3 m#2 m#3 m#4 m#5 m#6 m#7 n#2 n#3 n#4 n#5 p#2 p#3 q#2 q#3 r#2 r#3 u#3 1#1 1#2` |
| **28** | stem top | `B#1 D#1 E#1 F#1 H#1 H#4 I#1 J#1 K#1 L#1 N#1 N#4 P#1 R#1 U#1 U#2 b#1 d#1 h#1 i#1 k#1 l#1 m#1 n#1 p#1 r#1 u#1 u#2` |
| **16** | diagonal end | `A#2 K#5 M#2 M#3 R#4 V#1 W#1 X#1 X#2 Y#1 k#5 v#1 w#1 x#1 x#2 y#1` |
| 4 | bar end | `E#4 L#3 Z#2 2#1` |
| 3 | bar end | `E#3 F#4 Z#1` |
| 2 | beak lip | `C#1 G#1` |
| 2 | small second | `I#2 U#3` |
| 2 | bar end | `T#1 T#2` |
| 2 | diagonal end | `V#2 v#2` · `W#2 w#2` · `X#3 X#4` · `x#3 x#4` |
| 2 | apex | `W#3 w#3` |
| 2 | bar end | `z#1 z#2` |
| 2 | foot | `4#1 4#2` |

Note what the 58-group contains: **both feet of the same stem** (`l#2 l#3`,
`i#2 i#3`, `h#2…h#5`, all six of `m#2…m#7`), the lowercase foot and the capital
foot, the x-height foot and the ascender foot. A punchcutter's two feet on one
`l` are never the same punch; here they are exact mirrors of each other and of
56 others.

The `2` group has the *left* and *right* feet of the `4` in it, and `T#1 T#2`
are the two ends of the T's arm — the same story one letter down.

**Near copies (2–8%): 3,028 pairs.** So even the serifs that are not exact are
overwhelmingly clustered: 5,198 of the ~10,300 possible pairs in the font are
within 8% of each other.

### 3b. Serifs, POST-CUT — what the shipped outline actually has

**19 exact groups covering 125 of 144.** The cut is doing real work and it is
not enough:

| pre-cut | post-cut |
|---|---|
| 58 feet, one group | 22 + 18 + 18 (three phase classes) |
| 28 stem tops, one group | 16 + 9 + 2 + 1 |
| 16 diagonal ends, one group | **16, unchanged** |
| near copies 3,028 pairs | 1,426 pairs |

The 16 diagonal ends come through the cut intact. That is the clearest statement
of the limit: a 1-in-4 decimation with four phases can produce at most four
classes, so it can hide a group of four and cannot hide a group of sixteen.

### 3c. Counters, unscaled

29 holes in the font. **Four exact pairs, and every one of them is the same call
made twice.**

| pair | symmetric difference | what it is |
|---|---|---|
| `O` / `Q` | **0.0%** | `cap_ring` called with the same radius; the Q's tail is a separate stroke |
| `%`'s two rings | **0.0%** | the same `ring` twice |
| `b` / `p` | **0.3%** | `bowl_stem(…, 'left', …)` for both; only the stem's extent differs |
| `d` / `q` | **0.6%** | `bowl_stem(…, 'right', …)` for both |

And two near pairs (2–8%): `6` / `9` at **4.97%**, `g`'s loop / `8`'s upper ring
at **7.88%**.

### 3d. Counters, scale-normalized — the softer list

After normalizing both counters to one area, the exact pairs become
`B~1`/`P~1` (**1.7%**), plus the four above. And one that just misses the
threshold but is worth naming: **`o` against `Q` is 3.3% once scaled, against
15.4% unscaled — the lowercase o is the capital O reduced, not a different
letter's counter.** `D~1` against `b~1` is 9.3% scaled.

### 3e. The counter inventory, with each one's nearest neighbour

The whole table is in the tool's output and the JSON; the shape of it:

| counter | area | w/h | nearest (unscaled) | nearest (scaled) |
|---|---|---|---|---|
| `O` `Q` | 259,058 | 0.866 | each other 0.0% | each other 0.0% |
| `b` `p` | 84,853 | 0.746 | each other 0.3% | each other 0.3% |
| `d` `q` | 84,853 | 0.746 | each other 0.6% | each other 0.6% |
| `o` | 98,333 | 0.906 | `p` 15.4% | `Q` **3.3%** |
| `e` | 24,207 | 1.738 | `8`'s upper 37.5% | `g`'s bowl 20.9% |
| `a` | 34,238 | 1.044 | `&` 27.6% | `8`'s upper 17.9% |
| `g` bowl / loop | 52,281 / 49,670 | 1.573 / 1.066 | each other 24.8% | — |
| `D` | 227,691 | 0.774 | `Q` 19.2% | `b` 9.3% |
| `B` upper / lower | 76,925 / 50,991 | 0.938 / 1.008 | `P` 8.3% / `8` 10.7% | `P` **1.7%** / `R` 3.4% |
| `A` | 48,823 | 0.809 | `B` lower 38.8% | `%` 36.0% |
| `4` | 41,606 | 0.635 | `A` 44.0% | `#` 36.1% |

---

## 4. What matters for the word image at 13 pt

The owner's standing goal (guide §00) is the **word image**, and the standing
rule (§0000) is the **space inside and between**. Ranked by how much of a page
each repetition actually paints:

1. **The foot.** Every stem in `e t a o i n s h r d l u` that has a foot has
   *this* foot: `i n h r d l u a m p q b k f`. In a line of text the baseline is
   a row of 58-way-identical brackets at a near-constant pitch. This is the
   single largest mechanical signal in the face.
2. **The stem top.** Same population minus the ones that have no top, and at
   13 pt the top wedge is what gives the x-line its texture.
3. **b d p q as one bowl.** Four of the twelve commonest letters share one
   counter, and `d`/`q` is `b`/`p` reflected. In `and`, `had`, `bed` the reader
   sees the same white twice.
4. **o as a shrunk O.** Only visible in mixed-case setting, but `o` is the
   commonest round in English and it is not its own drawing.
5. **The diagonal end**, which survives the cut untouched — but it lands on
   `v w x y k` and the capitals, so it costs less per page than 1–3.

---

## 5. Recommendations, ranked — each one thing a punchcutter's hand does

**Not made. The owner rules.** Each is a small change to a construction that
already exists, and none of them leaves the family described in guide §2.

### R1. Break the two feet of one stem apart (58 serifs → 2 populations, one constant)

`primitives.stem`'s `foot='both'` emits two wedges with identical
`wl * foot_len` and `wd * foot_depth`, differing only in `sd`. Give the two sides
different numbers: the **left foot 1.0 × 1.0 and the right foot 0.94 × 1.06** of
today's, say. It is one line, it varies the largest group in the font at a
stroke, and it is what actually happens at the desk — the right foot is cut on
the exit of the stroke and the left on the entry, and no cutter matches them.

### R2. Two stem-top families, ascender and x-height (28 serifs → 2)

`top_len` and `top_drop` are 1.0 for every stem in the font. The pen has further
to travel into an ascender's top than into an x-height stem's, so set
**b d h k l to length 1.05, fillet 0.60** and **i m n p r u to length 0.95,
fillet 0.70**. Two families keyed to a real difference between the letters, not
a random jitter.

### R3. Stop b/d/p/q sharing one ring (4 counters → 4)

`glyphs/stems.py:bowl_stem` hardcodes `rx_c = 214 * wf` for all four. Two nudges,
either independently:
  - the **descenders take a slightly wider, shallower bowl** — `rx_c` 218 and
    `ry` −4 for `p q` — since they hang below the x-line and read heavier there;
  - **break the mirror** by giving the left-stem pair and the right-stem pair
    different superellipse squareness, `k` 1.90 for `b p` against 1.85 for
    `d q` (or a `rot` of ±1.5°, which the `ring` primitive already accepts and
    nothing currently uses).

### R4. The lowercase o is not the capital O reduced

3.3% apart once scaled. The lowercase round in a humanist text face is
relatively **wider and rounder** than the capital. Take the `o`'s `k` down by
about 0.12 from `BOWL_K` (rounder shoulders), or take the cap `O`'s up by the
same — whichever direction he wants — so the two counters are different
drawings and not one drawing at two sizes.

### R5. Size the diagonal wedge off the stroke's own angle (16 serifs → a spread)

`diag_wedge` pins 0.9 × 0.9 for every diagonal in the font, so a wedge on the
A's 47° leg and one on the Y's 70° arm are the same serif. Make the scale a
function of the angle it sits on — `0.9 · (0.94 + 0.12·|sin θ|)` gives about
±6% across the population — which is the nib's own behaviour rather than a
jitter, and it is the group the cut cannot help with.

**Two lower-priority ones**, recorded so they are not re-found: the five
identical punctuation dots (`! , : ; …`, `S*0.55` at the same place) and the four
identical quote dots would take a per-mark radius spread of a few percent; and
the `6`/`9` counters at 4.97% could be separated by the tail treatments already
ruled in rounds 70–74 rather than by touching the rings.

---

## 6. What was checked and found VARIED

So the next pass does not redo it.

- **`s`, `t` and `c` carry no bracketed wedge at all** — the s is a spine with
  two pen cuts, the t a stem with `cut_top` and no foot, the c an arc with a
  beak. There is no serif on them to repeat, and three of the twelve common
  letters are therefore already outside the finding.
- **15 serifs have no twin anywhere in the font**, pre-cut:
  `&#1 9#1 9#2 9#3 A#1 K#4 M#1 M#4 S#1 Y#2 a#1 c#1 k#4 q#1 y#2`. The A's flat
  foot, the K's and k's kick feet, the M's outer feet, the 9's three flag
  wedges, the a's hood flag, the y's tail wedge and the q's tail are each their
  own shape. The rulings that made them (round 36's flat A foot, the kick angles
  at 65/60/56/37, round 71's flag-diag) are exactly why.
- **The bar-end serifs are already three orientation families**, not one — 5
  rising, 4 hanging-right, 4 hanging-left — and `T#1`/`T#2` are their own pair.
- **The beak** is used on `C` and `G` with the same lip and on `S` with its own
  profile; `c` gets a smaller lip (0.35 × 0.6 against 0.4 × 0.7). Three
  treatments across four glyphs, which is the family behaving.
- **The counters are in good shape and the finding is small.** Of 29 holes, 21
  have no exact twin unscaled and 19 have none after scaling. `e`, `a`, `A`,
  `4`, `D`, `#`, `@`, `&`'s two, `g`'s bowl and `0` are all more than 12% from
  their nearest neighbour unscaled. The e's eye in particular (w/h 1.738, nearest 37.5%) is
  the most distinctive white in the font — the round-39/46 dials did their job.
- **The `8` is not two copies of one ring**: the upper is 25,949 units and the
  lower 49,529, and neither is within 2% of the other or of the `6`.
- **`B`'s two bowls are not each other** — more than 10.7% apart unscaled (the
  lower bowl's nearest neighbour anywhere is the 8's upper ring at 10.7%, so the
  upper bowl is further still). The round-58 shared-waist ruling did not
  collapse them.
- **The `m`'s three stems are three different stems** as drawn (`x0`, `x1`, `x2`
  at different entasis spans) — it is only their *feet* that are identical, which
  is R1's problem and not a separate one.
- **The post-cut check was run and is reported**, so nobody needs to re-ask
  whether the cut already solves this: it splits the 58 feet into three classes
  and leaves the 16 diagonal ends untouched. A 1-in-4 decimation with one seed
  has four phases and cannot separate a group larger than four.
- The `%`'s two identical rings are inside one glyph and were left out of the
  ranking deliberately: a percent sign's two rings being the same ring is not a
  defect.

---

## 7. Confidence

Every number here is measured against the tree at this commit and the round-65
pen defaults, by the script named above, and reproducible by re-running it. The
construction census is from instrumented calls, not from reading the source, so
it cannot be wrong about which arguments a glyph passed. The outline numbers
depend on the window definition in §1b — a different window would move the
percentages, though not the grouping, since the exact groups sit at 0.0–0.6%
and the next-nearest non-member is far above 2%. The *interpretation* in §4
(which repetitions matter at 13 pt) is judgment and has not been tested on a
render; the owner judges pictures.

---

## Postscript, the same evening: the life

Owner: "alter anything identical very slightly so they render the same at
small scale, but are full of life at large scale." Done in
`outlines/primitives.py` (`LIFE`, `life()`, `begin_glyph()`): every
`wedge()` takes +-6% on length and depth and +-10% on drop and fillet,
every `ring()` +-0.06 on its exponent and +-0.6 degrees of rotation,
deterministic per (glyph, call index) so the variable font's masters stay
compatible. This instrument was also corrected: it normalized the symmetric
difference by a window that was mostly stem, so a 6% change in the wedge
alone read as 1% and passed the 2% "exact" threshold; `clip_serif` now
keeps only the part outside the stroke's edge. Re-run on the same build,
life off: 128 of 145 serifs with an exact twin pre-cut, 116 post-cut. Life
on: **40 of 149 pre-cut, 17 post-cut.** At 13 pt on the four-level
pipeline the two builds are 96.5% pixel-identical over the 147 common
words, the rest one gray step at edges, 0.09% black-white flips. The
counters O/Q, b/p, d/q are separated by the ring's exponent and rotation
jitter; the o is still the O's construction reduced (recommendation 4
stands, not done).

## Status, 2026-09-14 (round 90 font, life on) -- owner asked

Re-run of `outlines/cmp/variety.py` on the round 90 Albo-Medium (a curve 8
with the hollow's curve, dot style 1, y at 0.97). The headline then and now:

| | 2026-09-13, life off | 2026-09-13, life on | 2026-09-14, round 90 |
|---|---|---|---|
| serifs with an exact twin, pre-cut | 128 of 145 | 40 of 149 | **42 of 153** (19 groups) |
| serifs with an exact twin, post-cut | 116 | 17 | **17 of 153** (8 groups) |
| counters exact, unscaled | O/Q b/p d/q | -- | **O/Q (0.7%), b/p (0.4%)**; d/q at 2.0-2.7% |
| 13 pt, 147 words, pixels identical to the life-off build | -- | 96.5% | not re-measured |

So the "same at small size" half holds (96.5% of pixels, the rest one gray
step at edges) and the "full of life at large size" half is about three
quarters done. Three faults in the life itself, found today by spying on
`life()` while drawing 4 Z 9 O Q:

1. **The hash is nearly linear in the call index.** `life()` seeds on the
   string `"<glyph>#<n>"` with `x = x * 131 + ord(ch)`; consecutive n give
   consecutive values, so the 9's eight draws step 0.088, 0.096, 0.103,
   0.111, 0.119, 0.126, 0.134 on one channel -- a glyph's own serifs move
   TOGETHER, which is why 9#4/9#6 differ by 0.06% and 9#3/9#5/9#7 are a
   post-cut group. A real mix (splitmix64, or hashlib over the seed) is a
   one-line fix; it moves every serif's jitter, so Medium and VF rebuild.
2. **Z#1/Z#3 and 4#1/4#2 are byte-identical (0.0%)** even though the Z's four
   and the 4's two `life()` draws differ. Either those serifs come through a
   path that does not take the draw, or the audit's serif finder is
   labelling a non-wedge feature (the 4's crossbar corners?) as feet. Not
   traced yet.
3. **The ring jitter is under the audit's own threshold.** +-0.06 on the
   exponent and +-0.6 degrees move O/Q by 0.7% and b/p by 0.4% of the
   counter's area; the postscript above said "separated" -- it was not,
   by the 2% rule this document uses. The o is still the O's construction
   reduced (R4). A larger rotation (+-2 degrees) or an rx/ry breath of
   +-1% would clear 2%; the o wants its own construction regardless.

Cross-glyph pre-cut groups still standing (life on): bar ends E/T/Z and
F/T/z, feet F/Y/i, F/h, H/b, I/k, K/m, R/1, h/u, h/n, l/m, diagonal ends
K/X (x2), k/x, and L/R's top wedges. The recommendations R1-R5 above are
all still open; the life was the owner's chosen route instead of R1/R2/R5,
and with faults 1-2 fixed it should take most of these groups with it.

