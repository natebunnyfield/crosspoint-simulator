# WiFi on iOS — plan

Status: Phases 0, 1, 3, the simulator half of Phase 2, and **Phase 4 (done
2026-08-28)** — the gate split and the skipped mode screen, which needed write
access to `crosspoint-reader` and now has it. What remains is the other firmware
half of Phase 2: the mapped port in the painted URL. Written 2026-08-06 against
simulator `c66d39f` and firmware `4ef1a62`; the Phase 4 section below is dated
where it was updated.

**Two things in this document have been overtaken by the firmware and are
corrected in place below**: `NetworkModeSelectionActivity` no longer exists as
an activity (it is an `OptionPopup` inside `CrossPointWebServerActivity`), and
the OTA gate is spelled `CROSSPOINT_NO_DEVICE_FLASH`, not `CROSSPOINT_NO_OTA`.

~~**None of it has been built for iOS.**~~ **Overtaken.** There is a Mac in the
loop now: `crosspoint_core` and the `CrossPointX3` app target both build for
`arm64-apple-ios`, the app runs on an iPhone simulator, and the scripted runs
quoted in Phase 4 below are from it. What is still true is the narrower claim:
there is **no paired device**, and the iOS *Simulator* cannot answer the three
things in Known limits — the real SSID, signal strength, and a genuine `en0`
address. `NEHotspotNetwork.fetchCurrent` returns nil there whatever the
entitlements say.

The host tests still carry the logic those paths run, by forcing the platform
macros on and substituting scripted backends: `wifi_host_test`,
`http_dispatch_test`, `restart_semantics_test`, `host_settings_test` (both arms),
plus the existing `pad_core_test`. They cannot tell you whether iOS reports what
the code expects.

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
| Show `Create Hotspot` on iOS? | **No.** Hide the row, and with one mode left skip the mode screen entirely |

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
| Bonjour service discovery | **yes** | `DNSServiceRegister`, no entitlement beyond the local-network prompt |
| mDNS hostname `crosspoint.local` | **no** | Bonjour publishes services, not hostnames; an app cannot claim a `.local` name |
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

**There is a THIRD case this paragraph did not cover, and it was landing in the
wrong one** (found and fixed 2026-08-28). `NWPathMonitor` answers "on WiFi" with
no entitlement at all; the SSID comes from `NEHotspotNetwork.fetchCurrent`,
which needs Access WiFi Information *plus* Location permission and returns nil
on the iOS Simulator whatever the entitlements say. So "genuinely associated,
name withheld" is common — every Simulator run, and any device where Location is
denied — and requiring the name folded it into the same branch as *no network at
all*: a one-row list offering "Add hidden network…", then an SSID keyboard and a
password keyboard, **for a network the phone was already on and which `begin()`
cannot change**. That is the scan-picker-password ritual the simplified path
exists to remove. `hostScanCount()` now gates on `connected && isWifi` alone and
`SSID()` labels the row `Wi-Fi` when iOS withholds the name — not a fabricated
network, since the association is real and only its name is missing, and not an
empty string either, because `WifiSelectionActivity` DROPS a row whose SSID is
empty and the count would then disagree with the list. `tests/wifi_host_test.cpp`
pinned the old behavior explicitly (`"a nameless association is not a listable
network"`); that assertion is inverted, with the argument, rather than deleted.

## Findings in the simulator tree

1. **The iOS exclusion lists are a silent no-op.** `CMakeLists.txt:176-177`
   calls `list(REMOVE_ITEM ... ${CROSSPOINT_IOS_EXCLUDED_SIM_SOURCES})`, but
   `e75ab8c` put the definitions in the *generated*
   `cmake/CrossPointSources.cmake` and the next regeneration (`af2e842`) wiped
   them — `tools/gen_cmake_sources.py` has no idea they exist. CMake does not
   error on `list(REMOVE_ITEM x ${undefined})`. The log prints
   `stripped 0 simulator + 0 firmware network/OTA TUs`. **Fixed in Phase 0.**

2. ~~**All 18 network TUs are in the iOS source set today.** Only
   `CROSSPOINT_NO_NETWORK=1` keeps them out of the UI. Whether they still
   compile for `arm64-apple-ios` is unverified.~~ **Resolved 2026-08-07.** They
   compile and link: `crosspoint_core` and the `CrossPointX3` app target both
   build for `arm64-apple-ios` with the network TUs in. `CROSSPOINT_NO_NETWORK`
   is gone; `CROSSPOINT_NO_DEVICE_FLASH` now gates only OTA and SD Firmware
   Update, and the exclusion list is down from 16 TUs to 4.

