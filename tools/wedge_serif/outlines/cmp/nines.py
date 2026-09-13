"""Ten 9s with serifed tails, one TTF each, and the page to choose from
(owner 2026-09-13: "give me ten variants on a 9 serifed tail to choose
from"). The reference font is built once; then for each variant in
glyphs/nines.py the registry's '9' is rebound, the 9 ALONE is rebuilt with
the reference's solved widths pinned (so the bowl and counter are the
reference's) and the cutter's phase primed to where the full build cut
the 9, and that glyph's glyf entry and hmtx row are spliced into a copy of
the reference TTF as Albo-nine<NN>.ttf. The page shows each 9 in "6 9 /
19 99" at 230 px figure height on fixed origins, and a sentence at 13 pt
through the reader's four-level pipeline; every heading carries the
numbers the owner's standing rule asks for -- the bowl counter (unchanged),
the white between the serif and the bowl at 54 px, and the sidebearing and
advance against the current 9.

    cd tools/wedge_serif && python3 -W ignore -m outlines.cmp.nines <out_dir>
"""
import sys, os, io, math, base64, html, shutil, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from .. import build, pen, geom, cut
from ..glyphs import GLYPHS, figures, nines
from . import proof
import latin, round19

PX_EM = 54                     # 13 pt on the 2x reader
FIG_PX = 230                   # block (a): the figure box (FIG_BOX['9'], 0.97 cap heights) drawn this tall
TEXT = "In 1929 the 9 ships; 99 tons; 1,969 and 9,199 by 1899."
SERIF_TIP = 70.0               # units right of the tail's tip: the serif's protruding part, under the bowl's left side, where "the white above the serif" is read

def fig_units():
    top, bot = latin.FIG_BOX['9']; return (top - bot) * pen.CAP, top * pen.CAP, bot * pen.CAP

# ---------------------------------------------------------------- building
def build_reference(out_dir):
    t = time.time(); path, W, report = build.build(out_dir); dt = time.time() - t
    # the cutter's phase counter when the full build reached the 9: one per contour cut before it, in CHARS order
    n_before = sum(report[ch]['contours'] for ch in build.CHARS[:build.CHARS.index('9')] if ch in report)
    print(f"reference {path} in {dt:.1f}s; contours cut before the 9: {n_before}")
    return path, W, report, n_before

def _rotate_to(ring, start, tol=1e-3):
    """The ring's coordinate list started at the vertex nearest `start`
    (within tol), else unchanged."""
    pts = list(ring)
    if pts and pts[0] == pts[-1]: pts = pts[:-1]
    k = min(range(len(pts)), key=lambda i: math.dist(pts[i], start))
    return pts[k:] + pts[:k] if math.dist(pts[k], start) <= tol else pts

def canon(g, ref):
    """`g` (one polygon, one hole) with its rings started where the
    reference's start: shapely's union begins the counter ring one vertex
    later than g_nine's, and the one-in-four cut keeps different facets
    of the SAME counter from a different start. Called after the ink
    spread, since the spread may restart a ring too."""
    from shapely.geometry import Polygon
    if g.geom_type != 'Polygon' or ref.geom_type != 'Polygon' or len(g.interiors) != len(ref.interiors): return g
    ext = _rotate_to(g.exterior.coords, ref.exterior.coords[0])
    holes = [_rotate_to(h.coords, rh.coords[0]) for h, rh in zip(g.interiors, ref.interiors)]
    return Polygon(ext, holes)

def build_variant(out_dir, fn, W_ref, n_before, ref_drawn):
    """Rebuild the 9 alone as `fn` with the reference's W, cut phase and
    ring starts (ref_drawn: the reference's spread 9, as build.draw made it)."""
    saved_fn, saved_solve, saved_cutter, saved_draw = GLYPHS['9'], build.solve_widths, cut.Cutter, build.draw
    def primed(seed=73, every=4):
        k = saved_cutter(seed, every); k.n = n_before; return k
    def draw(ch, W=None):
        g = saved_draw(ch, W); return canon(g, ref_drawn) if ch == '9' else g
    try:
        GLYPHS['9'] = fn; build.solve_widths = lambda passes=3: dict(W_ref); cut.Cutter = primed; build.draw = draw
        path, W, report = build.build(out_dir, only='9')
    finally:
        GLYPHS['9'], build.solve_widths, cut.Cutter, build.draw = saved_fn, saved_solve, saved_cutter, saved_draw
    return path, report['9']

