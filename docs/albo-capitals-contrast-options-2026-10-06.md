# Albo: the Bold capitals' light strokes, as options (2026-10-06)

Owner todo (2026-10-03): *"make capitals the right size and shape and
contrast"*. This is fix 1 of `docs/albo-capitals-audit-2026-10-04.md`: the bold
capitals' contrast.

**Status: SHIPPED, C1** (owner *"C1 wins"*), as round 482
(`docs/albo-round-482-2026-10-07.md`). Before the ruling: options; 1.0 on
every dial is round 481 byte for byte.

Proof page: https://claude.ai/artifact/QcF1PNp1nAJKYncZdtAoHS (drawn by
`tools/wedge_serif/instruments/caps_contrast_proof.py`).

## The dials (all four act ABOVE STEM 84 only)

| env | where | what it scales |
|---|---|---|
| `ALBO_CAP_BAR_BOLD` | `caps_straight.py` (`CAP_BAR`), and `aldine.py` `_IBAR` | the bars: A E F G H L Z in the B; A G H L Z (and E F through caps_straight) in the Z. The T keeps `pen.CAP_BAR` and its ruled `T_BAR_K` |
| `ALBO_CAP_THIN_BOLD` | `caps_straight.pw` (mult 0.72 only), and `aldine.cdiag` (the nib's thin) | the thin diagonals: A M V W in the B; every `cdiag` in the Z. The roman X (`X_THIN`), Y (`Y_THIN`, ruled) and K arm (round 480, ruled) are not 0.72 and are left alone |
| `ALBO_CAP_CON_BOLD` | `caps_straight.cap_ring` / `cap_arc` | `con` on the B's O, Q and C bowls. `half_bowl` (B D P R) has no contrast lever |
| `ALBO_CAP_NIB_BOLD` | `aldine.py` `CAP_CON` | the Z's nib ratio (2.20 x this). The thick is held, so only the thins of CURVED strokes lighten; a straight stroke has one direction and does not move |

The italic E's middle-bar microserif now reads `_CS.CAP_BAR` rather than
`pen.CAP_BAR`, so it stays seated on the bar when the bar thins. Identical at
1.0.

## The arms and what they measure

Contrast is the audit's measure: per capital, Albo's p90/p10 chamfer-ridge
thickness over the six references' median, then the median over the 26.
Measured with `instruments/poor_trace.measure` against the reference values in
`bench/cap-audit-2026-10-04/` (the baseline re-measures to the audit's 0.554 and
0.484, so the instrument agrees). The lowercase targets are 0.86 (B) and 0.76 (Z).

| arm | bars | thin | bowl con | nib | B contrast | B thin | Z contrast | Z thin |
|---|---|---|---|---|---|---|---|---|
| today (481) | 1.00 | 1.00 | 1.0 | 1.0 | 0.550 | 1.85 | 0.484 | 2.06 |
| **C1** | 0.85 | 0.85 | 1.0 | 1.2 | 0.581 | 1.56 | 0.553 | 1.97 |
| **C2** | 0.70 | 0.70 | 1.0 | 1.5 | 0.667 | 1.49 | 0.625 | 1.71 |
| **C3** | 0.70 | 0.70 | 1.6 | 1.5 | 0.676 | 1.47 | 0.625 | 1.71 |
| **C4** | 0.55 | 0.55 | 1.8 | 1.8 | 0.800 | 1.23 | 0.699 | 1.49 |

In the Z, C3 is the same font as C2: the bowl `con` dial only reaches the
roman's ring and arc, and the Z's bowls are already on the nib dial.

## Gates (`instruments/poor_gates.sh base arm "Bold BoldItalic"`), every arm

POOR GATES: no delta in all four. Hairs (letters and full sweep): none new.
Touch: 0 -> 0 in both cuts. Counter dents: 1 -> 1. Glitch on the moved
glyphs: the same count of findings before and after (pre-existing). Contour
census unchanged. Approved letters unchanged. The e mouth gate ok.
`kern_classes`, `clearance.py` and `mark_crowd.py` were not run: this is an
options round and nothing ships.

## Checked and CLEAN

- **Defaults byte-identical in all four cuts**: `cmp_outlines.py` reports 0 of
  530 glyph outlines differ for R, I, B and Z, against a build of HEAD (c441b25)
  in a clean worktree.
- **The R and I cannot move**: every dial is gated on `S > 84.0`, and the 400s
  are stem 66.9. Checked by the identity build above, not by reading.
- `docs/albo-STATE.md` regenerated: only the dials' line numbers moved (the new
  dials are numeric, and the STATE table lists letter arms).

## What these arms do NOT reach (measured on the arms, not inferred)

- **I J L U** (B 2.35-3.34 thin): no hairline. Their p10 is a stem or a wedge,
  as the audit predicted. Untouched.
- **The Z's N** stays at 0.33 contrast in every arm: its light strokes are
  straight stems (`cstem_i`), which neither the nib ratio nor the diagonal's
  thin reaches. The Z's R, K, X, Y also do not move.
- **The Z's V and W** move little (0.47 -> 0.51 and 0.53 -> 0.57 at C2). The
  nib's thin is only part of a diagonal's width at those angles.
- **B D P R bowls**: no lever.
- **The T**: kept on its ruled bar.

A second pass for any of these is a new dial, not more of these four.
