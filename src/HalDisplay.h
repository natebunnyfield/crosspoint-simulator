#pragma once
#include <Arduino.h>
#include <EInkDisplay.h>

#include <atomic>

// Supersampling factor between the LOGICAL screen coordinate space the firmware
// draws in and the PHYSICAL framebuffer this HAL owns. Mirrors the firmware
// header's macro (which defaults to 1); here it is >1 so text can be rasterised
// at the host panel's real pixel density.
//
// LAYOUT IS UNAFFECTED BY DESIGN: GfxRenderer::getScreenWidth()/getScreenHeight()
// still report 528x792 on X3, every advance/kern/line-break still comes from the
// 1x .cpfont tables, and only the pixel-write layer multiplies up. Raising this
// must therefore never move a line break; if it does, something started reading
// panel geometry as layout input.
//
// Cost at 2: framebuffer 792*528/8 = 52,272 B -> 1584*1056/8 = 209,088 B, and
// HalDisplay.cpp holds four of those (bwBase + lsb + msb + frameBufferStorage)
// plus an ARGB present buffer of DISPLAY_WIDTH*DISPLAY_HEIGHT*4 = 6.7 MB.
// Defaults to 1 -- the simulator mirrors the device unless a build opts in.
// Supersampling is requested explicitly with -DCROSSPOINT_RENDER_SCALE=2:
// [env:simulator] passes it for the desktop build, ios/CMakeLists.txt for the
// app. A single default of 2 here meant every consumer silently paid 4x the
// framebuffer and ~2.5x the page render time, including runs that only wanted
// to check firmware behavior against the real panel geometry.
#ifndef CROSSPOINT_RENDER_SCALE
#define CROSSPOINT_RENDER_SCALE 1
#endif

// cp::renderScale() / cp::setRenderScale(). Lives in the firmware so the
// renderer and this HAL agree on one definition; see RenderScale.h for why the
// factor is latched at startup rather than live.
#include <RenderScale.h>

class HalDisplay {
public:
  // Constructor with pin configuration
  HalDisplay();

  // Destructor
  ~HalDisplay();

  // Refresh modes
  enum RefreshMode {
    FULL_REFRESH, // Full refresh with complete waveform
    HALF_REFRESH, // Half refresh (1720ms) - balanced quality and speed
    FAST_REFRESH  // Fast refresh using custom LUT
  };

  // Initialize the display hardware and driver
  void begin();
  void begin(bool seamless);

  // Display dimensions, in PHYSICAL framebuffer pixels. At
  // CROSSPOINT_RENDER_SCALE > 1 these are a multiple of the panel the firmware
  // believes it is driving; the logical panel the firmware lays out against is
  // still EInkDisplay::DISPLAY_WIDTH x DISPLAY_HEIGHT and is what
  // GfxRenderer::getScreenWidth()/getScreenHeight() report.
  // THE CEILING, NOT NECESSARILY THE CURRENT GEOMETRY. These are constexpr
  // because every static allocation in HalDisplay.cpp is sized from them --
  // four full framebuffers plus the ARGB present buffer -- and an array bound
  // cannot move after the compiler has run.
  //
  // The factor this process is ACTUALLY rendering at is cp::renderScale(),
  // latched once at startup from the owner's setting (see RenderScale.h), and
  // it may be anything from 1 up to RENDER_SCALE. Use the active*() accessors
  // below for anything that walks the framebuffer, sizes the SDL texture or
  // converts between logical and device coordinates; use these only to size
  // storage. Getting that backwards at scale 2 on a ceiling-3 build reads
  // 2.25x past the live picture and shows the buffer's stale tail.
  static constexpr int RENDER_SCALE = CROSSPOINT_RENDER_SCALE;
  static constexpr uint16_t DISPLAY_WIDTH = EInkDisplay::DISPLAY_WIDTH * RENDER_SCALE;
  static constexpr uint16_t DISPLAY_HEIGHT = EInkDisplay::DISPLAY_HEIGHT * RENDER_SCALE;
  static constexpr uint16_t DISPLAY_WIDTH_BYTES = DISPLAY_WIDTH / 8;
  static constexpr uint32_t BUFFER_SIZE =
      static_cast<uint32_t>(DISPLAY_WIDTH_BYTES) * DISPLAY_HEIGHT;

  // Framebuffer geometry at the ACTIVE render scale. Equal to the constants
  // above whenever the owner is running at the ceiling, which is the default.
  static uint16_t activeWidth() {
    return static_cast<uint16_t>(EInkDisplay::DISPLAY_WIDTH * cp::renderScale());
  }
  static uint16_t activeHeight() {
    return static_cast<uint16_t>(EInkDisplay::DISPLAY_HEIGHT * cp::renderScale());
  }
  static uint16_t activeWidthBytes() { return static_cast<uint16_t>(activeWidth() / 8); }
  static uint32_t activeBufferSize() {
    return static_cast<uint32_t>(activeWidthBytes()) * activeHeight();
  }

