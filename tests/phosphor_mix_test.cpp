// Host test for src/PhosphorMix.h.
//
// Every failure mode is a wrong color or a wrong decay, which no compiler and
// no other test can see -- the same reason PanelPalette and PhosphorGrain have
// theirs.

#include "PhosphorMix.h"

#include <cstdio>
#include <algorithm>
#include <cmath>
#include <cstring>

using namespace phosphormix;
using panelpalette::Palette;

static int failures = 0;
static void check(bool ok, const char *what) {
  if (!ok) { std::printf("FAIL: %s\n", what); failures++; }
}

static int presetOf(const char *pnum) {
  for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
    const char *p = panelpalette::kPresetInfo[i].phosphor;
    if (p && std::strcmp(p, pnum) == 0) return panelpalette::kPresetInfo[i].preset;
  }
  return -1;
}

static bool samePalette(const Palette &a, const Palette &b) {
  return std::memcmp(a.ink, b.ink, 3) == 0 && std::memcmp(a.paper, b.paper, 3) == 0;
}

int main() {
  const int P1 = presetOf("P1"), P3 = presetOf("P3"), P11 = presetOf("P11");
  const int P33 = presetOf("P33"), P15 = presetOf("P15");
  check(P1 > 0 && P3 > 0 && P11 > 0 && P33 > 0 && P15 > 0, "test phosphors exist");

  // --- THE PREMIX LIST IS EXACTLY THE PHYSICAL ONE -------------------------
  // Blends carry a "+" or a second compound; cascades carry an afterglow. A row
  // wrongly on this list disappears from the ingredient shelf; a row wrongly
  // off it lets a mixture be mixed. Both directions pinned.
  {
    const char *premix[] = {"P4", "P6", "P7", "P14", "P17", "P18", "P23", "P40"};
    for (const char *p : premix)
      check(isPremixPhosphor(p), "premix recognised");
    const char *pure[] = {"P1", "P3", "P11", "P22G", "P22R", "P22B",
                          "P35",  // ZnS,ZnSe:Ag is a solid solution, ONE lattice
                          "P45", "P20", "P15", "P33"};
    for (const char *p : pure)
      check(!isPremixPhosphor(p), "pure phosphor not flagged as premix");
    check(!isPremixPhosphor("P2") && isPremixPhosphor("P23"),
          "prefix does not match: P2 pure while P23 premix");
    for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
      const auto &info = panelpalette::kPresetInfo[i];
      if (!info.phosphor) 
        check(!isMixablePreset(info.preset), "a non-phosphor row is never an ingredient");
    }
  }

  // --- A SINGLE-COMPONENT BLEND IS THAT PHOSPHOR, EXACTLY ------------------
  // The identity case is what makes the round trip through linear light
  // testable: sRGB -> linear -> weighted(1) -> sRGB must be byte-exact.
  {
    Component c[] = {{P1, 3}};
    const Result r = mixBlend(c, 1);
    check(samePalette(r.dark, panelpalette::resolve(P1, true, -1, -1)),
          "one-component blend reproduces the phosphor's dark pair exactly");
    check(samePalette(r.light, panelpalette::resolve(P1, false, -1, -1)),
          "…and its light pair");
    check(r.trailMs == panelpalette::trailMsForPreset(P1), "…and its trail");
    check(!r.hasTail, "one component has nothing to shift toward");
  }

  // --- BLENDING IS LINEAR-LIGHT, NOT BYTE AVERAGING ------------------------
  // The convexity of the gamma curve means a byte-average is DARKER than the
  // physical mixture. Green P1 ink 33FF33 + blue P11 ink: the linear mix's G
  // channel must be brighter than the byte midpoint.
  {
    Component c[] = {{P1, 1}, {P11, 1}};
    const Result r = mixBlend(c, 2);
    const Palette g = panelpalette::resolve(P1, true, -1, -1);
    const Palette b = panelpalette::resolve(P11, true, -1, -1);
    const int byteMid = (g.ink[1] + b.ink[1]) / 2;
    check(r.dark.ink[1] > byteMid,
          "50/50 blend is brighter than the byte midpoint (linear light)");
    // and weights matter: 3:1 toward green is greener than 1:1
    Component heavy[] = {{P1, 3}, {P11, 1}};
    const Result rh = mixBlend(heavy, 2);
    check(rh.dark.ink[1] > r.dark.ink[1] && rh.dark.ink[2] < r.dark.ink[2],
          "weights pull the mixture toward the heavier component");
  }

  // --- THE TRAIL IS THE SLOWEST COMPONENT'S, AND SO IS THE TAIL ------------
  // P33 (1000 ms class) blended with P15 (extremely short): the mixture's
  // afterglow lasts as long as P33 and dies toward P33's color, because P15 has
  // already gone dark.
  {
    Component c[] = {{P15, 1}, {P33, 1}};
    const Result r = mixBlend(c, 2);
    check(r.trailMs == panelpalette::trailMsForPreset(P33),
          "blend trail is the slowest component's");
    const Palette p33 = panelpalette::resolve(P33, true, -1, -1);
    check(r.hasTail && std::memcmp(r.tail, p33.ink, 3) == 0,
          "what lingers is the slow component's ink");
    // equal-speed blend: dims without changing color
    Component eq[] = {{P1, 1}, {P3, 1}};
    const Result re = mixBlend(eq, 2);
    check(re.trailMs > 0.0f, "equal-ish blend still glows");
  }

  // --- THREE COMPONENTS: THE TRIAD IS THE COLOR TUBE'S OWN WHITE -----------
  // A color CRT made every color, white included, from exactly three
  // phosphors. Blending our P22R + P22G + P22B must come out near-neutral --
  // the channels within a factor that reads as white, not as any member's own
  // hue -- and moving one gun's weight must pull the mixture toward that gun.
  {
    const int R22 = presetOf("P22R"), G22 = presetOf("P22G"), B22 = presetOf("P22B");
    check(R22 > 0 && G22 > 0 && B22 > 0, "the triad exists");
    Component triad[] = {{R22, 1}, {G22, 1}, {B22, 1}};
    const Result w = mixBlend(triad, 3);
    const int mx = std::max({w.dark.ink[0], w.dark.ink[1], w.dark.ink[2]});
    const int mn = std::min({w.dark.ink[0], w.dark.ink[1], w.dark.ink[2]});
    check(mn > 0 && mx < 256 && (mx - mn) < 96,
          "equal-weight triad ink is near-neutral: the tube's white");
    Component redHeavy[] = {{R22, 5}, {G22, 1}, {B22, 1}};
    const Result rw = mixBlend(redHeavy, 3);
    check(rw.dark.ink[0] > w.dark.ink[0] && rw.dark.ink[1] < w.dark.ink[1],
          "turning up one gun pulls the mixture toward it");
    // and four components is the ceiling, enforced not crashed
    Component four[] = {{R22, 1}, {G22, 1}, {B22, 1}, {presetOf("P1"), 1}};
    const Result f4 = mixBlend(four, 4);
    check(f4.trailMs > 0.0f, "four components mix");
    Component five[] = {{R22, 1}, {G22, 1}, {B22, 1}, {presetOf("P1"), 1},
                        {presetOf("P3"), 1}};
    const Result f5 = mixBlend(five, 5);
    check(std::memcmp(f5.dark.ink, f4.dark.ink, 3) == 0,
          "a fifth component is ignored at the cap, not a buffer overrun");
  }

  // --- PREMIXES ARE REFUSED AS INGREDIENTS ---------------------------------
  {
    const int P7 = presetOf("P7"), P4 = presetOf("P4");
    Component c[] = {{P1, 1}, {P7, 1}};
    const Result r = mixBlend(c, 2);
    check(samePalette(r.dark, panelpalette::resolve(P1, true, -1, -1)),
          "a premix in a blend is skipped, leaving the pure component alone");
    const Result rp = mixParts(P4, P1, P1);
    check(samePalette(rp.dark, panelpalette::kDefaultDark),
          "a premix as a part falls back to default rather than being used");
    const Result rc = mixCascade(P7, P1);
    check(samePalette(rc.dark, panelpalette::kDefaultDark),
          "a premix as a cascade layer falls back too");
  }

  // --- PARTS: EACH ROLE COMES FROM ITS DONOR, BOTH POLARITIES --------------
  {
    const Result r = mixParts(P1, P11, P33);
    const Palette gD = panelpalette::resolve(P1, true, -1, -1);
    const Palette gL = panelpalette::resolve(P1, false, -1, -1);
    const Palette bD = panelpalette::resolve(P11, true, -1, -1);
    const Palette bL = panelpalette::resolve(P11, false, -1, -1);
    check(std::memcmp(r.dark.ink, gD.ink, 3) == 0 &&
              std::memcmp(r.light.ink, gL.ink, 3) == 0,
          "parts: ink from the ink donor in both polarities");
    check(std::memcmp(r.dark.paper, bD.paper, 3) == 0 &&
              std::memcmp(r.light.paper, bL.paper, 3) == 0,
          "parts: paper from the paper donor in both polarities");
    check(r.trailMs == panelpalette::trailMsForPreset(P33),
          "parts: trail from the trail donor");
    check(!r.hasTail, "parts is not a mixture, so nothing shifts color");
  }

  // --- CASCADE: FLASH PAINTS, PERSISTENCE LINGERS --------------------------
  {
    const Result r = mixCascade(P11, P33);
    check(samePalette(r.dark, panelpalette::resolve(P11, true, -1, -1)),
          "cascade: the flash layer's palette paints the page");
    check(r.trailMs == panelpalette::trailMsForPreset(P33),
          "cascade: the persistence layer's trail");
    const Palette p33 = panelpalette::resolve(P33, true, -1, -1);
    check(r.hasTail && std::memcmp(r.tail, p33.ink, 3) == 0,
          "cascade: what lingers is the persistence layer's ink");
  }

  // --- A MIX UNDER CONSTRUCTION PAINTS AS IT GOES --------------------------
  // The first role picked must show on the page; unset roles take their part
  // from the Default preset. The old behavior blanked to the full default
  // until every role was set, which on a phone read as "picking does nothing".
  {
    const Result r = mixParts(P1, -1, -1);
    const Palette gD = panelpalette::resolve(P1, true, -1, -1);
    check(std::memcmp(r.dark.ink, gD.ink, 3) == 0,
          "parts: the one picked role paints immediately");
    check(std::memcmp(r.dark.paper, panelpalette::kDefaultDark.paper, 3) == 0,
          "parts: the unset paper role is the Default preset's");
    const Result rc = mixCascade(P11, -1);
    check(std::memcmp(rc.dark.ink,
                      panelpalette::resolve(P11, true, -1, -1).ink, 3) == 0,
          "cascade: the flash paints before the persistence is chosen");
    check(rc.trailMs == panelpalette::trailMsForPreset(panelpalette::kPresetDefault),
          "cascade: unset persistence is the Default preset's (no glow)");
    // ...and a premix donor still bails whole, exactly as before.
    const int P4 = presetOf("P4");
    const Result rp = mixParts(P4, -1, -1);
    check(std::memcmp(rp.dark.ink, panelpalette::kDefaultDark.ink, 3) == 0,
          "parts: a premix donor still falls back whole");
  }

  // --- DEGENERATE INPUT IS THE DEFAULT PAGE, NOT GARBAGE -------------------
  {
    const Result r = mixBlend(nullptr, 0);
    check(samePalette(r.dark, panelpalette::kDefaultDark) &&
              samePalette(r.light, panelpalette::kDefaultLight),
          "an empty blend is the default page");
    Component junk[] = {{-1, 5}, {99999, 2}};
    const Result rj = mixBlend(junk, 2);
    check(samePalette(rj.dark, panelpalette::kDefaultDark),
          "unused slots and unknown presets contribute nothing");
    Component zero[] = {{P1, 0}, {P11, -3}};
    const Result rz = mixBlend(zero, 2);
    check(rz.dark.ink[1] > 0 && rz.dark.ink[2] > 0,
          "weights below 1 clamp to 1 rather than dividing by zero");
  }

  // --- EVERY PREMIX HAS A RECIPE, AND EVERY RECIPE RESOLVES ----------------
  // The recipe table is data; what can rot silently is a component name that
  // stops matching a row, or a recipe whose ingredient is itself a premix.
  {
    const char *premix[] = {"P4", "P6", "P7", "P14", "P17", "P18", "P23", "P40"};
    for (const char *p : premix) {
      const PremixRecipe *r = recipeFor(p);
      check(r != nullptr, "every premix has a recipe");
      if (!r) continue;
      const int pa = presetOf(r->a), pb = presetOf(r->b);
      check(pa > 0 && pb > 0, "recipe components name real rows");
      check(isMixablePreset(pa) && isMixablePreset(pb),
            "recipe components are pure, never premixes themselves");
      if (r->mode == Blend)
        check(r->weightA >= 1 && r->weightB >= 1, "blend weights usable");
    }
    check(recipeFor("P1") == nullptr, "pure phosphors have no recipe");
    check(recipeFor(nullptr) == nullptr, "null is not a recipe");
    // The recipes are FITTED (2026-08-21), and the fit is the contract: each
    // blend recipe's computed dark ink must land within dE 12 of its shipped
    // premix, and no recipe may use P10 -- a dark-trace screen absorbs, so a
    // fit that leans on it is an artifact.
    auto lab3 = [](const unsigned char c[3], float out[3]) {
      auto lin = [](unsigned char v) {
        const float f = v / 255.0f;
        return f <= 0.04045f ? f / 12.92f : std::pow((f + 0.055f) / 1.055f, 2.4f);
      };
      const float r = lin(c[0]), g = lin(c[1]), b = lin(c[2]);
      const float X = .4124f * r + .3576f * g + .1805f * b;
      const float Y = .2126f * r + .7152f * g + .0722f * b;
      const float Z = .0193f * r + .1192f * g + .9505f * b;
      auto f = [](float t) { return t > 0.008856f ? std::cbrt(t) : 7.787f * t + 16.0f / 116; };
      const float fx = f(X / 0.95047f), fy = f(Y), fz = f(Z / 1.08883f);
      out[0] = 116 * fy - 16; out[1] = 500 * (fx - fy); out[2] = 200 * (fy - fz);
    };
    for (int i = 0; i < kPremixRecipeCount; i++) {
      const PremixRecipe &r = kPremixRecipes[i];
      check(std::strcmp(r.a, "P10") && std::strcmp(r.b, "P10") &&
                (!r.c || std::strcmp(r.c, "P10")),
            "no recipe uses the dark-trace screen as a donor");
      if (r.mode != Blend) continue;
      Component c[3] = {{presetOf(r.a), r.weightA},
                        {presetOf(r.b), r.weightB},
                        {r.c ? presetOf(r.c) : -1, r.weightC}};
      const Result m = mixBlend(c, 3);
      const panelpalette::Palette ship =
          panelpalette::resolve(presetOf(r.phosphor), true, -1, -1);
      float la[3], lb[3];
      lab3(m.dark.ink, la); lab3(ship.ink, lb);
      const float d = std::sqrt((la[0]-lb[0])*(la[0]-lb[0]) +
                                (la[1]-lb[1])*(la[1]-lb[1]) +
                                (la[2]-lb[2])*(la[2]-lb[2]));
      check(d < 12.0f, "a fitted recipe lands near its shipped premix");
    }
  }

  // --- THE PERSISTENCE BANDS COVER THE SHELF, IN ORDER ---------------------
  // Every pure row lands in a band, band index is monotonic in trail, and no
  // band is empty -- an empty band is a header over nothing.
  {
    int counts[kTrailBandCount] = {};
    float prevTrail = -1.0f;
    for (int i = 0; i < panelpalette::kPresetInfoCount; i++) {
      const auto &info = panelpalette::kPresetInfo[i];
      if (!info.phosphor || isPremixPhosphor(info.phosphor)) continue;
      const float t = panelpalette::trailMsForPreset(info.preset);
      const int b = trailBand(t);
      check(b >= 0 && b < kTrailBandCount, "every pure row lands in a band");
      counts[b]++;
    }
    for (int b = 0; b < kTrailBandCount; b++)
      check(counts[b] > 0, "no persistence band is empty");
    check(trailBand(16.7f) == 0 && trailBand(126.5f) == 1 &&
              trailBand(282.8f) == 2 && trailBand(1095.4f) == 3 &&
              trailBand(2828.4f) == 4,
          "the band edges sit in the data's own gaps");
    check(trailBand(20.0f) < trailBand(63.2f) &&
              trailBand(400.0f) < trailBand(692.8f),
          "band index is monotonic across the gaps");
  }

  // --- WITHIN A BAND: TRAIL, THEN HUE, RED FIRST ---------------------------
  {
    // Trail dominates: P3 at 322 ms sorts after every 283 ms row in its band.
    const int P3 = presetOf("P3"), P45 = presetOf("P45");
    check(trailBand(322.5f) == trailBand(282.8f) &&
              shelfSortKey(P3) > shelfSortKey(P45),
          "a longer trail sorts later inside the same band");
    // Hue breaks ties on the rotated wheel: among the 283 ms rows, red-orange
    // P13 before yellow P28 before green P43 before near-neutral white P45.
    const int P13 = presetOf("P13"), P28 = presetOf("P28"), P43 = presetOf("P43");
    check(shelfSortKey(P13) < shelfSortKey(P28) &&
              shelfSortKey(P28) < shelfSortKey(P43) &&
              shelfSortKey(P43) < shelfSortKey(P45),
          "equal trails order by hue, red first, blue-whites late");
  }

  if (failures == 0) std::printf("phosphor_mix_test: all checks passed\n");
  return failures ? 1 : 0;
}
