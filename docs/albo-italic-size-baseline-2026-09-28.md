# Albo Italic against its Roman: size and baseline sitting (2026-09-28)

Owner, 2026-09-28: *"check if italic is smaller and higher off the baseline
than roman."* This doc starts from that report. It measures how much smaller
and how much higher the italic is, and why.

**Surveyed:** the round-426 fonts as built (simulator `24a556b`/`289d5d1`,
`Albo-{Regular,Italic,Bold,BoldItalic}.ttf`, upm 1000). The firmware was read at
crosspoint-reader `fd2efadc3`. Nothing was built and nothing was changed.

**Method:** everything comes from unhinted FreeType (`FT_LOAD_NO_HINTING`).
Font-unit figures come from a 1000 ppem raster (1 px = 1 unit), plus
fontTools bounding boxes. Pixel figures come from `fit_audit/legib.py`'s
`Renderer`, which is the converter's pipeline: unhinted, 8-bit coverage cut to
2-bit, HarfBuzz placement with kerning. The scripts are in the session
scratchpad (`italic-size/m1.py`–`m4.py`, `fig.py`). Their method is written out
in the appendix, so they can be re-created once the scratchpad is gone.

## 1. Verdict

- **YES, it is smaller.** Weighted by English letter frequency, the italic's
  lowercase body is **435.4 units tall against the roman's 446.8 (−2.5%)**. It
  also sets **0.89** of the roman's width on the same text. That makes the
  apparent area (height × width) about **0.87** of the roman's. The reference
  italics are 0.986–1.018 on height (Georgia 1.001, Charter 0.986,
  Palatino 1.018).
- **YES, it sits higher.** The same weighting puts the italic's body bottom
  **7.5 units higher** than the roman's (−1.0 against −8.5). Every reference
  italic sits **lower** than its roman, by 1.6 to 3.0 units. The cause is
  the round letters, which carry **half the roman's overshoot or less**:

  | ink bottom, units | o | c | e |
  |---|---|---|---|
  | Regular | −15 | −13 | −15 |
  | Italic | −7 | −8 | **+6** |

  The italic `e`, the commonest letter in English, **does not reach the
  baseline at all**.
- **At reading size this is one whole pixel row.** At 12–18 pt on the X3
  (25–37.5 ppem), the roman's `o e c u` each light a row **below** the
  baseline. The italic's `o e c u` light nothing there. At 2x on the phone
  (58–75 ppem), the italic `e` stops at the baseline where the roman `e`
  dips a row below it.
- **The line itself is NOT placed higher.** The vertical metrics are the same
  in all four files. The firmware takes every style's baseline from the
  REGULAR's ascender. See §5, which found these clean.
- **The earlier "x-height 1.000/1.013" came from the wrong instrument.** It
  measured the `x`'s top, which is a serif flare. The `x` is the one letter
  that is TALLER in the italic (457 against 451), while `n m` are 14–15 units
  shorter. See §4.
- **The Bold pair is mostly fine on size.** The Bold Italic body is 1.003 of
  the Bold's height. It still sits 3.3 units higher, from the same
  half-overshoot on `o c e`.

## 2. Measurements

### 2a. Per-letter extents (outline bounding boxes, units)

| | x | v | n | m | r | u | o | e | c | s | a |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **top** Regular | 451 | 443 | 447 | 448 | 439 | 430 | 444 | 444 | 442 | 447 | 433 |
| **top** Italic | 457 | 456 | 437 | 437 | 458 | 437 | 442 | 443 | 445 | 439 | 445 |
| **top** Bold | 461 | 448 | 450 | 451 | 443 | 430 | 444 | 444 | 438 | 452 | 438 |
| **top** BoldItalic | 470 | 467 | 446 | 445 | 457 | 438 | 444 | 457 | 465 | 456 | 453 |

| bottom, units | n | m | h | i | l | u | x | o | e | c | s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Regular | −1 | −1 | −1 | −1 | −1 | −16 | −22 | −15 | −15 | −13 | −17 |
| Italic | −7 | −8 | −8 | −8 | −6 | −9 | −19 | −7 | **+6** | −8 | −27 |
| Bold | −1 | −1 | −1 | −1 | −1 | −19 | −32 | −15 | −15 | −9 | −22 |
| BoldItalic | −7 | −10 | −11 | −11 | −11 | −13 | −28 | −8 | −7 | −8 | −40 |

