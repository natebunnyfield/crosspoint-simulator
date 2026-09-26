#!/usr/bin/env python3
"""Apple Vision reading the DEVICE's pixels, per hinting arm (2026-09-26).

The Kept Legibility Index reads 8-bit antialiased text at 9-26 px. The reader
draws Albo at 16.7-37.5 ppem (1x) and 33.3-75 ppem (2x), in FOUR grey levels.
This sets the index's own word corpus (bench_v3.TOKENS, shuffled with the
index's seeds, five words a line) from converter-faithful 2-bit glyphs
(compose.py) at each real size and at 9 px, and reads it with the index's
Vision reader. Reports character accuracy (SequenceMatcher ratio, as the
index) and the confusion pairs, reduced with the index's own reduction.

    KLI_DIR=... python3 reader_read.py --fonts DIR --img DIR --out res.json
"""
import argparse, json, os, random, subprocess, sys
from difflib import SequenceMatcher
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import raster  # noqa: E402
from compose import Setter, to_gray  # noqa: E402

KLI = os.environ["KLI_DIR"]
sys.path.insert(0, os.path.join(KLI, "bench"))
from bench_v3 import TOKENS  # noqa: E402
from bench_v2_core import chunk_words  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "etrace"))
from kli_e import pair_counts  # noqa: E402

OCR = os.path.join(KLI, "ocr", "visionocr")
REPS = 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--img", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--arms", default="today,ttfa-q,light,nohint")
    a = ap.parse_args()
    os.makedirs(a.img, exist_ok=True)
    man = []
    for arm in a.arms.split(","):
        for style in ("Regular", "Italic"):
            path = raster.font_path(a.fonts, arm, style)
            for key, sz, dpi, ppem, tier in raster.sizes():
                if key.endswith("@2x") and key.startswith("8pt"):
                    continue  # 8pt@2x is 16pt at 1x, the same ppem
                st = Setter(path, sz, dpi, raster.ARMS[arm][1])
                for rep in range(REPS):
                    rnd = random.Random(rep * 31 + 7)
                    order = TOKENS[:]
                    rnd.shuffle(order)
                    lines = chunk_words(order, 5)
                    w = int(max(st.width(l) for l in lines)) + 2
                    lv = st.set_lines(lines, w)
                    p = os.path.join(a.img, f"{arm}__{style}__{key}__r{rep}.png")
                    Image.fromarray(to_gray(lv)).save(p)
                    man.append((p, arm, style, key, " ".join(order)))
    out = {}
    for i in range(0, len(man), 40):
        chunk = man[i:i + 40]
        proc = subprocess.run([OCR] + [m[0] for m in chunk], capture_output=True, text=True)
        for ln in proc.stdout.splitlines():
            parts = ln.split("\t")
            if len(parts) >= 2:
                out[parts[0]] = parts[1]
    res = {}
    for p, arm, style, key, gt in man:
        o = " ".join(out.get(p, "").split())
        d = res.setdefault(arm, {}).setdefault(style, {}).setdefault(key, {"reps": []})
        d["reps"].append({"gt": gt, "ocr": o, "acc": SequenceMatcher(None, gt, o, autojunk=False).ratio()})
    for arm in res:
        for style in res[arm]:
            for key, d in res[arm][style].items():
                d["acc"] = round(sum(r["acc"] for r in d["reps"]) / len(d["reps"]), 4)
                pc = pair_counts(d["reps"])
                d["confusions"] = sorted(pc.items(), key=lambda kv: -kv[1])[:8]
                d["e_o"] = pc.get("e>o", 0)
    json.dump(res, open(a.out, "w"), indent=1)
    keys = [k for k, *_ in raster.sizes() if k != "8pt@2x"]
    print(f"{'arm/style':18s}" + "".join(f"{k:>9s}" for k in keys))
    for arm in res:
        for style in res[arm]:
            print(f"{arm + ' ' + style:18s}" + "".join(f"{res[arm][style][k]['acc'] * 100:9.2f}" for k in keys))


if __name__ == "__main__":
    main()
