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

}  // namespace sim_host_screen
