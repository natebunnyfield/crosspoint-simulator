import sys, glob, os
from PIL import Image, ImageDraw
d, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
fs = sorted(glob.glob(d+'/*.png'))[a:b+1]
ims = [Image.open(f) for f in fs]
W, H = ims[0].size
# crop the top half of the glass where the paper's top edge and first lines are
box = (0, 0, W, H//2)
cw, ch = box[2]-box[0], box[3]-box[1]
sheet = Image.new('L', (cw*len(ims)+8*(len(ims)-1), ch+40), 0)
dr = ImageDraw.Draw(sheet)
for i,(f,im) in enumerate(zip(fs,ims)):
    x = i*(cw+8)
    sheet.paste(im.crop(box), (x, 40))
    dr.text((x+4, 8), os.path.basename(f)[5:-4]+'s', fill=255)
sheet.save(out)
print(sheet.size)
