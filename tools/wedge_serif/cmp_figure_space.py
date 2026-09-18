"""The hundred figure pairs, measured against the faces that fit figures well.

Owner 2026-09-18: *"correct numeral spacing."*

METHOD is `cmp_touch.py`'s, and its `profiles` is imported rather than copied:
each glyph is rendered once and reduced to a left and a right ink profile, and
a pair's minimum white is arithmetic on two profiles plus the pair's SHAPED
advance -- so the kern table is in every number. White is in em.

WHY A REFERENCE BAND AND NOT A TARGET. Figures are not letters: a run of them
is read as a column of digits rather than as a word image, so the eye is far
more sensitive to one gap being wider than its neighbours than to the whole set
being loose or tight. The fault this looks for is therefore SPREAD -- the
difference between a face's widest and tightest figure pair -- and not the
median, which is a tracking choice. `--spread` is the ratio a face is allowed
between its 90th and 10th percentile pair before it is called uneven, and its
default of 2.5 is set FROM the references rather than chosen: on the body-edge
measure they run Poetica 1.78, Coelacanth 1.84, Times 2.40, New York 2.42,
Pagella 2.52, Georgia 2.55 and Flanker 5.58. A gate most good faces fail is not
a gate. Albo's italic reads 1.31 after round 216 and 2.03 before it.

    PYTHON_GIL=0 python3 cmp_figure_space.py <built>/Albo-Italic.ttf
    PYTHON_GIL=0 python3 cmp_figure_space.py <ttf> --refs --top 14
"""
import argparse, os, sys
import numpy as np
from PIL import ImageFont
from cmp_touch import profiles

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = [
    ("Flanker Griffo it", os.path.join(HERE, "refs", "flanker-griffo-italic.otf")),
    ("Pagella it",        os.path.join(HERE, "refs", "texgyrepagella-italic.otf")),
    ("Poetica",           os.path.join(HERE, "refs", "poetica-std-regular.otf")),
    ("Coelacanth it",     os.path.join(HERE, "refs", "coelacanth-italic.otf")),
    ("Times",             "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf"),
    ("Georgia",           "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"),
    ("New York",          "/System/Library/Fonts/NewYorkItalic.ttf"),
]
D = list("0123456789")


def body_edges(prof, q=80):
    """Each glyph's edge where it STANDS rather than where it REACHES --
    docs/albo-spacing-method.md measure 3, the one that survived. A percentile
    of the ink over the rows the glyph occupies: the qth for the right edge,
    the (100-q)th for the left. What the extreme reaches past that is the
    glyph's OWN white and belongs to the glyph, not to the gap -- which is the
    whole reason the italic's tailed figures measure loose on min white."""
    out = {}
    for ch, (r, l) in prof.items():
        rr = r[~np.isnan(r)]; ll = l[~np.isnan(l)]
        out[ch] = (float(np.percentile(rr, q)), float(np.percentile(ll, 100 - q)),
                   float(rr.max()), float(ll.min()))
    return out


def pairs(ttf, xh=300, chars=None, body=False, q=80):
    chars = chars or D
    prof, fnt, size = profiles(ttf, chars, xh)
    have = [c for c in chars if c in prof]
    out = {}
    lenb = {y: fnt.getlength(y) for y in have}
    be = body_edges(prof, q) if body else None
    for x in have:
        rx, _ = prof[x]
        for y in have:
            _, ly = prof[y]
            off = fnt.getlength(x + y) - lenb[y]
            if body:
                out[(x, y)] = float((off + be[y][1]) - be[x][0]) / size
                continue
            both = ~np.isnan(rx) & ~np.isnan(ly)
            if not both.any():
                continue
            out[(x, y)] = float(np.min((off + ly[both]) - rx[both]) / size)
    return out


def own_white(ttf, chars=None, xh=300, q=80):
    """How far past its body edge each glyph reaches, in em, per side."""
    prof, fnt, size = profiles(ttf, chars or D, xh)
    be = body_edges(prof, q)
    return {ch: ((v[2] - v[0]) / size, (v[1] - v[3]) / size) for ch, v in be.items()}


def stats(g):
    v = np.array(sorted(g.values()))
    p10, p90 = float(np.percentile(v, 10)), float(np.percentile(v, 90))
    return dict(n=len(v), lo=float(v.min()), p10=p10, med=float(np.median(v)),
                p90=p90, hi=float(v.max()), spread=(p90 / p10 if p10 > 0 else float("inf")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ttf")
    ap.add_argument("--xh", type=int, default=300)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--refs", action="store_true", help="also measure the reference faces")
    ap.add_argument("--spread", type=float, default=2.5, help="allowed p90/p10 ratio")
    ap.add_argument("--per-digit", action="store_true", help="each digit's mean white, left and right")
    ap.add_argument("--body", action="store_true", help="body-edge gap (spacing-method measure 3) instead of min white")
    ap.add_argument("--own", action="store_true", help="print how much open white each digit owns")
    a = ap.parse_args()

    g = pairs(a.ttf, a.xh, body=a.body)
    s = stats(g)
    print(f"\n{os.path.basename(a.ttf)} -- {s['n']} figure pairs at a {a.xh} px x-height, white in em\n")
    print(f"  tightest {s['lo']:.4f}   p10 {s['p10']:.4f}   median {s['med']:.4f}"
          f"   p90 {s['p90']:.4f}   widest {s['hi']:.4f}   SPREAD {s['spread']:.2f}x")

    order = sorted(g.items(), key=lambda kv: kv[1])
    print(f"\n  tightest {a.top}" + " " * 12 + f"widest {a.top}")
    for i in range(a.top):
        (lx, ly), lv = order[i]
        (rx, ry), rv = order[-1 - i]
        print(f"    {lx}{ly}  {lv:8.4f}" + " " * 12 + f"{rx}{ry}  {rv:8.4f}")

    if a.per_digit:
        print("\n  each digit's mean white, as the LEFT of a pair and as the RIGHT")
        print(f"    {'digit':6}{'right flank':>13}{'left flank':>12}")
        for d in D:
            R = [v for (x, y), v in g.items() if x == d]
            L = [v for (x, y), v in g.items() if y == d]
            if R and L:
                print(f"    {d:6}{np.mean(R):13.4f}{np.mean(L):12.4f}")

    if a.own:
        ow = own_white(a.ttf, xh=a.xh)
        print("\n  open white each digit OWNS, past its body edge (em)")
        print(f"    {'digit':6}{'right':>9}{'left':>9}")
        for d in D:
            if d in ow: print(f"    {d:6}{ow[d][0]:9.4f}{ow[d][1]:9.4f}")

    if a.refs:
        print("\n  the same measurement on faces that fit figures well\n")
        print(f"    {'face':20}{'p10':>9}{'median':>9}{'p90':>9}{'spread':>9}")
        for name, path in REFS:
            if not os.path.exists(path):
                print(f"    {name:20}   (not installed)"); continue
            try:
                t = stats(pairs(path, a.xh, body=a.body))
            except Exception as e:
                print(f"    {name:20}   ({type(e).__name__})"); continue
            print(f"    {name:20}{t['p10']:9.4f}{t['med']:9.4f}{t['p90']:9.4f}{t['spread']:9.2f}x")

    print()
    if s["spread"] > a.spread:
        print(f"  UNEVEN: p90/p10 is {s['spread']:.2f}x, over the {a.spread:.2f}x allowed.")
        return 1
    print(f"  even: p90/p10 is {s['spread']:.2f}x, within the {a.spread:.2f}x allowed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
