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
a parallel-sided cut seated on the stem's right edge, running from the counter
at 0.432 down to 0.305 — below the bowl's own lowest ink at 0.33 — so it
**leaves the letter cleanly at both ends** instead of tapering to a point
inside it.

**Round 161 cut it as a wedge and round 162 corrected that**, on the owner's
ruling: *"make it a clean line through for P hairline."* The first cut copied
the Y's SHAPE, and that was the wrong half to copy. On the Y the wedge closes
because the two strokes genuinely meet there; on the P the bowl's terminal
**lies against** the stem for its whole last stretch, so a gap that closes
reads as a nick taken out of a join rather than as two strokes side by side.
What transfers between the two letters is the gap's WIDTH, not its outline.

| dial | ships | what it is |
|---|---|---|
| `ALBO_ALD_P_GAP` | 1.0 | 0 turns it off; the letter is then byte-identical to round 160 |
| `ALBO_ALD_P_GAP_W` | 0.0135 | width, × cap |
| `ALBO_ALD_P_GAP_TOP` | 0.432 | where it meets the counter, × cap |
| `ALBO_ALD_P_GAP_BOT` | 0.305 | where it leaves the ink, × cap |
| `ALBO_ALD_P_GAP_X` | 0.0645 | the stem's right edge, × cap right of `x0` |

**`P_GAP_X` is measured from `x0`, the glyph's own drawing origin, and not from
the rendered outline.** The first cut of this took the 188 units the stem's
right edge reads on the built font and landed the gap 87 units too far right,
in the middle of the bowl — the built font's coordinates are post-sidebearing,
and the drawing's are not. Anything placed by a measurement off a TTF has to be
converted back through the bearing first.

## What it renders

| y / cap | the P's gap after round 162 |
|---|---|
| 0.32 | — below the bowl's ink; stem only |
| 0.33 | 7.0 |
| 0.34–0.38 | 7.0 · 6.9 · 6.9 · 6.9 · 6.9 |
| 0.39–0.42 | 6.9 · 6.8 · 6.8 · 6.8 |
| 0.43 | 26.3 — the counter |

Constant to within 0.2 of a unit over 0.10 of the cap, against the Y's 7.7 over
0.04. The two letters leave nearly the same white; the P's runs three times as
far, because that is how far its two strokes lie against each other.

`P_GAP_W` fell 0.0172 → 0.0135 when the wedge became a parallel cut, and that
is arithmetic rather than a second decision: a tapered cut only reaches its
declared width at one end, so the same number rendered 7.3 as a wedge and 9.8
as a line.

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

---

## 2026-09-21 — the ITALIC CAPITAL Y gets one, and it is the widest in the face

Owner, across two rounds: *"yes to 1.1 and increase hairline"*, then from five
widths, *".016 wins"*.

Until now this page described the ROMAN Y and the P. The italic capital Y had
no gap: its spine was heavy enough (thick 93.8 units, the heaviest diagonal in
either style) that the arm merged solid into it. Correcting that weight to 1.1
— which put the thick at 73.8, inside the family's 66–75 — **opened a gap by
itself**, 6.1 units, and he then asked for it wider.

| | units of white at the join |
|---|---|
| italic Y before round 354 | none — one contour |
| after the spine correction alone | 6.1 |
| the roman Y's own, for scale | 7.2–7.9 |
| **shipped** | **14.3** |

So the italic capital's gap is deliberately about twice the roman's. That is
his reading of *"increase"*, made on the rendered letter at four sizes.

| dial | ships | what it is |
|---|---|---|
| `ALBO_ALD_Y_GAP` | 0.016 | the arm's ROOT displaced from the spine, × cap; tapers to nothing by the fourth point, so the arm's curve, reach and terminal do not move. 0 is bit-exact inert |
| `ALBO_ALD_Y_SPINE_INK` | 1.10 | the spine's weight, × `Y_INK`. Below 1.18 the glyph is two contours — which IS the gap |

**`ALBO_ALD_Y_ARM_INK` IS NOT THE LEVER and was tried first.** Thinning the arm
moves both of its edges, so 1.38 → 1.08 walks the gap 6.1 → 6.3 → 5.7 → 5.8:
non-monotone, inside the raster's own noise, and no use. The gap is where the
arm's root PASSES the spine, not how wide the arm is. Same shape of mistake as
the three spacing measures in `albo-spacing-method.md`: a lever that plausibly
should work, measured, and rejected.

**And `ladder.py` reported the real dial FLAT** before it was fixed — it built
`--style Italic` with no environment, which is not the aldine italic, so no
aldine dial could move anything. It now carries the style's own environment.
A false FLAT is worse than no tool: the entire output of that file is
"stop laddering that."
