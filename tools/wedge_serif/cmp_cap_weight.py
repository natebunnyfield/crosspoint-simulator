"""Is an italic capital the weight of its own roman?

Round 131c. The owner said "AHNV are all off on weight, especially N" and the
two metrics I reached for first disagreed with each other AND with the render:
the median of a row's horizontal runs read the A 1.81x too heavy (a crossbar is
one enormous run per row), the 30th percentile read it 0.71x too light (it
catches the hairline). This one is 2 x AREA / OUTLINE LENGTH -- the mean width
of the ink -- taken off the outline, so it needs no raster and no threshold.

The TARGET for each re-cut capital is the ratio its OWN roman carries against
the roman's untouched controls. The A's is 0.89, not 1.00: a diagonal letter is
lighter than a stemmed one, and a metric that does not know that fattens every
A in the alphabet.

    cd tools/wedge_serif && python3 cmp_cap_weight.py [--tol 0.05]

Builds a roman and an Aldine italic into a temp dir and exits non-zero when a
re-cut capital sits more than --tol from its roman's ratio.
"""
import math, os, subprocess, sys, tempfile
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.basePen import BasePen

# Round 135 added Y and O. A letter joins this string the moment it is re-cut,
# because the string does double duty: it names what is CHECKED, and it is
# also what is EXCLUDED from the control median the check normalizes by. Leave
# a re-cut letter out and it silently helps set the bar it is measured against.
RECUT = "AGHNOQSUVY"
CAPS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = dict(FJORD_STEM="66.9", FJORD_CONTRAST="0.892", FJORD_WIDTH="95", PYTHON_GIL="0")


class _Perim(BasePen):
    """Outline length, curves flattened. A stroke of mean width w and skeleton
    length L has area ~ w*L and perimeter ~ 2L, so 2A/P is that w."""
    def __init__(self, gs):
        super().__init__(gs); self.L = 0.0; self._p = None; self._s = None
    def _moveTo(self, p): self._p = p; self._s = p
    def _lineTo(self, p): self.L += math.dist(self._p, p); self._p = p
    def _flatten(self, pts, n):
        prev = self._p
        for i in range(1, n + 1):
            t = i / n
            q = list(pts)
            while len(q) > 1:      # de Casteljau
                q = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                     for a, b in zip(q, q[1:])]
            self.L += math.dist(prev, q[0]); prev = q[0]
        self._p = pts[-1]
    def _curveToOne(self, a, b, c): self._flatten([self._p, a, b, c], 24)
    def _qCurveToOne(self, a, b): self._flatten([self._p, a, b], 20)
    def _closePath(self):
        if self._p and self._s: self.L += math.dist(self._p, self._s)


def widths(ttf):
    """char -> mean ink width, and the same normalised by the median of the
    capitals this module does NOT redraw."""
    f = TTFont(ttf); gs = f.getGlyphSet(); cmap = f.getBestCmap()
    w = {}
    for ch in CAPS:
        n = cmap.get(ord(ch))
        if not n: continue
        ap = AreaPen(gs); gs[n].draw(ap)
        pp = _Perim(gs); gs[n].draw(pp)
        if pp.L > 0: w[ch] = 2 * abs(ap.value) / pp.L
    ctl = sorted(v for c, v in w.items() if c not in RECUT)
    med = ctl[len(ctl) // 2]
    return {c: v / med for c, v in w.items()}


def build(out, italic):
    env = dict(os.environ); env.update(COMMON)
    cmd = [sys.executable, "-m", "outlines.build", out]
    if italic:
        env.update(ALBO_ITALIC="aldine", FJORD_SLANT="13")
        cmd += ["--style", "Italic"]
    r = subprocess.run(cmd, cwd=HERE, env=env, capture_output=True, text=True)
    if r.returncode: sys.exit("build failed:\n" + r.stderr[-2000:])
    name = "Albo-Italic.ttf" if italic else "Albo-Medium.ttf"
    return os.path.join(out, name)


def main():
    tol = 0.05
    if "--tol" in sys.argv: tol = float(sys.argv[sys.argv.index("--tol") + 1])
    with tempfile.TemporaryDirectory() as d:
        rom = widths(build(os.path.join(d, "R"), False))
        ita = widths(build(os.path.join(d, "I"), True))
    bad = []
    print("     roman  italic   diff   (mean ink width, x the untouched capitals' median)")
    for ch in RECUT:
        if ch not in rom or ch not in ita: continue
        diff = ita[ch] - rom[ch]
        flag = "  <-- OFF" if abs(diff) > tol else ""
        if flag: bad.append(ch)
        print("  %s  %.2f    %.2f   %+.2f%s" % (ch, rom[ch], ita[ch], diff, flag))
    print("\n%d re-cut capital(s) more than %.2f from their roman." % (len(bad), tol))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
