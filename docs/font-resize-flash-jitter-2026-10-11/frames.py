# Decode a simctl recording at full resolution, every frame (passthrough),
# and save gray frames + their pts into an npz-free list of PNGs.
import subprocess, sys, re, os
from PIL import Image
mov, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
W, H = 630, 1368  # half resolution
p = subprocess.run(['ffmpeg','-loglevel','info','-i',mov,'-fps_mode','passthrough',
    '-vf',f'scale={W}:{H}:flags=area,showinfo','-f','rawvideo','-pix_fmt','gray','-'],
    capture_output=True)
pts = [float(m.group(1)) for m in re.finditer(rb'pts_time:([0-9.]+)', p.stderr)]
n = len(p.stdout)//(W*H)
for i in range(n):
    Image.frombytes('L',(W,H),p.stdout[i*W*H:(i+1)*W*H]).save(f'{out}/{i:04d}_{pts[i]:.3f}.png')
print(n, 'frames', len(pts), 'pts')
