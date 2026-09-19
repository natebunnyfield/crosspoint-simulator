# wedge_serif — the Albo type exploration toolchain (Fjord until round 58, 2026-09-13)

A parametric humanist wedge-serif being designed for longform reading on the
CrossPoint X3 and its iOS port, by evolution: the owner is shown populations
of variants and marks keepers; each round narrows or diverges on his ruling.
The full dated log of rounds, rulings, measurements and negative results is
[`docs/wedge-serif-exploration.md`](../../docs/wedge-serif-exploration.md).
**Read its "State" section first.** This file is the map of the code. How to draw a glyph that belongs -- pen, serifs, proportions, rulings, the judging loop -- is [`docs/fjord-glyph-guide.md`](../../docs/fjord-glyph-guide.md).

## The owner's working rules (recorded at round 51, 2026-09-12; still standing at round 179)

1. **He judges pictures, never prose.** Every round ends in an Artifact page
   of real renders; for fonts, the page embeds the TTFs and sets text in
   them. A word is not enough: *"I cannot judge this by a single word. It
   needs to be a sentence with meaning behind it."* The evaluation sentence
   is in the exploration doc.
2. **Diverge on request, converge on ruling.** *"Right now everything's
   converging, and I needed to diverge ... This is an evolutionary
   approach."* Do not narrow a population on your own judgment.
3. **The deliverable is vector font files.** *"what i need are vector font
   files, not bitmap treatments. we are generating fonts for epub reading."*
   Raster treatments were a wrong turn (round 11).
4. **Humanist end of the spectrum**, longform text face, legible.
5. **Defects can be charm.** *"there is a charm to naively putting shapes
   together and having defects ... let me decide what needs fixing."* Keep
   defects as knobs, never auto-polish.
6. **Elegance is in the drawing, not the dials.** *"try harder. there is no
   elegance"* was answered by a second drawing model, not new parameters.
7. **He names the letters; one ask per round.** Since round 25 he starts
   from what works and names what to fix; a round is that fix, rendered
   before/after, the specimen republished, the TTF sent, the doc appended.
8. **No spacing page** (round 25). Bearings come from the fitting rule; his
   spacing readout of round 22 stands.
9. **Rulings are reversible only by him** -- the J's bar was "kept always"
   in round 21 and removed in round 36 on his word.
10. **Always pay attention to the space inside and between characters** (owner, 2026-09-13). Counters and apertures, and the fitting: every variant page reports both; every ruling on weight, contrast, width or x-height is checked for what it did to them.
11. **Build only what the task needs** (owner, 2026-09-14: "stop regenerating fonts and assets unnecessarily, only if a task needs it"). A ladder of static Mediums and one page is a round; the VF rebuild, the specimen / sliders / proof republish and the TTF resend are batched until a ruling lands or he asks. A status question gets a doc update, not a build.
12. **"Detwinning"** is the owner's name (2026-09-14) for the variety work: the audit (`outlines/cmp/variety.py`, `docs/albo-variety-audit-2026-09-13.md`) plus the life (`primitives.life`), making every serif and counter very slightly its own so they render the same at reading size and differ at display size.

## Files

