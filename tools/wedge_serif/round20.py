"""Round 20: the non-lowercase set matched to the garalde references the
way the lowercase was matched to the S tier. Owner 2026-09-12: 'match
uppercase to garamond sabon etc. do every step that lowercase went through
for the non-lowercase characters and punctuation.' No Garamond or Sabon is
on disk; the references are Dante, Van den Keere, Hoefler Text and Doves
(medians in fonts/garalde_caps.json, measured at a 1000 px em).

Steps, mirroring the lowercase: proportions (cap height 0.941 asc, cap stem
1.137 lowercase, old-style figure boxes), per-glyph WIDTHS solved to the
references' ink widths, fitting (cap sidebearings from the references' H:
0.042 cap heights per straight side, by side fraction), then the same
construction: linear pen, counterpunches, bowls to stems, stems into
curves."""
import json, os, sys, base64, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round12, round17, round19, latin, alphabet2 as A
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

REF = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "garalde_caps.json")))["median"] if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "garalde_caps.json")) else None
SEED, EVERY, AMP = round19.SEED, round19.EVERY, round19.AMP
CHARS, GLYPH_ORDER, gname = round19.CHARS, round19.GLYPH_ORDER, round19.gname

def draw(ch, p, glyphs_all, pen_fn, post):
    c = round19.ctx_with_cut(p)
    if ch.isdigit():
        top, bot = latin.FIG_BOX[ch]; latin._FIG[0] = (top - bot) * latin.capH(c)
    else:
        latin._FIG[0] = None
    A.outline = pen_fn
    try: polys = glyphs_all[ch](c)
    finally: A.outline = round12.ORIG
    polys = round12.flatten(polys)
    if ch.isdigit():
        dy = latin.FIG_BOX[ch][1] * latin.capH(c)
        polys = [type(poly)([(x, y + dy) for x, y in poly]) for poly in polys]   # keep Hole as Hole
    if post: polys = post(polys, c)
    return round17.orient_with_holes(polys), c

def solve_widths(p, glyphs_all, pen_fn):
    """Three passes: draw, measure the ink width, scale the glyph's width
    multiplier toward the reference's width x cap height."""
    c = round19.ctx_with_cut(p); C = latin.capH(c)
    for _ in range(3):
        for ch in CHARS:
            if not (ch.isupper() or ch.isdigit()) or ch == 'I' or ch == '1' or ch not in REF: continue
            polys, _c = draw(ch, p, glyphs_all, pen_fn, None)
            xs = [x for poly in polys for (x, y) in poly]; drawn = max(xs) - min(xs)
            target = REF[ch]["w"] * C
            if drawn > 1: latin.W[ch] = max(0.7, min(1.45, latin.W.get(ch, 1.0) * (target / drawn) ** 0.85))
    return dict(latin.W)

def build(out_dir, name="Fjord", style="Regular"):
    p = dict(round19.DESIGN)
    saved_glyphs = dict(A.GLYPHS); saved_arch = A._arch
    A.GLYPHS.update(round17.cp_glyphs(SEED, EVERY, AMP, 1.0, None)); round17.patch_arch(1.0)
    glyphs_all = round19.all_glyphs()
    pen_fn = round17.pen_linear(SEED, EVERY, AMP); post = round17.Cut(SEED, 4, 3.0, 2.0, hand=False)
    try:
        solved = solve_widths(p, glyphs_all, round12.ORIG)
        c = round19.ctx_with_cut(p); C = latin.capH(c)
        fb = FontBuilder(1000, isTTF=True); fb.setupGlyphOrder(GLYPH_ORDER)
        fb.setupCharacterMap({ord(ch): gname(ch) for ch in CHARS} | {32: 'space'})
        glyphs, metrics = {}, {}
        capbear = REF["Hbear"] / 2 * C if REF else A.bearing(c, 'straight')
        for ch in CHARS:
            polys, cc = draw(ch, p, glyphs_all, pen_fn, post)
            isCap = ch.isupper() or ch.isdigit()
            top = C if isCap else c["xh"]
            band = [x for poly in polys for (x, y) in poly if -c["over"] <= y <= top + c["over"]]
            xs = [x for poly in polys for (x, y) in poly]
            l, r = (min(band), max(band)) if band else (min(xs), max(xs))
            lt, rt = round19.SIDES.get(ch, ('straight', 'straight'))
            # owner 2026-09-12: caps +34 per mille from the spacing page (+17
            # each side), then "reduce lowercase letter spacing to match
            # uppercase's": one basis for both cases, the references' H bearing
            lsb = capbear * A.SIDE_FRACTION[lt] + 17; rsb = capbear * A.SIDE_FRACTION[rt] + 17
            adv = lsb + (r - l) + rsb; dx = lsb - l
            pen = TTGlyphPen(None)
            for poly in polys:
                pts = [(round(x + dx), round(y)) for x, y in poly]
                pen.moveTo(pts[0])
                for q in pts[1:]: pen.lineTo(q)
                pen.closePath()
            glyphs[gname(ch)] = pen.glyph(); metrics[gname(ch)] = (int(round(adv)), int(round(min(xs) + dx)))
        pen = TTGlyphPen(None); pen.moveTo((50, 0)); pen.lineTo((50, 700)); pen.lineTo((450, 700)); pen.lineTo((450, 0)); pen.closePath()
        glyphs['.notdef'] = pen.glyph(); metrics['.notdef'] = (500, 50)
        # owner 2026-09-12: word-spacing -110 per mille (for capitals; applied to the one space)
        glyphs['space'] = TTGlyphPen(None).glyph(); metrics['space'] = (int(A.n_counter(c) * 1.7) - 110, 0)
        fb.setupGlyf(glyphs); fb.setupHorizontalMetrics(metrics)
        fb.setupHorizontalHeader(ascent=900, descent=-300)
        fb.setupNameTable(dict(familyName=name, styleName=style, fullName=f"{name} {style}", psName=f"{name}-{style}", uniqueFontIdentifier=f"{name};{style};2026-09-12"))
        fb.setupOS2(sTypoAscender=900, sTypoDescender=-300, usWinAscent=900, usWinDescent=300, sxHeight=int(p["xh"]), sCapHeight=int(C))
        fb.setupPost()
        path = os.path.join(out_dir, f"{name}-{style}.ttf"); fb.save(path); return path, solved
    finally:
        A.GLYPHS.clear(); A.GLYPHS.update(saved_glyphs); A._arch = saved_arch; latin.W.clear(); latin._FIG[0] = None

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    os.makedirs(out, exist_ok=True)
    path, solved = build(out); TTFont(path)
    html_ = round19.page(path).replace("Round 19. The complete Latin set in one file, Fjord-Regular.ttf, on the k6 construction: capitals, lowercase, lining figures, text punctuation, quotes and dashes.", "Round 20. Capitals, figures and marks matched to the garalde references (Dante, Van den Keere, Hoefler Text, Doves) the way the lowercase was matched: widths solved per letter, cap stems at 1.14 of the lowercase, capitals fitted at the references' bearings, old-style figures in their measured boxes.")
    open(os.path.join(out, "fjord-specimen.html"), "w").write(html_)
    print("ok", os.path.getsize(path) // 1024, "KB; width multipliers:", {k: round(v, 2) for k, v in sorted(solved.items())})
