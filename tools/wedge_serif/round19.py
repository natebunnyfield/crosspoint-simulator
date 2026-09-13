"""Round 19: the complete Latin set as one TrueType, on the k6 construction
(round 17/18: linear pen, counterpunched bowls, bowls kept to stems, stems
overlapping their curves). Owner 2026-09-12: 'let's make a complete latin
alphabet with punctuation and address the many issues that need
addressing', and 'be sure that the bowl like g is clear of overhanging
shapes from outside'. A-Z a-z 0-9, text punctuation, quotes, dashes.
"""
import math, os, random, sys, zipfile, html, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round12, round15, round17, latin, alphabet2 as A
from round12 import V, signed_area
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools import agl

SEED, EVERY, AMP = 73, 4, 0.0          # k6: pure decimation, no jitter
import round10
DESIGN = dict(round10.steps()[-1][2]); DESIGN.update(round17.G, e_bar_overlap=0.45, trap_depth=0.6)

CHARS = ([chr(k) for k in range(ord('A'), ord('Z') + 1)] + [chr(k) for k in range(ord('a'), ord('z') + 1)] +
         list("0123456789") + list(latin.PUNCT.keys()))
def gname(ch):
    if ch == ' ': return 'space'
    return agl.UV2AGL.get(ord(ch), 'uni%04X' % ord(ch))
GLYPH_ORDER = ['.notdef', 'space'] + [gname(ch) for ch in CHARS]

ORIG = round12.ORIG
def all_glyphs():
    g = dict(A.GLYPHS); g.update(latin.CAPS); g.update(latin.FIGS); g.update(latin.PUNCT); return g
SIDES = dict(A.SIDES); SIDES.update(latin.SIDES)

def ctx_with_cut(p):
    c = A.ctx(p); c["_cut"] = round17.make_cut(SEED, EVERY, AMP); return c

def glyph_polys(ch, p, pen, post, glyphs):
    c = ctx_with_cut(p)
    A.outline = pen
    try: polys = glyphs[ch](c)
    finally: A.outline = ORIG
    polys = round12.flatten(polys)
    if post: polys = post(polys, c)
    return round17.orient_with_holes(polys), c

def build(out_dir, name="Fjord", style="Regular"):
    p = dict(DESIGN)
    saved_glyphs = dict(A.GLYPHS); saved_arch = A._arch
    A.GLYPHS.update(round17.cp_glyphs(SEED, EVERY, AMP, 1.0, None)); round17.patch_arch(1.0)
    glyphs_all = all_glyphs()
    try:
        fb = FontBuilder(1000, isTTF=True); fb.setupGlyphOrder(GLYPH_ORDER)
        fb.setupCharacterMap({ord(ch): gname(ch) for ch in CHARS} | {32: 'space'})
        glyphs, metrics = {}, {}
        c = ctx_with_cut(p)
        pen_fn = round17.pen_linear(SEED, EVERY, AMP); post = round17.Cut(SEED, 4, 3.0, 2.0, hand=False)
        for ch in CHARS:
            polys, cc = glyph_polys(ch, p, pen_fn, post, glyphs_all)
            top = latin.capH(c) if (ch.isupper() or ch.isdigit()) else c["xh"]   # caps fit on the cap band
            band = [x for poly in polys for (x, y) in poly if -c["over"] <= y <= top + c["over"]]
            xs = [x for poly in polys for (x, y) in poly]
            l, r = (min(band), max(band)) if band else (min(xs), max(xs))
            lt, rt = SIDES.get(ch, ('straight', 'straight'))
            capf = 1.15 if (ch.isupper() or ch.isdigit()) else 1.0
            lsb = A.bearing(c, lt) * capf; adv = lsb + (r - l) + A.bearing(c, rt) * capf
            dx = lsb - l
            pen = TTGlyphPen(None)
            for poly in polys:
                pts = [(round(x + dx), round(y)) for x, y in poly]
                pen.moveTo(pts[0])
                for q in pts[1:]: pen.lineTo(q)
                pen.closePath()
            glyphs[gname(ch)] = pen.glyph(); metrics[gname(ch)] = (int(round(adv)), int(round(min(xs) + dx)))
        pen = TTGlyphPen(None); pen.moveTo((50, 0)); pen.lineTo((50, 700)); pen.lineTo((450, 700)); pen.lineTo((450, 0)); pen.closePath()
        glyphs['.notdef'] = pen.glyph(); metrics['.notdef'] = (500, 50)
        glyphs['space'] = TTGlyphPen(None).glyph(); metrics['space'] = (int(A.n_counter(c) * 1.7), 0)
        fb.setupGlyf(glyphs); fb.setupHorizontalMetrics(metrics)
        fb.setupHorizontalHeader(ascent=900, descent=-300)
        fb.setupNameTable(dict(familyName=name, styleName=style, fullName=f"{name} {style}", psName=f"{name}-{style}", uniqueFontIdentifier=f"{name};{style};2026-09-12"))
        fb.setupOS2(sTypoAscender=900, sTypoDescender=-300, usWinAscent=900, usWinDescent=300, sxHeight=int(p["xh"]), sCapHeight=int(latin.capH(c)))
        fb.setupPost()
        path = os.path.join(out_dir, f"{name}-{style}.ttf"); fb.save(path); return path
    finally:
        A.GLYPHS.clear(); A.GLYPHS.update(saved_glyphs); A._arch = saved_arch

