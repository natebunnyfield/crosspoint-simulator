#pragma once

// WHICH APP THIS IS, for ios/GestureBindings.h's Device-keyed rules. Kept out
// of that header so it stays pure (tests/gesture_bindings_test.cpp compiles it
// with nothing but -Iios), and kept in ONE place so the recognizers, the
// volume adapter and the shim cannot disagree about it.
// FREEINK_DEVICE_PICCO comes from the command line with SIMULATOR_DEVICE_PICCO
// (ios/CMakeLists.txt); BoardConfig.h is included so the macro is never read
// as an undefined 0 (tests/freeink_macro_include_test.py).

#include "BoardConfig.h"
#include "GestureBindings.h"

namespace gesturebind {
#if FREEINK_DEVICE_PICCO
constexpr Device kThisDevice = Device::Picco;
#else
constexpr Device kThisDevice = Device::X3;
#endif
}  // namespace gesturebind