def splice(ref_ttf, var_ttf, out_ttf):
    """The variant's nine (outline and metrics) into a copy of the reference."""
    ref = TTFont(ref_ttf); var = TTFont(var_ttf)
    ref['glyf']['nine'] = var['glyf']['nine']; ref['hmtx']['nine'] = var['hmtx']['nine']
    ref.save(out_ttf); TTFont(out_ttf)   # re-open: a broken splice fails here, not on the page
    return out_ttf

# ---------------------------------------------------------------- measuring
def nine_contours(ttf):
    """[(points, is_hole)] of the TTF's nine, from its glyf coordinates."""
    f = TTFont(ttf); g = f['glyf']['nine']; out = []
    coords, ends = list(g.coordinates), list(g.endPtsOfContours); s = 0
    for e in ends:
        pts = [tuple(p) for p in coords[s:e + 1]]; s = e + 1
        out.append((pts, geom.signed_area(pts) < 0))
    return out

def counter_report(ref_rep, var_rep, tol=1e-3):
    """The bowl counter of the variant against the reference's, point for
    point, on the builder's CUT, FLOAT contours (report['9']['pts']) taken
    relative to each glyph's own first hole vertex: the fit places a
    glyph by its full extent, so a longer tail moves the whole 9 by a
    fraction of a unit and the TTF's rounded coordinates then differ by
    0 or 1 everywhere while the outline has not moved."""
    def holes(rep):
        hs = [pts for pts, hole in rep['pts'] if hole]
        return [[(x - h[0][0], y - h[0][1]) for x, y in h] for h in hs]
    hr, hv = holes(ref_rep), holes(var_rep)
    if len(hr) != 1 or len(hv) != 1: return f"counter: {len(hv)} holes (reference {len(hr)})"
    a, b = hr[0], hv[0]
    if len(a) == len(b) and all(math.dist(p, q) <= tol for p, q in zip(a, b)): return f"counter identical to the current 9 (all {len(a)} cut vertices)"
    ba, bb = geom.bbox(geom.poly(a)), geom.bbox(geom.poly(b))
    return f"counter same bbox ({'yes' if all(abs(x - y) < 0.5 for x, y in zip(ba, bb)) else 'NO'}), {sum(1 for p, q in zip(a, b) if math.dist(p, q) > tol)} of {len(a)} cut vertices differ"

def quantized_glyph(ttf, ch, px=PX_EM, ss=8, pad=6):
    """One glyph at `px` through the four-level pipeline (proof.eink's
    method: 8x supersampled coverage, the reader's thresholds). Returns the
    level array and the x of the glyph's origin in it."""
    big = ImageFont.truetype(ttf, px * ss); f = TTFont(ttf); upm = f['head'].unitsPerEm
    adv = f['hmtx'][round19.gname(ch)][0] * px / upm
    w = int(adv + 2 * pad + 20); h = int(px * 1.6)
    im = Image.new('L', (w * ss, h * ss), 255); d = ImageDraw.Draw(im)
    base = int(px * 1.05)
    d.text((pad * ss, base * ss), ch, font=big, fill=0, anchor='ls')
    a = np.asarray(im, dtype=np.float32) / 255.0
    cov = 1.0 - a.reshape(h, ss, w, ss).mean(axis=(1, 3))
    out = np.full(cov.shape, 255, dtype=np.uint8)
    out[cov >= proof.THRESH[0]] = proof.LEVELS[1]; out[cov >= proof.THRESH[1]] = proof.LEVELS[2]; out[cov >= proof.THRESH[2]] = proof.LEVELS[3]
    return out, pad, base

