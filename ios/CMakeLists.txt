# iOS app target: the peripheral-impersonator harness plus the real firmware.
#
# main() comes from the firmware side (src/simulator_main.cpp, inside
# crosspoint_core); this target supplies only the gesture harness that
# simulator_main calls into. Rendering belongs to HalDisplay, exactly as on
# desktop -- the harness draws nothing.

set(CROSSPOINT_IOS_BUNDLE_ID "com.natebunnyfield.crosspoint.x3" CACHE STRING
  "iOS bundle identifier")
set(CROSSPOINT_IOS_TEAM_ID "" CACHE STRING
  "Apple Developer Team ID. Required for device builds; leave empty for the Simulator.")

# Version and build number, driven by ios/testflight.sh.
#
# CFBundleVersion must be unique for a given marketing version, so every upload
# needs a new one. TestFlight's daily upload cap (error 90382) is also scoped per
# marketing version, so the answer to hitting it is bumping the marketing
# version, not waiting for the next day.
set(CROSSPOINT_IOS_MARKETING_VERSION "0.1.0" CACHE STRING
  "CFBundleShortVersionString")
set(CROSSPOINT_IOS_BUILD_NUMBER "1" CACHE STRING
  "CFBundleVersion; must be unique per marketing version")

configure_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/Info.plist.in
  ${CMAKE_CURRENT_BINARY_DIR}/Info.plist
  @ONLY)

# The asset catalog carries the app icon. TestFlight validation rejects an
# upload without one, so it is part of the target rather than an afterthought.
set(CROSSPOINT_ASSETS ${CMAKE_CURRENT_SOURCE_DIR}/Assets.xcassets)
set_source_files_properties(${CROSSPOINT_ASSETS} PROPERTIES
  MACOSX_PACKAGE_LOCATION Resources)

# Settings > CrossPoint X3. A .bundle is just a directory, and the only file in
# it is Root.plist, so it goes in as a resource at that path rather than needing
# a bundle target of its own.
set(CROSSPOINT_SETTINGS_BUNDLE ${CMAKE_CURRENT_SOURCE_DIR}/Settings.bundle/Root.plist)
set_source_files_properties(${CROSSPOINT_SETTINGS_BUNDLE} PROPERTIES
  MACOSX_PACKAGE_LOCATION "Resources/Settings.bundle")

add_executable(CrossPointX3 MACOSX_BUNDLE
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointIOSShim.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointAppearance.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointPrefs.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointWiFi.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointHttp.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointScreen.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointReadAloud.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointAccessibility.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/PadCore.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/ReadAloudCore.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointPageTextInput.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointKeyboardBar.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointPaletteMixer.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointLightInkPicker.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointZenRecognizers.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointBookImport.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointDiagLog.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointFsPrep.cpp
  ${CROSSPOINT_SETTINGS_BUNDLE}
  ${CROSSPOINT_ASSETS})

# The Objective-C++ translation units: the live-appearance probe
# (CrossPointAppearance.h explains why SDL's cached theme is not usable) and the
# iOS-native preferences behind Settings.bundle. ARC is set per-file rather than
# on the target because everything else here is plain C++, where the flag is
# meaningless. UIKit is named explicitly rather than leaned on as a transitive
# SDL3 dependency -- this link requirement is these files' own, and it should
# not break if SDL rearranges its interface libraries.
set_source_files_properties(
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointAppearance.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointPrefs.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointWiFi.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointHttp.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointScreen.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointReadAloud.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointAccessibility.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointPageTextInput.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointKeyboardBar.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointPaletteMixer.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointLightInkPicker.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointZenRecognizers.mm
  ${CMAKE_CURRENT_SOURCE_DIR}/CrossPointBookImport.mm
  PROPERTIES COMPILE_FLAGS "-fobjc-arc")

