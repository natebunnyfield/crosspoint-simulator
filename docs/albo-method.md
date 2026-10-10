# How to draw Albo from the evidence — a method for the next agent

2026-09-17. Written after a session in which most of the work was wasted, and
written mainly to say *how* it was wasted, because the failures generalise and
the successes mostly do not.

This is the **method** doc. It does not repeat what the letters are
(`docs/albo-aldine-targets.md`, `docs/albo-aldine-metrics.md`), how a glyph is
built (`docs/fjord-glyph-guide.md`), or what was decided when
(`docs/wedge-serif-exploration.md`). It says how to get from a photograph of a
printed page to a typeface without spending days on things that cannot work.

---


## 0. How an option page is made (owner ruling 2026-10-09)

*"only give me mathematically sound options. change shapes as much as is
needed in a variety of ways, do not overfit, use reference fonts."* So, for
every page from round 485 on:

1. **Start from a measurement against the references.** Each arm answers a
   number the references establish (`word_measure.py`, `word_parts.py`,
   `cmp_aldine_*`, the capitals audit), and the page prints that number for
   every arm beside the references' range.
2. **Vary in kind, not in degree.** A page is shape, weight, width and
   construction arms side by side, not one dial at five settings. A ladder
   is for the pick AFTER the kind is chosen.
