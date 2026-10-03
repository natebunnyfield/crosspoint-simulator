# Albo: the italic parentheses' height (2026-10-02)

Owner todo: *"italic parentheses seem low or text is too high"*.

**Status: SHIPPED, P3** (owner 2026-10-02, *"P3 wins next"*), as round 466
(`docs/albo-round-466-2026-10-02.md`). The dial is `ALBO_ALD_PAREN_RAISE`
(`tools/wedge_serif/outlines/glyphs/marks.py`, `PAREN_RAISE_IT`), in units, for
the italics only: Italic and Bold Italic, which share `paren()`. It ships at 48.
Setting it to 0 builds round 465's parentheses. Before the ruling, the status
was options P1 / P2 / P3 beside today.

## 1. Which side is off: the parentheses

The italic draws the roman's parentheses, sheared, at the roman's height:
−251..735 (Bold Italic −265..742). Its letters stand taller than the roman's:

| | x top | l, d top | f top | p bottom | g bottom |
|---|---|---|---|---|---|
| Regular | 451 | 771 | 764 | −281 | −294 |
| Italic | 457 | 783 | 799 | −286 | −197 |

So within the italic, the l and d rise 48 units above the parentheses, against
36 in the roman. The italic's own shallow g (−197) puts even more of its weight
high.

**Against the references.** Measured in x-heights, from outline ink boxes,
unhinted (`tools/wedge_serif/instruments/paren_height.py`, verified against
source):
- "( top / ( bot" are the parenthesis's extremes.
- "asc" is the l's top and "desc" is the p's bottom.
- "ctr off" is the parenthesis's center minus the center of [desc, asc];
  positive means it sits high.

