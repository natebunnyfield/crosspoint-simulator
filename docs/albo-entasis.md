# Albo's entasis: no stroke is dead straight

Round 180, 2026-09-16. Owner, asked whether to attack the italic's ruled
outlines by curving the centrelines or by varying the widths along them:
**"both curve and slight enstasis"**. This is what that came out as, what it
measured before and after, and the five things that were tried and do not work.

The code is `tools/wedge_serif/outlines/glyphs/aldine.py`; the ENTASIS block at
the head of that module carries the same reasoning beside the dials, and the
per-helper notes carry the per-letter half. The gate is
`tools/wedge_serif/cmp_aldine_straight.py`.

---

## 1. What was wrong, measured

`cmp_aldine_straight.py` calls a run of outline points STRAIGHT when every one
of them lies within 1.5 units of the chord joining its ends, and reports any
such run of 129 units (0.30 x-height) or longer — longer than any pen cut
(~94 units) or serif blade this family draws, so it can only be a stroke.

Before this round, **44 of 62 glyphs carried one**, for a total of **50,192
units** of straight edge, the longest a single 669-unit run on the V.

Three helpers drew almost all of it, and each was straight for its own reason:

| Helper | What it drew | Why it was straight | Worst runs, units |
|---|---|---|---|
| `hm_stem` | the lowercase stems — i l n m h u a r | `stroke([(xc, y0), (xc, y1)], sw)`: a TWO-POINT path at a CONSTANT width, so both edges were parallel straight lines | l 656, b 485*, m 365, a 361, i 315, u 308, h 301, n 301 |
| `cstem_i` | the capital stems — H N R P L K | it has taken a `bow` since round 131 and draws a five-point catmull for it, but `CAP_BOW` has shipped at **0.0** since round 134: the bow was built and switched off | L 611, P 457, H 430, R 363, K 342 |
| `cdiag` | the capital diagonals — N V A M X W | `mid` defaults to the EXACT midpoint of the two ends, which makes a three-point catmull a ruled line | V 669, W 625, N 591, M 577, A 524, X 381 |

\* the b draws its own stem rather than calling `hm_stem`, and so did three
other strokes; see §5.

---

## 2. The model

Two closed forms, applied to every stroke this round touches.

**The sway** displaces the centreline PERPENDICULAR TO ITSELF by
`amt * sin(2*pi*w*t)` — an S, or w of them. **The waist** scales the width by
`1 - E*(sin(pi*t) - 2/pi)` — fullest at the two ends, thinnest in the middle.

Four properties, each of which is load-bearing:

- **Both are zero at both ends.** `sin(2 pi t)` is 0 at t=0 and t=1, so a swayed
  stem starts and ends exactly where the ruled one did. Every junction in the
  face — the head lying across a stem's top, the exit off its foot, the arch
  landing on it, the bowl hung on it, the serif wedge seated on its edge — is
  untouched, and nothing downstream had to be re-fitted.
- **Both are zero-mean.** The mean of `sin(pi t)` is `2/pi`, which is what the
  waist subtracts, so the letter's colour does not move; `cmp_cap_weight.py`
  stays green with no compensating change to `CAP_W`.
- **They have opposite symmetry**: the sway is odd about the stroke's middle,
  the waist even. §4.2 is why that is the whole design.
- **Neither is a key table.** `primitives.widths()` smoothsteps between its
  keys, so curvature jumps at every key and a few-key table plants a visible
  crease at each one. `sin(pi t)` is smooth to every order.

The waist is **ends-swell**, which is what the roman already does
(`pen.ENT = DESIGN["flare"]`, "stems swell 14% at their ends"). It is also the
half of the choice the owner has already ruled on from the other side: a stem
fullest in the MIDDLE is the bulge round 134 took out of the capitals.

---

## 3. The dials, and what ships

Every one is an env var with a default, in the module's `ALBO_ALD_*` style.

