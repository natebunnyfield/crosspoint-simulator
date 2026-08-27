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

# zen_gesture retired 2026-08-22: the three-finger toggle is a native
# UITapGestureRecognizer now (owner: "be sure to swap 3 finger tap to apple";
# ios/CrossPointZenRecognizers.mm), so the SDL detector and its test are
# archived beside their old paths.

# The zen deliberate TAP -- the one gesture left on the SDL classifier since
# every gesture that moves became a native UIKit recognizer (owner 2026-08-22
# "let's use apple for swiping instead"; ios/CrossPointZenRecognizers.mm).
# Pins the tap gates and that the classifier answers None for all motion and
# all multi-finger taps, which is half of the no-double-fire argument.
run zen_verbs \
  c++ -std=c++17 -Iios -o "$OUT/zen_verbs" tests/zen_verbs_test.cpp

# The ONE-FINGER HOLD: two thresholds (0.75 s select, 5 s zen toggle) and three
# outcomes on a single gesture, after the owner's 2026-08-27 ruling that the
# select fires on the LIFT so one hold can never fire both. Exists for exactly
# the reason text_entry_enter below does -- both inversions of a two-way
# routing rule are SILENT. A select that stops firing reads as a gesture the
# phone did not deliver; a select that fires alongside the toggle reads as the
# toggle misfiring; and neither can be driven off-device, since UIKit
# recognizers live above SDL where no script and no simctl can reach. Sweeps
# both boundaries from either side, a cancelled touch, a second finger, and
# that the tracker comes back clean for the next hold (a sticky poison would
# mean select never fires again, with nothing to say why).
run zen_hold \
  c++ -std=c++17 -Iios -o "$OUT/zen_hold" tests/zen_hold_test.cpp

# The page-tap candidate's arm/spoil lifecycle (2026-08-21 audit findings #1
# and #3): no exit path may leave it latched, and a second concurrent finger
# spoils it. Pure because the SDL event watch it was extracted from cannot be
# compiled off-device, and both failure modes are silent.
run tap_candidate \
  c++ -std=c++17 -Iios -o "$OUT/tap_candidate" tests/tap_candidate_test.cpp

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

# The light page's historical-ink picker core (2026-08-22 doctrine: light mode
# is paper and ink; dark keeps the gun mixer). Every ink x paper pair floor
# swept at 7:1, the Beer-Lambert dilution ramp pinned monotone and byte-exact
# at both ends, and the default pinned to the shipped 2D2D2D-on-FBFBF9 -- all
# wrong-COLOR failure modes no other test can see. -Iios as well: it also pins
# that makePaletteOn preserves every offered paper byte-for-byte as the pad's
# field, which is the color half of the panel/sheet seam.
# -O1 is not a style choice: the ink x paper x dial sweeps make this the
# suite's single biggest cost (~6.4 s at -O0 against 0.15 s to compile it).
run light_ink \
  c++ -std=c++17 -O1 -Isrc -Iios -o "$OUT/light_ink" tests/light_ink_test.cpp

# The AA plane decode. Dark mode paints only full ink in the base pass, so every
# glyph edge arrives base-WHITE and flagged -- and the decode used to discard
# exactly those, leaving dark-mode text with no antialiasing at all. The masks
# are the firmware's own, so this tests the contract rather than the code.
# ST-010's page fade: the decay of the page you are reading, its floor, and
# that the floor stays legible on every palette -- including the low-contrast
# one, which cannot afford to fade at all.
run page_fade \
  c++ -std=c++17 -Isrc -o "$OUT/page_fade" tests/page_fade_test.cpp

# When a phosphor trail stops being able to change a pixel -- the rule that ends
# the self-driving present loop. Both failure modes are silent: one present too
# early and a visible ghost pops off the glass, one trail too late and a core
# burns redrawing one picture. It is also the case where the desktop canary is
# actively MISLEADING: SDL's software blitter truncates its blends, so the trail
# dies earlier there than on a rounding GPU backend, and a model tuned against a
# desktop capture ships a ghost to the phone. The test runs both arithmetics
# against the bound.
run trail_lifetime \
  c++ -std=c++17 -Isrc -o "$OUT/trail_lifetime" tests/trail_lifetime_test.cpp

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

