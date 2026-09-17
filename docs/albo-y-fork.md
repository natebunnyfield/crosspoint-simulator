# Albo's italic y: the fork, the tail, and what "seems very high" actually is

**Owner, 2026-09-16:** the italic `y` *"seems very high"* in a word.

Measure-and-propose. Nothing in `tools/wedge_serif/` was changed to produce
this file: every arm below is an existing `ALBO_ALD_Y_*` env dial, and the two
that are not are stated as not-in-the-tree and were built from a patched COPY
of `aldine.py` in a scratch sandbox.

Everything is measured on an **unsheared raster at a fixed x-height** — the
procedure `cmp_aldine_g.py` uses, so a 13-degree slant and Pagella's 10 answer
the same question — and reported in Albo's design units at xh 429. Thickness is
a Euclidean distance transform rather than a scanline chord, because this tail
runs nearly horizontally at its foot, where a horizontal chord reports **148
units for a 30-unit hairline**, and it is vertically continuous with the body at
its head, where a vertical chord reports the whole letter. Built at
`ee94121`+working tree, y outline verified identical before and after the run
(another agent was editing `aldine.py`'s `g` at the time; the `y` did not move).

## 1. The premise that brought me here is no longer true

An earlier note recorded that **the y's fork closes around the middle of its
x-height** while the v's closes at the baseline, and named a possible fix —
bring the junction down. Measured on today's build, with `Y_LBOW = 41` in it:

| | fork closes | as a fraction of the x-height |
|---|---|---|
| **Albo y, shipped** | **31.8** | 0.074 |
| Albo y with `Y_LBOW=0` (round 176) | 59.7 | 0.139 |
| Albo **v** | 72.6 | 0.169 |
| Flanker Griffo y | 82.9 | 0.193 |
| Poetica y | 62.6 | 0.146 |
| Pagella y | −8.9 (below the baseline) | — |
| Cancelleresca y | −47.2 | — |

The y's fork closes **lower than its own v**, and lower than every reference y
but the two that close below the baseline. It was never near the middle of the
x-height: at its worst, before the bow, it was 0.139 of it.

**What `Y_LBOW = 41` already bought**, largest interior white by height:

| height | 0.80 xh | 0.60 | 0.40 | 0.25 | 0.15 |
|---|---|---|---|---|---|
| `Y_LBOW` 0 | 105.1 | 92.2 | 53.6 | 26.5 | 2.9 |
| `Y_LBOW` 41 (ships) | **136.6** | **130.8** | **92.2** | **58.6** | **26.5** |
| Albo's v, for scale | 109.4 | 100.8 | 52.9 | 17.2 | 0.0 |

The bow widened the counter by 30–70% at every height and dropped the closure
28 units. The y's counter is now **wider than the v's at every height**, which
is the opposite of the complaint the bow was drawn to answer. So: the junction
is not the fault, there is nothing left to lower, and lowering it further is not
reachable by a dial anyway — `Y_LBOW` pins both ends of the stroke by
construction, so no value of it moves the meeting point.

**The top is not the fault either**, which the earlier note had right and this
run confirms: y 441, v 446, u 445, x 439, n 433 (outline, build space). The y
sits inside the band its neighbours occupy.

## 2. What IS different about this y

It is the deepest descender in the font — and almost none of that depth is
under the letter.

| | advance | deepest ink | **hang under its own body** | inside its own advance box | descender ink left of the origin |
|---|---|---|---|---|---|
| **Albo y** | 385 | **289** | **227** | 242 | **50.2 %** |
| Flanker Griffo | 443 | 326 | 326 | 326 | 0.0 % |
| Pagella | 445 | 245 | 245 | 245 | 1.6 % |
| Poetica | 354 | 286 | 212 | 233 | 46.4 % |
| Cancelleresca | 482 | 424 | 385 | 400 | 25.0 % |

Measured on the SHEARED render with the glyph's own origin and advance known,
because this is a question about a line of text and not about a drawing.

**Half of this y's descender lands under the letter before it.** In its own
column the reader gets 227 units of hang where Flanker gives 326 — and the ink
that is there is a 22-unit hairline travelling at 35–50 degrees off horizontal,
not a stroke going down. That is what "seems very high" looks like as a number:
in `my yearly youth` the y's descender is a thin line skimming just under the
baseline on its way somewhere else, so the letter's own mass ends at the
baseline and it reads like an `n` with a flourish.

Tail weight and direction, by depth (EDT thickness; angle off horizontal):

| | −0.10 xh | −0.25 xh | −0.45 xh |
|---|---|---|---|
| **Albo** | 22.6 @ 50° | 22.2 @ 47° | 25.0 @ 35° |
| Flanker | 22.4 @ 61° | 19.2 @ 63° | 18.6 @ 63° |
| Poetica | 24.6 @ 48° | 29.8 @ 42° | 44.4 @ 29° |
| Pagella | 42.9 @ 59° | 33.4 @ 54° | 60.8 @ 37° |

Two corrections to the record while we are here. The tail is **22 units**, not
the 31 the earlier note quoted — 31 is the number in `aldine.py`'s round-135
comment describing the tail Albo had **before** round 135 ("Albo's ran 31 / 35 /
43 / 52 / 58"), and the dial has said 26 since. And the tail is not "nearly
horizontal" at the top: it leaves the junction at 50 degrees and *flattens* on
the way down, reaching 33 degrees at −0.60 xh.

**The tail's descent PROFILE is not the fault, and this is the negative result
that killed the obvious fix.** Normalizing each tail between its junction and
its deepest point:

| | half its depth spent by | four fifths by | travel ÷ depth |
|---|---|---|---|
| **Albo** | 33.3 % of the travel | 58.9 % | **1.33** |
| Cancelleresca (round 135's reference) | 31.6 % | 57.5 % | 1.20 |
| Poetica | 35.7 % | 64.9 % | 1.26 |
| Pagella | 29.6 % | 56.2 % | 1.19 |
| Flanker | 27.0 % | 27.0 % | 0.77 |

Round 135 set out to make this tail plunge and then whip, the way Cancelleresca
does, and **it succeeded** — Albo's profile is within two points of the
reference's at both marks. What is out of line is the last column: Albo spends
1.33 units of leftward travel per unit of depth, the flattest of the five, on
the **narrowest advance** of the five (385 against 443, 445, 482). A tail on the
reference's own profile still leaves the letter's column at 78 % of its depth
when the letter is that narrow and the swash reaches that far.

## 3. The ladder

`scratchpad/y_fork_ladder.png` — each rung large with rules, then the same
English at 30 px and 20 px.

| | dials | hang under the body | inside the advance | q+y white, em |
|---|---|---|---|---|
| **A** shipped | `X 8, W 26, Y −0.62` | 227 | 49.8 % | 0.030 |
| **B** hairline thickened | `W 36` | 234 | 51.4 % | 0.030 |
| **C** swash half pulled in | `X 70` | 227 | 59.3 % | 0.091 |
| **D** swash at Flanker's extent | `X 118` | 267 | 70.4 % | **0.140** |
| **E** pulled in and thickened | `X 118, W 36` | 267 | 73.0 % | **0.140** |
| **F** floor dropped | `Y −0.75` | **221** | 45.3 % | 0.030 |
| *G* plunge 0.60 *(not in the tree)* | — | 254 | 53.5 % | 0.030 |
| *H* plunge 0.85 *(not in the tree)* | — | 268 | 56.3 % | 0.030 |

Costs, in the order they matter:

- **B is nearly free and nearly nothing.** A thicker hairline is thicker
  downward too, so it buys 7 units of hang. It is a colour change, not a fix.
- **C buys nothing at all on the number that matters.** Pulling the reach to 70
  moves ink into the advance box (49.8 → 59.3 %) without moving the hang under
  the body one unit, because the deepest point is still out past the letter.
- **D and E work, and they cost two things.** They reverse the owner's own
  2026-09-16 ruling — *"the owner took Poetica's full swash"*, the one place
  chancery is allowed to move the text lowercase — and they blow **q+y** from
  0.030 em of white to **0.140**, nearly five times any ordinary pair (n+y is
  0.088, o+y 0.062). `('q','y'): 90` in `kern.py` was solved for a tail that
  reaches unit 8; retract the tail and that cell is a hole. Both would need
  re-solving. `Q+y` is unaffected — Q's own tail is the constraint there, not
  the y's.
- **F is the obvious move and it backfires.** Dropping the floor makes the
  letter 54 units deeper overall and the hang under the letter 6 units
  *shallower*, because the extra depth is spent further out to the left. 55 % of
  the descender then lands under the previous letter.
- **`Y_TAIL_DROP 40`**, measured and not laddered: deepest ink 289 → 302, hang
  unchanged at 227, and the share landing left of the origin rises to 59 %. A
  bigger terminal drop is more ink under the *neighbour*.

Every arm passes `cmp_touch.py`: 0 touching, 0 under the 0.012 em floor. The
advance does not move (385 → 384), because `build.py` fits the y's bearings from
ink inside the x-height band and the tail is invisible to it.

## 4. What the dials cannot reach

**Steepening the tail while keeping its reach.** `Y_TAIL_X` and `Y_TAIL_Y` move
only the path's LAST point; the four points between the baseline and the floor —
`(244, −0.15) (210, −0.32) (172, −0.46) (128, −0.55)` — are literals. So the
tail's depth at the moment it leaves the letter's own column is fixed at about
−0.53 xh whatever the dials say, and `Y_TAIL_X` can only buy hang by **giving up
the swash**: at 118 the tail is short, at 170 it hooks back to the right under
the letter and is no longer the reference's shape at all.

The code change that reaches it is one dial and four points. Pull those four
sub-baseline points DOWN toward the floor without moving their x:

```python
_PL = float(os.environ.get("ALBO_ALD_Y_TAIL_PLUNGE", 0.0))
_sub = [(244, -0.15), (210, -0.32), (172, -0.46), (128, -0.55)]
_sub = [(x, y + _PL * (TY - y)) for x, y in _sub]
```

The tail then drops to its floor while it is still under the letter and runs
left along the bottom — which is what Cancelleresca does and what the reach
ruling wants. **Measured, in a scratch copy, not applied:**

| `Y_TAIL_PLUNGE` | hang under the body | leftmost | half its depth by | q+y | touch gate |
|---|---|---|---|---|---|
| 0.00 (= shipped) | 227 | 8 | 33.3 % | 0.030 | clean |
| 0.35 | 241 | 8 | 25.7 % | 0.030 | — |
| 0.60 | 254 | 8 | 23.1 % | 0.030 | clean |
| 0.85 | **268** | 8 | 21.8 % | 0.030 | clean |

At 0.85 it delivers **option D's hang number with the swash intact and every
pair white unchanged** — q+y stays at 0.030, p+y at 0.038, g+y at 0.025, so
nothing needs re-spacing. Verified against the shipped drawing first: the
sandbox at `PLUNGE 0.0` reproduces the shipped `y` outline point for point.

## 5. Recommendation

**Ship the plunge, not the retraction.** Concretely: add `Y_TAIL_PLUNGE` and
ladder 0.45 / 0.60 / 0.75 / 0.85 for the owner to pick from. My own pick off the
four built is **0.60** — 0.85 buys 14 more units of hang and starts to read as a
hook with a horizontal line under it rather than one curve, and this letter has
a standing ruling against serpentines and elbows.

The reason is the cost column, not the hang column. D and E reach the same place
by spending two things the plunge spends nothing of: an owner ruling about the
swash, and the q+y pair. The complaint is that the letter has no ink under
itself; the fix should be to put ink under it, not to take the flourish away.

If the plunge is not wanted, **B is the only option that costs nothing** and it
should be described honestly as a colour change — 7 units of hang will not
answer the report.

## 6. What was checked and found clean

- The y's **top** (441) is inside its neighbours' band. Not the fault.
- The **fork** closes at 31.8, lower than the v's 72.6. Not the fault, and
  `Y_LBOW = 41` is why.
- The tail's **descent profile** matches Cancelleresca's within two points at
  both marks. Round 135 did what it said. Not the fault.
- The **advance** does not move under any arm (385 → 384).
- `cmp_touch.py` is clean on the shipped build, on `X 118`, and on both plunge
  arms: 0 touching, 0 under the floor, 5,193 pairs.
- The **hairline** is 22 units, not the 31 quoted from a stale comment.

## 7. How to re-run this

There is no committed instrument for the y yet — the scripts behind these
numbers were scratch, because this task owned one file. If an option is picked,
they should land as `tools/wedge_serif/cmp_aldine_y.py`, because four of the
seven numbers above were wrong before they were measured. The procedure:

1. render the glyph alone, unsheared about the baseline by the slant measured
   off the `l` stem (two of the four references declare an `italicAngle` that is
   not their own — Cancelleresca says 0 and is plainly slanted), at an x-height
   taken from the `x` glyph's own ink height so every font is normalized the
   same way;
2. **fork** — walking down from mid x-height, the deepest row still carrying two
   ink runs;
3. **hang** — on the SHEARED render with the origin and advance known, the
   deepest ink in the columns the body occupies, and the share of sub-baseline
   ink falling left of the origin;
4. **thickness** — twice the Euclidean distance transform, never a chord;
5. **profile** — the column-by-column depth of the sub-baseline ink, reported as
   the fraction of leftward travel spent by half and four fifths of the depth.
