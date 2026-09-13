"""Build Albo-Medium.ttf (Albo-Regular until round 83; Fjord until round 58) from the designed outlines: draw, extract the
contours (exteriors ccw, counters cw), apply the linear cut, fit with the
round-20 rule, write the TrueType and the round-19 specimen.

    cd tools/wedge_serif && PYTHON_GIL=0 python3 -m outlines.build <out_dir> [--nocut]
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import round19, round20, latin, alphabet2 as A
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from . import geom, pen, cut
from . import primitives as PR
from .glyphs import GLYPHS

CHARS, GLYPH_ORDER, gname = round19.CHARS, round19.GLYPH_ORDER, round19.gname
SIDES = round19.SIDES
REF = round20.REF
C = pen.CAP
INK_SPREAD = 1.2

def ctx(ch, W=None):
    """Per-glyph context: the fixed proportions, the lowercase width factor
    (baked into every lowercase x radius and width through c['wf']), and
    the capitals' solved width multipliers."""
    return dict(xh=pen.XH, asc=pen.ASC, desc=pen.DESC, s=pen.S, cs=pen.CS, cap=C, over=pen.OVER, arch_over=pen.ARCH_OVER,
                wf=pen.WF if ch.islower() else 1.0, W=W or {}, ch=ch)

def draw(ch, W=None):
    """The glyph's ink as one shapely geometry (figures shifted into their
    old-style box)."""
    c = ctx(ch, W)
    if ch.isdigit():
        top, bot = latin.FIG_BOX[ch]; c["figH"] = (top - bot) * C
    PR.begin_glyph(ch)   # the life: deterministic per-glyph perturbation of wedges and rings
    g = GLYPHS[ch](c)
    # the record's Cut post-op grew every polygon 1.2 units (offset_naive,
    # grow 3.0 x 0.4) to re-close the joins it had opened; the joins are
    # real now, but the 1.2 units were part of the shipped weight (the l's
    # stem measured 81, not the pen's 77), so the same ink spread is kept.
    g = g.buffer(INK_SPREAD, join_style=2)
    if ch.isdigit():
        import shapely.affinity
        g = shapely.affinity.translate(g, 0, latin.FIG_BOX[ch][1] * C)
    return g

def solve_widths(passes=3):
    """Capitals and figures: scale each glyph's width multiplier so its ink
    width lands on the references' median (round 20's rule, same clamps)."""
    W = {}
    for _ in range(passes):
        for ch in CHARS:
            if not (ch.isupper() or ch.isdigit()) or ch in ('I', '1') or ch not in REF or ch not in GLYPHS: continue
            g = draw(ch, W); x0, y0, x1, y1 = geom.bbox(g); drawn = x1 - x0
            target = REF[ch]["w"] * C * pen.WIDTH   # the wdth axis scales the references' widths
            if drawn > 1: W[ch] = max(0.7, min(1.45, W.get(ch, 1.0) * (target / drawn) ** 0.85))
    return W

def fit(ch, conts, c):
    """Round 20's bearing rule: ink measured in the x-height band (cap band
    for capitals and figures); the g and every non-letter on their full
    extent; bearing per side = capbear x SIDE_FRACTION + 17."""
    isCap = ch.isupper() or ch.isdigit(); top = C if isCap else pen.XH
    xs_all = [x for pts, _ in conts for x, y in pts]
    band = [x for pts, _ in conts for x, y in pts if -pen.OVER <= y <= top + pen.OVER]
    l, r = (min(band), max(band)) if band else (min(xs_all), max(xs_all))
    if ch == 'g' or not ch.isalpha(): l, r = min(xs_all), max(xs_all)
    lt, rt = SIDES.get(ch, ('straight', 'straight'))
    capbear = REF["Hbear"] / 2 * C * pen.WIDTH   # the fitting follows the width axis
    lsb = capbear * A.SIDE_FRACTION[lt] + 17; rsb = capbear * A.SIDE_FRACTION[rt] + 17
    adv = lsb + (r - l) + rsb; dx = lsb - l
    return adv, dx, min(xs_all) + dx

WEIGHT_CLASS = {"Thin": 100, "ExtraLight": 200, "Light": 300, "Regular": 400, "Medium": 500, "SemiBold": 600, "Bold": 700}

