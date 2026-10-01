#!/usr/bin/env python3
"""qmark_neck.py -- the QUESTION MARK'S NECK, read one way off Albo and off the references.

Owner 2026-10-01: *"subagent to improve question mark middle to bottom stroke."* The stroke is
the one from the middle of the curl -- the bowl's 3 o'clock, where the hook is furthest right --
down to just above the dot. Not the crown, not the dot. docs/albo-question-mark-2026-10-01.md.

Every glyph goes through fig27_trace.Face: rendered UNHINTED, UNSHEARED by its MEASURED slant (the
`l`'s axis -- refs_registry.py records why never `post.italicAngle`), scaled so the face's x lands
on Albo's 429 units, 2 px per unit. Albo builds go through the SAME function, so an arm and a
reference are read by one instrument (docs/albo-method.md section 4).

How the neck is found, so a number can be traced back to pixels:
  1. the HOOK is the largest separate part, the DOT the lowest of the others;
  2. the hook's centreline is the GEODESIC level sets from its lowest pixel, inside the ink:
     every 1-unit band of geodesic distance is one cross-section of the stroke; its centroid is
     the centreline point and twice the largest distance-to-edge inside it is the stroke's width
     there (the inscribed circle, so it is the PERPENDICULAR width whatever the stroke's angle);
  3. the NECK is that centreline from the hook's furthest-right point (3 o'clock) to the foot.
     u = 0 is 3 o'clock, u = 1 the foot.

Printed per face (units are Albo's at xh 429; `/n` = over the SAME face's n stem):
  n          the face's n stem
  w@u        the neck's width at u = 0, .25, .5, .75, .9, over n
  min, max   the neck's thinnest and thickest, over n, and the u where each falls
  a@u        the centreline's angle from HORIZONTAL at u (90 = vertical, < 90 leans like '/')
  foot       the horizontal ink run 40, 80 and 20 units above the neck's lowest point, over n
             (fixed heights: at a bold's n, "1.0 n up" is already inside the neck's bend)
  face       the end face's slope, degrees (0 = level; + = rising to the right, the pen cut)
  gap        neck bottom to dot top, units, and over the dot's diameter
  dx         the foot's centre minus the dot's centre, units (+ = the foot right of the dot)
  dot        the dot's diameter over n, and over the foot's 0.5 n run
  ink        the neck's ink area (3 o'clock to foot) over n^2 -- how much black it puts down

    PYTHON_GIL=0 $VENV/bin/python instruments/qmark_neck.py --cut Italic [--albo LABEL=DIR ...]
        [--sheet out.png] [--json out.json] [--refs-only|--albo-only]
"""
import argparse, json, math, os, sys
import numpy as np
from scipy import ndimage as ndi
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fig27_trace import Face, SUP, PAL, RF, XH_ALBO, PX  # noqa: E402
from poor_trace import nstem  # noqa: E402

