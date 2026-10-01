# The question mark's neck: measured, and three arms (2026-10-01)

Owner, verbatim: *"subagent to improve question mark middle to bottom stroke."*

The stroke in question runs from the middle of the curl (its 3 o'clock, where
the hook is furthest right) down to just above the dot. It does not include the
crown, the curl's left terminal or the dot. Surveyed at commit `391f3cc`, the
round 454-455 fonts that shipped as TestFlight build 280.

**Status: three arms behind `ALBO_Q_NECK` (Q1, Q2, Q3). The default is today's
neck.** A default build is outline-identical to HEAD and to the shipped build-280
TTFs: `cmp_outlines.py --advances` finds 0 of 530 glyphs different in all four
cuts. Nothing has shipped. The recommendation is **Q1** (section 10).

Proofs, PNG at native pixels, in `docs/albo-question-mark-2026-10-01/`:

| file | what it shows |
|---|---|
| `summary.png` | the compact one: italic `aquí? ¿Usted vive aquí?` and roman `Why? What is it?` at 10 pt on the X3, through the reader's renderer, 5x nearest-neighbour. Rows: today, Q1, Q2, Q3 |
| `words_<cut>.png` | both lines in each cut, 10 pt, 5x nearest-neighbour |
| `words2x_<cut>.png` | `aquí?  Why?  it?` on the phone's 2x tier (10 pt x 2), 3x nearest-neighbour |
| `glyphs_<cut>.png` | one `?` per build plus three or four references at ONE x-height (150 px), as drawn (italics sheared), FreeType unhinted |
| `neck_zoom_<cut>.png` | the neck at 1.2 px/unit from the live builder, every outline vertex dotted: today's Bold notches, and the arms' joins |
| `neck_refs_<cut>.png` | the measuring sheet: today and the text-face panel, unsheared at Albo's x-height, each neck's traced centreline in red |

---

## 1. What is wrong with today's neck

Four faults, measured in all four cuts. "n" is the same face's own n stem and
"units" are Albo design units at x-height 429 (section 2).

1. **The neck ends at its heaviest point.**
   - The foot reads 1.28 n (roman) and 1.15 n (italic). That is the widest
     point of the whole neck.
   - 22 of the 26 reference 400s end at 0.25-0.64 n (median 0.47). The four
     that do not are Berkeley's flared kick (in both styles), Poetica's curl,
     and Albertus, whose neck closes to a 0.31 n point 20 units lower.
   - 13 of 15 text faces end their `?` within 0.08 n of their own `!`'s foot
     (table B). Albo's own `!` ends at 0.79 n (roman) and 0.71 n (italic), so
     Albo's `?` ends 1.6 times heavier than its own `!`.
2. **It stands too close to its dot.**
   - In the 400s the white between the neck and the dot is 36.5 units (roman)
     and 34 units (italic): 0.31-0.35 of the dot's diameter.
   - The references leave 41-105 units (median 64 in the roman, 71 in the
     italic). Albo's own `!` leaves 53.5 and 51.5.
   - `Q_DOT_CLEAR`'s docstring says the `?` and the `!` clear their dots
     identically. Round 375 changed the `?`'s rule to 0.55 S, against the
     `!`'s 0.8 S. The family's 20-degree pen cut then dips the low corner of
     the end face another 12 units toward the dot.
3. **The heel comes from the stroke's direction.** The descent cubic turns
   vertical in its last ~85 units. The bowl profile (vertical stress) gives a
   vertical stroke its full width, and the plan multiplies the end by 1.05.
   So the stroke swells into a heel right where every reference thins
   (THE ONE RULE, `docs/albo-method.md` section 1).
4. **At the 700s the neck folds.**
   - The dot clearance raises the foot with S, but the descent still starts
     at 0.5 C. That leaves 87 units of height for a 110-unit stroke that has
     to move 90 units left.
   - The centreline runs at 25 degrees and then turns vertical in about 30
     units. Its tightest turn is 0.81 of the stroke's half-width, so the
     inner edge folds.
   - Seen in `neck_zoom_Bold.png`: a notch on the counter side, a second notch
     at the foot's right corner, and a 125-unit slanted boot.
   - Neither the contour-hairs gate nor the touch gate reports it (section 8).

