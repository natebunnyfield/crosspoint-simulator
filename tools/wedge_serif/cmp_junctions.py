"""THE JUNCTION DETECTORS (round 274). Two passes over a built font's outlines:

  SLIVERS / SHARDS  white narrower than `--thin` units (a hairline gap, a
                    notch, a crack) and ink narrower than it (a spur, a tooth,
                    a tick): the region minus its morphological opening at
                    thin/2, pieces of `--min-area` and over.
  STEPS             a jog in an edge -- a segment shorter than 12 units between
                    two turns of opposite sign whose neighbours run nearly
                    parallel -- of `--min-step` units and over: a stem corner
                    standing proud of a face, an end face poking out of a
                    stem, a ledge where an arch lands.

Both found the bold italic's head/stem, arch/stem and exit/foot faults of
round 274 (docs/albo-family-2026-09-19.md section 20); neither is the glitch
sweep, which looks for pinches and self-crossings. A step is not always a
fault -- the outstroke's underside leaving a flat foot is one by construction
-- so read the location. Exit 1 when anything is found.

    cmp_junctions.py FONT.ttf [--chars unımhlria] [--thin 6] [--min-area 10] [--min-step 1.5]
"""
import sys, os, math, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
import cmp_aldine_glitch as G

def ink_of(conts):
    outer = unary_union([Polygon(p).buffer(0) for p, h in conts if not h])
    holes = [Polygon(p).buffer(0) for p, h in conts if h]
    return outer.difference(unary_union(holes)) if holes else outer

def thin_pieces(g, thin, min_area):
    k = thin / 2.0
    s = g.difference(g.buffer(-k, join_style=2).buffer(k, join_style=2))
    return [p for p in getattr(s, 'geoms', [s]) if not p.is_empty and p.area >= min_area]

def slivers_shards(ink, thin, min_area):
    b = ink.bounds
    white = box(b[0] - 40, b[1] - 40, b[2] + 40, b[3] + 40).difference(ink)
    return thin_pieces(white, thin, min_area), thin_pieces(ink, thin, min_area)

def turn(a, b, c):
    ax, ay = b[0] - a[0], b[1] - a[1]; bx, by = c[0] - b[0], c[1] - b[1]
    return math.degrees(math.atan2(ax * by - ay * bx, ax * bx + ay * by))

def steps_in(pts, min_off, max_len=12.0, min_turn=18.0, max_bend=30.0):
    q = []
    for p in pts:
        if not q or math.dist(q[-1], p) > 0.05: q.append(p)
    if len(q) > 1 and math.dist(q[0], q[-1]) <= 0.05: q.pop()
    n = len(q); out = []
    if n < 5: return out
    for i in range(n):
        a, b, c, d = q[(i - 1) % n], q[i], q[(i + 1) % n], q[(i + 2) % n]
        if math.dist(b, c) > max_len: continue
        t1 = turn(a, b, c); t2 = turn(b, c, d)
        if abs(t1) < min_turn or abs(t2) < min_turn or (t1 > 0) == (t2 > 0): continue
        if abs(turn(a, b, (b[0] + d[0] - c[0], b[1] + d[1] - c[1]))) > max_bend: continue
        ux, uy = b[0] - a[0], b[1] - a[1]; L = math.hypot(ux, uy) or 1.0
        off = abs((c[0] - b[0]) * (-uy / L) + (c[1] - b[1]) * (ux / L))
        if off >= min_off: out.append((off, b, c))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ttf'); ap.add_argument('--chars', default='unımhlria')
    ap.add_argument('--thin', type=float, default=6.0); ap.add_argument('--min-area', type=float, default=10.0)
    ap.add_argument('--min-step', type=float, default=1.5)
    a = ap.parse_args(); ns = nh = nt = 0
    for ch, conts, note in G.from_ttf(a.ttf, a.chars):
        if not conts: continue
        ink = ink_of(conts); sl, sh = slivers_shards(ink, a.thin, a.min_area)
        for p in sl:
            b = p.bounds; print(f"  {ch} WHITE sliver  area {p.area:6.1f}  [{b[0]:.0f}..{b[2]:.0f} x {b[1]:.0f}..{b[3]:.0f}]")
        for p in sh:
            b = p.bounds; print(f"  {ch} INK shard     area {p.area:6.1f}  [{b[0]:.0f}..{b[2]:.0f} x {b[1]:.0f}..{b[3]:.0f}]")
        st = sorted((f for pts, h in conts for f in steps_in(pts, a.min_step)), key=lambda f: -f[0])
        for off, b, c in st:
            print(f"  {ch} STEP {off:5.1f} units at ({b[0]:.0f},{b[1]:.0f})-({c[0]:.0f},{c[1]:.0f})")
        ns += len(sl); nh += len(sh); nt += len(st)
    print(f"{os.path.basename(a.ttf)} [{a.chars}]: white slivers < {a.thin:g}: {ns}, ink shards < {a.thin:g}: {nh}, steps >= {a.min_step:g}: {nt}")
    sys.exit(1 if ns or nh or nt else 0)

if __name__ == '__main__':
    main()
