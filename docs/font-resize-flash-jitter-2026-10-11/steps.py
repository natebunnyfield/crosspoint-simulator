# For each font step, every frame between the last settled frame before the
# step and the first frame after the sweep: its residual against the settled
# frame BEFORE the step and against the settled frame AFTER it. A frame that
# matches neither (both residuals high) is a frame that is neither the old page
# nor the new one -- the jitter or the flash.
import sys, glob, os
from PIL import Image, ImageChops, ImageStat
d = sys.argv[1]
fs = sorted(glob.glob(d+'/*.png'))
ts = [float(os.path.basename(f)[5:-4]) for f in fs]
# group frames into bursts separated by > 1.5 s of no frames
bursts, cur = [], [0]
for i in range(1, len(fs)):
    if ts[i]-ts[i-1] > 1.5: bursts.append(cur); cur=[i]
    else: cur.append(i)
bursts.append(cur)
def diff(a, b):
    A = Image.open(fs[a]).crop((0,120,630,1100)); B = Image.open(fs[b]).crop((0,120,630,1100))
    return ImageStat.Stat(ImageChops.difference(A,B)).mean[0]
for bi in range(1, len(bursts)):
    prev_settled = bursts[bi-1][-1]; br = bursts[bi]; new_settled = br[-1]
    if len(br) < 2: continue
    rows = []
    for i in br:
        rows.append(f'{ts[i]:.3f}:old={diff(i,prev_settled):.1f}/new={diff(i,new_settled):.1f}')
    print(f'burst@{ts[br[0]]:.2f}', ' '.join(rows))