## 2. How it was measured

`tools/wedge_serif/instruments/qmark_neck.py` (new). Every face goes through
`fig27_trace.Face`:
- rendered unhinted;
- unsheared by its MEASURED slant (the `l`'s axis; `refs_registry.py` explains
  why never `post.italicAngle`);
- scaled so its x lands on Albo's 429 units, at 2 px/unit.

Albo builds go through the same function as the references.

- **The centreline** is traced by geodesic distance inside the ink, starting
  from the hook's lowest pixel. Each 1-unit band of geodesic distance is one
  cross-section of the stroke. Its centroid is the centreline point. Twice the
  largest distance-to-edge inside the band is the stroke's perpendicular width,
  whatever the stroke's angle. **The neck** is that centreline from the
  furthest-right point (3 o'clock) to the foot. The red lines in
  `neck_refs_*.png` are this trace, drawn on every face so it can be checked by
  eye.
- **foot**: the horizontal ink run 40 units above the neck's lowest ink.
  - The first version measured at 0.5 n and 1.0 n. At a bold's n, "1.0 n up" is
    already inside the neck's bend, and Georgia Bold read 1.55 n there.
  - A horizontal run through a DIAGONAL end reads wider than the stroke itself.
    That applies to Q3 and to Albertus.
- **gap**: from the neck's lowest ink to the dot's top. Also read straight off
  the outlines in font units (`qmark_arms.py gap`, table D).
- **dot ÷ foot**: the dot's diameter over the foot run, i.e. how much heavier
  the dot is than the stroke's end above it.
- **mean width**: the neck's ink area over its length.
- **lower-neck angle**: the centreline's angle from horizontal at u = 0.75
  (90 = vertical).
  - Near the foot (u 0.9) the geodesic bands are arcs around the seed pixel,
    so the angle there is unreliable and is not quoted.
  - The `!` rows of the instrument mean something only for foot, face, gap
    and dot.

Panels:
- **Text faces**: Georgia, Charter, Times, Baskerville, Hoefler, Palatino and
  Pagella (roman and bold); Georgia, Charter, Palatino, Flanker, Poetica,
  Pagella, Coelacanth and Times italics (italic and bold italic).
- **Lineage** (`--lineage`), the faces Albo's own guide names:
  - Albertus Medium (the stroke reference, from `~/Downloads`);
  - ITC Berkeley Oldstyle;
  - Van den Keere;
  - Dante;
  - Edgar;
  - Golden Cockerel.

## 3. The measurements

### A. The 400s (today, the arms, the references)

Roman:

| | foot, n | gap, units (÷ dot) | dot ÷ foot | mean width, n | lower neck, deg |
|---|---|---|---|---|---|
| **today** | **1.28** | **36.5 (0.31)** | **1.49** | **1.06** | 67, vertical only in the last tenth |
| Q1 | 0.78 | 50.5 (0.43) | 2.45 | 0.90 | 86 |
| Q2 | 0.50 | 51.5 (0.44) | 3.82 | 0.78 | 83 |
| Q3 | 0.85 (diagonal end) | 49.5 (0.42) | 2.24 | 0.96 | 50 |
| 13 references, median | 0.48 | 64 (0.58) | 2.93 | 0.69 | 66-90 in all 7 text faces |
| 13 references, range | 0.26-1.17 | 54-105 | 1.09-5.22 | 0.55-0.87 | Albertus 55, Golden Cockerel 61 |
| Albo's own `!` | 0.79 | 53.5 (0.47) | 2.40 | | |

Italic:

| | foot, n | gap, units (÷ dot) | dot ÷ foot | mean width, n | lower neck, deg |
|---|---|---|---|---|---|
| **today** | **1.15** | **34.0 (0.35)** | **1.25** | **0.88** | 69 |
| Q1 | 0.70 | 51.5 (0.53) | 2.07 | 0.76 | 84 |
| Q2 | 0.43 | 52.5 (0.54) | 3.35 | 0.68 | 85 |
| Q3 | 0.76 (diagonal end) | 51.5 (0.53) | 1.89 | 0.82 | 53 |
| 13 references, median | 0.46 | 71 (0.70) | 3.12 | 0.72 | 68-94 in all 8 text faces |
| 13 references, range | 0.25-1.17 | 41.5-91.5 | 1.06-4.79 | 0.56-0.88 | |
| Albo's own `!` | 0.71 | 51.5 (0.54) | 1.99 | | |

Where the weight sits along a reference neck varies. There are two families:
- **The roman model** (Georgia, Charter, Times, Baskerville, Palatino,
  Pagella, Golden Cockerel, Albertus) is heaviest at the 3 o'clock, at
  1.0-1.13 n, and tapers to the foot.
- **The calligraphic model** (Flanker, Coelacanth, Van den Keere, Edgar,
  Hoefler) is thin at the 3 o'clock (0.31-0.62 n), carries a heavy diagonal
  belly (0.87-1.33 n), and ends thin.

Both models end light. Albo's italic 3 o'clock is light by round 382's ruling
(top-left heavy, right side medium), so its Q1 neck becomes a mild belly
(0.68 → 0.79 → 0.60 S): the calligraphic model. The roman Q1 tapers from the
start (0.99 → 0.75 → 0.59 S): the roman model.

### B. A face's `?` ends at the width its `!` ends at

Foot, n (`?` / `!`):

| roman | `?` / `!` | italic | `?` / `!` |
|---|---|---|---|
| Georgia | 0.49 / 0.51 | Georgia It | 0.51 / 0.51 |
| Charter | 0.64 / 0.66 | Charter It | 0.64 / 0.69 |
| Times | 0.26 / 0.34 | Palatino It | 0.46 / 0.47 |
| Baskerville | 0.32 / 0.39 | Flanker | 0.36 / 0.29 |
| Hoefler | 0.36 / 0.42 | Poetica | **1.17 / 0.48** |
| Palatino | 0.50 / 0.49 | Pagella It | 0.45 / 0.47 |
| Pagella | 0.48 / 0.47 | Coelacanth | **0.44 / 0.70** |
| **Albo today** | **1.28 / 0.79** | Times It | 0.25 / 0.22 |
| Albo Q1 | 0.78 / 0.79 | **Albo today** | **1.15 / 0.71** |
| | | Albo Q1 | 0.70 / 0.71 |

13 of the 15 text faces are within 0.08 n. The GAPS agree too, but only in the
italics: 6 of 8 italic text faces leave within 3 units of the same white over
both dots. Five of the seven romans stand the `?` 17-31 units closer to its dot
than their `!` (Georgia 54.5 against 78.5).

**Albertus ends both marks in a point.** Its `!` stem converges to a gothic tip
above the dot. Its `?` neck keeps its weight down a diagonal (0.94 n at the
middle, 0.88 n 40 units up), and then the outer edge sweeps into a straight
inner edge, leaving 0.31 n 20 units up. Q2 is drawn from this.

### C. The 700s

| | Bold foot, n | Bold gap (÷ dot) | Bold dot ÷ foot | BI foot, n | BI gap (÷ dot) | BI dot ÷ foot |
|---|---|---|---|---|---|---|
| **today** | **1.28** | 66.0 (0.41) | **1.22** | **1.27** | 51.5 (0.39) | **1.11** |
| Q1 | 0.79 | 63.0 (0.39) | 1.98 | 0.82 | 53.0 (0.40) | 1.73 |
| Q2 | 0.55 | 68.0 (0.42) | 2.86 | 0.56 | 57.0 (0.43) | 2.52 |
| Q3 | 0.88 | 59.5 (0.37) | 1.77 | 0.92 | 50.5 (0.38) | 1.53 |
| references, median | 0.38 (11) | 53 (38.5-70) | 3.09 | 0.46 (10) | 48 (37-56) | 2.96 |
| Albo's own `!` | 0.80 | 89.5 (0.57) | 1.94 | 0.83 | 86.5 (0.65) | 1.68 |

At the 700s today's gap is already inside the references' range. What was wrong
there was the shape: the fold, and a foot about three times the references'
median.

## 4. The mechanism, in the code

`_q8` in `outlines/glyphs/marks.py`:
- the upper catmull (left terminal, crown, 3 o'clock at `(0.88 w, 0.74 C)`,
  shoulder `P` at `(0.74 w, 0.5 C)`);
- one descent cubic from `P`, arriving vertical at `(0.5 w, end_y)` (round
  233's fix for a folded end);
- the bowl profile by direction, times `Q8_PLAN` (`(0.8, 1.0), (1.0, 1.05)` in
  both styles: heaviest at the foot);
- the pen cut at both ends;
- `_raise` scales the hook by 1.142 about `(w/2, end_y)` toward the ascender
  (round 369).

Traced at the italic 400:
- the descent runs 0.85-0.91 S down its 53-67-degree diagonal;
- it turns vertical over its last 75 units (85 after the raise);
- it ends at 1.04 S.

Traced at the Bold:
- `end_y` is 250.6 while `P` is at 337.2: an 87-unit descent;
- the centreline flattens to 24-30 degrees, where the profile thins the stroke
  to 0.63 S;
- it then turns vertical inside about 30 units, back to 0.99 S;
- the outer edge bulges and the inner edge folds.

## 5. The arms

`ALBO_Q_NECK=Q1|Q2|Q3`; unset or empty is today's neck.

What every arm keeps:
- **Today's curl, sample for sample.** The neck starts at the curl's 3 o'clock
  (the hook's furthest-right sample). Every sample and width before it is
  today's. Stroking is `raw`, so nothing is re-sampled.
- **The raise.** It still scales about today's `end_y`, and the foot is placed
  for that.
- **The bbox.** The foot sits over the dot's centre (`x = w/2`, which the
  raise holds).

What every arm does at the bottom:
- **Width = the bowl profile by direction × a declared taper.** The taper runs
  from today's width at the 3 o'clock, through `PEAK` (1.0) at `PEAK_U`
  (0.30), to the arm's end width. That is how the `!` is drawn too: the pen
  times a taper.
- **The end** is the `!`'s own foot, `EXCL_BOT × pen.th(vertical)`, divided by
  the raise. Q2 alone narrows further, to a chisel.
- **The white over the dot** is `max(GAP × REF_S, GAP_D × dot diameter)`:
  - `GAP` 0.8 gives 53.5 units, the 400 `!`'s;
  - `GAP_D` 0.40 is where today's 700s already stand (0.41 Bold, 0.38 Bold
    Italic), so a bold dot keeps its air.

The dials, all `ALBO_Q_NECK_<NAME>`, read through `_qn`. `gen_state.py` cannot
see a concatenated name, so they are listed here:

| dial | Q1 | Q2 | Q3 | what it moves |
|---|---|---|---|---|
| `GAP` | 0.8 | 0.8 | 0.8 | the white over the dot, × REF_S |
| `GAP_D` | 0.40 | 0.40 | 0.40 | ... never under this × the dot's diameter |
| `PEAK`, `PEAK_U` | 1.0, 0.30 | 1.0, 0.30 | 1.0, 0.30 | the taper's high point along the neck |
| `A` | 0.60 | 0.65 | 0.45 | the S's handle leaving the 3 o'clock, × its height |
| `B` | 0.50 | 0.55 | 0.40 | the handle arriving at the drop (Q3: at the end) |
| `DROP` | 0.26 | 0.32 | | the straight drop, × the neck's height |
| `KNEE` | | 0.72 | | the drop's width where it leaves the S, × S |
| `TIP` | | 0.30 | | the chisel's end, × S |
| `POW` | | 1.0 | | how the drop closes: 1 = a straight wedge |
| `ANG` | | | 66 | the end's direction, degrees from horizontal |
| `END_X` | | | 0.0 | the end's x off the dot's centre, × S |

**Q1, "like its own `!`".**
- The S leaves the bowl, crosses at 33-45 degrees from horizontal, and drops
  straight for the last quarter of its height.
- The drop tapers to the `!`'s foot and ends square, as the `!` does.
- Foot 0.78 / 0.70 n against the `!`'s 0.79 / 0.71. Gap 53 / 55 units against
  the `!`'s 56 / 55 (font units). The roman's 3 units is the two dots' own
  life-jitter: the `?`'s dot top sits 3 units higher.
- This is the shape the text faces share: in all 15, the lower neck runs within
  24 degrees of vertical.

**Q2, "Albertus wedge".**
- The same S arrives at a knee right of the dot.
- From the knee down, the drop's left edge runs straight. The right edge closes
  in a straight line to a 0.30 S chisel cut on the pen angle, rising to the
  right as the curl's own terminal does.
- It is drawn as ONE stroke whose centreline rides at `xs + w/2`, so only the
  right edge moves.
- Foot 0.50 / 0.43 n, the closest to the references' median of the three. It
  has the most air at reading size.

**Q3, "the original gesture".**
- No S and no drop. The stroke leaves the 3 o'clock as today's does and stays
  on a diagonal to its end, with no vertical turn. The bowl profile therefore
  thins it by direction instead of swelling it.
- It ends at the `!`'s foot width, on the family's pen cut, which on a
  66-degree stroke lies within 5 degrees of level.
- It is the smallest departure from today's drawing. Albertus's own centreline
  runs at 55-59 degrees to its end, and Golden Cockerel's at 61.

Turn against half-width (`qmark_arms.py turn`; under 1 folds, under ~1.4 a
corner shows at 2x), split into the junction / the rest of the neck:

| | Regular | Italic | Bold | Bold Italic |
|---|---|---|---|---|
| today | 2.91 / 3.81 | 4.36 / 4.49 | 1.53 / **0.81** | 2.10 / 1.18 |
| Q1 | 3.82 / 3.72 | 5.13 / 3.87 | 1.59 / 1.66 | 2.08 / 1.84 |
| Q2 | 3.06 / 3.45 | 3.55 / 3.70 | 1.42 / 1.43 | 1.58 / 1.56 |
| Q3 | 4.39 / 8.62 | 6.69 / 10.08 | 2.05 / 3.48 | 3.00 / 4.12 |

### D. The white over the dot, off the outlines (font units)

| | `?` R | I | B | BI | `¿` R | I | B | BI |
|---|---|---|---|---|---|---|---|---|
| today | 38 | 36 | 71 | 56 | 37 | 33 | 71 | 56 |
| Q1 | 53 | 55 | 68 | 58 | 52 | 52 | 68 | 58 |
| Q2 | 54 | 56 | 73 | 62 | 53 | 53 | 73 | 62 |
| Q3 | 52 | 55 | 64 | 55 | 52 | 52 | 64 | 55 |
| the `!` / `¡` | 56 | 55 | 96 | 95 | 58 | 57 | 95 | 94 |

### E. Does the dot stand apart at reading size?

Measured with the reader's renderer (`qmark_arms.py dotsep`: unhinted, 2-bit,
150 dpi). Each cell is the number of rows of pure paper between the dot and the
dark stroke above it, at 8, 10, 12, 14, 16 and 18 pt:

