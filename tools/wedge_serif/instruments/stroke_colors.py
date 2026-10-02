#!/usr/bin/env python3
"""stroke_colors.py -- Albo's words with every STROKE drawn in its own color.

Owner 2026-10-01: *"subagent to draw multicolor visualization of strokes for top twenty words in
corpus"*. The most frequent words in his own books (the epubs under ~/src/claude-tools/*/epub, read
as outlines/cmp/corpus.py reads them), set in Albo with the font's own advances and kerning
(HarfBuzz on a font built from the LIVE tree), and every letter's strokes colored two ways:

  roles    one color per ROLE, the same in every letter (stem, bowl, arch, diagonal, crossbar,
           serif, terminal, join, curve, dot); legend on the sheet
  strokes  every individual stroke its own hue; strokes that touch never share one, and a letter
           gets the same hues in every word it appears in

Where two strokes overlap the pixel is a DARKER blend of their colors (x0.62 per extra layer), so
every join -- a wedge's strip buried in its stem, an arch's root in the stem it branches from, an
exit leaving its stem -- is visible. Parts drawn as RAW POLYGONS in glyph code rather than by a
stroke primitive carry a diagonal hatch on both sheets.

HOW THE STROKES ARE CAPTURED. Nothing in the shipping code is changed, wrapped or monkeypatched
(glyph modules import primitives by name, so a patched module attribute would be bypassed anyway).
A sys.setprofile hook watches `outlines.build.draw(ch)` run:

  * every polygon `geom.poly` makes is an ATOM, kept with the call path that made it (the primitive,
    the glyph helpers above it, and the source line of each call);
  * every shapely operation the drawing applies afterwards is applied to the atoms that flow through
    it, tracked by object identity: union and unary_union pass them on; `difference` and
    `intersection` clip them by the other operand; `buffer` (the 1.2-unit ink spread, aldine's
    weight dial) and `affine_transform` (the italic lowercase scale, the shear, figure boxes) move
    them; the geometry utilities in geom.py (collapse_micro, close_corners, ...) pass them through.

So a stroke that was clipped, cut, spread and sheared lands exactly where the build put it, and
geometry made only to measure or to cut with (a construction head, an aperture, a trap) never
reaches the picture, because it never reaches the glyph.

STROKES. Atoms group into strokes: the innermost single-stroke primitive above an atom (stroke,
edge_stroke, wedge, dot, ring, ring_from, half_bowl, miter_chevron, ...); else a helper whose only
products are raw polygons (aldine's hm_sweep builds an arch from 36 quads -- one stroke); else the
polygon itself (the body `stem` draws, a head drawn as a polygon). Strokes whose final geometry is
identical (IoU > 0.999) are drawn once: the roman m's `_footed` draws each foot-carrying stem body
three times, once bare and once per foot.

ROLES come from the builder's own vocabulary, checked in this order, and the reason is recorded for
every stroke (`--table` prints it, the JSON keeps it):

  1. the primitive: wedge/diag_wedge/end_wedge/beak -> serif; dot -> dot; ring/ring_from/half_bowl
     -> bowl; the body `stem` draws -> stem (a stroke inside `stem`, the italic entry/exit -> join);
     a stroke inside `diagonal` -> diagonal, inside `bar` -> crossbar;
  2. names at the call sites, innermost first: the variable a part is assigned to and the name of
     its first argument (`hk = stroke(hook, ...)`, `bar = d_pen(...)`, `term = geom.poly(...)`);
  3. helper function names, outermost first (`hm_head`, `hm_exit`, `_e_tail`, `f_bar`, `_r_arm`);
     a name carrying two roles (`bowl_stem`) decides nothing; a tuple unpacked one level up
     (`st, tl, b = _t_clean(...)`) cannot say which target is which part and decides nothing;
  4. geometry of the centerline, measured before the italic shear: a curve whose net turn passes
     240 degrees is a bowl; a straight stroke, or a curved one with a straight run over half the
     x-height, is a stem (>= 84 degrees), crossbar (<= 30) or diagonal; anything else is a curve;
  5. a part no name spoke for that geometry could only call a curve takes its siblings' role when
     they agree (the a's hood is two strokes, `hood` and an unnamed underside).
  Two shape checks then correct names that mislead: a curve that starts inside a stem below half
  the x-height, dips to the baseline and rises away to the right is an EXIT (join) -- the italic d
  calls that stroke `tail`, the italic a calls the same construction `ex_`; and a part named as a
  tail that is mostly one long straight run (over 0.6 x-height) is classed by that run (the y's
  `_y_tail_ink` is its whole right diagonal).

THE CHECK, per glyph, in the JSON and the doc: (A) the union of the captured strokes against
`build.draw(ch)`, the live drawing (IoU); (B) the drawing against the BUILT glyph in the TTF once
aligned (the build's cut, integer rounding and contour clean-up are all that separate them);
(C) how much of the built glyph the strokes cover. Every stroke is clipped to the built outline, so
the colored silhouette IS the shipped letter; the few built pixels no stroke covers (the cut's
chords bulging past concave curves, and the fills `geom.close_corners` adds after the strokes are
unioned) take the nearest stroke's color, and the sheet's JSON counts them. (D) Since the
fonts are built from the live tree, every glyph used (outline, advance) and every word's shaping is
compared with the reader's copy in ~/src/crosspoint-reader/lib/EpdFont/local_fonts/Albo
(ALBO_SHIPPED_DIR overrides) and any difference is printed -- another agent shipped a round in the
middle of the session that wrote this, and only this comparison noticed.

    VENV=/path/to/venv/bin/python     # shapely, fontTools, uharfbuzz, Pillow, numpy, scipy
    cd tools/wedge_serif
    $VENV instruments/stroke_colors.py --out DIR                  # top 20 corpus words, Regular + Italic
    $VENV instruments/stroke_colors.py --out DIR --words "the of" # any words
    $VENV instruments/stroke_colors.py --out DIR --table          # also print every stroke's role and why

Each style runs in a child process carrying that style's environment, read from build_env.sh
(module state is fixed at import, so one process cannot hold two styles). Unless --fonts DIR is
given, the child first builds its TTF from the live tree into DIR/fonts (about 2 s). Output, per
style: stroke-colors-<Style>-roles.png and -strokes.png (the words), -key.png (every letter once,
its strokes numbered as the JSON numbers them) and stroke-colors-<Style>.json (per glyph: the check
numbers, and every stroke's role, the evidence for it and its builder path); plus DIR/words.json.
Images are composed at their native size (edges antialiased by 4x4 coverage
sampling, as a rasterizer does) and are never resized afterwards. Every row is a BASELINE (proof.py's
rule); rows are tall enough for the highest and deepest ink actually set.

Written 2026-10-01; docs/albo-stroke-colors-2026-10-01.md has the word list, the role table for the
twenty words' fifteen letters and the check numbers.
"""
import sys, os, re, math, json, glob, html, zipfile, argparse, subprocess, linecache, collections

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
STYLE_KEYS = {'Regular': 'ALBO_ROM_ENV', 'Italic': 'ALBO_ITA_ENV', 'Bold': 'ALBO_BLD_ENV', 'BoldItalic': 'ALBO_BIT_ENV'}
SHIPPED_DIR = "~/src/crosspoint-reader/lib/EpdFont/local_fonts/Albo"     # the reader's copy; ALBO_SHIPPED_DIR overrides
UI_FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
UI_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def style_env(style):
    """The style's shipping dials, read from build_env.sh -- the one place they are written."""
    txt = open(os.path.join(WS, 'build_env.sh')).read()
    m = re.search(r'^%s=\(([^)]*)\)' % STYLE_KEYS[style], txt, re.M)
    return dict(kv.split('=', 1) for kv in m.group(1).split())


