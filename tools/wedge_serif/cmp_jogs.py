"""cmp_jogs.py FONT [--json OUT] -- find STEPS and NICKS in contour edges.

ROUND 385 (2026-09-24). Owner: *"correct any fractures like this one from yen
character"* -- a small step breaking an otherwise straight stroke edge, where
two overlapping parts of a glyph were unioned with their edges misaligned. No
existing gate targets it: `cmp_contour_hairs.py` wants a reversal past 150
degrees, `cmp_aldine_glitch.py` a hole or a pinch, `albo_bumps.py` circles
every facet. Reported per glyph as (x, y) turn, `off` (edge-to-edge offset)
and `dev` (deepest excursion, units). Read `dev`: under 2 is invisible at any
size, the fractures fixed in round 385 measured 3-17. It MISSES the yen's own
nick (its flanks are not smooth enough), so it is a finder, not a gate.

A jog: within a short run of the outline (<= WIN units) the edge turns sharply
one way and then back (sum |turn| >= MIN_TURN, net turn <= NET), and the edge
on both sides of it is smooth for FLANK units (sum |turn| <= FLANK_TURN). That
is a step or notch in an otherwise continuous edge -- the fracture class the
owner showed on the yen, 2026-09-24. Reports the lateral offset between the
edge before and after (the step's height) and the deepest excursion."""
import sys, math, json
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
WIN, MIN_TURN, NET, FLANK, FLANK_TURN = 18.0, 60.0, 25.0, 24.0, 20.0
class P(BasePen):
    def __init__(s, gs): super().__init__(gs); s.c = []; s.cur = []
    def _moveTo(s, p): s.cur = [p]
    def _lineTo(s, p): s.cur.append(p)
    def _qCurveToOne(s, a, b):
        p0 = s.cur[-1]; n = max(2, int(math.dist(p0, a) + math.dist(a, b)) // 3)
        for i in range(1, n + 1):
            t = i / n; m = 1 - t
            s.cur.append((m*m*p0[0] + 2*m*t*a[0] + t*t*b[0], m*m*p0[1] + 2*m*t*a[1] + t*t*b[1]))
    def _curveToOne(s, a, b, c):
        p0 = s.cur[-1]
        for i in range(1, 13):
            t = i / 12; m = 1 - t
            s.cur.append((m**3*p0[0] + 3*m*m*t*a[0] + 3*m*t*t*b[0] + t**3*c[0], m**3*p0[1] + 3*m*m*t*a[1] + 3*m*t*t*b[1] + t**3*c[1]))
    def _closePath(s):
        if len(s.cur) > 2: s.c.append(s.cur)
        s.cur = []
def clean(pts):
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) > 0.75: out.append(p)
    if len(out) > 2 and math.dist(out[0], out[-1]) <= 0.75: out.pop()
    return out
def turns(pts):
    n = len(pts); T = []; L = []
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        a1 = math.atan2(b[1] - a[1], b[0] - a[0]); a2 = math.atan2(c[1] - b[1], c[0] - b[0])
        d = math.degrees((a2 - a1 + math.pi) % (2 * math.pi) - math.pi)
        T.append(d); L.append(math.dist(b, c))
    return T, L
def scan(pts):
    n = len(pts)
    if n < 8: return []
    T, L = turns(pts); found = []; used = set()
    for i in range(n):
        if abs(T[i]) < 20 or i in used: continue
        # window forward from i
        s = 0.0; j = i; tot = 0.0; net = 0.0; idx = []
        while s <= WIN and len(idx) < n:
            tot += abs(T[j % n]); net += T[j % n]; idx.append(j % n)
            s += L[j % n]; j += 1
            if tot >= MIN_TURN and abs(net) <= NET and abs(T[(j - 1) % n]) >= 20: break
        if not (tot >= MIN_TURN and abs(net) <= NET): continue
        # flanks
        def flank(k, step):
            s = 0.0; tt = 0.0; k = (k + step) % n
            while s < FLANK:
                tt += abs(T[k]); s += L[k if step > 0 else (k - 1) % n]; k = (k + step) % n
            return tt
        if flank(idx[0], -1) > FLANK_TURN or flank(idx[-1], +1) > FLANK_TURN: continue
        # offset: line through the flank before vs point after
        a0, a1 = pts[(idx[0] - 4) % n], pts[idx[0]]
        b1 = pts[(idx[-1] + 4) % n]
        dx, dy = a1[0] - a0[0], a1[1] - a0[1]; ln = math.hypot(dx, dy) or 1
        off = abs((b1[0] - a1[0]) * dy - (b1[1] - a1[1]) * dx) / ln
        dev = max(abs((pts[k][0] - a1[0]) * dy - (pts[k][1] - a1[1]) * dx) / ln for k in idx)
        used.update(idx)
        found.append(dict(x=round(pts[i][0]), y=round(pts[i][1]), turn=round(tot), net=round(net), off=round(off, 1), dev=round(dev, 1)))
    return found
if __name__ == '__main__':
    t = TTFont(sys.argv[1]); gs = t.getGlyphSet(); cm = {v: k for k, v in t.getBestCmap().items()}
    res = {}
    for gn in t.getGlyphOrder():
        p = P(gs); gs[gn].draw(p)
        f = []
        for c in p.c: f += scan(clean(c))
        f = [x for x in f if x['dev'] >= 1.0]
        if f: res[gn] = dict(ch=chr(cm[gn]) if gn in cm else '', finds=f)
    for gn, r in res.items():
        print(f"{gn:16s} {r['ch']:2s} " + '  '.join(f"({x['x']},{x['y']}) t{x['turn']} off{x['off']} dev{x['dev']}" for x in r['finds']))
    print(len(res), 'glyphs with jogs')
    if '--json' in sys.argv: json.dump(res, open(sys.argv[sys.argv.index('--json') + 1], 'w'), ensure_ascii=False)
