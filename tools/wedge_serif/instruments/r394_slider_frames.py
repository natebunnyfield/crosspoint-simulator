#!/usr/bin/env python3
"""Round 394, the SLIDER page: one slider per independent thick/thin dial,
every step a real FreeType render, prerendered.

Owner 2026-09-26: *"present this in an interactive way so i can slide
between full range"*. The options page offered 3-5 arms per group; this
spans each dial's whole usable range, lightest sensible value through as
shipped to past the strong arm, so he can find the edge himself.

For every dial x step it:
  1. builds the dial's style at the 400 AND the 700 (the shipped env of
     build_env.sh plus that one variable; the shipped step builds nothing
     extra -- it IS the baseline);
  2. measures, against the shipped build: each affected letter's ink change
     on the OUTLINE (unhinted, r394_visibility.render), the share of pixels
     changed by more than 8 levels in the sentence block at 27 px and 54 px
     (FreeType, glyphs held at the shipped positions so spacing does not
     count), and the letter's thin stroke (p10 of the chamfer ridge, units,
     against the shipped build's family median -- r391 / r394_thin_map);
  3. gates it on both weights: cmp_touch (any touching pair or pair under
     the floor), cmp_contour_hairs --letters (exit), cmp_counter_dents (any
     change from the shipped set), cmp_aldine_glitch --all (any finding the
     shipped build does not have -- e.g. the Bold Italic st pinching when the
     s's contrast drops), approved.py (the approved g's). A failing step is
     KEPT and flagged, so the edge is visible;
  4. writes ONE composite PNG per step (sentence at 27 px shown 2x nearest,
     the same at 54 px native, the key words at 27 px x3 as a DIFFERENCE
     against shipped, and a 160 px overlay of the affected letters), padded
     to the slider's tallest frame so a step swaps in place;
  5. writes index.html with the data inlined.

    python3 instruments/r394_slider_frames.py --work WORKDIR --out OUTDIR [--only A_bowl,...]

OUTDIR holds only index.html and frames/ (the publishable page); builds,
logs and measurements live in WORKDIR. Nothing in the font sources is read
from anywhere but the environment, so defaults are untouched.
"""
import argparse, concurrent.futures as cf, html, json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # tools/wedge_serif
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "instruments"))
W = 700
UI = "/System/Library/Fonts/Supplemental/Arial.ttf"

ENV = {
    "Regular": dict(FJORD_STEM="66.9", FJORD_CONTRAST="0.892"),
    "Italic": dict(ALBO_ITALIC="aldine", FJORD_STEM="66.9", FJORD_CONTRAST="0.80", FJORD_WIDTH="95", FJORD_SLANT="13"),
    "Bold": dict(FJORD_STEM="116", FJORD_SLANT="0", FJORD_CONTRAST="0.80", FJORD_WIDTH="95", FJORD_CUT="0"),
    "BoldItalic": dict(ALBO_ITALIC="aldine", FJORD_STEM="116", FJORD_SLANT="13", FJORD_CONTRAST="0.80", FJORD_WIDTH="95", FJORD_CUT="0"),
}
CUTS = {"roman": ("Regular", "Bold"), "italic": ("Italic", "BoldItalic")}

TEXT = {
 "A": "A quiet bride dipped a pale quill in dark ink and paced the brick quad, probing deep books for proof that a dappled pup had bounded past the pond. quadruped bibliophile dependable propaganda",
 "B": "Sixty yellow yachts sway lazily as sly boys say yes to seven easy stories; yesterday the systems seemed noisy, yet everyone stayed busy. mysteriously physiology sympathy",
 "C": "In the moonlit hamlet the ninth man hummed a haunting hymn, and nine hungry monks came home to the humming mill in the mountain mist. monochrome humanism phenomenon",
 "D": "Young Kiki kept six waxed kayaks by the dark lake; York's expert took the next taxi to fix the knotted boxes. Yes, Kenya's yak market thrived. breakneck knickknack",
 "E": "Every evening the eleven needle-makers sewed seven green sheets, then left the keen eyes of the settlement free to see the frozen trees. effervescence excellence",
 "F": "In 1838 the 36 ships left port; by 1863, 83 of them had sailed 3,688 miles, and on 6 March 1886 the log read 38.6 knots at 8:36. 1838 1863 3,688 663 388",
}

