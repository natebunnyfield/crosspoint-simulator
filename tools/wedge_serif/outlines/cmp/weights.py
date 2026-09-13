"""Albo's lighter weights: calibrate against industry norms, build, check, prove.

Owner (2026-09-13): "make thinner versions (calibrate against industry norms
(100 200 300 400) if we consider this to be 500". So the shipping Albo --
stem 84 on a 429 x-height, contrast 0.95 -- is the **500 (Medium)**, and this
module derives 400 / 300 / 200 / 100 from what real families actually do at
those weight classes rather than from a guess.

Four stages, each a subcommand (or `all`):

    cd tools/wedge_serif
    PYTHON_GIL=0 python3 -W ignore -m outlines.cmp.weights all <out_dir>

1. `calibrate` -- every font on this machine whose family spans a real weight
   range (>= 3 named weights reaching 350 or lighter, or an fvar wght axis) is
   measured: the l's stem waist over the x-height band, and the o's thin/thick.
   Ratios are taken against the family's OWN 500 (the anchor the owner named);
   a family with no 500 is anchored on its 400 and reported as such.
2. `derive` -- Albo's stem per weight = 84 x the median stem ratio. Its
   contrast comes from the same table's thin/thick trend, through the one
   identity that makes it mechanical: `primitives.BOWL['hair'] = 1 - 0.5c`
   with `max` 1.00, so the o's thin/thick IS `1 - 0.5c` (0.525 at the shipping
   0.95, and the guide's measured 1.4:1 at the old 0.60 confirms it).
3. `build` -- one `outlines.build` subprocess per weight with FJORD_STEM /
   FJORD_CONTRAST in the environment (pen.py reads them at import), then
   fontTools sets styleName and OS/2.usWeightClass, which the builder does not.
4. `topology` + `page` -- contour counts per glyph against the 500 (the check
   the variable font uses), and a mobile proof page.

Nothing here writes into fonts/rebuild/: today's `Albo-Regular.ttf` IS the 500
and must not be overwritten by the 400 this module builds under that name.
"""
import os, sys, io, json, math, base64, html, glob, shutil, statistics, subprocess, tempfile, collections

HERE = os.path.dirname(os.path.abspath(__file__))
WEDGE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, WEDGE)

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont, TTCollection

BIG = 1200              # px em for the stroke raster
EINK_PX = 54            # 13 pt on the 2x reader
HAIR_FLOOR = 6.0        # pen.HAIR_FLOOR, restated so calibrate() needs no build import

# ---------------------------------------------------------------- calibration

FONT_DIRS = ['/System/Library/Fonts', '/System/Library/Fonts/Supplemental', '/Library/Fonts',
             os.path.expanduser('~/Library/Fonts'),
             os.path.expanduser('~/src/crosspoint-reader/lib/EpdFont/local_fonts')]
# ALBO_REF_DIR: colon-separated extra directories (the scratchpad's wedge/ref,
# which carries Cheltenham Classic's Regular/Medium/Bold and EB Garamond's
# variable wght -- the two serif families here with a real 400->500 step)
FONT_DIRS += [d for d in os.environ.get('ALBO_REF_DIR', '').split(':') if d]

# Families whose Latin is a placeholder or a display face, or whose "weights"
# are not a designed ladder -- excluded with the reason, so the exclusion is
# reviewable rather than invisible.
SKIP_FAMILIES = {
    'Songti SC': 'CJK; the Latin is a secondary set',
    'Songti TC': 'CJK; the Latin is a secondary set',
    'Hiragino Sans': 'CJK; W0..W9 is not the 100..900 ladder',
    '.Hiragino Kaku Gothic Interface': 'system-internal duplicate',
    '.Apple SD Gothic NeoI': 'system-internal duplicate',
    '.Arial Hebrew Desk Interface': 'system-internal duplicate',
    '.Geeza Pro Interface': 'system-internal duplicate',
    'Arial Hebrew': 'Hebrew face; Latin is a secondary set',
    'Arial Hebrew Scholar': 'Hebrew face; Latin is a secondary set',
    'Copperplate': 'display face, no true lowercase',
    'American Typewriter': 'the ladder mixes Condensed and normal widths',
    'Avenir Next Condensed': 'a width, not a second weight ladder (Avenir Next covers it)',
    'Noto Sans Zawgyi': 'duplicate of Noto Sans Myanmar',
    'Sukhumvit Set': 'Thai face; Latin is a secondary set',
    'Thonburi': 'Thai face; Latin is a secondary set',
    '.SF Compact': 'the same design as System Font (SF Pro) at another width',
    '.SF Compact Rounded': 'the same design as System Font, rounded',
    '.SF NS Rounded': 'the same design as System Font, rounded',
    '.SF Camera': 'the same design as System Font, an interface cut',
    '.SF NS Mono': 'monospaced; its stem ladder is width-constrained',
    'Kohinoor Bangla': 'the same Latin as Kohinoor Devanagari',
    'Kohinoor Telugu': 'the same Latin as Kohinoor Devanagari',
    'ITF Devanagari Marathi': 'the same Latin as ITF Devanagari',
    'Damascus': 'Arabic face; the Latin l and o do not measure',
    '.Damascus PUA': 'Arabic face; the Latin l and o do not measure',
}
CLASSES = (100, 200, 300, 400, 500)   # the classes the owner named, plus the anchor


