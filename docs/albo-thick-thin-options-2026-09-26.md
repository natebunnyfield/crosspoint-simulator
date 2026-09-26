# Albo round 394: thick and thin, second pass, as OPTIONS (2026-09-26)

Owner, 2026-09-26: *"take passes but show me options using full words and
sentences before committing"*.

This round is the second thick/thin rebalancing pass. It covers every letter
that round 391 flagged and then left alone
(`docs/albo-round-391-2026-09-25.md` section 4), plus the new outliers the
re-run found. **Nothing in the shipped font changes.** Each lever is an env
dial, and its default draws round 393's letter.

- **Baseline:** round 393 accepted (`b40737c`), all four cuts built by
  `build_env.sh albo_build_all`.
- **Units:** font units (x-height 429, cap 674). Italic numbers are measured
  unsheared.
- **Status:** OPTIONS, awaiting the owner's picks. Record them in section 10.

## 1. The instrument, and what it can and cannot see

`cmp_weight_survey.py --json` on the round-393 build, grouped by
`instruments/r391_thick_thin.py`. The same method as round 391:

- **thin** is p10 of the chamfer-ridge thickness;
- **cut** is thick / thin;
- **colour** is ink in the reading band divided by advance times reference height.

New this round is `tools/wedge_serif/instruments/r394_thin_map.py`. It has two
modes:

- `map` draws every ridge point under a threshold in red, so each letter's p10
  is located on the letter and not taken on trust.
- `measure` reports an arm's thin, cut and colour against the **as-shipped
  build's** family medians. That yardstick is fixed on purpose: a median
  recomputed over the arm itself moves with the arm, which is
  `albo-method.md` section 1f.

Where the ridge map puts each thin, at the 400:

| letter | where its thin is |
|---|---|
| italic q, d, a | the bowl's crown: ring-table keys 45 and 90, which are 22 and 20 units |
| italic p | the bowl's arm and bottom-left join (`B_RING` 25–28), plus the foot's tips |
| italic b | the bowl's left join (`B_BOWL_RING` 150 and 165, which are 17 and 18) |
| italic s | the head's turn and the bottom turn; `S_PEN_CON` 7.0 re-spreads the whole letter to 7:1 after it is drawn |
| italic y | the tail: Cancelleresca's 26-unit hairline, `Y_TAIL_W` |
| italic 6 | the tail's run-out to 0.12, and the ring's lower right |
| roman n h m | the arch's start at the join (`N_JOIN_TAPER` 0.22) |
| roman x | the light diagonal, `pw × 0.72` on a down-left stroke |
| roman k | the arm |
| roman Y | the light right arm, `pw × 0.72` |
| roman e | the **bar**. At the 400, pen × 0.66 is about 20 units, which is under the `S × 0.35` floor, so the bar ships AT the floor (23.4). The tail's tip is thinner still, but it is too short a run to set the p10 |
| roman 3 | where each bowl runs along the pen's thin: the upper bowl's rising top left and the lower bowl's bottom. Not the waist |
| roman 8 | the nib's thin, at the upper ring's 12 o'clock, the waist, and the lower ring's 6 o'clock |

**Instrument limit, found and not chased.** At the 700, several p10s are
**serif tips** and not strokes. This is so for the roman x (−55%), z (−43%)
and 1 (−51%), and for the italic 1 (−49%). The ridge runs out into each
wedge's point. On the roman x at the 700, arms b and c read 40.6 and 29.8 from
the same four tips, which is noise, not a regression (maps checked). No arm
was built for those 700 rows.

## 2. Re-run on round 393: what is flagged now

At the 400, these letters are more than 25% under their family:

- **roman:** y −36%, n −28%, t −29%, x −30%, k −31%, s −27%, 3 −27%, 8 −29%,
  and the capital **Y −28%** (new);
- **italic:** q −31%, d −25%, p −25%, s −28%, y −25%, o −26%, **a −28%**
  (new), 6 −30%, and m / n / r / h −31 to −37%.

The ones round 391 did not list:

- **roman Y (capital).** It is the same double thinning round 224 fixed on
  the capital X. Included in group D.
- **italic a.** It is the q's and d's ring (`A_RING`), with the same crown.
  Its contrast was ruled on 2026-09-15/16 (`ALBO_ALD_CON_A`), so it is offered
  on its own dial, as group A arm e.

