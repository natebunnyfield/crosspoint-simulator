"""terminal_weight.py -- a c's top and bottom terminal weight, over the n's stem, from a raster at 600 px.

    python3 instruments/terminal_weight.py FONT.otf [FONT2 ...]

Largest vertical ink run in the right 38% of columns, top 45% of rows (top) and bottom 45% (bottom),
over the n's stem at mid-height; plus the ink AREA ratio of the two regions. A PROXY: the bottom region
also catches the bowl's own bottom, and a tall spike inflates the top's run (T3 read 1.29 on a horn),
so prefer the area ratio for "prominence". Reference bold italics, 2026-09-28: bottom 0.32-0.50 of the
stem, top/bottom run 1.5-3.7 (docs/albo-round-433-2026-09-28.md has the table).
"""
import sys, freetype, numpy as np
def mask(path, ch, px=600):
    f=freetype.Face(path); f.set_pixel_sizes(0,px)
    f.load_char(ch, freetype.FT_LOAD_RENDER|freetype.FT_LOAD_NO_HINTING); b=f.glyph.bitmap
    a=np.array(b.buffer,np.uint8).reshape(b.rows,b.pitch)[:, :b.width]>127
    return a
def stem(path):
    a=mask(path,'n'); r=a[a.shape[0]//2]; xs=np.nonzero(r)[0]
    runs=np.split(xs, np.nonzero(np.diff(xs)>1)[0]+1); return len(runs[0])
def term(path):
    a=mask(path,'c'); H,W=a.shape
    # vertical runs in right 35% columns: top region rows < 0.45H, bottom rows > 0.55H
    def maxrun(rows, cols):
        best=0
        for x in cols:
            col=a[rows, x]; 
            run=cur=0
            for v in col:
                cur=cur+1 if v else 0; run=max(run,cur)
            best=max(best,run)
        return best
    cols=range(int(W*0.62), W)
    top=maxrun(slice(0,int(H*0.45)), cols); bot=maxrun(slice(int(H*0.55),H), cols)
    area_t=a[:int(H*0.45), int(W*0.62):].sum(); area_b=a[int(H*0.55):, int(W*0.62):].sum()
    return top, bot, area_t, area_b
for p in sys.argv[1:]:
    s=stem(p); t,b,at,ab=term(p)
    print(f"{p.split('/')[-1][:34]:34} stem {s:3d}  top {t/s:.2f}  bot {b/s:.2f}  top/bot {t/b:.2f}  area t/b {at/ab:.2f}")
