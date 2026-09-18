# Albo's weight, letter by letter — 2026-09-17

Owner, 2026-09-17: *"do a full survey of all roman and italic letters and
numerals"*, asked in the same breath as *"increase thickness of bottom loop
enough to match visual weight of other letters"*. This is that question asked of
all 124 glyphs at once: **is any letter lighter, heavier or flatter than the
face it belongs to?**

Re-run it with `tools/wedge_serif/cmp_weight_survey.py`, which is the ledger —
the numbers below are its output, not a transcription:

```bash
cd tools/wedge_serif
PYTHON_GIL=0 python3 cmp_weight_survey.py --roman <roman.ttf> --italic <italic.ttf> --tol 0.15
```

## What is measured, and the trap in measuring it

The glyph is rasterised UNSHEARED at a fixed x-height, a chamfer distance
transform is taken over the ink, and the ridge of that transform is the stroke's
centreline; local thickness is twice the distance there. This is the method
`cmp_g_strokes.py` established, including its one rule: **no percentile
threshold on the ridge**, because keeping only the thick samples deletes every
thin stroke from the sample and reports a face as far less contrasted than it is.

    thin      the 10th percentile of thickness along the centreline
    stroke    the median -- what the letter's weight reads as
    thick     the 90th percentile
    contrast  thick / thin, the letter's own cut
    colour    ink over (advance x reference height), IN THE READING BAND

**The first cut of `colour` was wrong and is worth recording.** It divided the
letter's whole ink by (advance × x-height), which reads an `f` at 0.77 and an
`l` at 0.57 against an `o`'s 0.39 — the ascender's ink counted against a box
that stops at the x-height. What sets a word's colour is the band the word is
read in, so the ink is now taken from the baseline up to the reference height
and nothing above or below it counts.

**And grouping by CASE flags shape families rather than faults.** A stem letter's
ridge is almost all stem, so its median IS the stem; a round letter's ridge
includes its thins, so its median sits lower by construction. Grouped by case,
53 of 124 glyphs came out "more than 15% off" — which measures the alphabet, not
the drawing. The tables below group by **construction family** instead, which is
the comparison that means something.

### Roman

| family | n | stroke | contrast | colour | more than 20% off its family |
|---|---|---|---|---|---|
| stem | 29 | 79.0 | 1.95 | 0.308 | — |
| round | 11 | 62.5 | 1.83 | 0.305 | `S`+34% |
| diag | 11 | 61.0 | 1.90 | 0.261 | `X`-38% `x`-26% `A`-22% `V`-22% `Y`+33% `z`+63% |
| figure | 10 | 70.4 | 2.06 | 0.215 | `7`-33% |

### Italic

| family | n | stroke | contrast | colour | more than 20% off its family |
|---|---|---|---|---|---|
| stem | 29 | 66.2 | 2.46 | 0.311 | `p`-24% `T`-22% `P`+22% `H`+23% `E`+30% |
| round | 11 | 53.4 | 2.88 | 0.271 | `e`-31% `O`+24% |
| diag | 11 | 42.1 | 2.81 | 0.260 | `z`-36% `X`-30% `y`-23% `Z`+34% `A`+39% `Y`+92% |
| figure | 10 | 60.6 | 2.82 | 0.214 | `7`-32% `1`+22% |
## The findings, ranked

### 1. The two z's are not the same letter's z

| | thin | stroke | thick | contrast |
|---|---|---|---|---|
| roman `z` | 72.3 | **99.3** | 103.9 | 1.44 |
| italic `z` | 24.1 | **27.1** | 67.7 | 2.81 |

The roman z is the **heaviest lowercase in the face** and very nearly monoline;
the italic z is **the lightest glyph in the face**, 73% lighter than its roman.
Set side by side at 300 px they do not read as one typeface's z, and at 16 px
`zigzag` shows it plainly: the roman z's are the darkest marks in the line and
the italic z's fall out of it.

