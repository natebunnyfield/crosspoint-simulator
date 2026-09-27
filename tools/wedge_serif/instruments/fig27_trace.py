"""Trace the old-style 2 and 7 of the reference serifs into Albo's units
(round 406, 2026-09-26; docs/albo-figures-2-7-2026-09-26.md).

Owner 2026-09-26: *"give me options of redoing the 2 and 7 based on tracing
other reference fonts, both roman and italic"*.

"TRACING" HERE IS MEASUREMENT, NOT COPYING. Every reference glyph is rendered
UNHINTED with FreeType, UNSHEARED by its MEASURED slant (the `l`'s axis, never
`post.italicAngle` -- refs_registry.py records why), and scaled so the face's
own x-height lands on Albo's 429 units, at 2 px per unit. What comes out is a
skeleton-and-weight description in Albo's design units: where the strokes go,
how thick each one is against the SAME face's n stem, and the proportions of
the figure. The arms in `figures.py` are then Albo's own pen construction set
to those numbers; no outline point of any reference is used.

The SAME function measures an Albo build, so an arm and its reference are read
by one instrument (albo-method: an instrument that reads two things two ways
produces a difference that is the instrument).

    PYTHON_GIL=0 python3 instruments/fig27_trace.py --refs [--json OUT]
    PYTHON_GIL=0 python3 instruments/fig27_trace.py --albo DIR [--label L]

What each number is (units are Albo design units at xh 429 unless marked):

  the 2   w, top, bot     ink extent; `adv` the advance
          arc             the arc's horizontal thickness at its widest point
          crown           the vertical thickness at the arc's highest column
          slash, s_ang    the diagonal's perpendicular thickness and its angle
                          from horizontal, on rows 8-30% of the height above the
                          base; `s_bow` its bow (sagitta / length, + = bowed up
                          and left, i.e. concave, the Georgia/Hoefler spine)
          base            the base's vertical thickness, columns 55-80% of w
          over            the base's right end past the arc's right edge
          t_drop          how far down the arc's left terminal hangs (x height)
          t_size          the terminal's largest vertical run (a ball reads big)
          arc_w           the arc's rightmost ink as a fraction of the ink width
  the 7   w, top, bot     ink extent (bot < 0: the descender)
          bar_l/m/r       the bar's vertical thickness at 20/35/50% of w
          beak            ink hanging under the bar at its left end (units)
          leg_t, leg_b    the leg's perpendicular thickness, upper/lower quarter
          l_ang           the leg's angle from VERTICAL
          l_bow           its bow (+ = bowed toward the lower right, concave
                          seen from the bar's underside)
          foot_x          the leg's center at its lowest row, fraction of w
          flare           the foot's width over the lower leg's
  both    nstem           the face's n stem; every stroke is also reported
                          / nstem as `*_n`, which is what an arm is set to
"""
import argparse, json, math, os, sys
import numpy as np
import freetype

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
SUP = "/System/Library/Fonts/Supplemental/"
PAL = "/System/Library/Fonts/Palatino.ttc"
RF = os.path.join(WS, "refs") + "/"
XH_ALBO = 429.0
PX = 2.0          # px per Albo unit

# (label, path, face index, glyph for 2, glyph for 7, old-style?, italic?[, slant letter])
# HOEFLER TEXT ITALIC'S `l` IS NOT A BARE STEM: read the l's way it measures
# 21.0 degrees (15.0 on its upper half), where its `I` reads 13.4 / 13.2 and
# `post` says 13.5. Unsheared by 21 its figures lean LEFT, which is how it was
# caught. It is measured off the I.
REFS = [
    ("Georgia",            SUP + "Georgia.ttf",        0, "two", "seven", True, False),
    ("Hoefler Text",       SUP + "Hoefler Text.ttc",   0, "two.oldstyle", "seven.oldstyle", True, False),
    ("Palatino",           PAL,                        0, "twooldstyle", "sevenoldstyle", True, False),
    ("Big Caslon",         SUP + "BigCaslon.ttf",      0, "two", "seven", True, False),
    ("Charter",            SUP + "Charter.ttc",        0, "two", "seven", False, False),
    ("Baskerville",        SUP + "Baskerville.ttc",    0, "two", "seven", False, False),
    ("Georgia Italic",     SUP + "Georgia Italic.ttf", 0, "two", "seven", True, True),
    ("Hoefler Italic",     SUP + "Hoefler Text.ttc",   2, "two.oldstyle", "seven.oldstyle", True, True, "I"),
    ("Palatino Italic",    PAL,                        1, "twooldstyle", "sevenoldstyle", True, True),
    ("Flanker Griffo",     RF + "flanker-griffo-italic.otf", 0, "two.onum", "seven.onum", True, True),
    ("Poetica",            RF + "poetica-std-regular.otf",   0, "two", "seven", True, True),
    ("Pagella Italic",     RF + "texgyrepagella-italic.otf", 0, "two.oldstyle", "seven.oldstyle", True, True),
    ("Charter Italic",     SUP + "Charter.ttc",        1, "two", "seven", False, True),
    ("Baskerville Italic", SUP + "Baskerville.ttc",    2, "two", "seven", False, True),
]


