# Fjord rebuild: the designed-outline set (2026-09-13)

Every decision and every measured number of the rebuild, so the next agent
continues without re-deriving. The brief is `docs/fjord-glyph-guide.md` §0;
the rulings it obeys are that guide's §3. The round-17/20 generator is
untouched and still builds the round-51 font (the "before" here).

## State

- **All 93 glyphs drawn and built** (A–Z a–z 0–9, the 30 marks, space,
  .notdef): `outlines/glyphs/{arches,rounds,stems,diagonals,caps_straight,
  figures,marks}.py`. Built by `PYTHON_GIL=0 python3 -m outlines.build
  <out_dir>` from `tools/wedge_serif/`. Output for this round:
  `scratchpad/wedge/fonts/rebuild/Fjord-Regular.ttf` (16 KB; the round-51
  file is 32 KB -- one outline per solid instead of overlapping stroke
  polygons), `fjord-specimen.html` (the round-19 page), `fjord-rebuild.html`
  (the proof page), `fjord-overlay4.html`, and `Fjord-Regular-round51.ttf`
  (the before, copied).
- **Checked at 300–700 px and 54 px, family by family:** n m h u r, o c e,
  b d p q, a, s, i j l, f t, v w x y z, k, g -- each looked at over Garamond
  (and n m h u r over Van den Keere too) with `outlines.cmp.dbg`, then
  through FreeType with `outlines.cmp.look`. Capitals, figures and marks
  were looked at through FreeType at 170 px in one pass each; they were
  NOT individually overlaid on the references by eye (the flag instrument
  covers them, below). That is the honest boundary of this round's looking.
- **Nothing is committed or published** (per the brief).

## Architecture (what is where)

