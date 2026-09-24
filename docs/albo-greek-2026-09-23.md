# Albo's Greek, traced — round 373, 2026-09-23

Owner, 2026-09-23, after seeing the Greek set beside reference faces:
*"for greek letters: they are mostly wrong, trace"*.

All 19 Greek glyphs were redrawn: `α β γ δ ε θ λ μ π ρ σ τ φ ω Δ Π Σ Φ Ω`,
plus `∑ ∏`, which are copies of `Σ Π`. The code is
`tools/wedge_serif/outlines/glyphs/symbols2.py`, Greek section. No letters
were added (see §7). Surveyed on commit `1fd1fdd`, which includes round 371
(`b89be44`). Every number below was measured on the four built cuts
(Regular 400, Italic 400, Bold 700, BoldItalic 700, built with
`build_env.sh`'s shipping environment) unless it is marked as inferred.

## 1. The instrument: `tools/wedge_serif/cmp_greek.py`

Round 371 found the epsilon mirrored only by looking at it next to other
faces. No gate can see a letter that is clean geometry but the wrong shape.
`cmp_greek.py` turns that look into a script:

- **`iou`** — this is `cmp_aldine_shape.compare_xh` applied to the Greek.
  The lowercase is compared at one x-height and the capitals at one cap
  height. Both glyphs are aligned on the baseline and on their left ink
  edge, and the score is intersection over union. Each face's x-height is its
  OS/2 `sxHeight`, or the ink top of its `x` when it declares none (Iowan).
  Albo's own `x` is not used, because its wedge tips reach 451 where the
  x-height is 429.
- **`runs`** — the tracing tool. It maps each reference **into Albo's
  units**. Vertically the mapping is piecewise: 0 to x-height lands on 0..429,
  x-height to ascender on 429..771 (the top of Albo's `l`), and 0 to
  descender on 0..−281 (the bottom of Albo's `p`). Horizontally it scales by
  the ratio of the two faces' `o` widths. It then prints every ink run at
  fixed heights, so the centre of each stroke can be read at each height,
  one reference at a time.
- **`box`** — the same mapping, reduced to bounding boxes and their median.

The references are the Greek on this Mac: Palatino, Iowan Old Style, Georgia
and Times New Roman, in their roman, bold and italic cuts. Their Greek was
confirmed through the cmap. Albo draws a humanist face, so Iowan and Palatino
are the closest in spirit. **Calibration:** Albo's Latin letters, which
already belong to the face, score 0.40–0.62 in the Regular (o 0.57, n 0.60,
e 0.58, p 0.48, d 0.40) and 0.52–0.74 in the Bold, against the same
references. The shared weight and serif differences put that ceiling on
every letter. A Greek letter in that band is as close to the references as
Albo's own Latin is.

## 2. The audit: what was wrong, letter by letter (before, Regular)

Each entry gives width, bottom and top in Albo units, measured before the
change, then the median of the four references mapped into Albo units.

| | before (w, bottom..top) | ref median | what was structurally wrong |
|---|---|---|---|
| α | 338, −27..407 | 534, −16..446 | two-thirds width; short; the tail dipped under the baseline; the bowl was a free ring with a separate hooked stroke, not a stroke standing on the bowl's right side |
| β | 312, −186..621 | 446, −281..770 | stopped 150 under the ascender and 95 short of the descender; narrow; two bowls closed on the stem where the references run one stroke with a waist cusp |
| γ | 367, −108..441 | 477, −281..437 | a crossed Y with a slanting leg ending 173 above the descender line; no V on the baseline and no descender |
| δ | 293, −1..431 | 451, −16..770 | **did not ascend at all**: a small hook sat on a small bowl inside the x-height |
| ε | 306, −13..449 | 383, −16..446 | narrow; the waist was an X-crossing with spurs (round 371). The mirror was already fixed in 371 |
| θ | 277, −1..646 | 450, −16..770 | 124 short of the ascender; 62% of the reference width |
| λ | 379, −30..633 | 518, −11..745 | 112 short at the top; the long stroke ran on a single line with no hooked start and no foot; the leg's end sat under the baseline |
| μ | 280, −180..441 | 509, −281..429 | 55% width; descender 100 short; the right stem had no foot |
| π | 415, −15..430 | 530, −14..428 | legs were straight posts; the bar had no dropped left end; no tail |
| ρ | 305, −180..430 | 445, −281..445 | 68% width; descender 100 short; a hairline-floored ring lighter than the o |
| σ | 388, −1..323 | 522, −16..433 | **0.75 of the x-height** (the top at 323); the bar grazed the bowl (371) |
| τ | 320, −12..430 | 408, −14..428 | a T: plain stem, no tail, no dropped bar end |
| φ | 311, −185..569 | 584, −281..446 | the STROKED form (U+03D5's glyph) at half width. U+03C6's reference glyph since Unicode 3.0 is the looped form, and so is 3 of the 4 references |
| ω | 380, 25..292 | 633, −16..441 | **0.68 of the x-height, floating 25 above the baseline** (a subscript); dented counters at the 700s |
| Δ | 841, −1..677 | 633, 0..679 | a third too wide; one uniform stroke with no thick and thin |
| Π | 619, −1..676 | 733, 0..674 | 15% narrow; the bar did not overhang the stems |
| Σ | 471, −1..676 | 594, 0..674 | 21% narrow; no serifs on the bar ends |
| Φ | 461, −1..676 | 711, −1..677 | 65% width; a tall narrow bowl |
| Ω | 704, −1..621 | 730, 0..689 | **0.92 of the cap height**: an O cut off above two loose feet |

## 3. What each letter was traced to, and how it is drawn now

The skeleton coordinates are the median of the `runs` scanlines from Iowan,
Georgia and Times, with Palatino added where its letter has the same
structure. Palatino's π, ρ and τ are cursive forms and were left out. The
coordinates are written in Regular units against an `o` 465 wide. Each x is
scaled by `_u(c)`, the current build's `o` width divided by that 465, so a
letter keeps its proportion to the `o` at every weight and width. The weight
never comes from a table:

- straight and diagonal strokes use the pen (`pen_widths`);
- curves use the o's own round pen (`bowl_widths` × `O_W_ADJ`, floored at
  `O_FLOOR_ADJ`);
- bowls use the o's ring;
- free round ends take the c's finial (`finial_widths` / `finial_cut`);
- bars, wedges and capital stems are Albo's own.

| | traced targets (Albo units) | construction | after (w, bottom..top) |
|---|---|---|---|
| α | stroke centre at 0.80 o, top at x-height + 10, tail end 0.28 o past it at y 50 | o-ring with its right wall inside the stroke; the stroke ends in the t's tail | 515, −14..453 |
| β | stem centre 45; upper bowl right edge 0.76 o at 560–640; waist tip y 392; lower bowl 0.84 o at 215 | stem plus two round strokes meeting at the waist tip. **Open waist at ≤ stem 84** (tip centre 80 u right of the stem edge; ink gap measured 144 vs Iowan 147 at y 390). **Closed above 84** (§5) | 415, −281..776 |
| γ | left-arm centres 137/162/187/212 at y 340/280/215/150; right arm 390/370/345/312; V centreline junction at y −15 | pen strokes, the thick one running down-right; curled start with a finial; straight descender | 437, −281..453 |
| δ | neck back 0.22 o at y 560–640; hook top on the ascender; end at 0.81 o, y 668 | o-ring plus a round-pen neck ending in the c's finial | 453, −15..776 |
| ε | upper arc 60–330 wide, terminal (330, 372); lower arc terminal (370, 92); tongue at y 217 to x 262 | two round strokes that END at the waist (no crossing), plus a pen tongue | 384, −20..455 |
| θ | 0.97 o wide, baseline to ascender, bar at y 350 | tall o-ring, bar buried in both walls | 451, −14..772 |
| λ | long stroke through (230, 560) (272, 380) (343, 150), foot flick to (488, 32); leg foot at 0.13 o | pen strokes; the leg's foot cut level with the A's bracket at 0.7 size | 496, −6..772 |
| μ | the u of every reference with a descender | Albo's own roman u construction (`arches.g_u`), left stem run down to −DESC | 491, −281..430 |
| π | 1.12 o wide; legs at 0.40 and 0.83 o; left leg curving to (78, 8) | bar with a hanging left wedge; round-ended left leg; right leg in the t's tail | 531, −1..430 |
| ρ | bowl 0.96 o; stem's outer edge on the bowl's | o-ring plus a straight stem from mid-bowl to −DESC | 448, −281..444 |
| σ | bowl = o; flat top at x-height + 8; bar to 1.11 o | o-ring plus a bar from the crown whose underside drops away (1.30 swell) | 518, −15..438 |
| τ | 0.88 o wide; stem at 0.41 o | bar with a hanging left wedge; stem in the t's tail | 409, −1..430 |
| φ | loop sides 45 and 518; stem 0.60 o; looped top-left finial open to the stem | one round stroke from the finial round into the stem, plus a straight stem | 548, −281..455 |
| ω | 1.36 o; lobe sides 42 and 588; middle at 0.68 o rising to 318 | two mirrored round strokes starting on finials, plus a pen middle stroke | 620, −17..460 |
| Δ | 633 wide, apex at the cap line | the A's legs (thin 0.72, thick 1.0, `pw`) cut level at both ends, on a CAP_BAR base | 636, −1..679 |
| Π | 733 wide, stems at 0.18 / 0.82 | the T's bar (both ends hanging) over two cap stems with both feet | 736, −1..676 |
| Σ | 594 wide, vertex at 0.54 w on mid-cap | the E's outer bars (hanging and rising wedges) plus a **mitred** chevron | 588, −1..676 |
| Φ | 711 wide, bowl between 0.14 and 0.86 C | the O's ring plus a cap stem with top and foot wedges | 709, −1..676 |
| Ω | 730 wide, top 689, legs landing at 0.29 / 0.69 | one round-pen stroke that turns in to the legs (catmull through the superellipse), on two feet with rising outer wedges | 717, −1..689 |

## 4. Shape match: IoU, before → after

The comparison uses the lowercase at a common x-height and the capitals at a
common cap height, aligned on the baseline and the left ink edge. The full
tables, per letter and per reference, are in the scratchpad
(`greek373/iou-table-after.md`). The Regular table is reproduced below.

| cut vs reference set | mean of 19 letters × 4 references |
|---|---|
| **Regular vs roman refs** | **0.258 → 0.499** |
| **Bold vs bold refs** | **0.321 → 0.560** |
| Italic vs italic refs | 0.276 → 0.428 |
| BoldItalic vs italic refs | 0.326 → 0.376 |
| Italic, **unsheared 13°**, vs roman refs (control) | 0.256 → 0.543 |
| BoldItalic, unsheared, vs bold refs (control) | 0.321 → 0.564 |

Regular, mean over the four references (Palatino, Iowan, Georgia, Times):

| α | β | γ | δ | ε | θ | λ | μ | π | ρ |
|---|---|---|---|---|---|---|---|---|---|
| .25→.61 | .31→.52 | .11→.37 | .16→.37 | .34→.56 | .28→.42 | .14→.32 | .19→.34 | .35→.38 | .32→.52 |

| σ | τ | φ | ω | Δ | Π | Σ | Φ | Ω |
|---|---|---|---|---|---|---|---|---|
| .16→.57 | .44→.57 | .24→.54 | .19→.50 | .19→.64 | .40→.61 | .34→.49 | .22→.61 | .31→.55 |

Reading the numbers:

- **Every Regular letter's mean rose.** The Regular set now scores inside
  the calibration band of Albo's own Latin letters (0.40–0.62), apart from
  γ δ θ λ μ π. The ascending letters (δ θ λ) are held down by the method
  itself. Albo's ascender is 1.80 x-heights and the references' is about
  1.58. Albo's ascender is its own proportion (the `l` shares it), so a
  correct δ, θ or λ loses overlap at the top when the faces are compared
  at one x-height. μ scores 0.58 against Iowan, whose μ is exactly a u with
  a descender, and about 0.26 against the three references whose left stem
  is thinner and set further in.
- **The italic, measured against the italic references, falls on several
  letters in the BoldItalic** (β .36→.20, μ .48→.22, ρ .43→.22, λ .28→.18).
  Albo's italic Greek is the roman Greek sheared by 13°, which was already
  true before this round. The references' italic Greek is redrawn cursive:
  Palatino's italic ρ has a tail, and their slants differ. The control
  unshears Albo's italic and compares it with the roman references, and
  there the italic rises 0.256 → 0.543 and 0.321 → 0.564, the same gain the
  roman shows. So the drawing now matches in the italic too. The fall
  against italic references is the difference between a sheared roman
  and a cursive Greek: it is inferred from that control and was not tested
  further. A cursive Greek italic is recommendation 7c.

## 5. Gates, on all four cuts, before and after

Run with the shipping builds: `cmp_contour_hairs.py` (full and `--letters`),
`cmp_aldine_glitch.py --all --ttf`, `cmp_touch.py`, and `cmp_counter_dents.py`
at both 700s (`--chars` = the ASCII letters, figures and `&@`, plus the
Greek).

| finding | before | after |
|---|---|---|
| Greek HAIR / REVERSAL (hairs, full sweep) | Regular `alpha` 152.6° on a 3.2-unit arm | **none, all four cuts** |
| Greek glitch (SPLIT / CRACK / PINCH / NOTCH …) | none (round 371 cleared them) | **none** |
| Greek counter dents at the 700s | Bold ω 950/25.2 ×2 and δ 104/7.5; BoldItalic ω 969/26.4, 969/24.2 and δ 104/7.8 | **none**. `dents.Bold` and `dents.BoldItalic` now exit 0 |
| `hairs --letters` | Bold exit 1 (pre-existing, not Greek); others 0 | unchanged |
| touching pairs | Regular 1 / 2 below, Italic 0 / 0, Bold 0 / 2, BoldItalic 1 / 2 | identical |

`gates.sh` against the tracked baseline, after `--accept`, reports **GATES
UNCHANGED**. The accepted delta, and why each part is explained:

- Regular: `alpha` left the full-sweep hair list. It is the Greek fix.
- Italic: `trademark` and `uni2655` left the list and `uniE001` joined it.
  This is the cut-phase ripple below, and the cut-0 control shows no
  drawing of those glyphs changed.
- `contours-baseline.txt`: beta 3 → 2 and phi 3 → 2 in both 400s.

Three hair findings appeared while the letters were drawn, each at a join
the new drawing had created, and each was fixed:

| where | cause | fix |
|---|---|---|
| Ω legs, 169.5° REVERSAL | the legs ended on the feet's top edge, so they grazed it | the legs end inside the feet |
| σ, 153.4° HAIR | the bar's underside met the bowl's shoulder where the shoulder is flat | the bar swells to 1.30 so it crosses where the shoulder is steep |
| Bold γ V and ε waist (156–157°, 1-unit arms) | two heavy strokes met at a grazing crotch | `_close`, a 4-unit mitre close above stem 84. It is the device `_barred` already uses |

**The β's open waist at the 400s is read as a dent by `cmp_counter_dents`**
(Regular 16918/92.1, Italic 16520/90.0). The waist is designed to be open:
the two counters are one, as in all four references. The 2026-09-19 ruling
covers the 700 and the 900, and there the waist is closed and reads clean.
The 400s were not dent-gated before this round. Run the same way before,
the 400s read one dent, `δ` 226/10.9 (Regular) and 214/11.2 (Italic), and
that one is gone.

## 6. Scope: which glyphs changed

fontTools compares each glyph's coordinates, the before build against the
after build:

| cut | drawings changed | Greek | non-Greek | metrics-only |
|---|---|---|---|---|
| Regular | 82 | 21 | 61 | 0 |
| Italic | 86 | 21 | 65 | 0 |
| Bold | 21 | 21 | **0** | 0 |
| BoldItalic | 21 | 21 | **0** | 0 |

The non-Greek changes are **only the cut-phase ripple**, and this was
proved, not assumed. The Regular and the Italic were rebuilt at
`FJORD_CUT=0` from HEAD's toolchain and from this change. At cut 0 the
decimation phase does nothing, and **21 glyphs differ, all Greek, with 0
non-Greek**. The 700s ship at cut 0, which is why they show no ripple.

The rippled glyphs are the ones built after `omega` in glyph order: glyph
order index 199 onward, where omega is 194. They are symbols, figures'
fractions and superiors, chess pieces, suits, music signs and the
`uniE000`–`E005` / `FB0x` ligatures. **No Latin letter or ASCII figure
moved.**

The ripple could not be avoided without drawing the wrong letter. β
(3 → 2 at the 400s) and φ (3 → 2) change their contour counts because the
references' forms have fewer counters: β's open waist makes one counter,
and the looped φ has only one closed counter. The Greek block's total
therefore went from 32 to 30. Round 371 accepted the same class of ripple.

## 7. Checked and found CLEAN, negative results, recommendations

**Checked and clean.** The following were checked and nothing needed to
change:

- the approved-glyph ledger: `approved.py` is unchanged for both `g`s;
- the bench: `bench_fit.py --check` still matches;
- touching-pair counts are identical in all four cuts;
- the Greek glitch sweep is empty in all four cuts;
- `hairs --letters` is unchanged;
- no Greek glyph lost or gained an ink island.

`∑` and `∏` follow `Σ` and `Π` as before.

**Negative results.** Each of these was tried and did not work:

- The first γ ended its arms at y 30. The arms are thick and meet at a
  narrow angle, so their inner edges crossed about 90 units above that
  point, and the V sat 0.25 of the x-height up. The centreline junction
  has to be below the baseline, at y −15, for the crotch to land where the
  references put it (about y 70).
- A σ bar of constant thickness, equal to the ring's top wall, still
  raised a HAIR at the shoulder. The bar's thickness mattered less than
  the angle at which it met the shoulder.
- Sampling the Ω's arc every 15° and then adding leg points left a
  visible knee at the join. Sampling every 10° and adding intermediate leg
  points that bend gradually (54° → 72° → 80°) removed it.
- The first Δ used the A's square apex face, which stood up as a spur.
  Both faces are now cut level.

**Not changed, needs a ruling or a round of its own.**

- (a) **The missing Greek:** ζ η ι κ ν ξ ο υ χ ψ ς, and the capitals
  beyond Δ Π Σ Φ Ω. No Greek word can be set in Albo. Adding them was out
  of scope by instruction.
- (b) **Greek spacing:** every Greek glyph falls through to
  `SIDES` = straight/straight in `outlines/build.py`. The round letters
  (α δ ε θ ο ρ σ φ ω) would take the round fraction if they were given
  entries. Spacing is fitted from the owner's bench, so this was not
  touched.
- (c) **A cursive italic Greek:** the italic is the roman Greek sheared.
  Real italics redraw their Greek (§4).
- (d) **ω rises above the other lowercase:** its top is 460 against the
  reference median of 441, because the finial swell carries the lobes'
  terminals up. ε is 455 against 446.
- (e) γ: its right arm's top and its left curl are finials, where Iowan
  uses slab serifs. That choice was made to fit Albo's round terminals and
  is open to his eye.

## 8. Reproduce

```bash
cd tools/wedge_serif
PYTHON_GIL=0 python3 cmp_greek.py iou  <Albo-Regular.ttf> --style roman     # bold / italic
PYTHON_GIL=0 python3 cmp_greek.py box  <Albo-Regular.ttf>
PYTHON_GIL=0 python3 cmp_greek.py runs <Albo-Regular.ttf> αβγ --refs Iowan,Georgia
```
