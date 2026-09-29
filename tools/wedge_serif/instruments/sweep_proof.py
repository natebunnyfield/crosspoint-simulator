"""sweep_proof.py -- before/after proof rows: one text, several fonts, at a DISPLAY size and at the
READER's sizes, labeled, lossless.

    venv/bin/python instruments/sweep_proof.py out.png "text" "LABEL::FONT.ttf" ...
    env: PPEM (display size, default 140), READ (1 = add the reader rows, default 1), LABPX (label px)

Display row: HarfBuzz-shaped (kerns in), FreeType unhinted, 8-bit gray, at PPEM, native pixels.
Reader rows: fit_audit/legib.Renderer (the reader's converter: unhinted, 2-bit levels, HarfBuzz
placement) at 10 pt X3 (20.8 ppem) x5, 12 pt X3 x4, 8 pt phone (33.3) x3 and 10 pt phone (41.7) x3,
magnified by an integer factor with NEAREST -- the figure rules in CLAUDE.md (lossless, not shrunk,
the crop contains the thing). Written 2026-09-28 for the issue sweep.
"""
import os, sys
import numpy as np, freetype, uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fit_audit"))
from legib import Renderer  # noqa: E402

out = sys.argv[1]; text = sys.argv[2]; specs = [s.split("::") for s in sys.argv[3:]]
PPEM = int(os.environ.get("PPEM", "140")); READ = os.environ.get("READ", "1") == "1"
LABPX = int(os.environ.get("LABPX", "20"))   # label size in px: 72 puts an option's NUMBER big on its row (round 2 of the sweep)
LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", LABPX)
PAPER = (250, 249, 246)


def display(path):
    face = freetype.Face(path); face.set_pixel_sizes(0, PPEM)
    hf = hb.Font(hb.Face(hb.Blob.from_file_path(path))); upm = face.units_per_EM
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(hf, buf, {"kern": True})
    k = PPEM / upm; H = int(PPEM * 1.45); base = int(PPEM * 1.05)
    W = int(sum(p.x_advance for p in buf.glyph_positions) * k) + PPEM * 2
    c = np.zeros((H, W), np.uint8); x = float(PPEM) * 0.6
    for inf, pos in zip(buf.glyph_infos, buf.glyph_positions):
        face.load_glyph(inf.codepoint, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = face.glyph.bitmap
        if b.rows:
            a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width]
            gx = int(round(x + pos.x_offset * k)) + face.glyph.bitmap_left; gy = base - face.glyph.bitmap_top
            y0, x0 = max(0, gy), max(0, gx); y1, x1 = min(H, gy + a.shape[0]), min(W, gx + a.shape[1])
            c[y0:y1, x0:x1] = np.maximum(c[y0:y1, x0:x1], a[y0 - gy:y1 - gy, x0 - gx:x1 - gx])
        x += pos.x_advance * k
    xs = np.nonzero(c.any(0))[0]; c = c[:, :xs[-1] + 20]
    ci = c.astype(np.int32)
    return np.stack([v - ci * (v - 20) // 255 for v in PAPER], -1).astype(np.uint8)


def reader(path):
    """The four reader sizes, each its own row (a row per size keeps the image narrow enough to see)."""
    rows = []
    for ppem, mag in ((150 / 72 * 10, 5), (150 / 72 * 12, 4), (150 / 72 * 16, 3), (150 / 72 * 20, 3)):
        R = Renderer(path, 0, ppem)
        c = np.zeros((int(ppem * 1.5), int(ppem * 0.9 * len(text)) + int(ppem * 1.6)), np.uint8)
        R.line(text, c, int(ppem * 0.8), int(ppem * 1.1))   # x0 clear of an italic's negative bearings (legib's line does not clip)
        xs = np.nonzero(c.any(0))[0]; c = c[:, :xs[-1] + 6] if len(xs) else c
        g = np.kron(c, np.ones((mag, mag), np.uint8))
        lv = np.array([PAPER, (175, 175, 172), (100, 100, 98), (20, 20, 20)], np.uint8)
        rows.append(lv[np.minimum(g, 3)])
    return rows


parts = []
for lab, path in specs:
    head = Image.new("RGB", (1400, int(LABPX * 1.5)), PAPER); ImageDraw.Draw(head).text((8, LABPX // 4), lab, fill=(30, 30, 30), font=LAB)
    parts.append(np.array(head)); parts.append(display(path))
    if READ:
        parts += reader(path)
W = max(p.shape[1] for p in parts)
img = np.concatenate([np.concatenate([p, np.full((p.shape[0], W - p.shape[1], 3), PAPER, np.uint8)], 1) for p in parts], 0)
Image.fromarray(img).save(out); print(out, img.shape)