| italic | ( top | ( bot | asc | desc | ctr off | top − asc | desc − bot |
|---|---|---|---|---|---|---|---|
| **Albo Italic** | 1.609 | −0.533 | 1.713 | −0.626 | **−0.005** | **−0.104** | −0.093 |
| **Albo Bold Italic** | 1.581 | −0.537 | 1.668 | −0.611 | −0.007 | −0.087 | −0.073 |
| Flanker Griffo Italic | 1.836 | −0.423 | 1.750 | −0.761 | 0.212 | 0.086 | −0.338 |
| Poetica | 1.615 | −0.412 | 1.688 | −0.670 | 0.093 | −0.072 | −0.258 |
| Pagella Italic | 1.544 | −0.506 | 1.521 | −0.573 | 0.045 | 0.023 | −0.066 |
| Palatino Italic | 1.532 | −0.215 | 1.515 | −0.575 | 0.188 | 0.017 | −0.360 |
| Georgia Italic | 1.530 | −0.328 | 1.546 | −0.444 | 0.050 | −0.016 | −0.116 |
| Charter Italic | 1.477 | −0.292 | 1.515 | −0.448 | 0.059 | −0.037 | −0.156 |
| Times Italic | 1.571 | −0.484 | 1.571 | −0.484 | 0.000 | 0.000 | 0.000 |
| Baskerville Italic | 1.616 | −0.577 | 1.623 | −0.574 | −0.005 | −0.007 | 0.004 |
| reference median | 1.557 | −0.418 | 1.559 | −0.573 | **0.055** | **−0.004** | −0.136 |

- **References:** the parentheses reach the ascender (median −0.004). Their
  center sits above the middle of the letters' extremes (+0.055).
- **Albo:** its parentheses stop 0.104 x-height under its ascender, and their
  center sits 0.06 lower than the references'.
- **The text is not the outlier.** Albo's ascenders are long against its
  x-height, but that is so in both styles (1.71 in the Regular and in the
  Italic, against the references' 1.56). It is the face's design, so the fix
  is the parentheses.

**The roman measures the same relation** (top 0.080 under its ascender, center
+0.002 against the references' +0.059). It was not named and is not touched.
Neither are the brackets, braces or bar, which share `FENCE_RAISE` with the
parentheses (`marks.py`, round 98).

## 2. Raising a sheared parenthesis unbalances it

The italic parenthesis is sheared 13 degrees. Raise it, and the letters' band
sees a lower stretch of its arc, which lies further left of its own ink box.
That opens the white inside `(x` and closes it inside `x)`, by tan 13° each.

Measured with the shipped fence kerns, by the band gap that `local_ai/fences.py`
balances:

| raise | mean (close − open) | worst | pairs off by ≥ 8 |
|---|---|---|---|
| 0 (today) | +0.2 | 9 | 1 |
| +16 | −7.4 | 16 | 23 |
| +32 | −15.2 | 28 | 60 |
| +48 | −22.6 | 41 | 60 |

That is −0.46 units per unit raised, in the Italic and the Bold Italic alike.
**Any raise therefore needs its fence kerns re-measured**, or every
parenthesis hugs its closing letter.

`fences.py` gained `--cuts` and `--pairs`, which re-measure only the named cuts
and fences and leave the rest of the block alone.

**Control.** At raise 0, on today's outlines, it reproduces the shipped
paren kerns except for the x:
- Italic: `( x` −20 → −24, `x )` +20 → +24.
- Bold Italic: −16 → −18, +16 → +18.

These are stale since round 461 redrew the x. The fences were measured on the
old letter. A shipped raise refreshes them along with the rest.

## 3. The arms (fence kerns re-measured for each)

| arm | `ALBO_ALD_PAREN_RAISE` | ctr off | top − asc | desc − bot | Italic span |
|---|---|---|---|---|---|
| today | 0 | −0.005 | −0.104 | −0.093 | −251..735 |
| P1 | 16 | 0.030 | −0.069 | −0.128 | −235..751 |
| P2 | 32 | 0.065 | −0.034 | −0.163 | −219..767 |
| P3 | 48 | 0.100 | 0.001 | −0.198 | −203..783 |
| reference median | | 0.055 | −0.004 | −0.136 | |

- P2's center lands on the references' median.
- P3's top lands on the ascender, as most references' do.
- At 10 pt on the X3 a unit is 0.021 px, so P3 moves the parentheses up one
  pixel; on the phone's 2x tier, two.

**Gates, each arm against round 465:**

| gate | result |
|---|---|
| outlines moved | ( and ) only, both italics |
| touch | 0 / 0 |
| hairs | none new |
| counter dents | 1 → 1 |
| contour census | unchanged |
| approved letters | unchanged |
| kern classes | ok (Italic 124 / 159 at most, Bold Italic 124 / 160) |
| fence symmetry | restored: mean close − open within 0.1, worst 6, none ≥ 8 |

Each arm re-tunes 110–120 italic paren kerns per cut. Every other entry of the
table, roman and italic, is unchanged.

## 4. Reproduce an arm

    cd tools/wedge_serif; source build_env.sh; R=32
    env "${ALBO_ITA_ENV[@]}" ALBO_FENCES=0 ALBO_ALD_PAREN_RAISE=$R PYTHON_GIL=0 python3 -m outlines.build F --style Italic
    env "${ALBO_BIT_ENV[@]}" ALBO_FENCES=0 ALBO_ALD_PAREN_RAISE=$R PYTHON_GIL=0 python3 -m outlines.build F --style BoldItalic
    cp outlines/spacing_b2.json /abs/tab.json
    (cd local_ai && ALBO_SPACING_TABLES=/abs/tab.json $VENV/bin/python fences.py F --cuts Italic,BoldItalic --pairs "(")
    env "${ALBO_ITA_ENV[@]}" ALBO_SPACING_TABLES=/abs/tab.json ALBO_ALD_PAREN_RAISE=$R PYTHON_GIL=0 python3 -m outlines.build A --style Italic
    (Bold Italic the same with ALBO_BIT_ENV)
    $VENV/bin/python instruments/paren_height.py A        (needs the four cuts in A)
    $VENV/bin/python instruments/paren_proof.py PROOF today=<round 465> P1=... P2=... P3=...

To ship, regenerate the fences in the real table (`ALBO_SPACING_TABLES` unset)
and run the clearance loop as usual.

Proof page: https://claude.ai/artifact/4DV3uoG6csTzZSw5hZaPi1
