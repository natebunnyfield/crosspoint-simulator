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

---

# Round 379, 2026-09-24 — the whole Greek, a cursive italic, and spacing

Owner, 2026-09-24, to the three open items of §7 (a, b, c): *"yes to all"*.
Built on `c87068a` (round 375). Every number below was measured on the four
shipping cuts built with `build_env.sh`'s environments (Regular 400, Italic
400, Bold 700, BoldItalic 700) unless it says otherwise. Nothing here has
been seen by the owner; it is a proposal until he rules on the pictures.

## 9. What was added (item a)

| | glyphs | how |
|---|---|---|
| drawn lowercase | ζ η ι κ ν ξ υ χ ψ ς | traced (§9.1), drawn in `symbols2.py` from Albo's own parts |
| drawn capitals | Γ Θ Λ Ξ Ψ | from the Latin capitals' parts (F's stem and arm, the O, the A's legs, the T's bar, cap stems) |
| composite copies | Α Β Ε Ζ Η Ι Κ Μ Ν Ο Ρ Τ Υ Χ and ο | `build.GREEK_COPY`: a TrueType composite of the Latin glyph, at its advance and bearings. In the italic the component is the italic's own capital |
| tonos | ά έ ή ί ό ύ ώ | composites of the letter and Albo's acute (Unicode decomposes them to letter + U+0301); ό sits on the o |

37 new glyphs per cut, all four cuts; the cmap now holds the whole basic
Greek alphabet, both cases. Not added: the capitals with tonos (Ά Έ ...), the
dialytika (ϊ ϋ ΐ ΰ), U+0384 tonos as a spacing mark, and the polytonic
breathings, so John 1:1 was set monotonic (render b).

**Glyph order.** The new drawn Greek is APPENDED to `CHARS`
(`build.GREEK_APPEND`) instead of sorted in among the Greek, so cut.py's
per-contour phase counter does not advance for any glyph that already ships.
The composites draw no contours. Result, measured by outline hash with each
glyph's own x-origin factored out (`scope.py` in the round scratchpad):
**0 non-Greek glyphs changed shape, advance or side bearing, in all four
cuts** — Latin, figures, punctuation, symbols, `∑ ∏` and `µ` included. The
cut-0 control asked for was therefore not needed to separate a ripple: there
is none. `contours-baseline.txt` changed only by the 37 new rows per style
(74 rows, every one `None -> n`; no existing count moved), accepted.

**One roman change that is spacing and not drawing.** The roman Δ Φ Ω α γ δ
ε θ λ ρ σ φ ω hash as "changed" in the Regular and Bold. A control build with
`ALBO_GREEK_SPACING=0` hashes all of them identical to round 375: the change
is only the integer rounding of a re-fitted x offset (§11).

### 9.1 The traced targets, new letters (Albo units, x from the left ink edge)

Median of Iowan, Georgia, Times and Palatino through `cmp_greek.py runs`,
mapped as in §1. After = the Regular as built.

