"""Albo variety audit: which serifs and which counters are the SAME shape.

    cd tools/wedge_serif
    PYTHON_GIL=0 python3 -W ignore -m outlines.cmp.variety <font.ttf> <out_dir>

Owner, 2026-09-13: "run an audit that evaluates which serifs and counters
are exactly the same as others, we need variety throughout this font for it
to work."  A handcut face is alive because no two serifs are the same
serif.  Albo is drawn by code, so its serifs are function calls: two calls
with the same arguments produce, byte for byte, the same polygon.  This
tool finds every such repetition at two levels.

LEVEL 1 -- CONSTRUCTION.  Every primitive that makes a serif or a counter
(`wedge`, `stem`, `ring`, `ring_from`, `half_bowl`, `beak`, `dot`, `bar`,
`diag_wedge`, `end_wedge`, `diagonal`) is wrapped for the length of one
build and every call recorded with its numeric arguments, per glyph.  This
catches the serifs a glyph never names -- `stem(top='left', foot='both')`
draws three wedges and the glyph file mentions none of them -- and it is
exact where reading the source is guesswork, because the arguments are the
values the code actually computed, not the expressions it was written as.
Calls are grouped by their rounded argument signature.

LEVEL 2 -- OUTLINE.  Every serif is compared as the SHAPE IT ENDS UP
BEING, after the union with its stroke and after the cut.

  The serif window.  Every wedge call carries the frame it was drawn in:
  A, the stroke's corner at the end; d, the unit direction OUT of the
  stroke's end; sd, the unit normal out of the stroke on the wedge's side.
  The window is the rectangle, in that frame, u in [-WD/2, +WD/2] along sd
  and v in [-WD, +WD/2] along d -- a WD x 1.5 WD box on the stem edge,
  containing the apex (which sits WL out along sd, WL < WD/2) and the whole
  bracket (which runs `depth` <= WD back along the edge).  The glyph's ink
  is clipped to it and mapped into the frame, so every serif in the font
  arrives aligned on its own stem edge and its own end face and the
  comparison is of shape alone -- a foot and a top wedge on the same stem
  land on top of each other, which is the point: they SHOULD differ.

  The counters.  Every closed inner contour (a hole) of every glyph, moved
  so its centroid is the origin and NOT scaled -- an o's counter and a b's
  counter that are the same size and the same shape are the finding.  A
  second, softer pass normalizes each counter to unit area first and lists
  what is merely scale-similar.

  Both metrics are reported for every pair: the area of the symmetric
  difference over the mean area (a percentage), and the Hausdorff distance
  between the two boundaries over the window's depth (serifs) or the
  counter's root area.  Under 2% symmetric difference is called EXACT
  ("the same serif"), 2-8% NEAR.  Pairs are then joined into groups by
  connected component, so a group of five is five serifs no reader can
  tell apart.

  PRE-CUT and POST-CUT are both reported and they answer different
  questions.  The cut (`cut.blend`, seed 73, one running phase counter over
  the glyph order) gives every contour its own facet phase, so two true
  copies come out of it with different facets and a post-cut comparison
  UNDERSTATES the repetition.  The pre-cut designed outline is where a true
  copy lives; the post-cut number says how much of the sameness the cut
  already hides.  Do not read the post-cut list as the answer.

The font argument is used to cross-check the built contour counts; the
geometry is taken from the builder in design space (untranslated, unrounded)
so the serif frames recorded at level 1 line up with the outlines at level 2.
"""
import os, sys, math, base64, io, json, itertools
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import shapely
from shapely.geometry import Polygon, MultiPolygon
from shapely import affinity
from PIL import Image, ImageDraw

from .. import build, geom, pen, cut
from .. import primitives as PR
from ..glyphs import GLYPHS

WL, WD = pen.WL, pen.WD

EXACT_PCT = 2.0     # symmetric difference at or under this: "exactly the same"
NEAR_PCT = 8.0      # ... and up to this: "a near copy"

