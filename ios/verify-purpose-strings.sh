#!/usr/bin/env bash
#
# Refuse to upload an IPA that App Store Connect would bounce with ITMS-90683.
#
#   ios/verify-purpose-strings.sh <path/to/App.ipa>
#
# ONE check, TWO callers: ios/testflight.sh on the Mac and the TestFlight iOS
# workflow on a hosted runner. It lived inline in testflight.sh until
# 2026-09-05, when the workflow's own copy -- the older, unconditional one --
# failed run 21 by demanding NSCameraUsageDescription, a key Info.plist.in
# deliberately omits. Two copies of a gate drift; this is the one.
#
# Build 1 was rejected with ITMS-90683: the SDL3 of that era compiled its
# camera and Bluetooth drivers in, so the binary genuinely referenced those
# APIs and App Store Connect demanded purpose strings. Check the IPA that will
# actually be uploaded, not the source template, so a plist-processing
# regression cannot slip through. Cheap (<1s) next to a wasted upload and a
# burned build number.
#
# The demand is derived from the BINARY, at symbol level. A purpose string is
# required IFF the shipped binary actually references the API. Demanding all
# three unconditionally was right while SDL3 was built with every subsystem
# on. Once SDL_CAMERA/AUDIO/JOYSTICK/HAPTIC/SENSOR were turned off
# (CMakeLists.txt), CoreBluetooth, AVFoundation, CoreHaptics and AudioToolbox
# stopped linking at all and the strings were correctly dropped from
# Info.plist.in -- at which point an unconditional check blocks a build
# ITMS-90683 would never have rejected. Verified on build 21: zero undefined
# refs to CBCentral/AVCapture/CBPeripheral. Deriving the requirement from the
# binary still catches the original failure: re-enable an SDL subsystem, the
# framework returns, and the string is demanded again.

set -euo pipefail

IPA="${1:-}"
[[ -n "$IPA" && -f "$IPA" ]] || { echo "usage: $0 <App.ipa>" >&2; exit 2; }

PURPOSE_KEYS=(NSCameraUsageDescription
              NSBluetoothAlwaysUsageDescription
              NSBluetoothPeripheralUsageDescription)
IPA_PLIST_DIR=$(mktemp -d)
trap 'rm -rf "$IPA_PLIST_DIR"' EXIT
unzip -q "$IPA" 'Payload/*.app/Info.plist' -d "$IPA_PLIST_DIR"
IPA_PLIST=$(find "$IPA_PLIST_DIR" -name Info.plist | head -1)
[[ -n "$IPA_PLIST" ]] || { echo "ERROR: no Info.plist inside $IPA"; exit 1; }

unzip -q -o "$IPA" 'Payload/*.app/CrossPointX3' -d "$IPA_PLIST_DIR" 2>/dev/null || true
IPA_BIN=$(find "$IPA_PLIST_DIR/Payload" -maxdepth 2 -type f -name 'CrossPointX3' | head -1)
NEEDS_CAMERA=0
NEEDS_BT=0
CAMERA_WHY="no AVCapture class reference and no compiled-in camera driver class"
BT_WHY="CoreBluetooth not linked and no CBCentral/CBPeripheral reference"
if [[ -n "$IPA_BIN" ]]; then
  LINKED=$(otool -L "$IPA_BIN" 2>/dev/null || true)
  CLASSES=$(otool -v -s __TEXT __objc_classname "$IPA_BIN" 2>/dev/null || true)
  UNDEF=$(nm -u "$IPA_BIN" 2>/dev/null || true)
  # SYMBOL-LEVEL, deliberately not framework-level. Linking AVFoundation is not
  # a camera reference: since 2026-08-08 this binary links it for
  # AVSpeechSynthesizer (read-aloud), and the framework-level test demanded
  # NSCameraUsageDescription for a capability the app does not have -- measured
  # on build 39: zero AVCapture class refs, zero camera selectors, SDL built
  # with SDL_CAMERA_DISABLED. Using an API means an undefined
  # _OBJC_CLASS_$_AVCapture* symbol (or SDL's own camera driver classes compiled
  # in), so that is what is tested. If Apple ever bounces a build with
  # ITMS-90683 naming the camera DESPITE these all being zero, re-add the
  # framework test here and write down the build number.
  if grep -q '_OBJC_CLASS_\$_AVCapture' <<<"$UNDEF"; then
    NEEDS_CAMERA=1; CAMERA_WHY="binary references AVCapture classes"
  elif grep -qiE 'SDLCamera|CaptureVideoData' <<<"$CLASSES"; then
    NEEDS_CAMERA=1; CAMERA_WHY="SDL camera driver classes are compiled in"
  fi
  # CoreBluetooth vends nothing but Bluetooth, so the framework appearing in the
  # load commands IS a Bluetooth reference; the class test is belt and braces.
  if grep -q 'CoreBluetooth' <<<"$LINKED"; then
    NEEDS_BT=1; BT_WHY="CoreBluetooth is linked"
  elif grep -q '_OBJC_CLASS_\$_CBCentral\|_OBJC_CLASS_\$_CBPeripheral' <<<"$UNDEF"; then
    NEEDS_BT=1; BT_WHY="binary references CBCentral/CBPeripheral"
  fi
else
  # Could not inspect the binary -- demand everything rather than silently
  # skipping the check.
  echo "  WARNING: no binary found inside the IPA; requiring all purpose strings"
  NEEDS_CAMERA=1; CAMERA_WHY="binary could not be inspected"
  NEEDS_BT=1; BT_WHY="binary could not be inspected"
fi

MISSING=0
for key in "${PURPOSE_KEYS[@]}"; do
  case "$key" in
    NSCameraUsageDescription) REQUIRED=$NEEDS_CAMERA ;;
    NSBluetooth*) REQUIRED=$NEEDS_BT ;;
    *) REQUIRED=1 ;;
  esac
  case "$key" in
    NSCameraUsageDescription) WHY=$CAMERA_WHY ;;
    NSBluetooth*) WHY=$BT_WHY ;;
    *) WHY="always required" ;;
  esac
  VALUE=$(plutil -extract "$key" raw -o - "$IPA_PLIST" 2>/dev/null) || VALUE=""
  if [[ -n "$VALUE" && $REQUIRED -eq 1 ]]; then
    echo "  $key ok ($WHY)"
  elif [[ -n "$VALUE" ]]; then
    # Present but not demanded: harmless, but say so rather than implying it
    # was needed -- a declared-but-unused privacy string is worth noticing.
    echo "  $key present but not required ($WHY)"
  elif [[ $REQUIRED -eq 1 ]]; then
    echo "  $key MISSING ($WHY)"
    MISSING=1
  else
    echo "  $key not needed ($WHY)"
  fi
done
if [[ $MISSING -ne 0 ]]; then
  echo "ERROR: the IPA is missing purpose strings for APIs it actually"
  echo "references, and App Store Connect will reject it with ITMS-90683."
  echo "Fix ios/Info.plist.in and rebuild."
  exit 1
fi
