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
  src/CrossPointWebServer.cpp
  src/NetworkClient.cpp
  src/WebServer.cpp
  src/WebSocketsServer.cpp
  src/qrcode.cpp
  src/simulator_ota.cpp
)

# Firmware TUs. Paths relative to CROSSPOINT_FIRMWARE_DIR.
set(CROSSPOINT_IOS_EXCLUDED_FW_SOURCES
  src/WifiCredentialStore.cpp
  src/activities/network/CrossPointWebServerActivity.cpp
  src/activities/network/NetworkModeSelectionActivity.cpp
  src/activities/network/WifiSelectionActivity.cpp
  src/activities/settings/FontDownloadActivity.cpp
  src/activities/settings/OtaUpdateActivity.cpp
  src/activities/settings/SdFirmwareUpdateActivity.cpp
  src/network/CrossPointWebServer.cpp
  src/network/HttpDownloader.cpp
  src/network/WebDAVHandler.cpp
  src/network/WifiDiagnostics.cpp
  src/util/QrUtils.cpp
)
