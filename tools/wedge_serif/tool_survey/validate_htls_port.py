#!/usr/bin/env python3
"""Check the HTLS port against HTLS's own example font.

HTLetterspacer/Examples/ExampleFont-Glyphs3.glyphs ships spaced, with its
HTLS parameters stored as master custom parameters (paramArea / paramDepth /
paramOver) and its rules in LetterspacerTestFont_Export.json. If those
sidebearings were written by HTLS, the port must reproduce them.

    $VENV/bin/python validate_htls_port.py PATH/TO/HTLetterspacer/Examples
"""
import os, sys
import numpy as np
import glyphsLib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import htls_port as H  # noqa: E402


def contours_of(layer):
    out = []
    for path in layer.paths:
        nodes = list(path.nodes)
        # rotate so we start on an on-curve node
        k = next(i for i, n in enumerate(nodes) if n.type != "offcurve")
        nodes = nodes[k + 1:] + nodes[:k + 1]
        cur = [tuple(nodes[-1].position)]
        buf = []
        for n in nodes:
            if n.type == "offcurve":
                buf.append(tuple(n.position)); continue
            p = tuple(n.position)
            if n.type == "curve" and len(buf) == 2:
                p0 = cur[-1]
                for t in np.linspace(0, 1, 33)[1:]:
                    u = 1 - t
                    cur.append((u**3*p0[0]+3*u*u*t*buf[0][0]+3*u*t*t*buf[1][0]+t**3*p[0],
                                u**3*p0[1]+3*u*u*t*buf[0][1]+3*u*t*t*buf[1][1]+t**3*p[1]))
            else:
                cur.append(p)
            buf = []
        out.append(cur)
    return out


def main(ex):
    font = glyphsLib.GSFont(os.path.join(ex, "ExampleFont-Glyphs3.glyphs"))
    for mi, m in enumerate(font.masters):
        cp = {c.name: float(c.value) for c in m.customParameters}
        class F:  # the engine only needs these
            pass
        eng = H.Engine.__new__(H.Engine)
        eng.upm, eng.angle, eng.xHeight = font.upm, m.italicAngle or 0, m.xHeight
        eng.paramArea, eng.paramDepth, eng.paramOver = cp["paramArea"], cp["paramDepth"], cp["paramOver"]
        eng.paramFreq = H.paramFreq
        lay = {}
        for g in font.glyphs:
            if g.name and len(g.name) == 1 and g.name.isalpha():
                L = g.layers[m.id]
                if L.paths and not L.components:
                    lay[g.name] = (H.Layer(None, g.name, contours_of(L), L.width), L)
        diffs = []
        for c, (hl, L) in sorted(lay.items()):
            ref, f = (lay["H"][0], 1.25) if c.isupper() else (lay["x"][0], 1.0)
            eng.effectiveArea = eng.paramArea * f; eng.effectiveDepth = eng.paramDepth
            r = eng.setSpace(hl, ref)
            if r is None:
                continue
            lsb0 = hl.bounds[0]; rsb0 = hl.width - hl.bounds[2]
            diffs.append((c, r[0] - lsb0, r[1] - rsb0))
        d = np.array([[a, b] for _, a, b in diffs])
        exact = np.mean(np.abs(d) <= 1)
        print(f"master {m.name or mi}: {len(diffs)} letters, |port - stored| mean {np.abs(d).mean():.2f}, "
              f"within 1 unit {exact:.0%}; worst " +
              ", ".join(f"{c} {a:+.0f}/{b:+.0f}" for c, a, b in sorted(diffs, key=lambda t: -abs(t[1]) - abs(t[2]))[:6]))


if __name__ == "__main__":
    main(sys.argv[1])
