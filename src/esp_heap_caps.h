#pragma once

// Host stand-in for ESP-IDF's esp_heap_caps.h. Only the Picco build reaches
// it (src/main.cpp includes it under FREEINK_DEVICE_PICCO, for the sleep
// frame it parks in PSRAM). The host has one heap, so every capability is the
// same malloc; the capability bits exist so call sites compile unchanged.

#include <cstddef>
#include <cstdint>
#include <cstdlib>

#ifndef MALLOC_CAP_8BIT
#define MALLOC_CAP_EXEC (1 << 0)
#define MALLOC_CAP_32BIT (1 << 1)
#define MALLOC_CAP_8BIT (1 << 2)
#define MALLOC_CAP_DMA (1 << 3)
#define MALLOC_CAP_SPIRAM (1 << 10)
#define MALLOC_CAP_INTERNAL (1 << 11)
#define MALLOC_CAP_DEFAULT (1 << 12)
#endif

inline void *heap_caps_malloc(size_t size, uint32_t /*caps*/) {
  return std::malloc(size);
}
inline void *heap_caps_calloc(size_t n, size_t size, uint32_t /*caps*/) {
  return std::calloc(n, size);
}
inline void heap_caps_free(void *ptr) { std::free(ptr); }
