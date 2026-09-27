# Albo Italic against its Roman: size, set width and nib (2026-09-26)

Owner, 2026-09-26: *"check italic and roman are using the same nib. italic
seems too small."* Seen on the Reader Font preview at 18 pt, dark, where an
italic sentence follows a roman paragraph. This doc takes that report as the
premise and measures where the italic falls short.

**Surveyed:** the shipped round-404 fonts, built from `git archive 736d928`
with `build_env.sh`'s shipping environment. Round 405 (0bb48e5, the B2 refit
on session 6) landed while this was being written. It moves bearings by a few
units and does not change any conclusion here. It was not re-measured.

**Instruments** (all in `tools/wedge_serif/instruments/`):
`italic_size_nib.py` for the ratio table, `italic_ink_white.py` for the ink
and white split, and `italic_size_proof.py` for the proof image. Every number
comes from an UNHINTED FreeType raster at 1000 ppem (1 px = 1/1000 em), with
HarfBuzz shaping and kerning on.

## 1. The answer, short

- **The nib is not the same.** The italic's straight-stem letters are drawn
  at **0.83 of the roman's stem**. Measured at mid x-height the ratio is
  0.906, against a reference median of 0.962. That is inside the reference
  range (0.807 to 1.027), but in its lower half.
- **"Too small" is mostly SET WIDTH, not x-height.** The italic sets **0.81**
  of the roman's advance per character. All eleven references sit at 0.84 or
  above (median 0.93), so Albo is below every one of them. Its ink is
  **0.70** of the roman's width at mid x-height, where the references run
  0.80 to 1.14 (median 0.93). Its *white* is normal (0.92, against a
  reference median of about 0.89). So the letters themselves are drawn
  narrow; the spacing is not what is tight.
- **The x-height is 1.000.** The references run 0.991 to 1.035, with a median
  of 1.015. Albo is inside that range but at the low end, and most real
  italics are about 1.5% taller than their roman.
- The **apparent size** (x-height × width) is 0.81, below every reference
  (range 0.86 to 1.03, median 0.955). This is the number that matches what
  the owner saw.

## 2. The code trace: three nibs, not one

| what | where | at the 400 |
|---|---|---|
| Roman pen | `outlines/pen.py:42` `S = FJORD_STEM` · `:43` `CONTRAST` · `:149` `PEN = FlooredPen(_Pen(S, CONTRAST, ...))` | stem 66.9, contrast 0.892 (`build_env.sh:15`) |
| Italic env | `build_env.sh:16` | same `FJORD_STEM=66.9`, but `FJORD_CONTRAST=0.80`, `FJORD_WIDTH=95`, `FJORD_SLANT=13` |
| Italic **hm_\*** letters (a b d h i l m n p q r u, heads, exits, arches, dots) | `outlines/glyphs/aldine.py:878` `ALD_WF = pen.S / 84.0` × `:884` `HM_STEMW = 70 × ALD_WF` | Flanker's 70-unit stem scaled by 0.796 = **55.7 units = 0.83 S** |
| Italic "declared width" letters (t f j v w x y z c g, the bowls) | `aldine.py:194` `ALD_WF_UP = max(1.0, S / 84)` | **1.0**, which is the Medium's absolute widths (the t measures 67, the j 70) |
| Italic o, e | `aldine.py:1878` `O_THICK × S`, where S is `pen.S` itself | the roman's S |

Round 263 put the hm letters on `S / 84`. That factor was calibrated when the
face was drawn at the Medium's stem of 84, where Flanker's 70 is 0.83 of 84.
Round 266 re-anchored the family on the 400 (S = 66.9), and the factor
carried that 0.83 down with it. Round 269 then deliberately left the other
letters at 1.0 under the Medium ("a factor that also went DOWN would re-cut
ten letters"). So inside the italic, `i` and `l` measure 57 to 58 (horizontal
run at mid x-height) while `t` measures 67, `j` 70 and `f` 66. The roman's
`i`, `l` and `n` all measure 64.

Flanker's own italic stem is **1.01×** its roman's (74 against 73). Albo
copied Flanker's italic stem in absolute units, against a roman that was
heavier than Flanker's, and so ended up with 0.83.

