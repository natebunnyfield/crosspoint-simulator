"""Reference sheets for the poor-characters pass (2026-09-26;
docs/albo-poor-characters-2026-09-26.md): one PNG per character and cut, Albo
today first and each reference face after it, labelled, in three bands:

  1. READER SIZE: the character as each face renders it (slanted, as set) at
     Albo's x-height at 54 ppem -- every reference is sized so ITS x-height
     equals Albo's, not so its em does -- FreeType UNHINTED, the reader's 2-bit
     levels (fit_audit/legib.Renderer's quantiser), native pixels;
  2. the same raster at 3x NEAREST;
  3. DRAWING SIZE: the letter unsheared by its measured slant at Albo's
     x-height 429 = 143 px (poor_trace's Face at 1/3 px per unit), one shared
     baseline, the baseline and x-height ruled. This is the band to draw from.

    python3 instruments/poor_refsheet.py --albo DIR --out OUTDIR [--chars y:Regular,y:Bold,...]
"""
import argparse, os, sys
import numpy as np
import freetype
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fit_audit"))
from poor_trace import PANEL, face, XH_ALBO  # noqa: E402
from geom import quantize  # noqa: E402  (the converter's 2-bit cut)

PAPER = (250, 249, 246); INK = np.array([20, 20, 20], float)
LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
ALBO_PPEM = 54.0
DEFAULT = ["y:Regular", "y:Bold", "t:Regular", "t:Bold", "j:Regular", "s:Regular", "N:Bold", "T:Bold",
           "j:Italic", "t:Italic", "y:Italic", "y:BoldItalic", "r:BoldItalic", "V:BoldItalic",
           "W:BoldItalic", "F:Italic", "q:BoldItalic"]


def spec(path_idx):
    p, i = path_idx
    return p, i


def reader_raster(path, idx, ch, xh_ratio):
    """ch at a size where this face's x-height = Albo's at 54 ppem; 2-bit levels."""
    f = freetype.Face(path, index=idx)
    ppem = ALBO_PPEM * xh_ratio
    f.set_char_size(int(round(ppem * 64)), 0, 72, 72)
    f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    b = f.glyph.bitmap
    a = np.frombuffer(bytes(b.buffer), np.uint8).reshape(b.rows, b.pitch)[:, :b.width] if b.rows else np.zeros((1, 1), np.uint8)
    return quantize(a), f.glyph.bitmap_top


def xh_units(path, idx):
    f = freetype.Face(path, index=idx)
    f.set_char_size(f.units_per_EM * 64, 0, 72, 72)
    f.load_char("x", freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING)
    return f.glyph.outline.get_bbox().yMax, f.units_per_EM


def rgb(levels):
    t = (levels / 3.0)[..., None]
    return (np.array(PAPER, float) * (1 - t) + INK * t).astype(np.uint8)


def band(cells, pad=14, label_h=18):
    """cells: [(label, img_array, baseline_row)] -> one row, shared baseline."""
    top = max(b for _, _, b in cells); bot = max(im.shape[0] - b for _, im, b in cells)
    H = top + bot + label_h + 6; W = sum(max(im.shape[1], 70) + pad for _, im, _ in cells) + pad
    canvas = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(canvas); x = pad
    for lab, im, b in cells:
        canvas.paste(Image.fromarray(im), (x, top - b))
        d.text((x, H - label_h), lab, fill=(90, 90, 90), font=LAB)
        x += max(im.shape[1], 70) + pad
    return canvas


def sheet(ch, cut, albo_dir):
    italic = "Italic" in cut
    faces = [("Albo today", (os.path.join(albo_dir, f"Albo-{cut}.ttf"), 0))] + [(l, (p, i)) for l, p, i in PANEL[cut]]
    axh, aupm = xh_units(*faces[0][1])
    r1, r2, r3 = [], [], []
    for lab, (p, i) in faces:
        try:
            xh, upm = xh_units(p, i)
            lv, top = reader_raster(p, i, ch, (axh / aupm) / (xh / upm))
            r1.append((lab, rgb(lv), top))
            big = np.kron(lv, np.ones((3, 3), np.uint8)); r2.append((lab, rgb(big), top * 3))
            F = face(p, i, italic)
            m, x0, yt, adv = F.mask(ch)                 # 2 px per unit
            im = Image.fromarray(((~m) * 255).astype(np.uint8)).resize((max(1, m.shape[1] // 6), max(1, m.shape[0] // 6)), Image.LANCZOS)
            a = np.array(im); a3 = np.stack([a] * 3, -1)
            base = int(round(yt * 2 / 6))
            # rule the baseline and the x-height through the letter's cell
            for yy in (base, base - int(round(XH_ALBO * 2 / 6))):
                if 0 <= yy < a3.shape[0]: a3[yy, ::3] = (200, 120, 120)
            r3.append((lab, a3, base))
        except Exception as e:
            print("skip", lab, e, file=sys.stderr)
    rows = [band(r1), band(r2), band(r3)]
    W = max(r.width for r in rows); H = sum(r.height for r in rows) + 28 + 2 * 10
    out = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(out)
    d.text((8, 6), f"{ch}  --  {cut}   (1) reader size, 2-bit   (2) 3x nearest   (3) unsheared at xh 429, drawing size",
           fill=(30, 30, 30), font=LAB)
    y = 28
    for r in rows:
        out.paste(r, (0, y)); y += r.height + 10
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--albo", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--chars", default=",".join(DEFAULT))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for sp in a.chars.split(","):
        ch, cut = sp.split(":")
        name = f"{ch if ch.islower() else ch + '_cap'}-{cut}.png"
        sheet(ch, cut, a.albo).save(os.path.join(a.out, name)); print(name)


if __name__ == "__main__":
    main()
