#!/usr/bin/env python3
"""qmark_arms.py -- the ? neck ARMS (marks.py ALBO_Q_NECK = Q1 / Q2 / Q3) checked five ways.
docs/albo-question-mark-2026-10-01.md quotes every number from here; qmark_neck.py measures the
neck against the references.

  turn  SPEC ...        the live builder (run with the cut's env, build_env.sh): for each arm spec --
                        "" for today, "Q1", "Q2:B=0.5:DROP=0.3" for an arm with dial overrides
                        (ALBO_Q_NECK_<NAME>) -- the neck's tightest turn against its own half-width
                        below the curl's 3 o'clock, split into the junction (the 7 samples after it)
                        and the rest. r / (w/2) < 1 FOLDS the inner edge (today's Bold reads 0.81);
                        under ~1.4 it leaves a corner you can see at 2x.
  gap   LABEL=DIR ...   straight off each build's outlines (font units, as drawn): the white between
                        the dot's top and the stroke's lowest point, for ? ! and the inverted pair.
  dotsep LABEL=DIR ...  the reader's own renderer (fit_audit/legib.Renderer: unhinted, 2-bit) draws ?
                        at 8..18 pt on the X3 (150 dpi), 1x and 2x: WHITE rows (all level 0) / CLEAR
                        rows (all level <= 1) between the dot and the dark stroke above it, inside the
                        dot's columns. 0 clear rows (*) = the dot touches the stroke in dark ink.
  curl  A_DIR B_DIR     how far the ?'s outline ABOVE y 560 (the curl, above its 3 o'clock) moved
                        between two builds, unsheared for the italics: the arms keep the curl's samples
                        and widths exactly, so anything here is the linear cut re-faceting it.
  zoom OUT.png X0 Y0 X1 Y1 PX SPEC ...   the live builder (cut env): the window X0..X1, Y0..Y1 of the ?
                        (glyph units, as build.draw draws it) for each arm spec, PX px per unit, every
                        outline vertex dotted -- where a fold, a notch or a seam shows.
  proof OUT LABEL=DIR ...   the proof PNGs at native pixels: glyphs_<cut> (one ? per build and four
                        references at one 150 px x-height, as drawn), words_<cut> ("aqui? ¿Usted vive
                        aqui?" and "Why? What is it?" at 10 pt on the X3, 5x NEAREST), words2x_<cut>
                        (the phone's 2x tier, 3x NEAREST) and summary.png (italic + roman, 5x).

    source build_env.sh
    env "${ALBO_BLD_ENV[@]}" PYTHON_GIL=0 python3 instruments/qmark_arms.py turn "" Q1 Q2 Q3
    $VENV/bin/python instruments/qmark_arms.py gap today=$BASE Q1=$Q1 Q2=$Q2 Q3=$Q3
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
CUTS = ("Regular", "Italic", "Bold", "BoldItalic")


def _arms(specs):
    return [s.split("=", 1) for s in specs]


def cmd_turn(specs):
    sys.path.insert(0, WS)
    from outlines import build, geom
    from outlines.glyphs import marks as M
    real = M.stroke
    for spec in specs:
        a, *kv = spec.split(":")
        for p in kv:
            k, v = p.split("="); os.environ["ALBO_Q_NECK_" + k] = v
        M.Q_NECK = a.strip().upper()
        rec = []
        def spy(center, width, *aa, **kw):
            rec.append((list(center), width, kw)); return real(center, width, *aa, **kw)
        M.stroke = spy
        try:
            build.draw("?")
        finally:
            M.stroke = real
            for p in kv: os.environ.pop("ALBO_Q_NECK_" + p.split("=")[0], None)
        center, wf, kw = max(rec, key=lambda r: len(r[0]))
        pts = center if kw.get("raw") else geom.resample(center)
        n = len(pts) - 1
        i3 = max(range(n + 1), key=lambda i: pts[i][0])
        def rad(i):
            a_, b_, c_ = pts[i - 1], pts[i], pts[i + 1]
            cr = abs((b_[0] - a_[0]) * (c_[1] - a_[1]) - (b_[1] - a_[1]) * (c_[0] - a_[0]))
            return float("inf") if cr < 1e-9 else math.dist(a_, b_) * math.dist(b_, c_) * math.dist(c_, a_) / (2 * cr)
        def ratio(i): return rad(i) / max(1e-6, wf(i / n) / 2)
        zj = range(i3, min(n, i3 + 7)); zr = range(i3 + 7, n)
        j = min(zj, key=ratio); r_ = min(zr, key=ratio) if len(zr) else j
        print(f"{spec or 'today':28s} junction r {rad(j):6.1f} vs w/2 {wf(j / n) / 2:5.1f} = {ratio(j):.2f}   "
              f"rest r {rad(r_):6.1f} vs w/2 {wf(r_ / n) / 2:5.1f} = {ratio(r_):.2f}")
    M.Q_NECK = ""


def cmd_zoom(out, x0, y0, x1, y1, sc, specs):
    sys.path.insert(0, WS)
    from outlines import build
    from outlines.glyphs import marks as M
    from PIL import Image, ImageDraw, ImageFont
    x0, y0, x1, y1, sc = map(float, (x0, y0, x1, y1, sc))
    F = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    cells = []
    for spec in specs:
        a, *kv = spec.split(":")
        for p in kv:
            k, v = p.split("="); os.environ["ALBO_Q_NECK_" + k] = v
        M.Q_NECK = a.strip().upper()
        try:
            g = build.draw("?")
        finally:
            for p in kv: os.environ.pop("ALBO_Q_NECK_" + p.split("=")[0], None)
        W, H = int((x1 - x0) * sc), int((y1 - y0) * sc)
        im = Image.new("RGB", (W, H + 24), (250, 250, 248)); d = ImageDraw.Draw(im)
        tr = lambda x, y: ((x - x0) * sc, 24 + (y1 - y) * sc)
        polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
        for P in polys:
            d.polygon([tr(x, y) for x, y in P.exterior.coords], fill=(30, 30, 30))
            for h in P.interiors: d.polygon([tr(x, y) for x, y in h.coords], fill=(250, 250, 248))
        for P in polys:
            for ring in [P.exterior] + list(P.interiors):
                for x, y in ring.coords:
                    px, py = tr(x, y); d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(230, 60, 60))
        d.text((4, 4), spec or "today", fill=(0, 0, 0), font=F)
        cells.append(im)
    M.Q_NECK = ""
    sheet = Image.new("RGB", (sum(c.width for c in cells) + 10 * (len(cells) - 1), cells[0].height), (255, 255, 255))
    x = 0
    for c in cells: sheet.paste(c, (x, 0)); x += c.width + 10
    sheet.save(out); print(out, sheet.size)


def _contours(font, g, slant=0.0):
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    gs = font.getGlyphSet(); p = DecomposingRecordingPen(gs); gs[g].draw(p)
    k = math.tan(math.radians(slant)); out, cur = [], []
    for op, args in p.value:
        if op == "moveTo": cur = [args[0]]
        elif op in ("lineTo", "qCurveTo", "curveTo"): cur.extend(args)
        elif op in ("closePath", "endPath"):
            if cur: out.append([(x - y * k, y) for x, y in cur])
            cur = []
    return out


def cmd_gap(arms):
    from fontTools.ttLib import TTFont
    for lab, d in _arms(arms):
        for cut in CUTS:
            f = TTFont(os.path.join(d, f"Albo-{cut}.ttf")); row = []
            for g in ("question", "exclam"):
                cs = sorted(_contours(f, g), key=lambda c: min(y for _, y in c))
                dt, lo = max(y for _, y in cs[0]), min(y for _, y in cs[1])
                row.append(f"{g:8s} {lo - dt:5.1f} (dot top {dt:5.1f}, stroke low {lo:5.1f})")
            for g in ("questiondown", "exclamdown"):
                cs = sorted(_contours(f, g), key=lambda c: max(y for _, y in c))
                row.append(f"{g:12s} {min(y for _, y in cs[-1]) - max(y for _, y in cs[0]):5.1f}")
            print(f"{lab:6s} {cut:10s} " + "  ".join(row))


def cmd_dotsep(arms):
    import numpy as np
    from scipy import ndimage as ndi
    sys.path.insert(0, os.path.join(WS, "fit_audit"))
    from legib import Renderer
    PTS = [8, 10, 12, 14, 16, 18]
    for cut in CUTS:
        print(f"== {cut}   white/clear rows between dot and stroke: {PTS} pt at 1x, then at 2x")
        for lab, d in _arms(arms):
            cells = []
            for tier in (1, 2):
                for pt in PTS:
                    ppem = 150 / 72 * pt * tier
                    R = Renderer(os.path.join(d, f"Albo-{cut}.ttf"), 0, ppem)
                    c = np.zeros((int(ppem * 2), int(ppem * 2)), np.uint8); R.line("?", c, 4, int(ppem * 1.5))
                    dark = c >= 2
                    lab_, n = ndi.label(dark, structure=np.ones((3, 3)))
                    if n < 2: cells.append(" 0/0*"); continue
                    bots = ndi.maximum(np.arange(c.shape[0])[:, None] * np.ones_like(c), lab_, range(1, n + 1))
                    dot = int(np.argmax(bots)) + 1
                    ys, xs = np.nonzero(lab_ == dot)
                    x0, x1, top = max(0, xs.min() - 1), xs.max() + 2, ys.min()
                    rows = np.nonzero((dark[:top, x0:x1] & (lab_[:top, x0:x1] != dot)).any(1))[0]
                    if not len(rows): cells.append("  -/-"); continue
                    band = c[rows.max() + 1:top, x0:x1]
                    white = int((band.max(1) == 0).sum()) if band.size else 0
                    clear = int((band.max(1) <= 1).sum()) if band.size else 0
                    cells.append(f"{white:2d}/{clear}{'*' if clear == 0 else ' '}")
            print(f"   {lab:6s} " + " ".join(cells))


def cmd_curl(a_dir, b_dir, ymin=560.0):
    from fontTools.ttLib import TTFont
    from shapely.geometry import LineString, Point
    for cut in CUTS:
        sl = 13.0 if "Italic" in cut else 0.0
        A = _contours(TTFont(os.path.join(a_dir, f"Albo-{cut}.ttf")), "question", sl)
        B = _contours(TTFont(os.path.join(b_dir, f"Albo-{cut}.ttf")), "question", sl)
        la = [LineString(c + c[:1]) for c in A]; lb = [LineString(c + c[:1]) for c in B]
        pa = [p for c in A for p in c if p[1] > ymin]; pb = [p for c in B for p in c if p[1] > ymin]
        d1 = max((min(l.distance(Point(p)) for l in lb) for p in pa), default=0)
        d2 = max((min(l.distance(Point(p)) for l in la) for p in pb), default=0)
        print(f"{cut:10s} the curl above y {ymin:.0f} moved at most {max(d1, d2):.2f} units ({len(pa)} / {len(pb)} points)")


def cmd_proof(out, arms):
    import numpy as np, freetype
    from PIL import Image, ImageDraw, ImageFont
    sys.path.insert(0, os.path.join(WS, "fit_audit")); sys.path.insert(0, HERE)
    from legib import Renderer
    import poor_proof as P
    os.makedirs(out, exist_ok=True)
    arms = _arms(arms)
    SUP = "/System/Library/Fonts/Supplemental/"; PAL = "/System/Library/Fonts/Palatino.ttc"; RF = os.path.join(WS, "refs") + "/"
    PG = os.path.expanduser("~/Library/Fonts/"); DL = os.path.expanduser("~/Downloads/")
    REFS = {
        "Regular": [("Albertus", DL + "Albertus Medium Regular.ttf", 0), ("Georgia", SUP + "Georgia.ttf", 0), ("Palatino", PAL, 0), ("Times", SUP + "Times New Roman.ttf", 0)],
        "Italic": [("Flanker", RF + "flanker-griffo-italic.otf", 0), ("Coelacanth", RF + "coelacanth-italic.otf", 0), ("Pagella It", RF + "texgyrepagella-italic.otf", 0), ("Georgia It", SUP + "Georgia Italic.ttf", 0)],
        "Bold": [("Georgia B", SUP + "Georgia Bold.ttf", 0), ("Palatino B", PAL, 2), ("Times B", SUP + "Times New Roman Bold.ttf", 0)],
        "BoldItalic": [("Flanker B", RF + "flanker-griffo-bold-italic.otf", 0), ("Georgia BI", SUP + "Georgia Bold Italic.ttf", 0), ("Pagella BI", PG + "texgyrepagella-bolditalic.otf", 0)],
    }
    PAPER = tuple(int(v) for v in P.PAPER); INK = (20, 20, 20); XH = 150
    LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)

    def cell(path, idx, label):
        f = freetype.Face(path, idx)
        f.set_char_size(f.units_per_EM * 64, 0, 72, 72)
        f.load_char("x", freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING)
        f.set_char_size(int(round(XH * f.units_per_EM / f.glyph.outline.get_bbox().yMax * 64)), 0, 72, 72)
        f.load_char("?", freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        b = f.glyph.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] if b.rows else np.zeros((1, 1), np.uint8)
        W, H = 300, int(XH * 2.25) + 40; base = int(XH * 2.0) + 4
        cl = np.full((H, W, 3), PAPER, np.uint8); cl[base, :] = (175, 175, 175); cl[base - XH, :] = (210, 210, 210)
        x0, y0 = 40 + f.glyph.bitmap_left, base - f.glyph.bitmap_top; h, w = a.shape
        ys, xs = slice(max(0, y0), min(H, y0 + h)), slice(max(0, x0), min(W, x0 + w))
        sub = a[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0].astype(float)[..., None] / 255.0
        cl[ys, xs] = (cl[ys, xs] * (1 - sub) + np.array(INK) * sub).astype(np.uint8)
        im = Image.fromarray(cl); ImageDraw.Draw(im).text((8, 6), label, fill=(0, 0, 0), font=LAB)
        return np.array(im)

    def hcat(cs, gap=6):
        H = max(c.shape[0] for c in cs); parts = []
        for c in cs:
            parts += [np.concatenate([c, np.full((H - c.shape[0], c.shape[1], 3), PAPER, np.uint8)], 0), np.full((H, gap, 3), 255, np.uint8)]
        return np.concatenate(parts[:-1], 1)

    def vcat(blocks):
        W = max(b.shape[1] for b in blocks)
        padded = [np.concatenate([b, np.full((b.shape[0], W - b.shape[1], 3), PAPER, np.uint8)], 1) for b in blocks]
        sep = np.full((24, W, 3), 255, np.uint8)
        out_ = [padded[0]]
        for p in padded[1:]: out_ += [sep, p]
        return np.concatenate(out_, 0)

    def rows(cut, lines, pt, mag, tier=1):
        ppem = 150 / 72 * pt * tier; rs = []
        for lab, d in arms:
            R = Renderer(os.path.join(d, f"Albo-{cut}.ttf"), 0, ppem); segs = []
            for line in lines:
                c = np.zeros((int(ppem * 1.75), int(ppem * 30)), np.uint8); R.line(line, c, 4, int(ppem * 1.28))
                c = c[:, :np.nonzero(c.any(0))[0][-1] + 4]
                segs += [c, np.zeros((c.shape[0], int(ppem * 1.2)), np.uint8)]
            img = P.rgb(np.kron(np.concatenate(segs[:-1], 1), np.ones((mag, mag), np.uint8)))
            li = Image.new("RGB", (110, img.shape[0]), PAPER); ImageDraw.Draw(li).text((10, img.shape[0] // 2 - 12), lab, fill=(30, 30, 30), font=LAB)
            rs.append(np.concatenate([np.array(li), img], 1))
        W = max(r.shape[1] for r in rs)
        return np.concatenate([np.concatenate([r, np.full((r.shape[0], W - r.shape[1], 3), PAPER, np.uint8)], 1) for r in rs], 0)

    L1, L2 = "aquí? ¿Usted vive aquí?", "Why? What is it?"
    for cut in CUTS:
        cs = [cell(os.path.join(d, f"Albo-{cut}.ttf"), 0, f"Albo {lab}") for lab, d in arms]
        cs += [cell(p, i, lab) for lab, p, i in REFS[cut] if os.path.exists(p)]
        Image.fromarray(hcat(cs)).save(os.path.join(out, f"glyphs_{cut}.png"))
        Image.fromarray(vcat([rows(cut, [L1], 10, 5), rows(cut, [L2], 10, 5)])).save(os.path.join(out, f"words_{cut}.png"))
        Image.fromarray(rows(cut, ["aquí?", "Why?", "it?"], 10, 3, tier=2)).save(os.path.join(out, f"words2x_{cut}.png"))
    Image.fromarray(vcat([rows("Italic", [L1], 10, 5), rows("Regular", [L2], 10, 5)])).save(os.path.join(out, "summary.png"))
    for fn in sorted(os.listdir(out)):
        if fn.endswith(".png"): print(os.path.join(out, fn))


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "turn": cmd_turn(args)
    elif cmd == "gap": cmd_gap(args)
    elif cmd == "dotsep": cmd_dotsep(args)
    elif cmd == "curl": cmd_curl(*args)
    elif cmd == "zoom": cmd_zoom(args[0], *args[1:6], args[6:])
    elif cmd == "proof": cmd_proof(args[0], args[1:])
    else: raise SystemExit(__doc__)