# Optional bundled font families. Point this at a build-sd-fonts.py output
# directory (one subdirectory per family, .cpfont files inside) and each family
# ships inside the app under Resources/SeedFonts/<Family>/. At launch,
# CrossPointFsPrep copies them into the emulated SD card's visible "fonts/"
# root, so the phone gets font updates with the app instead of by hand through
# the Files app. Globbed at configure time — CI configures fresh every run, so
# a stale glob only affects incremental local builds.
# ONE source of truth for the supersampling factor: it becomes the firmware
# define AND selects which hi-res seed-font tier gets bundled. Setting it in one
# place only is exactly how a scale-3 build shipped carrying 2x fonts.
#
# 2 since 2026-08-23 (owner: "drop 3x support for now"). The number is the
# CEILING, so lowering it does four things at once and that is the point:
# all.h's `#if CROSSPOINT_RENDER_SCALE >= 3` block stops compiling the 3x
# builtin tables, main.cpp stops registering them, the seed loop below stops
# bundling `<family>/3x/`, and CrossPointFsPrep stops looking for that tier on
# the card. Nothing is deleted from disk or from the engine -- the 3x seed
# trees and `build-sd-fonts.py --scale 3` are untouched, so putting 3 back
# here is the whole re-enable. docs/ios-render-scale.md carries the checklist.
set(CROSSPOINT_IOS_RENDER_SCALE 2 CACHE STRING "Supersampling factor for the iOS app")

set(CROSSPOINT_IOS_SEED_FONTS_DIR "" CACHE PATH
  "Directory of .cpfont font families to bundle and seed at launch")

# Ship the seeded fonts BLOCK-COMPRESSED (owner 2026-08-23: "compress fonts in
# ios app").
#
# `.cpfont` stores its 2-bit glyph bitmaps raw -- 108 MB of the 118 MB the
# 1x+2x tiers occupy, at 2.4 bits/byte -- so the IPA's own zip squeezes them
# 3.4:1 for the download and the phone then expands them right back for the
# install. tools/compress_seed_fonts.py rewrites each file as a CPZ1 container
# and src/SimCompressedFile.h opens it transparently at the HAL's file layer,
# so the bytes stay compressed ON DISK and are inflated 32 KB at a time as the
# reader seeks. Measured on the shipped tree: 117,654,860 -> 34,837,381 bytes
# installed (0.296), against a download that grows by 1,398,702 because the
# containers no longer compress inside the zip -- 83 MB off the phone for
# 1.4 MB of download. Both figures are from docs/ios-app-size.md's 2026-08-23
# section, measured on the same zip settings for both arms.
#
# It runs HERE, at configure time, rather than being a step someone has to
# remember before a deploy: the whole class of bug this file already guards
# against is a bundle whose contents do not match what the build believes.
# ~40 s for the full tree, and skipped per file when the output is newer than
# its input, so a re-configure costs nothing.
#
# OFF is a supported build: the reader sniffs for the magic per file, so an
# uncompressed tree bundles and reads exactly as it always did. That is the
# escape hatch if a container is ever suspected, and it is what the desktop
# canary keeps exercising.
set(CROSSPOINT_IOS_COMPRESS_SEED_FONTS ON CACHE BOOL
  "Bundle seed fonts as CPZ1 block-compressed containers")

# The tree the FONTS came from, kept separate from the tree they are BUNDLED
# from: after compression those are two different directories, and every
# diagnostic below is about the source one -- that is where a family is added
# or removed.
set(_seed_source_dir "${CROSSPOINT_IOS_SEED_FONTS_DIR}")

if(CROSSPOINT_IOS_SEED_FONTS_DIR AND CROSSPOINT_IOS_COMPRESS_SEED_FONTS)
  set(_seed_cpz_dir "${CMAKE_BINARY_DIR}/seedfonts-cpz")
  message(STATUS "Seed fonts: compressing ${CROSSPOINT_IOS_SEED_FONTS_DIR} "
                 "-> ${_seed_cpz_dir}")
  execute_process(
    COMMAND ${CMAKE_COMMAND} -E env python3
            "${CMAKE_CURRENT_SOURCE_DIR}/../tools/compress_seed_fonts.py"
            --input "${CROSSPOINT_IOS_SEED_FONTS_DIR}"
            --output "${_seed_cpz_dir}"
            --max-tier ${CROSSPOINT_IOS_RENDER_SCALE}
            --quiet
    RESULT_VARIABLE _seed_cpz_rc
    OUTPUT_VARIABLE _seed_cpz_out
    ERROR_VARIABLE _seed_cpz_err)
  if(NOT _seed_cpz_rc EQUAL 0)
    # FATAL rather than a fallback to the raw tree: silently shipping 118 MB
    # where 35 MB was intended is exactly the kind of "it built fine" that the
    # gates below exist to stop.
    message(FATAL_ERROR
      "Seed fonts: compression failed (${_seed_cpz_rc}).\n"
      "${_seed_cpz_out}${_seed_cpz_err}\n"
      "Build it uncompressed with -DCROSSPOINT_IOS_COMPRESS_SEED_FONTS=OFF if "
      "that is what you want; do not leave this failing silently.")
  endif()
  string(STRIP "${_seed_cpz_out}" _seed_cpz_out)
  message(STATUS "Seed fonts: ${_seed_cpz_out}")
  set(CROSSPOINT_IOS_SEED_FONTS_DIR "${_seed_cpz_dir}")
