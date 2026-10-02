"""x_italic.py -- the italic x against the reference italics: one picture, one table.

    $S/venv/bin/python instruments/x_italic.py --fonts DIR --sheet OUT.png [--measure]

Every reference x at ONE x-height (260 px), baseline and x-line drawn, beside
Albo's Italic (I) and Bold Italic (Z) from DIR. `--measure` prints, per face,
measured on the outline UNSHEARED by the face's MEASURED slant (refs_registry for
the five registered italics, `post.italicAngle` for the rest, which declare it):

    w/xh     ink width over the face's own x-height (the bbox top of its x)
    thick    the heavier diagonal's horizontal run at .50, x the face's o stem
    thin     the lighter diagonal's run at .50 (or the nearest row where the
             two runs separate), same unit
    cross    the height where the two diagonals cross, x xh (the row whose
             single run is narrowest between .30 and .70)
    lean     each diagonal's centerline slope in degrees from vertical,
             thick then thin, between .20 and .80 (unsheared)
    ends     ink at the four corners: the leftmost x at .03 and .97 and the
             rightmost x at .03 and .97, each as a fraction of the ink width,
             which is where a hook or a ball shows up

Written 2026-10-01 for the owner's "give me options for italic x"
(docs/albo-italic-x-2026-10-01.md).
"""
import argparse, math, os, sys
import numpy as np
import freetype
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REFS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "refs")
SUP = "/System/Library/Fonts/Supplemental"
# the five registered italics carry refs_registry's MEASURED slant (two of them
# declare 0 in post); the system italics declare theirs and None reads it
FACES = [
    (os.path.join(REFS, "flanker-griffo-italic.otf"), 0, "Flanker Griffo", 11.7),
    (os.path.join(REFS, "poetica-std-regular.otf"), 0, "Poetica", 9.2),
    (os.path.join(REFS, "texgyrepagella-italic.otf"), 0, "Pagella", 11.7),
    (os.path.join(REFS, "coelacanth-italic.otf"), 0, "Coelacanth", 14.5),
    (os.path.join(REFS, "cancelleresca-bastarda-beta12.otf"), 0, "Cancelleresca", 10.3),
    ("/System/Library/Fonts/Palatino.ttc", 1, "Palatino", None),
    (os.path.join(SUP, "Hoefler Text.ttc"), 2, "Hoefler Text", None),
    (os.path.join(SUP, "Iowan Old Style.ttc"), 2, "Iowan", None),
    (os.path.join(SUP, "Baskerville.ttc"), 2, "Baskerville", None),
    (os.path.join(SUP, "Georgia Italic.ttf"), 0, "Georgia", None),
    (os.path.join(SUP, "Charter.ttc"), 1, "Charter", None),
    ("/System/Library/Fonts/Times.ttc", 2, "Times", None),
]


def outline_bitmap(path, idx, ch, xh_px, slant_deg=None, unshear=False):
    """Render ch so the face's x is xh_px tall; optionally unshear about the baseline."""
    f = freetype.Face(path, idx)
    f.set_pixel_sizes(0, 400)
    f.load_char("x", freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_BITMAP)
    xh = f.glyph.metrics.horiBearingY / 64.0
    size = int(round(400 * xh_px / xh))
    f.set_pixel_sizes(0, size)
    if unshear:
        ang = slant_deg
        if ang is None:
            try:
                from fontTools.ttLib import TTFont
                tt = TTFont(path, fontNumber=idx, lazy=True)
                ang = -float(tt["post"].italicAngle)
            except Exception:
                ang = 0.0
        t = math.tan(math.radians(ang))
        m = freetype.Matrix(int(1 * 0x10000), int(-t * 0x10000), 0, int(1 * 0x10000))
        f.set_transform(m, freetype.Vector(0, 0))
    f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_BITMAP)
    g = f.glyph; b = g.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] if b.rows else np.zeros((1, 1), np.uint8)
    return a, g.bitmap_left, g.bitmap_top, g.advance.x / 64.0