The italic's straight-stem letters sit slightly LOWER than the roman's (−7
against −1), because their exit strokes curve through the line. The round
letters sit higher. At 1000 ppem the exit strokes' half-max bottom is −1, so
those −7s are thin tips, not mass (§2b).

| | ascender b d h k l | f | descender p q | y | g | j | caps H I E T / O | figures |
|---|---|---|---|---|---|---|---|---|
| Regular | 771 | 763 | −281 | −277 | −294 | −298 | 676 / 689 | 1 433, 6 638, 7 −223 |
| Italic | 767–783 | 799 | −286 | −263 | **−197** | −295 | 675–676 / 689 | 1 433, 6 673, 7 −226 |
| Bold | 771 | 786 | −281 | −311 | −306 | −317 | 676 / 690 | 6 639 |
| BoldItalic | 767–802 | 809 | −287 | −272 | **−197** | −303 | 675–676 / 690 | 6 678 |

The capitals are identical and so are the figures, except the italic 6 and 8,
which are about 30 units taller. The italic ascenders run up to +12 units
taller. The italic **g's descender is −197 against −294**, a third
shallower. That was already recorded as misfit #6 in
`docs/albo-misfit-audit-2026-09-18.md:98`. The italic g is **owner-approved**
(`tools/wedge_serif/approved.json`, "Italic:g", round 409). Its shallow loop
adds to how much less ink a line of italic puts below the baseline. It is not
touched here without a ruling.

### 2b. The body band, per letter (half-max of each letter's row profile, units)

Top and bottom are where a letter's row coverage falls to half its median in
the 30–60% band of its own height. Unlike a bounding box, this ignores serif
tips and hairline flicks.

| TOP | n | m | u | x | a | o | e | c | s | r | v | w | z |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Regular | 441 | 441 | 430 | 431 | 431 | 441 | 443 | 442 | 442 | 437 | 430 | 422 | 430 |
| Italic | **427** | **426** | 426 | 442 | 431 | 436 | 438 | 445 | 436 | 438 | 447 | 431 | 434 |
| Georgia / It | 489 / 487 | 491 / 489 | 484 / 483 | 482 / 487 | 492 / 488 | 491 / 488 | 494 / 489 | 494 / 492 | 493 / 490 | 490 / 490 | 482 / 487 | 482 / 485 | 482 / 478 |
| Charter / It | 486 / 480 | 488 / 480 | 490 / 473 | 481 / 484 | 489 / 481 | 487 / 479 | 490 / 480 | 490 / 484 | 489 / 480 | 490 / 481 | 481 / 482 | 481 / 477 | 481 / 483 |
| Palatino / It | 467 / 468 | 468 / 471 | 456 / 468 | 462 / 475 | 466 / 474 | 469 / 473 | 471 / 475 | 473 / 478 | 469 / 474 | 469 / 475 | 458 / 469 | 458 / 466 | 455 / 470 |

| BOTTOM | n | m | h | i | l | u | x | a | o | e | c | s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Regular | −1 | −1 | −1 | −1 | −1 | −13 | −1 | −14 | −12 | −14 | −12 | −13 |
| Italic | −1 | −1 | −1 | −1 | −4 | −3 | −13 | −12 | **0** | **+10** | −2 | −15 |
| Bold | −1 | −1 | −1 | −1 | −1 | −12 | −8 | −11 | −9 | −13 | −8 | −12 |
| BoldItalic | −1 | −1 | −1 | −6 | −5 | −6 | −22 | −6 | +6 | −3 | −4 | −30 |
| Georgia It | 0 | 0 | 0 | −8 | −9 | −8 | −8 | −8 | −10 | −9 | −12 | −11 |
| Charter It | −1 | 0 | −1 | −6 | −8 | −6 | −5 | −7 | −5 | −8 | −9 | −7 |
| Palatino It | −3 | −2 | −2 | −7 | −7 | −7 | −11 | −4 | −7 | −10 | −12 | −14 |

