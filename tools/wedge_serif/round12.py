"""Round 12: VECTOR FONT FILES. Owner 2026-09-12: 'what i need are vector
font files, not bitmap treatments. we are generating fonts for epub reading.'

One TrueType file per technique, all from the B5.9 design. Every technique
here is an OUTLINE operation: a pen model (how a centerline becomes ink) or
an outline model (offset, rounding, decimation, jitter, clipping), never a
raster pass. Glyphs are the stroked polygons written as straight-segment
TrueType contours with a consistent winding, so overlaps union under the
nonzero rule (no boolean library builds on this Python; that is the trade).
Coverage: H, a-z, period, comma, hyphen, space. Advances from the fitting
rule (bearings by side type, x-height band, fit 0.8).
"""
import base64, html, io, math, os, random, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round10, round11, alphabet2 as A
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

B59 = round10.steps()[-1][2]
ORIG = A.outline
GLYPH_ORDER = [".notdef", "space", "H"] + list("abcdefghijklmnopqrstuvwxyz") + ["period", "comma", "hyphen"]
CHAR = {"space": " ", "period": ".", "comma": ",", "hyphen": "-", "H": "H"}
for ch in "abcdefghijklmnopqrstuvwxyz": CHAR[ch] = ch

# ---------------------------------------------------------------- outline ops
def signed_area(poly):
    return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))

def orient(polys):
    """All contours the same way round, so overlaps ADD under nonzero."""
    out = []
    for poly in polys:
        if len(poly) < 3: continue
        a = signed_area(poly)
        if abs(a) < 1e-6: continue
        out.append(poly if a > 0 else poly[::-1])
    return out

def chaikin(poly, passes=1):
    """Corner-cutting smoothing: the vector version of ink rounding."""
    for _ in range(passes):
        q = []
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            q.append((0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1)); q.append((0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1))
        poly = q
    return poly

def decimate(poly, every):
    keep = [p for i, p in enumerate(poly) if i % every == 0]
    return keep if len(keep) >= 3 else poly

def jitter(poly, amp, seed):
    rng = random.Random(seed)
    return [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in poly]

def clip_halfplane(poly, keep_below=None, keep_above=None):
    """Sutherland-Hodgman against y <= keep_below or y >= keep_above."""
    if keep_below is not None: inside = lambda p: p[1] <= keep_below; yc = keep_below
    else: inside = lambda p: p[1] >= keep_above; yc = keep_above
    out = []
    for cur, nxt in zip(poly, poly[1:] + poly[:1]):
        ci, ni = inside(cur), inside(nxt)
        if ci: out.append(cur)
        if ci != ni:
            t = (yc - cur[1]) / (nxt[1] - cur[1]) if nxt[1] != cur[1] else 0
            out.append((cur[0] + (nxt[0] - cur[0]) * t, yc))
    return out if len(out) >= 3 else None

def stencil(polys, bands):
    """Cut paper bands (y0, y1) through every contour: a stencil's bridges."""
    for y0, y1 in bands:
        nxt = []
        for poly in polys:
            lo = clip_halfplane(poly, keep_below=y0); hi = clip_halfplane(poly, keep_above=y1)
            if lo: nxt.append(lo)
            if hi: nxt.append(hi)
        polys = nxt
    return polys

def offset_naive(poly, d):
    """Grow a contour by d along vertex normals (an approximate outline
    offset; good enough for ink spread on well-behaved stroke polygons)."""
    n = len(poly); out = []
    for i in range(n):
        x0, y0 = poly[i - 1]; x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        ax, ay = x1 - x0, y1 - y0; bx, by = x2 - x1, y2 - y1
        la = math.hypot(ax, ay) or 1; lb = math.hypot(bx, by) or 1
        nx = (-ay / la - by / lb) / 2; ny = (ax / la + bx / lb) / 2
        L = math.hypot(nx, ny) or 1
        out.append((x1 + nx / L * d, y1 + ny / L * d))
    return out

