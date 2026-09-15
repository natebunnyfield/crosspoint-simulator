"""What a real italic does to its CAPITALS, measured against its own roman.

    python3 cmp_italic_caps.py [<albo-regular.ttf> <albo-italic.ttf>]

Albo's italic shears its capitals out of the roman and redraws none of them
(round 105 redrew the lowercase only). The question this answers is what the
reference faces actually do, so the redraw is measured rather than invented.

Four measurements, each per capital and per face:

  WIDTH     advance over that face's OWN H-ink cap height, italic against
            roman. The unit cannot be the em (cap/em runs 0.60..0.75 across
            these faces) and it cannot be the italic's own cap height either,
            because several italics cut their capitals SHORTER than the
            roman's -- which is itself one of the findings, so it has to be
            measured, not divided out.
  CAP       italic cap height over roman cap height, in em units.
  SLANT     the capital I's (or H's) stem slope against the lowercase l's.
            A chancery capital is often uprighter than the lowercase beside
            it; whether that is true of TEXT italics is the question.
  SHAPE     the round-104 oblique test, run on capitals: shear the roman by
            the italic's own angle and take intersection-over-union with the
            italic. LOW means the letter was REDRAWN; high means it is the
            sheared roman and needs nothing but a width.

The faces are roman/italic PAIRS from one family only -- an italic can only
be compared with the roman it was cut for.
"""
import os, sys, math, string, statistics, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

R = os.path.expanduser('~/src/crosspoint-reader/lib/EpdFont')
D = f'{R}/scripts/downloaded_fonts'
L = f'{R}/local_fonts'

# roman / italic pairs, oldest model first. Every one is a text face whose
# italic descends from a chancery hand; the two Baroque-model faces
# (Fleischmann, Caledonia) are kept as a control group at the other end.
PAIRS = [
    ('Van den Keere',  f'{L}/VandenKeere-Regular.otf',  f'{L}/VandenKeere-Italic.otf'),
    ('Venetian 301',   f'{L}/Venetian301-Regular.otf',  f'{L}/Venetian301-Italic.otf'),
    ('Golden Cockerel',f'{L}/GoldenCockerel-Roman.ttf', f'{L}/GoldenCockerel-Italic.ttf'),
    ('Lutetia Nova',   f'{L}/LutetiaNova-Book.ttf',     f'{L}/LutetiaNova-BookItalic.ttf'),
    ('DTL Romulus',    f'{L}/DTLRomulus-Regular.otf',   f'{L}/DTLRomulus-Italic.otf'),
    ('Dante MT',       f'{L}/DanteMT-Regular.ttf',      f'{L}/DanteMT-Italic.ttf'),
    ('Warbler Text',   f'{L}/WarblerText-Regular.otf',  f'{L}/WarblerText-Italic.otf'),
    ('Coelacanth',     f'{D}/Coelacanth/Coelacanth.otf',f'{D}/Coelacanth/CoelacanthItalic.otf'),
    ('Junicode',       f'{D}/Junicode/Junicode-SemiCondMedium.ttf', f'{D}/Junicode/Junicode-SemiCondMediumItalic.ttf'),
    ('Accanthis',      f'{D}/Accanthis/AccanthisADFStdNo3-Regular.otf', f'{D}/Accanthis/AccanthisADFStdNo3-Italic.otf'),
    ('Domitian',       f'{D}/Domitian/Domitian-Roman.otf', f'{D}/Domitian/Domitian-Italic.otf'),
    # controls: Baroque, Scotch and screen models rather than chancery
    ('DTL Fleischmann',f'{L}/DTLFleischmann-Regular.ttf', f'{L}/DTLFleischmann-Italic.ttf'),
    ('Caledonia',      f'{L}/CaledoniaCC-Regular.ttf',  f'{L}/CaledoniaCC-Italic.ttf'),
    ('Edgar',          f'{L}/Edgar-Regular.ttf',        f'{L}/Edgar-Italic.ttf'),
    ('Times New Roman','/System/Library/Fonts/Supplemental/Times New Roman.ttf',
                       '/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf'),
    ('Georgia',        '/System/Library/Fonts/Supplemental/Georgia.ttf',
                       '/System/Library/Fonts/Supplemental/Georgia Italic.ttf'),
]
CHANCERY = ['Van den Keere', 'Venetian 301', 'Golden Cockerel', 'Lutetia Nova', 'DTL Romulus',
            'Dante MT', 'Warbler Text', 'Coelacanth', 'Junicode', 'Accanthis', 'Domitian']
LET = string.ascii_uppercase
PX = 400