| File | What |
|---|---|
| `outlines/kern.py` | **Albo's kerning** (round 95, ruled "hand class kerning"): LEFT/RIGHT classes, `CLASS_PAIRS` and `PAIRS` in 18-unit steps, written as a GPOS `kern` feature by feaLib; `outlines.build` applies it to every build, `python3 -m outlines.kern <ttf> [<out>]` re-applies to an existing file in seconds. `reader_view()` runs the firmware's own extractor at 54 px. The lowercase is deliberately unkerned (measured: the fitting rule is right there). |
| `outlines/glyphs/ligatures.py` | fi fl ff ffi ffl (round 96) on the f's parts (`stems.f_ink` with a re-aimed hook); `FI_PUSH` / `FL_PUSH` / `FF_STEP` place the following stem. Reached by cmap U+FB00-FB04 (`build.LIGS`) and the `liga` feature in `outlines/kern.py`. |
| `outlines/cmp/rhythm.py` | The space BETWEEN letters against the space WITHIN (round 96b): the autokerner's clamped-white metric and a bridged variant, the font's rhythm over ~150 common English bigrams, a letter's white against every common neighbour on each side. `python3 -m outlines.cmp.rhythm <ttf> <letter>`. |
| `outlines/glyphs/accents.py` | The thirteen diacritics on the pen, the Czech apostrophe-caron, the dotless i and j (round 99). Each drawn at x=0 with its foot at y=0; `build.ACCENTED` places it. |
| `outlines/glyphs/symbols.py` · `symbols2.py` | The epub symbol set (round 99): arrows, guillemets, braces, marks, mathematics, currency, dingbats, geometric shapes; then the superscripts and fractions (which ARE the figures, scaled), the Greek, the non-composite Latin, the chess pieces, the card suits and the music signs. |
| `outlines/cmp/corpus.py` | **The coverage gate.** Counts every character in the owner's 34 epubs and diffs against a font's cmap, in frequency order; exits non-zero while any corpus codepoint is missing. Run it before claiming coverage. |
| the italic (round 100) | `pen.SLANT` shears the finished ink about the baseline; `pen.ITALIC` switches the letters a real italic redraws -- the single-storey a and the descending f, both in `glyphs/stems.py`. Build one with `FJORD_SLANT=11 FJORD_WIDTH=95 ... --style Italic`. **There are TWO italic lowercases and this is the default one**; see `outlines/glyphs/aldine.py` below. |
| `outlines/glyphs/aldine.py` | **The Aldine italic**, drawn from the Griffo scans (rounds 114-179), selected by `ALBO_ITALIC=aldine` (`ALBO_ALDINE=1` is an alias). `_DEFAULT = "classic"`, so it is reached by name only and nothing is deleted either way (round 118). It defines the whole lowercase -- enforced at import by an OWNERSHIP check, because a missing letter otherwise falls through to the classic italic and the build still succeeds -- plus twenty-one capitals, the ten figures through a hand press (`FIG_HAND`, round 167), and the capitals' bearing deltas (`CAP_BEARING_ADJ`). Round 118's note that it is lowercase-only is history. Nearly every dial in it is an `ALBO_ALD_*` env var with its ladder and its ruling in the comment beside it. |
| `wedge.py` | Round 1 model: five skeletons (f j o r d), the first pen, the first 20 options (`OPTIONS`). Historical; `alphabet2.py` supersedes its drawing. |
| `alphabet.py` | Round 3/4: the first full lowercase, fitting by the n, serifs on diagonals. Superseded by `alphabet2.py`. |
| `alphabet2.py` | **The drawing model in use.** Continuous thick-thin pen, tapered joins, bracketed wedges, pen-angle cuts, overshoot, one spline for the s, capital H, fitting rules, knobs (`serif_style`, `arch_start`, `fillet`, `power`, `naive_o`, `raw_joins`, `overshoot`, `n_width`, `fit`). `layout(p, text)` → polygons + advance; `wrap(p, text, units)`. |
| `round2.py` … `round10.py` | One script per round; each builds that round's page. `round5.MATCHED` (cut 3 at S-tier medians), `round7.POP` (24 by family), `round9.population()` (40 humanist), `round10.steps()` (B5 → garalde; `steps()[-1][2]` is **B5.9, the current design**). |
| `round11.py` | Pen models (translation nib, brush, pointed, constant, rotating, ribbon, gravity, low-poly, speed) and raster impression models. **The raster models are withdrawn as deliverables**; the pen models are reused by the font builders. |
| `round12.py` | **The font builder.** `build(v, out_dir)` writes one TrueType per technique dict; `BANK` has the 26 of round 12; `quadify`, `Multi`, `orient`, `chaikin`, `decimate`, `jitter`, `stencil`, `offset_naive`. |
| `round13.py` | Refinements of the three kept techniques (V23 Scissors, V15 Rotating nib, V19 Gravity), six each. |
| `round14.py` | V23a cut six times with independent randomness per font and per glyph (`Cut`, `hand`). The pattern for any "no identical defects" ask. |
| `round15.py` | Seed 73, clean: `CleanCut` (serifs never decimated, joins re-closed by growing, slivers dropped) and `GARAMOND` widths. |
| `round16.py` | Hairline-throughs cured six ways on c5 with quads (`pen_centerline_cut`, `SerifsOnly`). Superseded by round 17: the owner wanted the straight-cut look back. The e's bar overlap and the optional s spine (`s_spine`, `s_two`, `e_join_fill`) live in `alphabet2.py`. |
| `latin.py` | A–Z, 0–9, punctuation on the same pen: `capH` (1.625 xh), `_cstem` (cap stems with the wedge family; `top=` left/right/right+/left+), `bar(align=)`, `diag(taper0, taper1)`, `kick` (legs as the A's), `_bowl_ring` (the D's ring for D B P R), `_beak` (C G S), `_ramp`, `cp_ring`, `FIG_BOX`, `W` (solved widths); the & and @ are real glyphs. |
| `cmp_garamond.py`, `cmp_vdk.py` | Every glyph beside and over EB Garamond 400 / Van den Keere at matched x-height, deltas flagged. |
| `overlay_stier.py`, `fig_overlay.py` | Every glyph over the nine humanist S-tier faces; the figures over their old-style sets. |
| `word_weight.py` | Ink darkness per word and per letter at 54 px against two references, plus outline area. |
| `outlines/cmp/balance.py` | IN-WORD balance: each letter's darkness inside the 147 common words through the four-level pipeline at 13 pt -- the x-height band's ink and the darkest 6 px knot -- relative to the lowercase mean and divided by a reference face's same figure (`--ref`, `--ref2`: Albertus, EB Garamond). Round 88's instrument; `word_weight.py` averages a letter over its whole box and called the y ordinary. |
| `e_dials_page.py` | The e drawn through the builder for a grid of bar angle / thickness / height / arm length, as an interactive page. |
| `round19.py` | The first full-set builder (glyph order, cmap, specimen page). |
| `outlines/` | **The builder in use since round 54 (2026-09-13)**: the rebuild as designed outlines -- `geom.py` (shapely unions), `pen.py` (the pen as reference), `primitives.py`, `cut.py`, `build.py` (`python3 -m outlines.build <out_dir>` from this directory), `glyphs/` by family, `cmp/`, and `NOTES.md` with every decision. Since round 58 (2026-09-13) it writes `Albo-Medium.ttf` (the 500; round 83) + `albo-specimen.html` (family renamed Albo); bowl profile switch `primitives.set_bowl` (`DEFAULT_BOWL = 'B'`, the ruling; `'pen'` = the nib); env overrides `FJORD_STEM` `FJORD_CONTRAST` `FJORD_ASC` `FJORD_DESC` `FJORD_WIDTH` `FJORD_XH` `FJORD_SERIF` `FJORD_ARCH_FLOOR` parameterize a build (ladders and the VF's masters). |
| `cmp_capwidths.py` | Albo's capitals against Trajan, the humanist median (Coelacanth, Libris ADF, Dante, Van den Keere, Doves) and Helvetica, as advance over each face's own H-ink cap height. Writes the table in `docs/albo-capital-widths.md`. The measure that separates the three systems is ROUND-to-SQUARE, not overall width. Trajan Pro is Adobe-licensed: `~/src/crosspoint-reader/lib/EpdFont/local_fonts/`, gitignored. |
| `cmp_cap_weight.py` | **Is an italic capital the weight of its own roman?** Builds both fonts and measures each capital as 2 x AREA / OUTLINE LENGTH -- the mean width of the ink, off the outline, no raster and no threshold. Targets are PER LETTER: each re-cut italic capital is driven to the ratio its roman carries against the untouched capitals, so the A's target is 0.89 and not 1.00. Exits non-zero past `--tol` (default 0.05). Round 131c; the median-of-runs and 30th-percentile metrics it replaced disagreed with each other by 2.5x on the same letter. |
| `aldine_proof.py` | **The owner's proof page, in one command.** `python3 aldine_proof.py <Albo-Italic.ttf> <out_dir> [--text FILE]` writes `para27.png` / `para40.png` -- two paragraphs of running English in two registers (Austen, Darwin; `--text` replaces them, blank-line separated), each set in the candidate and in Flanker Griffo Italic at 1:1 on one measure -- plus `lc_a..z.png` / `uc_A..Z.png`, each letter as the hand-located scan crop from `aldine_autofit.SOURCES` beside Albo, Flanker Griffo, Pagella, Poetica and Cancelleresca at one x-height (capitals at one cap height), and the `index.html` that carries them, written beside the images. It replaces the throwaway scripts each pass was re-rolling, which is where a standing rule gets dropped: PNG at native pixels, nothing resampled after drawing but the scan crop (its factor rides in its label), no fixed width or height on any image in the CSS, and ASCII-only in PIL labels -- the default font draws an en-dash as a tofu box, and one shipped that way. |
| `cmp_aldine_metrics.py` | **The Aldine ledger**: every lowercase letter's measured target (line width, counter/ink, w/h) against what the build produces, with the source of each target named. A GATE -- non-zero past 10%. `python3 cmp_aldine_metrics.py [--only ae]`; it builds the italic itself, at the env quoted under "How to run". A script and not a table in a doc because the numbers drift the moment a shared dial moves and prose does not notice -- contrast arm D moved the o from 0.624 to 0.823 against a 0.617 target and nothing said so for a round. |
| `cmp_aldine_glitch.py` | **The glitch gate**: every glyph's outline swept for the union artifacts this font has ACTUALLY shipped -- detached ink islands, pinched counters, notches -- not for anything a designer might dislike. Every defect in its list was found by eye at 500 px after it had shipped and is invisible at reading size, which is the shape of mistake a comment cannot prevent. It caught the g's detached ear in round 175 when no proof image at reading size did. |
| `cmp_aldine_straight.py` | Every PERFECTLY STRAIGHT edge in the italic, with its run length, so a hand-cutting pass has a list instead of an impression (`--tol` 1.5 units, `--min` 0.30 x-heights). **A report, not a gate: it returns 0 whatever it finds** -- pen cuts, serif blades and the E/T/Z/f bars are straight by construction and are reported for a human to rule on. |
| `cmp_aldine_g.py` | **The binocular g's anatomy, measured on a RASTER** (round 176) -- so a font and a photograph of a printed page answer the same questions. Both counters (the two largest enclosed white regions), the crown and foot, the neck's ink at the waist, the ear's reach, depth and slope, all at a fixed x-height in Albo units. `PYTHON_GIL=0 python3 cmp_aldine_g.py` measures every reference plus Albo; `--ttf X.ttf` one font, `--png out.png` a contact sheet, `--xh` the raster's x-height (900). A REPORT, not a gate. Its table and the two negative results are `docs/albo-g-anatomy.md`. |
| `cmp_cap_space.py` | **Minimum WHITE between two capitals, in em** (round 177), on the SHAPED pair -- the second glyph is placed at `getlength(a+b) - getlength(b)`, so the GPOS kern table is in every number. Albo against Flanker Griffo and Pagella over 25 named pairs plus a 9-pair CONTROL block, because Albo's capitals run a uniform +0.045 em looser than Flanker and the fault is distance from THAT. `PYTHON_GIL=0 python3 cmp_cap_space.py <built>/Albo-Italic.ttf`, from this directory (the reference paths are relative). A report, not a gate. Its first cut placed the second glyph at the UNKERNED advance and called two touching pairs merely tight -- `docs/albo-capital-spacing.md`. |
| `cmp_touch.py` | **THE TOUCHING GATE** (round 178): all 5,193 pairs swept for letters whose ink meets. Each GLYPH is rendered once and reduced to a right-edge and a left-edge profile per scanline, so a pair's white is arithmetic rather than a second render; the advance is the shaped one, so the kern table is in it. **Exits non-zero** on any pair below `--floor` (0.012 em, about a third of this face's thinnest hairline) that is not in `EXEMPT` -- four f+ascender pairs, each with its reason. `PYTHON_GIL=0 python3 cmp_touch.py <built>/Albo-Italic.ttf [--floor 0.02 --top 40]`. |
| `proof.py` | **One renderer for every Albo proof image** (2026-09-16), so two proofs can be compared. It takes NO top coordinate: a row is a BASELINE and a size (`pr.row(text, px, rules=True)`), the image is grown to hold the deepest ACTUAL descender of the text being set, and the rules are drawn from the same numbers the type is. A library, not a CLI -- `from proof import Proof`. PIL's `text((x,y))` anchors the ASCENT TOP and `anchor="ls"` the baseline; mixing the two is self-consistent per image and makes every comparison between images a lie. It also reports the fact that hid behind it: the declared descender is 280 units and the italic **y reaches 297**. |
| `outlines/cmp/space.py` | The space inside and between (owner's standing rule): counters and apertures at 54 px on the four-level render, the o's counter against 1.036, bearings and word space; its section is appended to the proof page. |
| `outlines/variable.py` | **The variable font** (round 61): `python3 -m outlines.variable <out_dir>` builds 20 masters as env-parameterized subprocesses of `outlines.build`, compatibilizes them (contours matched by hole flag and centroid, start-aligned, sampled at the default's arc-length fractions; the cut projected onto the dense outline's chords), writes `Albo.designspace` and `Albo-VF.ttf` (wght CNTR ASCN DESC wdth CUTS XHGT SRIF). Per-glyph clamps and the corner masters are in `NOTES.md` "Round 61". |
| `round20.py` | The generator-based builder (rounds 20–53), kept as the reference construction: `build(out_dir, over=)` writes `Fjord-Regular.ttf` with capitals and figures solved to `garalde_caps.json`, lowercase drawn at `lc_width`, bearings by the fitting rule (non-letters and the g on their full extent). Start here for any change to the shipping font. |
| `garalde_caps.json` | Medians of Dante, Van den Keere, Hoefler Text, Doves: cap height, cap stem, figure height, H counter and bearings, per-glyph widths and vertical extents, all over cap height. |
| `round17.py` | The construction the full font uses. `pen_linear` (unfold, then facet, both end faces kept), `ring` (outer cut, counter clean), `cp_glyphs` (o d b p q g e a as the font draws them; `G_VARIANTS` with the G3 g as 0, `E_VARIANTS` with the ruled e as 0), `patch_arch`, `Cut` (the post-op; rounds polygons under 20 vertices), `orient_with_holes`. `bite` remains as the record of what does not work. |

Outputs go to a directory you pass as argv[1] (the session scratchpad by
convention); `build/fjord-fonts/` holds the latest TTFs and zips locally and
is gitignored. Every round's page URL is in the exploration doc.

## How to run

The builder in use is `outlines.build`, run as a module FROM THIS DIRECTORY:

```bash
cd ~/src/crosspoint-simulator/tools/wedge_serif
python3 -m outlines.build /tmp/albo                       # Albo-Medium.ttf + the specimen
FJORD_STEM=66.9 FJORD_CONTRAST=0.892 \
  python3 -m outlines.build /tmp/albo --style Regular     # the shipping 400 (round 83)

# THE ALDINE ITALIC, which is NOT the default -- `_DEFAULT = "classic"` in
# glyphs/aldine.py, so a plain --style Italic still builds the round-101-114b
# branching-arch italic. This is the env every gate below builds with:
ALBO_ITALIC=aldine FJORD_STEM=66.9 FJORD_CONTRAST=0.80 FJORD_WIDTH=95 \
  FJORD_SLANT=13 PYTHON_GIL=0 python3 -m outlines.build /tmp/albo --style Italic

# THE BOLD PAIR (round 259, 2026-09-19). The weight axis is FJORD_STEM; the
# Medium is 84. The stem is NOT settled -- 107 is gate-clean and 116 is what
# the reference garalde bolds measure. See docs/albo-family-2026-09-19.md.
FJORD_STEM=116 FJORD_SLANT=0 FJORD_CONTRAST=0.80 FJORD_WIDTH=95 FJORD_CUT=0 \
  PYTHON_GIL=0 python3 -m outlines.build /tmp/albo --style Bold
ALBO_ITALIC=aldine FJORD_STEM=116 FJORD_SLANT=13 FJORD_CONTRAST=0.80 \
  FJORD_WIDTH=95 FJORD_CUT=0 PYTHON_GIL=0 python3 -m outlines.build /tmp/albo --style BoldItalic
```

The historical per-round scripts still run, from the repo root:

```bash
cd ~/src/crosspoint-simulator
python3 tools/wedge_serif/round13.py /tmp/fjord   # 18 TTFs + page + zip
python3 tools/wedge_serif/round12.py /tmp/fjord   # the 26 technique TTFs
python3 tools/wedge_serif/round9.py  /tmp/fjord   # the 40-variant page + sheet
```

## The gates

Five scripts here exit non-zero on a finding; they are what a round reports
against. **Run them from this directory**, and note which of the neighbouring
instruments are NOT gates -- `cmp_aldine_straight.py` returns 0 whatever it finds, and so do
`cmp_aldine_g.py`, `cmp_cap_space.py` and `cmp_italic_caps.py`.

| gate | what it refuses | green at round 179 |
|---|---|---|
| `cmp_touch.py <ttf>` | a pair whose ink touches, or whose white is under `--floor` (0.012 em) | 0 of 5,193 pairs |
| `cmp_aldine_metrics.py` | a letter more than 10% off its own measured target (`--only abc` to narrow) | 0 out |
| `cmp_cap_weight.py --tol 0.05` | an italic capital that is not the weight of its own roman; the Y is exempt BY NAME (round 163) | 0 out |
| `cmp_aldine_glitch.py` | the union artifacts this font has actually shipped -- islands, pinches, notches. `--census` for calibration, `--ttf` for the post-cut file | 0 of 119 |
| `python3 -m outlines.cmp.corpus <ttf>` | a codepoint the owner's 34 epubs use and the cmap lacks | run before claiming coverage |

`cmp_aldine_glitch.py --all` also sweeps the punctuation, symbols and
dingbats and is **NOT** green; its ten findings are listed in the script's own
header, each looked at and none fixed, so the next pass does not re-find them.

Needs Pillow, numpy, fontTools (all present on the dev box; Python 3.14t).
`skia-pathops` does NOT build on this Python, so there are no outline
booleans; see "Limits".

## How a font is made (round20.build; round12.build is the older per-technique builder)

1. `alphabet2` draws each glyph as stroked polygons from the design params
   (`p`), with the technique's pen swapped in for `A.outline` and its
   outline post-op applied.
2. Contours are wound the same way (`orient`) so overlaps union under
   TrueType's nonzero rule. Pens whose outline can cross itself (brush,
   pointed, rotating, ribbon, gravity, speed) are `quadify`'d: one quad per
   centerline segment, each spanning two segments so neighbors overlap.
