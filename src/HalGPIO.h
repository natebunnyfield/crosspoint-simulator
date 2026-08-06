#pragma once

#include <Arduino.h>
#include <BatteryMonitor.h>
#include <InputManager.h>

#include <string>

// Display SPI pins (custom pins for XteinkX4, not hardware SPI defaults)
#ifndef EPD_SCLK
#define EPD_SCLK 8 // SPI Clock
#endif
#ifndef EPD_MOSI
#define EPD_MOSI 10 // SPI MOSI (Master Out Slave In)
#endif
#ifndef EPD_CS
#define EPD_CS 21 // Chip Select
#endif
#ifndef EPD_DC
#define EPD_DC 4 // Data/Command
#endif
#ifndef EPD_RST
#define EPD_RST 5 // Reset
#endif
#ifndef EPD_BUSY
#define EPD_BUSY 6 // Busy
#endif

#define SPI_MISO                                                               \
  7 // SPI MISO, shared between SD card and display (Master In Slave Out)

#define BAT_GPIO0 0 // Battery voltage

#define UART0_RXD 20 // Used for USB connection detection

class HalGPIO {
#if CROSSPOINT_EMULATED == 0
  InputManager inputMgr;
#endif

public:
  enum class DeviceType : uint8_t { X4, X3 };

private:
  DeviceType _deviceType = DeviceType::X4;

public:
  HalGPIO() = default;

  // Inline device type helpers for cleaner downstream checks
  inline bool deviceIsX3() const { return _deviceType == DeviceType::X3; }
  inline bool deviceIsX4() const { return _deviceType == DeviceType::X4; }
  bool isXteinkDevice() const;
  bool hasEdgeSideButtons() const;

  // Start button GPIO and setup SPI for screen and SD card
  void begin();

  // Clears the per-frame press/release edge latches. Must be called exactly
  // once per frame (before the firmware's loop()), NOT on every update().
  void beginFrame();

  // Button input methods
  void update();
  bool isPressed(uint8_t buttonIndex) const;
  bool wasPressed(uint8_t buttonIndex) const;
  bool wasAnyPressed() const;
  bool wasReleased(uint8_t buttonIndex) const;
  bool wasAnyReleased() const;

  // --- Live button injection (simulator-only; no firmware counterpart) ------
  //
  // Drives one button's full state — press edge, held level and press
  // timestamp — from a host harness that has no real keyboard behind it (the
  // on-screen pad on a phone, CROSSPOINT_SIM_INPUT_SCRIPT, a future automation
  // hook).
  //
  // WHY THIS EXISTS RATHER THAN SDL_PushEvent. Measured, not assumed:
  // SDL_PushEvent delivers an event to SDL's queue but never writes SDL's
  // internal keyboard state array, which is only filled on the real-input path.
  // A harness that injects by pushing events therefore drives the EDGE reads
  // (wasPressed/wasReleased, fed from the dequeued event) while every LEVEL read
  // — isPressed(), getHeldTime(), getPowerButtonHeldTime(), all of which consult
  // SDL_GetKeyboardState() — stays false. Everything timed off a held button
  // silently never fires: long-press-to-sleep, page-turn autorepeat, the
  // reader's font-family hold. These two entry points write the same three
  // arrays the SDL path writes, so both halves come from one place.
  //
  // Deliberately platform-neutral: it takes a HalGPIO::BTN_* index and contains
  // no #ifdef. The knowledge of which host maps what onto which button belongs
  // to the harness, above this layer.
  void injectButtonDown(uint8_t buttonIndex);
  void injectButtonUp(uint8_t buttonIndex);