These were left alone:

- **italic m n r h.** Round 391 already moved their hairline
  (`HM_ARCH_T` 22 → 26). Out of this pass's scope.
- **roman s t y.** Round 391 already floored them.
- **italic o.** `CON_O` is an owner ruling, and the o is not in scope.
- **the 700 rows** that are serif tips (section 1).
- **the italic g at the 700.** It reads −44%, but the g is an **approved
  letter** (`approved.py`) and was not touched. The bowl dial skips it by
  construction.
- **italic b.** It now reads −19%, under the 25% line, but it is kept in
  group A because it is the same construction.

## 3. The dials added (defaults draw round 393)

| dial | file | default | what it does |
|---|---|---|---|
| `ALBO_ALD_BOWL_HAIR` | `aldine.py` | 0 (off) | floors every key of the b, d, p and q ring tables at N units; never the g |
| `ALBO_ALD_A_HAIR` | `aldine.py` | 0 (off) | the same floor on the a's ring |
| `ALBO_ROM_LCX_THIN` | `diagonals.py` | 0.72 | the roman x's light diagonal, × the pen (`X_BL_THIN`) |
| `ALBO_ROM_K_ARM` | `diagonals.py` | unset (1.40) | the roman k's arm weight. It is roman-only, because the italic's λ is drawn through `g_k` and moved in the first build |
| `ALBO_ROM_Y_THIN` | `caps_straight.py` | 0.72 | the capital Y's light arm, × the pen |
| `ALBO_ROM_E_BAR_FLOOR` | `rounds.py` | 0.35 | the roman e bar's floor, × S. At or under stem 84 only (section 7) |
| `ALBO_FIG3_FLOOR` | `figures.py` | 0 (off) | a floor, × S, under the pen on both of the roman 3's strokes. It goes under the pen and not after the profile, so the waist still runs out to its point |
| `ALBO_FIG_8` = `y` / `z` | `figures.py` | ships `x` | the shipped `x` with the nib's thin raised from 0.15 to 0.22 / 0.30. `EIGHT_OPT_IT` maps y and z to the italic's own `x`, because a letter with no row resolves silently to option `a` |
| `ALBO_ALD_SIX_TAIL_END` | `figures.py` | 0 (off) | the italic 6's tail ends on this fraction of its width instead of running out to 0.12 |

Existing dials used unchanged: `ALBO_ALD_S_PEN_CON`, `ALBO_ALD_Y_TAIL_W`,
`ALBO_ROM_N_JOIN_TAPER`, `ALBO_ROM_N_JOIN_SPAN` and `ALBO_E_TAIL_R`.

**Default proof.** `cmp_outlines.py --advances` compared round 393's build
against the build with all of these dials at their defaults: **0 of 530
glyph outlines differ, and no advance differs**, on Regular, Italic, Bold and
BoldItalic. That was re-run after the last edit.

**Live proof.** `ladder.py` returned DIAL LIVE on every dial and every rung
offered: 2–4 distinct outlines each (Regular or Italic 400).

## 4. The groups, their arms and their numbers

Each cell reads **thin / cut / colour**, then the thin against the family
median, then the colour against it. Arm **a** is always as shipped.

### A. Italic bowls q p d b (primary), and the a

| arm | dial | q | p | d | b | a |
|---|---|---|---|---|---|---|
| a | as shipped | 27.1 / 2.67 (−31%) | 29.4 / 2.38 (−25%) | 29.4 / 2.38 (−25%) | 31.6 / 2.14 (−19%) | 23.3 / 3.19 (−28%) |
| b | `BOWL_HAIR` 26 | 29.4 / 2.46 (−25%) | 29.4 / 2.38 (−25%) | 33.1 / 2.16 (−16%) | 32.4 / 2.09 (−17%) | unchanged |
| **c** | `BOWL_HAIR` 30 | 32.4 / 2.30 (−17%) | 31.6 / 2.29 (−19%) | 36.1 / 2.00 (−8%) | 33.9 / 2.00 (−14%) | unchanged |
| d | `BOWL_HAIR` 34 | 36.1 / 2.12 (−8%) | 33.1 / 2.25 (−16%) | 38.4 / 1.88 (−2%) | 37.6 / 1.86 (−4%) | unchanged |
| e | `BOWL_HAIR` 30 + `A_HAIR` 30 | as c | as c | as c | as c | 31.6 / 2.36 (−2%) |

