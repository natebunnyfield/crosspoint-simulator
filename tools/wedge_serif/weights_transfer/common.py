"""Shared measurement for the weight-transfer study (2026-09-26).

Owner 2026-09-26: *"interpolated based on my answers what changes would be
applicable to all of albo fonts (thin, black, italic, bold italic, etc)"*.
docs/albo-weights-transfer-2026-09-26.md is the write-up; this module is the
instrument. Everything is in the font's own design units.

    white(a, b)   rsb(a) + kern + lsb(b), kern by HarfBuzz with ligatures off
                  -- gap_measure.py's measure, the one b2_fit.py fits against.
    n_anatomy()   the lowercase n at mid x-height: left stem, counter, right
                  stem, read as horizontal ink runs on a 1-unit raster. A shear
                  maps a horizontal run to a run of the same length, so the
                  italic needs no unshearing.
"""
import json, os, subprocess, sys
import numpy as np
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(WS))
CENSUS = os.path.join(HERE, "census-bigrams.json")
MARKS = set("'.,:;\"-!?")
AGL = {'.': 'period', ',': 'comma', ':': 'colon', ';': 'semicolon', "'": 'quotesingle',
       '"': 'quotedbl', '-': 'hyphen', '!': 'exclam', '?': 'question'}


class Font:
    def __init__(self, path, index=0):
        self.path = path
        self.tt = TTFont(path, fontNumber=index) if path.endswith(".ttc") else TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt["head"].unitsPerEm
        face = hb.Face(hb.Blob.from_file_path(path), index)
        self.hb = hb.Font(face)
        self.order = self.tt.getGlyphOrder()
        self._bounds = {}

    def gname(self, ch):
        return self.cmap.get(ord(ch))

    def bounds(self, name):
        if name not in self._bounds:
            from fontTools.pens.boundsPen import BoundsPen
            bp = BoundsPen(self.gs)
            self.gs[name].draw(bp)
            self._bounds[name] = bp.bounds
        return self._bounds[name]

    def shape(self, s):
        buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"liga": False, "clig": False, "dlig": False})
        return buf.glyph_infos, buf.glyph_positions

    def white(self, a, b):
        inf, pos = self.shape(a + b)
        if len(inf) != 2:
            return None
        n0, n1 = self.order[inf[0].codepoint], self.order[inf[1].codepoint]
        natural = self.hb.get_glyph_h_advance(inf[0].codepoint)
        kern = pos[0].x_advance - natural + pos[1].x_offset
        b0, b1 = self.bounds(n0), self.bounds(n1)
        if b0 is None or b1 is None:
            return None
        return (natural - b0[2]) + kern + b1[0]

    def xheight(self):
        return self.bounds(self.gname("x"))[3]

    def runs(self, ch, y):
        """Ink runs [(x0, x1)] of glyph ch on the row at height y, 1 unit/px."""
        name = self.gname(ch)
        b = self.bounds(name)
        x0 = int(b[0]) - 4; W = int(b[2] - b[0]) + 8
        pen = FreeTypePen(self.gs)
        self.gs[name].draw(TransformPen(pen, (1, 0, 0, 1, -x0, -int(y))))
        a = pen.array(width=W, height=3, transform=(1, 0, 0, 1, 0, 1)) > 0.5
        row = a[1]
        out, x = [], 0
        while x < W:
            if row[x]:
                s = x
                while x < W and row[x]:
                    x += 1
                out.append((s + x0, x + x0))
            x += 1
        return out

    def n_anatomy(self):
        xh = self.xheight()
        best = None
        for f in (0.40, 0.45, 0.50, 0.55):
            r = self.runs("n", xh * f)
            if len(r) >= 2:
                best = r; break
        if not best:
            return None
        (a0, a1), (b0, b1) = best[0], best[-1]
        hm = self.tt["hmtx"][self.gname("n")]
        bb = self.bounds(self.gname("n"))
        return dict(stem=a1 - a0, counter=b0 - a1, stem_r=b1 - b0, xh=xh,
                    lsb=bb[0], rsb=hm[0] - bb[2])


def census(min_n=0):
    return [(p, n) for p, n in json.load(open(CENSUS))["pairs"] if n >= min_n]


def head_json(rel):
    """A file as committed at HEAD -- the working copy of outlines/ belongs to
    another agent mid-round, so the shipped state is read from git."""
    return json.loads(subprocess.check_output(["git", "-C", REPO, "show", f"HEAD:{rel}"]))
