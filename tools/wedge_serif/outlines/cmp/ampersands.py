"""Ten ampersand variants, each spliced into a copy of the reference Albo:
build the reference once, then for each entry of `glyphs.ampersands.VARIANTS`
rebind the registry's '&' to it, build ONLY the & (its own fit: advance and
bearings from the variant's ink), and copy that glyph's `glyf` and `hmtx`
entries into a copy of the reference as Albo-amp<NN>.ttf. Then the mobile
proof page (PNG at native pixels, 750 px blocks at 375 CSS px) and the
outline measurements: the thinnest stroke and the narrowest counter.

    cd tools/wedge_serif && PYTHON_GIL=0 python3 -W ignore -m outlines.cmp.ampersands <out_dir>
"""
import sys, os, io, base64, html, math, shutil
import numpy as np
import shapely
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from .. import build, geom, pen
from ..glyphs import GLYPHS, ampersands
from . import proof

IDEAS = {
    'current': 'Van den Keere’s garalde & as it ships: one stroke on the pen, the arm’s wedge pointing right.',
    'et_caslon': 'The E-t ligature of the italic Caslon kind: a small epsilon whose bottom rises into a tall sheared t with the family’s top wedge.',
    'garamond': 'Garamond roman: the top loop OPEN, a thin down-left diagonal, a thick spur with the A’s foot wedge, the arm standing up into a right wedge.',
    'ringed': 'A looped &: the lower bowl a full ring on the o’s construction, a small open hook above, arm and spur springing from the ring.',
    'swash': 'The spur dives past the baseline and sweeps back left under the whole glyph, within the descender, to a wedge.',
    'cursive_et': 'The Garamond-italic Et: a cap-height cursive E whose middle arm runs on as the t’s crossbar through a short upright t.',
    'teardrop': 'The top loop a teardrop, closed and round at the top, pointed at the crossing where the diagonal, the bowl and the spur leave it.',
    'narrow': 'Tall and narrow: the garalde & at 0.7 of the shipping width, its loops drawn tall so the counters hold.',
    'wide_low': 'Wide and low: a lowercase-sized &, x-height plus a little, the arm reaching far right.',
    'flick': 'The spur turns up at the baseline into a short flick ending in a wedge, no ball.',
    'aspiring': 'My own: the arm does not stop at the cap line but rises to the ascender, straightens into a stem and takes the l’s wedge.',
}

# ---------------------------------------------------------------- measure
def polygon_from_contours(conts):
    ext = [Polygon(pts) for pts, hole in conts if not hole and len(pts) >= 3]
    hol = [Polygon(pts) for pts, hole in conts if hole and len(pts) >= 3]
    g = unary_union([shapely.make_valid(p) for p in ext])
    if hol: g = g.difference(unary_union([shapely.make_valid(p) for p in hol]))
    return g

def ray_widths(conts, boundary, outward=False, L=600.0, eps=0.6, dot_max=-0.8, const=0.22, span=3):
    """For every contour point, the distance along its normal (into the ink,
    or into the air with outward=True) to the next boundary crossing. A
    reading is kept only where the two edges FACE each other -- the normal
    at the hit is antiparallel (dot < dot_max) -- and where the reading is
    steady over +-span neighbours (within `const`), which drops the
    converging edges at a wedge's apex, a pen cut's corner, a crotch and a
    counter's pointed end: what is left is the width of a stroke, or of the
    air between two strokes. Returns [(width, point, hit)]."""
    shapely.prepare(boundary)
    allpts = []; normals = []
    for pts, hole in conts:
        tans = geom.tangents(pts, closed=True)
        for p, tn in zip(pts, tans):
            allpts.append(p); normals.append((-tn[1], tn[0]))     # the LEFT normal: into the ink for ccw exteriors and cw holes alike
    P = np.array(allpts); N = np.array(normals)
    sgn = -1.0 if outward else 1.0
    raw = []
    for i, (p, n) in enumerate(zip(allpts, normals)):
        a = (p[0] + sgn * n[0] * eps, p[1] + sgn * n[1] * eps); b = (p[0] + sgn * n[0] * L, p[1] + sgn * n[1] * L)
        hit = boundary.intersection(LineString([a, b]))
        if hit.is_empty: raw.append((math.inf, None)); continue
        pts_h = [hit] if hit.geom_type == 'Point' else [g for g in getattr(hit, 'geoms', []) if g.geom_type == 'Point']
        if not pts_h: raw.append((math.inf, None)); continue
        q = min(pts_h, key=lambda h: math.dist((h.x, h.y), p))
        raw.append((math.dist((q.x, q.y), p), (q.x, q.y)))
    out = []
    # per-contour neighbourhoods
    idx = 0
    for pts, hole in conts:
        n = len(pts)
        for k in range(n):
            w, q = raw[idx + k]
            if q is None: continue
            j = int(np.argmin(np.hypot(P[:, 0] - q[0], P[:, 1] - q[1])))
            if float(N[j] @ N[idx + k]) > dot_max: continue
            ok = True
            for d in range(-span, span + 1):
                w2, _ = raw[idx + (k + d) % n]
                if not math.isfinite(w2) or abs(w2 - w) > const * w: ok = False; break
            if ok: out.append((w, pts[k], q))
        idx += n
    return out

