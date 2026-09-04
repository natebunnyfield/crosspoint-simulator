#!/usr/bin/env bash
# Pins the 2026-09-04 network-surface hardening (docs/network-surface-hunt-2026-09-04.md).
# The iOS app binds these servers on ALL interfaces, so a crafted request from
# the phone's Wi-Fi must not crash it, escape the card, or park a channel. Each
# fix was verified with an ad-hoc probe when it landed; this makes those
# repeatable so a regression is caught headlessly.
#
# It launches the real firmware, navigates to File Transfer to start the
# server, and drives it over loopback (the port pair is moved to 18080/18081
# so a dev machine's own 8080 does not collide). SKIP (exit 2), not FAIL, when
# the binary/card is missing OR the server never comes up -- the menu walk can
# drift with the card contents, and a pin must not go red for that.
#
# Usage: tests/test_web_server_hardening.sh <firmware-checkout-dir>
set -u
FIRMWARE_DIR="${1:?usage: test_web_server_hardening.sh <firmware-checkout-dir>}"
BIN=""
for env_name in simulator_x3 simulator; do
  CAND="$FIRMWARE_DIR/.pio/build/$env_name/program"
  [ -x "$CAND" ] && { BIN="$CAND"; break; }
done
[ -n "$BIN" ] || { echo "SKIP: no simulator binary under $FIRMWARE_DIR/.pio/build"; exit 2; }
SETTINGS="$FIRMWARE_DIR/fs_/.crosspoint/settings.json"
[ -f "$SETTINGS" ] || { echo "SKIP: $SETTINGS not found -- run the simulator once first"; exit 2; }
command -v python3 >/dev/null || { echo "SKIP: python3 not found"; exit 2; }

HTTP=18080
WS=18081
# Refuse to run against a foreign server on the port: an orphaned sim (or
# anything) already on 18080 would answer our probes from a different card and
# fail them for no reason. SKIP rather than test the wrong process.
if python3 -c "import socket,sys
s=socket.socket(); s.settimeout(0.3)
sys.exit(0 if s.connect_ex(('127.0.0.1',$HTTP))==0 else 1)" 2>/dev/null; then
  echo "SKIP: port $HTTP already in use -- another server is running there"; exit 2
fi
WORK="$(mktemp -d)"
SIM_PID=""
cleanup() {
  if [ -n "$SIM_PID" ]; then kill "$SIM_PID" 2>/dev/null; wait "$SIM_PID" 2>/dev/null; fi
  rm -rf "$WORK"
}
trap cleanup EXIT

mkdir -p "$WORK/fs_/.crosspoint" "$WORK/fs_/books"
cp "$SETTINGS" "$WORK/fs_/.crosspoint/settings.json"
echo "seed" > "$WORK/fs_/books/seed.txt"

# Home forced by holding Back across the routing check (docs/headless-qa.md);
# with no books the menu starts on row 0. RIGHT to File Transfer, CONFIRM to
# open it, CONFIRM to start the server. Extra CONFIRMs are harmless.
SCRIPT="200:QTAP:BACK:2500;4000:RIGHT;4900:RIGHT;5800:RIGHT;6800:CONFIRM;8000:CONFIRM;10000:CONFIRM;60000:QUIT"
( cd "$WORK" && env SDL_VIDEODRIVER=dummy CROSSPOINT_SIM_HTTP_PORT="$HTTP" \
    CROSSPOINT_SIM_WIFI_NETWORKS='Alpha:-40:open' \
    CROSSPOINT_SIM_INPUT_SCRIPT="$SCRIPT" "$BIN" > "$WORK/sim.log" 2>&1 ) &
SIM_PID=$!

# Wait up to 25 s for the server to accept.
UP=0
for _ in $(seq 1 50); do
  if python3 -c "import socket,sys; s=socket.socket(); s.settimeout(0.4)
try:
    s.connect(('127.0.0.1',$HTTP)); s.close(); sys.exit(0)
except Exception: sys.exit(1)" 2>/dev/null; then UP=1; break; fi
  kill -0 "$SIM_PID" 2>/dev/null || { echo "SKIP: simulator exited before the server came up"; exit 2; }
  sleep 0.5
done
[ "$UP" -eq 1 ] || { echo "SKIP: web server never came up (menu walk may have drifted)"; exit 2; }

WORK="$WORK" HTTP="$HTTP" WS="$WS" SIM_PID="$SIM_PID" python3 - <<'PY'
import os, socket, time, base64, struct, subprocess, sys
WORK=os.environ['WORK']; HTTP=int(os.environ['HTTP']); WS=int(os.environ['WS'])
BOOKS=os.path.join(WORK,'fs_','books')
fails=[]
def check(cond, msg):
    print(("PASS" if cond else "FAIL")+": "+msg)
    if not cond: fails.append(msg)