Frequency-weighted over `e a o i n s r u c m w v x z` (English letter
frequencies; `i` is left out of the top because its dot sets it):

| | top | bottom | height | top / roman | height / roman | bottom Δ vs roman |
|---|---|---|---|---|---|---|
| Regular | 438.3 | −8.5 | 446.8 | | | |
| **Italic** | 434.5 | −1.0 | 435.4 | 0.991 | **0.975** | **+7.5 (higher)** |
| Bold | 438.4 | −7.3 | 445.7 | | | |
| BoldItalic | 442.9 | −4.0 | 446.9 | 1.010 | 1.003 | +3.3 |
| Georgia It | | | | 0.995 | 1.001 | −2.9 |
| Charter It | | | | 0.983 | 0.986 | −1.6 |
| Palatino It | | | | 1.011 | 1.018 | −3.0 |

Albo Italic is the only italic in the set that is both shorter than 0.986 and
sits higher than its roman.

For the whole alphabet with every letter weighted equally
(`acemnorsuvwxz`×2), the half-max band is almost equal: roman −7..436,
italic −5..434. The difference only shows up when the letters are weighted as
text uses them. That is because the italic's tall letters (`x v r c`) are
rare and its short or floating ones (`e o n m s`) are common.

**Width and ink**, on the same string: the italic sets **0.893** of the
roman's width (Bold Italic 0.897) and carries 0.969 of its ink. On the same
string, Georgia sets 1.035, Charter 0.952 and Palatino 0.898.

### 2c. At reading size (reader pipeline, 2-bit, px from the baseline)

Each cell is the lowest ink row / highest ink row. Row −1 is the first row
below the baseline.

| ppem | style | n | o | e | c | a | s | u |
|---|---|---|---|---|---|---|---|---|
| 25 (12 pt, X3) | Regular | 0/11 | **−1**/11 | **−1**/11 | **−1**/11 | −1/11 | −1/11 | **−1**/11 |
| | Italic | 0/11 | **0**/11 | **0**/11 | **0**/11 | −1/11 | −1/11 | **0**/11 |
| 33.3 (16 pt, X3) | Regular | 0/15 | −1/15 | −1/15 | −1/15 | −1/15 | −1/15 | −1/15 |
| | Italic | 0/15 | 0/15 | 0/15 | 0/15 | −1/15 | −1/15 | 0/15 |
| 37.5 (18 pt, X3) | Regular | 0/17 | −1/17 | −1/17 | −1/17 | −1/16 | −1/17 | −1/16 |
| | Italic | 0/**16** | 0/17 | 0/17 | 0/17 | −1/17 | −1/17 | −1/16 |
| 66.7 (16 pt, phone 2x) | Regular | 0/30 | −1/30 | −1/30 | −1/30 | −1/29 | −1/30 | −1/29 |
| | Italic | −1/**29** | −1/30 | **0**/30 | −1/30 | −1/30 | −2/29 | −1/29 |
| 75 (18 pt, phone 2x) | Regular | 0/34 | −1/34 | −1/34 | −1/33 | −1/33 | −1/34 | −1/32 |
| | Italic | −1/**33** | −1/33 | **0**/33 | −1/34 | −1/33 | −2/33 | −1/33 |

At 1x, the roman line has a lit row under the baseline wherever a round
letter stands, and the italic line does not. At 2x, the `e` still floats and
the `n` is a row short. When `acemnorsuvwxz` is weighted equally, the whole
line's half-max band and ink centroid are the same to 0.1 px at every size
from 16.7 to 75 ppem, because the rare letters average the common ones away.

**Proof figure:**
`scratchpad/italic-size/compare.png` (2810×1148, PNG, lossless). It shows
"once a mouse" in Regular then Italic on ONE baseline, with a red guide at
y=0 and a blue guide at x-height 429, drawn on paper pixels only. There are
four rows. The first is 37.5 ppem 2-bit at nearest ×4. The second is 75 ppem
2-bit at nearest ×2. The third is Regular/Italic at 200 ppem, 8-bit, 1:1. The
fourth is Bold/Bold Italic at 200 ppem, 8-bit, 1:1. In the 200 ppem row the
italic `o c e` clearly stop short of where the roman's dip, and the `n m`
crowns sit under the blue line. This figure is EVIDENCE (baseline sitting at
reading size).

