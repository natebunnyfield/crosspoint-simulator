#!/usr/bin/env bash
# "deploy mac apps" — the owner's phrase, 2026-08-19, meaning ALL THREE local
# bundles rebuilt and installed into /Applications.
#
# Not the App Store pipeline. deploy.sh is that: it signs, notarizes, embeds
# dylibs and uploads. This installs unsigned bundles for use on THIS Mac, which
# is what the three in /Applications have always been.
#
# Why it exists: those three sat at build 1 from 2026-08-07 for twelve days
# while every palette, the grain and the shortlist landed, and the owner was
# judging the Mac against them without either of us noticing.
#
#   BUILD=<n>   CFBundleVersion to stamp (default: the build-N tag + 1)
set -euo pipefail

SIM="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FW="${CROSSPOINT_FIRMWARE_DIR:-$HOME/src/crosspoint-reader}"
PACKAGER="$SIM/packaging/macos/package_macos_app.py"
DIST="$SIM/dist"
BUILD="${BUILD:-$(( $(git -C "$SIM" tag --list 'build-*' | sed 's/build-//' | sort -n | tail -1) + 1 ))}"

echo "== building from $FW, stamping build $BUILD"
( cd "$FW" && pio run -e simulator_x3 >/dev/null && pio run -e simulator >/dev/null )

rm -rf "$DIST"; mkdir -p "$DIST"
pkg() { python3 "$PACKAGER" build --version 0.1.0 --build "$BUILD" --output-dir "$DIST" "$@" >/dev/null; }

pkg --binary "$FW/.pio/build/simulator_x3/program" --device x3 \
    --env CROSSPOINT_SIM_DEVICE_PIXELS=1
pkg --binary "$FW/.pio/build/simulator_x3/program" --device x3 \
    --product-name CrossPointX3-2x --executable-name CrossPointX3-2x \
    --bundle-id com.crosspoint.CrossPointX3-2x \
    --env CROSSPOINT_SIM_DEVICE_PIXELS=1 --env CROSSPOINT_SIM_WINDOW_SCALE=2
pkg --binary "$FW/.pio/build/simulator/program" --device x4 \
    --env CROSSPOINT_SIM_DEVICE_PIXELS=1

# Verify AND boot each one before touching /Applications. A bundle that passes
# the purpose-string check can still fail to launch, and replacing a working app
# with one that does not is the worst outcome here.
for n in CrossPointX3 CrossPointX3-2x CrossPointX4; do
  python3 "$PACKAGER" verify "$DIST/$n.app" >/dev/null
  CROSSPOINT_SIM_INPUT_SCRIPT='2000:QUIT' SDL_VIDEODRIVER=dummy \
    "$DIST/$n.app/Contents/MacOS/$n" >/dev/null 2>&1 \
    || { echo "REFUSING TO INSTALL: $n built but does not run"; exit 1; }
done

for n in CrossPointX3 CrossPointX3-2x CrossPointX4; do
  pkill -x "$n" 2>/dev/null || true
done
sleep 1
for n in CrossPointX3 CrossPointX3-2x CrossPointX4; do
  rm -rf "/Applications/$n.app"
  cp -R "$DIST/$n.app" /Applications/
  echo "installed /Applications/$n.app (build $BUILD)"
done
