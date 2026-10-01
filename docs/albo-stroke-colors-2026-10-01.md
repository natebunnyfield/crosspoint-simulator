# Albo's strokes in color: the twenty most frequent words (2026-10-01)

Owner, verbatim: *"subagent to draw multicolor visualization of strokes for top twenty words in
corpus"*.

The twenty most frequent words in his own books, set in Albo Regular and Italic with the font's own
advances and kerning, every letter's strokes colored two ways: by ROLE (one color per role, the
same in every letter) and by STROKE (every stroke its own hue). Where two strokes overlap, the
pixel is a darker blend of both, so every join shows. A third sheet per style shows each letter
once with its strokes numbered, which is what the tables below refer to.

Measured on commit `85d4977` (round 456, TestFlight build 281), whose fonts are the reader's
fonts: the instrument's own build matches `~/src/crosspoint-reader/lib/EpdFont/local_fonts/Albo`
for every glyph drawn (outline and advance, 15 of 15 per style) and every word's shaping (20 of 20
per style). How sure each statement is: everything below is measured by the instrument or by the
one-off checks named, unless marked *inferred*.

## The pictures

PNG at native pixels, 200 px per x-height, composed at that size and never resized (edges are
antialiased by 4x4 coverage sampling, as a rasterizer does). They live outside the repo because the
instrument regenerates them in about a minute:

| sheet | file | size |
|---|---|---|
| Regular, by role | `/tmp/albo-stroke-colors-2026-10-01/stroke-colors-Regular-roles.png` | 2400 x 4419 |
| Regular, by stroke | `/tmp/albo-stroke-colors-2026-10-01/stroke-colors-Regular-strokes.png` | 2400 x 4309 |
| Regular, numbered key | `/tmp/albo-stroke-colors-2026-10-01/stroke-colors-Regular-key.png` | 2400 x 1334 |
| Italic, by role | `/tmp/albo-stroke-colors-2026-10-01/stroke-colors-Italic-roles.png` | 2400 x 4573 |
| Italic, by stroke | `/tmp/albo-stroke-colors-2026-10-01/stroke-colors-Italic-strokes.png` | 2400 x 4463 |
| Italic, numbered key | `/tmp/albo-stroke-colors-2026-10-01/stroke-colors-Italic-key.png` | 2400 x 1977 |

