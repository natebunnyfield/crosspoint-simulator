# shaped (harfbuzz: GPOS kerning applied) word rows, one per font, at one x-height; lossless gray
# python words_hb.py out.png XHPX "LABEL::font.ttf::text" ...
import sys, numpy as np, freetype, uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]; XH = int(sys.argv[2]); specs = [s.split("::") for s in sys.argv[3:]]
LF = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(XH * 0.55))
rows = []
for lab, path, text in specs:
    blob = hb.Blob.from_file_path(path); face = hb.Face(blob); font = hb.Font(face)
    upem = face.upem
    ft = freetype.Face(path); ft.set_pixel_sizes(0, 1000); ft.load_char('x', freetype.FT_LOAD_NO_SCALE)
    xh_units = ft.glyph.metrics.height
    px = XH * upem / xh_units
    ft.set_char_size(int(px * 64)); 
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(font, buf, {"kern": True, "liga": True})
    H = int(XH * 2.3); base = int(XH * 1.7); LW = int(XH * 1.6)
    W = LW + int(sum(p.x_advance for p in buf.glyph_positions) * px / upem) + 40
    im = Image.new("L", (W, H), 250); d = ImageDraw.Draw(im)
    d.text((10, base - int(XH * 0.75)), lab, fill=40, font=LF)
    x = float(LW)
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        ft.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        b = ft.glyph.bitmap
        if b.rows:
            a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width]
            gx = int(round(x + pos.x_offset * px / upem)) + ft.glyph.bitmap_left
            im.paste(Image.fromarray(255 - a), (gx, base - ft.glyph.bitmap_top), Image.fromarray(a))
        x += pos.x_advance * px / upem
    rows.append(im.crop((0, 0, min(W, int(x) + 30), H)))
W = max(r.width for r in rows); o = Image.new("L", (W, sum(r.height for r in rows)), 250); y = 0
for r in rows: o.paste(r, (0, y)); y += r.height
o.save(out); print(out, o.size)