endif()

if(CROSSPOINT_IOS_SEED_FONTS_DIR)
  file(GLOB _seed_families RELATIVE "${CROSSPOINT_IOS_SEED_FONTS_DIR}"
    "${CROSSPOINT_IOS_SEED_FONTS_DIR}/*")
  set(_seed_count 0)
  set(_seed_bundled_families "")
  foreach(_family IN LISTS _seed_families)
    set(_family_dir "${CROSSPOINT_IOS_SEED_FONTS_DIR}/${_family}")
    if(IS_DIRECTORY "${_family_dir}")
      file(GLOB _family_fonts "${_family_dir}/*.cpfont")
      if(_family_fonts)
        set_source_files_properties(${_family_fonts} PROPERTIES
          MACOSX_PACKAGE_LOCATION "Resources/SeedFonts/${_family}")
        target_sources(CrossPointX3 PRIVATE ${_family_fonts})
        list(LENGTH _family_fonts _n)
        math(EXPR _seed_count "${_seed_count} + ${_n}")
        list(APPEND _seed_bundled_families "${_family}")
        message(STATUS "Seed fonts: ${_family} (${_n} files)")
      endif()
      # Hi-res companion sets, for EVERY tier this build can render at.
      #
      # The directory name comes from the tier, not a literal "2x". Bundling
      # only 2x into a scale-3 build is worse than shipping nothing:
      # SdCardFontManager looks for `<family>/3x/` exactly, finds no companion,
      # and every reading face falls back to 1x replicated into 3x3 blocks --
      # coarser than the 2x build it replaced, and silent. A 25 MB IPA that
      # should have been ~120 MB was the only outward sign.
      #
      # EVERY TIER, NOT JUST THE CEILING, since 2026-08-15: the factor is now
      # the owner's setting, latched at launch (Settings > Page Sharpness, and
      # RenderScale.h for the mechanism), so the tier the app will ask for is
      # not known at build time. Missing the tier in use reproduces exactly the
      # silent fallback above. Tier 1 needs no companion -- at 1x the 1x face
      # already matches the framebuffer -- so the loop starts at 2.
      #
      # The ceiling is what excludes a tier, not a delete. At ceiling 2 this
      # loop simply never globs `<family>/3x/`, so the 3x trees stay in
      # build/seedfonts costing nothing in the bundle: 195,420,632 bytes
      # installed and 38,841,265 of the IPA that build 129 carried and build
      # 130 does not. Excluded rather than deleted deliberately -- rebuilding
      # a 3x tier is a ~40 minute rasterisation run, and this way re-enabling
      # is one number.
      #
      # The globs are deliberately separate rather than recursive: these files
      # must keep their own bundle subdirectory, since the companion is found by
      # the exact path `<family>/<scale>x/<same filename>`, and the hi-res cuts
      # carry the 1x filenames by design.
      # Guarded: `foreach(RANGE 2 1)` is a CMake error, not an empty loop, so a
      # ceiling of 1 would fail configure rather than simply bundle no
      # companions.
      if(CROSSPOINT_IOS_RENDER_SCALE GREATER_EQUAL 2)
      foreach(_tier RANGE 2 ${CROSSPOINT_IOS_RENDER_SCALE})
        file(GLOB _family_fonts_hr "${_family_dir}/${_tier}x/*.cpfont")
        if(_family_fonts_hr)
          set_source_files_properties(${_family_fonts_hr} PROPERTIES
            MACOSX_PACKAGE_LOCATION "Resources/SeedFonts/${_family}/${_tier}x")
          target_sources(CrossPointX3 PRIVATE ${_family_fonts_hr})
          list(LENGTH _family_fonts_hr _n2)
          math(EXPR _seed_count "${_seed_count} + ${_n2}")
          message(STATUS "Seed fonts: ${_family}/${_tier}x (${_n2} files)")
        else()
          message(WARNING "Seed fonts: ${_family} has no ${_tier}x set -- "
                          "it will render 1x-replicated when the owner picks that scale")
        endif()
      endforeach()
      endif()
    endif()
  endforeach()
  if(_seed_count EQUAL 0)
    message(FATAL_ERROR
      "CROSSPOINT_IOS_SEED_FONTS_DIR=${_seed_source_dir} "
      "contains no <Family>/*.cpfont files — wrong path, or the font build "
      "did not run.")
  endif()

  # --- Installed-family gate -----------------------------------------------
  #
  # A bundled family that sd-fonts.yaml's `installed_families` does not name is
  # DEAD WEIGHT, not a bonus: every reading surface filters through
  # readingfonts::offeredForReading(), and the editor faces resolve from the
  # compiled-in tables without ever consulting the card
  # (lib/EpdFont/../EditorFonts.h). Nothing in the app can select it, and
  # nothing said so — the seed list was hand-typed in two places (the CI
  # `seed_fonts` input and whatever local tree CROSSPOINT_SEED_FONTS_DIR points
  # at) with no cross-check. Build 126 shipped iA Writer Duo, Mono and Quattro
  # that way: 16,163,105 compressed bytes of the IPA (18.2 %) and 73,935,812
  # installed, all unreachable. See docs/ios-app-size.md A1.
  #
  # Same shape as the define-parity gate below: mechanical, at configure time,
  # before a single TU compiles.
  set(_sd_fonts_yaml "${CROSSPOINT_FIRMWARE_DIR}/lib/EpdFont/scripts/sd-fonts.yaml")
  if(NOT EXISTS "${_sd_fonts_yaml}")
    message(FATAL_ERROR
      "Seed fonts were requested but ${_sd_fonts_yaml} is missing, so the "
      "bundled families cannot be checked against installed_families. Point "
      "CROSSPOINT_FIRMWARE_DIR at a firmware checkout.")
  endif()
  file(STRINGS "${_sd_fonts_yaml}" _sd_fonts_lines)
  set(_installed_families "")
  set(_in_installed FALSE)
  foreach(_line IN LISTS _sd_fonts_lines)
    if(_line MATCHES "^installed_families:")
      set(_in_installed TRUE)
    elseif(_in_installed)
      if(_line MATCHES "^  *- +([A-Za-z0-9_]+)")
        list(APPEND _installed_families "${CMAKE_MATCH_1}")
      elseif(_line MATCHES "^[A-Za-z]")
        set(_in_installed FALSE)
      endif()
    endif()
  endforeach()
  if(NOT _installed_families)
    message(FATAL_ERROR
      "Parsed no installed_families out of ${_sd_fonts_yaml}. The key moved or "
      "its list format changed; fix this gate rather than deleting it.")
  endif()
  set(_unreachable_families "")
  foreach(_family IN LISTS _seed_bundled_families)
    if(NOT _family IN_LIST _installed_families)
      list(APPEND _unreachable_families "${_family}")
    endif()
  endforeach()
  if(_unreachable_families)
    string(REPLACE ";" ", " _unreachable_text "${_unreachable_families}")
    string(REPLACE ";" ", " _installed_text "${_installed_families}")
    message(FATAL_ERROR
      "Seed fonts: ${_unreachable_text} — bundled from "
      "${_seed_source_dir} but NOT in installed_families "
      "(${_installed_text}) in ${_sd_fonts_yaml}.\n"
      "No reading or editor surface in the app can select a family that list "
      "does not name, so this is megabytes of unreachable bundle. Remove it "
      "from the seed tree (and from the CI seed_fonts input), or, if it really "
      "should be selectable, add it to installed_families — which is an owner "
      "ruling, not a build fix.")
  endif()
  # ...and the INVERSE, which is the direction that actually bit. A family in
  # installed_families with nothing bundled is SILENT: the firmware believes it
  # is installed, every existing check passes, and the app simply does not have
  # the font. TeX Gyre Heros reached the upload step that way on 2026-08-23 --
  # built into ios/seedfonts and onto the card, but not into the tree this
  # bundle is actually copied from -- and only a hand check caught it.
  set(_unbundled_families "")
  foreach(_family IN LISTS _installed_families)
    if(NOT _family IN_LIST _seed_bundled_families)
      list(APPEND _unbundled_families "${_family}")
    endif()
  endforeach()
  if(_unbundled_families)
    string(REPLACE ";" ", " _unbundled_text "${_unbundled_families}")
    message(FATAL_ERROR
      "Seed fonts: ${_unbundled_text} — named in installed_families "
      "(${_sd_fonts_yaml}) but NOT bundled from "
      "${_seed_source_dir}.\n"
      "The firmware believes these are installed on every surface, so the app "
      "would ship believing in a font it does not carry. Build them into the "
      "seed tree at EVERY tier the app renders -- 1x and 2x since 2026-08-23, "
      "and CROSSPOINT_IOS_RENDER_SCALE above is what decides that:\n"
      "  for sc in 1 2; do build-sd-fonts.py --only <Family> --scale $sc "
      "--output-dir <seed tree>; done\n"
      "If a family is deliberately device-only, it does not belong in "
      "installed_families — that list means every surface.")
  endif()
  list(LENGTH _seed_bundled_families _n_fam)
  message(STATUS "Seed fonts: ${_n_fam} families, matching installed_families exactly")
