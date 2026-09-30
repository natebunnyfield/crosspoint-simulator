# fences.py's own rule, for the r alone: k = round((gap inside close - gap inside open) / 2),
# open pair +k, close pair -k, |k| < MIN_KERN dropped
import sys, os
WS = os.path.expanduser("~/src/crosspoint-simulator/tools/wedge_serif")
sys.path.insert(0, os.path.join(WS, "instruments")); sys.path.insert(0, os.path.join(WS, "local_ai"))
from fence_gap import G
import fences as F
for cut in ("Italic", "BoldItalic"):
    g = G(os.path.join(sys.argv[1], f"Albo-{cut}.ttf")); out = {}
    for o, c, on, cn in F.FENCES:
        go, gc = F.gapv(g, o + "r", (0, F.XH)), F.gapv(g, "r" + c, (0, F.XH))
        k = max(-F.MAX_K, min(F.MAX_K, int(round((gc - go) / 2))))
        if abs(k) >= F.MIN_KERN: out[f"{on} r"] = k; out[f"r {cn}"] = -k
        print(cut, o + "r", round(go, 1), "r" + c, round(gc, 1), "k", k)
    print(cut, out)
