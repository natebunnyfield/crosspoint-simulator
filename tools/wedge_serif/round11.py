"""Round 11: the same letters (B5.9, the garalde end of round 10) assembled
by different TECHNIQUES. Owner 2026-09-12: 'take a pass at different ways to
assemble those characters. one arranges the shapes naively, one simulates an
expert calligraphic brush, another uses counterpunch metal type, do all
possible historical techniques, multiple versions of one technique if it
makes sense, then come up with many more experimental ways.'

Two kinds of technique live here. PEN MODELS replace alphabet2.outline (how a
centerline becomes ink); IMPRESSION MODELS are raster passes over the drawn
mask (how ink meets a surface). Every tile is rendered the same way: the
skeleton at 8x, the technique applied, then a lossless large image and the
13 pt four-level e-ink line.
"""
import base64, html, io, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round3, round9, round10, alphabet2 as A
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np

STRING = "Hamburgers in a fjord."
B59 = round10.steps()[-1][2]
ORIG_OUTLINE = A.outline

# ------------------------------------------------------------ pen models
def pen_translation(nib_scale=1.0, hair=0.12):
    """A true broad nib: the outline is the centerline shifted by the nib
    vector each way. Thin exactly where the stroke runs along the nib;
    terminals are the nib's own edge (a parallelogram cut)."""
    def outline(pts, pen, profile=None, cut0=None, cut1=None):
        nw = pen.stem * nib_scale
        vx, vy = math.cos(pen.stress) * nw / 2, math.sin(pen.stress) * nw / 2
        tans = A.tangents(pts); n = len(pts) - 1; L = []; R = []
        for i, (p, tn) in enumerate(zip(pts, tans)):
            f = profile(i / n) if profile else 1.0
            nx, ny = -tn[1], tn[0]; h = pen.stem * hair / 2
            L.append((p[0] + vx * f + nx * h, p[1] + vy * f + ny * h))
            R.append((p[0] - vx * f - nx * h, p[1] - vy * f - ny * h))
        return L + R[::-1]
    return outline

def pen_brush(pressure=0.45, entry=0.25):
    """An expert pointed brush: pressure swells the middle of every stroke and
    the entry and exit thin to a point; direction still counts, softly."""
    def outline(pts, pen, profile=None, cut0=None, cut1=None):
        tans = A.tangents(pts); n = len(pts) - 1; L = []; R = []
        for i, (p, tn) in enumerate(zip(pts, tans)):
            t = i / n
            env = (1 - pressure) + pressure * math.sin(math.pi * t) ** 0.6
            tip = min(1.0, t / entry, (1 - t) / entry) ** 0.5 if entry > 0 else 1.0
            th = pen.th(tn) * env * (0.25 + 0.75 * tip) * (profile(t) if profile else 1.0)
            nx, ny = -tn[1], tn[0]
            L.append((p[0] + nx * th / 2, p[1] + ny * th / 2)); R.append((p[0] - nx * th / 2, p[1] - ny * th / 2))
        return L + R[::-1]
    return outline

def pen_pointed(contrast=0.85):
    """Copperplate: a flexible pointed nib. Hairline everywhere, swelling on
    the downstrokes with pressure; ends taper to a point."""
    def outline(pts, pen, profile=None, cut0=None, cut1=None):
        tans = A.tangents(pts); n = len(pts) - 1; L = []; R = []
        hair = pen.stem * (1 - contrast)
        for i, (p, tn) in enumerate(zip(pts, tans)):
            t = i / n
            down = max(0.0, -tn[1]) ** 1.4
            tip = min(1.0, t / 0.18, (1 - t) / 0.18) ** 0.7
            th = (hair + (pen.stem * 1.15 - hair) * down) * (0.2 + 0.8 * tip) * (profile(t) if profile else 1.0)
            nx, ny = -tn[1], tn[0]
            L.append((p[0] + nx * th / 2, p[1] + ny * th / 2)); R.append((p[0] - nx * th / 2, p[1] - ny * th / 2))
        return L + R[::-1]
    return outline

