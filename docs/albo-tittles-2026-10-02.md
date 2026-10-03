# Albo: smaller tittles that the reader still draws (2026-10-02)

Owner todo: *"reduce tittles slightly without losing them at small scale"*.

**Status: SHIPPED, D2** (owner 2026-10-02, *"D2 wins"*), as round 467
(`docs/albo-round-467-2026-10-02.md`).
- `ALBO_TITTLE_K` 0.90 with `ALBO_TITTLE_DY` 5 (Regular), and
  `ALBO_TITTLE_K_700` 0.90 (Bold), in `tools/wedge_serif/outlines/glyphs/stems.py`.
- They apply to the roman cuts only, since D2 leaves the italics alone.
- They scale the roman i's and j's dot, and the dots in ﬁ, ﬃ, ĳ and U+E002.
- They do NOT touch the dot accents, which keep `TIT_R`.
- K 1.0 with DY 0 builds round 466's dots.

Before the ruling, the status was options D1 / D2 / D3 beside today.

## 1. Where the tittles stand

Equivalent-disc diameter (units), over the i's own stem and over the x-height;
"clear" is the dot's floor above the x-line (`instruments/tittle_measure.py`;
Albo's x-height is its 429 design value):

| | dot | dot / stem | dot / xh | clear (xh) |
|---|---|---|---|---|
| Albo Regular | 90.5 | 1.41 | 0.211 | 0.235 |
| Albo Bold | 159.3 | 1.45 | **0.371** | 0.205 |
| Albo Italic | 82.3 | 1.39 | 0.192 | 0.298 |
| Albo Bold Italic | 121.9 | 1.20 | 0.284 | 0.231 |
| Georgia / Times / Pagella / Flanker Roman | | 1.41 / 1.23 / 1.21 / 1.40 | 0.266 / 0.222 / 0.216 / 0.233 | |
| Georgia / Times / Pagella / Flanker Italic, Poetica | | 1.46 / 1.37 / 1.48 / 1.44 / 1.62 | 0.262 / 0.221 / 0.208 / 0.231 / 0.209 | |

**By x-height:**
- The 400s' dots sit at the bottom of the references.
- The Bold's is far the largest (0.371).

**Against their own stems:**
- The 400s' dots are at the top of the band (1.41 and 1.39).
- That is what round 369 noted: Albo's stem is the lightest of the faces
  measured, so its dot reads large beside it.

## 2. The floor: what "losing them at small scale" means here

The reader rasterizes each glyph once per size: 8–18 pt at 1x and 2x, 150 dpi,
unhinted, four levels. `parts_audit`'s floor is 4 dark pixels (level >= 2) for a
glyph's smallest part. Today's dots, as `instruments/parts_check.py` counts them:

| 1x pt | 8 | 10 | 12 | 14 | 16 | 18 |
|---|---|---|---|---|---|---|
| Regular i | 1 | 4 | 4 | 4 | 7 | 9 |
| Italic i | 1 | 2 | 2 | 4 | 6 | 7 |
| Bold i | 4 | 9 | 13 | 15 | 24 | 29 |
| Bold Italic i | 3 | 4 | 8 | 11 | 12 | 15 |

- **The Regular** sits exactly on the floor at 10–14 pt on the X3.
- **The Italic** is already under it at 10 and 12 pt. That is why round 440
  grew it, and growing it did not fully clear it.
- **The bolds** have room.