3. **Do not overfit.** Matching the references' median by pushing one letter
   until the number lands (the u at 14% narrower, round 484's O) is not an
   option; an arm must stay inside what the references themselves do with
   that letter's proportions.
4. **The references are the yardstick**, drawn on the page at one x-height
   beside the arms where the question is a shape.
5. Change as much as is needed -- a letter may be redrawn, not only dialed.

## 0. The brief, and what each word in it constrains

The owner's standing brief, verbatim:

> I am trying to make word images that sound like they should, it is a legible
> and character filled text face that is inspired from metal letterpress that
> was derived from historical handwriting.

Four constraints, and they are not decoration:

| word | what it rules out |
|---|---|
| **word images** | judging letters on a specimen sheet. A letter is right when the *word* is right. Ladders are rendered as words, at reading size, always. |
| **legible** | any imperfection that costs reading. `docs/albo-imperfections.md` marks that line. |
| **character filled** | the smooth, optically-corrected, evenly-fitted default. Deliberate irregularity is the point. |
| **metal letterpress, derived from handwriting** | **the target is the metal, not the hand and not the scan.** The chain is handwriting → punch → matrix → type → impression. Each step adds and subtracts. |

**The chain is the single most useful idea here.** A scan is the *last* link:
ink spread, paper, one impression's bite. A digital revival is an
*interpretation* of the same punches. The hand is what the punchcutter was
imitating, not what he cut. So:

- **the scan** tells you proportion, colour, and what survives printing. It
  cannot tell you a stroke's true edge — ink spread inflates every width and can
  close a thin to nothing.
- **a revival** (Flanker Griffo, Pagella) tells you an edge, exactly, and tells
  you one designer's opinion. Two revivals disagreeing is information.
- **a calligraphic face** (Coelacanth, Cancelleresca) tells you the *hand* under
  the metal — the stroke order, the pen, the direction of travel.

Read a measurement's meaning from which link it came off.

---

## 1. THE ONE RULE

> **When a stroke comes out the wrong weight, check its DIRECTION before its
> width. In a pen model the width IS a function of where the stroke is going.**

This was written down on 2026-09-14 in `docs/italic-g-strokes.md` and then
ignored for an entire session. Rounds 176–181 tuned the g's loop: a keyed width
table, a thin-at-an-angle dial, a run-out depth, a taper amount. **All of it was
worthless.** The fault was that the loop was not on the letter's pen at all.

### How to test it in one command

`tools/wedge_serif/cmp_g_strokes.py` measures a letter's **pen signature**:
ridge of a distance transform for the centreline, twice the distance for
thickness, principal axis of the neighbours for direction, thickness binned by
direction.

**A face drawn on one pen has ONE signature for the whole letter.** A run at 15°
is thin wherever in the letter it happens. Measured on the g, bowl against loop:

| | bowl | loop | apart |
|---|---|---|---|
| Coelacanth | 15° | 30° | 15° |
| Flanker | 15° | 15° | 0° |
| **Albo, before round 182** | 15° | **75°** | **60°** |

And the shape of the profile is as diagnostic as the angle. A pen gives a smooth
single-peaked curve; a declared table gives noise:

```
Albo loop    … 75  28  34  40 102  42 …     adjacent 15° bins
Coelacanth   … 52  78  94  93  90  88 …
```

**If the profile jumps between adjacent bins, a width table is standing in for a
pen, and no amount of re-tuning that table will fix the letter.**

### Why a table cannot be repaired into a pen

`keyed_ring(keys=…)` declares a width **at an angle round the ring**. A pen gives
a width **for the direction the stroke runs**. On a circle those agree. On a
skewed egg, or a hand-warped contour, they do not — and the error is largest
exactly where the letter is most characterful.

The subtle half: a table can land the **thin** in the right place and still put
the **thick** 30° away, because in a table those are two independent entries and
in a pen they are one decision. Albo's g *bowl* had exactly that fault and looked
fine by its thin alone.

The fix is `keyed_ring(pen=(thick, thin_fraction, target))`, which takes widths
from `nib_widths_closed` while keeping skew, the hand table, and the outer
contour. Prefer it for every closed ring. The same fault was fixed on the O and Q
two months earlier; it recurred because nothing tested for it.

---

## 1b. THE SECOND RULE: a union does not blend

Found 2026-09-17, after it had been treated as a per-letter bug **four separate
times**.

> `geom.ink` / `union` does not blend two strokes, it **adds** them. Where a
> stroke is unioned onto another, the outline is tangent-continuous only if the
> two edges were already going the same way. If they cross at an angle the union
> leaves a **concave notch** on one side and a **convex spur** on the other —
> and **neither can be tuned away by changing either stroke's width**, because
> the fault is in the direction the edges arrive at, not in how fat they are.

Its instances, each of which cost rounds before the rule was named: the Q's tail
root (179), the g's ear rooted on the crown (176), the g's neck landing on the
loop (184), the g's ear against the bowl (185), and the g's neck **arriving** at
the loop (186) — where the fix was to make the stroke come in LEVEL
(`G_NECK_FLAT`) so it merges into the loop's curve instead of stabbing into it.

That last one also carries a negative result worth keeping. The references
reverse direction **twice** across the waist and Albo **zero** times — a real,
correct measurement — and the inference drawn from it, that the connector needed
a mid-path S, was wrong. Built at 0, 16 and 30 units of swing: neither the
reversal count nor the picture moved. **The fault was at the END of the stroke,
not in its middle.** A measurement can be sound and the thing you conclude from
it still be the wrong lever.

**How Coelacanth avoids it at the ear:** its bowl-top and ear are **one pen
movement**, so there is no union to notch. Albo cannot restructure every letter
that way, so the working fix is to make the joining stroke **leave tangent** —
in the g's ear, the stroke is held level for its first third (`G_EAR_TANG`)
because the crown's own tangent is level there. The edges then leave parallel by
construction rather than by a fitted number. Rooting it elsewhere, bowing it and
thinning it were all tried first; all still notched, because all of them change
width and position and none changes direction.

`tools/wedge_serif/cmp_joints.py` finds these: it ranks every sharp vertex on
the designed outline by turn angle × the shorter arm, and splits notches from
spurs. **Not every sharp corner is a fault** — a serif tip, the inside of a v,
a deliberate knife-stop are all legitimately sharp, and the instrument correctly
ranks the E's and T's serif tips at the top. It reports; you look.

## 1c. THE THIRD RULE: a stroke's end must match what it lands on

The g's neck arrived at its **full** width — and a *widening* one, its profile
running 56 / 50 / 64 over its length — onto the part of the loop where the ring
is at its **thinnest**, 49 units falling to 25. A stroke thicker than the one it
joins cannot merge into it; it protrudes, and a trim then cuts the protrusion
off square and leaves a spur.

The same rule states the terminal case — **and I got its direction backwards,
which is worth more than the rule itself.**

I read the g's ear as thick at the root tapering to a point, and built it that
way. Measured on columns that contain *only* the ear, Coelacanth runs
`44 → 51 → 61 → 72 → cut` and Flanker `63 → 62 → 62 → 62 → cut`. **Both leave the
bowl THIN, flare outward, and stop on a CUT. Neither comes to a point.** The
error came from reading a crop in which the root's column still held the
*bowl's* ink, so the root measured 228 units and looked like the thick end.

> **A junction crop measures both strokes.** Isolate the stroke — columns or rows
> containing only it — before reading any profile off it.

And the standing instruction that follows, the owner's own (2026-09-17):

> **For visuals, assume you might have it backwards, and test the inverted
> reading before tuning anything.** A ladder built on an inverted premise never
> converges, and it looks like progress the whole way.

## 1d. Provenance: measure freely, ship nothing foreign

Owner ruling 2026-09-17: *"do not adopt a license for albo."*

Coelacanth is OFL **with a reserved font name**. OFL's terms attach to a
derivative, so **numbers traced off it cannot ship** in a font that is to stay
unencumbered. The line that follows is clean and worth stating once:

> **Measuring a reference is research. Shipping its numbers is derivation.**

Every `cmp_*` script here measures references; that is fine and is the whole
method. `trace_g.py` may be run freely. But what shipped in the end was the g's
rings derived from **Albo's own pen** (`nib_widths_closed` on the family nib),
and it reaches the same place by the same physics — measured on the built font,
30°/120° at 2.83:1 against Coelacanth's 15°/105° at 2.80:1, thin and thick 90°
apart in both. **The pen equation is mathematics, not anyone's expression.**
The traced tables are kept behind `ALBO_ALD_G_TRACE=1` as a comparison arm only.

---

## 1e. THE FOURTH RULE: an import-bound constant swallows an override in silence

Found twice in two rounds, 2026-09-17, and it will happen again.

Several modules here do `from ..pen import S, CS, WL, WD, DROP, TH_V, ...`. That
**binds the values into that module's namespace at import**. Setting `pen.WL`
afterwards moves nothing there. A per-letter override that patches the wrong
namespace builds the letter **byte-identical to before — no error, no warning,
nothing at all.**

| override | patched | actually read from |
|---|---|---|
| J and T's full serif | `caps_straight.WL/WD/DROP` | **`primitives`** — `stem`, `bar`, `diag_wedge` |
| I and J's thinner stem | `caps_straight.CW` | **`pen.CAP_STEM`**, as an *attribute* |

The second is the useful distinction: `primitives.stem` computes its default as
`TH_V * pen.CAP_STEM` — an **attribute lookup resolved when the glyph is drawn**
— so `pen.CAP_STEM` is patchable while `caps_straight.CW` is not. Before writing
an override, grep for where the value is actually *read*, and prefer a name
reached through the module (`pen.X`) over one bound into it (`from pen import X`).

**And always diff the outlines after.** A build that "succeeds" proves nothing:

```python
from fontTools.pens.recordingPen import RecordingPen
# ... compare rp.value for every glyph, before vs after
```

Both of these were caught only that way.

## 1f. THE FIFTH RULE: a gate normalised by a shrinking control set will invent failures

`cmp_cap_weight` divided every capital by the median of "the capitals we have
not redrawn". That set shrank for fifty rounds — round 145 took the X and the W,
round 192 the I and the J — until it was **six letters**. A median over six is a
sample, not a yardstick.

When I and J left it, the median moved 2% and **H, M, N, Q and R all reported
OFF in a build where not one of them was touched.** The gate manufactured
exactly the failure mode it exists to rule out. The median now runs over all 26,
which one or two re-cut letters cannot move — that is what a median is for.

The general form: **a gate whose baseline is computed from the thing being
measured drifts as the work proceeds.** Prefer a baseline that is either fixed
or robust. And when a gate fails a glyph you did not touch, *check whether its
outline changed at all* before believing it — twice this session the answer was
"byte-identical, the ruler moved."

## 1g. Contrast is a consequence of the pen, not a dial to turn

The 8 measured 1.69:1 against Coelacanth's 3.59:1 and the owner asked for more
contrast. Two ways were tried and **both are recorded as failures**:

- **the hair floor** is not what binds it — 0.65 → 0.50 → 0.40 → 0.32 moved the
  contrast 1.63 → 1.69 and then stopped, because the family's bowl profile never
  asks for anything thinner;
- **a contrast exponent** on the ring's own widths reaches the number (2.55 at
  2.3) and **necks the counter into a kidney shape at every value**, because
  `ring` offsets the counter inward by the width at each point. `counter_smooth`
  2, 7 and 14 render the same pinch — it is not a sampling artifact.