endif()

# Default books, always bundled (small public-domain testers checked into
# ios/seedbooks/). CrossPointFsPrep copies each into books/ ONLY when absent —
# books are user data, so unlike fonts they are never overwritten or pruned.
file(GLOB _seed_books "${CMAKE_CURRENT_SOURCE_DIR}/seedbooks/*.epub")
if(_seed_books)
  set_source_files_properties(${_seed_books} PROPERTIES
    MACOSX_PACKAGE_LOCATION "Resources/SeedBooks")
  target_sources(CrossPointX3 PRIVATE ${_seed_books})
  list(LENGTH _seed_books _n)
  message(STATUS "Seed books: ${_n}")
endif()

if(NOT CROSSPOINT_BUILD_FIRMWARE)
  message(FATAL_ERROR
    "The iOS app needs the firmware source set. Configure with "
    "-DCROSSPOINT_BUILD_FIRMWARE=ON -DCROSSPOINT_FIRMWARE_DIR=<path>.")
endif()

# NetworkExtension carries NEHotspotNetwork (SSID + signal strength); Network
# carries NWPathMonitor (connectivity). Both are CrossPointWiFi.mm's own link
# requirements and are named here rather than left to come in transitively.
# AVFoundation carries AVSpeechSynthesizer and AVAudioSession — the read-aloud
# adapter's (CrossPointReadAloud.mm) own link requirement, named for the same
# reason the two above are.
target_link_libraries(CrossPointX3 PRIVATE crosspoint_core SDL3::SDL3
  "-framework UIKit"
  "-framework Network"
  "-framework NetworkExtension"
  "-framework AVFoundation")

