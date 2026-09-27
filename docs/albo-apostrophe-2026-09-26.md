# Albo: the apostrophe against the word image, as options (2026-09-26)

Owner, 2026-09-26: *"reduce apostrophe to match rest of word image"*.

**Status: OPTIONS. Nothing in the shipped font changes.** Every lever is an env
dial whose default (1.0) draws today's mark. With every dial unset, all four
cuts are **outline- and advance-identical** to HEAD `bdfd477` (round 402):
`cmp_outlines.py --advances` reports "0 of 530 shared glyph outlines differ,
IDENTICAL" on Regular, Italic, Bold and BoldItalic. `gates.sh`: GATES UNCHANGED.

- Code: `outlines/glyphs/marks.py` (the `APOS_*` block after `QUOTE_BODY`,
  `quote()`, `g_quotesingle`, `g_quotedbl`, and two optional overrides on
  `comma_tail`). No other file in `outlines/` was touched. `spacing_b2.json` and
  `kern.py` were not edited.
- Instruments: `tools/wedge_serif/instruments/apos_measure.py` (the tables
  below) and `instruments/apos_slider_frames.py` (the slider page).
- Slider page (scratch, not published):
  `/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/c03d2901-2d80-4074-84f8-7539dfb0f2e2/scratchpad/apos/index.html`,
  with 43 frames in `frames/` (6.8 MB).

## 1. Which glyph carries the apostrophe in his books

This was counted in the 41 epubs under `~/src/claude-tools/*/epub` (the
`outlines.cmp.corpus` set), with the tags stripped and the entities decoded.
The count is apostrophes that sit between two letters:

| codepoint | count | books |
|---|---|---|
| U+2019 `’` (quoteright) | **6,174** | 35 of the 38 books that contain any. It is the only form in WBN, ai, poly-Essentials and spanish-Essentials |
| U+0027 `'` (quotesingle) | 3,509 | 2,529 of these are the **Eighth Atlas** (843 in each of its three copies, all straight). The rest are trivia (231–373) and a few in the poly and spanish full editions |
| U+02BC `ʼ` | 0 | — |

So `’` carries the word image in almost every book, but not in all of them.
**The Eighth Atlas sets every apostrophe as `'`.** Both glyphs therefore get
dials. (`pair_census.py` folds `’` to `'`, so its pair counts cannot show this
split.)

## 2. Measured first (unhinted FreeType, 1000 ppem; `apos_measure.py`)

Each measure is divided by that font's own x-height (from its `x`) or by its own
lowercase stem (the `l` at half the x-height). This compares the references at
Albo's x-height without rescaling anything. Heights, horizontal runs and ink
areas do not change under a horizontal shear, so the italics are not unsheared.

**Roman.** References: Palatino, Charter, Georgia, Baskerville, Times, Pagella.

| | ’ height /xh | ’ foot /xh | ’ head /stem | ’ ink / n | ' ink / n | ' head /stem | stem /xh |
|---|---|---|---|---|---|---|---|
| **Albo Regular** | 0.554 | **0.871** | **1.859** | **0.204** | **0.252** | **1.375** | 0.135 |
| reference median | 0.560 | 0.946 | 1.545 | 0.185 | 0.165 | 1.141 | 0.176 |
| reference range | 0.548–0.640 | 0.917–1.015 | 1.226–1.790 | 0.173–0.207 | 0.132–0.262 | 1.000–1.400 | 0.173–0.189 |

**Italic.** References: Palatino It, Charter It, Georgia It, Flanker Griffo It,
Pagella It, Poetica.

| | ’ height /xh | ’ foot /xh | ’ head /stem | ’ ink / n | ' ink / n | ' head /stem | stem /xh |
|---|---|---|---|---|---|---|---|
| **Albo Italic** | 0.497 | **0.834** | **1.847** | **0.202** | **0.327** | **1.424** | 0.126 |
| reference median | 0.521 | 0.977 | 1.392 | 0.182 | 0.176 | 1.182 | 0.150 |
| reference range | 0.492–0.549 | 0.893–1.178 | 1.306–1.776 | 0.169–0.211 | 0.159–0.192 | 1.091–1.324 | 0.134–0.182 |

