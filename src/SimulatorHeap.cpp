#include "SimulatorHeap.h"

#include <atomic>
#include <cstdlib>
#include <new>

#include "SimulatorRebootResets.h"

namespace {

constexpr uint32_t kFlatHeap = 1024u * 1024u;  // what this always reported

// Read once. getenv on every getFreeHeap() would be silly -- the firmware calls
// it inside render loops.
struct Config {
  bool budget = false;
  bool pinned = false;
  uint32_t total = kFlatHeap;
  uint32_t pinnedFree = 0;

  Config() {
    if (const char *p = std::getenv("CROSSPOINT_SIM_HEAP_FREE")) {
      const long v = std::strtol(p, nullptr, 10);
      if (v > 0) {
        pinned = true;
        pinnedFree = static_cast<uint32_t>(v);
      }
    }
    if (const char *b = std::getenv("CROSSPOINT_SIM_HEAP")) {
      const long v = std::strtol(b, nullptr, 10);
      if (v > 0) {
        budget = true;
        total = static_cast<uint32_t>(v);
      }
    }
  }
};

const Config &config() {
  static const Config c;
  return c;
}

// Live only while a budget is on; otherwise the operators are a straight
// passthrough and cost a branch.
std::atomic<uint64_t> g_used{0};
std::atomic<uint32_t> g_minFree{0xFFFFFFFFu};

}  // namespace

namespace simheap {

bool budgetEnabled() { return config().budget || config().pinned; }

uint32_t totalBytes() { return config().budget ? config().total : kFlatHeap; }

uint32_t freeBytes() {
  const Config &c = config();
  if (c.pinned) return c.pinnedFree;
  if (!c.budget) return kFlatHeap;
  const uint64_t used = g_used.load(std::memory_order_relaxed);
  const uint32_t free = used >= c.total ? 0u : static_cast<uint32_t>(c.total - used);
  // Low-water mark, tracked on read: the firmware reads this constantly, and a
  // separate hook on every allocation would cost more than it is worth.
  uint32_t seen = g_minFree.load(std::memory_order_relaxed);
  while (free < seen && !g_minFree.compare_exchange_weak(seen, free)) {
  }
  return free;
}

// Fragmentation is not modelled. Saying so in one place beats every caller
// guessing why the two numbers always agree.
uint32_t maxAllocBytes() { return freeBytes(); }

uint32_t minFreeBytes() {
  const uint32_t m = g_minFree.load(std::memory_order_relaxed);
  return m == 0xFFFFFFFFu ? freeBytes() : m;
}

void noteAlloc(std::size_t bytes) {
  if (config().budget) g_used.fetch_add(bytes, std::memory_order_relaxed);
}

void noteFree(std::size_t bytes) {
  if (!config().budget) return;
  uint64_t used = g_used.load(std::memory_order_relaxed);
  const uint64_t take = bytes > used ? used : bytes;
  g_used.fetch_sub(take, std::memory_order_relaxed);
}

void resetForReboot() {
  g_used.store(0, std::memory_order_relaxed);
  g_minFree.store(0xFFFFFFFFu, std::memory_order_relaxed);
}

}  // namespace simheap

namespace {
// The in-process reboot keeps every static in the binary, so without this a
// rebooted run starts with the pre-reboot usage already spent.
const simreset::Registrar gHeapReset{[] { simheap::resetForReboot(); }};
}  // namespace

// ---------------------------------------------------------------------------
// Global operator new/delete.
//
// The accounting is DELIBERATELY ASYMMETRIC, and measurement is why it is
// documented rather than assumed. Only a sized delete can know how much to give
// back; the unsized forms give back nothing. It is tempting to say the compiler
// emits the sized form for ordinary C++ deletion so the books balance -- they
// do not. tests/heap_budget_test.cpp found libc++ freeing a std::vector's
// buffer WITHOUT going through the sized overload, so that allocation costs the
// budget and never returns it. malloc/free are not tracked at all, which makes
// vendored C (miniz, uzlib) invisible.
//
// The consequence to keep in mind: over a long run the budget drifts DOWN
// regardless of what the firmware frees. That is fine for what this is for --
// making low-memory branches reachable -- and it is why CROSSPOINT_SIM_HEAP_FREE
// exists: a test that needs an exact number should pin it rather than allocate
// its way to one. This is a pressure signal, not an allocator model.
// ---------------------------------------------------------------------------
void *operator new(std::size_t size) {
  void *p = std::malloc(size ? size : 1);
  if (!p) throw std::bad_alloc();
  simheap::noteAlloc(size);
  return p;
}

void *operator new[](std::size_t size) { return ::operator new(size); }

void *operator new(std::size_t size, const std::nothrow_t &) noexcept {
  void *p = std::malloc(size ? size : 1);
  if (p) simheap::noteAlloc(size);
  return p;
}

void *operator new[](std::size_t size, const std::nothrow_t &nt) noexcept {
  return ::operator new(size, nt);
}

void operator delete(void *p) noexcept { std::free(p); }
void operator delete[](void *p) noexcept { std::free(p); }
void operator delete(void *p, const std::nothrow_t &) noexcept { std::free(p); }
void operator delete[](void *p, const std::nothrow_t &) noexcept { std::free(p); }

void operator delete(void *p, std::size_t size) noexcept {
  if (p) simheap::noteFree(size);
  std::free(p);
}

void operator delete[](void *p, std::size_t size) noexcept {
  if (p) simheap::noteFree(size);
  std::free(p);
}
