# Albo's marks, measured — round 369

**2026-09-23.** Six owner instructions in one round, all about the small
marks. Every one was measured against six roman references before anything
moved, and the instrument is `tools/wedge_serif/cmp_marks.py` — **a file, not
a heredoc**, which is the first thing this round got right and the previous
one got wrong.

## Why the instrument is a file this time

Round 362 measured the same marks from an inline heredoc, published the
numbers, and deleted the script. Round 369 needed them again — for the
exclamation's dot, the tittles, the dieresis and "scale up punctuation" — and
had nothing to re-run, so the whole measurement was paid for twice. Per the
repo's own rule: a surprising number IS the instrument until proven otherwise,
and that cannot be done against a script that is gone.

```
python3 cmp_marks.py <font.ttf> [more...]     # subjects first, then six references
```

It renders every font to a common x-height and reads each mark back from the
raster. Extents could come out of `glyf` bounds exactly and for free; the
things that actually decide these asks cannot — a dot's DIAMETER when the mark
has two, the WHITE between a colon's pair, an exclamation stem's THICK,
whether a dieresis sits centred over its letter. One measurement path, no
per-font special case. **Every figure is divided by that font's own x-height**,
because a period is not "0.25 em" in any useful sense; it is a mark read beside
a lowercase, and the references disagree about em far more than about the body.

References: Georgia, Times New Roman, Baskerville, Charter, Hoefler Text,
Palatino (macOS system copies). `.ttc` files open at index 0, which is not
always the roman — the instrument prints each family name so that is visible.

## What was measured, and what shipped

| measure | Albo before | references | Albo after |
|---|---|---|---|
| `.` width | 0.174 | 0.241–0.277 | **0.259** |
| `.` height | 0.172 | 0.243–0.277 | **0.252** |
| `,` width | 0.181 | 0.323–0.427 | **0.344** |
| `,` height | 0.346 | 0.570–0.700 | **0.619** |
| `’` width | 0.181 | 0.289–0.399 | **0.358** |
| `’` height | 0.344 | 0.547–0.661 | **0.645** |
| `:` dot | 0.174 | 0.243–0.279 | **0.258** |
| `:` white | 0.560 | 0.401–0.586 | **0.433** |
| `!` dot | 0.247 (nib) | 0.236–0.277 | **0.261** |
| `!` thick | 0.184 | 0.217–0.259 | 0.181 |
| `!` dot ÷ thick | 1.346 | 0.970–1.205 | 1.442 ⚠ |
| `i` tittle | 0.160 | 0.221–0.261 | **0.191** |
| `i` stem | 0.139 | 0.175–0.209 | 0.136 |
| tittle ÷ stem | 1.153 | 1.148–1.444 | **1.397** |
| tittle gap | 0.209 | 0.224–0.383 | 0.212 ⚠ |
| `¨` white ÷ dot | **0.104** | 0.628–1.250 | **0.907** |
| `¨` centring on `ä` | 0.002 | −0.007…−0.086 | **−0.024** |

Shipped dials: `ALBO_MARK_DOT` 1.50, `ALBO_COMMA_LEN` 1.95, `ALBO_COMMA_W`
2.40, `ALBO_QUOTE_SIZE` 1.75, `ALBO_QUOTE_W` 1.65, `ALBO_COLON_SPAN` 1.05,
`ALBO_TITTLE` 1.20, `ALBO_DIE_GAP` 3.70, `ALBO_MARK_TALL` 1.0,
`ALBO_EXCL_NIB` 0, `ALBO_ACC_OPTICAL` 1.0.

## The five findings worth keeping

### 1. The dieresis was not tight, it was closed

White between the two dots measured **0.104 of a dot's own diameter** where the
references run 0.628–1.250. At 13 px the pair quantised to a single bar — every
German and Swedish umlaut in the face. The owner reported it as "give them
enough space between"; the measurement says it was ten times too tight, not a
shade.

