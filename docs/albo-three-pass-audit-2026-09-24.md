# Albo: three passes over all four cuts, 2026-09-24 (round 384)

The owner asked: *"take three passes at all albo fonts, find any issues and fix them present me before and after proof"*.

- **Proof page** (before/after, every cut): https://claude.ai/artifact/2NdNHhn8xVHkzzBjJGw8Kk
- **Surveyed:** HEAD `f1c8093`. All four cuts were built with `albo_build_all`: Regular, Italic, Bold and BoldItalic.
- **Why the bolds had never been swept:** `gates.sh` covers only Regular and Italic.
- **Instruments, on every cut:**
  - `cmp_contour_hairs.py` (the full sweep and `--letters`)
  - `cmp_aldine_glitch.py --ttf --all`
  - `cmp_touch.py`
  - `cmp_counter_dents.py`
  - `approved.py --check`
  - `cmp_outlines.py`, used as the scope proof against the baseline build
  - every finding was also looked at magnified
- **How sure:** every finding below is verified against the built TTF, and every fix was re-measured on a rebuild.

## Pass 1: what the instruments found

| Class | Where | Cause |
|---|---|---|
| Hairs: spurs under 8 units | Bold `m` (2 units, at the notch between its arches), Bold `Œ`, `œ`, `¸`, `¢`, `µ`, `ŋ`, `¤`, `♗`, `₈`, ﬂ/ﬄ, U+E001/E003 | Some come from the curve fit (`m`, `Œ`, `♗`: the dense drawing is clean, probed per glyph). Others are in the drawing itself (`¤`, `″`, `✓`, `✔`). Round 295's `geom.despike` only runs on the no-curve fallback path. |
| Guillemets `« »` collide | Bold and BoldItalic: a 760-unit hole trapped between the chevrons (glitch SPECK) | The gap was a fixed `XH*0.20`. It leaves 26 units of white at the 400 and −1 at the 700. |
| `″` merged | All four cuts | The second prime sat 0.60 S to the right, but a prime's top is 0.91 S wide. |
| `⇒ ⇐ ⇔` | All cuts: shafts jutting past the barbs. At the bolds the two shafts nearly merged (a 7-unit slit). | The shafts ran to the tip's x. The gap was a fixed `XH*0.13`. |
| `√` crack | All cuts: a white triangle at the join | A polyline stroke folds at a sharp vertex. |
| `✓ ✔` | Crack at the vertex in all cuts. The Bold heavy check came out as a slab plus a reversed sliver. | Same fold. |
| `≤ ≥` | Regular: a REVERSAL on 200-unit arms. Every cut: a flat 12° wedge beside the `<`'s 49°. | Chevron height `0.09 XH` over a `0.82 XH` run. |
| `♠ ♤` | The foot floated free of the lobes. The outline spade's foot was a separate trapezoid with a crack inside it. | The stem stopped at `CAP*0.10`; the lobes bottom out at `CAP*0.17`. |
| `♣ ♧` | White slivers between the lobes and a stub of stem between them. The outline club was three loose rings. | The lobes only touch. |
| `¥` | BoldItalic: a crack where the bars cross the arm. | The union of the bars and the italic Y. |
| Kerning | BoldItalic `q'` −0.0049 em (TOUCHING) and `q"` 0.0008. Regular `fT` 0.0048 (it had sat in the gate baseline, never kerned). Bold `QQ` 0.0114. | Pairs measured on the 400 and not re-checked at the 700. |

**Checked and CLEAN in pass 1:**
- **SPLITs:** every one is expected. That covers quotes, `…`, `¨`, `¡`, the fractions, the italic `Y`'s ruled hairline gap (`docs/albo-hairline-gap.md`), and the PUA/`ﬆ` two-island glyphs.
- **Counter dents:** none at the 700s. The one Regular `&` dent is the documented exception.
- **`--letters` hair sweep:** clean on Regular, Italic and BoldItalic. The Bold failed only on the `m` above.
- **Approved g's:** unchanged.

## The fixes (all tagged ROUND 384 in the source)