**At the 700:** q goes −42% → −33 / −26 / −19% on arms b / c / d, and d goes
−39% → −28 / −23 / −12%.

**Colour** rises by at most +0.017 (q, arm d). On arm c the change is +0.007
to +0.012.

**What each arm reverses:**

- No ruling set these ring tables' crown widths as such.
- `B_BOWL_RING`'s 150 and 165 keys (17 and 18) were round 135's fit to
  Pagella's hairline arm (*"match the middle stroke curve of pagella"*). Every
  arm lifts them, so the b's arm is less of a hairline than Pagella's.
- Arm e also moves the a, which reverses part of the a's contrast ruling
  (`CON_A`, 2026-09-15/16).

**The p barely moves.** It moves little because its p10 is shared with the
foot's tips (`PQ_FOOT_T` 21), which this dial does not touch.

**Recommended (revised, section 9): d.** Arm c, recommended first, is barely
visible at reading size (1.06% of pixels at 54 px). Originally: c is the smallest floor that clears q, p and d under the
25% line at the 400. The bowl's cut stays at 2.0–2.3, above the roman's
round-family 2.07, so the italic stays the more contrasted style. Arm d makes
the bowls read as monoline (b cut 1.86).

### B. Italic s and y

| arm | dial | s | y |
|---|---|---|---|
| a | as shipped: `S_PEN_CON` 7.0, `Y_TAIL_W` 26 | 23.3 / 2.55 (−28%) | 27.1 / 2.58 (−25%) |
| **b** | `S_PEN_CON` 5.5, `Y_TAIL_W` 30 | 25.2 / 2.45 (−22%) | 32.4 / 2.14 (−10%) |
| c | `S_PEN_CON` 4.5, `Y_TAIL_W` 34 | 29.0 / 2.18 (−10%) | 35.4 / 1.98 (−1%) |

**At the 700:** s goes −16% → −5 / +3%, and y goes −23% → −12 / −5%.

**Colour:** the s gains +0.003 / +0.007, and the y does not move.

**Spacing:** the s's fitted advance moves with its drawing, by +6 units on
arm b and +7 on arm c. That covers `s`, its five accented forms, and `st`
(U+FB06).

**What each arm reverses:**

- `Y_TAIL_W` 26 is the reference's hairline, taken on the owner's 2026-09-16
  ruling *"match y lowest brush stroke to the swoop of cancell"*. 30 and 34
  are heavier than Cancelleresca's.
- `S_PEN_CON` 7 came with the 2026-09-17 s pass (*"reduce the top line's
  visual weight, especially up its contrast"*). Lowering it gives some of
  that contrast back. `S_TOP` 0.86, the top line's own lightening, is not
  touched.

**Recommended: b.**

### C. Roman n h m join

| arm | dial | n | h | m |
|---|---|---|---|---|
| a | as shipped: taper 0.22 over 0.38 (round 232) | 24.5 / 2.95 (−28%) | 29.4 (−13%) | 29.4 (−13%) |
| b | 0.26 over 0.32, the pre-round-232 join | 28.6 / 2.53 (−16%) | 29.4 (−13%) | 27.1 (−20%) |
| **c** | 0.30 over 0.38 | 27.1 / 2.67 (−20%) | 30.1 (−11%) | 28.6 (−16%) |
| d | 0.34 over 0.38 | 29.4 / 2.49 (−13%) | 29.4 (−13%) | 29.4 (−13%) |

- **Colour:** changes by at most +0.003.
- **The 700:** the n does not move on arms c or d.

**What each arm reverses:** every arm except a gives back weight the owner
removed on purpose. Round 232 (R27 and R29) is quoted *"I wanted to slightly
reduce the weight of the joins"*. Arm b is exactly the join before that
round.

Arm b's shorter span measures the m **thinner** (−20%). Arm c keeps round
232's longer span and changes only the start width.

**Recommended (revised, section 9): a, as shipped.** No arm of this lever
moves the n, h or m by 1% of its ink on the outline; the p10 lift was the
crotch, not a visible stroke. (First recommendation was c.)

### D. Roman x, k, and the capital Y

| arm | dial | x | k | Y |
|---|---|---|---|---|
| a | as shipped: x 0.72, k arm 1.40, Y 0.72 | 26.3 / 2.49 (−30%) | 23.3 / 3.10 (−31%) | 27.1 / 2.75 (−28%) |
| b | 0.80, 1.55, 0.80 | 27.1 / 2.44 (−28%) | 24.1 / 2.97 (−29%) | 29.4 / 2.54 (−22%) |
| **c** | 0.90, 1.70, 0.90 | 30.1 / 2.20 (−20%) | 26.3 / 2.66 (−22%) | 32.4 / 2.30 (−14%) |

- **The 700:** k −15% → −4 / +4%, and Y −19% → −10 / +2%. The x's row there
  is serif tips (section 1).
- **Colour:** changes by +0.004 to +0.009.

**What each arm reverses:**

- **x:** the round-90 rulings are on the **bottom-left serif**
  (`X_BL_WEDGE` 1.15 and `X_BL_WIDTH` 1.0). At the 400 that wedge is sized on
  the thick diagonal and does not move with this dial, so no ruling is
  reversed at the 400. Above stem 84 the wedge's anchor interpolates toward
  the thin stroke, so the Bold's serif root moves slightly.
- **k:** the arm weight was raised by the owner's asks of 2026-09-13 (*"add
  some weight to the top right kick"*) and by round 92. These arms go further
  in the same direction.
- **Y:** there is no ruling on the thin arm. 0.90 is the value round 224 gave
  the capital X for the same fault.

**Recommended (revised, section 9): f.** Arms b and c are sub-pixel at the
phone's 2x. (First recommendation was c, which puts the Y and the x on the X's 0.90.)

