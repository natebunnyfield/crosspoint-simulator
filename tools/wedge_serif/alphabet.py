"""The full lowercase (plus . , - and space) on the same pen as wedge.py.

Every glyph is a function of the option's params p and returns
(polygons, advance). Coordinates in font units, y up, baseline 0, glyph
starts at x=0 with its left side bearing included. Same conventions as
wedge.glyphs: stems get wedge serifs, curves get the pen's contrast, and
terminals follow p["terminal"].
"""
import math
from wedge import (Pen, stroke, flare_profile, wedge, blob, bez, line,
                   superellipse, tangents)

def ctx(p):
    s = p["stem"]
    c = dict(
        xh=p["xh"], asc=p["asc"], desc=p["desc"], s=s, wf=p["width"],
        pen=Pen(s, p["contrast"], p["stress"]),
        fl=flare_profile(p["flare"], p["flare_shape"]),
        wl=p["wedge_len"] * s, wd=p["wedge_depth"] * s, tip=p["wedge_tip"] * s,
        term=p["terminal"], k=p["bowl_k"], foot=p["foot_scale"],
        st=math.radians(p["stress"]), flare=p["flare"])
    return c

def stem(c, polys, x0, y0, y1, top=True, top_side=-1, foot=True, foot_sides=(-1, 1), profile=None):
    prof = profile or c["fl"]
    polys.append(stroke(line((x0, y0), (x0, y1), 40), c["pen"], prof))
    th = c["pen"].thickness((0, 1))
    if top and c["wl"] > 0:
        polys.append(wedge((x0, y1), (0, 1), (-1, 0), th * prof(1.0), c["wl"], c["wd"], side=top_side, tip=c["tip"]))
    if foot and c["wl"] > 0:
        for sd in foot_sides:
            polys.append(wedge((x0, y0), (0, -1), (1, 0), th * prof(0.0), c["wl"] * c["foot"], c["wd"], side=sd, tip=c["tip"]))

def curve(c, polys, pts, flare_amt=0.0):
    polys.append(stroke(pts, c["pen"], flare_profile(flare_amt, "top") if flare_amt else None))

def terminal(c, polys, P, tan, th):
    if c["term"] == "teardrop":
        polys.append(blob(P, th * 0.62))
    elif c["term"] == "wedge":
        nx, ny = -tan[1], tan[0]
        polys.append(wedge(P, tan, (nx, ny), th, c["wl"] * 0.8, c["wd"] * 0.8, side=-1, tip=0))

def end_terminal(c, polys, pts, scale=1.0):
    tn = tangents(pts)[-1]
    terminal(c, polys, pts[-1], tn, c["pen"].thickness(tn) * scale)

def arc(c, cx, cy, rx, ry, a0_deg, a1_deg, n=80):
    return superellipse(cx, cy, rx, ry, c["k"], n, math.radians(a0_deg), math.radians(a1_deg))

def diag(c, polys, p0, p1, n=30):
    polys.append(stroke(line(p0, p1, n), c["pen"], c["fl"]))

# ---------------------------------------------------------------- glyphs
def g_o(c):
    P = []; rx = 245 * c["wf"]; ry = c["xh"] / 2 + 12; cx = 30 + rx
    ring = arc(c, cx, c["xh"] / 2, rx, ry, 90 + math.degrees(c["st"]), 450 + math.degrees(c["st"]), 120)
    P.append(stroke(ring, c["pen"]))
    return P, cx + rx + 30

def g_d(c):
    P = []; rx = 235 * c["wf"]; ry = c["xh"] / 2 + 12; cx = 30 + rx; x = cx + rx - c["s"] * 0.15
    P.append(stroke(arc(c, cx, c["xh"] / 2, rx, ry, 90, 450, 120), c["pen"]))
    stem(c, P, x, 0, c["asc"], top=True, foot=True, foot_sides=(1,))
    return P, x + c["s"] / 2 + 40 * c["wf"]

def g_b(c):
    P = []; rx = 235 * c["wf"]; ry = c["xh"] / 2 + 12; x = 40 * c["wf"] + c["s"] / 2; cx = x + rx - c["s"] * 0.15
    stem(c, P, x, 0, c["asc"], top=True, foot=True, foot_sides=(-1,))
    P.append(stroke(arc(c, cx, c["xh"] / 2, rx, ry, 90, 450, 120), c["pen"]))
    return P, cx + rx + 30

