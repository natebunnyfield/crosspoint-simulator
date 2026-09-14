"""The space BETWEEN letters against the space WITHIN them, measured (owner,
round 3: "the distance between characters should be the same as within
their characters"; round 96b: "examine 'jam' and other common english letter
combinations and see how the space between letters can be the same as
within letters").

The metric is the firmware autokerner's (optical_kern.py): per row of the
x-height band, the white between two glyphs' ink, CLAMPED at a reach depth
(1.6 n-counters) so a void deeper than the eye tracks stops counting; a row
where either glyph has no ink is fully open and counts the full depth. The
mean over the band is the pair's "white". The same measure inside one glyph
(the gap between its own ink runs) is its counter white. Everything in
design units at a 1000 px em, no hinting, so 1 px = 1 unit.

    cd tools/wedge_serif && PYTHON_GIL=0 python3 -m outlines.cmp.rhythm <font.ttf> [a]

Prints the counters, the font's own rhythm (frequency-weighted white over
the common lowercase bigrams that do not involve the letter under study),
and, for the letter, the white against each common neighbour on each side
with its frequency weight, and the bearing change that would put the
weighted median ON the rhythm.
"""
import sys, os, statistics
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

EM = 1000
REACH = 1.6

# English bigram frequencies (per cent of all bigrams; Norvig 2013, rounded),
# the common lowercase pairs that set a text face's rhythm.
BIGRAMS = {
    'th': 3.56, 'he': 3.07, 'in': 2.43, 'er': 2.05, 'an': 1.99, 're': 1.85, 'on': 1.76, 'at': 1.49, 'en': 1.45,
    'nd': 1.35, 'ti': 1.34, 'es': 1.34, 'or': 1.28, 'te': 1.20, 'of': 1.17, 'ed': 1.17, 'is': 1.13, 'it': 1.12,
    'al': 1.09, 'ar': 1.07, 'st': 1.05, 'to': 1.04, 'nt': 1.04, 'ng': 0.95, 'se': 0.93, 'ha': 0.93, 'as': 0.87,
    'ou': 0.87, 'io': 0.83, 'le': 0.83, 've': 0.83, 'co': 0.79, 'me': 0.79, 'de': 0.76, 'hi': 0.76, 'ri': 0.73,
    'ro': 0.73, 'ic': 0.70, 'ne': 0.69, 'ea': 0.69, 'ra': 0.69, 'ce': 0.65, 'li': 0.62, 'ch': 0.60, 'll': 0.58,
    'be': 0.58, 'ma': 0.57, 'si': 0.55, 'om': 0.55, 'ur': 0.54, 'ca': 0.54, 'el': 0.53, 'ta': 0.53, 'la': 0.53,
    'ns': 0.51, 'di': 0.50, 'fo': 0.49, 'ho': 0.49, 'pe': 0.48, 'ec': 0.48, 'pr': 0.47, 'no': 0.47, 'ct': 0.46,
    'us': 0.45, 'ac': 0.45, 'ot': 0.44, 'il': 0.43, 'tr': 0.43, 'ly': 0.42, 'nc': 0.42, 'et': 0.41, 'ut': 0.41,
    'ss': 0.41, 'so': 0.41, 'rs': 0.40, 'un': 0.40, 'lo': 0.39, 'wa': 0.39, 'ge': 0.39, 'ie': 0.38, 'wh': 0.38,
    'ee': 0.38, 'wi': 0.37, 'em': 0.37, 'ad': 0.37, 'ol': 0.36, 'rt': 0.36, 'po': 0.35, 'we': 0.35, 'na': 0.35,
    'ul': 0.35, 'ni': 0.34, 'ts': 0.34, 'mo': 0.34, 'ow': 0.33, 'pa': 0.32, 'im': 0.32, 'mi': 0.32, 'ai': 0.32,
    'sh': 0.32, 'ir': 0.32, 'su': 0.31, 'id': 0.30, 'os': 0.29, 'iv': 0.29, 'ia': 0.29, 'am': 0.29, 'fi': 0.29,
    'ci': 0.28, 'vi': 0.27, 'pl': 0.26, 'ig': 0.26, 'tu': 0.26, 'ev': 0.26, 'ld': 0.25, 'ry': 0.25, 'mp': 0.24,
    'fe': 0.24, 'bl': 0.23, 'ab': 0.23, 'gh': 0.23, 'ty': 0.23, 'op': 0.23, 'wo': 0.22, 'sa': 0.22, 'ay': 0.22,
    'ex': 0.22, 'ke': 0.21, 'fr': 0.21, 'oo': 0.21, 'av': 0.20, 'ag': 0.20, 'if': 0.20, 'ap': 0.20, 'gr': 0.20,
    'od': 0.19, 'bo': 0.19, 'sp': 0.19, 'rd': 0.19, 'do': 0.19, 'uc': 0.19, 'bu': 0.18, 'ei': 0.18, 'ov': 0.18,
    'by': 0.18, 'rm': 0.18, 'ep': 0.17, 'tt': 0.17, 'oc': 0.17, 'fa': 0.17, 'ef': 0.17, 'cu': 0.16, 'rn': 0.16,
    'sc': 0.16, 'gi': 0.15, 'da': 0.15, 'yo': 0.15, 'cr': 0.15, 'cl': 0.15, 'du': 0.15, 'ga': 0.15, 'ue': 0.15,
    'ff': 0.15, 'ba': 0.15, 'ak': 0.13, 'aw': 0.12, 'ja': 0.05, 'ka': 0.05, 'oa': 0.08, 'ua': 0.10, 'ya': 0.06,
    'va': 0.07, 'za': 0.01, 'qu': 0.15, 'ki': 0.14, 'ny': 0.13, 'nk': 0.12, 'lu': 0.12, 'ru': 0.12, 'ck': 0.12,
    'ib': 0.10, 'ub': 0.09, 'ob': 0.09, 'lt': 0.10, 'nl': 0.10, 'dr': 0.10, 'ye': 0.09, 'wn': 0.09, 'yi': 0.05,
}