# key: (group, title, env var, style, steps, shipped step value, recommended,
#       letters, key words, note, value->env formatter or None)
DIALS = [
 ("A_bowl", "A", "Italic bowls q p d b: hairline floor (units)", "ALBO_ALD_BOWL_HAIR", "italic",
  ["0", "22", "26", "30", "34", "38", "42", "46", "50"], "0", "34", "qpdb", "quad bid",
  "0 = the ring tables as drawn. A floor cannot go lighter than shipped. Lifts only the crown/arm hairline; the g is never touched.", None),
 ("A_a", "A", "Italic a: hairline floor (units)", "ALBO_ALD_A_HAIR", "italic",
  ["0", "22", "26", "30", "34", "38", "42", "46", "50"], "0", "0", "a", "a pale ant",
  "Moves the a's contrast, which is an owner ruling (CON_A, 2026-09-15/16).", None),
 ("B_s", "B", "Italic s: contrast target (thick:thin)", "ALBO_ALD_S_PEN_CON", "italic",
  ["9.0", "8.0", "7.0", "6.5", "6.0", "5.5", "5.0", "4.5", "4.0", "3.5", "3.0"], "7.0", "5.5", "s", "sly stays",
  "Lower = heavier hairlines. 7:1 came with the 2026-09-17 s pass (\"up its contrast\").", None),
 ("B_y", "B", "Italic y: tail hairline (units)", "ALBO_ALD_Y_TAIL_W", "italic",
  ["18", "22", "26", "30", "34", "38", "42", "46", "50"], "26", "30", "y", "yes yearly",
  "26 is Cancelleresca's hairline (owner, 2026-09-16: match the swoop of cancell).", None),
 ("C_join", "C", "Roman n h m: join start (x the pen)", "ALBO_ROM_N_JOIN_TAPER", "roman",
  ["0.10", "0.16", "0.22", "0.26", "0.30", "0.40", "0.55", "0.75", "1.00"], "0.22", "0.22", "nhm", "hymn man",
  "Round 232 lightened these joins on purpose. The join starts inside the stem, so even 1.00 moves the n's ink by ~0.05%.", None),
 ("D_x", "D", "Roman x: light diagonal (x the pen)", "ALBO_ROM_LCX_THIN", "roman",
  ["0.56", "0.60", "0.66", "0.72", "0.80", "0.90", "1.00", "1.10", "1.20"], "0.72", "1.00", "x", "six taxi",
  "0.72 compounds with the pen's own thin (round 224's X finding; the capital X ships 0.90).", None),
 ("D_k", "D", "Roman k: arm weight", "ALBO_ROM_K_ARM", "roman",
  ["1.10", "1.25", "1.40", "1.55", "1.70", "1.85", "2.00", "2.25", "2.50", "2.75"], "1.40", "2.50", "k", "kayak kick",
  "1.40 is round 92's; the owner asked for more arm weight on 2026-09-13.", None),
 ("D_Y", "D", "Roman capital Y: light arm (x the pen)", "ALBO_ROM_Y_THIN", "roman",
  ["0.56", "0.60", "0.66", "0.72", "0.80", "0.90", "1.00", "1.10", "1.20"], "0.72", "1.00", "Y", "York Yes",
  "No ruling on this arm; 0.90 is the capital X's value.", None),
 ("E_bar", "E", "Roman e: bar floor (x the stem, 400 only)", "ALBO_ROM_E_BAR_FLOOR", "roman",
  ["0.30", "0.35", "0.40", "0.45", "0.50", "0.55", "0.60", "0.65", "0.70"], "0.35", "0.45", "e", "eleven trees",
  "At the 400 the bar sits on this floor. The Bold is not affected (round 287's heavy bar).", None),
 ("E_exit", "E", "Roman e: exit end width (x the stroke)", "ALBO_E_TAIL_R", "roman",
  ["0.25", "0.30", "0.35", "0.40", "0.45", "0.55", "0.65", "0.75", "0.85"], "0.40", "0.40", "e", "eleven trees",
  "Heavier goes against the owner's two asks to lighten the e's tail (round 94; 2026-09-14).", None),
 ("F_3", "F", "Roman 3: hairline floor (x the stem)", "ALBO_FIG3_FLOOR", "roman",
  ["0", "0.25", "0.30", "0.33", "0.36", "0.40", "0.45", "0.50", "0.55", "0.60"], "0", "0.40", "3", "1833 3,3",
  "0 = the pen alone. A floor cannot go lighter than shipped.", None),
 ("F_8", "F", "Roman 8: nib thin (x the stem)", "ALBO_8_NIB", "roman",
  ["0.08", "0.11", "0.15", "0.19", "0.22", "0.26", "0.30", "0.35", "0.40", "0.45", "0.50"], "0.15", "0.15", "8", "1888 8,8",
  "0.15 is round 373/374's \"cut deeper wins\". Roman builds only.", lambda v: f"1.03,{v},0"),
 ("F_6", "F", "Italic 6: tail end (x its width)", "ALBO_ALD_SIX_TAIL_END", "italic",
  ["0.06", "0.12", "0.20", "0.30", "0.45", "0.60", "0.75", "0.90", "1.00"], "0.12", "0.60", "6", "1886 6,6",
  "0.12 is the shipped run-out to a point (the dial's 0).", None),
]
D = {d[0]: dict(zip(("key", "group", "title", "env", "style", "steps", "shipped", "rec", "letters", "words", "note", "fmt"), d)) for d in DIALS}