3. Advances come from the fitting rule: bearings by side type in the
   x-height band, `fit` 0.8; word space 1.7 n-counters.
4. fontTools `FontBuilder`: 1000 upm, hhea 900/−300, OS/2 x-height and cap
   height from the params, family name `Fjord <key> <title>`.
5. Every file is re-opened with `TTFont` and rendered through FreeType (PIL)
   before it ships.

## Limits, and the traps already paid for

- **No boolean operations.** Counterpunch is an approximation; the naive
  o's seam fills solid in a font (nonzero); stencil bridges are geometric
  clips (Sutherland–Hodgman), fine.
- **Abutting contours seam in FreeType** even with exactly shared edges
  (antialiasing conflation). Overlap them. Checked in the glyf table.
- **A self-crossing outline cancels under nonzero** and leaves slits, and
  the default pen crosses itself too once a cut jitters a tight curve (the
  "hairline-throughs" of round 16). Quadify, or cut the centerline instead of
  the ink (`round16.pen_centerline_cut`).
- **Booleans by clipping do not work under nonzero + holes.** Overlapping clip pieces wind twice and defeat a counter; partitioned pieces abut and seam. Cut traps into the counter contour and the stem polygon instead (`round17.bowl_stem`).
- **A cubic between two stems with its controls on the baseline never reaches the baseline** (the U and u floated 63 and 40 units). Put the controls below by ~0.55 of the start height.
- **A stem that ends exactly where its curve begins seams** (the j/f fractures). Overlap by half a stem.
- **A hole in TrueType is a contour wound the other way**, and it must lie entirely inside ink: a reverse-wound shape that pokes into paper renders FILLED (winding −1), so ink traps cannot be cut with paper polygons; they are made by the strokes' own geometry (`patch_arch`).
- **Editing any capital re-cuts every lowercase glyph after it.** `pen_linear`'s decimation phase is one counter across all strokes in CHARS order (A–Z first); a raster weight reading moves ±3% with no lowercase change. Compare outline areas, or builds with the same capitals.
- **`round20.build(over=...)`** takes design overrides; `arch_over_edge` (units past the x-height) is the arches' own overshoot knob, default the rounds'.
- **`cmp_garamond.py`** — every Fjord glyph beside and over EB Garamond 400 at matched x-height, flags width/height/stroke/position deltas; needs the reference TTF at `ref/` (fetch line in `docs/wedge-serif-exploration.md`, round 24).
- **`round17.cp_glyphs` overrides o d b p q g e a in the font.** A change to one of those in `alphabet2.py` never reaches `Fjord-Regular.ttf` (the looptail g was drawn twice for this reason). Edit the override.
- **Never replace a function by slicing to the next `def`** without checking
  what sits between; it ate the capital H once.