def g_p(c):
    P = []; rx = 235 * c["wf"]; ry = c["xh"] / 2 + 12; x = 40 * c["wf"] + c["s"] / 2; cx = x + rx - c["s"] * 0.15
    stem(c, P, x, -c["desc"], c["xh"], top=True, foot=True, foot_sides=(-1, 1))
    P.append(stroke(arc(c, cx, c["xh"] / 2, rx, ry, 90, 450, 120), c["pen"]))
    return P, cx + rx + 30

def g_q(c):
    P = []; rx = 235 * c["wf"]; ry = c["xh"] / 2 + 12; cx = 30 + rx; x = cx + rx - c["s"] * 0.15
    P.append(stroke(arc(c, cx, c["xh"] / 2, rx, ry, 90, 450, 120), c["pen"]))
    stem(c, P, x, -c["desc"], c["xh"], top=True, foot=True, foot_sides=(1,))
    return P, x + c["s"] / 2 + 40 * c["wf"]

def g_c(c):
    P = []; rx = 235 * c["wf"]; ry = c["xh"] / 2 + 12; cx = 30 + rx
    pts = arc(c, cx, c["xh"] / 2, rx, ry, 40, 320, 100)
    P.append(stroke(pts, c["pen"]))
    end_terminal(c, P, pts); end_terminal(c, P, pts[::-1])
    return P, cx + rx * 0.95 + 30

def g_e(c):
    P = []; rx = 235 * c["wf"]; ry = c["xh"] / 2 + 12; cx = 30 + rx
    pts = arc(c, cx, c["xh"] / 2, rx, ry, 0, 320, 100)
    P.append(stroke(pts, c["pen"]))
    end_terminal(c, P, pts[::-1])
    bar = line((cx - rx + c["s"] * 0.3, c["xh"] * 0.53), (cx + rx, c["xh"] * 0.53), 12)
    P.append(stroke(bar, c["pen"]))
    return P, cx + rx * 0.95 + 30

def g_a(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]
    x = 40 * wf + 380 * wf; rx = 180 * wf
    # two-storey: a right stem, a top hook to the left, a lower bowl
    stem(c, P, x, 0, xh * 0.98, top=False, foot=True, foot_sides=(-1, 1))
    hook = bez((x, xh * 0.72), (x, xh * 1.02), (x - 260 * wf, xh * 1.06), (x - 330 * wf, xh * 0.80), 36)
    curve(c, P, hook, c["flare"] * 0.5); end_terminal(c, P, hook)
    bowl = arc(c, x - rx, xh * 0.29, rx, xh * 0.31, 40, 360, 90)
    P.append(stroke(bowl, c["pen"]))
    return P, x + s / 2 + 40 * wf