def env_for(dial, v):
    if v == dial["shipped"]:
        return {}
    return {dial["env"]: dial["fmt"](v) if dial["fmt"] else v}


def build(outdir, cut, extra):
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, f"Albo-{cut}.ttf")
    if os.path.exists(p): return p
    e = dict(os.environ); e.update(ENV[cut]); e.update(extra); e["PYTHON_GIL"] = "0"
    r = subprocess.run([sys.executable, "-m", "outlines.build", outdir, "--style", cut], cwd=HERE, env=e,
                       capture_output=True, text=True)
    if r.returncode: raise SystemExit(f"build failed {outdir} {cut}\n{r.stderr[-800:]}")
    return p


def run(cmd):
    r = subprocess.run(cmd, cwd=HERE, env=dict(os.environ, PYTHON_GIL="0"), capture_output=True, text=True)
    return r.returncode, r.stdout


def gate_sig(ttf):
    """The set of findings of one cut, as comparable strings."""
    out = {}
    rc, t = run([sys.executable, "cmp_touch.py", ttf])
    m = re.search(r"(\d+) pair\(s\) TOUCHING, (\d+) below", t)
    out["touch"] = (int(m.group(1)), int(m.group(2))) if m else ("?",)
    rc, _ = run([sys.executable, "cmp_contour_hairs.py", ttf, "--letters"]); out["hairs"] = rc
    rc, t = run([sys.executable, "cmp_counter_dents.py", ttf])
    out["dents"] = t.strip().splitlines()[-1].split(":", 1)[-1].strip() if t.strip() else ""
    rc, t = run([sys.executable, "cmp_aldine_glitch.py", "--ttf", ttf, "--all"])
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
    if sig["dents"] != base["dents"]: f.append("dents")
    new = sorted(set(sig["glitch"]) - set(base["glitch"]))
    if new: f.append("glitch " + ", ".join(new))
    return f


