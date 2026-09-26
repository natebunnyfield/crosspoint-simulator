#!/usr/bin/env python3
"""Every LOCAL, non-VLM method on the five hardest pairs (docs/hard-pairs-eval-2026-09-26.md).

    $VENV/bin/python hard5_mech.py [--no-vision]  -> $HARD5_DIR/results_mech.json

Each method predicts d (units, on the 2026-09-20 zero) for each of the five
pairs, and NONE of them sees any reading of the pair it predicts:

  a  change nothing                 0
  b  shipped ridge (bench_fit)      the round-395 pipeline (4/4 floors, integer
                                    bearings, capital kerns) refit on the bench
                                    WITHOUT the pair; also printed: what the
                                    round-395 font actually carries (in-sample
                                    + his hand kerns -- NOT held out, context)
  c  B2 held out                    ridge on glyph identity + 38 shape features,
                                    bench + extras, refit without the pair
  d  classical optical              per-class target white (probe_fit m_optical:
                                    half depth-limited area, half 2-D gap), plus
                                    each measure alone
  e  vision add-on                  a FROZEN pretrained image encoder (DINOv2-small,
                                    SigLIP-base) embeds a picture of the pair at the
                                    zero; a ridge head (alpha by inner CV on the
                                    training rows only) maps embedding + style to d,
                                    trained on every OTHER pair he answered
  g2 B2 + vision ensemble           mean of c and the better-on-CV vision head

Also printed, for context on e: its 10-fold held-out error over ALL pairs he
answered, beside B2's on the same folds -- five pairs is an anecdote.
"""
import argparse, json, os, resource, time
import numpy as np
import freetype
from hard5_common import STYLES, SCRATCH, WS, all_readings  # sets sys.path
import bench_fit
import b2_fit
import features as FT

FONTS = FT.FONTS                       # the 2026-09-20 zero


def rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6   # macOS: bytes


def training_table(style):
    """{pair: mean of readings} exactly as the shipped B2 sees them."""
    J, W = b2_fit.combine(b2_fit.readings(style), 1.0)
    return J, W


# ------------------------------------------------------------------ b, d
def shipped_held(style, p):
    J = {q: d for q, d in bench_fit.judgments(style).items() if q != p}
    f = bench_fit.fit_judgments(J)
    return float(f["predict"](p)), float(f["predict_ridge"](p))


def optical_held(style, p, feats):
    J = {q: d for q, d in bench_fit.judgments(style).items() if q != p}
    c = bench_fit.pair_class(p)
    same = [q for q in J if bench_fit.pair_class(q) == c and q in feats]
    ta = np.median([feats[q]["area_x"] + J[q] for q in same])
    td = np.median([feats[q]["d2"] + J[q] for q in same])
    f = feats[p]
    return dict(mixed=float(0.5 * (ta - f["area_x"]) + 0.5 * (td - f["d2"])),
                area=float(ta - f["area_x"]), gap2d=float(td - f["d2"]), n_class=len(same))


