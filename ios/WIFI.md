# WiFi on iOS — plan

Status: **plan only**, nothing here is implemented. Written 2026-08-06 against
simulator `c66d39f` and firmware `4ef1a62`.

## Decisions (owner, 2026-08-06)

These were open questions in the first draft; they are settled and the plan is
shaped around them, not around the general case.

| Question | Ruling |
|---|---|
| What is WiFi for? | **Peer transfer first**, then Mac, then internet |
| Why at all, given Files sharing works? | **QA of the CrossPoint fork.** The point is exercising firmware code paths on the phone, not moving files conveniently |
| Screens that can't work — hide or keep? | **X3 parity.** The screens exist and behave like an X3 |
| Distribution | **Personal build.** No App Review, so ATS exceptions and self-serve entitlements are available |
| Firmware companion work | **Yes**, in scope |
| Real SSID, at the cost of a Location prompt | **Yes** |

"QA of the fork" is the load-bearing one. It inverts the usual trade: a path
that is *awkward but faithful* beats one that is *convenient but divergent*,
because a divergent path QAs nothing.

## What the firmware actually does

Read from the fork, not assumed. This is the part the first draft got only
half right.

**File Transfer offers two modes** (`NetworkModeSelectionActivity.cpp:21-24`):
`JOIN_NETWORK` and `CREATE_HOTSPOT`. Both end in `CrossPointWebServerActivity`
serving the web UI.

**`CREATE_HOTSPOT` is the peer-transfer flow**, and it is worth being precise
about because it is the primary use case and the hardest one:

* `WiFi.softAP("CrossPoint-Reader", nullptr, ...)` — an **open** AP, SSID and
  password are compile-time constants (`CrossPointWebServerActivity.cpp:23-26`).
* The screen paints a **WiFi-join QR**, `WIFI:T:nopass;S:CrossPoint-Reader;;`
  (line 400). The peer scans it with a phone camera and joins.
* A `DNSServer` runs a **captive portal** so any URL redirects to the device.
* mDNS advertises `crosspoint.local`, and a second QR encodes
  `http://crosspoint.local/` (lines 415-420).

So peer transfer is: *device becomes an AP, peer joins it by scanning a QR,
captive portal lands the peer on the web UI.*

## The platform ceiling, against that flow

| Firmware step | iOS | Why |
|---|---|---|
| Outbound TCP/TLS | **yes** | sockets and `NSURLSession` unrestricted |
| Listening HTTP/WS server | **yes**, foreground only | iOS suspends the app in background and the socket stops accepting |
| Report connection state | **yes** | `NWPathMonitor`, no entitlement |
| Report own LAN IP | **yes** | `getifaddrs()` on `en0` |
| Report current SSID | **yes**, entitled | *Access WiFi Information* + Location. Approved above |
| mDNS `crosspoint.local` | **yes** | Bonjour, `NSBonjourServices` — see below, this is mandatory now |
| Join a **named** network | **yes**, entitled | `NEHotspotConfiguration`, device-only. Needs no scan, and the X3's AP name is a constant |
| **Scan** | **no** | No public API at any tier. `NEHotspotHelper` is MDM/carrier-only |
| **Soft AP** | **no** | An app cannot bring up an access point |
| **Captive-portal DNS** | **no** | Port 53 needs root, and nothing would route peers' DNS to the app anyway |
| OTA / SD flash | **no** | No ESP32 to flash, no SD slot. Physical, not policy — a personal build does not unlock these |

**The peer-transfer flow's two hardest steps are the two iOS refuses.** That is
the headline. Everything downstream of "the peer is on the same network as the
app" works; the AP and the captive portal do not.

### The one genuinely good break

`WifiSelectionActivity` **already has the UI iOS needs.** On
`WIFI_SCAN_FAILED` it clears the list, calls `appendHiddenNetworkEntry()`, and
shows a network list whose only row is manual-SSID entry
(`WifiSelectionActivity.cpp:132-142`). That is precisely the shape
`NEHotspotConfiguration` wants: no enumeration, a typed name, a join.