Per-glyph data (every stroke's role, the evidence for it, its builder path, and the check numbers)
is in `stroke-colors-<Style>.json` beside them. To regenerate, with a Python that has shapely,
fontTools, uharfbuzz, Pillow, numpy and scipy:

    cd tools/wedge_serif
    $VENV instruments/stroke_colors.py --out /tmp/albo-stroke-colors-2026-10-01 --table

The instrument is `tools/wedge_serif/instruments/stroke_colors.py`; its docstring is the full
account of the method. It changes no shipping code.

## The twenty words

All 41 epubs under `~/src/claude-tools/*/epub/`, the corpus `outlines/cmp/corpus.py` and
`pair_census.py` read: 667,633 words, 20,975 distinct. Content documents only (`.xhtml`, `.html`,
`.htm`); `<head>`, `<style>` and `<script>` dropped (the WBN books carry inline CSS), tags
stripped, entities decoded. A word is a run of letters that may hold an inner apostrophe,
case-folded. Each word is set in its most frequent written form, which for all twenty is lowercase.

| rank | word | count | set as | surface forms (count) |
|---:|---|---:|---|---|
| 1 | the | 45,483 | `the` | `the` 37,045, `The` 8,430, `THE` 8 |
| 2 | a | 18,342 | `a` | `a` 16,597, `A` 1,745 |
| 3 | and | 16,113 | `and` | `and` 15,898, `And` 200, `AND` 15 |
| 4 | is | 12,649 | `is` | `is` 12,457, `Is` 178, `IS` 14 |
| 5 | in | 8,788 | `in` | `in` 8,318, `In` 468, `IN` 2 |
| 6 | to | 8,596 | `to` | `to` 8,461, `To` 127, `TO` 8 |
| 7 | of | 8,590 | `of` | `of` 8,550, `Of` 37, `OF` 3 |
| 8 | it | 7,844 | `it` | `it` 6,991, `It` 847, `IT` 6 |
| 9 | that | 4,953 | `that` | `that` 4,412, `That` 541 |
| 10 | not | 4,354 | `not` | `not` 4,164, `Not` 175, `NOT` 15 |
| 11 | for | 4,276 | `for` | `for` 4,087, `For` 189 |
| 12 | with | 4,001 | `with` | `with` 3,912, `With` 85, `WITH` 4 |
| 13 | as | 3,815 | `as` | `as` 3,782, `As` 33 |
| 14 | one | 3,780 | `one` | `one` 3,343, `One` 435, `ONE` 2 |
| 15 | on | 3,738 | `on` | `on` 3,590, `On` 147, `ON` 1 |
| 16 | you | 3,716 | `you` | `you` 3,240, `You` 463, `YOU` 13 |
| 17 | no | 3,146 | `no` | `no` 2,499, `No` 647 |
| 18 | what | 2,938 | `what` | `what` 2,071, `What` 867 |
| 19 | from | 2,742 | `from` | `from` 2,664, `From` 78 |
| 20 | are | 2,499 | `are` | `are` 2,388, `Are` 109, `ARE` 2 |

The twenty use fifteen letters: `a d e f h i m n o r s t u w y`.

How robust the list is:

- **Duplicate editions do not change the set.** Most books exist twice (a cascade re-flow beside
  the plain edition) and three have superseded versions. Dropping the 19 cascade editions and the 3
  superseded files (19 books, 272,289 words) gives the same twenty words; only the order shifts
  (`to` above `in`, `you` up from 16th to 12th, `as` down from 13th to 16th). The order above is the
  full corpus's, as the existing tools read it.
- **Why an apostrophe stays inside a word.** Counting bare letter runs instead splits `Kai's` and
  `it's`, and `s` becomes the 8th "word" (8,281) and pushes `are` out. Keeping the apostrophe
  inside the word changes nothing else in the top twenty.
- `I` is 28th (1,854, set as `I` 1,738 times), so no capital is drawn.
- No Spanish word reaches the top twenty, despite the Spanish books.

## How the strokes were captured

Nothing in the shipping code is wrapped or patched. Patching would not work in any case: the glyph
modules import the primitives by name (`from ..primitives import stroke, ring, ...`), so a patched
module attribute never reaches them. Instead, a `sys.setprofile` hook watches `outlines.build.draw`
draw each letter:

1. Every polygon `geom.poly` makes is an **atom**, kept with the call path that made it: the
   primitive, the glyph helpers above it, and the source line of each call.
2. Every shapely operation the drawing applies afterwards is applied to the atoms that flow
   through it, tracked by object identity. Unions pass atoms on. `difference` and `intersection`
   clip them by the other operand, so the `e`'s ring loses its aperture and the `d`'s ring is
   clipped at the stem exactly as built. `buffer` and `affine_transform` move them: the 1.2-unit
   ink spread, aldine's per-letter weight and width dials, the italic lowercase scale (x1.015, and
   x1.15 more horizontally) and the 13-degree shear. The geometry utilities in `geom.py` pass atoms through.
3. Geometry made only to measure or to cut never reaches the picture, because it never reaches the
   glyph. Two examples. The italic `n`'s `hm_follow_cut` draws a whole head just to find where the
   stem's top is cut (41 atoms made, 40 in the glyph). The roman `e`'s aperture polygon is a
   cutter.
4. Atoms group into **strokes**: the innermost single-stroke primitive above them (`stroke`,
   `wedge`, `ring`, `dot`, ...); else a helper whose only products are raw polygons (`hm_sweep`
   builds each italic arch from 36 quads, which is one stroke); else the polygon itself (the body
   `stem` draws, a head drawn as a polygon). Strokes with identical final geometry are drawn once.
   The roman `m`'s `_footed` draws each foot-carrying stem body three times, once bare and once per
   foot (4 merged); the roman `a` draws its stem twice, once per foot (1 merged). Left as three
   layers, they would read as a heavy join that does not exist.
5. Each stroke is aligned to the built glyph in the TTF by the build's horizontal fit offset,
   recovered by minimizing the symmetric difference, and clipped to the built outline. The colored
   silhouette is therefore the shipped letter. The words are set by HarfBuzz on the same TTF.

### The roles and their colors

