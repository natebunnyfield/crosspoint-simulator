# Albo: the pictographs redrawn, and a fracture sweep, 2026-09-24 (round 385)

The owner asked for three things:
- *"improve the chess, card and other symbols. they are distractingly weird currently."*
- From the round-384 proof page, the bold guillemets and the bold double arrow. Also *"address the weirdness and stray hairy mess in symbols"*.
- *"correct any fractures like this one from yen character"*. He sent a crop of a small nick breaking a stroke's edge.

**Surveyed:** HEAD `901a6ae`, with all four cuts built by `albo_build_all`. Every finding was checked in the built TTF, and every fix was re-measured on a rebuild. "Verified" below means measured on the final build.

The standing round-100 rulings this round finally acts on:
- *"use standard stanton or ascii or unicode shapes for chess symbols"*.
- *"use albo style for all symbols (arrows should match their words better, not be distractingly anachronistic)"*.

Both sat unaddressed in `docs/wedge-serif-exploration.md`, items 9 and 10.

## The references

These were measured side by side with the TTFs:
- **Apple Symbols:** chess, suits, notes.
- **DejaVu Sans / Sans Bold:** chess, suits, ⇒ ⇔.
- **STIX Two Math:** chess, suits, ⇒ ⇔.
- **Times New Roman / Bold:** guillemets, suits, arrows.
- **Georgia Bold:** guillemets.

For behavior in the italic, five italic text faces:
- Times New Roman Italic, Arial Italic, Courier New Italic, Georgia Italic and Verdana Italic.
- **Every one keeps the suits, the notes, the squares, circles and triangles, and the arrows UPRIGHT.** Times, Arial and Courier carry the whole set. Georgia and Verdana carry only the note.
- The same faces slant ¶ and §.

## What changed, symbol by symbol

### Chess: the twelve pieces (`symbols2._piece`, `_chess`, `_hollow`)

**What they were:**
- One trapezoid body under every piece.
- A cross-topped slab for the king.
- A three-pronged star for the queen, with ten contours in the white piece: two crown windows that the glitch gate called CRACKs, and hollow balls.
- A pentagon with a triangle bitten out for the bishop.
- An eleven-point polygon for the knight.
- All of them sheared in the italic, so they leaned as if falling over.

**What they are now:** Staunton figurines, following the grammar all three reference faces share.
- **The base:** every piece stands on a plinth with a cushion, then a waisted body flaring to the foot, then a collar.
- **The heads:**
  - king: a flared crown with a domed top and a cross;
  - queen: a cup coronet with five points, each carrying a ball;
  - rook: a turret wider than the tower, with three merlons and two crenels;
  - bishop: an ogive miter with a slit running down to the right, and a finial ball;
  - pawn: a ball on the collar;
  - knight: a horse head facing left, with ear, forehead, muzzle, the notch under the jaw, a full chest and an eye.
- **The heights step up the rank** (fraction of cap height): pawn 0.74, rook 0.86, knight 0.94 (built 0.99), bishop 0.97 (0.99), queen 1.00 (0.97), king 1.06.
- **Width:** 0.62-0.70 of the cap height. Before, it was 0.72-0.92, and 1.03 on the italic queen.
- **Advances:** 543-597 at the 400. Before, 608-812.

**The white piece:**
- It is the black silhouette's outline, plus the interior rules a figurine carries where the black piece steps: the plinth's top and the collar.
- Small parts (balls, the ear tip) are filled rather than left as specks.
- The outline grows with the square root of the stem: 28 units at the 400, 37 at the 700. Round 100 fixed it at 28 because a pen-derived width closed the old pieces' counters.
- **The narrowest counter, verified:** 29 at the 400 and 24 at the 700, both the rook's merlon interiors. The gate's floor is 12.

All twelve pieces are upright in the italics (`symbols._upright`).

### Suits: ♠ ♥ ♦ ♣ ♤ ♡ ♢ ♧ (`symbols2._heart` …)

