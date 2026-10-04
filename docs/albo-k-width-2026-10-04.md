# Albo: a narrower K (2026-10-04)

Owner todo: *"'K' is too wide."* Part of the capitals work
(`docs/albo-capitals-audit-2026-10-04.md`).

**Status: OPTIONS. Nothing shipped.** The dials:
- the roman: `ALBO_ROM_K_W` and `ALBO_ROM_K_W_BOLD` (`outlines/build.py`,
  `CAP_K_WIDTH`), a factor on the width solver's target;
- the italic K: aldine's existing per-letter `ALBO_ALD_WD_K`.

The defaults, 1.0, are round 476 byte for byte (control build).

## Measured

K's ink width over its own H's and R's, against the six references of each
cut (`instruments/poor_trace.py`):

| cut | Albo K / H | refs K / H | Albo K / R | refs K / R |
|---|---|---|---|---|
| Regular | 0.900 | 0.936 (0.88–1.04) | **1.194** | 1.077 |
| Italic | 0.869 | 0.925 | 0.954 | 0.998 |
| Bold | 0.908 | 0.969 | 1.095 | 1.074 |
| Bold Italic | 0.853 | 0.969 | 0.976 | 1.016 |

- **Against the references, the K is already a little narrow** in every cut.
- **Against Albo's own R it is wide in the Regular**, because the R is narrow
  (0.909 of the references, `docs/albo-capitals-audit-2026-10-04.md` §3).
- The owner's report is taken as given. The options narrow the K.

## The arms (the same factor in every cut)

| arm | factor | K / H Regular | Italic | Bold | Bold Italic |
|---|---|---|---|---|---|
| today | 1.0 | 0.900 | 0.869 | 0.908 | 0.853 |
| **W1** | 0.95 | 0.858 | 0.834 | 0.869 | 0.820 |
| **W2** | 0.90 | 0.817 | 0.800 | 0.832 | 0.786 |
| **W3** | 0.85 | 0.775 | 0.766 | 0.810 | 0.752 |

**Moved:** K and Ķ.

**Gates, each arm against round 476, all four cuts:** POOR GATES no delta.
Touch 0 / 0, no new hairs.

Proof page: https://claude.ai/artifact/5fFiA2a71e2gATkzZwyeZd