`FJORD_WIDTH=95` is **not** the cause. It barely reaches the aldine italic:
setting it to 100 moves only the `s` (+9 units), and 110 moves it +22. The
width lives in the per-letter drawing. `ALBO_ALD_HM_PITCH` moves only `h m n
r u`.

## 3. Measurements: italic/roman ratios

`xh` is the x's top. `stem` is the median horizontal run through `i l n m u`
at mid x-height. `hair` is the o's thinnest crossing. `wid` is the shaped
advance per character of an Austen paragraph. `ink` is the ink area per
character. `col` is ink / (wid × xh). `app` is xh × wid.

| face | xh | cap | asc | desc | stem | hair | wid | ink | col | app |
|---|---|---|---|---|---|---|---|---|---|---|
| Palatino | 1.011 | 0.999 | 0.936 | 1.004 | 0.807 | 1.150 | 0.904 | 0.818 | 0.896 | 0.913 |
| Pagella | 1.028 | 1.000 | 1.010 | 0.982 | 0.821 | 0.964 | 0.901 | 0.832 | 0.898 | 0.926 |
| Charter | 1.010 | 1.000 | 1.000 | 1.000 | 0.964 | 1.125 | 0.961 | 0.906 | 0.933 | 0.971 |
| Georgia | 1.015 | 1.000 | 1.000 | 1.000 | 1.000 | 1.133 | 1.018 | 0.992 | 0.961 | 1.033 |
| Baskerville | 1.035 | 1.000 | 1.000 | 0.964 | 0.871 | 0.909 | 0.840 | 0.841 | 0.967 | 0.870 |
| Hoefler Text | 1.035 | 1.000 | 0.999 | 1.004 | 0.978 | 0.969 | 0.877 | 0.969 | 1.067 | 0.908 |
| Iowan | 0.998 | 0.954 | 1.008 | 1.008 | 0.962 | 1.185 | 0.862 | 0.894 | 1.038 | 0.861 |
| Times | 0.991 | 0.986 | 1.000 | 0.959 | 0.929 | 1.364 | 0.999 | 0.903 | 0.912 | 0.990 |
| Flanker Griffo | 1.023 | 1.000 | 0.995 | 1.000 | 1.014 | 0.880 | 0.974 | 0.988 | 0.991 | 0.996 |
| Coelacanth | 1.012 | 1.009 | 1.013 | 1.000 | 0.914 | 1.069 | 0.944 | 0.932 | 0.976 | 0.955 |
| ITC Berkeley (Medium) | 1.035 | 1.000 | 0.997 | 1.032 | 1.027 | 0.931 | 0.928 | 0.949 | 0.987 | 0.961 |
| **reference median** | 1.015 | 1.000 | 1.000 | 1.000 | 0.962 | 1.069 | 0.928 | 0.906 | 0.967 | 0.955 |
| reference min / max | 0.991 / 1.035 | | | | 0.807 / 1.027 | 0.880 / 1.364 | 0.840 / 1.018 | 0.818 / 0.992 | 0.896 / 1.067 | 0.861 / 1.033 |
| **Albo r404** | **1.000** | 0.999 | 1.001 | 1.004 | **0.906** | **0.833** | **0.812** | 0.857 | 1.056 | **0.812** |

Absolute values for Albo (per 1000 em): the roman has xh 451 (the x's
serifs; sxHeight is 429), stem 64 and hair 12. The italic has xh 451, stem 58
and hair 10.

**Outside the reference range:** `wid` (0.812, below 0.840), `app` (0.812,
below 0.861) and `hair` (0.833, below 0.880). The hair measure is coarse:
±1 unit at 10 is ±10%. For the options below it swung from 7 to 21 on
shapes that did not change that much, so it is reported for today only.

**Per letter** (advance ratio, italic/roman): n 0.791, o 0.719, e 0.780,
a 0.878, space 0.857. The lowest reference n is Baskerville at 0.804, and
the lowest o is Baskerville at 0.729. Nine of the eleven references keep the
word space at 1.000.

**Ink and white split** (`italic_ink_white.py`: mid-x-height ink extent
against the rest of the advance, lowercase in the paragraph):

