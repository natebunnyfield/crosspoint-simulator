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

## Round 276 — the italic's finials

Date 2026-09-19. HEAD `01fe91f` (round 277) surveyed; built and gated on the
working tree that became round 276. Owner, on the italic cent page: *"that
italic has round finials that needs to replaced along with others."* Both
italic weights move, the shipped Italic 400 included; the Regular is proved
byte-identical below. Proofs: `tools/wedge_serif/shape/weights276/index.html`
(per glyph, before/after at 0.5 px/unit, the 400 and the 700 side by side;
runs at 13 px x8 and 40 px x2 for both weights; PNG at native pixels,
NEAREST only). Every number is measured on the built outline (the design-mode
probe, `scratchpad/R276/probe_it.py`, round 275's instrument with the
aldine module patched in and `PR.dot` logged) or on the built font.

### 1. The same construction, and one number the italic had to supply

The ends compose round 275's three primitives unchanged — `finial_widths`,
`finial_cut`, the swell to 1.10 over 13% into the face sheared 28 degrees
toward the vertical, no lip. What the italic adds is the FLOOR, because its
contrast is per letter and nearly every converted end sits on a hairline:
the c's top is 33.2 units wide at the 400, the r's arm 36.8, the y's tail
26.5, and 1.10 of any of those is a thin cut, not the c's terminal.

The floor is **the italic c's own top end** — the width its ball had, the
ring's width at the path's start x C_CAP0_R, the 2026-09-17 serif scale:
**65.6 at the 400, 90.6 at the 700** (`aldine.fin_floor`). Not
`rounds.c_top_width()`, and that is a measured decision, not a preference:
under the italic's pen that function reads 65.3 at the 400 (0.5% from the
italic's own) but **111.5 at the 700**, because it scales with S (x1.73 from
the 400) where every stroke in the aldine module scales with `ALD_WF_UP`
(x1.38). Built with it, the BoldItalic's terminals were a face 96% of the
stem wide on 43-unit hairlines, the c's top corner stood 20 units above the
letter's own crown (471 against the ball's 450), and the y's tail went 41
units deeper. The italic's own number keeps the c's top at the ball's weight
at both weights and lands every other converted end on it.

### 2. The inventory, decided by rendering

