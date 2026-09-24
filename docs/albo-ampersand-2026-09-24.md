# The italic ampersand, redrawn on the Aldine pen — round 377, 2026-09-24

Owner 2026-09-24, *"yes to all"*, which carries an item open since round 349:
**the italic ampersand is an outlier that needs a new drawing, not a dial.**

Surveyed at `c87068a` (round 375). Every number here comes from a built font
and one of three instruments committed with this round:
`tools/wedge_serif/instruments/amp_measure.py` (thirds, height, width, weight,
contrast, colour, vertical mass, against nine reference italics),
`instruments/amp_lean.py` (how far the letter's back leans once the face's own
slant is taken out) and `instruments/amp_touch.py` (the `&` against every
letter, figure and mark — `cmp_touch.py` has no `&` in its charset at all).
Builds are the four shipping cuts from `build_env.sh`'s `albo_build_all`
environment.

---

## 1. The ruling history

| round | commit | owner | what it did to the italic & |
|---|---|---|---|
| 309/311 | `29280ac` | *"an italic ampersand as previously requested"* (the queued brief: *"use a flowing and adorned curved E ampersand for italics"*) | four chancery `et` arms drawn on the Aldine nib (`et_b`..`et_e`); none default. The italic kept `a`, the ROMAN & sheared 13° |
| 312–314 | `2d02697` | *"trace alt051 in the albo style"*, *"make that letter form with the albo nib"*, *"drop the compact chancery et"* | Poetica's `ampersand.alt051` traced (`f`) and its spine run on a nib (`g`); widths taken from the SOURCE's width table |
| 316–317 | `78d57e9`, `8947694` | *"make variations that achieve more optically and styled balance"*, *"keep the left side strokes the same"* | WEIGHT, CON and SQUEEZE dials; the hold at 0.46 |
| 318 | `3de1886` | **"squeeze 0.38 wins"**, then *"reduce the visual distraction of a large top right extended stroke"* | curl dials built |
| 319 | `d82e186` | **"e wins, but it needs to have the italic lean and finials need to match albo (never round)"** | `ALBO_ALT051_LEAN` 1.0, the family finials |
| 321 | `9c156be` | **"c wins"** | the arm's route: PAVA, uniform resample, the join redistributed |
| 349 | `0e1d4ee` | *"finish amper"* | measured the italic & at **30.3 / 57.1 / 12.6** and called it the outlier — that letter was still `a`, the sheared roman |
| 350 | `6698a66` | *"that is not the italic ampersand that was selected today"* | `ALBO_IT_AMP` default `a` → `g`; the four ruled values applied; the `pen.ITALIC` guard added |
| 351 | `d247fca` | *"gate it, don't change it"* | the contour census |
| 352 | `d91fe0b` | **"leave the curl, it reads fine now"** | curl dials stay inert; the curl's gate finding accepted |

So the ruled FORM is Poetica's alt051 — the chancery Et, a curved E whose
lower bowl runs out into the t-stroke and a rising curl — with squeeze 0.38,
the italic lean, Albo finials, path c and the curl as drawn. This round keeps
every one of those and redraws what none of them ruled on.

### What "30.3 / 57.1 / 12.6" is

Ink mass in the left / middle / right third of the ink box, in percent, **on the
glyph as rendered (sheared)**. Reproduced: `ALBO_IT_AMP=a` measures
**30.4 / 57.5 / 12.1** with `amp_measure.py` (the half-point spread is raster
size). The roman's right third, 21.4, reproduces exactly. That letter stopped
shipping in round 350, so round 349's outlier finding was about a letter nobody
has seen since; the shipped `g` needed re-measuring, below.

---

## 2. What makes the shipped italic & (`g`) an outlier

Nine reference italics, measured the same way (each unsheared by its measured
slant: Flanker Griffo 11.7, Pagella 11.7, Poetica 9.2, Coelacanth 14.5 from
`refs_registry.py`; Georgia 13.1, Times New Roman 16.1, Palatino 12.0, Hoefler
Text 20.9, Baskerville 16.8 measured off `l` by the same 30/70% rule — Hoefler's
20.9 is probably inflated by its `l`'s exit stroke, and only moves the
unsheared columns).