run readaloud_geometry \
  c++ -std=c++20 -Isrc -o "$OUT/readaloud_geometry" tests/readaloud_geometry_test.cpp

run spoken_page_text \
  c++ -std=c++20 -Isrc -o "$OUT/spoken_page_text" tests/spoken_page_text_test.cpp

# Whether the Speak Screen exposure has to be rebuilt (src/ReadAloudExposure.h).
# The level check that runs every frame and re-pushes the held page whenever
# what assistive technology can reach stops matching what it should be. It is a
# pure header for the same reason the two above are: ios/CrossPointAccessibility
# .mm compiles only on a Mac, cannot be single-stepped on a phone, and every way
# this predicate can be wrong is SILENT -- the page is captured, the text is
# right, nothing logs, and the symptom is iOS saying "No speakable content could
# be found on the screen" over a page that is on the glass. Three of its terms
# were missing (a page published before the container existed, a container lost
# after a good build, a page view retained by a detached host); each is marked
# REGRESSION in the test and each fails against the boolean this replaced.
run readaloud_exposure \
  c++ -std=c++20 -Isrc -o "$OUT/readaloud_exposure" tests/readaloud_exposure_test.cpp

run read_aloud_channel \
  c++ -std=c++20 -Isrc -o "$OUT/read_aloud_channel" tests/read_aloud_channel_test.cpp

# The shake -> font-family channel (consume-once, bursts collapse, reboot
# drops a pending step). Pure for the same reason ReadAloudChannel is.
run font_family_step \
  c++ -std=c++17 -Isrc -o "$OUT/font_family_step" tests/font_family_step_channel_test.cpp

run read_aloud_core \
  c++ -std=c++17 -Iios -o "$OUT/read_aloud_core" tests/read_aloud_core_test.cpp ios/ReadAloudCore.cpp

# S-023, and the one link of the Speak Screen chain no C++ test here can reach:
# the iOS adapter's own boot path. Its reboot is a longjmp, so every static in
# ios/CrossPointReadAloud.mm survives while the channel flag they mirror is
# re-seeded -- and the pref-derived seed in begin() plus a surviving edge cache
# in perFrame left capture OFF for the rest of the process. The owner's
# a11y.log, 2026-08-26: healthy at t=112, `page=0B rects=0 fb=0B` from t=3738.
# Source-level because the live check needs UIKit, a booted phone and a reboot
# mid-run; it fails on all three of its properties against the pre-fix file.
run_direct readaloud_reboot_seed \
  python3 tests/readaloud_reboot_seed_test.py

# SimulatorLifecycle.cpp is compiled in so the millis-rebase registrar it
# registers is the REAL one the test's runAll() exercises (same trick as
# restart_semantics below).
run reboot_resets \
  c++ -std=c++20 -Isrc -o "$OUT/reboot_resets" tests/reboot_resets_test.cpp src/SimulatorLifecycle.cpp

run semphr_reboot \
  c++ -std=c++20 -Isrc -o "$OUT/semphr_reboot" tests/semphr_reboot_test.cpp

run heap_budget \
  c++ -std=c++20 -Isrc -o "$OUT/heap_budget" tests/heap_budget_test.cpp src/SimulatorHeap.cpp

# The web server's dispatch hand-off must signal the parked worker from a SCOPE
# GUARD (src/WebServer.cpp, handleClient()). Source-level since 2026-08-23: the
# C++ test this replaces included ZERO repo headers and re-implemented both the
# bug and the fix locally, so deleting the guard from the shipping code left it
# green -- and its assertions were bare assert(), which -DNDEBUG compiles away.
# The archived original sits beside its old path.
run_direct dispatch_signal \
  python3 tests/dispatch_signal_test.py

