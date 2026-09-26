#pragma once

// E-INK MODE (spike 2026-09-25): the real e-paper panel's refresh behavior,
// drawn on the phone. Owner ruling 2026-09-25: "the full-refresh FLASH, GHOSTING
// that accumulates across partial refreshes, and a SHAKE to clear the ghosts".
// Full write-up, sources and measurements: docs/eink-mode-spike-2026-09-25.md.
//
// PURE AND HOST-TESTED (tests/eink_panel_test.cpp), on the same terms as every
// other surface model here: every failure mode is a wrong picture that
// compiles. No SDL, no clock, no I/O -- the caller passes time in.
//
// --- WHAT IS KEYED ON WHAT ---------------------------------------------------
//
// Nothing here invents a schedule. The firmware already asks for a refresh
// MODE on every paint (HalDisplay::refreshDisplay's argument, which this HAL
// used to discard): FAST is the partial page turn, HALF is the reader's
// ghost-clearing refresh every N pages (ReaderUtils.h displayWithRefreshCycle,
// SETTINGS.getRefreshFrequency()) and the sleep screen, FULL is the rare OEM
// full write. So:
//
//   FAST        -> a partial: no animation, and the page it replaced leaves a
//                  residue in the ghost plane.
//   HALF / FULL -> the waveform the panel would run, frame by frame, and the
//                  ghost plane is cleared.
//
// --- THE WAVEFORMS ARE THE X3's OWN, DECODED ---------------------------------
//
// Not a generic "invert, black, white" guess: the UC8253 banks the firmware
// actually loads on the X3 (freeink-sdk src/lut/Uc8253X3Luts.h) are transcribed
// below. Each LUT group is [level-select byte, TP_A, TP_B, TP_C, TP_D frame
// counts, repeat]; the level byte is four 2-bit codes, 00 = hold (VCOM),
// 01 = drive BLACK, 10 = drive WHITE (01 is what every white->black table
// carries, 10 every black->white one). The four transition tables are indexed
// by (old, new) pixel: WW, WB, BW, BB.
//
//   _full (FULL)  ww 4A: black 24, hold 4, white 14+10       DTM1 is filled
//                 wb 04: hold 28, black 14, hold 10, black 10  WHITE first, so
//                 every pixel is WW or WB -- the ink the page is ABOUT to show
//                 holds its old state while every paper pixel goes black. The
//                 visible frame is the NEW page in NEGATIVE, merged with the old
//                 ink, and then the page. That is the classic e-ink flash.
//   _half (HALF)  ww=bw AA: white 19+5; wb=bb 55: black 19+5; hold 1. A
//                 SCRUB: every pixel is driven to its target with no inversion
//                 at all. On the X3 the reader's periodic "full" refresh does
//                 NOT flash black; it pushes the ghosts out over half a second.
//   _fast (FAST)  changed pixels driven 18 frames, unchanged ones 2.
//
// The X4 (SSD1677) runs OTP sequences (0xD7 half, 0xF7 full) whose frames are
// not in any file here, so a non-X3 build uses the X3 _full program for both
// HALF and FULL. Documented, not measured; the search that found no X4 frames
// is docs/eink-mode-spike-2026-09-25.md §2a.
//
// --- THE OPTICS ---------------------------------------------------------------
//
// A pixel's reflectance moves toward the rail it is driven at, exponentially,
// with time constant kTauFrames; a hold leaves it where it is. That makes every
// frame an AFFINE function of the starting level per transition class, which is
// what keeps a 1.7-million-pixel frame to one multiply-add per pixel.
//
// FRAME PERIOD kFramePeriodMs = 20 (50 Hz). NOT decoded -- the PLL register
// value (0x09) was not mapped to a rate. Bounded above by a MEASURED figure:
// Uc8253X3Driver.cpp records a warm FAST refresh at 435 ms, and the fast bank
// is 19 frames, so a frame is at most 22.9 ms (the 435 includes the SPI
// transfer). At 20 ms the X3 full is 62 frames = 1240 ms and the scrub 25
// frames = 500 ms.
//
// --- GHOSTS, AND THE 7:1 FLOOR -------------------------------------------------
//
// First-order optics would make a residue DECAY on every later refresh. Real
// panels ACCUMULATE remnant (DC imbalance, particle history), which is exactly
// why the firmware schedules a clearing refresh at all. So the ghost plane is
// phenomenological, and says so: on every partial,
//
//   ghost = ghost * kKeep + residue(old -> new)
//
// where a pixel that went LIGHTER keeps a fraction kResidueToWhite of the ink
// it lost (the famous gray ghost of the previous page's text on paper) and one
// that went DARKER keeps kResidueToBlack of the paper (a slightly light stroke).
// The fractions are tuned, not measured (see residueToWhite for the reasoning
// and for why the first-order optics alone would draw no visible ghost).
//
// A ghost is a second image, so it is held under the floor BY CONSTRUCTION: the
// cap is computed from the live palette as the largest symmetric g for which
// level g (the lightest ghosted ink) against level 255-g (the darkest ghosted
// paper) still measures >= kContrastFloor. The page's surface fields are OFF in
// e-ink mode (an e-paper panel is not a printed sheet; FieldSelection.h), so
// the ghost is the only thing spending the paper's headroom.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>