So **X3 parity on the join path needs zero new firmware UI.** `scanNetworks()`
returns `WIFI_SCAN_FAILED` on iOS, the existing failure branch renders, the
owner types an SSID, and the harness joins it. The screen is real, the flow is
real, and nothing is faked.

## Findings in the simulator tree

1. **The iOS exclusion lists are a silent no-op.** `CMakeLists.txt:176-177`
   calls `list(REMOVE_ITEM ... ${CROSSPOINT_IOS_EXCLUDED_SIM_SOURCES})`, but
   `e75ab8c` put the definitions in the *generated*
   `cmake/CrossPointSources.cmake` and the next regeneration (`af2e842`) wiped
   them — `tools/gen_cmake_sources.py` has no idea they exist. CMake does not
   error on `list(REMOVE_ITEM x ${undefined})`. The configure line prints
   `stripped 0 simulator + 0 firmware network/OTA TUs`. Hand-curated policy
   living in a generated file.

2. **All 18 network TUs are in the iOS source set today.** Only
   `CROSSPOINT_NO_NETWORK=1` (`ios/CMakeLists.txt:172`) keeps them out of the
   UI. Whether they still compile for `arm64-apple-ios` is unverified.

3. **Both shim servers bind `INADDR_LOOPBACK`** (`WebServer.cpp:435`,
   `WebSocketsServer.cpp:349`) — reachable by nothing but the phone itself.

4. **The painted URL hardcodes port 80, in three places.**
   `"http://" + connectedIP + "/"` (line 440), `http://crosspoint.local/`
   (line 415), and both are QR-encoded. `mapFirmwarePort` moves 80 → 8080 in
   the simulator and the firmware never learns. On desktop the developer
   compensates; on a phone every address and both QR codes are wrong.

5. **`WiFi.localIP()` is hardcoded `127.0.0.1`** (`WiFi.h:196`), which is what
   feeds finding 4.

6. **mDNS is a no-op stub.** `src/ESPmDNS.h` — `begin()` returns true,
   `addService()` does nothing. The firmware paints and QR-encodes
   `http://crosspoint.local/` as the *primary* address, so on iOS the main
   advertised URL resolves to nothing at all. This upgrades
   `NSLocalNetworkUsageDescription` + `NSBonjourServices` from "verify whether
   it's needed" to **required**.

7. **`SimHttpFetch` `popen()`s curl** (`SimHttpFetch.h:208`). No curl binary
   and no fork/exec in the iOS sandbox. Same gap already documented for the
   sandboxed Mac App Store build (`.claude/CONTEXT-sim-notes.md:232`) — one
   `NSURLSession` backend closes both.

## The model

Same shape as the button pad, one layer down: the pad impersonates seven GPIO
pins, the WiFi backend impersonates the *result* of an ESP32 radio — an
associated station with an IP — and declines to impersonate what iOS will not
expose. No `#if TARGET_OS_IPHONE` in the firmware; the seams are `WiFiClass`,
`SimHttpFetch`, `ESPmDNS`, and the two servers' bind address.

Where a capability is missing, the firmware learns through a **return value it
already handles** (`WIFI_SCAN_FAILED`, `softAP() == false`) rather than through
a new iOS-shaped branch. That is what makes X3 parity and honesty compatible.

## Phases

### Phase 0 — restore the switch (simulator, no behaviour change)

* Move both exclusion lists into `cmake/CrossPointIOSExclusions.cmake`, not
  generated, `include()`d from the root `CMakeLists.txt`.
* Configure-time assert that they are non-empty when `IOS`, so a regeneration
  cannot silently disarm them again.
* `gen_cmake_sources.py` *validates* the excluded paths against the fresh
  source set without owning them.
* Confirm a non-zero strip count in the configure log.

