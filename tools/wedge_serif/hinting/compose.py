"""Set lines of text from converter-faithful 2-bit glyphs (hinting study).

Glyph bitmaps are exactly the converter's (raster.py, proven by validate.py);
the LAYOUT is HarfBuzz (kern + liga, the same features the firmware carries
as its kern matrix and ligature pairs) with each glyph placed at the rounded
pen position. That layout is shared by every arm -- the converter's advance
is `linearHoriAdvance`, unhinted, so hinting cannot move a glyph -- which
makes any difference between two arms' pictures a difference in the glyphs.

Levels are drawn 0..3 as paper..ink on a neutral ramp (255, 170, 85, 0);
where two glyph boxes overlap the darker level wins.
"""
import numpy as np
import freetype
import uharfbuzz as hb
from raster import quantize

RAMP = np.array([255, 170, 85, 0], np.uint8)


class Setter:
    def __init__(self, path, size, dpi, extra_flags):
        self.path, self.flags = path, extra_flags
        self.face = freetype.Face(path)
        s = size << 6 if isinstance(size, int) else int(size * 64)
        self.face.set_char_size(s, s, dpi, dpi)
        self.ppem = size * dpi / 72.0
        data = open(path, "rb").read()
        self.hbfont = hb.Font(hb.Face(hb.Blob(data)))
        self.upem = self.hbfont.face.upem
        self.hbfont.scale = (self.upem, self.upem)
        self.cache = {}
        m = self.face.size
        self.asc = m.ascender / 64.0
        self.line = m.height / 64.0

    def glyph(self, gid):
        if gid not in self.cache:
            self.face.load_glyph(gid, freetype.FT_LOAD_RENDER | self.flags)
            b = self.face.glyph.bitmap
            if b.rows and b.width:
                a = np.frombuffer(bytes(b.buffer), np.uint8).reshape(b.rows, abs(b.pitch))[:, :b.width]
                lv = quantize(a.copy())
            else:
                lv = np.zeros((0, 0), np.uint8)
            self.cache[gid] = (lv, self.face.glyph.bitmap_left, self.face.glyph.bitmap_top)
        return self.cache[gid]

    def shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hbfont, buf, {"kern": True, "liga": True})
        k = self.ppem / self.upem
        return [(i.codepoint, p.x_advance * k) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    def width(self, text):
        return sum(a for _, a in self.shape(text))

    def wrap(self, text, width):
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if cur and self.width(t) > width:
                lines.append(cur); cur = w
            else:
                cur = t
        if cur:
            lines.append(cur)
        return lines

    def set_lines(self, lines, width, pad=None, leading=None):
        pad = int(round(self.ppem * 0.4)) if pad is None else pad
        lh = int(round(leading or self.line))
        H = pad * 2 + lh * len(lines)
        out = np.zeros((H, width + 2 * pad), np.uint8)
        for n, text in enumerate(lines):
            base = pad + int(round(self.asc)) + n * lh
            pen = float(pad)
            for gid, adv in self.shape(text):
                lv, left, top = self.glyph(gid)
                if lv.size:
                    x0 = int(round(pen)) + left
                    y0 = base - top
                    h, w = lv.shape
                    ys, xs = max(0, -y0), max(0, -x0)
                    ye, xe = min(h, H - y0), min(w, out.shape[1] - x0)
                    if ye > ys and xe > xs:
                        reg = out[y0 + ys:y0 + ye, x0 + xs:x0 + xe]
                        np.maximum(reg, lv[ys:ye, xs:xe], out=reg)
                pen += adv
        return out


def to_gray(levels):
    return RAMP[levels]