| role | color | what the builder calls it |
|---|---|---|
| stem | `#3468D6` | `stem` (its body), `hm_stem`, `m_midstem`, `stem = stroke(...)` |
| diagonal | `#42A6E8` | the stroke inside `diagonal`; straight strokes between 30 and 84 degrees |
| bowl / loop | `#E25038` | `ring`, `ring_from`, `_e_ring`, `bowl = stroke(...)`, `bowl_ = _a_tri(...)` |
| arch / shoulder / arm | `#F29C34` | `arch`, `hm_arch`, `arm = stroke(...)`, `_r_arm`, `stroke(hood, ...)` |
| curve / spine | `#D64C9C` | `stroke(spine, ...)`; curves no name and no straight run speak for |
| crossbar | `#2EA054` | `f_bar`, `bar = d_pen(...)`; straight strokes within 30 degrees of level |
| serif | `#8654C4` | `wedge`, `end_wedge`, and the Aldine head (`hm_head`, `bd_head`) |
| terminal | `#C8A614` | `_e_tail`, `stroke(hook, ...)`, `tl = geom.poly(...)`, `term = geom.poly(...)` |
| join (exit stroke) | `#14A6A0` | `hm_exit`, `ex_ = stroke(...)`, and the italic `d`'s exit (see below) |
| dot | `#5A5A5A` | `dot`, `ij_dot` |
| unnamed raw polygon | `#8C5A2C` | reserved; no part of the fifteen letters needed it |

A role is decided in this order, and the reason is recorded for every stroke:

1. the primitive;
2. names at the call sites, innermost first;
3. helper names, outermost first;
4. the centerline's geometry, measured before the shear;
5. an unnamed curve takes its siblings' role when they agree.

Two shape checks then correct names that mislead (below). The instrument's docstring has the exact
thresholds.

On the stroke sheet, hues come from twelve of middling lightness, so a two-layer overlap still
reads as darker rather than black. Each hue is chosen as far as possible (CIE76) from its
neighbors' hues. A letter keeps its hues in every word, and touching strokes never share one; no
clash across a letter boundary needed fixing in these twenty words.

## What each letter is made of

### Regular

