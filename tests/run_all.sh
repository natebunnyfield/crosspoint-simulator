#!/usr/bin/env bash
# Run every host-compilable simulator test.
#
# Exists because the only way to run this suite was to hand-copy six multi-line
# c++ invocations out of CLAUDE.md, so in practice it ran when someone
# remembered to. There is no CI on push or pull_request in this repo either
# (both workflows are workflow_dispatch), which means a green suite has never
# gated anything.
#
#   tests/run_all.sh          # build and run everything
#   tests/run_all.sh -k wifi  # only tests whose name matches
#
# The two shell tests (test_sleep_wake.sh, test_text_entry.sh) are NOT run here:
# both need a desktop binary built from a firmware checkout and exit 2 to mean
# SKIP, which a plain pass/fail runner would misreport. Run them by hand with a
# firmware path, as CLAUDE.md describes.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

FILTER="${2:-}"
[[ "${1:-}" == "-k" ]] || FILTER=""

pass=0 fail=0 skipped=0
failed_names=()

# run_direct <name> <command...> -- already-runnable tests, no compile step.
# The C++ tests need building first; a Python one does not, and faking a compile
# phase for it would only make the report lie about which phase failed.
run_direct() {
  local name="$1"; shift
  if [[ -n "$FILTER" && "$name" != *"$FILTER"* ]]; then
    return
  fi
  printf '%-22s ' "$name"
  if "$@" >"$OUT/$name.log" 2>&1; then
    echo "PASS"
    pass=$((pass + 1))
  else
    echo "FAIL"
    tail -16 "$OUT/$name.log" | sed 's/^/    /'
    fail=$((fail + 1)); failed_names+=("$name")
  fi
}

# run <name> <compile-command...> -- the binary is $OUT/<name>
run() {
  local name="$1"; shift
  if [[ -n "$FILTER" && "$name" != *"$FILTER"* ]]; then
    return
  fi
  printf '%-22s ' "$name"
  if ! "$@" >"$OUT/$name.log" 2>&1; then
    echo "COMPILE FAIL"
    sed -n '1,8p' "$OUT/$name.log" | sed 's/^/    /'
    fail=$((fail + 1)); failed_names+=("$name (compile)")
    return
  fi
  if "$OUT/$name" >>"$OUT/$name.log" 2>&1; then
    echo "PASS"
    pass=$((pass + 1))
  else
    echo "FAIL"
    tail -12 "$OUT/$name.log" | sed 's/^/    /'
    fail=$((fail + 1)); failed_names+=("$name")
  fi
}

cd "$REPO"

run pad_core \
  c++ -std=c++17 -Iios -o "$OUT/pad_core" tests/pad_core_test.cpp ios/PadCore.cpp

# Reads ios/Settings.bundle/Root.plist from the repo root -- hence the `cd`
# above -- and cross-checks every row label against the tone that row selects.
run pad_palette \
  c++ -std=c++17 -Iios -o "$OUT/pad_palette" tests/pad_palette_test.cpp

# The keyboard chip's chevron: that it antialiases, and that it is still the
# same shape it was when the owner approved it.
run chevron_coverage \
  c++ -std=c++17 -Iios -o "$OUT/chevron_coverage" tests/chevron_coverage_test.cpp
# The page's own ink and paper: the defaults byte-for-byte, the interpolation
# that produces every gray between them, the hex parsing behind the Custom
# fields, and the contrast figures the preset rows print in Settings.app. Reads
# Root.plist from the repo root, same as pad_palette above.
run panel_palette \
  c++ -std=c++17 -Isrc -o "$OUT/panel_palette" tests/panel_palette_test.cpp

# The AA plane decode. Dark mode paints only full ink in the base pass, so every
# glyph edge arrives base-WHITE and flagged -- and the decode used to discard
# exactly those, leaving dark-mode text with no antialiasing at all. The masks
# are the firmware's own, so this tests the contract rather than the code.
# ST-010's page fade: the decay of the page you are reading, its floor, and
# that the floor stays legible on every palette -- including the low-contrast
# one, which cannot afford to fade at all.
run page_fade \
  c++ -std=c++17 -Isrc -o "$OUT/page_fade" tests/page_fade_test.cpp

run grayscale_preview \
  c++ -std=c++17 -Isrc -o "$OUT/grayscale_preview" tests/grayscale_preview_test.cpp

run wifi_host \
  c++ -std=c++20 -Isrc -DCROSSPOINT_SIM_HOST_WIFI=1 -o "$OUT/wifi_host" tests/wifi_host_test.cpp

run http_dispatch \
  c++ -std=c++20 -Isrc -DCROSSPOINT_SIM_HOST_HTTP=1 -o "$OUT/http_dispatch" tests/http_dispatch_test.cpp

run restart_semantics \
  c++ -std=c++20 -Isrc -o "$OUT/restart_semantics" tests/restart_semantics_test.cpp src/SimulatorLifecycle.cpp

run task_registry \
  c++ -std=c++20 -Isrc -o "$OUT/task_registry" tests/task_registry_test.cpp

run text_entry_enter \
  c++ -std=c++20 -Isrc -o "$OUT/text_entry_enter" tests/text_entry_enter_test.cpp

