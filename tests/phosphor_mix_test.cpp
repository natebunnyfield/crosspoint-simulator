// Host test for src/PhosphorMix.h.
//
// Every failure mode is a wrong color or a wrong decay, which no compiler and
// no other test can see -- the same reason PanelPalette and PhosphorGrain have
// theirs.

#include "PhosphorMix.h"

#include <cstdio>
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
    // P4's second component is an EXACT compound match; pin the identity so a
    // future remap of the table cannot silently downgrade it.
    const PremixRecipe *p4 = recipeFor("P4");
    check(p4 && std::strcmp(p4->b, "P22G") == 0,
          "P4's yellow-green is P22G, the exact compound");
  }

  if (failures == 0) std::printf("phosphor_mix_test: all checks passed\n");
  return failures ? 1 : 0;
}
