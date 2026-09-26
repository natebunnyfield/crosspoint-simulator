#!/usr/bin/env python3
"""Kernagic (Oeyvind Kolaas, GPL-3.0, C + GTK2) run non-interactively on Albo.

SOURCE. github.com/hodefoting/kernagic, last commit 2019-03-27. Builds on
macOS 26 with `brew install gtk+` (62 MB) and
    make CFLAGS="-O2 -g -D_GNU_SOURCE -D_DARWIN_C_SOURCE -Wno-deprecated-declarations"
(stock `make` fails: strdup undeclared under -std=c99). Its non-interactive
mode is `kernagic IN.ufo -m METHOD -o OUT.ufo`; it rewrites sidebearings only
(no kerning). The compiled-in methods are `original` (no change), `bounds`
(bbox, zero bearings) and `gap` ("snap gap": each glyph's outermost detected
stems are placed `gap` x-heights from the advance edges, advance snapped to
`snap` units). `gap` is the only spacing method; it is what is scored.

TRAP: the default snap is 0 and `gap` divides by it, so every advance comes
back 0 unless `-s` is passed. `-s 1` (the CLI's own floor) is used here.

    $VENV/bin/python run_kernagic.py --kernagic PATH/TO/kernagic [--gap 0.3] [--fontset 0920]
"""
import argparse, json, os, subprocess, sys, tempfile, time
import extractor, ufoLib2
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def sidebearings(ufo, names):
    out = {}
    for ch, n in names.items():
        g = ufo[n]; p = BoundsPen(ufo); g.draw(p)
        out[ch] = (float(p.bounds[0]), float(g.width - p.bounds[2]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kernagic", required=True)
    ap.add_argument("--gap", type=float, default=0.3)
    ap.add_argument("--fontset", default="0920")
    a = ap.parse_args()
    T = C.Truth()
    white, meta = {}, {}
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        for s in C.STYLES:
            src = C.FONTSETS[a.fontset][s]
            u = ufoLib2.Font(); extractor.extractUFO(src, u)
            ufo_in = os.path.join(tmp, f"{s}.ufo"); ufo_out = os.path.join(tmp, f"{s}-kg.ufo")
            u.save(ufo_in, overwrite=True)
            subprocess.run([a.kernagic, ufo_in, "-m", "gap", "-s", "1", "-g", str(a.gap), "-o", ufo_out],
                           check=True, capture_output=True)
            cmap = TTFont(src).getBestCmap()
            chars = sorted({c for p in T.P[s] for c in p})
            sb = sidebearings(ufoLib2.Font.open(ufo_out), {c: cmap[ord(c)] for c in chars})
            white[s] = {p: sb[p[0]][1] + sb[p[1]][0] for p in T.P[s]}
            meta[s] = {c: [round(v[0]), round(v[1])] for c, v in sb.items()}
    name = "kernagic-gap" if a.gap == 0.3 else f"kernagic-gap{a.gap:g}"
    print(C.save_preds(name, a.fontset, white, {"gap": a.gap, "snap": 1, "sidebearings": meta,
                                                "seconds": round(time.time() - t0, 2)}))


if __name__ == "__main__":
    main()
