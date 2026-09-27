"""Axis (g): which glyphs a machine reader mistakes, as the reader renders them.

Rendering is the converter's: FreeType NO HINTING, 8-bit coverage cut to the
2-bit levels (>=12/8/4 of the top nibble), glyphs placed by HarfBuzz (so the
font's kerns are in), each glyph at its rounded pixel position.

The text is fixed (seeded) and identical for every face: dictionary words
chosen so every lowercase letter appears in >= 24 words, every capital as a
title-case initial and inside all-caps words, every figure in digit groups.
Four conditions, all stresses because at the reader's clean 16.7 ppem every
serif reads ~100% and nothing separates:

    blur1   16.7 ppem (8 pt at 150 dpi, the reader's smallest), gaussian 1.1 px
    blur2   16.7 ppem, gaussian 1.6 px
    px11    11 ppem, clean
    px9     9 ppem, clean (the Kept Legibility Index's floor)

Reader: Apple Vision (the index's own `visionocr`, language correction OFF).
Per ground-truth character: occurrences, errors (a gt position not inside an
`equal` opcode of difflib's alignment of the line), and the substitutions.

    VISIONOCR=... python3 legib.py --font LABEL PATH[:INDEX] ... --out legib.json
"""
import argparse, json, os, random, subprocess, sys, tempfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
import numpy as np
import freetype
import uharfbuzz as hb
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import LC, UC, FIG  # noqa: E402

VISION = os.environ.get("VISIONOCR")
CONDS = [("blur1", 16.6667, 1.1), ("blur2", 16.6667, 1.6), ("px11", 11.0, 0.0), ("px9", 9.0, 0.0)]
PER_LINE = 6
LINES_PER_IMG = 6


def text(seed=26):
    rnd = random.Random(seed)
    words = [w.strip() for w in open("/usr/share/dict/words") if w.strip().isalpha()]
    low = [w for w in words if w.islower() and 4 <= len(w) <= 8]
    cap = [w for w in words if w[0].isupper() and w[1:].islower() and 4 <= len(w) <= 8]
    items = []
    for c in LC:
        items += rnd.sample([w for w in low if c in w], 24)
    for c in UC:
        pool = [w for w in cap if w[0] == c] or [c + w[1:] for w in rnd.sample(low, 8)]
        items += rnd.sample(pool, min(8, len(pool)))
        items += [w.upper() for w in rnd.sample([w for w in low if c.lower() in w and len(w) <= 6], 6)]
    for _ in range(90):
        items.append("".join(rnd.choice(FIG) for _ in range(rnd.randint(3, 5))))
    rnd.shuffle(items)
    return [" ".join(items[i:i + PER_LINE]) for i in range(0, len(items), PER_LINE)]


def quantize(a8):
    n = a8 >> 4
    return np.where(n >= 12, 3, np.where(n >= 8, 2, np.where(n >= 4, 1, 0))).astype(np.uint8)


class Renderer:
    def __init__(self, path, index, ppem):
        self.face = freetype.Face(path, index)
        self.face.set_char_size(int(ppem * 64), int(ppem * 64), 72, 72)
        blob = hb.Blob.from_file_path(path)
        self.hbf = hb.Font(hb.Face(blob, index))
        self.upm = self.face.units_per_EM
        self.ppem = ppem
        self.cache = {}

    def glyph(self, gid):
        if gid not in self.cache:
            self.face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
            b = self.face.glyph.bitmap
            a = (np.frombuffer(bytes(b.buffer), dtype=np.uint8).reshape(b.rows, b.pitch)[:, :b.width]
                 if b.rows else np.zeros((0, 0), np.uint8))
            self.cache[gid] = (quantize(a), self.face.glyph.bitmap_left, self.face.glyph.bitmap_top)
        return self.cache[gid]

    def line(self, s, canvas, x0, base):
        buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
        hb.shape(self.hbf, buf, {"kern": True, "liga": False})
        k = self.ppem / self.upm
        x = x0
        for inf, pos in zip(buf.glyph_infos, buf.glyph_positions):
            lv, left, top = self.glyph(inf.codepoint)
            gx = int(round(x + pos.x_offset * k)) + left
            gy = base - top
            if lv.size:
                h, w = lv.shape
                sub = canvas[gy:gy + h, gx:gx + w]
                np.maximum(sub, lv[:sub.shape[0], :sub.shape[1]], out=sub)
            x += pos.x_advance * k