def build(out_dir, name="Albo", style="Medium", do_cut=True, only=None, dump=None):   # owner 2026-09-13, round 83: today's cut is the 500, "Rename to Medium"; the calibrated 400 is Albo-Regular
    os.makedirs(out_dir, exist_ok=True)
    W = solve_widths()
    cutter = cut.Cutter(73, 4)
    fb = FontBuilder(1000, isTTF=True); fb.setupGlyphOrder(GLYPH_ORDER)
    fb.setupCharacterMap({ord(ch): gname(ch) for ch in CHARS} | {32: 'space'})
    glyphs, metrics, report = {}, {}, {}
    for ch in CHARS:
        c = ctx(ch, W)
        if ch in GLYPHS and (only is None or ch in only):
            g = draw(ch, W); dense = geom.contours(g)
            # round 62: the cut is an amount on the DENSE point set (cut.blend):
            # every point kept, the dropped ones moved onto their chords -- the
            # same construction the variable font's masters use
            phases = [cutter.phase() for _ in dense]
            amount = pen.CUT_AMOUNT if do_cut else 0.0
            conts = [(cut.blend(pts, ph, amount), hole) for (pts, hole), ph in zip(dense, phases)]
        else:
            conts = []; dense = []; phases = []
        pen_ = TTGlyphPen(None)
        if conts:
            adv, dx, lsb_ink = fit(ch, conts, c)
            for pts, hole in conts:
                q = [(round(x + dx), round(y)) for x, y in pts]
                pen_.moveTo(q[0])
                for p in q[1:]: pen_.lineTo(p)
                pen_.closePath()
            report[ch] = dict(adv=adv, contours=len(conts), verts=sum(len(p) for p, _ in conts), lsb=lsb_ink, phases=phases,
                              pts=[([(x + dx, y) for x, y in pts], hole) for pts, hole in dense])   # the DENSE contours, translated by the cut's fit: the variable builder's master input
        else:
            adv, lsb_ink = 300, 0
        glyphs[gname(ch)] = pen_.glyph(); metrics[gname(ch)] = (int(round(adv)), int(round(lsb_ink)))
    p = TTGlyphPen(None); p.moveTo((50, 0)); p.lineTo((50, 700)); p.lineTo((450, 700)); p.lineTo((450, 0)); p.closePath()
    glyphs['.notdef'] = p.glyph(); metrics['.notdef'] = (500, 50)
    # the word space: 1.7 n-counters minus 110 (the owner's readout), on the
    # UNCONDENSED n counter as round 20 computed it (the space's context was
    # never the lowercase one), so it stays the record's 353
    glyphs['space'] = TTGlyphPen(None).glyph(); metrics['space'] = (int(pen.N_COUNTER_FULL * 1.7) - 110, 0)
    fb.setupGlyf(glyphs); fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=900, descent=-300)
    fb.setupNameTable(dict(familyName=name, styleName=style, fullName=f"{name} {style}", psName=f"{name}-{style}", uniqueFontIdentifier=f"{name};{style};2026-09-13"))
    fb.setupOS2(sTypoAscender=900, sTypoDescender=-300, usWinAscent=900, usWinDescent=300, sxHeight=int(pen.XH), sCapHeight=int(C), usWeightClass=WEIGHT_CLASS.get(style, 400))
    fb.setupPost()
    path = os.path.join(out_dir, f"{name}-{style}.ttf"); fb.save(path); TTFont(path)
    if dump:
        import json
        json.dump(dict(space=metrics['space'][0], W=W, params=dict(stem=pen.S, xh=pen.XH, asc=pen.ASC, desc=pen.DESC, contrast=pen.CONTRAST, width=pen.WIDTH, serif=pen.SERIF, cut=pen.CUT_AMOUNT),
                       glyphs={ch: dict(adv=r['adv'], lsb=r['lsb'], phases=r['phases'], contours=[(pts, hole) for pts, hole in r['pts']]) for ch, r in report.items()}), open(dump, 'w'))
    return path, W, report

if __name__ == "__main__":
    out = sys.argv[1]; do_cut = "--nocut" not in sys.argv
    style = sys.argv[sys.argv.index("--style") + 1] if "--style" in sys.argv else "Medium"
    dump = sys.argv[sys.argv.index("--dump") + 1] if "--dump" in sys.argv else None
    path, W, rep = build(out, style=style, do_cut=do_cut, dump=dump)
    if style != "Medium": print("ok", path); sys.exit(0)
    open(os.path.join(out, "albo-specimen.html"), "w").write(round19.page(path).replace("Round 19. The complete Latin set in one file, Fjord-Regular.ttf, on the k6 construction: capitals, lowercase, lining figures, text punctuation, quotes and dashes.", "Albo (named 2026-09-13, round 58; Fjord until then): all 93 glyphs as designed outlines under the standing rulings, the bowls on the Albertus-like firm profile he picked, the wedge family kept, the linear cut applied last. Design defaults: weight " + f"{pen.S:g}, contrast {pen.CONTRAST:g}, ascender {pen.ASC:g}, descender {pen.DESC:g}, width {pen.WIDTH * 100:g}, cut {pen.CUT_AMOUNT:g}, x-height {pen.XH:g}, serif {pen.SERIF * 100:g}.").replace("Fjord-Regular.ttf", "Albo-Medium.ttf").replace("Fjord", "Albo"))
    print("ok", path, len(rep), "glyphs drawn of", len(CHARS), "; caps W:", {k: round(v, 2) for k, v in sorted(W.items())})
