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

---

# Round 373 (2026-09-23) — the rulings on round 372, and the baseline

Owner rulings, verbatim: *"8: cut deeper wins"*; *"for 2: the bottom stroke
needs to not be thicker, vertically align the numerals to the baseline (check
italic numerals too)"*; *"9: h sink 8 + cut but patch the concave part on
bottom right outside"*. All in `outlines/glyphs/figures.py`. Baseline and after
were built from ONE snapshot of `tools/wedge_serif` at `1fd1fdd`, differing
only in `figures.py`, all four cuts through `build_env.sh`.

## 1. The 8 — option `w` ships, roman and Bold (`FIG_SHIP_ROM['8'] = 'w'`)

**Round 372's objection to `w` was arithmetic run backwards.** Its thin is
18 units, and 18 is *thicker* than the roman `s`'s 16.6 hairline, not thinner.
Re-measured on the shipped build with `cmp_fig_axis` (the chamfer ridge, which
is perpendicular to the stroke by construction): 18 at the upper ring's
12 o'clock, 20 at the lower ring's 6. Ring contrast is 3.77 (upper) and 3.58
(lower), against 1.50 before. (3.91 in round 372 was a single number, taken
before the waist fix below.)

**It failed a gate at the 700 and passed at the 400, and the fault was
there at both weights.** At the Bold, `w` opened a **CRACK** in the waist
(`cmp_aldine_glitch`, a hole of mean width 4.4) and a **HAIR** on `eight`
(`cmp_contour_hairs`, (231, 311)). At the 400, `fiveeighths` took a new HAIR.
The mechanism, measured on the rings before the ink spread:

| | lower-top wall + upper-bottom wall | overlap (`bowl_hair() x waist`) | result |
|---|---|---|---|
| a, 400 | 87.0 | 30.7 | covered |
| v, 400 | 65.4 | 30.7 | covered |
| **w, 400** | **29.8** | **30.7** | the counters intersect by 0.9; the 1.2 ink spread closed it |
| a, 700 | 150.9 | 53.3 | covered |
| **w, 700** | **46.0** | **53.3** | the counters intersect by 7.3: the CRACK |

The rings overlap by one family bowl stroke. A true nib's walls at 12 and
6 o'clock are its thin, which is less than that, so when the overlap exceeds
both walls together the two counters meet. This is §1b of `albo-method`: the
fault is in how the two strokes meet, and no width dial reaches it. **Fix
(WAIST ROOM, end of `g_eight`):** the overlap never exceeds the two walls as
drawn, less a quarter of the thinner wall. The figure is re-solved from the top
with the life counter reset, and `hold_h` still holds the height. After the fix
the overlap is 26.1 at the 400 and 40.2 at the 700. Every row whose walls
already cover the overlap (every row but `w`) never enters the branch, and
`a` was re-probed identical.

So `w` ships without falling back to a shallower arm. Its gates:
`cmp_contour_hairs` has no finding on `eight` and no new finding anywhere, in
any cut. `cmp_counter_dents` at 700 and 700 italic reads 0 and 0.
`cmp_aldine_glitch` reports the same sets as before.

**The italic 8 has the same fault and was NOT changed** (the asks were about
the roman). Italic `cmp_fig_axis --slant 13`: the 8's rings measure **1.50:1
(lower) and 1.38:1 (upper)**, against its own `0` at 3.39 and `o` at 3.07 —
flatter than the roman 8 was. Its thick also falls at 0 and 6.5 o'clock,
which no other italic round does.

## 2. The 2, and every figure on the baseline

Rejected on the ruling: `foot_ext` (rows k–n). They stay in the table and now
build 8 lower, because `TWO_LIFT` moved underneath them.