- **`outlines/build.py` `_despur`:**
  - At export, it removes an ON-curve vertex between two on-curve neighbors when all of these hold:
    - it turns past 150°;
    - its shorter arm is under 8 units;
    - it stands no further off the neighbors' chord than that arm.
  - That is the gate's own definition, narrowed so that a wedge or arrow tip (two long arms) and a curve junction can never qualify.
- **`outlines/build.py` `PHASE_LEGACY`:**
  - **The cut-phase ripple, contained.** The cut's phase counter is global, and six fixes changed a glyph's contour count (`″ √ ♠ ♣ ♤ ♧`). The first build of this round therefore moved 60 untouched glyphs of the 400s: the Greek, the superscripts, the fractions and the ligatures.
  - Those six now consume the phases they used to. After that, `cmp_outlines.py` against the pre-round build moves only the glyphs a fix names: 17 Regular, 20 Italic, 20 Bold, 20 BoldItalic.
- **`symbols.py`:**
  - The guillemet gap is `max(XH*0.20, stroke*(1+0.70)/sin a)`. 0.70 is the italic 400's own white ratio, so both 400s are byte-identical.
  - The `⇔` family:
    - The shafts end at the barbs.
    - The gap is `max(XH*0.13, 2*stroke)`.
    - The barbs reach a stroke past the outer shaft.
    - At both 400s the constants still win.
  - `≤ ≥` use the `<` chevron.
  - `″` is spaced by its own top width × 1.45.
  - The checks are two strokes joined by a hull at the vertex. The heavy check is the light check under a mitre dilation.
  - `_fill_cracks` (holes under 16 units mean width, measured BEFORE the ink spread, which shrinks them) is applied to `√`, `¥`, the checks and the hollow suits.
- **`symbols2.py`:**
  - The spade's stem reaches into the lobes.
  - The club gets a junction disc and a 6-unit mitre closing, which blunts the 12° V-notch where two lobes meet in the italic.
- **`ligatures.py`:** a 6-unit mitre closing on `ﬄ` only. It removes the slit where the first f's arch runs into the second. The global welder is held to an 8-unit mouth so it can never reach the Y's and P's ruled gap, and this slit's mouth is wider.
- **`kern.py`:** BoldItalic `q'` +20 and `q"` +15; roman `fT` +10; Bold `QQ` +4.

## Passes 2 and 3: what the rebuilds found

- **Pass 2:**
  - The fixes made in pass 1:
    - the guillemets, the double arrows, the radical and the yen;
    - the checks rebuilt as two strokes;
    - the suits' stems and junctions;
    - the export spur pass;
    - the kerns;
    - the phase table.
  - Pass 2 itself found three new problems:
    - The italic 400 guillemets had moved, although they were never flagged. The fix's first white ratio (0.85) was the roman's; the italic's is 0.71. Fixed.
    - Visually, `≤ ≥` were a flat wedge, the Bold `⇔` heads closed into a hexagon, and the Bold `✔` read as two blocks.
    - The ﬄ slit remained.
- **Pass 3:**
  - The BoldItalic ﬄ and the italic outline club were still long 13° V-notches, which a 3-unit closing does not reach. They were raised to 6.
  - The heavy check's stepped foot was fixed with the hull joint.

**Final state, measured on the last build:**
- `cmp_contour_hairs.py`, full sweep: **0 findings in all four cuts** (it was 11 / 10 / 9 / 9).
- `--letters`: PASS in all four.
- `cmp_touch.py`: 0 touching and **0 under the floor** in all four.
- Glitch: only `♕` remains (below).
- `approved.py`: unchanged.
- `gates.sh`: accepted and GATES UNCHANGED.
- `contours-baseline.txt`: re-accepted with the six count changes.

## Found and deliberately NOT changed

- **`♕` "CRACK" ×2 in every cut.** These are the white queen's crown windows: the hollow of the crown's triangles, a designed opening, 7 units mean width. At reading size they close up by themselves. Filling them would turn an outline queen's crown solid.
- **Regular `&` counter dent.** This is the documented exception (`cmp_counter_dents.py`'s header).
- **`albo_bumps.py` circles:** 227 roman / 231 italic at the 400, 200 / 204 at the 700. That instrument exists for the owner's eye, not for automatic repair, so it was run and not acted on.
- **The Bold heavy check `✔`** is heavy by design. It is now one clean outline, not re-proportioned.
