#pragma once
#include <cstdint>
inline void esp_restart() {}
#include "SimulatorHeap.h"

// Same budget as ESP.getFreeHeap(); see SimulatorHeap.h.
inline uint32_t esp_get_free_heap_size() { return simheap::freeBytes(); }