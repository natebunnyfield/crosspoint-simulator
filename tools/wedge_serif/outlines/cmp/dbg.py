"""Rasterize a glyph's geometry (or any list of shapely solids) straight
from the drawing, at a scale, with rules -- the debugging LOOK before the
font exists.  python3 -m outlines.cmp.dbg <chars> <out.png> [scale]"""
import sys, os
from PIL import Image, ImageDraw
from .. import geom, pen, build
from ..glyphs import GLYPHS

import os
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.boundsPen import BoundsPen
R = os.path.expanduser('~/src/crosspoint-reader/lib/EpdFont/local_fonts')
REFS = {'Garamond': '/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/414829eb-ff28-4317-bac9-e346395042d3/scratchpad/wedge/ref/EBGaramond-400.ttf',
        'VdK': f'{R}/VandenKeere-Regular.otf', 'Dante': f'{R}/DanteMT-Regular.ttf', 'Edgar': f'{R}/Edgar-Regular.ttf'}
_cache = {}
def ref_glyph(ch, face='Garamond', at_x=0.0):
    """The reference face's glyph as a shapely geometry scaled to Fjord's
    x-height (measured from its x), its left ink edge at at_x."""
    if face not in _cache:
        f = TTFont(REFS[face]); gs = f.getGlyphSet(); cm = f.getBestCmap()
        bp = BoundsPen(gs); gs[cm[ord('x')]].draw(bp); _cache[face] = (gs, cm, pen.XH / bp.bounds[3])
    gs, cm, sc = _cache[face]
    gn = cm.get(ord(ch))
    if gn is None: return None
    from fontTools.pens.basePen import BasePen
    class Flat(BasePen):
        def __init__(s): super().__init__(gs); s.cs = []; s.cur = None
        def _moveTo(s, p): s.cur = [p]
        def _lineTo(s, p): s.cur.append(p)
        def _curveToOne(s, c1, c2, p): s.cur.extend(geom.cubic(s.cur[-1], c1, c2, p, 6)[1:])
        def _qCurveToOne(s, c, p): s.cur.extend(geom.quad(s.cur[-1], c, p, 6)[1:])
        def _closePath(s): s.cs.append(s.cur); s.cur = None
        def _endPath(s): s._closePath()
    fp = Flat(); gs[gn].draw(fp)
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    polys = [Polygon([(x * sc, y * sc) for x, y in c]) for c in fp.cs if len(c) >= 3]
    polys = [shapely.make_valid(p) for p in polys]
    outs = [p for p in polys if True]
    # nonzero-ish: even-odd by symmetric difference of nested contours
    g = outs[0]
    for p in outs[1:]: g = g.symmetric_difference(p)
    b = g.bounds
    import shapely.affinity as aff
    return aff.translate(g, at_x - b[0], 0)

import shapely
def raster(geoms, out, scale=0.5, pad=40, colors=None, rules=True, labels=None, refs=()):
    polys = []
    for g in geoms:
        polys.extend(geom.contours(g, min_area=1))
    xs = [x for pts, _ in polys for x, y in pts] or [0, 100]; ys = [y for pts, _ in polys for x, y in pts] or [0, 100]
    x0, x1 = min(xs) - pad, max(xs) + pad; y0, y1 = min(ys) - pad, max(ys) + pad
    y0 = min(y0, -pen.DESC - 20); y1 = max(y1, pen.ASC + 40)
    W, H = int((x1 - x0) * scale), int((y1 - y0) * scale)
    im = Image.new('RGB', (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    T = lambda p: ((p[0] - x0) * scale, (y1 - p[1]) * scale)
    if rules:
        for yy, col in ((0, (150, 150, 150)), (pen.XH, (190, 190, 190)), (pen.CAP, (215, 215, 215)), (pen.ASC, (225, 225, 225)), (-pen.DESC, (225, 225, 225))):
            d.line([T((x0, yy)), T((x1, yy))], fill=col)
    for g in refs:
        for pts, hole in geom.contours(g, min_area=1):
            d.polygon([T(p) for p in pts], fill=(255, 255, 255) if hole else (255, 200, 200))
    import numpy as np
    base = np.array(im)
    for i, g in enumerate(geoms):
        col = np.array(colors[i] if colors else (0, 0, 0), dtype=np.uint8)
        acc = np.zeros((H, W), dtype=bool)
        for pts, hole in geom.contours(g, min_area=1):
            m = Image.new('1', (W, H), 0); ImageDraw.Draw(m).polygon([T(p) for p in pts], fill=1)
            acc ^= np.array(m, dtype=bool)          # even-odd over the contour set: exact for nested holes
        base[acc] = col
    im = Image.fromarray(base); im.save(out); return im

if __name__ == '__main__':
    chars, out = sys.argv[1], sys.argv[2]; scale = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    import shapely.affinity as aff
    face = sys.argv[4] if len(sys.argv) > 4 else None
    gs = []; rs = []; x = 0
    for ch in chars:
        g = build.draw(ch); b = geom.bbox(g)
        gs.append(aff.translate(g, x - b[0] + 30, 0))
        if face:
            r = ref_glyph(ch, face, x + 30)
            if r is not None: rs.append(r)
        x += (b[2] - b[0]) + 90
    raster(gs, out, scale, refs=rs); print(out)
