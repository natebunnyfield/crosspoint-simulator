#!/usr/bin/env python3
"""Every glyph's CONTOUR COUNT, as a reviewable baseline.

WHY THIS EXISTS. `outlines/cut.py`'s `Cutter` keeps `self.n`, a running
counter advanced once per contour, and each contour's decimation phase is
`Random(seed * 7919 + n)`. So a glyph whose CONTOUR COUNT changes shifts the
cut phase of every glyph built after it. On 2026-09-21 shipping the ruled
italic ampersand moved **169 other glyphs** in both styles for that reason,
and the diff had to be chased to the bottom before a one-glyph change could be
trusted. An ordinary ampersand swap moves exactly one glyph, because its
contour count is unchanged.

Owner ruling 2026-09-21, offered the choice between re-seeding the cutter per
glyph and gating it: **gate it, do not change the drawing.** Re-seeding would
re-cut all 493 glyphs in both styles, moving the deliberate irregularities on
every letter he has already judged.

So the ripple is not prevented; it is made LOUD. A change here is expected
and fine -- it just has to be a reviewable commit rather than a surprise in
someone else's diff, exactly as `gates-baseline.txt` and `approved.json` are.

    python3 cmp_contours.py --check  --regular R.ttf --italic I.ttf
    python3 cmp_contours.py --accept --regular R.ttf --italic I.ttf
    python3 cmp_contours.py R.ttf                      # just print the census

`--check` exits 1 when any glyph's contour count differs from the baseline,
naming each one and saying how many glyphs are built after it (which is how
many the cut phase will have moved).
"""
import argparse, os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, "contours-baseline.txt")


class _Count(BasePen):
    """Counts closed contours on the DECOMPOSED glyph, so a composite is
    counted as the outlines it actually draws rather than as its components."""
    def __init__(self, gs):
        BasePen.__init__(self, gs)
        self.n = 0
    def _moveTo(self, p): pass
    def _lineTo(self, p): pass
    def _curveToOne(self, a, b, c): pass
    def _closePath(self): self.n += 1
    def _endPath(self): self.n += 1


def census(path):
    f = TTFont(path)
    gs = f.getGlyphSet()
    out = {}
    for name in f.getGlyphOrder():
        p = _Count(gs)
        try:
            gs[name].draw(p)
        except Exception:
            continue
        if p.n:
            out[name] = p.n
    return out, f.getGlyphOrder()


def lines(style, path):
    c, _ = census(path)
    return [f"{style} {n} {c[n]}" for n in sorted(c)]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ttf", nargs="?")
    ap.add_argument("--regular")
    ap.add_argument("--italic")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--accept", action="store_true")
    a = ap.parse_args()

    if a.ttf and not (a.check or a.accept):
        for ln in lines("Font", a.ttf):
            print(ln)
        return 0
    if not (a.regular and a.italic):
        ap.error("--check/--accept need --regular and --italic")

    now = lines("Regular", a.regular) + lines("Italic", a.italic)
    if a.accept:
        with open(BASELINE, "w") as fh:
            fh.write("\n".join(now) + "\n")
        print(f"contour census written to {os.path.basename(BASELINE)} ({len(now)} glyphs)")
        return 0
    if not os.path.exists(BASELINE):
        print("no contours-baseline.txt yet -- run --accept once, review it, and commit it")
        return 2

    want = [l.rstrip("\n") for l in open(BASELINE) if l.strip()]
    wd = {" ".join(l.split()[:2]): int(l.split()[2]) for l in want}
    nd = {" ".join(l.split()[:2]): int(l.split()[2]) for l in now}
    order = {"Regular": [l.split()[1] for l in now if l.startswith("Regular ")],
             "Italic": [l.split()[1] for l in now if l.startswith("Italic ")]}
    bad = []
    for k in sorted(set(wd) | set(nd)):
        if wd.get(k) != nd.get(k):
            bad.append((k, wd.get(k), nd.get(k)))
    if not bad:
        print(f"contour census unchanged ({len(now)} glyphs)")
        return 0
    print("CONTOUR COUNT CHANGED -- every glyph built AFTER one of these will")
    print("have been re-cut, because cut.py's phase counter advances per contour:")
    for k, w, n in bad:
        style, name = k.split()
        after = 0
        if name in order.get(style, []):
            after = len(order[style]) - order[style].index(name) - 1
        print(f"  {style:8s} {name:16s} {w} -> {n}"
              f"   ({after} glyph(s) built after it in this style)")
    print("\nIf the change is intended, rerun with --accept and COMMIT the new")
    print("baseline with the reason. See this file's header for why.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