| file | what |
|---|---|
| `geom.py` | curves as sampled point lists at `SPACING` 11 units (the record's density, so the cut's facets are ~45 units as before); `poly`/`union`/`ink`/`contours` on **shapely 2.1.2** (installed this round; `skia-pathops` still does not build on 3.14t -- checked again). `contours()` returns exteriors ccw and holes cw for nonzero TrueType. |
| `pen.py` | the design constants from `round19.DESIGN` and `alphabet2.Pen(82, 0.60, 26, 0.95)`: `th(deg)`, `TH_V` 77.3, `TH_H` 55.4, `HAIR` 33; `check(outer, inner)` reports a drawn stroke's width against the pen. |
| `primitives.py` | `stem` (one solid: body with entasis + its wedges), `wedge` (the family's bracket, apex `length` out and `drop` back, quadratic bracket tangent to the stem edge, control 0.65 up), `stroke` (centerline + width f(t), square/pen-cut ends), `edge_stroke`, `ring` (designed superellipse outer, counter = pen offset, smoothed), `ring_from` (any drawn outer), `half_bowl` (the D's ring for D B P R), `diagonal` + `end_wedge` (the record's side convention: +1 on a top-left end points up-left), `bar`, `beak`, `trap`, `dot`, `widths` (keypoint interpolation). |
| `cut.py` | the one-in-four cut, seed 73, one running phase counter across contours in glyph order, **every corner kept** (turn > 20°). |
| `build.py` | draw → `buffer(1.2)` → contours → cut → round-20 fit → TTF. Caps/figures widths solved against `garalde_caps.json` medians exactly as `round20.solve_widths` (3 passes, clamps 0.7–1.45). |
| `cmp/dbg.py` | rasterizes the drawing (even-odd XOR of contours) with a reference face behind it. |
| `cmp/look.py` | FreeType render at a size with rules. |
| `cmp/checks.py` | o counter, bearings, validity, ink past the advance. |
| `cmp/overlay4.py` | the four-reference flag instrument (cmp_garamond's metrics) + overlay cells. |
| `cmp/proof.py` | the mobile-friendly proof page (750 px blocks at 375 CSS px, PNG only; e-ink quantization 0.108/0.42/0.812 → 255/200/96/0 at 54 px, 8x supersampled). |

## How "designed outline" is honored, exactly

- Stems: ONE contour per stem including its wedges. Entasis kept at 14%
  but as a **quartic** (`(2t−1)^4`), not the record's quadratic: same 88 at
  the ends, the middle 60% within 1% of 77 -- the quadratic waisted the whole
  stem visibly at 300 px. (Decision, not a ruling; reversible in
  `primitives.stem_width`.)
- Arches (n m h u r): BOTH edges are cubics I drew (`arches.arch_geom`):
  outer leaves the stem at 0.80 xh at 50°, peaks at xh+12 (ruling), comes
  down vertical into the right stem's right edge at 0.50 xh; inner peels
  off the stem at 0.52 xh (ruling) at 74°, peaks 52.6 under the outer,
  vertical into the right stem's left edge at 0.58 xh. `pen.check` on the
  n arch: width/pen 0.57 at the join (a hairline by design) … 0.96 at the
  stem. The u is the arch mirrored through the letter's centre and the
  x-height's middle, dropped 2 units so its bottom takes the rounds' 14.
- Rounds: the outer is the designed superellipse (k 2.1); the counter is
  the pen's inward offset by tangent, Chaikin-smoothed twice, resampled.
  This IS an offset, stated plainly; the stress it gives is the o's.
- The a's bowl: a drawn closed outer (diagonal top from the stem, round
  bottom), counter by pen offset with a 28-unit floor; the closing edge is
  82 inside the stem so the counter's offset lands ON the stem's edge.
- b d p q: the ring's far stroke centred half a stem outside the stem's
  centre (the record's placement) and the ring **clipped 5 units inside the
  stem's inner edge**; the union is the join, the counter's edge is the stem.
- Everything curved that is a stroke (c, e's arm, s, f hook, t tail, j
  tail, y tail, g neck and ear, Q tail, J hook, 2 3 5 6 9, &, @, ? ( ) ):
  `stroke(centerline, widths)` with the widths DECLARED as keypoints
  (`widths([...])`) or as `pen_widths` × a declared profile. Terminals:
  flare + pen cut (20°) where the record used them; beaks (face sheared
  −28°, lip 0.4 × 0.7 of the family) on C G S; lowercase c and s take the
  same beak with a 0.35 × 0.6 lip and −22° on the s.
- Joins: `geom.ink(solids, cutouts)` = shapely union minus the traps. No
  end face is visible anywhere; every buried end is inside the union.
- Traps: at the arch crotches (ruling), 0.22 stem deep, 18° half-angle,
  and at the b d p q crotches 0.18 stem. Invisible at 54 px, visible at 300.
- The cut: applied to the finished contours; corners (turn > 20°) always
  kept, so wedge apexes and end faces are never chamfered. Verified at
  700 px (`rb/cut1.png`): sharp apexes, faceted curves only.
- Ink spread: `build.INK_SPREAD` = 1.2 units buffer on every glyph -- the
  record's `Cut` grew every polygon by that (offset_naive, 3.0 × 0.4), and
  the shipped l stem measured 81, not the pen's 77; without it the page was
  4% lighter. Kept so the weight the owner picked his dials on survives.

## Regression pass (coordinator, after the first build): six defects, fixed

Found by rendering every glyph before/after at 150 px and suspects at 500 px
(`scratchpad/wedge/regress-z1..z4.png`, `regress-0..3.png`, re-rendered
after the fixes). Each with the cause, since every one was a construction
error of the rebuild and not a drawing choice:

1. **d q ran through the stem, 18% wide** (ink 589, adv 671/610): the
   record's stem placement `x = cx + rx_c − s/2` was copied with a `+`.
   Now d 507 / adv 589, q 507 / 528 (round 51: 501 / 583, 499 / 541).
2. **Nicks at the a b p u joins**: the b d p q trap cutouts pointed INTO
   the strokes (the crotch's air is the counter, the V opened the other
   way) -- removed, no ruling asks for them on the bowl letters; the u's
   trap was the n's point-reflected, so it faced into the bowl -- removed
   (the u carries none; n m h r keep theirs, 0.22 stem, facing the
   counter). The a's crotch under the hood: the bowl's top now springs at
   0.67 xh so the crotch is the shallow V round 51 has, not a 30-unit
   wedge; its counter's lower-left tooth (the pen-by-tangent offset
   stepping 33 → 77 over a few samples at the diagonal-to-round turn) is
   gone with DECLARED widths ramped along the bowl and a gentler turn.
   Contour counts after: a 2, b 2, p 2, u 1 (no join adds a hole).
3. **& slits, % slits**: the & was one self-crossing polygon whose
   crossings became holes; `stroke(pieces=True)` unions short overlapping
   pieces (the @'s ring too). The % rings used the centerline radius as
   the OUTER radius (counter 86 of 240); they take r + pen/2 now: 686 wide,
   counter 163 of 317, as round 51 (687).
4. **x heavy**: the thin stroke was 0.72 of the STEM (57); round 51 had
   0.72 of the pen at its down-left angle (50 × 0.72 = 36). Only the x was
   named; v w y still carry 57 -- for the coordinator to rule.
5. **5**: the bar was top-aligned on D where the record centred it (top
   433 → 460; round 51 461) and its stem lacked the cap factor (66 → 75).
6. **s**: had the capital's 0.92-stem spine and beak; round 51's lowercase
   s is the pen's own widths, flare 1.25 into a 20° cut both ends. Width
   328 → 366 (round 51: 366).

## Second regression pass: the thin-stroke rule everywhere, the g's joins

- **Round 51's rule for every diagonal** (`alphabet2._diag`, `latin.diag`):
  width = multiplier x the PEN's width at the stroke's own angle. A
  down-right stroke is the pen's ~82, a down-left one its ~50, so the
  "0.72" thins are 36-50 and the capital `diag`'s cap factor cancels (its
  thick diagonals are the pen's 82, not 88). `pw(p0, p1, mult)` in
  `diagonals.py` and `caps_straight.py` now gives exactly that. Applied to
  v w x y (thin 0.72), k (arm 0.78, leg 1.0), A (left leg 0.72, right 1.0),
  M (outer 0.72, inner 1.0), N (diagonal 1.0; its stems were already
  0.72 x the cap stem = 63), V W X Y (thin 0.72), K (arm max(0.72 pen,
  0.47 stem) = 38.5, leg 1.1 x pen at its angle = 47), U (right stem was
  already 0.78 x the cap stem = 69), and the y's tail takes round 51's
  profile (0.72 rising to 1.0 by the middle, flare 0.3 into the cut).
  Measured as horizontal ink runs across each glyph at 1000 px (thin /
  thick), round 51 → rebuild: v 54/90 → 53/91, w 54,55/87,89 → 55,55/88,90,
  y 62/92 → 68/91, x 54/108 → 54/107, A 55/92 → 54/90, M 54,57/81,94 →
  55,58/80,93, N 65,65/112 → 65,67/111, V 54/91 → 54/91, W 53,53/88,88 →
  55,55/89,90, X 54/110 → 54/109, Y 53/104 → 53/104, K 73/92 → 72/91,
  U 70/90 → 72/91. Ink widths within 8 of round 51 on every one.
  R's leg: ruled the same way on the third pass -- 1.05 x the pen at its
  60-degree angle (64), not the constant 92. Horizontal run across the leg
  at 0.22 C, round 51 → rebuild: 101 → 103 (the stem beside it 94 → 91);
  R ink 656 → 663, adv 731 → 738.
- **g**: the neck's square start face straddled the bowl's centerline and
  one corner broke the ring's edge (a nick at 500 px); it now starts 22
  units inside the bowl's stroke, and its end thins to 0.25 over the last
  10% so no corner reaches the loop's counter (round 51: taper_out 0.85 /
  8%). The ear starts 24 inside the ring at 0.45 of its width, rising to
  full by 28%. At 700 px (`rb/g700.png`) every join is one solid; g has 3
  contours (outer, bowl counter, loop counter).
- Word darkness after both passes: lowercase median 0.1334 → 0.1296, word
  median 0.1344 → 0.1290.

## Brush-stroke revision (owner on the shipped rebuild, 2026-09-13)

Owner: "D B P R all need a lot of brush stroke revision, after those do
every other letter." The rule, from the coordinator: every point of every
curved stroke at the thickness the pen gives its tangent; joins and
terminals as strokes the nib could make. Stems, the wedge family and every
§3 number unchanged. Before = `Fjord-Regular-ship1.ttf` (the first
shipped rebuild), phase 1 = `Fjord-Regular-phase1.ttf`.

**Phase 1, D B P R** (`fjord-phase1-DBPR.html`). Why the bowls were tubes:
`half_bowl` looked the pen's tangent up by an index computed on the
pre-resampled path, so after `ring_from` resampled it the widths were
shifted by the closing segments' samples and the top took the right
side's 77. `half_bowl` is now a PEN STROKE: the designed centerline (half
superellipse, k x 1.12, outer edges on the cap line and baseline, the
fixed widths) offset by pen.th(tangent)/2 both sides, both ends running
22 units into the stem and tapering to 0.42 of the pen over 10% (no slit,
no square end). The opened bottom (ruling) lifts the centerline's lower
half by 0.15 of the horizontal and adds 0.3 to the width, so the outer
edge holds. `pen.check` width/pen: D 0.43 at the start, 1.09-1.33
through the opened lower half (the ruling's +30%), 0.98-1.00 over the
upper half, 0.41 at the end; B upper 0.94-1.01 (0.79-0.81 at the
shoulder, where the nearest-inner metric shortens across the turn), B
lower / P / R as the D. B: upper bowl 0.86 of the lower (ruling), both
bowls' thin ends meeting at the stem at 0.55 C -- the waist is the pen's
horizontal thinning to a hairline at the stem. R: the leg is a stroke,
foot-first on a cubic bowed 9 units outward, 1.05 x the pen at 60° (64)
at the foot thinning to 0.42 of that where it enters the bowl's stroke at
-52°; the A's foot wedge. **Pen stress note**: the ruled pen (26°) puts a
bowl's maximum at the tangent 116°, i.e. 2 o'clock, and its thinnest at
11 and 5; Van den Keere's D carries its weight at 4 o'clock. That is the
pen's definition, not the drawing -- moving it is an owner's ruling and
would move every round.

**Phase 2, every other letter** (`fjord-phase2-{rounds,bowls,arches,
diagonals,caps,figures,marks}.html`):
- arches n m h u r: round 51's nib arch again -- a designed centerline
  leaving the left stem's inner edge at 0.52 xh (ruling), solved to put the
  outer edge at xh + 12 (ruling), vertical into the right stem at 0.60 xh
  -- offset by the pen (hairline up along the stress, 55 over the top, the
  full stem down the shoulder), thinning into the stem (taper 0.30 over
  32%). The right stems rise to 0.66 xh so the arch's end face is inside.
  The trap notch stays. `pen.check` on the n: 0.30 at the join (the
  taper) rising to 1.0 by t 0.33, 1.0 thereafter (a 1.39 spike at t 0.46
  is the nearest-point metric crossing the peak's inner curvature). u:
  round 51's nib u (cubic bottoming at the rounds' overshoot, pen widths
  thinning 0.42 into the right stem). r: round 51's arm (pen widths with
  the 0.78-stem floor of round 36, taper 0.5 into the stem, flare 0.5 into
  the pen cut).