  // Logical panel geometry (what the firmware would see on real hardware).
  // Independent of the render scale by construction, which is why the iOS
  // coordinate mapping in CrossPointAccessibility.mm and CrossPointReadAloud.mm
  // is spelled in these and needs no change when the scale moves.
  static constexpr uint16_t LOGICAL_WIDTH = EInkDisplay::DISPLAY_WIDTH;
  static constexpr uint16_t LOGICAL_HEIGHT = EInkDisplay::DISPLAY_HEIGHT;

  // Frame buffer operations
  void clearScreen(uint8_t color = 0xFF) const;
  void drawImage(const uint8_t *imageData, uint16_t x, uint16_t y, uint16_t w,
                 uint16_t h, bool fromProgmem = false) const;
  void drawImageTransparent(const uint8_t *imageData, uint16_t x, uint16_t y,
                            uint16_t w, uint16_t h,
                            bool fromProgmem = false) const;

  // Persistent black/white polarity used by the X4 Pro frontlight panel.
  void setInverted(bool inverted);
  bool toggleInverted();
  bool isInverted() const;

  void displayBuffer(RefreshMode mode = RefreshMode::FAST_REFRESH,
                     bool turnOffScreen = false);
  void displayBufferAsync(RefreshMode mode = RefreshMode::FAST_REFRESH);
  void waitRefreshComplete();
  bool supportsAsyncRefresh() const;
  void displayWindow(int x, int y, int w, int h);
  void refreshDisplay(RefreshMode mode = RefreshMode::FAST_REFRESH,
                      bool turnOffScreen = false);
  void setBusyWaitSliceHook(bool (*)(int8_t, uint8_t)) {}

  // Power management
  void deepSleep();

  // Access to frame buffer
  uint8_t *getFrameBuffer() const;
  uint8_t *lendFrameBufferStorage(uint32_t *sizeOut);
  void returnFrameBufferStorage();

  // Runtime geometry passthrough
  uint16_t getDisplayWidth() const;
  uint16_t getDisplayHeight() const;
  uint16_t getDisplayWidthBytes() const;
  uint32_t getBufferSize() const;

  void displayGrayscaleBase(RefreshMode fallback = HALF_REFRESH,
                            bool turnOffScreen = false);
  void preconditionGrayscale();
  void preconditionGrayscale(uint16_t x, uint16_t y, uint16_t w, uint16_t h);

  void copyGrayscaleBuffers(const uint8_t *lsbBuffer, const uint8_t *msbBuffer);
  void copyGrayscaleLsbBuffers(const uint8_t *lsbBuffer);
  void copyGrayscaleMsbBuffers(const uint8_t *msbBuffer);
  void cleanupGrayscaleBuffers(const uint8_t *bwBuffer);

  void displayGrayBuffer(bool turnOffScreen = false,
                         const unsigned char *lut = nullptr,
                         bool factoryMode = false);

  // The simulator intentionally advertises strip grayscale support so host
  // builds exercise the same low-memory path as the device firmware, and so
  // streamed plane data can feed the same grayscale preview compositor as the
  // legacy full-frame API.
  void writeGrayscalePlaneStrip(bool lsbPlane, const uint8_t *rows,
                                uint16_t yStart, uint16_t numRows);
  bool supportsStripGrayscale() const;

  // Simulator only: call from main thread to push rendered pixels to SDL.
  // Suspend GPU work while the app is backgrounded.
  //
  // Read-aloud declares UIBackgroundModes:audio, so the process keeps running
  // with the screen locked -- and it turns pages while it reads. A page turn
  // renders, which sets pendingPresent, which would submit Metal work from the
  // background. Apple documents that as grounds for TERMINATION, and being
  // killed mid-chapter is worse than the feature is good.
  //
  // The pending flag is deliberately NOT cleared: the frame is still owed, and
  // setBackgrounded(false) re-arms it so the page the owner missed appears the
  // moment they unlock. Desktop never calls this and is unaffected.
  static void setBackgrounded(bool backgrounded);

  void presentIfNeeded();
  // Simulator only: returns true once a hard shutdown has been requested.
  bool shouldQuit() const;

private:
  EInkDisplay einkDisplay;
  // Atomic because polarity is written from the main thread (host appearance /
  // CROSSPOINT_SIM_DARK via SimulatorOverlay::setPanelDark) while the render
  // task reads it during framebuffer conversion. Private member only -- the
  // public surface above still mirrors the firmware HAL exactly.
  std::atomic<bool> inverted{false};
};

extern HalDisplay display;
