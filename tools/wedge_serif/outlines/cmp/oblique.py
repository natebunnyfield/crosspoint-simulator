"""Is this italic an ITALIC, or an oblique? (2026-09-14)

An oblique is the roman, slanted. A true italic is a different set of
skeletons, descended from a cursive hand, that happens also to slope. So the
test is mechanical: shear the family's OWN roman by its italic's angle and
see how much of the italic that accounts for, per letter, normalized to a
common height and registered horizontally. Intersection over union.

1.00 means the italic IS the sheared roman. Measured on real families:

    ITC Berkeley   0.306
    Coelacanth     0.431
    Albo, round 103  0.852     <- the reason this module exists

The per-letter column is the useful half: it names which letters a family
actually redrew. For the two real italics those are the arch letters (n m h),
the ascenders (l b h k) and the diagonals (k w z); for Albo they were only
the three that had been redrawn by hand.

    cd tools/wedge_serif && PYTHON_GIL=0 python3 -m outlines.cmp.oblique ROMAN.ttf ITALIC.ttf
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

PX = 400
CHARS = 'abdefghklmnopqrstuvwxyz'

def glyph_img(path, ch, shear=0.0, size=PX):
    ft = ImageFont.truetype(path, size); im = Image.new('L', (size * 3, size * 3), 0)
    ImageDraw.Draw(im).text((size, size * 2), ch, font=ft, fill=255, anchor='ls')
    a = np.asarray(im) > 128
    if shear:
        out = np.zeros_like(a)
        for y in range(a.shape[0]):
            dx = int(round((size * 2 - y) * shear))
            if dx == 0: out[y] = a[y]
            elif dx > 0: out[y, dx:] = a[y, :-dx]
            else: out[y, :dx] = a[y, -dx:]
        a = out
    ys, xs = np.where(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(ys) else None

def norm(img, H=300):
    if img is None: return None
    im = Image.fromarray((img * 255).astype(np.uint8))
    return np.asarray(im.resize((max(1, int(im.size[0] * H / im.size[1])), H), Image.LANCZOS)) > 127

def iou(a, b, reg=14):
    """Overlap, allowing a small horizontal registration so the score measures
    SHAPE and not where the shear happened to put the letter."""
    if a is None or b is None: return None
    W = max(a.shape[1], b.shape[1])
    pa = np.zeros((a.shape[0], W), bool); pa[:, :a.shape[1]] = a
    pb = np.zeros((b.shape[0], W), bool); pb[:, :b.shape[1]] = b
    best = 0.0
    for off in range(-reg, reg + 1):
        sb = np.roll(pb, off, axis=1); u = (pa | sb).sum()
        if u: best = max(best, (pa & sb).sum() / u)
    return best

def slant_of(italic_path):
    """The italic's angle: its `post` table where it has one, otherwise
    recovered from the l's own slope (Coelacanth carries no italicAngle)."""
    ang = -TTFont(italic_path, fontNumber=0)['post'].italicAngle
    if abs(ang) >= 0.5: return ang
    a = glyph_img(italic_path, 'l'); h = a.shape[0]
    top = np.where(a[int(h * 0.15)])[0].mean(); bot = np.where(a[int(h * 0.85)])[0].mean()
    return math.degrees(math.atan2(top - bot, h * 0.70))

def report(roman, italic, chars=CHARS):
    ang = slant_of(italic); sh = math.tan(math.radians(ang))
    scores = {}
    for ch in chars:
        s = iou(norm(glyph_img(roman, ch, shear=sh)), norm(glyph_img(italic, ch)))
        if s is not None: scores[ch] = s
    mean = sum(scores.values()) / len(scores)
    print(f"{os.path.basename(italic)}: slant {ang:.1f} deg, overlap with its own sheared roman {mean:.3f}")
    print("  (1.00 = a pure oblique; ITC Berkeley 0.306, Coelacanth 0.431)")
    print("  least like the sheared roman -- the letters this family actually redrew:")
    print("   " + '  '.join(f"{c} {v:.2f}" for c, v in sorted(scores.items(), key=lambda kv: kv[1])[:10]))
    return mean, scores

if __name__ == '__main__':
    report(sys.argv[1], sys.argv[2])