**What they were:**
- The heart was two circles on a straight-sided triangle.
- The spade was the same shape inverted, on a trapezoid foot.
- The diamond was 0.55 as wide as tall.
- All stood about 0.76 of the cap height, a quarter under the capitals they sit beside in a bridge hand.
- They were sheared in the italic.

**What they are now:**
- **Heart:** convex cubic curves to the point, with no straight edge.
- **Spade:** the heart inverted, with a stem leaving the cleft and flaring in two concave curves to a foot.
- **Club:** three lobes merged, on the same foot, keeping round 384's junction disc and 6-unit closing.
- **Diamond:** 0.72 wide to tall, with faintly concave sides.
- **Size and position:** 0.90-0.93 of the cap height, on the baseline. The points dip by half the round overshoot.
- **In the italic:** upright.

**Two defects in the new drawing, both fixed:**
- **The foot's tip.** The concave flare met the baseline almost tangent, a 168° REVERSAL. It now lands on a short upright edge.
- **The hollow foot.** The outline left a 17-25-unit white needle inside it, past round 384's 16-unit fill. The hollow suits are now filled below 40. Their real counters measure 119 (♧ at the 700) and up.

### Music (`symbols2._note`, `g_natural`, `g_sharp`, `g_flat`)
- **♪:** the flag was a four-point polygon. It is now a curved teardrop.
- **♮ was drawn as an H.** Both stems ran almost the full height, and it is now engraved:
  - the LEFT stem rises above the upper bar and stops at the lower;
  - the RIGHT stem starts at the upper bar and runs below.
- **♮ ♯ weights:** the bars are the heavy strokes (1.45 MATH) and the stems the light ones (0.45 TH_V), as engraved.
- **All six are upright in the italics.**

### Pilcrow ¶ (`symbols.g_paragraph`)
- **Before:** the font's P with its counter filled, plus a second stem. That put the solid bowl *between* the two stems, making a block at the 400 and a capital A in the italic.
- **Now:** the reference construction:
  - two light stems (0.55 of the cap stem), with a stem's width of white between them;
  - a solid reversed-D bowl hanging off the LEFT stem, from the cap line to 0.42 of the cap height;
  - a flat top joining the stems;
  - no foot wedges. Round 272's inner feet had met at the 700.
- **In the italic:** it slants, as the references' does, with no chancery exit hook on its stems.
- **Advance:** 696 → 408 at the 400.

### Geometric shapes
- **Upright in the italic.** A sheared ■ is a parallelogram, a different sign.
- **○** was the pen's ring, with the letter o's thick-sided stress. At the 700 it read as an **o**. It is now monoline, as □ and △ are.

### Guillemets « » ‹ › (bold cuts only; `symbols._guillemet_heavy`)
- **Before:** at the 700 they were the 400's 180-unit monoline chevron with its stroke nearly doubled (32 → 57). A chevron was a third stroke thick, with two butted round ends at the point.
- **Now** (above stem 84), one tapered polygon (`_chevron`):
  - 0.56 of the x-height tall;
  - a sharp point;
  - the pen's contrast: the arm falling to the right is heavy, the one rising is light;
  - ends cut level, as in Times New Roman Bold and Georgia Bold;
  - the gap keeps round 384's white ratio (0.70) against the heavy arm.
- **The 400s are byte-identical.** Their construction is kept below `GUIL_PEN_ABOVE`, and `cmp_outlines` confirms they did not move.

### Arrows → ← ↔ ↑ ↓ ↕ ↗ ↘ ↖ ↙ and ⇒ ⇐ ⇔ (`symbols._arrowhead`, `_arrow`, `_darrow`)
- **Before:** the heads were pen strokes butted at the point. At the 700 they piled into a knot, and the bold ⇔ read as "a lumpy hexagon with barbs".
- **The head is now `_arrowhead`,** as in STIX Two and Apple Symbols:
  - two curved barbs bowing toward the shaft, tapering to level-cut ends;
  - one sharp point;
  - the white between the double arrow's shafts running in to an inner corner.
