"""How firmly a letter holds the x-height line in a word: ink inside the band
0.85-1.05 xh over the letter's ink width (upright, from the builders), for the
a and its neighbours. Owner 2026-09-27: "variants of M2 and other L1 with
better xheight and word image". Pass KEY=VAL after the style env.
"""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
if os.environ.get("_XB_CHILD"):
    sys.path.insert(0, ROOT)
    from shapely.geometry import box
    from outlines import build as B
    xh = B.pen.XH; out = {}
    for ch in "aodnue":
        g = B.GLYPHS[ch](B.ctx(ch)); x0, y0, x1, y1 = g.bounds
        out[ch] = dict(band=g.intersection(box(x0 - 5, 0.85 * xh, x1 + 5, 1.05 * xh)).area / (x1 - x0), top=y1)
    print(json.dumps(out)); sys.exit(0)
env = dict(os.environ, _XB_CHILD="1", PYTHON_GIL="0")
for kv in sys.argv[1:]:
    k, v = kv.split("=", 1); env[k] = v
p = subprocess.run([sys.executable, __file__], env=env, capture_output=True, text=True, cwd=ROOT)
try:
    d = json.loads(p.stdout.strip().splitlines()[-1])
    print("band " + "  ".join(f"{c} {d[c]['band']:5.1f}" for c in "aodnue") + f"   a top {d['a']['top']:.0f} (o {d['o']['top']:.0f} n {d['n']['top']:.0f})   {' '.join(sys.argv[1:])[-90:]}")
except Exception: print(p.stderr[-1000:])
