# Albo's figures, 2026-09-23 — the 8's diagonal, the 2's foot, the italic 9's counter

Round 368. Three owner asks about the figures, all answered as NEW OPTION ROWS
in `figures.py`'s existing `ALBO_FIG_<d>` mechanism. **Nothing shipped changed:
the default build is bit-identical in both styles** (0 of 493 glyphs differ,
compiled `glyf` plus `hmtx`, against a tree whose only difference is this file).

Date: 2026-09-23. Built at `FJORD_STEM=66.9 FJORD_CONTRAST=0.892` (roman) and
`ALBO_ITALIC=aldine FJORD_STEM=66.9 FJORD_CONTRAST=0.80 FJORD_WIDTH=95
FJORD_SLANT=13` (italic) — `build_env.sh`. Every number below is measured on a
built font, not inferred from code.

---

## 1. The 8 — *"thinning out bottom left stroke and top right stroke"*

### The instrument

`tools/wedge_serif/cmp_fig_axis.py` (new). It imports `raster`, `dist` and
`ridge` from `cmp_g_strokes.py` unchanged, so the thickness is the same number
that file's tables are — twice the chamfer distance at the ridge, i.e. the
inscribed circle, which is **perpendicular to the stroke by construction**. What
is new is only the binning: by CLOCK POSITION about each ring's own counter,
because a ring runs through every direction and `cmp_g_strokes`'s
direction-binning cannot separate two places that share one.

**Validated before use**, as the method doc demands: Albo's `o`, `O` and `0`
come back thinnest at 12 and 6 o'clock and thickest at 3 and 9, which is what
`bowl_th` with `BOWL_OPTIONS['B']` (no `stress` key) must give. An instrument
that said anything else would have been wrong.

**One instrument bug found and fixed inside this round.** `max(prof.values())`
as the ring's peak is not safe: at a squared corner the inscribed circle is
bigger than the wall is thick, so raising the superellipse exponent inflates one
bin and nothing else — measured 69 → 79 at k 2.9 and 69 → **114** at k 4.0, with
neighbouring bins at 71 and 94. `cmp_fig_axis.peak()` takes the median of the
four heaviest bins instead. Every number below is the robust peak; the first
draft of this table used the max and overstated the `k` arms by 7 points.

### The measurement

Named point over the ring's own peak — scale-free, so faces of different weight
compare:

| | lower 7:30 | upper 1:30 | ring contrast | 7:30 / 4:30 |
|---|---|---|---|---|
| **Albo 8a (shipped)** | **0.82** | **0.77** | **1.50:1** | **1.16** |
| Georgia | 0.73 | 0.71 | 2.86:1 | 1.45 |
| Flanker Griffo | 0.65 | 0.65 | 2.51:1 | 1.42 |
| Pagella | 0.62 | 0.62 | 2.87:1 | 1.57 |
| Big Caslon | 0.49 | 0.49 | 6.69:1 | 2.08 |
| Poetica | 0.99 | 0.98 | 3.46:1 | 2.66 |

**He is right, and the mechanism is not the one the phrase suggests.** The 8's
axis is where Georgia's and Flanker's are (thin at 11.5–6 o'clock). It is heavy
at the two named points because **the ring never gets thin**: 1.50:1 against the
face's own `o` at 2.04 and `0` at 1.95, the flattest round in the roman.
`EIGHT_FLOOR = 0.65 S` is what holds it flat — 41% over the family's own bowl
hair of 0.46 S.

**And the last column is the ruling to make.** At 1.16 the 8 is the least
diagonal of the six, and Albo's own rounds run 1.15–1.20 (`o` 1.15, `0` 1.18,
`6` 1.20; the `9` is 0.92). Thinning the named points by turning the nib does
exactly what he asked and takes the 8's axis *away* from its own family and from
every reference. Cutting the ring deeper moves toward them.

### Four negative results

1. **`con` cannot do this** — and it is the obvious lever (option `c` is exactly
   it). `ring(con=)` re-spreads widths about their GEOMETRIC MEAN, and 7:30 sits
   above that mean, so raising it *thickens* the named point: the lower goes
   0.82 → 0.82 and the upper 0.77 → **0.85**, with the peak 69 → 79. The
   contrast ratio improves and the letter he is looking at does not.
2. **`k`, the squareness, reads as a fix and is not one.** 2.9 measures 0.78 /
   0.68 at no cost in height — and **the render is a rounded rectangle, not an
   8**, at 2.55 already and unmistakably at 2.9. The number and the picture
   disagreed and the picture won. Part of the apparent gain was the peak bug
   above.
3. **The floor is not free.** Releasing it alone takes the 8's top from 603 to
   553 and widens the recorded 8-vs-6 shortfall from 21 units to **71** —
   `ring_for_counter` solves the outer radius from the counter, and a thinner
   wall is a smaller ring (four wall crossings × 12.7 units). A new `hold_h`
   buys it back and the counters then grow by those same 50 units.
   `ring_stress` costs nothing: it holds 603 to the unit.
