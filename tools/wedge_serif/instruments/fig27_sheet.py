"""The round-406 option sheet for the traced 2 and 7: one compact PNG.

For the roman and for the italic, a line of figures in context at 54 px,
UNHINTED (FreeType NO_HINTING, as the reader renders Albo since round 401),
shaped with HarfBuzz so the kern table is in it. Today's line on top, then one
line per arm, each labelled with the reference it traces and that reference's
OWN 2 and 7 drawn beside the label at the same x-height, for comparison.

    uv run --no-project --with uharfbuzz --with freetype-py --with numpy \\
      --with pillow python instruments/fig27_sheet.py --today DIR \\
      --arm o=DIR --arm p=DIR ... --out sheet.png
"""
import argparse, os, sys
import numpy as np
import freetype, uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fig27_trace import REFS

TEXT = "1927 2024 7:27 £72 27 of 72"
PPEM = 54
UI = "/System/Library/Fonts/Helvetica.ttc"
# which reference each arm letter traces, per style (docs/albo-figures-2-7-2026-09-26.md)
TRACE = {
    "Regular": {"o": "Georgia", "p": "Palatino", "q": "Hoefler Text", "r": "Big Caslon"},
    "Italic": {"o": "Flanker Griffo", "p": "Palatino Italic", "q": "Georgia Italic", "r": "Poetica"},
}


def line(path, text=TEXT, ppem=PPEM, index=0, glyph_names=None):
    """Grey (0 ink .. 255 paper) image of `text`, or of the named glyphs."""
    face = freetype.Face(path, index=index); face.set_char_size(ppem * 64)
    upm = face.units_per_EM
    if glyph_names:
        gl = [(face.get_name_index(n.encode()), None) for n in glyph_names]
    else:
        blob = hb.Blob.from_file_path(path); hf = hb.Font(hb.Face(blob, index))
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
        hb.shape(hf, buf, {"kern": True, "liga": True})
        gl = [(i.codepoint, p.x_advance) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]
    H = int(PPEM * 1.6); base = int(PPEM * 1.08)   # one row geometry for every size, so a reference sits on the same baseline
    canvas = np.zeros((H, max(ppem, PPEM) * (len(gl) + 2)), np.float32)
    pen = ppem * 0.1
    for gid, adv in gl:
        face.load_glyph(gid, freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_BITMAP)
        face.glyph.render(freetype.FT_RENDER_MODE_NORMAL)
        bm = face.glyph.bitmap
        if bm.rows:
            a = np.array(bm.buffer, np.float32).reshape(bm.rows, bm.pitch)[:, :bm.width] / 255.0
            x = int(round(pen)) + face.glyph.bitmap_left; y = base - face.glyph.bitmap_top
            y0, x0 = max(0, y), max(0, x)
            sub = a[y0 - y:min(H, y + bm.rows) - y, x0 - x:]
            canvas[y0:y0 + sub.shape[0], x0:x0 + sub.shape[1]] = np.maximum(
                canvas[y0:y0 + sub.shape[0], x0:x0 + sub.shape[1]], sub)
        pen += (adv * ppem / upm) if adv is not None else face.glyph.linearHoriAdvance / 65536.0 + ppem * 0.08
    w = int(pen + ppem * 0.1)
    return Image.fromarray((255 - canvas[:, :w] * 255).astype(np.uint8))


def ref_pair(label):
    for lab, p, i, g2, g7, *_ in REFS:
        if lab == label:
            f = freetype.Face(p, index=i); f.set_char_size(1000 * 64)
            f.load_char("x", freetype.FT_LOAD_NO_SCALE); xh = f.glyph.metrics.height
            ppem = int(round(PPEM * 0.429 * f.units_per_EM / xh))   # the reference's x-height = Albo's at 54 px
            return line(p, ppem=ppem, index=i, glyph_names=[g2, g7])
    raise KeyError(label)


