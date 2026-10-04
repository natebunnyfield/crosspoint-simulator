#!/usr/bin/env python3
"""mid_punct.py -- where does Albo's MID punctuation sit vertically, against references
measured the same way? Owner todo 2026-10-04: *"raise middot and other mid punctuation to
be optically vertically centered"* (docs/albo-mid-punctuation-2026-10-04.md).

    $VENV/bin/python instruments/mid_punct.py DIR [DIR2 ...] [--json OUT.json] [--refs-only]
    $VENV/bin/python instruments/mid_punct.py --summary DIR     # the doc's markdown tables

DIR holds the four Albo-*.ttf. Every number is read off the OUTLINE (FreeType, unscaled,
unhinted), in font units, so a TrueType and a CFF reference answer the same question; the
italics are measured as shipped -- a shear about the baseline moves nothing vertically.

  center      (yMin + yMax) / 2 of the glyph's ink box. The area centroid is printed beside
              it where they differ by more than 3 units (the wedge middle dot, the bold
              guillemets, the composite signs +- != <= >= whose parts are unequal)
  xh          the lowercase body, as the MEDIAN of ten estimates: the tops of z u dotless-i
              n m, and yMax + yMin of o e c s a (a round letter's overshoot taken as
              symmetric). No single letter is safe -- Palatino's and Albo's head serifs
              rise above the body (x 965 on a 936 Palatino, x 451 on a 429 Albo), Albo
              Italic's round letters dip 16 and rise 7, and an arch overshoots. The
              diagonals (v w x y) and the r are left OUT: in a wedge face their head
              serifs rise, and with them in, Albo Bold Italic read 448 on a lowercase drawn
              at 435 (429 x 1.015, +1.2 spread). The ten land on every Albo cut's drawn
              x-height (R 430, I 435, B 430, Z 438). Against the DECLARED OS/2 x-height
              (printed below): within 3 units for Georgia roman and bold, Berkeley and
              Times New Roman in every cut; Times roman +5 and bold +11, where its tops and
              its rounds disagree by 30 and the median falls between; 17-30 under the
              declaration for Palatino and the Georgia and Times italics, whose declared
              value is their serif or stem tops, not the body
  cap         the H's top
  fig         the 0's yMax + yMin: its body, overshoot taken out; LINING when that is over
              0.85 of the cap, OLD-STYLE otherwise (Albo and Georgia are old-style)
  /xh /cap    center / xh, center / cap.  /fig_m: center / the figures' middle (fig / 2)
  lift        center - xh/2: units ABOVE the x-height's middle (the lowercase body's
              center line); lift/xh the same over the x-height

The reference set is the one the owner named: Georgia, Charter, Palatino, Times (Times.ttc,
Linotype's), Albertus Medium (roman only -- the family has no italic or bold here) and ITC
Berkeley Oldstyle, each in the cut that answers Albo's. Times New Roman is measured too and
printed, but kept OUT of the median so one design does not vote twice.
"""
import json, os, sys
import numpy as np, freetype
from fontTools.ttLib import TTFont
from fontTools.pens.statisticsPen import StatisticsPen

