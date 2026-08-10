#!/usr/bin/env bash
# End-to-end pin for the read-aloud capture (FW-A/FW-B plus the automatable
# core of gate G0): boots the desktop simulator against a FRESH card holding
# one tiny generated EPUB, turns a page through HalGPIO::queueButtonTap (the
# QTAP script action — the exact API the iOS adapter turns pages with, not
# just injectButton*), and asserts the channel's publishes: a first page with
# text, a DIFFERENT page after the tap, curly quotes and accents surviving as
# UTF-8, a cleared publish on reader exit, no soft hyphens (U+00AD) anywhere,
# and silence without the env var.
#
#   tests/test_read_aloud_capture.sh <firmware-checkout>   # binary built first
#
# Exit 2 = SKIP (missing binary or python3), the test_sleep_wake.sh
# convention — a missing precondition is not a failure.
#
# The book is GENERATED, not the ios/seedbooks EPUB, deliberately: that one is
# a Project Gutenberg mono-file book whose single chapter takes tens of
# seconds to paginate on first open, which made this test both slow and
# timing-flaky. Two one-paragraph chapters paginate instantly and make the
# page-turn assertion deterministic. A fresh card with exactly one book boots
# straight into it ("the device IS the current book"), so no navigation is
# needed before the tap.
set -uo pipefail

FW="${1:-}"
if [[ -z "$FW" ]]; then
  echo "usage: $0 <firmware-checkout>"
  exit 2
fi
BIN=""
for env in simulator_x3 simulator; do
  if [[ -x "$FW/.pio/build/$env/program" ]]; then
    BIN="$FW/.pio/build/$env/program"
    break
  fi
done
if [[ -z "$BIN" ]]; then
  echo "SKIP: no simulator binary under $FW/.pio/build (run a pio build first)"
  exit 2
fi
command -v python3 >/dev/null || { echo "SKIP: python3 not available"; exit 2; }

CARD="${CROSSPOINT_RA_KEEP_CARD:-$(mktemp -d)}"
mkdir -p "$CARD"
trap 'rm -rf "$CARD"' EXIT
mkdir -p "$CARD/fs_/books"

python3 - "$CARD/fs_/books/read-aloud-fixture.epub" <<'PYEOF'
import sys, zipfile