def measure(conts):
    """The thinnest stroke and the narrowest counter of a glyph's built
    contours: hair = the least facing-edge width through the ink; gap = the
    least facing-edge width through the air (open apertures included);
    holes = each closed counter's largest inscribed circle, as a diameter."""
    g = polygon_from_contours(conts); boundary = g.boundary
    ink = ray_widths(conts, boundary, outward=False)
    air = ray_widths(conts, boundary, outward=True)
    hair = min(ink, key=lambda r: r[0]) if ink else (math.nan, None, None)
    gap = min(air, key=lambda r: r[0]) if air else (math.nan, None, None)
    holes = []
    for pts, hole in conts:
        if not hole: continue
        h = shapely.make_valid(Polygon(pts))
        if h.is_empty: continue
        seg = shapely.maximum_inscribed_circle(h, 0.5); holes.append(2 * seg.length)
    return dict(hair=hair[0], hair_at=hair[1], gap=gap[0], gap_at=gap[1], holes=sorted(holes),
                contours=len(conts), bbox=geom.bbox(g))

# ---------------------------------------------------------------- build + splice
def build_variant(fn, out_dir, tag):
    """Build only the & with the registry rebound to `fn`; also return the
    DESIGNED outline's contours (pre-cut), which is what the measurements
    read: the cut keeps one vertex in four, so on the built contours the
    facing-edge filter's window spans four times the distance and drops the
    short strokes -- a 41-unit diagonal read as 68 on the cut polygon."""
    orig = GLYPHS['&']; GLYPHS['&'] = fn
    try:
        path, W, rep = build.build(out_dir, name='Albo', style='amp' + tag, only='&')
        conts = geom.contours(build.draw('&', W))
    finally:
        GLYPHS['&'] = orig
    return path, rep['&'], conts

def splice(ref_path, var_path, out_path):
    ref = TTFont(ref_path); var = TTFont(var_path)
    ref['glyf']['ampersand'] = var['glyf']['ampersand']
    ref['hmtx']['ampersand'] = var['hmtx']['ampersand']
    ref.save(out_path); TTFont(out_path)   # re-open: the file must parse
    return out_path

# ---------------------------------------------------------------- page
def block_caps(path, lines, px, width=proof.W, pad=14, line=1.15):
    """Lines at `px`, each with a faint baseline and cap-height line. Two
    lines, because "Dombey & Son" at 150 px is ~950 px wide and a 750 px
    block clipped the & off its first version."""
    font = ImageFont.truetype(path, px); asc, desc = font.getmetrics()
    f = TTFont(path); cap = f['OS/2'].sCapHeight * px / f['head'].unitsPerEm
    lh = int(round(px * line)); H = int(pad * 2 + asc + desc + lh * (len(lines) - 1))
    im = Image.new('L', (width, H), 255); d = ImageDraw.Draw(im)
    for i, text in enumerate(lines):
        y = pad + asc + i * lh
        d.line([(0, y), (width, y)], fill=215); d.line([(0, y - cap), (width, y - cap)], fill=228)
        d.text((pad, y), text, font=font, fill=0, anchor='ls')
    return im

