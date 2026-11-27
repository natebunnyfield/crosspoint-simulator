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
# It also pins what the 2026-11-27 review passes found and fixed (firmware
# docs/review-passes-2026-11-27.md): a name with '+' or '%' lands under its own
# name (R-03), a POST with no file in it is refused and writes nothing (R-02)
# and does not read an upload that is not there (a reboot on the device),
# names of 249 to 255 characters upload and 256 is refused by name (R-11), a
# refused curl -T says why (R-12), and a page upload that has gone silent stops
# holding its file name against curl (R-01). And a card that stops taking
# writes partway through a curl -F leaves no partial file behind, so the retry
# is not refused as "File already exists". And a curl -F that sends two files
# in one request is answered for both of them, not for the last one alone.
# And a file piped into curl -T (a chunked body, which the server cannot read)
# is refused and writes nothing, where the device stored an empty file under
# the name and said 201, or 204 with the book that was there gone.
# And a form posted to a route that takes no file reaches the firmware with its
# fields: New Folder, Rename and Move, which the File Transfer page posts as
# forms, answered "Missing ..." 400 on this simulator and on the iOS app.
#
# It boots the desktop PICCO simulator on a scratch card it makes itself, walks
# to File Transfer, and drives the server over loopback on a private port pair
# (CROSSPOINT_BLINK_TEST_PORT, default 18480, and the next port for the page's
# WebSocket). Every byte that lands is checked by md5 against what was sent.
#
# SKIP (exit 2) only for a missing precondition, all of them checked BEFORE the
# simulator is launched: no simulator_picco binary, no curl or python3, or the
# port already answering. Once the simulator has been launched, a server that
# never answers and a simulator that exits are both FAIL (exit 1): that is
# "File Transfer was opened and nothing can upload", the thing this test exists
# to catch, and it used to SKIP and leave the suite green (R-09). It needs no
# card of yours: it builds its own, so a missing fs_/.crosspoint is not a
# reason to skip here.
#
# Runs in about 30 s. bash 3.2 (macOS) must be able to parse it: no `case`
# inside $( ), no associative arrays.
#
# Usage: tests/test_blink_upload.sh <firmware-checkout-dir>
#        CROSSPOINT_BLINK_TEST_BIN=<program> overrides the binary (to run the
#        checks against a build from before a fix and watch them fail).
set -u
FIRMWARE_DIR="${1:?usage: test_blink_upload.sh <firmware-checkout-dir>}"
BIN="${CROSSPOINT_BLINK_TEST_BIN:-$FIRMWARE_DIR/.pio/build/simulator_picco/program}"
[ -x "$BIN" ] || { echo "SKIP: no $BIN (pio run -e simulator_picco)"; exit 2; }
command -v curl >/dev/null || { echo "SKIP: curl not found"; exit 2; }
command -v python3 >/dev/null || { echo "SKIP: python3 not found"; exit 2; }

HTTP="${CROSSPOINT_BLINK_TEST_PORT:-18480}"
WSPORT=$((HTTP + 1))
H="127.0.0.1:$HTTP"
# Refuse a port something else already answers on: its card is not ours.
if curl -s -m 1 -o /dev/null "http://$H/" 2>/dev/null; then
  echo "SKIP: port $HTTP already answers -- another server is running there"; exit 2
fi

