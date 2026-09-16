"""Drive a letter's counter toward the SCAN's counter, over several passes.

Round 133, owner: *"match a and e to scans better. take multiple passes."*
Each pass builds the font, measures the letter's counter with
`cmp_aldine_counter` -- the same code that reads the scan -- and moves one
dial if it helps. It stops when no dial helps.

    python3 aldine_fit_counter.py a '{"ALBO_ALD_A_CTR_H":[290,200,380,15], ...}'

The score is a weighted L1 over the shape numbers that survive a shear and a
54 px photograph: how much of the letter's black the hole takes back, its
proportion, its FILL (an ellipse 0.79, a triangle 0.50 -- the number that says
teardrop), where its widest row sits, its floor, and the ten-row silhouette.
The silhouette carries half the weight, because everything else can be right
while the shape is wrong.
"""
import os, sys, json, subprocess, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cmp_aldine_counter as CC

BASE = dict(os.environ, ALBO_ITALIC="aldine", FJORD_STEM="66.9", FJORD_CONTRAST="0.892",
            FJORD_WIDTH="95", FJORD_SLANT="13", PYTHON_GIL="0")
W = dict(area_ink=3.0, wh=1.5, fill=4.0, widest=1.5, floor=2.0, h_ink=1.5,
         ink_wh=3.0, profile=5.0)


def score(target, got):
    if not got: return 99.0
    t, g = target[0], got[0]
    s = sum(W[k] * abs(t[k] - g[k])
            for k in ('area_ink', 'wh', 'fill', 'widest', 'floor', 'h_ink', 'ink_wh'))
    dp = sum(abs(a - c) + abs(b - d) for (a, b), (c, d) in zip(t['profile'], g['profile']))
    return s + W['profile'] * dp / len(t['profile'])


def main():
    ch, dials = sys.argv[1], json.loads(sys.argv[2])
    path, box, note = CC.SCAN[ch]
    target = CC.from_image(path, box)
    print('target: %s' % note); CC.show(ch + ' scan', target)
    tmp = tempfile.mkdtemp()

    def evaluate(vals):
        env = dict(BASE); env.update({k: str(v) for k, v in vals.items()})
        r = subprocess.run([sys.executable, '-m', 'outlines.build', tmp, '--style', 'Italic'],
                           cwd=HERE, env=env, capture_output=True, text=True)
        if r.returncode: sys.exit('build failed:\n' + r.stderr[-1200:])
        return score(target, CC.from_font(tmp + '/Albo-Italic.ttf', ch)), CC.from_font(tmp + '/Albo-Italic.ttf', ch)

    vals = {k: v[0] for k, v in dials.items()}
    best, got = evaluate(vals)
    print('\npass 0  score %.3f' % best); CC.show(ch + ' build', got)
    for p in range(1, 9):
        moved = False
        for k, (v0, lo, hi, step) in dials.items():
            for d in (+step, -step):
                t = dict(vals); t[k] = round(min(hi, max(lo, vals[k] + d)), 4)
                if t[k] == vals[k]: continue
                s, g = evaluate(t)
                if s < best - 1e-3:
                    best, vals, got, moved = s, t, g, True
                    print('  %-26s -> %-8s score %.3f' % (k, t[k], s)); break
        if not moved: break
        print('pass %d  score %.3f' % (p, best))
    print('\nfinal score %.3f' % best); CC.show(ch + ' build', got)
    print(json.dumps(vals))
    shutil.rmtree(tmp)


if __name__ == '__main__':
    main()
