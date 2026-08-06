#include "SimulatorBuildIdentity.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>

// This TU belongs to crosspoint_core, so the constants below are the CORE's —
// that is the whole point of the file. See the header for what it guards.
SimulatorBuildIdentity coreBuildIdentity() { return localBuildIdentity(); }

void verifyBuildIdentityMatchesCore(const SimulatorBuildIdentity &local,
                                    const char *who) {
  const SimulatorBuildIdentity core = coreBuildIdentity();
  const bool sameDevice = std::strcmp(local.device, core.device) == 0;
  const bool match = sameDevice && local.logicalWidth == core.logicalWidth &&
                     local.logicalHeight == core.logicalHeight &&
                     local.renderScale == core.renderScale;

  if (match) {
    std::printf("[BUILD] %s and firmware core agree: %s, %ux%u logical, %dx "
                "render scale\n",
                who, core.device, core.logicalWidth, core.logicalHeight,
                core.renderScale);
    std::fflush(stdout);
    return;
  }

  std::fprintf(stderr,
               "\n[BUILD] FATAL: split-brain binary. %s and the firmware core "
               "compiled against different build settings.\n"
               "  %-14s device=%s logical=%ux%u renderScale=%d\n"
               "  %-14s device=%s logical=%ux%u renderScale=%d\n"
               "A compile definition is set on one CMake target and not the "
               "other. Cross-cutting defines belong on crosspoint_core PUBLIC, "
               "never PRIVATE on the app target -- see ios/CMakeLists.txt.\n\n",
               who, who, local.device, local.logicalWidth, local.logicalHeight,
               local.renderScale, "firmware core", core.device,
               core.logicalWidth, core.logicalHeight, core.renderScale);
  std::fflush(stderr);
  // Nothing downstream of here is trustworthy: the halves disagree about panel
  // geometry and about which board's capabilities the firmware may use. Dying
  // at startup is how this stops being a bug report about a distant feature.
  std::abort();
}