def panel(style, today, arms, ui, uis, extra=(), mark=None):
    rows = [("today (shipped)", None, line(os.path.join(today, f"Albo-{style}.ttf")))]
    for k, d in arms:
        ref = TRACE[style][k]
        rows.append((f"{k}  traces {ref}" + ("  *" if mark == k else ""), ref_pair(ref), line(os.path.join(d, f"Albo-{style}.ttf"))))
    for lab, d in extra:
        rows.append((lab, None, line(os.path.join(d, f"Albo-{style}.ttf"))))
    LW = 300; W = LW + max(r[2].width for r in rows) + 10; RH = rows[0][2].height
    im = Image.new("L", (W, 34 + RH * len(rows)), 255); dr = ImageDraw.Draw(im)
    dr.text((10, 8), f"{'Roman' if style == 'Regular' else 'Italic'} -- 54 px, unhinted", font=ui, fill=0)
    for j, (lab, rp, ln) in enumerate(rows):
        y = 34 + j * RH
        dr.text((10, y + RH // 2 - 9), lab, font=uis, fill=60)
        if rp is not None: im.paste(rp.crop((0, 0, rp.width, min(rp.height, RH))), (LW - rp.width - 8, y))
        im.paste(ln, (LW, y))
    for j in range(1, len(rows)):
        dr.line([(0, 34 + j * RH), (W, 34 + j * RH)], fill=215)
    return im


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", required=True); ap.add_argument("--arm", action="append", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--extra-rom", action="append", default=[], help="LABEL=DIR, an extra roman row (a mixed recommendation)")
    ap.add_argument("--mark-it", help="the italic arm letter to star as recommended")
    ap.add_argument("--rows", action="append", default=[],
                    help="LABEL|DIR[|REFERENCE] -- an explicit row list for ONE style (--style), in place of --arm; round 408's variation sheet")
    ap.add_argument("--style", default="Italic")
    A = ap.parse_args()
    if A.rows:
        ui = ImageFont.truetype(UI, 17); uis = ImageFont.truetype(UI, 15)
        rows = [("today (shipped)", None, line(os.path.join(A.today, f"Albo-{A.style}.ttf")))]
        for r in A.rows:
            lab, d, *ref = r.split("|")
            rows.append((lab, ref_pair(ref[0]) if ref else None, line(os.path.join(d, f"Albo-{A.style}.ttf"))))
        LW = 430; W = LW + max(r[2].width for r in rows) + 10; RH = rows[0][2].height
        im = Image.new("L", (W, 34 + RH * len(rows)), 255); dr = ImageDraw.Draw(im)
        dr.text((10, 8), f"{A.style} -- 54 px, unhinted", font=ui, fill=0)
        for j, (lab, rp, ln) in enumerate(rows):
            y = 34 + j * RH
            dr.text((10, y + RH // 2 - 9), lab, font=uis, fill=60)
            if rp is not None: im.paste(rp.crop((0, 0, rp.width, min(rp.height, RH))), (LW - rp.width - 8, y))
            im.paste(ln, (LW, y))
        for j in range(1, len(rows)):
            dr.line([(0, 34 + j * RH), (W, 34 + j * RH)], fill=215)
        im.save(A.out); print(A.out, im.size); sys.exit(0)
    arms = [tuple(a.split("=", 1)) for a in A.arm]
    ui = ImageFont.truetype(UI, 17); uis = ImageFont.truetype(UI, 15)
    ex = [tuple(e.split("=", 1)) for e in A.extra_rom]
    ps = [panel("Regular", A.today, arms, ui, uis, extra=ex), panel("Italic", A.today, arms, ui, uis, mark=A.mark_it)]
    W = max(p.width for p in ps)
    out = Image.new("L", (W, sum(p.height for p in ps) + 12), 255); y = 0
    for p in ps: out.paste(p, (0, y)); y += p.height + 12
    out.save(A.out); print(A.out, out.size)
