"""All four styles' spacing on one page, each against its OWN reference set.

Owner 2026-09-19: *"take at least one pass at smart spacing for letters and
words on all fonts."* "All fonts" is now four -- Medium, Italic, Bold,
BoldItalic -- and the three instruments that answer spacing each took one font
and one (italic) reference list. This runs `cmp_space_2d`'s class medians over
every built style, picks the reference set from the style's name (`refsets.py`),
and adds the two derived numbers a WEIGHT question needs:

  BETWEEN / WITHIN -- the lower+lower median gap divided by the `n`'s own
      counter. This is round 3's ruling as a number (*"the distance between
      characters should be the same as within"*) and it is the only spacing
      measure here that a change of weight leaves alone: a bold's counters
      shrink, so a bold that keeps its regular's bearings reads looser on this
      ratio even though not one gap moved. A gap in em cannot see that.

  SPACE / COUNTER -- the word space over the same counter, for the same reason.
      Measured across eleven reference families regular-to-bold, the word space
      over the X-HEIGHT barely moves (0.978-1.057, median 1.00) while this ratio
      climbs by a third, so "a bold wants a wider word space" is FALSE of the
      references in absolute terms and true only relative to the counters.

    PYTHON_GIL=0 python3 cmp_space_all.py <dir-of-built-ttfs>
    PYTHON_GIL=0 python3 cmp_space_all.py <dir> --unit xh
    PYTHON_GIL=0 python3 cmp_space_all.py <dir> --against <other-dir>   # before/after
"""
import argparse, os, sys
import numpy as np
import refsets
from cmp_space_2d import Face, CLASSES, class_medians, LOWER, glyph_sides

STYLES = ["Medium", "Italic", "Bold", "BoldItalic"]


def measure(path, xh=150, unit="em"):
    rset = refsets.pick(path)
    me = Face(path, xh, unit=unit)
    mine = class_medians(me)
    b = refsets.basis(path)
    rows = {}
    for label, p, i in refsets.entries(rset):
        try:
            f = Face(p, xh, index=i, unit=unit)
            rows[label] = (class_medians(f), refsets.basis(p, i))
        except Exception as e:
            print("  (%s: %s %s)" % (label, type(e).__name__, e))
    return dict(set=rset, mine=mine, basis=b, refs=rows, face=me)


def band(refs, key):
    v = [r[0][key][0] for r in refs.values() if r[0][key][0] is not None]
    return (min(v), float(np.median(v)), max(v)) if v else None


def ratio_band(refs, kind):
    out = []
    for cm, bs in refs.values():
        g = cm["lower+lower"][0]
        if g is None or not bs["ctr"]: continue
        # both in the same units: the class median is per em or per xh, the
        # counter is per xh, so the gap is re-expressed per xh first.
        out.append((g, bs))
    return out


def print_style(name, m, unit):
    b = m["basis"]
    print("\n  %s   [refs: %s]   xh %.4f em, stem %.3f xh, n-counter %.3f xh"
          % (name, m["set"], b["xh"], b["stem"] or 0, b["ctr"] or 0))
    print("    %-14s%8s%9s%8s%8s%10s   n" % ("class", "Albo", "ref med", "ref lo", "ref hi", "verdict"))
    for cl in CLASSES:
        v, n = m["mine"][cl]
        row = "    %-14s%8.3f" % (cl, v if v is not None else float("nan"))
        bd = band(m["refs"], cl)
        if bd and v is not None:
            lo, md, hi = bd
            row += "%9.3f%8.3f%8.3f%10s" % (md, lo, hi, "LOOSE" if v > hi else ("tight" if v < lo else "in band"))
        print(row + "   %d" % n)


def derived(name, m):
    """BETWEEN/WITHIN and SPACE/COUNTER for one style against its set."""
    b = m["basis"]
    g = m["mine"]["lower+lower"][0]
    # the class median is in em (Face default) -- put it on the x-height, which
    # is the unit the counter is in, so the ratio is dimensionless either way.
    gx = g / b["xh"] if b["xh"] else None
    bw = gx / b["ctr"] if (gx and b["ctr"]) else None
    sc = b["spctr"]
    rb, rs = [], []
    for cm, bs in m["refs"].values():
        rg = cm["lower+lower"][0]
        if rg and bs["ctr"] and bs["xh"]:
            rb.append((rg / bs["xh"]) / bs["ctr"])
        if bs["spctr"]: rs.append(bs["spctr"])
    def fmt(v, arr):
        if v is None or not arr: return "%8s%9s%8s%8s%10s" % ("--", "--", "--", "--", "--")
        lo, md, hi = min(arr), float(np.median(arr)), max(arr)
        return "%8.3f%9.3f%8.3f%8.3f%10s" % (v, md, lo, hi, "LOOSE" if v > hi else ("tight" if v < lo else "in band"))
    print("    %-14s" % "between/within" + fmt(bw, rb))
    print("    %-14s" % "space/counter" + fmt(sc, rs))
    print("    %-14s%8.3f" % ("space (xh)", b["space"]) +
          "%9.3f%8.3f%8.3f" % ((lambda a: (float(np.median(a)), min(a), max(a)))(
              [bs["space"] for _, bs in m["refs"].values()])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--against", help="a second directory: print BEFORE -> AFTER")
    ap.add_argument("--unit", default="em", choices=["em", "xh"])
    ap.add_argument("--xh", type=int, default=150)
    ap.add_argument("--sides", action="store_true", help="also per-lowercase-letter sides")
    a = ap.parse_args()

    for st in STYLES:
        p = os.path.join(a.dir, "Albo-%s.ttf" % st)
        if not os.path.exists(p): continue
        m = measure(p, a.xh, a.unit)
        print_style("Albo-" + st, m, a.unit)
        derived("Albo-" + st, m)
        if a.against:
            q = os.path.join(a.against, "Albo-%s.ttf" % st)
            if os.path.exists(q):
                n = measure(q, a.xh, a.unit)
                print("    %-14s%8s%9s" % ("(was)", "", ""))
                for cl in CLASSES:
                    v0, _ = n["mine"][cl]; v1, _ = m["mine"][cl]
                    if v0 is None or v1 is None: continue
                    print("      %-12s%8.3f -> %.3f  %+0.3f" % (cl, v0, v1, v1 - v0))
        if a.sides:
            s = glyph_sides(m["face"], list(LOWER))
            print("    per-letter sides (its right / its left), em:")
            for ch in sorted(s):
                print("      %s  %.3f  %.3f" % (ch, s[ch][0], s[ch][1]))
            R = [v[0] for v in s.values()]; L = [v[1] for v in s.values()]
            print("      spread: right %.3f-%.3f (%.2fx), left %.3f-%.3f (%.2fx)"
                  % (min(R), max(R), max(R) / min(R), min(L), max(L), max(L) / min(L)))
    print()


if __name__ == "__main__":
    sys.exit(main())