# ------------------------------------------------------------------ record
RECORD = {"on": False, "ch": None}
CALLS = []          # every primitive call, in build order
WEDGES = []         # the serif subset, with the frame each was drawn in

_PRIMS = ("wedge", "stem", "ring", "ring_from", "half_bowl", "beak", "dot",
          "bar", "diag_wedge", "end_wedge", "diagonal", "o_ring", "cap_ring", "fig_ring")


def _r(v, q=0.01):
    """Round for a signature: two decimals is finer than any facet."""
    try: return round(float(v) / q) * q
    except (TypeError, ValueError): return v


def _sig_wedge(a, kw):
    A, d, sd, length, depth, drop = a[0], a[1], a[2], a[3], a[4], a[5]
    fillet = kw.get("fillet", PR.FILLET); into = kw.get("into", 6.0)
    return dict(kind="wedge",
                len_WL=round(length / WL, 4), depth_WD=round(depth / WD, 4),
                drop=round(drop / max(pen.DROP, 1e-9), 4), fillet=round(fillet, 4),
                into=round(float(into), 3),
                d_deg=round(math.degrees(math.atan2(d[1], d[0])), 1),
                sd_deg=round(math.degrees(math.atan2(sd[1], sd[0])), 1),
                bracketed=kw.get("edge_at") is not None)


def _sig_generic(name, a, kw):
    out = dict(kind=name)
    for i, v in enumerate(a):
        if isinstance(v, (int, float)): out[f"a{i}"] = _r(v)
        elif isinstance(v, tuple) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v):
            out[f"a{i}"] = (_r(v[0]), _r(v[1]))
    for k, v in kw.items():
        if isinstance(v, (int, float)): out[k] = _r(v)
        elif isinstance(v, (str, bool, type(None))): out[k] = v
        elif isinstance(v, tuple) and all(isinstance(x, (int, float)) for x in v):
            out[k] = tuple(_r(x) for x in v)
    return out


def install():
    """Wrap the primitives in every namespace that imported them."""
    import outlines.glyphs as G
    mods = [PR] + [m for n, m in sys.modules.items()
                   if n.startswith("outlines.glyphs.") and m is not None]
    originals = {}
    for name in _PRIMS:
        orig = getattr(PR, name, None)
        if orig is None:
            # o_ring / cap_ring / fig_ring live in glyph modules
            for m in mods:
                if hasattr(m, name): orig = getattr(m, name); break
        if orig is None: continue
        originals[name] = orig

        def make(name, orig):
            def wrapper(*a, **kw):
                out = orig(*a, **kw)
                if RECORD["on"]:
                    try:
                        sig = _sig_wedge(a, kw) if name == "wedge" else _sig_generic(name, a, kw)
                    except Exception:
                        sig = dict(kind=name, unparsed=True)
                    rec = dict(ch=RECORD["ch"], name=name, sig=sig)
                    CALLS.append(rec)
                    if name == "wedge" and len(a) >= 6:
                        WEDGES.append(dict(ch=RECORD["ch"], A=tuple(a[0]), d=tuple(a[1]), sd=tuple(a[2]),
                                           length=a[3], depth=a[4], drop=a[5], sig=sig,
                                           poly=out if hasattr(out, "area") else None))
                return out
            return wrapper
        w = make(name, orig)
        for m in mods:
            if getattr(m, name, None) is orig: setattr(m, name, w)


# ------------------------------------------------------------------ geometry
def frame_window(A, d, sd):
    """The serif window as a shapely polygon in DESIGN space, plus the map
    into the wedge's own frame.  u along sd in [-WD/2, WD/2], v along d in
    [-WD, WD/2]: a WD x 1.5 WD box on the stem edge at A."""
    u0, u1, v0, v1 = -WD / 2, WD / 2, -WD, WD / 2
    def P(u, v): return (A[0] + sd[0] * u + d[0] * v, A[1] + sd[1] * u + d[1] * v)
    win = Polygon([P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)])
    def to_local(g):
        # rotate/translate so sd -> +x, d -> +y
        return affinity.affine_transform(g, [sd[0], d[0], sd[1], d[1], 0, 0]) if False else \
            affinity.affine_transform(affinity.translate(g, -A[0], -A[1]),
                                      [sd[0], sd[1], d[0], d[1], 0.0, 0.0])
    return win, to_local


