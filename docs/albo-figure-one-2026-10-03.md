# Albo: a taller figure 1 (2026-10-03)

Owner todo: *"1 needs to be taller, visually balanced with other numbers"*.

**Status: OPTIONS. Nothing shipped.** The dial is `ALBO_FIG_1_TOP`
(`tools/wedge_serif/latin.py`, `FIG_BOX['1']`): the 1's box top, as a fraction
of the cap height. 0.64 (the default) is round 473 byte for byte (control
build).

## What was short

Albo's figures are old-style: 0 1 2 sit in the x-height band, 6 and 8 rise,
and 3 4 5 7 9 descend (`latin.FIG_BOX`, the references' medians). Measured
tops (ink, units):

| cut | x | 1 | 7 | 5 | 0 | 2 |
|---|---|---|---|---|---|---|
| Regular | 451 | **433** | 447 | 450 | 460 | 470 |
| Italic | 457 | **433** | 453 | 452 | 460 | 478 |
| Bold | 461 | **433** | 447 | 466 | 460 | 488 |
| Bold Italic | 470 | **433** | 466 | 466 | 460 | 493 |

- **Why it is short.** The 1's flat top stops ON its box line (0.64 C). The 5
  and 7 share that line but their top strokes stand about 15 units over it.
  The round 0 and 2 overshoot further.
- **The result.** The 1 is the shortest small figure in every cut, under the
  x-height itself, and the gap grows with the weight.
- **The reference.** Georgia's old-style 1 is the height of its 0 and 2 (1105
  each, x 986).

## The arms (the same raise in every cut)

| arm | `ALBO_FIG_1_TOP` | the 1's top | reads |
|---|---|---|---|
| today | 0.64 | 433 | |
| **F1** | 0.6622 | 448 | the flat figures' line (the Regular's 5 and 7) |
| **F2** | 0.6800 | 460 | the 0's top, in every cut |
| **F3** | 0.6949 | 470 | the Regular's 2 |

**Moved:** the 1, and the glyphs built from it: ½ ¼ ⅓ ⅛, ¹ and ₁.

**Gates, each arm against round 473, all four cuts:** POOR GATES no delta.
Touch 0 / 0, no new hairs.

Proof page: https://claude.ai/artifact/XQypudj49cbhdgQXuarRvF