# ------------------------------------------------------------------ e
def pair_image(face, hbfont, order, a, b, em=110, size=224):
    """The pair alone at the zero, HarfBuzz kern in, FreeType coverage, centred."""
    import uharfbuzz as hb
    face.set_pixel_sizes(0, em)
    buf = hb.Buffer(); buf.add_str(a + b); buf.guess_segment_properties()
    hb.shape(hbfont, buf, {"liga": False, "kern": True})
    s = em / 1000
    canvas = np.zeros((size * 2, size * 2), np.float32)
    pen = size * 0.5; base = size * 1.2
    for inf, pos in zip(buf.glyph_infos, buf.glyph_positions):
        face.load_glyph(inf.codepoint, freetype.FT_LOAD_RENDER)
        g = face.glyph; bm = g.bitmap
        if bm.rows:
            A = np.array(bm.buffer, np.uint8).reshape(bm.rows, bm.width) / 255.0
            x = int(round(pen + g.bitmap_left)); y = int(round(base - g.bitmap_top))
            canvas[y:y + bm.rows, x:x + bm.width] = np.maximum(canvas[y:y + bm.rows, x:x + bm.width], A)
        pen += pos.x_advance * s
    ys, xs = np.nonzero(canvas > 0.05)
    cy, cx = (ys.min() + ys.max()) // 2, (xs.min() + xs.max()) // 2
    crop = canvas[max(0, cy - size // 2):cy + size // 2, max(0, cx - size // 2):cx + size // 2]
    out = np.zeros((size, size), np.float32); out[:crop.shape[0], :crop.shape[1]] = crop
    return (255 - out * 255).astype(np.uint8)


def embed_all(items, which):
    """items: [(style, pair)]. Returns (E [n, d], seconds, download MB note)."""
    import torch
    from PIL import Image
    from transformers import AutoImageProcessor, AutoModel
    name = {"dinov2-small": "facebook/dinov2-small", "siglip-base": "google/siglip-base-patch16-224"}[which]
    t0 = time.time()
    proc = AutoImageProcessor.from_pretrained(name)
    model = AutoModel.from_pretrained(name).eval()
    if which == "siglip-base":
        enc = lambda px: model.vision_model(pixel_values=px).pooler_output
    else:
        enc = lambda px: (lambda o: torch.cat([o.last_hidden_state[:, 0], o.last_hidden_state[:, 1:].mean(1)], 1))(model(pixel_values=px))
    load_s = time.time() - t0
    faces = {s: (freetype.Face(FONTS[s]), FT.Font(FONTS[s])) for s in STYLES}
    imgs = []
    for s, p in items:
        face, F = faces[s]
        imgs.append(Image.fromarray(pair_image(face, F.hb, F.order, p[0], p[1])).convert("RGB"))
    t1 = time.time(); E = []
    with torch.no_grad():
        for i in range(0, len(imgs), 32):
            px = proc(images=imgs[i:i + 32], return_tensors="pt")["pixel_values"]
            E.append(enc(px).float().numpy())
    return np.vstack(E), load_s, time.time() - t1, imgs


def head_fit(X, y):
    from sklearn.linear_model import RidgeCV
    from sklearn.preprocessing import StandardScaler
    sc = StandardScaler().fit(X)
    m = RidgeCV(alphas=np.logspace(0, 5, 21), cv=5).fit(sc.transform(X), y)
    return lambda Z: m.predict(sc.transform(Z)), float(m.alpha_)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--no-vision", action="store_true")
    args = ap.parse_args()
    sel = json.load(open(os.path.join(SCRATCH, "selection.json")))["top5"]
    fonts = {s: FT.Font(p) for s, p in FONTS.items()}
    res = dict(pairs=[], timing={}, notes={})
    t = time.time()
    feats = {}
    for s in STYLES:
        need = set(bench_fit.judgments(s)) | {x["pair"] for x in sel if x["style"] == s}
        feats[s] = {p: FT.pair_features(fonts[s], p[0], p[1], s == "italic")[0] for p in need}
    res["timing"]["features_s"] = round(time.time() - t, 2)
    for x in sel:
        s, p = x["style"], x["pair"]
        t = time.time(); sh, sh_ridge = shipped_held(s, p); tb = time.time() - t
        t = time.time(); op = optical_held(s, p, feats[s]); td = time.time() - t
        res["pairs"].append(dict(style=s, pair=p, his=x["his"], readings=x["readings"],
                                 spread=x["spread"], a_nothing=0.0, b_shipped_held=sh,
                                 b_shipped_ridge_cont=round(sh_ridge, 1), c_b2_held=x["b2_held"],
                                 d_optical=round(op["mixed"], 1), d_area=round(op["area"], 1),
                                 d_gap2d=round(op["gap2d"], 1)))
        res["timing"].setdefault("b_s", []).append(round(tb, 3))
        res["timing"].setdefault("d_s", []).append(round(td, 4))
    if not args.no_vision:
        items, y, st = [], [], []
        for s in STYLES:
            J, _ = training_table(s)
            for p, d in J.items():
                items.append((s, p)); y.append(d); st.append(float(s == "italic"))
        for x in sel:
            if (x["style"], x["pair"]) not in items:
                items.append((x["style"], x["pair"])); y.append(np.nan); st.append(float(x["style"] == "italic"))
        y = np.array(y); st = np.array(st)[:, None]
        for which in ("dinov2-small", "siglip-base"):
            E, load_s, emb_s, imgs = embed_all(items, which)
            X = np.hstack([E, st])
            if which == "dinov2-small":
                os.makedirs(os.path.join(SCRATCH, "vision_inputs"), exist_ok=True)
                for (s, p), im in zip(items, imgs):
                    if any(s == z["style"] and p == z["pair"] for z in sel):
                        im.save(os.path.join(SCRATCH, "vision_inputs", f"{s}_{p.replace(chr(39), 'apos')}.png"))
            # leave-pair-out for the five
            t = time.time()
            for r in res["pairs"]:
                k = items.index((r["style"], r["pair"]))
                tr = [i for i in range(len(items)) if items[i][1] != r["pair"] and not np.isnan(y[i])]  # both styles out
                f, alpha = head_fit(X[tr], y[tr])
                r[f"e_{which}"] = round(float(f(X[[k]])[0]), 1)
                r[f"e_{which}_alpha"] = alpha
            head_s = (time.time() - t) / len(res["pairs"])
            # context: 10-fold over every answered pair, B2 on the SAME folds
            ok = np.nonzero(~np.isnan(y))[0]
            rng = np.random.default_rng(20260926); perm = rng.permutation(ok)
            ev, eb = [], []
            for fo in range(10):
                held = set(perm[fo::10].tolist()); tr = [i for i in ok if i not in held]
                f, _ = head_fit(X[tr], y[tr])
                ev += list(np.abs(f(X[sorted(held)]) - y[sorted(held)]))
                if which == "dinov2-small":
                    for s in STYLES:
                        Hs = {items[i][1] for i in held if items[i][0] == s}
                        R = {q: v for q, v in b2_fit.readings(s).items() if q not in Hs}
                        Jt, Wt = b2_fit.combine(R, 1.0)
                        fe = {q: FT.pair_features(fonts[s], q[0], q[1], s == "italic")[0]
                              for q in set(Jt) | Hs if q not in feats[s]}
                        feats[s].update(fe)
                        pr = b2_fit.fit(s, {q: v for q, v in Jt.items()}, feats[s], Wt)[2]
                        eb += [abs(pr(items[i][1]) - y[i]) for i in held if items[i][0] == s]
            res["notes"][which] = dict(load_s=round(load_s, 1), embed_s_per_image=round(emb_s / len(items), 4),
                                       n_images=len(items), head_fit_s=round(head_s, 2),
                                       cv10_all_pairs=round(float(np.mean(ev)), 2), rss_mb=round(rss_mb()))
            if eb:
                res["notes"]["b2_cv10_same_folds"] = round(float(np.mean(eb)), 2)
                res["notes"]["nothing_all_pairs"] = round(float(np.mean(np.abs(y[ok]))), 2)
            print(which, res["notes"][which], flush=True)
        best = min(("dinov2-small", "siglip-base"), key=lambda w: res["notes"][w]["cv10_all_pairs"])
        res["notes"]["ensemble_uses"] = best
        for r in res["pairs"]:
            r["g2_b2_plus_vision"] = round(0.5 * r["c_b2_held"] + 0.5 * r[f"e_{best}"], 1)
    res["notes"]["peak_rss_mb"] = round(rss_mb())
    json.dump(res, open(os.path.join(SCRATCH, "results_mech.json"), "w"), indent=1)
    cols = [k for k in res["pairs"][0] if k[:2] in ("a_", "b_", "c_", "d_", "e_", "g2") and not k.endswith("alpha")]
    print(f"{'pair':10s} {'his':>6s} " + " ".join(f"{c[:14]:>14s}" for c in cols))
    for r in res["pairs"]:
        print(f"{r['style'][:3]} {r['pair']:6s} {r['his']:+6.1f} " + " ".join(f"{r[c]:+14.1f}" for c in cols))
    print("MAE      " + " " * 7 + " ".join(f"{np.mean([abs(r[c] - r['his']) for r in res['pairs']]):14.1f}" for c in cols))
    print(json.dumps(res["notes"], indent=1), json.dumps(res["timing"]))


if __name__ == "__main__":
    main()
