# Albo's Aldine italic against Coelacanth Italic, glyph by glyph — 2026-09-17

Owner 2026-09-17: *"compare every alphanumeric of coelacanth italic with our
aldine italic and show me an informative table graphic of what could be
improved."*

All 62 alphanumerics, measured on both faces and ranked worst-first. The table
graphic is the deliverable; this file is the method, the numbers as text, and
the half a graphic cannot carry — **what turned out NOT to be a difference, and
what the instrument cannot see at all.**

Instrument: [`tools/wedge_serif/cmp_vs_coelacanth.py`](../tools/wedge_serif/cmp_vs_coelacanth.py).

```
ALBO_ITALIC=aldine FJORD_SLANT=13 FJORD_CONTRAST=0.80 FJORD_WIDTH=95 FJORD_CUT=0 \
PYTHON_GIL=0 python3 -m outlines.build <dir> --style Italic

PYTHON_GIL=0 python3 cmp_vs_coelacanth.py --albo <dir>/Albo-Italic.ttf \
    --png albo_vs_coelacanth.png --json t.json
```

Measured against Albo as built at commit `2554465` (*"albo: the g's joint — the
compound-path diagnosis"*), and Coelacanth Italic as registered in
`refs_registry.py`. 23 s for the pair.

---

## 1. What is compared, and what is deliberately not

Coelacanth is the yardstick because its x-height is **425/1000** against Albo's
429 — closer than any other reference — so the two set to a common x-height
without either being scaled past recognition, and because it is the face the g's
brush-stroke analysis was taken off (`docs/italic-g-strokes.md`).

It is **not a target to copy**. Albo is aimed at metal letterpress and is
deliberately its own proportions. Measured, raw, at a common x-height:

| | ink width, Albo / Coelacanth | stem | height above baseline |
|---|---|---|---|
| lowercase | 0.904 | 1.036 | 1.037 |
| uppercase | **0.856** | **1.085** | 0.969 |
| digits | 0.997 | **1.141** | 1.038 |

Albo is a **narrower, heavier** face than Coelacanth — most at the capitals (14%
narrower) and the digits (14% heavier stem). Every one of those is a design
decision, and a table of raw ratios would flag all 62 glyphs and say nothing.

**So every proportion figure in the table is a RESIDUAL against Albo's own
face-wide median for that glyph's class.** "Albo is narrow" disappears; "this
letter is 18% wide while the rest of its own alphabet is 14% narrow" survives.

And **every shape figure carries Coelacanth as its control.** The pen column is
not Albo's deviation from its own nib — it is that deviation *minus
Coelacanth's on the same letter*, because some letters cannot state a nib angle
on any face and an instrument with no control files that as an Albo fault. The
`z` is the proof: it reads 40° off Albo's nib and **46° off Coelacanth's**, so
its excess is −6 and the table correctly does not flag it.

### Scoring

Each fault is a robust z-score (its residual over 1.4826 × the MAD of that
metric across all 62 glyphs), weighted: pen 1.25, width 1.00, stem 1.00,
contrast 0.85, notch 0.90, height 0.75, depth 0.55, colour 0.40. The glyph's
score is **the worst term plus a third of the rest** — not a plain sum. A sum
ranks the glyph with six trivial complaints above the glyph with one real fault;
the first cut put Albo's `u` (11% narrow, one notch, 2% tall) two rows above its
`E`, whose arms are as heavy as its stem.

`< 2.2` reads as matching, `>= 4.0` as needing real work. **18 match, 28 are
middling, 16 need work.**

---

## 2. The eight that need work first

Confidence: **verified** means the number was checked against the rendered
letter by eye, at size, before it was written down.

1. **`E` — score 16.5, the worst in the alphabet, and not marginally.** Its
   strokes come out thinnest at **112°**, where the face's nib sits at 24°: the
   arms are as heavy as the stem, so the letter is thin where the pen is thick
   and thick where it is thin. Coelacanth's E is 38°/24°, a 14° miss; Albo's is
   74°. The stem also measures 14% heavy for its own alphabet. *Verified —
   rendered both E's at 150 px and Albo's three arms are visibly the weight of
   its stem while Coelacanth's are hairlines.*
2. **`d` — 9.2.** Thins at 158° against the face's 24°, 38° further off than
   Coelacanth. The bowl and the ascender disagree about which way the nib is
   held. Also 8% wide and 4% short. *Verified by the same measurement at two
   raster sizes (300 px and 420 px), which agree to 2°.*
3. **`8` — 8.0.** Tops **17% short** for a digit of its class: Albo's 6 reaches
   1.54 xh and its 8 only 1.30, where Coelacanth puts both at 1.50. Albo's two
   ascending figures disagree with each other. Hairline also too fat, 1.6:1
   against Coelacanth's 3.1:1. *Verified — the raw heights are in §5.*
4. **`7` — 6.3.** Effectively **monolinear**: 1.1:1 contrast where Coelacanth's
   is 2.6:1 and Albo's own alphabet averages 2.23:1. Its stem is also 23% light
   and it descends 0.14 xh deeper than its class. *Verified — rendered, the
   diagonal is one uniform weight end to end.*
5. **`S` — 6.3.** Thins at 50° against 24°, 20° further off than Coelacanth;
   stem 18% light; descends 0.09 xh deeper than its class. The spine is being
   drawn at the wrong angle, not merely too thin.
6. **`H` — 6.1.** Thins at **0°** — horizontally — against a 24° nib, 24°
   further off than Coelacanth. Both stems read the same weight where an italic
   at this nib should differentiate them. Stem 11% heavy, 8% wide.
7. **`X` — 5.3.** The **thinnest hairline in the face**: 6.1:1 contrast against
   Coelacanth's 3.0:1, from a hairline of **0.038 xh** where the rest of Albo's
   alphabet runs 0.047 (`m`) to 0.160 (`N`) — so the X's thin is 19% under the
   next thinnest letter and a quarter of the fattest. At a 13 pt reading size on
   e-ink this diagonal is the one most likely to break up. *Verified against the
   15th-percentile ridge thickness for all 62.*
8. **`9` — 5.3.** 12% tall for a digit of its class and 12% wide. Unlike the 8
   this is a plain proportion miss, with nothing wrong with the strokes.

Then, immediately behind them: **`p`** (17% wide, 9% short), **`i`** (hairline
too fat, 2.2:1 against 3.1:1), **`a` `c` `q` `g` `k`** (all 12–18° off the nib —
see §4), **`1`** (25% narrow, but read §6 first), **`j`**, **`I`**, **`Z`**
(stem 23% heavy), **`z`**, and **`5`** (the only glyph in the face carrying more
than one excess union notch).

## 3. The eighteen that match and need nothing

`D` `B` `n` `6` `m` `x` `v` `P` `r` `h` `f` `Y` `F` `M` `t` `3` `w` `K`

`D` carries the lowest score in the alphabet (0.4): within 2% on both width and
stem, exactly on the nib, no excess notches. Its one gap is a hairline 14%
fatter than Coelacanth's — which is not nothing, and is the reminder that
"matches" here means *no measured axis stands out*, not *identical*. The arch
letters `n` `m` `h` and the diagonal `v` `x`
`w` sit in this group, which is worth noting against
`docs/italic-vs-oblique.md`: the letters that were once the weakest evidence of
a true italic now measure clean against a real one.

---

## 4. The one finding that is a pattern rather than a glyph

**Albo's bowl-and-shoulder letters run their nib flatter than the rest of its own
alphabet.** Ten glyphs deviate by 12° or more:

```
a 18°   c 18°   d 38°   g 12°   k 14°   q 12°   E 74°   H 24°   I 12°   S 20°
```

Five of those — `a c d g q` — are the letters whose bowl is a closed curve
joined to a stem. On Coelacanth the same five sit within **8°** of its nib
(a 4, c 6, d 8, g 0, q 6); on Albo they are at 22, 24, 46, 12 and 18. The
three capitals (`E H I`) are a separate case: they are the letters whose ink is
mostly horizontal-and-vertical, and on all three Albo reads flatter than
Coelacanth by 12–74°.

This is the `cmp_g_strokes.py` principle applied to a whole alphabet: *a face
drawn on one pen has ONE signature for the whole letter.* Where a letter's
thinnest direction disagrees with the face's, its widths were declared rather
than written, and no amount of re-tuning a width table will make it read as
written.

---

## 5. NEGATIVE RESULTS — what I measured that is NOT a difference

Recorded because these are the candidates that will otherwise be re-proposed
forever, and because each cost a measurement.

* **The nib angle itself is IDENTICAL: 24° on both faces.** Pooled over every
  ridge sample in all 62 glyphs. Albo's pen is held at the right angle overall —
  this was the most obvious candidate for a face-level fault and it is not one.
  What varies is per-letter conformance to it (§4), not the face's own pen.
  *High confidence: pooled over 59 831 ridge samples on Albo at 420 px per
  x-height, profiled in 2° steps with a ±22° window.*
* **Whole-alphabet contrast is close: Albo 2.23:1, Coelacanth 2.45:1.** Albo is
  9% flatter overall. That is within the spread of the individual letters and is
  not worth a change; the contrast faults are *per glyph* (the 7 at 1.1, the X
  at 6.1), not systemic.
* **The union-notch bug class is NOT widespread.** The concave-notch failure
  that cost rounds on the g, the Q and the ear is present on exactly four
  glyphs as an excess over Coelacanth: `a` 1/0, `q` 1/0, `u` 1/0, `5` 3/1. Albo
  has **35 concave notches to Coelacanth's 60** over the whole alphabet, and
  Coelacanth's eight largest are the inner vertices of `V W M N w`, which are
  correct. Raw notch counts are not a verdict on either face.
* **`z` is not at fault for its diagonal.** 40° off Albo's nib, 46° off
  Coelacanth's. Its verdict is a stem 14% light, not a pen fault.
* **The descender depths are broadly right.** Once residualised inside a band
  taken off Coelacanth's own value (flat with flat, descender with descender),
  the median glyph is **0.014 xh** out and only the `7` exceeds 0.09 (0.138).
  Depth is the weakest-weighted term in the score for exactly that reason.
* **The profile-depth gate never fires.** `nib_angle` refuses to report an angle
  off a flat direction profile (max/min < 1.40). Albo's shallowest is the 7 at
  1.48 and Coelacanth's the F at 1.86, so the gate filters nothing in this pair.
  It is kept because a gate that never fires looks removable right up until it
  is the only thing between a flat letter and a confident 74° verdict.
* **The digit-height pattern is shared, not Albo's invention.** Both faces use
  ranging figures — `6` and `8` ascend, `3 4 5 7 9` descend, `0 1 2` sit near
  the x-height. Only the `8` (§2.3) is out of step, and it is out of step with
  **Albo's own 6**, not with Coelacanth's convention.

Raw digit heights above the baseline, in x-heights:

```
       0     1     2     3     4     5     6     7     8     9
Albo  1.09  1.02  1.14  1.12  1.05  1.08  1.54  1.02  1.30  1.11
Coel  0.98  0.96  1.09  1.08  1.01  1.07  1.50  1.02  1.50  0.95
```

---

## 6. What this instrument CANNOT measure — read before acting on a row

* **Some rows compare two different letterform DESIGNS, not a good and a bad
  draw of one.** Coelacanth's italic `1` is an I-shaped figure with full top and
  bottom serifs, 0.976 xh wide; Albo's is a flagged figure with no foot, 0.733.
  Coelacanth's italic `I` is **1.514 xh wide** against Albo's 1.055 — a swash-ish
  capital of a kind Albo does not have. The `1` and `I` rows are therefore a
  design difference dressed as a width fault, and the owner's call, not the
  instrument's.
* **Nothing about serifs.** Bracket shape, wedge angle, the taper the owner
  named on 2026-09-17, entry and exit strokes, ball versus sheared terminals —
  none of it is separable from the stroke it sits on at this resolution.
  `cmp_joints.py` sees a serif tip only as a sharp vertex.
* **Nothing about fine anatomy.** The g's two counters, the ear's reach, the
  neck's waist — `cmp_aldine_g.py` does those per letter and this does not.
* **Nothing about optical correction.** Overshoot on round letters is folded
  into the `top` figure and cannot be told from a letter that is simply tall.
* **Nothing about how the letters set as words.** No fitting, no kerning, no
  colour in a line — `proof_words.py` and `cmp_cap_space.py` are those
  instruments.
* **Resolution floor.** The raster is 420 px per x-height, so a feature under
  ~2 px — about **5 design units** at Albo's 429 — is invisible. The distance
  transform is chamfer (1, 1.414), an approximation to Euclidean, and thickness
  figures carry roughly 1% of that.
* **`J` on Albo, and `i` `r` on Coelacanth, have no pen reading at all.** Fewer
  than 40 of the 90 direction windows were measurable: their ink does not run in
  enough directions to locate a minimum. The table prints `–`, not a guess.

### One finding that is real but deliberately NOT in the graphic

**Albo is the more loosely fitted face.** Its ink is 10% narrower than
Coelacanth's, but its advances are only 3% narrower — so relative to the ink it
draws, Albo leaves more air. Per glyph, the largest divergences between the
advance residual and the ink residual:

```
tighter than its own norm:   i −34%   j −19%   E −19%   m −18%   l −16%
looser  than its own norm:   5 +46%   J +36%   S +26%   7 +23%   I +23%
```

This is **fitting, not drawing**, which is why it is not a column in a table the
owner asked to be about the glyphs, and why it should be confirmed with
`cmp_cap_space.py` / `cmp_touch.py` before anything is moved. *Medium
confidence: derived from `hmtx` advances against measured ink bounding boxes,
not from a spacing test.*

---

## 7. The full ranking

`wid` and `stem` are residuals against Albo's own class median, not ratios.
`contrast` is Albo / Coelacanth, stem over hairline (85th percentile of ridge
thickness over the 15th). `pen` is Albo's deviation from its own 24° nib minus
Coelacanth's from its own. `ntch` is the concave-vertex count, Albo/Coelacanth.

| ch | score | wid | stem | contrast | pen | ntch | what could be improved |
|---|---|---|---|---|---|---|---|
| `E` | 16.5 | +2% | +14% | 1.7 / 1.9 | +74° | 0/2 | thins at 112° where the face's nib is 24° — 74° further off than Coelacanth is here; stem 14% heavy for its own alphabet |
| `d` | 9.2 | +8% | +1% | 2.5 / 2.6 | +38° | 0/0 | thins at 158° where the face's nib is 24° — 38° further off than Coelacanth is here; 4% short above the baseline for its class; 8% wide for its own alphabet |
| `8` | 8.0 | -2% | -3% | 1.6 / 3.1 | +2° | 0/2 | 17% short above the baseline for its class; hairline too fat — 1.6:1 here, Coelacanth 3.1:1 |
| `7` | 6.3 | -12% | -23% | 1.1 / 2.6 | +0° | 0/0 | descends 0.14 xh deeper than its class; hairline too fat — 1.1:1 here, Coelacanth 2.6:1; stem 23% light for its own alphabet; 12% narrow for its own alphabet; 3% short above the baseline for its class |
| `S` | 6.3 | -4% | -18% | 2.3 / 3.0 | +20° | 0/0 | thins at 50° where the face's nib is 24° — 20° further off than Coelacanth is here; descends 0.09 xh deeper than its class; stem 18% light for its own alphabet; 2% tall above the baseline for its class |
| `H` | 6.1 | +8% | +11% | 1.6 / 1.9 | +24° | 0/4 | thins at 0° where the face's nib is 24° — 24° further off than Coelacanth is here; stem 11% heavy for its own alphabet; 8% wide for its own alphabet |
| `9` | 5.3 | +12% | -0% | 1.7 / 2.5 | +2° | 0/0 | 12% tall above the baseline for its class; 12% wide for its own alphabet |
| `X` | 5.3 | -3% | +1% | 6.1 / 3.0 | +0° | 0/4 | hairline too thin — 6.1:1 here, Coelacanth 3.0:1; descends 0.05 xh deeper than its class; 4% tall above the baseline for its class; sets 20% lighter than its class |
| `p` | 4.9 | +17% | -5% | 2.7 / 2.4 | +6° | 0/1 | 9% short above the baseline for its class; 17% wide for its own alphabet; thins at 14° where the face's nib is 24° — 6° further off than Coelacanth is here |
| `i` | 4.9 | +2% | -14% | 2.2 / 3.1 | -- | 0/0 | 9% short above the baseline for its class; hairline too fat — 2.2:1 here, Coelacanth 3.1:1; stem 14% light for its own alphabet |
| `a` | 4.9 | -1% | +14% | 2.9 / 2.8 | +18° | 1/0 | thins at 2° where the face's nib is 24° — 18° further off than Coelacanth is here; 1 concave notch where strokes union — no stroke width tunes these out; stem 14% heavy for its own alphabet |
| `c` | 4.7 | -7% | -6% | 2.4 / 2.5 | +18° | 0/0 | thins at 0° where the face's nib is 24° — 18° further off than Coelacanth is here; 7% narrow for its own alphabet |
| `1` | 4.7 | -25% | +7% | 2.8 / 2.5 | -12° | 0/0 | 25% narrow for its own alphabet; hairline too thin — 2.8:1 here, Coelacanth 2.5:1; descends 0.04 xh shallower than its class; 3% tall above the baseline for its class |
| `j` | 4.5 | +8% | -7% | 1.7 / 1.6 | -2° | 0/0 | 9% short above the baseline for its class; 8% wide for its own alphabet; descends 0.03 xh deeper than its class |
| `k` | 4.4 | +2% | +8% | 2.0 / 2.7 | +14° | 1/1 | thins at 8° where the face's nib is 24° — 14° further off than Coelacanth is here; descends 0.06 xh shallower than its class; hairline too fat — 2.0:1 here, Coelacanth 2.7:1 |
| `I` | 4.3 | -19% | +13% | 1.4 / 2.0 | +12° | 0/0 | thins at 4° where the face's nib is 24° — 12° further off than Coelacanth is here; 19% narrow for its own alphabet; stem 13% heavy for its own alphabet; hairline too fat — 1.4:1 here, Coelacanth 2.0:1 |
| `Z` | 3.9 | -10% | +23% | 2.0 / 1.7 | +4° | 0/1 | stem 23% heavy for its own alphabet; 4% short above the baseline for its class; hairline too thin — 2.0:1 here, Coelacanth 1.7:1; 10% narrow for its own alphabet; thins at 70° where the face's nib is 24° — 4° further off than Coelacanth is here; descends 0.03 xh shallower than its class |
| `z` | 3.9 | -1% | -14% | 2.5 / 2.0 | +2° | 0/1 | 5% short above the baseline for its class; stem 14% light for its own alphabet; descends 0.05 xh shallower than its class; sets 25% lighter than its class; hairline too thin — 2.5:1 here, Coelacanth 2.0:1 |
| `5` | 3.8 | -0% | +8% | 2.1 / 2.5 | -50° | 3/1 | 2 concave notches where strokes union — no stroke width tunes these out; descends 0.04 xh deeper than its class; sets 28% blacker than its class; 3% short above the baseline for its class |
| `q` | 3.8 | +12% | -3% | 2.6 / 2.4 | +12° | 1/0 | thins at 6° where the face's nib is 24° — 12° further off than Coelacanth is here; 12% wide for its own alphabet; 1 concave notch where strokes union — no stroke width tunes these out; descends 0.03 xh shallower than its class |
| `Q` | 3.6 | +20% | +3% | 2.5 / 2.2 | -18° | 0/2 | 20% wide for its own alphabet; descends 0.05 xh deeper than its class; hairline too thin — 2.5:1 here, Coelacanth 2.2:1; 3% short above the baseline for its class; sets 22% blacker than its class |
| `g` | 3.5 | +7% | +14% | 2.6 / 2.4 | +12° | 0/1 | thins at 36° where the face's nib is 24° — 12° further off than Coelacanth is here; stem 14% heavy for its own alphabet |
| `4` | 3.3 | -7% | +18% | 2.1 / 2.3 | +0° | 0/2 | descends 0.08 xh shallower than its class; stem 18% heavy for its own alphabet; 7% narrow for its own alphabet; hairline too thin — 2.1:1 here, Coelacanth 2.3:1 |
| `2` | 3.3 | +0% | -10% | 1.4 / 2.8 | +0° | 0/1 | descends 0.09 xh shallower than its class; hairline too fat — 1.4:1 here, Coelacanth 2.8:1; stem 10% light for its own alphabet |
| `0` | 3.3 | +6% | +0% | 1.6 / 2.3 | +0° | 0/0 | 7% tall above the baseline for its class |
| `G` | 3.3 | -0% | -11% | 2.2 / 2.7 | -28° | 0/0 | descends 0.09 xh deeper than its class; 4% tall above the baseline for its class; stem 11% light for its own alphabet |
| `N` | 3.3 | +10% | -3% | 1.4 / 2.6 | +8° | 0/2 | hairline too fat — 1.4:1 here, Coelacanth 2.6:1; thins at 0° where the face's nib is 24° — 8° further off than Coelacanth is here; 10% wide for its own alphabet; sets 23% blacker than its class |
| `o` | 3.2 | -2% | +18% | 3.9 / 2.1 | -8° | 0/0 | hairline too thin — 3.9:1 here, Coelacanth 2.1:1; stem 18% heavy for its own alphabet |
| `y` | 3.0 | -1% | +6% | 3.0 / 1.9 | -4° | 1/1 | hairline too thin — 3.0:1 here, Coelacanth 1.9:1; descends 0.05 xh deeper than its class; 2% tall above the baseline for its class |
| `U` | 2.9 | +12% | +6% | 1.8 / 2.0 | -4° | 0/0 | descends 0.08 xh deeper than its class; 12% wide for its own alphabet |
| `A` | 2.9 | +16% | -11% | 2.0 / 2.9 | -8° | 0/0 | 16% wide for its own alphabet; stem 11% light for its own alphabet; 3% tall above the baseline for its class; hairline too fat — 2.0:1 here, Coelacanth 2.9:1 |
| `R` | 2.8 | -3% | -14% | 2.4 / 2.2 | +4° | 0/1 | stem 14% light for its own alphabet; hairline too thin — 2.4:1 here, Coelacanth 2.2:1; descends 0.04 xh shallower than its class; thins at 16° where the face's nib is 24° — 4° further off than Coelacanth is here |
| `J` | 2.6 | -4% | +11% | 1.4 / 2.0 | -- | 0/0 | descends 0.05 xh shallower than its class; hairline too fat — 1.4:1 here, Coelacanth 2.0:1; stem 11% heavy for its own alphabet; sets 19% blacker than its class |
| `l` | 2.5 | +4% | -13% | 1.9 / 1.4 | -2° | 0/0 | 4% short above the baseline for its class; stem 13% light for its own alphabet; hairline too thin — 1.9:1 here, Coelacanth 1.4:1 |
| `u` | 2.5 | -11% | +1% | 2.8 / 3.0 | +2° | 1/0 | 11% narrow for its own alphabet; 1 concave notch where strokes union — no stroke width tunes these out; 2% tall above the baseline for its class |
| `C` | 2.4 | -2% | -16% | 2.7 / 2.5 | -20° | 0/0 | stem 16% light for its own alphabet; hairline too thin — 2.7:1 here, Coelacanth 2.5:1 |
| `W` | 2.4 | +19% | -2% | 2.1 / 2.7 | +0° | 0/3 | 19% wide for its own alphabet |
| `T` | 2.4 | -5% | +2% | 1.8 / 1.8 | +2° | 0/1 | 3% short above the baseline for its class; descends 0.04 xh shallower than its class |
| `V` | 2.4 | +18% | -7% | 2.1 / 2.6 | -4° | 0/1 | 18% wide for its own alphabet |
| `L` | 2.3 | -13% | -1% | 1.5 / 2.0 | -2° | 0/0 | 13% narrow for its own alphabet; hairline too fat — 1.5:1 here, Coelacanth 2.0:1 |
| `O` | 2.3 | +11% | -13% | 2.4 / 2.3 | -6° | 0/0 | stem 13% light for its own alphabet; 11% wide for its own alphabet; hairline too thin — 2.4:1 here, Coelacanth 2.3:1 |
| `e` | 2.2 | +10% | +13% | 2.8 / 2.9 | -30° | 0/0 | stem 13% heavy for its own alphabet; 10% wide for its own alphabet; descends 0.03 xh shallower than its class |
| `b` | 2.2 | +13% | -14% | 2.4 / 2.3 | -8° | 0/1 | stem 14% light for its own alphabet; 13% wide for its own alphabet |
| `s` | 2.2 | -6% | -13% | 2.7 / 3.0 | -2° | 0/0 | stem 13% light for its own alphabet |
| `K` | 2.2 | +12% | -13% | 3.5 / 3.5 | -8° | 0/3 | matches |
| `w` | 2.1 | -6% | -12% | 2.6 / 3.1 | -8° | 0/3 | matches |
| `3` | 2.1 | +7% | +9% | 2.6 / 2.5 | -4° | 0/0 | matches |
| `t` | 2.0 | -3% | -4% | 2.1 / 2.3 | +4° | 0/1 | matches |
| `M` | 1.8 | +0% | -3% | 2.3 / 2.2 | +4° | 0/3 | matches |
| `F` | 1.8 | -5% | +11% | 1.6 / 2.0 | -6° | 0/2 | matches |
| `Y` | 1.8 | -9% | +6% | 2.5 / 2.9 | +4° | 0/0 | matches |
| `f` | 1.7 | -2% | +2% | 1.7 / 1.9 | -20° | 0/0 | matches |
| `h` | 1.7 | -0% | +2% | 3.1 / 2.4 | -2° | 0/1 | matches |
| `r` | 1.5 | +0% | -5% | 3.1 / 3.3 | -- | 1/1 | matches |
| `P` | 1.4 | +0% | +12% | 2.3 / 2.2 | -10° | 0/0 | matches |
| `v` | 1.4 | -1% | +8% | 3.2 / 2.8 | -6° | 0/0 | matches |
| `x` | 1.4 | -3% | +2% | 2.7 / 2.4 | -4° | 0/2 | matches |
| `m` | 1.1 | +8% | -1% | 3.5 / 3.1 | -2° | 0/1 | matches |
| `6` | 1.1 | +7% | -2% | 2.2 / 2.7 | -10° | 0/0 | matches |
| `n` | 1.0 | +7% | +3% | 3.3 / 3.0 | +0° | 0/1 | matches |
| `B` | 0.9 | +4% | +4% | 1.7 / 2.2 | -14° | 0/1 | matches |
| `D` | 0.4 | -1% | -2% | 1.7 / 2.0 | +0° | 0/0 | matches |

---

## 8. Two traps this instrument had to be rebuilt around

Both produced a confident, plausible, wrong table first. They are in the
script's docstring too; they are here because the next person to write a
whole-alphabet measurement will hit them again.

**Do not take the pen's thin direction as the argmin over 15° bins.**
`cmp_g_strokes.py` does, and on a single g that is fine. Over 62 glyphs it is
not: a bin holding four ridge samples off a serif tip wins the argmin. The first
run of this script reported Albo's `Y` at **22.15:1** contrast and its `V` at
**15.29:1**, against Coelacanth's 3.14 and 2.45 — and quantised every angle to a
multiple of 15, so that all 62 glyphs "deviated" from a median that fell between
two bins and the table flagged the entire alphabet. The fix is a sliding ±22°
window at 2° steps, each window a median over at least 25 samples; and contrast
is not read off that profile at all, but from percentiles of ridge thickness,
which have no argmin to capture.

**`top` and `depth` cannot be residualised by letter case.** The lowercase
"class" holds x-height letters and ascenders together, so its median height is a
number no letter in it has. Height is a log ratio (Albo's cap is 94.8% of
Coelacanth's on *every* cap, so a class median removes it cleanly); depth is an
absolute difference — a flat letter's depth is ~0 and a ratio explodes — so it is
residualised inside a band read off Coelacanth's own value.

And the one that is not a trap but a rule, from `cmp_g_strokes.ridge`: **no
percentile threshold on the ridge sample.** Keeping only the top of the distance
range deletes every thin stroke, because a thin stroke's distance is small all
along it. An instrument that samples only the thick parts of a letter cannot
measure how thin the thin parts are.
