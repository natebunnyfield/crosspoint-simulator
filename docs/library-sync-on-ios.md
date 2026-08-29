# Update Library on iOS — what was blocking it, and what now runs

2026-08-28. Simulator `db03944` + this change; firmware `aeda1e234` + this
change. Both trees left dirty and uncommitted.

Owner's ask: *"implement everything needed for Update Library to just work on
ios app, including simplified wifi implementation."*

Two independent blockers, one in each repo. Neither was a bug in the feature —
Update Library works on hardware — and both were the same shape: a firmware path
that assumes a machine the phone is not.

---

## 1. The token had nowhere to go

`LibraryUpdater` fetches a release from a **private** repo, so every request
carries `Authorization: Bearer <SETTINGS.githubToken>`. That field is set by
hand-editing `/.crosspoint/settings.json` on the card. **A phone cannot open
that file**, so library sync was unconfigurable on iOS — and the feature's own
"no token" screen printed *"Set githubToken in settings.json, then try again"*,
which is advice the owner could not follow.

### Where it lives now

`Settings > CrossPoint X3 > Library > GitHub Token` — a
`PSTextFieldSpecifier` with `IsSecure`, so iOS masks it as it is typed and keeps
it out of QuickType. It is the ninth of ten `PSGroupSpecifier`s in
`ios/Settings.bundle/Root.plist` (37 rows, counted with `plistlib` rather than
asserted) and the first NON-appearance row added since the 2026-08-23
clear-out. That
ruling ("make these settings the default and remove them from ios app settings
as options") was about *appearance* dials that had one right answer; this is
configuration with no other route at all, in the same class as the Read Aloud and
Zen rows that stayed.

### How it reaches the fetch — and why NOT through `SETTINGS.githubToken`

```
Settings.app "githubToken"
  -> NSUserDefaults
  -> ios/CrossPointHostSettings.mm  (sim_host_settings::githubToken)
  -> src/SimHostSettings.h          (the channel; folds to a constant off-iOS)
  -> LibraryUpdater.cpp             (githubTokenValue(), #ifdef SIMULATOR)
  -> bearerHeaderValue()            -> "Authorization: Bearer …"
```

It is **not** copied into `SETTINGS.githubToken` at boot, and that is a decision
rather than an omission. Anything landing in that field is written out by the
next settings save (`CrossPointSettings.cpp:90`), and on iOS the directory it
saves to is the simulated card — which File Transfer and WebDAV serve to
anything on the network the moment that screen is open. Asking for the token at
the moment the header is built keeps NSUserDefaults the single copy, for no loss
of function.

**The precise claim, corrected by adversarial review 2026-08-28.** An earlier
draft said `LibraryUpdater` is the only reader of `SETTINGS.githubToken` in the
whole firmware. It is not: `CrossPointSettings.cpp:90-91` reads it too, to
serialize it back into `settings.json`. That is exactly the reader this design
is avoiding, and it is why the substitution is complete anyway — the *consuming*
sites are `LibraryUpdater.cpp:68` and `:80` and nothing else, and because
nothing ever seeds the field on iOS, the serializer has nothing to write. The
`if (githubToken[0] != '\0')` guard there means the key does not even appear in
the file. But "no other reader exists" was the wrong sentence for the right
conclusion, and the wrong sentence is the one a future session would rely on.

`SETTINGS.githubToken` still wins on hardware and on the desktop, where the host
channel answers nothing.

### The size constraint, and what happens at the edge

The destination is `char githubToken[104]` — sized for a fine-grained PAT
(`github_pat_` + 82 chars). `sim_host_settings::githubToken()` copies at most
`cap - 1` bytes and returns the token's **full** length, snprintf-style, so the
one call site can tell that a truncation happened *without ever holding the
untruncated value*. It logs the LENGTH and says the token will not
authenticate. `tests/host_settings_test.cpp` runs every copy through a buffer
with poison either side of it, and pins the exact-fit case as the boundary.

Nothing logs the value. `tests/host_settings_test.cpp` reads
`ios/CrossPointHostSettings.mm` as text and fails on `NSLog`, `printf`,
`fprintf`, `SDL_Log` or `LOG_` appearing in it at all. The copy is
`sim_host_settings::copyToken` — ONE function that both backends and the test's
stand-in call, so the poison-buffer sweep sits under the bytes the phone runs
rather than under a transcription of them. It was three separate transcriptions
until adversarial review pointed out that the test therefore proved its own copy
correct and the phone's copy not at all.

**One place the token is exposed and it is the DESKTOP, not the phone.**
`SimHttpFetch`'s curl backend builds `-H 'Authorization: Bearer <token>'` into a
shell string for `popen()` (`src/SimHttpFetch.h:230-232`), so during a desktop
fetch the credential is visible in `ps` to any local process. That is
pre-existing for the settings.json route and the new
`CROSSPOINT_SIM_GITHUB_TOKEN` hatch widens who meets it. It does NOT apply to
iOS, where that branch is not compiled at all.

### The hint had to change too

`STR_LIBRARY_NEEDS_TOKEN_HINT_HOST` — *"Set GitHub Token in the Settings app,
then try again."* — is chosen when the host advertises a settings surface, and
the settings.json sentence stays everywhere else. Note `tr()` is a macro that
pastes `StrId::` onto its argument, so it cannot take a value chosen at runtime;
the selector returns the resolved `const char*` from `I18N.get()`.

---

## 2. The WiFi screens assumed hardware iOS does not have

`ios/WIFI.md` Phase 4, specified 2026-08-06 and unbuildable until now for want
of firmware write access. Full account there; the short version:

* **`CROSSPOINT_NO_SOFTAP`** is new, and gates the `CREATE_HOTSPOT` choice.
* **With one mode left the mode screen is skipped entirely**, per the owner's
  ruling. `onEnter()` calls `onNetworkModeSelected(JOIN_NETWORK)` directly.
* Back from the WiFi list goes **Home**, since the popup it used to return to no
  longer exists on that build.

**Two corrections to the plan, both found by reading rather than assuming.**
`NetworkModeSelectionActivity` is gone — the firmware replaced it with an
in-place `OptionPopup`, so the gate is four small `#ifdef`s in
`CrossPointWebServerActivity.cpp` rather than one table entry. And the OTA gate
is **`CROSSPOINT_NO_DEVICE_FLASH`**, not the `CROSSPOINT_NO_OTA` the plan names;
it already exists, is already on for iOS, and was not touched.

### The scan, and the third case nobody had

The phone cannot scan, and does not need to: it is already on a network, and
`sim_wifi_host` reports that one association as a one-row "scan". That was
already built (Phase 1). What was NOT handled is **associated but unnamed**:
`NWPathMonitor` answers "on WiFi" with no entitlement, while the SSID needs
Access WiFi Information *plus* Location and is nil on the iOS Simulator
regardless. That case fell into the same branch as *no network at all* and
produced "Add hidden network…" → SSID keyboard → password keyboard, **for a
network the phone was already on and which `begin()` cannot change** — the exact
ritual the simplified path exists to remove.

`hostScanCount()` now gates on `connected && isWifi` alone; `SSID()` labels the
row `Wi-Fi` when iOS withholds the name. Not a fabricated network — the
association is real and only its name is missing — and not an empty string,
because `WifiSelectionActivity` drops a row whose SSID is empty and the count
would then disagree with the list.

**`tests/wifi_host_test.cpp` pinned the OLD behavior by name** (`"a nameless
association is not a listable network"`). That assertion is inverted, with the
argument written out beside it, rather than deleted. Flagged here because
overturning someone's deliberate pin is worth being loud about.

### The first-open race, fixed

`sim_wifi_host::current()` starts its `NWPathMonitor` lazily, which is correct
and late: the first caller reads "not connected" because the first callback has
not run. Update Library's first question is `WiFi.status()` in `onEnter`, so the
first open after launch would paint "No Wi-Fi" on a phone that was on Wi-Fi and
then work on the second try — the shape of a bug nobody can reproduce.
`simulator_main.cpp` now starts the monitor before `setup()`. A no-op everywhere
but iOS.

---

## 3. TestFlight's curl restriction does NOT block this

`CLAUDE.md` warns that a sandboxed build cannot spawn `/usr/bin/curl`, so
`SimHttpFetch`-backed flows do not work on TestFlight. **That is the macOS App
Store path, and it does not apply to iOS.** `src/SimHttpFetch.h:264-278` is
`#if CROSSPOINT_SIM_HOST_HTTP` — on iOS the curl branch is not compiled at all,
and `hostFetch` (`ios/CrossPointHttp.mm`, NSURLSession) is the only transport.
The mock-root and `file://` fixture paths sit ahead of both, unchanged.

Proven, not reasoned: the run in §4 below reached `api.github.com` over TLS from
inside the app and came back with a status code.

---

## 4. How far it was driven headlessly, and where that stops

All measured 2026-08-28 on an iPhone Air simulator (iOS 26.5), `CrossPointX3`
built for `arm64-apple-ios` from `build/ios-verify`, driven with
`CROSSPOINT_SIM_INPUT_SCRIPT` through `SIMCTL_CHILD_*`.

**No token configured** (`defaults delete … githubToken`):

```
[1492] [ACT] Entering activity: Boot
[1708] [ACT] Entering activity: Home
[17086] [ACT] Entering activity: LibraryUpdate
[17097] [INF] [LIB] no GitHub token configured
```

Note what is NOT there: no `NO_WIFI`. On the desktop this same screen says "No
Wi-Fi connection" unless File Transfer has run first, because `WiFi.status()`
answers from a member that nothing has set. On the phone it answers from
`NWPathMonitor`, so the reader is connected from launch and Update Library is
reachable straight off Home. That difference is the whole reason the feature can
"just work" there.

**A token in the Settings key** — a value invented on the spot for this run,
`fake_pat_NOT_A_REAL_TOKEN_for_plumbing_proof`, written with
`simctl spawn … defaults write`:

```
[19591] [ACT] Entering activity: LibraryUpdate
[19604] [DBG] [HTTP] Fetching (custom headers):
        https://api.github.com/repos/natebunnyfield/claude-tools/releases/tags/library-latest
[20247] [ERR] [HTTP] unexpected status: 401
[20247] [ERR] [LIB] Release fetch failed
```

**401 is the proof.** It is what GitHub returns for a bearer token it does not
recognise, and it can only be reached if the token left NSUserDefaults, crossed
the channel, survived the `NO_TOKEN` gate, reached `bearerHeaderValue()`, and
went out on a real TLS request. A missing token stops at the line above; a
missing transport never gets a status at all.

**File Transfer, same build:**

```
[22585] [ACT] Entering activity: CrossPointWebServer
[22586] [WEBACT] Single network mode on this build; joining directly
[22586] [WEBACT] Network mode selected: Join Network
[22586] [ACT] Entering activity: WifiSelection
```

and the desktop canary in the same session, unchanged:
`[WEBACT] Showing network mode popup...`.

### Where it stops being testable off-device

* **The last step — a 200 and an actual sync — needs a real token**, which is
  the owner's to enter and was deliberately not obtained, invented or requested.
  Everything up to the authorization decision is proven; what GitHub does with a
  *valid* token is not.
* **The Settings.app row itself.** `simctl spawn defaults write` writes the same
  NSUserDefaults key the row writes, which is why the plumbing proof stands, but
  that the row *renders*, that `IsSecure` masks it, and that a value typed into
  it lands in the persistent domain are device/GUI checks. The text gate in
  `host_settings_test` covers only that the key name in the backend matches the
  key name in the plist.
* **The real SSID and the labelled row.** `NEHotspotNetwork.fetchCurrent`
  returns nil on the Simulator, so every Simulator run exercises the *withheld
  name* branch and none of them exercises the named one. Unchanged from
  `ios/WIFI.md`'s Known limits.
* **Peer transfer** still needs a second machine and stays hand-tested.

---

## 5. Checked and found CLEAN — so the next pass does not re-read it

* **`SimHttpFetch` on iOS.** Read end to end. The curl branch is not compiled;
  mock-root and `file://` precede the transport and are unchanged. No action.
* **`CROSSPOINT_NO_DEVICE_FLASH`.** Already defined `PUBLIC` on
  `crosspoint_core`, already gating both firmware-update activities, their Home
  rows, the WebDAV PUT hand-off and `simulator_ota.cpp`. Nothing re-enabled; no
  OTA path was touched while the gates moved.
* **`ios/CrossPointWiFi.mm`.** Phase 1 is complete as written — `NWPathMonitor`
  for state, `getifaddrs()` past `en0` for the address, `fetchCurrent` for name
  and strength with the dBm mapping. No change needed for either blocker.
* **`SETTINGS.githubToken` readers.** Two CONSUMERS, both in
  `LibraryUpdater.cpp` (`:68`, `:80`) — no web-settings row, no WebDAV surface,
  no other activity — plus the serializer at `CrossPointSettings.cpp:90-91`,
  which is the one this design routes around. See the correction in §1.
* **The define-parity gate.** `CROSSPOINT_NO_SOFTAP` went on
  `crosspoint_core PUBLIC`, and the configure-time `FATAL_ERROR` that catches an
  app-target-only define did not fire.
* **`tests/dial_table_test.cpp` and `tests/panel_palette_test.cpp`** both read
  `Root.plist`; both still pass with the Library group inserted. The
  assertions that certain appearance keys are ABSENT are unaffected — nothing
  appearance-related was added.
* **Firmware suite**: 594/594. **Simulator suite**: 64/64 (62 before, plus the
  two new `host_settings` arms). **Desktop canary**: builds and runs.

---

## 6. What adversarial review found, and what was done about it

Run read-only over both diffs before this was reported. One finding had teeth.

* **MEDIUM, fixed.** *Opening File Transfer on iOS and immediately backing out
  restarted the app.* `onExit()` reboots whenever `WiFi.getMode() !=
  WIFI_MODE_NULL`, and skipping the mode popup means `onEnter()` now always
  reaches `WiFi.mode(WIFI_STA)` — so a cancel that used to leave the mode NULL
  and skip `silentRestart()` instead took the in-process `longjmp` reboot for
  having done nothing. Nothing else on that path clears it: `disconnect(false)`
  does not, and `WifiSelectionActivity::onExit` deliberately leaves WiFi state
  to its parent. The `NO_SOFTAP` cancel branch now calls `WiFi.mode(WIFI_OFF)`
  first, which restores the pre-gate behavior exactly for "opened, backed out,
  never connected" and leaves the post-transfer reboot alone. **The §4 File
  Transfer capture never pressed Back, which is why my own testing missed it.**
* **Fixed.** The test's host arm re-typed the copy instead of calling it —
  `copyToken` is now one function all three sites share.
* **Fixed.** `githubToken()` allocated autoreleased objects on a `std::thread`
  with no pool; it has an explicit `@autoreleasepool` now.
* **Fixed.** A one-frame window in which `render()` could paint a bare "File
  Transfer" header over a popup this build never shows — `onEnter()` moves the
  state off `MODE_SELECTION` before dispatching rather than relying on the
  dispatch to do it.
* **Fixed, documentation.** The "only reader" sentence above, the group index,
  the stale line numbers, and `CLAUDE.md`'s Settings.app group table — in a file
  that says out loud to count the groups rather than trust prose.
* **Disproved by the reviewer, recorded so nobody re-checks:** no dangling
  pointer from `hostSsidOrLabel()` at any of its three call sites; no off-by-one
  at `cap == 0` or `cap == 1`; no stranded state or unreachable exit from the
  `#ifdef` split; `startActivityForResult` from inside `onEnter()` is safe
  because `ActivityManager` clears `pendingAction` before calling `onEnter` and
  services the push on its next loop iteration; the i18n regeneration is
  index-consistent and the new string needs no font rebuild, since every glyph
  in it is already in the generated charset.

---

## 7. One thing found and NOT fixed — a suggestion, not a change

**A wrong token now says "Could not reach GitHub."** 401 maps to
`HttpDownloader::HTTP_ERROR`, which `LibraryUpdateActivity` renders as
`STR_UPDATE_CHECK_FAILED` — *"Could not reach GitHub"*. That was a fair message
when the token could only come from a file the owner had already edited
carefully; now that it is typed on a phone keyboard, a mistyped or expired token
is the most likely failure the feature has, and the screen sends the owner to
debug Wi-Fi over a request GitHub answered promptly and correctly.

The fix has the same shape as the existing `NOT_FOUND` split, whose comment
already makes this exact argument for 404: add an `UNAUTHORIZED` code to
`HttpDownloader`, a `LibraryUpdater::BAD_TOKEN`, and a sentence that says the
token was rejected. It is not built here because it is outside the named ask,
and the whole of it is a change to firmware error paths that reach hardware.