- **The shafts are plain rules.** The single arrow's tail used to carry the pen's slanted cut, a letter's terminal on a sign. Each double-arrow shaft ends in the middle of the barb it enters, measured on the head.
- **Size.** At 20 px the old → and ⇒ read as a dash and an equals sign.
  - Horizontal arrows are 0.75 em long (ARROW_LEN_H, 1.75 x-height). They were 0.57 em. Times and STIX run 0.9-1.0 em.
  - Heads reach 0.32 x-height (→) and at least 0.40 x-height (⇒) off the axis.
  - The barbs are about 1.8 strokes thick at the point.
  - Vertical and diagonal arrows keep the old length, or they would drop through the baseline.
- **Arrows are NOT made upright in the italic.** The references keep them upright, but the owner's round-100 ruling asks arrows to match their words. That is left for him.

### √ (`symbols.g_radical`)
- **Before:** a pen stroke through three points with a swelling width, folded at the V and crack-filled. At the 700 the long leg carried a 9-unit step two-thirds of the way up.
- **Now:** one monoline mitered path (tick, V, long leg, bar), the construction of Albo's other mathematical signs.

## The fracture sweep: all glyphs, all four cuts

**The instrument is new:** `tools/wedge_serif/cmp_jogs.py`.
- **What it finds:** a short run of outline (up to 18 units) that turns sharply one way and back, with net turn ≤ 25°, between two smooth flanks. That is a step or nick in an otherwise continuous edge.
- **Why existing gates miss it:**
  - `cmp_contour_hairs.py` needs a turn past 150°;
  - `cmp_aldine_glitch.py` needs a hole or a pinch;
  - `albo_bumps.py` circles every facet.
- **Limit: it misses the yen's own nick.** Its flanks are not smooth enough, so it is a finder, not a gate.

**Counts of glyphs with a jog of 3 units or more,** before → after:

| Cut | Before | After |
|---|---|---|
| Regular | 16 | 5 |
| Italic | 15 | 11 |
| Bold | 29 | 15 |
| BoldItalic | 27 | 22 |