# The desktop's settings file. Every failure mode is a dial that silently does
# not apply -- a bad line reverting every OTHER dial, a missing key answering 0
# where 0 is a real choice (grain off, fade off), or the shipped template not
# parsing to the defaults it documents.
run sim_settings_file \
  c++ -std=c++17 -Isrc -o "$OUT/sim_settings_file" tests/sim_settings_file_test.cpp

# The phosphor mixer's math. Every failure mode is a wrong color or a wrong
# decay: a blend averaged in sRGB bytes instead of linear light darkens every
# mixture, a premix accepted as an ingredient mixes a mixture, and a tail that
# points at the wrong component makes the afterglow die toward the wrong color.
run phosphor_mix \
  c++ -std=c++17 -Isrc -o "$OUT/phosphor_mix" tests/phosphor_mix_test.cpp

# The four-gun mixer's CSV codec. Weights are POSITIONAL, never matched by
# preset: two guns may share a phosphor, and the by-preset lookup this
# replaces collapsed both onto one stored pair (the duplicated-guns bug,
# 2026-08-22). Every failure mode is a silently rewritten recipe.
run gun_mix_csv \
  c++ -std=c++17 -Isrc -o "$OUT/gun_mix_csv" tests/gun_mix_csv_test.cpp

# The grain field. Every failure mode is a wrong PICTURE -- a field that only
# darkens is the difference between texture and the page-flash bug class, "off"
# that is nearly-off instead of bit-exact is a silent change to every install
# that turned it off, and a cell that regressed to one pixel drops below acuity
# and renders as the flat fill the feature exists to replace. None of that
# compiles differently.
run phosphor_grain \
  c++ -std=c++17 -Isrc -o "$OUT/phosphor_grain" tests/phosphor_grain_test.cpp

# WHICH of those fields composites, and the mutual exclusion that makes every
# budget above and below it true. Each surface pass clamps itself to a budget
# computed on the assumption that IT IS THE ONLY PASS, so two fields over one
# page multiply and the product can sit under the 7:1 floor that seven separate
# tests each prove individually. That rule was five lines in the middle of a
# 4,800-line present function with no coverage at all until 2026-08-23; it is
# src/FieldSelection.h now, and this sweeps the whole dial space for it. Also
# pins the two budget SHARES, which were bare literals at three sites in
# HalDisplay.cpp and four more in this directory -- so the app and its tests
# could disagree with no symptom at all.
run field_selection \
  c++ -std=c++17 -Isrc -Itests -o "$OUT/field_selection" tests/field_selection_test.cpp

# Known-answer vectors for the host MD5 shim, RFC 1321's own test suite. Exactly
# the argument sha256 above is here for, never applied to MD5 until 2026-08-23:
# src/MD5Builder.h is a dispatcher over TWO implementations that must agree
# (CommonCrypto on macOS, OpenSSL on Linux) and neither had a single vector. A
# divergence is not a crash, it is the same book hashing two ways on two
# machines -- which the file-transfer and font-download paths compare.
run md5 \
  c++ -std=c++17 -Isrc -Itests -o "$OUT/md5" tests/md5_test.cpp

# The 2026-08-22 doctrine split: letterpress is the light page's surface,
# scanlines the dark one's. Both pure headers whose every failure mode is a
# wrong picture -- same reason phosphor_grain has a test.
run letterpress \
  c++ -std=c++17 -Isrc -o "$OUT/letterpress" tests/letterpress_test.cpp

run scanlines \
  c++ -std=c++17 -Isrc -o "$OUT/scanlines" tests/scanlines_test.cpp

# The 2026-08-23 roadmap items, all three pure headers with the same property:
# every failure mode is a wrong picture nobody is looking at when it happens.
#
# show_through covers the paper item (roadmap 1a) and the per-stock opacity it
# rides on -- a mirror in the wrong coordinate space, a downsample that samples
# the dither instead of averaging it (ST-008 through the back door), and a
# fourth consumer of the paper budget that does not declare its share.
run show_through \
  c++ -std=c++17 -Isrc -o "$OUT/show_through" tests/show_through_test.cpp

