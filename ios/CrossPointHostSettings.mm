// iOS backend for sim_host_settings: the values the owner types in
// Settings > CrossPoint X3 that the emulated e-ink panel cannot take.
//
// There is exactly one today, and it is a credential, so this file is
// deliberately small and separate from ios/CrossPointPrefs.mm: the token's read
// path should be short enough to audit in one screen. Three rules it follows
// and nothing here may relax:
//
//   * NEVER log the value, whole or truncated. The LENGTH is fine and is the
//     only thing that ever leaves here.
//   * It is not written anywhere. NSUserDefaults is the one copy this build
//     keeps; see SimHostSettings.h for why it is deliberately NOT seeded into
//     SETTINGS.githubToken, which would persist it onto the simulated card that
//     File Transfer serves over the LAN.
//   * The Settings.bundle row is marked IsSecure, so iOS masks it while it is
//     typed and does not offer it to the QuickType bar.
//
// NSUserDefaults is thread-safe, and this is called from the FreeRTOS task
// thread that runs the fetch rather than from the SDL main thread -- unlike
// most of CrossPointPrefs.mm, which touches UIKit and is main-thread only.

#include "SimHostSettings.h"

#import <Foundation/Foundation.h>

#include <cstring>
#include <string>

namespace sim_host_settings {
namespace {

// MUST match the Key of the PSTextFieldSpecifier in
// ios/Settings.bundle/Root.plist. A typo here is silent -- -stringForKey:
// answers nil and the owner sees "not configured" forever, having typed it --
// so tests/host_settings_test.cpp reads both files as text and fails when the
// two names drift apart.
NSString *const kGithubToken = @"githubToken";

}  // namespace

size_t githubToken(char *out, size_t cap) {
  // An explicit pool: this runs on the FreeRTOS task thread that drives the
  // fetch, and src/freertos/ maps xTaskCreate onto std::thread, which installs
  // none. Without it the two autoreleased objects below leak and the runtime
  // logs a "no pool in place" line per call. The memcpy into `out` finishes
  // inside the block, so nothing here outlives it.
  @autoreleasepool {
    NSString *stored =
        [[NSUserDefaults standardUserDefaults] stringForKey:kGithubToken];
    if (!stored) {
      if (out && cap != 0) out[0] = '\0';
      return 0;
    }

    // Leading/trailing whitespace is what a paste from a browser or a password
    // manager brings with it, and a token with a trailing newline authenticates
    // as nothing at all with no clue on screen as to why.
    NSString *trimmed = [stored
        stringByTrimmingCharactersInSet:[NSCharacterSet
                                            whitespaceAndNewlineCharacterSet]];
    // The copy and the truncation are sim_host_settings::copyToken's, not a
    // second implementation of them -- that is what puts this path under the
    // poison-buffer tests in tests/host_settings_test.cpp.
    return copyToken(trimmed.UTF8String, out, cap);
  }
}

bool hasSettingsSurface() { return true; }

}  // namespace sim_host_settings