def xhtml(title, body):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"><head><title>{title}</title></head>
<body>{body}</body></html>'''

CH1 = xhtml("One", "<p>Chapter one begins with a “curly quoted” "
                   "greeting at the café by the sea.</p>")
CH2 = xhtml("Two", "<p>Chapter two is entirely different text about a quiet "
                   "walk through the hills.</p>")
OPF = '''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="id" version="2.0">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:title>Read Aloud Fixture</dc:title><dc:language>en</dc:language>
<dc:identifier id="id">read-aloud-fixture</dc:identifier>
</metadata>
<manifest>
<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
<item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
<item id="ch2" href="ch2.xhtml" media-type="application/xhtml+xml"/>
</manifest>
<spine toc="ncx"><itemref idref="ch1"/><itemref idref="ch2"/></spine>
</package>'''
NCX = '''<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
<head><meta name="dtb:uid" content="read-aloud-fixture"/></head>
<docTitle><text>Read Aloud Fixture</text></docTitle>
<navMap>
<navPoint id="n1" playOrder="1"><navLabel><text>One</text></navLabel><content src="ch1.xhtml"/></navPoint>
<navPoint id="n2" playOrder="2"><navLabel><text>Two</text></navLabel><content src="ch2.xhtml"/></navPoint>
</navMap></ncx>'''
CONTAINER = '''<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>'''

with zipfile.ZipFile(sys.argv[1], "w") as z:
    z.writestr("mimetype", "application/epub+zip", zipfile.ZIP_STORED)
    z.writestr("META-INF/container.xml", CONTAINER, zipfile.ZIP_DEFLATED)
    z.writestr("OEBPS/content.opf", OPF, zipfile.ZIP_DEFLATED)
    z.writestr("OEBPS/toc.ncx", NCX, zipfile.ZIP_DEFLATED)
    z.writestr("OEBPS/ch1.xhtml", CH1, zipfile.ZIP_DEFLATED)
    z.writestr("OEBPS/ch2.xhtml", CH2, zipfile.ZIP_DEFLATED)
PYEOF

cd "$CARD"

fail=0
check() {
  if ! eval "$2"; then
    echo "FAIL: $1"
    fail=1
  fi
}

LOG="$CARD/run.log"
SHOT="$CARD/page1.bmp"
# LOG=2 dumps the rects too; the screenshot is taken while that same first page
# is on the panel, so the geometry assertion below can compare the two.
CROSSPOINT_SIM_READALOUD_LOG=2 SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
CROSSPOINT_SIM_INPUT_SCRIPT='6000:QTAP:RIGHT;12000:BACK;15000:QUIT' \
CROSSPOINT_SIM_SCREENSHOTS="4000:$SHOT" \
timeout 90 "$BIN" >"$LOG" 2>&1

check "two page publishes with text (boot page + QTAP page turn)" \
  "grep -q 'gen=1 cleared=0 bytes=[1-9]' '$LOG' && grep -q 'gen=2 cleared=0 bytes=[1-9]' '$LOG'"
check "the tap reached a DIFFERENT page, not a re-render" \
  "grep -q 'gen=1 .*Chapter one' '$LOG' && grep -q 'gen=2 .*Chapter two' '$LOG'"
# Plain -F rather than -P: BSD grep (macOS) has no -P, and the bytes below are
# already UTF-8 in this file, so a literal match is both portable and exact.
check "curly quotes and accents survive as UTF-8" \
  "grep -qF 'café' '$LOG' && grep -qF '“curly' '$LOG'"
check "reader exit publishes the cleared page" \
  "grep -q 'READALOUD] page gen=[0-9]* cleared=1' '$LOG'"
check "no soft hyphens in any published text" \
  "! grep -qF \"$(printf '\\xc2\\xad')\" '$LOG'"

# --- rect geometry: every rect must actually sit on its word ----------------
#
# The published rects are what the highlight paints, and nothing else in this
# test would notice them drifting. They did drift: PageLine::yPos is the line's
# TOP, but the capture subtracted the font ascender from it as though it were a
# baseline, lifting every rect a full line -- so the highlight sat one line
# above the word being spoken. On the first line the result clamped to 0, which
# hid it. Caught only by looking at the panel on iOS.
#
# The assertion is deliberately about INK, not about the arithmetic: for each
# sampled rect, the band it covers must contain dark pixels within its own
# column range. That stays true if fonts, margins or line heights change, and
# fails for any systematic offset.
python3 - "$LOG" "$SHOT" <<'GEOEOF'
import re, sys, struct

log, shot = sys.argv[1], sys.argv[2]
# ONLY the first page's rects: the log also carries the post-QTAP page, and
# the screenshot is of page one. Comparing page two's rects against page one's
# pixels is how the first version of this check "failed" on a correct build.
rects = []
seen_first_page = False
for line in open(log, "rb").read().decode("utf-8", "replace").splitlines():
    if "READALOUD] page gen=" in line:
        if seen_first_page:
            break          # page two starts here
        seen_first_page = True
        continue
    m = re.search(r"READALOUD-RECT\] x=(\d+) y=(\d+) w=(\d+) h=(\d+).*?\"(.*)\"$", line)
    if m:
        rects.append(tuple(int(m.group(i)) for i in range(1, 5)) + (m.group(5),))
if not rects:
    print("FAIL: rect geometry — no rects in the log (LOG=2 not honored?)"); sys.exit(1)

try:
    raw = open(shot, "rb").read()
except OSError as e:
    print("FAIL: rect geometry — no screenshot (%s)" % e); sys.exit(1)

# Minimal BMP reader: bottom-up, 24/32bpp, no PIL dependency on CI.
off, w, h, bpp = struct.unpack_from("<I", raw, 10)[0], *struct.unpack_from("<ii", raw, 18), struct.unpack_from("<H", raw, 28)[0]
if bpp not in (24, 32):
    print("SKIP-GEO: unexpected %d bpp screenshot" % bpp); sys.exit(0)
stride = ((w * bpp // 8) + 3) & ~3
def dark(x, y):
    if not (0 <= x < w and 0 <= y < abs(h)): return False
    row = (abs(h) - 1 - y) if h > 0 else y
    i = off + row * stride + x * (bpp // 8)
    b, g, r = raw[i], raw[i+1], raw[i+2]
    return (r + g + b) // 3 < 128

# CONTAINMENT, not overlap. Overlap is too weak to be a pin: the ascender bug
# shifted every rect up by 26 px against a 35 px line box, so the shifted band
# still clipped the word and a touch-test passed on a broken build. Requiring
# the word's ink to sit INSIDE the rect (a few px of slack for descenders)
# fails for any systematic offset of more than a few pixels.
TOL = 5
def bandsFor(cols):
    """Contiguous runs of rows that have ink anywhere in these columns."""
    out, start = [], None
    for py in range(abs(h)):
        hit = any(dark(px, py) for px in cols)
        if hit and start is None:
            start = py
        elif not hit and start is not None:
            out.append((start, py - 1)); start = None
    if start is not None:
        out.append((start, abs(h) - 1))
    return out

bad = []
checked = 0
for (x, y, rw, rh, word) in rects[:25]:
    cols = range(x, min(x + rw, w))
    # The word's own ink band: the one overlapping this rect most. Picking by
    # overlap rather than by a window keeps a NEIGHBOURING line's ink in the
    # same columns from being merged into the measurement.
    best, bestOv = None, 0
    for (a, b) in bandsFor(cols):
        ov = min(b, y + rh) - max(a, y) + 1
        if ov > bestOv:
            best, bestOv = (a, b), ov
    if best is None:
        bad.append((word, x, y, rw, rh, "no ink in these columns")); continue
    checked += 1
    if best[0] < y - TOL or best[1] > y + rh + TOL:
        bad.append((word, x, y, rw, rh, "ink %d..%d outside band %d..%d"
                    % (best[0], best[1], y, y + rh)))
if bad:
    print("FAIL: rect geometry — %d of the first %d rects do not contain their word:"
          % (len(bad), min(25, len(rects))))
    for b in bad[:5]:
        print("        %-16s x=%d y=%d w=%d h=%d  %s" % b)
    sys.exit(1)
print("rect geometry: %d rects contain their word's ink" % checked)
GEOEOF
if [[ $? -ne 0 ]]; then fail=1; fi

LOG2="$CARD/run2.log"
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
CROSSPOINT_SIM_INPUT_SCRIPT='3000:QUIT' \
timeout 60 "$BIN" >"$LOG2" 2>&1
check "no publishes at all without CROSSPOINT_SIM_READALOUD_LOG" \
  "! grep -q 'READALOUD' '$LOG2'"

if [[ $fail -eq 0 ]]; then
  echo "test_read_aloud_capture: all passed"
fi
exit $fail