Coelacanth gets 3.59:1 from the **pen**: thin where the stroke runs along the
nib's edge, thick where it runs across. That varies the width without ever
pinching a counter, because thin and thick land where the stroke's *direction*
puts them. Which is §1 again. **The 8's rings want what the g's rings got in
round 182**, and no dial substitutes for it.

## 1h. THE SIXTH RULE: when a letter does not read as itself, look at its structure, then DRAW the part

2026-09-28, the Bold Italic c: rounds 433–434. The full record is in
`docs/albo-round-433-2026-09-28.md` from "Follow-up" on.

**How the day went:**
- The owner asked for the top serif "more" and the bottom "less".
- The finial floor delivered the weights: bottom 0.49 of the stem, top/bottom 2.6×, both in the references' range.
- He then said *"the top sucks"*.
- Two more passes on the same machinery, carrying the stroke round and growing the swell inward, came back *"much worse and worse, do better"*.
- The next attempt started from the picture instead of a dial, and was accepted (D3) on the first set of arms.

**What the picture showed** (`instruments/ref_sheet.py`, every reference c at one x-height):
- Poetica, Coelacanth, Cancelleresca, Flanker, Pagella, Georgia, Berkeley and Times ALL have a round crown arching over.
- In all of them the terminal hangs off the crown's right end at about 0.75–0.85 xh, and its underside hooks back into the counter.
- Albo's c had no arch, in the 400 and the 700 alike. The crown was a straight ramp rising right, and the terminal was the highest point of the letter: a horn.
- No width or angle dial could have produced the arch, because the structure was wrong.

**Why the machinery could not fix it:**
- `PR.finial_widths` swells a stroke's width symmetrically about its path. At a heavy floor, half the extra width stands up and out: T3's ink top reached 507, on a 444 o.
- Shifting the path so the swell grows inward only (hang) self-intersects. The swell's half-width exceeds the inner radius at the top-right corner of a squarish superellipse, so the inner offset loops. It tore a hole in the outline and flipped the face across the counter.
- Lowering the start angle hangs the terminal, but the swelled end still became a flag, with a long shallow face produced by `finial_cut`.

