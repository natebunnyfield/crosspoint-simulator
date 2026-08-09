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
  PROPERTIES COMPILE_FLAGS "-fobjc-arc")

# Optional bundled font families. Point this at a build-sd-fonts.py output
# directory (one subdirectory per family, .cpfont files inside) and each family
# ships inside the app under Resources/SeedFonts/<Family>/. At launch,
# CrossPointFsPrep copies them into the emulated SD card's visible "fonts/"
# root, so the phone gets font updates with the app instead of by hand through
# the Files app. Globbed at configure time — CI configures fresh every run, so
# a stale glob only affects incremental local builds.
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
      # Hi-res companion set. This glob is deliberately separate rather than
      # recursive: the 2x files must keep their own bundle subdirectory, since
      # SdCardFontManager finds a companion by the exact path `<family>/2x/<same
      # filename>`. Flattening them into the family directory would collide with
      # the 1x files, which carry identical names by design.
      file(GLOB _family_fonts_2x "${_family_dir}/2x/*.cpfont")
      if(_family_fonts_2x)
        set_source_files_properties(${_family_fonts_2x} PROPERTIES
          MACOSX_PACKAGE_LOCATION "Resources/SeedFonts/${_family}/2x")
        target_sources(CrossPointX3 PRIVATE ${_family_fonts_2x})
        list(LENGTH _family_fonts_2x _n2)
        math(EXPR _seed_count "${_seed_count} + ${_n2}")
        message(STATUS "Seed fonts: ${_family}/2x (${_n2} files)")
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
# HalDisplay.cpp (framebuffer size) and SdCardFontManager.cpp (2x companion
# loading) live in crosspoint_core; a define on CrossPointX3 never reaches
# them, and HalDisplay.h silently defaults the scale to 1 -- which is exactly
# how TestFlight builds through 15 shipped 1x while the pbxproj showed a =2
# that only covered the seven harness TUs. PUBLIC so the harness TUs see the
# same value and the two layers cannot disagree.
target_compile_definitions(crosspoint_core PUBLIC CROSSPOINT_RENDER_SCALE=2)

# The 28 built-in Noto/Ubuntu faces are unreachable on iOS: FontSelectionActivity
# hides built-in faces whenever SD families are installed (line 93-101 in the
# firmware), and testflight.sh hard-fails the configure when CROSSPOINT_IOS_SEED_FONTS_DIR
# is not set, so an iOS build always has at least the four S-tier families.
# Stripping them saves ~1 MB of arm64 .o / binary section.
# CalendarSleepScreen and getReaderFontId() both already handle OMIT_FONTS.
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
  # honour Access WiFi Information (fetchCurrent returns nil there whatever the
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
