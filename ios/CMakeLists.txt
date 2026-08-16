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
set(CROSSPOINT_IOS_RENDER_SCALE 3 CACHE STRING "Supersampling factor for the iOS app")

set(CROSSPOINT_IOS_SEED_FONTS_DIR "" CACHE PATH
  "Directory of .cpfont font families to bundle and seed at launch")
if(CROSSPOINT_IOS_SEED_FONTS_DIR)
  file(GLOB _seed_families RELATIVE "${CROSSPOINT_IOS_SEED_FONTS_DIR}"
    "${CROSSPOINT_IOS_SEED_FONTS_DIR}/*")
  set(_seed_count 0)
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
      # already matches the framebuffer -- so the loop starts at 2, and the
      # cost of the extra tier is the 2x set (~53 MB against the 3x set's
      # ~114 MB on the six installed families).
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
      "CROSSPOINT_IOS_SEED_FONTS_DIR=${CROSSPOINT_IOS_SEED_FONTS_DIR} "
      "contains no <Family>/*.cpfont files — wrong path, or the font build "
      "did not run.")
  endif()
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
# 3 since 2026-08-15, matching the @3x screens this ships to. Raising it is not
# just this number: the renderer is scale-generic, but every hi-res font tier
# must EXIST at the new scale, because the companion is blitted one bitmap pixel
# to one device pixel. A family with no 3x set renders 1x-replicated into 3x3
# blocks -- coarser than the 2x it replaced -- and a 2x set cannot stand in,
# since 2 does not divide 3. So seedfonts/ carries a full 3x tier and
# convert-builtin-fonts.sh emits _3x built-ins.
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

# OMIT_FONTS strips the three NON-DEFAULT built-in reader sizes: Libre Franklin
# Reader at 12, 16 and 18 pt, four styles each -- twelve faces, ~350 KB of 2-bit
# compressed glyph data (a direct byte count of the twelve font headers). Their
# EpdFont objects sit under `#ifndef OMIT_FONTS` in the firmware's src/main.cpp,
# so under the macro that data goes unreferenced and the linker drops it. Libre
# Franklin is now the ONLY built-in reading family -- owner ruling 2026-08-07
# deleted Noto Serif, Noto Sans and Ubuntu from the firmware outright -- so there
# are no alternative built-in typefaces left to strip, only sizes of the one
# family. The former "~1 MB / 28 Noto+Ubuntu faces" line described a set that no
# longer exists.
#
# Safe because nothing the reader must draw depends on those three:
#   * getReaderFontId()'s default answer is the 14 pt cut, which stays OUTSIDE
#     the guard and so is registered in every build (firmware src/main.cpp;
#     CrossPointSettings.cpp getReaderFontId() is written so 14 pt is the size it
#     can always return).
#   * a selected SD reading family resolves BEFORE the built-in switch is reached
#     (CrossPointSettings.cpp), and an iOS build always ships seeded SD families
#     -- testflight.sh hard-fails the configure when CROSSPOINT_SEED_FONTS_DIR is
#     unset.
#   * the one chrome path that reaches for the stripped 18 pt cut, the generated
#     cover title, gates it behind renderer.getLineHeight(id) > 0 and falls back
#     to a UI face (firmware BaseTheme.cpp) -- a stripped id reads as absence,
#     not a crash.
#
# WHAT THIS DEFINE HAS ALREADY COST, so the next person weighs it properly:
# it strips font DATA while src/fontIds.h keeps vending the ids, so callers
# still believe the fonts exist. Nothing fails to compile and nothing warns --
# the renderer simply has no glyphs for an id it was just handed. iOS is the
# ONLY build that defines it, so anything it breaks is invisible on desktop.
#
# THE EDITOR MONOSPACE FAMILIES ARE DELIBERATELY EXEMPT -- DO NOT "TIDY" THEM
# BACK UNDER THE GUARD. Space Mono 12 and IBM Plex Mono 12 (four styles each) are
# the Editor Font setting's built-in answer on a blank card, and unlike the
# reader faces they have NO SD equivalent seeded on iOS -- strip them and the
# setting has nothing at all to resolve to. They sat inside `#ifndef OMIT_FONTS`
# until firmware commit 63ea6e6b; because iOS is the one build that defines the
# macro, on the phone every Editor Font row failed its
# renderer.getFontMap().count(id) availability check and the whole setting
# collapsed to UI chrome. Both families and their insertFont() calls now live
# OUTSIDE the guard in firmware src/main.cpp, beside Libre Franklin Reader 14,
# and test/omit_fonts/OmitFontsTest.cpp pins that set -- move either back inside
# and a firmware test fails instead of iOS silently shipping the broken setting.
target_compile_definitions(crosspoint_core PUBLIC OMIT_FONTS)

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
  XCODE_ATTRIBUTE_ONLY_ACTIVE_ARCH[variant=Release] "NO")

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