| | traced construction | after w, bottom..top | ref median w, bottom..top |
|---|---|---|---|
| ζ | cap stroke under the ascender (curl at (95,752), run at y 690); spine x 330 at 630, 205 at 500, 88 at 330, 45 at 200; round bottom at y 20; right side 0.76 o down to -90, hooked left to (245,-222) | 397, -255..762 | 403, -246..769 |
| η | Albo's n (stem + wedge, arch, stem) with the right stem to -281; no feet (3 of 4 refs) | 445, -281..447 | 481, -281..446 |
| ι | the i's stem and wedge, no dot, no foot, turning into the t's tail (end 147 u right, y 86) | 265, 3..430 | 262, -14..441 |
| κ | the k's arm and leg at the x-height (arm from 0.40 xh to the k's end wedge, leg at the k's 56°) | 461, -22..460 | 527, -11..442 |
| ν | the v's thick stroke, a thin stroke curving upright to the x-height in the c's finial | 439, -13..442 | 484, -13..440 |
| ξ | ζ's cap stroke and bottom; upper lobe ending at a left waist (y 348) with a pen tongue to 0.71 o, as ε | 400, -255..762 | 428, -245..772 |
| υ | the u's left stem, one round stroke turning on the baseline and up to the finial | 450, -10..455 | 492, -16..443 |
| χ | down-right stroke heavy (the pen's broad side), down-left thin; both to the descender. Refs split 2/2 on which stroke is thick; the pen decided | 493, -283..454 | 515, -247..437 |
| ψ | straight stem ascender to descender through a υ cup. Refs split 2/2 on the stem's top (Iowan, Palatino: ascender; Georgia, Times: x-height); the humanist two were followed | 570, -281..784 | 640, -281..584 |
| ς | the c's top finial, round left side, ζ's bottom | 395, -255..457 | 383, -244..446 |
| Γ | F without the middle arm | 549, -1..676 | 527, 0..674 |
| Θ | Albo's O, bar at mid-cap from 0.31 to 0.69 with an upright tick (0.20 C tip to tip) at each end, floating clear of both walls as in all four refs | 703, -15..690 | 701, -15..689 |
| Λ | the A without its bar, at the A's own solved width | 696, -15..689 | 726, 0..679 |
| Ξ | T's top bar, bottom bar with rising wedges, middle bar 0.23..0.76 with the Θ's ticks | 608, -1..676 | 607, 0..674 |
| Ψ | cap stem (both wedges, both feet) and two arms, cap stems from the cap line turning in on the O's round pen to meet it at 0.30 C | 767, -1..676 | 802, 0..674 |

## 10. The cursive italic (item c)

**What the italic references do**, measured unsheared by each face's own
slant off `l` (`instruments/greek376_italic_widths.py`,
`greek376_latin_analogue.py`, `greek376_italic_caps.py`):

- A Greek lowercase keeps its proportion to its LATIN ANALOGUE across the
  roman/italic change: η/n 0.87 italic vs 0.90 roman, μ/u 0.91 vs 0.95, κ/k
  1.03 vs 1.01, σ/o 1.08 vs 1.12, ο/o 1.00 vs 1.00 (medians of 4). It does
  NOT keep its width against the o: Iowan's italic o is 0.78 of its roman o
  while its italic α is 0.96 of its roman α.
- The italic Greek capitals are the roman ones ~4% narrower: median italic/
  roman 0.965 over Γ..Ω (H 0.96, O 0.94, E 0.97 on the same faces).
- The redraw is cursive: η is an italic n with a descender, μ an italic u
  with one, ν the italic v's movement, ι a plain-topped stem with an exit, τ
  and π a drooping bar over stems that leave in an exit, κ a stem with a
  curved arm and a flicked leg.

**Construction** (`outlines/glyphs/greek_italic.py`, live only under
`ALBO_ITALIC=aldine`; nothing in `aldine.py` was edited):

- **Built from the Aldine letters themselves**: η = `a_n`'s stem, head, arch,
  right stem run to the descender; μ = `a_u` plus a descender stem; ν = `a_v`'s
  frame, points and width table with the thin stroke carried upright to the
  x-height into the finial; ι = the i's stem and `hm_exit` with no head and no
  dot (a plain top keeps it from reading as ı); α = the italic o's ring, a
  stroke rising 12 over the x-height, and `hm_exit(.., 'a')`; τ and π = a
  drooping pen bar, `hm_stem` and `hm_exit` ('t' and 'n'); κ = `hm_stem` +
  `hm_head`, a nib arm into the italic finial and a nib leg that flicks up; υ
  and ψ = the u's down-round-up movement with the head, carried to the
  x-height; σ and ρ = the italic ring with a thinning nib bar / an Aldine
  stem.
- **The traced roman skeleton re-drawn in the italic's hand** for the letters
  with no Latin shape (β γ δ ε ζ θ λ ξ ς φ χ ω): `symbols2.hand()` installs an
  `ItalicHand` for one draw, and the roman functions' five helpers route to
  it — the skeleton unit scaled by (Albo's italic Latin analogue / roman),
  measured LIVE from the two drawings (o 0.70, x 0.88, y 0.77, k 0.74 in the
  shipping Italic); the ring = the Aldine o's (superellipse at `O_K`, 35°
  nib re-spread to `CON_O`); round strokes on that nib; pen strokes on the
  50° chancery nib sized so a vertical is the Aldine stem; stems = `hm_stem`
  / `hm_head`; free ends = the italic finial at `fin_floor()`.
- **Capitals**: all ten drawn Greek capitals take `symbols2._cw` — the Latin
  capitals' measured `CAP_NARROW` 0.953 on POSITIONS, italic only, and never
  for ∑ ∏ (which borrow Σ Π). The 14 copies are the italic's own Latin.

**IoU against the four italic references** (`cmp_greek.py iou --style
italic`, sheared glyphs compared as rendered; means over letters × refs):

| | Italic 400 | BoldItalic 700 |
|---|---|---|
| 19 existing letters, round 375 (sheared) → 376 (cursive) | 0.428 → 0.420 | 0.376 → 0.463 |
| 10 new lowercase | 0.357 | 0.416 |
| 5 new capitals | 0.376 | 0.508 |
| **calibration: Albo's own italic Latin** n u v o t k a p i H A O E | 0.430 (n 0.32, u 0.27, v 0.37, t 0.58) | 0.493 |

Read honestly: at the BoldItalic the cursive moved the Greek toward the
references by +0.087; at the Italic 400 it did NOT move the mean (−0.008).
α 0.57→0.47, τ 0.50→0.25, γ 0.31→0.20, θ 0.47→0.38 fell; μ, λ, ρ, ω, Δ, Σ,
Φ, Ω rose. Albo's own italic n and u score 0.32 and 0.27 on the same
instrument — the Aldine lowercase is narrower than every reference italic
(its o is 0.76 xh against their median ~0.86), and letters built from its
parts inherit that. The italic τ (built from the t, 281 wide) and η (from the
n) sit where the Latin they are made of sits. This is a number for the owner
to weigh against the picture (render c), not a verdict.

## 11. Spacing (item b)

**Method.** `build.GREEK_SIDES` gives each Greek SIDE the final bearing of the
Latin letter whose side it is (ο o/o, α o/t, η n/n, ρ o/o, σ o/r, ι i/t, υ
u/o, Θ O/O, Π H/H, Σ Z/E ...), measured in the band and space that letter is
fitted in (`fit_greek`: the Aldine lowercase unsheared as `fit_aldine`,
everything else as `fit`). On top, `GREEK_SIDE_ADJ` carries the references'
own Greek-minus-Latin offset where Albo fell outside their spread, fitted by
`instruments/greek376_space.py --fit`: in EACH face, a Greek side's 2-D
closest-approach white (`cmp_space_2d.Face.gap`, shaped pairs, partners
`aeinorstu` / `HOEDN`) minus its analogue's; a side inside the four
references' spread is left alone, one outside is moved to the nearer edge
(clamped 30 units a pass, two passes, the third reproduces the table to ±2).
Rows: `rom` (Regular), `bold` (Bold, against the bold references), `ald`
(both italics; there is no bold-italic Greek reference set). The eta is the
clearest case: its stems have no feet, so copying the n's bearing set it
0.04 em TIGHTER than the references put it; +34 units on its right fixes it.
**One row is hand-set, not fitted:** the italic Ψ (12, 14) — its arms'
two-way wedges, sheared, touched in ΨΨ.

| cut (refs) | mean abs(Albo − ref median), em: default → round 379 | sides inside the refs' spread |
|---|---|---|
| Regular (roman) | 0.0126 → 0.0083 | 42 → 63 of 68 |
| Bold (bold) | 0.0130 → 0.0082 | 40 → 57 of 68 |
| Italic (italic) | 0.0238 → 0.0109 | 33 → 59 of 68 |
| BoldItalic (italic) | 0.0248 → 0.0117 | 37 → 56 of 68 |

"Default" is the same drawings built with `ALBO_GREEK_SPACING=0` (every Greek
glyph on the straight/straight rule). The bench (`bench_fit.py --check`) is
untouched; no Latin bearing moved.

## 12. Gates, four cuts, before (round 375) and after

| gate | result |
|---|---|
| `cmp_contour_hairs` full + `--letters` | **no new finding** in any cut. Three were raised while drawing and fixed: Regular ξ 166° REVERSAL at a two-lobe hairpin (redrawn with an ε-style waist and tongue) and a 151° HAIR at its curl (curl eased); Italic ε 151° HAIR at the waist (`_close3`, a 3-unit mitre close); Italic ρ 165° REVERSAL where stem and ring edges grazed (stem moved 3 units outside the ring) |
| `cmp_aldine_glitch --all --ttf` | no new finding. Θ (2 islands, the floating bar) and Ξ (3 bars) are declared in `MULTI` with the reason, the way `=` and `%` are |
| `cmp_counter_dents` at 700 and 900 (ASCII letters, figures, `&@`, all Greek) | Bold 0, BoldItalic 0. The first italic build dented α and ρ at the 700 (the stroke on the italic ring); `_heavy` (convex counters above stem 84) fixed both. Italic 400 keeps round 373's open-waist β (15068/90.0, was 16520/90.0); the ruling covers the 700/900 |
| `cmp_touch` (ASCII pairs) | identical counts all four cuts |
| Greek pairs (`instruments/greek376_touch.py`, 4,949 pairs: Greek×Greek, Greek×Latin both ways) | **0 Greek-Greek pairs under 0.012 em** in any cut, once the italic Ψ was widened. Remaining findings are all mixed-script: descenders into the Latin j/f/q tails and y (ηj χj ηf χf ζf ξj ςj qβ qρ ...), f's hook over Π/Τ (0.0005, 0.0048 em Regular). Not fixed; see §14 |
| `./gates.sh` | GATES UNCHANGED; both approved g's unchanged (`approved.py`); bench matches; contour census accepted (74 added rows only) |
| `gen_state.py --check` | was already OUT OF DATE at `c87068a` (round 375 moved lines in `marks.py`); regenerated |

## 13. Checked and found CLEAN

- 0 non-Greek outline, advance or bearing change in any of the four cuts.
- The roman's existing Greek drawings are byte-identical to round 375 when
  the new spacing is switched off (`ALBO_GREEK_SPACING=0`).
- ∑ ∏ unchanged in the italic although Σ Π narrowed (`_cw` keys on the
  character being drawn).
- Italic contour counts of the 19 redrawn letters equal round 375's (no
  phase ripple: every glyph after them hashes identical).