## 3. Mechanism

1. **The italic o carries half the overshoot, by construction.**
   `outlines/glyphs/aldine.py:1897-1899`: `ry = xh/2 + OVER*0.5`, centered so
   the ink runs −OVER/2..xh+OVER/2 (±7). The roman o is
   `outlines/glyphs/rounds.py:39`, `ry = xh/2 + OVER`, so it runs
   −14..xh+14. Round 409's `IT_LC_SCALE` 1.015 (`outlines/build.py:198-200`,
   default at `:246`) scales about the origin. It lifts the italic's top by
   about 6.5 units, which brings the o's top level with the roman's
   (442 against 444). It leaves the bottom at half the roman's overshoot
   (−7 against −15).
2. **The italic c copies that band.** `aldine.py:2089-2090`: "Same outer band
   as the o (−OVER/2 .. xh+OVER/2)". Its bottom is −8 against −13.
3. **The italic e's floor is a fixed CENTERLINE, and the stroke under it has
   thinned.** `aldine.py:2326`: `E_FLOOR = 0.078` xh. The rationale at
   `:2297-2325` says the bottom arc's centerline stands at E_FLOOR and its
   underside, "40 units of half-width", lands on the o's overshoot. That was
   measured at round 135, 2026-09-16, where it gave an ink bottom of −0.015 xh.
   The underside is the centerline minus half the stroke width, and that
   width is `S × …` (`aldine.py:2595`). *Inferred, not rebuilt:* round 135
   ran when the face was drawn at stem 84. Round 266 (`pen.py:15-26`)
   re-anchored the 400 on stem 66.9, and the thinner bottom stroke lifted the
   underside off the line. The strongest evidence is that the same floor
   gives **+6 in the Italic (stem 66.9) and −7 in the Bold Italic (stem
   116)**, so the e's sitting follows the pen weight.
4. **The italic arches crest low.** `aldine.py:1103`: `HM_ARCH_TOP = 0.935` xh
   is the apex centerline for `h m n r u`, and a hairline tops it. The
   n/m ink tops out at 437 (half-max 427) against the roman's 447 (441). The
   roman arch carries `ARCH_OVER` (12 units,
   `outlines/glyphs/arches.py:106`). The docstring at `aldine.py:1391-1397`
   records that HM_ARCH_TOP is a weak lever: it moves the rendered apex by
   about a sixth of itself.
5. **Width.** The italic lowercase still sets at 0.89 of the roman's width
   after round 409's arm m (`IT_LC_SETW` 1.15, `build.py:247`). That is
   inside the reference range but under its median of 0.93
   (`docs/albo-italic-size-nib-2026-09-26.md` §3). At the same height, a
   narrower letter reads as a smaller one.

### Why the earlier check said the x-height was fine

`tools/wedge_serif/instruments/italic_size_nib.py:120` takes `xh = f.top("x")`,
which is the `x`'s top. On Albo that is a serif flare and not the body, and
it is exactly the letter that moves the other way: 457 italic against 451
roman. So round 409 was measured "xh 1.013" while the body text is 0.975.
Any future size check should use a frequency-weighted half-max band (§2b),
not a single glyph's bounding box.

## 4. Checked and found clean

- **Vertical metrics are identical in all four files.** hhea 1000/−300/0,
  OS/2 typo 1000/−300/0, usWin 1000/320, sxHeight 429, sCapHeight 674.
  head.yMin/yMax: Regular −298/971, Italic −297/983, Bold −317/1002,
  BoldItalic −307/1015. The italics' higher yMax is accents and `f`, and
  nothing reads it for placement.
- **The firmware does not place the italic line differently.**
  `sd-fonts.yaml:2295` overrides the metrics identically for all four styles
  (ascent 1023, descent −343) and sets no `synthetic:`, `scale:` or
  `baseline_shift_em` for Albo. `lib/GfxRenderer/GfxRenderer.cpp:752`
  (`yPos = y + getFontAscenderSize(...)`) gets its ascender from
  `:2820`, which is the REGULAR's for every style. Glyphs are then placed at
  `cursorY − top` (`:506`), using FreeType's own `bitmap_top`. So a word
  switched into italic sits on exactly the roman's baseline row.