# ===================================================================== corpus
WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
DROP_RE = re.compile(r"<(head|style|script)\b.*?</\1\s*>", re.S | re.I)


def corpus_counts(root=None):
    """Words in every epub under root/*/epub/*.epub: the content documents only (.xhtml .html .htm),
    <head>, <style> and <script> dropped, tags stripped, entities decoded. A word is a run of
    letters that may carry an inner apostrophe (so "it's" is one word and possessive 's never
    counts as the word "s"), case-folded. Returns (counts, surface forms per word, books)."""
    root = root or os.environ.get('ALBO_CORPUS', os.path.expanduser('~/src/claude-tools'))
    books = sorted(glob.glob(os.path.join(root, '*', 'epub', '*.epub')))
    cnt = collections.Counter(); forms = collections.defaultdict(collections.Counter)
    for b in books:
        try:
            z = zipfile.ZipFile(b)
        except Exception:
            continue
        for n in z.namelist():
            if not n.lower().endswith(('.xhtml', '.html', '.htm')):
                continue
            t = z.read(n).decode('utf-8', 'ignore')
            t = html.unescape(re.sub(r'<[^>]+>', ' ', DROP_RE.sub(' ', t)))
            for w in WORD_RE.findall(t):
                w = w.replace('’', "'")
                f = w.casefold(); cnt[f] += 1; forms[f][w] += 1
    return cnt, forms, books


def top_words(n):
    cnt, forms, books = corpus_counts()
    out = []
    for i, (w, c) in enumerate(cnt.most_common(n), 1):
        out.append(dict(rank=i, word=w, count=c, form=forms[w].most_common(1)[0][0],
                        forms=forms[w].most_common(4)))
    return out, dict(books=len(books), words=sum(cnt.values()), distinct=len(cnt))


# ===================================================================== capture
SHAPELY_OPS = {
    ('affinity.py', 'affine_transform'): 'affine',
    ('base.py', 'buffer'): 'buffer', ('constructive.py', 'buffer'): 'buffer',
    ('base.py', 'union'): 'cat2', ('set_operations.py', 'union'): 'cat2',
    ('set_operations.py', 'coverage_union'): 'cat2',
    ('base.py', 'symmetric_difference'): 'symdiff', ('set_operations.py', 'symmetric_difference'): 'symdiff',
    ('ops.py', 'unary_union'): 'catall', ('set_operations.py', 'union_all'): 'catall',
    ('set_operations.py', 'coverage_union_all'): 'catall',
    ('base.py', 'difference'): 'diff', ('set_operations.py', 'difference'): 'diff',
    ('base.py', 'intersection'): 'inter', ('set_operations.py', 'intersection'): 'inter',
    ('base.py', 'convex_hull'): 'pass', ('constructive.py', 'convex_hull'): 'pass',
    ('base.py', 'simplify'): 'pass', ('constructive.py', 'simplify'): 'pass',
    ('constructive.py', 'make_valid'): 'pass', ('validation.py', 'make_valid'): 'pass',
    ('base.py', 'normalize'): 'pass', ('constructive.py', 'normalize'): 'pass',
}
# primitives that draw exactly ONE stroke, however many pieces they make it from
SINGLE = {'stroke', 'edge_stroke', 'miter_chevron', 'wedge', 'diag_wedge', 'end_wedge', 'beak', 'dot',
          '_punch_dot', 'ring', 'ring_from', 'half_bowl', 'trap'}
COMBINE = {'union', 'ink'}       # geom.union / geom.ink: the shapely ops inside them carry the atoms


class Call:
    __slots__ = ('name', 'file', 'line', 'site', 'parent', 'children', 'args', 'idx', 'made', 'ret')

    def __init__(self, name, file, line, site, parent, args, idx):
        self.name, self.file, self.line, self.site = name, file, line, site
        self.parent, self.args, self.idx = parent, args, idx
        self.children = []; self.made = []; self.ret = None

    def path(self):
        out = []; c = self
        while c is not None:
            out.append(c); c = c.parent
        return out[::-1]


class Tracer:
    """The sys.setprofile hook. See the module docstring."""

    def __init__(self):
        import outlines, shapely
        from shapely.geometry.base import BaseGeometry
        self.BG = BaseGeometry
        self.OUT = os.path.dirname(outlines.__file__) + os.sep
        self.SHP = os.path.dirname(shapely.__file__) + os.sep
        self.GEOMPY = os.path.join(self.OUT, 'geom.py')
        self.stack = []; self.calls = []; self.roots = []; self.frames = {}
        self.prov = {}; self.keep = []; self.atoms = []; self.cutters = set(); self.opg = {}
        self.opaque = None; self.leaf = None; self.shp = None

    def isg(self, x):
        return isinstance(x, self.BG)

    def geoms_in(self, v, depth=0):
        if self.isg(v):
            return [v]
        if depth < 2 and isinstance(v, (list, tuple)):
            return [g for x in v for g in self.geoms_in(x, depth + 1)]
        return []

    def pv(self, g):
        return self.prov.get(id(g), [])

    def setp(self, g, lst):
        seen = set(); out = []
        for a in lst:
            if a not in seen:
                seen.add(a); out.append(a)
        self.prov[id(g)] = out; self.keep.append(g)

    def stash(self, obj):
        self.opg[id(obj)] = obj; self.keep.append(obj)
        return id(obj)

    def new_atom(self, g, call):
        aid = len(self.atoms)
        self.atoms.append(dict(aid=aid, geom=g, call=call))
        call.made.append(aid)
        self.setp(g, [(aid, ())])

    def __call__(self, frame, event, arg):
        if event == 'call':
            if self.leaf is not None or self.opaque is not None or self.shp is not None:
                return
            co = frame.f_code; fn = co.co_filename
            if fn.startswith(self.OUT):
                cl = frame.f_back
                site = (cl.f_code.co_filename, cl.f_lineno, cl.f_code.co_name) if cl else None
                parent = self.stack[-1] if self.stack else None
                c = Call(co.co_name, fn, co.co_firstlineno, site, parent, dict(frame.f_locals), len(self.calls))
                self.calls.append(c)
                (parent.children if parent else self.roots).append(c)
                self.stack.append(c); self.frames[id(frame)] = c
                if fn == self.GEOMPY and co.co_name == 'poly':
                    self.leaf = frame
                elif (fn == self.GEOMPY and co.co_name not in COMBINE) or co.co_name == 'convex_holes':
                    self.opaque = frame
            elif fn.startswith(self.SHP):
                k = (os.path.basename(fn), co.co_name)
                if k in SHAPELY_OPS:
                    self.shp = (frame, SHAPELY_OPS[k], co, dict(frame.f_locals))
        elif event == 'return':
            if self.shp is not None:
                if frame is self.shp[0]:
                    try:
                        self.shop(arg)
                    finally:
                        self.shp = None
                return
            c = self.frames.get(id(frame))
            if c is None or not self.stack or self.stack[-1] is not c:
                return
            del self.frames[id(frame)]
            self.stack.pop(); c.ret = arg
            if self.leaf is frame:
                self.leaf = None
                if self.isg(arg) and not arg.is_empty:
                    self.new_atom(arg, c)
                return
            if self.opaque is frame:          # a geometry utility: what goes in comes out
                self.opaque = None
                srcs = [x for v in c.args.values() for x in self.geoms_in(v)]
                for g in self.geoms_in(arg):
                    if id(g) not in self.prov:
                        self.setp(g, [a for s in srcs for a in self.pv(s)])
                return
            for g in self.geoms_in(arg):      # a geometry made outside the tracked ops
                if id(g) in self.prov:
                    continue
                srcs = [x for v in c.args.values() for x in self.geoms_in(v) if id(x) in self.prov]
                if srcs and c.name not in SINGLE:
                    self.setp(g, [a for s in srcs for a in self.pv(s)])
                elif not g.is_empty:
                    self.new_atom(g, c)

    def shop(self, ret):
        frame, kind, co, loc = self.shp
        if not self.isg(ret):
            return
        p = [loc.get(n) for n in co.co_varnames[:co.co_argcount]]
        if kind == 'affine':
            m = tuple(float(v) for v in p[1])
            self.setp(ret, [(a, ops + (('A', m),)) for a, ops in self.pv(p[0])])
        elif kind == 'buffer':
            d = float(p[1])
            kw = {k: loc[k] for k in ('quad_segs', 'cap_style', 'join_style', 'mitre_limit', 'single_sided') if k in loc}
            kw.update(loc.get('kwargs') or {})
            op = ('B', d, self.stash(kw))
            self.setp(ret, [(a, ops + ((op,) if d else ())) for a, ops in self.pv(p[0])])
        elif kind == 'cat2':
            self.setp(ret, self.pv(p[0]) + self.pv(p[1]))
        elif kind == 'symdiff':
            oa, ob = ('D', self.stash(p[1])), ('D', self.stash(p[0]))
            self.setp(ret, [(a, ops + (oa,)) for a, ops in self.pv(p[0])] + [(a, ops + (ob,)) for a, ops in self.pv(p[1])])
        elif kind == 'catall':
            src = loc.get('geoms') if 'geoms' in loc else p[0]
            if self.isg(src):
                lst = self.pv(src) if id(src) in self.prov else [a for g in getattr(src, 'geoms', []) for a in self.pv(g)]
            else:
                lst = [a for g in list(src) for a in self.pv(g)]
            self.setp(ret, lst)
        elif kind == 'diff':
            if self.isg(p[1]):
                o = ('D', self.stash(p[1]))
                self.setp(ret, [(a, ops + (o,)) for a, ops in self.pv(p[0])])
            else:
                self.setp(ret, self.pv(p[0]))
            for a, _ in self.pv(p[1]):
                self.cutters.add(a)
        elif kind == 'inter':
            if self.pv(p[0]) and self.isg(p[1]):
                o = ('I', self.stash(p[1])); self.setp(ret, [(a, ops + (o,)) for a, ops in self.pv(p[0])])
            elif self.pv(p[1]) and self.isg(p[0]):
                o = ('I', self.stash(p[0])); self.setp(ret, [(a, ops + (o,)) for a, ops in self.pv(p[1])])
        elif kind == 'pass':
            self.setp(ret, self.pv(p[0]))