PG = os.path.expanduser("~/Library/Fonts/")
# The panels: poor_trace.PANEL's six per cut, plus Pagella (the TeX Gyre Palatino, the italic's
# proportion fallback) and, in the italic, Coelacanth (refs_registry.py). Poetica is in poor_trace's
# italic panel and kept.
PANEL = {
    "Regular": [("Georgia", SUP + "Georgia.ttf", 0), ("Charter", SUP + "Charter.ttc", 0),
                ("Times", SUP + "Times New Roman.ttf", 0), ("Baskerville", SUP + "Baskerville.ttc", 0),
                ("Hoefler", SUP + "Hoefler Text.ttc", 0), ("Palatino", PAL, 0),
                ("Pagella", PG + "texgyrepagella-regular.otf", 0)],
    "Bold": [("Georgia B", SUP + "Georgia Bold.ttf", 0), ("Charter B", SUP + "Charter.ttc", 3),
             ("Times B", SUP + "Times New Roman Bold.ttf", 0), ("Baskerville B", SUP + "Baskerville.ttc", 1),
             ("Hoefler B", SUP + "Hoefler Text.ttc", 1), ("Palatino B", PAL, 2),
             ("Pagella B", PG + "texgyrepagella-bold.otf", 0)],
    "Italic": [("Georgia It", SUP + "Georgia Italic.ttf", 0), ("Charter It", SUP + "Charter.ttc", 1),
               ("Palatino It", PAL, 1), ("Flanker", RF + "flanker-griffo-italic.otf", 0),
               ("Poetica", RF + "poetica-std-regular.otf", 0), ("Pagella It", RF + "texgyrepagella-italic.otf", 0),
               ("Coelacanth", RF + "coelacanth-italic.otf", 0), ("Times It", SUP + "Times New Roman Italic.ttf", 0)],
    "BoldItalic": [("Georgia BI", SUP + "Georgia Bold Italic.ttf", 0), ("Charter BI", SUP + "Charter.ttc", 2),
                   ("Palatino BI", PAL, 3), ("Flanker B", RF + "flanker-griffo-bold-italic.otf", 0),
                   ("Times BI", SUP + "Times New Roman Bold Italic.ttf", 0), ("Hoefler BI", SUP + "Hoefler Text.ttc", 3),
                   ("Pagella BI", PG + "texgyrepagella-bolditalic.otf", 0)],
}
# The LINEAGE panel (--lineage): the faces Albo's own guide names -- Albertus for the stroke
# (docs/fjord-glyph-guide.md section 00), Berkeley Oldstyle for what a warm text face does, Van den
# Keere and Dante for proportion -- plus Edgar and Golden Cockerel from the reader's font shelf.
DL = os.path.expanduser("~/Downloads/"); LF = os.path.expanduser("~/src/crosspoint-reader/lib/EpdFont/local_fonts/")
BK = DL + "ITC Berkeley Oldstyle/ITC Berkeley Oldstyle "
LINEAGE = {
    "Regular": [("Albertus", DL + "Albertus Medium Regular.ttf", 0), ("Berkeley", BK + "Medium/ITC Berkeley Oldstyle Medium.otf", 0),
                ("VdKeere", LF + "VandenKeere-Regular.otf", 0), ("Dante", LF + "DanteMT-Regular.ttf", 0),
                ("Edgar", LF + "Edgar-Regular.ttf", 0), ("GCockerel", LF + "GoldenCockerel-Roman.ttf", 0)],
    "Bold": [("Berkeley B", BK + "Bold/ITC Berkeley Oldstyle Bold.otf", 0), ("VdKeere B", LF + "VandenKeere-Bold.otf", 0),
             ("Dante B", LF + "DanteMT-Bold.ttf", 0), ("Edgar B", LF + "Edgar-Bold.ttf", 0)],
    "Italic": [("Berkeley It", BK + "Medium Italic/ITC Berkeley Oldstyle Medium Italic.otf", 0),
               ("VdKeere It", LF + "VandenKeere-Italic.otf", 0), ("Dante It", LF + "DanteMT-Italic.ttf", 0),
               ("Edgar It", LF + "Edgar-Italic.ttf", 0), ("GCockerel It", LF + "GoldenCockerel-Italic.ttf", 0)],
    "BoldItalic": [("Berkeley BI", BK + "Bold Italic/ITC Berkeley Oldstyle Bold Italic.otf", 0),
                   ("Dante BI", LF + "DanteMT-BoldItalic.ttf", 0), ("Edgar BI", LF + "Edgar-BoldItalic.ttf", 0)],
}
US = (0.0, 0.25, 0.5, 0.75, 0.9)
FOOT_H = (20.0, 40.0, 80.0)     # the foot's rows, units above the neck's lowest ink (fixed, so a bold's n cannot carry them into the bend)


def face(path, idx, italic):
    ch = "I" if (italic and path.endswith("Hoefler Text.ttc")) else "l"
    return Face(path, idx, slant=None if italic else 0.0, slant_ch=ch)


def split(a):
    """(hook mask, dot mask or None): the hook is the largest part, the dot the lowest other."""
    lab, n = ndi.label(a, structure=np.ones((3, 3)))
    if n == 0: raise ValueError("no ink")
    sz = ndi.sum(a, lab, range(1, n + 1))
    comps = [(i + 1, s) for i, s in enumerate(sz) if s > 0.002 * a.sum()]
    hook = max(comps, key=lambda t: t[1])[0]
    others = [c for c, _ in comps if c != hook]
    dot = max(others, key=lambda c: np.nonzero(lab == c)[0].max()) if others else None
    return lab == hook, (lab == dot) if dot is not None else None


