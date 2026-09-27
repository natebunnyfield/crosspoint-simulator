"""Would the fit metric have found the letters he has already fixed?

Each case is a letter the owner ruled on, with the build BEFORE the fix and
the build after it (both rebuilt from `git archive <commit>` so nothing is
taken from a stale file). The metric is run on the pre-fix build WITHOUT the
spacing axis (f) -- his spacing answers postdate most of these fixes, and
using them would be hindsight -- and the case counts as CAUGHT when the
letter scores F >= 2.0 in its own cut. Also reported: its rank in that cut,
its score after the fix, and the reason axis.

Negative controls: the letters he APPROVED (approved.json) and the two fixes
he REJECTED and had reverted (round 224's roman Q tail and S, undone in 225).

    python3 validate.py --geom g.json --legib l.json --out validation.json
"""
import argparse, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score as S  # noqa: E402

# (pre, post, cut, letters, source)
FIXED = [
    ("r393", "r395", "Italic", "bdpqasy6", "round 395, his thick/thin slider picks"),
    ("r393", "r395", "Regular", "xYe38", "round 395, his thick/thin slider picks"),
    ("r392", "r393", "Regular", "R", "round 393, the roman R takes the Bold R's balance"),
    ("r392", "r393", "BoldItalic", "j", "round 393, the bold italic j head"),
    ("r390", "r391", "Italic", "hmnru", "round 391, the italic arch hairline"),
    ("r390", "r391", "Regular", "sty", "round 391, roman hairline floors"),
    ("r397", "r398", "BoldItalic", "g", "round 398, the Bold Italic g on the weight axis"),
    ("r399", "r400", "Regular", "e", "round 400, the e read as o"),
    ("r372", "r373", "Regular", "XI", "round 373, his X width and I wedges"),
    ("r372", "r373", "Italic", "f", "round 373, his italic f"),
    ("r377", "r378", "Italic", "4", "round 378, the italic 4 heavier"),
    ("r377", "r378", "BoldItalic", "4", "round 378, the italic 4 heavier"),
    ("r377", "r378", "Bold", "457", "round 378, Bold figure widths"),
    ("r223", "r224", "Regular", "X", "round 224, kept"),
    ("r223", "r224", "Italic", "zAk", "round 224, kept"),
]
REJECTED = [("r223", "Regular", "QS", "round 224's Q tail and S, reverted by him in round 225")]
APPROVED = [("Regular", "g"), ("Italic", "g")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geom", required=True)
    ap.add_argument("--legib", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--variants", action="store_true")
    a = ap.parse_args()
    if a.variants:
        return variants(a)
    geom, legib = json.load(open(a.geom)), json.load(open(a.legib))
    tags = sorted({c[0] for c in FIXED} | {c[1] for c in FIXED} | {"r223", "r402"})
    scored = {t: S.score_tag(geom, legib, None, t) for t in tags}

    def look(tag, cut, ch):
        R = scored[tag].get(cut)
        if not R or ch not in R:
            return None
        order = sorted(R, key=lambda c: -R[c]["F"])
        r = R[ch]
        return dict(F=round(r["F"], 2), rank=order.index(ch) + 1, of=len(R), flag=bool(r["flag"]),
                    reason=f"{r['reason']}:{r['axes'][r['reason']]['by']}",
                    axes={k: round(v["z"], 2) for k, v in r["axes"].items()})

    out = {"fixed": [], "rejected": [], "approved": [], "base_rate": {}}
    caught = total = 0
    for pre, post, cut, letters, src in FIXED:
        for ch in letters:
            b, af = look(pre, cut, ch), look(post, cut, ch)
            if b is None:
                continue
            total += 1; caught += b["flag"]
            out["fixed"].append(dict(case=f"{cut} {ch}", pre=pre, post=post, source=src, before=b, after=af))
            print(f"{'CAUGHT' if b['flag'] else 'missed':6s} {cut:10s} {ch}  {pre}: F {b['F']:5.2f} rank {b['rank']:2d}/{b['of']} "
                  f"[{b['reason']}]  ->  {post}: F {af['F']:5.2f} rank {af['rank']:2d}   ({src})")
    ranks = [c["before"]["rank"] / c["before"]["of"] for c in out["fixed"]]
    print(f"\nCAUGHT {caught} of {total} fixed letters at F >= {S.FLAG}; "
          f"median pre-fix rank percentile {np.median(ranks):.0%} (chance 50%)")
    top10 = sum(c["before"]["rank"] <= 10 for c in out["fixed"])
    print(f"in the pre-fix build's top 10 of its cut: {top10} of {total}")
    drop = [c["before"]["F"] - c["after"]["F"] for c in out["fixed"] if c["after"]]
    print(f"score fell after the fix in {sum(d > 0 for d in drop)} of {len(drop)} (median change {-np.median(drop):+.2f})")
    out["summary"] = dict(caught=caught, total=total, median_rank_pct=float(np.median(ranks)), top10=top10,
                          fell=int(sum(d > 0 for d in drop)))
    # base rate: fraction of ALL glyphs flagged in each pre-fix cut used
    for pre, post, cut, letters, src in FIXED:
        R = scored[pre].get(cut)
        if R:
            out["base_rate"][f"{pre}/{cut}"] = round(sum(r["flag"] for r in R.values()) / len(R), 3)
    br = list(out["base_rate"].values())
    print(f"base flag rate in those cuts: median {np.median(br):.0%} (so chance would catch ~{np.median(br) * total:.1f} of {total})")
    for tag, cut, letters, src in REJECTED:
        for ch in letters:
            b = look(tag, cut, ch)
            out["rejected"].append(dict(case=f"{cut} {ch}", tag=tag, source=src, before=b))
            print(f"REJECTED-FIX control {cut} {ch} at {tag}: F {b['F']:.2f} flag {b['flag']} [{b['reason']}]")
    for cut, ch in APPROVED:
        for tag in ("r393", "r397", "r402"):
            b = look(tag, cut, ch)
            if b:
                out["approved"].append(dict(case=f"{cut} {ch}", tag=tag, **b))
                print(f"APPROVED control {cut} {ch} at {tag}: F {b['F']:.2f} flag {b['flag']} [{b['reason']}]")
    json.dump(out, open(a.out, "w"), indent=1)


def variants(a):
    """The sensitivity table: does the catch survive other reasonable choices?"""
    geom, legib = json.load(open(a.geom)), json.load(open(a.legib))
    tags = sorted({c[0] for c in FIXED} | {"r223", "r402"})
    rows = []
    for refnorm in ("full", "diff", "none"):
        for flag in (1.5, 2.0, 2.5):
            S.REFNORM, S.FLAG = refnorm, flag
            sc = {t: S.score_tag(geom, legib, None, t) for t in tags}
            got = tot = top10 = 0
            base = []
            for pre, post, cut, letters, src in FIXED:
                R = sc[pre].get(cut)
                if not R:
                    continue
                base.append(np.mean([r["F"] >= flag for r in R.values()]))
                order = sorted(R, key=lambda c: -R[c]["F"])
                for ch in letters:
                    tot += 1; got += R[ch]["F"] >= flag; top10 += order.index(ch) < 10
            ctrl = sum(sc["r223"]["Regular"][c]["F"] >= flag for c in "QS") + \
                sum(sc["r402"][cut]["g"]["F"] >= flag for cut in ("Regular", "Italic"))
            br = float(np.median(base))
            rows.append(dict(refnorm=refnorm, flag=flag, caught=got, of=tot, top10=top10,
                             base=round(br, 3), chance=round(br * tot, 1), controls_flagged=int(ctrl)))
            print(f"{refnorm:5s} F>={flag}: caught {got}/{tot}, top10 {top10}, base rate {br:.0%} "
                  f"(chance {br * tot:.1f}), controls flagged {ctrl}/4")
    S.REFNORM, S.FLAG = "full", 2.0
    json.dump(rows, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