WORK="$(mktemp -d)"
SIM_PID=""
WS_PID=""
cleanup() {
  if [ -n "$WS_PID" ]; then kill "$WS_PID" 2>/dev/null; wait "$WS_PID" 2>/dev/null; fi
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

# A page upload that gets no data is given up on after 30 s on the device.
# The simulator reads a shorter window from this variable so check 11 can
# wait it out; a binary from before that fix ignores it.
STALL_MS=5000

# Home forced by holding Back across the routing check (docs/headless-qa.md);
# an empty card starts the menu on its first row. On the Picco the rocker's
# upper end (UP) is next-item, so UP x3 is File Transfer; CONFIRM opens it,
# CONFIRM takes Join Network, CONFIRM joins the one scripted network.
SCRIPT="200:QTAP:BACK:2500;4000:UP;4900:UP;5800:UP;6800:CONFIRM;8000:CONFIRM;10000:CONFIRM;85000:QUIT"
# A full card, for check 12: no file this simulator writes may pass FULL_AT
# bytes. python3 sets the limit because it takes bytes; a shell's `ulimit -f`
# counts 512-byte blocks in one shell and 1024-byte blocks in the next (zsh
# and bash 3.2 on this Mac). SIGXFSZ is ignored, and stays ignored across the
# exec, so a write past the limit comes back short the way a full card's does
# and does not kill the process. Every other upload here is 5 MiB or less.
FULL_AT=6291456
# `exec` twice, so $! is the simulator itself and cleanup kills it, not a
# subshell or the python that set the limit.
( cd "$WORK" && exec env SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    CROSSPOINT_SIM_HTTP_PORT="$HTTP" CROSSPOINT_SIM_WS_STALL_MS="$STALL_MS" \
    CROSSPOINT_SIM_WIFI_NETWORKS='Alpha:-40:open' \
    CROSSPOINT_SIM_INPUT_SCRIPT="$SCRIPT" python3 -c 'import os, resource, signal, sys
hard = resource.getrlimit(resource.RLIMIT_FSIZE)[1]
resource.setrlimit(resource.RLIMIT_FSIZE, (int(sys.argv[1]), hard))
signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
os.execv(sys.argv[2], [sys.argv[2]])' "$FULL_AT" "$BIN" > "$WORK/sim.log" 2>&1 ) &
SIM_PID=$!

# From here on the simulator HAS been launched: nothing below may SKIP.
never_served() {  # never_served <what happened>
  echo "--- the screens it reached:"
  grep "Entering activity" "$WORK/sim.log" | tail -4
  echo "--- the end of its log:"
  tail -6 "$WORK/sim.log"
  echo "FAIL: $1"
  echo "FAIL: File Transfer's server never served, so no Blink upload is possible"
  exit 1
}
UP=0
for _ in $(seq 1 60); do
  if curl -s -m 1 -o /dev/null "http://$H/api/status"; then UP=1; break; fi
  kill -0 "$SIM_PID" 2>/dev/null || never_served "the simulator exited before its web server answered on port $HTTP"
  sleep 0.5
done
[ "$UP" -eq 1 ] || never_served "the simulator ran for 30 s and its web server never answered on port $HTTP"

fails=0
check() {  # check <ok 0|1> <what was done and what came back>
  if [ "$1" -eq 1 ]; then echo "PASS: $2"; else echo "FAIL: $2"; fails=$((fails + 1)); fi
}
md5of() {
  python3 -c 'import hashlib,sys
try: print(hashlib.md5(open(sys.argv[1],"rb").read()).hexdigest())
except OSError: print("MISSING")' "$1"
}
same() { [ "$(md5of "$1")" = "$(md5of "$2")" ] && echo 1 || echo 0; }
# card <sent> <on card>: how the card's copy compares, in words, for the
# PASS/FAIL line. Worked out from the files, so a failing line cannot say the
# bytes match when they do not (R-14).
card() {
  a="$(md5of "$1")"; b="$(md5of "$2")"
  if [ "$b" = MISSING ]; then echo "NOT on the card under that name"
  elif [ "$a" = "$b" ]; then echo "same bytes on the card"
  else echo "DIFFERENT bytes on the card"; fi
}
# is <got> <wanted>: 1 when equal.
is() { [ "$1" = "$2" ] && echo 1 || echo 0; }
# both <0|1> <0|1>: 1 when both are 1.
both() { [ "$1" -eq 1 ] && [ "$2" -eq 1 ] && echo 1 || echo 0; }
# has <text> <fragment>: 1 when the fragment is in the text. A helper, not a
# `case` inside $( ): macOS's bash 3.2 cannot parse that.
has() { case "$1" in *"$2"*) echo 1 ;; *) echo 0 ;; esac; }
# code_of <curl output ending in " [NNN]">
code_of() { c="${1##*\[}"; echo "${c%\]}"; }
# listing: every visible file and folder on the card with its size, sorted.
# Hidden entries are left out: the firmware keeps its own state in them.
listing() {
  python3 -c 'import os,sys
root=sys.argv[1]; out=[]
for d,dirs,files in os.walk(root):
    dirs[:]=[x for x in dirs if not x.startswith(".")]
    for f in files:
        if not f.startswith("."):
            p=os.path.join(d,f); out.append("%s %d" % (os.path.relpath(p,root), os.path.getsize(p)))
    for x in dirs: out.append(os.path.relpath(os.path.join(d,x),root)+"/")
print("\n".join(sorted(out)))' "$CARD"
}

BIG="$SRC/Café Book.epub"          # a space and a non-ASCII letter
head -c 5242880 /dev/urandom > "$BIG"
head -c 200000 /dev/urandom > "$SRC/second.epub"
head -c 7777 /dev/urandom > "$SRC/replacement.bin"
head -c 300000 /dev/urandom > "$SRC/Ñandú v2.epub"
head -c 4096 /dev/urandom > "$SRC/query.epub"
head -c 60000 /dev/urandom > "$SRC/C++ Primer.epub"
head -c 5000 /dev/urandom > "$SRC/100%25 Proof.epub"   # a literal %25 in the name
head -c 9000 /dev/urandom > "$SRC/small.epub"
head -c 50000 /dev/urandom > "$SRC/Stuck Book.epub"

# 1. WebDAV PUT, curl -T into an existing folder; curl names the file.
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$BIG" "http://$H/books/")
check "$(both "$(is "$code" 201)" "$(same "$BIG" "$CARD/books/Café Book.epub")")" \
  "curl -T 5 MB 'Café Book.epub' into /books/ -> $code (want 201), $(card "$BIG" "$CARD/books/Café Book.epub")"