def page(entries, out, png_dir=None):
    """entries: [(name, ttf_path, measures)]; png_dir also saves every block."""
    parts = []
    if png_dir: os.makedirs(png_dir, exist_ok=True)
    for name, ttf, m in entries:
        parts.append(f'<h2>{html.escape(name)}</h2><p>{html.escape(IDEAS.get(name, ""))}</p>')
        if m:
            holes = ', '.join(f'{h:.0f}' for h in m['holes']) or 'none'
            parts.append(f'<p class="m">adv {m["adv"]:.0f} · ink {m["bbox"][2]-m["bbox"][0]:.0f} × {m["bbox"][3]-m["bbox"][1]:.0f} · contours {m["contours"]} · thinnest stroke {m["hair"]:.0f} · narrowest air {m["gap"]:.0f} · counters ⌀ {holes}</p>')
        a = block_caps(ttf, ['Dombey', '& Son'], 150)
        if png_dir: a.save(os.path.join(png_dir, f'{name}-a.png'))
        parts.append(f'<figure><img src="{proof.b64(a)}" width="{a.size[0]}" height="{a.size[1]}"><figcaption>Dombey & Son at 150 px, on two lines; baseline and cap height ruled</figcaption></figure>')
        b = proof.eink(ttf, 'Smith & Sons, Procter & Gamble, Marks & Spencer, & so on.')
        if png_dir: b.save(os.path.join(png_dir, f'{name}-b.png'))
        parts.append(f'<figure><img src="{proof.b64(b)}" width="{b.size[0]}" height="{b.size[1]}"><figcaption>13 pt on the 2x reader, four levels</figcaption></figure>')
    body = ''.join(parts)
    doc = f'''<title>Albo Ampersands</title>
<style>:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:16px 10px 60px;font:15px/1.45 -apple-system,Arial,sans-serif}}main{{max-width:900px;margin:0 auto}}h1{{font-size:22px;margin:0 0 6px}}h2{{font-size:15px;margin:26px 0 4px;border-top:1px solid var(--rule);padding-top:10px}}
figure{{margin:0 0 10px}}figure img{{width:100%;max-width:375px;height:auto;image-rendering:pixelated;display:block;background:#fff}}figcaption{{font-size:11px;color:var(--soft);margin-top:2px}}
p{{max-width:64ch;color:var(--soft);font-size:13px;margin:4px 0 8px}}p.m{{font-size:11px}}</style>
<main><h1>Albo Ampersands</h1><p>Ten florid ampersands drawn on Albo’s pen (2026-09-13), each spliced into the reference font; the shipping & first. Every image is PNG at native pixels, 750 px blocks shown at 375 CSS px. Units: 1000 per em; the stem is {pen.S:.0f}, the pen’s hair {pen.HAIR:.1f}, 0.6 S = {0.6 * pen.S:.1f}.</p>{body}</main>'''
    open(out, 'w').write(doc); print(out, len(doc) // 1024, 'KB')

def run(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ref_dir = os.path.join(out_dir, 'ref'); ref_path, W, rep = build.build(ref_dir, only=None)
    ref_ttf = os.path.join(out_dir, 'Albo-Regular.ttf'); shutil.copy(ref_path, ref_ttf)
    r = rep['&']; m = measure(geom.contours(build.draw('&', W))); m['adv'] = r['adv']
    entries = [('current', ref_ttf, m)]; rows = [('current', m)]
    def show(tag, name, adv, lsb, m):
        at = lambda p: f'({p[0]:.0f},{p[1]:.0f})' if p else '-'
        print(f'{tag} {name:12s} adv {adv:6.1f} lsb {lsb:5.1f} contours {m["contours"]} hair {m["hair"]:5.1f} at {at(m["hair_at"])} gap {m["gap"]:5.1f} at {at(m["gap_at"])} holes {[round(h) for h in m["holes"]]}')
    show('  ', 'current', r['adv'], r['lsb'], m)
    for i, (name, fn) in enumerate(ampersands.VARIANTS, 1):
        vdir = os.path.join(out_dir, 'var', f'{i:02d}')
        vpath, vr, conts = build_variant(fn, vdir, f'{i:02d}')
        out_ttf = splice(ref_ttf, vpath, os.path.join(out_dir, f'Albo-amp{i:02d}.ttf'))
        m = measure(conts); m['adv'] = vr['adv']
        entries.append((name, out_ttf, m)); rows.append((name, m))
        show(f'{i:02d}', name, vr['adv'], vr['lsb'], m)
    page(entries, os.path.join(out_dir, 'albo-ampersands.html'), png_dir=os.path.join(out_dir, 'png'))
    return rows

if __name__ == '__main__':
    run(sys.argv[1])
