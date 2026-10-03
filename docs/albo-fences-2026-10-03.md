# Albo: every fence past the ascender and the descender (2026-10-03)

**Owner ruling (2026-10-02, answering "what should happen to the italic brackets
after round 466?"):** *"extend them so they are higher than ascender and lower
than descender. adjust all."*

**Status: the RULE is ruled; the MARGIN is an option.** E1 / E2 / E3 put
every fence 10 / 25 / 40 units past both lines. The mechanism is
`ALBO_FENCE_SPAN=1` with `ALBO_FENCE_OVER` (`tools/wedge_serif/outlines/build.py`).
With the span off (the default until the ruling) the build is byte-identical
to round 467 in all four cuts (control build).

"All" is read as **every fence in every cut**:
- the glyphs ( ) [ ] { } | ¦;
- in the Regular, Italic, Bold and Bold Italic.

It also settles two questions that were queued:
- the roman parentheses sat low in the same way the italic ones had;
- the fence kerns around letters redrawn since they were measured had gone
  stale.

## 1. Where the fences stood (round 467)

The fences are round 98's: from the descender depth to the cap height, raised
50 units (`marks.FENCE_RAISE`), and the parentheses 16 units longer at each
end. The italic parentheses have been raised 48 more since round 466.

Against each cut's own letters, where the ascender is the tallest of b d h k l
and the descender the deepest of g j p q y:

| cut | ascender | descender | ( over the ascender | ( under the descender |
|---|---|---|---|---|
| Regular | 771 (l) | −298 (j) | −37 | −47 |
| Italic | 783 (l) | −295 (j) | 0 | −92 |
| Bold | 771 (l) | −317 (j) | −29 | −52 |
| Bold Italic | 801 (k) | −303 (j) | −11 | −86 |

So no cut's parentheses reached below its descender, and only the italic's
reached its ascender. The brackets, braces and bar are shorter still: [ runs
−231..726 in every cut.

The deepest descender is the j in all four cuts. In the Bold Italic, the
tallest ascender is the k, not the l.

## 2. The mechanism

`build.draw` measures the lines once per process from its own output:
- the tallest of b d h k l and the deepest of g j p q y, after the italic's
  lowercase scale (`IT_LC_SCALE`) and the ink spread, so they are the shipped
  ink;
- not the italic f, whose hook stands over the line (799 in the Italic).

It hands every fence builder `c["fence"] = (top, bottom)`, the lines plus
`FENCE_OVER`. It then draws once, measures, and corrects once, so the fence's
INK lands on the lines whatever its pen does at its cut ends. Measured, every
fence lands within one unit, in all four cuts and all three margins.

- **The builders** (`marks.paren`, `marks.bracket`, the three `symbols` brace
  constructions, the bar and the broken bar) take those lines when given. They
  draw their old geometry when not: no stretch, so stroke weights are kept.
- **The broken bar** keeps its gap on `MID`, the lowercase's optical middle.
- **The italic parentheses' round-466 raise** (`ALBO_ALD_PAREN_RAISE`) does not
  apply under the span, which places them by the lines.
- **A redrawn ascender or descender moves the fences with it.** A table of
  heights would go stale silently (`docs/albo-method.md`).

## 3. The fence kerns, re-measured whole

Every fence's height changed, so `local_ai/fences.py` re-measured the whole
fence block, all fences in all cuts. For each arm it ran on an
`ALBO_FENCES=0` build of that arm's outlines, written to a candidate table.

Balance after, as close − open across the 62 letters and figures
(`fence_gap` band gap):
- **each arm:** mean within ±0.9 and worst 6 units, for every fence in every
  cut;
- **round 467:** the italic [ ] was 15 units off and { } 14. Those kerns were
  measured before the italic x and a were redrawn (rounds 461–462), so every
  arm also fixes those.

## 4. The arms

| arm | `ALBO_FENCE_OVER` | Regular ( span | Italic ( span |
|---|---|---|---|
| today | (span off) | −251..734 | −203..783 |
| E1 | 10 | −309..782 | −305..794 |
| E2 | 25 | −324..797 | −320..809 |
| E3 | 40 | −339..812 | −335..824 |

**Gates, each arm against round 467:**

| gate | result |
|---|---|
| outlines moved | the eight fences, nothing else, in each cut |
| touch | 0 / 0 |
| hairs | none new |
| glitch | 0 findings on the fences, before and after |
| counter dents | 1 → 1 |
| contour census | unchanged |
| approved letters | unchanged |
| e mouth | ok |
| POOR GATES | no delta |
| kern classes | ok (worst: Bold Italic 124 / 160) |

## 5. Reproduce an arm

    cd tools/wedge_serif; source build_env.sh; O=25
    (all four cuts) env "${ALBO_ROM_ENV[@]}" ALBO_FENCES=0 ALBO_FENCE_SPAN=1 ALBO_FENCE_OVER=$O PYTHON_GIL=0 python3 -m outlines.build F --style Regular   # and Italic, Bold, BoldItalic
    cp outlines/spacing_b2.json /abs/tab.json
    (cd local_ai && ALBO_SPACING_TABLES=/abs/tab.json $VENV/bin/python fences.py F)
    (all four cuts) env "${ALBO_ROM_ENV[@]}" ALBO_SPACING_TABLES=/abs/tab.json ALBO_FENCE_SPAN=1 ALBO_FENCE_OVER=$O PYTHON_GIL=0 python3 -m outlines.build A --style Regular
    $VENV/bin/python instruments/fence_proof.py PROOF today=<round 467> E1=... E2=... E3=...

To ship: set the span on and the margin in `build.py`, regenerate the fences in
the real table, run the clearance loop, and retire `PAREN_RAISE_IT`.

Proof page: https://claude.ai/artifact/9UnfAUMqzng8u8NeQtQrrw
