# WiFi on iOS — plan

Status: **plan only**, nothing here is implemented. Written 2026-08-06 against
`c66d39f`.

The one-line version: an iPhone cannot impersonate the X3's *radio*, but it can
impersonate everything the radio is **for**. The firmware's WiFi features split
cleanly into "needs an 802.11 chip we control" (impossible) and "needs an IP
address" (already works, and is switched off by accident today).

## The platform ceiling

Decide this before writing code, because it determines which firmware screens
can exist on the phone at all.

| Firmware capability | iOS | Why |
|---|---|---|
| Outbound TCP/TLS (`NetworkClient`, downloads) | **yes** | BSD sockets and `NSURLSession` are unrestricted |
| Listening HTTP/WebSocket server on the LAN | **yes**, foreground only | `bind`/`listen` work; iOS suspends the app in background, so the socket stops accepting |
| Report "am I connected, and on what" | **yes** | `NWPathMonitor`, no entitlement |
| Report own LAN IP | **yes** | `getifaddrs()` on `en0`, no entitlement |
| Report current SSID | **entitlement** | `NEHotspotNetwork.fetchCurrent` needs *Access WiFi Information* **and** Location permission. A reader app asking for location will be questioned at review. Recommend: don't. |
| **Scan for networks** | **no** | No public API at any entitlement tier. `NEHotspotHelper` is MDM/carrier-only. |
| **Join a network programmatically** | partial | `NEHotspotConfiguration` can join an SSID *you already know the name of*, with the *Hotspot Configuration* entitlement, device-only. Cannot enumerate, so it cannot back a picker. |
| **Soft AP** | **no** | An app cannot bring up an access point. Personal Hotspot is user-driven from Settings only. |
| OTA firmware flash | **no**, permanently | App Store guideline 2.5.2 forbids downloading and executing code |

So: **`WifiSelectionActivity`'s scan-and-pick model has no iOS implementation and
never will.** Everything else does.

## What is actually true in the tree today

Five findings, all verifiable from this checkout:

1. **The iOS exclusions were silently lost.** The root `CMakeLists.txt:176-177`
   calls `list(REMOVE_ITEM ... ${CROSSPOINT_IOS_EXCLUDED_SIM_SOURCES})`, but
   nothing defines that variable any more. It was added in `e75ab8c` to the
   *generated* `cmake/CrossPointSources.cmake`, and the next regeneration
   (`af2e842`, then `5c2e067`) wiped it — `tools/gen_cmake_sources.py` has no
   idea the lists exist. CMake does not error on `list(REMOVE_ITEM x ${undefined})`;
   it is a no-op. The configure line prints
   `stripped 0 simulator + 0 firmware network/OTA TUs` and the build carries the
   entire network stack.

   Consequence: **hand-curated policy is living in a generated file.** Fix that
   first, in `cmake/CrossPointIOSExclusions.cmake` (not generated), plus a
   configure-time assert so an empty list is loud rather than silent.

2. **All 18 network TUs are in the iOS source set right now** — 6 simulator
   (`NetworkClient`, `WebServer`, `WebSocketsServer`, `CrossPointWebServer`,
   `qrcode`, `simulator_ota`) and 12 firmware (`src/network/*`,
   `src/activities/network/*`, `WifiCredentialStore`, `FontDownloadActivity`,
   `OtaUpdateActivity`, `SdFirmwareUpdateActivity`, `QrUtils`). Only
   `CROSSPOINT_NO_NETWORK=1` (`ios/CMakeLists.txt:172`) keeps them out of the
   UI, via `#ifdef`s on the firmware side. Whether they still *compile* for
   `arm64-apple-ios` is unverified — they have not been exercised since the
   exclusions were meant to remove them.

3. **The servers bind loopback.** `WebServer.cpp:435` and
   `WebSocketsServer.cpp:349` both use `htonl(INADDR_LOOPBACK)`. On a phone that
   makes the file-transfer server reachable by nothing at all. Desktop wants to
   keep loopback (binding `0.0.0.0` on a dev machine exposes it to the office);
   this has to be a deliberate switch, not a blanket change.

4. **`WiFi.localIP()` is hardcoded `127.0.0.1`** (`WiFi.h:196`) and
   `scanNetworks()` returns two invented SSIDs. The firmware paints that address
   on the file-transfer screen and into the QR code, so on a phone it would
   print an address that is correct for nobody. Note also that
   `mapFirmwarePort` moves 80 → 8080, but the *displayed* URL comes from the
   firmware and does not know that — on desktop the user compensates; on a
   phone a wrong URL makes the feature useless.

5. **`SimHttpFetch` shells out to `curl`** (`SimHttpFetch.h:208`, `popen`).
   There is no `curl` binary on iOS and no `fork`/`exec` in the sandbox, so
   every download path — fonts, catalogs, sync — is dead on arrival. This is the
   same gap already documented for the sandboxed Mac App Store build in
   `.claude/CONTEXT-sim-notes.md:232`. **One `NSURLSession` backend closes both.**

## The model

Same shape as the button pad, one layer down. The pad impersonates seven GPIO
pins; here the harness impersonates the *result* of an ESP32 radio — an
associated station with an IP — and refuses to impersonate the parts of the
radio iOS will not expose. No `#if TARGET_OS_IPHONE` in the firmware.

| Layer | Sees | Change |
|---|---|---|
| Harness (`ios/`) | `NWPathMonitor`, `getifaddrs`, `NSURLSession` | new |
| Device (`WiFiClass`, `SimHttpFetch`) | "connected, here is my IP", "here is your HTTP response" | backend swap |
| Firmware | a station-mode WiFi that is already associated | gating only |

The honest posture for the un-impersonable parts is **absent, not faked**:
`scanNetworks()` returns 0 and `softAP()` returns false on iOS rather than
inventing networks, and the firmware screens that depend on them are compiled
out. A fake scan list that cannot be joined is worse than no scan screen.

## Phases

Each phase is independently shippable and leaves the desktop build green.

### Phase 0 — restore the switch (this repo, no behaviour change)

* Move the two exclusion lists out of the generated file into
  `cmake/CrossPointIOSExclusions.cmake`; `include()` it from the root
  `CMakeLists.txt`.
* Assert at configure time that both lists are non-empty when `IOS`, so the
  next regeneration cannot silently disarm them again.
* Have `tools/gen_cmake_sources.py` *validate* the exclusion paths against the
  freshly generated source set (an excluded TU that no longer exists is drift
  too) without owning them.
* Confirm the reported strip count is non-zero in the configure log.

Ends with the iOS build in the state the commit message claimed it was in.

### Phase 1 — tell the truth about the connection (this repo)

* `WiFiClass` grows an iOS backend. Follow the `MD5Builder.h` dispatcher
  pattern already in the tree: `WiFi.h` keeps the public surface, the body
  moves behind `WiFiBackend_sim.h` / `WiFiBackend_ios.mm`.
  * `status()` ← `NWPathMonitor`: `.satisfied` + `usesInterfaceType(.wifi)` →
    `WL_CONNECTED`; satisfied on cellular → also connected (the firmware only
    cares that IP works); unsatisfied → `WL_DISCONNECTED`.
  * `localIP()` ← `getifaddrs()`, first IPv4 on `en0`.
  * `SSID()` → a non-lying placeholder (`"iPhone network"`), *not* an
    entitlement request. Revisit only if the owner wants the real name enough
    to accept a Location prompt.
  * `scanNetworks()` → 0, `softAP()` → false, `begin()` → current status.
    The radio is not ours to command.
* Keep the env-var fakes (`CROSSPOINT_SIM_WIFI_*`) on the desktop path
  untouched — they are the QA harness for the firmware's failure branches.

### Phase 2 — make the server reachable (this repo)

* Bind `INADDR_ANY` under an explicit opt-in — `CROSSPOINT_SIM_BIND_ALL`,
  defaulted **on for iOS, off for desktop**, in both `WebServer.cpp` and
  `WebSocketsServer.cpp`. Desktop dev machines keep loopback.
* Surface the mapped port to the firmware so the painted URL and the QR code
  say `http://192.168.x.x:8080/` and not `http://192.168.x.x/`. Cheapest honest
  route: a `crosspoint_simulator::httpPort()` accessor the firmware's
  `CrossPointWebServerActivity` reads under `#ifdef SIMULATOR` (firmware
  companion change).
* Keep `UIApplication.isIdleTimerDisabled` set while the server is running —
  a transfer that dies because the screen locked will read as a bug.
* Verify from a Mac: browser to the address, and Finder → *Connect to Server*
  for the WebDAV route.
* Document the Personal Hotspot workaround as the AP-mode analogue: the owner
  turns Personal Hotspot on in Settings, the Mac joins it, the server answers
  on the hotspot address. Zero code, and it reproduces the X3's AP workflow.

### Phase 3 — in-process HTTP client (this repo; also fixes Mac App Store)

* Split `SimHttpFetch.h` into a dispatcher plus backends, exactly as
  `MD5Builder.h` does. The mock-root and `file://` paths stay shared — they are
  platform-independent and useful on iOS for QA.
* `SimHttpFetch_apple.mm`: `NSURLSession`, `dispatch_semaphore` to keep the
  synchronous `fetch()` signature the call sites in `HTTPClient.h` and
  `esp_http_client.h` expect. **Never call it from the SDL main thread** —
  firmware download paths run on task threads, and that has to stay true.
* Map `NSError` domains onto the `curlExitCodeToHttpError` codes the firmware
  already branches on, so error handling does not need to change.
* ATS: remote fetches must be HTTPS. Add `NSAllowsLocalNetworking` for the
  local-server case rather than `NSAllowsArbitraryLoads`, which draws review
  questions. A plain-HTTP OPDS catalog will fail, by design — flag it in the
  UI rather than weakening ATS.
* Use the Linux/desktop `curl` backend as the reference for behaviour parity;
  the two must agree on redirects, timeouts, and basic auth.

### Phase 4 — re-enable the screens (firmware repo, companion PR)

`CROSSPOINT_NO_NETWORK` is currently one blunt switch over three unrelated
concerns. Split it:

| New gate | Covers | iOS |
|---|---|---|
| `CROSSPOINT_NO_WIFI_RADIO` | scan, join, soft-AP: `WifiSelectionActivity`, `NetworkModeSelectionActivity`, `WifiCredentialStore` | **on** (compiled out) |
| `CROSSPOINT_NO_OTA` | `OtaUpdateActivity`, `SdFirmwareUpdateActivity`, `simulator_ota.cpp` | **on**, permanently |
| *(nothing)* | web server, WebDAV, downloads, QR, diagnostics | **off** — these ship |

Then the iOS exclusion list shrinks to the OTA/radio TUs, and
`CrossPointWebServerActivity`, `HttpDownloader`, `WebDAVHandler`,
`WifiDiagnostics`, `FontDownloadActivity`, `QrUtils` and `qrcode.cpp` come back.

Network mode selection needs a third state for "the network is not mine to
choose" — the phone is already on a network, so the activity either skips
straight to the server screen or reports `WL_DISCONNECTED` with "connect this
iPhone to WiFi in Settings".

## What stays off, permanently

* **OTA and SD firmware flash.** Guideline 2.5.2, and there is no SD slot.
  Do not revisit.
* **The scan-and-join picker.** No API. If a future owner wants typed-SSID
  joining, that is `NEHotspotConfiguration` + an entitlement + a text-entry
  screen — a different feature from the one the firmware has, and it should be
  proposed as such, not smuggled in as "fixing" the picker.

## Entitlements and Info.plist

Phases 1–3 as scoped need **no new entitlements**. What may be needed:

* `NSLocalNetworkUsageDescription` — required for *outgoing* local-network
  connections and Bonjour. A pure listening server should not trigger it, but
  this must be **verified on a physical device**, not assumed; the iOS local
  network prompt has moved between releases. If `ESPmDNS` ever stops being a
  no-op stub (`src/ESPmDNS.h`), this plus `NSBonjourServices` becomes mandatory.
* `NSAppTransportSecurity` → `NSAllowsLocalNetworking` only.
* `ITSAppUsesNonExemptEncryption` stays `false`: HTTPS via the OS is exempt.

## Verification

Desktop first, every phase — it is the canary (`CLAUDE.md`).

```bash
cd $HOME/src/crosspoint-reader && pio run -e simulator     # must stay green
CROSSPOINT_SIM_WIFI_CONNECT=fail .pio/build/simulator/program   # failure branches
```

iOS:

* Configure log shows a **non-zero** strip count (Phase 0).
* Simulator: file-transfer screen paints the Mac-reachable address and port.
* Device, same WiFi as a Mac: browser fetch, WebDAV mount, a font download that
  completes, and the same three with the app backgrounded mid-transfer (expect
  failure — confirm it fails *cleanly*).
* Personal Hotspot path, as the AP-mode substitute.

## Open questions for the owner

1. Is the real SSID worth a Location permission prompt? Recommendation: **no**.
2. Should the phone's server be reachable at all, or is Files/iTunes sharing
   (`UIFileSharingEnabled`, already on) enough? Phases 2 and 4 only pay off if
   the answer is "reachable".
3. Font downloads on iOS overlap with `CROSSPOINT_IOS_SEED_FONTS_DIR`, which
   already ships families in the bundle. If seeding is the answer, Phase 3
   drops to "unbreak the Mac App Store build" and stops being iOS work.
