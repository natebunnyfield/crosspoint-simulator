#!/usr/bin/env python3
"""Score every method on the hard five: one table, position-bias checks.

    $VENV/bin/python hard5_score.py [--model qwen3-vl-8b-instruct-mlx]
    -> $HARD5_DIR/results.json and a printed table
"""
import argparse, collections, json, os
import numpy as np
from hard5_common import SCRATCH


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--model", default="qwen3-vl-8b-instruct-mlx")
    args = ap.parse_args()
    M = json.load(open(os.path.join(SCRATCH, "results_mech.json")))
    V = json.load(open(os.path.join(SCRATCH, "results_vlm-" + args.model + ".json")))
    rows = M["pairs"]
    for r in rows:
        lad = [x for x in V["ladder"] if x["pair"] == r["pair"] and x["style"] == r["style"] and x["est"] is not None]
        r["f_vlm_ladder"] = round(float(np.mean([x["est"] for x in lad])), 1) if lad else None
        r["f_vlm_ladder_calls"] = [(x["variant"], x["scale"], x["order"], x["label"], x["est"]) for x in lad]
        mix = [x for x in V["mixed"] if x["pair"] == r["pair"] and x["style"] == r["style"] and x["est"] is not None]
        r["g1_b2_top3_vlm"] = round(float(np.mean([x["est"] for x in mix])), 1) if mix else None
        r["g1_calls"] = [(x["variant"], x["order"], x["label"], x["est"]) for x in mix]
    cols = ["a_nothing", "b_shipped_held", "c_b2_held", "d_optical", "d_area", "d_gap2d",
            "e_dinov2-small", "e_siglip-base", "f_vlm_ladder", "g1_b2_top3_vlm", "g2_b2_plus_vision"]
    mae = {c: round(float(np.mean([abs(r[c] - r["his"]) for r in rows])), 1) for c in cols}
    print(f"{'pair':10s} {'his':>6s} {'spread':>6s} " + " ".join(f"{c[:12]:>12s}" for c in cols))
    for r in rows:
        print(f"{r['style'][:3]} {r['pair']:6s} {r['his']:+6.1f} {r['spread']:6.0f} "
              + " ".join(f"{r[c]:+12.1f}" for c in cols))
    print(f"{'MAE':24s}" + " ".join(f"{mae[c]:12.1f}" for c in cols))

    # ---- position bias
    bias = {}
    lad = [x for x in V["ladder"] if x["label"]]
    bias["ladder_label_counts"] = dict(collections.Counter(x["label"] for x in lad))
    bias["ladder_first_shown_share"] = round(np.mean([x["pos"] == 0 for x in lad]), 2)
    pairs = collections.defaultdict(dict)
    for x in V["ladder"]:
        pairs[(x["n"], x["variant"], x["scale"])][x["order"]] = x["label"]
    agree = [v["AtoI"] == v["ItoA"] for v in pairs.values() if v.get("AtoI") and v.get("ItoA")]
    bias["ladder_order_reversal_agreement"] = f"{sum(agree)}/{len(agree)}"
    bias["ladder_no_answer_first_pass"] = sum(1 for x in V["ladder"] if x.get("retry"))
    mix = [x for x in V["mixed"] if x["label"]]
    bias["mixed_first_shown_share"] = round(np.mean([x["pos"] == 0 for x in mix]), 2)
    mp = collections.defaultdict(dict)
    for x in V["mixed"]:
        mp[(x["n"], x["variant"])][x["order"]] = x["label"]
    ag = [v["fwd"] == v["rev"] for v in mp.values() if v.get("fwd") and v.get("rev")]
    bias["mixed_order_reversal_agreement"] = f"{sum(ag)}/{len(ag)}"
    afc = [x for x in V["afc"] if x["answer"]]
    bias["afc_answer_counts"] = dict(collections.Counter(x["answer"] for x in afc))
    bias["afc_no_answer_first_pass"] = sum(1 for x in V["afc"] if x.get("retry"))
    for other in ("zero", "B2-held", "r395"):
        for ident in (False, True):
            s = [x for x in afc if x["other"] == other and x["identical"] == ident]
            if s:
                bias[f"afc_vs_{other}{'_IDENTICAL' if ident else ''}_chose_his"] = \
                    f"{sum(x['chose'] == 'his' for x in s)}/{len(s)}"
    print(json.dumps(bias, indent=1))
    t = dict(ladder_median_s=float(np.median([x["sec"] for x in V["ladder"]])),
             mixed_median_s=float(np.median([x["sec"] for x in V["mixed"]])),
             afc_median_s=float(np.median([x["sec"] for x in V["afc"]])), lms_rss_mb=V["rss_mb"])
    print(json.dumps(t))
    json.dump(dict(rows=rows, mae=mae, bias=bias, vlm_timing=t, mech_notes=M["notes"], mech_timing=M["timing"]),
              open(os.path.join(SCRATCH, "results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
