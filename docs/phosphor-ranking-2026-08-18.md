# Phosphor runoff, 2026-08-18 — RESULT VOID

**The result of this run is not usable.** It is kept because the failure is
worth more than the ranking would have been: it produced a measured noise floor
and a list of method requirements, now written up in
[`perceptual-test-method.md`](perceptual-test-method.md).

An earlier version of this file drew four conclusions from the run. All four are
retracted below. Do not cite this document for a preference about phosphors.

## What was run

All 42 phosphor presets, A/B runoff on the tier page: one lit card at a time on
pure black, flipping between two contenders. 105 comparisons, Elo K=32 from
1500. Games: 40 items at 5, one at 6 (P12), one at 4 (P7); 210 games against 105
comparisons, which balances.

**Labels were off** for the whole run (owner confirmed). So the only thing on
screen was a rectangle of ink-on-paper and a sentence. No P-number, no name, no
persistence figure.

## Why the result is void

Simulate an item with **no quality at all** — five games, every outcome a coin
flip, K=32 with near-even opponents:

| | |
|---|---|
| simulated sd of a truly average item | **35.9 points** |
| observed sd across the 42 phosphors | **36.0 points** |

Observed variance = signal + noise. That leaves a signal sd of about **2.6
points against 36 points of noise**. The full 1420-1580 spread is what chance
produces on its own.

Confirmed independently by catch trials that happened by accident. Four
phosphors share the ink `#FFA472` on paper `#190800`, so with labels off they
were **byte-identical cards**:

| | rating | tier assigned |
|---|---|---|
| P33 Radar Orange Longest | 1580 | S |
| P12 Orange Persistent | 1565 | S |
| P19 Radar Orange | 1548 | A |
| P38 Radar Amber | 1545 | A |

Four identical stimuli spread 35 points — a full standard deviation of the whole
ranking — and straddled a tier boundary. The other identical pair (`#00FF97` on
`#00190A`: P22G, P46) spread 1 point. Two catch groups is a thin estimate, but
the four-card group is decisive on its own.

The gap between the top band (1545-1580) and the next (1500-1517) is 28 points,
which is inside that noise.

## The cause was the pairing algorithm

`makePair()` gave every item its **closest-rated** opponent from the first round.
Justified in the code comment as "a matchup you can call instantly teaches the
ranking nothing" — true when refining an order that has already separated, wrong
at the start. It manufactures 50/50 matchups and stops separation from ever
beginning. The algorithm engineered the coin flip it then reported.

Corroboration: the four identical cards spread 35 points where an unconstrained
random walk predicts 72. Less than chance, because closest-rated pairing
contracts the ratings.

## The four retracted claims

1. **"Contrast is not what was being judged."** The statistics were sound —
   Spearman rho(rating, contrast) = +0.086, permutation p = 0.59, and the tie
   structure caps a perfect predictor at |rho| = 0.987 so ties were not masking
   anything. But the claim is **empty**: if the ranking is noise, nothing
   predicts it, and a null says nothing about preference.
2. **"Persistence is what was being judged."** Retracted outright, on two
   independent grounds. Statistically, rho = +0.153, p = 0.34 — never
   significant; the supporting figure originally cited was a comparison of tier
   MEANS, which is a much weaker instrument and was the one that happened to
   agree. Mechanically, worse: **the page never rendered decay.** `paint()` set
   a background, a foreground and a string; the file contains no
   `requestAnimationFrame`, no `setInterval`, no CSS transition. With labels off
   there was not even a text channel. The variable was never shown.
3. **"Hue drives it — long-lived orange on top, saturated blue at the bottom."**
   Never established. It rested on the same tier means, and warm hue is
   entangled with trail in this set (rho = +0.317, p = 0.041), so the two could
   not have been separated even with real data.
4. **"P33/P12/P19/P38 prove that rows sharing a page can be told apart by their
   decay."** Exactly backwards. Those four were identical cards with the
   distinguishing variable not rendered; their scatter is the noise measurement
   above, i.e. evidence *against* the reading. The 2026-08-17 ruling that two
   rows may share a page if they decay differently still stands on its own
   merits — it simply gets no support from here.

## Analysis errors, separately from the data

- **Circular.** The tier split (10/15/25/25/15/10) was invented for the page,
  applied to the ratings, and then tier membership was used as evidence *about*
  the ratings. Tier means are not independent data.
- **Post-hoc cut.** "Warm" as hue <= 60 deg or >= 340 deg was chosen after
  seeing the data.
- **Half the stimulus never tested.** Ink hue, saturation, luminance and
  contrast were analyzed; paper tone never was.
- Two factual slips in the first write-up: "five strata" (there are 8 bands: 1,
  1, 6, 12, 1, 14, 5, 2) and "5 games each except P7" (P12 had 6).

## Not a removal list — and now not a list of anything

Owner ruling 2026-08-17 ships the whole JEDEC registry. Nothing here authorizes
dropping a row, and after the above nothing here authorizes reordering one
either.
