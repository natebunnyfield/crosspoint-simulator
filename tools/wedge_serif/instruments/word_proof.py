#!/usr/bin/env python3
"""word_proof.py -- the owner's frequent and neglected words, set in Albo and in the reference
faces through the reader's pipeline, as lossless proof pictures
(docs/albo-word-images-2026-10-04.md).

Every row is one face at ONE x-height in pixels (Albo's at the named size; each reference scaled
to match, `word_measure.Face`), FreeType unhinted, the converter's 2-bit levels, HarfBuzz with kern
and liga, then magnified by an INTEGER factor with NEAREST so a pixel stays a pixel. Nothing is
resampled after the raster. Labels are ASCII (PIL's default fallback draws an en-dash as tofu).

    $VENV instruments/word_proof.py --albo DIR --corpus corpus.json --out OUTDIR --callouts default

It writes:
  top-R.png          the 30 commonest word images, Regular, 10 pt on the X3, 4x
  top-R-phone.png    the same at 10 pt on the phone (the 2x tier), 2x
  top-IBZ.png        the commonest words of each other cut in that cut (I, B, Z), 10 pt X3, 4x
  neglected-R.png    the most neglected words (word_corpus.py's index), Regular, 10 pt X3, 4x
  letter-<id>.png    one per called-out letter: the words it hurts, Albo's cut against references
  mechanism-R.png    n u / c / f drawn large with the measured join heights and advances marked
  mechanism-B.png    the same for the Bold
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import word_measure as WM  # noqa: E402

PAPER = np.array([250, 249, 246], float)
INK = np.array([20, 20, 20], float)
LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
SMALL = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
CUTL = {"Regular": "R", "Italic": "I", "Bold": "B", "BoldItalic": "Z"}


# The per-letter figures of docs/albo-word-images-2026-10-04.md section 8 (`--callouts default`):
# id -> the cut, a label, the words (his frequent carriers of the letter, word_corpus.py's
# letter_words), the references to set beside Albo, and words per line.
CALLOUTS = {
    'c-R': {"cut": "Regular", "letter": "c", "refs": ["Georgia", "Berkeley", "Albertus"], "per": 4, "words": ["which", "can", "because", "each", "back", "such", "once", "since"]},
    'u-R': {"cut": "Regular", "letter": "u", "refs": ["Georgia", "Charter", "Berkeley"], "per": 4, "words": ["you", "about", "out", "but", "would", "number", "under", "human"]},
    'f-R': {"cut": "Regular", "letter": "f", "refs": ["Georgia", "Charter", "Berkeley"], "per": 4, "words": ["of", "for", "from", "first", "form", "before", "after", "different"]},
    'k-R': {"cut": "Regular", "letter": "k", "refs": ["Georgia", "Berkeley", "Albertus"], "per": 4, "words": ["like", "kept", "work", "takes", "book", "back", "know", "keep"]},
    'e-I': {"cut": "Italic", "letter": "e", "refs": ["Georgia", "Charter", "Berkeley"], "per": 4, "words": ["the", "times", "values", "one", "page", "next", "answer", "these"]},
    'c-I': {"cut": "Italic", "letter": "c", "refs": ["Georgia", "Charter", "Berkeley"], "per": 4, "words": ["which", "chain", "because", "back", "country", "became", "each", "once"]},
    'h-I': {"cut": "Italic", "letter": "h", "refs": ["Georgia", "Charter", "Berkeley"], "per": 4, "words": ["the", "with", "Chapter", "right", "chain", "that", "what", "them"]},
    'f-I': {"cut": "Italic", "letter": "f", "refs": ["Georgia", "Charter", "Berkeley"], "per": 4, "words": ["of", "from", "for", "four", "first", "before", "life", "after"]},
    'vw-I': {"cut": "Italic", "letter": "v w", "refs": ["Georgia", "Charter", "Berkeley"], "per": 4, "words": ["values", "even", "every", "over", "with", "answer", "wrong", "two"]},
    'bold-B': {"cut": "Bold", "letter": "the Bold's widths (a o s g w dark; n h i l u light)", "refs": ["Georgia", "Charter", "Berkeley"], "per": 5, "words": ["and", "a", "in", "it", "is", "the", "English", "What", "answers", "call"]},
    'T-R': {"cut": "Regular", "letter": "T", "refs": ["Georgia", "Charter", "Albertus"], "per": 4, "words": ["The", "That", "Two", "This", "Then", "They", "Three", "To"]},
    'AI-R': {"cut": "Regular", "letter": "A, I", "refs": ["Georgia", "Charter", "Berkeley"], "per": 5, "words": ["A", "And", "After", "As", "At", "I", "It", "In", "If", "I'm"]},
    'worst-R': {"cut": "Regular", "letter": "the least even of his commonest words", "refs": ["Georgia", "Charter", "Berkeley"], "per": 5, "words": ["of", "can", "That", "case", "fact", "off", "far", "back", "each", "call"]},
    'worst-I': {"cut": "Italic", "letter": "the least even of his commonest words", "refs": ["Georgia", "Charter", "Berkeley"], "per": 5, "words": ["The", "It", "In", "She", "This", "keep", "be", "he", "people", "does"]},
}


def rgb(levels):
    t = (levels.astype(float) / 3.0)[..., None]
    return (PAPER * (1 - t) + INK * t).astype(np.uint8)


def line_img(face, text, mag):
    c, base, pad, g = face.raster(text, pad=int(face.ppem))
    cols = np.nonzero(c.any(0))[0]
    rows = np.nonzero(c.any(1))[0]
    if len(cols):
        c = c[:, max(cols[0] - 3, 0):cols[-1] + 4]
    return rgb(np.kron(c, np.ones((mag, mag), np.uint8)))


def label(text, h, w=260, sub=None):
    im = Image.new("RGB", (w, h), tuple(int(v) for v in PAPER))
    d = ImageDraw.Draw(im)
    y = max(2, h // 2 - (20 if sub else 12))
    d.text((10, y), text, fill=(30, 30, 30), font=LAB)
    if sub:
        d.text((10, y + 26), sub, fill=(110, 110, 110), font=SMALL)
    return np.array(im)


def hjoin(parts, gap=0):
    H = max(p.shape[0] for p in parts)
    out = []
    for p in parts:
        out.append(np.concatenate([p, np.full((H - p.shape[0], p.shape[1], 3), PAPER, np.uint8)], 0))
        if gap:
            out.append(np.full((H, gap, 3), PAPER, np.uint8))
    return np.concatenate(out, 1)


def vstack(rows, gap=6, rule=True):
    W = max(r.shape[1] for r in rows)
    out = []
    for i, r in enumerate(rows):
        out.append(np.concatenate([r, np.full((r.shape[0], W - r.shape[1], 3), PAPER, np.uint8)], 1))
        if i < len(rows) - 1:
            out.append(np.full((gap, W, 3), (215, 213, 208) if rule else PAPER, np.uint8))
    return np.concatenate(out, 0)


def header(text, W, h=40):
    im = Image.new("RGB", (W, h), (236, 234, 229))
    ImageDraw.Draw(im).text((10, 9), text, fill=(20, 20, 20), font=LAB)
    return np.array(im)


def face_rows(albo, cut, refs, size="x3-10"):
    """[(label, Face)] -- Albo's cut first, then each reference that has the cut."""
    xh = WM.SIZES[size]
    it = cut in ("Italic", "BoldItalic")
    out = [(f"Albo {CUTL[cut]}", WM.Face(os.path.join(albo, f"Albo-{cut}.ttf"), 0, xh, italic=it))]
    for r in refs:
        if cut in WM.REFS[r]:
            p, i = WM.REFS[r][cut]
            out.append((f"{r} {CUTL[cut]}", WM.Face(p, i, xh, italic=it)))
    return out