3. **Both shim servers bind `INADDR_LOOPBACK`** (`WebServer.cpp:435`,
   `WebSocketsServer.cpp:349`) — reachable by nothing but the phone itself.

4. **The painted URL hardcodes port 80, in three places.**
   `"http://" + connectedIP + "/"` (line 440), `http://crosspoint.local/`
   (line 415), both QR-encoded. `mapFirmwarePort` moves 80 → 8080 and the
   firmware never learns, so every address on that screen is wrong on a phone.

5. **`WiFi.localIP()` is hardcoded `127.0.0.1`** (`WiFi.h:196`), which feeds
   finding 4.

6. **mDNS was a no-op stub, and the hostname is unreachable regardless.**
   `src/ESPmDNS.h` used to return true from `begin()` and do nothing. It now
   publishes a real Bonjour service — but the firmware advertises and
   QR-encodes `http://crosspoint.local/` as its **primary** address, and no
   Apple API lets an app claim that hostname. So that URL is a dead link on
   iOS whatever we do, and **the IP URL is the only address a peer can use**.
   Fixing the port in that URL is therefore load-bearing, not cosmetic.
   `NSLocalNetworkUsageDescription` + `NSBonjourServices` are still required
   for the service registration itself.

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

### Phase 1 — the radio tells the truth (simulator) ✅ done

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

* **Units.** `signalStrength` is normalized 0.0–1.0; the firmware wants dBm and
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
behavior and Simulator runs keep the env fakes.

### Phase 2 — make the server reachable (simulator + firmware) — simulator side done

This is the phase that delivers peer transfer.

* ✅ `CROSSPOINT_SIM_BIND_ALL`, default **on for iOS, off for desktop**, in
  `WebServer.cpp` and `WebSocketsServer.cpp` via
  `crosspoint_simulator::bindAddressHostOrder()`. Dev machines keep loopback,
  and the override forces either way.
* ✅ **Bonjour advertisement**, `<dns_sd.h>`-backed, replacing the `ESPmDNS.h`
  stub on Apple platforms. Registered only when the server is bound to all
  interfaces, since advertising a loopback-only socket invites a connection
  that cannot work.

  **This does NOT make `crosspoint.local` resolve, and that claim earlier in
  this document was wrong.** ESP-IDF's mDNS claims a *hostname*; Bonjour's
  `DNSServiceRegister` publishes a *service*. An app may not claim an arbitrary
  `.local` hostname — the daemon will not cede one — so the firmware's primary
  painted URL stays unreachable on Apple platforms no matter what is
  implemented here. What it does buy is real discovery: Finder's Network,
  Safari's Bonjour bookmarks, `dns-sd -B _http._tcp`.

  The consequence is that **the IP URL is the only reachable address**, which
  promotes the mapped-port fix below from a polish item to the one that decides
  whether peer transfer works at all.
* **Teach the firmware the mapped port** so the URL and both QR codes say
  `:8080`: read `crosspoint_simulator::httpPort()` under `#ifdef SIMULATOR` at
  the three sites in `CrossPointWebServerActivity.cpp`. **Needs write access to
  the firmware repo.**
* ✅ **`ESP.restart()` routed into `SimulatorLifecycle`** as
  `rebootAsFirmwareRestart()`, deliberately NOT `rebootAsPowerWake()` — that
  sets a wake reason the firmware reads as "the user pressed POWER", and a
  restart is nobody pressing anything. On iOS the in-process `longjmp` reboot
  means the firmware's `RTC_NOINIT` globals survive exactly as RTC memory does
  on hardware, so `silentRestart()`'s "come back on Home" lands. On desktop the
  reboot is `execvp` and those globals do **not** survive, so it is opt-in via
  `CROSSPOINT_SIM_FIRMWARE_RESTART=1` rather than changing the canary's
  behavior untested.
* ✅ `isIdleTimerDisabled` while the server runs, via `sim_host_screen`. A
  transfer is minutes of no input; without it the phone locks the screen,
  suspends the app, and the socket stops accepting mid-transfer — which during
  QA reads as a bug in the firmware's web server.

### Phase 3 — in-process HTTP (simulator) ✅ done

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

### Phase 4 — re-enable the screens (firmware) ✅ done 2026-08-28

The gate is split, and it was already halfway there:

| Gate | Covers | iOS |
|---|---|---|
| `CROSSPOINT_NO_SOFTAP` | the `CREATE_HOTSPOT` choice, and with it the whole mode screen | **on** — added 2026-08-28 |
| `CROSSPOINT_NO_DEVICE_FLASH` | `SdFirmwareUpdateActivity`, `OnlineFirmwareUpdateActivity`, their Home rows, the WebDAV firmware-PUT hand-off, `simulator_ota.cpp` | **on**, permanently — already existed |
| *(none)* | web server, WebDAV, downloads, QR, diagnostics, `WifiSelectionActivity`, `WifiCredentialStore` | **off** — these ship |

