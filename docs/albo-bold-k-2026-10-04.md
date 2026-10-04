# Albo: the Bold K's top-right serif (2026-10-04)

Owner, on the narrower-K page: *"13.5% narrower wins for regular roman but
bold needs rework (especially top right serif)"*. The Regular shipped at 0.865
as round 477.

**Status: OPTIONS. Nothing shipped.** The dials:
- `ALBO_ROM_K_ARM_SERIF_700` (`outlines/glyphs/caps_straight.py`), the arm's
  end-wedge scale above stem 84. Today it is 0.9, `end_wedge`'s default.
- `ALBO_ROM_K_W_BOLD` (`outlines/build.py`), the width factor.

The defaults are round 477 byte for byte (control build).

## Why the serif turns into a horn

The K's arm is the family's `diagonal()` with `serif0=1`, so its top-right end
takes the diagonal wedge, 0.9 × the wedge unit `WL` by `WD`. That unit grows
with the stem. At the Bold's 116 the wedge stands up from the arm's end and
curls back into a horn, where the Regular's reads as a small spur.

## The arms (Bold only; all at the Regular's ruled 0.865 width)

| arm | width | arm serif | reads |
|---|---|---|---|
| today | 1.0 | 0.9 | |
| **V0** | 0.865 | 0.9 | narrower only, today's spur |
| **V1** | 0.865 | 0.6 | the spur about the Regular's in proportion |
| **V2** | 0.865 | 0.35 | a micro-spur |
| **V3** | 0.865 | 0 | no spur: the arm ends square |

**Moved:** K and Ķ.

**Gates (Bold, against round 477):** POOR GATES no delta. Touch 0 / 0, glitch
1 → 1 (pre-existing on Ķ).

Proof page: https://claude.ai/artifact/U6tuYio65AmgyayeZczwWF
