#pragma once
#include <cstddef>
#include <cstdint>

// A budgeted stand-in for the device's heap (S-001).
//
// THE PROBLEM THIS SOLVES. ESP.getFreeHeap() returned a flat 1 MB, and the
// firmware is full of branches that only run when free heap is LOW: the
// background page build (EpubReaderActivity.cpp:268), the plane buffer
// (:1692), retaining a mini font (SdCardFont.cpp:121), image decode
// (ImageBlock.cpp:152), the JPEG path and the CSS parser. On a 380 KB device
// those fire; against a flat megabyte not one of them is reachable. The only
// pre-device gate the project has could not execute its own degradation paths.
//
// HOW IT WORKS. A budget starts at a device-realistic total and shrinks as the
// firmware allocates, tracked by the global operator new/delete in
// SimulatorHeap.cpp. It is not a simulation of the ESP allocator -- it does not
// model fragmentation, and the host's allocator behaves nothing like it. What
// it does give is a number that FALLS UNDER PRESSURE, which is what those
// branches are testing for.
//
// OPT-IN, always. Without the env var the reported heap is exactly the flat
// 1 MB it has always been, so every existing headless script and screenshot
// run is untouched.
//
//   CROSSPOINT_SIM_HEAP=380000    budget mode: total bytes, counts down
//   CROSSPOINT_SIM_HEAP_FREE=40000 pin free heap to a fixed value
//
// The pin exists because a countdown is not reproducible enough to assert on:
// a test that wants "the CSS parser refuses at 12 KB free" should say so
// outright rather than allocate its way there. The pin wins when both are set.
namespace simheap {

// Reads the env once. Called from ESP's accessors, so no caller has to.
bool budgetEnabled();

// Bytes the firmware could still allocate. Flat 1 MB unless a mode is on.
uint32_t freeBytes();

// Total, and the largest single block. Fragmentation is not modelled, so the
// largest block is the free figure -- stated here rather than implied, because
// a caller comparing the two on device is asking a question this cannot answer.
uint32_t totalBytes();
uint32_t maxAllocBytes();

// Low-water mark of freeBytes() since boot.
uint32_t minFreeBytes();

// Called by the global operator new/delete.
void noteAlloc(std::size_t bytes);
void noteFree(std::size_t bytes);

// Reset to the starting budget; the in-process reboot registers this.
void resetForReboot();

}  // namespace simheap