def pen_constant(scale=1.0):
    """Compass and rule: every stroke the same width, as a constructed
    Renaissance alphabet or a monoline skeleton."""
    def outline(pts, pen, profile=None, cut0=None, cut1=None):
        tans = A.tangents(pts); L = []; R = []
        for p, tn in zip(pts, tans):
            th = pen.stem * scale; nx, ny = -tn[1], tn[0]
            L.append((p[0] + nx * th / 2, p[1] + ny * th / 2)); R.append((p[0] - nx * th / 2, p[1] - ny * th / 2))
        return L + R[::-1]
    return outline

def pen_rotating(sweep_deg=50):
    """Experimental: the nib ROTATES along every stroke, so the thick and
    thin trade places within one letter."""
    def outline(pts, pen, profile=None, cut0=None, cut1=None):
        tans = A.tangents(pts); n = len(pts) - 1; L = []; R = []
        for i, (p, tn) in enumerate(zip(pts, tans)):
            t = i / n; phi = math.atan2(tn[1], tn[0]); st = pen.stress + math.radians(sweep_deg) * (t - 0.5)
            th = pen.hair + (pen.stem - pen.hair) * abs(math.sin(phi - st)) ** 1.1
            th *= profile(t) if profile else 1.0; nx, ny = -tn[1], tn[0]
            L.append((p[0] + nx * th / 2, p[1] + ny * th / 2)); R.append((p[0] - nx * th / 2, p[1] - ny * th / 2))
        return L + R[::-1]
    return outline

def pen_ribbon(waves=2.5, depth=0.5):
    """Experimental: a twisted ribbon. Thickness breathes along the stroke on
    its own period, regardless of direction."""
    def outline(pts, pen, profile=None, cut0=None, cut1=None):
        tans = A.tangents(pts); n = len(pts) - 1; L = []; R = []
        for i, (p, tn) in enumerate(zip(pts, tans)):
            t = i / n; th = pen.th(tn) * ((1 - depth) + depth * abs(math.sin(math.pi * waves * t)))
            th *= profile(t) if profile else 1.0; nx, ny = -tn[1], tn[0]
            L.append((p[0] + nx * th / 2, p[1] + ny * th / 2)); R.append((p[0] - nx * th / 2, p[1] - ny * th / 2))
        return L + R[::-1]
    return outline

def pen_gravity(sag=0.6):
    """Experimental: ink is heavy. Every stroke thickens toward the baseline
    as if the wet letter had sagged."""
    def outline(pts, pen, profile=None, cut0=None, cut1=None):
        tans = A.tangents(pts); n = len(pts) - 1; L = []; R = []
        for i, (p, tn) in enumerate(zip(pts, tans)):
            t = i / n; g = 1 + sag * max(0.0, 1 - p[1] / 480.0)
            th = pen.th(tn) * g * (profile(t) if profile else 1.0); nx, ny = -tn[1], tn[0]
            L.append((p[0] + nx * th / 2, p[1] + ny * th / 2)); R.append((p[0] - nx * th / 2, p[1] - ny * th / 2))
        return L + R[::-1]
    return outline

def pen_lowpoly(every=7, seed=3):
    """Experimental: the outline keeps one vertex in `every`, so every curve
    is a few flat facets -- cut with shears, not drawn."""
    def outline(pts, pen, profile=None, cut0=None, cut1=None):
        poly = ORIG_OUTLINE(pts, pen, profile, cut0, cut1)
        keep = [q for i, q in enumerate(poly) if i % every == 0 or i == len(poly) - 1]
        return keep if len(keep) >= 3 else poly
    return outline

def pen_speed(fast=0.45):
    """Experimental: a pen whose thickness is its speed. Straight runs are
    fast and thin; the curves slow the hand and thicken. Curvature decides."""
    def outline(pts, pen, profile=None, cut0=None, cut1=None):
        tans = A.tangents(pts); n = len(pts) - 1; L = []; R = []
        for i, (p, tn) in enumerate(zip(pts, tans)):
            a = tans[max(0, i - 3)]; b = tans[min(n, i + 3)]
            curv = math.hypot(b[0] - a[0], b[1] - a[1])  # 0 on a straight
            th = pen.stem * (fast + (1 - fast) * min(1.0, curv * 2.2)) * (profile(i / n) if profile else 1.0)
            nx, ny = -tn[1], tn[0]
            L.append((p[0] + nx * th / 2, p[1] + ny * th / 2)); R.append((p[0] - nx * th / 2, p[1] - ny * th / 2))
        return L + R[::-1]
    return outline