Worth doing on its own merits, independent of any WiFi decision.

### Phase 1 — the radio tells the truth (simulator)

`WiFi.h` keeps its public surface; the body moves behind a dispatcher, the
pattern `MD5Builder.h` already uses. iOS backend in `WiFiBackend_ios.mm`:

| Call | iOS |
|---|---|
| `status()` | `NWPathMonitor` — satisfied → `WL_CONNECTED` |
| `localIP()` | `getifaddrs()`, first IPv4 on `en0` |
| `SSID()` | `NEHotspotNetwork.fetchCurrent` (entitled, approved) |
| `RSSI()` | not exposed by iOS; return a fixed plausible value and note it |
| `scanNetworks()` / `scanComplete()` | `WIFI_SCAN_FAILED` — drives the existing manual-entry branch |
| `begin(ssid, pass)` | `NEHotspotConfiguration` join, device-only |
| `softAP()` | `false` — see Phase 2 for what the firmware then shows |

Desktop keeps the `CROSSPOINT_SIM_WIFI_*` env fakes untouched; they are the QA
harness for the firmware's failure branches and this plan leans on those
branches more, not less.

### Phase 2 — make the server reachable (simulator)

* `CROSSPOINT_SIM_BIND_ALL`, default **on for iOS, off for desktop**, in
  `WebServer.cpp` and `WebSocketsServer.cpp`. Dev machines keep loopback.
* **Real mDNS.** Replace the `ESPmDNS.h` stub with a Bonjour-backed
  implementation on Apple platforms so `crosspoint.local` — the address the
  firmware advertises first and QR-encodes — actually resolves. Without this
  the primary peer-transfer address is a dead link.
* **Teach the firmware the mapped port** so the URL and both QR codes say
  `:8080`. Firmware companion: read `crosspoint_simulator::httpPort()` under
  `#ifdef SIMULATOR` at the three sites in `CrossPointWebServerActivity.cpp`.
* `isIdleTimerDisabled` while the server runs — a transfer that dies to a
  screen lock will read as a firmware bug during QA, which is the exact failure
  mode this whole exercise is meant to avoid.

### Phase 3 — in-process HTTP (simulator; also unbreaks Mac App Store)

* Split `SimHttpFetch.h` into dispatcher + backends, as `MD5Builder.h` does.
  The mock-root and `file://` paths stay shared — platform-independent, and
  useful for scripted QA on iOS.
* `SimHttpFetch_apple.mm`: `NSURLSession` + `dispatch_semaphore` to preserve
  the synchronous `fetch()` the call sites in `HTTPClient.h` and
  `esp_http_client.h` expect. **Never from the SDL main thread.**
* Map `NSError` domains onto the existing `curlExitCodeToHttpError` codes so
  firmware error handling is untouched.
* Personal build, so ATS is a free choice: `NSAllowsLocalNetworking` for the
  local server, and arbitrary loads are available if a plain-HTTP catalog needs
  QA-ing. Prefer the narrow exception; take the wide one only when a real test
  target demands it.

### Phase 4 — re-enable the screens (firmware)

Split the blunt gate into three:

| Gate | Covers | iOS |
|---|---|---|
| `CROSSPOINT_NO_SOFTAP` | `CREATE_HOTSPOT` row in `NetworkModeSelectionActivity` | **on** |
| `CROSSPOINT_NO_OTA` | `OtaUpdateActivity`, `SdFirmwareUpdateActivity`, `OtaUpdater`, `FirmwareFlasher`, `simulator_ota.cpp` | **on**, permanently |
| *(none)* | web server, WebDAV, downloads, QR, diagnostics, `WifiSelectionActivity` | **off** — these ship |

`WifiSelectionActivity` and `WifiCredentialStore` come back unchanged — the
scan-failed branch carries them. `NetworkModeSelectionActivity` loses one of
its two rows; with `MENU_ENTRIES` already table-driven
(`NetworkModeSelectionActivity.cpp:21`) that is a one-entry `#ifdef`, not a
rewrite.

