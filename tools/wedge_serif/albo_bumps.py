"""Every bump and glitch the instruments can find, circled in thin red on a
hi-res sheet, one per style, for the owner to confirm by marking up.

Owner 2026-09-18: *"make a hires image with thin red circles around all of the
bumps and glitches you can identify in each character. I will confirm they
need fixes by highlighting them in another color. I will also highlight things
that need fixing that you did not find and circle."*

WHAT IS CIRCLED. The outline is flattened and walked; at each vertex the turn
angle and its change against the neighbours are taken. A vertex is a BUMP when
the edge's direction jolts by more than KINK degrees between one segment and
the next inside a run that is otherwise gentle (a corner -- a turn over
CORNER -- is a designed feature and is not marked), or when the curvature
changes sign twice within a few vertices by more than WAVE degrees (a
zig-zag). Adjacent hits are merged into one circle. Each circle is numbered;
the index file lists style, glyph, number, position in design units and what
was measured, so a confirmation ("roman n 3") maps to a place in the outline.

    PYTHON_GIL=0 python3 albo_bumps.py --roman R.ttf --italic I.ttf --out DIR
"""
import argparse, json, math, os, string
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

GLYPHS = list(string.ascii_uppercase) + list(string.ascii_lowercase) + list("0123456789") + list(".,;:!?'\"-&@()")
KINK, CORNER, WAVE, MERGE = 9.0, 38.0, 7.0, 48.0     # degrees, degrees, degrees, units (MERGE: one circle per 48 units of a wavy edge)


def contours(ttf, ch, f=None):
    f = f or TTFont(ttf); cmap = f.getBestCmap(); gs = f.getGlyphSet()
    if ord(ch) not in cmap: return []
    r = RecordingPen(); gs[cmap[ord(ch)]].draw(r)
    polys, cur = [], []
    def q(p0, p1, p2, n=10):
        return [((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0], (1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]) for t in [i/n for i in range(1, n+1)]]
    for op, a in r.value:
        if op == 'moveTo': cur = [a[0]]
        elif op == 'lineTo': cur.append(a[0])
        elif op == 'qCurveTo':
            pts = list(a)
            if pts[-1] is None: pts = pts[:-1] + [cur[0]]
            for i in range(len(pts) - 1):
                mid = ((pts[i][0]+pts[i+1][0])/2, (pts[i][1]+pts[i+1][1])/2) if i < len(pts)-2 else pts[-1]
                cur += q(cur[-1], pts[i], mid)
        elif op in ('closePath', 'endPath'):
            if len(cur) > 3: polys.append(cur)
            cur = []
    return polys


def bumps(polys):
    """[(x, y, kind, value)] in design units.

    The first cut marked every vertex whose turn jolted by 9 degrees -- which
    is every facet of every bowl at 11-unit spacing (1,623 circles on the
    roman), not a bump. A bump is a DEVIATION FROM THE LOCAL TREND: each
    vertex is compared with a Gaussian average of its neighbours over +-WIN
    vertices; where the outline is a smooth arc that average lies a fraction
    of a unit inside it (a facet is not a bump), where the edge waves it lies
    off by units. Local maxima of that deviation over DEV units are circled;
    corners (turn over CORNER) and their two neighbours are excluded, because
    smoothing across a designed corner invents a deviation. Kinks over KINK
    degrees that are not corners are circled too."""
    hits = []
    WIN, DEV, KINKD = 6, 1.2, 20.0
    # The moving-average residual of the second cut was wrong on tight curves:
    # the average of an arc's neighbours lies INSIDE the arc by its sagitta,
    # six units at the o's ends, so every bowl lit up (1,504 circles). The
    # trend is a CIRCLE fitted to the +-WIN neighbours (Kasa's algebraic fit)
    # and the residual is the vertex's distance from that circle -- zero on a
    # true arc of any radius, units on a wave.
    def circle_resid(Q, i):
        idx = [(i + k) % len(Q) for k in range(-WIN, WIN + 1) if k != 0]
        X = Q[idx]; x, y = X[:, 0], X[:, 1]
        M = np.column_stack([x, y, np.ones_like(x)]); b = -(x * x + y * y)
        try: (D, E, F), *_ = np.linalg.lstsq(M, b, rcond=None)
        except Exception: return 0.0
        cx, cy = -D / 2, -E / 2; r2 = cx * cx + cy * cy - F
        if r2 <= 0: return 0.0
        r = math.sqrt(r2)
        if r > 4000: # a straight run: distance from the fitted line instead
            u = X[-1] - X[0]; L = math.hypot(*u) or 1.0; v = Q[i] - X[0]
            return abs(u[0] * v[1] - u[1] * v[0]) / L
        return abs(math.hypot(Q[i][0] - cx, Q[i][1] - cy) - r)
    for P in polys:
        A = np.array(P, float); n = len(A)
        if n < 2 * WIN + 4: continue
        d = np.roll(A, -1, axis=0) - A; seg = np.hypot(d[:, 0], d[:, 1])
        ang = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
        turn = np.roll((np.roll(ang, -1) - ang + 180) % 360 - 180, 1)
        corner = np.abs(turn) > CORNER
        near_corner = corner.copy()
        for k in range(1, WIN + 1): near_corner |= np.roll(corner, k) | np.roll(corner, -k)
        dev = np.array([0.0 if near_corner[i] else circle_resid(A, i) for i in range(n)])
        for i in range(n):
            if near_corner[i] or seg[i] < 0.5 or seg[i - 1] < 0.5: continue
            if dev[i] > DEV and dev[i] >= dev[i - 1] and dev[i] >= dev[(i + 1) % n]:
                hits.append((float(A[i, 0]), float(A[i, 1]), 'wave', float(dev[i])))
            elif abs(turn[i]) > KINKD and not corner[i]:
                hits.append((float(A[i, 0]), float(A[i, 1]), 'kink', float(abs(turn[i]))))
    hits.sort(key=lambda h: -h[3]); out = []
    for h in hits:
        if all(math.hypot(h[0]-o[0], h[1]-o[1]) > MERGE for o in out): out.append(h)
    return out


