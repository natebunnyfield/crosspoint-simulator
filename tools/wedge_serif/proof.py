"""One renderer for every Albo proof image, so two proofs can be compared.

Owner 2026-09-16: *"when you are making the proof images, they seem to use
different y vertical alignment logic"*. He is right, and it was mine rather
than the font's.

THE BUG. PIL's `ImageDraw.text((x, y), ...)` places the text's ASCENT TOP at
`y` unless an `anchor` is given; `anchor="ls"` places its BASELINE there. Every
proof in this session was written inline and ad hoc, and the two conventions
were mixed -- between images, and inside single images where a headline row was
anchored and the word rows under it were not. Both are self-consistent, so
nothing ever looked broken; what breaks is COMPARING two proofs, because the
same letter sits `ascent` pixels apart between them for no reason visible on
the page. A descender shows it first: with no anchor the y hangs into whatever
is below, with `ls` it hangs below a line you can actually draw.

It also hid a real fact about this font. The declared descender is 280 units
(0.28 em) and the italic **y reaches 297** -- so a descender rule drawn from
the metrics is 17 units above the y's own tip, and the y appears to break a
line that is not where its ink ends. `descender_px()` reports both.

So: nothing here takes a top coordinate. A row is a BASELINE and a size, the
image is grown to hold the deepest descender in the text actually being set,
and rules are drawn from the same numbers the type is.

    from proof import Proof
    pr = Proof(ttf, width=1500)
    pr.row("every gypsy", 200, rules=True)      # x-line, baseline, descender
    pr.row("every green edge sees", 44)
    pr.label("round 172")
    pr.save("/tmp/x.png")
"""
import os

XH = 429.0
CAP = 674.0
DESC = 280.0
UPM = 1000.0
_UI = "/System/Library/Fonts/Supplemental/Arial.ttf"


def descender_px(font_path, px):
    """(declared, actual) descender depth in pixels at this size -- they differ,
    and which one a rule is drawn from changes what the picture seems to say."""
    from fontTools.ttLib import TTFont
    from fontTools.pens.boundsPen import BoundsPen
    f = TTFont(font_path); gs = f.getGlyphSet()
    lo = 0
    for g in ("y", "g", "p", "q", "j"):
        if g in gs:
            bp = BoundsPen(gs); gs[g].draw(bp)
            if bp.bounds: lo = min(lo, bp.bounds[1])
    return DESC * px / UPM, -lo * px / UPM


class Proof:
    def __init__(self, ttf, width=1500, pad=30, bg=255, ink=0):
        from PIL import Image, ImageDraw
        self.ttf = ttf; self.W = width; self.pad = pad
        self.bg = bg; self.ink = ink
        self.rows = []          # (kind, text, px, rules, font_path)

    def row(self, text, px, rules=False, ttf=None):
        self.rows.append(("type", text, px, rules, ttf or self.ttf)); return self

    def label(self, text, px=19):
        self.rows.append(("label", text, px, False, None)); return self

    def gap(self, px=24):
        self.rows.append(("gap", "", px, False, None)); return self

    def save(self, path):
        from PIL import Image, ImageDraw, ImageFont
        # height first: every type row owns ascent + the DEEPEST ACTUAL
        # descender of the font it is set in, never the metrics' guess.
        h = self.pad; plan = []
        for kind, text, px, rules, ttf in self.rows:
            if kind == "gap": h += px; plan.append(h); continue
            if kind == "label": h += int(px * 1.7); plan.append(h); continue
            f = ImageFont.truetype(ttf, px)
            asc, _ = f.getmetrics()
            _, act = descender_px(ttf, px)
            base = h + asc
            plan.append(base)
            h = int(base + act + px * 0.10)
        im = Image.new("L", (self.W, h + self.pad), self.bg)
        d = ImageDraw.Draw(im)
        for (kind, text, px, rules, ttf), y in zip(self.rows, plan):
            if kind == "gap": continue
            if kind == "label":
                d.text((self.pad, y - int(px * 1.2)), text,
                       font=ImageFont.truetype(_UI, px), fill=140)
                continue
            if rules:
                ui = ImageFont.truetype(_UI, 17)
                for v, c, t in ((XH, 168, "x-line"), (0.0, 150, "baseline"),
                                (-DESC, 206, "descender")):
                    yy = int(y - v * px / UPM)
                    d.line([(0, yy), (self.W, yy)], fill=c)
                    d.text((self.W - 104, yy - 21), t, font=ui, fill=c - 10)
            d.text((self.pad, y), text, font=ImageFont.truetype(ttf, px),
                   anchor="ls", fill=self.ink)          # ALWAYS the baseline
        im.save(path)
        return path