| | Regular 1x | Regular 2x | Italic 1x | Italic 2x |
|---|---|---|---|---|
| today | 0 1 1 1 1 2 | 1 1 1 2 2 2 | - 1 0 1 1 1 | 1 2 2 2 2 2 |
| Q1 | 1 1 1 2 1 2 | 1 2 2 2 3 3 | 0 1 1 1 2 1 | 2 2 2 3 3 3 |
| Q2 | 1 2 1 2 1 2 | 1 2 2 3 3 3 | 1 1 1 1 2 2 | 2 2 3 3 3 3 |
| Q3 | 1 1 1 2 1 2 | 1 2 2 2 3 3 | 0 1 1 1 2 1 | 2 2 2 3 3 3 |

How to read the table:
- `-`: no dark stroke pixel stands over the dot's columns.
- At the 700s, Q1 and Q3 keep one row fewer than today at 12-18 pt 1x, and Q2
  keeps today's. Bold today reads 1 1 2 2 3 3 against Q1's 1 1 1 1 2 2.
- **No arm, in any cut or at any size, lets the dot touch the stroke in dark
  ink.** The CLEAR-row column of `dotsep` never reads 0.

## 6. What else moves (and what does not)

- **Only `question` and `questiondown` change**, in every cut and arm
  (`cmp_outlines.py`, 2 of 530). Their advances move by 0-2 units, which is the
  ink's extent rounding.
