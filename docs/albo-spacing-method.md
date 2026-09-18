# How space between letters works, and the three measures that got it wrong

Owner, 2026-09-17, after a fitting pass tightened `Vi` until it read too tight:
*"you need to have more optical space between Vi. there is a rhythm to word
images that you are ignoring. research how space between and within letters
works."*

He is right, and this doc exists because the same mistake was made three times
in one day under three different statistics. **Read this before fitting
anything.**

## The principle

**The space between letters is judged against the space inside them.** A page
reads evenly when the white column between two letters belongs to the same
family as the white inside the letters on either side of it. That is why a
spacing rule can never be "every pair gets N units of white": an `o` carries a
large round counter and wants generous flanks, an `i` carries none and wants
little, and the eye is comparing the two whites as it moves.

The corollary, and the one this project kept violating:

> **A letter's own open white belongs to the letter, not to the gap.**

A `V` splays. The triangle of paper under its right arm is part of the letter's
own image — it is what a V looks like — and it is NOT space between the V and
whatever follows. Measure the gap from the V's furthest ink and you will count
that triangle twice: once as the letter's shape and again as spacing, and then
you will "correct" it by jamming the next letter into the V.

## What each letter actually owns

Measured on the shipped italic as *extreme edge minus body edge* — how far the
letter reaches past where its ink actually stands — in em at a 300 px x-height:

| letter | own white, right | own white, left |
|---|---|---|
| o | 0.019 | 0.019 |
| m | 0.026 | 0.034 |
| u | 0.034 | 0.019 |
| n | 0.047 | 0.034 |
| l | 0.063 | 0.070 |
| i | 0.076 | 0.042 |
| A | 0.114 | 0.275 |
| r | 0.153 | 0.033 |
| X | 0.193 | 0.191 |
| **V** | **0.236** | 0.146 |
| L | 0.245 | 0.113 |
| E | 0.279 | 0.093 |
| T | 0.310 | 0.154 |

The V owns **five times** what the n owns and **twelve times** what the o owns.
Any measure that does not subtract this before comparing pairs is measuring the
alphabet's shapes, not its spacing.

## The three measures, and how each failed

### 1. Minimum white (round 198)

The narrowest point between two letters, targeted at 0.136 em — a figure
extrapolated from a regression over sixteen pairs the owner had set by hand,
not measured from the face.

**How it failed.** Minimum white cannot see an open shape at all: it reports the
single closest approach, which for `Vi` happens low down where the V's vertex
passes the i's stem. `Vi` therefore passed while reading twice too loose, and
`um` — two stems whose whole channel is narrow and even — was flagged as fine
while reading too tight. The owner named both, unprompted, from the page.

### 2. Mean gap across the band (round 199)

The average distance between the two letters over the x-height band, targeted at
the face's own `n`/`o` rhythm of 0.144 em.

**How it failed.** It reproduced the owner's three verdicts, which is why it was
believed — and then it drove `Vi` from 0.352 to 0.224 and he said the pair now
needed MORE space. The mean counts every row equally, so the V's splay enters
the average at full weight: 0.236 of the "gap" was the V's own shape. The rule
then removed real spacing to compensate for white that was never spacing.

It also produced a result that should have been read as a warning rather than a
finding: **1,317 pairs wanted 54 units or more of tightening**, ten times the
reader's 255-pair table. A rule that says almost every pair in the font is wrong
is far more likely to be a wrong rule.

### 3. Body-edge gap (round 200, the one to use)

Each letter's edge taken as a percentile of its ink over the band — where the
letter *stands* rather than where it *reaches* — and the gap measured between
those. The splay stays with the letter.

On this measure the rhythm letters land at `oo` 0.077, `no` 0.104, and `Vi`
reads 0.252 before any change: genuinely loose, but by a third of what the mean
gap claimed, and the correction is a third of the size.

## What this means for fitting

1. **Space by the letter, not by the pair.** A sidebearing is a property of the
   letter and should be proportional to the white that letter owns on that side.
   Kerns are for the exceptions a pair of shapes creates, and there should be
   tens of them, not thousands.
2. **A rule that wants to move everything is broken.** The 255-pair table is not
   just a device limit; it is a sanity bound. If a fit wants 1,317 exceptions,
   stop and question the measure.
3. **The owner's eye is the gate.** All three statistics agreed with the numbers
   and two of them disagreed with him. When a measure and his reading of the page
   diverge, the measure is what changes.

## What is in the font now

Round 200 withdraws the round-199 capital pass, which rested on measure 2, and
its `Vi` kern of −126. Two things from that round survive because he asked for
them by name and they are right on any measure:

* **J's right bearing at −74**, which fixes `Ju` (mean gap 0.226 → 0.152).
* **`um` +30**, which opens the pair he called too tight, to 0.144 exactly.

`Vi` is back at 0.352 mean gap — loose by measure 3 as well, and the next thing
to fit, but with a correction near 80 units rather than 126, and taken out of
V's own bearing rather than out of the pair.

The sixteen pairs and five bearings the owner set at his bench (round 198) are
untouched throughout.

## Round 211 — what `oo` measures in faces that are fitted, and the o's own two sides

