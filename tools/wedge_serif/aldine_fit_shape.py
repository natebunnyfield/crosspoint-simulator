"""Coordinate descent of one Aldine letter's env dials against a reference,
scored by cmp_aldine_shape's overlay IoU. The per-pass tool the owner asked
for on 2026-09-15 ("take multiple passes at each until the shape ... match").

    python3 aldine_fit_shape.py <ch> '<dials json>' [--ref poetica|flanker|pagella] [--ring VAR '<keys json>']

dials json:  {"ALBO_ALD_A_SKEW": [start, lo, hi, step], ...}
ring:        an env var holding "deg:width,deg:width,..." (see keyed_ring in
             glyphs/aldine.py) and a json {"0": [start, lo, hi, step], ...}
Prints each accepted move, then the best IoU and the dial values to bake.
It scores SHAPE only -- the eye still judges the overlay it leaves behind.
"""
import os, sys, json, subprocess, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cmp_aldine_shape as CS

BASE = dict(os.environ, ALBO_ITALIC="aldine", FJORD_STEM="66.9", FJORD_CONTRAST="0.80",
            FJORD_WIDTH="95", FJORD_SLANT="13", PYTHON_GIL="0")


def main():
    argv = sys.argv[1:]
    ref_kind = 'poetica'; ring_var = None; ring_keys = None
    if '--ref' in argv:
        i = argv.index('--ref'); ref_kind = argv[i + 1]; del argv[i:i + 2]
    if '--ring' in argv:
        i = argv.index('--ring'); ring_var = argv[i + 1]; ring_keys = json.loads(argv[i + 2]); del argv[i:i + 3]
    ch, dials = argv[0], json.loads(argv[1])
    tmp = tempfile.mkdtemp()
    rmask, rb = CS.font_mask_xh(CS.REF_FONTS[ref_kind], ch)

    def evaluate(vals, ring):
        env = dict(BASE); env.update({k: str(v) for k, v in vals.items()})
        if ring: env[ring_var] = ",".join("%s:%s" % (a, w) for a, w in ring.items())
        r = subprocess.run([sys.executable, "-m", "outlines.build", tmp, "--style", "Italic"],
                           cwd=HERE, env=env, capture_output=True, text=True)
        if r.returncode: sys.exit("build failed:\n" + r.stderr[-1500:])
        cmask, cb = CS.font_mask_xh(tmp + "/Albo-Italic.ttf", ch)
        return CS.compare_xh(rmask, rb, cmask, cb)[0]

    vals = {k: v[0] for k, v in dials.items()}
    ring = {k: v[0] for k, v in ring_keys.items()} if ring_keys else None
    best = evaluate(vals, ring); print("start IoU %.3f  (ref %s)" % (best, ref_kind))
    for _ in range(4):
        moved = False
        for k, (v0, lo, hi, step) in dials.items():
            for d in (+step, -step):
                t = dict(vals); t[k] = round(min(hi, max(lo, vals[k] + d)), 4)
                if t[k] == vals[k]: continue
                s = evaluate(t, ring)
                if s > best + 1e-4:
                    best, vals, moved = s, t, True; print("  %s -> %s  IoU %.3f" % (k, t[k], s)); break
        if ring_keys:
            for k, (v0, lo, hi, step) in ring_keys.items():
                for d in (+step, -step):
                    t = dict(ring); t[k] = round(min(hi, max(lo, ring[k] + d)), 2)
                    if t[k] == ring[k]: continue
                    s = evaluate(vals, t)
                    if s > best + 1e-4:
                        best, ring, moved = s, t, True; print("  ring %s -> %s  IoU %.3f" % (k, t[k], s)); break
        if not moved: break
    print("best IoU %.3f" % best); print(json.dumps(vals))
    if ring: print(json.dumps(ring))
    shutil.rmtree(tmp)


if __name__ == '__main__':
    main()
