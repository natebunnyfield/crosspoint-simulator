// Host test for src/PowerOnWarmUp.h -- the bzzt-thonk warm-up.
//
// Every failure mode here is a wrong PICTURE, and this one is worse placed than
// the collapse's: the collapse runs when nobody is watching, this one runs
// between the owner and the page he just asked for.
//
// A last frame that is not the identity leaves the page permanently dim, and
// nothing in the app ever says so. A drive above nominal anywhere in the SETTLE
// phase is an additive pass over a dark ground, which is the page-flash and
// gray-background bug class the surface stack spent a week removing. A first
// frame that is not black is a flash at wake, and it is also a seam, because
// the collapse left the glass exactly black. A bzzt whose bursts are equal is a
// strobe rather than a fault. A thonk that does not overshoot is a fade wearing
// the word's clothes -- "nothing about it should feel like a fade" -- and a
// screenshot cannot tell those two apart. And a disabled animation that is not
// bit-exact identity changes what every wake looks like for every install that
// never turned this on.

#include "PowerOnWarmUp.h"
#include "PowerOffCollapse.h"

#include <cmath>
#include <cstdio>
#include "TestCheck.h"
using testcheck::check;

using namespace poweron;

static int &failures = testcheck::g_failures;

static bool isIdentity(const State &s) {
  return s.phase == Phase::Settle && s.verticalScale == 1.0f &&
         s.horizontalScale == 1.0f && s.showPicture && s.drive == 1.0f &&
         s.lineWidthFrac == 0.0f && s.lineAlpha == 0.0f && s.crackle == 0.0f &&
         s.surroundVeil == 0.0f;
}