def quantize_geoms(geoms, frame, px=PX_EM, ss=8, upm=1000, pad_units=60):
    """Design geometry (figure frame, units) through the four-level
    pipeline at `px`: 8x supersampled coverage, the reader's thresholds.
    `frame` is the (x0, y0, x1, y1) box the image is laid out on, so two
    renders share pixel positions. Returns (levels, x_of_unit(fn),
    row_of_unit(fn)); every polygon in `geoms` is drawn (holes as paper)."""
    x0, y0, x1, y1 = frame; k = px / upm
    W_ = int(math.ceil((x1 - x0 + 2 * pad_units) * k)); H_ = int(math.ceil((y1 - y0 + 2 * pad_units) * k))
    im = Image.new('L', (W_ * ss, H_ * ss), 255); d = ImageDraw.Draw(im)
    X = lambda x: (x - x0 + pad_units) * k * ss; Y = lambda y: (y1 + pad_units - y) * k * ss
    for g in geoms:
        for pts, hole in geom.contours(g, min_area=0.5): d.polygon([(X(x), Y(y)) for x, y in pts], fill=255 if hole else 0)
    a = np.asarray(im, dtype=np.float32) / 255.0
    cov = 1.0 - a.reshape(H_, ss, W_, ss).mean(axis=(1, 3))
    out = np.full(cov.shape, 255, dtype=np.uint8)
    out[cov >= proof.THRESH[0]] = proof.LEVELS[1]; out[cov >= proof.THRESH[1]] = proof.LEVELS[2]; out[cov >= proof.THRESH[2]] = proof.LEVELS[3]
    return out, (lambda x: int((x - x0 + pad_units) * k)), (lambda y: int((y1 + pad_units - y) * k))

def aperture_report(fn, c, px=PX_EM):
    """The white between the tail's serif and the bowl above it at `px`
    on the four-level render, measured on the design outline (the ink
    spread is 0.06 px here and the cut keeps every corner): the glyph and
    its RING ALONE go through the same pipeline, and in each column the
    white is the run of paper (255; light gray counts as ink) between the
    ring's lowest ink row and the first ink row of the glyph below it.
    Two readings: the min over the serif's protruding columns (the tip to
    SERIF_TIP units right of it, under the bowl's left side -- the white
    the serif itself makes), and the min over every column from the tip to
    the bowl's center -- the pocket between tail and bowl at its
    narrowest, where a word image fills first; right of the center the
    tail joins the ring and the white is 0 by construction."""
    g = fn(c); b = nines._base(c); ring = b['ring']; frame = geom.bbox(g)
    lv, X, Y = quantize_geoms([g], frame, px); lr, _, _ = quantize_geoms([ring], frame, px)
    tip_x = frame[0]; x0 = X(tip_x); x_tip = X(tip_x + SERIF_TIP); x_mid = X(b['cx'])
    def gap(x):
        ring_ink = np.where(lr[:, x] < 255)[0]
        if not len(ring_ink): return None
        r = int(ring_ink.max()); below = np.where(lv[r + 1:, x] < 255)[0]
        return int(below.min()) if len(below) else None
    tip = [v for v in (gap(x) for x in range(x0, x_tip + 1)) if v is not None]
    pocket = [v for v in (gap(x) for x in range(x0, x_mid + 1)) if v is not None]
    if not tip or not pocket: return "white to the bowl: no column has bowl above tail", None
    return (f"white to the bowl at {px} px: {min(tip)} px of paper above the serif's tip (min over its first {len(tip)} columns), "
            f"pocket under the bowl's left half narrowest {min(pocket)} px"), (min(tip), min(pocket))

def metrics(ttf):
    f = TTFont(ttf); adv, lsb = f['hmtx']['nine']; g = f['glyf']['nine']; g.recalcBounds(f['glyf'])
    return adv, lsb, g.xMin, g.xMax, g.yMin

