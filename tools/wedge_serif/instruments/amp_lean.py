"""How far the '&''s BACK leans once its face's own slant is taken out -- round 377.

The back of a curved-E ampersand is the left edge of its two bowls. Fitting a
line to the leftmost ink of every row from 20% to 80% of the ink height gives
the back's lean; a letter drawn at its face's slant reads the same residual as
the reference form drawn upright. Poetica's alt051 -- the ruled form's source
-- is unsheared by its own measured 9.2 degrees (refs_registry) to give that
reference residual, and each Albo build by the face's 13.

    PYTHON_GIL=0 python3 instruments/amp_lean.py ALBO_ITALIC.ttf [...]
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from amp_measure import _ink, size_for_xh
import refs_registry as RR


def back_lean(mask):
    ys = np.nonzero(mask.any(1))[0]; y0, y1 = ys.min(), ys.max(); h = y1 - y0
    pts = []
    for y in range(int(y0 + 0.2 * h), int(y0 + 0.8 * h)):
        xs = np.nonzero(mask[y])[0]
        if len(xs): pts.append((y, xs.min()))
    Y = np.array([p[0] for p in pts], float); X = np.array([p[1] for p in pts], float)
    # the back is a CURVE; its lean is the chord of the fitted line, top to bottom
    k = np.polyfit(Y, X, 1)[0]
    return math.degrees(math.atan(-k))    # + = top to the right


def poetica_alt051(slant):
    from fontTools.ttLib import TTFont
    from fontTools.pens.basePen import BasePen
    f = TTFont(RR.path("Poetica")); gs = f.getGlyphSet()
    class P(BasePen):
        def __init__(s, g): super().__init__(g); s.polys = []; s.cur = []
        def _moveTo(s, p): s.cur = [p]
        def _lineTo(s, p): s.cur.append(p)
        def _curveToOne(s, a, b, c):
            p0 = s.cur[-1]
            for i in range(1, 17):
                t = i / 16; m = 1 - t
                s.cur.append(tuple(m**3*p0[j] + 3*m*m*t*a[j] + 3*m*t*t*b[j] + t**3*c[j] for j in (0, 1)))
        def _closePath(s): s.polys.append(s.cur); s.cur = []
    p = P(gs); gs["ampersand.alt051"].draw(p)
    sh = math.tan(math.radians(slant)); sc = 1.0
    W, H = 1400, 1200; base = 1000
    acc = np.zeros((H, W), bool)
    for poly in p.polys:
        im = Image.new("1", (W, H), 0)
        ImageDraw.Draw(im).polygon([(100 + (x - sh * y) * sc, base - y * sc) for x, y in poly], fill=1)
        acc ^= np.asarray(im, bool)
    return acc


def main():
    print(f"Poetica alt051 unsheared {RR.slant('Poetica')}: back lean {back_lean(poetica_alt051(RR.slant('Poetica'))):+.1f} deg")
    print(f"Poetica alt051 as drawn:          back lean {back_lean(poetica_alt051(0.0)):+.1f} deg")
    for p in sys.argv[1:]:
        size, _ = size_for_xh(p, 0)
        m, _ = _ink(p, 0, "&", size, 13.0)
        print(f"{p}  unsheared 13: back lean {back_lean(m):+.1f} deg")


if __name__ == "__main__":
    main()