def geodesic(mask, seeds):
    """Geodesic distance (px, 8-connected, diagonal steps sqrt 2) inside `mask` from `seeds`."""
    H, W = mask.shape
    ys, xs = np.nonzero(mask)
    idx = -np.ones(mask.shape, np.int64); idx[ys, xs] = np.arange(len(ys))
    r, c, w = [], [], []
    for dy, dx, cost in ((0, 1, 1.0), (1, 0, 1.0), (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2))):
        y2, x2 = ys + dy, xs + dx
        ok = (y2 < H) & (x2 >= 0) & (x2 < W)
        ok2 = ok.copy(); ok2[ok] = mask[y2[ok], x2[ok]]
        a_, b_ = idx[ys[ok2], xs[ok2]], idx[y2[ok2], x2[ok2]]
        r += [a_, b_]; c += [b_, a_]; w += [np.full(len(a_), cost)] * 2
    G = coo_matrix((np.concatenate(w), (np.concatenate(r), np.concatenate(c))), shape=(len(ys), len(ys))).tocsr()
    si = idx[seeds[0], seeds[1]]
    d = dijkstra(G, directed=False, indices=si, min_only=True)
    out = np.full(mask.shape, np.inf); out[ys, xs] = d
    return out


def centreline(hook, x0, yt):
    """[(cx, cy, w)] in units from the hook's lowest pixel round to its other end, by 1-unit
    bands of geodesic distance."""
    H, W = hook.shape
    dt = ndi.distance_transform_edt(np.pad(hook, 1))[1:-1, 1:-1]
    rows = np.nonzero(hook.any(1))[0]; rb = rows.max()
    cs = np.nonzero(hook[rb])[0]
    g = geodesic(hook, (np.full(len(cs), rb), cs))
    ys, xs = np.nonzero(hook)
    band = np.floor(g[ys, xs] / PX).astype(int)
    order = np.argsort(band)
    ys, xs, band = ys[order], xs[order], band[order]
    cuts = np.nonzero(np.diff(band))[0] + 1
    out = []
    for yy, xx in zip(np.split(ys, cuts), np.split(xs, cuts)):
        cx = x0 + (xx.mean() + 0.5) / PX; cy = yt - (yy.mean() + 0.5) / PX
        out.append((cx, cy, 2 * dt[yy, xx].max() / PX))
    return np.array(out)


