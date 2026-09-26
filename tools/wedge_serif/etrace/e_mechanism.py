#!/usr/bin/env python3
"""Measure the roman e's eye and mouth, in design units and as rendered.

The e has two whites: the EYE (the closed counter above the bar) and the
lower counter, which opens to the right through the MOUTH (between the bar's
underside and the exit terminal). An e reads as o when the mouth is shut and
the bar is lost in a closed ring.

DESIGN UNITS (FreeType at 1000 ppem, unhinted, so 1 px = 1 unit):
  bar      -- the bar's vertical ink run at the eye's center column
  eye_h    -- the eye's height at that column; eye_r its largest inscribed radius
  mouth    -- the widest disc that can travel from the lower counter's deepest
              point OUT to the exterior (maximin on the distance transform), as
              a diameter: the narrowest the mouth gets along its best path
  mouth_v  -- the vertical white between the terminal's top and the bar's
              underside, at the terminal's tip column

AS RENDERED (FreeType FT_LOAD_RENDER -- the AUTOHINTER, since Albo carries no
bytecode -- which is what the firmware's converter and the Kept Legibility
Index both ask for):
  hint_under@P -- how far the autohinter moves the bar's underside at P ppem
              (px, + = up), against FT_LOAD_NO_HINTING
  mouth@P   -- mouth_block(): for every pixel row whose center lies in the
              drawn mouth band, the darkest pixel a path must cross from the
              glyph's center column out past its right-most ink; the lightest
              such row. 0 = the mouth reads open, 1 = sealed by full ink.
              8-bit at index sizes, the converter's 2-bit above 16 ppem.

    python3 e_mechanism.py LABEL=FONT.ttf ... [--json out.json]
"""
import sys, json
import numpy as np
import freetype
from scipy import ndimage as ndi
from PIL import Image, ImageFilter


