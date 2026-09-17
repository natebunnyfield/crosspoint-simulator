"""How evenly does the Aldine italic fit? Every lowercase letter, both sides.

Round 197. The standing brief is the WORD IMAGE, so the test is not a
sidebearing number but the WHITE a reader sees between two letters. For each
letter x this measures the minimum white in `nx`, `ox` (its left side) and
`xn`, `xo` (its right), on the SHAPED pair so the kern table is in it.

MEASURED THE WAY `cmp_touch` MEASURES, and the first cut of this file was not:
it rendered the pair as one string and split the raster at the advance. On a
13-degree face the glyphs overlap horizontally, so that split hands part of the
second letter to the first and reports a near-zero gap -- it read 0.0014 em for
half the alphabet while the touch gate, correctly, reported nothing under
0.012. Per-glyph edge profiles, offset by the shaped advance, is the only sound
way; there is no raster of the pair at all.

A letter is out of line when its white differs from the alphabet's median by
more than --tol. The suggested deltas are in design units, which is what the
glyph code takes.

    PYTHON_GIL=0 python3 cmp_italic_space.py <font.ttf> [--tol 0.010]
"""
import argparse, sys
import numpy as np
from PIL import ImageFont
from fontTools.ttLib import TTFont
from cmp_touch import profiles

LOWER = "abcdefghijklmnopqrstuvwxyz"
NEIGH = ("n", "o")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ttf")
    ap.add_argument("--tol", type=float, default=0.010)
    ap.add_argument("--xh", type=int, default=300)
    a = ap.parse_args()

    chars = sorted(set(LOWER) | set(NEIGH))
    prof, fnt, size = profiles(a.ttf, chars, a.xh)

    def white(x, y):
        if x not in prof or y not in prof: return None
        rx, _ = prof[x]; _, ly = prof[y]
        off = fnt.getlength(x + y) - fnt.getlength(y)
        both = ~np.isnan(rx) & ~np.isnan(ly)
        if not both.any(): return None
        return float(np.min((off + ly[both]) - rx[both]) / size)

    rows = []
    for ch in LOWER:
        L = [white(n, ch) for n in NEIGH]
        R = [white(ch, n) for n in NEIGH]
        L = [v for v in L if v is not None]; R = [v for v in R if v is not None]
        if not L or not R: continue
        rows.append((ch, sum(L) / len(L), sum(R) / len(R)))
    if not rows: sys.exit("no measurements")

    ml = float(np.median([r[1] for r in rows]))
    mr = float(np.median([r[2] for r in rows]))
    print("  %d letters at a %d px x-height; median white  left %.4f em  right %.4f em"
          % (len(rows), a.xh, ml, mr))
    print("\n   ch    left     right      off L     off R    suggested (units/1000)")
    bad = 0
    for ch, l, r in sorted(rows, key=lambda t: -(abs(t[1] - ml) + abs(t[2] - mr))):
        dl, dr = l - ml, r - mr
        flag = "  <--" if (abs(dl) > a.tol or abs(dr) > a.tol) else ""
        if flag: bad += 1
        print("   %s   %.4f   %.4f   %+7.4f  %+7.4f   %+5.0f %+5.0f%s"
              % (ch, l, r, dl, dr, -dl * 1000, -dr * 1000, flag))
    print("\n  %d letter(s) more than %.3f em from the median." % (bad, a.tol))
    return 0


if __name__ == "__main__":
    sys.exit(main())
