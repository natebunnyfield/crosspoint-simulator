#pragma once

#include <Arduino.h>
#include <BatteryMonitor.h>
#include <InputManager.h>

#include <string>

#include "ReadAloudChannel.h"
#include "ReadingChannel.h"
#include "TextEntryKeyRouting.h"

// A STABLE 64-bit key for a book, from its path. MIRRORS the firmware's
// lib/hal/HalGPIO.h definition exactly -- this header shadows that one on a
// simulator build, so the two must agree byte for byte or the same book keys
// differently on device and off it.
//
// FNV-1a spelled out rather than borrowed, because determinism across builds is
// the whole point: std::hash<std::string> is implementation-defined and libc++
// and libstdc++ disagree. Consumed by publishReaderPageIdentity below.
#ifndef CROSSPOINT_READER_BOOK_KEY
#define CROSSPOINT_READER_BOOK_KEY
inline uint64_t readerBookKey(const std::string& path) {
  uint64_t h = 1469598103934665603ull;  // FNV offset basis
  for (const char c : path) {
    h ^= static_cast<uint64_t>(static_cast<unsigned char>(c));
    h *= 1099511628211ull;  // FNV prime
  }
  return h;
}
#endif

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
  // Mirrors InputManager::isDebouncePending() on device
  // (freeink-sdk/libs/hardware/InputManager/include/InputManager.h:47). The
  // simulator commits button state synchronously, so nothing is ever mid-
  // debounce here.
  bool isDebouncePending() const { return false; }

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
  //
  // The second argument says whether the open field is one line or many, and
  // it decides one thing only: who owns the Return key. A single-line field
  // leaves it as BTN_CONFIRM (Select on the on-screen keyboard), a multi-line
  // one gives it to the text as a line break. Full contract and the two bug
  // reports behind it: src/TextEntryKeyRouting.h. Defaulted so the device HAL's
  // signature and every existing call site stay as they are.
  using TextEntryLines = textentry::Lines;
  void setTextEntryActive(bool active,
                          TextEntryLines lines = TextEntryLines::Single);
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

  // Show or hide the host's software keyboard while the field stays open --
  // simulator-only, like injectTypedText, and with no device counterpart: a
  // keyboard you can dismiss is a thing only a host has.
  //
  // It exists because on iPhone the keyboard is otherwise a trap. It covers
  // roughly 40% of the screen, the panel is squeezed into what is left, and
  // unlike iPad the iPhone software keyboard has NO dismiss key -- so with a
  // field open there was no way to see the page, or to use the firmware's own
  // on-screen grid, without leaving the screen entirely.
  //
  // Hiding does not close the field: the firmware's flag is untouched, the
  // grid keyboard keeps working, and typed text still routes here the moment
  // the keyboard comes back. The keyboard also does not come up on its own --
  // every text-entry edge resets to hidden (owner ruling 2026-08-12), so a
  // field always opens with the chip showing and waits for an explicit tap;
  // see the comment in setTextEntryActive() and HostKeyboardState.h.
  // isHostKeyboardVisible() is false whenever no field is open, so
  // `isTextEntryActive() && !isHostKeyboardVisible()` is exactly the state
  // the iOS harness paints its "Tap to type" chip in -- which now also covers
  // the moment a field first opens, not just a keyboard dismissed mid-field.
  void setHostKeyboardVisible(bool visible);
  bool isHostKeyboardVisible() const;

  // MAIN THREAD ONLY, once per frame. Starts and stops SDL text input on the
  // active-flag edge, which on a phone is what raises and dismisses the
  // software keyboard -- a UIKit operation, so it cannot ride along with the
  // firmware task that flips the flag. Desktop needs the call too: SDL only
  // emits SDL_EVENT_TEXT_INPUT between StartTextInput and StopTextInput.
  void pumpHostTextInput();

  // --- Read-aloud page channel --------------------------------------------
  //
  // The device has no speaker; every host running the simulator has one, and
  // this channel carries the reader's page text (and per-word rects) out to
  // a host speech consumer. Full contract: src/ReadAloudChannel.h and
  // .claude/PLAN-tts-read-aloud.md.
  //
  // TWO HALVES, same split as the keyboard channel above and for the same
  // reason — only the first is firmware-facing:
  //
  //   readAloudCaptureWanted() / publishReadAloudPage() mirror the device
  //   HAL, where they are inline no-ops (`lib/hal/HalGPIO.h`: wanted is
  //   `false`, so the capture branch folds away on device). The reader
  //   checks wanted during a page render, publishes the displayed page's
  //   text after it, and publishes nullptr on exit ("no page" — consumers
  //   stop speech).
  //
  //   setReadAloudCaptureWanted() / consumeReadAloudPage() are
  //   simulator-only, like injectButton*: the host consumer's side. Exactly
  //   one consumer per build (the env-gated desktop logger in
  //   simulator_main.cpp, or the iOS adapter).
  bool readAloudCaptureWanted() const;
  void publishReadAloudPage(const char *utf8, size_t utf8Len,
                            const ReadAloudWordRect *rects, size_t rectCount);
  void setReadAloudCaptureWanted(bool wanted);
  bool consumeReadAloudPage(ReadAloudPage &out);

  // --- Font-family step channel (shake -> next reading font) --------------
  //
  // Same two-halves split as the read-aloud channel, pointed the same way as
  // the keyboard channel: a host gesture the device does not have (an iPhone
  // SHAKE in zen mode) asks the reader to cycle to the next font family.
  // Contract: src/FontFamilyStepChannel.h (consume-once, bursts collapse).
  //
  //   consumeFontFamilyStep() is firmware-facing and mirrors the device HAL,
  //   where it is an inline no-op returning false (lib/hal/HalGPIO.h), so the
  //   reader's poll folds away on device.
  //
  //   injectFontFamilyStep() is simulator-only, like injectButton*: the
  //   host's side (the zen shake responder on iOS, SHAKE in
  //   CROSSPOINT_SIM_INPUT_SCRIPT on the desktop).
  bool consumeFontFamilyStep();
  void injectFontFamilyStep();

  // The reader's FINAL text-block insets — top after the paint-time cap-ink
  // trim, then right, bottom, left — in FRAMEBUFFER pixels. Firmware-facing
  // half of the same split as the read-aloud channel: an inline no-op on
  // device (lib/hal/HalGPIO.h), a real store here. EpubReaderActivity
  // publishes on every render; the host reads the latest values through
  // SimulatorOverlay::readerTextInsetsPx() (the iOS zen sheet places the page
  // from them instead of calibrated constants). Atomics, because publish runs
  // on the firmware task and the consumer is the main-thread relayout.
  void publishReaderTextInsets(int topPx, int rightPx, int bottomPx, int leftPx);

  // WHICH PAGE OF WHICH BOOK IS ON SCREEN. Firmware-facing half of the same
  // split as the insets channel above: an inline no-op on device
  // (lib/hal/HalGPIO.h), a real latch here. Published once per DISPLAYED page
  // by every reader activity; the host reads it through
  // SimulatorOverlay::readerPageIdentity().
  //
  // WHY THIS EXISTS. The light page's paper is generated, and paper is not a
  // property of the LAUNCH -- a book is not re-printed when you close it. Both
  // light-mode fields seed from a hash of these three numbers, so a page you
  // turn back to is the same sheet, including across a relaunch. See
  // src/PaperDefects.h and docs/paper-defects.md.
  //
  // NOTHING CLEARS THE LATCH, deliberately: it is superseded rather than
  // cleared, by whichever publisher spoke last. Since 2026-08-24 that is
  // either this or publishScreenIdentity below, so walking out of a book into
  // a menu moves to the MENU's sheet rather than keeping the last page's --
  // see that comment for why the earlier "keep the page's sheet" answer went
  // with the launch-seed fallback it existed to soften.
  //
  // Atomics, because publish runs on the firmware task and the consumer is the
  // main-thread present path.
  void publishReaderPageIdentity(uint64_t bookKey, int32_t spineIndex,
                                 int32_t pageInSpine);

  // WHICH SYSTEM SCREEN IS ON GLASS. Same split as the identity above: an
  // inline no-op on device (lib/hal/HalGPIO.h), a real latch here. Published
  // once per activity entry by Activity::onEnter() -- the one place every
  // screen in the firmware passes through -- for every activity that is NOT a
  // reader.
  //
  // WHY READERS ARE SKIPPED THERE rather than publishing and being overwritten:
  // a reader publishes its page identity from its RENDER, which is strictly
  // after its onEnter(), so publishing here as well would put one screen-seeded
  // present between the two on every book open. That present would carry the
  // previous screen's pixels on a third sheet, which is a visible flicker of
  // the paper tone and a wasted output-size field build.
  //
  // The argument is `screenKey`, the FNV-1a of the activity name; the seed the
  // fields use is sheetid::forScreen of it. See src/SheetIdentity.h.
  void publishScreenIdentity(uint32_t screenKey);

  // WHAT THE READER JUST PUT ON GLASS, AND WHAT IT WAS SET TO WHEN IT DID.
  // Firmware-facing half; an inline no-op on device (lib/hal/HalGPIO.h). The
  // sink is readinglog::publishPage -- one JSONL line per displayed page,
  // never leaving the device. See src/ReadingLog.h and
  // docs/reading-experiments.md.
  //
  // Deliberately NOT the identity channel with more fields: that one seeds the
  // PAPER on the present path and is superseded rather than cleared, this one
  // appends to a ledger. Two consumers, two lifetimes, two channels.
  void publishReadingPage(const ReadingPageSample &sample);

  // Simulator-only. Schedule a full synthetic button tap — press edge, held
  // level for holdMs, release edge — that fires INSIDE update(), which is
  // the only place an injected edge is visible to the firmware: beginFrame()
  // clears the edge latches at the top of each frame, and the harness's
  // per-frame hook runs after loop(), so a press injected there is wiped
  // before any wasPressed() can see it. The on-screen pad never hits this
  // because its event watch fires inside update()'s pump; anything driven by
  // a main-loop hook (the read-aloud page turn) must go through here.
  void queueButtonTap(uint8_t buttonIndex, unsigned long holdMs);

  // Simulator-only, the host consumer's side like injectButton* — the
  // firmware never calls it. Drop every queued tap, releasing the press of
  // any tap whose down already fired so no held level survives the caller's
  // boundary. The reboot registry and the sleep path clear the queue on their
  // own; the caller this exists for is APP BACKGROUNDING (iOS harness): a
  // queued tap that survived a backgrounding fired its release with the whole
  // background span attached on return, which the firmware classifies as a
  // long press.
  void clearPendingButtonTaps();

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
  bool wasTouchLongPress(float &nx, float &ny) const;
  void suppressTouchContact();
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
  void pollUsbState() {}

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
