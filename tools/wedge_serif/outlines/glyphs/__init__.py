"""The glyph registry: ch -> fn(c) -> shapely geometry. One module per
family; each registers into GLYPHS at import."""
import functools

GLYPHS = {}

# ROUND 367 -- WHICH GLYPH IS BEING DRAWN, so a dot can be unique to it.
# Owner 2026-09-23, having ruled the filed flat: *"it needs to be subtly
# unique to each dot."* A dot does not know what it belongs to -- `dot()`
# takes a centre and a radius and nothing else, and there are some
# twenty-five call sites across the marks, the tittles, the accents, the
# ligatures and the symbols. Rather than thread an identifier through every
# one of them, the decorator records the glyph it is about to draw and
# `primitives.dot()` reads it, counting the dots WITHIN that glyph so the
# colon's two and the ellipsis's three each get their own.
#
# Saved and restored rather than merely set: glyphs call other glyphs (the
# yen is `GLYPHS['Y']`, the ligatures build from their own letters), so a
# nested draw must hand the name back when it returns or every dot after it
# is keyed to the wrong letter.
CURRENT = {"ch": "", "n": 0}

def glyph(*chars):
    def deco(fn):
        _name = chars[0]
        def wrapped(*a, **k):
            prev = (CURRENT["ch"], CURRENT["n"])
            CURRENT["ch"], CURRENT["n"] = _name, 0
            try:
                return fn(*a, **k)
            finally:
                CURRENT["ch"], CURRENT["n"] = prev
        # functools.wraps, and __module__ ABOVE ALL: aldine.py proves it defines
        # the whole lowercase by asking each registered glyph which module it
        # came from, and a wrapper that answers `outlines.glyphs` makes every
        # Aldine letter look missing. The build then fails loudly, which is
        # that check working -- but only because it exists.
        functools.update_wrapper(wrapped, fn)
        for ch in chars: GLYPHS[ch] = wrapped
        return wrapped
    return deco
from . import arches  # noqa: E402,F401
for _m in ("rounds", "stems", "diagonals", "caps_straight", "caps_round", "caps_diag", "figures", "marks", "ligatures", "accents", "symbols", "symbols2", "italic", "aldine", "greek_italic"):
    try:
        __import__(f"{__name__}.{_m}")
    except ImportError as e:
        if _m not in str(e): raise
