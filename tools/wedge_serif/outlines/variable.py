"""Albo-VF.ttf: the variable font (round 61, owner: "a variable axis font
that allows adjustment of contrast, ascender length, descender length,
line width, condensed to expanded, handcut to smooth and anything else").

    cd tools/wedge_serif && PYTHON_GIL=0 python3 -m outlines.variable <out_dir>

Every axis parameter reaches the drawing through an env override read at
import (pen.py, primitives.py), so ONE MASTER IS ONE SUBPROCESS of
outlines.build, built --nocut and dumped as float contours. 1 default +
2 per axis, sparse. Compatibility: the DEFAULT master keeps its dense
point set; every other master is matched to it contour by contour
(same hole flag, nearest centroid in bbox-normalized coordinates), its
start rotated to the point nearest the default's, and SAMPLED AT THE
DEFAULT'S ARC-LENGTH FRACTIONS, so point i sits at the same place along
every master's outline. The cut is then a DISPLACEMENT on that dense set:
the shipping 1-in-4 cut (seed 73, the same phase sequence) keeps a set of
indices per contour, and every other point is moved onto the chord
between its kept neighbours -- the polygon renders exactly as the
decimated one. CUTS 0 is the dense outline unprojected, CUTS 200 the
projection displaced twice; corners are kept per master (detected on the
master's own points), so a master's corners are never chamfered."""
import os, sys, json, math, subprocess, html, base64, io, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT)
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, SourceDescriptor
from fontTools import varLib
from fontTools.varLib.instancer import instantiateVariableFont
import round19
from . import geom, cut
from .cut import corners, project

CHARS, GLYPH_ORDER, gname = round19.CHARS, round19.GLYPH_ORDER, round19.gname

from . import pen as _pen
D_ = _pen.DESIGN
# tag, name, min, default, max, env var, (min value, max value) as the env var wants them.
# Defaults are the static builder's (pen.DESIGN; round 65: wght 84, CNTR 0.95,
# ASCN 770, DESC 280, wdth 100, CUTS 87, XHGT 429, SRIF 92). The wght and CNTR
# ranges are FOUND by build_vf: the widest end at which no more than three
# glyphs need a per-glyph clamp (round 62; the candidates are in RANGE_TRIALS).
AXES = [
    ["wght", "Weight",    50,   D_["stem"],     140,  "FJORD_STEM",     (50, 140)],
    ["CNTR", "Contrast",  0.00, D_["contrast"], 1.00, "FJORD_CONTRAST", (0.00, 1.00)],
    ["ASCN", "Ascender",  700,  D_["asc"],      830,  "FJORD_ASC",      (700, 830)],
    ["DESC", "Descender", 180,  D_["desc"],     340,  "FJORD_DESC",     (180, 340)],
    ["wdth", "Width",     80,   100,            120,  "FJORD_WIDTH",    (80, 120)],
    ["CUTS", "Cut",       0,    D_["cut"],      200,  None,             (0, 200)],
    ["XHGT", "x-height",  380,  D_["xh"],       460,  "FJORD_XH",       (380, 460)],
    ["SRIF", "Serif",     60,   D_["serif"],    140,  "FJORD_SERIF",    (60, 140)],
]
# Round 62 found wght 50/140 and CNTR 0.05/0.95 by trial (RANGE_TRIALS);
# round 65 rules the contrast range 0.00 / 0.95 / 1.00 outright and keeps
# wght 50/140, so no search runs -- glyphs that change topology at an end
# are clamped per glyph as before.
RANGE_TRIALS = {}
MAX_CLAMPED_GLYPHS = 3
PREVIOUS = ("round 62", {"wght": 84, "CNTR": 0.80, "ASCN": 770, "DESC": 256, "wdth": 100, "CUTS": 115, "XHGT": 429, "SRIF": 100})

