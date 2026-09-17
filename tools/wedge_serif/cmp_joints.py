"""Every place two strokes meet, ranked by how badly they meet.

Owner 2026-09-17: *"you are missing the tapered shape of the serif and the joint
in the connecting line"*, then *"assume you have missed other key noteworthy
principles. find them, document them."*

THE PRINCIPLE THIS MEASURES, which had been treated four separate times as a
per-letter bug before it was named:

    `geom.ink`/`union` does not BLEND two strokes, it adds them. So where a
    stroke is unioned onto another, the outline is tangent-continuous only if
    the two edges were already going the same way. If they cross at an angle,
    the union leaves a CONCAVE NOTCH on one side and a CONVEX SPUR on the
    other -- and NEITHER can be tuned away by changing either stroke's WIDTH,
    because the fault is in the direction the edges arrive at, not in how fat
    they are.

Its four known instances, all of which cost rounds: the Q's tail root (round
179), the g's ear rooted on the crown (round 176), the g's neck landing on the
loop (round 184), and the g's ear against the bowl (still open). Coelacanth has
none of them at the ear because its bowl-top and ear are ONE pen movement rather
than two shapes added.

WHAT IT REPORTS. On each glyph's designed outline it finds vertices where the
contour turns sharply, splits them into CONCAVE (a notch cut into the ink) and
CONVEX (a spur sticking out), and ranks by turn angle x the length of the
shorter arm -- so a sharp corner between two long runs outranks a sharp corner
on a 2-unit fragment, which is what the eye does too.

NOT EVERY SHARP CORNER IS A FAULT. The inside of a v, a serif's own bracket, a
deliberate knife-stop: all legitimately sharp. This ranks and reports; it does
not fail a build. Read it with the letters open beside you.

    PYTHON_GIL=0 python3 cmp_joints.py <font.ttf>
    PYTHON_GIL=0 python3 cmp_joints.py <ttf> --chars g --top 12
"""
import argparse, math, sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

XH = 429.0


def contours(ttf, ch):
    f = TTFont(ttf); gs = f.getGlyphSet(); cmap = f.getBestCmap()
    if ord(ch) not in cmap: return None, 1.0
    rp = RecordingPen(); gs[cmap[ord(ch)]].draw(rp)
    upm = f["head"].unitsPerEm
    try: sx = f["OS/2"].sxHeight or upm * 0.5
    except Exception: sx = upm * 0.5
    sc = XH / sx
    out, cur = [], []
    def bez(p0, ps, n=12):
        r = []
        if len(ps) == 2:
            c, p1 = ps
            for i in range(1, n + 1):
                t = i / n; m = 1 - t
                r.append((m*m*p0[0] + 2*m*t*c[0] + t*t*p1[0],
                          m*m*p0[1] + 2*m*t*c[1] + t*t*p1[1]))
        else:
            c1, c2, p1 = ps
            for i in range(1, n + 1):
                t = i / n; m = 1 - t
                r.append((m**3*p0[0] + 3*m*m*t*c1[0] + 3*m*t*t*c2[0] + t**3*p1[0],
                          m**3*p0[1] + 3*m*m*t*c1[1] + 3*m*t*t*c2[1] + t**3*p1[1]))
        return r
    for op, a in rp.value:
        if op == "moveTo": cur = [a[0]]
        elif op == "lineTo": cur.append(a[0])
        elif op == "curveTo": cur.extend(bez(cur[-1], list(a)))
        elif op == "qCurveTo":
            pts = [p for p in a if p is not None]
            for i in range(len(pts) - 1):
                nxt = pts[i+1] if i + 1 == len(pts) - 1 else \
                      ((pts[i][0] + pts[i+1][0]) / 2, (pts[i][1] + pts[i+1][1]) / 2)
                cur.extend(bez(cur[-1], [pts[i], nxt]))
        elif op == "closePath":
            if len(cur) > 3: out.append([(x * sc, y * sc) for x, y in cur])
            cur = []
    if cur and len(cur) > 3: out.append([(x * sc, y * sc) for x, y in cur])
    return out, sc


def corners(cs, min_turn=45.0, min_arm=8.0):
    """Sharp vertices, with their sign and the length of the shorter arm."""
    out = []
    for c in cs:
        n = len(c)
        if n < 6: continue
        A = 0.5 * sum(c[i][0]*c[(i+1) % n][1] - c[(i+1) % n][0]*c[i][1] for i in range(n))
        ccw = A > 0
        for i in range(n):
            p0, p1, p2 = c[(i-1) % n], c[i], c[(i+1) % n]
            v1 = (p1[0]-p0[0], p1[1]-p0[1]); v2 = (p2[0]-p1[0], p2[1]-p1[1])
            L1 = math.hypot(*v1); L2 = math.hypot(*v2)
            if L1 < min_arm or L2 < min_arm: continue
            cr = v1[0]*v2[1] - v1[1]*v2[0]
            dt = v1[0]*v2[0] + v1[1]*v2[1]
            turn = math.degrees(math.atan2(cr, dt))
            if abs(turn) < min_turn: continue
            # on a ccw outer contour a LEFT turn is convex ink, a RIGHT turn concave
            concave = (turn < 0) if ccw else (turn > 0)
            out.append((abs(turn) * min(L1, L2), abs(turn), concave, p1))
    out.sort(reverse=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ttf")
    ap.add_argument("--chars", default=None)
    ap.add_argument("--top", type=int, default=24)
    ap.add_argument("--min-turn", type=float, default=45.0)
    a = ap.parse_args()
    chars = list(a.chars) if a.chars else \
        [chr(c) for c in range(ord('a'), ord('z')+1)] + \
        [chr(c) for c in range(ord('A'), ord('Z')+1)] + list("0123456789")
    rows = []
    for ch in chars:
        cs, _ = contours(a.ttf, ch)
        if not cs: continue
        for score, turn, concave, p in corners(cs, a.min_turn):
            rows.append((score, ch, turn, concave, p))
    rows.sort(reverse=True)
    print(f"\n  sharp joints on the designed outline, unsheared, xh {XH:.0f}")
    print(f"  ranked by turn x shorter arm -- a NOTCH is ink cut away, a SPUR sticks out\n")
    print(f"  {'ch':4}{'turn':>7}{'kind':>8}{'score':>9}   at (x, y)")
    for score, ch, turn, concave, p in rows[:a.top]:
        print(f"  {ch:4}{turn:6.0f}°{('NOTCH' if concave else 'spur'):>8}{score:9.0f}"
              f"   ({p[0]:5.0f}, {p[1]:5.0f})")
    n_notch = sum(1 for r in rows if r[3])
    print(f"\n  {len(rows)} sharp joints over {len(chars)} glyphs; {n_notch} are notches.\n")


if __name__ == "__main__":
    main()