def render_images(label, path, index, lines, outdir):
    paths = []
    for cname, ppem, blur in CONDS:
        R = Renderer(path, index, ppem)
        lh = int(ppem * 1.9)
        for i in range(0, len(lines), LINES_PER_IMG):
            chunk = lines[i:i + LINES_PER_IMG]
            W = int(ppem * 0.75 * max(len(s) for s in chunk)) + 40
            H = lh * len(chunk) + int(ppem * 2)
            cv = np.zeros((H, W), np.uint8)
            for j, s in enumerate(chunk):
                R.line(s, cv, 16, int(ppem * 1.3) + j * lh)
            im = Image.fromarray((255 - cv * 85).astype(np.uint8), "L")
            if blur:
                im = im.filter(ImageFilter.GaussianBlur(blur))
            p = os.path.join(outdir, f"{label}__{cname}__{i // LINES_PER_IMG:03d}.png")
            im.save(p)
            paths.append((p, cname, chunk))
    return paths


def ocr(paths, batch=16):
    out = {}
    groups = [paths[i:i + batch] for i in range(0, len(paths), batch)]

    def run(g):
        r = subprocess.run([VISION] + g, capture_output=True, text=True)
        res = {}
        for ln in r.stdout.splitlines():
            if "\t" in ln:
                p, t = ln.split("\t", 1)
                res[p] = t
        return res
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as ex:
        for res in ex.map(run, groups):
            out.update(res)
    return out


def score(gt_lines, read):
    """Per gt char: [occurrences, errors], and the substitutions."""
    gt = " ".join(gt_lines)
    occ, err, sub = Counter(), Counter(), Counter()
    ok = np.zeros(len(gt), bool)
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, gt, read, autojunk=False).get_opcodes():
        if tag == "equal":
            ok[i1:i2] = True
        elif tag == "replace" and (i2 - i1) == (j2 - j1):
            for a, b in zip(gt[i1:i2], read[j1:j2]):
                if a != b and not a.isspace():
                    sub[f"{a}>{b}"] += 1
    for i, ch in enumerate(gt):
        if ch.isspace():
            continue
        occ[ch] += 1
        if not ok[i]:
            err[ch] += 1
    return occ, err, sub


def run_font(label, spec, lines, work):
    path, idx = (spec.rsplit(":", 1) + ["0"])[:2] if spec.count(":") and not spec.endswith(".ttf") else (spec, "0")
    d = os.path.join(work, label.replace("/", "_"))
    os.makedirs(d, exist_ok=True)
    imgs = render_images(label.replace("/", "_"), path, int(idx), lines, d)
    read = ocr([p for p, _, _ in imgs])
    res = {"occ": Counter(), "err": Counter(), "sub": Counter(), "by_cond": defaultdict(lambda: [0, 0])}
    for p, cname, chunk in imgs:
        o, e, s = score(chunk, read.get(p, ""))
        res["occ"].update(o); res["err"].update(e); res["sub"].update(s)
        res["by_cond"][cname][0] += sum(o.values()); res["by_cond"][cname][1] += sum(e.values())
    return {"occ": dict(res["occ"]), "err": dict(res["err"]), "sub": dict(res["sub"].most_common(400)),
            "by_cond": dict(res["by_cond"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", nargs=2, action="append", metavar=("LABEL", "PATH[:INDEX]"), default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", default=None)
    a = ap.parse_args()
    if not VISION:
        sys.exit("set VISIONOCR to the kept-legibility-index's ocr/visionocr binary")
    work = a.work or tempfile.mkdtemp(prefix="legib")
    lines = text()
    cache = json.load(open(a.out)) if os.path.exists(a.out) else {}
    for label, spec in a.font:
        if label in cache:
            continue
        cache[label] = run_font(label, spec, lines, work)
        o = sum(cache[label]["occ"].values()); e = sum(cache[label]["err"].values())
        print(f"{label}: {e}/{o} char errors ({e / max(o, 1):.1%})", flush=True)
        json.dump(cache, open(a.out, "w"))


if __name__ == "__main__":
    main()