- The roman Greek IoU mean is unchanged (0.499 Regular, 0.560 Bold) for the
  19 existing letters; the new roman letters score 0.43 (lowercase) and 0.48
  (capitals) against the Latin copies' 0.41 on the same instrument.

## 14. Negative results, and what is not done

- **The first ξ ran both lobes to a common tip** at the right, as a pen
  writes it; the hairpin is a 166° REVERSAL whatever the widths. The waist
  had to be built like the ε's.
- **The first italic Λ read the A's width through `W`**, which in the italic
  solves the Aldine A — a different drawing — and made Λ 0.72 of the roman's,
  a slash (IoU 0.07). It now takes the roman A's own solve (600 on the width
  axis) narrowed by `_cw`: IoU 0.28 (A itself 0.31).
- **The first italic υ and ψ used the u's own path**, whose low point sits in
  the left third; both read as v. They now turn round in the middle and are
  1.30 / 1.10 pitches wide.
- **Fitting the spacing to the references' MEDIAN** asked to move nearly
  every side of the roman, eight of them to the 30-unit clamp, while the
  analogue transfer alone had barely moved the roman's mean (0.0126 → 0.0124):
  four faces disagree by up to 0.07 em on one side. Fitting only what lies
  OUTSIDE their spread, to its nearer edge, is what §11 ships.
