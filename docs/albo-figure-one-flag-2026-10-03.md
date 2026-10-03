# Albo: the Bold Italic 1's flag (2026-10-03)

Owner, on the taller-1 page: *"F1 bold italic serif is way too big."* F1
shipped as round 474. This answers the flag.

**Status: OPTIONS. Nothing shipped.** The dials are `ALBO_ALD_ONE_FLAG_W_700`
(the flag's weight multiplier, replacing `ONE_FLAG_W`) and
`ALBO_ALD_ONE_FLAG_X_700` (its reach), Bold Italic only
(`outlines/glyphs/figures.py`). The defaults, 1.15 and 1.0, are round 474 byte
for byte (control build).

## Why it is big

The italic 1's flag reaches a constant 150 units from the stem
(`_o1['flag']`), but its weight rides the stem. It is drawn on the bowl
profile with a floor of 0.62 S, then multiplied by `ONE_FLAG_W` 1.15
(round 218). So in the Bold Italic (S 116 against the Italic's 66.9) it is an
83-unit wedge against the Italic's 48: a big triangular block at the top-left
of a figure whose stem is 101 units.

## The arms (Bold Italic only)

| arm | `ONE_FLAG_W_700` | `ONE_FLAG_X_700` | reads |
|---|---|---|---|
| today | 1.15 | 1.0 | |
| **K1** | 0.92 | 1.0 | the flag 20% thinner |
| **K2** | 0.75 | 1.0 | 35% thinner |
| **K3** | 0.75 | 0.8 | 35% thinner and 20% shorter (reach 120) |

**Moved:** the 1, and ½ ¼ ⅓ ⅛, ¹ and ₁ built from it.

**Gates (Bold Italic, against round 474):** POOR GATES no delta. Touch 0 / 0,
no new hairs.

Proof page: https://claude.ai/artifact/J1sHur1FPyX5SxFtwTRuxy