class Multi(list):
    """Several polygons standing in for one: a pen whose outline may cross
    itself hands back one quad per centerline segment instead, all wound the
    same way, so the nonzero union is exact."""

def quadify(pen_fn):
    def outline(pts, pen, profile=None, cut0=None, cut1=None):
        poly = pen_fn(pts, pen, profile, cut0, cut1)
        n = len(poly) // 2
        L, R = poly[:n], poly[n:][::-1]
        quads = Multi()
        # each quad spans TWO segments, so neighbors overlap by one: a shared
        # edge alone left a hairline seam in FreeType's rasterizer (seen on
        # every quadified font, 2026-09-12), an overlap does not.
        for i in range(n - 1):
            j = min(n - 1, i + 2)
            q = [L[i], L[i + 1], L[j], R[j], R[i + 1], R[i]]
            if abs(signed_area(q)) > 1e-3: quads.append(q)
        return quads
    return outline

def flatten(polys):
    out = []
    for poly in polys:
        if isinstance(poly, Multi): out.extend(poly)
        else: out.append(poly)
    return out

# ---------------------------------------------------------------- techniques
def V(key, title, blurb, pen=None, post=None, over=None, fixed=None):
    return dict(key=key, title=title, blurb=blurb, pen=pen, post=post, over=over or {}, fixed=fixed)

def post_spread(d=7, passes=1):
    def f(polys, c):
        polys = [offset_naive(p, d) for p in polys]
        return [chaikin(p, passes) for p in polys]
    return f

def post_round(passes=2):
    return lambda polys, c: [chaikin(p, passes) for p in polys]

def post_lowpoly(every):
    return lambda polys, c: [decimate(p, every) for p in polys]

def post_jitter(amp, seed=1):
    return lambda polys, c: [jitter(p, amp, seed + i) for i, p in enumerate(polys)]

def post_scissors(every=5, amp=6, seed=2):
    return lambda polys, c: [jitter(decimate(p, every), amp, seed + i) for i, p in enumerate(polys)]

def post_stencil(polys, c):
    xh = c["xh"]; w = c["s"] * 0.28
    return stencil(polys, [(xh * 0.74 - w / 2, xh * 0.74 + w / 2), (xh * 0.28 - w / 2, xh * 0.28 + w / 2)])

def post_counterpunch(polys, c):
    # outer swell + rounding; counters stay where the strokes leave them
    # (a true counterpunch needs a boolean subtract; approximate)
    return [chaikin(offset_naive(p, 8), 1) for p in polys]