- **SUPERSEDED, round 19's state** -- coverage was A–Z a–z 0–9 and 30 punctuation marks, no accents, one style, no kerning. Accents (`glyphs/accents.py`, round 99), the symbol set (`glyphs/symbols.py` / `symbols2.py`, round 99), the ligatures (`glyphs/ligatures.py`, round 96) and class kerning (`outlines/kern.py`, round 95) have all landed since, and `outlines/cmp/corpus.py` is the live answer to what is missing. Five styles are installed on the reader.
- **The e is 9% narrower than the o with the bar at 0.58**; do not draw it
  on the o's width again (round 9).
- **Small polygons must never be decimated** (a 14-vertex wedge cut to three is a spike); `CleanCut` guards at 20 vertices.
- **The n widens with the stem** (`n_width + 0.9·(stem − 110)`) or a bold
  closes its counters and, through the fitting rule, its letter space.

## Taking a font to the reader

**Done, 2026-09-14** (owner: "install it everywhere"), and this section used to
say "not done yet". Albo is the twelfth installed family and the first drawn
in-house: five styles in
`~/src/crosspoint-reader/lib/EpdFont/local_fonts/Albo/` (Regular, Italic,
SemiBold, Bold, BoldItalic), a `name: Albo` entry in
`lib/EpdFont/scripts/sd-fonts.yaml` on `intervals: reading` with the tier's
canonical size ramp, and `Albo` in that file's installed list. The route for
the next family is the same: copy the TTFs in, add the entry, run
`build-sd-fonts.py --only Albo` at 1x and `--scale 2`, validate with
`tools/validate_seed_fonts.py`.