# The harness impersonates an X3. ON THE LIBRARY, PUBLIC -- the same trap
# CROSSPOINT_RENDER_SCALE fell into below, and it bit harder: the device macro
# was PRIVATE on CrossPointX3 for 15+ builds, so the seven harness TUs compiled
# as X3 while all 155 firmware/HAL TUs in crosspoint_core silently took
# BoardConfig.h's #else branch and built an X4.
#
# What that cost, beyond the two layers disagreeing about panel geometry
# (792x528 vs 800x480):
#   * HalClock::begin() left _available false (it only arms the clock for X3 /
#     X4 Pro), so getDateTime() failed and EVERY calendar sleep screen hit
#     SleepActivity's "no RTC available" fallback and painted the stock logo
#     screen instead. Custom fell through to the calendar and so to the same
#     stock screen. That is the "no matter what I pick, I get the logo" bug.
#   * gpio.deviceIsX3() answered false, so the X3-only differential refresh in
#     renderLastScreenSleepScreen() never ran.
#   * HalTiltSensor::begin() left _available false, contrary to ios/README.md.
# SIMULATOR itself already reaches both layers via CROSSPOINT_DEFINES.
target_compile_definitions(crosspoint_core PUBLIC SIMULATOR_DEVICE_X3)

# Native-density glyph rasterisation, ON THE LIBRARY, not the app target.
#
# 3 from 2026-08-15 to 2026-08-23, matching the @3x screens this ships to; 2
# since, per the owner ruling. Moving it is not just this number: the renderer
# is scale-generic, but every hi-res font tier must EXIST at the new scale,
# because the companion is blitted one bitmap pixel to one device pixel. A
# family with no set at the tier in use renders 1x-replicated into NxN blocks --
# coarser than the tier it replaced -- and a 2x set cannot stand in for 3x,
# since 2 does not divide 3. So a tier is only offered when seedfonts/ carries
# it AND convert-builtin-fonts.sh has emitted its built-ins.
# HalDisplay.cpp (framebuffer size) and SdCardFontManager.cpp (2x companion
# loading) live in crosspoint_core; a define on CrossPointX3 never reaches
# them, and HalDisplay.h silently defaults the scale to 1 -- which is exactly
# how TestFlight builds through 15 shipped 1x while the pbxproj showed a =2
# that only covered the seven harness TUs. PUBLIC so the harness TUs see the
# same value and the two layers cannot disagree.
# CROSSPOINT_RENDER_SCALE is now the CEILING: static allocations and which
# hi-res glyph tiers get compiled in are sized on it, while the factor actually
# rendered at is latched at launch from Settings > Page Sharpness and may be
# anything from 1 up to it. CROSSPOINT_RENDER_SCALE_RUNTIME is what turns the
# active factor from a constant into storage; without it the two are the same
# number and the setting would be silently ignored.
#
# PUBLIC on the core, never PRIVATE on the app target, for the reason the table
# at the top of this file records: a define that reaches only one target
# compiles clean and fails somewhere distant.
target_compile_definitions(crosspoint_core PUBLIC
  CROSSPOINT_RENDER_SCALE=${CROSSPOINT_IOS_RENDER_SCALE}
  CROSSPOINT_RENDER_SCALE_RUNTIME=1)