### 2. "Center dieresis optically" has a precise meaning, and it is a TABLE

The composite builder centres every above-mark on the base letter's **ink
bounding box** (`outlines/build.py`), so Albo measured a centring error of
0.000–0.002 of the x-height on every letter — dead centre, and wrong, because
no reference does that. Accent centre minus the base's ink centre, ÷ x-height:

| letter | Georgia | Times | Baskerville | Charter | Hoefler | verdict |
|---|---|---|---|---|---|---|
| `o` | +0.008 | −0.001 | +0.018 | +0.000 | +0.002 | centred |
| `u` | −0.009 | −0.001 | +0.001 | +0.003 | −0.013 | centred |
| `n` | −0.007 | −0.001 | +0.000 | −0.036 | −0.005 | centred |
| `a` | −0.050 | −0.034 | −0.087 | −0.024 | −0.030 | **LEFT, 5 of 5** |
| `e` | +0.019 | +0.034 | +0.000 | +0.028 | +0.034 | **RIGHT, 4 of 5** |

**Two candidate formulas were tested and both failed.** Centring on the
letter's TOP BAND reproduces the `a` (−0.019) and the `o` (+0.002) and then
invents a shift the references do not make on the `u` (−0.047) and the `n`
(−0.068), and would throw the `Ĺ`'s accent 0.433 of an x-height left. Centring
on the ADVANCE is noisier still (the `a` ranges +0.022 to −0.052 across the
same five faces). What the references have is a short hand-made table, so
that is what shipped: `ACC_OPTICAL = {'a': -0.030, 'e': +0.030}`, lowercase
keys only, because the measurement was taken on lowercase and says nothing
about `A` and `E`.

### 3. All six references cut `!` and `?` to the CAP line, not the ascender

`! of cap` runs 0.988–1.024 across all six; `! of asc` runs 0.909–0.956. Albo
already sat at 1.021 of cap, exactly where they all sit. The owner asked for
the ascender and that is what shipped (`ALBO_MARK_TALL` 1.0) — but his eye is
reading something real: **Albo's ascender overshoots its own cap by 16%, the
largest gap of the seven** (Baskerville 4%, Palatino 7%, Times 7%, Hoefler 8%,
Charter 10%, Georgia 13%). So beside an `h` or a `b`, Albo's `!` looks shorter
than the same ratio looks anywhere else. `ALBO_MARK_TALL=0` restores the cap
line exactly.

### 4. The exclamation's dot cannot satisfy both measures, and the reason is structural

All six references put the `!`'s dot at the same size as their period (0.236–
0.277 against 0.241–0.277) AND at 0.97–1.21 of the `!`'s own thick. Albo cannot
have both, because **its exclamation stem is thinner than every reference
relative to the x-height** — 0.181 against 0.217–0.259. That is not a fault in
the mark: `! thick ÷ i stem` reads 1.32 against the references' 1.19–1.37, in
band, because Albo is simply a lighter face than all six. Shipped on the
direct measurement (dot = period, 6 of 6 references) rather than on the derived
ratio, which is confounded by the stem. `ALBO_EXCL_DOT` 0.76 is the
stem-matched arm and is one word away.

### 5. Three marks broke on the scale-up, and the gate found all three

Every one is the same shape — **a fixed separation, or an unscaled dot, against
a mark that grew**:

- `quotedblleft` / `quotedblright` merged **2 contours → 1**: a double quote
  drawn as a single blob. `DQ_GAP` was a centre-to-centre distance, so a bigger
  mark closed the white. The owner's round-94 complaint was *"give more space
  for double quotes so they don't touch"* — a statement about the WHITE — so
  the pair is spaced by white now, measured off the first mark's own ink.
- `quotedblbase` went **2 → 4**: built on the raw `DOT_R` while its tail took
  the punctuation dials, so a small dot carried a large mark's tail and the two
  detached. Every other comma in the face is on `MDOT`.
