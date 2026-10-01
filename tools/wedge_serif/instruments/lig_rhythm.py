"""lig_rhythm.py -- does each LIGATURE keep the word's stem rhythm? Round 456 (2026-10-01), owner:
*"don't do ligatures if they aren't aligned with stem rhythm of words"*.

    venv/bin/python instruments/lig_rhythm.py FONT ...             # per ligature
    venv/bin/python instruments/lig_rhythm.py --sheet OUT.png FONT  # the stems drawn, ligated over unligated
    PYTHON_GIL=0 python3 instruments/lig_rhythm.py --check FONT ...  # the gate: exit 1 on a ligature out of rhythm

The rhythm a word has without the ligature is the font's own: every letter at its fitted bearings
and kerning (B2, fitted to the owner's bench). So a ligature is IN RHYTHM when its stems stand
where the separate letters' stems stand, and the letter after it starts where it would have.
Measured on HarfBuzz shapings of the same text with `liga` on and off, rasterized at 1 px per
unit: the stems are the ink runs in the x-height's middle band (0.35-0.65 of it) -- the f's
stem, the i's, the l's -- matched left to right, each as its run's centre. Per sequence:
  stems    each stem's x with the ligature minus without, units (+ = right)
  after    the advance with the ligature minus without: how far everything after it moves
Words: the same on carrier words from the owner's books, every stem in the word.
"""
import sys, os
import numpy as np
try:
    import freetype, uharfbuzz as hb
except ImportError:          # the build python: --check needs neither
    freetype = hb = None

SEQS = ["ff", "fi", "fl", "ffi", "ffl"]
WORDS = ["first", "find", "office", "different", "fly", "flat", "affect", "offer", "baffle", "shuffle", "life", "field"]


class Font:
    def __init__(self, path):
        self.path = path
        self.f = freetype.Face(path); self.upm = self.f.units_per_EM; self.f.set_pixel_sizes(0, self.upm)
        self.hbf = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        from fontTools.ttLib import TTFont
        t = TTFont(path); self.xh = t["OS/2"].sxHeight or 0.45 * self.upm

    def shape(self, s, liga):
        buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
        hb.shape(self.hbf, buf, {"kern": True, "liga": liga, "clig": liga})
        x = 0; out = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            out.append((info.codepoint, x + pos.x_offset)); x += pos.x_advance
        return out, x

    def raster(self, s, liga):
        glyphs, adv = self.shape(s, liga)
        parts = []
        for g, x in glyphs:
            self.f.load_glyph(g, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
            b = self.f.glyph.bitmap
            a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] >= 128 if b.rows else np.zeros((0, 0), bool)
            parts.append((a, int(round(x)) + self.f.glyph.bitmap_left, self.f.glyph.bitmap_top))
        H, base = int(self.upm * 1.4), int(self.upm * 1.05); W = adv + self.upm
        c = np.zeros((H, W), bool)
        for a, l, t in parts:
            if not a.size: continue
            y0 = base - t; x0 = l + 50
            c[max(0, y0):y0 + a.shape[0], max(0, x0):x0 + a.shape[1]] |= a[max(0, -y0):, max(0, -x0):][:H - max(0, y0), :W - max(0, x0)]
        return c, base, adv, len(glyphs)

    def stems(self, s, liga):
        """Stem centres (x, units from the text origin) in the x-height's middle band, and the advance."""
        c, base, adv, n = self.raster(s, liga)
        rows = range(int(base - 0.65 * self.xh), int(base - 0.35 * self.xh))
        cols = c[list(rows)].sum(0) >= 0.9 * len(rows)         # a column inked through the whole band: a stem
        xs = np.nonzero(cols)[0]
        if not xs.size: return [], adv, n
        runs = np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1)
        return [float(r.mean()) - 50 for r in runs], adv, n


def report(path):
    F = Font(path); print(os.path.basename(path))
    for s in SEQS:
        off, a0, n0 = F.stems(s, False); on, a1, n1 = F.stems(s, True)
        lig = "LIGATES" if n1 < n0 else "does not ligate"
        d = [round(b - a) for a, b in zip(off, on)] if len(off) == len(on) else f"stem count {len(off)} -> {len(on)}"
        print(f"  {s:4s} {lig:15s} stems off {[round(x) for x in off]}  on {[round(x) for x in on]}  shift {d}  after {a1 - a0:+d}")
    for w in WORDS:
        off, a0, n0 = F.stems(w, False); on, a1, n1 = F.stems(w, True)
        if n1 == n0: continue
        if len(off) == len(on):
            d = [round(b - a) for a, b in zip(off, on)]
            print(f"  {w:10s} stem shifts {d}  (max {max(abs(v) for v in d)})")
        else:
            print(f"  {w:10s} stem count {len(off)} -> {len(on)}")