def text_block(faces, lines, mag, title):
    rows = []
    for lab, F in faces:
        imgs = [line_img(F, ln, mag) for ln in lines]
        body = vstack(imgs, gap=4 * mag, rule=False)
        rows.append(hjoin([label(lab, body.shape[0]), body]))
    img = vstack(rows)
    return np.concatenate([header(title, img.shape[1]), img], 0)


def save(img, path):
    Image.fromarray(img).save(path)
    print(os.path.basename(path), img.shape[1], "x", img.shape[0])


def wrap(words, per):
    return [" ".join(words[i:i + per]) for i in range(0, len(words), per)]


def mechanism_figure(albo, out, cut="Regular", refs=("Georgia", "Charter", "Berkeley", "Albertus"), XHPX=120):
    """The parts behind three callouts, drawn LARGE so the structure is visible (a context figure for
    the reader-size rows, not a reading-size proof): each face's n and u with the n's arch depth and
    the u's bowl rise ticked in red (word_parts.joins, scaled from Albo units), and its c and f with
    the advance drawn as two blue lines. Native unhinted coverage at a 120 px x-height, no resampling."""
    import word_parts as WP
    import freetype
    rows = []
    for lab, cut_, p, i in [("Albo", cut, os.path.join(albo, f"Albo-{cut}.ttf"), 0)] + \
            [(r, cut, WM.REFS[r][cut][0], WM.REFS[r][cut][1]) for r in refs if cut in WM.REFS[r]]:
        xh_em = WM.measure_xh(p, i)
        ppem = XHPX / xh_em
        f = freetype.Face(p, i); f.set_char_size(int(round(ppem * 64)), int(round(ppem * 64)), 72, 72)
        J = WP.joins(p, i, False)
        k = XHPX / WP.XH
        H = int(XHPX * 2.75); base = int(XHPX * 2.1)
        panels = []
        for text in ("nu", "c", "f"):
            W = int(XHPX * (3.9 if text == "nu" else 2.6))
            im = np.full((H, W, 3), PAPER, np.uint8)
            x = XHPX * 0.35
            advs = []
            for ch in text:
                gid = f.get_char_index(ch)
                a, left, top = WM._render(f, gid)
                adv = f.glyph.advance.x / 64.0
                if a.size:
                    t = (a.astype(float) / 255.0)[..., None]
                    gx = int(round(x)) + left; gy = base - top
                    y0, x0 = max(gy, 0), max(gx, 0)
                    sub = im[y0:gy + a.shape[0], x0:gx + a.shape[1]]
                    tt = t[y0 - gy:y0 - gy + sub.shape[0], x0 - gx:x0 - gx + sub.shape[1]]
                    sub[:] = (sub * (1 - tt) + INK * tt).astype(np.uint8)
                advs.append((x, x + adv))
                x += adv
            if text == "nu":
                yn = base - int(round((WP.XH - J.get("n_arch_depth", 0)) * k))
                yu = base - int(round(J.get("u_bowl_rise", 0) * k))
                (n0, n1), (u0, u1) = advs
                im[yn - 1:yn + 2, int(n0):int(n0 + XHPX * 0.45)] = (200, 40, 40)
                im[yu - 1:yu + 2, int(u1 - XHPX * 0.45):int(u1)] = (200, 40, 40)
            else:
                for xa in advs[0]:
                    im[int(base - XHPX * 1.6):base + int(XHPX * 0.3), int(round(xa)):int(round(xa)) + 2] = (60, 100, 200)
            im[base:base + 1, :] = (190, 190, 190); im[base - XHPX:base - XHPX + 1, :] = (215, 215, 215)
            panels.append(im)
        body = hjoin(panels, gap=6)
        lab_im = Image.new("RGB", (330, body.shape[0]), tuple(int(v) for v in PAPER))
        d = ImageDraw.Draw(lab_im)
        y = body.shape[0] // 2 - 40
        d.text((10, y), f"{lab} {CUTL[cut]}", fill=(30, 30, 30), font=LAB)
        d.text((10, y + 30), f"n arch {J.get('n_arch_depth', 0):.0f} below the x-line", fill=(150, 30, 30), font=SMALL)
        d.text((10, y + 52), f"u bowl {J.get('u_bowl_rise', 0):.0f} above the baseline", fill=(150, 30, 30), font=SMALL)
        d.text((10, y + 74), "(units at a 429 x-height)", fill=(110, 110, 110), font=SMALL)
        rows.append(hjoin([np.array(lab_im), body]))
    img = vstack(rows, gap=4, rule=False)
    img = np.concatenate([header("Drawn large: 120 px x-height, unhinted, no resampling. Red: where the n arch and the u bowl leave their stems. "
                                 "Blue: the advance of c and f", img.shape[1]), img], 0)
    save(img, os.path.join(out, f"mechanism-{CUTL[cut]}.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--albo", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--measure")
    ap.add_argument("--out", required=True)
    ap.add_argument("--callouts", help="default (the CALLOUTS table) or a JSON file: {id: {cut, letter, words, refs, per}}")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    C = json.load(open(a.corpus))
    refs = ["Georgia", "Charter", "Palatino", "Times", "Berkeley", "Albertus"]

    top = [r["word"] for r in C["top"]][:30]
    lines = wrap(top, 10)
    save(text_block(face_rows(a.albo, "Regular", refs), lines, 4,
                    "The 30 commonest word images in his books, Regular, 10 pt on the X3 (2-bit, unhinted), 4x NEAREST"),
         os.path.join(a.out, "top-R.png"))
    save(text_block(face_rows(a.albo, "Regular", refs, "ph-10"), lines, 2,
                    "The same 30 words at 10 pt on the phone (the 2x tier), 2x NEAREST"),
         os.path.join(a.out, "top-R-phone.png"))
    blocks = []
    for cut in ("Italic", "Bold", "BoldItalic"):
        words = [w for w, n in C["top_by_cut"][CUTL[cut]][:20]]
        blocks.append(text_block(face_rows(a.albo, cut, refs), wrap(words, 10), 4,
                                 f"The commonest words set in {cut} ({CUTL[cut]}) in his books, 10 pt X3, 4x NEAREST"))
    save(vstack(blocks, gap=16, rule=False), os.path.join(a.out, "top-IBZ.png"))
    neg = sorted(C["words"], key=lambda r: -r["score"])
    negw = [r["word"] for r in neg if len(r["word"]) >= 2][:30]
    save(text_block(face_rows(a.albo, "Regular", refs), wrap(negw, 10), 4,
                    "The most neglected word images (frequency x share of letters and pairs never worked on), Regular, 10 pt X3, 4x"),
         os.path.join(a.out, "neglected-R.png"))
    mechanism_figure(a.albo, a.out, "Regular")
    mechanism_figure(a.albo, a.out, "Bold", refs=("Georgia", "Charter", "Berkeley"))
    if a.callouts:
        table = CALLOUTS if a.callouts == "default" else json.load(open(a.callouts))
        for cid, spec in table.items():
            blocks = []
            for size, mag in (("x3-10", 4), ("ph-10", 2)):
                fr = face_rows(a.albo, spec["cut"], spec.get("refs", refs), size)
                title = (f"'{spec['letter']}' in {spec['cut']} ({CUTL[spec['cut']]}): "
                         + ("10 pt X3, 4x NEAREST" if size == "x3-10" else "10 pt phone (2x tier), 2x NEAREST"))
                blocks.append(text_block(fr, wrap(spec["words"], spec.get("per", 6)), mag, title))
            save(vstack(blocks, gap=16, rule=False), os.path.join(a.out, f"letter-{cid}.png"))


if __name__ == "__main__":
    main()
