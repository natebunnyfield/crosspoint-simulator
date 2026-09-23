#!/usr/bin/env python3
"""Albo's MARKS against roman references: the dots, the tittles, the dieresis.

WHY THIS EXISTS AS A FILE. Round 362 measured the same things from an inline
heredoc, published the numbers, and deleted the instrument. Round 369 then
needed them again -- for the exclamation's dot, the tittles, the dieresis and
"scale up punctuation slightly" -- and had nothing to re-run. Per the repo's
own rule: a surprising number IS the instrument until proven otherwise, and
that cannot be done against a script that is gone.

WHAT IT MEASURES, and why from a RASTER rather than from the outline bounds.
Extents (a period's width, a comma's reach) come out of `glyf` bounds exactly
and for free. Everything that actually decides these four asks does not:
a dot's DIAMETER when the mark has two of them, the WHITE between a colon's
pair, an exclamation stem's THICK, whether a dieresis sits centred over its
letter. Those are per-component measurements, so every font -- Albo and the
references alike -- is rendered to a common x-height and read back the same
way. One measurement path, no per-font special case.

EVERY FIGURE IS DIVIDED BY THE X-HEIGHT, measured from that font's own 'x'.
A period is not "0.25 em" in any useful sense; it is a mark read beside a
lowercase, and the references disagree about em far more than they disagree
about the body.

THE ONE TRAP. A .ttc holds several faces and PIL opens index 0 by default,
which is not always the roman -- check the reported family name, printed in
the header row, rather than trusting the filename.
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REFS = [
    ("/System/Library/Fonts/Supplemental/Georgia.ttf", 0, "Georgia"),
    ("/System/Library/Fonts/Supplemental/Times New Roman.ttf", 0, "Times"),
    ("/System/Library/Fonts/Supplemental/Baskerville.ttc", 0, "Baskerville"),
    ("/System/Library/Fonts/Supplemental/Charter.ttc", 0, "Charter"),
    ("/System/Library/Fonts/Supplemental/Hoefler Text.ttc", 0, "Hoefler"),
    ("/System/Library/Fonts/Supplemental/Palatino.ttc", 0, "Palatino"),
]

PX = 900          # nominal em; the x-height lands near 400-470 px on these faces

def _load(path, idx, px):
    return ImageFont.truetype(path, px, index=idx)

def _raster(f, text, pad=40):
    """One glyph on white, with the BASELINE at a known row."""
    asc, desc = f.getmetrics()
    w = int(f.getlength(text)) + 2 * pad
    h = asc + desc + 2 * pad
    im = Image.new("L", (max(w, 8), max(h, 8)), 255)
    ImageDraw.Draw(im).text((pad, pad + asc), text, font=f, fill=0, anchor="ls")
    return np.asarray(im) < 128, pad + asc     # mask, baseline row

def _bbox(m):
    ys, xs = np.nonzero(m)
    if not len(ys): return None
    return xs.min(), ys.min(), xs.max(), ys.max()

def _components(m):
    """4-connected components, biggest first. No scipy in this tree."""
    lab = np.zeros(m.shape, np.int32); n = 0; out = []
    H, W = m.shape
    for sy in range(H):
        for sx in range(W):
            if not m[sy, sx] or lab[sy, sx]: continue
            n += 1; stack = [(sy, sx)]; lab[sy, sx] = n; pix = []
            while stack:
                y, x = stack.pop(); pix.append((y, x))
                for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny, nx = y+dy, x+dx
                    if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not lab[ny, nx]:
                        lab[ny, nx] = n; stack.append((ny, nx))
            a = np.array(pix)
            out.append(dict(n=len(pix), y0=a[:,0].min(), y1=a[:,0].max(),
                            x0=a[:,1].min(), x1=a[:,1].max(),
                            cx=a[:,1].mean(), cy=a[:,0].mean()))
    out.sort(key=lambda d: -d["n"])
    return out

def _max_run_w(m, y0, y1):
    """The widest horizontal ink run in a row band -- a stem's THICK."""
    best = 0
    for y in range(int(y0), int(y1) + 1):
        row = m[y]; run = 0
        for v in row:
            run = run + 1 if v else 0
            if run > best: best = run
    return best

