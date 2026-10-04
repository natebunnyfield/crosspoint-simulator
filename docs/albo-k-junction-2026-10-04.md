# Albo: where the K's leg meets its arm (2026-10-04)

Owner, on the Bold K page: *"you are attaching the bottom right stroke at the
wrong place on the upper right arm."*

**Status: Regular SHIPPED, J1** (owner *"the regular J1 R is best, bold is messy"*), as
round 478 (`docs/albo-round-478-2026-10-04.md`). The Bold K is being reworked
(`docs/albo-bold-k-2026-10-04.md`). Before the ruling: options. The dial is `ALBO_ROM_K_U` /
`ALBO_ROM_K_U_700` (`outlines/glyphs/caps_straight.py`, `K_U`): how far out
along the arm, from the stem, the leg springs (`u` in `g_K`). 0.16 has been
the value since round 36, and the default is round 477 byte for byte (control
build). The roman only; the italic K is aldine's own.

## Measured (`tools/wedge_serif/instruments/k_junction.py`)

The junction is the crotch between arm and leg. It is found as the leftmost
point of the white wedge between them, flood-filled from a seed 70% of the way
out and kept left of it so it cannot leak round the arm's tip. Every K is
rendered at a 300 px cap height.

| | right of the stem (cap) | height (cap) | along the arm |
|---|---|---|---|
| **Albo Regular, round 477** | 0.113 | 0.547 | 0.19 |
| **Albo Bold** (at 0.865 width) | 0.090 | 0.560 | 0.20 |
| Georgia / Charter / Times | 0.160 / 0.197 / 0.147 | 0.563 / 0.557 / 0.557 | 0.25 / 0.32 / 0.22 |
| Baskerville / Palatino / Pagella | 0.180 / 0.140 / 0.133 | 0.600 / 0.553 / 0.553 | 0.26 / 0.20 / 0.19 |
| regular references, median | 0.150 | 0.557 | 0.235 |
| Georgia Bold / Times Bold | 0.227 / 0.217 | 0.607 / 0.620 | 0.32 / 0.30 |

Albo's leg leaves the arm closer to the stem than the references', and in the
Bold much closer and lower.

## The arms (Regular and Bold; the Bold at the Regular's ruled 0.865 width, today's spur)

| arm | `u` | Regular: right / height / along | Bold: right / height / along |
|---|---|---|---|
| today | 0.16 | 0.113 / 0.547 / 0.19 | 0.090 / 0.560 / 0.20 |
| **J1** | 0.24 | 0.163 / 0.590 / 0.27 | 0.130 / 0.597 / 0.29 |
| **J2** | 0.32 | 0.210 / 0.630 / 0.35 | 0.167 / 0.630 / 0.37 |
| **J3** | 0.40 | 0.257 / 0.670 / 0.44 | 0.207 / 0.667 / 0.46 |

- J1 is about the regular references' median.
- J2 is about Charter's, and the bold references' place along the arm.
- The leg's angle is re-solved so its foot still lands half a stem past the
  arm's tip.
- Any J can be combined with the Bold's spur options V0–V3
  (`docs/albo-bold-k-2026-10-04.md`).

**Moved:** K and Ķ.

**Gates (Regular and Bold, against round 477):** POOR GATES no delta. Touch
0 / 0, glitch unchanged.

Proof page: https://claude.ai/artifact/UMBAR1jU5zTCrcEBMeYMDA
