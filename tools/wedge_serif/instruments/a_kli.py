"""Summarise a kli_e.py result for the letter a: grand, crowded, and every
confusion that involves a (a read as x, and x read as a), summed and listed.
Owner 2026-09-27: "take multiple passes at making it globby in a way that
helps legibility of words".

    python3 instruments/a_kli.py RESULT.json
"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "etrace"))
d = json.load(open(sys.argv[1]))
def pairs(reps):
    from difflib import SequenceMatcher
    c = {}
    for r in reps:
        gt, o = r.get("gt", ""), r.get("ocr", "")
        if not gt or not o: continue
        for tag, i1, i2, j1, j2 in SequenceMatcher(None, gt, o, autojunk=False).get_opcodes():
            if tag != "replace": continue
            a, b = gt[i1:i2], o[j1:j2]
            if len(a) != len(b):
                k = min(len(a), len(b))
                if not k: continue
                a, b = a[-k:], b[-k:]
            for x, y in zip(a, b):
                if x.isspace() or y.isspace() or x == y: continue
                c[f"{x}>{y}"] = c.get(f"{x}>{y}", 0) + 1
    return c
for font, raw in d["raw"].items():
    reps = [r for cond in (raw.values() if isinstance(raw, dict) else [raw]) for r in (cond if isinstance(cond, list) else [])]
    c = pairs(reps)
    a_as = {k: v for k, v in c.items() if k.startswith("a>")}; as_a = {k: v for k, v in c.items() if k.endswith(">a")}
    s = d["summary"][font]
    print(f"{font:10s} grand {s['grand']*100:5.1f}  crowded {s['crowded']*100:5.1f}  a-misread {sum(a_as.values()):4d} {dict(sorted(a_as.items(), key=lambda kv: -kv[1])[:5])}  read-as-a {sum(as_a.values()):4d} {dict(sorted(as_a.items(), key=lambda kv: -kv[1])[:4])}")