- The italic's horizontal is the 50° nib's THICKEST stroke, so the ζ/ξ cap
  stroke first came out a heavy slab; it is drawn at 0.62 in the italic hand.

**Not done:**
- Greek **kerning**: no Greek glyph is in `kern.py`'s classes (the copies do
  not inherit the A's or the T's pairs; ΤΑ, ΑΥ, ΛΑ are unkerned).
- Capital tonos forms (Ά Έ Ή Ί Ό Ύ Ώ), dialytika, polytonic breathings.
- Mixed-script collisions in §12 (Greek descenders against Latin j/f/q/y);
  they are pairs no Greek or English text sets adjacently.
- The italic Greek IoU at the 400 did not rise (§10); if the owner wants the
  italic Greek WIDER than Albo's own italic Latin, the unit in
  `greek_italic.analogue_ratio` is the one lever.
- The tonos is centred on the letter's ink box (no optical table for Greek,
  as round 369 made for a and e).
- Nothing here is device-confirmed; renders only.

**Renders** (round scratchpad `greek376/`): `a-alphabet-four-cuts.png`,
`b1-greek-text-54px.png`, `b2-greek-text-13px-x5-nearest.png`,
`c-italic-before-after-refs.png`.

```bash
cd tools/wedge_serif
PYTHON_GIL=0 python3 instruments/greek376_space.py <default.ttf> <after.ttf> --style roman|bold|italic [--fit]
PYTHON_GIL=0 python3 instruments/greek376_touch.py <Albo-Italic.ttf>
cd instruments && PYTHON_GIL=0 python3 greek376_latin_analogue.py && PYTHON_GIL=0 python3 greek376_italic_caps.py
```