**The procedure, in order:**
1. **Look before tuning.** Render the letter from every reference at one x-height (`instruments/ref_sheet.py`). Say in one sentence what they all share and Albo lacks. If you cannot, you are not ready to change code.
2. **Find the machinery's limit.** If the shared feature needs mass on ONE side of a stroke, or a terminal that turns against the path, no symmetric-width dial will make it.
3. **Draw the part.** Stop the stroke at a junction and union on an explicit shape: cubics for the edges, a straight cut face (the family's wedge, never a ball — round 276). Precedents:
   - the roman t's tail, round 420 (`_t_clean` in `stems.py`);
   - the italic c's top, round 434 (`_c_drawn_top` in `aldine.py`).
4. **Iterate on the live builder, not on font builds.** `instruments/glyph_view.py` draws a glyph from the current code in 0.1 s; a cut takes 1–2 min.
   - Overlay the references unsheared by their MEASURED slant: `instruments/glyph_overlay.py` reads `refs_registry.py`.
   - Zoom joins at 4× with the vertices and construction points marked: `instruments/glyph_zoom.py`.
5. **Show width as a number.** A drawn terminal changes the letter's reach; the c went from 0.77 to 0.87 of its o. Offer an arm that keeps the old width. The owner chose that one (D3, 0.83).

**What went wrong inside the drawn part** (each seen only at 4× zoom; no gate saw either):
- **A junction right of the apex leaves a corner on the crown.** Where the stroke's edge is already descending, a drawn edge that rises first makes a dip. Put the junction LEFT of the apex (100° here), where the edge still rises, and the arch continues unbroken.
- **Leave along the stroke's own EDGE, not the centerline's travel.** A varying-width stroke's edges are not parallel to its centerline, and the difference shows as a kink.
- **Keep a cubic's control points monotonic along the curve.** The underside first left the face at 150° with a long arrival handle. Its second control point landed right of its first, so the curve went left, right, left: an S. That left the counter's top-right as a tall slot. Leaving steeply (120–125°) with a short arrival handle gives one concave hook.

**Related lessons from the same day:**
- **Smooth what was TAKEN, not the widths** (round 432). Round 429 thinned the c's lower left by reading the o's nib off each sample's direction, with a running maximum and a per-sample outward shift. The counter came out with a point (400) and a lump over a slit (700). `albo_bumps`, the hairs sweep and the glitch sweep all passed it. The fix smoothed (new width − old width), which is 0 outside the blend, so the finial stems that `fin_floor` reads stayed untouched.
- **A floor stops governing below the swell.** `C_FIN_BOT_700` below about 0.6 changed nothing, because `finial_widths` takes max(swell, floor / end width) and the swell (1.10 × the end's width) wins. To go lighter, taper the widths themselves (`C_TAIL`).
- **A taper must start after the bowl's lowest point,** or it thins the bottom and the overshoot goes. `C_TAIL_T` 0.25 lost the c's overshoot (−8 → −1); 0.12 kept it.
- **A heavy weight needs its own numbers.** The 700 read "not enough" at the 400's values. Use per-weight dials that default to the 400's (`_700` suffix, read when `S > 84`).

## 2. The order of operations

1. **Measure the references before drawing.** All of them, on one instrument, in
   Albo's design units.
2. **Measure the pen signature** of the letter you are about to change, and of
   the reference. If they differ in *direction*, stop — nothing about width will
   help.
3. **Decide which link in the chain you are copying**, and say so.
4. **Change the model, not the number.** A dial is right when the model is right
   and the amount is a matter of taste.
5. **Ladder the amount** — 3–5 rungs, rendered as words at reading size — and
   let the owner rule. Never ladder past a broken model; that is churn and he
   will say so.
6. **Gate**, then commit with the measurement in the message.

---

## 3. The instruments, and what each is for

All in `tools/wedge_serif/`, all runnable as `PYTHON_GIL=0 python3 <name>`.

| instrument | question it answers |
|---|---|
| `cmp_g_strokes.py` | what pen is this letter on? one signature, or several? |
| `cmp_aldine_g.py` | the binocular g's anatomy, on a raster so a font and a *photograph* answer the same question |
| `cmp_g_loop.py` | does a closed loop taper, and where |
| `cmp_cap_space.py` | minimum white between two capitals, on the **shaped** pair |
| `cmp_touch.py` | **gate.** all 5,193 pairs; any two letters touching |
| `cmp_aldine_metrics.py` | **gate.** every letter within 10% of its measured target |
| `cmp_cap_weight.py` | **gate.** an italic capital carries its roman's weight |
| `cmp_aldine_glitch.py` | **gate.** seven classes of union artifact |
| `cmp_aldine_straight.py` | how much dead-straight outline the face carries (a REPORT — it returns 0 whatever it finds) |
| `cmp_joints.py` | every place two strokes meet, ranked — notches and spurs |
| `cmp_vs_coelacanth.py` | all 62 alphanumerics against the reference, worst-first, as a table graphic |
| `proof_words.py --title` | a title-case page: the densest word for every initial, so every capital is shown against lowercase |
| `trace_g.py` | a reference letter's centreline and width, ring by ring (research only — see §1d) |
| `refs_registry.py` | **gate.** the references and their TRUE slants |
| `proof_words.py` | a proof built from the owner's own corpus |
| `proof.py` | the one renderer. Every row is a BASELINE. |
| `instruments/glyph_view.py` | **the drawing loop**: glyphs straight from the live builder (`outlines.build.draw`), 0.1 s each, no font build |
| `instruments/glyph_overlay.py` | your glyph under every reference's outline, all unsheared by MEASURED slant (`refs_registry.py`); prints c/o width |
| `instruments/glyph_zoom.py` | 4× zoom of a join with every outline vertex dotted and the glyph's own construction points marked; where corners and S-curves show |
| `instruments/ref_sheet.py` | one glyph from many fonts at ONE x-height; the picture that diagnosed the italic c (§1h) |
| `instruments/terminal_weight.py` | a c's top and bottom terminal over the stem, and their ink-area ratio (a proxy; a spike inflates the run, so trust the area) |
| `instruments/word_rows.py` / `reading_rows.py` | the compact labeled option image, and the reader-size rows (unhinted, 2-bit, NEAREST). **Only `reading_rows.py` is the reader's pipeline.** `word_rows.py` is 8-bit, and it kerns with `FT_Get_Kerning`, which reads only a legacy `kern` table. Albo has no `kern` table (its kerning is GPOS), so `word_rows.py` sets Albo unkerned: *To* comes out 726 units wide where the reader draws 614 (2026-10-04, `docs/albo-word-images-2026-10-04.md` §7). Use it for shape options, not for fit |
| `instruments/word_corpus.py` / `word_measure.py` / `word_parts.py` / `word_callouts.py` / `word_proof.py` | his words, per cut, and which letters hurt them: the corpus and the neglect index; each letter's color and gaps in his frequent words through the reader's pipeline, at nine sizes, against six references; the parts that explain each call (stem joins, mouths, bar ends, advances); the ranked call list; and the proof PNGs (`docs/albo-word-images-2026-10-04.md`) |

**Use `proof.py` for every image.** Before it existed, proofs mixed PIL's
anchored and unanchored conventions, so the same letter sat `ascent` pixels
apart between two images for no visible reason — and comparing two proofs was
meaningless.

---

## 4. Instruments lie, and they lie plausibly

This is the part worth the most. **Five instrument bugs in one session, every
one of which produced a believable number**, and three of which were reported to
the owner before being caught.

| what it said | what was wrong |
|---|---|
| g loop contrast **880:1**, **544:1** | a ray fired from a counter's centroid returns **0** wherever it escapes through a gap. Any ratio against that is garbage. |
| Coelacanth's pen contrast **1.50:1**, thin and thick **45°** apart | the ridge test kept only ink in the top 38% of the distance range — which **deletes every thin stroke from the sample**, because a thin stroke's distance is small all along it. The real answer is 2.80:1 at 90°. A broad nib *must* give 90°. |
| `YA` and `YU` merely "tight" | the second glyph was placed at the **unkerned** advance, so the GPOS table was invisible. With it in, those two capitals were **touching**. |
| the `i`'s outstroke reach = **0** | measured against the stem's right edge *at mid x-height* — and entasis makes that bulge past a short exit. |
| Coelacanth slant **−14.0°**, Poetica **−10.7°** | slant measured over `l`,`n`,`m`; a row's midpoint spans two stems and an arch on `n`. Only a single bare stem is valid. A **sign reversal** is too large to be a slant. |

### The rules that follow

- **A surprising number is the instrument until proven otherwise.** Especially a
  very large ratio, a zero, or a sign flip.
- **Validate against a case whose answer you already know.** A broad nib gives
  thin and thick 90° apart. If your instrument says 45°, it is wrong.
- **Never threshold a sample by the quantity you are measuring.** Filtering ink
  by thickness before measuring thickness is circular and silently deletes the
  tail you care about.
- **Render it.** Three of the five were caught by looking at the picture. When
  the number and the picture disagree, the picture wins and the instrument gets
  fixed.
- **When you correct a number you already reported, correct the doc too** — a
  wrong figure in an md outlives the conversation.

---

## 5. Tables go stale, silently

Every spacing and weight fault found this session was a **table that had
outlived the letter it was fitted to**:

- the **Y**'s bearings were fitted before round 163 redrew it; `−116` on its
  right described a letter that no longer existed, and `YA`/`YU` touched.
- the **Q**'s kern cells were solved for a tail that later grew and then was
  trimmed; `Qg` fell to 0.002 em.
- the **A**'s left bearing, `−151`, was a good number on the bench and collided
  with ten letters in words.
- **one `hm_exit` served seven letters**, so `i l n m h u a` had one outstroke
  between them — 4 units of spread across six letters.
- the **g**'s loop table stood in for a pen (§1).

**So: after redrawing any letter, re-run the gates that measure its
relationships, not just the ones that measure the letter.** `cmp_touch.py` and
`cmp_cap_space.py` exist because nothing else notices.

And when you must keep a number the owner set by eye, **compensate rather than
overwrite**: raising the A's left bearing by +126 and deepening the four tuck
cells by exactly the same amount left `TA VA FA PA` within 0.0001 em of where he
put them, while every other letter before an `A` gained the space it never had.

---

## 6. Ergonomics: measure the reader, do not guess

The owner's own epub library is the corpus (`outlines/cmp/corpus.py`,
`proof_words.py`). It held 512,344 word tokens and 1,910,349 letter pairs on
2026-09-17. On 2026-10-04 the same root holds 41 epubs and 667,084 words
(`instruments/word_corpus.py`, which also says which cut each word is set in).
The library grows, so re-count it rather than quoting either figure. Use it.
The word-level version of this section, which letters hurt his commonest word
images in each cut, is `docs/albo-word-images-2026-10-04.md`.

Worked example, the bottom outstroke. The question "how long should this letter's
exit be" is answerable: how often does the letter **end a word** (where the exit
is a terminal in white space and can run long), and **what follows it** when it
does not?

