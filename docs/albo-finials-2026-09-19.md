# Albo: the round finials changed out for the c's top end (round 275)

Date 2026-09-19. Surveyed at commit 514ae30 (round 273); built and gated on
the working tree that became round 275. Every number below is measured on
the built outline or the built font, not estimated, unless it says so.

Owner 2026-09-19, verbatim: *"change out round finials (like c top serif)"*,
and after round 273's ladder of five ends for the c's top: *"a works but my
ask was about the round finials"*. So the c's top AS DRAWN is the model, and
the ball and teardrop ends elsewhere in the roman become it. All four roman
weights move, the shipped 400 included. The italic is not touched (proved
below).

Proofs: `tools/wedge_serif/shape/weights275/index.html` (per-glyph
before/after at 0.5 px/unit for the 400 and the 700; runs at 13 px x8 and
40 px x2 for all four weights; PNG at native pixels, NEAREST integer
magnification only).

## 1. The model construction

`rounds.g_c`, option 'a', as it has been since R18 despurred it: the stroke
SWELLS to 1.10 of the pen over its first 13% (`widths([(0.0, 1.10), (0.13,
1.0), ...])`) and ends on a face sheared 28 degrees toward the vertical
(`cut0 = -28 deg` into `primitives.stroke`), no lip. Measured on the built
c: end width 60.8 at the 400 (stem 66.9) and 103.4 at the 700 (stem 116),
face length 68.9 / 117.1.

It is now three primitives in `outlines/primitives.py`, the ONE definition
every converted terminal composes and the c itself draws through:

- `FINIAL_SWELL = 1.10`, `FINIAL_SPAN = 0.13`, `FINIAL_CUT_DEG = 28.0`.
- `finial_widths(base, at_start, profile=None, floor=0.0)` -- the swell on
  one end of a width function, with the same smoothstep `widths()` uses, so
  the c composes to the same numbers it declared before. `floor` is the least
  width the swelled end may have: a terminal on a hairline takes the swell
  that lands it on the floor instead of 1.10 of nearly nothing.
- `finial_cut(pts, at_start)` -- the signed cut, in `stroke()`'s convention,
  that shears that end's face 28 degrees toward the vertical. The sign is
  decided per end from the end tangent (`stroke()` moves the left-of-travel
  corner forward and the right one back at a start, the reverse at an end);
  on the c's top it resolves to the -28 the c always carried.
