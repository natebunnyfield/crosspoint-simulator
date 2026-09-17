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