```
ch   ends a word   next is round      ch   ends a word   next is round
t       24.2%          34%            h       10.5%          79%   (e 51%)
n       24.1%          74%            u        5.8%          35%
l       15.4%          52%            i        2.7%          40%
```

An `i` ends a word 2.7% of the time — its exit is a connector in 97 appearances
out of 100, so a long free flick was being drawn for a case that never happens.
An `h` is followed by `e` 51% of the time, and a round letter's ink starts set in
from its own edge, so the h's exit has least room to cross. Coelacanth gives the
h **no exit at all**.

Note what this method also does: it tells you when the references **do not**
support a change. Flanker (23–24) and Pagella (23–28) are as uniform as Albo was;
only Coelacanth varies. Say that out loud rather than quietly picking the
reference that agrees with you.

---

## 7. Gates beat prose

A comment is not a control. Every trap in this file that became a script has
stopped recurring; every one that stayed a paragraph came back.

`cmp_touch.py` swept all 5,193 pairs and found **46 touching** — `LA`, which the
owner spotted by eye, was the *30th worst*. `RA` was at −0.145 em. Nobody would
have typed `qj` or `Qg`.

**If you catch yourself writing "remember to…" in a doc, write a gate instead.**

### The discipline every dial owes

**A dial's zero must reproduce the previous round exactly**, verified by
comparing *outlines*, not TTF checksums (a TTF carries a build timestamp, so
md5 always differs). This caught a "no-op" that was not one: replacing a ring's
315° key with keys at 300° and 330°, all at the same width, shortens the segment
wrapping round to the next key and thickens the ring — the `g` changed at a
default that was supposed to be inert.

