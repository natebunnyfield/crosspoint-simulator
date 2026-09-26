#!/usr/bin/env python3
"""Round 394 (thick/thin options, 2026-09-26): WHERE is a letter's thin, and
how does a candidate arm measure against a FIXED yardstick.

Two jobs, both on `cmp_weight_survey.measure`'s own method (unsheared raster at
xh 380 px, chamfer ridge, thickness = 2 x distance, no percentile threshold):

  map      draw each letter's mask with every ridge point thinner than
           --red units in red (and under --orange in orange), so a p10 is
           never taken on trust -- round 391's rule;
  measure  thin / cut / colour for the named letters of one font, each against
           the FAMILY MEDIAN OF A BASELINE SURVEY (`--base WS.json`, the
           as-shipped build). The yardstick is fixed on purpose: a median
           recomputed over the arm itself moves with the arm, which is the
           shrinking-control-set trap of docs/albo-method.md section 1f.

    python3 instruments/r394_thin_map.py map FONT.ttf "qpdb" OUT.png [--slant 13]
    python3 instruments/r394_thin_map.py measure FONT.ttf "qpdb" --base WS.json \
        --style italic [--slant 13]
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import cmp_weight_survey as ws  # noqa: E402
from r391_thick_thin import fam  # noqa: E402

XH = ws.XH


def ridge_map(ttf, ch, slant, px=380, red=24.0, orange=30.0):
    mask, base = ws.raster(ttf, ch, slant, px)
    d = ws.chamfer(mask)
    p = np.pad(d, 1, mode="constant"); c = p[1:-1, 1:-1]
    keep = (mask & (d >= 1.5) & (c >= p[1:-1, :-2]) & (c >= p[1:-1, 2:])
            & (c >= p[:-2, 1:-1]) & (c >= p[2:, 1:-1]))
    u = XH / px
    t = 2.0 * d * u
    rgb = np.full(mask.shape + (3,), 255, np.uint8)
    rgb[mask] = (200, 200, 200)
    ys, xs = np.nonzero(keep)
    for y, x in zip(ys, xs):
        col = (60, 60, 60)
        if t[y, x] < red: col = (220, 0, 0)
        elif t[y, x] < orange: col = (240, 140, 0)
        rgb[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = col
    return Image.fromarray(rgb)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["map", "measure"])
    ap.add_argument("ttf"); ap.add_argument("chars")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--slant", type=float, default=0.0)
    ap.add_argument("--red", type=float, default=24.0)
    ap.add_argument("--orange", type=float, default=30.0)
    ap.add_argument("--base"); ap.add_argument("--style", default="roman")
    ap.add_argument("--json")
    a = ap.parse_args()
    if a.mode == "map":
        ims = [ridge_map(a.ttf, ch, a.slant, red=a.red, orange=a.orange) for ch in a.chars]
        H = max(i.height for i in ims); W = sum(i.width for i in ims)
        sheet = Image.new("RGB", (W, H), (255, 255, 255)); x = 0
        for i in ims:
            sheet.paste(i, (x, H - i.height)); x += i.width
        sheet.save(a.out); print("wrote", a.out); return
    base = json.load(open(a.base))[a.style]
    rows = [r for g in base.values() for r in g]
    fams = {}
    for r in rows: fams.setdefault(fam(r["ch"]), []).append(r)
    med = {f: dict(thin=np.median([r["thin"] for r in rs]),
                   cut=np.median([r["thick"] / r["thin"] for r in rs]),
                   colour=np.median([r["colour"] for r in rs])) for f, rs in fams.items()}
    out = {}
    for ch in a.chars:
        r = ws.measure(a.ttf, ch, a.slant)
        m = med[fam(ch)]; cut = r["thick"] / r["thin"]
        out[ch] = dict(thin=r["thin"], thick=r["thick"], stroke=r["stroke"], cut=cut,
                       colour=r["colour"], dThin=r["thin"] / m["thin"] - 1,
                       dCut=cut / m["cut"] - 1, dCol=r["colour"] / m["colour"] - 1,
                       px27=r["thin"] * 27 / 1000.0)
        o = out[ch]
        print(f"  {ch}  thin {o['thin']:5.1f}  thick {o['thick']:5.1f}  cut {cut:4.2f}  "
              f"colour {o['colour']:.3f}  dThin {o['dThin']:+4.0%}  dCut {o['dCut']:+4.0%}  "
              f"dCol {o['dCol']:+4.0%}  px27 {o['px27']:.2f}")
    if a.json: json.dump(out, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