BANK = [
 V("V01", "Naive assembly", "the first model: shapes butted, square ends, straight wedges", over=dict(naive_o=True, raw_joins=True, cut_deg=0, fillet=0.0)),
 V("V02", "Broad nib, 26°", "a true translation pen; the outline is the nib itself", pen=quadify(round11.pen_translation(1.0))),
 V("V03", "Broad nib, 40°", "the same nib held steeper", pen=quadify(round11.pen_translation(1.0)), over=dict(stress=40)),
 V("V04", "Expert brush", "pressure swells the middle of every stroke; entries and exits taper", pen=quadify(round11.pen_brush(0.45, 0.25))),
 V("V05", "Expert brush, light hand", "less pressure, quicker entries", pen=quadify(round11.pen_brush(0.3, 0.15)), over=dict(stem=76)),
 V("V06", "Pointed pen", "hairlines with swelling downstrokes", pen=quadify(round11.pen_pointed(0.85))),
 V("V07", "Counterpunch (approx.)", "outer form swollen and filed round; counters as the strokes leave them", post=post_counterpunch),
 V("V08", "Letterpress, ink spread", "every contour grown 7 units and rounded", post=post_spread(7, 1)),
 V("V09", "Letterpress, heavy", "grown 12 units, rounded twice", post=post_spread(12, 2)),
 V("V10", "Wood type", "edge jitter on a heavier cut", post=post_jitter(4, 3), over=dict(stem=100, contrast=0.35)),
 V("V11", "Constructed", "constant-width strokes, circular bowls", pen=round11.pen_constant(0.95), over=dict(bowl_k=2.0, contrast=0.0)),
 V("V12", "Stencil", "two paper bands cut through everything", post=post_stencil, over=dict(stem=100)),
 V("V13", "Typewriter", "monospaced on a 560-unit cell, slab-ish wedges", over=dict(stem=90, contrast=0.3, wedge_len=0.9, wedge_depth=1.0, fillet=0.0), fixed=560),
 V("V14", "Phototype", "rounded corners, tight fit", post=post_round(2), over=dict(fit=0.55)),
 V("V15", "Rotating nib, 50°", "the nib turns along each stroke", pen=quadify(round11.pen_rotating(50))),
 V("V16", "Rotating nib, 110°", "a wide turn", pen=quadify(round11.pen_rotating(110))),
 V("V17", "Ribbon", "a twisted ribbon, 2.5 waves per stroke", pen=quadify(round11.pen_ribbon(2.5, 0.5))),
 V("V18", "Ribbon, fast twist", "five waves", pen=quadify(round11.pen_ribbon(5, 0.6))),
 V("V19", "Gravity", "wet ink sagging toward the baseline", pen=quadify(round11.pen_gravity(0.6))),
 V("V20", "Speed pen", "thickness is speed: straights thin, curves thick", pen=quadify(round11.pen_speed(0.45))),
 V("V21", "Low-poly", "one vertex in seven", post=post_lowpoly(7)),
 V("V22", "Low-poly, coarser", "one in eleven", post=post_lowpoly(11)),
 V("V23", "Scissors", "cut from paper: decimated and jittered", post=post_scissors(5, 6)),
 V("V24", "Wax cast", "rounded four times; every join melts", post=post_round(4), over=dict(stem=96)),
 V("V25", "Brush, then letterpress", "the expert brush, grown and rounded", pen=quadify(round11.pen_brush(0.45, 0.25)), post=post_spread(6, 1)),
 V("V26", "Pointed pen, then stencil", "copperplate with bridges", pen=quadify(round11.pen_pointed(0.85)), post=post_stencil),
]

# ---------------------------------------------------------------- building
def glyph_polys(p, name, pen, post):
    c = A.ctx(p)
    A.outline = pen or ORIG
    try:
        fn = A.GLYPHS[CHAR[name]] if name in CHAR and CHAR[name] in A.GLYPHS else A.GLYPHS.get(name)
        polys = fn(c)
    finally:
        A.outline = ORIG
    polys = flatten(polys)
    if post: polys = post(polys, c)
    return orient(polys), c

def build(v, out_dir):
    p = dict(B59); p.update(v["over"])
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(GLYPH_ORDER)
    fb.setupCharacterMap({ord(CHAR[n]): n for n in GLYPH_ORDER if n in CHAR})
    glyphs = {}; metrics = {}
    c = A.ctx(p)
    for name in GLYPH_ORDER:
        pen = TTGlyphPen(None)
        if name == ".notdef":
            for (x0, y0, x1, y1) in [(50, 0, 450, 700)]:
                pen.moveTo((x0, y0)); pen.lineTo((x0, y1)); pen.lineTo((x1, y1)); pen.lineTo((x1, y0)); pen.closePath()
            glyphs[name] = pen.glyph(); metrics[name] = (500, 50); continue
        if name == "space":
            glyphs[name] = pen.glyph(); metrics[name] = (int(A.n_counter(c) * 1.7), 0); continue
        polys, _ = glyph_polys(p, name, v["pen"], v["post"])
        band = [x for poly in polys for (x, y) in poly if -c["over"] <= y <= c["xh"] + c["over"]]
        xs = [x for poly in polys for (x, y) in poly]
        l, r = (min(band), max(band)) if band else (min(xs), max(xs))
        ch = CHAR[name]; lt, rt = A.SIDES.get(ch) or A.SIDES[ch.lower()]
        if v["fixed"]:
            adv = v["fixed"]; lsb = (adv - (r - l)) / 2
        else:
            lsb = A.bearing(c, lt); adv = lsb + (r - l) + A.bearing(c, rt)
        dx = lsb - l
        for poly in polys:
            pts = [(round(x + dx), round(y)) for x, y in poly]
            pen.moveTo(pts[0])
            for q in pts[1:]: pen.lineTo(q)
            pen.closePath()
        glyphs[name] = pen.glyph()
        metrics[name] = (int(round(adv)), int(round(min(x for poly in polys for (x, y) in poly) + dx)))
    fb.setupGlyf(glyphs); fb.setupHorizontalMetrics(metrics)
    asc, desc = 900, -300
    fb.setupHorizontalHeader(ascent=asc, descent=desc)
    fam = f"Fjord {v['key']} {v['title']}"
    fb.setupNameTable(dict(familyName=fam, styleName="Regular", fullName=fam, psName="Fjord" + v["key"], uniqueFontIdentifier="Fjord;" + v["key"] + ";2026-09-12"))
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, usWinAscent=asc, usWinDescent=-desc, sxHeight=int(p["xh"]), sCapHeight=int(p["asc"] * 0.94))
    fb.setupPost()
    path = os.path.join(out_dir, f"Fjord-{v['key']}.ttf"); fb.save(path)
    return path