SUP = "/System/Library/Fonts/Supplemental/"; SYS = "/System/Library/Fonts/"; DL = os.path.expanduser("~/Downloads/")
BK = DL + "ITC Berkeley Oldstyle/ITC Berkeley Oldstyle "
CUTS = ("Regular", "Italic", "Bold", "BoldItalic")
LABEL = {"Regular": "R", "Italic": "I", "Bold": "B", "BoldItalic": "Z"}   # never "BI"
REFS = {   # (label, path, ttc index); every one of these is in the median
    "Regular": [("Georgia", SUP + "Georgia.ttf", 0), ("Charter", SUP + "Charter.ttc", 0),
                ("Palatino", SYS + "Palatino.ttc", 0), ("Times", SYS + "Times.ttc", 0),
                ("Albertus", DL + "Albertus Medium Regular.ttf", 0),
                ("Berkeley", BK + "Medium/ITC Berkeley Oldstyle Medium.otf", 0)],
    "Italic": [("Georgia", SUP + "Georgia Italic.ttf", 0), ("Charter", SUP + "Charter.ttc", 1),
               ("Palatino", SYS + "Palatino.ttc", 1), ("Times", SYS + "Times.ttc", 2),
               ("Berkeley", BK + "Medium Italic/ITC Berkeley Oldstyle Medium Italic.otf", 0)],
    "Bold": [("Georgia", SUP + "Georgia Bold.ttf", 0), ("Charter", SUP + "Charter.ttc", 3),
             ("Palatino", SYS + "Palatino.ttc", 2), ("Times", SYS + "Times.ttc", 1),
             ("Berkeley", BK + "Bold/ITC Berkeley Oldstyle Bold.otf", 0)],
    "BoldItalic": [("Georgia", SUP + "Georgia Bold Italic.ttf", 0), ("Charter", SUP + "Charter.ttc", 2),
                   ("Palatino", SYS + "Palatino.ttc", 3), ("Times", SYS + "Times.ttc", 3),
                   ("Berkeley", BK + "Bold Italic/ITC Berkeley Oldstyle Bold Italic.otf", 0)],
}
EXTRA = {   # printed, NOT in the median
    "Regular": [("TNR", SUP + "Times New Roman.ttf", 0)], "Italic": [("TNR", SUP + "Times New Roman Italic.ttf", 0)],
    "Bold": [("TNR", SUP + "Times New Roman Bold.ttf", 0)], "BoldItalic": [("TNR", SUP + "Times New Roman Bold Italic.ttf", 0)],
}
# the inventory: (class, char, name). The class is the dial that moves it (outlines/glyphs/
# marks.py and symbols.py, MID_DY); U+00AD is drawn but invisible until a line breaks on it.
GLYPHS = [("dot", "\u00b7", "middle dot"), ("bullet", "\u2022", "bullet"), ("bullet", "\u2219", "bullet operator"),
          ("dash", "-", "hyphen-minus"), ("dash", "\u2010", "hyphen"), ("dash", "\u2011", "nb hyphen"),
          ("dash", "\u00ad", "soft hyphen"), ("dash", "\u2012", "figure dash"), ("dash", "\u2013", "en dash"),
          ("dash", "\u2014", "em dash"), ("dash", "\u2015", "horiz bar"),
          ("math", "\u2212", "minus"), ("math", "+", "plus"), ("math", "=", "equal"), ("math", "\u00d7", "multiply"),
          ("math", "\u00f7", "divide"), ("math", "\u00b1", "plus-minus"), ("math", "\u2260", "not equal"),
          ("math", "\u2248", "almost equal"), ("math", "<", "less"), ("math", ">", "greater"),
          ("math", "\u2264", "less-equal"), ("math", "\u2265", "greater-equal"), ("math", "~", "tilde"),
          ("guil", "\u00ab", "guillemet L"), ("guil", "\u00bb", "guillemet R"), ("guil", "\u2039", "single guil L"),
          ("guil", "\u203a", "single guil R"),
          # measured for the record and NOT dialed: the arrows are symbols, not punctuation, and
          # the corpus's commonest symbol (the rightwards arrow, 2,583 uses). Of the references
          # only Times New Roman draws them (on its math axis), so they carry no median here
          ("arrow", "\u2192", "right arrow"), ("arrow", "\u2190", "left arrow"), ("arrow", "\u2194", "left-right arrow"),
          ("arrow", "\u21d2", "double arrow R"), ("misc", "\u00ac", "not sign"), ("misc", "\u221e", "infinity")]


XH_TOPS = "zu\u0131nm"   # flat or arched tops
XH_ROUNDS = "oecsa"      # yMin + yMax: the body with the overshoot taken out


def _box(face, ch):
    if not face.get_char_index(ch): return None
    face.load_char(ch, freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING)
    b = face.glyph.outline.get_bbox()
    return None if b.yMax <= b.yMin else (b.yMin, b.yMax)


