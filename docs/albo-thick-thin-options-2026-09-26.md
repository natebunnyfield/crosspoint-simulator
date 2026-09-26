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
- **Status:** OPTIONS, awaiting the owner's picks. Record them in section 9.

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

**Recommended: c.** It is the smallest floor that clears q, p and d under the
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

**Recommended: c**, the smallest move that clears the n. Arm a, keeping his
ruling, is a sound pick too.

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

**Recommended: c.** It puts the Y and the x on the X's 0.90.

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

**Recommended: b.** The e was not flagged (−20%), so the smallest arm.

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

- the **3 at b** (floor 0.33);
- the **8 as shipped** (a), keeping his ruling and not darkening the darkest
  figure further;
- the **italic 6 at b** (0.45).

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

## 9. Owner picks

*(to be recorded here: one line per group, with the quote)*

| group | pick | quote | date |
|---|---|---|---|
| A italic bowls | | | |
| B italic s y | | | |
| C roman n h m | | | |
| D roman x k Y | | | |
| E roman e | | | |
| F figures 3 / 8 / 6 | | | |
