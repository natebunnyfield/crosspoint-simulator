# Albo's roman e read as o: traced (2026-09-26)

> **RULING, 2026-09-26: "Ship A".** Arm A is the default as of round 400
> (`docs/albo-round-400-2026-09-26.md`).
> - **The change:** `ALBO_ROM_E_BAR_TOP` 0.585 in `rounds.py`; his 0.45 floor
>   is kept. The dials from `etrace/e_arms.patch` are now in the live tree.
> - **The gate:** `etrace/e_hint_gate.py` runs on the Regular in `gates.sh`.
> - **Round 400 Regular:** Vision **3** e>o (round 399: 136), Tesseract 0.
>   Only `e ae oe` moved; advances and kerning are unchanged.
> - **The Bold does not take the dial:** its e is unchanged, reads 7 e>o, and
>   is not gated (the limit is calibrated on the 400).

Owner, on the finding in `docs/spacing-tools-survey-2026-09-26.md` §4b:
*"Trace it, show options."* The Kept Legibility Index's reader (Apple Vision)
reads Albo's roman **e as o 131 times in round 397** and 117 in round 395,
against 6 in the 2026-09-20 font. Georgia, Charter and Times read 0.

- **Surveyed:** every commit touching `tools/wedge_serif` from `8ce01d5`
  (the commit that built `bench/fonts-2026-09-20/`, verified: 0 of 486
  outlines and advances differ) to `c25375b` (round 397).