def _runs(seq, thresh=128):
    out, start = [], None
    for i, v in enumerate(seq):
        if v < thresh and start is None: start = i
        elif v >= thresh and start is not None: out.append((start, i - start)); start = None
    if start is not None: out.append((start, len(seq) - start))
    return out


def _runs_bool(mask):
    """(start, length) of True runs in a 1-D boolean array."""
    import numpy as np
    m = np.asarray(mask).astype(np.int8)
    d = np.diff(np.concatenate(([0], m, [0])))
    starts = np.flatnonzero(d == 1); ends = np.flatnonzero(d == -1)
    return list(zip(starts.tolist(), (ends - starts).tolist()))


def _render(path, index, ch, px):
    f = ImageFont.truetype(path, px, index=index)
    asc, desc = f.getmetrics()
    adv = f.getlength(ch)
    im = Image.new('L', (max(1, int(adv)) + 2 * px // 3, asc + desc), 255)
    ImageDraw.Draw(im).text((px // 3, asc), ch, font=f, fill=0, anchor='ls')
    return im, asc


def measure(path, index=0):
    """stem (the l's waist), xh, o thick and thin, and the n's advance -- all
    in font units (upm-normalized). Raster at BIG px em, so a unit is
    upm/BIG px; at upm 1000 that is 0.83 units of quantization."""
    import numpy as np
    tt = TTFont(path, fontNumber=index if path.lower().endswith('.ttc') else -1, lazy=True)
    upm = tt['head'].unitsPerEm
    u = upm / BIG                                     # units per raster pixel

    imx, ascx = _render(path, index, 'x', BIG)
    ax = np.asarray(imx) < 128
    rows_with_ink = np.flatnonzero(ax.any(axis=1))
    if not len(rows_with_ink): raise ValueError('no x')
    xh = (ascx - int(rows_with_ink[0])) * u

    def waist(ch, lo=0.30, hi=0.70):
        im, asc = _render(path, index, ch, BIG)
        a = np.asarray(im) < 128
        widths = []
        for frac in [lo + (hi - lo) * i / 12 for i in range(13)]:
            y = asc - int(xh * frac / u)
            if not (0 <= y < a.shape[0]): continue
            r = _runs_bool(a[y])
            if r: widths.append(max(L for _, L in r))
        return statistics.median(widths) * u if widths else 0.0

    stem = waist('l')
    if stem <= 0: stem = waist('i')

    # the o: thick = the mean of the two side runs at mid x-height; thin = the
    # mean of the top and bottom vertical runs down the bowl's centre column
    imo, asco = _render(path, index, 'o', BIG)
    ao = np.asarray(imo) < 128
    yo = asco - int(xh * 0.5 / u)
    thick = thin = 0.0
    if 0 <= yo < ao.shape[0]:
        ro = _runs_bool(ao[yo])
        if len(ro) >= 2:
            thick = (ro[0][1] + ro[-1][1]) / 2 * u
            cx = (ro[0][0] + ro[-1][0] + ro[-1][1]) // 2
            vr = _runs_bool(ao[:, cx])
            if len(vr) >= 2: thin = (vr[0][1] + vr[-1][1]) / 2 * u
    nadv = ImageFont.truetype(path, BIG, index=index).getlength('n') * u
    return dict(stem=stem, xh=xh, o_thick=thick, o_thin=thin, n_adv=nadv, upm=upm)


def _static_families():
    fam = collections.defaultdict(dict)
    for d in FONT_DIRS:
        for p in sorted(glob.glob(d + '/*')):
            if not p.lower().endswith(('.ttf', '.otf', '.ttc')): continue
            try:
                fonts = TTCollection(p, lazy=True).fonts if p.lower().endswith('.ttc') else [TTFont(p, lazy=True)]
            except Exception:
                continue
            for i, f in enumerate(fonts):
                try:
                    if 'fvar' in f: continue
                    n = f['name']; family = n.getDebugName(16) or n.getDebugName(1) or '?'
                    sub = n.getDebugName(17) or n.getDebugName(2) or ''
                    if 'talic' in sub or 'blique' in sub: continue
                    if 'ondensed' in sub or 'arrow' in sub: continue
                    w = f['OS/2'].usWeightClass
                    if w in fam[family] and 'egular' not in sub and 'oman' not in sub: continue
                    fam[family][w] = (p, i, sub)
                except Exception:
                    pass
    out = {}
    for k, v in fam.items():
        if k in SKIP_FAMILIES: continue
        allw = sorted(v); ws = sorted(w for w in v if w in CLASSES)
        # either a real weight ladder reaching 350 or lighter, or at least the
        # 400 -> 500 step the owner's anchor needs (Cheltenham Classic, Dante)
        if (len(allw) >= 3 and min(allw) <= 350 and any(w >= 400 for w in allw)) or (400 in ws and 500 in ws):
            out[k] = v
    return out


def _variable_sources():
    """Variable fonts whose wght axis is a designed ladder. Instances are cut
    with fontTools' instancer into a temp dir."""
    cands = ['/System/Library/Fonts/SFNS.ttf', '/System/Library/Fonts/NewYork.ttf',
             os.path.expanduser('~/src/crosspoint-reader/lib/EpdFont/local_fonts/WarblerVariable-Roman.ttf')]
    for d in FONT_DIRS:
        cands += sorted(glob.glob(d + '/*.ttf')) + sorted(glob.glob(d + '/*.otf'))
    out = {}
    for p in cands:
        if not os.path.exists(p): continue
        try:
            f = TTFont(p, lazy=True)
            if 'fvar' not in f: continue
            ax = {a.axisTag: a for a in f['fvar'].axes}
            if 'wght' not in ax: continue
            nm = f['name']
            sub = nm.getDebugName(17) or nm.getDebugName(2) or ''
            if 'talic' in sub or 'blique' in sub or 'talic' in os.path.basename(p): continue
            name = nm.getDebugName(16) or nm.getDebugName(1)
            if name in out: continue          # the roman file wins over any later sibling
            out[name] = (p, ax['wght'].minValue, ax['wght'].maxValue)
        except Exception:
            pass
    return out


def calibrate(out_dir):
    from fontTools.varLib import instancer
    rows = []          # (family, kind, weight, path, stem, xh, thick, thin, nadv)
    tmp = os.path.join(out_dir, '_inst'); os.makedirs(tmp, exist_ok=True)

    for family, v in sorted(_static_families().items()):
        for w in CLASSES:
            if w not in v: continue
            p, i, sub = v[w]
            try:
                m = measure(p, i)
            except Exception as e:
                print(f'  ! {family} {w}: {e}'); continue
            rows.append(dict(family=family, kind='static', weight=w, path=p, style=sub, **m))

    for family, (p, lo, hi) in sorted(_variable_sources().items()):
        base = TTFont(p)
        for w in CLASSES:
            if not (lo <= w <= hi): continue
            q = os.path.join(tmp, f'{family.replace(" ", "")}-{w}.ttf')
            if not os.path.exists(q):
                f = TTFont(p)
                loc = {'wght': float(w)}
                for a in f['fvar'].axes:
                    if a.axisTag == 'opsz': loc['opsz'] = min(max(15.0, a.minValue), a.maxValue)
                instancer.instantiateVariableFont(f, loc, inplace=True, updateFontNames=False)
                f.save(q)
            try:
                m = measure(q)
            except Exception as e:
                print(f'  ! {family} {w}: {e}'); continue
            rows.append(dict(family=family, kind='variable', weight=w, path=p, style=f'wght {w}', **m))
        del base

    # ratios against the family's own 500, or its 400 when it has no 500
    per = collections.defaultdict(dict)
    for r in rows: per[r['family']][r['weight']] = r
    for fam, ws in per.items():
        anchor = 500 if 500 in ws else (400 if 400 in ws else max(ws))
        for w, r in ws.items():
            r['anchor'] = anchor
            r['stem_ratio'] = r['stem'] / ws[anchor]['stem'] if ws[anchor]['stem'] else 0.0
            r['contrast'] = (r['o_thin'] / r['o_thick']) if r['o_thick'] else 0.0
            a = ws[anchor]
            ac = (a['o_thin'] / a['o_thick']) if a['o_thick'] else 0.0
            r['contrast_ratio'] = (r['contrast'] / ac) if ac else 0.0
            r['width_ratio'] = (r['n_adv'] / r['xh']) / (a['n_adv'] / a['xh']) if a['xh'] and a['n_adv'] else 0.0
    json.dump(rows, open(os.path.join(out_dir, 'calibration.json'), 'w'), indent=1)
    print(f'{len(rows)} instances measured across {len(per)} families -> calibration.json')
    return rows


# ------------------------------------------------------------------- deriving

ALBO_500 = dict(stem=84.0, contrast=0.95, xh=429.0, serif=92.0, width=100.0)
NAMES = {100: 'Thin', 200: 'ExtraLight', 300: 'Light', 400: 'Regular', 500: 'Medium'}


def usable(rows):
    """Drop what cannot be calibrated against, each with its reason:
    a family whose LATIN does not move across the ladder (a non-Latin face
    carrying one shared Latin -- the Noto script families, SF's script cuts),
    and any instance whose o gave no measurable thick or thin."""
    per = collections.defaultdict(dict)
    for r in rows: per[r['family']][r['weight']] = r
    keep, dropped = [], []
    for fam, ws in per.items():
        sr = [r['stem_ratio'] for r in ws.values()]
        if max(sr) - min(sr) < 0.02 and len(ws) > 1:
            dropped.append((fam, 'the Latin is identical across the ladder')); continue
        if any(r['o_thick'] <= 0 or r['o_thin'] <= 0 for r in ws.values()):
            dropped.append((fam, 'no measurable o bowl')); continue
        if any(r['o_thin'] / r['o_thick'] > 0.98 for r in ws.values()):
            dropped.append((fam, 'the o measures monoline -- not a Latin bowl')); continue
        order = [ws[w]['stem'] for w in sorted(ws)]
        if any(b < a - 1e-9 for a, b in zip(order, order[1:])):
            dropped.append((fam, 'the stem is not monotonic in the weight class')); continue
        keep += list(ws.values())
    return keep, dropped


def derive(rows):
    """Albo's parameters per weight class. Stem: the median of the references'
    stem-to-500 ratios x 84. Contrast: the median thin/thick ratio applied to
    the shipping o's 0.525 (= 1 - 0.5 x 0.95), inverted through the same
    identity, clamped into the VF's ruled CNTR range 0.05..0.95."""
    per = collections.defaultdict(dict)
    for r in rows: per[r['family']][r['weight']] = r
    # families anchored on their own 400 (no Medium cut) are bridged onto the
    # 500 through the pooled 400/500 ratio, so every number in the table is a
    # ratio to a 500 as the owner framed it
    b400 = [r['stem_ratio'] for f in per for r in [per[f].get(400)] if r and r['anchor'] == 500]
    bridge = statistics.median(b400) if b400 else 1.0
    bc = [r['contrast_ratio'] for f in per for r in [per[f].get(400)] if r and r['anchor'] == 500 and r['contrast_ratio']]
    bridge_c = statistics.median(bc) if bc else 1.0
    for f in per:
        for w, r in per[f].items():
            if r['anchor'] == 400:
                r['stem_ratio'] *= bridge; r['contrast_ratio'] *= bridge_c; r['bridged'] = True
    out = {500: dict(stem=ALBO_500['stem'], contrast=ALBO_500['contrast'], n=0,
                     stem_ratio=1.0, stem_spread=(1.0, 1.0), c_ratio=1.0, c_spread=(1.0, 1.0), width_ratio=1.0)}
    for w in (400, 300, 200, 100):
        sr = sorted(r['stem_ratio'] for r in (per[f].get(w) for f in per) if r and 0 < r['stem_ratio'] < 0.999)
        cr = sorted(r['contrast_ratio'] for r in (per[f].get(w) for f in per) if r and 0 < r['contrast_ratio'] < 4)
        wr = sorted(r['width_ratio'] for r in (per[f].get(w) for f in per) if r and r['width_ratio'] > 0)
        if not sr: continue
        m = statistics.median(sr)
        cm = statistics.median(cr) if cr else 1.0
        stem = round(ALBO_500['stem'] * m, 1)
        T = min(0.95, 0.525 * cm)                  # the o's target thin/thick
        c = max(0.05, min(0.95, round(2.0 * (1.0 - T), 3)))
        out[w] = dict(stem=stem, contrast=c, n=len(sr), stem_ratio=round(m, 4),
                      stem_spread=(round(sr[0], 3), round(sr[-1], 3)),
                      c_ratio=round(cm, 4), c_spread=(round(cr[0], 3), round(cr[-1], 3)) if cr else (0, 0),
                      width_ratio=round(statistics.median(wr), 4) if wr else 1.0,
                      width_spread=(round(wr[0], 3), round(wr[-1], 3)) if wr else (0, 0))
    for w, d in out.items():
        hair = max(HAIR_FLOOR, d['stem'] * (1 - d['contrast']))
        d['hair'] = round(hair, 2)
        d['hair_px'] = round(hair / 1000 * EINK_PX, 3)
        d['hair_floored'] = d['stem'] * (1 - d['contrast']) < HAIR_FLOOR
        d['o_thin_over_thick'] = round(1 - 0.5 * d['contrast'], 3)
        d['stem_over_xh'] = round(d['stem'] / ALBO_500['xh'], 3)
        # the wedge family's unit: WL = 0.85 x stem x serif, WD = 1.7 x stem x serif
        s = ALBO_500['serif'] / 100.0
        d['wedge_len'] = round(0.85 * d['stem'] * s, 1)
        d['wedge_depth'] = round(1.7 * d['stem'] * s, 1)
    return out


# ------------------------------------------------------------------- building

def build_weight(out_dir, w, params, force=False):
    style = NAMES[w]
    path = os.path.join(out_dir, f'Albo-{style}.ttf')
    if os.path.exists(path) and not force:
        print(f'  {style}: exists, kept'); return path
    env = dict(os.environ)
    env['FJORD_STEM'] = f"{params['stem']:g}"
    env['FJORD_CONTRAST'] = f"{params['contrast']:g}"
    env['PYTHON_GIL'] = '0'
    cmd = [sys.executable, '-W', 'ignore', '-m', 'outlines.build', out_dir, '--style', style]
    r = subprocess.run(cmd, cwd=WEDGE, env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:]); print(r.stderr[-3000:]); raise SystemExit(f'build failed for {style}')
    # the builder writes no usWeightClass and no typographic family/subfamily
    f = TTFont(path)
    f['OS/2'].usWeightClass = w
    f['OS/2'].fsSelection = (f['OS/2'].fsSelection & ~0x21) | (0x40 if w == 400 else 0)
    nt = f['name']
    nt.setName('Albo', 16, 3, 1, 0x409); nt.setName(style, 17, 3, 1, 0x409)
    nt.setName('Albo', 16, 1, 0, 0); nt.setName(style, 17, 1, 0, 0)
    f.save(path)
    print(f"  {style}: stem {params['stem']:g}, contrast {params['contrast']:g} -> {os.path.basename(path)}")
    return path


# ------------------------------------------------------------------- topology

def contour_counts(path):
    f = TTFont(path); gs = f['glyf']; cm = f.getBestCmap(); out = {}
    for cp, gn in sorted(cm.items()):
        g = gs[gn]
        if g.numberOfContours <= 0: continue
        out[chr(cp)] = g.numberOfContours
    return out


def topology(paths):
    """Contour counts per glyph against the 500 -- the check `variable.py`
    runs on every master. A glyph whose count moves has changed topology
    (a counter closed, a hood met a stem, a spur parted)."""
    base = contour_counts(paths[500]); res = {}
    for w, p in sorted(paths.items()):
        if w == 500: res[w] = []; continue
        c = contour_counts(p)
        res[w] = sorted((ch, base.get(ch), c.get(ch)) for ch in set(base) | set(c) if base.get(ch) != c.get(ch))
    return res


def lightest_holding(out_dir, ch, contrast, lo=10.0, hi=None, base_count=None, steps=6):
    """Bisect for the lightest stem at which `ch` keeps the 500's contour
    count, at the given contrast. One `outlines.build --only` is not exposed
    on the CLI, so this builds the whole set per probe; kept to a few probes."""
    from outlines import build as B
    hi = hi or ALBO_500['stem']
    # a probe is a draw(), not a font: the contour count comes straight from
    # the geometry, which is what the topology check reads anyway
    def count(stem):
        env = dict(os.environ, FJORD_STEM=f'{stem:g}', FJORD_CONTRAST=f'{contrast:g}', PYTHON_GIL='0')
        code = ('import sys;sys.path.insert(0,".");from outlines import build,geom;'
                f'print(len(geom.contours(build.draw({ch!r}))))')
        r = subprocess.run([sys.executable, '-W', 'ignore', '-c', code], cwd=WEDGE, env=env,
                           capture_output=True, text=True)
        try: return int(r.stdout.strip().splitlines()[-1])
        except Exception: return -1
    want = base_count if base_count is not None else count(ALBO_500['stem'])
    if count(lo) == want: return lo, want
    a, b = lo, hi
    for _ in range(steps):
        m = (a + b) / 2
        if count(m) == want: b = m
        else: a = m
    return round(b, 1), want


# ----------------------------------------------------------------------- page

def b64(im):
    buf = io.BytesIO(); im.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def ink_stats(im):
    """Share of ink pixels at level 0 (of all non-paper pixels), and page ink
    (mean darkness of the block, 0 = white paper, 1 = solid black)."""
    import numpy as np
    a = np.asarray(im, dtype=np.float32)
    nonpaper = a < 250
    black = a <= 1
    share = float(black.sum()) / max(1, int(nonpaper.sum()))
    page = float((255.0 - a).mean() / 255.0)
    return share, page


def page(out_dir, params, paths, topo, notes):
    from . import proof
    import word_weight
    order = [500, 400, 300, 200, 100]
    words = ' '.join(word_weight.WORDS)
    parts = ["<!-- Albo weights, derived 2026-09-13 -->",
             "<title>Albo Weights</title>",
             "<style>body{margin:0;padding:12px;font:14px/1.45 -apple-system,system-ui,sans-serif;"
             "background:#fbfbf9;color:#1a1a1a;max-width:400px}"
             "img{width:100%;max-width:375px;image-rendering:pixelated;display:block;margin:6px 0}"
             "h1{font-size:19px;margin:6px 0}h2{font-size:16px;margin:22px 0 2px}"
             "p.m{font-size:12px;color:#555;margin:2px 0 8px}"
             "table{border-collapse:collapse;font-size:11px;width:100%}"
             "th,td{border:1px solid #ddd;padding:2px 4px;text-align:right}"
             "th:first-child,td:first-child{text-align:left}"
             "@media(prefers-color-scheme:dark){body{background:#151515;color:#e8e8e8}"
             "th,td{border-color:#444}p.m{color:#aaa}}</style>",
             "<h1>Albo, five weights</h1>",
             "<p class=m>The shipping Albo (stem 84 on a 429 x-height, contrast 0.95) is the 500. "
             "100/200/300/400 are derived from the stem-to-500 ratios of every weight family on this "
             "machine that reaches 350 or lighter. Every image is a PNG at native pixels, 750 px wide, "
             "shown at 375 CSS px.</p>"]
    for w in order:
        d = params[w]
        p = paths[w]
        big = proof.block(p, 'Hamburgefonstiv 1928', 52, line=1.25)
        ein = proof.eink(p, words)
        share, pageink = ink_stats(ein)
        broke = topo.get(w) or []
        parts.append(f"<h2>{w} {NAMES[w]} &mdash; stem {d['stem']:g}, contrast {d['contrast']:g}</h2>")
        parts.append(
            f"<p class=m>hair {d['hair']:.1f} units = {d['hair_px']:.2f} px at 54 px em"
            + (" (at the pen's absolute floor of 6)" if d['hair_floored'] else "")
            + f"; stem/x-height {d['stem_over_xh']:.3f}; o thin:thick 1:{1/d['o_thin_over_thick']:.2f}; "
            + (f"calibration ratio {d['stem_ratio']:.3f} of the 500 (n={d['n']} families, "
               f"{d['stem_spread'][0]:.2f}&ndash;{d['stem_spread'][1]:.2f})" if w != 500 else "the anchor")
            + f"; wedge unit {d['wedge_len']:.0f} &times; {d['wedge_depth']:.0f}"
            + (f"; topology: {len(broke)} glyph(s) move" if broke else "; topology: clean")
            + "</p>")
        parts.append(f'<img src="{b64(big)}" width="{big.size[0]}" height="{big.size[1]}" alt="Hamburgefonstiv 1928">')
        parts.append(f"<p class=m>The 147 common words, 13 pt on the four-level e-ink pipeline "
                     f"&mdash; ink at black {share*100:.1f}%, page ink {pageink:.4f}.</p>")
        parts.append(f'<img src="{b64(ein)}" width="{ein.size[0]}" height="{ein.size[1]}" alt="147 words at 13 pt">')
        params[w]['ink_at_black'] = round(share, 4); params[w]['page_ink'] = round(pageink, 5)
    parts.append('<h2>Calibration</h2>')
    parts.append(notes)
    open(os.path.join(out_dir, 'albo-weights.html'), 'w').write('\n'.join(parts))
    return os.path.join(out_dir, 'albo-weights.html')


def calibration_table_html(rows):
    per = collections.defaultdict(dict)
    for r in rows: per[r['family']][r['weight']] = r
    out = ['<table><tr><th>family</th><th>wt</th><th>stem/xh</th><th>ratio to anchor</th><th>o thin/thick</th></tr>']
    for fam in sorted(per):
        for w in sorted(per[fam]):
            r = per[fam][w]
            a = '*' if w == r['anchor'] else ''
            out.append(f"<tr><td>{html.escape(fam)}</td><td>{w}{a}</td>"
                       f"<td>{r['stem']/r['xh']:.3f}</td><td>{r['stem_ratio']:.3f}</td>"
                       f"<td>{r['contrast']:.3f}</td></tr>")
    out.append('</table><p class=m>* the family\'s anchor (its own 500, or its 400 where it has none). '
               'Stem is the l\'s waist over 0.30&ndash;0.70 of the x-height, median; o thin/thick is the '
               'bowl\'s vertical run at its centre column over its side run at mid x-height. '
               'Rasters at 1200 px em.</p>')
    return '\n'.join(out)


# ----------------------------------------------------------------------- main

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'all'
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(WEDGE, 'fonts', 'weights')
    os.makedirs(out_dir, exist_ok=True)
    cj = os.path.join(out_dir, 'calibration.json')

    if cmd in ('calibrate', 'all') or not os.path.exists(cj):
        rows = calibrate(out_dir)
    else:
        rows = json.load(open(cj))
    if cmd == 'calibrate': return

    rows, dropped = usable(rows)
    print(f'{len(rows)} instances usable; dropped {len(dropped)} families:')
    for f, why in sorted(dropped): print(f'  - {f}: {why}')
    params = derive(rows)
    print('\nweight  stem  contrast   hair(u/px)  o thin:thick  stem ratio (spread)   n')
    for w in (500, 400, 300, 200, 100):
        d = params[w]
        print(f"{w:5d}  {d['stem']:5.1f}  {d['contrast']:6.3f}  {d['hair']:6.2f}/{d['hair_px']:.2f}"
              f"   1:{1/d['o_thin_over_thick']:.2f}      {d['stem_ratio']:.3f} "
              f"({d['stem_spread'][0]:.2f}-{d['stem_spread'][1]:.2f})  {d['n']}")
    json.dump(params, open(os.path.join(out_dir, 'derived.json'), 'w'), indent=1, default=str)
    if cmd == 'derive': return

    paths = {}
    force = '--force' in sys.argv
    for w in (500, 400, 300, 200, 100):
        paths[w] = build_weight(out_dir, w, params[w], force=force)
    if cmd == 'build': return

    topo = topology(paths)
    print('\ntopology against the 500 (contour counts):')
    for w in (400, 300, 200, 100):
        b = topo[w]
        print(f'  {w} {NAMES[w]}: ' + ('clean' if not b else ', '.join(f'{ch!r} {a}->{c}' for ch, a, c in b)))
    json.dump({str(k): v for k, v in topo.items()}, open(os.path.join(out_dir, 'topology.json'), 'w'), indent=1)
    if cmd == 'topology': return

    out = page(out_dir, params, paths, topo, calibration_table_html(rows))
    json.dump(params, open(os.path.join(out_dir, 'derived.json'), 'w'), indent=1, default=str)
    print('\npage:', out)


if __name__ == '__main__':
    main()