- **Roman 2:** `TWO_LIFT` 8.0 → **0.0**. This is the stale constant from
  round 372, corrected by translation only; no stroke changes weight. The foot
  goes from +7 to −1 (the 1's line), and the top from 473 to 465, level with
  the 3.
- **Italic 2:** `TWO_BAR_DROP` 42 → **0** as well. With the drop it bottomed at
  −35, 34 units below its one flat-footed sibling (the 1, at −1). **This
  reverses round 212's ruling** (*"lower the crossbar of 2 … to where the
  crossbar of 4 is"*), on the newer ruling's word. `ALBO_ALD_TWO_BAR_DROP=42`
  restores it exactly. **Flagged for the owner.**
- **0, 6, 8: their foot overshot twice.** `latin.FIG_BOX` gives these three a
  bottom of −0.02 CAP (13.5 units), and their rings are then drawn from −OVER,
  so the overshoot is counted twice: −28/−29 against the face's own `o`, `O`
  and `e` at −15. Every reference with old-style figures puts its round
  figures' foot at its own `o`'s overshoot:

  | | 0 / 6 / 8 bottom | o bottom |
  |---|---|---|
  | Georgia | −16 / −16 / −17 | −15 |
  | Pagella | −11 / −11 / −11 | −11 |
  | Flanker | −10 / −10 / −10 | −10 |
  | Poetica | −16 / −16 / −16 | −14 |
  | Big Caslon | −3 / 0 / −4 | −3 |
  | Albo before | −28 / −29 / −29 | −15 |

  The correction is `ROUND_FOOT` in `figures.py`; `latin.py` was left alone,
  because FIG_BOX also sets heights. **The 0** is drawn 13.5 units shorter and
  lifted 13.5, so its top stays at 460, level with the round-topped 3 and 9, as
  every reference keeps it. **The 6 and 8** are only translated up 13.5: they
  are ascenders with ruled drawings, and both move together, so the 8's
  21-unit shortfall under the 6 is kept to the unit. `ALBO_FIG_ROUND_FOOT=0`
  restores the old −28/−29.

Bottom / top of every figure, in design units, built fonts:

| | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| Regular before | −28/460 | −1/433 | **+7/473** | −226/465 | −210/446 | −226/450 | −29/624 | −219/447 | −29/603 | −216/463 |
| Regular after | **−15**/460 | −1/433 | **−1/465** | = | = | = | **−15/638** | = | **−15/617** | = |
| Italic before | −28/460 | −1/433 | **−35/476** | −223/467 | −210/446 | −224/452 | −29/654 | −210/433 | −29/579 | −216/465 |
| Italic after | **−15**/460 | −1/433 | **−1/467** | = | = | = | **−15/667** | = | **−15/593** | = |
| Bold before | −29/460 | −1/433 | +7/488 | −229/484 | −210/446 | −228/466 | −29/625 | −225/447 | −29/571 | −216/479 |
| Bold after | **−15**/460 | −1/433 | **−1/480** | = | = | = | **−15/639** | = | **−15/584** | = |
| BoldItalic before | −29/460 | −1/433 | −35/492 | −225/484 | −210/446 | −224/466 | −29/655 | −210/433 | −29/658 | −216/479 |
| BoldItalic after | **−15**/460 | −1/433 | **−1/484** | = | = | = | **−15/668** | = | **−15/671** | = |

The Bold and BoldItalic follow the 400s without separate handling.

**The descenders were checked and NOT changed.** The flat feet sit on the box
line (the 4 at −210 in every cut, and the italic 7), and the round bottoms (3,
5) overshoot it by 13–19, which is the face's round overshoot. Between them are
the roman 7's angled cut at −219 (−225 Bold) and the 9's tail flag at −216,
the owner's ruled `NINE_BOTTOM`. Georgia runs its descenders level (−178 to
−181) and Pagella spreads 20 (−212 to −232), so Albo's 16 is inside the
references' range and follows the same flat-vs-round logic the baseline now
does.

## 3. The italic 9 — `h` plus the patch, shipped as row `j` (`FIG_SHIP_IT['9'] = 'j'`)

`h` stays in the table unchanged, as the picture he ruled on. **The concavity,
found on the outline:** walking the outer contour's right side, `h` turns
−26.8° then −5.2° at (402, 117)–(407, 123). That is a 32° re-entrant kink
where the tail's outer edge leaves the ring's flank. The shipped `a` has the
same kink at (378, 97), so it is not new to `h`. `h`'s HAIR at (328, 66) is a
different place, the crotch under the bowl.

