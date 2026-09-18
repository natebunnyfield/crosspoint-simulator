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

## Round 216 — the figures, and the measure-1 failure a third time

Owner, 2026-09-18: *"correct numeral spacing."*

**Again the ITALIC. The roman's figures were already right** — median body-edge
gap 0.108 em against Georgia's 0.106 and Pagella's 0.129 — and are byte-identical
after this round, outlines and metrics.

### The fault was mechanical, and it is this document's own subject

`outlines/build.py`'s `fit` gives a figure its bearing off `min(xs_all)` /
`max(xs_all)` — where the glyph *reaches*. Measured with
`tools/wedge_serif/cmp_figure_space.py`, each italic digit's flank white tracked
almost exactly how far it reaches past where it *stands*:

| digit | own white, left (em) | its left flank (em) |
|---|---|---|
| 9 | **0.114** | **0.222** |
| 4 | 0.072 | 0.173 |
| 3 | 0.069 | 0.172 |
| 5 | 0.057 | 0.172 |
| 0 | **0.006** | **0.112** |

The 9's tail swings left under the baseline, so everything before a 9 was pushed
a full bearing past the tail's tip; the 0 reaches nowhere and sat tight. **Every
overhang was paid for twice** — once as the glyph's own shape and again as
spacing. That is measure 1's failure from the top of this document, in the
figures, and the cure is the same measure 3: fit on the body edge.

`_body_edges` in `outlines/build.py` takes each side as a percentile of the
glyph's per-row ink extremes (80th right, 20th left) on the **sheared** contours
— sheared is correct, because both glyphs of a pair move together at any one
row, so a gap is shear-invariant.

### Two dials, because evenness and colour are two decisions

`FIG_BODY` is how much of the overhang is absorbed and `FIG_TRACK` gives the
tightening back uniformly. Absorbing it all is not available:

| body / track | median | spread | flank sd | tightest pair |
|---|---|---|---|---|
| 0 / 0 (round 215) | 0.1532 | 2.03× | 0.0275 | 0.0708 |
| 0.50 / 0 | 0.1113 | 1.61× | 0.0141 | 0.0436 |
| 0.75 / 0 | 0.0932 | 1.47× | 0.0108 | **0.0080** — under the floor |
| 1.00 / 0 | 0.0743 | 1.67× | 0.0127 | **−0.0298** — touching |
| **0.75 / 20** | **0.1332** | **1.31×** | **0.0108** | 0.0480 |

At full absorption the tails genuinely collide: a 9's tail needs *some*
clearance even though it is not spacing. **0.75 / 20** takes the evenness of the
0.75 arm and puts the colour back — median 0.1332 against New York 0.135,
Pagella 0.129, Coelacanth 0.139.

Per-digit flanks go from a 0.112–0.222 spread to **0.114–0.157**.

### Three kerns, for round 178's reason exactly

The R's leg and the Q's tail were already the tightest ink in the font
(0.023–0.031 em against letters), and the digits' new left bearings took three
pairs under the floor: `R4` 0.031 → −0.012 and `R2` 0.024 → −0.004, both
touching, and `Q3` 0.035 → 0.011.

They are **pairs and not a looser fit**, because the clash is pair-dependent:
the R's leg reaches right *below* the figures' band, so it only meets a digit
with ink down there — `R4` and `R2` do, `R8` and `R0` do not — and widening the
4's left bearing to clear one R would open every other pair the 4 is in.
`O1`, `R1` and `Q5` tightened too and all three still clear the floor, so they
are left alone: three kerns, not six.

### What moved

Ten glyphs: the ten ASCII digits, metrics only — their outlines are identical
to round 215's once normalised on their own left edge (worst point deviation
1.00 unit, which is the integer grid). The superscript, subscript and fraction
figures are **not** touched: `isfig` is ASCII-only by design, and those are
composed at other sizes.

Gates: glitch 0 of 119, touch 0 of 5,197, roman byte-identical in both outlines
and metrics.

## Round 220 — the italic's punctuation, and the mark that was not the fault

Owner's own italic to-do, 2026-09-18: *"adjust punctuation of italic (include
apostrophe with 's' having too much space)."*

### A row-wise measure cannot see `s'` AT ALL

Both instruments this project uses for a gap — `cmp_touch`'s minimum white and
this document's body-edge gap — walk the rows the two glyphs **share**. An `s`
and an apostrophe share none: the s lives in the x-height band and the mark sits
entirely above it. `s'` came back `n/a` from both, on Albo and on three of the
seven references.

