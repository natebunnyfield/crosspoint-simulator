// iOS backend for sim_host_screen. See the header for why this exists.

#include "SimHostScreen.h"

#import <UIKit/UIKit.h>

namespace sim_host_screen {

void setKeepAwake(bool keepAwake) {
  // isIdleTimerDisabled is main-thread-only, and callers are firmware task
  // threads (WebServer::begin runs on one). dispatch_async rather than sync:
  // sync from the main thread would deadlock, and nothing here needs to know
  // when the flag actually landed.
  dispatch_async(dispatch_get_main_queue(), ^{
    UIApplication.sharedApplication.idleTimerDisabled = keepAwake ? YES : NO;
  });
}

int maximumFramesPerSecond() {
  // The window's own screen where there is one, so an app on an external
  // display reports that display rather than the built-in panel. mainScreen is
  // the fallback and is what a plain single-screen phone answers with anyway.
  UIScreen *screen = nil;
  for (UIScene *scene in UIApplication.sharedApplication.connectedScenes) {
    if ([scene isKindOfClass:UIWindowScene.class]) {
      screen = ((UIWindowScene *)scene).screen;
      if (screen) break;
    }
  }
  if (!screen) screen = UIScreen.mainScreen;
  return screen ? (int)screen.maximumFramesPerSecond : 0;
}

bool highFrameRateDeclared() {
  // READ BACK FROM THE BUNDLE, not from a compile-time constant. The key is
  // written by ios/CMakeLists.txt into a generated Info.plist; asking the
  // bundle is the only way for the log line to be about the binary that is
  // running rather than about what the source intended.
  id v = NSBundle.mainBundle.infoDictionary[@"CADisableMinimumFrameDuration"];
  return [v respondsToSelector:@selector(boolValue)] && [v boolValue];
}

}  // namespace sim_host_screen