### E. Roman e bar

| arm | dial | e (400) |
|---|---|---|
| a | as shipped: bar floor 0.35 S | 27.1 / 2.50 (−20%) |
| **b** | floor 0.40 S | 29.4 / 2.31 (−13%) |
| c | floor 0.45 S | 31.6 / 2.14 (−7%) |
| d | floor 0.45 S, exit end `E_TAIL_R` 0.55 | 31.6 / 2.14 (−7%) |

- **Colour:** +0.006 / +0.011 / +0.012.
- **The 700:** the bar floor applies only at or under stem 84 (section 7), so
  the Bold's e is identical on arms b and c. Arm d's exit end also reaches
  the Bold: e, æ and œ move, and its p10 stays at 49.7.
- **Spacing:** the fitter reads the new bar. The e's advance moves by 1 unit
  at most (arm b: e, æ and the accented e's −1; arms c and d: œ +1).

**What each arm reverses:**

- Round 92 thinned the bar (0.72 → 0.66 × the pen). It has never reached the
  400, because the floor binds there, so arms b and c reverse nothing ruled
  at that weight.
- Arm d thickens the **exit's end**. That goes against the owner's two asks
  to lighten the e's bottom-right stroke (round 94, then 2026-09-14, which is
  `E_ARM_THIN` 0.92).

**Recommended (revised, section 9): c.** Arm b, first recommended as the
smallest, is sub-pixel at 2x (0.72%).

### F. Figures: roman 3 and 8, italic 6

| arm | dial | 3 (roman) | 8 (roman) | 6 (italic) |
|---|---|---|---|---|
| a | as shipped: 3 on the pen alone, 8 `x`, 6 runs out | 23.3 / 2.94 (−27%) | 22.6 / 3.10 (−29%), colour 0.242 | 21.1 / 3.79 (−30%) |
| b | 3 floor 0.33, 8 `y`, 6 ends 0.45 | 27.1 / 2.53 (−15%) | 27.1 / 2.61 (−15%), 0.250 | 23.1 / 3.49 (−23%) |
| c | 3 floor 0.40, 8 `z`, 6 ends 0.60 | 30.1 / 2.27 (−6%) | 31.6 / 2.29 (−1%), 0.258 | 24.8 / 3.24 (−18%) |

**At the 700:**

- italic 6 −24% → −4 / +7%;
- 8 −30% → −17 / +4%;
- 3 −3% → −9 / +4%. The 3's arm b reads *thinner* at the 700. Its outline
  does get the floor, so this is a ridge-sampling shift, not a lost stroke.

**The italic 8 moves with the 6 in arms b and c.** It is solved onto the 6's
line (`to_six='shipped'`, round 374). The 8's own dial is roman-only and was
proven to leave the italic identical.