The gap a reader sees there is **diagonal** — the s's top-right shoulder against
the apostrophe's lower-left — so the honest measure is the closest approach in
TWO dimensions between the two ink sets, taken on the shaped pair. That is a
third measure, and it is the one this round is fitted on. (Implemented as the
nearest distance between A's right ink boundary and B's left; a full distance
transform needs scipy, which is not installed here.)

### And on that measure the apostrophe was in band

| pair | Albo, was | reference median | reference range |
|---|---|---|---|
| `s'` | 0.216 | 0.168 | 0.134 – 0.257 |
| `n'` | 0.242 | 0.218 | 0.171 – 0.301 |
| `s,` | **0.198** | 0.129 | 0.048 – 0.168 |
| `s.` | **0.164** | 0.132 | 0.052 – 0.155 |
| `e!` | **0.156** | 0.119 | 0.068 – 0.140 |
| `!a` | **0.236** | 0.167 | 0.100 – 0.187 |
| `?o` | **0.218** | 0.142 | 0.120 – 0.305 |

Flanker Griffo — the primary reference — puts `s'` at **0.257** and Pagella at
0.222, both looser than Albo's 0.216. **The quotes were never the fault.** Every
STOP, by contrast, was the loosest of the eight faces measured.

This corrects what the owner was told earlier in the session, which was that
`s'` opened 120 units against `so`'s 70. That is true and it is not evidence:
it compares a mark's bearing against a letter's without asking what a fitted
face does with the same pair, which is the whole method at the top of this file.

### The fix is a class split, not a dial

`PUNCT_MARKS` held the stops and the quotes together at round 97b's
`capbear × 2.25 + 17`, which was set on the ROMAN and is right for the quotes.
`PUNCT_STOPS` now takes its own factor, **1.05**, italic only — and two marks
need a delta on top, because a symmetric class factor cannot fit an asymmetric
shape:

* the **comma** at 1.05 read `s,` 0.166 against 0.129 *and* `,a` 0.080 against
  0.123 — wrong on both sides at once, because its ink hangs left of where a
  period's sits. `(−37, +43)` units.
* the **!** and the **?** were loose on the right alone: `(0, −39)` and
  `(0, −48)`.

Shipped, every pair lands on its reference median: `s,` **0.130** (ref 0.129),
`s.` 0.132 (0.132), `e!` 0.125 (0.119), `n?` 0.138 (0.130), `!a` 0.167 (0.167),
`?o` 0.152 (0.142), `,a` 0.122 (0.123). The quotes are untouched.

**One kern, and it is the Q again.** `Q,` fell to 0.008 em when the comma's
bearings came in — the same tail, the same reason, and the same answer as `Q3`
in round 216: the tail runs below the comma's own band, so it is a pair.

Seven italic glyphs move, metrics only: period, comma, colon, semicolon, exclam,
question, ellipsis. Roman byte-identical in outlines and metrics. Gates: glitch
0 of 119, touch 0 of 5,197, figure spacing holds at 1.31×.

## Round 221 — the whole font on one measure, and the quote's other side

Owner, 2026-09-18: *"take a pass at all spacing including 'apostrophe s'. use
and update md files."*

### Measure 4: the closest approach in two dimensions

`tools/wedge_serif/cmp_space_2d.py`. Every gap instrument before it — minimum
white, the body-edge gap — walks the rows two glyphs *share*, and a high mark
and a low letter share none. Round 220 measured `s'` (the letter before the
mark), found it in band, and never once measured `'s`, which is the pair the
owner had named. **A row-wise measure returned n/a for exactly the pair under
complaint, and the round shipped on the pair next to it.** Measure 4 takes the
nearest distance between the first glyph's right ink boundary and the second's
left, on the shaped pair, in em — the diagonal a reader actually sees.

It also groups by CLASS AND SIDE, because a bearing is a property of one side
of one letter (round 211), and reports each class's median against the seven
references' medians. A class out of band is a bearing; a pair out of band is a
kern.

### The ledger, both styles, at the start of the round

