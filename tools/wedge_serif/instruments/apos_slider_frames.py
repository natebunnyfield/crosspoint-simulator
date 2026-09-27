#!/usr/bin/env python3
"""The APOSTROPHE slider page (2026-09-26): one slider per apostrophe dial,
every step a real FreeType render, UNHINTED (FT_LOAD_NO_HINTING, as the
reader renders Albo since round 401), prerendered.

Owner 2026-09-26: *"reduce apostrophe to match rest of word image"*. The
dials are ALBO_APOS_* in outlines/glyphs/marks.py; 1.0 is today, byte for
byte. Modeled on r394_slider_frames.py (the thick/thin page he ruled from).

For every dial x step it:
  1. builds all four cuts with that one variable (the shipped step builds
     nothing extra -- it IS the baseline);
  2. gates every cut: cmp_touch (any touching pair or pair under the floor),
     cmp_contour_hairs --letters (exit) and the full sweep (any row the
     shipped build does not have), cmp_counter_dents (any change),
     cmp_aldine_glitch --all (any finding the shipped build lacks), and
     approved.py on the 400s. A failing step is KEPT and flagged;
  3. measures the mark against its own letters and the reference medians
     (instruments/apos_measure.py) and the white of the pairs the owner
     judged on the bench ('s n' r' t'), both the horizontal white
     (rsb + kern + lsb) and the 2-D closest approach, in font units;
  4. writes ONE composite PNG per step: the paragraph at 27 px shown 2x
     nearest (roman, italic), the same words at 54 px native, the key words
     at 27 px x3 as a DIFFERENCE against shipped (glyphs held at the shipped
     positions, so a spacing change does not read as a shape change), and a
     200 px close-up of "n't" (filled, and overlaid on shipped);
  5. writes index.html with the data inlined, plus the RECOMMENDED
     combination with the doubles flag off and on.

    ALBO_BUILD_PY=$(which python3) uv run --python 3.13 --with uharfbuzz --with freetype-py \
        --with shapely --with fonttools --with pillow --with numpy \
        python instruments/apos_slider_frames.py --work WORKDIR --out OUTDIR
"""
import argparse, concurrent.futures as cf, json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import freetype, uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tools/wedge_serif
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "instruments"))
import apos_measure as AM

W = 760
# The builds and the gates run on the tree's own interpreter (free-threaded,
# shapely); this script's rendering needs uharfbuzz, whose abi3 wheel does not
# load on a free-threaded build, so it may run elsewhere (uv run --with ...).
BUILD_PY = os.environ.get("ALBO_BUILD_PY", "python3")
UI = "/System/Library/Fonts/Supplemental/Arial.ttf"
ENV = {
    "Regular": dict(FJORD_STEM="66.9", FJORD_CONTRAST="0.892"),
    "Italic": dict(ALBO_ITALIC="aldine", FJORD_STEM="66.9", FJORD_CONTRAST="0.80", FJORD_WIDTH="95", FJORD_SLANT="13"),
    "Bold": dict(FJORD_STEM="116", FJORD_SLANT="0", FJORD_CONTRAST="0.80", FJORD_WIDTH="95", FJORD_CUT="0"),
    "BoldItalic": dict(ALBO_ITALIC="aldine", FJORD_STEM="116", FJORD_SLANT="13", FJORD_CONTRAST="0.80", FJORD_WIDTH="95", FJORD_CUT="0"),
}

Q = "’"
TEXT = {
    "curly": ("It’s nine o’clock, and I’m sure they’re fine, so don’t wait up. We’ve read "
              "Suvi’s notes; she’ll say the world’s rock ’n’ roll isn’t what it was, "
              "and that’s that. ‘Quiet,’ Wren’s sister said. “You can’t,” he answered."),
    "straight": ("It's nine o'clock, and I'm sure they're fine, so don't wait up. We've read Suvi's notes; "
                 "she'll say the world's rock 'n' roll isn't what it was, and that's that. "
                 "'Quiet,' Wren's sister said. \"You can't,\" he answered."),
}
SHORT = {"curly": "It’s nine o’clock; don’t wait. Suvi’s notes aren’t they’re.",
         "straight": "It's nine o'clock; don't wait. Suvi's notes aren't they're."}
KEY = {"curly": "don’t it’s they’re", "straight": "don't it's they're"}
CLOSE = {"curly": "n’t", "straight": "n't"}
PAIRS = {"curly": ["n’", "’s", "t’", "r’", "’t"], "straight": ["n'", "'s", "t'", "r'", "'t"]}

