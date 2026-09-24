#!/usr/bin/env python3
"""Round 379: cmp_touch.py's sweep over the GREEK -- which that gate does not
reach (it walks A-Z a-z 0-9 and eleven marks). Every Greek letter against
every Greek letter, and each against the Latin lowercase in both orders, on
the SHAPED pair (kern table in), with cmp_touch's own profiles and floor.

    PYTHON_GIL=0 python3 instruments/greek376_touch.py FONT.ttf [--floor 0.012]

Exit 1 on any pair below the floor. Same row-wise blind spot as cmp_touch:
a thin stroke that passes a later glyph on rows the later glyph also
occupies reads as a collision; look at the pair before acting on it.
"""
import os, sys, argparse
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from cmp_touch import profiles

GREEK = "αβγδεζηθικλμνξοπρσςτυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
LATIN = "abcdefghijklmnopqrstuvwxyz"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ttf"); ap.add_argument("--floor", type=float, default=0.012)
    ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args()
    prof, fnt, size = profiles(a.ttf, GREEK + LATIN, 300)
    pairs = [(x, y) for x in GREEK for y in GREEK] + [(x, y) for x in GREEK for y in LATIN] + \
            [(x, y) for x in LATIN for y in GREEK]
    rows = []
    for x, y in pairs:
        if x not in prof or y not in prof: continue
        rx, _ = prof[x]; _, ly = prof[y]
        off = fnt.getlength(x + y) - fnt.getlength(y)
        both = ~np.isnan(rx) & ~np.isnan(ly)
        if not both.any(): continue
        rows.append((float(np.min((off + ly[both]) - rx[both]) / size), x, y))
    rows.sort()
    bad = [r for r in rows if r[0] < a.floor]
    print(f"{os.path.basename(a.ttf)}: {len(rows)} Greek pairs swept, floor {a.floor} em; "
          f"{sum(1 for r in bad if r[0] <= 0)} touching, {len(bad)} below the floor")
    for g, x, y in rows[:a.top]:
        print(f"  {x+y}  {g:+.4f}" + ("   <-- TOUCHING" if g <= 0 else ("   <-- under the floor" if g < a.floor else "")))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