class Face:
    def __init__(self, path, index=0, slant=None, slant_ch="l"):
        self.slant_ch = slant_ch
        self.f = freetype.Face(path, index=index)
        self.upm = self.f.units_per_EM
        self.xh = self._bbox_units("x")[3]
        self.slant = self.measure_slant() if slant is None else slant
        self.k = XH_ALBO / self.xh           # font units -> Albo units

    def _gid(self, name_or_char):
        if len(name_or_char) == 1:
            return self.f.get_char_index(ord(name_or_char))
        return self.f.get_name_index(name_or_char.encode())

    def _bbox_units(self, g):
        self.f.set_char_size(self.upm * 64, 0, 72, 72)
        self.f.set_transform(freetype.Matrix(0x10000, 0, 0, 0x10000), freetype.Vector(0, 0))
        self.f.load_glyph(self._gid(g), freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING)
        b = self.f.glyph.outline.get_bbox()
        return (b.xMin, b.yMin, b.xMax, b.yMax)

    def mask(self, g, shear=None):
        """(bool array rows top->bottom, x0 units, ytop units, advance units)."""
        s = self.slant if shear is None else shear
        ppem = self.upm * self.k * PX
        self.f.set_char_size(int(round(ppem * 64)), 0, 72, 72)
        m = freetype.Matrix(0x10000, int(round(-math.tan(math.radians(s)) * 0x10000)), 0, 0x10000)
        self.f.set_transform(m, freetype.Vector(0, 0))
        self.f.load_glyph(self._gid(g), freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_BITMAP)
        self.f.glyph.render(freetype.FT_RENDER_MODE_NORMAL)
        bm = self.f.glyph.bitmap
        a = np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.pitch)[:, :bm.width] >= 128
        adv = self.f.glyph.linearHoriAdvance / 65536.0 / PX
        return a, self.f.glyph.bitmap_left / PX, self.f.glyph.bitmap_top / PX, adv

    def measure_slant(self):
        """Measured off the `l` (refs_registry.measure_slant's rule: a single
        bare stem, centers at 30% and 70% of its height)."""
        self.k = XH_ALBO / self.xh
        a, x0, yt, _ = self.mask(self.slant_ch, shear=0.0)
        ys = np.nonzero(a.any(1))[0]; r0, r1 = ys.min(), ys.max()
        c = []
        for fr in (0.30, 0.70):
            r = int(r1 - (r1 - r0) * fr); xs = np.nonzero(a[r])[0]
            c.append(((xs.min() + xs.max()) / 2.0, r))
        # rows grow downward: a stem leaning right has its upper center further right
        return math.degrees(math.atan2(c[1][0] - c[0][0], c[0][1] - c[1][1]))


class G:
    """A glyph mask with row/column run queries in Albo units (y up)."""
    def __init__(self, a, x0, yt, adv):
        self.a, self.x0, self.yt, self.adv = a, x0, yt, adv
        ys = np.nonzero(a.any(1))[0]; xs = np.nonzero(a.any(0))[0]
        self.X0, self.X1 = self.ux(xs.min()), self.ux(xs.max() + 1)
        self.Y1, self.Y0 = self.uy(ys.min()), self.uy(ys.max() + 1)
        self.W, self.H = self.X1 - self.X0, self.Y1 - self.Y0

    def ux(self, c): return self.x0 + c / PX
    def uy(self, r): return self.yt - r / PX
    def col(self, x): return int(round((x - self.x0) * PX))
    def row(self, y): return int(round((self.yt - y) * PX))

    def runs_row(self, y):
        r = self.row(y)
        if not 0 <= r < self.a.shape[0]: return []
        return _runs(self.a[r], self.ux)

    def runs_col(self, x):
        c = self.col(x)
        if not 0 <= c < self.a.shape[1]: return []
        out = []
        for s, e in _idx_runs(self.a[:, c]):
            out.append((self.uy(e), self.uy(s)))      # (bottom, top) in units
        return sorted(out)


