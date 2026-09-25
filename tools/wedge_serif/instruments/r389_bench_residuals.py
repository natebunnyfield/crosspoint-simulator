# ROUND 389 -- every bench pair: where the font sits now against where the owner put it.
# usage: python3 instruments/r389_bench_residuals.py BUILT_DIR [--json OUT]
"""For every pair he judged (bench_values.json `literal`, plus the 09-25 re-ask,
whose rows take the MEAN of his two answers), in both styles:

    target   = white(pair, 09-20 bench font) + his delta
    residual = white(pair, BUILT font) - target        (+ = looser than he set)

White is rsb(L) + kern + lsb(R) with the kern taken from the GPOS by HarfBuzz
(hb-shape over a text file, one pair per line -- the same number
instruments/r388_pair_white.py gives, batched). Zero is his own zero: the bench
fonts are the files both bench pages rendered (bench/fonts-2026-09-20).

The g rows are dropped, as bench_fit drops them (2026-09-21 ruling: judged
against a g that was since redrawn).
"""
import argparse, json, os, subprocess, sys, tempfile
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(HERE, "bench")


def _shape(path, lines, feats):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write("\n".join(lines) + "\n"); tf = fh.name
    out = subprocess.run(["hb-shape", "--output-format=json", "--no-glyph-names",
                          f"--features={feats}", f"--text-file={tf}", path],
                         capture_output=True, text=True, check=True).stdout
    os.unlink(tf)
    return [json.loads(l) for l in out.strip().splitlines()]


def whites(path, pairs):
    """{pair: (rsb, kern, lsb, white)} for 2-char strings."""
    f = TTFont(path); hm = f["hmtx"]; gl = f["glyf"]; cm = f.getBestCmap()
    def side(n):
        adv, lsb = hm[n]; g = gl[n]
        if not g.numberOfContours: return 0, adv
        g.recalcBounds(gl)
        return lsb, adv - lsb - (g.xMax - g.xMin)
    pairs = [p for p in pairs if all(ord(c) in cm for c in p)]
    on = _shape(path, pairs, ""); off = _shape(path, pairs, "-kern")
    out = {}
    for p, a, b in zip(pairs, on, off):
        if len(a) != 2 or len(b) != 2:     # a ligature took the pair (roman fi fl ...)
            continue
        k = a[0]["ax"] - b[0]["ax"]
        r = side(cm[ord(p[0])])[1]; l = side(cm[ord(p[1])])[0]
        out[p] = (r, k, l, r + k + l)
    return out


def targets(style):
    lit = json.load(open(os.path.join(HERE, "bench_values.json")))["literal"][style]
    J = {p: float(d) for p, d in lit.items() if "g" not in p}
    reask = {}
    ans = json.load(open(os.path.join(BENCH, "answers", "reask-2026-09-25-answers.json")))["answers"]
    for a in ans:
        if a["style"] == style and a["pair"] in J:
            reask[a["pair"]] = a["delta"]
    return J, reask


def residuals(built_dir):
    out = {}
    for style, fn in (("roman", "Albo-Regular.ttf"), ("italic", "Albo-Italic.ttf")):
        J, reask = targets(style)
        w0 = whites(os.path.join(BENCH, "fonts-2026-09-20", fn), list(J))
        w1 = whites(os.path.join(built_dir, fn), list(J))
        rows = {}
        for p, d in J.items():
            if p not in w0 or p not in w1: continue
            dm = (d + reask[p]) / 2 if p in reask else d
            tgt = w0[p][3] + dm
            rows[p] = dict(delta=d, reask=reask.get(p), delta_used=dm, white0920=w0[p][3],
                           target=tgt, white=w1[p][3], kern=w1[p][1], resid=w1[p][3] - tgt,
                           moved=w1[p][3] - w0[p][3])
        out[style] = rows
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("built")
    ap.add_argument("--json")
    ap.add_argument("--top", type=int, default=25)
    a = ap.parse_args()
    R = residuals(a.built)
    for style, rows in R.items():
        print(f"\n{style}: {len(rows)} judged pairs; largest |white - his target|")
        for p, r in sorted(rows.items(), key=lambda kv: -abs(kv[1]["resid"]))[:a.top]:
            ra = f" reask {r['reask']:+d}" if r["reask"] is not None else ""
            print(f"  {p:3} resid {r['resid']:+6.1f}  his {r["delta"]:+4.0f}{ra}  white 09-20 {r['white0920']:5d}"
                  f" -> now {r['white']:5d} (kern {r['kern']:+d})")
    if a.json: json.dump(R, open(a.json, "w"), indent=1)