# ------------------------------------------------------------ rendering
def draw_mask(p, text, em_px, ss, pen=None, param_over=None, fixed_adv=None, paper_holes=False):
    """The skeleton drawn at em_px * ss, as an L mask (255 = ink)."""
    pp = dict(p); pp.update(param_over or {})
    A.outline = pen or ORIG_OUTLINE
    try:
        if fixed_adv:
            polys = []; x = 0.0; c = A.ctx(pp)
            for ch in text:
                if ch == ' ': x += fixed_adv; continue
                fn = A.GLYPHS.get(ch) or A.GLYPHS.get(ch.lower())
                if not fn: continue
                gp = fn(c); xs = [q[0] for poly in gp for q in poly]; l, r = min(xs), max(xs)
                off = x + (fixed_adv - (r - l)) / 2 - l
                polys.extend([[(q[0] + off, q[1]) for q in poly] for poly in gp]); x += fixed_adv
            adv = x
        else:
            polys, adv = A.layout(pp, text)
    finally:
        A.outline = ORIG_OUTLINE
    scale = em_px * ss / 1000.0; top = pp["asc"] + 60
    W, H = int((adv + 80) * scale), int((top + pp["desc"] + 90) * scale)
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    for poly in polys:
        d.polygon([((x + 40) * scale, (top - y) * scale) for x, y in poly], fill=255)
    return im, scale

def quantize4(gray):
    px = gray.load(); out = Image.new("L", gray.size, 255); po = out.load()
    for y in range(gray.size[1]):
        for x in range(gray.size[0]):
            c = 1 - px[x, y] / 255.0
            po[x, y] = 255 if c < 0.108 else 200 if c < 0.42 else 96 if c < 0.812 else 0
    return out

