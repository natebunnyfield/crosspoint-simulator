"""Measure axes (a)-(e) for every Albo build given and the reference panel,
in parallel, into one cache JSON.

    python3 run_geom.py --albo r402=DIR [--albo r393=DIR ...] --out geom.json
"""
import argparse, json, os, sys
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import REFS, CUTS  # noqa: E402
import geom  # noqa: E402


def job(a):
    key, path, idx = a
    try:
        return key, geom.measure_font(path, idx)
    except Exception as e:  # a missing cut in an old snapshot
        return key, {"error": repr(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--albo", action="append", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-refs", action="store_true")
    a = ap.parse_args()
    cache = json.load(open(a.out)) if os.path.exists(a.out) else {}
    jobs = []
    for spec in a.albo:
        tag, d = spec.split("=", 1)
        for cut in CUTS:
            p = os.path.join(d, f"Albo-{cut}.ttf")
            if os.path.exists(p) and f"{tag}/{cut}" not in cache:
                jobs.append((f"{tag}/{cut}", p, 0))
    if not a.no_refs:
        for r, cuts in REFS.items():
            for cut, (p, i) in cuts.items():
                if f"{r}/{cut}" not in cache:
                    jobs.append((f"{r}/{cut}", p, i))
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        for key, res in ex.map(job, jobs):
            cache[key] = res
            print(key, "error" in res and res["error"] or len(res["glyphs"]), flush=True)
    json.dump(cache, open(a.out, "w"))


if __name__ == "__main__":
    main()
