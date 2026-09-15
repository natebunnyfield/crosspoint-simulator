"""Cap widths of Albo against the three width systems the owner named on
2026-09-15: Trajan, humanist, Helvetica.

    python3 cmp_capwidths.py [<albo-regular.ttf>]

Every width is the ADVANCE over the face's own H-ink CAP HEIGHT, which is the
only unit that compares capitals across faces with different ems and different
cap-to-em ratios (they run 0.596 to 0.753 em here). The humanist column is the
MEDIAN of five faces rather than one, so no single cut's quirk becomes the
model; Trajan and Helvetica are single faces because each IS its own system.

Writes docs/albo-capital-widths.md's table. Trajan Pro is Adobe-licensed and
lives in the firmware repo's gitignored lib/EpdFont/local_fonts/.
"""
import os, sys, string, statistics, json
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

R = os.path.expanduser('~/src/crosspoint-reader/lib/EpdFont')
HUMANIST = ['Coelacanth', 'Libris ADF', 'Dante MT', 'Van den Keere', 'Doves Type']
FACES = [('Trajan Pro',    f'{R}/local_fonts/TrajanPro-Regular.ttf'),
         ('Helvetica',     '/System/Library/Fonts/Helvetica.ttc'),
         ('Coelacanth',    f'{R}/scripts/downloaded_fonts/Coelacanth/Coelacanth.otf'),
         ('Libris ADF',    f'{R}/scripts/downloaded_fonts/LibrisADF/LibrisADFStd-Regular.otf'),
         ('Dante MT',      f'{R}/local_fonts/DanteMT-Regular.ttf'),
         ('Van den Keere', f'{R}/local_fonts/VandenKeere-Regular.otf'),
         ('Doves Type',    f'{R}/local_fonts/DovesType-Text.ttf')]
LET = string.ascii_uppercase


def widths(path):
    """{letter: advance / cap height}, plus cap height as a fraction of the em."""
    f = TTFont(path, fontNumber=0) if path.endswith('.ttc') else TTFont(path)
    gs = f.getGlyphSet(); cm = f.getBestCmap(); upem = f['head'].unitsPerEm
    bp = BoundsPen(gs); gs[cm[ord('H')]].draw(bp); cap = bp.bounds[3]
    return {c: f['hmtx'][cm[ord(c)]][0] / cap for c in LET if ord(c) in cm}, cap / upem


def main(albo):
    res = {}
    for nm, p in FACES:
        if os.path.exists(p):
            res[nm] = widths(p)[0]
        else:
            print(f'MISSING {nm}: {p}', file=sys.stderr)
    res['Albo'] = widths(albo)[0]
    rows = {c: dict(trajan=res['Trajan Pro'][c],
                    humanist=statistics.median([res[n][c] for n in HUMANIST if n in res]),
                    helvetica=res['Helvetica'][c], albo=res['Albo'][c]) for c in LET}
    print(f'{"":3s} {"Trajan":>8s} {"humanist":>9s} {"Helvetica":>10s} {"Albo":>8s}')
    for c in LET:
        r = rows[c]
        print(f'{c:3s} {r["trajan"]:8.3f} {r["humanist"]:9.3f} {r["helvetica"]:10.3f} {r["albo"]:8.3f}')
    # the summary that actually separates the three systems
    sq = 'BEFLPS'; rnd = 'CDGOQ'
    print()
    for k in ('trajan', 'humanist', 'helvetica', 'albo'):
        med = statistics.median([rows[c][k] for c in LET])
        ro = statistics.median([rows[c][k] for c in rnd])
        sqm = statistics.median([rows[c][k] for c in sq])
        wide = [rows[c][k] for c in LET if c not in 'IJ']
        print(f'{k:10s} median {med:.3f}  round {ro:.3f}  square {sqm:.3f}  '
              f'round/square {ro / sqm:.3f}  spread {max(wide) / min(wide):.2f}x')
    return rows


if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else 'build/fjord-fonts/Albo-Regular.ttf'
    json.dump(main(a), open('capwidths.json', 'w'), indent=1)
