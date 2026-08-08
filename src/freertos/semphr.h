#pragma once
#include <atomic>
#include <condition_variable>
#include <cstdint>
#include <mutex>
#include <thread>
#include <vector>

#include "FreeRTOS.h"
#include "task.h"

// A recursive mutex the shim owns outright, rather than std::recursive_mutex.
//
// The reason is the iOS in-process reboot. ESP.restart() there is a longjmp,
// which skips destructors -- so a RenderLock held at that moment never runs
// xSemaphoreGive, and the mutex stays locked with a holder that no longer
// exists. The render task then blocks forever on the first frame after the
// reboot, and the app looks hung with no clue why.
//
// std::recursive_mutex cannot be rescued from that: unlocking one you do not
// own is undefined, and destroying one with a waiter parked on it is worse. So
// the lock is built from a plain mutex, a condition variable and an explicit
// owner/count, which CAN be reset to "free" and have its waiters woken. That is
// what forceReleaseAllForReboot() does, and it is registered to run just before
// the jump (SimulatorRebootResets.h).
struct SimMutex {
  std::mutex m;
  std::condition_variable cv;
  // Ownership is keyed on a per-thread TOKEN, not on TaskHandle_t and not on
  // std::thread::id. Both of those let an unrelated thread walk into a held
  // lock as though it were re-entering: handles are shared by every thread not
  // created through xTaskCreate, and a std::thread::id is REUSED once its
  // thread ends -- which is exactly the case here, since the whole point is a
  // holder that died without giving the lock back. The token is drawn from a
  // counter that only goes up. The handle is kept because
  // xSemaphoreGetMutexHolder reports it.
  uint64_t ownerToken = 0;
  TaskHandle_t holder = nullptr;
  uint16_t holdCount = 0;
};
typedef SimMutex *SemaphoreHandle_t;

namespace simsemphr {

// Unique for the life of the process, never recycled.
inline uint64_t currentOwnerToken() {
  static std::atomic<uint64_t> next{1};
  thread_local const uint64_t token = next.fetch_add(1);
  return token;
}

// Every mutex ever created, so the reboot reset can find them. Never erased:
// FreeRTOS mutexes here live for the process, and a dangling entry would be a
// worse bug than the leak.
inline std::mutex &registryLock() {
  static std::mutex m;
  return m;
}
inline std::vector<SimMutex *> &registry() {
  static std::vector<SimMutex *> v;
  return v;
}

// Drop every lock and wake everyone waiting. Called ONLY on the in-process
// reboot path, where the threads that held these locks are about to be
// abandoned along with their stacks.
inline void forceReleaseAllForReboot() {
  std::lock_guard<std::mutex> guard(registryLock());
  for (SimMutex *sem : registry()) {
    std::lock_guard<std::mutex> lock(sem->m);
    sem->ownerToken = 0;
    sem->holder = nullptr;
    sem->holdCount = 0;
    sem->cv.notify_all();
  }
}

}  // namespace simsemphr

inline SemaphoreHandle_t xSemaphoreCreateMutex() {
  auto *sem = new SimMutex();
  std::lock_guard<std::mutex> guard(simsemphr::registryLock());
  simsemphr::registry().push_back(sem);
  return sem;
}

inline bool xSemaphoreTake(SemaphoreHandle_t sem, uint32_t /*ticksToWait*/) {
  if (!sem)
    return true;
  const uint64_t self = simsemphr::currentOwnerToken();
  std::unique_lock<std::mutex> lock(sem->m);
  // Recursive: the holder walks straight back in. Everyone else waits for the
  // count to reach zero.
  sem->cv.wait(lock,
               [sem, self] { return sem->holdCount == 0 || sem->ownerToken == self; });
  sem->ownerToken = self;
  sem->holder = xTaskGetCurrentTaskHandle();
  sem->holdCount++;
  return true;
}

inline bool xSemaphoreGive(SemaphoreHandle_t sem) {
  if (!sem)
    return true;
  std::lock_guard<std::mutex> lock(sem->m);
  // A give from a thread that does not hold it is a no-op rather than a
  // corruption: after forceReleaseAllForReboot() the old holder's unwind (if it
  // ever runs) must not decrement someone else's count.
  if (sem->holdCount == 0 || sem->ownerToken != simsemphr::currentOwnerToken())
    return true;
  if (--sem->holdCount == 0) {
    sem->ownerToken = 0;
    sem->holder = nullptr;
    sem->cv.notify_all();
  }
  return true;
}

inline TaskHandle_t xSemaphoreGetMutexHolder(SemaphoreHandle_t sem) {
  if (!sem)
    return nullptr;
  std::lock_guard<std::mutex> lock(sem->m);
  return sem->holder;
}

// xQueuePeek on a mutex: pdTRUE if the mutex is available (not taken).
inline int xQueuePeek(SemaphoreHandle_t sem, void *, uint32_t) {
  if (!sem)
    return pdTRUE;
  std::lock_guard<std::mutex> lock(sem->m);
  return sem->holdCount == 0 ? pdTRUE : pdFALSE;
}