**What each arm reverses:**

- **The 8's thin is an owner ruling:** round 373, *"8: cut deeper wins"*, then
  round 374's `x`. The 8 is also already the darkest figure (colour +57% over
  the figures' median), and arms y and z darken it further (+62% / +67%).
- **The 3's shipped `g`** (round 374) is about its upper bowl's width, not its
  weight, so the floor does not reverse it.
- **The italic 6's run-out** is the shape round 211 drew. The roman 6 ships a
  pen cut at 0.30 (`i`, owner, round 250).
- **The italic 6's ring** carries `FIG_CON` 1.8, which is shared with the
  italic 0 and 9. Lifting the 6's ring alone would part it from them, so it is
  not offered. Only the tail is.

**Recommended, per figure (the dials are independent):**

- the **3 at c** (floor 0.40; revised from b, which is sub-pixel at 2x, section 9);
- the **8 as shipped** (a), keeping his ruling and not darkening the darkest
  figure further;
- the **italic 6 at c** (0.60; revised from b, section 9).

## 5. Gates, every arm, all four cuts

Each arm was built as all four cuts, with that arm's env on top of
`build_env.sh`.

| gate | result on every arm (A b–e, B b–c, C b–d, D b–c, E b–d, F b–c) |
|---|---|
| `cmp_touch.py` | 0 touching, 0 below the floor, on all four cuts. Exempt counts 6 / 7, as shipped |
| `cmp_contour_hairs.py --letters` | exit 0 on all four cuts |
| `cmp_counter_dents.py` | only the Regular `&` (the drawn exception, 630 / 7.9), as shipped; 0 on the other three |
| `approved.py --check` | both approved g's unchanged |
| `cmp_aldine_glitch.py --ttf --all` | the finding set is identical to round 393's on every cut |

On the default code, `gates.sh` reports **GATES UNCHANGED**. It also reports
`build.py matches the bench` and `contour census unchanged (1056 glyphs)`.

`gen_state.py` was regenerated. `ALBO_ROM_K_ARM` does not appear in its
table, because it is read with an `if os.environ.get`, not with a
`float(os.environ.get(...))` default.

**Outlines moved per arm, against round 393** (`cmp_outlines.py`):

| group | cuts | glyphs that moved |
|---|---|---|
| A | Italic and BoldItalic | b, d, đ, p, q, U+E000 (fb). Arm e adds a, æ, ª |
| B | Italic and BoldItalic | s and its 5 accented forms, U+FB06 (st), y. Advances: the s family |
| C | Regular and Bold | n, h, m, ħ, ŋ, η, ⁿ, U+E001, U+E005, and ń in the Regular |
| D | Regular and Bold | x, k, ĸ, U+E003, Y, ¥. Italic λ identical after the roman-only gate |
| E | Regular (arm d also Bold) | e, æ, œ, and the accented e's that follow; advances within 1 unit |
| F | all four cuts | 3 or 6 and 8, their super- and subscripts, and the fractions that carry them |

## 6. The proof

Session scratch `tt2/`, `index.html` with `img/`. The images are lossless
PNG, 700 px wide. For each group:

- a zoom: key words at 27 px, 3× nearest-neighbor, one row per arm;
- one image per arm: the group's sentence plus long words, at 27 px shown 2×
  nearest-neighbor and again at 54 px native, labeled with the arm's letter.
  "a - as shipped" is always first.

The sentences are full English, rich in the group's letters:

- *"A quiet bride dipped a pale quill…"*
- *"Sixty yellow yachts sway lazily…"*
- *"In the moonlit hamlet the ninth man hummed a haunting hymn…"*
- *"Young Kiki kept six waxed kayaks…"*
- *"Every evening the eleven needle-makers…"*
- *"In 1838 the 36 ships left port…"*

**Effect against each group's arm a:** the mean absolute pixel difference is
0.3–2.1 levels. Between 0.6% and 3.5% of pixels move by more than 4 levels.

Group B re-flows, because the s's advance moves. At page scale these are
tenths of a pixel, as round 391 found, and the zoom row is where they show.

## 7. Negative results and traps found this round

- **The e's bar multiplier is dead at the 400.** Round 92's 0.66, and 0.72 or
  0.78 in its place, all build the Regular e outline-identical (0 of 530),
  because `S × 0.35` binds. The live lever is the floor itself.