def _centroid(tt, ch):
    gname = tt.getBestCmap().get(ord(ch))
    if gname is None: return None
    gs = tt.getGlyphSet(); p = StatisticsPen(glyphset=gs); gs[gname].draw(p)
    return p.meanY if p.area else None


def face_metrics(path, idx=0):
    f = freetype.Face(path, idx)
    est = [_box(f, c)[1] for c in XH_TOPS] + [sum(_box(f, c)) for c in XH_ROUNDS]
    xh = float(np.median(est)); cap = float(_box(f, "H")[1]); z0 = _box(f, "0")
    fig = float(z0[0] + z0[1])
    tt = TTFont(path, fontNumber=idx); os2 = tt["OS/2"]
    return dict(upm=f.units_per_EM, xh=xh, xh_est=est, os2_xh=getattr(os2, "sxHeight", None), cap=cap,
                fig=fig, fig_style="lining" if fig > 0.85 * cap else "old-style")


def measure(path, idx=0, label=""):
    m = face_metrics(path, idx); f = freetype.Face(path, idx); tt = TTFont(path, fontNumber=idx)
    marks = {}
    for cls, ch, name in GLYPHS:
        b = _box(f, ch)
        if b is None: continue
        ctr = (b[0] + b[1]) / 2.0; cen = _centroid(tt, ch)
        marks[ch] = dict(cls=cls, name=name, ymin=b[0], ymax=b[1], ctr=ctr, centroid=cen,
                         xh=ctr / m["xh"], cap=ctr / m["cap"], lift=ctr - m["xh"] / 2, lift_xh=(ctr - m["xh"] / 2) / m["xh"],
                         fig=ctr / (m["fig"] / 2))
    return dict(label=label, path=path, idx=idx, metrics=m, marks=marks)


def ref_set(cut, extra=False):
    out = []
    for l, p, i in REFS[cut] + (EXTRA[cut] if extra else []):
        if os.path.exists(p): out.append(measure(p, i, l))
    return out


def stats(vals):
    v = [x for x in vals if x is not None]
    return (float(np.median(v)), float(min(v)), float(max(v)), len(v)) if v else (None, None, None, 0)


def report(albo_dirs, as_json=None, refs_only=False):
    blob = {}
    for cut in CUTS:
        refs = ref_set(cut); extra = [r for r in ref_set(cut, True) if r["label"] == "TNR"]
        rows = [] if refs_only else [measure(os.path.join(d, f"Albo-{cut}.ttf"), 0, f"Albo {LABEL[cut]} {os.path.basename(os.path.normpath(d))}")
                                     for d in albo_dirs if os.path.exists(os.path.join(d, f"Albo-{cut}.ttf"))]
        print(f"\n==== {cut} ({LABEL[cut]}) " + "=" * 60)
        print(f"{'face':22s} {'xh':>6s} {'(z u i n m | o e c s a)':>52s} {'OS/2':>6s} {'cap':>6s} {'fig':>6s} style")
        for r in rows + refs + extra:
            m = r["metrics"]; e = " ".join(f"{v:.0f}" for v in m["xh_est"])
            print(f"{r['label']:22s} {m['xh']:6.0f} {e:>52s} {str(m['os2_xh']):>6s} {m['cap']:6.0f} {m['fig']:6.0f} {m['fig_style']}")
        print(f"\n{'glyph':16s} {'face':22s} {'ymin':>5s} {'ymax':>5s} {'ctr':>6s} {'/xh':>6s} {'/cap':>6s} {'lift':>6s} {'lift/xh':>8s} {'/fig_m':>6s}  centroid")
        cblob = {"albo": rows, "refs": refs, "extra": extra, "summary": {}}
        for cls, ch, name in GLYPHS:
            got = [(r["label"], r["marks"][ch]) for r in rows + refs + extra if ch in r["marks"]]
            if not got: continue
            for lab, k in got:
                cen = "" if k["centroid"] is None or abs(k["centroid"] - k["ctr"]) <= 3 else f"{k['centroid']:.1f}"
                print(f"U+{ord(ch):04X} {name:10s} {lab:22s} {k['ymin']:5.0f} {k['ymax']:5.0f} {k['ctr']:6.1f} {k['xh']:6.3f} {k['cap']:6.3f} "
                      f"{k['lift']:6.1f} {k['lift_xh']:8.3f} {k['fig']:6.3f}  {cen}")
            s = {q: stats([r["marks"][ch][q] if ch in r["marks"] else None for r in refs]) for q in ("xh", "cap", "lift_xh", "fig")}
            cblob["summary"][ch] = s
            if s["xh"][3]:
                print(f"{'':16s} {'refs median [range] n':22s} /xh {s['xh'][0]:.3f} [{s['xh'][1]:.3f}..{s['xh'][2]:.3f}] n={s['xh'][3]}"
                      f"   /cap {s['cap'][0]:.3f} [{s['cap'][1]:.3f}..{s['cap'][2]:.3f}]   lift/xh {s['lift_xh'][0]:+.3f}"
                      f"   /fig_m {s['fig'][0]:.3f}")
            print()
        blob[cut] = cblob
    if as_json:
        json.dump(blob, open(as_json, "w"), indent=1, default=float, ensure_ascii=False)
        print("wrote", as_json)
    return blob


