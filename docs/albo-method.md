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
loop (184), the g's ear against the bowl (185).

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

The same rule states the terminal case: **a terminal is a wedge, not a bar.**
The ear ran 1.10 → 0.62 of its own thickness and stopped on a flat cut, so its
edges stayed nearly parallel and it read as a slab. Coelacanth's closes to a
true point — the two edges converge. Taper to 0.12 and it is a wedge.

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
| `trace_g.py` | a reference letter's centreline and width, ring by ring (research only — see §1d) |
| `refs_registry.py` | **gate.** the references and their TRUE slants |
| `proof_words.py` | a proof built from the owner's own corpus |
| `proof.py` | the one renderer. Every row is a BASELINE. |

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
`proof_words.py`) — 512,344 word tokens, 1,910,349 letter pairs. Use it.

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