run host_keyboard \
  c++ -std=c++20 -Isrc -o "$OUT/host_keyboard" tests/host_keyboard_test.cpp

run readaloud_lines \
  c++ -std=c++20 -Isrc -o "$OUT/readaloud_lines" tests/readaloud_lines_test.cpp

run read_aloud_channel \
  c++ -std=c++20 -Isrc -o "$OUT/read_aloud_channel" tests/read_aloud_channel_test.cpp

run read_aloud_core \
  c++ -std=c++17 -Iios -o "$OUT/read_aloud_core" tests/read_aloud_core_test.cpp ios/ReadAloudCore.cpp

run reboot_resets \
  c++ -std=c++20 -Isrc -o "$OUT/reboot_resets" tests/reboot_resets_test.cpp

run semphr_reboot \
  c++ -std=c++20 -Isrc -o "$OUT/semphr_reboot" tests/semphr_reboot_test.cpp

run heap_budget \
  c++ -std=c++20 -Isrc -o "$OUT/heap_budget" tests/heap_budget_test.cpp src/SimulatorHeap.cpp

run dispatch_signal \
  c++ -std=c++20 -o "$OUT/dispatch_signal" tests/dispatch_signal_test.cpp

# The desktop's settings file. Every failure mode is a dial that silently does
# not apply -- a bad line reverting every OTHER dial, a missing key answering 0
# where 0 is a real choice (grain off, fade off), or the shipped template not
# parsing to the defaults it documents.
run sim_settings_file \
  c++ -std=c++17 -Isrc -o "$OUT/sim_settings_file" tests/sim_settings_file_test.cpp

# The grain field. Every failure mode is a wrong PICTURE -- a field that only
# darkens is the difference between texture and the page-flash bug class, "off"
# that is nearly-off instead of bit-exact is a silent change to every install
# that turned it off, and a cell that regressed to one pixel drops below acuity
# and renders as the flat fill the feature exists to replace. None of that
# compiles differently.
run phosphor_grain \
  c++ -std=c++17 -Isrc -o "$OUT/phosphor_grain" tests/phosphor_grain_test.cpp

# S-001's four remaining reversals. Every failure mode there is a stub quietly
# answering the OPPOSITE of the hardware, which no compile and no screenshot can
# see -- and the panic latch in particular has to be one-shot or the desktop
# reboot loops back into the crash screen forever.
run device_truth \
  c++ -std=c++20 -Isrc -o "$OUT/device_truth" tests/device_truth_test.cpp

# Known-answer vectors for the mbedtls SHA-256 shim. It was a 32-byte XOR fold
# that returned success, and nothing but a published vector can see that: the
# signature, the output length and the determinism are all indistinguishable
# from a real digest. macOS uses CommonCrypto (no extra flag); Linux uses
# OpenSSL, which the sample ini already links for the MD5 path.
# An empty array expands to an unbound-variable error under `set -u` on the
# bash 3.2 that ships with macOS, so the two platforms get two invocations
# rather than one with a maybe-empty flag list.
if [[ "$(uname -s)" == "Linux" ]]; then
  run sha256 \
    c++ -std=c++20 -Isrc -o "$OUT/sha256" tests/sha256_test.cpp -lcrypto
else
  run sha256 \
    c++ -std=c++20 -Isrc -o "$OUT/sha256" tests/sha256_test.cpp
fi

# The one Python test. tools/gen_cmake_sources.py writes the single file that
# tells the iOS build which firmware sources to compile, and it used to be able
# to write an empty one and exit 0. Builds its own throwaway trees, so it needs
# no firmware checkout and never touches the real one.
run_direct gen_cmake_sources \
  python3 tests/gen_cmake_sources_test.py

# The two keyboard chips must take their colours from one definition. Source
# level on purpose -- the real check needs UIKit and a booted simulator, and a
# hardcoded colour is invisible to every other test here.
run_direct chip_tint_source \
  python3 tests/chip_tint_source_test.py

# build_identity needs the firmware's include set. Skip rather than fail when
# there is no firmware checkout to point at -- that is a missing precondition,
# not a broken test, and reporting it as FAIL would train people to ignore reds.
if FW_FLAGS=$(python3 tools/fw_include_flags.py 2>/dev/null) && [[ -n "$FW_FLAGS" ]]; then
  # shellcheck disable=SC2086
  run build_identity \
    c++ -std=c++17 -DSIMULATOR -DSIMULATOR_DEVICE_X3 -DCROSSPOINT_RENDER_SCALE=2 -Isrc $FW_FLAGS \
        -o "$OUT/build_identity" tests/build_identity_test.cpp src/SimulatorBuildIdentity.cpp
else
  printf '%-22s %s\n' "build_identity" "SKIP (no firmware include set; run a pio build first)"
  skipped=$((skipped + 1))
fi

echo
if [[ $fail -eq 0 ]]; then
  echo "$pass passed, $skipped skipped"
  exit 0
fi
echo "$pass passed, $fail FAILED, $skipped skipped"
printf '  %s\n' "${failed_names[@]}"
exit 1
