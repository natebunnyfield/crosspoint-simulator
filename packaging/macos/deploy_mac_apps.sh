#!/usr/bin/env bash
# "deploy mac apps" — the owner's phrase, 2026-08-19, meaning ALL the local
# bundles rebuilt and installed into /Applications.
#
# Not the App Store pipeline. deploy.sh is that: it signs, notarizes, embeds
# dylibs and uploads. This installs unsigned bundles for use on THIS Mac, which
# is what the ones in /Applications have always been.
#
# Why it exists: those three sat at build 1 from 2026-08-07 for twelve days
# while every palette, the grain and the shortlist landed, and the owner was
# judging the Mac against them without either of us noticing.
#
# THE FOUR BUNDLES, and which of them actually supersamples:
#
#   CrossPointX3      X3 panel, render scale 1 — device-exact
#   CrossPointX3-2x   X3 panel, render scale 1, WINDOW doubled
#   CrossPointX3-3x   X3 panel, RENDER SCALE 3 — supersampled glyphs
#   CrossPointX4      X4 panel, render scale 1 — device-exact
#
# The -2x name has always described the WINDOW, not the rasterisation: it is
# the same binary as CrossPointX3 with CROSSPOINT_SIM_WINDOW_SCALE=2, so its
# glyphs are the 1x glyphs magnified. -3x is the different thing — a separate
# binary compiled at CROSSPOINT_RENDER_SCALE=3, so the hi-res paths are compiled
# in and it reads the <Family>/3x/ .cpfont companions. Layout is unaffected
# either way: advances, kerning and pagination keep reading the 1x tables
# (docs/render-scale.md).
#
#   BUILD=<n>   CFBundleVersion to stamp (default: the build-N tag + 1)
set -euo pipefail

SIM="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FW="${CROSSPOINT_FIRMWARE_DIR:-$HOME/src/crosspoint-reader}"
PACKAGER="$SIM/packaging/macos/package_macos_app.py"
DIST="$SIM/dist"
BUILD="${BUILD:-$(( $(git -C "$SIM" tag --list 'build-*' | sed 's/build-//' | sort -n | tail -1) + 1 ))}"
APPS=(CrossPointX3 CrossPointX3-2x CrossPointX3-3x CrossPointX4)

echo "== building from $FW, stamping build $BUILD"
rm -rf "$DIST"; mkdir -p "$DIST"
pkg() { python3 "$PACKAGER" build --version 0.1.0 --build "$BUILD" --output-dir "$DIST" "$@" >/dev/null; }

# THE 3x CUT FIRST, AND PACKAGED BEFORE THE NEXT BUILD RUNS. CROSSPOINT_RENDER_SCALE
# changes the compiler command line but NOT the output path, so both cuts of
# simulator_x3 land on the same .pio/build/simulator_x3/program and the second
# build overwrites the first. Doing 3x first also leaves the tree at the 1x
# default, which is what a later bare `pio run -e simulator_x3` expects.
echo "== simulator_x3 at render scale 3"
( cd "$FW" && CROSSPOINT_RENDER_SCALE=3 pio run -e simulator_x3 >/dev/null )
# WINDOW_SCALE=3 alongside it so one framebuffer pixel lands on one device
# pixel. The window is sized in LOGICAL panel pixels, so without it the 3x
# framebuffer is presented downsampled into a panel-sized surface and the extra
# rasterisation detail — the whole point of this bundle — is thrown away before
# it reaches the glass (HalDisplay.cpp, simulatorWindowScale). RENDER_SCALE=3 is
# redundant while the ceiling is 3 (unset means the ceiling) and is passed
# anyway, so the bundle still renders at 3 if the ceiling ever rises.
pkg --binary "$FW/.pio/build/simulator_x3/program" --device x3 \
    --product-name CrossPointX3-3x --executable-name CrossPointX3-3x \
    --bundle-id com.crosspoint.CrossPointX3-3x \
    --env CROSSPOINT_SIM_DEVICE_PIXELS=1 \
    --env CROSSPOINT_SIM_WINDOW_SCALE=3 \
    --env CROSSPOINT_SIM_RENDER_SCALE=3

echo "== simulator_x3 and simulator at render scale 1"
( cd "$FW" && pio run -e simulator_x3 >/dev/null && pio run -e simulator >/dev/null )

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
for n in "${APPS[@]}"; do
  python3 "$PACKAGER" verify "$DIST/$n.app" >/dev/null
  CROSSPOINT_SIM_INPUT_SCRIPT='2000:QUIT' SDL_VIDEODRIVER=dummy \
    "$DIST/$n.app/Contents/MacOS/$n" >/dev/null 2>&1 \
    || { echo "REFUSING TO INSTALL: $n built but does not run"; exit 1; }
done

for n in "${APPS[@]}"; do
  pkill -x "$n" 2>/dev/null || true
done
sleep 1
for n in "${APPS[@]}"; do
  rm -rf "/Applications/$n.app"
  cp -R "$DIST/$n.app" /Applications/
  echo "installed /Applications/$n.app (build $BUILD)"
done

# A bundle's simulated card is keyed by its NAME
# ($HOME/Library/Application Support/<app>/fs_, HalStorage.cpp:66), so a newly
# added bundle starts with an EMPTY one -- no books and, more to the point for
# this one, no fonts. With no <Family>/3x/ companions on the card every glyph
# falls back to 1x-replicated ("No hi-res companion", SdCardFontManager.cpp) and
# the 3x build shows nothing a 2x window would not. So seed the fonts from the
# firmware's fs_, where install-sim-fonts.py puts all three tiers (1x + 2x/ +
# 3x/). FIRST RUN ONLY: an existing card is never touched, so a card the owner
# has arranged survives every later deploy. Books are deliberately not copied --
# they can be large, and a drag into the folder is the normal way in.
CARD_3X="$HOME/Library/Application Support/CrossPointX3-3x/fs_"
if [ -d "$CARD_3X/fonts" ]; then
  echo "CrossPointX3-3x card already has fonts; left alone"
elif [ -d "$FW/fs_/fonts" ]; then
  mkdir -p "$CARD_3X"
  cp -R "$FW/fs_/fonts" "$CARD_3X/fonts"
  echo "seeded $CARD_3X/fonts from $FW/fs_/fonts (first run; books not copied)"
else
  echo "NOTE: $FW/fs_/fonts does not exist, so CrossPointX3-3x has no fonts yet."
  echo "      Run: (cd $FW && python3 scripts/install-sim-fonts.py) then re-run this."
fi