**What was fixed (letters: judge these separately, before/after in the round's proof):**

| Glyph | Defect | Fix |
|---|---|---|
| ß (all cuts) | The stem's flat top stood out of the shoulder as a square step: 11.5 (R), 10.6 (It), 11.3 (B). The italic entry flick made a spur. | Stem stops inside the shoulder, swell spread, no italic entry; `geom.ease_step` over the join. |
| ſ, ﬁ ﬂ ﬀ ﬃ ﬄ, PUA fb fh fj fk | The f's stem top-left corner stood out of the hook, 4.7-6.4 units. This is the defect R20 fixed on the f. | R20's `flush` join via a new `finial=False` switch. The ligature hooks are unchanged. |
| Italic f-ligatures, ſ | A hair where the italic ENTRY flick drawn at a stem top poked out beside the hook: f stem, ligature i and l. | `it_entry=False` on those stems. |
| ﬀ ﬃ second f | Same step, not buried by the first hook (it ends 76 units above). | `geom.ease_step` on its left half only. The flush there turned the hook-to-hook slit into a needle. |
| υ ψ | The round stroke left the stem wider than the stem: 6 (R), 10 (B). | It leaves at the stem's width (`_ent`). |
| φ | The loop met the stem's flat top at a slant: 6.5 (It), 17 (BI). | The loop arrives vertical at the stem's width, plus a stem-wide ease. |
| β | The stem's flat top stood where the leaning curve had left it: 9.4 (BI). | Stem stops 30 units into the curve, plus ease. |
| Italic Greek (β φ ω) | The roman `ent` ratio was used with the italic hand's pen. | `ItalicHand.ent()`. |
| Italic ρ | The stem sits 3 units outside the ring (a deliberate round-379 choice), leaving a step at its top: 3.7 / 4.7. | Hull over a band that stops at the stem's middle. |
| Italic Þ | Lowercase entry and exit flicks on a capital: an 8.6-unit spur. | `cap=True`. |
| Italic fh (PUA) | The hook came to rest on the h at a single point after the flush (PINCH 0.00). | Joined with the 6-unit lens. |

**Found and NOT fixed** (reported for a ruling, magnified in the round's proof):

| Glyph | Where | Size | Why left |
|---|---|---|---|
| **¥** | Regular: a notch on the stem's left just under the bars. Italic: a sliver of the right arm poking between the bars. | Visible at 300 px | Another agent is producing ¥ options (instruction). |
| G (BI) | Where the spur's bend meets the arc | 9.6 | Owner-ruled construction (R04, R05, round 238). |
| J Ĳ Ĵ (B) | The stem into the descender | 7.0 | Core capital; a descender redraw is a design question. |
| ð (BI), and italic ð generally | The bar crossing, 14.2 | 14.2 | The italic ð reads as a Cyrillic б: a drawing problem, not a fracture. |
| Ψ | Arms into the stem | 3.8 (R), 6.0 (B), 5.7 (BI) | Small; the arms' construction needs its own look. |
| Italic R, Ŕ Ř Ŗ | Bowl into stem, leg | 6.0, 5.1 | Owner-ruled capital. |
| δ (It) | The crotch where the neck leaves the bowl | 7.1 | A designed join, not a step. |
| ȷ ĵ (It, BI) | Descender curve | 5.0, 6.9 | Small. |
| 4, £, K (BI); D P Þ Ð (BI) | Bar and stem joins | 3-4.3 | Under visibility at reading size. |
| ’ ” | — | 8 | Quote marks are another agent's (instruction). |

**Checked and CLEAN:**
- 1-2-unit jogs at every capital's foot bracket (y 94) and at stem-bar joins. They are invisible at any size, and a 1-unit deviation is 0.027 px at 13 pt.
- The remaining Bold g, m, n and p 2-3-unit ticks.
- The regular 400 guillemets, as drawn.

## Gates on the final build (all four cuts)

| Gate | Result |
|---|---|
| `cmp_contour_hairs.py`, full sweep | 0 findings, PASS on all four |
| `--letters` | PASS on all four |
| `cmp_aldine_glitch.py --all` | No new finding. ♕'s two crown CRACKs and the queens' SPLITs are gone. The only diffs are the PUA ligatures' pre-existing SPLIT areas shifting, and the italic fh's SPLIT, which is resolved. |
| `cmp_touch.py` | 0 touching, 0 under the floor |
| `cmp_counter_dents.py` | Only the documented Regular & |
| `approved.py --check` | Unchanged |
| `gates.sh` | GATES UNCHANGED |

- **Tightened in `cmp_aldine_glitch.py`'s MULTI:** the queen and spade island allowances were removed. An allowance above the drawing's count would hide a real fracture. ♘ (the eye) was added.

**The cut-phase ripple is contained:**
- Nine chess pieces changed contour count, and the italic fh changed only in the italic.
- `PHASE_LEGACY` gains the nine.
- A new `PHASE_LEGACY_STYLE` holds `('Italic', U+E001): 2`. A global entry would have re-cut the roman.
- `cmp_outlines.py` against HEAD moves only the glyphs named here:
  - 54 Regular;
  - 71 Italic, which adds the upright shapes and notes and the hand-drawn ω;
  - 58 Bold, which adds the guillemets;
  - 74 BoldItalic.

## Negatives

- **A 6-unit closing on ﬃ and ﬀ** (round 384's ﬄ fix) sealed the slit between the two hooks into a pocket in the roman. Rejected.
- **The flush join on the second f of ﬀ and ﬃ** turned that slit into a needle, a REVERSAL in both italics. Rejected; that f is eased instead.
- **The first hull box on ﬃ** reached the first f's hook and sealed the same pocket (contours 2 → 3). It was narrowed to 0.75 stem left of the second stem and 0.35 stem above its top.
- **Straight-sided "mitered chevron" arrowheads** read as a lumpy lozenge at the 700. They were replaced by curved barbs.
- **A strongly bowed barb** left the shafts poking out past the head's outer curve.

## RULED 2026-09-25 (owner)

The letter fixes from this pass (proofs 10–12: ß, ſ, the f-ligatures, υ ψ φ β ρ, the italic Þ) are all **kept**, as shipped in build 211.