# corner_defocus covers the dark item (D3), and the claim only a test can make:
# a defocused corner must lose raster CONTRAST while losing no LIGHT. A field
# that forgets to divide the widening out of its own normalization lifts the
# corners instead, which is the page-flash bug class wearing a physics
# argument. It also pins the ellipse -- an isotropic model passes every other
# check here and reads as "the corner text is worse".
run corner_defocus \
  c++ -std=c++17 -O1 -Isrc -o "$OUT/corner_defocus" tests/corner_defocus_test.cpp

# power_off_collapse covers the sleep animation (D8). Its first frame must be
# the sleep screen byte for byte -- anything else is a flash at sleep -- and its
# last must be exactly dark, or a lit dot sits on the glass all night.
run power_off_collapse \
  c++ -std=c++17 -Isrc -o "$OUT/power_off_collapse" \
  tests/power_off_collapse_test.cpp

# power_on_warm_up covers the other half of the same switch. Its LAST frame must
# be the page byte for byte, or every wake leaves a permanent dim; and its
# settle phase must never ask for more light than nominal, because that phase
# composites over the finished page as a darken-only MOD and an additive pass
# over a dark ground is the page-flash bug class.
run power_on_warm_up \
  c++ -std=c++17 -Isrc -o "$OUT/power_on_warm_up" \
  tests/power_on_warm_up_test.cpp

# Chain and laid lines for a laid paper stock (2026-08-22 paper research). At
# ~1.9 px the laid pitch is ST-008 territory, so this pins the box-integrated
# no-beat case the way scanlines_test pins its 2.39 px pitch, plus per-page
# determinism, darken-only, and the floor through the sheet budget split.
run laid_structure \
  c++ -std=c++17 -Isrc -o "$OUT/laid_structure" tests/laid_structure_test.cpp

# The paper the letterpress prints on: its marks, and its identity. Two failure
# classes no compiler can see. A defect that LIFTS is the page-flash bug class;
# a mark that outlives the paper's REMAINING budget (the tooth already spent
# against it, and its clamp is conditional) puts a reading page under 7:1; and a
# page seed that still carries the launch seed renders perfectly while failing
# the one claim the feature exists for -- the same page is the same sheet.
run paper_defects \
  c++ -std=c++17 -O1 -Isrc -o "$OUT/paper_defects" tests/paper_defects_test.cpp

# WHICH sheet each of those pages is -- and, since 2026-08-24, each system
# screen too. A seed that folds to 0 reads as "nothing published" and silently
# restores the per-launch sheet; a screen seed that collides with a page seed
# prints a menu on a leaf of the open book; and the FNV-1a behind a screen's key
# has two copies that cannot share a header (the firmware is not linked against
# this repo on device), so this reads the firmware's copy as text where a
# sibling checkout exists. Run from the repo root, like pad_palette above.
run sheet_identity \
  c++ -std=c++17 -Isrc -o "$OUT/sheet_identity" tests/sheet_identity_test.cpp

# THE DIAL TABLE, and the divergence nothing could catch before it. Adding one
# surface effect used to touch nine plumbing sites, three of which were parallel
# lists of the same values kept in sync by hand -- and on 2026-08-23 two of them
# drifted in a single day (the beam at 67 ms against the app's 55, and three of
# the grain's four arguments). This reads the shipped ios/ sources as text and
# fails when what CROSSPOINT_SIM_AS_SHIPPED seeds is not what the app pushes.
# Reads from the repo root, same as pad_palette and panel_palette above.
run dial_table \
  c++ -std=c++17 -Isrc -o "$OUT/dial_table" tests/dial_table_test.cpp