It is not a bug in either drawing — it is the pen model behaving consistently.
The z's main stroke is a diagonal, and at the roman's nib angle that diagonal
runs across the nib (thick) while at the italic's it runs along it (thin). The
fault is that nothing arbitrates between them, and 27 units at a 429 x-height is
about one pixel at 16 px.

### 2. The italic runs 16% lighter than the roman, and unevenly

Median across the 62 letters: the italic's stroke is **−16%** against the
roman's. That much is ordinary — an italic is a lighter, quicker hand. The
spread is not: `z` −73%, `y` −47%, `w` −43%, `T` −43%, `4` −37%, `f` −36% at one
end, and `A` **+24%**, `N` +10%, `Z` +9% at the other. Two letters (`M`, `O`)
match exactly.

### 3. The italic's diagonals are its weak family

Family stroke medians, italic: stem 66.2, round 53.4, **diag 42.1**, figure
60.6. The diagonals are 36% under the stems and carry the widest spread in the
face (`Y` +92%, `A` +39%, `Z` +34% against `z` −36%, `X` −30%, `y` −23%). The
roman's diagonals are 23% under its stems with a tighter spread.

### 4. Two hairlines are at the edge of what survives printing

`X` italic: thin **15.1** units, contrast **6.75** — the most extreme cut in the
face. `s` roman: thin **16.6**, contrast 5.05. At a 16 px x-height those are
about 0.6 px. Everything else in the face sits between 20 and 90.

### 5. The `7` is the lightest figure in both styles, consistently

Colour 0.132 roman and 0.128 italic, against the next lightest at 0.20 and the
figure median at 0.215. Consistent across both styles, so it is the design
rather than a slip — but in a run of figures the 7 reads as a gap.

### 6. What the g's lower loop cost and bought (round 206)

The owner's instruction was *"increase thickness of bottom loop enough to match
visual weight of other letters"*. Measured before: the loop's stroke ran **36.8**
units against the round letters' median of **46.7** (o 53.4, a 49.7, c 46.7,
s 45.2, e 36.9) — the lightest thing in the face. `G_LOOP_PEN` 64 → **84** puts
it at **48.9**, inside that band.

**Two measures disagreed about this letter and both are true.** By stroke
thickness the loop was the lightest thing in the face; by COLOUR its descender
band was already the darkest (0.205 against `p` 0.187, `q` 0.166, `y` 0.129),
because the loop is a large ring — a lot of ink spread thinly. Raising the pen
to match the o's stroke exactly (pen ~96-104) takes that band to 0.27-0.29, half
again as dark as the p. 84 is the value that matches the rounds' STROKE without
making the g the darkest letter on the page.

The ceiling is mechanical rather than aesthetic: at **96** the thickening crown
closes on the connector and the glitch gate reads 2.83 units of white left; at
**104** that white is gone, which **no gate can see**, because a filled bay has
no concave corner. This is the same trap the compound-path attempt hit in round
196.

After the change the **bowl is now the lighter half of the g** — 42.3 against
the loop's 48.9 — and the letter as a whole still measures 42.9 against the
rounds' 53.4. Nothing was done about that; it is his call.

## What was checked and found clean

- **The roman's stems.** 29 glyphs, median 79.0, and not one of them more than
  20% off it. The roman's stem weight is as uniform as a drawn face gets.
- **Colour by family.** Roman stem 0.308 against round 0.305; italic stem 0.311
  against round 0.271. The roman's two main families are within 1% of each other
  in blackness, which is what a text face wants.
- **Figures against each other.** Apart from the 7, both styles' figures sit
  within 20% of their median, and their advances are within 10% of one another
  (348-532 roman, 311-603 italic) — they will set in columns.
- **The `O`/`M` pair** is bit-identical in weight across the two styles, which
  is a useful anchor: it says the two builds share a scale and the −16% is real
  and not an artefact of measuring two different rasters.
