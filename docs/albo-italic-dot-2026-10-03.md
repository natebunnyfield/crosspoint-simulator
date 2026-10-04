# Albo: can the italic i/j dot gain pixels by moving? (2026-10-03)

The owner was asked "2 of 4":
- The italic i/j dot is drawn with only 2 dark pixels at 10 and 12 pt on the
  X3, under the 4-pixel floor the font checks use, even after round 440
  enlarged it.
- The reader always draws that dot the same way at each size, so moving it a
  few units, without making it bigger, might let it land on more pixels.

He answered *"Try it."*

**Status: OPTIONS. Nothing shipped.** The dials are `ALBO_ALD_DOT_DY` /
`ALBO_ALD_DOT_DX` (and `_700`) in `outlines/glyphs/aldine.py`: the dot's lift
and rightward move, in whole units of the SHEARED glyph. Defaults of 0 are
round 475 byte for byte (control build).

## Why a search on the built dot is exact here

Round 467's italic predictions failed on real builds because SCALING the dot
re-samples its 22-point polygon. A whole-unit TRANSLATION does not:
- The superellipse is generated about its center, and the shear is undone in
  the dial.
- The TTF's integer rounding of `p + d` is `round(p) + d`.

So `tittle_search`'s exact-coverage count on the built contour is what the
build renders. Confirmed below on a real build.

## The search (dy −16..+16, dx −8..+8; i and j; 8–18 pt at 1x and 2x)

- **Strict rule** (no raster may lose a single pixel): **nothing** passes but
  (0, 0). Every move that gains at 10–12 pt loses a pixel somewhere else.
- **Floor rule** (no raster may fall under 4, or lose a pixel if already
  under 4):
  - The best is dy +8, dx +1 (M1). Neighbors at +9 do as well, and +2 to +3
    gain less.
  - **No placement gains anything at 10 pt.** The dot is about 1.7 px across
    there, too small for any position to cover 4 pixels.
- **Bold Italic:** the best moves gain only at 8 pt (3 → 4). It was already at
  or above the floor from 10 pt, so it is left alone.

## M1 on a real build (`instruments/parts_check.py`, Italic)

| | 8 pt | 10 pt | 12 pt | 14 pt | 16 pt |
|---|---|---|---|---|---|
| i, today | 1 | 2 | 2 | 4 | 6 |
| i, M1 | **2** | 2 | **3** | 5 | 6 |
| j, today | 1 | 2 | 3 | 4 | 6 |
| j, M1 | **2** | 2 | **4** | 4 | 5 |

- The 2x tier stays at 5 or more everywhere. Some rasters there lose a pixel
  or two above the floor (i at 10 pt @2x 9 → 7).
- The dot sits 8 units higher: its floor's clearance over the x-line goes from
  0.298 to about 0.317 x-height.
- **Moved:** i, j and ĳ in the Italic.

**To reach 4 pixels at 10 pt the dot would have to grow.** Round 440 sized
it, and round 467 deliberately left the italic dots alone.

Proof page: https://claude.ai/artifact/SiEZ5YGDXtmsM1yFSr27ja
