#!/usr/bin/env python3
"""OCR at degradation as a spacing judge: which white makes each word most legible to a machine reader?

THE IDEA (the premise of every OCR-as-legibility tool, e.g. the Kept
Legibility Index, github.com/JessieSalas/kept-legibility-index, MIT). For each
pair he has answered, render the word it was benched in, with that one gap
moved by delta units (delta on a grid, every other glyph untouched), degrade it
to where the reader starts to fail, read it back, and score character accuracy.
The delta that reads best is the reader's "answer" for that pair, on the same
scale as his.

THE READER is the index's own: Apple Vision, .accurate, language correction
OFF, en-US (ocr/visionocr.swift in that repo, built with swiftc). Optional
second reader: Tesseract 5 (--tesseract), psm 8 (one word).

RENDERING. The 2026-09-20 bench fonts (the zero his answers are on), HarfBuzz
with kerning and no ligatures, outlines rasterized by FreeType at 4x and
box-filtered to the target size so a sub-pixel delta is still a real change.

    $VENV/bin/python ocr_judge.py --visionocr PATH/visionocr --pilot     # choose conditions
    $VENV/bin/python ocr_judge.py --visionocr PATH/visionocr             # the full run
"""
import argparse, json, os, subprocess, sys, tempfile, time, zlib
import numpy as np
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.transformPen import TransformPen
from PIL import Image
from scipy.ndimage import gaussian_filter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

DELTAS = list(range(-40, 41, 10))
SS = 4


class Renderer:
    def __init__(self, path):
        self.tt = TTFont(path); self.gs = self.tt.getGlyphSet(); self.order = self.tt.getGlyphOrder()
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(path)))

    def word(self, text, i, delta, em_px, blur, noise, seed):
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"liga": False, "clig": False, "dlig": False})
        x, pos = 0.0, []
        for k, (inf, gp) in enumerate(zip(buf.glyph_infos, buf.glyph_positions)):
            pos.append((self.order[inf.codepoint], x + gp.x_offset))
            x += gp.x_advance
            if inf.cluster == i:          # the left glyph of the benched pair
                x += delta
        sc = em_px * SS / 1000.0
        pad = 0.6 * 1000
        W = int((x + 2 * pad) * sc) + SS; H = int(1.9 * 1000 * sc)
        W -= W % SS; H -= H % SS
        pen = FreeTypePen(self.gs)
        for name, gx in pos:
            self.gs[name].draw(TransformPen(pen, (1, 0, 0, 1, gx, 0)))
        cov = pen.array(width=W, height=H, transform=(sc, 0, 0, sc, pad * sc, 0.55 * 1000 * sc))
        cov = cov.reshape(H // SS, SS, W // SS, SS).mean((1, 3))
        img = 1.0 - cov
        if blur:
            img = gaussian_filter(img, blur)
        if noise:
            img = img + np.random.default_rng(seed).normal(0, noise, img.shape)
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))


def char_acc(gt, got):
    got = got.strip()
    m, n = len(gt), len(got)
    d = list(range(n + 1))
    for a in range(1, m + 1):
        prev, d[0] = d[0], a
        for b in range(1, n + 1):
            cur = min(d[b] + 1, d[b - 1] + 1, prev + (gt[a - 1] != got[b - 1]))
            prev, d[b] = d[b], cur
    return max(0.0, 1 - d[n] / max(1, m))


def read_vision(exe, paths, chunk=400):
    out = {}
    for k in range(0, len(paths), chunk):
        r = subprocess.run([exe] + paths[k:k + chunk], capture_output=True, text=True, check=True)
        for line in r.stdout.splitlines():
            p, _, t = line.partition("\t")
            out[p] = t
    return out


def read_tesseract(paths):
    import pytesseract
    return {p: pytesseract.image_to_string(Image.open(p), config="--psm 8").strip() for p in paths}


