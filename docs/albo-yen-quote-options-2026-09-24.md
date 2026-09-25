# Albo: the yen's gap and the quotes' symmetry, as options (2026-09-24)

Owner, 2026-09-24: *"give me clever options for the Italic and bold italic yen
characters to have a visible gap like the Y branch and trunk has; give me
options for making the single quote and double quote characters slightly more
and very symmetrical."*

**Nothing ships from this doc.** Every option is env-selectable with today's
drawing as the default:

- `ALBO_YEN_GAP=a|b|c|d|e`
- `ALBO_QUOTE_SYM=a|b|c|d|e`

`a` is today's drawing in both. With both variables unset, all four cuts are
**outline-identical to HEAD `901a6ae`**. `cmp_outlines.py` reports "0 of 530
shared glyph outlines differ" on Regular, Italic, Bold and BoldItalic.
`gates.sh` reports GATES UNCHANGED.

Code:
- `g_yen` and `_yen_gapped` in `outlines/glyphs/symbols.py`. Only the yen
  function was touched.
- `quote_sym`, `straight_quote` and `quote` in `outlines/glyphs/marks.py`.
- `OPTION_PHASE` in `outlines/build.py`.

Instruments: `tools/wedge_serif/instruments/yenq_*.py`. Set `ALBO_OPT_DIR` to a
folder that holds `head/`, `opt_b/` … `opt_e/`. Each of those is one
`albo_build_all` OUTDIR, built with `ALBO_YEN_GAP=X ALBO_QUOTE_SYM=X
ALBO_YEN_GAP_ROMAN=1`.

## The cut-phase ripple, contained

The yen options add islands, so the yen's contour count goes from 1 to as many
as 5. The cut's phase counter is global (`PHASE_LEGACY`, round 384), so an
un-contained option would re-cut every glyph after the yen.

`build.OPTION_PHASE` handles this. When an option is set, the glyph re-draws
its default and consumes that default's contour count. Any contours beyond it
take their phase from the side counter.

Proof: with an option set, `cmp_outlines.py` against HEAD moves exactly 9
glyphs in every cut, and no others. The 9 are `quotedbl`, `quotedblleft`,
`quotedblright`, `quoteleft`, `quoteright`, `quotesingle`, `uni02BB`,
`uni02BC` and `yen`. This held for all four option builds × four cuts.

I did not build without the containment to measure the ripple it prevents.
Round 384 measured that ripple (60 glyphs for six contour-count changes), and
this uses the same mechanism.

## The Y's gap, measured first (built HEAD, unsheared)

| cut | the Y's white between arm and trunk |
|---|---|
| Italic | **13.0 units** at 0.418 cap (nearest approach, two islands) |
| BoldItalic | **1.3 units** at 0.431 cap. Invisible at any size, and it reads as touching in the 6× crop. |
| Regular, Bold | **none.** The roman Y is one contour, and rows 0.34–0.46 of the cap are one solid run. `albo-hairline-gap.md`'s 7–8 unit table for the roman Y describes an older drawing. |

So the only gap there is to "echo" is the Italic 400's. Every option therefore
cuts a designed white of **16.8 drawing units** (`ALBO_YEN_GAP_W`), which is
the Italic Y's own measured distance before the ink spread. That builds to
**13.7–14.1 units in every cut**.

Two things follow in the BoldItalic:
- The yen's arm root is trimmed to the same white.
- The yen then shows a gap that the BoldItalic Y itself does not have. That is
  a finding about the BoldItalic **Y**, recorded here and not fixed: its ruled
  gap nearly closes at the 700.

## Yen options

