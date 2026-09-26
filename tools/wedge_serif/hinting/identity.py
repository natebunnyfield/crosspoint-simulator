#!/usr/bin/env python3
"""How many of an arm's glyphs are the SAME 2-bit bitmap as another arm's?

For each pair of arms, style and size: the share of U+0020..U+007E whose
converter bitmap (levels, width, height, left, top) is identical. It answers
"is ttfautohint just LIGHT autohinting by another road" and "how much of the
face does hinting actually touch" without a reader in the loop.

    python3 identity.py --fonts DIR
"""
import argparse, os, sys, itertools
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import raster  # noqa: E402

CPS = [c for c in range(0x21, 0x7F)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--pairs", default="today:ttfa-q,today:light,today:nohint,ttfa-q:light,ttfa-q:nohint,light:nohint,ttfa-q:ttfa-n,ttfa-q:ttfa-s")
    a = ap.parse_args()
    keys = [s for s in raster.sizes() if s[0] != "8pt@2x"]
    print(f"{'pair':20s} {'style':8s}" + "".join(f"{k[0]:>9s}" for k in keys))
    for pair in a.pairs.split(","):
        x, y = pair.split(":")
        for style in ("Regular", "Italic"):
            row = []
            for key, sz, dpi, ppem, tier in keys:
                gx = raster.render_set(raster.font_path(a.fonts, x, style), sz, dpi, raster.ARMS[x][1], CPS)
                gy = raster.render_set(raster.font_path(a.fonts, y, style), sz, dpi, raster.ARMS[y][1], CPS)
                same = sum(1 for c in CPS if c in gx and gx[c].left == gy[c].left and gx[c].top == gy[c].top
                           and gx[c].lv.shape == gy[c].lv.shape and np.array_equal(gx[c].lv, gy[c].lv))
                row.append(100.0 * same / len(gx))
            print(f"{pair:20s} {style:8s}" + "".join(f"{v:9.0f}" for v in row))


if __name__ == "__main__":
    main()
