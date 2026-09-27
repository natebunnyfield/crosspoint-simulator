"""thinmap.py FONT CH OUT : fit_audit.geom's own stroke() ridge; ridge points at or
under the glyph's p10 are red, p10-p25 orange -- where a 'cut'/'thin' flag lives."""
import sys, numpy as np
sys.path.insert(0,"/Users/natebunnyfield/src/crosspoint-simulator/tools/wedge_serif/fit_audit")
import geom
from common import Font
from scipy import ndimage
from PIL import Image
path,ch,out=sys.argv[1:4]
F=Font(path,0)
m,left,top,adv=geom.hi_mask(F,ch,F.slant if hasattr(F,"slant") else 0.0)
d=ndimage.distance_transform_edt(m); p=np.pad(d,1); c=p[1:-1,1:-1]
keep=(m&(d>=1.5)&(c>=p[1:-1,:-2])&(c>=p[1:-1,2:])&(c>=p[:-2,1:-1])&(c>=p[2:,1:-1]))
t=2*d
p10,p25=np.percentile(t[keep],[10,25])
img=np.where(m[...,None],np.array([60,60,60],np.uint8),np.array([255,255,255],np.uint8)).astype(np.uint8)
r=keep&(t<=p10); o=keep&(t>p10)&(t<=p25)
r=ndimage.binary_dilation(r,iterations=3); o=ndimage.binary_dilation(o,iterations=2)
img[o]=[255,160,0]; img[r]=[255,0,0]
im=Image.fromarray(img); im=im.resize((im.width//2,im.height//2),Image.LANCZOS); im.save(out)
u=F.upm/geom.HI_PPEM
print(f"p10 {p10*u:.1f} p25 {p25*u:.1f} units")
