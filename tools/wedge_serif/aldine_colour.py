#!/usr/bin/env python3
"""COLOUR: make the page even, without losing the letters' measured targets.

Round 130 fitted every letter to its own source and the page still came out
uneven -- ink in the x-height band over the advance ran 0.64 to 1.62 times the
median. Each letter was right and the page was wrong, which is the wrong thing
optimised: the brief is word images.

This pulls every letter's colour toward the median by moving ONLY its weight,
and it refuses any move that would push a letter off a target it was measured
against. The measured targets win; colour is solved inside what they leave.

    python3 aldine_colour.py                # report the spread
    python3 aldine_colour.py --passes 3     # solve and print the table
"""
import argparse, json, os, statistics, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import aldine_autofit as AF

LC = 'abcdefghijklmnopqrstuvwxyz'
TOL = 0.12          # how far a measured letter may drift from its own target


def colours(ttf, size=200):
    """Ink inside the X-HEIGHT BAND over the advance, per letter.

    The band matters. Ink over advance x em ranks every ascender as dark --
    it is measuring height. Ink over the letter's own bounding box ranks every
    narrow or dotted letter as light -- the dot's gap is inside the box. Both
    were tried and both are wrong; only the band measures colour.
    """
    ft = ImageFont.truetype(ttf, size); a, d = ft.getmetrics()
    def draw(ch):
        w = int(ft.getlength(ch)) + size
        im = Image.new('L', (w, a + d + size), 255)
        ImageDraw.Draw(im).text((size // 2, a + size // 2), ch, font=ft, fill=0, anchor='ls')
        return im
    ob = draw('o').point(lambda v: 255 - v).getbbox()
    top, bot = ob[1], ob[3]
    out = {}
    for ch in LC:
        im = draw(ch); px = im.load(); W, H = im.size
        ink = sum(1 for y in range(top, bot) for x in range(W) if px[x, y] < 128)
        adv = ft.getlength(ch)
        if adv: out[ch] = ink / (adv * (bot - top))
    return out


def build(overrides, out, chars=LC + 'o'):
    env = dict(os.environ, **AF.BUILD_ENV,
               **{k: f'{v:.4f}' for k, v in overrides.items()})
    subprocess.run([sys.executable, '-W', 'ignore', '-m', 'outlines.build', out,
                    '--style', 'Italic', '--only', chars],
                   env=env, cwd=HERE, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.join(out, 'Albo-Italic.ttf')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--passes', type=int, default=0)
    ap.add_argument('--gain', type=float, default=0.55)
    args = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix='aldine-colour-')
    lw = {}
    ttf = build(lw, os.path.join(tmp, 'p0'))
    base = colours(ttf)
    med0 = statistics.median(base.values())
    print(f"before: {min(base.values())/med0:.2f} to {max(base.values())/med0:.2f} x median")
    if not args.passes:
        for ch in sorted(base, key=lambda c: -base[c]):
            print(f"   {ch}: {base[ch]/med0:5.2f}")
        return 0

    # the measured letters keep their targets; everything else is free
    targets = {ch: AF.measure_source(ch) for ch in LC}
    for p in range(args.passes):
        ttf = build(lw, os.path.join(tmp, f'p{p+1}'))
        cur = colours(ttf); med = statistics.median(cur.values())
        moved = 0
        for ch in LC:
            r = cur[ch] / med
            if abs(r - 1.0) < 0.06: continue
            want = lw.get(f'ALBO_ALD_LW_{ch}', None)
            if want is None:
                from outlines.glyphs import aldine as A
                want = A.FIT.get(ch, (1.0, 1.0))[0]
            trial = dict(lw); trial[f'ALBO_ALD_LW_{ch}'] = max(
                0.45, min(2.30, want * (1.0 / r) ** args.gain))
            # refuse the move if it breaks a target the letter was measured on
            t = targets.get(ch)
            if t and not t.get('derived'):
                tt = build(trial, os.path.join(tmp, f'p{p+1}{ch}'), ch + 'o')
                if AF.err(AF.measure_build(tt, ch), t) > TOL: continue
            lw = trial; moved += 1
        ttf = build(lw, os.path.join(tmp, f'e{p+1}'))
        c2 = colours(ttf); m2 = statistics.median(c2.values())
        print(f"  pass {p+1}: moved {moved:2d}   spread "
              f"{min(c2.values())/m2:.2f} to {max(c2.values())/m2:.2f}")
    print("\n  # solved weights")
    for k in sorted(lw): print(f"    {k[-1]!r}: {lw[k]:.3f},")
    return 0


if __name__ == '__main__':
    sys.exit(main())
