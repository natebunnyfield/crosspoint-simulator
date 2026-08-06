# WiFi on iOS — plan

Status: **plan only** apart from Phase 0. Written 2026-08-06 against simulator
`c66d39f` and firmware `4ef1a62`.

## Decisions (owner, 2026-08-06)

| Question | Ruling |
|---|---|
| What is WiFi for? | **Peer transfer first**, then Mac, then internet |
| Why at all, given Files sharing works? | **QA of the CrossPoint fork.** The point is exercising firmware code paths on the phone, not moving files conveniently |
| Screens that can't work — hide or keep? | **X3 parity.** The screens exist and behave like an X3 |
| Distribution | **Personal build.** No App Review |
| Firmware companion work | **Yes**, in scope |
| Real SSID, at the cost of a Location prompt | **Yes** |
| Does peer transfer need the hotspot? | **No — it happens over a regular WiFi network** |

The last two are the ones that decide how much of this is buildable, and the
answer is: nearly all of it.

"QA of the fork" is the load-bearing motive. It makes an *awkward but faithful*
path beat a *convenient but divergent* one, because a divergent path QAs
nothing.

## What the firmware does

Read from the fork, not assumed.

**File Transfer offers two modes** (`NetworkModeSelectionActivity.cpp:21-24`),
both ending in `CrossPointWebServerActivity` serving the web UI:

* **`JOIN_NETWORK`** — `WifiSelectionActivity` scans, the owner picks, the
  device joins, mDNS advertises `crosspoint.local`, the server starts. The peer
  is any machine on the same network. **This is the peer-transfer path**, and
  it is the one that matters.
* **`CREATE_HOTSPOT`** — an open AP named by a compile-time constant
  (`CrossPoint-Reader`, `CrossPointWebServerActivity.cpp:23-26`), a
  `WIFI:T:nopass;S:...` join QR, and a captive-portal DNS. This is the
  *no-network fallback*: what you use in a hotel, not the normal flow.

That split is the whole story for iOS. The normal flow needs an IP address; the
fallback needs an 802.11 radio. iOS gives the first and refuses the second.

## The platform ceiling

| Firmware step | iOS | Why |
|---|---|---|
| Outbound TCP/TLS | **yes** | sockets and `NSURLSession` unrestricted |
| Listening HTTP/WS server | **yes**, foreground only | iOS suspends the app in background and the socket stops accepting |
| Connection state | **yes** | `NWPathMonitor`, no entitlement |
| Own LAN IP | **yes** | `getifaddrs()` on `en0` |
| Current SSID | **yes**, entitled | *Access WiFi Information* + Location. Approved |
| mDNS `crosspoint.local` | **yes** | Bonjour — mandatory, see finding 6 |
| Join a **named** network | yes, entitled | `NEHotspotConfiguration`, device-only. **Not needed** — see Phase 1 |
| **Scan** | **no** | No public API at any tier |
| **Soft AP** | **no** | An app cannot bring up an access point |
| **Captive-portal DNS** | **no** | Port 53 needs root, and nothing routes peers' DNS to the app |
| OTA / SD flash | **no** | No ESP32 to flash, no SD slot. Physical, not policy |

**Peer transfer over a regular network needs nothing from the "no" column.**
Only `CREATE_HOTSPOT` does, and it is the fallback.

### The join path needs no fakery at all

The phone is *already* on a network when the owner opens File Transfer, and
with *Access WiFi Information* the harness knows its real name. So on iOS
`scanNetworks()` returns **1** — the network the phone is genuinely associated
with — and `SSID(0)` is its real SSID.

Every downstream step then works as written: the list renders one true row,
`WifiCredentialStore`'s saved-network auto-connect
(`tryNextSavedNetworkFromScan`) matches it, selecting it "connects" instantly
because the phone already is connected, and `CrossPointWebServerActivity`
proceeds to `startWebServer()`. No new firmware UI, no invented networks, and
no `NEHotspotConfiguration` — **one fewer entitlement than the previous draft
assumed.**

`WIFI_SCAN_FAILED` stays the honest answer for the other case: the phone is on
cellular or offline. `WifiSelectionActivity` already handles it by falling back
to a manual-SSID-entry list (`WifiSelectionActivity.cpp:132-142`), which is the
correct thing to show someone whose phone isn't on WiFi.

