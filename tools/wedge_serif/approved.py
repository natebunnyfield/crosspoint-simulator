#!/usr/bin/env python3
"""The approved-glyph ledger: what the owner actually ruled on, by outline.

ROUND 336 IS WHY THIS EXISTS. Every dial in the ladders was explicit on the
command line (`ALBO_G_OPEN=futura ...`) and none of it was in the SHIP build,
which took the table's defaults -- so the roman shipped `j`, a letter with a
different tail and terminal from every figure the owner approved. Nothing
caught it: both builds were gate-clean and both drew a plausible g. The check
that did catch it was hashing the shipped glyph against the build he ruled on,
by hand.

    python3 approved.py --add g --style Regular --ttf OUT/Albo-Regular.ttf \
        --round 336 --quote "use the most recent approved one instead"
    python3 approved.py --check --regular A.ttf --italic B.ttf

`--check` fails when an approved glyph no longer draws what was approved. It
is deliberately NOT a gate on every glyph: only letters the owner has ruled on
go in, and a ruling that supersedes an earlier one overwrites its row.
"""
import argparse, hashlib, json, os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "approved.json")


def gh(ttf, ch):
    f = TTFont(ttf); gs = f.getGlyphSet()
    n = f.getBestCmap()[ord(ch)]
    p = RecordingPen(); gs[n].draw(p)
    return hashlib.md5(repr(p.value).encode()).hexdigest()


def load():
    return json.load(open(LEDGER)) if os.path.exists(LEDGER) else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--add"); ap.add_argument("--style", default="Regular")
    ap.add_argument("--ttf"); ap.add_argument("--round", default="")
    ap.add_argument("--quote", default="")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--regular"); ap.add_argument("--italic")
    a = ap.parse_args()
    led = load()
    if a.add:
        key = f"{a.style}:{a.add}"
        led[key] = {"outline": gh(a.ttf, a.add), "round": a.round, "quote": a.quote}
        json.dump(led, open(LEDGER, "w"), indent=1, sort_keys=True)
        print(f"approved {key} = {led[key]['outline'][:12]}  (round {a.round})")
        return 0
    if a.check:
        paths = {"Regular": a.regular, "Italic": a.italic}
        bad = 0
        for key, rec in sorted(led.items()):
            style, ch = key.split(":", 1)
            p = paths.get(style)
            if not p:
                continue
            now = gh(p, ch)
            ok = now == rec["outline"]
            print(f"  {key:<12} {'ok' if ok else 'CHANGED'}  round {rec['round']}"
                  + ("" if ok else f"\n      approved {rec['outline'][:12]} -> now {now[:12]}"
                                   f"\n      ruled on: \"{rec['quote']}\""))
            bad += 0 if ok else 1
        if bad:
            print(f"\n{bad} approved glyph(s) no longer draw what was approved. Either the "
                  f"change is a new ruling -- re-run --add and say so in the commit -- or "
                  f"the ship build is not the build he ruled on, which is round 336.")
            return 1
        print(f"all {len(led)} approved glyph(s) unchanged")
        return 0
    ap.print_help(); return 2


if __name__ == "__main__":
    sys.exit(main())