def apply_ops(g, ops, opg):
    import shapely.affinity as aff
    for op in ops:
        k = op[0]
        if k == 'A':
            g = aff.affine_transform(g, op[1])
        elif k == 'B':
            g = g.buffer(op[1], **opg[op[2]])
        elif k == 'D':
            g = g.difference(opg[op[1]])
        elif k == 'I':
            g = g.intersection(opg[op[1]])
        if g.is_empty:
            break
    return g


def capture(ch, W=None):
    from outlines import build
    tr = Tracer()
    sys.setprofile(tr)
    try:
        g = build.draw(ch, W)
    finally:
        sys.setprofile(None)
    return g, tr


# ===================================================================== strokes and roles
ROLES = ['stem', 'diagonal', 'bowl', 'arch', 'curve', 'crossbar', 'serif', 'terminal', 'join', 'dot', 'raw']
ROLE_LABEL = {'stem': 'stem', 'diagonal': 'diagonal', 'bowl': 'bowl / loop', 'arch': 'arch / shoulder / arm',
              'curve': 'curve / spine', 'crossbar': 'crossbar', 'serif': 'serif (wedge, Aldine head)',
              'terminal': 'terminal (hook, tail, ear)', 'join': 'join (exit stroke)', 'dot': 'dot',
              'raw': 'unnamed raw polygon'}
ROLE_COLOR = {'stem': (52, 104, 214), 'diagonal': (66, 166, 232), 'bowl': (226, 80, 56), 'arch': (242, 156, 52),
              'curve': (214, 76, 156), 'crossbar': (46, 160, 84), 'serif': (134, 84, 196),
              'terminal': (200, 166, 20), 'join': (20, 166, 160), 'dot': (90, 90, 90), 'raw': (140, 90, 44)}
KEYWORDS = {
    'serif': {'wedge', 'serif', 'head', 'beak', 'lip', 'bracket', 'spur'},
    'stem': {'stem', 'midstem', 'shaft'},
    'bowl': {'ring', 'bowl', 'loop', 'eye', 'oval'},
    'arch': {'arch', 'shoulder', 'hood', 'arm'},
    'diagonal': {'diagonal', 'diag', 'leg'},
    'crossbar': {'bar', 'crossbar', 'cross'},
    'terminal': {'tail', 'hook', 'term', 'terminal', 'finial', 'ear', 'flag', 'curl'},
    'join': {'exit', 'entry', 'flick', 'outstroke', 'instroke'},
    'dot': {'dot', 'tittle'},
    'curve': {'spine'},
}
ALIAS = {'tl': 'tail', 'hk': 'hook', 'ex': 'exit'}
WORD2ROLE = {w: r for r, ws in KEYWORDS.items() for w in ws}
STEM_DEG, BAR_DEG = 84.0, 30.0


def name_roles(name):
    """The roles a name speaks for: its tokens split on '_' and case, aliases expanded."""
    toks = [t.lower() for t in re.split(r'[^A-Za-z0-9]+|_', re.sub(r'([a-z])([A-Z])', r'\1_\2', name or '')) if t]
    toks = [ALIAS.get(t, t) for t in toks if len(t) > 1 and not t.isdigit()]
    return {WORD2ROLE[t] for t in toks if t in WORD2ROLE}, toks


def glyph_index(path):
    w = [i for i, x in enumerate(path) if x.name == 'wrapped']
    return (w[-1] + 1) if w else 1


def instance_of(tr, atom):
    c = atom['call']; path = c.path(); gi = glyph_index(path)
    for x in reversed(path[gi:-1] if c.name == 'poly' else path[gi:]):
        if x.name in SINGLE:
            return x
    if c.name == 'poly':
        P = c.parent
        if P is not None and P in path and path.index(P) > gi:
            kids = [k for k in P.children
                    if k.made or k.name in SINGLE or (k.name not in COMBINE and k.name != 'poly'
                                                       and k.ret is not None and tr.geoms_in(k.ret))]
            if kids and all(k.name == 'poly' for k in kids):
                return P
    return c


def site_names(rec):
    """Names at the line that called `rec`: the assignments its result goes to (each a list of
    targets, so a tuple unpacking stays visible as one), then the name of its first argument."""
    if not rec.site:
        return [], []
    line = linecache.getline(rec.site[0], rec.site[1])
    nm = re.escape(rec.name)
    tg = re.findall(r'([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s*=\s*(?:[A-Za-z_]\w*\.)*' + nm + r'\s*\(', line)
    fa = re.findall(r'(?:^|[^\w.])(?:[A-Za-z_]\w*\.)*' + nm + r'\s*\(\s*([A-Za-z_]\w*)\s*[,)]', line)
    return [[t.strip() for t in g.split(',')] for g in tg], fa


def centerline(rec):
    for k in ('center', 'outer', 'pts'):
        v = rec.args.get(k)
        if (isinstance(v, (list, tuple)) and len(v) >= 2
                and all(isinstance(p, (list, tuple)) and len(p) == 2 for p in v[:4])):
            try:
                return [(float(x), float(y)) for x, y in v]
            except (TypeError, ValueError):
                return None
    return None


