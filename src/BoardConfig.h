#pragma once

#include <cstdint>

// Keep the small portion of the FreeInk BoardConfig surface used outside the
// device HAL available without pulling ESP32-only GPIO headers into the native
// build. Device and panel-controller selection are compile-time in the
// simulator so each production hardware revision can be exercised explicitly.
#define FREEINK_LOG_TRANSPORT_HWCDC 0
#define FREEINK_LOG_TRANSPORT_ROM_PRINTF 1
#define FREEINK_LOG_TRANSPORT FREEINK_LOG_TRANSPORT_HWCDC

// Two device defines at once would silently pick the first branch below and
// leave the other selection with no effect. This fork's own guard (4978f6f)
// covered the X3/X4 Pro pair only, and noted the display-controller half was
// N/A because BoardConfig had no SIMULATOR_DISPLAY_* profiles — upstream
// 1a88857 + ef68da8 add both, so the wider guard applies here now.
#if (defined(SIMULATOR_DEVICE_X3) + defined(SIMULATOR_DEVICE_X4_PRO) + \
     defined(SIMULATOR_DEVICE_STICKY) + defined(SIMULATOR_DEVICE_PICCO)) > 1
#error "Select at most one simulated device"
#endif

// FREEINK_DEVICE_PICCO must come from the COMMAND LINE with the device macro,
// as it does on the device env. Firmware TUs test it before including this
// header (notes/KeyboardPanel.cpp), and a TU that sees it undefined compiles
// its Picco half out while its callers' half stays in.
#if defined(SIMULATOR_DEVICE_PICCO) && \
    !(defined(FREEINK_DEVICE_PICCO) && FREEINK_DEVICE_PICCO)
#error "SIMULATOR_DEVICE_PICCO needs -DFREEINK_DEVICE_PICCO=1 beside it"
#endif

#if defined(SIMULATOR_DEVICE_PICCO) && \
    (defined(SIMULATOR_DISPLAY_UC8179) || defined(SIMULATOR_DISPLAY_UC8279))
#error "BOOX Picco uses SSD1677; do not select an Xteink controller override"
#endif

#if defined(SIMULATOR_DISPLAY_UC8179) && defined(SIMULATOR_DISPLAY_UC8279)
#error "Select at most one simulated display controller"
#endif

#if defined(SIMULATOR_DEVICE_X3) && defined(SIMULATOR_DISPLAY_UC8179)
#error "Xteink X3 revisions use UC8253 or UC8279d, not UC8179"
#endif

#if defined(SIMULATOR_DEVICE_STICKY) && \
    (defined(SIMULATOR_DISPLAY_UC8179) || defined(SIMULATOR_DISPLAY_UC8279))
#error "Seeed Sticky uses SSD1677; do not select an Xteink controller override"
#endif

// BOOX Picco (owner 2026-11-25: a second iOS app, "Full Picco as a second
// app"). Same 800x480 SSD1677 geometry as Sticky; touch (TMA525C) and an I2C
// warm/cool frontlight. FREEINK_DEVICE_PICCO turns on the firmware's own Picco
// paths: keyboard-only touch, the iOS-norm gesture decoder, the rocker table,
// the Brightness/Warmth/Slide Switch rows (crosspoint-reader
// docs/picco-port-2026-11-05.md). Every other profile leaves it 0, which is
// also the SDK's default.
#if defined(SIMULATOR_DEVICE_PICCO)
#define FREEINK_DEVICE_X4 0
#define FREEINK_DEVICE_X3 0
#define FREEINK_DEVICE_X4PRO 0
#define FREEINK_DEVICE_STICKY 0
#define FREEINK_CAP_TOUCH 1
#define FREEINK_CAP_FRONTLIGHT 1
#elif defined(SIMULATOR_DEVICE_STICKY)
#define FREEINK_DEVICE_X4 0
#define FREEINK_DEVICE_X3 0
#define FREEINK_DEVICE_X4PRO 0
#define FREEINK_DEVICE_STICKY 1
#define FREEINK_CAP_TOUCH 1
#define FREEINK_CAP_FRONTLIGHT 0
#elif defined(SIMULATOR_DEVICE_X4_PRO)
#define FREEINK_DEVICE_X4 0
#define FREEINK_DEVICE_X3 0
#define FREEINK_DEVICE_X4PRO 1
#define FREEINK_DEVICE_STICKY 0
#define FREEINK_CAP_TOUCH 1
#define FREEINK_CAP_FRONTLIGHT 1
#elif defined(SIMULATOR_DEVICE_X3)
#define FREEINK_DEVICE_X4 0
#define FREEINK_DEVICE_X3 1
#define FREEINK_DEVICE_X4PRO 0
#define FREEINK_DEVICE_STICKY 0
#define FREEINK_CAP_TOUCH 0
#define FREEINK_CAP_FRONTLIGHT 0
#else
#define FREEINK_DEVICE_X4 1
#define FREEINK_DEVICE_X3 0
#define FREEINK_DEVICE_X4PRO 0
#define FREEINK_DEVICE_STICKY 0
#define FREEINK_CAP_TOUCH 0
#define FREEINK_CAP_FRONTLIGHT 0
#endif

