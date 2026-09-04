# Network-surface hunt — the web server the phone publishes, 2026-09-04

Read-only probing pass (one agent, probes under a scratch card, the
`simulator_x3` binary at firmware `7cabffea0` / simulator `8b45288`) over the
host web-server shims — `src/WebServer.cpp`, `src/WebSocketsServer.cpp`,
`src/NetworkClient.cpp`, `src/HalStorage.cpp` — and the firmware handlers they
serve (`crosspoint-reader/src/network/CrossPointWebServer.cpp`,
`WebDAVHandler.cpp`). The iOS app binds both servers on ALL interfaces
(`CLAUDE.md`), so a crafted request from the phone's Wi-Fi must not crash the
app, write outside the card, or read outside it. Eleven findings; six fixed
in this repo the same day, one in the firmware, four recorded.

## Findings

| # | What | Where | Severity | Status |
|---|---|---|---|---|
| 1 | **A dripping client froze the firmware's main thread on Back** — `stop()` shut down only the LISTENING fd and then `join()`ed a worker parked in the body loop, which `recv` keeps alive as long as bytes arrive. Measured: 1 byte / 2 s PUT, Back at 32 s, `Entering activity: Home` at 69.8 s — 37.7 s frozen, bounded only by the 256 MB body cap. The same `stop()` runs from the S-013 reboot registrar, so a peer could hold the post-transfer reboot too. | `src/WebServer.cpp` `stop()` | would-ship (remote UI hang) | **FIXED** — the worker publishes the fd it is serving (`activeClient`), `stop()` shuts that down too. Re-measured, see below. |
| 2 | **Fourteen bytes of WebSocket header forced a 256 MB zero-filled allocation per connection** — `payload.assign(len, 0)` before a payload byte was read. Measured RSS 15 → 271 MB from one peer, 383 MB from four; on a phone that is a jetsam kill. | `src/WebSocketsServer.cpp` frame reader | would-ship (crash-class on iOS) | **FIXED** — the payload grows as bytes ARRIVE, 64 KB at a time; a peer has to send what it claims. Re-measured: three such frames, RSS 23 → 22 MB. |
| 3 | **A case-only WebDAV MOVE deleted the source** on a case-insensitive filesystem — `Case.txt → case.txt` saw the destination "exist" (it IS the source), removed it under the overwrite rule, then failed to open the source: `500`, file gone. Reproduced on APFS (the packaged Mac apps); the card's FAT is case-insensitive too (inferred). | firmware `WebDAVHandler.cpp` `handleMove` | would-ship (data loss) | **FIXED in the firmware** (`strcasecmp` equal → rename through a temporary name, never an overwrite). Re-probed: `201`, content preserved. |
| 4 | **Chunked or unparsable Content-Length PUTs created an empty file and answered 201** — `strtoull` gave 0 for `abc` / `0x10`, and `Transfer-Encoding: chunked` was never read. | `src/WebServer.cpp` header parse | silent-wrong-output | **FIXED** — chunked → `501`, a non-numeric length → `400`, nothing written. Re-probed. |
| 5 | **A multipart POST with no parseable part reported the PREVIOUS upload's success** — the route handler ran with zero parts and read an `UploadState` nothing had reset. | `src/WebServer.cpp` dispatch | silent-wrong-output | **FIXED** — zero parts → `400`, the handler does not run. |
| 6 | **Multipart `size_t` underflow when a boundary immediately follows the part headers** — `dataEnd -= 2` below `dataStart`, `substr` took the rest of the body (second part's headers landed in the first part's file). | `src/WebServer.cpp` `parseMultipart` | silent-wrong-output (malformed input) | **FIXED** — the CRLF is trimmed only when there is room for it. |
| 7 | A PUT body is held in three copies although the raw handler already streamed it to disk (100 MB PUT → 235 MB RSS peak; the cap implies ~600 MB). | `src/WebServer.cpp` `body` / `String(body)` / `currentBody` | latent (a large legitimate upload on a low-RAM phone) | recorded, S-036 |
| 8 | One accept worker, serialized, 5 s socket timeouts: one idle connection delays the next client 4.7 s; 30 idle connections → the 31st times out at 64 s. Recovers when the peer stops. | `src/WebServer.cpp` worker | latent DoS | recorded, S-036 |
| 9 | `%00` truncated the path and the request ran on the shorter one (no escape — every traversal form was refused downstream). | `src/WebServer.cpp` | cosmetic | **FIXED** — a NUL in the decoded path is `400`. |
| 10 | WS `START` with an absurd size is accepted (`toInt()` saturates), the upload can never complete, writes until disconnect; the partial is removed on disconnect. | firmware `CrossPointWebServer.cpp` | latent | recorded, firmware B-044 |
| 11 | `dispatchAbandoned`/`dispatchPending` are never cleared, so a `WebServer` `begin()`-ed again after `stop()` would lose every response — unreachable, `CrossPointWebServer::begin` constructs a fresh object. One `std::thread` handle per WS connection kept until `close()`. | `src/WebServer.cpp`, `src/WebSocketsServer.cpp` | cosmetic | recorded here |

