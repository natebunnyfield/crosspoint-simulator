"""Does an Aldine italic letter have the SHAPE of its reference?

Round 132. The owner: "examine a then each subsequent letter, take multiple
passes at each until the shape and strokes and serifs match what they should
based on a referenced vector or bitmap." This is the instrument for each pass:
the letter and its reference are both reduced to an ink mask, scaled to the
same ink HEIGHT, aligned on their left and bottom ink edges, and compared as
intersection over union. It also writes an overlay -- the reference in grey,
the candidate's ink over it -- which is what the eye judges; the number only
says whether a pass moved toward the reference or away from it.

The reference is the SCAN CROP where one exists (aldine_autofit.SOURCES; the
1501 metal is the target) and Flanker Griffo Italic otherwise -- the closest
digital face to the scans, supplied by the owner 2026-09-15.

    python3 cmp_aldine_shape.py <Albo-Italic.ttf> a [b c ...] [--out DIR] [--ref flanker|scan]
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import aldine_autofit as AF

FLANKER = os.path.join(HERE, 'refs', 'flanker-griffo-italic.otf')
H = 360          # every mask is scaled so its ink is this tall
PAD = 24


def font_mask(path, ch, px=600):
    f = ImageFont.truetype(path, px)
    im = Image.new('L', (px * 3, px * 3), 255)
    ImageDraw.Draw(im).text((px * 0.5, px * 0.6), ch, font=f, fill=0)
    a = np.asarray(im) < 128
    return a


def scan_mask(ch):
    if ch not in AF.SOURCES: return None
    path, box, xh, note = AF.SOURCES[ch]
    im = Image.open(os.path.expanduser(path)).convert('L').crop(box)
    # scale up before thresholding so the edge is a curve, not a staircase
    k = max(1.0, 8.0 * 54 / xh)
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    a = np.asarray(im).astype(float)
    # Otsu
    hist, _ = np.histogram(a, bins=256, range=(0, 256))
    p = hist / hist.sum(); w = np.cumsum(p); m = np.cumsum(p * np.arange(256))
    mt = m[-1]; var = (mt * w - m) ** 2 / np.maximum(w * (1 - w), 1e-9)
    t = int(np.argmax(var))
    return a < t


def crop_bbox(a):
    ys, xs = np.where(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def norm(a):
    """Crop to ink, scale to height H (keeping aspect), as a float image."""
    a = crop_bbox(a)
    im = Image.fromarray((a * 255).astype(np.uint8))
    w = max(1, int(round(im.width * H / im.height)))
    im = im.resize((w, H), Image.LANCZOS)
    return np.asarray(im) > 127


def compare(ref, cand):
    """IoU on masks aligned at their left/bottom ink edges, padded to a
    common canvas. Returns (iou, overlay image, ref w/h, cand w/h)."""
    W = max(ref.shape[1], cand.shape[1])
    def pad(a):
        out = np.zeros((H, W), bool); out[:, :a.shape[1]] = a; return out
    r, c = pad(ref), pad(cand)
    inter = (r & c).sum(); union = (r | c).sum()
    iou = inter / union if union else 0.0
    # overlay: reference light grey, candidate-only dark grey, both black
    img = np.full((H, W), 255, np.uint8)
    img[r & ~c] = 200
    img[c & ~r] = 110
    img[r & c] = 0
    return iou, Image.fromarray(img), ref.shape[1] / H, cand.shape[1] / H


def sheet(ch, albo_ttf, ref_kind):
    if ref_kind == 'scan':
        rm = scan_mask(ch)
        if rm is None: return None
        label = 'scan ' + AF.SOURCES[ch][3]
    else:
        rm = font_mask(FLANKER, ch); label = 'Flanker Griffo'
    ref = norm(rm); cand = norm(font_mask(albo_ttf, ch))
    iou, ov, rwh, cwh = compare(ref, cand)
    # side-by-side: ref | albo | overlay
    cells = [Image.fromarray(((~ref) * 255).astype(np.uint8)),
             Image.fromarray(((~cand) * 255).astype(np.uint8)), ov]
    names = [label, 'Albo', 'overlay  IoU %.3f' % iou]
    W = sum(c.width for c in cells) + PAD * (len(cells) + 1)
    out = Image.new('L', (W, H + PAD * 2 + 30), 255); d = ImageDraw.Draw(out)
    lab = ImageFont.load_default(16); x = PAD
    for c, n in zip(cells, names):
        out.paste(c, (x, PAD)); d.text((x, H + PAD + 6), n, font=lab, fill=110)
        x += c.width + PAD
    d.text((W - 200, 4), '%s   w/h ref %.2f  albo %.2f' % (ch, rwh, cwh), font=lab, fill=60)
    return iou, out, rwh, cwh


def main():
    args = []; skip = False
    for i, a in enumerate(sys.argv[1:]):
        if skip: skip = False; continue
        if a.startswith('--'): skip = True; continue
        args.append(a)
    ttf, letters = args[0], args[1:]
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(HERE, 'shape')
    ref_kind = sys.argv[sys.argv.index('--ref') + 1] if '--ref' in sys.argv else 'auto'
    os.makedirs(out, exist_ok=True)
    for ch in letters:
        kinds = ['scan', 'flanker'] if ref_kind == 'auto' else [ref_kind]
        for k in kinds:
            r = sheet(ch, ttf, k)
            if r is None: continue
            iou, im, rwh, cwh = r
            p = os.path.join(out, '%s_%s.png' % (ch, k)); im.save(p)
            print('%s  %-8s IoU %.3f   w/h ref %.2f albo %.2f   %s' % (ch, k, iou, rwh, cwh, p))


if __name__ == '__main__':
    main()
