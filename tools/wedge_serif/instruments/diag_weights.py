"""The heavy diagonals' perpendicular thickness, side by side, for one or more
fonts (2026-10-04; docs/albo-bold-k-2026-10-04.md, fifth pass -- the table that
found the Bold K's leg 10-16% heavier than Albo's own V, A, W and X).

Each stroke is read with k_arm_trace's renderer (unhinted, the face's H top on
Albo's 676): its ink run in a band where it stands alone, both edges fitted with
a straight line, thickness = the run's median width x sin(angle). The stem is the
H's at 0.20-0.30 C.

    python3 instruments/diag_weights.py "Albo Bold=Albo-Bold.ttf" "Times Bold=/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"

Run from tools/wedge_serif.
"""
import sys, math, numpy as np
sys.path.insert(0, "instruments"); import k_arm_trace as K
def stroke(path, ch, lo, hi, pick, idx=0):
    a, l, t = K.render(path, idx, ch); ys, xl, xr = [], [], []
    for yu in np.arange(K.CAP_ALBO*lo, K.CAP_ALBO*hi, 2.0):
        y = int(round(t - yu*K.PX)); rs = K.runs(a[y])
        if not rs: continue
        r = pick(rs); ys.append(yu); xl.append(r[0]/K.PX); xr.append(r[1]/K.PX)
    ys = np.array(ys); gl = np.polyfit(ys, xl, 1); gr = np.polyfit(ys, xr, 1); sl = (gl[0]+gr[0])/2
    ang = math.degrees(math.atan2(1.0, abs(sl))); w = np.median(np.array(xr)-np.array(xl))
    return w*math.sin(math.radians(ang)), ang
P = {"K leg": ("K", 0.15, 0.40, lambda rs: max(rs[1:], key=lambda r: r[1]-r[0])),
     "R leg": ("R", 0.08, 0.28, lambda rs: rs[-1]),
     "X thick": ("X", 0.08, 0.32, lambda rs: rs[-1]),
     "V thick": ("V", 0.55, 0.80, lambda rs: rs[0]),
     "A thick": ("A", 0.40, 0.62, lambda rs: rs[-1]),
     "W thick": ("W", 0.55, 0.80, lambda rs: rs[0]),
     "H stem": ("H", 0.20, 0.30, lambda rs: rs[0])}
for f in sys.argv[1:]:
    lab, path = f.split("=", 1); out = []
    st = stroke(path, "H", 0.20, 0.30, lambda rs: rs[0])[0]
    for k, (ch, lo, hi, pick) in P.items():
        try: w, a = stroke(path, ch, lo, hi, pick); out.append(f"{k} {w:4.0f} ({w/st:4.2f}) @{a:4.1f}")
        except Exception as e: out.append(f"{k} ERR")
    print(lab + ": " + " | ".join(out))
