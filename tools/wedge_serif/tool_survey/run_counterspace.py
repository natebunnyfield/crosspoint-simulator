#!/usr/bin/env python3
"""Simon Cozens' CounterSpace, run on Albo: the desired white of every answered pair.

SOURCE. github.com/simoncozens/CounterSpace (Apache-2.0, last commit
2024-04-27), CounterSpace.py unmodified. It needs `tensorfont`; the pinned
0.0.6 no longer imports (skimage.util.pad was removed), 0.2.0 does and has the
same API. Its own venv, because tensorfont pulls its own numpy/skimage:

    uv venv -p python3.12 venv-cs
    uv pip install -p venv-cs/bin/python tensorfont==0.2.0 numpy scipy fonttools
    venv-cs/bin/python run_counterspace.py --cs-dir PATH/TO/CounterSpace [--smoothing 2] [--fontset 0920]

WHAT IT DOES (CounterSpace.py). determine_parameters() fits the widths and
strengths of three Gaussian "lights" so that the key pairs HH OO HO OH EE AV,
set at the font's OWN current spacing, show equal lit counter-area; space(l, r)
then walks the distance until the pair's lit area reaches that of its
reference pair (nn for anything with a lowercase letter, HH otherwise). So it
is self-calibrating to the font it is given, and its output is a distance --
rsb + kern + lsb, the same white this survey scores -- in font units.

The reference zone is the reference pair's ink height. `serif_smoothing`
blurs serifs out of the contour (README: "increase to 20 or so if you have
prominent serifs"; class default 2, autospace.py uses 0).

Writes preds/counterspace-s<smoothing>-<fontset>.json (common.save_preds's
format, written here without importing common, whose sklearn is not in this venv).
"""
import argparse, json, os, sys, time
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cs-dir", required=True)
    ap.add_argument("--smoothing", type=int, default=2)   # pixels; the library slices with it
    ap.add_argument("--fontset", default="0920")
    a = ap.parse_args()
    sys.path.insert(0, a.cs_dir)
    from CounterSpace import CounterSpace
    meta = json.load(open(os.path.join(HERE, "preds", "pairs.json")))
    white, info = {}, {}
    t0 = time.time()
    for s in ("roman", "italic"):
        path = meta["fonts"][a.fontset][s]
        cmap = TTFont(path).getBestCmap()
        c = CounterSpace(path, serif_smoothing=a.smoothing)
        t = time.time()
        opts = c.determine_parameters()
        info[s] = {"options": {k: float(v) for k, v in opts.items()}, "fit_seconds": round(time.time() - t, 1)}
        white[s] = {}
        for p in meta["pairs"][s]:
            white[s][p] = float(c.space(cmap[ord(p[0])], cmap[ord(p[1])]))
        print(f"{s}: {len(white[s])} pairs, {time.time() - t:.0f} s", flush=True)
    out = os.path.join(HERE, "preds", f"counterspace-s{a.smoothing:g}-{a.fontset}.json")
    json.dump({"tool": f"counterspace-s{a.smoothing:g}", "fontset": a.fontset,
               "meta": {"smoothing": a.smoothing, "seconds": round(time.time() - t0, 1), **info},
               "white": white}, open(out, "w"), indent=0, ensure_ascii=False)
    print("wrote", out)


if __name__ == "__main__":
    main()
