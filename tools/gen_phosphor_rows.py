#!/usr/bin/env python3
"""Emit the C++ and plist for every remaining JEDEC phosphor row.

Run from the repo root:  python3 tools/gen_phosphor_rows.py > /tmp/rows.txt
Nothing is written in place -- the output is reviewed and pasted, because
PanelPalette.h carries hand-written commentary this must not clobber.
"""
import sys
sys.path.insert(0, 'tools')
from derive_phosphors import (chroma_from_nm, chroma_from_xy, mix, lift,
                              to_bytes, contrast, hexs)
from phosphor_table import TABLE

LIGHT_TINT = 0.25
DARK_GROUND = 0.010
# The band is modelled in CHROMATICITY space now, inside chroma_from_nm, where
# it belongs -- see the comment there. Mixing white in afterwards, on top of the
# gamut mapping, is what made every green a pale mint.
BAND_BROADEN = 0.0

# hue family + sort key, so the picker stays "hue first, fastest to slowest".
FAMILY = {
    "P46": "Green", "P24": "Green", "P31": "Green", "P22G": "Green",
    "P53": "Green", "P43": "Green", "P20": "Green", "P1": "Green",
    "P34": "Green", "P39": "Green", "P15": "Green", "P2": "Green",
    "P47": "Blue", "P5": "Blue", "P55": "Blue", "P11": "Blue",
    "P22B": "Blue", "P16": "Blue",
    "P45": "White", "P4": "White", "P6": "White", "P18": "White",
    "P23": "White", "P35": "White", "P40": "White",
    "P3": "Amber", "P28": "Amber", "P19": "Amber", "P26": "Amber",
    "P38": "Amber", "P12": "Amber", "P33": "Amber",
    "P25": "Red", "P13": "Red", "P27": "Red", "P21": "Red",
    "P22R": "Red", "P56": "Red",
    "P7": "Cascade", "P14": "Cascade", "P17": "Cascade",
    "P10": "Special",
}
FAMILY_ORDER = ["Green", "Amber", "Red", "Blue", "White", "Cascade", "Special"]

# The twelve already shipped, with the decay their PresetInfo row carries, so
# the sort can interleave old and new rows correctly.
SHIPPED_ROWS = [
    ("P31", "kPresetGreenFastCrt", 1.0), ("P1", "kPresetGreenCrt", 20.0),
    ("P39", "kPresetGreenLongCrt", 150.0), ("P3", "kPresetAmberCrt", 13.0),
    ("P22R", "kPresetRedCrt", 10.0), ("P56", "kPresetRedProjCrt", 10.0),
    ("P47", "kPresetBlueFastCrt", 0.05), ("P11", "kPresetBlueCrt", 2.0),
    ("P22B", "kPresetBlueTvCrt", 10.0), ("P45", "kPresetWhiteCrt", 10.0),
    ("P4", "kPresetGrayCrt", 33.0), ("P7", "kPresetCascadeCrt", 1000.0),
]


def chroma_of(src):
    if src[0] == 'nm':
        return chroma_from_nm(src[1])
    if src[0] == 'xy':
        return chroma_from_xy(src[1], src[2])
    if src[0] == 'mix':
        acc = [0, 0, 0]
        for nm, w in src[1]:
            c = chroma_from_nm(nm)
            acc = [acc[i] + c[i] * w for i in range(3)]
        hi = max(acc)
        return [q / hi for q in acc]
    return None


def tones(src):
    # P10 does not emit. A dark-trace tube is a scotophor: the beam colours
    # KCl's F-centres and the trace goes dark VIOLET on the screen's own pale
    # ground. So it is the one CRT row whose light pair is the authentic one
    # and whose ink is not a phosphor colour at all.
    if src[0] == 'scotophor':
        return ((0x3A, 0x23, 0x52), (0xF2, 0xF0, 0xEA),
                (0xC9, 0xB6, 0xDE), (0x14, 0x11, 0x19))
    c = mix(chroma_of(src), [1, 1, 1], BAND_BROADEN)
    pl = mix([1, 1, 1], c, LIGHT_TINT)
    il = lift(c, pl)
    pd = [q * DARK_GROUND for q in c]
    idk = lift(c, pd)
    return to_bytes(il), to_bytes(pl), to_bytes(idk), to_bytes(pd)


