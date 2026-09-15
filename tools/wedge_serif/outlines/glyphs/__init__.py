"""The glyph registry: ch -> fn(c) -> shapely geometry. One module per
family; each registers into GLYPHS at import."""
GLYPHS = {}
def glyph(*chars):
    def deco(fn):
        for ch in chars: GLYPHS[ch] = fn
        return fn
    return deco
from . import arches  # noqa: E402,F401
for _m in ("rounds", "stems", "diagonals", "caps_straight", "caps_round", "caps_diag", "figures", "marks", "ligatures", "accents", "symbols", "symbols2", "italic"):
    try:
        __import__(f"{__name__}.{_m}")
    except ImportError as e:
        if _m not in str(e): raise