def _idx_runs(v):
    d = np.diff(np.concatenate([[0], v.astype(np.int8), [0]]))
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))


def _runs(v, ux):
    return [(ux(s), ux(e)) for s, e in _idx_runs(v)]


def _fit(ys, xs):
    """x = a y + b, and the signed sagitta of a quadratic over the same span."""
    ys, xs = np.asarray(ys), np.asarray(xs)
    a, b = np.polyfit(ys, xs, 1)
    q = np.polyfit(ys, xs, 2); ym = (ys.min() + ys.max()) / 2
    sag = np.polyval(q, ym) - (a * ym + b)
    L = math.hypot(ys.max() - ys.min(), a * (ys.max() - ys.min()))
    return a, b, sag / max(L, 1e-6)


def nstem(face):
    g = G(*face.mask("n"))
    rs = g.runs_row(XH_ALBO * 0.45)
    return rs[0][1] - rs[0][0] if rs else float("nan")


def m_two(g):
    o = dict(w=g.W, top=g.Y1, bot=g.Y0, adv=g.adv)
    H = g.H
    # base: the bottom run in columns 55-80% of the ink width
    bth, btop, bright = [], [], g.X0
    for f in np.linspace(0.55, 0.80, 11):
        rs = g.runs_col(g.X0 + g.W * f)
        if rs: bth.append(rs[0][1] - rs[0][0]); btop.append(rs[0][1])
    o["base"] = float(np.median(bth)); ybt = float(np.median(btop))
    for y in np.linspace(g.Y0 + 1, ybt - 1, 8):
        rs = g.runs_row(y)
        if rs: bright = max(bright, rs[-1][1])
    # the arc: rows above 45% of the height; its right edge's widest row
    best = None
    for y in np.arange(g.Y0 + 0.45 * H, g.Y0 + 0.92 * H, 0.5):
        rs = g.runs_row(y)
        if rs and (best is None or rs[-1][1] > best[0]): best = (rs[-1][1], y)
    arcR, yR = best
    ws = []
    for y in np.arange(yR - 0.02 * H, yR + 0.02 * H, 0.5):
        rs = g.runs_row(y)
        if rs: ws.append(rs[-1][1] - rs[-1][0])
    o["arc"] = float(np.median(ws)); o["arc_w"] = (arcR - g.X0) / g.W
    o["over"] = bright - arcR
    # the crown: the column whose top is highest
    tops = []
    for x in np.arange(g.X0 + 0.2 * g.W, g.X1 - 0.1 * g.W, 0.5):
        rs = g.runs_col(x)
        if rs: tops.append((rs[-1][1], rs[-1][1] - rs[-1][0], x))
    tops.sort(); o["crown"] = float(np.median([t[1] for t in tops[-5:]]))
    o["crown_x"] = (tops[-1][2] - g.X0) / g.W
    # the slash: rows 8-30% of the height above the base's top, leftmost run
    ys, xs, hw = [], [], []
    for y in np.arange(ybt + 0.08 * H, ybt + 0.30 * H, 0.5):
        rs = g.runs_row(y)
        if rs:
            ys.append(y); xs.append((rs[0][0] + rs[0][1]) / 2); hw.append(rs[0][1] - rs[0][0])
    a, b, sag = _fit(ys, xs)
    th = math.atan2(1.0, abs(a))                     # from horizontal
    o["slash"] = float(np.median(hw)) * math.sin(th)
    o["s_ang"] = math.degrees(th)
    o["s_bow"] = -sag if a > 0 else sag
    # the terminal: ink left of 40% of w and above 45% of H
    lowest, tsz = g.Y1, 0.0
    for x in np.arange(g.X0, g.X0 + 0.40 * g.W, 0.5):
        for bot, top in g.runs_col(x):
            if top > g.Y0 + 0.45 * H:
                lowest = min(lowest, max(bot, g.Y0 + 0.45 * H))
                if x < g.X0 + 0.22 * g.W: tsz = max(tsz, top - bot)
    o["t_drop"] = (g.Y1 - lowest) / H; o["t_size"] = tsz
    o["t_left"] = min((r[0] for y in np.arange(g.Y0 + 0.5 * H, g.Y1, 1.0) for r in g.runs_row(y)[:1]), default=g.X0) - g.X0
    return o


