#pragma once

// A diagnostics log the OWNER can read, on the phone, without a Mac.
//
// Every Speak Screen round trip so far has failed the same way: the phone
// state was invisible. SDL_Log lines die in os_log on a TestFlight build, so
// each report came back as a symptom with no evidence, and two fixes were
// shipped on reasoning about what the state "must" be.
//
// The harness chdir()s into the app's Documents directory (the emulated SD
// card), and Info.plist exposes that directory in the Files app as
// On My iPhone -> CrossPoint X3. So a log written to diagnostics/a11y.log is
// readable and share-able FROM THE PHONE: open the Files app, tap the file,
// long-press to share. That closes the loop a TestFlight build cannot close
// any other way.
//
// Lines are timestamped since launch and mirrored to SDL_Log, so a device with
// a Mac attached still gets them in the console. The file survives relaunches
// (rotated, not truncated) precisely because "it did not work an hour ago"
// must still be answerable.
//
// This is the ACCESSIBILITY log. Keep it scoped: page publishes, element
// state, assistive-tech transitions, geometry. It is not a general logger --
// growing it into one would bury the twenty lines that matter under thousands
// that do not.

#include <cstdarg>

// Append one line, printf-style. Thread-safe; called from the SDL main thread
// in practice. Mirrors to SDL_Log with an [A11Y-FILE] prefix.
void CrossPointDiag_log(const char *fmt, ...) __attribute__((format(printf, 1, 2)));

// Where the log lands, relative to the card root.
inline constexpr const char *kCrossPointDiagPath = "diagnostics/a11y.log";