What the tables say:

- **The curly `’` is not too tall.** Its height sits at the reference median in
  the roman and 5% under it in the italic. Round 375 put it there, and that
  still holds.
- **It is too heavy for its own letters.**
  - Its head is 1.86 of Albo's stem. The references' median is 1.55 (roman)
    and 1.39 (italic).
  - Albo's head is above the whole italic range and at the top of the roman
    range.
  - The cause is the stem, not the dot. Albo's stem is thin for its x-height:
    0.135 against a reference median of 0.176. Round 369 sized the marks' dots
    per x-height, so a dot the right size for the x-height is heavy for this
    stem.
  - Its ink is +10% of an `n` over the reference median in both styles.
- **It reaches further down into the x-height band.** Its foot is at 0.87 of
  the x-height (italic 0.83). The references' median is 0.95 (italic 0.98).
  - In the italic, part of this is round 222's ruled QUOTE_DROP (50 units, "so
    the mark nests").
- **The straight `'` is the most out of line.**
  - Its ink is 0.25 of an `n` (italic 0.33), against a median of 0.165
    (italic 0.176). That is +53% and +86%.
  - Its head is 1.38 of the stem (italic 1.42), against a median of 1.14
    (italic 1.18).
  - It is not too tall in the roman (0.526 against 0.589). The weight comes
    from width.
- **The comma** is 0.617 of the x-height against 0.589: in band. No comma dial
  was needed, and the comma is untouched.

## 3. The dials

These are all in `marks.py`. Each one is 1.0 today, byte for byte. They move the
**single** marks only: `’ ‘ ʼ ʻ`, or `'` for the two straight dials.

- `‘` moves with `’` because it is the other half of the pair.
- `ALBO_APOS_DOUBLES=1` carries the same dials onto `“ ”` (and `"` for the
  straight dials). This is a **proposal** and is off by default, because the
  ask named the apostrophe.
  - The case for it: `”` is drawn as two `’`. Without it, a nested quote sets a
    heavy `”` beside a lighter `’`.

| env | what it moves | anchor |
|---|---|---|
| `ALBO_APOS_HEAD` | the curly mark's **dot** only | Its top stays on the line and the tail follows the dot's center, so the foot rises by what the radius loses |
| `ALBO_APOS_SCALE` | the whole curly mark | about its own top (the anchor `CURLY_SCALE` already uses) |
| `ALBO_APOS_TAIL` | the curly tail's reach and swing (the comma's L and W, for this mark only) | the dot is kept |
| `ALBO_APOS_TAIL_W` | the curly tail's width (the pen's 0.85→0.30 taper) | the dot is kept |
| `ALBO_APOS_STRAIGHT_W` | the straight `'`'s thickness | about its own axis; round 386's option c shape is kept |
| `ALBO_APOS_STRAIGHT` | the straight `'` as a whole | about its top |
| `ALBO_APOS_DOUBLES` | `1` = the doubles follow | — |

No dial changes a contour count, so the cut phase (`PHASE_LEGACY`,
`_option_phase_k`) is untouched.

## 4. Results per dial (Regular / Italic)

Each step was built in all four cuts and gated in all four. The gates were:

- `cmp_touch`;
- `cmp_contour_hairs --letters`, plus the full sweep diffed against shipped;
- `cmp_counter_dents`;
- `cmp_aldine_glitch --all`, diffed against shipped;
- `approved.py`.

**Every step of every dial is green**, including the extreme ones.

