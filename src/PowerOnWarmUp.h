#pragma once

// BZZT THONK -- the tube coming back, for the DARK page, and ONLY from the dot
// the collapse left. The other half of src/PowerOffCollapse.h.
//
// DOCTRINE (2026-08-22): dark mode is a CRT. The collapse switches the tube off
// at sleep; nothing switched it back on, so the glass simply had a picture on
// it again. One switch owns both halves of the tube's life -- owner ruling
// 2026-08-23, "show crt powering on animation if power off animation is
// enabled" -- and there is no second Settings row.
//
// THE TRIGGER IS A STATE, NOT AN EVENT (owner, same day: "only when there's a
// dot there, then do the 'bzzt thonk' screen warmup animation"). Not "was this
// a wake": the tube must have been SWITCHED OFF, by the collapse, on this
// glass. A cold launch, a wake with the dial off, a wake from a light page and
// a firmware restart all miss it, because none of them collapsed to a dot.
//
// AND THE DOT IS NOT LITERALLY STILL THERE -- measured 2026-08-23, brightest
// channel 19/255 anywhere on the glass after the collapse finishes, which is
// the grain over black and not a dot. The collapse ends at EXACTLY zero on
// purpose ("a dot left at one part in a thousand would sit on the glass all
// night"), and that is an owner-facing trade the Settings row exists for, so it
// is not reversed here. What carries the state instead is a flag the collapse
// records on the frame it starts, and what makes the owner's sentence true on
// the glass is the DOT PHASE below: the animation opens by relighting the dot
// at exactly the width and place the collapse closed it to. The seam is
// literal, without leaving a lit pixel on the panel for eight hours.
//
// THE TWO BEATS, and neither is a ramp.
//
//   BZZT -- the electrical snap. The supplies come up before anything useful
//   does: the dot flickers in unequal bursts (a gate, not a strobe -- see
//   kBzztPulses), scanline crackle streaks across the glass, and the line
//   punches out sideways in DISCRETE steps, one per burst. Nothing eases.
//
//   THONK -- the raster slamming open. The line thumps to full height and
//   arrives HARD: openAt overshoots past the panel into overscan, bounces once
//   under, and lands. That is a mechanical arrival, which is what the word
//   means; an ease-out curve here reads as a fade and was the first attempt.
//
// WHY THERE IS A DOT AND A LINE AND THEN A RASTER, in that order. Switching a
// tube off, the vertical yoke dies first (raster -> line) and the horizontal
// second (line -> dot). Coming back up, the supplies arrive in the order they
// can: there is a dot, the line scan catches, and the field scan last. So the
// warm-up runs the collapse's three stages backwards -- and this is the one
// place the two halves genuinely mirror, which is why this model has a
// horizontalScale where the first attempt did not.
//
// WHY IT CANNOT DELAY THE WAKE. Nothing waits for this. The firmware boots,
// paginates and renders exactly as it always did; the animation only decides
// what the glass shows while that happens, from inside HalDisplay's present.
// The heater phase in particular is FREE: the caller credits it against the
// boot the wake already spent (see kHeaterMs), and a desktop relaunch spends
// ~1.3 s there.
//
// SKIPPING IS PART OF THE CONTRACT, not an afterthought: this animation stands
// between the owner and the page he just asked for, which the collapse never
// does. The caller drops it on any fresh press. Only a press DOWN may skip,
// because the release of the very tap that woke the device can still be in the
// queue.
//
// THE SETTLE PHASE MAY ONLY DARKEN. It is the one phase that composites over
// the FINISHED page -- chrome, grain and all -- so it is a MOD pass, and
// driveAt is built to touch nominal exactly at both ends of it. An overshoot
// landing there would need an additive pass over a dark ground, which is the
// page-flash bug class. The overshoot lives in the THONK, where the caller owns
// the draw and expresses it over black.
//
// Pure and clock-free; tests/power_on_warm_up_test.cpp is the only instrument.
// The caller owns the clock, exactly as it owns the render.

#include <cmath>
#include <cstdint>

