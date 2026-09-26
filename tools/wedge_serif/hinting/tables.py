#!/usr/bin/env python3
"""Summary tables from measure.py / gate_sweep.py / kli_arms.py / reader_read.py.

    python3 tables.py --res DIR --html out.html --md out.md
"""
import argparse, json, os

ARMS = ["today", "ttfa-q", "ttfa-n", "ttfa-s", "light", "nohint"]
NAME = {"today": "TODAY", "ttfa-q": "TTFA default (qsq)", "ttfa-n": "TTFA natural (nnn)",
        "ttfa-s": "TTFA strong (sss)", "light": "LIGHT", "nohint": "NO HINTING"}
READER = ["8pt", "10pt", "12pt", "14pt", "16pt", "18pt"]
TWOX = ["10pt@2x", "12pt@2x", "14pt@2x", "16pt@2x", "18pt@2x"]


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def tab(title, header, rows):
    return title, header, rows


def build(res):
    m = json.load(open(os.path.join(res, "measure.json")))
    g = json.load(open(os.path.join(res, "gate.json")))
    kli = {}
    for f in ("kli-flags0.json", "kli-nohint.json", "kli-light.json"):
        p = os.path.join(res, f)
        if os.path.exists(p):
            kli.update(json.load(open(p))["summary"])
    rd = json.load(open(os.path.join(res, "reader.json"))) if os.path.exists(os.path.join(res, "reader.json")) else {}
    kmap = {"today": "today", "ttfa-q": "ttfaq", "ttfa-n": "ttfan", "light": "light", "nohint": "nohint"}
    out = []
    # 1 legibility
    rows = []
    for a in ARMS:
        k = kmap.get(a)
        R, I = kli.get(f"{k} R"), kli.get(f"{k} I")
        rows.append([NAME[a],
                     f"{R['grand']*100:.1f}" if R else "-", f"{R['crowded']*100:.1f}" if R else "-",
                     str(R["e_o"]) if R else "-", str(R.get("tess_e_o", "-")) if R else "-",
                     f"{I['grand']*100:.1f}" if I else "-", str(I["e_o"]) if I else "-",
                     f"{g[a]['verdict']} {g[a]['worst8']:.3f}"])
    rows.append(["Georgia (ref)", f"{kli['Georgia']['grand']*100:.1f}", f"{kli['Georgia']['crowded']*100:.1f}",
                 str(kli["Georgia"]["e_o"]), "0", "", "", ""])
    out.append(tab("Kept Legibility Index (v3.1, 9-26 px, 8-bit) and the e hint gate (8-12 ppem)",
                   ["arm", "roman grand", "roman crowded", "roman e>o Vision", "roman e>o Tesseract",
                    "italic grand", "italic e>o", "e gate (worst mouth_block)"], rows))
    # 2 reader-size Vision
    if rd:
        rows = []
        for a in ["today", "ttfa-q", "light", "nohint"]:
            for s in ("Regular", "Italic"):
                d = rd[a][s]
                rows.append([f"{NAME[a]} {s[0]}", f"{d['9px']['acc']*100:.1f}",
                             f"{min(d[k]['acc'] for k in READER)*100:.2f}",
                             f"{mean([d[k]['acc'] for k in READER])*100:.2f}",
                             f"{min(d[k]['acc'] for k in TWOX)*100:.2f}",
                             str(sum(d[k]['e_o'] for k in READER + TWOX))])
        out.append(tab("Apple Vision on the converter's own 2-bit pixels (index corpus, 4 shuffles per size)",
                       ["arm", "9 px", "1x worst", "1x mean", "2x worst", "e>o at reader sizes"], rows))
    # 3 colour, stems, alignment at 1x
    for style in ("Regular", "Italic"):
        rows = []
        for a in ARMS:
            d = m[a][style]
            rows.append([NAME[a],
                         " ".join(f"{d[k]['colour']:.2f}" for k in READER),
                         f"{mean([d[k]['colour_letter_sd'] for k in READER]):.3f}",
                         " ".join(str(d[k]["stem_shapes"]) for k in READER),
                         " ".join(f"{d[k]['stem_spread']:.2f}" for k in READER),
                         f"{mean([d[k]['align'].get('top_flat', {}).get('crisp') for k in READER] + [d[k]['align'].get('bot_flat', {}).get('crisp') for k in READER]):.2f}",
                         f"{mean([d[k]['align'].get('top_round', {}).get('crisp') for k in READER] + [d[k]['align'].get('bot_round', {}).get('crisp') for k in READER]):.2f}",
                         f"{max(max(d[k]['align'].get(gp, {}).get('spread', 0) for gp in ('top_flat', 'bot_flat')) for k in READER):.2f}"])
        out.append(tab(f"{style}, the six reader sizes at 1x (8 10 12 14 16 18 pt = 16.7-37.5 ppem)",
                       ["arm", "colour vs outline, per size", "per-letter colour sd", "stem shapes, per size",
                        "stem spread px, per size", "flat edge crisp", "round edge crisp", "flat edge spread px (worst)"], rows))
        rows = []
        for a in ARMS:
            d = m[a][style]
            rows.append([NAME[a], " ".join(f"{d[k]['colour']:.2f}" for k in TWOX),
                         " ".join(str(d[k]["stem_shapes"]) for k in TWOX),
                         f"{mean([d[k]['align'].get('top_flat', {}).get('crisp') for k in TWOX] + [d[k]['align'].get('bot_flat', {}).get('crisp') for k in TWOX]):.2f}"])
        out.append(tab(f"{style}, the 2x tier, 10-18 pt drawn at 20-36 pt = 41.7-75 ppem (its 8 pt is 16 pt at 1x, already above)",
                       ["arm", "colour vs outline", "stem shapes", "flat edge crisp"], rows))
    return out


def to_html(tabs):
    s = []
    for title, hdr, rows in tabs:
        s.append(f"<h2>{title}</h2><table><tr>" + "".join(f"<th>{h}</th>" for h in hdr) + "</tr>")
        for r in rows:
            s.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
        s.append("</table>")
    return "\n".join(s)


def to_md(tabs):
    s = []
    for title, hdr, rows in tabs:
        s.append(f"**{title}**\n")
        s.append("| " + " | ".join(hdr) + " |")
        s.append("|" + "---|" * len(hdr))
        for r in rows:
            s.append("| " + " | ".join(r) + " |")
        s.append("")
    return "\n".join(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", required=True)
    ap.add_argument("--html")
    ap.add_argument("--md")
    a = ap.parse_args()
    t = build(a.res)
    if a.html:
        open(a.html, "w").write(to_html(t))
    if a.md:
        open(a.md, "w").write(to_md(t))
    print(to_md(t))


if __name__ == "__main__":
    main()
