# Albo: the Bold K's top-right serif (2026-10-04)

Owner, on the narrower-K page: *"13.5% narrower wins for regular roman but
bold needs rework (especially top right serif)"*. The Regular shipped at 0.865
as round 477.

**Status: SHIPPED** as round 479 (`docs/albo-round-479-2026-10-04.md`): T4 with the
connection points moved onto the Regular's (owner *"T4 is closest but move the
connection points to match regular better"*). Before that: two passes of options. The first pass's V0–V3 shrank the
spur; the owner's answer was *"try again, the top right bold serif is short ...
bold is messy"*. The dials:
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

## Second pass (2026-10-04): the junction cleaned, the serif longer

Owner, on the junction page: *"try again, the top right bold serif is short.
the regular J1 R is best, bold is messy"*. The Regular shipped J1 as round
478. For the Bold, two things, both seen only at a 700 px cap:

**The mess is the leg's buried end.** It runs 0.1 CS past the arm's
centerline at over half its full width (`kick`, bury 0.1, taper 0.45), and at
the Bold the leg (0.93 S) is twice the arm (0.47 S), so its top corner stands
through the arm's upper edge: a bump at u 0.24, a notch at 0.32. The Regular's
leg is narrow enough not to. `ALBO_ROM_K_LEG_CLIP_700=1` clips the leg to the
half-plane under the arm's upper edge, so nothing of it shows above the arm.
Every arm below has it.

**The serif is short** because the arm's end carries a single wedge on its
outer side, which curls up rather than out. New dial
`ALBO_ROM_K_ARM_SERIF_IN_700`: a second wedge on the arm end's inner side, the
two-sided terminal Albo's stem tops carry (H, N, U), which reads as a flared
end rather than a curl.

All at the Regular's ruled width (0.865) and junction (u 0.24, which in the
Bold measures 0.29 of the way along the arm, the bold references' 0.30–0.32):

| arm | outer wedge | inner wedge | reads |
|---|---|---|---|
| T0 | 0.9 | none | today's spur, junction cleaned |
| T1 | 1.3 | none | the spur 45% bigger |
| T2 | 1.6 | none | the spur 80% bigger, reaching the cap line |
| T3 | 0.9 | 0.7 | two-sided: today's spur plus a smaller inner wedge, a flared end |
| T4 | 1.3 | 1.0 | two-sided, bigger |

**Moved:** K and Ķ. **Gates (Bold, against round 478):** POOR GATES no delta
on every arm. Touch 0 / 0, glitch 1 → 1 (pre-existing on Ķ).

Proof page (second pass): https://claude.ai/artifact/9D5jrYTvSSPahDeg1VTHnG
