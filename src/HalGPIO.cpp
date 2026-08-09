#include "HalGPIO.h"

#include "ReadAloudLines.h"
#include "SimulatorRebootResets.h"

#include <BoardConfig.h>
#include <GfxRenderer.h>
#include <SDL3/SDL.h>

#include <algorithm>
#include <atomic>
#include <cctype>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <mutex>
#include <string>
#include <vector>

#include "HalDisplay.h"
#include "SimulatorLifecycle.h"

// Defined in HalDisplay.cpp — set here so all SDL event polling lives in one
// place.
extern std::atomic<bool> quitRequested;
extern GfxRenderer renderer;
// Also HalDisplay.cpp's, for SDL_StartTextInput, which needs the window.
// A free function rather than a HalDisplay method for the usual reason: the
// HAL's public surface has to stay the shape the firmware expects, and a
// window handle has no analog on an e-ink board.
extern SDL_Window *simulatorWindow();

// Keyboard mapping:
//   BTN_BACK    (0) → Escape
//   BTN_CONFIRM (1) → Return
//   BTN_LEFT    (2) → Left arrow
//   BTN_RIGHT   (3) → Right arrow
//   BTN_UP      (4) → Up arrow
//   BTN_DOWN    (5) → Down arrow
//   BTN_POWER   (6) → P
//   Simulator sleep shortcut → S

static constexpr int NUM_BUTTONS = 7;
static constexpr SDL_Scancode SIMULATOR_SLEEP_SCANCODE = SDL_SCANCODE_S;
static constexpr SDL_Scancode HOME_KEY_SCANCODE = SDL_SCANCODE_H;
static constexpr int TOUCH_TAP_SLOP_PX = 28;
static constexpr int TOUCH_SWIPE_MIN_PX = 60;
static constexpr unsigned long TOUCH_SWIPE_MAX_MS = 700;
static constexpr unsigned long HOME_KEY_LONG_PRESS_MS = 700;

static const SDL_Scancode buttonScancode[NUM_BUTTONS] = {
    SDL_SCANCODE_ESCAPE, // BTN_BACK
    SDL_SCANCODE_RETURN, // BTN_CONFIRM
    SDL_SCANCODE_LEFT,   // BTN_LEFT
    SDL_SCANCODE_RIGHT,  // BTN_RIGHT
    SDL_SCANCODE_UP,     // BTN_UP
    SDL_SCANCODE_DOWN,   // BTN_DOWN
    SDL_SCANCODE_P,      // BTN_POWER
};

static bool pressedThisFrame[NUM_BUTTONS] = {};
static bool releasedThisFrame[NUM_BUTTONS] = {};
static unsigned long buttonPressTime[NUM_BUTTONS] = {};
// Span of the most recent completed press. The device's InputManager keeps
// returning buttonPressFinish - buttonPressStart after release, and firmware
// release handlers (short- vs long-press branches) read getHeldTime() on the
// release frame — without this the shim reports 0 there and every release
// classifies as a short press.
static unsigned long lastReleasedSpan = 0;
static bool syntheticButtonDown[NUM_BUTTONS] = {};
// Set by injectButtonDown, consumed only by the deep-sleep wake loop. An EDGE,
// not a level: a fast tap's down and up can both land inside one event-pump
// burst (a 1 ms scripted tap; iOS delivering queued FINGER_DOWN+FINGER_UP
// after unlock), so by the time the sleep loop's 10 ms poll looks at
// syntheticButtonDown[] the level is already gone and the wake is missed.
// The latch survives until the sleep loop reads it. Regression test:
// tests/test_sleep_wake.sh in the simulator repo.
static std::atomic<bool> syntheticWakeEdge{false};
static bool simulatorSleepRequested = false;

// --- Host keyboard text entry (see the block comment in HalGPIO.h) ---------
//
// The flag is atomic because the firmware task sets it (a text-entry activity
// entering) while the main thread reads it in pumpHostTextInput(). The buffer
// takes a mutex rather than an atomic because the iOS harness can queue from a
// UIKit callback on a thread of its own.
static std::atomic<bool> textEntryActive{false};
static std::mutex typedTextMutex;
static std::string typedTextBuffer;

static ReadAloudChannel readAloudChannel;

// Pending synthetic taps (queueButtonTap). Queued from the harness's
// per-frame hook and drained at the top of update() — both on the main
// thread, so no lock.
struct PendingButtonTap {
  uint8_t button;
  unsigned long holdMs;
  bool downSent = false;
  unsigned long upAtTicks = 0;
};
static std::vector<PendingButtonTap> pendingButtonTaps;

static bool scancodeIsEnter(SDL_Scancode sc) {
  return sc == SDL_SCANCODE_RETURN || sc == SDL_SCANCODE_KP_ENTER ||
         sc == SDL_SCANCODE_RETURN2;
}

// The scancodes that keep their button meaning while a text field is open.
// Escape cancels the entry and the arrows move the on-screen grid selection --
// both are things a typist still reaches for, and neither produces a
// character. Every other key belongs to the text.
//
// RETURN IS IN THAT LIST TOO, and it is the whole reason this comment is long.
// Return is BTN_CONFIRM, which is "Select" on every on-screen keyboard -- the
// key that types the highlighted character. While a text field was open it was
// swallowed here and queued as TYPED_COMMIT instead, so pressing Select on the
// daisywheel committed the field and left the screen rather than typing. The
// arrows survived, so the wheel still rotated; only picking was broken, which
// is what made it read as "Select exits instead of typing".
//
// This was invisible to CROSSPOINT_SIM_INPUT_SCRIPT, which writes
// syntheticButtonDown[] and never goes through a scancode at all -- so every
// scripted run showed Select working while a human pressing the same key did
// not. Worth remembering before trusting a scripted pass on an input bug.
//
// A host typist keeps a commit: Cmd+Return or Ctrl+Return, handled in update()
// before this gate. Plain Return now belongs to the on-screen keyboard, which
// is the default input method and has its own OK / RET key besides.
static bool scancodeSurvivesTextEntry(SDL_Scancode sc) {
  return sc == SDL_SCANCODE_ESCAPE || sc == SDL_SCANCODE_LEFT ||
         sc == SDL_SCANCODE_RIGHT || sc == SDL_SCANCODE_UP ||
         sc == SDL_SCANCODE_DOWN || scancodeIsEnter(sc);
}