def sheet(ttf, out_png, out_index, label, per_row=8, cap_px=300):
    f = TTFont(ttf); upm = f['head'].unitsPerEm
    cap = 674.0; scale = cap_px / cap
    fnt = ImageFont.truetype(ttf, int(round(upm * scale)))
    cell_w, cell_h = int(cap_px * 1.75), int(cap_px * 2.05)
    rows = (len(GLYPHS) + per_row - 1) // per_row
    W, H = cell_w * per_row + 40, cell_h * rows + 80
    im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    try: lab = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    except Exception: lab = ImageFont.load_default()
    d.text((20, 18), f"{label} -- every bump the instrument finds, circled and numbered; mark the ones that need a fix in another colour, and circle what I missed", fill=(60, 60, 60), font=lab)
    index = []; k = 0
    for gi, ch in enumerate(GLYPHS):
        cx0 = 20 + (gi % per_row) * cell_w; cy0 = 60 + (gi // per_row) * cell_h
        base = cy0 + int(cap_px * 1.45); ox = cx0 + int(cap_px * 0.35)
        d.text((cx0 + 8, cy0 + 4), ch, fill=(150, 150, 150), font=lab)
        d.text((ox, base), ch, fill=(0, 0, 0), font=fnt, anchor="ls")
        polys = contours(ttf, ch, f)
        if not polys: continue
        # glyph origin at (ox, base) in the image; design units scale by `scale` (y up)
        lsb = f['hmtx'][f.getBestCmap()[ord(ch)]][1]
        xs = [x for P in polys for x, y in P]; xmin = min(xs)
        for (x, y, kind, val) in bumps(polys):
            k += 1
            px = ox + (x - xmin + lsb) * scale; py = base - y * scale
            r = 13
            d.ellipse([px - r, py - r, px + r, py + r], outline=(220, 30, 30), width=2)
            d.text((px + r + 2, py - r - 4), str(k), fill=(220, 30, 30), font=lab)
            index.append(dict(style=label, glyph=ch, n=k, x=round(x), y=round(y), kind=kind, degrees=round(val, 1)))
    im.save(out_png)
    with open(out_index, "w") as fh: json.dump(index, fh, indent=1)
    return k, im.size


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--roman", required=True); ap.add_argument("--italic", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    for sty, p in (("roman", a.roman), ("italic", a.italic)):
        n, size = sheet(p, os.path.join(a.out, f"bumps-{sty}.png"), os.path.join(a.out, f"bumps-{sty}.json"), f"Albo {sty}")
        print(f"{sty}: {n} circles, {size}")


if __name__ == "__main__":
    main()