| measure | refs, min – median – max | **Italic `g` (shipped)** | BoldItalic `g` |
|---|---|---|---|
| stroke median ÷ body letters' (`o e n c s a d g u`) | 0.60 – 0.85 – 1.04 | **1.06** — above all nine | 0.80 |
| contrast (90/10 pct along the ridge) ÷ body letters' | 0.73 – 0.92 – 1.19 | **0.70** — below all nine (1.74 vs 2.48) | 0.73 |
| advance ÷ the `o`'s | 1.32 – 1.72 – 2.34 | **2.35** — above all nine | **2.41** |
| back lean after the face's slant is removed | Poetica alt051 upright: 10.5° | **18.9°** | **18.9°** |
| ink above the box's middle, % | 35.5 – 42.5 – 50.4 | 49.6 | 49.2 |
| sheared thirds L / M / R | 27.8–53.1 / 26.1–46.5 / 15.9–30.3 | 43.3 / 33.9 / 22.9 — **inside** | 42.0 / 35.0 / 23.0 |
| ink top, × x-height | 1.26 – 1.43 – 1.70 | 1.63 | 1.60 |
| ink height ÷ cap height | 0.89 – 1.03 – 1.16 | 1.13 | 1.16 |
| ink width (unsheared), × x-height | 1.35 – 1.37 – 1.70 | 1.52 | 1.49 |

**The outlier, in one line: the heaviest and the flattest ampersand on the
shelf against its own body letters, the widest, and leaning about 9° more than
the italic it sits in.** On round 349's own measure — the thirds — it is inside
the band.

Both causes are in the construction, read from the source
(`outlines/glyphs/ampersands.py`, `alt051_nib`):

1. **The pen is Poetica's, not Albo's.** The width at every sample is
   `ALT051_WIDTHS` — the reference's own traced half-widths, 12–77 units —
   multiplied by the nib's factor to the power 0.45, then compressed toward its
   mean (`CON` 0.45) and inflated (`WEIGHT` 1.36). The nib it modulates by is
   `aldine.nib_widths`, whose `nib()` defaults to **phi 50**; `ALT051_PHI = 35`
   is declared and is read nowhere (grep). Compression toward the mean is what
   makes it flat; the 1.36 is what makes it heavy.
2. **The lean is doubled.** `ALT051_LEAN = 1.0` stopped counter-shearing the
   spine, and the spine was read off Poetica, which already leans 9.2°.
   `build.draw` then adds 13. Measured by `amp_lean.py`: Poetica's alt051
   reads 19.2° as drawn and 10.5° upright; the shipped `g` reads **18.9°** after
   Albo's 13 is taken out — Poetica's lean, whole, on top of Albo's.

---

## 3. The new drawing — `ALBO_IT_AMP=h`, `ampersands.alt376_aldine`

**Kept, because they are rulings:** `ALT051_SPINE` / `_WAIST` / `_SPUR`, path
pass `c`, squeeze 0.38 about the 0.46 hold, `NIB_H` 1.62 x-heights, the curl as
drawn, the family finial (`PR.finial_widths` / `PR.finial_cut`) on both free
ends of the main stroke.

**Redrawn:**