def measure(path, idx, name):
    f = _load(path, idx, PX)
    try: fam = f.getname()[0]
    except Exception: fam = name
    m, bl = _raster(f, "x"); b = _bbox(m)
    xh = b[3] - b[1] + 1
    R = {"font": name, "fam": fam, "xh_px": xh}

    def ext(ch):
        mm, bb = _raster(f, ch); q = _bbox(mm)
        if q is None: return None
        return dict(w=(q[2]-q[0]+1)/xh, h=(q[3]-q[1]+1)/xh,
                    drop=(q[3]-bb)/xh, mask=mm, base=bb)

    # the CAP and the ASCENDER, from the font's own letters -- the ! and the ?
    # are measured against both, because "up to the ascender" is a question
    # about which of the two they are cut to and the references disagree.
    mh, _ = _raster(f, "H"); qh = _bbox(mh); cap = (qh[3] - qh[1] + 1) / xh
    mb, _ = _raster(f, "b"); qb = _bbox(mb); ascd = (qb[3] - qb[1] + 1) / xh
    R["cap"], R["asc"] = cap, ascd

    p = ext("."); R["period_w"], R["period_h"] = (p["w"], p["h"]) if p else (None, None)
    for ch, tag in (("!", "excl"), ("?", "quest")):
        e2 = ext(ch)
        if e2 is None: continue
        R[tag + "_top"] = e2["h"] + (e2["drop"] if e2["drop"] < 0 else 0.0) if False else None
        mm2, bb2 = _raster(f, ch); q2 = _bbox(mm2)
        R[tag + "_top"] = (bb2 - q2[1]) / xh          # the mark's TOP above the baseline
        R[tag + "_of_cap"] = R[tag + "_top"] / cap
        R[tag + "_of_asc"] = R[tag + "_top"] / ascd
    cm = ext(","); R["comma_w"], R["comma_h"] = (cm["w"], cm["h"]) if cm else (None, None)
    ap = ext("’") or ext("'")
    R["quote_w"], R["quote_h"] = (ap["w"], ap["h"]) if ap else (None, None)

    # the colon: two dots, and the white between them
    cl = ext(":")
    if cl:
        cs = _components(cl["mask"])[:2]
        if len(cs) == 2:
            cs.sort(key=lambda d: d["y0"])
            R["colon_gap"] = (cs[1]["y0"] - cs[0]["y1"]) / xh
            R["colon_dot"] = np.mean([c["x1"]-c["x0"]+1 for c in cs]) / xh

    # the exclamation: dot, stem thick, and the dot against that thick
    ex = ext("!")
    if ex:
        cs = _components(ex["mask"])
        if len(cs) >= 2:
            cs.sort(key=lambda d: d["y0"])
            stem_c, dot_c = cs[0], cs[-1]
            R["excl_dot"] = (dot_c["x1"]-dot_c["x0"]+1)/xh
            R["excl_thick"] = _max_run_w(ex["mask"], stem_c["y0"], stem_c["y1"])/xh
            R["excl_dot_over_thick"] = R["excl_dot"]/R["excl_thick"] if R["excl_thick"] else None
            R["excl_gap"] = (dot_c["y0"] - stem_c["y1"])/xh

    # the i: its tittle against its own stem
    ii = ext("i")
    if ii:
        cs = _components(ii["mask"])
        if len(cs) >= 2:
            cs.sort(key=lambda d: d["y0"])
            tit, body = cs[0], cs[-1]
            R["tittle_d"] = (tit["x1"]-tit["x0"]+1)/xh
            R["i_stem"] = _max_run_w(ii["mask"], body["y0"]+ (body["y1"]-body["y0"])*0.35,
                                                 body["y0"]+ (body["y1"]-body["y0"])*0.55)/xh
            R["tittle_over_stem"] = R["tittle_d"]/R["i_stem"] if R["i_stem"] else None
            R["tittle_gap"] = (body["y0"] - tit["y1"])/xh
            R["tittle_off"] = (tit["cx"] - body["cx"])/xh    # + = tittle right of the stem

    # the dieresis, on a real letter: its two dots, their spacing, its centring.
    # MEASURED ON ALL THREE LETTERS, not the first that parses: every reference
    # sits LEFT of the ink centre, and whether that is an 'a'-shaped optical
    # correction or a constant is not a question one letter can answer.
    for ch, tag in ((u"\u00f6", "o"), (u"\u00e4", "a"), (u"\u00fc", "u")):
        dd = ext(ch)
        if dd is None: continue
        cs = _components(dd["mask"])
        tops = [c for c in cs if c["y1"] < dd["base"] - xh * 0.55]
        if len(tops) != 2: continue
        tops.sort(key=lambda d: d["cx"])
        body = max((c for c in cs if c not in tops), key=lambda d: d["n"])
        dia = float(np.mean([c["x1"] - c["x0"] + 1 for c in tops]))
        R["die_dot"] = dia / xh
        R["die_white"] = (tops[1]["x0"] - tops[0]["x1"]) / xh
        R["die_gap_over_dot"] = (tops[1]["x0"] - tops[0]["x1"]) / dia
        R["die_err_" + tag] = (((tops[0]["cx"] + tops[1]["cx"]) / 2.0)
                               - ((body["x0"] + body["x1"]) / 2.0)) / xh
    return R