  // --- Host keyboard text entry -------------------------------------------
  //
  // The X3 has seven buttons and no keyboard, so the firmware's text entry
  // pecks characters out of an on-screen grid. Every host running the
  // simulator DOES have a keyboard -- the Mac's, an iPhone's software
  // keyboard, a Bluetooth keyboard paired to the phone -- and this is the
  // channel that carries it into the firmware's own text field. The grid is
  // untouched and still works; typing is an additional input, not a
  // replacement.
  //
  // TWO HALVES, and only the first is firmware-facing:
  //
  //   setTextEntryActive() / consumeTypedText() mirror the device HAL, where
  //   they are inline no-ops (`lib/hal/HalGPIO.h`). A text-entry activity
  //   announces itself on enter, stands down on exit, and drains this queue
  //   in its loop().
  //
  //   injectTypedText() / pumpHostTextInput() are simulator-only, like
  //   injectButton*: the host's side of the same channel.
  //
  // WHY THE ACTIVE FLAG IS LOAD-BEARING, not just a hint. Real key events are
  // mapped to buttons by scancode, and that map spends letters: P is POWER, S
  // is the sleep shortcut, H is the Home key, Return is CONFIRM. Typing
  // "password" into a Wi-Fi field would otherwise press POWER twice, sleep the
  // device on the 's' and fire Home on the 'h'. While the flag is set,
  // update() maps only Escape and the four arrows (cancel and grid
  // navigation, both of which a typist still wants) and routes everything else
  // to this queue. isPressed() applies the same rule, so a held letter cannot
  // show up as a held button either.
  //
  // The queue is a byte stream, not a char stream: printable input arrives as
  // UTF-8 (one SDL_EVENT_TEXT_INPUT can carry several code points, and an
  // iPhone's keyboard emits emoji), and the three editing keys ride along as
  // the control bytes below. Consumers walk the chunk and split it on those.
  void setTextEntryActive(bool active);
  bool isTextEntryActive() const;
  bool consumeTypedText(std::string &out);

  // Editing keys, encoded in the byte stream above. Same values on device.
  static constexpr char TYPED_BACKSPACE = '\b';
  static constexpr char TYPED_COMMIT = '\n';
  static constexpr char TYPED_CANCEL = '\x1b';

  // Host injection: the iOS harness, CROSSPOINT_SIM_INPUT_SCRIPT's TYPE
  // action. Dropped (with a log line) when no text field is open, so a
  // mistimed script fails loudly instead of leaking characters into the next
  // field that opens.
  void injectTypedText(const char *utf8);

  // MAIN THREAD ONLY, once per frame. Starts and stops SDL text input on the
  // active-flag edge, which on a phone is what raises and dismisses the
  // software keyboard -- a UIKit operation, so it cannot ride along with the
  // firmware task that flips the flag. Desktop needs the call too: SDL only
  // emits SDL_EVENT_TEXT_INPUT between StartTextInput and StopTextInput.
  void pumpHostTextInput();

  unsigned long getHeldTime() const;
  unsigned long getPowerButtonHeldTime() const;
  bool hasTouch() const;
  bool hasHomeKey() const;
  bool wasHomeKeyPressed() const;
  bool wasHomeKeyTapped() const;
  bool wasHomeKeyLongPressed() const;
  bool wasTouchTap(float &nx, float &ny) const;
  bool wasTouchDown(float &nx, float &ny) const;
  bool wasTouchReleased() const;
  bool isTouchTapCandidate(float &nx, float &ny, unsigned long &heldMs) const;
  bool isTouchHeldAt(float &nx, float &ny) const;
  unsigned long lastTouchHeldMs() const;
  bool wasSwipe(float &nxStart, float &nyStart, float &nxEnd,
                float &nyEnd) const;
  bool wasTouchActivity() const;
  void setSharedConfirmPowerShortPressEmitsPower(bool enabled);
  bool consumeSimulatorSleepRequest();

  // Setup wake up GPIO and enter deep sleep
  void startDeepSleep();

  // Verify power button was held long enough after wakeup.
  // The host wake path is synthetic, so verification always succeeds.
  bool verifyPowerButtonWakeup(uint16_t requiredDurationMs,
                               bool shortPressAllowed);

  // Check if USB is connected
  bool isUsbConnected() const;

  // Returns true once per edge (plug or unplug) since the last update()
  bool wasUsbStateChanged() const;

  enum class WakeupReason { PowerButton, AfterFlash, AfterUSBPower, Other };

  WakeupReason getWakeupReason() const;

  // Button indices
  static constexpr uint8_t BTN_BACK = 0;
  static constexpr uint8_t BTN_CONFIRM = 1;
  static constexpr uint8_t BTN_LEFT = 2;
  static constexpr uint8_t BTN_RIGHT = 3;
  static constexpr uint8_t BTN_UP = 4;
  static constexpr uint8_t BTN_DOWN = 5;
  static constexpr uint8_t BTN_POWER = 6;
};

extern HalGPIO gpio; // Singleton