- a: the bowl's counter is the pen's offset at each tangent, the width
  sequence averaged over +-4 samples (a tight turn steps it); the closing
  edge inside the stem at 40 so the counter lands on the stem.
- U: the bowl on round 51's profile -- the pen x CAP_STEM(1 - 0.22 t),
  swelling by the entasis over the first and last 15% to meet the stems.
- 2 4 7: their straight diagonals at the pen's width for their angle
  (they were the vertical's 77 / 58).
- , ; ‘ ’ “ ” ! ( ): tails, the bang and the parens on the pen x round
  51's profiles ((0.9 - 0.6 t), (0.55 + 0.5 t), (0.6 + 0.4 sin)).
- Already on the pen and left alone: o c e, b d p q, g, s, f t, j (its
  tail holds stem weight through the turn by ruling), y's tail, the
  straight diagonals (0.72 / 1.0 x the pen at their angle), C G S, O Q,
  J, the figures' arcs, & @ ? % *.
- Kept as ruled: stems (entasis, wedges), the e's bar, the K arm's 0.47
  floor, the R leg's 1.05, the Q tail's belly floor, the 9's 0.9, the j.

## Numbers (all measured on the built TTF)

- o: outer 501 × 443, **counter 353 × 340 = 1.036** (ruling). O_RX 227 (was
  226; the +1 lands the aspect exactly).
- Bearings: no non-letter under 20 a side. Letters past the advance: f
  right −82 (hook), j left −85 (tail), J left … (hook), Q right −540 (tail)
  -- the ruled tucks -- and **q right −16** (its right foot wedge, measured
  outside the band; the record's q had the same shape). Left as is.
- The advances of stem letters grew ~10 units (l 292 → 304, n 636 → 646):
  the wedges are sharp now, so the band's ink is wider; a 13 pt line holds
  ~3% fewer characters than the round-51 build (visible in the proof's
  paragraph pairs).
- Word space 353 (the record's; computed on the uncondensed n counter as
  round 20 did -- my first build had 313 from the condensed one).
- Weight, `word_weight.py` at 54 px, round 51 → rebuild: lowercase median
  darkness 0.1334 → 0.1317 (−1.3%), word median 0.1344 → 0.1295 (−3.6%).
  Per letter: n −12, h −11, r −10, l −10, a −9, m −8 … g +10, x +8, s +8.
  Two causes, both intended: the arches are designed thinner over the
  shoulder (the references'), and the wedges are SHARP now -- the record's
  Cut chaikin-rounded every wedge apex, so its letters were ~10 units
  narrower in the band (l advance 292 → 304, n 636 → 646) and read darker
  per advance. The o e c s x g got a little darker (true counters, beaks).
- Mean stroke by 2·area/perimeter is NOT comparable before/after: the
  round-51 glyphs are overlapping polygons and their perimeter double-counts,
  so their "stroke" was understated (v 52 → 63, n 51 → 64 are the same ink).
- Flags (`cmp/overlay4.py`, cmp_garamond's thresholds), round 51 → rebuild:
  **Garamond 35 → 43, Van den Keere 32 → 41, Dante 67 → 69, Edgar 65 → 64,
  of 92.** An earlier build of the same drawings read 32 / 34 / 68 / 63;
  the difference is `geom.poly` keeping every piece of a self-crossing
  stroke (needed for the &, whose loop was lost) and eleven glyphs then
  sitting 1–5% over a threshold that they sat just under: d q width +23%
  (the right foot below the band; the record's d had the same foot but
  its Cut rounded the apex ~10 units shorter), A V W Y 7 8 9 % # stroke
  +29–32% (threshold 25%), p q bottom +0.13 (threshold 0.12; the ruled
  descender), 2 3 top +0.12. None is a drawing defect; each was looked at. The Dante/Edgar counts are structural (their cap/x ratio and
  figure boxes flag every capital and figure on "top"); the Garamond/VdK
  residue is punctuation (quotes, parens, slashes, =, +, …), I (width, by
  design), J (bottom, by design), and every diagonal letter (v w x y z A V
  W Y 7) on **stroke +29–47%** -- which is the contrast ruling (0.60 kept:
  the pen's thin diagonal is 57 where Garamond's is ~30) now measured
  honestly on one outline per glyph. e was
  +28% wide at E_RX 195 and is at 186 (441 → ~420 wide); t was +0.15 xh
  tall and its top is xh+95 (was +120).
- Caps width multipliers solved: A .94 B 1.16 C .92 D 1.45(clamp) E 1.05
  F .94 G .88 H 1.05 J 1.45(clamp) K .98 L 1.04 M 1.02 N 1.05 O .89 P 1.07
  R 1.09 S .98 T 1.30 U .96 V 1.08 W 1.17 X 1.21 Y 1.11 Z 1.27. Q reads
  the O's key as the record did (its tail would otherwise shrink the ring).

## Where the rulings could not be met, or were bent

- **q's right foot** pokes 14 past the advance (band fitting rule vs. a
  foot below the band). Not fixed: the fitting rule is ruled.
- **The entasis curve** (quartic) and **the e's radius** (186) and **the
  t's top** (xh+95) and **the r's reach** (172·wf) are shape decisions toward
  the references, inside the guide's "the strokes' actual outlines … are
  drawn again". None touches a §3 number.
- **Dot height** of i j (xh+118+0.3 s) kept from the record; Van den Keere
  flags it low, Garamond does not.
- **Parens** overshoot cap/desc by 16 (was 30); still the tallest marks.
- **Ink traps** are a cutout, not a paper polygon (the README trap).
- **Counters are offsets**, not hand-drawn second curves (stated above).

## Not done / next

- Individual eye-overlays of capitals, figures and marks on the four
  references (only the flag instrument and one 170 px look each).
- The stroke flags on v w x y z are the contrast ruling; if the owner wants
  the diagonals lighter that is a pen decision, not a drawing fix.
- Accents, kerning, hinting, the bold: unchanged, as the guide's §6/§7.