| | ink-mid | white | adv | italic white/adv |
|---|---|---|---|---|
| references | 0.80 to 1.14 (median 0.93) | 0.79 to 1.02 (median 0.89) | 0.81 to 1.02 | 0.41 to 0.51 |
| Albo r404 | **0.696** | 0.917 | 0.797 | **0.53** |

## 4. Options (env dials, default = today)

Added in this commit:

- `ALBO_ALD_NIB` (`aldine.py:877`) multiplies `ALD_WF`, which covers the hm
  letters only.
- `ALBO_IT_LC_SCALE` (`build.py:244`) is a uniform scale of the italic
  lowercase ink.
- `ALBO_IT_LC_SETW` (`build.py:245`) is a horizontal-only scale of the italic
  lowercase ink.

Both `build.py` dials act about the origin, on the UNSHEARED ink, before the
ink spread and the shear (`build.py:198`). The fit then derives bearings from
the scaled shape.

**Defaults are outline-identical to today.** `cmp_outlines.py` reports 0 of
530 shared glyph outlines differing, Regular and Italic, and `gates.sh`
reports GATES UNCHANGED against the baseline.

| arm | dials | xh | stem | wid | ink | col | app |
|---|---|---|---|---|---|---|---|
| a today | none | 1.000 | 0.906 | 0.812 | 0.857 | 1.056 | 0.812 |
| b | SCALE 1.03 | 1.029 | 0.922 | 0.828 | 0.907 | 1.065 | 0.852 |
| **c** | SCALE 1.05 | 1.049 | 0.953 | 0.837 | 0.942 | 1.072 | 0.878 |
| d | SCALE 1.08 | 1.078 | 0.969 | 0.853 | 0.995 | 1.082 | 0.920 |
| **e** | NIB 1.06 | 1.000 | 0.953 | 0.815 | 0.877 | 1.077 | 0.815 |
| f | NIB 1.20 (the hm stem = the roman's S) | 1.000 | 1.078 | 0.821 | 0.924 | 1.127 | 0.821 |
| g | SETW 1.08 | 0.998 | 0.969 | 0.855 | 0.922 | 1.081 | 0.853 |
| **h** | SETW 1.15 | 0.998 | 1.031 | 0.894 | 0.979 | 1.098 | 0.892 |
| i | SCALE 1.02 + SETW 1.10 | 1.018 | 1.016 | 0.878 | 0.975 | 1.092 | 0.893 |
| **m** | SCALE 1.015 + SETW 1.15 + NIB 0.92 | 1.013 | 0.953 | 0.899 | 0.977 | 1.073 | 0.911 |
| n | SCALE 1.015 + SETW 1.20 + NIB 0.88 | 1.013 | 0.969 | 0.924 | 1.002 | 1.070 | 0.936 |

Scaling moves the set width by about half the factor. SCALE 1.05 moves `wid`
+3%, and SETW 1.15 moves it +10%, because the fit and the absolute B2 deltas
hold part of the white.

To reach the reference width, the horizontal stretch has to be large. That
thickens vertical strokes with it, so a width that matches the references
wants the hm nib turned DOWN (arms m and n). Even so, the net stem is heavier
than today's (0.953 against 0.906).

`col` stays above the reference median in every arm. The italic's x-height
band is already denser than its roman's, and no arm here fixes that.

### Gates per shown arm (italic 400; dents on the matching BoldItalic 700)

| arm | hairs --letters / all | touch (5,193 pairs) | approved.py | contour census | dents 700 |
|---|---|---|---|---|---|
| a | = today / = today | 0 / 0 | ok | unchanged | 0 |
| c | = today / = today | **4 touching** (qj qf qp qy) | **Italic g changed** | unchanged | 0 |
| e | = today / = today | 0 / 0 | ok (g not on ALD_WF) | unchanged | 0 |
| h | = today / = today | **2 touching** (qj qf), 3 under floor (4j Jj 4f) | **Italic g changed** | unchanged | 0 |
| m | = today / = today | **4 touching** (qj qf qp qy), 3 under floor | **Italic g changed** | unchanged | 0 |
| n | = today / = today | **6 touching** (+4j Jj), 1 under floor | **Italic g changed** | **CHANGED**: iota 1→2 contours, which re-cuts 256 glyphs | 0 |

**The approved italic g.** Arm e does not touch it: the g is on `ALD_WF_UP`,
not `ALD_WF`, and its IoU against today is 1.0000. Every SCALE or SETW arm
changes it, and changes it UNIFORMLY. This was checked by applying the
arm's own transform to today's g (unshear, scale, reshear) in the raster and
comparing:

| arm | g | a | n |
|---|---|---|---|
| c | 0.986 | 0.988 | 0.988 |
| h | 0.992 | 0.986 | 0.984 |
| m | 0.988 | 0.964 | 0.923 |

The 1 to 1.5% on the g is edge-raster and cut noise. In m, the a and n are
lower because the NIB part of that arm acts on them and not on the g.
Shipping any SCALE or SETW arm is a new ruling on the g: `approved.py --add
g --style Italic`.

**The touching pairs are all descender collisions.** They are the italic q's
tail against a following f j p y, plus j under 4 and J. Round 178's rule
applies: they want kern pairs, not a wider fitting band.

**Line fit** (the vertical metrics are fixed: hhea +1000/−300, usWin
1000/320). Today the italic's lowercase already reaches −319, inside usWin.
At SCALE 1.03 it reaches −328, at 1.05 −335 and at 1.08 −344, all past usWin
320, which risks clipping on Windows-metric renderers. The accented tops
(head yMax) go 972 → 1011 at 1.05. Line spacing is unaffected (1300/em).
Arm m reaches −323.

**B2 spacing.** The italic's bench fit (`ALD_LC_ADJ`, the B2 tables, the
kerns) is ABSOLUTE units learned on today's italic, and none of these dials
rescales it. Any SETW arm widens the letters' own white as well: white per
character goes 200.9 → 219.4 (h) and 221.5 (m), against the roman's 219.2.
That is +9 to 10%, so every pair white the owner judged on the bench moves.
Shipping h or m means a re-bench of the italic rows (or at least the
spacing proof) before the refit is trusted. Arm e leaves the white unchanged
(200.8).