- `U+0326` comma-below and the four `Ș ș Ț ț` that carry it went **1 → 2** and
  **2 → 3**: an accent on an accent-sized dot, whose tail grew with punctuation
  it is not. `comma_tail` takes an explicit `k` now, and the accent passes 1.0.

**None of these is visible in a render of the mark that changed** — the comma
itself is fine at every setting. They were found by the contour census in
`gates.sh`, and the hair-gate churn they caused (a dozen glyphs entering and
leaving the Regular's and Italic's hair lists) was the **cut ripple**, not new
drawing faults: `cut.py`'s phase counter advances per contour, so a
contour-count change re-cuts every glyph built after it. Fixing the three
contour counts returned the hair lists to the baseline exactly.

### 6. The colon closes as its dot opens

Both of the colon's dots are anchored inside the x-height band, so every unit
the dot gains, the white loses two: swept 0.560 at `MARK_DOT` 1.0 down to
0.346 at 1.62, out through the references' floor of 0.401. **The mark a
punctuation scale-up is most likely to close is the colon** — the opposite of
"readable at small sizes". `ALBO_COLON_SPAN` 1.05 lets the upper dot sit a
little proud of the x-height; white 0.433.

## What was checked and found CLEAN

- **The tittle's gap over the x-height.** Growing the dot on a fixed centre
  took it 0.209 → 0.179 at `TITTLE` 1.40 — a bigger tittle that reads as a
  MERGED one. `dot_y` rises with the tittle now, so the gap held at 0.212. It
  remains 5% under the references' 0.224 floor, which is pre-existing and was
  not made worse.