def built_overhang(ttf):
    """The tail's tip past the bowl's left ink on the built outline: the
    glyph's xMin against the leftmost point in the bowl's band (y >= 0)."""
    pts = [p for c, h in nine_contours(ttf) for p in c]
    bowl_left = min(x for x, y in pts if y >= 0); return bowl_left - min(x for x, y in pts)

# ---------------------------------------------------------------- rendering
def b64(im):
    buf = io.BytesIO(); im.save(buf, format='PNG'); return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

WORDS = (("6", "9"), ("19", "99"))

def figure_block(ttf, origins, px, width=proof.W):
    """"6 9" over "19 99": every WORD starts on a fixed origin (the
    reference's advances plus fixed gaps, the same x for every variant)
    and runs on the variant's OWN advances, so "19" and "99" are the pairs
    the font really sets while the words stay aligned across variants.
    The figure box's three rules faint behind each line: its top, the
    baseline, its bottom."""
    f = TTFont(ttf); upm = f['head'].unitsPerEm; font = ImageFont.truetype(ttf, px)
    figH, top_u, bot_u = fig_units(); top = top_u * px / upm; bot = -bot_u * px / upm
    lh = int(top + bot + 40); H = lh * len(origins) + 10
    im = Image.new('L', (width, H), 255); d = ImageDraw.Draw(im)
    for i, line in enumerate(origins):
        base = 10 + i * lh + int(top) + 16
        for y, tone in ((base - top, 232), (base, 210), (base + bot, 232)): d.line([(0, y), (width, y)], fill=tone)
        for word, x in line: d.text((x, base), word, font=font, fill=0, anchor='ls')
    return im

def fixed_origins(ref_ttf, px, gap_word=34, pad=14):
    f = TTFont(ref_ttf); upm = f['head'].unitsPerEm
    adv = lambda ch: f['hmtx'][round19.gname(ch)][0] * px / upm
    lines = []
    for words in WORDS:
        x = pad; line = []
        for wi, wd in enumerate(words):
            if wi: x += gap_word
            line.append((wd, x)); x += sum(adv(ch) for ch in wd)
        lines.append(line)
    return lines, x

