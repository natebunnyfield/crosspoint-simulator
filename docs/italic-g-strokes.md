# The calligraphic strokes of Coelacanth's italic g — measured, 2026-09-14

Owner: *"show me that understand the underlying calligraphic brush strokes of
g based on coelacanth's g."*

Three cuts of Albo's italic g had come out wrong in the same way — a loop
like wire — and each fix had been a guess at a width. So the letter was
measured instead. Instrument: the skeleton and its thickness, below;
`scratchpad/gan/` holds the arrays.

## Method

Coelacanth Italic's `g` rasterised at a 900 px em, a chamfer distance
transform over the ink, the ridge of that transform taken as the stroke's
centerline (2,303 samples), the local thickness read as twice the distance,
and the local direction from a PCA of the neighbouring ridge points. Every
figure below is that data, not an impression.

## What it says

**The pen's edge lies at 22 degrees.** Width against the direction the stroke
runs (0 = a horizontal run, 90 = vertical), in units per 1000 em:

| direction | median width |
|---|---|
| 0–15 | 53 |
| **15–30** | **32  ← thinnest** |
| 30–45 | 32 |
| 45–60 | 39 |
| 60–75 | 56 |
| 75–90 | 69 |
| 90–105 | 71 |
| **105–120** | **73  ← thickest** |
| 120–135 | 67 |
| 135–150 | 65 |
| 150–165 | 73 |
| 165–180 | 69 |

Thinnest and thickest sit 90 degrees apart, which is what a broad nib does:
a stroke running ALONG the edge shows the pen's thin dimension, a stroke
across it shows the full width. So the pen is held with its edge at about
**22 degrees**, and the ratio of the medians is **2.3:1**.

**Albo's own pen is at 26 degrees.** Within four degrees of Coelacanth's. So
the widths of this letter never needed declaring — the pen already gives
them. What was wrong was the geometry.

## The three findings that decide the letter

1. **The loop is a big ROUND tilted oval, not a flat sweep.** On the stroke
   map its left side and its bottom-left are thick and its right side thin,
   because those runs go across the pen and along it respectively. **A flat
   loop runs horizontal the whole way round, and a horizontal run is the
   pen's thin** — which is exactly why three cuts of Albo's loop came out as
   wire no matter what floor or width table they were given. The failure was
   never the width; it was that the stroke never travelled in the thick
   direction.
2. **The bowl is the o**, closed, with the same thick-left thin-right
   modulation.
3. **The neck is a hairline and the ear is one short thick stroke** off the
   bowl's shoulder — the two shortest strokes in the letter and the only two
   that are not part of a ring.

## What Albo's g is now

`o_ring(c, O_RX)` for the bowl — the o's own call, so the two cannot drift —
a **ring** for the loop rather than a stroke, a hairline neck, and an ear.
Letting the loop be a ring is the whole fix: a ring has ascending and
descending runs by construction, so the pen modulates it without being told
to. `outlines/glyphs/italic.py`, `g_g_it`.

## The rule this leaves behind

**When a stroke comes out the wrong weight, check its DIRECTION before its
width.** In a pen model the width is a function of where the stroke is
going. Three rounds were spent raising floors and declaring width tables on a
stroke whose only real fault was that it ran the wrong way.
