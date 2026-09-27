"""The reference tables for the poor-characters pass (2026-09-26;
docs/albo-poor-characters-2026-09-26.md): each character measured in Albo
today and in each reference face of the matching cut, in Albo's units (xh 429,
unhinted, unsheared by the measured slant -- poor_trace / fig27_trace.Face).

Common columns (every character):
  w top bot     ink extent, units          lsb rsb   bearings, units
  n             that face's n stem (horizontal run at 0.55 of the n's height)
  thin med thick   chamfer-ridge p10 / p50 / p90 over n      cut   p90 / p10
Per-character columns are named in EXTRA below; every ratio is over that
face's own stem so faces of different weight compare.

t's L/R arm read 0.00 where the face's bar is not on the 0.93 xh row (Baskerville,
Palatino): n/a there, not zero. W's rise/fall is nan where the row at 0.55 cap
does not cut four runs (Flanker B, Hoefler BI).

NOTE (found in this pass): Albo's numbers here are scaled by Albo's own x's top,
which carries ~28 units of wedge over the 429 line, so Albo's heights read about
6% low against the references'. The fit audit's lines do not have this bias.

    python3 instruments/poor_tables.py --albo DIR [--chars y,t,...] > tables.md
"""
import argparse, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from poor_trace import PANEL, face, measure, nstem, _runs, PX, XH_ALBO  # noqa: E402


def stem_at(F, ch, f=0.5, which=0):
    a, x0, yt, adv = F.mask(ch)
    y = int(round((yt - f * XH_ALBO) * PX))
    r = _runs(a[max(0, min(a.shape[0] - 1, y))])
    s, e = r[which]
    return (e - s) / PX


def col_runs(F, ch, xf):
    a, x0, yt, adv = F.mask(ch)
    ys, xs = np.nonzero(a)
    x = xs.min() + int(xf * (xs.max() - xs.min()))
    return [(e - s) / PX for s, e in _runs(a[:, x])]


def row_runs(F, ch, f, cap=False):
    a, x0, yt, adv = F.mask(ch)
    H = a.shape[0]
    y = int(H * (1 - f)) if cap else int(round((yt - f * XH_ALBO) * PX))
    return [(s / PX, e / PX) for s, e in _runs(a[max(0, min(H - 1, y))])]


def bot(F, ch):
    a, x0, yt, adv = F.mask(ch)
    return yt - a.shape[0] / PX


def ex_y(F, n):
    rr = row_runs(F, "y", -0.3)
    tail = min((e - s) for s, e in rr) if rr else float("nan")
    return {"y-p": bot(F, "y") - bot(F, "p"), "tail@-.3/n": tail / n}


def ex_t(F, n):
    a, x0, yt, adv = F.mask("t")
    stem = _runs(a[int(round((yt - 0.5 * XH_ALBO) * PX))])[0]
    bar = _runs(a[int(round((yt - 0.93 * XH_ALBO) * PX))])
    L = (stem[0] - bar[0][0]) / PX if bar else float("nan")
    R = (bar[-1][1] - stem[1]) / PX if bar else float("nan")
    return {"L arm/n": L / n, "R arm/n": R / n, "bar/n": col_runs(F, "t", 0.85)[0] / n,
            "tail/n": col_runs(F, "t", 0.85)[-1] / n}


def ex_j(F, n):
    a, x0, yt, adv = F.mask("j")
    ys, xs = np.nonzero(a)
    r = _runs(a[int(round((yt - 0.5 * XH_ALBO) * PX))]); sl = r[-1][0]
    return {"stem lsb/n": (x0 + sl / PX) / n, "hook reach/n": (sl - xs.min()) / PX / n, "ink lsb": x0 + xs.min() / PX}


def ex_s(F, n):
    ms, mo = measure(F, "s"), measure(F, "o")
    return {"s/o thin": ms["thin_n"] / mo["thin_n"], "s/o med": ms["med_n"] / mo["med_n"], "s/o thick": ms["thick_n"] / mo["thick_n"]}


def ex_N(F, n):
    a, _, _, _ = F.mask("H"); rr = _runs(a[int(a.shape[0] * 0.3)]); hs = (rr[0][1] - rr[0][0]) / PX
    ws = [e - s for s, e in row_runs(F, "N", 0.5, cap=True)]
    return {"thin/H": ws[0] / hs, "diag run/H": (ws[1] / hs) if len(ws) > 2 else float("nan")}


def ex_T(F, n):
    a, x0, yt, adv = F.mask("T"); ys, xs = np.nonzero(a); W = xs.max() - xs.min()
    bar = col_runs(F, "T", 0.22)[0]
    st = _runs(a[int(a.shape[0] * 0.55)])[0]; stw = (st[1] - st[0]) / PX
    return {"bar/stem": bar / stw, "w/cap": W / PX / yt}


