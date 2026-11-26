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
// The contract is narrow on purpose, and there are two values in it, both
// credentials with the same shape.
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
// THE CLAUDE API KEY (2026-09-05). ClaudeChat reads its key from
// /claude-key.txt on the card root (src/notes/ClaudeChat.cpp, readApiKey), the
// same one-line-file convention as the GitHub token and for the same reason a
// phone cannot use it: there is no way to edit a file on the card from
// Settings.app. iOS Settings > CrossPoint X3 > Claude API Key is the home it
// gets, next to the GitHub token, and claudeApiKey() below is the wire from
// there to ClaudeChat's readApiKey().
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
// SINCE 2026-11-26 the paragraphs above are history: the firmware's key store
// (crosspoint-reader src/util/KeyStore.h) is the only reader and writer of
// both values, through the getters and setters here, and nothing reads a key
// from the card or settings.json any more (the old copies are ignored, not
// migrated: owner ruling, no backwards compatibility while in alpha). The
// firmware's own Settings rows set them on every host; on the desktop they
// land in host-keys.txt beside the card. crosspoint-reader
// docs/keys-and-paste-2026-11-26.md.
//
// NEVER LOG THE VALUE, in whole or in part. The length is fine; the bytes are
// not.

#include <cstddef>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <string>
#include <sys/stat.h>

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

// The simulated card's root (HalStorage.cpp); the desktop key file sits beside it.
std::string simulatorStorageRootForHost();

namespace sim_host_settings {

// The name of the desktop escape hatch, so a doc or a test can name it once.
// Deliberately not consulted on the host path: a phone has no environment to
// set, and a build that read both would have two answers to one question.
inline constexpr char kGithubTokenEnvVar[] = "CROSSPOINT_SIM_GITHUB_TOKEN";
// Same escape hatch, for the Claude API key.
inline constexpr char kClaudeApiKeyEnvVar[] = "CROSSPOINT_SIM_CLAUDE_KEY";

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

// Same contract as githubToken() above, for the Claude API key ClaudeChat
// sends as the x-api-key header. A separate function rather than a second
// parameter to githubToken(), because the two are unrelated credentials for
// unrelated features that happen to share this one mechanism -- see
// ClaudeChat.cpp's readApiKey().
size_t claudeApiKey(char *out, size_t cap);

// Does this host offer a settings surface the owner can actually reach?
//
// It decides WHICH SENTENCE the "no token" screen prints: the firmware's own
// Settings row everywhere, plus the Settings app on a phone. Kept apart from githubToken() above because the two answer different
// questions: a phone with an empty field has a surface and no token.
bool hasSettingsSurface();

// WRITE the key, from the firmware's own Settings rows and the device web
// page's Keys section (firmware util/KeyStore.h, owner 2026-11-26). `value`
// null or empty REMOVES the key. Returns false when the store refused it.
// The iOS backend writes the same NSUserDefaults keys the Settings.app rows
// do (storage ruling 2026-11-26, "NVS + NSUserDefaults"), so either surface
// sees the other's value. NEVER log `value`.
bool setGithubToken(const char *value);
bool setClaudeApiKey(const char *value);

#if !CROSSPOINT_SIM_HOST_SETTINGS

// The desktop's key store: one file BESIDE the simulated card, never inside it
// (Manage Files, File Transfer and WebDAV all show the card), next to the
// desktop's settings.json. Lines of `name=value`. Owner-only permissions.
inline std::string desktopKeyFilePath() {
  std::string root = ::simulatorStorageRootForHost();
  while (!root.empty() && root.back() == '/') root.pop_back();
  const size_t slash = root.find_last_of('/');
  const std::string parent = slash == std::string::npos ? std::string(".") : root.substr(0, slash);
  return parent + "/host-keys.txt";
}

inline std::string desktopKeyRead(const char *name) {
  std::string found;
  FILE *f = std::fopen(desktopKeyFilePath().c_str(), "rb");
  if (!f) return found;
  char line[512];
  const size_t nameLen = std::strlen(name);
  while (std::fgets(line, sizeof(line), f)) {
    if (std::strncmp(line, name, nameLen) == 0 && line[nameLen] == '=') {
      found = line + nameLen + 1;
      while (!found.empty() && (found.back() == '\n' || found.back() == '\r')) found.pop_back();
    }
  }
  std::fclose(f);
  return found;
}

inline bool desktopKeyWrite(const char *name, const char *value) {
  // Read the other names back, then rewrite the whole file.
  std::string keep;
  if (FILE *f = std::fopen(desktopKeyFilePath().c_str(), "rb")) {
    char line[512];
    const size_t nameLen = std::strlen(name);
    while (std::fgets(line, sizeof(line), f)) {
      if (std::strncmp(line, name, nameLen) == 0 && line[nameLen] == '=') continue;
      keep += line;
    }
    std::fclose(f);
  }
  if (value && value[0]) {
    if (std::strchr(value, '\n') || std::strchr(value, '\r')) return false;
    keep += name;
    keep += '=';
    keep += value;
    keep += '\n';
  }
  const std::string path = desktopKeyFilePath();
  FILE *f = std::fopen(path.c_str(), "wb");
  if (!f) return false;
  const bool ok = std::fwrite(keep.data(), 1, keep.size(), f) == keep.size();
  std::fclose(f);
  chmod(path.c_str(), 0600);  // owner-only: it holds keys
  return ok;
}

// No host settings surface. The token still has a route in -- an environment
// variable -- because otherwise the whole authenticated path would be
// unexercisable off-device without typing one in: a headless QA run should not
// have to drive the Settings row to prove the plumbing. Unset (the default, and the only
// state the desktop canary ever sees) every call folds to 0 and nothing about
// the existing behavior moves.
// The environment variable first (the QA hatch, unchanged), then the desktop
// key file the firmware's Settings rows write.
inline size_t githubToken(char *out, size_t cap) {
  if (const char *env = std::getenv(kGithubTokenEnvVar); env && env[0]) return copyToken(env, out, cap);
  return copyToken(desktopKeyRead("githubToken").c_str(), out, cap);
}

// Same reasoning as githubToken() above, for CROSSPOINT_SIM_CLAUDE_KEY.
inline size_t claudeApiKey(char *out, size_t cap) {
  if (const char *env = std::getenv(kClaudeApiKeyEnvVar); env && env[0]) return copyToken(env, out, cap);
  return copyToken(desktopKeyRead("claudeApiKey").c_str(), out, cap);
}

inline bool setGithubToken(const char *value) { return desktopKeyWrite("githubToken", value); }
inline bool setClaudeApiKey(const char *value) { return desktopKeyWrite("claudeApiKey", value); }

// FALSE even when the environment variables above are set. The variables are a
// QA hatch, not a place the owner can be sent to; the sentence this picks has
// to name somewhere he can go, and on the desktop that is the firmware's own
// Settings row (the hint the "no token" screen prints when this is false).
inline bool hasSettingsSurface() { return false; }

#endif

}  // namespace sim_host_settings