SUMMARY = [("\u00b7", "middle dot"), ("\u2022", "bullet"), ("-", "hyphen"), ("\u2013", "en dash"), ("\u2014", "em dash"),
           ("\u2212", "minus"), ("+", "plus"), ("=", "equal"), ("\u00d7", "multiply"), ("\u00f7", "divide"),
           ("\u00ab", "guillemet"), ("\u2192", "right arrow")]


def summary(albo_dir):
    """The doc's two tables (markdown): each glyph's center over the x-height and over the cap
    height, Albo beside the references' median [range], per cut; then the same centers as Albo
    UNITS -- where each frame's median would put the mark in this cut."""
    per = {cut: (measure(os.path.join(albo_dir, f"Albo-{cut}.ttf"), 0, "Albo"), ref_set(cut)) for cut in CUTS}
    for q, title in (("xh", "center / x-height"), ("cap", "center / cap height")):
        print(f"\n| {title} | " + " | ".join(f"{LABEL[c]} Albo | {LABEL[c]} refs" for c in CUTS) + " |")
        print("|---|" + "---|---|" * len(CUTS))
        for ch, name in SUMMARY:
            cells = []
            for cut in CUTS:
                a, refs = per[cut]; v = [r["marks"][ch][q] for r in refs if ch in r["marks"]]
                cells.append(f"{a['marks'][ch][q]:.3f}" if ch in a["marks"] else "--")
                cells.append(f"{np.median(v):.3f} [{min(v):.3f}-{max(v):.3f}] n{len(v)}" if v else "--")
            print(f"| {name} U+{ord(ch):04X} | " + " | ".join(cells) + " |")
    print("\n| center, Albo units | " + " | ".join(f"{LABEL[c]} today | {LABEL[c]} xh-median | {LABEL[c]} cap-median" for c in CUTS) + " |")
    print("|---|" + "---|---|---|" * len(CUTS))
    for ch, name in SUMMARY:
        cells = []
        for cut in CUTS:
            a, refs = per[cut]; m = a["metrics"]
            vx = [r["marks"][ch]["xh"] for r in refs if ch in r["marks"]]; vc = [r["marks"][ch]["cap"] for r in refs if ch in r["marks"]]
            cells += [f"{a['marks'][ch]['ctr']:.0f}" if ch in a["marks"] else "--",
                      f"{np.median(vx) * m['xh']:.0f}" if vx else "--", f"{np.median(vc) * m['cap']:.0f}" if vc else "--"]
        print(f"| {name} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    a = sys.argv[1:]; js = None
    if "--summary" in a:
        summary([x for x in a if x != "--summary"][0]); sys.exit(0)
    if "--json" in a: i = a.index("--json"); js = a[i + 1]; del a[i:i + 2]
    ro = "--refs-only" in a; a = [x for x in a if x != "--refs-only"]
    report(a, js, ro)