def profile(font_path, chars):
    """Per glyph: advance (units), per-row ink runs in the x-height band, x
    relative to the glyph origin, y up from the baseline."""
    f = TTFont(font_path); cm = f.getBestCmap(); hm = f['hmtx']
    xh = f['OS/2'].sxHeight; k = EM / f['head'].unitsPerEm
    pil = ImageFont.truetype(font_path, EM)
    out = {}
    W, H = 3 * EM, 3 * EM; ox, base = EM, 2 * EM
    for ch in chars:
        if ord(ch) not in cm: continue
        im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).text((ox, base), ch, font=pil, fill=255, anchor='ls')
        a = np.asarray(im) > 128
        rows = {}
        for y in range(1, int(xh * k) + 1):
            row = a[base - y]
            xs = np.where(row)[0]
            if not len(xs): continue
            runs = []; start = xs[0]; prev = xs[0]
            for x in xs[1:]:
                if x != prev + 1: runs.append((start - ox, prev - ox)); start = x
                prev = x
            runs.append((start - ox, prev - ox)); rows[y] = runs
        out[ch] = dict(adv=hm[cm[ord(ch)]][0] * k, rows=rows)
    return out, int(xh * k)

def counter_white(g, band, depth):
    vals = []
    for y in band:
        runs = g['rows'].get(y)
        if not runs or len(runs) < 2: continue
        gaps = [runs[i + 1][0] - runs[i][1] - 1 for i in range(len(runs) - 1)]
        vals.append(min(max(gaps), depth))
    return statistics.mean(vals) if vals else None

def pair_white(a, b, band, depth, k=0.0):
    vals = []
    for y in band:
        ra = a['rows'].get(y); rb = b['rows'].get(y)
        if not ra or not rb: vals.append(depth); continue
        gap = (a['adv'] - ra[-1][1] - 1) + rb[0][0] + k
        vals.append(min(max(gap, 0.0), depth))
    return statistics.mean(vals)

def wmedian(pairs):
    """Weighted median of [(value, weight)]."""
    pairs = sorted(pairs); tot = sum(w for _, w in pairs); acc = 0
    for v, w in pairs:
        acc += w
        if acc >= tot / 2: return v
    return pairs[-1][0]

