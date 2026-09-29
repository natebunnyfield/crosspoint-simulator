# Albo family bench, 2026-09-28

**Status: arm B SHIPPED as round 431 (owner, 2026-09-28: "B recency + classes").** Measured on built fonts at commit 2ea3ea7 plus the working-tree edits named below. The zero is round 430 (`bench/fonts-2026-09-28-r430`, with its `spacing_b2.json` kept beside it).

## Why the bench

He flagged ro, re, ha and um as poorly kerned (screenshot, 2026-09-28). Four readings of those pairs moved the B2 fit by 1–4 units, so he chose "bench the families". That is 19 roman pairs: r before round letters (ro re rc rd ra rg), letters before a (ha na ma la ta ea), and the m/n joins (um un nm mm am em im). Two italic repeats (os, ry) were added as a consistency check. Page: https://claude.ai/artifact/ECsEvaAXmFwBmPzgY73dKF, key `bench/family-2026-09-28.key.json`.

## His answers (delta from round 430's white, units)

ro −19 · re −13 · rc +2 · rd −20 · ra −27 · rg −3 · ha −6 · na −12 · ma +8 · la +11 · ta −15 · ea +6 · um −31 · un −16 · nm −5 · mm +5 · am +10 · em −8 · im +9 · italic os +11 · italic ry −1.

um is now the most consistent reading in the set: −49 / −55 / −49 on the fit's zero, over three sittings.

## Findings

1. **Equal-weight refit barely moves (verified).** ro −3, ra −2, um −4. Two causes:
   - **His 09-20 bench readings disagree with today's.** On the fit's zero: ra +17 then vs −15 now, na +29 vs −12, un +14 vs −14, rd +28 vs +8. The mean sits where neither reading is.
   - **The r readings split by what follows it.** Before a round letter he wants the r tighter (ra −15, rs −30, ro −7, re −6). Before an ascender stem he wants it looser (rh +27, rt +25, rb +11, rk +10). B2 has one number for r's right side, so the two halves cancel.
2. **Regularization is not the cause (verified).** The r-family residuals are identical at every (ALPHA_ID, ALPHA_F) from (1, 30) to (0.1, 0.3). Held-out error only worsens as alpha drops: 8.84 → 9.57.
3. **Interaction features did not help (verified; negative result).** Three were tried: the left glyph's lower-right recess × the right glyph's round left, × stem-ness, and the recess alone. Residuals were unchanged to the unit and held-out error was 8.84 → 8.90.
4. **Side-class terms do help, on the roman (verified).** One ridge term per (left glyph, right glyph's left-side class) and one per (left glyph's right-side class, right glyph). Held-out error at alpha 3, equal-weight targets:
   - roman 8.69 → 8.46;
   - italic 8.81 → 9.06 (worse), so the terms are roman only (`ALBO_B2_CLASS_STYLES`, default `roman`).
   - The classes are hand-assigned (`b2_fit.LCLS` / `RCLS`).
   - um is out of reach of any class: m and n share a left-side class.
5. **The ingest misread the italic ry (verified; bug, fixed).** The bbox conversion gave +99 on the fit's zero for a −1 answer. The italic y's tail travelled 106 units in round 409's resize, and a bbox white reads that as spacing. The fix is to convert through the page's own spacing tables, as target = table value + delta (`active_ingest.table_white`).
   - This agrees with the bbox conversion to the unit on all 17 roman rows that take it.
   - The italic ry becomes 9 and os 18.
   - Held pairs and out-of-scope pairs keep the bbox conversion; each row records `conv`.
   - **Not yet done:** italic rows from s3–s6 with bbox jumps over 25 (ys jo ja up wr ps Fr ws) may carry the same error. Their zeros' tables were not kept beside the fonts, but can be recovered from git.

## Rulings and changes this round

- **Recency (owner 2026-09-28: "weight more recent measurements much heavier").** In `b2_fit.combine`:
  - Each reading weighs 0.5^(age / 1 day), counted from his newest reading.
  - A pair's fit weight is 1 + 3 × its newest reading's recency.
  - `ALBO_B2_RECENCY=0` reproduces the equal-weight refit byte for byte (checked).
- **rd released from the roman HOLD and its round-384 hand kern (+20) dropped under B2.** He read rd again. Both arms land rd at −23 / −24 against his −20.
- **Holds re-measured** so every held pair keeps round 430's white exactly in both arms (verified, 0 drift).

## The two arms (moves from round 430, measured on built fonts)

| pair | his | A recency | B recency + classes |
|---|---|---|---|
| ro | −19 | −8 | −14 |
| re | −13 | −6 | −12 |
| ra | −27 | −8 | −21 |
| rd | −20 | −23 | −24 |
| ta | −15 | −6 | −10 |
| na | −12 | −4 | −8 |
| um | −31 | −12 | −14 |
| un | −16 | −10 | −14 |
| ea | +6 | −3 | +7 |
| am | +10 | +2 | +5 |

- Pairs moved by 5 or more: A 71 and B 172, of about 500 roman pairs; italic 7 in both.
- Tables: `outlines/_arm_A.json` and `_arm_B.json`.
- Not yet run on either arm: fences, clearance and the gates. These are run on the chosen arm before shipping.
