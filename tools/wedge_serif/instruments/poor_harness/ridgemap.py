"""ridgemap.py FONT CH OUT: fit_audit.geom's ridge colored by thickness band relative to the glyph's p50:
blue < 0.8 p50, green 0.8-1.2, red > 1.2. Prints the ridge-point share per band and p10/p50/p90."""
import sys, numpy as np
sys.path.insert(0,"/Users/natebunnyfield/src/crosspoint-simulator/tools/wedge_serif/fit_audit")
import geom
from common import Font
from scipy import ndimage
from PIL import Image
path,ch,out=sys.argv[1:4]
F=Font(path,0)
m,left,top,adv=geom.hi_mask(F,ch,F.slant)
d=ndimage.distance_transform_edt(m); p=np.pad(d,1); c=p[1:-1,1:-1]
keep=(m&(d>=1.5)&(c>=p[1:-1,:-2])&(c>=p[1:-1,2:])&(c>=p[:-2,1:-1])&(c>=p[2:,1:-1]))
u=F.upm/geom.HI_PPEM; t=2*d*u
p10,p50,p90=np.percentile(t[keep],[10,50,90])
img=np.where(m[...,None],np.array([200,200,200],np.uint8),np.array([255,255,255],np.uint8)).astype(np.uint8)
for lo,hi,col in [(0,0.8,[0,0,255]),(0.8,1.2,[0,160,0]),(1.2,99,[255,0,0])]:
    sel=keep&(t>=lo*p50)&(t<hi*p50); img[ndimage.binary_dilation(sel,iterations=2)]=col
    print(f"  {lo}-{hi} x p50: {sel.sum()/keep.sum():.0%}")
print(f"p10 {p10:.1f} p50 {p50:.1f} p90 {p90:.1f}")
im=Image.fromarray(img); im=im.resize((im.width//2,im.height//2),Image.LANCZOS); im.save(out)
