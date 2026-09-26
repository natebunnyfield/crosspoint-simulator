#!/usr/bin/env python3
"""Is the e->o confusion a property of the SHAPE, or of one pixel size?

The Kept Legibility Index reads body text at exactly 9 px (and 12). A cliff in
a dial (the e bar floor: 0.42 gives 5 e>o, 0.45 gives 131) smells of pixel
grid phase, so this renders the index's own word corpus with the index's own
renderer (bench/render.py: HarfBuzz + FreeType FT_LOAD_RENDER) and degrade(),
at a sweep of em sizes including half-pixel ones, and reads each image with
the same Apple Vision reader. Counts e>o with the index's reduction.

    KLI_DIR=... python3 size_sweep.py --font A a.ttf --font B b.ttf --out res.json
"""
import argparse, json, os, random, subprocess, sys

KLI = os.environ["KLI_DIR"]
sys.path.insert(0, os.path.join(KLI, "bench"))
from bench_v2_core import degrade, render_lines, chunk_words  # noqa: E402
from bench_v3 import TOKENS  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kli_e import pair_counts  # noqa: E402

OCR = os.path.join(KLI, "ocr", "visionocr")
SIZES = [8, 8.5, 9, 9.5, 10, 10.5, 11, 12, 13]
BLURS = [0.0, 0.6]
REPS = 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", nargs=2, action="append", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--img", required=True, help="scratch dir for the rendered images")
    a = ap.parse_args()
    os.makedirs(a.img, exist_ok=True)
    man = []
    for label, path in a.font:
        for size in SIZES:
            for blur in BLURS:
                for rep in range(REPS):
                    rnd = random.Random(rep * 31 + 7)
                    order = TOKENS[:]
                    rnd.shuffle(order)
                    img = render_lines(path, 0, None, chunk_words(order, 5), size, width=780)
                    img = degrade(img, blur=blur)
                    p = os.path.join(a.img, f"{label}__{size}__{blur}__{rep}.png")
                    img.save(p)
                    man.append((p, label, size, blur, " ".join(order)))
    out = {}
    for i in range(0, len(man), 40):
        chunk = man[i:i + 40]
        proc = subprocess.run([OCR] + [m[0] for m in chunk], capture_output=True, text=True)
        for ln in proc.stdout.splitlines():
            parts = ln.split("\t")
            if len(parts) >= 2:
                out[parts[0]] = parts[1]
    res = {}
    for p, label, size, blur, gt in man:
        res.setdefault(label, {}).setdefault(f"{size}/{blur}", []).append({"gt": gt, "ocr": out.get(p, "")})
    table = {lab: {k: pair_counts(v).get("e>o", 0) for k, v in d.items()} for lab, d in res.items()}
    json.dump(dict(table=table, sizes=SIZES, blurs=BLURS, reps=REPS), open(a.out, "w"), indent=1)
    hdr = "".join(f"{s:>7}" for s in SIZES)
    for blur in BLURS:
        print(f"blur {blur}   {hdr}")
        for lab in table:
            print(f"  {lab:18s}" + "".join(f"{table[lab][f'{s}/{blur}']:>7}" for s in SIZES))


if __name__ == "__main__":
    main()