int main() {
  Params on;
  on.enabled = true;
  Params off;  // enabled defaults false

  // --- OFF IS BIT-EXACT OFF -------------------------------------------------
  {
    bool identity = true;
    for (float t = -50.0f; t < totalMs() + 500.0f; t += 3.0f) {
      const State s = stateAt(off, t);
      if (s.active || s.finished || !isIdentity(s)) identity = false;
    }
    check(identity,
          "a disabled warm-up is the identity at every time, exactly");
  }

  // --- THE FIRST FRAME IS BLACK, AND THAT IS WHERE THE COLLAPSE LEFT IT -----
  {
    const State s = stateAt(on, 0.0f);
    check(s.active, "the opening frame is an active frame");
    check(s.phase == Phase::Heater, "the opening frame is the heater");
    check(s.drive == 0.0f, "the tube emits nothing on the opening frame");
    check(!s.showPicture, "there is no picture on the opening frame");
    check(s.lineAlpha == 0.0f, "there is no dot on the opening frame");
    check(s.surroundVeil == 1.0f, "the chrome is dark on the opening frame");
    check(!s.finished, "the opening frame is not the last one");
    const State before = stateAt(on, -100.0f);
    check(before.phase == Phase::Heater && before.drive == 0.0f,
          "a negative elapsed is the same black frame, not a jump");
  }

  // --- THE LAST FRAME IS THE PAGE, UNTOUCHED --------------------------------
  // The pair to the collapse's "the terminal state is exactly black". Anything
  // short of exact leaves a permanent dim on every page read after a wake.
  {
    const State s = stateAt(on, totalMs());
    check(s.finished, "the warm-up is finished at its stated total");
    check(isIdentity(s), "the terminal state is the identity, exactly");
    bool stays = true;
    for (float t = totalMs(); t < totalMs() + 5000.0f; t += 17.0f) {
      const State l = stateAt(on, t);
      if (!l.finished || !isIdentity(l)) stays = false;
    }
    check(stays, "it stays the identity forever after, exactly");
  }

  // --- THE SEAM: THIS OPENS ON THE DOT THE COLLAPSE CLOSED TO ---------------
  // The owner's trigger is "only when there's a dot there". The collapse ends
  // at exactly zero brightness, so the dot on the glass is the one THIS draws
  // -- and it has to be the same dot, at the same width, or the two halves do
  // not join. Reading the collapse's own constants is what makes a drift in
  // either file fail here rather than on the phone.
  {
    check(kDotWidthFrac == poweroff::kDotWidthFrac,
          "the dot opens at exactly the width the collapse closed to");
    check(kLineHeightFrac == poweroff::kLineHeightFrac,
          "the line is exactly the thickness the collapse's was");
    check(kLineScale == poweroff::kLineScale,
          "the raster's hairline height matches the collapse's handover");
    check(kGainMax == poweroff::kGainMax,
          "both halves cap the beam drive at the same place");
    // And the collapse really does end dark, which is why the dot phase exists.
    poweroff::Params cp;
    cp.enabled = true;
    const poweroff::State last = poweroff::stateAt(cp, poweroff::totalMs());
    check(last.dotAlpha == 0.0f && last.finished,
          "the collapse leaves NO lit dot: the warm-up has to relight it");
  }

  // --- THE HEATER SHOWS NOTHING, THEN THE DOT ------------------------------
  {
    bool dark = true;
    for (float t = 0.0f; t < kHeaterMs; t += 1.0f) {
      const State s = stateAt(on, t);
      if (s.phase != Phase::Heater || s.drive != 0.0f || s.lineAlpha != 0.0f)
        dark = false;
    }
    check(dark, "nothing emits for the whole heater phase");
    const State d = stateAt(on, dotStartMs());
    check(d.phase == Phase::Dot, "the dot relights the instant the heater ends");
    check(d.lineAlpha == 1.0f, "the dot comes back at full brightness");
    check(d.lineWidthFrac == kDotWidthFrac, "the dot is a dot, not a line");
    check(!d.showPicture, "a dot carries no picture");
    bool steady = true;
    for (float t = dotStartMs(); t < bzztStartMs(); t += 1.0f) {
      const State s = stateAt(on, t);
      if (s.phase != Phase::Dot || s.lineAlpha != 1.0f ||
          s.lineWidthFrac != kDotWidthFrac)
        steady = false;
    }
    check(steady, "the dot holds steady: it is an anchor, not a beat");
  }

  // --- BZZT IS A FAULT, NOT A STROBE ---------------------------------------
  {
    float sum = 0.0f;
    for (int i = 0; i < kBzztPulses; ++i) sum += kBzztPulseWidths[i];
    check(std::fabs(sum - 1.0f) < 1e-5f, "the bursts fill the bzzt exactly");
    check(kBzztPulses % 2 == 1,
          "there is an odd number of bursts, so the beat ends LIT");
    // Equal-length bursts are a strobe. Every adjacent pair must differ, and
    // no two ON bursts may share a length either.
    bool unequal = true;
    for (int i = 1; i < kBzztPulses; ++i)
      if (kBzztPulseWidths[i] == kBzztPulseWidths[i - 1]) unequal = false;
    check(unequal, "no two adjacent bursts are the same length");
    // AND EVERY BURST OUTLASTS A FRAME. A burst shorter than the display's
    // frame falls between two of them and is never drawn: the first version of
    // this gate had four such, and rendered as one dark gap and one steady
    // line. Nothing but this check can see that -- the model was perfect.
    bool longEnough = true;
    for (int i = 0; i < kBzztPulses; ++i)
      if (kBzztPulseWidths[i] * kBzztMs < kMinBurstMs) longEnough = false;
    check(longEnough, "every burst lasts at least one 60 Hz frame");

    // It really does flicker: both states must occur, and more than twice.
    int transitions = 0;
    bool prev = false, first = true;
    bool everOn = false, everOff = false;
    for (float t = bzztStartMs(); t < thonkStartMs(); t += 0.25f) {
      const State s = stateAt(on, t);
      const bool lit = s.lineAlpha > 0.0f;
      everOn = everOn || lit;
      everOff = everOff || !lit;
      if (!first && lit != prev) transitions++;
      prev = lit;
      first = false;
    }
    check(everOn && everOff, "the bzzt actually gates on and off");
    check(transitions >= 6, "the bzzt crackles rather than blinking once");

    // The line punches out in STEPS, and lands full width before the thonk.
    const State start = stateAt(on, bzztStartMs());
    const State end = stateAt(on, thonkStartMs() - 0.001f);
    check(start.horizontalScale < 0.35f,
          "the bzzt starts near the dot's width, not near a line");
    check(std::fabs(end.horizontalScale - 1.0f) < 1e-5f,
          "the line is full width by the time the thonk starts");
    check(end.lineAlpha == 1.0f,
          "the bzzt hands a LIT line to the thonk, not a dark one");
    // Stepped, not eased: a smooth ramp would take a different value at every
    // sample, a stepped one repeats within a burst.
    int distinct = 0;
    float prevW = -1.0f;
    for (float t = bzztStartMs(); t < thonkStartMs(); t += 0.25f) {
      const float w = stateAt(on, t).horizontalScale;
      if (w != prevW) distinct++;
      prevW = w;
    }
    check(distinct <= (kBzztPulses + 1) / 2,
          "the line widens in discrete steps, one per burst -- it does not ease");
    // And it only ever widens.
    bool monotone = true;
    prevW = -1.0f;
    for (float t = bzztStartMs(); t < thonkStartMs(); t += 0.25f) {
      const float w = stateAt(on, t).horizontalScale;
      if (w < prevW) monotone = false;
      prevW = w;
    }
    check(monotone, "the line scan never loses ground");

    // The crackle rides the lit bursts, dies out, and never outlives the beat.
    bool crackleOk = true;
    for (float t = 0.0f; t <= totalMs(); t += 0.5f) {
      const State s = stateAt(on, t);
      if (s.phase != Phase::Bzzt && s.crackle != 0.0f) crackleOk = false;
      if (s.crackle > 0.0f && s.lineAlpha == 0.0f) crackleOk = false;
    }
    check(crackleOk, "crackle exists only inside a lit bzzt burst");
    check(stateAt(on, bzztStartMs() + 1.0f).crackle >
              stateAt(on, thonkStartMs() - 1.0f).crackle,
          "the crackle dies out as the supply catches");
    // The streaks jump per burst and repeat exactly on the same burst -- a
    // hash that crawled would read as a moving band rather than interference.
    bool placed = true;
    for (int b = 0; b < kBzztPulses; ++b)
      for (int i = 0; i < kCrackleStreaks; ++i) {
        const float f = crackleRowFrac(b, i);
        if (f < 0.0f || f >= 1.0f) placed = false;
        if (crackleRowFrac(b, i) != f) placed = false;
      }
    check(placed, "every crackle streak lands on the glass, deterministically");
    bool spread = false;
    for (int b = 0; b < kBzztPulses; ++b)
      if (crackleRowFrac(b, 0) != crackleRowFrac(0, 0)) spread = true;
    check(spread, "the streaks move between bursts");
  }

  // --- THONK ARRIVES HARD --------------------------------------------------
  // THE LOAD-BEARING ONE for the owner's word. A monotone ease-out passes every
  // other check in this file and looks like a fade on the glass.
  {
    check(openAt(0.0f) == 0.0f, "the raster starts from the line, exactly");
    check(openAt(1.0f) == 1.0f, "the raster lands whole, exactly");
    float peak = 0.0f;
    float trough = 2.0f;
    bool peaked = false;
    for (float v = 0.0f; v <= 1.0f; v += 0.001f) {
      const float o = openAt(v);
      if (o > peak) peak = o;
      if (peak > 1.0f) peaked = true;
      if (peaked && o < trough) trough = o;
    }
    check(peak > 1.05f, "the raster OVERSHOOTS into overscan: it is not a fade");
    check(peak < 1.20f, "the overshoot is a thump, not a lurch");
    check(trough < 1.0f, "it bounces back under before it settles");
    check(trough > 0.95f, "the bounce is one bounce, not a wobble");

    const State t0 = stateAt(on, thonkStartMs());
    check(t0.phase == Phase::Thonk, "the thonk starts when the bzzt ends");
    check(std::fabs(t0.verticalScale - kLineScale) < 1e-6f,
          "the thonk starts from the line's own height");
    check(t0.horizontalScale == 1.0f, "the thonk runs at full width throughout");
    check(t0.showPicture, "the picture rides the raster from the first instant");
    const State t1 = stateAt(on, settleStartMs() - 0.001f);
    check(std::fabs(t1.verticalScale - 1.0f) < 2e-3f,
          "the raster is whole by the end of the thonk");
    check(t1.lineAlpha < 0.01f,
          "the line has dissolved into the raster by the handover");
    // Overscan really is drawn: some frame must exceed the panel.
    bool overscanned = false;
    for (float t = thonkStartMs(); t < settleStartMs(); t += 0.5f)
      if (stateAt(on, t).verticalScale > 1.0f) overscanned = true;
    check(overscanned, "the raster genuinely overscans the panel mid-thonk");
    // And the beam drive follows the geometry both ways.
    bool capped = true;
    for (float t = 0.0f; t <= totalMs(); t += 0.25f)
      if (stateAt(on, t).drive > kGainMax + 1e-5f) capped = false;
    check(capped, "the beam drive never exceeds the cap");
    bool dimmerWhenOverscanned = true;
    for (float t = thonkStartMs(); t < settleStartMs(); t += 0.5f) {
      const State s = stateAt(on, t);
      if (s.verticalScale > 1.0f && s.drive >= 1.0f)
        dimmerWhenOverscanned = false;
    }
    check(dimmerWhenOverscanned,
          "the overscanned raster is dimmer: same beam over more glass");
  }

  // --- THE SETTLE CAN ONLY DARKEN ------------------------------------------
  // The one phase that composites over the FINISHED page, chrome and grain
  // included, so the only cheap way to express it is a MOD pass -- which cannot
  // lift. It must also touch nominal EXACTLY at both ends, or the handover
  // steps and the last frame is not the page.
  {
    bool darkenOnly = true;
    float dimmest = 1.0f;
    for (float t = settleStartMs(); t <= totalMs(); t += 0.25f) {
      const State s = stateAt(on, t);
      if (s.phase != Phase::Settle) darkenOnly = false;
      if (s.drive > 1.0f) darkenOnly = false;
      if (s.drive < dimmest) dimmest = s.drive;
    }
    check(darkenOnly, "the settle never asks for more light than nominal");
    check(dimmest > 0.90f,
          "the settle's sag stays within a few percent of nominal");
    check(dimmest < 1.0f, "the settle actually sags: it is a supply, not a step");
    check(driveAt(0.0f) == 1.0f, "the sag starts at nominal, exactly");
    check(driveAt(1.0f) == 1.0f, "the sag ends at nominal, exactly");
    const State a = stateAt(on, settleStartMs() - 0.5f);
    const State b = stateAt(on, settleStartMs() + 0.5f);
    check(std::fabs(a.drive - b.drive) < 0.02f,
          "brightness does not step across the thonk/settle handover");
  }

  // --- THE CHROME COMES UP ONCE, AND IS GONE BEFORE THE END ----------------
  {
    bool monotone = true;
    float prev = 2.0f;
    for (float t = 0.0f; t <= totalMs(); t += 0.5f) {
      const float v = stateAt(on, t).surroundVeil;
      if (v > prev + 1e-6f) monotone = false;
      prev = v;
    }
    check(monotone, "the chrome's veil only ever lifts");
    check(stateAt(on, settleStartMs()).surroundVeil == 1.0f,
          "the chrome is still dark at the handover, so nothing pops in");
    check(stateAt(on, totalMs()).surroundVeil == 0.0f,
          "the veil is exactly gone on the last frame");
  }

  // --- IT IS SHORT, AND THAT IS THE POINT ----------------------------------
  // The collapse is 1020 ms and nothing waits on it. This one is in front of
  // the page, and the owner asked for something "sharp attack, brief,
  // physical". A future edit that lets it grow should have to argue with this.
  {
    check(totalMs() <= 400.0f, "the whole warm-up fits in four hundred ms");
    check(settleStartMs() <= 350.0f,
          "the page is whole within a third of a second");
    check(kThonkMs < poweroff::kFadeMs,
          "the thonk is quicker than the collapse's fade: it arrives, not eases");
  }

  if (failures == 0) std::printf("power_on_warm_up: all checks passed\n");
  return failures == 0 ? 0 : 1;
}
