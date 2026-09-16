"""A letter's COUNTERS, measured identically on a scan and on a build.

Round 133. The owner, twice: *"match the counterspace for a to the griffo
scans"*, then *"match a and e to scans better. take multiple passes."* This is
the instrument those passes run on, and the point of it is that the SAME code
reads a 54 px photograph of 1501 metal and a 400 px render of our outline:
binarize (Otsu on an upscale), flood the background in from the border, and
every white region that survives inside the ink is a counter.

What it reports per counter, all of it scale-free so a scan and a render
compare directly:

    area / ink        how much of the letter's black the hole takes back
    w / h             its proportion -- SHEARED, as both the scan and the
                      build are, so it is not the design-space number
    fill              area / (w x h): an ellipse is 0.79, a triangle 0.50.
                      This is the number that says "teardrop" or "oval", and
                      it is the one a bbox cannot see.
    widest at         where the widest row sits, 0 at the floor
    floor             its lowest point above the letter's own bottom, x the
                      letter's height
    profile           left and right edge at ten heights, x the counter's
                      width -- the silhouette, which is what a shape is

A letter with two counters (the e) reports both, largest first.

    python3 cmp_aldine_counter.py scan a            # the scan crop
    python3 cmp_aldine_counter.py font <ttf> a e    # a build
"""
import os, sys
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

HEIGHTS = (0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95)


def _otsu(a):
    hist, _ = np.histogram(a, bins=256, range=(0, 256)); p = hist / hist.sum()
    w = np.cumsum(p); m = np.cumsum(p * np.arange(256)); mt = m[-1]
    var = (mt * w - m) ** 2 / np.maximum(w * (1 - w), 1e-9)
    return int(np.argmax(var))


def _holes(ink):
    """Every enclosed white region, largest first, as lists of (y, x)."""
    H, W = ink.shape
    bg = np.zeros_like(ink); q = deque()
    for x in range(W):
        for y in (0, H - 1):
            if not ink[y, x] and not bg[y, x]: bg[y, x] = True; q.append((y, x))
    for y in range(H):
        for x in (0, W - 1):
            if not ink[y, x] and not bg[y, x]: bg[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and not ink[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True; q.append((ny, nx))
    hole = (~ink) & (~bg); seen = np.zeros(hole.shape, bool); out = []
    for y in range(H):
        for x in range(W):
            if hole[y, x] and not seen[y, x]:
                q = deque([(y, x)]); seen[y, x] = True; pts = []
                while q:
                    cy, cx = q.popleft(); pts.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and hole[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; q.append((ny, nx))
                out.append(pts)
    return sorted(out, key=len, reverse=True)


def ink_wh(ink):
    """The letter's own ink proportion, sheared as drawn -- the counter can
    only be right inside a letter of the right shape, and the a's scan is
    0.75 where both digital revivals are 0.94."""
    iy, ix = np.where(ink)
    return (ix.max() - ix.min() + 1) / (iy.max() - iy.min() + 1)


def metrics(ink, min_frac=0.01):
    """[dict per counter], largest first. Counters under `min_frac` of the
    ink are dropped -- at 54 px a photograph leaves specks, and a speck that
    is counted as a counter is how a shape measurement goes wrong quietly."""
    iy, ix = np.where(ink)
    if not len(iy): return []
    inkn = ink.sum(); inkh = iy.max() - iy.min() + 1; inkbot = iy.max()
    out = []
    for pts in _holes(ink):
        if len(pts) < min_frac * inkn: continue
        ys = [p[0] for p in pts]; xs = [p[1] for p in pts]
        ch = max(ys) - min(ys) + 1; cw = max(xs) - min(xs) + 1
        prof = []
        for f in HEIGHTS:
            row = int(round(max(ys) - f * (ch - 1)))
            r = [x for (y, x) in pts if y == row]
            prof.append(((min(r) - min(xs)) / cw, (max(r) - min(xs)) / cw) if r else (0.0, 0.0))
        widest = max(range(len(HEIGHTS)), key=lambda i: prof[i][1] - prof[i][0])
        out.append(dict(area_ink=len(pts) / inkn, wh=cw / ch, fill=len(pts) / (cw * ch),
                        widest=HEIGHTS[widest], floor=(inkbot - max(ys)) / inkh,
                        h_ink=ch / inkh, ink_wh=ink_wh(ink), profile=prof))
    return out


def from_image(path, box=None, k=8):
    im = Image.open(os.path.expanduser(path)).convert('L')
    if box: im = im.crop(box)
    if k != 1: im = im.resize((im.width * k, im.height * k), Image.LANCZOS)
    a = np.asarray(im).astype(float)
    return metrics(a < _otsu(a))


def from_font(ttf, ch, px=400):
    f = ImageFont.truetype(ttf, px)
    im = Image.new('L', (px * 3, px * 3), 255)
    ImageDraw.Draw(im).text((px, int(px * 1.8)), ch, font=f, fill=0, anchor='ls')
    return metrics(np.asarray(im) < 128)


# The scan each letter is matched to. The `a`'s two sources agree to within
# 0.03 on every profile row; the macro is the cleaner photograph and is the
# one quoted, with the owner's crop as the check.
SCAN = {
    'a': ('~/Downloads/griffo-macro.png', (264, 44, 306, 105), 'macro "ad"'),
    'e': ('~/Downloads/griffo-macro.png', (592, 342, 634, 406), 'macro "naues"'),
    'd': ('~/Downloads/griffo-macro.png', (75, 15, 140, 120), 'macro "udos"'),
    'o': ('~/Downloads/griffo-macro.png', (142, 57, 190, 118), 'macro "udos"'),
}


def show(label, ms):
    if not ms: print('%-22s no counter' % label); return
    for i, m in enumerate(ms):
        print('%-22s %s area/ink %.2f  w/h %.2f  fill %.2f  widest %.2f  floor %.2f  h/ink %.2f  letter w/h %.2f' % (
            label if i == 0 else '', ['largest', 'second', 'third'][min(i, 2)],
            m['area_ink'], m['wh'], m['fill'], m['widest'], m['floor'], m['h_ink'], m['ink_wh']))
    p = ms[0]['profile']
    print('   profile  ' + '  '.join('%.2f:%.2f-%.2f' % (h, l, r) for h, (l, r) in zip(HEIGHTS, p)))


def main():
    if sys.argv[1] == 'scan':
        for ch in sys.argv[2:]:
            path, box, note = SCAN[ch]
            show('%s  scan %s' % (ch, note), from_image(path, box))
    else:
        ttf = sys.argv[2]
        for ch in sys.argv[3:]:
            show('%s  %s' % (ch, os.path.basename(ttf)), from_font(ttf, ch))


if __name__ == '__main__':
    main()
