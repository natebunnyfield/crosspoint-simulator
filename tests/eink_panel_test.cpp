// Host test for src/EinkPanel.h -- e-ink mode's panel model (spike 2026-09-25).
//
// Every failure mode is a wrong picture that compiles: a ghost that breaches
// the 7:1 floor, a clearing refresh that leaves residue, a flash that ends on
// the wrong page, a transcription error in the X3 waveform. Each is pinned.

#include <cstdio>
#include <random>
#include <string>
#include <vector>

#include "EinkPanel.h"
#include "PanelPalette.h"
#include "TestCheck.h"

using testcheck::check;
static int &failures = testcheck::g_failures;

namespace {

struct Lut {
  uint32_t v[256];
};

Lut lutFor(uint32_t inkHex, uint32_t paperHex) {
  panelpalette::Palette p{};
  p.ink[0] = inkHex >> 16; p.ink[1] = (inkHex >> 8) & 0xFF; p.ink[2] = inkHex & 0xFF;
  p.paper[0] = paperHex >> 16; p.paper[1] = (paperHex >> 8) & 0xFF; p.paper[2] = paperHex & 0xFF;
  Lut l{};
  for (int i = 0; i < 256; i++)
    l.v[i] = panelpalette::colorForLevel(static_cast<uint8_t>(i), p);
  return l;
}

// A page: random text-like ink on paper, with a few AA grays.
std::vector<uint8_t> page(int w, int h, unsigned seed) {
  std::mt19937 rng(seed);
  std::vector<uint8_t> v(static_cast<size_t>(w) * h, eink::kPaper);
  for (auto &p : v) {
    const unsigned r = rng() % 100;
    p = r < 18 ? 0 : r < 21 ? 96 : r < 24 ? 200 : 255;
  }
  return v;
}

int levelOf(const Lut &l, uint32_t argb) {
  for (int i = 0; i < 256; i++)
    if (l.v[i] == argb) return i;
  return -1;
}

}  // namespace