**Ruling 2026-09-19 (owner, on the question "run the TestFlight font
refresh up to the validation gate?"): yes, refresh through validation, stop
before the deploy.** When rounds 274 (the bold italic's junctions) and 275
(the round finials) land: copy the four TTFs (Regular, Italic, Bold,
BoldItalic at the re-anchored 400 and the corrected 700s) into
`lib/EpdFont/local_fonts/Albo/`, delete `Albo-SemiBold.ttf` (the 500 is
retired), correct the recipe's comment block, `build-sd-fonts.py --only Albo`
at 1x and `--scale 2` into `~/src/crosspoint-reader/fs_/fonts`, run
`tools/validate_seed_fonts.py`, and hand over the deploy command plus a 1x
contact sheet of the reader's own raster (the 400's weight is judged there).
The deploy itself is the owner's: it needs his GUI Terminal for codesign.
The full checklist is section 14 of `docs/albo-family-2026-09-19.md`.

**Queued 2026-09-19 (owner, on the cent page: "that italic has round
finials that needs to replaced along with others"):** the ITALIC's round
finials go the way of the roman's (round 275, `docs/albo-finials-2026-09-19.md`)
-- the italic c's top (its beak's ball), the r's ball, and every other ball or
teardrop end in `aldine.py` -- as round 276, after rounds 274 and 275 land,
reusing the roman round's helper. The c's top as drawn (`ALBO_ROM_C_TOP` a)
is the model, per the owner's "a works".

**Ruling 2026-09-19 (owner, on the cent page): the cent's bar is centered on
the c's counter at every weight**, the 400s included -- `symbols._currency_bar(counter=True)`
ungated (round 276).

**Ruling 2026-09-19 (owner, on the bold-serifs ladder: "b wins"): the wedge
serif is the 400's at every weight above the 400** -- length 52.3, depth 104.6,
drop 17.2, the numbers `pen.WL / WD / DROP` give at stem 66.9 -- instead of
scaling with the stem (1.73x at the 700, 2.2x at the 900). Both styles, since
the italic's wedges take the same three numbers. Lands as round 277, applied
in `pen.py` once round 274 (the bold italic's junctions) releases the tree;
the 200 keeps its stem-scaled wedge (not asked).

**Ruling 2026-09-19 (owner): round 274's junction rebuild -- the head on the
stem, the arch's landing, the exit at the foot, the u's left stem top, the
dotless i as the i without its dot -- applies to the ITALIC 400 as well as
the 700** ("Yes, both weights"). The `S > 84` gates on that code in
`aldine.py` come off as round 278, after round 276 (the italic's finials)
releases the file; the Italic 400 moves in about 40 glyphs (a h i l m n r u
dotless-i and their composites), measured and proofed as round 274 was.

**Ruling 2026-09-19 (owner): round 275's re-fitted advances stand** ("Keep
the new fit") -- the a's advance 519 -> 510 at the 700 and 558 -> 545 at the
900, the J, r, 3 and 5 by 1-4 units, because the teardrop point the fitter had
measured to is gone. No bearing delta.

**Ruling 2026-09-19 (owner, on the light-serif ladder: "b wins"): the
ExtraLight 200's wedge is 0.75 of the 400's** -- 39.2 long, 78.4 deep, drop
12.9 -- instead of scaling with its stem (34 x 68). `pen.py`, round 279.

**Ruling 2026-09-19 (owner, on the black-serif ladder: "a wins"): the Black
900 keeps the 400's wedge** (52 x 105, round 277's rule) -- laddered against
1.15, 1.30, the square root (1.49) and 1.75, and confirmed as it stands. Nothing
moved.

**WITHDRAWN 2026-09-19 (owner): the roman Q is NOT kerned against , ; and .**
Round 280 added +430 / +456 to those three pairs at the 700 / 900 on a question
framed as "kern the Q against the punctuation, or leave it"; the owner, on
seeing the result: *"lose the Q punctuation kerning. you misunderstood the need
entirely."* Reverted the same day (the kern table carries no Q pair; the tail
itself was never changed and stays long under round 225). The need behind the
Q-and-punctuation item is OPEN and is not "space them apart"; do not re-propose
a kern for it.

**Those installed files predate the Aldine italic.** They were written
2026-09-14 18:10; rounds 114-179 ran on 2026-09-15 and -16, and the italic
lowercase they drew is reached only by `ALBO_ITALIC=aldine`, which is not the
build default. So the `Albo-Italic.ttf` on the reader is the classic
branching-arch italic, and nothing from rounds 114-179 has been installed.

## Reference faces (scratchpad `wedge/ref/`, measured in `docs/fjord-glyph-guide.md` §000)

`Albertus-Medium.ttf` (the stroke target; `-sxh.ttf` is the same file with `OS/2.sxHeight` added so `outlines/cmp/proof.block` can rule it), `ITCBerkeley-{Medium,Bold,MediumItalic,BoldItalic}.otf`, `Berkeley-Oldstyle-Bold.ttf`, `miju-goudy/` (clone of aperezdc/miju-goudy: `font/MijuGoudy-*.ttf`, `sukhumala/`), `cheltenham-classic/` (clone of vetrivelcsamy/cheltenham-classic: `docs/font-files/CheltenhamClassic*.ttf`), `EBGaramond-400.ttf`. Van den Keere, Dante, Doves, Edgar live in the firmware repo's `lib/EpdFont/local_fonts/`. The scratchpad is session-local: re-copy from `~/.claude/uploads/` or re-clone if it is gone.

## The reference italics

`refs_registry.py` is the one list of them, and it exists for a single trap:
**a font's declared italic angle is not its slant, and two of the five declare
zero.** Every instrument here unshears a reference by its angle before comparing
it with Albo, so trusting `post.italicAngle` measures those two faces *sheared*
and produces plausible wrong numbers with no error.

| reference | true slant | what it is for |
|---|---|---|
| Flanker Griffo Italic | 11.7° (declares 12.0) | the primary reference — Griffo's own letter |
| **Coelacanth Italic** | **14.5° (declares 0)** | Centaur/Bruce Rogers lineage; the face `IT_SERIF` and the g's brush-stroke analysis were measured off. x-height 425/1000, the closest of any reference to Albo's 429 |
| Pagella Italic | 11.7° (declares 10.0) | proportion fallback where no scan crop exists |
| Poetica Std | 9.2° (declares 11.0) | the owner's preferred shape fallback |
| Cancelleresca Bastarda | **10.3° (declares 0)** | a chancery hand, 28 glyphs, lowercase only |

```bash
PYTHON_GIL=0 python3 refs_registry.py     # prints the table and re-measures it; non-zero on drift
```

It is a gate as well as a table: it re-measures every face and fails if one has
drifted, which is what happens when a file is replaced by a different cut under
the same name. **The slant is measured off `l` and only `l`** — a single bare
stem. The row-midpoint method spans two stems and an arch on `n`/`m` and a bowl
on `b`/`d`/`h`/`k`; adding `n` and `m` to the median flipped Coelacanth from
+14.5 to −14.0 and Poetica from +9.2 to −10.7, which is how the error was
caught. A sign reversal is too large to be a slant and too plausible to ignore.
