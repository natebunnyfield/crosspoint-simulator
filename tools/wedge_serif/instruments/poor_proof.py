"""One proof image per character for the poor-characters pass (2026-09-26;
docs/albo-poor-characters-2026-09-26.md).

Each image: for every cut the character was flagged in, today's build on top
and each arm beneath, labelled; a row is the character in two words from the
owner's own books (proof_words.corpus()) at the reader's size, 54 px, FreeType
UNHINTED and 2-bit (fit_audit/legib.Renderer, the reader's pipeline since
round 401), and beside it the letter alone at the same 54 px, magnified 3x
NEAREST. Lossless PNG at native pixels; no scaling anywhere after the raster.

    python3 instruments/poor_proof.py SPEC.json OUTDIR
SPEC: {"y": {"cuts": ["Regular", "Bold"], "words": ["every", "yearly"],
             "arms": [["today", DIR], ["traced: Georgia", DIR], ...]}, ...}
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "fit_audit"))
from legib import Renderer  # noqa: E402
import uharfbuzz as hb  # noqa: E402

PPEM = 54
PAPER = np.array([250, 249, 246], float)
INK = np.array([20, 20, 20], float)
LABEL = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)


def line(R, text):
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(R.hbf, buf, {"kern": True})
    k = PPEM / R.upm
    H = int(PPEM * 1.55); base = int(PPEM * 1.08)
    W = int(PPEM * 0.9 * len(text)) + 20
    c = np.zeros((H, W), np.uint8); x = 6.0; right = 0
    for inf, pos in zip(buf.glyph_infos, buf.glyph_positions):
        lv, left, top = R.glyph(inf.codepoint)
        gx = int(round(x + pos.x_offset * k)) + left; gy = base - top
        if lv.size:
            h, w = lv.shape
            sub = c[max(gy, 0):gy + h, gx:gx + w]
            np.maximum(sub, lv[max(0, -gy):max(0, -gy) + sub.shape[0], :sub.shape[1]], out=sub)
            right = max(right, gx + w)
        x += pos.x_advance * k
    return c[:, :right + 6]


def rgb(levels):
    t = (levels / 3.0)[..., None]
    return (PAPER * (1 - t) + INK * t).astype(np.uint8)


def row(label, path, words, ch):
    R = Renderer(path, 0, PPEM)
    w = line(R, "  ".join(words))
    g = line(R, ch)
    ys = np.nonzero(g.any(1))[0]
    g = g[max(ys[0] - 2, 0):ys[-1] + 3]            # the letter's own ink rows, then 3x NEAREST
    g = np.kron(g, np.ones((3, 3), np.uint8))
    lab = Image.new("RGB", (190, w.shape[0]), tuple(int(v) for v in PAPER))
    ImageDraw.Draw(lab).text((6, w.shape[0] // 2 - 9), label, fill=(90, 90, 90), font=LABEL)
    parts = [np.array(lab), rgb(w), np.full((w.shape[0], 16, 3), PAPER, np.uint8)]
    gi = rgb(g)
    parts_img = np.concatenate([np.concatenate(parts, 1)], 0)
    Hh = max(parts_img.shape[0], gi.shape[0])
    def padh(a):
        return np.concatenate([a, np.full((Hh - a.shape[0], a.shape[1], 3), PAPER, np.uint8)], 0)
    return np.concatenate([padh(parts_img), padh(gi)], 1)


def stack(rows, gap=2, rule=False):
    W = max(r.shape[1] for r in rows)
    out = []
    for r in rows:
        out.append(np.concatenate([r, np.full((r.shape[0], W - r.shape[1], 3), PAPER, np.uint8)], 1))
        out.append(np.full((gap, W, 3), (205, 203, 198) if rule else PAPER, np.uint8))
    return np.concatenate(out[:-1], 0)


def header(text, W):
    im = Image.new("RGB", (W, 26), tuple(int(v) for v in PAPER))
    ImageDraw.Draw(im).text((6, 4), text, fill=(30, 30, 30), font=LABEL)
    return np.array(im)


def main():
    spec, out = json.load(open(sys.argv[1])), sys.argv[2]
    os.makedirs(out, exist_ok=True)
    for ch, s in spec.items():
        blocks = []
        for cut in s["cuts"]:
            rows = []
            for label, d in s["arms"]:
                p = os.path.join(d, f"Albo-{cut}.ttf")
                if os.path.exists(p):
                    rows.append(row(label, p, s["words"], ch))
            b = stack(rows, 2, rule=True)
            blocks.append(np.concatenate([header(f"{ch}  --  {cut}", b.shape[1]), b], 0))
        img = stack(blocks, 14)
        name = f"{ch}.png" if ch.islower() else f"{ch}_cap.png"
        Image.fromarray(img).save(os.path.join(out, name))
        print(name, img.shape)


if __name__ == "__main__":
    main()