def finish(mask, ss):
    """Ink mask at ss x -> gray image at 1x (255 paper, 0 ink)."""
    small = mask.resize((mask.width // ss, mask.height // ss), Image.BOX)
    return ImageChops.invert(small)

# ------------------------------------------------------------ impression models (raster)
def noise(shape, seed, blur=0):
    rng = np.random.default_rng(seed); n = rng.random(shape).astype(np.float32)
    im = Image.fromarray((n * 255).astype(np.uint8))
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im).astype(np.float32) / 255.0

def imp_none(mask, ss, scale): return mask

def imp_ink_spread(mask, ss, scale, spread=0.09, rnd=0.6):
    """Letterpress: the ink wicks out and every corner rounds."""
    d = int(spread * 88 * scale) | 1
    m = mask.filter(ImageFilter.MaxFilter(d)) if d > 1 else mask
    m = m.filter(ImageFilter.GaussianBlur(rnd * 88 * scale * 0.5))
    return m.point(lambda v: 255 if v >= 128 else 0)

def imp_squash(mask, ss, scale):
    """Letterpress, heavy impression: spread plus a gray halo where the
    paper was crushed around the ink (a four-level page can show it)."""
    core = imp_ink_spread(mask, ss, scale, 0.07, 0.5)
    halo = core.filter(ImageFilter.MaxFilter(int(0.16 * 88 * scale) | 1)).filter(ImageFilter.GaussianBlur(0.3 * 88 * scale))
    a = np.asarray(core).astype(np.float32); h = np.asarray(halo).astype(np.float32)
    return Image.fromarray(np.clip(np.maximum(a, h * 0.42), 0, 255).astype(np.uint8))

def imp_counterpunch(mask, ss, scale, swell=0.14, crisp=0.06):
    """Counterpunch metal type: the counters are struck first as their own
    crisp shapes, the outer form is filed and grows soft and full."""
    a = np.asarray(mask) > 127
    # enclosed background = holes
    bg = Image.fromarray((~a).astype(np.uint8) * 255)
    ff = bg.copy(); ImageDraw.floodfill(ff, (0, 0), 128)
    ffa = np.asarray(ff); holes = (ffa == 255)
    holes_im = Image.fromarray(holes.astype(np.uint8) * 255)
    holes_im = holes_im.filter(ImageFilter.MaxFilter(int(crisp * 88 * scale) | 1))  # counters cut a little larger, crisp
    outer = mask.filter(ImageFilter.MaxFilter(int(swell * 88 * scale) | 1)).filter(ImageFilter.GaussianBlur(0.25 * 88 * scale)).point(lambda v: 255 if v >= 128 else 0)
    o = np.asarray(outer) > 127; h = np.asarray(holes_im) > 127
    return Image.fromarray(((o & ~h) * 255).astype(np.uint8))

def imp_woodcut(mask, ss, scale, amp=0.35, seed=7):
    """Wood type: the knife leaves every edge a little ragged and the counters a
    little squarer."""
    n = noise((mask.height, mask.width), seed, blur=1.2 * scale * 8)
    b = np.asarray(mask.filter(ImageFilter.GaussianBlur(0.12 * 88 * scale))).astype(np.float32) / 255.0
    return Image.fromarray(((b + (n - 0.5) * amp) > 0.5).astype(np.uint8) * 255)

def imp_weathered(mask, ss, scale, seed=11, loss=0.55):
    """Experimental: rain on a painted sign; ink lost in flakes from the edges in."""
    n = noise((mask.height, mask.width), seed, blur=2.0 * scale * 8)
    dist = np.asarray(mask.filter(ImageFilter.GaussianBlur(0.35 * 88 * scale))).astype(np.float32) / 255.0
    keep = (dist > 0.5) & ((n * 0.9 + dist * 0.4) > loss)
    return Image.fromarray((keep * 255).astype(np.uint8))

def imp_stencil(mask, ss, scale, bar=0.24):
    """Stencil: bridges keep the counters attached; two bands of paper cut
    through everything at the heights a stencil cutter would choose."""
    a = np.asarray(mask).copy(); H = mask.height
    top = int((B59["asc"] + 60 - B59["xh"] * 0.74) * scale); bot = int((B59["asc"] + 60 - B59["xh"] * 0.28) * scale)
    w = int(bar * 88 * scale)
    for y0 in (top, bot):
        a[max(0, y0 - w // 2):y0 + w // 2, :] = 0
    return Image.fromarray(a)

def imp_pixel(mask, ss, scale, grid_em=18):
    """The pixel era: the letter at 18 px per em, one bit, blown back up."""
    f = (88 * scale) / (88 * grid_em / 1000.0)  # hi-res px per grid px
    W, H = max(1, int(mask.width / f)), max(1, int(mask.height / f))
    small = mask.resize((W, H), Image.BOX).point(lambda v: 255 if v >= 128 else 0)
    return small.resize(mask.size, Image.NEAREST)

def imp_phototype(mask, ss, scale):
    """1970s phototype: the light bloomed a little, every corner is soft."""
    return mask.filter(ImageFilter.GaussianBlur(0.1 * 88 * scale)).point(lambda v: 255 if v >= 118 else 0)

def imp_halftone(mask, ss, scale, pitch=0.28):
    """Experimental: the stroke is a screen of dots whose size follows the
    ink's own weight."""
    b = np.asarray(mask.filter(ImageFilter.GaussianBlur(0.2 * 88 * scale))).astype(np.float32) / 255.0
    H, W = b.shape; P = max(2, int(pitch * 88 * scale))
    yy, xx = np.mgrid[0:H, 0:W]; cy = (yy // P) * P + P / 2; cx = (xx // P) * P + P / 2
    r = np.hypot(yy - cy, xx - cx)
    out = r < (P * 0.62) * np.sqrt(np.clip(b, 0, 1))
    return Image.fromarray((out * 255).astype(np.uint8))

def imp_stitch(mask, ss, scale, pitch=0.22):
    """Experimental: embroidered; the ink is a run of stitches along the stroke."""
    H, W = mask.height, mask.width; P = max(2, int(pitch * 88 * scale))
    yy, xx = np.mgrid[0:H, 0:W]
    lane = ((xx + yy * 0.35) % P) / P
    a = np.asarray(mask) > 127
    out = a & ((lane > 0.18) & (lane < 0.86))
    return Image.fromarray((out * 255).astype(np.uint8))

def imp_misregister(mask, ss, scale, dx=0.06):
    """Two-color print, misregistered: a gray impression sits a little off the
    black one (the four levels can carry it)."""
    a = np.asarray(mask).astype(np.float32)
    off = int(dx * 88 * scale)
    g = np.zeros_like(a); g[:, off:] = a[:, :-off] if off > 0 else a
    return Image.fromarray(np.maximum(a, g * 0.45).astype(np.uint8))

def imp_ghost(mask, ss, scale):
    """The reader's own defect: the previous page's ghost under this one."""
    a = np.asarray(mask).astype(np.float32); dy = int(0.18 * 88 * scale) * 3
    g = np.zeros_like(a); g[:-dy, :] = a[dy:, :]
    return Image.fromarray(np.maximum(a, g * 0.3).astype(np.uint8))

def imp_incised(mask, ss, scale):
    """Stone, V-cut: only the walls of the groove catch light -- the letter is
    its own outline with a hairline of shadow inside."""
    er = mask.filter(ImageFilter.MinFilter(int(0.18 * 88 * scale) | 1))
    wall = ImageChops.subtract(mask, er)
    groove = er.filter(ImageFilter.MinFilter(int(0.3 * 88 * scale) | 1))
    core = ImageChops.subtract(er, groove)
    a = np.asarray(wall).astype(np.float32); c = np.asarray(core).astype(np.float32)
    return Image.fromarray(np.maximum(a, c * 0.35).astype(np.uint8))

def imp_dither(mask, ss, scale):
    """The panel's own process: the antialiased letter carried as an ordered
    2-bit dither instead of four flat levels."""
    b = np.asarray(mask.filter(ImageFilter.GaussianBlur(0.25 * 88 * scale))).astype(np.float32) / 255.0
    H, W = b.shape; bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    cell = int(max(1, 0.09 * 88 * scale))
    yy, xx = np.mgrid[0:H, 0:W]; th = bayer[(yy // cell) % 4, (xx // cell) % 4]
    return Image.fromarray(((b > th) * 255).astype(np.uint8))

def imp_blob(mask, ss, scale):
    """Experimental: over-smoothed; every join melts, like type cast in wax."""
    return mask.filter(ImageFilter.GaussianBlur(0.32 * 88 * scale)).point(lambda v: 255 if v >= 128 else 0)

def imp_scissors(mask, ss, scale, seed=5):
    """Experimental: cut from paper with scissors; straight snips, a little off."""
    a = np.asarray(mask) > 127
    H, W = a.shape; rng = np.random.default_rng(seed)
    out = a.copy()
    for _ in range(int(W / (0.4 * 88 * scale))):
        x = int(rng.integers(0, W)); y = int(rng.integers(0, H)); ang = rng.uniform(0, math.pi)
        L = int(0.5 * 88 * scale); dx, dy = math.cos(ang), math.sin(ang)
        for k in range(-L, L):
            xi, yi = int(x + dx * k), int(y + dy * k)
            if 0 <= xi < W and 0 <= yi < H and rng.random() < 0.35: out[yi, xi] = False
    return Image.fromarray((out * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))

# ------------------------------------------------------------ the bank
# (key, group, title, blurb, pen, impression, param overrides, fixed advance)
BANK = [
 ("H01", "historical", "Naive assembly", "the first model: shapes butted, the o with its seam, square ends", None, imp_none, dict(naive_o=True, raw_joins=True, cut_deg=0, fillet=0.0), None),
 ("H02", "historical", "Broad nib, held at 26°", "a true translation pen: the outline is the nib itself, thin where the stroke runs along it", pen_translation(1.0), imp_none, dict(), None),
 ("H03", "historical", "Broad nib, held at 40°", "the same nib, steeper; the thicks move to the diagonals", pen_translation(1.0), imp_none, dict(stress=40), None),
 ("H04", "historical", "Expert brush", "pointed brush: pressure swells the middle of every stroke, entry and exit taper to a point", pen_brush(0.45, 0.25), imp_none, dict(), None),
 ("H05", "historical", "Expert brush, light hand", "the same brush with less pressure and quicker entries", pen_brush(0.3, 0.15), imp_none, dict(stem=76), None),
 ("H06", "historical", "Pointed pen (copperplate)", "hairlines with swelling downstrokes", pen_pointed(0.85), imp_none, dict(), None),
 ("H07", "historical", "Counterpunch metal type", "counters struck crisp and a little large, the outer form filed full and soft", None, imp_counterpunch, dict(), None),
 ("H08", "historical", "Counterpunch, softer file", "more swell outside, the same counters", None, lambda m, s, sc: imp_counterpunch(m, s, sc, 0.22, 0.05), dict(), None),
 ("H09", "historical", "Letterpress, ink spread", "the type printed on soft paper: ink wicks, corners round", None, imp_ink_spread, dict(), None),
 ("H10", "historical", "Letterpress, heavy impression", "spread plus the crushed-paper halo", None, imp_squash, dict(), None),
 ("H11", "historical", "Wood type", "the knife: ragged edges, squarer counters", None, imp_woodcut, dict(stem=100, contrast=0.35), None),
 ("H12", "historical", "Stone, V-cut", "incised: the groove's walls and a shadow in the trough", None, imp_incised, dict(stem=104, contrast=0.4), None),
 ("H13", "historical", "Constructed (compass and rule)", "constant-width strokes, circular bowls, the Renaissance drawing-board letter", pen_constant(0.95), imp_none, dict(bowl_k=2.0, contrast=0.0), None),
 ("H14", "historical", "Stencil", "two bridges keep every counter attached", None, imp_stencil, dict(stem=100), None),
 ("H15", "historical", "Typewriter", "monospaced on a 560-unit cell, the ribbon's halo", None, imp_phototype, dict(stem=90, contrast=0.3, wedge_len=0.9, wedge_depth=1.0, fillet=0.0), 560),
 ("H16", "historical", "Phototype, 1970s", "light bloomed through the negative; tight fit", None, imp_phototype, dict(fit=0.55), None),
 ("H17", "historical", "Pixel era, 18 px", "one bit on an 18 px em, blown back up", None, imp_pixel, dict(), None),
 ("H18", "historical", "Ordered dither", "the panel's own 2-bit process, Bayer instead of flat levels", None, imp_dither, dict(), None),
 ("X01", "experimental", "Rotating nib", "the nib turns 50° along each stroke; thick and thin trade places inside a letter", pen_rotating(50), imp_none, dict(), None),
 ("X02", "experimental", "Rotating nib, wide sweep", "a 110° turn", pen_rotating(110), imp_none, dict(), None),
 ("X03", "experimental", "Ribbon", "a twisted ribbon: thickness breathes on its own period", pen_ribbon(2.5, 0.5), imp_none, dict(), None),
 ("X04", "experimental", "Ribbon, fast twist", "five waves per stroke", pen_ribbon(5, 0.6), imp_none, dict(), None),
 ("X05", "experimental", "Gravity", "wet ink sags: every stroke heavier toward the baseline", pen_gravity(0.6), imp_none, dict(), None),
 ("X06", "experimental", "Speed pen", "thickness is speed: straights fast and thin, curves slow and thick", pen_speed(0.45), imp_none, dict(), None),
 ("X07", "experimental", "Low-poly", "one vertex in seven; curves as facets", pen_lowpoly(7), imp_none, dict(), None),
 ("X08", "experimental", "Low-poly, coarser", "one in eleven", pen_lowpoly(11), imp_none, dict(), None),
 ("X09", "experimental", "Weathered", "a painted sign after the rain: flakes lost from the edges in", None, imp_weathered, dict(stem=100), None),
 ("X10", "experimental", "Halftone stroke", "the stroke as a dot screen whose dots follow the ink's weight", None, imp_halftone, dict(stem=110), None),
 ("X11", "experimental", "Stitched", "embroidered: a run of stitches along the stroke", None, imp_stitch, dict(stem=110), None),
 ("X12", "experimental", "Misregistered two-color", "a gray impression a little off the black", None, imp_misregister, dict(), None),
 ("X13", "experimental", "Ghosted", "the previous page under this one, the reader's own defect made a feature", None, imp_ghost, dict(), None),
 ("X14", "experimental", "Wax cast", "over-smoothed; every join melts", None, imp_blob, dict(), None),
 ("X15", "experimental", "Scissors", "cut from paper, straight snips, a little off", None, imp_scissors, dict(stem=104), None),
 ("X16", "experimental", "Brush, then letterpress", "the expert brush printed on soft paper", pen_brush(0.45, 0.25), imp_ink_spread, dict(), None),
 ("X17", "experimental", "Counterpunch, then woodcut knife", "metal counters, wood edges", None, lambda m, s, sc: imp_woodcut(imp_counterpunch(m, s, sc), s, sc, 0.25), dict(), None),
 ("X18", "experimental", "Pointed pen, then pixels", "copperplate on an 18 px em", pen_pointed(0.85), imp_pixel, dict(), None),
 ("X19", "experimental", "Naive, then stencil", "the first model with bridges", None, imp_stencil, dict(naive_o=True, raw_joins=True, cut_deg=0, fillet=0.0), None),
 ("X20", "experimental", "Gravity, then halftone", "sagging ink as a dot screen", pen_gravity(0.6), imp_halftone, dict(stem=108), None),
]

def render(entry, em_px, ss):
    key, group, title, blurb, pen, imp, over, fixed = entry
    mask, scale = draw_mask(B59, STRING, em_px, ss, pen=pen, param_over=over, fixed_adv=fixed)
    mask = imp(mask, ss, scale)
    return finish(mask, ss)

def b64(im):
    buf = io.BytesIO(); im.save(buf, format="PNG"); return base64.b64encode(buf.getvalue()).decode()

def page():
    tiles = []
    for entry in BANK:
        key, group, title, blurb = entry[:4]
        big = render(entry, 150, 4)
        ek = quantize4(render(entry, round3.EM_PX, 8)); mag = ek.resize((ek.width * 2, ek.height * 2), Image.NEAREST)
        tiles.append(f'''<figure class="opt {group}">
  <img class="big" src="data:image/png;base64,{b64(big)}" width="{big.width}" height="{big.height}" alt="">
  <div class="eink"><img src="data:image/png;base64,{b64(mag)}" width="{mag.width}" height="{mag.height}" alt=""></div>
  <figcaption><span class="num">{key}</span> <b>{html.escape(title)}</b><span class="blurb">{html.escape(blurb)} · large image 150 px em, lossless; e-ink line 13 pt at 2x, four levels, 2x NEAREST</span></figcaption>
</figure>''')
    return f'''<title>Hamburgers by Technique</title>
<style>
:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}
:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:20px 14px 60px;font:15px/1.45 -apple-system,"Helvetica Neue",Arial,sans-serif}}
main{{max-width:1180px;margin:0 auto}} h1{{font-size:24px;margin:0 0 4px}}
.lede{{color:var(--soft);max-width:66ch;margin:0 0 22px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:22px 26px}}
.opt{{margin:0;border-top:1px solid var(--rule);padding-top:12px}}
.opt.experimental{{border-top-color:var(--soft)}}
.big{{display:block;max-width:100%;height:auto;background:#fff}}
.eink{{overflow-x:auto;margin-top:6px}} .eink img{{display:block;image-rendering:pixelated;image-rendering:crisp-edges;background:#F9F3E9;max-width:none}}
figcaption{{margin-top:6px;font-size:13px}} .num{{display:inline-block;min-width:3.5ch;color:var(--soft);margin-right:6px}}
.blurb{{display:block;color:var(--soft)}}
</style>
<main>
<h1>Hamburgers by Technique</h1>
<p class="lede">Round 11. One design (B5.9) assembled thirty-eight ways. H01–H18 are historical techniques as pen models and impression models: naive assembly, the broad nib at two angles, the expert brush at two pressures, the pointed pen, counterpunch metal type twice, letterpress twice, wood type, incised stone, the constructed letter, stencil, typewriter, phototype, the pixel era, the panel's own dither. X01–X20 are techniques that have not been done: rotating nib, ribbon, gravity, speed pen, low-poly, weathered, halftone stroke, stitched, misregistered, ghosted, wax cast, scissors, and crosses between techniques. The large image is a lossless 150 px em; the strip below is the same line at 13 pt on four-level e-ink.</p>
<div class="grid">{''.join(tiles)}</div>
</main>'''

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(out, "hamburgers-technique.html"), "w").write(page())
    for key in ("H04", "H07", "X01", "X10"):
        e = [b for b in BANK if b[0] == key][0]; render(e, 150, 4).save(os.path.join(out, f"tech_{key}.png"))
    print("ok", len(BANK))
