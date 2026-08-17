# CrossPoint Simulator

A simulator for [CrossPoint](https://github.com/crosspoint-reader/crosspoint-reader)-based firmware. It compiles the **real firmware** for the host and renders the e-ink panel in an SDL3 window — no device required. Can be used with forks of CrossPoint, but any new methods added to the firmware will need to be stubbed. If your fork diverges from the CrossPoint HAL, see [FORKING.md](FORKING.md).

**One source set, two toolchains.** The same firmware plus this HAL builds as a
desktop binary through PlatformIO, and as a native iOS app through CMake — 129
firmware translation units and 23 simulator ones for `arm64-apple-ios`, running
on a real iPhone with an on-screen button pad. The desktop build stays the
canary: it is the one that must be green first.

| | Desktop | iOS |
|---|---|---|
| Built by | PlatformIO, from the **consuming firmware repo** | CMake + Xcode, from **this** repo |
| Entry point | `src/simulator_main.cpp` | the same `main()`, under a UIKit harness |
| Read this | this file | [ios/README.md](ios/README.md) |

There is no desktop build target inside this repo — it ships as a PlatformIO
library that firmware adds as a `lib_dep` named `simulator`. The iOS target is
built here; see [ios/README.md](ios/README.md) and
[CROSSPOINT_X3_IOS_PORT_CONTEXT.md](CROSSPOINT_X3_IOS_PORT_CONTEXT.md).

**Beyond running the firmware, this fork adds:** a read-aloud page channel that
hands the displayed page to a host text-to-speech engine, host-keyboard text
entry into the firmware's own fields (with the software keyboard's show/hide
contract), a 14-preset page palette and a button-pad contrast dial, dark-mode
re-present from a cached frame, `SimulatorOverlay` for chrome outside the panel,
1x/2x/3x render scale, and Mac App Store + TestFlight packaging. Each has its
own section below or its own file in [docs/](docs/).

> [!NOTE]
> **Platform support:** macOS and Linux/WSL use different native compiler and library flags. Start from `sample-platformio-macos.ini` on macOS, or `sample-platformio-linux-wsl.ini` on Linux/WSL. Native Windows is not supported; use WSL and follow the Linux instructions.

> [!WARNING]
> This has been tested on x86_64 macOS (Intel), ARM64 macOS (Apple Silicon,
> M4), and Ubuntu under WSL on Windows. Other platforms may need additional
> libraries or platform-specific stubs.

## Prerequisites

SDL3 and `curl` must be installed on the host machine (the sources migrated
from SDL2 during the iOS port — an SDL2-only host fails compiling
`HalDisplay.cpp` with `'SDL3/SDL.h' file not found`). Linux/WSL users also
need OpenSSL development headers for MD5 support.

```bash
# macOS
brew install sdl3

# Linux — Debian/Ubuntu (including WSL): libsdl3-dev where packaged
# (Ubuntu 24.10+/Debian 13); on older releases build SDL3 from source.
sudo apt install libsdl3-dev libssl-dev

# Linux — Fedora/RHEL
sudo dnf install SDL3-devel openssl-devel

# Linux — Arch
sudo pacman -S sdl3 openssl
```

## Integration

Add the simulator to your firmware's platformio.ini as a `lib_dep` and configure the `[env:simulator]` environment. Use the sample file for your host OS:

- `sample-platformio-macos.ini`
- `sample-platformio-linux-wsl.ini`

No scripts need to be copied into the firmware repo for the simulator to build. The simulator library automatically patches consumer-side compatibility issues from its own build script when PlatformIO fetches it as a dependency, including the common `GfxRenderer::setOrientation()` hook needed for SDL window resizing.

Keep the sample `build_src_filter` exclusions unless your firmware has already
moved those files behind simulator guards. In the current CrossPoint layout,
the firmware-owned `CrossPointWebServer` and `WebDAVHandler` compile against
the simulator's lower-level `WebServer`, `WebSocketsServer`, and
`NetworkClient` shims. This exercises the real settings, files, status, and
WebDAV routes instead of a reduced simulator-only substitute.