SPECIMEN = [
 ("caps", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
 ("lower", "abcdefghijklmnopqrstuvwxyz"),
 ("figures", "0123456789"),
 ("punct", ".,:;!?'\"‘’“” -–— ()[] /\\ *+= &%#@_…"),
 ("pangram", "Beyond the quiet fjord, a jackdaw skims low over black water, while the last light of dusk hazes the zinc-gray peaks and a vixen crosses the frozen marsh."),
 ("sentence", "What we make of the time we have is the only thing that was ever ours to make, and the people we made it for are the ones who will remember how it went."),
 ("mixed", "Hamburgers in a fjord. Quick “Zephyrs” & 1234567890; (Wolf-Jaw) — 45% of 6/7, Mr. O’Neil!"),
]

def page(path):
    b = base64.b64encode(open(path, "rb").read()).decode()
    rows = ''.join(f'<section><h2>{k}</h2><p class="{"big" if k in ("caps","lower","figures","punct") else "text"}">{html.escape(t)}</p></section>' for k, t in SPECIMEN)
    return f'''<title>Fjord Specimen</title>
<style>@font-face{{font-family:"Fjord";src:url(data:font/ttf;base64,{b}) format("truetype")}}
:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:20px 14px 60px;font:15px/1.45 -apple-system,Arial,sans-serif}}main{{max-width:900px;margin:0 auto}}h1{{font-size:24px;margin:0 0 4px}}.lede{{color:var(--soft);max-width:64ch;margin:0 0 20px}}
section{{border-top:1px solid var(--rule);padding:12px 0}}h2{{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--soft);margin:0 0 6px}}
.big{{font-family:Fjord,serif;font-size:52px;line-height:1.2;margin:0;word-break:break-all}}.text{{font-family:Fjord,serif;font-size:22px;line-height:1.4;margin:0;max-width:34em}}</style>
<main><h1>Fjord Specimen</h1><p class="lede">Round 19. The complete Latin set in one file, Fjord-Regular.ttf, on the k6 construction: capitals, lowercase, lining figures, text punctuation, quotes and dashes. Set here by the file itself. {len(CHARS) + 1} glyphs.</p>{rows}</main>'''

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    os.makedirs(out, exist_ok=True)
    path = build(out); TTFont(path)
    open(os.path.join(out, "fjord-specimen.html"), "w").write(page(path))
    print("ok", path, len(CHARS) + 1, "glyphs", os.path.getsize(path) // 1024, "KB")
