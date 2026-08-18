# Phosphor shortlist runoff, 2026-08-18 — VALID

Second attempt, after the first was
[voided as noise](phosphor-ranking-2026-08-18.md). Method requirements it was
built to satisfy: [`perceptual-test-method.md`](perceptual-test-method.md).

## What was run

The 42 presets paint 38 distinct pages. Those were collapsed by **complete
linkage in CIELAB at dE 25** — no two members of a group further apart than that
— leaving **12 genuinely different choices**, each represented by its group
medoid. Full round robin, 66 pairs, of which **3 were auto-tied** for sitting
under dE 20 (the range the owner had already called unanswerable) and never
shown. **63 comparisons, all answered.**

One lit card at a time on black, 900 ms blank to a dark neutral between trials
and 350 ms between the two cards of a pair, card displaced +/-12 px each
showing, the shipped grain pass on the card, labels hidden.

## Result

| # | page | score | carries |
|---|---|---|---|
| 1 | **P3 Amber** `#FFB000` on `#1A1000` | 10/11 | P28 |
| 2 | **P12/P19/P33/P38 Orange Persistent** `#FFA472` on `#190800` | 10/11 | P26 |
| 3 | **P22G/P46 TV Green** `#00FF97` on `#00190A` | 9/11 | P34 |
| 4 | P4 Gray `#C9E7FF` on `#14181A` | 7/11 | P18, P6, P23, P40, P45 |
| 5 | P7 Cascade `#C4C6FF` on `#000327` | 6/11 | P10, P35 |
| 6 | P11 Blue `#8B92FF` on `#00061A` | 5.5/11 | — |
| 7 | P55 Blue Projector `#BCA9FF` on `#060019` | 5/11 | P5, P16, P14, P17, P22B, P47 |
| 8 | P53 Projector Green `#00FF63` on `#001904` | 4.5/11 | P2, P43, P31 |
| 9 | P15 Blue-Green Fastest `#00FFCA` on `#001912` | 3.5/11 | P24 |
| 10 | P25 Orange Lead `#FF9C9B` on `#190101` | 3/11 | P13, P27, P21, P56 |
| 11 | P22R Red `#FF6F6C` on `#1A0300` | 2/11 | — |
| 12 | P1 Green `#33FF33` on `#001A00` | 0.5/11 | P39, P20 |

## Why this one is believable, unlike the last

**Transitivity.** 11 circular triads (A>B, B>C, C>A) against a maximum of 70 for
n=12. Kendall's coefficient of consistency **zeta = 0.843**. Coin-flip judging
produces 45.5 on average; **not one of 20,000 simulated random runs scored 11 or
fewer** (p = 0.00005). The calls were consistent, and consistency is exactly
what the first run could not demonstrate.

**Separation.** With 11 games each, a coin-flip item has a standard deviation of
1.66 wins, so gaps under about 3.3 wins are not separable. The top three
(10, 10, 9) sit clear of everything from 7 down. #1 against #4 is 1.8 sd —
borderline; #1 against #5 is 2.4 sd — real.

**Every question was answerable.** The design constraint that fixed the second
attempt: no pair under dE 20 was ever shown, and the owner used the "too close"
button rarely enough that a full order emerged.

## What it does NOT correlate with — and this time the null means something

Because the judging is demonstrably consistent, there IS signal here. It simply
is not any single colorimetric axis:

| | Spearman rho | p |
|---|---|---|
| contrast ratio | +0.172 | 0.59 |
| ink luminance | +0.123 | 0.70 |
| paper luminance | +0.004 | 0.996 |
| ink saturation | -0.041 | 0.90 |
| warmth (hue distance from 30 deg) | +0.004 | 0.996 |

Warmth in particular fails despite amber and orange finishing first and second,
because the other warm pages finish 10th (P25 salmon) and 11th (P22R red). The
preference is for a specific amber-orange at a specific chroma, not for warm
pages. No reduction to a single number reproduces this ordering; treat the
ranking itself as the finding.

**The canonical CRT green came last.** P1 `#33FF33` — the phosphor everyone
means when they say "CRT" — finished 12th of 12 at 0.5/11, and it carries P39
and P20 with it. Worth stating plainly because it is the opposite of what a
default would have assumed.

## Diversity of the top

Minimum pairwise separation among the top six is **dE 22.5**, between P4 Gray
and P7 Cascade — two whitish pages that are near-neighbours by the owner's own
threshold. Taking the top **five with P7 dropped in favour of P11 Blue** raises
the minimum separation to **dE 42.3** while costing half a win of score:

`P3 Amber` · `P12/P19/P33/P38 Orange` · `P22G/P46 TV Green` · `P4 Gray` · `P11 Blue`

Two warms, a green, a white and a blue, every pair clearly distinct.

## Still open: which PRESET ships for a winning PAGE

The runoff decided pages, not presets, because labels were hidden and decay was
never rendered. Two winners are painted by more than one preset, differing only
in trail:

- **Orange `#FFA472`** — P12 (693 ms), P19 (1095 ms), P33 (2828 ms), P38
  (1095 ms), plus P26 absorbed at 1095 ms.
- **Mint `#00FF97`** — P22G (63 ms) and P46 (17 ms), plus P34 absorbed.

That is a persistence question and needs a test that actually animates decay —
which no page in this project has done yet.

## Not a removal list

Owner ruling 2026-08-17 ships the whole JEDEC registry. A shortlist promotes;
it does not delete. Everything outside the top stays reachable in the full
picker.
