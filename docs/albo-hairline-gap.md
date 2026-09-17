# Albo's hairline gap

**Owner ruling, 2026-09-16:** *"record the hairline gap from Y into md file and
add it to P before middle connector."*

This file exists because the gap was not designed. It is what two strokes
happened to leave between them on one letter, the owner saw it, named it, and
made it a feature of the face. Without a written record the next person to
touch the Y would have closed it as a defect — it looks exactly like the
fracture class this font has shipped and fixed half a dozen times.

## What it is, measured

On the built italic Y, unsheared, at a cap of 674 design units. Horizontal
cuts through the join, reading the two ink runs and the white between them:

| y / cap | the two ink runs | white between |
|---|---|---|
| 0.37 | 86–169 | — one run; the strokes are merged |
| 0.38 | 83–163 · 170–179 | **7.2** |
| 0.39 | 79–156 · 164–186 | **7.9** |
| 0.40 | 76–151 · 158–194 | **7.7** |
| 0.41 | 72–144 · 152–203 | **8.1** |
| 0.42 | 69–139 · 147–210 | **7.8** |
| 0.43 | 65–134 · 148–217 | 14.7 — opening into the fork |

So: **about eight units wide, held within one unit over 0.04 of the cap, and
closed at the bottom.** A wedge, not a slot. At a 13 pt text size that is about
a fifth of a pixel — it is not a feature you can see in a paragraph, and that
is the point: it is what makes the join look cut rather than moulded when the
letter is large, and it costs nothing when the letter is small.

Where it comes from on the Y: the right arm's first traced point sits 46 units
right of the spine's centreline at the join, and the two strokes' half-widths
(about 34 and 22) overlap — so the strokes themselves merge. The gap is the
white left **under** the arm, between the arm's underside and the spine's right
edge, as the two come together. Nothing draws it.

## Why the P did not have it

Measured the same way on the P before round 161: 0.33 to 0.42 of the cap is
**one solid run** — the bowl's lower terminal and the stem simply merge, and
the counter only opens at 0.43. The P's two strokes come together going *down*
where the Y's come together going *up*, and the P's arrive nearly parallel, so
there was no wedge for them to leave.

## How it is cut on the P

`geom.ink`'s cutout, in `a_P` (`tools/wedge_serif/outlines/glyphs/aldine.py`):
a four-point wedge seated on the stem's right edge, widest where the counter
opens and narrowing downward, tapering to 0.74 of its width rather than to a
point — because the Y's gap is near-parallel over its run and a true triangle
reads as a nick rather than as a gap.

| dial | ships | what it is |
|---|---|---|
| `ALBO_ALD_P_GAP` | 1.0 | 0 turns it off; the letter is then byte-identical to round 160 |
| `ALBO_ALD_P_GAP_W` | 0.0172 | width, × cap |
| `ALBO_ALD_P_GAP_TOP` | 0.432 | where it meets the counter, × cap |
| `ALBO_ALD_P_GAP_BOT` | 0.384 | where it closes, × cap |
| `ALBO_ALD_P_GAP_X` | 0.0645 | the stem's right edge, × cap right of `x0` |

**`P_GAP_X` is measured from `x0`, the glyph's own drawing origin, and not from
the rendered outline.** The first cut of this took the 188 units the stem's
right edge reads on the built font and landed the gap 87 units too far right,
in the middle of the bowl — the built font's coordinates are post-sidebearing,
and the drawing's are not. Anything placed by a measurement off a TTF has to be
converted back through the bearing first.

## What it renders

| y / cap | the P's gap after round 161 |
|---|---|
| 0.38 | — closed |
| 0.39 | 6.3 |
| 0.40 | 7.0 |
| 0.41 | 7.6 |
| 0.42 | 8.3 |
| 0.43 | 26.3 — the counter |

Mean 7.3 against the Y's 7.7, and held within a unit over the same 0.04 of the
cap. The two letters now leave the same white where their strokes meet.

## Where else it could go, and deliberately has not

Every junction in the capitals where two strokes merge into one mass is a
candidate: the **B**'s two bowls against its stem, the **R**'s bowl arm, the
**K**'s leg where it buries in the stem, the **D**'s bowl foot. None of them
has been touched. Two reasons, both worth stating so this is a decision and
not an omission:

1. **It has only been ruled for two letters.** The Y's is native and the P's
   was asked for by name.
2. **A gap at every junction is not a hand-cut face, it is a mannerism.** The
   Y's reads as character because it is the only one; four more and it becomes
   the face's signature, which is a much larger decision than this one.

If the owner wants it spread, the mechanism generalises immediately — the
cutout is five numbers and `geom.ink` already takes a list.