def page(entries, out_html):
    """entries: [(label, sub, ttf)] -- the current 9 first."""
    figH, _, _ = fig_units(); px = int(round(FIG_PX * 1000 / figH))
    origins, right = fixed_origins(entries[0][2], px)
    parts = []; png_dir = os.path.join(os.path.dirname(out_html), 'png'); os.makedirs(png_dir, exist_ok=True)
    for i, (label, sub, ttf) in enumerate(entries):
        a = figure_block(ttf, origins, px); bblk = proof.eink(ttf, TEXT, pt=13, scale=2)
        a.save(os.path.join(png_dir, f'{i:02d}-a.png')); bblk.save(os.path.join(png_dir, f'{i:02d}-b.png'))   # the same PNGs, as files, for the look step
        parts.append(f'<section><h2>{html.escape(label)}<br><small>{html.escape(sub)}</small></h2>'
                     f'<figure><img src="{b64(a)}" width="{a.size[0]}" height="{a.size[1]}"><figcaption>6 9 / 19 99 at {FIG_PX} px figure height ({px} px em); words on fixed origins, pairs on the font\'s own advances; rules: figure top, baseline, figure bottom</figcaption></figure>'
                     f'<figure><img src="{b64(bblk)}" width="{bblk.size[0]}" height="{bblk.size[1]}"><figcaption>13 pt on the 2x reader, the four-level pipeline ({PX_EM} px em, 8x supersampled, 255/200/96/0)</figcaption></figure></section>')
    body = ''.join(parts)
    doc = f'''<title>Albo Nines</title>
<style>:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:16px 10px 60px;font:15px/1.45 -apple-system,Arial,sans-serif}}main{{max-width:900px;margin:0 auto}}h1{{font-size:22px;margin:0 0 6px}}h2{{font-size:15px;margin:26px 0 4px;border-top:1px solid var(--rule);padding-top:12px}}
h2 small{{display:block;font-weight:normal;font-size:12px;line-height:1.4;color:var(--soft);margin-top:4px}}p{{max-width:64ch;color:var(--soft);font-size:13px;margin:0 0 8px}}figure{{margin:0 0 10px}}figure img{{width:100%;max-width:375px;height:auto;image-rendering:pixelated;display:block;background:#fff}}figcaption{{font-size:11px;color:var(--soft);margin-top:2px}}</style>
<main><h1>Albo Nines</h1><p>Ten ways the 9's tail can end in a serif from the wedge family, on the current ring and counter. Every image is PNG at native pixels, 750 px wide shown at 375 CSS px (one image pixel per screen pixel on a 2x phone). The current 9 first.</p>{body}</main>'''
    open(out_html, 'w').write(doc); print(out_html, len(doc) // 1024, 'KB')

# ---------------------------------------------------------------- main
def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ref_ttf, W_ref, report, n_before = build_reference(os.path.join(out_dir, 'ref'))
    cur_ttf = os.path.join(out_dir, 'Albo-Medium.ttf'); shutil.copy(ref_ttf, cur_ttf)
    cur_adv, cur_lsb, cur_xmin, cur_xmax, cur_ymin = metrics(cur_ttf); cur_over = built_overhang(cur_ttf)
    c = build.ctx('9', W_ref); c["figH"] = fig_units()[0]
    cur_ap, _ = aperture_report(figures.g_nine, c)
    ref_drawn = build.draw('9', W_ref)   # the reference's spread 9: the ring starts every variant's build is aligned to
    print(f"current: built overhang {cur_over}, lsb {cur_lsb}, advance {cur_adv}, bowl ink {cur_xmin + cur_over}..{cur_xmax}, yMin {cur_ymin}; {cur_ap}")
    entries = [("current (pen cut, overhang 11)", f"built overhang {cur_over:.0f}; {cur_ap}; lsb {cur_lsb}, advance {cur_adv}; bowl ink {cur_xmin + cur_over:.0f}..{cur_xmax}; tail bottom {cur_ymin}", cur_ttf)]
    rows = []
    for i, (name, fn) in enumerate(nines.VARIANTS, 1):
        t = time.time()
        g = fn(c); dx0, dy0, _, _ = geom.bbox(g); design_over = -dx0; design_bot = dy0   # the design outline, unspread
        var_ttf, rep = build_variant(os.path.join(out_dir, f'v{i:02d}'), fn, W_ref, n_before, ref_drawn)
        out_ttf = splice(cur_ttf, var_ttf, os.path.join(out_dir, f'Albo-nine{i:02d}.ttf'))
        adv, lsb, xmin, xmax, ymin = metrics(out_ttf); over = built_overhang(out_ttf)
        cr = counter_report(report['9'], rep); ap, apn = aperture_report(fn, c)
        idea, serif = nines.INFO[name]
        sub = (f"overhang {over:.0f} built ({design_over:.1f} on the design outline; current {cur_over:.0f}); serif {serif}; {cr}; {ap}; "
               f"lsb {lsb} (current {cur_lsb}), advance {adv} (current {cur_adv}); bowl ink {xmin + over:.0f}..{xmax} (current {cur_xmin + cur_over:.0f}..{cur_xmax}); tail bottom {ymin} (current {cur_ymin})")
        entries.append((f"{i}. {name} -- {idea}", sub, out_ttf))
        rows.append(dict(i=i, name=name, idea=idea, serif=serif, over=over, design_over=design_over, bot=design_bot, ymin=ymin, counter=cr, aperture=apn, lsb=lsb, adv=adv, xmin=xmin, xmax=xmax, contours=rep['contours']))
        print(f"{i:2d} {name:14s} {time.time() - t:4.1f}s overhang {over:5.1f} (design {design_over:5.1f}) yMin {ymin} contours {rep['contours']} lsb {lsb} adv {adv} bowl {xmin + over}..{xmax} | {cr} | {ap}")
    page(entries, os.path.join(out_dir, 'albo-nines.html'))
    return rows

if __name__ == '__main__':
    main(sys.argv[1])
