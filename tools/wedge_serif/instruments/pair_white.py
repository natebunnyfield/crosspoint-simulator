"""Mean white between two letters across the x-height (rows 0.15-0.85 xh),
shaped with HarfBuzz (kerning included), unhinted at 1000 ppem: for each row,
the gap from the left letter's rightmost ink to the right letter's leftmost
ink; the mean over rows where both have ink. Owner 2026-09-27: "matching the
other letters and maximizing word image" -- the a's bearing is set from its
bounding box, so a new shape needs its WHITE checked, not its lsb.

    venv/bin/python instruments/pair_white.py FONT.ttf na an da ad oa ao ...
"""
import sys, numpy as np, freetype, uharfbuzz as hb
path = sys.argv[1]; face = freetype.Face(path); face.set_pixel_sizes(0, 1000)
blob = hb.Blob.from_file_path(path); hf = hb.Face(blob); font = hb.Font(hf); upm = hf.upem
xh = 429
def glyph_mask(gid):
    face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = face.glyph.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] > 127
    return a, face.glyph.bitmap_left, face.glyph.bitmap_top
out = []
for pair in sys.argv[2:]:
    buf = hb.Buffer(); buf.add_str(pair); buf.guess_segment_properties(); hb.shape(font, buf, {"kern": True})
    x = 0; rows = {}
    for k, (info, pos) in enumerate(zip(buf.glyph_infos, buf.glyph_positions)):
        a, l, t = glyph_mask(info.codepoint); ox = x + pos.x_offset * 1000 / upm
        for yy in range(a.shape[0]):
            y = t - yy
            if not (0.15 * xh <= y <= 0.85 * xh): continue
            xs = np.where(a[yy])[0]
            if len(xs): rows.setdefault(y, [None, None])[k] = (ox + l + xs.min(), ox + l + xs.max())
        x += pos.x_advance * 1000 / upm
    gaps = [r[1][0] - r[0][1] for r in rows.values() if r[0] and r[1]]
    out.append(f"{pair} {np.mean(gaps):5.0f}")
print("  ".join(out))