def resample(pts, step=4.0):
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b)
        n = max(1, int(d // step))
        for k in range(1, n + 1):
            t = k / n; out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def shape_of(pts):
    """Turning, straightness and the longest straight run of a centerline (font units, degrees)."""
    pts = resample(pts)
    if len(pts) < 3:
        return None
    L = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    seg = [(math.atan2(b[1] - a[1], b[0] - a[0]), math.dist(a, b)) for a, b in zip(pts, pts[1:]) if math.dist(a, b) > 1e-6]
    th = [seg[0][0]]
    for a, _ in seg[1:]:
        d = (a - th[-1] + math.pi) % (2 * math.pi) - math.pi
        th.append(th[-1] + d)
    net = math.degrees(th[-1] - th[0])
    tot = sum(abs(math.degrees(b - a)) for a, b in zip(th, th[1:]))
    # longest run whose direction stays inside a 12-degree window (two pointers)
    best = (0.0, 0, 0); i = 0; run = 0.0
    lo = collections.deque(); hi = collections.deque()
    for j in range(len(th)):
        while lo and th[lo[-1]] >= th[j]: lo.pop()
        lo.append(j)
        while hi and th[hi[-1]] <= th[j]: hi.pop()
        hi.append(j)
        run += seg[j][1]
        while math.degrees(th[hi[0]] - th[lo[0]]) > 12.0:
            run -= seg[i][1]; i += 1
            if lo[0] < i: lo.popleft()
            if hi[0] < i: hi.popleft()
        if run > best[0]:
            best = (run, i, j)
    run, i, j = best
    ang = math.degrees(sum(th[k] * seg[k][1] for k in range(i, j + 1)) / max(1e-9, sum(seg[k][1] for k in range(i, j + 1))))
    chord = math.dist(pts[0], pts[-1])
    return dict(L=L, straight=chord / L if L else 1.0, net=net, turn=tot, run=run, run_ang=ang,
                chord_ang=math.degrees(math.atan2(pts[-1][1] - pts[0][1], pts[-1][0] - pts[0][0])))


def by_angle(deg):
    a = abs(((deg + 90.0) % 180.0) - 90.0)        # 0 = horizontal, 90 = vertical
    return 'stem' if a >= STEM_DEG else ('crossbar' if a <= BAR_DEG else 'diagonal'), a


class Stroke:
    def __init__(self, sid, rec, aids, geom, raw):
        self.sid, self.rec, self.aids, self.geom, self.raw = sid, rec, aids, geom, raw
        self.role = None; self.why = ''; self.src = ''; self.pts = None; self.shape = None
        self.merged = []


def classify(strokes, xh, tr):
    """Rules 1-5 and the two shape checks of the module docstring, in that order."""
    gi_of = {}
    for s in strokes:
        path = s.rec.path(); gi = glyph_index(path); gi_of[s.sid] = (path, gi)
    # 1. the primitive
    for s in strokes:
        r = s.rec; par = r.parent.name if r.parent else ''
        if r.name in ('wedge', 'diag_wedge', 'end_wedge', 'beak'):
            s.role, s.why = 'serif', f'primitive {r.name}'
        elif r.name in ('dot', '_punch_dot'):
            s.role, s.why = 'dot', f'primitive {r.name}'
        elif r.name in ('ring', 'ring_from', 'half_bowl'):
            s.role, s.why = 'bowl', f'primitive {r.name}'
        elif r.name == 'stem' or (r.name == 'poly' and par == 'stem'):
            s.role, s.why = 'stem', 'primitive stem (its body)'
        elif r.name == 'stroke' and par == 'stem':
            s.role, s.why = 'join', 'primitive stem (its italic entry/exit stroke)'
        elif r.name == 'stroke' and par == 'diagonal':
            s.role, s.why = 'diagonal', 'primitive diagonal'
        elif r.name == 'stroke' and par == 'bar':
            s.role, s.why = 'crossbar', 'primitive bar'
        elif r.name == 'miter_chevron':
            s.role, s.why = 'diagonal', 'primitive miter_chevron'
        if s.role:
            s.src = 'primitive'
    # 2. call-site names, innermost first; 3. helper names, outermost first
    for s in strokes:
        if s.role:
            continue
        path, gi = gi_of[s.sid]
        chain = path[gi + 1:]
        for depth, rec in enumerate(reversed(chain)):
            groups, fa = site_names(rec)
            if depth == 0:     # the part's own call: the first target holds it (`solid, L, R = stroke(...)`)
                tg = [g[0] for g in groups]
            else:              # one level up a tuple unpacking cannot say which target is this part
                tg = [g[0] for g in groups if len(g) == 1]
            for kind, names in (('assigned to', tg), ('first argument', fa)):
                for nm in names:
                    rs, _ = name_roles(nm)
                    if len(rs) == 1:
                        s.role = rs.pop(); s.why = f"{kind} `{nm}` at {os.path.basename(rec.site[0])}:{rec.site[1]}"; s.src = 'call site'
                        break
                if s.role: break
            if s.role: break
        if s.role:
            continue
        for rec in chain:
            if rec.name in ('poly', 'stroke'):
                continue
            rs, _ = name_roles(rec.name)
            if len(rs) == 1:
                s.role = rs.pop(); s.why = f"helper `{rec.name}`"; s.src = 'helper'
                break
    named = {s.sid: s.role for s in strokes if s.role}      # what the builder's names said
    # 4. geometry
    for s in strokes:
        s.pts = centerline(s.rec)
        s.shape = shape_of(s.pts) if s.pts else None
        if s.role:
            continue
        f = s.shape
        if f is None:
            s.role, s.why, s.src = 'raw', 'no primitive, no name, no centerline', 'none'
            continue
        if abs(f['net']) >= 240.0:
            s.role, s.why = 'bowl', f"geometry: curve turning {abs(f['net']):.0f} degrees net"
        elif f['straight'] >= 0.97:
            s.role, a = by_angle(f['chord_ang']); s.why = f"geometry: straight at {a:.0f} degrees"
        elif f['run'] >= 0.5 * xh:
            s.role, a = by_angle(f['run_ang']); s.why = f"geometry: {f['run'] / xh:.2f} xh straight run at {a:.0f} degrees"
        else:
            s.role, s.why = 'curve', f"geometry: curved (net turn {f['net']:.0f}, longest straight run {f['run'] / xh:.2f} xh)"
        s.src = 'geometry'
    # 5. siblings: an unnamed curve (or unnamed polygon) made in the same helper call as named parts
    #    that agree takes their role -- the a's hood is two strokes, `hood` and an unnamed underside
    for s in strokes:
        if s.sid in named or s.role not in ('curve', 'raw'):
            continue
        par = s.rec.parent
        path, gi = gi_of[s.sid]
        if par is None or par not in path or path.index(par) <= gi:
            continue
        sib = {named[t.sid] for t in strokes if t is not s and t.sid in named and t.rec.parent is par}
        if len(sib) == 1:
            r = sib.pop()
            s.why = f"{s.why}; no name of its own, and its siblings in `{par.name}` are {r}"
            s.role = r; s.src = 'sibling'
    # shape check: a long straight run named as a tail is classed by the run
    for s in strokes:
        f = s.shape
        if s.role == 'terminal' and s.src in ('call site', 'helper') and f and f['run'] >= 0.6 * xh:
            r, a = by_angle(f['run_ang'])
            s.why = f"{s.why}, but it is mostly one {f['run'] / xh:.2f} xh straight run at {a:.0f} degrees"
            s.role = r; s.src = 'shape check'
    # shape check: an exit leaves a stem at its foot and rises away to the right
    stems = [t for t in strokes if t.role == 'stem']
    from shapely.geometry import Point
    from shapely.ops import unary_union
    for s in strokes:
        if s.role not in ('terminal', 'curve') or not s.pts or not stems:
            continue
        p0 = s.pts[0]; ymin = min(y for _, y in s.pts); pe = s.pts[-1]
        inside = any(unary_union([tr.atoms[a]['geom'] for a in t.aids]).distance(Point(p0)) <= 3.0 for t in stems)
        if (inside and p0[1] < 0.55 * xh and ymin < 0.18 * xh and pe[0] - p0[0] > 0.12 * xh
                and pe[1] - ymin > 0.02 * xh):
            s.why = f"{s.why}; but it starts inside a stem at {p0[1] / xh:.2f} xh, dips to {ymin / xh:.2f} xh and rises away right: an exit"
            s.role = 'join'; s.src = 'shape check'


def glyph_strokes(ch, W, xh):
    """Capture one glyph: (drawn glyph, [Stroke], tracer, notes)."""
    from shapely.ops import unary_union
    g, tr = capture(ch, W)
    fin = collections.OrderedDict()
    for aid, ops in tr.pv(g):
        pg = apply_ops(tr.atoms[aid]['geom'], ops, tr.opg)
        if not pg.is_empty and pg.area > 0.05:
            fin.setdefault(aid, []).append(pg)
    groups = collections.OrderedDict()
    for aid in fin:
        inst = instance_of(tr, tr.atoms[aid])
        groups.setdefault(inst.idx, (inst, []))[1].append(aid)
    strokes = []
    prim_file = os.path.join(tr.OUT, 'primitives.py')
    for k, (inst, aids) in groups.items():
        geom = unary_union([p for a in aids for p in fin[a]])
        if geom.is_empty:
            continue
        raw = (len(aids) == 1 and tr.atoms[aids[0]]['call'].name == 'poly'
               and (tr.atoms[aids[0]]['call'].parent is None
                    or tr.atoms[aids[0]]['call'].parent.file != prim_file))
        strokes.append(Stroke(len(strokes), inst, aids, geom, raw))
    classify(strokes, xh, tr)
    # identical duplicates are one stroke
    keep = []
    for s in strokes:
        dup = None
        for t in keep:
            if t.role == s.role:
                inter = t.geom.intersection(s.geom).area
                uni = t.geom.union(s.geom).area
                if uni > 0 and inter / uni > 0.999:
                    dup = t; break
        if dup is not None:
            dup.merged.append(s.sid)
        else:
            keep.append(s)
    for i, s in enumerate(keep):
        s.sid = i
    return g, keep, tr


# ===================================================================== the built font
def ttf_outline(gs, gname):
    from fontTools.pens.basePen import BasePen
    from shapely.geometry import Polygon

    class P(BasePen):
        def __init__(self, gs):
            super().__init__(gs); self.cs = []; self.cur = []

        def _moveTo(self, p): self.cur = [p]
        def _lineTo(self, p): self.cur.append(p)

        def _qCurveToOne(self, p1, p2):
            p0 = self.cur[-1]
            for k in range(1, 9):
                t = k / 8
                self.cur.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                                 (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))

        def _curveToOne(self, p1, p2, p3):
            p0 = self.cur[-1]
            for k in range(1, 13):
                t = k / 12; u = 1 - t
                self.cur.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                                 u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))

        def _closePath(self):
            if len(self.cur) >= 3: self.cs.append(self.cur)
            self.cur = []

        _endPath = _closePath

    pen_ = P(gs); gs[gname].draw(pen_)
    g = Polygon()
    for c in pen_.cs:
        g = g.symmetric_difference(Polygon(c).buffer(0))
    return g