def http(method, path, headers=None, body=b'', timeout=8):
    s=socket.create_connection(('127.0.0.1',HTTP), timeout=timeout)
    h=dict(headers or {})
    if body and 'Content-Length' not in h: h['Content-Length']=str(len(body))
    req=f'{method} {path} HTTP/1.1\r\nHost: x\r\n'+''.join(f'{k}: {v}\r\n' for k,v in h.items())+'\r\n'
    s.sendall(req.encode('latin1')+body)
    out=b''
    try:
        while len(out)<65536:
            c=s.recv(4096)
            if not c: break
            out+=c
    except socket.timeout: pass
    s.close()
    return out.split(b'\r\n',1)[0].decode('latin1','replace')

# 1. chunked PUT -> refused, no file
st=http('PUT','/books/chunk.txt',{'Transfer-Encoding':'chunked'},b'5\r\nhello\r\n0\r\n\r\n')
check('501' in st and not os.path.exists(os.path.join(BOOKS,'chunk.txt')), f"chunked PUT refused ({st}), no file")

# 2. non-numeric Content-Length -> 400, no file
st=http('PUT','/books/bad.txt',{'Content-Length':'0x10'},b'hello')
check('400' in st and not os.path.exists(os.path.join(BOOKS,'bad.txt')), f"bad Content-Length refused ({st})")

# 3. case-only WebDAV MOVE keeps the source's content, no temp leak
open(os.path.join(BOOKS,'Case.txt'),'w').write('case-content\n')
st=http('MOVE','/books/Case.txt',{'Destination':'/books/case.txt'})
lc=[f for f in os.listdir(BOOKS) if f.lower()=='case.txt']
content=open(os.path.join(BOOKS,lc[0])).read().strip() if lc else ''
leftover=[f for f in os.listdir(BOOKS) if 'casemove' in f]
check('201' in st and content=='case-content' and not leftover, f"case MOVE preserved content ({st}), no temp leak")

# 4. a normal WebDAV PUT still works (raw path)
st=http('PUT','/books/ok.txt',{'Content-Length':'7'},b'goodput')
check('201' in st and os.path.exists(os.path.join(BOOKS,'ok.txt')) and open(os.path.join(BOOKS,'ok.txt')).read()=='goodput', f"normal PUT works ({st})")

# 5. path traversal cannot escape the card
canary=os.path.join(WORK,'outside.txt'); open(canary,'w').write('SECRET')
st=http('GET','/books/..%2f..%2f..%2foutside.txt')
check('200' not in st or 'SECRET' not in st, f"traversal GET did not serve outside file ({st})")

# 6. WebSocket START with an absurd size -> refused; a normal one -> READY
def ws_handshake(s):
    key=base64.b64encode(b'0123456789abcdef').decode()
    s.sendall(f'GET / HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n'.encode())
    buf=b''
    s.settimeout(3)
    while b'\r\n\r\n' not in buf:
        c=s.recv(4096)
        if not c: break
        buf+=c

def ws_start(name, size):
    s=socket.create_connection(('127.0.0.1',WS), timeout=6)
    ws_handshake(s)
    pl=f'START:{name}:{size}:/books'.encode()
    s.sendall(bytes([0x81,0x80|len(pl)])+b'\x00\x00\x00\x00'+pl)
    r=b''
    s.settimeout(3)
    try:
        for _ in range(4):
            c=s.recv(4096)
            if not c: break
            r+=c
            if b'READY' in r or b'ERROR' in r or b'DONE' in r: break
    except socket.timeout: pass
    s.close(); return r
check(b'ERROR' in ws_start('evilbig.txt','99999999999999999999999'), "WS START with absurd size refused")
check(b'READY' in ws_start('normal.txt','100'), "WS START with a normal size accepted")

# 7. a WS frame header claiming 256 MB with no payload does not blow RSS
def rss(pid): return int(subprocess.check_output(['ps','-o','rss=','-p',str(pid)]).strip())//1024
simpid=int(os.environ.get('SIM_PID','0')) or None
if simpid:
    before=rss(simpid)
    socks=[]
    for _ in range(3):
        s=socket.create_connection(('127.0.0.1',WS), timeout=6)
        key=base64.b64encode(b'abcdefghijklmnop').decode()
        s.sendall(f'GET / HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n'.encode())
        time.sleep(0.2); s.recv(4096)
        s.sendall(bytes([0x82,0xFF])+struct.pack('>Q',256*1024*1024)+b'\x00\x00\x00\x00')
        socks.append(s)
    time.sleep(1.0); after=rss(simpid)
    for s in socks: s.close()
    check(after-before < 100, f"three 256 MB WS-header frames added {after-before} MB RSS (was ~360)")

sys.exit(1 if fails else 0)
PY
RC=$?
if [ "$RC" -eq 0 ]; then echo "PASS: web server hardening pins hold"; else echo "FAIL: a web server hardening pin regressed"; fi
exit $RC
