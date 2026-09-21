"""The white between two glyphs = the left glyph's RIGHT bearing + the kern +
the right glyph's LEFT bearing. Summing the two ADVANCES is wrong: it counts
the right-hand glyph's far side, which is not in the gap at all -- it read the
apostrophe's two bearings as one and reported -77 for a -44 change."""
from fontTools.ttLib import TTFont
from kernlookup import kern_table
AGL={'.':'period',',':'comma',':':'colon',';':'semicolon',"'":'quotesingle'}
def gn(c): return c if c.isalpha() else AGL.get(c,c)
def gapper(path):
    f=TTFont(path); hm=f['hmtx']; gl=f['glyf']; k,_=kern_table(path)
    def side(c):
        n=gn(c); adv,lsb=hm[n]; g=gl[n]
        w=(g.xMax-g.xMin) if g.numberOfContours else 0
        return lsb, adv-lsb-w
    def gap(a,b):
        return side(a)[1] + k(a,b) + side(b)[0]
    return gap
