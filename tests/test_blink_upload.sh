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
# name (R-03), a POST with no file in it is refused and writes nothing (R-02),
# names of 249 to 255 characters upload and 256 is refused by name (R-11), a
# refused curl -T says why (R-12), and a page upload that has gone silent stops
# holding its file name against curl (R-01).
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
# `exec`, so $! is the simulator itself and cleanup kills it, not a subshell.
( cd "$WORK" && exec env SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    CROSSPOINT_SIM_HTTP_PORT="$HTTP" CROSSPOINT_SIM_WS_STALL_MS="$STALL_MS" \
    CROSSPOINT_SIM_WIFI_NETWORKS='Alpha:-40:open' \
    CROSSPOINT_SIM_INPUT_SCRIPT="$SCRIPT" "$BIN" > "$WORK/sim.log" 2>&1 ) &
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
after="$(listing)"
check "$(is "$before" "$after")" \
  "the card after those three refusals: $([ "$before" = "$after" ] && echo "unchanged" || echo "CHANGED")"
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

# 12. The simulator is still running and still serving after all of that.
code=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "http://$H/api/status")
alive=0; kill -0 "$SIM_PID" 2>/dev/null && alive=1
check "$(both "$(is "$code" 200)" "$alive")" \
  "after every check: GET /api/status -> $code (want 200), the simulator is $([ "$alive" -eq 1 ] && echo "running" || echo "NOT running")"

if [ "$fails" -eq 0 ]; then echo "PASS: every Blink upload landed intact"; exit 0; fi
echo "FAIL: $fails Blink upload check(s) failed"
exit 1
