#!/usr/bin/env python3
"""The e hint gate's own sweep (8..12 ppem in quarter pixels, 8-bit coverage,
limit 0.15), run for every hinting ARM rather than only for FreeType's
default. Also the same sweep on the 2-bit levels the device would get.

    python3 gate_sweep.py --fonts DIR [--style Regular]
"""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import raster  # noqa: E402
from measure import e_band, mouth_block  # noqa: E402

LIMIT = 0.15


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    res = {}
    for arm in raster.ARMS:
        path = raster.font_path(a.fonts, arm, "Regular")
        band = e_band(path)
        rows = []
        for q in range(32, 49):
            ppem = q / 4.0
            g = raster.render_set(path, ppem, 72, raster.ARMS[arm][1], [ord("e")])[ord("e")]
            rows.append((ppem, mouth_block(g.a8 / 255.0, g.top, ppem, band),
                         mouth_block(g.lv / 3.0, g.top, ppem, band)))
        w8 = max(rows, key=lambda r: r[1]); w2 = max(rows, key=lambda r: r[2])
        fails = [r[0] for r in rows if r[1] > LIMIT]
        res[arm] = dict(worst8=w8[1], worst8_at=w8[0], worst2=w2[2], worst2_at=w2[0],
                        fails_at=fails, verdict="FAIL" if fails else "ok")
        print(f"{arm:8s} {res[arm]['verdict']:4s} worst 8-bit {w8[1]:.3f} @ {w8[0]:5.2f}  "
              f"worst 2-bit {w2[2]:.3f} @ {w2[0]:5.2f}  failing sizes {fails}")
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