# OMIT_FONTS is NO LONGER DEFINED HERE, and the blank page it caused is why.
#
# It stripped the three non-default built-in reader sizes -- Libre Franklin
# Reader at 12, 16 and 18 pt, ~350 KB of glyph data -- on the theory that
# nothing the reader must draw depends on them. That safety argument was
# FALSE at its first bullet: CrossPointSettings.cpp getReaderFontId() snaps a
# persisted fontSize onto BUILTIN_READER_POINT_SIZES and returns the 12/16/18
# ids for those sizes; only the `default:` branch answers 14 pt. With no SD
# family selected and fontSize 18, the reader asked GfxRenderer for
# LIBREFRANKLIN_READER_18_FONT_ID, drawText's fontMap lookup missed, logged
# "Font -421869102 not found" once per string, and drew NOTHING -- an
# entirely blank page on the glass while the firmware reported successful
# page renders (found 2026-08-21; the frame's mean luma was exactly the
# paper tone, which is how "blank" was proven against "erased").
#
# This is the SECOND breakage of the same shape (the first collapsed the
# Editor Font setting until firmware 63ea6e6b moved the monospace families
# outside the guard). The define strips font DATA while src/fontIds.h keeps
# vending the ids, so nothing fails to compile and nothing warns; iOS was the
# only build defining it, so the desktop could never see the damage. ~350 KB
# in an iOS app bundle does not buy that failure mode; the firmware's
# `#ifndef OMIT_FONTS` guards stay for device builds that want them.

# Firmware-flash TUs (OTA, SD Firmware Update) are excluded from the iOS source
# set -- see cmake/CrossPointIOSExclusions.cmake. This define gates their menu
# entries and includes so nothing dangles or fails to compile without them.
#
# It used to be CROSSPOINT_NO_NETWORK, which also took Wi-Fi, File Transfer,
# font downloads and Claude with it. That was right when the iOS build had no
# radio -- WiFi.scanNetworks() returned a synthetic list and localIP() was
# hardcoded to 127.0.0.1, so File Transfer drew a QR code pointing at loopback
# (B-008). It stopped being right at 4a98ba8, which gave the target
# CrossPointWiFi.mm over NetworkExtension, in-process HTTP, Bonjour, and servers
# bound to all interfaces. Keeping the wider flag after that was suppressing
# features the app can actually run. Flashing an ESP32 partition from a phone is
# the only part that stays impossible, so the name now says only that.
target_compile_definitions(crosspoint_core PUBLIC CROSSPOINT_NO_DEVICE_FLASH=1)
# No side buttons on this chassis: the harness draws an on-screen pad instead,
# so the firmware's bracket hints label controls that do not exist -- and on a
# tablet they render inside the text column, running through the note being
# typed (owner ruling + screenshot, 2026-08-09). PUBLIC on the CORE target, per
# the one-device-macro rule: a define that reaches only the app target produces
# halves that disagree.
target_compile_definitions(crosspoint_core PUBLIC CROSSPOINT_NO_PHYSICAL_SIDE_BUTTONS=1)

