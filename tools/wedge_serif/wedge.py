"""A parametric humanist wedge-serif synthesizer, for one word: "fjord".

Every option is the SAME five skeletons drawn with a different pen, flare,
wedge, proportion and stress. Output: SVG polygons (one <path> per stroke,
separate fills, so overlaps union visually) and a PIL raster for a preview.
Font space: 1000 upm, y up. Baseline y=0.
"""
import math

EM = 1000.0

# ---------------------------------------------------------------- geometry
def bez(p0, p1, p2, p3, n=36):
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        x = mt**3*p0[0] + 3*mt*mt*t*p1[0] + 3*mt*t*t*p2[0] + t**3*p3[0]
        y = mt**3*p0[1] + 3*mt*mt*t*p1[1] + 3*mt*t*t*p2[1] + t**3*p3[1]
        pts.append((x, y))
    return pts

def line(p0, p1, n=24):
    return [(p0[0] + (p1[0]-p0[0])*i/n, p0[1] + (p1[1]-p0[1])*i/n) for i in range(n+1)]

def superellipse(cx, cy, rx, ry, k=2.0, n=96, a0=0.0, a1=2*math.pi):
    """k=2 circle/ellipse; k>2 squarer. Sampled by angle."""
    pts = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        c, s = math.cos(a), math.sin(a)
        x = cx + rx * math.copysign(abs(c) ** (2.0 / k), c)
        y = cy + ry * math.copysign(abs(s) ** (2.0 / k), s)
        pts.append((x, y))
    return pts

def tangents(pts):
    t = []
    for i in range(len(pts)):
        a = pts[max(0, i-1)]; b = pts[min(len(pts)-1, i+1)]
        dx, dy = b[0]-a[0], b[1]-a[1]
        L = math.hypot(dx, dy) or 1.0
        t.append((dx/L, dy/L))
    return t

# ---------------------------------------------------------------- the pen
class Pen:
    def __init__(self, stem, contrast, stress_deg):
        self.stem = stem
        self.hair = stem * (1.0 - contrast)
        self.stress = math.radians(stress_deg)

    def thickness(self, tan):
        # broad nib held at `stress`: full stem when the stroke runs
        # perpendicular to the nib, hairline when along it.
        phi = math.atan2(tan[1], tan[0])
        return max(self.stem * abs(math.sin(phi - self.stress)), self.hair)

def stroke(pts, pen, profile=None, end_scale=None):
    """Outline a centerline. profile(t)->thickness multiplier (flare/entasis)."""
    tans = tangents(pts)
    left, right = [], []
    n = len(pts) - 1
    for i, (p, tn) in enumerate(zip(pts, tans)):
        th = pen.thickness(tn)
        if profile:
            th *= profile(i / n)
        nx, ny = -tn[1], tn[0]
        left.append((p[0] + nx*th/2, p[1] + ny*th/2))
        right.append((p[0] - nx*th/2, p[1] - ny*th/2))
    return left + right[::-1]

def flare_profile(amount, shape="entasis"):
    """Albertus: the stem swells toward both ends. shape 'entasis' = concave
    stem (thin middle), 'ends' = only the last 30% each end swells."""
    def f(t):
        if shape == "entasis":
            return 1.0 + amount * (2*t - 1)**2
        if shape == "ends":
            e = max(0.0, (abs(2*t - 1) - 0.4) / 0.6)
            return 1.0 + amount * e**1.6
        if shape == "top":
            return 1.0 + amount * max(0.0, (t - 0.55) / 0.45)**1.5
        return 1.0
    return f

def wedge(P, d, n, th, length, depth, side=-1, tip=0.0):
    """A triangular serif at stem end P. d = unit outward direction of the
    stem at its end, n = unit normal, th = stem thickness there.
    side -1 = the serif sticks out to the -n side (left of an upright stem
    when d points up), +1 the other side. `tip` lifts/drops the apex along d."""
    A = (P[0] + side*n[0]*th/2, P[1] + side*n[1]*th/2)          # stem corner
    B = (A[0] + side*n[0]*length + d[0]*tip, A[1] + side*n[1]*length + d[1]*tip)  # apex
    C = (A[0] - d[0]*depth, A[1] - d[1]*depth)                    # back down the stem
    # two interior points so the serif overlaps INTO the stem: no hairline slit
    # where two polygons merely touch.
    Ci = (C[0] - side*n[0]*th*0.45, C[1] - side*n[1]*th*0.45)
    Ai = (A[0] - side*n[0]*th*0.45, A[1] - side*n[1]*th*0.45)
    return [Ai, A, B, C, Ci]