The roman builds every stem with the `stem` primitive, so every stem's wedges are separate strokes
(top-left wedge plus two feet on a full stem, two feet on an arch's right stem). An arch is one
`stroke` that starts inside the left stem and lands on the right one. The `o` and the `s` are a
single stroke each. The `e` is a ring drawn in glyph code (`_e_ring`, a raw polygon that mirrors
`primitives.ring`), with its aperture cut out, a separate crossbar and a separate tail. The `a`'s
top (the hood) is two strokes, an outer run-then-arc and an underside cubic, which overlap almost
entirely. On the role sheet that overlap shows as a dark band along the hood.

| letter | strokes | roles, stroke 1 first (the numbers on the key sheet) |
|---|---:|---|
| `t` | 3 | 1 stem · 2 terminal (raw) · 3 crossbar |
| `h` | 8 | 1 stem · 2 serif · 3 serif · 4 serif · 5 stem · 6 serif · 7 serif · 8 arch |
| `e` | 3 | 1 bowl (raw) · 2 crossbar · 3 terminal |
| `a` | 6 | 1 stem · 2 serif · 3 serif · 4 arch · 5 arch · 6 bowl |
| `n` | 8 | 1 stem · 2 serif · 3 serif · 4 serif · 5 stem · 6 serif · 7 serif · 8 arch |
| `d` | 4 | 1 bowl · 2 stem · 3 serif · 4 serif |
| `i` | 5 | 1 stem · 2 serif · 3 serif · 4 serif · 5 dot |
| `s` | 1 | 1 curve |
| `o` | 1 | 1 bowl |
| `f` | 5 | 1 stem · 2 serif · 3 serif · 4 terminal · 5 crossbar |
| `r` | 5 | 1 stem · 2 serif · 3 serif · 4 serif · 5 arch |
| `w` | 6 | 1 diagonal · 2 serif · 3 diagonal · 4 diagonal · 5 diagonal · 6 serif |
| `y` | 4 | 1 diagonal · 2 serif · 3 diagonal · 4 serif |
| `u` | 6 | 1 stem · 2 serif · 3 stem · 4 serif · 5 serif · 6 bowl |
| `m` | 12 | 1 stem · 2 serif · 3 serif · 4 serif · 5 stem · 6 serif · 7 serif · 8 stem · 9 serif · 10 serif · 11 arch · 12 arch |

77 strokes: 60 decided by the primitive, 6 by a call-site name, 7 by a helper name, 2 by geometry,
1 by its sibling, 1 by a shape check.

### Italic

The aldine italic is built from helpers rather than from `stem` and `wedge`: `hm_stem` (stem),
`hm_head` (the Aldine head across a stem's top, which plays the serif's part and is colored as one),
`hm_arch` (each arch a 36-quad sweep), and `hm_exit` (the outstroke that leaves every foot, the
italic's join). The `t` and the `f` are each one pen movement (the `t`'s stem runs into its exit,
the `f`'s hook runs down into its tail) plus a crossbar. The `e` is one stroke for the whole loop
and tail plus a short bar. The `s` is one stroke, the `w` four, the `y` two (the second carries the
tail). Three parts are polygons drawn in glyph code: the `d`'s head (`bd_head`), the `i`'s dot
(`ij_dot`) and the `r`'s terminal (`term`). Two more are in the `m`: its head's rounded end
(`hm_head`'s `cap`, round 143, the `m` only) and its middle stem's round foot (`m_midstem`'s `cap`).

| letter | strokes | roles, stroke 1 first (the numbers on the key sheet) |
|---|---:|---|
| `t` | 2 | 1 stem · 2 crossbar |
| `h` | 5 | 1 stem · 2 serif · 3 arch · 4 stem · 5 join |
| `e` | 2 | 1 bowl · 2 crossbar |
| `a` | 4 | 1 bowl · 2 stem · 3 serif · 4 join |
| `n` | 5 | 1 stem · 2 serif · 3 arch · 4 stem · 5 join |
| `d` | 4 | 1 bowl · 2 stem · 3 serif (raw) · 4 join |
| `i` | 4 | 1 stem · 2 serif · 3 join · 4 dot (raw) |
| `s` | 1 | 1 curve |
| `o` | 1 | 1 bowl |
| `f` | 2 | 1 stem · 2 crossbar |
| `r` | 4 | 1 stem · 2 serif · 3 arch · 4 terminal (raw) |
| `w` | 4 | 1 diagonal · 2 diagonal · 3 diagonal · 4 diagonal |
| `y` | 2 | 1 diagonal · 2 diagonal |
| `u` | 4 | 1 stem · 2 stem · 3 join · 4 serif |
| `m` | 9 | 1 stem · 2 serif · 3 serif (raw) · 4 arch · 5 arch · 6 stem · 7 stem (raw) · 8 stem · 9 join |

53 strokes: 2 decided by the primitive, 12 by a call-site name, 26 by a helper name, 11 by
geometry, 2 by a shape check.

### Every role the primitive did not decide, and the evidence

Regular:

| letter | stroke | role | builder path | evidence |
|---|---:|---|---|---|
| `t` | 2 | **terminal** | `g_t > _t_clean > poly` | assigned to `tl` at stems.py:543 |
| `t` | 3 | **crossbar** | `g_t > _t_clean > stroke` | geometry: straight at 0 degrees |
| `h` | 8 | **arch** | `g_h > arch > arch_geom > stroke` | helper `arch` |
| `e` | 1 | **bowl** | `g_e > _e_ring` | helper `_e_ring` |
| `e` | 2 | **crossbar** | `g_e > stroke` | geometry: straight at 5 degrees |
| `e` | 3 | **terminal** | `g_e > _e_tail > edge_stroke` | helper `_e_tail` |
| `a` | 4 | **arch** | `g_a > _build > stroke` | first argument `hood` at stems.py:719 |
| `a` | 5 | **arch** | `g_a > _build > stroke` | geometry: curved (net turn 165, longest straight run 0.09 xh); no name of its own, and its siblings in `_build` are arch |
| `n` | 8 | **arch** | `g_n > arch > arch_geom > stroke` | helper `arch` |
| `s` | 1 | **curve** | `g_s > _mk > stroke` | first argument `spine` at stems.py:897 |
| `f` | 4 | **terminal** | `g_f > f_ink > stroke` | assigned to `hk` at stems.py:316 (`stroke(hook, ...)`) |
| `f` | 5 | **crossbar** | `g_f > f_ink > f_bar > stroke` | helper `f_bar` |
| `r` | 5 | **arch** | `g_r > stroke` | assigned to `arm` at arches.py:284 |
| `y` | 3 | **diagonal** | `g_y > _y_tail_ink > stroke` | first argument `tail` at diagonals.py:376, but it is mostly one 1.53 xh straight run at 74 degrees |
| `u` | 6 | **bowl** | `g_u > stroke` | assigned to `bowl` at arches.py:234 |
| `m` | 11 | **arch** | `g_m > arch > arch_geom > stroke` | helper `arch` |
| `m` | 12 | **arch** | `g_m > arch > arch_geom > stroke` | helper `arch` |

Italic, leaving out the 26 strokes the `hm_*` helpers name directly (every `hm_stem` a stem, every
`hm_head` a serif, every `hm_arch` an arch, every `hm_exit` a join; all listed in the JSON):

| letter | stroke | role | builder path | evidence |
|---|---:|---|---|---|
| `t` | 1 | **stem** | `a_t > d_pen > stroke` | geometry: 1.09 xh straight run at 88 degrees |
| `t` | 2 | **crossbar** | `a_t > d_pen > stroke` | assigned to `bar` at aldine.py:5449 |
| `e` | 1 | **bowl** | `a_e > stroke` | geometry: curve turning 401 degrees net |
| `e` | 2 | **crossbar** | `a_e > stroke` | geometry: straight at 18 degrees |
| `a` | 1 | **bowl** | `a_a > _a_tri_glyph > _a_tri > _a_tri_at > stroke` | assigned to `bowl_` at aldine.py:3871 |
| `a` | 4 | **join** | `a_a > _a_tri_glyph > stroke` | assigned to `ex_` at aldine.py:3894 |
| `d` | 2 | **stem** | `a_d > stroke` | assigned to `stem` at aldine.py:4272 |
| `d` | 3 | **serif** | `a_d > bd_head` | assigned to `head` at aldine.py:4273 |
| `d` | 4 | **join** | `a_d > stroke` | assigned to `tail` at aldine.py:4281; but it starts inside a stem at 0.30 xh, dips to 0.06 xh and rises away right: an exit |
| `i` | 4 | **dot** | `a_i > ij_dot` | helper `ij_dot` |
| `s` | 1 | **curve** | `a_s > _mk > stroke` | geometry: curved (net turn 25, longest straight run 0.23 xh) |
| `f` | 1 | **stem** | `a_f > d_pen > stroke` | geometry: 1.34 xh straight run at 88 degrees |
| `f` | 2 | **crossbar** | `a_f > d_pen > stroke` | assigned to `bar` at aldine.py:5390 |
| `r` | 3 | **arch** | `a_r > _r_arm > _r_drawn_term > stroke` | helper `_r_arm` |
| `r` | 4 | **terminal** | `a_r > _r_arm > _r_drawn_term > poly` | assigned to `term` at aldine.py:4841 |
| `w` | 1 | **diagonal** | `a_w > d_pen > stroke` | geometry: 0.72 xh straight run at 78 degrees |
| `w` | 2 | **diagonal** | `a_w > d_pen > stroke` | geometry: straight at 74 degrees |
| `w` | 3 | **diagonal** | `a_w > d_pen > stroke` | geometry: straight at 79 degrees |
| `w` | 4 | **diagonal** | `a_w > d_pen > stroke` | geometry: straight at 76 degrees |
| `y` | 1 | **diagonal** | `a_y > d_pen > stroke` | geometry: 0.66 xh straight run at 71 degrees |
| `y` | 2 | **diagonal** | `a_y > d_pen > stroke` | assigned to `tail` at aldine.py:7931, but it is mostly one 0.92 xh straight run at 74 degrees |
| `u` | 1 | **stem** | `a_u > stroke` | geometry: 0.79 xh straight run at 89 degrees |
| `m` | 3 | **serif** | `a_m > hm_head > poly` | helper `hm_head` (the head's rounded end) |
| `m` | 6 | **stem** | `a_m > m_midstem > stroke` | helper `m_midstem` |
| `m` | 7 | **stem** | `a_m > m_midstem > poly` | helper `m_midstem` (the middle stem's round foot) |

## Raw polygons, and what could not be attributed

**Raw polygons** are parts drawn by `geom.poly` in glyph code rather than by a stroke primitive.
They are hatched on every sheet. There are seven: the roman `e`'s ring and the roman `t`'s tail;
the italic `d`'s head, `i`'s dot and `r`'s terminal; and the italic `m`'s head end and middle-stem
foot. Each carries a builder name that gives it a role, so the reserved "unnamed raw polygon" color
is unused.

**No part went unattributed.** Every atom that reaches a glyph belongs to a stroke with a role. What
the strokes do not cover is ink that no drawing call makes: it is added after the strokes are
unioned. In the pictures it takes the nearest stroke's color: 1.03% of the Regular sheets' glyph
pixels and 0.83% of the Italic's, counted on the supersampled grid. It comes from three sources:

- **The build's cut.** Its chords bulge past concave curves; this is most of it, see (B) and (C)
  below.
- **`geom.close_corners`, a morphological closing.**
  - The italic `s` (`aldine.py:5848`, radius 18 units): carried through the stroke's own later
    operations, the closing contributes exactly 164.1 units², and all 164.1 units² of the drawn `s`
    that no stroke covers lie inside it. The largest piece, 136 units², is at the top terminal.
  - The roman `h` (`arches.py:179`, radius 3): 73.0 of the 90.5 uncovered units².
- **Per-stroke ink spread.** Applying the 1.2-unit mitre spread stroke by stroke, rather than to the
  union, leaves hairline slivers: the `h`'s other 17.5 units², and at most 2.3 units² in any other
  letter.

## The check: do the colored parts reassemble each glyph?

Three numbers per glyph:

- **A**: the union of the captured strokes against the live drawing `build.draw(ch)`, as IoU.
- **B**: the drawing against the built glyph in the TTF, after alignment.
- **C**: the share of the built glyph the strokes cover.

| Regular | A | B | C | uncovered (units²) | stroke ink past the built outline | duplicates merged |
|---|---:|---:|---:|---:|---:|---:|
| `t` | 0.99998 | 0.9867 | 0.9925 | 347 | 0.0059 | 0 |
| `h` | 0.99902 | 0.9733 | 0.9871 | 1,235 | 0.0145 | 0 |
| `e` | 0.99999 | 0.9752 | 0.9892 | 667 | 0.0144 | 0 |
| `a` | 0.99990 | 0.9712 | 0.9871 | 910 | 0.0163 | 1 |
| `n` | 0.99991 | 0.9790 | 0.9897 | 760 | 0.0109 | 0 |
| `d` | 0.99995 | 0.9766 | 0.9896 | 993 | 0.0132 | 0 |
| `i` | 0.99999 | 0.9796 | 0.9911 | 351 | 0.0117 | 0 |
| `s` | 1.00000 | 0.9564 | 0.9893 | 562 | 0.0344 | 0 |
| `o` | 1.00000 | 0.9767 | 0.9881 | 877 | 0.0117 | 0 |
| `f` | 0.99990 | 0.9824 | 0.9917 | 546 | 0.0094 | 0 |
| `r` | 0.99999 | 0.9827 | 0.9896 | 453 | 0.0071 | 0 |
| `w` | 0.99997 | 0.9916 | 0.9938 | 573 | 0.0022 | 0 |
| `y` | 0.99992 | 0.9823 | 0.9911 | 692 | 0.0090 | 0 |
| `u` | 0.99994 | 0.9807 | 0.9908 | 633 | 0.0103 | 0 |
| `m` | 0.99989 | 0.9759 | 0.9888 | 1,237 | 0.0132 | 4 |

| Italic | A | B | C | uncovered (units²) | stroke ink past the built outline | duplicates merged |
|---|---:|---:|---:|---:|---:|---:|
| `t` | 0.99998 | 0.9739 | 0.9945 | 269 | 0.0212 | 0 |
| `h` | 0.99991 | 0.9848 | 0.9935 | 568 | 0.0089 | 0 |
| `e` | 0.99986 | 0.9568 | 0.9878 | 656 | 0.0325 | 0 |
| `a` | 0.99980 | 0.9766 | 0.9920 | 595 | 0.0159 | 0 |
| `n` | 0.99979 | 0.9832 | 0.9924 | 518 | 0.0096 | 0 |
| `d` | 1.00000 | 0.9787 | 0.9883 | 1,291 | 0.0098 | 0 |
| `i` | 0.99982 | 0.9624 | 0.9950 | 188 | 0.0341 | 0 |
| `s` | 0.99570 | 0.9644 | 0.9871 | 537 | 0.0276 | 0 |
| `o` | 1.00000 | 0.9710 | 0.9872 | 784 | 0.0166 | 0 |
| `f` | 1.00000 | 0.9738 | 0.9927 | 707 | 0.0194 | 0 |
| `r` | 0.99995 | 0.9839 | 0.9930 | 329 | 0.0092 | 0 |
| `w` | 0.99999 | 0.9850 | 0.9935 | 611 | 0.0086 | 0 |
| `y` | 1.00000 | 0.9770 | 0.9936 | 462 | 0.0171 | 0 |
| `u` | 0.99996 | 0.9752 | 0.9942 | 403 | 0.0195 | 0 |
| `m` | 0.99978 | 0.9828 | 0.9933 | 663 | 0.0107 | 0 |

Reading the numbers:

- **A is 0.9997 or better** everywhere except the roman `h` (0.99902) and the italic `s` (0.99570).
  Both gaps are the corner closings accounted for in the section above.
- **B, 0.956 to 0.992, is the build's deliberate cut.** It moves dropped vertices onto chords, one
  vertex in four kept, and that is not a capture error. Control, measured on round 455's tree (round
  456 changed no outline): a Regular build with `FJORD_CUT=0` raises B for `s o h e n a t f r` from
  0.956-0.987 to 0.992-0.993. What remains is integer rounding and the build's contour clean-up
  (weld, despike, despur).
- **C, 0.987 to 0.995**, is the same cut seen from the built side. The uncovered pixels are filled
  from the nearest stroke, and "stroke ink past the built outline" is clipped away. Neither is
  visible as a defect on the sheets.

**Is the picture what ships?** Two checks say yes:

- **Against the reader's fonts.** The instrument builds its TTFs from the live tree and compares
  them with the reader's copy. Every glyph drawn is identical in outline and advance (15 of 15 per
  style), and all 20 words shape identically, in both styles. A sweep of all 7,225 pairs over 85
  characters (letters, figures, punctuation, accented vowels) also shapes identically.
- **The build itself.** A build of the same tree with the build Python (`3.14.4t`, fontTools
  4.64.0) is byte-identical to the reader's fonts in every table but `head`, which is the build
  timestamp. The instrument's venv (fontTools 4.66.1) encodes GPOS and GSUB with different bytes
  and the same positions.

## Checked and found clean, and the traps on the way

- **A round shipped mid-session, and only the shipped-font comparison caught it.** Round 456
  (ligatures only where they keep the stem rhythm; the italic mark rule at 0.95) landed at 18:03 as
  build 281, after this work's first comparison at 17:55 had shown the tree byte-identical to the
  reader's fonts. The next comparison showed GSUB and GPOS differences. Every one of them was round
  456's: the Regular no longer ligates `ff`/`fi`, and six italic pairs with `í`/`ñ` moved 1-11
  units. None touches the twenty words. The worktree was fast-forwarded to round 456 and everything
  above was re-run there. The instrument now runs this comparison on every run (check D in its
  docstring).
- **The capture misses nothing the drawing keeps.** A, above.
- **Names alone mislead in three places, and two shape checks correct them:**
  - The roman `y`'s `_y_tail_ink` is its whole right diagonal, not a terminal.
  - The italic `y`'s `tail` is likewise its whole second diagonal.
  - The italic `d`'s `tail` is the same exit construction the italic `a` calls `ex_`.
- **Two rule bugs caught on the first sheets, now fixed:**
  - The roman `t`'s crossbar had copied its sibling tail's role, before geometry could call it
    straight and level.
  - Every stroke inside `_t_clean` and `_build` took a name from a tuple unpacked one level up
    (`st, tl, b = _t_clean(...)`), which cannot say which target is which part.
- **A latent bug was found and deleted.** aldine's width dial calls `affinity.scale`, which hands
  shapely a 12-element (3D) matrix; a point helper that read only six elements was dead code and is
  gone. The stroke geometry was never affected, because shapely receives the whole matrix.

## Limits

- **Roles are an interpretation.** The builder's names come first and geometry second, and the
  evidence is recorded for every part. A single pen movement gets one role, the role of its longest
  straight run. So the italic `t`'s stem-and-exit, the `f`'s hook-stem-tail and the `u`'s
  stem-into-bowl are each one stroke colored as a stem. The stroke sheet shows each as one hue,
  which is the more literal view.
- **The Aldine head is colored as a serif** because it plays the serif's part on the italic stems.
  The builder calls it a head, and the JSON says so.
- **Overlaps are computed on 4x supersampled binary masks.** Two-layer overlaps darken by x0.62 per
  extra layer. A hairline overlap narrower than a quarter pixel is not drawn.
- **The instrument covers these 30 glyphs.** It runs on any word, but its role rules were checked
  on these 30 glyphs only. On another letter, read its `--table` output before trusting a color.