ROWS = [
    ("cap", "cap / xh"), ("asc", "asc / xh"),
    ("excl_top", "! top"), ("excl_of_cap", "! of cap"), ("excl_of_asc", "! of asc"),
    ("quest_top", "? top"), ("quest_of_cap", "? of cap"), ("quest_of_asc", "? of asc"),
    ("period_w",  ". width"),      ("period_h",  ". height"),
    ("comma_w",   ", width"),      ("comma_h",   ", height"),
    ("quote_w",   "’ width"), ("quote_h",   "’ height"),
    ("colon_dot", ": dot"),        ("colon_gap", ": white"),
    ("excl_dot",  "! dot"),        ("excl_thick","! thick"),
    ("excl_dot_over_thick", "! dot / thick"),
    ("tittle_d",  "i tittle"),     ("i_stem",    "i stem"),
    ("tittle_over_stem", "tittle / stem"),
    ("tittle_gap","tittle gap"),   ("tittle_off","tittle offset"),
    ("die_dot",   "¨ dot"),   ("die_white", "¨ white"),
    ("die_gap_over_dot", "¨ white / dot"),
    ("die_err_o", "¨ err on ö"),
    ("die_err_a", "¨ err on ä"),
    ("die_err_u", "¨ err on ü"),
]

def main(argv):
    subjects = []
    for a in argv:
        subjects.append((a, 0, os.path.basename(a).replace(".ttf", "")))
    rows = [measure(*s) for s in subjects] + [measure(*r) for r in REFS]
    names = [r["font"] for r in rows]
    w = max(len(n) for n in names) + 1
    print("x-height px:  " + "".join(f"{r['xh_px']:>9d}" for r in rows))
    print("family:       " + "  ".join(r["fam"][:7] for r in rows))
    print("-" * (16 + 9 * len(rows)))
    nsub = len(subjects)
    for key, lab in ROWS:
        vals = [r.get(key) for r in rows]
        line = f"{lab:<16}"
        for v in vals:
            line += "     n/a " if v is None else f"{v:>9.3f}"
        ref = [v for v in vals[nsub:] if v is not None]
        if ref: line += f"   refs {min(ref):.3f}-{max(ref):.3f}"
        print(line)

if __name__ == "__main__":
    main(sys.argv[1:])
