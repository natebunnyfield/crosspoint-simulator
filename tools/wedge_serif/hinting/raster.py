"""Converter-faithful rasterizer for the hinting study (2026-09-26).

Replicates what the firmware's `lib/EpdFont/scripts/fontconvert_sdcard.py`
does to ONE glyph of a real (non-synthetic, no-rule) style:

  * `face.set_char_size(size << 6, size << 6, 150, 150)` -- 150 DPI, so the
    ppem is `pt * 150 / 72` (8 pt = 16.67 ppem);
  * `face.load_glyph(gi, FT_LOAD_RENDER)` -- FT_LOAD_DEFAULT hinting, target
    NORMAL, grayscale render. Albo carries no fpgm/prep/glyf instructions, so
    FreeType hands every glyph to the AUTOHINTER;
  * no gamma: the 8-bit coverage is taken as-is, cut to its top nibble and
    quantized to 2 bits at nibble >= 12 / 8 / 4, i.e. coverage >= 192 -> 3,
    >= 128 -> 2, >= 64 -> 1, else 0;
  * advance = `linearHoriAdvance` (UNHINTED), so hinting never moves a glyph's
    position, only its pixels.

`validate.py` checks this against the converter's own `rasterize_font_style`
bit for bit. An ARM is (font file, extra load flags):

  today   : shipped TTF, flags 0            (autohinter, NORMAL target)
  light   : shipped TTF, FT_LOAD_TARGET_LIGHT (autohinter, vertical only)
  nohint  : shipped TTF, FT_LOAD_NO_HINTING
  ttfa-*  : ttfautohint output, flags 0     (the font's own bytecode)
"""
import os
import numpy as np
import freetype

FT_LOAD_NO_HINTING = 0x2
FT_LOAD_TARGET_LIGHT = 0x10000  # FT_LOAD_TARGET_(FT_RENDER_MODE_LIGHT)

ARMS = {
    # name      font prefix   extra flags          label
    "today":   ("today",      0,                    "TODAY (autohinter)"),
    "ttfa-q":  ("ttfa-qsq",   0,                    "TTFAUTOHINT (default, gray=quantized)"),
    "ttfa-n":  ("ttfa-nnn",   0,                    "TTFAUTOHINT (gray=natural)"),
    "ttfa-s":  ("ttfa-sss",   0,                    "TTFAUTOHINT (gray=strong)"),
    "light":   ("today",      FT_LOAD_TARGET_LIGHT, "LIGHT autohint (vertical only)"),
    "nohint":  ("today",      FT_LOAD_NO_HINTING,   "NO HINTING"),
}

READER_PT = [8, 10, 12, 14, 16, 18]  # sd-fonts.yaml Albo `sizes:`


def sizes():
    """(key, pt_or_px, dpi, ppem, tier) for every measured size."""
    out = [("9px", 9, 72, 9.0, "9px")]
    for pt in READER_PT:
        out.append((f"{pt}pt", pt, 150, pt * 150 / 72, "1x"))
    for pt in READER_PT:
        out.append((f"{pt}pt@2x", pt * 2, 150, pt * 2 * 150 / 72, "2x"))
    return out


def font_path(fonts_dir, arm, style):
    return os.path.join(fonts_dir, f"{ARMS[arm][0]}-{style}.ttf")


def quantize(a8):
    """The converter's 8-bit -> 2-bit cut (via the 4-bit nibble)."""
    n = a8 >> 4
    return np.where(n >= 12, 3, np.where(n >= 8, 2, np.where(n >= 4, 1, 0))).astype(np.uint8)


class Glyph:
    __slots__ = ("cp", "a8", "lv", "left", "top", "adv")

    def __init__(self, cp, a8, left, top, adv):
        self.cp, self.a8, self.left, self.top, self.adv = cp, a8, left, top, adv
        self.lv = quantize(a8)


def render_set(path, size, dpi, extra_flags, cps):
    """{cp: Glyph} at this size, as the converter would rasterize it."""
    f = freetype.Face(path)
    f.set_char_size(size << 6 if isinstance(size, int) else int(size * 64),
                    size << 6 if isinstance(size, int) else int(size * 64), dpi, dpi)
    out = {}
    for cp in cps:
        gi = f.get_char_index(cp)
        if gi == 0:
            continue
        f.load_glyph(gi, freetype.FT_LOAD_RENDER | extra_flags)
        b = f.glyph.bitmap
        if b.rows and b.width:
            p = abs(b.pitch)
            a = np.frombuffer(bytes(b.buffer), dtype=np.uint8).reshape(b.rows, p)[:, :b.width]
            if b.pitch < 0:
                a = a[::-1]
        else:
            a = np.zeros((0, 0), np.uint8)
        out[cp] = Glyph(cp, a.copy(), f.glyph.bitmap_left, f.glyph.bitmap_top,
                        f.glyph.linearHoriAdvance / 65536.0)
    return out
