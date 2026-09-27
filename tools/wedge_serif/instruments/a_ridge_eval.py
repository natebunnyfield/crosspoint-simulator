"""Ridge thin / thick of the italic a straight from the builders (no font
build): rasterise the upright geometry at 1 unit = 1 px in THIS python (which
has the builders), then hand the bitmap to a python with scipy for the ridge.
Owner 2026-09-27: "try again with the goal of appropriate thick and thin".

    env "${ALBO_ITA_ENV[@]}" python3 instruments/a_ridge_eval.py VENV_PY KEY=VAL ...
"""
import os, sys, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
venv = sys.argv[1]
for kv in sys.argv[2:]:
    k, v = kv.split("=", 1); os.environ[k] = v
sys.path.insert(0, ROOT)
import numpy as np
from PIL import Image, ImageDraw
from outlines import build as B
res = {}
for ch in "ao":
    g = B.GLYPHS[ch](B.ctx(ch)); x0, y0, x1, y1 = g.bounds; pad = 10
    W, H = int(x1 - x0) + 2 * pad, int(y1 - y0) + 2 * pad
    im = Image.new("1", (W, H), 0); d = ImageDraw.Draw(im)
    for p in getattr(g, "geoms", [g]):
        d.polygon([(x - x0 + pad, y1 - y + pad) for x, y in p.exterior.coords], fill=1)
        for h in p.interiors: d.polygon([(x - x0 + pad, y1 - y + pad) for x, y in h.coords], fill=0)
    f = tempfile.mktemp(suffix=".npy"); np.save(f, np.array(im, bool)); res[ch] = f
code = r'''
import sys, numpy as np
from scipy.ndimage import distance_transform_edt as edt, maximum_filter
for ch, f in zip("ao", sys.argv[1:]):
    a = np.load(f); d = edt(np.pad(a, 2)); r = (d == maximum_filter(d, 3)) & (d > 3); w = 2 * d[r]
    print(f"{ch} thin(p10) {np.percentile(w,10):5.1f}  p25 {np.percentile(w,25):5.1f}  thick(p90) {np.percentile(w,90):5.1f}", end="   ")
'''
print(subprocess.run([venv, "-c", code, res["a"], res["o"]], capture_output=True, text=True).stdout, " ".join(sys.argv[2:]))
