#!/usr/bin/env python3
"""HT Letterspacer, run headless on a TTF: a line-for-line port of its engine.

SOURCE. github.com/huertatipografica/HTLetterspacer (GPL-3.0), commit of
2026-08-17, HTLetterspacer.glyphsPlugin/Contents/Resources/htls/engine.py --
itself "a faithful port of the standalone script's HTLetterspacerLib". The
geometry below keeps its functions (totalMarginList, zoneMargins, setDepth,
diagonize, closeOpenCounters, deslant, calculateSBValue, setSpace) and their
arithmetic, including the math.ceil calls. Only the Glyphs API is replaced:

  * layer.calculateIntersectionsStartPoint_endPoint_  -> exact crossings of a
    horizontal line with the outline, flattened at 32 steps per curve; the
    script takes result[1] and result[-2], i.e. the first and last crossing.
  * layer.bounds -> the outline's bbox (BoundsPen).
  * master.italicAngle -> -post.italicAngle (Glyphs counts a right lean
    positive; OpenType negative). xHeight -> OS/2 sxHeight.
  * rules: HTLS's own default_rules() (config.py): uppercase letters use the
    H as reference zone at 125% area, lowercase the x at 100%; anything else
    (the marks) matches no rule and is its own reference at 100%.
  * Glyphs measures an ITALIC layer's LSB/RSB on the de-slanted outline
    (about x-height/2), so the engine's newL/newR are de-slanted values; they
    are converted back to bbox sidebearings for the white measure.

HTLS sets sidebearings only. It writes no kerning, so its white for a pair is
rsb'(a) + lsb'(b).

    $VENV/bin/python htls_port.py [--area 400] [--depth 15] [--fontset 0920|r397|both]
"""
import argparse, math, os, sys, time
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

paramFreq = 5
DEFAULT_MARGIN = 1e6


class P:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x, self.y = x, y

    def __iter__(self):
        return iter((self.x, self.y))

    def __getitem__(self, i):
        return (self.x, self.y)[i]