- **`¿` derives by rotation** (`symbols.g_questiondown`), so it takes each arm
  with no code of its own. Its bbox is unchanged, so its placement is too.
- **The curl.**
  - In the 700s the outline above y 560 (the curl, above its 3 o'clock) is
    identical, 0.00 units.
  - In the shipping 400s it moves up to 3.12 units (`qmark_arms.py curl`). The
    geometry is identical: built with `FJORD_CUT=0` the 400s' curl moves 0.00
    too.
  - The 3 units come from the linear cut. It keeps every fourth vertex of each
    contour, and a neck with a different point count re-phases which vertices
    the curl keeps. Measured, not assumed.
- **Not touched:** spacing (`spacing_b2.json`), kerning (`kern.py`), `gates.sh`,
  `local_ai/`, the `!`, every dot.

## 7. Gates (each run on today's fonts too, and compared)

| gate | today | Q1 | Q2 | Q3 |
|---|---|---|---|---|
| `cmp_contour_hairs.py --letters` (52 glyphs × 4 cuts) | 0 findings | 0 | 0 | 0 |
| `cmp_contour_hairs.py` full sweep (328 glyphs × 4 cuts) | 0 findings | 0 | 0 | 0 |
| `?`/`¿` worst turn | ≤ 122° | ≤ 111° | ≤ 119° | ≤ 122° |
| `cmp_touch.py` (5,309 pairs × 4 cuts) | 0 touching, 0 under floor | same | same | same |
| `cmp_touch.py --composites` (63,776 pairs × 4 cuts) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| `parts_check.py "?¿"`, smallest part, 8-18 pt 1x and 2x | flags at 8 pt (all but Bold), `¿` Italic also 10 pt | **`?` identical to today at every size** (the dot is the smallest part); `¿` within ±2 px; no new flag | same | same |

The `?` pairs in the italic touch sweep move by at most 1.4/1000 em:
- `F?` 0.0302 → 0.0288 (Q1, Q3);
- `C?` 0.0565 → 0.0551;
- `??` 0.0509 → 0.0505.

All are far above the 0.012 floor.

**A cost, not a gate.** `parts_check.py` with `FAINT=1` measures the share of
the glyph's ridge that renders at 2-bit level 1 or lower. A lighter neck end
renders paler at the smallest size:

| | italic `?` 8 pt | italic `¿` 8 pt | italic `¿` 10 pt |
|---|---|---|---|
| today | 25 % | 26 % (flagged) | 15 % |
| Q1 | 30 % | 26 % | 22 % |
| Q2 | 33 % | 34 % | 29 % |
| Q3 | 29 % | 29 % | 22 % |

parts_audit's line is 25 %. Today's `¿` already crosses it at 8 pt. From 12 pt
up, and at every size on the 2x tier, every arm sits under 25 %. The 700s and
the roman stay under it throughout; the largest roman reading is Q2's 20-22 % at
8 pt, against today's 3-5 %.

## 8. Negative results

- **A turned foot, the old-style kick of Palatino and Pagella, was drawn as a
  fourth arm and cut.** Albo's roman has no such terminal. At the 700s the
  bend's inner radius came out 12 units (turn ratio 1.36), a visible notch.
- **Q2 as a drawn spur unioned onto the stroke** left a white seam at the knee
  and a corner where the two edges met. It is now one stroke, which has neither.
- **Q2's drop on a convex taper** (`POW` 2.2: hold, then sweep in) left a waist
  above a bulb at the 700. A straight wedge (`POW` 1) does not.
- **Q2 with a heavy knee** (`KNEE` 0.80 or 0.85) swelled the knee past the S's
  own diagonal and notched the counter side at the 700. 0.72 is the heaviest
  that stays smooth.
- **S handles of 0.40 off the 3 o'clock** turned the stroke twice as fast as
  today's curl does there (10 degrees a sample against 5). The Bold's
  counter-side edge then cornered at the junction: an inner radius of 6 units,
  ratio 1.10. 0.60 / 0.65 fixed it. Q3's 0.45 never had the problem.
- **The first gap rule, `max(0.8 REF_S, 0.55 S)`,** closed the Bold's dot by
  4-12 units (today's 71 → 59-67). The dot-relative floor replaced it.
- **The contour-hairs gate does NOT see today's Bold notches** (0 findings).
  They are concave corners, not reversals past 165 degrees and not hairs. Only a
  zoom or the turn ratio shows them. The touch gate cannot either: it measures
  between glyphs.
- **The first `qmark_neck.py` foot rows** were placed at 0.5 n and 1.0 n above
  the bottom. In the bolds those land in the bend, and Georgia Bold read 1.55 n.
  Fixed heights (40, 80 and 20 units) replaced them.
- **The reference that "ends heavy" is not a model to follow here.** Poetica
  and Berkeley end heavy because their foot curls or kicks. Neither is a
  straight stroke that thickens.

## 9. Checked and found fine

- The default is outline-identical to HEAD and to the shipped build-280 TTFs.
  `cmp_outlines.py --advances` reports 0 of 530 in all four cuts, and it was
  re-run after every code edit.
- The arms change no glyph but `?` and `¿`.
- Every arm builds in all four cuts with the shipping environment (`build_env.sh`
  arrays). `gen_state.py --check` passes after regeneration. The new arm reads
  `ALBO_Q_NECK` (empty); its sub-dials are in section 5's table.
- Contour quality: 0 short segments, 0 duplicate points and no reversal over
  122 degrees in `?`/`¿` in every arm and cut.
- The touch whites of `?` pairs are unchanged in the roman, Bold and Bold
  Italic. In the italic the largest change is 1.4/1000 em, all far over the
  floor.

## 10. Recommendation: Q1

Q1 is the only arm that fixes every measured fault while matching a rule Albo
already has:
- the `?` ends at its `!`'s foot (0.78 / 0.79 n roman, 0.70 / 0.71 n italic);
- it ends square, as the `!` does;
- it stands over the dot by the `!`'s white in the 400s;
- it drops vertically over the dot, which the lower neck does in all 15 text
  faces;
- it clears every gate;
- it fixes the 700s' fold (turn ratio 0.81 → 1.66 / 1.84);
- at 8 pt it pales less than Q2 (italic faint share 30 % / 26 % against Q2's
  33 % / 34 %), about as little as Q3.

Its honest costs:
- It changes the descent's gesture (an S and a drop, where today is one
  diagonal).
- Its foot (0.70-0.82 n) is still heavier than the references' median (~0.47).
  That is Albo's own `!` weight, and the "Albertus heavy" of 2026-09-13.
- In the roman its white over the dot (50.5 units on the instrument) sits just
  under the lightest reference (54). Albo's `!` is there too. `GAP` is the
  number if he wants more air.

**Q2** is the answer if the owner wants Albertus's character in this mark.
- It is the closest to the references' end weight and gives the most air at
  reading size.
- It is the faintest at 8 pt.
- Its foot no longer matches the `!`, which ends square. Albertus points both
  marks, so the `!` would want the same point; that is a separate ask.

**Q3** is the answer if he wants today's gesture kept.
- It fixes the weight, the gap, the heel and the 700 fold, while the stroke
  stays one diagonal.
- Its dot stands out least of the three: dot ÷ foot 1.5-2.2, against the
  references' 2.9-3.1.

## 11. Reproduce

```bash
cd tools/wedge_serif && source build_env.sh
# a cut with an arm (any of ALBO_Q_NECK=Q1|Q2|Q3, plus ALBO_Q_NECK_<NAME> dials)
env "${ALBO_ITA_ENV[@]}" ALBO_Q_NECK=Q1 PYTHON_GIL=0 python3 -m outlines.build $OUT --style Italic
# the neck against the references (text panel; --lineage for Albertus, Berkeley, Van den Keere, Dante, Edgar, Golden Cockerel)
$VENV/bin/python instruments/qmark_neck.py --cut Italic --albo today=$BASE --albo Q1=$Q1 [--sheet out.png]
# the arms: turn (live builder, cut env), gap, dotsep, curl, zoom, proof
env "${ALBO_BLD_ENV[@]}" PYTHON_GIL=0 python3 instruments/qmark_arms.py turn "" Q1 Q2 Q3
$VENV/bin/python instruments/qmark_arms.py gap today=$BASE Q1=$Q1 Q2=$Q2 Q3=$Q3
$VENV/bin/python instruments/qmark_arms.py proof OUTDIR today=$BASE Q1=$Q1 Q2=$Q2 Q3=$Q3
```