### Phase 5 — peer transfer, as far as it goes

The AP cannot exist, so the honest substitutes, in preference order:

1. **Both peers on one existing WiFi.** `JOIN_NETWORK` on the phone, peer opens
   `http://crosspoint.local:8080/`. Full fidelity from the peer's side; the
   only divergence is that the owner joined the network through iOS Settings
   instead of the firmware's picker.
2. **Personal Hotspot as the `CREATE_HOTSPOT` stand-in.** The owner turns it on
   in Settings, the peer joins it, the phone serves on the hotspot address. The
   topology matches the X3's AP mode exactly; only the "device brings up the
   AP" step is manual, and the captive portal is absent.
3. **Phone joins a real X3's AP.** `NEHotspotConfiguration(ssid:
   "CrossPoint-Reader")` — an open network whose name is a compile-time
   constant, so no scan is needed. This makes the phone a *client* of a real
   X3's web UI, which is the reverse of what the firmware does and would be new
   UI. **Out of scope** unless the owner wants it as a feature in its own
   right; it is recorded here because it is the one peer-to-peer path iOS is
   genuinely good at.

Option 2 is the one to document prominently — it is what "peer transfer on the
phone" will mean in practice.

## Entitlements and Info.plist

Personal build, so all of these are self-serve capabilities:

* `com.apple.developer.networking.wifi-info` (*Access WiFi Information*) +
  `NSLocationWhenInUseUsageDescription` — real SSID, approved above.
* `com.apple.developer.networking.HotspotConfiguration` — the typed-SSID join.
  Device-only; the iOS Simulator will fail these calls, so Phase 1's join path
  cannot be QA'd on the Simulator.
* `NSLocalNetworkUsageDescription` + `NSBonjourServices` (`_http._tcp`) —
  **required**, not optional, once Phase 2 makes mDNS real.
* `NSAppTransportSecurity` → `NSAllowsLocalNetworking`.
* `ITSAppUsesNonExemptEncryption` stays `false`.

## What stays off, permanently

* **OTA and SD firmware flash.** There is no ESP32 to flash and no SD slot.
  A personal build does not change this — it was never only a guideline 2.5.2
  problem.
* **Soft AP and captive portal.** No API, and none is coming.

## Verification

Desktop first, every phase — it is the canary.

```bash
cd $HOME/src/crosspoint-reader && pio run -e simulator
CROSSPOINT_SIM_WIFI_CONNECT=fail .pio/build/simulator/program
```

iOS, in order of what each proves:

* Configure log shows a **non-zero** strip count (Phase 0).
* Settings → File Transfer reaches `NetworkModeSelectionActivity` with one row.
* `JOIN_NETWORK` → the scan-failed branch renders the manual-entry list.
* The server screen paints an address with the right port, and both QR codes
  scan to something that resolves.
* From a Mac on the same WiFi: browser fetch, `crosspoint.local:8080`
  resolution, WebDAV mount, a font download that completes.
* Same three with the app backgrounded mid-transfer — expect failure, confirm
  it fails *cleanly* rather than wedging the firmware.
* Personal Hotspot path end to end (Phase 5, option 2).
* Device-only: the `NEHotspotConfiguration` join. Cannot be QA'd on the
  Simulator, and there is still no paired device (`README.md`, "Still
  deferred").

## Open

* **Peer-transfer QA has a floor.** Options 1 and 2 both require a second
  machine and a manual Settings step, so this cannot become part of a scripted
  `CROSSPOINT_SIM_INPUT_SCRIPT` run. The firmware's AP branch will stay
  hand-tested.
* **`RSSI()` has no iOS source.** A fixed value keeps the signal-bars UI
  rendering, but bars that never move are a small standing lie. Alternative is
  hiding them on iOS, which breaks X3 parity. Parity wins by default here;
  flagging it because it is the one place the two principles collide.
