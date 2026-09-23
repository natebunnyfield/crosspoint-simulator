# Capital spacing — after U, and with Y

2026-09-16. Owner: *"adjust the letter spacing of capitals especially after U
and with Y"*.

Instrument: **`tools/wedge_serif/cmp_cap_space.py`**. It renders a pair, places
the second glyph at the pair's *shaped* advance, and reports the minimum
horizontal white between the two inks over every row they share — in em, so
three fonts at three units-per-em compare directly.

```
PYTHON_GIL=0 python3 cmp_cap_space.py <built>/Albo-Italic.ttf
```

## The baseline, which is not zero

Albo's capitals run a **uniform +0.045 em looser than Flanker** — HN +0.048,
NN +0.048, HH +0.043, OO +0.043, EN +0.070, DO +0.055 — and nobody has
complained about any of them. That is the face's own rhythm. A pair's target is
therefore Flanker's white **plus ~0.045**, and a fault is distance from *that*.
The script prints those control pairs first for this reason.

## What was wrong

| | before | after | Flanker |
|---|---|---|---|
| UI | +0.193 | +0.053 | — |
| UM | +0.153 | +0.068 | — |
| UR | +0.145 | +0.060 | — |
| UN | +0.135 | +0.050 | — |
| UP | +0.133 | +0.048 | — |
| **YA** | **−0.185** | +0.033 | — |
| **YO** | −0.198 | −0.035 | — |
| **LY** | −0.155 | +0.008 | — |
| **YU** | −0.090 | +0.020 | — |
| RY | −0.085 | +0.058 | — |

(columns are Albo minus Flanker, in em)

**U stood about 0.13 em too far from everything after it.** **Y was 0.10–0.20 em
too close on both sides — and `YA` and `YU` measured a negative gap: the two
letters actually touched.**

## The instrument's own bug, and why it matters

The first cut placed the second glyph at `getlength(a)` — the **unkerned**
advance — so the whole GPOS kern table was invisible and every number described
bearings alone. It was the corrected run that found `YA` and `YU` touching; the
un-kerned run had called them merely tight, and a softening tuned to it would
have shipped two colliding capitals. The offset is
`getlength(a+b) - getlength(b)`.

## The fix, and why it is mostly bearings rather than kerns

