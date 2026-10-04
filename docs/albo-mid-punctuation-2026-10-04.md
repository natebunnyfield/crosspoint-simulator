# Albo's mid punctuation: where it sits, and three options to raise it (2026-10-04)

Owner todo, verbatim: *"raise middot and other mid punctuation to be optically vertically
centered"*.

- **Surveyed:** commit `c1aa749` (round 480's letters). The fonts measured are the round-480
  build, and a clean build of that commit with this doc's dials at their defaults is identical
  to them by outline: 530 of 530 glyphs, advances included, in all four cuts.
- **Status:** OPTIONS BUILT, NOTHING SHIPPED. The dials are in the builders with defaults that
  reproduce round 480 byte for byte. Three arms are labeled **Q1, Q2, Q3**. Cuts are R I B Z
  (Regular, Italic, Bold, Bold Italic).
- **Confidence key:** *measured* means read off the built fonts by a script named here and
  re-runnable. *Inferred* means a judgment drawn from measurements. *Unconfirmed* means it
  depends on the owner's eye or the device's glass.

---

## 1. The short answer

Albo's mid punctuation is not uniformly low. It depends on what "centered" is measured against.

- **Against the x-height** (the lowercase body), the middle dot, the hyphen, the dashes and the
  guillemets already sit on the six references' median, or a little above it. The **bullet**
  and the **mathematical signs** sit low: the bullet by about 0.25 x-height, the minus, times and
  divide by about 0.11. The plus and equals sit 0.05 x-height above the other signs, so the math
  signs do not share one axis, where five of the six references do. *(measured)*
- **Against the cap height**, every one of them is low. The middle dot is at 0.445 of the cap
  where the references' median is 0.500, and the dashes are at 0.339 against 0.358. The reason is
  that Albo's capitals stand 1.54–1.57 x-heights tall, where the references' stand 1.37–1.51.
  *(measured)*
- **The references cannot say which frame to use.** Across 21 reference cuts, an x-anchored
  model and a cap-anchored model fit about equally well, and a free fit explains 2–4% of the
  spread. Their cap/x-height ratios span too little to separate the two. *(measured; a negative
  result)*
- **The X3's pixel grid constrains the choice.** The reader draws Albo unhinted at 2-bit levels,
  and the 400s' dashes and minus are under a pixel tall at 8–12 pt. A whole-unit raise can
  therefore turn a dark bar into two pale rows:
  - the cap-frame dash raise (+13) makes the 10 pt hyphen 77–100% faint;
  - the cap-frame math raise (+72) makes the 10 pt minus 100% faint and fills in the =.

  The arms take their shifts from the windows where the grid stays clean. *(measured)*

So the options are a ladder of how far to raise. Every rung sits inside the references' range in
at least one of the two frames, and every bar measures solid on the X3's own raster (headless;
how it looks on the glass is unconfirmed). Q3's dashes sit 0.006 x-height over Albertus, the
highest, and inside the cap-height range.

| arm | middle dot | bullet | hyphen and dashes | math signs (one axis) | guillemets |
|---|---|---|---|---|---|
| today | 301 (box) / 310 (mass) | 214 | 229 | 214 (+ and =: 236) | 214 |
| **Q1** the references against the x-height | unchanged | **328** | unchanged | **266** | unchanged |
| **Q2** the references against the capitals | **325 / 334** | **344** | unchanged (+13 is pale on the grid) | **266** (+72 is pale on the grid) | unchanged |
| **Q3** the top of the references' range | **338 / 347** (its box on the cap middle) | **344** | **254** (Albertus's height; the grid's clean window) | **266** | unchanged |

Units are the Regular's: the ink center in font units, 1000 to the em, x-height 430, cap 676.
Every cut moves by the same amounts.

---

## 2. What was measured, and how

`tools/wedge_serif/instruments/mid_punct.py` reads every glyph's ink box off the **outline**
(FreeType, unscaled, unhinted), in font units. A TrueType and a CFF reference therefore answer
the same question. The italics are measured as shipped: a shear about the baseline moves nothing
vertically.

- **center** is the midpoint of the ink box. The area centroid is printed where it differs by
  more than 3 units: the wedge middle dot (box 301, mass 310), the bold guillemets, and the
  composite signs ± ≠ ≤ ≥, whose parts are unequal.
