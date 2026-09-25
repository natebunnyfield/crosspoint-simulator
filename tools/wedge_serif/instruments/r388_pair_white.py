# ROUND 388 -- measured every pair white in docs/albo-round-388-2026-09-25.md.
# usage: PYTHON_GIL=0 python3 instruments/r388_pair_white.py FONT.ttf Fi Fo "'s"
"""white = rsb(L) + kern + lsb(R), kern read by HarfBuzz from the font's own GPOS."""
import sys, json, subprocess
from fontTools.ttLib import TTFont
def shaped_adv(path, text, feats):
    out = subprocess.run(['hb-shape', '--output-format=json', '--no-glyph-names', f'--features={feats}', path, text],
                         capture_output=True, text=True, check=True).stdout
    return [g['ax'] for g in json.loads(out)]
def white(path, a, b):
    f = TTFont(path); hm = f['hmtx']; gl = f['glyf']; cm = f.getBestCmap()
    na, nb = cm[ord(a)], cm[ord(b)]
    def side(n):
        adv, lsb = hm[n]; g = gl[n]; g.recalcBounds(gl) if g.numberOfContours else None
        w = (g.xMax - g.xMin) if g.numberOfContours else 0
        return lsb, adv - lsb - w
    k = shaped_adv(path, a+b, '')[0] - shaped_adv(path, a+b, '-kern')[0]
    return dict(L=na, R=nb, rsb=side(na)[1], kern=k, lsb=side(nb)[0], white=side(na)[1]+k+side(nb)[0])
if __name__ == '__main__':
    path = sys.argv[1]
    for p in sys.argv[2:]:
        print(p, white(path, p[0], p[1]))
