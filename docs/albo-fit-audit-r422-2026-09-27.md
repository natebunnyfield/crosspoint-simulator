# Albo fit audit on round 422 (2026-09-27)

Owner, after the poor-characters list closed: *"Fresh fit audit"*. The fit
audit (`docs/albo-fit-audit-2026-09-26.md`, F >= 2.0 flags) re-run on round
422 (`5db853d`), all four cuts, against the round-409 scores the
poor-characters list was drawn from. Spacing axis regenerated from HEAD
(`fit_audit/spacing.py --rev HEAD`). Reference-face geometry and legibility
reused from the 2026-09-26 run (unchanged faces). One build scored
(`instruments/poor_harness/score.sh`), not the 16-build validation set, which
tests the metric and was not re-run.

Every number is from `fit-r422.json` / `fit-r409.json` (session scratchpad);
confidence: measured.

## 1. The list (F >= 1.8, was = round 409)

| cut | flagged |
|---|---|
| Regular | e 4.45 (stroke; was 4.32) · Q 3.96 (width) · I 3.84 (stroke) · M 3.83 (spacing) · j 3.51 (spacing; was 3.70) · S 2.73 (spacing) · J 2.72 · t 2.65 (spacing; was 2.77) · 6 2.51 · l 2.25 · k 2.25 · a 2.15 (spacing) · 8 2.05 · y 1.90 (was 3.15) |
| Italic | F 5.23 (stroke; was 5.04) · g 4.21 (vertical; was 4.71) · j 2.83 (spacing; was 4.17) · **2 2.36 (stroke -3.3; was 1.78)** · J 2.23 · I 2.09 · **r 2.08 (vertical, top +3.9; was 0.00)** |
| Bold | y 4.27 (stroke; was 4.04) · e 4.09 · I 4.08 · k 3.10 · Q 3.08 · 6 2.67 · 8 2.66 · K 2.49 · z 2.24 · r 2.21 · L 2.08 · H 1.93 |
| BoldItalic | g 4.11 (was 5.67) · r 3.63 (stroke) · q 2.17 (bearings) · 1 2.11 · **2 2.09 (stroke -2.6; was 0.15)** · V 1.92 · 7 1.91 |

## 2. What rounds 410-422 did to the letters they touched

Regular t 2.77 -> 2.65 (still led by spacing: B2 not refit for the new t),
j 3.70 -> 3.51 (same), s 2.64 -> 0.55, y 3.15 -> 1.90. Italic t 2.60 -> 1.07,
j 4.17 -> 2.83, a 0.38 -> 0.00. Bold t 3.12 -> 0.91, N 2.52 -> 0.54,
T 1.89 -> 0.62; Bold y 4.04 -> 4.27 (round 412's sweep, ruled). BoldItalic
y 2.32 -> 1.79, g 5.67 -> 4.11.

## 3. New flags since round 409, read

- **Italic 2 and BoldItalic 2, stroke -3.3 / -2.6 sigma** -- round 410's
  pen-drawn 2d (owner pick) measures as the lightest figure of its family
  (col1x -0.66 / -1.18, bot -1.6 / -2.5). The one new flag that is a
  DRAWING and not a ruling or a statistic. Candidate.
- **Italic r, vertical top +3.9** -- round 417's `sho` arm puts the r's top
  above its family's line. That is the owner's ruled drawing (417/418);
  recorded, not proposed.
- **Bold L 1.78 -> 2.08, H 1.65 -> 1.93, r 2.00 -> 2.21 (all on `thin`)** --
  none of the three was redrawn since round 409 (checked: `cmp_outlines.py` round-409 Bold vs round-422 Bold moves 28 glyphs -- the N, T, j, s, t, y families -- and not L, H or r); their
  `thin` z rose 0.2-0.3 because the family's own statistics moved when round
  415 thinned the Bold N. Drift of a relative metric, not a defect. NOT
  candidates.

## 4. Excluded, and why (unchanged from the 2026-09-26 list)

e (rounds 395/400), Q (round 225 tail), I l J (wedge serifs), k K (the ruled
kick), the approved g's, S (rounds 225/231), M and a and the Regular t / j
(spacing only: B2, his bench), z Bold (a serif tip), Bold y (round 412
sweep), Italic F (round 416's bars; its remaining flag is the cap stem's
p50 and B2 kerns, section 2 of the poor-characters doc), BoldItalic r (418),
q and V (ruled as is today), figures 1 6 7 8 (unruled but not new).

## 5. Checked and found CLEAN

Every letter rounds 420-422 moved (t j a in their cuts, the p/q untouched):
no new flag above 1.8 except as listed; Italic a F 0.00, BoldItalic a 0.00,
BoldItalic t 0.17, BoldItalic j 0.03.

## Next

The italic 2 (both cuts), drawn by the main session as weight arms on the
2d construction, to the owner as an options page.