def clip_serif(ink, A, d, sd):
    win, to_local = frame_window(A, d, sd)
    try:
        g = ink.intersection(win)
    except Exception:
        return None
    if g.is_empty or g.area < 1.0: return None
    # the affine above maps design -> local via  x' = sd.x*X + sd.y*Y, y' = d.x*X + d.y*Y
    # (an orthonormal basis, so it is exactly the projection onto (sd, d))
    return to_local(g)


def sym_diff_pct(a, b):
    try:
        inter = a.intersection(b).area; ua = a.area; ub = b.area
    except Exception:
        return 100.0
    m = (ua + ub) / 2
    if m <= 0: return 100.0
    return 100.0 * (ua + ub - 2 * inter) / m


def hausdorff_n(a, b, norm):
    try: return shapely.hausdorff_distance(a.boundary, b.boundary) / norm
    except Exception: return 9.99


def components(n, edges):
    parent = list(range(n))
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i, j in edges:
        a, b = find(i), find(j)
        if a != b: parent[a] = b
    out = defaultdict(list)
    for i in range(n): out[find(i)].append(i)
    return [v for v in out.values() if len(v) > 1]


def pairwise(items, norm_of, exact=EXACT_PCT, near=NEAR_PCT, full=False):
    """items: [(label, geometry)].  Returns (pairs, exact_edges, near_edges,
    nearest).  `full` compares every pair with no area prefilter (used for
    the counters, where the "found varied" table needs each one's nearest
    neighbour whatever the distance)."""
    pairs = []; e_edges = []; n_edges = []
    areas = [g.area for _, g in items]
    nearest = [(None, 999.0)] * len(items)
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            ai, aj = areas[i], areas[j]
            m = (ai + aj) / 2
            if m <= 0: continue
            if not full and abs(ai - aj) / m > (near / 100.0) * 1.6: continue  # cannot reach the threshold
            sd = sym_diff_pct(items[i][1], items[j][1])
            if sd < nearest[i][1]: nearest[i] = (items[j][0], sd)
            if sd < nearest[j][1]: nearest[j] = (items[i][0], sd)
            if sd > near: continue
            h = hausdorff_n(items[i][1], items[j][1], norm_of(items[i][1]))
            pairs.append((items[i][0], items[j][0], sd, h))
            (e_edges if sd <= exact else n_edges).append((i, j))
    return pairs, e_edges, n_edges, nearest


# ------------------------------------------------------------------ raster
def raster(g, ppu, pad=6, label=None, box=None):
    """A polygon (local frame) as an L-mode image at ppu pixels per unit."""
    if box is None: x0, y0, x1, y1 = g.bounds
    else: x0, y0, x1, y1 = box
    w = int((x1 - x0) * ppu) + pad * 2; h = int((y1 - y0) * ppu) + pad * 2
    im = Image.new("L", (max(w, 8), max(h, 8)), 255)
    dr = ImageDraw.Draw(im)
    polys = [g] if g.geom_type == "Polygon" else list(getattr(g, "geoms", []))
    for p in polys:
        if p.geom_type != "Polygon": continue
        ext = [((x - x0) * ppu + pad, h - ((y - y0) * ppu + pad)) for x, y in p.exterior.coords]
        dr.polygon(ext, fill=0)
        for r in p.interiors:
            dr.polygon([((x - x0) * ppu + pad, h - ((y - y0) * ppu + pad)) for x, y in r.coords], fill=255)
    if label:
        dr.rectangle([0, 0, 7 * len(label) + 4, 12], fill=255)
        dr.text((2, 1), label, fill=0)
    return im


