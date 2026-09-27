"""Italic r 'sho' arm: ink of the r's arm against the n's shoulder in the same
window (unsheared, from each stem's right edge to 0.70 of the pitch, above
0.5 xh). Run under an italic env; prints the ratio for each ALBO_ALD_R_SHO_K
given on the command line. Owner 2026-09-27: "balance optically".

    env "${ALBO_ITA_ENV[@]}" python3 instruments/r_sho_balance.py 0.9 1.0 1.1
"""
import os, sys, subprocess, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
if os.environ.get("_RSHO_CHILD"):
    sys.path.insert(0, ROOT)
    from shapely.geometry import box
    from outlines import build as B
    from outlines.glyphs import aldine as A
    xh = B.pen.XH
    def win_area(ch):
        g = B.GLYPHS[ch](B.ctx(ch)); x0 = B.pen.S * 1.0
        P = A.HM_PITCH * xh; sw = A.HM_STEMW * A.hm_u(B.ctx(ch))
        return g.intersection(box(x0 + sw / 2, 0.5 * xh, x0 + 0.70 * P, xh * 1.2)).area
    print(json.dumps(dict(r=win_area('r'), n=win_area('n'))))
    sys.exit(0)
for k in sys.argv[1:] or ["1.0"]:
    env = dict(os.environ, _RSHO_CHILD="1", ALBO_ALD_R_OPT="sho", ALBO_ALD_R_SHO_K=k, PYTHON_GIL="0")
    out = subprocess.run([sys.executable, __file__], env=env, capture_output=True, text=True, cwd=ROOT)
    try:
        d = json.loads(out.stdout.strip().splitlines()[-1]); print(f"k {k}: r {d['r']:.0f}  n {d['n']:.0f}  r/n {d['r']/d['n']:.3f}")
    except Exception:
        print(out.stderr[-800:])