The simulator defaults to the original X4 panel shape and SSD1677 controller.
Device-specific environments can extend the base simulator environment with
these flags:

- `-DSIMULATOR_DEVICE_X3` switches the framebuffer to 792x528 landscape,
  selects the X3 board profile, and exposes the simulator tilt sensor.
- `-DSIMULATOR_DEVICE_X4_PRO` keeps the X4 family's 800x480 framebuffer and
  selects the X4 Pro board profile. It exposes touch and swipe input, the
  capacitive Home key, the RTC, display inversion, and frontlight state.
- `-DSIMULATOR_DEVICE_STICKY` selects the Seeed Sticky's 800x480 SSD1677
  profile. It exposes touch and swipe input, the RTC, and the tilt sensor
  without exposing the X4 Pro-only Home key or frontlight.
- `-DSIMULATOR_DISPLAY_UC8179` selects the newer UC8179 controller used by
  some X4 and X4 Pro production batches.
- `-DSIMULATOR_DISPLAY_UC8279` selects UC8279d on X3, or the 800x480 UC8279
  controller on X4-family profiles.

The sample PlatformIO files include ready-to-use environments for the original
profiles plus `simulator_sticky`, `simulator_x3_uc8279`, `simulator_x4_uc8179`,
`simulator_x4_uc8279`, `simulator_x4_pro_uc8179`, and
`simulator_x4_pro_uc8279`. The UC8279 X4 Pro path mirrors current FreeInk SDK
support but remains pending validation on physical UC8279 X4 Pro hardware.

Controller profiles expose the same framebuffer geometry and device
capabilities as their original production run. The simulator records the
selected `BoardConfig::DisplayController` and identifies it in the window title;
it does not attempt to model controller timing, LUT waveforms, ghosting, or
power sequencing.

If a fork has a custom renderer and the auto-patch cannot recognize it, its simulator build should notify the display when orientation changes:

```cpp
#ifdef SIMULATOR
display.setSimulatorOrientation(static_cast<int>(o));
#endif
```

Put that in the renderer's orientation setter after updating the renderer's own orientation state.
By default, the simulator keeps its own `JPEGDEC`, `PNGdec`, and QRCode compatibility shims so existing firmware projects can update this library without changing their simulator environment. To test against the native decoder libraries instead, follow the opt-in comments in the sample PlatformIO files: define `CROSSPOINT_SIM_USE_NATIVE_DECODERS`, set `lib_compat_mode = off`, change simulator `lib_ignore` to `hal, WebSockets`, and add the native `PNGdec`/`JPEGDEC` dependencies. `WebSockets` is ignored only in native simulator builds because this repo supplies the host-backed `WebSocketsServer` implementation.

If you only want a self-contained simulator dependency, stop there.

If you also want the `Run Simulator` task to appear in the consuming repo's PlatformIO IDE task list (under the "Custom" folder), let the consuming project own the IDE task registration. Add `custom_run_simulator_target_owner = project` to `[env:simulator]`, then add one project-level hook:

For a normal fetched dependency:

```ini
custom_run_simulator_target_owner = project

extra_scripts =
  pre:scripts/gen_i18n.py
  pre:scripts/git_branch.py
  pre:scripts/build_html.py
  post:.pio/libdeps/$PIOENV/simulator/run_simulator_project.py
```

For a local symlinked dependency:

```ini
custom_run_simulator_target_owner = project

extra_scripts =
  pre:scripts/gen_i18n.py
  pre:scripts/git_branch.py
  pre:scripts/build_html.py
  post:../crosspoint-simulator/run_simulator_project.py
```

Use the symlink form only when the `Crosspoint` repo and this `crosspoint-simulator` repo are checked out side by side and your `lib_deps` entry is:

```ini
simulator=symlink://../crosspoint-simulator
```

The `custom_run_simulator_target_owner = project` line tells the library-side hook not to register the same launcher a second time. Without that, closing one simulator window can immediately relaunch another because both the library hook and the project hook try to own `run_simulator`.

Do not point `post:` at `run_simulator.py` directly. That file is already auto-loaded via `library.json` and is the backward-compatible library hook.

The `post:` line above only exposes the task in the consuming project UI. The actual launcher logic still lives in this simulator repo.


## Setup

Place EPUB books at `./fs_/books/` in the Crosspoint repo's root. This maps to the `/books/` path on the physical SD card.

## Build and run

Run this command from the Crosspoint project after you have added the `[env:simulator]` config to Crosspoint's `platformio.ini` file. Alternatively, if you added the project hook above, you can click "Build" from PlatformIO's IDE task list and then "Run Simulator" (nested under the "Custom" folder).

```bash
pio run -e simulator -t run_simulator
```

## Controls

| Key    | Action                             |
| ------ | ---------------------------------- |
| ↑ / ↓  | Page back / forward (side buttons) |
| ← / →  | Left / right front buttons         |
| Return | Confirm / Select                   |
| Escape | Back                               |
| P      | Power                              |
| S      | Simulate sleep                     |
| H      | X4 Pro capacitive Home key         |
| Mouse  | Touch-device tap and swipe         |

When the simulator is on the sleep screen, pressing any mapped simulator key wakes it. Under the hood the simulator relaunches itself and reports a synthetic power-button wake, because the native build has no real ESP deep-sleep resume path.

**Your keyboard reaches the firmware's text fields.** The X3 has no keyboard, so
firmware text entry pecks characters out of an on-screen grid — but the host's
real keyboard is carried into that same field. The firmware opens and closes the
channel, and while it is open **the table above is suspended** for everything
except Escape and the arrows. Without that, typing a Wi-Fi password would press
POWER on every `p` and sleep the device on every `s`.

Return is the one key decided per field, and both inversions of this have shipped
as bugs — hence [src/TextEntryKeyRouting.h](src/TextEntryKeyRouting.h) and a
truth-table test:

| Field | Return | Cmd/Ctrl+Return |
|---|---|---|
| Single-line (Wi-Fi password, device owner, rename) | Select — types the highlighted character | commits |
| Multi-line (note editor, Claude chat) | inserts a line break | reaches the panel's pick |

## Automated QA and screenshots

Two optional environment variables make repeatable navigation and screenshot
tests possible without desktop-control permissions:

- `CROSSPOINT_SIM_INPUT_SCRIPT` schedules input as
  `<milliseconds>:<action>`, separated by semicolons. Button actions use
  `<key>[:<hold-milliseconds>]`; keys are `BACK`, `ENTER`, `LEFT`, `RIGHT`,
  `UP`, `DOWN`, `POWER`, `SLEEP`, `HOME`, and `QUIT`. A normal key press is
  held for 80 ms unless a duration is provided.
- Touch-device actions use `TAP:<x>,<y>[,<hold-milliseconds>]` or
  `SWIPE:<x1>,<y1>,<x2>,<y2>[,<duration-milliseconds>]`. Coordinates are in
  displayed logical pixels, so they match UI layouts and screenshots after the
  firmware changes orientation. Normalized coordinates from 0.0 to 1.0 are
  also accepted for existing scripts.
- `CROSSPOINT_SIM_SCREENSHOTS` saves BMP screenshots as
  `<milliseconds>:<path>`, separated by semicolons. Create the destination
  directory before running the simulator.
- `RAWKEY:<NAME>[:<holdMs>]` pushes a real SDL key event
  (`RAWKEY:RETURN`, `RAWKEY:CMD+RETURN`, also `ESCAPE`, the arrows, `BACKSPACE`,
  `P`). It is the **only** script action that goes through the scancode→button
  gate — the button actions write the synthetic state directly, below SDL, so a
  scripted pass proves nothing about key routing. It still cannot fake a held
  *level*; see the note in [CLAUDE.md](CLAUDE.md).