# --- Define parity gate ----------------------------------------------------
#
# Every define above is deliberately on crosspoint_core PUBLIC, because a
# define that reaches only the app target reaches 7 of the 162 TUs and the
# binary's two halves then disagree in silence. That has now happened twice
# (CROSSPOINT_RENDER_SCALE, SIMULATOR_DEVICE_X3), and both times the symptom
# surfaced somewhere unrelated to the cause.
#
# So: fail the CONFIGURE if the app target ever carries a define the core does
# not. Cheap, mechanical, and it fires before a single TU is compiled — which
# a reviewer noticing the word PRIVATE demonstrably does not.
#
# If a genuinely harness-only define is ever needed (something no firmware or
# HAL TU can see by construction), add it to the allow-list below WITH the
# reason it cannot go on the library.
set(CROSSPOINT_HARNESS_ONLY_DEFINES
  # <NAME> — why the core must not see it
)
get_target_property(_app_defs CrossPointX3 COMPILE_DEFINITIONS)
get_target_property(_core_defs crosspoint_core COMPILE_DEFINITIONS)
get_target_property(_core_iface_defs crosspoint_core INTERFACE_COMPILE_DEFINITIONS)
foreach(_list _core_defs _core_iface_defs _app_defs)
  if(NOT ${_list})
    set(${_list} "")
  endif()
endforeach()
foreach(_def IN LISTS _app_defs)
  string(REGEX REPLACE "=.*$" "" _name "${_def}")
  if(_name IN_LIST CROSSPOINT_HARNESS_ONLY_DEFINES)
    continue()
  endif()
  set(_found FALSE)
  foreach(_core_def IN LISTS _core_defs _core_iface_defs)
    string(REGEX REPLACE "=.*$" "" _core_name "${_core_def}")
    if(_core_name STREQUAL _name)
      set(_found TRUE)
      break()
    endif()
  endforeach()
  if(NOT _found)
    message(FATAL_ERROR
      "'${_def}' is defined on the CrossPointX3 app target but not on "
      "crosspoint_core. The firmware and the whole HAL are in crosspoint_core, "
      "so this define reaches 7 TUs and misses ~155 of them — the binary's two "
      "halves will disagree and nothing will say so at build time.\n"
      "Move it to target_compile_definitions(crosspoint_core PUBLIC ...), or, "
      "if it truly must not reach the library, add it to "
      "CROSSPOINT_HARNESS_ONLY_DEFINES in ios/CMakeLists.txt with the reason.")
  endif()
endforeach()

set_target_properties(CrossPointX3 PROPERTIES
  MACOSX_BUNDLE_INFO_PLIST ${CMAKE_CURRENT_BINARY_DIR}/Info.plist
  XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER ${CROSSPOINT_IOS_BUNDLE_ID}
  XCODE_ATTRIBUTE_IPHONEOS_DEPLOYMENT_TARGET "26.0"
  # 1,2 = iPhone + iPad. layoutPad() branches on the idiom: phone keeps the
  # two-row pad under the panel; iPad centers the panel full-safe-height and
  # moves the pad into the side margins (owner-approved spec, ios/README.md).
  XCODE_ATTRIBUTE_TARGETED_DEVICE_FAMILY "1,2"
  XCODE_ATTRIBUTE_ENABLE_BITCODE "NO"
  # ld64's DEAD_CODE_STRIPPING defaults to NO (Ld.xcspec), so until 2026-08-22
  # the archive linked with no -dead_strip at all: the summed object
  # contributions of libcrosspoint_core.a + libSDL3.a (21.07 MB) essentially
  # equalled the binary's non-zerofill segments (20.35 MB). The glyph tables
  # are all reached from setupDisplayAndFonts(), the harness loads no plugin
  # and does no dlsym, and __objc_classlist is 240 bytes -- so there is nothing
  # here that only a runtime lookup can find. Measure __TEXT,__const before and
  # after when touching this: if it MOVES, a glyph table was stripped.
  XCODE_ATTRIBUTE_DEAD_CODE_STRIPPING "YES"
  XCODE_ATTRIBUTE_ASSETCATALOG_COMPILER_APPICON_NAME "AppIcon"
  # Required for `xcodebuild archive` to produce a DISTRIBUTABLE archive.
  #
  # CMake generates Xcode targets with SKIP_INSTALL=YES, so archive builds the
  # app but never installs it into the archive: Products/ comes out empty and
  # the archive Info.plist has no ApplicationProperties. Xcode then finds no
  # valid distribution methods and -exportArchive fails with the misleading
  # `exportOptionsPlist error for key "method" expected one {}` — an EMPTY set
  # of methods, not a bad method string.
  XCODE_ATTRIBUTE_SKIP_INSTALL "NO"
  XCODE_ATTRIBUTE_INSTALL_PATH "$(LOCAL_APPS_DIR)"
  # A release build for distribution should not carry the simulator's debug
  # assertions; the firmware is noisy enough on a 64-bit host as it is.
  XCODE_ATTRIBUTE_ONLY_ACTIVE_ARCH[variant=Release] "NO"
  # A SHIPPED BUILD MUST BE SYMBOLICATABLE. CMake's Release config carries no
  # `-g`, so Xcode wrote GCC_GENERATE_DEBUGGING_SYMBOLS = NO, no DWARF was
  # emitted, and every archive's dSYMs/ directory came out EMPTY -- which is
  # only discovered when a crash report arrives. Build 110's device crash
  # (2026-08-21) had to be diagnosed by disassembling the shipped binary and
  # reading registers, for exactly this reason.
  #
  # Debug info lives in the .o files and is collected into the dSYM at link
  # time; the shipped Mach-O keeps only the debug map in its symbol table, and
  # the product is stripped. So this is close to free in the IPA -- measured
  # rather than assumed; the numbers are in docs/ios-app-size.md.
  XCODE_ATTRIBUTE_GCC_GENERATE_DEBUGGING_SYMBOLS[variant=Release] "YES"
  XCODE_ATTRIBUTE_DEBUG_INFORMATION_FORMAT[variant=Release] "dwarf-with-dsym")

