#!/usr/bin/env bash
# End-to-end pin for SPEED READ's two live behaviors that no pure test can
# reach (docs/speed-read-rsvp-2026-09-25.md, "What is left" as of the spike):
#
#   1. TURNED ON MID-PAGE, it starts on the page ALREADY SHOWN. The mode is
#      switched on through the settings.json watcher four seconds into a run
#      whose book page was rendered with nobody asking for its words; the page
#      must arrive (a re-render asked of the firmware, HalDisplay.cpp
#      requestFirmwareRender) with NO page-forward in between. Before the fix
#      this run showed nothing at all until the next page render.
#   2. A TAP PAUSES AND RESUMES. SRTAP makes the exact call the iOS harness
#      makes for a zen deliberate tap (SimulatorOverlay::speedReadTakeTap):
#      while paused no word may advance, and on resume the reader continues
#      from the word it held -- the next word shown is the held one's
#      successor, not a skip and not a replay.
#
# Plus the gate itself: a tap with no word up is NOT taken (it must fall
# through to whatever the glass does, never be eaten).
#
#   tests/test_speed_read_live.sh <firmware-checkout>   # binary built first
#
# Exit 2 = SKIP (no binary / python3), the run_shell_skip convention. The book
# is GENERATED on a fresh card, as in test_read_aloud_capture.sh, so the page
# and its word count are deterministic and the owner's card is never touched.
set -uo pipefail

FW="${1:-}"
[[ -n "$FW" ]] || { echo "usage: $0 <firmware-checkout>"; exit 2; }
BIN=""
for env in simulator_x3 simulator; do
  if [[ -x "$FW/.pio/build/$env/program" ]]; then
    BIN="$FW/.pio/build/$env/program"
    break
  fi
done
[[ -n "$BIN" ]] || { echo "SKIP: no simulator binary under $FW/.pio/build"; exit 2; }
command -v python3 >/dev/null || { echo "SKIP: python3 not available"; exit 2; }
if ! grep -a -q 're-render requested' "$BIN"; then
  echo "SKIP: $BIN predates the speed-read re-render (rebuild it)"
  exit 2
fi

CARD="$(mktemp -d)"
trap 'rm -rf "$CARD"' EXIT
mkdir -p "$CARD/fs_/books"

python3 - "$CARD/fs_/books/speed-read-fixture.epub" <<'PYEOF'
import sys, zipfile
words = ("alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo "
         "lima mike november oscar papa quebec romeo sierra tango uniform "
         "victor whiskey xray yankee zulu").split()
body = "<p>" + " ".join(words) + "</p>"
CH = f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>One</title></head>
<body>{body}</body></html>'''
OPF = '''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="id" version="2.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Speed Read Fixture</dc:title><dc:language>en</dc:language>
<dc:identifier id="id">speed-read-fixture</dc:identifier>
</metadata>
<manifest>
<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
<item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
</manifest>
<spine toc="ncx"><itemref idref="ch1"/></spine>
</package>'''
NCX = '''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<head><meta name="dtb:uid" content="speed-read-fixture"/></head>
<docTitle><text>Speed Read Fixture</text></docTitle>
<navMap><navPoint id="n1" playOrder="1"><navLabel><text>One</text></navLabel>
<content src="ch1.xhtml"/></navPoint></navMap></ncx>'''
CONTAINER = '''<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>'''
with zipfile.ZipFile(sys.argv[1], "w") as z:
    z.writestr("mimetype", "application/epub+zip", zipfile.ZIP_STORED)
    z.writestr("META-INF/container.xml", CONTAINER, zipfile.ZIP_DEFLATED)
    z.writestr("OEBPS/content.opf", OPF, zipfile.ZIP_DEFLATED)
    z.writestr("OEBPS/toc.ncx", NCX, zipfile.ZIP_DEFLATED)
    z.writestr("OEBPS/ch1.xhtml", CH, zipfile.ZIP_DEFLATED)
PYEOF

cd "$CARD"
LOG="$CARD/run.log"
# 150 wpm = 400 ms a plain word, so the 26 words outlast the run. Timeline:
#   1500 SRTAP  -- mode off: must NOT be taken
#   ~4 s        -- settings.json: speedRead 1 (the watcher re-reads ~1 Hz)
#   10000 SRTAP -- pause (was 8000: a slow cold start could land the page after it)
#   13000 SRTAP -- resume
CROSSPOINT_SIM_DARK=0 SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
CROSSPOINT_SIM_SPEED_READ_LOG=1 CROSSPOINT_SIM_SPEED_READ_WPM=150 \
CROSSPOINT_SIM_INPUT_SCRIPT='1500:SRTAP;10000:SRTAP;13000:SRTAP;16000:QUIT' \
timeout 90 "$BIN" >"$LOG" 2>&1 &
PID=$!
for _ in $(seq 1 40); do [[ -f settings.json ]] && break; sleep 0.1; done
sleep 4
if [[ ! -f settings.json ]]; then
  echo "FAIL: no settings.json was written (the watcher is the toggle path)"
  wait "$PID"
  exit 1
fi
python3 - <<'PYEOF'
import re
p = "settings.json"
s = open(p).read()
s2 = re.sub(r'"speedRead":\s*\d+', '"speedRead": 1', s)
assert s2 != s, "speedRead key not found in settings.json"
open(p, "w").write(s2)
PYEOF
wait "$PID"

python3 - "$LOG" <<'PYEOF'
import re, sys
lines = open(sys.argv[1], errors="replace").read().splitlines()
sr = [l[l.index("[speedread]"):] for l in lines if "[speedread]" in l]
fail = []
def need(c, msg):
    if not c: fail.append(msg)

need(any("tap not taken" in l for l in sr[:3]),
     "a tap with the mode off was taken (it must fall through)")
try:
    on = next(i for i, l in enumerate(sr) if l == "[speedread] on")
except StopIteration:
    print("FAIL: the settings.json toggle never turned speed read on")
    for l in sr: print("  ", l)
    sys.exit(1)
need(any("re-render requested: yes" in l for l in sr[on:on + 3]),
     "no re-render was requested on the off->on edge")
page = next((i for i, l in enumerate(sr) if i > on and "page gen=" in l), None)
need(page is not None, "turned on mid-page, but no page's words ever arrived")
need(not any("page forward" in l for l in sr[on:(page or len(sr))]),
     "the page arrived only after a page turn (not the page already shown)")
p = next((i for i, l in enumerate(sr) if l == "[speedread] paused"), None)
r = next((i for i, l in enumerate(sr) if l == "[speedread] resumed"), None)
need(p is not None and r is not None and r > p, "no pause then resume seen")
if p is not None and r is not None:
    need(not any(" word " in l for l in sr[p:r]), "a word advanced while paused")
    held = [l for l in sr[:p] if " word " in l]
    after = [l for l in sr[r:] if " word " in l]
    idx = lambda l: int(re.search(r" word (\d+)/", l).group(1))
    need(bool(held) and bool(after), "no words either side of the pause")
    if held and after:
        need(idx(after[0]) == idx(held[-1]) + 1,
             f"resume went from word {idx(held[-1])} to {idx(after[0])}, "
             "expected the next one")
if fail:
    for f in fail: print("FAIL:", f)
    for l in sr: print("  ", l)
    sys.exit(1)
print(f"PASS: mid-page start ({sr[page]}); pause held, resume continued")
PYEOF