**The mechanism** is the roman's round-233 fault. The italic tail started
8 units inside the wall at 0.08 of its width, with its first handle almost
straight down, while the ring's tangent at −20° runs 3.6× further left. Its
outer edge therefore came out through the ring's outer contour at an angle.
**Negative result:** turning only the handle onto the tangent (built, measured)
removes the (328, 66) hair but leaves the kink at 22°. Direction was half the
cause and width the other half.

**The patch** is the roman's round-233 construction, with the wall measured on
the italic's own cut ring (con, stress and oval make it anything but
`bowl_th`). The tail starts at the middle of the wall, its handle lies along
the ring's tangent, and it begins at the wall's own width and sheds to its
width rule over `NINE_TAPER_ROM_T`. Both edges then leave on the ring's two
contours. The roman's start dials (0.97 / 0.20) were kept after a 5-rung ladder
(0.85–1.00 × 0.10–0.30): every rung was clean, and the counter moved by 0.02 at
most.

| | worst concave turn, right outside | `cmp_contour_hairs` on `nine` | counter area/ink | fill | widest |
|---|---|---|---|---|---|
| a (shipped before) | 31.7° at (378, 97) | REVERSAL (389, 162) | 0.82 | 0.76 | 0.55 |
| h (as ruled) | 26.8° at (402, 117) | HAIR (328, 66) | 0.86 | 0.79 | 0.45 |
| **j (ships)** | **6.6°** (facet level) | **none** | 0.85 | 0.78 | 0.45 |

What the patch costs: the counter's lower right comes in by 3% of its width at
rows 0.15–0.25, because the tail's inner edge now runs along the wall. **The
roman 9 is clean there:** its right outside turns no more than 5.2° at any
vertex. Its only large turns are the inside crotch fillet at (345, 73), which
is deliberate (round 233).

## Changed glyphs (fontTools `glyf` + `hmtx`, per style)

- **Regular**, 13: `zero two six eight` + `onehalf uni2070 uni2078 uni2080 uni2088 oneeighth threeeighths fiveeighths seveneighths`.
- **Italic**, 19: `zero two six eight nine` + `uni00B2 onehalf uni2070 uni2078 uni2079 uni2080 uni2082 uni2086 uni2089 twothirds oneeighth threeeighths fiveeighths seveneighths`.
- **Bold**, 12: `zero two six eight` + `uni2070 uni2078 uni2080 uni2088 oneeighth threeeighths fiveeighths seveneighths`.
- **BoldItalic**, 13: `zero two six eight nine` + `uni00B2 onehalf uni2070 uni2079 uni2080 uni2082 uni2089 twothirds`.

Every changed glyph is a figure or a superscript, subscript or fraction built
from one. No contour count changed (the `cmp_contours` census is unchanged, so
no re-cut cascade). The advances move by 1–2 units, except the italic 2 (471 →
475, lsb 9 → 19) and the BoldItalic 2 (504 → 512): its bar now sits inside the
fitting band. `approved.py`: both approved glyphs are unchanged.

## Gates, before → after

- **`cmp_contour_hairs`:** `--letters` is identical in all four cuts. The full
  sweep has no new finding in any cut and two fewer. Italic `nine` is the
  patch. **BoldItalic `six` is NOT a fix:** its 1.4-unit arm is still there,
  re-snapped by the 13.5-unit lift into a 128.7° turn that the gate does not
  flag.
- **`cmp_touch`:** identical rows in all four cuts.
- **`cmp_counter_dents`:** 0 and 0 at the 700s, as before.
- **`cmp_aldine_glitch --ttf`:** identical sets (Italic Y and ﬆ, BoldItalic Y),
  and none of them a figure.

## Checked and found CLEAN

- The roman 9's right outside (see above).
- Every 8 row other than `w` never reaches the waist-room branch.
- `hold_h` holds the Bold `w`'s height: 571 before, 584.5 after the 13.5 lift.
- The italic 9's left flank, as round 372 already found.
- The glyph lists above are the only changes, from a shared snapshot.

## What was not done

- **The italic 8's flat ring**, reported above. It wants its own ruling.
- **The italic 2's round-212 reversal** needs the owner's confirmation.

---

# Round 374 (2026-09-23) — *"yes, address all numeral issues"*

