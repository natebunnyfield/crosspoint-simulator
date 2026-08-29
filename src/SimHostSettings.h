#pragma once

// Host-provided CONFIGURATION, for the one class of setting the emulated e-ink
// panel cannot take: a value the owner must TYPE, on a platform whose only
// keyboard-and-text-field surface is the host's own Settings app.
//
// This is a free-function hook, deliberately NOT a new field on the firmware's
// CrossPointSettings -- the same reasoning as SimWiFiHost.h and
// SimulatorOverlay.h. The firmware's settings live in a file on the card and
// travel with it; these do not. They are properties of THIS HOST running the
// app, and on device hardware there is nothing to read.
//
// The contract is narrow on purpose, and there is exactly one value in it.
//
// THE GITHUB TOKEN. Update Library fetches a release from a PRIVATE repo, so
// every request carries "Authorization: Bearer <token>", read from
// SETTINGS.githubToken. On a device that field is set by hand-editing
// /.crosspoint/settings.json on the card. ON A PHONE THERE IS NO WAY TO EDIT
// THAT FILE, so the feature was unconfigurable there and the screen's own hint
// ("Set githubToken in settings.json, then try again") was advice the owner
// could not follow. iOS Settings > CrossPoint X3 > GitHub Token is the home it
// gets, and this is the wire from there to the fetch.
//
// IT IS NEVER WRITTEN BACK TO THE CARD. The host store stays the only copy the
// host build keeps: LibraryUpdater asks for the token at the moment it builds
// the header, rather than seeding SETTINGS.githubToken at boot, because
// anything that lands in that field is persisted into
// /.crosspoint/settings.json by the next settings save -- and on iOS that
// directory is served over the LAN by the file-transfer server and WebDAV the
// moment the owner opens File Transfer. Not writing it is one fewer copy of a
// credential, for no loss of function.
//
// NEVER LOG THE VALUE, in whole or in part. The length is fine; the bytes are
// not.

#include <cstddef>
#include <cstdlib>
#include <cstring>

#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif

// Overridable so the host branch can be exercised off-device: the real backend
// is iOS-only and cannot be compiled or run on Linux, which would otherwise
// leave the branch the firmware takes on a phone with no test at all. Same
// escape hatch, and the same reason, as CROSSPOINT_SIM_HOST_WIFI and
// CROSSPOINT_SIM_HOST_HTTP. tests/host_settings_test.cpp defines this and
// supplies its own backend.
#ifndef CROSSPOINT_SIM_HOST_SETTINGS
#if defined(__APPLE__) && TARGET_OS_IPHONE
#define CROSSPOINT_SIM_HOST_SETTINGS 1
#else
#define CROSSPOINT_SIM_HOST_SETTINGS 0
#endif
#endif

namespace sim_host_settings {

// The name of the desktop escape hatch, so a doc or a test can name it once.
// Deliberately not consulted on the host path: a phone has no environment to
// set, and a build that read both would have two answers to one question.
inline constexpr char kGithubTokenEnvVar[] = "CROSSPOINT_SIM_GITHUB_TOKEN";

// THE COPY ITSELF, in ONE place, because it is the part with teeth and every
// backend was re-typing it.
//
// `out` may be null and `cap` may be 0; the result is always NUL-terminated
// when there is room for a terminator, and never writes `cap` bytes or more.
// Returns the source's FULL length -- see githubToken() below for why that
// rather than the number of bytes written.
//
// It lives here rather than in each backend so that the poison-buffer sweep in
// tests/host_settings_test.cpp exercises the SHIPPED code. The first version of
// this file had the same six lines written out three times -- the inline hatch,
// the Objective-C backend, and the test's own stand-in -- which meant the test
// proved its own copy correct and the phone's copy not at all. Adversarial
// review, 2026-08-28.
inline size_t copyToken(const char *value, char *out, size_t cap) {
  if (out && cap != 0) out[0] = '\0';
  if (!value || !value[0]) return 0;
  const size_t length = std::strlen(value);
  if (out && cap != 0) {
    const size_t copied = length < cap - 1 ? length : cap - 1;
    std::memcpy(out, value, copied);
    out[copied] = '\0';
  }
  return length;
}

// Copy the host's GitHub token into `out`, NUL-terminated.
//
// Returns the token's FULL length, snprintf-style, so a caller can tell that a
// truncation happened WITHOUT ever holding the untruncated value: bytes
// actually written are min(returned, cap - 1). 0 means the host has none, which
// is the ordinary answer everywhere but a configured phone.
//
// Truncates rather than overflowing, because the destination is a fixed
// char[104] in the firmware and the alternative to a short token is a smashed
// stack. A truncated token will fail authentication; that is why the length
// comes back, so the one call site can say so in a log line.
//
// Safe to call from any thread -- the iOS backend reads NSUserDefaults, which
// is thread-safe, and the fetch runs on a FreeRTOS task thread rather than the
// SDL main thread.
size_t githubToken(char *out, size_t cap);

// Does this host offer a settings surface the owner can actually reach?
//
// It decides WHICH SENTENCE the "no token" screen prints -- "settings.json" is
// the truth on a device and on the desktop simulator, and a dead end on a
// phone. Kept apart from githubToken() above because the two answer different
// questions: a phone with an empty field has a surface and no token.
bool hasSettingsSurface();

#if !CROSSPOINT_SIM_HOST_SETTINGS

// No host settings surface. The token still has a route in -- an environment
// variable -- because otherwise the whole authenticated path would be
// unexercisable off-device: the card's settings.json is the owner's route, but
// a headless QA run should not have to write a credential into a file inside
// the simulated card to prove the plumbing. Unset (the default, and the only
// state the desktop canary ever sees) every call folds to 0 and nothing about
// the existing behavior moves.
inline size_t githubToken(char *out, size_t cap) {
  return copyToken(std::getenv(kGithubTokenEnvVar), out, cap);
}

// FALSE even when the environment variable above is set. The variable is a QA
// hatch, not a place the owner can be sent to; the sentence this picks has to
// name somewhere he can go, and on the desktop that is settings.json.
inline bool hasSettingsSurface() { return false; }

#endif

}  // namespace sim_host_settings