- **A 0.45 bar floor at the 700 made the e thinner.** p10 went from 49.7 to
  42.1: a new sliver where the heavier bar meets the ring, not a lift.
  `E_BAR_FLOOR` therefore applies only at or under stem 84, and the Bold is
  identical on arms b and c.
- **`E_TAIL_R` does not move the e's p10.** 0.55 and 0.70 both read 27.1.
  The tail's tip is too short a run to set the 10th percentile. It moves
  colour by +0.001–0.002 only.
- **`ALBO_FIG_8=y` without an italic row would have drawn the italic 8 as
  option `a`.** `OPT()` resolves a letter with no row in a table to `a`,
  silently. Fixed by aliasing y and z to the italic's shipped `x`, and proven
  outline-identical.
- **`ALBO_ROM_K_ARM` moved the italic λ.** It is drawn through the roman
  `g_k`. The dial is now roman-only (`not pen.ITALIC`).
- **`pen_widths(..., floor=)` applies the floor AFTER the profile.** On the
  3 it would have lifted the waist's taper-to-0.04, so the 3's floor is
  applied under the pen and the profile multiplied over it.
- **Group families.** q, p, d and b sit in the STEM family (median 39.2)
  because of their stems, while their thin is a bowl. Against the italic's
  ROUND median (32.4) they read q −16%, d and p −9% as shipped. Both are
  honest, and this pass uses round 391's map so the numbers compare.

## 8. Checked and found clean (do not re-open)

- **The approved g's.** Not reachable by any dial here: `_hair` is applied
  inside a_a / a_b / a_d / a_p / a_q only. `approved.py` is green on every arm.
- **The roman z at the 700 (−43%), the roman x at the 700 (−55%), and the
  roman and italic 1 at the 700 (−51 / −49%).** These are serif-tip ridges
  (maps checked). No stroke is thin.
- **The italic BoldItalic r (−50%).** Serif tips plus its arm. Round 391
  recorded it and did not chase it, and neither does this round.
- **The italic 6's ring.** Its thin is `FIG_CON`, which is shared with the
  italic 0 and 9 (section 4F).

## 9. Rework: "i dont see differences in thick thin" (2026-09-26)

Owner, on the published page: *"i dont see differences in thick thin"*. Taken
at face value, and he was right. The first page compared stacked sentence
rows, and most arms change a fraction of a pixel.

**The mechanism.**

- The p10 moves are real on the outline, but small in ink. On arm c, the q's
  hairline goes from 27 to 32 units, which is 0.14 px at a 27 px em.
- The renderer then quantizes it. On this font, FreeType's default load, as
  used by PIL and by the reader's converter (`fontconvert_sdcard.py`
  `FT_LOAD_RENDER`, read, not changed), behaves exactly like
  `FT_LOAD_FORCE_AUTOHINT`: stems snap to the pixel grid. A sub-pixel change
  therefore either vanishes or jumps a whole pixel column.
- Measured on the roman n (arm C b): the outline's ink moves +0.4%. The
  FreeType 54 px render moves +10.2%, because one column of the right stem
  flips. The hinted 27 px render moves +0.2%.

**The new instrument.** `tools/wedge_serif/instruments/r394_visibility.py`
reports both numbers per letter: `geo` (outline ink, unhinted) and `ft`
(FreeType at 27 px and 54 px).

**Visibility per arm.** Two measures, both against arm a:

- **27 px / 54 px:** pixels changed by more than 8 levels, as a share of the
  whole sentence block. The block is FreeType-rendered, with every glyph at
  arm a's positions so spacing shifts do not count. The measure is diluted by
  the letters an arm does not touch.
- **letter ink (geo):** each affected letter's ink change on the outline.

Under 1% at 54 px is called **sub-pixel at reading size**.