namespace eink {

// GrayscalePreview's scale: 0 is full ink, 255 is paper.
constexpr int kInk = 0;
constexpr int kPaper = 255;

enum class Refresh : int { None = -1, Full = 0, Half = 1, Fast = 2 };

enum Drive : int8_t { B = -1, H = 0, W = 1 };  // drive black / hold / white

// Column order of Segment::drive: the UC8253 transition tables.
enum Cls { WW = 0, WB = 1, BW = 2, BB = 3 };

struct Segment {
  int frames;
  int8_t drive[4];
};

struct Program {
  const char *name;
  // DTM1 filled white before the write (the X3 _full path): the "old" half of
  // the class is then white for every pixel, whatever was on the glass.
  bool oldAssumedWhite;
  int nseg;
  Segment seg[6];
};

inline constexpr Program kX3Full = {
    "X3 _full (OEM)", true, 5,
    {{24, {B, H, H, W}},
     {4, {H, H, H, H}},
     {14, {W, B, W, B}},
     {10, {W, H, W, H}},
     {10, {H, B, H, B}}}};

inline constexpr Program kX3HalfScrub = {
    "X3 _half (scrub)", false, 2,
    {{24, {W, B, W, B}}, {1, {H, H, H, H}}}};

constexpr int totalFrames(const Program &p) {
  int n = 0;
  for (int i = 0; i < p.nseg; i++) n += p.seg[i].frames;
  return n;
}

constexpr double kTauFrames = 4.0;
constexpr int kFramePeriodMs = 20;
constexpr int kFastDriveFrames = 18;  // _fast: 14 + 4 frames on a changed pixel

// Ghost dynamics (see header). kKeep is per partial refresh.
// The first-order optics above would leave exp(-18/4) = 1.1% of a full swing
// after the fast bank's 18 drive frames -- about 3 levels, invisible. Real
// panels ghost harder than that, which is the remnant this term stands for;
// 3% per partial (7.6 levels) with 8% forgotten per partial saturates at the
// palette's cap after four or five turns over the same spot, which is the
// "builds up over a few pages" the owner described. TUNED, NOT MEASURED.
constexpr double kKeep = 0.92;
inline double residueToWhite() { return 0.030; }
constexpr double kResidueToBlack = 0.015;
// The largest ghost the design ever wants, in levels, before the floor caps it.
constexpr int kDesignCapLevels = 26;
constexpr double kContrastFloor = 7.0;

// Ghost plane fixed point: 1/16 level.
constexpr int kGhostScale = 16;

inline const Program &programFor(Refresh r, bool isX3) {
  if (r == Refresh::Half && isX3) return kX3HalfScrub;
  return kX3Full;
}

// --- luminance from the ARGB ramp -------------------------------------------
inline double srgbToLinear(int c8) {
  const double c = c8 / 255.0;
  return c <= 0.04045 ? c / 12.92 : std::pow((c + 0.055) / 1.055, 2.4);
}
inline double luminanceArgb(uint32_t argb) {
  return 0.2126 * srgbToLinear((argb >> 16) & 0xFF) +
         0.7152 * srgbToLinear((argb >> 8) & 0xFF) +
         0.0722 * srgbToLinear(argb & 0xFF);
}
inline double contrast(uint32_t a, uint32_t b) {
  double la = luminanceArgb(a), lb = luminanceArgb(b);
  if (la < lb) std::swap(la, lb);
  return (la + 0.05) / (lb + 0.05);
}

// The ghost cap for this palette: the largest g <= kDesignCapLevels such that
// the lightest ghosted ink (level g) against the darkest ghosted paper (level
// 255 - g) measures >= floor. Returns 0 when the bare palette is already under
// the floor -- then no ghost is drawn at all, which is the only honest answer.
inline int ghostCapLevels(const uint32_t lut[256], double floor = kContrastFloor) {
  int cap = 0;
  for (int g = 0; g <= kDesignCapLevels; g++) {
    if (contrast(lut[g], lut[255 - g]) >= floor) cap = g;
    else break;
  }
  return cap;
}

// The affine map a pixel of class `c` starting at level s0 is under after
// `frames` frames of program p:  s = a * s0 + b.
struct Affine {
  double a = 1.0, b = 0.0;
};
inline Affine affineAt(const Program &p, int c, int frames) {
  const double r = std::exp(-1.0 / kTauFrames);
  Affine m;
  int left = frames;
  for (int i = 0; i < p.nseg && left > 0; i++) {
    const int n = std::min(left, p.seg[i].frames);
    left -= n;
    const int d = p.seg[i].drive[c];
    if (d == H) continue;
    const double T = d == W ? kPaper : kInk;
    const double k = std::pow(r, n);
    // s' = T + (s - T) k  = k s + T (1 - k)
    m.a = k * m.a;
    m.b = k * m.b + T * (1.0 - k);
  }
  return m;
}

inline int classOf(bool oldWhite, bool newWhite) {
  return oldWhite ? (newWhite ? WW : WB) : (newWhite ? BW : BB);
}

// --- THE PANEL ----------------------------------------------------------------
//
// Owned by HalDisplay.cpp, touched only under pixelBufMutex. Level images are
// the panel's own (framebuffer pixels, rotation not applied).
class Panel {
 public:
  // Called on every level write while e-ink mode is live on a light page.
  // `levels` is the page as the firmware drew it; `transition` is the refresh
  // the firmware asked for (None for a compose/reconvert of the SAME page).
  // Writes the displayed page -- levels plus ghost -- through `lut` into `out`.
  void onLevels(const uint8_t *levels, int w, int h, Refresh transition,
                const uint32_t lut[256], uint64_t nowMs, bool isX3,
                uint32_t *out) {
    const size_t n = static_cast<size_t>(w) * h;
    const bool fresh = !valid_ || w != w_ || h != h_;
    if (fresh) reset(w, h);
    cap_ = ghostCapLevels(lut);
    std::memcpy(lut_, lut, sizeof lut_);
    if (!fresh && transition == Refresh::Fast) {
      accumulate(levels, n);
    } else if (!fresh && (transition == Refresh::Half ||
                          transition == Refresh::Full)) {
      // FROM THE OLD PAGE: prev_ still holds it here (it is overwritten two
      // lines down). Passing `levels` started the waveform from the NEW page,
      // so the glass jumped first and then flashed unchanged content, and on
      // HALF no changed pixel was ever driven (adversarial review, build 213).
      startFlash(prev_.data(), n, programFor(transition, isX3), nowMs);
    }
    std::memcpy(prev_.data(), levels, n);
    if (flashActive_) std::memcpy(flashNew_.data(), levels, n);
    write(levels, n, out);
  }