def run(args, conds, deltas, pairs, label):
    T = C.Truth(); W = C.words()
    rend = {s: Renderer(C.FONTSETS["0920"][s]) for s in C.STYLES}
    jobs = []
    with tempfile.TemporaryDirectory() as tmp:
        for s in C.STYLES:
            for p in pairs[s]:
                word, i = W[(s, p)]
                for ci, (em, blur, noise) in enumerate(conds):
                    for rep in range(args.reps):
                        for d in deltas:
                            f = os.path.join(tmp, f"{len(jobs)}.png")
                            rend[s].word(word, i, d, em, blur, noise, seed=zlib.crc32(f"{s}|{p}|{ci}|{rep}".encode())).save(f)
                            jobs.append((s, p, word, ci, rep, d, f))
        t0 = time.time()
        paths = [j[-1] for j in jobs]
        got = read_tesseract(paths) if args.tesseract else read_vision(args.visionocr, paths)
        secs = time.time() - t0
    acc = {}
    for s, p, word, ci, rep, d, f in jobs:
        acc.setdefault((s, p), {}).setdefault(d, []).append(char_acc(word, got.get(f, "")))
    print(f"{label}: {len(jobs)} images read in {secs:.0f} s ({1000 * secs / max(1, len(jobs)):.0f} ms each)")
    return acc, secs, len(jobs)


def predict(curve):
    """curve {delta: [acc]} -> the reader's answer: the vertex of a quadratic fit
    to mean accuracy (clipped to the grid), or 0 when the curve is flat."""
    ds = np.array(sorted(curve)); m = np.array([np.mean(curve[d]) for d in ds])
    if m.max() - m.min() < 1e-9:
        return 0.0, 0.0
    a, b, c = np.polyfit(ds, m, 2)
    if a < 0:
        v = float(np.clip(-b / (2 * a), ds.min(), ds.max()))
    else:
        v = float(ds[np.argmax(m)])
    return v, float(m.max() - m.min())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--visionocr")
    ap.add_argument("--tesseract", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--pilot-conds", default="7:0:0,8:0:0,9:0:0,9:0.6:0,10:0.8:0,11:1.0:0,12:1.3:0,"
                    "11:0.9:0.08,13:1.2:0.12,14:1.6:0.1")
    ap.add_argument("--conds", default="10:0:0,12:0.7:0,12:0:0.1,14:0:0.15",   # pilot: 0.50-0.66 char acc at delta 0
                    help="em_px:blur_px:noise_sd, comma-separated")
    a = ap.parse_args()
    T = C.Truth()
    if a.pilot:
        rng = np.random.default_rng(1)
        pairs = {s: list(rng.choice(T.P[s], 20, replace=False)) for s in C.STYLES}
        a.reps = 1
        for cond in a.pilot_conds.split(","):
            em, bl, no = map(float, cond.split(":"))
            acc, _, _ = run(a, [(em, bl, no)], [0], pairs, cond)
            v = [np.mean(c[0]) for c in acc.values()]
            print(f"   {cond}: mean char acc at delta 0 = {np.mean(v):.2f}, words perfect {np.mean(np.array(v) == 1):.0%}")
        return
    conds = [tuple(map(float, c.split(":"))) for c in a.conds.split(",")]
    acc, secs, n = run(a, conds, DELTAS, T.P, "full")
    white = {s: {} for s in C.STYLES}
    strength = {s: {} for s in C.STYLES}
    for (s, p), curve in acc.items():
        v, rng_ = predict(curve)
        white[s][p] = T.white0920[s][p] + v
        strength[s][p] = rng_
    name = "ocr-tesseract" if a.tesseract else "ocr-vision"
    curves = {f"{s}|{p}": {str(d): float(np.mean(v)) for d, v in c.items()} for (s, p), c in acc.items()}
    print(C.save_preds(name, "0920", white, {"conds": conds, "deltas": DELTAS, "reps": a.reps,
                                              "images": n, "seconds": round(secs), "curves": curves}))


if __name__ == "__main__":
    main()