| class | italic | roman | ref median | ref band | italic verdict |
|---|---|---|---|---|---|
| lower+lower | 0.095 | 0.108 | 0.079 | 0.058 – 0.086 | loose, by his tracking |
| cap+lower | 0.128 | 0.128 | 0.100 | 0.073 – 0.119 | loose — the capitals are his |
| cap+cap | 0.129 | 0.095 | 0.078 | 0.058 – 0.094 | the documented +0.045 rhythm |
| digit+digit | 0.132 | 0.102 | 0.115 | 0.078 – 0.154 | in band (round 216) |
| letter+stop | 0.130 | 0.134 | 0.099 | 0.074 – 0.136 | in band (round 220) |
| stop+letter | 0.131 | 0.141 | 0.123 | 0.065 – 0.146 | in band (round 220) |
| letter+quote | 0.163 | 0.216 | 0.155 | 0.105 – 0.221 | in band |
| **quote+letter** | **0.244** | 0.195 | 0.148 | 0.105 – 0.217 | **LOOSE — this round** |

(The references are seven ITALICS. The roman column is measured against them
for want of a roman set, so its "loose" reads overstate: a roman is normally
fitted a little wider than its italic. Recorded, not acted on.)

### What was fixed: the quotes' right side

Each quote's two sides, median white against lowercase partners:

| mark | its right | its left |
|---|---|---|
| ’ | **0.255** | 0.133 |
| ” | **0.256** | 0.132 |
| ' | **0.249** | 0.208 |

The right side is nearly twice the left, from one flat bearing on both sides of
a mark that sits at cap height in a face sheared 13° — its ink already leans
toward the next letter. `ALD_QUOTE_RSB` takes 100 units off every quote's
right bearing, italic only. A horizontal shift does not transfer 1:1 to a
diagonal gap (−60 → −0.043 em, −100 → −0.071), so it was swept rather than
computed:

| rsb | quote+letter | `'s` | `'l` | touch gate |
|---|---|---|---|---|
| 0 | 0.244 | 0.286 | 0.208 | clean |
| −60 | 0.201 | 0.241 | 0.148 | clean |
| **−100** | **0.173** | **0.214** | **0.109** | **clean** |
| −120 | 0.161 | 0.201 | 0.089 | `'V` `"V` touching |

References for `'s`: 0.136 – 0.254, Flanker 0.254 and Pagella 0.224 above
Albo's 0.214, five faces below it. `'l`: 0.030 – 0.136. Six italic glyphs move,
metrics only; the roman is byte-identical. The owner's `f`+quote and `r`+quote
kerns sit on the marks' LEFT and are untouched.

### What was measured and deliberately not moved

* **The lowercase is his.** Italic lower+lower reads 0.095 against a 0.079
  median, and per letter the excess is UNIFORM (sd 0.010 across 18 letters'
  right sides) — that is round 136's +26 tracking he dialled at his bench, 13 a
  side, almost exactly the 0.016 em gap to the median. Built and measured so the
  question can be put with pictures: at +13 the class reads **0.083** (in band,
  one f-pair under the floor — `fU` 0.010), at +0 it reads **0.070** (on the
  median, eight f-pairs under the floor). Both arms are `ALBO_ALD_TRACK`, which
  exists for exactly this. Not shipped; his call.
* **Every capital's bearing is in `CAP_BEARING_ADJ`, round 137 — his table.**
  cap+lower's 0.128 is the right sides of E, H, N, T (0.153 – 0.165 against a
  0.100 median); T's, V's and W's LEFT sides at 0.205 – 0.231 are their own
  open white and not a fault by this document's first rule. cap+cap's 0.129 is
  the +0.045 rhythm `docs/albo-capital-spacing.md` records. Left alone.
* **The roman.** lower+lower 0.108, uniform (sd 0.017), against italic
  references only. No roman reference set is loaded; measuring one is the
  next step if the roman is ever to be re-fitted, not this table.

Gates: glitch 0 of 119, touch 0 of 5,197, figure spacing 1.31×.

## Round 222 — the apostrophe, third time: it comes down

Owner, on the round-221 proof: *"too much space between apostrophe and previous
and next letters. compare with other reference fonts."*

### Round 221 judged the band at its loose end

Rendered side by side at one x-height — the comparison he asked for — the mark
visibly NESTS between the letters in Georgia, New York, Coelacanth and Poetica
and floats in Albo. Round 221's band ran 0.105–0.217 because Flanker (0.254 on
`'s`) and Pagella hold its top; "in band" meant "not looser than the loosest".
The faces that read fitted are the tight four, and their medians are the
targets this round is fitted to: `t'` 0.109, `n'` 0.210, `s'` 0.166, `'s`
0.164, `'t` 0.115, `'l` 0.070.

