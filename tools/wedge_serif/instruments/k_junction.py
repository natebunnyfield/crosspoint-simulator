#!/usr/bin/env python3
"""k_junction.py -- where does the K's leg meet its arm? (docs/albo-k-junction-2026-10-04.md)

    $VENV/bin/python instruments/k_junction.py [--sheet OUT.png] LABEL=FONT[:IDX] ...

Each K is rendered unhinted at a 300 px cap height. The white wedge between the arm and the leg
is flood-filled from a seed between them in a column 70% of the way out, kept left of that column
so it cannot leak round the arm's tip; its leftmost point is the junction (the crotch). Reported: how far right of the stem's right edge (at 0.25 of the cap) and
how high, both in cap heights, and how far out along the arm (0 = at the stem, 1 = at the arm's
tip) -- the arm is the ink run that reaches the box's top-right.
"""
import sys, os
import numpy as np, freetype
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont
CH = 300


def measure(path, idx=0):
    f = freetype.Face(path, idx)
    f.load_char("H", freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING); cap = f.glyph.outline.get_bbox().yMax
    f.set_char_size(int(round(CH * f.units_per_EM / cap * 64)), 0, 72, 72)
    f.load_char("K", freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width]; ink = a >= 128; top = f.glyph.bitmap_top
    H, W = ink.shape
    r25 = int(top - CH * 0.25); xs = np.nonzero(ink[r25])[0]; sr0 = xs[0]
    while sr0 + 1 < W and ink[r25, sr0 + 1]: sr0 += 1
    # the wedge: seed between the arm and the leg in a column 70% of the way out, flood-fill the
    # white kept LEFT of that column (so it cannot leak round the arm's tip), take its leftmost point
    tip_x = np.nonzero(ink[max(0, int(top - CH)):int(top - CH * 0.85) + 1].any(0))[0].max()
    foot_x = np.nonzero(ink[int(top - CH * 0.15):int(top) + 1].any(0))[0].max()
    xs_ = int(sr0 + 0.70 * (min(tip_x, foot_x) - sr0))
    col = ink[:, xs_]; runs = []; y = int(top - CH * 0.98)
    while y < int(top):
        if col[y]:
            y0 = y
            while y < H and col[y]: y += 1
            runs.append((y0, y))
        else: y += 1
    best = None
    if len(runs) >= 2:
        seed = ((runs[0][1] + runs[1][0]) // 2, xs_)
        sub = ~ink[:, :xs_ + 1]
        lab, _ = ndi.label(sub)
        k = lab[seed]
        if k:
            ys, xs = np.nonzero(lab == k)
            i = xs.argmin(); best = (xs[i], ys[i], len(xs))
    if best is None: return None, (a, top)
    cx, cy = best[0], best[1]
    frac = (cx - sr0) / max(1, tip_x - sr0)
    return dict(dx=(cx - sr0) / CH, y=(top - cy) / CH, along=frac, px=(cx, cy)), (a, top)


if __name__ == "__main__":
    args = sys.argv[1:]; sheet = None
    if args and args[0] == "--sheet": sheet = args[1]; args = args[2:]
    cells = []; LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    for spec in args:
        lab, rest = spec.split("=", 1); path, _, idx = rest.partition(":")
        m, (a, top) = measure(path, int(idx or 0))
        print(f"{lab:14s} " + (f"junction {m['dx']:.3f} cap right of the stem, at {m['y']:.3f} of the cap, {m['along']:.2f} of the way along the arm" if m else "no junction found"))
        if sheet:
            im = Image.new("L", (a.shape[1] + 40, CH + 90), 250); im.paste(Image.fromarray(255 - a), (20, 60 + CH - top), Image.fromarray(a))
            d = ImageDraw.Draw(im); d.text((6, 4), lab, fill=0, font=LAB)
            if m: x, y = m["px"]; d.ellipse([20 + x - 7, 60 + CH - top + y - 7, 20 + x + 7, 60 + CH - top + y + 7], outline=120, width=3)
            cells.append(np.array(im.convert("RGB")))
    if sheet:
        Hh = max(c.shape[0] for c in cells)
        rows = [cells[i:i + 5] for i in range(0, len(cells), 5)]
        Wmax = max(sum(c.shape[1] for c in r) for r in rows)
        out = []
        for r in rows:
            rr = np.concatenate([np.concatenate([c, np.full((Hh - c.shape[0], c.shape[1], 3), 250, np.uint8)], 0) for c in r], 1)
            out.append(np.concatenate([rr, np.full((Hh, Wmax - rr.shape[1], 3), 250, np.uint8)], 1))
        Image.fromarray(np.concatenate(out, 0)).save(sheet)



def lower(path, idx=0, root=0.45):
    """The K's OTHER connection: where the arm leaves the stem -- its underside (the apex of the
    lower-left counter) and its upper edge, as heights in cap units, read in the column two pixels
    right of the stem's right edge (the arm is the ink run holding the half-cap row there)."""
    f = freetype.Face(path, idx)
    f.load_char("H", freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING); cap = f.glyph.outline.get_bbox().yMax
    f.set_char_size(int(round(CH * f.units_per_EM / cap * 64)), 0, 72, 72)
    f.load_char("K", freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width]; ink = a >= 128; top = f.glyph.bitmap_top
    H, W = ink.shape
    r25 = int(top - CH * 0.25); xs = np.nonzero(ink[r25])[0]; sr0 = xs[0]
    while sr0 + 1 < W and ink[r25, sr0 + 1]: sr0 += 1
    col = ink[:, sr0 + 2]; runs = []; y = int(top - CH * 0.98)
    while y < min(H, int(top)):
        if col[y]:
            y0 = y
            while y < H and col[y]: y += 1
            runs.append((y0, y))
        else: y += 1
    # the arm is the LOWEST ink run whose bottom lies above the root's row (it has risen off the
    # root by the stem's edge) and whose top is under the stem's top wedge
    mid = int(top - CH * root)
    arm = [r for r in runs if r[1] <= mid + CH * 0.12 and r[0] >= top - CH * 0.9]
    if not arm: return None
    a_ = max(arm, key=lambda r: r[1])
    return dict(arm_under=(top - a_[1]) / CH, arm_over=(top - a_[0]) / CH)
