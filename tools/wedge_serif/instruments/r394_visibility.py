#!/usr/bin/env python3
"""Round 394 (2026-09-26): is an arm's change VISIBLE at reading size?

Owner, on the first round-394 page: *"i dont see differences in thick thin"*.
He was right. The p10 instrument (r391_thick_thin / r394_thin_map) reports a
hairline moving 27 -> 32 units, and that is 0.1 px at a 27 px em. This answers
the question the p10 cannot: how much ink does each letter gain, and how many
pixels change, AS RENDERED.

Two measures per letter, arm B against arm A (both TTFs):
  geo      ink change of the OUTLINE, rasterised unhinted (16x supersample,
           box filter) -- the true thickness change, independent of the grid;
  ft 1x/2x ink change and pixels changed >8 levels, rendered by FreeType's
           default load (what PIL and the reader's fontconvert_sdcard.py
           FT_LOAD_RENDER both use) at 27 px and 54 px.

THE FINDING THAT MADE THIS NECESSARY: FreeType's default load on Albo (no
bytecode) behaves exactly like FT_LOAD_FORCE_AUTOHINT -- stems snap to the
pixel grid. A join change that moves the roman n's outline ink by +0.4%
renders +10.2% at 54 px (a whole column flips on the right stem), and the
same machinery can erase a real sub-pixel lift. So `ft` is what the reader
sees and `geo` is what was drawn; a proof must report both.

    python3 instruments/r394_visibility.py A.ttf B.ttf "qpdb" [--slant 0]
"""
import argparse, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.basePen import BasePen
_F = {}
def font(p):
    if p not in _F: _F[p] = TTFont(p)
    return _F[p]
class _Poly(BasePen):
    def __init__(s, gs): super().__init__(gs); s.polys = []; s.cur = []
    def _moveTo(s, p): s.cur = [p]
    def _lineTo(s, p): s.cur.append(p)
    def _curveToOne(s, a, b, c):
        p0 = s.cur[-1]
        for i in range(1, 9):
            t = i / 8; u = 1 - t
            s.cur.append((u**3*p0[0]+3*u*u*t*a[0]+3*u*t*t*b[0]+t**3*c[0], u**3*p0[1]+3*u*u*t*a[1]+3*u*t*t*b[1]+t**3*c[1]))
    def _qCurveToOne(s, a, b):
        p0 = s.cur[-1]
        for i in range(1, 9):
            t = i / 8; u = 1 - t
            s.cur.append((u*u*p0[0]+2*u*t*a[0]+t*t*b[0], u*u*p0[1]+2*u*t*a[1]+t*t*b[1]))
    def _closePath(s): s.polys.append(s.cur); s.cur = []
def glyph_polys(path, ch):
    f = font(path); gs = f.getGlyphSet(); n = f.getBestCmap()[ord(ch)]
    pen = _Poly(gs); gs[n].draw(pen); return pen.polys, f["hmtx"][n][0]
def render(path, text, px, w, h, x0, base, positions=None, ss=16):
    """coverage array (h, w) in 0..1; text laid out on the font's own advances
    (no kerning) unless `positions` (px) is given."""
    upm = font(path)["head"].unitsPerEm; k = px / upm * ss
    im = Image.new("L", (w * ss, h * ss), 0); d = ImageDraw.Draw(im)
    x = x0
    for i, ch in enumerate(text):
        polys, adv = glyph_polys(path, ch) if ch != " " else ([], font(path)["hmtx"]["space"][0])
        ox = positions[i] if positions else x
        # nonzero winding: draw even-odd via XOR layers is wrong for overlaps; use
        # outer-fill then holes: fontTools contours are wound; approximate by
        # filling each contour with XOR on a mask.
        m = Image.new("1", im.size, 0)
        for poly in polys:
            pts = [((ox + px_ * px / upm) * ss, (base - py * px / upm) * ss) for px_, py in poly]
            layer = Image.new("1", im.size, 0); ImageDraw.Draw(layer).polygon(pts, fill=1)
            m = Image.fromarray(np.asarray(m) ^ np.asarray(layer))
        im.paste(255, mask=m)
        x += adv * px / upm
    a = np.asarray(im, dtype=float).reshape(h, ss, w, ss).mean(axis=(1, 3)) / 255.0
    return a


def ft_cov(path, ch, px):
    h = int(px * 1.6); w = int(px * 1.2); base = int(px * 1.15)
    im = Image.new("L", (w, h), 0)
    ImageDraw.Draw(im).text((int(px * 0.15), base), ch, font=ImageFont.truetype(path, px), fill=255, anchor="ls")
    return np.asarray(im, dtype=float) / 255.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("chars")
    a = ap.parse_args()
    for ch in a.chars:
        A = render(a.a, ch, 200, 260, 330, 20, 250); B = render(a.b, ch, 200, 260, 330, 20, 250)
        row = [f"{ch}  geo {100 * (B.sum() - A.sum()) / A.sum():+5.1f}%"]
        for key, px in (("1x", 27), ("2x", 54)):
            fa, fb = ft_cov(a.a, ch, px), ft_cov(a.b, ch, px)
            chg = (np.abs(fa - fb) * 255 > 8).sum() / max(1, ((fa > .5) | (fb > .5)).sum())
            row.append(f"ft {key} ink {100 * (fb.sum() - fa.sum()) / fa.sum():+5.1f}%  px {100 * chg:4.0f}%")
        print("   ".join(row))


if __name__ == "__main__":
    main()