---

## 8. Structural gotchas that cost real time

- **The fitting band cannot see a descender.** `outlines/build.py` fits a glyph
  from ink inside its x-height or cap band, so `q`'s tail, `Q`'s tail and `f`'s
  hook are invisible to their own bearings (`g` and `J` are excepted by name).
  Do **not** "fix" this by fitting them on full extent: `q`'s tail reaches far
  right *below* the baseline, so that would space `qu` — very nearly every q in
  English — by ink nowhere near the `u`. It is a pair problem; kern it.
- **Shear is applied at BUILD time.** Glyph code is unsheared design space.
  Unshear every reference before comparing — by its **measured** slant, never
  `post.italicAngle`, which is **0 on two of the five references** and wrong by
  ~1.8° on two more.
- **`widths()` smoothsteps between keys**, so a sparse width table puts a
  curvature jump at every key and the edge facets. Prefer a closed-form function
  of `t`.
- **A hump bow and a waist cancel** on the edge where they meet. Doing both of
  the obvious things to un-rule a straight stroke can leave one flank straighter
  than it started.
- **`con()` is a normaliser, not a scaler.** It returns the target contrast
  whatever goes in, so "a swayed path varies its own width for free" is false.
- **zsh does not word-split unquoted variables** — `env $E python3` silently
  builds the wrong font. Inline the env vars.
- **`outlines.build` takes its output dir as `sys.argv[1]`**, not `--out`.
- **Build the control arm with NO dials.** On 2026-09-28 a helper that added the
  arm's shared settings to every build also added them to the "default" build.
  The default then compared DIFFERENT against the shipped font, and nearly read
  as a regression. A default-identity check is only honest from a bare
  environment.
- **A script run by zsh may not get the shell's python.** `python3` there can
  resolve to another interpreter, which died on `PYTHON_GIL=0` with "Python
  runtime state: preinitialized". Name the interpreter by its absolute path in
  scripts (the asdf shim). `${(P)name}` needs `${=${(P)name}}` to word-split.
- **Another agent in the same tree: stage only your own hunks.** If someone else
  has uncommitted edits in the file you are shipping, build in a clean
  `git worktree` off HEAD, then `git diff > p; git apply --cached p; git apply p`
  in the main tree. Their work stays unstaged and out of your commit (round 435).

---

## 9. What the owner rules, and how to ask

He rules on **pictures**, not numbers — and on words at reading size, not on
letters at display size. So:

- publish a real rendering; a described option is not an option
  (`p0-render-visuals-never-prose`);
- PNG at native pixels, never JPEG, never CSS-scaled;
- one question per turn;
- a ladder is 3–5 rungs with the current state labelled, and **state the cost of
  each rung** — pushing the outstroke variation past 1.0 put three pairs under
  the spacing floor and one pair touching, which the gate found and the eye would
  not have;
- he may pick a value **past the top of your ladder** (`Y_LBOW` 41 off a ladder
  ending at 36). That is his call, not an extrapolation for you to second-guess.

---

