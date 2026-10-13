# Installing on King without TestFlight — measured 2026-10-11

Question (owner): can local installs replace TestFlight, faster and just as well?
Everything below was measured on soup against King (iPhone Air, iPhone18,4, iOS 26.6.2)
on 2026-10-11, starting from archive `build-323`.

## 1. Direct install (`xcrun devicectl`) needs King on the LAN or a cable

- catalock's `scripts/install-device.sh` already does build + `devicectl device install` +
  launch, ≈1.5 min (`~/src/catalock/docs/device-install.md`). The same team (`887M8FR447`)
  signs this app, and King is registered on it.
- **Tailscale does NOT carry it.** With King's Wi-Fi AND Bluetooth off (cellular + Tailscale
  only), `xcrun devicectl device info details --device <coredevice id>` failed:
  `A connection to this device could not be established`, `tunnelState: unavailable`.
  CoreDevice finds phones by Bonjour, which Tailscale does not carry.
- **`devicectl list devices` lies for a while.** It kept printing `available (paired)` after
  the connection was gone and only turned `unavailable` later. Check reachability with a call
  that needs a tunnel (`device info details`), never with `list devices`.

## 2. Ad hoc install over Tailscale works from anywhere

The phone PULLS from soup over HTTPS, the reverse of `devicectl`'s push, and that crosses
the tailnet.

- **Export:** `xcodebuild -exportArchive` on the existing archive with `method`
  `release-testing` (Xcode 26's name for ad hoc), automatic signing, the ASC key flags from
  `ios/testflight.sh`, and a `manifest` dict (appURL / displayImageURL / fullSizeImageURL).
  **14.5 s.** It produced `iOS Team Ad Hoc Provisioning Profile:
  com.natebunnyfield.crosspoint.x3`, expires 2027-09-18, six devices including King's
  hardware UDID `00008150-001211643A38401C`. Both the Apple Distribution identity and the
  profile already existed or were minted with no manual step.
- **Serving:** `tailscale serve --set-path /x3 <dir>` is REFUSED on this Mac ("Path serving
  is not supported on macOS due to sandbox restrictions"; this is the App Store build of
  Tailscale). Instead: a Python `http.server` on `127.0.0.1:8791` over `build/ota/`
  (gitignored), plus `tailscale serve --bg --https=443 --set-path /x3 http://127.0.0.1:8791`,
  the same pattern as europa's `/books`. Manifest served as `text/xml`. The tailnet
  certificate is valid (HTTPS enabled 2026-10-11). The page is `https://soup.taild108cf.ts.net/x3/`
  with an `itms-services://?action=download-manifest&url=…/x3/manifest.plist` link.
  The server is NOT a launchd service, so it does not survive a reboot.
- **Result: installed** on King, after the owner deleted the TestFlight copy.

## 3. An ad hoc build will NOT install over the TestFlight copy (observed once)

Access log, King = 100.82.144.16, `com.apple.appstored` = the iOS installer:

- 14:50:58–14:51:37: the manifest, a HEAD, the icon, then **three GETs of the .ipa, each
  aborted by the phone** (`BrokenPipeError` on the server). The install did not land.
- The owner deleted the TestFlight app.
- 14:51:44: the manifest, the .ipa, and no abort. Installed.

So with the TestFlight build present, the installer gave up mid-download. The cause is inferred,
not proven: iOS refusing to replace a TestFlight-installed app with an ad hoc one of the same
bundle id.

**What it actually cost, 2026-10-11:** the owner deleted the app to get past this, and lost
the GitHub token and the Claude API key (both NSUserDefaults only, `ios/CrossPointHostSettings.mm`
keys `githubToken` / `claudeApiKey`, deliberately never written anywhere else), plus the card:
notes and Claude chat (`claude-chat.md`, dated `*.md` notes on the card root), books and positions.
No copy of either credential exists on soup (checked: no `claude-key.txt` under the firmware
`fs_/` or any `~/Library/Application Support/CrossPoint*/fs_/`, `githubToken` empty in every
`settings.json`), and there is no Finder backup of King (`~/Library/Application Support/MobileSync/Backup`
does not exist). The warning below was written AFTER the loss; it should have preceded the test.
**Never suggest a step that deletes this app without first saying the card and both credentials
go with it.**

**Cost: deleting the app deletes its data container, which IS the card** (Files: On My
iPhone > CrossPoint X3): books, positions, `settings.json`, installed fonts. Switching
TestFlight → ad hoc therefore wipes the card once. Whether going BACK (ad hoc → TestFlight)
needs a delete as well is untested. Ad hoc → ad hoc updates should replace in place, keeping data;
that is also untested.

## 4. What ad hoc does not give you (unchanged from TestFlight)

- `ios/testflight.sh`'s gates run before its archive. A script that archives for ad hoc must
  run the same gates (canary, source set, device define, seed-font set, dSYM, purpose strings).
- No build number or tag history unless the script writes one.
- No TestFlight crash reports; pull crash logs off the phone instead.

## 5. Ad hoc over ad hoc: updates in place, keeping the card (owner-confirmed 2026-10-11)

- Build 325 (commit 1bf9f493) installed over the build-323 ad hoc copy with no delete; the owner
  confirmed the card and both credentials survived.
- The fixed build (95faa605) carried the SAME build number, 325, and still installed over it.
  The script now numbers past the last build in `build/ota/builds.log` anyway (3199ff15).
- The flow is `CROSSPOINT_SEED_FONTS_DIR=$HOME/src/crosspoint-reader/fs_/fonts ios/testflight.sh --adhoc`,
  then Install at https://soup.taild108cf.ts.net/x3/. It runs straight from an agent shell on soup
  (signing worked with no Terminal.app hop).

## 6. RETIRED (owner 2026-10-13, verbatim: *"Retire ad hoc"*, over making the server a LaunchAgent)

- Done 2026-10-13: the `/x3` route removed (`tailscale serve --https=443 --set-path /x3 off`;
  `/v1` and `/books` left as they were) and the `127.0.0.1:8791` server stopped. `/x3` now
  answers 404. `build/ota/` and `ios/testflight.sh --adhoc` are left in place, so bringing it
  back is sections 2 and 5: start the server, re-add the route.
- Builds go through TestFlight only.
- Still untested: going back to TestFlight from an ad hoc install. If the phone holds the ad hoc
  copy, the TestFlight build may not install over it, and the delete that would take wipes the
  card and both credentials. Warn before suggesting one.