def _smooth(v, k=5):
    if len(v) < k: return v
    pad = np.concatenate([np.full(k // 2, v[0]), v, np.full(k // 2, v[-1])])
    return np.convolve(pad, np.ones(k) / k, mode="valid")


def measure(F, ch="?"):
    a, x0, yt, adv = F.mask(ch)
    hook, dot = split(a)
    n = nstem(F)
    cl = centreline(hook, x0, yt)
    cx, cy, cw = _smooth(cl[:, 0]), _smooth(cl[:, 1]), cl[:, 2]
    # 3 o'clock: the furthest-right point of the centreline (the hook's bowl, never its curl's end)
    i3 = int(np.argmax(cx))
    seg = slice(0, i3 + 1)
    nx, ny, nw = cx[seg][::-1], cy[seg][::-1], cw[seg][::-1]       # from 3 o'clock down to the foot
    s = np.concatenate([[0], np.cumsum(np.hypot(np.diff(nx), np.diff(ny)))]); L = s[-1]
    u = s / max(L, 1e-9)
    # angle from horizontal of the centreline, over a +/- 4-unit chord
    def ang(i):
        j0, j1 = max(0, i - 4), min(len(nx) - 1, i + 4)
        dx, dy = nx[j1] - nx[j0], ny[j1] - ny[j0]
        return math.degrees(math.atan2(dy, dx)) % 180.0 if (dx or dy) else float("nan")
    # The geodesic band nearest the seed is an arc, not a cross-section: drop the last 0.6 n of the
    # profile from the min/max (the foot is read off the rows instead).
    keep = s <= L - 0.6 * n
    def at(uu): return int(np.argmin(np.abs(u - uu)))
    o = {"n": n, "L": L / n}
    o["w"] = {f"{uu:.2f}": float(nw[at(uu)] / n) for uu in US}
    o["a"] = {f"{uu:.2f}": ang(at(uu)) for uu in US}
    kw = nw[keep] if keep.any() else nw
    o["min"] = (float(kw.min() / n), float(u[keep][np.argmin(kw)]) if keep.any() else float("nan"))
    o["max"] = (float(kw.max() / n), float(u[keep][np.argmax(kw)]) if keep.any() else float("nan"))
    o["top"] = (float(nx[0]), float(ny[0]))
    # the foot, off the rows
    hy, hx = np.nonzero(hook)
    yb = yt - (hy.max() + 1) / PX                                  # the neck's lowest ink, units
    def run_at(hh):
        r = int(round((yt - (yb + hh)) / 1.0 * PX))
        if not 0 <= r < a.shape[0]: return float("nan"), float("nan")
        cols = np.nonzero(hook[r])[0]
        if not len(cols): return float("nan"), float("nan")
        # the run nearest the neck's centreline at that height
        d = np.diff(np.concatenate([[0], hook[r].astype(np.int8), [0]]))
        st, en = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
        yy = yb + hh; k = int(np.argmin(np.abs(ny - yy))); xc = (nx[k] - x0) * PX
        best = min(zip(st, en), key=lambda se: 0 if se[0] <= xc <= se[1] else min(abs(se[0] - xc), abs(se[1] - xc)))
        return (best[1] - best[0]) / PX, x0 + (best[0] + best[1]) / 2 / PX
    (f02, c02), (f05, c05), (f10, c10) = (run_at(h) for h in FOOT_H)
    o["foot"] = (f05 / n, f10 / n, f02 / n)          # at 40, 80 and 20 units above the lowest ink
    # the end face: the lowest ink row in each column of the foot (ink within 0.6 n of the bottom)
    lo = []
    rlim = int(round(0.6 * n * PX))
    for c in range(hook.shape[1]):
        col = np.nonzero(hook[:, c])[0]
        if len(col) and col.max() >= hy.max() - rlim:
            lo.append((x0 + (c + 0.5) / PX, yt - (col.max() + 1) / PX))
    lo = np.array(lo)
    if len(lo) >= 4:
        # trim the side walls: keep the columns whose lowest ink is within the bottom 0.6 n band
        sl = np.polyfit(lo[:, 0], lo[:, 1], 1)[0]
        o["face"] = math.degrees(math.atan(sl))
        o["foot_span"] = float((lo[:, 0].max() - lo[:, 0].min()) / n)
    else:
        o["face"], o["foot_span"] = float("nan"), float("nan")
    if dot is not None:
        dy_, dx_ = np.nonzero(dot)
        dtop = yt - dy_.min() / PX; dbot = yt - (dy_.max() + 1) / PX
        dcx = x0 + (dx_.mean() + 0.5) / PX
        dd = 0.5 * ((dy_.max() + 1 - dy_.min()) + (dx_.max() + 1 - dx_.min())) / PX
        o["gap"] = (float(yb - dtop), float((yb - dtop) / dd))
        o["dx"] = float((c02 if c02 == c02 else nx[-1]) - dcx)
        o["dot"] = (float(dd / n), float(dd / f05) if f05 == f05 else float("nan"))
        o["dot_bot"] = float(dbot)
    # the neck's ink: hook pixels whose geodesic band falls in the neck
    o["ink"] = float(np.sum(nw[1:] * np.diff(s)) / (n * n))
    o["_profile"] = [(float(u[i]), float(nw[i] / n), ang(i), float(nx[i]), float(ny[i])) for i in range(0, len(u), 2)]
    o["_mask"] = (a, x0, yt)
    o["slant"] = F.slant
    return o


def report(lab, o):
    w = " ".join(f"{o['w'][k]:.2f}" for k in sorted(o["w"]))
    an = " ".join(f"{o['a'][k]:4.0f}" for k in sorted(o["a"]))
    g = o.get("gap", (float("nan"),) * 2); dt = o.get("dot", (float("nan"),) * 2)
    print(f"{lab:14s} n {o['n']:5.1f}  w@u {w}  min {o['min'][0]:.2f}@{o['min'][1]:.2f} max {o['max'][0]:.2f}@{o['max'][1]:.2f}"
          f"  a@u {an}  foot {o['foot'][0]:.2f}/{o['foot'][1]:.2f}/{o['foot'][2]:.2f}  face {o['face']:5.1f}"
          f"  gap {g[0]:5.1f} ({g[1]:.2f}d)  dx {o.get('dx', float('nan')):5.1f}  dot {dt[0]:.2f}n {dt[1]:.2f}f  ink {o['ink']:.2f}  L {o['L']:.2f}n")


def sheet(results, out, title=""):
    """Each face's ? at one x-height (0.5 px per Albo unit: the 2 px/unit mask block-averaged 4x4),
    baseline and x-line, the neck's centreline overlaid in red. For the measurer's eye, not a proof."""
    from PIL import Image, ImageDraw, ImageFont
    F = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    sc = 0.5; k = int(round(PX / sc))
    cells = []
    for lab, o in results:
        a, x0, yt = o["_mask"]
        H, W = a.shape; H2, W2 = (H // k + 1) * k, (W // k + 1) * k
        m = np.zeros((H2, W2)); m[:H, :W] = a
        g = 1.0 - m.reshape(H2 // k, k, W2 // k, k).mean(axis=(1, 3))
        im = Image.fromarray((40 + 210 * g).astype(np.uint8)).convert("RGB")
        cell = Image.new("RGB", (int(620 * sc) + 20, int(1000 * sc) + 40), (250, 250, 248))
        d = ImageDraw.Draw(cell)
        base = int(820 * sc) + 10; ox = 20 - int(min(0.0, x0) * sc)
        for yy, colr in ((0, (190, 190, 190)), (XH_ALBO, (215, 215, 215))):
            d.line([(0, base - yy * sc), (cell.width, base - yy * sc)], fill=colr)
        mask = Image.fromarray((255 * (g < 0.99)).astype(np.uint8))
        cell.paste(im, (ox + int(x0 * sc), base - int(yt * sc)), mask)
        pts = [(ox + p[3] * sc, base - p[4] * sc) for p in o["_profile"]]
        if len(pts) > 1: d.line(pts, fill=(220, 30, 30), width=1)
        d.text((4, 4), lab, fill=(0, 0, 0), font=F)
        d.text((4, cell.height - 22), f"w {o['w']['0.00']:.2f}>{o['w']['0.50']:.2f}>{o['foot'][0]:.2f}", fill=(60, 60, 60), font=F)
        cells.append(cell)
    cols = min(8, len(cells)); rows = (len(cells) + cols - 1) // cols
    Wc = cells[0].width; Hc = cells[0].height; top = 24 if title else 0
    sh = Image.new("RGB", (Wc * cols, Hc * rows + top), (250, 250, 248))
    if title: ImageDraw.Draw(sh).text((6, 4), title, fill=(0, 0, 0), font=F)
    for i, c in enumerate(cells): sh.paste(c, ((i % cols) * Wc, (i // cols) * Hc + top))
    sh.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cut", default="Italic")
    ap.add_argument("--albo", action="append", default=[], help="LABEL=DIR of an Albo build")
    ap.add_argument("--sheet"); ap.add_argument("--json")
    ap.add_argument("--albo-only", action="store_true")
    ap.add_argument("--lineage", action="store_true", help="the LINEAGE panel instead of the text-face panel")
    ap.add_argument("--ch", default="?")
    A = ap.parse_args()
    italic = "Italic" in A.cut
    entries = []
    for spec in A.albo:
        lab, d = spec.split("=", 1)
        entries.append((lab, face(os.path.join(d, f"Albo-{A.cut}.ttf"), 0, italic)))
    if not A.albo_only:
        for lab, p, i in (LINEAGE if A.lineage else PANEL)[A.cut]:
            try:
                entries.append((lab, face(p, i, italic)))
            except Exception as e:
                print("skip", lab, e, file=sys.stderr)
    res = []
    for lab, F in entries:
        try:
            o = measure(F, A.ch)
        except Exception as e:
            print("skip", lab, e, file=sys.stderr); continue
        report(lab, o); res.append((lab, o))
    if A.sheet: sheet(res, A.sheet, title=f"{A.cut} -- the ? neck (red: its centreline, 3 o'clock to foot)")
    if A.json:
        json.dump({lab: {k: v for k, v in o.items() if not k.startswith("_mask")} for lab, o in res}, open(A.json, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