Owner, 2026-09-18: *"adjust oo spacing until 'good' looks correct (it currently
touches)."*

**He was reading the ITALIC. The roman was already right and was not touched.**

The pair never reached zero white, so `cmp_touch` never flagged it — it is a
fitting fault, not a collision, which is what the gate is for and what it is
blind to. The instrument that answers it is the same min white, measured
against **seven faces that are fitted**: Flanker Griffo Italic, Coelacanth
Italic, Pagella Italic, Poetica, Times New Roman, Georgia, New York.

| `oo`, min white at a 300 px x-height | em |
|---|---|
| Poetica | 0.067 |
| Georgia | 0.070 |
| Pagella It | 0.071 |
| Times New Roman | 0.071 |
| Flanker Griffo It | 0.075 |
| Coelacanth It | 0.079 |
| New York | 0.081 |
| **median** | **0.071** |
| Albo ROMAN | **0.073** — inside the band, 31st tightest of 676 lowercase pairs |
| Albo ITALIC | **0.040** — 43% under, 6th tightest of 676 |

Every fitted face in reach lands `oo` between 0.067 and 0.081 em, roman and
italic alike. That band is the single most useful number this round produced:
it is narrow, it crosses five centuries and two postures, and it costs seven
font loads to re-derive.

**Why a bearing and not an `oo` kern.** His own word settles it. In `good` the
two gaps after the g were o+o 0.040 and o+d 0.048, against g+o 0.118 — nearly
three times either. A kern on `oo` fixes one of the two and leaves the next one
shut, and he would have looked at the same word again.

**The letter's two sides disagreed, and only one of them was wrong.** Measured
as deviation from the seven-face median: the o's LEFT-side family (`x+o`, 17
partners) sits **+0.012 em** — healthy. Its RIGHT-side family (`o+x`) sits
**−0.020**, and `oo`, two identical bowls approaching at the same height, is its
worst case at −0.030. So the correction is the right bearing alone: `ALD.BEARINGS['o']`
(−18, 58) → (−18, 86), held for now as `ALD_BEARING_ADJ` in `outlines/build.py`.
The right side lands at +0.006, i.e. in agreement with the letter's own left;
`oo` lands 0.068 and `od` 0.076 against medians of 0.071 and 0.077.

**The arithmetic is exact, so no ladder was run.** A bearing enters the advance
and leaves `dx = lsb - l` alone, so `rsb += D` adds exactly D units of white to
every `o?` pair and moves nothing else in the font — confirmed after the build:
the o's outline is byte-identical, 187 points, same bbox, advance 368 → 396.
Every shape, counter, contrast and detwinning gate is therefore unaffected by
construction and none was re-run.

### The negative results

* **The ROMAN needs nothing.** 0.073 against the 0.071 median. Its `oo` was left
  exactly as it was and the roman build is bit-identical — 0 glyph metric
  changes. Do not "fix" it.
* **The ratio agreed with itself and was useless.** `oo` ÷ mean(`on`,`no`) is
  0.49 in the roman and 0.51 in the italic — the two styles look equally wrong
  on a ratio, and one of them is correct. Only the ABSOLUTE white separated
  them. The ratio misleads here because Albo's `n` stands well inside its own
  serifs (roman: the serif reaches x=49, the stem stands at ~119), so `on` and
  `nn` measure a different thing from what they measure in the references.
  `nn`'s minimum is its FOOT SERIFS (105 units) while its real channel is 226.
* **`ov ow oy ox` are still short** (−0.035 to −0.016) and are NOT the o's fault:
  `vo wo yo` all sit at or above the reference. That is the v/w/y/x LEFT side.
  Left alone.
* **`o` before a mark opened 28 units with everything else**, and was already
  correct before — the marks carry deliberately generous bearings (round 97b,
  *"punctuation needs to breathe"*), which had been silently paying for the o's
  tight right side. On min white it now reads loose (`o.` +0.046, `o,` +0.089
  against the reference median), but min white cannot see a mark sitting low and
  open — the doc above is about exactly this failure — so it was judged by eye
  at the phone's real 54 px em and reads airier rather than loose. Deliberately
  NOT compensated; six italic-only pair exceptions is a bigger change than the
  fault. If it is ever revisited, the numbers are here.
* **`oc` and `or` are round-202 bench values of HIS and were not overruled.**
  The bearing would have carried them to 0.114 and 0.136 against medians of
  0.074 and 0.075, so their kerns are halved 36 → 18, ITALIC ONLY, landing them
  0.096 and 0.118 — ten units from his own figures, half a STEP, about half a
  pixel at 13 pt on the 2x app. The gate on that halving reads `ALD.ON` rather
  than re-reading the environment, so it cannot disagree with the predicate
  `fit()` uses to choose `fit_aldine`.
* **No kern pair was added.** The single-glyph table is 79 entries before and
  after, against the reader's 255 cap.

## The larger finding, which measure 3 does not remove

Albo's italic counters measure **145 units against Flanker Griffo's 226** at the
same x-height, while its absolute inter-letter white is **127 against Flanker's
167** — the second tightest of the five reference italics. The letters are
narrow relative to their fitting. No table can fix that, and it is the reason
every spacing rule tried so far wants to close gaps that are not really open.
That is a drawing decision.