| arm | 27 px | 54 px | letter ink (geo) | verdict |
|---|---|---|---|---|
| A b | 0.25% | 0.23% | q +1.1, p +0.2, d +1.1, b +1.6 | sub-pixel |
| A c | 0.80% | 1.06% | q +2.7, p +2.1, d +2.4, b +2.7 | barely |
| A d | 0.94% | 1.61% | q +4.2, p +4.2, d +3.6, b +4.3 | visible |
| A e | 0.92% | 1.15% | as c, plus a +2.2 | barely |
| **A f (strong, floor 44)** | 1.49% | 1.01% | q +9.4, p +10.5, d +8.4, b +10.1 | visible in the close-up and the difference figure; cut 1.55–1.8 |
| B b | 1.94% | 1.55% | s +4.7, y +2.8 | visible |
| B c | 3.56% | 1.89% | s +7.2, y +5.5 | visible |
| **B f (strong: s 4.5, y tail 42)** | 3.52% | 1.94% | s +7.2, y +10.8 | visible |
| C b | 0.39% | 1.04% | n +0.4, h +0.6, m +0.6 | sub-pixel (the 54 px figure is grid snapping, not ink) |
| C c | 0.44% | 1.18% | n −0.1, h +0.9, m 0.0 | sub-pixel |
| C d | 0.59% | 1.02% | n +0.3, h +0.1, m +0.1 | sub-pixel |
| C strong | — | — | taper 1.0 (the lever's maximum): n +0.05%, h +1.0% | **none possible**, skipped |
| D b | 1.03% | 0.70% | x +2.0, k +0.1, Y +1.3 | sub-pixel |
| D c | 1.16% | 0.98% | x +4.3, k +0.9, Y +3.2 | sub-pixel |
| **D f (strong: x 1.0, k arm 2.5, Y 1.0)** | 1.23% | 1.04% | x +6.5, k +5.5, Y +5.4 | visible at 27 px ×2 (Y's arm and k's arm plainly heavier) |
| E b | 0.49% | 0.72% | e +2.1 | sub-pixel |
| E c | 0.77% | 2.18% | e +3.9 | visible |
| E d | 0.93% | 2.22% | e +4.6 | visible |
| **E f (strong, bar floor 0.60)** | 0.82% | 2.15% | e +9.7 | visible |
| F b | 1.42% | 1.08% | 3 +1.4, 8 +4.2, 6 +1.8 | small |
| F c | 2.05% | 1.41% | 3 +2.6, 8 +7.9, 6 +2.4 | visible |
| **F f (strong: 3 floor 0.55, 8 nib thin 0.45, 6 ends 0.90)** | 2.11% | 1.58% | 3 +6.0, 8 +15.5, 6 +4.0 | visible |

A block-level number can read lower for a stronger arm (A f at 54 px),
because an arm can also move a glyph's outline position by a fraction of a
pixel. The fitter then snaps differently. The per-letter `geo` column is the
thickness.

**The strong arms, all gates green.** For every f arm on all four cuts:

- `cmp_touch` 0 / 0;
- hairs `--letters` exit 0;
- counter dents as shipped;
- `approved.py` unchanged;
- glitch finding set identical to round 393's.

They use existing dials only, so there are no code changes and the defaults
are still outline-identical: re-proven, 0 of 530 on all four cuts.

The F strong arm sets the 8 through the existing `ALBO_8_NIB`
(`"1.03,0.45,0"`) on the **roman builds only**, because that env var would
also reach the italic 8.

**Skipped, and why:**

- **The s past arm c's 4.5:1.** At `S_PEN_CON` 4.0 the Bold Italic `st`
  (U+FB06) PINCHes to 2.2 units, and at 3.0 it SPLITs. Both are new glitch
  findings. B f keeps the s at 4.5 and strengthens only the y.
- **A strong C.** The join lever has no visible range at all, because the
  arch starts inside the stem. Making the n's join heavier would take a
  different model (the crotch, not the taper), against the round-232 ruling.
  It is not built.

**The page, reworked in place** (scratch `tt2/index.html`). Each group now
has:

- a visibility table, then the recommendation;
- a 160 px close-up: each arm's letters filled, then overlaid on arm a, with
  ink added in blue and arm a's outline in red;
- the key-word zoom;
- each arm's sentence image with a **difference figure directly under it**:
  27 px ×3, arm a in gray, ink the arm adds in blue, ink it removes in red.
  Any change over about 2% coverage is drawn at full strength.

Group C's strong arm is absent by the finding above.

## 9b. The slider page (2026-09-26)

Owner: *"present this in an interactive way so i can slide between full
range"*.

**The generator.** `tools/wedge_serif/instruments/r394_slider_frames.py`
builds one slider per independent dial:

- every step is built at the 400 and the 700, gated, measured and rendered by
  FreeType;
- each step becomes one composite PNG: the sentence at 27 px shown 2×, the
  same at 54 px, the key-word difference against as shipped, and a 220 px
  overlay of the affected letters;
- the data are inlined into `index.html`.

A step that fails a gate is kept and flagged. **Copy picks** emits
`{env var: value}`, where `null` means as shipped. The page has 124 files
(123 frames and the HTML) and weighs 13 MB.

**The dials.** Each row gives the dial's environment variable, its steps, the
shipped step (S) and the recommended step (R). A floor cannot go lighter than
shipped, so a floor slider starts at its shipped 0.

| slider | env | steps | S | R | gate edge found |
|---|---|---|---|---|---|
| A bowls q p d b | `ALBO_ALD_BOWL_HAIR` | 0 22 26 30 34 38 42 46 50 | 0 | 34 | none |
| A the a | `ALBO_ALD_A_HAIR` | 0 22 26 30 34 38 42 46 50 | 0 | 0 | none |
| B s contrast | `ALBO_ALD_S_PEN_CON` | 9 8 7 6.5 6 5.5 5 4.5 4 3.5 3 | 7.0 | 5.5 | 4.0 and 3.5: Bold Italic st PINCH; 3.0: SPLIT |
| B y tail | `ALBO_ALD_Y_TAIL_W` | 18 22 26 30 34 38 42 46 50 | 26 | 30 | none. The thin stroke stops rising past 38, because the p10 moves off the tail |
| C join | `ALBO_ROM_N_JOIN_TAPER` | 0.10 0.16 0.22 0.26 0.30 0.40 0.55 0.75 1.00 | 0.22 | 0.22 | none. The n's ink moves under ±0.2% over the whole range |
| D x | `ALBO_ROM_LCX_THIN` | 0.56 0.60 0.66 0.72 0.80 0.90 1.00 1.10 1.20 | 0.72 | 1.00 | 0.56 to 0.66: the Bold x SPLITs (its bottom-left serif detaches) |
| D k arm | `ALBO_ROM_K_ARM` | 1.10 1.25 1.40 1.55 1.70 1.85 2.00 2.25 2.50 2.75 | 1.40 | 2.50 | none |
| D Y | `ALBO_ROM_Y_THIN` | 0.56 0.60 0.66 0.72 0.80 0.90 1.00 1.10 1.20 | 0.72 | 1.00 | none |
| E bar | `ALBO_ROM_E_BAR_FLOOR` | 0.30 0.35 0.40 0.45 0.50 0.55 0.60 0.65 0.70 | 0.35 | 0.45 | none |
| E exit | `ALBO_E_TAIL_R` | 0.25 0.30 0.35 0.40 0.45 0.55 0.65 0.75 0.85 | 0.40 | 0.40 | none. The e's ink moves at most ±2% over the whole range |
| F 3 | `ALBO_FIG3_FLOOR` | 0 0.25 0.30 0.33 0.36 0.40 0.45 0.50 0.55 0.60 | 0 | 0.40 | none |
| F 8 | `ALBO_8_NIB` (thin in `"1.03,t,0"`, roman builds only) | 0.08 0.11 0.15 0.19 0.22 0.26 0.30 0.35 0.40 0.45 0.50 | 0.15 | 0.15 | none |
| F italic 6 | `ALBO_ALD_SIX_TAIL_END` | 0.06 0.12 0.20 0.30 0.45 0.60 0.75 0.90 1.00 | 0.12 (unset) | 0.60 | none |

**Reading the pixel figures.** The pixels-changed numbers are over the whole
sentence block, so a dial whose letter is rare there reads low. The Y is the
clearest case: its arm at 1.20 adds 9.4% to the letter's ink, and the block
still reads 0.1%. The per-letter ink change is the figure to judge by.

**Bold x at 0.56 to 0.66 is a new negative result.** Under 0.72 the Bold x's
bottom-left serif separates from its thin stroke. That is round 90's anchor
problem again (`x_bl_anchor`), now reached from below.

## 10. Owner picks

*(to be recorded here: one line per group, with the quote)*

| group | pick | quote | date |
|---|---|---|---|
| A italic bowls | | | |
| B italic s y | | | |
| C roman n h m | | | |
| D roman x k Y | | | |
| E roman e | | | |
| F figures 3 / 8 / 6 | | | |