# ------------------------------------------------------------------ rendering
def wrap(font, text, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if font.getlength(t) <= width or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def fixed_draw(d, path, ref, text, px, x0, base, fill):
    f = ImageFont.truetype(path, px); fr = ImageFont.truetype(ref, px, layout_engine=ImageFont.Layout.RAQM)
    for i, ch in enumerate(text):
        if ch != " ": d.text((x0 + fr.getlength(text[:i]), base), ch, font=f, fill=fill, anchor="ls")


def block(path, text, px, width, ref=None):
    """ref=None: the real set line (RAQM, the arm's own spacing). ref given:
    glyph by glyph at the ref font's positions (shape only)."""
    fr = ImageFont.truetype(ref or path, px, layout_engine=ImageFont.Layout.RAQM)
    pad = max(4, px // 4); lines = wrap(fr, text, width - 2 * pad)
    lh = int(round(px * 1.35)); asc = int(round(px * 0.95))
    im = Image.new("L", (width, lh * len(lines) + int(px * 0.5)), 255); d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        if ref: fixed_draw(d, path, ref, ln, px, pad, asc + i * lh, 0)
        else: d.text((pad, asc + i * lh), ln, font=ImageFont.truetype(path, px, layout_engine=ImageFont.Layout.RAQM), fill=0, anchor="ls")
    return im


def diffimg(ca, cx):
    add = np.clip((cx - ca) * 4, 0, 1); rem = np.clip((ca - cx) * 4, 0, 1)
    both = np.minimum(ca, cx) * (1 - np.maximum(add, rem))
    r = 255 - both * 140 - add * 255; g = 255 - both * 140 - add * 150 - rem * 255; b = 255 - both * 140 - rem * 255
    return Image.fromarray(np.stack([r, g, b], -1).clip(0, 255).astype(np.uint8))


def cov_fixed(path, ref, text, px, w, h, base):
    im = Image.new("L", (w, h), 0); fixed_draw(ImageDraw.Draw(im), path, ref, text, px, 6, base, 255)
    return np.asarray(im, dtype=float) / 255.0


def slot(path, ch, px, sw, h, base):
    im = Image.new("L", (sw, h), 0)
    ImageDraw.Draw(im).text((int(px * 0.08), base), ch, font=ImageFont.truetype(path, px), fill=255, anchor="ls")
    return np.asarray(im, dtype=float) / 255.0


def label(text, size=17, fill=(70, 70, 70), bg=(255, 255, 255), h=28):
    im = Image.new("RGB", (W, h), bg); ImageDraw.Draw(im).text((6, h - 8), text, font=ImageFont.truetype(UI, size), fill=fill, anchor="ls")
    return im


def frame(dial, v, ttf, ref):
    parts = [label(f"{dial['title']}  =  {v}" + ("   [as shipped]" if v == dial["shipped"] else "")
                   + ("   [recommended]" if v == dial["rec"] else ""), 19, (0, 0, 0), (235, 235, 230), 34)]
    text = TEXT[dial["group"]]
    parts.append(label("27 px, shown 2x nearest-neighbor"))
    s27 = block(ttf, text, 27, W // 2); parts.append(s27.resize((W, s27.height * 2), Image.NEAREST).convert("RGB"))
    parts.append(label("54 px, native (the phone's 2x)"))
    parts.append(block(ttf, text, 54, W).convert("RGB"))
    parts.append(label("difference against as shipped, 27 px x3: gray same, blue added, red removed"))
    fa = ImageFont.truetype(ref, 27, layout_engine=ImageFont.Layout.RAQM)
    w = int(fa.getlength(dial["words"])) + 14; h = 42
    dimg = diffimg(cov_fixed(ref, ref, dial["words"], 27, w, h, 31), cov_fixed(ttf, ref, dial["words"], 27, w, h, 31)).resize((w * 3, h * 3), Image.NEAREST)
    row = Image.new("RGB", (W, h * 3), "white"); row.paste(dimg.crop((0, 0, min(W, dimg.width), h * 3)), (0, 0)); parts.append(row)
    px = 220; hh = int(px * 1.12); base = int(px * 0.82)
    parts.append(label(f"{px} px close-up: this step filled | overlaid on shipped (blue added, red line = shipped outline)"))
    sw = max(int(ImageFont.truetype(ref, px).getlength(ch) + px * 0.22) for ch in dial["letters"])
    cells = []
    for ch in dial["letters"]:
        ca = slot(ref, ch, px, sw, hh, base); cx = slot(ttf, ch, px, sw, hh, base)
        cells.append(Image.fromarray((255 - cx * 255).astype(np.uint8)).convert("RGB"))
        ma = ca > 0.5; er = ma.copy()
        for _ in range(2): er = er & np.roll(er, 1, 0) & np.roll(er, -1, 0) & np.roll(er, 1, 1) & np.roll(er, -1, 1)
        ov = np.array(diffimg(ca, cx), dtype=float); ov[ma & ~er] = (200, 0, 0)
        cells.append(Image.fromarray(ov.astype(np.uint8)))
    per = max(2, (W // sw) // 2 * 2)
    for k in range(0, len(cells), per):
        row = Image.new("RGB", (W, hh), "white")
        for i, c in enumerate(cells[k:k + per]): row.paste(c, (i * sw, 0))
        parts.append(row)
    out = Image.new("RGB", (W, sum(p.height for p in parts)), "white"); y = 0
    for p in parts: out.paste(p, (0, y)); y += p.height
    return out


# ------------------------------------------------------------------ measuring
def measure(dial, v, ttf, ref, fam_med, style):
    import r394_visibility as V
    import cmp_weight_survey as WS
    from r391_thick_thin import fam
    m = {"letters": {}}
    for ch in dial["letters"]:
        A = V.render(ref, ch, 200, 260, 330, 20, 250); X = V.render(ttf, ch, 200, 260, 330, 20, 250)
        r = WS.measure(ttf, ch, 13.0 if style == "italic" else 0.0)
        m["letters"][ch] = dict(ink=100.0 * (X.sum() - A.sum()) / A.sum(), thin=r["thin"],
                                dthin=100.0 * (r["thin"] / fam_med[fam(ch)] - 1))
    text = TEXT[dial["group"]]
    for key, px, width in (("px27", 27, W // 2), ("px54", 54, W)):
        a = np.asarray(block(ref, text, px, width, ref=ref), dtype=int)
        x = np.asarray(block(ttf, text, px, width, ref=ref), dtype=int)
        m[key] = 100.0 * (np.abs(a - x) > 8).mean()
    return m


def job_measure(args):
    key, v, ttf, ref, fam_med, style, frame_path = args
    dial = D[key]
    m = measure(dial, v, ttf, ref, fam_med, style)
    frame(dial, v, ttf, ref).save(frame_path)
    return key, v, m


def job_gate(args):
    key, v, paths = args
    return key, v, {cut: gate_sig(p) for cut, p in paths.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=""); ap.add_argument("-j", type=int, default=8)
    a = ap.parse_args()
    keys = [k for k in D if not a.only or k in a.only.split(",")]
    os.makedirs(os.path.join(a.out, "frames"), exist_ok=True)
    bdir = os.path.join(a.work, "build")
    base = os.path.join(bdir, "shipped")
    # 1. builds
    jobs = [(base, c, {}) for c in ENV]
    for k in keys:
        for i, v in enumerate(D[k]["steps"]):
            if v == D[k]["shipped"]: continue
            for c in CUTS[D[k]["style"]]:
                jobs.append((os.path.join(bdir, f"{k}_{i}"), c, env_for(D[k], v)))
    with cf.ThreadPoolExecutor(a.j) as ex: list(ex.map(lambda j: build(*j), jobs))
    print("built", len(jobs), flush=True)

    def path(k, i, cut):
        v = D[k]["steps"][i]
        return os.path.join(base if v == D[k]["shipped"] else os.path.join(bdir, f"{k}_{i}"), f"Albo-{cut}.ttf")

    # 2. family medians of the SHIPPED build (fixed yardstick, albo-method 1f)
    wsj = os.path.join(a.work, "ws400.json")
    if not os.path.exists(wsj):
        run([sys.executable, "cmp_weight_survey.py", "--roman", f"{base}/Albo-Regular.ttf",
             "--italic", f"{base}/Albo-Italic.ttf", "--json", wsj])
    from r391_thick_thin import fam
    ws = json.load(open(wsj)); med = {}
    for style, groups in ws.items():
        rows = [r for g in groups.values() for r in g]; fams = {}
        for r in rows: fams.setdefault(fam(r["ch"]), []).append(r["thin"])
        med[style] = {f: float(np.median(t)) for f, t in fams.items()}

    # 3. gates (baseline first)
    base_sig = {c: gate_sig(os.path.join(base, f"Albo-{c}.ttf")) for c in ENV}
    gjobs = [(k, v, {c: path(k, i, c) for c in CUTS[D[k]["style"]]})
             for k in keys for i, v in enumerate(D[k]["steps"]) if v != D[k]["shipped"]]
    gates = {}
    with cf.ProcessPoolExecutor(a.j) as ex:
        for k, v, sig in ex.map(job_gate, gjobs):
            f = []
            for c, s in sig.items():
                f += [f"{c}: {x}" for x in fails(s, base_sig[c])]
            gates[(k, v)] = f
    # approved g's, on the 400s (the other style from the shipped build)
    for k in keys:
        for i, v in enumerate(D[k]["steps"]):
            if v == D[k]["shipped"]: continue
            reg = path(k, i, "Regular") if D[k]["style"] == "roman" else f"{base}/Albo-Regular.ttf"
            it = path(k, i, "Italic") if D[k]["style"] == "italic" else f"{base}/Albo-Italic.ttf"
            rc, _ = run([sys.executable, "approved.py", "--check", "--regular", reg, "--italic", it])
            if rc: gates[(k, v)].append("approved g changed")
    print("gated", flush=True)

    # 4. measure + frames
    mjobs = []
    for k in keys:
        st = D[k]["style"]; cut = CUTS[st][0]
        for i, v in enumerate(D[k]["steps"]):
            mjobs.append((k, v, path(k, i, cut), f"{base}/Albo-{cut}.ttf", med[st], st,
                          os.path.join(a.out, "frames", f"{k}_{i:02d}.png")))
    meas = {}
    with cf.ProcessPoolExecutor(a.j) as ex:
        for k, v, m in ex.map(job_measure, mjobs):
            meas[(k, v)] = m
    # pad every slider's frames to its tallest, so a step swaps in place
    for k in keys:
        fr = [os.path.join(a.out, "frames", f"{k}_{i:02d}.png") for i in range(len(D[k]["steps"]))]
        H = max(Image.open(p).height for p in fr)
        for p in fr:
            im = Image.open(p)
            if im.height < H:
                o = Image.new("RGB", (W, H), "white"); o.paste(im, (0, 0)); o.save(p, optimize=True)
            else:
                im.save(p, optimize=True)
    data = []
    for k in keys:
        d = D[k]; steps = []
        for i, v in enumerate(d["steps"]):
            m = meas[(k, v)]
            steps.append(dict(v=v, env=(d["fmt"](v) if d["fmt"] else v), img=f"frames/{k}_{i:02d}.png",
                              px27=round(m["px27"], 2), px54=round(m["px54"], 2),
                              letters={c: {kk: round(x, 1) for kk, x in r.items()} for c, r in m["letters"].items()},
                              fails=gates.get((k, v), [])))
        data.append(dict(key=k, group=d["group"], title=d["title"], env=d["env"], note=d["note"],
                         style=d["style"], shipped=d["steps"].index(d["shipped"]), rec=d["steps"].index(d["rec"]),
                         shipped_env=(d["fmt"](d["shipped"]) if d["fmt"] else d["shipped"]), steps=steps))
    json.dump(data, open(os.path.join(a.work, "slider_data.json"), "w"), indent=1)
    open(os.path.join(a.out, "index.html"), "w").write(page(data))
    print("wrote", a.out)


GROUPS = {"A": "Italic bowls", "B": "Italic s and y", "C": "Roman n h m join", "D": "Roman x, k and Y",
          "E": "Roman e", "F": "Figures 3, 8 and italic 6"}


def page(data):
    js = json.dumps(data)
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thick Thin Sliders</title>
<style>
:root{--bg:#fbfbf9;--fg:#1d1d1b;--mute:#66645f;--rule:#dddad3;--card:#fff;--accent:#7a3b2e;--ship:#2d6a3e;--rec:#1f55b0;--bad:#b3261e}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161615;--fg:#e8e6e1;--mute:#a19e97;--rule:#3a3935;--card:#202020;--accent:#e0a090;--ship:#7fc795;--rec:#8fb4ff;--bad:#ff8a80}}
:root[data-theme="dark"]{--bg:#161615;--fg:#e8e6e1;--mute:#a19e97;--rule:#3a3935;--card:#202020;--accent:#e0a090;--ship:#7fc795;--rec:#8fb4ff;--bad:#ff8a80}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font:16px/1.45 -apple-system,system-ui,sans-serif;margin:0;padding:16px}
main{max-width:720px;margin:0 auto}
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
.nums{font-size:.85em;margin:.4em 0}.nums td{padding:1px 6px 1px 0;vertical-align:top}
.bad{color:var(--bad);font-weight:700}.ok{color:var(--ship)}
.val{font-weight:700}
button{font:inherit;padding:.5em 1em;border:1px solid var(--rule);background:var(--card);color:var(--fg);border-radius:6px}
textarea{width:100%;height:9em;font:12px/1.3 ui-monospace,monospace;background:var(--card);color:var(--fg);border:1px solid var(--rule)}
.bar{position:sticky;top:0;background:var(--bg);padding:.4em 0;z-index:2;border-bottom:1px solid var(--rule)}
</style></head><body><main>
<div class="bar"><button id="copy">Copy picks</button> <span id="copied" class="mute"></span></div>
<h1>Thick and thin, full range</h1>
<p>One slider per dial. Every step is a real render (FreeType, as the reader renders), prerendered: the sentence at 27&nbsp;px shown 2&times;, the same at 54&nbsp;px, the key words as a difference against as shipped, and a 160&nbsp;px close-up. <span style="color:var(--ship);font-weight:700">S</span> marks as shipped, <span style="color:var(--rec);font-weight:700">R</span> the recommended step. A step that fails a gate is still shown, flagged in red.</p>
<p class="mute">Numbers under each image, against as shipped: <b>ink</b> is the letter's ink change on its outline; <b>27/54 px</b> is the share of the sentence block's pixels that change (under about 1% at 54 px is below a pixel at reading size); <b>thin</b> is the letter's thin stroke in font units and its distance from its letter family (round 391 flagged under &minus;25%). Arrow keys step the focused slider; picks are remembered on this device.</p>
<div id="dials"></div>
<h2>Picks</h2>
<p class="mute">JSON of every slider's current value, keyed by its environment variable; <code>null</code> means as shipped (leave the variable unset). If the copy button cannot reach the clipboard, copy from here.</p>
<textarea id="picks" readonly></textarea>
</main>
<script>
const DATA = """ + js + """;
const GROUPS = """ + json.dumps(GROUPS) + """;
function load(k,d){try{const v=localStorage.getItem('tt394:'+k);return v===null?d:parseInt(v,10)}catch(e){return d}}
function save(k,v){try{localStorage.setItem('tt394:'+k,String(v))}catch(e){}}
const state={};const preloaded={};
function preload(d){if(preloaded[d.key])return;preloaded[d.key]=1;d.steps.forEach(s=>{const i=new Image();i.src=s.img})}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function nums(d,i){const s=d.steps[i];let h='<table class="nums">';
 h+='<tr><td>value</td><td><span class="val">'+esc(s.v)+'</span>'+(i===d.shipped?' <span class="ok">(as shipped)</span>':'')+(i===d.rec?' <span style="color:var(--rec)">(recommended)</span>':'')+'</td></tr>';
 h+='<tr><td>pixels changed</td><td>27 px '+s.px27.toFixed(2)+'% &nbsp; 54 px '+s.px54.toFixed(2)+'%'+(i!==d.shipped&&s.px54<1?' &mdash; <i>sub-pixel at reading size</i>':'')+'</td></tr>';
 for(const [c,r] of Object.entries(s.letters)){h+='<tr><td>'+esc(c)+'</td><td>ink '+(r.ink>=0?'+':'')+r.ink.toFixed(1)+'% &nbsp; thin '+r.thin.toFixed(1)+' units ('+(r.dthin>=0?'+':'')+r.dthin.toFixed(0)+'% vs family)</td></tr>'}
 h+='<tr><td>gates</td><td>'+(i===d.shipped?'<span class="ok">as shipped</span>':(s.fails.length?'<span class="bad">fails '+esc(s.fails.join('; '))+'</span>':'<span class="ok">all green</span>'))+'</td></tr>';
 return h+'</table>'}
function picks(){const o={};DATA.forEach(d=>{const j=state[d.key];o[d.env]=j===d.shipped?null:d.steps[j].env});return JSON.stringify(o,null,1)}
function refresh(){document.getElementById('picks').value=picks()}
let lastGroup='';const root=document.getElementById('dials');
DATA.forEach(d=>{
 if(d.group!==lastGroup){const h=document.createElement('h2');h.textContent=d.group+'. '+GROUPS[d.group];root.appendChild(h);lastGroup=d.group}
 const wrap=document.createElement('div');wrap.className='dial';
 const n=d.steps.length;let i=load(d.key,d.shipped);if(!(i>=0&&i<n))i=d.shipped;state[d.key]=i;
 let ticks='';d.steps.forEach((s,j)=>{const cls=j===d.shipped?'tick ship':(j===d.rec?'tick rec':'tick');const mark=(j===d.shipped?'S ':'')+(j===d.rec&&j!==d.shipped?'R ':'')+(j===d.rec&&j===d.shipped?'R ':'');
   ticks+='<span class="'+cls+'" style="left:calc('+(j/(n-1)*100)+'% + '+(8-16*j/(n-1))+'px)">'+esc(mark+s.v)+'</span>'});
 wrap.innerHTML='<h3>'+esc(d.title)+'</h3><p class="mute">'+esc(d.env)+' &middot; '+esc(d.note)+'</p>'+
  '<div class="track"><input type="range" min="0" max="'+(n-1)+'" step="1" value="'+i+'" aria-label="'+esc(d.title)+'"><div class="ticks">'+ticks+'</div></div>'+
  '<img alt="'+esc(d.title)+'" src="'+d.steps[i].img+'"><div class="numbox">'+nums(d,i)+'</div>';
 root.appendChild(wrap);
 const r=wrap.querySelector('input'),img=wrap.querySelector('img'),nb=wrap.querySelector('.numbox');
 const set=j=>{j=Math.max(0,Math.min(n-1,j));state[d.key]=j;r.value=j;img.src=d.steps[j].img;nb.innerHTML=nums(d,j);save(d.key,j);refresh()};
 r.addEventListener('input',()=>set(parseInt(r.value,10)));
 ['pointerdown','focus','touchstart','mouseenter'].forEach(ev=>r.addEventListener(ev,()=>preload(d),{passive:true}));
 r.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowDown'){e.preventDefault();set(state[d.key]-1)}else if(e.key==='ArrowRight'||e.key==='ArrowUp'){e.preventDefault();set(state[d.key]+1)}});
 if('IntersectionObserver' in window){const io=new IntersectionObserver(es=>{es.forEach(x=>{if(x.isIntersecting){preload(d);io.disconnect()}})},{rootMargin:'400px'});io.observe(wrap)}
});
refresh();
document.getElementById('copy').addEventListener('click',async()=>{const t=picks();const m=document.getElementById('copied');
 try{await navigator.clipboard.writeText(t);m.textContent='copied'}catch(e){const ta=document.getElementById('picks');ta.focus();ta.select();m.textContent='select and copy from the box at the foot of the page'}});
</script></body></html>"""


if __name__ == "__main__":
    main()
