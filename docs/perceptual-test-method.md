# How to run a perceptual test here

Written 2026-08-18, after a phosphor ranking came back statistically
indistinguishable from coin flips. Every requirement below is paid for by a
specific failure in that run — see
[`phosphor-ranking-2026-08-18.md`](phosphor-ranking-2026-08-18.md).

This applies to any A/B or ranking test on color, type, grain, or rendering.

## Wash out perception between stimuli

Owner requirement, 2026-08-18: *"we need to cleanse my perception better. leave
a gap, blank out the screen, have silence or low noise, etc."*

Back-to-back stimuli contaminate each other. Chromatic adaptation and
afterimages carry from one card into the judgment of the next. The last runoff
flipped straight from card A to card B and was **sold as solving** the
simultaneous-contrast problem it did not solve — it moved the contamination from
space to time, which is not the same as removing it.

- **Blank to a dark NEUTRAL field between stimuli.** Not white (it bleaches),
  and not the stimulus's own ground (it does not wash anything out).
- **Enforce a minimum gap, and keep it SHORT.** Owner ruling 2026-08-18, after
  four seconds per trial made a 123-trial session not worth doing: *"reduce
  delay to under a second."* The current pages use 900 ms between trials and
  350 ms between the two cards of one trial. It must not be skippable by a fast
  keypress, or an impatient run silently reverts to back-to-back — but a gap
  long enough to be perfect and long enough to abandon the session is worth
  nothing. Pace is a validity requirement too.
- **Nothing else moves during the gap** — no toast, no counter ticking, no
  animation. Anything changing is a second stimulus.
- **Silence.** No sound from the page, and run it in a quiet room.
- **Displace the next stimulus slightly** so an afterimage does not sit exactly
  on top of it.

## Fix the viewing conditions, and say so on the page

- **Night Shift and True Tone OFF.** Either one warps every hue judgment, and
  neither announces itself.
- Auto-brightness off, brightness fixed for the session.
- Same room light each session.
- Note fatigue: keep a session short, and discard the first few trials as
  practice.

## Carry catch trials

**Deliberately repeat identical stimuli** so the noise floor is measured rather
than assumed. This is the single most valuable thing the last run produced, and
it happened by accident: four phosphors share the ink `#FFA472` on the same
paper, so with labels hidden they were byte-identical cards. They spread a full
standard deviation of the whole ranking and straddled a tier boundary. Without
those four there would have been no way to know the result was noise.

Repeat some real pairs too, to measure judgment consistency separately from
stimulus similarity.

## Do not test a variable the page does not render

The last run's ranking was analyzed against phosphor persistence. The page never
animated decay — `paint()` set a background, a foreground and a string, and the
file contains zero `requestAnimationFrame`, zero `setInterval` and zero CSS
transitions. Persistence had no channel to the eye at all, and with labels off it
had no channel through text either. Every persistence conclusion was drawn about
a variable the subject was never shown.

Before analyzing factor X, grep the page for the code that renders X.

## Make the stimulus the real thing

Flat CSS `background`/`color` is not the page. The shipped panel goes through the
emissive ramp, antialiasing, the grain pass, the beam and the glow. A judgment
made on a flat rectangle does not transfer.

## Never ask a comparison the subject cannot make

The second design failed on this and it is the more expensive mistake. Pages
were clustered by perceptual similarity and then compared **within** cluster,
which draws almost every question from the hardest tail of the space: across the
38 distinct pages only 12% of pairs sit under dE 20, but four of the five pairs
actually shown were under dE 21. Owner, after five trials: *"these are all too
close and it is a waste of my time."*

His five calls calibrate the threshold exactly:

| pair | dE (ink, CIELAB) | verdict |
|---|---|---|
| P5 vs P55 | 1.4 | too close |
| P43 vs P31 | 9.9 | too close |
| P15 vs P34 | 18.1 | too close |
| P11 vs P22B | 20.5 | decisive |
| P43 vs P39 | 21.3 | decisive |

**Collapse before judging.** Group the candidates by complete linkage so no two
members of a group exceed dE 25, judge one representative per group (the
medoid), and let the winner carry its members. That took 38 pages to 12 real
choices. **Auto-tie anything left under dE 20** rather than asking it — a pair
the subject cannot separate is a pair whose answer carries no information, and
for a shortlist two indistinguishable pages are interchangeable anyway.

## Pairing and stopping rules

The last run's pairing algorithm chose each item's **closest-rated** opponent
from the first round. That is right for refining an order that has already
separated (Swiss late rounds) and actively wrong at the start: it manufactures
50/50 matchups and prevents separation from ever beginning. The algorithm
engineered the coin flip it then reported.

- **Spread early, refine late.** Random or deliberately-distant pairings for the
  first rounds; closest-rated only once an order exists.
- **Guard against repeat pairs**, or one judgment gets counted several times.
- **Record ties.** "Too close to call" near a boundary is exactly the
  information that sets the boundary. The last page's `skip` discarded it.
- **Budget the comparisons against the noise.** With K=32 and 5 games, an item
  with no real quality has a rating sd of 35.9 points — which is what the whole
  42-item spread measured. Either run far more comparisons, or **rank fewer
  things**: a coarse pass into three buckets, then a proper ranking inside the
  top bucket only, costs a fraction as much and resolves more.

## Check the arithmetic before believing the output

Cheap and it catches real bugs: games summed over items must equal twice the
comparison count. (It did — 210 = 210. What it exposed instead was that the
summary said "5 games each" when one item had 6 and another 4.)
