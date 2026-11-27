#!/usr/bin/env bash
# Uploads that need no web page (owner 2026-11-27: "make it possible for blink
# to upload a file no matter what bugs happen in file transfer screen").
#
# Blink Shell on an iPhone has curl and no browser, and for months the File
# Transfer page's script did not parse (firmware B-080), which silently blocked
# every upload made through the page. This pins the two uploads curl makes with
# no page at all, against the real firmware's server, plus the plain-HTML form
# the firmware serves at GET /upload for a browser with no working script.
# The commands are the ones written in the firmware's docs/upload-from-blink.md,
# with only the host and port changed.
#
# It boots the desktop PICCO simulator on a scratch card it makes itself, walks
# to File Transfer, and drives the server over loopback on a private port pair
# (CROSSPOINT_BLINK_TEST_PORT, default 18480 and 18481). Every byte that lands is
# checked by md5 against what was sent.
#
# SKIP (exit 2), not FAIL, when there is no simulator_picco binary, no curl or
# python3, the port is taken, or the server never comes up (the menu walk can
# drift). It needs no card of yours: it builds its own, so a missing
# fs_/.crosspoint is not a reason to skip here.
#
# Usage: tests/test_blink_upload.sh <firmware-checkout-dir>
set -u
FIRMWARE_DIR="${1:?usage: test_blink_upload.sh <firmware-checkout-dir>}"
BIN="$FIRMWARE_DIR/.pio/build/simulator_picco/program"
[ -x "$BIN" ] || { echo "SKIP: no $BIN (pio run -e simulator_picco)"; exit 2; }
command -v curl >/dev/null || { echo "SKIP: curl not found"; exit 2; }
command -v python3 >/dev/null || { echo "SKIP: python3 not found"; exit 2; }

HTTP="${CROSSPOINT_BLINK_TEST_PORT:-18480}"
H="127.0.0.1:$HTTP"
# Refuse a port something else already answers on: its card is not ours.
if curl -s -m 1 -o /dev/null "http://$H/" 2>/dev/null; then
  echo "SKIP: port $HTTP already answers -- another server is running there"; exit 2
fi

WORK="$(mktemp -d)"
SIM_PID=""
cleanup() {
  if [ -n "$SIM_PID" ]; then kill "$SIM_PID" 2>/dev/null; wait "$SIM_PID" 2>/dev/null; fi
  rm -rf "$WORK"
}
trap cleanup EXIT

CARD="$WORK/fs_"
SRC="$WORK/src"
mkdir -p "$CARD/books" "$SRC"
# Beside the card, so the desktop settings watcher neither reads the
# developer's own file nor writes a template into this run.
echo '{}' > "$WORK/settings.json"

# Home forced by holding Back across the routing check (docs/headless-qa.md);
# an empty card starts the menu on its first row. On the Picco the rocker's
# upper end (UP) is next-item, so UP x3 is File Transfer; CONFIRM opens it,
# CONFIRM takes Join Network, CONFIRM joins the one scripted network.
SCRIPT="200:QTAP:BACK:2500;4000:UP;4900:UP;5800:UP;6800:CONFIRM;8000:CONFIRM;10000:CONFIRM;85000:QUIT"
# `exec`, so $! is the simulator itself and cleanup kills it, not a subshell.
( cd "$WORK" && exec env SDL_VIDEODRIVER=dummy CROSSPOINT_SIM_HTTP_PORT="$HTTP" \
    CROSSPOINT_SIM_WIFI_NETWORKS='Alpha:-40:open' \
    CROSSPOINT_SIM_INPUT_SCRIPT="$SCRIPT" "$BIN" > "$WORK/sim.log" 2>&1 ) &
SIM_PID=$!

UP=0
for _ in $(seq 1 60); do
  if curl -s -m 1 -o /dev/null "http://$H/api/status"; then UP=1; break; fi
  kill -0 "$SIM_PID" 2>/dev/null || { echo "SKIP: simulator exited before the server came up"; exit 2; }
  sleep 0.5
done
if [ "$UP" -ne 1 ]; then
  grep "Entering activity" "$WORK/sim.log" | tail -3
  echo "SKIP: web server never came up (menu walk may have drifted)"; exit 2
fi

