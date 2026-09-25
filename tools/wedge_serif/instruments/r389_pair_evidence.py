# ROUND 389 -- the evidence table for every pair in docs/albo-round-389-2026-09-25.md.
# usage: PYTHON_GIL=0 python3 instruments/r389_pair_evidence.py FONT.ttf [--bench BENCHFONT.ttf] fo or rt ...
"""Four readings of one pair, so no verdict rests on a single measure
(docs/albo-spacing-method.md records three that were each believed and wrong).

  white   rsb(L) + kern + lsb(R) in font units, kern from the GPOS by HarfBuzz
          (instruments/r388_pair_white.py).
  bench   where he has judged the pair: his target white = the pair's white in
          the 09-20 bench fonts + his literal delta; `now-tgt` is how far the
          font sits from it (+ = looser than he asked).
  M4 int  Measure 4 (cmp_space_2d, the 2-D closest approach) as a PAIR
          INTERACTION: g(ab) - g(an) - g(nb) + g(nn), i.e. what the pair does
          beyond what its two letters' sides already do against the neutral n.
          The same number is taken in every reference face, and `M4 d` is
          Albo's interaction minus the references' median, in units. This
          subtracts the face's tracking and both letters' bearings, so what is
          left is the pair and nothing else. The o-neutral version is printed
          beside it; a finding needs both to agree in sign.
  M5 int  The same interaction on Measure 5 (cmp_word_white, clamped mean
          white over the x-height band) -- the measure that sees an open
          shoulder the 2-D minimum cannot. n/a for marks.

A positive `d` means Albo's pair is LOOSER than the references' same pair,
relative to its own letters.
"""
import argparse, os, sys, json, subprocess
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import refsets
from cmp_space_2d import Face as F4
from cmp_word_white import Face as F5
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r388_pair_white import white as hb_white


def interaction(g, a, b, n):
    v = [g(a, b), g(a, n), g(n, b), g(n, n)]
    if any(x is None for x in v): return None
    return v[0] - v[1] - v[2] + v[3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ttf")
    ap.add_argument("pairs", nargs="+")
    ap.add_argument("--bench", help="the 09-20 bench font of the same style")
    ap.add_argument("--json")
    a = ap.parse_args()
    rset = refsets.pick(a.ttf)
    style = "italic" if "Italic" in os.path.basename(a.ttf) else "roman"
    lit = json.load(open(os.path.join(HERE, "bench_values.json")))["literal"][style]
    me4 = F4(a.ttf); me5 = F5(a.ttf)
    r4 = [F4(p, index=i) for _, p, i in refsets.entries(rset)]
    r5 = []
    for _, p, i in refsets.entries(rset):
        try: r5.append(F5(p, index=i))
        except Exception: pass
    rows = []
    print(f"{os.path.basename(a.ttf)}  refs={rset}  (units = em x 1000)")
    print(f"  {'pair':5}{'white':>7}{'bench d':>8}{'now-tgt':>8}"
          f"{'M4':>7}{'M4 ref':>7}{'M4int n':>8}{'ref':>6}{'d n':>6}{'d o':>6}"
          f"{'M5int n':>8}{'ref':>6}{'d n':>6}{'d o':>6}")
    for p in a.pairs:
        L, R = p[0], p[1]
        w = hb_white(a.ttf, L, R)["white"]
        bd = lit.get(p); tgt = None
        if bd is not None and a.bench:
            tgt = hb_white(a.bench, L, R)["white"] + bd
        row = dict(pair=p, white=w, bench=bd, now_minus_target=(w - tgt) if tgt is not None else None)
        g4 = me4.gap(L, R)
        rg4 = [f.gap(L, R) for f in r4]; rg4 = [x for x in rg4 if x is not None]
        row["m4"] = g4 * 1000 if g4 is not None else None
        row["m4_ref"] = float(np.median(rg4)) * 1000 if rg4 else None
        for tag, meF, refF in (("m4", me4.gap, [f.gap for f in r4]),
                               ("m5", me5.white, [f.white for f in r5])):
            for n in "no":
                mi = interaction(meF, L, R, n)
                ri = [x for g in refF if (x := interaction(g, L, R, n)) is not None]
                row[f"{tag}_int_{n}"] = mi * 1000 if mi is not None else None
                row[f"{tag}_ref_{n}"] = float(np.median(ri)) * 1000 if ri else None
                row[f"{tag}_d_{n}"] = (mi - float(np.median(ri))) * 1000 if (mi is not None and ri) else None
        rows.append(row)
        f = lambda v, w=7, d=0: (f"{v:{w}.{d}f}" if v is not None else " " * (w - 3) + "n/a")
        print(f"  {p:5}{w:7d}{(f'{bd:+8d}' if bd is not None else '       -')}{f(row['now_minus_target'],8)}"
              f"{f(row['m4'])}{f(row['m4_ref'])}{f(row['m4_int_n'],8)}{f(row['m4_ref_n'],6)}{f(row['m4_d_n'],6)}{f(row['m4_d_o'],6)}"
              f"{f(row['m5_int_n'],8)}{f(row['m5_ref_n'],6)}{f(row['m5_d_n'],6)}{f(row['m5_d_o'],6)}")
    if a.json: json.dump(rows, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
