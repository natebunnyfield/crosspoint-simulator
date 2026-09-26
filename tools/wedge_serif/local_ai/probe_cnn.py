#!/usr/bin/env python3
"""A tiny image model trained on HIS bench answers with MLX, held out.

PROBE for docs/local-ai-spacing-options-2026-09-26.md, option B's image arm.
Input: the shaped pair on the bench's own fonts, rasterized with FreeType
coverage at 16 design units per pixel (a 62 px em, a little above the phone's
54 px), cropped 64 x 80 px around the gap, the left and right glyph in separate
channels, plus the style flag.  Output: his d, in units.  Loss: Huber.

Same folds as bench_fit.py --cv, but only the FIRST shuffle (10 fits), because
the image model is the slow one; the matching first-shuffle numbers of the
shipped pipeline and the hybrid are printed beside it so the comparison is
like for like.  Seeds fixed.  Architecture and epochs fixed before the run.

    $VENV/bin/python probe_cnn.py
"""
import json, os, sys, time
import numpy as np
import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import bench_fit  # noqa: E402
import features as FT  # noqa: E402
import probe_fit as PF  # noqa: E402
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.transformPen import TransformPen

UPX = 16.0
CW, CH = 64, 80
EPOCHS, LR, WD, BATCH = 120, 2e-3, 1e-3, 32


def crop(F, a, b):
    names, adv, kern = F.shape(a, b)
    f = FT.pair_features(F, a, b, False)[0]
    # centre on the gap: halfway across the bbox white after A's right ink edge
    mid = F.tt["glyf"][names[0]].xMax + f["h_gap"] / 2
    x_left = mid - CW * UPX / 2
    out = []
    for name, dx in ((names[0], 0), (names[1], adv + kern)):
        pen = FreeTypePen(F.gs)
        F.gs[name].draw(TransformPen(pen, (1, 0, 0, 1, dx - x_left, 300)))
        out.append(pen.array(width=CW, height=CH, transform=(1 / UPX, 0, 0, 1 / UPX, 0, 0)))
    return np.stack(out, -1).astype(np.float32)


class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.c1 = nn.Conv2d(2, 16, 5, padding=2)
        self.c2 = nn.Conv2d(16, 32, 3, padding=1)
        self.c3 = nn.Conv2d(32, 32, 3, padding=1)
        self.fc1 = nn.Linear(32 * 10 * 8 + 1, 64)
        self.fc2 = nn.Linear(64, 1)
        self.drop = nn.Dropout(0.3)

    def __call__(self, x, s):
        pool = lambda t: nn.MaxPool2d(2, 2)(t)
        x = pool(nn.relu(self.c1(x)))
        x = pool(nn.relu(self.c2(x)))
        x = pool(nn.relu(self.c3(x)))
        x = x.reshape(x.shape[0], -1)
        x = mx.concatenate([x, s], 1)
        return self.fc2(self.drop(nn.relu(self.fc1(x)))).squeeze(-1)


def train_predict(Xtr, Str, ytr, Xte, Ste, seed):
    mx.random.seed(seed); rng = np.random.default_rng(seed)
    net = Net(); opt = optim.AdamW(learning_rate=LR, weight_decay=WD)
    ysc = 20.0

    def loss(m, x, s, y):
        return nn.losses.huber_loss(m(x, s), y / ysc, delta=1.0, reduction="mean")
    lg = nn.value_and_grad(net, loss)
    Xtr, Str, ytr = mx.array(Xtr), mx.array(Str), mx.array(ytr)
    n = Xtr.shape[0]
    net.train()
    for _ in range(EPOCHS):
        perm = rng.permutation(n)
        for i in range(0, n, BATCH):
            idx = mx.array(perm[i:i + BATCH])
            _, g = lg(net, Xtr[idx], Str[idx], ytr[idx])
            opt.update(net, g); mx.eval(net.parameters(), opt.state)
    net.eval()
    return np.array(net(mx.array(Xte), mx.array(Ste))) * ysc


def main():
    t0 = time.time()
    fonts = {s: FT.Font(p) for s, p in FT.FONTS.items()}
    J = {s: bench_fit.judgments(s) for s in PF.STYLES}
    img = {s: {p: crop(fonts[s], p[0], p[1]) for p in J[s]} for s in PF.STYLES}
    print(f"rendered {sum(len(v) for v in img.values())} crops in {time.time()-t0:.1f}s")
    FO = PF.folds()
    errs, errs_ship, errs_hyb = [], [], []
    t1 = time.time()
    for i in range(PF.K):
        held = {s: FO[s][i][2] for s in PF.STYLES}          # repeat 0
        tr = [(s, p) for s in PF.STYLES for p in J[s] if p not in held[s]]
        te = [(s, p) for s in PF.STYLES for p in held[s]]
        Xtr = np.stack([img[s][p] for s, p in tr]); Str = np.array([[float(s == "italic")] for s, _ in tr], np.float32)
        ytr = np.array([J[s][p] for s, p in tr], np.float32)
        Xte = np.stack([img[s][p] for s, p in te]); Ste = np.array([[float(s == "italic")] for s, _ in te], np.float32)
        pr = train_predict(Xtr, Str, ytr, Xte, Ste, seed=i)
        train = {s: {p: d for p, d in J[s].items() if p not in held[s]} for s in PF.STYLES}
        ship = PF.m_shipped(train); hyb = PF.m_hybrid(train)
        for (s, p), v in zip(te, pr):
            errs.append(abs(v - J[s][p])); errs_ship.append(abs(ship(s, p) - J[s][p]))
            errs_hyb.append(abs(hyb(s, p) - J[s][p]))
    dt = time.time() - t1
    print(f"first shuffle, 10 folds, {len(errs)} held-out judgments:")
    print(f"   MLX CNN on pair images      {np.mean(errs):6.2f}   ({dt:.0f}s for 10 fits, {dt/10:.1f}s per fit)")
    print(f"   shipped ridge pipeline      {np.mean(errs_ship):6.2f}")
    print(f"   hybrid identity+features    {np.mean(errs_hyb):6.2f}")
    print(f"   do nothing                  {np.mean([abs(J[s][p]) for s in PF.STYLES for p in J[s]]):6.2f}")


if __name__ == "__main__":
    main()