  // A host-requested full refresh (the shake): the panel runs its full
  // waveform over the page it is already showing, and the ghosts go. `out`
  // receives the settled (ghost-free) page, which is what presents once the
  // flash is over. Returns false when there is no page to refresh.
  bool requestFull(uint64_t nowMs, uint32_t *out) {
    if (!valid_) return false;
    const size_t n = static_cast<size_t>(w_) * h_;
    startFlash(prev_.data(), n, kX3Full, nowMs);
    std::memcpy(flashNew_.data(), prev_.data(), n);
    write(prev_.data(), n, out);
    return true;
  }

  // Render the flash frame due at nowMs into `out`. Returns 1 when a NEW frame
  // was written, 0 when the due frame is the one already written, and -1 when
  // no flash is running (including the call that ends one: the caller then
  // presents the settled page it already has).
  int flashFrame(uint64_t nowMs, uint32_t *out) {
    if (!flashActive_) return -1;
    const int total = totalFrames(*prog_);
    const int f = static_cast<int>((nowMs - flashStartMs_) / kFramePeriodMs);
    if (f >= total) {
      flashActive_ = false;
      lastFrame_ = -1;
      return -1;
    }
    if (f == lastFrame_) return 0;
    lastFrame_ = f;
    // Every pixel's frame is a function of (class, starting level) only, so
    // the frame is 4 x 256 table entries and one lookup per pixel -- the
    // per-pixel affine in doubles cost 14 ms a frame at 2x, this ~2.
    uint32_t tab[4][256];
    for (int c = 0; c < 4; c++) {
      const Affine m = affineAt(*prog_, c, f);
      for (int s0 = 0; s0 < 256; s0++) {
        const double s = m.a * s0 + m.b;
        tab[c][s0] = lut_[static_cast<uint8_t>(
            std::clamp(static_cast<int>(s + 0.5), 0, 255))];
      }
    }
    const size_t n = static_cast<size_t>(w_) * h_;
    const bool oldAllW = prog_->oldAssumedWhite;
    for (size_t i = 0; i < n; i++) {
      const uint8_t o = flashOld_[i];
      const int c = classOf(oldAllW || o >= 128, flashNew_[i] >= 128);
      out[i] = tab[c][o];
    }
    return 1;
  }