def analyse(font_path, letter='a', verbose=True):
    chars = sorted(set(''.join(BIGRAMS)) | {letter, 'n', 'o'})
    G, xh = profile(font_path, chars); band = list(range(1, xh + 1))
    n_runs = [max(r[i + 1][0] - r[i][1] - 1 for i in range(len(r) - 1)) for y in band if (r := G['n']['rows'].get(y)) and len(r) > 1]
    n_counter = statistics.median(n_runs); depth = REACH * n_counter
    cn = counter_white(G['n'], band, depth); co = counter_white(G['o'], band, depth); cl = counter_white(G[letter], band, depth)
    rhythm_pairs = [(pair_white(G[a], G[b], band, depth), w) for (a, b), w in ((tuple(k), v) for k, v in BIGRAMS.items()) if letter not in (a, b) and a in G and b in G]
    rhythm = wmedian(rhythm_pairs)
    left = [(b, pair_white(G[b], G[letter], band, depth), w) for (b, l), w in ((tuple(k), v) for k, v in BIGRAMS.items()) if l == letter and b != letter and b in G]
    right = [(b, pair_white(G[letter], G[b], band, depth), w) for (l, b), w in ((tuple(k), v) for k, v in BIGRAMS.items()) if l == letter and b != letter and b in G]
    lm = wmedian([(v, w) for _, v, w in left]); rm = wmedian([(v, w) for _, v, w in right])
    res = dict(n_counter=n_counter, depth=depth, counter_n=cn, counter_o=co, counter_letter=cl, rhythm=rhythm,
               left=sorted(left, key=lambda t: -t[2]), right=sorted(right, key=lambda t: -t[2]), left_median=lm, right_median=rm,
               lsb_delta=rhythm - lm, rsb_delta=rhythm - rm)
    if verbose:
        print(f"{os.path.basename(font_path)}: n counter {n_counter:.0f}, reach {depth:.0f}; counter white n {cn:.0f} o {co:.0f} {letter} {cl:.0f}")
        print(f"  rhythm (weighted median white over {len(rhythm_pairs)} common bigrams without '{letter}'): {rhythm:.0f}")
        print(f"  '{letter}' on the LEFT of it -- weighted median {lm:.0f} (rhythm {rhythm - lm:+.0f}):")
        print('   ' + '  '.join(f"{b}{letter} {v:.0f}" for b, v, w in res['left']))
        print(f"  '{letter}' on the RIGHT of it -- weighted median {rm:.0f} (rhythm {rhythm - rm:+.0f}):")
        print('   ' + '  '.join(f"{letter}{b} {v:.0f}" for b, v, w in res['right']))
    return res

if __name__ == '__main__':
    analyse(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'a')

# ---------------------------------------------------------------- round 97: the solve

def bridged_profiles(g, w):
    """Outer left/right profiles with concavities shorter than w bridged (a
    vertical rolling window over the per-row extremes -- what the eye does
    with the notch under the a's hood or a c's aperture)."""
    ys = sorted(g['rows']); left = {}; right = {}
    for y in ys:
        win = [yy for yy in ys if abs(yy - y) <= w / 2]
        left[y] = min(g['rows'][yy][0][0] for yy in win); right[y] = max(g['rows'][yy][-1][1] for yy in win)
    return left, right

def white_table(G, band, depth, w, chars):
    """{(a, b): white} for every ordered pair of chars, bridged at w, unkerned."""
    prof = {c: bridged_profiles(G[c], w) for c in chars}
    T = {}
    for a in chars:
        la, ra = prof[a]
        for b in chars:
            lb, rb = prof[b]; vals = []
            for y in band:
                if y not in ra or y not in lb: vals.append(depth); continue
                vals.append(min(max((G[a]['adv'] - ra[y] - 1) + lb[y], 0.0), depth))
            T[(a, b)] = statistics.mean(vals)
    return T