# THE FROZEN PAGE. Owner ruling 2026-08-24 took the paper and CRT controls out
# of the app and froze both appearances -- Sanguine on India for light, and for
# dark the four-gun blend from his own screenshot of the mixer. src/FrozenPage.h
# states only the INPUTS and derives every tone from the pure models, which is
# the right way round but means nothing in the source says what the page looks
# like: a transposed gun or a wrong weight compiles perfectly, and there is no
# longer any control on the phone that would show it. This is the third party
# that compares the derivation against the numbers he read off the mixer's own
# readout (dark CFD4CC on 171B1B, fade 1095 ms), pins the light page as
# something OTHER than that blend's light rendition -- confusing the two is the
# likeliest way to freeze the wrong thing -- and re-derives the 7:1 contrast of
# both pairs independently of the clamp that chose them. Compiles ios/ directly,
# which works because FrozenPage.h is plain C++ over src/ models.
run frozen_page \
  c++ -std=c++17 -Isrc -Iios -o "$OUT/frozen_page" tests/frozen_page_test.cpp

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

# THE SEED-FONT GATE'S OWN INSTRUMENT. tools/validate_seed_fonts.py is what
# refuses a .cpfont tree whose files do not render the size their filenames
# claim (B-039: InknutJunicode's L slot shipped at half size on 2026-08-26 and
# loaded with no error anywhere -- crosspoint-reader/docs/inknut-l-slot-2026-08-26.md).
# It runs at iOS configure time and again in ios/testflight.sh, on
# build/seedfonts, which is GITIGNORED and different on every machine -- so a
# test over the real tree would prove nothing about anyone else's. This one
# synthesises header-only fixtures in a temp directory and asserts, for each of
# the eight checks, that the planted fault is rejected AND that the same tree
# without it passes. A gate that has quietly become a no-op prints OK and
# everyone downstream believes it; that is not hypothetical here, the deploy's
# device-profile guard passed the broken build it was written for.
run_direct validate_seed_fonts \
  python3 tests/validate_seed_fonts_test.py

# The two keyboard chips must take their colours from one definition. Source
# level on purpose -- the real check needs UIKit and a booted simulator, and a
# hardcoded colour is invisible to every other test here.
run_direct chip_tint_source \
  python3 tests/chip_tint_source_test.py

# WHERE EACH POLARITY'S TONES COME FROM (owner P1 2026-08-23, "ink is not being
# picked up"). Two tests, because the bug had two halves and neither could see
# the other: the C++ one drives the shipped decision functions and compares
# BYTES for both appearances across load, switch and both editor orders, while
# the Python one pins that the light-mode ink picker and the dark-mode gun mixer
# still write only their own polarity's fields. chip_tint_source above passed
# through this entire bug -- it asserts a delegation chain and never a tone.
run panel_source \
  c++ -std=c++17 -Isrc -Iios -o "$OUT/panel_source" tests/panel_source_test.cpp

run_direct panel_source_owners \
  python3 tests/panel_source_test.py

# THE READING LEDGER (docs/reading-experiments.md). Three tests for one feature,
# because it has three independent silent failure modes and no visible ones --
# nothing renders differently when any of this is wrong, and the cost of a
# mistake is a conclusion about which font to read in that was never true.
#
# reading_log covers the MODEL: the config id (a collision merges two arms into
# one, a spurious change shatters a comparison into singletons -- and both look
# like data), the JSON escaping (a quote in an SD card font family name makes a
# line no parser accepts, and the loss looks exactly like "he did not read much
# with that font"), the retention bound, and the append/rotate round trip. It
# also reads the FIRMWARE's copy of the mirrored POD as text where a sibling
# checkout exists, since the two cannot share a header and a field reordered on
# one side would compile cleanly on both. It prints the measured cost of one
# appended line beside the 30-130 ms a page turn already costs.
run reading_log \
  c++ -std=c++17 -Isrc -o "$OUT/reading_log" tests/reading_log_test.cpp