def sheet(out, path):
    from PIL import Image, ImageDraw, ImageFont
    F = Font(path); lab = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    rows = []
    for w in SEQS + ["office", "different", "affect", "baffle", "fly"]:
        for liga in (False, True):
            c, base, adv, n = F.raster(w, liga)
            st, _, _ = F.stems(w, liga)
            img = np.full(c.shape + (3,), 250, np.uint8); img[c] = (30, 30, 30)
            im = Image.fromarray(img); d = ImageDraw.Draw(im)
            for x in st:
                X = x + 50; d.line([(X, base - 1.2 * F.xh), (X, base + 0.15 * F.xh)], fill=(220, 40, 30) if liga else (40, 110, 230), width=4)
            d.text((10, 10), f"{w} {'ligature' if liga else 'separate'}", fill=(30, 30, 30), font=lab)
            im = im.crop((0, int(base - 1.5 * F.xh), min(im.width, int(adv + 150)), int(base + 0.4 * F.xh)))
            rows.append(im.resize((im.width // 2, im.height // 2), Image.NEAREST))
    W = max(r.width for r in rows); H = sum(r.height for r in rows)
    o = Image.new("RGB", (W, H), (250, 250, 250)); y = 0
    for r in rows: o.paste(r, (0, y)); y += r.height
    o.save(out); print(out, o.size)


# THE GATE (`--check`, gates.sh `ligrhythm.<style>`): runs on the BUILD python (PIL's raqm layout,
# no uharfbuzz/scipy). THE RHYTHM is the median of the face's own between-letter stem intervals over
# plain stem letters (the last stem of the first letter to the first of the second, in il li ii ll
# ni in ln nl hi ih mi im ui iu lu ul); a substituted ligature keeps it when every stem interval
# INSIDE it (f to f, f to i, f to l) lies within TOL of that median. TOL = 10 units, the owner's own
# re-ask repeatability (10.83, docs/local-ai-spacing-options-2026-09-26.md).
RHYTHM_PAIRS = ["il", "li", "ii", "ll", "ni", "in", "ln", "nl", "hi", "ih", "mi", "im", "ui", "iu", "lu", "ul"]
STEM_COUNT = {"i": 1, "l": 1, "n": 2, "h": 2, "m": 3, "u": 2}
TOL = 10


def pil_stems(path, s, liga, xh, upm):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(path, upm, layout_engine=ImageFont.Layout.RAQM)
    W, H, ox, base = int(upm * (len(s) + 2)), int(upm * 1.6), 50, int(upm * 1.1)
    im = Image.new("L", (W, H), 255)
    ImageDraw.Draw(im).text((ox, base), s, font=f, fill=0, anchor="ls",
                            features=(["liga"] if liga else ["-liga", "-clig"]))
    a = np.asarray(im) < 128
    rows = list(range(int(base - 0.65 * xh), int(base - 0.35 * xh)))
    xs = np.nonzero(a[rows].sum(0) >= 0.9 * len(rows))[0]
    if not xs.size: return []
    return [float(r.mean()) - ox for r in np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1)]


def substituted(path):
    from fontTools.ttLib import TTFont
    t = TTFont(path); rev = {g: chr(c) for c, g in t.getBestCmap().items()}
    out = []
    if "GSUB" in t:
        g = t["GSUB"].table; idx = set()
        for fr in g.FeatureList.FeatureRecord:
            if fr.FeatureTag == "liga": idx.update(fr.Feature.LookupListIndex)
        for i in idx:
            for st in g.LookupList.Lookup[i].SubTable:
                for first, ls in getattr(st, "ligatures", {}).items():
                    for lg in ls:
                        seq = rev.get(first, "") + "".join(rev.get(c, "") for c in lg.Component)
                        if len(seq) == 1 + len(lg.Component): out.append(seq)
    return sorted(set(out), key=lambda q: (len(q), q)), t["OS/2"].sxHeight or 450, t["head"].unitsPerEm


def check(path):
    seqs, xh, upm = substituted(path)
    iv = []
    for p in RHYTHM_PAIRS:
        st = pil_stems(path, p, False, xh, upm); k = STEM_COUNT[p[0]]
        if len(st) == STEM_COUNT[p[0]] + STEM_COUNT[p[1]]: iv.append(st[k] - st[k - 1])
    med = float(np.median(iv))
    bad = []
    for q in seqs:
        st = pil_stems(path, q, True, xh, upm)
        gaps = [b - a for a, b in zip(st, st[1:])]
        off = [round(g - med) for g in gaps]
        ok = len(st) == len(q) and all(abs(o) <= TOL for o in off)
        print(f"  {q:4s} stem intervals {[round(g) for g in gaps]} vs rhythm {med:.0f} -> {off}  {'in rhythm' if ok else 'OUT OF RHYTHM'}")
        if not ok: bad.append(q)
    print(f"{os.path.basename(path)}: rhythm {med:.0f} (between-letter stem intervals {min(iv):.0f}-{max(iv):.0f}); "
          f"substituted {seqs or 'none'}; out of rhythm: {' '.join(bad) or 'none'}")
    return bad


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--sheet":
        sheet(a[1], a[2])
    elif a and a[0] == "--check":
        sys.exit(1 if any([check(p) for p in a[1:]]) else 0)
    else:
        for p in a: report(p)
