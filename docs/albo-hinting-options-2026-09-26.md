# Albo hinting: measured before choosing (2026-09-26)

Owner ruling, 2026-09-26: *"Measure first"* on hinting. Background:
`docs/albo-e-legibility-2026-09-26.md` (commit `17f1c2b`). Albo ships with no
TrueType hinting bytecode, so FreeType's autohinter decides the grid fitting
of every glyph, and on one e outline it sealed the e's mouth at 8–9.75 ppem.
This doc measures what the device actually gets under three answers to "who
hints Albo", and records what was checked and found clean.

- **Fonts:** round 399, `tools/wedge_serif/bench/fonts-2026-09-26-r399/`
  (Regular md5 `9e05a3fc…`, Italic `b3b36062…`). Round 400's e fix was
  being applied in parallel and is NOT in these fonts, so the e>o failure is
  still present in them. Bold and BoldItalic were not measured.
- **Converter:** crosspoint-reader `lib/EpdFont/scripts` at `9b78f5d5c`
  (HEAD `7c1d151bc`), run from a scratch copy.
- **FreeType:** 2.13.2 (freetype-py's bundled build, the same version the
  converter's own Python gets). ttfautohint 1.8.4 (Homebrew; FreeType License
  or GPLv2; the output font carries no license obligation).
- **How sure:** everything here is [measured] unless tagged [inferred].
- **Code:** `tools/wedge_serif/hinting/` (listed at the foot).

## 1. Answer

**On the device nothing is broken, and no arm changes how well the text reads
at the sizes the reader draws.** Every arm reads 99.3–100% under Apple Vision
at every reader size, 1x and 2x, with zero e>o; the e's mouth is open in every
arm at every reader size (the smallest is 16.7 ppem). The e failure lives at
8–9.75 ppem, which only the Kept Legibility Index draws.

**What hinting does change on the device is WEIGHT and STEM REGULARITY, and it
trades one for the other:**

- **TODAY (autohinter, NORMAL target)** snaps the roman's vertical stems
  horizontally: the same stem is drawn 2–3 ways across `b d h i j k l m n p q
  r u` where every other arm draws it 6–7 ways. The price is weight: the roman
  renders **4–10% darker than its outline** at 1x (stem ink at 10 pt 1.72 px
  against 1.44 px unhinted, +19%), and its letters are unevenly darkened
  (per-letter colour sd 0.072 against 0.037–0.048). **Every judgment the owner
  has made of Albo's roman weight on a device was made on this emboldened
  rendering.**
- **TTFAUTOHINT** does NOT behave like the autohinter in this pipeline.
  FreeType 2.13's TrueType interpreter (v40) ignores horizontal
  instructions [inferred from the numbers: stems and colour match LIGHT, not
  TODAY], so its bytecode hints Albo **vertically only**: true colour
  (0.98–1.01 from 10 pt up), crisp x-height and baseline, unsnapped stems. At
  default settings it does **not** fix the e: gate FAIL 0.255, index e>o 130.
  Its `natural` stem mode passes (0.141, e>o 3) — a knife edge again, now in
  a tool setting rather than an outline.
- **LIGHT (the autohinter, vertical only)** gives nearly the same pixels as
  ttfautohint without a new tool: true colour, crisp flat edges, unsnapped
  stems, **and the e gate passes** (0.118; index e>o 6). For the italic it is
  **bit-identical to TODAY** at every size — the autohinter already hints
  Albo's italic vertically only.
- **NO HINTING** gives the truest colour (0.97–1.01) and the most even letters
  (sd 0.037), at the cost of grey x-height and baseline edges (round-letter
  edge crispness 0.67 against 0.87) and the gate (FAIL 0.267 at 8 ppem: the
  mouth band is about one pixel tall there, and unaligned it lands as two
  grey rows).

