# Which letters do not fit the rest of Albo — 2026-09-18

> **CORRECTION, later the same day — read this before the tables below.** The
> instrument this audit's weight columns came from, `cmp_weight_survey.py`, had
> two bugs, found by the two glyph agents of round 224 and verified on cases
> whose answers are known:
>
> 1. **Its `--slant` sign was inverted.** PIL's affine maps output → input, so
>    the "unshear" ADDED 13° instead of removing it: the italic `l`'s stem, +12.2°
>    at slant 0, read **+24.0° at +13** and −0.8° at −13. Every ITALIC number in
>    section (b) below, in `docs/albo-weight-survey-2026-09-17.md`, and in this
>    session's rounds 208–219 was measured at **26° of shear**.
> 2. **It cropped the raster to the ink's bounding box**, so a stroke lying on the
>    box edge — a bar, a Z's top, a stem's outer side — had no background beyond
>    it and read at up to **twice** its thickness. The roman Z's 59-unit bars came
>    back as 93 and 117 and the letter as "+65%, the heaviest in the roman".
>
> Both are fixed in the script (sign flipped; a 48 px margin kept). On the fixed
> instrument, against the merged round-224 builds:
>
> | glyph | this audit said | corrected | verdict |
> |---|---|---|---|
> | italic Y | +92% of diagonals | −6% of capitals (70.4) | not a fault; ruled anyway (rounds 161/163/194) |
> | italic A | +39%, apex 712 | −19% of capitals (61.0); apex **695** after round 224 | the apex was real, the weight was the shear |
> | italic z | −36%, thin/stroke 0.89 | −28% of lowercase → diagonal 27 → 36 in round 224; 50.4 now | real, and fixed |
> | italic 1 | +36% of figures | +21% — a lone stem against a bowl-led median | not a fault |
> | italic 6 / 7 / 8 | (rounds 212–219's "matched at 53.4") | **65.1 / 65.5 / 63.2** — still matched | the match survives; the number was wrong |
> | roman Z | +65%, heaviest, monoline | 58.7, **−23% of capitals**; bars 0.63 of its diagonal | **void** — crop artifact; not touched |
> | roman W | +43% | +18% — a median of two thicks and two thins | stroke-count artifact; not touched |
> | roman Q | +84% width, 14 touching pairs | tail 1.80 → **1.08** cap heights in round 224; all 14 clear | real, and fixed |
> | roman S | +27% | 77.5, +2% after round 224 (profile rebuilt on the round family's bowl) | real, and fixed |
> | roman X | −28% | 51.2, −33% of capitals (its thin raised 0.72 → 0.90) | partly fixed; the italic X is now the lighter of the pair |
>
> The (c) finding that the roman figures never received the body fit was
> correct and is round 223. Sections (d) and (e) stand.

Owner, 2026-09-18: *"identify what characters in the font are not fitting the
rest of the font in roman and italic, update md file with results."*

A ledger, not an essay. Every row is a number from an instrument in
`tools/wedge_serif/` plus the lever that would move it. Nothing here was
changed; this is a read-only pass.

## (a) What was audited, and how sure each finding is

| | |
|---|---|
| italic | `Albo-Italic.ttf`, built from **round 222** (`5e1729e`, 2026-09-18, *"the italic's quotes come down 50 units and in on both sides"*) |
| roman | `Albo-Medium.ttf`, built from **round 221** (`e87a3bd`, 2026-09-18) |
| repo HEAD during the audit | `5e1729e` |

**The roman binary is one round older than the italic, and only on the quote
marks.** Round 222 is italic-quotes-only by its own commit message and rounds
220 and 221 each record *"roman byte-identical in outlines and metrics"*. The
roman was NOT rebuilt at 222 to prove it — that is an inference from the round
log, not a measurement — and it is irrelevant to a fit audit of letters either
way.

**Confidence, per class of finding:**

| class | instrument | confidence |
|---|---|---|
| WEIGHT (stroke median, thin, cut, color) | `cmp_weight_survey.py`, regrouped by construction family | **measured** |
| SPACING (2-D closest approach, by class and side) | `cmp_space_2d.py` | **measured**; roman verdicts are against ITALIC references (see §d) |
| FIGURE spacing | `cmp_figure_space.py --body --per-digit --own` | **measured** |
| PROPORTION — heights, overshoots, descender depths | outline bbox off the TTF | **measured**; shear-invariant |
| PROPORTION — widths, italic | outline bbox | **NOT trusted** — a 13° shear inflates a bbox width in proportion to the glyph's height, so the italic's width-by-family table measures the shear. Italic proportion findings below are heights only |
| DEFECTS | `cmp_aldine_glitch.py`, `cmp_touch.py` | **measured** |
| by eye | two English paragraphs per style at 13 px ×6 NEAREST and at 40 px, plus a named-word sheet at 13 px ×12 and 90 px | **by eye**, and labelled as such |

**The grouping is by CONSTRUCTION FAMILY, not by case.** `cmp_weight_survey.py`
groups by case in its own output, and at `--tol 0.15` that flags **47 of 124
glyphs** on this build — which is the failure
`docs/albo-weight-survey-2026-09-17.md` already names: *"grouped by case, 53 of
124 glyphs came out more than 15% off — which measures the alphabet, not the
drawing."* The family medians below are computed from that script's own
`--json` output. The map used:

    round   a c e g o s   C G O Q S          (11 per style)
    diag    v w x y z     A V W X Y Z        (11)
    figure  0-9                              (10)
    stem    everything else                  (30)

## (b) ITALIC — ranked misfits, worst first

Family medians on this build: **stem 65.9** (cut 2.43, color 0.315),
**round 54.2** (2.88, 0.275), **diag 42.1** (2.81, 0.260),
**figure 54.9** (2.97, 0.215). `thin ÷ stroke` is round 219's modulation
measure — low modulates, high is flat.

| # | glyph | the number | judged against | lever |
|---|---|---|---|---|
| 1 | **Y** | stroke **80.9, +92%** of its family; thin/stroke 0.45 | diag median 42.1 | `ALBO_ALD_CAP_Y_*` are bearings only — the Y's weight is its spine and arms in `aldine.py` `@glyph('Y')`; the family's weight dial is `ALBO_ALD_CAP_CON` |
| 2 | **z** | stroke **27.1, −36%**, AND thin/stroke **0.89** (the flattest lowercase) | diag median 42.1, modulation median 0.69 | `ALBO_ALD_Z_DIAG` (27.0), `ALBO_ALD_Z_W` (1.03) |
| 3 | **A** | stroke **58.7, +39%**; and cap top **712**, the tallest capital in the face, +32 over the flat line (680) and +25 over the V (687) | diag median 42.1; cap overshoot family | `ALBO_ALD_CAP_A_W`, `ALBO_ALD_CAP_A_AP` (apex), `ALBO_ALD_CAP_A_BAR` |
| 4 | **1** | stroke **74.5, +36%**; thin/stroke **0.33** — the most modulated AND the heaviest figure | figure median 54.9 | `ONE_FLAG_W` (1.15, round 218), `ONE_FLAG_CURVE` (−0.18), `ONE_EXIT_LEN` (0.70) |
| 5 | **Z** | stroke **56.4, +34%** | diag median 42.1 | `ALBO_ALD_CAP_Z_D` (1.09), `ALBO_ALD_CAP_Z_BAR` (1.06) |
| 6 | **g** | **descender −194** where the family runs −282 to −297 (p −282, q −282, j −293, f −294, y −297): the loop is **31–35% shallower** than every other descender in the style. Stroke also −21% of the round family | descender family; round median 54.2 | `ALBO_ALD_G_LSCALE` (0.9 — its comment says *"the crown stays on the baseline"*, so it shortens downward), `ALBO_ALD_G_LOOP_Y` (64), `ALBO_ALD_G_LTOP` (4) |
| 7 | **e** | stroke **36.1, −33%**; and its ink bottom sits at **+2**, i.e. ABOVE the baseline, where o −8, c −8, a −10, s −32 — the only round letter in the style with no baseline overshoot | round median 54.2 | `ALBO_ALD_E_PEN`, `ALBO_ALD_E_THICK`/`E_THIN`, `ALBO_ALD_E_FLOOR` |
| 8 | **X** | stroke **29.4, −30%**, and **thin 15.1 units** — the thinnest ink in either style, cut 6.80 | diag median 42.1 | `ALBO_ALD_CAP_X_D` (0.879), `ALBO_ALD_CAP_X_TW` (1.153), `ALBO_ALD_CAP_X_THIN` |
| 9 | **E** | stroke **84.3, +28%** — the heaviest capital | stem median 65.9 | `ALBO_ALD_CAP_CON` |
| 10 | **5** | stroke **70.0, +27%** | figure median 54.9 | `FIG_CON`, and the 5's own ring/bar in `aldine.py` `FIG_HAND` |
| 11 | **O** | stroke **67.7, +25%**; and cap top 690 against G **717** and S **710** — the round capitals' overshoots disagree by 27 units, where the roman's agree to 1 (G 691, O 690) | round median 54.2; roman's own round-cap line | `ALBO_ALD_CAP_CON`; the G's and S's ring tops in `aldine.py` |
| 12 | **R (spacing)** | right side **0.048 em** against a capital-side median of ~0.135 — the tightest side in the font. `R1` 0.0142, `RR` / `Rx` 0.0228, `Rn` 0.0242, `Ri` / `Rj` 0.0256, all just over the 0.012 floor | `cmp_space_2d --per-glyph upper` | `ALBO_ALD_CAP_R_RSB`, `ALBO_ALD_CAP_R_KFULL`/`KFADE` (the leg). Round 216 already answered the digit half with three kerns; this is the letter half |
| 13 | **f, p, T, H, P** | f −25%, p −22%, T −21%, H +23%, P +22% | stem median 65.9 | per-letter: `ALBO_ALD_P_STEMW`, `ALBO_ALD_CAP_P_W`, `ALBO_ALD_CAP_CON` |
| 14 | **y** | stroke **31.6, −25%**; thin 23.3 | diag median 42.1 | `ALBO_ALD_Y_INK`, `Y_SPINE_INK`, `Y_ARM_INK` |
| 15 | **ascender line is ragged** | b **759**, d 771, h 774, l 774, f **798**, k **806** — a **47-unit spread**, 11% of the x-height. The roman's six ascenders span **1 unit** (771–772) | the roman's own ascender line | `ALBO_ALD_B_ASC` (the b, which is the short one), `ALBO_ALD_K_AEDGE`, `FJORD_ASC` globally |
| 16 | **u** | x-line top **448** where n 433, m 435, r 433, z 431 — +15, about 3.5% of the x-height | the style's own x-line | `ALBO_ALD_U_RISE_X`, `ALBO_ALD_U_JOIN` |
| 17 | **Y (overshoot)** | cap top **680** — sits exactly on the flat line, no apex overshoot, where X is 701 and A is 712 | the style's own pointed capitals | the Y's apex in `aldine.py` `@glyph('Y')` |
| 18 | **`"W`** | **0.0124 em**, the single tightest pair in the italic — clears the 0.012 floor by 0.0004 | `cmp_touch` | a kern pair, as `Q,` and `Q3` were (rounds 216, 220) |
| 19 | **d, x right side** | d **0.080**, x **0.082** em — the two tightest lowercase right sides against a class median of 0.095 | `cmp_space_2d --per-glyph lower` | `ALD.BEARINGS['d']`, `['x']` |
| 20 | **8** | color **0.280, +30%** of the figures' median — the darkest figure | figure color median 0.215 | consistent with the roman's +50%, so probably the design; ranked last for that reason |

**By eye, at 13 px and at 90 px** (the pictures agree with the numbers and add
two things the numbers do not):

* the **z** is the palest mark on the page — in *zigzag*, *jazz* and *lazy* it
  drops out of the line while the a and g beside it hold. This is finding 2
  seen rather than measured, and it is the single most visible misfit in the
  style.
* the **fl / ffl ligature closes up at 13 px**: *flitting* and *fluffy* read
  with a capital-like mass at the head. **Tested the inverted reading as
  `docs/albo-method.md` §1c requires: at 90 px both are clean and correctly
  formed, and `cmp_aldine_glitch` reports no finding on any of the five
  ligatures.** So this is a reading-size legibility question about
  `FI_PUSH` / `FL_PUSH` / `FF_STEP` in `glyphs/ligatures.py`, not an outline
  defect. Confidence: **by eye only.**
* the **g**'s shallow loop (finding 6) is visible beside a y at reading size —
  in *zigzag* the g's tail stops well short of the line the y drops to.

## (c) ROMAN — ranked misfits, worst first

Family medians: **stem 81.3** (cut 1.79, color 0.316), **round 66.2**
(1.68, 0.325), **diag 62.8** (1.82, 0.272), **figure 65.5** (2.04, 0.223).

| # | glyph | the number | judged against | lever |
|---|---|---|---|---|
| 1 | **Q** | ink width **1214 units = 1.80 cap heights, +84%** of the round family; its tail causes **14 of the font's 19 touching pairs** (`Q9` −0.468 em through `QQ` −0.042) | round-capital width family; `cmp_touch` | no env dial — the tail is a hard-coded cubic in `glyphs/caps_straight.py` `g_Q`, ending at `W * 1.80, −C * 0.20`. Shortening it, or 14 kern pairs |
| 2 | **Z** | stroke **103.9, +65%** — the heaviest glyph in the roman — AND thin/stroke **0.90**, nearly monoline | diag median 62.8; modulation median 0.79 | `ALBO_ALD_CAP_Z_D` is the italic's; the roman capital Z is `CAP_Z_DIAG` in `glyphs/caps_straight.py` (the exploration doc records `CAP_Z_DIAG` 1.14 → 1.09) |
| 3 | **W** | stroke **89.6, +43%**; ink width 1027 = 1.52 cap heights | diag median 62.8 | the W's diagonals in `glyphs/diagonals.py` |
| 4 | **Y** | stroke **82.8, +32%**; color −30% | diag median 62.8 | `FJORD_Y_LEFT_W` is the lowercase y's; the capital's spine is in `glyphs/diagonals.py` |
| 5 | **X** | stroke **45.2, −28%**; thin 33.1 | diag median 62.8 | `X_BL_WEDGE` / `X_BL_WIDTH` in `glyphs/diagonals.py` are the wedge, not the weight — the diagonals themselves are in the same `@glyph('X')` |
| 6 | **S** | stroke **84.3, +27%**; thin 31.6, cut 3.01 — the roman's most contrasted round. Cap top **699** against O 690, G 691, C 691 | round median 66.2 | the S's spine in `glyphs/rounds.py` |
| 7 | **figures are fitted on the REACH, not the body** | spread **p90/p10 = 2.10×** against the italic's 1.31×. `47` 0.2662 em against `00` 0.0814 — **3.3× between the widest and tightest pair**. The 4 owns 0.0815 em of open white on its right and the 7 owns 0.0944 on its left, and each is paid for twice | `cmp_figure_space --body --own`; the italic's own 1.31× | **`FIG_BODY` / `FIG_TRACK` in `outlines/build.py` — round 216's fix, which was applied to the italic only.** Passes the 2.50× gate, so nothing has flagged it |
| 8 | **1** | stroke **81.3, +24%** — the heaviest figure | figure median 65.5 | `ONE_FLAG_WEDGE` (round 75's microserif, which stands in the roman by ruling) and the 1's stem in `glyphs/figures.py` |
| 9 | **4** | stroke **49.7, −24%**; color −20% | figure median 65.5 | `glyphs/figures.py` `@glyph('4')` |
| 10 | **7** | stroke **51.9, −21%**; color **0.147, −34%** — the lightest figure in the style; thin/stroke **0.97**, the flattest glyph in the roman | figure median 65.5 | `SEVEN_BAR_W` / `SEVEN_DIAG_W` (shared with the italic — round 213 records the leak). Round 219 fixed exactly this in the italic (0.94 → 0.83) and the roman was left at 0.97 |
| 11 | **z (overshoot)** | ink top **430**, bottom **−1** — the only lowercase diagonal with no overshoot at either end, where v 445/−16, w 443/−15, x 455/−26, y 444/−308 | its own family | `ALBO_Z_W` (0.84), and the bars' `align top/bottom` in `glyphs/diagonals.py`, which is what pins them to the grid |
| 12 | **s** | ink top **450** against o 444, c 446, e 444 — **6 units proud of the round letters' line**. Round 208b brought the ITALIC's s down to the o's line for exactly this and the roman was not touched | the style's own round letters | the roman s in `glyphs/rounds.py`; the italic's dial was `ALBO_ALD_S_HEIGHT` |
| 13 | **x** | ink top 455, bottom −26 against v 445/−16 and w 443/−15 — 10 units more overshoot at each end than its family | its own family | `X_BL_WEDGE`, and the x's diagonals |
| 14 | **fi, ff, fT, f)** | **touching**: −0.0255, −0.0188, −0.0059, −0.0031 em. `VI` 0.0002 and `(j` 0.0051 are under the 0.012 floor without touching | `cmp_touch` | `FI_PUSH` (0.35) / `FF_STEP` (1.38) in `glyphs/ligatures.py` reposition the ligature, not the unligated pair — these need the f's right bearing or kerns |
| 15 | **T, L, J, C color** | T −35%, L −30%, J −31%, C −33% of their families' color | family color medians | structural (open letters), ranked low; recorded so it is not re-found |
| 16 | **8** | color **0.333, +50%** of the figures' median — the darkest figure | figure color median 0.223 | same item as the italic's #20; consistent across styles, so design |
| 17 | **lowercase fitting is uneven** | per-glyph right sides span **0.085 (s) to 0.137 (u)**, a 1.6× spread, against the italic's 1.45× | `cmp_space_2d --per-glyph lower` | `ALD.BEARINGS` is the italic's table; the roman is fitted by the rule in `outlines/build.py`. **See the caveat in §d before acting on any roman spacing number** |

**By eye** (the pictures add one thing):

* **the Q's tail visibly collides at reading size.** In *Question* at 13 px the
  tail runs under and into the `ue`. Finding 1, seen.
* the **w** is conspicuously wide and light in running text — *However*,
  *with worms crawling* read with holes in them. That is the W's lowercase
  partner, and the lowercase w measures −26% by case grouping but only +47% on
  width; it does not flag on the family weight table, so it is **by eye only**
  and wants a measurement of its own before anyone moves it.

## (d) Checked and found CLEAN, by instrument

So the next pass does not redo these.

| instrument | result |
|---|---|
| `cmp_aldine_glitch.py --ttf <italic>` | **0 findings of 119 glyphs.** Clean |
| `cmp_aldine_glitch.py --ttf <roman>` | **0 findings of 119 glyphs.** Clean |
| `cmp_aldine_glitch.py --chars 'ﬁﬂﬀﬃﬄ'`, both styles | **0 of 5.** This CORRECTS the premise this audit was given — the roman does NOT carry two glitch findings on `fi` and `ffi`. Those two appear in the script's `EXPECT_ISLANDS` table (`'ﬁ': 2, 'ﬃ': 2 — the i's dot`), i.e. their two ink islands are *declared expected* and are not findings |
| `cmp_aldine_glitch.py --all`, italic | 13 findings of 290 — the same pre-existing set the round log has recorded since round 212 (six SPLITs on `“ ” … ¨ ˝ ¡`, seven CRACKs on `¥ √ ♕ ♣ ♤ ♧ ✔`). Not letters; not re-opened |
| `cmp_aldine_glitch.py --all`, roman | 12 of 290 — the same set less the `¥` CRACK |
| `cmp_touch.py <italic>` | **0 touching, 0 below the 0.012 em floor, of 5,201 pairs.** Clean. Tightest is `"W` at 0.0124 (finding 18) |
| `cmp_touch.py <roman>` | **18 pairs touching + 1 exempt (`fl`, −0.0695) = 19 pairs of touching ink; 20 below the floor.** This CONFIRMS the premise's count of 19 and its "14 of them the Q's tail": the 14 Q pairs are `Q9 Q3 QJ Q5 Q) Qj Q( Qg Q7 Qp Qy Q4 Qq QQ`. The gate's own headline says 18 because `fl` is exempt by name |
| `cmp_figure_space.py --body`, italic | median 0.1327 em, **spread 1.31×**, per-digit flanks 0.114–0.157. Holds exactly where round 216 left it. Clean |
| `cmp_space_2d.py --refs`, italic | `digit+digit` 0.132, `letter+stop` 0.130, `stop+letter` 0.131, `letter+quote` 0.119, `quote+letter` 0.126 — **five of eight classes in band.** Rounds 216, 220 and 222 hold |
| `cmp_weight_survey`, roman stems | 30 glyphs, median 81.3, **not one more than 20% off it.** The roman's stem weight is as uniform as a drawn face gets — unchanged from the 2026-09-17 finding |
| `cmp_weight_survey`, roman `z` | **stroke 57.2, −9% of its diag family. NO LONGER A FAULT.** `docs/albo-weight-survey-2026-09-17.md` finding 1 calls the roman z *"the heaviest lowercase in the face"* at stroke 99.3; **rounds 207 and 210 re-cut it on the owner's ruling** (*"the roman z narrowed and lightened until razzmatazz balances"*) and that finding is superseded. Do not re-raise it |
| roman ascender line | b, d, h, k, l all top at **771** and the f at 772 — a 1-unit spread. Clean, and the yardstick the italic's 47-unit spread (finding 15) is measured against |
| roman descender line | p −281, q −281, j −297, y −308, g −305 — a 27-unit spread with no outlier. Clean |
| roman flat-capital line | I B D E F H L N P R T Z all top at 676–677. Clean |
| italic flat-capital line | B D E F I J T U 676, H K L N P R Y 679–680. Clean |
| italic `2` bottom | −35, which is round 212's deliberate drop (*"the 2's ink bottom goes 7 → −29, which makes it descend like the 0 rather than sit on the line: named, not assumed"*). Not a fault |

**What could NOT be measured, and why:**

* **`cmp_aldine_metrics.py`** (the gate that fails a letter more than 10% off its
  own measured w/h target) — it runs `outlines.build` in a subprocess to build
  the italic it measures. Another agent is editing `outlines/` during this
  session, so running it would both race that work and measure an in-progress
  tree rather than the two built fonts. **Not run.** It is the instrument that
  answers PROPORTION properly and it should be the first thing run once the
  tree is quiet.
* **`outlines/cmp/variety.py`** (byte-identical serif and counter twins — the
  detwinning audit) — it imports `outlines.build` and wraps the primitives for
  the length of an in-process build. Same reason. **Not run.**
* **`cmp_cap_weight.py`** — builds both fonts. Same reason. **Not run.**
* **A roman reference band.** `cmp_space_2d`'s seven references are all
  ITALICS. The roman's three "LOOSE" verdicts (`lower+lower` 0.108 against a
  0.079 median, `cap+lower` 0.128, `cap+cap` 0.095) are measured against the
  wrong posture and **overstate**, since a roman is normally fitted a little
  wider than its italic. Round 221 recorded the same caveat. Roman finding 17
  above rests on the SPREAD across the roman's own letters, which is
  posture-free; the class medians are not evidence until a roman reference set
  is loaded.
* **Italic widths.** The 13° shear inflates a bbox width in proportion to the
  glyph's height — the italic `I` measures 288 units of bbox width against the
  roman's 230 for the same stem. Every italic proportion finding above is a
  HEIGHT, which a shear about the baseline leaves exact. An italic width
  comparison needs the unsheared raster `cmp_weight_survey` already takes.

## (e) Owner-ruled — measured, deliberately NOT flagged

These are his, by ruling. They appear in the numbers as deviations and are not
faults.

| item | the ruling |
|---|---|
| **Every capital's bearing** — `CAP_BEARING_ADJ` in `glyphs/aldine.py` | round 137, his table. Italic `cap+lower` 0.128 against a 0.100 reference median is the right sides of E, H, N, T at 0.153–0.165 |
| **The lowercase tracking** — `BEARINGS`, +26 | round 136, his bench. Italic `lower+lower` 0.095 against 0.079, and the excess is UNIFORM (sd 0.010 across 18 letters). Both arms are built and laddered under `ALBO_ALD_TRACK`; round 221 left the choice with him |
| **The 16 kern pairs and 5 bearings** — `PAIRS` in `outlines/kern.py` | round 198, set at his bench |
| **T, V, W left sides at 0.205–0.231 em** | their own open white. `docs/albo-spacing-method.md`'s first rule: *a letter's own open white belongs to the letter, not to the gap*. The V owns 0.236 em on its right where the o owns 0.019 |
| **`cap+cap` at 0.129** | the documented +0.045 em rhythm, `docs/albo-capital-spacing.md` |
| **The 7's color gap** (italic 0.171, roman 0.147, against figure medians 0.215 and 0.223) | round 212: *"By COLOUR they do not converge and cannot"* — a 7 is two strokes over a lot of white. The STROKE is the measure that answers the ask, and the italic's is at +0%. Roman finding 10 above is about its **stroke and its modulation**, not its color |
| **The italic 2's descent to −35** | round 212, named not assumed |
| **`fl`, `fb`, `fh`, `fU` in `cmp_touch`'s `EXEMPT`** | round 96b — the f's hook is drawn to land on an ascender's top-left wedge |
| **The italic `oc` / `or` kerns, halved** | round 202 bench values of his, halved rather than overruled in round 211 |
| **`o` before a mark reading loose** (`o.` +0.046, `o,` +0.089 on min white) | round 211, deliberately not compensated — min white cannot see a mark sitting low and open, and it was judged by eye at 54 px |
| **The roman 1's microserif** — `ONE_FLAG_WEDGE` | round 75. Round 217 superseded it **in the italic only**; restoring it to the italic would be undoing that round, and removing it from the roman would be undoing round 75 |
| **The roman z's weight** | rounds 207 and 210, his ruling. Now −9% of its family and correct; see §d |
| **Defects as charm** | the standing rule (`tools/wedge_serif/README.md` rule 5): *"there is a charm to naively putting shapes together and having defects … let me decide what needs fixing."* Nothing in §b or §c is proposed as a fix; they are a list for him to rule on |

## Re-running this

```bash
cd tools/wedge_serif
PYTHON_GIL=0 python3 cmp_weight_survey.py --roman R.ttf --italic I.ttf --json w.json
PYTHON_GIL=0 python3 cmp_space_2d.py I.ttf --refs
PYTHON_GIL=0 python3 cmp_space_2d.py I.ttf --per-glyph lower      # also upper, stops, quotes
PYTHON_GIL=0 python3 cmp_figure_space.py I.ttf --body --per-digit --own
PYTHON_GIL=0 python3 cmp_aldine_glitch.py --ttf I.ttf [--all]
PYTHON_GIL=0 python3 cmp_touch.py I.ttf --top 60
```

The family regrouping in §b and §c is over `cmp_weight_survey.py`'s own
`--json`, with the four-family map printed in §a. If that regrouping is wanted
as a permanent column, it belongs in the script beside `GROUPS`, not in this
file — a table in a doc goes stale the moment a shared dial moves, which is the
reason `cmp_aldine_metrics.py` is a script and not a table.