def render(path, ppem, ch="e", hinting=True, twobit=False, blur=0.0, pad=6):
    f = freetype.Face(path)
    f.set_pixel_sizes(0, ppem) if isinstance(ppem, int) else f.set_char_size(int(ppem * 64))
    flags = freetype.FT_LOAD_RENDER | (0 if hinting else freetype.FT_LOAD_NO_HINTING)
    f.load_char(ch, flags)
    b = f.glyph.bitmap
    a = np.frombuffer(bytes(b.buffer), dtype=np.uint8).reshape(b.rows, b.pitch)[:, :b.width].astype(float)
    if twobit:
        q = (a.astype(int) >> 4)
        a = np.select([q >= 12, q >= 8, q >= 4], [3, 2, 1], 0) / 3.0 * 255
    a = np.pad(a, pad)
    if blur:
        im = Image.fromarray((255 - a).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
        a = 255 - np.asarray(im, dtype=float)
    return a / 255.0, f.glyph.bitmap_top + pad, f.glyph.bitmap_left - pad   # ink coverage 0..1


def maximin(light, seed, exterior_mask, conn=2):
    """Largest t such that {light >= t} connects seed to the exterior
    (binary search: if t connects, every smaller t does too)."""
    levels = np.unique(light[light <= light[seed]])      # ascending
    st = ndi.generate_binary_structure(2, conn)
    def ok(t):
        lab, _ = ndi.label(light >= t, structure=st)
        L = lab[seed]
        return bool(L) and bool(np.any(exterior_mask & (lab == L)))
    lo, hi, best = 0, len(levels) - 1, 0.0
    while lo <= hi:
        mid = (lo + hi) // 2
        if ok(levels[mid]):
            best = float(levels[mid]); lo = mid + 1
        else:
            hi = mid - 1
    return best


def design(path):
    cov, top, left = render(path, 1000, hinting=False)
    ink = cov >= 0.5
    H, W = ink.shape
    white = ~ink
    lab, n = ndi.label(white)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    enclosed = [i for i in range(1, n + 1) if i not in border]
    eye = max(enclosed, key=lambda i: (lab == i).sum())
    ys, xs = np.nonzero(lab == eye)
    cxe = int(round(xs.mean()))
    col = ink[:, cxe]
    eye_bottom = ys[xs == cxe].max()            # row index (down is +)
    r = eye_bottom + 1
    while r < H and col[r]:
        r += 1
    bar = r - eye_bottom - 1
    bar_under_row = r
    dt_white = ndi.distance_transform_edt(white)
    eye_r = float(dt_white[lab == eye].max())
    eye_h = int((lab == eye)[:, cxe].sum())
    # lower counter seed: deepest white below the bar, inside the ink's bbox, left of center-right
    rows_in = np.nonzero(ink.any(1))[0]; cols_in = np.nonzero(ink.any(0))[0]
    sub = np.zeros_like(white)
    sub[bar_under_row:rows_in.max() - 5, cols_in.min() + 5:cxe + 1] = True
    cand = np.where(sub & white, dt_white, 0)
    seed = np.unravel_index(np.argmax(cand), cand.shape)
    ext = np.zeros_like(white); ext[:, -1] = True; ext[0] = True; ext[-1] = True; ext[:, 0] = True
    mouth = 2 * maximin(dt_white, seed, ext, conn=2)
    # terminal tip: the right-most ink below the bar underside
    lowR = ink.copy(); lowR[:bar_under_row + 1] = False
    tip_col = np.nonzero(lowR.any(0))[0].max() - 2
    tip_top = np.nonzero(lowR[:, tip_col])[0].min()
    # white above the terminal at that column up to the next ink
    rr = tip_top - 1
    while rr > 0 and not ink[rr, tip_col]:
        rr -= 1
    mouth_v = tip_top - rr - 1 if rr > 0 else None
    base = top  # baseline row = bitmap_top (+pad) from the top
    return dict(bar=int(bar), bar_underside=int(base - bar_under_row), eye_h=eye_h, eye_r=round(eye_r, 1),
                mouth=round(mouth, 1), mouth_v=mouth_v, xh_top=int(base - rows_in.min()), terminal_top=int(base - tip_top),
                lower_seed=(int(seed[0]), int(seed[1])), cxe=cxe), (cov, top, left)


def hint_shift(path, ppem, geo):
    """How far FreeType's AUTOHINTER moves the bar's two edges and the bowl's
    top, in px, at this ppem. The TTF carries no bytecode, so FT_LOAD_DEFAULT
    (what the index's renderer and the firmware's converter both ask for)
    falls to the autohinter; FT_LOAD_NO_HINTING is the drawn outline."""
    def pts(flags):
        f = freetype.Face(path); f.set_char_size(int(ppem * 64)); f.load_char("e", flags)
        return np.array(f.glyph.outline.points, float) / 64.0
    u, h = pts(freetype.FT_LOAD_NO_HINTING), pts(freetype.FT_LOAD_DEFAULT)
    s = ppem / 1000.0
    out = {}
    for name, yu in (("under", geo["bar_underside"]), ("bartop", geo["bar_underside"] + geo["bar"]),
                     ("top", geo["xh_top"])):
        sel = np.abs(u[:, 1] - yu * s) <= 6 * s
        out[name] = round(float((h[sel, 1] - u[sel, 1]).mean()), 3) if sel.any() else None
    return out


def mouth_block(path, ppem, geo, twobit=False, blur=0.0):
    """How SHUT the mouth is as rendered: for every pixel row whose center
    lies in the drawn mouth band (terminal top .. bar underside), the darkest
    pixel a path must cross going from the glyph's center column out past its
    right-most ink; the answer is the lightest such row. 0 = one row runs
    clear to the outside (the mouth reads open); 1 = every row is sealed
    by full ink."""
    cov, top, left = render(path, ppem, twobit=twobit, blur=blur, pad=3)
    s = ppem / 1000.0
    lo, hi = geo["terminal_top"] * s, geo["bar_underside"] * s
    inkcols = np.nonzero((cov > 0.05).any(0))[0]
    c0 = (inkcols.min() + inkcols.max()) // 2; c1 = inkcols.max()
    best = 1.0
    for r in range(cov.shape[0]):
        yc = top - r - 0.5            # the row's center, px above the baseline
        if lo <= yc <= hi:
            best = min(best, float(cov[r, c0:c1 + 1].max()))
    return round(best, 3)


SIZES = [8, 9, 9.5, 10, 12, 16.67, 20.83, 27.08, 33.33]   # 16.67.. = the reader's 8/10/13/16 pt at 150 dpi (1x)


def measure(path):
    geo, _ = design(path)
    for p in SIZES:
        hs = hint_shift(path, p, geo)
        geo[f"hint_under@{p}"] = hs["under"]; geo[f"hint_bartop@{p}"] = hs["bartop"]
        geo[f"mouth@{p}"] = mouth_block(path, p, geo, twobit=(p > 16))
    geo["mouth@9blur"] = mouth_block(path, 9, geo, blur=0.6)
    return geo


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    args = [a for a in args if a != out]
    res = {}
    for a in args:
        label, path = a.split("=", 1); print("measuring", label, path, file=sys.stderr)
        res[label] = measure(path)
    keys = ["bar", "bar_underside", "terminal_top", "mouth_v", "mouth", "eye_h", "eye_r"] + \
           [f"hint_under@{p}" for p in SIZES[:5]] + ["mouth@8", "mouth@9", "mouth@9blur", "mouth@9.5", "mouth@10", "mouth@16.67", "mouth@27.08"] + [f"hint_under@{p}" for p in SIZES[5:]]
    print(f"{'':14s}" + "".join(f"{k[:14]:>15s}" for k in keys))
    for label, g in res.items():
        print(f"{label:14s}" + "".join(f"{str(g.get(k)):>15s}" for k in keys))
    if out:
        json.dump(res, open(out, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
