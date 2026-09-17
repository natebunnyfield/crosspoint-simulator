"""Minimum WHITE between two capitals, in em, measured the same way on any font.

Owner 2026-09-16: *"adjust the letter spacing of capitals especially after U
and with Y"*. He named the right two letters; this is what says by how much.

WHAT IT MEASURES. Both glyphs are rendered, the second placed at the pair's
SHAPED advance, and the gap is the minimum horizontal distance between the two
inks over every row they both occupy -- which is the white a reader actually
sees, not a bearing sum. Reported in em so three fonts at three upms compare.

THE BUG THIS SCRIPT HAD, worth keeping because it invalidated a whole reading:
the second glyph was first placed at `getlength(a)`, the UNKERNED advance, so
the GPOS kern table was invisible and the numbers described bearings alone.
With the kern in, Albo's YA and YU measured a NEGATIVE gap -- the letters
touched -- and the un-kerned run had called them merely tight. The offset is
`getlength(a+b) - getlength(b)`, which is a's advance as shaped in that pair.

HOW TO READ IT. Albo's capitals run a uniform +0.045 em looser than Flanker
(HN, NN, HH, OO, EN, DO all sit between +0.042 and +0.070), and nobody has
complained about those -- it is the face's own rhythm. So a pair's target is
Flanker PLUS about 0.045, and what matters is the distance from THAT, not from
zero. The CONTROL block is printed first for exactly this reason.

    PYTHON_GIL=0 python3 cmp_cap_space.py <built>/Albo-Italic.ttf
"""

import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

def gap(ttf, a, b, px=400):
    f=TTFont(ttf); upm=f["head"].unitsPerEm
    fnt=ImageFont.truetype(ttf, px)
    W,H=px*4,px*3
    def draw(s):
        im=Image.new("L",(W,H),255); ImageDraw.Draw(im).text((px, px*2), s, font=fnt, fill=0, anchor="ls")
        return np.asarray(im)<128
    A=draw(a); AB=draw(a+b)
    B=AB & ~A
    # B may clip where they overlap; draw b alone at the pair's KERNED offset.
    # getlength(a) alone is the unkerned advance -- using it measures bearings
    # only and the whole GPOS kern table is invisible, which is what the first
    # cut of this script did. getlength(a+b) - getlength(b) is a's advance AS
    # SHAPED IN THAT PAIR, so the kern is in it.
    adv=fnt.getlength(a+b)-fnt.getlength(b)
    imb=Image.new("L",(W,H),255); ImageDraw.Draw(imb).text((px+adv, px*2), b, font=fnt, fill=0, anchor="ls")
    B=np.asarray(imb)<128
    if not A.any() or not B.any(): return None
    # per row, right edge of A and left edge of B; the gap is the min over rows both occupy
    best=None
    for y in range(H):
        ra=np.nonzero(A[y])[0]; rb=np.nonzero(B[y])[0]
        if not len(ra) or not len(rb): continue
        g=rb.min()-ra.max()
        if best is None or g<best: best=g
    if best is None:   # no shared row: fall back to the bbox gap
        ax=np.nonzero(A.any(0))[0]; bx=np.nonzero(B.any(0))[0]
        best=bx.min()-ax.max()
    return best/px   # in em

PAIRS = ["UN","UT","UR","US","UA","UV","UL","UO","UU","UI","UP","UM",
         "YA","YO","YE","YT","YS","YU","AY","LY","TY","OY","VY","RY","NY"]
CTRL  = ["HN","HO","NN","OO","HH","NO","ON","EN","DO"]
rows=[]
fonts=[(sys.argv[1],"ALBO"),("refs/flanker-griffo-italic.otf","Flanker"),("refs/texgyrepagella-italic.otf","Pagella")]
print(f"{'pair':6}" + "".join(f"{n:>12}" for _,n in fonts) + "     vs Flanker")
for grp,name in ((CTRL,"CONTROL -- pairs nobody complained about"),(PAIRS,"THE TWO THE OWNER NAMED")):
    print(f"\n  {name}")
    for p in grp:
        vals=[]
        for t,_ in fonts:
            try: vals.append(gap(t,p[0],p[1]))
            except Exception: vals.append(None)
        d = (vals[0]-vals[1]) if (vals[0] is not None and vals[1] is not None) else None
        print(f"  {p:6}" + "".join(f"{('--' if v is None else '%.4f'%v):>12}" for v in vals)
              + ("" if d is None else f"   {d:+.4f}" + ("   <-- WIDE" if d>0.030 else ("   <-- tight" if d<-0.030 else ""))))