# 2. A new folder (MKCOL), then curl -T into it.
code=$(curl -s -o /dev/null -w '%{http_code}' -X MKCOL "http://$H/New%20Shelf/")
check "$(both "$(is "$code" 201)" "$([ -d "$CARD/New Shelf" ] && echo 1 || echo 0)")" \
  "MKCOL /New Shelf/ -> $code (want 201), folder $([ -d "$CARD/New Shelf" ] && echo "on the card" || echo "NOT on the card")"
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$SRC/second.epub" "http://$H/New%20Shelf/")
check "$(both "$(is "$code" 201)" "$(same "$SRC/second.epub" "$CARD/New Shelf/second.epub")")" \
  "curl -T into the new folder -> $code (want 201), $(card "$SRC/second.epub" "$CARD/New Shelf/second.epub")"

# 3. Overwrite: curl -T to a file that exists replaces it (204 No Content).
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$SRC/replacement.bin" "http://$H/books/Caf%C3%A9%20Book.epub")
check "$(both "$(is "$code" 204)" "$(same "$SRC/replacement.bin" "$CARD/books/Café Book.epub")")" \
  "curl -T over an existing file -> $code (want 204), the new file: $(card "$SRC/replacement.bin" "$CARD/books/Café Book.epub")"

# 4. Multipart POST /upload, folder as a form field BEFORE the file -- the
#    order the device's parser needs (the shim here would accept either).
out=$(curl -s -w ' [%{http_code}]' -F "path=/New Shelf" -F "file=@$SRC/Ñandú v2.epub" "http://$H/upload")
check "$(both "$(is "$(code_of "$out")" 200)" "$(same "$SRC/Ñandú v2.epub" "$CARD/New Shelf/Ñandú v2.epub")")" \
  "curl -F path then file -> $out (want 200), $(card "$SRC/Ñandú v2.epub" "$CARD/New Shelf/Ñandú v2.epub")"

# 5. Multipart POST /upload, folder in the query string.
out=$(curl -s -w ' [%{http_code}]' -F "file=@$SRC/query.epub" "http://$H/upload?path=/books")
check "$(both "$(is "$(code_of "$out")" 200)" "$(same "$SRC/query.epub" "$CARD/books/query.epub")")" \
  "curl -F with ?path=/books -> $out (want 200), $(card "$SRC/query.epub" "$CARD/books/query.epub")"

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
check "$(both "$(is "$code" 200)" "$(is "$form_ok" 0)")" \
  "GET /upload -> $code (want 200), $([ "$form_ok" -eq 0 ] && echo "a plain form (path before file, no <script>)" || echo "NOT the plain form (multipart POST to /upload, path before file, no <script>)")"

# 7. A name curl has to escape lands under its own name (R-03). curl -T sends
#    'C++ Primer.epub' as C%2B%2B%20Primer.epub. The host's HTTP shim used to
#    decode the path and the firmware decoded it again, so each '+' became a
#    space ('C   Primer.epub') and '%25' became '%'. The device decodes once.
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$SRC/C++ Primer.epub" "http://$H/books/")
check "$(both "$(is "$code" 201)" "$(same "$SRC/C++ Primer.epub" "$CARD/books/C++ Primer.epub")")" \
  "curl -T 'C++ Primer.epub' into /books/ -> $code (want 201), $(card "$SRC/C++ Primer.epub" "$CARD/books/C++ Primer.epub"); /books/ holds: $(ls "$CARD/books" | tr '\n' '|')"
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$SRC/100%25 Proof.epub" "http://$H/books/")
check "$(both "$(is "$code" 201)" "$(same "$SRC/100%25 Proof.epub" "$CARD/books/100%25 Proof.epub")")" \
  "curl -T '100%25 Proof.epub' into /books/ -> $code (want 201), $(card "$SRC/100%25 Proof.epub" "$CARD/books/100%25 Proof.epub")"
code=$(curl -s -o "$WORK/back.bin" -w '%{http_code}' "http://$H/books/C%2B%2B%20Primer.epub")
check "$(both "$(is "$code" 200)" "$(same "$SRC/C++ Primer.epub" "$WORK/back.bin")")" \
  "GET /books/C%2B%2B%20Primer.epub -> $code (want 200), $([ "$(same "$SRC/C++ Primer.epub" "$WORK/back.bin")" -eq 1 ] && echo "the bytes sent" || echo "NOT the bytes sent")"