# key, title, env, kind, steps, shipped, recommended, note
DIALS = [
    ("head", "’ head: the dot only (x its radius)", "ALBO_APOS_HEAD", "curly",
     ["1.00", "0.95", "0.90", "0.85", "0.80", "0.75", "0.70", "0.65"], "1.00", "0.85",
     "The dot shrinks toward the top line; the tail follows its center, so the foot rises by what the radius loses."),
    ("scale", "’ whole mark (x, about its top)", "ALBO_APOS_SCALE", "curly",
     ["1.00", "0.95", "0.90", "0.85", "0.80", "0.75", "0.70"], "1.00", "1.00",
     "Head and tail together, hung from the same line. Round 375 set the height at the reference median."),
    ("tail", "’ tail reach and swing (x)", "ALBO_APOS_TAIL", "curly",
     ["1.00", "0.95", "0.90", "0.85", "0.80", "0.75", "0.70"], "1.00", "1.00",
     "The comma's L and W for the apostrophe only; the dot is kept."),
    ("tailw", "’ tail width (x)", "ALBO_APOS_TAIL_W", "curly",
     ["1.00", "0.90", "0.80", "0.70", "0.60"], "1.00", "1.00",
     "The pen's taper along the tail, 0.85 to 0.30 of the pen, scaled."),
    ("sw", "straight ' thickness (x, about its axis)", "ALBO_APOS_STRAIGHT_W", "straight",
     ["1.00", "0.90", "0.85", "0.80", "0.75", "0.70", "0.65", "0.60"], "1.00", "0.75",
     "U+0027, the apostrophe of the Eighth Atlas (843 per copy). Round 386's option c shape kept."),
    ("ss", "straight ' whole mark (x, about its top)", "ALBO_APOS_STRAIGHT", "straight",
     ["1.00", "0.95", "0.90", "0.85", "0.80", "0.75"], "1.00", "1.00",
     "Round 377 matched the straight quotes' height to the curly ones'."),
]
D = {d[0]: dict(zip(("key", "title", "env", "kind", "steps", "shipped", "rec", "note"), d)) for d in DIALS}


def env_for(d, v):
    return {} if v == d["shipped"] else {d["env"]: v}


def rec_env():
    return {d["env"]: d["rec"] for d in D.values() if d["rec"] != d["shipped"]}


def build(outdir, cut, extra):
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, f"Albo-{cut}.ttf")
    if os.path.exists(p): return p
    e = dict(os.environ); e.update(ENV[cut]); e.update(extra); e["PYTHON_GIL"] = "0"
    r = subprocess.run([BUILD_PY, "-m", "outlines.build", outdir, "--style", cut], cwd=HERE, env=e,
                       capture_output=True, text=True)
    if r.returncode: raise SystemExit(f"build failed {outdir} {cut}\n{r.stderr[-800:]}")
    return p


def run(cmd):
    r = subprocess.run(cmd, cwd=HERE, env=dict(os.environ, PYTHON_GIL="0"), capture_output=True, text=True)
    return r.returncode, r.stdout


def gate_sig(ttf):
    out = {}
    rc, t = run([BUILD_PY, "cmp_touch.py", ttf])
    m = re.search(r"(\d+) pair\(s\) TOUCHING, (\d+) below", t)
    out["touch"] = (int(m.group(1)), int(m.group(2))) if m else ("?",)
    rc, _ = run([BUILD_PY, "cmp_contour_hairs.py", ttf, "--letters"]); out["hairs"] = rc
    rc, t = run([BUILD_PY, "cmp_contour_hairs.py", ttf])
    out["hairs_all"] = sorted(ln.split()[0] for ln in t.splitlines() if re.match(r"^\s+\S+\s+segs", ln))
    rc, t = run([BUILD_PY, "cmp_counter_dents.py", ttf])
    out["dents"] = t.strip().splitlines()[-1].split(":", 1)[-1].strip() if t.strip() else ""
    rc, t = run([BUILD_PY, "cmp_aldine_glitch.py", "--ttf", ttf, "--all"])
    g, found = None, []
    for ln in t.splitlines():
        if re.search(r"U\+[0-9A-F]+$", ln): g = ln.split()[-1]
        elif re.match(r"^    [A-Z]+ ", ln): found.append(f"{g} {ln.split()[0]}")
    out["glitch"] = sorted(found)
    return out


def fails(sig, base):
    f = []
    if sig["touch"] != (0, 0): f.append(f"touch {sig['touch']}")
    if sig["hairs"] != 0: f.append("hairs")
    new_h = sorted(set(sig["hairs_all"]) - set(base["hairs_all"]))
    if new_h: f.append("hairs(all) " + " ".join(new_h))
    if sig["dents"] != base["dents"]: f.append("dents")
    new = sorted(set(sig["glitch"]) - set(base["glitch"]))
    if new: f.append("glitch " + ", ".join(new))
    return f


