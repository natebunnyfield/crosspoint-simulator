"""Every pair, every class, measured as the CLOSEST APPROACH IN TWO DIMENSIONS,
against the faces that are fitted.

Owner 2026-09-18: *"take a pass at all spacing including 'apostrophe s'."*

WHY A THIRD GAP MEASURE. `cmp_touch.py` (minimum white) and `cmp_figure_space.py
--body` (the body-edge gap) both walk the rows the two glyphs SHARE. An
apostrophe and an s share none -- the mark sits entirely above the x-height --
so both returned n/a for exactly the pair the owner named, and round 220 judged
the quotes "in band" on `s'` while never once measuring `'s`. The gap a reader
sees between a high mark and a low letter is DIAGONAL; this measures it as the
nearest distance between the first glyph's right ink boundary and the second's
left, on the SHAPED pair (kern table included), in em.

WHAT A CLASS IS. A sidebearing is a property of a letter, and a letter's two
sides are two properties (round 211: the o's left was right and its right was
wrong). So the ledger is by CLASS and SIDE -- lowercase after lowercase,
capital before lowercase, quote before letter, letter before stop... -- and a
class is judged by its MEDIAN against the seven references' medians. A single
pair is a kern; a class is a bearing.

WHICH REFERENCES. Not a list in this file any more: `refsets.py` holds four
sets -- roman, italic, bold, bolditalic -- and the set is chosen from the built
font's NAME unless `--set` says otherwise. The seven italics are unchanged and
in their original order, so every number in docs/albo-spacing-method.md stays
comparable; the other three sets are new on 2026-09-19 and close the hole
docs/albo-misfit-audit-2026-09-18.md §d names, which is that a roman was being
judged against italics. Read `refsets.py`'s header before trusting a bold band:
Albo's Bold is a 1.30 weight ratio where the references' are 1.39-2.29.

    PYTHON_GIL=0 python3 cmp_space_2d.py <built>/Albo-Italic.ttf
    PYTHON_GIL=0 python3 cmp_space_2d.py <ttf> --refs            # the reference band
    PYTHON_GIL=0 python3 cmp_space_2d.py <ttf> --refs --set bold # force a set
    PYTHON_GIL=0 python3 cmp_space_2d.py <ttf> --refs --unit xh  # per x-height, not per em
    PYTHON_GIL=0 python3 cmp_space_2d.py <ttf> --pairs "'s 't 'c s' o. ,a"
    PYTHON_GIL=0 python3 cmp_space_2d.py <ttf> --per-glyph quotes # each mark's own two sides
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
import refsets

HERE = os.path.dirname(os.path.abspath(__file__))
LOWER = "aeinorstuvxhldmgpc"          # the frequent lowercase, both sides
UPPER = "AEHNOTRSLVW"
DIGIT = "0123456789"
STOPS = ".,;:!?"
QUOTES = ["’", "‘", "'", "”", "“", '"']
CLASSES = {                           # name: (lefts, rights)
    "lower+lower": (LOWER, LOWER),
    "cap+lower":   (UPPER, LOWER),
    "cap+cap":     (UPPER, UPPER),
    "digit+digit": (DIGIT, DIGIT),
    "letter+stop": (LOWER, STOPS),
    "stop+letter": (STOPS, LOWER),
    "letter+quote": (LOWER, QUOTES),
    "quote+letter": (QUOTES, LOWER),
}


class Face:
    def __init__(self, path, xh=150, index=0, unit="em"):
        self.path = path
        f = TTFont(path, fontNumber=index) if path.lower().endswith(".ttc") else TTFont(path)
        # THE X-HEIGHT IS MEASURED, NOT DECLARED. `OS/2.sxHeight` is absent in
        # Charter and Iowan, zero in New York and wrong by 34% in Poetica --
        # see refsets.py's header. It only sizes the raster (every number here
        # is per-em), but a face rendered 52% off its asked-for size quantises
        # its gaps on a different grid from what it is compared with.
        self.xh_em = refsets.measure_xh(path, index)
        self.size = int(round(xh / self.xh_em))
        self.fnt = ImageFont.truetype(path, self.size, index=index)
        self.cmap = f.getBestCmap()
        # `em` keeps every published number comparable; `xh` is the unit a
        # reader actually sees, since these faces' x-heights run 0.395-0.481 em.
        self.denom = self.size if unit == "em" else self.size * self.xh_em
        self.W = self.H = self.size * 4
        self.ox, self.oy = self.size, int(self.size * 2.4)
        self._edge = {}

    def has(self, ch): return ord(ch) in self.cmap

    def _ink(self, txt, dx=0.0):
        im = Image.new("L", (self.W, self.H), 255)
        ImageDraw.Draw(im).text((self.ox + dx, self.oy), txt, font=self.fnt, fill=0, anchor="ls")
        return np.asarray(im) < 128

    def edges(self, ch):
        """(right boundary points, left boundary points) of one glyph at the origin."""
        if ch in self._edge: return self._edge[ch]
        M = self._ink(ch)
        if not M.any(): self._edge[ch] = None; return None
        R, L = [], []
        for y in np.nonzero(M.any(1))[0]:
            xs = np.nonzero(M[y])[0]; R.append((xs.max(), y)); L.append((xs.min(), y))
        self._edge[ch] = (np.array(R, float), np.array(L, float))
        return self._edge[ch]

    def gap(self, a, b):
        if not (self.has(a) and self.has(b)): return None
        ea, eb = self.edges(a), self.edges(b)
        if ea is None or eb is None: return None
        off = self.fnt.getlength(a + b) - self.fnt.getlength(b)
        P = ea[0]; Q = eb[1].copy(); Q[:, 0] += off
        d = np.sqrt((P[:, None, 0] - Q[None, :, 0]) ** 2 + (P[:, None, 1] - Q[None, :, 1]) ** 2)
        return float(d.min() / self.denom)


def class_medians(face):
    out = {}
    for name, (ls, rs) in CLASSES.items():
        v = [g for a in ls for b in rs if (g := face.gap(a, b)) is not None]
        out[name] = (float(np.median(v)) if v else None, len(v))
    return out


def glyph_sides(face, chars):
    """For each glyph: its median white as the LEFT of a pair (i.e. its own
    right side) and as the RIGHT (its own left side), against the lowercase."""
    out = {}
    for ch in chars:
        R = [g for b in LOWER if (g := face.gap(ch, b)) is not None]
        L = [g for x in LOWER if (g := face.gap(x, ch)) is not None]
        if R and L: out[ch] = (float(np.median(R)), float(np.median(L)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ttf")
    ap.add_argument("--refs", action="store_true")
    ap.add_argument("--set", dest="rset", default="auto",
                    choices=["auto", "roman", "italic", "bold", "bolditalic"],
                    help="which reference set (default: from the font's name)")
    ap.add_argument("--unit", default="em", choices=["em", "xh"])
    ap.add_argument("--pairs", help="space-separated pairs to print individually")
    ap.add_argument("--per-glyph", choices=["quotes", "stops", "lower", "upper"],
                    help="each glyph of that set: its median white as LEFT of a pair and as RIGHT")
    ap.add_argument("--xh", type=int, default=150)
    a = ap.parse_args()

    rset = refsets.pick(a.ttf) if a.rset == "auto" else a.rset
    me = Face(a.ttf, a.xh, unit=a.unit)
    print(f"\n{os.path.basename(a.ttf)} -- closest approach in 2-D, {a.unit}, at a {a.xh} px x-height"
          f"  [refs: {rset}]\n")
    mine = class_medians(me)
    refs, rfaces = [], []
    if a.refs:
        for n, p, i in refsets.entries(rset):
            try:
                f = Face(p, a.xh, index=i, unit=a.unit)
                rfaces.append((n, f)); refs.append((n, class_medians(f)))
            except Exception as e: print(f"  ({n}: {type(e).__name__} {e})")
    print(f"  {'class':14}{'Albo':>8}" + (f"{'ref med':>9}{'ref lo':>8}{'ref hi':>8}{'verdict':>10}" if refs else "") + "   n")
    for name in CLASSES:
        m, n = mine[name]
        row = f"  {name:14}{(m if m is not None else float('nan')):8.3f}"
        if refs:
            rv = [r[name][0] for _, r in refs if r[name][0] is not None]
            if rv:
                lo, hi, md = min(rv), max(rv), float(np.median(rv))
                verdict = "LOOSE" if m > hi else ("tight" if m < lo else "in band")
                row += f"{md:9.3f}{lo:8.3f}{hi:8.3f}{verdict:>10}"
        print(row + f"   {n}")

    if a.per_glyph:
        sets = {"quotes": QUOTES, "stops": list(STOPS), "lower": list(LOWER), "upper": list(UPPER)}[a.per_glyph]
        mySide = glyph_sides(me, sets)
        rSide = [glyph_sides(f, sets) for _, f in rfaces]
        print(f"\n  each {a.per_glyph} glyph: median white as the LEFT of a pair (its right side) and as the RIGHT (its left side)")
        hdr = f"    {'glyph':8}{'its right':>11}{'its left':>10}"
        if rSide: hdr += f"{'ref R':>9}{'ref L':>9}{'dR':>8}{'dL':>8}"
        print(hdr)
        for ch in sets:
            if ch not in mySide: continue
            R, L = mySide[ch]
            row = f"    {repr(ch):8}{R:11.3f}{L:10.3f}"
            if rSide:
                rr = [d[ch][0] for d in rSide if ch in d]; rl = [d[ch][1] for d in rSide if ch in d]
                if rr and rl:
                    mr, ml = float(np.median(rr)), float(np.median(rl))
                    row += f"{mr:9.3f}{ml:9.3f}{R - mr:+8.3f}{L - ml:+8.3f}"
            print(row)

    if a.pairs:
        print()
        faces = [("Albo", me)] + (rfaces if a.refs else [])
        prs = a.pairs.split()
        print(f"  {'face':20}" + "".join(f"{p:>8}" for p in prs))
        for n, f in faces:
            print(f"  {n:20}" + "".join((f"{g:8.3f}" if (g := f.gap(p[0], p[1])) is not None else "     n/a") for p in prs))
        if a.refs and len(faces) > 1:
            print(f"  {'ref median':20}" + "".join(
                (f"{np.median(v):8.3f}" if (v := [g for _, f in rfaces if (g := f.gap(p[0], p[1])) is not None]) else "     n/a")
                for p in prs))
    print()


if __name__ == "__main__":
    sys.exit(main())