- **x-height** is the median of ten estimates: the tops of z u ı n m, and yMax + yMin of o e c
  s a. A round letter's overshoot is taken as symmetric. No single letter is safe:
  - Palatino's and Albo's head serifs rise above the body (x 965 on a 936 Palatino, x 451 on a
    429 Albo);
  - Albo Italic's round letters dip 16 and rise 7;
  - an arch overshoots.

  The diagonals and the r are left out because in a wedge face their serifs rise. With them in,
  the Bold Italic read 448 on a lowercase drawn at 435. The ten read every Albo cut at its drawn
  x-height: R 430, I 435, B 430, Z 438. Against the declared OS/2 value they agree within 3 units
  for Georgia roman and bold, Berkeley and Times New Roman, and differ by up to 30 where the
  declaration is a serif top. *(measured; the estimator is a choice, and ±2% of x-height moves a
  ratio by about ±0.01)*
- **cap** is the H's top. **fig** is the 0's body. Albo's and Georgia's figures are old-style;
  the others are lining.
- **The references**, as the owner named them:
  - Georgia, Charter, Palatino and Times (Linotype's, `Times.ttc`) from `/System/Library/Fonts`;
  - `~/Downloads/Albertus Medium Regular.ttf`, roman only (no italic or bold exists here);
  - ITC Berkeley Oldstyle, Medium, Medium Italic, Bold and Bold Italic.

  Each is measured in the cut that answers Albo's. Times New Roman is measured and printed but
  kept out of the medians, so that one design does not vote twice.

### 2a. Today's position of every mid mark (Albo, round 480)

| glyph | builder | how it is placed | center, units: R / I / B / Z |
|---|---|---|---|
| U+00B7 middle dot | `symbols.py:274` `g_middot` | the Trajan wedge's vertex centroid at `CAP × MIDDOT_Y` (0.46) | box 301 / 301 / 294 / 294; mass 310 everywhere |
| U+2022 bullet, U+2219 bullet operator | `symbols.py:285`, `:287` | a dot on `MID` = `XH × 0.5` | 214 |
| U+002D, U+2010, U+2011, U+00AD, U+2012, U+2013, U+2014, U+2015 | `marks.py:919` `dash()` (callers `:929–933`, `:1172–1183`) | a bar at `CAP × 0.34` (the roman's rises 16.6 units to the right, round 251) | 229 (the Bold hyphen 228) |
| U+2212 minus, × ÷ ± ≈ < > ≤ ≥ ~ ∞ | `symbols.py:677–741` | about `MID` | minus 214; × 210 (box; its centroid is on MID) |
| + = (and ≠'s bars) | `marks.py:987`, `:991` | at `XH × 0.55` | 236 |
| ¬ | `symbols.py:1007` | bar at `MID + 0.16 XH` | 236 |
| « » ‹ › | `symbols.py:290` | apex on `MID` | 214 |
| → ← ↔ ⇒ (not punctuation; measured for the record) | `symbols.py` arrows | on `MID` | 214 |

### 2b. Albo beside the references: center over the x-height

Albo's value, then the references' median [range] and count, per cut.

| center / x-height | R Albo | R refs | I Albo | I refs | B Albo | B refs | Z Albo | Z refs |
|---|---|---|---|---|---|---|---|---|
| middle dot U+00B7 | 0.700 | 0.707 [0.566-0.762] n6 | 0.692 | 0.691 [0.571-0.722] n5 | 0.685 | 0.683 [0.552-0.762] n5 | 0.672 | 0.691 [0.555-0.738] n5 |
| bullet U+2022 | 0.499 | 0.735 [0.606-0.871] n6 | 0.493 | 0.767 [0.611-0.842] n5 | 0.499 | 0.756 [0.615-0.871] n5 | 0.490 | 0.764 [0.618-0.844] n5 |
| hyphen U+002D | 0.533 | 0.527 [0.494-0.580] n6 | 0.526 | 0.517 [0.497-0.555] n5 | 0.531 | 0.513 [0.491-0.550] n5 | 0.523 | 0.506 [0.496-0.553] n5 |
| en dash U+2013 | 0.533 | 0.525 [0.494-0.585] n6 | 0.526 | 0.508 [0.498-0.571] n5 | 0.533 | 0.517 [0.484-0.580] n5 | 0.523 | 0.501 [0.496-0.582] n5 |
| em dash U+2014 | 0.533 | 0.525 [0.494-0.585] n6 | 0.526 | 0.508 [0.498-0.571] n5 | 0.533 | 0.516 [0.484-0.580] n5 | 0.523 | 0.501 [0.496-0.582] n5 |
| minus U+2212 | 0.499 | 0.591 [0.547-0.699] n6 | 0.493 | 0.623 [0.570-0.676] n5 | 0.499 | 0.607 [0.561-0.700] n5 | 0.490 | 0.614 [0.574-0.678] n5 |
| plus U+002B | 0.549 | 0.591 [0.547-0.699] n6 | 0.543 | 0.620 [0.570-0.676] n5 | 0.549 | 0.607 [0.559-0.699] n5 | 0.539 | 0.613 [0.574-0.677] n5 |
| equal U+003D | 0.549 | 0.560 [0.542-0.699] n6 | 0.543 | 0.581 [0.512-0.676] n5 | 0.549 | 0.608 [0.560-0.699] n5 | 0.539 | 0.583 [0.548-0.677] n5 |
| multiply U+00D7 | 0.488 | 0.591 [0.554-0.700] n6 | 0.483 | 0.623 [0.570-0.677] n5 | 0.480 | 0.607 [0.560-0.700] n5 | 0.471 | 0.613 [0.575-0.678] n5 |
| divide U+00F7 | 0.498 | 0.590 [0.548-0.699] n6 | 0.492 | 0.622 [0.570-0.676] n5 | 0.498 | 0.607 [0.560-0.700] n5 | 0.489 | 0.614 [0.574-0.678] n5 |
| guillemet U+00AB | 0.499 | 0.499 [0.495-0.549] n6 | 0.493 | 0.502 [0.483-0.539] n5 | 0.499 | 0.499 [0.489-0.551] n5 | 0.490 | 0.509 [0.484-0.554] n5 |

### 2c. The same, over the cap height

| center / cap height | R Albo | R refs | I Albo | I refs | B Albo | B refs | Z Albo | Z refs |
|---|---|---|---|---|---|---|---|---|
| middle dot U+00B7 | 0.445 | 0.500 [0.395-0.513] n6 | 0.446 | 0.457 [0.395-0.502] n5 | 0.436 | 0.490 [0.385-0.513] n5 | 0.436 | 0.495 [0.385-0.506] n5 |
| bullet U+2022 | 0.317 | 0.498 [0.422-0.586] n6 | 0.318 | 0.508 [0.422-0.586] n5 | 0.317 | 0.553 [0.429-0.586] n5 | 0.318 | 0.553 [0.429-0.586] n5 |
| hyphen U+002D | 0.339 | 0.359 [0.341-0.402] n6 | 0.339 | 0.358 [0.342-0.383] n5 | 0.338 | 0.359 [0.339-0.384] n5 | 0.339 | 0.359 [0.339-0.384] n5 |
| en dash U+2013 | 0.339 | 0.357 [0.341-0.406] n6 | 0.339 | 0.358 [0.336-0.395] n5 | 0.339 | 0.358 [0.333-0.405] n5 | 0.339 | 0.359 [0.334-0.404] n5 |
| em dash U+2014 | 0.339 | 0.357 [0.341-0.406] n6 | 0.339 | 0.358 [0.336-0.395] n5 | 0.339 | 0.358 [0.333-0.405] n5 | 0.339 | 0.359 [0.334-0.404] n5 |
| minus U+2212 | 0.317 | 0.410 [0.380-0.470] n6 | 0.318 | 0.424 [0.384-0.470] n5 | 0.317 | 0.426 [0.386-0.471] n5 | 0.318 | 0.430 [0.385-0.471] n5 |
| plus U+002B | 0.349 | 0.406 [0.380-0.470] n6 | 0.350 | 0.419 [0.384-0.470] n5 | 0.349 | 0.425 [0.385-0.470] n5 | 0.350 | 0.425 [0.385-0.470] n5 |
| equal U+003D | 0.349 | 0.388 [0.365-0.470] n6 | 0.350 | 0.394 [0.346-0.470] n5 | 0.349 | 0.421 [0.386-0.470] n5 | 0.350 | 0.405 [0.375-0.470] n5 |
| multiply U+00D7 | 0.311 | 0.409 [0.382-0.471] n6 | 0.311 | 0.425 [0.385-0.471] n5 | 0.305 | 0.430 [0.386-0.471] n5 | 0.306 | 0.430 [0.385-0.471] n5 |
| divide U+00F7 | 0.317 | 0.409 [0.380-0.470] n6 | 0.317 | 0.424 [0.385-0.470] n5 | 0.317 | 0.425 [0.386-0.471] n5 | 0.317 | 0.425 [0.385-0.471] n5 |
| guillemet U+00AB | 0.317 | 0.351 [0.331-0.381] n6 | 0.318 | 0.337 [0.334-0.372] n5 | 0.317 | 0.352 [0.336-0.385] n5 | 0.318 | 0.358 [0.336-0.384] n5 |

### 2d. What the references do, mark by mark (the conventions)

These are Regular values. *(measured)*

- **The middle dot sits on the figures' middle.** For lining figures that is the cap middle.
  - Charter, Times and Albertus are at exactly 1.000 of their figures' middle (0.500 cap) and
    Berkeley at 1.022.
  - Georgia, whose figures are old-style like Albo's, puts it on *those* figures' middle (1.044,
    0.566 x-height).
  - Palatino sits lower, at 0.898.
  - Over the x-height they spread 0.566–0.762, with a median of 0.707. Albo's 0.700 sits on that
    median, but at 0.445 of the cap it sits under four of the six (Charter, Times, Albertus,
    Berkeley) against the capitals; only Georgia and Palatino are lower.
- **The bullet** is larger than the middle dot in every reference and sits higher: 0.606–0.871
  x-height, median 0.735, about the cap middle (0.498). Albo's is centered on the x-height's
  middle, 0.499. It is also about half the references' diameter (§10).
- **The hyphen and the dashes** are where the references disagree most:
  - Times and Charter put them on the x-height's exact middle (0.494–0.496);
  - Berkeley at 0.513–0.517;
  - Palatino and Georgia at 0.534–0.566;
  - Albertus, Albo's model face, highest at 0.580–0.585.

  Albo's 0.533 is mid-pack, with a lift of 14 units against the median's 12.
- **The mathematical signs share one axis**, the minus's, in five of the six:
  - Georgia (0.566 x-height), Charter (0.615), Times (0.553), Albertus (0.547) and Berkeley
    (0.699) draw + − = × ÷ there;
  - Palatino's = alone sits 0.04 em under its minus.

  That axis sits 0.05–0.20 x-height above the x-height's middle, Georgia's old-style figures
  included. Albo's minus, times and divide sit on the middle itself; its + and = sit 22 units
  higher.
- **The guillemets sit on the x-height's exact middle** in Charter, Palatino, Times and Berkeley
  (0.495–0.499), and higher only in Georgia and Albertus. Albo's sit on the middle (0.499). They
  are fine and none of the arms moves them.

---

## 3. The frame question, and why the references cannot answer it

A mark the references center at a fixed fraction of their x-height lands low against Albo's
capitals, and vice versa. Albo's cap/x-height is R 1.572, I 1.552, B 1.572, Z 1.541, outside
every reference's 1.366–1.511.

**The negative result.** Each reference's mark center over its x-height was regressed on its
cap/x-height ratio. Over 21 reference cuts:

- the slope is noise (R² 0.02 for the middle dot, 0.04 for the bullet, 0.02 for the dashes and
  the math signs);
- an x-anchored and a cap-anchored model leave nearly the same squared error. Only the
  guillemets (0.0106 against 0.0139) and the = (0.057 against 0.065) lean toward x-anchoring.

The references vary between designs more than their proportions vary, so no measurement here can
say which frame to center Albo in. The arms span both frames instead of pretending to know.
*(measured: an inline regression in this session, not kept as a script, which is why the numbers
are recorded here)*

**What the owner's books use them for** (corpus contexts, his 41 epubs, counted 2026-10-04):

- The middle dot (5,129 uses) is a spaced separator:
  - between lowercase words (2,052);
  - between a figure and a capital (1,586, numbered headings such as "1 · Wrap the vendor");
  - between a lowercase word and a capital (629).
- The hyphen (14,692) joins lowercase words (10,900) and figures (2,052, dates).
- The em dash (14,038) stands between lowercase words (9,721).
- The en dash (615) stands mostly between figures (334, "3–7"), and Albo's figures are old-style.
- The + (1,257) and = (1,663) stand between lowercase words in the Spanish grammar books (958 and
  1,189).
- The bullet appears 3 times.

So the lowercase frame governs most of what he reads. The middle dot's figure-and-capital
headings are the one heavy use where the capitals frame it. *(measured)*

---

## 4. The X3's pixel grid decides which shifts are usable

The reader rasterizes Albo unhinted and cuts it to 2-bit levels (round 401). At 150 dpi one
pixel is 60, 48 and 40 units at 8, 10 and 12 pt. The 400s' dashes are about 40 units thick and
the minus about 35, so the bar is under a pixel tall. Where it lands on the grid decides whether it draws as
one dark row or as two pale ones. The reader's sizes are 8, 10, 12, 14, 16 and 18 pt (the
`sd-fonts.yaml` ramp; `docs/wedge-serif-exploration.md:3621`). From 14 pt up, and at the phone's
2x tier at every size, every bar below draws solid at every shift.

**The instruments.**

- `instruments/parts_check.py` with `FAINT=1` reports the share of a stroke's ridge that the
  reader draws at level 1 or lighter. It is flagged over 25.
- `instruments/mid_punct_grid.py`, new, gives the same number for any shift without building a
  font: FreeType's transform moves the outline before it is rasterized.
  - It reproduces `parts_check` exactly at shift 0. On the built arms it agrees except in a few
    cells sitting on a level threshold, where its 1/64-pixel rounding moves coverage by at most
    4/255.
  - A one-unit export rounding does the same between two builds, so shifts were taken from the
    middles of clean windows, never from an edge.
- For the "=", the scanner also asks whether its two bars are *seen*: whether the middle columns'
  darkest-per-row profile has a row a level lighter than a bar on each side.

**The windows** (the 400s; the bolds' 85-unit bars draw solid at every shift):

| class | shift | 8 / 10 / 12 pt, faint % (R) | (I) | verdict |
|---|---|---|---|---|
| dashes | 0 (today) | hyphen 77 / 16 / 0, em 56 / 15 / 0 | 16 / 10 / 0, 8 / 1 / 0 | today |
| dashes | **+2 to +21** | **72–100 at 8 pt** (100 from +2 to +17); 27–100 at 10 pt | 100 at 8 pt; 100 at 10 pt for +7 to +15 | **the faint valley**: it includes the cap-frame median, +13 |
| dashes | **+22 to +30** | +22 is about today's (58 / 18 / 0); from +23 better than today, e.g. +25: hyphen 23 / 2 / 0, em 31 / 1 / 0 | today's from +22 to +24, better from +25 (0 / 10 / 0, 0 / 1 / 0) | **the good window** |
| math (one axis) | **+42 to +57** | minus, plus, divide 0–1 at each | 0–3 | clean bars |
| math (one axis) | +43 to +56 | the = is lost only at 8 pt | lost only at 8 pt | **the = window** (+51 is mid-window) |
| math (one axis) | +63 to +80 | the minus is 100% faint at 12 pt (+63 to +68), at 10 pt (+67 to +80) and at 8 pt (+73 to +80) | much the same, from +64 | **includes the cap-frame median, +72** |

**The first Q2 and Q3 used the cap-frame values (dashes +13, math +72) and were rebuilt.**
Measured on those builds:

- the 10 pt hyphen was 77% faint in the Regular and 100% in the Italic;
- the 10 pt minus was 100% faint in both;
- the plus was 30–66% faint at 10 pt;
- the = was not seen as two bars at 10 pt.

The arms that remain take the dash and math shifts from the clean windows. *(measured)*

---

## 5. The dials (`outlines/glyphs/marks.py:856–895`, `symbols.py:1114–1140`)

| variable | default | what it does |
|---|---|---|
| `ALBO_MID_DY_DOT` | 0 | raises the middle dot, in units |
| `ALBO_MID_DY_BULLET` | 0 | raises the bullet and the bullet operator |
| `ALBO_MID_DY_DASH` | 0 | raises all eight dashes: hyphen-minus, hyphen, non-breaking and soft hyphen, figure dash, en and em dash, horizontal bar |
| `ALBO_MID_DY_MATH` | 0 | raises − + = × ÷ ± ≠ ≈ < > ≤ ≥ ~ ¬ ∞ |
| `ALBO_MID_DY_GUIL` | 0 | raises « » ‹ › (built for completeness; no arm moves them) |
| `ALBO_MID_DY_<CLASS>_<R\|I\|B\|Z>` | unset | the same, in one cut only; beats the all-cuts value (checked in all four cuts) |
| `ALBO_MID_MATH_ONE_AXIS` | 0 | 1 puts + and = (and so ≠'s bars) on the axis the other math signs are drawn about, `MID`. Today they stand 0.05 x-height (21.45 units) above it |

- **How a class moves.** At the foot of `symbols.py`, a class whose shift is non-zero is
  re-registered as its own drawing translated up, whole. This happens before `build.draw` adds the
  ink spread and the italic shear, so the shape is unchanged.
- **Composites stay consistent.** ≠ composes from `marks.g_equal`, the function rather than the
  registry entry, so it builds from the unmoved = and moves once, with its class.
- **Defaults reproduce round 480.** Nothing is re-registered at 0, and + and = keep `XH × 0.55`
  unless the switch is on.

**Default identity.** A bare build of all four cuts, in a clean worktree off `c1aa749` holding only
these two files, compares IDENTICAL to round 480 with `cmp_outlines.py --advances`: 0 of 530
glyphs differ in every cut. This was re-checked on the final files. *(measured)*

**Rigidity.** Every moved glyph is today's outline translated, to within 1 unit by Hausdorff
distance. Its advance and sidebearings are unchanged, and in the italics the fit re-centers the
sheared ink, so the horizontal offset is 0 there too. Two details sit under that 1 unit:

- the export rounds half-units to even, so an odd shift moves some points one unit further;
- the 400s' hand-cut re-facets the multiply's crossing at under a unit.

The exceptions are + = ≠, which differ by 22 units by design: one axis brings them down first.
*(measured)*

---

## 6. The options

Each arm is one value per class for all four cuts. The per-cut targets differ by at most 6
units, because the italics' x-heights are 435 and 438 against 430. That is 0.12 px at 10 pt on
the X3, and every cut draws these marks at the same heights today.

### Q1 — the references against the x-height

`ALBO_MID_DY_BULLET=113 ALBO_MID_MATH_ONE_AXIS=1 ALBO_MID_DY_MATH=51`

The bullet and the math signs reach the references' pooled median over the x-height:

- the bullet at 0.756 x-height, which puts it 113 units up on average across the four cuts (111
  to 117);
- the math axis at 0.614, from shifts of 49 to 54, set at 51, mid-window on the grid.

The middle dot, the dashes and the guillemets are left: by this frame they already sit on the
median.

### Q2 — the references against the capitals, where the grid allows

`ALBO_MID_DY_DOT=24 ALBO_MID_DY_BULLET=129 ALBO_MID_MATH_ONE_AXIS=1 ALBO_MID_DY_MATH=51`

- The middle dot's mass reaches the pooled median over the cap, 0.495, which is +24 in every cut.
- The bullet reaches 0.508 of the cap, +128 to +129.
- The dashes stay. Their cap-frame +13 is in the faint valley (§4).
- The math stays at Q1's +51. The cap-frame +72 draws the 10 pt minus pale and fills in the =.

### Q3 — the top of the references' range

`ALBO_MID_DY_DOT=37 ALBO_MID_DY_DASH=25 ALBO_MID_DY_BULLET=129 ALBO_MID_MATH_ONE_AXIS=1 ALBO_MID_DY_MATH=51`

Q2, plus two changes:

- **The middle dot's box sits on the cap middle** (338 = 0.500 cap), as Charter, Times and
  Albertus place theirs. Its mass lands at 0.513 cap, Berkeley's, the references' highest.
- **The dashes rise to 254**, 0.591 x-height. Albertus, the highest reference, is at
  0.580–0.585, which is +20 to +23 here. The grid's clean window runs from +22 to +30. +25 sits
  inside both, robust to a unit either way.

**Resulting centers** (units, then over the x-height and over the cap; measured on the built
arms):

| R (xh 430, cap 676) | today | Q1 | Q2 | Q3 |
|---|---|---|---|---|
| middle dot, box / mass | 301 / 310 (0.721 xh, 0.459 cap) | same | 325 / 334 (0.777, 0.494) | 338 / 347 (0.807, 0.513) |
| bullet | 214 (0.499, 0.317) | 328 (0.762, 0.484) | 344 (0.799, 0.508) | 344 |
| hyphen, en and em dash | 229 (0.533, 0.339) | same | same | 254 (0.591, 0.376) |
| minus, +, =, ÷ | 214 / 236 (0.499 / 0.549) | 266 (0.617, 0.393) | 266 | 266 |
| multiply (box) | 210 | 261 | 261 | 261 |
| guillemet | 214 (0.499) | same | same | same |

The other cuts move by the same units. Over the x-height, the Italic reads Q3's dashes 0.584,
math 0.610, bullet 0.753 (Q1) or 0.790 (Q2/Q3). The Bold Italic reads 0.580, 0.606, 0.748 and
0.784.

**On the X3's grid** (`parts_check.py FAINT=1` on the built fonts, faint % at 8 / 10 / 12 pt):

| | R today | R Q1, Q2 | R Q3 | I today | I Q1, Q2 | I Q3 |
|---|---|---|---|---|---|---|
| hyphen | 77 / 16 / 0 | 77 / 16 / 0 | **23 / 2 / 0** | 16 / 10 / 0 | 16 / 10 / 0 | 16 / 10 / 0 |
| en dash | 53 / 15 / 0 | same | **34 / 4 / 0** | 8 / 4 / 0 | same | **0 / 4 / 0** |
| em dash | 56 / 15 / 0 | same | **31 / 1 / 0** | 8 / 1 / 0 | same | **0 / 1 / 0** |
| minus, divide | 0 / 0 / 1 | 0 / 0 / 1 | 0 / 0 / 1 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| plus | 34 / 30 / 1 | **0 / 0 / 0** | **0 / 0 / 0** | 81 / 66 / 0 | **2 / 0 / 0** | **2 / 0 / 0** |
| equal, faint % | 0 / 1 / 34 | 100 / 1 / 1 | 100 / 1 / 1 | 3 / 2 / 26 | 55 / 2 / 0 | 55 / 2 / 0 |
| equal, two bars lost at | 8, 10, 12 pt | 8 pt only | 8 pt only | 8, 10 pt | 8 pt only | 8 pt only |

Every arm's math makes the + solid and the = readable as two bars at 10 and 12 pt. Today's
Regular = draws as a block at 8, 10 and 12 pt (the lead picture's "4 ▬ 12"). The trade is the
8 pt =, which is a block in every arm and today alike: today's block is dark, the arms' is pale.
The bolds draw every bar solid at every size, today and in all three arms. *(measured; how it
reads on the glass is unconfirmed)*

### Gates and clearance, per arm (against round 480)

| | Q1 | Q2 | Q3 |
|---|---|---|---|
| glyphs moved (each cut) | 17: • ∙ and the 15 math signs | 18: + the middle dot | 26: + the 8 dashes |
| `poor_gates.sh` | **no delta** | **no delta** | **no delta** |
| hairs (letters and full sweep) | no new rows | no new rows | no new rows |
| touch (`cmp_touch`, includes `-`) | 0 / 0 → 0 / 0 | 0 / 0 → 0 / 0 | 0 / 0 → 0 / 0 |
| glitch on the moved glyphs | 0 with findings | 0 | 0 |
| counter dents (bolds) | 1 → 1 | 1 → 1 | 1 → 1 |
| contours / approved / e mouth | unchanged / unchanged / ok | same | same |
| `clearance.py` | 0 kerns | 0 | 0 |
| `clearance.py --composites` | 0 | 0 | 0 |
| `mark_crowd.py --clear` (italics, the recipe's default) | 0 | 0 | 0 |

The clearance steps wrote to scratch copies of the table (`ALBO_SPACING_TABLES` set to an
absolute path). The repo's `spacing_b2.json` is byte-identical to HEAD.

`mark_crowd.py --clear --cuts Regular,Bold --dry` reports 1,632 pairs, identical row for row in
round 480 and in every arm. Those rows are pre-existing: the 2-D rule is applied to the italics
only, by design (round 453). *(measured)*

---

## 7. The proof pictures

All are PNG at native pixels in the session scratchpad's `midpunct/` directory, published by the
main session. Text goes through the reader's own rasterization
(`instruments/tittle_proof.text_img`: unhinted, 2-bit, HarfBuzz with the kerns). Each image was
made by `instruments/mid_punct_proof.py`, and every row is labeled today, Q1, Q2 or Q3.

| file | caption |
|---|---|
| `lead.png` | **The one to rule from.** "1 · Wrap — well-known 3–7 · 3 × 4 = 12 − 2 • list", Regular, 10 pt on the X3 (150 dpi), **4x NEAREST**; today on top |
| `lead44.png` | the same line at 44 pt, 1x |
| `words_R.png` `words_I.png` `words_B.png` `words_Z.png` | the six test lines ("co·operate · the ·· list", "well-known self-made", "1990–2000 pages 3–7", "word—word", "• first item", "3 × 4 = 12 − 2 ÷ 1 + 0") at 44 pt, 1x; one block per line, today first; R I B Z = Regular, Italic, Bold, Bold Italic |
| `read_R.png` `read_I.png` `read_B.png` `read_Z.png` | the same at 10 pt on the X3, **4x NEAREST** |
| `marks_R.png` `marks_I.png` `marks_B.png` `marks_Z.png` | each mark alone (· • - – — − + = × ÷, and « unchanged for reference) at a 300 px x-height, 8-bit unhinted, against the baseline, the dotted x-height middle, the x-line and the cap line, with a tick at its ink center and the center in units under each cell; today, Q1, Q2, Q3 side by side |

---

## 8. Negative results (recorded so they are not re-proposed)

- **"Centered on the x-height's middle" was not built.** It was the first option suggested for
  this ask. Albo's mid marks are already at or above that middle, so the rule would lower the
  middle dot by 86 units and the dashes by 14, against an ask to raise. No reference puts a
  middle dot there; the lowest is Georgia at 0.552 x-height. *(measured)*
- **"The math signs on the figures' middle" was not built.** Albo's figures are old-style: their
  body is 445 tall and its middle 223. The rule would place the math axis at 0.517 x-height, below
  every reference's (0.547–0.700). That includes Georgia, the one old-style reference, whose
  taller figures put its middle at 0.543 x-height and its math at 0.566. *(measured)*
- **The cap-frame dashes (+13) and math (+72)** were built as the first Q2 and Q3, measured pale
  on the X3 grid (§4), and replaced. *(measured)*
- **The frame regression** cannot separate x-anchored from cap-anchored placement in these
  references (§3). *(measured)*
- **A five-letter x-height** (o z u x v) read Albo Bold Italic at 448 on a lowercase drawn at
  435, because Albo's diagonals carry rising serifs. It was replaced by the ten-letter median.
  *(measured)*

## 9. Checked and found fine

- **The guillemets** sit on the references' x-height median (0.499 against 0.499 in R). No arm
  moves them.
- **The middle dot never vanishes** at 8–14 pt for any shift from 0 to +45 (`mid_punct_grid.py
  --dot`). It keeps at least one dark pixel at 8 pt and at least two from 10 pt.
- **The bolds' bars** (85 units) draw solid at every shift and size scanned.
- **Arm hygiene:**
  - no advance or sidebearing moved;
  - the contour census is unchanged (1,056 glyphs);
  - the 2 approved glyphs are unchanged;
  - the touch, hairs and glitch gates are unchanged;
  - no clearance kern is needed;
  - `spacing_b2.json` is untouched.
- **∙ (U+2219) follows the bullet class.** In the references that draw it (Georgia, Charter,
  Albertus) it is the middle dot's shape at the middle dot's height. Today Albo's sits 95 units
  under its middle dot's mass; the bullet class's shift brings it within 18 (Q1), 10 (Q2) and 4
  (Q3) units of it.

## 10. Open findings, not acted on (each is a separate question for the owner)

- **The bullet is about half the references' size.** Albo's is 125 units across (0.29
  x-height). The references' bullets run 0.53–0.75 of their x-height. Raised, it reads more like
  a raised dot than a bullet in the 44 pt proof. *(inferred)*
- **The = bars' gap is under a pixel at 8 and 10 pt.** It is about 35 units, against a pixel of
  60 and 48. The 8 pt = draws as a block today and in every arm; only redrawing the gap would fix it.
- **Albo's dashes are thin.** They are 40 units (0.093 x-height) against the references'
  0.14–0.24. That is why their darkness depends on the grid at 8–10 pt. Thicker bars would
  likely draw solid at any height, as the bolds' 85-unit bars do at every shift. *(inferred)*
- **The arrows.** The rightwards arrow is the commonest symbol in his books, at 2,583 uses. The
  arrows sit on the x-height's middle (0.498). With the math raised, the arrow in "x → y" will
  sit about 50 units under the = in "x = y". Only Times New Roman among the references draws arrows, at 0.564 x-height on
  its own (lower) axis. An arrow class would be one more entry in `MID_CLASSES`.
- **The middle dot's existing dial.** `ALBO_MIDDOT_Y` (`symbols.py:236`, 0.46 of the cap) is the
  same lever in another unit. A ship could fold the chosen shift into it: +24 units is about
  +0.036. The new dial stacks on it and does not replace it.

## 11. Reproduce

The measurement:

```bash
cd tools/wedge_serif
VENV=<the measurement venv: numpy, freetype, uharfbuzz, scipy>
$VENV/bin/python instruments/mid_punct.py --summary R480_DIR                     # §2b, §2c
$VENV/bin/python instruments/mid_punct.py R480_DIR --json out.json              # every glyph and reference
$VENV/bin/python instruments/mid_punct_grid.py R480_DIR --dash 0:31:1 --math 30:81:1 --dot 0:46:1   # §4
FAINT=1 $VENV/bin/python instruments/parts_check.py "-–—−=+÷·" ARM/Albo-Regular.ttf ...            # §6 grid table
$VENV/bin/python instruments/mid_punct_proof.py OUT today=R480 Q1=Q1DIR Q2=Q2DIR Q3=Q3DIR          # §7
```

An arm, built as round 480 is built, with the dials added to every cut:

```bash
source build_env.sh
env "${ALBO_ROM_ENV[@]}" ALBO_MID_DY_DOT=37 ALBO_MID_DY_DASH=25 ALBO_MID_DY_BULLET=129 \
  ALBO_MID_MATH_ONE_AXIS=1 ALBO_MID_DY_MATH=51 PYTHON_GIL=0 python3 -m outlines.build OUT --style Regular
# ...and ALBO_ITA_ENV --style Italic, ALBO_BLD_ENV --style Bold, ALBO_BIT_ENV --style BoldItalic
bash instruments/poor_gates.sh R480_DIR OUT "Regular Italic Bold BoldItalic"
```