4. **A true nib** (round 195's own prescription) reaches 3.91:1 — and puts its
   thin at **18 units**, thinner than the roman `s`'s 16.6 hairline, on a figure
   that must survive a 13 px four-level render. Offered as arm `w`, not
   recommended.

### The arms (`ALBO_FIG_8=r`…`w`)

All height-neutral: top 603, bottom −29, 8/6 = 0.966, the shipped values to the
unit. `cmp_contour_hairs` finding set against the shipped build: **r, s, t
identical** (12 glyphs with findings); **u, v, w each add one** — a 2.0-unit
HAIR in `threeeighths`, where the released floor thins the denominator 8 at 12
o'clock. The `eight` glyph itself carries no finding in any of the seven.

| arm | what | lower 7:30 | upper 1:30 | contrast | 7:30 / 4:30 |
|---|---|---|---|---|---|
| a | shipped | 0.82 | 0.77 | 1.50 | 1.16 |
| r | nib +9° | 0.71 | 0.73 | 1.53 | 0.93 |
| s | nib +18° | 0.67 | 0.70 | 1.53 | 0.81 |
| t | nib +26° | 0.69 | 0.67 | 1.51 | 0.77 |
| u | floor released, height held | 0.83 | 0.72 | 1.98 | 1.21 |
| **v** | **u + nib 9°** | **0.75** | **0.67** | **2.00** | **0.98** |
| w | true nib (thin 0.15 S) | 0.81 | 0.71 | 3.91 | 1.36 |

**Recommendation: `v`.** It is the only arm that answers the diagnosis as well
as the symptom — it restores the face's own contrast (1.50 → 2.00, against the
`o`'s 2.04 and the `0`'s 1.95), brings both named points into the references'
band, and keeps the axis near neutral (0.98) instead of reversing it. Its costs
are measured and small: one new hair in `threeeighths`, and counters ~10% taller
at an unchanged outer height. `s` is the alternative if he wants the named
points thinner still and will accept a reverse axis no reference has.

---

## 2. The 2 — *"moving it down to match other numerals"*

These are old-style figures, so 3 4 5 7 9 descend and the comparison group is
the five that sit on the line — and within it the FLAT feet, because a round
foot is supposed to overshoot.

| | bottom | top | foot |
|---|---|---|---|
| 0 | −28 | 460 | round (overshoots) |
| 1 | −1 | 433 | **flat** |
| **2** | **+7** | **473** | **flat — 8 units over the 1, 36 over the 0/6/8** |
| 6 | −29 | 624 | round |
| 8 | −29 | 603 | round |

(3 −226/465, 4 −210/446, 5 −226/450, 7 −219/447, 9 −216/463 descend.)

**(a) The foot hovers: yes, by 8 units against the 1's flat feet.** The cause is
`TWO_LIFT = 8.0` (figures.py), a constant fitted on 2026-09-13 to a drawing that
has since been replaced by round 249's option `b` (base 1.50 of the bar weight,
26 units longer). It was fitted when the 2 bottomed at −7; under today's drawing
the same +8 puts the ink's lowest point at +7. *Section 5 of `albo-method.md` in
one line — a table that outlived the letter it was fitted to.*

**(b) The top: he says it matches and it nearly does**, but it is the tallest of
the eight low figures — 473 against the 3's 465, the 9's 463 and the 0's 460. So
dropping the whole glyph by 8 moves the top *toward* its neighbours, not away.

**The italic 2 does not hover** and is not touched: it bottoms at −35, below even
the round figures, because its bar carries round 212's drop of 42. These rows are
roman-only (`TWO_OPT_IT` is built from `b` and `c` alone).

**The trade, and there is no third way inside this construction:** bringing the
foot down either MOVES THE TOP (translate the glyph, `lift`) or THICKENS THE BASE
(extend the bar's bottom edge, its top edge and end wedge unmoved, `foot_ext`).

| arm | foot | top | base depth | advance |
|---|---|---|---|---|
| b | +7 | 473 | 83 | 460 |
| j | −1 | 465 | 83 | 458 |
| **k** | **−1** | **473** | **91** | **460** |
| l | −9 | 473 | 99 | 460 |
| m | −17 | 473 | 107 | 460 |
| n | −29 | 473 | 119 | 460 |

`cmp_contour_hairs`: **all five arms have a finding set identical to the shipped
build**, and `two` carries no finding in any of them.

**Recommendation: `k`.** The foot lands on the 1's line with the top held at 473
exactly as he asked, the advance unchanged, and the gate unmoved. Its cost is a
base bar 8 units deeper (83 → 91, +10%) — and by round 255's own table that is an
improvement, since Albo's 2 base measures 0.80 of the 0's thick side where the
references run 0.80–1.20. `j` is the alternative: no stroke changes weight at
all, and the top moves 8 units toward the 0/3/9, at the cost of 2 units of
advance.

---

## 3. The italic 9 — *"awkward left outside curve and counter"*

Two named faults, measured separately because they are separate contours.

### The left outside curve is NOT the fault, and the first instrument said it was

Reading the leftmost ink over the glyph's whole height puts the TAIL in the
sample — it descends to the left — and every face then reports a wobble:
**Flanker's italic 9 came back at 303 units of departure from a parabola, Albo's
at 138.** A number that large about a professionally drawn reference is the
instrument, not the face. Windowed to the BOWL's own rows (the rows its counter
spans), the picture inverts:

| face | reversals | max departure from a parabola |
|---|---|---|
| **Albo italic 9** | 1 | **2.0 u** |
| Albo italic 6 | 0 | 4.1 u |
| Albo italic 0 | 0 | 2.0 u |
| Flanker italic 9 | 1 | 4.7 u |
| Pagella italic 9 | 1 | 1.8 u |
| Poetica 9 | 0 | 1.4 u |

The italic 9's left flank is the cleanest among Albo's own italic rounds.
Instrument: `tools/wedge_serif/instruments/fig_left_flank.py`.

### The counter is the fault, and the TAIL is what does it

`cmp_aldine_counter`, largest counter, italic. `fill` is area over bounding box;
0.785 is an ellipse exactly.

| | area/ink | w/h | fill | widest row | floor |
|---|---|---|---|---|---|
| **9 (shipped)** | **0.82** | 0.68 | **0.76** | **0.55** | 0.43 |
| 6 | 0.89 | 0.68 | 0.78 | 0.45 | 0.05 |
| 0 | 1.17 | 0.57 | 0.78 | 0.55 | 0.07 |
| o | 1.10 | 0.58 | 0.76 | 0.45 | 0.10 |

The lever is where the tail enters the ring — `NINE_JOIN_SINK_IT`, 30 units on
the italic against the roman's 8. Laddered: **sink 8 gives fill 0.78** (the 6's
and the 0's), **sink 45 gives 0.75**. Less sink is better — which is exactly what
round 211's own note says (*"the join wants to start further OUT"*), and 30 is
further IN than the 8 it replaced. **The constant and the note beside it
disagree; the measurement supports the note.**

**Dead-dial control, run first:** `ALBO_ALD_NINE_RING_OVAL=1.0` reproduces the
shipped italic to every digit of every number above, because the italic's ring
already takes `FIG_OVAL` 1.0 through `fig_ring`. The counter is already pulled
onto its own ellipse; what dents it happens afterwards, in the union.

### The shipped italic 9 carries a gate finding today

`cmp_contour_hairs` reports a **REVERSAL of 170.4° at (389, 162), arms
14.9 / 17.3** — the right flank at mid-height, where the tail leaves the ring.
`albo_bumps` circles the same place (italic mark 223, a spur at (387, 180)) and
two more on this glyph (222 at (242, 434), 224 at (296, 49)), against **one** on
the roman 9 (219, a notch at (342, 65)). The fault has been visible to two
instruments and was never read off them.

| arm | what | area/ink | fill | widest | flank | `cmp_contour_hairs` on `nine` |
|---|---|---|---|---|---|---|
| a | shipped | 0.82 | 0.76 | 0.55 | 2.0 | REVERSAL (389,162) |
| e | sink 8 | 0.83 | 0.78 | 0.55 | 2.0 | HAIR (328,66) |
| **f** | **sink 0** | **0.83** | **0.78** | **0.45** | **2.8** | **none — leaves the report** |
| g | ring cut 1.4 | 0.86 | 0.77 | 0.45 | 1.6 | HAIR (390,164) |
| h | e + g | 0.86 | 0.79 | 0.45 | 1.6 | HAIR (328,66) |
| i | e + bigger bowl | 0.89 | 0.78 | 0.45 | 3.3 | none — leaves the report |

The glitch gate (`cmp_aldine_glitch --ttf`) is 2 findings on every arm including
the shipped one, and `nine` is in none of them.

**Recommendation: `f`.** It and `i` are the only two that remove the shipped
finding without adding one, and `f` changes only where the tail enters — `i`
moves the bowl's own radius, which is a larger change than was asked for and has
the worst flank of the six. `f` brings the counter's widest row down from 0.55 of
its height to 0.45 (the 6's) and its fill to the family's 0.78, for 0.8 of a unit
on the flank (2.0 → 2.8, still under the 6's 4.1 and Flanker's 4.7).

---

## What was checked and found CLEAN

- **Default bit-identity**, roman and italic, `glyf` + `hmtx`, against a tree
  whose only difference is `figures.py`: **0 of 493 glyphs differ**, re-proved
  after each of the three edits. (An earlier check read 177 and then 71 — both
  were other agents' concurrent edits to `accents.py`, `marks.py`, `stems.py`,
  `symbols.py` leaking into the baseline, not this change. Snapshot BOTH sides
  from the same tree.)
- **The roman 9** has one `albo_bumps` mark against the italic's three, and its
  bowl flank reads 1 reversal / 1.9 u. It does not have the italic's fault.
- **The 8's advance and width** are unchanged in every arm (491, 411).
- **The 2's advance** is unchanged in every `foot_ext` arm (460); only the
  translation arm `j` moves it, by 2 units.
- **`cmp_aldine_glitch`** is unchanged by every arm of all three glyphs.
- **`cmp_fig_axis`'s validation case** (the `o`/`O`/`0` reading thin at 12 and 6)
  passes, which is what licenses every other number it produced.