- **The `tittle offset`** (tittle centre against its stem's) is 0.006, inside
  the references' −0.010…+0.024. Nothing to do.
- **`ö` and `ü` centring** after the optical table: +0.002 both, against the
  references' −0.000…+0.021 and −0.013…+0.020. The table touches only `a` and
  `e`, as intended.
- **All four cuts build**, and the contour census is unchanged at 982 glyphs.
- **`approved.py`**: both owner-ruled glyphs unchanged. **`bench_fit --check`**:
  `build.py` still matches the bench.
- **`cmp_touch`**: the raised `?` scaled its hook uniformly about its own
  lowest point, which carried the upper-left arm **25 units left**; in the
  italic, where the slant already leans that arm backwards, `U?` closed to
  0.0093 em against the 0.012 floor. Swept: `U?` is the ONLY pair under the
  floor — `V? W? Y? T?` all sit at 0.03 em or better. Fixed with a kern pair
  and not a wider fitting band, per `docs/albo-capital-spacing.md`: widening
  the `?`'s left bearing would loosen it after all 26 lowercase to fix five
  capitals.

## The stale-doc trap this round walked into

`marks.py`'s `g_question` docstring said *"0 is the round-77 hook"*. It is not:
`QUESTION_VARIANTS[0]` is `_q8`, the original Albertus-heavy mark, and `_q0` is
at index 1. The ascender change was therefore applied to a constructor nothing
builds. **The `!` rose and the `?` did not, identically, across a four-rung
ladder** — which is the only reason it was caught, and is exactly the dead-dial
signature this repo keeps rediscovering. The docstring is corrected in place
and says what it cost.

## Still open

- `ALBO_EXCL_DOT` — shipped 1.00 (dot = period). 0.88 and 0.76 built and
  rendered; the owner's eye decides.
- `ALBO_MARK_TALL` — shipped 1.0 (the ascender, as asked). 0 / 0.35 / 0.70
  built and rendered, with the references' cap-line band on the page.
- The middle dot's wedge — apex, tilt and aspect are dials; five arms rendered.
- The `?` variant selection and the `1`'s fitting, both carried over from
  round 362 and still unruled.

## Round 375 — 2026-09-24: seated, smaller, and the Bold

Owner, on the round-374 specimen: *"quotes are too big. punctuation needs to
rest on baseline better. take a pass at all of them to make sure recent
changes work."* All numbers /1000 em, lowest ink against the baseline.

| finding | measured | fix | after |
|---|---|---|---|
| dots float | Albo . : ! ? … bottom at 0 to +3, its o at −15; six references sink their dots a median **0.88 of their own o's overshoot** (Times −13/o −13, Baskerville −16/−16, Charter −9/−9, Georgia −10/−15, Hoefler −17/−22, Palatino −5/−15) | `DOT_SINK` 13 roman / 6 italic (the italic o dips 7); every baseline dot and the comma's dot take `BY` | roman −10 to −13, italic −3 to −6 |
| curly quotes too big | 305 tall; references 253–285, median 262 | `CURLY_SCALE` 0.86, scaled as a unit about its own top | 262 |
| **? dot nearly touching its hook** | **2 units** of white: the hook's clearance was computed for `DOT_R*1.1` while round 369 drew the dot at `MDOT*1.1`, 1.65x bigger | clearance from where the dot now is; dot = the period's (was 1.1x) | 49 units (the ! has 56) |
| ellipsis never scaled | dots 80 wide beside a period of 123 — built on raw `DOT_R`, which round 369's scale-up missed | the period's dot, white held at one dot | 119 |
| **the Bold's marks 1.7x too big** | every mark is built from S, so the Bold (S 116) grew them 1.73x: period 214, comma 510, quote 453 against Georgia/Times/Palatino/Charter Bold 152–193 / 304–356 / 288–343. Round 369 fitted the 400 only | dots scale by `WF = (66.9/S)^0.4`; the comma tail's LENGTH is laid out in the 400's stem at every weight (its width still comes from the pen) | 172 / 322 / 289, all in band; the 400s byte-identical |
| **comma-below fused to its letter** | ș ț Ș Ț were one contour with their mark in every cut — the composite hung the mark's top at the baseline while the s dips 15 through it — so they read as the cedilla forms ş ţ beside them | U+0326 composites hang `OVER + 0.30 S` lower; cedilla and ogonek untouched | detached |

**Found and deliberately NOT changed:** the STRAIGHT quotes `'` `"` are
*short* — 182 tall against the references' 240–292 and against the curly
quotes' 262 — so the two quote forms disagree. Growing them contradicts
"quotes are too big", so they are left and flagged.

**Checked CLEAN:** the ! dot equals the period in all four cuts; the colon's
upper dot top sits on the x-height; the comma stays in band after the sink
(roman −183 bottom); the double quotes stay separated (spaced by white, round
369); contour census unchanged (982); approved glyphs unchanged; gates
unchanged; touch and hair sweeps on both Bolds identical to before the round.

## Round 376 — 2026-09-24: "yes to all"

- **Straight quotes match the curly ones.** 182 (roman) / 163 (italic) tall →
  260 / 259, against the curly quotes' 262 and the references' 240–292.
  `STRAIGHT_TALL` 1.44 roman / 1.66 italic; the body length is laid out in the
  400's stem at every weight, as the comma's tail is (round 375), so the Bold's
  come out 276 / 270 rather than 1.7x.
- **The ? is narrower, same shape.** It stays the owner's 2026-09-13 mark and
  stays at the ascender, but raising it scaled it uniformly, so it had grown
  wider too: 0.973 of the x-height against references 0.63–0.80,
  width/height 0.583 against 0.38–0.52. `Q8_W` 0.86 narrows the spine only
  (stroke widths still from the pen): width/height 0.513. It is still wider
  than the references against the x-height because it is taller than theirs,
  by ruling.
- **The italic 1's left side** (round 374 recorded "needs an O1 kern"). It was
  not one pair: every pair ENDING in the 1 was short (O1 0.016 em vs refs
  0.133, 01 0.058 vs 0.157, 11 0.087, 21 0.077, 81 0.091) while every pair
  starting with it was in band — a bearing. `build.ALD_FIG_ADJ['1']` +45 left,
  italic only, plus an O1 kern +36: O1 0.094, 01 0.103, 11 0.130, 21 0.119,
  81 0.136.
- **Checked and NOT changed: the italic f before a word space.** Seen on the
  round-374 specimen ("the fishermen", "still feel") and measured: the 2-D
  white from the previous word to the f is 0.83–0.87 of the white to an n,
  where the references run Times 0.77–0.85, Flanker 0.77–0.92, Georgia
  0.55–0.80. Ordinary italic-f behaviour; left alone.

## Round 380 — 2026-09-24: the italic's own marks, and the ?'s contrast

Owner: *"italic punctuation is too big"* and *"question marks do not fit albo
style (mostly line contrast)."*

- **Italic marks, against ITALIC references for the first time** (Flanker,
  Pagella, Coelacanth, Poetica, Georgia, Times, Palatino italic; per x-height):
  period 0.267 → 0.226 (median 0.218 — italic references carry smaller dots
  than roman ones), comma 0.464×0.630 → 0.389×0.553 (was outside the band on
  both axes; median 0.384×0.540), curly quote width 0.415 → 0.357 (max 0.384).
  `IT_DOT` 0.85, `IT_COMMA_W` 0.80, `IT_COMMA_LEN` 0.88, `IT_QUOTE` 0.90,
  italic only; the roman is byte-identical.
- **The ?'s line contrast.** Thick/thin on the hook (chamfer ridge p90/p10):
  1.32, against Albo's own o and c 1.93, its 3 2.76, Georgia's ? 2.47, Times'
  4.26 — near monoline, because round 19's 0.78 S floor held every part of the
  hook at "Albertus weight". The floor drops to the family's bowl hairline
  0.46 S (roman: 1.32 → 2.06, on its o; Bold 2.04 vs its o 1.96). The italic's
  o runs 2.88; floor 0.36 alone saturated at 2.29, so the hook's light arm
  plan also thins in the italic (`Q8_LIGHT` 0.45): 2.50. The THICK is
  unchanged in every cut, so the 2026-09-13 ruling's weight holds where the pen
  is heavy. Hook-to-dot white 39–72 units across the cuts; no hair, touch or
  dent finding.
- Seen and not fixed: the ?'s outline is faceted, like the round-377 ampersand
  and — per the owner's note — the italic figures.

## Round 382 — 2026-09-24: the italic ? had its weight on the wrong side

Owner: *"italic question mark has inverted thickness, the top left should be
thick."* Round 380 did this: to raise the italic hook's contrast it thinned
the LEFT ARM and TOP (plan 0.45 there), so the weight moved right. Measured by
clock position about the hook (median ridge thickness / the hook's thickest):
round 381's italic read left 0.40, top-left 0.45, right 0.91, lower-right 1.00.
Reference italics put it the other way: top-left Flanker 1.00, Coelacanth 1.00,
Georgia 1.00, Times 0.86; right side 0.43–0.76. Seen at size, the references'
weight sits at the START of the hook — Georgia's ball terminal, Flanker's
heavy flat swash — where Albo's began on a thin tapered arm.

The italic gets its own width plan along the hook (`Q8_PLAN_IT`): heavy up the
left arm into the top-left, lighter from t 0.28 (`Q8_CROWN_T`, laddered
0.16 / 0.22 / 0.28), medium down the right, heavy into the foot; its floor
drops to 0.24 S so the plan, not the floor, sets the thins. Italic: top-left
0.45 → 0.98, contrast 3.18. Bold Italic: top-left 1.00, crown 0.51, right
0.74 — the references' pattern outright. Roman untouched.

**Instrument note, recorded because it cost a wrong turn:** the first ladder
of crown/right values returned three identical rows — a dead dial. The crown
point sat at t 0.34, past where the hook actually crowns, and the 0.36 S floor
was holding the right side. Moving the crown point and lowering the floor made
both live.