namespace poweron {

// THE HEATER, and why it is not felt. The cathode is cold and the glass is
// black. The caller credits this phase against the time the wake has ALREADY
// spent booting -- so on any real wake it is spent before the first frame
// exists, and it costs nothing. It is here because on a fast in-process wake
// there may be nothing to credit, and a tube that lights instantly is wrong.
constexpr float kHeaterMs = 50.0f;

// THE DOT, relit where the collapse closed it. The anchor, and the whole reason
// the owner's "only when there's a dot there" is true on the glass rather than
// only in a flag.
constexpr float kDotMs = 35.0f;

// BZZT: the flicker, and the line punching out sideways through it.
constexpr float kBzztMs = 140.0f;

// THONK: the raster slamming to full height, overshooting into overscan.
constexpr float kThonkMs = 120.0f;

// The supplies coming to rest under the finished page. Darken-only.
constexpr float kSettleMs = 50.0f;

inline float totalMs() {
  return kHeaterMs + kDotMs + kBzztMs + kThonkMs + kSettleMs;
}

// Where each beat starts, so nothing has to add the same four numbers twice.
inline float dotStartMs() { return kHeaterMs; }
inline float bzztStartMs() { return kHeaterMs + kDotMs; }
inline float thonkStartMs() { return kHeaterMs + kDotMs + kBzztMs; }
inline float settleStartMs() {
  return kHeaterMs + kDotMs + kBzztMs + kThonkMs;
}

// The dot's width as a fraction of the page width and the line's thickness as a
// fraction of the screen height. Both are the collapse's own constants, because
// the dot this opens on is the dot that one closed to; if they drift, the seam
// shows.
constexpr float kDotWidthFrac = 0.006f;
constexpr float kLineHeightFrac = 0.004f;

// The vertical scale the raster starts the thonk from -- the collapse's
// handover width, for the same reason.
constexpr float kLineScale = 0.012f;

// Cap on the total beam drive, as the collapse caps it: 1/scale diverges as the
// raster closes on a hairline, and past this there is no structure left in the
// picture at all.
constexpr float kGainMax = 3.0f;

// THE BZZT GATE. Unequal bursts, because equal ones are a strobe and a strobe
// is not an electrical fault. Alternating on/off from ON, as fractions of the
// bzzt phase; the last is ON, so the beat hands a LIT line to the thonk rather
// than a dark one. Must sum to 1.
//
// EVERY BURST IS LONGER THAN A FRAME, and that constraint is what set kBzztMs.
// The first attempt had nine bursts inside 80 ms -- four of them 1.6 to 4 ms
// long, which at 60 Hz (and at the desktop's ~15 ms present cadence) fall
// BETWEEN two frames and are simply never drawn. It modelled beautifully and
// rendered as one dark gap and one steady line: the crackle did not exist. A
// model finer than the display's frame is not detail, it is a lie, and nothing
// but a frame-length floor catches it. tests/power_on_warm_up_test.cpp pins it
// against kMinBurstMs.
constexpr float kMinBurstMs = 16.7f;  // one frame at 60 Hz
constexpr int kBzztPulses = 7;
constexpr float kBzztPulseWidths[kBzztPulses] = {0.135f, 0.150f, 0.140f,
                                                 0.160f, 0.136f, 0.145f,
                                                 0.134f};

// How many crackle streaks the caller draws while the gate is on. Three: enough
// to read as interference, few enough not to read as a pattern.
constexpr int kCrackleStreaks = 3;

// The thonk's arrival. 1 - e^(-c v) cos(d v), with d fixed at 5*pi/2 so v = 1
// is the THIRD crossing of unity: up through it, over into overscan, back
// under, and exactly there at the end. c sets how dead the supply is; 6 gives
// about 9% of overscan, which is a thump rather than a lurch.
constexpr float kThonkDamping = 6.0f;
constexpr float kThonkRing = 7.8539816f;  // 5*pi/2

// How far the supplies sag under the finished page before recovering. Small,
// and it is the ONLY brightness move that lands on a page anyone is reading.
constexpr float kSettleDip = 0.06f;

enum class Phase {
  Heater,  // nothing is drawn; the glass is black
  Dot,     // the collapse's dot, relit, steady
  Bzzt,    // the flicker, and the line punching out sideways
  Thonk,   // the raster slamming to full height, over black
  Settle,  // the page is whole; the supplies are still coming to rest
};

struct Params {
  // OFF IS THE DEFAULT AND OFF IS BIT-EXACT: stateAt returns the identity
  // state -- whole picture, nominal drive, no line, no veil -- at every elapsed
  // time, so a caller that steps a disabled animation draws exactly the frame
  // it drew before this existed.
  bool enabled = false;
};

struct State {
  // Is anything to be drawn other than the untouched frame?
  bool active = false;
  // Has the animation run out? The caller stops stepping; the frame it stops
  // on is the ordinary present, untouched.
  bool finished = false;
  Phase phase = Phase::Settle;
  // The picture, scaled about the panel's centre. 1 = whole; ABOVE 1 in the
  // thonk's overshoot, which is overscan and is meant to clip.
  float verticalScale = 1.0f;
  float horizontalScale = 1.0f;
  // Draw the picture at all? False until the raster has height to carry it.
  // Defaults TRUE, so the identity state -- disabled, and finished -- means
  // "the whole picture, normally", which is what the caller draws anyway.
  bool showPicture = true;
  // Total beam drive. 1 = nominal. Above 1 only where the caller owns the draw
  // and can express it over black -- never in Settle.
  float drive = 1.0f;
  // The dot / line: width as a fraction of the page width, and brightness.
  float lineWidthFrac = 0.0f;
  float lineAlpha = 0.0f;
  // Scanline crackle, and which burst it belongs to. The caller places the
  // streaks from the index, so they jump per burst instead of crawling.
  float crackle = 0.0f;
  int crackleBurst = 0;
  // How dark the chrome OUTSIDE the page still is. 1 = fully dark, 0 = normal.
  float surroundVeil = 0.0f;
};

// The gate, its burst index, and how far the line has punched out. b is 0 at
// the start of the bzzt and 1 at its end. `onCount` is how many bursts have
// LIT, which is what steps the width -- so the line jumps out with the
// crackle instead of sliding under it.
inline void bzztGateAt(float b, bool *lit, int *burst, int *onCount) {
  *lit = false;
  *burst = 0;
  *onCount = 0;
  float edge = 0.0f;
  for (int i = 0; i < kBzztPulses; ++i) {
    const bool isOn = (i % 2) == 0;
    if (isOn) (*onCount)++;
    edge += kBzztPulseWidths[i];
    if (b < edge) {
      *lit = isOn;
      *burst = i;
      return;
    }
  }
  // Past the end (float slop only): the last burst is ON by construction.
  *lit = true;
  *burst = kBzztPulses - 1;
}

// Where a crackle streak sits, 0..1 down the glass. A hash rather than a table,
// so the streaks move with the burst and repeat exactly on the same burst.
inline float crackleRowFrac(int burst, int streak) {
  uint32_t h = static_cast<uint32_t>(burst) * 2654435761u +
               static_cast<uint32_t>(streak) * 40503u + 1u;
  h ^= h >> 15;
  h *= 2246822519u;
  h ^= h >> 13;
  return static_cast<float>(h % 10000u) / 10000.0f;
}

// The thonk's arrival curve. 0 at v = 0, exactly 1 at v = 1, one overshoot into
// overscan and one bounce under in between.
inline float openAt(float v) {
  if (v <= 0.0f) return 0.0f;
  if (v >= 1.0f) return 1.0f;  // EXACTLY whole: the handover must not step
  return 1.0f - std::exp(-kThonkDamping * v) * std::cos(kThonkRing * v);
}

// The settle's sag. Exactly 1 at both ends and never above it, which is the
// whole reason this phase may be a MOD pass over the finished page.
inline float driveAt(float s) {
  if (s <= 0.0f || s >= 1.0f) return 1.0f;
  return 1.0f - kSettleDip * std::sin(3.14159265f * s);
}

// THE ANSWER: what the glass shows `elapsedMs` after the tube was switched on.
//
// t = 0 is BLACK -- no picture, no dot, zero drive -- which is exactly where
// the collapse left the glass, so the two halves join with no seam. t >= total
// is the IDENTITY, exactly, so the last frame of a warm-up is byte-identical to
// the page the wake would have shown with the dial off.
inline State stateAt(const Params &p, float elapsedMs) {
  State s;
  if (!p.enabled) return s;
  if (elapsedMs < 0.0f) elapsedMs = 0.0f;
  s.active = true;

  if (elapsedMs >= totalMs()) {
    s.finished = true;
    return s;  // the identity, exactly
  }

  if (elapsedMs < dotStartMs()) {
    // THE HEATER. Nothing is emitting, so nothing is drawn; the caller clears
    // to black and presents that.
    s.phase = Phase::Heater;
    s.showPicture = false;
    s.verticalScale = kLineScale;
    s.horizontalScale = kDotWidthFrac;
    s.drive = 0.0f;
    s.surroundVeil = 1.0f;
    return s;
  }

  if (elapsedMs < bzztStartMs()) {
    // THE DOT, relit where the collapse closed it. Steady and full: the
    // cathode is emitting into a stationary spot, which is the brightest thing
    // a tube ever does and the reason spot-killer circuits exist.
    s.phase = Phase::Dot;
    s.showPicture = false;
    s.verticalScale = kLineScale;
    s.horizontalScale = kDotWidthFrac;
    s.drive = kGainMax;
    s.lineWidthFrac = kDotWidthFrac;
    s.lineAlpha = 1.0f;
    s.surroundVeil = 1.0f;
    return s;
  }

  if (elapsedMs < thonkStartMs()) {
    // BZZT. The gate decides whether there is any beam this instant; the burst
    // count decides how far the line scan has caught. Both are steps.
    s.phase = Phase::Bzzt;
    s.showPicture = false;
    const float b = (elapsedMs - bzztStartMs()) / kBzztMs;
    bool lit = false;
    int burst = 0, onCount = 0;
    bzztGateAt(b, &lit, &burst, &onCount);
    const int onTotal = (kBzztPulses + 1) / 2;
    const float open = static_cast<float>(onCount) / static_cast<float>(onTotal);
    s.verticalScale = kLineScale;
    s.horizontalScale = kDotWidthFrac + (1.0f - kDotWidthFrac) * open;
    s.drive = kGainMax;
    s.lineWidthFrac = s.horizontalScale;
    s.lineAlpha = lit ? 1.0f : 0.0f;
    // The crackle rides the lit bursts and dies out as the supply catches, so
    // the interference is worst at the start where the fault is.
    s.crackle = lit ? (1.0f - b) : 0.0f;
    s.crackleBurst = burst;
    s.surroundVeil = 1.0f;
    return s;
  }

  if (elapsedMs < settleStartMs()) {
    // THONK. The field scan catches and the raster slams open past the panel,
    // bounces once, and lands. The picture rides it from the first instant --
    // there is a full-width line to carry it now.
    s.phase = Phase::Thonk;
    const float v = (elapsedMs - thonkStartMs()) / kThonkMs;
    const float open = openAt(v);
    s.verticalScale = kLineScale + (1.0f - kLineScale) * open;
    s.horizontalScale = 1.0f;
    s.showPicture = true;
    // Same light into less height -- the identical statement the collapse
    // makes. In the overshoot it runs the other way and the overscanned raster
    // is genuinely dimmer, which is also true.
    float d = 1.0f / (s.verticalScale > 1e-4f ? s.verticalScale : 1e-4f);
    if (d > kGainMax) d = kGainMax;
    s.drive = d;
    // The line dissolves INTO the raster rather than being replaced by it, so
    // the two never cross-fade through a gap.
    s.lineWidthFrac = 1.0f;
    float a = 1.0f - open;
    if (a < 0.0f) a = 0.0f;
    s.lineAlpha = a;
    s.surroundVeil = 1.0f;
    return s;
  }

  // THE SUPPLIES SETTLE. The raster is whole and the page is the ordinary
  // composed frame; all that is left is a few percent of sag, applied as a
  // darken-only pass, and the chrome outside the page coming up.
  s.phase = Phase::Settle;
  const float st = (elapsedMs - settleStartMs()) / kSettleMs;
  s.drive = driveAt(st);
  float veil = 1.0f - st;
  if (veil < 0.0f) veil = 0.0f;
  s.surroundVeil = veil;
  return s;
}

}  // namespace poweron