| dial, step | ’ head /stem | ’ ink / n | ’ foot /xh | ’ height /xh | advance |
|---|---|---|---|---|---|
| shipped | 1.86 / 1.85 | 0.204 / 0.202 | 0.871 / 0.834 | 0.554 / 0.497 | 305 / 189 |
| HEAD 0.90 | 1.70 / 1.68 | 0.178 / 0.178 | 0.884 / 0.846 | 0.539 / 0.484 | 301 / 183 |
| **HEAD 0.85 (R)** | **1.61 / 1.56** | **0.167 / 0.168** | 0.890 / 0.851 | 0.533 / 0.482 | 298 / 180 |
| HEAD 0.80 | 1.56 / 1.47 | 0.156 / 0.157 | 0.896 / 0.857 | 0.524 / 0.475 | 295 / 177 |
| SCALE 0.90 | 1.69 / 1.68 | 0.166 / 0.165 | 0.926 / 0.883 | 0.499 / 0.448 | 291 / 172 |
| SCALE 0.85 | 1.59 / 1.58 | 0.149 / 0.147 | 0.953 / 0.908 | 0.474 / 0.422 | 283 / 164 |
| TAIL 0.80 | 1.86 / 1.90 | 0.188 / 0.184 | 0.953 / 0.908 | 0.471 / 0.418 | 288 / 166 |
| TAIL_W 0.70 | 1.89 / 1.90 | 0.191 / 0.187 | 0.871 / 0.836 | 0.550 / 0.490 | 306 / 187 |
| *reference median* | *1.54 / 1.39* | *0.185 / 0.182* | *0.946 / 0.977* | *0.560 / 0.521* | |

| straight dial, step | ' head /stem | ' ink / n | ' height /xh | advance |
|---|---|---|---|---|
| shipped | 1.38 / 1.42 | 0.252 / 0.327 | 0.526 / 0.531 | 247 / 166 |
| STRAIGHT_W 0.80 | 1.11 / 1.15 | 0.203 / 0.262 | same | 230 / 150 |
| **STRAIGHT_W 0.75 (R)** | **1.03 / 1.08** | **0.191 / 0.247** | same | 225 / 146 |
| STRAIGHT_W 0.70 | 0.97 / 1.02 | 0.178 / 0.231 | same | 221 / 142 |
| STRAIGHT 0.85 | 1.17 / 1.22 | 0.183 / 0.236 | 0.448 / 0.452 | 234 / 146 |
| *reference median* | *1.14 / 1.18* | *0.165 / 0.176* | *0.589 / 0.503* | |

What each dial does:

- **TAIL_W does almost nothing.** Ink moves −6% at 0.70, and the head ratio
  rises slightly, because the head is the widest run.
- **TAIL and SCALE shorten the mark below the references' height.** This is
  the one dimension that was already right, and it undoes round 375's median.
- **HEAD is the lever the measurement names.** It reduces the one thing that
  is out of band, weight against the stem, and costs 4% of height.

## 5. Recommendation

`{"ALBO_APOS_HEAD": "0.85", "ALBO_APOS_STRAIGHT_W": "0.75"}`, with the doubles
left unchanged, and the owner's call on `ALBO_APOS_DOUBLES`.

- **`’` HEAD 0.85.**
  - Head/stem goes to 1.61 roman (median 1.54) and 1.56 italic (median 1.39,
    range top 1.78).
  - Ink per `n` goes to 0.167 / 0.168, just under both reference ranges'
    floors (0.173 / 0.169).
  - The foot rises 0.02 of an x-height, and the height stays within 4%.
  - **HEAD 0.90** is the conservative rung: ink per `n` lands on the median
    (0.178), and head/stem is 1.70 / 1.68, still inside both ranges.
- **`'` STRAIGHT_W 0.75.**
  - Head/stem goes to 1.03 / 1.08. The roman is inside the range (1.00–1.40);
    the italic is just under its floor of 1.09.
  - Ink goes to 0.191 / 0.247. The italic straight stays heavier than every
    reference even so, because of its shape: a parallel stroke at full length
    (QUOTE_OPT a with sym c). A width dial cannot fix that without going under
    the references' head.
  - STRAIGHT (the uniform scale) is not recommended. The roman `'` is already
    shorter than the references.
- **Scope, proved:** under the recommended picks, `cmp_outlines.py` against
  shipped moves exactly `quoteleft quoteright quotesingle uni02BB uni02BC` in
  every cut. With `ALBO_APOS_DOUBLES=1` it moves those plus
  `quotedbl quotedblleft quotedblright`.
