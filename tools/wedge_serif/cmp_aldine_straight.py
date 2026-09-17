"""Every PERFECTLY STRAIGHT edge in the Aldine italic, measured.

Owner 2026-09-16: *"find any perfectly straight lines in italic letters and
make those characters handcut"*. This is the FINDING half -- a read-only sweep
that says which letters have a dead straight run in their outline and how long
it is, so the drawing work has a list instead of an impression.

WHAT COUNTS AS STRAIGHT, and why the thresholds are what they are. A run of
consecutive outline points is straight when every point in it lies within
`--tol` units of the chord joining its ends. The font is drawn at a 674 cap on
an 84-unit stem, `build.draw()` grows every outline by INK_SPREAD 1.2 a side,
and `geom.resample`'s spacing is a few units -- so a tolerance under about 1
unit reports quantisation, not design. 1.5 is the default: half the ink spread,
comfortably inside a hairline, and far below anything an eye reads as a bend.

WHAT IS NOT A FINDING. Three kinds of straight are DELIBERATE in this face and
are excluded by length rather than by name:

  * a pen cut -- the family's `CUT` face across the end of a stroke. At a
    lowercase stem's 72 units and a 40-degree cut that face is about 94 units
    long, so nothing under 0.30 of the x-height (129 units) can be one.
  * a serif's blade -- WL/WD/DROP make faces of the same order.
  * a bar's own flat -- the E's arms, the T's, the Z's, the f's crossbar. These
    ARE straight by construction and the owner's instruction is about them too,
    so they are reported and left for a human to rule on rather than filtered.

So `--min` is the real dial: it is the run length, in x-heights, below which a
straight edge is assumed to be a terminal rather than a stroke. 0.30 by
default.

Usage:
    cd tools/wedge_serif && python3 cmp_aldine_straight.py [--tol 1.5] [--min 0.30]
                                                          [--chars abc] [--all]
"""
import math, os, subprocess, sys, tempfile

XH = 429.0
SLANT = 13.0
LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def build(out):
    env = dict(os.environ, ALBO_ITALIC="aldine", FJORD_SLANT=str(SLANT),
               FJORD_CONTRAST="0.80", FJORD_WIDTH="95", FJORD_CUT="0",
               PYTHON_GIL="0")
    subprocess.run([sys.executable, "-W", "ignore", "-m", "outlines.build", out,
                    "--style", "Italic"], check=True, env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.join(out, "Albo-Italic.ttf")


def contours(path, name, n=12):
    from fontTools.ttLib import TTFont
    from fontTools.pens.recordingPen import RecordingPen
    f = TTFont(path); gs = f.getGlyphSet()
    if name not in gs: return []
    rp = RecordingPen(); gs[name].draw(rp)
    cs = []; cur = []; pt = None

    def bez(p0, ps, k):
        out = []
        if len(ps) == 2:
            p1, p2 = ps
            for i in range(1, k + 1):
                t = i / k; m = 1 - t
                out.append((m * m * p0[0] + 2 * m * t * p1[0] + t * t * p2[0],
                            m * m * p0[1] + 2 * m * t * p1[1] + t * t * p2[1]))
        else:
            p1, p2, p3 = ps
            for i in range(1, k + 1):
                t = i / k; m = 1 - t
                out.append((m**3 * p0[0] + 3*m*m*t * p1[0] + 3*m*t*t * p2[0] + t**3 * p3[0],
                            m**3 * p0[1] + 3*m*m*t * p1[1] + 3*m*t*t * p2[1] + t**3 * p3[1]))
        return out

    for op, a in rp.value:
        if op == "moveTo": pt = a[0]; cur = [pt]
        elif op == "lineTo": pt = a[0]; cur.append(pt)
        elif op == "qCurveTo":
            ps = list(a)
            if ps and ps[-1] is None: ps = ps[:-1]
            prev = pt
            for i in range(len(ps) - 1):
                c = ps[i]; nx = ps[i + 1]
                if i < len(ps) - 2:
                    nx = ((ps[i][0] + ps[i+1][0]) / 2, (ps[i][1] + ps[i+1][1]) / 2)
                cur += bez(prev, [c, nx], n); prev = nx
            pt = prev
        elif op == "curveTo": cur += bez(pt, list(a), n); pt = a[-1]
        elif op in ("closePath", "endPath"):
            if cur: cs.append(cur); cur = []
    if cur: cs.append(cur)
    t = math.tan(math.radians(SLANT))
    return [[(x - t * y, y) for x, y in c] for c in cs]      # UNSHEARED


def straight_runs(c, tol):
    """Maximal runs of consecutive points within `tol` of their own chord."""
    n = len(c); out = []; i = 0
    while i < n:
        j = i + 1
        best = None
        while j < i + n:
            a = c[i % n]; b = c[j % n]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            if L < 1e-9: j += 1; continue
            ok = True
            for k in range(i + 1, j):
                p = c[k % n]
                d = abs(dx * (a[1] - p[1]) - dy * (a[0] - p[0])) / L
                if d > tol: ok = False; break
            if not ok: break
            best = (j, L); j += 1
        if best and best[0] - i >= 3:
            out.append((i % n, best[0] % n, best[1]))
            i = best[0]
        else:
            i += 1
    return out


def main():
    tol = 1.5; mn = 0.30
    if "--tol" in sys.argv: tol = float(sys.argv[sys.argv.index("--tol") + 1])
    if "--min" in sys.argv: mn = float(sys.argv[sys.argv.index("--min") + 1])
    chars = LETTERS
    if "--chars" in sys.argv: chars = sys.argv[sys.argv.index("--chars") + 1]
    floor = mn * XH
    with tempfile.TemporaryDirectory() as d:
        ttf = build(os.path.join(d, "I"))
        rows = []
        for ch in chars:
            name = ch if ch.isalpha() else {"0": "zero", "1": "one", "2": "two",
                                            "3": "three", "4": "four", "5": "five",
                                            "6": "six", "7": "seven", "8": "eight",
                                            "9": "nine"}.get(ch, ch)
            found = []
            for c in contours(ttf, name):
                for _, _, L in straight_runs(c, tol):
                    if L >= floor: found.append(L)
            if found:
                found.sort(reverse=True)
                rows.append((ch, found))
    print("straight edges at tol %.1f units, runs of %.2f x-height (%.0f units) or more\n"
          % (tol, mn, floor))
    print("  ch   n   longest   all runs, units")
    for ch, f in sorted(rows, key=lambda r: -r[1][0]):
        print("  %-3s %2d   %6.0f    %s" % (ch, len(f), f[0],
                                            " ".join("%.0f" % v for v in f[:8])))
    print("\n%d of %d glyphs carry a straight edge that long." % (len(rows), len(chars)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
