"""r_variants.py -- live-builder glyphs per dial variant, side by side, one row (round 448).

    python3 instruments/r_variants.py OUT.png it|bi CHARS "LABEL|ALBO_ALD_R_TF=0.20 ..." "Coel|REF:refs/coelacanth-italic.otf" ...

Each variant runs the builder in its own process with its dials (they are read at import), at one
x-height (429 units, SC px per unit, default 0.9). A "REF:path" variant renders a reference font at
the same x-height. Every variant prints its [r-term] debug line (ALBO_ALD_R_DEBUG): READ IT. On
2026-09-30 five variants were laddered with ALBO_ALD_R_TX / _TY, which are not dials (the drawn
terminal's `_rt` prefixes "T": the tip is ALBO_ALD_R_TTX / _TTY), and the tip never moved; the
debug line is what showed it. docs/albo-round-448-2026-09-30.md.
"""
if __name__ == "__main__" and len(__import__("sys").argv) > 1 and __import__("sys").argv[1] == "--dump":
    import sys, os, json
    sys.path.insert(0, os.getcwd())
    from outlines import build
    out = {}
    for ch in sys.argv[2]:
        g = build.draw(ch)
        polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
        out[ch] = [[list(P.exterior.coords), [list(h.coords) for h in P.interiors]] for P in polys]
    print(json.dumps(out)); raise SystemExit(0)
import sys, os, json, subprocess
from PIL import Image, ImageDraw, ImageFont
out, style, chars = sys.argv[1], sys.argv[2], sys.argv[3]
specs = sys.argv[4:]
ENV = {"it": "ALBO_ITALIC=aldine FJORD_STEM=66.9 FJORD_CONTRAST=0.80 FJORD_WIDTH=95 FJORD_SLANT=13",
       "bi": "ALBO_ITALIC=aldine FJORD_STEM=116 FJORD_SLANT=13 FJORD_CONTRAST=0.80 FJORD_WIDTH=95 FJORD_CUT=0"}[style]
SC = float(os.environ.get("SC", "0.9")); TOP = 560; BOT = -40
LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
here = os.path.dirname(os.path.abspath(__file__))
cells = []
import freetype, numpy as np
def ref_cell(lab, path):
    f = freetype.Face(path); f.set_pixel_sizes(0, 200); f.load_char('x', freetype.FT_LOAD_NO_HINTING)
    xh = f.glyph.metrics.height / 64; f.set_pixel_sizes(0, int(round(200 * 429 * SC / xh)))
    gl = []
    for ch in chars:
        f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width]; gl.append((a, f.glyph.bitmap_left, f.glyph.bitmap_top))
    W = sum(a.shape[1] + int(50 * SC) for a, _, _ in gl) + 30; H = int((TOP - BOT) * SC) + 50
    im = Image.new("L", (W, H), 250); d = ImageDraw.Draw(im); base = int(TOP * SC) + 40
    for yy in (base, base - 429 * SC): d.line([(0, yy), (W, yy)], fill=205)
    x0 = 15
    for a, l, t in gl:
        im.paste(Image.fromarray(255 - a), (x0, base - t), Image.fromarray(a)); x0 += a.shape[1] + int(50 * SC)
    d.text((8, 4), lab, font=LAB, fill=0); return im
for sp in specs:
    lab, _, ev = sp.partition("|")
    if ev.startswith("REF:"):
        cells.append(ref_cell(lab, ev[4:])); continue
    env = dict(os.environ); env["PYTHON_GIL"] = "0"; env["ALBO_ALD_R_DEBUG"] = "1"
    for kv in (ENV + " " + ev).split():
        k, v = kv.split("=", 1); env[k] = v
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "--dump", chars], env=env, capture_output=True, text=True,
                       cwd=os.path.expanduser("~/src/crosspoint-simulator/tools/wedge_serif"))
    if r.returncode: print(r.stderr[-2000:]); sys.exit(1)
    lines = r.stdout.strip().splitlines(); data = json.loads(lines[-1])
    for ln in lines[:-1]:
        if ln.startswith("[r-term]"): print(f"{lab:6s} {ln}")
    xs = [x for ch in chars for P in data[ch] for x, _ in P[0]]
    widths = []
    for ch in chars:
        cx = [x for P in data[ch] for x, _ in P[0]]; widths.append((min(cx), max(cx)))
    W = int(sum((b - a + 50) * SC for a, b in widths)) + 30
    H = int((TOP - BOT) * SC) + 50
    im = Image.new("L", (W, H), 250); d = ImageDraw.Draw(im)
    base = int(TOP * SC) + 40
    for yy in (base, base - 429 * SC): d.line([(0, yy), (W, yy)], fill=205)
    x0 = 15
    for ch, (a, b) in zip(chars, widths):
        for ext, holes in data[ch]:
            d.polygon([(x0 + (x - a) * SC, base - y * SC) for x, y in ext], fill=0)
            for h in holes: d.polygon([(x0 + (x - a) * SC, base - y * SC) for x, y in h], fill=250)
        x0 += int((b - a + 50) * SC)
    d.text((8, 4), lab, font=LAB, fill=0)
    cells.append(im)
Wt = sum(c.width for c in cells) + 10 * (len(cells) - 1); Ht = max(c.height for c in cells)
o = Image.new("L", (Wt, Ht), 255); x = 0
for c in cells: o.paste(c, (x, 0)); x += c.width + 10
o.save(out); print(out, o.size)
