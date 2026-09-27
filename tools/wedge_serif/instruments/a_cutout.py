"""The white notch under the italic a's bottom join: white area in the box
from 60 units left of the stem's left edge to the edge, baseline to 90 units,
that is NOT inside the bowl's counter (owner 2026-09-27: "add more area under
bottom join" -- "the little cutout on the bottom"). Upright, from the builders."""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
if os.environ.get("_AC_CHILD"):
    sys.path.insert(0, ROOT)
    from shapely.geometry import box, Polygon
    from outlines import build as B
    from outlines.glyphs import aldine as A
    c = B.ctx('a'); g = B.GLYPHS['a'](c); xh = c["xh"]; u = xh / A.A_UNIT
    xs = B.pen.S * 0.6 + A.A_STEM_X * u; sw = A.HM_STEMW * A.hm_u(c); e = xs - sw / 2
    counter = [Polygon(h) for p in getattr(g, "geoms", [g]) for h in p.interiors]
    region = box(e - 60, 0, e, 90).difference(g)
    for cp in counter: region = region.difference(cp)
    print(json.dumps(dict(cutout=region.area))); sys.exit(0)
env = dict(os.environ, _AC_CHILD="1", PYTHON_GIL="0")
for kv in sys.argv[1:]:
    k, v = kv.split("=", 1); env[k] = v
p = subprocess.run([sys.executable, __file__], env=env, capture_output=True, text=True, cwd=ROOT)
try: print(f"cutout {json.loads(p.stdout.strip().splitlines()[-1])['cutout']:.0f} units^2   {' '.join(sys.argv[1:])}")
except Exception: print(p.stderr[-1200:])