# ------------------------------------------------------------------ unhinted setting
class Setter:
    def __init__(self, path, ppem):
        self.face = freetype.Face(path); self.face.set_pixel_sizes(0, ppem); self.ppem = ppem
        self.hbf = hb.Font(hb.Face(hb.Blob(open(path, "rb").read())))
        self.upem = self.hbf.face.upem; self.hbf.scale = (self.upem, self.upem); self.cache = {}

    def glyph(self, gid):
        if gid not in self.cache:
            self.face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
            b = self.face.glyph.bitmap
            a = (np.frombuffer(bytes(b.buffer), np.uint8).reshape(b.rows, abs(b.pitch))[:, :b.width].copy()
                 if b.rows and b.width else np.zeros((0, 0), np.uint8))
            self.cache[gid] = (a, self.face.glyph.bitmap_left, self.face.glyph.bitmap_top)
        return self.cache[gid]

    def shape(self, text):
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
        hb.shape(self.hbf, buf, {"kern": True, "liga": True})
        k = self.ppem / self.upem; out, x = [], 0.0
        for i, p in zip(buf.glyph_infos, buf.glyph_positions):
            out.append((i.codepoint, x + p.x_offset * k)); x += p.x_advance * k
        return out, x

    def wrap(self, text, width):
        lines, cur = [], ""
        for w in text.split():
            t = (cur + " " + w).strip()
            if cur and self.shape(t)[1] > width: lines.append(cur); cur = w
            else: cur = t
        return lines + ([cur] if cur else [])


