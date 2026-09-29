"""counter_shape.py -- how much of a glyph's COUNTER is straight or cornered, from a built font.

    PYTHON_GIL=0 python3 instruments/counter_shape.py FONT.ttf obdpq [FONT2.ttf]

For each counter (a contour lying inside another of the same glyph): its perimeter, its longest
STRAIGHT run (consecutive outline points all within 1.5 units of the chord between the run's ends --
cmp_aldine_straight.py's rule), and its CORNERS (turns sharper than 35 degrees over a 12-unit
neighbourhood, the curve flattened first). A counter that is an oval reads short runs and no
corners; round 270's convex hull at the 700 leaves long straight chords and a corner at each end of
one. Written 2026-09-28 for the Bold Italic's lozenge counters (docs/albo-issue-sweep-2026-09-28.md).
"""
import sys, math
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from shapely.geometry import Polygon

TOL, TURN, NB = 1.5, 35.0, 12.0


def contours(path, ch):
    f = TTFont(path); gs = f.getGlyphSet(); name = f.getBestCmap()[ord(ch)]
    p = DecomposingRecordingPen(gs); gs[name].draw(p)
    out, cur = [], []
    for op, args in p.value:
        if op == 'moveTo': cur = [args[0]]
        elif op == 'lineTo': cur.append(args[0])
        elif op == 'qCurveTo':
            pts = [cur[-1]] + list(args)
            # TrueType implied on-curve points between consecutive off-curve ones
            offs, end = pts[1:-1], pts[-1]
            seq = [pts[0]]
            for i, c in enumerate(offs):
                nxt = offs[i + 1] if i + 1 < len(offs) else end
                mid = nxt if i + 1 == len(offs) else ((c[0] + nxt[0]) / 2, (c[1] + nxt[1]) / 2)
                a = seq[-1]
                for k in range(1, 9):
                    t = k / 8; m = 1 - t
                    seq.append((m * m * a[0] + 2 * m * t * c[0] + t * t * mid[0], m * m * a[1] + 2 * m * t * c[1] + t * t * mid[1]))
            cur += seq[1:]
        elif op == 'curveTo':
            a = cur[-1]; b, c, d = args
            for k in range(1, 13):
                t = k / 12; m = 1 - t
                cur.append((m**3*a[0] + 3*m*m*t*b[0] + 3*m*t*t*c[0] + t**3*d[0], m**3*a[1] + 3*m*m*t*b[1] + 3*m*t*t*c[1] + t**3*d[1]))
        elif op in ('closePath', 'endPath'):
            if len(cur) > 2: out.append(cur)
            cur = []
    return out


def straight_runs(pts):
    n = len(pts); best = 0.0
    for i in range(n):
        j = i + 2
        while j < i + n:
            a, b = pts[i], pts[j % n]
            L = math.dist(a, b)
            if L < 1e-6: j += 1; continue
            ok = all(abs((b[0] - a[0]) * (a[1] - pts[k % n][1]) - (a[0] - pts[k % n][0]) * (b[1] - a[1])) / L <= TOL
                     for k in range(i + 1, j))
            if not ok: break
            best = max(best, L); j += 1
    return best


def corners(pts):
    n = len(pts); cs = 0
    cum = [0.0]
    for i in range(1, n): cum.append(cum[-1] + math.dist(pts[i - 1], pts[i]))
    per = cum[-1] + math.dist(pts[-1], pts[0])
    def at(s):
        s %= per
        for i in range(n):
            s1 = cum[i + 1] if i + 1 < n else per
            if s <= s1:
                a, b = pts[i], pts[(i + 1) % n]; seg = s1 - cum[i] or 1.0; t = (s - cum[i]) / seg
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        return pts[0]
    step = 3.0; k = int(per / step); turns = []
    for m in range(k):
        s = m * step; p0, p1, p2 = at(s - NB), at(s), at(s + NB)
        a1 = math.atan2(p1[1] - p0[1], p1[0] - p0[0]); a2 = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        d = abs((math.degrees(a2 - a1) + 180) % 360 - 180); turns.append(d)
    inside = False
    for m, d in enumerate(turns):
        if d > TURN and not inside: cs += 1; inside = True
        elif d <= TURN * 0.6: inside = False
    return cs, per


for path in [a for a in sys.argv[1:] if a.endswith('.ttf')]:
    for ch in sys.argv[2]:
        cs = contours(path, ch); polys = [Polygon(c).buffer(0) for c in cs]
        rows = []
        for i, (c, P) in enumerate(zip(cs, polys)):
            if any(j != i and polys[j].area > P.area and polys[j].contains(P.representative_point()) for j in range(len(cs))):
                k, per = corners(c); rows.append(f"counter per {per:5.0f} straight {straight_runs(c):5.1f} corners {k}")
        print(f"{path.split('/')[-2][-8:]}/{path.split('/')[-1][5:-4]:10s} {ch}: " + " | ".join(rows))