- **Capital height and figure heights** are the same across styles (§2a),
  except the italic 6/8 at +30 units. Capitals are not part of this report.
- **The straight-stem feet** (`n m h i l`) sit ON the line in both styles.
  Their half-max bottom is −1, and the italic's −7 to −8 bounding box is the
  thin exit tip.
- **The weighted body band at pixel level** (§2c, last paragraph) and the ink
  centroid agree within 0.1 px, so the italic line is not shifted as a whole.
  The effect is per-letter.

## 5. Fix options (not implemented)

**A. Put the full overshoot back on the italic `o c e`.** *(Recommended
first. This is the "higher" half.)*
- The o and c band goes to −OVER at the bottom, at `aldine.py:1897-1899` and
  `:2090`. Keep the top as it is, since `IT_LC_SCALE` already levels it.
- `E_FLOOR` becomes weight-aware: the target is the underside, and the floor
  is that target plus half the bottom stroke's width. Otherwise the 400 and
  the 700 keep disagreeing.
- Expected result: the italic weighted bottom goes from −1.0 to about −8,
  level with the roman. At 1x, the `o e c` rows under the baseline come back.
- Cost: three letters re-cut, none of them approved. This is vertical only,
  so the B2 spacing is untouched.
- Re-run `gates.sh`. The e-mouth gate matters most, because a lower e floor
  changes the aperture. `cmp_touch` probably does not move.

**B. Raise the italic's arch and bowl crests to the roman's body top.** *(The
"smaller" half, on height.)*
- `h m n r u` want about 12–15 units at the crest.
- HM_ARCH_TOP cannot deliver this on its own, because it transmits about
  1/6 (`aldine.py:1391-1397`). It means reworking the arch tail, or adding a
  vertical-only scale to the hm family, anchored at the baseline.
- Do NOT raise `IT_LC_SCALE` for this. It is uniform, so it widens and
  deepens everything and pushes the ascenders further above the roman's
  (they are already up to +12). It also re-cuts the approved g.
- Cost: five to seven letters re-cut. The joins at the stem top must be
  re-checked for slits (the comment at `aldine.py:1430-1432`). Then run the
  hairs and bumps gates.
- Expected result: the weighted height ratio goes from 0.975 to about 0.99.

**C. More set width** (`ALBO_IT_LC_SETW` 1.15 → about 1.20, arm n of
`docs/albo-italic-size-nib-2026-09-26.md`).
- Width 0.89 → about 0.92, the reference median.
- Cost, measured there: +6 touching descender pairs needing kerns, the iota
  contour change, a re-approval of the g, and an italic bench pass, because
  the pair whites grow.
- This is the most expensive option and answers "smaller" without answering
  "higher". Take it only if A+B still read small.

The shallow italic g (−197) contributes to the "higher" impression. It is an
approved letter, so any change to its descender is a new ruling and belongs
to none of the options above.

## Appendix: how to re-measure

- **Outline table:** fontTools `BoundsPen` over the cmap glyph, per letter.
- **Half-max band:** FreeType `set_char_size(1000*64, …, 72, 72)`,
  `FT_LOAD_RENDER | FT_LOAD_NO_HINTING`. Row profile = coverage summed per
  row. Take the plateau as the median of rows between 30% and 60% of the
  glyph's height. Top and bottom are the first and last rows at 50% or more
  of that plateau, with row centers at `bitmap_top − r − 0.5`.
- **Frequency weights:** e 12.7, a 8.2, o 7.5, i 7.0, n 6.7, s 6.3, r 6.0,
  u 2.8, c 2.8, m 2.4, w 2.4, v 1.0, x 0.15, z 0.07.
- **Pixel rows:** `legib.quantize` on each glyph's 8-bit bitmap. A lit row is
  any level of 1 or more. Row r spans `bitmap_top − r − 1 .. bitmap_top − r`
  px above the baseline.
- **These instruments belong in `tools/wedge_serif/instruments/`**, per this
  repo's rule. They were not put there because another agent was editing that
  tree while this was written.