**Recommendation.** Do not adopt ttfautohint: under the FreeType that renders
Albo it buys nothing LIGHT does not, it did not fix the e by default, and it
adds a build tool and bytecode to every consumer. Keep **TODAY** until the
owner has looked, because the choice between TODAY and LIGHT is a visual one —
**regular stems at a darker weight, or the drawn weight with irregular stems**
— and the whole roman was tuned on the darker one. If LIGHT is chosen, it is a
per-family converter option (a `hint_target: light` key in `sd-fonts.yaml`
beside the existing `force_autohint`), roman only in effect, costing +0.3% of
cpfont bytes. The e itself is being fixed in the outline (round 400), which is
the right place: no hinting arm is a guarantee against the next knife edge.
This is an architectural choice for the owner, so it is presented, not taken.

## 2. How the converter hints today (file:line, firmware repo)

`lib/EpdFont/scripts/fontconvert_sdcard.py`:

- `:882` — `face.set_char_size(size << 6, size << 6, 150, 150)`: 150 DPI, so
  ppem = pt × 150 / 72. Albo's ramp (`sd-fonts.yaml:2269`, `sizes: [8, 10,
  12, 14, 16, 18]`) is **16.67, 20.83, 25.00, 29.17, 33.33, 37.50 ppem**.
- `:919` — `load_flags = freetype.FT_LOAD_RENDER` for a real (non-synthetic)
  style: default hinting, target NORMAL, antialiased 8-bit coverage. `:921`
  adds `FT_LOAD_FORCE_AUTOHINT` only when the family sets `force_autohint`
  (`build-sd-fonts.py:1247`); Albo does not. **With no fpgm/prep/instructions
  in the font, FreeType's default IS the autohinter** — the e trace measured
  default == `FORCE_AUTOHINT` bit for bit, and `sd-fonts.yaml:2246` says the
  same.
- **No gamma.** `:1193` keeps the top nibble of the 8-bit coverage and `:1212`
  cuts it to 2 bits: coverage ≥ 192 → 3, ≥ 128 → 2, ≥ 64 → 1, else 0.
- `:1244` — the advance is `linearHoriAdvance`, the UNHINTED advance, so
  hinting never moves a glyph; it only changes the glyph's own pixels. Every
  glyph is rendered once at an integer origin (no sub-pixel positioning).
- The 2x tier is the same converter at doubled point sizes
  (`build-sd-fonts.py:1042`, `s * scale`): 16..36 pt, 33.3..75 ppem. **Its 8 pt
  is pixel-identical to 1x 16 pt.**
- The metrics override (`apply_metrics_override`) rewrites hhea/OS2 only and
  moves no glyph pixel; it was skipped in the arms.

**Faithfulness of the harness:** `hinting/raster.py` reimplements that path;
`hinting/validate.py` imports the converter's own `rasterize_font_style` and
compares width, height, left, top, advance and the packed 2-bit bitmap:
**27,504 glyph renders (U+0020–007E, U+00A0–00FF; six arms; both styles; all
twelve reader sizes), 0 mismatches.** The NO HINTING and LIGHT arms went through
the real converter with one scratch patch: an env var OR'd into the PRIMARY
face's load flags only (fallback faces untouched).

## 3. The arms

| arm | font | converter load flags |
|---|---|---|
| TODAY | shipped TTF | `FT_LOAD_RENDER` (autohinter, NORMAL) |
| TTFAUTOHINT (qsq) | `ttfautohint -n` (defaults: gray stem mode quantized, `-x 14`, `-l 8 -r 50`, `-G 200`, `-D latn`, `-f none`) | `FT_LOAD_RENDER` (the bytecode) |
| TTFA natural / strong | same with `-a nnn` / `-a sss` | same |
| LIGHT | shipped TTF | `FT_LOAD_RENDER \| FT_LOAD_TARGET_LIGHT` |
| NO HINTING | shipped TTF | `FT_LOAD_RENDER \| FT_LOAD_NO_HINTING` |

`-x 0` (no x-height increase below 14 ppem) was built and not measured
further: it can only act below 14 ppem, under every reader size.

**How much of the face each arm touches** (`hinting/identity.py`, share of
U+0021–007E whose 2-bit bitmap is identical, Regular):

| pair | 9 px | 8 pt | 12 pt | 18 pt | 12 pt@2x | 18 pt@2x |
|---|---|---|---|---|---|---|
| TODAY = NO HINTING | 11% | 0% | 2% | 0% | 0% | 0% |
| TODAY = LIGHT | 34% | 29% | 24% | 16% | 18% | 18% |
| TODAY = TTFA | 29% | 15% | 12% | 3% | 3% | 2% |
| TTFA = LIGHT | 60% | 28% | 29% | 16% | 10% | 4% |
| TTFA qsq = nnn | 78% | 76% | 90% | 68% | 70% | 62% |

Italic: TODAY = LIGHT is **100% at every size**. Hinting touches essentially
every glyph at every size, 2x included; there is no size at which "hinting
does not matter" in bytes, only in reading.

## 4. Numbers

### 4a. Kept Legibility Index (v3.1, 9–26 px, 8-bit) and the e gate (8–12 ppem)

The index's own protocol and reduction (`etrace/kli_e.py`, run through
`hinting/kli_arms.py`, which sets the load-flag arms). The index calls a
difference under about one point a tie. Georgia reproduced the survey's
94.0 / 91.7 exactly, so the pipeline is the survey's.

| arm | roman grand | roman crowded | roman e>o Vision | roman e>o Tesseract | italic grand | italic e>o | e gate |
|---|---|---|---|---|---|---|---|
| TODAY | 88.0 | 60.4 | **136** | 17 | 86.4 | 6 | **FAIL** 0.243 |
| TTFA (qsq) | 88.0 | 54.5 | **130** | 31 | 86.7 | 7 | **FAIL** 0.255 |
| TTFA natural | 88.2 | 51.8 | 3 | 0 | — | — | ok 0.141 |
| TTFA strong | — | — | — | — | — | — | **FAIL** 0.263 |
| LIGHT | 88.6 | 57.0 | 6 | 0 | 86.4 | 6 | ok 0.118 |
| NO HINTING | 88.7 | 58.0 | 2 | 0 | 86.7 | 5 | **FAIL** 0.267 (8 ppem) |
| Georgia (ref) | 94.0 | 91.7 | 0 | 0 | | | |

- Every grand mean is within 0.7 of every other: a tie. `crowded` moves
  51.8–60.4, a spread the survey saw between runs of different fonts; single
  runs, treat as noise [inferred].
- The e>o collapse follows the e gate except for NO HINTING, which passes the
  index (2) and fails the gate. The gate was calibrated on hinted renders; at
  8 ppem the unhinted mouth is a sub-pixel band that the gate calls grey and
  Vision still reads. The gate is conservative here, not wrong.
- The italic's top confusions (a>e 77–82, u>w 67–76, n>x 52–64) are the same
  in every arm: they are the drawing, not the hinting.

### 4b. Apple Vision on the device's own pixels

`hinting/reader_read.py`: the index's word corpus, four seeded shuffles, set
from the converter's 2-bit glyphs at each real size, read by the index's
reader. Character accuracy, %:

| arm | 9 px | 1x worst | 1x mean | 2x worst | e>o at all reader sizes |
|---|---|---|---|---|---|
| TODAY R | 81.1 | 99.66 | 99.93 | 99.80 | 0 |
| TODAY I | 54.7 | 99.49 | 99.89 | 99.80 | 0 |
| TTFA R | 79.1 | 99.73 | 99.90 | 99.93 | 0 |
| TTFA I | 46.4 | 99.32 | 99.85 | 99.80 | 0 |
| LIGHT R | 69.7 | 99.73 | 99.92 | 99.93 | 0 |
| LIGHT I | 54.7 | 99.49 | 99.89 | 99.80 | 0 |
| NO HINTING R | 76.1 | 99.70 | 99.88 | 99.93 | 0 |
| NO HINTING I | 52.7 | 99.80 | 99.93 | 99.86 | 0 |

**At reader sizes the machine reader is at its ceiling in every arm** — the
remaining errors are one or two characters in ~3,000 (`f>t`, `l>!`, `G>C`).
It cannot rank the arms there; the owner's eye has to. At 9 px in four grey
levels TODAY reads best (81%), which is the one place the x-snapping helps a
reader measurably — and 9 px is not a reader size.

### 4c. Weight, stems, alignment — Regular, 1x (16.7–37.5 ppem)

`hinting/measure.py`. **Colour** = the 2-bit ink of a–z against the unhinted
8-bit area of the same glyphs at the same ppem (1.00 = the outline's own
weight; NO HINTING's ≈ 1.00 shows the 2-bit cut itself is unbiased). **Stem
shapes** = how many distinct level patterns the lowercase stem at mid
x-height is drawn with across 13 letters. **Crisp** = mean peak level of the
outermost row of x-height and baseline edges (1 = lands on a pixel edge).

| arm | colour 8/10/12/14/16/18 pt | per-letter colour sd | stem shapes | stem spread px | flat edge crisp | round edge crisp |
|---|---|---|---|---|---|---|
| TODAY | 1.08 1.06 1.07 1.04 1.10 1.10 | 0.072 | 2 2 2 3 3 2 | 0.33–1.33 | 1.00 | 0.87 |
| TTFA (qsq) | 1.06 0.98 0.99 1.01 1.00 1.00 | 0.048 | 3 6 6 6 6 7 | 0.33–1.67 | 1.00 | 0.85 |
| LIGHT | 1.06 0.97 0.99 1.01 1.00 1.01 | 0.043 | 3 6 6 6 6 7 | 0.33–2.00 | 0.95 | 0.87 |
| NO HINTING | 0.97 0.99 1.00 1.01 0.99 1.00 | 0.037 | 4 6 6 6 6 7 | 0.67–2.00 | 0.90 | 0.67 |

Mean stem ink, px (TODAY / LIGHT / NO HINTING): 8 pt 1.03 / 1.05 / 1.21,
10 pt 1.72 / 1.41 / 1.41, 12 pt 2.08 / 1.64 / 1.67, 16 pt 2.74 / 2.21 / 2.18,
18 pt 3.10 / 2.49 / 2.41. **TODAY's stems are 9–27% wider from 10 pt up** (14 pt the least).

2x tier (20–36 pt, 41.7–75 ppem), Regular colour: TODAY 1.09 1.07 1.04 0.99
1.00; LIGHT 1.04 0.99 1.01 1.01 0.99; NO HINTING 1.00 0.99 1.00 1.00 0.99. The
phone's small sizes are emboldened too; from 16 pt (66.7 ppem) up the arms
converge.

**Italic** (both tiers): TODAY = LIGHT, bit for bit; TTFA within 0.01 of
them; colour 0.94–1.03 in every arm; stems 6–10 shapes in every arm — the
autohinter does not x-snap this italic, so it has no regular stems to lose.

### 4d. Cost

`hinting/cost.sh`, the real converter, Albo Regular + Italic, `reading`
intervals, no fallback chain (the chain's glyphs are the same bytes in every
arm):

| arm | 1x .cpfont bytes | 2x .cpfont bytes | converter time 1x / 2x |
|---|---|---|---|
| TODAY | 544,019 | 1,626,277 | 0.8 s / 1.9 s |
| TTFA (qsq) | 544,147 (+0.02%) | 1,625,200 (−0.07%) | 0.8 s / 2.0 s |
| LIGHT | 545,603 (+0.3%) | 1,631,394 (+0.3%) | 0.8 s / 1.9 s |
| NO HINTING | 552,570 (+1.6%) | 1,637,465 (+0.7%) | 0.8 s / 1.4 s |

ttfautohint itself: 0.04 s per style; the TTF grows 116 → 143 KB (Regular)
and 115 → 140 KB (Italic), which ships only if the TTF does (the reader ships
the .cpfont). Cost does not separate the arms.

### 4e. What changes on each device

- **X3** draws the 1x .cpfont's bitmaps as they are; there is no runtime
  rasterizer and no runtime hinting. Whatever the converter's load flags decide
  IS the device's pixels.
- **Phone** draws the 2x tier: the same converter at doubled sizes, so the same
  decision, at 33–75 ppem, where the arms differ by 0–10% colour and not at all
  in reading.
- **TTFAUTOHINT** is the only arm that changes a FILE other consumers read:
  every FreeType consumer of the TTF (the Kept Legibility Index, the desktop
  specimens in `tools/wedge_serif`) would switch from the autohinter to the
  bytecode. LIGHT and NO HINTING change only the converter's call and leave the
  TTF and every other tool alone.

## 5. Checked and found CLEAN

- The roman e's mouth at every reader size, every arm, 1x and 2x, on both the 8-bit
  coverage and the 2-bit levels: `mouth_block` 0.00 throughout. The e failure
  does not reach the device in any arm.
- Baseline alignment of the flat-bottomed roman letters (`f h i l m n r t z`)
  at every reader size: one row, crisp, in TODAY, LIGHT, TTFA natural and NO
  HINTING; TTFA default and strong spread 0.33 px at 8 pt.
- Flat x-height tops (`r u z`): one row in TODAY and TTFA default/strong at
  every reader size; LIGHT spreads 0.33 px at three sizes, TTFA natural at two,
  NO HINTING at four (12 pt at 1x; 12, 16, 18 pt at 2x).
- Advances: identical in every arm (the converter uses the unhinted advance),
  so no arm changes line length, line breaks or the kern table.
- The harness against the converter: 0 of 27,504 renders differ (§2).
- The index pipeline against the survey: Georgia 94.0 / 91.7, identical.

## 6. Not checked

- Bold and BoldItalic (the reader's other two slots).
- The owner's eye. The proof page (below) is the instrument for it; nothing in
  §4 can rank TODAY against LIGHT at a reader size, because the machine reader
  is at its ceiling there.
- FreeType's v35 interpreter or `interpreter-version` properties (freetype-py
  does not expose the property; the converter runs the default, v40).
- ttfautohint control files (`-m`) or reference-font blue zones (`-R`).

## 7. Proof and code

Proof page: session scratchpad `hinting/proof/index.html` — the same English
paragraph, long words and an italic line at 9 px and every reader size, 1x and
2x, in TODAY / TTFAUTOHINT / LIGHT / NO HINTING, converter pixels at 1:1, and
4× nearest crops of *effervescence*, *minimum*, *benevolence* at 9 px, 8 pt,
10 pt and 8 pt@2x with the four arms stacked in one image. Regenerate with
`proof.py`.

`tools/wedge_serif/hinting/`:

- `raster.py` — the converter's rasterization, arm by arm.
- `validate.py` — `raster.py` against the converter's own function.
- `measure.py` — e mouth, stems, alignment, colour.
- `gate_sweep.py` — the e gate's 8–12 ppem sweep per arm.
- `identity.py` — which glyphs two arms draw identically.
- `kli_arms.py` — the index for a load-flag arm (wraps `etrace/kli_e.py`).
- `reader_read.py` — Vision on converter pixels at reader sizes.
- `compose.py` — sets text from converter glyphs (HarfBuzz layout).
- `cost.sh` — the converter's bytes and time per arm.
- `tables.py` — the tables above from the JSON results.
- `proof.py` — the proof page.
- `results/` — this run's outputs: `measure.json`, `gate.json`,
  `identity.txt`, `tables.md`, and the index and Vision summaries
  (`kli_summary.json`, `reader_summary.json`; raw reader text dropped).

Re-run order: build the ttfautohint fonts (`ttfautohint -n [-a nnn|sss]
Albo-<Style>.ttf ttfa-<mode>-<Style>.ttf`, the shipped TTF copied to
`today-<Style>.ttf`), copy the firmware's `lib/EpdFont/scripts` and apply the
two-line patch described in `validate.py`, then `validate.py`, `measure.py`,
`gate_sweep.py`, `kli_arms.py` (three processes: flags 0, 0x2, 0x10000),
`reader_read.py`, `cost.sh`, `tables.py`, `proof.py`. Python needs numpy,
freetype-py, uharfbuzz, Pillow, fontTools; the index needs its Swift reader
built (`swiftc -O -o ocr/visionocr ocr/visionocr.swift`) and `KLI_DIR`.