**The OTA half was NOT called `CROSSPOINT_NO_OTA` and never has been.** It is
`CROSSPOINT_NO_DEVICE_FLASH`, and it landed with the network un-gating at
4a98ba8 — the name says only what stays impossible, which is writing an ESP32
partition. Nothing about that changed here; it is recorded because the plan's
own table names a macro that does not exist and the next reader would go looking
for it. The two gates are kept SEPARATE even though both are on for this target
and always will be: they are different impossibilities, and collapsing them is
exactly how `CROSSPOINT_NO_NETWORK` came to be suppressing features the app
could run.

**`NetworkModeSelectionActivity` is gone**, so the `MENU_ENTRIES` sentence below
is stale: the firmware replaced that whole activity with an in-place
`OptionPopup` (`CrossPointWebServerActivity::showNetworkModePopup`). The gate is
therefore not a one-entry `#ifdef` in a table but four small ones in
`CrossPointWebServerActivity.cpp`, which come to the same thing:

* `onEnter()` calls `onNetworkModeSelected(JOIN_NETWORK)` directly instead of
  showing the popup.
* `onWifiSelectionComplete(false)` — the cancel branch — calls `onGoHome()`
  instead of re-showing a popup that this build never showed.
* `showNetworkModePopup()` and the `MODE_SELECTION` arm of `loop()` compile out
  entirely, so no dead branch can be reached by a state that cannot occur.
* The `networkModePopup` MEMBER and the `MODE_SELECTION` enumerator stay, so the
  state machine has one shape across both builds.

Measured 2026-08-28 on an iPhone Air simulator, from a scripted run:

```
[WEBACT] Single network mode on this build; joining directly
[WEBACT] Network mode selected: Join Network
[ACT] Entering activity: WifiSelection
```

and the desktop canary, unchanged in the same session, still prints
`[WEBACT] Showing network mode popup...`.

**One consequence worth naming: backing out now reboots.** `onExit()` calls
`silentRestart()` whenever `WiFi.getMode() != WIFI_MODE_NULL`, and skipping the
mode screen means entering File Transfer always sets `WIFI_STA` — so Back from
the WiFi list goes Home *through a restart*, where before it could return to a
popup having touched nothing. On iOS that is the in-process `longjmp` reboot and
is exactly what finding 8 above asks for; on the desktop `ESP.restart()` is still
opt-in behind `CROSSPOINT_SIM_FIRMWARE_RESTART`, so the canary is unmoved.

**And with one mode left, the mode screen is skipped entirely** (owner ruling).
`CrossPointWebServerActivity::onEnter` goes straight to
`onNetworkModeSelected(JOIN_NETWORK)` rather than launching
`NetworkModeSelectionActivity`. A menu offering one choice is a keypress that
can only go one way, and a one-row version of that screen is not parity with
the X3 either — parity ends the moment the second row goes. Back from the WiFi
list therefore returns Home rather than to a mode screen, which is what
`onWifiSelectionComplete`'s cancel branch has to be pointed at.

Note this leaves `NetworkModeSelectionActivity` unreachable on iOS and so
unexercised there; it is still covered by the desktop build, which is the
canary anyway.

### Phase 5 — the hotspot fallback, as far as it goes

With `Create Hotspot` hidden this is no longer a screen at all — it is an owner
workflow, documented rather than built, for the no-network case:

* **Personal Hotspot.** The owner turns it on in Settings, the peer joins, the
  phone serves on the hotspot address. Topologically identical to the X3's AP
  mode; the "device raises the AP" step is manual and there is no captive
  portal.
* One technical consequence for Phase 1: with Personal Hotspot up and no WiFi
  association, the phone's own address is not on `en0` — it is on the hotspot's
  bridge interface, and `NWPathMonitor` reports cellular. So `localIP()` must
  fall back past `en0` rather than treating its absence as "no address", or the
  server screen will paint nothing usable in exactly the case this fallback
  exists for.
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
* Settings → File Transfer goes **straight** to a one-row network list naming
  the network the phone is actually on — no mode screen, no `Create Hotspot`.
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

Nothing. Every design question this plan raised has a ruling; what is left is
execution and the limits below.

**Phase 2's remaining firmware half — the mapped port — is still open and is now
the only thing between this and working peer transfer.** The three sites in
`CrossPointWebServerActivity.cpp` still paint and QR-encode port 80 while the
shim listens on 8080, so every address on the server screen is wrong on a phone.
It was deliberately left alone in the 2026-08-28 pass, which was scoped to the
gate split and to Update Library.

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