def face_list(fonts_dir):
    out = []
    for nm, lab in (("Albo-Italic.ttf", "Albo I (today)"), ("Albo-BoldItalic.ttf", "Albo Z (today)")):
        p = os.path.join(fonts_dir, nm)
        if os.path.exists(p):
            out.append((p, 0, lab, None))
    return out + [f for f in FACES if os.path.exists(f[0])]


def sheet(faces, out_path, ch="x", cols=7, unshear=False):
    F = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
    W, H, XH, BASE = 300, 380, 200, 300
    cells = []
    for path, idx, lab, sl in faces:
        a, left, top, adv = outline_bitmap(path, idx, ch, XH, sl, unshear)
        im = Image.new("L", (W, H), 250); d = ImageDraw.Draw(im)
        d.line([(0, BASE), (W, BASE)], fill=200); d.line([(0, BASE - XH), (W, BASE - XH)], fill=200)
        ox = (W - a.shape[1]) // 2 - left if a.shape[1] < W else 0
        im.paste(Image.fromarray(255 - a), (ox + left, BASE - top), Image.fromarray(a))
        d.text((6, 6), lab, fill=0, font=F)
        cells.append(im)
    rows = (len(cells) + cols - 1) // cols
    out = Image.new("L", (W * cols, H * rows), 250)
    for i, c in enumerate(cells):
        out.paste(c, ((i % cols) * W, (i // cols) * H))
    out.save(out_path)
    return out.size


def runs(row):
    r = []; on = False
    for i, v in enumerate(row):
        if v and not on: s = i; on = True
        elif not v and on: r.append((s, i - 1)); on = False
    if on: r.append((s, len(row) - 1))
    return r


def measure(path, idx, lab, sl):
    XH = 400
    a, left, top, adv = outline_bitmap(path, idx, "x", XH, sl, unshear=True)
    ink = a > 127
    o, ol, ot, _ = outline_bitmap(path, idx, "o", XH, sl, unshear=True)
    # o stem: widest horizontal run at mid-height
    orow = (o > 127)[ot - XH // 2] if 0 <= ot - XH // 2 < o.shape[0] else None
    ostem = max((e - s + 1) for s, e in runs(orow)) if orow is not None and runs(orow) else 1
    H, Wd = ink.shape
    def row_at(fr):
        y = top - int(round(fr * XH))
        return ink[y] if 0 <= y < H else np.zeros(Wd, bool)
    cols_any = np.where(ink.any(axis=0))[0]
    x0, x1 = cols_any[0], cols_any[-1]; w = x1 - x0 + 1
    # crossing: narrowest single-run row between .30 and .70
    best = None
    for k in range(30, 71):
        rr = runs(row_at(k / 100))
        if len(rr) == 1:
            wd = rr[0][1] - rr[0][0] + 1
            if best is None or wd < best[1]:
                best = (k / 100, wd)
    cross = best[0] if best else float("nan")
    # thick / thin: two runs nearest .50 that are separate
    th = tn = float("nan")
    for dk in range(0, 25):
        for k in (50 + dk, 50 - dk):
            rr = runs(row_at(k / 100))
            if len(rr) >= 2:
                ws = sorted((e - s + 1) for s, e in rr)[-2:]
                tn, th = ws[0] / ostem, ws[1] / ostem
                break
        if th == th:
            break
    # lean: track the centers of the two diagonals from .20 to .80
    pts = {0: [], 1: []}
    for k in range(20, 81, 2):
        rr = runs(row_at(k / 100))
        if len(rr) == 2:
            for j in (0, 1):
                pts[j].append((k / 100 * XH, (rr[j][0] + rr[j][1]) / 2))
    leans = []
    for j in (0, 1):
        if len(pts[j]) >= 4:
            yy, xx = zip(*pts[j]); p = np.polyfit(yy, xx, 1)
            leans.append(math.degrees(math.atan(p[0])))
        else:
            leans.append(float("nan"))
    def ends(fr):
        rr = runs(row_at(fr))
        if not rr: return (float("nan"), float("nan"))
        return ((rr[0][0] - x0) / w, (rr[-1][1] - x0) / w)
    e03, e97 = ends(0.03), ends(0.97)
    return dict(label=lab, wxh=w / XH, thick=th, thin=tn, cross=cross,
                lean=leans, e03=e03, e97=e97, ostem=ostem / XH)


def pen_profile(ttf, ch, slant, px=520, band=15):
    """cmp_g_strokes' pen signature (thickness binned by run direction) for any
    glyph: the method doc's ONE RULE test. A letter on the face's own pen bins
    like the face's o."""
    import cmp_g_strokes as G
    mask, base, _ = G.raster(ttf, ch, slant, px)
    d = G.dist(mask)
    pts = G.ridge(mask, d)
    dirs = G.directions(pts)
    bins = {}
    for (y, x, v), a_ in zip(pts, dirs):
        if a_ is None: continue
        bins.setdefault(int(a_ // band) * band, []).append(2 * v)
    return {b: float(np.median(v)) for b, v in sorted(bins.items()) if len(v) >= 4}


def pen_report(fonts_dir):
    subj = [(os.path.join(fonts_dir, "Albo-Italic.ttf"), 13.0, "Albo I"),
            (os.path.join(fonts_dir, "Albo-BoldItalic.ttf"), 13.0, "Albo Z"),
            (os.path.join(REFS, "flanker-griffo-italic.otf"), 11.7, "Flanker"),
            (os.path.join(REFS, "poetica-std-regular.otf"), 9.2, "Poetica"),
            (os.path.join(REFS, "texgyrepagella-italic.otf"), 11.7, "Pagella"),
            (os.path.join(REFS, "coelacanth-italic.otf"), 14.5, "Coelacanth"),
            (os.path.join(SUP, "Georgia Italic.ttf"), 12.0, "Georgia"),
            (os.path.join(SUP, "Times New Roman Italic.ttf"), 15.0, "Times NR")]
    print("pen signature: median stroke width (px at 520 px x-height) by run direction, x against the face's own o")
    for ttf, sl, lab in subj:
        if not os.path.exists(ttf): continue
        for ch in ("o", "x"):
            p = pen_profile(ttf, ch, sl)
            thin = min(p, key=p.get); thick = max(p, key=p.get)
            print(f"  {lab:10s} {ch}  " + " ".join(f"{b:>3d}:{p[b]:3.0f}" for b in p)
                  + f"   thin@{thin:3d} thick@{thick:3d}  {p[thick]/p[thin]:.2f}:1")


def hairlines(path, idx, sl, XH=400):
    """Perpendicular stroke widths, as fractions of the x-height, read with a
    Euclidean distance transform at each run's centre (twice the distance to
    white there): the x's rising hairline at .25-.38 and .60-.72 (clear of the
    crossing and the terminals), the v's and y's rising stroke at .35-.65,
    the w's two rising strokes, and the o's thinnest (rays from its counter's
    centre). Returns a dict."""
    from scipy.ndimage import distance_transform_edt as edt
    out = {}
    def load(ch):
        a, left, top, adv = outline_bitmap(path, idx, ch, XH, sl, unshear=True)
        ink = a > 127
        return ink, top, edt(ink)
    def runs_at(ink, top, fr):
        y = top - int(round(fr * XH))
        return (runs(ink[y]) if 0 <= y < ink.shape[0] else []), y
    def widths_of(ch, frs, pick):
        ink, top, d = load(ch); ws = []
        for fr in frs:
            rr, y = runs_at(ink, top, fr)
            for r in pick(rr):
                xc = (r[0] + r[1]) // 2
                ws.append(2 * d[y, max(r[0], min(r[1], xc))] - 1)
        return float(np.median(ws)) / XH if ws else float("nan")
    lo = [k / 100 for k in range(25, 39)]; hi = [k / 100 for k in range(60, 73)]
    xa = widths_of("x", lo, lambda rr: rr[:1] if len(rr) == 2 else [])
    xb = widths_of("x", hi, lambda rr: rr[-1:] if len(rr) == 2 else [])
    out["x"] = (xa + xb) / 2
    out["x_thick"] = (widths_of("x", lo, lambda rr: rr[-1:] if len(rr) == 2 else []) +
                      widths_of("x", hi, lambda rr: rr[:1] if len(rr) == 2 else [])) / 2
    mid = [k / 100 for k in range(35, 66)]
    out["v"] = widths_of("v", mid, lambda rr: rr[-1:] if len(rr) == 2 else [])
    out["y"] = widths_of("y", mid, lambda rr: rr[-1:] if len(rr) == 2 else [])
    out["w"] = widths_of("w", mid, lambda rr: [rr[1], rr[3]] if len(rr) == 4 else [])
    ink, top, d = load("o")
    ys, xs = np.nonzero(ink)
    cy, cx = top - XH // 2, (xs.min() + xs.max()) / 2
    th = []
    for ang in np.linspace(0, 2 * math.pi, 180, endpoint=False):
        dx, dy = math.cos(ang), -math.sin(ang); inside = False; n = 0
        for s in range(0, XH):
            x = int(round(cx + dx * s)); y = int(round(cy + dy * s))
            if not (0 <= y < ink.shape[0] and 0 <= x < ink.shape[1]): break
            if ink[y, x]:
                inside = True; n = max(n, d[y, x])
            elif inside:
                break
        if n: th.append(2 * n - 1)
    out["o_thin"] = min(th) / XH; out["o_thick"] = max(th) / XH
    return out


def hair_report(fonts_dir):
    print(f"{'face':18s}  {'x thin':>6s} {'v':>6s} {'w':>6s} {'y':>6s} {'o thin':>6s}  x/v   x/o   (x thick, o thick)   -- units at xh 429")
    for f in face_list(fonts_dir):
        h = hairlines(f[0], f[1], f[3])
        k = 429
        print(f"{f[2]:18s}  {h['x']*k:6.1f} {h['v']*k:6.1f} {h['w']*k:6.1f} {h['y']*k:6.1f} {h['o_thin']*k:6.1f}  "
              f"{h['x']/h['v']:.2f}  {h['x']/h['o_thin']:.2f}   ({h['x_thick']*k:.0f}, {h['o_thick']*k:.0f})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--sheet")
    ap.add_argument("--unshear", action="store_true", help="draw the sheet unsheared as well")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--pen", action="store_true", help="the pen signature, x against o")
    ap.add_argument("--hair", action="store_true", help="hairline widths: x, v, w, y against the o")
    a = ap.parse_args()
    faces = face_list(a.fonts)
    if a.sheet:
        print(a.sheet, sheet(faces, a.sheet, unshear=a.unshear))
    if a.pen:
        pen_report(a.fonts)
    if a.hair:
        hair_report(a.fonts)
    if a.measure:
        print(f"{'face':18s} {'w/xh':>5s} {'thick':>5s} {'thin':>5s} {'t/t':>4s} {'cross':>5s}  {'lean thick/thin':>15s}  ends .03 L/R   .97 L/R   (o stem/xh)")
        for f in faces:
            m = measure(*f)
            l = m["lean"]
            print(f"{m['label']:18s} {m['wxh']:5.2f} {m['thick']:5.2f} {m['thin']:5.2f} {m['thin']/m['thick']:4.2f} {m['cross']:5.2f}  {l[0]:6.1f} {l[1]:6.1f}     "
                  f"{m['e03'][0]:.2f} {m['e03'][1]:.2f}   {m['e97'][0]:.2f} {m['e97'][1]:.2f}   ({m['ostem']:.3f})")