  // Abandon a running sequence; the caller presents the settled page.
  void endFlash() {
    flashActive_ = false;
    lastFrame_ = -1;
  }
  bool flashActive() const { return flashActive_; }
  // The level the running waveform started pixel i from (tests).
  uint8_t flashStartLevel(size_t i) const { return flashOld_[i]; }
  int cap() const { return cap_; }
  // The ghost at pixel i, in levels (signed; negative = darker than the page).
  double ghostAt(size_t i) const {
    return static_cast<double>(ghost_[i]) / kGhostScale;
  }
  void invalidate() {
    valid_ = false;
    flashActive_ = false;
  }
  bool valid() const { return valid_; }

 private:
  void reset(int w, int h) {
    w_ = w;
    h_ = h;
    const size_t n = static_cast<size_t>(w) * h;
    prev_.assign(n, kPaper);
    ghost_.assign(n, 0);
    flashOld_.assign(n, kPaper);
    flashNew_.assign(n, kPaper);
    flashActive_ = false;
    valid_ = true;
  }

  void accumulate(const uint8_t *levels, size_t n) {
    const int keep = static_cast<int>(kKeep * 1024 + 0.5);
    const int toW = static_cast<int>(residueToWhite() * 1024 + 0.5);
    const int toB = static_cast<int>(kResidueToBlack * 1024 + 0.5);
    const int lim = kDesignCapLevels * kGhostScale;
    const int toW16 = toW * kGhostScale, toB16 = toB * kGhostScale;
    for (size_t i = 0; i < n; i++) {
      int g = (ghost_[i] * keep) >> 10;
      const int d = static_cast<int>(levels[i]) - prev_[i];
      // lighter: keeps part of the ink it lost (darker than target: negative)
      if (d > 0) g -= (d * toW16) >> 10;
      else if (d < 0) g += (-d * toB16) >> 10;
      ghost_[i] = static_cast<int16_t>(g < -lim ? -lim : g > lim ? lim : g);
    }
  }

  void startFlash(const uint8_t *oldLevels, size_t n, const Program &p,
                  uint64_t nowMs) {
    // What the glass shows NOW is the old page plus its ghosts: that is the
    // state the waveform starts from.
    for (size_t i = 0; i < n; i++)
      flashOld_[i] = displayed(oldLevels[i], ghost_[i]);
    std::fill(ghost_.begin(), ghost_.end(), 0);
    prog_ = &p;
    flashStartMs_ = nowMs;
    flashActive_ = true;
    lastFrame_ = -1;
  }

  uint8_t displayed(uint8_t level, int16_t g) const {
    const int c = cap_ * kGhostScale;
    const int gg = std::clamp(static_cast<int>(g), -c, c);
    return static_cast<uint8_t>(
        std::clamp(static_cast<int>(level) + gg / kGhostScale, 0, 255));
  }

  void write(const uint8_t *levels, size_t n, uint32_t *out) const {
    if (cap_ == 0) {
      for (size_t i = 0; i < n; i++) out[i] = lut_[levels[i]];
      return;
    }
    for (size_t i = 0; i < n; i++) out[i] = lut_[displayed(levels[i], ghost_[i])];
  }

  bool valid_ = false;
  int w_ = 0, h_ = 0;
  int cap_ = 0;
  uint32_t lut_[256] = {};
  std::vector<uint8_t> prev_;
  std::vector<int16_t> ghost_;
  std::vector<uint8_t> flashOld_, flashNew_;
  const Program *prog_ = &kX3Full;
  bool flashActive_ = false;
  uint64_t flashStartMs_ = 0;
  int lastFrame_ = -1;
};

}  // namespace eink