- **Built from `git archive` snapshots** in the session scratchpad, never the
  live tree, with `build_env.sh`'s roman recipe (`FJORD_STEM=66.9
  FJORD_CONTRAST=0.892`). The round-397 rebuild matches
  `bench/fonts-2026-09-26-r397/` (0 of 530 differ).
- **Units:** font units, upem 1000, x-height 429.
- **How sure:** each finding is tagged [measured] or [inferred].

## 1. Answer

**Cause:** round 395 (`95bf547`), dial `ALBO_ROM_E_BAR_FLOOR` 0.35 → **0.45**,
`tools/wedge_serif/outlines/glyphs/rounds.py:232`, applied at `rounds.py:345`
(`th = max(pen.th(E_DEG) * e_th, S * E_BAR_FLOOR)`). That is the owner's own
pick from the round-394 slider page.

**But not because the bar is thicker.** [measured] The e is drawn with no
hinting bytecode, so FreeType's default load (what the index's renderer and
the firmware's converter both ask for) runs the **autohinter**. On this one
outline the autohinter pulls the e's bar and upper bowl **down 0.23–0.34 px
at 9–12 ppem**, where every neighboring outline is pushed up 0.03–0.08 px.
That inks the one pixel row that was the e's mouth, and the letter becomes a
closed ring. The flip is a knife edge in outline coordinates:

| bar floor | 0.44 | 0.445 | 0.448 | **0.449** | **0.45** | 0.451 | 0.455 | 0.48 | 0.52 |
|---|---|---|---|---|---|---|---|---|---|
| hint gate | ok | ok | ok | **FAIL** | **FAIL** | ok | ok | ok | ok |

A 0.13-unit window around the owner's pick fails and everything around it
passes. So any e outline edit can land in a window like this, and the right
defense is a gate, not a dial (§6).

**Where it matters:** [measured] only at **8–9.75 ppem**. The reader draws
Albo at 16.7 ppem and up (8 pt at 150 dpi, `sd-fonts.yaml` sizes 8–18), and
at every reader size the mouth is clear (§3). **The device is not affected.**
The index is, because its body cells read 9 px text.

**Recommendation:** Arm A, bar top **0.58 → 0.585** of the x-height, plus the
gate. Section 5.

## 2. Bisection [measured]

### 2a. Confirming the finding: a second run and a second reader

`tools/wedge_serif/etrace/kli_e.py` runs the index's own v3.1 protocol
(`bench_v31.run`: same corpus, 12 conditions, 8 repetitions, same seeds), then
counts with the index's own `confusions_from_raw` reduction.

- **Second run:** reproduces the survey exactly: 6 / 117 / 131. The render is
  seeded and Vision is deterministic on identical images, so a repeat run is a
  check of the pipeline, not of noise.
- **Second instrument:** Tesseract 5 (LSTM, `--psm 6`) on the SAME images,
  upscaled 4× Lanczos (it cannot read a 9 px em at all). A different model
  family. It agrees on the direction: **0 / 16 / 20**.
- **Where the errors are:** body-9px and body-9px-blur. In round 397 that is
  57 and 67 of the 168 e's in each cell, 34% and 40%. body-12px: 0.

| font | Vision e>o | Tesseract e>o | grand | crowded |
|---|---|---|---|---|
| 09-20 bench (`8ce01d5`) | 6 | 0 | 89.1 | 68.0 |
| r393 (`6ce1562`) | 4 | 0 | 87.7 | 53.0 |
| r394 (`03945f1`, dials only) | 4 | 0 | 87.7 | 53.0 |
| **r395 (`95bf547`)** | **117** | **16** | 87.5 | 52.6 |
| **r397 (`c25375b`)** | **131** | **20** | 88.1 | 63.5 |
| Georgia | 0 | 0 | 94.0 | 91.7 |
| Charter | 0 | 0 | 94.8 | 99.3 |

### 2b. Every commit in the range

`etrace/bisect_all.sh` built the Regular at every one of the 117 commits
touching `tools/wedge_serif` from `8ce01d5` to `c25375b`, all 117 built, and
ran the hint gate (§6) on each (`etrace/results/bisect.tsv`). The e's
DRAWING was hashed with its left bearing taken out, so a spacing round does
not read as a redraw:

| commits | e drawing | hint gate |
|---|---|---|
| `8ce01d5` (09-20 bench) … `66da73a` (round 394 page), 109 commits | one drawing, unchanged | ok (0.05–0.13) |
| **`95bf547` round 395** … `c25375b` round 397, 8 commits | the round-395 drawing | **FAIL** (0.23–0.26) |

The e's drawing changed ONCE in the range, at round 395, and the gate flips
with it. The index was then spent where it can tell something: on
`8ce01d5`, round 393, round 394, round 395 and round 397 (§2a).

### 2c. Inside round 395: the dial toggle

Round 395 changed ten defaults; only `ALBO_ROM_E_BAR_FLOOR` reaches the roman
e (the others draw the italic, x, Y, 3 and 8). Round 395 rebuilt with
`ALBO_ROM_E_BAR_FLOOR=0.35` puts `e`, `ae`, `oe` back to round 393 exactly
(`cmp_outlines`; only the x, Y, 3, 8 family still differ) and reads **4**
e>o, Tesseract 0. On round 397 the same toggle reads 6. The floor is the
whole cause, and the spacing rounds after it (396, 397) add only 117 → 131.

## 3. Mechanism [measured]

`tools/wedge_serif/etrace/e_mechanism.py`.

### 3a. In design units (FreeType unhinted, 1000 ppem)

| floor | bar at eye column | bar underside | eye height | mouth (widest disc that gets out) | white above terminal tip |
|---|---|---|---|---|---|
| 0.35 (r393, 09-20) | 26 | 224 | 160 | 148 | 158 |
| 0.42 | 31 | 219 | 160 | 144 | 153 |
| 0.44 | 32 | 218 | 159 | 143 | 152 |
| **0.45 (today)** | 33 | 217 | 159 | 141 | 151 |
| 0.48 | 35 | 215 | 160 | 140 | 149 |

The floor grows the bar DOWNWARD from a fixed top (`bar_top = xh × 0.58`,
`under = bar_top − th`, `rounds.py:346-347`), so each 0.01 of floor takes
about 0.7 units off the mouth. The drawing moves smoothly from 0.42 to 0.48,
and 0.48 has less mouth than 0.45 yet reads clean. **Ink mass is not the
cause.**

### 3b. As rendered

The mouth band (between the terminal's top at 83 and the bar's underside at
217) is 1.2 px tall at 9 ppem, so the letter's identity rides on ONE pixel
row. The autohinter's move of the bar's underside (px, + = up):

| floor | 8 | 9 | 9.5 | 10 | 12 | 16.7 | 27.1 | 33.3 |
|---|---|---|---|---|---|---|---|---|
| 0.35 | +0.31 | +0.08 | −0.03 | +0.38 | −0.08 | +0.45 | +0.19 | +0.36 |
| **0.45** | −0.03 | **−0.23** | **−0.34** | +0.08 | **−0.34** | +0.28 | +0.17 | +0.34 |
| 0.48 | +0.28 | +0.08 | −0.03 | +0.38 | −0.06 | +0.44 | +0.22 | +0.36 |

`mouth_block` (0 = one row runs clear from the center to the outside, 1 =
sealed by full ink), autohinted as the index renders:

| floor | 8 | 9 | 9 + blur 0.6 | 9.5 | 10 | 16.7 (2-bit) | 27.1 (2-bit) |
|---|---|---|---|---|---|---|---|
| 0.35 | 0.00 | 0.07 | 0.18 | 0.00 | 0.02 | 0 | 0 |
| 0.44 | 0.02 | 0.08 | 0.20 | 0.00 | 0.02 | 0 | 0 |
| **0.45** | **0.22** | **0.23** | **0.29** | **0.21** | 0.00 | 0 | 0 |
| 0.48 | 0.04 | 0.10 | 0.21 | 0.00 | 0.02 | 0 | 0 |

The proof page shows the 9 ppem e of each build 16× nearest: the clean
builds are a `c` with a bar, the failing ones a ring.

- **It is the autohinter:** [measured] default loading equals
  `FT_LOAD_FORCE_AUTOHINT` bit for bit, and `FT_LOAD_NO_AUTOHINT` equals
  `FT_LOAD_NO_HINTING`. Unhinted, 0.42 and 0.45 render nearly the same 9 px e.
  FreeType 2.13.2.
- **It is local to the e:** [measured] the other 25 lowercase render
  identically between 0.45 and 0.445 / 0.455 at 9, 12, 16.7 and 27.1 ppem.
  The e is not moving the font's blue zones.
- **Which hinter decision flips** is not traced inside FreeType's `af_latin`.
  [inferred] The on-curve points along the bar's underside near its right
  join are placed differently by the curve fitter at 0.45 (`401,231` →
  `453,235` against `379,230` → `412,233` → `453,236` at 0.44), which is the
  kind of change that makes the autohinter link a different pair of edges.

### 3c. Across sizes, with the same reader

`etrace/size_sweep.py`, the index's corpus and renderer, 4 repetitions per
cell, e>o:

| em px | 8 | 8.5 | 9 | 9.5 | 10–13 |
|---|---|---|---|---|---|
| 0.35, clean / blur | 0 / 0 | 0 / 0 | 0 / 1 | 0 / 0 | 0 |
| 0.42, clean / blur | 0 / 0 | 0 / 0 | 0 / 1 | 0 / 0 | 0 |
| **0.45**, clean / blur | **18 / 6** | **27 / 21** | **30 / 34** | **11 / 12** | 0 |
| Georgia, clean / blur | 0 / 1 | 0 / 0 | 0 / 0 | 0 / 0 | 0 |

It is not a single-size grid accident: it holds over 8–9.5 px and stops at
10. The reader's smallest Albo size is 16.7 ppem.

## 4. Options

Two new dials in `tools/wedge_serif/etrace/e_arms.patch` (applies to HEAD's
`rounds.py`, which is unchanged since `95bf547`; not applied to the live
tree). Both default to today: 0 of 530 outlines move.

- `ALBO_ROM_E_BAR_TOP`: the bar's top, × x-height (default round 92's 0.58).
- `ALBO_ROM_E_BAR_TAPER`: the underside rises toward the mouth end by this
  fraction of the bar (default 0).

The terminal arms use the existing `ALBO_E_TIPX_R` (0.92) and `ALBO_E_TIPY_R`
(0.19). Everything is roman, stem ≤ 84, like the floor itself.

| arm | dial | keeps his 0.45? | Vision e>o | Tess e>o | grand | crowded | gate |
|---|---|---|---|---|---|---|---|
| today | — | yes | 131 | 20 | 88.1 | 63.5 | FAIL 0.235 |
| **A** | bar top 0.585 | **yes** | **4** | 0 | 88.9 | 67.0 | ok 0.078 |
| A2 | bar top 0.596 | yes | 4 | 0 | 88.7 | 64.4 | ok 0.067 |
| F | floor 0.455 | **no, +0.005** | 4 | 0 | 88.9 | 67.0 | ok 0.102 |
| C | tip x 0.88 | yes | 4 | 0 | 88.9 | 67.0 | ok 0.110 |
| B | taper 0.5 | yes | 76 | 8 | 88.3 | 63.6 | FAIL 0.212 |
| C′ | tip x 0.84 | yes | 132 | 21 | 88.1 | 63.5 | FAIL 0.239 |
| D | tip y 0.15 | yes | 9 (+33 e>c) | 0 | 88.1 | 59.7 | FAIL at 8.75–9 |

- **A: raise the bar 2 units.** The floor's thickness stays exactly his
  0.45; the bar sits 2.1 units higher, so the eye loses 2 units (159 → 157)
  and the mouth gains 2 (141 → 144). It moves `e`, `ae`, `oe` only. The
  advance and bounding box are unchanged, so **B2 needs nothing**.
  Neighbors 0.583 / 0.587 / 0.59 / 0.593 / 0.6 / 0.61 all pass the gate, and
  so does 0.585 with the floor at 0.44 / 0.45 / 0.46. 0.575 passes, but
  **0.58, today's value, fails**.
- **A2: grow the bar upward instead.** At 0.596 the underside returns to
  where 0.35 had it (224), the eye loses 7 units (159 → 152), and the
  accent composites shift their marks by 1 unit (acute `112 → 111`). The
  e's advance moves 494 → 493 and xMax 453 → 452, which is under the kern
  quantum (1.16 units on the phone), so B2 needs nothing.
- **F: move his number by 0.005.** 0.33 units of bar, invisible at any size.
  It is still a change to his pick, so it is labeled. 0.451 is the smallest
  passing step. It is the arm most exposed to the knife edge: 0.449 fails.
- **C: shorten the exit terminal.** It keeps the floor, but it moves round
  110's tip (0.92) and it is fragile: 0.86 / 0.87 / 0.88 / 0.89 / 0.91 pass,
  and **0.84 / 0.90 / 0.93 / 0.94 fail**.
- **B (taper) does not fix it**, and **D (a lower terminal) half-fixes it**
  but trades it for 33 `e>c`. They are recorded as negatives.

Gates on A, A2, F and C (`c25375b`'s own scripts):

- `cmp_touch.py`: 0 touching, 0 below the floor, 6 exempt (same as today).
- `cmp_contour_hairs.py`: full and `--letters` both exit 0.
- `cmp_counter_dents.py`: only the documented `&`.
- `approved.py --check`: both approved g's unchanged. **The g's do not
  move.**
- `cmp_outlines.py`: A and F move `e ae oe`. C moves `e ae oe egrave`. A2 moves
  `e ae oe` plus 7 accent composites by 1 unit.

## 5. Recommendation

**Arm A at 0.585, plus the gate.**

- It is the smallest change that keeps his 0.45 exactly.
- It has the widest measured margin of the four passing arms.
- It recovers the index's crowded cell (63.5 → 67.0) and grand mean
  (88.1 → 88.9).

It changes nothing a reader can see at 27 or 54 px (proof page, rows 3–4),
and **nothing on the device**, which never draws Albo below 16.7 ppem.
If the owner prefers no change at all, that is defensible on the device. In
that case, ship the gate alone, so that the next e edit that lands in such a
window is caught.

**Not built, and the owner's call:** give Albo real hinting (ttfautohint
bytecode at export) or have the converter load it with `FT_LOAD_NO_HINTING`.
Either removes the autohinter's decision from every glyph, not only the e. It
is a font-wide architectural change and is not measured here.

## 6. The gate

`tools/wedge_serif/etrace/e_hint_gate.py FONT.ttf` renders the roman e as the
index does at every quarter ppem from 8 to 12, and fails when `mouth_block`
exceeds 0.15.

- **Albo readings:** clean builds read 0.05–0.13. The failing ones read
  0.20–0.26 over 8–9.75 ppem.
- **Checked against both readers** on all 17 builds the index read (§2a, §2c,
  §4). The gate passes every build that Vision reads at 4–6 e>o and
  Tesseract at 0 (13 builds). It fails every build that Vision reads at
  76–132 (4 builds). The one build between those, D, reads 9 e>o and 33 e>c,
  and the gate fails it at 8.75–9 ppem only.
- **Not a general legibility measure.** It is calibrated on Albo's e only.
  Georgia and Times FAIL it while reading 0 e>o, because their e's mouth is
  not in Albo's place.
- **Wired into `gates.sh` in round 400** (Regular only). The gate was
  rewritten there to need only numpy and freetype.

## 7. Checked and found clean

- **The italic:** 8 e>o in round 397 (the survey's run, not re-run here),
  the same order as the 09-20 roman. The floor does not reach it: the italic
  branch of `rounds.py:345` is a fixed 0.35.
- **The Bold:** the floor applies at or under stem 84 only (round 395 §3), so
  the Bold e did not move.
- **Round 394:** added dials only. Its build is identical in e>o (4) to
  round 393.
- **The spacing rounds 396–397 (B2):** they do not move the e's drawing.
  They move e>o 117 → 131 through placement, and the crowded cell
  52.6 → 63.5.
- **Other letters' hinting:** not disturbed by the e (§3b).
- **The reader's sizes:** `mouth_block` 0 at 16.7 and 27.1 ppem, 2-bit,
  every build.

## 8. Not verified

- The flip was not traced inside FreeType's autohinter (§3b, inferred).
- Device feel: nothing to feel; the device sizes are measured clean.
- The index's other Albo confusions (`0>o` 57, `k>l` 40, `I>l` 34, `n>m` 31)
  are unchanged by every arm and were not investigated.

## Files

- `tools/wedge_serif/etrace/snap_build.sh`: builds a commit from a
  `git archive` snapshot, with optional `ETRACE_PATCH`.
- `tools/wedge_serif/etrace/kli_e.py`: the index plus Tesseract, and e>o by
  condition.
- `tools/wedge_serif/etrace/size_sweep.py`: the same reader over 8–13 px.
- `tools/wedge_serif/etrace/e_mechanism.py`: design-unit and hinted
  measures.
- `tools/wedge_serif/etrace/e_hint_gate.py`: the gate.
- `tools/wedge_serif/etrace/bisect_all.sh`: every commit, e hash plus gate.
- `tools/wedge_serif/etrace/e_arms.patch`: the two option dials.
- `tools/wedge_serif/etrace/e_proof.py`: the proof page.
- `tools/wedge_serif/etrace/results/`: the run outputs (JSON / TSV).
- **The index:** github.com/JessieSalas/kept-legibility-index at `aff8fb3`.
  Its Swift reader was built locally.