### Bearings alone cannot get there

At the apostrophe's height its neighbours are capitals and ascenders. Sweeping
the two bearings (`ALD_QUOTE_LSB` × `ALD_QUOTE_RSB`) toward the tight four
flags 14 pairs at −40 / −140 — `'V` `"V` `f'` `U'` `T'` `V'` `'W` `j'` and the
quote-on-quote pairs — while `'s` is still at 0.189. The mark grazes the tall
glyphs beside it long before it reaches the x-height letter it is usually next
to, because that gap is a *diagonal* down to the letter's top.

### The lever the references use is HEIGHT

Measured (bounds, ÷ x-height): Albo's apostrophe hung from CAP — top 1.57,
bottom 1.09 — like Times and New York; the faces that nest sit lower: Georgia
top 1.52 / bottom 0.98, Pagella 1.39, Poetica 1.09. `QUOTE_DROP` in
`outlines/glyphs/marks.py` lowers all six quote glyphs, italic only — the
straight and curly quotes stay top-aligned to each other as they were designed.
Lowering the mark shortens the diagonal to an x-height letter's top without
moving it toward a capital's stem:

| drop / lsb / rsb | `t'` | `n'` | `s'` | `'s` | `'t` | `'l` | touch gate |
|---|---|---|---|---|---|---|---|
| 0 / −20 / −120 | 0.152 | 0.229 | 0.203 | 0.201 | 0.170 | 0.089 | `'V` `"V` touching |
| **50 / −20 / −120 — A, shipped** | **0.134** | **0.195** | **0.168** | **0.164** | **0.128** | 0.108 | `'V` `"V` `'W` → 3 kerns, then clean |
| 100 / −20 / −120 — B, built | 0.098 | 0.167 | 0.135 | 0.130 | 0.086 | 0.120 | clean, no kerns |
| 150 / −20 / −120 | 0.080 | 0.145 | 0.111 | 0.102 | 0.061 | 0.111 | `'?` under the floor |
| tight-four median | 0.109 | 0.210 | 0.166 | 0.164 | 0.115 | 0.070 | |

**A lands on the tight-four medians** (`'s` 0.164 exactly; `s'` 0.168 against
0.166) with the mark's bottom at 0.98 xh, which is Georgia's to the hundredth.
**B is tighter than every one of the tight four** on the round letters and
matches New York and Coelacanth on `'s`; it needs no kern. Both are built and on
the proof; A ships because it is the measured middle of the faces that read
right, and B is one dial away (`ALBO_ALD_QUOTE_DROP=100`).

The three kerns are the V's splay meeting the STRAIGHT quotes (`'V` −0.014,
`"V` −0.013, `'W` 0.012 at A): pairs, for round 178's reason. The curly quotes
clear — their tails hang inward.

Six italic glyphs move, outlines and metrics; the roman is byte-identical.
Gates: glitch 0 of 119, touch 0 of 5,197. Class medians after: letter+quote
0.119, quote+letter 0.126.

## Round 223 — the roman's figures get the body fit; the Q's tail does not get a kern

The misfit audit (`docs/albo-misfit-audit-2026-09-18.md`) found round 216's
body fit gated to the italic. `ROM_FIG_BODY` / `ROM_FIG_TRACK` in
`outlines/build.py` give the roman its own pair, and the roman wants less of
both: its digits have no tails swinging under the baseline, and absorbing 0.75
of the overhang puts `77` and `44` into contact (the 7's bar and the 4's
crossbar, meeting themselves). **0.45 / 8**, with `77` +36 and `44` +18 as
roman-gated pairs: spread **2.10× → 1.53×**, flank sd 0.030 → 0.017, median
0.1148 (Georgia 0.106, Pagella 0.129), tightest figure pair 0.042 em. The
roman's 19 pre-existing touching pairs are unchanged — not one added — and the
italic is byte-identical.

**The Q's tail was tried as fourteen kerns and that is the wrong rule.** The
pairs measure −0.25 to −0.49 em — the tail runs half an em under the next glyph
— so the smallest kerns that clear the floor are +270 to +522 units, up to half
the Q's own advance, and `Qg` `Qj` `Qp` still touch afterwards because the tail
meets a descender at a different row. Removed in the same round. The fault is
the tail's length (`caps_straight.py g_Q`, a hard-coded cubic with no dial) and
it is fixed there, as a drawing.