def set_block(path, text, ppem, width, ref=None):
    """Coverage 0..1. ref=None: the arm's own layout. ref given: every glyph at
    the REF font's position (shape only)."""
    s = Setter(path, ppem); r = Setter(ref, ppem) if ref else s
    pad = max(4, ppem // 4); lines = r.wrap(text, width - 2 * pad)
    lh = int(round(ppem * 1.35)); asc = int(round(ppem * 0.95))
    out = np.zeros((lh * len(lines) + int(ppem * 0.5), width), np.uint8)
    for n, ln in enumerate(lines):
        base = asc + n * lh
        gl, _ = s.shape(ln); pos, _ = r.shape(ln)
        for (gid, _x), (_g, x) in zip(gl, pos):
            a, left, top = s.glyph(gid)
            if not a.size: continue
            x0 = pad + int(round(x)) + left; y0 = base - top; h, w = a.shape
            ys, xs = max(0, -y0), max(0, -x0); ye, xe = min(h, out.shape[0] - y0), min(w, out.shape[1] - x0)
            if ye > ys and xe > xs:
                reg = out[y0 + ys:y0 + ye, x0 + xs:x0 + xe]; np.maximum(reg, a[ys:ye, xs:xe], out=reg)
    return out.astype(float) / 255.0


def gray(cov):
    return Image.fromarray((255 - cov * 255).clip(0, 255).astype(np.uint8)).convert("RGB")


def diffimg(ca, cx):
    add = np.clip((cx - ca) * 4, 0, 1); rem = np.clip((ca - cx) * 4, 0, 1)
    both = np.minimum(ca, cx) * (1 - np.maximum(add, rem))
    r = 255 - both * 140 - add * 255; g = 255 - both * 140 - add * 150 - rem * 255; b = 255 - both * 140 - rem * 255
    return Image.fromarray(np.stack([r, g, b], -1).clip(0, 255).astype(np.uint8))


def label(text, size=17, fill=(70, 70, 70), bg=(255, 255, 255), h=28):
    im = Image.new("RGB", (W, h), bg)
    ImageDraw.Draw(im).text((6, h - 8), text, font=ImageFont.truetype(UI, size), fill=fill, anchor="ls")
    return im


def pad_to(a, h, w):
    o = np.zeros((h, w)); o[:min(h, a.shape[0]), :min(w, a.shape[1])] = a[:h, :w]; return o


def frame(title, kind, fonts, refs):
    """fonts / refs: {"Regular": path, "Italic": path}."""
    parts = [label(title, 19, (0, 0, 0), (235, 235, 230), 34)]
    for st in ("Regular", "Italic"):
        parts.append(label(f"{st}, 27 px unhinted, shown 2x nearest-neighbor"))
        c = set_block(fonts[st], TEXT[kind], 27, W // 2)
        parts.append(gray(c).resize((W, c.shape[0] * 2), Image.NEAREST))
    for st in ("Regular", "Italic"):
        parts.append(label(f"{st}, 54 px unhinted, native (the phone's 2x)"))
        parts.append(gray(set_block(fonts[st], SHORT[kind], 54, W)))
    parts.append(label("difference against as shipped, 27 px x3, at shipped positions: gray same, blue added, red removed"))
    for st in ("Regular", "Italic"):
        ca = set_block(refs[st], KEY[kind], 27, W // 3 + 60, ref=refs[st])
        cx = set_block(fonts[st], KEY[kind], 27, W // 3 + 60, ref=refs[st])
        h = max(ca.shape[0], cx.shape[0]); ca, cx = pad_to(ca, h, ca.shape[1]), pad_to(cx, h, ca.shape[1])
        d = diffimg(ca, cx).resize((ca.shape[1] * 3, h * 3), Image.NEAREST)
        row = Image.new("RGB", (W, h * 3), "white"); row.paste(d.crop((0, 0, min(W, d.width), h * 3)), (0, 0))
        parts.append(row)
    parts.append(label("200 px close-up per style: this step, own spacing | overlaid on shipped (blue added, red line = shipped)"))
    cells = []
    for st in ("Regular", "Italic"):
        cx = set_block(fonts[st], CLOSE[kind], 200, W // 2)
        ca = set_block(refs[st], CLOSE[kind], 200, W // 2, ref=refs[st]); cf_ = set_block(fonts[st], CLOSE[kind], 200, W // 2, ref=refs[st])
        h = max(cx.shape[0], ca.shape[0]); cx, ca, cf_ = (pad_to(a, h, W // 2) for a in (cx, ca, cf_))
        ink = np.nonzero((np.maximum(np.maximum(cx, ca), cf_) > 0.02).any(1))[0]   # trim the empty leading
        y0, y1 = max(0, ink[0] - 12), min(h, ink[-1] + 13); cx, ca, cf_ = cx[y0:y1], ca[y0:y1], cf_[y0:y1]; h = y1 - y0
        ov = np.array(diffimg(ca, cf_), dtype=float); ma = ca > 0.5; er = ma.copy()
        for _ in range(2): er = er & np.roll(er, 1, 0) & np.roll(er, -1, 0) & np.roll(er, 1, 1) & np.roll(er, -1, 1)
        ov[ma & ~er] = (200, 0, 0)
        row = Image.new("RGB", (W, h), "white"); row.paste(gray(cx), (0, 0)); row.paste(Image.fromarray(ov.astype(np.uint8)), (W // 2, 0))
        cells.append(row)
    parts += cells
    out = Image.new("RGB", (W, sum(p.height for p in parts)), "white"); y = 0
    for p in parts: out.paste(p, (0, y)); y += p.height
    return out


# ------------------------------------------------------------------ spacing
class _Poly(BasePen):
    def __init__(self, gs):
        super().__init__(gs); self.rings, self.cur = [], []
    def _moveTo(self, p): self.cur = [p]
    def _lineTo(self, p): self.cur.append(p)
    def _curveToOne(self, a, b, c):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8; u = 1 - t
            self.cur.append((u**3*p0[0] + 3*u*u*t*a[0] + 3*u*t*t*b[0] + t**3*c[0], u**3*p0[1] + 3*u*u*t*a[1] + 3*u*t*t*b[1] + t**3*c[1]))
    def _qCurveToOne(self, a, b):
        p0 = self.cur[-1]
        for i in range(1, 7):
            t = i / 6; u = 1 - t
            self.cur.append((u*u*p0[0] + 2*u*t*a[0] + t*t*b[0], u*u*p0[1] + 2*u*t*a[1] + t*t*b[1]))
    def _closePath(self):
        if len(self.cur) > 2: self.rings.append(self.cur)
        self.cur = []
    _endPath = _closePath


def poly(font, gname):
    pen = _Poly(font.getGlyphSet()); font.getGlyphSet()[gname].draw(pen)
    g = None
    for r in pen.rings:
        p = Polygon(r).buffer(0)
        g = p if g is None else g.symmetric_difference(p)
    return g


def pair_white(path, pairs):
    """{pair: (horizontal white, 2-D closest), advance of the mark}, font units."""
    f = TTFont(path); cmap = f.getBestCmap(); hbf = hb.Font(hb.Face(hb.Blob(open(path, "rb").read())))
    out = {}
    for pr in pairs:
        buf = hb.Buffer(); buf.add_str(pr); buf.guess_segment_properties(); hb.shape(hbf, buf, {"kern": True})
        names = [f.getGlyphOrder()[i.codepoint] for i in buf.glyph_infos]
        x1 = buf.glyph_positions[0].x_advance
        a = poly(f, names[0]); b = poly(f, names[1])
        from shapely.affinity import translate
        b = translate(b, xoff=x1 + buf.glyph_positions[1].x_offset)
        hw = b.bounds[0] - a.bounds[2]
        out[pr] = (round(hw, 1), round(a.distance(b), 1))
    q = "quoteright" if "’" in "".join(pairs) else "quotesingle"
    out["adv"] = f["hmtx"][q][0]
    return out


# ------------------------------------------------------------------ jobs
def job_measure(args):
    key, title, kind, fonts, refs, frame_path = args
    m = {}
    for st in ("Regular", "Italic"):
        R = AM.measure(st, fonts[st], 0)
        mk = R["apos"] if kind == "curly" else R["straight"]
        m[st] = dict(h=mk["h"], head=mk["head"], foot=mk["bot"],
                     ink_n=(R["apos_over_n"] if kind == "curly" else R["straight_over_n"]),
                     pairs=pair_white(fonts[st], PAIRS[kind]))
    for sz, k in ((27, "px27"), (54, "px54")):
        a = set_block(refs["Regular"], TEXT[kind], sz, W // 2 if sz == 27 else W, ref=refs["Regular"])
        x = set_block(fonts["Regular"], TEXT[kind], sz, W // 2 if sz == 27 else W, ref=refs["Regular"])
        m[k] = 100.0 * (np.abs(a - x) > 8 / 255).mean()
    frame(title, kind, fonts, refs).save(frame_path)
    return key, m


def job_gate(args):
    key, paths = args
    return key, {c: gate_sig(p) for c, p in paths.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("-j", type=int, default=8); ap.add_argument("--page-only", action="store_true")
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, "frames"), exist_ok=True)
    bdir = os.path.join(a.work, "build"); base = os.path.join(bdir, "shipped")
    variants = {}   # key -> (dir, env)
    for k, d in D.items():
        for i, v in enumerate(d["steps"]):
            variants[(k, i)] = (base, {}) if v == d["shipped"] else (os.path.join(bdir, f"{k}_{i}"), env_for(d, v))
    RE = rec_env()
    variants[("combo", 0)] = (os.path.join(bdir, "combo_single"), dict(RE))
    variants[("combo", 1)] = (os.path.join(bdir, "combo_doubles"), dict(RE, ALBO_APOS_DOUBLES="1"))
    jobs = sorted({(dr, c, tuple(sorted(e.items()))) for dr, e in variants.values() for c in ENV})
    with cf.ThreadPoolExecutor(a.j) as ex: list(ex.map(lambda j: build(j[0], j[1], dict(j[2])), jobs))
    print("built", len(jobs), flush=True)
    P = lambda key, c: os.path.join(variants[key][0], f"Albo-{c}.ttf")
    refs = {c: os.path.join(base, f"Albo-{c}.ttf") for c in ENV}

    cache = os.path.join(a.work, "measure_cache.json")
    if a.page_only and os.path.exists(cache):
        C = json.load(open(cache)); gates = {tuple(json.loads(k)): v for k, v in C["gates"].items()}
        meas = {tuple(json.loads(k)): v for k, v in C["meas"].items()}
    else:
        base_sig = {c: gate_sig(refs[c]) for c in ENV}
        gjobs = [(key, {c: P(key, c) for c in ENV}) for key, (dr, _) in variants.items() if dr != base]
        gates = {}
        with cf.ProcessPoolExecutor(a.j) as ex:
            for key, sig in ex.map(job_gate, gjobs):
                gates[key] = [f"{c}: {x}" for c, s in sig.items() for x in fails(s, base_sig[c])]
        for key, (dr, _) in variants.items():
            if dr == base: continue
            rc, _ = run([BUILD_PY, "approved.py", "--check", "--regular", P(key, "Regular"), "--italic", P(key, "Italic")])
            if rc: gates[key].append("approved glyph changed")
        print("gated", flush=True)
        mjobs = []
        for key in variants:
            k, i = key
            kind = "curly" if k == "combo" else D[k]["kind"]
            title = (f"{D[k]['title']}  =  {D[k]['steps'][i]}" + ("   [as shipped]" if D[k]["steps"][i] == D[k]["shipped"] else "")
                     + ("   [recommended]" if D[k]["steps"][i] == D[k]["rec"] else "")) if k != "combo" else \
                    ("Recommended picks together, doubles " + ("follow (“ ” and \" too)" if i else "unchanged"))
            mjobs.append((key, title, kind, {st: P(key, st) for st in ("Regular", "Italic")},
                          {st: refs[st] for st in ("Regular", "Italic")},
                          os.path.join(a.out, "frames", f"{k}_{i:02d}.png")))
        meas = {}
        with cf.ProcessPoolExecutor(a.j) as ex:
            for key, m in ex.map(job_measure, mjobs): meas[key] = m
        # the combo frames also carry the straight paragraph? no: one frame per combo arm, curly text
        json.dump({"gates": {json.dumps(list(k)): v for k, v in gates.items()},
                   "meas": {json.dumps(list(k)): v for k, v in meas.items()}}, open(cache, "w"), indent=1)
    # pad each slider's frames to its tallest
    groups = {k: [f"{k}_{i:02d}.png" for i in range(len(d["steps"]))] for k, d in D.items()}
    groups["combo"] = ["combo_00.png", "combo_01.png"]
    for k, fr in groups.items():
        fr = [os.path.join(a.out, "frames", p) for p in fr]
        H = max(Image.open(p).height for p in fr)
        for p in fr:
            im = Image.open(p)
            if im.height < H:
                o = Image.new("RGB", (W, H), "white"); o.paste(im, (0, 0)); o.save(p, optimize=True)
    refm = {}
    for st, rows in (("Regular", AM.REFS_ROMAN), ("Italic", AM.REFS_ITALIC)):
        rr = [AM.measure(*r) for r in rows if os.path.exists(r[1])]
        refm[st] = {"curly": dict(h=float(np.median([r["apos"]["h"] for r in rr])),
                                  head=float(np.median([r["apos"]["head"] for r in rr])),
                                  foot=float(np.median([r["apos"]["bot"] for r in rr])),
                                  ink_n=float(np.median([r["apos_over_n"] for r in rr]))),
                    "straight": dict(h=float(np.median([r["straight"]["h"] for r in rr])),
                                     head=float(np.median([r["straight"]["head"] for r in rr])),
                                     foot=float(np.median([r["straight"]["bot"] for r in rr])),
                                     ink_n=float(np.median([r["straight_over_n"] for r in rr])))}
    data = []
    for k, d in D.items():
        steps = []
        for i, v in enumerate(d["steps"]):
            m = meas[(k, i)]
            steps.append(dict(v=v, img=f"frames/{k}_{i:02d}.png", px27=round(m["px27"], 2), px54=round(m["px54"], 2),
                              st={st: m[st] for st in ("Regular", "Italic")}, fails=gates.get((k, i), [])))
        data.append(dict(key=k, title=d["title"], env=d["env"], note=d["note"], kind=d["kind"],
                         shipped=d["steps"].index(d["shipped"]), rec=d["steps"].index(d["rec"]), steps=steps))
    combo = [dict(img=f"frames/combo_{i:02d}.png", st={st: meas[("combo", i)][st] for st in ("Regular", "Italic")},
                  fails=gates.get(("combo", i), []), px27=round(meas[("combo", i)]["px27"], 2),
                  px54=round(meas[("combo", i)]["px54"], 2)) for i in (0, 1)]
    shipped_curly = meas[("head", 0)]; shipped_straight = meas[("sw", 0)]
    json.dump(dict(dials=data, combo=combo, refm=refm, rec=RE), open(os.path.join(a.work, "slider_data.json"), "w"), indent=1)
    open(os.path.join(a.out, "index.html"), "w").write(page(data, combo, refm, RE))
    print("wrote", a.out)


def page(data, combo, refm, RE):
    js = json.dumps(dict(dials=data, combo=combo, refm=refm, rec=RE))
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Apostrophe Sliders</title>
<style>
:root{--bg:#fbfbf9;--fg:#1d1d1b;--mute:#66645f;--rule:#dddad3;--card:#fff;--accent:#7a3b2e;--ship:#2d6a3e;--rec:#1f55b0;--bad:#b3261e}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161615;--fg:#e8e6e1;--mute:#a19e97;--rule:#3a3935;--card:#202020;--accent:#e0a090;--ship:#7fc795;--rec:#8fb4ff;--bad:#ff8a80}}
:root[data-theme="dark"]{--bg:#161615;--fg:#e8e6e1;--mute:#a19e97;--rule:#3a3935;--card:#202020;--accent:#e0a090;--ship:#7fc795;--rec:#8fb4ff;--bad:#ff8a80}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font:16px/1.45 -apple-system,system-ui,sans-serif;margin:0;padding:16px}
main{max-width:780px;margin:0 auto}
h1{font-size:1.45em;margin:.2em 0}h2{font-size:1.15em;margin:1.8em 0 .2em;border-top:1px solid var(--rule);padding-top:.8em}
h3{font-size:1em;margin:1.2em 0 .2em}
p{margin:.35em 0}.mute{color:var(--mute);font-size:.9em}
img{width:100%;height:auto;image-rendering:pixelated;display:block;background:#fff;border:1px solid var(--rule)}
.dial{margin:1em 0 2em}
.track{position:relative;margin:.4em 0 1.9em}
input[type=range]{width:100%;margin:0;height:2.2em;touch-action:pan-y}
.ticks{position:absolute;left:0;right:0;top:2.2em;height:1.6em;font-size:.72em}
.tick{position:absolute;transform:translateX(-50%);text-align:center;white-space:nowrap;color:var(--mute)}
.tick.ship{color:var(--ship);font-weight:700}.tick.rec{color:var(--rec);font-weight:700}
.nums{font-size:.82em;margin:.4em 0;border-collapse:collapse}.nums td,.nums th{padding:1px 8px 1px 0;vertical-align:top;text-align:left;font-variant-numeric:tabular-nums}
.bad{color:var(--bad);font-weight:700}.ok{color:var(--ship)}
.val{font-weight:700}
button{font:inherit;padding:.5em 1em;border:1px solid var(--rule);background:var(--card);color:var(--fg);border-radius:6px}
button[aria-pressed="true"]{background:var(--rec);color:#fff;border-color:var(--rec)}
textarea{width:100%;height:9em;font:12px/1.3 ui-monospace,monospace;background:var(--card);color:var(--fg);border:1px solid var(--rule)}
.bar{position:sticky;top:0;background:var(--bg);padding:.4em 0;z-index:2;border-bottom:1px solid var(--rule)}
.scroll{overflow-x:auto}
</style></head><body><main>
<div class="bar"><button id="copy">Copy picks</button> <span id="copied" class="mute"></span></div>
<h1>The apostrophe, full range</h1>
<p>One slider per dial. Every step is a real build and a real render: FreeType, <b>unhinted</b>, as the reader renders Albo since round 401. Each frame: the paragraph at 27&nbsp;px shown 2&times; (roman, italic), the same words at 54&nbsp;px, the key words as a difference against as shipped, and a 200&nbsp;px close-up of &ldquo;n&rsquo;t&rdquo;. <span style="color:var(--ship);font-weight:700">S</span> is as shipped, <span style="color:var(--rec);font-weight:700">R</span> the recommended step. A step that fails a gate is still shown, flagged in red.</p>
<p class="mute">Numbers under each image, Regular and Italic, with the reference median (six roman or six italic faces, scaled to the same x-height) in the last column: <b>height</b> and <b>foot</b> in x-heights (foot = how far down the mark reaches); <b>head</b> = the mark's widest run over the face's own lowercase stem; <b>ink / n</b> = the mark's ink over an n's. <b>White</b> = rsb + kern + lsb and the 2-D closest approach, font units, for the pairs judged on the bench. Every dial moves the single marks only (&rsquo; &lsquo; &#700; &#699;, or ' for the two straight dials). Arrow keys step the focused slider; picks are remembered on this device.</p>
<div id="dials"></div>
<h2>The recommended picks together</h2>
<p class="mute">Built as one font. The toggle carries the same dials onto the double quotes (<code>ALBO_APOS_DOUBLES=1</code>), so a nested quote does not set a large &rdquo; beside a small &rsquo;. That is a proposal: the ask named the apostrophe, so it is off unless you turn it on.</p>
<div class="row"><button id="dbl0" aria-pressed="true">Doubles unchanged</button> <button id="dbl1" aria-pressed="false">Doubles follow</button></div>
<img id="comboimg" alt="recommended picks together"><div id="combonums"></div>
<h2>Picks</h2>
<p class="mute">JSON of every slider's current value, keyed by its environment variable; <code>null</code> means as shipped (leave the variable unset). If the copy button cannot reach the clipboard, copy from here.</p>
<textarea id="picks" readonly></textarea>
</main>
<script>
const ALL = """ + js + """;
const DATA = ALL.dials, REFM = ALL.refm;
function load(k,d){try{const v=localStorage.getItem('apos:'+k);return v===null?d:parseInt(v,10)}catch(e){return d}}
function save(k,v){try{localStorage.setItem('apos:'+k,String(v))}catch(e){}}
const state={};const preloaded={};let dbl=0;
function preload(d){if(preloaded[d.key])return;preloaded[d.key]=1;d.steps.forEach(s=>{const i=new Image();i.src=s.img})}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function f3(x){return x.toFixed(3)}
function sttable(st,kind,base){
 const R=REFM,rows=[['height','h'],['foot','foot'],['head','head'],['ink / n','ink_n']];
 let h='<div class="scroll"><table class="nums"><tr><th></th><th>Regular</th><th>ref</th><th>Italic</th><th>ref</th></tr>';
 rows.forEach(([lab,k])=>{h+='<tr><td>'+lab+'</td>';['Regular','Italic'].forEach(s=>{const v=st[s][k],b=base?base[s][k]:null;
   h+='<td>'+f3(v)+(b!==null&&Math.abs(v-b)>0.0005?' <span class="mute">('+(v>=b?'+':'')+((v/b-1)*100).toFixed(0)+'%)</span>':'')+'</td><td class="mute">'+f3(R[s][kind][k])+'</td>'});h+='</tr>'});
 const pairs=Object.keys(st.Regular.pairs).filter(p=>p!=='adv');
 pairs.forEach(p=>{h+='<tr><td>white '+esc(p)+'</td>';['Regular','Italic'].forEach(s=>{const v=st[s].pairs[p],b=base?base[s].pairs[p]:null;
   h+='<td colspan="2">'+v[0].toFixed(0)+' / '+v[1].toFixed(0)+(b?' <span class="mute">(&Delta; '+(v[0]-b[0]>=0?'+':'')+(v[0]-b[0]).toFixed(0)+' / '+(v[1]-b[1]>=0?'+':'')+(v[1]-b[1]).toFixed(0)+')</span>':'')+'</td>'});h+='</tr>'});
 h+='<tr><td>advance</td>';['Regular','Italic'].forEach(s=>{const v=st[s].pairs.adv,b=base?base[s].pairs.adv:null;h+='<td colspan="2">'+v+(b!==null&&v!==b?' <span class="mute">(&Delta; '+(v-b)+')</span>':'')+'</td>'});
 return h+'</tr></table></div>'}
function nums(d,i){const s=d.steps[i],b=d.steps[d.shipped];let h='<table class="nums">';
 h+='<tr><td>value</td><td><span class="val">'+esc(s.v)+'</span>'+(i===d.shipped?' <span class="ok">(as shipped)</span>':'')+(i===d.rec?' <span style="color:var(--rec)">(recommended)</span>':'')+'</td></tr>';
 h+='<tr><td>pixels changed</td><td>roman paragraph: 27 px '+s.px27.toFixed(2)+'% &nbsp; 54 px '+s.px54.toFixed(2)+'%</td></tr>';
 h+='<tr><td>gates</td><td>'+(i===d.shipped?'<span class="ok">as shipped</span>':(s.fails.length?'<span class="bad">fails '+esc(s.fails.join('; '))+'</span>':'<span class="ok">all green (4 cuts)</span>'))+'</td></tr></table>';
 return h+sttable(s.st,d.kind,i===d.shipped?null:b.st)}
function picks(){const o={};DATA.forEach(d=>{const j=state[d.key];o[d.env]=j===d.shipped?null:d.steps[j].v});o.ALBO_APOS_DOUBLES=dbl?'1':null;return JSON.stringify(o,null,1)}
function refresh(){document.getElementById('picks').value=picks()}
const root=document.getElementById('dials');
DATA.forEach(d=>{
 const wrap=document.createElement('div');wrap.className='dial';
 const n=d.steps.length;let i=load(d.key,d.shipped);if(!(i>=0&&i<n))i=d.shipped;state[d.key]=i;
 let ticks='';d.steps.forEach((s,j)=>{const cls=j===d.shipped?'tick ship':(j===d.rec?'tick rec':'tick');const mark=(j===d.shipped?'S ':'')+(j===d.rec&&j!==d.shipped?'R ':'')+(j===d.rec&&j===d.shipped?'R ':'');
   ticks+='<span class="'+cls+'" style="left:calc('+(j/(n-1)*100)+'% + '+(8-16*j/(n-1))+'px)">'+esc(mark+s.v)+'</span>'});
 wrap.innerHTML='<h2>'+esc(d.title)+'</h2><p class="mute">'+esc(d.env)+' &middot; '+esc(d.note)+'</p>'+
  '<div class="track"><input type="range" min="0" max="'+(n-1)+'" step="1" value="'+i+'" aria-label="'+esc(d.title)+'"><div class="ticks">'+ticks+'</div></div>'+
  '<div class="numbox">'+nums(d,i)+'</div><img alt="'+esc(d.title)+'" src="'+d.steps[i].img+'">';
 root.appendChild(wrap);
 const r=wrap.querySelector('input'),img=wrap.querySelector('img'),nb=wrap.querySelector('.numbox');
 const set=j=>{j=Math.max(0,Math.min(n-1,j));state[d.key]=j;r.value=j;img.src=d.steps[j].img;nb.innerHTML=nums(d,j);save(d.key,j);refresh()};
 r.addEventListener('input',()=>set(parseInt(r.value,10)));
 ['pointerdown','focus','touchstart','mouseenter'].forEach(ev=>r.addEventListener(ev,()=>preload(d),{passive:true}));
 r.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowDown'){e.preventDefault();set(state[d.key]-1)}else if(e.key==='ArrowRight'||e.key==='ArrowUp'){e.preventDefault();set(state[d.key]+1)}});
 if('IntersectionObserver' in window){const io=new IntersectionObserver(es=>{es.forEach(x=>{if(x.isIntersecting){preload(d);io.disconnect()}})},{rootMargin:'400px'});io.observe(wrap)}
});
const head=DATA.find(d=>d.key==='head');
function setDbl(v){dbl=v;const c=ALL.combo[v];document.getElementById('comboimg').src=c.img;
 document.getElementById('dbl0').setAttribute('aria-pressed',v?'false':'true');document.getElementById('dbl1').setAttribute('aria-pressed',v?'true':'false');
 document.getElementById('combonums').innerHTML='<table class="nums"><tr><td>picks</td><td>'+esc(JSON.stringify(ALL.rec))+(v?' + ALBO_APOS_DOUBLES=1':'')+'</td></tr><tr><td>gates</td><td>'+(c.fails.length?'<span class="bad">fails '+esc(c.fails.join('; '))+'</span>':'<span class="ok">all green (4 cuts)</span>')+'</td></tr></table>'+sttable(c.st,'curly',head.steps[head.shipped].st);
 try{localStorage.setItem('apos:dbl',String(v))}catch(e){}refresh()}
document.getElementById('dbl0').addEventListener('click',()=>setDbl(0));document.getElementById('dbl1').addEventListener('click',()=>setDbl(1));
let d0=0;try{d0=parseInt(localStorage.getItem('apos:dbl')||'0',10)||0}catch(e){}setDbl(d0);
refresh();
document.getElementById('copy').addEventListener('click',async()=>{const t=picks();const m=document.getElementById('copied');
 try{await navigator.clipboard.writeText(t);m.textContent='copied'}catch(e){const ta=document.getElementById('picks');ta.focus();ta.select();m.textContent='select and copy from the box at the foot of the page'}});
</script></body></html>"""


if __name__ == "__main__":
    main()
