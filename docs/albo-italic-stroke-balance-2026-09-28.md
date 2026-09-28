# Albo Italic: stroke balance, the c's bottom left and its kin (2026-09-28)

Owner, 2026-09-28: *"italic c is too thick on it's bottom left, address it to
match others. find similar issues in italic and address those as well."*

This doc takes that report as given. It measures how much too thick the c is,
fixes it behind a dial, surveys the italic lowercase (Italic 400 and
BoldItalic 700) for the same kind of fault, and fixes the clear cases the same
way. **Every fix is behind an env dial that defaults to today.** A default
build is outline- and advance-identical to the tree it started from
(`cmp_outlines.py --advances`: IDENTICAL for both cuts). Nothing here ships
until the owner rules.

**Surveyed:** simulator `5040c69`, `outlines/glyphs/aldine.py`, built with
`build_env.sh`'s `ALBO_ITA_ENV` / `ALBO_BIT_ENV`.
**How sure:** every number below was measured on built fonts in this session
(unhinted FreeType, 1000 ppem, so 1 px = 1 unit, unsheared by the build's 13°).
Where a claim rests on reading code, the doc says so.

## 1. The measurement, and why it is by direction

Albo's rule is **direction before width** (`docs/albo-method.md` §1). Under one
pen, a stroke's width depends on the direction it travels. So the fair
comparison between two letters is their width at the same stroke direction,
not at the same place.

**Instrument** (scratch scripts `medial.py`, `pen_target.py`, `cfit.py`,
`rankpen.py`; the method is in the appendix so they can be rebuilt):

- Rays from the bowl center every 2°.
- On each ray, take the first ink run met going outward. The point of maximum
  distance-transform value on that run is the medial point, and 2 × EDT there
  is the stroke width (the largest inscribed disc).
- The stroke direction is the chord between the neighboring rays' medial
  points (mod 180; 0 = horizontal, 90 = vertical).
- For most letters, the center is the enclosed counter's centroid. For the c,
  it is the drawn ellipse center: the left stroke's midpoint at the center
  height plus 1.167 × rx. Its bounding-box center sits 28 units left of the
  drawn center, and that mislabels every angle.
- **The sibling pen** is the median width at each direction, in 5° bins, over
  the o, the a and the e. These three agree with one another to within ~5
  units at every direction at the 400. At the 700 the e is itself an outlier
  (§3), so the pen there is the o and the a.

### 1a. The c against the pen (the ask)

Mean of (c − pen), in units, over the stated arc. Ray angles are about the c's
drawn center. The lower-left core is 190–265°, which excludes the bottom
finial's swell.

| cut | arc | today | `C_LOW=1` | `C_LOW=1 C_UP=1` |
|---|---|---|---|---|
| Italic 400 | lower left 190–265 | **+11.6 (+17%)** | **+2.4 (+4%)** | +2.1 (+3%) |
| Italic 400 | upper left 110–175 | +19.7 (+50%) | +19.6 (+50%) | **+6.5 (+17%)** |
| BoldItalic 700 | lower left 190–265 | **+13.3 (+14%)** | **+5.8 (+7%)** | +5.2 (+6%) |
| BoldItalic 700 | upper left 110–175 | +27.2 (+50%) | +27.1 (+49%) | **+14.9 (+27%)** |

The same numbers by position (ray-angle widths at the 400; siblings measured
about their own centers):

| ray ° | 180 | 210 | 240 | 270 |
|---|---|---|---|---|
| c today | 80 | 85 | 82 | 60 |
| c `C_LOW=1` | 74 | 74 | 75 | 48 |
| o / a / e | 66 / 60 / 68 | 77 / 75 / 75 | 72 / 80 / 68 | 44 / 50 / 47 |

`cmp_weight_survey.py` (ridge p90 = "thick"):

- **Italic c:** thick 85.8 → **76.8** (`C_LOW`), against the o's 75.3. Its
  stroke median goes from +14% of the lowercase to +9% (`C_LOW`) and +4%
  (both dials).
- **BoldItalic c:** thick 117.4 → **109.1**, against the o's 109.9.

The table the c was drawn from (`C_RING`) is Flanker's own c, which has a
near-vertical stress. The o beside it in every word is on the Aldine nib's
oblique stress. Neither letter has a stem, so the eye compares them directly.
That is why the owner saw the c and not d, q, b or p, which carry the same
excess (§3, row 6).

## 2. What each dial does, and the recommended value

| dial | default (today) | recommended | what it does |
|---|---|---|---|
| `ALBO_ALD_C_LOW` | 0 | **1** (the ask) | Moves the c's lower left onto the **o's own pen**: O_THICK, O_THIN re-spread by CON_O, O_PEN, and the o's sqrt(84 S) law above stem 84. The width is read from each centerline sample's direction, then smoothed with a moving average. The blend is full over normalized angles 195–250 and fades out by 300. |
| `ALBO_ALD_C_UP` | 0 | 1, **owner's call** | The same move for the upper left (full 125–165, fading in from 95). It is the larger deviation (+50%) but was not named. |
| `ALBO_ALD_E_S_UP` | 0 | **1** | Puts the e's widths on the o's sqrt(84 S) above stem 84. This is round 272's o fix applied to the e. It changes the 700 only; the Italic 400 is byte-identical at any value. |
| `ALBO_ALD_V_THICK` | 1.0 | **0.88** | Scales the v's thick-diagonal table only, holding its two end keys. |
| `ALBO_ALD_K_NIB` | 0 | **1** | Multiplies the k's stem by ALD_NIB (0.92). This is what round 411 did for the j and the t (owner: "same nib"). |

The c's two dials cross over normalized angles 165–195 in complementary raised
cosines, so neither dial alone leaves a step. Three rules hold in every arm:

1. **The top end is never blended.** `fin_floor()` reads the c's width at its
   top end, and every italic finial is sized from that width. Checked: with
   both c dials on, only c, cent, the c-accents and uniE004 move.
2. **The outer contour is kept; only the counter grows.** This is the o's rule.
   Each sample's center moves outward by half of what its width lost. The c's
   bbox and advance are identical to today at both weights (38, −8, 339, 445 /
   adv 362 at the 400).
3. **Past the bottom, the width takes a running maximum into the finial.** The
   counter's lowest point is the letter's bottom.

The e's E_S_UP moves its loop outward the same way past the shoulder; the bar
stays on its own line. The BoldItalic e's bbox (37, −7, 418, 457) and advance
(476) are held.

**The recommended set:** `C_LOW=1 E_S_UP=1 V_THICK=0.88 K_NIB=1`, plus
`C_UP=1` if the owner wants the whole c on the o's pen.

## 3. The survey, ranked

**The metric:** the same stroke role, measured against the siblings that share
it.

- **Bowls:** mean (w − pen) by direction per quadrant (`rankpen.py`).
- **Stems:** the horizontal run at y = 100 / 300 / 600, unsheared.
- **Diagonals:** the ridge width binned by direction, 98–128°.

A finding is "clear" when the siblings agree with one another and the letter
stands outside them at both weights.

| # | letter · segment | 400 | 700 | against | status |
|---|---|---|---|---|---|
| 1 | **c lower left** (asked) | +12.5 (+19%) | +14.8 (+17%) | o a e pen | FIXED `C_LOW` |
| 2 | **c upper left** | +18.0 (+45%) | +24.9 (+46%) | o a e pen | FIXED behind `C_UP`, owner's call |
| 3 | **e lower left, 700 only** | +0.4 (clean) | +20.6 (+23%) | o a pen | FIXED `E_S_UP`: 124–131 → 106–111 at dir 105–125, against o/a 100–111 |
| 4 | **v thick diagonal** | 88–89 | 121–122 | y 76, x 72, w 72 / y 104, x 99, w 99–100 | FIXED `V_THICK=0.88`: 76–78 / 106–108 |
| 5 | **k stem** | 68–69 | 116–117 | i l h 60–64, b 62, d 63–65 / i l h 104–108 | FIXED `K_NIB=1`: 63 / 107 |
| 6 | d, q bowls; b, p lower right | d/q UL +12..+14, LL +14; b/p LR +16..+22 | d/q UL +18, LL +14; b/p LR +17..+29 | o a e pen | **NOT FIXED: owner question.** Same direction as the c. But these four with the c are five of the eight bowl letters, so "heavy" is the majority, and all four bowls hang on stems. Recommending a change would mean the o, a and e define the pen for the whole face. That is a ruling, not a measurement. |
| 7 | j, t stems | j 75, t 72 against i 62 | j 99–103, t 96–99 against i 104–107 | i | Owner-ruled, round 411 ("same nib", arm `nib` over `trc`). Not touched. |
| 8 | f | | | | Owner-ruled, round 373 (F_INK 0.88). Not touched. |
| 9 | g | | | | Approved letter (`approved.json`, round 409). Not touched. |
| 10 | w thick 72 / 99 (lighter than v, y) | | | | Owner-ruled W_THICK 0.86 (2026-09-16, "reads as a blot"). Not touched; after row 4 the v, x, y and w agree to within 6. |

**Checked and found CLEAN:**

- **Stems of i l h n m r u b d p q:** 60–65 at the 400 and 104–108 at the 700,
  all within ±3 of one another. The k was the lone outlier (row 5).
- **Arch shoulders of n m h r u:** they share `hm_arch`, and their runs agree.
- **o, a, e at the 400:** they agree with one another by direction to within
  ±5 units over every quadrant where they overlap (o LL −0.2, e LL +0.4,
  a LL +7.0 after the owner's own A_BL "slightly thicker on bottom left").
- **Hairlines:** the y's (34–41 at dir 22–82) matches the v's (34–48). The x
  thick diagonal (72 / 99) sits with the y and the w.
- **The Italic 400 e:** clean. Its lighter overall weight in
  `cmp_weight_survey` (−26% stroke median) comes from the bar and the eye's
  hairline, not from its loop, which sits on the o by direction.

## 4. Interaction with the half-overshoot finding

The finding is `docs/albo-italic-size-baseline-2026-09-28.md`: the italic's
round letters carry half the roman's overshoot, and it awaits the owner's
choice. **These fixes do not move any letter's baseline or x-height sitting.**

- **The c:** the first cut of `C_LOW` thinned about the centerline. That
  raised the c's ink bottom from −8 to 0 at the 400 and to +1 at the 700,
  which removed all of its overshoot and made that finding worse. The shipped
  dial thins from the inside, so the c's bottom stays at −8 at both weights,
  top 445 / 465, advance unchanged.
- **The e:** `E_S_UP` thinned about the centerline did the same at the 700
  (−7 → −2 and 457 → 452). It too thins from the inside now, and holds
  −7 / 457.
- **Composition:** if the owner picks an overshoot fix that moves the c's or
  the e's outer bottom down, these dials compose with it. They move only the
  inner edge.

## 5. Drawn and cut

- **A refitted C_RING table** (4 fitting passes, keys fitted to the pen by
  direction; mean |w − pen| 14.2 → 2.2 units): cut. Neighboring keys stepped
  by 7–15 units. The key-to-key smoothstep turned each step into a flat and a
  corner on the outer left contour, visible at 700 px. The pen-by-direction
  construction replaced it.
- **A fitted 293 key** (it went to 16 units): cut. The bottom finial then stood
  on a hairline stalk.
- **C_LOW's first fade window** (out by 305) cut a V-notch into the counter at
  a ≈ 285–295: the pen's thin direction lies just before the finial swell.
  Fixed by fading out by 300 and taking a running maximum past the bottom.
- **Thinning about the centerline:** cut for the c and the e (§4).
- **A V_TW change** instead of V_THICK: not tried. The v's hairline is not
  heavy (34–48 against the y's 38–44), so V_TW would have thinned a stroke
  that is right.

## 6. Found and not fixed

- **The BoldItalic c has a narrow notch** in its counter at the bottom right,
  where the bottom turns up into the finial. It exists today (visible at
  150 px x-height), and the gates (glitch, hairs) do not flag it. With
  `C_LOW=1` it is ~4 units deeper. The likely cause, not verified, is the
  inner offset cusping on the tight turn under the finial's swell. Reported,
  not touched.
- **The BoldItalic e fails the Regular's e-mouth gate** (`etrace/e_hint_gate.py`,
  not gated for italics) today: reader-size worst 0.169. `E_S_UP=1` improves
  it to 0.118, and the 9–12 ppem worst from 0.765 to 0.549. Recorded as a side
  effect, not a claim.

## 7. Gates

`instruments/poor_gates.sh BASE ARM "Italic BoldItalic"` was run on every arm
(`C_LOW`, `C_LOW+C_UP`, `K_NIB`, `V_THICK=0.88`, `E_S_UP`, all five together,
and the recommended four). Every run returned **POOR GATES: no delta**:

- hairs (`--letters` and full): no new rows
- touch: 0 / 0 → 0 / 0
- counter dents: unchanged
- glitch on the moved glyphs: 0 findings
- contour census: unchanged (1056)
- approved: both letters unchanged

**What moves with each dial:**

- `K_NIB` also moves the Greek λ in the Italic by 1–2 units at four points.
  `greek_italic.py` keys λ to the k (`VIA_ROMAN`).
- `E_S_UP` moves the e composites and æ / œ.
- `cmp_aldine_metrics.py` has no c, k or v rows. Its e row is the 400, which
  `E_S_UP` leaves byte-identical.

## 8. Proof

Lossless PNGs at native pixels, one per letter, plus `proof_all.png`. They are
in the session scratchpad (`italic-c/proof_{c,k,v,e,all}.png`).

- **Left:** the letter among its siblings (o c e a, l k h, v y w, o e a) at a
  150 px x-height, unhinted 8-bit.
- **Right:** three words at the reader's 54 px through `fit_audit/legib.Renderer`
  (unhinted, 2-bit, HarfBuzz kern), then the letter alone, magnified 3×
  NEAREST.

## Appendix: re-creating the instruments

- **`glyph(font, ch)`:** FreeType `FT_LOAD_NO_HINTING` at 1000 ppem, padded by
  60 px. Each row is resampled at x + y·tan 13°, with y measured from the
  baseline, which unshears it. Threshold at 0.5 coverage.
- **`samples()`:** as §1. The first ink run on each ray; width = 2 × max EDT
  on the run. Direction = atan2 of the chord between the medial points at
  a ± 2°.
- **`c_samples()`:** the c's center = the midpoint of the first ink run on the
  row at y = 1.015 × 223.5, plus 1.167 × 111.8. Those are the drawn center
  height and rx from `_c_ring` at xh 429, times the build's italic lowercase
  scale (`IT_LC_SCALE` 1.015 × `IT_LC_SETW` 1.15 in x).
- **`pen_curve()`:** all free-arc samples of the sibling letters, median per 5°
  bin of direction, with gaps interpolated circularly.

  Free arcs, in ray-angle degrees about the bowl center:

  | letter | free arc |
  |---|---|
  | o | all |
  | c | 100–300 |
  | e | 170–300 (the bar blocks its upper rays) |
  | a, d, q | 95–290 |
  | b, p | 290–75 |
