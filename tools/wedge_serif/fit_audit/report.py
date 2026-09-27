"""Markdown tables for the doc from a scored fit JSON (score.py --out).

    python3 report.py fit.json legib.json TAG > tables.md
"""
import json, sys

sys.path.append(__import__("os").path.dirname(__file__))
from common import CUTS, LC, UC, FIG  # noqa: E402
from score import AXES  # noqa: E402

NAMES = {k: v[0] for k, v in AXES.items()}


def why(r, n=2):
    ranked = sorted(r["axes"].items(), key=lambda kv: -AXES[kv[0]][2] * max(0, abs(kv[1]["z"]) - 1) ** 2)
    out = []
    for k, v in ranked[:n]:
        if abs(v["z"]) <= 1:
            break
        out.append(f"{NAMES[k]} {v['z']:+.1f} ({v['by']})")
    return "; ".join(out) or "--"


def main():
    F = json.load(open(sys.argv[1])); L = json.load(open(sys.argv[2])); tag = sys.argv[3]
    for cut in CUTS:
        R = F[cut]
        order = sorted(R, key=lambda c: -R[c]["F"])
        print(f"\n#### {cut}: {sum(R[c]['flag'] for c in R)} of {len(R)} flagged\n")
        print("| rank | glyph | F | a col | b str | c prop | d vert | e bear | f spc | g leg | h x-cut | why (top two axes past 1 sigma) |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for i, c in enumerate(order[:20]):
            r = R[c]
            cells = " | ".join(f"{r['axes'][k]['z']:+.1f}" if k in r["axes"] else "n/a" for k in "abcdefgh")
            print(f"| {i + 1} | **{c}**{' FLAG' if r['flag'] else ''} | {r['F']:.2f} | {cells} | {why(r)} |")
        print("\nFull order, worst first: " + " ".join(order))


if __name__ == "__main__":
    main()