| env | name | what it draws | white, built (Italic / BoldItalic) | islands (I / BI) |
|---|---|---|---|---|
| `a` | today | two full bars over the join, `_fill_cracks` | — (buried) | 1 / 1 |
| `b` | **CHANNEL** | the gap carried down the trunk's right edge through both bars. Each bar fuses to the trunk on the left and stands one gap off it on the right, as the arm does | 13.8 / 14.0 | 2 / 2 |
| `c` | **FREE TRUNK** | the same white on both sides: no bar touches the trunk | 13.8–14.4 / 14.0–14.1 | 4 / 4 |
| `d` | **ONE BAR** | a single bar, 1.15× the rule, at the arm-end height. Its right half grows out of the arm, its left out of the trunk, and the gap splits it | 13.7 / 13.7 | 2 / 2 |
| `e` | **ABOVE** | both bars lifted over the join (gap +0.11 and +0.25 cap) to cross the branches, so the gap stands clear beneath them | the Y's own (13.0) / opened to ~14 | 1 / 1 |

Dials, for later tuning: `ALBO_YEN_GAP_W` (16.8), `ALBO_YEN_D_Y` (0.03 cap
above the gap), `ALBO_YEN_E_LO` / `ALBO_YEN_E_HI` (0.11 / 0.25).

**Upright cuts.** The options apply to the italics only. `ALBO_YEN_GAP_ROMAN=1`
applies them to Regular and Bold too, which is how the proof shows them. They
**should not ship there**: the roman Y has no gap, so the yen would carry a
feature its own letter lacks. On the roman, b/c/d read as a notch beside the
stem, and e as a strike-through of the fork.

**Reading size:** at 20 px a 14-unit white is 0.28 px. It is invisible in
running text in every option (see the 2× text strip). As with the Y, it is a
feature of the large letter.

### Gates, per option (all four cuts)

| check | result |
|---|---|
| `cmp_contour_hairs.py` (full sweep) | PASS in every cut, every option |
| `cmp_touch.py` | 0 touching and 0 under the floor, every cut, every option |
| `cmp_aldine_glitch.py --ttf --all` | **No CRACK, PINCH, NEEDLE or SPECK from any option.** The only new row is `¥ SPLIT` (b, c, d: 2–4 islands, where 1 is expected). |

The SPLIT is the same class the gate already reports for the Italic Y, and
which round 384 accepted in prose ("the italic Y's ruled hairline gap").

**Proposal for the gate:** do not add ¥ to `MULTI` as a constant, because the
island count differs by option and by cut. Have the gate read
`symbols.yen_gap_opt()` and expect the Y's own island count plus the bar pieces
the option draws. Also give the Y itself a `MULTI` entry of 2 in the italics,
so both designed gaps are recognized rather than noted in prose. Not
implemented; it waits on which option (if any) is chosen.

**A near-crack found and fixed inside option b/c:** the Italic arm's tip lands
7.96 drawing units (5.0 built) above the right-hand piece of the lower bar. That
is a slit, the same thing round 384 filled, not the designed gap.

- It is welded: the convex hull of the arm and that bar piece within 14 units
  of their nearest approach, kept out of the gap's halo.
- A mitre closing was tried first and did nothing. A closing cannot bridge a
  corner to an edge: the dilated neck is narrower than the erosion that
  follows.
- After the weld, the Italic b has 2 islands, not 3.

**Seen and not fixed:** in `d` (Italic, BoldItalic) and `b`/`c` (BoldItalic),
the bar's lower edge meets the arm's cut edge in a 2–3 unit ledge. It is
visible only in the 6× crop, and no gate flags it.

## Quote options — a ladder

`s` = 0, 1/3, 2/3, 1 for a, b, c, d. What `s` scales:

- **straight ' "**: the roman's written-tick LEAN; its top PEN CUT; round 251's
  per-mark table (so at d the two marks of " are identical, which undoes the
  owner's "slightly randomized" of 2026-09-18 at that rung only); the italic's
  foot PEN CUT. At d each mark is a straight stroke with square ends: tapered
  on the roman, parallel on the italic.
- **curly ‘ ’ “ ”** (and ʼ ʻ, which call the same function): the tail's
  sideways swing and bend scale by 1 − s. The tail's width blends by s from
  the pen's comma taper to a cone that runs from the dot's full diameter to the
  comma's tip. At d the mark is the convex hull of the two: a symmetric
  teardrop on a plain round dot, with no filed flat. From b on, ‘ is the exact
  mirror of ’. Before, it ended 0.55 W across where ’ ends 0.60 W, and the
  dot's filed flat did not mirror.
- **e**: the other reading of "symmetrical" for a curly quote. It is d's
  teardrop, symmetric about its own axis, tilted 20° (`ALBO_QUOTE_SYM_TILT`,
  the comma's own tip-to-dot lean) so it still reads as a 9 or a 6. The
  straight quotes take d.
- **Not touched:** ‚ „ (the low quotes are the comma itself).

Measured on the built TTFs (italics unsheared;
`instruments/yenq_quote_symmetry.py`). Definitions:

- **mirror IoU**: the mark against its own mirror image about the vertical.
- **axis IoU**: the same test after rotating the mark upright.
- **tilt**: the principal-axis angle from vertical.
- **edge Σ**: left-edge slope plus right-edge slope, in degrees; 0 means
  mirror-symmetric.

| cut | option | `'` mirror IoU | `'` edge Σ | `’` mirror IoU | `’` tilt | `’` edge Σ | `‘` mirror IoU | “‘ vs mirrored ’” IoU | `"` mark-to-mark IoU |
|---|---|---|---|---|---|---|---|---|---|
| Regular | a | 0.803 | +5.9 | 0.650 | 12.6° | +17.0 | 0.561 | 0.847 | 0.983 |
| | b | 0.858 | +4.0 | 0.730 | 8.3° | +12.4 | 0.730 | 0.955 | 0.987 |
| | c | 0.929 | +1.5 | 0.790 | 4.5° | +6.6 | 0.796 | 0.970 | 0.990 |
| | d | **0.995** | 0.0 | **0.962** | 0.2° | 0.0 | **0.999** | 0.957 | 0.993 |
| | e | 0.995 | 0.0 | 0.500 (axis 0.954) | 19.8° | — | 0.511 | 0.967 | 0.993 |
| Italic | a | 0.931 | −0.4 | 0.640 | 11.8° | +15.2 | 0.584 | 0.866 | 0.990 |
| | b | 0.957 | +0.1 | 0.743 | 7.8° | +10.8 | 0.740 | 0.945 | 0.993 |
| | c | 0.976 | +0.1 | 0.810 | 3.8° | +4.8 | 0.809 | 0.955 | 0.994 |
| | d | **0.996** | −0.2 | **0.959** | 0.2° | −0.1 | **0.993** | 0.962 | 0.993 |
| | e | 0.996 | −0.2 | 0.496 (axis 0.959) | 20.2° | — | 0.502 | 0.946 | 0.993 |
| Bold | a | 0.774 | +7.9 | 0.783 | 13.3° | +11.0 | 0.743 | 0.887 | 0.998 |
| | d | 0.999 | 0.0 | 1.000 | 0.0° | 0.0 | 1.000 | 1.000 | 0.998 |
| BoldItalic | a | 0.898 | +0.1 | 0.797 | 12.0° | +9.0 | 0.764 | 0.883 | 0.995 |
| | d | 0.999 | +0.1 | 0.995 | 0.2° | −0.2 | 0.995 | 0.995 | 0.997 |

The Bold's and BoldItalic's b and c sit on the same ladder: ’ IoU 0.808 / 0.866
(Bold) and 0.814 / 0.873 (BoldItalic). The full table is the instrument's
output.

Why the 400s stop short of 1.000 at d: the hand-cut facet decimation
(`FJORD_CUT`) is itself asymmetric. The Bolds, built with `FJORD_CUT=0`, reach
0.995–1.000.

**Gates for the quotes** (same builds): hairs PASS, 0 touching, 0 under the
floor, and no new glitch rows. The two existing “ ” SPLIT rows are unchanged in
kind. The closest quote pairs move slightly but stay above the 0.012 em floor:

- BoldItalic `'?`: 0.0127 at HEAD → 0.0130–0.0139
- Italic `'?`: 0.0172 → 0.0154 (b) … 0.0169 (d)
- BoldItalic `q'`: 0.0151 → 0.0180–0.0209, which is more room

## Recommendation

- **Yen: `b` (CHANNEL), italics only.**
  - It is the one option where the gap reads as the Y's own gap continued: the
    same white, on the same side, following the same edge down through both
    bars.
  - It keeps the two-bar ¥ that readers expect.
  - It adds one island and no finding beyond the expected SPLIT.
  - `d` is the most distinctive: the bar grows out of the arm. But a one-bar ¥
    is the less common form and reads closer to a yuan/JIS variant.
  - `c` is busier (4 islands) for no extra echo of the Y.
  - `e` keeps the Y's gap literally untouched but moves the bars off the join
    that a ¥'s bars normally cross.
- **Quotes: `b` if "slightly more", `d` if "very".**
  - `c` is the middle rung.
  - `d` meets "very symmetrical" in the strict sense: mirror IoU 0.96–1.00,
    tilt 0°.
  - `e` is the curly-quote alternative, for keeping direction: symmetric about
    its own axis, 0.95–0.995.
  - One cost at `d`: the straight double quote loses round 251's per-mark
    variation. That was an owner ruling, so choosing d reverses it for ".

## Tried and discarded

- **Curly quote straightened at the pen's own width.** The first cut of `d`:
  a thin pin stuck in a ball, looked at and rejected. The blended cone
  replaced it.
- **Single bar exactly at the gap's nearest-point height** (`ALBO_YEN_D_Y=0`).
  The arm's tip sat on the bar as an angle, not inside it. 0.02–0.04 were
  laddered, and 0.03 ships as the option's default.
- **Yen bars at gap + 0.13 / + 0.29 cap for `e`.** The upper bar ran into the
  top serifs. Lowered to +0.11 / +0.25.
- **The BoldItalic's own Y gap (3.4 drawing units) as the yen's white.** It
  builds to about 1 unit, which cannot be seen. Replaced by the Italic's 16.8
  in every cut.
- **A morphological closing for the Italic arm-to-bar slit.** Inert, for the
  reason given above.

## Proof images (lossless PNG, native pixels)

Rendered from the four TTFs of each option build via PIL (RAQM):

1. `yen-grid.png`: the ¥ at 110 px em. Rows a–e, columns the four cuts.
2. `yen-gap-crop-italic-6x.png` and `yen-gap-crop-bolditalic-6x.png`: the Y's
   gap beside the ¥'s, rows b–e, rasterized from the TTF outline at 6 px per
   design unit (one sample per pixel centre).
3. `yen-text-2x.png` and `yen-text-roman-2x.png`: "Price ¥1,200 · ¥Y" at
   20 px, magnified 2× nearest.
4. `quotes-straight-grid.png` (110 px em) and `quotes-curly-grid.png` (84 px
   em, so the Bold's six marks fit their cell).
5. `quotes-curly-text-2x.png` and `quotes-straight-text-2x.png`: a sentence
   with 'single' and "double" quotes and an apostrophe, at 20 px, 2× nearest.

`instruments/yenq_proofs.py` regenerates all of them.

## RULED 2026-09-24 (owner)

*"for yen, b for italics only; c for straight quotes, leave curly alone"*

- **¥, Italic and BoldItalic:** option **b**, the channel, as the code default (`"b" if pen.ITALIC else "a"` in `g_yen`). The romans stay **a**.
- **Straight quotes `'` `"`, all four cuts:** option **c**, as the code default (`QUOTE_SYM_DEFAULT` in `marks.py`). Curly quotes stay **a**. Each kind has its own switch (`ALBO_QUOTE_SYM_STRAIGHT` / `_CURLY`); `ALBO_QUOTE_SYM` still overrides both.
- **Phase containment:** `build._option_phase_k` now ALWAYS counts the `a` drawing for these glyphs, because a shipped default adds islands as surely as an env var does.
- **Proof of scope:** `cmp_outlines.py` against the pre-ruling build moves only `quotesingle` and `quotedbl` in every cut, plus `yen` in the two italics.
- **Gates:** the contour census records the italic ¥ at 1 → 2, accepted. Hairs, touch and glitch are clean in all four cuts.