#    A '+' in a path is a '+'. The firmware's WebDAV handler used to decode
#    its paths with the server's FORM decoder, where '+' means a space. Its
#    own folder listing (PROPFIND) writes a '+' as it is, so the address it
#    gave for 'C++ Primer.epub' fetched 'C   Primer.epub' and answered 404; a
#    name typed into the address with a '+' was stored with a space and
#    answered 201; and a MOVE's Destination lost its '+' the same way.
href=$(curl -s -m 20 -X PROPFIND -H 'Depth: 1' "http://$H/books/" | python3 -c 'import re,sys
hrefs=[h for h in re.findall(r"<D:href>([^<]*)</D:href>", sys.stdin.read()) if "Primer" in h]
print(hrefs[0] if hrefs else "")')
code=000
[ -n "$href" ] && code=$(curl -s -g -m 20 -o "$WORK/listed.bin" -w '%{http_code}' "http://$H$href")
check "$(both "$(is "$code" 200)" "$(same "$SRC/C++ Primer.epub" "$WORK/listed.bin")")" \
  "PROPFIND /books/ lists 'C++ Primer.epub' as '${href:-(not listed)}'; GET of that address -> $code (want 200), $([ "$(same "$SRC/C++ Primer.epub" "$WORK/listed.bin")" -eq 1 ] && echo "the bytes sent" || echo "NOT the bytes sent")"
code=$(curl -s -m 20 -o /dev/null -w '%{http_code}' -T "$SRC/query.epub" "http://$H/books/Raw+Plus.txt")
check "$(both "$(is "$code" 201)" "$(same "$SRC/query.epub" "$CARD/books/Raw+Plus.txt")")" \
  "curl -T to the typed address /books/Raw+Plus.txt -> $code (want 201), as 'Raw+Plus.txt': $(card "$SRC/query.epub" "$CARD/books/Raw+Plus.txt"); as 'Raw Plus.txt': $([ -e "$CARD/books/Raw Plus.txt" ] && echo "a file (the '+' was read as a space)" || echo "nothing")"
code=$(curl -s -m 20 -o /dev/null -w '%{http_code}' -X MOVE -H "Destination: http://$H/books/Moved+Here.txt" "http://$H/books/Raw+Plus.txt")
check "$(both "$(is "$code" 201)" "$(same "$SRC/query.epub" "$CARD/books/Moved+Here.txt")")" \
  "MOVE /books/Raw+Plus.txt to Destination /books/Moved+Here.txt -> $code (want 201), as 'Moved+Here.txt': $(card "$SRC/query.epub" "$CARD/books/Moved+Here.txt"); /books/ holds: $(ls "$CARD/books" | tr '\n' '|')"

# 8. A POST with no file in it is refused and writes nothing (R-02). These
#    all follow good uploads (checks 4 and 5), and used to be answered 200
#    "File uploaded successfully" with the PREVIOUS upload's name.
before="$(listing)"
out=$(curl -s -w ' [%{http_code}]' -F "path=/books" -F "file=My Book.epub" "http://$H/upload")
check "$(both "$(is "$(code_of "$out")" 400)" "$(has "$out" "Nothing was uploaded")")" \
  "curl -F with the @ left off (file=My Book.epub) -> $out (want 400 'Nothing was uploaded')"
out=$(curl -s -w ' [%{http_code}]' -F "path=/books" "http://$H/upload")
check "$(both "$(is "$(code_of "$out")" 400)" "$(has "$out" "Nothing was uploaded")")" \
  "curl -F with the folder and no file -> $out (want 400 'Nothing was uploaded')"
out=$(curl -s -w ' [%{http_code}]' -X POST "http://$H/upload")
check "$(both "$(is "$(code_of "$out")" 400)" "$(has "$out" "Nothing was uploaded")")" \
  "a bare POST /upload -> $out (want 400 'Nothing was uploaded')"
#    A body with no form around it is the same refusal. On the device the
#    server hands such a body to the upload callback with no upload to read,
#    and a callback that reads one anyway is a null dereference and a reboot;
#    the simulator makes the same calls and logs that read instead.
out=$(curl -s -w ' [%{http_code}]' --data-binary "@$SRC/small.epub" "http://$H/upload?path=/books")
check "$(both "$(is "$(code_of "$out")" 400)" "$(has "$out" "Nothing was uploaded")")" \
  "curl --data-binary @small.epub (the file as the body, no form) -> $out (want 400 'Nothing was uploaded')"
out=$(curl -s -w ' [%{http_code}]' -d x "http://$H/upload")
check "$(both "$(is "$(code_of "$out")" 400)" "$(has "$out" "Nothing was uploaded")")" \
  "curl -d x -> $out (want 400 'Nothing was uploaded')"
after="$(listing)"
check "$(is "$before" "$after")" \
  "the card after those five refusals: $([ "$before" = "$after" ] && echo "unchanged" || echo "CHANGED")"
nulls="$(grep -c "upload() read with no upload in progress" "$WORK/sim.log")"
check "$(is "$nulls" 0)" \
  "requests whose upload callback read an upload that was not there: $nulls (want 0; each one reboots the device)"
out=$(curl -s -w ' [%{http_code}]' -F "path=/New Shelf" -F "file=@$SRC/small.epub" "http://$H/upload")
check "$(both "$(is "$(code_of "$out")" 200)" "$(same "$SRC/small.epub" "$CARD/New Shelf/small.epub")")" \
  "a real curl -F straight after the refusals -> $out (want 200), $(card "$SRC/small.epub" "$CARD/New Shelf/small.epub")"

# 9. Long names (R-11). curl -T writes to a temporary name first; for a name
#    of 249 to 255 characters the old '<name>.davtmp' was itself too long and
#    the upload failed. 256 is past what the card stores and is refused by
#    name, before anything is written.
N250="$(python3 -c "print('n' * 245 + '.epub')")"
N256="$(python3 -c "print('x' * 251 + '.epub')")"
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$SRC/small.epub" "http://$H/books/$N250")
check "$(both "$(is "$code" 201)" "$(same "$SRC/small.epub" "$CARD/books/$N250")")" \
  "curl -T to a 250-character name -> $code (want 201), $(card "$SRC/small.epub" "$CARD/books/$N250")"
before="$(listing)"
out=$(curl -s -w ' [%{http_code}]' -T "$SRC/small.epub" "http://$H/books/$N256")
after="$(listing)"
check "$(both "$(both "$(is "$(code_of "$out")" 400)" "$(has "$out" "too long")")" "$(is "$before" "$after")")" \
  "curl -T to a 256-character name -> $out (want 400 '... too long ...'), the card $([ "$before" = "$after" ] && echo "unchanged" || echo "CHANGED")"
left="$(find "$CARD" -name '*.davtmp' | wc -l | tr -d ' ')"
check "$(is "$left" 0)" "temporary .davtmp files left on the card: $left (want 0)"

# 10. A refused curl -T says why (R-12). Each of these was '500 Write failed -
#     incomplete upload or disk full'. The first is the easy slip in Blink:
#     the folder with no slash on the end, so curl adds no file name.
out=$(curl -s -w ' [%{http_code}]' -T "$SRC/small.epub" "http://$H/books")
check "$(both "$(is "$(code_of "$out")" 405)" "$(has "$out" "is a folder")")" \
  "curl -T to /books with no slash after it -> $out (want 405 '... is a folder ...')"
out=$(curl -s -w ' [%{http_code}]' -T "$SRC/small.epub" "http://$H/No%20Such%20Shelf/")
check "$(both "$(is "$(code_of "$out")" 409)" "$(has "$out" "does not exist")")" \
  "curl -T into a folder that is not there -> $out (want 409 '... does not exist ...')"

# 11. A page upload that has gone silent does not hold its file name (R-01).
#     This is the owner's case: the page's script dies mid-upload with its
#     socket open. curl must be told what holds the name (423), must get
#     through under another name at once, and must get through under the same
#     name once the page has sent nothing for the stall window -- with the
#     page's socket STILL open. Before the fix the name stayed held until the
#     tab closed and curl -T answered 500.
python3 - "$WSPORT" "Stuck Book.epub" /books 5242880 "$WORK/ws.out" <<'PY' &
import base64, os, struct, socket, sys, time
port, name, folder, size, out = int(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
def say(text):
    with open(out, "a") as f: f.write(text + "\n")
try:
    s = socket.create_connection(("127.0.0.1", port), timeout=5)
    key = base64.b64encode(os.urandom(16)).decode()
    s.sendall(("GET / HTTP/1.1\r\nHost: 127.0.0.1:%d\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
               "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (port, key)).encode())
    hdr = b""
    while b"\r\n\r\n" not in hdr:
        c = s.recv(1)
        if not c: raise EOFError("closed during the handshake")
        hdr += c
    def frame(op, data):
        mask = os.urandom(4); n = len(data)
        if n < 126: h = struct.pack("!BB", 0x80 | op, 0x80 | n)
        elif n < 65536: h = struct.pack("!BBH", 0x80 | op, 0x80 | 126, n)
        else: h = struct.pack("!BBQ", 0x80 | op, 0x80 | 127, n)
        return h + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    def exact(n):
        d = b""
        while len(d) < n:
            c = s.recv(n - len(d))
            if not c: raise EOFError("closed by the server")
            d += c
        return d
    def message():
        _, b2 = exact(2); n = b2 & 0x7f
        if n == 126: n = struct.unpack("!H", exact(2))[0]
        elif n == 127: n = struct.unpack("!Q", exact(8))[0]
        return exact(n).decode(errors="replace")
    s.sendall(frame(1, ("START:%s:%d:%s" % (name, size, folder)).encode()))
    reply = message()
    s.sendall(frame(2, os.urandom(4096)))
    say("HOLDING " + reply)
    # Say nothing more and keep the socket open; note what the server sends.
    s.settimeout(40)
    try:
        while True: say("SERVER " + message())
    except (EOFError, socket.timeout, OSError) as e:
        say("END " + str(e))
except Exception as e:
    say("BROKEN " + str(e))
PY
WS_PID=$!
held=0
for _ in $(seq 1 40); do
  if grep -q "^HOLDING READY" "$WORK/ws.out" 2>/dev/null; then held=1; break; fi
  grep -Eq "^(BROKEN|HOLDING)" "$WORK/ws.out" 2>/dev/null && break
  sleep 0.1
done
check "$held" "a page upload of 'Stuck Book.epub' started over the WebSocket and went silent: $(head -1 "$WORK/ws.out" 2>/dev/null || echo "no answer") (want HOLDING READY)"
t0=$(date +%s)
out=$(curl -s -w ' [%{http_code}]' -T "$SRC/Stuck Book.epub" "http://$H/books/")
check "$(both "$(is "$(code_of "$out")" 423)" "$(has "$out" "Stuck Book.epub")")" \
  "curl -T of the name the page holds -> $out (want 423 naming the upload)"
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$SRC/Stuck Book.epub" "http://$H/books/Stuck%20Book-2.epub")
check "$(both "$(is "$code" 201)" "$(same "$SRC/Stuck Book.epub" "$CARD/books/Stuck Book-2.epub")")" \
  "curl -T under another name meanwhile -> $code (want 201), $(card "$SRC/Stuck Book.epub" "$CARD/books/Stuck Book-2.epub")"
# Wait out the stall window, measured from before the 423 above (the page's
# last data came earlier still), plus a second.
while [ $(( $(date +%s) - t0 )) -lt $(( STALL_MS / 1000 + 2 )) ]; do sleep 0.2; done
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$SRC/Stuck Book.epub" "http://$H/books/")
open_still=0; kill -0 "$WS_PID" 2>/dev/null && ! grep -Eq "^(END|BROKEN)" "$WORK/ws.out" && open_still=1
check "$(both "$(both "$(is "$code" 201)" "$(same "$SRC/Stuck Book.epub" "$CARD/books/Stuck Book.epub")")" "$open_still")" \
  "curl -T of that name after $((STALL_MS / 1000)) s of silence from the page -> $code (want 201), $(card "$SRC/Stuck Book.epub" "$CARD/books/Stuck Book.epub"), the page's socket $([ "$open_still" -eq 1 ] && echo "still open" || echo "NOT open any more"); the page was told: $(grep "^SERVER" "$WORK/ws.out" | head -1 || true)"
kill "$WS_PID" 2>/dev/null; wait "$WS_PID" 2>/dev/null; WS_PID=""

# 12. The card stops taking writes partway through an upload (a full card).
#     Nothing may be left under the file's name: a truncated book in the
#     library, and a retry refused as "File already exists". curl -T always
#     discarded its temporary file; curl -F and the plain form closed the
#     partial file and left it. The simulator cannot write a file past FULL_AT
#     bytes (set at launch), and the curl -T line doubles as the proof that
#     the limit is in force: if it answers 201, these checks tested nothing.
head -c $((FULL_AT + 700000)) /dev/urandom > "$SRC/Too Big.epub"
head -c $((FULL_AT + 100)) /dev/urandom > "$SRC/Just Over.epub"
gone() { [ -e "$1" ] && echo 0 || echo 1; }
left() { [ -e "$1" ] && echo "a $(wc -c < "$1" | tr -d ' ')-byte file LEFT on the card" || echo "nothing left on the card"; }
out=$(curl -s -g -w ' [%{http_code}]' -T "$SRC/Too Big.epub" "http://$H/books/Too%20Big%20Put.epub")
check "$(both "$(both "$(is "$(code_of "$out")" 500)" "$(has "$out" "discarded")")" "$(gone "$CARD/books/Too Big Put.epub")")" \
  "curl -T of a file the card has no room for -> $out (want 500 '... discarded'; a 201 means the test's size limit is not in force), $(left "$CARD/books/Too Big Put.epub")"
left_tmp="$(find "$CARD" -name '*.davtmp' | wc -l | tr -d ' ')"
check "$(is "$left_tmp" 0)" "temporary .davtmp files left by that: $left_tmp (want 0)"
#     The write that fails is a full buffer in the middle of the body.
out=$(curl -s -w ' [%{http_code}]' -F "path=/books" -F "file=@$SRC/Too Big.epub" "http://$H/upload")
check "$(both "$(both "$(is "$(code_of "$out")" 500)" "$(has "$out" "discarded")")" "$(gone "$CARD/books/Too Big.epub")")" \
  "curl -F of a file the card has no room for -> $out (want 500 '... discarded'), $(left "$CARD/books/Too Big.epub")"
#     The retry once there is room: a file that fits, under the same name.
out=$(curl -s -w ' [%{http_code}]' -F "path=/books" -F "file=@$SRC/small.epub;filename=Too Big.epub" "http://$H/upload")
check "$(both "$(is "$(code_of "$out")" 200)" "$(same "$SRC/small.epub" "$CARD/books/Too Big.epub")")" \
  "curl -F under the same name once it fits -> $out (want 200), $(card "$SRC/small.epub" "$CARD/books/Too Big.epub")"
#     The write that fails is the last one: FULL_AT is a whole number of the
#     server's 4096-byte buffers, so the 100 bytes over go out when the body ends.
out=$(curl -s -w ' [%{http_code}]' -F "path=/books" -F "file=@$SRC/Just Over.epub" "http://$H/upload")
check "$(both "$(both "$(is "$(code_of "$out")" 500)" "$(has "$out" "discarded")")" "$(gone "$CARD/books/Just Over.epub")")" \
  "curl -F of a file 100 bytes over what the card has room for -> $out (want 500 '... discarded'), $(left "$CARD/books/Just Over.epub")"

# 13. Two files in one curl -F are answered for both. The reply used to speak
#     for the last file alone: a refused first file read as "200 File uploaded
#     successfully: <the second>", and a stored first file as a bare 400 for
#     the second. /New Shelf/small.epub is on the card since check 8, so
#     sending it again is the refusal ("File already exists").
for n in b c d e; do head -c 3000 /dev/urandom > "$SRC/multi-$n.epub"; done
kept="$(md5of "$CARD/New Shelf/small.epub")"
out=$(curl -s -w ' [%{http_code}]' --form-string "path=/New Shelf" -F "file=@$SRC/small.epub" -F "file=@$SRC/multi-b.epub" "http://$H/upload")
said=$(both "$(both "$(has "$out" "1 of 2 files stored")" "$(has "$out" "small.epub (File already exists")")" "$(has "$out" "Stored: multi-b.epub")")
check "$(both "$(both "$(is "$(code_of "$out")" 400)" "$said")" "$(same "$SRC/multi-b.epub" "$CARD/New Shelf/multi-b.epub")")" \
  "curl -F of a file that exists, then a new one -> $out (want 400 '1 of 2 files stored. Not stored: small.epub (File already exists ...). Stored: multi-b.epub'), the new one: $(card "$SRC/multi-b.epub" "$CARD/New Shelf/multi-b.epub")"
out=$(curl -s -w ' [%{http_code}]' --form-string "path=/New Shelf" -F "file=@$SRC/multi-c.epub" -F "file=@$SRC/small.epub" "http://$H/upload")
said=$(both "$(both "$(has "$out" "1 of 2 files stored")" "$(has "$out" "small.epub (File already exists")")" "$(has "$out" "Stored: multi-c.epub")")
check "$(both "$(both "$(is "$(code_of "$out")" 400)" "$said")" "$(same "$SRC/multi-c.epub" "$CARD/New Shelf/multi-c.epub")")" \
  "curl -F of a new file, then one that exists -> $out (want 400 '1 of 2 files stored. Not stored: small.epub (File already exists ...). Stored: multi-c.epub'), the new one: $(card "$SRC/multi-c.epub" "$CARD/New Shelf/multi-c.epub")"
check "$(is "$kept" "$(md5of "$CARD/New Shelf/small.epub")")" \
  "the file that was already there after those two: $([ "$kept" = "$(md5of "$CARD/New Shelf/small.epub")" ] && echo "unchanged" || echo "CHANGED")"
out=$(curl -s -w ' [%{http_code}]' --form-string "path=/New Shelf" -F "file=@$SRC/multi-d.epub" -F "file=@$SRC/multi-e.epub" "http://$H/upload")
check "$(both "$(both "$(is "$(code_of "$out")" 200)" "$(has "$out" "2 files uploaded successfully: multi-d.epub, multi-e.epub")")" "$(both "$(same "$SRC/multi-d.epub" "$CARD/New Shelf/multi-d.epub")" "$(same "$SRC/multi-e.epub" "$CARD/New Shelf/multi-e.epub")")")" \
  "curl -F of two new files -> $out (want 200 '2 files uploaded successfully: multi-d.epub, multi-e.epub'), the first: $(card "$SRC/multi-d.epub" "$CARD/New Shelf/multi-d.epub"), the second: $(card "$SRC/multi-e.epub" "$CARD/New Shelf/multi-e.epub")"
before="$(listing)"
out=$(curl -s -w ' [%{http_code}]' --form-string "path=/New Shelf" -F "file=@$SRC/multi-d.epub" -F "file=@$SRC/multi-e.epub" "http://$H/upload")
after="$(listing)"
check "$(both "$(both "$(is "$(code_of "$out")" 400)" "$(has "$out" "0 of 2 files stored. Not stored: multi-d.epub (File already exists: multi-d.epub) and 1 more")")" "$(is "$before" "$after")")" \
  "the same two again -> $out (want 400 '0 of 2 files stored. Not stored: multi-d.epub (File already exists: multi-d.epub) and 1 more'), the card $([ "$before" = "$after" ] && echo "unchanged" || echo "CHANGED")"
#     One file per request is answered as it always was, straight after.
out=$(curl -s -w ' [%{http_code}]' --form-string "path=/New Shelf" -F "file=@$SRC/multi-e.epub;filename=multi-f.epub" "http://$H/upload")
check "$(both "$(is "$out" "File uploaded successfully: multi-f.epub [200]")" "$(same "$SRC/multi-e.epub" "$CARD/New Shelf/multi-f.epub")")" \
  "one new file straight after -> $out (want exactly 'File uploaded successfully: multi-f.epub [200]'), $(card "$SRC/multi-e.epub" "$CARD/New Shelf/multi-f.epub")"
out=$(curl -s -w ' [%{http_code}]' --form-string "path=/New Shelf" -F "file=@$SRC/multi-e.epub" "http://$H/upload")
check "$(is "$out" "File already exists: multi-e.epub [400]")" \
  "one file that exists straight after -> $out (want exactly 'File already exists: multi-e.epub [400]')"

# 14. A file piped into curl -T. curl cannot know the length, so it sends the
#     body chunked, and the server cannot read chunks: its parser takes the
#     body as zero bytes long. That used to end as an empty file under the
#     name and 201, or 204 with an existing book replaced by 0 bytes. It did
#     so on the device alone: this shim refused the request itself (501) and
#     the firmware never saw it. Now the shim hands it over as the device's
#     parser does, and the firmware refuses it and leaves the card alone.
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$SRC/small.epub" "http://$H/books/Piped.epub")
before="$(listing)"
out=$(cat "$SRC/multi-b.epub" | curl -s -g -m 20 -w ' [%{http_code}]' -T - "http://$H/books/Piped.epub")
check "$(both "$(both "$(is "$(code_of "$out")" 411)" "$(has "$out" "by name")")" "$(both "$(is "$code" 201)" "$(same "$SRC/small.epub" "$CARD/books/Piped.epub")")")" \
  "cat FILE | curl -T - over a book that is there (put there first -> $code, want 201) -> $out (want 411 '... Give curl the file by name ...'), the book that was there: $(card "$SRC/small.epub" "$CARD/books/Piped.epub")"
out=$(cat "$SRC/multi-b.epub" | curl -s -g -m 20 -w ' [%{http_code}]' -T - "http://$H/books/Piped%20New.epub")
after="$(listing)"
check "$(both "$(both "$(is "$(code_of "$out")" 411)" "$(gone "$CARD/books/Piped New.epub")")" "$(is "$before" "$after")")" \
  "cat FILE | curl -T - to a new name -> $out (want 411), $(left "$CARD/books/Piped New.epub"), the card $([ "$before" = "$after" ] && echo "unchanged" || echo "CHANGED")"
left_tmp="$(find "$CARD" -name '*.davtmp' | wc -l | tr -d ' ')"
check "$(is "$left_tmp" 0)" "temporary .davtmp files left by the two piped uploads: $left_tmp (want 0)"
#     The same file given by name, straight after, lands.
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$SRC/multi-b.epub" "http://$H/books/Piped%20New.epub")
check "$(both "$(is "$code" 201)" "$(same "$SRC/multi-b.epub" "$CARD/books/Piped New.epub")")" \
  "curl -T of that file by name straight after -> $code (want 201), $(card "$SRC/multi-b.epub" "$CARD/books/Piped New.epub")"

# 15. A form posted to a route that takes no file: New Folder, Rename and
#     Move, as the File Transfer page posts them (a FormData POST is
#     multipart) and as `curl -F` does from Blink. The device reads a form's
#     fields into the request whatever the route; this shim read them only for
#     a route that takes an upload, so all three answered "Missing ..." 400
#     here and on the iOS app. A form field is not URL-encoded, so the '+' and
#     the '%25' in the folder's name are the name.
FORM_DIR="$CARD/Form+Shelf 50%25"
out=$(curl -s -m 20 -w ' [%{http_code}]' --form-string 'name=Form+Shelf 50%25' --form-string 'path=/' "http://$H/mkdir")
check "$(both "$(is "$(code_of "$out")" 200)" "$([ -d "$FORM_DIR" ] && echo 1 || echo 0)")" \
  "form POST /mkdir name='Form+Shelf 50%25' -> $out (want 200), folder $([ -d "$FORM_DIR" ] && echo "on the card under that name" || echo "NOT on the card under that name")"
code=$(curl -s -o /dev/null -w '%{http_code}' -T "$SRC/query.epub" "http://$H/books/Form.epub")
out=$(curl -s -m 20 -w ' [%{http_code}]' --form-string 'path=/books/Form.epub' --form-string 'name=Form Renamed.epub' "http://$H/rename")
check "$(both "$(both "$(is "$(code_of "$out")" 200)" "$(same "$SRC/query.epub" "$CARD/books/Form Renamed.epub")")" "$(gone "$CARD/books/Form.epub")")" \
  "form POST /rename of a book (put there first -> $code, want 201) -> $out (want 200), under the new name: $(card "$SRC/query.epub" "$CARD/books/Form Renamed.epub"), the old name: $(left "$CARD/books/Form.epub")"
out=$(curl -s -m 20 -w ' [%{http_code}]' --form-string 'path=/books/Form Renamed.epub' --form-string 'dest=/Form+Shelf 50%25' "http://$H/move")
check "$(both "$(both "$(is "$(code_of "$out")" 200)" "$(same "$SRC/query.epub" "$FORM_DIR/Form Renamed.epub")")" "$(gone "$CARD/books/Form Renamed.epub")")" \
  "form POST /move into that folder -> $out (want 200), in the folder: $(card "$SRC/query.epub" "$FORM_DIR/Form Renamed.epub"), where it was: $(left "$CARD/books/Form Renamed.epub")"

# 16. The simulator is still running and still serving after all of that.
code=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "http://$H/api/status")
alive=0; kill -0 "$SIM_PID" 2>/dev/null && alive=1
check "$(both "$(is "$code" 200)" "$alive")" \
  "after every check: GET /api/status -> $code (want 200), the simulator is $([ "$alive" -eq 1 ] && echo "running" || echo "NOT running")"

if [ "$fails" -eq 0 ]; then echo "PASS: every Blink upload landed intact"; exit 0; fi
echo "FAIL: $fails Blink upload check(s) failed"
exit 1
