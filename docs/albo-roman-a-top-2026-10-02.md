# The roman a's top stroke and its eye, as options (2026-10-02)

Owner todo, 2026-10-01: *"raise just the top stroke of roman 'a' so it
matches the same x height and interior spacing of others"*. Then 2026-10-02:
*"show me improved roman 'a'"*.

**Status: OPTIONS, awaiting a pick.** Nothing shipped. The dials are in
`outlines/glyphs/stems.py` (the `A_RISE` / `A_LIFT` / `A_BOWL_TOP` block
above `g_a`), and all default to today's letter.

- **Surveyed:** build 282.
- **Instrument:** `tools/wedge_serif/instruments/a_roman_top.py`.
- **Proof tool:** `instruments/a_arms.py`.

## 1. What was measured

The tops are ink tops. The eye is the white between the a's top stroke and
its bowl: a vertical run at 30% of the ink width, from the bowl's top edge up
to the hood's underside. The e's eye is the same white between its bar and
its top arc, at its center column. The counters are vertical, at center.
Everything is in units at Albo's o height, 444.

| face | a top / o top | a eye / e eye | a counter / o counter |
|---|---|---|---|
| **Albo Regular** | **433 / 444** | **0.67** | **0.50** |
| **Albo Bold** | **438 / 444** | **0.68** | **0.41** |
| Georgia | 444 / 444 | 1.20 | 0.35 |
| Charter | 444 / 444 | 1.26 | 0.38 |
| Palatino | 441 / 444 | 0.93 | 0.38 |
| Hoefler Text | 444 / 444 | 1.58 | 0.31 |
| Baskerville | 444 / 444 | 1.63 | 0.39 |
| Big Caslon | 444 / 444 | 1.56 | 0.29 |
| Iowan | 445 / 444 | 1.39 | 0.33 |
| Pagella | 444 / 444 | 0.93 | 0.38 |
| Albertus | 444 / 444 | 1.40 | 0.22 |

Two faults, and the second one is the larger:

- **Height.** The a stops 11 units under its own o in the Regular, and 6
  in the Bold. Every reference's a reaches its o, Palatino within 3.
- **The eye.** Albo's eye is two thirds of its own e's eye. In every
  reference it is at least 0.93 of the e's, and in most it is larger. The
  cause is the bowl: it rises to 0.60 of the x-height, and its counter is
  half the o's, where the references hold 0.22 to 0.39.

**Raising the top stroke alone cannot close the eye gap.** Matching even the
lowest reference (0.93) by that route needs the eye to grow about 40 units,
and the top stroke can rise only 11 before it passes the x-line. So the
eye-matching options also lower where the bowl meets the stem.

## 2. History

**2026-09-27** (`docs/albo-poor-characters-2026-09-26.md`, "Roman a
height"): the crown raised to the o (H1, `A_RISE` 14 / 8) and three widths
were shown. The ruling was **"A, as is"**. The 2026-10-01 todo reopens the
height and adds the interior.

## 3. The options

| label | what moves | env | a top (R / B) | eye a/e (R / B) | counter a/o (R / B) |
|---|---|---|---|---|---|
| today | -- | -- | 433 / 438 | 0.67 / 0.68 | 0.50 / 0.41 |
| **T1** | the top stroke's crown, bent up; terminal kept (2026-09-27's H1) | `ALBO_ROM_A_RISE=14 ALBO_ROM_A_RISE_700=8` | 444 / 444 | 0.72 / 0.70 | 0.50 / 0.41 |
| **T2** | the whole top stroke lifted as one piece (crown, underside, terminal), the stem carried up under it | `ALBO_ROM_A_LIFT=10 ALBO_ROM_A_LIFT_700=6` | 444 / 444 | 0.74 / 0.72 | 0.50 / 0.41 |
| **T3** | T2, and the bowl meets the stem at 0.50 xh (today 0.60) | T2 + `ALBO_ROM_A_BOWL_TOP=0.50 ALBO_ROM_A_BOWL_TOP_700=0.50` | 444 / 444 | 0.85 / 0.86 | 0.47 / 0.38 |
| **T4** | T2, and the bowl at 0.42 xh (Bold 0.45) | T2 + `ALBO_ROM_A_BOWL_TOP=0.42 ALBO_ROM_A_BOWL_TOP_700=0.45` | 444 / 444 | 0.94 / 0.92 | 0.44 / 0.37 |

T1 and T2 are the ask as written: just the top stroke. T3 and T4 also lower
the bowl's top, which is the only way to reach the references' interior
spacing (T4 lands on their lowest ratio, Palatino's and Pagella's 0.93).

The Bold's bowl is lowered less at T4, to 0.45 rather than 0.42. Its counter
is already small (0.41 of the o's), and at 0.42 it read as a slot.

## 4. Gates (each arm against build 282, Regular and Bold)

- **POOR GATES: no delta**, all four arms: hairs (letters and full), touch,
  counter dents, glitch, contour census, approved letters, e mouth.
- **What moves:** a, its accented forms, æ and ª.
- **A note on ą:** `cmp_outlines.py` compares a composite by its components
  and their offsets. ą (a + ogonek) reads as unmoved in the Regular T3,
  though it carries the new a: its ogonek offset happened not to change.

## 5. Reproduce

    cd tools/wedge_serif; source build_env.sh
    env "${ALBO_ROM_ENV[@]}" ALBO_ROM_A_LIFT=10 ALBO_ROM_A_BOWL_TOP=0.50 PYTHON_GIL=0 python3 -m outlines.build OUT --style Regular
    env "${ALBO_BLD_ENV[@]}" ALBO_ROM_A_LIFT_700=6 ALBO_ROM_A_BOWL_TOP_700=0.50 PYTHON_GIL=0 python3 -m outlines.build OUT --style Bold
    $VENV/bin/python instruments/a_roman_top.py OUT            # and --refs for the table above
    $VENV/bin/python instruments/a_arms.py proof PROOF today=T T1=A1 ...

Proof page: https://claude.ai/artifact/87rfCQ9xb8LNRBuxCZiCDM