## 5. Recommendation

The measured shortfall is **set width**, so the arm that answers "too small"
is one that widens.

- **m** (SCALE 1.015, SETW 1.15, NIB 0.92) is the only built arm with every
  ratio inside the reference range: xh 1.013, stem 0.953, wid 0.899,
  ink 0.977, app 0.911.
- **h** (SETW 1.15 alone) is the one-dial version. Its stem (1.031) lands
  just past the reference max of 1.027.

Both cost the same things:

- 2 to 4 q-descender kerns and 3 under-floor pairs
- a re-approval of the italic g (the change is uniform)
- an italic bench pass, because the pair whites grow about 10%

**e** (NIB 1.06) is the literal answer to "same nib". It moves the stem to
the reference median at no gate cost, but it barely moves the apparent size
(0.815), so on its own it does not answer "too small". **c** (x-height +5%)
is the obvious reading of "too small", but it pushes the x-height past every
reference (1.049 against a max of 1.035) while still leaving the width below
the reference minimum.

This is the owner's call on the picture. The recommendation is m, with h as
the simpler fallback.

## 6. Checked and found clean

- The default dials are outline-identical: 0 of 530 glyphs differ in
  Regular and in Italic. `gates.sh` on the working tree (round 405 plus
  these dials) reports GATES UNCHANGED: approved, bench, contour census, the
  e mouth, hairs and touch.
- `FJORD_WIDTH` is not the width lever for the aldine italic. At 100 it moves
  only the `s`.
- Cap height ratio 0.999: the capitals are not what reads small.
  Ascender 1.001, descender 1.004.
- The dents gate at 700 is 0 on every arm.
- The hairs gate (letters and full sweep, reduced to names exactly as gates.sh reduces them) matches today on every shown arm.

## Proof

`scratchpad/nib/italic-size-nib.png` (session scratchpad, not published) is
roman then italic on one line at 14 and 18 pt on the phone (2x). It is
unhinted, 2-bit, on the frozen dark page, with today on top of each block and
arms c, e, h and m below. To regenerate it, run `italic_size_proof.py DIR`
over a directory holding `today/` and `opt_{c,e,h,m}/`.