int main() {
  // ---- 1. The waveform tables are the X3 banks, frame for frame. ----------
  check(eink::totalFrames(eink::kX3Full) == 62,
        "X3 _full is 24+4+14+10 then 10 = 62 frames (Uc8253X3Luts.h)");
  check(eink::totalFrames(eink::kX3HalfScrub) == 25,
        "X3 _half is 19 then 6 = 25 frames");
  check(eink::totalFrames(eink::kX3Full) * eink::kFramePeriodMs == 1240,
        "full refresh lasts 1240 ms at the assumed 50 Hz");
  check(eink::kX3Full.oldAssumedWhite && !eink::kX3HalfScrub.oldAssumedWhite,
        "only the full write fills DTM1 white first");
  // The scrub never drives a pixel AWAY from its target: WW/BW white, WB/BB black.
  for (int s = 0; s < eink::kX3HalfScrub.nseg; s++) {
    const auto &sg = eink::kX3HalfScrub.seg[s];
    check(sg.drive[eink::WW] != eink::B && sg.drive[eink::BW] != eink::B &&
              sg.drive[eink::WB] != eink::W && sg.drive[eink::BB] != eink::W,
          "the X3 half refresh is a scrub, not an inversion");
  }

  // ---- 2. The affine form equals frame-by-frame stepping. ------------------
  {
    const double r = std::exp(-1.0 / eink::kTauFrames);
    for (int c = 0; c < 4; c++)
      for (int s0 : {0, 96, 200, 255, 137})
        for (int f : {0, 1, 10, 24, 27, 40, 61, 62}) {
          double s = s0;
          int left = f;
          for (int i = 0; i < eink::kX3Full.nseg && left > 0; i++)
            for (int k = 0; k < eink::kX3Full.seg[i].frames && left > 0; k++, left--) {
              const int d = eink::kX3Full.seg[i].drive[c];
              if (d != eink::H) {
                const double T = d == eink::W ? 255.0 : 0.0;
                s = T + (s - T) * r;
              }
            }
          const auto m = eink::affineAt(eink::kX3Full, c, f);
          check(std::fabs(m.a * s0 + m.b - s) < 1e-6,
                "affine map equals stepping the panel frame by frame");
        }
  }

  // ---- 3. The full flash: black with the new page in NEGATIVE, then the page.
  {
    const auto ww = eink::affineAt(eink::kX3Full, eink::WW, 24);
    const auto wb = eink::affineAt(eink::kX3Full, eink::WB, 24);
    check(ww.a * 255 + ww.b < 10,
          "end of phase A: a pixel that will be paper has been driven black");
    check(std::fabs(wb.a * 255 + wb.b - 255) < 1e-9,
          "...while one that will be ink HOLDS its old (paper) state: a negative");
    const auto wwEnd = eink::affineAt(eink::kX3Full, eink::WW, 62);
    const auto wbEnd = eink::affineAt(eink::kX3Full, eink::WB, 62);
    check(wwEnd.a * 0 + wwEnd.b > 245, "paper ends at paper");
    check(wbEnd.a * 255 + wbEnd.b < 10, "ink ends at ink");
  }

  // ---- 4. Ghost cap from the palette, and the 7:1 floor. --------------------
  const Lut frozen = lutFor(0x5C332B, 0xF9F3E9);  // Sanguine on India (FrozenPage.h)
  const Lut deflt = lutFor(0x2D2D2D, 0xFBFBF9);   // kDefaultLight
  const Lut solar = lutFor(0x657B83, 0xFDF6E3);   // Solarized light, 4.13:1
  {
    const int capF = eink::ghostCapLevels(frozen.v);
    const int capD = eink::ghostCapLevels(deflt.v);
    std::printf("ghost cap: frozen page %d levels, default %d, solarized %d\n",
                capF, capD, eink::ghostCapLevels(solar.v));
    check(capF > 0, "the shipped page has headroom for a visible ghost");
    check(eink::contrast(frozen.v[capF], frozen.v[255 - capF]) >= 7.0,
          "frozen page: worst ghosted ink vs worst ghosted paper >= 7:1");
    check(eink::contrast(deflt.v[capD], deflt.v[255 - capD]) >= 7.0,
          "default page: worst ghosted pair >= 7:1");
    check(eink::ghostCapLevels(solar.v) == 0,
          "a palette already under the floor gets NO ghost at all");
  }

  // ---- 5. Accumulation, the floor on real output, and clearing. ------------
  const int W = 96, H = 64;
  const size_t N = static_cast<size_t>(W) * H;
  std::vector<uint32_t> out(N);
  for (const Lut *lut : {&frozen, &deflt}) {
    eink::Panel panel;
    auto p0 = page(W, H, 1);
    panel.onLevels(p0.data(), W, H, eink::Refresh::None, lut->v, 0, true, out.data());
    for (size_t i = 0; i < N; i++)
      check(out[i] == lut->v[p0[i]], "a fresh panel shows the page exactly");
    const int cap = panel.cap();
    double maxGhost = 0;
    int darkestPaper = 255, lightestInk = 0;
    for (int turn = 1; turn <= 14; turn++) {
      auto pg = page(W, H, 100 + turn);
      panel.onLevels(pg.data(), W, H, eink::Refresh::Fast, lut->v, turn * 1000,
                     true, out.data());
      for (size_t i = 0; i < N; i++) {
        const int lv = levelOf(*lut, out[i]);
        if (pg[i] == 255 && lv >= 0) darkestPaper = std::min(darkestPaper, lv);
        if (pg[i] == 0 && lv >= 0) lightestInk = std::max(lightestInk, lv);
        maxGhost = std::max(maxGhost, std::fabs(panel.ghostAt(i)));
      }
    }
    std::printf("after 14 partials: darkest paper %d, lightest ink %d, cap %d\n",
                darkestPaper, lightestInk, cap);
    check(darkestPaper < 255, "ghosts appear on paper across partial refreshes");
    check(darkestPaper >= 255 - cap && lightestInk <= cap,
          "no displayed pixel leaves the cap");
    check(eink::contrast(lut->v[lightestInk], lut->v[darkestPaper]) >= 7.0,
          "measured on the rendered output: ink vs paper stays >= 7:1");
    // A partial that repeats the SAME page adds nothing; ghosts only decay.
    {
      auto same = page(W, H, 114);
      double before = 0, after = 0;
      for (size_t i = 0; i < N; i++) before += std::fabs(panel.ghostAt(i));
      panel.onLevels(same.data(), W, H, eink::Refresh::Fast, lut->v, 20000, true,
                     out.data());
      for (size_t i = 0; i < N; i++) after += std::fabs(panel.ghostAt(i));
      check(after <= before, "re-drawing the same page adds no ghost");
    }
    // HALF clears every ghost, and the settled page is exact.
    auto shown = page(W, H, 114);  // the page drawn last, just above
    auto clean = page(W, H, 999);
    panel.onLevels(clean.data(), W, H, eink::Refresh::Half, lut->v, 30000, true,
                   out.data());
    bool exact = true;
    for (size_t i = 0; i < N; i++) {
      if (panel.ghostAt(i) != 0) exact = false;
      if (out[i] != lut->v[clean[i]]) exact = false;
    }
    check(exact, "a clearing refresh leaves no ghost and the exact page");
    check(panel.flashActive(), "...and runs its waveform");
    // ...STARTING FROM THE OLD PAGE: every pixel whose level changed by more
    // than half the range starts nearer its old level than its new one. The
    // first cut started from the new page (adversarial review, build 213).
    {
      size_t changed = 0, fromOld = 0;
      for (size_t i = 0; i < N; i++) {
        const int d = static_cast<int>(clean[i]) - shown[i];
        if (d > 128 || d < -128) {
          changed++;
          const int s = panel.flashStartLevel(i);
          if (std::abs(s - shown[i]) < std::abs(s - clean[i])) fromOld++;
        }
      }
      check(changed > 0 && fromOld == changed, "the waveform starts from the OLD page");
    }
    std::vector<uint32_t> frame(N);
    check(panel.flashFrame(30000, frame.data()) == 1, "frame 0 renders");
    check(panel.flashFrame(30005, frame.data()) == 0,
          "the same panel frame is not rebuilt");
    check(panel.flashFrame(30000 + 25 * 20, frame.data()) == -1,
          "the X3 scrub ends after 25 frames (500 ms)");
    check(!panel.flashActive(), "and the sequence is over");
  }

  // ---- 6. The host full refresh (the shake): same page, ghosts go. ---------
  {
    eink::Panel panel;
    auto a = page(W, H, 7), b = page(W, H, 8);
    panel.onLevels(a.data(), W, H, eink::Refresh::None, frozen.v, 0, true, out.data());
    panel.onLevels(b.data(), W, H, eink::Refresh::Fast, frozen.v, 10, true, out.data());
    bool anyGhost = false;
    for (size_t i = 0; i < N; i++) anyGhost |= panel.ghostAt(i) != 0;
    check(anyGhost, "a partial left ghosts");
    check(panel.requestFull(100, out.data()), "a full refresh is accepted");
    bool clear = true;
    for (size_t i = 0; i < N; i++) clear &= out[i] == frozen.v[b[i]];
    check(clear, "the settled page after a host full refresh is exactly the page");
    std::vector<uint32_t> frame(N);
    // Mid phase A: every paper pixel of the page is dark (the flash).
    panel.flashFrame(100 + 23 * 20, frame.data());
    int dark = 0, paperPx = 0;
    for (size_t i = 0; i < N; i++)
      if (b[i] == 255) {
        paperPx++;
        if (levelOf(frozen, frame[i]) < 40) dark++;
      }
    check(dark == paperPx, "the full flash takes every paper pixel dark");
    check(panel.flashFrame(100 + 62 * 20, frame.data()) == -1,
          "the full refresh ends at 1240 ms");
    eink::Panel cold;
    check(!cold.requestFull(0, out.data()), "no page yet: nothing to refresh");
  }

  // ---- 7. A palette under the floor draws the page untouched. --------------
  {
    eink::Panel panel;
    auto a = page(W, H, 3), b = page(W, H, 4);
    panel.onLevels(a.data(), W, H, eink::Refresh::None, solar.v, 0, true, out.data());
    panel.onLevels(b.data(), W, H, eink::Refresh::Fast, solar.v, 10, true, out.data());
    bool exact = true;
    for (size_t i = 0; i < N; i++) exact &= out[i] == solar.v[b[i]];
    check(exact, "cap 0: the ghost plane is not drawn");
  }

  // WHICH PROGRAM RUNS WHERE (2026-09-25). The X3 has its own decoded banks;
  // every other build still BORROWS the X3 _full program for both HALF and
  // FULL, because the X4's SSD1677 runs OTP sequences (0xD7 / 0xF7) whose
  // frames exist in no file the search found (docs/eink-mode-spike-2026-09-25.md
  // §2a). Pinned so that a real X4 transcription has to change this on purpose.
  {
    using eink::Refresh;
    check(&eink::programFor(Refresh::Half, true) == &eink::kX3HalfScrub,
          "X3 HALF is the decoded scrub");
    check(&eink::programFor(Refresh::Full, true) == &eink::kX3Full,
          "X3 FULL is the decoded _full");
    check(&eink::programFor(Refresh::Half, false) == &eink::kX3Full &&
              &eink::programFor(Refresh::Full, false) == &eink::kX3Full,
          "non-X3 builds borrow the X3 _full for both (no X4 frames found)");
    check(eink::totalFrames(eink::kX3Full) == 62 &&
              eink::totalFrames(eink::kX3HalfScrub) == 25,
          "frame counts match Uc8253X3Luts.h (62 / 25)");
  }

  if (failures) {
    std::printf("eink_panel_test: %d FAILED\n", failures);
    return 1;
  }
  std::printf("eink_panel_test: all passed\n");
  return 0;
}