def blob(P, r, n=28):
    return [(P[0] + r*math.cos(2*math.pi*i/n), P[1] + r*math.sin(2*math.pi*i/n)) for i in range(n)]

# ---------------------------------------------------------------- glyphs
def glyphs(p):
    """Return list of polygons for f j o r d, and the advance width."""
    xh, asc, desc = p["xh"], p["asc"], p["desc"]
    s = p["stem"]; wf = p["width"]
    pen = Pen(s, p["contrast"], p["stress"])
    fl = flare_profile(p["flare"], p["flare_shape"])
    wl, wd = p["wedge_len"] * s, p["wedge_depth"] * s
    term = p["terminal"]
    k = p["bowl_k"]
    polys = []
    x = 0.0
    gap = 70 * wf + (s - 110) * 0.6  # heavier cuts need more air

    def stem_polys(x0, y0, y1, top_wedge=True, foot=True, top_side=-1, foot_sides=(-1, 1)):
        pts = line((x0, y0), (x0, y1), 40)
        polys.append(stroke(pts, pen, fl))
        th_top = pen.thickness((0, 1)) * fl(1.0)
        th_bot = pen.thickness((0, 1)) * fl(0.0)
        if top_wedge and wl > 0:
            polys.append(wedge((x0, y1), (0, 1), (-1, 0), th_top, wl, wd, side=top_side, tip=p["wedge_tip"] * s))
        if foot and wl > 0:
            for sd in foot_sides:
                polys.append(wedge((x0, y0), (0, -1), (1, 0), th_bot, wl * p["foot_scale"], wd, side=sd, tip=p["wedge_tip"] * s))

    def terminal(P, tan, th):
        if term == "teardrop":
            polys.append(blob(P, th * 0.62))
        elif term == "wedge":
            nx, ny = -tan[1], tan[0]
            polys.append(wedge(P, tan, (nx, ny), th, wl * 0.8, wd * 0.8, side=-1, tip=0))
        # 'cut' and 'flare' need nothing extra (flare is in the profile)

    # ---- f
    r = 150 * wf
    fx = x + 60 * wf + s/2
    stem_polys(fx, 0, asc - r, top_wedge=False, foot=True)
    hook = bez((fx, asc - r), (fx, asc + 8), (fx + r*0.9, asc + 8), (fx + r*1.25, asc - r*0.5), 40)
    polys.append(stroke(hook, pen, flare_profile(p["flare"]*0.6, "top")))
    tn = tangents(hook)[-1]
    terminal(hook[-1], tn, pen.thickness(tn) * (1 + p["flare"]*0.6))
    bar = line((fx - 120*wf, xh), (fx + 150*wf, xh), 12)
    polys.append(stroke(bar, pen, lambda t: 1.0 + 0.35*p["flare"]*abs(2*t-1)))
    x = fx + 150 * wf + gap + 25 * wf

    # ---- j
    jx = x + s/2 + 40*wf
    rj = 170 * wf
    stem_polys(jx, -desc + rj*0.15, xh, top_wedge=True, foot=False, top_side=-1)
    tail = bez((jx, -desc + rj*0.15), (jx, -desc - rj*0.55), (jx - rj*0.6, -desc - rj*0.75), (jx - rj*1.15, -desc - rj*0.25), 40)
    polys.append(stroke(tail, pen, flare_profile(p["flare"]*0.5, "top")))
    tn = tangents(tail)[-1]
    terminal(tail[-1], tn, pen.thickness(tn))
    dot = p["dot"]
    dy = xh + 105 + s*0.3  # under the f hook, not in it
    if dot == "round":
        polys.append(blob((jx, dy), s*0.5))
    elif dot == "square":
        h = s*0.55
        polys.append([(jx-h, dy-h), (jx+h, dy-h), (jx+h, dy+h), (jx-h, dy+h)])
    else:  # wedge-shaped dot
        h = s*0.6
        polys.append([(jx-h*1.1, dy-h*0.6), (jx+h*1.1, dy-h*0.9), (jx+h*0.7, dy+h*1.0), (jx-h*0.8, dy+h*0.8)])
    x = jx + s/2 + gap

    # ---- o
    rx = 245 * wf; ry = xh/2 + 12
    cx = x + rx + 10
    ring = superellipse(cx, xh/2, rx - s/2*0.0, ry, k, 120, math.radians(p["stress"]) + math.pi/2, math.radians(p["stress"]) + math.pi/2 + 2*math.pi)
    polys.append(stroke(ring, pen, lambda t: 1.0 + p["o_swell"]*0.0))
    x = cx + rx + gap

    # ---- r
    rx_ = x + s/2 + 40*wf
    stem_polys(rx_, 0, xh, top_wedge=True, foot=True, top_side=-1)
    arm = bez((rx_, xh*0.62), (rx_, xh*0.98), (rx_ + 120*wf, xh + 6), (rx_ + 205*wf, xh - 40), 36)
    polys.append(stroke(arm, pen, flare_profile(p["flare"]*0.7, "top")))
    tn = tangents(arm)[-1]
    terminal(arm[-1], tn, pen.thickness(tn) * (1 + p["flare"]*0.7))
    x = rx_ + 205*wf + gap * 0.9

    # ---- d
    rxd = 235 * wf; ryd = xh/2 + 12
    cxd = x + rxd + 10
    dx = cxd + rxd - s*0.15
    bowl = superellipse(cxd, xh/2, rxd, ryd, k, 120, math.radians(p["stress"]) + math.pi/2, math.radians(p["stress"]) + math.pi/2 + 2*math.pi)
    polys.append(stroke(bowl, pen))
    stem_polys(dx, 0, asc, top_wedge=True, foot=True, top_side=-1, foot_sides=(1,))
    x = dx + s/2 + 40*wf

    # slant
    if p["slant"]:
        sh = math.tan(math.radians(p["slant"]))
        polys = [[(px + py*sh, py) for (px, py) in poly] for poly in polys]
        x += asc * sh
    return polys, x

