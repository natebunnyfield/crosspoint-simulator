"""Cut the owner's yellow regions out of his marked sheets: threshold, downsample x4, dilate,
label by BFS, bbox per component, map to glyph cell -> glyph units. Writes regions.json."""
import sys, json, numpy as np
from PIL import Image
from collections import deque
sys.path.insert(0, '/Users/natebunnyfield/src/crosspoint-simulator/tools/wedge_serif')
from albo_bumps import GLYPHS
SC = 300 / 674.0
SHEETS = [('roman','top','/Users/natebunnyfield/Downloads/bumps-roman-v2-top.png',0),
          ('roman','bottom','/Users/natebunnyfield/Downloads/bumps-roman-v2-bottom.png',3827),
          ('italic','top','/Users/natebunnyfield/Downloads/bumps-italic-v2-top.png',0),
          ('italic','bottom','/Users/natebunnyfield/Downloads/bumps-italic-v2-bottom.png',3840)]
out = {'roman': [], 'italic': []}
for style, half, path, cut in SHEETS:
    try: im = Image.open(path).convert('RGB')
    except FileNotFoundError: print('MISSING', path); continue
    a = np.asarray(im).astype(int)
    m = (a[:,:,0]>180)&(a[:,:,1]>170)&(a[:,:,2]<170)&(a[:,:,0]-a[:,:,2]>60)
    D = 4; h, w = m.shape; m4 = m[:h//D*D, :w//D*D].reshape(h//D, D, w//D, D).any(axis=(1,3))
    # dilate by 3 cells (12 px) to merge marker strokes
    md = m4.copy()
    for _ in range(3):
        p = np.pad(md, 1); md = p[:-2,1:-1]|p[2:,1:-1]|p[1:-1,:-2]|p[1:-1,2:]|md
    seen = np.zeros_like(md, dtype=bool); H, W = md.shape; comps = []
    for y in range(H):
        for x in range(W):
            if md[y,x] and not seen[y,x]:
                q = deque([(y,x)]); seen[y,x] = True; ys=[]; xs=[]; n=0
                while q:
                    cy, cx = q.popleft(); ys.append(cy); xs.append(cx); n += 1
                    for ny, nx in ((cy-1,cx),(cy+1,cx),(cy,cx-1),(cy,cx+1)):
                        if 0<=ny<H and 0<=nx<W and md[ny,nx] and not seen[ny,nx]: seen[ny,nx]=True; q.append((ny,nx))
                raw = m4[min(ys):max(ys)+1, min(xs):max(xs)+1].sum()
                if raw < 6: continue   # a stray speck
                comps.append((min(xs)*D, min(ys)*D+cut, (max(xs)+1)*D, (max(ys)+1)*D+cut, int(raw*D*D)))
    for sx0, sy0, sx1, sy1, px in comps:
        cx, cy = (sx0+sx1)/2, (sy0+sy1)/2
        col = int((cx-20)//705); row = int((cy-60)//615); gi = row*6+col
        if not (0 <= col < 6 and 0 <= gi < len(GLYPHS)): continue
        ox = 20+col*705+105; base = 60+row*615+435
        ux0, ux1 = (sx0-ox)/SC, (sx1-ox)/SC; uy1, uy0 = (base-sy0)/SC, (base-sy1)/SC
        out[style].append(dict(glyph=GLYPHS[gi], half=half, box=[round(ux0),round(uy0),round(ux1),round(uy1)], px=px, sheet=[sx0,sy0,sx1,sy1]))
for style in out:
    out[style].sort(key=lambda r: (GLYPHS.index(r['glyph']), -r['box'][3], r['box'][0]))
    k = {}
    for r in out[style]:
        k[r['glyph']] = k.get(r['glyph'], 0) + 1; r['id'] = f"{'R' if style=='roman' else 'I'}{r['glyph']}{k[r['glyph']]}"
    print(style, len(out[style]), 'regions;', sorted(set(r['glyph'] for r in out[style])))
json.dump(out, open('/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/06bd1159-4703-424c-abda-64842a60926b/scratchpad/ledger2/regions.json','w'), indent=1)
