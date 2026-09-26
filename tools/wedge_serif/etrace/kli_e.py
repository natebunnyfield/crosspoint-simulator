#!/usr/bin/env python3
"""The Kept Legibility Index, run for the e->o question (2026-09-26).

Runs the index's OWN v3.1 protocol (github.com/JessieSalas/kept-legibility-index,
bench/bench_v31.run -- same corpus, conditions, seeds, reader) over a panel of
fonts, then reduces the reader's raw output with the index's own
`score_candidate.confusions_from_raw` and reports, per font:

  - the grand mean and the `crowded` cell;
  - e>o in total and PER CONDITION (the survey only had the total);
  - the top confusions.

--tess adds a SECOND READER on the very same images: Tesseract 5 (LSTM,
--psm 6), each image upscaled 4x Lanczos first because Tesseract does not read
a 9 px em at all. It is a different model family from Apple Vision, so a
confusion both readers make is a property of the drawing, not of one reader.

    KLI_DIR=.../kept-legibility-index python3 kli_e.py \
        --font "A" a.ttf --font "B" b.ttf --ref Georgia --out res.json [--tess]

The index writes its images into KLI_DIR/bench/img-v31/<label>__<cond>__r<n>.png
(labels are made filename-safe there); nothing here edits the index.
"""
import argparse, json, os, subprocess, sys, shutil
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher

KLI = os.environ.get("KLI_DIR")
if not KLI:
    sys.exit("set KLI_DIR to a kept-legibility-index checkout")
BENCH = os.path.join(KLI, "bench")
sys.path.insert(0, BENCH)
os.environ.setdefault("VISIONOCR", os.path.join(KLI, "ocr", "visionocr"))
import bench_v31  # noqa: E402
import score_candidate  # noqa: E402

TESS_CONDS = ["body-9px", "body-9px-blur", "body-12px", "body-12px-blur", "passthrough"]


def pair_counts(reps, want=None):
    """score_candidate's reduction, per list of {gt, ocr}; want=(x, y) counts one pair."""
    c = {}
    for r in reps:
        gt, o = r.get("gt", ""), r.get("ocr", "")
        if not gt or not o:
            continue
        for tag, i1, i2, j1, j2 in SequenceMatcher(None, gt, o, autojunk=False).get_opcodes():
            if tag != "replace":
                continue
            a, b = gt[i1:i2], o[j1:j2]
            if len(a) != len(b):
                k = min(len(a), len(b))
                if not k:
                    continue
                a, b = a[-k:], b[-k:]
            for x, y in zip(a, b):
                if x.isspace() or y.isspace() or x == y:
                    continue
                c[f"{x}>{y}"] = c.get(f"{x}>{y}", 0) + 1
    return c


def tess_read(path):
    from PIL import Image
    im = Image.open(path).convert("L")
    im = im.resize((im.width * 4, im.height * 4), Image.LANCZOS)
    tmp = path[:-4] + ".x4.png"
    im.save(tmp)
    p = subprocess.run(["tesseract", tmp, "-", "--psm", "6", "-l", "eng"],
                       capture_output=True, text=True)
    os.remove(tmp)
    return " ".join(p.stdout.split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", nargs=2, action="append", metavar=("LABEL", "PATH"), default=[])
    ap.add_argument("--ref", action="append", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--tess", action="store_true")
    a = ap.parse_args()
    panel = [(n, p, 0, None) for n, p in a.font]
    for n in a.ref:
        path, idx, w = score_candidate.KNOWN[n]
        panel.append((n, path, idx, w))
    tmpname = "etrace-" + os.path.basename(a.out)
    bench_v31.run(panel, out_name=tmpname, keep_raw=True)
    res = json.load(open(os.path.join(BENCH, tmpname)))
    os.remove(os.path.join(BENCH, tmpname))
    raw = res["raw_reader_output"]
    summary = {}
    for label, conds in raw.items():
        per = {c: pair_counts(reps).get("e>o", 0) for c, reps in conds.items()}
        allc = {}
        for reps in conds.values():
            for k, v in pair_counts(reps).items():
                allc[k] = allc.get(k, 0) + v
        R = res["results"][label]
        summary[label] = dict(grand=R["grand_mean"], crowded=R["cells"]["crowded"]["mean"],
                              legible_px=R["legible_down_to_px"], e_o=sum(per.values()),
                              e_o_by_cond={k: v for k, v in per.items() if v},
                              e_total=sum(r["gt"].count("e") for reps in conds.values() for r in reps),
                              top=sorted(allc.items(), key=lambda kv: -kv[1])[:10])
    if a.tess:
        for label in raw:
            safe = label.replace(" ", "_")
            jobs = [(c, r, os.path.join(bench_v31.OUT, f"{safe}__{c}__r{r}.png"))
                    for c in TESS_CONDS for r in range(bench_v31.REPS)]
            with ThreadPoolExecutor(8) as ex:
                outs = list(ex.map(lambda j: tess_read(j[2]), jobs))
            per = {}
            for (c, r, _), o in zip(jobs, outs):
                gt = raw[label][c][r]["gt"]
                per.setdefault(c, []).append({"gt": gt, "ocr": o})
            summary[label]["tess_e_o_by_cond"] = {c: pair_counts(v).get("e>o", 0) for c, v in per.items()}
            summary[label]["tess_e_o"] = sum(summary[label]["tess_e_o_by_cond"].values())
            allc = {}
            for v in per.values():
                for k, n in pair_counts(v).items():
                    allc[k] = allc.get(k, 0) + n
            summary[label]["tess_top"] = sorted(allc.items(), key=lambda kv: -kv[1])[:8]
    json.dump(dict(summary=summary, raw=raw), open(a.out, "w"), indent=1)
    for label, s in summary.items():
        t = f"  tess e>o {s['tess_e_o']:4d} {s['tess_e_o_by_cond']}" if "tess_e_o" in s else ""
        print(f"{label:24s} grand {s['grand']*100:5.1f} crowd {s['crowded']*100:5.1f} "
              f"e>o {s['e_o']:4d} {s['e_o_by_cond']}{t}")


if __name__ == "__main__":
    main()