def g_g(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; desc = c["desc"]
    rx = 235 * wf; ry = xh / 2 + 12; cx = 30 + rx; x = cx + rx - s * 0.15
    P.append(stroke(arc(c, cx, xh / 2, rx, ry, 90, 450, 120), c["pen"]))
    stem(c, P, x, -desc * 0.25, xh, top=True, foot=False, top_side=1)
    tail = bez((x, -desc * 0.25), (x, -desc * 1.05), (cx - rx * 0.9, -desc * 1.1), (cx - rx * 1.1, -desc * 0.55), 40)
    curve(c, P, tail, c["flare"] * 0.5); end_terminal(c, P, tail)
    return P, x + s / 2 + 40 * wf

def _arch(c, P, x0, x1, xh, drop=0.62):
    pts = bez((x0, xh * drop), (x0, xh * 1.02), (x1, xh * 1.02), (x1, xh * 0.62), 40)
    curve(c, P, pts)

def g_n(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x0 = 40 * wf + s / 2; x1 = x0 + 400 * wf
    stem(c, P, x0, 0, xh, top=True, foot=True)
    _arch(c, P, x0, x1, xh)
    stem(c, P, x1, 0, xh * 0.66, top=False, foot=True)
    return P, x1 + s / 2 + 40 * wf

def g_h(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x0 = 40 * wf + s / 2; x1 = x0 + 400 * wf
    stem(c, P, x0, 0, c["asc"], top=True, foot=True)
    _arch(c, P, x0, x1, xh)
    stem(c, P, x1, 0, xh * 0.66, top=False, foot=True)
    return P, x1 + s / 2 + 40 * wf

def g_m(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x0 = 40 * wf + s / 2; x1 = x0 + 360 * wf; x2 = x1 + 360 * wf
    stem(c, P, x0, 0, xh, top=True, foot=True)
    _arch(c, P, x0, x1, xh); stem(c, P, x1, 0, xh * 0.66, top=False, foot=True, foot_sides=())
    _arch(c, P, x1, x2, xh); stem(c, P, x2, 0, xh * 0.66, top=False, foot=True)
    return P, x2 + s / 2 + 40 * wf

def g_u(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x0 = 40 * wf + s / 2; x1 = x0 + 400 * wf
    stem(c, P, x0, xh * 0.38, xh, top=True, foot=False)
    pts = bez((x0, xh * 0.38), (x0, -10), (x1, -10), (x1, xh * 0.38), 40)
    curve(c, P, pts)
    stem(c, P, x1, 0, xh, top=True, foot=True, foot_sides=(1,))
    return P, x1 + s / 2 + 40 * wf

def g_i(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x = 40 * wf + s / 2
    stem(c, P, x, 0, xh, top=True, foot=True)
    P.append(blob((x, xh + 105 + s * 0.3), s * 0.5))
    return P, x + s / 2 + 40 * wf

def g_l(c):
    P = []; wf = c["wf"]; s = c["s"]; x = 40 * wf + s / 2
    stem(c, P, x, 0, c["asc"], top=True, foot=True)
    return P, x + s / 2 + 40 * wf

def g_t(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x = 60 * wf + s / 2; r = 130 * wf
    stem(c, P, x, r * 0.9, xh + 110, top=False, foot=False)
    tail = bez((x, r * 0.9), (x, -8), (x + r * 0.8, -8), (x + r * 1.4, r * 0.55), 36)
    curve(c, P, tail, c["flare"] * 0.5); end_terminal(c, P, tail)
    bar = line((x - 110 * wf, xh), (x + 150 * wf, xh), 12)
    P.append(stroke(bar, c["pen"]))
    return P, x + 160 * wf

def g_k(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x = 40 * wf + s / 2
    stem(c, P, x, 0, c["asc"], top=True, foot=True)
    diag(c, P, (x + 380 * wf, xh * 0.98), (x + s * 0.3, xh * 0.42))
    diag(c, P, (x + 170 * wf, xh * 0.55), (x + 400 * wf, 0))
    return P, x + 400 * wf + 40 * wf

def g_v(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x = 30 * wf; w = 470 * wf
    diag(c, P, (x + s * 0.4, xh), (x + w / 2, 0))
    diag(c, P, (x + w - s * 0.4, xh), (x + w / 2, 0))
    return P, x + w + 30 * wf

def g_w(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x = 30 * wf; w = 720 * wf
    diag(c, P, (x + s * 0.4, xh), (x + w * 0.27, 0))
    diag(c, P, (x + w * 0.5, xh * 0.95), (x + w * 0.27, 0))
    diag(c, P, (x + w * 0.5, xh * 0.95), (x + w * 0.73, 0))
    diag(c, P, (x + w - s * 0.4, xh), (x + w * 0.73, 0))
    return P, x + w + 30 * wf

def g_x(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x = 30 * wf; w = 460 * wf
    diag(c, P, (x + s * 0.4, xh), (x + w - s * 0.4, 0))
    diag(c, P, (x + w - s * 0.4, xh), (x + s * 0.4, 0))
    return P, x + w + 30 * wf

def g_y(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; desc = c["desc"]; x = 30 * wf; w = 470 * wf
    diag(c, P, (x + s * 0.4, xh), (x + w / 2, 0))
    tail = bez((x + w - s * 0.4, xh), (x + w * 0.55, -desc * 0.6), (x + w * 0.45, -desc * 1.05), (x + w * 0.05, -desc * 0.9), 44)
    curve(c, P, tail, c["flare"] * 0.4); end_terminal(c, P, tail)
    return P, x + w + 30 * wf

def g_z(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x = 40 * wf; w = 430 * wf
    P.append(stroke(line((x, xh), (x + w, xh), 12), c["pen"]))
    diag(c, P, (x + w - s * 0.2, xh), (x + s * 0.2, 0))
    P.append(stroke(line((x, 0), (x + w, 0), 12), c["pen"]))
    return P, x + w + 40 * wf

def g_s(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x = 40 * wf; w = 400 * wf
    top = bez((x + w * 0.95, xh * 0.82), (x + w * 0.75, xh * 1.08), (x + w * 0.02, xh * 1.05), (x + w * 0.12, xh * 0.62), 40)
    mid = bez((x + w * 0.12, xh * 0.62), (x + w * 0.22, xh * 0.28), (x + w * 0.95, xh * 0.66), (x + w * 0.9, xh * 0.28), 40)
    bot = bez((x + w * 0.9, xh * 0.28), (x + w * 0.85, -xh * 0.1), (x + w * 0.2, -xh * 0.08), (x + w * 0.04, xh * 0.2), 40)
    for seg in (top, mid, bot):
        curve(c, P, seg)
    end_terminal(c, P, top[::-1]); end_terminal(c, P, bot)
    return P, x + w + 40 * wf

def g_r(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x = 40 * wf + s / 2
    stem(c, P, x, 0, xh, top=True, foot=True)
    arm = bez((x, xh * 0.62), (x, xh * 0.98), (x + 120 * wf, xh + 6), (x + 205 * wf, xh - 40), 36)
    curve(c, P, arm, c["flare"] * 0.7); end_terminal(c, P, arm, 1 + c["flare"] * 0.7)
    return P, x + 205 * wf + 40 * wf

def g_f(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; asc = c["asc"]; r = 150 * wf; x = 60 * wf + s / 2
    stem(c, P, x, 0, asc - r, top=False, foot=True)
    hook = bez((x, asc - r), (x, asc + 8), (x + r * 0.9, asc + 8), (x + r * 1.25, asc - r * 0.5), 40)
    curve(c, P, hook, c["flare"] * 0.6); end_terminal(c, P, hook, 1 + c["flare"] * 0.6)
    P.append(stroke(line((x - 120 * wf, xh), (x + 150 * wf, xh), 12), c["pen"]))
    return P, x + 150 * wf + 50 * wf

def g_j(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; desc = c["desc"]; rj = 170 * wf; x = 40 * wf + s / 2 + 120 * wf
    stem(c, P, x, -desc + rj * 0.15, xh, top=True, foot=False)
    tail = bez((x, -desc + rj * 0.15), (x, -desc - rj * 0.55), (x - rj * 0.6, -desc - rj * 0.75), (x - rj * 1.15, -desc - rj * 0.25), 40)
    curve(c, P, tail, c["flare"] * 0.5); end_terminal(c, P, tail)
    P.append(blob((x, xh + 105 + s * 0.3), s * 0.5))
    return P, x + s / 2 + 40 * wf

def g_period(c):
    P = [blob((60 * c["wf"] + c["s"] * 0.55, c["s"] * 0.55), c["s"] * 0.55)]
    return P, 120 * c["wf"] + c["s"] * 1.1

def g_comma(c):
    s = c["s"]; x = 60 * c["wf"] + s * 0.55
    P = [blob((x, s * 0.55), s * 0.55)]
    tail = bez((x + s * 0.1, s * 0.2), (x + s * 0.1, -s * 0.5), (x - s * 0.3, -s * 0.9), (x - s * 0.6, -s * 1.2), 20)
    P.append(stroke(tail, c["pen"], lambda t: 0.9 - 0.6 * t))
    return P, 120 * c["wf"] + s * 1.1

def g_hyphen(c):
    P = [stroke(line((40 * c["wf"], c["xh"] * 0.48), (40 * c["wf"] + 240 * c["wf"], c["xh"] * 0.48), 8), c["pen"])]
    return P, 320 * c["wf"]

def g_space(c):
    return [], 250 * c["wf"]

GLYPHS = {
    'a': g_a, 'b': g_b, 'c': g_c, 'd': g_d, 'e': g_e, 'f': g_f, 'g': g_g, 'h': g_h, 'i': g_i,
    'j': g_j, 'k': g_k, 'l': g_l, 'm': g_m, 'n': g_n, 'o': g_o, 'p': g_p, 'q': g_q, 'r': g_r,
    's': g_s, 't': g_t, 'u': g_u, 'v': g_v, 'w': g_w, 'x': g_x, 'y': g_y, 'z': g_z,
    '.': g_period, ',': g_comma, '-': g_hyphen, ' ': g_space,
}

def layout(p, text):
    """Polygons for a line of text, plus its advance. Unknown chars are skipped."""
    c = ctx(p)
    polys = []; x = 0.0
    for ch in text:
        fn = GLYPHS.get(ch.lower())
        if not fn:
            continue
        gp, adv = fn(c)
        polys.extend([[(px + x, py) for (px, py) in poly] for poly in gp])
        x += adv + (22 + c["s"] * 0.16) * c["wf"]  # tracking: the bearings alone ran tight
    if p["slant"]:
        sh = math.tan(math.radians(p["slant"]))
        polys = [[(px + py * sh, py) for (px, py) in poly] for poly in polys]
    return polys, x

def wrap(p, text, max_units):
    """Greedy word wrap by advance width, in font units."""
    words = text.split(' ')
    lines, cur = [], ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if layout(p, trial)[1] <= max_units or not cur:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines
