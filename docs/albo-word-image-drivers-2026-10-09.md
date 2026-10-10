# What makes his common words uneven: the decomposition (2026-10-09)

Owner, 2026-10-09, after two letter-by-letter option pages (the u, round 484;
the c, round 485): *"I did not say anything about 'c' being pale. I said I need
you to figure out how to make a better word image by adjusting letters in an
intentional, evidence based way."* This is the evidence, from the same
instrument as the 2026-10-04 finding pass (`instruments/word_measure.py`;
corpus his 41 epubs, the 100 commonest word images = 225,680 tokens; the
reader's pipeline at nine sizes; six references set at the same x-height).

## The objective

A word reads as one image when its letters carry one color. The measure is a
word's UNEVENNESS: the spread of its letters' slot darkness over the word's
own darkness (`word_evenness`), against the same word in the references.
Today, Regular: the 100 commonest words run a median unevenness of 0.056
against the references' 0.045; **36% of the tokens are in a word that is less
even than in every reference.** Bold: 0.062 against 0.050; 39%.

## What drives it (Regular)

Each slot's darkness minus the references' median for the same slot,
token-weighted over the top 100 words; the share column is each letter's part
of the total deviation.

| letter | vs references | tokens | share of the deviation |
|---|---|---|---|
| o | **+7.1%** dark | 63,651 | 20.4% |
| a | **+8.3%** dark | 50,636 | 18.8% |
| f | **-14.3%** pale | 18,705 | 12.0% |
| n | -2.7% | 53,106 | 6.5% |
| i | -3.0% | 45,458 | 6.1% |
| d | -5.5% | 23,910 | 5.9% |
| h | -1.6% | 78,346 | 5.6% |
| e | +1.0% | 92,867 | 4.0% |
| T | -7.9% | 8,328 | 2.9% |
| u | -3.1% | 12,080 | 1.7% |
| c | -10.4% | 3,496 | 1.6% |

Three letters are half the problem: the a and o are dark, the f is pale, and
every other letter is within a few percent. The u (round 484) and the c
(round 485) are 1.7% and 1.6% of it -- which is why round 485's best arm moved
the top-100 gap from +0.0138 to +0.0133, 4% of the way.

## What drives it (Bold)

| letter | vs references | tokens | share |
|---|---|---|---|
| h | -5.7% | 78,346 | 13.2% |
| i | -9.1% | 44,404 | 11.8% |
| e | +4.1% | 92,867 | 11.2% |
| o | +5.5% | 63,651 | 10.2% |
| a | +6.6% | 50,636 | 9.8% |
| n | -4.8% | 53,106 | 7.4% |
| s | +5.6% | 38,012 | 6.3% |
| f | -11.8% | 17,651 | 6.1% |
| w | +9.4% | 17,590 | 4.8% |
| r | -5.3% | 26,806 | 4.2% |

The Bold's picture is the widths finding (2026-10-04 row 7): the straight
letters h i n r l widened from the Regular and read pale, the rounds and the
a did not widen and read dark. One cause, two signs.

## Where the two rounds stand against this

- Round 484 (the u 10% narrower, shipped): u-words' gap 0.0132 -> 0.0121
  Regular; the top-100 gap unchanged to three places. A real but small gain.
- Round 485 (the c, options): X moves the c-words' gap 0.0376 -> 0.0048 and
  the top-100 gap by 4%. Worth shipping for *which*, *each*, *back*; not the
  word image.

## What would move the word image

1. **The a and o in the Regular** (39% of the deviation). Both are RULED:
   the o's bowl profile (round 58) and weight (round 226, *"the roman o at
   the owner's pick"*); the a's counter and hairlines. Nothing moves there
   without a new ruling, and this table is the case for asking.
2. **The f in the Regular** (12%): its bar ends 61 units inside its advance
   where every reference's ends within 17 (finding 4.6); pale and loose.
   Not ruled.
3. **The Bold's widths** (the whole Bold table): widen b d p q a g o e s with
   the weight as the references do (medians n 1.05, b 1.09), or narrow the
   straight letters back. Not ruled.

Method for each, per `docs/albo-method.md` §0: arms by kind, each derived
from a reference number, scored on THIS table (the top-100 gap and the share
of tokens in a word less even than every reference), not on the letter alone.

## Negative results

- A letter's own number against the references' median (round 484's u band,
  round 485's c width/mouth) predicts the word image poorly when the letter is
  rare in the common words: the c is in 3 of the top 100.
- The terminal arms on the c (T, K) change its shape toward the references
  and its color by under 1%.
