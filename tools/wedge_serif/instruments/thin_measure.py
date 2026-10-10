"""thin_measure.py -- the o's top and bottom stroke thickness and the a's hood, at a 429 x-height, Albo against the references.

    $VENV instruments/thin_measure.py --albo DIR

o: the vertical ink run at the letter's center column, at the top and at the bottom (units); the
left and right runs at mid x-height. a: the top run at the column 55% across (the hood), the bowl's
upper stroke at 55% across (the second run from the top), the left run at 0.3 xh (the bowl's left).
All over the n's stem too. Round 486 (the a and o reopened, 2026-10-09)."""
import argparse, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import word_parts as WP, word_measure as WM
def runs(col):
    xs=np.nonzero(col)[0]; out=[]
    if not len(xs): return out
    s=xs[0]
    for k in range(1,len(xs)):
        if xs[k]!=xs[k-1]+1: out.append((s,xs[k-1])); s=xs[k]
    out.append((s,xs[-1])); return out
def meas(p,i,it):
    r=WP.mask(p,i,'n',it); m,left,top,adv=r; y=WP.rows_y(m,top)
    mid=int(np.argmin(np.abs(y-WP.XH*0.5))); stem=runs(m[mid])[0]; stem=stem[1]-stem[0]+1
    out={"stem":stem}
    r=WP.mask(p,i,'o',it); m,left,top,adv=r; y=WP.rows_y(m,top)
    cols=np.nonzero(m.any(0))[0]; cx=(cols[0]+cols[-1])//2; rr=runs(m[:,cx])
    out["o_top"]=rr[0][1]-rr[0][0]+1; out["o_bot"]=rr[-1][1]-rr[-1][0]+1
    mid=int(np.argmin(np.abs(y-WP.XH*0.5))); rr=runs(m[mid]); out["o_left"]=rr[0][1]-rr[0][0]+1; out["o_right"]=rr[-1][1]-rr[-1][0]+1
    r=WP.mask(p,i,'a',it); m,left,top,adv=r; y=WP.rows_y(m,top)
    cols=np.nonzero(m.any(0))[0]; c55=int(cols[0]+0.55*(cols[-1]-cols[0])); rr=runs(m[:,c55])
    out["a_hood"]=rr[0][1]-rr[0][0]+1; out["a_bowl_top"]=(rr[1][1]-rr[1][0]+1) if len(rr)>1 else -1
    r30=int(np.argmin(np.abs(y-WP.XH*0.3))); rr=runs(m[r30]); out["a_bowl_left"]=rr[0][1]-rr[0][0]+1
    return out
ap=argparse.ArgumentParser(); ap.add_argument("--albo",required=True); a=ap.parse_args()
for lab,cut,p,i in WP.faces(a.albo):
    if cut!="Regular": continue
    o=meas(p,i,False); s=o["stem"]
    print("%-9s stem %3d | o top %3d (%.2f) bot %3d (%.2f) sides %3d/%3d (%.2f) | a hood %3d (%.2f) bowl-top %3d (%.2f) bowl-left %3d (%.2f)" % (lab,s,o["o_top"],o["o_top"]/s,o["o_bot"],o["o_bot"]/s,o["o_left"],o["o_right"],o["o_left"]/s,o["a_hood"],o["a_hood"]/s,o["a_bowl_top"],o["a_bowl_top"]/s,o["a_bowl_left"],o["a_bowl_left"]/s))