3 px/unit crops around every `stroke()` end and every `PR.dot`, at the 400
and the 700, before and after (`scratchpad/R276/base400.png`, `base700.png`,
`base400b.png` for the capitals, marks and figures, `base400c.png` for the
rest of the lowercase and the aldine capitals; `final400.png`,
`final700.png`). "was" is the construction read from the code and confirmed
on the render; widths are the terminal's ink at the end, design units,
400 / 700; the face is `stroke()`'s signed cut in degrees. The 400's
"before" widths and every "after" are measured; the 700's "before" for the
table-drawn lobes and the `d_ball` ovals (f j k x v w y, the r's oval, the
J's flare) are the 400's x ALD_WF_UP (1.381), the module's own scaling, not
re-measured -- the discs of the c and the s at the 700 are measured.

| terminal | was | decision | end width before | after | face before -> after |
|---|---|---|---|---|---|
| c top (`a_c`) | `cs_round_end` + `PR.dot`, the disc 1.15 x the end's half-width, on a 33.2 / 43.6 stroke | CONVERTED, floored (the floor IS this width); trimmed as the cap trimmed it | 65.6 / 90.6 | 65.6 / 90.6 | round -> -28 |
| c bottom | a semicircular cap of the stroke's width | CONVERTED, floored; trimmed as before | 37.6 / 52.2 | 65.6 / 90.6 | round -> -28 |
| s head (`a_s`) | a semicircular cap | CONVERTED, floored; untrimmed | 41.5 / 59.2 | 65.6 / 90.6 | round -> -28 |
| s foot | a disc on a path widened 1.5x over its last 14% (`S_FOOT`, the 2026-09-17 foot) | CONVERTED, floored; the 1.5x widening goes with the disc it grew (kept, the foot flares 1.65x into the face — a flared cut, not the c's 1.10); trimmed back by the face's throw, (w/2) tan 28 | 84.6 / 67.2 | 65.6 / 90.6 | round -> -28 |
| r arm (`a_r`) | a separate 84 x 106 oval (x ALD_WF_UP: 116 x 146 at the 700) on an arm 36.8 / 59.4 wide at its end | CONVERTED, floored (1.10 x 36.8 = 40.5); the arm carried `fin_reach` past the ball's old centre so the rightmost ink holds: 243 -> 244 / 308 -> 309 | 84 / 116 | 65.6 / 90.6 | oval -> -28 |
| f hook (`a_f`) | a lobe in the width table (32 -> 54 -> 60 -> 44, x F_TW), closing on a flat face | CONVERTED, floored (1.10 x 49.3 = 54.2); the table now carries the hook at its own 44 | 67.2 (tip 35.8) / 92.8 | 65.6 / 90.6 | flat -> +28 |
| f tail | a lobe (34 -> 46 -> 50 -> 22) on a flat face | CONVERTED, floored; the hairline eases 34 -> 42 | 56.0 (tip 24.6) / 77.3 | 65.6 / 90.6 | flat -> +28 |
| j tail (`a_j`) | a lobe (36 -> 44 -> 48 -> 20) on a flat face | CONVERTED, floored; 36 -> 42 | 52.8 (tip 22.0) / 72.9 | 65.6 / 90.6 | flat -> +28 |
| j head | the pen cut under the wedge head | not a finial, stays | 46.2 / 63.8 | -- | +20 |
| v rise (`a_v`) | `d_ball`, a 70 x 64 oval on the pen's angle set back over a 53.8 flat end | CONVERTED, floored (1.10 x 53.8 = 59.2); centerline end unmoved — the ball sat back over the stroke and the stroke's own face reached as far | 70 / 97 | 65.6 / 90.6 | oval -> +28 |
| w rise (`a_w`) | the same, over 52.8 | CONVERTED, floored | 70 / 97 | 65.6 / 90.6 | oval -> +28 |
| w apex ends | buried in the apex | stay | -- | -- | -- |
| x top right (`a_x`) | a swell in the table (27 -> 40 -> 64 -> 54) on a flat face — "the ball on the thin's top" drawn as width | CONVERTED, floored; 27 -> 34 -> 40 | 64.0 (tip 54.0) / 88.3 | 65.6 / 90.6 | flat -> +28 |
| x hooks (under the thin's start, off the thick's foot) | curls narrowing to a tip (30, 38) below their bend | not balls, stay | 30.0 / 38.0 | -- | flat |
| y rise (`a_y`) | `d_ball` over a 49.0 end | CONVERTED, floored | 70 / 97 | 65.6 / 90.6 | oval -> +28 |
| y tail | the round-135 DROP: `d_ball` at squash 1.55 (84 x 54) with the hairline swelling 1.4x then 2.1x into it | CONVERTED, floored: the tail is the reference's constant 26.5 hairline to its end and the floor is a 2.5x swell over the last 13%; the end carried `fin_reach` along the last segment so the swash keeps Y_TAIL_X: leftmost 19 -> 20 / 32 -> 34 | 84 / 116 | 65.6 / 90.6 | oval -> -28 |
| k arm (`a_k`) | a swell (40 -> 48 -> 64 -> 52) on a flat face, "ball 81 wide at .90" drawn as width | CONVERTED, floored; 40 -> 44 -> 48 | 69.1 (tip 56.2) / 95.4 | 65.6 / 90.6 | flat -> -28 |
| k leg | a flick tapering to 23.8 | not a ball, stays | 23.8 / 32.8 | -- | flat |
| J hook (`caps_straight.g_J`, the `pen.ITALIC` branch) | the flare 1.3 over the last 35% into the 20-degree cut — round 275's roman teardrop, left in the italic for one round | CONVERTED: the branch removed, the italic takes the roman's finial (no floor, the J's own) | 86.7 / 150.3 | 73.4 / 127.2 | +20 -> +28 |
| 2 top (`figures.g_two`, italic option a) | the profile's 1.1 swell over the first 15% into the cut, the 3's top's construction | CONVERTED (same end width; span 15 -> 13%, the face); gated `pen.ITALIC`, the roman's option b keeps round 249's plain cut | 75.0 / 128.6 | 75.0 / 128.6 | +20 -> -28 |
| 3 top (`g_three`, the `pen.ITALIC` branch) | the 1.1 swell over 10% into the cut | CONVERTED: the branch merged into the roman's finial line (same end width; span, face) | 60.7 / 105.2 | 60.7 / 105.2 | +20 -> +28 |
| 3 bottom, 5 bowl end | run-outs to 0.45 of the pen (`THREE_TAIL_END`, `FIVE_TAIL_END`) | not balls, stay | 29.9 / 29.8 | -- | flat |
| 5 top | a bar with a hanging wedge | not a finial, stays | -- | -- | -- |
| cent | the c with the bar | follows the c | as the c | as the c | -- |
| e terminal (`a_e`) | the blunt 0.40 S end of 2026-09-16 ("blunt instead of angular") | not a ball, stays | 26.8 / 46.4 | -- | flat |
| g ear | a bar flaring then narrowing into the 20-degree cut | a bar on a cut, stays | 55.4 / 76.5 | -- | +20 |
| t top, t exit, t bar | points and tapers (20.2 / 14.6 / 22-25) | stay | -- | -- | -- |
| z (four tips, the top bar's right end) | tapers to 13-29 | stay | -- | -- | -- |
| a exit | the hairline exit, 14.5 at the cut | stays | -- | -- | +20 |
| C G S | the beaks with lips (73 / 36 / 60 at the -28 cut) | beaks, stay (round 275's reading) | -- | -- | -28 |
| ?, & | `_q8`'s cuts, the ampersand's own -53 cut | stay | -- | -- | -- |
| 6 top, 9 tail, 7 | a 4.6-unit point, a 12.9 tip on a -34 cut, bars | stay | -- | -- | -- |
| every dot | `ij_dot`, `dot()` | not a finial, stay | -- | -- | -- |
| b d h i l m n o p q u; H N U V A G Q R P Z L K M Y X W E F T I | probed at 1.5 px/unit: no disc; every flat end wider than 45 units is a stem under a head or a foot | clean | -- | -- | -- |

`cs_round_end` still serves the c (its walk-back is the trim); `d_ball` has
no callers and is left as `_diag` was; `C_CAP0_DROP`, `S_CAP0`, `S_CAP1`,
`S_CAP1_R`, `S_FOOT`, `S_FOOT_T` are gone (a dial nobody may turn), their
history left in place. `d_pen` grew `fin0` / `fin1`; `_c_ring` is the c's
path factored out so `fin_floor` can read the letter's own end.

### 3. Position and reach

The centerline end of every converted stroke is where it was, with two
exceptions carried on purpose: the r's arm and the y's tail, whose ball stood
PROUD of the stroke, are carried `fin_reach` further — the ball's extent past
the old end less the face's own throw along x — so the r's rightmost and the
y's leftmost ink hold to within two units at both weights (above). Measured
in the built fonts (sheared units, advance / lsb / bbox):

- Italic 400: c 337 -> 341 (xmax 314 -> 299, the top's face reaches less far
  right than the ball did); r 340 -> 341 (xmax 329 -> 339); v 394 (xmax 371
  -> 376); w 573 -> 574; x 455 (ymax 439 -> 451); k unchanged; J 315 -> 308
  (xmax 352 -> 345, as the roman's J did); 2 471 -> 473; 3 unchanged; cent
  399 -> 384 (its bar moved by the earlier ruling in the same build).
  f lsb -199 -> -215, j -210 -> -226, y -155 -> -166 and ymin -297 -> -319:
  the tails' faces lie across a stroke heading up-left, so the lower corner
  reaches 16 units further left and 22 deeper than the lobe's tip — outside
  the fitting band, so no advance moves; the pairs it met are kerned (below).
- BoldItalic: c 336 -> 344 (xmax 314 -> 287); r 375 -> 376 (xmax 365 ->
  378); v 408 -> 409; w 586 -> 587; J 372 -> 360; 2 496 -> 504 (lsb 6 -> 14);
  f lsb -206 -> -226, j -187 -> -211, y -167 -> -182 and ymin -307 -> -337.
- **The s: 313 -> 292, lsb 0 -> -31 at the 400; lsb 8 -> -8 at the 700, the
  advance 336 unchanged.** The mechanism, read in `build.fit_aldine`: the
  bearings are solved from the ink inside the band [-OVER, XH+OVER]. The old
  foot's disc had its leftmost at y 7, INSIDE the band, so the foot priced the
  letter's left. The new foot's face lies across a stroke running out level,
  its two corners 2 (w/2) tan 28 = 35 units apart along the stroke, and the
  forward (lower) corner sits at y -27 — outside the band. So the band's
  leftmost is now the face's upper corner and the lower one hangs 31 units
  past the origin; the head's face likewise reaches 16 units less far right
  than its disc did, and the band width shrank 28, which the advance follows.
  NOT pinned, for round 275's reason: the rule measures the band's ink and
  the disc no longer occupies it. `ALD.BEARINGS['s']` is one line if the
  owner wants the old advance back. The touch gate is the safety here and it
  passes (Rs 0.0176, qs cleared).

### 4. What was tried and did not hold

- `rounds.c_top_width()` as the floor (section 1): 111.5 at the 700, the
  terminal 96% of the stem, the c's top corner above its crown. Replaced by
  the italic c's own end.
- `fin_reach` with the face's across-offset ADDED to its throw: the r came
  out 15 units short of its reach (228 for 243) and the y 20 (39 for 19). On
  both ends the forward corner is the one inside the turn, which gives that
  offset BACK; the sign is measured, and the docstring says so.
- The c on its untrimmed path: 19 units wider on the right in the build,
  because the cap's trim was what kept a round terminal from growing the
  letter (its own docstring) — the top's face stood 15 units further along
  the path than the ball's centre. The cap's trim is kept, C_CAP0 / C_CAP1
  now naming only that.
- The s on its untrimmed path: 37 / 47 units further left at 400 / 700 in the
  build, and Rs 0.0090 / qs 0.0094 under the floor. Trimmed back by the face's
  throw; the fitter then re-priced it as section 3 says.
- The first touch sweep after the finials: **4 touching / 6 under the floor
  at the 400, 7 / 9 at the 700**, from a baseline of 0 / 0 at both — every one
  an f hook against a capital's top-left serif (fV -0.0150 em, fW -0.0073, fU
  0.0116; at the 700 fV -0.0259, fW -0.0167, f? -0.0117, fE 0.0048, fU 0.0078),
  or an f / j tail's lower corner under the 4's foot or the q's (4j -0.0167,
  4f -0.0038, qf 0.0119; at the 700 4f -0.0245, 4j -0.0102, qj -0.0080, qf
  -0.0037). Baseline: fV 0.0222, fW 0.0228, fU 0.0273, qf 0.0219, 4j 0.1007,
  4f 0.1150; at the 700 f? 0.0127, qf 0.0149, qj 0.0149, fE 0.0219, fV
  0.0242, fW 0.0262, fU 0.0279, 4f 0.0985, 4j 0.1114. A descender clash is a
  kern pair (round 178's reason), and the hook's is the same shape: it meets
  only a capital with a serif at that height. Kerned in `kern.py`'s italic
  block, added to what each pair carries: fV +30, 4j +32, fW +22, 4f +18, fU
  +4, qf +4 at both weights; the 700 over those f? +27, qj +23, 4f +21, qf
  +15, fV +11, fW +10, fE +10, fU +4. GPOS pairs changed: 6 in the Italic, 9
  in the BoldItalic (listed in section 6).
- `echo ====` in zsh, again: it ate the 700's final probe once.

### 5. Gates, verbatim (built fonts, this round)

```
== Italic 400: glitch
β  U+03B2
    CRACK   hole mean width 4.04 < 12.0 (area 106, perim 52)
122 glyphs swept, 1 with findings
== touch
  0 pair(s) TOUCHING, 0 below the 0.012 em floor, 1 exempt.
== dents
-- Albo-Italic: 1 dent(s) in 1 glyph(s)
   9:1058/13.7
== junctions
Albo-Italic.ttf [unımhlria]: white slivers < 6: 0, ink shards < 6: 0, steps >= 1.5: 24
== figure_space --body
  even: p90/p10 is 1.36x, within the 2.50x allowed.
== BoldItalic: glitch
122 glyphs swept, 0 with findings
== touch
  0 pair(s) TOUCHING, 0 below the 0.012 em floor.
== dents
-- Albo-BoldItalic: 0 dent(s) in 0 glyph(s)
== junctions
Albo-BoldItalic.ttf [unımhlria]: white slivers < 6: 0, ink shards < 6: 0, steps >= 1.5: 5
== figure_space --body
  even: p90/p10 is 1.47x, within the 2.50x allowed.
```

Against the baselines: glitch the ruled β alone at the 400 and 0 at the 700;
touch 0 / 0 / 1 exempt and 0 / 0 (baseline 0 / 0 / 1 and 0 / 0); dents the
9's `9:1058/13.7` at the 400 byte-for-byte the baseline's and 0 at the 700;
junction steps 24 at the 400 (baseline 24) and 5 at the 700 (round 274's 5),
slivers and shards 0.

`cmp_aldine_metrics.py`, before -> after: a 0.767 -> 0.768 (+21%, OFF at
both — pre-existing, not this round's letter), e 0.371 -> 0.369, o 1.106 ->
1.105, y w/h 0.713 -> 0.707 (DERIVED, no target: the tail's face is wider
and deeper); i and u unchanged. 1 letter outside 10% before and after, the
same letter.

### 6. Glyphs moved per weight

`diffglyphs.py` against `R277b/i400`, `R277b/bi`, `R277b/r400`:

```
italic glyphs differing: 44 | GPOS pairs changed: 6 [(('f', 'U'), (36, 40)), (('f', 'V'), (18, 48)), (('f', 'W'), (0, 22)), (('four', 'f'), (0, 18)), (('four', 'j'), (0, 32)), (('q', 'f'), (108, 112))]
bolditalic glyphs differing: 44 | GPOS pairs changed: 9 [(('f', 'E'), (0, 10)), (('f', 'U'), (36, 44)), (('f', 'V'), (18, 59)), (('f', 'W'), (0, 32)), (('f', 'question'), (-15, 12)), (('four', 'f'), (0, 39)), (('four', 'j'), (0, 32)), (('q', 'f'), (190, 209)), (('q', 'j'), (170, 193))]
r400 glyphs differing: 0 [] | GPOS pairs changed: 0 []
```

The 44, identical at both weights: IJ J Jcircumflex c cacute ccaron ccedilla
ccircumflex cdotaccent cent f ij j k kgreenlandic onehalf onethird r racute
rcaron s sacute scaron scedilla scircumflex three threeeighths threequarters
two twothirds uni00B2 uni00B3 uni0157 uni0219 uni2082 uni2083 v w wcircumflex
x y yacute ycircumflex ydieresis — every one a converted glyph or a composite
of one. The 3 is in it for its top only. The Italic's cent carries the
earlier `_currency_bar(counter=True)` ruling in the same build, as expected.

### 7. What was checked and found CLEAN

- The Regular 400: 0 glyphs, 0 GPOS pairs — `g_J`'s roman line, the figures'
  roman branches and `kern.py`'s roman table are untouched; the kern block is
  inside the aldine gate.
- The tidy that retired the dials: byte-identical to the build before it, 0
  glyphs / 0 GPOS at both italic weights.
- Every end in the table's lower half (e g t z a, the x's hooks, the k's leg,
  the j's head, the w's apex, the 3's and 5's run-outs, the 5's bar, the 6,
  the 9, the 7, C G S, ? and &, the dots), and the 31 glyphs probed at 1.5
  px/unit: no disc, no lobe.
- The BoldItalic's J shows a hairline white notch at the hook / stem junction
  in the proof — in the BEFORE image as well as the after; pre-existing, and
  the glitch sweep reads 0 on it.
- The italic's `_solid` (the v's and y's fold above the 400) still applies;
  the BoldItalic's glitch sweep is 0 with the new ends.
- The figures' spread: 1.36x / 1.47x, within 2.5x, both weights.
- `git status`: exactly `aldine.py`, `caps_straight.py`, `figures.py`,
  `kern.py`, the two docs and `shape/weights276/` — nothing else.

### 8. Left for a later round

- The s's advance (313 -> 292 at the 400) is the band fitter's honest reading
  of a foot whose lower corner now hangs below the band; if he wants the old
  fit, `ALD.BEARINGS['s']`.
- The f, j and y tails' lower corners reach 16-24 units further left and
  22-30 deeper than the lobes did; priced only where they met the 4 and the q.
- C G S keep their beaks with lips, as the roman's do — the same open
  question round 275 left.
- `d_ball` is dead code, kept as `_diag` is.
