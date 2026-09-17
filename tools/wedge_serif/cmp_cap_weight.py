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

RECUT = "AGHKLMNOPQRSUVWXYZ"   # both round-135 passes, plus round 145's X and W
# ADDING A LETTER HERE ALSO TAKES IT OUT OF THE CONTROLS, and that is not the
# harmless bookkeeping it looks like. `widths()` divides every ratio by the
# median of the capitals NOT in this string, so round 145 shrank the controls
# from B C D E F I J T W X to B C D E F I J T -- and X is the LIGHTEST capital
# in the alphabet (0.834 of the old median in the roman), so dropping it and
# the W lifts the median hard. Measured on the round-144 tree, changing nothing
# but this string: roman median 55.95 -> 59.31 (+6.0%), italic 56.44 -> 59.19
# (+4.9%).
#
# The two builds do NOT move by the same factor, so the DIFF -- the only number
# this script decides on -- moves too, by about +0.01 on the stemmed capitals:
#
#     H +0.036 -> +0.046    M +0.037 -> +0.045    N +0.033 -> +0.042
#     O -0.048 -> -0.035    G -0.039 -> -0.028    V -0.028 -> -0.017
#
# Nothing crossed 0.05 in either direction, but H M N now sit within 0.005 of
# the rail where they had 0.014, and that is the margin a future round has to
# work in. Recorded rather than tuned away: a letter this module redraws cannot
# honestly stay in the control set, which is what the set is for.
CAPS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = dict(FJORD_STEM="66.9", FJORD_CONTRAST="0.80", FJORD_WIDTH="95", PYTHON_GIL="0")


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


# ROUND 163 -- ONE LETTER IS EXEMPT FROM THE ROMAN-PARITY RULE, BY NAME AND
# WITH ITS REASON. Owner 2026-09-16: *"Y needs to match weight of other
# capitals be by thicker on right stroke and tall enough to reach line"*.
#
# Round 131c's rule is that an italic capital carries its OWN roman's weight,
# and that is what every other row here checks. The Y cannot do both things at
# once, because Albo's ROMAN Y is itself the light one: measured as this script
# measures, against the untouched capitals' median --
#
#   the italic capitals   A 0.88  G 0.90  H 1.09  K 0.95  L 0.99  M 0.96
#                         N 1.02  O 0.97  P 1.00  Q 0.92  R 1.03  S 0.95
#                         U 0.95  V 0.85  W 0.89  X 0.81  Z 1.01
#   the roman Y           0.89
#   the italic Y, before  0.93
#
# -- so holding parity with the roman pins the italic Y at 0.89-0.93, which is
# the bottom of the alphabet beside V, W and X, and the owner is looking at a
# page rather than at a gate. At the arm weight he asked for, the italic Y
# reads 0.99: level with L at 0.99 and P at 1.00, which is what "match the
# other capitals" means.
#
# THE EXEMPTION IS A NAMED ROW AND NOT A WIDER TOLERANCE, deliberately: moving
# --tol would excuse every letter silently, and the next drift in any of the
# other seventeen would pass unnoticed. The Y's own number is still PRINTED
# every run, so the cost stays visible.
#
# THE WAY OUT, if it is ever wanted: thicken the ROMAN Y's right arm to match
# (`caps_straight.g_Y`, whose arm is `pw(q0, q1, 0.72)` -- that 0.72 is the
# thin factor). Then parity returns and this row goes. It was not done here
# because the instruction named the italic and the roman ships in Albo Regular.
EXEMPT = {"Y": "round 163: the owner's weight ruling; the roman Y is the light one"}


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
        if flag and ch in EXEMPT:
            flag = "  <-- exempt: " + EXEMPT[ch]
        elif flag:
            bad.append(ch)
        print("  %s  %.2f    %.2f   %+.2f%s" % (ch, rom[ch], ita[ch], diff, flag))
    print("\n%d re-cut capital(s) more than %.2f from their roman." % (len(bad), tol))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