class FlatPen(BasePen):
    def __init__(self, gs, steps=32):
        super().__init__(gs); self.contours = []; self.cur = None; self.steps = steps

    def _moveTo(self, pt):
        self.cur = [pt]; self.contours.append(self.cur)

    def _lineTo(self, pt):
        self.cur.append(pt)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, self.steps + 1)[1:]:
            u = 1 - t
            self.cur.append((u**3 * p0[0] + 3 * u*u*t * p1[0] + 3 * u*t*t * p2[0] + t**3 * p3[0],
                             u**3 * p0[1] + 3 * u*u*t * p1[1] + 3 * u*t*t * p2[1] + t**3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for t in np.linspace(0, 1, self.steps + 1)[1:]:
            u = 1 - t
            self.cur.append((u*u * p0[0] + 2 * u*t * p1[0] + t*t * p2[0],
                             u*u * p0[1] + 2 * u*t * p1[1] + t*t * p2[1]))

    def _closePath(self):
        pass


class Layer:
    def __init__(self, font, name, contours=None, width=None):
        if contours is None:
            gs = font.getGlyphSet()
            pen = FlatPen(gs); gs[name].draw(pen)
            contours = pen.contours
        segs = []
        pts = []
        for c in contours:
            c = [tuple(map(float, q)) for q in c]
            pts += c
            for i in range(len(c)):
                segs.append((c[i - 1], c[i]))
        self.segs = np.array(segs) if segs else np.zeros((0, 2, 2))
        self.pts = np.array(pts) if pts else np.zeros((0, 2))
        self.bounds = (float(self.pts[:, 0].min()), float(self.pts[:, 1].min()),
                       float(self.pts[:, 0].max()), float(self.pts[:, 1].max()))
        self.width = width if font is None else font["hmtx"][name][0]

    def crossings(self, y):
        s = self.segs
        if not len(s):
            return []
        y0, y1 = s[:, 0, 1], s[:, 1, 1]
        m = ((y0 <= y) & (y1 > y)) | ((y1 <= y) & (y0 > y))
        a = s[m]
        t = (y - a[:, 0, 1]) / (a[:, 1, 1] - a[:, 0, 1])
        return sorted(a[:, 0, 0] + t * (a[:, 1, 0] - a[:, 0, 0]))


def area(points):
    s = 0
    for ii in range(-1, len(points) - 1):
        s = s + (points[ii].x * points[ii + 1].y - points[ii + 1].x * points[ii].y)
    return abs(s) * 0.5


def getMargins(layer, y):
    xs = layer.crossings(y)
    if len(xs) < 1:          # Glyphs' result has 2 extra endpoints: count <= 2 -> none
        return (None, None)
    return (xs[0], xs[-1])


def totalMarginList(layer, minY, maxY, angle, minYref, maxYref, freq=paramFreq):
    y = minY
    listL, listR = [], []
    slantPosL, slantPosR = DEFAULT_MARGIN, -DEFAULT_MARGIN
    result = False
    while y <= maxY:
        lpos, rpos = getMargins(layer, y)
        if lpos is not None:
            listL.append(P(lpos, y))
            if minYref <= y <= maxYref:
                result = True
        else:
            listL.append(P(slantPosL, y))
        if rpos is not None:
            listR.append(P(rpos, y))
            if minYref <= y <= maxYref:
                result = True
        else:
            listR.append(P(slantPosR, y))
        y += freq
    if result:
        return listL, listR
    return False, False


def zoneMargins(lMargins, rMargins, minY, maxY):
    return ([x for x in lMargins if minY <= x.y <= maxY], [x for x in rMargins if minY <= x.y <= maxY])


class Engine:
    def __init__(self, font, area_param=400.0, depth=15.0, over=0.0):
        self.font = font
        self.upm = font["head"].unitsPerEm
        self.angle = -font["post"].italicAngle
        self.xHeight = font["OS/2"].sxHeight
        self.paramArea, self.paramDepth, self.paramOver = area_param, depth, over
        self.paramFreq = paramFreq
        self.cmap = font.getBestCmap()
        self._layers = {}

    def layer(self, ch):
        n = self.cmap[ord(ch)]
        if n not in self._layers:
            self._layers[n] = Layer(self.font, n)
        return self._layers[n]

    # --- verbatim geometry ---
    def overshoot(self):
        return self.xHeight * self.paramOver / 100

    def maxPoints(self, points, minY, maxY):
        L = sorted(points[0], key=lambda tup: tup[0])
        R = sorted(points[1], key=lambda tup: tup[0])
        return P(*L[0]), P(*R[-1])

    def processMargins(self, lMargin, rMargin, lExtreme, rExtreme):
        lMargin, rMargin = self.setDepth(lMargin, rMargin, lExtreme, rExtreme)
        lMargin, rMargin = self.diagonize(lMargin, rMargin)
        lMargin = self.closeOpenCounters(lMargin, lExtreme)
        rMargin = self.closeOpenCounters(rMargin, rExtreme)
        return lMargin, rMargin

    def setDepth(self, marginsL, marginsR, lExtreme, rExtreme):
        depth = self.xHeight * self.effectiveDepth / 100
        maxdepth = lExtreme.x + depth
        mindepth = rExtreme.x - depth
        marginsL = [P(min(p.x, maxdepth), p.y) for p in marginsL]
        marginsR = [P(max(p.x, mindepth), p.y) for p in marginsR]
        y = marginsL[0].y - self.paramFreq
        while y > self.minYref:
            marginsL.insert(0, P(maxdepth, y)); marginsR.insert(0, P(mindepth, y)); y -= self.paramFreq
        y = marginsL[-1].y + self.paramFreq
        while y < self.maxYref:
            marginsL.append(P(maxdepth, y)); marginsR.append(P(mindepth, y)); y += self.paramFreq
        return marginsL, marginsR

    def diagonize(self, marginsL, marginsR):
        ystep = abs(marginsL[0].y - marginsL[1].y)
        for i in range(len(marginsL) - 1):
            if marginsL[i + 1].x - marginsL[i].x > ystep:
                marginsL[i + 1].x = marginsL[i].x + ystep
            if marginsR[i + 1].x - marginsR[i].x < -ystep:
                marginsR[i + 1].x = marginsR[i].x - ystep
        for i in reversed(range(len(marginsL) - 1)):
            if marginsL[i].x - marginsL[i + 1].x > ystep:
                marginsL[i].x = marginsL[i + 1].x + ystep
            if marginsR[i].x - marginsR[i + 1].x < -ystep:
                marginsR[i].x = marginsR[i + 1].x - ystep
        return marginsL, marginsR

    def closeOpenCounters(self, margin, extreme):
        margin.insert(0, P(extreme.x, self.minYref))
        margin.append(P(extreme.x, self.maxYref))
        return margin

    def deslant(self, margin):
        mline = self.xHeight / 2
        return [P(p.x - (p.y - mline) * math.tan(math.radians(self.angle)), p.y) for p in margin]

    def calculateSBValue(self, polygon):
        amplitudeY = self.maxYref - self.minYref
        areaUPM = self.effectiveArea * ((self.upm / 1000) ** 2)
        whiteArea = areaUPM * 100
        propArea = (amplitudeY * whiteArea) / self.xHeight
        valor = propArea - area(polygon)
        return valor / amplitudeY

    def setSpace(self, layer, referenceLayer):
        overshoot = self.overshoot()
        self.minYref = referenceLayer.bounds[1] - overshoot
        self.maxYref = referenceLayer.bounds[3] + overshoot
        self.minY, self.maxY = layer.bounds[1], layer.bounds[3]
        lT, rT = totalMarginList(layer, self.minY, self.maxY, self.angle, self.minYref, self.maxYref, self.paramFreq)
        if not lT and not rT:
            return None
        lZ, rZ = zoneMargins(lT, rT, self.minYref, self.maxYref)
        if self.angle:
            lZ, rZ, lT, rT = self.deslant(lZ), self.deslant(rZ), self.deslant(lT), self.deslant(rT)
        lFull, rFull = self.maxPoints([lT, rT], self.minY, self.maxY)
        lExt, rExt = self.maxPoints([lZ, rZ], self.minYref, self.maxYref)
        lPoly, rPoly = self.processMargins(lZ, rZ, lExt, rExt)
        distanceL = math.ceil(lExt.x - lFull.x)
        distanceR = math.ceil(rFull.x - rExt.x)
        newL = math.ceil(0 - distanceL + self.calculateSBValue(lPoly))
        newR = math.ceil(0 - distanceR + self.calculateSBValue(rPoly))
        return newL, newR

    # --- rules: HTLS default_rules() ---
    def space(self, ch):
        lay = self.layer(ch)
        if ch.isupper():
            ref, factor = self.layer("H"), 1.25
        elif ch.islower():
            ref, factor = self.layer("x"), 1.0
        else:
            ref, factor = lay, 1.0
        self.effectiveArea = self.paramArea * factor
        self.effectiveDepth = self.paramDepth
        r = self.setSpace(lay, ref)
        if r is None:
            return None
        newL, newR = r
        # Glyphs: italic sidebearings are measured on the de-slanted outline.
        t = math.tan(math.radians(self.angle)); ml = self.xHeight / 2
        ds = lay.pts[:, 0] - (lay.pts[:, 1] - ml) * t
        xmin, xmax = lay.bounds[0], lay.bounds[2]
        lsb = newL + (xmin - ds.min())
        rsb = newR + (ds.max() - xmax)
        return float(lsb), float(rsb)


def run(fontset, area_param, depth):
    T = C.Truth()
    out, meta = {}, {}
    for s in C.STYLES:
        eng = Engine(TTFont(C.FONTSETS[fontset][s]), area_param, depth)
        chars = sorted({c for p in T.P[s] for c in p})
        sb = {c: eng.space(c) for c in chars}
        bad = [c for c, v in sb.items() if v is None]
        if bad:
            raise SystemExit(f"{s}: no spacing for {bad}")
        out[s] = {p: sb[p[0]][1] + sb[p[1]][0] for p in T.P[s]}
        meta[s] = {c: [round(v[0], 1), round(v[1], 1)] for c, v in sb.items()}
    return out, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--area", type=float, default=400.0)
    ap.add_argument("--depth", type=float, default=15.0)
    ap.add_argument("--fontset", default="both")
    a = ap.parse_args()
    for fs in (["0920", "r397"] if a.fontset == "both" else [a.fontset]):
        t0 = time.time()
        white, sb = run(fs, a.area, a.depth)
        name = "htls" if (a.area, a.depth) == (400.0, 15.0) else f"htls-a{a.area:g}-d{a.depth:g}"
        path = C.save_preds(name, fs, white, {"area": a.area, "depth": a.depth, "sidebearings": sb,
                                              "seconds": round(time.time() - t0, 2)})
        print(f"{fs}: {time.time() - t0:.1f} s -> {path}")


if __name__ == "__main__":
    main()