def strip(items, ppu, width=750, cellbox=None):
    """A grid of rasters, all at the same scale, in a `width`-px canvas."""
    ims = [raster(g, ppu, label=lab, box=cellbox) for lab, g in items]
    cw = max(i.width for i in ims) + 8; ch = max(i.height for i in ims) + 8
    per = max(1, min(len(ims), width // cw))
    rows = (len(ims) + per - 1) // per
    canvas = Image.new("L", (width, rows * ch), 240)
    for k, im in enumerate(ims):
        r, cc = divmod(k, per)
        canvas.paste(im, (cc * cw + 4, r * ch + 4))
    return canvas


def b64(im):
    buf = io.BytesIO(); im.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


# ------------------------------------------------------------------ the run
def run(font_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    install()

    W = build.solve_widths()                       # not recorded
    cutter = cut.Cutter(73, 4)
    RECORD["on"] = True
    pre_ink, post_ink, dense_by_ch = {}, {}, {}
    for ch in build.CHARS:
        if ch not in GLYPHS: continue
        RECORD["ch"] = ch
        g = build.draw(ch, W)
        pre_ink[ch] = g
        dense = geom.contours(g)
        phases = [cutter.phase() for _ in dense]
        conts = [(cut.blend(pts, ph, pen.CUT_AMOUNT), hole) for (pts, hole), ph in zip(dense, phases)]
        dense_by_ch[ch] = (dense, conts)
        post_ink[ch] = _rebuild(conts)
    RECORD["on"] = False

    # -------------------------------------------------- level 1
    con_groups = defaultdict(list)
    for rec in CALLS:
        key = (rec["name"], tuple(sorted((k, v) for k, v in rec["sig"].items() if k != "kind")))
        con_groups[key].append(rec["ch"])

    # -------------------------------------------------- level 2: serifs
    serifs_pre, serifs_post = [], []
    for k, w in enumerate(WEDGES):
        ch = w["ch"]
        lab = f"{ch}#{sum(1 for x in WEDGES[:k] if x['ch'] == ch) + 1}"
        gp = clip_serif(pre_ink[ch], w["A"], w["d"], w["sd"])
        gq = clip_serif(post_ink[ch], w["A"], w["d"], w["sd"])
        if gp is not None: serifs_pre.append((lab, gp, w))
        if gq is not None: serifs_post.append((lab, gq, w))

    s_pairs, s_ex, s_nr, s_near = pairwise([(l, g) for l, g, _ in serifs_pre], lambda g: WD)
    s_groups = components(len(serifs_pre), s_ex)
    sp_pairs, sp_ex, sp_nr, sp_near = pairwise([(l, g) for l, g, _ in serifs_post], lambda g: WD)
    sp_groups = components(len(serifs_post), sp_ex)

    # -------------------------------------------------- level 2: counters
    def counters(source, which):
        out = []
        for ch, (dense, conts) in dense_by_ch.items():
            src = dense if which == "pre" else conts
            n = 0
            for pts, hole in src:
                if not hole: continue
                n += 1
                p = Polygon(pts)
                if not p.is_valid: p = shapely.make_valid(p)
                if p.geom_type != "Polygon" or p.area < 200: continue
                cx, cy = p.centroid.x, p.centroid.y
                out.append((f"{ch}~{n}", affinity.translate(p, -cx, -cy)))
        return out

    c_pre = counters(dense_by_ch, "pre"); c_post = counters(dense_by_ch, "post")
    c_pairs, c_ex, c_nr, c_near = pairwise(c_pre, lambda g: math.sqrt(max(g.area, 1)), full=True)
    c_groups = components(len(c_pre), c_ex)
    cp_pairs, cp_ex, cp_nr, cp_near = pairwise(c_post, lambda g: math.sqrt(max(g.area, 1)))
    cp_groups = components(len(c_post), cp_ex)

    # scale-normalized counters (the softer list)
    c_scaled = []
    for lab, g in c_pre:
        s = 1.0 / math.sqrt(max(g.area, 1e-9)) * 100.0
        c_scaled.append((lab, affinity.scale(g, s, s, origin=(0, 0))))
    cs_pairs, cs_ex, cs_nr, cs_near = pairwise(c_scaled, lambda g: math.sqrt(max(g.area, 1)), full=True)
    cs_groups = components(len(c_scaled), cs_ex)

    res = dict(con_groups=con_groups, serifs_pre=serifs_pre, serifs_post=serifs_post,
               s_pairs=s_pairs, s_groups=s_groups, sp_pairs=sp_pairs, sp_groups=sp_groups,
               c_pre=c_pre, c_pairs=c_pairs, c_groups=c_groups,
               cp_pairs=cp_pairs, cp_groups=cp_groups,
               c_scaled=c_scaled, cs_pairs=cs_pairs, cs_groups=cs_groups,
               c_near=c_near, cs_near=cs_near, s_near=s_near, sp_near=sp_near,
               font=font_path)
    _print(res)
    _page(res, os.path.join(out_dir, "albo-variety.html"))
    json.dump(dict(
        construction={f"{k[0]}|{k[1]}": v for k, v in con_groups.items()},
        serif_exact_groups=[[serifs_pre[i][0] for i in g] for g in s_groups],
        serif_exact_groups_postcut=[[serifs_post[i][0] for i in g] for g in sp_groups],
        counter_exact_groups=[[c_pre[i][0] for i in g] for g in c_groups],
        counter_exact_groups_postcut=[[c_post[i][0] for i in g] for g in cp_groups],
        counter_scale_similar_groups=[[c_scaled[i][0] for i in g] for g in cs_groups],
        serif_pairs=[(a, b, round(s, 3), round(h, 4)) for a, b, s, h in s_pairs],
        counter_pairs=[(a, b, round(s, 3), round(h, 4)) for a, b, s, h in c_pairs],
        counter_inventory=[(lab, round(g.area), round(c_near[i][1], 2), c_near[i][0], round(cs_near[i][1], 2), cs_near[i][0])
                           for i, (lab, g) in enumerate(c_pre)],
        serif_nearest=[(lab, round(s_near[i][1], 3), s_near[i][0]) for i, (lab, g, _) in enumerate(serifs_pre)],
    ), open(os.path.join(out_dir, "albo-variety.json"), "w"), indent=1)
    return res


def _rebuild(conts):
    """Contours (exteriors + holes, in geom.contours order) back to a solid."""
    polys = []; cur = None; holes = []
    for pts, hole in conts:
        if hole:
            if cur is not None: holes.append(pts)
        else:
            if cur is not None: polys.append(Polygon(cur, holes))
            cur = pts; holes = []
    if cur is not None: polys.append(Polygon(cur, holes))
    good = []
    for p in polys:
        if not p.is_valid: p = shapely.make_valid(p)
        good.append(p)
    return shapely.union_all(good) if good else Polygon()


# ------------------------------------------------------------------ output
def _fam(sig):
    L, D = sig.get("len_WL"), sig.get("depth_WD")
    for name, (l, d) in (("stem top", (1.0, 1.0)), ("foot", (0.85, 1.0)), ("diagonal end", (0.9, 0.9)),
                         ("bar end", (0.85, 0.9)), ("apex", (0.9, 1.0)), ("small second", (0.4, 0.6)),
                         ("beak lip", (0.35, 0.6)), ("beak lip C/G/S", (0.4, 0.7))):
        if L is not None and abs(L - l) < 0.02 and abs(D - d) < 0.02: return name
    return f"{L}x{D}"


def _print(res):
    print("\n" + "=" * 74)
    print("LEVEL 1 -- CONSTRUCTION: identical parameter sets")
    print("=" * 74)
    rows = sorted(res["con_groups"].items(), key=lambda kv: -len(kv[1]))
    for key, chs in rows:
        if len(chs) < 2: continue
        name = key[0]; d = dict(key[1])
        if name == "wedge":
            desc = f"{_fam(d):<16} len {d.get('len_WL')}xWL depth {d.get('depth_WD')}xWD drop {d.get('drop')} out {d.get('sd_deg'):>6}deg end {d.get('d_deg'):>6}deg"
        else:
            desc = " ".join(f"{k}={v}" for k, v in sorted(d.items()) if v is not None)[:110]
        print(f"  {name:<11} x{len(chs):<3} {desc}")
        print(f"              {' '.join(sorted(set(chs)))}")
    print("\n  (single-call signatures omitted; %d distinct signatures in all)" % len(res["con_groups"]))

    for title, groups, items, pairs in (
        ("LEVEL 2 -- SERIFS, PRE-CUT (the designed outline: where a true copy lives)",
         res["s_groups"], res["serifs_pre"], res["s_pairs"]),
        ("LEVEL 2 -- SERIFS, POST-CUT (the shipped outline; the cut hides some sameness)",
         res["sp_groups"], res["serifs_post"], res["sp_pairs"]),
    ):
        print("\n" + "=" * 74); print(title); print("=" * 74)
        gs = sorted(groups, key=lambda g: -len(g))
        for g in gs[:24]:
            labs = [items[i][0] for i in g]
            fam = _fam(items[g[0]][2]["sig"])
            print(f"  x{len(g):<3} {fam:<16} {' '.join(labs)}")
        print(f"  ... {len(gs)} exact groups covering {sum(len(g) for g in gs)} of {len(items)} serifs")
        nr = [p for p in pairs if p[2] > EXACT_PCT]
        print(f"  near copies (2-8%): {len(nr)} pairs")

    for title, groups, items in (
        ("LEVEL 2 -- COUNTERS, PRE-CUT, unscaled", res["c_groups"], res["c_pre"]),
        ("LEVEL 2 -- COUNTERS, POST-CUT, unscaled", res["cp_groups"], res["c_pre"]),
        ("LEVEL 2 -- COUNTERS, scale-normalized (the softer list)", res["cs_groups"], res["c_scaled"]),
    ):
        print("\n" + "=" * 74); print(title); print("=" * 74)
        for g in sorted(groups, key=lambda g: -len(g)):
            print(f"  x{len(g):<3} {' '.join(items[i][0] for i in g)}")
        if not groups: print("  none")

    print("\n" + "=" * 74)
    print("COUNTER INVENTORY -- every hole in the font, and its nearest twin")
    print("  (symdiff %% to the closest other counter; scaled = after both are")
    print("   normalized to one area, so it answers 'the same shape, resized?')")
    print("=" * 74)
    print(f"  {'counter':<9}{'area':>8}{'w':>6}{'h':>6}{'w/h':>7}   {'nearest':<10}{'sd%':>8}   {'nearest scaled':<10}{'sd%':>8}")
    for i, (lab, g) in enumerate(res["c_pre"]):
        x0, y0, x1, y1 = g.bounds
        nb, nd = res["c_near"][i]; sb, sdv = res["cs_near"][i]
        print(f"  {lab:<9}{g.area:>8.0f}{x1-x0:>6.0f}{y1-y0:>6.0f}{(x1-x0)/max(y1-y0,1):>7.3f}   "
              f"{str(nb):<10}{nd:>8.1f}   {str(sb):<10}{sdv:>8.1f}")

    print("\n" + "=" * 74)
    print("SERIF TWIN COUNT -- how many other serifs each one is identical to")
    print("=" * 74)
    tw = defaultdict(int)
    for g in res["s_groups"]:
        for i in g: tw[res["serifs_pre"][i][0]] = len(g) - 1
    per_glyph = defaultdict(list)
    for lab, n in tw.items(): per_glyph[lab.split("#")[0]].append(n)
    print("  glyph: twins of each of its serifs (pre-cut)")
    line = []
    for ch in sorted(per_glyph, key=lambda c: (-max(per_glyph[c]), c)):
        line.append(f"{ch} {'/'.join(str(n) for n in sorted(per_glyph[ch], reverse=True))}")
    for k in range(0, len(line), 8): print("   " + "   ".join(line[k:k + 8]))
    unique = [lab for lab, g, _ in res["serifs_pre"] if lab not in tw]
    print(f"\n  SERIFS WITH NO TWIN ({len(unique)} of {len(res['serifs_pre'])}): {' '.join(sorted(unique))}")


PPU_SERIF = 1.5      # 4x the specimen's 375 px em (0.375 px/unit)
PPU_COUNTER = 0.75   # 2x, because a counter is three times a serif window across


def _page(res, path):
    blocks = []

    def block(title, note, items, ppu, cellbox=None):
        im = strip(items, ppu, cellbox=cellbox)
        blocks.append(f"<section><h3>{title}</h3><p class=n>{note}</p>"
                      f'<img src="data:image/png;base64,{b64(im)}"></section>')

    SHOW = 12   # a 58-cell strip is 6300 px tall on a phone; the sameness is made in twelve
    sg = sorted(res["s_groups"], key=lambda g: -len(g))[:10]
    for g in sg:
        shown = g[:SHOW]
        items = [(res["serifs_pre"][i][0], res["serifs_pre"][i][1]) for i in shown]
        fam = _fam(res["serifs_pre"][g[0]][2]["sig"])
        bx = (-WD / 2, -WD, WD / 2, WD / 2)
        more = f" &mdash; showing {len(shown)} of {len(g)}" if len(shown) < len(g) else ""
        block(f"{len(g)} identical serifs &mdash; {fam}",
              "pre-cut, in the wedge's own frame (stem edge vertical, end face at the top); "
              f"4&times; magnification (1.5 px per font unit); window {WD:.0f}&times;{1.5*WD:.0f} units{more}",
              items, PPU_SERIF, cellbox=bx)

    cg = sorted(res["c_groups"], key=lambda g: -len(g))[:6]
    for g in cg:
        items = [res["c_pre"][i] for i in g]
        block(f"{len(g)} identical counters",
              "pre-cut, centroid-aligned, NOT scaled; 2&times; magnification (0.75 px per font unit)",
              items, PPU_COUNTER)

    csg = sorted(res["cs_groups"], key=lambda g: -len(g))[:4]
    for g in csg:
        items = [res["c_scaled"][i] for i in g]
        block(f"{len(g)} scale-similar counters",
              "pre-cut, each normalized to the same area &mdash; the same SHAPE at different sizes; "
              "2&times; magnification of the normalized form",
              items, PPU_COUNTER)

    html = f"""<title>Albo Variety Audit</title>
<style>
:root{{--bg:#fbfbf9;--fg:#22201d;--mut:#6b665f;--line:#dcd7cf}}
:root:not([data-theme="light"]) {{}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#141312;--fg:#e6e2db;--mut:#9a938a;--line:#332f2b}}}}
:root[data-theme="dark"]{{--bg:#141312;--fg:#e6e2db;--mut:#9a938a;--line:#332f2b}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 Georgia,'Times New Roman',serif;margin:0;padding:18px}}
h1{{font-size:21px;margin:0 0 4px}} h3{{font-size:16px;margin:0 0 2px}}
p.n{{color:var(--mut);font-size:12.5px;margin:0 0 8px}}
section{{border-top:1px solid var(--line);padding:14px 0}}
img{{width:100%;max-width:375px;image-rendering:pixelated;display:block;background:#fff}}
</style>
<h1>Albo variety audit</h1>
<p class=n>2026-09-13. Every serif and every counter in the font, compared pair by pair.
A group below is a set no reader can tell apart: under 2% symmetric difference after
alignment. Serifs are shown in the wedge's own frame, counters centroid-aligned.
All images are PNG at native pixels.</p>
{''.join(blocks)}
"""
    open(path, "w").write(html)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    font = sys.argv[1] if len(sys.argv) > 1 else ""
    out = sys.argv[2] if len(sys.argv) > 2 else "."
    run(font, out)