def page(paths):
    css = []; tiles = []
    for v, path in zip(BANK, paths):
        b = base64.b64encode(open(path, "rb").read()).decode()
        css.append(f'@font-face{{font-family:"F{v["key"]}";src:url(data:font/ttf;base64,{b}) format("truetype")}}')
        tiles.append(f'''<section class="cut">
  <h2><span class="num">{v["key"]}</span>{html.escape(v["title"])} <span class="blurb">{html.escape(v["blurb"])} · Fjord-{v["key"]}.ttf, {os.path.getsize(path)//1024} KB</span></h2>
  <p class="big" style="font-family:'F{v["key"]}',serif">Hamburgers in a fjord.</p>
  <p class="text" style="font-family:'F{v["key"]}',serif">what we make of the time we have is the only thing that was ever ours to make, and the people we made it for are the ones who will remember how it went.</p>
</section>''')
    return f'''<title>Fjord Font Files</title>
<style>
{"".join(css)}
:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}
:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:20px 14px 60px;font:15px/1.45 -apple-system,"Helvetica Neue",Arial,sans-serif}}
main{{max-width:900px;margin:0 auto}} h1{{font-size:24px;margin:0 0 4px}}
.lede{{color:var(--soft);max-width:64ch;margin:0 0 22px}}
.cut{{border-top:1px solid var(--rule);padding:14px 0 8px}} h2{{font-size:15px;margin:0 0 8px}}
.num{{color:var(--soft);font-variant-numeric:tabular-nums;margin-right:8px}}
.blurb{{display:block;font-weight:normal;color:var(--soft);font-size:12px}}
.big{{font-size:64px;line-height:1.1;margin:0 0 6px;text-wrap:balance}}
.text{{font-size:22px;line-height:1.4;margin:0;max-width:34em}}
</style>
<main>
<h1>Fjord Font Files</h1>
<p class="lede">Round 12. Twenty-six TrueType files from the B5.9 design, one per technique, all vector: pen models and outline operations, no raster. This page sets the line and the evaluation sentence in the font files themselves, so what you see is the file, rendered by your phone. Coverage is H, a–z, and . , - for now.</p>
{''.join(tiles)}
</main>'''

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    os.makedirs(out, exist_ok=True)
    paths = [build(v, out) for v in BANK]
    for pth in paths: TTFont(pth)  # must parse
    open(os.path.join(out, "fjord-fonts.html"), "w").write(page(paths))
    with zipfile.ZipFile(os.path.join(out, "fjord-fonts.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for pth in paths: z.write(pth, os.path.basename(pth))
    print("ok", len(paths), "fonts ->", out)
