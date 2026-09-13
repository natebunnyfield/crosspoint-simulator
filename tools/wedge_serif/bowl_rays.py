"""Stroke thickness of a bowl by angle: ray-cast from the bowl's center at
1000 px, the outermost ink run on each ray. 0 = 3 o'clock, + = up.
python3 bowl_rays.py <font> <chars>"""
import sys, math
from PIL import Image, ImageDraw, ImageFont
import numpy as np
def rays(font, ch, S=1000, angles=range(-80, 81, 20)):
    f = ImageFont.truetype(font, S); im = Image.new('L', (S*2, S*2), 255); d = ImageDraw.Draw(im); d.text((S//4, S//4), ch, font=f, fill=0)
    a = np.array(im) < 128; ys, xs = np.nonzero(a); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    if ch in 'DPR': cx = x0 + (x1-x0)*0.55; cy = (y0+y1)/2 if ch == 'D' else y0 + (y1-y0)*0.28
    elif ch == 'B': cx = x0 + (x1-x0)*0.55; cy = y0 + (y1-y0)*0.74
    else: cx = (x0+x1)/2; cy = (y0+y1)/2
    out = []
    for deg in angles:
        th = math.radians(deg); dx, dy = math.cos(th), -math.sin(th); r = 0; inside = False; runs = []; start = None
        while r < S:
            x = int(cx+dx*r); y = int(cy+dy*r)
            if not (0 <= x < a.shape[1] and 0 <= y < a.shape[0]): break
            v = a[y, x]
            if v and not inside: inside = True; start = r
            if not v and inside: inside = False; runs.append((start, r))
            r += 1
        out.append((deg, (runs[-1][1]-runs[-1][0]) if runs else 0))
    return out
if __name__ == '__main__':
    for ch in sys.argv[2]:
        r = rays(sys.argv[1], ch); print(ch, [t for _, t in r], 'max at', max(r, key=lambda x: x[1])[0])