def ident(pnum, name):
    # Named for the PHOSPHOR, not the marketing name: kPresetP22GCrt. The
    # display names carry hyphens and spaces ("Blue-Green Long") which are not
    # identifiers, and a P-number is already unique and stable.
    return "kPreset" + pnum + "Crt"


def main():
    preset = 26
    rows = []
    for pnum, name, comp, colour, src, pers, decay, after in TABLE:
        il, pl, idk, pd = tones(src)
        rows.append(dict(pnum=pnum, name=name, comp=comp, colour=colour,
                         pers=pers, decay=decay, after=after, preset=preset,
                         ident=ident(pnum, name), il=il, pl=pl, idk=idk, pd=pd,
                         cl=contrast(il, pl), cd=contrast(idk, pd)))
        preset += 1

    print("// ---- enum ----")
    for r in rows:
        print(f"  {r['ident']} = {r['preset']},  // {r['pnum']} {r['comp']}, "
              f"{r['colour'].lower()}, {r['pers']}")

    print("\n// ---- isKnownPreset ----")
    print("         " + " ||\n         ".join(
        f"preset == {r['ident']}" for r in rows))

    print("\n// ---- palette cases ----")
    for r in rows:
        print(f"  case {r['ident']}:  // {r['pnum']}, {r['cl']:.1f}:1 / {r['cd']:.1f}:1")
        print(f"    return dark ? Palette{{{{0x{r['idk'][0]:02X}, 0x{r['idk'][1]:02X}, 0x{r['idk'][2]:02X}}}, "
              f"{{0x{r['pd'][0]:02X}, 0x{r['pd'][1]:02X}, 0x{r['pd'][2]:02X}}}}}")
        print(f"                : Palette{{{{0x{r['il'][0]:02X}, 0x{r['il'][1]:02X}, 0x{r['il'][2]:02X}}}, "
              f"{{0x{r['pl'][0]:02X}, 0x{r['pl'][1]:02X}, 0x{r['pl'][2]:02X}}}}};")

    # sorted display order across old and new
    allrows = [(FAMILY.get(p, "Special"), d, ident, p, None)
               for p, ident, d in SHIPPED_ROWS]
    allrows += [(FAMILY.get(r['pnum'], "Special"), r['decay'], r['ident'],
                 r['pnum'], r) for r in rows]
    allrows.sort(key=lambda t: (FAMILY_ORDER.index(t[0]), t[1]))

    print("\n// ---- kPresetInfo, in display order ----")
    for fam, decay, idn, pnum, r in allrows:
        if r is None:
            print(f"  // (shipped) {idn}  {pnum}  {fam}  decay {decay}")
        else:
            aft = "kCascadeAfterglow" if r['after'] else "nullptr"
            print(f'    {{{idn}, "CRT", "{r["name"]}", "{pnum} {r["comp"]}", '
                  f'"{pnum}", "{r["pers"]}", {decay}f, {aft}}},')

    print("\n// ---- Root.plist rows, in display order ----")
    for fam, decay, idn, pnum, r in allrows:
        if r is None:
            print(f"  <!-- shipped: {pnum} -->")
        else:
            print(f"\t\t\t\t<string>CRT · {r['name']} — {pnum} {r['colour'].lower()}, "
                  f"{r['cd']:.1f}:1</string>")
    print("\n// ---- values ----")
    for fam, decay, idn, pnum, r in allrows:
        print(f"\t\t\t\t<integer>{r['preset']}</integer>" if r else f"  <!-- {pnum} -->")


main()