# ---------------------------------------------------------------- output
def svg_for(p, scale=0.28):
    polys, adv = glyphs(p)
    top, bot = p["asc"] + 40, -p["desc"] - 200
    w = (adv + 40) * scale; h = (top - bot) * scale
    d = []
    for poly in polys:
        pts = " ".join(f"{(x+20)*scale:.1f},{(top - y)*scale:.1f}" for x, y in poly)
        d.append(f'<polygon points="{pts}"/>')
    return f'<svg viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" fill="currentColor">{"".join(d)}</svg>', adv

def raster(p, scale=0.5, ink=(0x5C,0x33,0x2B), paper=(0xF9,0xF3,0xE9)):
    from PIL import Image, ImageDraw
    polys, adv = glyphs(p)
    top, bot = p["asc"] + 40, -p["desc"] - 200
    W, H = int((adv + 40) * scale), int((top - bot) * scale)
    im = Image.new("RGB", (W, H), paper)
    dr = ImageDraw.Draw(im)
    for poly in polys:
        dr.polygon([((x+20)*scale, (top - y)*scale) for x, y in poly], fill=ink)
    return im

BASE = dict(xh=480, asc=720, desc=220, stem=110, contrast=0.55, stress=18, width=1.0,
            flare=0.25, flare_shape="entasis", wedge_len=0.23, wedge_depth=0.45, wedge_tip=0.0,
            foot_scale=0.8, terminal="cut", bowl_k=2.0, dot="round", slant=0, o_swell=0)