def m_seven(g):
    o = dict(w=g.W, top=g.Y1, bot=g.Y0, adv=g.adv)
    H = g.H
    bars = []
    for f in (0.20, 0.35, 0.50):
        rs = g.runs_col(g.X0 + g.W * f)
        bars.append((rs[-1][1] - rs[-1][0], rs[-1][0]) if rs else (float("nan"), g.Y1))
    o["bar_l"], o["bar_m"], o["bar_r"] = bars[0][0], bars[1][0], bars[2][0]
    ybb = bars[1][1]
    low = g.Y1
    for x in np.arange(g.X0, g.X0 + 0.08 * g.W, 0.5):
        for bot, top in g.runs_col(x):
            if top > ybb - 0.35 * H: low = min(low, bot)
    o["beak"] = max(0.0, ybb - low)
    ys, xs, hw = [], [], []
    for y in np.arange(g.Y0 + 0.04 * H, ybb - 0.10 * H, 0.5):
        rs = g.runs_row(y)
        if rs:
            r = rs[-1]; ys.append(y); xs.append((r[0] + r[1]) / 2); hw.append(r[1] - r[0])
    ys, xs, hw = map(np.asarray, (ys, xs, hw))
    a, b, sag = _fit(ys, xs)
    ang_h = math.atan2(1.0, abs(a))
    # local angle per row for the perpendicular width (the italic leg curves)
    loc = np.gradient(xs, ys)
    perp = hw * np.sin(np.arctan2(1.0, np.abs(loc)))
    n = len(ys); q = max(3, n // 4)
    o["leg_b"] = float(np.median(perp[q // 2:q + q // 2]))
    o["leg_t"] = float(np.median(perp[-q:]))
    o["l_ang"] = 90.0 - math.degrees(ang_h)
    o["l_bow"] = sag
    o["foot_x"] = (xs[0] - g.X0) / g.W
    o["flare"] = float(np.median(perp[:3])) / max(o["leg_b"], 1e-6)
    return o


def measure(face, g2, g7):
    ns = nstem(face)
    t = m_two(G(*face.mask(g2))); s = m_seven(G(*face.mask(g7)))
    for d in (t, s):
        for k in list(d):
            if k in ("arc", "crown", "slash", "base", "t_size", "bar_l", "bar_m", "bar_r", "leg_t", "leg_b"):
                d[k + "_n"] = d[k] / ns
    return dict(nstem=ns, slant=face.slant, two=t, seven=s)


def fmt(label, r):
    t, s = r["two"], r["seven"]
    return (f"{label:22} sl {r['slant']:5.1f} n {r['nstem']:5.1f} | 2: w {t['w']:4.0f} top {t['top']:4.0f} bot {t['bot']:4.0f} "
            f"arc {t['arc_n']:.2f} crown {t['crown_n']:.2f} slash {t['slash_n']:.2f}@{t['s_ang']:4.1f} bow {t['s_bow']:+.3f} "
            f"base {t['base_n']:.2f} over {t['over']:4.0f} tdrop {t['t_drop']:.2f} tsz {t['t_size_n']:.2f} arcw {t['arc_w']:.2f} | "
            f"7: w {s['w']:4.0f} top {s['top']:4.0f} bot {s['bot']:5.0f} bar {s['bar_l_n']:.2f}/{s['bar_m_n']:.2f}/{s['bar_r_n']:.2f} "
            f"beak {s['beak']:4.0f} leg {s['leg_t_n']:.2f}->{s['leg_b_n']:.2f} ang {s['l_ang']:4.1f} bow {s['l_bow']:+.3f} "
            f"foot {s['foot_x']:.2f} flare {s['flare']:.2f}")


def albo_faces(d):
    out = []
    for cut, sl in (("Regular", 0.0), ("Italic", 13.0), ("Bold", 0.0), ("BoldItalic", 13.0)):
        p = os.path.join(d, f"Albo-{cut}.ttf")
        if os.path.exists(p): out.append((cut, Face(p, 0, slant=sl)))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs", action="store_true")
    ap.add_argument("--albo", action="append", default=[])
    ap.add_argument("--label", action="append", default=[])
    ap.add_argument("--json")
    A = ap.parse_args()
    res = {}
    if A.refs:
        for lab, p, i, g2, g7, osf, it, *sl in REFS:
            r = measure(Face(p, i, slant_ch=(sl or ["l"])[0]), g2, g7); r.update(oldstyle=osf, italic=it)
            res[lab] = r; print(fmt(lab + ("" if osf else " (lining)"), r))
    for j, d in enumerate(A.albo):
        tag = A.label[j] if j < len(A.label) else os.path.basename(d.rstrip("/"))
        for cut, f in albo_faces(d):
            r = measure(f, "2", "7"); res[f"{tag}/{cut}"] = r; print(fmt(f"{tag}/{cut}", r))
    if A.json: json.dump(res, open(A.json, "w"), indent=1)