def solve(font_path, iters=12, clamp=60, bridge=0.5, rhythm=None):
    """Per-letter bearing deltas (lsb, rsb) that put the frequency-weighted
    common bigrams on the rhythm. Gauss-Seidel on
    sum_w (r_a + l_b + white_ab - R)^2. Returns (deltas, R, residuals)."""
    chars = sorted(set(''.join(BIGRAMS)))
    G, xh = profile(font_path, chars); band = list(range(1, xh + 1))
    n_runs = [max(r[i + 1][0] - r[i][1] - 1 for i in range(len(r) - 1)) for y in band if (r := G['n']['rows'].get(y)) and len(r) > 1]
    nc = statistics.median(n_runs); depth = REACH * nc; w = bridge * nc
    T = white_table(G, band, depth, w, chars)
    pairs = [((a, b), wt) for (a, b), wt in ((tuple(k), v) for k, v in BIGRAMS.items()) if a in G and b in G]
    R = rhythm if rhythm is not None else wmedian([(T[p], wt) for p, wt in pairs])
    l = {c: 0.0 for c in chars}; r = {c: 0.0 for c in chars}
    for _ in range(iters):
        for c in chars:
            ps = [(p, wt) for p, wt in pairs if p[1] == c]
            if ps: l[c] = max(-clamp, min(clamp, -sum(wt * (r[p[0]] + T[p] - R) for p, wt in ps) / sum(wt for _, wt in ps)))
            ps = [(p, wt) for p, wt in pairs if p[0] == c]
            if ps: r[c] = max(-clamp, min(clamp, -sum(wt * (l[p[1]] + T[p] - R) for p, wt in ps) / sum(wt for _, wt in ps)))
    res = {p: r[p[0]] + l[p[1]] + T[p] - R for p, _ in pairs}
    before = {p: T[p] - R for p, _ in pairs}
    return {c: (round(l[c]), round(r[c])) for c in chars}, R, res, before, pairs

def spread(dev, pairs):
    """Weighted mean |deviation| and the extremes."""
    tot = sum(wt for _, wt in pairs)
    return sum(wt * abs(dev[p]) for p, wt in pairs) / tot, min(dev.values()), max(dev.values())

def patch(font_path, deltas, out):
    """Apply bearing deltas to a built TTF (translate outlines, widen advances)."""
    f = TTFont(font_path); hm = f['hmtx']; cm = f.getBestCmap(); g = f['glyf']
    for ch, (dl, dr) in deltas.items():
        n = cm.get(ord(ch))
        if not n or (dl == 0 and dr == 0): continue
        adv, lsb = hm[n]; hm[n] = (adv + dl + dr, lsb + dl)
        if dl and g[n].numberOfContours > 0: g[n].coordinates.translate((dl, 0))
    f.save(out); return out

def solve_cat(font_path, sides, iters=12, clamp=60, bridge=0.5):
    """Round 97b: like solve(), but the target for a pair is the weighted
    median white of ITS SIDE CATEGORY (left glyph's right side x right
    glyph's left side, from round19.SIDES) in the font as given -- so a
    round next to a round stays tighter than a stem next to a stem, the
    ratio the fitting rule set and the owner had accepted, and only the
    scatter WITHIN a category is solved away."""
    chars = sorted(set(''.join(BIGRAMS)))
    G, xh = profile(font_path, chars); band = list(range(1, xh + 1))
    n_runs = [max(r[i + 1][0] - r[i][1] - 1 for i in range(len(r) - 1)) for y in band if (r := G['n']['rows'].get(y)) and len(r) > 1]
    nc = statistics.median(n_runs); depth = REACH * nc; w = bridge * nc
    T = white_table(G, band, depth, w, chars)
    pairs = [((a, b), wt) for (a, b), wt in ((tuple(k), v) for k, v in BIGRAMS.items()) if a in G and b in G]
    cat = lambda a, b: (sides.get(a, ('straight', 'straight'))[1], sides.get(b, ('straight', 'straight'))[0])
    cells = {}
    for p, wt in pairs: cells.setdefault(cat(*p), []).append((T[p], wt))
    target = {c: wmedian(v) for c, v in cells.items()}
    Rp = {p: target[cat(*p)] for p, _ in pairs}
    l = {c: 0.0 for c in chars}; r = {c: 0.0 for c in chars}
    for _ in range(iters):
        for c in chars:
            ps = [(p, wt) for p, wt in pairs if p[1] == c]
            if ps: l[c] = max(-clamp, min(clamp, -sum(wt * (r[p[0]] + T[p] - Rp[p]) for p, wt in ps) / sum(wt for _, wt in ps)))
            ps = [(p, wt) for p, wt in pairs if p[0] == c]
            if ps: r[c] = max(-clamp, min(clamp, -sum(wt * (l[p[1]] + T[p] - Rp[p]) for p, wt in ps) / sum(wt for _, wt in ps)))
    res = {p: r[p[0]] + l[p[1]] + T[p] - Rp[p] for p, _ in pairs}
    before = {p: T[p] - Rp[p] for p, _ in pairs}
    return {c: (round(l[c]), round(r[c])) for c in chars}, target, res, before, pairs
