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

    python3 cmp_aldine_shape.py <Albo-Italic.ttf> a [b c ...] [--out DIR] [--ref scan|poetica|flanker|pagella]

Font-against-font comparisons scale both faces to one X-HEIGHT and align on
the BASELINE (so an ascender that is longer stays longer and counts against
the match); a scan crop has no known baseline, so it is compared on the ink
box instead.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import aldine_autofit as AF

FLANKER = os.path.join(HERE, 'refs', 'flanker-griffo-italic.otf')
POETICA = os.path.join(HERE, 'refs', 'poetica-std-regular.otf')
PAGELLA = os.path.join(HERE, 'refs', 'texgyrepagella-italic.otf')
# Owner 2026-09-16: "poetica is my preferred fallback" -- where no scan crop
# exists, the shape to match is Poetica's. Flanker stays as the weight/colour
# comparator (it is the face that matches the 1501 page's darkness).
REF_FONTS = {'poetica': POETICA, 'flanker': FLANKER, 'pagella': PAGELLA}
H = 360          # every mask is scaled so its ink is this tall
PAD = 24


def _xh_units(path):
    from fontTools.ttLib import TTFont
    from fontTools.pens.boundsPen import BoundsPen
    f = TTFont(path); gs = f.getGlyphSet(); n = f.getBestCmap()[ord('x')]
    bp = BoundsPen(gs); gs[n].draw(bp)
    return bp.bounds[3] / f['head'].unitsPerEm


def font_mask(path, ch, px=600):
    f = ImageFont.truetype(path, px)
    im = Image.new('L', (px * 3, px * 3), 255)
    ImageDraw.Draw(im).text((px * 0.5, px * 0.6), ch, font=f, fill=0)
    a = np.asarray(im) < 128
    return a


XH_PX = 240      # in x-height mode every font is scaled so its x-height is this


def font_mask_xh(path, ch):
    """Ink mask with the font scaled so its x-height is XH_PX and the
    BASELINE at a known row -- so two fonts compare on the letter's own
    proportion (an ascender that is longer stays longer) instead of on the
    bounding box. Returns (mask, baseline_row)."""
    px = int(round(XH_PX / _xh_units(path)))
    f = ImageFont.truetype(path, px)
    W = px * 4; Hh = px * 4; base = int(px * 2.4)
    im = Image.new('L', (W, Hh), 255)
    ImageDraw.Draw(im).text((px, base), ch, font=f, fill=0, anchor='ls')
    return np.asarray(im) < 128, base


def compare_xh(ref, rb, cand, cb):
    """IoU of two baseline-aligned, x-height-scaled masks, aligned on their
    left ink edge; canvas cropped to the union's bbox for the overlay."""
    def shift(a, b):
        ys, xs = np.where(a)
        return a, xs.min(), b
    ra, rl, _ = shift(ref, rb); ca, cl, _ = shift(cand, cb)
    # translate candidate so its left edge and baseline meet the reference's
    dx = rl - cl; dy = rb - cb
    c = np.zeros_like(ra)
    ys, xs = np.where(ca)
    ys2 = ys + dy; xs2 = xs + dx
    ok = (ys2 >= 0) & (ys2 < c.shape[0]) & (xs2 >= 0) & (xs2 < c.shape[1])
    c[ys2[ok], xs2[ok]] = True
    inter = (ra & c).sum(); union = (ra | c).sum()
    iou = inter / union if union else 0.0
    ys, xs = np.where(ra | c)
    y0, y1, x0, x1 = ys.min() - PAD, ys.max() + PAD, xs.min() - PAD, xs.max() + PAD
    r2, c2 = ra[y0:y1, x0:x1], c[y0:y1, x0:x1]
    img = np.full(r2.shape, 255, np.uint8)
    img[r2 & ~c2] = 200; img[c2 & ~r2] = 110; img[r2 & c2] = 0
    return iou, Image.fromarray(img), r2, c2


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
        ref = norm(rm); cand = norm(font_mask(albo_ttf, ch))
        iou, ov, rwh, cwh = compare(ref, cand)
    else:
        rmask, rb = font_mask_xh(REF_FONTS[ref_kind], ch)
        cmask, cb = font_mask_xh(albo_ttf, ch)
        label = ref_kind
        iou, ov, ref, cand = compare_xh(rmask, rb, cmask, cb)
        def _wh(a):
            ys, xs = np.where(a); return (xs.max() - xs.min() + 1) / max(1, ys.max() - ys.min() + 1)
        rwh, cwh = _wh(ref), _wh(cand)
    # side-by-side: ref | albo | overlay
    cells = [Image.fromarray(((~ref) * 255).astype(np.uint8)),
             Image.fromarray(((~cand) * 255).astype(np.uint8)), ov]
    names = [label, 'Albo', 'overlay  IoU %.3f' % iou]
    W = sum(c.width for c in cells) + PAD * (len(cells) + 1)
    Hc = max(c.height for c in cells)
    out = Image.new('L', (W, Hc + PAD * 2 + 30), 255); d = ImageDraw.Draw(out)
    lab = ImageFont.load_default(16); x = PAD
    for c, n in zip(cells, names):
        out.paste(c, (x, PAD)); d.text((x, Hc + PAD + 6), n, font=lab, fill=110)
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
        kinds = ['scan', 'poetica', 'flanker'] if ref_kind == 'auto' else [ref_kind]
        for k in kinds:
            r = sheet(ch, ttf, k)
            if r is None: continue
            iou, im, rwh, cwh = r
            p = os.path.join(out, '%s_%s.png' % (ch, k)); im.save(p)
            print('%s  %-8s IoU %.3f   w/h ref %.2f albo %.2f   %s' % (ch, k, iou, rwh, cwh, p))


if __name__ == '__main__':
    main()
