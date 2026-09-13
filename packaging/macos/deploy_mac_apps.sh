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
# THE FOUR BUNDLES, and what each renders at:
#
#   CrossPointX3      X3 panel, render 1, window 1 — DEVICE-EXACT reference
#   CrossPointX3-2x   X3 panel, render 2, window 2 — supersampled glyphs
#   CrossPointX3-3x   X3 panel, render 3, window 3 — supersampled glyphs
#   CrossPointX4      X4 panel, render 1, window 1 — DEVICE-EXACT reference
#
# Until 2026-09-13 the -2x name described the WINDOW and not the rasterisation:
# it was the same 1x binary with CROSSPOINT_SIM_WINDOW_SCALE=2, so its glyphs
# were 1x glyphs magnified. It now really renders at 2 (owner ruling: rebuild
# the 2x and all versions to use high fidelity), which means what you have been
# judging in it has changed — that is the point, not a side effect.
#
# CrossPointX3 and CrossPointX4 stay at 1 deliberately. They are the only
# bundles that show what the hardware shows, and a comparison needs something to
# compare against. Layout never varies with any of this: advances, kerning and
# pagination keep reading the 1x tables (docs/render-scale.md).
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

# ONE X3 BUILD, AT THE CEILING. CROSSPOINT_RENDER_SCALE is a CEILING, not the
# factor rendered at: a binary compiled at 3 renders at 1, 2 or 3, latched once
# at startup from CROSSPOINT_SIM_RENDER_SCALE (docs/render-scale.md,
# simulator_main.cpp latchRenderScale). So all three X3 bundles share this one
# binary and differ only in LSEnvironment. It was briefly built twice, once per
# scale; that was unnecessary, and it had a trap, because both cuts write the
# same .pio/build/simulator_x3/program and the second silently overwrote the
# first.
echo "== simulator_x3 at render-scale ceiling 3 (serves all three X3 bundles)"
( cd "$FW" && CROSSPOINT_RENDER_SCALE=3 pio run -e simulator_x3 >/dev/null )
echo "== simulator (X4)"
( cd "$FW" && pio run -e simulator >/dev/null )

# CROSSPOINT_SIM_RENDER_SCALE=1 ON THE PLAIN BUNDLE IS LOAD-BEARING, NOT NOISE:
# unset means "the ceiling", so leaving it off would render CrossPointX3 at 3
# and cost the only bundle that shows what the hardware shows. At scale 1 the
# hi-res companions are deliberately not registered at all (the switch's
# default: case), so this is device-exact, not 3x-downsampled.
pkg --binary "$FW/.pio/build/simulator_x3/program" --device x3 \
    --env CROSSPOINT_SIM_DEVICE_PIXELS=1 \
    --env CROSSPOINT_SIM_RENDER_SCALE=1
# WINDOW_SCALE matches RENDER_SCALE on the supersampled pair so one framebuffer
# pixel lands on one device pixel. The window is sized in LOGICAL panel pixels,
# so without it the bigger framebuffer is presented downsampled into a
# panel-sized surface and the extra rasterisation detail — the whole point —
# is thrown away before it reaches the glass (HalDisplay.cpp,
# simulatorWindowScale).
pkg --binary "$FW/.pio/build/simulator_x3/program" --device x3 \
    --product-name CrossPointX3-2x --executable-name CrossPointX3-2x \
    --bundle-id com.crosspoint.CrossPointX3-2x \
    --env CROSSPOINT_SIM_DEVICE_PIXELS=1 \
    --env CROSSPOINT_SIM_WINDOW_SCALE=2 \
    --env CROSSPOINT_SIM_RENDER_SCALE=2
pkg --binary "$FW/.pio/build/simulator_x3/program" --device x3 \
    --product-name CrossPointX3-3x --executable-name CrossPointX3-3x \
    --bundle-id com.crosspoint.CrossPointX3-3x \
    --env CROSSPOINT_SIM_DEVICE_PIXELS=1 \
    --env CROSSPOINT_SIM_WINDOW_SCALE=3 \
    --env CROSSPOINT_SIM_RENDER_SCALE=3
# X4 stays device-exact and is built at the default ceiling 1, so it has no
# scale to set. An X4-2x/-3x would need this env built at a ceiling too.
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

# THE HI-RES COMPANIONS EACH SUPERSAMPLED BUNDLE NEEDS ON ITS OWN CARD.
#
# A bundle's simulated card is keyed by its NAME ($HOME/Library/Application
# Support/<app>/fs_, HalStorage.cpp:66), so every bundle has a SEPARATE card and
# a new one starts empty. A card without <Family>/<N>x/ companions is not an
# error anyone sees: every glyph quietly falls back to 1x-replicated ("No hi-res
# companion", SdCardFontManager.cpp) and the bundle looks like a plain zoom.
#
# That bites hardest on CrossPointX3-2x, which is NOT new: it has a card in use,
# with fonts, that has never needed a 2x/ tier because until today it rendered
# at 1. Seeding "first run only" would leave exactly that card stale.
#
# So: copy the whole tree when there is no card yet, and otherwise ADD only the
# missing <Family>/<N>x/ directories. Additive — nothing existing is replaced or
# removed, so a card the owner has arranged survives. Books are never copied;
# they can be large, and a drag into the folder is the normal way in.
ensure_tier() {  # $1 = bundle name, $2 = tier
  local card="$HOME/Library/Application Support/$1/fs_/fonts"
  local src="$FW/fs_/fonts"
  if [ ! -d "$src" ]; then
    echo "NOTE: $src does not exist, so $1 has no ${2}x companions."
    echo "      Run: (cd $FW && python3 scripts/install-sim-fonts.py) then re-run this."
    return 0
  fi
  if [ ! -d "$card" ]; then
    mkdir -p "$(dirname "$card")"
    cp -R "$src" "$card"
    echo "$1: seeded fonts from $src (new card; books not copied)"
    return 0
  fi
  local added=0 fam name
  for fam in "$card"/*/; do
    [ -d "$fam" ] || continue
    name="$(basename "$fam")"
    if [ ! -d "$fam/${2}x" ] && [ -d "$src/$name/${2}x" ]; then
      cp -R "$src/$name/${2}x" "$fam/${2}x"
      added=$((added + 1))
    fi
  done
  if [ "$added" -gt 0 ]; then
    echo "$1: added ${2}x companions for $added existing famil$([ "$added" -eq 1 ] && echo y || echo ies)"
  else
    echo "$1: ${2}x companions already present"
  fi
}

ensure_tier CrossPointX3-2x 2
ensure_tier CrossPointX3-3x 3
