"""The r's terminal against the o: inscribed-circle diameter of the r's arm end
(ink right of 72% of the r's box, upper half) and of the o's ink (its thickest
stroke), unsheared, from the builders. Owner 2026-09-27: "terminal needs to be
as thick as o and other letters to balance". Pass KEY=VAL env overrides after
the style's env; prints both numbers.

    env "${ALBO_ITA_ENV[@]}" python3 instruments/r_terminal_solve.py ALBO_ALD_R_OPT=sho ALBO_ALD_R_SHO_END=4.6
"""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
if os.environ.get("_RT_CHILD"):
    sys.path.insert(0, ROOT)
    import shapely
    from shapely.geometry import box
    from outlines import build as B
    def mic(g): return 2 * shapely.maximum_inscribed_circle(g, tolerance=0.25).length
    r = B.GLYPHS['r'](B.ctx('r')); x0, y0, x1, y1 = r.bounds
    term = r.intersection(box(x0 + 0.72 * (x1 - x0), (y0 + y1) / 2, x1 + 1, y1 + 1))
    print(json.dumps(dict(o=mic(B.GLYPHS['o'](B.ctx('o'))), r=mic(term))))
    sys.exit(0)
env = dict(os.environ, _RT_CHILD="1", PYTHON_GIL="0")
for kv in sys.argv[1:]:
    k, v = kv.split("=", 1); env[k] = v
out = subprocess.run([sys.executable, __file__], env=env, capture_output=True, text=True, cwd=ROOT)
try:
    d = json.loads(out.stdout.strip().splitlines()[-1]); print(f"{' '.join(sys.argv[1:]) or 'today'}: o {d['o']:.1f}  r-terminal {d['r']:.1f}  r/o {d['r']/d['o']:.3f}")
except Exception:
    print(out.stderr[-1500:])