- `rounds.c_top_width()` -- the c's own end width from the c's own geometry
  (1.10 x the bowl pen at the c's start tangent: 60.8 / 103.4), the floor
  the hairline finials are held to.

The c is BYTE-IDENTICAL through the helper: `diffglyphs.py` against the
round-273 (400) and round-272d (700/900/200) builds does not list `c` at any
weight.

What "28 degrees toward the vertical" does on a stroke that does not head
where the c's does: the r's arm ends heading -21 degrees at the 700, so its face lands
at 97 degrees from horizontal (near vertical, lower corner forward); the f's
hook ends heading -57 and its face lands at 61 (the c's own 68, flipped);
the a's hood ends heading -108 (down-left) and its face lands at 134 with the
INNER corner forward -- the same relation the c's top has (inner corner
forward, outer corner cut back), which on the a is the opposite lean to the
teardrop's point it replaces. On every converted end the corner that comes
forward is the concave side's, as on the c.

## 2. The inventory, decided by rendering

Rendered at 1.5 px/unit in 130-unit crops around every stroke end, at the
400 and the 700, before and after (`scratchpad/R275/base*.png`,
`new*.png`, `deferred.png`). "was" is the construction read from the code
and confirmed on the render; widths are the stroke's width at the end
(design units, 400 / 700); "face" is `stroke()`'s signed cut in degrees.

| terminal | was | decision | end width before | end width after | face before -> after |
|---|---|---|---|---|---|
| c top | swell 1.10 / 13%, -28 face | the model; not changed | 60.8 / 103.4 | 60.8 / 103.4 | -28 -> -28 |
| f hook end (`stems.f_ink`, flush) | flare 1.2 over the last 30% into the 20-degree cut; a teardrop | CONVERTED | 79.9 / 138.6 | 73.3 / 127.1 | +20 -> +28 |
| r arm end (`arches.g_r`, R31 option c) | flare 1.15 over the last 45% into the cut; a knob | CONVERTED | 66.8 / 106.3 | 63.9 / 101.6 | +20 -> +28 |
| y tail end (`diagonals.g_y`) | flare 1.3 over the last 30% into the cut; a teardrop | CONVERTED, floored | 61.1 / 106.0 | 60.8 / 103.4 | +20 -> +28 |
| a hood end (`stems.g_a`, hood and underside) | swell 1.12 over the last 25% into the cut, "a teardrop not a flag" | CONVERTED | 66.4 / 97.3 | 65.2 / 95.6 | +20 -> -28 |
| J hook end (`caps_straight.g_J`) | flare 1.3 over the last 35% into the cut; a teardrop | CONVERTED | 80.8 / 143.9 | 68.3 / 121.2 | +20 -> +28 |
| J top | the I's wedge | a wedge, stays | -- | -- | -- |
| 3 top (`figures`, waist 'e' ships) | swell 1.1 over the first 10% into the cut | CONVERTED (same end width; span 10 -> 13%, face) | 60.7 / 105.2 | 60.7 / 105.2 | +20 -> +28 |
| 3 bottom | flare 1.25 over the last 15% into the cut | CONVERTED, floor set (did not bind) | 83.1 / 144.3 | 73.1 / 127.0 | +20 -> +28 |
| 5 bowl end (`figures.g_five`) | flare 1.25 over the last 15% into the cut | CONVERTED, floor set (did not bind) | 82.8 / 144.0 | 72.9 / 126.7 | +20 -> +28 |
| 5 top | a bar with a hanging wedge | not a finial, stays | -- | -- | -- |
| j tail end (`stems.g_j`) | thins to 0.10 S -- a POINT (6.7 / 11.6 wide) | not a ball, stays | 6.7 / 11.6 | -- | -- |
| g ear end (`stems.g_g`) | a straight stroke rising 8 deg on the cut; its 1.05 flare never shows because the end sits ON its 0.72 S floor (48.2 = 0.72 x 66.9; 83.5 = 0.72 x 116) | a bar on a cut, stays | 48.2 / 83.5 | -- | -- |
| ? hook start (`marks._q8`, the shipped variant) | 0.7 of the profile at a 0.78 S floor, `cut0 = CUT`, no swell; `_q7`'s "curled teardrop" is not the shipped variant | a plain cut, stays | -- | -- | -- |
| 2 top (`figures`, option 'b' ships) | `start_w` 1.0 -- round 249 removed its swell ("without the bulge"); a blunt 20-degree cut on a stroke heading down | a blunt cut, stays; re-adding a swell would reverse round 249 | -- | -- | -- |
| 6 top (option 'i' ships) | thins to 0.30 into the cut (round 250, "blunt and short"); option 'e' is the ball and does not ship | a thin cut, stays | -- | -- | -- |
| 9 tail (option 'u' ships) | a square face with the 0.35 x 0.70 wedge (round 257); option 'k' is the ball and does not ship | a wedge, stays | -- | -- | -- |
| s, C, G, S, &, t | flared cuts and beaks | per the ask, stay | -- | -- | -- |
| every dot (i j . , : ; ! ? and the marks) | `dot()` | not a finial, stays | -- | -- | -- |

The swell reference and the floor, per terminal. The c's rule is 1.10 of
the pen at that point. Measured against the c's own end (60.8 / 103.4):

- f: the hook ends on the pen's thick (66.6 / 115.5), 1.10 of it is 73.3 /
  127.1 -- above the c's, no floor.
- r: the arm's floor is 0.60 S (R31 'c'); 1.10 of the arm's end (58.1 /
  92.4) is 63.9 / 101.6 -- within 2% of the c's, no floor.
- y: the tail runs out heading LEFT, on the pen's THIN (47.0 / 81.5); 1.10 of
  that is 51.7 / 89.7, 15% and 13% under the c's end. It takes the floor, so
  its swell is 1.29 / 1.27 of the pen -- the ball's weight kept (61.1 -> 60.8
  at the 400), its shape and its face changed.
- a: 1.10 of the hood's end is 65.2 / 95.6. The 700's 95.6 is 8% under the
  c's end, and no floor is set: round 272 thinned the 700 and 900 hoods on
  purpose ("roman 700 and 900 'a' is too thick") and a floor would hand back
  a third of that.
- J: 1.10 of the blend's end is 68.3 / 121.2, above the c's, no floor.
- 3 bottom and 5 end: floored to the c's end as a guard; both head up-left on
  the pen's thick and 1.10 of it (73.1 / 127.0 and 72.9 / 126.7) is above
  the floor, so the floor does not bind at either weight.

## 3. Position and reach

The centerline end of every converted stroke is where it was; only the end's
shape changes. But the 28-degree face moves the two corners further than the
20-degree cut did (0.27 of the width against 0.18), so the INK's extreme
moves by a few units where a corner was the glyph's edge:

- The f's hook: the forward (inner, lower) corner would reach 0.074 of the
  pen further down-right than round 42's -- 4.9 units at the 400, 8.6 at the
  700 -- into the f-capital pairs that already sit at the touch floor.
  Measured on the first build: `fW` at the 200 went from +0.0019 em to
  -0.0024 (TOUCHING) and `fT` at the 700 fell under the floor (0.0086). The
  hook's end now RETREATS along its own tangent by exactly that amount
  (`F_FINIAL_RETREAT` in `f_ink`, derived from the two cuts and the two
  swells, not typed), so the forward corner lands where it always has: `fW`
  at the 200 reads 0.0019 again, `fT` at the 700 reads 0.0172. The hook is
  0.074 of a pen shorter on its centerline; the f's end width is unchanged
  (73.3 / 127.0) and its right ink is at 377 / 421 against 383 / 431 before.
- Elsewhere the OUTER corner recedes, and where it was the band's extreme
  the fitting rule (`build.fit`, ink measured in the x-height or cap band,
  the J on its full extent) moved the advance with it, at 400 / 700 / 900 /
  200: J 439->435 / 443->444 / 448->446 / 418->414; r 345->344 / 411->410 /
  -- / 314->311; a -- / 519->510 / 558->545 / --; 3 396->393 / 437->433 /
  459->450 / 379->378; 5 436->433 / 469->464 / 487->484 / 420->418; their
  composites follow. NOT pinned, on purpose: the rule measures the ink's
  extreme, and the teardrop's point no longer occupies that white -- at the
  700 the a's hood end is now flush with its bowl's left edge (both at x 21)
  where the point stood 9 units past it. Pinning the advance would add 9-13
  units of white beside the 700 / 900 a where there is no ink. The f and the
  y do not move an advance: their ends lie outside the band. If the owner
  wants the old advances back, it is a per-glyph delta in `BEARING_ADJ`, and
  it is weight-dependent, which is why it is not done here.

## 4. What was tried and did not hold

- The finial with no floor on the y: 51.7 / 89.7 wide, 15% under the c's end
  -- a thin cut on a hairline, not the c's terminal. The floor was added and
  is `c_top_width()` rather than a number, so it moves with the c.
- The f's hook with the finial and no retreat: two touch pairs grew (above).
  A kern was not the answer -- the pairs were already recorded under the
  floor and GPOS was to stay at 0 changed -- and clamping the shear would
  have made the f's face a different construction from the c's.
- Estimating the J's "before" from the probe's log during `solve_widths()`:
  the solver draws the J with intermediate width multipliers, and the number
  read there (84.8) was not the built J's (80.8). Every "before" in this doc
  is from a HEAD copy of the package (`git archive HEAD`) probed with the
  final widths.
- `echo ====` in zsh: `=` at the start of a word is command expansion. Not a
  finding about the face, but it ate one probe run.

## 5. Gates, verbatim (built fonts, this round)

```
== 400
β  U+03B2
    CRACK   hole mean width 4.17 < 12.0 (area 108, perim 52)
122 glyphs swept, 1 with findings
  3 pair(s) TOUCHING, 5 below the 0.012 em floor, 14 exempt.
-- Albo-Regular: 1 dent(s) in 1 glyph(s)
   &:737/9.1
== 700
122 glyphs swept, 0 with findings
  4 pair(s) TOUCHING, 6 below the 0.012 em floor, 14 exempt.
-- Albo-Bold: 0 dent(s) in 0 glyph(s)
== 900
122 glyphs swept, 0 with findings
  5 pair(s) TOUCHING, 7 below the 0.012 em floor, 14 exempt.
-- Albo-Black: 0 dent(s) in 0 glyph(s)
== 200
β  U+03B2
    CRACK   hole mean width 7.86 < 12.0 (area 420, perim 107)
122 glyphs swept, 1 with findings
  2 pair(s) TOUCHING, 17 below the 0.012 em floor, 14 exempt.
-- Albo-ExtraLight: 1 dent(s) in 1 glyph(s)
   &:925/12.1
```

Against the baselines: glitch 0 at 700 / 900 and the ruled β alone at 400 /
200; touch 400 3/5/14 (was 3/5/14), 700 4/6/14 (was 4/7/14 -- one pair
opened), 900 5/7/14 (was 5/7/14), 200 2/17/14 (was 2/17/14); dents 0 at
700 / 900, and the 400 / 200 ampersand dent (`&:737/9.1`, `&:925/12.1`) is
byte-for-byte the baseline's -- the & was not touched.

