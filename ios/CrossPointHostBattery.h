#pragma once

// iOS battery adapter. Starts UIDevice battery monitoring, publishes the
// phone's level and charging state into sim_host_battery, and keeps them
// current from UIKit's two battery notifications.
//
// Call start() once after the window exists; there is nothing to stop, because
// the app's lifetime is the observation's lifetime.
void CrossPointHostBattery_start(void);