| Env var | Ships | What it does |
|---|---|---|
| `ALBO_ALD_ENT` | 1.0 | the MASTER. Multiplies all six amplitude dials, so a ladder is one variable. **0 is the bit-exact arm** — every path falls back to its round-179 straight line. |
| `ALBO_ALD_ENT_SWAY` | 3.0 | lowercase stems: the S's amplitude, units |
| `ALBO_ALD_ENT_WAIST` | 0.055 | lowercase stems: the entasis, × the width |
| `ALBO_ALD_ENT_CAP_SWAY` | 4.0 | capital stems: the S, units |
| `ALBO_ALD_ENT_CAP_WAIST` | 0.050 | capital stems: the entasis |
| `ALBO_ALD_ENT_DIAG_SWAY` | 4.0 | capital diagonals: the S, units |
| `ALBO_ALD_ENT_DIAG_WAIST` | 0.045 | capital diagonals: the entasis |
| `ALBO_ALD_ENT_WAVE` | 250 | the sway's WAVELENGTH in units for stems. Period count is `round(length / wave)`, floored at 1. 0 (or anything over ~1100) gives exactly one S per stroke. |
| `ALBO_ALD_ENT_DIAG_WAVE` | 600 | the same for capital diagonals, which need a longer one (§4.5) |

The magnitudes sit inside the house's hand-cut unit of 2–7 units at a 674 cap
(`docs/albo-imperfections.md`): the lowercase stem is 70 units wide, so a
3-unit sway is 4% of its own width and the waist moves 4 units across the whole
stroke.

`CAP_BOW` is deliberately left at **0.0**. It is the SINGLE HUMP round 134
removed on the owner's own report — *"there is a pervasive issue of bulging
with a and H and other letters"* — and re-opening it is neither what he asked
for nor, arithmetically, what works (§4.2).

---

## 4. What was tried and does not work

### 4.1 "A swayed path varies its own width for free" — FALSE

`nib_widths` takes the width from the stroke's DIRECTION, so it reads as though
bowing a path would produce entasis at no cost. It does not, because `con()` is
a **normaliser and not a scaler**: it re-spreads whatever width range it is
handed onto the letter's contrast target EXACTLY. Measured by calling it:

```
con([1.000, 1.005], 2.20) -> 2.200:1
con([1.000, 1.010], 2.20) -> 2.200:1
con([1.000, 1.100], 2.20) -> 2.200:1
```

A half-percent ripple and a ten-percent one come out as the same 2.2:1 spread.
The one-degree direction change a 4-unit sway puts into a capital stem would
therefore have rendered as a stem half as wide at its waist as at its ends.

So: **the widths are solved on the UNSWAYED path**, and the waist is multiplied
in afterwards, beside `_taper`, which is applied post-`con` for the same
reason. The two lists need not be the same length, because `wf` is a function of
`t` and `stroke` resamples the path it is actually given.

This also explains why `CAP_BOW` could ship at 0.45 in round 131 and why `CAP_W`
had to move 1.36 → 1.16 when it went to 0: with the bow off, the stem's widths
are uniform and `con` is a no-op, and the whole of that width change was `con`
being switched off by accident.

### 4.2 A hump bow plus a waist CANCEL — one flank comes out dead straight

This is the one that would have cost most, because it is what a designer would
reach for: a small bow, plus a small entasis, both of the things that are
supposed to fix a ruled stroke.

A hump displaces the centreline by `B*sin(pi t)`, whose second derivative is
`-B*pi^2*sin(pi t)/H^2` — **one sign for the whole stroke**. A waist scales the
half-width by `(1 - E*(sin(pi t) - 2/pi))`, whose second derivative is
`+(sw/2)*E*pi^2*sin(pi t)/H^2` — also one sign, and the opposite one. They
cancel exactly on the edge where they meet, at

```
B = sw * E / 2        (35 * E units on the 70-unit lowercase stem)
```

At the very settings that look modest — B ≈ 3.5 units with E = 0.10 — one flank
of the stem is straighter than it was before either dial was touched.

An S is ODD about the stroke's middle where the waist is EVEN, so no choice of
the two amplitudes can cancel anywhere but at isolated points. It also puts its
curvature maximum (a quarter and three quarters along) exactly where the waist's
is zero, and its one inflection (the middle) exactly where the waist's peaks.
They cover each other's flats. Modelled on a 429-unit stem 70 wide, longest
straight run:

| | longest run |
|---|---|
| neither | 429 |
| the S alone | 197 |
| the waist alone | 356 |
| both, at a third of either's amplitude | 223 |