def align_dx(g_draw, g_ttf):
    """The build's horizontal fit offset, recovered by minimizing the symmetric difference between
    the drawn glyph and the built one (the cut and the rounding are all that separate them)."""
    from shapely import affinity
    def cost(dx):
        return affinity.translate(g_draw, dx, 0).symmetric_difference(g_ttf).area
    d = g_ttf.bounds[0] - g_draw.bounds[0]
    for step, span in ((0.5, 8), (0.05, 10)):
        d = min((d + k * step for k in range(-span, span + 1)), key=cost)
    return d, cost(d)


def iou(a, b):
    u = a.union(b).area
    return a.intersection(b).area / u if u else 1.0


# ===================================================================== colors for the strokes sheet
# twelve hues of middling lightness, so a two-layer overlap (x0.62) still reads as darker, not black
PALETTE = [(215, 40, 60), (245, 135, 40), (215, 175, 0), (135, 190, 40), (40, 150, 75), (25, 165, 155),
           (65, 185, 235), (55, 95, 215), (125, 75, 205), (215, 70, 185), (160, 100, 45), (245, 140, 170)]


def _lab(c):
    def lin(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(float(v)) for v in c)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return (116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z)))


LAB = [_lab(c) for c in PALETTE]


def pick_hue(bad, used, near, order):
    """A palette index not in `bad`, unused if possible, as far (CIE76) from the `near` hues as possible;
    ties go to `order`, a per-letter rotation."""
    pool = [c for c in order if c not in bad and c not in used] or [c for c in order if c not in bad] or list(order)
    if not near:
        return pool[0]
    return max(pool, key=lambda c: (min(math.dist(LAB[c], LAB[k]) for k in near), -order.index(c)))


def color_glyph(strokes, seed):
    """Every stroke its own hue while the palette lasts, never a neighbor's (touching within 8 units),
    each chosen as far from its neighbors' hues as the palette allows. Larger strokes choose first."""
    n = len(PALETTE); order = [(seed + 5 * k) % n for k in range(n)]
    nb = {s.sid: {t.sid for t in strokes if t is not s and s.geom.distance(t.geom) <= 8.0} for s in strokes}
    col = {}
    for s in sorted(strokes, key=lambda s: -s.geom.area):
        near = [col[t] for t in nb[s.sid] if t in col]
        col[s.sid] = pick_hue(set(near), set(col.values()), near, order)
    return col


# ===================================================================== render
def raster_mask(geom, ox, oy, sc, W, H):
    """A 0/1 mask of `geom` (font units, y up) at scale sc, origin (ox, oy) = canvas pixel of (0, 0)."""
    import numpy as np
    from PIL import Image, ImageDraw
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    polys = [geom] if geom.geom_type == 'Polygon' else [p for p in getattr(geom, 'geoms', []) if p.geom_type == 'Polygon']
    for P in polys:
        if P.is_empty:
            continue
        d.polygon([(ox + x * sc, oy - y * sc) for x, y in P.exterior.coords], fill=1)
        for h in P.interiors:
            d.polygon([(ox + x * sc, oy - y * sc) for x, y in h.coords], fill=0)
    return np.asarray(im, dtype=np.uint8)


