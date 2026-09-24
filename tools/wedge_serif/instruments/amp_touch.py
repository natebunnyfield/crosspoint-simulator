"""The '&' against every letter, figure and mark, both orders -- round 377.

cmp_touch.py's charset is A-Z a-z 0-9 and . , ; : ! ? ' " ( ) - -- it has no
'&', so the touching gate says nothing at all about the ampersand. This is the
same arithmetic (cmp_touch.profiles, the SHAPED advance so the kern is in it,
the same 0.012 em floor) with '&' added to one side of every pair.

    PYTHON_GIL=0 python3 instruments/amp_touch.py FONT.ttf [--floor 0.012]
"""
import argparse, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cmp_touch import profiles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ttf"); ap.add_argument("--floor", type=float, default=0.012)
    ap.add_argument("--xh", type=int, default=300); ap.add_argument("--top", type=int, default=6)
    a = ap.parse_args()
    others = ([chr(c) for c in range(65, 91)] + [chr(c) for c in range(97, 123)]
              + list("0123456789") + list(".,;:!?'\"()- "))[:-1]
    chars = others + ["&"]
    prof, fnt, size = profiles(a.ttf, chars, a.xh)
    rows = []
    for x, y in [("&", o) for o in others] + [(o, "&") for o in others]:
        if x not in prof or y not in prof: continue
        rx, _ = prof[x]; _, ly = prof[y]
        off = fnt.getlength(x + y) - fnt.getlength(y)
        both = ~np.isnan(rx) & ~np.isnan(ly)
        if not both.any(): continue
        rows.append((float(np.min((off + ly[both]) - rx[both]) / size), x + y))
    rows.sort()
    bad = [r for r in rows if r[0] < a.floor]
    for g, p in rows[:a.top]:
        print(f"  {p:4}{g:10.4f}{'   <-- TOUCHING' if g <= 0 else ('   <-- under floor' if g < a.floor else '')}")
    print(f"{len(rows)} '&' pairs; {sum(1 for r in bad if r[0] <= 0)} touching, "
          f"{len(bad)} below {a.floor} em")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
