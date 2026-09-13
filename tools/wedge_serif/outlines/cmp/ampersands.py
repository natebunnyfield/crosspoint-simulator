"""Ten ampersand variants, each spliced into a copy of the reference Albo:
build the reference once, then for each entry of `glyphs.ampersands.VARIANTS`
rebind the registry's '&' to it, build ONLY the & (its own fit: advance and
bearings from the variant's ink), and copy that glyph's `glyf` and `hmtx`
entries into a copy of the reference as Albo-amp<NN>.ttf. Then the mobile
proof page (PNG at native pixels, 750 px blocks at 375 CSS px) and the
outline measurements: the thinnest stroke and the narrowest counter.

    cd tools/wedge_serif && PYTHON_GIL=0 python3 -W ignore -m outlines.cmp.ampersands <out_dir>
    ... --gen 2     # generation II: `VARIANTS2` bred from the current and the teardrop,
                    # Albo-amp2-NN.ttf and albo-ampersands-2.html, the two parents first

Generation II adds three readings per glyph (owner: "always pay attention to
the space inside and between characters"): the white kept inside the top
loop and the lower bowl on the four-level render at 54 px (13 pt on the 2x
reader) -- an open loop reports its white as joined to the outside --, the
narrowest APERTURE that seals a counter (the smallest morphological closing
that makes a new hole; the ray scan cannot see a gap whose two edges do not
face each other), and the sidebearings against the shipping &'s.
"""
import sys, os, io, base64, html, math, shutil
import numpy as np
import shapely
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from .. import build, geom, pen
from .. import primitives as PR
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