def ex_F(F, n):
    a, x0, yt, adv = F.mask("F"); ys, xs = np.nonzero(a); H = a.shape[0]
    st = _runs(a[int(H * 0.85)])[0]; stw = (st[1] - st[0]) / PX
    top = _runs(a[int(H * 0.06)]); reach = (top[-1][1] - st[1]) / PX
    bars = col_runs(F, "F", 0.62)
    return {"top bar/stem": bars[0] / stw, "mid bar/stem": (bars[1] / stw) if len(bars) > 1 else float("nan"),
            "top arm/stem": reach / stw}


def ex_jt_it(F, n):
    i = stem_at(F, "i")
    return {"j/i": stem_at(F, "j") / i, "t/i": stem_at(F, "t") / i, "f/i": stem_at(F, "f") / i}


def ex_r(F, n):
    a, x0, yt, adv = F.mask("r"); ys, xs = np.nonzero(a)
    st = _runs(a[int(round((yt - 0.3 * XH_ALBO) * PX))])[0]
    root = col_runs(F, "r", min(0.99, (st[1] - xs.min()) / max(1, xs.max() - xs.min()) + 0.08))
    return {"arm reach/n": (xs.max() - st[1]) / PX / n, "root/n": (root[0] / n) if root else float("nan")}


def ex_VW(ch):
    def f(F, n):
        ws = [e - s for s, e in row_runs(F, ch, 0.55, cap=True)]
        if ch == "V" and len(ws) >= 2: return {"rise/fall": ws[1] / ws[0], "fall/n": ws[0] / n}
        if ch == "W" and len(ws) >= 4: return {"rise/fall": (ws[1] + ws[3]) / (ws[0] + ws[2]), "fall/n": ws[0] / n}
        return {"rise/fall": float("nan"), "fall/n": float("nan")}
    return f


def ex_q(F, n):
    m = measure(F, "q")
    return {"lsb/n": m["lsb"] / n, "rsb/n": m["rsb"] / n}


# character -> (cuts, extra function, terminal note per face read off the sheets)
EXTRA = {
    "y": (["Regular", "Bold"], ex_y), "t": (["Regular", "Bold"], ex_t), "j": (["Regular"], ex_j),
    "s": (["Regular"], ex_s), "N": (["Regular", "Bold"], ex_N), "T": (["Bold"], ex_T),
    "y_it": (["Italic", "BoldItalic"], ex_y), "jt_it": (["Italic", "BoldItalic"], ex_jt_it),
    "r_it": (["BoldItalic"], ex_r), "V_it": (["BoldItalic"], ex_VW("V")), "W_it": (["BoldItalic"], ex_VW("W")),
    "F_it": (["Italic"], ex_F), "q_it": (["BoldItalic"], ex_q),
}


def table(key, albo_dir):
    cuts, fx = EXTRA[key]; ch = key[0]
    if key == "jt_it": ch = "j"
    out = []
    for cut in cuts:
        italic = "Italic" in cut
        ents = [("Albo today", face(os.path.join(albo_dir, f"Albo-{cut}.ttf"), 0, italic))]
        for lab, p, i in PANEL[cut]:
            try: ents.append((lab, face(p, i, italic)))
            except Exception: pass
        rows = []
        for lab, F in ents:
            try:
                m = measure(F, ch); n = m["nstem"]; e = fx(F, n)
            except Exception as ex:
                rows.append(f"| {lab} | n/a ({type(ex).__name__}) |"); continue
            base = [f"{m['w']:.0f}", f"{m['top']:.0f}", f"{m['bot']:.0f}", f"{m['lsb']:.0f}", f"{m['rsb']:.0f}",
                    f"{n:.0f}", f"{m['thin_n']:.2f}", f"{m['med_n']:.2f}", f"{m['thick_n']:.2f}", f"{m['cut']:.2f}"]
            rows.append("| " + " | ".join([lab] + base + [f"{v:.2f}" if abs(v) < 20 else f"{v:.0f}" for v in e.values()]) + " |")
            hdr = list(e.keys())
        out.append(f"\n**{ch} -- {cut}** (poor_trace units, xh 429)\n")
        out.append("| face | w | top | bot | lsb | rsb | n | thin | med | thick | cut | " + " | ".join(hdr) + " |")
        out.append("|---" * (11 + len(hdr)) + "|")
        out += rows
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--albo", required=True)
    ap.add_argument("--chars", default=",".join(EXTRA))
    a = ap.parse_args()
    for k in a.chars.split(","):
        print(table(k, a.albo))


if __name__ == "__main__":
    main()
