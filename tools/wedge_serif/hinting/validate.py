#!/usr/bin/env python3
"""Is raster.py the converter, bit for bit?

Imports `rasterize_font_style` from a COPY of the firmware's
lib/EpdFont/scripts (--conv), with one scratch patch: the env var
CPFONT_PRIMARY_LOAD_FLAGS_OR is OR'd into the primary face's load flags, so
the NO HINTING / LIGHT arms can be put through the real converter too. For
every arm, style and reader size (1x and 2x) it compares width, height, left,
top, advance (12.4 fixed) and the packed 2-bit bitmap of U+0020..U+007E and
U+00A0..U+00FF against raster.py.

    python3 validate.py --conv DIR --fonts DIR
"""
import argparse, os, sys, io, contextlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import raster  # noqa: E402

CPS = list(range(0x20, 0x7F)) + list(range(0xA0, 0x100))


def unpack(packed, w, h):
    n = w * h
    out = np.zeros(n, np.uint8)
    for i in range(n):
        out[i] = (packed[i // 4] >> (6 - 2 * (i % 4))) & 3
    return out.reshape(h, w) if n else np.zeros((0, 0), np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conv", required=True)
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--arms", default=",".join(raster.ARMS))
    a = ap.parse_args()
    sys.path.insert(0, a.conv)
    import fontconvert_sdcard as fc
    bad = 0
    total = 0
    for arm in a.arms.split(","):
        os.environ["CPFONT_PRIMARY_LOAD_FLAGS_OR"] = str(raster.ARMS[arm][1])
        for style, sid in (("Regular", 0), ("Italic", 2)):
            path = raster.font_path(a.fonts, arm, style)
            for key, sz, dpi, ppem, tier in raster.sizes():
                if dpi != 150:
                    continue
                with contextlib.redirect_stderr(io.StringIO()):
                    sd = fc.rasterize_font_style(path, sz, [(0x20, 0x7E), (0xA0, 0xFF)], style_id=sid)
                mine = raster.render_set(path, sz, dpi, raster.ARMS[arm][1], CPS)
                for g, packed in sd.all_glyphs:
                    m = mine.get(g.code_point)
                    if m is None:
                        continue
                    total += 1
                    lv = unpack(packed, g.width, g.height)
                    ok = (g.width == m.lv.shape[1] if m.lv.size else g.width == 0) and \
                         (g.height == m.lv.shape[0] if m.lv.size else g.height == 0) and \
                         g.left == m.left and g.top == m.top and \
                         g.advance_x == fc.fp4_from_ft16_16(int(round(m.adv * 65536))) and \
                         np.array_equal(lv, m.lv)
                    if not ok:
                        bad += 1
                        if bad <= 10:
                            print(f"MISMATCH {arm} {style} {key} U+{g.code_point:04X}")
            print(f"{arm:8s} {style:8s} checked", flush=True)
    print(f"{total} glyph renders compared, {bad} mismatches")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