## 6. Glyphs moved per weight

`diffglyphs.py` against `R273b/r400` (400) and `R272d/r700`, `r900`, `r200`:

```
w400 glyphs differing: 23 ['J', 'a', 'f', 'r', 'y', 'three', 'five', 'ordfeminine', 'uni00B3', 'threequarters', 'ae', 'IJ', 'uni2075', 'uni2083', 'uni2085', 'onethird', 'twothirds', 'threeeighths', 'fiveeighths', 'Jcircumflex'] | GPOS pairs changed: 0 []
w700 glyphs differing: 32 ['J', 'a', 'f', 'r', 'y', 'three', 'five', 'ordfeminine', 'uni00B3', 'threequarters', 'ae', 'IJ', 'uni2075', 'uni2083', 'uni2085', 'onethird', 'twothirds', 'threeeighths', 'fiveeighths', 'agrave'] | GPOS pairs changed: 0 []
w900 glyphs differing: 31 ['J', 'a', 'f', 'r', 'y', 'three', 'five', 'ordfeminine', 'uni00B3', 'threequarters', 'ae', 'IJ', 'uni2075', 'uni2083', 'uni2085', 'onethird', 'twothirds', 'threeeighths', 'fiveeighths', 'agrave'] | GPOS pairs changed: 0 []
w200 glyphs differing: 23 ['J', 'a', 'f', 'r', 'y', 'three', 'five', 'ordfeminine', 'uni00B3', 'threequarters', 'ae', 'IJ', 'uni2075', 'uni2083', 'uni2085', 'onethird', 'twothirds', 'threeeighths', 'fiveeighths', 'Jcircumflex'] | GPOS pairs changed: 0 []
```

The full 400 list: IJ J Jcircumflex a ae f five fiveeighths onethird
ordfeminine r racute rcaron three threeeighths threequarters twothirds
uni00B3 uni0157 uni2075 uni2083 uni2085 y. The 700 and 900 add the nine
accented a's (their advance moved with the a's). Every entry is a converted
glyph or a composite of one; nothing else moved.

## 7. What was checked and found CLEAN

- The c: not in any weight's diff list -- byte-identical through the helper,
  advances included.
- The italic: `Albo-Italic.ttf` built (ALBO_ITALIC=aldine, slant 13) from a
  HEAD copy and from HEAD plus this round's seven files: `italic glyphs
  differing: 0 [] | GPOS pairs changed: 0 []`. The aldine italic registers
  its own c a r f j g y J; the figures 2 3 5 are shared and every figure
  change is behind `not pen.ITALIC`.
- GPOS: 0 pairs changed at every weight.
- The 2: its top is a blunt cut with no swell (round 249's ruling) and stays.
- The j, the g's ear, the ?, the 6, the 9, the s C G S & t, every dot: read
  from the code and confirmed on the render, none is a ball (table above).
- The f-ligatures: `f_ink` with `hook_profile` / `hook_cut=False` (the
  ligatures' path) is untouched; `ALBO_LIGS` is off in every build anyway.
- The ampersand does not call `f_ink` (grep); its dent is the baseline's.
- The a's option c / d wedge seat (`A_TERM_WEDGE`, not shipped) now reads the
  finial's cut so it would still seat on the corner the cut leaves.
- `git status`: exactly the seven files below are modified; `aldine.py` is
  clean.

## 8. Files

`tools/wedge_serif/outlines/primitives.py` (the three primitives),
`outlines/glyphs/rounds.py` (the c through the helper; `c_top_width`),
`outlines/glyphs/stems.py` (f, a), `outlines/glyphs/arches.py` (r),
`outlines/glyphs/diagonals.py` (y), `outlines/glyphs/caps_straight.py` (J),
`outlines/glyphs/figures.py` (3, 5); proofs in
`tools/wedge_serif/shape/weights275/`.

## 9. Left for a later round

The italic's balls were not in this ask and are not touched. Named from
the code paths, NOT rendered this round (another agent is in `aldine.py`):
the aldine italic's own c, a, r, f, j, g, y and J terminals in
`outlines/glyphs/aldine.py`, and the shared figures' ends -- the 3's two
ends, the 5's bowl end, the 2's top -- which keep the roman's OLD flare into
the 20-degree cut under their `pen.ITALIC` branches (`figures.py`; the
italic 3 / 5 tails become run-outs when `THREE_TAIL_END` / `FIVE_TAIL_END`
are set). Which of those are balls and which are run-outs is a render
question for that round; this round's inventory method (the `stroke()`
patch in `scratchpad/R275/probe.py`) applies as is.
