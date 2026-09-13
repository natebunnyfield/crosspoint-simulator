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

## Numbers (all measured on the built TTF)

- o: outer 501 × 443, **counter 353 × 340 = 1.036** (ruling). O_RX 227 (was
  226; the +1 lands the aspect exactly).
- Bearings: no non-letter under 20 a side. Letters past the advance: f
  right −82 (hook), j left −85 (tail), J left … (hook), Q right −540 (tail)
  -- the ruled tucks -- and **q right −14** (its right foot wedge, measured
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