### 4.3 Raising the amplitude is the WRONG lever — it is a cube root

Near the S's inflection the centreline departs from its own tangent by
`amt*(2*pi/lam)^3*d^3/6`, so the flat patch the detector finds there is

```
2 * lam * (0.0363 / amt)^(1/3)   units long
```

— **linear in the wavelength and only a cube root in the amplitude**. Getting
that patch under the 129-unit floor at λ=400 needs the sway raised from 3 units
to 8.6, which is 12% of a stem's own width and a shape nobody would call
slight. At λ=250 the shipped 3 units does it. Measured on the built font,
moving one dial at a time:

| stem wavelength | glyphs flagged | total straight edge |
|---|---|---|
| 600 | 45 of 62 | 48,798 |
| 400 | 45 | 42,975 |
| 300 | 45 | 42,975 (429/300 still rounds to one period) |
| **250** | **38** | **37,087** |
| 200 | 34 | 35,070 |

200 was rejected on what it LOOKS like rather than what it measures: rendered
at 400 px the H's left stem is visibly bent and the h's ascender carries a
double curve.

### 4.4 One S per stroke, whatever its length, is wrong

The first cut used exactly one period per stroke. A hand's waver does not
stretch to fit whatever stroke it is drawing, and the measurement agrees: at
the same 3-unit sway the i's 429-unit stem came out with a longest run of 208
units and the l's 725-unit ascender, drawn with the identical dial, with 384.
The l is not less swayed; it is swayed over a longer span, and the flat at the
inflection grows as the SQUARE of the stroke's length.

The period count is `round(length / wavelength)`. **Rounded**, because a
fractional number of periods does not come back to zero at the far end, and
every junction in the face is built on the promise that it does — an ascender
ending 2 units left of where its head lies across it is a defect, not a waver.

### 4.5 A capital diagonal will not take the stems' wavelength

At the stems' own 250, rendered at 430 px, the l h n u H read as lively and the
**V's two diagonals read as DENTED** — a visible notch a third of the way down
the right one, where three periods of a 4-unit sway cross a stroke that is
otherwise one movement. At 350 the W ripples along its whole length. It is the
same amplitude that is invisible on a stem, and the difference is what the
stroke IS: a stem is drawn a dozen times a line and its waver is the page's
texture; a capital diagonal is drawn once, and every departure from its chord
is read as an event.

600 puts one S on a 600-unit diagonal and two on the V's 700-unit one, and is
where the dent stops being visible. It costs about 6,000 units of straight edge
against 450 for no change in the glyph count, which is the trade taken.

### 4.6 The glyph COUNT is a poor metric; total straight length is the live one

The count only moves when EVERY run in a glyph drops under 129, so a change
that halves the longest run in thirty letters can leave it flat or move it the
wrong way. The first cut of this round took the total from 50,192 to 35,426
units — a 29% cut, with the V down 669 → 180 and the l 656 → 198 — and the
count from 44 to **45**, because runs that had been single long ones were now
several shorter ones still over the floor. Both numbers are reported here for
that reason.

---

## 5. What it bought

Shipped defaults, against round 179:

```
44 of 62 glyphs flagged, 50,192 units    ->    38 of 62, 36,897 units
```

Six glyphs went from flagged to **clean**: **b P R a K i**.

Longest run per glyph, before → after, for everything that moved:

```
l 656 -> 141    b 485 ->   0    P 457 ->   0    L 611 -> 198
V 669 -> 305    R 363 ->   0    a 361 ->   0    K 342 ->   0
W 625 -> 308    i 315 ->   0    N 591 -> 303    M 577 -> 317
A 524 -> 307    m 365 -> 179    u 308 -> 133    X 381 -> 263
h 301 -> 191    n 301 -> 191    H 430 -> 371
```

Four strokes outside the three helpers were the same defect written out
longhand, and took the same two dials:

- **the b's ascender** (485/472/462) — its own catmull through three collinear
  points. The S is laid on the STRAIGHT SECTION only, down to xh\*0.28 where the
  stroke leaves the stem's line into the bowl's bottom arc, because `ent_sway`
  displaces a path perpendicular to itself and over a turn that tight would
  ride round the corner and waver the exit.
