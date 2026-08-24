// S-002 (second half): a mutex held when the iOS in-process reboot longjmps.
//
// The jump skips destructors, so a RenderLock alive at that moment never runs
// xSemaphoreGive. With std::recursive_mutex underneath there was no way back
// from that -- the lock stayed held by a thread that no longer existed, and the
// render task blocked forever on the first frame after the reboot.
//
// These pin the shim's own recursive mutex and the reboot release.

#include "freertos/semphr.h"

#include <atomic>
#include <cassert>
#include <chrono>
#include <cstdio>
#include <thread>
#define TESTCHECK_FATAL_DIALECT
#include "TestCheck.h"

namespace {

bool takenWithin(SemaphoreHandle_t sem, std::chrono::milliseconds limit) {
  std::atomic<bool> got{false};
  std::thread t([&] {
    xSemaphoreTake(sem, 0);
    got = true;
    xSemaphoreGive(sem);
  });
  const auto deadline = std::chrono::steady_clock::now() + limit;
  while (!got && std::chrono::steady_clock::now() < deadline)
    std::this_thread::sleep_for(std::chrono::milliseconds(2));
  const bool result = got;
  if (!result) {
    // Unblock the probe so the process can exit, then let it finish.
    simsemphr::forceReleaseAllForReboot();
  }
  t.join();
  return result;
}

}  // namespace

int main() {
  // --- it is still a mutex -------------------------------------------------
  SemaphoreHandle_t sem = xSemaphoreCreateMutex();
  xSemaphoreTake(sem, 0);
  CHECK(xQueuePeek(sem, nullptr, 0) == pdFALSE && "a held mutex must read as unavailable");
  CHECK(!takenWithin(sem, std::chrono::milliseconds(150)) &&
         "another thread must NOT get in while it is held");
  xSemaphoreGive(sem);
  CHECK(xQueuePeek(sem, nullptr, 0) == pdTRUE);
  CHECK(takenWithin(sem, std::chrono::milliseconds(500)) && "released: the next taker gets in");

  // --- recursive for the holder --------------------------------------------
  xSemaphoreTake(sem, 0);
  xSemaphoreTake(sem, 0);
  xSemaphoreTake(sem, 0);
  CHECK(xQueuePeek(sem, nullptr, 0) == pdFALSE);
  xSemaphoreGive(sem);
  xSemaphoreGive(sem);
  CHECK(xQueuePeek(sem, nullptr, 0) == pdFALSE && "still held: three takes need three gives");
  xSemaphoreGive(sem);
  CHECK(xQueuePeek(sem, nullptr, 0) == pdTRUE);

  // --- THE REGRESSION ------------------------------------------------------
  // A thread takes the lock and vanishes without giving it back, which is
  // exactly what the longjmp does to whoever held a RenderLock.
  {
    std::thread abandoner([&] { xSemaphoreTake(sem, 0); });
    abandoner.join();  // gone, still holding
  }
  CHECK(xQueuePeek(sem, nullptr, 0) == pdFALSE && "precondition: the lock is stuck");
  CHECK(!takenWithin(sem, std::chrono::milliseconds(150)) &&
         "precondition: nobody else can take it — this is the deadlock");

  simsemphr::forceReleaseAllForReboot();

  CHECK(xQueuePeek(sem, nullptr, 0) == pdTRUE && "the reboot release must free it");
  CHECK(takenWithin(sem, std::chrono::milliseconds(500)) &&
         "after the reboot release the render task gets its frame");

  // --- a late give from the abandoned holder must not corrupt anything ------
  // If the old holder's unwind ever does run, its give lands on a mutex that
  // now belongs to someone else. It has to be a no-op, not a decrement.
  xSemaphoreTake(sem, 0);  // this thread owns it now
  {
    std::thread stale([&] { xSemaphoreGive(sem); });
    stale.join();
  }
  CHECK(xQueuePeek(sem, nullptr, 0) == pdFALSE &&
         "a give from a non-holder must not release someone else's lock");
  xSemaphoreGive(sem);
  CHECK(xQueuePeek(sem, nullptr, 0) == pdTRUE);

  // --- the release covers every mutex, not just the last one ---------------
  SemaphoreHandle_t a = xSemaphoreCreateMutex();
  SemaphoreHandle_t b = xSemaphoreCreateMutex();
  {
    std::thread t([&] {
      xSemaphoreTake(a, 0);
      xSemaphoreTake(b, 0);
    });
    t.join();
  }
  simsemphr::forceReleaseAllForReboot();
  CHECK(xQueuePeek(a, nullptr, 0) == pdTRUE && xQueuePeek(b, nullptr, 0) == pdTRUE &&
         "every registered mutex is released, not only the most recent");

  std::puts("semphr_reboot: PASS");
  return 0;
}