## Findings in the simulator tree

1. **The iOS exclusion lists are a silent no-op.** `CMakeLists.txt:176-177`
   calls `list(REMOVE_ITEM ... ${CROSSPOINT_IOS_EXCLUDED_SIM_SOURCES})`, but
   `e75ab8c` put the definitions in the *generated*
   `cmake/CrossPointSources.cmake` and the next regeneration (`af2e842`) wiped
   them — `tools/gen_cmake_sources.py` has no idea they exist. CMake does not
   error on `list(REMOVE_ITEM x ${undefined})`. The log prints
   `stripped 0 simulator + 0 firmware network/OTA TUs`. **Fixed in Phase 0.**

2. **All 18 network TUs are in the iOS source set today.** Only
   `CROSSPOINT_NO_NETWORK=1` keeps them out of the UI. Whether they still
   compile for `arm64-apple-ios` is unverified.

3. **Both shim servers bind `INADDR_LOOPBACK`** (`WebServer.cpp:435`,
   `WebSocketsServer.cpp:349`) — reachable by nothing but the phone itself.

4. **The painted URL hardcodes port 80, in three places.**
   `"http://" + connectedIP + "/"` (line 440), `http://crosspoint.local/`
   (line 415), both QR-encoded. `mapFirmwarePort` moves 80 → 8080 and the
   firmware never learns, so every address on that screen is wrong on a phone.

5. **`WiFi.localIP()` is hardcoded `127.0.0.1`** (`WiFi.h:196`), which feeds
   finding 4.

6. **mDNS is a no-op stub.** `src/ESPmDNS.h` — `begin()` returns true,
   `addService()` does nothing. The firmware advertises and QR-encodes
   `http://crosspoint.local/` as the **primary** address, so on iOS the main
   peer-facing address resolves to nothing. This makes
   `NSLocalNetworkUsageDescription` + `NSBonjourServices` required, not
   optional.

7. **`SimHttpFetch` `popen()`s curl** (`SimHttpFetch.h:208`). No curl binary and
   no fork/exec in the iOS sandbox. Same gap already documented for the
   sandboxed Mac App Store build (`.claude/CONTEXT-sim-notes.md:232`) — one
   `NSURLSession` backend closes both.

8. **The post-transfer reboot never happens.** `CrossPointWebServerActivity`'s
   `onExit()` calls `silentRestart()` (line 114) to clear heap fragmentation,
   which paints a "Loading…" popup and calls `ESP.restart()` — and
   `src/Arduino.h:41` is `void restart() {}`. On hardware that call never
   returns; in the simulator it returns immediately and execution falls through
   with a stale popup on screen. **So the reboot-to-Home that every real file
   transfer ends with is not exercised at all**, on desktop or iOS. For a QA
   vehicle that is the gap that matters most on this screen, and the machinery
   to fix it already exists: `SimulatorLifecycle`'s in-process reboot
   (setjmp/longjmp), built for the iOS deep-sleep wake because iOS reports a
   self-terminating process as a crash.

## The model

Same shape as the button pad, one layer down: the pad impersonates seven GPIO
pins; the WiFi backend impersonates the *result* of an ESP32 radio — an
associated station with an IP — and declines to impersonate what iOS will not
expose. No `#if TARGET_OS_IPHONE` in the firmware. The seams are `WiFiClass`,
`SimHttpFetch`, `ESPmDNS`, `ESP.restart()`, and the servers' bind address.

Where a capability is missing, the firmware learns through a **return value it
already handles** (`WIFI_SCAN_FAILED`, `softAP() == false`) rather than a new
iOS-shaped branch. That is what makes parity and honesty compatible.

## Phases

### Phase 0 — restore the switch ✅ done

* Both exclusion lists moved to `cmake/CrossPointIOSExclusions.cmake`, not
  generated, `include()`d from the root `CMakeLists.txt`.
* Configure-time `FATAL_ERROR` if either list is empty when `IOS`, naming this
  regression so the next person reads the story rather than rediscovering it.
* `gen_cmake_sources.py` cross-checks the exclusions against the freshly
  generated source set and warns on any that no longer exist, without owning
  them.

### Phase 1 — the radio tells the truth (simulator)

`WiFi.h` keeps its public surface; the body moves behind a dispatcher, the
pattern `MD5Builder.h` already uses. iOS backend in `WiFiBackend_ios.mm`:

| Call | iOS |
|---|---|
| `status()` | `NWPathMonitor` — satisfied → `WL_CONNECTED` |
| `localIP()` | `getifaddrs()`, first IPv4 on `en0` |
| `SSID()` / `SSID(0)` | `NEHotspotNetwork.fetchCurrent` (entitled) |
| `scanNetworks()` / `scanComplete()` | **1** on WiFi — the real current network; `WIFI_SCAN_FAILED` on cellular or offline |
| `RSSI()` / `RSSI(0)` | **real**, from the same `fetchCurrent` — see below |
| `begin(ssid, pass)` | already associated → return `status()` |
| `softAP()` | `false` |

Desktop keeps the `CROSSPOINT_SIM_WIFI_*` env fakes untouched — they are the QA
harness for the firmware's failure branches, and this plan leans on those
branches more, not less.

**Signal strength passes through.** `NEHotspotNetwork` carries `signalStrength`
next to the SSID, so the `fetchCurrent` call this phase already makes returns
both. Two things it needs on the way to `RSSI()`:

* **Units.** `signalStrength` is normalised 0.0–1.0; the firmware wants dBm and
  `barsForRssi` bands it at −85/−75/−65/−55 rising and −88/−78/−68/−58 falling
  (`CrossPointWebServerActivity.cpp:61-68`). Map linearly onto roughly −100…−40
  so all four bars and the hysteresis are reachable. The absolute dBm is
  synthesised, but it is a monotone function of a real measurement, so the bars
  move when and only when the signal does — which is the whole of what the UI
  claims.
* **Async.** `fetchCurrent` has a completion handler and `RSSI()` is
  synchronous, so cache the last value and refresh it on `NWPathMonitor`
  updates plus a slow timer. The web server activity polls RSSI in its loop
  (line 293), so a value a second or two old is fine.

**Verify granularity on device** before trusting the hysteresis: the property
is documented as a 0–1 scale but iOS is not obliged to report it finely, and if
it turns out to be coarse or pinned the bars will step rather than glide.
`fetchCurrent` also returns nil on the iOS Simulator, so this is a device-only
behaviour and Simulator runs keep the env fakes.

### Phase 2 — make the server reachable (simulator + firmware)

This is the phase that delivers peer transfer.

* `CROSSPOINT_SIM_BIND_ALL`, default **on for iOS, off for desktop**, in
  `WebServer.cpp` and `WebSocketsServer.cpp`. Dev machines keep loopback.
* **Real mDNS**, Bonjour-backed, replacing the `ESPmDNS.h` stub on Apple
  platforms — without it the primary advertised address is a dead link.
* **Teach the firmware the mapped port** so the URL and both QR codes say
  `:8080`: read `crosspoint_simulator::httpPort()` under `#ifdef SIMULATOR` at
  the three sites in `CrossPointWebServerActivity.cpp`.
* **Route `ESP.restart()` into `SimulatorLifecycle`** so the post-transfer
  reboot actually happens (finding 8). Fixes desktop too.
* `isIdleTimerDisabled` while the server runs — a transfer that dies to a
  screen lock will read as a firmware bug during QA, which is exactly the
  failure this exercise exists to avoid.

### Phase 3 — in-process HTTP (simulator; also unbreaks Mac App Store)

* Split `SimHttpFetch.h` into dispatcher + backends, as `MD5Builder.h` does.
  Mock-root and `file://` paths stay shared — platform-independent and useful
  for scripted QA on iOS.
* `SimHttpFetch_apple.mm`: `NSURLSession` + `dispatch_semaphore` to preserve the
  synchronous `fetch()` the call sites in `HTTPClient.h` and `esp_http_client.h`
  expect. **Never from the SDL main thread.**
* Map `NSError` domains onto the existing `curlExitCodeToHttpError` codes so
  firmware error handling is untouched.
* Personal build, so ATS is a free choice: `NSAllowsLocalNetworking` for the
  local server; take a wider exception only when a real QA target demands it.

### Phase 4 — re-enable the screens (firmware)

Split the blunt gate into three:

| Gate | Covers | iOS |
|---|---|---|
| `CROSSPOINT_NO_SOFTAP` | the `CREATE_HOTSPOT` row in `NetworkModeSelectionActivity` | **on** |
| `CROSSPOINT_NO_OTA` | `OtaUpdateActivity`, `SdFirmwareUpdateActivity`, `OtaUpdater`, `FirmwareFlasher`, `simulator_ota.cpp` | **on**, permanently |
| *(none)* | web server, WebDAV, downloads, QR, diagnostics, `WifiSelectionActivity`, `WifiCredentialStore` | **off** — these ship |

`MENU_ENTRIES` is already table-driven, so dropping the hotspot row is a
one-entry `#ifdef`, not a rewrite. With one row left, consider whether the mode
screen should be skipped entirely on iOS — that is a parity judgement for the
owner, not a technical one.

### Phase 5 — the hotspot fallback, as far as it goes

Only for the no-network case, since peer transfer proper is Phase 2:

* **Personal Hotspot.** The owner turns it on in Settings, the peer joins, the
  phone serves on the hotspot address. Topologically identical to the X3's AP
  mode; the "device raises the AP" step is manual and there is no captive
  portal.
* **Phone joins a real X3's AP.** `NEHotspotConfiguration(ssid:
   "CrossPoint-Reader")` — open network, constant name, no scan needed. This
  makes the phone a *client* of a real X3's web UI, the reverse of what the
  firmware does, and would be new UI. **Out of scope**; recorded because it is
  the one peer-to-peer path iOS is genuinely good at.

## Entitlements and Info.plist

Personal build, all self-serve:

* `com.apple.developer.networking.wifi-info` (*Access WiFi Information*) +
  `NSLocationWhenInUseUsageDescription` — the real SSID, which is what lets the
  join path avoid fakery.
* `NSLocalNetworkUsageDescription` + `NSBonjourServices` (`_http._tcp`) —
  **required** once Phase 2 makes mDNS real.
* `NSAppTransportSecurity` → `NSAllowsLocalNetworking`.
* `ITSAppUsesNonExemptEncryption` stays `false`.
* *Hotspot Configuration* is **not** needed. It would only be for Phase 5's
  out-of-scope option.

## What stays off, permanently

* **OTA and SD firmware flash.** No ESP32 to flash, no SD slot. A personal
  build does not change this — it was never only a policy problem.
* **Soft AP and captive portal.** No API, and none is coming.

## Verification

Desktop first, every phase — it is the canary.

```bash
cd $HOME/src/crosspoint-reader && pio run -e simulator
CROSSPOINT_SIM_WIFI_CONNECT=fail .pio/build/simulator/program
```

iOS, in order of what each proves:

* Configure log shows a **non-zero** strip count (Phase 0).
* Settings → File Transfer → Join Network shows a one-row list naming the
  network the phone is actually on.
* The server screen paints an address with the right port, and both QR codes
  scan to something that resolves.
* From a Mac on the same WiFi: browser fetch, `crosspoint.local:8080`
  resolution, WebDAV mount, a font download that completes. **This is peer
  transfer; if it works, the primary use case is done.**
* Backing out of File Transfer reboots to Home rather than falling through with
  a stale popup (finding 8).
* Signal bars track reality: walk away from the router and watch them fall,
  which is also the check for whether `signalStrength` is finely enough
  quantised to be worth the mapping.
* Same flows with the app backgrounded mid-transfer — expect failure, confirm
  it fails *cleanly* rather than wedging the firmware.
* Personal Hotspot path (Phase 5).

## Open

* **The one-row mode screen.** With `CREATE_HOTSPOT` gone, `Join Network` is
  the only choice on that screen. Parity says keep it; usability says skip
  straight to the server. Owner's call at Phase 4, and the only design question
  left in this plan.

## Known limits, not open questions

* **Peer-transfer QA needs a second machine**, so it cannot fold into a scripted
  `CROSSPOINT_SIM_INPUT_SCRIPT` run. Everything up to "the server is listening"
  can be scripted; the transfer itself stays hand-tested.
* **Three behaviours are device-only** and cannot be QA'd on the iOS Simulator:
  the real SSID, signal strength, and anything depending on a genuine `en0`
  address. There is still no paired device (`README.md`, "Still deferred"),
  which is now the binding constraint on verifying Phases 1 and 2 rather than a
  background note.
* **The app must stay foregrounded** for the whole of a transfer. iOS suspends
  background apps and the listening socket stops accepting.
