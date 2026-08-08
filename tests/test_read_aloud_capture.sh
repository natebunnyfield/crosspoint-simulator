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

CARD="$(mktemp -d)"
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
CROSSPOINT_SIM_READALOUD_LOG=1 SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
CROSSPOINT_SIM_INPUT_SCRIPT='6000:QTAP:RIGHT;12000:BACK;15000:QUIT' \
timeout 90 "$BIN" >"$LOG" 2>&1

check "two page publishes with text (boot page + QTAP page turn)" \
  "grep -q 'gen=1 cleared=0 bytes=[1-9]' '$LOG' && grep -q 'gen=2 cleared=0 bytes=[1-9]' '$LOG'"
check "the tap reached a DIFFERENT page, not a re-render" \
  "grep -q 'gen=1 .*Chapter one' '$LOG' && grep -q 'gen=2 .*Chapter two' '$LOG'"
check "curly quotes and accents survive as UTF-8" \
  "grep -qP 'caf\xc3\xa9' '$LOG' && grep -qP '\xe2\x80\x9ccurly' '$LOG'"
check "reader exit publishes the cleared page" \
  "grep -q 'READALOUD] page gen=[0-9]* cleared=1' '$LOG'"
check "no soft hyphens in any published text" \
  "! grep -qP '\\xc2\\xad' '$LOG'"

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
