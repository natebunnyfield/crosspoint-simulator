"""How the italic references redraw their Greek: per letter, unsheared ink
width over the face's own o, italic against roman; slant measured off `l`."""
import sys, math, statistics as stt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
SUP = "/System/Library/Fonts/Supplemental/"
PAIRS = [("Iowan", (SUP + "Iowan Old Style.ttc", 0), (SUP + "Iowan Old Style.ttc", 2)),
         ("Georgia", (SUP + "Georgia.ttf", 0), (SUP + "Georgia Italic.ttf", 0)),
         ("Times", (SUP + "Times New Roman.ttf", 0), (SUP + "Times New Roman Italic.ttf", 0)),
         ("Palatino", ("/System/Library/Fonts/Palatino.ttc", 0), ("/System/Library/Fonts/Palatino.ttc", 1))]
LC = "αβγδεζηθικλμνξοπρσςτυφχψω"
PX = 400

def mask(path, idx, ch, px=PX):
    f = ImageFont.truetype(path, px, index=idx)
    im = Image.new("L", (px * 3, px * 3), 255)
    ImageDraw.Draw(im).text((px, int(px * 2)), ch, font=f, fill=0, anchor="ls")
    return np.asarray(im) < 128, int(px * 2)

def slant(path, idx):
    m, base = mask(path, idx, "l")
    rows = [r for r in range(m.shape[0]) if m[r].any()]
    r0, r1 = rows[0], rows[-1]; h = r1 - r0
    ys, xs = [], []
    for r in range(int(r0 + h * 0.25), int(r0 + h * 0.75)):
        c = np.nonzero(m[r])[0]; xs.append((c[0] + c[-1]) / 2); ys.append(base - r)
    k = np.polyfit(ys, xs, 1)[0]
    return k   # dx per dy

def width(path, idx, ch, k):
    m, base = mask(path, idx, ch)
    ys, xs = np.nonzero(m)
    xu = xs - k * (base - ys)
    return xu.max() - xu.min(), (base - ys).min(), (base - ys).max()

if __name__ == "__main__":
    tab = {}
    for name, R, I in PAIRS:
        kr = slant(*R); ki = slant(*I)
        print(f"{name}: roman slant {math.degrees(math.atan(kr)):.1f}  italic slant {math.degrees(math.atan(ki)):.1f}")
        orw = width(*R, "o", kr)[0]; oiw = width(*I, "o", ki)[0]
        xr = width(*R, "x", kr)[2]; xi = width(*I, "x", ki)[2]
        print(f"   o width roman {orw} italic {oiw} (italic/roman {oiw/orw:.3f}); x-height r {xr} i {xi}")
        for ch in LC:
            try:
                wr = width(*R, ch, kr); wi = width(*I, ch, ki)
            except Exception:
                continue
            tab.setdefault(ch, []).append((name, wr[0] / orw, wi[0] / oiw, wi[0] / wr[0], wr[1] / xr, wi[1] / xi, wr[2] / xr, wi[2] / xi))
    print("\nletter  (w/o roman -> italic) per face;  median italic/roman width ratio (raw)")
    for ch, rows in tab.items():
        print(ch, "  ".join(f"{n[:3]} {a:.2f}->{b:.2f}" for n, a, b, *_ in rows),
              f"| raw i/r {stt.median(r[3] for r in rows):.2f}",
              f"| bottom r {stt.median(r[4] for r in rows):+.2f} i {stt.median(r[5] for r in rows):+.2f}",
              f"| top r {stt.median(r[6] for r in rows):.2f} i {stt.median(r[7] for r in rows):.2f}")