fails=0
check() {  # check <ok 0|1> <message>
  if [ "$1" -eq 1 ]; then echo "PASS: $2"; else echo "FAIL: $2"; fails=$((fails + 1)); fi
}
md5of() {
  python3 -c 'import hashlib,sys
try: print(hashlib.md5(open(sys.argv[1],"rb").read()).hexdigest())
except OSError: print("MISSING")' "$1"
}
same() { [ "$(md5of "$1")" = "$(md5of "$2")" ] && echo 1 || echo 0; }
# posted <curl output ending in [code]> <sent> <on card>: a 200 and the bytes.
# A helper, not a `case` inside $( ): macOS's bash 3.2 cannot parse that.
posted() { [ "${1%\[200\]}" != "$1" ] && same "$2" "$3" || echo 0; }

BIG="$SRC/Café Book.epub"          # a space and a non-ASCII letter
head -c 5242880 /dev/urandom > "$BIG"
head -c 200000 /dev/urandom > "$SRC/second.epub"
head -c 7777 /dev/urandom > "$SRC/replacement.bin"
head -c 300000 /dev/urandom > "$SRC/Ñandú v2.epub"
head -c 4096 /dev/urandom > "$SRC/query.epub"

# 1. WebDAV PUT, curl -T into an existing folder; curl names the file.
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$BIG" "http://$H/books/")
check "$([ "$code" = 201 ] && same "$BIG" "$CARD/books/Café Book.epub" || echo 0)" \
  "curl -T 5 MB 'Café Book.epub' into /books/ -> $code, bytes match"

# 2. A new folder (MKCOL), then curl -T into it.
code=$(curl -s -o /dev/null -w '%{http_code}' -X MKCOL "http://$H/New%20Shelf/")
check "$([ "$code" = 201 ] && [ -d "$CARD/New Shelf" ] && echo 1 || echo 0)" "MKCOL /New Shelf/ -> $code"
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$SRC/second.epub" "http://$H/New%20Shelf/")
check "$([ "$code" = 201 ] && same "$SRC/second.epub" "$CARD/New Shelf/second.epub" || echo 0)" \
  "curl -T into the new folder -> $code, bytes match"

# 3. Overwrite: curl -T to a file that exists replaces it (204 No Content).
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$SRC/replacement.bin" "http://$H/books/Caf%C3%A9%20Book.epub")
check "$([ "$code" = 204 ] && same "$SRC/replacement.bin" "$CARD/books/Café Book.epub" || echo 0)" \
  "curl -T over an existing file -> $code, new bytes on the card"

# 4. Multipart POST /upload, folder as a form field BEFORE the file -- the
#    order the device's parser needs (the shim here would accept either).
out=$(curl -s -w ' [%{http_code}]' -F "path=/New Shelf" -F "file=@$SRC/Ñandú v2.epub" "http://$H/upload")
check "$(posted "$out" "$SRC/Ñandú v2.epub" "$CARD/New Shelf/Ñandú v2.epub")" \
  "curl -F path then file -> $out, bytes match"

# 5. Multipart POST /upload, folder in the query string.
out=$(curl -s -w ' [%{http_code}]' -F "file=@$SRC/query.epub" "http://$H/upload?path=/books")
check "$(posted "$out" "$SRC/query.epub" "$CARD/books/query.epub")" \
  "curl -F with ?path=/books -> $out, bytes match"

# 6. The no-script form: served, posts multipart to /upload, the folder field
#    ahead of the file input, and no script anywhere in it.
FORM="$WORK/form.html"
code=$(curl -s -o "$FORM" -w '%{http_code}' "http://$H/upload")
FORM="$FORM" python3 - <<'PY'
import os, sys
html = open(os.environ['FORM'], encoding='utf-8', errors='replace').read()
low = html.lower()
ok = ('<form' in low and 'action="/upload"' in low and 'method="post"' in low
      and 'enctype="multipart/form-data"' in low and '<script' not in low
      and 0 <= low.find('name="path"') < low.find('type="file"'))
sys.exit(0 if ok else 1)
PY
form_ok=$?
check "$([ "$code" = 200 ] && [ "$form_ok" -eq 0 ] && echo 1 || echo 0)" \
  "GET /upload -> $code, a plain form (path before file, no <script>)"

if [ "$fails" -eq 0 ]; then echo "PASS: every Blink upload landed intact"; exit 0; fi
echo "FAIL: $fails Blink upload check(s) failed"
exit 1
