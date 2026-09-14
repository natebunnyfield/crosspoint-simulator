# wedge_serif — the Albo type exploration toolchain (Fjord until round 58, 2026-09-13)

A parametric humanist wedge-serif being designed for longform reading on the
CrossPoint X3 and its iOS port, by evolution: the owner is shown populations
of variants and marks keepers; each round narrows or diverges on his ruling.
The full dated log of rounds, rulings, measurements and negative results is
[`docs/wedge-serif-exploration.md`](../../docs/wedge-serif-exploration.md).
**Read its "State" section first.** This file is the map of the code. How to draw a glyph that belongs -- pen, serifs, proportions, rulings, the judging loop -- is [`docs/fjord-glyph-guide.md`](../../docs/fjord-glyph-guide.md).

## The owner's working rules (fifty-one rounds, 2026-09-12)

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
| the italic (round 100) | `pen.SLANT` shears the finished ink about the baseline; `pen.ITALIC` switches the letters a real italic redraws -- the single-storey a and the descending f, both in `glyphs/stems.py`. Build one with `FJORD_SLANT=11 FJORD_WIDTH=95 ... --style Italic`. |
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
| `outlines/cmp/space.py` | The space inside and between (owner's standing rule): counters and apertures at 54 px on the four-level render, the o's counter against 1.036, bearings and word space; its section is appended to the proof page. |
| `outlines/variable.py` | **The variable font** (round 61): `python3 -m outlines.variable <out_dir>` builds 20 masters as env-parameterized subprocesses of `outlines.build`, compatibilizes them (contours matched by hole flag and centroid, start-aligned, sampled at the default's arc-length fractions; the cut projected onto the dense outline's chords), writes `Albo.designspace` and `Albo-VF.ttf` (wght CNTR ASCN DESC wdth CUTS XHGT SRIF). Per-glyph clamps and the corner masters are in `NOTES.md` "Round 61". |
| `round20.py` | The generator-based builder (rounds 20–53), kept as the reference construction: `build(out_dir, over=)` writes `Fjord-Regular.ttf` with capitals and figures solved to `garalde_caps.json`, lowercase drawn at `lc_width`, bearings by the fitting rule (non-letters and the g on their full extent). Start here for any change to the shipping font. |
| `garalde_caps.json` | Medians of Dante, Van den Keere, Hoefler Text, Doves: cap height, cap stem, figure height, H counter and bearings, per-glyph widths and vertical extents, all over cap height. |
| `round17.py` | The construction the full font uses. `pen_linear` (unfold, then facet, both end faces kept), `ring` (outer cut, counter clean), `cp_glyphs` (o d b p q g e a as the font draws them; `G_VARIANTS` with the G3 g as 0, `E_VARIANTS` with the ruled e as 0), `patch_arch`, `Cut` (the post-op; rounds polygons under 20 vertices), `orient_with_holes`. `bite` remains as the record of what does not work. |

Outputs go to a directory you pass as argv[1] (the session scratchpad by
convention); `build/fjord-fonts/` holds the latest TTFs and zips locally and
is gitignored. Every round's page URL is in the exploration doc.

## How to run

```bash
cd ~/src/crosspoint-simulator
python3 tools/wedge_serif/round13.py /tmp/fjord   # 18 TTFs + page + zip
python3 tools/wedge_serif/round12.py /tmp/fjord   # the 26 technique TTFs
python3 tools/wedge_serif/round9.py  /tmp/fjord   # the 40-variant page + sheet
```

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
- **Coverage is A–Z a–z 0–9 and 30 punctuation marks** (round 19). No accents; the epub pipeline's `reading` interval wants Latin-1 and Extended-A. Only a regular exists; the reader's recipe expects four styles. No kerning.
- **The e is 9% narrower than the o with the bar at 0.58**; do not draw it
  on the o's width again (round 9).
- **Small polygons must never be decimated** (a 14-vertex wedge cut to three is a spike); `CleanCut` guards at 20 vertices.
- **The n widens with the stem** (`n_width + 0.9·(stem − 110)`) or a bold
  closes its counters and, through the fitting rule, its letter space.

## Taking a font to the reader

Not done yet. The route: copy the chosen TTF into
`~/src/crosspoint-reader/lib/EpdFont/local_fonts/Fjord/`, add a family to
`lib/EpdFont/scripts/sd-fonts.yaml` (see the AtkinsonHyperlegibleNext entry
for the shape; `metrics:` sets the line), run `build-sd-fonts.py --only
Fjord` at 1x and `--scale 2`, validate with `tools/validate_seed_fonts.py`,
then bundle as a trial family (`docs/trial-fonts.md`). Four styles are
expected; the bold can come from `round4.bold_of` on the design params, the
italics do not exist.

## Reference faces (scratchpad `wedge/ref/`, measured in `docs/fjord-glyph-guide.md` §000)

`Albertus-Medium.ttf` (the stroke target; `-sxh.ttf` is the same file with `OS/2.sxHeight` added so `outlines/cmp/proof.block` can rule it), `ITCBerkeley-{Medium,Bold,MediumItalic,BoldItalic}.otf`, `Berkeley-Oldstyle-Bold.ttf`, `miju-goudy/` (clone of aperezdc/miju-goudy: `font/MijuGoudy-*.ttf`, `sukhumala/`), `cheltenham-classic/` (clone of vetrivelcsamy/cheltenham-classic: `docs/font-files/CheltenhamClassic*.ttf`), `EBGaramond-400.ttf`. Van den Keere, Dante, Doves, Edgar live in the firmware repo's `lib/EpdFont/local_fonts/`. The scratchpad is session-local: re-copy from `~/.claude/uploads/` or re-clone if it is gone.