# ------------------------------------------------------------------ metrics
def face(path):
    f = TTFont(path, fontNumber=0) if path.endswith('.ttc') else TTFont(path)
    gs = f.getGlyphSet(); cm = f.getBestCmap(); upem = f['head'].unitsPerEm
    def bounds(ch):
        if ord(ch) not in cm: return None
        bp = BoundsPen(gs); gs[cm[ord(ch)]].draw(bp); return bp.bounds
    cap = bounds('H')[3]
    adv = {c: f['hmtx'][cm[ord(c)]][0] for c in LET if ord(c) in cm}
    ink = {}
    for c in LET:
        b = bounds(c)
        if b: ink[c] = (b[2] - b[0], b[3] - b[1])
    return dict(cap=cap, upem=upem, adv=adv, ink=ink, bounds=bounds)


# ------------------------------------------------------------------- raster
def glyph_img(path, ch, shear=0.0, size=PX):
    ft = ImageFont.truetype(path, size); im = Image.new('L', (size * 3, size * 3), 0)
    ImageDraw.Draw(im).text((size, size * 2), ch, font=ft, fill=255, anchor='ls')
    a = np.asarray(im) > 128
    if shear:
        out = np.zeros_like(a)
        for y in range(a.shape[0]):
            dx = int(round((size * 2 - y) * shear))
            if dx == 0: out[y] = a[y]
            elif dx > 0: out[y, dx:] = a[y, :-dx]
            else: out[y, :dx] = a[y, -dx:]
        a = out
    ys, xs = np.where(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(ys) else None


def norm(img, H=300, W=None):
    """Height-normalised (the round-104 test), or box-normalised when W is
    given. The two answer different questions and BOTH are needed here: a
    height-only score falls when a letter merely narrows, which is exactly
    the change capitals make most, so it cannot by itself say whether a
    letter was redrawn."""
    if img is None: return None
    im = Image.fromarray((img * 255).astype(np.uint8))
    w = W if W else max(1, int(im.size[0] * H / im.size[1]))
    return np.asarray(im.resize((w, H), Image.LANCZOS)) > 127


def iou(a, b, reg=14):
    if a is None or b is None: return None
    W = max(a.shape[1], b.shape[1])
    pa = np.zeros((a.shape[0], W), bool); pa[:, :a.shape[1]] = a
    pb = np.zeros((b.shape[0], W), bool); pb[:, :b.shape[1]] = b
    best = 0.0
    for off in range(-reg, reg + 1):
        sb = np.roll(pb, off, axis=1); u = (pa | sb).sum()
        if u: best = max(best, (pa & sb).sum() / u)
    return best


def stem_slant(path, ch, lo=0.28, hi=0.72):
    """Degrees of slope of a letter's left ink edge between two heights.
    Uses the LEFT edge rather than the row mean: a capital with a serif or a
    bowl has ink that is not the stem, and the leftmost run at each row is
    the stem in I, H, l, E, F, B, P, D. The band is kept well inside the
    serifs -- at 0.15/0.85 an italic I's own bracketing walked the reading
    by two degrees."""
    a = glyph_img(path, ch)
    if a is None: return None
    h = a.shape[0]
    xs = []
    for f in (lo, hi):
        w = np.where(a[int(h * f)])[0]
        if not len(w): return None
        xs.append(w.min())
    return math.degrees(math.atan2(xs[0] - xs[1], h * (hi - lo)))


def cap_slant(path, letters='IHEFBPDL'):
    """The capitals' slope: the median over every capital with a plain left
    stem, because one letter can carry a swash or a flourish (Junicode's
    italic I reads four degrees off its own H)."""
    v = [stem_slant(path, c) for c in letters]
    v = [x for x in v if x is not None]
    return statistics.median(v) if v else None


def serif_spread(path, ch='I'):
    """A stem's foot width over its own width at mid height -- the serif
    family's spread. 1.0 is a sans; the roman figure and the italic figure
    of the same face are what matter, not the absolute."""
    a = glyph_img(path, ch)
    if a is None: return None
    h = a.shape[0]
    def run(y):
        w = np.where(a[y])[0]
        return (w.max() - w.min() + 1) if len(w) else 0
    mid = statistics.median([run(y) for y in range(int(h * 0.40), int(h * 0.60))])
    foot = max(run(y) for y in range(max(0, h - 4), h))
    return foot / mid if mid else None


# --------------------------------------------------------------------- main
def measure(name, roman, italic):
    fr, fi = face(roman), face(italic)
    ur, ui = fr['upem'], fi['upem']
    capr, capi = fr['cap'], fi['cap']
    ang = -TTFont(italic, fontNumber=0)['post'].italicAngle
    lc = stem_slant(italic, 'l')
    if abs(ang) < 0.5: ang = lc if lc else 0.0
    sh = math.tan(math.radians(ang))
    rows = {}
    for c in LET:
        if c not in fr['adv'] or c not in fi['adv']: continue
        wr = fr['adv'][c] / capr; wi = fi['adv'][c] / capi
        ir = fr['ink'][c][0] / capr; ii = fi['ink'][c][0] / capi
        gr = glyph_img(roman, c, shear=sh); gi = glyph_img(italic, c)
        shape = iou(norm(gr), norm(gi))
        shape_w = iou(norm(gr, W=260), norm(gi, W=260), reg=4)   # width normalised too
        rows[c] = dict(wr=wr, wi=wi, ratio=wi / wr, ink_r=ir, ink_i=ii, ink_ratio=ii / ir,
                       shape=shape, shape_w=shape_w)
    return dict(name=name, slant=ang, lc_slant=lc,
                cap_slant=cap_slant(italic),
                cap_slant_roman=cap_slant(roman),
                cap_ratio=(capi / ui) / (capr / ur),
                xh_ratio=None, serif_r=serif_spread(roman), serif_i=serif_spread(italic),
                rows=rows)


def main(albo_r=None, albo_i=None):
    out = []
    for nm, r, i in PAIRS:
        if not (os.path.exists(r) and os.path.exists(i)):
            print(f'MISSING {nm}', file=sys.stderr); continue
        out.append(measure(nm, r, i))
    if albo_r and albo_i and os.path.exists(albo_r) and os.path.exists(albo_i):
        out.append(measure('Albo TODAY', albo_r, albo_i))

    print(f'{"face":17s} {"slant":>6s} {"capI":>6s} {"lc l":>6s} {"cap h":>6s} '
          f'{"w med":>6s} {"ink med":>7s} {"serif R":>7s} {"serif I":>7s}')
    for f in out:
        rs = [v['ratio'] for v in f['rows'].values()]
        iks = [v['ink_ratio'] for v in f['rows'].values()]
        print(f'{f["name"]:17s} {f["slant"]:6.1f} {f["cap_slant"] or 0:6.1f} {f["lc_slant"] or 0:6.1f} '
              f'{f["cap_ratio"]:6.3f} {statistics.median(rs):6.3f} {statistics.median(iks):7.3f} '
              f'{f["serif_r"] or 0:7.2f} {f["serif_i"] or 0:7.2f}')

    ch = [f for f in out if f['name'] in CHANCERY]
    print(f'\nPER LETTER, italic advance / roman advance (each over its own cap height)')
    print(f'{"":3s} ' + ' '.join(f'{f["name"][:7]:>7s}' for f in ch) + f' {"MEDIAN":>7s} {"SHAPE":>6s} {"SHAPEw":>6s}')
    med, shp, shw = {}, {}, {}
    for c in LET:
        vals = [f['rows'][c]['ratio'] for f in ch if c in f['rows']]
        ss = [f['rows'][c]['shape'] for f in ch if c in f['rows'] and f['rows'][c]['shape'] is not None]
        sw = [f['rows'][c]['shape_w'] for f in ch if c in f['rows'] and f['rows'][c]['shape_w'] is not None]
        if not vals: continue
        med[c] = statistics.median(vals); shp[c] = statistics.median(ss); shw[c] = statistics.median(sw)
        print(f'{c:3s} ' + ' '.join(f'{f["rows"][c]["ratio"]:7.3f}' if c in f['rows'] else f'{"":7s}' for f in ch)
              + f' {med[c]:7.3f} {shp[c]:6.3f} {shw[c]:6.3f}')
    print(f'\nall-letter median width ratio {statistics.median(med.values()):.3f}, '
          f'median shape {statistics.median(shp.values()):.3f}, '
          f'width-normalised {statistics.median(shw.values()):.3f}')
    print('letters MOST redrawn (lowest WIDTH-NORMALISED score -- a real construction change):')
    print('  ' + '  '.join(f'{c} {v:.2f}' for c, v in sorted(shw.items(), key=lambda kv: kv[1])[:10]))
    print('letters LEAST redrawn (a sheared roman at the right width would do):')
    print('  ' + '  '.join(f'{c} {v:.2f}' for c, v in sorted(shw.items(), key=lambda kv: -kv[1])[:10]))
    print('narrowest (median width ratio): ' + '  '.join(f'{c} {v:.3f}' for c, v in sorted(med.items(), key=lambda kv: kv[1])[:8]))
    print('widest:                         ' + '  '.join(f'{c} {v:.3f}' for c, v in sorted(med.items(), key=lambda kv: -kv[1])[:8]))
    json.dump(dict(faces=out, med=med, shape=shp, shape_w=shw), open('italic_caps.json', 'w'), indent=1)
    return out, med, shp


if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else None
    b = sys.argv[2] if len(sys.argv) > 2 else None
    main(a, b)