- **Gates:** `gates.sh` reads GATES UNCHANGED for the defaults, for the
  recommended picks, and for the picks with doubles. Those runs covered the
  approved glyphs, the bench check, the contour census (1,056), the e's mouth,
  touch and hairs.

## 6. Spacing: what B2 does with a smaller apostrophe

The fit (`build.fit`) takes every mark's bearings off its **full ink extent**
(`not ch.isalpha()` → `min/max` over all points), plus the flat mark bearing
and the round-221/222 italic quote offsets.

B2's own contribution to the quotes is one mark row:

| style | row |
|---|---|
| roman | `'` (−7, −2), applied to every quote through the `ROM_PUNCT_ADJ["'"]` fallback |
| italic | `'` (+7, −1) |

The rest is the bench-derived kern pairs in `kern.py`, which carry `quoteright`
and `quotesingle` together: `n' −23`, `r' −36`, `y'`, and others.

So when the ink shrinks, the **horizontal white at the extremes is held
exactly**. The advance shrinks by the ink width lost, and the kerns (absolute)
are untouched.

Measured on the judged pairs (horizontal white / 2-D closest approach, font
units), shipped → HEAD 0.85:

| pair | Regular | Italic |
|---|---|---|
| n’ | 80/166 → 80/170 | 80/121 → 80/122 |
| ’s | 75/207 → 75/207 | −80/169 → −81/167 |
| t’ | 68/129 → 68/129 | 71/74 → 71/73 |
| r’ | 64/64 → 64/64 | 25/33 → 25/29 |
| ’t | 91/154 → 91/160 | 13/123 → 12/121 |
| advance of ’ | 305 → 298 | 189 → 180 |

**HEAD moves no judged white by more than 6 units.** The 2-D approach changes
by the few units the rising foot opens. SCALE and TAIL open the 2-D white more
(r’ roman 64 → 74 at SCALE 0.85), because the foot leaves the x-height band.

STRAIGHT_W 0.75 keeps every horizontal white and moves the 2-D approach by −6
to −1.

The words set 7–9 units tighter per apostrophe, which is the advance change.
That is the intended "smaller mark in the same gap", not a spacing change. If
the other agent's refit re-judges these pairs, it will see the new mark, since
the bearings follow the ink.

## 7. Checked and found CLEAN

- The comma, period and colon, and the round-369 marks' dot: not touched. The
  comma measures in band (0.617 against a median of 0.589 x-height).
- The low quotes `‚ „`: they are the comma, and are untouched.
- The curly quotes' symmetry option (`ALBO_QUOTE_SYM_CURLY`, ruled "leave curly
  alone"): the dials compose with it, since the `s > 0` branch takes the same
  `_r`, tail and scale. No shape family changed. At defaults it is byte-identical.
- Bold and BoldItalic: the dials apply through the same code. Every gate is
  green at every step. The bolds were not measured against bold references.

## 8. Page, and how to re-run

- **The page.** Each dial has a slider across its full range, with S and R
  marked. Each step shows:
  - the paragraph at 27 px, shown 2× nearest (roman and italic);
  - the words at 54 px native;
  - a difference view at 27 px ×3 at shipped positions;
  - a 200 px close-up of "n’t", own spacing and overlaid on shipped;
  - its numbers against the reference median, the pair whites and the gate
    flags.

  A final section shows the recommended picks built together, with a toggle for
  the doubles. **Copy picks** emits `{env: value}`, where `null` means shipped.
- **Rendering.** The page renders unhinted (FT_LOAD_NO_HINTING, round 401) with
  HarfBuzz layout, 8-bit coverage.
- **To re-run:**

  ```
  ALBO_BUILD_PY=$(which python3) uv run --python 3.13 --with uharfbuzz --with freetype-py \
      --with shapely --with fonttools --with pillow --with numpy \
      python instruments/apos_slider_frames.py --work WORK --out OUT
  ```

  uharfbuzz's abi3 wheel does not load on the tree's free-threaded 3.14t, so
  the renderer runs under uv. The builds and gates run on the tree's own
  interpreter.

## 9. Owner picks

(awaiting)
