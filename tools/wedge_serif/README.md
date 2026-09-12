# wedge_serif — the Fjord type exploration toolchain

A parametric humanist wedge-serif being designed for longform reading on the
CrossPoint X3 and its iOS port, by evolution: the owner is shown populations
of variants and marks keepers; each round narrows or diverges on his ruling.
The full dated log of rounds, rulings, measurements and negative results is
[`docs/wedge-serif-exploration.md`](../../docs/wedge-serif-exploration.md).
**Read its "State" section first.** This file is the map of the code.

## The owner's working rules (from thirteen rounds, 2026-09-12)

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

## Files

| File | What |
|---|---|
| `wedge.py` | Round 1 model: five skeletons (f j o r d), the first pen, the first 20 options (`OPTIONS`). Historical; `alphabet2.py` supersedes its drawing. |
| `alphabet.py` | Round 3/4: the first full lowercase, fitting by the n, serifs on diagonals. Superseded by `alphabet2.py`. |
| `alphabet2.py` | **The drawing model in use.** Continuous thick-thin pen, tapered joins, bracketed wedges, pen-angle cuts, overshoot, one spline for the s, capital H, fitting rules, knobs (`serif_style`, `arch_start`, `fillet`, `power`, `naive_o`, `raw_joins`, `overshoot`, `n_width`, `fit`). `layout(p, text)` → polygons + advance; `wrap(p, text, units)`. |
| `round2.py` … `round10.py` | One script per round; each builds that round's page. `round5.MATCHED` (cut 3 at S-tier medians), `round7.POP` (24 by family), `round9.population()` (40 humanist), `round10.steps()` (B5 → garalde; `steps()[-1][2]` is **B5.9, the current design**). |
| `round11.py` | Pen models (translation nib, brush, pointed, constant, rotating, ribbon, gravity, low-poly, speed) and raster impression models. **The raster models are withdrawn as deliverables**; the pen models are reused by the font builders. |
| `round12.py` | **The font builder.** `build(v, out_dir)` writes one TrueType per technique dict; `BANK` has the 26 of round 12; `quadify`, `Multi`, `orient`, `chaikin`, `decimate`, `jitter`, `stencil`, `offset_naive`. |
| `round13.py` | Refinements of the three kept techniques (V23 Scissors, V15 Rotating nib, V19 Gravity), six each. |
| `round14.py` | V23a cut six times with independent randomness per font and per glyph (`Cut`, `hand`). The pattern for any "no identical defects" ask. |

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

## How a font is made (round12.build)

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
- **A self-crossing outline cancels under nonzero** and leaves slits.
  Quadify.
- **Coverage is H, a–z, `. , -`, space.** No other capitals, digits,
  accents or punctuation yet; the epub pipeline's `reading` interval wants
  far more. Only a regular exists; the reader's recipe expects four styles.
- **The e is 9% narrower than the o with the bar at 0.58**; do not draw it
  on the o's width again (round 9).
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
