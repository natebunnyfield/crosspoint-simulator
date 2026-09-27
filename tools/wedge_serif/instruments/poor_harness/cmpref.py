import json,sys,statistics as st
sys.path.insert(0,"/Users/natebunnyfield/src/crosspoint-simulator/tools/wedge_serif/fit_audit")
from common import FAMILY, REFS
g=json.load(open(sys.argv[1]))
tag=sys.argv[2]
def fam(ch):
    f=FAMILY.get(ch); return f,[x for x,y in FAMILY.items() if y==f]
for spec in sys.argv[3:]:
    ch,cut,*keys=spec.split(":")
    f,m=fam(ch)
    print(f"== {ch} {cut} family={f}")
    for face in [tag]+list(REFS):
        G=g[f"{face}/{cut}"]["glyphs"]
        if ch not in G: continue
        row=[]
        for k in keys:
            v=G[ch][k]; med=st.median(G[x][k] for x in m if x in G and x!=ch)
            row.append(f"{k} {v:7.3f} (fam {med:7.3f}, r {v/med if med else 0:5.2f})")
        print(f"  {face:12s} "+" | ".join(row))