# And on the LIBRARY as well, for the same reason every cross-cutting define
# goes there: the app target is 7 TUs of 162. A dSYM built from the harness
# alone symbolicates the harness alone, and every firmware frame -- which is
# where the crashes are -- stays a bare address.
#
# STRIP_INSTALLED_PRODUCT NO is the other half, and without it the first half
# is a placebo. `xcodebuild archive` runs with DEPLOYMENT_POSTPROCESSING=YES,
# which strips every INSTALLED product -- including this static library, which
# CMake installs into UninstalledProducts/ and then links the app against by
# absolute path. Stripping an .a removes its DWARF, dsymutil finds no debug map
# entry for those objects, and the dSYM comes out covering the 18 harness TUs
# and none of the 144 firmware ones: 2.7 MB of exactly the frames that never
# crash. Measured that way once (2026-08-22) before this line was added.
set_target_properties(crosspoint_core PROPERTIES
  XCODE_ATTRIBUTE_GCC_GENERATE_DEBUGGING_SYMBOLS[variant=Release] "YES"
  XCODE_ATTRIBUTE_DEBUG_INFORMATION_FORMAT[variant=Release] "dwarf-with-dsym"
  XCODE_ATTRIBUTE_STRIP_INSTALLED_PRODUCT "NO")

if(CROSSPOINT_IOS_TEAM_ID)
  # Entitlements are attached to DEVICE builds only. The Simulator does not
  # honor Access WiFi Information (fetchCurrent returns nil there whatever the
  # entitlements say), and attaching one it cannot satisfy only invites a
  # signing failure on a build that needs no signature at all.
  #
  # The capability must also be enabled on the App ID in the developer portal,
  # or automatic signing fails with a profile mismatch. See the entitlements
  # file itself, which spells out where.
  set_target_properties(CrossPointX3 PROPERTIES
    XCODE_ATTRIBUTE_DEVELOPMENT_TEAM ${CROSSPOINT_IOS_TEAM_ID}
    XCODE_ATTRIBUTE_CODE_SIGN_STYLE "Automatic"
    XCODE_ATTRIBUTE_CODE_SIGN_ENTITLEMENTS
      "${CMAKE_CURRENT_SOURCE_DIR}/CrossPointX3.entitlements")
else()
  # Simulator builds need no signature; forcing this off keeps a machine with
  # multiple identities from picking one at random.
  set_target_properties(CrossPointX3 PROPERTIES
    XCODE_ATTRIBUTE_CODE_SIGNING_REQUIRED "NO"
    XCODE_ATTRIBUTE_CODE_SIGN_IDENTITY "")
endif()
