"""Fjord rebuild (2026-09-13): every glyph as a DESIGNED OUTLINE.

The round-17/20 generator (alphabet2 / round17 / latin / round20) stays
untouched as the record and the fallback. This package draws the same 93
glyphs again under the owner's rulings (docs/fjord-glyph-guide.md §0, §3):
each glyph is its own contours -- stems with their wedges as one closed
contour, bowls as an outer contour with a designed counter, strokes with
declared widths along them -- joined by real outline union (shapely), so no
end is buried and no junction patched. The pen model (pen.py) is the
REFERENCE for what width a stroke has at an angle; the widths in the glyph
code are declared against it and checked by pen.check(). The faceted
one-in-four linear cut (cut.py) goes on last, keeping every corner.
"""