- **lead with ONE small image** (2026-09-26: *"just show me a small image with
  all your recs"*): the word image at reading size, today on top, each option
  labeled beneath. He then rules in one line (*"yes to everything but the
  straight italic apostrophe"*, *"j wins"*). Long proof pages come second.
- **for a continuous dial, give him sliders across the FULL range** (2026-09-26:
  *"present this in an interactive way so i can slide between full range"*),
  one slider per dial, every step a real render, shipped and recommended
  marked, "Copy picks" JSON back.
- **a change he cannot see is not an option.** 2026-09-26: *"i dont see
  differences in thick thin"* -- the arms moved under a pixel at reading size.
  Measure visibility at the phone's 2x before showing, and say "sub-pixel"
  plainly; offer one arm strong enough to see.
- **"decide blind" is a real answer**: ask the question without the picture
  when he says so. A misclick is re-asked, and the record says it was.

## 10. The honest reflection

What produced value this session: the **corpus** measurement of the outstroke;
the **collision sweep**; the **pen-signature** instrument and the one-pen fix;
the capital re-spacing; and — after the owner said the work so far was worthless
and to go and understand the strokes — the three rules in §1b–§1d, each of which
had been costing rounds unnamed.

What was worthless: every round spent tuning the g's loop *width* — a table
re-phased, a thin-at-angle dial, a run-out ladder, a taper amount — because the
loop was on the wrong pen and no width could fix that. Also: three ladders built
and sent before the model underneath them was checked.

The pattern is one sentence. **I tuned parameters of a model I had not verified
was the right model.** The check that would have caught it existed, was written
in this repo three days earlier, and took one command to run.

> Before you turn a dial, measure whether the thing the dial controls is the
> thing that is wrong.

## Two more instrument bugs, 2026-09-18 — the survey's slant sign and its crop edge

Six and seven in this file's series, and like the five before them each
produced a believable number that was acted on. Both live in
`tools/wedge_serif/cmp_weight_survey.py::raster` (the slant one also in
`cmp_g_strokes.py`), both are fixed, and both were found not by reading the
code but by two agents measuring a case whose answer is known: a bare stem's
lean, and a Z's bar against its own outline.

1. **The slant sign.** `Image.AFFINE` maps *output* to *input*, so the "unshear"
   with a positive `k` doubled the shear. The italic `l` leaned +12.2° at slant
   0, **+24.0° at `--slant 13`**, −0.8° at −13. The default was +13. Every
   italic weight in `docs/albo-weight-survey-2026-09-17.md` and in rounds
   208–219 was taken at 26°. The owner's rulings in those rounds were made on
   pictures and stand; the *numbers* beside them do not, and the ones that
   mattered were re-measured — the 6/7/8 match of round 212 holds (65.1 / 65.5
   / 63.2 on the fixed instrument).
2. **The crop edge.** The mask was cropped to the ink's bounding box before the
   chamfer, so any stroke on the box's edge had no background beyond it and
   read at up to twice its width. It inflated every letter whose thick stroke
   is its outer edge — the roman Z (+65% → −23%), W, E, F, L, T, I, the 7's
   bar, the 2 and 5 — and it is why the misfit audit's roman table led with a
   letter that was never heavy.

The rule these add to the five above: **an instrument's first run must include
a case whose answer you already know.** A bare stem has one width and one
angle; a bar has the thickness its outline says. Neither had been checked.

## 2026-09-18, round 226 — "I don't see a wobble difference": the wobble is the polygon

The owner asked for most of the wobble to come out; round 225 cut every
deliberate irregularity to a third (`ALBO_HAND_SCALE` 0.3) and he saw no
difference. Measured, he was right: **the imperfection layer moves the italic
lowercase by zero units** and the roman lowercase by ≤ 8 (the i's dot). The
tables live on A g Q R Z X E F T; the `LIFE` jitter is a fifth of a pixel at
13 px by design. None of it is what reads as wobble.

**What reads as wobble is the export.** Every contour leaves the builder as a
dense polyline at ~11-unit spacing, unioned facet by facet and rounded to the
integer grid. A curvature-noise measure (the second difference of the edge's
angle per 10 units of contour, on the flattened outline):

| | n | m | o | e | a | s |
|---|---|---|---|---|---|---|
| Albo italic | 19.8 | 21.1 | 6.1 | 11.3 | 11.7 | **129** |
| Albo roman | 16.7 | 19.5 | 4.4 | 7.6 | 11.5 | 8.3 |
| Georgia italic | 3.1 | 3.1 | 2.1 | 4.1 | 2.6 | 1.6 |
| Flanker Griffo | 0.7 | 0.7 | 0.9 | 1.1 | 1.2 | 1.4 |

Albo's edges are 3–20× noisier than the references'. The n's and m's arches
turn 12–28° at individual facets. That is the "hand-drawn" look he is calling
wobble, and it is not a table — it is the union of stroke polygons.

**Three export-side cures were built and none ships** (`ALBO_CURVES`, default
0, keeps the code; `geom.fit_curves`):

1. *Corner-preserving averaging* of the polygon — noise went UP (n 19.8 → 26.3)
   because the integer grid re-quantises the moved points, and small marks
   shrank up to 24%.
2. *Least-squares cubic fitting* between corners — noise down 2–25×, but the
   fit drifts: a heart's inner contour left its polygon by 144 units and the
   roman e's tail pinched to 2 units at every tolerance tried.
3. *Catmull-Rom interpolation* through every third point, clamped handles,
   per-run verification with polygon fallback — safe (area change median
   0.02%), but it can only fit the runs that are already gentle, which
   excludes exactly the faceted arches; n 16.7 → 14.7, still five times
   Georgia, with two pinch findings per style from tips.

**The fix is upstream, and it is a round of its own**: the strokes have to be
smooth before they are unioned — width functions sampled without per-point
noise, or the union followed by a curve-aware smoothing that knows a hairline
from a bowl. Recorded here so the next attempt starts from these numbers and
not from the tables again. `ALBO_HAND_SCALE` stays at 0.3: the capitals'
hand cuts (Q R Z) were visible and he asked for less.


## 11. What the owner said about making type, 2026-09-24 → 26 — read before any round

Collected at his request (*"reflect on everything I have said about font making
and update md files"*). Each line is his words, then what it binds. Earlier
standing rules live in §0 (the brief), §9 (how to ask), `docs/fjord-glyph-guide.md`
§0, and `docs/albo-imperfections.md`; this section adds what this stretch taught.

**On drawing**
- *"those are crappy variations. do better with more 7 leg tweaks and 2 that
  joins in a smoother way. i need albo style."* — A variation is a DESIGN MOVE
  in Albo's own pen (stroke direction, where it thickens, the 20° pen cut, the
  28° finial face, the Aldine cursive flow), never a one-parameter nudge. The
  standing rule from 2026-09-13 already said it: **glyph drawing is not
  delegated** to subagents; they measure, gate and render ladders. This week
  broke that rule (apostrophe, 2/7, worst-characters arms were drawn by
  subagents) and the 2/7 variations came back rejected. Before offering
  drawings, render them beside the letters they must live with and cut the ones
  that don't read as Albo.
- *"trace other reference fonts and come up with original solutions too. take
  three passes."* — Options come in two kinds: TRACED (measured from a named
  reference, redrawn in Albo's pen, never pasted) and ORIGINAL (Albo's own).
  Three passes = draw, measure-and-cut, adversarial review.
- *"make it match the style better"* (italic straight apostrophe) and *"reduce
  apostrophe to match rest of word image"* — marks and punctuation are judged by
  whether they belong to the word image in weight and pen, not by their own
  proportions.
- *"The Roman R should match the optical balance of the bold capital R"*,
  *"check that 'g' is right in bold italic"*, *"check italic and roman are using
  the same nib. italic seems too small."* — **every cut is checked, not just the
  400**, and a letter must hold the same construction and optical balance across
  weights and between roman and italic. (Round 409: the italic was on three
  different pens and drawn 19% narrow; the measurement against 11 real families
  proved his eye.)
- *"interpolated based on my answers what changes would be applicable to all of
  albo fonts"* — a ruling on one cut is a question about all cuts; say how it
  transfers (docs/albo-weights-transfer-2026-09-26.md).
- *"take a pass at balancing out the thick and thin strokes for better word
  images"* / *"give me the likely letters that would benefit from being redone
  because optically they are outliers ... determine a metric for what is well
  fitted"* — he wants the outliers found by a stated, validated metric
  (docs/albo-fit-audit-2026-09-26.md), then options, then his pick.

**On spacing and the model**
- *"we're trying to get a strong model not overfitting"* (ruling out pinning his
  answers) — his bench answers are TRAINING DATA; the fit decides every pair;
  held-out error is the score. He is consistent to ~10.7 units; no answer is
  gospel, including his own.
- *"i corrected the ones that needed it the most but mostly skipped the ones
  that didn't"* — a skip means "fine as shipped" (= 0).
- *"it seems overdue to see what other existing tools can offer"* — survey and
  RUN existing tools before building; record the negatives
  (docs/spacing-tools-survey-2026-09-26.md, docs/hard-pairs-eval-2026-09-26.md:
  no vision model and no existing spacer beats the fit on his answers).
- *"todo: check kerning on 'bowl'"* — a screenshot note is a bench row, not an
  opinion to argue with.

**On rendering and shipping**
- *"no hinting wins"* — judge on what the reader actually draws (Albo unhinted
  since round 401); every weight judgment before that was on a heavier rendering.
- *"the most recent albo version needs to make it on update"* — every Albo
  change ships to EVERY channel the same day: TestFlight bundle AND the
  `fonts-latest` release (republish from the validated seed tree).

**On reading (not type, but the same taste)**
- *"those all stink. i need new ways to read not gimmicks"* — evidence over
  effects; see docs/research-new-ways-to-read-2026-09-26.md.

**The reflection.** The rounds that landed first time (thick/thin sliders, the
e bar, j wins, m for the italic) all had three things: a measured reason, real
renders at reading size, and a single compact picture to rule from. The one that
failed (the 2/7 variations) had parameters instead of pen-drawn design and was
drawn by a subagent. Draw it yourself, in the pen, and cut before you show.