- **the u's left stroke** (272) — same shape, same treatment.
- **the A's left leg** (`_flat_foot_diag`, 481) and **the M's left stroke**
  (577) — both are `cdiag`'s body copied, and inherited its ruled midpoint.
- **the X's thin diagonal** (378) — round 165's hand cut already moves its
  middle control point; the sway composes with that offset rather than
  replacing it, so that asymmetry survives.
- **the m's middle brush stroke** (`m_midstem`, 320) — `hm_stem`'s shape
  without `hm_stem`'s code, so it did not move when that helper did.

### Gates

All green at the shipped defaults:

```
cmp_aldine_metrics.py     0 letters outside 10% of a measured target
cmp_cap_weight.py --tol 0.05   0 re-cut capitals more than 0.05 from their roman
cmp_aldine_glitch.py      119 glyphs swept, 0 with findings
cmp_touch.py              0 pairs TOUCHING, 0 below the 0.012 em floor
```

No bearing and no kern value had to move. That is the zero-mean property
earning itself: the sway does not shift a stem's average position and the waist
does not change a letter's colour, so the fitted spacing of round 178 still
holds.

### The zero arm is bit-exact

Built at `ALBO_ALD_ENT=0` and compared glyph by glyph against round 179:
**0 of 119 glyphs differ in a single coordinate**, and `hmtx` is identical. The
only difference in the file is the build timestamp.

---

## 6. What is left, and why

**24 glyphs still carry a run, and most of them cannot be reached from
`aldine.py`.**

- **J I D B and the digits 1 2 4 7 9** are not defined in this module at all —
  the italic takes them from the roman (`caps_straight.py`, `figures.py`),
  sheared. J's 509-unit run is now the longest in the face.
- **E F T** are `_press(_CS.g_E(c), ...)` — the roman's drawing with round 165's
  hand-cut table on top. Their stems are the roman's ruled verticals. Re-cutting
  them was rejected once already (round 165's own note: "a second copy of
  `g_E`'s bar arithmetic in this module is a copy that drifts"), and the same
  argument holds here.
- **The H's and the L's remaining runs are BARS** — H 371 and 367 are the two
  edges of its crossbar at 3 degrees, L 198 is the bottom bar's underside. The
  gate's own docstring names bars as deliberate and reports them for a human to
  rule on rather than filtering them. Nothing here changed them.
- **z v w x y t f j k Z Y U G** are lowercase and capitals drawn through
  `d_pen`, `keyed_ring` and their own inline paths, each with its own width
  table. They are the next round's work if the owner wants it, and each needs
  its own decision about where a sway may be laid, for the reason the b's note
  gives.

**Two strokes deliberately got the sway and NOT the waist**, and that is a gap
rather than a decision: the **b's stem** and the **u's left stroke** both run
their `widths()` table over the stem AND the turn AND the tail on one `t`.
`ent_waist` is `1 + 2*amt/pi` at its ends rather than 1, so folding it over the
stem's share alone leaves a step at the table's key, and folding it over the
whole path fattens the tail. A waist that is exactly 1 at both ends and thinner
between loses `amt*2/pi` of the stroke's area, which is a weight change the
gates would catch. Neither was worth solving for two strokes in this round.

---

## 7. The ladder

Four rungs, rendered through `proof.py` so the baselines line up with every
other proof in this project. Off, shipped, double, and clearly too much:

| Rung | Dials | Flagged | Total straight edge |
|---|---|---|---|
| OFF | `ALBO_ALD_ENT=0` | 44 of 62 | 50,192 |
| **SHIPPED** | defaults | **38 of 62** | **36,897** |
| DOUBLE | `ALBO_ALD_ENT=2` | 36 of 62 | 32,425 |
| TOO MUCH | `ALBO_ALD_ENT=4 ALBO_ALD_ENT_WAVE=150 ALBO_ALD_ENT_DIAG_WAVE=250` | 28 of 62 | 20,167 |

Each rung shows the display-size string `lbhmniu HVAM` at 150 px and two lines
of running English at 30 px and 20 px. The text sizes are where the answer is:
at 20 and 30 px all four rungs but the last are indistinguishable, which is the
point — this is a display-size property of the drawing, not a text-size one.