- `TYPE:<text>` types into an open firmware text field (`\b` backspace,
  `\n` commit, `\e` cancel; `;` cannot appear in the text).
- `QTAP:<BUTTON>[:<holdMs>]` queues a press that fires inside `update()` rather
  than after `loop()`, which is what harness automation needs.
- The heap, battery, panic and OTA overrides live in their own table under
  [Forcing state the host does not have](#forcing-state-the-host-does-not-have).
- A sleep/wake test starts a fresh simulator process, matching the existing
  deep-sleep model. Set `CROSSPOINT_SIM_INPUT_SCRIPT_AFTER_WAKE` and
  `CROSSPOINT_SIM_SCREENSHOTS_AFTER_WAKE` for that second process. The
  pre-sleep schedules are cleared during relaunch so they cannot repeat
  forever.

Times are measured from process startup. For example:

```bash
mkdir -p ./qa-artifacts
CROSSPOINT_SIM_INPUT_SCRIPT='900:DOWN;1250:DOWN;1600:DOWN;1900:ENTER;3000:QUIT' \
CROSSPOINT_SIM_SCREENSHOTS='2400:./qa-artifacts/settings.bmp' \
  .pio/build/simulator/program
```

An X4 Pro touch and Home-key smoke test can use:

```bash
CROSSPOINT_SIM_INPUT_SCRIPT='2000:TAP:240,530;3000:HOME:100;3900:QUIT' \
CROSSPOINT_SIM_SCREENSHOTS='2500:./qa-artifacts/x4-pro-settings.bmp;3500:./qa-artifacts/x4-pro-home.bmp' \
  .pio/build/simulator_x4_pro/program
```

For Sticky, the same touch path is available without the Home key:

```bash
CROSSPOINT_SIM_INPUT_SCRIPT='2000:TAP:240,530;3600:QUIT' \
CROSSPOINT_SIM_SCREENSHOTS='1500:./qa-artifacts/sticky-home.bmp;3000:./qa-artifacts/sticky-settings.bmp' \
  .pio/build/simulator_sticky/program
```

A deterministic sleep/wake smoke test can use:

```bash
CROSSPOINT_SIM_INPUT_SCRIPT='900:SLEEP;3500:ENTER' \
CROSSPOINT_SIM_INPUT_SCRIPT_AFTER_WAKE='2200:QUIT' \
CROSSPOINT_SIM_SCREENSHOTS_AFTER_WAKE='1600:./qa-artifacts/wake.bmp' \
  .pio/build/simulator/program
```

The screenshot contains the SDL renderer output at the host's actual drawable
resolution, including Retina/HiDPI scaling. BMP is used because `SDL_SaveBMP` is
built in and adds no image-encoding dependency to the simulator — so a capture is
a BMP whatever you name the file, and anything that sniffs by content will refuse
a `.png` that is really a BMP. Convert with
`sips -s format png shot.bmp --out shot.png`.

> [!IMPORTANT]
> Read [docs/headless-qa.md](docs/headless-qa.md) before writing a screenshot
> script. Four of its five points cost a wrong diagnosis first — the worst being
> that **lists navigate on the FRONT pair**, so scripting `DOWN` at a menu does
> nothing (correctly: the side buttons page by a screenful, and a one-screen menu
> has no next screenful). Script `RIGHT`. It also records that Home starts on a
> book cover rather than a menu row, that presses need ~900 ms between them or
> half are swallowed, and that launch resumes the last book so the starting
> screen is not fixed.

### Forcing state the host does not have

The desktop has no radio, no gauge and no panic handler, so several firmware
branches are unreachable without help. **Every one of these is opt-in and leaves
the historical answer in place when unset**, so an existing script or screenshot
run is never changed by their presence.

| Variable | Forces |
|---|---|
| `CROSSPOINT_SIM_HEAP=380000` | a heap budget that counts down as the firmware allocates |
| `CROSSPOINT_SIM_HEAP_FREE=40000` | a pinned free-heap figure (wins over the budget) |
| `CROSSPOINT_SIM_BATTERY=<0-100>` | battery percentage; unset reports 100 |
| `CROSSPOINT_SIM_USB=0` | USB unplugged; unset reports always-connected |
| `CROSSPOINT_SIM_ASYNC_REFRESH=1` | the panel advertises async refresh, so the reader's overlapped page turn runs |
| `CROSSPOINT_SIM_PANIC=<reason>` | this boot is the boot after a panic — enters `CrashActivity` and writes `/crash_report.txt` |
| `CROSSPOINT_SIM_OTA_PARTITION=1` | a real next-update partition exists, so SD firmware update gets past "Invalid firmware" |
| `CROSSPOINT_SIM_OTA=none\|available\|error` | what the OTA release check reports |
| `CROSSPOINT_SIM_OTA_VERSION=<string>` | the version that check names |
| `CROSSPOINT_SIM_OTA_INSTALL=error\|ok\|cancel` | how an OTA install ends |
| `CROSSPOINT_SIM_WIFI_NETWORKS`, `_CONNECT`, `_AP` | the Wi-Fi scan results and connection outcome |
| `CROSSPOINT_SIM_HOST_KEYBOARD=1` | a host software keyboard is up — the editors drop their own panel and give the rows to text |
| `CROSSPOINT_SIM_DARK=1` | panel polarity (but `SETTINGS.darkMode` wins during `setup()` on the desktop) |
| `CROSSPOINT_SIM_PANEL_{INK,PAPER}_{LIGHT,DARK}` | the page's two tones, as hex |
| `CROSSPOINT_SIM_SD=<path>` | where the simulated SD card lives; unset uses `./fs_` |
| `CROSSPOINT_SIM_FIRMWARE_RESTART=1` | `ESP.restart()` really re-execs, instead of doing nothing |

The panic latch is deliberately **one-shot**: it consumes its own variable on the
first read, so the reboot out of the crash screen lands somewhere else — exactly
as the boot after a real panic does on hardware. Without that, the crash screen
would have no exit.

`CROSSPOINT_SIM_PANIC` also demonstrates the intent of the whole group. Before
it existed, `isRebootFromPanic()` returned `false` unconditionally, so
`CrashActivity` compiled into every build and could not be entered by any means
— the simulator was not failing to test that screen, it was reporting the screen
as covered. The rest of the table has the same shape.

## Running the tests

Twenty-two host tests build and run in one command, and it exits non-zero on the
first failure:

```bash
tests/run_all.sh            # everything
tests/run_all.sh -k palette # only tests whose name matches
```

They cover input routing, text entry, the panel and pad palettes, sleep, the
network shims, restart semantics, task lifetime, read-aloud, SHA-256, the
device-truth flags above, and the build-identity guard. Run them when touching
any of those.

Three shell tests are **not** in the runner, because each needs a firmware
checkout and uses exit code 2 to mean SKIP, which a pass/fail runner would
misreport as a failure:

```bash
tests/test_sleep_wake.sh <firmware-checkout>          # deep-sleep wake edge latch
tests/test_text_entry.sh <firmware-checkout>          # host keyboard into a firmware field
tests/test_read_aloud_capture.sh <firmware-checkout>  # page capture + a scripted page turn
```

## The color dials

Three host-side settings decide what the page and the pad look like. **None of
this reaches device firmware**, which has no Settings app to expose it.

| Dial | Lives in | Documented in |
|---|---|---|
| Page palette — 15 named presets plus Custom | [src/PanelPalette.h](src/PanelPalette.h) | [ios/README.md](ios/README.md), [docs/crt-phosphor-presets.md](docs/crt-phosphor-presets.md) |
| Button pad outline and fill | [ios/PadPalette.h](ios/PadPalette.h) | [docs/pad-outline-black-and-white.md](docs/pad-outline-black-and-white.md) |
| Render scale 1x / 2x / 3x | firmware `RenderScale.h`, latched in `simulator_main.cpp` | [docs/ios-render-scale.md](docs/ios-render-scale.md) |

On the desktop the page palette is set with the `CROSSPOINT_SIM_PANEL_*`
variables above; on iOS it is a picker in Settings.app. Both polarities default
to what this repo always hardcoded, so a build that never sets one is
pixel-identical to before the dial existed.

## Mac App Store packaging

The native build produces a bare executable at `.pio/build/<env>/program`. The
Mac App Store needs it inside a `.app` bundle whose `Info.plist` carries privacy
purpose strings, or App Store Connect rejects the upload:

```
ITMS-90683: Missing purpose string in Info.plist ... should contain a
NSCameraUsageDescription key with a user-facing purpose string
```

The simulator only calls `SDL_Init(SDL_INIT_VIDEO)`; it never opens a camera or
a Bluetooth device. The rejection comes from Apple's static scan of the linked
SDL library, which references those APIs for camera and game-controller
support. As Apple's own notice puts it, "While your app might not use these
APIs, a purpose string is still required."

[packaging/macos/Info.plist.in](packaging/macos/Info.plist.in) holds those
strings and is the single source of truth for all three subcommands of
[packaging/macos/package_macos_app.py](packaging/macos/package_macos_app.py):

```bash
# Wrap a built binary in a bundle that already has the purpose strings.
python3 packaging/macos/package_macos_app.py build \
  --binary .pio/build/simulator_x3/program \
  --device x3 --version 0.1.0 --build 2 \
  --bundle-id com.example.CrossPointX3 --output-dir dist

# Add missing purpose strings to a bundle built by some other pipeline.
python3 packaging/macos/package_macos_app.py patch dist/CrossPointX3.app

# Exit non-zero if a bundle would be rejected. Run this before every upload.
python3 packaging/macos/package_macos_app.py verify dist/CrossPointX3.app
```

`--device` picks the product and executable name (`x3`, `x4`, `x4-pro`).
`patch` works on Xcode-built bundles too — it reads binary plists and writes
them back in the same format, touching only the missing keys.

From a consuming firmware repo, the same packaging runs as a PlatformIO target:

```bash
pio run -e simulator_x3 -t package_macos_app
```

The target infers the device from the environment's `SIMULATOR_DEVICE_*` flag
and reads these optional project options:

```ini
[env:simulator_x3]
custom_macos_app_bundle_id = com.example.CrossPointX3
custom_macos_app_version = 0.1.0
custom_macos_app_build = 2
custom_macos_app_output_dir = dist
custom_macos_app_icon = packaging/macos/CrossPoint.icns
```

Two things are on you before an upload: `custom_macos_app_bundle_id` must match
the app record in App Store Connect, and `custom_macos_app_build` must be higher
than any build already uploaded for that version.

### Shipping to TestFlight

[packaging/macos/deploy.sh](packaging/macos/deploy.sh) runs the whole chain —
build, bundle, verify purpose strings, embed dylibs, sign, `productbuild`,
`altool --upload-app`, tag. Run it on the Mac from the firmware project:

```bash
BUNDLE_ID=com.example.CrossPointX3 \
SIGN_APP="Apple Distribution: Your Name (TEAMID)" \
SIGN_INSTALLER="3rd Party Mac Developer Installer: Your Name (TEAMID)" \
ASC_KEY_ID=XXXXXXXXXX ASC_ISSUER=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx \
ASC_KEY_PATH=~/.appstoreconnect/private_keys/AuthKey_XXXXXXXXXX.p8 \
  ./packaging/macos/deploy.sh
```

`DRY_RUN=1` prints every command without running it, and `SKIP_UPLOAD=1` stops
after signing. `BUILD_NUMBER` auto-bumps from the last `macos-build-N` tag —
Apple silently rejects a duplicate build number, and build 1 is already consumed.

Signing needs the login keychain, which only a GUI Terminal session has. Firing
`deploy.sh` from a sandboxed agent shell or a bare SSH session fails partway
through with `errSecInternalComponent`. Route it through Terminal.app instead:

```bash
osascript packaging/macos/deploy.applescript
osascript packaging/macos/deploy.applescript "BUILD_NUMBER=3" "SKIP_UPLOAD=1"
```

Each argument is a `KEY=VALUE` pair, passed through `env` so it survives into
the shell Terminal spawns. This needs the Mac logged in and unlocked, and
`osascript` allowed to control Terminal under Privacy & Security → Automation.
AppleScript returns as soon as Terminal starts the command; it cannot report
whether the deploy succeeded.

### Shipping without a Mac

[.github/workflows/testflight.yml](.github/workflows/testflight.yml) runs the
same chain on a GitHub-hosted `macos-latest` runner, so shipping does not depend
on one machine being awake and unlocked. Trigger it from the Actions tab.

Without secrets it builds, packages, verifies the purpose strings, embeds
dylibs, and uploads the `.app` as an artifact — a standing check that a bundle
would pass Apple's validation. Add these repository secrets to enable signing
and upload: `MACOS_CERT_P12`, `MACOS_CERT_P12_PASSWORD`, `MACOS_INSTALLER_P12`,
`MACOS_INSTALLER_P12_PASSWORD`, `SIGN_APP`, `SIGN_INSTALLER`, `BUNDLE_ID`,
`ASC_KEY_ID`, `ASC_ISSUER`, `ASC_KEY_P8`, `MACOS_PROVISIONING_PROFILE`. Produce
the blobs with `base64 -i cert.p12 | pbcopy`, then re-run with `skip_upload`
unchecked.

`MACOS_PROVISIONING_PROFILE` is base64 of a Mac App Store `.provisionprofile`
for your bundle ID. App Sandbox is not a portal capability — it comes from
`CrossPoint.entitlements` and needs nothing enabled on the App ID. It is
embedded at `Contents/embedded.provisionprofile` before signing, because the
signature seals it. Xcode does this during `-exportArchive`; a hand-assembled
bundle has to do it explicitly, and the store rejects a build without one even
though `codesign` succeeds locally. `deploy.sh` takes the same thing as a file
path in `PROVISIONING_PROFILE`.

The runner creates its own keychain and calls `security set-key-partition-list`,
which is what stops `codesign` from blocking on a GUI prompt. That replaces the
Terminal.app detour needed on a personal Mac.

> [!WARNING]
> Mac App Store builds must be sandboxed
> ([packaging/macos/CrossPoint.entitlements](packaging/macos/CrossPoint.entitlements)),
> and the sandbox blocks spawning binaries outside the bundle. `SimHttpFetch`
> shells out to `/usr/bin/curl`, so OPDS/catalog downloads, KOReader sync, and
> SD-font fetches will fail in a TestFlight build until those flows move to an
> in-process HTTP client. Reading local books is unaffected.

## Notes

**Host-backed network flows**: OPDS/catalog downloads and KOReader sync use the
host's `curl` binary through simulator implementations of `HTTPClient` and
`esp_http_client`. This keeps the firmware code path intact while allowing the
desktop build to reach real HTTP/HTTPS services.

**Mocked downloads**: Set `CROSSPOINT_SIM_HTTP_MOCK_ROOT` to a folder of local
fixtures to make host-backed HTTP requests return local files by basename before
falling back to the real network. This is useful for SD-font testing because the
firmware can request its normal release URLs while the simulator serves a local
`fonts.json` and `.cpfont` files:

```bash
cd /path/to/firmware
python3 -m pip install -r lib/EpdFont/scripts/requirements.txt
python3 lib/EpdFont/scripts/build-sd-fonts.py \
  --only NotoSansExtended \
  --manifest \
  --base-url "https://github.com/crosspoint-reader/crosspoint-fonts/releases/download/local/"
CROSSPOINT_SIM_HTTP_MOCK_ROOT="$PWD/lib/EpdFont/scripts/output" \
  pio run -e simulator -t run
```

The mock still uses the firmware's normal manifest parsing, file download,
write-to-SD, `.cpfont` validation, registry refresh, and font-selection flow.

**File transfer**: The simulator provides host-backed `WebServer`,
`WebSocketsServer`, and `NetworkClient` shims so firmware-owned file-transfer
routes can run on the host. Firmware web servers that bind port 80 are exposed
on `http://127.0.0.1:8080/`; WebSocket servers that bind port 81 are exposed on
`ws://127.0.0.1:8081/`. Set `CROSSPOINT_SIM_HTTP_PORT` to another unprivileged
port if that pair is occupied; the WebSocket endpoint uses the following port.
For example, `CROSSPOINT_SIM_HTTP_PORT=18080` exposes HTTP on 18080 and
WebSocket on 18081. This supports the browser file manager, WebSocket upload
progress, streamed downloads, and common WebDAV-style requests such as
`OPTIONS`, `PROPFIND`, `PUT`, `DELETE`, `MKCOL`, `MOVE`, and `COPY`. WebDAV
`LOCK` and `UNLOCK` remain compatibility-only unless the firmware implements
locking semantics.

The `run_simulator` target also accepts the port through PlatformIO, which is
convenient when the conflict is permanent on a development machine:

```ini
[env:simulator]
custom_simulator_http_port = 18080
```

Direct binary launches use the environment variable form.

**Firmware updates**: nothing here ever writes flash or moves a boot pointer —
`esp_partition_write()`, `esp_partition_erase_range()` and `ota_boot::switchTo()`
all fail honestly, which is a failure mode the firmware already handles and
reports. What *is* now reachable, opt-in, is everything up to the first byte
written: `CROSSPOINT_SIM_OTA_PARTITION=1` gives the firmware a real next-update
partition (geometry read off the firmware's own `partitions.csv`), so the SD
firmware update screen gets past "Invalid firmware" into its size and image
checks, and `CROSSPOINT_SIM_OTA=available` drives the release-check flow.

The image validator itself is still stubbed, and that is a firmware build
decision rather than a simulator one — `platformio.ini` drops
`network/FirmwareFlasher.cpp` from the `simulator` env, so
`validateImageFile()` returns `UNSUPPORTED_IN_SIMULATOR` even though it only
reads a file and does arithmetic. Tracked as **S-014** in [BUGS.md](BUGS.md).

**Image previews**: The default simulator shims decode JPEG and PNG files on the
host and render a rough grayscale preview through the firmware's normal image
callbacks. This is meant to make image pages and PNG sleep overlays visible
while testing desktop flows. Native decoder libraries can be enabled with the
sample config's opt-in flags when decoder compatibility matters more than the
self-contained default. Neither mode simulates device-specific e-ink image
quality, refresh behavior, or memory pressure.

**Cache**: On first open of an ebook, an "Indexing..." popup will appear while the section cache is built. If you see rendering issues after a code change that affects layout, delete `./fs_/.crosspoint/` to clear stale caches.

> [!WARNING]
> **Upstream compatibility:** The simulator mirrors interfaces used by Crosspoint. If Crosspoint adds or changes methods in a shared library and the simulator build reaches that code path, the simulator can fail to compile or link until a matching implementation or stub is added here. In many cases this is just a small no-op shim. Open a PR if the change tracks upstream CrossPoint, fills a gap in the emulated Arduino/ESP-IDF layer, or fixes the simulator itself. If the change only matches your own fork's HAL, maintain it in a fork of this repo instead. See [FORKING.md](FORKING.md).