def compose_word(items, sc, SS, asc, desc, pad, hatch_px):
    """items = (strokes, built outline, x0, x1): strokes are [(geometry in word units, RGB, raw?)], every
    one already clipped to the built outline. Overlaps are averaged and darkened x0.62 per extra layer;
    built pixels no stroke covers take the nearest stroke's color. Returns (RGB uint8 image, stats)."""
    import numpy as np
    from scipy import ndimage as ndi
    strokes, ttf, x0, x1 = items
    S = sc * SS
    W = int(math.ceil((x1 - x0) * S)) + 2 * pad * SS
    H = int(math.ceil((asc + desc) * S))
    ox = pad * SS - x0 * S; oy = asc * S
    glyph = raster_mask(ttf, ox, oy, S, W, H).astype(bool)
    cnt = np.zeros((H, W), np.float32); acc = np.zeros((H, W, 3), np.float32)
    rawm = np.zeros((H, W), bool)
    for geom, color, raw in strokes:
        m = raster_mask(geom, ox, oy, S, W, H).astype(bool) & glyph
        cnt += m; acc[m] += color
        if raw: rawm |= m
    covered = cnt > 0
    fill = np.zeros((H, W, 3), np.float32)
    fill[covered] = acc[covered] / cnt[covered][:, None]
    dark = np.where(cnt > 1, 0.62 ** (cnt - 1), 1.0).astype(np.float32)
    fill *= dark[:, :, None]
    gap = glyph & ~covered
    nfill = int(gap.sum())
    if nfill and covered.any():
        _, (iy, ix) = ndi.distance_transform_edt(~covered, return_indices=True)
        fill[gap] = fill[iy[gap], ix[gap]]
    if hatch_px and rawm.any():
        yy, xx = np.mgrid[0:H, 0:W]
        stripe = ((xx + yy) // (hatch_px * SS)) % 2 == 0
        fill[rawm & stripe] *= 0.72
    img = np.full((H, W, 3), 255.0, np.float32)
    img[glyph] = fill[glyph]
    # 4x4 coverage sampling: the mean of each SSxSS block is the pixel
    h, w = H // SS, W // SS
    img = img[:h * SS, :w * SS].reshape(h, SS, w, SS, 3).mean(axis=(1, 3))
    return np.clip(img + 0.5, 0, 255).astype(np.uint8), dict(glyph_px=int(glyph.sum()), nearest_filled_px=nfill)


def render_sheet(words, placed, coloring, style, meta, out_path, px_xh, xh):
    """words: [word dict]; placed[i] = [(gname, x, y, Glyph)] for word i."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from shapely import affinity
    sc = px_xh / xh; SS = 4; pad = 10
    try:
        k = (px_xh / 200.0) if meta.get('poster') else 1.0     # --poster: everything scales with the letters
        fnt = ImageFont.truetype(UI_FONT, int(30 * k)); fsm = ImageFont.truetype(UI_FONT, int(24 * k))
        fbd = ImageFont.truetype(UI_BOLD, int(36 * k * (1.6 if meta.get('poster') else 1))); flab = ImageFont.truetype(UI_BOLD, int(30 * k))
    except OSError:
        fnt = fsm = fbd = flab = ImageFont.load_default()
    # vertical extent of the ink actually set
    tops = [0.0]; bots = [0.0]
    for wl in placed:
        for gname, x, y, G in wl:
            b = G.ttf.bounds
            if b[3] > b[1]:
                tops.append(b[3] + y); bots.append(b[1] + y)
    asc = max(tops) + 20; desc = -min(bots) + 20
    blocks = []; stats = dict(glyph_px=0, nearest_filled_px=0)
    for w, wl in zip(words, placed):
        strokes = []; ttf_parts = []; xs = []
        for gname, x, y, G in wl:
            if G.ttf.is_empty:
                continue
            ttf_parts.append(affinity.translate(G.ttf, x, y))
            xs += [G.ttf.bounds[0] + x, G.ttf.bounds[2] + x]
            for s in G.strokes:
                gg = affinity.translate(s.geom_built, x, y)
                c = ROLE_COLOR[s.role] if coloring == 'roles' else PALETTE[w['colors'][G.key][s.sid]]
                strokes.append((gg, c, s.raw))
            if not G.strokes:      # not captured: the built outline in gray
                strokes.append((affinity.translate(G.ttf, x, y), (170, 170, 170), False))
        from shapely.ops import unary_union
        ttf = unary_union(ttf_parts)
        x0, x1 = (min(xs), max(xs)) if xs else (0, 100)
        img, st = compose_word((strokes, ttf, x0, x1), sc, SS, asc, desc, pad, 7)
        for k in stats: stats[k] += st[k]
        blocks.append((w, img))
    # flow layout, rows on baselines
    poster = meta.get('poster'); k = (px_xh / 200.0) if poster else 1.0
    maxw = int(18 * px_xh) if poster else 2400      # a poster's row: 18 x-heights, about a 3:4 sheet for a 100-letter pangram
    gapx = int((0.33 * px_xh / 0.45) if poster else 70); margin = int(40 * k * (2 if poster else 1))
    label_h = 0 if poster else 44
    rows = []; cur = []; cw = 0
    for w, img in blocks:
        bw = max(img.shape[1], 10)
        if cur and cw + gapx + bw > maxw - 2 * margin:
            rows.append(cur); cur = []; cw = 0
        cur.append((w, img)); cw += (gapx if cw else 0) + bw
    if cur: rows.append(cur)
    word_h = blocks[0][1].shape[0] if blocks else 100
    # header: title, legend, notes -- measured and wrapped before anything is placed
    title = (f"Albo {style}: the {len(words)} most frequent words in {meta['books']} books "
             f"({meta['words']:,} words), every stroke colored by {'ROLE' if coloring == 'roles' else 'STROKE'}")
    if poster:
        title = f"{poster}  ·  Albo {style}, every stroke colored by {'role' if coloring == 'roles' else 'stroke'}"
    if coloring == 'roles':
        used = {s.role for wl in placed for _, _, _, G in wl for s in G.strokes}
        legend = [r for r in ROLES if r in used]
        notes = ("Where two strokes overlap the color is a darker blend of both: those are the joins.  "
                 "Hatched = drawn as a raw polygon in glyph code, not by a stroke primitive.  "
                 "Roles come from the builder's own names (primitive, call site, helper), else from the "
                 "stroke's centerline; docs/albo-stroke-colors-2026-10-01.md lists the evidence for every part.")
    else:
        legend = []
        notes = ("Every stroke its own hue; strokes that touch never share one; a letter keeps its hues in every "
                 "word.  Where two strokes overlap the color is a darker blend of both: those are the joins.  "
                 "Hatched = drawn as a raw polygon in glyph code, not by a stroke primitive.")
    dm = ImageDraw.Draw(Image.new('RGB', (8, 8)))
    y = margin + int(36 * k * (1.6 if poster else 1)); title_base = y; y += int(24 * k)
    items = []
    if legend:
        x = margin; y += int(44 * k)
        for r in legend:
            wt = int(48 * k) + int(dm.textlength(ROLE_LABEL[r], font=fnt)) + int(44 * k)
            if x > margin and x + wt > maxw - margin:
                x = margin; y += int(48 * k)
            items.append((x, y, r)); x += wt
        y += int(18 * k)
    note_lines = []; cur_l = ''
    for wd in notes.split(' '):
        t = (cur_l + ' ' + wd).strip()
        if cur_l and dm.textlength(t, font=fsm) > maxw - 2 * margin:
            note_lines.append(cur_l); cur_l = wd
        else:
            cur_l = t
    if cur_l: note_lines.append(cur_l)
    y += int(40 * k); notes_base = y; y += int(32 * k) * (len(note_lines) - 1) + int(30 * k)
    head_h = y
    total_h = head_h + len(rows) * (label_h + word_h + int(30 * k)) + margin
    sheet = Image.new('RGB', (maxw, total_h), (255, 255, 255)); d = ImageDraw.Draw(sheet)
    d.text((margin, title_base), title, font=fbd, fill=(20, 20, 20), anchor='ls')
    for x, yb, r in items:
        d.rectangle([x, yb - int(30 * k), x + int(38 * k), yb + int(4 * k)], fill=ROLE_COLOR[r])
        d.text((x + int(48 * k), yb), ROLE_LABEL[r], font=fnt, fill=(30, 30, 30), anchor='ls')
    for j, ln in enumerate(note_lines):
        d.text((margin, notes_base + int(32 * k) * j), ln, font=fsm, fill=(70, 70, 70), anchor='ls')
    y = head_h
    for row in rows:
        x = margin
        for w, img in row:
            if not poster:
                lab = f"{w['rank']}  {w['form']}  {w['count']:,}"
                d.text((x + 10, y + label_h - 8), lab, font=flab, fill=(40, 40, 40), anchor='ls')
            sheet.paste(Image.fromarray(img), (x, y + label_h))
            x += img.shape[1] + gapx
        y += label_h + word_h + int(30 * k)
    sheet = sheet.crop((0, 0, maxw, y + margin))
    sheet.save(out_path)
    return stats


def render_key(style, glyphs, out_path, px_xh, xh):
    """Every distinct letter once, colored by role, each stroke NUMBERED as the JSON and the doc
    number it -- the picture the per-stroke table is read against."""
    from PIL import Image, ImageDraw, ImageFont
    from shapely.ops import polylabel
    sc = px_xh / xh; SS = 4; pad = 30
    try:
        fnum = ImageFont.truetype(UI_BOLD, 30); flab = ImageFont.truetype(UI_BOLD, 34); fbd = ImageFont.truetype(UI_BOLD, 36)
        fsm = ImageFont.truetype(UI_FONT, 24); fsmn = ImageFont.truetype(UI_BOLD, 22)
    except OSError:
        fnum = flab = fbd = fsm = fsmn = ImageFont.load_default()
    gl = [G for G in glyphs if G.strokes]
    asc = max(G.ttf.bounds[3] for G in gl) + 20; desc = -min(G.ttf.bounds[1] for G in gl) + 20
    tiles = []
    for G in gl:
        x0, x1 = G.ttf.bounds[0], G.ttf.bounds[2]
        items = [(s.geom_built, ROLE_COLOR[s.role], s.raw) for s in G.strokes]
        img, _ = compose_word((items, G.ttf, x0, x1), sc, SS, asc, desc, pad, 7)
        tile = Image.fromarray(img); d = ImageDraw.Draw(tile)
        for s in G.strokes:
            g = s.geom_built
            P = g if g.geom_type == 'Polygon' else max(getattr(g, 'geoms', []), key=lambda p: p.area)
            pt = P.centroid         # mid-height on a stem, where polylabel would pick its swollen foot
            if not P.contains(pt):  # a bowl or an arch: its centroid is in the white
                try:
                    pt = polylabel(P, tolerance=1.0)
                except Exception:
                    pt = P.representative_point()
            d.text((pad + (pt.x - x0) * sc, (asc - pt.y) * sc), str(s.sid + 1),
                   font=fnum if g.area >= 5000 else fsmn, fill=(0, 0, 0),
                   anchor='mm', stroke_width=4, stroke_fill=(255, 255, 255))
        tiles.append((G, tile))
    maxw = 2400; margin = 40; gapx = 40; label_h = 50
    rows = []; cur = []; cw = 0
    for G, t in tiles:
        if cur and cw + gapx + t.width > maxw - 2 * margin:
            rows.append(cur); cur = []; cw = 0
        cur.append((G, t)); cw += (gapx if cw else 0) + t.width
    if cur: rows.append(cur)
    th = tiles[0][1].height
    note = ("Each letter once, strokes colored by role (legend on the roles sheet) and numbered as in "
            "stroke-colors-%s.json and docs/albo-stroke-colors-2026-10-01.md. Hatched = raw polygon." % style)
    head = margin + 100
    sheet = Image.new('RGB', (maxw, head + len(rows) * (label_h + th + 20) + margin), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    d.text((margin, margin + 36), f"Albo {style}: the strokes of every letter in the words, numbered", font=fbd,
           fill=(20, 20, 20), anchor='ls')
    d.text((margin, margin + 80), note, font=fsm, fill=(70, 70, 70), anchor='ls')
    y = head
    for row in rows:
        x = margin
        for G, t in row:
            d.text((x + pad, y + label_h - 10), f"{G.ch}  ({len(G.strokes)})", font=flab, fill=(40, 40, 40), anchor='ls')
            sheet.paste(t, (x, y + label_h)); x += t.width + gapx
        y += label_h + th + 20
    sheet.crop((0, 0, maxw, y + margin)).save(out_path)


# ===================================================================== one style (child process)
class Glyph:
    pass


def run_style(style, words, meta, out, fonts_dir, px_xh, table):
    sys.path.insert(0, WS)
    os.chdir(WS)
    if fonts_dir is None:
        fonts_dir = os.path.join(out, 'fonts')
        os.makedirs(fonts_dir, exist_ok=True)
        r = subprocess.run([sys.executable, '-m', 'outlines.build', fonts_dir, '--style', style],
                           cwd=WS, capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"font build failed:\n{r.stdout}\n{r.stderr}")
    ttf_path = os.path.join(fonts_dir, f'Albo-{style}.ttf')
    from fontTools.ttLib import TTFont
    import uharfbuzz as hb
    from shapely import affinity
    from shapely.ops import unary_union
    from outlines import build, pen
    xh = pen.XH
    tt = TTFont(ttf_path); gs = tt.getGlyphSet(); order = tt.getGlyphOrder()
    rcmap = {}
    for cp, gn in sorted(tt.getBestCmap().items()):
        rcmap.setdefault(gn, chr(cp))
    face = hb.Face(hb.Blob.from_file_path(ttf_path)); hfont = hb.Font(face)
    W = build.solve_widths() if any(ch.isupper() for w in words for ch in w['form']) else None
    cache = {}

    def glyph(gname):
        if gname in cache:
            return cache[gname]
        G = Glyph(); G.key = gname; G.ch = rcmap.get(gname); G.ttf = ttf_outline(gs, gname); G.strokes = []
        G.check = {}
        if G.ch and not G.ttf.is_empty:
            g, strokes, tr = glyph_strokes(G.ch, W, xh)
            dx, cost = align_dx(g, G.ttf)
            parts = unary_union([s.geom for s in strokes]) if strokes else None
            if parts is None:      # nothing captured for this glyph: it is drawn in the built outline's gray
                G.check = dict(uncaptured=True)
                cache[gname] = G
                return G
            for s in strokes:
                s.geom_built = affinity.translate(s.geom, dx, 0).intersection(G.ttf)
            strokes = [s for s in strokes if not s.geom_built.is_empty and s.geom_built.area > 0.5]
            for i, s in enumerate(strokes):
                s.sid = i
            pb = affinity.translate(parts, dx, 0)
            G.strokes = strokes
            G.check = dict(dx=round(dx, 2),
                           parts_vs_drawn_iou=round(iou(parts, g), 6),
                           drawn_vs_built_iou=round(iou(affinity.translate(g, dx, 0), G.ttf), 6),
                           built_area=round(G.ttf.area, 1),
                           built_covered=round(pb.intersection(G.ttf).area / G.ttf.area, 6),
                           built_uncovered_units2=round(G.ttf.difference(pb).area, 1),
                           spill_past_built=round(pb.difference(G.ttf).area / G.ttf.area, 6),
                           atoms=len(tr.atoms), atoms_in_glyph=len(tr.pv(g)), cutters=len(tr.cutters),
                           strokes=len(strokes), raw_polygons=sum(1 for s in strokes if s.raw),
                           duplicates_merged=sum(len(s.merged) for s in strokes))
        cache[gname] = G
        return G

    placed = []
    for w in words:
        buf = hb.Buffer(); buf.add_str(w['form']); buf.guess_segment_properties()
        hb.shape(hfont, buf, {"kern": True, "liga": True})
        x = 0; wl = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            gname = order[info.codepoint]
            wl.append((gname, x + pos.x_offset, pos.y_offset, glyph(gname)))
            x += pos.x_advance
        placed.append(wl)
    # stroke hues: per letter, then any touching clash across a letter boundary fixed in that word
    base = {}
    for gname, G in cache.items():
        seed = (ord(G.ch) * 5) % len(PALETTE) if G.ch else 0
        base[gname] = color_glyph(G.strokes, seed)
    clashes = 0
    for w, wl in zip(words, placed):
        cols = {gname: dict(base[gname]) for gname, _, _, _ in wl}
        w['colors'] = cols
        for (ga, xa, ya, A), (gb, xb, yb, B) in zip(wl, wl[1:]):
            if ga == gb:
                continue
            for sb in B.strokes:
                gbm = affinity.translate(sb.geom_built, xb, yb)
                near = [sa for sa in A.strokes if affinity.translate(sa.geom_built, xa, ya).distance(gbm) <= 30.0]
                if any(cols[ga][sa.sid] == cols[gb][sb.sid] for sa in near):
                    own = [cols[gb][t.sid] for t in B.strokes
                           if t is not sb and t.geom_built.distance(sb.geom_built) <= 8.0]
                    near_c = [cols[ga][sa.sid] for sa in near] + own
                    pick = pick_hue(set(near_c), set(), near_c, list(range(len(PALETTE))))
                    cols[gb] = dict(cols[gb]); cols[gb][sb.sid] = pick; clashes += 1
    # is what we drew what SHIPS? the fonts above come from the live tree; compare every glyph used
    # (outline and advance) and every word's shaping against the reader's copy, when it is present
    vs = None
    ship = os.path.join(os.path.expanduser(os.environ.get('ALBO_SHIPPED_DIR', SHIPPED_DIR)), f'Albo-{style}.ttf')
    if os.path.exists(ship) and os.path.realpath(ship) != os.path.realpath(ttf_path):
        from fontTools.pens.recordingPen import RecordingPen
        st_ = TTFont(ship); sgs = st_.getGlyphSet(); sorder = st_.getGlyphOrder()
        sfont = hb.Font(hb.Face(hb.Blob.from_file_path(ship)))
        gdiff = []
        for gname in cache:
            if gname not in sgs:
                gdiff.append(gname); continue
            pa, pb = RecordingPen(), RecordingPen()
            gs[gname].draw(pa); sgs[gname].draw(pb)
            if pa.value != pb.value or gs[gname].width != sgs[gname].width:
                gdiff.append(gname)
        wdiff = []
        for w in words:
            res = []
            for f_, od in ((hfont, order), (sfont, sorder)):
                buf = hb.Buffer(); buf.add_str(w['form']); buf.guess_segment_properties()
                hb.shape(f_, buf, {"kern": True, "liga": True})
                res.append([(od[i.codepoint], p.x_advance, p.x_offset, p.y_offset)
                            for i, p in zip(buf.glyph_infos, buf.glyph_positions)])
            if res[0] != res[1]:
                wdiff.append(w['form'])
        vs = dict(shipped=ship, glyphs_differing=gdiff, words_shaped_differently=wdiff)
        print(f"{style}: against the shipped {ship}: {len(gdiff)} of {len(cache)} glyphs differ in outline or "
              f"advance, {len(wdiff)} of {len(words)} words shape differently"
              + (f" -- {gdiff + wdiff}" if gdiff or wdiff else ''))
    os.makedirs(out, exist_ok=True)
    rpath = os.path.join(out, f'stroke-colors-{style}-roles.png')
    spath = os.path.join(out, f'stroke-colors-{style}-strokes.png')
    kpath = os.path.join(out, f'stroke-colors-{style}-key.png')
    st_r = render_sheet(words, placed, 'roles', style, meta, rpath, px_xh, xh)
    st_s = render_sheet(words, placed, 'strokes', style, meta, spath, px_xh, xh)
    seen = []
    for wl in placed:
        for gname, _, _, G in wl:
            if G not in seen: seen.append(G)
    render_key(style, seen, kpath, px_xh, xh)
    rep = dict(style=style, font=ttf_path, vs_shipped=vs, px_per_xheight=px_xh, xheight_units=xh,
               sheets=dict(roles=rpath, strokes=spath, key=kpath), raster=dict(roles=st_r, strokes=st_s),
               cross_letter_hue_clashes_fixed=clashes, glyphs={})
    for gname, G in cache.items():
        rep['glyphs'][gname] = dict(char=G.ch, check=G.check, strokes=[
            dict(n=s.sid + 1, role=s.role, why=s.why, decided_by=s.src, raw_polygon=s.raw,
                 builder=' > '.join(x.name for x in s.rec.path()[glyph_index(s.rec.path()):]),
                 site=(f"{os.path.relpath(s.rec.site[0], WS)}:{s.rec.site[1]}" if s.rec.site else ''),
                 area=round(s.geom_built.area, 1), atoms=len(s.aids), merged_duplicates=len(s.merged))
            for s in G.strokes])
    jpath = os.path.join(out, f'stroke-colors-{style}.json')
    json.dump(rep, open(jpath, 'w'), indent=1, ensure_ascii=False)
    print(f"{style}: {rpath}\n{style}: {spath}\n{style}: {kpath}\n{style}: {jpath}")
    worst = min((G.check.get('built_covered', 1.0), gn) for gn, G in cache.items() if G.check)
    print(f"{style}: {len(cache)} glyphs; worst built coverage {worst[0]:.5f} ({worst[1]}); "
          f"nearest-filled px {st_r['nearest_filled_px']} of {st_r['glyph_px']} (supersampled)")
    if table:
        for gname, G in cache.items():
            c = G.check
            print(f"\n{style} {G.ch!r}  strokes={c.get('strokes')} raw={c.get('raw_polygons')} "
                  f"A={c.get('parts_vs_drawn_iou')} B={c.get('drawn_vs_built_iou')} C={c.get('built_covered')}")
            for s in G.strokes:
                print(f"  {s.sid + 1:2d} {s.role:9s} {'RAW ' if s.raw else '    '}"
                      f"{' > '.join(x.name for x in s.rec.path()[glyph_index(s.rec.path()) + 1:]):40s} {s.why}")


# ===================================================================== main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--out', required=True)
    ap.add_argument('--words', help='space-separated words instead of the corpus top N')
    ap.add_argument('--top', type=int, default=20)
    ap.add_argument('--styles', default='Regular,Italic')
    ap.add_argument('--fonts', help='a directory holding Albo-<Style>.ttf (default: build from the live tree)')
    ap.add_argument('--px-xh', type=float, default=200.0, help='pixels per x-height (default 200)')
    ap.add_argument('--table', action='store_true')
    ap.add_argument('--poster', help='a POSTER of --words under this title: sized by --px-xh, no per-word counts')
    ap.add_argument('--child', help=argparse.SUPPRESS)
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    wpath = os.path.join(out, 'words.json')
    if a.child:
        d = json.load(open(wpath))
        run_style(a.child, d['words'], d['meta'], out, os.path.abspath(a.fonts) if a.fonts else None, a.px_xh, a.table)
        return
    os.makedirs(out, exist_ok=True)
    if a.words:
        words = [dict(rank=i, word=w.casefold(), count=0, form=w, forms=[]) for i, w in enumerate(a.words.split(), 1)]
        meta = dict(books=0, words=0, distinct=0)
        cnt, forms, books = corpus_counts()
        for w in words:
            w['count'] = cnt.get(w['word'], 0)
        meta = dict(books=len(books), words=sum(cnt.values()), distinct=len(cnt))
        if a.poster: meta['poster'] = a.poster
    else:
        words, meta = top_words(a.top)
    json.dump(dict(words=words, meta=meta), open(wpath, 'w'), indent=1, ensure_ascii=False)
    print(f"{meta['books']} books, {meta['words']:,} words, {meta['distinct']:,} distinct")
    for w in words:
        print(f"  {w['rank']:2d}  {w['form']:8s} {w['count']:>7,}")
    sys.stdout.flush()
    for style in [s.strip() for s in a.styles.split(',') if s.strip()]:
        env = dict(os.environ)
        for k in list(env):
            if k.startswith('FJORD_') or k == 'ALBO_ITALIC':
                del env[k]
        env.update(style_env(style))
        cmd = [sys.executable, os.path.abspath(__file__), '--out', out, '--child', style, '--px-xh', str(a.px_xh)]
        if a.fonts: cmd += ['--fonts', a.fonts]
        if a.table: cmd += ['--table']
        r = subprocess.run(cmd, env=env, cwd=WS)
        if r.returncode:
            sys.exit(r.returncode)


if __name__ == '__main__':
    main()