Y is tight in **both** directions, and several of the worst pairs — **OY, NY** —
have no kern cell at all, because C G O Q and N were right-hand classes only.
A deficit that shows with no kern in play is the letter's own bearings. **Round
163 rebuilt the Y** (the owner's weight ruling, the arm pulled in) and its
bearings were never re-solved: the `−116` on its right was fitted to a Y that no
longer exists.

- `aldine.CAP_U_RSB` +12 → **−72**
- `aldine.CAP_Y_LSB` 0 → **+90**, `CAP_Y_RSB` −116 → **−6**
- `kern.py`: `('L','VWY')` −108 → −36, `('R','VWY')` −54 → 0, `('Y','O')` −54 → 0,
  `('Y','A')` −108 → 0
- a **new left class `Oleft`** (C G O Q) with `('Oleft','VWY') = +36` — positive,
  which is rare here and correct: OY was the worst pair in the measurement and
  had no cell at all, because a round capital *followed by* a diagonal one could
  not be spoken about
- two pair exceptions the one U bearing could not serve: `('U','U') +72` (two
  identical stems, so both bearings are the tight one) and `('U','I') −54` (the
  I carries a +33 left bearing of its own, being a bare stem)

Every pair in the sweep now sits inside the band the untouched control pairs
occupy. Worst residuals: YO −0.035 and YT +0.088.

---

# Round 178 — the collision sweep

Owner 2026-09-16: *"fix LA and any other touching letter combinations"*. The
second half is the instruction: `LA` was found by eye, and anything found by eye
has siblings nobody happened to type.

Instrument: **`tools/wedge_serif/cmp_touch.py`**, which sweeps **all 5,193 pairs**
(A–Z, a–z, 0–9 and eleven marks). It renders each GLYPH once and reduces it to
two profiles — for every scanline, the rightmost and leftmost ink — so a pair's
white is arithmetic rather than a second render. The second glyph is placed at
`getlength(a+b) - getlength(b)`, the pair's *shaped* advance, so the kern table
is in every number.

**46 pairs were touching.** `LA` was the 30th worst, at −0.008 em, against `RA`
at −0.145.

## Three causes, in order of how many pairs each owned

**1. A's left bearing, −151 — ten pairs.** R k z x 4 3 A , d L all collided with
it. That number is an owner's own from the round-137 bench, and it is what lets
a T, V, W or Y tuck over the A's sloping left. So it is raised by **+126** and
the four kern cells that do the tucking are deepened by *exactly* the same
amount — `('T','A')` −90 → −216, `('VW','A')` −90 → −216, `('Y','A')` 0 → −126,
`('FP','A')` −72 → −198. TA, VA, FA, PA and YA measure within **0.0001 em** of
where they were; every other letter before an A gains 0.126. The raise is 126
rather than a round number because a kern value must be a multiple of STEP (18,
the reader's kern quantum) and the compensation has to be exact.

**2. R's right (−56 → 0) and W's right (−132 → −60)** — twelve pairs and five.
Rs RE Rk Rz Rh Rl Rj Rg Rm Rp Rr; WV W" W' WW WU. `WA` moves +0.072 as a
consequence and is the one approved pair this round changes; it still sits
tighter than VA.

**3. THE FITTING BAND CANNOT SEE A DESCENDER** — the remaining thirteen.
`outlines/build.py` fits a glyph from the ink inside its x-height or cap band
(`-OVER <= y <= top + OVER`), so a stroke that leaves the band is invisible to
the letter's own bearings. The g and the J are already excepted there by name;
the q, the Q and the f are not, and their tails and hooks are what survived
every bearing fix above — qj −0.110, qf −0.085, Qg −0.078, qy −0.060, gj −0.048.

### Why those are kern pairs and not a band change

Fitting those letters on their full extent is the tidier fix and it is the wrong
one: **q's tail reaches far right *below* the baseline**, so a full-extent fit
would space `qu` — very nearly every q in English — by ink that is nowhere near
the u. The clash is genuinely pair-dependent: it happens only when the *second*
letter also has ink down there. Values are per-pair rather than a class cell
because the depths differ by an order of magnitude (qj −0.110, Qf −0.004), and
one number that fixes qj opens `qp` to 0.127.

## Result

**0 touching, 0 below the 0.012 em floor**, from 46 and 66. The floor is stated
rather than assumed: about a third of the thinnest hairline this face draws,
which is where two letters stop reading as two at 13 pt. Pairs that are *meant*
to interlock — the f's hook onto an ascender's top-left wedge — are in
`cmp_touch.EXEMPT` with their reason.

---

## Round 348 — the roman Q's thirteen pairs, kerned; and the gate that could not see it

Owner 2026-09-21, choosing between a shorter tail and kern pairs: *"kern Q"*.
The letter is untouched.

The Q's ink runs to **x=1312 on a 777-unit advance** — the tail overhangs 535
units past its own body and dips to y=−272 — so any following descender crosses
it. `Quiet`, `Qu`, `QU` and `Question` are all correct and are unchanged by
this round, because u, i, e, t and U have nothing below the baseline.

**Ten of the thirteen genuinely INTERSECTED**, measured as a 2-D distance
between rasterised outlines. `Q7` did not and takes no kern (it clears by
0.0125 em); `Q5` and `Q3` passed within 0.007 em. Each kern is the smallest
value, swept −400..+900 by 20 and ordered by absolute size, that reaches
`cmp_touch`'s own 0.012 em floor on ink:

| | 4 | 7 | 9 | q | y | ( | ) | p | g | j | J | 5 | 3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kern | −60 | — | +60 | +140 | +360 | +440 | +440 | +460 | +480 | +500 | +500 | +500 | +520 |
| after | .0146 | .0125 | .0125 | .0150 | .0168 | .0236 | .0237 | .0150 | .0195 | .0200 | .0135 | .0135 | .0135 |

Nine of them cost a third to a half of an em, which is a visible hole. They
ship because every one is a sequence that does not occur in English — round
225's own argument for exempting them, used here to license the repair instead.

### The instrument finding, which is the part worth keeping

**`cmp_touch` cannot report this fix, and its numbers about the Q were never
about touching.** It compares, per raster ROW, the second glyph's left edge
with the first glyph's RIGHTMOST INK ON THAT ROW. The Q's tail reaches x=1312
on rows the following glyph also occupies, so the row-wise number sits at
−0.25 to −0.49 em *whatever the kern does*, short of pushing the pair clean
past the tail's end — and it reported `Q7` at −0.4075 when that pair has never
touched anything.

Same family as the three measures `docs/albo-spacing-method.md` already
records: a row-wise reading cannot follow a thin stroke past a later glyph, any
more than minimum-white can see an open shape. The thirteen stay EXEMPT there
with the reason corrected — it is the instrument that cannot follow the tail,
not the drawing that is wrong.

**And one of my own measurements was wrong first.** An ad-hoc polygon
rasteriser written for the sweep dropped the tail entirely — a long thin closed
contour at 0.2 px/unit renders as sub-pixel spans that PIL's `polygon` fill
discards — so `Q7`, `Q9` and `Q4` came back clear at a 20-unit kern while the
tail ran straight through the figure. Caught by rendering the pair and looking
at it. Use the font's own rasteriser.

---

## Round 360 — the Bold had no collisions at all, and two were the gate's own

The Bold carried **four TOUCHING pairs** through builds 205, 206 and 207, and
they were reported in each deploy as pre-existing and unfixed. Measured, none
of the four is touching.

| pair | the gate said | measured 2-D | what it actually is |
|---|---|---|---|
| `Q,` | −0.4254 | **+0.0613 em** | the tail reaching past a mark, never meeting it |
| `Q;` | −0.4168 | **+0.0632 em** | same |
| `ff` | −0.0341 | — | **the font ligates it**; the sequence is never drawn |
| `fi` | −0.0234 | — | same |

**`Q,` and `Q;` are the row-wise blind spot round 348 already documented** for
the other thirteen Q pairs — they only surfaced at the Bold because a mark's
own width moves with weight. Exempted with their measured clearance; no kern,
because none is needed.

**`ff` and `fi` were a different bug, and it is fixed rather than exempted.**
`cmp_touch` places the second glyph at `getlength(xy) − getlength(y)`; for a
ligating pair that is the LIGATURE's advance applied to two loose glyphs, which
overlaps them by construction and then reports the overlap. Measured on the
Bold, `ff` shapes to 618 units against 772 for two separate f's.
`ligating_pairs()` now reads the two-glyph sequences out of the font's own
`liga` feature and drops them before the verdict — from GSUB rather than a hand
list, because the roman carries ff fi fl ffi ffl and the italic carries none
(owner 2026-09-21), so any hand list would be wrong for one of the two styles
the day it was written.

**The Bold now reports 0 touching pairs.** What is left across the whole family
is one genuine row: the Regular's `VI` at −0.0052 em, long-standing and in the
baseline.

**Neither font changed.** This round is the instrument.