OPTIONS = [
 ("1  Albertus lineage", "flared stems, no separate wedge, moderate contrast",
  dict(flare=0.55, flare_shape="ends", wedge_len=0.00, contrast=0.5, stress=15, terminal="flare")),
 ("2  Icone lineage", "concave stems, crisp wedges, near-mono",
  dict(flare=0.35, flare_shape="entasis", wedge_len=0.55, wedge_depth=1.10, contrast=0.25, stress=10, terminal="wedge", dot="wedge")),
 ("3  Text cut", "moderate everything, built for 11 pt",
  dict(stem=105, xh=500, flare=0.18, wedge_len=0.40, wedge_depth=0.70, contrast=0.45, stress=20, terminal="cut")),
 ("4  Chisel", "big triangular wedges, low contrast, Friz-Quadrata weight",
  dict(stem=135, flare=0.12, wedge_len=0.75, wedge_depth=1.30, contrast=0.3, stress=12, terminal="wedge", foot_scale=1.0, dot="square")),
 ("5  Calligraphic", "high contrast, strong stress, small hooked wedges",
  dict(stem=115, contrast=0.8, stress=30, flare=0.2, wedge_len=0.35, wedge_depth=0.60, wedge_tip=0.25, terminal="teardrop")),
 ("6  Monoline flare", "Optima-like: almost no contrast, gentle swell, no wedge",
  dict(stem=100, contrast=0.1, stress=0, flare=0.4, flare_shape="ends", wedge_len=0.00, terminal="flare")),
 ("7  Condensed", "narrow, tall x-height, quick wedges",
  dict(width=0.78, xh=530, stem=105, flare=0.22, wedge_len=0.40, wedge_depth=0.75, contrast=0.4, stress=14)),
 ("8  Wide", "extended, low x-height, generous bowls",
  dict(width=1.25, xh=440, stem=105, flare=0.25, wedge_len=0.45, wedge_depth=0.80, contrast=0.5, stress=18)),
 ("9  Slanted", "an upright's skeleton at 7 degrees, teardrop terminals",
  dict(slant=7, flare=0.25, wedge_len=0.40, wedge_depth=0.75, contrast=0.55, stress=25, terminal="teardrop")),
 ("10 Classical", "low x-height, long ascenders, quiet wedges, book weight",
  dict(xh=430, asc=760, desc=250, stem=95, flare=0.2, wedge_len=0.35, wedge_depth=0.65, contrast=0.6, stress=22)),
 ("11 Modern tall", "tall x-height, short ascenders, squarish bowls",
  dict(xh=560, asc=700, desc=200, stem=110, bowl_k=2.6, flare=0.2, wedge_len=0.45, wedge_depth=0.80, contrast=0.4, stress=12)),
 ("12 Heavy display", "bold, blunt wedges both sides of the foot",
  dict(stem=165, contrast=0.35, stress=10, flare=0.15, wedge_len=0.40, wedge_depth=0.90, foot_scale=1.0, terminal="wedge", dot="square")),
 ("13 Light", "hairline weight, sharp long wedges",
  dict(stem=62, contrast=0.5, stress=18, flare=0.3, wedge_len=0.80, wedge_depth=1.20, terminal="wedge")),
 ("14 Squared humanist", "superellipse bowls, straight-sided wedges",
  dict(bowl_k=3.2, stem=115, contrast=0.35, stress=8, flare=0.1, wedge_len=0.50, wedge_depth=1.00, terminal="cut", dot="square")),
 ("15 Reverse stress", "rustic: the weight sits on the horizontals",
  dict(stress=90+20, contrast=0.55, stem=115, flare=0.25, wedge_len=0.45, wedge_depth=0.80, terminal="cut")),
 ("16 Extreme flare", "trumpet stems, no wedges, the ends do the talking",
  dict(flare=0.95, flare_shape="ends", wedge_len=0.00, contrast=0.4, stress=15, terminal="flare")),
 ("17 Rounded", "soft round terminals and dots, low wedges",
  dict(terminal="teardrop", dot="round", flare=0.2, wedge_len=0.30, wedge_depth=0.70, wedge_tip=0.3, contrast=0.4, stress=16)),
 ("18 Inscriptional", "chisel-cut: sharp entasis and tipped wedges, high stress",
  dict(flare=0.45, flare_shape="entasis", wedge_len=0.60, wedge_depth=1.00, wedge_tip=0.4, contrast=0.6, stress=28, terminal="wedge")),
 ("19 Sturdy text", "low contrast, moderate wedges, medium weight, a screen face",
  dict(stem=120, contrast=0.3, stress=14, xh=510, flare=0.18, wedge_len=0.42, wedge_depth=0.75, terminal="cut")),
 ("20 Asymmetric", "wedges only on the left, feet only on the right; a hand's bias",
  dict(flare=0.3, flare_shape="ends", wedge_len=0.50, wedge_depth=0.90, foot_scale=0.6, contrast=0.5, stress=20, terminal="wedge")),
]

def option_params(i):
    name, blurb, over = OPTIONS[i]
    p = dict(BASE); p.update(over)
    return name, blurb, p

if __name__ == "__main__":
    import sys, os
    out = os.path.dirname(os.path.abspath(__file__))
    from PIL import Image
    tiles = []
    for i in range(len(OPTIONS)):
        name, blurb, p = option_params(i)
        im = raster(p, 0.5)
        im.save(os.path.join(out, f"opt{i+1:02d}.png"))
        tiles.append(im)
    W = max(t.width for t in tiles); H = max(t.height for t in tiles)
    sheet = Image.new("RGB", (W*4, H*5), (0xF9,0xF3,0xE9))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % 4) * W, (i // 4) * H))
    sheet.save(os.path.join(out, "sheet.png"))
    print("ok", W, H)