# ---------------------------------------------------------------- masters (subprocesses)
def build_master(out_dir, name, env_over):
    """One outlines.build subprocess, --nocut, dumped as JSON. Returns the JSON path."""
    mdir = os.path.join(out_dir, "masters"); os.makedirs(mdir, exist_ok=True)
    js = os.path.join(mdir, f"{name}.json")
    env = dict(os.environ); env.update({k: str(v) for k, v in env_over.items()}); env["PYTHON_GIL"] = "0"
    r = subprocess.run([sys.executable, "-m", "outlines.build", mdir, "--nocut", "--style", "m_" + name, "--dump", js], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(js): raise RuntimeError(f"master {name} failed:\n{r.stderr[-2000:]}")
    return js

def build_masters_parallel(out_dir, specs, workers=None):
    workers = workers or int(os.environ.get('FJORD_VF_JOBS', 3))   # 2026-09-13: six parallel builds ran the Mac out of memory and the run was killed; three is safe
    """specs: [(name, env_over)]; returns {name: json_path}."""
    mdir = os.path.join(out_dir, "masters"); os.makedirs(mdir, exist_ok=True)
    procs = {}; out = {}; pending = list(specs)
    while pending or procs:
        while pending and len(procs) < workers:
            name, env_over = pending.pop(0); js = os.path.join(mdir, f"{name}.json")
            env = dict(os.environ); env.update({k: str(v) for k, v in env_over.items()}); env["PYTHON_GIL"] = "0"
            procs[name] = (subprocess.Popen([sys.executable, "-m", "outlines.build", mdir, "--nocut", "--style", "m_" + name, "--dump", js], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True), js)
        for name, (p, js) in list(procs.items()):
            if p.poll() is not None:
                err = p.stderr.read(); del procs[name]
                if p.returncode != 0 or not os.path.exists(js): raise RuntimeError(f"master {name} failed:\n{err[-1500:]}")
                out[name] = js
        import time; time.sleep(0.3)
    return out

def load(js):
    d = json.load(open(js)); g = {}
    for ch, r in d["glyphs"].items():
        g[ch] = dict(adv=r["adv"], lsb=r["lsb"], phases=r.get("phases"), contours=[([tuple(p) for p in pts], hole) for pts, hole in r["contours"]])
    return dict(space=d["space"], params=d["params"], glyphs=g)

# ---------------------------------------------------------------- compatibility
def bbox_of(conts):
    xs = [x for pts, _ in conts for x, y in pts]; ys = [y for pts, _ in conts for x, y in pts]
    return min(xs), min(ys), max(xs), max(ys)

def norm(p, bb):
    x0, y0, x1, y1 = bb; w = max(1e-6, x1 - x0); h = max(1e-6, y1 - y0)
    return ((p[0] - x0) / w, (p[1] - y0) / h)

def centroid(pts):
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

def cum_fractions(pts):
    d = [0.0]
    for a, b in zip(pts, pts[1:] + pts[:1]): d.append(d[-1] + math.dist(a, b))
    L = d[-1] or 1.0
    return [v / L for v in d[:-1]], L

def sample_at(pts, fracs):
    """Points on the closed polyline `pts` at the given arc-length fractions."""
    d, L = cum_fractions(pts); d = d + [1.0]; n = len(pts); out = []; j = 0
    for f in fracs:
        f = min(max(f, 0.0), 1.0 - 1e-9)
        while j < n - 1 and d[j + 1] <= f: j += 1
        while j > 0 and d[j] > f: j -= 1
        a = pts[j]; b = pts[(j + 1) % n]; seg = d[j + 1] - d[j]; t = (f - d[j]) / seg if seg > 1e-12 else 0.0
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out

def match_contours(default_conts, master_conts, bb_d, bb_m):
    """Pair each default contour with the master contour of the same hole
    flag whose bbox-normalized centroid is nearest (one-to-one, greedy)."""
    used = set(); order = []
    for pts, hole in default_conts:
        cd = norm(centroid(pts), bb_d); best = None
        for j, (mpts, mhole) in enumerate(master_conts):
            if j in used or mhole != hole: continue
            cm = norm(centroid(mpts), bb_m); dist = math.dist(cd, cm)
            if best is None or dist < best[0]: best = (dist, j)
        if best is None: return None
        used.add(best[1]); order.append(master_conts[best[1]])
    return order

def align_start(mpts, d0_norm, bb_m):
    """Rotate the master contour so its start is the point nearest the default's start (normalized)."""
    k = min(range(len(mpts)), key=lambda i: math.dist(norm(mpts[i], bb_m), d0_norm))
    return mpts[k:] + mpts[:k]

def align_corners(fd_c, fm_c, gap=0.06):
    """Order-preserving alignment of two corner sequences (fractions along
    their contours): the monotone pairing minimizing the sum of |fd - fm|
    over pairs plus `gap` per unpaired corner (Needleman-Wunsch). A corner
    present on one side only costs a gap instead of stealing its neighbour's
    partner, which is what a greedy nearest-in-window pairing did at the
    E's bar ends."""
    n, m = len(fd_c), len(fm_c)
    INF = float("inf"); D = [[INF] * (m + 1) for _ in range(n + 1)]; B = [[None] * (m + 1) for _ in range(n + 1)]
    D[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0: continue
            best = (INF, None)
            if i > 0 and j > 0 and D[i - 1][j - 1] + abs(fd_c[i - 1] - fm_c[j - 1]) < best[0]: best = (D[i - 1][j - 1] + abs(fd_c[i - 1] - fm_c[j - 1]), "p")
            if i > 0 and D[i - 1][j] + gap < best[0]: best = (D[i - 1][j] + gap, "d")
            if j > 0 and D[i][j - 1] + gap < best[0]: best = (D[i][j - 1] + gap, "m")
            D[i][j], B[i][j] = best
    pairs = []; i, j = n, m
    while i > 0 or j > 0:
        b = B[i][j]
        if b == "p": pairs.append((i - 1, j - 1)); i -= 1; j -= 1
        elif b == "d": i -= 1
        else: j -= 1
    return pairs[::-1]

def sample_like(dpts, mpts, deg=30.0):
    """The master contour sampled at the default's arc-length fractions,
    CORNER-ANCHORED: the two contours' corners (turns over `deg`) are
    aligned in order (align_corners), and each stretch between paired
    corners is sampled at the default's fractions within that stretch --
    so every paired corner lands exactly, and a bar whose length changed
    with an axis keeps its end faces square instead of having them cut to
    a slant by a chord between two samples (the E, T and ] at the weight
    and width ends)."""
    fd, _ = cum_fractions(dpts); fm, _ = cum_fractions(mpts)
    cd = [i for i in sorted(corners(dpts, deg)) if i > 0]; cm = [j for j in sorted(corners(mpts, deg)) if j > 0]
    al = align_corners([fd[i] for i in cd], [fm[j] for j in cm])
    pairs = [(0, 0)] + [(cd[a], cm[b]) for a, b in al if abs(fd[cd[a]] - fm[cm[b]]) <= 0.12] + [(len(dpts), len(mpts))]
    fdx = fd + [1.0]; fmx = fm + [1.0]; fr = [0.0] * len(dpts)
    for (a_d, a_m), (b_d, b_m) in zip(pairs, pairs[1:]):
        span_d = fdx[b_d] - fdx[a_d]; span_m = fmx[b_m] - fmx[a_m]
        for k in range(a_d, b_d):
            u = (fdx[k] - fdx[a_d]) / span_d if span_d > 1e-12 else 0.0
            fr[k] = fmx[a_m] + u * span_m
    return sample_at(mpts, fr)

def compatibilize(default, master, label):
    """Master glyphs re-expressed on the default's point structure. Returns
    (glyphs, problems): glyphs[ch] = (contours [(pts, hole)], adv, lsb);
    problems = [(ch, message)] for glyphs whose topology did not match
    (those are NOT in glyphs)."""
    out = {}; problems = []
    for ch, dg in default["glyphs"].items():
        mg = master["glyphs"].get(ch)
        if mg is None: problems.append((ch, "missing in master")); continue
        dconts = dg["contours"]; mconts = mg["contours"]
        if len(mconts) != len(dconts):
            # a union sliver under 200 units of area is not a topology change
            big = [(pts, hole) for pts, hole in mconts if abs(geom.signed_area(pts)) >= 200.0]
            if len(big) == len(dconts): mconts = big
            else: problems.append((ch, f"{len(mconts)} contours against the default's {len(dconts)}")); continue
        bb_d = bbox_of(dconts); bb_m = bbox_of(mconts)
        matched = match_contours(dconts, mconts, bb_d, bb_m)
        if matched is None: problems.append((ch, "hole/outer counts differ")); continue
        conts = []; sliver = None
        for (dpts, hole), (mpts, mhole) in zip(dconts, matched):
            mpts = align_start(mpts, norm(dpts[0], bb_d), bb_m)
            spts = sample_like(dpts, mpts); conts.append((spts, hole))
            # round 65: a resampled contour that crosses itself by a real
            # sliver (a join resampled across a tight junction) is a clamp
            # case like a topology change; zero-area pinches from integer
            # rounding are not (they appear only in make_glyph, after this)
            a = crossing_sliver(spts)
            if a >= SLIVER_MIN and (sliver is None or a > sliver[0]): sliver = (a, spts)
        if sliver: problems.append((ch, f"resampled contour crosses itself, sliver {sliver[0]:.0f} units^2")); continue
        out[ch] = (conts, mg["adv"], mg["lsb"])
    return out, problems

SLIVER_MIN = 4.0   # units^2: below this a self-crossing is a rounding pinch, not a drawing
def crossing_sliver(pts):
    """Area of the smallest piece a self-crossing contour splits into (0 when
    it is valid or the crossing is a zero-area pinch)."""
    from shapely.geometry import Polygon
    from shapely.validation import make_valid
    if len(pts) < 4: return 0.0
    p = Polygon(pts)
    if p.is_valid: return 0.0
    mv = make_valid(p); pieces = [g.area for g in getattr(mv, "geoms", [mv]) if g.area > 0]
    return min(pieces) if len(pieces) > 1 else 0.0

# ---------------------------------------------------------------- the cut as a displacement
def cut_plans(default):
    """The shipping cut's phase per contour: the static builder dumps them
    (the same Cutter sequence it cut with), so the VF's default master is
    the static's construction to the point."""
    return {ch: g["phases"] for ch, g in default["glyphs"].items()}

def apply_cut(conts, phases, amount=100.0):
    """cut.blend on every contour: 0 the dense outline, 100 the 1-in-4
    projection, 200 the 1-in-8 (facets twice as long), linear between. (A
    first version moved each point twice its cut displacement for 200,
    which gouged past neighbouring edges at the brackets.)"""
    return [(cut.blend(pts, ph, amount), hole) for (pts, hole), ph in zip(conts, phases)]

# ---------------------------------------------------------------- master TTFs
def make_glyph(conts):
    """A glyf glyph straight from coordinates: TTGlyphPen drops a last
    point that rounds onto the first, which happened in some masters and
    not others (the n and u lost a point in one master each), and every
    master must keep every point."""
    import array
    from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
    from fontTools.ttLib.tables import ttProgram
    g = Glyph(); coords = []; ends = []
    for pts, hole in conts:
        for x, y in pts: coords.append((round(x), round(y)))
        ends.append(len(coords) - 1)
    g.coordinates = GlyphCoordinates(coords); g.endPtsOfContours = ends
    g.flags = array.array("B", [1] * len(coords)); g.numberOfContours = len(conts)
    g.program = ttProgram.Program(); g.program.fromBytecode(b"")
    return g

def write_master(path, glyphs, space, name="Albo", style="Master", xh=415, cap=674):
    fb = FontBuilder(1000, isTTF=True); fb.setupGlyphOrder(GLYPH_ORDER)
    fb.setupCharacterMap({ord(ch): gname(ch) for ch in CHARS} | {32: 'space'})
    glyf, metrics = {}, {}
    for ch in CHARS:
        conts, adv, lsb = glyphs[ch]
        glyf[gname(ch)] = make_glyph(conts)
        xmin = min(round(x) for pts, _ in conts for x, y in pts)
        metrics[gname(ch)] = (int(round(adv)), xmin)
    p = TTGlyphPen(None); p.moveTo((50, 0)); p.lineTo((50, 700)); p.lineTo((450, 700)); p.lineTo((450, 0)); p.closePath()
    glyf['.notdef'] = p.glyph(); metrics['.notdef'] = (500, 50)
    glyf['space'] = TTGlyphPen(None).glyph(); metrics['space'] = (int(space), 0)
    fb.setupGlyf(glyf); fb.setupHorizontalMetrics(metrics); fb.setupHorizontalHeader(ascent=900, descent=-300)
    fb.setupNameTable(dict(familyName=name, styleName=style, fullName=f"{name} {style}", psName=f"{name}-{style}", uniqueFontIdentifier=f"{name};{style};2026-09-13"))
    fb.setupOS2(sTypoAscender=900, sTypoDescender=-300, usWinAscent=900, usWinDescent=300, sxHeight=int(xh), sCapHeight=int(cap))
    fb.setupPost(); fb.save(path); return path

# ---------------------------------------------------------------- the build
ENV_DEFAULT = {"FJORD_STEM": D_["stem"], "FJORD_CONTRAST": D_["contrast"], "FJORD_ASC": D_["asc"], "FJORD_DESC": D_["desc"], "FJORD_WIDTH": 100, "FJORD_XH": D_["xh"], "FJORD_SERIF": D_["serif"]}
CAP = 415 * 1.625; OVER = 14
import alphabet2 as A
import round20

def fit_master(ch, conts, params):
    """Round 20's fitting rule on the PROJECTED (cut) contours with the
    master's own x-height and width -- the masters were built --nocut, and
    the dense outline reaches ~2 units past the cut polygon, which shifted
    every default glyph 2 units and its advance with it."""
    xh = params["xh"]; width = params["width"]
    isCap = ch.isupper() or ch.isdigit(); top = CAP if isCap else xh
    xs_all = [x for pts, _ in conts for x, y in pts]
    band = [x for pts, _ in conts for x, y in pts if -OVER <= y <= top + OVER]
    l, r = (min(band), max(band)) if band else (min(xs_all), max(xs_all))
    if ch == 'g' or not ch.isalpha(): l, r = min(xs_all), max(xs_all)
    lt, rt = round19.SIDES.get(ch, ('straight', 'straight'))
    capbear = round20.REF["Hbear"] / 2 * CAP * width
    lsb = capbear * A.SIDE_FRACTION[lt] + 17; rsb = capbear * A.SIDE_FRACTION[rt] + 17
    adv = lsb + (r - l) + rsb; dx = lsb - l
    return adv, dx

def finish(glyphs, params, phases, amount=None):
    """Project the cut onto every glyph and re-fit it: {ch: (contours, adv, lsb)}."""
    out = {}
    if amount is None: amount = D_["cut"]
    for ch, (conts, adv0, lsb0) in glyphs.items():
        cut_conts = apply_cut(conts, phases[ch], amount=amount)
        adv, dx = fit_master(ch, cut_conts, params)
        moved = [([(x + dx, y) for x, y in pts], hole) for pts, hole in cut_conts]
        out[ch] = (moved, adv, min(x for pts, _ in moved for x, y in pts))
    return out

def master_with_clamps(out_dir, default, mname, env_over, jsons, report, log):
    """A drawn master compatibilized against the default, with the PER-GLYPH
    clamp loop: a glyph whose topology changes at this location takes its
    contours from a rebuild with every set parameter pulled 25% toward its
    default, again until it matches; every other glyph keeps the location.
    Nothing is dropped; every clamp is reported. Returns (glyphs, master)."""
    js = jsons.get(mname) or build_master(out_dir, mname, env_over); m = load(js)
    glyphs, problems = compatibilize(default, m, mname)
    over = dict(env_over); attempt = 0
    while problems and attempt < 5:
        attempt += 1; over = {k: ENV_DEFAULT[k] + (v - ENV_DEFAULT[k]) * 0.75 for k, v in over.items()}
        log(f"  {mname}: {', '.join(ch for ch, _ in problems)} changed topology; those take a rebuild at {over}")
        m2 = load(build_master(out_dir, f"{mname}_clamp{attempt}", over)); g2, p2 = compatibilize(default, m2, mname)
        still = []
        for ch, msg in problems:
            if ch in g2: glyphs[ch] = g2[ch]; report["clamps"].append((mname, ch, msg, dict(over)))
            else: still.append((ch, msg))
        problems = still
    for ch, msg in problems:
        glyphs[ch] = (default["glyphs"][ch]["contours"], default["glyphs"][ch]["adv"], default["glyphs"][ch]["lsb"])
        report["clamps"].append((mname, ch, msg + " -- GAVE UP, default contours", None))
    return glyphs, m

def corners_spec():
    r = {t: (mn, mx) for t, n, mn, d, mx, *_ in AXES}
    return [("wght_max_wdth_min", {"FJORD_STEM": r["wght"][1], "FJORD_WIDTH": 80}, {"wght": r["wght"][1], "wdth": 80}),
            ("XHGT_max_ASCN_min", {"FJORD_XH": 460, "FJORD_ASC": 700}, {"XHGT": 460, "ASCN": 700}),
            ("wght_max_CNTR_max", {"FJORD_STEM": r["wght"][1], "FJORD_CONTRAST": r["CNTR"][1]}, {"wght": r["wght"][1], "CNTR": r["CNTR"][1]}),
            ("wght_min_CNTR_min", {"FJORD_STEM": r["wght"][0], "FJORD_CONTRAST": r["CNTR"][0]}, {"wght": r["wght"][0], "CNTR": r["CNTR"][0]}),
            ("wght_min_CNTR_max", {"FJORD_STEM": r["wght"][0], "FJORD_CONTRAST": r["CNTR"][1]}, {"wght": r["wght"][0], "CNTR": r["CNTR"][1]})]

def find_ranges(out_dir, default, log):
    """Round 62: try the wider ends (RANGE_TRIALS) and pull each in to the
    widest value at which no more than MAX_CLAMPED_GLYPHS glyphs change
    topology. Every trial is one subprocess; they run in parallel."""
    specs = []
    for (tag, side), vals in RANGE_TRIALS.items():
        envk = next(a[5] for a in AXES if a[0] == tag)
        for v in vals: specs.append((f"trial_{tag}_{side}_{v}", {envk: v}))
    jsons = build_masters_parallel(out_dir, specs)
    found = {}; trials = {}
    for (tag, side), vals in RANGE_TRIALS.items():
        envk = next(a[5] for a in AXES if a[0] == tag)
        for v in vals:
            m = load(jsons[f"trial_{tag}_{side}_{v}"]); glyphs, problems = compatibilize(default, m, f"trial {tag} {side} {v}")
            trials[(tag, side, v)] = [ch for ch, _ in problems]
            log(f"  trial {tag} {side} = {v}: {len(problems)} glyphs change topology" + (f" ({', '.join(ch for ch, _ in problems)})" if problems else ""))
            if len(problems) <= MAX_CLAMPED_GLYPHS: found[(tag, side)] = (v, jsons[f"trial_{tag}_{side}_{v}"]); break
        else:
            v = vals[-1]; found[(tag, side)] = (v, jsons[f"trial_{tag}_{side}_{v}"])
    for i, a in enumerate(AXES):
        if (a[0], "min") in found and (a[0], "max") in found:
            mn = found[(a[0], "min")][0]; mx = found[(a[0], "max")][0]
            AXES[i] = [a[0], a[1], mn, a[3], mx, a[5], (mn, mx)]
    return found, trials

def build_vf(out_dir, log=print):
    os.makedirs(out_dir, exist_ok=True); mdir = os.path.join(out_dir, "masters")
    report = dict(clamps=[], masters={}, trials={})
    default = load(build_master(out_dir, "default", {})); phases = cut_plans(default)
    found, report["trials"] = find_ranges(out_dir, default, log) if RANGE_TRIALS else ({}, {})
    log("ranges: " + ", ".join(f"{a[0]} {a[2]} / {a[3]} / {a[4]}" for a in AXES if a[0] in ("wght", "CNTR")))
    jsons = {"default": os.path.join(mdir, "default.json")}
    specs = []
    for tag, name, mn, df, mx, envk, (vmin, vmax) in AXES:
        if envk is None: continue
        for side, v in (("min", vmin), ("max", vmax)):
            if (tag, side) in found: jsons[f"{tag}_{side}"] = found[(tag, side)][1]
            else: specs.append((f"{tag}_{side}", {envk: v}))
    for cname, env_over, loc in corners_spec(): specs.append((cname, env_over))
    log(f"building {len(specs)} more masters in subprocesses ...")
    jsons.update(build_masters_parallel(out_dir, specs))
    dense_default = {ch: (g["contours"], g["adv"], g["lsb"]) for ch, g in default["glyphs"].items()}
    cut_default = D_["cut"]
    masters = {"default": (finish(dense_default, default["params"], phases, cut_default), default["space"], {}),
               "CUTS_min": (finish(dense_default, default["params"], phases, 0.0), default["space"], {"CUTS": 0}),
               "CUTS_max": (finish(dense_default, default["params"], phases, 200.0), default["space"], {"CUTS": 200})}
    for tag, name, mn, df, mx, envk, (vmin, vmax) in AXES:
        if envk is None: continue
        for side, target in (("min", vmin), ("max", vmax)):
            mname = f"{tag}_{side}"
            glyphs, m = master_with_clamps(out_dir, default, mname, {envk: target}, jsons, report, log)
            masters[mname] = (finish(glyphs, m["params"], phases, cut_default), m["space"], {tag: mn if side == "min" else mx})
            report["masters"][mname] = dict(value=target, params=m["params"])
            if mname == "CNTR_max":   # the derived corner: contrast max at CUTS 200
                masters["CNTR_max_CUTS_max"] = (finish(glyphs, m["params"], phases, 200.0), m["space"], {"CNTR": mx, "CUTS": 200})
    for cname, env_over, loc in corners_spec():
        glyphs, m = master_with_clamps(out_dir, default, cname, env_over, jsons, report, log)
        masters[cname] = (finish(glyphs, m["params"], phases, cut_default), m["space"], loc)
        report["masters"][cname] = dict(value=env_over, params=m["params"])
    # write the master TTFs and the designspace
    ds = DesignSpaceDocument()
    for tag, name, mn, df, mx, envk, _ in AXES:
        a = AxisDescriptor(); a.tag = tag; a.name = name; a.minimum = mn; a.default = df; a.maximum = mx; ds.addAxis(a)
    default_loc = {name: df for tag, name, mn, df, mx, envk, _ in AXES}; tag2name = {t: n for t, n, *_ in AXES}
    for mname, (glyphs, space, loc) in masters.items():
        xh = report["masters"].get(mname, {}).get("params", {}).get("xh", D_["xh"])
        path = write_master(os.path.join(mdir, f"Albo-{mname}.ttf"), glyphs, space, style=mname, xh=xh)
        s_ = SourceDescriptor(); s_.path = path; s_.name = mname; s_.familyName = "Albo"; s_.styleName = mname
        location = dict(default_loc)
        for tag, v in loc.items(): location[tag2name[tag]] = v
        s_.location = location; ds.addSource(s_)
    ds_path = os.path.join(out_dir, "Albo.designspace"); ds.write(ds_path)
    vf, model, _ = varLib.build(ds_path, exclude=["MVAR"])
    vf["name"].setName("Albo", 1, 3, 1, 0x409); vf["name"].setName("Albo", 16, 3, 1, 0x409)
    vf_path = os.path.join(out_dir, "Albo-VF.ttf"); vf.save(vf_path)
    log(f"wrote {vf_path}  ({len(masters)} masters)")
    return vf_path, report, masters

# ---------------------------------------------------------------- verification
def contours_of(font, gn):
    g = font['glyf'][gn]
    if g.numberOfContours <= 0: return []
    coords, ends, flags = g.getCoordinates(font['glyf']); out = []; start = 0
    for e in ends:
        out.append([tuple(p) for p in coords[start:e + 1]]); start = e + 1
    return out

def defects(font):
    """Per glyph: self-intersecting contours + crossing contour pairs + contours wound against their area sign."""
    from shapely.geometry import Polygon
    import shapely
    out = {}
    for gn in font.getGlyphOrder():
        cs = contours_of(font, gn)
        if not cs: continue
        bad = 0; polys = []
        for c in cs:
            if len(c) < 3: bad += 1; continue
            p = Polygon(c)
            if not p.is_valid: bad += 1
            polys.append(p)
        for i in range(len(polys)):
            for j in range(i + 1, len(polys)):
                try:
                    if polys[i].is_valid and polys[j].is_valid and polys[i].boundary.crosses(polys[j].boundary): bad += 1
                except Exception: bad += 1
        if bad: out[gn] = bad
    return out

def instance(vf_path, loc, out_path):
    vf = TTFont(vf_path); st = instantiateVariableFont(vf, loc); st.save(out_path); return out_path

def compare_to_static(inst_path, static_path):
    """Max distance from any vertex of the static font's outline to the instance's outline, per glyph; the max over glyphs."""
    from shapely.geometry import LineString, Point
    a = TTFont(static_path); b = TTFont(inst_path); worst = (0.0, None)
    for gn in a.getGlyphOrder():
        ca = contours_of(a, gn); cb = contours_of(b, gn)
        if not ca or not cb: continue
        rings = [LineString(c + [c[0]]) for c in cb if len(c) >= 2]
        for c in ca:
            for p in c:
                d = min(r.distance(Point(p)) for r in rings)
                if d > worst[0]: worst = (d, gn)
    return worst

def page_ink(path, px=54):
    import word_weight
    from PIL import ImageFont
    f = ImageFont.truetype(path, px)
    return sum(word_weight.measure_word(f, w, px)["ink"] for w in word_weight.WORDS)

def render_line(path, text, px=150, label=""):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(path, px); a, d = f.getmetrics(); w = int(f.getlength(text)) + 40
    im = Image.new('L', (w, a + d + 24), 255); dr = ImageDraw.Draw(im); dr.text((6, 3), label, fill=120); dr.text((20, 20 + a), text, font=f, fill=0, anchor='ls')
    return im

def stack(ims, gap=8):
    from PIL import Image
    W = max(i.size[0] for i in ims); H = sum(i.size[1] for i in ims) + gap * len(ims)
    s = Image.new('L', (W, H), 255); y = 0
    for i in ims: s.paste(i, (0, y)); y += i.size[1] + gap
    return s

# ---------------------------------------------------------------- pages
def slider_page(vf_path, out):
    b = base64.b64encode(open(vf_path, "rb").read()).decode()
    rows = ''.join(f'<div class="ax"><label for="a_{tag}">{html.escape(name)} <code>{tag}</code></label><input type="range" id="a_{tag}" data-tag="{tag}" min="{mn}" max="{mx}" value="{df}" step="{0.01 if mx - mn < 5 else 1}"><b id="v_{tag}">{df}</b></div>' for tag, name, mn, df, mx, *_ in AXES)
    para = html.escape(round19.PARAGRAPHS[1])
    return f'''<title>Albo Variable</title>
<style>@font-face{{font-family:"AlboVF";src:url(data:font/ttf;base64,{b}) format("truetype")}}
:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:16px 12px 60px;font:15px/1.45 -apple-system,Arial,sans-serif}}main{{max-width:900px;margin:0 auto}}h1{{font-size:22px;margin:0 0 4px}}p.lede{{color:var(--soft);font-size:13px;max-width:64ch;margin:0 0 14px}}
.ctl{{position:sticky;top:0;background:var(--paper);border-bottom:1px solid var(--rule);padding:8px 0 10px;z-index:2}}.ax{{display:grid;grid-template-columns:9.5em 1fr 4.5em;gap:8px;align-items:center;margin:3px 0}}.ax label{{font-size:13px}}.ax code{{color:var(--soft);font-size:11px}}.ax input{{width:100%}}.ax b{{font-variant-numeric:tabular-nums;text-align:right;font-size:13px}}
button{{margin-top:6px;font:13px -apple-system,Arial;padding:4px 12px;border:1px solid var(--rule);background:transparent;color:var(--ink);border-radius:4px}}
.vf{{font-family:"AlboVF",serif}}h2{{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--soft);margin:22px 0 6px;border-top:1px solid var(--rule);padding-top:10px}}
.big{{font-size:52px;line-height:1.15;margin:0;word-break:break-word}}.text{{font-size:22px;line-height:1.4;margin:0;max-width:34em}}.read{{font-size:26px;line-height:1.25;margin:0;max-width:22em}}</style>
<main><h1>Albo Variable</h1><p class="lede">Eight axes on one file, set live by <code>font-variation-settings</code>. Defaults are the shipping Albo Medium (the 500; the calibrated 400 is Albo Regular). The "at reading size" block is 13 pt on a 2x reader pretended at 26 px.</p>
<div class="ctl">{rows}<button id="reset">Reset to the shipping defaults</button></div>
<h2>52 px</h2><p class="vf big">Hamburgefonstiv quick fjord zephyrs &amp; 1234567890</p>
<h2>22 px</h2><p class="vf text">{para}</p>
<h2>At reading size (13 pt on 2x)</h2><p class="vf read">{para}</p>
<script>
const A={json.dumps([[t, df] for t, n, mn, df, mx, *_ in AXES])};
function apply(){{const s=A.map(([t,d])=>{{const el=document.getElementById('a_'+t);document.getElementById('v_'+t).textContent=(+el.value).toFixed(el.step==='1'?0:2);return '"'+t+'" '+el.value}}).join(', ');document.querySelectorAll('.vf').forEach(e=>e.style.fontVariationSettings=s)}}
A.forEach(([t])=>document.getElementById('a_'+t).addEventListener('input',apply));
document.getElementById('reset').addEventListener('click',()=>{{A.forEach(([t,d])=>document.getElementById('a_'+t).value=d);apply()}});apply();
</script></main>'''

def proof_page(vf_path, out_dir):
    from .cmp.proof import b64, eink
    tmp = os.path.join(out_dir, "instances"); os.makedirs(tmp, exist_ok=True)
    default_loc = {tag: df for tag, name, mn, df, mx, *_ in AXES}
    figs = []
    def img(im, cap): figs.append(f'<figure><img src="{b64(im)}" width="{im.size[0]}" height="{im.size[1]}"><figcaption>{html.escape(cap)}</figcaption></figure>')
    para = round19.PARAGRAPHS[1][:260]
    import word_weight; words = " ".join(word_weight.WORDS)   # round 65 (owner: "always pay attention to the space inside and between characters"): the rhythm first
    p = instance(vf_path, dict(default_loc), os.path.join(tmp, "default.ttf")); cap = "the new default: " + ", ".join(f"{t} {v}" for t, v in default_loc.items())
    img(eink(p, words), cap + " -- the 147 common words"); img(eink(p, para), cap)
    pprev = instance(vf_path, dict(PREVIOUS[1]), os.path.join(tmp, "previous.ttf")); cap = f"the {PREVIOUS[0]} default for comparison: " + ", ".join(f"{t} {v}" for t, v in PREVIOUS[1].items())
    img(eink(pprev, words), cap + " -- the 147 common words"); img(eink(pprev, para), cap)
    # the space inside and between: counters, apertures, fitting, on the default instance
    from .cmp import space as SP
    prev_static = os.environ.get("ALBO_PREVIOUS_STATIC"); prev_used = prev_static if prev_static and os.path.exists(prev_static) else pprev
    lines, m, counters, apertures = SP.describe(p, prev_used)
    wide = instance(vf_path, dict(default_loc, wdth=120), os.path.join(tmp, "wdth_120_probe.ttf")); r100 = m["o_counter"][2]; r120 = SP.metrics(wide)["o_counter"][2]
    if abs(r120 - r100) > 1e-6: lines.append(f"on the wdth axis the o's counter reads {r100:.3f} at 100 and {r120:.3f} at 120, so wdth {100 + (SP.O_RULING - r100) / (r120 - r100) * 20:.0f} would put it on the {SP.O_RULING} ruling (not applied; the width is his call)")
    lines[2] = lines[2].replace("against " + os.path.basename(prev_used), "against " + (f"the {PREVIOUS[0]} static build" if prev_used == prev_static else f"the {PREVIOUS[0]} location instanced from this VF"))
    space_html = "<h2>The space inside and between</h2><ul>" + "".join(f"<li>{html.escape(l)}</li>" for l in lines) + "</ul>"
    for tag, name, mn, df, mx, *_ in AXES:
        for side, v in (("min", mn), ("max", mx)):
            loc = dict(default_loc); loc[tag] = v
            p = instance(vf_path, loc, os.path.join(tmp, f"{tag}_{side}.ttf")); img(eink(p, para), f"{name} ({tag}) {side} = {v}")
    doc = f'''<title>Albo Variable Proof</title>
<style>:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:16px 10px 60px;font:15px/1.45 -apple-system,Arial,sans-serif}}main{{max-width:900px;margin:0 auto}}h1{{font-size:22px;margin:0 0 6px}}p{{max-width:64ch;color:var(--soft);font-size:13px}}
h2{{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:var(--soft);margin:22px 0 6px;border-top:1px solid var(--rule);padding-top:10px}}ul{{max-width:80ch;font-size:13px;color:var(--soft);padding-left:18px}}li{{margin:0 0 6px}}
figure{{margin:0 0 12px}}figure img{{width:100%;max-width:375px;height:auto;image-rendering:pixelated;display:block;background:#fff}}figcaption{{font-size:11px;color:var(--soft);margin-top:2px}}</style>
<main><h1>Albo Variable, on the reader's pipeline</h1><p>13 pt on the 2x reader (54 px em), 8x supersampled, quantized to the panel's four levels: the new default on the 147 common words and on the paragraph, the previous default it replaces the same way, then each axis at its minimum and maximum (the wght and CNTR labels carry the ranges as landed). PNG at native pixels, 750 px blocks at 375 CSS px.</p>{''.join(figs)}{space_html}</main>'''
    out = os.path.join(out_dir, "albo-variable-proof.html"); open(out, "w").write(doc); return out

def verify(vf_path, out_dir, static_path, log=print):
    """(1) the default instance against the shipping static; (2) every axis
    extreme instanced, defect-counted against its master and rendered at
    150 px; (3) three two-axis corners the same way."""
    tmp = os.path.join(out_dir, "instances"); os.makedirs(tmp, exist_ok=True)
    default_loc = {tag: df for tag, name, mn, df, mx, *_ in AXES}
    res = {}
    d = instance(vf_path, dict(default_loc), os.path.join(tmp, "default.ttf"))
    dev, gn = compare_to_static(d, static_path); ink_d, ink_s = page_ink(d), page_ink(static_path)
    fa, fb = TTFont(static_path), TTFont(d)
    dadv = max(abs(fa['hmtx'][g][0] - fb['hmtx'][g][0]) for g in fa.getGlyphOrder()); dlsb = max(abs(fa['hmtx'][g][1] - fb['hmtx'][g][1]) for g in fa.getGlyphOrder())
    res["default"] = dict(max_dev=dev, glyph=gn, ink_ratio=ink_d / ink_s, max_dadv=dadv, max_dlsb=dlsb)
    log(f"(1) default instance vs {os.path.basename(static_path)}: max vertex deviation {dev:.2f} units (glyph {gn}); advances differ by at most {dadv}, side bearings {dlsb}; 147-word ink (PIL 54 px) {ink_d:.0f} vs {ink_s:.0f} = {100 * (ink_d / ink_s - 1):+.2f}%")
    text = "handgloves Rhythm 1234"; ims = [render_line(d, text, 150, "default")]
    res["extremes"] = {}
    mdir = os.path.join(out_dir, "masters")
    for tag, name, mn, df, mx, *_ in AXES:
        for side, v in (("min", mn), ("max", mx)):
            loc = dict(default_loc); loc[tag] = v
            p = instance(vf_path, loc, os.path.join(tmp, f"{tag}_{side}.ttf"))
            di = defects(TTFont(p)); dm = defects(TTFont(os.path.join(mdir, f"Albo-{tag}_{side}.ttf")))
            res["extremes"][f"{tag}_{side}"] = (sum(di.values()), sum(dm.values()), di)
            ims.append(render_line(p, text, 150, f"{name} {side} = {v}   defects: instance {sum(di.values())}, master {sum(dm.values())}"))
    stack(ims).save(os.path.join(out_dir, "vf-extremes.png"))
    log("(2) extremes: " + ", ".join(f"{k} {a}/{b}" for k, (a, b, _) in res["extremes"].items()))
    r = {t: (mn, mx) for t, n, mn, d_, mx, *_ in AXES}
    corners_ = [("wght max + wdth min", {"wght": r["wght"][1], "wdth": 80}), ("CNTR max + CUTS 200", {"CNTR": r["CNTR"][1], "CUTS": 200}), ("XHGT max + ASCN min", {"XHGT": 460, "ASCN": 700}),
                ("wght max + CNTR max", {"wght": r["wght"][1], "CNTR": r["CNTR"][1]}), ("wght min + CNTR min", {"wght": r["wght"][0], "CNTR": r["CNTR"][0]}),
                ("wght min + CNTR max", {"wght": r["wght"][0], "CNTR": r["CNTR"][1]})]
    ims = []; res["corners"] = {}
    for label, over in corners_:
        loc = dict(default_loc); loc.update(over)
        p = instance(vf_path, loc, os.path.join(tmp, "corner_" + label.replace(" + ", "_").replace(" ", "_") + ".ttf"))
        di = defects(TTFont(p)); res["corners"][label] = (sum(di.values()), di)
        ims.append(render_line(p, text, 150, f"{label}   defects {sum(di.values())} {dict(list(di.items())[:6])}"))
        ims.append(render_line(p, "ABGQ&@? nmhu bdpq g", 150, ""))
    stack(ims).save(os.path.join(out_dir, "vf-corners.png"))
    log("(3) corners: " + ", ".join(f"{k}: {a}" for k, (a, _) in res["corners"].items()))
    return res

if __name__ == "__main__":
    out_dir = sys.argv[1]
    vf_path, report, masters = build_vf(out_dir)
    print("clamps:", report["clamps"] or "none")
    static = os.path.join(os.path.dirname(os.path.abspath(out_dir.rstrip('/'))), "Albo-Medium.ttf")
    if os.path.exists(static): verify(vf_path, out_dir, static)
    open(os.path.join(out_dir, "albo-variable.html"), "w").write(slider_page(vf_path, None))
    print("pages:", proof_page(vf_path, out_dir), os.path.join(out_dir, "albo-variable.html"))
