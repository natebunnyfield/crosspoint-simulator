"""Evaluate the italic a's top for a set of env overrides WITHOUT a font build:
draw the glyph from the builders (unsheared), rasterise it at 1 unit = 1 px,
and run a_top_profile.profile on it, with the x's top as the x-height (as the
font measure does). Run under ALBO_ITA_ENV / ALBO_BIT_ENV.

    env "${ALBO_ITA_ENV[@]}" python3 instruments/a_top_eval.py ALBO_ALD_A_TOP=470 ...
"""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
if os.environ.get("_AT_CHILD"):
    sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
    import numpy as np
    from PIL import Image, ImageDraw
    from outlines import build as B
    from a_top_profile import profile
    def raster(g, pad=40):
        x0, y0, x1, y1 = g.bounds; W = int(x1 - x0) + 2 * pad; H = int(y1 + pad) - int(min(y0, 0) - pad)
        top = int(y1 + pad)
        im = Image.new("1", (W, H), 0); d = ImageDraw.Draw(im)
        polys = getattr(g, "geoms", [g])
        for p in polys:
            d.polygon([(x - x0 + pad, top - y) for x, y in p.exterior.coords], fill=1)
            for h in p.interiors: d.polygon([(x - x0 + pad, top - y) for x, y in h.coords], fill=0)
        return np.array(im, bool), top
    a, base = raster(B.GLYPHS['a'](B.ctx('a'))); xg = B.GLYPHS['x'](B.ctx('x'))
    d = profile(a, xg.bounds[3], base, straighten=False)   # the builders draw UPRIGHT; the build shears
    print(json.dumps({k: float(v) for k, v in d.items() if k != "img"}))
    sys.exit(0)
env = dict(os.environ, _AT_CHILD="1", PYTHON_GIL="0")
for kv in sys.argv[1:]:
    k, v = kv.split("=", 1); env[k] = v
out = subprocess.run([sys.executable, __file__], env=env, capture_output=True, text=True, cwd=ROOT)
try:
    d = json.loads(out.stdout.strip().splitlines()[-1])
    print(f"left30 {d['left30']:.3f}  crown {d['crown']:.3f} @ {d['crown_x']:.2f}  valley {d['valley']:.3f} @ {d['valley_x']:.2f}  "
          f"droop {d['crown'] - d['valley']:.3f}  stem {d['stem']:.3f}   {' '.join(sys.argv[1:])}")
except Exception:
    print(out.stderr[-1500:])