## CLEAN — checked and found solid, with what was tried

- **Path traversal, every form**: `..`, `%2e%2e`, double-encoded `%252e`,
  `..%2f`, backslashes, `//etc`, absolute paths, NUL, via GET / PUT / MKCOL /
  MOVE / COPY / DELETE, `/download`, `/api/files`, `/mkdir`, `/rename`,
  `/move`, `/delete`, a multipart `filename=`, a WS `START` — 39 requests,
  nothing landed outside `fs_`. `FsHelpers::normalisePath` clamps `..` at the
  root; `HalStorage::containsUnsafeSegment` refused the ten that reached it;
  backslash names are literal files.
- **Content-Length** `-1`, `2^64-1`, `2^64+5`, 300 MB → `413`; a length
  larger than the body, and a duplicate header → `400` after the 5 s timeout.
- **Request framing**: no final CRLF, cut mid-header, LF-only → closed after
  5 s, no response; a 1 MB request line or 1 MB of headers → reset at the
  1 MiB cap; a header without `:` ignored; 60 KB header value fine; bare and
  trailing `%` → the decoder's bound holds; odd query shapes fine.
- **`std::stoi` / `substr` class**: no `stoi`/`stol` on any served path;
  the sim `String` accessors are bounds-safe. cppcheck's
  `src/CrossPointWebServer.cpp:412` is guarded AND not compiled (the firmware
  sets `-DCROSSPOINT_SIMULATOR_PROJECT_WEBSERVER`, which `#ifndef`s the
  legacy substitute out).
- **WebSocket**: a 2^63 length → reset; truncated 126-length → clean close;
  unmasked frames accepted; NUL in START → refused; fragmented START →
  continuation dropped; a 200-byte ping and reserved opcode 0xB → ignored;
  overflow BIN → `Upload overflow`; a second client mid-upload → refused;
  `+` size, a 3000-char name, an empty name → refused.
- **Concurrency**: disconnect mid-response on a 20 MB DAV GET and on
  `/download` → the next request answered in 0.00 s; `raw()` runs on the
  worker but is ordered before `handle()` by the park mutex; per-request
  state is single-use because the worker is parked during dispatch;
  `client()` dups the fd — no use-after-free found.
- **Upload paths**: PUT to a directory / under a file / to `/` → `500`,
  target intact; MKCOL with a body → `415`, over a file or the root → `405`,
  missing parent → `409`; MOVE onto a non-empty dir → `500`, both intact;
  MOVE dir over file → `204` (RFC 4918 Overwrite:T); COPY dir → `403`;
  DELETE `/` refused; `:*<>|` names created literally. Disk-full not probed.

## Re-measurements after the fixes (same probes, rebuilt binary)

| probe | before | after |
|---|---|---|
| chunked PUT | `201`, 0-byte file | `501`, no file |
| `Content-Length: 0x10` PUT | `201`, 0-byte file | `400`, no file |
| MOVE `Case.txt → case.txt` | `500`, source gone | `201`, content intact |
| 3 × WS header claiming 256 MB, no payload | 383 MB RSS (4 conns) | 22 MB |
| drip PUT (1 byte / 2 s), Back at 32.0 s | `Entering activity: Home` 37.7 s later | `Incomplete request body: 9/1000` at 32.202 s, Home at 32.215 s — **38 ms** |