- **The Aldine italic's own pen, and nothing else.** Width =
  `thin + (thick − thin)·|sin(direction − 35°)|` (`et_nib`, which is
  `aldine.nib` repeated for the import order), thick **0.86 S** (the e's
  `ALBO_ALD_E_THICK`), **5:1** (`ALBO_ALD_CON`, arm B), **phi 35** (the o's, c's
  and e's), floored at **0.30 S** (`ET_FLOOR` — round 311 found that at phi 35
  an up-and-right stroke otherwise prints at 11 units), the nib's 9-sample
  moving average, and the Aldine tip taper (0.62 over 12%) on the bar and the
  spur. Widths are keyed on **arc length**, the parameter `stroke` itself uses
  (round 317's bug 3). No source width table, no mix, no CON, no WEIGHT.
- **The italic lean.** The squeezed spine is unsheared by Poetica's measured
  9.2° about the baseline — what the Aldine e does with `E_PAGE_SLANT` — so
  `build.draw`'s 13° lands the letter at the face's slope.

`ALBO_IT_AMP_H_WT` (1.00), `_H_THICK`, `_H_CON`, `_H_FLOOR` and
`ALBO_IT_AMP_SRC_SLANT` are dials on it; all ship at the values above.
**`ALBO_IT_AMP=g` builds round 350's letter unchanged**, and `a` the sheared
roman.

### Before and after

| measure | refs band | Italic `g` → **`h`** | BoldItalic `g` → **`h`** |
|---|---|---|---|
| stroke ÷ body | 0.60 – 0.85 – 1.04 | 1.06 → **0.78** | 0.80 → **0.77** |
| contrast ÷ body | 0.73 – 0.92 – 1.19 | 0.70 → **0.78** (1.93 / 2.48) | 0.73 → **0.78** (1.85 / 2.38) |
| advance ÷ `o` | 1.32 – 1.72 – 2.34 | 2.35 → **2.12** | 2.41 → **2.22** |
| advance, units | — | 943 → **852** | 971 → **894** |
| back lean, face slant removed | 10.5 (Poetica upright) | 18.9 → **9.8** | 18.9 → **9.6** |
| ink top × xh | 1.26 – 1.43 – 1.70 | 1.63 → 1.59 | 1.60 → 1.58 |
| ink height ÷ cap | 0.89 – 1.03 – 1.16 | 1.13 → 1.10 | 1.16 → 1.15 |
| ink width × xh | 1.35 – 1.37 – 1.70 | 1.52 → 1.37 | 1.49 → 1.37 |
| sheared thirds L / M / R | 27.8–53.1 / 26.1–46.5 / 15.9–30.3 | 43.3/33.9/22.9 → 43.4/**25.2**/**31.4** | 42.0/35.0/23.0 → 42.2/28.7/29.1 |
| unsheared thirds M | 27.3 – 45.0 | 23.2 → **16.7** | 25.7 → **18.7** |
| ink above middle, % | 35.5 – 42.5 – 50.4 | 49.6 → **51.6** | 49.2 → **51.4** |
| fill of own box ÷ body's | 0.62 – 0.79 – 0.91 | 0.71 → **0.60** | 0.63 → 0.65 |
| contours | — | 1 → 1 | 1 → 1 |

**Into the band:** weight, contrast, advance and lean, in both italic weights.
Height and width were in the band before and stay in it.

**Now OUT of the band, and said plainly:** the italic 400's sheared middle third
(25.2 against a floor of 26.1) and right third (31.4 against a ceiling of 30.3),
the ink above the middle (51.6 and 51.4 against 50.4), and the 400's fill of
its own box (0.60 against 0.62). The first three are the same fact: with the
lean corrected, the ruled curl stands upright at the right edge and is the
tallest thing in the letter, so mass sits right and high with a gap between the
E and the curl. **That is the curl, and the curl is ruled closed** (round 352).
It is reported here, not changed. The fill is the price of the lighter pen.

### Negative results, so they are not re-run

- **`ALBO_IT_AMP_H_WT` 1.08 and 1.16** land the weight at 0.87 and 0.91 of the
  body — nearer the references' median — but the contrast ratio falls to 0.72
  and 0.75, **below** the band: the floor holds the thins while the thicks
  grow. The pen unscaled (1.00) is the only rung inside the band on both.
  Contrast here is the pen's consequence, not a dial (`albo-method.md` §1g).
- **Squeeze 0.30** (off the 0.38 ruling, measured only) makes the thirds WORSE —
  right third 36.7 — and the advance 2.01. The squeeze is not the lever for the
  mass distribution; the curl is.
- **The two changes separated** (`ALBO_IT_AMP_SRC_SLANT=0`, the new pen at the
  old doubled lean, Italic 400): weight 0.78, contrast 0.78 — **the pen alone
  fixes both** — but advance 2.30, back lean 18.5°, sheared thirds
  42.3 / 33.4 / 24.3 (inside the band) and ink above the middle 52.5. So the
  lean correction is what takes the advance 2.30 → 2.12 and the back
  18.5° → 9.8°, **and it is also what moves the thirds out of the band**
  (middle 33.4 → 25.2, right 24.3 → 31.4): at 22° the curl was smeared
  leftward into the middle third; at the face's 13° it stands at the right
  edge. That is a real trade, and it is the owner's call; the ruled "italic
  lean" is what ships.

---

## 4. Gates, all four cuts, before (`c87068a`) and after

Run by the round's own driver over both builds and diffed line for line; the
only difference in the whole report is one row.

| gate | Regular | Italic | Bold | BoldItalic |
|---|---|---|---|---|
| `cmp_contour_hairs.py` full | 11, unchanged | **11 → 10**: the ampersand's finding is GONE | 9, unchanged | 8, unchanged; & never listed |
| `cmp_contour_hairs.py --letters` | 0 | 0 | 1 (pre-existing), unchanged | 0 |
| `cmp_touch.py` | unchanged | 0 / 0, unchanged | unchanged | `q'` touching, pre-existing, unchanged |
| `amp_touch.py` (the & against 73 others, both orders) | 0 below floor | 0 below floor (closest `o&` 0.106 → 0.100 em) | 0 | 0 (closest `q&` 0.054 → 0.048 em) |
| `cmp_aldine_glitch.py --all --ttf` | 19, unchanged | 23, unchanged; & not listed | 25, unchanged | 28, unchanged; & not listed |
| `cmp_counter_dents.py` | the roman `&` 630/7.9, unchanged (the documented lower-loop exception is the ROMAN's) | 0 → 0 | 0 → 0 | 0 → 0 |
| `approved.py` | Regular:g ok | Italic:g ok | — | — |
| `cmp_contours.py` | census unchanged, 982 glyphs | | | |
| `./gates.sh` | one delta: `hairs.all.Italic` loses `ampersand`; accepted into `gates-baseline.txt` | | | |

**The ruled curl finding is removed, not kept.** In the `c87068a` build it
reads `HAIR x1, worst turn 164.0 deg at (810, 676), arms 81.9/24.2` (round 350
recorded it as a 165.5° REVERSAL at (813, 676); same place, and the decimation
phase moves it a little). The new pen's widths at the curl no longer fold the
outline there. The curl's ROUTE is unchanged.

**Re-verified after rebasing onto `8789371`** (the other round-376 commit:
quotes, `?`, the italic `1`): all four cuts rebuilt with `ALBO_IT_AMP=g` and
with the new default, the whole report diffed again — the same single row —
and `./gates.sh` reads **GATES UNCHANGED** against the accepted baseline. The
new ampersand's outline and advance are identical before and after the rebase,
so every measurement above stands.

**Scope, by outline (`cmp_outlines.py --advances`):** Regular 0 of 493 differ;
Bold 0 of 493; Italic **1 of 493 — `ampersand`**, outline and advance;
BoldItalic **1 of 493 — `ampersand`**. No composite references `ampersand` in
either italic. The contour count is unchanged (1 → 1), so no cut ripple
(round 350's 169-glyph re-cut does not recur). The roman is identical by
outline in both weights.

`docs/albo-STATE.md` regenerated: `ALBO_IT_AMP` **g → h** and the five new
dials. It was already stale before this round (stamped `3e2a226`; round 375's
marks.py line shifts and three new dials `ALBO_CURLY_SCALE`,
`ALBO_MARK_TAIL_FIXED`, `ALBO_MARK_WEIGHT_EXP` were missing) and those rows
come with the regeneration.

---

## 5. Checked and found CLEAN

- **The roman ampersand** — identical by outline at 400 and 700; the `pen.ITALIC`
  guard in `marks.g_ampersand` (round 350) is present and is what keeps `h` out
  of it. Round 349's "roman is clean" finding re-reproduced: right third 21.4.
- **The `ALBO_IT_AMP` leak** — guarded (`if pen.ITALIC and IT_AMP in ET_OPTIONS`).
- **Composites** — none use `ampersand` in either italic.
- **Contour census** — unchanged.
- **Spacing** — both bearings stay 59 / 59 units in both italics; the `&`
  keeps about 0.10 em of white to its neighbours, as before.

## 6. Not measured, not claimed

- On-device rendering. Nothing here was installed on the reader.
- The owner's eye. The renders are in the session scratchpad
  (`scratchpad/albo/amp376/`): the letter large before/after in both italic
  weights, beside all nine references at one x-height, and *"Smith & Sons,
  Black & White, rock & roll, bread & butter"* at 40 and 27 px and at 13 px
  ×5 nearest-neighbour.
