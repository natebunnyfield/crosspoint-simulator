# Albo: vital parts that go missing at the reader's sizes (2026-09-28)

Owner: *"find all instances where vital parts of a letter go missing like the
tittle of i here"* (a phone screenshot of the italic: i's without dots, e's
reading as c) and *"crossbars like f might not be thick enough at small scale"*.

**Instrument:** `tools/wedge_serif/instruments/parts_audit.py`. Every encoded
glyph, all four cuts (round 427 build), rendered as the reader's converter
renders it (`set_char_size(pt*64, pt*64, 150, 150)`, unhinted, 8-bit cut to 2
bits: top nibble >= 12/8/4 -> 3/2/1, as `etrace/e_hint_gate.py`), at every Albo
slot (8, 10, 12, 14, 16, 18 pt; 1x = the X3, 2x = the phone), against a 400 px
master. Three checks: PARTS (each separate ink part -- tittle, accent, a colon's
dot -- must have >= 4 px at level >= 2 in its OWN footprint), COUNTERS (every
counter of >= 0.04 em square must stay enclosed by level >= 2 ink), FAINT
STROKE (share of the stroke centre line landing at level <= 1). The f and t bars
were measured separately (dark rows across the bar).

**Two instrument bugs, fixed before any number below:** (1) the first parts
check read each part's footprint with a 1 px margin, and a tittle sitting just
above its stem borrowed the stem's ink -- it passed every i; (2) the counter
check counted the pinholes a union leaves at a join (the BoldItalic u had one)
as counters. And one misreading of my own: a line render showed the italic i's
dots as ABSENT at display scale; magnified, they are there, 2 x 2 px.

## Findings (basic set; about 170 accented glyphs per 400 cut also fail, below)

| what | cut | where it fails | mechanism (verified / inferred) |
|---|---|---|---|
| **i and j tittle** | Italic | under 4 dark px at every 1x size 8-16 pt and 8 pt@2x (2 x 2 px at 10 pt@2x) | the italic tittle is smaller than its stem is wide (verified at 150 px); on the phone the 2x page is also minified ~0.8 with linear filtering, which greys a 2 px dot [inferred]. The app's ink rounding (27/106) does NOT remove it (verified with InkRounding.h in a harness) |
| i, j tittle | Regular | 8 pt only (j also 12 pt) | small at the smallest slot |
| **f bar** | Regular | 0 dark rows at 8 pt, 1 at every other size, 2x included | bar = 0.8 x TH_H = 30 units; the t's is 42; Georgia 47, Charter 47, Palatino 49, Hoefler 51 (verified) |
| f bar | Bold | 1-2 rows | 54-55 units (0.50 stem; refs 0.33-0.50) -- adequate |
| **e bar / eye** | Regular, Italic | counter broken at 4 (R) / 6 (I) of 12 sizes | the bar lands at level 1: reads as c at 8 pt italic (seen) |
| g, 8, 6, 0, o, b, d, p, q | Regular, Italic | counter open at the smallest sizes | top/bottom hairlines render at level 1 |
| : ; ! ? dots | Regular, Italic | 8 pt (italic colon also 10 pt) | dots too small at the smallest slot |
| accents (acute, double acute, macron...) | all | ~170 glyphs per 400 cut, ~65 per 700 cut | the marks are hairline-thin at 1x small sizes |
| dashes - – — | Italic, BoldItalic | faint stroke > 25% | thin horizontals |
| , ; ' " quotes | Regular | faint stroke | thin tails |

Checked and found CLEAN (basic set): the Bold's i/j/punctuation dots; the Bold
Italic's i; t bars in all four cuts (1-4 dark rows); every cut's figures'
separate parts.

## Options (behind dials, default today)

- **f bar** (`ALBO_ROM_F_BAR_TH`, stems.py, default 0.8 x TH_H): F1 1.0,
  **F2 1.15 = the t's bar**, F3 1.3 (Georgia's absolute weight). Gates clean
  (touch 0, hairs 0); moves f and the f-ligatures, Regular and Bold.
- **Italic tittle** (aldine.py, pending: the file is with the italic-c agent):
  enlarge to the roman's tittle/stem ratio.
- e bar, accents, dashes, dots: to be drawn after the owner rules on the above.

Page: see the round page linked in the session.
