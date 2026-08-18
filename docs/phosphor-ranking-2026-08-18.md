# Phosphor runoff, 2026-08-18

Owner ranking of all 42 phosphor presets, collected with the A/B runoff page
(one lit card at a time on pure black; sequential flip, never two lit at once).
Elo K=32 from 1500, 105 comparisons, 5 games each except P7 Cascade at 4.

Method note that matters for reading this: the page is black and the chrome is
neutral gray **on purpose**. Owner 2026-08-18 — 42 colored cards on one screen
means every card is judged against its neighbors (simultaneous contrast), the
eye white-balances to the average of the field (chromatic adaptation), and the
raised field luminance closes the pupil. One lit card against black is the
actual viewing condition of a CRT in a dark room.

## The ranking as given

| Tier | Phosphors |
|---|---|
| S | P33 Radar Orange Longest, P12 Orange Persistent, P6 White TV, P18 White Soft |
| A | P26 Radar Orange Long, P19 Radar Orange, P28 Yellow, P38 Radar Amber, P53 Projector Green, P2 Blue-Green Long |
| B | P3 Amber, P4 Gray, P10 Dark Trace, P15 Blue-Green Fastest, P22G TV Green, P24 VFD Green, P56 Red Projector, P40 White Long, P34 Green Longest, P46 Green Fastest, P7 Cascade |
| C | P55 Blue Projector, P47 Blue Fast, P5 Blue Fastest, P1 Green, P11 Blue, P14 Cascade Orange, P16 Violet, P17 Cascade Yellow, P21 Radar Red, P25 Orange Lead, P35 Blue-White |
| D | P31 Green Fast, P43 Terbium Green, P23 White Warm, P39 Green Long, P13 Red-Orange, P22R Red |
| F | P27 Red-Orange Deep, P45 White, P22B Blue TV, P20 Yellow-Green Long |

## What the tiers actually resolve — READ THIS BEFORE USING THEM

**Six tiers is over-precise for 105 comparisons.** With 5 games each, Elo is
close to a win count, and the ratings collapse into five strata:

| Rating band | Count | Wins |
|---|---|---|
| 1545-1580 | 8 | 4-5 |
| 1500-1517 | 13 | 3 |
| 1483-1487 | 14 | 2 |
| 1452 | 5 | 1 |
| 1420-1423 | 2 | 0 |

The tier cuts are percentile cuts on the rank order, so **two of the five
boundaries fall inside a tie group**. P2 Blue-Green Long (A) and P3 Amber (B)
both sit at 1516 — that split is array order, not a judgment. Same for the
C|D boundary at 1484/1483.

What IS resolved: a **top group of about 8**, a large middle of about 27, and a
**bottom group of about 7**. Treat S+A as one finding and D+F as one finding;
do not act on B-versus-C.

## What the ranking correlates with

Measured on the shipped dark-mode tones (`presetPalette(preset, true)`):

| Tier | n | contrast | ink luminance | ink hue | ink sat | trail |
|---|---|---|---|---|---|---|
| S | 4 | 11.8:1 | 0.607 | 117° | 0.39 | 918 ms |
| A | 6 | 11.5:1 | 0.588 | 65° | 0.76 | 788 ms |
| B | 11 | 13.0:1 | 0.686 | 159° | 0.65 | 826 ms |
| C | 11 | 10.3:1 | 0.500 | 192° | 0.40 | 392 ms |
| D | 6 | 11.8:1 | 0.644 | 162° | 0.64 | 349 ms |
| F | 4 | 11.8:1 | 0.624 | 219° | 0.50 | 312 ms |

**Contrast is not the driver.** S and F have the *same* mean contrast, 11.8:1.
The highest-contrast phosphor in the set, P23 White Warm at 15.8:1, landed in D;
the lowest, P22R Red at 7.3:1, also landed in D. Whatever is being judged here,
it is not legibility headroom.

**Persistence is.** S/A/B average 918/788/826 ms of trail; C/D/F average
392/349/312. The top half carries roughly 2.4x the afterglow of the bottom half.
That is the single cleanest signal in the data.

**Hue is the other one.** The top is orange and amber (14-47°) plus the two soft
blue-whites; the bottom is saturated blue (P22B, 239°), cyan-white (P45, 193°),
deep red (P27, 354°) and chartreuse (P20, 91°). Saturated primaries lose;
long-persistence orange wins.

**The canonical phosphors did not win.** P1 Green — the phosphor everyone means
when they say "CRT" — is C. P3 Amber is B. Both were beaten by their obscure
radar-tube cousins, which paint a nearly identical page and simply hold it
longer.

**The identical-page rows separated by decay, and that held up.** P33, P12, P19
and P38 all paint the exact same ink (#FFA472) on the same paper; the ONLY thing
distinguishing them is trail. They landed S, S, A, A — clustered, and led by
P33, the longest tail in the set at 2828 ms. That is direct evidence for the
2026-08-17 ruling that two palette rows may paint the same page if they decay
differently: with the glow running, the owner can in fact tell them apart, and
ranked them in roughly trail order. P13 and P27 (both #FF9BA5) landed D and F —
adjacent, same result.

## Not a removal list

Owner ruling 2026-08-17, "be sure to include all possible phosphors": the whole
JEDEC registry ships. A low tier here is a preference, not a defect, and nothing
in this document authorizes dropping a row. See the standing rule on never
silently removing user-facing capability.
