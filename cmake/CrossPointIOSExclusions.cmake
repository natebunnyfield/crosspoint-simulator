# TUs excluded from the iOS target only. NOT GENERATED -- edit by hand.
#
# This file exists because it was once part of cmake/CrossPointSources.cmake,
# which IS generated. e75ab8c added the two lists there; af2e842 regenerated the
# file and silently deleted them, because tools/gen_cmake_sources.py does not
# know they exist. Nothing failed: CMake treats
# `list(REMOVE_ITEM x ${undefined})` as a no-op, so the configure line went on
# printing a strip count of 0 while the iOS binary carried the whole network
# stack. Policy about what to build is a human decision and does not belong in a
# derived file; keeping it here is what makes the next regeneration harmless.
#
# Applied via list(REMOVE_ITEM ...) in the root CMakeLists.txt, before
# crosspoint_core is created. The desktop build never reads this file.
#
# See ios/WIFI.md for which of these come back as iOS gains network support,
# and which (OTA, SD flash) never will.

# Simulator HAL/shim TUs. Paths relative to this repo root.
set(CROSSPOINT_IOS_EXCLUDED_SIM_SOURCES
  # Dead in every configuration, not iOS-specific: the whole file sits behind
  # #ifndef CROSSPOINT_SIMULATOR_PROJECT_WEBSERVER and every consumer defines it.
  src/CrossPointWebServer.cpp
  # The OTA stub goes out with the activity it serves.
  src/simulator_ota.cpp
)
set(CROSSPOINT_IOS_EXCLUDED_FW_SOURCES
  # Only what a phone genuinely cannot do.
  #
  # Networking came back when the iOS target grew a real radio (4a98ba8:
  # CrossPointWiFi.mm over NetworkExtension, in-process HTTP, Bonjour, servers
  # bound to all interfaces). Before that, excluding it was correct -- File
  # Transfer drew a QR code pointing at 127.0.0.1 (B-008). After it, the
  # exclusion was hiding features that work.
  #
  # These two write firmware to an ESP32 partition. That does not become
  # possible; CROSSPOINT_NO_DEVICE_FLASH gates their menu entries to match.
  src/activities/settings/OtaUpdateActivity.cpp
  src/activities/settings/SdFirmwareUpdateActivity.cpp
)