# reading_arm covers PHASE 2's assignment, which nothing calls yet. Tested
# early on purpose: an assignment that is not balanced, not deterministic, or
# not re-derivable from the seed in the log produces a clean-looking dataset and
# a wrong answer, and by the time there is enough data to notice, the data is
# what there is. The properties asserted there ARE the design.
run reading_arm \
  c++ -std=c++17 -Isrc -o "$OUT/reading_arm" tests/reading_arm_test.cpp

# reading_report covers the OUTCOME COMPUTATION, which lives offline in
# tools/reading_report.py because an outcome definition baked into the device is
# one that cannot be revised. Its central case is the one that would otherwise
# be found by believing a result: a log where the BOOKS differ enormously and
# the arms do not differ at all must not produce a significant arm effect.
run_direct reading_report \
  python3 tests/reading_report_test.py

# build_identity needs the firmware's include set. Skip rather than fail when
# there is no firmware checkout to point at -- that is a missing precondition,
# not a broken test, and reporting it as FAIL would train people to ignore reds.
if FW_FLAGS=$(python3 tools/fw_include_flags.py 2>/dev/null) && [[ -n "$FW_FLAGS" ]]; then
  # shellcheck disable=SC2086
  run build_identity \
    c++ -std=c++17 -DSIMULATOR -DSIMULATOR_DEVICE_X3 -DCROSSPOINT_RENDER_SCALE=2 -Isrc $FW_FLAGS \
        -o "$OUT/build_identity" tests/build_identity_test.cpp src/SimulatorBuildIdentity.cpp

  # Update Library's compare logic (firmware src/network/LibrarySyncPlan.h).
  # Pure header, but it lives in the firmware repo, so it rides the same
  # include-set guard as build_identity. Every wrong verdict is silent on
  # device: a skipped update, a book re-downloaded forever, or a manifest
  # filename escaping /books/.
  # shellcheck disable=SC2086
  run library_sync_plan \
    c++ -std=c++17 -Isrc $FW_FLAGS \
        -o "$OUT/library_sync_plan" tests/library_sync_plan_test.cpp

  # The CPZ1 container the HAL's file layer opens transparently. Rides the same
  # guard because it decodes with the firmware's miniz (InflateStream), and it
  # compiles those two TUs rather than stubbing them: a stub would prove the
  # container's arithmetic and nothing about the decoder the app actually runs.
  # -Wno-deprecated silences clang's note about compiling miniz_impl.c in C++
  # mode, which is how every other build here compiles it too.
  FW_DIR=$(printf '%s\n' $FW_FLAGS | sed -n 's|^-I\(.*\)/lib/miniz/src$|\1|p' | head -n 1)
  if [[ -n "$FW_DIR" ]]; then
    # shellcheck disable=SC2086
    run cpz_container \
      c++ -std=c++17 -Wno-deprecated -Isrc -DCPZ_REPO_ROOT="\"$REPO\"" $FW_FLAGS \
          -o "$OUT/cpz_container" tests/cpz_container_test.cpp \
          "$FW_DIR/lib/miniz/src/InflateStream.cpp" \
          "$FW_DIR/lib/Memory/BuildScratch.cpp" \
          "$FW_DIR/lib/miniz/src/miniz_impl.c"
  else
    printf '%-22s %s\n' "cpz_container" "SKIP (no firmware miniz include dir)"
    skipped=$((skipped + 1))
  fi
else
  printf '%-22s %s\n' "build_identity" "SKIP (no firmware include set; run a pio build first)"
  printf '%-22s %s\n' "library_sync_plan" "SKIP (no firmware include set; run a pio build first)"
  printf '%-22s %s\n' "cpz_container" "SKIP (no firmware include set; run a pio build first)"
  skipped=$((skipped + 3))
fi

echo
if [[ $fail -eq 0 ]]; then
  echo "$pass passed, $skipped skipped"
  exit 0
fi
echo "$pass passed, $fail FAILED, $skipped skipped"
printf '  %s\n' "${failed_names[@]}"
exit 1