def holes_of(g):
    polys = [g] if g.geom_type == 'Polygon' else [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']
    return sum(len(p.interiors) for p in polys)

def aperture(conts, r_max=60.0, tol=0.5):
    """The narrowest opening that seals a counter: the smallest closing
    radius r (buffer out, then in) at which the ink gains a hole, as a width
    2r. None when no closing up to r_max (an opening wider than 2 r_max, or
    no open counter at all). Existing counters are all wider than 2 r_max,
    so the closing cannot lose one and lower the count."""
    g = polygon_from_contours(conts); h0 = holes_of(g)
    closing = lambda r: g.buffer(r, join_style='round').buffer(-r, join_style='round')
    if holes_of(closing(r_max)) <= h0: return None
    lo, hi = 0.0, r_max
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if holes_of(closing(mid)) > h0: hi = mid
        else: lo = mid
    return 2 * hi

def counters54(ttf):
    """The & alone through the reader's four-level pipeline at 54 px (13 pt
    on the 2x reader): every enclosed region of WHITE (255, not the grays),
    top to bottom, as (pixels, centre y as a fraction of the ink's height,
    0 = top). White that reaches the image's edge is the outside, so an
    open loop contributes nothing here -- which is the reading."""
    im = proof.eink(ttf, '&', width=160, pad=12); a = np.asarray(im); H, Wd = a.shape
    white = a == 255; ink_rows = np.where((a < 255).any(axis=1))[0]
    y_top, y_bot = (int(ink_rows[0]), int(ink_rows[-1])) if len(ink_rows) else (0, H - 1)
    seen = np.zeros_like(white)
    def flood(sy, sx):
        stack = [(sy, sx)]; seen[sy, sx] = True; n = 0; ys = 0
        while stack:
            y, x = stack.pop(); n += 1; ys += y
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                v, u = y + dy, x + dx
                if 0 <= v < H and 0 <= u < Wd and white[v, u] and not seen[v, u]: seen[v, u] = True; stack.append((v, u))
        return n, ys / n
    for y in range(H):
        for x in (0, Wd - 1):
            if white[y, x] and not seen[y, x]: flood(y, x)
    for x in range(Wd):
        for y in (0, H - 1):
            if white[y, x] and not seen[y, x]: flood(y, x)
    regions = []
    for y in range(H):
        for x in range(Wd):
            if white[y, x] and not seen[y, x]:
                n, cy = flood(y, x)
                if n >= 2: regions.append((n, (cy - y_top) / max(1, y_bot - y_top)))
    return sorted(regions, key=lambda r: r[1])

def name_counters(regions):
    """loop = the topmost enclosed white, bowl = the bottommost; a lone
    region in the lower half is the bowl with the loop open."""
    if not regions: return dict(loop=None, bowl=None, other=0)
    if len(regions) == 1:
        n, fy = regions[0]
        return dict(loop=None, bowl=n, other=0) if fy > 0.5 else dict(loop=n, bowl=None, other=0)
    return dict(loop=regions[0][0], bowl=regions[-1][0], other=len(regions) - 2)

def bearings(ttf):
    """(adv, lsb, rsb) of the & from the shipped TTF's own tables."""
    f = TTFont(ttf); g = f['glyf']['ampersand']; g.recalcBounds(f['glyf']); adv, lsb = f['hmtx']['ampersand']
    return adv, g.xMin, adv - g.xMax

IDEAS2 = {
    'teardrop_top': 'The current with only the teardrop’s top: the closed round loop dropped onto the shipping &’s crossing, arm, hooked foot and bowl.',
    'current_arm': 'The teardrop with only the current’s arm: round 67’s loop, straight spur and foot wedge, the arm rising to the current’s 0.64 C under the right-pointing flag.',
    'midpoint': 'Every dial at the midpoint: the loop a hook, closed round the top and open at the lower left; a 41° crossing; the arm to 0.58 C; the hooked foot; the bowl half way to the o’s.',
    'mid_light': 'The midpoint with a lighter spur, 0.8 of the pen.',
    'mid_heavy': 'The midpoint with a heavier spur, 1.2 of the pen, straight, on the A’s foot wedge.',
    'mid_narrow': 'The midpoint at 0.9 of the current’s width.',
    'mid_wide': 'The midpoint at 1.1 of the current’s width.',
    'beak': 'The midpoint with a shorter arm ending in the C’s beak -- the face sheared to vertical, a lip under it -- and a steeper crossing.',
    'upturn': 'A closed loop, smaller and with its point higher; the arm turning up into the stem’s right wedge; a steeper, plain-cut spur.',
    'round_bowl': 'The current’s open spiral with a bigger loop, the o’s round lower bowl and the arm on a plain pen cut.',
}

def dials_line(fn):
    """The dials a VARIANTS2 entry moved off `bred`'s defaults, mechanically."""
    import inspect
    defaults = {k: v.default for k, v in inspect.signature(ampersands.bred).parameters.items() if v.default is not inspect._empty}
    d = getattr(fn, 'dials', {})
    moved = [f'{k} {v}' for k, v in d.items() if defaults.get(k) != v]
    return 'moved: ' + ', '.join(moved) if moved else 'every dial at its default (the midpoint)'

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

def page(entries, out, png_dir=None, gen=1):
    """entries: [(name, ttf_path, measures[, heading, note])]; png_dir also
    saves every block. gen 2 writes the second page: its own title, the
    given heading per glyph (number, name, the dials moved, the 54 px
    counters and the bearings), the given note under it."""
    parts = []
    if png_dir: os.makedirs(png_dir, exist_ok=True)
    for e in entries:
        name, ttf, m = e[:3]; head = e[3] if len(e) > 3 else name; note = e[4] if len(e) > 4 else IDEAS.get(name, "")
        parts.append(f'<h2>{html.escape(head)}</h2><p>{html.escape(note)}</p>')
        if m:
            holes = ', '.join(f'{h:.0f}' for h in m['holes']) or 'none'
            ap = f' · aperture {m["aperture"]:.0f}' if m.get('aperture') else (' · no aperture under 120' if 'aperture' in m else '')
            parts.append(f'<p class="m">adv {m["adv"]:.0f} · ink {m["bbox"][2]-m["bbox"][0]:.0f} × {m["bbox"][3]-m["bbox"][1]:.0f} · contours {m["contours"]} · thinnest stroke {m["hair"]:.0f} · narrowest air {m["gap"]:.0f}{ap} · counters ⌀ {holes}</p>')
        a = block_caps(ttf, ['Dombey', '& Son'], 150)
        if png_dir: a.save(os.path.join(png_dir, f'{name}-a.png'))
        parts.append(f'<figure><img src="{proof.b64(a)}" width="{a.size[0]}" height="{a.size[1]}"><figcaption>Dombey & Son at 150 px, on two lines; baseline and cap height ruled</figcaption></figure>')
        b = proof.eink(ttf, 'Smith & Sons, Procter & Gamble, Marks & Spencer, & so on.')
        if png_dir: b.save(os.path.join(png_dir, f'{name}-b.png'))
        parts.append(f'<figure><img src="{proof.b64(b)}" width="{b.size[0]}" height="{b.size[1]}"><figcaption>13 pt on the 2x reader, four levels{"; Smith & Sons first, for the fit on both sides" if gen == 2 else ""}</figcaption></figure>')
    body = ''.join(parts)
    if gen == 2:
        title = 'Albo Ampersands II'
        intro = (f'A second generation of ampersands (2026-09-13), bred from two parents -- the shipping & and round 67’s teardrop -- by one parametric drawing whose dials span them; the parents first, then ten settings, each spliced into the reference font. '
                 f'Every image is PNG at native pixels, 750 px blocks shown at 375 CSS px. Each heading carries the dials moved off the midpoint, the white kept inside the top loop and the lower bowl on the four-level render at 54 px (13 pt on the 2x reader; “open” = its white joins the outside), and the sidebearings against the current &. '
                 f'Units: 1000 per em; the stem is {pen.S:.0f}, the pen’s hair {pen.HAIR:.1f}, the bowl’s hair {PR.bowl_hair():.1f}, 0.6 S = {0.6 * pen.S:.1f}; contrast {pen.CONTRAST:.2f}, descender {pen.DESC:.0f}, cut {pen.CUT_AMOUNT:.0f}, serif {pen.SERIF * 100:.0f}.')
    else:
        title = 'Albo Ampersands'
        intro = f'Ten florid ampersands drawn on Albo’s pen (2026-09-13), each spliced into the reference font; the shipping & first. Every image is PNG at native pixels, 750 px blocks shown at 375 CSS px. Units: 1000 per em; the stem is {pen.S:.0f}, the pen’s hair {pen.HAIR:.1f}, 0.6 S = {0.6 * pen.S:.1f}.'
    doc = f'''<title>{title}</title>
<style>:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:16px 10px 60px;font:15px/1.45 -apple-system,Arial,sans-serif}}main{{max-width:900px;margin:0 auto}}h1{{font-size:22px;margin:0 0 6px}}h2{{font-size:15px;margin:26px 0 4px;border-top:1px solid var(--rule);padding-top:10px}}
figure{{margin:0 0 10px}}figure img{{width:100%;max-width:375px;height:auto;image-rendering:pixelated;display:block;background:#fff}}figcaption{{font-size:11px;color:var(--soft);margin-top:2px}}
p{{max-width:64ch;color:var(--soft);font-size:13px;margin:4px 0 8px}}p.m{{font-size:11px}}</style>
<main><h1>{title}</h1><p>{intro}</p>{body}</main>'''
    open(out, 'w').write(doc); print(out, len(doc) // 1024, 'KB')

def fmt_counters(c):
    loop = 'open' if c['loop'] is None else f'{c["loop"]} px'
    bowl = 'open' if c['bowl'] is None else f'{c["bowl"]} px'
    return f'54 px white: loop {loop} · bowl {bowl}' + (f' · +{c["other"]} other' if c['other'] else '')

def run(out_dir, gen=1):
    os.makedirs(out_dir, exist_ok=True)
    ref_dir = os.path.join(out_dir, 'ref'); ref_path, W, rep = build.build(ref_dir, only=None)
    ref_ttf = os.path.join(out_dir, 'Albo-Medium.ttf'); shutil.copy(ref_path, ref_ttf)
    r = rep['&']; conts0 = geom.contours(build.draw('&', W)); m = measure(conts0); m['adv'] = r['adv']
    def show(tag, name, adv, lsb, m):
        at = lambda p: f'({p[0]:.0f},{p[1]:.0f})' if p else '-'
        ap = f' aperture {m["aperture"]:5.1f}' if m.get('aperture') else ''
        c54 = f' | {fmt_counters(m["c54"])} | lsb {m["lsb"]:.0f} rsb {m["rsb"]:.0f}' if 'c54' in m else ''
        print(f'{tag} {name:13s} adv {adv:6.1f} lsb {lsb:5.1f} contours {m["contours"]} hair {m["hair"]:5.1f} at {at(m["hair_at"])} gap {m["gap"]:5.1f} at {at(m["gap_at"])}{ap} holes {[round(h) for h in m["holes"]]}{c54}')
    if gen == 1:
        entries = [('current', ref_ttf, m)]; rows = [('current', m)]
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
    # ---- generation II: the two parents, then VARIANTS2
    def enrich(m, conts, ttf):
        m['aperture'] = aperture(conts); m['c54'] = name_counters(counters54(ttf))
        adv, lsb, rsb = bearings(ttf); m['lsb'], m['rsb'] = lsb, rsb; return m
    m = enrich(m, conts0, ref_ttf); cur = m
    bear = lambda m: f'lsb {m["lsb"]:.0f} · rsb {m["rsb"]:.0f}' + ('' if m is cur else f' (current {cur["lsb"]:.0f} · {cur["rsb"]:.0f})')
    entries = [('current', ref_ttf, m, f'Parent A — current: the shipping & (marks.g_ampersand) · {fmt_counters(m["c54"])} · {bear(m)}', IDEAS['current'])]
    rows = [('current', m)]; show('P1', 'current', r['adv'], r['lsb'], m)
    td_fn = dict(ampersands.VARIANTS)['teardrop']
    vpath, vr, conts = build_variant(td_fn, os.path.join(out_dir, 'var', 'teardrop'), '2-td')
    td_ttf = splice(ref_ttf, vpath, os.path.join(out_dir, 'Albo-amp2-teardrop.ttf'))
    m = enrich(measure(conts), conts, td_ttf); m['adv'] = vr['adv']
    entries.append(('teardrop', td_ttf, m, f'Parent B — teardrop: round 67’s #6 (amp_teardrop) · {fmt_counters(m["c54"])} · {bear(m)}', IDEAS['teardrop']))
    rows.append(('teardrop', m)); show('P2', 'teardrop', vr['adv'], vr['lsb'], m)
    for i, (name, fn) in enumerate(ampersands.VARIANTS2, 1):
        vpath, vr, conts = build_variant(fn, os.path.join(out_dir, 'var', f'2-{i:02d}'), f'2-{i:02d}')
        out_ttf = splice(ref_ttf, vpath, os.path.join(out_dir, f'Albo-amp2-{i:02d}.ttf'))
        m = enrich(measure(conts), conts, out_ttf); m['adv'] = vr['adv']
        head = f'{i}. {name} — {dials_line(fn)} · {fmt_counters(m["c54"])} · {bear(m)}'
        entries.append((name, out_ttf, m, head, IDEAS2.get(name, ''))); rows.append((name, m))
        show(f'{i:02d}', name, vr['adv'], vr['lsb'], m)
    page(entries, os.path.join(out_dir, 'albo-ampersands-2.html'), png_dir=os.path.join(out_dir, 'png'), gen=2)
    return rows

if __name__ == '__main__':
    args = [a for a in sys.argv[1:]]
    gen = int(args[args.index('--gen') + 1]) if '--gen' in args else 1
    out = [a for i, a in enumerate(args) if a != '--gen' and (i == 0 or args[i - 1] != '--gen')][0]
    run(out, gen=gen)
