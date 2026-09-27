"""Fit of the italic a against its neighbours, from the builders (upright):
colour (ink / (advance x xh)), counter area (the glyph's holes; for n, the
white under the arch down to the baseline inside the stems), and the round
letters' contrast (o: thick = horizontal cut at mid height, thin = vertical
cut at the centre, top). Owner 2026-09-27: "increase the fit and style. adjust
size of counter and contrast". Pass KEY=VAL overrides after the style env.

    env "${ALBO_ITA_ENV[@]}" python3 instruments/a_fit.py ALBO_ALD_A_TRI=mid
"""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
if os.environ.get("_AF_CHILD"):
    sys.path.insert(0, ROOT)
    from shapely.geometry import LineString, box
    from outlines import build as B
    xh = B.pen.XH
    def holes(g):
        ps = getattr(g, "geoms", [g]); from shapely.geometry import Polygon
        return sum(Polygon(h).area for p in ps for h in p.interiors)
    def runs(g, line):
        r = g.intersection(line); gs = getattr(r, "geoms", [r])
        return sorted([s.length for s in gs if s.length > 0])
    out = {}
    adv = B.metrics_for if hasattr(B, "metrics_for") else None
    for ch in "aodneuq":
        g = B.GLYPHS[ch](B.ctx(ch)); x0, y0, x1, y1 = g.bounds
        band = g.intersection(box(x0 - 5, 0, x1 + 5, xh))
        d = dict(colour=band.area / ((x1 - x0) * xh), counter=holes(g), width=x1 - x0)
        # the bowl's contrast: a horizontal cut at 0.45 xh (the sides) and a vertical cut
        # through the counter's centre (the top and bottom)
        hs = [h for p in getattr(g, "geoms", [g]) for h in p.interiors]
        if hs:
            from shapely.geometry import Polygon
            hp = max((Polygon(h) for h in hs), key=lambda p: p.area); cx, cy = hp.centroid.x, hp.centroid.y
            side = runs(g, LineString([(x0 - 5, cy), (x1 + 5, cy)])); tb = runs(g, LineString([(cx, y0 - 5), (cx, y1 + 5)]))
            d.update(side_max=max(side) if side else 0, tb_min=min(tb) if tb else 0)
        out[ch] = d
    print(json.dumps(out)); sys.exit(0)
env = dict(os.environ, _AF_CHILD="1", PYTHON_GIL="0")
for kv in sys.argv[1:]:
    k, v = kv.split("=", 1); env[k] = v
p = subprocess.run([sys.executable, __file__], env=env, capture_output=True, text=True, cwd=ROOT)
try:
    d = json.loads(p.stdout.strip().splitlines()[-1])
except Exception:
    print(p.stderr[-1500:]); sys.exit(1)
a, o, dd, n = d["a"], d["o"], d["d"], d["n"]
con = lambda g: g.get("side_max", 0) / (g.get("tb_min", 1) or 1)
print(f"a colour {a['colour']:.3f} (n {n['colour']:.3f} o {o['colour']:.3f} d {dd['colour']:.3f})  "
      f"counter {a['counter']:.0f} (o {o['counter']:.0f} d {dd['counter']:.0f} e {d['e']['counter']:.0f} q {d['q']['counter']:.0f})  "
      f"contrast {con(a):.2f} (o {con(o):.2f} d {con(dd):.2f} q {con(d['q']):.2f})  width {a['width']:.0f} (d {dd['width']:.0f})   {' '.join(sys.argv[1:])}")