**Scope.** Changes are in `outlines/glyphs/figures.py` and `outlines/build.py`
(`solve_widths` only, as the coordinator authorised). The before and after
builds come from one snapshot of HEAD `217d675`, which includes the Greek, and
the two differ only in those two files. All four cuts use `build_env.sh`.
Every number below is measured on the built fonts.

## The ledger

| # | item | before | fix | after |
|---|---|---|---|---|
| a | **Italic 8 flat** | rings 1.50 / 1.38:1 against its 0 (3.39) and o (3.07); BoldItalic 1.38 / 1.31 | `EIGHT_OPT_IT['x']`: a true nib (1.30 / 0.20 × S), floor released, `con` 1.0, set on the 6's line | **2.76 / 2.92:1**, colour 0.217 (was 0.222); BoldItalic 3.36 / 3.42 |
| b | **8 short of its 6** | top 8/6: R 617/638, I 593/667, B 584/639, BI 671/668 | `to_six='shipped'` in the new `x` rows (roman `x` = `w` + to_six) | **637/638, 667/667, 639/639, 668/668** |
| c | **the 2 flat** | cut: R 1.44 (o 2.00), I 1.55 (o 2.84) | roman `TWO_OPT['g']` (arc 1.0 of the profile, slash held at 0.70, base unchanged); italic `TWO_OPT_IT['g']` (the slash held at 0.70, the arc at the italic's own 0.82) | **R 1.85, I 2.09**; Bold 2.25 → 2.33; BoldItalic 2.40 → 2.16 |
| c | the 3's upper lobe (roman) | upper/lower lobe 0.79 (refs 0.82–0.94) | `THREE_OPT['g']` (round 255) | **0.90**; Bold 0.80 → 0.90 |
| c | the other figures' cut | 0 1 5 6 7 9 sit inside their references' ratio to the o (Georgia 0.77–1.15, Flanker 0.39–0.82, Pagella 0.78–1.17) | none | CLEAN |
| d | spacing spread | `cmp_figure_space --body` R 1.62×, I 1.34×, B 1.54×, BI 1.42× (refs 1.78–5.58×); the "2.10×" of the misfit audit was already answered on 2026-09-21 | none needed | R 1.65×, I 1.36×, B 1.70×, BI 1.41×; `cmp_space_2d` digit+digit **in band in all four** (R 0.091 [0.086–0.142], I 0.129, B 0.088, BI 0.130) |
| e | **width clamp** | italic solved against SHEARED ink, so 8 of 9 italic figures sat on the 0.70 floor; unsheared the 7 was **−13.5%** under its target, the 5 +13.5%, 3 +8.1%, 9 +7.9%, 2 +7.3%; roman 3 +2.9%, 5 +7.8% on the floor | `build.py`: figures measured unsheared (`ALBO_FIG_WIDTH_UNSHEAR`), figure floor 0.55 at stem ≤ 84 (`ALBO_FIG_WIDTH_FLOOR`) | italic, every figure within +2.0% of target (7 now +0.1%); roman 3 +1.0%, 5 +1.1% |
| f | weight by family | the 7 as the lightest figure: roman 7 stroke −10% (round 361 fixed it); italic 4 −18% | italic 4 bar (below) | CLEAN / see g-4 |
| g | **the 1 (roman)** | ink/0 ink 0.477 (refs 0.535–0.79); advance 249 | `ONE_OPT['i']` = h with feet 1.6 × FOOT | **0.579**, advance 277; Bold 0.594 → 0.696 |
| g | the 1 (italic) | 0.567 | none: `O1` touches past ~0.58 (round 229's ladder) | NOT FIXED, needs a kern |
| — | **the 4's bar under the baseline** (found in round 255, added here) | centre R −6, I −6, B +16, BI +1 u (refs +28 to +98) | roman `FOUR_OPT['e']` (raised to 0.378 and the capitals' bar weight); italic `FOUR_OPT_IT['d']` at 0.36 | **R +44, I +30, B +62, BI +44** |
| h | BoldItalic `six`, the 1.4-unit arm | round 373 already put it under the gate (128.7°, arm 1.0 / 6.4) | none | looked at ×4 (below) |
| i | gate findings on figures | hairs: `uni2081` (R), `uni2086` (I), `uni2074` (BI) | — | **all three gone, none added** |
| j | italic vs Flanker / Pagella | heights, descenders and direction checked | the 4's bar (above) | see "checked" |

## How each was fixed, and the negative results

**The 8, both styles.** First negative result: the option alphabet ended at `w`,
so a row `x` resolved silently to `a`. The first ladder built today's 8 under
every rung, and it was caught only because the heights did not move. `OPT()`
now accepts a–z.

**The waist overlap** (`ALBO_8_WAIST_ROOM`) — the rings' two walls must overlap
by more than a sliver.
- On the taller rings, 0.25 put HAIRs on the scaled 8s (`threeeighths`,
  `uni2088`) at the ring crossing. Laddered 0.10–0.80: the findings moved from
  glyph to glyph at facet level.
- 0.35 and 0.10 were clean in all four cuts. 0.35 ships, because 0.10 leaves
  the walls overlapping by 1.5 units, next to the crack round 373 fixed.

**The italic nib.**
- At the roman's 1.03 / 0.15 the thick was 54 against the 0's 85. The
  italic's 0 and 6 carry FIG_CON 1.8 and its 8 does not.
- 1.75 / 0.22 matched the 0's ring exactly (thick 88, 3.27 / 3.47:1). It
  rendered as the darkest glyph in a run, visibly bold in `1889` at 13 px:
  colour 0.274 against the 0's 0.168.
- 1.30 / 0.20 keeps the old colour (0.217) and moves only the cut.

**The height.** This reverses the round-64 ruling (*"make it shorter"*) in
favour of five references out of six. `w`, the unmoved height, is still one
letter away.

**The 2.**
- Roman `g` answers round 255's two misses: the arc is 0.72 of the 0's side
  where the references run 0.87–1.43, and the cut. It keeps the base the owner
  ruled must not thicken.
- Cost at the Bold: advance 474 → 503. The Bold's width target is 11% under
  its ink and pinned at the 0.70 floor (see e).
- Alternatives measured: `ALBO_2G_TOPW=0.85` (cut 1.73, Bold advance 487) and
  `=0.74` (cut 1.92, colour −11%, Bold advance 474).
- Italic arc laddered 0.82 / 0.90 / 1.0:
  - 1.0: BoldItalic advance 512 → 543, and a larger notch where the finial
    meets the counter.
  - 0.82: best italic cut (2.09), BoldItalic advance 514. Colour 0.137 → 0.118.
  - 0.90 is the middle: cut 1.98, colour 0.126.

**The 4.**
- Roman `e` is round 255's recommendation.
- In the italic, `e` opened a HAIR at the BoldItalic counter apex (152°), so
  `d` (raised only) ships.
- At the roman's 0.378 the italic bar put `z4` at 0.0115 em and BoldItalic
  `q4` at 0.0109, both under the 0.012 floor. Laddered 0.34 / 0.35 / 0.36;
  0.36 is the highest clean rung.
- The italic 4 stays the lightest italic figure by stroke (40.6 against the
  figures' ~55). Weighting its bar is what opened the hair.

**Width (e).**
- Negative result: a 0.55 floor on the Bold pinned its 5 at 0.55 and still
  read +8.9%, visibly squeezed.
- The Bold's targets are the 400's reference widths × 0.95, which a bold
  cannot reach. That is a target problem, so the bolds keep 0.70.
- Residual, unchanged: Bold figures run +6% to +28% over target, BoldItalic
  +12% to +32%.

**The 1.**
- Feet 1.6 / 2.0 / 2.4 × FOOT and flag reach 95 / 125 laddered. Every rung
  widens the white with the ink, since the bearings follow the ink.
- 1.6 is the first rung inside the band: spread 1.62 → 1.65× at the 400.
- 2.4 put two more pairs under the touch floor. The flag's reach bought
  nothing measurable.

**BoldItalic `six` (h), NOT changed.**
- Magnified ×4, the "arm" is the tip of the white pocket between the tail and
  the bowl. The contour's first and last points sit one unit apart there
  (246, 397) and (247, 397).
- Round 373's lift already took it out of the gate. What remains is a sharp
  pocket at integer precision, not a hair.
- Clearing it would take a crotch fillet on the 6 in all four cuts, which is a
  design change nobody asked for. Recorded rather than done.

## Changed glyphs, per style (glyf + hmtx, one snapshot)

- **Regular (27):** `one two three four five eight` + `uni00B2 uni00B3 uni00B9 onequarter onehalf threequarters uni2074 uni2075 uni2078 uni2081 uni2082 uni2083 uni2084 uni2085 uni2088 onethird twothirds oneeighth threeeighths fiveeighths seveneighths`.
- **Italic (36):** all ten figures except `one` + 26 superiors, inferiors and
  fractions. The 0/3/5/6/7/9 are here through the width solve.
- **Bold (24):** `one two three four eight` + 19 composites.
- **BoldItalic (20):** `two four seven eight` + 16 composites.

Proof of scope:
- Every non-figure glyph is byte-identical in glyf and hmtx in all four cuts,
  capitals included.
- GPOS is identical in all four.
- No contour count moved (`cmp_contours` census unchanged).

## Gates, before → after

- `cmp_contour_hairs --letters` is unchanged in all four cuts.
- Full sweep: −1 finding in the Regular (`uni2081`), −1 in the Italic
  (`uni2086`), −1 in the BoldItalic (`uni2074`); the Bold is unchanged.
- `cmp_touch`: counts unchanged in all four (R 0/1, I 0/0, B 0/1, BI 1/2);
  the under-floor sets are identical.
- `cmp_counter_dents` at the 700s: 0 / 0.
- `cmp_aldine_glitch`: identical sets.
- `./gates.sh`: the delta is the two removals only (`uni2081`, `uni2086`).
  Approved glyphs are unchanged, the bench matches, and the contour census is
  unchanged.
- `albo_bumps` (a review sheet, not a gate): italic 8 2 → 4 marks, at the
  crown and foot where `FIG_HAND`'s ±3-unit press lands on the nib's thin wall,
  and at the ring crossing. Italic 9 1 → 2, roman 3 4 → 5, roman 4 4 → 3.
  None is a gate finding.

## Checked and found CLEAN

- The 0 1 5 6 7 9 cut against the references' ratio to their own o.
- The figures' spacing spread (d) is under every reference.
- The roman 7's weight (round 361).
- Descenders: 3 4 5 7 9 run −201 to −229 in all four cuts; Georgia spreads
  3 units and Pagella 20.
- Round foots at −15 and flat feet at −1 in all four cuts.
- Italic heights: the low figures stand at 1.07 of the italic's x-height,
  against Flanker and Pagella at ~1.0. That is inside the roman references'
  1.04–1.12 and was left alone.
- Direction and construction against Flanker and Pagella found nothing like
  the Greek's faults. The only structural miss was the 4's bar, now fixed.

## Not done

- The italic 1's width needs an `O1` kern (`kern.py`).
- The Bold width targets.
- The italic 4's weight.
- The BoldItalic 6 pocket.
- `FIG_HAND` press positions on the italic 8 (`aldine.py`).

Renders: `/private/tmp/.../scratchpad/albo/figs374/` — see the report.

---

# Round 376, figures (2026-09-24) — the Bold width target and the italic 4's weight

Owner: *"yes to all"* (round 374's open items). Changes are in
`outlines/glyphs/figures.py` and `outlines/build.py` (`solve_widths` and its
constants only). Before and after are built from one snapshot of HEAD
(`8c2fddc`; the base `build.py` and `figures.py` were checked equal to HEAD),
all four cuts, through `build_env.sh`.

## 1. The figures' width target knows the weight (`build.py`)

**Before.** The target was the 400's reference width × `pen.WIDTH` at every
weight. The Bold's figures ran +6% to +28% over target, the BoldItalic's +12%
to +32%, and the solver sat on its 0.70 floor. Growth from the 400 was
uneven. Figure ink, Bold minus Regular, in units:

| | 0 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| before | +3 | +48 | +54 | −23 | +70 | +22 | −20 | +17 | +20 |
| after | +10 | +17 | +18 | +5 | +16 | +13 | +7 | +8 | +10 |

**What bold references do.** Eleven regular/bold pairs on this Mac: Georgia,
Times New Roman, Charter, Palatino and Baskerville in roman and italic, plus
Hoefler Text Black. The stem is the `l`'s horizontal cut at 40% of its height;
the figure is its ink width, old-style where the face has it. Figure width
gained per unit of stem gained:

| face | K |
|---|---|
| Georgia Bold | 1.15 |
| Georgia Bold Italic | 1.20 |
| Times New Roman Bold | 0.29 |
| Times New Roman Bold Italic | 0.46 |
| Charter Bold | 0.78 |
| Charter Bold Italic | 0.38 |
| Palatino Bold | −0.11 |
| Palatino Bold Italic | 0.61 |
| Baskerville Bold | 0.61 |
| Baskerville Bold Italic | 0.63 |
| Hoefler Text Black | 0.88 |

The median is **0.61**, and overall the references' figures widen ×0.99 to
×1.19.

**The rule.**
- `target += FIG_BOLD_K × (S − 66.9) × Albo's own measured l-stem per S`.
- `FIG_BOLD_K` is 0.61. The l-stem-per-S factor is 0.917 roman and 0.819
  italic: 64.0 → 109.0 and 57.5 → 97.7 against S 66.9 → 116.
- With a target it can reach, the bold takes the figures' 0.55 floor
  (`ALBO_FIG_BOLD_FLOOR`). At S = 66.9 the term is zero.
- `ALBO_FIG_BOLD_K=0 ALBO_FIG_BOLD_FLOOR=0` restores the old solve.

**After.** Every solved Bold figure is +0.0% to +2.9% of target, and every
BoldItalic figure +0.3% to +2.2%. The exception is the 8 (Bold +8.5%,
BoldItalic +4.3%), whose width comes from the 6's bowl counter rather than
from W.

Overall figure ink, bold over regular:

| | before | after |
|---|---|---|
| Bold | ×1.061 (0.95–1.20 per figure) | ×1.030 (1.01–1.05) |
| BoldItalic | ×1.119 (1.05–1.18) | ×1.069 (1.02–1.10) |

The Bold's ×1.03 is inside the references' band but near its narrow end
(Palatino 0.99, Times 1.05), because the Bold is condensed to `FJORD_WIDTH` 95
by design.

Spacing:

| | figure-space spread | digit+digit |
|---|---|---|
| Bold | 1.70 → 1.81× | 0.088, in band, unchanged |
| BoldItalic | 1.46 → 1.51× | 0.134 → 0.131, in band |

Both spreads are still under every reference (1.78–5.58×).

## 2. The italic 4's weight (`FOUR_OPT_IT['f']`, shipped)

**Before.** `cmp_weight_survey` (the ridge median) read the 4 at −24% of the
italic's figures and −26% of the BoldItalic's, the lightest in both. By mean
stroke width (2 × area / outline length) it was −3%: the stem carries it. The
light parts are the bar and the diagonal, which are what the eye reads.

**Ladder** (bar × stem × diagonal):
- 1.0 / 1.2 / 0.86: heavier stem, no change on the ridge measure (−24%).
- 1.15 / 1.12 / 0.86 and 1.25 / 1.2 / 0.86: clean.
- **1.15 / 1.0 / 0.86: clean. Ships.**
- 1.2 / 1.0 / 0.90: a HAIR on the italic superior `uni2074`.
- 1.25 / 1.05 / 0.86: clean.
- 1.0 / 1.1 / 0.95: the BoldItalic went from 2 pairs under the touch floor to
  5, with 3 touching.
- Round 374's `e` (bar 1.45) had opened the counter-apex HAIR in the
  BoldItalic.

**After** (1.15 / 1.0 / 0.86: the bar 15% heavier, the diagonal option `b`'s
0.86, the stem unchanged):

| | ridge median | mean stroke width | colour |
|---|---|---|---|
| Italic | −24% → **−7%** | −3% → **+1%** | 0.134 → 0.141 |
| BoldItalic | −27% → **−14%** | +1% → **+5%** | — |

No hair, and touch and dents are unchanged.

## 3. Found on the way: the 7's mitre misses the diagonal

The BoldItalic 7's re-solved width turned a pre-existing construction step
into a gate HAIR at 153°, (478, 371).

**The mechanism.** The bar's end face is laid on the diagonal's edge as `pw`
predicts it. The built diagonal, on its own profile and a curve in the italic,
does not sit on that line. Measured as the diagonal's built edge, extended to
the bar's end, minus the bar's end:

| cut | step (units) |
|---|---|
| Regular | −1.1 |
| Italic | +7.3 |
| Bold | −6.7 (the bar stands proud) |
| BoldItalic | +12.4 (the diagonal's corner stands proud) |

**The fix.**
- The bar's end is moved onto the BUILT edge, read just below the bar's end,
  and cut parallel to it. It is re-measured until it lands within 0.1 unit.
- **Bolds only**: the round required the Regular and Italic to be
  byte-identical, and no tolerance separates the four cuts, because the
  Italic's step (7.3) is larger than the Bold's (6.7).
- The Regular's and Italic's steps are recorded, not fixed.
  `ALBO_FIG_7_MITRE_ALL=1` applies the fix to them too; measured, it takes the
  Italic from +7.3 to +0.3.

**Two negative results, both caught on the probe and neither shipped:**
- Reading the edge 60 units down the italic's CURVED diagonal misses the join
  by ~4 units.
- Reading at 0.85 of the full bar depth missed the italic's tapered end face,
  and the correction ran away to W 0.55.

## Changed glyphs (glyf + hmtx)

| cut | changed |
|---|---|
| Regular | **0**: byte-identical |
| Italic | 5: `four onequarter threequarters uni2074 uni2084` |
| Bold | 36: all ten figures except the 1, and their 26 composites |
| BoldItalic | 36: all ten figures except the 1, and their 26 composites |

No contour count moved in any cut, and no non-figure glyph changed.

## Gates

- `./gates.sh`: **GATES UNCHANGED**. Approved glyphs are unchanged, the bench
  matches, and the contour census is unchanged.
- `cmp_contour_hairs --letters`: unchanged in all four cuts.
- Full sweep: unchanged in the Regular, Italic and Bold.
- **BoldItalic: +1, `uni2088` (the subscript 8), 153° at (132, 167), a 1-unit
  arm.** It is rounding, not drawing:
  - `uni2078`, the SUPERIOR 8, is the same outline 274 units higher; 162 of
    its 312 points differ from the subscript only by 1 unit of rounding, and
    at the same spot it reads 108°, which is clean.
  - Laddering the 8's waist overlap (0.10 / 0.20 / 0.30 / 0.35 / 0.45 / 0.50)
    left it at every rung.
  - It appears because the BoldItalic 8 changed through the 6's re-solved
    width, which is what sizes the 8's counters.
  - Recorded, not fixed. A fix would be in `symbols2.py` (`SUB_Y`) or the
    exporter, neither of which is mine.
- `cmp_touch`: under-floor and touching sets identical in all four cuts.
- `cmp_counter_dents` at 700: 0 / 0.
- `cmp_aldine_glitch`: identical sets.

## Checked and found CLEAN

- The Regular and Italic width solve is untouched, proved byte-identical.
- The Bold 5 at W 0.57 (the round-374 worry) sits +2.9% over its reachable
  target and renders unpinched (render 1).
- The superior and inferior 4s in the italic.

## OPEN — owner note, 2026-09-24: "italic numerals are not polished enough"

Recorded as a standing note, not yet a round. After rounds 372–378 fixed the
measured faults (baseline alignment, the 8's contrast and height, the 2's and
3's contrast, the width solver's slanted-ink bug, the 1's left bearing, the
4's weight, the 7's bar), the owner's eye still finds the ITALIC figures
unpolished. That is a finish judgment the instruments here have not captured:
every italic figure now passes weight, contrast, width, baseline, hair, touch
and dent checks, so the next pass must start from rendering the italic
figures large beside Flanker Griffo, Pagella and Poetica's figures and
reading them for curve quality, terminal finish, joins and rhythm — the same
kind of fault the ampersand showed (right proportions, faceted contour) —
rather than from another measurement table. Seen on the round-377 ampersand
and worth checking here first: FACETED OUTLINES where the others are smooth.