**The no-loss rule used below:** no raster may fall under min(4, today's count).
- Where a raster is on or above the floor, it may not drop under it.
- Where a raster is already under it, it may not lose a pixel.

## 3. The search

Each raster's pixel phase is fixed by the outline's coordinates, so a smaller
dot that is also MOVED can keep pixels a smaller dot in place would lose.
`instruments/tittle_search.py` works on the dot contour of the built i and j:
- It scales the dot about the center of its floor, so the white under it is
  kept.
- It lifts it dy units, and optionally nudges it dx units sideways.
- It computes each pixel's exact area coverage at the twelve rasters.
- At k 1 and dy 0 it reproduces `parts_check`'s count exactly for every cut.

The smallest dot each cut can take under the no-loss rule:

| cut | smallest k | at |
|---|---|---|
| Regular | **0.94** | lift 8 (0.95 at lift 7–8; 0.97 at lift 5–8). A sideways nudge of up to ±4 opens nothing below 0.94 |
| Italic | 0.99 | lift 1–2. With a nudge: 0.96 at lift 8, right 3 |
| Bold | **0.80** | lift 12. 0.86 needs no lift; 0.90 passes from −7 to +12 |
| Bold Italic | 0.94 | lift 1 |

**A uniform −10%, placed where it loses least:**
- Regular, lifted 5: the i and j at 12 pt go from 4 to 3.
- Italic, lowered 10: the j at 12 pt goes from 4 to 2.
- Bold Italic, lifted 6 and right 1: the j at 8 pt goes from 3 to 2.

## 4. Negative results

**The italic predictions do not survive a real build.** The italic dot is a
22-point polygon, and the builder's polygon is not a uniform scale of today's:
- Today's (`ALBO_ALD_DOT_SCALE` 1.26) is a leaning rhombus 95 units wide.
- At 1.197, 1.134 and 1.071 it is 78, 77 and 78 wide, with a vertical right
  edge.

So the search's italic placements missed. Built with them, the Italic lost a
pixel at 10 pt (i) and 14 pt (j), and the Bold Italic at 8 pt (j). The roman
dot is a true circle and lands within a unit of the search, and its counts
held on the real build.

The italic offset dials were therefore withdrawn rather than shipped
half-calibrated. The options leave the italics alone, except D3, which shows
what shrinking them costs.

**An i/j-only build (`--only ij`, 0.6 s) is not a stand-in:** its dot differs
from the full build's ((179, 551, 269, 636) against (176, 556, 271, 631)).

**The dot accents were left out on purpose.** `TITTLE` (round 369) still
scales the dieresis and dot-above, because they are the same optical object.
Shrinking them was not asked, and they sit at their own floors: today ï is 2
dark px at 10 pt and ä is 3.

## 5. The arms (all measured on full builds)

| arm | dials | Regular dot / xh | Bold | Italic | Bold Italic | rasters that lose |
|---|---|---|---|---|---|---|
| today | | 0.211 | 0.371 | 0.192 | 0.284 | |
| **D1** | `TITTLE_K` 0.94, `TITTLE_DY` 8, `TITTLE_K_700` 0.90 | 0.198 (−6%) | 0.335 (−10%) | unchanged | unchanged | **none** |
| **D2** | `TITTLE_K` 0.90, `TITTLE_DY` 5, `TITTLE_K_700` 0.90 | 0.190 (−10%) | 0.335 | unchanged | unchanged | Regular i 10 and 12 pt, j 12 pt: 4 → 3 |
| **D3** | D2, and `ALD_DOT_SCALE` 1.134, `ALD_DOT_SCALE_700` 0.90 | 0.190 | 0.335 | 0.170 (−11%) | 0.256 (−10%) | D2's, plus: Italic i 10 pt 2 → 1, 14 pt 4 → 2; j 10 pt 2 → 1, 12 and 14 pt 4 → 3; Bold Italic j 8 pt 3 → 1, i 8 pt 3 → 2 |

**Gates, each arm against round 466:**
- Moved: i, j, ĳ, ﬁ, ﬃ and U+E002 in the romans; in D3 also i, j and ĳ in the
  italics.
- POOR GATES: no delta. Touch 0 / 0 in every cut (the lifted roman dot meets
  nothing), no new hairs, contour census unchanged, approved letters
  unchanged, e mouth ok.

## 6. Reproduce

    cd tools/wedge_serif; source build_env.sh
    env "${ALBO_ROM_ENV[@]}" ALBO_TITTLE_K=0.94 ALBO_TITTLE_DY=8 PYTHON_GIL=0 python3 -m outlines.build OUT --style Regular
    env "${ALBO_BLD_ENV[@]}" ALBO_TITTLE_K_700=0.90 PYTHON_GIL=0 python3 -m outlines.build OUT --style Bold
    $VENV/bin/python instruments/parts_check.py ij OUT/Albo-Regular.ttf OUT/Albo-Bold.ttf
    $VENV/bin/python instruments/tittle_search.py <round 466>/Albo-Regular.ttf --k 0.90:1.00:0.01 --dy -12:12:1
    $VENV/bin/python instruments/tittle_proof.py PROOF today=... D1=... D2=... D3=...    (dirs with all four cuts)

Proof page: https://claude.ai/artifact/QMofFZaofDZPRQj2PaX6r8