#define FREEINK_MCU_C3 (FREEINK_DEVICE_X3 || FREEINK_DEVICE_X4)

namespace BoardConfig {

enum class Board {
  XteinkX4,
  XteinkX3,
  XteinkX3Uc8279,
  XteinkX4Pro,
  Sticky,
  Picco,
};

enum class DisplayController {
  SSD1677,
  UC8253,
  UC8279,
  UC8179,
};

struct ViewableInsets {
  uint8_t top = 9;
  uint8_t right = 3;
  uint8_t bottom = 3;
  uint8_t left = 3;
};

struct BoardProfile {
  Board board;
  const char *name;
  DisplayController displayController;
  uint8_t displayControllerVariant;
  struct {
    int8_t up;
    int8_t down;
  } input;
  ViewableInsets viewableInsets = {};
};

#if defined(SIMULATOR_DISPLAY_UC8179)
inline constexpr DisplayController X4_DISPLAY_CONTROLLER =
    DisplayController::UC8179;
inline constexpr uint8_t X4_DISPLAY_CONTROLLER_VARIANT = 0x01;
#elif defined(SIMULATOR_DISPLAY_UC8279)
inline constexpr DisplayController X4_DISPLAY_CONTROLLER =
    DisplayController::UC8279;
// The SDK supports LUT_VER 0x02, 0x68, and reserved 0x69. Model the documented
// 0x68 production variant by default; callers can still inspect the controller.
inline constexpr uint8_t X4_DISPLAY_CONTROLLER_VARIANT = 0x68;
#else
inline constexpr DisplayController X4_DISPLAY_CONTROLLER =
    DisplayController::SSD1677;
inline constexpr uint8_t X4_DISPLAY_CONTROLLER_VARIANT = 0;
#endif

inline constexpr BoardProfile XTEINK_X4 = {Board::XteinkX4, "xteink_x4",
                                           X4_DISPLAY_CONTROLLER,
                                           X4_DISPLAY_CONTROLLER_VARIANT,
                                           {4, 5}};
inline constexpr BoardProfile XTEINK_X3 = {Board::XteinkX3, "xteink_x3",
                                           DisplayController::UC8253, 0, {4, 5}};
inline constexpr BoardProfile XTEINK_X3_UC8279 = {
    Board::XteinkX3Uc8279, "xteink_x3_uc8279", DisplayController::UC8279, 0,
    {4, 5}};
inline constexpr BoardProfile XTEINK_X4_PRO = {
    Board::XteinkX4Pro, "xteink_x4_pro", X4_DISPLAY_CONTROLLER,
    X4_DISPLAY_CONTROLLER_VARIANT, {0, 7}};
inline constexpr BoardProfile STICKY = {
    Board::Sticky, "sticky", DisplayController::SSD1677, 0, {5, 6}};
// The Picco's rocker arrives on the up/down slots; the firmware's Picco
// mapButton remap turns them into Right (upper) / Left (lower).
inline constexpr BoardProfile PICCO = {
    Board::Picco, "picco", DisplayController::SSD1677, 0, {4, 5}};

#if defined(SIMULATOR_DEVICE_PICCO)
inline BoardProfile ACTIVE = PICCO;
#elif defined(SIMULATOR_DEVICE_STICKY)
inline BoardProfile ACTIVE = STICKY;
#elif defined(SIMULATOR_DEVICE_X4_PRO)
inline BoardProfile ACTIVE = XTEINK_X4_PRO;
#elif defined(SIMULATOR_DEVICE_X3)
#if defined(SIMULATOR_DISPLAY_UC8279)
inline BoardProfile ACTIVE = XTEINK_X3_UC8279;
#else
inline BoardProfile ACTIVE = XTEINK_X3;
#endif
#else
inline BoardProfile ACTIVE = XTEINK_X4;
#endif

inline bool selectDevice(Board board) {
  switch (board) {
  case Board::XteinkX4:
    ACTIVE = XTEINK_X4;
    return true;
  case Board::XteinkX3:
    ACTIVE = XTEINK_X3;
    return true;
  case Board::XteinkX3Uc8279:
    ACTIVE = XTEINK_X3_UC8279;
    return true;
  case Board::XteinkX4Pro:
    ACTIVE = XTEINK_X4_PRO;
    return true;
  case Board::Sticky:
    ACTIVE = STICKY;
    return true;
  case Board::Picco:
    ACTIVE = PICCO;
    return true;
  }
  return false;
}

inline bool isX4Pro() { return ACTIVE.board == Board::XteinkX4Pro; }
inline bool isSticky() { return ACTIVE.board == Board::Sticky; }
inline bool isPicco() { return ACTIVE.board == Board::Picco; }
inline bool hasTouch() { return isX4Pro() || isSticky() || isPicco(); }
inline bool hasHomeKey() { return isX4Pro(); }
inline bool hasPwmFrontlight() { return isX4Pro(); }

inline void holdPowerRails() {}

} // namespace BoardConfig
