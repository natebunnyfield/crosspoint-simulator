#pragma once

// Desktop-only. Reads the settings file described in SimulatorSettingsFile.h
// and pushes it through the same SimulatorOverlay setters the iOS harness uses,
// so the two platforms drive one set of dials from one set of keys.
//
// Cheap to call every frame: it stats one file and returns unless the mtime
// moved. Compiled to nothing on iOS, which has NSUserDefaults instead.
namespace simsettings {
void pollSettingsFile();
}
