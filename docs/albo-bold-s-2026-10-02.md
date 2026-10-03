# Albo: the Bold S's width (2026-10-02)

Owner todo: *"bold S seems small in 'Step'"*.

**Status: OPTIONS. Nothing shipped.** The dial is `ALBO_ROM_S_W_BOLD` in
`tools/wedge_serif/outlines/build.py` (`CAP_S_WIDTH_BOLD`), default 1.0. At 1.0
the Bold is byte-identical to round 464's (`cmp_outlines`: 0 of 530 glyphs
differ).

## 1. What is small about it

The Bold S is not short. It is narrow. Each glyph's outline ink box was measured
unhinted, in font units, by `tools/wedge_serif/instruments/bold_s_proof.py
--measure` (verified against source):

| | S/H width | S/E width | S/O height |
|---|---|---|---|
| **Albo Bold, round 464** | **0.544** | **0.747** | 1.007 |
| Georgia Bold | 0.686 | 0.876 | 0.999 |
| Charter Bold | 0.651 | 0.853 | 0.989 |
| Palatino Bold | 0.649 | 0.935 | 1.000 |
| TeX Gyre Pagella Bold | 0.661 | 0.933 | 1.000 |
| Times New Roman Bold | 0.629 | 0.771 | 1.009 |
| Baskerville Bold | 0.599 | 0.777 | 1.000 |
| reference median | 0.650 | 0.864 | 1.000 |
| reference range | 0.60–0.69 | 0.77–0.93 | 0.99–1.01 |

- **Height:** the S's height against its own O is inside the references (1.007
  against 0.99–1.01).
- **Width:** against its own H, the S is narrower than every reference: 0.544,
  where the narrowest reference (Baskerville Bold) is 0.599.
- **Against the E:** the same, 0.747 against 0.77–0.93.
- **The Regular S** measures 0.540, the same. It was not named and is not
  touched.

## 2. Negative result: a scale in `g_S` is undone

The first dial scaled the S's width inside its builder
(`caps_straight.py` `g_S`). It barely moved the letter:

| scale applied in `g_S` | ×1.10 | ×1.16 | ×1.20 |
|---|---|---|---|
| ink width (round 464: 407) | 409 | 418 | 428 |

`build.solve_widths` re-solves every capital's width multiplier, over three
passes, until its ink lands on the references' median target. A scale applied
while drawing is therefore taken back out on the next pass. The comments on
`CAP_NT_WIDTH` already say so ("a scale in draw() is undone, see below"), from
the N and T options of 2026-09-26.

The dial is now a factor on the solver's TARGET, as `CAP_NT_WIDTH` is. It
applies to the Bold only (stem > 84) and to the roman only, and it is checked
in `solve_widths`. The draw-time dial was reverted.

## 3. The arms

| arm | `ALBO_ROM_S_W_BOLD` | S/H | S/E | S/O h | S ink / advance |
|---|---|---|---|---|---|
| today | 1.0 | 0.544 | 0.747 | 1.007 | 407 / 479 |
| S1 | 1.10 | 0.592 | 0.813 | 1.010 | 443 / 516 |
| S2 | 1.15 | 0.618 | 0.848 | 1.004 | 462 / 534 |
| S3 | 1.20 | 0.642 | 0.881 | 1.006 | 480 / 553 |

- S1 lands just under the narrowest reference (Baskerville Bold, 0.60).
- S2 lands between Baskerville Bold and Times Bold (0.63).
- S3 lands near the references' median (Charter Bold and Palatino Bold, 0.65).
- The solver's three passes do not fully converge, which is why ×1.20 measures
  0.642 rather than 0.653.

## 4. What moves, and the gates

**`cmp_outlines`, every arm against today:**
- 8 glyphs move: S, Ś, Š, Ş, Ŝ, Ș, $ and §. Nothing else.
- $ and § are drawn from the S (`symbols.py` `g_dollar`, `g_section`; the
  section's docstring says *"the font's own S"*), so they widen with it.
- The $ advance goes 524 → 560 / 579 / 598. Today's 524 equals the figure
  zero's advance by coincidence, not by a rule: the $ takes its ink plus its
  own bearings, and those bearings do not move.

**`instruments/poor_gates.sh` (Bold), every arm against today:**
- hairs: none new in the letter sweep or the full sweep;
- touch: 0 / 0 before and after;
- counter-dent lines: 1 → 1;
- glitch: 5 of the 8 moved glyphs have findings before and after (no change).

The contours, approved-letters and e-mouth gates read only the Regular and
Italic. Neither changes, since the dial is Bold-only.

**The spacing does not change.** The S keeps its fitted bearings and every
kern, and those are absolute units. So the white at the S's extremes stays
where his bench answers put it, and the S grows inward from them.

**Checked and found clean:**
- default build byte-identical to round 464 (0 of 530);
- the Regular, Italic and Bold Italic untouched by construction (the factor is
  gated on `not pen.SHEAR and pen.S > 84`) and byte-identical in the arms;
- the kern table unchanged.

## 5. Reproduce

    cd tools/wedge_serif; source build_env.sh
    env "${ALBO_BLD_ENV[@]}" ALBO_ROM_S_W_BOLD=1.15 PYTHON_GIL=0 python3 -m outlines.build OUT --style Bold
    $VENV/bin/python instruments/bold_s_proof.py --measure today=<dir> S2=OUT
    $VENV/bin/python instruments/bold_s_proof.py PROOF today=<dir> S1=... S2=... S3=...

Proof page: https://claude.ai/artifact/YUHMkg2N7jLRGUYAsFWAUy