static void queueTypedBytes(const char *bytes, size_t length) {
  if (!bytes || length == 0)
    return;
  std::lock_guard<std::mutex> lock(typedTextMutex);
  typedTextBuffer.append(bytes, length);
}

namespace {

struct TouchState {
  bool down = false;
  bool pressedThisFrame = false;
  bool releasedThisFrame = false;
  bool movedBeyondTapSlop = false;
  bool activityThisFrame = false;
  float startNx = 0.0f;
  float startNy = 0.0f;
  float currentNx = 0.0f;
  float currentNy = 0.0f;
  unsigned long pressedAt = 0;
  unsigned long lastHeldMs = 0;
};

TouchState touchState;
bool homeKeyDown = false;
bool homeKeyPressedThisFrame = false;
bool homeKeyTappedThisFrame = false;
bool homeKeyLongPressedThisFrame = false;
bool homeKeyLongFired = false;
unsigned long homeKeyPressedAt = 0;

enum class SyntheticAction {
  KeyDown,
  KeyUp,
  TouchDown,
  TouchUp,
  HomeDown,
  HomeUp,
  TypeText,
  Sleep,
  Quit,
  QueuedTap
};

struct SyntheticEvent {
  unsigned long atMs;
  SyntheticAction action;
  int button = -1;
  float logicalNx = 0.0f;
  float logicalNy = 0.0f;
  std::string text;
  bool handled = false;
  unsigned long holdMs = 0; // QueuedTap only
};

// TYPE payload escapes. The script's own separators (';' between items) cannot
// appear in text, and the three editing keys have no printable spelling, so
// they get backslash escapes: \b backspace, \n commit (the on-screen OK key),
// \e cancel, \\ a literal backslash.
std::string decodeTypeEscapes(const std::string &raw) {
  std::string out;
  out.reserve(raw.size());
  for (size_t i = 0; i < raw.size(); i++) {
    if (raw[i] != '\\' || i + 1 >= raw.size()) {
      out.push_back(raw[i]);
      continue;
    }
    switch (raw[++i]) {
    case 'b':
      out.push_back(HalGPIO::TYPED_BACKSPACE);
      break;
    case 'n':
      out.push_back(HalGPIO::TYPED_COMMIT);
      break;
    case 'e':
      out.push_back(HalGPIO::TYPED_CANCEL);
      break;
    case '\\':
      out.push_back('\\');
      break;
    default:
      out.push_back('\\');
      out.push_back(raw[i]);
      break;
    }
  }
  return out;
}

std::vector<SyntheticEvent> syntheticEvents;
bool syntheticEventsInitialized = false;

// The in-process (iOS) reboot keeps this TU's statics. Without these resets the
// *_AFTER_WAKE promotion in rebootAsPowerWake() has no effect on the phone --
// the schedule was already latched -- and a reboot performed while a text field
// was open leaves the keyboard channel on, which keeps the scancode->button map
// suppressed and makes the buttons appear dead. See SimulatorRebootResets.h.
const simreset::Registrar gGpioRebootReset{[] {
  syntheticEventsInitialized = false;
  syntheticEvents.clear();
  textEntryActive.store(false);
}};

float clamp01(float value) { return std::max(0.0f, std::min(1.0f, value)); }

void logicalToPanelNormalized(float logicalNx, float logicalNy, float &panelNx,
                              float &panelNy) {
  const int logicalWidth = renderer.getScreenWidth();
  const int logicalHeight = renderer.getScreenHeight();
  const int lx = static_cast<int>(clamp01(logicalNx) *
                                  static_cast<float>(logicalWidth - 1));
  const int ly = static_cast<int>(clamp01(logicalNy) *
                                  static_cast<float>(logicalHeight - 1));

  int physicalX = 0;
  int physicalY = 0;
  switch (renderer.getOrientation()) {
  case GfxRenderer::Portrait:
    physicalX = ly;
    physicalY = HalDisplay::DISPLAY_HEIGHT - 1 - lx;
    break;
  case GfxRenderer::PortraitInverted:
    physicalX = HalDisplay::DISPLAY_WIDTH - 1 - ly;
    physicalY = lx;
    break;
  case GfxRenderer::LandscapeClockwise:
    physicalX = HalDisplay::DISPLAY_WIDTH - 1 - lx;
    physicalY = HalDisplay::DISPLAY_HEIGHT - 1 - ly;
    break;
  case GfxRenderer::LandscapeCounterClockwise:
  default:
    physicalX = lx;
    physicalY = ly;
    break;
  }

  panelNx = clamp01(static_cast<float>(physicalX) /
                    static_cast<float>(HalDisplay::DISPLAY_WIDTH - 1));
  panelNy = clamp01(static_cast<float>(physicalY) /
                    static_cast<float>(HalDisplay::DISPLAY_HEIGHT - 1));
}

void updateTouchMovement(float panelNx, float panelNy) {
  touchState.currentNx = panelNx;
  touchState.currentNy = panelNy;
  const float dx =
      (touchState.currentNx - touchState.startNx) * HalDisplay::DISPLAY_WIDTH;
  const float dy =
      (touchState.currentNy - touchState.startNy) * HalDisplay::DISPLAY_HEIGHT;
  if (std::abs(dx) > TOUCH_TAP_SLOP_PX || std::abs(dy) > TOUCH_TAP_SLOP_PX) {
    touchState.movedBeyondTapSlop = true;
  }
}

void beginTouch(float logicalNx, float logicalNy) {
  if (!BoardConfig::hasTouch())
    return;
  float panelNx = 0.0f;
  float panelNy = 0.0f;
  logicalToPanelNormalized(logicalNx, logicalNy, panelNx, panelNy);
  touchState.down = true;
  touchState.pressedThisFrame = true;
  touchState.activityThisFrame = true;
  touchState.movedBeyondTapSlop = false;
  touchState.startNx = panelNx;
  touchState.startNy = panelNy;
  touchState.currentNx = panelNx;
  touchState.currentNy = panelNy;
  touchState.pressedAt = SDL_GetTicks();
}

void moveTouch(float logicalNx, float logicalNy) {
  if (!touchState.down)
    return;
  float panelNx = 0.0f;
  float panelNy = 0.0f;
  logicalToPanelNormalized(logicalNx, logicalNy, panelNx, panelNy);
  updateTouchMovement(panelNx, panelNy);
}

void endTouch(float logicalNx, float logicalNy) {
  if (!touchState.down)
    return;
  moveTouch(logicalNx, logicalNy);
  touchState.down = false;
  touchState.releasedThisFrame = true;
  touchState.activityThisFrame = true;
  touchState.lastHeldMs = SDL_GetTicks() - touchState.pressedAt;
}

void beginHomeKey() {
  if (!BoardConfig::hasHomeKey() || homeKeyDown)
    return;
  homeKeyDown = true;
  homeKeyPressedThisFrame = true;
  homeKeyLongFired = false;
  homeKeyPressedAt = SDL_GetTicks();
}

void endHomeKey() {
  if (!homeKeyDown)
    return;
  if (!homeKeyLongFired &&
      SDL_GetTicks() - homeKeyPressedAt < HOME_KEY_LONG_PRESS_MS) {
    homeKeyTappedThisFrame = true;
  }
  homeKeyDown = false;
}

void updateHomeKeyHold() {
  if (homeKeyDown && !homeKeyLongFired &&
      SDL_GetTicks() - homeKeyPressedAt >= HOME_KEY_LONG_PRESS_MS) {
    homeKeyLongFired = true;
    homeKeyLongPressedThisFrame = true;
  }
}

bool parseTouchSpec(const std::string &detail, float &x1, float &y1, float &x2,
                    float &y2, unsigned long &duration, bool swipe) {
  unsigned parsedDuration = swipe ? 250 : 80;
  int parsed = 0;
  if (swipe) {
    parsed = std::sscanf(detail.c_str(), "%f,%f,%f,%f,%u", &x1, &y1, &x2, &y2,
                         &parsedDuration);
    if (parsed < 4)
      return false;
  } else {
    parsed = std::sscanf(detail.c_str(), "%f,%f,%u", &x1, &y1, &parsedDuration);
    if (parsed < 2)
      return false;
    x2 = x1;
    y2 = y1;
  }

  // Scripts normally use logical display pixels because those coordinates are
  // easy to read from UI layouts and screenshots. Preserve support for the
  // earlier 0.0-1.0 normalized form so existing local QA scripts keep working.
  const auto normalize = [](float value, int extent) {
    if (value >= 0.0f && value <= 1.0f)
      return value;
    return clamp01(value / static_cast<float>(std::max(1, extent - 1)));
  };
  const int logicalWidth = renderer.getScreenWidth();
  const int logicalHeight = renderer.getScreenHeight();
  x1 = normalize(x1, logicalWidth);
  y1 = normalize(y1, logicalHeight);
  x2 = normalize(x2, logicalWidth);
  y2 = normalize(y2, logicalHeight);
  duration = parsedDuration;
  return true;
}

void requestSimulatorSleep() {
  simulatorSleepRequested = true;
  // Current CrossPoint firmware sleeps on a held physical power button. Keep
  // the compatibility latch above for older consumers, and also drive the
  // current public HalGPIO state so the S shortcut follows the real firmware
  // sleep path. No matching injectButtonUp(): the shortcut has no release, so
  // POWER stays held until clearButtonState() runs at sleep entry — which is
  // what makes the firmware's held-duration check pass.
  gpio.injectButtonDown(HalGPIO::BTN_POWER);
}

std::string uppercase(std::string value) {
  std::transform(
      value.begin(), value.end(), value.begin(),
      [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
  return value;
}

int namedButton(const std::string &name) {
  if (name == "ESCAPE" || name == "BACK")
    return HalGPIO::BTN_BACK;
  if (name == "RETURN" || name == "ENTER" || name == "CONFIRM")
    return HalGPIO::BTN_CONFIRM;
  if (name == "LEFT")
    return HalGPIO::BTN_LEFT;
  if (name == "RIGHT")
    return HalGPIO::BTN_RIGHT;
  if (name == "UP")
    return HalGPIO::BTN_UP;
  if (name == "DOWN")
    return HalGPIO::BTN_DOWN;
  if (name == "P" || name == "POWER")
    return HalGPIO::BTN_POWER;
  return -1;
}

void initializeSyntheticEvents() {
  if (syntheticEventsInitialized)
    return;
  syntheticEventsInitialized = true;

  const char *script = std::getenv("CROSSPOINT_SIM_INPUT_SCRIPT");
  if (!script || script[0] == '\0')
    return;

  const std::string spec(script);
  size_t start = 0;
  while (start < spec.size()) {
    const size_t end = spec.find(';', start);
    const std::string item = spec.substr(
        start, end == std::string::npos ? std::string::npos : end - start);
    const size_t firstColon = item.find(':');
    const size_t secondColon = firstColon == std::string::npos
                                   ? std::string::npos
                                   : item.find(':', firstColon + 1);
    if (firstColon != std::string::npos) {
      const unsigned long atMs =
          std::strtoul(item.substr(0, firstColon).c_str(), nullptr, 10);
      const std::string key = uppercase(
          item.substr(firstColon + 1, secondColon == std::string::npos
                                          ? std::string::npos
                                          : secondColon - firstColon - 1));
      if (key == "QUIT") {
        syntheticEvents.push_back({atMs, SyntheticAction::Quit});
      } else if (key == "S" || key == "SLEEP") {
        syntheticEvents.push_back({atMs, SyntheticAction::Sleep});
      } else if (key == "HOME") {
        const unsigned long holdMs =
            secondColon == std::string::npos
                ? 80
                : std::strtoul(item.substr(secondColon + 1).c_str(), nullptr,
                               10);
        syntheticEvents.push_back({atMs, SyntheticAction::HomeDown});
        syntheticEvents.push_back({atMs + holdMs, SyntheticAction::HomeUp});
      } else if (key == "TYPE" && secondColon != std::string::npos) {
        // Everything after the second colon is the text, verbatim (so it may
        // contain ':' but not ';'), through decodeTypeEscapes.
        SyntheticEvent typed{atMs, SyntheticAction::TypeText};
        typed.text = decodeTypeEscapes(item.substr(secondColon + 1));
        syntheticEvents.push_back(std::move(typed));
      } else if (key == "QTAP" && secondColon != std::string::npos) {
        // QTAP:<BUTTON>[:<holdMs>] routes through HalGPIO::queueButtonTap —
        // the API the iOS read-aloud adapter turns pages with — so a
        // headless script pins that exact path, not just injectButton*.
        const std::string rest = item.substr(secondColon + 1);
        const size_t thirdColon = rest.find(':');
        const int button = namedButton(uppercase(
            thirdColon == std::string::npos ? rest : rest.substr(0, thirdColon)));
        if (button >= 0) {
          SyntheticEvent tap{atMs, SyntheticAction::QueuedTap, button};
          tap.holdMs = thirdColon == std::string::npos
                           ? 60
                           : std::strtoul(rest.substr(thirdColon + 1).c_str(),
                                          nullptr, 10);
          syntheticEvents.push_back(std::move(tap));
        }
      } else if ((key == "TAP" || key == "SWIPE") &&
                 secondColon != std::string::npos) {
        float x1 = 0.0f;
        float y1 = 0.0f;
        float x2 = 0.0f;
        float y2 = 0.0f;
        unsigned long duration = 0;
        const bool swipe = key == "SWIPE";
        if (parseTouchSpec(item.substr(secondColon + 1), x1, y1, x2, y2,
                           duration, swipe)) {
          syntheticEvents.push_back(
              {atMs, SyntheticAction::TouchDown, -1, x1, y1});
          syntheticEvents.push_back(
              {atMs + duration, SyntheticAction::TouchUp, -1, x2, y2});
        }
      } else {
        const int button = namedButton(key);
        if (button >= 0) {
          const unsigned long holdMs =
              secondColon == std::string::npos
                  ? 80
                  : std::strtoul(item.substr(secondColon + 1).c_str(), nullptr,
                                 10);
          syntheticEvents.push_back({atMs, SyntheticAction::KeyDown, button});
          syntheticEvents.push_back(
              {atMs + holdMs, SyntheticAction::KeyUp, button});
        }
      }
    }

    if (end == std::string::npos)
      break;
    start = end + 1;
  }

  std::sort(syntheticEvents.begin(), syntheticEvents.end(),
            [](const SyntheticEvent &a, const SyntheticEvent &b) {
              return a.atMs < b.atMs;
            });
}

void processSyntheticEvents() {
  initializeSyntheticEvents();
  const unsigned long now = millis();
  for (auto &event : syntheticEvents) {
    if (event.handled || event.atMs > now)
      continue;
    event.handled = true;
    switch (event.action) {
    case SyntheticAction::KeyDown:
      gpio.injectButtonDown(static_cast<uint8_t>(event.button));
      break;
    case SyntheticAction::KeyUp:
      gpio.injectButtonUp(static_cast<uint8_t>(event.button));
      break;
    case SyntheticAction::TouchDown:
      beginTouch(event.logicalNx, event.logicalNy);
      break;
    case SyntheticAction::TouchUp:
      endTouch(event.logicalNx, event.logicalNy);
      break;
    case SyntheticAction::HomeDown:
      beginHomeKey();
      break;
    case SyntheticAction::HomeUp:
      endHomeKey();
      break;
    case SyntheticAction::TypeText:
      gpio.injectTypedText(event.text.c_str());
      break;
    case SyntheticAction::Sleep:
      requestSimulatorSleep();
      break;
    case SyntheticAction::Quit:
      quitRequested.store(true);
      break;
    case SyntheticAction::QueuedTap:
      gpio.queueButtonTap(static_cast<uint8_t>(event.button), event.holdMs);
      break;
    }
  }
}

} // namespace

static void clearButtonState() {
  for (int i = 0; i < NUM_BUTTONS; i++) {
    pressedThisFrame[i] = false;
    releasedThisFrame[i] = false;
    buttonPressTime[i] = 0;
    syntheticButtonDown[i] = false;
  }
  {
    std::lock_guard<std::mutex> lock(typedTextMutex);
    typedTextBuffer.clear();
  }
  touchState = {};
  homeKeyDown = false;
  homeKeyPressedThisFrame = false;
  homeKeyTappedThisFrame = false;
  homeKeyLongPressedThisFrame = false;
  homeKeyLongFired = false;
  homeKeyPressedAt = 0;
}

static int scancodeToButton(SDL_Scancode sc) {
  for (int i = 0; i < NUM_BUTTONS; i++) {
    if (buttonScancode[i] == sc)
      return i;
  }
  return -1;
}

void HalGPIO::begin() {
#if defined(SIMULATOR_DEVICE_X4_PRO)
  _deviceType = DeviceType::X4;
  BoardConfig::selectDevice(BoardConfig::Board::XteinkX4Pro);
#elif defined(SIMULATOR_DEVICE_X3)
  _deviceType = DeviceType::X3;
  BoardConfig::selectDevice(BoardConfig::Board::XteinkX3);
#else
  _deviceType = DeviceType::X4;
  BoardConfig::selectDevice(BoardConfig::Board::XteinkX4);
#endif
}

bool HalGPIO::isXteinkDevice() const {
  // Match the firmware helper's narrower meaning: the runtime-detected C3
  // X3/X4 pair. X4 Pro is an Xteink product but uses its own S3 board profile.
  return BoardConfig::ACTIVE.board == BoardConfig::Board::XteinkX3 ||
         BoardConfig::ACTIVE.board == BoardConfig::Board::XteinkX4;
}

bool HalGPIO::hasEdgeSideButtons() const {
  return BoardConfig::ACTIVE.board == BoardConfig::Board::XteinkX3 ||
         BoardConfig::ACTIVE.board == BoardConfig::Board::XteinkX4Pro;
}

void HalGPIO::beginFrame() {
  // Clear the press/release edge latches once per frame. See update() for why
  // this is deliberately separate from the SDL poll.
  for (int i = 0; i < NUM_BUTTONS; i++) {
    pressedThisFrame[i] = false;
    releasedThisFrame[i] = false;
  }
  touchState.pressedThisFrame = false;
  touchState.releasedThisFrame = false;
  touchState.activityThisFrame = false;
  homeKeyPressedThisFrame = false;
  homeKeyTappedThisFrame = false;
  homeKeyLongPressedThisFrame = false;
}

void HalGPIO::update() {
  // Per-frame press/release edges are intentionally NOT cleared here; that
  // happens once per frame in beginFrame(). The firmware calls update() several
  // times within a single frame (e.g. CrossPointWebServerActivity polls input
  // between handleClient() bursts, on top of the top-of-loop gpio.update() in
  // main.cpp). If edges were cleared on every update(), a key press drained by
  // an earlier update() would be wiped before a later update()'s wasPressed()
  // check could observe it — which made Back/Exit require repeated presses.
  // Latching edges for the whole frame keeps wasPressed() stable across all
  // update() calls in that frame, matching the on-device InputManager.

  // Fire queued synthetic taps here, inside update(), so their edges land in
  // the same window real input's do (see queueButtonTap in HalGPIO.h — an
  // edge injected after loop() is wiped by the next beginFrame() unseen).
  if (!pendingButtonTaps.empty()) {
    const unsigned long now = SDL_GetTicks();
    for (auto it = pendingButtonTaps.begin(); it != pendingButtonTaps.end();) {
      if (!it->downSent) {
        injectButtonDown(it->button);
        it->downSent = true;
        it->upAtTicks = now + it->holdMs;
        ++it;
      } else if (now >= it->upAtTicks) {
        injectButtonUp(it->button);
        it = pendingButtonTaps.erase(it);
      } else {
        ++it;
      }
    }
  }

  // HalGPIO owns all SDL event polling so keyboard and quit events are never
  // split between two callers (HalDisplay::presentIfNeeded only renders).
  SDL_Event e;
  while (SDL_PollEvent(&e) != 0) {
    if (e.type == SDL_EVENT_QUIT) {
      quitRequested.store(true);
      continue;
    }

    // Text entry claims the keyboard first, before the scancode→button map
    // gets a look at it. Without this the letters of the password ARE the
    // button map: P powers off, S sleeps, H is Home. Escape, the arrows and
    // Return fall through (scancodeSurvivesTextEntry).
    if (textEntryActive.load()) {
      if (e.type == SDL_EVENT_TEXT_INPUT) {
        queueTypedBytes(e.text.text, e.text.text ? SDL_strlen(e.text.text) : 0);
        continue;
      }
      // Cmd+Return / Ctrl+Return is the host typist's commit. Plain Return is
      // BTN_CONFIRM and belongs to the on-screen keyboard's Select -- see the
      // note on scancodeSurvivesTextEntry for why it may not be swallowed here.
      // Checked BEFORE the survives-gate, which now lets plain Return through.
      if (e.type == SDL_EVENT_KEY_DOWN && !e.key.repeat &&
          scancodeIsEnter(e.key.scancode) &&
          (e.key.mod & (SDL_KMOD_GUI | SDL_KMOD_CTRL)) != 0) {
        const char c = HalGPIO::TYPED_COMMIT;
        queueTypedBytes(&c, 1);
        continue;
      }
      if ((e.type == SDL_EVENT_KEY_DOWN || e.type == SDL_EVENT_KEY_UP) &&
          !scancodeSurvivesTextEntry(e.key.scancode)) {
        if (e.type == SDL_EVENT_KEY_DOWN) {
          // Backspace deliberately honours key repeat -- holding it to erase a
          // word is the whole point.
          if (e.key.scancode == SDL_SCANCODE_BACKSPACE) {
            const char c = HalGPIO::TYPED_BACKSPACE;
            queueTypedBytes(&c, 1);
          }
        }
        // Everything else is swallowed: its character arrives separately as
        // SDL_EVENT_TEXT_INPUT, already composed (dead keys, IME, an iPhone
        // keyboard's autocorrect replacement).
        continue;
      }
    }

    if (e.type == SDL_EVENT_KEY_DOWN && !e.key.repeat) {
      if (e.key.scancode == HOME_KEY_SCANCODE) {
        beginHomeKey();
        continue;
      }
      if (e.key.scancode == SIMULATOR_SLEEP_SCANCODE) {
        requestSimulatorSleep();
        continue;
      }
      int btn = scancodeToButton(e.key.scancode);
      if (btn >= 0) {
        pressedThisFrame[btn] = true;
        buttonPressTime[btn] = SDL_GetTicks();
      }
    } else if (e.type == SDL_EVENT_KEY_UP) {
      if (e.key.scancode == HOME_KEY_SCANCODE) {
        endHomeKey();
        continue;
      }
      int btn = scancodeToButton(e.key.scancode);
      if (btn >= 0) {
        releasedThisFrame[btn] = true;
        if (buttonPressTime[btn] > 0)
          lastReleasedSpan = SDL_GetTicks() - buttonPressTime[btn];
        // Clear it: a stale timestamp let a release-then-much-later level read
        // report a hold of however long ago the press was. Only
        // clearButtonState() used to reset this, at sleep entry.
        buttonPressTime[btn] = 0;
      }
    } else if (e.type == SDL_EVENT_MOUSE_BUTTON_DOWN &&
               e.button.button == SDL_BUTTON_LEFT) {
      const float logicalNx =
          static_cast<float>(e.button.x) /
          std::max(1, static_cast<int>(renderer.getScreenWidth()) - 1);
      const float logicalNy =
          static_cast<float>(e.button.y) /
          std::max(1, static_cast<int>(renderer.getScreenHeight()) - 1);
      beginTouch(logicalNx, logicalNy);
    } else if (e.type == SDL_EVENT_MOUSE_MOTION && touchState.down) {
      const float logicalNx =
          static_cast<float>(e.motion.x) /
          std::max(1, static_cast<int>(renderer.getScreenWidth()) - 1);
      const float logicalNy =
          static_cast<float>(e.motion.y) /
          std::max(1, static_cast<int>(renderer.getScreenHeight()) - 1);
      moveTouch(logicalNx, logicalNy);
    } else if (e.type == SDL_EVENT_MOUSE_BUTTON_UP &&
               e.button.button == SDL_BUTTON_LEFT) {
      const float logicalNx =
          static_cast<float>(e.button.x) /
          std::max(1, static_cast<int>(renderer.getScreenWidth()) - 1);
      const float logicalNy =
          static_cast<float>(e.button.y) /
          std::max(1, static_cast<int>(renderer.getScreenHeight()) - 1);
      endTouch(logicalNx, logicalNy);
    }
  }
  processSyntheticEvents();
  updateHomeKeyHold();
}

bool HalGPIO::isPressed(uint8_t buttonIndex) const {
  if (buttonIndex >= NUM_BUTTONS)
    return false;
  // SDL3 returns const bool* here; SDL2 returned const Uint8*.
  const bool *state = SDL_GetKeyboardState(NULL);
  // Same rule as the event path in update(): while a text field is open the
  // keyboard belongs to the text, so a held letter must not read as a held
  // button either. The on-screen pad (syntheticButtonDown) is unaffected --
  // it never went through a scancode.
  const bool keyboardOwnsButton =
      !textEntryActive.load() ||
      scancodeSurvivesTextEntry(buttonScancode[buttonIndex]);
  return (keyboardOwnsButton && state[buttonScancode[buttonIndex]]) ||
         syntheticButtonDown[buttonIndex];
}

bool HalGPIO::wasPressed(uint8_t buttonIndex) const {
  if (buttonIndex >= NUM_BUTTONS)
    return false;
  return pressedThisFrame[buttonIndex];
}

bool HalGPIO::wasReleased(uint8_t buttonIndex) const {
  if (buttonIndex >= NUM_BUTTONS)
    return false;
  return releasedThisFrame[buttonIndex];
}

bool HalGPIO::wasAnyPressed() const {
  for (int i = 0; i < NUM_BUTTONS; i++) {
    if (pressedThisFrame[i])
      return true;
  }
  return false;
}

bool HalGPIO::wasAnyReleased() const {
  for (int i = 0; i < NUM_BUTTONS; i++) {
    if (releasedThisFrame[i])
      return true;
  }
  return false;
}

void HalGPIO::injectButtonDown(uint8_t buttonIndex) {
  if (buttonIndex >= NUM_BUTTONS)
    return;
  pressedThisFrame[buttonIndex] = true;
  // The level bit is the whole point of this entry point: SDL_GetKeyboardState()
  // is never written for anything the host injects, so isPressed(),
  // getHeldTime() and getPowerButtonHeldTime() have nothing else to read.
  syntheticButtonDown[buttonIndex] = true;
  syntheticWakeEdge.store(true);
  // Held-time calculations use SDL_GetTicks() for real keyboard events;
  // injected presses must use the same clock origin to avoid unsigned
  // underflow being mistaken for an immediate long press.
  buttonPressTime[buttonIndex] = SDL_GetTicks();
}

void HalGPIO::injectButtonUp(uint8_t buttonIndex) {
  if (buttonIndex >= NUM_BUTTONS)
    return;
  releasedThisFrame[buttonIndex] = true;
  syntheticButtonDown[buttonIndex] = false;
  if (buttonPressTime[buttonIndex] > 0)
    lastReleasedSpan = SDL_GetTicks() - buttonPressTime[buttonIndex];
  buttonPressTime[buttonIndex] = 0;  // see the note in update()'s key-up arm
}

void HalGPIO::setTextEntryActive(bool active) {
  const bool was = textEntryActive.exchange(active);
  if (was == active)
    return;
  // Both edges drop whatever is queued. On the rising edge that discards
  // anything a mistimed host typed before the field existed; on the falling
  // edge it stops the tail of one entry (the characters that arrived in the
  // same frame as the commit) leaking into the next field that opens.
  {
    std::lock_guard<std::mutex> lock(typedTextMutex);
    typedTextBuffer.clear();
  }
  SDL_Log("[TEXT] text entry %s", active ? "active" : "inactive");
}

bool HalGPIO::isTextEntryActive() const { return textEntryActive.load(); }

bool HalGPIO::consumeTypedText(std::string &out) {
  std::lock_guard<std::mutex> lock(typedTextMutex);
  if (typedTextBuffer.empty())
    return false;
  out.assign(typedTextBuffer);
  typedTextBuffer.clear();
  return true;
}

void HalGPIO::injectTypedText(const char *utf8) {
  if (!utf8 || !*utf8)
    return;
  if (!textEntryActive.load()) {
    // Loud on purpose: a script that types before the field opens would
    // otherwise look like a firmware bug rather than a timing bug.
    SDL_Log("[TEXT] dropped injected text (no text field open): \"%s\"", utf8);
    return;
  }
  queueTypedBytes(utf8, SDL_strlen(utf8));
}

void HalGPIO::pumpHostTextInput() {
  static bool applied = false;
  const bool want = textEntryActive.load();
  if (want == applied)
    return;
  SDL_Window *window = simulatorWindow();
  if (!window)
    return; // before the first HalDisplay::begin(); retried next frame
  applied = want;
  if (want) {
    // On a phone this is what raises the software keyboard; a paired Bluetooth
    // keyboard suppresses that itself and types straight through. On desktop
    // it is what makes SDL emit SDL_EVENT_TEXT_INPUT at all.
    SDL_StartTextInput(window);
    // Both flags are worth having in the log, because together they decide
    // which keyboard the owner actually gets -- and because SDL's own
    // software-keyboard backspace is conditional on the second one being
    // FALSE (SDL_uikitviewcontroller.m's textFieldTextDidChange only
    // synthesises SDL_SCANCODE_BACKSPACE when !SDL_HasKeyboard(), on the
    // assumption that a real keyboard would have sent the key itself). An iOS
    // Simulator reports a keyboard whether or not one is attached, so a
    // soft-keyboard Delete does nothing there. See ios/README.md.
    SDL_Log("[TEXT] host text input started (screen keyboard support %d, "
            "keyboard attached %d)",
            SDL_HasScreenKeyboardSupport() ? 1 : 0, SDL_HasKeyboard() ? 1 : 0);
  } else {
    SDL_StopTextInput(window);
  }
}

// CROSSPOINT_SIM_READALOUD_DUMP=1 turns capture on for the DESKTOP build and
// prints what an assistive technology would be handed, one line per element.
//
// It exists because the iOS builder is the one piece of this path that cannot
// be run off-device, and it was wrong in a way nobody could see: labels arrived
// starting mid-word. Reading the .mm and reasoning about it produced two wrong
// fixes; this prints the answer against a real book in one run.
//
// Still ONE consumer per build -- this is the desktop's, and the iOS adapter is
// the phone's. They are never both compiled in.
static bool readAloudDumpEnabled() {
  static const bool on = [] {
    const char *v = std::getenv("CROSSPOINT_SIM_READALOUD_DUMP");
    return v != nullptr && v[0] == '1';
  }();
  return on;
}

bool HalGPIO::readAloudCaptureWanted() const {
  return readAloudDumpEnabled() || readAloudChannel.wanted();
}

void HalGPIO::publishReadAloudPage(const char *utf8, size_t utf8Len,
                                   const ReadAloudWordRect *rects,
                                   size_t rectCount) {
  readAloudChannel.publish(utf8, utf8Len, rects, rectCount);
  if (!readAloudDumpEnabled())
    return;
  if (utf8 == nullptr) {
    SDL_Log("[A11Y-DUMP] page cleared");
    return;
  }
  const std::string text(utf8, utf8Len);
  const std::vector<ReadAloudWordRect> v(rects ? rects : nullptr,
                                         rects ? rects + rectCount : nullptr);
  const auto lines = readaloud::groupIntoLines(text, v);
  SDL_Log("[A11Y-DUMP] %zu rects -> %zu line elements, %zu bytes of text",
          rectCount, lines.size(), text.size());
  for (size_t i = 0; i < lines.size(); i++) {
    const auto &l = lines[i];
    SDL_Log("[A11Y-DUMP]   [%02zu] bytes %u..%u at (%u,%u %ux%u) \"%s\"", i,
            l.byteOffset, l.byteEnd, l.x, l.y, l.w, l.h, l.text.c_str());
  }
}

void HalGPIO::setReadAloudCaptureWanted(bool wanted) {
  readAloudChannel.setWanted(wanted);
}

bool HalGPIO::consumeReadAloudPage(ReadAloudPage &out) {
  return readAloudChannel.consume(out);
}

void HalGPIO::queueButtonTap(uint8_t buttonIndex, unsigned long holdMs) {
  if (buttonIndex >= NUM_BUTTONS)
    return;
  pendingButtonTaps.push_back({buttonIndex, holdMs});
}

unsigned long HalGPIO::getHeldTime() const {
  // While a button is held: longest held time among the pressed buttons.
  // Nothing held: span of the last completed press, matching the device's
  // InputManager (buttonPressFinish - buttonPressStart survives the release).
  unsigned long now = SDL_GetTicks();
  unsigned long maxHeld = 0;
  bool anyPressed = false;
  // SDL3 returns const bool* here; SDL2 returned const Uint8*.
  const bool *state = SDL_GetKeyboardState(NULL);
  const bool textOwnsKeyboard = textEntryActive.load();
  for (int i = 0; i < NUM_BUTTONS; i++) {
    // Same rule as isPressed(): while a text field is open a held letter is
    // text, not a held button. Without this, typing a word containing 'p' read
    // as POWER being held and fired the long-press power-off.
    const bool keyboardOwnsButton =
        !textOwnsKeyboard || scancodeSurvivesTextEntry(buttonScancode[i]);
    if (((keyboardOwnsButton && state[buttonScancode[i]]) || syntheticButtonDown[i]) &&
        buttonPressTime[i] > 0) {
      anyPressed = true;
      unsigned long held = now - buttonPressTime[i];
      if (held > maxHeld)
        maxHeld = held;
    }
  }
  if (!anyPressed)
    return lastReleasedSpan;
  return maxHeld;
}

unsigned long HalGPIO::getPowerButtonHeldTime() const {
  // SDL3 returns const bool* here; SDL2 returned const Uint8*.
  const bool *state = SDL_GetKeyboardState(NULL);
  // Same rule as isPressed(): POWER's scancode is 'p' on the host keyboard, so
  // while a text field is open it belongs to the text. The on-screen pad
  // (syntheticButtonDown) never went through a scancode and is unaffected.
  const bool keyboardOwnsPower =
      !textEntryActive.load() ||
      scancodeSurvivesTextEntry(buttonScancode[BTN_POWER]);
  if ((!(keyboardOwnsPower && state[buttonScancode[BTN_POWER]]) &&
       !syntheticButtonDown[BTN_POWER]) ||
      buttonPressTime[BTN_POWER] == 0)
    return 0;
  return SDL_GetTicks() - buttonPressTime[BTN_POWER];
}

bool HalGPIO::hasTouch() const { return BoardConfig::hasTouch(); }

bool HalGPIO::hasHomeKey() const { return BoardConfig::hasHomeKey(); }

bool HalGPIO::wasHomeKeyPressed() const { return homeKeyPressedThisFrame; }

bool HalGPIO::wasHomeKeyTapped() const { return homeKeyTappedThisFrame; }

bool HalGPIO::wasHomeKeyLongPressed() const {
  return homeKeyLongPressedThisFrame;
}

bool HalGPIO::wasTouchTap(float &nx, float &ny) const {
  if (!touchState.releasedThisFrame || touchState.movedBeyondTapSlop)
    return false;
  nx = touchState.startNx;
  ny = touchState.startNy;
  return true;
}

bool HalGPIO::wasTouchDown(float &nx, float &ny) const {
  if (!touchState.pressedThisFrame)
    return false;
  nx = touchState.startNx;
  ny = touchState.startNy;
  return true;
}

bool HalGPIO::wasTouchReleased() const { return touchState.releasedThisFrame; }

bool HalGPIO::isTouchTapCandidate(float &nx, float &ny,
                                  unsigned long &heldMs) const {
  if (!touchState.down || touchState.movedBeyondTapSlop) {
    heldMs = 0;
    return false;
  }
  nx = touchState.startNx;
  ny = touchState.startNy;
  heldMs = SDL_GetTicks() - touchState.pressedAt;
  return true;
}

bool HalGPIO::isTouchHeldAt(float &nx, float &ny) const {
  if (!touchState.down)
    return false;
  nx = touchState.currentNx;
  ny = touchState.currentNy;
  return true;
}

unsigned long HalGPIO::lastTouchHeldMs() const { return touchState.lastHeldMs; }

bool HalGPIO::wasSwipe(float &nxStart, float &nyStart, float &nxEnd,
                       float &nyEnd) const {
  if (!touchState.releasedThisFrame ||
      touchState.lastHeldMs > TOUCH_SWIPE_MAX_MS)
    return false;
  const float dx =
      (touchState.currentNx - touchState.startNx) * HalDisplay::DISPLAY_WIDTH;
  const float dy =
      (touchState.currentNy - touchState.startNy) * HalDisplay::DISPLAY_HEIGHT;
  if (std::abs(dx) < TOUCH_SWIPE_MIN_PX && std::abs(dy) < TOUCH_SWIPE_MIN_PX)
    return false;
  nxStart = touchState.startNx;
  nyStart = touchState.startNy;
  nxEnd = touchState.currentNx;
  nyEnd = touchState.currentNy;
  return true;
}

bool HalGPIO::wasTouchActivity() const { return touchState.activityThisFrame; }
void HalGPIO::setSharedConfirmPowerShortPressEmitsPower(bool /*enabled*/) {}

bool HalGPIO::consumeSimulatorSleepRequest() {
  const bool requested = simulatorSleepRequested;
  simulatorSleepRequested = false;
  return requested;
}

HalGPIO::WakeupReason HalGPIO::getWakeupReason() const {
  if (SimulatorLifecycle::consumeWakeReason() ==
      SimulatorLifecycle::WakeReason::PowerButton) {
    return WakeupReason::PowerButton;
  }
  return WakeupReason::Other;
}
// Always-connected hid the unplug repaint and drew the charging bolt forever
// (S-001). CROSSPOINT_SIM_USB=0 reports unplugged; unset keeps the old true.
bool HalGPIO::isUsbConnected() const {
  static const bool connected = [] {
    const char *v = std::getenv("CROSSPOINT_SIM_USB");
    return !(v && v[0] == '0' && v[1] == '\0');
  }();
  return connected;
}
bool HalGPIO::wasUsbStateChanged() const { return false; }
void HalGPIO::startDeepSleep() {
  clearButtonState();
  // The press that put the device to sleep set the wake edge on its way down;
  // consume it so entering sleep does not instantly wake.
  syntheticWakeEdge.store(false);

  while (true) {
    processSyntheticEvents();
    if (quitRequested.load())
      return;
    // EDGE, not level: syntheticButtonDown[] can already be false again if the
    // tap's down and up both arrived in this iteration's pump (see the latch's
    // declaration comment). Any injected press since sleep began is a wake.
    if (syntheticWakeEdge.exchange(false)) {
      clearButtonState();
      SimulatorLifecycle::rebootAsPowerWake();
    }

    SDL_Event e;
    while (SDL_PollEvent(&e) != 0) {
      if (e.type == SDL_EVENT_QUIT) {
        quitRequested.store(true);
        return;
      }

      if (e.type == SDL_EVENT_KEY_DOWN && !e.key.repeat &&
          scancodeToButton(e.key.scancode) >= 0) {
        clearButtonState();
        SimulatorLifecycle::rebootAsPowerWake();
      }
    }

    SDL_Delay(10);
  }
}
bool HalGPIO::verifyPowerButtonWakeup(uint16_t /*requiredDurationMs*/,
                                      bool /*shortPressAllowed*/) {
  return true;
}

HalGPIO gpio;
